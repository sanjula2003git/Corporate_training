"""
Story stages for the CNC Machining Optimization course.
=======================================================
The narrative beats that make AI inevitable for a Manufacturing / Mechanical
Engineering student who has never met it:

  shopfloor       - a batch to cut. Push hard and wreck tools; push soft and lose the shift.
  enter-ai        - machinist + sensors. Not a replacement: watch every cut, not just the first.
  trial           - one machining pass. Reality BECOMES a row of readings.
  two-records     - readings vs a surface image. Can one model do both?
  surface-problem - a grid of pixels. Which one is the defect? None.
  handmade        - reduce the image to average brightness by hand. Watch it miss chatter.
  why-dl          - therefore: Deep Learning.
  machinist-brain - how a machinist decides -> that IS a neuron.
  learning-loop   - predict -> measure -> adjust -> repeat, before terminology.
  cnn-journey     - filters slide over the surface and learn the defect pattern.
  tool-chipping   - a CNN calls the chip AND shows where it looked (Grad-CAM).
  audit           - a machining audit. The confusion matrix emerges from it.
  fusion-engine   - the product: back off the feed, change the tool.
  pipeline        - the whole machining workflow, start to finish.

The surface and tool images are fully synthetic (numpy), rendered as heatmaps.
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

NOSE_R = 0.8
RA_LIMIT = 3.5


# ================================================================ physics (echo of app.py)
def _vib(Vc, f, ap, wear=0.0):
    return 0.6 + 1.5 * ap + 0.008 * Vc + 2.2 * wear


def _tool_life(Vc, f, ap):
    return 22.0 * (180.0 / Vc) ** 2.2 * (0.25 / f) ** 0.55 * (2.0 / ap) ** 0.35


def _roughness(f, wear, vib):
    return (f ** 2) / (32.0 * NOSE_R) * 1000.0 * (1 + 0.5 * wear) + 0.12 * vib


# ================================================================ synthetic images
@st.cache_data(show_spinner=False)
def make_surface(kind="good", feed=0.20, size=64, seed=0):
    """A machined surface as a brightness grid. Good = fine, even feed marks.
    Chatter = the same marks with a low-frequency band across them. Torn =
    irregular dark tears. Means are kept similar so brightness alone can't grade it."""
    rng = np.random.default_rng(seed)
    Y, X = np.mgrid[0:size, 0:size]
    period = 2.5 + feed * 12          # finer grooves at low feed
    grooves = 0.5 + 0.22 * np.sin(2 * np.pi * Y / period)
    img = grooves + rng.normal(0, 0.03, (size, size))
    if kind == "chatter":
        band = 0.5 + 0.5 * np.sin(2 * np.pi * X / 15.0)     # chatter bands across the feed
        img = 0.5 + (img - 0.5) * (0.5 + 1.1 * band)
        img += 0.12 * np.sin(2 * np.pi * (X + Y) / 9.0)
    elif kind == "torn":
        for _ in range(7):
            cy, cx = rng.integers(6, size - 6, 2)
            r = rng.integers(3, 7)
            img[(Y - cy) ** 2 + (X - cx) ** 2 < r ** 2] -= rng.uniform(0.25, 0.45)
    elif kind == "good-bright":
        img = img + 0.12
    return np.clip(img, 0, 1)


@st.cache_data(show_spinner=False)
def make_tool_edge(chipped=False, size=64, seed=1):
    """A tool cutting edge, top view. Bright tool body meets dark background at a
    near-vertical edge. A chip is a small bite taken out of that edge. Returns the
    image and a Grad-CAM-style heat map that concentrates on the chip."""
    rng = np.random.default_rng(seed)
    Y, X = np.mgrid[0:size, 0:size]
    edge = 40 + 2.0 * np.sin(Y / 9.0)
    img = np.where(X < edge, 0.82, 0.16).astype(float)
    cam = np.full((size, size), 0.08)
    if chipped:
        cy, cx = 32, 40
        chip = ((Y - cy) ** 2 + (X - cx) ** 2 < 5.5 ** 2) & (X < cx + 3)
        img[chip] = 0.16                                  # bite out of the edge
        cam = 0.08 + 0.92 * np.exp(-(((Y - cy) ** 2 + (X - cx) ** 2) / (2 * 6.0 ** 2)))
    img = np.clip(img + rng.normal(0, 0.03, (size, size)), 0, 1)
    return img, cam


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


