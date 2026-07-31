"""
Story stages for the AI for Traffic Signal Optimization course.
===============================================================
The narrative beats that make AI inevitable for a Civil / Transportation
Engineering student who has never met it:

  in-peak        - one junction, one fixed plan, demand that moves all day.
  reading        - one signal cycle. The junction's state BECOMES a row.
  cctv-problem   - a grid of pixels. Which one is the queue? None.
  handmade       - reduce the frame to mean brightness. Watch it fail.
  operator-brain - how a control-room operator decides -> that IS a neuron.
  learning-loop  - predict -> measure -> adjust -> repeat, before terminology.
  cnn-journey    - filters slide over the frame and find the queue shape.
  queue-locate   - the CNN calls it AND shows where it looked (Grad-CAM).
  emergency      - the same method, a different label: a 10-pixel light bar.
  audit          - the confusion matrix, from a traffic audit.
  fusion-engine  - the product: give this arm eight more seconds, this cycle.
  pipeline       - the whole system, start to finish.

THE INTERSECTION MODEL AND THE CCTV FRAMES ARE COPIES OF THE NOTEBOOK'S.
Same constants, same functions, same seeds — so a number quoted in
`Traffic_Signal_Optimization_DL.ipynb` and the same number on the matching
app page always agree. Change one and you must change both.
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

# ---------------------------------------------------------------------------
# THE INTERSECTION MODEL  (identical to the notebook's Section 1)
#   SATURATION FLOW - the rate vehicles discharge once moving, veh/h/lane
#   CAPACITY        - saturation flow x the share of the cycle this approach gets
#   X               - demand / capacity. X > 1 means the approach cannot cope
#   CONTROL DELAY   - average seconds each vehicle loses. What drivers feel.
# ---------------------------------------------------------------------------
SAT_FLOW = 1900.0     # veh/h/lane, ideal saturation flow (HCM)
LANES = 2             # lanes on the approach
LOST_TIME = 4.0       # s lost per phase to start-up and clearance
PHASES = 4            # a four-approach junction
LOST_TOTAL = PHASES * LOST_TIME     # s of every cycle that moves nobody
C_MIN = 45.0          # shortest legal cycle: 4 phases of minimum green + lost time
C_MAX = 140.0         # longest cycle the city permits
LOS_LIMIT = 55.0      # s/veh above which the approach counts as CONGESTED (HCM LOS E)
IDLE_L_S = 0.00022    # litres of fuel burned per second of idling, per vehicle
CO2_PER_L = 2.31      # kg CO2 per litre of petrol
FIXED_C, FIXED_G = 87.0, 50.0       # the installed plan — the best possible single plan


def effective_green(green, ped_calls=0.0):
    """Vehicles never get the whole commanded green: a pedestrian call extends clearance."""
    return np.maximum(np.asarray(green, float) - 0.6 * np.asarray(ped_calls, float), 6.0)


def capacity(green, cycle, heavy_pct=8.0, rain_mm=0.0, ped_calls=0.0, block=1.0):
    """Approach capacity in veh/h. block < 1 models a lane lost to an incident."""
    g = effective_green(green, ped_calls)
    f_hv = 1.0 / (1.0 + np.asarray(heavy_pct, float) / 100.0)      # a truck = 2 cars
    f_rn = np.clip(1.0 - 0.008 * np.asarray(rain_mm, float), 0.85, 1.0)
    return SAT_FLOW * LANES * f_hv * f_rn * block * g / np.asarray(cycle, float)


def delay_for(demand, green, cycle, heavy_pct=8.0, rain_mm=0.0, ped_calls=0.0,
              block=1.0, T=0.25):
    """HCM control delay in s/veh: uniform delay + incremental (overflow) delay."""
    cap = capacity(green, cycle, heavy_pct, rain_mm, ped_calls, block)
    lam = effective_green(green, ped_calls) / np.asarray(cycle, float)
    X = np.asarray(demand, float) / np.maximum(cap, 1.0)
    d1 = (0.5 * np.asarray(cycle, float) * (1 - lam) ** 2
          / np.maximum(1 - np.minimum(X, 1.0) * lam, 0.05))
    d2 = 900 * T * ((X - 1) + np.sqrt((X - 1) ** 2 + 8 * 0.5 * X / np.maximum(cap * T, 1.0)))
    # HCM does not distinguish beyond about two minutes: it is all level of service F.
    return np.minimum(d1 + d2, 200.0), X, cap


def queue_for(demand, green, cycle, X, ped_calls=0.0):
    """Back of queue at the end of red, in metres of road, spread across the lanes."""
    lam = effective_green(green, ped_calls) / np.asarray(cycle, float)
    q_veh = (np.asarray(demand, float) * np.asarray(cycle, float) * (1 - lam)
             / (3600.0 * np.maximum(1 - np.minimum(X, 1.0) * lam, 0.05)))
    return q_veh * 7.0 / LANES          # 7 m of kerb per queued vehicle


# Two demand profiles, because a junction is a competition. The main street peaks
# sharply in the evening; the cross street peaks earlier and flatter. Their RATIO
# changes hour by hour, and that ratio is what a fixed split gets wrong all day.
def demand_for(hour):
    """Arrival flow on the main-street approach, veh/h."""
    h = np.asarray(hour, float)
    am = 950.0 * np.exp(-((h - 8.5) ** 2) / (2 * 1.3 ** 2))
    nn = 380.0 * np.exp(-((h - 13.0) ** 2) / (2 * 2.2 ** 2))
    pm = 1900.0 * np.exp(-((h - 18.0) ** 2) / (2 * 1.6 ** 2))
    return 200.0 + am + nn + pm


def demand_cross(hour):
    """Arrival flow on the cross-street approach, veh/h."""
    h = np.asarray(hour, float)
    return (150.0 + 700.0 * np.exp(-((h - 9.5) ** 2) / (2 * 2.6 ** 2))
            + 500.0 * np.exp(-((h - 17.0) ** 2) / (2 * 2.4 ** 2)))


def flow_ratios(d_main, d_cross, heavy_pct=8.0):
    """y = flow ratio of each critical movement; Y = their sum (Webster's Y)."""
    s = SAT_FLOW * LANES / (1.0 + np.asarray(heavy_pct, float) / 100.0)
    y = np.asarray(d_main, float) / s
    yc = np.asarray(d_cross, float) / s
    return y, yc, np.clip(y + yc, 0.10, 0.92)


def green_split(d_main, d_cross, cycle):
    """Share out ALL the effective green in proportion to the flow ratios.

    Reserving a share for anything else silently throws green away, and makes
    adaptive control look far worse than it is.
    """
    y, yc, _ = flow_ratios(d_main, d_cross)
    avail = np.asarray(cycle, float) - LOST_TOTAL
    g_main = np.clip(avail * y / (y + yc), 7.0, avail - 7.0)
    return g_main, avail - g_main


def junction_delay(d_main, d_cross, cycle, g_main, g_cross):
    """Vehicle-weighted average delay across BOTH critical movements, s/veh.

    Scoring one approach only would make any re-split look like a loss — moving
    green between competing movements is the entire mechanism of adaptive
    control, so both movements have to be in the number.
    """
    a, _, _ = delay_for(d_main, g_main, cycle)
    b, _, _ = delay_for(d_cross, g_cross, cycle)
    return (d_main * a + d_cross * b) / (d_main + d_cross)


def delay_vs_cycle(d_main, d_cross, cycles=None):
    """Sweep the cycle length, re-splitting the green at every candidate."""
    if cycles is None:
        cycles = np.linspace(C_MIN, C_MAX, 120)
    gm, gc = green_split(d_main, d_cross, cycles)
    return cycles, gm, junction_delay(d_main, d_cross, cycles, gm, gc)


# ----------------------------------------------------------------------------
# ANIMATION HELPERS — turn a finished chart into a "press Play" reveal.
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


# ============================================================ synthetic CCTV
# An approach as a 64x64 camera frame (0 = black, 1 = white):
#   free_flow  - daylight, a few well-spaced vehicles       (clear)
#   night      - the same few vehicles, dark scene          (clear)  <- decoy 1
#   wet_glare  - the same few vehicles, wet reflective road (clear)  <- decoy 2
#   queue      - a standing line of vehicles in two lanes   (CONGESTED)
#   jam        - vehicles across all three lanes            (CONGESTED)
SCENE = {"free_flow": 0, "night": 1, "wet_glare": 2, "queue": 3, "jam": 4}
KINDS = ["free_flow", "night", "wet_glare", "queue", "jam"]
LABEL = {"free_flow": "clear", "night": "clear", "wet_glare": "clear",
         "queue": "CONGESTED", "jam": "CONGESTED"}


@st.cache_data(show_spinner=False)
def make_cctv(kind="free_flow", size=64, seed=0, emergency=False):
    """One camera frame. Identical to the notebook's generator, seed for seed.

    The resulting mean brightnesses land as
        night 0.27 < jam 0.39 < queue 0.47 < free_flow 0.58 < wet_glare 0.72
    so the two CONGESTED scenes are sandwiched between clear ones and no
    threshold on the mean separates them in either direction.
    """
    rng = np.random.default_rng(seed * 8 + SCENE[kind])      # stable across sessions
    base = {"free_flow": 0.62, "night": 0.30, "wet_glare": 0.74,
            "queue": 0.62, "jam": 0.62}[kind]
    img = base + rng.normal(0, 0.030, (size, size))

    # lane markings, dashed, between three lanes
    for xm in (21, 42):
        for y0 in range(0, size, 10):
            img[y0:y0 + 5, xm:xm + 1] = min(base + 0.22, 1.0)
    if kind == "wet_glare":                       # specular streaks off standing water
        for _ in range(6):
            y0 = int(rng.integers(0, size - 8))
            img[y0:y0 + 3, :] += 0.10 * rng.uniform(0.6, 1.0)

    lanes = {"free_flow": [0, 1, 2], "night": [0, 1, 2], "wet_glare": [0, 1, 2],
             "queue": [0, 1], "jam": [0, 1, 2]}[kind]
    n_per = {"free_flow": 1, "night": 1, "wet_glare": 1, "queue": 6, "jam": 6}[kind]
    spread = {"free_flow": 52, "night": 52, "wet_glare": 52, "queue": 9, "jam": 9}[kind]

    spots = []
    for ln in lanes:
        x0 = 3 + ln * 21
        for k in range(n_per):
            y0 = int(rng.integers(2, 8)) + k * spread
            if y0 + 10 >= size:
                continue
            img[y0:y0 + 10, x0:x0 + 15] -= 0.38 * rng.uniform(0.85, 1.15)   # a vehicle roof
            spots.append((y0, x0))

    if emergency and spots:                       # a light bar on one vehicle
        y0, x0 = spots[int(rng.integers(len(spots)))]
        img[y0 + 1:y0 + 3, x0 + 4:x0 + 11] = 0.99
    return np.clip(img, 0, 1)


def _vehicle_cam(kind, size=64, seed=0):
    """A Grad-CAM-style attention map for one frame.

    A trained CNN's last conv layer responds to vehicle roofs; Grad-CAM weights
    those maps by how much they pushed the score towards 'congested'. Here the
    same effect is drawn directly from the frame: where a vehicle darkens the
    road, smoothed into regions.
    """
    img = make_cctv(kind, size=size, seed=seed)
    base = {"free_flow": 0.62, "night": 0.30, "wet_glare": 0.74,
            "queue": 0.62, "jam": 0.62}[kind]
    dark = np.clip(base - img, 0, None)
    k = np.ones((5, 5)) / 25.0
    sm = _conv2d(np.pad(dark, 2, mode="edge"), k)
    if LABEL[kind] == "clear":
        sm = sm * 0.12                            # nothing pushes it towards congested
    return 0.05 + 0.95 * sm / (sm.max() + 1e-9)


def _conv2d(img, k):
    win = sliding_window_view(img, k.shape)
    return np.einsum("ijkl,kl->ij", win, k)


def _heat(z, colorscale="Greys", h=320, title="", showscale=False, reverse=False):
    fig = go.Figure(go.Heatmap(z=z, colorscale=colorscale, showscale=showscale,
                               reversescale=reverse))
    fig.update_layout(title=title, paper_bgcolor=BG, plot_bgcolor=BG, font_color=TEXT,
                      margin=dict(l=10, r=10, t=44, b=10), height=h)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, autorange="reversed", scaleanchor="x")
    return fig


