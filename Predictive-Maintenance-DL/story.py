"""
Story stages for the Predictive Maintenance course.
====================================================
The narrative beats that make AI inevitable for a Mechanical Engineering
student who has never met it:

  floor          - a shift on the floor. Machines drift to failure between rounds.
  enter-ai       - engineer + sensors. Not a replacement: continuous watching.
  inspection     - machine health check. Reality BECOMES a row of readings.
  two-signals    - readings vs a raw waveform. Can one model do both?
  signal-problem - 2,048 samples. Which one is the fault? None.
  handmade       - reduce the waveform to RMS by hand. Watch it miss early faults.
  why-dl         - therefore: Deep Learning.
  engineer-brain - how an engineer decides -> that IS a neuron.
  learning-loop  - predict -> measure -> adjust -> repeat, before terminology.
  cnn-journey    - filters slide along the signal and learn the fault pattern.
  lstm           - the degradation trend, not the snapshot -> remaining useful life.
  audit          - a reliability audit. The confusion matrix emerges from it.
  fusion-engine  - the product: Pump P-12, bearing fault, act within two weeks.
  pipeline       - the whole maintenance workflow, start to finish.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

BG, PANEL = "#0e1117", "#161b22"
POS, NEG = "#4fc3f7", "#ff8a65"
GREEN, AMBER, RED = "#66bb6a", "#ffb74d", "#ef5350"
TECH = "#ba68c8"
MUTED, TEXT = "#8b949e", "#e6edf3"

MACHINES = ["⚙️ Motor M-3", "💧 Pump P-12", "🌀 Compressor C-7", "🛠️ CNC S-2"]
MAC_COLOR = [RED, AMBER, "#ba68c8", "#4dd0e1"]


# ================================================================ shared signals
@st.cache_data(show_spinner=False)
def make_vibration(fault=False, severity=1.0, n=2048, seed=3):
    """A raw accelerometer window. Healthy = rotation + noise. Faulty = plus a
    periodic bearing impact (an impulse train ringing a resonance)."""
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    base = 0.6 * np.sin(2 * np.pi * 6 * t / n) + 0.3 * np.sin(2 * np.pi * 17 * t / n)
    noise = rng.normal(0, 0.25, n)
    sig = base + noise
    if fault:
        period = 96                       # bearing impact spacing (samples)
        ring = np.exp(-np.arange(40) / 7.0) * np.sin(2 * np.pi * 0.28 * np.arange(40))
        impacts = np.zeros(n)
        for start in range(20, n - 40, period):
            impacts[start:start + 40] += ring
        sig = sig + severity * 1.1 * impacts
    return sig


@st.cache_data(show_spinner=False)
def make_degradation(weeks=26, seed=11):
    """A machine's vibration trend over time: flat, then an accelerating rise."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, weeks)
    trend = 2.0 + 0.4 * t + 6.0 * (t ** 3.2)          # slow then steep
    trend = trend + rng.normal(0, 0.18, weeks)
    return np.round(trend, 2)