# ================================================================ 1 · the shop floor
def render_shopfloor(style, animate):
    st.title("A batch on the machine — choosing the settings")
    st.markdown("#### Push the cut too hard and you wreck tools. Cut too soft and the shift runs long.")
    st.caption("You set one dial: how hard to push. Everything else follows from it.")

    ap = 1.5
    rate, tool_cost, scrap_cost = 75.0, 35.0, 20.0

    def economics(aggr):
        Vc = 80 + aggr * 190
        f = 0.08 + aggr * 0.34
        mrr = Vc * f * ap
        batch_time = 60.0 / mrr                         # relative hours for a fixed batch
        life = _tool_life(Vc, f, ap)
        tools = batch_time * 60 / max(life, 1)
        Ra = _roughness(f, 0.15, _vib(Vc, f, ap))
        scrap_rate = 1 / (1 + np.exp(-(Ra - RA_LIMIT) * 4))   # rises as finish blows the limit
        cost = batch_time * rate + tools * tool_cost + scrap_rate * 100 * scrap_cost
        return Vc, f, batch_time, tools, Ra, scrap_rate, cost

    aggr = st.slider("How hard do you push the cut?  (conservative → aggressive)", 0.0, 1.0, 0.5, 0.02)
    Vc, f, bt, tools, Ra, scrap_rate, cost = economics(aggr)

    grid = np.linspace(0, 1, 100)
    costs = np.array([economics(a)[6] for a in grid])
    best_a = grid[int(np.argmin(costs))]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=grid, y=costs, mode="lines", line=dict(color=MUTED, width=2),
                             name="total cost"))
    fig.add_trace(go.Scatter(x=[best_a], y=[costs.argmin() and costs.min()], mode="markers",
                             marker=dict(size=14, color=GREEN, symbol="star"), name="sweet spot"))
    fig.add_trace(go.Scatter(x=[aggr], y=[cost], mode="markers",
                             marker=dict(size=15, color=POS), name="your setting"))
    fig.update_layout(title="total cost per batch vs how hard you push")
    fig.update_xaxes(title="conservative  ←   aggressiveness   →  aggressive")
    fig.update_yaxes(title="cost ($, relative)")
    st.plotly_chart(style(fig, 380), use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Speed / feed", f"{Vc:.0f} / {f:.2f}")
    c2.metric("Batch time", f"{bt:.1f} h")
    c3.metric("Inserts used", f"{tools:.0f}")
    c4.metric("Scrap risk", f"{scrap_rate*100:.0f}%",
              delta="finish out of tolerance" if Ra > RA_LIMIT else "finish OK",
              delta_color="inverse")

    st.markdown("### So — can you find the best setting by hand?")
    if st.button("Answer", type="primary"):
        st.error("**Not reliably.** One dial has a clean U-shape. Real machining has three dials — speed, "
                 "feed and depth — that interact, on every new material and tool. The sweet spot moves, and "
                 "there are thousands of combinations.")
        st.info("👉 So the fix is not a better machinist — it is a model that can score every setting and "
                "hand back the fastest safe one. The machinist stays in charge; the search is what AI takes "
                "off their plate.")


# ================================================================ 2 · continuous monitoring
def render_enter_ai(style, animate):
    st.title("A second set of senses — continuous cut monitoring")
    st.markdown("#### Same machine, same job. Check only the first part, or every part?")
    parts = 40
    rng = np.random.default_rng(3)
    wear = np.linspace(0, 1, parts) ** 1.6                      # the tool dulls through the batch
    Ra = _roughness(0.2, wear, _vib(180, 0.2, 1.5)) + rng.normal(0, 0.08, parts)
    crossed = np.where(Ra > RA_LIMIT)[0]
    first_bad = int(crossed[0]) + 1 if len(crossed) else parts

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=Ra, x=np.arange(1, parts + 1), mode="lines+markers",
                             line=dict(color=POS, width=2), name="surface roughness"))
    fig.add_hline(y=RA_LIMIT, line=dict(color=RED, width=2, dash="dash"),
                  annotation_text="tolerance limit", annotation_position="top left")
    fig.add_trace(go.Scatter(x=[1], y=[Ra[0]], mode="markers",
                             marker=dict(size=18, color=AMBER, symbol="circle-open",
                                         line=dict(width=3)), name="first-article check only"))
    fig.update_layout(title="surface roughness across the batch as the tool wears")
    fig.update_xaxes(title="part number"); fig.update_yaxes(title="roughness (µm)")
    st.plotly_chart(style(fig, 380), use_container_width=True)

    missed = int((Ra > RA_LIMIT).sum())
    c1, c2 = st.columns(2)
    c1.metric("Scrap missed — first-article check", missed, delta_color="inverse")
    c2.metric("Scrap missed — continuous check", 0, f"-{missed}")
    st.success(f"Checking only part 1 passes the whole batch — the tool was still sharp then. It wears "
               f"mid-batch, and from part {first_bad} on, every part is out of tolerance and nobody looked. "
               f"Continuous monitoring catches the drift the moment it crosses the line.")

    st.markdown("### Machinist **+** AI. Never machinist *vs* AI.")
    a, b = st.columns(2)
    a.markdown("**The machinist stays in charge of**\n\n- diagnosing the actual cause\n- judging if a part "
               "is fit to ship\n- feeling a hot chuck, hearing a dull tool\n- setting and signing the "
               "job\n- judgement — which AI has none of")
    b.markdown("**Where one person needs a hand**\n\n- checking every part, not just the first\n- searching "
               "thousands of settings\n- staying alert across three shifts\n- reading vibration to 0.1 mm/s"
               "\n- never looking away")
    st.info("The system's job is not to decide. It hands the machinist **the cuts that matter right now** "
            "and the setting worth trying, so a person makes the call. The machinist is superior — AI just "
            "eases the load one pair of hands cannot carry.")


