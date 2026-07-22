"""
Story stages for the Bridge Digital Twin course.
================================================
The narrative beats that make AI inevitable for a Civil / Structural Engineering
student who has never met it:

  in-service      - a bridge deteriorates every day, inspected every year or two.
  enter-ai        - inspector + sensors. Not a replacement: watch always, not on a calendar.
  reading         - one sensor sweep. The bridge's state BECOMES a row of readings.
  two-records     - readings vs a crack image. Can one model do both?
  crack-problem   - a grid of pixels. Which one is the crack? None.
  handmade        - reduce the image to average brightness by hand. Watch it miss the hairline.
  why-dl          - therefore: Deep Learning.
  engineer-brain  - how an inspector decides -> that IS a neuron.
  learning-loop   - predict -> measure -> adjust -> repeat, before terminology.
  cnn-journey     - filters slide over the surface and learn the crack pattern.
  crack-locate    - a CNN calls the crack AND shows where it looked (Grad-CAM).
  audit           - a safety audit. The confusion matrix emerges from it.
  fusion-engine   - the product: inspect this pier within the month.
  pipeline        - the whole digital twin, start to finish.

The crack and corrosion images are fully synthetic (numpy), rendered as heatmaps.
No image assets, no torch: pure illustration, consistent with the notebook.
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

INTERVENE = 55.0    # condition rating below which a component needs intervention


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


# ================================================================ deterioration (echo of app.py)
def _condition(damage):
    """Health index 0..100 from latent damage 0..1 (higher rating = healthier)."""
    return np.clip(100.0 * (1.0 - damage), 0, 100)


def _damage_curve(months, rate=0.012, accel=0.0006, seed=0, noise=1.2):
    """A component's latent damage growing over time: slow drift that accelerates,
    with a little measurement noise. Returns damage in 0..1."""
    t = np.arange(months)
    d = rate * t + accel * t ** 2
    return np.clip(d, 0, 1.2), t


# ================================================================ synthetic images
@st.cache_data(show_spinner=False)
def make_crack(kind="sound", size=64, seed=0):
    """A concrete surface as a brightness grid. Sound = even grey texture.
    Hairline = one thin dark near-vertical line (low contrast). Map = several
    branching lines. Wet = a uniformly darker but undamaged patch. Means are kept
    similar between sound and hairline so brightness alone can't grade it."""
    rng = np.random.default_rng(seed)
    Y, X = np.mgrid[0:size, 0:size]
    img = 0.62 + rng.normal(0, 0.05, (size, size))          # grey concrete + speckle
    img += 0.03 * np.sin(2 * np.pi * X / 21.0)              # faint form-work shading

    def draw_line(img, x0, drift, width, depth):
        col = x0 + drift * (Y - size / 2) / size * size
        band = np.exp(-((X - col) ** 2) / (2 * width ** 2))
        return img - depth * band

    if kind == "hairline":
        img = draw_line(img, 30, 0.25, 0.9, 0.42)
    elif kind == "map":
        img = draw_line(img, 22, 0.4, 1.1, 0.4)
        img = draw_line(img, 40, -0.3, 1.0, 0.38)
        img = draw_line(img, 32, 0.1, 0.8, 0.3)
    elif kind == "wet":
        cy, cx = 34, 30
        img -= 0.16 * np.exp(-(((Y - cy) ** 2 + (X - cx) ** 2) / (2 * 20.0 ** 2)))
    elif kind == "corrosion":
        for _ in range(6):
            cy, cx = rng.integers(10, size - 10, 2)
            r = rng.integers(4, 9)
            img[(Y - cy) ** 2 + (X - cx) ** 2 < r ** 2] -= rng.uniform(0.2, 0.4)
    return np.clip(img, 0, 1)


@st.cache_data(show_spinner=False)
def make_deck(cracked=True, size=72, seed=1):
    """A deck-soffit region, top view. A diagonal crack runs across the sound
    concrete. Returns the image and a Grad-CAM-style heat map along the crack."""
    rng = np.random.default_rng(seed)
    Y, X = np.mgrid[0:size, 0:size]
    img = 0.62 + rng.normal(0, 0.045, (size, size))
    img += 0.025 * np.sin(2 * np.pi * Y / 26.0)
    cam = np.full((size, size), 0.06)
    if cracked:
        # a diagonal path with a little meander
        path_x = 0.7 * Y + 10 + 4.0 * np.sin(Y / 8.0)
        band = np.exp(-((X - path_x) ** 2) / (2 * 1.3 ** 2))
        img = img - 0.42 * band
        cam = 0.06 + 0.94 * np.exp(-((X - path_x) ** 2) / (2 * 4.0 ** 2))
    return np.clip(img, 0, 1), cam


