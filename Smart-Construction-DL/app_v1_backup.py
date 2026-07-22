"""
Smart Construction Site - Deep Learning illustration app
=========================================================
One file, 23 stage pages. Each notebook step links here with ?stage=<id>.

3Blue1Brown-style: dark canvas, glowing nodes, weighted edges.
ANIMATED (plotly frames, press Play) + INTERACTIVE (sliders/toggles) + VOICE narration.
"""

import os
import json
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, confusion_matrix

# ----------------------------------------------------------------------------
# THEME / PALETTE  (3b1b-ish)
# ----------------------------------------------------------------------------
BG, PANEL = "#0e1117", "#161b22"
POS, NEG = "#4fc3f7", "#ff8a65"
GREEN, AMBER, RED = "#66bb6a", "#ffb74d", "#ef5350"
MUTED, TEXT = "#8b949e", "#e6edf3"

FEATURES = ["gas_ppm", "dust_level", "temperature_c", "humidity",
            "accel_mag", "proximity_m", "noise_db"]
NICE = ["Gas (ppm)", "Dust", "Temp (C)", "Humidity", "Accel", "Proximity", "Noise (dB)"]

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, "audio")
CNN_ASSETS = os.path.join(HERE, "cnn_assets")

st.set_page_config(page_title="Smart Construction Site - DL", page_icon="🦺", layout="wide")


def style(fig, h=440):
    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG, font_color=TEXT,
        margin=dict(l=30, r=30, t=60, b=30), height=h,
        template="plotly_dark", legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="#222933", zerolinecolor="#333")
    fig.update_yaxes(gridcolor="#222933", zerolinecolor="#333")
    return fig


def animate(fig, frames, ms=350, loop_hint=True):
    """Attach frames + Play/Pause controls (this is what makes it dynamic)."""
    fig.frames = frames
    fig.update_layout(updatemenus=[dict(
        type="buttons", direction="left", showactive=False,
        x=1.0, y=1.16, xanchor="right", yanchor="top",   # right side: keeps the chart clear
        bgcolor=PANEL, bordercolor=MUTED, font=dict(color=TEXT, size=13),
        buttons=[
            dict(label="▶  Play", method="animate",
                 args=[None, dict(frame=dict(duration=ms, redraw=True),
                                  fromcurrent=True, transition=dict(duration=120))]),
            dict(label="⏸  Pause", method="animate",
                 args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")]),
        ])])
    return fig


# ----------------------------------------------------------------------------
# VOICE NARRATION
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def narration_text():
    p = os.path.join(AUDIO, "narration.json")
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {}


def narrate(stage):
    mp3 = os.path.join(AUDIO, f"{stage}.mp3")
    if not os.path.isfile(mp3):
        return
    st.caption("🔊  **Narration** — press play to hear what's happening inside this step")
    st.audio(mp3, format="audio/mp3")
    txt = narration_text().get(stage)
    if txt:
        with st.expander("📄 Transcript"):
            st.write(txt)


# ----------------------------------------------------------------------------
# DATA (generated behind the scenes; cached)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_data():
    rng = np.random.default_rng(42)
    N = 1200
    df = pd.DataFrame({
        "shift_id": np.arange(1, N + 1),
        "gas_ppm": rng.normal(50, 15, N).round(1),
        "dust_level": rng.normal(80, 25, N).round(1),
        "temperature_c": rng.normal(34, 5, N).round(1),
        "humidity": rng.normal(60, 12, N).round(1),
        "accel_mag": rng.normal(1.0, 0.3, N).round(2),
        "proximity_m": np.abs(rng.normal(4, 2, N)).round(2),
        "noise_db": rng.normal(85, 8, N).round(1),
    })
    risk = ((df.gas_ppm > 70).astype(int) + (df.dust_level > 110).astype(int)
            + (df.temperature_c > 40).astype(int) + (df.accel_mag > 1.6).astype(int)
            + (df.proximity_m < 1.5).astype(int) + (df.noise_db > 95).astype(int))
    df["accident_incident"] = (risk >= 2).astype(int)

    dirty = df.copy()
    for col in ["gas_ppm", "dust_level", "temperature_c", "humidity", "proximity_m"]:
        dirty.loc[rng.choice(N, int(0.06 * N), replace=False), col] = np.nan
    dirty.loc[rng.choice(N, 15, replace=False), "gas_ppm"] = 9999
    dirty.loc[rng.choice(N, 12, replace=False), "temperature_c"] = 150
    dirty.loc[rng.choice(N, 10, replace=False), "proximity_m"] = -5
    dirty = pd.concat([dirty, dirty.sample(20, random_state=4)], ignore_index=True)

    clean = dirty.drop_duplicates().copy()
    clean.loc[clean.gas_ppm > 1000, "gas_ppm"] = np.nan
    clean.loc[clean.temperature_c > 60, "temperature_c"] = np.nan
    clean.loc[clean.proximity_m < 0, "proximity_m"] = np.nan
    for col in ["gas_ppm", "dust_level", "temperature_c", "humidity", "proximity_m"]:
        clean[col] = clean[col].fillna(clean[col].median())

    scaler = MinMaxScaler()
    norm = clean.copy()
    norm[FEATURES] = scaler.fit_transform(clean[FEATURES])

    X, y = norm[FEATURES].values, norm["accident_incident"].values
    Xtr, Xtmp, ytr, ytmp = train_test_split(X, y, test_size=0.30, random_state=42, stratify=y)
    Xval, Xte, yval, yte = train_test_split(Xtmp, ytmp, test_size=0.50, random_state=42, stratify=ytmp)
    return dict(truth=df, dirty=dirty, clean=clean, norm=norm, scaler=scaler,
                Xtr=Xtr, ytr=ytr, Xval=Xval, yval=yval, Xte=Xte, yte=yte)


@st.cache_resource(show_spinner=False)
def get_models():
    d = get_data()
    rf = RandomForestClassifier(n_estimators=200, random_state=42).fit(d["Xtr"], d["ytr"])
    mlp = MLPClassifier(hidden_layer_sizes=(8, 6), max_iter=800, random_state=42).fit(d["Xtr"], d["ytr"])
    return rf, mlp


@st.cache_resource(show_spinner=False)
def train_arch(hidden, activation="relu", solver="adam", lr=0.001):
    """Train an ANN with a user-chosen architecture / machinery."""
    d = get_data()
    m = MLPClassifier(hidden_layer_sizes=hidden, activation=activation, solver=solver,
                      learning_rate_init=lr, max_iter=700, random_state=42)
    m.fit(d["Xtr"], d["ytr"])
    return m


def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -50, 50)))


def forward_pass(mlp, x):
    """Returns pre-activations z per layer and activations a per layer (a[0] = x)."""
    zs, acts, a = [], [x], x
    for i, (W, b) in enumerate(zip(mlp.coefs_, mlp.intercepts_)):
        z = a @ W + b
        zs.append(z)
        a = np.maximum(0, z) if i < len(mlp.coefs_) - 1 else sigmoid(z)
        acts.append(a)
    return zs, acts


def neuron_sensitivity(mlp, x, l, j):
    """∂(activation of neuron j in layer l) / ∂(each of the 7 input sensors).
    This is literally 'what sensor pattern does this neuron detect', by chain rule."""
    zs, acts = forward_pass(mlp, x)
    L = len(mlp.coefs_)
    if l - 1 < L - 1:
        dact = (zs[l - 1] > 0).astype(float)          # ReLU'
    else:
        a = acts[-1]; dact = a * (1 - a)               # sigmoid'
    g = np.zeros_like(zs[l - 1], dtype=float)
    g[j] = dact[j]                                     # grad wrt z[l-1]
    k = l - 1
    while k > 0:
        g = (g @ mlp.coefs_[k].T) * (zs[k - 1] > 0).astype(float)
        k -= 1
    return g @ mlp.coefs_[0].T                         # grad wrt the input sensors


@st.cache_resource(show_spinner=False)
def feature_emergence(hidden=(8, 6), epochs=60, every=2):
    """Train from RANDOM, snapshotting layer-1 weights so we can watch features form."""
    d = get_data()
    m = MLPClassifier(hidden_layer_sizes=hidden, solver="adam", learning_rate_init=0.01,
                      random_state=0, max_iter=1)
    snaps, losses, eps = [], [], []
    for e in range(epochs):
        m.partial_fit(d["Xtr"], d["ytr"], classes=np.array([0, 1]))
        if e % every == 0:
            snaps.append(m.coefs_[0].copy()); losses.append(float(m.loss_)); eps.append(e)
    return snaps, losses, eps


def backprop(mlp, x, y_true):
    """Real backprop (chain rule). Returns zs, acts, deltas (error signal), dW, db."""
    zs, acts = forward_pass(mlp, x)
    L = len(mlp.coefs_)
    deltas = [None] * L
    # sigmoid output + binary cross-entropy => dLoss/dz = a - y
    deltas[-1] = acts[-1] - float(y_true)
    for i in range(L - 2, -1, -1):
        deltas[i] = (deltas[i + 1] @ mlp.coefs_[i + 1].T) * (zs[i] > 0).astype(float)  # ReLU'
    dW = [np.outer(acts[i], deltas[i]) for i in range(L)]
    db = [d.copy() for d in deltas]
    return zs, acts, deltas, dW, db


# positions are (left%, top%) over the real construction-site photo
SENSORS = [
    ("Gas sensor", "🟢", 14, 78, "gas_ppm", "ML", "Toxic / flammable gas (ppm)."),
    ("Dust sensor", "🌫️", 30, 22, "dust_level", "ML", "Airborne particulate level."),
    ("Temperature", "🌡️", 73, 20, "temperature_c", "ML", "Heat-stress risk."),
    ("Humidity", "💧", 13, 35, "humidity", "ML", "Moisture conditions."),
    ("Accelerometer", "📉", 87, 50, "accel_mag", "ML", "Sudden impacts / falls (g)."),
    ("Proximity", "📡", 79, 74, "proximity_m", "ML", "Distance to machinery (m)."),
    ("Noise sensor", "🔊", 7, 60, "noise_db", "ML", "Industrial noise (dB)."),
    ("Helmet camera", "📷", 43, 40, None, "DL", "Raw pixels → CNN helmet check."),  # the real CCTV pole
    ("GPS + RFID", "🛰️", 57, 90, None, "Fusion", "Which worker, and where."),
]
STAGE_COLOR = {"ML": POS, "DL": AMBER, "Fusion": GREEN}


# ============================================================================
# STAGES
# ============================================================================
@st.cache_data(show_spinner=False)
def site_image_b64():
    p = os.path.join(HERE, "site", "construction_site.jpg")
    if not os.path.isfile(p):
        return None
    import base64
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode()


