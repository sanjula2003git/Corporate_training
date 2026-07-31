"""
AI for Traffic Signal Optimization - Deep Learning illustration app
===================================================================
One project, 29 stage pages, taught as one signal-optimisation scheme.
Each notebook step links here with ?stage=<id>.

Dark canvas, animated Plotly (press Play) + interactive sliders/toggles.
Every page: traffic activity -> engineering challenge -> AI concept ->
technical illustration -> notebook connection.

The problem: a junction runs one fixed plan while demand moves all day.
Instrument it, and learn to predict, explain and reduce its delay.
  Detectors : count, speed, occupancy, heavy share, green, cycle, hour,
              rain, pedestrian calls.
  ML        : predict the cycle's delay and queue; flag a congested cycle.
  DL        : grade a CCTV frame, locate the queue (Grad-CAM), spot a light bar.
  System    : incident detection + cycle optimisation + adaptive control.

THE INTERSECTION MODEL IS THE NOTEBOOK'S, imported from story.py. Numbers
quoted in Traffic_Signal_Optimization_DL.ipynb and numbers on the matching app
page therefore agree.
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

# the nine detector channels — order matches story.render_reading exactly
FEATURES = ["vehicle_count", "avg_speed_kmh", "occupancy_pct", "heavy_veh_pct",
            "green_time_s", "cycle_time_s", "hour_of_day", "rain_mm", "ped_calls"]
NICE = ["Vehicles/cycle", "Speed (km/h)", "Occupancy (%)", "Heavy veh (%)",
        "Green (s)", "Cycle (s)", "Hour", "Rain (mm)", "Ped calls"]

# every junction constant comes from story.py, which is a copy of the notebook's
SAT_FLOW, LANES = story.SAT_FLOW, story.LANES
LOST_TOTAL = story.LOST_TOTAL
C_MIN, C_MAX = story.C_MIN, story.C_MAX
LOS_LIMIT = story.LOS_LIMIT
IDLE_L_S, CO2_PER_L = story.IDLE_L_S, story.CO2_PER_L
FIXED_C, FIXED_G = story.FIXED_C, story.FIXED_G

st.set_page_config(page_title="AI for Traffic Signal Optimization", page_icon="🚦",
                   layout="wide")
bridge.inject_css()


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


def signals_for(demand, green, cycle, heavy_pct, rain_mm, hour, ped_calls, block=1.0):
    """The nine detector channels, noise-free. Column order == FEATURES.

    Speed and occupancy are CONSEQUENCES of saturation, not independent inputs.
    That is exactly why they are the two channels the model leans on hardest.
    """
    demand = np.asarray(demand, float)
    _, X, _ = story.delay_for(demand, green, cycle, heavy_pct, rain_mm, ped_calls, block)
    count = demand * np.asarray(cycle, float) / 3600.0
    speed = np.clip(52.0 - 30.0 * np.minimum(X, 1.3) ** 1.6 - 0.5 * np.asarray(rain_mm, float),
                    5.0, 60.0)
    occ = np.clip(8.0 + 62.0 * np.minimum(X, 1.3), 0.0, 95.0)
    return np.stack(np.broadcast_arrays(count, speed, occ,
                                        np.asarray(heavy_pct, float),
                                        np.asarray(green, float),
                                        np.asarray(cycle, float),
                                        np.asarray(hour, float),
                                        np.asarray(rain_mm, float),
                                        np.asarray(ped_calls, float)), axis=-1)


# ----------------------------------------------------------------------------
# DATA  (the controller's log export — same generator as the notebook)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_data():
    rng = np.random.default_rng(42)
    n = 1600
    hour = rng.uniform(0, 24, n)
    demand = np.clip(story.demand_for(hour) * rng.normal(1.0, 0.12, n), 60, None)
    cycle = rng.uniform(60, 130, n)
    # the share of the available green this approach was given, across every plan
    # ever run here — that variation is what teaches the model green is a lever
    green = (cycle - LOST_TOTAL) * rng.uniform(0.25, 0.58, n)
    heavy = rng.uniform(2, 18, n)
    rain = np.where(rng.random(n) < 0.25, rng.uniform(0, 12, n), 0.0)
    ped = rng.integers(0, 9, n).astype(float)

    b = signals_for(demand, green, cycle, heavy, rain, hour, ped)
    dl, X, cap = story.delay_for(demand, green, cycle, heavy, rain, ped)
    qm = story.queue_for(demand, green, cycle, X, ped)

    df = pd.DataFrame({
        "cycle_id": np.arange(1, n + 1),
        "vehicle_count": np.clip(b[:, 0] + rng.normal(0, 1.4, n), 0, None).round(1),
        "avg_speed_kmh": np.clip(b[:, 1] + rng.normal(0, 1.8, n), 0, None).round(1),
        "occupancy_pct": np.clip(b[:, 2] + rng.normal(0, 2.5, n), 0, 100).round(1),
        "heavy_veh_pct": b[:, 3].round(1),
        "green_time_s": b[:, 4].round(1),
        "cycle_time_s": b[:, 5].round(1),
        "hour_of_day": b[:, 6].round(2),
        "rain_mm": b[:, 7].round(1),
        "ped_calls": b[:, 8].round(0),
    })
    df["queue_length_m"] = np.clip(qm + rng.normal(0, 3.0, n), 0, None).round(1)
    df["avg_wait_s"] = np.clip(dl + rng.normal(0, 2.5, n), 0, None).round(1)
    df["congested"] = (df.avg_wait_s > LOS_LIMIT).astype(int)

    # the faults every real controller export carries
    dirty = df.copy()
    for c in FEATURES:
        dirty.loc[rng.choice(n, int(0.06 * n), replace=False), c] = np.nan
    dirty.loc[rng.choice(n, 14, replace=False), "occupancy_pct"] = 100.0   # loop stuck ON
    dirty.loc[rng.choice(n, 11, replace=False), "avg_speed_kmh"] = 255.0   # radar 'no data'
    dirty.loc[rng.choice(n, 12, replace=False), "vehicle_count"] = 9999.0  # counter rollover
    dirty.loc[rng.choice(n, 10, replace=False), "green_time_s"] = 0.0      # log gap
    dirty = pd.concat([dirty, dirty.sample(20, random_state=4)], ignore_index=True)

    clean = dirty.drop_duplicates().copy()
    clean.loc[clean.vehicle_count > 500, "vehicle_count"] = np.nan
    clean.loc[clean.avg_speed_kmh > 120, "avg_speed_kmh"] = np.nan
    clean.loc[clean.occupancy_pct >= 99.5, "occupancy_pct"] = np.nan
    clean.loc[clean.green_time_s <= 0.5, "green_time_s"] = np.nan
    for c in FEATURES:
        clean[c] = clean[c].fillna(clean[c].median())

    scaler = MinMaxScaler()
    norm = clean.copy()
    norm[FEATURES] = scaler.fit_transform(clean[FEATURES])

    Xall = norm[FEATURES].values
    ycong = norm["congested"].values
    ywait = norm["avg_wait_s"].values
    yqueue = norm["queue_length_m"].values

    idx = np.arange(len(Xall))
    itr, itmp = train_test_split(idx, test_size=0.30, random_state=42, stratify=ycong)
    ival, ite = train_test_split(itmp, test_size=0.50, random_state=42, stratify=ycong[itmp])

    return dict(truth=df, dirty=dirty, clean=clean, norm=norm, scaler=scaler,
                Xtr=Xall[itr], Xval=Xall[ival], Xte=Xall[ite],
                ytr=ycong[itr], yval=ycong[ival], yte=ycong[ite],
                WaTr=ywait[itr], WaTe=ywait[ite],
                QuTr=yqueue[itr], QuTe=yqueue[ite])


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
    wa = RandomForestRegressor(n_estimators=200, random_state=42).fit(d["Xtr"], d["WaTr"])
    qu = RandomForestRegressor(n_estimators=200, random_state=42).fit(d["Xtr"], d["QuTr"])
    return wa, qu


@st.cache_data(show_spinner=False)
def best_fixed_plan():
    """The best possible SINGLE fixed plan, by exhaustive search over cycle and
    split, scored on vehicle-weighted junction delay across the whole day.

    The baseline has to be the best fixed plan the junction could run — beating
    a badly tuned plan would prove nothing. This is the search that re-derives
    the installed plan the notebook quotes.
    """
    h = np.arange(0, 24, 0.25)
    dm, dc = story.demand_for(h), story.demand_cross(h)
    veh = dm + dc
    best = (None, None, np.inf)
    for cyc in np.arange(C_MIN, C_MAX + 1, 1.0):
        avail = cyc - LOST_TOTAL
        for gm in np.arange(7.0, avail - 6.0, 1.0):
            d = story.junction_delay(dm, dc, cyc, gm, avail - gm)
            tot = float(np.sum(d * veh))
            if tot < best[2]:
                best = (cyc, gm, tot)
    cyc, gm, tot = best
    return dict(cycle=float(cyc), green_main=float(gm),
                veh_hours=tot * 0.25 / 3600.0, veh=float(np.sum(veh) * 0.25))


# ============================================================================
# TECHNICAL RENDERERS
# ============================================================================
def render_load():
    st.title("③ The controller log arrives")
    d = get_data()
    raw = d["dirty"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Signal cycles logged", f"{len(raw):,}")
    c2.metric("Columns", raw.shape[1])
    c3.metric("Detector channels", len(FEATURES))
    st.caption("The first thing you do with any controller export: check what actually arrived.")
    st.write("")
    st.dataframe(raw.head(8), use_container_width=True, hide_index=True)
    st.info("Types and counts look plausible — but plausible is not verified. The next step inspects the "
            "channels for dropouts and stuck loops before anything is built on them.")


def render_inspect():
    st.title("④ Detector health check")
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
    st.write("")

    col = st.selectbox("Inspect one channel's distribution", FEATURES,
                       format_func=lambda c: NICE[FEATURES.index(c)])
    vals = raw[col].dropna()
    fig2 = go.Figure(go.Histogram(x=vals, nbinsx=50, marker_color=POS))
    fig2.update_layout(title=f"{NICE[FEATURES.index(col)]} — a spike far from the pack is a fault")
    st.plotly_chart(style(fig2, 340), use_container_width=True)
    st.info("A loop stuck ON (100%), a radar writing its no-data sentinel (255 km/h), a counter rollover "
            "(9,999 vehicles) and a controller log gap (0 s of green) all announce themselves here. "
            "Diagnosis only — nothing is repaired yet.")


def render_clean():
    st.title("⑤ Dropouts and stuck loops out")
    d = get_data()
    before, after = len(d["dirty"]), len(d["clean"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows before", f"{before:,}")
    c2.metric("Rows after", f"{after:,}", f"-{before-after} duplicates")
    c3.metric("Missing after", int(d["clean"][FEATURES].isna().sum().sum()))
    st.caption("Impossible readings → removed, then gaps filled with the channel's median.")
    st.write("")
    col = st.selectbox("See a channel before vs after", FEATURES,
                       format_func=lambda c: NICE[FEATURES.index(c)])
    fig = go.Figure()
    fig.add_trace(go.Box(y=d["dirty"][col], name="dirty", marker_color=NEG))
    fig.add_trace(go.Box(y=d["clean"][col], name="clean", marker_color=GREEN))
    fig.update_layout(title=f"{NICE[FEATURES.index(col)]}: the impossible tails are gone")
    st.plotly_chart(style(fig, 380), use_container_width=True)
    st.info("**Why the median, not the mean?** The mean is dragged badly by a single 9,999-vehicle counter "
            "rollover. The median — the middle value — barely notices it, so the filled-in reading stays "
            "physically realistic.")


def render_normalize():
    st.title("⑥ Put every channel on one scale")
    st.info("📐 **Every channel reports in its own unit — vehicles, km/h, percent, seconds, millimetres.** "
            "Put them all on one common 0–1 scale first, so the model compares them fairly instead of "
            "trusting whichever reading happens to have the biggest *number*.")
    st.write("")
    n1, n2, n3 = st.columns(3)
    n1.metric("Cycle time reads", "87 s")
    n2.metric("Occupancy reads", "64 %")
    n3.metric("Rain reads", "3 mm")
    st.caption("Same cycle, same instant. To a raw model, cycle time looks **thirty times more important "
               "than rain** — purely because of its unit, when 3 mm of rain is what just took 8% off the "
               "saturation flow. Press Play to collapse a channel onto 0–1:")
    st.write("")
    d = get_data()
    col = st.selectbox("Channel", FEATURES, index=2,
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
    st.title("⑦ Known cycles vs a sealed set")
    st.info("🧪 **Never test a signal model on the very cycles it was tuned on.** It would just repeat what "
            "it memorised, and you would learn nothing about next week's peak.")
    st.caption("Press Play: the cycles divide into train / validation / test.")
    st.write("")
    d = get_data()
    parts = [("Train", d["ytr"], POS), ("Validation", d["yval"], AMBER), ("Test", d["yte"], GREEN)]
    ok = [int((a == 0).sum()) for _, a, _ in parts]
    bad = [int((a == 1).sum()) for _, a, _ in parts]
    names = [n for n, _, _ in parts]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=names, y=ok, name="coping", marker_color=GREEN))
    fig.add_trace(go.Bar(x=names, y=bad, name="congested", marker_color=RED))
    fig.update_layout(barmode="stack",
                      title="cycles per split (the congestion rate is kept balanced across all three)")
    style(fig, 380)
    animate(fig, _bars_grow([dict(x=names, y=ok, color=GREEN, name="coping"),
                             dict(x=names, y=bad, color=RED, name="congested")]), ms=90)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Train", f"{len(d['ytr'])}")
    c2.metric("Validation", f"{len(d['yval'])}")
    c3.metric("Test (sealed)", f"{len(d['yte'])}")
    st.info("The test cycles are locked away now and only opened at the audit. That is the one fair score "
            "of what the model will do on the junction's next peak.")


def render_ml_baseline():
    st.title("⑧ Delay from the detectors — Random Forest")
    d = get_data()
    wa_m, qu_m = get_regressors()

    st.markdown("##### Predicted vs measured delay, on the sealed cycles")
    pred = wa_m.predict(d["Xte"])
    lo = float(min(d["WaTe"].min(), pred.min())); hi = float(max(d["WaTe"].max(), pred.max()))
    fig = go.Figure(go.Scatter(x=d["WaTe"], y=pred, mode="markers",
                               marker=dict(size=6, color=POS, opacity=0.6, line=dict(width=0))))
    fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines",
                             line=dict(color=MUTED, dash="dash"), showlegend=False))
    fig.update_layout(title="the model has never seen these cycles")
    fig.update_xaxes(title="measured delay (s/veh)"); fig.update_yaxes(title="predicted delay (s/veh)")
    st.plotly_chart(style(fig, 380), use_container_width=True)

    c1, c2 = st.columns(2)
    c1.metric("Delay R² on sealed cycles", f"{r2_score(d['WaTe'], pred):.3f}")
    c2.metric("Queue R² on sealed cycles", f"{r2_score(d['QuTe'], qu_m.predict(d['Xte'])):.3f}")
    st.caption("You never wrote a delay equation. An engineer named the nine channels; the forest learned "
               "the mapping from 1,600 logged cycles.")
    st.write("")

    st.markdown("##### Try a cycle — set the demand and the plan")
    c = st.columns(4)
    hour = c[0].slider("Hour of day", 0.0, 23.75, 18.0, 0.25)
    cyc = c[1].slider("Cycle length (s)", int(C_MIN), int(C_MAX), int(FIXED_C), 1)
    gm = c[2].slider("Green to this approach (s)", 7, 120, int(FIXED_G), 1)
    rain = c[3].slider("Rain (mm)", 0.0, 12.0, 0.0, 0.5)
    c2b = st.columns(2)
    heavy = c2b[0].slider("Heavy vehicles (%)", 2.0, 18.0, 8.0, 0.5)
    ped = c2b[1].slider("Pedestrian calls this cycle", 0, 8, 3, 1)
    gm = min(gm, cyc - LOST_TOTAL - 7)

    demand = float(story.demand_for(hour))
    row = signals_for(np.array([demand]), np.array([float(gm)]), np.array([float(cyc)]),
                      np.array([heavy]), np.array([rain]), np.array([hour]), np.array([float(ped)]))
    row_s = d["scaler"].transform(row)
    dly = float(wa_m.predict(row_s)[0])
    q = float(qu_m.predict(row_s)[0])
    truth, X, cap = story.delay_for(demand, gm, cyc, heavy, rain, ped)
    ok = dly <= LOS_LIMIT
    st.write("")

    m = st.columns(4)
    m[0].metric("Demand at this hour", f"{demand:,.0f} veh/h")
    m[1].metric("Capacity of this approach", f"{float(cap):,.0f} veh/h")
    m[2].metric("Degree of saturation X", f"{float(X):.2f}", "over capacity" if X > 1 else "coping",
                delta_color="off")
    m[3].metric("Predicted queue", f"{q:.0f} m")
    st.write("")
    m2 = st.columns(2)
    m2[0].metric("Predicted delay", f"{dly:.0f} s/veh", f"true {float(truth):.0f}")
    m2[1].metric("LOS E threshold", f"{LOS_LIMIT:.0f} s/veh", delta_color="off")
    st.write("")
    st.markdown(f"<div style='padding:14px;border-radius:4px;text-align:center;font-size:18px;"
                f"font-weight:700;background:{GREEN if ok else RED};color:#0e1117'>"
                f"{'✅ coping — within the level-of-service target' if ok else '❌ congested — LOS E or worse'}"
                f"</div>", unsafe_allow_html=True)
    st.write("")
    st.info("Add rain, or heavy vehicles, and the delay climbs without a single extra vehicle arriving — "
            "because both cut the saturation flow. That is the interaction a spreadsheet formula misses "
            "and the forest learned. The incident detector and the decision engine build on this "
            "prediction.")


def render_drivers():
    st.title("⑨ What drives congestion — feature importance")
    d = get_data()
    wa_m, _ = get_regressors()
    rf, _mlp = get_models()

    which = st.radio("Rank the drivers of…", ["Delay per vehicle", "Whether the cycle was congested"],
                     horizontal=True)
    imp = (wa_m if which.startswith("Delay") else rf).feature_importances_
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
    st.success(f"**{top}** moves the prediction more than anything else. That is where a traffic engineer "
               f"should look first — and it is a claim that can be checked against signal theory.")
    st.write("")

    st.markdown("##### Importance is not proof of cause")
    st.markdown("""