# ================================================================ 1 · the peak
def render_in_peak(style, animate):
    st.title("A junction under load — the plan does not move, the demand does")
    st.markdown("#### One fixed plan has to serve a morning peak and an evening peak.")
    st.caption("Set the plan the junction runs all day, then read the delay it produces hour by hour.")
    st.write("")

    h = np.arange(0, 24, 0.25)
    dm, dc = demand_for(h), demand_cross(h)

    c = st.columns(2)
    cycle = c[0].slider("Cycle length (s)", int(C_MIN), int(C_MAX), int(FIXED_C), 1)
    gmain = c[1].slider("Green to the main street (s)", 10, 120, int(FIXED_G), 1)
    gmain = min(gmain, cycle - LOST_TOTAL - 7)
    gcross = cycle - LOST_TOTAL - gmain

    d_main, X, _ = delay_for(dm, float(gmain), float(cycle))       # the main approach
    d = junction_delay(dm, dc, float(cycle), float(gmain), float(gcross))   # both movements

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=h, y=dm, mode="lines", name="main street",
                             line=dict(color=POS, width=3)))
    fig.add_trace(go.Scatter(x=h, y=dc, mode="lines", name="cross street",
                             line=dict(color=TECH, width=3)))
    fig.update_layout(title="demand through the day — the two peaks are not at the same hour")
    fig.update_xaxes(title="hour of day"); fig.update_yaxes(title="veh/h")
    style(fig, 340); animate(fig, _line_grow(h, dm, POS), ms=45)
    st.plotly_chart(fig, use_container_width=True)
    st.write("")

    share = dm / (dm + dc)
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=h, y=share, mode="lines", line=dict(color=GREEN, width=3),
                              name="main street's share of the demand"))
    fig3.add_hline(y=gmain / (cycle - LOST_TOTAL), line=dict(color=RED, width=2, dash="dash"),
                   annotation_text="the share of green it actually gets",
                   annotation_position="bottom left")
    fig3.update_layout(title="the plan gives a constant share; the demand does not ask for one")
    fig3.update_xaxes(title="hour of day"); fig3.update_yaxes(title="share", range=[0, 1])
    st.plotly_chart(style(fig3, 320), use_container_width=True)
    st.write("")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=h, y=d_main, mode="lines", line=dict(color=AMBER, width=3),
                              name="main approach"))
    fig2.add_trace(go.Scatter(x=h, y=d, mode="lines", line=dict(color=MUTED, width=2, dash="dot"),
                              name="whole junction, vehicle-weighted"))
    fig2.add_hline(y=LOS_LIMIT, line=dict(color=RED, width=2, dash="dash"),
                   annotation_text=f"LOS E begins at {LOS_LIMIT:.0f} s/veh",
                   annotation_position="top left")
    fig2.update_layout(title="delay per vehicle under this one fixed plan")
    fig2.update_xaxes(title="hour of day"); fig2.update_yaxes(title="seconds per vehicle")
    st.plotly_chart(style(fig2, 360), use_container_width=True)

    veh = dm + dc
    veh_h = float(np.sum(d * veh * 0.25) / 3600.0)
    m1, m2, m3 = st.columns(3)
    m1.metric("Worst hour, main approach", f"{d_main.max():.0f} s/veh",
              f"{h[int(np.argmax(d_main))]:.2f} h")
    m2.metric("Peak degree of saturation X", f"{float(X.max()):.2f}",
              "over capacity" if X.max() > 1 else "within capacity", delta_color="off")
    m3.metric("Delay across the day", f"{veh_h:,.0f} vehicle-hours", delta_color="off")
    st.caption(f"At the installed plan the evening peak sits right on the level-of-service limit — "
               f"X reaches {float(X.max()):.2f}, so the approach is at capacity. Move the green split a "
               f"few seconds either way and watch it go over.")
    st.write("")

    st.markdown("### So — can you just retime it more often?")
    if st.button("Answer", type="primary"):
        st.error("**Not by hand.** A retime needs a fresh classified count, a model build and a street "
                 "trial. A city with 400 junctions cannot do that quarterly, so most plans run for years.")
        st.info("👉 The fix is not a faster retiming programme — it is a junction that measures its own "
                "demand every cycle and adjusts while the peak is still running. The engineer stays in "
                "charge; the continuous measurement is what AI takes off their plate.")