def _conv2d(img, k):
    win = sliding_window_view(img, k.shape)
    return np.einsum("ijkl,kl->ij", win, k)


def _heat(z, colorscale="gray", h=320, title="", showscale=False):
    fig = go.Figure(go.Heatmap(z=z, colorscale=colorscale, showscale=showscale))
    fig.update_layout(title=title, paper_bgcolor=BG, plot_bgcolor=BG, font_color=TEXT,
                      margin=dict(l=10, r=10, t=44, b=10), height=h)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, autorange="reversed", scaleanchor="x")
    return fig


# ================================================================ 1 · the bridge in service
def render_in_service(style, animate):
    st.title("A bridge under load — deterioration never stops")
    st.markdown("#### Damage grows every day. The eye only checks every year or two.")
    st.caption("Set how often the bridge is inspected, and watch how long real damage goes unseen.")

    months = 96                                         # 8 years
    dmg, t = _damage_curve(months, rate=0.010, accel=0.00055)
    cond = _condition(dmg)
    crossed = np.where(cond < INTERVENE)[0]
    onset = int(crossed[0]) if len(crossed) else months

    interval = st.slider("Months between visual inspections", 6, 36, 24, 6)
    insp_pts = np.arange(0, months, interval)
    # the first inspection AT or AFTER the condition crosses the intervention line
    seen = insp_pts[insp_pts >= onset]
    detected = int(seen[0]) if len(seen) else months
    undetected = max(0, detected - onset)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=cond, mode="lines", line=dict(color=POS, width=3),
                             name="true condition"))
    fig.add_hline(y=INTERVENE, line=dict(color=RED, width=2, dash="dash"),
                  annotation_text="intervention level", annotation_position="bottom left")
    fig.add_trace(go.Scatter(x=insp_pts, y=cond[np.clip(insp_pts, 0, months - 1)],
                             mode="markers", marker=dict(size=13, color=AMBER, symbol="triangle-down"),
                             name="visual inspection"))
    if onset < months:
        fig.add_vrect(x0=onset, x1=detected, fillcolor=RED, opacity=0.12, line_width=0)
        fig.add_annotation(x=(onset + detected) / 2, y=INTERVENE - 12,
                           text="damage present, unseen", showarrow=False,
                           font=dict(color=RED, size=12))
    fig.update_layout(title="condition over 8 years, with inspections marked (press Play)")
    fig.update_xaxes(title="month"); fig.update_yaxes(title="condition rating (100 = healthy)")
    style(fig, 400); animate(fig, _line_grow(t, cond, POS), ms=45)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Damage crosses the line", f"month {onset}")
    c2.metric("First inspection that sees it", f"month {detected}")
    c3.metric("Months damage went unseen", undetected, delta_color="inverse")

    st.markdown("### So — can you just inspect more often?")
    if st.button("Answer", type="primary"):
        st.error("**Not affordably.** Halve the interval and you double the inspection cost while still "
                 "missing damage that appears the day after a visit. Widen it to save money and damage hides "
                 "for a year or more. The calendar cannot track a process that never pauses.")
        st.info("👉 So the fix is not a better inspection schedule — it is a system that watches continuously "
                "and forecasts the condition before it crosses the line. The inspector stays in charge; the "
                "continuous watch is what AI takes off their plate.")