- Occupancy **rises** and speed **falls** as an approach saturates, so both look important. They are two
  views of one condition, not two conditions — and both are *consequences* of saturation, not causes of it.
- Vehicle count is the demand you must serve. It is **not a fault**, and no timing plan makes it go away.
- **Green time and cycle time are the only two channels you can actually change.** That is why they matter
  more than their importance score suggests: a lever with a small coefficient still beats a large
  coefficient you cannot move.
    """)
    st.info("Switch between the two rankings above. The change tells you something real: predicting *how "
            "much* delay is not the same question as predicting *whether the cycle failed*.")


def render_neuron():
    st.title("⑬ The neuron — z = w·x + b")
    st.caption("Set a weight for each channel. The neuron multiplies, sums, adds a bias, and squashes the "
               "result to a probability that the cycle was congested.")
    st.write("")
    d = get_data()
    row = d["norm"].iloc[7]
    x = row[FEATURES].values.astype(float)
    cols = st.columns(len(FEATURES))
    # count, occupancy, heavy and rain push towards congestion; speed and green push away
    default_w = [0.8, -1.0, 1.1, 0.4, -0.9, 0.3, 0.1, 0.5, 0.2]
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
    st.write("")

    fig = go.Figure(go.Bar(x=NICE, y=w * x, marker_color=[POS if v >= 0 else NEG for v in w * x],
                           text=[f"{v:+.2f}" for v in w * x], textposition="outside"))
    fig.update_layout(title=f"each channel's contribution · z = {z:+.2f} → p(congested) = {p:.2f}")
    fig.update_yaxes(title="w × x")
    st.plotly_chart(style(fig, 380), use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Weighted sum z", f"{z:+.2f}")
    c2.metric("After sigmoid", f"{p:.2f}")
    c3.metric("Call", "congested" if p > 0.5 else "coping")
    st.info("Nothing here is mysterious: nine multiplications, a sum, a bias, and a squash. A real network "
            "does not let you set these weights — it learns them from the log, which is the whole point.")


def render_activation():
    st.title("⑭ Activation — turning a sum into a decision")
    st.caption("The weighted sum can be any number. An activation function turns it into something a "
               "controller can act on.")
    st.write("")
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
    st.write("")

    st.markdown("##### Why not a hard threshold?")
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=xs, y=(xs > 0).astype(float), mode="lines",
                              line=dict(color=RED, width=3, shape="hv"), name="hard limit"))
    fig3.add_trace(go.Scatter(x=xs, y=sigmoid(xs), mode="lines",
                              line=dict(color=POS, width=3), name="sigmoid"))
    fig3.update_layout(title="a hard limit has no slope — training has nothing to follow")
    st.plotly_chart(style(fig3, 320), use_container_width=True)
    st.info("Two reasons for the smooth curve. It reports **how confident** the call is, so a borderline "
            "cycle is not treated as a certainty. And it has a **gradient everywhere**, which is what lets "
            "gradient descent work at all.")


def render_gradient_descent():
    st.title("⑯ Loss and gradient descent")
    st.caption("Loss = how wrong. Gradient = which way is better. Learning rate = how big a step.")
    st.write("")
    lr = st.slider("Learning rate (step size)", 0.02, 1.05, 0.25, 0.01)
    xs = np.linspace(-4, 4, 200)
    loss = xs ** 2
    path = [3.6]
    for _ in range(18):
        grad = 2 * path[-1]
        path.append(path[-1] - lr * grad)
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
    style(fig, 380); animate(fig, frames, ms=180)
    st.plotly_chart(fig, use_container_width=True)
    st.info("Too small a step and it crawls; too big and it bounces past the minimum and starts flagging "
            "every quiet cycle. The gradient always points downhill — the art is the step size.")


def render_network():
    st.title("⑰ The network — layered neurons")
    st.caption("One neuron draws one straight line. Layers bend the boundary around real congestion "
               "patterns. Here: occupancy vs speed, with the model's decision surface behind the cycles.")
    st.write("")
    d = get_data()
    depth_opts = {"2 (one tiny layer)": (2,), "6": (6,), "12 → 6": (12, 6), "16 → 8": (16, 8)}
    depth_label = st.select_slider("Hidden layer size", options=list(depth_opts), value="12 → 6")
    depth = depth_opts[depth_label]
    idx = [FEATURES.index("occupancy_pct"), FEATURES.index("avg_speed_kmh")]
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
    fig.update_layout(title="decision surface — red = predicted congested")
    fig.update_xaxes(title="occupancy (scaled)"); fig.update_yaxes(title="average speed (scaled)")
    st.plotly_chart(style(fig, 420), use_container_width=True)
    st.info("With one tiny layer the boundary is nearly straight. Add width and depth and it wraps around "
            "the high-occupancy, low-speed corner — the pattern a single weighted sum cannot hold.")


def render_training():
    st.title("⑱ Training — the loss falls, then flattens")
    st.write("")
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
    fig.add_trace(go.Scatter(y=losses, mode="lines", line=dict(color=POS, width=2), name="training loss"))
    fig.add_trace(go.Scatter(y=val, mode="lines", line=dict(color=AMBER, width=2),
                             name="validation error"))
    frames = [go.Frame(data=[go.Scatter(y=losses[:k + 1], mode="lines", line=dict(color=POS, width=2)),
                             go.Scatter(y=val[:k + 1], mode="lines", line=dict(color=AMBER, width=2))],
                       name=str(k)) for k in range(0, len(losses), 3)]
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
            f"{best} — past that point the network is memorising these cycles rather than learning the "
            "pattern. That turn is where you stop.")


def render_proof():
    st.title("㉓ The verdict — each tool doing the part it is good for")
    st.write("")
    d = get_data()
    wa_m, _ = get_regressors()
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mlp = MLPRegressor(hidden_layer_sizes=(16, 8), max_iter=1200,
                           random_state=0).fit(d["Xtr"], d["WaTr"])
    r_rf = r2_score(d["WaTe"], wa_m.predict(d["Xte"]))
    r_ann = r2_score(d["WaTe"], mlp.predict(d["Xte"]))
    c1, c2 = st.columns(2)
    c1.metric("Random Forest — delay R²", f"{r_rf:.3f}")
    c2.metric("Neural network — delay R²", f"{r_ann:.3f}", f"{r_ann - r_rf:+.3f} vs RF")
    st.write("")
    st.table(pd.DataFrame({
        "": ["Delay & queue from the 9 readings", "Grade a CCTV frame from pixels",
             "Spot a ten-pixel light bar", "Who names the features?"],
        "ML — Random Forest": ["✅ works", "❌ can't even start", "❌ no", "The engineer"],
        "DL — ANN / CNN": ["✅ works", "✅ learns the pattern", "✅ yes", "The network learns them"],
    }))
    st.success("On the nine named channels both tools predict delay about equally well, because the "
               "engineer already named the factors. On the raw camera frame — where nobody can hand-write "
               "the rule — the CNN takes that part off the engineer's plate. AI does not out-think the "
               "engineer here; it just handles the job a person cannot do by hand.")
    st.info("When an engineer has named the features, use machine learning — simpler, faster, easier to "
            "defend at a design review. When nobody can, as with the camera frame, deep learning is the "
            "option that works.")


# ============================================================================
# CONTROL & OPTIMISATION
# ============================================================================
def render_incident():
    st.title("㉔ Normal for this demand — and the excess it cannot explain")
    st.caption("Occupancy is *supposed* to rise at 08:30 and again at 18:00. The monitor learns what "
               "occupancy the demand and the timing plan already explain, then flags only the rest.")
    st.write("")

    rng = np.random.default_rng(7)
    # learn "normal": occupancy as a function of demand and green share
    n_h = 900
    h_h = rng.uniform(0, 24, n_h)
    dm_h = story.demand_for(h_h) * rng.normal(1.0, 0.10, n_h)
    g_h = (FIXED_C - LOST_TOTAL) * rng.uniform(0.4, 0.6, n_h)
    b_h = signals_for(dm_h, g_h, FIXED_C, 8.0, 0.0, h_h, 3.0)
    lin = LinearRegression().fit(np.c_[dm_h, g_h / FIXED_C], b_h[:, 2])

    tq = np.arange(6.0, 21.0, 0.25)
    dm_l = story.demand_for(tq) * rng.normal(1.0, 0.06, len(tq))
    g_l = np.full(len(tq), FIXED_G)
    b_l = signals_for(dm_l, g_l, FIXED_C, 8.0, 0.0, tq, 3.0)
    occ = b_l[:, 2] + rng.normal(0, 1.2, len(tq))

    c = st.columns(2)
    inject = c[0].toggle("Block a lane at 15:00 (a broken-down bus)", value=True)
    severity = c[1].slider("How much of the approach is lost", 0.10, 0.60, 0.35, 0.05)
    if inject:
        blocked = (tq >= 15.0) & (tq <= 17.0)
        b_b = signals_for(dm_l[blocked], g_l[blocked], FIXED_C, 8.0, 0.0, tq[blocked], 3.0,
                          block=1.0 - severity)
        occ[blocked] = b_b[:, 2] + rng.normal(0, 1.2, int(blocked.sum()))

    expected = lin.predict(np.c_[dm_l, g_l / FIXED_C])
    resid = occ - expected
    sigma = float(np.std(resid[tq < 12.0])) or 1.0
    thr = 3.0 * sigma
    alarm = np.where(resid > thr)[0]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tq, y=occ, mode="lines", name="measured occupancy",
                             line=dict(color=POS, width=2.5)))
    fig.add_trace(go.Scatter(x=tq, y=expected, mode="lines", name="expected for the demand",
                             line=dict(color=MUTED, width=2, dash="dash")))
    fig.update_layout(title="the raw occupancy at 15:00 is lower than the evening peak — "
                            "a fixed threshold sees nothing")
    fig.update_xaxes(title="hour of day"); fig.update_yaxes(title="occupancy (%)")
    style(fig, 380); animate(fig, _line_grow(tq, occ, POS), ms=45)
    st.plotly_chart(fig, use_container_width=True)
    st.write("")

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=tq, y=resid, marker_color=np.where(resid > thr, RED, POS), showlegend=False))
    fig2.add_hline(y=thr, line=dict(color=RED, width=1.5, dash="dash"),
                   annotation_text=f"alarm at 3σ = {thr:.1f} points")
    fig2.update_layout(title="residual = measured − expected (near zero when normal)")
    fig2.update_xaxes(title="hour of day"); fig2.update_yaxes(title="unexplained occupancy (points)")
    st.plotly_chart(style(fig2, 340), use_container_width=True)

    m1, m2, m3 = st.columns(3)
    if len(alarm):
        first = float(tq[int(alarm[0])])
        m1.metric("Incident first flagged", f"{first:.2f} h")
        m2.metric("Intervals over threshold", len(alarm), delta_color="inverse")
        m3.metric("Warning before the evening peak", f"{(18.0 - first)*60:.0f} min")
        st.error(f"A fixed occupancy alarm cannot separate these two events: the blockage at 15:00 sits "
                 f"**below** the perfectly normal evening peak. The **residual** asks a different question "
                 f"— not *is this high?* but *is this higher than the demand explains?* — and it crosses "
                 f"the line at {first:.2f} h, {(18.0 - first)*60:.0f} minutes before the evening peak "
                 f"arrives on top of it.")
    else:
        m1.metric("Incident flagged", "none")
        m2.metric("Intervals over threshold", 0)
        m3.metric("Unexplained occupancy", "0 points")
        st.success("The residual stays near zero: every rise in occupancy is explained by the demand and "
                   "the plan. Nothing anomalous — which is what most days should look like.")
    st.info("Set a fixed threshold high enough to ignore the evening peak and it hides the blockage. Set "
            "it low enough to catch the blockage and it cries wolf every weekday at 18:00.")


def render_optimize():
    st.title("㉕ The best cycle length")
    st.caption("Sweep the cycle length, re-split the green by flow ratio at every candidate, and read off "
               "the minimum. The answer changes completely between the night and the evening peak.")
    st.write("")

    hours = [(3.0, GREEN, "03:00 — night"), (9.0, POS, "09:00 — morning peak"),
             (13.0, AMBER, "13:00 — midday"), (18.0, RED, "18:00 — evening peak")]
    fig = go.Figure()
    rows = []
    for hh, col, name in hours:
        dmn, dcr = float(story.demand_for(hh)), float(story.demand_cross(hh))
        cyc, grn, dd = story.delay_vs_cycle(dmn, dcr)
        b = int(np.argmin(dd))
        _, _, Y = story.flow_ratios(dmn, dcr)
        c_web = float(np.clip((1.5 * LOST_TOTAL + 5) / (1 - Y), C_MIN, C_MAX))
        d_web = float(np.interp(c_web, cyc, dd))
        fig.add_trace(go.Scatter(x=cyc, y=dd, mode="lines", name=name, line=dict(color=col, width=2.5)))
        fig.add_trace(go.Scatter(x=[cyc[b]], y=[dd[b]], mode="markers",
                                 marker=dict(size=15, color=col, symbol="star"), showlegend=False))
        rows.append([name, f"{dmn:,.0f} + {dcr:,.0f}", f"{float(Y):.2f}", f"{cyc[b]:.0f} s",
                     f"{grn[b]:.0f} s", f"{dd[b]:.0f} s", f"{c_web:.0f} s",
                     f"+{d_web - dd[b]:.1f} s"])
    fig.add_hline(y=LOS_LIMIT, line=dict(color=RED, width=1.5, dash="dash"),
                  annotation_text=f"congested above {LOS_LIMIT:.0f} s")
    fig.add_vline(x=FIXED_C, line=dict(color=MUTED, width=1.5, dash="dot"),
                  annotation_text=f"the fixed plan ({FIXED_C:.0f} s)", annotation_position="top left")
    fig.update_layout(title="delay across the cycle-length range — the star is the best plan for that hour")
    fig.update_xaxes(title="cycle length (s)")
    fig.update_yaxes(title="junction delay (s/veh)", range=[0, 140])
    st.plotly_chart(style(fig, 430), use_container_width=True)
    st.write("")

    st.dataframe(pd.DataFrame(rows, columns=[
        "Hour", "Demand main + cross (veh/h)", "Y", "Best cycle", "Main green",
        "Delay there", "Webster's C₀", "Webster costs"]),
        use_container_width=True, hide_index=True)
    st.write("")

    st.markdown("##### Read the four curves as a traffic engineer")
    st.markdown(f"""