# ================================================================ the floor
@st.cache_data(show_spinner=False)
def machine_timeline(T=64):
    """A shift where four machines drift into warning/critical, and one engineer
    can only stand at one machine per round."""
    rng = np.random.default_rng(7)
    active = np.zeros((4, T), dtype=bool)
    for i in range(4):
        t = int(rng.integers(0, 8))
        while t < T:
            dur = int(rng.integers(3, 8))
            if t + dur < T:
                active[i, t:t + dur] = True
            t += dur + int(rng.integers(4, 11))
    rounds = np.array([(t // 8) % 4 for t in range(T)])       # one machine per round
    watched = active[rounds, np.arange(T)]
    missed = int(active.sum() - watched.sum())
    return active, rounds, missed


def _timeline_fig(active, rounds, style, animate, ai=False):
    T = active.shape[1]
    fig = go.Figure()
    for i in range(4):
        fig.add_trace(go.Scatter(x=list(range(T)), y=[i] * T, mode="lines",
                                 line=dict(color="#222933", width=16), hoverinfo="skip",
                                 showlegend=False))
    blocks = []
    for i in range(4):
        fig.add_trace(go.Scatter(x=[], y=[], mode="markers",
                                 marker=dict(size=15, color=MAC_COLOR[i], symbol="square"),
                                 hoverinfo="skip", showlegend=False))
        blocks.append(len(fig.data) - 1)
    fig.add_trace(go.Scatter(x=[], y=[], mode="markers",
                             marker=dict(size=26, color="rgba(0,0,0,0)",
                                         line=dict(color="#ffffff", width=3)),
                             hoverinfo="skip", showlegend=False))
    eye = len(fig.data) - 1
    fig.add_trace(go.Scatter(x=[], y=[], mode="markers",
                             marker=dict(size=17, color="rgba(0,0,0,0)",
                                         line=dict(color=RED, width=3)),
                             hoverinfo="skip", showlegend=False))
    missmark = len(fig.data) - 1

    frames, seen_miss = [], []
    for t in range(T):
        data = []
        for i in range(4):
            xs = [k for k in range(t + 1) if active[i, k]]
            data.append(go.Scatter(x=xs, y=[i] * len(xs), mode="markers",
                                   marker=dict(size=15, color=MAC_COLOR[i], symbol="square")))
        if ai:
            data.append(go.Scatter(x=[t] * 4, y=list(range(4)), mode="markers",
                                   marker=dict(size=26, color="rgba(0,0,0,0)",
                                               line=dict(color=GREEN, width=3))))
        else:
            data.append(go.Scatter(x=[t], y=[rounds[t]], mode="markers",
                                   marker=dict(size=26, color="rgba(0,0,0,0)",
                                               line=dict(color="#ffffff", width=3))))
        if not ai:
            for i in range(4):
                if active[i, t] and rounds[t] != i:
                    seen_miss.append((t, i))
            data.append(go.Scatter(x=[m[0] for m in seen_miss], y=[m[1] for m in seen_miss],
                                   mode="markers", marker=dict(size=17, color="rgba(0,0,0,0)",
                                                               line=dict(color=RED, width=3))))
            title = (f"hour {t}   ·   engineer is at <b>{MACHINES[rounds[t]]}</b>"
                     f"   ·   <span style='color:{RED}'>drift missed elsewhere: {len(seen_miss)}</span>")
        else:
            data.append(go.Scatter(x=[], y=[], mode="markers",
                                   marker=dict(size=17, color="rgba(0,0,0,0)")))
            title = f"hour {t}   ·   <span style='color:{GREEN}'>sensors watch all 4 · missed: 0</span>"
        frames.append(go.Frame(data=data, traces=blocks + [eye, missmark],
                               layout=go.Layout(title=title), name=str(t)))
    fig.update_yaxes(tickmode="array", tickvals=list(range(4)), ticktext=MACHINES,
                     range=[-0.6, 3.6])
    fig.update_xaxes(title="hours into the shift", range=[-1, T])
    style(fig, 380)
    animate(fig, frames, ms=90)
    return fig


def render_floor(style, animate):
    st.title("A shift on the factory floor")
    st.markdown("#### Four machines drift toward failure. There is one engineer.")
    active, rounds, missed = machine_timeline()
    fig = _timeline_fig(active, rounds, style, animate, ai=False)
    fig.update_layout(title="hour 0   ·   the shift begins")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("⬛ = a machine is showing warning signs   ·   ⚪ = where the engineer is standing   ·   "
               "🔴 = drift nobody was watching")

    c1, c2, c3 = st.columns(3)
    c1.metric("Warning-hours this shift", int(active.sum()))
    c2.metric("The engineer caught", int(active.sum()) - missed)
    c3.metric("Nobody was watching", missed, f"-{missed} missed", delta_color="inverse")

    st.markdown("### So — can one engineer watch all of this?")
    st.caption("Every hour of every shift. Every machine. Four drifting at once.")
    if st.button("Answer", type="primary"):
        st.error(f"**No.** One engineer is *one person* and can stand at one machine per round. This "
                 f"shift, **{missed} warning-hours** passed while they were busy at another machine. The "
                 f"limit is simple reach — one person, many machines.")
        st.info("👉 So the fix is more coverage: sensors that watch the other machines between rounds and "
                "flag the drift. The engineer stays in charge; the sensors carry the watching one person "
                "cannot cover alone.")


def render_enter_ai(style, animate):
    st.title("A second set of senses — continuous monitoring")
    st.markdown("#### Same machines. Same shift. Nothing about them changes.")
    active, rounds, missed = machine_timeline()
    fig = _timeline_fig(active, rounds, style, animate, ai=True)
    fig.update_layout(title="hour 0   ·   this time, sensors watch every machine")
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    c1.metric("Missed — engineer alone", missed, delta_color="inverse")
    c2.metric("Missed — engineer + sensors", 0, f"-{missed}")

    st.success("**Sensors do not get tired, take a break, or stand in one place.** They report every "
               "machine, every hour, so drift is caught between rounds. That repetitive watching is the "
               "one job they take off the engineer.")

    st.markdown("### Engineer **+** AI. Never engineer *vs* AI.")
    a, b = st.columns(2)
    a.markdown("**The engineer stays in charge of**\n\n- diagnosing the actual fault\n- judging if it "
               "runs to the weekend\n- feeling a hot casing, hearing a bad bearing\n- signing the work "
               "order\n- judgement — which AI has none of")
    b.markdown("**Where one person needs a hand**\n\n- watching 40 machines at once\n- sampling every "
               "second, all shift\n- staying alert across three shifts\n- reading vibration to 0.1 mm/s\n"
               "- never looking away")
    st.info("The system's job is not to decide. It hands the engineer **the machines that matter right "
            "now**, so a person makes the call. The engineer is superior — AI just eases the load one "
            "pair of hands cannot carry.")


# ================================================================ inspection
def render_inspection(get_data, style, animate):
    st.title("Machine health inspection — how a machine becomes data")
    st.markdown("#### The model will never stand at your machine.")
    d = get_data()
    row = d["dirty"].iloc[5]

    st.markdown("You inspect the pump, read every instrument, and log it. "
                "Watch what actually reaches the model:")

    steps = [
        ("🔧  The real machine", "A pump runs. The bearing is warm, the oil is darkening, vibration is "
                                "creeping up.", MUTED),
        ("📟  Instruments read it", "Each gauge reports one number. Nothing else — no context, no cause.", POS),
        ("🌊  The accelerometer captures it", "A stream of amplitude samples. Not a fault — a stream of "
                                             "numbers.", AMBER),
        ("📄  It becomes one row", "This row of readings is the *entire* machine as far as the model is "
                                   "concerned.", GREEN),
    ]
    i = st.slider("Walk through the inspection", 1, 4, 1)
    for k, (t, txt, c) in enumerate(steps, start=1):
        if k <= i:
            st.markdown(f"<div style='padding:12px 16px;margin:6px 0;border-radius:10px;"
                        f"border-left:4px solid {c};background:{PANEL};color:{TEXT}'>"
                        f"<b>{t}</b><br><span style='color:{MUTED}'>{txt}</span></div>",
                        unsafe_allow_html=True)
    if i == 4:
        st.markdown("##### What each sensor reads, and why it matters")
        st.caption("The seven instruments on each machine, the quantity each measures, and the failure "
                   "mode it is there to catch:")
        st.dataframe(pd.DataFrame([
            ["🌡️ Temperature", "Bearing / casing temperature", "°C", "Friction, lubrication loss"],
            ["🧭 Pressure", "Discharge / line pressure", "bar", "Blockage, seal leak"],
            ["📳 Vibration", "RMS velocity", "mm/s", "Bearing / imbalance / misalignment"],
            ["🔄 Speed", "Shaft speed", "RPM", "Load and duty context"],
            ["⚡ Current", "Motor current draw", "A", "Rising mechanical load"],
            ["🛢️ Oil quality", "Lubricant condition index", "0–100", "Wear debris, degradation"],
            ["⏱️ Runtime", "Hours since last service", "h", "Wear-out with age"],
        ], columns=["Sensor", "What it measures", "Unit", "Failure mode it catches"]),
            use_container_width=True, hide_index=True)

        st.markdown("##### One machine, one moment = one row of those seven numbers")
        cols = ["temperature_c", "pressure_bar", "vibration_mm_s", "rpm", "current_a",
                "oil_quality", "runtime_h"]
        st.dataframe(pd.DataFrame([row[cols].values], columns=[
            "Temp (°C)", "Pressure (bar)", "Vibration (mm/s)", "Speed (RPM)", "Current (A)",
            "Oil (0–100)", "Runtime (h)"]), use_container_width=True, hide_index=True)
        st.info("The model never stands at your machine — it sees only this row. If the row is wrong, the "
                "prediction is wrong, and the model has no way to notice. That is why the next stages are "
                "about the data, not the model.")


# ================================================================ two signals
def render_two_signals(style, animate):
    st.title("Two kinds of record — a reading and a waveform")
    st.markdown("#### The same machine produces both. They are not the same problem.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div style='border-top:3px solid {POS};background:{PANEL};border-radius:10px;"
                    f"padding:14px'><b style='color:{POS}'>📊 The instrument summary</b><br>"
                    f"<span style='color:{MUTED};font-size:13px'>Seven values an engineer named and gave "
                    f"units. Each already means something.</span></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({
            "Sensor": ["Temp", "Pressure", "Vibration", "Speed", "Current", "Oil", "Runtime"],
            "Value": ["78 °C", "5.4 bar", "6.8 mm/s", "1490 RPM", "38 A", "44", "12 400 h"],
        }), use_container_width=True, hide_index=True, height=300)
        st.caption("**7 named numbers.** A human can read it.")
    with c2:
        st.markdown(f"<div style='border-top:3px solid {AMBER};background:{PANEL};border-radius:10px;"
                    f"padding:14px'><b style='color:{AMBER}'>🌊 The raw accelerometer</b><br>"
                    f"<span style='color:{MUTED};font-size:13px'>Thousands of amplitude samples a second. "
                    f"Nothing in it is named.</span></div>", unsafe_allow_html=True)
        sig = make_vibration(fault=True)
        fig = go.Figure(go.Scatter(y=sig[:512], mode="lines", line=dict(color=AMBER, width=1)))
        fig.update_layout(title="one window · 2,048 samples")
        fig.update_xaxes(title="sample"); fig.update_yaxes(title="amplitude")
        st.plotly_chart(style(fig, 300), use_container_width=True)
        st.caption("**2,048 unnamed numbers.** The fault is in the shape.")

    st.info("One machine, two records. The Random Forest handles the seven readings. It cannot be pointed "
            "at 2,048 unnamed samples at all — which is exactly the wall that makes deep learning "
            "necessary later.")


# ================================================================ raw signal wall
def render_signal_problem(style, animate):
    st.title("What the accelerometer actually sends")
    st.markdown("#### A worn bearing — you *hear* it instantly. Now find it in the numbers.")
    sig = make_vibration(fault=True)
    st.caption(f"One vibration window from a faulty bearing: **{len(sig):,} amplitude samples.** "
               "None of them is labeled 'fault'.")

    zoom = st.slider("Zoom into a slice of the window", 64, len(sig), len(sig), step=64)
    fig = go.Figure(go.Scatter(y=sig[:zoom], mode="lines", line=dict(color=AMBER, width=1)))
    fig.update_layout(title=f"showing samples 0 … {zoom:,}")
    fig.update_xaxes(title="sample index"); fig.update_yaxes(title="amplitude")
    st.plotly_chart(style(fig, 340), use_container_width=True)

    if st.button("Where is the fault?", type="primary"):
        st.error("It is not any single sample. The fault is a **faint periodic impact** — the bearing "
                 "striking a defect once per revolution — repeating every ~96 samples and buried under "
                 "normal rotation and noise.")
        st.info("At inspection an engineer had already named temperature and pressure, so the Random "
                "Forest had features to weigh. Here nothing is pre-named. There is no column called "
                "'fault' — only its shape, spread across thousands of numbers.")


def render_handmade(style, animate):
    st.title("The vibration rulebook, by hand")
    st.markdown("#### Reduce the waveform to one number, set a limit, watch it miss.")
    st.caption("The standard approach: compute RMS level and alarm above an ISO limit. It works for a "
               "machine screaming at 8 mm/s. The problem is the *early* fault.")

    healthy = make_vibration(fault=False, seed=1)
    early = make_vibration(fault=True, severity=0.35, seed=2)      # early bearing fault
    severe = make_vibration(fault=True, severity=1.2, seed=3)
    rough = make_vibration(fault=False, seed=9) * 1.9             # healthy but rough-running

    def rms(x):
        return float(np.sqrt(np.mean(x ** 2)))
    cases = [("Healthy", rms(healthy), GREEN), ("Rough-running (healthy)", rms(rough), GREEN),
             ("Early bearing fault", rms(early), RED), ("Severe fault", rms(severe), RED)]

    thr = st.slider("Set the RMS alarm threshold (mm/s equivalent)", 0.3, 2.0, 1.1, 0.05)
    fig = go.Figure()
    for name, v, c in cases:
        fig.add_trace(go.Bar(x=[name], y=[v], marker_color=c, name=name, showlegend=False,
                             text=f"{v:.2f}", textposition="outside"))
    fig.add_hline(y=thr, line=dict(color=POS, width=2, dash="dash"),
                  annotation_text=f"threshold {thr:.2f}", annotation_position="top left")
    fig.update_layout(title="one number per machine — can a line separate fault from healthy?")
    st.plotly_chart(style(fig, 360), use_container_width=True)

    missed = [n for n, v, c in cases if c == RED and v < thr]
    false_al = [n for n, v, c in cases if c == GREEN and v >= thr]
    a, b = st.columns(2)
    a.metric("Faults missed", len(missed), ", ".join(missed) or "none")
    b.metric("False alarms", len(false_al), ", ".join(false_al) or "none")
    st.warning("No single threshold separates the **early fault** from a **rough-running healthy** "
               "machine. RMS throws away the periodic shape that actually distinguishes them. Every "
               "hand-made feature is a rule you must maintain, and each discards most of the signal.")


def render_why_dl(style):
    st.title("The rulebook runs out — therefore, deep learning")
    st.markdown("#### An expert does it instantly and cannot write down the rule.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div style='border-top:3px solid {RED};background:{PANEL};border-radius:10px;"
                    f"padding:16px;height:100%'><b style='color:{RED}'>Writing rules by hand</b>"
                    f"<ul style='color:{MUTED};font-size:14px;line-height:1.7'>"
                    f"<li>Every threshold is too tight or too loose</li>"
                    f"<li>One feature per rule, most of the signal thrown away</li>"
                    f"<li>Different for every machine type</li>"
                    f"<li>You maintain it forever</li></ul></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div style='border-top:3px solid {GREEN};background:{PANEL};border-radius:10px;"
                    f"padding:16px;height:100%'><b style='color:{GREEN}'>Learning from examples</b>"
                    f"<ul style='color:{MUTED};font-size:14px;line-height:1.7'>"
                    f"<li>You supply healthy and faulty windows</li>"
                    f"<li>The network discovers the features itself</li>"
                    f"<li>It finds the pattern wherever it appears</li>"
                    f"<li>No rulebook to maintain</li></ul></div>", unsafe_allow_html=True)
    st.info("Deep learning does not dig deeper into your named readings — machine learning already handles "
            "those. It works where there are **no named readings at all**: the raw signal. When nobody can "
            "write the rule, the model learns it from examples. That is the turning point of this course.")


# ================================================================ how a machine learns
def render_engineer_brain(style):
    st.title("The engineer's judgement — that is a neuron")
    st.markdown("#### Weigh each signal by how much it predicts trouble, sum, decide.")
    st.caption("Move each weight to match how much *you* would trust that signal, and watch the decision.")
    signals = [("Vibration high", 0.9), ("Oil degraded", 0.6), ("Temp high", 0.5),
               ("Current high", 0.4), ("Ambient warm", 0.1)]
    vals, weights = [], []
    for name, default in signals:
        w = st.slider(name, 0.0, 1.0, default, 0.05, key=f"eb_{name}")
        weights.append(w)
        vals.append(1.0)      # all signals currently "present"
    z = float(np.dot(vals, weights)) - 1.6
    p = 1 / (1 + np.exp(-z))
    st.metric("Weighted evidence → failure probability", f"{p*100:.0f}%")
    call = "🔴 PULL FOR SERVICE" if p > 0.5 else "🟢 KEEP RUNNING"
    st.markdown(f"<div style='padding:18px;border-radius:10px;text-align:center;font-size:20px;"
                f"font-weight:700;background:{RED if p>0.5 else GREEN};color:#0e1117'>{call}</div>",
                unsafe_allow_html=True)
    st.info("Weigh each input, sum, add a baseline, decide. That is exactly one artificial **neuron**. "
            "The weights are what the engineer's experience becomes — and learning is just setting them "
            "from data instead of by hand.")


def render_learning_loop(style, animate):
    st.title("Every breakdown teaches — the learning loop")
    st.markdown("#### Predict → see what happened → adjust → repeat.")
    steps = [("① Predict", "The model calls a machine healthy or failing.", POS),
             ("② Measure", "The maintenance log says what actually happened.", AMBER),
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


# ================================================================ CNN
def render_cnn_journey(style, animate):
    st.title("Inside the CNN — reading the vibration")
    st.markdown("#### A small learned filter slides along the signal and fires on the fault pattern.")
    sig = make_vibration(fault=True)[:512]
    # a crude "impact detector" filter (matched to the ringdown) — illustration of a learned filter
    filt = np.exp(-np.arange(40) / 7.0) * np.sin(2 * np.pi * 0.28 * np.arange(40))
    filt = filt / np.linalg.norm(filt)
    fmap = np.convolve(sig, filt[::-1], mode="valid")

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=sig, mode="lines", line=dict(color=AMBER, width=1),
                             name="raw signal"))
    fig.add_trace(go.Scatter(y=fmap * 0 - 3, mode="lines", line=dict(color=TECH, width=1.5),
                             name="feature map"))
    fig.add_trace(go.Scatter(x=[], y=[], mode="lines", line=dict(color=POS, width=3),
                             name="filter window"))
    frames = []
    STEP = 8
    for pos in range(0, len(sig) - 40, STEP):
        built = np.full(len(sig), np.nan)
        built[:pos + 1] = fmap[:pos + 1] - 3 if pos < len(fmap) else np.nan
        # feature map so far
        fm = np.full(len(sig), np.nan)
        upto = min(pos + 1, len(fmap))
        fm[:upto] = fmap[:upto] - 3.0
        win_x = list(range(pos, pos + 40))
        win_y = list(sig[pos:pos + 40])
        frames.append(go.Frame(data=[
            go.Scatter(y=sig, mode="lines", line=dict(color=AMBER, width=1)),
            go.Scatter(y=fm, mode="lines", line=dict(color=TECH, width=1.5)),
            go.Scatter(x=win_x, y=win_y, mode="lines", line=dict(color=POS, width=3)),
        ], name=str(pos)))
    fig.update_layout(title="raw signal (amber) · filter window (blue) · feature map building (violet)")
    fig.update_xaxes(title="sample"); fig.update_yaxes(visible=False)
    style(fig, 400); animate(fig, frames, ms=60)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("▶ Press Play. The filter slides across the window; the violet feature map spikes each "
               "time it lines up with a bearing impact.")
    st.info("Early filters find simple shapes; deeper layers combine them into a fault signature. The "
            "network **learns** these filters from labeled windows — you never wrote the rule the "
            "hand-made threshold could not capture.")