# ================================================================ 3 · one cutting pass
def render_trial(get_data, style, animate):
    st.title("One cutting pass — how a cut becomes data")
    st.markdown("#### The model will never stand at your machine.")
    d = get_data()
    row = d["dirty"].iloc[5]

    st.markdown("You set the parameters, make the cut, and measure the result. "
                "Watch what actually reaches the model:")
    steps = [
        ("🛠️  The real cut", "The tool bites the steel. Swarf curls off, the spindle loads up, the edge "
                             "starts to dull.", MUTED),
        ("📟  Instruments read it", "Force, vibration, temperature and current — each one number. No "
                                    "context, no cause.", POS),
        ("📷  The camera captures it", "A photo of the finished surface. Not a grade — a grid of pixels.", AMBER),
        ("📄  It becomes one row", "This row of settings, readings and outcome is the *entire* cut as far "
                                   "as the model is concerned.", GREEN),
    ]
    i = st.slider("Walk through the pass", 1, 4, 1)
    for k, (t, txt, c) in enumerate(steps, start=1):
        if k <= i:
            st.markdown(f"<div style='padding:12px 16px;margin:6px 0;border-radius:10px;"
                        f"border-left:4px solid {c};background:{PANEL};color:{TEXT}'>"
                        f"<b>{t}</b><br><span style='color:{MUTED}'>{txt}</span></div>",
                        unsafe_allow_html=True)
    if i == 4:
        st.markdown("##### What each channel records, and why it matters")
        st.dataframe(pd.DataFrame([
            ["⚡ Cutting force", "Dynamometer", "N", "Overload, rising with wear and depth"],
            ["📳 Vibration", "Accelerometer", "mm/s", "Chatter, instability"],
            ["🌡️ Temperature", "Thermocouple / IR", "°C", "Heat at high speed — tool softening"],
            ["🔌 Spindle current", "Drive", "A", "Power drawn — load and dull-tool drag"],
            ["🏃 Cutting speed", "Setting", "m/min", "Set by the machinist — drives tool life"],
            ["➡️ Feed rate", "Setting", "mm/rev", "Set by the machinist — drives the finish"],
            ["⬇️ Depth of cut", "Setting", "mm", "Set by the machinist — drives the load"],
        ], columns=["Channel", "Source", "Unit", "What it tells you"]),
            use_container_width=True, hide_index=True)

        st.markdown("##### One pass = one row of those numbers")
        cols = ["cutting_speed", "feed_rate", "depth_of_cut", "force_n", "vibration_mm_s",
                "temperature_c", "current_a"]
        st.dataframe(pd.DataFrame([row[cols].values], columns=[
            "Speed", "Feed", "Depth", "Force (N)", "Vibration", "Temp (°C)", "Current (A)"]),
            use_container_width=True, hide_index=True)
        st.info("The model never stands at your machine — it sees only this row. If the row is wrong, the "
                "prediction is wrong, and the model has no way to notice. That is why the next stages are "
                "about the data, not the model.")