# ================================================================ 2 · the digital twin
def render_enter_ai(style, animate):
    st.title("A bridge that reports itself — the digital twin")
    st.markdown("#### Same structure, same job. Check on a calendar, or watch continuously?")
    months = 60
    dmg, t = _damage_curve(months, rate=0.011, accel=0.0007)
    cond = _condition(dmg)
    onset = int(np.argmax(cond < INTERVENE)) if (cond < INTERVENE).any() else months

    interval = 24
    insp_pts = np.arange(0, months, interval)
    seen = insp_pts[insp_pts >= onset]
    detected = int(seen[0]) if len(seen) else months

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=cond, mode="lines", line=dict(color=POS, width=2.5),
                             name="continuous monitoring"))
    fig.add_hline(y=INTERVENE, line=dict(color=RED, width=2, dash="dash"),
                  annotation_text="intervention level", annotation_position="bottom left")
    fig.add_trace(go.Scatter(x=insp_pts, y=cond[np.clip(insp_pts, 0, months - 1)],
                             mode="markers", marker=dict(size=15, color=AMBER, symbol="triangle-down"),
                             name="2-yearly inspection"))
    if onset < months:
        fig.add_trace(go.Scatter(x=[onset], y=[cond[onset]], mode="markers",
                                 marker=dict(size=16, color=POS, symbol="circle-open",
                                             line=dict(width=3)), name="twin catches it here"))
        fig.add_trace(go.Scatter(x=[detected], y=[cond[min(detected, months - 1)]], mode="markers",
                                 marker=dict(size=16, color=RED, symbol="x"),
                                 name="inspection catches it here"))
    fig.update_layout(title="when each approach first notices the damage (press Play)")
    fig.update_xaxes(title="month"); fig.update_yaxes(title="condition rating")
    style(fig, 400); animate(fig, _line_grow(t, cond, POS, width=2.5), ms=45)
    st.plotly_chart(fig, use_container_width=True)

    lag = max(0, detected - onset)
    c1, c2 = st.columns(2)
    c1.metric("Detection lag — 2-yearly inspection", f"{lag} months", delta_color="inverse")
    c2.metric("Detection lag — continuous twin", "0 months", f"-{lag}")
    st.success(f"The damage crosses the line in month {onset}. The next inspection is not until month "
               f"{detected}, so it hides for {lag} months. The twin flags the crossing the moment it "
               f"happens — the gap the calendar cannot close.")

    st.markdown("### Inspector **+** AI. Never inspector *vs* AI.")
    a, b = st.columns(2)
    a.markdown("**The inspector stays in charge of**\n\n- diagnosing the actual cause\n- judging if a defect "
               "is serious\n- tapping a pier, feeling the movement\n- deciding to close a lane\n- judgement "
               "— which AI has none of")
    b.markdown("**Where one person needs a hand**\n\n- watching every span, every minute\n- separating "
               "seasonal swings from damage\n- forecasting months ahead\n- reading strain to a microstrain"
               "\n- never looking away")
    st.info("The system's job is not to decide. It hands the engineer **the spans that matter right now** "
            "and the forecast worth acting on, so a person makes the call. The inspector is superior — AI "
            "just eases the load one pair of eyes cannot carry across a whole network.")


# ================================================================ 3 · one sensor sweep
def render_reading(get_data, style, animate):
    st.title("One sensor sweep — how a bridge's state becomes data")
    st.markdown("#### The model will never stand on the deck.")
    d = get_data()
    row = d["dirty"].iloc[5]

    st.markdown("At one instant the system reads every channel at once. "
                "Watch what actually reaches the model:")
    steps = [
        ("🌉  The real bridge", "Trucks cross, the deck flexes, a pier settles a hair, salt works into a "
                               "crack. All of it happening at once.", MUTED),
        ("📡  Sensors read it", "Frequency, strain, vibration, tilt, crack width, corrosion — each one "
                                "number. No context, no cause.", POS),
        ("🚁  The drone captures it", "A photo of the concrete surface. Not a grade — a grid of pixels.", AMBER),
        ("📄  It becomes one row", "This row of readings and the condition at that moment is the *entire* "
                                   "bridge as far as the model is concerned.", GREEN),
    ]
    i = st.slider("Walk through the sweep", 1, 4, 1)
    for k, (t, txt, c) in enumerate(steps, start=1):
        if k <= i:
            st.markdown(f"<div style='padding:12px 16px;margin:6px 0;border-radius:10px;"
                        f"border-left:4px solid {c};background:{PANEL};color:{TEXT}'>"
                        f"<b>{t}</b><br><span style='color:{MUTED}'>{txt}</span></div>",
                        unsafe_allow_html=True)
    if i == 4:
        st.markdown("##### What each channel records, and why it matters")
        st.dataframe(pd.DataFrame([
            ["📉 Natural frequency", "Accelerometers", "Hz", "Drops as stiffness is lost — the key early sign"],
            ["📏 Strain", "Strain gauges", "µε", "Rises under load as a section weakens"],
            ["📳 Vibration RMS", "Accelerometers", "m/s²", "Grows with damage and heavy traffic"],
            ["📐 Tilt", "Inclinometers", "°", "Settlement and rotation at piers"],
            ["🩹 Crack width", "Crack sensors", "mm", "Direct opening of a monitored crack"],
            ["🧪 Corrosion", "Corrosion probes", "%", "Section loss in the reinforcement"],
            ["🌡️ Temperature", "Weather station", "°C", "Shifts frequency — must be separated from damage"],
            ["🚚 Traffic load", "Weigh-in-motion", "t", "The live load crossing at that moment"],
        ], columns=["Channel", "Source", "Unit", "What it tells you"]),
            use_container_width=True, hide_index=True)

        st.markdown("##### One sweep = one row of those numbers")
        cols = ["nat_freq_hz", "strain_ue", "accel_rms", "tilt_deg", "crack_width_mm",
                "corrosion_pct", "temperature_c", "traffic_load_t"]
        st.dataframe(pd.DataFrame([row[cols].values], columns=[
            "Freq (Hz)", "Strain (µε)", "Vib (m/s²)", "Tilt (°)", "Crack (mm)",
            "Corr (%)", "Temp (°C)", "Load (t)"]),
            use_container_width=True, hide_index=True)
        st.info("The model never stands on the deck — it sees only this row. If the row is wrong, the "
                "estimate is wrong, and the model has no way to notice. That is why the next stages are "
                "about the data, not the model.")


