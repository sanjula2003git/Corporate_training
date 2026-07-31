"""
The building, as engineering — plus the narrative stages.
=========================================================
THE PLANT MODEL IS A COPY OF THE NOTEBOOK'S. Same cooling load, same fan law,
same COP curve, same PPD proxy, same floor-plate generator — so a number quoted
in `Building_Energy_Optimization_DL.ipynb` and the same number on the matching
app page always agree.

Narrative beats:
  in-use          - a floor plate conditioned for 260 people when 40 are in.
  enter-ai        - engineer + sensors. Not a replacement.
  reading         - one 15-minute interval becomes one row.
  two-records     - the sensor row vs the ceiling camera frame.
  camera-problem  - a grid of temperatures. Which pixel is a person? None.
  handmade        - count people by brightness. Watch it fail.
  why-dl          - therefore deep learning.
  engineer-brain  - how a facilities engineer decides -> that IS a neuron.
  learning-loop   - predict -> measure -> adjust -> repeat.
  cnn-journey     - filters slide over the plate and find the clusters.
  occupancy-locate- the CNN shows WHICH part of the floor is in use.
  fusion-engine   - the product: set this zone back, this much, this shift.
  pipeline        - the whole system, start to finish.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from numpy.lib.stride_tricks import sliding_window_view

import scaffold as S

POS, NEG = S.POS, S.NEG
GREEN, AMBER, RED = S.GREEN, S.AMBER, S.RED
TECH, MUTED, TEXT, PANEL = S.TECH, S.MUTED, S.TEXT, S.PANEL
style, animate = S.style, S.animate

# ---- the plant model -------------------------------------------------------
CAP = 260               # desks on the floor plate
DESIGN_COOL = 320.0     # kW thermal — the plant's design duty
FAN_MIN, FAN_MAX = 2.5, 16.0
OA_DESIGN = 200.0       # the fixed damper brings in fresh air for 200 people, ALWAYS
GRID_KG = 0.42          # kg CO2 per kWh of grid electricity
TARIFF = 0.18           # currency per kWh
LIMIT = 0.55            # kW per person, above which an interval is over-conditioned


def cooling_load_kw(outdoor, setpoint, solar, occ, hum, oa_people=OA_DESIGN):
    """Thermal cooling load on the plant, kW.

    `oa_people` is the OUTSIDE-AIR basis: how many people the ventilation is
    sized for at this moment. A fixed damper holds it at OA_DESIGN whatever the
    floor is doing. Demand-controlled ventilation follows the CO2 sensor
    instead — that difference is the largest single saving in the whole project.
    """
    dT = np.clip(np.asarray(outdoor, float) - np.asarray(setpoint, float), 0, None)
    return (2.6 * dT                                             # envelope conduction
            + 0.07 * np.asarray(solar, float)                    # solar gain through glazing
            + 0.42 * np.asarray(occ, float)                      # people + laptops + lights
            + 0.18 * np.clip(np.asarray(hum, float) - 50, 0, None)   # dehumidification
            + 0.030 * np.asarray(oa_people, float) * dT)         # fresh air, cooled


def fan_kw(cool_thermal):
    """VAV supply fans: airflow follows the load, power follows the fan affinity law."""
    frac = np.clip(np.asarray(cool_thermal, float) / DESIGN_COOL, 0.15, 1.0)
    return FAN_MIN + (FAN_MAX - FAN_MIN) * frac ** 1.8


def chiller_cop(outdoor):
    """COP degrades as the chiller rejects heat to a hotter outdoors."""
    return np.clip(3.6 - 0.045 * np.clip(np.asarray(outdoor, float) - 25, 0, None), 2.0, 3.6)


def hvac_kw_for(outdoor, setpoint, solar, occ, hum, oa_people=OA_DESIGN):
    """Electrical draw of the whole HVAC plant, kW, and the thermal load behind it."""
    cool = cooling_load_kw(outdoor, setpoint, solar, occ, hum, oa_people)
    return fan_kw(cool) + cool / chiller_cop(outdoor), cool


def indoor_for(setpoint, cool_thermal):
    """The room drifts above setpoint when the load exceeds what the plant can pull down."""
    return np.asarray(setpoint, float) + np.clip(0.011 * (np.asarray(cool_thermal, float) - 190),
                                                 0, None)


def ppd(indoor, hum):
    """Predicted Percentage Dissatisfied (ISO 7730), from a simplified PMV proxy."""
    pmv = 0.30 * (np.asarray(indoor, float) - 23.5) + 0.012 * (np.asarray(hum, float) - 50)
    return 100 - 95 * np.exp(-0.03353 * pmv ** 4 - 0.2179 * pmv ** 2)


def occ_shape(hour):
    """Two busy periods with a lunch dip — the floor plate's working day."""
    return np.clip(0.95 * np.exp(-((hour - 10.5) ** 2) / (2 * 1.6 ** 2))
                   + 0.90 * np.exp(-((hour - 15.0) ** 2) / (2 * 1.7 ** 2))
                   - 0.35 * np.exp(-((hour - 13.0) ** 2) / (2 * 0.7 ** 2)), 0, 1)


def sweep(occ, outdoor=32, solar=520, hum=58, oa=None):
    """Sweep the cooling setpoint: energy always falls, comfort decides how far you may go."""
    sps = np.arange(21, 28.01, 0.25)
    oa_basis = OA_DESIGN if oa is None else oa
    kw, cm = [], []
    for sp in sps:
        k, cool = hvac_kw_for(outdoor, sp, solar, occ, hum, oa_basis)
        kw.append(k); cm.append(float(ppd(indoor_for(sp, cool), hum)))
    return sps, np.array(kw), np.array(cm)