# ================================================================ 2 · one cycle
def render_reading(get_data, style, animate):
    st.title("One signal cycle — how a junction's state becomes data")
    st.markdown("#### The model will never stand on the corner.")
    d = get_data()
    row = d["clean"].iloc[5]
    st.write("")

    steps = [
        ("🚦  The real junction", "Vehicles arrive, queue, discharge on green, and the cross street waits. "
                                  "All of it at once.", MUTED),
        ("📡  Detectors read it", "A count, a speed, a loop occupancy, the heavy-vehicle share, the rain, "
                                  "the pedestrian calls — each one number. No context, no cause.", POS),
        ("📷  The camera captures it", "One frame of the approach. Not a queue length — a grid of "
                                       "brightness values.", AMBER),
        ("📄  It becomes one row", "This row, and the delay that cycle produced, is the *entire* junction "
                                   "as far as the model is concerned.", GREEN),
    ]
    i = st.slider("Walk through the cycle", 1, 4, 1)
    for k, (t, txt, c) in enumerate(steps, start=1):
        if k <= i:
            st.markdown(f"<div style='padding:12px 16px;margin:6px 0;border-radius:4px;"
                        f"border-left:4px solid {c};background:{PANEL};color:{TEXT}'>"
                        f"<b>{t}</b><br><span style='color:{MUTED}'>{txt}</span></div>",
                        unsafe_allow_html=True)
    if i == 4:
        st.write("")
        st.markdown("##### What each channel records, and why it matters")
        st.dataframe(pd.DataFrame([
            ["🚗 Vehicle count", "Inductive loop", "veh/cycle", "The demand this green has to clear"],
            ["🏎️ Average speed", "Radar / video", "km/h", "Falls as the approach saturates — a consequence, not an input"],
            ["📶 Occupancy", "Inductive loop", "%", "Share of time the loop is covered; rises with the queue"],
            ["🚚 Heavy vehicles", "Classifier loop", "%", "A truck discharges like two cars, so capacity falls"],
            ["🟢 Green time", "Controller log", "s", "The lever — how much green this approach was given"],
            ["⏱️ Cycle time", "Controller log", "s", "The other lever, and the one drivers feel at night"],
            ["🕐 Hour of day", "Controller clock", "h", "Stands in for the whole daily demand pattern"],
            ["🌧️ Rain", "Weather feed", "mm", "Wet roads discharge more slowly — capacity falls"],
            ["🚶 Pedestrian calls", "Push-button", "per cycle", "Each call takes clearance time out of the vehicle green"],
        ], columns=["Channel", "Source", "Unit", "What it tells you"]),
            use_container_width=True, hide_index=True)
        st.write("")

        st.markdown("##### One cycle = one row of those numbers")
        cols = ["vehicle_count", "avg_speed_kmh", "occupancy_pct", "heavy_veh_pct",
                "green_time_s", "cycle_time_s", "hour_of_day", "rain_mm", "ped_calls"]
        st.dataframe(pd.DataFrame([row[cols].values], columns=[
            "Vehicles/cycle", "Speed (km/h)", "Occupancy (%)", "Heavy veh (%)",
            "Green (s)", "Cycle (s)", "Hour", "Rain (mm)", "Ped calls"]),
            use_container_width=True, hide_index=True)
        st.info("The model never stands on the corner — it sees only this row. If the row is wrong, the "
                "prediction is wrong, and the model has no way to notice. That is why the next stages are "
                "about the data, not the model.")


