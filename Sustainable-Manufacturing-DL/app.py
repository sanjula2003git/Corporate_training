"""
AI for Sustainable Manufacturing - Deep Learning illustration app
=================================================================
One project, 30 stage pages, taught as one plant-sustainability build.
Each notebook step links here with ?stage=<id>.

Dark canvas, animated Plotly (press Play) + interactive sliders/toggles.
Every page: manufacturing activity -> engineering challenge -> AI concept ->
technical illustration -> notebook connection.

The problem: a plant consumes energy continuously and reviews it monthly.
Instrument it, and learn to predict, explain and reduce its energy and carbon.
  Meters : machine load, motor temperature, compressed-air pressure and flow,
           idle share, units produced, material used, ambient temperature.
  ML     : predict the hour's kWh and CO2; flag a wasteful hour; rank drivers.
  DL     : grade a thermal frame, locate the loss (Grad-CAM).
  System : anomaly detection + operating-point optimisation + fusion + dashboard.
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

# The eight metered channels — order matches story.render_reading exactly.
FEATURES = ["load_pct", "motor_temp_c", "air_pressure_bar", "air_flow_m3h",
            "idle_pct", "units_per_hr", "material_kg", "ambient_temp_c"]
NICE = ["Load (%)", "Motor temp (°C)", "Air pressure (bar)", "Air flow (m³/h)",
        "Idle (%)", "Units/hour", "Material (kg)", "Ambient (°C)"]

SPEC_LIMIT = 2.00       # kWh per unit above which an hour counts as wasteful
GRID_KG = 0.72          # kg CO2 per kWh from the grid
BASELOAD = 36.0         # kW the plant draws before any machine is loaded
LOAD_LIN = 0.30         # kW per % load — the useful work
LOAD_SQ = 0.0135        # kW per (% load)^2 — losses that grow faster than output

st.set_page_config(page_title="AI for Sustainable Manufacturing", page_icon="🏭",
                   layout="wide")
bridge.inject_css()   # the plant energy-console display language


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
# THE PLANT ENERGY MODEL  (approximate, monotone, teaching-grade)
# The eight channels are consequences of a hidden inefficiency ("waste": air
# leaks, failed lagging, poor scheduling) and the operating conditions. The SAME
# functions drive the synthetic dataset AND the "try an hour" tools, so they
# always agree.
# ----------------------------------------------------------------------------
def _units_for(load, idle):
    """Units produced in the hour, from machine load and idle share."""
    return 1.35 * load * (1.0 - idle / 100.0)


def _signals_for(waste, load, idle, ambient):
    """Build the 8-channel row(s) the models expect, noise-free.
    Works on scalars or numpy arrays. Column order == FEATURES."""
    waste = np.asarray(waste, float)
    load = np.asarray(load, float)
    idle = np.asarray(idle, float)
    ambient = np.asarray(ambient, float)

    motor = ambient + 14.0 + 0.30 * load + 22.0 * waste      # °C
    press = 6.8 - 1.6 * waste                                # bar (leak drops it)
    flow = 28.0 + 70.0 * waste + 0.35 * load                 # m³/h (leak raises it)
    units = _units_for(load, idle)                           # units/h
    material = 0.90 * units * (1.0 + 0.35 * waste)           # kg (scrap grows with waste)
    return np.stack([load, motor, press, flow, idle, units, material, ambient], axis=-1)


def _energy_for(waste, load, idle, ambient):
    """Electricity drawn in the hour, kWh.

    Three parts, and the third is what makes the optimisation page interesting:
      BASELOAD           - lighting, ventilation, standby air. Paid whatever you make.
      LOAD_LIN * load    - the useful work, proportional to output.
      LOAD_SQ * load**2  - losses that grow FASTER than output: drives pushed past
                           their best-efficiency point, extra cooling, more scrap.
    Baseload alone would make high load always greener per unit. The squared term
    pushes back, so specific energy has a genuine minimum in between.
    """
    load = np.asarray(load, float)
    return (BASELOAD + LOAD_LIN * load + LOAD_SQ * load ** 2
            + 42.0 * np.asarray(waste, float)
            + 0.22 * np.asarray(idle, float)
            + 0.55 * np.clip(np.asarray(ambient, float) - 24.0, 0, None))


def _co2_for(energy_kwh, material_kg):
    """kg CO2: grid electricity plus the embodied carbon of the material consumed."""
    return GRID_KG * np.asarray(energy_kwh, float) + 0.05 * np.asarray(material_kg, float)


# ----------------------------------------------------------------------------
# DATA  (synthetic plant energy log, generated + cached)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_data():
    rng = np.random.default_rng(42)
    N = 1500
    waste = rng.uniform(0.0, 0.9, N)
    load = rng.uniform(30.0, 100.0, N)
    idle = rng.uniform(0.0, 35.0, N)
    ambient = rng.uniform(12.0, 38.0, N)

    base = _signals_for(waste, load, idle, ambient)
    load_c = np.clip(base[:, 0] + rng.normal(0, 1.2, N), 0, None)
    motor = base[:, 1] + rng.normal(0, 1.5, N)
    press = base[:, 2] + rng.normal(0, 0.08, N)
    flow = np.abs(base[:, 3] + rng.normal(0, 3.0, N))
    idle_c = np.clip(base[:, 4] + rng.normal(0, 1.0, N), 0, None)
    units = np.abs(base[:, 5] + rng.normal(0, 2.0, N))
    material = np.abs(base[:, 6] + rng.normal(0, 2.5, N))

    energy = _energy_for(waste, load, idle, ambient) + rng.normal(0, 1.5, N)
    co2 = _co2_for(energy, material)
    specific = energy / np.clip(units, 1e-6, None)
    wasteful = (specific > SPEC_LIMIT).astype(int)

    df = pd.DataFrame({
        "hour_id": np.arange(1, N + 1),
        "load_pct": load_c.round(1), "motor_temp_c": motor.round(1),
        "air_pressure_bar": press.round(2), "air_flow_m3h": flow.round(1),
        "idle_pct": idle_c.round(1), "units_per_hr": units.round(0),
        "material_kg": material.round(1), "ambient_temp_c": ambient.round(1),
        "energy_kwh": energy.round(1), "co2_kg": co2.round(1),
        "kwh_per_unit": specific.round(3), "wasteful": wasteful,
    })

    # a realistically messy historian export: dropouts, stuck/impossible values, duplicates
    dirty = df.copy()
    for col in FEATURES:
        dirty.loc[rng.choice(N, int(0.06 * N), replace=False), col] = np.nan
    dirty.loc[rng.choice(N, 13, replace=False), "air_flow_m3h"] = 0.0       # dead flow meter
    dirty.loc[rng.choice(N, 10, replace=False), "motor_temp_c"] = 999.0     # thermocouple fault
    dirty.loc[rng.choice(N, 12, replace=False), "air_pressure_bar"] = 0.0   # frozen pressure channel
    dirty.loc[rng.choice(N, 11, replace=False), "load_pct"] = 9999.0        # saturated drive tag
    dirty = pd.concat([dirty, dirty.sample(20, random_state=4)], ignore_index=True)

    clean = dirty.drop_duplicates().copy()
    clean.loc[clean.load_pct > 150, "load_pct"] = np.nan
    clean.loc[clean.motor_temp_c > 200, "motor_temp_c"] = np.nan
    clean.loc[clean.air_flow_m3h <= 0, "air_flow_m3h"] = np.nan
    clean.loc[clean.air_pressure_bar <= 0.5, "air_pressure_bar"] = np.nan
    for col in FEATURES:
        clean[col] = clean[col].fillna(clean[col].median())

    scaler = MinMaxScaler()
    norm = clean.copy()
    norm[FEATURES] = scaler.fit_transform(clean[FEATURES])

    X = norm[FEATURES].values
    ywaste = norm["wasteful"].values
    yen = norm["energy_kwh"].values
    yco2 = norm["co2_kg"].values

    idx = np.arange(len(X))
    itr, itmp = train_test_split(idx, test_size=0.30, random_state=42, stratify=ywaste)
    ival, ite = train_test_split(itmp, test_size=0.50, random_state=42, stratify=ywaste[itmp])

    return dict(truth=df, dirty=dirty, clean=clean, norm=norm, scaler=scaler,
                Xtr=X[itr], Xval=X[ival], Xte=X[ite],
                ytr=ywaste[itr], yval=ywaste[ival], yte=ywaste[ite],
                EnTr=yen[itr], EnTe=yen[ite],
                CoTr=yco2[itr], CoTe=yco2[ite])


@st.cache_resource(show_spinner=False)
def get_models():
    d = get_data()
    rf = RandomForestClassifier(n_estimators=200, random_state=42).fit(d["Xtr"], d["ytr"])
    mlp = MLPClassifier(hidden_layer_sizes=(12, 6), max_iter=800,
                        random_state=42).fit(d["Xtr"], d["ytr"])
    return rf, mlp


@st.cache_resource(show_spinner=False)
def get_regressors():
    d = get_data()
    en = RandomForestRegressor(n_estimators=200, random_state=42).fit(d["Xtr"], d["EnTr"])
    co = RandomForestRegressor(n_estimators=200, random_state=42).fit(d["Xtr"], d["CoTr"])
    return en, co


# ============================================================================
# TECHNICAL RENDERERS  (Part 4 of each page)
# ============================================================================
def render_load():
    st.title("⑤ The energy log arrives")
    d = get_data()
    raw = d["dirty"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Production hours logged", f"{len(raw):,}")
    c2.metric("Columns", raw.shape[1])
    c3.metric("Meter channels", len(FEATURES))
    st.caption("The first thing you do with any historian export: check what actually arrived.")
    st.dataframe(raw.head(8), use_container_width=True, hide_index=True)
    st.info("Types and counts look plausible — but plausible is not verified. The next step inspects the "
            "channels for dropouts and stuck meters before anything is built on them.")


def render_inspect():
    st.title("⑥ Meter health check")
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
    fig2.update_layout(title=f"{NICE[FEATURES.index(col)]} — a spike far from the pack is a meter fault")
    st.plotly_chart(style(fig2, 340), use_container_width=True)
    st.info("A saturated drive tag (9,999%), a faulted thermocouple (999 °C), a dead flow meter (0 m³/h) "
            "and a frozen pressure channel (0 bar) all announce themselves here. Diagnosis only — nothing "
            "is repaired yet.")


def render_clean():
    st.title("⑦ Dropouts and stuck meters out")
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
    st.info("**Why the median, not the mean?** The mean is dragged badly by a single 999 °C thermocouple "
            "fault. The median — the middle value — barely notices it, so the filled-in reading stays "
            "physically realistic.")


def render_normalize():
    st.title("⑧ Put every channel on one scale")
    st.info("📐 **Every channel reports in its own unit — percent, °C, bar, m³/h, units per hour, kilograms.** "
            "Put them all on one common 0–1 scale first, so the model compares them fairly instead of "
            "trusting whichever reading happens to have the biggest *number*.")
    n1, n2, n3 = st.columns(3)
    n1.metric("Air flow reads", "68 m³/h")
    n2.metric("Pressure reads", "5.9 bar")
    n3.metric("Idle reads", "9 %")
    st.caption("Same hour, same instant. To a raw model, air flow looks **ten times more important than "
               "pressure** — purely because of its unit, when a 0.9 bar drop is the clearest leak signal "
               "on the list. Press Play to collapse a channel onto 0–1:")
    d = get_data()
    col = st.selectbox("Channel", FEATURES, index=3,
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
    st.title("⑨ Known hours vs a sealed set")
    st.info("🧪 **Never test an energy model on the very hours it was tuned on.** It would just repeat what it "
            "memorised, and you would learn nothing about next week's production. So some hours train the "
            "model, and some are sealed until the audit.")
    st.caption("Press Play: the hours divide into train / validation / test.")
    d = get_data()
    parts = [("Train", d["ytr"], POS), ("Validation", d["yval"], AMBER), ("Test", d["yte"], GREEN)]
    eff = [int((a == 0).sum()) for _, a, _ in parts]
    bad = [int((a == 1).sum()) for _, a, _ in parts]
    names = [n for n, _, _ in parts]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=eff, name="efficient hour", marker_color=GREEN))
    fig.add_trace(go.Bar(x=names, y=bad, name="wasteful hour", marker_color=RED))
    fig.update_layout(barmode="stack",
                      title="hours per split (the waste rate is kept balanced across all three)")
    style(fig, 380)
    animate(fig, _bars_grow([dict(x=names, y=eff, color=GREEN, name="efficient hour"),
                             dict(x=names, y=bad, color=RED, name="wasteful hour")]), ms=90)
    st.plotly_chart(fig, use_container_width=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Train", f"{len(d['ytr'])}")
    c2.metric("Validation", f"{len(d['yval'])}")
    c3.metric("Test (sealed)", f"{len(d['yte'])}")
    st.info("The test hours are locked away now and only opened at the sustainability audit. That is the one "
            "fair score of what the model will do on the plant's next shift.")


def render_ml_baseline():
    st.title("⑩ Energy from the readings — Random Forest")
    d = get_data()
    en_m, co_m = get_regressors()

    st.markdown("##### Predicted vs metered energy, on the sealed hours")
    pred = en_m.predict(d["Xte"])
    lo = float(min(d["EnTe"].min(), pred.min())); hi = float(max(d["EnTe"].max(), pred.max()))
    fig = go.Figure(go.Scatter(x=d["EnTe"], y=pred, mode="markers",
                               marker=dict(size=6, color=POS, opacity=0.6, line=dict(width=0))))
    fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines",
                             line=dict(color=MUTED, dash="dash"), showlegend=False))
    fig.update_layout(title="the model has never seen these hours")
    fig.update_xaxes(title="metered kWh"); fig.update_yaxes(title="predicted kWh")
    st.plotly_chart(style(fig, 380), use_container_width=True)

    c1, c2 = st.columns(2)
    c1.metric("Energy R² on sealed hours", f"{r2_score(d['EnTe'], pred):.3f}")
    c2.metric("CO₂ R² on sealed hours", f"{r2_score(d['CoTe'], co_m.predict(d['Xte'])):.3f}")
    st.caption("You never wrote an energy equation. An engineer named the eight factors; the forest learned "
               "the mapping from 1,500 logged hours.")

    st.markdown("##### Try an hour — set the hidden waste and the operating conditions")
    c = st.columns(4)
    waste = c[0].slider("Hidden waste (leaks, lagging)", 0.0, 0.9, 0.35, 0.02)
    load = c[1].slider("Machine load (%)", 30, 100, 70, 1)
    idle = c[2].slider("Idle share (%)", 0, 35, 8, 1)
    amb = c[3].slider("Ambient (°C)", 12, 38, 24, 1)

    row = _signals_for(np.array([waste]), np.array([float(load)]),
                       np.array([float(idle)]), np.array([float(amb)]))
    row_s = d["scaler"].transform(row)
    kwh_hat = float(en_m.predict(row_s)[0])
    co2_hat = float(co_m.predict(row_s)[0])
    units = float(row[0, FEATURES.index("units_per_hr")])
    spec = kwh_hat / max(units, 1e-6)
    ok = spec <= SPEC_LIMIT

    m = st.columns(4)
    m[0].metric("Predicted energy", f"{kwh_hat:.1f} kWh",
                f"true {float(_energy_for(waste, load, idle, amb)):.1f}")
    m[1].metric("Predicted CO₂", f"{co2_hat:.1f} kg")
    m[2].metric("Units produced", f"{units:.0f}")
    m[3].metric("Energy per unit", f"{spec:.2f} kWh", f"limit {SPEC_LIMIT:.2f}",
                delta_color="off")
    st.markdown(f"<div style='padding:14px;border-radius:10px;text-align:center;font-size:18px;"
                f"font-weight:700;background:{GREEN if ok else RED};color:#0e1117'>"
                f"{'✅ efficient hour — within the limit' if ok else '❌ wasteful hour — above the limit'}</div>",
                unsafe_allow_html=True)
    st.info("Raise the hidden waste and watch the air flow, motor temperature and kWh all move together — "
            "which is exactly the correlation the forest learned to exploit. The anomaly detector and the "
            "fusion screen both build on this prediction.")


def render_drivers():
    st.title("⑪ What drives the bill — feature importance")
    d = get_data()
    en_m, _ = get_regressors()
    rf, _mlp = get_models()

    which = st.radio("Rank the drivers of…", ["Energy consumed (kWh)", "Whether the hour was wasteful"],
                     horizontal=True)
    imp = (en_m if which.startswith("Energy") else rf).feature_importances_
    order = np.argsort(imp)[::-1]
    fig = go.Figure(go.Bar(x=[NICE[i] for i in order], y=imp[order], marker_color=POS,
                           text=[f"{imp[i]:.2f}" for i in order], textposition="outside"))
    fig.update_layout(title=f"drivers of {which.lower()}")
    fig.update_yaxes(title="importance")
    style(fig, 380)
    animate(fig, _bars_grow([dict(x=[NICE[i] for i in order], y=list(imp[order]), color=POS,
                                  text=[f"{imp[i]:.2f}" for i in order])]), ms=70)
    st.plotly_chart(fig, use_container_width=True)

    top = NICE[int(order[0])]
    st.success(f"**{top}** moves the prediction more than anything else. That is where an energy engineer "
               f"should look first — and it is a claim the plant can go and check on the floor.")

    st.markdown("##### Importance is not proof of cause")
    st.markdown(f"""