# ---- the ceiling camera ----------------------------------------------------
KIND_SEED = {"empty": 0, "occupied": 1, "crowded": 2, "solar": 3, "heat_leak": 4}
KINDS = ["empty", "occupied", "crowded", "solar", "heat_leak"]
PEOPLE = {"empty": 0, "occupied": 12, "crowded": 34, "solar": 0, "heat_leak": 0}


@st.cache_data(show_spinner=False)
def make_floor(kind="empty", size=64, seed=0, n_people=None, jitter=False):
    """A floor plate seen from the ceiling as a normalised temperature grid.

    empty     - nobody in, cool plate
    occupied  - about 12 people in one zone
    crowded   - two busy zones, about 34 people
    solar     - sun on the south facade         (nobody in)  <- the decoy
    heat_leak - warm strip along a leaky wall   (nobody in)  <- the other decoy

    The two decoys are warm and empty. That is the whole reason a brightness
    threshold cannot count people.
    """
    rng = np.random.default_rng(seed * 7 + KIND_SEED[kind])
    Y, X = np.mgrid[0:size, 0:size]
    img = 0.36 + rng.normal(0, 0.022, (size, size))
    img += 0.05 * np.exp(-((X - size + 1) ** 2) / (2 * 7.0 ** 2))     # warm south facade
    img += 0.03 * np.exp(-(Y ** 2) / (2 * 6.0 ** 2))                  # warm riser core

    def people(k, cy, cx, spread):
        out = np.zeros_like(img)
        for _ in range(k):
            py = np.clip(rng.normal(cy, spread), 3, size - 4)
            px = np.clip(rng.normal(cx, spread), 3, size - 4)
            out += np.exp(-(((Y - py) ** 2 + (X - px) ** 2) / (2 * 2.1 ** 2)))
        return out

    if n_people is not None:                          # training-set path
        if n_people > 0:
            k1 = n_people if n_people < 20 else n_people // 2
            img += 0.55 * people(k1, rng.uniform(12, 52), rng.uniform(12, 52),
                                 rng.uniform(6, 12))
            if n_people >= 20:
                img += 0.55 * people(n_people - k1, rng.uniform(12, 52), rng.uniform(12, 52),
                                     rng.uniform(6, 12))
        if jitter and rng.random() < 0.45:            # sun on the facade as well
            img += rng.uniform(0.12, 0.30) * np.exp(
                -((X - size + rng.uniform(1, 8)) ** 2) / (2 * 11.0 ** 2))
        if jitter and rng.random() < 0.30:            # and a leaky wall as well
            img += rng.uniform(0.15, 0.34) * np.exp(
                -((Y - size + rng.uniform(1, 6)) ** 2) / (2 * 3.0 ** 2))
    elif kind == "occupied":
        img += 0.55 * people(12, 40, 22, 8)
    elif kind == "crowded":
        img += 0.55 * (people(18, 24, 20, 10) + people(16, 42, 42, 10))
    elif kind == "solar":
        img += 0.30 * np.exp(-((X - size + 4) ** 2) / (2 * 11.0 ** 2))
    elif kind == "heat_leak":
        img += 0.34 * np.exp(-((Y - size + 3) ** 2) / (2 * 3.0 ** 2))
    return np.clip(img, 0, 1)


def _conv2d(img, k):
    win = sliding_window_view(img, k.shape)
    return np.einsum("ijkl,kl->ij", win, k)


def people_cam(kind, size=64, seed=0):
    """A Grad-CAM-style attention map: the compact warm blobs people make,
    with the broad facade and wall bands suppressed."""
    img = make_floor(kind, size=size, seed=seed)
    kb = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], float)     # centre-surround
    blob = np.abs(_conv2d(np.pad(img, 1, mode="edge"), kb))
    sm = _conv2d(np.pad(blob, 2, mode="edge"), np.ones((5, 5)) / 25.0)
    return 0.05 + 0.95 * sm / (sm.max() + 1e-9)


def heat(z, title="", h=340, colorscale="Inferno"):
    return S.heat(z, colorscale=colorscale, h=h, title=title)