def render_overview():
    st.title("🦺 Smart Construction Site")
    st.caption("A real site. The sensors are hidden — **hover or tap** anywhere on the site to find them.")
    d = get_data()
    latest = d["dirty"].iloc[-1]

    b64 = site_image_b64()
    if not b64:
        st.error("site/construction_site.jpg not found.")
    else:
        hotspots = ""
        for name, emoji, left, top, col, stage, _desc in SENSORS:
            c = STAGE_COLOR[stage]
            reading = f"{latest[col]:.1f}" if col and not pd.isna(latest[col]) else "image frame"
            hotspots += (
                f'<div class="hot" style="--c:{c};left:{left}%;top:{top}%">{emoji}'
                f'<span class="lab"><b>{name}</b> · {stage}<br>reading: {reading}</span></div>')
        legend = "".join(
            f'<span class="lg"><i style="background:{c}"></i>{s} stage</span>'
            for s, c in STAGE_COLOR.items())
        html = f"""
<style>
  *{{box-sizing:border-box}}
  body{{margin:0;background:#0e1117;font-family:-apple-system,"Segoe UI",Roboto,sans-serif}}
  .bar{{display:flex;align-items:center;gap:16px;margin:0 0 10px;flex-wrap:wrap}}
  .tog{{cursor:pointer;color:#e6edf3;font-size:12.5px;background:#161b22;border:1px solid #30363d;
        padding:6px 11px;border-radius:8px;user-select:none}}
  .tog:hover{{border-color:#4fc3f7}}
  .lg{{color:#8b949e;font-size:12px;margin-right:10px;display:inline-flex;align-items:center}}
  .lg i{{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:5px}}
  .wrap{{position:relative;width:100%;border-radius:12px;overflow:hidden;line-height:0;
         border:1px solid #30363d}}
  .wrap img{{width:100%;height:auto;display:block}}
  .hot{{position:absolute;transform:translate(-50%,-50%);width:40px;height:40px;border-radius:50%;
        display:flex;align-items:center;justify-content:center;font-size:17px;line-height:1;
        cursor:pointer;background:transparent;border:2px solid transparent;opacity:0;
        transition:all .2s ease;-webkit-tap-highlight-color:transparent}}
  .hot:hover,.hot:active{{opacity:1;background:rgba(13,17,23,.85);border-color:var(--c);
        box-shadow:0 0 0 9px rgba(255,255,255,.05), 0 0 30px 6px var(--c);
        transform:translate(-50%,-50%) scale(1.2)}}
  .lab{{position:absolute;top:128%;left:50%;transform:translateX(-50%);white-space:nowrap;
        background:rgba(13,17,23,.95);border:1px solid var(--c);color:#e6edf3;padding:6px 10px;
        border-radius:8px;font-size:11.5px;line-height:1.4;opacity:0;pointer-events:none;
        transition:opacity .2s}}
  .hot:hover .lab,.hot:active .lab{{opacity:1}}
  #rv{{display:none}}
  #rv:checked ~ .wrap .hot{{opacity:.85;background:rgba(13,17,23,.6);border-color:var(--c);
        box-shadow:0 0 14px 2px var(--c)}}
</style>
<input type="checkbox" id="rv">
<div class="bar">
  <label class="tog" for="rv">👁 Reveal / hide all sensors</label>
  <span>{legend}</span>
</div>
<div class="wrap">
  <img src="data:image/jpeg;base64,{b64}" alt="construction site">
  {hotspots}
</div>
"""
        st.iframe(html, height=760)
        st.caption("💡 The **helmet camera** sits on the real CCTV pole in the middle of the shot. "
                   "Tick *Reveal* to show every device at once.")

    st.subheader("Inspect a device")
    pick = st.selectbox("Choose a sensor / camera", [s[0] for s in SENSORS])
    s = next(x for x in SENSORS if x[0] == pick)
    c1, c2, c3 = st.columns(3)
    c1.metric("Live reading",
              f"{latest[s[4]]:.1f}" if s[4] and not pd.isna(latest[s[4]]) else "image frame")
    c2.metric("Feeds AI stage", s[5])
    c3.markdown(f"**What it does**\n\n{s[6]}")
    st.info({"ML": "→ Sensor numbers go to the **ANN** to predict *accident risk*.",
             "DL": "→ Raw pixels go to the **CNN** to detect a *missing helmet*.",
             "Fusion": "→ Location joins sensor-risk + helmet-check into one **site-safety** call."}[s[5]])


def render_load():
    st.title("1.0 — Load the site's sensor logs")
    st.caption("One row per shift. Red = a problem we must fix (blank, impossible value, or duplicate).")
    d = get_data()
    view = d["dirty"].head(25).copy()

    def hl(v):
        return "color:#ff6b6b;font-weight:700" if (pd.isna(v) or v in (9999, 150, -5)) else ""
    st.dataframe(view.style.map(hl, subset=FEATURES), width="stretch", height=480)
    c1, c2, c3 = st.columns(3)
    c1.metric("Shifts logged", f"{len(d['dirty']):,}")
    c2.metric("Missing readings", int(d["dirty"][FEATURES].isna().sum().sum()))
    c3.metric("Duplicate rows", int(d["dirty"].duplicated().sum()))


def render_inspect():
    st.title("1.1 — Inspect: how messy is it?")
    st.caption("Press Play to watch the damage tally up, sensor by sensor.")
    d = get_data(); dirty = d["dirty"]
    miss = dirty[FEATURES].isna().sum().values

    fig = go.Figure(go.Bar(x=NICE, y=[0] * 7, marker_color=POS))
    frames = [go.Frame(data=[go.Bar(x=NICE, y=list(miss[:k]) + [0] * (7 - k))], name=str(k))
              for k in range(8)]
    fig.update_yaxes(range=[0, max(miss) * 1.25])
    fig.update_layout(title="Missing readings per sensor (a device dropped out)")
    style(fig, 380); animate(fig, frames, ms=260)
    st.plotly_chart(fig, width="stretch")

    imp = {"gas > 1000 ppm": int((dirty.gas_ppm > 1000).sum()),
           "temp > 60 °C": int((dirty.temperature_c > 60).sum()),
           "proximity < 0 m": int((dirty.proximity_m < 0).sum())}
    c1, c2 = st.columns([2, 1])
    f2 = go.Figure(go.Bar(x=list(imp), y=list(imp.values()), marker_color=RED))
    f2.update_layout(title="Impossible values — broken hardware, not real readings")
    c1.plotly_chart(style(f2, 340), width="stretch")
    c2.metric("Duplicate rows", int(dirty.duplicated().sum()))
    c2.metric("Total missing", int(dirty[FEATURES].isna().sum().sum()))