# ================================================================ 4 · reading vs image
def render_two_records(style, animate):
    st.title("Two kinds of record — a reading and a crack image")
    st.markdown("#### The same span produces both. They are not the same problem.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div style='border-top:3px solid {POS};background:{PANEL};border-radius:10px;"
                    f"padding:14px'><b style='color:{POS}'>📊 The sensor summary</b><br>"
                    f"<span style='color:{MUTED};font-size:13px'>Eight values an engineer named and gave "
                    f"units. Each already means something.</span></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({
            "Channel": ["Frequency", "Strain", "Vibration", "Tilt", "Crack", "Corrosion", "Temp", "Load"],
            "Value": ["2.9 Hz", "310 µε", "0.42 m/s²", "0.18°", "0.6 mm", "14 %", "22 °C", "18 t"],
        }), use_container_width=True, hide_index=True, height=330)
        st.caption("**8 named numbers.** A human can read it.")
    with c2:
        st.markdown(f"<div style='border-top:3px solid {AMBER};background:{PANEL};border-radius:10px;"
                    f"padding:14px'><b style='color:{AMBER}'>🖼️ The raw crack image</b><br>"
                    f"<span style='color:{MUTED};font-size:13px'>Thousands of pixels. Nothing in it is "
                    f"named.</span></div>", unsafe_allow_html=True)
        st.plotly_chart(_heat(make_crack("hairline"), title="one surface · 64 × 64 pixels", h=330),
                        use_container_width=True)
        st.caption("**4,096 unnamed numbers.** The crack is in the pattern.")

    st.info("One span, two records. The Random Forest handles the eight readings. It cannot be pointed at "
            "4,096 unnamed pixels at all, which is why deep learning is needed later.")


# ================================================================ 5 · the raw image
def render_crack_problem(style, animate):
    st.title("What the drone actually sends")
    st.markdown("#### A hairline crack — you *see* it instantly. Now find it in the numbers.")
    kind = st.selectbox("Choose a surface", ["hairline", "map", "sound"], index=0)
    img = make_crack(kind)
    st.plotly_chart(_heat(img, title=f"one surface image · {img.size:,} pixel values", h=380),
                    use_container_width=True)
    st.caption("Every pixel is just a brightness number between 0 and 1. None of them is labeled 'crack'.")

    if st.button("Where is the crack?", type="primary"):
        st.error("It is not any single pixel. A crack is a **thin dark path** winding across the surface; "
                 "map-cracking is a **branching network** of them. The crack is a *pattern* spread over "
                 "hundreds of pixels — no one number holds it.")
        st.info("At the reading an engineer had already named strain and frequency, so the Random Forest had "
                "features to weigh. Here nothing is pre-named. There is no column called 'crack' — only its "
                "shape, spread across the whole image.")