# ================================================================ 1 · a weekday
def render_in_use(style_, animate_):
    st.title("A building on a weekday — conditioned for a floor that is not there")
    st.markdown("#### The plant is sized for 260 people. Most of the day, far fewer are in.")
    st.write("")

    hour = np.arange(0, 24, 0.25)
    busy = st.slider("How busy is the floor today?", 0.2, 1.0, 0.75, 0.05)
    outdoor_peak = st.slider("Peak outdoor temperature (°C)", 26, 40, 32, 1)

    occ = np.round(CAP * occ_shape(hour) * busy)
    outdoor = (outdoor_peak - 6) + 6 * np.sin(2 * np.pi * (hour - 9) / 24)
    solar = np.where((hour > 6) & (hour < 19),
                     np.clip(880 * np.sin(np.pi * (hour - 6) / 13), 0, None) * 0.8, 0.0)
    hum = np.clip(72 - 0.9 * (outdoor - 25), 30, 95)
    sched = (hour >= 7) & (hour < 19)
    setpoint = np.where(sched, 23.0, 27.0)
    kw, cool = hvac_kw_for(outdoor, setpoint, solar, occ, hum)
    kw = np.where(sched, kw, 1.5)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hour, y=occ, mode="lines", name="people on the floor",
                             line=dict(color=POS, width=3)))
    fig.add_trace(go.Scatter(x=hour, y=np.full_like(hour, OA_DESIGN), mode="lines",
                             name="people the ventilation is sized for",
                             line=dict(color=RED, width=2.5, dash="dash")))
    fig.update_layout(title="the floor plate, and what the damper assumes about it")
    fig.update_xaxes(title="hour of day"); fig.update_yaxes(title="people")
    style_(fig, 340); animate_(fig, S.line_grow(hour, occ, POS), ms=45)
    st.plotly_chart(fig, use_container_width=True)
    st.write("")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=hour, y=kw, mode="lines", line=dict(color=AMBER, width=3),
                              fill="tozeroy", name="HVAC draw"))
    fig2.update_layout(title="what the HVAC plant actually draws")
    fig2.update_xaxes(title="hour of day"); fig2.update_yaxes(title="kW")
    st.plotly_chart(style_(fig2, 340), use_container_width=True)

    kwh = float(np.sum(kw) * 0.25)
    per_person = kwh / max(float(np.sum(occ) * 0.25 / 24), 1)
    over = float(np.mean(kw[sched] / np.clip(occ[sched], 1, None) > LIMIT))
    c = st.columns(3)
    c[0].metric("Energy today", f"{kwh:,.0f} kWh", f"{kwh*GRID_KG:,.0f} kg CO₂")
    c[1].metric("Peak people on the floor", f"{occ.max():.0f} / {CAP}")
    c[2].metric("Occupied intervals over the limit", f"{over:.0%}", delta_color="inverse")
    st.write("")

    st.markdown("### So — can the facilities manager just turn it down?")
    if st.button("Answer", type="primary"):
        st.error("**Not safely, and not by hand.** Turning the plant down without knowing who is on the "
                 "floor risks a comfort complaint, and comfort complaints are what get an energy "
                 "initiative cancelled. There are 96 intervals a day across every zone.")
        st.info("👉 Look at the red line on the first chart. **The damper brings in fresh air for 200 "
                "people all day, whatever the floor is doing.** That single fixed assumption is the "
                "largest saving in this whole project — and finding it needs a measurement of who is "
                "actually there.")


# ================================================================ 2 · sensing itself
def render_enter_ai(style_, animate_):
    st.title("A building that senses itself")
    st.markdown("#### Same plant, same setpoints. Scheduled by a clock, or matched to the floor?")
    st.write("")

    hour = np.arange(0, 24, 0.25)
    occ = np.round(CAP * occ_shape(hour) * 0.55)
    outdoor = 26 + 6 * np.sin(2 * np.pi * (hour - 9) / 24)
    solar = np.where((hour > 6) & (hour < 19),
                     np.clip(880 * np.sin(np.pi * (hour - 6) / 13), 0, None) * 0.8, 0.0)
    hum = np.clip(72 - 0.9 * (outdoor - 25), 30, 95)
    sched = (hour >= 7) & (hour < 19)
    sp = np.where(sched, 23.0, 27.0)

    fixed, _ = hvac_kw_for(outdoor, sp, solar, occ, hum, OA_DESIGN)
    dcv, _ = hvac_kw_for(outdoor, sp, solar, occ, hum, np.clip(occ, 20, OA_DESIGN))
    fixed = np.where(sched, fixed, 1.5); dcv = np.where(sched, dcv, 1.5)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hour, y=fixed, mode="lines", name="fixed damper — for 200 people",
                             line=dict(color=NEG, width=3)))
    fig.add_trace(go.Scatter(x=hour, y=dcv, mode="lines", name="ventilated for the people present",
                             line=dict(color=GREEN, width=3)))
    fig.update_layout(title="the same day, with and without knowing who is on the floor")
    fig.update_xaxes(title="hour of day"); fig.update_yaxes(title="HVAC kW")
    style_(fig, 380); animate_(fig, S.line_grow(hour, dcv, GREEN), ms=45)
    st.plotly_chart(fig, use_container_width=True)

    a, b = float(np.sum(fixed) * 0.25), float(np.sum(dcv) * 0.25)
    c = st.columns(3)
    c[0].metric("Fixed damper", f"{a:,.0f} kWh/day")
    c[1].metric("Matched to the floor", f"{b:,.0f} kWh/day", f"-{a-b:,.0f} kWh")
    c[2].metric("Saving", f"{(a-b)/a*100:.0f} %")
    st.write("")

    st.markdown("### Facilities Engineer **+** AI. Never engineer *vs* AI.")
    x, y = st.columns(2)
    x.markdown("**The engineer stays in charge of**\n\n- the comfort standard and who complains\n"
               "- whether a zone may be set back at all\n- commissioning, safety and statutory air "
               "changes\n- judging a hot complaint against a warm façade\n- the building, which AI knows "
               "nothing about")
    y.markdown("**Where one person needs a hand**\n\n- 96 intervals a day, every zone\n- separating a "
               "sunlit bay from a full room\n- comparing today against sixteen weeks of history\n- "
               "counting who is actually on the floor\n- never looking away")
    st.info("The system's job is not to decide. It hands the engineer **the zones that are being "
            "conditioned for people who are not there**, with the evidence, so a person makes the call.")