# ================================================================ 4 · reading vs image
def render_two_records(style, animate):
    st.title("Two kinds of record — a reading and a surface image")
    st.markdown("#### The same part produces both. They are not the same problem.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div style='border-top:3px solid {POS};background:{PANEL};border-radius:10px;"
                    f"padding:14px'><b style='color:{POS}'>📊 The instrument summary</b><br>"
                    f"<span style='color:{MUTED};font-size:13px'>Seven values an engineer named and gave "
                    f"units. Each already means something.</span></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({
            "Channel": ["Speed", "Feed", "Depth", "Force", "Vibration", "Temp", "Current"],
            "Value": ["180 m/min", "0.20 mm/rev", "1.5 mm", "680 N", "4.6 mm/s", "300 °C", "10.4 A"],
        }), use_container_width=True, hide_index=True, height=300)
        st.caption("**7 named numbers.** A human can read it.")
    with c2:
        st.markdown(f"<div style='border-top:3px solid {AMBER};background:{PANEL};border-radius:10px;"
                    f"padding:14px'><b style='color:{AMBER}'>🖼️ The raw surface image</b><br>"
                    f"<span style='color:{MUTED};font-size:13px'>Thousands of pixels. Nothing in it is "
                    f"named.</span></div>", unsafe_allow_html=True)
        st.plotly_chart(_heat(make_surface("chatter"), title="one surface · 64 × 64 pixels", h=300),
                        use_container_width=True)
        st.caption("**4,096 unnamed numbers.** The defect is in the pattern.")

    st.info("One part, two records. The Random Forest handles the seven readings. It cannot be pointed at "
            "4,096 unnamed pixels at all, which is why deep learning is needed later.")


# ================================================================ 5 · the raw image
def render_surface_problem(style, animate):
    st.title("What the camera actually sends")
    st.markdown("#### A chatter mark — you *see* it instantly. Now find it in the numbers.")
    kind = st.selectbox("Choose a surface", ["chatter", "torn", "good"], index=0)
    img = make_surface(kind)
    st.plotly_chart(_heat(img, title=f"one surface image · {img.size:,} pixel values", h=380),
                    use_container_width=True)
    st.caption("Every pixel is just a brightness number between 0 and 1. None of them is labeled "
               "'defect'.")

    if st.button("Where is the defect?", type="primary"):
        st.error("It is not any single pixel. A chatter fault is a **repeating band** across the feed "
                 "marks; a tear is an **irregular dark patch**. The defect is a *pattern* spread over "
                 "thousands of pixels — no one number holds it.")
        st.info("At the trial an engineer had already named force and feed, so the Random Forest had "
                "features to weigh. Here nothing is pre-named. There is no column called 'defect' — only "
                "its shape, spread across the whole image.")