- Air flow **rises** with a leak and line pressure **falls**, so both look important. They are two views of
  one fault, not two faults.
- Machine load dominates total kWh and is **not waste** — the plant is supposed to be producing. That is
  why the wasteful-hour model ranks the channels completely differently from the energy model.
- Use the ranking to decide **what to investigate**, then confirm on site. The model never authorises a
  spend on its own.
    """)
    st.info("Switch between the two rankings above. The change tells you something real: predicting *how "
            "much* energy is used is not the same question as predicting *whether it was wasted*.")


def render_neuron():
    st.title("⑯ The neuron — z = w·x + b")
    st.caption("Set a weight for each channel. The neuron multiplies, sums, adds a bias, and squashes the "
               "result to a probability that the hour was wasteful. This is the single computation every "
               "layer repeats.")
    d = get_data()
    row = d["norm"].iloc[7]
    x = row[FEATURES].values.astype(float)
    cols = st.columns(len(FEATURES))
    # air flow and idle push towards waste; pressure and units push away from it
    default_w = [0.2, 0.5, -0.9, 1.0, 0.8, -0.7, 0.2, 0.3]
    w = []
    for i, c in enumerate(cols):
        with c:
            st.caption(NICE[i])
            w.append(st.slider(NICE[i], -1.5, 1.5, default_w[i], 0.1,
                               key=f"w{i}", label_visibility="collapsed"))
    b = st.slider("Bias b — the baseline before any reading is seen", -2.0, 2.0, -0.3, 0.1)
    w = np.array(w)
    z = float(np.dot(w, x) + b)
    p = float(sigmoid(z))

    fig = go.Figure(go.Bar(x=NICE, y=w * x, marker_color=[POS if v >= 0 else NEG for v in w * x],
                           text=[f"{v:+.2f}" for v in w * x], textposition="outside"))
    fig.update_layout(title=f"each channel's contribution · z = {z:+.2f} → p(wasteful) = {p:.2f}")
    fig.update_yaxes(title="w × x")
    st.plotly_chart(style(fig, 380), use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Weighted sum z", f"{z:+.2f}")
    c2.metric("After sigmoid", f"{p:.2f}")
    c3.metric("Call", "wasteful" if p > 0.5 else "efficient")
    st.info("Nothing here is mysterious: eight multiplications, a sum, a bias, and a squash. A real network "
            "does not let you set these weights — it learns them from the log, which is the whole point.")


def render_activation():
    st.title("⑰ Activation — turning a sum into a decision")
    st.caption("The weighted sum can be any number. An activation function turns it into something a plant "
               "can act on.")
    z = st.slider("Weighted sum z coming out of the neuron", -6.0, 6.0, 1.2, 0.1)
    xs = np.linspace(-6, 6, 300)

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Scatter(x=xs, y=sigmoid(xs), mode="lines", line=dict(color=POS, width=3)))
        fig.add_trace(go.Scatter(x=[z], y=[sigmoid(z)], mode="markers",
                                 marker=dict(size=14, color=AMBER), showlegend=False))
        fig.add_hline(y=0.5, line=dict(color=MUTED, dash="dot"))
        fig.update_layout(title=f"sigmoid — probability · σ({z:.1f}) = {sigmoid(z):.3f}")
        st.plotly_chart(style(fig, 340), use_container_width=True)
    with c2:
        fig2 = go.Figure(go.Scatter(x=xs, y=np.maximum(0, xs), mode="lines",
                                    line=dict(color=TECH, width=3)))
        fig2.add_trace(go.Scatter(x=[z], y=[max(0, z)], mode="markers",
                                  marker=dict(size=14, color=AMBER), showlegend=False))
        fig2.update_layout(title=f"ReLU — passes positive evidence · ReLU({z:.1f}) = {max(0, z):.2f}")
        st.plotly_chart(style(fig2, 340), use_container_width=True)

    st.markdown("##### Why not a hard alarm limit?")
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=xs, y=(xs > 0).astype(float), mode="lines",
                              line=dict(color=RED, width=3, shape="hv"), name="hard limit"))
    fig3.add_trace(go.Scatter(x=xs, y=sigmoid(xs), mode="lines",
                              line=dict(color=POS, width=3), name="sigmoid"))
    fig3.update_layout(title="a hard limit has no slope — training has nothing to follow")
    st.plotly_chart(style(fig3, 320), use_container_width=True)
    st.info("Two reasons for the smooth curve. It reports **how confident** the call is, so a borderline "
            "hour is not treated as a certainty. And it has a **gradient everywhere**, which is what lets "
            "gradient descent work at all.")


def render_gradient_descent():
    st.title("⑲ Loss and gradient descent")
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
    st.info("Too small a step and it crawls; too big and it bounces past the minimum and starts flagging "
            "every efficient hour. The gradient always points downhill — the art is the step size.")


def render_network():
    st.title("⑳ The network — layered neurons")
    st.caption("One neuron draws one straight line. Layers bend the boundary around real waste patterns. "
               "Here: air flow vs idle share, with the model's decision surface behind the hours.")
    d = get_data()
    depth_opts = {"2 (one tiny layer)": (2,), "6": (6,), "12 → 6": (12, 6), "16 → 8": (16, 8)}
    depth_label = st.select_slider("Hidden layer size", options=list(depth_opts), value="12 → 6")
    depth = depth_opts[depth_label]
    idx = [FEATURES.index("air_flow_m3h"), FEATURES.index("idle_pct")]
    Xtr2 = d["Xtr"][:, idx]
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
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
    fig.update_layout(title="decision surface — red = predicted wasteful")
    fig.update_xaxes(title="air flow (scaled)"); fig.update_yaxes(title="idle share (scaled)")
    st.plotly_chart(style(fig, 420), use_container_width=True)
    st.info("With one tiny layer the boundary is nearly straight. Add width and depth and it wraps around "
            "the high-flow, high-idle corner — the pattern a single weighted sum cannot hold.")


def render_training():
    st.title("㉑ Training — the loss falls, then flattens")
    d = get_data()
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
    fig.add_trace(go.Scatter(y=losses, mode="lines", line=dict(color=POS, width=2),
                             name="training loss"))
    fig.add_trace(go.Scatter(y=val, mode="lines", line=dict(color=AMBER, width=2),
                             name="validation error"))
    frames = [go.Frame(data=[go.Scatter(y=losses[:k + 1], mode="lines",
                                        line=dict(color=POS, width=2)),
                             go.Scatter(y=val[:k + 1], mode="lines",
                                        line=dict(color=AMBER, width=2))], name=str(k))
              for k in range(0, len(losses), 3)]
    fig.update_layout(title="training loss and held-out error over epochs")
    fig.update_xaxes(title="epoch"); fig.update_yaxes(title="loss / error rate")
    style(fig, 400); animate(fig, frames, ms=60)
    st.plotly_chart(fig, use_container_width=True)
    best = int(np.argmin(val))
    c1, c2, c3 = st.columns(3)
    c1.metric("Final training loss", f"{losses[-1]:.3f}")
    c2.metric("Best epoch on validation", best)
    c3.metric("Test accuracy", f"{m.score(d['Xte'], d['yte'])*100:.1f}%")
    st.info("The training loss keeps falling. The validation error stops improving around epoch "
            f"{best} — past that point the network is memorising these hours rather than learning the "
            "pattern. That turn is where you stop.")


def render_proof():
    st.title("㉔ The verdict — each tool doing the part it is good for")
    d = get_data()
    en_m, _ = get_regressors()
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mlp = MLPRegressor(hidden_layer_sizes=(16, 8), max_iter=1200,
                           random_state=0).fit(d["Xtr"], d["EnTr"])
    r_rf = r2_score(d["EnTe"], en_m.predict(d["Xte"]))
    r_ann = r2_score(d["EnTe"], mlp.predict(d["Xte"]))
    c1, c2 = st.columns(2)
    c1.metric("Random Forest — energy R²", f"{r_rf:.3f}")
    c2.metric("Neural network — energy R²", f"{r_ann:.3f}", f"{r_ann - r_rf:+.3f} vs RF")
    st.table(pd.DataFrame({
        "": ["Energy & CO₂ from the 8 readings", "Grade a thermal frame from pixels",
             "Who names the features?"],
        "ML — Random Forest": ["✅ works", "❌ can't even start", "The engineer"],
        "DL — ANN / CNN": ["✅ works", "✅ learns the pattern", "The network learns them"],
    }))
    st.success("On the eight named channels both tools predict energy about equally well, because the "
               "engineer already named the factors. On the raw thermal frame — where nobody can hand-write "
               "the rule — the CNN takes that part off the engineer's plate. AI does not out-think the "
               "engineer here; it just handles the job a person cannot do by hand.")
    st.info("When an engineer has named the features, use machine learning — simpler, faster, easier to "
            "defend in an audit. When nobody can, as with the thermal frame, deep learning is the option "
            "that works.")


# ============================================================================
# PREDICTION & OPTIMISATION — the two teaching beats specific to this project
# ============================================================================
def render_anomaly():
    st.title("㉕ Normal for this load — and the excess it cannot explain")
    st.caption("A plant's consumption swings with load and with the weather. The monitor learns that normal "
               "relationship, then flags only the excess those conditions do not account for.")

    rng = np.random.default_rng(7)
    # learn "normal" from a clean history: energy depends on load and ambient
    n_tr = 500
    load_tr = rng.uniform(30, 100, n_tr)
    amb_tr = rng.uniform(12, 38, n_tr)
    en_tr = _energy_for(0.05, load_tr, 8.0, amb_tr) + rng.normal(0, 1.5, n_tr)
    # load, load² and ambient — the shape of "normal" the plant already knows about
    lin = LinearRegression().fit(np.c_[load_tr, load_tr ** 2, amb_tr], en_tr)

    hours = 480
    th = np.arange(hours)
    load = 65 + 22 * np.sin(2 * np.pi * th / 24.0) + rng.normal(0, 2.0, hours)   # shift pattern
    amb = 24 + 9 * np.sin(2 * np.pi * (th - 6) / 24.0) + rng.normal(0, 1.0, hours)  # day/night
    kwh = _energy_for(0.05, load, 8.0, amb) + rng.normal(0, 1.6, hours)

    c = st.columns(2)
    inject = c[0].toggle("Inject a compressed-air leak (real waste)", value=True)
    onset = c[1].slider("Hour it begins", 120, 400, 240, 10)
    if inject:
        extra = 42.0 * np.clip((th - onset) * 0.0025, 0, 0.55)   # a slowly opening leak
        kwh = kwh + extra

    expected = lin.predict(np.c_[load, load ** 2, amb])
    resid = kwh - expected
    sigma = float(np.std(resid[:100])) or 1.0
    thr = 3.0 * sigma
    alarm = np.where(resid > thr)[0]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=th, y=kwh, mode="lines", name="metered kWh",
                             line=dict(color=POS, width=2)))
    fig.add_trace(go.Scatter(x=th, y=expected, mode="lines", name="expected for load & weather",
                             line=dict(color=MUTED, width=2, dash="dash")))
    fig.update_layout(title="metered consumption vs what the conditions predict (press Play)")
    fig.update_xaxes(title="hour"); fig.update_yaxes(title="kWh per hour")
    ks = sorted(set(list(range(2, hours + 1, 16)) + [hours]))
    frames = [go.Frame(data=[
        go.Scatter(x=th[:k], y=kwh[:k], mode="lines", line=dict(color=POS, width=2)),
        go.Scatter(x=th[:k], y=expected[:k], mode="lines",
                   line=dict(color=MUTED, width=2, dash="dash"))]) for k in ks]
    style(fig, 380); animate(fig, frames, ms=40)
    st.plotly_chart(fig, use_container_width=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=th, y=resid, marker_color=np.where(resid > thr, RED, POS),
                          showlegend=False))
    fig2.add_hline(y=thr, line=dict(color=RED, width=1.5, dash="dash"),
                   annotation_text=f"alarm at 3σ = {thr:.1f} kWh")
    fig2.update_layout(title="residual = metered − expected (near zero when normal)")
    fig2.update_xaxes(title="hour"); fig2.update_yaxes(title="unexplained kWh")
    st.plotly_chart(style(fig2, 340), use_container_width=True)

    m1, m2, m3 = st.columns(3)
    if len(alarm):
        lost = float(np.sum(np.clip(resid[int(alarm[0]):], 0, None)))
        m1.metric("Anomaly first flagged", f"hour {int(alarm[0])}")
        m2.metric("Hours over threshold", len(alarm), delta_color="inverse")
        m3.metric("Unexplained energy since", f"{lost:,.0f} kWh",
                  f"{lost * GRID_KG / 1000:.1f} t CO₂", delta_color="inverse")
        st.error(f"The raw consumption never left its daily band, so a fixed kWh alarm would have stayed "
                 f"silent through the whole shift pattern. The **residual** — what load and weather cannot "
                 f"explain — crosses the line at hour {int(alarm[0])}. That is the leak, caught inside "
                 f"normal-looking operation.")
    else:
        m1.metric("Anomaly flagged", "none")
        m2.metric("Hours over threshold", 0)
        m3.metric("Unexplained energy", "0 kWh")
        st.success("The residual stays near zero: every swing in consumption is explained by load and "
                   "weather. Nothing anomalous — which is what most shifts should look like.")
    st.info("A fixed kWh threshold either trips on every hot afternoon or hides a leak inside a busy shift. "
            "Learning normal-for-the-conditions and scoring the residual separates the two. That is anomaly "
            "detection — the early-warning branch of the monitor.")


def render_optimize():
    st.title("㉖ The efficient operating point")
    st.caption("Sweep the machine load, predict the energy at each setting, and read off where the kilowatt-"
               "hours per unit are lowest. The greenest setting is a minimum on a curve, not the bottom of "
               "the dial.")

    d = get_data()
    en_m, _ = get_regressors()
    c = st.columns(3)
    waste = c[0].slider("Hidden waste (leaks, lagging)", 0.0, 0.9, 0.25, 0.05)
    idle = c[1].slider("Idle share (%)", 0, 35, 8, 1)
    amb = c[2].slider("Ambient (°C)", 12, 38, 24, 1)

    loads = np.linspace(30, 100, 71)
    rows = _signals_for(np.full_like(loads, waste), loads,
                        np.full_like(loads, float(idle)), np.full_like(loads, float(amb)))
    kwh = en_m.predict(d["scaler"].transform(rows))
    units = _units_for(loads, float(idle))
    spec = kwh / np.clip(units, 1e-6, None)
    co2_per_unit = _co2_for(kwh, rows[:, FEATURES.index("material_kg")]) / np.clip(units, 1e-6, None)
    best = int(np.argmin(spec))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=loads, y=spec, mode="lines", line=dict(color=POS, width=3),
                             name="kWh per unit"))
    fig.add_trace(go.Scatter(x=[loads[best]], y=[spec[best]], mode="markers",
                             marker=dict(size=16, color=GREEN, symbol="star"),
                             name="efficient point"))
    fig.add_hline(y=SPEC_LIMIT, line=dict(color=RED, width=2, dash="dash"),
                  annotation_text=f"wasteful above {SPEC_LIMIT:.2f} kWh/unit",
                  annotation_position="top left")
    fig.update_layout(title="specific energy across the operating range (press Play)")
    fig.update_xaxes(title="machine load (%)"); fig.update_yaxes(title="kWh per unit")
    style(fig, 400); animate(fig, _line_grow(loads, spec, POS), ms=45)
    st.plotly_chart(fig, use_container_width=True)

    m = st.columns(4)
    m[0].metric("Efficient load", f"{loads[best]:.0f} %")
    m[1].metric("At that point", f"{spec[best]:.2f} kWh/unit")
    m[2].metric("CO₂ per unit there", f"{co2_per_unit[best]:.2f} kg")
    m[3].metric("Worst point on the curve", f"{spec.max():.2f} kWh/unit",
                f"+{(spec.max()/spec[best]-1)*100:.0f}% vs best", delta_color="inverse")

    st.markdown("##### What the curve is telling you")
    st.markdown(f"""