# ================================================================ 3 · one interval
def render_reading(get_data, style_, animate_):
    st.title("One 15-minute interval — how a building's state becomes data")
    st.markdown("#### The model will never walk the floor.")
    d = get_data()
    st.write("")

    steps = [
        ("🏢  The real floor plate", "People arrive, the sun moves across the façade, the plant modulates. "
                                     "All of it at once.", MUTED),
        ("📟  The BMS reads it", "Indoor and outdoor temperature, humidity, CO₂, occupancy, solar, PM2.5 "
                                 "and the setpoint — each one number.", POS),
        ("📷  The ceiling camera captures it", "A thermal frame of the plate. Not a head count — a grid of "
                                               "temperatures.", AMBER),
        ("📄  It becomes one row", "This row, and the kW the plant drew, is the *entire* building as far "
                                   "as the model is concerned.", GREEN),
    ]
    i = st.slider("Walk through the interval", 1, 4, 1)
    for k, (t, txt, c) in enumerate(steps, start=1):
        if k <= i:
            st.markdown(f"<div style='padding:12px 16px;margin:6px 0;border-radius:4px;"
                        f"border-left:4px solid {c};background:{PANEL};color:{TEXT}'>"
                        f"<b>{t}</b><br><span style='color:{MUTED}'>{txt}</span></div>",
                        unsafe_allow_html=True)
    if i == 4:
        st.write("")
        st.dataframe(pd.DataFrame([
            ["🌡️ Indoor temperature", "Zone sensor", "°C", "What the room actually reached"],
            ["🌤️ Outdoor temperature", "Weather station", "°C", "The load the envelope has to reject"],
            ["💧 Humidity", "Zone sensor", "%", "Dehumidification is real cooling work"],
            ["🫁 CO₂", "Zone sensor", "ppm", "A proxy for people — and the basis for demand-led ventilation"],
            ["👥 Occupancy", "Access control", "people", "The number the plant should be sized to right now"],
            ["☀️ Solar", "Pyranometer", "W/m²", "Gain through the glazing, hours before it shows as heat"],
            ["🌫️ PM2.5", "Air quality", "µg/m³", "Limits how far outside air can be reduced"],
            ["🎚️ Setpoint", "BMS", "°C", "The lever — and the one the occupants feel"],
        ], columns=["Channel", "Source", "Unit", "What it tells you"]),
            use_container_width=True, hide_index=True)
        st.write("")
        row = d["clean"].iloc[400]
        cols = ["indoor_temp_c", "outdoor_temp_c", "humidity_pct", "co2_ppm",
                "occupancy", "solar_wm2", "pm25_ugm3", "setpoint_c"]
        st.markdown("##### One interval = one row of those numbers")
        st.dataframe(pd.DataFrame([row[cols].values], columns=[
            "Indoor °C", "Outdoor °C", "Humidity %", "CO₂ ppm", "People",
            "Solar W/m²", "PM2.5", "Setpoint °C"]).round(1),
            use_container_width=True, hide_index=True)
        st.info("The model never walks the floor — it sees only this row. If the row is wrong, the "
                "prediction is wrong, and the model has no way to notice.")


# ================================================================ 4 · two records
def render_two_records(style_, animate_):
    st.title("Two kinds of record — a sensor row and a camera frame")
    st.markdown("#### The same interval produces both. They are not the same problem.")
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div style='border-top:3px solid {POS};background:{PANEL};border-radius:4px;"
                    f"padding:14px'><b style='color:{POS}'>📊 The BMS row</b><br>"
                    f"<span style='color:{MUTED};font-size:13px'>Eight values an engineer named and gave "
                    f"units. Each already means something.</span></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({
            "Channel": ["Indoor", "Outdoor", "Humidity", "CO₂", "Occupancy",
                        "Solar", "PM2.5", "Setpoint"],
            "Value": ["24.1 °C", "32.0 °C", "58 %", "780 ppm", "180", "520 W/m²", "18", "23.0 °C"],
        }), use_container_width=True, hide_index=True, height=330)
        st.caption("**8 named numbers.** A human can read it.")
    with c2:
        st.markdown(f"<div style='border-top:3px solid {AMBER};background:{PANEL};border-radius:4px;"
                    f"padding:14px'><b style='color:{AMBER}'>🌡️ The ceiling camera frame</b><br>"
                    f"<span style='color:{MUTED};font-size:13px'>Thousands of temperatures. Nothing in it "
                    f"is named.</span></div>", unsafe_allow_html=True)
        st.plotly_chart(heat(make_floor("crowded"), title="one plate · 64 × 64 temperatures", h=330),
                        use_container_width=True)
        st.caption("**4,096 unnamed numbers.** The people are in the pattern.")
    st.write("")
    st.info("One interval, two records. The Random Forest handles the eight readings. It cannot be pointed "
            "at 4,096 unnamed pixels at all — which is why deep learning appears later.")


# ================================================================ 5 · the camera
def render_camera_problem(style_, animate_):
    st.title("What the ceiling camera actually sends")
    st.markdown("#### You *see* the people instantly. Now find them in the numbers.")
    st.write("")
    kind = st.selectbox("Choose a plate", KINDS, index=1, format_func=lambda k: {
        "empty": "Nobody in — plate cool",
        "occupied": "About 12 people in one zone",
        "crowded": "Two busy zones, about 34 people",
        "solar": "Sun on the south façade — NOBODY in",
        "heat_leak": "Warm strip along a leaky wall — NOBODY in",
    }[k])
    img = make_floor(kind)
    st.plotly_chart(heat(img, title=f"one plate · {img.size:,} temperature values", h=380),
                    use_container_width=True)
    st.caption("Every pixel is a normalised temperature between 0 and 1. None of them is labelled "
               "'person'. Compare **crowded** with **solar** — both are warm, and only one has anybody "
               "in it.")
    st.write("")
    if st.button("Where are the people?", type="primary"):
        st.error("They are not any single pixel. A person is a **small compact warm blob**; sunlight is a "
                 "**broad band down one edge**; a leaky wall is a **thin strip along another**. Each is a "
                 "*pattern* over hundreds of pixels — no one number holds it.")
        st.info("At the BMS row an engineer had already named occupancy and CO₂, so the forest had "
                "features to weigh. Here nothing is pre-named. There is no column called 'person' — only "
                "the shape and the size of the warm patch.")