# ================================================================ 6 · threshold by hand
def render_handmade(style, animate):
    st.title("The crack rulebook, by hand")
    st.markdown("#### Reduce the image to one number, set a limit, watch it miss.")
    st.caption("The standard shortcut: take the average brightness of the image and flag anything too dark. "
               "It works for an obviously map-cracked, dark surface. The problem is the hairline and the "
               "wet patch.")

    cases = [("Sound surface", make_crack("sound"), GREEN),
             ("Sound (wet patch)", make_crack("wet"), GREEN),
             ("Hairline crack (defect)", make_crack("hairline"), RED),
             ("Map-cracking (defect)", make_crack("map"), RED)]
    means = [(n, float(im.mean()), c) for n, im, c in cases]

    thr = st.slider("Set the average-brightness flag threshold", 0.45, 0.68, 0.58, 0.01)
    fig = go.Figure()
    for n, v, c in means:
        fig.add_trace(go.Bar(x=[n], y=[v], marker_color=c, showlegend=False,
                             text=f"{v:.2f}", textposition="outside"))
    fig.add_hline(y=thr, line=dict(color=POS, width=2, dash="dash"),
                  annotation_text=f"flag below {thr:.2f}", annotation_position="top left")
    fig.update_layout(title="one number per image — can a line separate defect from sound?")
    fig.update_yaxes(title="average brightness", range=[0, 0.8])
    style(fig, 360)
    animate(fig, _bars_grow([dict(x=[n], y=[v], color=c, text=f"{v:.2f}") for n, v, c in means]), ms=90)
    st.plotly_chart(fig, use_container_width=True)

    missed = [n for n, v, c in means if c == RED and v >= thr]
    false_al = [n for n, v, c in means if c == GREEN and v < thr]
    a, b = st.columns(2)
    a.metric("Defects missed", len(missed), ", ".join(missed) or "none")
    b.metric("Sound flagged", len(false_al), ", ".join(false_al) or "none")
    st.warning("**A hairline barely moves the average brightness** — one thin line among thousands of grey "
               "pixels — while a harmless wet patch drags it right down. One number throws away the pattern "
               "that actually distinguishes them. Every hand-made image feature is a rule you must maintain, "
               "and each discards most of the picture.")


# ================================================================ 7 · why deep learning
def render_why_dl(style):
    st.title("The rulebook runs out — therefore, deep learning")
    st.markdown("#### An expert grades it instantly and cannot write down the rule.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div style='border-top:3px solid {RED};background:{PANEL};border-radius:10px;"
                    f"padding:16px;height:100%'><b style='color:{RED}'>Writing rules by hand</b>"
                    f"<ul style='color:{MUTED};font-size:14px;line-height:1.7'>"
                    f"<li>Every brightness limit is too tight or too loose</li>"
                    f"<li>One feature per rule, most of the image thrown away</li>"
                    f"<li>Different for every material, light and camera angle</li>"
                    f"<li>You maintain it forever</li></ul></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='border-top:3px solid {GREEN};background:{PANEL};border-radius:10px;"
                    f"padding:16px;height:100%'><b style='color:{GREEN}'>Learning from examples</b>"
                    f"<ul style='color:{MUTED};font-size:14px;line-height:1.7'>"
                    f"<li>You supply sound and cracked images</li>"
                    f"<li>The network discovers the features itself</li>"
                    f"<li>It finds the crack wherever it appears</li>"
                    f"<li>No rulebook to maintain</li></ul></div>", unsafe_allow_html=True)
    st.info("Deep learning does not dig deeper into your named readings — machine learning already handles "
            "those. It works where there are **no named readings at all**: the raw image. When nobody can "
            "write the rule, the model learns it from examples. That is the turning point of this course.")


# ================================================================ 8 · the inspector's judgement
def render_engineer_brain(style):
    st.title("The inspector's judgement — that is a neuron")
    st.markdown("#### Weigh each signal by how much it predicts damage, sum, decide.")
    st.caption("Move each weight to match how much *you* would trust that signal, and watch the decision.")
    signals = [("Frequency drop", 0.9), ("Strain high", 0.7), ("Tilt rising", 0.6),
               ("Corrosion high", 0.5), ("Temperature high", 0.2)]
    vals, weights = [], []
    for name, default in signals:
        w = st.slider(name, 0.0, 1.0, default, 0.05, key=f"eb_{name}")
        weights.append(w)
        vals.append(1.0)
    z = float(np.dot(vals, weights)) - 1.7
    p = 1 / (1 + np.exp(-z))
    st.metric("Weighted evidence → damage probability", f"{p*100:.0f}%")
    call = "🔴 FLAG FOR INSPECTION" if p > 0.5 else "🟢 KEEP MONITORING"
    st.markdown(f"<div style='padding:18px;border-radius:10px;text-align:center;font-size:20px;"
                f"font-weight:700;background:{RED if p>0.5 else GREEN};color:#0e1117'>{call}</div>",
                unsafe_allow_html=True)
    st.info("Weigh each input, sum, add a baseline, decide. That is exactly one artificial **neuron**. The "
            "weights are what the inspector's experience becomes — and learning is just setting them from "
            "data instead of by hand.")