# ================================================================ LSTM
def render_lstm(style, animate):
    st.title("Reading the trend — remaining useful life")
    st.markdown("#### One reading says little; the trend is what matters.")
    trend = make_degradation()
    weeks = len(trend)
    limit = 8.0     # failure threshold mm/s

    now = st.slider("Weeks of history observed", 3, weeks, 12)
    hist = trend[:now]
    # naive projection to the failure limit from the recent slope
    slope = np.polyfit(np.arange(max(0, now - 4), now), hist[-min(4, now):], 1)[0]
    slope = max(slope, 1e-3)
    rul = max(0.0, (limit - hist[-1]) / slope)

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=hist, mode="lines+markers", line=dict(color=POS, width=2),
                             name="observed vibration"))
    fig.add_hline(y=limit, line=dict(color=RED, width=2, dash="dash"),
                  annotation_text="failure limit", annotation_position="top left")
    proj_x = [now - 1, now - 1 + rul]
    proj_y = [hist[-1], limit]
    fig.add_trace(go.Scatter(x=proj_x, y=proj_y, mode="lines", line=dict(color=AMBER, width=2, dash="dot"),
                             name="projected"))
    fig.update_layout(title="vibration trend over time")
    fig.update_xaxes(title="week"); fig.update_yaxes(title="vibration (mm/s)", range=[0, 10])
    st.plotly_chart(style(fig, 380), use_container_width=True)

    c1, c2 = st.columns(2)
    c1.metric("Latest reading", f"{hist[-1]:.1f} mm/s")
    c2.metric("Estimated remaining useful life", f"{rul:.0f} weeks",
              delta="critical" if rul < 4 else "watch" if rul < 10 else "healthy",
              delta_color="inverse")
    st.info("The tabular model sees one row and cannot tell a rising trend from a steady one — it never "
            "sees the sequence. An **LSTM** reads readings in order and carries a memory of what came "
            "before, so it answers not just *is it failing* but *how long have we got*.")