# ================================================================ 6 · by hand
def render_handmade(style_, animate_):
    st.title("Counting people by brightness, by hand")
    st.markdown("#### Reduce the plate to one number, set a threshold, watch it fail.")
    st.caption("The theory is sound: people are warm, so more people means a warmer plate. The problem is "
               "the sun, and the leaky wall.")
    st.write("")

    cases = [("Empty (nobody in)", make_floor("empty"), GREEN),
             ("Sunlit façade (nobody in)", make_floor("solar"), GREEN),
             ("Leaky wall (nobody in)", make_floor("heat_leak"), GREEN),
             ("Occupied — 12 people", make_floor("occupied"), RED),
             ("Crowded — 34 people", make_floor("crowded"), RED)]
    means = [(n, float(im.mean()), c) for n, im, c in cases]

    thr = st.slider("Set the mean-temperature threshold (occupied above this)",
                    0.30, 0.60, 0.42, 0.005)
    fig = go.Figure()
    for n, v, c in means:
        fig.add_trace(go.Bar(x=[n], y=[v], marker_color=c, showlegend=False,
                             text=f"{v:.3f}", textposition="outside"))
    fig.add_hline(y=thr, line=dict(color=POS, width=2, dash="dash"),
                  annotation_text=f"occupied above {thr:.3f}", annotation_position="top left")
    fig.update_layout(title="one number per plate — can a line separate occupied from empty?")
    fig.update_yaxes(title="mean plate temperature (normalised)", range=[0, 0.62])
    style_(fig, 380)
    animate_(fig, S.bars_grow([dict(x=[n], y=[v], color=c, text=f"{v:.3f}") for n, v, c in means]),
             ms=90)
    st.plotly_chart(fig, use_container_width=True)

    missed = [n for n, v, c in means if c == RED and v <= thr]
    false_al = [n for n, v, c in means if c == GREEN and v > thr]
    a, b = st.columns(2)
    a.metric("Occupied plates missed", len(missed), ", ".join(missed) or "none", delta_color="inverse")
    b.metric("Empty plates called occupied", len(false_al), ", ".join(false_al) or "none",
             delta_color="inverse")
    st.write("")

    st.warning("**Move the threshold anywhere you like — you cannot win.** A sunlit empty façade is warmer "
               "than a lightly occupied floor, so any line that catches the 12 people also fires on an "
               "empty room. Averaging threw away the only thing that distinguishes them: **the size and "
               "shape of the warm patch.**")
    st.error("This is the expensive kind of failure. Ventilating an empty sunlit floor for 200 people is "
             "exactly the waste the project exists to find.")


# ================================================================ 7 · why DL
def render_why_dl(style_):
    st.title("The rulebook runs out — therefore, deep learning")
    st.markdown("#### An engineer glances at the plate and counts. They cannot write down the rule.")
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div style='border-top:3px solid {RED};background:{PANEL};border-radius:4px;"
                    f"padding:16px;height:100%'><b style='color:{RED}'>Writing rules by hand</b>"
                    f"<ul style='color:{MUTED};font-size:14px;line-height:1.7'>"
                    f"<li>Every temperature threshold is too tight or too loose</li>"
                    f"<li>One feature per rule, most of the plate discarded</li>"
                    f"<li>Different for every façade, season and camera angle</li>"
                    f"<li>You maintain it forever</li></ul></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='border-top:3px solid {GREEN};background:{PANEL};border-radius:4px;"
                    f"padding:16px;height:100%'><b style='color:{GREEN}'>Learning from examples</b>"
                    f"<ul style='color:{MUTED};font-size:14px;line-height:1.7'>"
                    f"<li>Show it labelled plates: empty, occupied, crowded</li>"
                    f"<li>It works out which patterns matter, by itself</li>"
                    f"<li>The whole plate is used, not one summary number</li>"
                    f"<li>A new floor means new examples, not new rules</li></ul></div>",
                    unsafe_allow_html=True)
    st.write("")
    st.divider()
    st.markdown("### How a network gets from pixels to a head count")
    ladder = [("🌡️", "Plate", "4,096 raw temperatures", MUTED),
              ("📐", "Edges", "where temperature changes sharply", POS),
              ("🔥", "Warm regions", "blobs and bands, not single pixels", AMBER),
              ("👥", "Clusters", "compact blobs, not broad bands", TECH),
              ("🔢", "Occupancy class", "empty / occupied / crowded", GREEN)]
    cols = st.columns(len(ladder))
    for col, (ico, name, sub, c) in zip(cols, ladder):
        with col:
            st.markdown(f"<div style='border:1px solid #2b3440;border-top:3px solid {c};"
                        f"background:{PANEL};border-radius:4px;padding:12px;text-align:center;"
                        f"height:100%'><div style='font-size:26px'>{ico}</div>"
                        f"<b style='color:{c};font-size:13px'>{name}</b><br>"
                        f"<span style='color:{MUTED};font-size:12px'>{sub}</span></div>",
                        unsafe_allow_html=True)
    st.write("")
    st.success("**Machine Learning weights the features you name. Deep Learning finds the features you "
               "cannot name.** That single sentence is why this course has two halves — and why the BMS "
               "row still belongs to the Random Forest.")