# ================================================================ 9 · the learning loop
def render_learning_loop(style, animate):
    st.title("Every missed crack teaches — the learning loop")
    st.markdown("#### Predict → see the true state → adjust → repeat.")
    steps = [("① Predict", "The model calls a span sound or damaged.", POS),
             ("② Measure", "The recorded condition says what was really there.", AMBER),
             ("③ Adjust", "Every weight is nudged to be a little less wrong.", TECH),
             ("④ Repeat", "Thousands of times a second, until the error stops falling.", GREEN)]
    fig = go.Figure()
    pos = [(0, 1), (1, 1), (1, 0), (0, 0)]
    for (name, _, c), (x, y) in zip(steps, pos):
        fig.add_shape(type="rect", x0=x - 0.42, x1=x + 0.42, y0=y - 0.28, y1=y + 0.28,
                      line=dict(color=c, width=2), fillcolor=PANEL)
        fig.add_annotation(x=x, y=y, text=f"<b>{name}</b>", showarrow=False,
                           font=dict(color=TEXT, size=14))
    for a, b in [(0, 1), (1, 2), (2, 3), (3, 0)]:
        fig.add_annotation(x=pos[b][0], y=pos[b][1], ax=pos[a][0], ay=pos[a][1],
                           xref="x", yref="y", axref="x", ayref="y", showarrow=True,
                           arrowhead=2, arrowsize=1.3, arrowwidth=2, arrowcolor=MUTED,
                           standoff=32, startstandoff=32)
    fig.update_xaxes(visible=False, range=[-0.8, 1.8])
    fig.update_yaxes(visible=False, range=[-0.8, 1.8])

    # a token circulates the loop (press Play) — predict → measure → adjust → repeat
    tok = lambda x, y: go.Scatter(x=[x], y=[y], mode="markers", hoverinfo="skip",
                                  marker=dict(size=22, color=POS, symbol="circle",
                                              line=dict(color=BG, width=2)))
    fig.add_trace(tok(pos[0][0], pos[0][1]))
    loop = pos + [pos[0]]
    frames = []
    for a in range(4):
        (x0, y0), (x1, y1) = loop[a], loop[a + 1]
        for tt in np.linspace(0, 1, 9, endpoint=False):
            frames.append(go.Frame(data=[tok(x0 + (x1 - x0) * tt, y0 + (y1 - y0) * tt)]))
    style(fig, 360); animate(fig, frames, ms=70)
    st.plotly_chart(fig, use_container_width=True)
    for name, txt, c in steps:
        st.markdown(f"<div style='border-left:4px solid {c};padding:4px 0 4px 14px;margin:4px 0;"
                    f"color:{TEXT}'><b>{name}</b> — <span style='color:{MUTED}'>{txt}</span></div>",
                    unsafe_allow_html=True)
    st.info("Done by hand this loop takes a career, and the lessons live in one person's head. Training "
            "runs the same loop thousands of times a second, and the lesson lives in the weights.")


# ================================================================ 10 · inside the CNN
def render_cnn_journey(style, animate):
    st.title("Inside the CNN — reading the surface")
    st.markdown("#### Small learned filters slide across the image and fire on the crack pattern.")
    kind = st.selectbox("Choose a surface to feed the CNN", ["hairline", "sound", "map"], index=0)
    img = make_crack(kind)

    # input with an animated scanning filter window
    fig = go.Figure(go.Heatmap(z=img, colorscale="gray", showscale=False))
    win = go.Scatter(x=[0], y=[0], mode="markers",
                     marker=dict(size=26, color="rgba(0,0,0,0)", line=dict(color=POS, width=3),
                                 symbol="square"))
    fig.add_trace(win)
    frames = []
    for r in range(4, 60, 6):
        for c in range(4, 60, 10):
            frames.append(go.Frame(data=[go.Heatmap(z=img, colorscale="gray", showscale=False),
                                         go.Scatter(x=[c], y=[r], mode="markers",
                                                    marker=dict(size=26, color="rgba(0,0,0,0)",
                                                                line=dict(color=POS, width=3),
                                                                symbol="square"))]))
    fig.update_layout(title="the filter window slides over every patch (press Play)",
                      paper_bgcolor=BG, plot_bgcolor=BG, font_color=TEXT,
                      margin=dict(l=10, r=10, t=44, b=10), height=380)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, autorange="reversed", scaleanchor="x")
    animate(fig, frames, ms=60)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### The feature maps each filter produces")
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], float)
    sobel_y = sobel_x.T
    lap = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], float)
    maps = [("Vertical-edge filter", np.abs(_conv2d(img, sobel_x))),
            ("Horizontal-edge filter", np.abs(_conv2d(img, sobel_y))),
            ("Line / texture filter", np.abs(_conv2d(img, lap)))]
    cols = st.columns(3)
    for col, (name, fm) in zip(cols, maps):
        col.plotly_chart(_heat(fm, colorscale="Inferno", title=name, h=250),
                         use_container_width=True)

    score = float(np.abs(_conv2d(img, lap)).mean())
    verdict = "CRACK" if score > 0.045 else "sound surface"
    colr = RED if score > 0.045 else GREEN
    st.markdown(f"<div style='padding:14px;border-radius:10px;text-align:center;font-size:18px;"
                f"font-weight:700;background:{colr};color:#0e1117'>CNN grade: {verdict} "
                f"(line energy {score:.3f})</div>", unsafe_allow_html=True)
    st.caption("▶ Press Play to watch the filter sweep the image. Early filters find simple edges; deeper "
               "layers pool them into one grade.")
    st.info("The network **learns** these filters from labeled images — you never wrote the rule the "
            "hand-made brightness threshold could not capture. A hairline lights up the line filter that a "
            "sound surface leaves quiet.")


