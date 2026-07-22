"""
AI-Based CNC Machining Optimization - Deep Learning illustration app
====================================================================
One project, 28 stage pages, taught as one machining-optimization project.
Each notebook step links here with ?stage=<id>.

Dark canvas, animated Plotly (press Play) + interactive sliders/toggles.
Every page: machining activity -> engineering challenge -> AI concept ->
technical illustration -> notebook connection.

The problem: choose cutting speed, feed rate and depth of cut to cut fastest
without wrecking the finish or the tool.
  Sensors : force, vibration, temperature, spindle current, + a camera.
  ML      : predict surface roughness, predict tool life, recommend the setting.
  DL      : grade the machined surface, detect a chipped tool edge.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neural_network import MLPClassifier

import story
import bridge

# ----------------------------------------------------------------------------
# THEME / PALETTE
# ----------------------------------------------------------------------------
BG, PANEL = "#0e1117", "#161b22"
POS, NEG = "#4fc3f7", "#ff8a65"
GREEN, AMBER, RED = "#66bb6a", "#ffb74d", "#ef5350"
TECH = "#ba68c8"
MUTED, TEXT = "#8b949e", "#e6edf3"

FEATURES = ["cutting_speed", "feed_rate", "depth_of_cut", "force_n",
            "vibration_mm_s", "temperature_c", "current_a"]
NICE = ["Speed (m/min)", "Feed (mm/rev)", "Depth (mm)", "Force (N)",
        "Vibration (mm/s)", "Temp (°C)", "Current (A)"]

RA_LIMIT = 3.5          # µm  - surface-roughness tolerance (scrap above this)
TL_LIMIT = 7.0          # min - minimum acceptable tool life
NOSE_R = 0.8            # mm  - tool nose radius (fixed)

st.set_page_config(page_title="CNC Machining Optimization - DL", page_icon="🛠️", layout="wide")
bridge.inject_css()   # CNC's distinct industrial-DRO display language


def style(fig, h=440):
    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG, font_color=TEXT,
        margin=dict(l=30, r=30, t=60, b=30), height=h,
        template="plotly_dark", legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="#222933", zerolinecolor="#333")
    fig.update_yaxes(gridcolor="#222933", zerolinecolor="#333")
    return fig


def animate(fig, frames, ms=350):
    fig.frames = frames
    fig.update_layout(updatemenus=[dict(
        type="buttons", direction="left", showactive=False,
        x=1.0, y=1.16, xanchor="right", yanchor="top",
        bgcolor=PANEL, bordercolor=MUTED, font=dict(color=TEXT, size=13),
        buttons=[
            dict(label="▶  Play", method="animate",
                 args=[None, dict(frame=dict(duration=ms, redraw=True),
                                  fromcurrent=True, transition=dict(duration=120))]),
            dict(label="⏸  Pause", method="animate",
                 args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")]),
        ])])
    return fig


def narrate(stage):
    """No audio assets in this build; every page carries its own text narration."""
    return


def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -50, 50)))


# ----------------------------------------------------------------------------
# THE MACHINING PHYSICS  (approximate, monotone, teaching-grade)
# The sensors are consequences of the settings and the tool-wear state; the
# targets (roughness, tool life) follow textbook forms. Same functions drive
# the synthetic dataset AND the optimizer's grid search, so they stay consistent.
# ----------------------------------------------------------------------------
def _force(Vc, f, ap, wear):
    return 1500.0 * ap * (f ** 0.75) * (1 + 0.35 * wear)


def _temp(Vc, f, ap, wear):
    return 90.0 + 0.85 * Vc + 260.0 * f + 22.0 * wear * (Vc / 150.0)


def _vib(Vc, f, ap, wear):
    return 0.6 + 1.5 * ap + 0.008 * Vc + 2.2 * wear


def _current(force, Vc):
    return 4.0 + 0.006 * force + 0.02 * Vc


def _roughness(f, wear, vib):
    # classic Ra ~ f^2 / (32 * r_nose), worsened by wear and vibration
    return (f ** 2) / (32.0 * NOSE_R) * 1000.0 * (1 + 0.5 * wear) + 0.12 * vib


def _tool_life(Vc, f, ap):
    # Taylor-style: life collapses with speed, and falls with feed and depth
    return 22.0 * (180.0 / Vc) ** 2.2 * (0.25 / f) ** 0.55 * (2.0 / ap) ** 0.35


def _features_for(Vc, f, ap, wear=0.0):
    """Build the 7-feature row(s) the models expect, from settings (noise-free).
    Works on scalars or numpy arrays."""
    force = _force(Vc, f, ap, wear)
    vib = _vib(Vc, f, ap, wear)
    temp = _temp(Vc, f, ap, wear)
    cur = _current(force, Vc)
    return np.stack([Vc, f, ap, force, vib, temp, cur], axis=-1)


# ----------------------------------------------------------------------------
# DATA  (synthetic machining log, generated + cached)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_data():
    rng = np.random.default_rng(42)
    N = 1400
    Vc = rng.uniform(60, 280, N)
    f = rng.uniform(0.05, 0.45, N)
    ap = rng.uniform(0.3, 3.0, N)
    wear = rng.uniform(0, 1, N)

    force = _force(Vc, f, ap, wear) + rng.normal(0, 80, N)
    vib = np.abs(_vib(Vc, f, ap, wear) + rng.normal(0, 0.3, N))
    temp = _temp(Vc, f, ap, wear) + rng.normal(0, 8, N)
    cur = _current(force, Vc) + rng.normal(0, 0.8, N)

    Ra = np.clip(_roughness(f, wear, vib) + rng.normal(0, 0.15, N), 0.2, None)
    life = np.clip(_tool_life(Vc, f, ap) + rng.normal(0, 2, N), 3, 120)
    scrap = ((Ra > RA_LIMIT) | (life < TL_LIMIT)).astype(int)

    df = pd.DataFrame({
        "pass_id": np.arange(1, N + 1),
        "cutting_speed": Vc.round(0), "feed_rate": f.round(3),
        "depth_of_cut": ap.round(2), "force_n": force.round(0),
        "vibration_mm_s": vib.round(2), "temperature_c": temp.round(0),
        "current_a": cur.round(1),
        "roughness_um": Ra.round(2), "tool_life_min": life.round(0), "scrap": scrap,
    })

    # a realistically messy export: dropouts, stuck/impossible values, duplicates
    dirty = df.copy()
    for col in ["force_n", "vibration_mm_s", "temperature_c", "current_a", "feed_rate"]:
        dirty.loc[rng.choice(N, int(0.06 * N), replace=False), col] = np.nan
    dirty.loc[rng.choice(N, 14, replace=False), "force_n"] = 9999      # saturated dynamometer
    dirty.loc[rng.choice(N, 10, replace=False), "temperature_c"] = 999  # thermocouple fault
    dirty.loc[rng.choice(N, 12, replace=False), "vibration_mm_s"] = 0.0  # dead probe
    dirty = pd.concat([dirty, dirty.sample(20, random_state=4)], ignore_index=True)

    clean = dirty.drop_duplicates().copy()
    clean.loc[clean.force_n > 8000, "force_n"] = np.nan
    clean.loc[clean.temperature_c > 700, "temperature_c"] = np.nan
    clean.loc[clean.vibration_mm_s <= 0, "vibration_mm_s"] = np.nan
    for col in ["force_n", "vibration_mm_s", "temperature_c", "current_a", "feed_rate"]:
        clean[col] = clean[col].fillna(clean[col].median())

    scaler = MinMaxScaler()
    norm = clean.copy()
    norm[FEATURES] = scaler.fit_transform(clean[FEATURES])

    X = norm[FEATURES].values
    yscrap = norm["scrap"].values
    yRa = norm["roughness_um"].values
    yTL = norm["tool_life_min"].values

    idx = np.arange(len(X))
    itr, itmp = train_test_split(idx, test_size=0.30, random_state=42, stratify=yscrap)
    ival, ite = train_test_split(itmp, test_size=0.50, random_state=42, stratify=yscrap[itmp])

    return dict(truth=df, dirty=dirty, clean=clean, norm=norm, scaler=scaler,
                Xtr=X[itr], Xval=X[ival], Xte=X[ite],
                ytr=yscrap[itr], yval=yscrap[ival], yte=yscrap[ite],
                RaTr=yRa[itr], RaTe=yRa[ite], TLtr=yTL[itr], TLte=yTL[ite])


@st.cache_resource(show_spinner=False)
def get_models():
    d = get_data()
    rf = RandomForestClassifier(n_estimators=200, random_state=42).fit(d["Xtr"], d["ytr"])
    mlp = MLPClassifier(hidden_layer_sizes=(10, 6), max_iter=800, random_state=42).fit(d["Xtr"], d["ytr"])
    return rf, mlp


@st.cache_resource(show_spinner=False)
def get_regressors():
    d = get_data()
    ra = RandomForestRegressor(n_estimators=200, random_state=42).fit(d["Xtr"], d["RaTr"])
    tl = RandomForestRegressor(n_estimators=200, random_state=42).fit(d["Xtr"], d["TLtr"])
    return ra, tl


# ============================================================================
# TECHNICAL RENDERERS  (Part 4 of each page)
# ============================================================================
def render_load():
    st.title("⑤ The machining log arrives")
    d = get_data()
    raw = d["dirty"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Passes logged", f"{len(raw):,}")
    c2.metric("Columns", raw.shape[1])
    c3.metric("Sensors + settings", len(FEATURES))
    st.caption("The first thing you do with any export: check what actually arrived.")
    st.dataframe(raw.head(8), use_container_width=True, hide_index=True)
    st.info("Types and counts look plausible — but plausible is not verified. The next step inspects the "
            "readings for dropouts and stuck channels before anything is built on them.")


def render_inspect():
    st.title("⑥ Sensor health check")
    d = get_data()
    raw = d["dirty"]
    miss = raw[FEATURES].isna().sum()
    fig = go.Figure(go.Bar(x=NICE, y=miss.values, marker_color=AMBER,
                           text=miss.values, textposition="outside"))
    fig.update_layout(title="missing readings per channel")
    st.plotly_chart(style(fig, 360), use_container_width=True)

    col = st.selectbox("Inspect one channel's distribution", FEATURES,
                       format_func=lambda c: NICE[FEATURES.index(c)])
    vals = raw[col].dropna()
    fig2 = go.Figure(go.Histogram(x=vals, nbinsx=50, marker_color=POS))
    fig2.update_layout(title=f"{NICE[FEATURES.index(col)]} — the spike far from the pack is a sensor fault")
    st.plotly_chart(style(fig2, 340), use_container_width=True)
    st.info("A saturated dynamometer (9,999 N), a faulted thermocouple (999 °C) and a dead vibration "
            "probe (0 mm/s) all announce themselves here. Diagnosis only — nothing is repaired yet.")


def render_clean():
    st.title("⑦ Dropouts and spikes out")
    d = get_data()
    before, after = len(d["dirty"]), len(d["clean"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows before", f"{before:,}")
    c2.metric("Rows after", f"{after:,}", f"-{before-after} duplicates")
    c3.metric("Missing after", int(d["clean"][FEATURES].isna().sum().sum()))
    st.caption("Impossible values → removed, then gaps filled with the channel's median.")
    col = st.selectbox("See a channel before vs after", FEATURES,
                       format_func=lambda c: NICE[FEATURES.index(c)])
    fig = go.Figure()
    fig.add_trace(go.Box(y=d["dirty"][col], name="dirty", marker_color=NEG))
    fig.add_trace(go.Box(y=d["clean"][col], name="clean", marker_color=GREEN))
    fig.update_layout(title=f"{NICE[FEATURES.index(col)]}: the impossible tails are gone")
    st.plotly_chart(style(fig, 380), use_container_width=True)
    st.info("**Why the median, not the mean?** The mean is dragged by a 9,999 N saturation spike. The "
            "median — the middle value — barely notices it.")


def render_normalize():
    st.title("⑧ Standardize the channels")
    st.info("🛠️ **Every channel uses a different unit — m/min, mm/rev, mm, newtons, °C, amps.** Put them "
            "all on one common 0–1 scale first, so the model compares them fairly instead of trusting "
            "whichever reading happens to have the biggest *number*.")
    n1, n2, n3 = st.columns(3)
    n1.metric("Force reads", "680 N")
    n2.metric("Feed reads", "0.20 mm/rev")
    n3.metric("Temperature reads", "300 °C")
    st.caption("Same cut, same instant. To a model, force looks **thousands of times more important than "
               "feed** — purely because of its unit. Press Play to collapse a channel onto 0–1:")
    d = get_data()
    col = st.selectbox("Channel", FEATURES, index=1,
                       format_func=lambda c: NICE[FEATURES.index(c)])
    raw = d["clean"][col].values
    nrm = d["norm"][col].values
    fig = go.Figure(go.Histogram(x=raw, marker_color=MUTED, nbinsx=50))
    frames = []
    for k in range(13):
        t = k / 12
        x = (1 - t) * raw + t * nrm
        frames.append(go.Frame(data=[go.Histogram(x=x, marker_color=POS if t > 0.5 else MUTED,
                                                   nbinsx=50)], name=str(k)))
    fig.update_layout(title=f"{NICE[FEATURES.index(col)]}: raw range collapsing into 0–1")
    style(fig, 400); animate(fig, frames, ms=140)
    st.plotly_chart(fig, use_container_width=True)
    lo, hi = float(d["clean"][col].min()), float(d["clean"][col].max())
    v = st.slider("Try a raw reading", lo, hi, float(d["clean"][col].median()))
    c1, c2 = st.columns(2)
    c1.metric("Raw value", f"{v:.2f}")
    c2.metric("Scaled (0–1)", f"{(v - lo) / (hi - lo + 1e-9):.3f}")


def render_split():
    st.title("⑨ Trial cuts vs the acceptance run")
    st.info("🛠️ **Never test a settings model on the very passes it was tuned on.** It would just repeat "
            "what it memorised, and you would learn nothing about the next part. So some passes train the "
            "model, and some are sealed until the machining audit.")
    st.caption("Press Play: the passes divide into train / validation / test.")
    d = get_data()
    parts = [("Train", d["ytr"], POS), ("Validation", d["yval"], AMBER), ("Test", d["yte"], GREEN)]
    good = [int((a == 0).sum()) for _, a, _ in parts]
    scrap = [int((a == 1).sum()) for _, a, _ in parts]
    names = [n for n, _, _ in parts]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=good, name="good part", marker_color=GREEN))
    fig.add_trace(go.Bar(x=names, y=scrap, name="scrap", marker_color=RED))
    fig.update_layout(barmode="stack", title="passes per split (scrap rate kept balanced across all three)")
    st.plotly_chart(style(fig, 380), use_container_width=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Train", f"{len(d['ytr'])}")
    c2.metric("Validation", f"{len(d['yval'])}")
    c3.metric("Test (sealed)", f"{len(d['yte'])}")
    st.info("The test passes are locked away now and only opened at the machining audit. That is the one "
            "fair score.")


def render_ml_baseline():
    st.title("⑩ Finish and tool life from the readings — Random Forest")
    d = get_data()
    ra_m, tl_m = get_regressors()

    st.markdown("##### What each model learned to weigh — you never set these")
    cA, cB = st.columns(2)
    for col, model, title, colr in [(cA, ra_m, "drivers of surface roughness", POS),
                                    (cB, tl_m, "drivers of tool life", AMBER)]:
        imp = model.feature_importances_
        order = np.argsort(imp)[::-1]
        fig = go.Figure(go.Bar(x=[NICE[i] for i in order], y=imp[order], marker_color=colr,
                               text=[f"{imp[i]:.2f}" for i in order], textposition="outside"))
        fig.update_layout(title=title)
        col.plotly_chart(style(fig, 330), use_container_width=True)
    r1, r2 = st.columns(2)
    from sklearn.metrics import r2_score
    r1.metric("Roughness R² on sealed passes", f"{r2_score(d['RaTe'], ra_m.predict(d['Xte'])):.2f}")
    r2.metric("Tool-life R² on sealed passes", f"{r2_score(d['TLte'], tl_m.predict(d['Xte'])):.2f}")
    st.caption("Feed dominates roughness; speed dominates tool life — exactly what a machinist would tell "
               "you, but here it was learned from 1,400 outcomes, not stated as a rule.")

    st.markdown("##### Try a setting")
    c = st.columns(3)
    Vc = c[0].slider("Cutting speed (m/min)", 60, 280, 180, 5)
    f = c[1].slider("Feed rate (mm/rev)", 0.05, 0.45, 0.20, 0.01)
    ap = c[2].slider("Depth of cut (mm)", 0.3, 3.0, 1.5, 0.1)
    row = _features_for(np.array([Vc]), np.array([f]), np.array([ap]))
    row_s = d["scaler"].transform(row)
    ra_hat = float(ra_m.predict(row_s)[0])
    tl_hat = float(tl_m.predict(row_s)[0])
    ok = ra_hat <= RA_LIMIT and tl_hat >= TL_LIMIT
    m1, m2, m3 = st.columns(3)
    m1.metric("Predicted roughness", f"{ra_hat:.2f} µm", f"limit {RA_LIMIT}")
    m2.metric("Predicted tool life", f"{tl_hat:.0f} min", f"min {TL_LIMIT:.0f}")
    m3.metric("Removal rate", f"{Vc * f * ap:.1f}", "higher = faster")
    st.markdown(f"<div style='padding:14px;border-radius:10px;text-align:center;font-size:18px;"
                f"font-weight:700;background:{GREEN if ok else RED};color:#0e1117'>"
                f"{'✅ within limits' if ok else '❌ out of tolerance / tool too short'}</div>",
                unsafe_allow_html=True)
    st.info("You never wrote an equation. You named the factors — an engineer did that at the trial — and "
            "the Random Forest learned the mapping from 1,400 cuts. The optimizer later searches over "
            "exactly these two predictions.")


def render_neuron():
    st.title("⑮ The neuron — z = w·x + b")
    st.caption("Set a weight for each channel. The neuron multiplies, sums, adds a bias, and squashes to a "
               "probability of a bad part. This is the single computation every layer repeats.")
    d = get_data()
    row = d["norm"].iloc[7]
    x = row[FEATURES].values.astype(float)
    cols = st.columns(len(FEATURES))
    default_w = [0.5, 0.9, 0.3, 0.4, 0.7, 0.4, 0.2]
    w = []
    for i, c in enumerate(cols):
        w.append(c.slider(NICE[i].split(" ")[0], -1.0, 1.0, default_w[i], 0.05, key=f"nw_{i}"))
    b = st.slider("Bias b", -3.0, 1.0, -1.2, 0.1)
    z = float(np.dot(x, w) + b)
    p = sigmoid(z)
    tbl = pd.DataFrame({"Channel": NICE, "x (scaled)": np.round(x, 2),
                        "weight w": np.round(w, 2), "w·x": np.round(x * w, 2)})
    st.dataframe(tbl, use_container_width=True, hide_index=True)
    c1, c2 = st.columns(2)
    c1.metric("z = w·x + b", f"{z:.2f}")
    c2.metric("sigmoid(z) → scrap prob", f"{p*100:.0f}%")
    st.info("Change a weight and watch one cut's score cross the line. Learning, next, is just setting "
            "these weights automatically instead of by hand.")


def render_activation():
    st.title("⑯ Activation — the smooth reject switch")
    z = np.linspace(-8, 8, 200)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=z, y=sigmoid(z), name="sigmoid", line=dict(color=POS, width=3)))
    fig.add_trace(go.Scatter(x=z, y=np.maximum(0, z) / 8, name="ReLU (scaled)",
                             line=dict(color=AMBER, width=3)))
    fig.update_layout(title="a raw score becomes a decision")
    fig.update_xaxes(title="z (weighted evidence)")
    st.plotly_chart(style(fig, 360), use_container_width=True)
    zv = st.slider("Weighted evidence z", -8.0, 8.0, 0.0, 0.1)
    c1, c2 = st.columns(2)
    c1.metric("sigmoid(z)", f"{sigmoid(zv):.2f}", "scrap probability")
    c2.metric("ReLU(z)", f"{max(0, zv):.2f}", "passes strong evidence")
    st.info("A hard cut-off flips on a single noisy reading. Sigmoid ramps up smoothly — doubt, concern, "
            "certainty. Without a non-linear activation, stacking neurons stays a straight line and learns "
            "nothing curved.")


def render_gradient_descent():
    st.title("⑱ Loss and gradient descent")
    st.caption("Loss = how wrong. Gradient = which way is better. Learning rate = how big a step. "
               "Watch the step size decide whether it converges or overshoots.")
    lr = st.slider("Learning rate (step size)", 0.02, 1.05, 0.25, 0.01)
    xs = np.linspace(-4, 4, 200)
    loss = xs ** 2
    path = [3.6]
    for _ in range(18):
        grad = 2 * path[-1]
        path.append(path[-1] - lr * grad)
    path = np.array(path)
    fig = go.Figure(go.Scatter(x=xs, y=loss, mode="lines", line=dict(color=MUTED, width=2),
                               name="loss"))
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
    style(fig, 380); animate(fig, frames, ms=180)
    st.plotly_chart(fig, use_container_width=True)
    st.info("Too small a step and it crawls; too big and it bounces past the minimum into rejecting good "
            "parts. The gradient always points downhill — the art is the step size.")


def render_network():
    st.title("⑲ The network — layered neurons")
    st.caption("One neuron draws one straight line. Layers bend the boundary around real scrap patterns. "
               "Here: feed vs cutting speed, with the model's decision surface behind the cuts.")
    d = get_data()
    depth_opts = {"2 (one tiny layer)": (2,), "6": (6,), "12 → 6": (12, 6), "16 → 8": (16, 8)}
    depth_label = st.select_slider("Hidden layer size", options=list(depth_opts), value="12 → 6")
    depth = depth_opts[depth_label]
    idx = [FEATURES.index("feed_rate"), FEATURES.index("cutting_speed")]
    Xtr2 = d["Xtr"][:, idx]
    m = MLPClassifier(hidden_layer_sizes=depth, max_iter=600, random_state=0).fit(Xtr2, d["ytr"])
    gx, gy = np.meshgrid(np.linspace(0, 1, 80), np.linspace(0, 1, 80))
    grid = np.c_[gx.ravel(), gy.ravel()]
    zz = m.predict_proba(grid)[:, 1].reshape(gx.shape)
    fig = go.Figure()
    fig.add_trace(go.Heatmap(x=np.linspace(0, 1, 80), y=np.linspace(0, 1, 80), z=zz,
                             colorscale="RdBu_r", showscale=False, opacity=0.55))
    te = d["Xte"][:, idx]
    fig.add_trace(go.Scatter(x=te[:, 0], y=te[:, 1], mode="markers",
                             marker=dict(size=6, color=d["yte"], colorscale=[[0, GREEN], [1, RED]],
                                         line=dict(width=0.5, color="#0e1117")),
                             showlegend=False))
    fig.update_layout(title="decision surface — red = predicted scrap")
    fig.update_xaxes(title="feed (scaled)"); fig.update_yaxes(title="cutting speed (scaled)")
    st.plotly_chart(style(fig, 420), use_container_width=True)
    st.info("With one tiny layer the boundary is nearly straight. Add width and depth and it wraps around "
            "the high-feed, high-speed corner — the pattern a single neuron cannot hold.")


def render_training():
    st.title("⑳ Training — the loss falls, then flattens")
    d = get_data()
    lr = st.select_slider("Learning rate", options=[0.0005, 0.001, 0.005, 0.02], value=0.001)
    m = MLPClassifier(hidden_layer_sizes=(12, 6), learning_rate_init=lr,
                      max_iter=1, warm_start=True, random_state=0)
    losses = []
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for _ in range(120):
            m.fit(d["Xtr"], d["ytr"])
            losses.append(m.loss_)
    losses = np.array(losses)
    fig = go.Figure(go.Scatter(y=losses, mode="lines", line=dict(color=MUTED, width=2)))
    frames = [go.Frame(data=[go.Scatter(y=losses[:k + 1], mode="lines",
                                        line=dict(color=POS, width=2))], name=str(k))
              for k in range(0, len(losses), 3)]
    fig.update_layout(title="training loss over epochs")
    fig.update_xaxes(title="epoch"); fig.update_yaxes(title="loss")
    style(fig, 380); animate(fig, frames, ms=60)
    st.plotly_chart(fig, use_container_width=True)
    c1, c2 = st.columns(2)
    c1.metric("Final training loss", f"{losses[-1]:.3f}")
    c2.metric("Test accuracy", f"{m.score(d['Xte'], d['yte'])*100:.1f}%")
    st.info("The loss falls fast, then flattens — more epochs on the same passes only memorise them. "
            "You stop when held-out error stops improving.")


def render_proof():
    st.title("㉔ The verdict — each tool doing the part it is good for")
    st.table(pd.DataFrame({
        "": ["Roughness / tool life (readings)", "Grade the surface from pixels", "Who names the features?"],
        "ML — Random Forest": ["✅ works", "❌ can't even start", "The engineer"],
        "DL — ANN / CNN": ["✅ works", "✅ learns the pattern", "The network learns them"],
    }))
    st.success("On the seven named readings both tools work, because the engineer already named the "
               "factors. On the raw surface image — where no one can hand-write the rule — the CNN takes "
               "that part off the machinist's plate. AI does not out-think the machinist here; it just "
               "handles the job a person cannot do by hand, so the two together cover the whole cut.")
    st.info("When an engineer has named the features, use machine learning — simpler, faster, easier to "
            "defend. When nobody can, as with the surface image, deep learning is the option that works.")


# ============================================================================
# THE OPTIMIZER  —  the sweet spot (the new teaching beat)
# ============================================================================
def render_optimize():
    st.title("㉕ Finding the sweet spot")
    st.caption("Sweep every speed × feed combination, let the trained models score each one, and pick the "
               "fastest setting still inside your limits. This is machine learning turned into a decision.")
    d = get_data()
    ra_m, tl_m = get_regressors()

    c = st.columns(3)
    ap = c[0].slider("Depth of cut (mm) — fixed for this map", 0.3, 3.0, 1.5, 0.1)
    max_ra = c[1].slider("Roughness tolerance (µm)", 1.0, 6.0, RA_LIMIT, 0.1)
    min_tl = c[2].slider("Minimum tool life (min)", 3, 40, int(TL_LIMIT))

    vc_ax = np.linspace(60, 280, 70)
    f_ax = np.linspace(0.05, 0.45, 70)
    VC, F = np.meshgrid(vc_ax, f_ax)
    rows = _features_for(VC.ravel(), F.ravel(), np.full(VC.size, ap))
    rows_s = d["scaler"].transform(rows)
    ra_hat = ra_m.predict(rows_s).reshape(VC.shape)
    tl_hat = tl_m.predict(rows_s).reshape(VC.shape)
    mrr = VC * F * ap
    feasible = (ra_hat <= max_ra) & (tl_hat >= min_tl)

    mrr_feasible = np.where(feasible, mrr, np.nan)
    if np.isfinite(mrr_feasible).any():
        bi = np.nanargmax(mrr_feasible)
        r, cc = np.unravel_index(bi, mrr.shape)
        bestVc, bestF = VC[r, cc], F[r, cc]
        best_ra, best_tl, best_mrr = ra_hat[r, cc], tl_hat[r, cc], mrr[r, cc]
    else:
        bestVc = bestF = best_ra = best_tl = best_mrr = None

    fig = go.Figure(go.Heatmap(x=vc_ax, y=f_ax, z=mrr_feasible, colorscale="Viridis",
                               colorbar=dict(title="removal<br>rate"),
                               hovertemplate="speed %{x:.0f}<br>feed %{y:.2f}<br>rate %{z:.1f}<extra></extra>"))
    # grey-out the infeasible region
    fig.add_trace(go.Heatmap(x=vc_ax, y=f_ax, z=np.where(feasible, np.nan, 1),
                             colorscale=[[0, "#161b22"], [1, "#161b22"]], showscale=False,
                             hoverinfo="skip", opacity=0.82))
    if bestVc is not None:
        fig.add_trace(go.Scatter(x=[bestVc], y=[bestF], mode="markers+text",
                                 marker=dict(size=20, color=RED, symbol="star",
                                             line=dict(color="#fff", width=1.5)),
                                 text=["  optimum"], textposition="middle right",
                                 textfont=dict(color=TEXT, size=13), showlegend=False))
    fig.update_layout(title="feasible settings, colored by removal rate — dark = outside your limits")
    fig.update_xaxes(title="cutting speed (m/min)"); fig.update_yaxes(title="feed rate (mm/rev)")
    st.plotly_chart(style(fig, 460), use_container_width=True)

    if bestVc is None:
        st.error("No setting satisfies these limits. Loosen the roughness tolerance or the minimum tool "
                 "life — the map goes completely dark when nothing is feasible.")
        return

    st.markdown("##### The recommended setting")
    k = st.columns(4)
    k[0].metric("Cutting speed", f"{bestVc:.0f} m/min")
    k[1].metric("Feed rate", f"{bestF:.2f} mm/rev")
    k[2].metric("Predicted roughness", f"{best_ra:.2f} µm", f"≤ {max_ra:.1f}")
    k[3].metric("Predicted tool life", f"{best_tl:.0f} min", f"≥ {min_tl}")

    # productivity vs a cautious baseline
    base = _features_for(np.array([90.0]), np.array([0.10]), np.array([ap]))
    base_mrr = 90.0 * 0.10 * ap
    speedup = best_mrr / base_mrr if base_mrr > 0 else 1.0
    st.success(f"The optimizer removes metal **{speedup:.1f}× faster** than a cautious "
               f"90 m/min · 0.10 mm/rev pass, while holding the finish and tool-life limits. That "
               f"multiplier is the whole reason for the search.")

    st.markdown("##### Productivity vs tool life — the trade-off, and where the optimum sits")
    samp = np.random.default_rng(0).choice(VC.size, 900, replace=False)
    fig2 = go.Figure(go.Scatter(
        x=mrr.ravel()[samp], y=tl_hat.ravel()[samp], mode="markers",
        marker=dict(size=6, color=ra_hat.ravel()[samp], colorscale="Turbo",
                    colorbar=dict(title="Ra µm"), line=dict(width=0)),
        hoverinfo="skip", showlegend=False))
    fig2.add_hline(y=min_tl, line=dict(color=RED, width=1.5, dash="dash"),
                   annotation_text="min tool life")
    fig2.add_trace(go.Scatter(x=[best_mrr], y=[best_tl], mode="markers",
                              marker=dict(size=18, color=RED, symbol="star",
                                          line=dict(color="#fff", width=1.5)), showlegend=False))
    fig2.update_layout(title="each dot is a setting · color = roughness · star = the chosen one")
    fig2.update_xaxes(title="removal rate (faster →)")
    fig2.update_yaxes(title="tool life (min)")
    st.plotly_chart(style(fig2, 400), use_container_width=True)
    st.info("Push removal rate up and tool life falls and roughness reddens. The optimum is the rightmost "
            "point still above the tool-life line and still green enough on roughness — a balance no single "
            "rule gives you, and it moves the moment the tolerance changes.")


# ============================================================================
# THE OPTIMIZATION DASHBOARD — the closing page
# ============================================================================
def render_dashboard():
    st.title("㉘ The machining optimization dashboard")
    st.caption("The batch on one screen: the recommended setting, and the time, tools and scrap it saves "
               "against how the job was run before.")
    d = get_data()
    ra_m, tl_m = get_regressors()

    st.markdown("### The business case — set your batch")
    c1, c2, c3 = st.columns(3)
    parts = c1.slider("Parts in the batch", 20, 2000, 500, 20)
    machine_rate = c2.slider("Machine rate ($/hour)", 20, 200, 75, 5)
    tool_cost = c3.slider("Cost per cutting insert ($)", 5, 120, 35, 5)

    ap = 1.5
    # baseline: a cautious setting most shops default to
    base_Vc, base_f = 100.0, 0.12
    base_row = d["scaler"].transform(_features_for(np.array([base_Vc]), np.array([base_f]), np.array([ap])))
    base_tl = float(tl_m.predict(base_row)[0])
    base_mrr = base_Vc * base_f * ap

    # optimized: search the grid under the standard limits
    vc_ax = np.linspace(60, 280, 60); f_ax = np.linspace(0.05, 0.45, 60)
    VC, F = np.meshgrid(vc_ax, f_ax)
    rows = d["scaler"].transform(_features_for(VC.ravel(), F.ravel(), np.full(VC.size, ap)))
    ra_hat = ra_m.predict(rows).reshape(VC.shape)
    tl_hat = tl_m.predict(rows).reshape(VC.shape)
    mrr = VC * F * ap
    feas = (ra_hat <= RA_LIMIT) & (tl_hat >= TL_LIMIT)
    mrr_f = np.where(feas, mrr, np.nan)
    bi = np.nanargmax(mrr_f); r, cc = np.unravel_index(bi, mrr.shape)
    opt_Vc, opt_f, opt_mrr, opt_tl = VC[r, cc], F[r, cc], mrr[r, cc], tl_hat[r, cc]

    # cycle time scales inversely with removal rate; tool changes scale with life
    base_time = parts / base_mrr
    opt_time = parts / opt_mrr
    base_tools = max(1, base_time * 60 / max(base_tl, 1))
    opt_tools = max(1, opt_time * 60 / max(opt_tl, 1))
    # normalize the two "times" to plausible hours (calibrate baseline to a full shift-ish number)
    scale = 8.0 / base_time
    base_h, opt_h = base_time * scale, opt_time * scale

    time_saved = base_h - opt_h
    money_time = time_saved * machine_rate
    tool_saved = base_tools - opt_tools
    money_tool = tool_saved * tool_cost
    total = money_time + money_tool

    top = st.columns(2)
    top[0].markdown(
        f"<div style='background:{PANEL};border-radius:10px;padding:16px;border-left:5px solid {MUTED}'>"
        f"<span style='color:{MUTED};font-size:12px'>CAUTIOUS BASELINE</span><br>"
        f"<b style='font-size:18px'>{base_Vc:.0f} m/min · {base_f:.2f} mm/rev</b><br>"
        f"<span style='color:{MUTED}'>{base_h:.1f} h · {base_tools:.0f} inserts</span></div>",
        unsafe_allow_html=True)
    top[1].markdown(
        f"<div style='background:{PANEL};border-radius:10px;padding:16px;border-left:5px solid {GREEN}'>"
        f"<span style='color:{MUTED};font-size:12px'>AI-RECOMMENDED SETTING</span><br>"
        f"<b style='font-size:18px'>{opt_Vc:.0f} m/min · {opt_f:.2f} mm/rev</b><br>"
        f"<span style='color:{GREEN}'>{opt_h:.1f} h · {opt_tools:.0f} inserts</span></div>",
        unsafe_allow_html=True)
    st.write("")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Batch time (h)", "Inserts used"], y=[base_h, base_tools],
                         name="cautious baseline", marker_color=MUTED,
                         text=[f"{base_h:.1f}", f"{base_tools:.0f}"], textposition="outside"))
    fig.add_trace(go.Bar(x=["Batch time (h)", "Inserts used"], y=[opt_h, opt_tools],
                         name="AI-recommended", marker_color=GREEN,
                         text=[f"{opt_h:.1f}", f"{opt_tools:.0f}"], textposition="outside"))
    fig.update_layout(barmode="group", title="before vs after — same batch, same limits")
    st.plotly_chart(style(fig, 380), use_container_width=True)

    k = st.columns(3)
    k[0].metric("Time saved on this batch", f"{time_saved:.1f} h", f"${money_time:,.0f}")
    k[1].metric("Inserts saved", f"{tool_saved:.0f}", f"${money_tool:,.0f}")
    k[2].metric("Total saved / batch", f"${total:,.0f}")
    st.info("Faster metal removal shortens the batch; keeping the tool inside its life limit avoids extra "
            "insert changes. This is the number a shop manager acts on — and the reason every earlier stage "
            "was worth building. Both settings hold the same finish and tool-life limits; the AI one just "
            "sits at the productive edge of them.")


# ============================================================================
# THE COURSE, AS ONE MACHINING-OPTIMIZATION PROGRAMME
# bridge.open_page() puts the machining context, challenge and AI connection
# ABOVE each renderer; bridge.close_page() puts the notebook connection BELOW.
# ============================================================================
STAGES = {
    "start":          ("⓪ The project — read this first",
                       lambda: bridge.render_start(style, animate)),
    # PHASE 1 — why machining optimization exists
    "shopfloor":      ("① A batch on the machine", lambda: story.render_shopfloor(style, animate)),
    "enter-ai":       ("② Continuous cut monitoring", lambda: story.render_enter_ai(style, animate)),
    # PHASE 2 — the record
    "trial":          ("③ One cutting pass", lambda: story.render_trial(get_data, style, animate)),
    "two-records":    ("④ Reading vs image", lambda: story.render_two_records(style, animate)),
    # PHASE 3 — the data
    "load":           ("⑤ The machining log arrives", render_load),
    "inspect":        ("⑥ Sensor health check", render_inspect),
    "clean":          ("⑦ Dropouts & spikes", render_clean),
    "normalize":      ("⑧ Standardize units", render_normalize),
    "split":          ("⑨ Trial vs acceptance", render_split),
    "ml-baseline":    ("⑩ Finish & tool life", render_ml_baseline),
    # PHASE 4 — the image that makes DL inevitable
    "surface-problem": ("⑪ The raw image", lambda: story.render_surface_problem(style, animate)),
    "handmade":       ("⑫ Threshold by hand", lambda: story.render_handmade(style, animate)),
    "why-dl":         ("⑬ Therefore deep learning", lambda: story.render_why_dl(style)),
    # PHASE 5 — how a machine learns
    "machinist-brain": ("⑭ How a machinist decides", lambda: story.render_machinist_brain(style)),
    "neuron":         ("⑮ The neuron", render_neuron),
    "activation":     ("⑯ Activation", render_activation),
    "learning-loop":  ("⑰ Learn from scrap", lambda: story.render_learning_loop(style, animate)),
    "gradient-descent": ("⑱ Loss & gradient descent", render_gradient_descent),
    "network":        ("⑲ The network", render_network),
    "training":       ("⑳ Training", render_training),
    # PHASE 6 — the surface
    "cnn-journey":    ("㉑ Inside the CNN", lambda: story.render_cnn_journey(style, animate)),
    # PHASE 7 — the tool
    "tool-chipping":  ("㉒ Detecting a chipped tool", lambda: story.render_tool_chipping(style, animate)),
    # PHASE 8 — evaluation
    "audit":          ("㉓ The machining audit",
                       lambda: story.render_audit(get_data, get_models, style, animate)),
    "proof":          ("㉔ The verdict", render_proof),
    # PHASE 9 — optimization & fusion
    "optimize":       ("㉕ The sweet spot", render_optimize),
    "fusion-engine":  ("㉖ The control screen", lambda: story.render_fusion_engine(style)),
    "pipeline":       ("㉗ The whole cell", lambda: story.render_pipeline(style)),
    # PHASE 10 — the business case
    "dashboard":      ("㉘ The optimization dashboard", render_dashboard),
}

ALIASES = {"floor": "shopfloor", "overview": "shopfloor", "two-signals": "two-records",
           "fusion": "fusion-engine", "lstm": "tool-chipping"}

stage = st.query_params.get("stage", "start")
stage = ALIASES.get(stage, stage)
if stage not in STAGES:
    stage = "start"

with st.sidebar:
    st.markdown("### 🛠️ A Machining Optimization Problem")
    st.caption("You are optimizing a CNC job, and AI keeps turning out to be the thing that eases the "
               "search one machinist cannot do by hand.")
    keys = list(STAGES)
    sel = st.selectbox("Where are we in the shop?", keys, index=keys.index(stage),
                       format_func=lambda k: STAGES[k][0])
    if sel != stage:
        st.query_params["stage"] = sel
        st.rerun()

    if stage in bridge.BY_ID:
        step = bridge.BY_ID[stage]
        pos = bridge.ORDER.index(stage) + 1
        pname = bridge.PHASES[step["phase"]][0]
        st.progress(pos / len(bridge.ORDER),
                    text=f"phase {step['phase']+1}/{len(bridge.PHASES)} · {pname}")
        st.markdown(
            f"<div style='font-size:12px;line-height:1.6'>"
            f"<span style='color:#8b949e'>MACHINING STEP</span><br>"
            f"<b style='color:#ffb74d'>{step['civil']}</b><br>"
            f"<span style='color:#8b949e'>IS THE AI CONCEPT</span><br>"
            f"<b style='color:#4fc3f7'>{step['ai']}</b></div>",
            unsafe_allow_html=True)
    st.divider()
    if st.button("🗺️  The whole project map", use_container_width=True):
        st.query_params["stage"] = "start"
        st.rerun()
    st.caption("▶ Press **Play** on a chart to animate it.")

# ---- the five-part page -----------------------------------------------------
if stage != "start":
    bridge.open_page(stage, style, animate)

STAGES[stage][1]()

if stage != "start":
    bridge.close_page(stage)

st.divider()
narrate(stage)

keys = list(STAGES)
i = keys.index(stage)
nav1, nav2 = st.columns(2)
if i > 0:
    nav1.markdown(f"[← {STAGES[keys[i-1]][0]}](?stage={keys[i-1]})")
if i < len(keys) - 1:
    nav2.markdown(f"<div style='text-align:right'><a href='?stage={keys[i+1]}'>"
                  f"{STAGES[keys[i+1]][0]} →</a></div>", unsafe_allow_html=True)