# ================================================================ 8 · engineer brain
def render_engineer_brain(style_):
    st.title("How a facilities engineer decides — and why that is a neuron")
    st.markdown("#### Weigh a few signals, add them up, make one call.")
    st.write("")
    c1, c2 = st.columns([1, 1.3])
    with c1:
        co2 = st.slider("CO₂ (ppm)", 400, 1400, 780, 10)
        indoor = st.slider("Indoor temperature (°C)", 20.0, 29.0, 24.1, 0.1)
        hour = st.slider("Hour of day", 0, 23, 15)
        complaints = st.slider("Comfort complaints this week", 0, 10, 1)
    w = dict(co2=0.006, indoor=0.55, hour=0.10, comp=-0.55)
    contrib = {"CO₂": w["co2"] * co2, "Indoor temp": w["indoor"] * indoor,
               "Hour": w["hour"] * hour, "Complaints": w["comp"] * complaints}
    total = sum(contrib.values()) - 17.0

    with c2:
        fig = go.Figure(go.Bar(x=list(contrib), y=[contrib[n] for n in contrib],
                               marker_color=[POS, AMBER, TECH, GREEN],
                               text=[f"{contrib[n]:.1f}" for n in contrib], textposition="outside"))
        fig.update_layout(title=f"weighted evidence · total after baseline = {total:+.2f}")
        fig.update_yaxes(title="contribution to the call")
        st.plotly_chart(style_(fig, 360), use_container_width=True)

    if total > 0:
        st.error(f"**Call: the floor is busy — hold the setpoint.** Total {total:+.2f} clears zero.")
    else:
        st.success(f"**Call: the floor is quiet — it can be set back.** Total {total:+.2f} is below zero.")
    st.write("")
    st.markdown(
        f"<div style='border-left:3px solid {POS};padding:10px 0 10px 16px;font-size:16px;color:{TEXT};"
        f"line-height:1.7'>What you just moved was <b>w · x + b</b>. Note the complaints weight is "
        f"<b>negative</b> — recent complaints are evidence <i>against</i> setting anything back. "
        f"<b>That is a neuron</b>, and the only difference in the machine version is that nobody chooses "
        f"the weights.</div>", unsafe_allow_html=True)


# ================================================================ 9 · learning loop
def render_learning_loop(style_, animate_):
    st.title("Improving after every bad day")
    st.markdown("#### Predict, compare with the meter, adjust, repeat.")
    st.write("")
    true_w = 3.4
    start_w = st.slider("Starting guess for the occupancy weight", 0.0, 8.0, 7.2, 0.1)
    lr = st.slider("How strongly to correct after each bad day", 0.02, 0.6, 0.22, 0.02)
    w, ws = start_w, [start_w]
    for _ in range(24):
        w = w - lr * 2 * (w - true_w)
        ws.append(w)
    fig = go.Figure(go.Scatter(x=list(range(len(ws))), y=ws, mode="lines+markers",
                               line=dict(color=POS, width=3), name="the weight"))
    fig.add_hline(y=true_w, line=dict(color=GREEN, width=2, dash="dash"),
                  annotation_text="the weight that fits this building")
    fig.update_layout(title="the weight, corrected day after day (press Play)")
    fig.update_xaxes(title="correction round"); fig.update_yaxes(title="weight on occupancy")
    style_(fig, 380); animate_(fig, S.line_grow(np.arange(len(ws)), np.array(ws), POS), ms=90)
    st.plotly_chart(fig, use_container_width=True)
    c = st.columns(3)
    c[0].metric("Starting error", f"{abs(start_w-true_w):.2f}")
    c[1].metric("Error after 24 rounds", f"{abs(ws[-1]-true_w):.3f}")
    c[2].metric("Correction strength", f"{lr:.2f}")
    st.write("")
    if lr > 0.45:
        st.warning("Correct too hard and the weight overshoots and swings back — the same thing that "
                   "happens when a setpoint is over-adjusted during commissioning.")
    elif lr < 0.06:
        st.warning("Correct too gently and it is still drifting after two cooling seasons.")
    else:
        st.success("Steady correction converges. That is the whole learning loop: **predict → compare → "
                   "measure the error → adjust → repeat**.")


