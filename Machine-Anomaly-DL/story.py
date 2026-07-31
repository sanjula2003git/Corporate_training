"""
The machine, as physics — plus the narrative stages.
====================================================
THE MACHINE MODEL IS A COPY OF THE NOTEBOOK'S. Same constants, same waveform,
same spectrum averaging, same eight features — so a number quoted in
`Unusual_Machine_Behaviour_DL.ipynb` and the same number on the matching app
page always agree. Change one and you must change both.

Narrative beats:
  breakdown      - a machine fails between inspections.
  sensors        - one burst becomes eight numbers and a spectrum.
  analyst-brain  - how an analyst decides -> that IS a neuron.
  fusion-engine  - the product: this machine, this part, this many days.
  pipeline       - the whole system, start to finish.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

import scaffold as S

POS, NEG = S.POS, S.NEG
GREEN, AMBER, RED = S.GREEN, S.AMBER, S.RED
TECH, MUTED, TEXT, PANEL = S.TECH, S.MUTED, S.TEXT, S.PANEL
style, animate = S.style, S.animate

# --- the machine, as physics ------------------------------------------------
FS = 5000.0             # sampling rate, Hz
NSAMP = 2048            # samples per burst -> 0.41 s, 2.44 Hz resolution
SHAFT_HZ = 25.0         # 1500 rpm
GEAR_TEETH = 20
GEAR_HZ = SHAFT_HZ * GEAR_TEETH        # gear mesh frequency, 500 Hz
BPFO_HZ = SHAFT_HZ * 3.6               # outer-race ball pass frequency, 90 Hz
NBINS = 512                            # keep 0 .. 1248 Hz of the spectrum
TVEC = np.arange(NSAMP) / FS
FREQS = np.arange(NBINS) * FS / NSAMP
NAVG = 8                               # spectra the analyser linear-averages
DB_FLOOR = 1e-3

FEATURES = ["rms_mm_s", "peak_g", "kurtosis", "crest_factor",
            "amp_1x", "amp_2x", "bearing_temp_c", "motor_current_a"]
NICE = ["RMS (mm/s)", "Peak (g)", "Kurtosis", "Crest factor",
        "1x amp", "2x amp", "Temp (C)", "Current (A)"]
FAULTS = ["healthy", "imbalance", "misalignment", "bearing", "gear"]


def waveform(kind="healthy", load=0.70, seed=0, sev=1.0):
    """A rotating machine is never silent. Even in perfect health it shows its
    shaft speed, a little of the second harmonic, the gear mesh tone, and a
    broadband noise floor."""
    rng = np.random.default_rng(seed)
    t = TVEC
    ph = lambda: rng.uniform(0, 2 * np.pi)
    a1 = 0.55 + 0.25 * load                        # residual imbalance grows a little with load
    x = rng.normal(0, 0.10 + 0.03 * load, NSAMP)   # broadband floor
    x += a1 * np.sin(2 * np.pi * SHAFT_HZ * t + ph())
    x += 0.16 * np.sin(2 * np.pi * 2 * SHAFT_HZ * t + ph())
    x += 0.07 * np.sin(2 * np.pi * 3 * SHAFT_HZ * t + ph())
    x += 0.05 * np.sin(2 * np.pi * GEAR_HZ * t + ph())        # healthy gear mesh tone

    if kind == "imbalance":
        x += sev * 1.30 * np.sin(2 * np.pi * SHAFT_HZ * t + ph())
    elif kind == "misalignment":
        x += sev * 0.95 * np.sin(2 * np.pi * 2 * SHAFT_HZ * t + ph())
        x += sev * 0.45 * np.sin(2 * np.pi * 3 * SHAFT_HZ * t + ph())
    elif kind == "bearing":
        # spalled outer race: a repeating IMPACT that rings the housing at 800 Hz
        imp = np.zeros(NSAMP)
        imp[::max(int(FS / BPFO_HZ), 1)] = 1.0
        ring = np.exp(-TVEC[:220] * 250.0) * np.sin(2 * np.pi * 800.0 * TVEC[:220])
        x += sev * 1.10 * np.convolve(imp, ring)[:NSAMP]
    elif kind == "gear":
        # a chipped tooth: the mesh tone grows and picks up +/- 1x sidebands.
        # It is TONAL, not impulsive, and carries very little energy — which is
        # exactly why overall RMS does not move. The spectrum pages depend on this.
        x += sev * 0.13 * np.sin(2 * np.pi * GEAR_HZ * t + ph())
        x += sev * 0.07 * np.sin(2 * np.pi * (GEAR_HZ - SHAFT_HZ) * t + ph())
        x += sev * 0.07 * np.sin(2 * np.pi * (GEAR_HZ + SHAFT_HZ) * t + ph())
    return x


def raw_spectrum(x):
    """Single-sided amplitude spectrum of ONE burst, first NBINS bins."""
    return np.abs(np.fft.rfft(x * np.hanning(NSAMP)))[:NBINS] * 2.0 / NSAMP


def avg_spectrum(kind, load, rng, sev=1.0, navg=NAVG):
    """NAVG bursts, linear-averaged — what the analyser actually stores.

    A real analyser never stores one spectrum: averaging cancels what is random
    and leaves what is periodic. A gear peak standing 9σ clear of normal in an
    8-average spectrum stands barely 2σ clear in a single one, and the spectrum
    pages do not work without it.
    """
    return np.mean([raw_spectrum(waveform(kind, load, int(rng.integers(1e9)), sev))
                    for _ in range(navg)], axis=0)


def bin_at(hz):
    """Index of the spectrum bin nearest a frequency."""
    return int(np.argmin(np.abs(FREQS - hz)))


def features_from(x, kind, load, ambient, rng, sev=1.0):
    """The eight named channels an engineer would compute from one burst."""
    s = raw_spectrum(x)
    rms = float(np.sqrt(np.mean(x ** 2)))
    peak = float(np.max(np.abs(x)))
    kurt = float(np.mean((x - x.mean()) ** 4) / (x.var() ** 2 + 1e-12))
    # temperature and current are SLOW channels: they respond to friction and
    # load, and they are the last things to move.
    temp = ambient + 22.0 + 14.0 * load + (9.0 * sev if kind == "bearing" else 0.0)
    curr = 42.0 + 46.0 * load + (3.0 * sev if kind == "misalignment" else 0.0)
    return [rms, peak, kurt, peak / (rms + 1e-9),
            float(s[bin_at(SHAFT_HZ)]), float(s[bin_at(2 * SHAFT_HZ)]),
            temp + rng.normal(0, 0.4), curr + rng.normal(0, 0.6)]


def measure(kind, load, ambient, rng, sev=1.0):
    """One logged measurement: features from a burst, plus the averaged spectrum."""
    x = waveform(kind, load, seed=int(rng.integers(1e9)), sev=sev)
    return (features_from(x, kind, load, ambient, rng, sev),
            avg_spectrum(kind, load, rng, sev))


def diagnose(peak_hz):
    """The frequency map a vibration analyst already uses."""
    table = [(SHAFT_HZ, "1 × shaft", "Imbalance"),
             (2 * SHAFT_HZ, "2 × shaft", "Misalignment"),
             (GEAR_HZ, "gear mesh", "Gear tooth defect"),
             (800.0, "housing resonance", "Bearing spall")]
    hz, name, diag = min(table, key=lambda r: abs(r[0] - peak_hz))
    if abs(hz - peak_hz) > 60:
        return ("Unclassified", f"{peak_hz:.0f} Hz")
    return (diag, f"{name} ({hz:.0f} Hz)")


# ================================================================ 1 · breakdown
def render_breakdown():
    st.title("A machine that stops without warning")
    st.markdown("#### The failure is fast. The inspection is slow.")
    st.caption("Set how often the machine is inspected, and watch how much of the fault's life goes by "
               "unseen.")
    st.write("")

    days = np.arange(0, 61)
    sev = np.clip((days - 22) / 38.0, 0, 1) ** 1.7          # a spall opening up
    level = 1.0 + 0.35 * sev + 4.0 * sev ** 3               # overall level barely moves at first

    interval = st.slider("Days between inspections", 1, 60, 30, 1)
    visits = np.arange(0, 61, interval)
    detect_at = 1.0 + 0.35 * 0.55 + 4.0 * 0.55 ** 3          # the level a walk-round would notice
    seen = [v for v in visits if level[v] > detect_at]
    found = seen[0] if seen else 61

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days, y=level, mode="lines", line=dict(color=POS, width=3),
                             name="overall vibration level"))
    fig.add_trace(go.Scatter(x=visits, y=level[np.clip(visits, 0, 60)], mode="markers",
                             marker=dict(size=13, color=AMBER, symbol="triangle-down"),
                             name="inspection"))
    fig.add_hline(y=detect_at, line=dict(color=MUTED, width=2, dash="dot"),
                  annotation_text="the level a walk-round would actually notice")
    fig.add_vline(x=60, line=dict(color=RED, width=2), annotation_text="seizure",
                  annotation_position="top left")
    if found <= 60:
        fig.add_vrect(x0=22, x1=found, fillcolor=RED, opacity=0.10, line_width=0)
        fig.add_annotation(x=(22 + found) / 2, y=1.2, text="fault developing, unseen",
                           showarrow=False, font=dict(color=RED, size=12))
    fig.update_layout(title="a bearing spall over 60 days, with inspections marked (press Play)")
    fig.update_xaxes(title="day"); fig.update_yaxes(title="overall level ÷ healthy")
    style(fig, 400); animate(fig, S.line_grow(days, level, POS), ms=60)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Fault starts", "day 22")
    c2.metric("First inspection that sees it", f"day {found}" if found <= 60 else "never — it seized")
    c3.metric("Warning bought", f"{max(0, 60 - found)} days", delta_color="off")
    st.write("")

    st.markdown("### So — can you just inspect more often?")
    if st.button("Answer", type="primary"):
        st.error("**Not by hand.** A plant has hundreds of machines. Walking every one weekly is a "
                 "full-time job that still misses a fault starting the day after the visit — and the "
                 "overall level, which is what a walk-round records, **moves last**.")
        st.info("👉 The fix is not a tighter route. It is a system that listens every hour and knows what "
                "this machine's normal sounds like. The analyst stays in charge; the continuous listening "
                "is what AI takes off their plate.")
        st.warning("And there is a second problem this project exists for: **the next failure may be a "
                   "mode this plant has never seen.** There is nothing to train a classifier on.")


# ================================================================ 2 · sensors
def render_sensors(get_data):
    st.title("Where the sensors sit — and what they throw away")
    st.markdown("#### One burst of vibration becomes eight numbers. Look at what is lost.")
    st.write("")

    kind = st.selectbox("Machine state", FAULTS, index=0)
    rng = np.random.default_rng(3)
    x = waveform(kind, 0.7, seed=3)
    spec = avg_spectrum(kind, 0.7, rng)

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Scatter(x=TVEC[:500], y=x[:500], mode="lines",
                                   line=dict(color=POS, width=1)))
        fig.update_layout(title="what the accelerometer records")
        fig.update_xaxes(title="time (s)"); fig.update_yaxes(title="amplitude", range=[-4, 4])
        st.plotly_chart(style(fig, 320), use_container_width=True)
    with c2:
        fig2 = go.Figure(go.Scatter(x=FREQS, y=spec + 1e-5, mode="lines",
                                    line=dict(color=TECH, width=1)))
        fig2.update_layout(title="the same burst, as a spectrum")
        fig2.update_xaxes(title="frequency (Hz)")
        fig2.update_yaxes(title="amplitude", type="log", range=[-4, 0])
        st.plotly_chart(style(fig2, 320), use_container_width=True)
    st.caption("Look at **gear** in the spectrum and remember what it looks like — a small growth at the "
               "500 Hz mesh tone with sidebands either side. It matters four pages from now.")
    st.write("")

    st.markdown("##### From 2,048 samples to eight numbers")
    rows = []
    for k in FAULTS:
        f = features_from(waveform(k, 0.7, seed=5), k, 0.7, 21.0, np.random.default_rng(0))
        rows.append([k] + [round(v, 2) for v in f])
    st.dataframe(pd.DataFrame(rows, columns=["State"] + NICE),
                 use_container_width=True, hide_index=True)
    st.write("")

    st.markdown("##### What each channel records, and why it matters")
    st.dataframe(pd.DataFrame([
        ["📈 RMS velocity", "Accelerometer", "mm/s", "Overall energy — the ISO 10816 number"],
        ["⛰️ Peak", "Accelerometer", "g", "The largest single excursion in the burst"],
        ["🔺 Kurtosis", "Computed", "—", "How spiky the trace is; impacts raise it long before RMS moves"],
        ["📊 Crest factor", "Computed", "—", "Peak ÷ RMS — another view of impacting"],
        ["1️⃣ 1× amplitude", "Spectrum bin", "—", "Energy at shaft speed: imbalance lives here"],
        ["2️⃣ 2× amplitude", "Spectrum bin", "—", "Twice shaft speed: misalignment lives here"],
        ["🌡️ Housing temperature", "Thermocouple", "°C", "Friction heats the bearing — a slow channel"],
        ["⚡ Motor current", "Clamp", "A", "Load, and the extra a dragging coupling draws"],
    ], columns=["Channel", "Source", "Unit", "What it tells you"]),
        use_container_width=True, hide_index=True)
    st.write("")

    st.warning("**This reduction is the step the whole condition-monitoring industry is built on, and it "
               "throws information away.** That is not a criticism — 2,048 numbers an hour per machine is "
               "not something a person can review. It is simply the trade this course is about to examine.")
    st.info("Compare the **gear** row in the table with the others. Its eight numbers look almost healthy. "
            "Its spectrum does not. Keep both records.")


# ================================================================ 3 · the analyst
def render_analyst_brain():
    st.title("How an analyst decides — and why that is a neuron")
    st.markdown("#### Weigh a few signals, add them up, make one call.")
    st.caption("Move the readings. The bar is the analyst's mental total; zero is where they raise a job.")
    st.write("")

    c1, c2 = st.columns([1, 1.3])
    with c1:
        rms = st.slider("RMS velocity (mm/s)", 0.5, 8.0, 2.4, 0.1)
        kurt = st.slider("Kurtosis (how spiky)", 2.0, 12.0, 4.5, 0.1)
        temp = st.slider("Housing temperature above ambient (°C)", 5.0, 45.0, 24.0, 0.5)
        hours = st.slider("Hours since the last overhaul (thousands)", 0.0, 40.0, 22.0, 0.5)
    weights = dict(rms=0.75, kurt=0.42, temp=0.09, hours=0.035)
    contrib = {"RMS": weights["rms"] * rms, "Kurtosis": weights["kurt"] * kurt,
               "Temperature": weights["temp"] * temp, "Hours run": weights["hours"] * hours}
    total = sum(contrib.values()) - 5.6      # bias: the analyst's baseline scepticism

    with c2:
        fig = go.Figure(go.Bar(x=list(contrib), y=[contrib[n] for n in contrib],
                               marker_color=[POS, AMBER, TECH, GREEN],
                               text=[f"{contrib[n]:.1f}" for n in contrib], textposition="outside"))
        fig.update_layout(title=f"weighted evidence · total after baseline = {total:+.2f}")
        fig.update_yaxes(title="contribution to the call")
        st.plotly_chart(style(fig, 360), use_container_width=True)

    if total > 0:
        st.error(f"**Call: raise a job.** Weighted total {total:+.2f} clears zero.")
    else:
        st.success(f"**Call: leave it running.** Weighted total {total:+.2f} sits below zero.")
    st.write("")

    st.markdown(
        f"<div style='border-left:3px solid {POS};padding:10px 0 10px 16px;font-size:16px;color:{TEXT};"
        f"line-height:1.7'>What you just moved was <b>w · x + b</b>. Each slider is an input <i>x</i>, "
        f"each fixed multiplier is a weight <i>w</i>, the baseline scepticism is the bias <i>b</i>, and "
        f"comparing the total to zero is the activation. <b>That is a neuron</b> — the only difference in "
        f"the machine version is that nobody chooses the weights: they are learned from the log.</div>",
        unsafe_allow_html=True)
    st.info("Note what this cannot do: it needs somebody to have decided that RMS, kurtosis, temperature "
            "and hours are the right four signals. The autoencoder later needs no such decision.")


# ================================================================ 4 · the work order
def render_fusion_engine():
    st.title("The work order")
    st.markdown("#### A score, a frequency and a date — one instruction.")
    st.caption("This is the product. Everything before it existed to fill in these rows.")
    st.write("")

    rows = [
        dict(m="Machine 07 · gearbox", sev=6.4, hz=f"{GEAR_HZ:.0f} Hz mesh + sidebands",
             part="Gear tooth defect", days=17, pr="HIGH",
             act="Inspect the gearbox at the next shutdown; order a pinion"),
        dict(m="Machine 12 · motor DE bearing", sev=4.1, hz="≈ 800 Hz housing ring",
             part="Bearing spall", days=9, pr="HIGH",
             act="Order a bearing now; schedule the change within two weeks"),
        dict(m="Machine 03 · pump", sev=2.6, hz=f"{2*SHAFT_HZ:.0f} Hz (2 × shaft)",
             part="Misalignment", days=40, pr="MEDIUM",
             act="Re-align the coupling at the next planned stop"),
        dict(m="Machine 21 · fan", sev=0.8, hz="no dominant bin",
             part="—", days=0, pr="LOW", act="No action — within normal for this machine"),
    ]
    colr = {"HIGH": RED, "MEDIUM": AMBER, "LOW": GREEN}
    for r in rows:
        st.markdown(
            f"<div style='background:{PANEL};border-left:5px solid {colr[r['pr']]};border-radius:4px;"
            f"padding:14px 18px;margin:8px 0'>"
            f"<div style='display:flex;justify-content:space-between;align-items:baseline'>"
            f"<b style='color:{TEXT};font-size:17px'>{r['m']}</b>"
            f"<span style='color:{colr[r['pr']]};font-size:12px;letter-spacing:.14em'>{r['pr']}</span></div>"
            f"<span style='color:{MUTED};font-size:14px'>"
            f"📉 severity <b style='color:{POS}'>{r['sev']:.1f}σ</b> &nbsp;·&nbsp; "
            f"🔎 error peak at <b>{r['hz']}</b> &nbsp;·&nbsp; "
            f"🔧 {r['part']} &nbsp;·&nbsp; "
            f"⏱️ {'about ' + str(r['days']) + ' days' if r['days'] else 'no trend'}</span><br>"
            f"<span style='color:{GREEN};font-size:15px'>▸ {r['act']}</span></div>",
            unsafe_allow_html=True)

    st.write("")
    st.divider()
    st.markdown("### Where each column came from")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div style='background:{PANEL};border-top:3px solid {POS};border-radius:4px;padding:14px;"
                f"height:100%'><b style='color:{POS}'>📉 Severity</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>The autoencoder's rebuild error, in standard "
                f"deviations of healthy. No fault was ever labelled to get it.</span></div>",
                unsafe_allow_html=True)
    c2.markdown(f"<div style='background:{PANEL};border-top:3px solid {TECH};border-radius:4px;padding:14px;"
                f"height:100%'><b style='color:{TECH}'>🔎 Frequency</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>The bin that failed to rebuild. This is the "
                f"only column that says <i>which component</i>.</span></div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='background:{PANEL};border-top:3px solid {AMBER};border-radius:4px;padding:14px;"
                f"height:100%'><b style='color:{AMBER}'>⏱️ Days</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>The trend in the score, extrapolated. This is "
                f"the column that decides whether it goes in this week's plan.</span></div>",
                unsafe_allow_html=True)
    st.write("")
    st.success("**The score says something is wrong; the frequency says what; the trend says by when.** "
               "None of the three is a work order on its own.")
    st.info("Note what the screen does *not* do: it never stops a machine by itself. Every row ends in a "
            "recommendation a planner approves.")


# ================================================================ 5 · the pipeline
def render_pipeline():
    st.title("The whole system, start to finish")
    st.markdown("#### Every stage of the course, and what feeds what.")
    st.write("")

    nodes = [
        (0.6, 5.2, "⚙️ Machine", AMBER), (0.6, 3.2, "📡 Accelerometer", AMBER),
        (2.6, 5.2, "🔢 8 features", AMBER), (2.6, 3.2, "🌊 512-bin spectrum", AMBER),
        (4.6, 5.2, "🧹 Clean", TECH), (4.6, 3.2, "📐 Per-bin scale", TECH),
        (6.4, 5.2, "⏳ AE 8→3→8", POS), (6.4, 3.2, "⏳ AE 512→16→512", POS),
        (8.4, 4.2, "🔗 Score + frequency", GREEN), (10.4, 4.2, "📋 Work order", GREEN),
    ]
    edges = [(0, 2), (1, 3), (2, 4), (3, 5), (4, 6), (5, 7), (6, 8), (7, 8), (8, 9)]

    fig = go.Figure()
    for a, b in edges:
        x0, y0 = nodes[a][0], nodes[a][1]
        x1, y1 = nodes[b][0], nodes[b][1]
        fig.add_annotation(x=x1 - 0.55, y=y1, ax=x0 + 0.55, ay=y0, xref="x", yref="y",
                           axref="x", ayref="y", showarrow=True, arrowhead=2,
                           arrowsize=1.2, arrowwidth=2, arrowcolor="#3a4655", text="")
    for x, y, label, c in nodes:
        fig.add_shape(type="rect", x0=x - 0.95, x1=x + 0.95, y0=y - 0.5, y1=y + 0.5,
                      line=dict(color=c, width=2), fillcolor=PANEL)
        fig.add_annotation(x=x, y=y, text=f"<b>{label}</b>", showarrow=False,
                           font=dict(size=12, color=TEXT))
    fig.add_annotation(x=1.6, y=6.2, text="THE NAMED-FEATURE PATH", showarrow=False,
                       font=dict(size=11, color=POS))
    fig.add_annotation(x=1.6, y=2.2, text="THE RAW-SPECTRUM PATH", showarrow=False,
                       font=dict(size=11, color=AMBER))
    fig.update_xaxes(visible=False, range=[-0.6, 11.8])
    fig.update_yaxes(visible=False, range=[1.6, 6.7])
    fig.update_layout(title="sensors → data → two autoencoders → work order")
    st.plotly_chart(style(fig, 420), use_container_width=True)
    st.write("")

    st.markdown("### Read it as a chain, not a diagram")
    st.markdown("""
- The **named-feature path** and the **raw-spectrum path** stay separate until the score is formed. They
  have to: one has columns an engineer chose, the other has 512 bins nobody named.
- Cleaning sits *before* both. A dead sensor that survives it becomes the most anomalous thing in the file
  and the monitor will report it, confidently, forever.
- Both models are trained on **healthy readings only**. No fault label enters training anywhere on this
  drawing — they exist solely to score the result afterwards.
- The work order is where a score becomes an action, and it always ends with a person.
    """)
    st.info("Everything in this course is one of those boxes. If a stage feels abstract, find it on this "
            "drawing and ask what would break downstream without it.")