# ================================================================ 11 · locate the crack + Grad-CAM
def render_crack_locate(style, animate):
    st.title("Locating the crack — and showing where")
    st.markdown("#### The CNN calls the crack, and Grad-CAM points to the pixels that convinced it.")
    cracked = st.toggle("Show a cracked deck region", value=True)
    img, cam = make_deck(cracked=cracked)

    # a defect score calibrated against both classes so the boundary sits at ~0.5
    lap = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], float)

    def energy(im):
        return float(np.abs(_conv2d(im, lap)).mean())
    e_sound = energy(make_deck(False)[0])
    e_crack = energy(make_deck(True)[0])
    e = energy(img)
    z = 8.0 * (e - (e_sound + e_crack) / 2) / (e_crack - e_sound + 1e-9)
    prob = 1 / (1 + np.exp(-z))

    c1, c2 = st.columns(2)
    c1.plotly_chart(_heat(img, title="deck-soffit image (what the drone sees)", h=360),
                    use_container_width=True)
    c2.plotly_chart(_heat(cam, colorscale="Inferno", title="Grad-CAM — where the CNN looked", h=360),
                    use_container_width=True)

    m1, m2 = st.columns(2)
    m1.metric("CNN: crack probability", f"{prob*100:.0f}%")
    call = "🔴 CRACK — log location & inspect" if prob > 0.5 else "🟢 SURFACE SOUND"
    m2.markdown(f"<div style='padding:14px;border-radius:10px;text-align:center;font-size:18px;"
                f"font-weight:700;background:{RED if prob>0.5 else GREEN};color:#0e1117;margin-top:6px'>"
                f"{call}</div>", unsafe_allow_html=True)
    st.info("A flat cracked/sound answer is not enough — an engineer will not act on a black box. "
            "**Grad-CAM** highlights the pixels that drove the call, so the heat lands on the crack itself. "
            "The engineer sees the verdict *and* the evidence, marks exactly where it is for the repair "
            "crew, and can overrule it.")


# ================================================================ 12 · the safety audit
def render_audit(get_data, get_models, style, animate):
    st.title("The safety audit — the confusion matrix")
    st.markdown("#### Line up every call against the recorded condition.")
    d = get_data()
    rf, _ = get_models()
    yte = d["yte"]
    pred = rf.predict(d["Xte"])
    tn = int(((yte == 0) & (pred == 0)).sum())
    fp = int(((yte == 0) & (pred == 1)).sum())
    fn = int(((yte == 1) & (pred == 0)).sum())
    tp = int(((yte == 1) & (pred == 1)).sum())

    cells = [[("Called sound · was sound", tn, GREEN), ("Called damaged · was sound", fp, AMBER)],
             [("Called sound · was DAMAGED", fn, RED), ("Called damaged · was damaged", tp, GREEN)]]
    st.write("")
    for r in range(2):
        cols = st.columns(2)
        for c in range(2):
            label, val, color = cells[r][c]
            cols[c].markdown(
                f"<div style='background:{PANEL};border:2px solid {color};border-radius:10px;"
                f"padding:18px;text-align:center'><div style='color:{MUTED};font-size:12px'>{label}</div>"
                f"<div style='color:{color};font-size:34px;font-weight:700'>{val}</div></div>",
                unsafe_allow_html=True)
    st.write("")
    acc = (tn + tp) / max(1, tn + fp + fn + tp)
    c1, c2, c3 = st.columns(3)
    c1.metric("Overall accuracy", f"{acc*100:.0f}%")
    c2.metric("Damage missed (FN)", fn, "the dangerous box", delta_color="inverse")
    c3.metric("Sound flagged (FP)", fp, "wasted inspections", delta_color="off")
    st.warning("Never quote accuracy alone. The **red box — called sound, was damaged** — is the failure "
               "left on the bridge, the whole reason the system exists. A model that calls everything sound "
               "scores well on accuracy and misses every real defect.")