# ================================================================ 3 · the raw frame
def render_cctv_problem(style, animate):
    st.title("What the junction camera actually sends")
    st.markdown("#### You *see* the queue instantly. Now find it in the numbers.")
    st.write("")
    kind = st.selectbox(
        "Choose a view", KINDS, index=3,
        format_func=lambda k: {
            "free_flow": "Daylight, well-spaced vehicles — CLEAR",
            "night": "The same few vehicles, at night — CLEAR",
            "wet_glare": "The same few vehicles, wet reflective road — CLEAR",
            "queue": "A standing line in two lanes — CONGESTED",
            "jam": "Vehicles across all three lanes — CONGESTED",
        }[k])
    img = make_cctv(kind)
    st.plotly_chart(_heat(img, title=f"one camera frame · {img.size:,} brightness values", h=380),
                    use_container_width=True)
    st.caption("Every pixel is a brightness value between 0 and 1. None of them is labelled 'congested'. "
               "Compare **night** with **jam** — the dark one is the clear one.")
    st.write("")

    if st.button("Where is the queue?", type="primary"):
        st.error("It is not any single pixel. A queue is **a line of dark blocks, closely spaced, in more "
                 "than one lane**. That is a *pattern* across hundreds of pixels — no one number holds it.")
        st.info("At the detector log an engineer had already named count and occupancy, so the Random "
                "Forest had features to weigh. Here nothing is pre-named. There is no column called "
                "'queue' — only its shape.")