# ================================================================ 6 · threshold by hand
def render_handmade(style, animate):
    st.title("The finish rulebook, by hand")
    st.markdown("#### Reduce the image to one number, set a limit, watch it miss.")
    st.caption("The standard shortcut: take the average brightness of the image and reject anything too "
               "dark. It works for an obviously torn, dark surface. The problem is chatter.")

    cases = [("Good finish", make_surface("good"), GREEN),
             ("Good (brighter lighting)", make_surface("good-bright"), GREEN),
             ("Chatter (defect)", make_surface("chatter"), RED),
             ("Torn (defect)", make_surface("torn"), RED)]
    means = [(n, float(im.mean()), c) for n, im, c in cases]

    thr = st.slider("Set the average-brightness reject threshold", 0.30, 0.70, 0.45, 0.01)
    fig = go.Figure()
    for n, v, c in means:
        fig.add_trace(go.Bar(x=[n], y=[v], marker_color=c, showlegend=False,
                             text=f"{v:.2f}", textposition="outside"))
    fig.add_hline(y=thr, line=dict(color=POS, width=2, dash="dash"),
                  annotation_text=f"reject below {thr:.2f}", annotation_position="top left")
    fig.update_layout(title="one number per image — can a line separate defect from good?")
    fig.update_yaxes(title="average brightness", range=[0, 0.8])
    st.plotly_chart(style(fig, 360), use_container_width=True)

    missed = [n for n, v, c in means if c == RED and v >= thr]
    false_al = [n for n, v, c in means if c == GREEN and v < thr]
    a, b = st.columns(2)
    a.metric("Defects missed", len(missed), ", ".join(missed) or "none")
    b.metric("Good parts rejected", len(false_al), ", ".join(false_al) or "none")
    st.warning("**Chatter has almost the same average brightness as a good finish** — the banding cancels "
               "out in the mean. One number throws away the pattern that actually distinguishes them. Every "
               "hand-made image feature is a rule you must maintain, and each discards most of the picture.")


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
                    f"<li>Different for every material and finish</li>"
                    f"<li>You maintain it forever</li></ul></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='border-top:3px solid {GREEN};background:{PANEL};border-radius:10px;"
                    f"padding:16px;height:100%'><b style='color:{GREEN}'>Learning from examples</b>"
                    f"<ul style='color:{MUTED};font-size:14px;line-height:1.7'>"
                    f"<li>You supply good and defective images</li>"
                    f"<li>The network discovers the features itself</li>"
                    f"<li>It finds the pattern wherever it appears</li>"
                    f"<li>No rulebook to maintain</li></ul></div>", unsafe_allow_html=True)
    st.info("Deep learning does not dig deeper into your named readings — machine learning already handles "
            "those. It works where there are **no named readings at all**: the raw image. When nobody can "
            "write the rule, the model learns it from examples. That is the turning point of this course.")


# ================================================================ 8 · the machinist's judgement
def render_machinist_brain(style):
    st.title("The machinist's judgement — that is a neuron")
    st.markdown("#### Weigh each signal by how much it predicts a bad part, sum, decide.")
    st.caption("Move each weight to match how much *you* would trust that signal, and watch the decision.")
    signals = [("Vibration high", 0.9), ("Feed high", 0.7), ("Cutting force high", 0.5),
               ("Temperature high", 0.4), ("Speed high", 0.3)]
    vals, weights = [], []
    for name, default in signals:
        w = st.slider(name, 0.0, 1.0, default, 0.05, key=f"mb_{name}")
        weights.append(w)
        vals.append(1.0)
    z = float(np.dot(vals, weights)) - 1.6
    p = 1 / (1 + np.exp(-z))
    st.metric("Weighted evidence → scrap probability", f"{p*100:.0f}%")
    call = "🔴 REJECT / BACK OFF" if p > 0.5 else "🟢 RUN THE CUT"
    st.markdown(f"<div style='padding:18px;border-radius:10px;text-align:center;font-size:20px;"
                f"font-weight:700;background:{RED if p>0.5 else GREEN};color:#0e1117'>{call}</div>",
                unsafe_allow_html=True)
    st.info("Weigh each input, sum, add a baseline, decide. That is exactly one artificial **neuron**. The "
            "weights are what the machinist's experience becomes — and learning is just setting them from "
            "data instead of by hand.")