# ================================================================ audit
def render_audit(get_data, get_models, style, animate):
    st.title("The reliability audit — the confusion matrix")
    st.markdown("#### Line up every call against what actually happened.")
    d = get_data()
    rf, _ = get_models()
    yte = d["yte"]
    pred = rf.predict(d["Xte"])
    tn = int(((yte == 0) & (pred == 0)).sum())
    fp = int(((yte == 0) & (pred == 1)).sum())
    fn = int(((yte == 1) & (pred == 0)).sum())
    tp = int(((yte == 1) & (pred == 1)).sum())

    cells = [[("Called healthy · stayed healthy", tn, GREEN), ("Called failing · false alarm", fp, AMBER)],
             [("Called healthy · it FAILED", fn, RED), ("Called failing · it failed", tp, GREEN)]]
    st.write("")
    top = st.columns(2)
    top[0].caption(" ")
    top[1].caption(" ")
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
    c2.metric("Missed failures (FN)", fn, "the costly box", delta_color="inverse")
    c3.metric("False alarms (FP)", fp, "wasted callouts", delta_color="off")
    st.warning("Never quote accuracy alone. The **red box — called healthy, it failed** — is the unplanned "
               "downtime the whole system exists to prevent. A model that calls everything healthy scores "
               "well on accuracy and misses every real failure.")