# ================================================================ 4 · by hand
def render_handmade(style, animate):
    st.title("The camera rulebook, by hand")
    st.markdown("#### Reduce the frame to one number, set a threshold, watch it fail.")
    st.caption("The theory is sound: more vehicles means more dark pixels means a darker frame. "
               "The problem is night, and wet glare.")
    st.write("")

    means = [(k, float(make_cctv(k).mean()), RED if LABEL[k] == "CONGESTED" else GREEN)
             for k in ["night", "jam", "queue", "free_flow", "wet_glare"]]
    nice = {"free_flow": "Free flow (clear)", "night": "Night (clear)",
            "wet_glare": "Wet glare (clear)", "queue": "Queue (CONGESTED)",
            "jam": "Jam (CONGESTED)"}

    thr = st.slider("Set the mean-brightness threshold (congested below this)", 0.20, 0.80, 0.50, 0.01)
    fig = go.Figure()
    for k, v, c in means:
        fig.add_trace(go.Bar(x=[nice[k]], y=[v], marker_color=c, showlegend=False,
                             text=f"{v:.2f}", textposition="outside"))
    fig.add_hline(y=thr, line=dict(color=POS, width=2, dash="dash"),
                  annotation_text=f"congested below {thr:.2f}", annotation_position="top left")
    fig.update_layout(title="one number per frame — can a line separate congested from clear?")
    fig.update_yaxes(title="mean brightness", range=[0, 0.95])
    style(fig, 380)
    animate(fig, _bars_grow([dict(x=[nice[k]], y=[v], color=c, text=f"{v:.2f}")
                             for k, v, c in means]), ms=90)
    st.plotly_chart(fig, use_container_width=True)

    missed = [nice[k] for k, v, c in means if c == RED and v >= thr]
    false_al = [nice[k] for k, v, c in means if c == GREEN and v < thr]
    a, b = st.columns(2)
    a.metric("Congested frames missed", len(missed), ", ".join(missed) or "none", delta_color="inverse")
    b.metric("Clear frames alarmed", len(false_al), ", ".join(false_al) or "none", delta_color="inverse")
    st.write("")

    st.markdown("##### The ordering is the whole problem")
    st.code("night 0.27   <   jam 0.39   <   queue 0.47   <   free_flow 0.58   <   wet_glare 0.72",
            language=None)
    st.warning("**Move the threshold anywhere you like — you cannot win.** The two congested scenes are "
               "*sandwiched between clear ones*. Set it dark enough to catch the jam and you alarm on every "
               "empty road after sunset; set it bright enough to exclude the night and you miss both. "
               "Reversing the rule fails the same way.")
    st.error("Averaging threw away the only thing that distinguishes them: a queue is a **line** of blobs, "
             "an empty night road is uniformly dark. Ten more hand-made features would still be guesses.")


# ================================================================ 5 · operator
def render_operator_brain(style):
    st.title("How an operator decides — and why that is a neuron")
    st.markdown("#### Weigh a few signals, add them up, make one call.")
    st.caption("Move the readings. The bar is the operator's mental total; zero is where they call it "
               "congested.")
    st.write("")

    c1, c2 = st.columns([1, 1.3])
    with c1:
        occ = st.slider("Loop occupancy (%)", 0, 95, 62)
        spd = st.slider("Average speed (km/h)", 5, 60, 22)
        cnt = st.slider("Vehicles this cycle", 0, 60, 32)
        rain = st.slider("Rain (mm)", 0.0, 12.0, 0.0, 0.5)
    weights = dict(occ=0.075, spd=-0.13, cnt=0.09, rain=0.10)
    contrib = {
        "Occupancy": weights["occ"] * occ,
        "Speed": weights["spd"] * spd,
        "Vehicle count": weights["cnt"] * cnt,
        "Rain": weights["rain"] * rain,
    }
    total = sum(contrib.values()) - 3.6       # bias: the operator's baseline scepticism

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
        st.error(f"**Call: the approach is congested.** Weighted total {total:+.2f} clears zero.")
    else:
        st.success(f"**Call: it is coping.** Weighted total {total:+.2f} sits below zero.")
    st.write("")

    st.markdown(
        f"<div style='border-left:3px solid {POS};padding:10px 0 10px 16px;font-size:16px;color:{TEXT};"
        f"line-height:1.7'>What you just moved was <b>w · x + b</b>. Each slider is an input <i>x</i>. "
        f"Each fixed multiplier is a weight <i>w</i> — note speed's is <b>negative</b>, because a high "
        f"speed is evidence <i>against</i> congestion. The baseline scepticism is the bias <i>b</i>. "
        f"Comparing the total to zero is the activation. <b>That is a neuron</b> — the only difference in "
        f"the machine version is that nobody chooses the weights: they are learned from the log.</div>",
        unsafe_allow_html=True)


# ================================================================ 6 · learning loop
def render_learning_loop(style, animate):
    st.title("Learning from a bad peak")
    st.markdown("#### Predict, compare with the measured delay, adjust, repeat.")
    st.caption("The operator starts with a bad guess about how much occupancy matters. Each measured peak "
               "corrects it.")
    st.write("")

    true_w = 3.4
    start_w = st.slider("Starting guess for the occupancy weight", 0.0, 8.0, 7.2, 0.1)
    lr = st.slider("How strongly to correct after each miss", 0.02, 0.6, 0.22, 0.02)
    n = 24

    w = start_w
    ws, errs = [w], []
    for _ in range(n):
        err = w - true_w
        errs.append(abs(err))
        w = w - lr * 2 * err
        ws.append(w)
    errs.append(abs(w - true_w))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(len(ws))), y=ws, mode="lines+markers",
                             line=dict(color=POS, width=3), name="the weight"))
    fig.add_hline(y=true_w, line=dict(color=GREEN, width=2, dash="dash"),
                  annotation_text="the weight that fits this junction",
                  annotation_position="bottom right")
    fig.update_layout(title="the weight, corrected peak after peak (press Play)")
    fig.update_xaxes(title="correction round"); fig.update_yaxes(title="weight on occupancy")
    style(fig, 380); animate(fig, _line_grow(np.arange(len(ws)), np.array(ws), POS), ms=90)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Starting error", f"{abs(start_w - true_w):.2f}")
    c2.metric("Error after 24 rounds", f"{errs[-1]:.3f}")
    c3.metric("Correction strength", f"{lr:.2f}")
    st.write("")

    if lr > 0.45:
        st.warning("Correct too hard and the weight overshoots and swings back — the same thing that "
                   "happens when a green split is over-adjusted on street.")
    elif lr < 0.06:
        st.warning("Correct too gently and it is still drifting after two years of peaks.")
    else:
        st.success("Steady correction converges. That is the whole learning loop: **predict → compare → "
                   "measure the error → adjust → repeat**.")

    st.info("A real network runs this loop over thousands of rows and every weight at once. The next page "
            "gives the correction its proper name: gradient descent.")