# ================================================================ 13 · fusion
def render_fusion_engine(style):
    st.title("The bridge health screen — AI fusion")
    st.markdown("#### Each feed alone is close to noise. Fused, they are one prioritized call.")
    c1, c2, c3, c4 = st.columns(4)
    reading = c1.slider("Condition risk (ANN)", 0.0, 1.0, 0.6, 0.05)
    crack = c2.toggle("Crack graded (drone CNN)", value=True)
    anomaly = c3.toggle("Anomaly (unexplained)", value=True)
    rul = c4.select_slider("Forecast RUL", ["> 24 mo", "12–24 mo", "6–12 mo", "< 6 mo"], value="6–12 mo")

    rul_w = {"> 24 mo": 0.2, "12–24 mo": 0.5, "6–12 mo": 0.8, "< 6 mo": 1.0}[rul]
    urgency = (0.35 * reading + 0.2 * (1 if crack else 0) + 0.2 * (1 if anomaly else 0) + 0.25 * rul_w)

    if urgency > 0.65:
        msg, color, act = "🚨 URGENT — inspect this component now", RED, "Schedule within the week"
    elif urgency > 0.4:
        msg, color, act = "⚠️ PRIORITISE — inspect within the month", AMBER, "Add to the near-term plan"
    else:
        msg, color, act = "✅ MONITOR — no action yet", GREEN, "Keep watching"
    st.markdown(f"<div style='padding:24px;border-radius:12px;text-align:center;font-size:22px;"
                f"font-weight:700;background:{color};color:#0e1117'>{msg}<br>"
                f"<span style='font-size:15px;font-weight:500'>{act}</span></div>",
                unsafe_allow_html=True)
    st.caption(f"Fused urgency score: **{urgency:.2f}** · condition + crack + anomaly + RUL, weighted by how "
               f"close the forecast failure is.")
    st.info("A dropping condition estimate, a crack graded by the CNN, an anomaly the weather cannot "
            "explain, and a shrinking RUL together are not four weak signals. That is **one clear call**: "
            "inspect this component within the month. Several models, one prioritized alert, one engineer "
            "who acts.")


# ================================================================ 14 · the whole twin
def render_pipeline(style, animate):
    st.title("The complete bridge digital twin")
    st.markdown("#### Every stage of the course, in one flow.")
    stages = [("📡", "Sense"), ("🚁", "Photo"), ("🧹", "Clean"), ("📐", "Prepare"), ("🌲", "Model"),
              ("🖼️", "Crack CNN"), ("🌡️", "Anomaly"), ("📋", "Audit"), ("📅", "Forecast"),
              ("🔗", "Fuse"), ("🔔", "Serve")]
    fig = go.Figure()
    n = len(stages)
    for i, (icon, name) in enumerate(stages):
        fig.add_shape(type="rect", x0=i - 0.4, x1=i + 0.4, y0=-0.4, y1=0.4,
                      line=dict(color=POS, width=2), fillcolor=PANEL)
        fig.add_annotation(x=i, y=0.12, text=icon, showarrow=False, font=dict(size=20))
        fig.add_annotation(x=i, y=-0.22, text=f"<b>{name}</b>", showarrow=False,
                           font=dict(size=10, color=TEXT))
        if i < n - 1:
            fig.add_annotation(x=i + 0.6, y=0, ax=i + 0.4, ay=0, xref="x", yref="y",
                               axref="x", ayref="y", showarrow=True, arrowhead=2,
                               arrowsize=1.2, arrowwidth=1.6, arrowcolor=MUTED)
    fig.update_xaxes(visible=False, range=[-0.8, n - 0.2])
    fig.update_yaxes(visible=False, range=[-0.9, 0.9])

    # a data packet travels the whole pipeline (press Play)
    pkt = lambda x: go.Scatter(x=[x], y=[0], mode="markers", hoverinfo="skip",
                               marker=dict(size=16, color=AMBER, symbol="diamond",
                                           line=dict(color=BG, width=1.5)))
    fig.add_trace(pkt(0))
    frames = [go.Frame(data=[pkt(i / 3.0)]) for i in range(0, (n - 1) * 3 + 1)]
    style(fig, 220); animate(fig, frames, ms=70)
    st.plotly_chart(fig, use_container_width=True)
    st.info("Any single stage done well is worthless if the chain breaks: a perfect model on dirty data, or "
            "a great forecast nobody acts on, prevents no failure. **The value is the whole pipeline** — "
            "ingest, clean, prepare, model, evaluate, forecast, fuse, serve.")