# ================================================================ fusion
def render_fusion_engine(style):
    st.title("The maintenance control room — AI fusion")
    st.markdown("#### Each feed alone is close to noise. Fused, they are a work order.")
    c1, c2, c3, c4 = st.columns(4)
    reading = c1.slider("Reading risk (ANN)", 0.0, 1.0, 0.7, 0.05)
    cnn = c2.toggle("Bearing-fault pattern (CNN)", value=True)
    rul = c3.slider("Trend: weeks to limit (LSTM)", 1, 26, 3)
    crit = c4.select_slider("Asset criticality", ["Spare", "Standard", "Critical"], value="Critical")

    crit_w = {"Spare": 0.4, "Standard": 0.7, "Critical": 1.0}[crit]
    urgency = (0.4 * reading + 0.3 * (1 if cnn else 0) + 0.3 * (1 - min(rul, 26) / 26)) * crit_w

    if urgency > 0.6:
        msg, color, act = "🚨 WORK ORDER — raise now", RED, f"Act within {rul} weeks"
    elif urgency > 0.35:
        msg, color, act = "⚠️ PLAN — schedule inspection", AMBER, "Add to next planned stop"
    else:
        msg, color, act = "✅ MONITOR — keep watching", GREEN, "No action needed"
    st.markdown(f"<div style='padding:24px;border-radius:12px;text-align:center;font-size:22px;"
                f"font-weight:700;background:{color};color:#0e1117'>{msg}<br>"
                f"<span style='font-size:15px;font-weight:500'>{act}</span></div>",
                unsafe_allow_html=True)
    st.caption(f"Fused urgency score: **{urgency:.2f}** · reading + signal + trend, weighted by how "
               f"critical the asset is.")
    st.info("Pump P-12, a critical asset, with elevated reading risk, a bearing-fault pattern, and a "
            "3-week trend is not three weak signals. It is **one work order with a deadline**. Several "
            "models, one decision, one engineer who acts.")