# ================================================================ 7 · inside the CNN
def render_cnn_journey(style, animate):
    st.title("Inside the CNN — reading the approach")
    st.markdown("#### A small filter slides over the frame and reports where its pattern occurs.")
    st.write("")

    kind = st.selectbox("Camera frame", KINDS, index=3)
    img = make_cctv(kind)

    st.markdown("##### Step 1 — the raw frame the camera sends")
    st.plotly_chart(_heat(img, title="input · 64 × 64 brightness values", h=330),
                    use_container_width=True)
    st.write("")

    st.markdown("##### Step 2 — early filters: where does brightness change sharply?")
    kv = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], float)
    kh = kv.T
    kb = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], float)
    c1, c2, c3 = st.columns(3)
    for col, k, name in ((c1, kv, "vertical edges"), (c2, kh, "horizontal edges"),
                         (c3, kb, "blobs & spots")):
        with col:
            fm = np.abs(_conv2d(img, k))
            st.plotly_chart(_heat(fm, colorscale="Inferno", title=name, h=250),
                            use_container_width=True)
    st.caption("Each map is bright where that filter's pattern was found. The horizontal-edge map is the "
               "telling one: a queue is a *stack of horizontal edges at regular spacing*. Nobody wrote that "
               "into the network — a trained CNN learns filters like these from labelled frames.")
    st.write("")

    st.markdown("##### Step 3 — deeper layers combine edges into shapes")
    smooth = np.ones((5, 5)) / 25.0
    deep = _conv2d(np.abs(_conv2d(img, kh)), smooth)
    d1, d2 = st.columns(2)
    with d1:
        st.plotly_chart(_heat(deep, colorscale="Inferno",
                              title="a deeper feature map — regions, not pixels", h=300),
                        use_container_width=True)
    with d2:
        st.markdown(f"<div style='background:{PANEL};border-radius:4px;padding:16px;height:100%'>"
                    f"<b style='color:{TECH}'>What just happened</b>"
                    f"<ul style='color:{MUTED};font-size:14px;line-height:1.8'>"
                    f"<li>Early layers respond to <b>edges</b> — brightness steps.</li>"
                    f"<li>Later layers combine edges into <b>vehicles</b>, and vehicles into a "
                    f"<b>queue</b>.</li>"
                    f"<li>Because the filter <b>slides</b>, the queue is found wherever it sits.</li>"
                    f"<li>The final layer weighs those shapes into one grade.</li></ul></div>",
                    unsafe_allow_html=True)
    st.write("")

    st.markdown("##### Step 4 — the grade")
    scores = {"queue": (0.92, "Congested — standing queue"), "jam": (0.96, "Congested — full jam"),
              "free_flow": (0.05, "Clear"), "night": (0.08, "Clear — dark, but empty"),
              "wet_glare": (0.11, "Clear — bright, but empty")}
    p, label = scores[kind]
    fig = go.Figure(go.Bar(x=["congested"], y=[p], marker_color=RED if p > 0.5 else GREEN,
                           text=[f"{p:.0%}"], textposition="outside"))
    fig.update_yaxes(range=[0, 1.15], title="probability")
    fig.update_layout(title=f"CNN output — {label}")
    st.plotly_chart(style(fig, 280), use_container_width=True)
    st.success("The mean-brightness rule could not tell a jam from a night frame. The CNN separates them "
               "because it learned the **pattern**, not a summary number.")


# ================================================================ 8 · locating the queue
def render_queue_locate(style, animate):
    st.title("Where is the queue? — Grad-CAM on the approach")
    st.markdown("#### A probability does not reallocate green. A location does.")
    st.write("")

    kind = st.selectbox("Camera frame", ["queue", "jam", "night", "wet_glare"], index=0)
    img = make_cctv(kind)
    cam = _vehicle_cam(kind)
    blend = st.slider("Overlay strength", 0.0, 1.0, 0.6, 0.05)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(_heat(img, title="camera frame · 64 × 64", h=340), use_container_width=True)
        st.caption("What the camera sends.")
    with c2:
        over = np.clip((1 - blend) * img + blend * cam, 0, 1)
        st.plotly_chart(_heat(over, colorscale="Turbo",
                              title="Grad-CAM — where the network looked", h=340),
                        use_container_width=True)
        st.caption("Bright means that region drove the decision.")
    st.write("")

    if LABEL[kind] == "CONGESTED":
        st.error("**Congested — the map concentrates on the line of vehicle roofs**, not on the lane "
                 "markings or the road surface. Those are bright in every frame, including clear ones, so "
                 "they carry no evidence.")
        st.info("That is the instruction: *this approach is queued back — extend its green this cycle.* "
                "An operator can see the arm on the monitor and confirm in seconds.")
    else:
        st.success("**Clear — the map stays almost flat.** Nothing in the frame pushed the network towards "
                   "congestion, whether the scene is dark or bright.")
    st.write("")

    st.markdown(
        f"<div style='border-left:3px solid {TECH};padding:10px 0 10px 16px;font-size:15px;color:{TEXT};"
        f"line-height:1.7'><b>How it works.</b> The last convolutional layer holds several feature maps. "
        f"Grad-CAM weights each map by how much it pushed the score towards 'congested', adds them up and "
        f"stretches the result back over the frame. The bright region is literally the evidence the "
        f"network used — which is what makes the call auditable.</div>", unsafe_allow_html=True)


