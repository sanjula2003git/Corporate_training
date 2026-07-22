"""
AI-Based Bridge Digital Twin - Deep Learning illustration app
=============================================================
One project, 29 stage pages, taught as one structural-health-monitoring build.
Each notebook step links here with ?stage=<id>.

Dark canvas, animated Plotly (press Play) + interactive sliders/toggles.
Every page: structural activity -> engineering challenge -> AI concept ->
technical illustration -> notebook connection.

The problem: a bridge deteriorates continuously but is inspected once every year
or two. Instrument it, and learn to estimate and forecast its condition.
  Sensors : natural frequency, strain, vibration, tilt, crack width, corrosion,
            temperature, traffic load, + a drone camera.
  ML      : estimate the condition rating from the readings; forecast RUL.
  DL      : grade a crack image, locate the crack (Grad-CAM).
  The twin: anomaly detection + RUL forecast + fusion into one prioritized alert.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

import story
import bridge

# ----------------------------------------------------------------------------
# THEME / PALETTE   (identical language to the sibling apps)
# ----------------------------------------------------------------------------
BG, PANEL = "#0e1117", "#161b22"
POS, NEG = "#4fc3f7", "#ff8a65"
GREEN, AMBER, RED = "#66bb6a", "#ffb74d", "#ef5350"
TECH = "#ba68c8"
MUTED, TEXT = "#8b949e", "#e6edf3"

# The eight named channels — order matches story.render_reading exactly.
FEATURES = ["nat_freq_hz", "strain_ue", "accel_rms", "tilt_deg",
            "crack_width_mm", "corrosion_pct", "temperature_c", "traffic_load_t"]
NICE = ["Frequency (Hz)", "Strain (µε)", "Vibration (m/s²)", "Tilt (°)",
        "Crack (mm)", "Corrosion (%)", "Temp (°C)", "Load (t)"]

INTERVENE = 55.0        # condition rating below which a component needs work
D_FAIL = 1.0 - INTERVENE / 100.0   # latent damage at the intervention line (0.45)
FREQ0 = 3.30            # Hz  - healthy natural frequency of the deck

st.set_page_config(page_title="Bridge Digital Twin - DL", page_icon="🌉", layout="wide")
bridge.inject_css()   # the bridge app's monitoring-console display language


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


# ----------------------------------------------------------------------------
# ANIMATION HELPERS  (mirror of the pair in story.py)
# _line_grow : draw trace-0 (a line) on left-to-right.
# _bars_grow : grow every bar up from zero together.
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


def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -50, 50)))


# ----------------------------------------------------------------------------
# THE STRUCTURAL PHYSICS  (approximate, monotone, teaching-grade)
# The eight sensors are consequences of a component's latent damage and the
# environment. Frequency DROPS as stiffness is lost; everything else rises. The
# SAME function drives the synthetic dataset AND the "try a reading" tools, so
# they stay consistent — mirrors _condition/_damage_curve in story.py.
# ----------------------------------------------------------------------------
def _condition(damage):
    """Health index 0..100 from latent damage 0..1 (higher rating = healthier)."""
    return np.clip(100.0 * (1.0 - damage), 0, 100)


def _sensors_for(damage, temp, load):
    """Build the 8-channel row(s) the models expect from latent damage and the
    environment (noise-free). Works on scalars or numpy arrays."""
    freq = FREQ0 * (1 - 0.30 * damage) - 0.015 * (temp - 20.0)   # stiffness + thermal
    strain = 90.0 + 480.0 * damage + 5.5 * load                  # µε
    accel = 0.12 + 1.15 * damage + 0.018 * load                  # m/s² RMS
    tilt = 0.02 + 0.85 * damage                                  # degrees
    crack = 0.05 + 2.6 * damage                                  # mm
    corr = 1.5 + 47.0 * damage                                   # %
    return np.stack([freq, strain, accel, tilt, crack, corr, temp, load], axis=-1)


# ----------------------------------------------------------------------------
# DATA  (synthetic monitoring log, generated + cached)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_data():
    rng = np.random.default_rng(42)
    N = 1500
    damage = rng.uniform(0.0, 0.9, N)
    temp = rng.uniform(2.0, 38.0, N)
    load = rng.uniform(3.0, 40.0, N)

    base = _sensors_for(damage, temp, load)
    freq = base[:, 0] + rng.normal(0, 0.03, N)
    strain = np.abs(base[:, 1] + rng.normal(0, 12, N))
    accel = np.abs(base[:, 2] + rng.normal(0, 0.06, N))
    tilt = np.abs(base[:, 3] + rng.normal(0, 0.03, N))
    crack = np.abs(base[:, 4] + rng.normal(0, 0.12, N))
    corr = np.clip(base[:, 5] + rng.normal(0, 2.0, N), 0, None)

    cond = _condition(damage)
    damaged = (cond < INTERVENE).astype(int)

    df = pd.DataFrame({
        "sweep_id": np.arange(1, N + 1),
        "nat_freq_hz": freq.round(3), "strain_ue": strain.round(0),
        "accel_rms": accel.round(3), "tilt_deg": tilt.round(3),
        "crack_width_mm": crack.round(2), "corrosion_pct": corr.round(1),
        "temperature_c": temp.round(1), "traffic_load_t": load.round(1),
        "condition": cond.round(1), "damaged": damaged,
    })

    # a realistically messy export: dropouts, stuck/impossible values, duplicates
    dirty = df.copy()
    for col in ["nat_freq_hz", "strain_ue", "accel_rms", "tilt_deg",
                "crack_width_mm", "corrosion_pct", "temperature_c"]:
        dirty.loc[rng.choice(N, int(0.06 * N), replace=False), col] = np.nan
    dirty.loc[rng.choice(N, 13, replace=False), "strain_ue"] = 9999      # saturated gauge
    dirty.loc[rng.choice(N, 10, replace=False), "temperature_c"] = 999   # thermocouple fault
    dirty.loc[rng.choice(N, 12, replace=False), "accel_rms"] = 0.0       # dead accelerometer
    dirty.loc[rng.choice(N, 11, replace=False), "nat_freq_hz"] = 0.0     # frozen frequency channel
    dirty = pd.concat([dirty, dirty.sample(20, random_state=4)], ignore_index=True)

    clean = dirty.drop_duplicates().copy()
    clean.loc[clean.strain_ue > 5000, "strain_ue"] = np.nan
    clean.loc[clean.temperature_c > 200, "temperature_c"] = np.nan
    clean.loc[clean.accel_rms <= 0, "accel_rms"] = np.nan
    clean.loc[clean.nat_freq_hz <= 0.5, "nat_freq_hz"] = np.nan
    for col in FEATURES:
        clean[col] = clean[col].fillna(clean[col].median())

    scaler = MinMaxScaler()
    norm = clean.copy()
    norm[FEATURES] = scaler.fit_transform(clean[FEATURES])

    X = norm[FEATURES].values
    ydmg = norm["damaged"].values
    ycon = norm["condition"].values      # 0..100 condition rating (regression target)

    idx = np.arange(len(X))
    itr, itmp = train_test_split(idx, test_size=0.30, random_state=42, stratify=ydmg)
    ival, ite = train_test_split(itmp, test_size=0.50, random_state=42, stratify=ydmg[itmp])

    return dict(truth=df, dirty=dirty, clean=clean, norm=norm, scaler=scaler,
                Xtr=X[itr], Xval=X[ival], Xte=X[ite],
                ytr=ydmg[itr], yval=ydmg[ival], yte=ydmg[ite],
                ConTr=ycon[itr], ConTe=ycon[ite])


@st.cache_resource(show_spinner=False)
def get_models():
    d = get_data()
    rf = RandomForestClassifier(n_estimators=200, random_state=42).fit(d["Xtr"], d["ytr"])
    mlp = MLPClassifier(hidden_layer_sizes=(12, 6), max_iter=800, random_state=42).fit(d["Xtr"], d["ytr"])
    return rf, mlp


@st.cache_resource(show_spinner=False)
def get_regressors():
    d = get_data()
    con = RandomForestRegressor(n_estimators=200, random_state=42).fit(d["Xtr"], d["ConTr"])
    return (con,)


# ============================================================================
# TECHNICAL RENDERERS  (Part 4 of each page)
# ============================================================================
def render_load():
    st.title("⑤ The monitoring log arrives")
    d = get_data()
    raw = d["dirty"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Sensor sweeps logged", f"{len(raw):,}")
    c2.metric("Columns", raw.shape[1])
    c3.metric("Sensor channels", len(FEATURES))
    st.caption("The first thing you do with any export: check what actually arrived.")
    st.dataframe(raw.head(8), use_container_width=True, hide_index=True)
    st.info("Types and counts look plausible — but plausible is not verified. The next step inspects the "
            "channels for dropouts and stuck sensors before anything is built on them.")


def render_inspect():
    st.title("⑥ Sensor health check")
    d = get_data()
    raw = d["dirty"]
    miss = raw[FEATURES].isna().sum()
    fig = go.Figure(go.Bar(x=NICE, y=miss.values, marker_color=AMBER,
                           text=miss.values, textposition="outside"))
    fig.update_layout(title="missing readings per channel")
    style(fig, 360)
    animate(fig, _bars_grow([dict(x=NICE, y=list(miss.values), color=AMBER,
                                  text=list(miss.values))]), ms=80)
    st.plotly_chart(fig, use_container_width=True)

    col = st.selectbox("Inspect one channel's distribution", FEATURES,
                       format_func=lambda c: NICE[FEATURES.index(c)])
    vals = raw[col].dropna()
    fig2 = go.Figure(go.Histogram(x=vals, nbinsx=50, marker_color=POS))
    fig2.update_layout(title=f"{NICE[FEATURES.index(col)]} — a spike far from the pack is a sensor fault")
    st.plotly_chart(style(fig2, 340), use_container_width=True)
    st.info("A saturated strain gauge (9,999 µε), a faulted thermocouple (999 °C), a dead accelerometer "
            "(0 m/s²) and a frozen frequency channel (0 Hz) all announce themselves here. Diagnosis only — "
            "nothing is repaired yet.")


def render_clean():
    st.title("⑦ Dropouts and spikes out")
    d = get_data()
    before, after = len(d["dirty"]), len(d["clean"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows before", f"{before:,}")
    c2.metric("Rows after", f"{after:,}", f"-{before-after} duplicates")
    c3.metric("Missing after", int(d["clean"][FEATURES].isna().sum().sum()))
    st.caption("Impossible readings → removed, then gaps filled with the channel's median.")
    col = st.selectbox("See a channel before vs after", FEATURES,
                       format_func=lambda c: NICE[FEATURES.index(c)])
    fig = go.Figure()
    fig.add_trace(go.Box(y=d["dirty"][col], name="dirty", marker_color=NEG))
    fig.add_trace(go.Box(y=d["clean"][col], name="clean", marker_color=GREEN))
    fig.update_layout(title=f"{NICE[FEATURES.index(col)]}: the impossible tails are gone")
    st.plotly_chart(style(fig, 380), use_container_width=True)
    st.info("**Why the median, not the mean?** The mean is dragged by a 9,999 µε saturation spike. The "
            "median — the middle value — barely notices it, so the filled-in reading stays realistic.")


def render_normalize():
    st.title("⑧ Put every channel on one scale")
    st.info("📐 **Every channel reports in its own unit — hertz, microstrain, m/s², degrees, mm, percent, "
            "°C, tonnes.** Put them all on one common 0–1 scale first, so the model compares them fairly "
            "instead of trusting whichever reading happens to have the biggest *number*.")
    n1, n2, n3 = st.columns(3)
    n1.metric("Strain reads", "310 µε")
    n2.metric("Frequency reads", "2.9 Hz")
    n3.metric("Corrosion reads", "14 %")
    st.caption("Same sweep, same instant. To a raw model, strain looks **a hundred times more important than "
               "frequency** — purely because of its unit, when a 0.2 Hz drop is the strongest early warning. "
               "Press Play to collapse a channel onto 0–1:")
    d = get_data()
    col = st.selectbox("Channel", FEATURES, index=1,
                       format_func=lambda c: NICE[FEATURES.index(c)])
    rawv = d["clean"][col].values
    nrm = d["norm"][col].values
    fig = go.Figure(go.Histogram(x=rawv, marker_color=MUTED, nbinsx=50))
    frames = []
    for k in range(13):
        t = k / 12
        x = (1 - t) * rawv + t * nrm
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
    st.title("⑨ Known sweeps vs a sealed set")
    st.info("🧪 **Never test a condition model on the very sweeps it was tuned on.** It would just repeat "
            "what it memorised, and you would learn nothing about the next reading off the bridge. So some "
            "sweeps train the model, and some are sealed until the safety audit.")
    st.caption("Press Play: the sweeps divide into train / validation / test.")
    d = get_data()
    parts = [("Train", d["ytr"], POS), ("Validation", d["yval"], AMBER), ("Test", d["yte"], GREEN)]
    sound = [int((a == 0).sum()) for _, a, _ in parts]
    dmg = [int((a == 1).sum()) for _, a, _ in parts]
    names = [n for n, _, _ in parts]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=sound, name="sound", marker_color=GREEN))
    fig.add_trace(go.Bar(x=names, y=dmg, name="needs intervention", marker_color=RED))
    fig.update_layout(barmode="stack", title="sweeps per split (damage rate kept balanced across all three)")
    style(fig, 380)
    animate(fig, _bars_grow([dict(x=names, y=sound, color=GREEN, name="sound"),
                             dict(x=names, y=dmg, color=RED, name="needs intervention")]), ms=90)
    st.plotly_chart(fig, use_container_width=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Train", f"{len(d['ytr'])}")
    c2.metric("Validation", f"{len(d['yval'])}")
    c3.metric("Test (sealed)", f"{len(d['yte'])}")
    st.info("The test sweeps are locked away now and only opened at the safety audit. That is the one fair "
            "score of the model's behaviour on the bridge's next reading.")


def render_ml_baseline():
    st.title("⑩ Condition from the readings — Random Forest")
    d = get_data()
    (con_m,) = get_regressors()

    st.markdown("##### What the model learned to weigh — you never set these")
    imp = con_m.feature_importances_
    order = np.argsort(imp)[::-1]
    fig = go.Figure(go.Bar(x=[NICE[i] for i in order], y=imp[order], marker_color=POS,
                           text=[f"{imp[i]:.2f}" for i in order], textposition="outside"))
    fig.update_layout(title="drivers of the condition rating")
    style(fig, 340)
    animate(fig, _bars_grow([dict(x=[NICE[i] for i in order], y=list(imp[order]), color=POS,
                                  text=[f"{imp[i]:.2f}" for i in order])]), ms=70)
    st.plotly_chart(fig, use_container_width=True)

    pred = con_m.predict(d["Xte"])
    fig2 = go.Figure(go.Scatter(x=d["ConTe"], y=pred, mode="markers",
                                marker=dict(size=6, color=POS, opacity=0.6, line=dict(width=0))))
    fig2.add_trace(go.Scatter(x=[0, 100], y=[0, 100], mode="lines",
                              line=dict(color=MUTED, dash="dash"), showlegend=False))
    fig2.update_layout(title="predicted vs recorded condition on the sealed sweeps")
    fig2.update_xaxes(title="recorded condition"); fig2.update_yaxes(title="predicted condition")
    st.plotly_chart(style(fig2, 380), use_container_width=True)
    st.metric("Condition R² on sealed sweeps", f"{r2_score(d['ConTe'], pred):.2f}")
    st.caption("Frequency, crack width and corrosion dominate — exactly what an engineer would tell you, but "
               "here it was learned from 1,500 sweeps, not stated as a rule.")

    st.markdown("##### Try a reading — set the true state and the weather")
    c = st.columns(3)
    dmg = c[0].slider("True latent damage", 0.0, 0.9, 0.4, 0.02)
    temp = c[1].slider("Temperature (°C)", 2, 38, 20)
    load = c[2].slider("Traffic load (t)", 3, 40, 20)
    row = _sensors_for(np.array([dmg]), np.array([float(temp)]), np.array([float(load)]))
    row_s = d["scaler"].transform(row)
    con_hat = float(con_m.predict(row_s)[0])
    true_con = float(_condition(dmg))
    ok = con_hat >= INTERVENE
    m1, m2, m3 = st.columns(3)
    m1.metric("Predicted condition", f"{con_hat:.0f}", f"true {true_con:.0f}")
    m2.metric("Intervention line", f"{INTERVENE:.0f}")
    m3.metric("Natural frequency", f"{row[0,0]:.2f} Hz")
    st.markdown(f"<div style='padding:14px;border-radius:10px;text-align:center;font-size:18px;"
                f"font-weight:700;background:{GREEN if ok else RED};color:#0e1117'>"
                f"{'✅ sound — keep monitoring' if ok else '❌ below the line — needs intervention'}</div>",
                unsafe_allow_html=True)
    st.info("You never wrote an equation. You named the factors — an engineer did that — and the Random "
            "Forest learned the mapping from readings to a condition rating. The forecast and the fusion "
            "screen both build on this estimate.")


def render_neuron():
    st.title("⑮ The neuron — z = w·x + b")
    st.caption("Set a weight for each channel. The neuron multiplies, sums, adds a bias, and squashes to a "
               "probability of damage. This is the single computation every layer repeats.")
    d = get_data()
    row = d["norm"].iloc[7]
    x = row[FEATURES].values.astype(float)
    cols = st.columns(len(FEATURES))
    default_w = [-0.9, 0.6, 0.5, 0.5, 0.8, 0.7, 0.1, 0.2]   # freq weighted negative (drop = damage)
    w = []
    for i, c in enumerate(cols):
        w.append(c.slider(NICE[i].split(" ")[0], -1.0, 1.0, default_w[i], 0.05, key=f"nw_{i}"))
    b = st.slider("Bias b", -3.0, 1.0, -0.8, 0.1)
    z = float(np.dot(x, w) + b)
    p = sigmoid(z)
    tbl = pd.DataFrame({"Channel": NICE, "x (scaled)": np.round(x, 2),
                        "weight w": np.round(w, 2), "w·x": np.round(x * w, 2)})
    st.dataframe(tbl, use_container_width=True, hide_index=True)
    c1, c2 = st.columns(2)
    c1.metric("z = w·x + b", f"{z:.2f}")
    c2.metric("sigmoid(z) → damage prob", f"{p*100:.0f}%")
    st.info("A dropping frequency should push toward damage, so its weight is negative. Change a weight and "
            "watch one sweep's score cross the line. Learning, next, is just setting these weights "
            "automatically instead of by hand.")


def render_activation():
    st.title("⑯ Activation — the smooth raise-the-flag switch")
    z = np.linspace(-8, 8, 200)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=z, y=sigmoid(z), name="sigmoid", line=dict(color=POS, width=3)))
    fig.add_trace(go.Scatter(x=z, y=np.maximum(0, z) / 8, name="ReLU (scaled)",
                             line=dict(color=AMBER, width=3)))
    fig.update_layout(title="a raw score becomes a decision (press Play)")
    fig.update_xaxes(title="z (weighted evidence)")
    ys, yr = sigmoid(z), np.maximum(0, z) / 8
    ks = sorted(set(list(range(2, len(z) + 1, 8)) + [len(z)]))
    frames = [go.Frame(data=[go.Scatter(x=z[:k], y=ys[:k], mode="lines", line=dict(color=POS, width=3)),
                             go.Scatter(x=z[:k], y=yr[:k], mode="lines", line=dict(color=AMBER, width=3))])
              for k in ks]
    style(fig, 360); animate(fig, frames, ms=45)
    st.plotly_chart(fig, use_container_width=True)
    zv = st.slider("Weighted evidence z", -8.0, 8.0, 0.0, 0.1)
    c1, c2 = st.columns(2)
    c1.metric("sigmoid(z)", f"{sigmoid(zv):.2f}", "damage probability")
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
    st.info("Too small a step and it crawls; too big and it bounces past the minimum into flagging every "
            "sound span. The gradient always points downhill — the art is the step size.")


def render_network():
    st.title("⑲ The network — layered neurons")
    st.caption("One neuron draws one straight line. Layers bend the boundary around real damage patterns. "
               "Here: frequency vs strain, with the model's decision surface behind the sweeps.")
    d = get_data()
    depth_opts = {"2 (one tiny layer)": (2,), "6": (6,), "12 → 6": (12, 6), "16 → 8": (16, 8)}
    depth_label = st.select_slider("Hidden layer size", options=list(depth_opts), value="12 → 6")
    depth = depth_opts[depth_label]
    idx = [FEATURES.index("nat_freq_hz"), FEATURES.index("strain_ue")]
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
    fig.update_layout(title="decision surface — red = predicted damage")
    fig.update_xaxes(title="frequency (scaled)"); fig.update_yaxes(title="strain (scaled)")
    st.plotly_chart(style(fig, 420), use_container_width=True)
    st.info("With one tiny layer the boundary is nearly straight. Add width and depth and it wraps around "
            "the low-frequency, high-strain corner — the pattern a single neuron cannot hold.")


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
    st.info("The loss falls fast, then flattens — more epochs on the same sweeps only memorise them. You "
            "stop when held-out error stops improving.")


def render_proof():
    st.title("㉔ The verdict — each tool doing the part it is good for")
    d = get_data()
    (con_m,) = get_regressors()
    mlp = MLPRegressor(hidden_layer_sizes=(16, 8), max_iter=1200, random_state=0)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mlp.fit(d["Xtr"], d["ConTr"])
    r_rf = r2_score(d["ConTe"], con_m.predict(d["Xte"]))
    r_ann = r2_score(d["ConTe"], mlp.predict(d["Xte"]))
    c1, c2 = st.columns(2)
    c1.metric("Random Forest — condition R²", f"{r_rf:.2f}")
    c2.metric("Neural network — condition R²", f"{r_ann:.2f}", f"{r_ann - r_rf:+.2f} vs RF")
    st.table(pd.DataFrame({
        "": ["Condition from the 8 readings", "Grade the crack from pixels", "Who names the features?"],
        "ML — Random Forest": ["✅ works", "❌ can't even start", "The engineer"],
        "DL — ANN / CNN": ["✅ works", "✅ learns the pattern", "The network learns them"],
    }))
    st.success("On the eight named readings both tools estimate condition about equally well, because the "
               "engineer already named the factors. On the raw crack image — where no one can hand-write the "
               "rule — the CNN takes that part off the inspector's plate. AI does not out-think the "
               "inspector here; it just handles the job a person cannot do by hand.")
    st.info("When an engineer has named the features, use machine learning — simpler, faster, easier to "
            "defend. When nobody can, as with the crack image, deep learning is the option that works.")


# ============================================================================
# THE TWIN — anomaly detection & RUL forecast (the new teaching beats)
# ============================================================================
def render_anomaly():
    st.title("㉕ Normal for the weather — and the change it can't explain")
    st.caption("A bridge's natural frequency swings with temperature every day. The twin learns that normal "
               "relationship, then flags only the drop the weather does not account for.")

    rng = np.random.default_rng(7)
    # learn "normal" from a clean year of history: frequency depends on temperature
    t_tr = rng.uniform(2, 38, 400)
    f_tr = FREQ0 - 0.015 * (t_tr - 20) + rng.normal(0, 0.02, 400)
    lin = LinearRegression().fit(t_tr[:, None], f_tr)

    months = 120
    tm = np.arange(months)
    temp = 20 + 12 * np.sin(2 * np.pi * tm / 12.0) + rng.normal(0, 1.0, months)  # seasonal
    freq_obs = FREQ0 - 0.015 * (temp - 20) + rng.normal(0, 0.02, months)         # normal behaviour

    c = st.columns(2)
    inject = c[0].toggle("Inject a stiffness loss (real damage)", value=True)
    onset = c[1].slider("Month it begins", 60, 110, 84, 2)
    if inject:
        drop = np.clip((tm - onset) * 0.004, 0, None)   # a slow unexplained frequency loss
        freq_obs = freq_obs - drop

    expected = lin.predict(temp[:, None])
    resid = freq_obs - expected
    thr = 0.05
    alarm = np.where(resid < -thr)[0]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tm, y=freq_obs, mode="lines+markers", name="observed frequency",
                             line=dict(color=POS, width=2), marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=tm, y=expected, mode="lines", name="expected for the weather",
                             line=dict(color=MUTED, width=2, dash="dash")))
    fig.update_layout(title="observed frequency vs what the temperature predicts (press Play)")
    fig.update_xaxes(title="month"); fig.update_yaxes(title="natural frequency (Hz)")
    ks = sorted(set(list(range(2, len(tm) + 1, 4)) + [len(tm)]))
    frames = [go.Frame(data=[
        go.Scatter(x=tm[:k], y=freq_obs[:k], mode="lines+markers",
                   line=dict(color=POS, width=2), marker=dict(size=4)),
        go.Scatter(x=tm[:k], y=expected[:k], mode="lines",
                   line=dict(color=MUTED, width=2, dash="dash"))]) for k in ks]
    style(fig, 360); animate(fig, frames, ms=40)
    st.plotly_chart(fig, use_container_width=True)

    fig2 = go.Figure()
    colr = np.where(resid < -thr, RED, POS)
    fig2.add_trace(go.Bar(x=tm, y=resid, marker_color=colr, showlegend=False))
    fig2.add_hline(y=-thr, line=dict(color=RED, width=1.5, dash="dash"),
                   annotation_text="alarm threshold")
    fig2.update_layout(title="residual = observed − expected (near zero when normal)")
    fig2.update_xaxes(title="month"); fig2.update_yaxes(title="residual (Hz)")
    st.plotly_chart(style(fig2, 340), use_container_width=True)

    m1, m2 = st.columns(2)
    if len(alarm):
        m1.metric("Anomaly first flagged", f"month {int(alarm[0])}")
        m2.metric("Sweeps over threshold", len(alarm), delta_color="inverse")
        st.error(f"The raw frequency never left its seasonal band, so a fixed alarm would have stayed "
                 f"silent. The **residual** — what temperature cannot explain — crosses the line in month "
                 f"{int(alarm[0])}. That is the stiffness loss, caught inside the normal swing.")
    else:
        m1.metric("Anomaly flagged", "none")
        m2.metric("Sweeps over threshold", 0)
        st.success("The residual stays near zero all year: every frequency swing is explained by the "
                   "weather. Nothing anomalous — exactly what you want most months.")
    st.info("A fixed frequency threshold either trips every summer or hides real damage inside the seasonal "
            "swing. Learning the normal frequency-for-temperature and scoring the residual separates the "
            "two. That is anomaly detection — the early-warning branch of the twin.")


def render_rul_forecast():
    st.title("㉖ How long until it needs work — RUL")
    st.caption("A component's condition drifts down over months. Fit the trend, extend it to the "
               "intervention line, and read off the Remaining Useful Life.")

    rng = np.random.default_rng(3)
    horizon = 120
    c = st.columns(3)
    obs = c[0].slider("Months of history observed", 12, 84, 48, 6)
    rate = c[1].slider("Deterioration rate", 0.004, 0.016, 0.009, 0.001)
    quad = c[2].toggle("Fit an accelerating (quadratic) trend", value=True)

    tm = np.arange(horizon)
    damage = np.clip(rate * tm + 0.00006 * tm ** 2, 0, 1.2)
    cond_true = _condition(damage)
    cond_obs = cond_true[:obs] + rng.normal(0, 1.6, obs)     # noisy monitored history

    tt = tm[:obs]
    if quad:
        coef = np.polyfit(tt, cond_obs, 2)
    else:
        coef = np.polyfit(tt, cond_obs, 1)
    trend = np.poly1d(coef)
    future = np.arange(horizon)
    proj = trend(future)
    below = np.where(proj <= INTERVENE)[0]
    cross = int(below[0]) if len(below) else horizon
    rul = max(0, cross - obs)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tm, y=cond_true, mode="lines", name="true condition (unseen future)",
                             line=dict(color=MUTED, width=1.5, dash="dot")))
    fig.add_trace(go.Scatter(x=tt, y=cond_obs, mode="markers", name="monitored history",
                             marker=dict(size=6, color=POS)))
    fig.add_trace(go.Scatter(x=future[obs - 1:cross + 1], y=proj[obs - 1:cross + 1], mode="lines",
                             name="fitted trend, projected", line=dict(color=AMBER, width=3)))
    fig.add_hline(y=INTERVENE, line=dict(color=RED, width=2, dash="dash"),
                  annotation_text="intervention level", annotation_position="bottom left")
    fig.add_vline(x=obs, line=dict(color=TEXT, width=1),
                  annotation_text="today", annotation_position="top")
    if cross < horizon:
        fig.add_trace(go.Scatter(x=[cross], y=[INTERVENE], mode="markers",
                                 marker=dict(size=16, color=RED, symbol="x"),
                                 name="projected crossing"))
    fig.update_layout(title="condition history, the fitted trend, and where it crosses the line")
    fig.update_xaxes(title="month"); fig.update_yaxes(title="condition rating", range=[0, 105])
    style(fig, 420)
    seg_x, seg_y = future[obs - 1:cross + 1], proj[obs - 1:cross + 1]
    if len(seg_x) >= 3:
        # keep true-condition (trace 0) and history (trace 1) full; grow the amber projection (trace 2)
        frames = [go.Frame(data=[
            go.Scatter(x=tm, y=cond_true, mode="lines", line=dict(color=MUTED, width=1.5, dash="dot")),
            go.Scatter(x=tt, y=cond_obs, mode="markers", marker=dict(size=6, color=POS)),
            go.Scatter(x=seg_x[:k], y=seg_y[:k], mode="lines", line=dict(color=AMBER, width=3))])
            for k in range(2, len(seg_x) + 1)]
        animate(fig, frames, ms=70)
    st.plotly_chart(fig, use_container_width=True)

    true_below = np.where(cond_true <= INTERVENE)[0]
    true_cross = int(true_below[0]) if len(true_below) else horizon
    k = st.columns(3)
    k[0].metric("Projected crossing", f"month {cross}" if cross < horizon else "beyond horizon")
    k[1].metric("Remaining useful life", f"{rul} months")
    k[2].metric("Actual crossing", f"month {true_cross}", f"{cross - true_cross:+d} vs forecast")
    if obs < 30:
        st.warning("With only a short history the trend is uncertain — extend the observed window and the "
                   "projected crossing settles onto the true one. A forecast is only as good as the trend "
                   "it can see.")
    st.info("Reactive maintenance waits for the line to be crossed; calendar maintenance repairs whether it "
            "is needed or not. Fitting the trend and extrapolating answers the question the asset manager "
            "actually asks: **how many months until this component needs work?**")


# ============================================================================
# THE PREDICTIVE-MAINTENANCE DASHBOARD — the closing page
# ============================================================================
def render_dashboard():
    st.title("㉙ The predictive-maintenance dashboard")
    st.caption("The network on one screen: catch damage early with the twin, or wait for it to show. The "
               "difference is repair cost, closures avoided, and risk taken off the bridges.")

    st.markdown("### The business case — set your network")
    c1, c2, c3 = st.columns(3)
    bridges = c1.slider("Bridges monitored", 5, 200, 40, 5)
    planned_cost = c2.slider("Planned repair ($k / bridge)", 20, 300, 80, 10)
    reactive_mult = c3.slider("Emergency repair multiplier", 2.0, 8.0, 4.0, 0.5)

    c4, c5 = st.columns(2)
    fail_rate = c4.slider("Bridges developing damage per year (%)", 2, 30, 12, 1) / 100.0
    closure_cost = c5.slider("Cost of an emergency closure ($k)", 50, 1000, 300, 50)

    at_risk = bridges * fail_rate
    # reactive: every damaged bridge hits an emergency repair + a share end in closure
    reactive_repair = at_risk * planned_cost * reactive_mult
    reactive_closure = at_risk * 0.4 * closure_cost
    reactive_total = reactive_repair + reactive_closure
    # predictive: caught early → planned repair, closures largely avoided
    predictive_repair = at_risk * planned_cost
    predictive_closure = at_risk * 0.05 * closure_cost
    predictive_total = predictive_repair + predictive_closure
    saved = reactive_total - predictive_total
    closures_avoided = at_risk * (0.4 - 0.05)

    top = st.columns(2)
    top[0].markdown(
        f"<div style='background:{PANEL};border-radius:10px;padding:16px;border-left:5px solid {MUTED}'>"
        f"<span style='color:{MUTED};font-size:12px'>REACTIVE — WAIT FOR DAMAGE TO SHOW</span><br>"
        f"<b style='font-size:20px'>${reactive_total:,.0f}k / year</b><br>"
        f"<span style='color:{MUTED}'>{at_risk:.0f} emergency repairs · {at_risk*0.4:.0f} closures</span></div>",
        unsafe_allow_html=True)
    top[1].markdown(
        f"<div style='background:{PANEL};border-radius:10px;padding:16px;border-left:5px solid {GREEN}'>"
        f"<span style='color:{MUTED};font-size:12px'>PREDICTIVE — THE DIGITAL TWIN</span><br>"
        f"<b style='font-size:20px'>${predictive_total:,.0f}k / year</b><br>"
        f"<span style='color:{GREEN}'>{at_risk:.0f} planned repairs · {at_risk*0.05:.0f} closures</span></div>",
        unsafe_allow_html=True)
    st.write("")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Repairs", "Closures"], y=[reactive_repair, reactive_closure],
                         name="reactive", marker_color=MUTED,
                         text=[f"${reactive_repair:,.0f}k", f"${reactive_closure:,.0f}k"],
                         textposition="outside"))
    fig.add_trace(go.Bar(x=["Repairs", "Closures"], y=[predictive_repair, predictive_closure],
                         name="predictive", marker_color=GREEN,
                         text=[f"${predictive_repair:,.0f}k", f"${predictive_closure:,.0f}k"],
                         textposition="outside"))
    fig.update_layout(barmode="group", title="reactive vs predictive — same network, same year")
    style(fig, 380)
    animate(fig, _bars_grow([
        dict(x=["Repairs", "Closures"], y=[reactive_repair, reactive_closure], color=MUTED, name="reactive",
             text=[f"${reactive_repair:,.0f}k", f"${reactive_closure:,.0f}k"]),
        dict(x=["Repairs", "Closures"], y=[predictive_repair, predictive_closure], color=GREEN, name="predictive",
             text=[f"${predictive_repair:,.0f}k", f"${predictive_closure:,.0f}k"])]), ms=90)
    st.plotly_chart(fig, use_container_width=True)

    k = st.columns(3)
    k[0].metric("Bridges caught early / year", f"{at_risk:.0f}")
    k[1].metric("Emergency closures avoided", f"{closures_avoided:.0f}")
    k[2].metric("Saved per year", f"${saved:,.0f}k")
    st.info("Catching damage while it is still a planned repair avoids the emergency-repair multiplier and "
            "most of the closures. This is the number an asset manager acts on — and the reason every "
            "earlier stage, from cleaning the data to forecasting the RUL, was worth building.")


# ============================================================================
# THE COURSE, AS ONE STRUCTURAL-HEALTH-MONITORING PROGRAMME
# bridge.open_page() puts the structural context, challenge and AI connection
# ABOVE each renderer; bridge.close_page() puts the notebook connection BELOW.
# ============================================================================
STAGES = {
    "start":          ("⓪ The project — read this first",
                       lambda: bridge.render_start(style, animate)),
    # PHASE 1 — why predictive SHM exists
    "in-service":     ("① A bridge under load", lambda: story.render_in_service(style, animate)),
    "enter-ai":       ("② The digital twin", lambda: story.render_enter_ai(style, animate)),
    # PHASE 2 — a single reading
    "reading":        ("③ One sensor sweep", lambda: story.render_reading(get_data, style, animate)),
    "two-records":    ("④ Reading vs image", lambda: story.render_two_records(style, animate)),
    # PHASE 3 — instrumenting & the data
    "load":           ("⑤ The monitoring log arrives", render_load),
    "inspect":        ("⑥ Sensor health check", render_inspect),
    "clean":          ("⑦ Dropouts & spikes", render_clean),
    "normalize":      ("⑧ One common scale", render_normalize),
    "split":          ("⑨ Known vs sealed", render_split),
    "ml-baseline":    ("⑩ Condition from readings", render_ml_baseline),
    # PHASE 6 — the image that makes DL inevitable
    "crack-problem":  ("⑪ The raw image", lambda: story.render_crack_problem(style, animate)),
    "handmade":       ("⑫ Threshold by hand", lambda: story.render_handmade(style, animate)),
    "why-dl":         ("⑬ Therefore deep learning", lambda: story.render_why_dl(style)),
    # PHASE 7 — how a machine learns
    "engineer-brain": ("⑭ The inspector's judgement", lambda: story.render_engineer_brain(style)),
    "neuron":         ("⑮ The neuron", render_neuron),
    "activation":     ("⑯ Activation", render_activation),
    "learning-loop":  ("⑰ The learning loop", lambda: story.render_learning_loop(style, animate)),
    "gradient-descent": ("⑱ Loss & gradient descent", render_gradient_descent),
    "network":        ("⑲ The network", render_network),
    "training":       ("⑳ Training", render_training),
    # PHASE 8 — reading the crack
    "cnn-journey":    ("㉑ Inside the CNN", lambda: story.render_cnn_journey(style, animate)),
    # PHASE 9 — locating the damage
    "crack-locate":   ("㉒ Locating the crack", lambda: story.render_crack_locate(style, animate)),
    # PHASE 10 — the safety audit
    "audit":          ("㉓ The safety audit",
                       lambda: story.render_audit(get_data, get_models, style, animate)),
    "proof":          ("㉔ The verdict", render_proof),
    # PHASE 11 — prediction & the twin
    "anomaly":        ("㉕ Normal vs anomaly", render_anomaly),
    "rul-forecast":   ("㉖ Remaining useful life", render_rul_forecast),
    "fusion-engine":  ("㉗ The bridge health screen", lambda: story.render_fusion_engine(style)),
    "pipeline":       ("㉘ The whole twin", lambda: story.render_pipeline(style, animate)),
    # PHASE 12 — the business case
    "dashboard":      ("㉙ The predictive-maintenance dashboard", render_dashboard),
}

ALIASES = {"overview": "in-service", "two-signals": "two-records", "fusion": "fusion-engine",
           "rul": "rul-forecast", "forecast": "rul-forecast", "twin": "enter-ai"}

stage = st.query_params.get("stage", "start")
stage = ALIASES.get(stage, stage)
if stage not in STAGES:
    stage = "start"

with st.sidebar:
    st.markdown("### 🌉 A Structural Health Problem")
    st.caption("You are building a bridge digital twin, and AI keeps turning out to be the thing that covers "
               "the watch one inspector cannot keep across a whole network.")
    keys = list(STAGES)
    sel = st.selectbox("Where are we on the bridge?", keys, index=keys.index(stage),
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
            f"<span style='color:#8b949e'>STRUCTURAL STEP</span><br>"
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