# ================================================================ 9 · the learning loop
def render_learning_loop(style, animate):
    st.title("Every scrapped part teaches — the learning loop")
    st.markdown("#### Predict → see the part → adjust → repeat.")
    steps = [("① Predict", "The model calls a setting good or scrap.", POS),
             ("② Measure", "The measured part says what actually came off.", AMBER),
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
    st.plotly_chart(style(fig, 360), use_container_width=True)
    for name, txt, c in steps:
        st.markdown(f"<div style='border-left:4px solid {c};padding:4px 0 4px 14px;margin:4px 0;"
                    f"color:{TEXT}'><b>{name}</b> — <span style='color:{MUTED}'>{txt}</span></div>",
                    unsafe_allow_html=True)
    st.info("Done by hand this loop takes a career, and the lessons live in one person's head. Training "
            "runs the same loop thousands of times a second, and the lesson lives in the weights.")


# ================================================================ 10 · inside the CNN
def render_cnn_journey(style, animate):
    st.title("Inside the CNN — reading the surface")
    st.markdown("#### Small learned filters slide across the image and fire on the defect pattern.")
    kind = st.selectbox("Choose a surface to feed the CNN", ["chatter", "good", "torn"], index=0)
    img = make_surface(kind)

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
            ("Texture filter", np.abs(_conv2d(img, lap)))]
    cols = st.columns(3)
    for col, (name, fm) in zip(cols, maps):
        col.plotly_chart(_heat(fm, colorscale="Inferno", title=name, h=250),
                         use_container_width=True)

    score = float(np.abs(_conv2d(img, lap)).mean())
    verdict = "DEFECT" if score > 0.10 else "good finish"
    colr = RED if score > 0.10 else GREEN
    st.markdown(f"<div style='padding:14px;border-radius:10px;text-align:center;font-size:18px;"
                f"font-weight:700;background:{colr};color:#0e1117'>CNN grade: {verdict} "
                f"(texture energy {score:.3f})</div>", unsafe_allow_html=True)
    st.caption("▶ Press Play to watch the filter sweep the image. Early filters find simple edges; deeper "
               "layers pool them into one grade.")
    st.info("The network **learns** these filters from labeled images — you never wrote the rule the "
            "hand-made brightness threshold could not capture. A chatter surface lights up the texture "
            "filter that a good finish leaves quiet.")


# ================================================================ 11 · tool chipping + Grad-CAM
def render_tool_chipping(style, animate):
    st.title("Detecting a chipped tool — and showing where")
    st.markdown("#### The CNN calls the chip, and Grad-CAM points to the pixels that convinced it.")
    chipped = st.toggle("Show a chipped tool edge", value=True)
    img, cam = make_tool_edge(chipped=chipped)

    # a defect score calibrated against both classes so the boundary sits at ~0.5
    lap = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], float)

    def energy(im):
        return float(np.abs(_conv2d(im, lap)).mean())
    e_intact = energy(make_tool_edge(False)[0])
    e_chip = energy(make_tool_edge(True)[0])
    e = energy(img)
    z = 8.0 * (e - (e_intact + e_chip) / 2) / (e_chip - e_intact + 1e-9)
    prob = 1 / (1 + np.exp(-z))

    c1, c2 = st.columns(2)
    c1.plotly_chart(_heat(img, title="tool-edge image (what the camera sees)", h=340),
                    use_container_width=True)
    c2.plotly_chart(_heat(cam, colorscale="Inferno", title="Grad-CAM — where the CNN looked", h=340),
                    use_container_width=True)

    m1, m2 = st.columns(2)
    m1.metric("CNN: chip probability", f"{prob*100:.0f}%")
    call = "🔴 CHIPPED — change the tool" if prob > 0.5 else "🟢 EDGE INTACT"
    m2.markdown(f"<div style='padding:14px;border-radius:10px;text-align:center;font-size:18px;"
                f"font-weight:700;background:{RED if prob>0.5 else GREEN};color:#0e1117;margin-top:6px'>"
                f"{call}</div>", unsafe_allow_html=True)
    st.info("A flat pass/fail is not enough — an engineer will not act on a black box. **Grad-CAM** "
            "highlights the pixels that drove the call, so the heat lands on the chip itself. The machinist "
            "sees the verdict *and* the evidence, and can overrule it. Once a tool chips, every part after "
            "it is scrap — catching it here saves the batch.")