- **Light demand (night, midday) — the optimum is the shortest legal cycle.** There is no interior minimum:
  with little traffic every extra second of cycle is a second of pointless red, so the curve climbs from
  the left-hand edge. The floor at {C_MIN:.0f} s is not a modelling choice — it is four phases of minimum
  green plus the time a pedestrian needs to cross.
- **Heavy demand (both peaks) — a genuine interior minimum.** Below it, lost time eats so much capacity
  that the approach saturates and delay explodes. Above it, capacity is fine but every red is longer.
- **The regime to watch for.** If **Y** — the sum of the critical flow ratios — approaches 1, the minimum
  runs off to the legal maximum cycle and stays congested there. That junction is **out of capacity**, and
  no timing plan is a solution. The honest report is *"this needs another lane, a different phase order, or
  less traffic"* — not *"we need a longer cycle"*.
- **On Webster's formula.** Compare the two *delay* figures, not the two cycle lengths. Webster's C₀ sits
  up to twenty seconds from the star and still costs under a second of extra delay. The curve is flat near
  its bottom, which is why a closed form from 1958 survived the arrival of computers.
    """)
    st.success(f"The best cycle runs from {C_MIN:.0f} s to over 100 s across a single day — it more than "
               f"doubles. Compare that with the dotted line: the one fixed plan the junction actually runs.")


def render_adaptive():
    st.title("㉖ Fixed-time vs adaptive, over a whole day")
    st.caption("The honest comparison: the best possible fixed plan, found by searching every cycle and "
               "split, against a plan recomputed from the demand at every interval.")
    st.write("")

    h = np.arange(0, 24, 0.25)
    dm, dc = story.demand_for(h), story.demand_cross(h)
    veh = dm + dc
    fixed = best_fixed_plan()

    g_cross_fixed = fixed["cycle"] - LOST_TOTAL - fixed["green_main"]
    d_fixed = story.junction_delay(dm, dc, fixed["cycle"], fixed["green_main"], g_cross_fixed)

    # adaptive: at every interval, sweep the cycle and take the best plan
    cyc_grid = np.linspace(C_MIN, C_MAX, 60)
    d_adapt = np.zeros_like(h)
    c_adapt = np.zeros_like(h)
    g_adapt = np.zeros_like(h)
    for i in range(len(h)):
        gm, gc = story.green_split(dm[i], dc[i], cyc_grid)
        dd = story.junction_delay(dm[i], dc[i], cyc_grid, gm, gc)
        b = int(np.argmin(dd))
        d_adapt[i], c_adapt[i], g_adapt[i] = dd[b], cyc_grid[b], gm[b]

    vh_fixed = float(np.sum(d_fixed * veh) * 0.25 / 3600.0)
    vh_adapt = float(np.sum(d_adapt * veh) * 0.25 / 3600.0)
    cut = (vh_fixed - vh_adapt) / vh_fixed * 100.0

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=h, y=d_fixed, mode="lines", name="best fixed plan",
                             line=dict(color=NEG, width=3)))
    fig.add_trace(go.Scatter(x=h, y=d_adapt, mode="lines", name="adaptive, re-planned each interval",
                             line=dict(color=POS, width=3)))
    fig.add_hline(y=LOS_LIMIT, line=dict(color=RED, width=2, dash="dash"),
                  annotation_text=f"congested above {LOS_LIMIT:.0f} s/veh", annotation_position="top left")
    fig.update_layout(title="junction delay per vehicle through the day")
    fig.update_xaxes(title="hour of day"); fig.update_yaxes(title="seconds per vehicle")
    style(fig, 400); animate(fig, _line_grow(h, d_adapt, POS), ms=45)
    st.plotly_chart(fig, use_container_width=True)

    m = st.columns(4)
    m[0].metric("Best fixed plan found", f"{fixed['cycle']:.0f} s cycle",
                f"{fixed['green_main']:.0f} s main green", delta_color="off")
    m[1].metric("Fixed — delay across the day", f"{vh_fixed:,.0f} veh-h")
    m[2].metric("Adaptive — delay across the day", f"{vh_adapt:,.0f} veh-h",
                f"{vh_adapt - vh_fixed:,.0f} veh-h")
    m[3].metric("Delay reduction", f"{cut:.0f} %")
    st.write("")

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=h, y=np.full(len(h), fixed["cycle"]), mode="lines",
                              name="fixed cycle", line=dict(color=NEG, width=3)))
    fig2.add_trace(go.Scatter(x=h, y=c_adapt, mode="lines", name="adaptive cycle",
                              line=dict(color=POS, width=3)))
    fig2.add_trace(go.Scatter(x=h, y=np.full(len(h), fixed["green_main"]), mode="lines",
                              name="fixed main green", line=dict(color=NEG, width=2, dash="dot")))
    fig2.add_trace(go.Scatter(x=h, y=g_adapt, mode="lines", name="adaptive main green",
                              line=dict(color=AMBER, width=2, dash="dot")))
    fig2.update_layout(title="what the controller actually does")
    fig2.update_xaxes(title="hour of day"); fig2.update_yaxes(title="seconds")
    st.plotly_chart(style(fig2, 360), use_container_width=True)
    st.write("")

    st.info(f"The mechanism is visible in the second chart. Adaptive control runs a **short** cycle at "
            f"night, because a long one is pointless red, and a **long** cycle in the evening peak, "
            f"because lost time is the binding constraint there — and it moves the green between the two "
            f"streets as their ratio changes. A fixed plan can do neither, so it sits between and is wrong "
            f"most of the day. Scored on vehicle-weighted junction delay: a **{cut:.0f}% reduction**.")
    st.warning(f"**Read that figure carefully.** The baseline is already the strongest fixed plan "
               f"available ({fixed['cycle']:.0f} s / {fixed['green_main']:.0f} s, found by exhaustive "
               f"search), which is the fair comparison. But the adaptive side here has a **perfect demand "
               f"forecast** and a two-movement junction. Published results for real adaptive systems "
               f"(SCOOT, SCATS) are typically **10–20%**. The mechanism is real; the exact percentage "
               f"belongs to this model.")


def render_dashboard():
    st.title("㉗ The traffic dashboard")
    st.caption("Everything above becomes three numbers a city can approve: vehicle-hours, fuel and "
               "emissions. Change the assumptions and watch the case move.")
    st.write("")

    h = np.arange(0, 24, 0.25)
    dm, dc = story.demand_for(h), story.demand_cross(h)
    veh = dm + dc
    fixed = best_fixed_plan()
    d_fixed = story.junction_delay(dm, dc, fixed["cycle"], fixed["green_main"],
                                   fixed["cycle"] - LOST_TOTAL - fixed["green_main"])
    cyc_grid = np.linspace(C_MIN, C_MAX, 60)
    d_adapt = np.array([np.min(story.junction_delay(
        dm[i], dc[i], cyc_grid, *story.green_split(dm[i], dc[i], cyc_grid))) for i in range(len(h))])
    cut_model = float((np.sum(d_fixed * veh) - np.sum(d_adapt * veh)) / np.sum(d_fixed * veh) * 100.0)

    c = st.columns(3)
    junctions = c[0].slider("Junctions in the scheme", 1, 120, 25, 1)
    realised = c[1].slider("Share of the modelled saving actually realised (%)", 10, 100, 55, 5)
    value = c[2].slider("Value of time (currency / vehicle-hour)", 4.0, 30.0, 12.0, 0.5)

    # --- the arithmetic, all of it on the assumptions above ------------------
    DAYS = 250                                     # working days per year
    base_vh_day = float(np.sum(d_fixed * veh) * 0.25 / 3600.0)     # per junction per day
    saved_vh_day = base_vh_day * (cut_model / 100.0) * (realised / 100.0)
    base_vh_year = base_vh_day * junctions * DAYS
    saved_vh_year = saved_vh_day * junctions * DAYS

    fuel_l = saved_vh_year * 3600.0 * IDLE_L_S     # litres burned per second of idling
    co2_t = fuel_l * CO2_PER_L / 1000.0
    money = saved_vh_year * value
    pct = saved_vh_year / base_vh_year * 100.0

    k = st.columns(4)
    k[0].metric("Delay avoided", f"{saved_vh_year:,.0f} veh-h / year")
    k[1].metric("Fuel avoided", f"{fuel_l:,.0f} litres / year")
    k[2].metric("Carbon avoided", f"{co2_t:,.0f} t CO₂ / year")
    k[3].metric("Time value kept", f"{money:,.0f} / year")
    st.write("")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Before — one fixed plan", "After — adaptive control"],
                         y=[base_vh_year, base_vh_year - saved_vh_year],
                         marker_color=[RED, GREEN],
                         text=[f"{base_vh_year:,.0f} veh-h",
                               f"{base_vh_year - saved_vh_year:,.0f} veh-h"],
                         textposition="outside"))
    fig.update_layout(title="annual delay across the scheme, before and after", showlegend=False)
    fig.update_yaxes(title="vehicle-hours per year")
    style(fig, 380)
    animate(fig, _bars_grow([dict(x=["Before — one fixed plan", "After — adaptive control"],
                                  y=[base_vh_year, base_vh_year - saved_vh_year], color=GREEN,
                                  text=[f"{base_vh_year:,.0f} veh-h",
                                        f"{base_vh_year - saved_vh_year:,.0f} veh-h"])]), ms=90)
    st.plotly_chart(fig, use_container_width=True)
    st.write("")

    st.info(f"With **{junctions} junctions**, **{realised}%** of the modelled saving actually realised and "
            f"time valued at **{value:.1f} per vehicle-hour**, the scheme keeps **{money:,.0f} a year** and "
            f"avoids **{co2_t:,.0f} tonnes of CO₂** — about **{pct:.1f}%** of the network's delay.")
    st.warning("**Read the assumptions, not just the total.** Every figure here is arithmetic on the three "
               "sliders and on one modelled junction. The 'after' bar never reaches zero and never will: "
               "the junction still has to stop one street to let the other through. The realised share is "
               "the honest part — a scheme commissioned badly saves none of it.")


# ============================================================================
# THE COURSE, AS ONE SIGNAL SCHEME
# ============================================================================
STAGES = {
    "start":            ("⓪ The project — read this first",
                         lambda: bridge.render_start(style, animate)),
    # PHASE 1 — why signal control needs AI
    "in-peak":          ("① A junction under load", lambda: story.render_in_peak(style, animate)),
    # PHASE 2 — one signal cycle
    "reading":          ("② One signal cycle", lambda: story.render_reading(get_data, style, animate)),
    # PHASE 3 & 4 — instrumenting and preparing
    "load":             ("③ The controller log arrives", render_load),
    "inspect":          ("④ Detector health check", render_inspect),
    "clean":            ("⑤ Dropouts & stuck loops", render_clean),
    "normalize":        ("⑥ One common scale", render_normalize),
    "split":            ("⑦ Known vs sealed", render_split),
    # PHASE 5 — delay from the detectors
    "ml-baseline":      ("⑧ Delay from the detectors", render_ml_baseline),
    "drivers":          ("⑨ What drives congestion", render_drivers),
    # PHASE 6 — the image that makes DL inevitable
    "cctv-problem":     ("⑩ The raw CCTV frame", lambda: story.render_cctv_problem(style, animate)),
    "handmade":         ("⑪ Mean brightness by hand", lambda: story.render_handmade(style, animate)),
    # PHASE 7 — how a machine learns
    "operator-brain":   ("⑫ The operator's judgement", lambda: story.render_operator_brain(style)),
    "neuron":           ("⑬ The neuron", render_neuron),
    "activation":       ("⑭ Activation", render_activation),
    "learning-loop":    ("⑮ The learning loop", lambda: story.render_learning_loop(style, animate)),
    "gradient-descent": ("⑯ Loss & gradient descent", render_gradient_descent),
    "network":          ("⑰ The network", render_network),
    "training":         ("⑱ Training", render_training),
    # PHASE 8 — reading the camera
    "cnn-journey":      ("⑲ Inside the CNN", lambda: story.render_cnn_journey(style, animate)),
    # PHASE 9 — locating the queue
    "queue-locate":     ("⑳ Locating the queue", lambda: story.render_queue_locate(style, animate)),
    "emergency":        ("㉑ Emergency preemption", lambda: story.render_emergency(style, animate)),
    # PHASE 10 — the audit
    "audit":            ("㉒ The traffic audit",
                         lambda: story.render_audit(get_data, get_models, style, animate)),
    "proof":            ("㉓ The verdict", render_proof),
    # PHASE 11 — control & optimisation
    "incident":         ("㉔ Normal vs incident", render_incident),
    "optimize":         ("㉕ The best cycle length", render_optimize),
    "adaptive":         ("㉖ Fixed-time vs adaptive", render_adaptive),
    "fusion-engine":    ("㉗ The decision engine", lambda: story.render_fusion_engine(style)),
    "pipeline":         ("㉘ The whole system", lambda: story.render_pipeline(style, animate)),
    # PHASE 12 — the business case
    "dashboard":        ("㉙ The traffic dashboard", render_dashboard),
}

ALIASES = {"overview": "in-peak", "cctv": "cctv-problem", "delay": "ml-baseline",
           "fusion": "fusion-engine", "importance": "drivers", "cnn": "cnn-journey",
           "gradcam": "queue-locate", "anomaly": "incident", "cycle": "optimize",
           "engineer-brain": "operator-brain", "enter-ai": "in-peak"}

stage = st.query_params.get("stage", "start")
stage = ALIASES.get(stage, stage)
if stage not in STAGES:
    stage = "start"

with st.sidebar:
    st.markdown("### 🚦 A Signal Timing Problem")
    st.caption("You are making a junction keep up with its own demand, and AI keeps turning out to be the "
               "thing that covers the watch one engineer cannot keep across every cycle.")
    keys = list(STAGES)
    sel = st.selectbox("Where are we in the scheme?", keys, index=keys.index(stage),
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
            f"<span style='color:#8b949e'>TRAFFIC STEP</span><br>"
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

keys = list(STAGES)
i = keys.index(stage)
nav1, nav2 = st.columns(2)
if i > 0:
    nav1.markdown(f"[← {STAGES[keys[i-1]][0]}](?stage={keys[i-1]})")
if i < len(keys) - 1:
    nav2.markdown(f"<div style='text-align:right'><a href='?stage={keys[i+1]}'>"
                  f"{STAGES[keys[i+1]][0]} →</a></div>", unsafe_allow_html=True)