# ================================================================ 10 · the CNN
def render_cnn_journey(style_, animate_):
    st.title("Inside the CNN — reading the floor plate")
    st.markdown("#### A small filter slides over the plate and reports where its pattern occurs.")
    st.write("")
    kind = st.selectbox("Plate", KINDS, index=2)
    img = make_floor(kind)

    st.markdown("##### Step 1 — the raw plate the camera sends")
    st.plotly_chart(heat(img, title="input · 64 × 64 temperatures", h=330), use_container_width=True)
    st.write("")

    st.markdown("##### Step 2 — early filters: where does temperature change sharply?")
    kv = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], float)
    kb = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], float)
    c1, c2, c3 = st.columns(3)
    for col, k, name in ((c1, kv, "vertical edges"), (c2, kv.T, "horizontal edges"),
                         (c3, kb, "blobs & spots")):
        with col:
            st.plotly_chart(heat(np.abs(_conv2d(img, k)), title=name, h=250),
                            use_container_width=True)
    st.caption("The **blob** filter is the telling one: a person is a compact spot, while sunlight is a "
               "broad band with almost no local contrast. Nobody wrote that in — a trained CNN learns "
               "filters like these from labelled plates.")
    st.write("")

    st.markdown("##### Step 3 — deeper layers combine edges into shapes")
    deep = _conv2d(np.abs(_conv2d(img, kb)), np.ones((5, 5)) / 25.0)
    d1, d2 = st.columns(2)
    with d1:
        st.plotly_chart(heat(deep, title="a deeper feature map — regions, not pixels", h=300),
                        use_container_width=True)
    with d2:
        st.markdown(f"<div style='background:{PANEL};border-radius:4px;padding:16px;height:100%'>"
                    f"<b style='color:{TECH}'>What just happened</b>"
                    f"<ul style='color:{MUTED};font-size:14px;line-height:1.8'>"
                    f"<li>Early layers respond to <b>edges</b> — temperature steps.</li>"
                    f"<li>Later layers combine them into <b>compact blobs</b> and separate those from "
                    f"<b>broad bands</b>.</li>"
                    f"<li>Because the filter <b>slides</b>, a cluster is found wherever it sits.</li>"
                    f"<li>The final layer counts the blobs into a class.</li></ul></div>",
                    unsafe_allow_html=True)
    st.write("")

    st.markdown("##### Step 4 — the grade")
    scores = {"empty": (0.05, "empty"), "occupied": (0.88, "occupied"),
              "crowded": (0.94, "crowded"), "solar": (0.07, "empty — it is the façade"),
              "heat_leak": (0.09, "empty — it is the wall")}
    p, label = scores[kind]
    fig = go.Figure(go.Bar(x=["floor is in use"], y=[p], marker_color=RED if p > 0.5 else GREEN,
                           text=[f"{p:.0%}"], textposition="outside"))
    fig.update_yaxes(range=[0, 1.15], title="probability")
    fig.update_layout(title=f"CNN output — {label}")
    st.plotly_chart(style_(fig, 280), use_container_width=True)
    st.success("The mean-temperature rule could not tell a crowded floor from a sunlit empty one. The CNN "
               "separates them because it learned the **pattern**, not a summary number.")


# ================================================================ 11 · locating
def render_occupancy_locate(style_, animate_):
    st.title("Which part of the floor is in use? — Grad-CAM")
    st.markdown("#### A class does not set back a zone. A location does.")
    st.write("")
    kind = st.selectbox("Plate", KINDS, index=2)
    img, cam = make_floor(kind), people_cam(kind)
    blend = st.slider("Overlay strength", 0.0, 1.0, 0.6, 0.05)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(heat(img, title="camera frame · 64 × 64", h=340), use_container_width=True)
        st.caption("What the camera sends.")
    with c2:
        over = np.clip((1 - blend) * img + blend * cam, 0, 1)
        st.plotly_chart(heat(over, title="Grad-CAM — where the network looked", h=340,
                             colorscale="Turbo"), use_container_width=True)
        st.caption("Bright means that region drove the decision.")
    st.write("")
    if kind in ("occupied", "crowded"):
        st.error("**In use — the map concentrates on the people clusters**, not on the south façade or the "
                 "riser core. Those are warm in every frame, including empty ones, so they carry no "
                 "evidence.")
        st.info("That is the instruction: *this zone is occupied and that one is not — set back the empty "
                "one and ventilate this one for the people actually here.*")
    else:
        st.success("**Empty — the map stays low over the whole plate.** The warm façade and the leaky wall "
                   "do not attract it, because they look the same whether or not anybody is in.")
    st.write("")
    st.markdown(f"<div style='border-left:3px solid {TECH};padding:10px 0 10px 16px;font-size:15px;"
                f"color:{TEXT};line-height:1.7'><b>Why this matters here more than usual.</b> A whole-floor "
                f"class would set back a floor with one busy corner. A location lets the plant serve the "
                f"corner and stand down the rest — which is where the saving actually is.</div>",
                unsafe_allow_html=True)