# ================================================================ 12 · the machining audit
def render_audit(get_data, get_models, style, animate):
    st.title("The machining audit — the confusion matrix")
    st.markdown("#### Line up every call against the measured part.")
    d = get_data()
    rf, _ = get_models()
    yte = d["yte"]
    pred = rf.predict(d["Xte"])
    tn = int(((yte == 0) & (pred == 0)).sum())
    fp = int(((yte == 0) & (pred == 1)).sum())
    fn = int(((yte == 1) & (pred == 0)).sum())
    tp = int(((yte == 1) & (pred == 1)).sum())

    cells = [[("Called good · was good", tn, GREEN), ("Called scrap · was good", fp, AMBER)],
             [("Called good · was SCRAP", fn, RED), ("Called scrap · was scrap", tp, GREEN)]]
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
    c2.metric("Scrap shipped (FN)", fn, "the costly box", delta_color="inverse")
    c3.metric("Good parts rejected (FP)", fp, "wasted parts", delta_color="off")
    st.warning("Never quote accuracy alone. The **red box — called good, was scrap** — is the defect that "
               "reaches the customer, the whole reason the system exists. A model that calls everything "
               "good scores well on accuracy and misses every real defect.")


# ================================================================ 13 · fusion
def render_fusion_engine(style):
    st.title("The machining control screen — AI fusion")
    st.markdown("#### Each feed alone is close to noise. Fused, they are one recommendation.")
    c1, c2, c3, c4 = st.columns(4)
    reading = c1.slider("Reading risk (ANN)", 0.0, 1.0, 0.7, 0.05)
    surface = c2.toggle("Chatter grade (surface CNN)", value=True)
    tool = c3.toggle("Chip flag (tool CNN)", value=True)
    stage_ = c4.select_slider("Cut type", ["Roughing", "Semi-finish", "Finishing"], value="Finishing")

    stage_w = {"Roughing": 0.6, "Semi-finish": 0.8, "Finishing": 1.0}[stage_]
    urgency = (0.4 * reading + 0.3 * (1 if surface else 0) + 0.3 * (1 if tool else 0)) * stage_w

    if urgency > 0.6:
        msg, color, act = "🚨 STOP — back off feed & change the tool", RED, "Act before the next part"
    elif urgency > 0.35:
        msg, color, act = "⚠️ ADJUST — reduce feed, re-check", AMBER, "Trim the setting this cut"
    else:
        msg, color, act = "✅ RUN — keep cutting", GREEN, "No action needed"
    st.markdown(f"<div style='padding:24px;border-radius:12px;text-align:center;font-size:22px;"
                f"font-weight:700;background:{color};color:#0e1117'>{msg}<br>"
                f"<span style='font-size:15px;font-weight:500'>{act}</span></div>",
                unsafe_allow_html=True)
    st.caption(f"Fused urgency score: **{urgency:.2f}** · reading + surface + tool, weighted by how much "
               f"the finish matters on this cut.")
    st.info("Elevated force and vibration, a chatter grade from the surface CNN, and a chip flag from the "
            "tool CNN together are not three weak signals. On a finishing cut that is **one clear call**: "
            "back off and change the tool. Several models, one decision, one machinist who acts.")


# ================================================================ 14 · the whole cell
def render_pipeline(style):
    st.title("The complete optimized machining cell")
    st.markdown("#### Every stage of the course, in one flow.")
    stages = [("📟", "Sense"), ("📷", "Photo"), ("🧹", "Clean"), ("📏", "Prepare"), ("🌲", "Model"),
              ("🖼️", "Surface CNN"), ("🔩", "Tool CNN"), ("📋", "Audit"), ("🎯", "Optimize"),
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
    st.plotly_chart(style(fig, 220), use_container_width=True)
    st.info("Any single stage done well is worthless if the chain breaks: a perfect model on dirty data, or "
            "a great recommendation nobody acts on, saves no time and no tools. **The value is the whole "
            "pipeline** — ingest, clean, prepare, model, evaluate, optimize, fuse, serve.")
