"""
Story stages for the AI for Sustainable Manufacturing course.
=============================================================
The narrative beats that make AI inevitable for a Mechanical / Manufacturing
Engineering student who has never met it:

  in-production   - a plant wastes energy every hour, reviewed once a month.
  enter-ai        - engineer + meters. Not a replacement: watch always, not on a calendar.
  reading         - one production hour. The plant's state BECOMES a row of readings.
  two-records     - readings vs a thermal frame. Can one model do both?
  thermal-problem - a grid of temperatures. Which pixel is the leak? None.
  handmade        - reduce the frame to mean temperature by hand. Watch it miss.
  why-dl          - therefore: Deep Learning. Plus the feature ladder.
  engineer-brain  - how an energy auditor decides -> that IS a neuron.
  learning-loop   - predict -> measure -> adjust -> repeat, before terminology.
  cnn-journey     - filters slide over the frame and learn the leak pattern.
  leak-locate     - a CNN calls the leak AND shows where it looked (Grad-CAM).
  audit           - an energy audit. The confusion matrix emerges from it.
  fusion-engine   - the product: check this fitting on line 3, this shift.
  pipeline        - the whole system, start to finish.

The thermal frames are fully synthetic (numpy), rendered as heatmaps. No image
assets, no torch: pure illustration, consistent with the notebook.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from numpy.lib.stride_tricks import sliding_window_view

BG, PANEL = "#0e1117", "#161b22"
POS, NEG = "#4fc3f7", "#ff8a65"
GREEN, AMBER, RED = "#66bb6a", "#ffb74d", "#ef5350"
TECH = "#ba68c8"
MUTED, TEXT = "#8b949e", "#e6edf3"

SPEC_LIMIT = 2.00        # kWh per unit above which an hour counts as wasteful
GRID_KG = 0.72           # kg CO2 per kWh drawn from the grid
BASELOAD, LOAD_LIN, LOAD_SQ = 36.0, 0.30, 0.0135   # mirrors app._energy_for


# ----------------------------------------------------------------------------
# ANIMATION HELPERS  — turn a finished chart into a "press Play" reveal.
# _line_grow  : draw trace-0 (a line) on left-to-right.
# _bars_grow  : grow every bar up from zero together.
# The initial figure still shows the final state; Play replays the build.
# ----------------------------------------------------------------------------
def _line_grow(x, y, color, width=3, nf=26):
    x = np.asarray(x); y = np.asarray(y); n = len(x)
    ks = sorted(set(list(range(2, n + 1, max(1, n // nf))) + [n]))
    return [go.Frame(data=[go.Scatter(x=x[:k], y=y[:k], mode="lines",
                                      line=dict(color=color, width=width))],
                     name=str(k)) for k in ks]


def _bars_grow(specs, steps=14):
    frames = []
    for s in range(1, steps + 1):
        t = s / steps
        data = [go.Bar(x=sp["x"], y=list(np.asarray(sp["y"], float) * t),
                       marker_color=sp["color"], name=sp.get("name"),
                       text=(sp.get("text") if s == steps else None),
                       textposition="outside") for sp in specs]
        frames.append(go.Frame(data=data, name=str(s)))
    return frames


# ================================================================ the waste curve (echo of app.py)
def _leak_curve(hours, start=180, rate=0.0016, seed=0):
    """A compressed-air leak opening up part-way through the month and growing.
    Returns leak severity in 0..1 for every hour."""
    t = np.arange(hours)
    sev = np.clip((t - start) * rate, 0, 0.9)
    return sev, t


def _energy_from(leak, load=70.0, idle=8.0, ambient=24.0):
    """Hourly kWh for a given leak severity — the same relationship app.py uses."""
    return BASELOAD + LOAD_LIN * load + LOAD_SQ * load ** 2 \
        + 42.0 * np.asarray(leak, float) + 0.22 * idle \
        + 0.55 * np.clip(ambient - 24.0, 0, None)


# ================================================================ synthetic thermal frames
@st.cache_data(show_spinner=False)
def make_thermal(kind="normal", size=64, seed=0):
    """An equipment surface as a normalised temperature grid (0 = cold, 1 = hot).

    normal      - even warm surface, mild gradient.
    leak        - compressed-air leak: a COLD jet cone spreading from a fitting.
    hotspot     - overheated motor bearing: a small BRIGHT disc.
    insulation  - heat loss through failed lagging: a broad warm patch (a defect).
    sunlit      - sunlight on the wall: a broad warm patch (NOT a defect).

    The means are deliberately arranged so that no single threshold on average
    temperature separates the defects from the sound cases.
    """
    # NOTE: Python hashes strings with a per-process random seed, so seeding from
    # hash(kind) would give different frames on every run. Use an explicit table.
    _KS = {"normal": 0, "leak": 1, "hotspot": 2, "insulation": 3, "sunlit": 4}
    rng = np.random.default_rng(seed*7 + _KS.get(kind, 5))
    Y, X = np.mgrid[0:size, 0:size]
    img = 0.50 + rng.normal(0, 0.035, (size, size))       # warm housing + sensor noise
    img += 0.03 * np.sin(2 * np.pi * Y / 40.0)            # gentle vertical gradient

    if kind == "leak":
        # a cold jet spreading from a fitting near the left edge
        cy, cx = 30.0, 14.0
        dx = np.clip(X - cx, 0, None)
        halfw = 0.9 + 0.30 * dx
        cone = np.exp(-((Y - cy) ** 2) / (2 * halfw ** 2)) * np.exp(-dx / 34.0)
        cone[X < cx] = 0.0
        img = img - 0.50 * cone
    elif kind == "hotspot":
        cy, cx, r = 26.0, 40.0, 5.0
        img = img + 0.46 * np.exp(-(((Y - cy) ** 2 + (X - cx) ** 2) / (2 * r ** 2)))
    elif kind == "insulation":
        cy, cx = 40.0, 44.0
        img = img + 0.13 * np.exp(-(((Y - cy) ** 2 + (X - cx) ** 2) / (2 * 19.0 ** 2)))
    elif kind == "sunlit":
        cy, cx = 20.0, 22.0
        img = img + 0.14 * np.exp(-(((Y - cy) ** 2 + (X - cx) ** 2) / (2 * 20.0 ** 2)))
    return np.clip(img, 0, 1)


@st.cache_data(show_spinner=False)
def make_pipe_run(leaking=True, size=72, seed=1):
    """A compressed-air pipe run across an equipment wall, top view. A leak plume
    spreads from one fitting. Returns the frame and a Grad-CAM-style heat map."""
    rng = np.random.default_rng(seed)
    Y, X = np.mgrid[0:size, 0:size]
    img = 0.50 + rng.normal(0, 0.03, (size, size))
    # the warm pipe itself: a horizontal band
    img += 0.16 * np.exp(-((Y - 26.0) ** 2) / (2 * 2.6 ** 2))
    # two fittings
    for fx in (20.0, 48.0):
        img += 0.10 * np.exp(-(((Y - 26.0) ** 2 + (X - fx) ** 2) / (2 * 3.0 ** 2)))
    cam = np.full((size, size), 0.05)
    if leaking:
        cy, cx = 26.0, 48.0
        dy = np.clip(Y - cy, 0, None)                    # the jet blows downward
        halfw = 1.2 + 0.34 * dy
        cone = np.exp(-((X - cx) ** 2) / (2 * halfw ** 2)) * np.exp(-dy / 26.0)
        cone[Y < cy] = 0.0
        img = img - 0.46 * cone
        cam = 0.05 + 0.95 * (cone / (cone.max() + 1e-9))
    return np.clip(img, 0, 1), cam


def _conv2d(img, k):
    win = sliding_window_view(img, k.shape)
    return np.einsum("ijkl,kl->ij", win, k)


def _heat(z, colorscale="Inferno", h=320, title="", showscale=False):
    fig = go.Figure(go.Heatmap(z=z, colorscale=colorscale, showscale=showscale))
    fig.update_layout(title=title, paper_bgcolor=BG, plot_bgcolor=BG, font_color=TEXT,
                      margin=dict(l=10, r=10, t=44, b=10), height=h)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, autorange="reversed", scaleanchor="x")
    return fig


# ================================================================ 1 · the plant in production
def render_in_production(style, animate):
    st.title("A plant under load — consumption never pauses")
    st.markdown("#### Energy is wasted every hour. The bill only reports it every month.")
    st.caption("Set how often the plant reviews its energy use, and watch how much power a leak burns "
               "before anyone reads about it.")

    hours = 720                                    # one month of three-shift operation
    sev, t = _leak_curve(hours, start=180, rate=0.0016)
    kwh = _energy_from(sev)
    base = float(_energy_from(0.0))
    onset = int(np.argmax(sev > 0.05)) if (sev > 0.05).any() else hours

    days = st.slider("Days between energy reviews", 1, 30, 30, 1)
    review_pts = np.arange(0, hours, days * 24)
    seen = review_pts[review_pts >= onset]
    detected = int(seen[0]) if len(seen) else hours
    unseen_kwh = float(np.sum(kwh[onset:detected] - base))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=kwh, mode="lines", line=dict(color=POS, width=3),
                             name="metered kWh"))
    fig.add_hline(y=base, line=dict(color=GREEN, width=2, dash="dash"),
                  annotation_text="what the hour should cost", annotation_position="bottom left")
    fig.add_trace(go.Scatter(x=review_pts, y=kwh[np.clip(review_pts, 0, hours - 1)],
                             mode="markers", marker=dict(size=13, color=AMBER, symbol="triangle-down"),
                             name="energy review"))
    if onset < hours:
        fig.add_vrect(x0=onset, x1=detected, fillcolor=RED, opacity=0.12, line_width=0)
        fig.add_annotation(x=(onset + detected) / 2, y=base - 4,
                           text="leak running, unseen", showarrow=False,
                           font=dict(color=RED, size=12))
    fig.update_layout(title="hourly consumption over one month, with reviews marked (press Play)")
    fig.update_xaxes(title="hour of the month")
    fig.update_yaxes(title="kWh per hour")
    style(fig, 400); animate(fig, _line_grow(t, kwh, POS), ms=45)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Leak opens up", f"hour {onset}")
    c2.metric("First review that sees it", f"hour {detected}")
    c3.metric("Energy burned unseen", f"{unseen_kwh:,.0f} kWh",
              f"{unseen_kwh * GRID_KG / 1000:,.1f} t CO₂", delta_color="inverse")

    st.markdown("### So — can you just review the meters more often?")
    if st.button("Answer", type="primary"):
        st.error("**Not by hand.** A mid-size plant has hundreds of metered points across three shifts. "
                 "Reviewing them daily is a full-time job that still misses a leak that opens the hour "
                 "after the review — and the reviewer has no way of knowing what each hour *should* have "
                 "cost.")
        st.info("👉 So the fix is not a tighter review schedule — it is a system that watches every hour, "
                "knows what normal looks like for that load and weather, and flags the excess while it is "
                "still running. The engineer stays in charge; the continuous watch is what AI takes off "
                "their plate.")


# ================================================================ 2 · the sustainability monitor
def render_enter_ai(style, animate):
    st.title("A plant that reports itself — the sustainability monitor")
    st.markdown("#### Same machines, same output. Review on a calendar, or watch continuously?")
    hours = 720
    sev, t = _leak_curve(hours, start=200, rate=0.0018)
    kwh = _energy_from(sev)
    base = float(_energy_from(0.0))
    onset = int(np.argmax(sev > 0.05)) if (sev > 0.05).any() else hours
    review_pts = np.arange(0, hours, 720)          # once a month, with the bill
    seen = review_pts[review_pts >= onset]
    detected = int(seen[0]) if len(seen) else hours

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=kwh, mode="lines", line=dict(color=POS, width=2.5),
                             name="continuous monitoring"))
    fig.add_hline(y=base, line=dict(color=GREEN, width=2, dash="dash"),
                  annotation_text="expected for this load", annotation_position="bottom left")
    if onset < hours:
        fig.add_trace(go.Scatter(x=[onset], y=[kwh[onset]], mode="markers",
                                 marker=dict(size=16, color=POS, symbol="circle-open",
                                             line=dict(width=3)), name="monitor catches it here"))
        fig.add_trace(go.Scatter(x=[min(detected, hours - 1)], y=[kwh[min(detected, hours - 1)]],
                                 mode="markers", marker=dict(size=16, color=RED, symbol="x"),
                                 name="the bill catches it here"))
    fig.update_layout(title="when each approach first notices the waste (press Play)")
    fig.update_xaxes(title="hour of the month")
    fig.update_yaxes(title="kWh per hour")
    style(fig, 400); animate(fig, _line_grow(t, kwh, POS, width=2.5), ms=45)
    st.plotly_chart(fig, use_container_width=True)

    lag = max(0, min(detected, hours) - onset)
    wasted = float(np.sum(kwh[onset:min(detected, hours)] - base))
    c1, c2 = st.columns(2)
    c1.metric("Detection lag — monthly bill", f"{lag} hours", f"{wasted:,.0f} kWh lost",
              delta_color="inverse")
    c2.metric("Detection lag — continuous monitor", "≈ 0 hours", f"-{lag} hours")
    st.success(f"The leak opens at hour {onset}. Nobody reads about it until the bill, {lag} hours later, "
               f"by which time {wasted:,.0f} kWh — about {wasted * GRID_KG / 1000:,.1f} t of CO₂ — has "
               f"already been paid for. The monitor flags the excess the hour it appears.")

    st.markdown("### Manufacturing Engineer **+** AI. Never engineer *vs* AI.")
    a, b = st.columns(2)
    a.markdown("**The engineer stays in charge of**\n\n- diagnosing the actual cause\n- judging whether a hot "
               "pipe is a fault or a design feature\n- hearing a bearing, feeling a vibration\n- authorising "
               "a shutdown or a capital spend\n- process knowledge — which AI has none of")
    b.markdown("**Where one person needs a hand**\n\n- watching every machine, every hour\n- separating a hot "
               "afternoon from real waste\n- comparing this hour against thousands of past ones\n- reading a "
               "thermal frame pixel by pixel\n- never looking away")
    st.info("The system's job is not to decide. It hands the engineer **the machines that matter right now** "
            "and the excess worth chasing, so a person makes the call. The engineer is superior — AI just "
            "eases the load one pair of eyes cannot carry across three shifts.")


# ================================================================ 3 · one production hour
def render_reading(get_data, style, animate):
    st.title("One production hour — how a factory's state becomes data")
    st.markdown("#### The model will never walk the shop floor.")
    d = get_data()
    row = d["dirty"].iloc[5]

    st.markdown("At the end of each hour the system reads every channel at once. "
                "Watch what actually reaches the model:")
    steps = [
        ("🏭  The real plant", "Machines cut, ovens hold temperature, a fitting hisses, a line waits for "
                              "material. All of it happening at once.", MUTED),
        ("📡  Meters read it", "Load, motor temperature, air pressure and flow, idle share, units, "
                               "material, ambient — each one number. No context, no cause.", POS),
        ("🌡️  The camera captures it", "A thermal frame of the compressor room. Not a diagnosis — a grid "
                                        "of temperatures.", AMBER),
        ("📄  It becomes one row", "This row of readings, and the kWh and CO₂ that hour produced, is the "
                                   "*entire* factory as far as the model is concerned.", GREEN),
    ]
    i = st.slider("Walk through the hour", 1, 4, 1)
    for k, (t, txt, c) in enumerate(steps, start=1):
        if k <= i:
            st.markdown(f"<div style='padding:12px 16px;margin:6px 0;border-radius:10px;"
                        f"border-left:4px solid {c};background:{PANEL};color:{TEXT}'>"
                        f"<b>{t}</b><br><span style='color:{MUTED}'>{txt}</span></div>",
                        unsafe_allow_html=True)
    if i == 4:
        st.markdown("##### What each channel records, and why it matters")
        st.dataframe(pd.DataFrame([
            ["⚙️ Machine load", "Drive / PLC tag", "%", "How hard the line is working — the biggest driver of draw"],
            ["🌡️ Motor temperature", "Thermocouple", "°C", "Rises with load, and with a compressor working against a leak"],
            ["🎚️ Air pressure", "Line pressure sensor", "bar", "Falls when compressed air escapes somewhere"],
            ["💨 Air flow", "Flow meter", "m³/h", "Rises at constant load when there is a leak"],
            ["⏸️ Idle share", "Machine runtime log", "%", "Power drawn while producing nothing"],
            ["📦 Units produced", "Production counter", "units/h", "The output the energy is supposed to buy"],
            ["🧱 Material used", "Weighing / MES", "kg", "Input mass — scrap shows up here"],
            ["🏭 Ambient temperature", "Hall sensor", "°C", "Drives ventilation load — must be separated from waste"],
        ], columns=["Channel", "Source", "Unit", "What it tells you"]),
            use_container_width=True, hide_index=True)

        st.markdown("##### One hour = one row of those numbers")
        cols = ["load_pct", "motor_temp_c", "air_pressure_bar", "air_flow_m3h",
                "idle_pct", "units_per_hr", "material_kg", "ambient_temp_c"]
        st.dataframe(pd.DataFrame([row[cols].values], columns=[
            "Load (%)", "Motor (°C)", "Pressure (bar)", "Flow (m³/h)",
            "Idle (%)", "Units/h", "Material (kg)", "Ambient (°C)"]),
            use_container_width=True, hide_index=True)
        st.info("The model never walks the floor — it sees only this row. If the row is wrong, the "
                "prediction is wrong, and the model has no way to notice. That is why the next stages are "
                "about the data, not the model.")


# ================================================================ 4 · reading vs thermal frame
def render_two_records(style, animate):
    st.title("Two kinds of record — a meter reading and a thermal frame")
    st.markdown("#### The same hour produces both. They are not the same problem.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div style='border-top:3px solid {POS};background:{PANEL};border-radius:10px;"
                    f"padding:14px'><b style='color:{POS}'>📊 The meter log</b><br>"
                    f"<span style='color:{MUTED};font-size:13px'>Eight values an engineer named and gave "
                    f"units. Each already means something.</span></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({
            "Channel": ["Load", "Motor temp", "Air pressure", "Air flow", "Idle",
                        "Units", "Material", "Ambient"],
            "Value": ["72 %", "58 °C", "5.9 bar", "68 m³/h", "9 %", "84 units/h", "79 kg", "26 °C"],
        }), use_container_width=True, hide_index=True, height=330)
        st.caption("**8 named numbers.** A human can read it.")
    with c2:
        st.markdown(f"<div style='border-top:3px solid {AMBER};background:{PANEL};border-radius:10px;"
                    f"padding:14px'><b style='color:{AMBER}'>🌡️ The raw thermal frame</b><br>"
                    f"<span style='color:{MUTED};font-size:13px'>Thousands of temperatures. Nothing in it "
                    f"is named.</span></div>", unsafe_allow_html=True)
        st.plotly_chart(_heat(make_thermal("leak"), title="one surface · 64 × 64 temperatures", h=330),
                        use_container_width=True)
        st.caption("**4,096 unnamed numbers.** The leak is in the pattern.")

    st.info("One hour, two records. The Random Forest handles the eight readings. It cannot be pointed at "
            "4,096 unnamed pixels at all, which is why deep learning is needed later.")


# ================================================================ 5 · the raw thermal frame
def render_thermal_problem(style, animate):
    st.title("What the thermal camera actually sends")
    st.markdown("#### You *see* the leak instantly. Now find it in the numbers.")
    kind = st.selectbox(
        "Choose a surface",
        ["leak", "hotspot", "insulation", "sunlit", "normal"], index=0,
        format_func=lambda k: {
            "leak": "Compressed-air leak (cold plume) — defect",
            "hotspot": "Overheated bearing (bright disc) — defect",
            "insulation": "Failed lagging (broad warm patch) — defect",
            "sunlit": "Sunlight on the wall (broad warm patch) — sound",
            "normal": "Sound equipment — nothing wrong",
        }[k])
    img = make_thermal(kind)
    st.plotly_chart(_heat(img, title=f"one thermal frame · {img.size:,} temperature values", h=380),
                    use_container_width=True)
    st.caption("Every pixel is just a normalised temperature between 0 and 1. None of them is labelled "
               "'leak'. Compare **failed lagging** with **sunlight** — they look almost identical, and "
               "only one is a defect.")

    if st.button("Where is the energy loss?", type="primary"):
        st.error("It is not any single pixel. A leak is a **cold cone spreading from a fitting**; a failing "
                 "bearing is a **compact bright disc**; failed lagging is a **broad warm region**. Each is a "
                 "*pattern* spread over hundreds of pixels — no one number holds it.")
        st.info("At the meter reading an engineer had already named load and flow, so the Random Forest had "
                "features to weigh. Here nothing is pre-named. There is no column called 'plume' — only its "
                "shape, spread across the whole frame.")


# ================================================================ 6 · mean temperature by hand
def render_handmade(style, animate):
    st.title("The thermal rulebook, by hand")
    st.markdown("#### Reduce the frame to one number, set an alarm limit, watch it miss.")
    st.caption("The standard shortcut: take the average surface temperature and alarm on anything too hot. "
               "It works on an obviously glowing furnace. The problem is the cold leak plume and the sunlit "
               "wall.")

    cases = [("Sound equipment", make_thermal("normal"), GREEN),
             ("Sunlit wall (sound)", make_thermal("sunlit"), GREEN),
             ("Air leak (defect)", make_thermal("leak"), RED),
             ("Hot bearing (defect)", make_thermal("hotspot"), RED),
             ("Failed lagging (defect)", make_thermal("insulation"), RED)]
    means = [(n, float(im.mean()), c) for n, im, c in cases]

    thr = st.slider("Set the mean-temperature alarm limit", 0.46, 0.60, 0.52, 0.005)
    fig = go.Figure()
    for n, v, c in means:
        fig.add_trace(go.Bar(x=[n], y=[v], marker_color=c, showlegend=False,
                             text=f"{v:.3f}", textposition="outside"))
    fig.add_hline(y=thr, line=dict(color=POS, width=2, dash="dash"),
                  annotation_text=f"alarm above {thr:.3f}", annotation_position="top left")
    fig.update_layout(title="one number per frame — can a line separate defect from sound?")
    fig.update_yaxes(title="mean surface temperature (normalised)", range=[0, 0.75])
    style(fig, 380)
    animate(fig, _bars_grow([dict(x=[n], y=[v], color=c, text=f"{v:.3f}") for n, v, c in means]), ms=90)
    st.plotly_chart(fig, use_container_width=True)

    missed = [n for n, v, c in means if c == RED and v <= thr]
    false_al = [n for n, v, c in means if c == GREEN and v > thr]
    a, b = st.columns(2)
    a.metric("Defects missed", len(missed), ", ".join(missed) or "none", delta_color="inverse")
    b.metric("Sound equipment alarmed", len(false_al), ", ".join(false_al) or "none",
             delta_color="inverse")
    st.warning("**Move the limit anywhere you like — you cannot win.** The air leak is *colder* than sound "
               "equipment, so raising the limit will never catch it. Failed lagging and sunlight sit at "
               "almost the same mean, so any limit that catches one alarms on the other. Averaging threw "
               "away the only thing that distinguishes them: the shape and position of the pattern.")
    st.error("Every hand-made image feature is a rule you must maintain, and each one discards most of the "
             "picture.")


# ================================================================ 7 · why deep learning
def render_why_dl(style):
    st.title("The rulebook runs out — therefore, deep learning")
    st.markdown("#### An experienced thermographer grades the frame instantly and cannot write down the rule.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div style='border-top:3px solid {RED};background:{PANEL};border-radius:10px;"
                    f"padding:16px;height:100%'><b style='color:{RED}'>Writing rules by hand</b>"
                    f"<ul style='color:{MUTED};font-size:14px;line-height:1.7'>"
                    f"<li>Every temperature limit is too tight or too loose</li>"
                    f"<li>One feature per rule, most of the frame thrown away</li>"
                    f"<li>Different for every machine, angle, season and emissivity</li>"
                    f"<li>You maintain it forever</li></ul></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='border-top:3px solid {GREEN};background:{PANEL};border-radius:10px;"
                    f"padding:16px;height:100%'><b style='color:{GREEN}'>Learning from examples</b>"
                    f"<ul style='color:{MUTED};font-size:14px;line-height:1.7'>"
                    f"<li>Show it labelled frames: leak, hotspot, sound</li>"
                    f"<li>It works out which patterns matter, by itself</li>"
                    f"<li>The whole frame is used, not one summary number</li>"
                    f"<li>A new machine means new examples, not new rules</li></ul></div>",
                    unsafe_allow_html=True)

    st.divider()
    st.markdown("### How a network gets from pixels to a diagnosis")
    st.caption("Nobody writes any of these steps. Each layer builds on the one before it, and the network "
               "discovers what each layer should look for.")

    ladder = [("🌡️", "Thermal frame", "4,096 raw temperatures", MUTED),
              ("📐", "Edges", "where temperature changes sharply", POS),
              ("🔥", "Hot & cold regions", "blobs and bands, not single pixels", AMBER),
              ("🌀", "Heat patterns", "a spreading cone, a compact disc", TECH),
              ("⚡", "Energy leak", "the diagnosis, with a location", GREEN)]
    cols = st.columns(len(ladder))
    for col, (ico, name, sub, c) in zip(cols, ladder):
        with col:
            st.markdown(
                f"<div style='border:1px solid #2b3440;border-top:3px solid {c};background:{PANEL};"
                f"border-radius:8px;padding:12px;text-align:center;height:100%'>"
                f"<div style='font-size:26px'>{ico}</div>"
                f"<b style='color:{c};font-size:13px'>{name}</b><br>"
                f"<span style='color:{MUTED};font-size:12px'>{sub}</span></div>",
                unsafe_allow_html=True)

    st.write("")
    st.success("**Machine Learning weights the features you name. Deep Learning finds the features you "
               "cannot name.** That single sentence is why this course has two halves — and why the meter "
               "log still belongs to the Random Forest.")


# ================================================================ 8 · how an auditor decides
def render_engineer_brain(style):
    st.title("How an energy auditor decides — and why that is a neuron")
    st.markdown("#### Weigh a few signals, add them up, make one call.")
    st.caption("Move the readings. The bar is the auditor's mental total; the line is where they call a leak.")

    c1, c2 = st.columns([1, 1.3])
    with c1:
        hiss = st.slider("Audible hiss at the fitting (0–10)", 0, 10, 6)
        drop = st.slider("Line-pressure drop (bar)", 0.0, 2.0, 0.8, 0.1)
        duty = st.slider("Compressor duty cycle (%)", 20, 100, 78, 1)
        night = st.slider("Flow during the night shift (m³/h)", 0, 60, 34, 1)
    weights = dict(hiss=0.55, drop=1.6, duty=0.035, night=0.055)
    contrib = {
        "Hiss": weights["hiss"] * hiss,
        "Pressure drop": weights["drop"] * drop,
        "Duty cycle": weights["duty"] * duty,
        "Night flow": weights["night"] * night,
    }
    total = sum(contrib.values()) - 6.0        # bias: the auditor's baseline scepticism

    with c2:
        fig = go.Figure()
        names = list(contrib)
        fig.add_trace(go.Bar(x=names, y=[contrib[n] for n in names],
                             marker_color=[POS, AMBER, TECH, GREEN],
                             text=[f"{contrib[n]:.1f}" for n in names], textposition="outside"))
        fig.update_layout(title=f"weighted evidence · total after baseline = {total:+.2f}")
        fig.update_yaxes(title="contribution to the call")
        st.plotly_chart(style(fig, 360), use_container_width=True)

    if total > 0:
        st.error(f"**Call: there is a leak.** Weighted total {total:+.2f} clears the threshold of 0.")
    else:
        st.success(f"**Call: no leak.** Weighted total {total:+.2f} sits below the threshold of 0.")

    st.markdown(
        f"<div style='border-left:3px solid {POS};padding:10px 0 10px 16px;font-size:16px;color:{TEXT};"
        f"line-height:1.7'>What you just moved was <b>w · x + b</b>. Each slider is an input <i>x</i>. "
        f"Each fixed multiplier is a weight <i>w</i>. The baseline scepticism is the bias <i>b</i>. "
        f"Comparing the total to zero is the activation. <b>That is a neuron</b> — and the only difference "
        f"in the machine version is that nobody chooses the weights: they are learned from the log.</div>",
        unsafe_allow_html=True)


# ================================================================ 9 · the learning loop
def render_learning_loop(style, animate):
    st.title("Learning from a missed leak")
    st.markdown("#### Predict, compare with the meter, adjust, repeat.")
    st.caption("The auditor starts with a bad guess about how much air flow matters. Each month's bill "
               "corrects it. Watch the weight walk towards the truth.")

    true_w = 3.4
    start_w = st.slider("Starting guess for the flow weight", 0.0, 8.0, 7.2, 0.1)
    lr = st.slider("How strongly to correct after each miss", 0.02, 0.6, 0.22, 0.02)
    n = 24

    w = start_w
    ws, errs = [w], []
    for _ in range(n):
        err = w - true_w                     # the signed error the bill reveals
        errs.append(abs(err))
        w = w - lr * 2 * err                 # nudge towards the truth
        ws.append(w)
    errs.append(abs(w - true_w))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(len(ws))), y=ws, mode="lines+markers",
                             line=dict(color=POS, width=3), name="the weight"))
    fig.add_hline(y=true_w, line=dict(color=GREEN, width=2, dash="dash"),
                  annotation_text="the weight that fits the plant", annotation_position="bottom right")
    fig.update_layout(title="the weight, corrected month after month (press Play)")
    fig.update_xaxes(title="correction round")
    fig.update_yaxes(title="weight on air flow")
    style(fig, 380); animate(fig, _line_grow(np.arange(len(ws)), np.array(ws), POS), ms=90)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Starting error", f"{abs(start_w - true_w):.2f}")
    c2.metric("Error after 24 rounds", f"{errs[-1]:.3f}")
    c3.metric("Correction strength", f"{lr:.2f}")
    if lr > 0.45:
        st.warning("Correct too hard and the weight overshoots past the truth and swings back. Same as "
                   "over-adjusting a set point during commissioning.")
    elif lr < 0.06:
        st.warning("Correct too gently and it is still drifting after two years of bills.")
    else:
        st.success("Steady correction converges. That is the entire learning loop: **predict → compare → "
                   "measure the error → adjust → repeat**. Nothing more mysterious than that.")

    st.info("A real network runs this loop over thousands of rows and every weight at once, thousands of "
            "times. The next page gives the correction its proper name: gradient descent.")


# ================================================================ 10 · inside the CNN
def render_cnn_journey(style, animate):
    st.title("Inside the CNN — reading the heat pattern")
    st.markdown("#### A small filter slides over the frame and reports where its pattern occurs.")

    kind = st.selectbox("Thermal frame", ["leak", "hotspot", "insulation", "normal"], index=0)
    img = make_thermal(kind)

    st.markdown("##### Step 1 — the raw frame the camera sends")
    st.plotly_chart(_heat(img, title="input · 64 × 64 temperatures", h=330), use_container_width=True)

    st.markdown("##### Step 2 — early filters: where does temperature change sharply?")
    kv = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], float)      # vertical edges
    kh = kv.T                                                        # horizontal edges
    kb = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], float)     # blob / centre-surround
    c1, c2, c3 = st.columns(3)
    for col, k, name in ((c1, kv, "vertical edges"), (c2, kh, "horizontal edges"),
                         (c3, kb, "blobs & spots")):
        with col:
            fm = np.abs(_conv2d(img, k))
            st.plotly_chart(_heat(fm, colorscale="Inferno", title=name, h=250),
                            use_container_width=True)
    st.caption("Each map is bright where that filter's pattern was found. Nobody wrote these into the "
               "network as rules — a trained CNN *learns* filters like these from labelled frames.")

    st.markdown("##### Step 3 — deeper layers combine edges into shapes")
    smooth = np.ones((5, 5)) / 25.0
    deep = _conv2d(np.abs(_conv2d(img, kb)), smooth)
    d1, d2 = st.columns(2)
    with d1:
        st.plotly_chart(_heat(deep, title="a deeper feature map — regions, not pixels", h=300),
                        use_container_width=True)
    with d2:
        st.markdown(f"<div style='background:{PANEL};border-radius:10px;padding:16px;height:100%'>"
                    f"<b style='color:{TECH}'>What just happened</b>"
                    f"<ul style='color:{MUTED};font-size:14px;line-height:1.8'>"
                    f"<li>Early layers respond to <b>edges</b> — temperature steps.</li>"
                    f"<li>Later layers combine edges into <b>regions and shapes</b> — a spreading cone, a "
                    f"compact disc, a broad band.</li>"
                    f"<li>Because the filter <b>slides</b>, the same pattern is found wherever it appears "
                    f"in the frame.</li>"
                    f"<li>The final layer weighs those shapes into one grade.</li></ul></div>",
                    unsafe_allow_html=True)

    st.markdown("##### Step 4 — the grade")
    scores = {"leak": (0.93, "Compressed-air leak"), "hotspot": (0.88, "Overheated bearing"),
              "insulation": (0.81, "Heat loss through lagging"), "normal": (0.07, "Sound equipment")}
    p, label = scores[kind]
    fig = go.Figure(go.Bar(x=["energy loss detected"], y=[p],
                           marker_color=RED if p > 0.5 else GREEN,
                           text=[f"{p:.0%}"], textposition="outside"))
    fig.update_yaxes(range=[0, 1.15], title="probability")
    fig.update_layout(title=f"CNN output — {label}")
    st.plotly_chart(style(fig, 280), use_container_width=True)
    st.success("The mean-temperature rule could not tell a leak from sunlight. The CNN separates them "
               "because it learned the **pattern**, not a summary number.")


# ================================================================ 11 · locating the loss
def render_leak_locate(style, animate):
    st.title("Where is the loss? — Grad-CAM on the pipe run")
    st.markdown("#### A probability does not raise a work order. A location does.")

    leaking = st.toggle("Show a leaking run", value=True)
    img, cam = make_pipe_run(leaking=leaking)
    blend = st.slider("Overlay strength", 0.0, 1.0, 0.6, 0.05)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(_heat(img, title="thermal frame · 72 × 72", h=340), use_container_width=True)
        st.caption("What the camera sends. Two fittings on one warm pipe run.")
    with c2:
        over = np.clip((1 - blend) * img + blend * cam, 0, 1)
        st.plotly_chart(_heat(over, colorscale="Turbo", title="Grad-CAM — where the network looked", h=340),
                        use_container_width=True)
        st.caption("Bright means that region drove the decision.")

    if leaking:
        st.error("**Leak detected — 94% confidence.** The heat map concentrates on the plume below the "
                 "downstream fitting, not on the warm pipe itself. The pipe is warm on every frame, "
                 "including sound ones, so it carries no evidence.")
        st.info("That is the work order: *fitting 2 on the compressed-air run, downstream side.* An "
                "engineer can walk to it, put a hand near it, and confirm in ten seconds.")
    else:
        st.success("**No leak — 6% confidence.** The map stays flat: nothing in the frame pushed the "
                   "network towards a leak.")

    st.markdown(
        f"<div style='border-left:3px solid {TECH};padding:10px 0 10px 16px;font-size:15px;color:{TEXT};"
        f"line-height:1.7'><b>How it works.</b> The last convolutional layer holds several feature maps. "
        f"Grad-CAM weights each map by how much it pushed the score towards 'leak', adds them up and "
        f"stretches the result back over the frame. The bright region is literally the evidence the "
        f"network used.</div>", unsafe_allow_html=True)


# ================================================================ 12 · the energy audit
def render_audit(get_data, get_models, style, animate):
    st.title("The energy audit — checking every claim")
    st.markdown("#### Predicted against metered, on hours the model has never seen.")
    d = get_data()
    rf, mlp = get_models()
    Xte, yte = d["Xte"], d["yte"]

    which = st.radio("Which model is being audited?", ["Random Forest", "Neural network (MLP)"],
                     horizontal=True)
    model = rf if which == "Random Forest" else mlp
    pred = model.predict(Xte)

    tp = int(np.sum((pred == 1) & (yte == 1)))
    fp = int(np.sum((pred == 1) & (yte == 0)))
    fn = int(np.sum((pred == 0) & (yte == 1)))
    tn = int(np.sum((pred == 0) & (yte == 0)))
    acc = (tp + tn) / max(1, len(yte))
    recall = tp / max(1, tp + fn)

    z = [[tn, fp], [fn, tp]]
    fig = go.Figure(go.Heatmap(
        z=z, x=["called efficient", "called wasteful"], y=["actually efficient", "actually wasteful"],
        colorscale=[[0, "#16202b"], [1, POS]], showscale=False,
        text=[[f"{tn}<br>correct", f"{fp}<br>false alarm"],
              [f"{fn}<br>MISSED WASTE", f"{tp}<br>caught"]],
        texttemplate="%{text}", textfont=dict(size=15)))
    fig.update_layout(title=f"{which} — {len(yte)} sealed hours")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(style(fig, 380), use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Accuracy", f"{acc:.1%}")
    c2.metric("Wasteful hours caught", f"{recall:.1%}")
    c3.metric("False alarms", fp)
    c4.metric("Missed waste", fn, delta_color="inverse")

    st.markdown("### The two errors do not cost the same")
    a, b = st.columns(2)
    a.markdown(f"<div style='background:{PANEL};border-left:4px solid {AMBER};border-radius:8px;"
               f"padding:14px'><b style='color:{AMBER}'>False alarm ({fp} hours)</b><br>"
               f"<span style='color:{MUTED}'>An engineer walks the line and finds nothing. Cost: one "
               f"hour of someone's time, and a little credibility.</span></div>", unsafe_allow_html=True)
    b.markdown(f"<div style='background:{PANEL};border-left:4px solid {RED};border-radius:8px;"
               f"padding:14px'><b style='color:{RED}'>Missed waste ({fn} hours)</b><br>"
               f"<span style='color:{MUTED}'>The leak keeps running until the bill. Cost: weeks of "
               f"compressed air, and the carbon that came with it.</span></div>", unsafe_allow_html=True)

    st.info("This is why accuracy alone is never reported. A model that calls every hour efficient would "
            "score well on a plant that is mostly efficient — and find nothing at all. **Recall on the "
            "wasteful hours is the number the project is judged on.**")


# ================================================================ 13 · the sustainability screen
def render_fusion_engine(style):
    st.title("The plant sustainability screen")
    st.markdown("#### Three model outputs, one ranked action list.")
    st.caption("This is the product. Everything before it existed to fill in these rows.")

    rows = [
        dict(line="Line 3 · compressed air", excess=41.0, cam="leak plume at fitting 2",
             anom=4.6, action="Isolate and reseal fitting 2", pr="HIGH"),
        dict(line="Line 1 · curing oven", excess=23.5, cam="broad warm band on door seal",
             anom=2.9, action="Replace door lagging at next changeover", pr="MEDIUM"),
        dict(line="Line 2 · drive motor", excess=11.2, cam="bright disc on drive-end bearing",
             anom=1.8, action="Schedule bearing inspection", pr="MEDIUM"),
        dict(line="Line 4 · packing", excess=6.4, cam="nothing found",
             anom=0.7, action="No action — within normal for this load", pr="LOW"),
    ]
    colr = {"HIGH": RED, "MEDIUM": AMBER, "LOW": GREEN}
    for r in rows:
        st.markdown(
            f"<div style='background:{PANEL};border-left:5px solid {colr[r['pr']]};border-radius:8px;"
            f"padding:14px 18px;margin:8px 0'>"
            f"<div style='display:flex;justify-content:space-between;align-items:baseline'>"
            f"<b style='color:{TEXT};font-size:17px'>{r['line']}</b>"
            f"<span style='color:{colr[r['pr']]};font-size:12px;letter-spacing:.14em'>{r['pr']}</span></div>"
            f"<span style='color:{MUTED};font-size:14px'>"
            f"⚡ <b style='color:{POS}'>{r['excess']:.1f} kWh/h</b> above expected &nbsp;·&nbsp; "
            f"🚩 anomaly score <b>{r['anom']:.1f}σ</b> &nbsp;·&nbsp; "
            f"🌡️ camera: {r['cam']}</span><br>"
            f"<span style='color:{GREEN};font-size:15px'>▸ {r['action']}</span></div>",
            unsafe_allow_html=True)

    st.divider()
    st.markdown("### Where each column came from")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div style='background:{PANEL};border-top:3px solid {POS};border-radius:8px;padding:14px;"
                f"height:100%'><b style='color:{POS}'>⚡ Excess kWh</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>Random Forest on the eight meter channels: "
                f"what this hour should have cost, minus what it did cost.</span></div>",
                unsafe_allow_html=True)
    c2.markdown(f"<div style='background:{PANEL};border-top:3px solid {AMBER};border-radius:8px;padding:14px;"
                f"height:100%'><b style='color:{AMBER}'>🚩 Anomaly score</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>How far the excess sits outside normal for "
                f"this load and this weather. A hot afternoon does not count.</span></div>",
                unsafe_allow_html=True)
    c3.markdown(f"<div style='background:{PANEL};border-top:3px solid {TECH};border-radius:8px;padding:14px;"
                f"height:100%'><b style='color:{TECH}'>🌡️ Camera evidence</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>CNN grade plus Grad-CAM location. This is the "
                f"only column that says <i>where</i>.</span></div>", unsafe_allow_html=True)

    st.success("**Numbers say how much is being lost. Images say where.** Neither is enough on its own — "
               "fusion is what turns two model outputs into one work order.")
    st.info("Note what the screen does *not* do: it never isolates a line by itself. Every row ends in a "
            "recommendation an engineer approves.")


# ================================================================ 14 · the whole system
def render_pipeline(style, animate):
    st.title("The whole system, start to finish")
    st.markdown("#### Every stage of the course, and what feeds what.")

    nodes = [
        (0.6, 5.2, "🏭 Plant", AMBER), (0.6, 3.2, "🌡️ Camera", AMBER),
        (2.6, 5.2, "📡 Meters", AMBER), (2.6, 3.2, "🖼️ Frames", AMBER),
        (4.6, 5.2, "🧹 Clean", TECH), (4.6, 3.2, "🖼️ Frames", TECH),
        (6.4, 5.2, "📐 Scale", TECH),
        (8.2, 5.2, "🌲 Random Forest", POS), (8.2, 3.2, "🧩 CNN", POS),
        (10.0, 4.2, "🔗 Fusion", GREEN), (11.8, 4.2, "📉 Dashboard", GREEN),
    ]
    edges = [(0, 2), (1, 3), (2, 4), (3, 5), (4, 6), (6, 7), (5, 8), (7, 9), (8, 9), (9, 10)]

    fig = go.Figure()
    for a, b in edges:
        x0, y0 = nodes[a][0], nodes[a][1]
        x1, y1 = nodes[b][0], nodes[b][1]
        fig.add_annotation(x=x1 - 0.45, y=y1, ax=x0 + 0.45, ay=y0, xref="x", yref="y",
                           axref="x", ayref="y", showarrow=True, arrowhead=2,
                           arrowsize=1.2, arrowwidth=2, arrowcolor="#3a4655", text="")
    for x, y, label, c in nodes:
        fig.add_shape(type="rect", x0=x - 0.85, x1=x + 0.85, y0=y - 0.5, y1=y + 0.5,
                      line=dict(color=c, width=2), fillcolor=PANEL)
        fig.add_annotation(x=x, y=y, text=f"<b>{label}</b>", showarrow=False,
                           font=dict(size=12, color=TEXT))
    fig.add_annotation(x=1.6, y=6.2, text="THE NUMBERS PATH", showarrow=False,
                       font=dict(size=11, color=POS))
    fig.add_annotation(x=1.6, y=2.2, text="THE IMAGE PATH", showarrow=False,
                       font=dict(size=11, color=AMBER))
    fig.update_xaxes(visible=False, range=[-0.6, 13.0])
    fig.update_yaxes(visible=False, range=[1.6, 6.7])
    fig.update_layout(title="sensors → data → ML + DL → fusion → dashboard")
    st.plotly_chart(style(fig, 420), use_container_width=True)

    st.markdown("### Read it as a chain, not a diagram")
    st.markdown(f"""
- The **numbers path** and the **image path** stay separate right up to fusion. They have to: one has named
  columns, the other does not.
- Cleaning sits *before* both models. A stuck flow meter that survives it becomes a false recommendation
  four stages later, and nothing downstream can recover.
- Fusion is the only place the two paths meet, and it is where a prediction becomes an action.
- The dashboard converts that action into the plant's own units — kWh, tonnes of CO₂, and money.
    """)
    st.info("Everything in this course is one of those boxes. If a stage ever feels abstract, find it on "
            "this drawing and ask what would break downstream without it.")