- At low load the plant still pays its **baseload** — lighting, ventilation, standby compressors — and
  spreads it across very few units. Energy per unit is high even though total kWh is low.
- As load rises, each unit carries less of that fixed cost, so the curve falls.
- Push further and **losses start growing faster than output**: drives run past their best-efficiency
  point, cooling load rises, scrap goes up. The curve turns back upward.
- Those two effects give a **minimum**, here at about **{loads[best]:.0f}% load**.
- Raise the hidden waste slider and the whole curve lifts: a leak taxes every unit produced, no matter how
  well the line is scheduled. The efficient point also drifts towards **higher** load, because there is now
  more fixed cost to spread. The curve is a model prediction, so read the trend rather than the exact
  percent.
    """)
    st.success("Two separate recommendations come out of this page: **run at the efficient point**, and "
               "**fix the waste that lifts the whole curve**. The dashboard prices both.")


# ============================================================================
# THE BUSINESS CASE
# Every number below is arithmetic on assumptions the student sets. None of it
# is a measurement, and the AI bar never reaches zero.
# ============================================================================
def render_dashboard():
    st.title("㉚ The sustainability dashboard")
    st.caption("Everything above becomes three numbers a plant manager can approve: kilowatt-hours, tonnes "
               "of CO₂, and money. Change the assumptions and watch the case move.")

    c = st.columns(3)
    machines = c[0].slider("Metered machines on site", 4, 60, 18, 1)
    tariff = c[1].slider("Electricity tariff (currency / kWh)", 0.06, 0.40, 0.16, 0.01)
    fixed = c[2].slider("Share of identified waste actually fixed (%)", 10, 90, 55, 5)

    # --- the arithmetic, all of it on the assumptions above ------------------
    HOURS = 24 * 30                          # a month of three-shift operation
    kwh_per_machine_hour = 130.0             # typical metered draw per machine hour
    waste_share = 0.14                       # of consumption, identifiable as avoidable waste

    baseline_kwh = machines * kwh_per_machine_hour * HOURS
    avoidable_kwh = baseline_kwh * waste_share
    saved_kwh = avoidable_kwh * fixed / 100.0
    ai_kwh = baseline_kwh - saved_kwh

    saved_co2_t = saved_kwh * GRID_KG / 1000.0
    saved_cost = saved_kwh * tariff
    pct = saved_kwh / baseline_kwh * 100.0

    k = st.columns(4)
    k[0].metric("Energy avoided", f"{saved_kwh/1000:,.0f} MWh / month")
    k[1].metric("Carbon avoided", f"{saved_co2_t*12:,.0f} t CO₂ / year")
    k[2].metric("Cost avoided", f"{saved_cost:,.0f} / month")
    k[3].metric("Consumption removed", f"{pct:.1f} %")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Before — manual monthly review", "After — continuous monitoring"],
                         y=[baseline_kwh / 1000, ai_kwh / 1000],
                         marker_color=[RED, GREEN],
                         text=[f"{baseline_kwh/1000:,.0f} MWh", f"{ai_kwh/1000:,.0f} MWh"],
                         textposition="outside"))
    fig.update_layout(title="monthly plant consumption, before and after", showlegend=False)
    fig.update_yaxes(title="MWh per month")
    style(fig, 380)
    animate(fig, _bars_grow([dict(x=["Before — manual monthly review", "After — continuous monitoring"],
                                  y=[baseline_kwh / 1000, ai_kwh / 1000], color=GREEN,
                                  text=[f"{baseline_kwh/1000:,.0f} MWh",
                                        f"{ai_kwh/1000:,.0f} MWh"])]), ms=90)
    st.plotly_chart(fig, use_container_width=True)

    st.info(f"With **{machines} machines**, **{fixed}%** of the identified waste actually fixed, and a "
            f"tariff of **{tariff:.2f}/kWh**, the plant keeps **{saved_cost:,.0f} per month** and avoids "
            f"**{saved_co2_t*12:,.0f} tonnes of CO₂ a year** — about **{pct:.1f}%** of its consumption.")
    st.warning("**Read the assumptions, not just the total.** Every figure here is arithmetic on the three "
               "sliders — none of it is a measurement. The 'after' bar never reaches zero and never will: "
               "the plant still has to make product, and only part of the waste it finds is economic to "
               "fix. A recommendation that nobody acts on saves nothing at all.")


# ============================================================================
# THE COURSE, AS ONE SUSTAINABLE-MANUFACTURING PROGRAMME
# bridge.open_page() puts the manufacturing context, challenge and AI connection
# ABOVE each renderer; bridge.close_page() puts the notebook connection BELOW.
# ============================================================================
STAGES = {
    "start":           ("⓪ The project — read this first",
                        lambda: bridge.render_start(style, animate)),
    # PHASE 1 — why sustainable manufacturing needs AI
    "in-production":   ("① A plant under load", lambda: story.render_in_production(style, animate)),
    "enter-ai":        ("② The sustainability monitor", lambda: story.render_enter_ai(style, animate)),
    # PHASE 2 — one production hour
    "reading":         ("③ One production hour", lambda: story.render_reading(get_data, style, animate)),
    "two-records":     ("④ Reading vs thermal frame", lambda: story.render_two_records(style, animate)),
    # PHASE 3 & 4 — instrumenting and preparing the data
    "load":            ("⑤ The energy log arrives", render_load),
    "inspect":         ("⑥ Meter health check", render_inspect),
    "clean":           ("⑦ Dropouts & stuck meters", render_clean),
    "normalize":       ("⑧ One common scale", render_normalize),
    "split":           ("⑨ Known vs sealed", render_split),
    # PHASE 5 — energy from the readings
    "ml-baseline":     ("⑩ Energy from the readings", render_ml_baseline),
    "drivers":         ("⑪ What drives the bill", render_drivers),
    # PHASE 6 — the image that makes DL inevitable
    "thermal-problem": ("⑫ The raw thermal frame", lambda: story.render_thermal_problem(style, animate)),
    "handmade":        ("⑬ Mean temperature by hand", lambda: story.render_handmade(style, animate)),
    "why-dl":          ("⑭ Therefore deep learning", lambda: story.render_why_dl(style)),
    # PHASE 7 — how a machine learns
    "engineer-brain":  ("⑮ The auditor's judgement", lambda: story.render_engineer_brain(style)),
    "neuron":          ("⑯ The neuron", render_neuron),
    "activation":      ("⑰ Activation", render_activation),
    "learning-loop":   ("⑱ The learning loop", lambda: story.render_learning_loop(style, animate)),
    "gradient-descent": ("⑲ Loss & gradient descent", render_gradient_descent),
    "network":         ("⑳ The network", render_network),
    "training":        ("㉑ Training", render_training),
    # PHASE 8 — reading the heat pattern
    "cnn-journey":     ("㉒ Inside the CNN", lambda: story.render_cnn_journey(style, animate)),
    # PHASE 9 — locating the loss
    "leak-locate":     ("㉓ Locating the loss", lambda: story.render_leak_locate(style, animate)),
    # PHASE 10 — the sustainability audit
    "audit":           ("㉔ The energy audit",
                        lambda: story.render_audit(get_data, get_models, style, animate)),
    "proof":           ("㉕ The verdict", render_proof),
    # PHASE 11 — prediction & optimisation
    "anomaly":         ("㉖ Normal vs excess", render_anomaly),
    "optimize":        ("㉗ The efficient operating point", render_optimize),
    "fusion-engine":   ("㉘ The sustainability screen", lambda: story.render_fusion_engine(style)),
    "pipeline":        ("㉙ The whole system", lambda: story.render_pipeline(style, animate)),
    # PHASE 12 — the business case
    "dashboard":       ("㉚ The sustainability dashboard", render_dashboard),
}

ALIASES = {"overview": "in-production", "two-signals": "two-records",
           "fusion": "fusion-engine", "energy": "ml-baseline",
           "thermal": "thermal-problem", "gradcam": "leak-locate",
           "monitor": "enter-ai", "importance": "drivers",
           "sweet-spot": "optimize", "cnn": "cnn-journey"}

stage = st.query_params.get("stage", "start")
stage = ALIASES.get(stage, stage)
if stage not in STAGES:
    stage = "start"

with st.sidebar:
    st.markdown("### 🏭 A Sustainability Problem")
    st.caption("You are making a factory measurably greener, and AI keeps turning out to be the thing that "
               "covers the watch one engineer cannot keep across three shifts.")
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
            f"<span style='color:#8b949e'>MANUFACTURING STEP</span><br>"
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
