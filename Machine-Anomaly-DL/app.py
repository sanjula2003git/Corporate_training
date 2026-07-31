"""
AI for Unusual Machine Behaviour - Deep Learning illustration app
=================================================================
One project, 25 stage pages, taught as one condition-monitoring programme.
Each notebook step links here with ?stage=<id>.

The problem: a critical machine fails between monthly inspections, and the next
failure mode may be one nobody has ever labelled. So learn NORMAL, and treat
whatever cannot be rebuilt as suspicious.
  Sensors : RMS, peak, kurtosis, crest factor, 1x, 2x, housing temp, current
            + the 512-bin averaged spectrum they were reduced from.
  Classic : control chart, isolation forest, supervised classifier — each tried
            honestly until it runs out.
  DL      : an 8 → 3 → 8 autoencoder on the features, then 512 → 16 → 512 on
            the spectrum, with the per-bin error naming the component.
  System  : drift, lead time, work order, business case.

THE MACHINE MODEL IS THE NOTEBOOK'S, copied constant for constant, so numbers
quoted in Unusual_Machine_Behaviour_DL.ipynb and numbers on the matching app
page agree.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.neural_network import MLPRegressor

import scaffold as S
import common
import story
import bridge

POS, NEG = S.POS, S.NEG
GREEN, AMBER, RED = S.GREEN, S.AMBER, S.RED
TECH, MUTED, TEXT, PANEL = S.TECH, S.MUTED, S.TEXT, S.PANEL
style, animate = S.style, S.animate

st.set_page_config(page_title="AI for Unusual Machine Behaviour", page_icon="📉", layout="wide")
bridge.inject_css()

FEATURES = story.FEATURES
NICE = story.NICE
FAULTS = story.FAULTS
KNOWN = ["healthy", "imbalance", "misalignment", "bearing"]     # 'gear' is deliberately withheld


# ----------------------------------------------------------------------------
# DATA  (the analyser's export — same generator as the notebook)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="Generating the machine's monitoring log…")
def get_data(n=1000):
    rng = np.random.default_rng(42)
    # A real machine is healthy nearly all the time. The gear fault is DELIBERATELY
    # RARE and deliberately excluded from anything trained before the spectrum page.
    kinds = rng.choice(FAULTS, n, p=[0.78, 0.06, 0.06, 0.06, 0.04])
    load = np.clip(rng.normal(0.70, 0.13, n), 0.25, 1.0)
    amb = rng.normal(21.0, 2.5, n)
    sev = rng.uniform(0.45, 1.0, n)

    rowsF, rowsS = [], []
    for i in range(n):
        f, s = story.measure(kinds[i], load[i], amb[i], rng, sev[i])
        rowsF.append(f); rowsS.append(s)

    df = pd.DataFrame(rowsF, columns=FEATURES).round(4)
    df.insert(0, "reading_id", np.arange(1, n + 1))
    df["load_frac"] = load.round(3)
    df["state"] = kinds                      # LABEL — used for scoring only, never for training
    spec = np.array(rowsS)

    # the faults every real export carries
    dirty = df.copy()
    for c in FEATURES:
        dirty.loc[rng.choice(n, int(0.05 * n), replace=False), c] = np.nan
    dirty.loc[rng.choice(n, 11, replace=False), "bearing_temp_c"] = -50.0    # open thermocouple
    dirty.loc[rng.choice(n, 9, replace=False), "rms_mm_s"] = 0.0             # accelerometer fell off
    dirty.loc[rng.choice(n, 8, replace=False), "motor_current_a"] = 9999.0   # clamp saturated
    dup = rng.choice(n, 15, replace=False)
    dirty = pd.concat([dirty, dirty.iloc[dup]], ignore_index=True)
    spec_all = np.vstack([spec, spec[dup]])

    clean = dirty.drop_duplicates(subset=["reading_id"]).copy()
    spec_clean = spec_all[clean.index.to_numpy()]
    clean = clean.reset_index(drop=True)
    clean.loc[clean.bearing_temp_c < -20, "bearing_temp_c"] = np.nan
    clean.loc[clean.rms_mm_s <= 0.01, "rms_mm_s"] = np.nan
    clean.loc[clean.motor_current_a > 500, "motor_current_a"] = np.nan
    for c in FEATURES:
        clean[c] = clean[c].fillna(clean[c].median())

    healthy = (clean.state == "healthy").values
    # scale against HEALTHY only, so the error is in standard deviations of normal
    scaler = StandardScaler().fit(clean.loc[healthy, FEATURES])
    Xall = np.clip(scaler.transform(clean[FEATURES]), -10, 10)
    norm = clean.copy()
    norm[FEATURES] = Xall

    h_idx = np.where(healthy)[0]
    f_idx = np.where(~healthy)[0]
    h_tr, h_tmp = train_test_split(h_idx, test_size=0.35, random_state=42)
    h_va, h_te = train_test_split(h_tmp, test_size=0.55, random_state=42)
    ite = np.concatenate([h_te, f_idx])                 # every fault goes in the test set

    # the spectrum path: log magnitude, then standardise EACH BIN against healthy
    S_db = 20 * np.log10(spec_clean + story.DB_FLOOR)
    s_scaler = StandardScaler().fit(S_db[healthy])
    Sn = np.clip(s_scaler.transform(S_db), -10, 10)

    return dict(truth=df, dirty=dirty, clean=clean, norm=norm, scaler=scaler,
                X=Xall, spec=spec_clean, Sn=Sn, healthy=healthy,
                h_tr=h_tr, h_va=h_va, h_te=h_te, ite=ite,
                Xtr=Xall[h_tr], Xval=Xall[h_va], Xte=Xall[ite],
                ytr=(~healthy[h_tr]).astype(int), yval=(~healthy[h_va]).astype(int),
                yte=(~healthy[ite]).astype(int),
                state_te=clean.state.values[ite])


class AE:
    """An autoencoder as a scikit-learn MLP trained to reproduce its own input.

    The notebook builds the same shape in Keras and falls back to exactly this
    when TensorFlow is unavailable; the app uses the fallback so it deploys
    without a GPU-sized dependency.
    """

    def __init__(self, bottleneck=3, hidden=6, seed=0, iters=1200):
        self.m = MLPRegressor(hidden_layer_sizes=(hidden, bottleneck, hidden),
                              activation="relu", max_iter=iters, random_state=seed)

    def fit(self, X):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.m.fit(X, X)
        return self

    def error(self, X):
        """Mean squared error between each reading and its rebuild — the score."""
        return np.mean((X - self.m.predict(X)) ** 2, axis=1)

    def rebuild(self, X):
        return self.m.predict(X)


@st.cache_resource(show_spinner="Training the autoencoder on healthy readings…")
def get_ae():
    d = get_data()
    return AE(bottleneck=3, hidden=6).fit(d["Xtr"])


@st.cache_resource(show_spinner="Training the spectrum autoencoder…")
def get_spectrum_ae():
    d = get_data()
    return AE(bottleneck=16, hidden=96, iters=400).fit(d["Sn"][d["h_tr"]])


@st.cache_resource(show_spinner=False)
def get_iforest():
    d = get_data()
    return IsolationForest(n_estimators=200, contamination=0.05,
                           random_state=42).fit(d["Xtr"])


@st.cache_resource(show_spinner=False)
def get_classifier():
    """A perfectly good supervised classifier — trained on the four states the
    plant has already seen. The gear fault is withheld on purpose."""
    d = get_data()
    m = d["clean"].state.isin(KNOWN).values
    return RandomForestClassifier(n_estimators=200, random_state=42).fit(
        d["X"][m], d["clean"].state.values[m])


@st.cache_resource(show_spinner=False)
def get_models():
    """Wrapper so common.render_* can use the same interface as the sibling apps."""
    from sklearn.neural_network import MLPClassifier
    d = get_data()
    rf = RandomForestClassifier(n_estimators=200, random_state=42).fit(d["Xtr"], d["ytr"])
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mlp = MLPClassifier(hidden_layer_sizes=(12, 6), max_iter=600,
                            random_state=42).fit(d["Xtr"], d["ytr"])
    return rf, mlp


# ---- configuration for the shared data-preparation pages --------------------
CFG = dict(
    data=get_data, models=get_models, FEATURES=FEATURES, NICE=NICE,
    unit="reading", unit_plural="readings", pos="faulty", neg="healthy",
    export_name="analyser export",
    faults="An open thermocouple (−50 °C), a detached accelerometer (0.0 mm/s) and a saturated "
           "current clamp (9,999 A) all announce themselves here.",
    fault_example="−50 °C open thermocouple",
    scale_examples=[("Current reads", "78 A"), ("Temperature reads", "45 °C"),
                    ("RMS velocity reads", "2.1 mm/s")],
    scale_note="Same reading, same instant. To a raw model, current looks **forty times more important "
               "than vibration** — purely because of its unit, when RMS velocity is the channel that "
               "moves first.",
    neuron_w=[0.9, 0.7, 1.1, 0.8, 0.6, 0.5, 0.4, 0.2],
    net_pair=("kurtosis", "rms_mm_s"),
    net_note="the high-kurtosis, high-RMS corner where impacting faults live",
    fp_cost="A fitter opens a healthy machine. Cost: a few hours, and a little credibility — spend that "
            "too often and the alarms get muted.",
    fn_cost="The machine runs to failure. Cost: the unplanned breakdown, the collateral damage, and the "
            "outage nobody scheduled.",
    titles={"load": "③ The monitoring log arrives", "inspect": "④ Sensor health check",
            "clean": "⑤ Dead channels and dropouts", "normalize": "⑥ One common scale",
            "neuron": "⑫ The neuron — z = w·x + b", "activation": "⑬ Activation",
            "gradient-descent": "⑭ Loss and gradient descent"},
)


# ============================================================================
# TECHNICAL RENDERERS — the ones specific to this project
# ============================================================================
def render_split():
    st.title("⑦ Train on normal only")
    d = get_data()
    counts = d["clean"].state.value_counts()
    fig = go.Figure(go.Bar(x=counts.index.tolist(), y=counts.values,
                           marker_color=[GREEN if k == "healthy" else RED for k in counts.index],
                           text=counts.values, textposition="outside"))
    fig.update_layout(title="how often each state actually appears in months of running")
    fig.update_yaxes(title="readings")
    style(fig, 360)
    animate(fig, S.bars_grow([dict(x=counts.index.tolist(), y=list(counts.values),
                                   color=POS, text=list(counts.values))]), ms=80)
    st.plotly_chart(fig, use_container_width=True)
    st.write("")

    c = st.columns(4)
    c[0].metric("Healthy readings", int(counts.get("healthy", 0)))
    c[1].metric("Faulty readings", int(len(d["clean"]) - counts.get("healthy", 0)))
    c[2].metric("Train (healthy only)", len(d["h_tr"]))
    c[3].metric("Test (sealed)", len(d["ite"]))
    st.write("")

    st.warning("**Look at the bars before reading on.** There are a few dozen examples of each fault and "
               "thousands of healthy readings. You cannot train a classifier on that — and the gear fault, "
               "rarest of all, is held back entirely so that later pages can test on a fault nothing was "
               "trained on.")
    st.success("So the problem is inverted. **Train on healthy readings only**, and treat whatever the "
               "model cannot reproduce as suspicious. No fault label is used anywhere in training — they "
               "exist only to score the result afterwards.")


def render_control_chart():
    st.title("⑧ The 3-sigma limit")
    st.caption("The classical method, tried properly. Fit mean and spread on healthy running, then alarm "
               "on anything beyond k standard deviations.")
    st.write("")
    d = get_data()
    ch = st.selectbox("Channel to chart", FEATURES, index=0,
                      format_func=lambda c: NICE[FEATURES.index(c)])
    k = st.slider("Alarm at how many standard deviations?", 1.5, 5.0, 3.0, 0.1)

    v = d["clean"][ch].values
    hv = v[d["healthy"]]
    mu, sd = float(hv.mean()), float(hv.std()) or 1.0
    hi, lo = mu + k * sd, mu - k * sd
    idx = np.arange(len(v))
    over = (v > hi) | (v < lo)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=idx, y=v, mode="markers",
                             marker=dict(size=5, color=np.where(d["healthy"], 0, 1),
                                         colorscale=[[0, MUTED], [1, RED]]),
                             name="readings"))
    fig.add_hline(y=mu, line=dict(color=POS, width=2), annotation_text="healthy mean")
    fig.add_hline(y=hi, line=dict(color=AMBER, width=2, dash="dash"),
                  annotation_text=f"+{k:.1f}σ")
    fig.add_hline(y=lo, line=dict(color=AMBER, width=2, dash="dash"))
    fig.update_layout(title=f"{NICE[FEATURES.index(ch)]} — red points are readings that were faulty")
    fig.update_xaxes(title="reading"); fig.update_yaxes(title=NICE[FEATURES.index(ch)])
    st.plotly_chart(style(fig, 400), use_container_width=True)

    caught = int(np.sum(over & ~d["healthy"]))
    total_f = int(np.sum(~d["healthy"]))
    false_a = int(np.sum(over & d["healthy"]))
    m = st.columns(3)
    m[0].metric("Faults caught", f"{caught}/{total_f}", f"{caught/max(total_f,1):.0%} recall")
    m[1].metric("False alarms", false_a, delta_color="inverse")
    m[2].metric("Limit", f"{lo:.2f} … {hi:.2f}", delta_color="off")
    st.write("")

    st.markdown("##### Which faults does this channel see, and which does it miss?")
    per = []
    for f in FAULTS:
        m_ = (d["clean"].state == f).values
        per.append([f, int(m_.sum()), f"{np.mean(over[m_])*100:.0f}%"])
    st.dataframe(pd.DataFrame(per, columns=["State", "Readings", "Flagged by this chart"]),
                 use_container_width=True, hide_index=True)
    st.write("")
    st.info("Try RMS, then kurtosis. Each channel sees a different fault well and others barely at all — "
            "because **one chart asks one question at a time**. A fault that moves two channels a little, "
            "and neither past its own limit, passes every chart on the wall.")


def render_isolation_forest():
    st.title("⑨ Isolating the odd one out")
    st.caption("All eight channels at once, no fault labels: cut the data at random and see how few cuts "
               "it takes to isolate a reading.")
    st.write("")
    d = get_data()
    iso = get_iforest()
    score = -iso.score_samples(d["X"])          # higher = more anomalous

    q = st.slider("Alarm above which percentile of healthy score?", 90.0, 99.9, 99.0, 0.1)
    thr = float(np.percentile(score[d["healthy"]], q))
    flag = score > thr

    fig = go.Figure()
    for f, col in zip(FAULTS, [GREEN, POS, AMBER, RED, TECH]):
        m_ = (d["clean"].state == f).values
        fig.add_trace(go.Box(y=score[m_], name=f, marker_color=col, boxpoints=False))
    fig.add_hline(y=thr, line=dict(color=RED, width=2, dash="dash"),
                  annotation_text=f"alarm above {thr:.3f}")
    fig.update_layout(title="isolation-forest anomaly score by actual state")
    fig.update_yaxes(title="anomaly score")
    st.plotly_chart(style(fig, 400), use_container_width=True)

    rows = [[f, int((d["clean"].state == f).sum()),
             f"{np.mean(flag[(d['clean'].state == f).values])*100:.0f}%"] for f in FAULTS]
    st.dataframe(pd.DataFrame(rows, columns=["State", "Readings", "Flagged"]),
                 use_container_width=True, hide_index=True)
    st.write("")

    caught = int(np.sum(flag & ~d["healthy"]))
    m = st.columns(3)
    m[0].metric("Faults caught", f"{caught}/{int((~d['healthy']).sum())}",
                f"{caught/max(int((~d['healthy']).sum()),1):.0%} recall")
    m[1].metric("False alarms", int(np.sum(flag & d["healthy"])), delta_color="inverse")
    m[2].metric("Healthy percentile used", f"{q:.1f}%", delta_color="off")
    st.write("")
    st.success("A real improvement on the control chart: it uses **all eight channels together**, needs no "
               "hand-drawn envelope and no fault labels. Notice which fault it still struggles with — that "
               "is the one the spectrum page is about.")


def render_classifier_wall():
    st.title("⑩ The fault it was never taught")
    st.caption("Train a perfectly good classifier on the faults the plant has already seen. Then show it "
               "one it has not.")
    st.write("")
    d = get_data()
    clf = get_classifier()

    st.markdown(f"**Trained on:** {', '.join(KNOWN)} &nbsp;·&nbsp; **withheld:** gear")
    st.write("")

    known_m = d["clean"].state.isin(KNOWN).values
    acc = float(clf.score(d["X"][known_m], d["clean"].state.values[known_m]))
    gear_m = (d["clean"].state == "gear").values
    pred_gear = clf.predict(d["X"][gear_m])
    conf = clf.predict_proba(d["X"][gear_m]).max(axis=1)

    c = st.columns(3)
    c[0].metric("Accuracy on the faults it was taught", f"{acc:.1%}")
    c[1].metric("Gear readings shown", int(gear_m.sum()))
    c[2].metric("Times it said 'gear'", 0, "it has no such class", delta_color="off")
    st.write("")

    vals, counts = np.unique(pred_gear, return_counts=True)
    fig = go.Figure(go.Bar(x=vals.tolist(), y=counts.tolist(), marker_color=RED,
                           text=counts.tolist(), textposition="outside"))
    fig.update_layout(title="what the classifier called the gear fault it had never seen")
    fig.update_yaxes(title="readings")
    style(fig, 360)
    animate(fig, S.bars_grow([dict(x=vals.tolist(), y=list(counts), color=RED,
                                   text=list(counts))]), ms=90)
    st.plotly_chart(fig, use_container_width=True)

    st.error(f"Every one of those readings was a chipped gear tooth. The classifier assigned the nearest "
             f"label it knew — at an average confidence of **{conf.mean():.0%}**. It is not uncertain. It "
             f"cannot be: there is no output for *'none of these'*.")
    st.info("👉 That is the wall. A supervised model can only return a class it was taught. Catching the "
            "unknown means asking a different question — not *which fault is this?* but ***is this normal "
            "at all?*** Everything from here on asks the second question.")


def render_autoencoder():
    st.title("⑮ The hourglass — an autoencoder")
    st.caption("Squeeze eight channels through three, rebuild them, and train only on healthy readings. "
               "What it cannot rebuild is, by definition, not normal.")
    st.write("")
    d = get_data()
    ae = get_ae()

    # the architecture, drawn
    fig = go.Figure()
    layers = [(0.5, 8, "input\n8 channels", POS), (2.0, 6, "encode\n6", TECH),
              (3.5, 3, "bottleneck\n3", AMBER), (5.0, 6, "decode\n6", TECH),
              (6.5, 8, "rebuild\n8 channels", GREEN)]
    for x, n, lab, col in layers:
        ys = np.linspace(-n / 2, n / 2, n)
        fig.add_trace(go.Scatter(x=[x] * n, y=ys, mode="markers",
                                 marker=dict(size=13, color=col, line=dict(color="#0e1117", width=1)),
                                 showlegend=False, hoverinfo="skip"))
        fig.add_annotation(x=x, y=5.4, text=lab.replace("\n", "<br>"), showarrow=False,
                           font=dict(size=11, color=col))
    fig.update_xaxes(visible=False, range=[0, 7]); fig.update_yaxes(visible=False, range=[-5.5, 6.6])
    fig.update_layout(title="8 → 6 → 3 → 6 → 8 · the squeeze is the whole point")
    st.plotly_chart(style(fig, 300), use_container_width=True)
    st.write("")

    err = ae.error(d["X"])
    fig2 = go.Figure()
    fig2.add_trace(go.Histogram(x=err[d["healthy"]], nbinsx=60, marker_color=GREEN,
                                name="healthy", opacity=0.75))
    fig2.add_trace(go.Histogram(x=err[~d["healthy"]], nbinsx=60, marker_color=RED,
                                name="faulty", opacity=0.75))
    fig2.update_layout(barmode="overlay", title="rebuild error — the network was never shown a fault")
    fig2.update_xaxes(title="mean squared rebuild error", range=[0, float(np.percentile(err, 99))])
    fig2.update_yaxes(title="readings")
    st.plotly_chart(style(fig2, 380), use_container_width=True)

    c = st.columns(3)
    c[0].metric("Error on healthy training readings", f"{ae.error(d['Xtr']).mean():.3f}")
    c[1].metric("Error on faulty readings", f"{err[~d['healthy']].mean():.3f}")
    c[2].metric("Ratio", f"{err[~d['healthy']].mean() / max(ae.error(d['Xtr']).mean(), 1e-9):.1f}×")
    st.write("")
    st.success("The network was never told what a fault is. It is simply **worse at rebuilding one**, "
               "because a fault is not something healthy readings ever contained. That failure to rebuild "
               "is the anomaly score.")
    st.info("**Why the bottleneck matters.** Without the squeeze the network could copy its input straight "
            "through and learn nothing. Three numbers force it to keep only what healthy readings have in "
            "common — which is exactly what 'normal' means.")


def render_threshold():
    st.title("⑯ Where to draw the line")
    st.caption("A score is not an alarm. Set the threshold on held-out HEALTHY readings, at the "
               "false-alarm rate the plant will tolerate — then measure what it catches.")
    st.write("")
    d = get_data()
    ae = get_ae()
    err = ae.error(d["X"])

    q = st.slider("Allowed false-alarm rate on healthy readings (%)", 0.2, 10.0, 2.0, 0.2)
    thr = float(np.percentile(err[d["h_va"]], 100 - q))
    flag = err > thr

    fig = go.Figure()
    for f, col in zip(FAULTS, [GREEN, POS, AMBER, RED, TECH]):
        m_ = (d["clean"].state == f).values
        fig.add_trace(go.Box(y=err[m_], name=f, marker_color=col, boxpoints=False))
    fig.add_hline(y=thr, line=dict(color=RED, width=2, dash="dash"),
                  annotation_text=f"alarm above {thr:.3f}")
    fig.update_layout(title="rebuild error by actual state")
    fig.update_yaxes(title="rebuild error", range=[0, float(np.percentile(err, 99.5))])
    st.plotly_chart(style(fig, 400), use_container_width=True)

    te = d["ite"]
    caught = int(np.sum(flag[te] & (d["yte"] == 1)))
    total = int(np.sum(d["yte"] == 1))
    false_a = int(np.sum(flag[te] & (d["yte"] == 0)))
    m = st.columns(3)
    m[0].metric("Faults caught on the sealed set", f"{caught}/{total}",
                f"{caught/max(total,1):.0%} recall")
    m[1].metric("False alarms", false_a, delta_color="inverse")
    m[2].metric("Threshold", f"{thr:.3f}", delta_color="off")
    st.write("")

    st.markdown("##### The two errors, priced")
    a, b = st.columns(2)
    a.markdown(f"<div style='background:{PANEL};border-left:4px solid {AMBER};border-radius:4px;"
               f"padding:14px'><b style='color:{AMBER}'>False alarm</b><br>"
               f"<span style='color:{MUTED}'>A fitter opens a healthy machine. A few hours, and a little "
               f"credibility. Spend that too often and the alarms get muted — which is how monitoring "
               f"projects really die.</span></div>", unsafe_allow_html=True)
    b.markdown(f"<div style='background:{PANEL};border-left:4px solid {RED};border-radius:4px;"
               f"padding:14px'><b style='color:{RED}'>Missed fault</b><br>"
               f"<span style='color:{MUTED}'>The machine runs to failure: the unplanned breakdown, the "
               f"collateral damage and the outage nobody scheduled.</span></div>", unsafe_allow_html=True)
    st.write("")
    st.warning("Drag the slider and watch recall move with it. **Never choose the threshold to maximise "
               "recall** — choose it from what a false alarm costs this plant, then report the recall you "
               "got. Doing it the other way round is how a monitor ends up muted.")


def render_spectrum_ae():
    st.title("⑰ Rebuilding the spectrum")
    st.caption("The same idea, pointed at 512 frequency bins instead of eight named numbers.")
    st.write("")
    d = get_data()
    ae = get_ae()
    sae = get_spectrum_ae()

    fe = ae.error(d["X"])
    se = sae.error(d["Sn"])
    fe_n = fe / np.percentile(fe[d["healthy"]], 99)
    se_n = se / np.percentile(se[d["healthy"]], 99)

    rows = []
    for f in FAULTS:
        m_ = (d["clean"].state == f).values
        rows.append([f, f"{np.median(fe_n[m_]):.2f}", f"{np.median(se_n[m_]):.2f}"])
    st.markdown("##### Score relative to the healthy 99th percentile (1.00 = the alarm line)")
    st.dataframe(pd.DataFrame(rows, columns=[
        "State", "Eight features → autoencoder", "512 spectrum bins → autoencoder"]),
        use_container_width=True, hide_index=True)
    st.write("")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=FAULTS, y=[float(np.median(fe_n[(d["clean"].state == f).values]))
                                      for f in FAULTS],
                         name="eight features", marker_color=AMBER))
    fig.add_trace(go.Bar(x=FAULTS, y=[float(np.median(se_n[(d["clean"].state == f).values]))
                                      for f in FAULTS],
                         name="spectrum", marker_color=POS))
    fig.add_hline(y=1.0, line=dict(color=RED, width=2, dash="dash"), annotation_text="alarm line")
    fig.update_layout(title="which input keeps the evidence?")
    fig.update_yaxes(title="score ÷ healthy 99th percentile")
    st.plotly_chart(style(fig, 400), use_container_width=True)
    st.write("")

    kind = st.selectbox("Look at one state's spectrum", ["healthy", "imbalance", "bearing", "gear"],
                        index=3)
    cand = np.where((d["clean"].state == kind).values)[0]
    i = int(cand[np.argmax(se[cand])])
    rec = sae.rebuild(d["Sn"][i][None, :])[0]
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=story.FREQS, y=d["Sn"][i], mode="lines", name="measured",
                              line=dict(color=POS, width=1.4)))
    fig2.add_trace(go.Scatter(x=story.FREQS, y=rec, mode="lines", name="rebuilt as healthy",
                              line=dict(color=AMBER, width=1.4)))
    fig2.update_layout(title=f"{kind} — measured spectrum vs the network's attempt to rebuild it")
    fig2.update_xaxes(title="frequency (Hz)")
    fig2.update_yaxes(title="standardised magnitude (healthy σ)")
    st.plotly_chart(style(fig2, 380), use_container_width=True)
    st.write("")

    st.success("Neither model was ever shown a gear fault. The difference is not the architecture — it is "
               "**what the input kept**. The mesh tone is a small tonal peak that averages away into "
               "overall RMS, and survives untouched in the spectrum.")
    st.info("Standardising **each bin** against healthy is what makes this work. Without it the naturally "
            "noisy low-frequency bins dominate the rebuild error and drown a new peak in a normally quiet "
            "one — which is precisely the thing being looked for.")


def render_which_frequency():
    st.title("⑱ Reading the error spectrum")
    st.caption("The rebuild error is per bin. The bin that failed names the component.")
    st.write("")
    d = get_data()
    sae = get_spectrum_ae()
    se = sae.error(d["Sn"])

    kind = st.selectbox("Which state?", ["imbalance", "misalignment", "bearing", "gear", "healthy"],
                        index=3)
    cand = np.where((d["clean"].state == kind).values)[0]
    i = int(cand[np.argmax(se[cand])])
    row = d["Sn"][i]
    rec = sae.rebuild(row[None, :])[0]
    err = (row - rec) ** 2

    fig = go.Figure(go.Scatter(x=story.FREQS, y=err, mode="lines", line=dict(color=TECH, width=1.6),
                               fill="tozeroy"))
    for hz, lab, col in [(story.SHAFT_HZ, "1x — imbalance", POS),
                         (2 * story.SHAFT_HZ, "2x — misalignment", AMBER),
                         (story.GEAR_HZ, "mesh — gear", GREEN),
                         (800.0, "housing ring — bearing", RED)]:
        fig.add_vline(x=hz, line=dict(color=col, width=1.5, dash="dot"),
                      annotation_text=lab, annotation_font=dict(size=10, color=col))
    fig.update_layout(title=f"{kind} — rebuild error per frequency bin")
    fig.update_xaxes(title="frequency (Hz)"); fig.update_yaxes(title="squared error")
    st.plotly_chart(style(fig, 420), use_container_width=True)

    peak_hz = float(story.FREQS[int(np.argmax(err))])
    diag = story.diagnose(peak_hz)
    c = st.columns(3)
    c[0].metric("Peak error at", f"{peak_hz:.0f} Hz")
    c[1].metric("Nearest known frequency", diag[1])
    c[2].metric("Therefore", diag[0])
    st.write("")

    st.markdown("##### The frequency map a vibration analyst already uses")
    st.dataframe(pd.DataFrame([
        ["1 × shaft", f"{story.SHAFT_HZ:.0f} Hz", "Imbalance", "Balance the rotor"],
        ["2 × shaft", f"{2*story.SHAFT_HZ:.0f} Hz", "Misalignment", "Re-align the coupling"],
        ["Gear mesh ± 1×", f"{story.GEAR_HZ:.0f} Hz", "Gear tooth defect", "Inspect the gearbox"],
        ["Housing resonance", "≈ 800 Hz", "Bearing spall", "Replace the bearing"],
    ], columns=["Feature", "Frequency", "Diagnosis", "Action"]),
        use_container_width=True, hide_index=True)
    st.write("")
    st.success("Nothing here was labelled. The network learned what healthy spectra look like; the bin "
               "where it failed is the evidence, and the frequency map an analyst already knows turns that "
               "into a component and an action.")


def render_audit():
    st.title("⑲ The monitoring audit")
    st.markdown("#### Every alarm checked, on readings the model has never seen.")
    st.write("")
    d = get_data()
    ae, sae = get_ae(), get_spectrum_ae()
    which = st.radio("Which detector?", ["Feature autoencoder (8 channels)",
                                         "Spectrum autoencoder (512 bins)"], horizontal=True)
    err = ae.error(d["X"]) if which.startswith("Feature") else sae.error(d["Sn"])
    q = st.slider("Allowed false-alarm rate on healthy readings (%)", 0.5, 10.0, 2.0, 0.5)
    thr = float(np.percentile(err[d["h_va"]], 100 - q))

    te = d["ite"]
    pred = (err[te] > thr).astype(int)
    yte = d["yte"]
    tp = int(np.sum((pred == 1) & (yte == 1))); fp = int(np.sum((pred == 1) & (yte == 0)))
    fn = int(np.sum((pred == 0) & (yte == 1))); tn = int(np.sum((pred == 0) & (yte == 0)))
    acc = (tp + tn) / max(1, len(yte)); recall = tp / max(1, tp + fn)

    fig = go.Figure(go.Heatmap(
        z=[[tn, fp], [fn, tp]], x=["called healthy", "called faulty"],
        y=["actually healthy", "actually faulty"],
        colorscale=[[0, "#16202b"], [1, POS]], showscale=False,
        text=[[f"{tn}<br>correct", f"{fp}<br>false alarm"],
              [f"{fn}<br>MISSED FAULT", f"{tp}<br>caught"]],
        texttemplate="%{text}", textfont=dict(size=15)))
    fig.update_layout(title=f"{which} — {len(yte)} sealed readings")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(style(fig, 380), use_container_width=True)

    c = st.columns(4)
    c[0].metric("Accuracy", f"{acc:.1%}")
    c[1].metric("Faults caught", f"{recall:.1%}")
    c[2].metric("False alarms", fp)
    c[3].metric("Missed faults", fn, delta_color="inverse")
    st.write("")

    st.markdown("##### Recall by fault type — the number that actually matters")
    rows = []
    for f in FAULTS[1:]:
        m_ = d["state_te"] == f
        if m_.sum():
            rows.append([f, int(m_.sum()), f"{np.mean(pred[m_])*100:.0f}%",
                         "never trained on" if f == "gear" else "seen before"])
    st.dataframe(pd.DataFrame(rows, columns=["Fault", "Sealed readings", "Caught", "Note"]),
                 use_container_width=True, hide_index=True)
    st.write("")
    st.info("Switch detectors above and watch the gear row. That is the whole argument of this project in "
            "one line of a table: a fault nothing was trained on, caught by the model whose input kept the "
            "evidence.")


def render_proof():
    st.title("⑳ The verdict — every method, measured")
    st.write("")
    d = get_data()
    ae, sae, iso = get_ae(), get_spectrum_ae(), get_iforest()
    clf = get_classifier()

    te = d["ite"]
    yte = d["yte"]
    gear = d["state_te"] == "gear"
    seen = (yte == 1) & ~gear

    def _rates(score):
        thr = float(np.percentile(score[d["h_va"]], 98))
        p = score[te] > thr
        return (float(np.mean(p[seen])), float(np.mean(p[gear])),
                float(np.mean(p[yte == 0])))

    rms = d["clean"]["rms_mm_s"].values
    chart_score = np.abs((rms - rms[d["healthy"]].mean()) / (rms[d["healthy"]].std() + 1e-9))
    methods = [
        ("3σ control chart (RMS)", *_rates(chart_score)),
        ("Isolation forest (8 channels)", *_rates(-iso.score_samples(d["X"]))),
        ("Autoencoder (8 channels)", *_rates(ae.error(d["X"]))),
        ("Autoencoder (512 spectrum bins)", *_rates(sae.error(d["Sn"]))),
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=[m[0] for m in methods], y=[m[1] for m in methods],
                         name="faults it has seen", marker_color=POS))
    fig.add_trace(go.Bar(x=[m[0] for m in methods], y=[m[2] for m in methods],
                         name="the gear fault nothing was trained on", marker_color=RED))
    fig.update_layout(title="recall, at a fixed 2% false-alarm rate on healthy readings")
    fig.update_yaxes(title="share caught", range=[0, 1.1])
    style(fig, 400)
    st.plotly_chart(fig, use_container_width=True)
    st.write("")

    st.table(pd.DataFrame({
        "": ["Faults it has seen", "A fault nobody labelled", "Needs fault examples?",
             "Explains itself?"],
        "3σ chart": ["✅ some", "❌ mostly no", "No", "✅ one number"],
        "Isolation forest": ["✅ good", "⚠️ partly", "No", "⚠️ hard"],
        "Classifier": ["✅ best", "❌ never — no such class", "Yes, many", "✅ a label"],
        "Autoencoder": ["✅ good", "✅ yes", "No", "✅ the error spectrum"],
    }))
    st.success("There is no single winner. On faults the plant has already seen, the control chart is "
               "faster, cheaper and far easier to defend at a reliability review — and most of the time it "
               "is enough. The autoencoder earns its place on exactly one thing: **the fault nobody could "
               "have labelled in advance.**")
    st.info("AI does not out-think the analyst here. It keeps a watch on every machine, every hour, that "
            "no person could keep — and it asks a question a classifier structurally cannot ask.")


def render_drift():
    st.title("㉑ When normal moves")
    st.caption("A rebuilt machine runs differently. New bearings bed in. Seasons change. A monitor "
               "baselined once will slowly fill with false alarms.")
    st.write("")
    rng = np.random.default_rng(11)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    overhaul = st.slider("Month of the overhaul", 1, 10, 6, 1)
    rebase = st.toggle("Rebaseline after the overhaul", value=False)

    base = 1.0 + 0.035 * np.arange(12)                       # slow bedding-in and seasonal drift
    base[overhaul:] += 0.55                                  # the machine genuinely runs differently now
    if rebase:
        base[overhaul:] -= 0.55
    fa = np.clip((base - 1.0) * 9.0 + 2.0, 0, None) + rng.normal(0, 0.4, 12)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=months, y=np.clip(fa, 0, None),
                         marker_color=np.where(np.arange(12) >= overhaul, AMBER, POS),
                         showlegend=False))
    fig.add_hline(y=2.0, line=dict(color=GREEN, width=2, dash="dash"),
                  annotation_text="the false-alarm rate the plant agreed to")
    fig.update_layout(title="false alarms per month" + (" — rebaselined" if rebase else ""))
    fig.update_xaxes(title="month"); fig.update_yaxes(title="false alarms")
    st.plotly_chart(style(fig, 380), use_container_width=True)

    after = float(np.mean(fa[overhaul:]))
    c = st.columns(3)
    c[0].metric("False alarms before the overhaul", f"{np.mean(fa[:overhaul]):.1f} / month")
    c[1].metric("After", f"{after:.1f} / month",
                f"{after - np.mean(fa[:overhaul]):+.1f}", delta_color="inverse")
    c[2].metric("Rebaselined", "yes" if rebase else "no", delta_color="off")
    st.write("")

    if not rebase:
        st.error("The machine is healthy. The model is stale. The usual response is to **raise the "
                 "threshold** — which quietly destroys the sensitivity that justified the project, and "
                 "nobody notices until a real fault is missed.")
    else:
        st.success("Retrained on a fresh window of healthy running after the overhaul, the false-alarm "
                   "rate returns to the agreed level and the sensitivity is intact.")
    st.info("**A rebaseline is a maintenance action with a date and a reason** — logged, like any other. "
            "It is not a slider somebody nudges when the alarms get annoying.")


def render_lead_time():
    st.title("㉒ Days of warning")
    st.caption("Warning is only worth what it buys. Fourteen days lets you order a bearing and schedule "
               "an outage; two days means a rushed repair with whatever is in the store.")
    st.write("")

    rng = np.random.default_rng(5)
    FAILS_ON = 60
    days = np.arange(FAILS_ON + 1)
    sev = np.clip((days - 22) / (FAILS_ON - 22), 0, 1) ** 1.7      # the spall opening up

    q = st.slider("Allowed false-alarm rate (%)", 0.5, 10.0, 2.0, 0.5)
    # each method's score rises differently as the fault develops
    curves = {
        "3σ control chart (RMS)": 1.0 + 5.5 * sev ** 2.6,
        "Isolation forest": 1.0 + 6.5 * sev ** 1.9,
        "Autoencoder (features)": 1.0 + 7.5 * sev ** 1.4,
        "Autoencoder (spectrum)": 1.0 + 8.5 * sev ** 1.0,
    }
    thr = 1.0 + 4.0 * (q / 10.0) ** 0.4 + 1.2

    fig = go.Figure()
    rows = []
    for (name, c), col in zip(curves.items(), [MUTED, AMBER, POS, GREEN]):
        c = c + rng.normal(0, 0.05, len(days))
        fig.add_trace(go.Scatter(x=days, y=c, mode="lines", name=name, line=dict(color=col, width=2.5)))
        over = np.where(c > thr)[0]
        first = int(over[0]) if len(over) else FAILS_ON
        rows.append([name, f"day {first}", f"{FAILS_ON - first} days"])
        if len(over):
            fig.add_trace(go.Scatter(x=[first], y=[c[first]], mode="markers",
                                     marker=dict(size=13, color=col, symbol="star"),
                                     showlegend=False))
    fig.add_hline(y=thr, line=dict(color=RED, width=2, dash="dash"), annotation_text="alarm level")
    fig.add_vline(x=FAILS_ON, line=dict(color=RED, width=2),
                  annotation_text="failure", annotation_position="top left")
    fig.update_layout(title="a bearing spall opening up over 60 days (press Play)")
    fig.update_xaxes(title="day"); fig.update_yaxes(title="score ÷ alarm-free level")
    style(fig, 420)
    animate(fig, S.line_grow(days, list(curves.values())[3], GREEN), ms=45)
    st.plotly_chart(fig, use_container_width=True)
    st.write("")

    st.dataframe(pd.DataFrame(rows, columns=["Method", "First sustained alarm", "Days of warning"]),
                 use_container_width=True, hide_index=True)
    st.write("")
    st.info("Lower the allowed false-alarm rate and every method alarms later. That is the trade, and it "
            "cannot be avoided — only chosen deliberately. **Days of warning, not accuracy, is what the "
            "plant is actually buying.**")
    st.warning("A method that alarms on day 58 is technically correct and commercially worthless: there is "
               "no time to get a part. Report lead time, and the argument about accuracy stops.")


def render_dashboard():
    st.title("㉓ The reliability dashboard")
    st.caption("Everything above becomes three numbers a plant manager can approve: breakdowns avoided, "
               "downtime, and money.")
    st.write("")

    c = st.columns(3)
    machines = c[0].slider("Machines monitored", 5, 200, 60, 5)
    downtime_cost = c[1].slider("Cost of one hour of unplanned downtime", 200, 20000, 4000, 200)
    detected = c[2].slider("Share of failures this system actually catches in time (%)", 10, 90, 55, 5)

    # --- the arithmetic, all of it on the assumptions above ------------------
    FAULTS_PER_MACHINE_YEAR = 0.8
    UNPLANNED_H = 26.0             # hours lost to an unplanned failure
    PLANNED_H = 6.0                # hours lost when the same repair is scheduled
    FALSE_ALARM_H = 3.0            # hours a fitter spends opening a healthy machine
    FALSE_ALARMS_PER_MACHINE_YEAR = 2.0

    failures = machines * FAULTS_PER_MACHINE_YEAR
    caught = failures * detected / 100.0
    hours_before = failures * UNPLANNED_H
    hours_after = (failures - caught) * UNPLANNED_H + caught * PLANNED_H \
        + machines * FALSE_ALARMS_PER_MACHINE_YEAR * FALSE_ALARM_H
    saved_h = hours_before - hours_after
    money = saved_h * downtime_cost
    pct = saved_h / hours_before * 100.0

    k = st.columns(4)
    k[0].metric("Failures caught in time", f"{caught:.0f} / {failures:.0f} per year")
    k[1].metric("Downtime avoided", f"{saved_h:,.0f} hours / year")
    k[2].metric("Value", f"{money:,.0f} / year")
    k[3].metric("Downtime removed", f"{pct:.0f} %")
    st.write("")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Before — monthly route", "After — continuous monitoring"],
                         y=[hours_before, hours_after], marker_color=[RED, GREEN],
                         text=[f"{hours_before:,.0f} h", f"{hours_after:,.0f} h"],
                         textposition="outside"))
    fig.update_layout(title="annual downtime across the fleet, before and after", showlegend=False)
    fig.update_yaxes(title="hours per year")
    style(fig, 380)
    animate(fig, S.bars_grow([dict(x=["Before — monthly route", "After — continuous monitoring"],
                                   y=[hours_before, hours_after], color=GREEN,
                                   text=[f"{hours_before:,.0f} h", f"{hours_after:,.0f} h"])]), ms=90)
    st.plotly_chart(fig, use_container_width=True)
    st.write("")

    st.info(f"With **{machines} machines**, **{detected}%** of failures caught in time and downtime valued "
            f"at **{downtime_cost:,}/hour**, the programme avoids **{saved_h:,.0f} hours** and "
            f"**{money:,.0f}** a year — about **{pct:.0f}%** of unplanned downtime.")
    st.warning("**Read the assumptions, not just the total.** The 'after' bar includes the cost of the "
               "false alarms — a fitter opening healthy machines — because leaving that out is the single "
               "most common way these business cases get overstated. It never reaches zero: some failure "
               "modes give no warning at all, and a warning nobody acts on saves nothing.")


# ============================================================================
# THE COURSE, AS ONE MONITORING PROGRAMME
# ============================================================================
STAGES = {
    "start":            ("⓪ The project — read this first", bridge.render_start),
    "breakdown":        ("① A machine that stops without warning", story.render_breakdown),
    "sensors":          ("② Where the sensors sit", lambda: story.render_sensors(get_data)),
    "load":             ("③ The monitoring log arrives", lambda: common.render_load(CFG)),
    "inspect":          ("④ Sensor health check", lambda: common.render_inspect(CFG)),
    "clean":            ("⑤ Dead channels & dropouts", lambda: common.render_clean(CFG)),
    "normalize":        ("⑥ One common scale", lambda: common.render_normalize(CFG)),
    "split":            ("⑦ Train on normal only", render_split),
    "control-chart":    ("⑧ The 3σ limit", render_control_chart),
    "isolation-forest": ("⑨ Isolating the odd one out", render_isolation_forest),
    "classifier-wall":  ("⑩ The fault it was never taught", render_classifier_wall),
    "analyst-brain":    ("⑪ The analyst's judgement", story.render_analyst_brain),
    "neuron":           ("⑫ The neuron", lambda: common.render_neuron(CFG)),
    "activation":       ("⑬ Activation", lambda: common.render_activation(CFG)),
    "gradient-descent": ("⑭ Loss & gradient descent", lambda: common.render_gradient_descent(CFG)),
    "autoencoder":      ("⑮ The hourglass", render_autoencoder),
    "threshold":        ("⑯ Where to draw the line", render_threshold),
    "spectrum-ae":      ("⑰ Rebuilding the spectrum", render_spectrum_ae),
    "which-frequency":  ("⑱ Reading the error spectrum", render_which_frequency),
    "audit":            ("⑲ The monitoring audit", render_audit),
    "proof":            ("⑳ The verdict", render_proof),
    "drift":            ("㉑ When normal moves", render_drift),
    "lead-time":        ("㉒ Days of warning", render_lead_time),
    "fusion-engine":    ("㉓ The work order", story.render_fusion_engine),
    "pipeline":         ("㉔ The whole system", story.render_pipeline),
    "dashboard":        ("㉕ The reliability dashboard", render_dashboard),
}

ALIASES = {"overview": "breakdown", "anomaly": "autoencoder", "fusion": "fusion-engine",
           "spectrum": "spectrum-ae", "engineer-brain": "analyst-brain",
           "enter-ai": "sensors", "ml-baseline": "control-chart"}

stage = bridge.route(STAGES, ALIASES)

if stage != "start":
    bridge.open_page(stage)

STAGES[stage][1]()

if stage != "start":
    bridge.close_page(stage)

S.footer_nav(STAGES, stage)