def render_clean():
    st.title("1.2 — Clean")
    st.caption("Press Play: watch the impossible spikes get caught, then the gaps filled.")
    d = get_data()
    col = st.selectbox("Sensor to watch", FEATURES, index=0)

    raw = d["dirty"][col]
    stage1 = raw.dropna()                                    # as logged (incl. impossible spikes)
    stage2 = raw.replace([9999, 150, -5], np.nan).dropna()   # impossible -> removed
    stage3 = d["clean"][col]                                 # gaps filled with median

    steps = [("1 · As logged — note the impossible spike", stage1, RED),
             ("2 · Impossible values marked missing", stage2, AMBER),
             ("3 · Gaps filled with the median", stage3, GREEN)]
    hi = max(stage1.max(), stage3.max())
    lo = min(stage1.min(), stage3.min())

    fig = go.Figure(go.Histogram(x=stage1, marker_color=RED, nbinsx=60))
    frames = [go.Frame(data=[go.Histogram(x=s, marker_color=c, nbinsx=60)],
                       layout=go.Layout(title=t), name=str(i))
              for i, (t, s, c) in enumerate(steps)]
    fig.update_xaxes(range=[lo - abs(lo) * 0.1 - 1, hi * 1.05])
    fig.update_layout(title=steps[0][0])
    style(fig, 420); animate(fig, frames, ms=1400)
    st.plotly_chart(fig, width="stretch")

    b, a = len(d["dirty"]), len(d["clean"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", f"{b} → {a}", f"-{b-a} duplicates")
    c2.metric("Missing before", int(d["dirty"][FEATURES].isna().sum().sum()))
    c3.metric("Missing after", int(d["clean"][FEATURES].isna().sum().sum()))
    st.info("**Why the median, not the average?** The average gets dragged upward by those faulty "
            "spikes. The median — the middle value — barely notices them.")


def render_normalize():
    st.title("1.3 — Normalize")
    st.caption("Press Play: watch every sensor squash into the same 0–1 range.")
    d = get_data()
    col = st.selectbox("Sensor", FEATURES, index=0)
    raw, nrm = d["clean"][col].values, d["norm"][col].values

    fig = go.Figure(go.Histogram(x=raw, marker_color=MUTED, nbinsx=50))
    frames = []
    for k in range(13):
        t = k / 12
        x = (1 - t) * raw + t * nrm          # morph raw -> scaled
        frames.append(go.Frame(data=[go.Histogram(x=x, marker_color=POS if t > 0.5 else MUTED,
                                                  nbinsx=50)], name=str(k)))
    fig.update_xaxes(range=[min(raw.min(), 0) - 1, raw.max() * 1.05])
    fig.update_layout(title=f"{col}: raw range collapsing into 0–1")
    style(fig, 420); animate(fig, frames, ms=140)
    st.plotly_chart(fig, width="stretch")

    lo, hi = float(d["clean"][col].min()), float(d["clean"][col].max())
    v = st.slider(f"Try a raw {col} reading", lo, hi, float(d["clean"][col].median()))
    c1, c2 = st.columns(2)
    c1.metric("Raw value", f"{v:.1f}")
    c2.metric("Scaled (0–1)", f"{(v - lo) / (hi - lo + 1e-9):.3f}")


def render_split():
    st.title("1.4 — Split")
    st.caption("Press Play: the data divides into train / validation / test.")
    d = get_data()
    parts = [("Train", d["ytr"], POS), ("Validation", d["yval"], AMBER), ("Test", d["yte"], GREEN)]
    safe = [int((a == 0).sum()) for _, a, _ in parts]
    inc = [int((a == 1).sum()) for _, a, _ in parts]
    names = [n for n, _, _ in parts]

    fig = go.Figure([go.Bar(x=names, y=[0, 0, 0], name="safe", marker_color="#37474f"),
                     go.Bar(x=names, y=[0, 0, 0], name="incident", marker_color=RED)])
    frames = []
    for k in range(13):
        t = k / 12
        frames.append(go.Frame(data=[go.Bar(x=names, y=[s * t for s in safe]),
                                     go.Bar(x=names, y=[i * t for i in inc])],
                               traces=[0, 1], name=str(k)))
    fig.update_yaxes(range=[0, (max(safe) + max(inc)) * 1.15])
    fig.update_layout(barmode="stack", title="Split sizes — incident share stays proportional (stratify)")
    style(fig, 420); animate(fig, frames, ms=110)
    st.plotly_chart(fig, width="stretch")
    st.caption("Test shifts are locked away — the model never trains on them (no data leakage).")


def render_compare():
    st.title("Machine Learning vs Deep Learning")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🤖 Machine Learning")
        st.markdown("- Human **picks the features** (gas, dust…)\n- Great on **tables**\n- CPU is fine\n"
                    "- Easier to explain\n- On our site: **sensors → risk**")
    with c2:
        st.subheader("🧠 Deep Learning")
        st.markdown("- Network **learns features itself**\n- Great on **images / audio / text**\n- Wants a GPU\n"
                    "- More of a black box\n- On our site: **camera pixels → helmet**")
    st.success("The promise: on the sensor table both do well — but only DL can go from **raw pixels** "
               "to *no helmet*. We prove it in the last stage.")


def render_ml_baseline():
    st.title("ML baseline — Random Forest on the sensors")
    st.caption("Press Play: the importance of each human-named sensor fills in.")
    d = get_data(); rf, _ = get_models()
    imp = pd.Series(rf.feature_importances_, index=NICE).sort_values()

    fig = go.Figure(go.Bar(x=[0] * 7, y=imp.index, orientation="h", marker_color=POS))
    frames = [go.Frame(data=[go.Bar(x=list(imp.values[:k]) + [0] * (7 - k), y=imp.index,
                                    orientation="h")], name=str(k)) for k in range(8)]
    fig.update_xaxes(range=[0, imp.max() * 1.2])
    fig.update_layout(title="ML weights HUMAN-NAMED sensors — it can rank them, never invent one")
    style(fig, 420); animate(fig, frames, ms=240)
    st.plotly_chart(fig, width="stretch")
    st.metric("Random Forest test accuracy", f"{accuracy_score(d['yte'], rf.predict(d['Xte'])):.3f}")


def render_what_is_dl():
    st.title("What is Deep Learning? — watch every input flow through the network")
    st.caption("Press ▶ Play: all 7 sensors fan out into every neuron, each neuron sums them and fires "
               "its activation, and the patterns get deeper and more abstract at every layer.")
    d = get_data(); _, mlp = get_models()
    idx = st.slider("Pick a shift to push through the network", 0, len(d["Xte"]) - 1, 0)
    x = d["Xte"][idx]

    # real forward pass through the trained net (7 -> 8 -> 6 -> 1)
    acts, a = [x], x
    for i, (W, b) in enumerate(zip(mlp.coefs_, mlp.intercepts_)):
        z = a @ W + b
        a = np.maximum(0, z) if i < len(mlp.coefs_) - 1 else sigmoid(z)
        acts.append(a)
    sizes = [len(v) for v in acts]
    xs = np.linspace(0.07, 0.93, len(sizes))
    ys = [np.linspace(0.10, 0.90, s) for s in sizes]
    bright = []
    for v in acts:
        bright.append((v - v.min()) / (np.ptp(v) + 1e-9) if len(v) > 1 else np.array([float(v[0])]))

    DIM = "rgba(79,195,247,0.10)"
    def colors(layer, lit_upto):
        if layer <= lit_upto:
            return [f"rgba(79,195,247,{0.25 + 0.72 * v:.2f})" for v in bright[layer]]
        return [DIM] * sizes[layer]

    fig = go.Figure()
    # static edges — every input connects to every neuron in the next layer
    for li in range(len(sizes) - 1):
        W = mlp.coefs_[li]; wmax = np.abs(W).max() + 1e-9
        for i in range(sizes[li]):
            for j in range(sizes[li + 1]):
                wv = W[i, j]
                fig.add_trace(go.Scatter(
                    x=[xs[li], xs[li + 1]], y=[ys[li][i], ys[li + 1][j]], mode="lines",
                    line=dict(color=POS if wv >= 0 else NEG, width=0.4 + 1.8 * abs(wv) / wmax),
                    opacity=0.13, hoverinfo="skip", showlegend=False))
    # node traces
    node_idx = []
    for li, s in enumerate(sizes):
        fig.add_trace(go.Scatter(x=[xs[li]] * s, y=ys[li], mode="markers",
                                 marker=dict(size=20, color=colors(li, 0 if li == 0 else -1),
                                             line=dict(color=POS, width=1)),
                                 hoverinfo="skip", showlegend=False))
        node_idx.append(len(fig.data) - 1)
    # travelling pulse trace
    fig.add_trace(go.Scatter(x=[], y=[], mode="markers",
                             marker=dict(size=7, color="#ffffff"), hoverinfo="skip", showlegend=False))
    pulse_idx = len(fig.data) - 1

    STORY = [
        "① The 7 sensor readings enter — this is the raw data",
        "② Every input travels to EVERY neuron, scaled by its weight",
        "③ Each neuron sums them (Σw·x+b) and fires its ACTIVATION → simple patterns",
        "④ Layer 2 combines those into richer patterns (gas high AND worker close)",
        "⑤ The output neuron turns the deepest pattern into one risk probability",
    ]
    frames = []
    # phase 0: inputs light up
    for k in range(4):
        frames.append(go.Frame(
            data=[go.Scatter(x=[xs[li]] * sizes[li], y=ys[li], mode="markers",
                             marker=dict(size=20 + (4 if li == 0 else 0), color=colors(li, 0),
                                         line=dict(color=POS, width=1))) for li in range(len(sizes))]
                 + [go.Scatter(x=[], y=[], mode="markers", marker=dict(size=7, color="#ffffff"))],
            traces=node_idx + [pulse_idx], layout=go.Layout(title=STORY[0]), name=f"a{k}"))
    # phases: travel + activate, layer by layer
    for li in range(len(sizes) - 1):
        pairs = [(i, j) for i in range(sizes[li]) for j in range(sizes[li + 1])]
        for k in range(9):
            t = k / 8
            px = [(1 - t) * xs[li] + t * xs[li + 1]] * len(pairs)
            py = [(1 - t) * ys[li][i] + t * ys[li + 1][j] for i, j in pairs]
            frames.append(go.Frame(
                data=[go.Scatter(x=[xs[l]] * sizes[l], y=ys[l], mode="markers",
                                 marker=dict(size=20, color=colors(l, li), line=dict(color=POS, width=1)))
                      for l in range(len(sizes))]
                     + [go.Scatter(x=px, y=py, mode="markers", marker=dict(size=7, color="#ffffff"))],
                traces=node_idx + [pulse_idx],
                layout=go.Layout(title=STORY[1] if li == 0 else STORY[2 + min(li - 1, 2)]), name=f"t{li}_{k}"))
        # arrival: activation fires on the target layer
        for k in range(3):
            frames.append(go.Frame(
                data=[go.Scatter(x=[xs[l]] * sizes[l], y=ys[l], mode="markers",
                                 marker=dict(size=20 + (5 if l == li + 1 else 0), color=colors(l, li + 1),
                                             line=dict(color=POS, width=1)))
                      for l in range(len(sizes))]
                     + [go.Scatter(x=[], y=[], mode="markers", marker=dict(size=7, color="#ffffff"))],
                traces=node_idx + [pulse_idx],
                layout=go.Layout(title=STORY[2 + min(li, 2)]), name=f"f{li}_{k}"))

    depth_labels = ["Raw sensors<br><i>numbers</i>",
                    "Layer 1<br><i>simple patterns</i>",
                    "Layer 2<br><i>combined patterns</i>",
                    "Output<br><i>risk</i>"]
    for li, lab in enumerate(depth_labels[:len(sizes)]):
        fig.add_annotation(x=xs[li], y=1.0, text=lab, showarrow=False,
                           font=dict(color=MUTED, size=11), align="center")
    fig.add_annotation(x=0.5, y=-0.06, text="deeper  →  more abstract patterns",
                       showarrow=False, font=dict(color=AMBER, size=12))
    fig.update_xaxes(visible=False, range=[0, 1])
    fig.update_yaxes(visible=False, range=[-0.10, 1.06])
    fig.update_layout(title=STORY[0])
    style(fig, 520); animate(fig, frames, ms=110)
    st.plotly_chart(fig, width="stretch")

    c1, c2, c3 = st.columns(3)
    c1.metric("Inputs entering", f"{sizes[0]} sensors")
    c2.metric("Connections carrying signal", f"{sum(sizes[i]*sizes[i+1] for i in range(len(sizes)-1))}")
    c3.metric("Final risk output", f"{float(acts[-1][0]):.3f}")

    st.markdown("#### Why depth = recognising deeper patterns")
    a, b = st.columns(2)
    a.markdown(
        "**On our sensors (this ANN)**\n\n"
        "- **Layer 1** reacts to *one thing at a time* — “is gas high?”, “is the jolt big?”\n"
        "- **Layer 2** combines layer 1's answers — “gas high **AND** worker close **AND** a jolt”\n"
        "- **Output** turns that deep pattern into a single risk probability")
    b.markdown(
        "**On the camera (the CNN, stage 6)**\n\n"
        "- **Early layers** → **edges** (the rim of a helmet)\n"
        "- **Middle layers** → **parts** (the curved shell, a strap)\n"
        "- **Deep layers** → **the whole concept** — “helmet”\n\n"
        "Same principle, different data. *Nobody programmed any of these patterns.*")
    st.info("**The loop that learns them:** forward pass → loss (how wrong) → backpropagation "
            "(who caused the error) → nudge every weight → repeat thousands of times.")


def render_neuron():
    st.title("A single neuron — drag the weights, press Play to watch it fire")
    d = get_data()
    idx = st.slider("Pick a shift (its 7 sensor readings feed the neuron)", 0, len(d["Xtr"]) - 1, 0)
    x = d["Xtr"][idx]
    cols = st.columns(7)
    w = np.array([cols[i].slider(NICE[i], -1.5, 1.5, [0.9, 0.6, 0.7, 0.1, 0.8, -0.9, 0.5][i], 0.1)
                  for i in range(7)])
    b = st.slider("Bias  b", -2.0, 2.0, -0.5, 0.1)
    z = float(np.dot(w, x) + b); out = float(sigmoid(z))

    ys = np.linspace(0.05, 0.95, 7)
    fig = go.Figure()
    wmax = max(abs(w).max(), 1e-6)
    for i in range(7):
        c = POS if w[i] >= 0 else NEG
        fig.add_trace(go.Scatter(x=[0.05, 0.5], y=[ys[i], 0.5], mode="lines",
                                 line=dict(color=c, width=1 + 6 * abs(w[i]) / wmax),
                                 opacity=0.65, hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=[0.05] * 7, y=ys, mode="markers+text",
                             marker=dict(size=26, color=PANEL, line=dict(color=POS, width=2)),
                             text=[f"{v:.2f}" for v in x], textposition="middle left",
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=[0.5], y=[0.5], mode="markers+text",
                             marker=dict(size=70, color=f"rgba(79,195,247,{0.25 + 0.6 * out:.2f})",
                                         line=dict(color=POS, width=2)),
                             text=[f"Σ+b<br>{z:.2f}"], textfont=dict(color=TEXT),
                             hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=[0.5, 0.9], y=[0.5, 0.5], mode="lines",
                             line=dict(color=GREEN, width=3), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[0.9], y=[0.5], mode="markers+text",
                             marker=dict(size=46, color=f"rgba(102,187,106,{0.3 + 0.6 * out:.2f})",
                                         line=dict(color=GREEN, width=2)),
                             text=[f"{out:.2f}"], textfont=dict(color=TEXT),
                             hoverinfo="skip", showlegend=False))
    # travelling signal pulse
    fig.add_trace(go.Scatter(x=[0.05] * 7, y=ys, mode="markers",
                             marker=dict(size=11, color="#ffffff"), hoverinfo="skip", showlegend=False))
    pulse = len(fig.data) - 1
    frames = []
    for k in range(21):
        t = k / 20
        if t <= 0.75:                       # inputs -> neuron body
            tt = t / 0.75
            px = (1 - tt) * 0.05 + tt * 0.5
            fx = [px] * 7
            fy = [(1 - tt) * yv + tt * 0.5 for yv in ys]
        else:                               # neuron -> output
            tt = (t - 0.75) / 0.25
            fx = [(1 - tt) * 0.5 + tt * 0.9] * 7
            fy = [0.5] * 7
        frames.append(go.Frame(data=[go.Scatter(x=fx, y=fy, mode="markers",
                                                marker=dict(size=11, color="#ffffff"))],
                               traces=[pulse], name=str(k)))
    fig.update_xaxes(visible=False, range=[-0.1, 1.05])
    fig.update_yaxes(visible=False, range=[0, 1])
    style(fig, 460); animate(fig, frames, ms=70)
    st.plotly_chart(fig, width="stretch")
    c1, c2, c3 = st.columns(3)
    c1.metric("Weighted sum  z = Σ(w·x)+b", f"{z:.3f}")
    c2.metric("Activation  sigmoid(z)", f"{out:.3f}")
    c3.metric("Neuron says", "⚠️ RISK" if out > 0.5 else "✅ SAFE")


def render_activation():
    st.title("Activation functions")
    z = np.linspace(-6, 6, 300)
    funcs = {"Sigmoid": sigmoid(z), "Tanh": np.tanh(z),
             "ReLU": np.maximum(0, z), "Leaky ReLU": np.where(z > 0, z, 0.1 * z)}
    pick = st.selectbox("Function", list(funcs))
    curve = funcs[pick]
    zval = st.slider("Weighted sum z", -6.0, 6.0, 1.0, 0.1)
    yval = float(np.interp(zval, z, curve))

    fig = go.Figure(go.Scatter(x=z, y=curve, mode="lines", line=dict(color=POS, width=3), name=pick))
    fig.add_trace(go.Scatter(x=[zval], y=[yval], mode="markers",
                             marker=dict(size=15, color=AMBER), showlegend=False))
    frames = [go.Frame(data=[go.Scatter(x=[zz], y=[float(np.interp(zz, z, curve))], mode="markers",
                                        marker=dict(size=15, color=AMBER))],
                       traces=[1], name=str(k)) for k, zz in enumerate(np.linspace(-6, 6, 40))]
    fig.update_layout(title=f"{pick}(z) = {yval:.3f} at z = {zval:.1f}")
    style(fig, 420); animate(fig, frames, ms=70)
    st.plotly_chart(fig, width="stretch")
    st.info({"Sigmoid": "0–1 output → final layer of a yes/no model (our risk output).",
             "Tanh": "−1…1, zero-centred → older hidden layers.",
             "ReLU": "Fast, avoids vanishing gradients → the default for hidden layers.",
             "Leaky ReLU": "Fixes 'dying ReLU' — keeps a small slope for negatives."}[pick])

    st.markdown("#### Which activation is actually best for **our site**?")
    st.caption("Not an opinion — we retrain the same ANN on the same shifts, changing only the activation.")
    d = get_data()
    rows = []
    for a, label in [("relu", "ReLU"), ("tanh", "Tanh"), ("logistic", "Sigmoid")]:
        m = train_arch((8, 6), activation=a)
        rows.append((label, accuracy_score(d["yte"], m.predict(d["Xte"])), len(m.loss_curve_)))
    best = max(rows, key=lambda r: r[1])[0]
    fig2 = go.Figure(go.Bar(x=[r[0] for r in rows], y=[r[1] for r in rows],
                            marker_color=[GREEN if r[0] == best else POS for r in rows],
                            text=[f"{r[1]:.3f}" for r in rows], textposition="outside"))
    fig2.update_yaxes(range=[0.5, 1.02])
    fig2.update_layout(title="Test accuracy on unseen shifts — hidden-layer activation swapped")
    st.plotly_chart(style(fig2, 380), width="stretch")
    st.success(f"**Winner on our data: {best}.** ReLU keeps gradients healthy so the network actually learns "
               "the 'gas high AND worker close' combinations. Tanh and Sigmoid squash their gradients toward "
               "zero in the hidden layers, so learning crawls. But note the **output** stays Sigmoid — we need "
               "a 0–1 probability of an incident, and only Sigmoid gives us that.")


def render_loss():
    st.title("Loss function — how wrong were we?")
    truth = st.radio("What actually happened this shift?", ["Incident (1)", "Safe (0)"], horizontal=True)
    yt = 1 if truth.startswith("Incident") else 0
    p = st.slider("Model's predicted probability of risk", 0.01, 0.99, 0.3, 0.01)
    loss = float(-(yt * np.log(p) + (1 - yt) * np.log(1 - p)))
    st.metric("Cross-entropy loss", f"{loss:.3f}")

    ps = np.linspace(0.01, 0.99, 200)
    curve = -(yt * np.log(ps) + (1 - yt) * np.log(1 - ps))
    fig = go.Figure(go.Scatter(x=ps, y=curve, mode="lines", line=dict(color=POS, width=3)))
    fig.add_trace(go.Scatter(x=[p], y=[loss], mode="markers",
                             marker=dict(size=15, color=AMBER), showlegend=False))
    frames = [go.Frame(data=[go.Scatter(x=[pp], y=[float(-(yt * np.log(pp) + (1 - yt) * np.log(1 - pp)))],
                                        mode="markers", marker=dict(size=15, color=AMBER))],
                       traces=[1], name=str(k)) for k, pp in enumerate(np.linspace(0.01, 0.99, 40))]
    fig.update_layout(title=f"Loss vs prediction (truth = {yt}) — confident AND wrong is punished hardest")
    style(fig, 420); animate(fig, frames, ms=70)
    st.plotly_chart(fig, width="stretch")

    st.markdown("#### Why cross-entropy and not MSE for **our site**?")
    st.caption("Same situation, two different loss functions. Watch how differently they punish a mistake.")
    bce = -(1 * np.log(ps))
    mse = (1 - ps) ** 2
    f2 = go.Figure()
    f2.add_trace(go.Scatter(x=ps, y=bce, mode="lines", name="Binary cross-entropy (ours)",
                            line=dict(color=GREEN, width=3)))
    f2.add_trace(go.Scatter(x=ps, y=mse, mode="lines", name="Mean squared error",
                            line=dict(color=AMBER, width=3, dash="dash")))
    f2.update_yaxes(range=[0, 5])
    f2.update_layout(title="An incident really happened (truth = 1). How badly is each wrong answer punished?",
                     xaxis_title="predicted probability of risk", yaxis_title="loss",
                     legend=dict(orientation="h", y=1.12, x=0))
    st.plotly_chart(style(f2, 400), width="stretch")
    c1, c2 = st.columns(2)
    c1.metric("Model says 1% risk, incident happened → BCE", f"{-np.log(0.01):.2f}")
    c2.metric("…same mistake → MSE", f"{(1 - 0.01) ** 2:.2f}")
    st.success("**Cross-entropy is the right choice for a safety system.** Look at the far left: the model "
               "confidently said *1% risk* on a shift that genuinely injured someone. MSE shrugs — its loss "
               "maxes out at 1.0, no matter how wrong. Cross-entropy explodes to 4.6 and keeps climbing toward "
               "infinity. That steepness is what forces the network to take a missed accident seriously. MSE is "
               "for predicting *quantities* — like the exact gas concentration. Cross-entropy is for "
               "*yes-or-no* calls — like whether this shift is about to go wrong.")


def _valley():
    w = np.linspace(-6, 10, 200)
    return w, (w - 2.0) ** 2 + 1


def _descend(lr, start=-4.0, steps=20):
    w, path = start, [start]
    for _ in range(steps):
        w -= lr * 2 * (w - 2.0); path.append(w)
    return np.array(path)


def render_gradient_descent():
    st.title("Gradient descent — watch the ball roll downhill")
    lr = st.slider("Learning rate (step size)", 0.01, 1.2, 0.1, 0.01)
    ws, ls = _valley()
    path = _descend(lr, steps=25)
    py = (path - 2) ** 2 + 1

    fig = go.Figure(go.Scatter(x=ws, y=ls, mode="lines", line=dict(color=MUTED, width=2), name="loss"))
    fig.add_trace(go.Scatter(x=path[:1], y=py[:1], mode="lines",
                             line=dict(color=POS, width=2), name="path"))
    fig.add_trace(go.Scatter(x=[path[0]], y=[py[0]], mode="markers",
                             marker=dict(size=18, color=AMBER, line=dict(color="#fff", width=1)), name="weights"))
    frames = [go.Frame(data=[go.Scatter(x=path[:k + 1], y=py[:k + 1]),
                             go.Scatter(x=[path[k]], y=[py[k]])],
                       traces=[1, 2], name=str(k)) for k in range(len(path))]
    fig.update_layout(title=f"Learning rate {lr} → settles at w ≈ {path[-1]:.2f}  (best = 2.0)")
    style(fig, 440); animate(fig, frames, ms=220)
    st.plotly_chart(fig, width="stretch")
    st.caption("The gradient points uphill — we step the opposite way. Each step = fewer wrong safety calls.")


def render_learning_rate():
    st.title("Learning rate — too low, just right, too high")
    st.caption("Press Play: three balls, same valley, three learning rates.")
    ws, ls = _valley()
    regimes = [("Too low (0.01) — crawls", 0.01, RED),
               ("Just right (0.10) — converges", 0.10, GREEN),
               ("Too high (1.05) — overshoots", 1.05, AMBER)]
    paths = [(_descend(lr, steps=25), c, n) for n, lr, c in regimes]

    fig = go.Figure(go.Scatter(x=ws, y=ls, mode="lines", line=dict(color=MUTED, width=2), showlegend=False))
    ball_idx = []
    for p, c, n in paths:
        fig.add_trace(go.Scatter(x=[p[0]], y=[(p[0] - 2) ** 2 + 1], mode="markers",
                                 marker=dict(size=15, color=c), name=n))
        ball_idx.append(len(fig.data) - 1)
    frames = []
    for k in range(25):
        data = [go.Scatter(x=[p[k]], y=[(p[k] - 2) ** 2 + 1], mode="markers",
                           marker=dict(size=15, color=c)) for p, c, _ in paths]
        frames.append(go.Frame(data=data, traces=ball_idx, name=str(k)))
    fig.update_yaxes(range=[0, 60])
    fig.update_layout(title="Same valley, three learning rates",
                      legend=dict(orientation="h", y=1.12, x=0))
    style(fig, 460); animate(fig, frames, ms=260)
    st.plotly_chart(fig, width="stretch")

    st.markdown("#### Which learning rate is actually best for **our site**?")
    st.caption("The valley above is a toy. Here is the real ANN, retrained on the real shifts, at four rates.")
    d = get_data()
    f2 = go.Figure()
    res = []
    for lr, c in [(0.0001, RED), (0.001, GREEN), (0.01, POS), (0.1, AMBER)]:
        m = train_arch((8, 6), lr=lr)
        f2.add_trace(go.Scatter(y=m.loss_curve_, mode="lines", name=f"lr={lr}", line=dict(color=c, width=3)))
        res.append((lr, accuracy_score(d["yte"], m.predict(d["Xte"]))))
    f2.update_layout(title="Real training loss at four learning rates", xaxis_title="epoch", yaxis_title="loss")
    st.plotly_chart(style(f2, 400), width="stretch")
    cols = st.columns(len(res))
    for c, (lr, acc) in zip(cols, res):
        c.metric(f"lr = {lr}", f"{acc:.3f}")
    st.success("**0.001 is our pick** — Adam's default, and you can see why. At 0.0001 the loss barely moves; "
               "the model would need a huge number of epochs just to learn that high gas plus close proximity "
               "means danger. At 0.1 the steps are so violent the loss jumps around and never settles into a "
               "reliable risk detector. 0.001 drops fast and stays down.")


def render_optimizer():
    st.title("Optimizers — the race to the bottom")
    st.caption("Press Play: SGD vs Momentum vs RMSprop vs Adam, same valley.")
    ws, ls = _valley()

    def run(kind, lr=0.12, steps=25):
        w, v, cache, path = -4.0, 0.0, 0.0, [-4.0]
        for _ in range(steps):
            g = 2 * (w - 2.0)
            if kind == "SGD":
                w -= lr * g
            elif kind == "Momentum":
                v = 0.8 * v - lr * g; w += v
            elif kind == "RMSprop":
                cache = 0.9 * cache + 0.1 * g * g; w -= lr * g / (np.sqrt(cache) + 1e-8)
            else:
                v = 0.9 * v + 0.1 * g; cache = 0.999 * cache + 0.001 * g * g
                w -= lr * v / (np.sqrt(cache) + 1e-8)
            path.append(w)
        return np.array(path)

    runs = [(k, run(k), c) for k, c in
            [("SGD", MUTED), ("Momentum", POS), ("RMSprop", AMBER), ("Adam", GREEN)]]
    fig = go.Figure(go.Scatter(x=ws, y=ls, mode="lines", line=dict(color="#3d4653", width=2), showlegend=False))
    idx = []
    for k, p, c in runs:
        fig.add_trace(go.Scatter(x=[p[0]], y=[(p[0] - 2) ** 2 + 1], mode="markers",
                                 marker=dict(size=15, color=c), name=k))
        idx.append(len(fig.data) - 1)
    frames = [go.Frame(data=[go.Scatter(x=[p[j]], y=[(p[j] - 2) ** 2 + 1], mode="markers",
                                        marker=dict(size=15, color=c)) for _k, p, c in runs],
                       traces=idx, name=str(j)) for j in range(26)]
    fig.update_layout(title="Adam gets there fastest and steadiest",
                      legend=dict(orientation="h", y=1.12, x=0))
    style(fig, 460); animate(fig, frames, ms=240)
    st.plotly_chart(fig, width="stretch")
    st.success("Adam = Momentum + RMSprop — adaptive and smooth. That's why the ANN uses it.")

    st.markdown("#### Which optimizer is actually best for **our site**?")
    st.caption("Same ANN, same shifts — only the optimizer changes. This is the real training loss.")
    d = get_data()
    f2 = go.Figure()
    res = []
    for solver, c in [("adam", GREEN), ("sgd", AMBER)]:
        m = train_arch((8, 6), solver=solver)
        f2.add_trace(go.Scatter(y=m.loss_curve_, mode="lines", name=solver.upper(),
                                line=dict(color=c, width=3)))
        res.append((solver.upper(), accuracy_score(d["yte"], m.predict(d["Xte"])), len(m.loss_curve_)))
    f2.update_layout(title="Real training loss on the site's sensor data",
                     xaxis_title="epoch", yaxis_title="loss")
    st.plotly_chart(style(f2, 400), width="stretch")
    cols = st.columns(len(res))
    for c, (n, acc, ep) in zip(cols, res):
        c.metric(f"{n} accuracy", f"{acc:.3f}", f"{ep} epochs")
    st.success("**Adam wins on our data** — it drops the loss faster and settles lower, without us hand-tuning "
               "anything. Our sensor signals are noisy (a jolt here, a gas spike there), and Adam's per-weight "
               "adaptive steps ride straight through that noise. Plain SGD uses one step size for every weight, "
               "so it takes far longer to find the same danger patterns.")


def render_network():
    st.title("The ANN — every sensor number flows into every neuron")
    st.caption("Change the architecture, then press ▶ Play to watch each layer deduce more than the last.")
    d = get_data()

    c1, c2, c3 = st.columns(3)
    n_layers = c1.slider("Hidden layers (depth)", 1, 3, 2)
    n_neurons = c2.slider("Neurons per hidden layer (width)", 2, 10, 8)
    idx = c3.slider("Shift to push through", 0, len(d["Xte"]) - 1, 0)
    hidden = tuple([n_neurons] * n_layers)
    mlp = train_arch(hidden)
    x = d["Xte"][idx]
    raw = d["scaler"].inverse_transform(x.reshape(1, -1))[0]

    # ---- 1. the numeric inputs, named ----
    st.markdown("#### 1 · The numeric inputs — this shift's real sensor readings")
    st.dataframe(pd.DataFrame({
        "Sensor (input name)": NICE,
        "Raw reading (real units)": [f"{v:.1f}" for v in raw],
        "Normalized input x": [f"{v:.3f}" for v in x],
    }), width="stretch", hide_index=True, height=280)
    st.caption("Every one of these 7 numbers is sent to **every** neuron in the first hidden layer.")

    # ---- real forward + backward pass ----
    y_true = float(d["yte"][idx])
    zs, acts, deltas, dW, db = backprop(mlp, x, y_true)
    sizes = [len(v) for v in acts]
    xs = np.linspace(0.07, 0.93, len(sizes))
    ys = [np.linspace(0.10, 0.90, s) for s in sizes]
    bright = [((v - v.min()) / (np.ptp(v) + 1e-9) if len(v) > 1 else np.array([float(v[0])])) for v in acts]

    DIM = "rgba(79,195,247,0.10)"
    def colors(l, lit):
        return ([f"rgba(79,195,247,{0.25 + 0.72 * v:.2f})" for v in bright[l]]
                if l <= lit else [DIM] * sizes[l])

    # ---- 2. INSIDE one neuron ----
    st.markdown("#### 2 · Inside ONE neuron — the arithmetic nobody shows you")
    st.caption("This is the whole mystery, and it is just multiply, add, then bend. Press ▶ Play to watch "
               "one sensor arrive at a time and push the running total around.")
    jn = st.slider("Which neuron in hidden layer 1?", 1, sizes[1], 1) - 1
    Wj, bj = mlp.coefs_[0][:, jn], mlp.intercepts_[0][jn]
    contrib = x * Wj
    labels = NICE + ["bias b"]
    vals = list(contrib) + [float(bj)]
    z_j, a_j = float(zs[0][jn]), float(acts[1][jn])

    figN = go.Figure(go.Bar(x=[0] * len(vals), y=labels, orientation="h",
                            marker_color=[POS if v >= 0 else NEG for v in vals],
                            text=[""] * len(vals), textposition="outside"))
    framesN = []
    for k in range(len(vals) + 1):
        shown = vals[:k] + [0] * (len(vals) - k)
        run = sum(vals[:k])
        txt = [f"{v:+.2f}" if i < k else "" for i, v in enumerate(vals)]
        if k == 0:
            t = "Neuron starts at zero. Nothing has arrived yet."
        elif k <= len(NICE):
            t = (f"{NICE[k-1]}:  x={x[k-1]:.2f} × w={Wj[k-1]:+.2f} = {vals[k-1]:+.2f}   "
                 f"→  running total z = {run:+.2f}")
        else:
            t = f"+ bias b = {bj:+.2f}   →  final z = {run:+.2f}"
        framesN.append(go.Frame(data=[go.Bar(x=shown, y=labels, orientation="h",
                                             marker_color=[POS if v >= 0 else NEG for v in vals],
                                             text=txt, textposition="outside")],
                                layout=go.Layout(title=t), name=str(k)))
    lim = max(abs(min(vals)), abs(max(vals))) * 1.6 + 0.1
    figN.update_xaxes(range=[-lim, lim], title="each sensor's contribution  w·x")
    figN.update_layout(title="Neuron starts at zero. Nothing has arrived yet.")
    style(figN, 420); animate(figN, framesN, ms=900)
    st.plotly_chart(figN, width="stretch")

    k1, k2, k3 = st.columns(3)
    k1.metric("z = Σ(w·x) + b", f"{z_j:+.3f}")
    k2.metric("activation used", "ReLU  →  max(0, z)")
    k3.metric("neuron output a", f"{a_j:.3f}", "fired ✅" if a_j > 0 else "silent — ReLU zeroed it")
    st.info("**That is the entire neuron.** Multiply each incoming number by a weight, add them all up, "
            "add the bias, push the total through one simple function. No thinking, no understanding — "
            "arithmetic. A network is just *millions* of this, wired together.")

    # ---- 3. forward propagation ----
    st.markdown("#### 3 · Forward propagation — all neurons at once")
    fig = go.Figure()
    for li in range(len(sizes) - 1):
        W = mlp.coefs_[li]; wmax = np.abs(W).max() + 1e-9
        for i in range(sizes[li]):
            for j in range(sizes[li + 1]):
                wv = W[i, j]
                fig.add_trace(go.Scatter(x=[xs[li], xs[li + 1]], y=[ys[li][i], ys[li + 1][j]],
                                         mode="lines", line=dict(color=POS if wv >= 0 else NEG,
                                                                 width=0.4 + 1.8 * abs(wv) / wmax),
                                         opacity=0.13, hoverinfo="skip", showlegend=False))
    node_idx = []
    for li, s in enumerate(sizes):
        fig.add_trace(go.Scatter(x=[xs[li]] * s, y=ys[li], mode="markers",
                                 marker=dict(size=20, color=colors(li, 0 if li == 0 else -1),
                                             line=dict(color=POS, width=1)),
                                 hoverinfo="skip", showlegend=False))
        node_idx.append(len(fig.data) - 1)
    fig.add_trace(go.Scatter(x=[], y=[], mode="markers", marker=dict(size=7, color="#fff"),
                             hoverinfo="skip", showlegend=False))
    pulse = len(fig.data) - 1

    def layer_story(li):
        if li == 0:
            return "Layer 1: each neuron does Σ(w·x)+b on ALL 7 sensors → ReLU → simple patterns"
        if li == len(sizes) - 2:
            return "Output: Σ(w·x)+b on the deepest patterns → Sigmoid → one risk probability"
        return f"Layer {li+1}: sums layer {li}'s answers → ReLU → richer combined patterns"

    frames = []
    for k in range(3):
        frames.append(go.Frame(
            data=[go.Scatter(x=[xs[l]] * sizes[l], y=ys[l], mode="markers",
                             marker=dict(size=20, color=colors(l, 0), line=dict(color=POS, width=1)))
                  for l in range(len(sizes))]
                 + [go.Scatter(x=[], y=[], mode="markers", marker=dict(size=7, color="#fff"))],
            traces=node_idx + [pulse],
            layout=go.Layout(title="The 7 numeric sensor readings enter"), name=f"a{k}"))
    for li in range(len(sizes) - 1):
        pairs = [(i, j) for i in range(sizes[li]) for j in range(sizes[li + 1])]
        for k in range(9):
            t = k / 8
            px = [(1 - t) * xs[li] + t * xs[li + 1]] * len(pairs)
            py = [(1 - t) * ys[li][i] + t * ys[li + 1][j] for i, j in pairs]
            frames.append(go.Frame(
                data=[go.Scatter(x=[xs[l]] * sizes[l], y=ys[l], mode="markers",
                                 marker=dict(size=20, color=colors(l, li), line=dict(color=POS, width=1)))
                      for l in range(len(sizes))]
                     + [go.Scatter(x=px, y=py, mode="markers", marker=dict(size=7, color="#fff"))],
                traces=node_idx + [pulse], layout=go.Layout(title=layer_story(li)), name=f"t{li}_{k}"))
        for k in range(3):
            frames.append(go.Frame(
                data=[go.Scatter(x=[xs[l]] * sizes[l], y=ys[l], mode="markers",
                                 marker=dict(size=20 + (5 if l == li + 1 else 0), color=colors(l, li + 1),
                                             line=dict(color=POS, width=1)))
                      for l in range(len(sizes))]
                     + [go.Scatter(x=[], y=[], mode="markers", marker=dict(size=7, color="#fff"))],
                traces=node_idx + [pulse], layout=go.Layout(title=layer_story(li)), name=f"f{li}_{k}"))

    labs = ["Sensors"] + [f"Hidden {i+1}" for i in range(n_layers)] + ["Risk"]
    for li, lab in enumerate(labs[:len(sizes)]):
        fig.add_annotation(x=xs[li], y=1.0, text=lab, showarrow=False, font=dict(color=MUTED, size=11))
    fig.add_annotation(x=0.5, y=-0.07, text="deeper  →  more deduction", showarrow=False,
                       font=dict(color=AMBER, size=12))
    fig.update_xaxes(visible=False, range=[0, 1])
    fig.update_yaxes(visible=False, range=[-0.11, 1.06])
    fig.update_layout(title="The 7 numeric sensor readings enter")
    style(fig, 500); animate(fig, frames, ms=110)
    st.plotly_chart(fig, width="stretch")

    # ---- 4. BACKPROPAGATION ----
    st.markdown("#### 4 · Backpropagation — the error walks backwards")
    pred, truth = float(acts[-1][0]), y_true
    err = pred - truth
    b1, b2, b3 = st.columns(3)
    b1.metric("Network predicted", f"{pred:.3f}")
    b2.metric("What actually happened", "incident (1)" if truth == 1 else "safe (0)")
    b3.metric("Error  (a − y)", f"{err:+.3f}", "too confident" if abs(err) > 0.5 else "close")
    st.caption("Backprop asks one question, layer by layer, from right to left: "
               "**how much did each weight contribute to that error?** The answer is the chain rule — "
               "nothing more mystical than that.")

    xsb = np.linspace(0.07, 0.93, len(sizes))
    ysb = [np.linspace(0.10, 0.90, s) for s in sizes]
    # error signal magnitude per layer (real deltas)
    dmag = []
    for i in range(len(sizes)):
        if i == 0:
            g = np.abs(deltas[0] @ mlp.coefs_[0].T)     # error reaching the inputs
        else:
            g = np.abs(deltas[i - 1])
        dmag.append(g / (g.max() + 1e-12))

    figB = go.Figure()
    for li in range(len(sizes) - 1):
        for i in range(sizes[li]):
            for j in range(sizes[li + 1]):
                figB.add_trace(go.Scatter(x=[xsb[li], xsb[li + 1]], y=[ysb[li][i], ysb[li + 1][j]],
                                          mode="lines", line=dict(color="#ff8a65", width=0.5),
                                          opacity=0.10, hoverinfo="skip", showlegend=False))
    nidx = []
    for li, s in enumerate(sizes):
        figB.add_trace(go.Scatter(x=[xsb[li]] * s, y=ysb[li], mode="markers",
                                  marker=dict(size=20, color=["rgba(255,138,101,0.10)"] * s,
                                              line=dict(color=NEG, width=1)),
                                  hoverinfo="skip", showlegend=False))
        nidx.append(len(figB.data) - 1)
    figB.add_trace(go.Scatter(x=[], y=[], mode="markers", marker=dict(size=7, color="#ffd54f"),
                              hoverinfo="skip", showlegend=False))
    pidx = len(figB.data) - 1

    def bcol(l, lit_from):
        return ([f"rgba(255,138,101,{0.22 + 0.75 * v:.2f})" for v in dmag[l]]
                if l >= lit_from else ["rgba(255,138,101,0.10)"] * sizes[l])

    STORYB = ["① The output was wrong by {:+.3f} — that error is the seed".format(err),
              "② Chain rule: how much did each hidden neuron contribute to that error?",
              "③ Same question again, one layer further back",
              "④ Every weight now knows its share of the blame → nudge it downhill"]
    framesB = []
    last = len(sizes) - 1
    for k in range(3):
        framesB.append(go.Frame(
            data=[go.Scatter(x=[xsb[l]] * sizes[l], y=ysb[l], mode="markers",
                             marker=dict(size=20 + (6 if l == last else 0), color=bcol(l, last),
                                         line=dict(color=NEG, width=1))) for l in range(len(sizes))]
                 + [go.Scatter(x=[], y=[], mode="markers", marker=dict(size=7, color="#ffd54f"))],
            traces=nidx + [pidx], layout=go.Layout(title=STORYB[0]), name=f"b{k}"))
    for step, li in enumerate(range(len(sizes) - 1, 0, -1)):
        pairs = [(i, j) for i in range(sizes[li]) for j in range(sizes[li - 1])]
        for k in range(9):
            t = k / 8
            px = [(1 - t) * xsb[li] + t * xsb[li - 1]] * len(pairs)
            py = [(1 - t) * ysb[li][i] + t * ysb[li - 1][j] for i, j in pairs]
            framesB.append(go.Frame(
                data=[go.Scatter(x=[xsb[l]] * sizes[l], y=ysb[l], mode="markers",
                                 marker=dict(size=20, color=bcol(l, li), line=dict(color=NEG, width=1)))
                      for l in range(len(sizes))]
                     + [go.Scatter(x=px, y=py, mode="markers", marker=dict(size=7, color="#ffd54f"))],
                traces=nidx + [pidx],
                layout=go.Layout(title=STORYB[min(step + 1, 2)]), name=f"bt{li}_{k}"))
        for k in range(2):
            framesB.append(go.Frame(
                data=[go.Scatter(x=[xsb[l]] * sizes[l], y=ysb[l], mode="markers",
                                 marker=dict(size=20 + (6 if l == li - 1 else 0), color=bcol(l, li - 1),
                                             line=dict(color=NEG, width=1))) for l in range(len(sizes))]
                     + [go.Scatter(x=[], y=[], mode="markers", marker=dict(size=7, color="#ffd54f"))],
                traces=nidx + [pidx], layout=go.Layout(title=STORYB[min(step + 1, 3)]), name=f"bf{li}_{k}"))
    labsb = ["Sensors"] + [f"Hidden {i+1}" for i in range(n_layers)] + ["Risk"]
    for li, lab in enumerate(labsb[:len(sizes)]):
        figB.add_annotation(x=xsb[li], y=1.0, text=lab, showarrow=False, font=dict(color=MUTED, size=11))
    figB.add_annotation(x=0.5, y=-0.07, text="←  error flows backwards  ←", showarrow=False,
                        font=dict(color=NEG, size=12))
    figB.update_xaxes(visible=False, range=[0, 1])
    figB.update_yaxes(visible=False, range=[-0.11, 1.06])
    figB.update_layout(title=STORYB[0])
    style(figB, 500); animate(figB, framesB, ms=110)
    st.plotly_chart(figB, width="stretch")

    st.markdown("**The actual weight updates** (layer 1, neuron {}) — gradient × learning rate:".format(jn + 1))
    upd = pd.DataFrame({
        "Weight (from)": NICE,
        "current w": [f"{v:+.4f}" for v in mlp.coefs_[0][:, jn]],
        "gradient ∂Loss/∂w": [f"{v:+.5f}" for v in dW[0][:, jn]],
        "change = −lr × grad": [f"{-0.001 * v:+.6f}" for v in dW[0][:, jn]],
        "new w": [f"{v - 0.001 * g:+.4f}" for v, g in zip(mlp.coefs_[0][:, jn], dW[0][:, jn])],
    })
    st.dataframe(upd, width="stretch", hide_index=True)
    st.info("**That is learning.** Each weight moves a *tiny* fraction against its own gradient. "
            "Repeat over thousands of shifts and those tiny nudges become a working risk detector. "
            "No insight, no intuition — just this table, millions of times.")

    # ---- 4b. backprop CREATES the features ----
    st.markdown("#### 4b · Watch backprop **build** the features out of random noise")
    st.caption("This is the whole point. We start a fresh network with **random** weights — it knows nothing. "
               "Then we let backprop run and snapshot layer 1 after every epoch. Press ▶ Play.")
    snaps, losses, eps = feature_emergence(hidden=(8, 6))
    zmax = max(np.abs(s).max() for s in snaps)
    figE = go.Figure(go.Heatmap(z=snaps[0].T, x=NICE, y=[f"n{i+1}" for i in range(snaps[0].shape[1])],
                                colorscale="RdBu", zmid=0, zmin=-zmax, zmax=zmax,
                                colorbar=dict(title="weight")))
    framesE = [go.Frame(data=[go.Heatmap(z=s.T, x=NICE, y=[f"n{i+1}" for i in range(s.shape[1])],
                                         colorscale="RdBu", zmid=0, zmin=-zmax, zmax=zmax)],
                        layout=go.Layout(title=f"epoch {e} — loss {l:.4f}"), name=str(k))
               for k, (s, l, e) in enumerate(zip(snaps, losses, eps))]
    figE.update_layout(title=f"epoch {eps[0]} — loss {losses[0]:.4f}  (random noise: it knows nothing yet)")
    style(figE, 420); animate(figE, framesE, ms=240)
    st.plotly_chart(figE, width="stretch")
    e1, e2 = st.columns(2)
    e1.metric("Loss at epoch 0 (random)", f"{losses[0]:.4f}")
    e2.metric(f"Loss at epoch {eps[-1]} (trained)", f"{losses[-1]:.4f}",
              f"{losses[-1]-losses[0]:+.4f}")
    st.success("**Nobody drew that pattern.** At epoch 0 the grid is random static — neuron 3 has no opinion "
               "about gas. By the end, columns have gone strongly red or blue: neurons have *become* "
               "detectors — 'this one watches gas and proximity', 'that one watches the jolt'. "
               "Backprop carved every one of those out of noise, using nothing but the error signal. "
               "**That is how a network comes to 'understand' anything: it doesn't. It gets shaped.**")

    # ---- 5. what each layer deduced ----
    st.markdown("#### 5 · What each layer actually deduced")
    st.caption("`z = Σ(wᵢ·xᵢ) + b` — the **weights** say how much to trust each incoming signal, "
               "the **bias** shifts the firing threshold so the neuron can say *'only when it's really high'*.")

    def deduce(li):
        W, b = mlp.coefs_[li], mlp.intercepts_[li]
        src = acts[li]
        names = NICE if li == 0 else [f"L{li}·n{k+1}" for k in range(len(src))]
        rows = []
        for j in range(W.shape[1]):
            contrib = W[:, j] * src
            top = np.argsort(-np.abs(contrib))[:2]
            drivers = ", ".join(
                f"{names[o]} ({'+' if contrib[o] >= 0 else '−'}{abs(contrib[o]):.2f})" for o in top)
            rows.append({"Neuron": f"n{j+1}",
                         "z = Σ(w·x)+b": f"{float(src @ W[:, j] + b[j]):+.2f}",
                         "bias b": f"{b[j]:+.2f}",
                         "after activation": f"{float(acts[li+1][j]):.2f}",
                         "deduced mostly from": drivers})
        return pd.DataFrame(rows)

    # feature-detection map per layer (real ∂activation/∂sensor)
    st.markdown("##### What feature does each neuron in each layer detect?")
    st.caption("For every neuron we compute **∂(its activation) / ∂(each sensor)** by chain rule — literally "
               "*'how much does this neuron care about gas? about proximity?'*. Red = fires when that sensor "
               "rises, blue = fires when it falls.")
    ftabs = st.tabs([f"Layer {i+1} detects…" for i in range(n_layers)] + ["Output detects…"])
    blend_stats = []
    for li, ftab in enumerate(ftabs):
        layer = li + 1
        S = np.array([neuron_sensitivity(mlp, x, layer, j) for j in range(sizes[layer])])
        # how many sensors does each neuron meaningfully blend?
        nz = [(np.abs(row) > 0.5 * (np.abs(row).max() + 1e-12)).sum() for row in S]
        blend_stats.append(float(np.mean(nz)) if len(nz) else 0.0)
        with ftab:
            smax = np.abs(S).max() + 1e-12
            fh = go.Figure(go.Heatmap(z=S, x=NICE, y=[f"n{j+1}" for j in range(sizes[layer])],
                                      colorscale="RdBu", zmid=0, zmin=-smax, zmax=smax,
                                      colorbar=dict(title="∂a/∂sensor")))
            fh.update_layout(title=f"Layer {layer}: what each neuron responds to, in sensor terms")
            st.plotly_chart(style(fh, 320), width="stretch")
            # name the strongest detector in this layer
            k = int(np.argmax(np.abs(S).max(axis=1)))
            row = S[k]
            top = np.argsort(-np.abs(row))[:3]
            desc = ", ".join(f"{NICE[t]} {'↑' if row[t] > 0 else '↓'}" for t in top)
            st.info(f"**Read it like this:** neuron n{k+1} of this layer is essentially a "
                    f"*“{desc}”* detector. It has no name and nobody assigned it that job — "
                    f"it's just where backprop happened to land.")
    b1, b2 = st.columns(2)
    b1.metric("Sensors blended per neuron — layer 1", f"{blend_stats[0]:.1f}")
    if len(blend_stats) > 1:
        b2.metric(f"…by layer {len(blend_stats)}", f"{blend_stats[-1]:.1f}",
                  f"{blend_stats[-1]-blend_stats[0]:+.1f} more sensors combined")
    st.caption("☝️ **This is 'deeper = more deduction', measured.** Layer 1 neurons key off one or two "
               "sensors. Deeper neurons blend more of them at once — that's a *combination* rule "
               "('gas high AND worker close AND a jolt') that no single layer-1 neuron could ever express.")

    st.markdown("##### The per-neuron arithmetic")
    tabs = st.tabs([f"Hidden layer {i+1}" for i in range(n_layers)] + ["Output"])
    for li, tab in enumerate(tabs):
        with tab:
            st.dataframe(deduce(li), width="stretch", hide_index=True)
            if li == 0:
                st.info("**Layer 1 sees raw sensors.** Each neuron can only spot *one simple thing* — "
                        "“is gas high?”, “was the jolt big?”. A neuron fires (value > 0) only when its "
                        "weighted sum beats its bias.")
            elif li < n_layers:
                st.info(f"**Layer {li+1} never sees the raw sensors.** It only sees layer {li}'s answers, "
                        "and combines them — “gas high **AND** worker close **AND** a jolt”. "
                        "That is deeper deduction.")
            else:
                st.info("**The output neuron** squashes the deepest pattern through Sigmoid into a single "
                        "0–1 probability: how likely this shift ends in an incident.")

    # ---- 6. architecture effect ----
    st.markdown("#### 6 · What changing depth & width does")
    params = sum(W.size for W in mlp.coefs_) + sum(b.size for b in mlp.intercepts_)
    acc = accuracy_score(d["yte"], mlp.predict(d["Xte"]))
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Architecture", f"7 → {' → '.join(str(h) for h in hidden)} → 1")
    m2.metric("Learnable parameters", f"{params:,}")
    m3.metric("Test accuracy", f"{acc:.3f}")
    m4.metric("Risk for this shift", f"{float(acts[-1][0]):.3f}",
              "⚠️ incident-likely" if acts[-1][0] > 0.5 else "✅ safe")
    st.caption("**More width** = more patterns findable *per level*. **More depth** = patterns built on "
               "patterns. But on a 7-sensor table there's only so much to find — pile on too many and accuracy "
               "stalls or dips (overfitting). Deep learning earns its keep on *pixels*, not 7 tidy columns.")

    # ---- 7. myth busting ----
    st.markdown("#### 7 · Myth-busting — what this thing is *not*")
    myths = [
        ("“A neuron is like a brain cell — it thinks.”",
         "It multiplies each input by a weight, adds them up, adds a bias, applies one function. "
         "That's the *entire* neuron — you watched it in section 2. The brain analogy is where the name came "
         "from in the 1940s, not a description of what it does."),
        ("“Each neuron detects one nameable thing.”",
         "Almost never. Features are **distributed** — one pattern is spread across many neurons, and each "
         "neuron contributes to many patterns. Our 'deduced mostly from' table shows the *biggest* "
         "contributors, not a clean label. A neuron rarely means one tidy human word."),
        ("“The activation function makes the decision.”",
         "It decides nothing. Its only job is to **bend the line**. Remove it and your 3 layers collapse "
         "algebraically into 1 straight line — no depth, no combinations, no 'gas high AND worker close'."),
        ("“Inputs go through the neurons one at a time.”",
         "All 7 hit every neuron **simultaneously** — it's a single matrix multiply. Our step-by-step "
         "animation is a teaching device to slow the arithmetic down so you can see it."),
        ("“Backpropagation is the network learning from its mistakes, like a person.”",
         "It's the **chain rule** from calculus. It computes how much each weight contributed to the error, "
         "then subtracts a tiny fraction of that. You saw the literal table in section 4. Pure arithmetic — "
         "no reflection, no insight."),
        ("“The engineer sets the weights.”",
         "They start **random**. Every weight you see was found by backprop. Nobody typed a single one, and "
         "nobody could tell you in advance what any of them should be."),
        ("“More layers = smarter.”",
         "On 7 tidy sensor columns, extra depth mostly **memorises the training shifts** (overfitting) — "
         "try it with the sliders and watch accuracy stall or drop. Depth pays off on *raw pixels*, where "
         "there's a real hierarchy to build."),
        ("“The CNN understands what a helmet is.”",
         "It has never seen a helmet, or a worker, or a building. It found pixel patterns that statistically "
         "correlate with the label. That's why it also calls two hard hats on the floor a *bobsled*."),
        ("“Bias is a minor detail.”",
         "Without a bias, every neuron is forced to make its decision around zero. The bias is exactly what "
         "lets a neuron say *'only fire when it's **really** high'* — it moves the threshold."),
    ]
    for m, r in myths:
        with st.expander(f"❌ Myth — {m}"):
            st.markdown(f"✅ **Reality.** {r}")

    # ---- 8. the machinery, each with its own playground ----
    st.markdown("#### 8 · The machinery this network runs on")
    g = st.columns(5)
    g[0].markdown("**Activation**\n\nReLU (hidden)\nSigmoid (output)\n\n[Explore →](?stage=activation)")
    g[1].markdown("**Loss**\n\nBinary cross-entropy\n\n[Explore →](?stage=loss)")
    g[2].markdown("**Gradient descent**\n\nSteps downhill on the loss\n\n[Explore →](?stage=gradient-descent)")
    g[3].markdown("**Learning rate**\n\n0.001 (Adam default)\n\n[Explore →](?stage=learning-rate)")
    g[4].markdown("**Optimizer**\n\nAdam\n\n[Explore →](?stage=optimizer)")
    st.caption("Change any of them — and see *why* ours is the right pick for this site — in their own stages.")


def render_training():
    st.title("Training — watch the loss fall, epoch by epoch")
    d = get_data(); _, mlp = get_models()
    lc = np.array(mlp.loss_curve_)
    fig = go.Figure(go.Scatter(x=[0], y=[lc[0]], mode="lines", line=dict(color=POS, width=3)))
    step = max(1, len(lc) // 40)
    frames = [go.Frame(data=[go.Scatter(x=list(range(k)), y=list(lc[:k]))], name=str(k))
              for k in range(1, len(lc) + 1, step)]
    fig.update_xaxes(range=[0, len(lc)]); fig.update_yaxes(range=[0, lc.max() * 1.05])
    fig.update_layout(title="ANN training loss", xaxis_title="epoch", yaxis_title="loss")
    style(fig, 440); animate(fig, frames, ms=60)
    st.plotly_chart(fig, width="stretch")
    st.metric("Final ANN test accuracy", f"{accuracy_score(d['yte'], mlp.predict(d['Xte'])):.3f}")


# ---- CNN stages (REAL precomputed VGG16 assets) ----
@st.cache_data(show_spinner=False)
def cnn_meta():
    preds = {}
    p = os.path.join(CNN_ASSETS, "predictions.json")
    if os.path.isfile(p):
        with open(p) as f:
            preds = json.load(f)
    imgs = sorted([d for d in (os.listdir(CNN_ASSETS) if os.path.isdir(CNN_ASSETS) else [])
                   if os.path.isdir(os.path.join(CNN_ASSETS, d))])
    return imgs, preds


def _asset(name, f):
    return os.path.join(CNN_ASSETS, name, f)


def _no_assets():
    st.error("cnn_assets/ not found. Run tools/precompute_cnn.py (needs torch).")


@st.cache_data(show_spinner=False)
def conv1_kernels():
    """The REAL first conv layer of VGG16: 64 filters, each 3 channels x 3x3."""
    p = os.path.join(CNN_ASSETS, "conv1_kernels.npz")
    if not os.path.isfile(p):
        return None, None
    z = np.load(p)
    return z["W"], z["b"]


@st.cache_data(show_spinner=False)
def cnn_shapes():
    p = os.path.join(CNN_ASSETS, "shapes.json")
    if os.path.isfile(p):
        with open(p) as f:
            return json.load(f)
    return {}


@st.cache_data(show_spinner=False)
def image_tensor(name):
    """input.png -> the exact (3,224,224) tensor VGG16 actually eats."""
    from PIL import Image
    im = Image.open(_asset(name, "input.png")).convert("RGB").resize((224, 224))
    arr = np.asarray(im).astype(np.float32) / 255.0
    arr = (arr - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
    return arr.transpose(2, 0, 1)


def render_cnn_input():
    st.title("CNN input — the site's camera frames")
    imgs, preds = cnn_meta()
    if not imgs:
        _no_assets(); return
    name = st.selectbox("Camera frame", imgs, index=min(3, len(imgs) - 1))
    c1, c2 = st.columns(2)
    c1.image(_asset(name, "input.png"), caption=name, width="stretch")
    with c2:
        st.subheader("Real VGG16 top-3 guesses")
        for label, p in preds.get(name, []):
            st.progress(min(1.0, float(p)), text=f"{label} — {p:.2f}")
    st.caption("No gas value, no temperature — just pixels. Worn-helmet frames land on 'crash helmet'.")

    st.markdown("#### What the network actually receives")
    q1, q2, q3 = st.columns(3)
    q1.metric("Not a photo — a grid of numbers", "224 × 224 × 3")
    q2.metric("Individual numbers fed in", "150,528")
    q3.metric("Objects / people it can see", "0")
    st.info("**Be honest about the failures.** `helmet_03` and `helmet_04` (helmets *worn on heads*) come back "
            "as **crash helmet**. But `helmet_00` — two perfectly clear yellow hard hats lying on a floor — "
            "comes back **bobsled (0.38)**, and `helmet_01` returns **mousetrap (0.54)**. "
            "The network never learned what a helmet *is*. It learned pixel patterns that correlate with the "
            "word in its training photos — and those photos had helmets *on people*. Change the context and "
            "it falls apart. That is the honest state of the art, not a bug in our demo.")


def render_feature_maps():
    st.title("Inside the CNN — real VGG16 feature maps")
    imgs, _ = cnn_meta()
    if not imgs:
        _no_assets(); return
    name = st.selectbox("Frame", imgs, index=min(3, len(imgs) - 1))
    depth = st.select_slider("Slide deeper into the network →",
                             options=["Input", "Early — edges", "Mid — textures / parts", "Deep — abstract"],
                             value="Early — edges")
    f = {"Input": "input.png", "Early — edges": "early.png",
         "Mid — textures / parts": "mid.png", "Deep — abstract": "deep.png"}[depth]
    st.image(_asset(name, f), caption=depth, width="stretch")
    st.caption("Each tile is one real learned filter. Edges → parts → abstraction as depth grows — "
               "and nobody programmed any of it.")
    with st.expander("See all depths side by side"):
        c1, c2, c3 = st.columns(3)
        c1.image(_asset(name, "early.png"), caption="Early — edges", width="stretch")
        c2.image(_asset(name, "mid.png"), caption="Mid — parts", width="stretch")
        c3.image(_asset(name, "deep.png"), caption="Deep — abstract", width="stretch")

    # ---------- inside ONE convolution ----------
    st.markdown("#### Inside ONE convolution — the arithmetic nobody shows you")
    W, bb = conv1_kernels()
    if W is None:
        st.warning("conv1_kernels.npz missing — rerun tools/precompute_cnn.py.")
    else:
        st.caption("A 'filter' sounds mysterious. It is a **3×3 grid of numbers**. Slide it over the image, "
                   "multiply the 27 overlapping values, add them up, add a bias. That's a convolution.")
        cf, cr, cc = st.columns(3)
        f = cf.slider("Which of the 64 real filters?", 1, W.shape[0], 1) - 1
        r = cr.slider("Patch row (y)", 0, 220, 110)
        c0 = cc.slider("Patch col (x)", 0, 220, 110)
        t = image_tensor(name)
        patch, kern = t[:, r:r + 3, c0:c0 + 3], W[f]
        prod = patch * kern
        z_c = float(prod.sum() + bb[f])
        a_c = max(0.0, z_c)

        chans = ["R", "G", "B"]
        labels = [f"{chans[c]}({i},{j})" for c in range(3) for i in range(3) for j in range(3)]
        vals = [float(prod[c, i, j]) for c in range(3) for i in range(3) for j in range(3)] + [float(bb[f])]
        labels = labels + ["bias b"]
        figC = go.Figure(go.Bar(x=[0] * len(vals), y=labels, orientation="h",
                                marker_color=[POS if v >= 0 else NEG for v in vals]))
        framesC = []
        for k in range(0, len(vals) + 1, 2):
            shown = vals[:k] + [0] * (len(vals) - k)
            run = sum(vals[:k])
            framesC.append(go.Frame(
                data=[go.Bar(x=shown, y=labels, orientation="h",
                             marker_color=[POS if v >= 0 else NEG for v in vals])],
                layout=go.Layout(title=f"{k} of 27 pixel×weight products added   →   running z = {run:+.3f}"),
                name=str(k)))
        lim = max(abs(min(vals)), abs(max(vals))) * 1.5 + 0.05
        figC.update_xaxes(range=[-lim, lim], title="pixel value × kernel weight")
        figC.update_layout(title="Nothing added yet — z = 0.000")
        style(figC, 560); animate(figC, framesC, ms=140)
        st.plotly_chart(figC, width="stretch")

        m1, m2, m3 = st.columns(3)
        m1.metric("z = Σ(pixel × weight) + b", f"{z_c:+.3f}")
        m2.metric("after ReLU", f"{a_c:.3f}", "fired ✅" if a_c > 0 else "silent — zeroed")
        m3.metric("This produces", "ONE pixel")
        st.info(f"**That whole animation produced a single pixel** of filter {f+1}'s feature map. "
                f"Slide the same 3×3 kernel across all 224×224 positions and you get one complete tile "
                f"in the *Early — edges* image above. Do it with all 64 filters. Then do it again, 13 times, "
                f"with bigger stacks. **That is a CNN.** It is this arithmetic, repeated ~15 billion times "
                f"per image.")

    # ---------- deeper = smaller, not sharper ----------
    sh = cnn_shapes()
    if sh:
        st.markdown("#### The shape myth — deeper does **not** mean more detail")
        st.dataframe(pd.DataFrame({
            "Depth": ["Early (block1)", "Mid (block3)", "Deep (block5)"],
            "Feature map size": [f"{sh['early'][1]}×{sh['early'][2]}",
                                 f"{sh['mid'][1]}×{sh['mid'][2]}",
                                 f"{sh['deep'][1]}×{sh['deep'][2]}"],
            "How many filters": [sh["early"][0], sh["mid"][0], sh["deep"][0]],
            "What it holds": ["Fine detail, no meaning", "Parts, some meaning", "Almost no detail, most meaning"],
        }), width="stretch", hide_index=True)
        st.caption("Resolution **collapses** 224 → 56 → 14 while the number of filters **grows** 64 → 256 → 512. "
                   "The network trades *where* something is for *what* it is.")

    # ---------- myths ----------
    st.markdown("#### Myth-busting — what the CNN is *not* doing")
    myths = [
        ("“The CNN sees the photo the way you do.”",
         "It receives a grid of numbers — 224×224×3 = 150,528 of them, normalised. No objects, no scene, "
         "no worker. Just numbers. Everything else is arithmetic on that grid."),
        ("“A filter is a complicated AI thing.”",
         "A first-layer filter is **9 numbers per colour channel** — 27 in total. You just watched all 27 get "
         "multiplied and added. That's it. The 'intelligence' is only in *what values* those 27 numbers took, "
         "and those were found by backprop, not written by anyone."),
        ("“Deeper layers see more detail.”",
         "The opposite. Detail is *destroyed* on purpose: 224×224 → 56×56 → 14×14. Deep layers are almost "
         "blind to *where* things are — they only keep *what* is there. That's why Grad-CAM's heatmap is "
         "blocky: it's upsampled from a 14×14 grid."),
        ("“Each filter detects an object.”",
         "Early filters fire on edges and colour blobs — they'd fire the same on a helmet, a cup, or a road "
         "sign. 'Helmet' only exists as a *combination* across hundreds of filters, deep in the stack. No "
         "single neuron owns the concept."),
        ("“The network learned what a helmet is.”",
         "It learned pixel statistics that correlate with a label. Proof from our own data: it calls two "
         "hard hats lying on a floor a **bobsled** (0.38), and a hat on a toolbox a **mousetrap** (0.54). "
         "It never learned 'helmet' — it learned *helmet-on-a-head-shaped-thing-in-photos-like-these*."),
        ("“Grad-CAM shows what the network was thinking.”",
         "It shows which *regions* most influenced one class score, computed from gradients in the last conv "
         "layer. It is a sensitivity map, not an explanation, and not a reason. It tells you **where**, never "
         "**why**."),
        ("“It must see the whole helmet to recognise one.”",
         "No. CNNs happily fire on parts and textures — a curved bright rim is often enough. That's also why "
         "they can be fooled by things that merely *look* like the parts they rely on."),
        ("“This needs to understand safety rules.”",
         "It has no concept of safety, danger, or a worker. It maps pixels to a number. The *meaning* — "
         "'no helmet means pull this person off site' — is supplied entirely by us, in the fusion stage."),
    ]
    for m, r in myths:
        with st.expander(f"❌ Myth — {m}"):
            st.markdown(f"✅ **Reality.** {r}")


def render_gradcam():
    st.title("Grad-CAM — where did the CNN look?")
    imgs, preds = cnn_meta()
    if not imgs:
        _no_assets(); return
    name = st.selectbox("Frame", imgs, index=min(3, len(imgs) - 1))
    top = preds.get(name, [["?", 0]])[0]
    show = st.toggle("Show Grad-CAM overlay", value=True)
    c1, c2 = st.columns(2)
    c1.image(_asset(name, "input.png"), caption="Camera frame", width="stretch")
    c2.image(_asset(name, "gradcam.png" if show else "input.png"),
             caption=f"Grad-CAM for '{top[0]}'" if show else "overlay off", width="stretch")
    st.success(f"Real Grad-CAM on VGG16's last conv layer (class: **{top[0]}**). "
               "The heat sits on the helmet — the network learned that locating feature itself.")

    st.markdown("#### How this heatmap is actually made (no magic)")
    st.markdown(
        "1. Run the photo forward, take the score for **one class** (here *{}*).\n"
        "2. Ask backprop: *how much would that score change if each of the 512 deep feature maps changed?* "
        "→ that's a gradient per map.\n"
        "3. Use those gradients as **weights**, add the 512 maps together, keep the positives.\n"
        "4. You now have a **14×14** grid. Stretch it to 224×224 and lay it over the photo.\n\n"
        "That blur you see? That's a 14×14 image blown up 16×. There is no fine detail in there to recover."
        .format(top[0]))

    st.markdown("#### Myth-busting — reading Grad-CAM honestly")
    for m, r in [
        ("“Grad-CAM shows what the network was thinking.”",
         "It shows **where**, never **why**. It's a sensitivity map: which regions most influenced one class "
         "score. It cannot tell you what the network believes, or that it 'knows' a helmet."),
        ("“The heat is precise — it outlines the helmet.”",
         "It's a 14×14 grid upsampled to 224×224. Every blob is ~16 pixels wide by construction. It points at "
         "a *region*, never an outline."),
        ("“If the heat is on the helmet, the model is right for the right reason.”",
         "Not guaranteed. It's evidence, not proof. A model can look at the right region and still use a "
         "shortcut — hi-vis orange, sky background, the shape of a shoulder. Grad-CAM narrows suspicion; it "
         "doesn't settle it."),
        ("“Grad-CAM works on any layer equally.”",
         "We deliberately use the **last** conv layer — the trade-off point where semantics are richest but "
         "spatial detail is nearly gone. Earlier layers give sharper maps that mean much less."),
    ]:
        with st.expander(f"❌ Myth — {m}"):
            st.markdown(f"✅ **Reality.** {r}")


def render_evaluate():
    st.title("Evaluate — ML vs ANN on unseen shifts")
    d = get_data(); rf, mlp = get_models()
    rf_acc = accuracy_score(d["yte"], rf.predict(d["Xte"]))
    ann_pred = mlp.predict(d["Xte"])
    ann_acc = accuracy_score(d["yte"], ann_pred)
    c1, c2 = st.columns(2)
    c1.metric("Random Forest (ML)", f"{rf_acc:.3f}")
    c2.metric("Neural Net (ANN)", f"{ann_acc:.3f}")
    cm = confusion_matrix(d["yte"], ann_pred)
    fig = go.Figure(go.Heatmap(z=cm, x=["Pred Safe", "Pred Incident"], y=["Safe", "Incident"],
                               colorscale="Blues", text=cm, texttemplate="%{text}", showscale=False))
    fig.update_layout(title="ANN confusion matrix")
    st.plotly_chart(style(fig, 400), width="stretch")
    st.warning(f"**The dangerous cell:** {cm[1][0]} shifts predicted *Safe* that actually had an incident — "
               "false negatives. A false alarm is annoying; a missed accident can cost a life.")


def render_compare_proof():
    st.title("The proof — DL digs deeper")
    st.table(pd.DataFrame({
        "": ["Sensor risk (table)", "Helmet from raw pixels", "Who designed the features?"],
        "ML — Random Forest": ["✅ works", "❌ can't even start", "A human"],
        "DL — ANN / CNN": ["✅ works", "✅ edges → parts → helmet", "The network itself"],
    }))
    st.success("Both handle the sensor table. Only DL went from raw pixels to *no helmet* — "
               "because it learned its own features. That is digging deeper.")


def render_fusion():
    st.title("AI Fusion — one site-safety decision")
    c1, c2 = st.columns(2)
    risk = c1.slider("Sensor risk (ANN)", 0.0, 1.0, 0.8, 0.05)
    helmet = c2.toggle("Helmet detected (CNN)", value=False)
    if risk > 0.5 and not helmet:
        msg, color = "🚨 CRITICAL — risky conditions AND no helmet", RED
    elif risk > 0.5:
        msg, color = "⚠️ WARNING — environmental risk detected", AMBER
    elif not helmet:
        msg, color = "⚠️ WARNING — PPE violation: helmet missing", AMBER
    else:
        msg, color = "✅ OK — site safe", GREEN
    st.markdown(f"<div style='padding:26px;border-radius:12px;text-align:center;font-size:22px;"
                f"background:{color};color:#0e1117;font-weight:700'>{msg}</div>", unsafe_allow_html=True)
    st.caption("Sensor risk + helmet check + worker location = comprehensive site monitoring.")


# ============================================================================
# ROUTER
# ============================================================================
STAGES = {
    "overview": ("Site overview", render_overview),
    "load": ("1.0 Load data", render_load),
    "inspect": ("1.1 Inspect", render_inspect),
    "clean": ("1.2 Clean", render_clean),
    "normalize": ("1.3 Normalize", render_normalize),
    "split": ("1.4 Split", render_split),
    "compare": ("2 ML vs DL (promise)", render_compare),
    "ml-baseline": ("2 ML baseline", render_ml_baseline),
    "what-is-dl": ("3 What is DL", render_what_is_dl),
    "neuron": ("4 Single neuron", render_neuron),
    "activation": ("4 Activation functions", render_activation),
    "loss": ("4½ Loss function", render_loss),
    "gradient-descent": ("4½ Gradient descent", render_gradient_descent),
    "learning-rate": ("4½ Learning rate", render_learning_rate),
    "optimizer": ("4½ Optimizers", render_optimizer),
    "network": ("5 ANN network", render_network),
    "training": ("5 Training", render_training),
    "cnn-input": ("6 CNN input", render_cnn_input),
    "feature-maps": ("6 Feature maps", render_feature_maps),
    "gradcam": ("6 Grad-CAM", render_gradcam),
    "evaluate": ("7 Evaluate", render_evaluate),
    "compare-proof": ("8 ML vs DL (proof)", render_compare_proof),
    "fusion": ("8 AI Fusion", render_fusion),
}

stage = st.query_params.get("stage", "overview")
if stage not in STAGES:
    stage = "overview"

with st.sidebar:
    st.markdown("### 🦺 Smart Site — DL")
    st.caption("Each notebook step opens its own stage here via `?stage=`.")
    keys = list(STAGES)
    sel = st.selectbox("Jump to a stage", keys, index=keys.index(stage),
                       format_func=lambda k: STAGES[k][0])
    if sel != stage:
        st.query_params["stage"] = sel
        st.rerun()
    st.divider()
    st.caption(f"Current: **{STAGES[stage][0]}**")
    st.caption("▶ Press **Play** on a chart to animate it.")

STAGES[stage][1]()
st.divider()
narrate(stage)
