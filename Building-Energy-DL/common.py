"""
common.py — the data-preparation and how-a-machine-learns pages.
================================================================
IDENTICAL COPY IN EVERY TEACHING APP FOLDER. These ten stages are the same
lesson in every project — only the words, the channel names and the class
labels change — so they live here and are configured by a `CFG` dict the app
passes in, instead of being written out nine times.

CFG keys
    data()          -> the cached dataset dict (dirty / clean / norm / scaler /
                       Xtr,Xval,Xte / ytr,yval,yte)
    models()        -> (classifier, mlp)
    FEATURES, NICE  -> column ids and their display names
    unit            -> what one row is: "cycle", "hour", "record", "segment"
    unit_plural     -> "cycles", "hours", ...
    pos, neg        -> the two class names, e.g. ("congested", "coping")
    export_name     -> "controller export", "BMS export", ...
    faults          -> one sentence naming the planted sensor faults
    fault_example   -> the value the median argument uses, e.g. "9,999-vehicle rollover"
    scale_examples  -> [(label, "87 s"), ...] three readings in different units
    scale_note      -> the sentence explaining which one wins unfairly
    neuron_w        -> default weight per feature (same length as FEATURES)
    net_pair        -> (feature_id_x, feature_id_y) for the decision surface
    net_note        -> what the corner of that surface means
    titles          -> {stage_id: "① Page title"}
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from sklearn.neural_network import MLPClassifier

import scaffold as S

POS, NEG = S.POS, S.NEG
GREEN, AMBER, RED = S.GREEN, S.AMBER, S.RED
TECH, MUTED, TEXT = S.TECH, S.MUTED, S.TEXT


def _t(C, key, fallback):
    return C.get("titles", {}).get(key, fallback)


# ---------------------------------------------------------------- ③ load
def render_load(C):
    st.title(_t(C, "load", "The log arrives"))
    raw = C["data"]()["dirty"]
    c1, c2, c3 = st.columns(3)
    c1.metric(f"{C['unit_plural'].capitalize()} logged", f"{len(raw):,}")
    c2.metric("Columns", raw.shape[1])
    c3.metric("Sensor channels", len(C["FEATURES"]))
    st.caption(f"The first thing you do with any {C['export_name']}: check what actually arrived.")
    st.write("")
    st.dataframe(raw.head(8), use_container_width=True, hide_index=True)
    st.info("Types and counts look plausible — but plausible is not verified. The next step inspects the "
            "channels for dropouts and stuck sensors before anything is built on them.")


# ---------------------------------------------------------------- ④ inspect
def render_inspect(C):
    st.title(_t(C, "inspect", "Sensor health check"))
    raw = C["data"]()["dirty"]
    F, N = C["FEATURES"], C["NICE"]
    miss = raw[F].isna().sum()
    fig = go.Figure(go.Bar(x=N, y=miss.values, marker_color=AMBER,
                           text=miss.values, textposition="outside"))
    fig.update_layout(title="missing readings per channel")
    S.style(fig, 360)
    S.animate(fig, S.bars_grow([dict(x=N, y=list(miss.values), color=AMBER,
                                     text=list(miss.values))]), ms=80)
    st.plotly_chart(fig, use_container_width=True)
    st.write("")

    col = st.selectbox("Inspect one channel's distribution", F,
                       format_func=lambda c: N[F.index(c)])
    vals = raw[col].dropna()
    fig2 = go.Figure(go.Histogram(x=vals, nbinsx=50, marker_color=POS))
    fig2.update_layout(title=f"{N[F.index(col)]} — a spike far from the pack is a sensor fault")
    st.plotly_chart(S.style(fig2, 340), use_container_width=True)
    st.info(C["faults"] + " Diagnosis only — nothing is repaired yet.")


# ---------------------------------------------------------------- ⑤ clean
def render_clean(C):
    st.title(_t(C, "clean", "Bad readings out"))
    d = C["data"]()
    F, N = C["FEATURES"], C["NICE"]
    before, after = len(d["dirty"]), len(d["clean"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows before", f"{before:,}")
    c2.metric("Rows after", f"{after:,}", f"-{before-after} duplicates")
    c3.metric("Missing after", int(d["clean"][F].isna().sum().sum()))
    st.caption("Impossible readings → removed, then gaps filled with the channel's median.")
    st.write("")
    col = st.selectbox("See a channel before vs after", F, format_func=lambda c: N[F.index(c)])
    fig = go.Figure()
    fig.add_trace(go.Box(y=d["dirty"][col], name="dirty", marker_color=NEG))
    fig.add_trace(go.Box(y=d["clean"][col], name="clean", marker_color=GREEN))
    fig.update_layout(title=f"{N[F.index(col)]}: the impossible tails are gone")
    st.plotly_chart(S.style(fig, 380), use_container_width=True)
    st.info(f"**Why the median, not the mean?** The mean is dragged badly by a single "
            f"{C['fault_example']}. The median — the middle value — barely notices it, so the filled-in "
            f"reading stays physically realistic.")


# ---------------------------------------------------------------- ⑥ normalize
def render_normalize(C):
    st.title(_t(C, "normalize", "Put every channel on one scale"))
    st.info("📐 **Every channel reports in its own unit.** Put them all on one common 0–1 scale first, so "
            "the model compares them fairly instead of trusting whichever reading happens to have the "
            "biggest *number*.")
    st.write("")
    cols = st.columns(len(C["scale_examples"]))
    for col, (lab, val) in zip(cols, C["scale_examples"]):
        col.metric(lab, val)
    st.caption(C["scale_note"] + " Press Play to collapse a channel onto 0–1:")
    st.write("")
    d = C["data"]()
    F, N = C["FEATURES"], C["NICE"]
    col = st.selectbox("Channel", F, index=0, format_func=lambda c: N[F.index(c)])
    rawv = d["clean"][col].values
    nrm = d["norm"][col].values
    fig = go.Figure(go.Histogram(x=rawv, marker_color=MUTED, nbinsx=50))
    frames = []
    for k in range(13):
        t = k / 12
        x = (1 - t) * rawv + t * nrm
        frames.append(go.Frame(data=[go.Histogram(x=x, marker_color=POS if t > 0.5 else MUTED,
                                                  nbinsx=50)], name=str(k)))
    fig.update_layout(title=f"{N[F.index(col)]}: raw range collapsing into 0–1")
    S.style(fig, 400); S.animate(fig, frames, ms=140)
    st.plotly_chart(fig, use_container_width=True)

    lo, hi = float(d["clean"][col].min()), float(d["clean"][col].max())
    v = st.slider("Try a raw reading", lo, hi, float(d["clean"][col].median()))
    c1, c2 = st.columns(2)
    c1.metric("Raw value", f"{v:.2f}")
    c2.metric("Scaled (0–1)", f"{(v - lo) / (hi - lo + 1e-9):.3f}")


# ---------------------------------------------------------------- ⑦ split
def render_split(C):
    st.title(_t(C, "split", "Known records vs a sealed set"))
    st.info(f"🧪 **Never test a model on the very {C['unit_plural']} it was tuned on.** It would just "
            f"repeat what it memorised, and you would learn nothing about the next ones.")
    st.caption(f"Press Play: the {C['unit_plural']} divide into train / validation / test.")
    st.write("")
    d = C["data"]()
    parts = [("Train", d["ytr"], POS), ("Validation", d["yval"], AMBER), ("Test", d["yte"], GREEN)]
    ok = [int((a == 0).sum()) for _, a, _ in parts]
    bad = [int((a == 1).sum()) for _, a, _ in parts]
    names = [n for n, _, _ in parts]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=ok, name=C["neg"], marker_color=GREEN))
    fig.add_trace(go.Bar(x=names, y=bad, name=C["pos"], marker_color=RED))
    fig.update_layout(barmode="stack",
                      title=f"{C['unit_plural']} per split (the rate is kept balanced across all three)")
    S.style(fig, 380)
    S.animate(fig, S.bars_grow([dict(x=names, y=ok, color=GREEN, name=C["neg"]),
                                dict(x=names, y=bad, color=RED, name=C["pos"])]), ms=90)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Train", f"{len(d['ytr'])}")
    c2.metric("Validation", f"{len(d['yval'])}")
    c3.metric("Test (sealed)", f"{len(d['yte'])}")
    st.info("The test rows are locked away now and only opened at the audit. That is the one fair score of "
            "what the model will do on new data.")


# ---------------------------------------------------------------- ⑬ neuron
def render_neuron(C):
    st.title(_t(C, "neuron", "The neuron — z = w·x + b"))
    st.caption(f"Set a weight for each channel. The neuron multiplies, sums, adds a bias, and squashes "
               f"the result to a probability that the {C['unit']} was {C['pos']}.")
    st.write("")
    d = C["data"]()
    F, N = C["FEATURES"], C["NICE"]
    row = d["norm"].iloc[7]
    x = row[F].values.astype(float)
    cols = st.columns(len(F))
    w = []
    for i, c in enumerate(cols):
        with c:
            st.caption(N[i])
            w.append(st.slider(N[i], -1.5, 1.5, float(C["neuron_w"][i]), 0.1,
                               key=f"w{i}", label_visibility="collapsed"))
    b = st.slider("Bias b — the baseline before any reading is seen", -2.0, 2.0, -0.3, 0.1)
    w = np.array(w)
    z = float(np.dot(w, x) + b)
    p = float(S.sigmoid(z))
    st.write("")

    fig = go.Figure(go.Bar(x=N, y=w * x, marker_color=[POS if v >= 0 else NEG for v in w * x],
                           text=[f"{v:+.2f}" for v in w * x], textposition="outside"))
    fig.update_layout(title=f"each channel's contribution · z = {z:+.2f} → p({C['pos']}) = {p:.2f}")
    fig.update_yaxes(title="w × x")
    st.plotly_chart(S.style(fig, 380), use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Weighted sum z", f"{z:+.2f}")
    c2.metric("After sigmoid", f"{p:.2f}")
    c3.metric("Call", C["pos"] if p > 0.5 else C["neg"])
    st.info(f"Nothing here is mysterious: {len(F)} multiplications, a sum, a bias, and a squash. A real "
            f"network does not let you set these weights — it learns them from the log, which is the whole "
            f"point.")


# ---------------------------------------------------------------- ⑭ activation
def render_activation(C):
    st.title(_t(C, "activation", "Activation — turning a sum into a decision"))
    st.caption("The weighted sum can be any number. An activation function turns it into something an "
               "engineer can act on.")
    st.write("")
    z = st.slider("Weighted sum z coming out of the neuron", -6.0, 6.0, 1.2, 0.1)
    xs = np.linspace(-6, 6, 300)

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Scatter(x=xs, y=S.sigmoid(xs), mode="lines", line=dict(color=POS, width=3)))
        fig.add_trace(go.Scatter(x=[z], y=[S.sigmoid(z)], mode="markers",
                                 marker=dict(size=14, color=AMBER), showlegend=False))
        fig.add_hline(y=0.5, line=dict(color=MUTED, dash="dot"))
        fig.update_layout(title=f"sigmoid — probability · σ({z:.1f}) = {S.sigmoid(z):.3f}")
        st.plotly_chart(S.style(fig, 340), use_container_width=True)
    with c2:
        fig2 = go.Figure(go.Scatter(x=xs, y=np.maximum(0, xs), mode="lines",
                                    line=dict(color=TECH, width=3)))
        fig2.add_trace(go.Scatter(x=[z], y=[max(0, z)], mode="markers",
                                  marker=dict(size=14, color=AMBER), showlegend=False))
        fig2.update_layout(title=f"ReLU — passes positive evidence · ReLU({z:.1f}) = {max(0, z):.2f}")
        st.plotly_chart(S.style(fig2, 340), use_container_width=True)
    st.write("")

    st.markdown("##### Why not a hard threshold?")
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=xs, y=(xs > 0).astype(float), mode="lines",
                              line=dict(color=RED, width=3, shape="hv"), name="hard limit"))
    fig3.add_trace(go.Scatter(x=xs, y=S.sigmoid(xs), mode="lines",
                              line=dict(color=POS, width=3), name="sigmoid"))
    fig3.update_layout(title="a hard limit has no slope — training has nothing to follow")
    st.plotly_chart(S.style(fig3, 320), use_container_width=True)
    st.info("Two reasons for the smooth curve. It reports **how confident** the call is, so a borderline "
            "case is not treated as a certainty. And it has a **gradient everywhere**, which is what lets "
            "gradient descent work at all.")


# ---------------------------------------------------------------- ⑯ gradient descent
def render_gradient_descent(C):
    st.title(_t(C, "gradient-descent", "Loss and gradient descent"))
    st.caption("Loss = how wrong. Gradient = which way is better. Learning rate = how big a step.")
    st.write("")
    lr = st.slider("Learning rate (step size)", 0.02, 1.05, 0.25, 0.01)
    xs = np.linspace(-4, 4, 200)
    loss = xs ** 2
    path = [3.6]
    for _ in range(18):
        path.append(path[-1] - lr * 2 * path[-1])
    path = np.array(path)
    fig = go.Figure(go.Scatter(x=xs, y=loss, mode="lines", line=dict(color=MUTED, width=2), name="loss"))
    fig.add_trace(go.Scatter(x=[path[0]], y=[path[0] ** 2], mode="markers",
                             marker=dict(size=14, color=POS)))
    frames = [go.Frame(data=[go.Scatter(x=xs, y=loss, mode="lines", line=dict(color=MUTED, width=2)),
                             go.Scatter(x=[path[k]], y=[path[k] ** 2], mode="markers+lines",
                                        marker=dict(size=14, color=POS),
                                        line=dict(color=POS, width=1))],
                       name=str(k)) for k in range(len(path))]
    settled = abs(path[-1]) < 0.1
    fig.update_layout(title=("converges to the minimum" if settled else
                             "overshoots — the step is too big"))
    fig.update_xaxes(title="weight"); fig.update_yaxes(title="loss")
    S.style(fig, 380); S.animate(fig, frames, ms=180)
    st.plotly_chart(fig, use_container_width=True)
    st.info("Too small a step and it crawls; too big and it bounces past the minimum. The gradient always "
            "points downhill — the art is the step size.")


# ---------------------------------------------------------------- ⑰ network
def render_network(C):
    st.title(_t(C, "network", "The network — layered neurons"))
    F, N = C["FEATURES"], C["NICE"]
    fa, fb = C["net_pair"]
    st.caption(f"One neuron draws one straight line. Layers bend the boundary around real patterns. "
               f"Here: {N[F.index(fa)]} vs {N[F.index(fb)]}, with the decision surface behind the data.")
    st.write("")
    d = C["data"]()
    depth_opts = {"2 (one tiny layer)": (2,), "6": (6,), "12 → 6": (12, 6), "16 → 8": (16, 8)}
    depth_label = st.select_slider("Hidden layer size", options=list(depth_opts), value="12 → 6")
    idx = [F.index(fa), F.index(fb)]
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = MLPClassifier(hidden_layer_sizes=depth_opts[depth_label], max_iter=600,
                          random_state=0).fit(d["Xtr"][:, idx], d["ytr"])
    gx, gy = np.meshgrid(np.linspace(0, 1, 80), np.linspace(0, 1, 80))
    zz = m.predict_proba(np.c_[gx.ravel(), gy.ravel()])[:, 1].reshape(gx.shape)
    fig = go.Figure()
    fig.add_trace(go.Heatmap(x=np.linspace(0, 1, 80), y=np.linspace(0, 1, 80), z=zz,
                             colorscale="RdBu_r", showscale=False, opacity=0.55))
    te = d["Xte"][:, idx]
    fig.add_trace(go.Scatter(x=te[:, 0], y=te[:, 1], mode="markers",
                             marker=dict(size=6, color=d["yte"], colorscale=[[0, GREEN], [1, RED]],
                                         line=dict(width=0.5, color="#0e1117")), showlegend=False))
    fig.update_layout(title=f"decision surface — red = predicted {C['pos']}")
    fig.update_xaxes(title=f"{N[F.index(fa)]} (scaled)")
    fig.update_yaxes(title=f"{N[F.index(fb)]} (scaled)")
    st.plotly_chart(S.style(fig, 420), use_container_width=True)
    st.info(f"With one tiny layer the boundary is nearly straight. Add width and depth and it wraps around "
            f"{C['net_note']} — the pattern a single weighted sum cannot hold.")


# ---------------------------------------------------------------- ⑱ training
def render_training(C):
    st.title(_t(C, "training", "Training — the loss falls, then flattens"))
    st.write("")
    d = C["data"]()
    lr = st.select_slider("Learning rate", options=[0.0005, 0.001, 0.005, 0.02], value=0.001)
    m = MLPClassifier(hidden_layer_sizes=(12, 6), learning_rate_init=lr,
                      max_iter=1, warm_start=True, random_state=0)
    losses, val = [], []
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for _ in range(120):
            m.fit(d["Xtr"], d["ytr"])
            losses.append(m.loss_)
            val.append(1.0 - m.score(d["Xval"], d["yval"]))
    losses = np.array(losses); val = np.array(val)
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=losses, mode="lines", line=dict(color=POS, width=2), name="training loss"))
    fig.add_trace(go.Scatter(y=val, mode="lines", line=dict(color=AMBER, width=2),
                             name="validation error"))
    frames = [go.Frame(data=[go.Scatter(y=losses[:k + 1], mode="lines", line=dict(color=POS, width=2)),
                             go.Scatter(y=val[:k + 1], mode="lines", line=dict(color=AMBER, width=2))],
                       name=str(k)) for k in range(0, len(losses), 3)]
    fig.update_layout(title="training loss and held-out error over epochs")
    fig.update_xaxes(title="epoch"); fig.update_yaxes(title="loss / error rate")
    S.style(fig, 400); S.animate(fig, frames, ms=60)
    st.plotly_chart(fig, use_container_width=True)
    best = int(np.argmin(val))
    c1, c2, c3 = st.columns(3)
    c1.metric("Final training loss", f"{losses[-1]:.3f}")
    c2.metric("Best epoch on validation", best)
    c3.metric("Test accuracy", f"{m.score(d['Xte'], d['yte'])*100:.1f}%")
    st.info(f"The training loss keeps falling. The validation error stops improving around epoch {best} — "
            f"past that point the network is memorising these {C['unit_plural']} rather than learning the "
            f"pattern. That turn is where you stop.")


# ---------------------------------------------------------------- audit
def render_audit(C):
    st.title(_t(C, "audit", "The audit — checking every claim"))
    st.markdown(f"#### Predicted against measured, on {C['unit_plural']} the model has never seen.")
    st.write("")
    d = C["data"]()
    rf, mlp = C["models"]()
    Xte, yte = d["Xte"], d["yte"]

    which = st.radio("Which model is being audited?", ["Random Forest", "Neural network (MLP)"],
                     horizontal=True)
    pred = (rf if which == "Random Forest" else mlp).predict(Xte)
    tp = int(np.sum((pred == 1) & (yte == 1)))
    fp = int(np.sum((pred == 1) & (yte == 0)))
    fn = int(np.sum((pred == 0) & (yte == 1)))
    tn = int(np.sum((pred == 0) & (yte == 0)))
    acc = (tp + tn) / max(1, len(yte))
    recall = tp / max(1, tp + fn)

    fig = go.Figure(go.Heatmap(
        z=[[tn, fp], [fn, tp]],
        x=[f"called {C['neg']}", f"called {C['pos']}"],
        y=[f"actually {C['neg']}", f"actually {C['pos']}"],
        colorscale=[[0, "#16202b"], [1, POS]], showscale=False,
        text=[[f"{tn}<br>correct", f"{fp}<br>false alarm"],
              [f"{fn}<br>MISSED", f"{tp}<br>caught"]],
        texttemplate="%{text}", textfont=dict(size=15)))
    fig.update_layout(title=f"{which} — {len(yte)} sealed {C['unit_plural']}")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(S.style(fig, 380), use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Accuracy", f"{acc:.1%}")
    c2.metric(f"{C['pos'].capitalize()} caught", f"{recall:.1%}")
    c3.metric("False alarms", fp)
    c4.metric("Missed", fn, delta_color="inverse")
    st.write("")

    st.markdown("### The two errors do not cost the same")
    a, b = st.columns(2)
    a.markdown(f"<div style='background:{S.PANEL};border-left:4px solid {AMBER};border-radius:4px;"
               f"padding:14px'><b style='color:{AMBER}'>False alarm ({fp})</b><br>"
               f"<span style='color:{MUTED}'>{C['fp_cost']}</span></div>", unsafe_allow_html=True)
    b.markdown(f"<div style='background:{S.PANEL};border-left:4px solid {RED};border-radius:4px;"
               f"padding:14px'><b style='color:{RED}'>Missed ({fn})</b><br>"
               f"<span style='color:{MUTED}'>{C['fn_cost']}</span></div>", unsafe_allow_html=True)
    st.write("")
    st.info(f"This is why accuracy alone is never reported. A model that calls every {C['unit']} "
            f"'{C['neg']}' scores well on a system that is mostly fine — and finds nothing. **Recall on "
            f"the {C['pos']} {C['unit_plural']} is the number the project is judged on.**")