# ================================================================ pipeline
def render_pipeline(style):
    st.title("The complete predictive-maintenance system")
    st.markdown("#### Every stage of the course, in one flow.")
    stages = [("📡", "Sense"), ("🧹", "Clean"), ("📏", "Prepare"), ("🌲", "Model"),
              ("🌊", "CNN"), ("⏳", "LSTM"), ("📋", "Audit"), ("🔗", "Fuse"), ("🔔", "Serve")]
    fig = go.Figure()
    n = len(stages)
    for i, (icon, name) in enumerate(stages):
        fig.add_shape(type="rect", x0=i - 0.4, x1=i + 0.4, y0=-0.4, y1=0.4,
                      line=dict(color=POS, width=2), fillcolor=PANEL)
        fig.add_annotation(x=i, y=0.12, text=icon, showarrow=False, font=dict(size=22))
        fig.add_annotation(x=i, y=-0.22, text=f"<b>{name}</b>", showarrow=False,
                           font=dict(size=11, color=TEXT))
        if i < n - 1:
            fig.add_annotation(x=i + 0.6, y=0, ax=i + 0.4, ay=0, xref="x", yref="y",
                               axref="x", ayref="y", showarrow=True, arrowhead=2,
                               arrowsize=1.2, arrowwidth=1.6, arrowcolor=MUTED)
    fig.update_xaxes(visible=False, range=[-0.8, n - 0.2])
    fig.update_yaxes(visible=False, range=[-0.9, 0.9])
    st.plotly_chart(style(fig, 220), use_container_width=True)
    st.info("Any single stage done well is worthless if the chain breaks: a perfect model on dirty data, "
            "or a great prediction nobody acts on, saves no downtime. **The value is the whole "
            "pipeline** — ingest, clean, prepare, model, evaluate, fuse, serve.")