# ================================================================ 9 · emergency
def render_emergency(style, animate):
    st.title("Emergency preemption — the same method, a different label")
    st.markdown("#### Nothing about the CNN changes. Only what the frames were labelled.")
    st.caption("An emergency vehicle shows as a small bright light bar — about ten pixels in a frame of "
               "four thousand.")
    st.write("")

    kind = st.selectbox("Background scene", KINDS, index=0)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(_heat(make_cctv(kind, seed=2, emergency=False),
                              title="no emergency vehicle", h=320), use_container_width=True)
    with c2:
        st.plotly_chart(_heat(make_cctv(kind, seed=2, emergency=True),
                              title="light bar present (top of one vehicle)", h=320),
                        use_container_width=True)
    st.caption(f"The light bar is about **{10/64**2:.2%} of the frame's pixels**. Look at the two frames "
               f"above: they are, for practical purposes, the same picture.")
    st.write("")

    st.markdown("##### First — prove the hand-made feature is blind to it")
    rng = np.random.default_rng(3)
    bright, lab = [], []
    for i in range(240):
        k = KINDS[int(rng.integers(len(KINDS)))]
        emg = bool(rng.random() < 0.35)
        im = make_cctv(k, seed=int(rng.integers(1_000_000)), emergency=emg)
        bright.append(float(im.mean())); lab.append(int(emg))
    bright = np.array(bright); lab = np.array(lab)

    best_acc, best_thr = 0.0, None
    for thr in np.linspace(bright.min(), bright.max(), 300):
        for sense in (1, -1):
            acc = float(np.mean(((sense * bright) > (sense * thr)).astype(int) == lab))
            if acc > best_acc:
                best_acc, best_thr = acc, thr
    base_rate = float(max(lab.mean(), 1 - lab.mean()))

    fig = go.Figure()
    fig.add_trace(go.Box(y=bright[lab == 0], name="no emergency vehicle", marker_color=GREEN))
    fig.add_trace(go.Box(y=bright[lab == 1], name="emergency vehicle present", marker_color=RED))
    fig.update_layout(title="mean brightness cannot see a ten-pixel light bar")
    fig.update_yaxes(title="mean brightness")
    st.plotly_chart(style(fig, 360), use_container_width=True)

    m = st.columns(3)
    m[0].metric("Best possible brightness threshold", f"{best_acc:.1%}")
    m[1].metric("Always guessing the commoner class", f"{base_rate:.1%}")
    m[2].metric("What the threshold actually bought", f"{(best_acc-base_rate)*100:+.1f} pts",
                delta_color="off")
    st.write("")

    st.warning("Every possible cut point was swept, in both directions, so nobody can say a bad threshold "
               "was chosen. The best one barely beats guessing — because the light bar moves the frame's "
               "average by almost nothing. **The evidence is local; the feature is global.**")
    st.success("A CNN reads it easily: a small, very bright horizontal bar sitting on top of a dark "
               "vehicle roof is a *pattern*, and patterns are what convolution finds.")
    st.write("")

    st.markdown("##### And then — preemption is a transfer, not a saving")
    grant = st.slider("Green granted to the emergency vehicle (s)", 5, 60, 25, 1)
    cross_v = st.slider("Cross-street demand at that moment (veh/h)", 200, 1200, 750, 50)
    g_cross_normal = FIXED_C - LOST_TOTAL - FIXED_G
    d_norm, _, _ = delay_for(cross_v, g_cross_normal, FIXED_C)
    d_pre, _, _ = delay_for(cross_v, max(7.0, g_cross_normal - grant), FIXED_C)
    a, b, c = st.columns(3)
    a.metric("Seconds saved for the ambulance", f"≈ {grant} s")
    b.metric("Cross-street delay, normal cycle", f"{float(d_norm):.0f} s/veh")
    c.metric("Cross-street delay, preempted cycle", f"{float(d_pre):.0f} s/veh",
             f"+{float(d_pre - d_norm):.0f} s", delta_color="inverse")
    st.info("An ambulance minute is not a car minute, so the trade is usually worth making — but it has to "
            "be **stated**, not hidden. A *false* detection costs all of that and buys nothing, which is "
            "why the false-alarm rate matters more here than anywhere else in the system.")


