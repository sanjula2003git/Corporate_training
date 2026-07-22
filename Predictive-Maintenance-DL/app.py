"""
Intelligent Predictive Maintenance System - Deep Learning illustration app
==========================================================================
One programme, 27 stage pages, taught as one predictive-maintenance project.
Each notebook step links here with ?stage=<id>.

Dark canvas, animated Plotly (press Play) + interactive sliders/toggles.
Every page: mechanical activity -> engineering challenge -> AI concept ->
technical illustration -> notebook connection.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
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

FEATURES = ["temperature_c", "pressure_bar", "vibration_mm_s", "rpm",
            "current_a", "oil_quality", "runtime_h"]
NICE = ["Temp (°C)", "Pressure (bar)", "Vibration (mm/s)", "Speed (RPM)",
        "Current (A)", "Oil (0–100)", "Runtime (h)"]

st.set_page_config(page_title="Predictive Maintenance - DL", page_icon="🏭", layout="wide")


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
# DATA  (synthetic industrial sensor log, generated + cached)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_data():
    rng = np.random.default_rng(42)
    N = 1200
    df = pd.DataFrame({
        "machine_id": np.arange(1, N + 1),
        "temperature_c": rng.normal(65, 12, N).round(1),
        "pressure_bar": rng.normal(6.0, 1.4, N).round(2),
        "vibration_mm_s": np.abs(rng.normal(2.6, 1.5, N)).round(2),
        "rpm": rng.normal(1500, 280, N).round(0),
        "current_a": rng.normal(30, 7, N).round(1),
        "oil_quality": np.clip(rng.normal(70, 15, N), 0, 100).round(0),
        "runtime_h": rng.uniform(0, 20000, N).round(0),
    })
    risk = ((df.vibration_mm_s > 5).astype(int)
            + (df.temperature_c > 85).astype(int)
            + (df.oil_quality < 45).astype(int)
            + (df.current_a > 44).astype(int)
            + (df.runtime_h > 15000).astype(int)
            + ((df.pressure_bar > 9) | (df.pressure_bar < 3)).astype(int))
    df["failure"] = (risk >= 2).astype(int)

    # a realistically messy export: dropouts, stuck/impossible values, duplicates
    dirty = df.copy()
    for col in ["temperature_c", "pressure_bar", "vibration_mm_s", "oil_quality", "current_a"]:
        dirty.loc[rng.choice(N, int(0.06 * N), replace=False), col] = np.nan
    dirty.loc[rng.choice(N, 14, replace=False), "temperature_c"] = 300     # sensor saturation
    dirty.loc[rng.choice(N, 10, replace=False), "pressure_bar"] = -3        # impossible
    dirty.loc[rng.choice(N, 12, replace=False), "vibration_mm_s"] = 0.0     # dead probe
    dirty = pd.concat([dirty, dirty.sample(20, random_state=4)], ignore_index=True)

    clean = dirty.drop_duplicates().copy()
    clean.loc[clean.temperature_c > 200, "temperature_c"] = np.nan
    clean.loc[clean.pressure_bar < 0, "pressure_bar"] = np.nan
    clean.loc[clean.vibration_mm_s <= 0, "vibration_mm_s"] = np.nan
    for col in ["temperature_c", "pressure_bar", "vibration_mm_s", "oil_quality", "current_a"]:
        clean[col] = clean[col].fillna(clean[col].median())

    scaler = MinMaxScaler()
    norm = clean.copy()
    norm[FEATURES] = scaler.fit_transform(clean[FEATURES])

    X, y = norm[FEATURES].values, norm["failure"].values
    Xtr, Xtmp, ytr, ytmp = train_test_split(X, y, test_size=0.30, random_state=42, stratify=y)
    Xval, Xte, yval, yte = train_test_split(Xtmp, ytmp, test_size=0.50, random_state=42, stratify=ytmp)
    return dict(truth=df, dirty=dirty, clean=clean, norm=norm, scaler=scaler,
                Xtr=Xtr, ytr=ytr, Xval=Xval, yval=yval, Xte=Xte, yte=yte)


@st.cache_resource(show_spinner=False)
def get_models():
    d = get_data()
    rf = RandomForestClassifier(n_estimators=200, random_state=42).fit(d["Xtr"], d["ytr"])
    mlp = MLPClassifier(hidden_layer_sizes=(10, 6), max_iter=800, random_state=42).fit(d["Xtr"], d["ytr"])
    return rf, mlp


@st.cache_resource(show_spinner=False)
def train_arch(hidden, activation="relu", lr=0.001):
    d = get_data()
    m = MLPClassifier(hidden_layer_sizes=hidden, activation=activation,
                      learning_rate_init=lr, max_iter=700, random_state=42)
    m.fit(d["Xtr"], d["ytr"])
    return m


# ============================================================================
# TECHNICAL RENDERERS  (Part 4 of each page)
# ============================================================================
def render_load():
    st.title("⑤ The sensor log arrives")
    d = get_data()
    raw = d["dirty"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Records logged", f"{len(raw):,}")
    c2.metric("Columns", raw.shape[1])
    c3.metric("Sensors", len(FEATURES))
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
    fig.update_layout(title="missing readings per sensor")
    st.plotly_chart(style(fig, 360), use_container_width=True)

    col = st.selectbox("Inspect one sensor's distribution", FEATURES,
                       format_func=lambda c: NICE[FEATURES.index(c)])
    vals = raw[col].dropna()
    fig2 = go.Figure(go.Histogram(x=vals, nbinsx=50, marker_color=POS))
    fig2.update_layout(title=f"{NICE[FEATURES.index(col)]} — the spike far from the pack is a sensor fault")
    st.plotly_chart(style(fig2, 340), use_container_width=True)
    st.info("A saturated thermocouple (300 °C), a clogged pressure line (-3 bar) and a dead vibration "
            "probe (0 mm/s) all announce themselves here. Diagnosis only — nothing is repaired yet.")


def render_clean():
    st.title("⑦ Dropouts and spikes out")
    d = get_data()
    before, after = len(d["dirty"]), len(d["clean"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows before", f"{before:,}")
    c2.metric("Rows after", f"{after:,}", f"-{before-after} duplicates")
    c3.metric("Missing after", int(d["clean"][FEATURES].isna().sum().sum()))
    st.caption("Impossible values → removed, then gaps filled with the sensor's median.")
    col = st.selectbox("See a sensor before vs after", FEATURES,
                       format_func=lambda c: NICE[FEATURES.index(c)])
    fig = go.Figure()
    fig.add_trace(go.Box(y=d["dirty"][col], name="dirty", marker_color=NEG))
    fig.add_trace(go.Box(y=d["clean"][col], name="clean", marker_color=GREEN))
    fig.update_layout(title=f"{NICE[FEATURES.index(col)]}: the impossible tails are gone")
    st.plotly_chart(style(fig, 380), use_container_width=True)
    st.info("**Why the median, not the mean?** The mean is dragged by a 300 °C saturation spike. The "
            "median — the middle value — barely notices it.")


def render_normalize():
    st.title("⑧ Standardize the sensors")
    st.info("🛠️ **Every sensor uses a different unit — °C, bar, mm/s, RPM, amps.** Put them all on one "
            "common 0–1 scale first, so the model compares them fairly instead of trusting whichever "
            "reading happens to have the biggest *number*.")
    n1, n2, n3 = st.columns(3)
    n1.metric("Speed reads", "1500 RPM")
    n2.metric("Temperature reads", "78 °C")
    n3.metric("Vibration reads", "6.8 mm/s")
    st.caption("Same machine, same instant. To a model, RPM looks **200× more important than vibration** — "
               "purely because of its unit. Press Play to collapse a sensor onto 0–1:")
    d = get_data()
    col = st.selectbox("Sensor", FEATURES, index=2,
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
    c1.metric("Raw value", f"{v:.1f}")
    c2.metric("Scaled (0–1)", f"{(v - lo) / (hi - lo + 1e-9):.3f}")


def render_split():
    st.title("⑨ Practice machines vs the acceptance test")
    st.info("🛠️ **Never test a health model on the very machines it was tuned on.** It would just repeat "
            "what it memorised, and you would learn nothing about a new machine. So some records train the "
            "model, and some are sealed until the reliability audit.")
    st.caption("Press Play: the records divide into train / validation / test.")
    d = get_data()
    parts = [("Train", d["ytr"], POS), ("Validation", d["yval"], AMBER), ("Test", d["yte"], GREEN)]
    healthy = [int((a == 0).sum()) for _, a, _ in parts]
    fail = [int((a == 1).sum()) for _, a, _ in parts]
    names = [n for n, _, _ in parts]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=healthy, name="healthy", marker_color=GREEN))
    fig.add_trace(go.Bar(x=names, y=fail, name="failure", marker_color=RED))
    fig.update_layout(barmode="stack", title="records per split (failure rate kept balanced across all three)")
    st.plotly_chart(style(fig, 380), use_container_width=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Train", f"{len(d['ytr'])}")
    c2.metric("Validation", f"{len(d['yval'])}")
    c3.metric("Test (sealed)", f"{len(d['yte'])}")
    st.info("The test machines are locked away now and only opened at the reliability audit. That is the "
            "one fair score.")


def render_ml_baseline():
    st.title("⑩ Failure risk from the gauges — Random Forest")
    d = get_data()
    rf, _ = get_models()
    imp = rf.feature_importances_
    order = np.argsort(imp)[::-1]
    fig = go.Figure(go.Bar(x=[NICE[i] for i in order], y=imp[order], marker_color=POS,
                           text=[f"{imp[i]:.2f}" for i in order], textposition="outside"))
    fig.update_layout(title="what the model learned to weigh — you never set these")
    st.plotly_chart(style(fig, 360), use_container_width=True)
    acc = rf.score(d["Xte"], d["yte"])
    st.metric("Accuracy on sealed test machines", f"{acc*100:.1f}%")

    st.markdown("##### Try a machine")
    c = st.columns(4)
    temp = c[0].slider("Temp °C", 40, 110, 90)
    vib = c[1].slider("Vibration mm/s", 0.0, 10.0, 6.5, 0.1)
    oil = c[2].slider("Oil quality", 0, 100, 40)
    run = c[3].slider("Runtime h", 0, 20000, 16000, 500)
    row = np.array([[temp, 6.0, vib, 1500, 32, oil, run]])
    row_s = d["scaler"].transform(row)
    p = rf.predict_proba(row_s)[0, 1]
    st.markdown(f"<div style='padding:16px;border-radius:10px;text-align:center;font-size:20px;"
                f"font-weight:700;background:{RED if p>0.5 else GREEN};color:#0e1117'>"
                f"Failure probability: {p*100:.0f}%</div>", unsafe_allow_html=True)
    st.info("You never wrote a threshold. You named the factors — an engineer already did that at "
            "inspection — and the Random Forest worked out the weighting from 1,200 outcomes.")


def render_neuron():
    st.title("⑮ The neuron — z = w·x + b")
    st.caption("Set a weight for each sensor. The neuron multiplies, sums, adds a bias, and squashes to a "
               "probability. This is the single computation every layer repeats.")
    d = get_data()
    machine = d["norm"].iloc[7]
    x = machine[FEATURES].values
    cols = st.columns(len(FEATURES))
    default_w = [0.4, 0.2, 0.9, 0.0, 0.5, -0.7, 0.6]
    w = []
    for i, c in enumerate(cols):
        w.append(c.slider(NICE[i].split(" ")[0], -1.0, 1.0, default_w[i], 0.05, key=f"nw_{i}"))
    b = st.slider("Bias b", -3.0, 1.0, -1.2, 0.1)
    z = float(np.dot(x, w) + b)
    p = sigmoid(z)
    tbl = pd.DataFrame({"Sensor": NICE, "x (scaled)": np.round(x, 2),
                        "weight w": np.round(w, 2), "w·x": np.round(x * w, 2)})
    st.dataframe(tbl, use_container_width=True, hide_index=True)
    c1, c2 = st.columns(2)
    c1.metric("z = w·x + b", f"{z:.2f}")
    c2.metric("sigmoid(z) → failure prob", f"{p*100:.0f}%")
    st.info("Change a weight and watch one machine's score cross the line. Learning, next, is just setting "
            "these weights automatically instead of by hand.")


def render_activation():
    st.title("⑯ Activation — the smooth alarm switch")
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
    c1.metric("sigmoid(z)", f"{sigmoid(zv):.2f}", "failure probability")
    c2.metric("ReLU(z)", f"{max(0, zv):.2f}", "passes strong evidence")
    st.info("A hard cut-off flips on a single noisy point. Sigmoid ramps up smoothly — doubt, concern, "
            "certainty. Without a non-linear activation, stacking neurons stays a straight line and learns "
            "nothing curved.")


def render_gradient_descent():
    st.title("⑱ Loss and gradient descent")
    st.caption("Loss = how wrong. Gradient = which way is better. Learning rate = how big a step. "
               "Watch the step size decide whether it converges or overshoots.")
    lr = st.slider("Learning rate (step size)", 0.02, 1.05, 0.25, 0.01)
    # a simple 1-D loss bowl; the weight steps downhill
    xs = np.linspace(-4, 4, 200)
    loss = xs ** 2
    w0, path = 3.6, [3.6]
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
    st.info("Too small a step and it crawls; too big and it bounces past the minimum into false alarms. "
            "The gradient always points downhill — the art is the step size.")


def render_network():
    st.title("⑲ The network — layered neurons")
    st.caption("One neuron draws one straight line. Layers bend the boundary around real failure patterns. "
               "Here: temperature vs vibration, with the model's decision surface behind the machines.")
    d = get_data()
    depth_opts = {"2 (one tiny layer)": (2,), "6": (6,), "12 → 6": (12, 6), "16 → 8": (16, 8)}
    depth_label = st.select_slider("Hidden layer size", options=list(depth_opts), value="12 → 6")
    depth = depth_opts[depth_label]
    # train a small net on two readable features
    idx = [FEATURES.index("temperature_c"), FEATURES.index("vibration_mm_s")]
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
    fig.update_layout(title="decision surface — red = predicted failure")
    fig.update_xaxes(title="temperature (scaled)"); fig.update_yaxes(title="vibration (scaled)")
    st.plotly_chart(style(fig, 420), use_container_width=True)
    st.info("With one tiny layer the boundary is nearly straight. Add width and depth and it wraps around "
            "the hot-and-high-vibration corner — the pattern a single neuron cannot hold.")


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
    st.info("The loss falls fast, then flattens — more epochs on the same machines only memorise them. "
            "You stop when held-out error stops improving.")


def render_proof():
    st.title("㉔ The verdict — each tool doing the part it is good for")
    st.table(pd.DataFrame({
        "": ["Failure risk (readings)", "Bearing fault from raw signal", "Who names the features?"],
        "ML — Random Forest": ["✅ works", "❌ can't even start", "The engineer"],
        "DL — ANN / CNN": ["✅ works", "✅ learns the pattern", "The network learns them"],
    }))
    st.success("On the seven named readings both tools work, because the engineer already named the "
               "factors. On the raw waveform — where no one can hand-write the rule — the CNN takes that "
               "part off the engineer's plate. AI does not out-think the engineer here; it just handles "
               "the job a person cannot do by hand, so the two together cover the whole machine.")
    st.info("When an engineer has named the features, use machine learning — simpler, faster, easier to "
            "defend. When nobody can, as with the raw signal, deep learning is the option that works.")


# ============================================================================
# THE PREDICTIVE MAINTENANCE CONTROL CENTER — the closing page
# ============================================================================
@st.cache_data(show_spinner=False)
def fleet(n=12):
    rng = np.random.default_rng(5)
    types = ["Motor", "Pump", "Compressor", "CNC spindle"]
    names = [f"{t[0]}-{rng.integers(1, 40)}" for t in rng.choice(types, n)]
    vib = np.round(np.abs(rng.normal(3.5, 2.2, n)), 1)
    temp = np.round(rng.normal(72, 14, n), 0)
    oil = rng.integers(30, 95, n)
    rul = np.clip((8.0 - vib) / 0.35 + rng.normal(0, 3, n), 0.5, 40).round(0)
    health = np.clip(100 - vib * 9 - (temp - 60) * 0.6 - (70 - oil) * 0.5, 2, 99).round(0)
    crit = rng.choice(["Critical", "Standard", "Spare"], n, p=[0.35, 0.45, 0.2])
    df = pd.DataFrame({"Machine": names, "Type": rng.choice(types, n), "Health": health,
                       "Vibration (mm/s)": vib, "Temp (°C)": temp, "Oil": oil,
                       "RUL (weeks)": rul, "Criticality": crit})
    urg = (100 - df["Health"]) / 100 * df["Criticality"].map(
        {"Critical": 1.0, "Standard": 0.7, "Spare": 0.4}) + (1 - df["RUL (weeks)"] / 40) * 0.3
    df["Priority"] = np.round(urg, 2)
    return df.sort_values("Priority", ascending=False).reset_index(drop=True)


def render_dashboard():
    st.title("㉗ The predictive maintenance control center")
    st.caption("Every machine on one screen, colored by health, ranked by how soon it needs attention.")
    df = fleet()

    def color(h):
        return RED if h < 40 else AMBER if h < 70 else GREEN
    top = df.iloc[0]
    st.markdown(f"<div style='padding:16px 20px;border-radius:10px;background:{PANEL};"
                f"border-left:5px solid {color(top['Health'])}'>"
                f"<span style='color:{MUTED};font-size:12px'>TOP PRIORITY WORK ORDER</span><br>"
                f"<b style='font-size:20px'>{top['Machine']} · {top['Type']}</b> — health "
                f"{top['Health']:.0f}%, vibration {top['Vibration (mm/s)']} mm/s, "
                f"~{top['RUL (weeks)']:.0f} weeks left · <b style='color:{RED}'>{top['Criticality']}</b>"
                f"</div>", unsafe_allow_html=True)
    st.write("")

    fig = go.Figure(go.Bar(
        x=df["Health"], y=df["Machine"], orientation="h",
        marker_color=[color(h) for h in df["Health"]],
        text=[f"{h:.0f}%" for h in df["Health"]], textposition="outside"))
    fig.update_layout(title="fleet health (ranked by priority)", yaxis=dict(autorange="reversed"))
    fig.update_xaxes(title="health %", range=[0, 110])
    st.plotly_chart(style(fig, 460), use_container_width=True)

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("### The business case — downtime avoided")
    c1, c2, c3 = st.columns(3)
    machines = c1.slider("Machines in fleet", 5, 200, 40, 5)
    down_cost = c2.slider("Unplanned downtime cost (per hour, $)", 500, 20000, 5000, 500)
    caught = c3.slider("Failures caught early per month", 0, 20, 6)
    hours_saved = caught * 14          # avg unplanned outage avoided ~14 h
    money = hours_saved * down_cost
    k = st.columns(3)
    k[0].metric("Downtime avoided", f"{hours_saved} h / month")
    k[1].metric("Cost avoided", f"${money:,.0f} / month")
    k[2].metric("Per year", f"${money*12:,.0f}")
    st.info("Planned intervention on an early-caught fault costs a fraction of the unplanned outage it "
            "prevents. This is the number a plant manager acts on — and the reason every earlier stage "
            "was worth building.")


# ============================================================================
# THE COURSE, AS ONE PREDICTIVE-MAINTENANCE PROGRAMME
# bridge.open_page() puts the mechanical context, challenge and AI connection
# ABOVE each renderer; bridge.close_page() puts the notebook connection BELOW.
# ============================================================================
STAGES = {
    "start":          ("⓪ The project — read this first",
                       lambda: bridge.render_start(style, animate)),
    # ACT 1 — why predictive maintenance exists
    "floor":          ("① A shift on the floor", lambda: story.render_floor(style, animate)),
    "enter-ai":       ("② Continuous monitoring", lambda: story.render_enter_ai(style, animate)),
    "inspection":     ("③ Machine inspection", lambda: story.render_inspection(get_data, style, animate)),
    "two-signals":    ("④ Two kinds of record", lambda: story.render_two_signals(style, animate)),
    # ACT 2 — the data
    "load":           ("⑤ The sensor log arrives", render_load),
    "inspect":        ("⑥ Sensor health check", render_inspect),
    "clean":          ("⑦ Dropouts & spikes", render_clean),
    "normalize":      ("⑧ Standardize units", render_normalize),
    "split":          ("⑨ Trial vs acceptance", render_split),
    "ml-baseline":    ("⑩ Risk from the gauges", render_ml_baseline),
    # ACT 3 — the signal that makes DL inevitable
    "signal-problem": ("⑪ The raw waveform", lambda: story.render_signal_problem(style, animate)),
    "handmade":       ("⑫ Threshold by hand", lambda: story.render_handmade(style, animate)),
    "why-dl":         ("⑬ Therefore deep learning", lambda: story.render_why_dl(style)),
    # ACT 4 — how a machine learns
    "engineer-brain": ("⑭ How an engineer decides", lambda: story.render_engineer_brain(style)),
    "neuron":         ("⑮ The neuron", render_neuron),
    "activation":     ("⑯ Activation", render_activation),
    "learning-loop":  ("⑰ Learn from failures", lambda: story.render_learning_loop(style, animate)),
    "gradient-descent": ("⑱ Loss & gradient descent", render_gradient_descent),
    "network":        ("⑲ The network", render_network),
    "training":       ("⑳ Training", render_training),
    # ACT 5 — the raw signal
    "cnn-journey":    ("㉑ Inside the CNN", lambda: story.render_cnn_journey(style, animate)),
    # ACT 6 — the trend
    "lstm":           ("㉒ Reading the trend", lambda: story.render_lstm(style, animate)),
    # ACT 7 — evaluation
    "audit":          ("㉓ The reliability audit",
                       lambda: story.render_audit(get_data, get_models, style, animate)),
    "proof":          ("㉔ The verdict", render_proof),
    # ACT 8 — the product
    "fusion-engine":  ("㉕ The fusion engine", lambda: story.render_fusion_engine(style)),
    "pipeline":       ("㉖ The whole pipeline", lambda: story.render_pipeline(style)),
    # ACT 9 — the business case
    "dashboard":      ("㉗ The control center", render_dashboard),
}

ALIASES = {"overview": "floor", "compare": "two-signals", "fusion": "fusion-engine"}

stage = st.query_params.get("stage", "start")
stage = ALIASES.get(stage, stage)
if stage not in STAGES:
    stage = "start"

with st.sidebar:
    st.markdown("### 🏭 A Reliability Dilemma")
    st.caption("You are running a plant on predictive maintenance, and AI keeps turning out to be the "
               "thing that eases the load one engineer cannot carry alone.")
    keys = list(STAGES)
    sel = st.selectbox("Where are we in the plant?", keys, index=keys.index(stage),
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
            f"<span style='color:#8b949e'>MACHINE ACTIVITY</span><br>"
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