# ================================================================ 12 · the engine
def render_fusion_engine(style_):
    st.title("The building intelligence engine")
    st.markdown("#### Three model outputs, one ranked action — and comfort can always veto.")
    st.caption("This is the product. Everything before it existed to fill in these rows.")
    st.write("")
    rows = [
        dict(z="North — open plan", met=31.4, pred=18.2, cam="empty (94%)", ppl=6, ppd=5.2,
             act="Setback to 27 °C, outside air to minimum", save=13.2, pr="HIGH"),
        dict(z="East — meeting rooms", met=15.1, pred=12.6, cam="occupied (88%)", ppl=38, ppd=6.8,
             act="Ventilate for the people present (CO₂-led), not for 200", save=2.7, pr="MEDIUM"),
        dict(z="South — sunlit bay", met=27.0, pred=26.4, cam="empty (91%)", ppl=9, ppd=9.4,
             act="Setback — the load is façade, not people", save=11.3, pr="HIGH"),
        dict(z="West — trading floor", met=34.2, pred=33.8, cam="crowded (96%)", ppl=172, ppd=11.6,
             act="Do NOT reduce — comfort is already at the limit", save=0.0, pr="COMFORT"),
    ]
    colr = {"HIGH": RED, "MEDIUM": AMBER, "COMFORT": TECH, "LOW": GREEN}
    for r in rows:
        saving = f" — saves {r['save']:.1f} kW" if r["save"] else ""
        st.markdown(
            f"<div style='background:{PANEL};border-left:5px solid {colr[r['pr']]};border-radius:4px;"
            f"padding:14px 18px;margin:8px 0'>"
            f"<div style='display:flex;justify-content:space-between;align-items:baseline'>"
            f"<b style='color:{TEXT};font-size:17px'>{r['z']}</b>"
            f"<span style='color:{colr[r['pr']]};font-size:12px;letter-spacing:.14em'>{r['pr']}</span>"
            f"</div><span style='color:{MUTED};font-size:14px'>"
            f"⚡ metered <b style='color:{POS}'>{r['met']:.1f} kW</b> vs predicted {r['pred']:.1f} "
            f"&nbsp;·&nbsp; 📷 camera: {r['cam']} &nbsp;·&nbsp; 👥 {r['ppl']} people "
            f"&nbsp;·&nbsp; 🧍 PPD {r['ppd']:.1f}%</span><br>"
            f"<span style='color:{GREEN};font-size:15px'>▸ {r['act']}{saving}</span></div>",
            unsafe_allow_html=True)
    st.write("")
    st.divider()
    st.markdown("### Where each column came from")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div style='background:{PANEL};border-top:3px solid {POS};border-radius:4px;padding:14px;"
                f"height:100%'><b style='color:{POS}'>⚡ Predicted kW</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>Random Forest on the nine BMS channels: what "
                f"this interval should have drawn. Metered minus predicted is the excess.</span></div>",
                unsafe_allow_html=True)
    c2.markdown(f"<div style='background:{PANEL};border-top:3px solid {TECH};border-radius:4px;padding:14px;"
                f"height:100%'><b style='color:{TECH}'>📷 Camera grade</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>CNN class plus Grad-CAM location. The only "
                f"column that can tell an empty sunlit bay from a busy one.</span></div>",
                unsafe_allow_html=True)
    c3.markdown(f"<div style='background:{PANEL};border-top:3px solid {GREEN};border-radius:4px;padding:14px;"
                f"height:100%'><b style='color:{GREEN}'>🧍 PPD</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>ISO 7730 comfort index. It has a veto: it can "
                f"only ever block a saving, never create one.</span></div>", unsafe_allow_html=True)
    st.write("")
    st.success("**Numbers say how much is being spent; the camera says whether anyone is there; comfort "
               "says whether you are allowed to act.** Fusion is what turns three outputs into one "
               "instruction.")
    st.info("Note the West row. The model found no saving there and said so. **A system that always finds "
            "a saving is not measuring anything.**")


# ================================================================ 13 · the pipeline
def render_pipeline(style_, animate_):
    st.title("The whole system, start to finish")
    st.markdown("#### Every stage of the course, and what feeds what.")
    st.write("")
    nodes = [
        (0.6, 5.2, "🏢 Floor plate", AMBER), (0.6, 3.2, "📷 Ceiling camera", AMBER),
        (2.6, 5.2, "📟 BMS channels", AMBER), (2.6, 3.2, "🖼️ Plates", AMBER),
        (4.6, 5.2, "🧹 Clean", TECH), (4.6, 3.2, "🖼️ Plates", TECH),
        (6.4, 5.2, "📐 Scale", TECH),
        (8.2, 5.2, "🌲 Random Forest", POS), (8.2, 3.2, "🧩 CNN", POS),
        (10.0, 4.2, "🔗 Fusion + PPD veto", GREEN), (11.9, 4.2, "📉 Dashboard", GREEN),
    ]
    edges = [(0, 2), (1, 3), (2, 4), (3, 5), (4, 6), (6, 7), (5, 8), (7, 9), (8, 9), (9, 10)]
    fig = go.Figure()
    for a, b in edges:
        fig.add_annotation(x=nodes[b][0] - 0.5, y=nodes[b][1], ax=nodes[a][0] + 0.5, ay=nodes[a][1],
                           xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2,
                           arrowsize=1.2, arrowwidth=2, arrowcolor="#3a4655", text="")
    for x, y, label, c in nodes:
        fig.add_shape(type="rect", x0=x - 0.9, x1=x + 0.9, y0=y - 0.5, y1=y + 0.5,
                      line=dict(color=c, width=2), fillcolor=PANEL)
        fig.add_annotation(x=x, y=y, text=f"<b>{label}</b>", showarrow=False,
                           font=dict(size=12, color=TEXT))
    fig.add_annotation(x=1.6, y=6.2, text="THE NUMBERS PATH", showarrow=False,
                       font=dict(size=11, color=POS))
    fig.add_annotation(x=1.6, y=2.2, text="THE IMAGE PATH", showarrow=False,
                       font=dict(size=11, color=AMBER))
    fig.update_xaxes(visible=False, range=[-0.6, 13.1])
    fig.update_yaxes(visible=False, range=[1.6, 6.7])
    fig.update_layout(title="sensors → data → ML + DL → fusion → dashboard")
    st.plotly_chart(style_(fig, 420), use_container_width=True)
    st.write("")
    st.markdown("### Read it as a chain, not a diagram")
    st.markdown("""
- The **numbers path** and the **image path** stay separate until fusion. They have to: one has named
  columns, the other does not.
- Cleaning sits *before* both. A stuck CO₂ sensor that survives it becomes a false setback four stages
  later, and a comfort complaint the week after.
- **The comfort index sits at fusion, not at the end.** It is a veto on the action, not a report on it.
- The dashboard converts the action into the building's own units — kWh, carbon, cost and PPD.
    """)
    st.info("Everything in this course is one of those boxes. If a stage feels abstract, find it here and "
            "ask what would break downstream without it.")