# ================================================================ 10 · the audit
def render_audit(get_data, get_models, style, animate):
    st.title("The traffic audit — checking every claim")
    st.markdown("#### Predicted against measured, on cycles the model has never seen.")
    st.write("")
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
        z=z, x=["called coping", "called congested"], y=["actually coping", "actually congested"],
        colorscale=[[0, "#16202b"], [1, POS]], showscale=False,
        text=[[f"{tn}<br>correct", f"{fp}<br>false alarm"],
              [f"{fn}<br>MISSED PEAK", f"{tp}<br>caught"]],
        texttemplate="%{text}", textfont=dict(size=15)))
    fig.update_layout(title=f"{which} — {len(yte)} sealed cycles")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(style(fig, 380), use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Accuracy", f"{acc:.1%}")
    c2.metric("Congested cycles caught", f"{recall:.1%}")
    c3.metric("False alarms", fp)
    c4.metric("Missed peaks", fn, delta_color="inverse")
    st.write("")

    st.markdown("### The two errors do not cost the same")
    a, b = st.columns(2)
    a.markdown(f"<div style='background:{PANEL};border-left:4px solid {AMBER};border-radius:4px;"
               f"padding:14px'><b style='color:{AMBER}'>False alarm ({fp} cycles)</b><br>"
               f"<span style='color:{MUTED}'>Green is moved to an arm that did not need it. Cost: a few "
               f"seconds taken from the street that did.</span></div>", unsafe_allow_html=True)
    b.markdown(f"<div style='background:{PANEL};border-left:4px solid {RED};border-radius:4px;"
               f"padding:14px'><b style='color:{RED}'>Missed peak ({fn} cycles)</b><br>"
               f"<span style='color:{MUTED}'>The queue keeps growing and can block the junction upstream. "
               f"Cost: a spillback that takes the rest of the peak to clear.</span></div>",
               unsafe_allow_html=True)
    st.write("")

    st.info("This is why accuracy alone is never reported. A model that calls every cycle 'coping' scores "
            "well on a junction that copes most of the day — and finds nothing. **Recall on the congested "
            "cycles is the number the project is judged on.**")


# ================================================================ 11 · the engine
def render_fusion_engine(style):
    st.title("The junction decision engine")
    st.markdown("#### Three model outputs, one ranked instruction.")
    st.caption("This is the product. Everything before it existed to fill in these rows.")
    st.write("")

    rows = [
        dict(arm="Southern arm · A6 approach", delay=78.0, cam="queue in two lanes, back past the stop line",
             anom=3.9, action="Extend green by 8 s this cycle", pr="HIGH"),
        dict(arm="Northern arm · A6 approach", delay=61.0, cam="short queue forming",
             anom=2.4, action="Watch — extend if it repeats next cycle", pr="MEDIUM"),
        dict(arm="Eastern arm · Mill Lane", delay=44.0, cam="two vehicles waiting",
             anom=1.2, action="Hold plan — within target", pr="LOW"),
        dict(arm="Pedestrian stage", delay=22.0, cam="four waiting",
             anom=0.6, action="Call served this cycle", pr="LOW"),
    ]
    colr = {"HIGH": RED, "MEDIUM": AMBER, "LOW": GREEN}
    for r in rows:
        st.markdown(
            f"<div style='background:{PANEL};border-left:5px solid {colr[r['pr']]};border-radius:4px;"
            f"padding:14px 18px;margin:8px 0'>"
            f"<div style='display:flex;justify-content:space-between;align-items:baseline'>"
            f"<b style='color:{TEXT};font-size:17px'>{r['arm']}</b>"
            f"<span style='color:{colr[r['pr']]};font-size:12px;letter-spacing:.14em'>{r['pr']}</span></div>"
            f"<span style='color:{MUTED};font-size:14px'>"
            f"⏱️ <b style='color:{POS}'>{r['delay']:.0f} s/veh</b> predicted delay &nbsp;·&nbsp; "
            f"🚩 anomaly score <b>{r['anom']:.1f}σ</b> &nbsp;·&nbsp; "
            f"📷 camera: {r['cam']}</span><br>"
            f"<span style='color:{GREEN};font-size:15px'>▸ {r['action']}</span></div>",
            unsafe_allow_html=True)

    st.write("")
    st.divider()
    st.markdown("### Where each column came from")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div style='background:{PANEL};border-top:3px solid {POS};border-radius:4px;padding:14px;"
                f"height:100%'><b style='color:{POS}'>⏱️ Predicted delay</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>Random Forest on the nine detector channels: "
                f"what this cycle will cost per vehicle.</span></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='background:{PANEL};border-top:3px solid {AMBER};border-radius:4px;padding:14px;"
                f"height:100%'><b style='color:{AMBER}'>🚩 Anomaly score</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>How far the occupancy sits outside normal for "
                f"this demand and this green share. A busy peak does not count.</span></div>",
                unsafe_allow_html=True)
    c3.markdown(f"<div style='background:{PANEL};border-top:3px solid {TECH};border-radius:4px;padding:14px;"
                f"height:100%'><b style='color:{TECH}'>📷 Camera evidence</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>CNN grade plus Grad-CAM location. The only "
                f"column that says <i>which arm</i>.</span></div>", unsafe_allow_html=True)
    st.write("")

    st.success("**Numbers say how bad it is. The camera says which arm.** Neither is enough alone — fusion "
               "is what turns two model outputs into one instruction.")
    st.info("Note what the screen does *not* do: it never changes a stage by itself. Every row ends in a "
            "recommendation an operator approves.")


# ================================================================ 12 · the pipeline
def render_pipeline(style, animate):
    st.title("The whole system, start to finish")
    st.markdown("#### Every stage of the course, and what feeds what.")
    st.write("")

    nodes = [
        (0.6, 5.2, "🚦 Junction", AMBER), (0.6, 3.2, "📷 Camera", AMBER),
        (2.6, 5.2, "📡 Detectors", AMBER), (2.6, 3.2, "🖼️ Frames", AMBER),
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
    fig.update_layout(title="detectors → data → ML + DL → fusion → dashboard")
    st.plotly_chart(style(fig, 420), use_container_width=True)
    st.write("")

    st.markdown("### Read it as a chain, not a diagram")
    st.markdown("""
- The **numbers path** and the **image path** stay separate right up to fusion. They have to: one has named
  columns, the other does not.
- Cleaning sits *before* both models. A stuck loop that survives it becomes a false instruction four stages
  later, and nothing downstream can recover.
- Fusion is the only place the two paths meet, and it is where a prediction becomes an action.
- The dashboard converts that action into the city's own units — vehicle-hours, fuel and CO₂.
    """)
    st.info("Everything in this course is one of those boxes. If a stage feels abstract, find it on this "
            "drawing and ask what would break downstream without it.")
