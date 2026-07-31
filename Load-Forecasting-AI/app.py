"""
AI for Electricity Load Forecasting - conceptual learning application
=====================================================================
One project, 33 stage pages, taught as one utility load-forecasting project.
Each notebook step corresponds to ?stage=<id> here.

Dark control-room canvas, animated Plotly (press Play) + interactive sliders.
Every page: power system activity -> engineering challenge -> AI connection ->
technical illustration -> notebook connection.

The problem: forecast electricity demand for every hour of tomorrow, tonight,
so the right generators can be committed.
  Inputs : historical demand, temperature, humidity, time of day, day of week,
           holiday indicator.
  Output : forecast demand in MW.
  Models : Linear Regression, Random Forest, Gradient Boosting, XGBoost.

This application is INDEPENDENT of the Colab notebook. It shares the demand
model and the seed, so the numbers agree, but imports nothing from it.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import story
import bridge

# ----------------------------------------------------------------------------
# THEME / PALETTE
# ----------------------------------------------------------------------------
BG, PANEL = "#0b0f14", "#131a22"
CYAN, AMBER = "#4fc3f7", "#ffb74d"
GREEN, RED, TECH = "#66bb6a", "#ef5350", "#ba68c8"
MUTED, TEXT = "#8b98a9", "#e6edf3"

st.set_page_config(page_title="Electricity Load Forecasting - AI",
                   page_icon="⚡", layout="wide")
bridge.inject_css()


def style(fig, h=440):
    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG, font_color=TEXT,
        margin=dict(l=30, r=30, t=60, b=30), height=h,
        template="plotly_dark", legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="#1d2630", zerolinecolor="#2b3743")
    fig.update_yaxes(gridcolor="#1d2630", zerolinecolor="#2b3743")
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


# ============================================================================
# THE DEMAND MODEL  (identical to the notebook, so both deliverables agree)
# ============================================================================
BASE_MW, GROWTH = 620.0, 0.035
COOL_BASE, HEAT_BASE = 24.0, 16.0
HOLIDAYS = {"01-26", "03-08", "03-29", "04-14", "05-01", "08-15",
            "10-02", "10-24", "11-12", "11-13", "12-25"}


def daily_shape(hour, weekend=False):
    h = np.asarray(hour, float)
    morning = 0.14 * np.exp(-((h - 10.0) ** 2) / (2 * 3.2 ** 2))
    evening = 0.36 * np.exp(-((h - 19.5) ** 2) / (2 * 1.8 ** 2))
    night = 0.15 * np.exp(-((h - 3.2) ** 2) / (2 * 2.8 ** 2))
    morning = np.where(weekend, morning * 0.45, morning)
    return 0.86 + morning + evening - night


def cooling_mw(T, H):
    """Air conditioning. Non-linear in temperature, and humidity only matters
    once it is already hot - that interaction is the heart of the problem."""
    cdd = np.clip(np.asarray(T, float) - COOL_BASE, 0, None)
    hum = 1.0 + 0.009 * np.clip(np.asarray(H, float) - 45.0, 0, None)
    return 5.4 * cdd ** 1.32 * hum


def heating_mw(T):
    hdd = np.clip(HEAT_BASE - np.asarray(T, float), 0, None)
    return 3.6 * hdd ** 1.15


def daytype_factor(dayofweek, holiday=0):
    dow = np.asarray(dayofweek)
    f = np.where(dow == 6, 0.875, np.where(dow == 5, 0.945, 1.00))
    return np.where(np.asarray(holiday) == 1, 0.845, f)


def demand_for(hour, T, H, dayofweek=0, holiday=0, years_in=0.0):
    shape = daily_shape(hour, np.asarray(dayofweek) >= 5)
    trend = (1 + GROWTH) ** np.asarray(years_in, float)
    return (BASE_MW * shape * daytype_factor(dayofweek, holiday) * trend
            + cooling_mw(T, H) * (0.80 + 0.20 * shape)
            + heating_mw(T))


F_CALENDAR = ["hour_sin", "hour_cos", "month_sin", "month_cos",
              "dayofweek", "is_weekend", "is_holiday"]
F_WEATHER = ["temperature_c", "humidity_pct", "cdd", "hdd"]
F_LAGS_DA = ["lag_24", "lag_48", "lag_168", "roll24_lag24", "max24_lag24"]
F_LAGS_ST = ["lag_1", "lag_2"]
DAY_AHEAD = F_CALENDAR + F_WEATHER + F_LAGS_DA
SHORT_TERM = DAY_AHEAD + F_LAGS_ST
NO_LAGS = F_CALENDAR + F_WEATHER
TARGET = "demand_mw"

NICE = {"hour_sin": "hour (sin)", "hour_cos": "hour (cos)",
        "month_sin": "month (sin)", "month_cos": "month (cos)",
        "dayofweek": "day of week", "is_weekend": "weekend flag",
        "is_holiday": "holiday flag", "temperature_c": "temperature",
        "humidity_pct": "humidity", "cdd": "cooling degree hrs",
        "hdd": "heating degree hrs", "lag_24": "demand 24 h ago",
        "lag_48": "demand 48 h ago", "lag_168": "demand 1 week ago",
        "roll24_lag24": "yesterday's mean", "max24_lag24": "yesterday's peak",
        "lag_1": "demand 1 h ago", "lag_2": "demand 2 h ago"}

TRAIN_END, VAL_END = "2024-05-01", "2024-07-01"


# ============================================================================
# DATA
# ============================================================================
@st.cache_data(show_spinner="Generating two years of SCADA history…")
def get_data():
    rng = np.random.default_rng(42)
    idx = pd.date_range("2023-01-01", periods=2 * 366 * 24, freq="h")
    idx = idx[idx.year < 2025]
    n = len(idx)

    doy = idx.dayofyear.to_numpy()
    hour = idx.hour.to_numpy().astype(float)
    dow = idx.dayofweek.to_numpy()
    holiday = np.isin(idx.strftime("%m-%d").to_numpy(), list(HOLIDAYS)).astype(int)

    ndays = n // 24 + 1
    anom = np.zeros(ndays)
    for d in range(1, ndays):
        anom[d] = 0.76 * anom[d - 1] + rng.normal(0, 2.1)

    Tm = 27.0 + 9.0 * np.sin(2 * np.pi * (doy - 105) / 365.0)
    T = np.clip(Tm - 5.5 * np.cos(2 * np.pi * (hour - 4) / 24.0)
                + anom[np.arange(n) // 24] + rng.normal(0, 0.6, n), 5.0, 48.0)
    Hm = 56.0 + 23.0 * np.sin(2 * np.pi * (doy - 150) / 365.0)
    H = np.clip(Hm - 0.9 * (T - Tm) + rng.normal(0, 4.0, n), 18.0, 98.0)

    weekend = dow >= 5
    yrs = (idx - idx[0]).days / 365.25
    load = demand_for(hour, T, H, dow, holiday, yrs)
    e = np.zeros(n)
    for t in range(1, n):
        e[t] = 0.72 * e[t - 1] + rng.normal(0, 7.5)

    truth = pd.DataFrame({
        "timestamp": idx, "demand_mw": (load + e).round(1),
        "temperature_c": T.round(1), "humidity_pct": H.round(1),
        "hour": hour.astype(int), "dayofweek": dow, "month": idx.month,
        "is_weekend": weekend.astype(int), "is_holiday": holiday})

    # ---- the export, as the historian actually hands it over ---------------
    r2 = np.random.default_rng(7)
    raw = truth.copy()
    raw.loc[r2.choice(n, 180, replace=False), "demand_mw"] = np.nan
    off = (raw.timestamp >= "2024-05-12") & (raw.timestamp < "2024-05-15")
    raw.loc[off, ["temperature_c", "humidity_pct"]] = np.nan
    fz = raw.index[(raw.timestamp >= "2023-11-06 08:00") & (raw.timestamp < "2023-11-06 22:00")]
    raw.loc[fz, "demand_mw"] = raw.loc[fz[0], "demand_mw"]
    raw.loc[r2.choice(n, 9, replace=False), "demand_mw"] = 9999.0
    raw = pd.concat([raw, raw.sample(24, random_state=3)], ignore_index=True)
    raw = raw.sort_values("timestamp").reset_index(drop=True)

    # ---- cleaning ----------------------------------------------------------
    clean = raw.drop_duplicates(subset="timestamp", keep="first").copy()
    clean.loc[clean.demand_mw > 2000, "demand_mw"] = np.nan
    s = clean.demand_mw
    runs = (s != s.shift()).cumsum()
    frozen = clean.groupby(runs).demand_mw.transform("size") >= 6
    clean.loc[frozen, "demand_mw"] = np.nan
    clean = clean.set_index("timestamp").sort_index().asfreq("h")
    for c in ["demand_mw", "temperature_c", "humidity_pct"]:
        clean[c] = clean[c].interpolate(method="time", limit=6)
    clean = clean.dropna(subset=["demand_mw", "temperature_c", "humidity_pct"])
    clean["hour"] = clean.index.hour
    clean["dayofweek"] = clean.index.dayofweek
    clean["month"] = clean.index.month
    clean["is_weekend"] = (clean.index.dayofweek >= 5).astype(int)
    clean["is_holiday"] = np.isin(clean.index.strftime("%m-%d").to_numpy(),
                                  list(HOLIDAYS)).astype(int)
    clean = clean.reset_index()
    clean["day_type"] = np.where(clean.is_holiday == 1, "Public holiday",
                          np.where(clean.dayofweek == 6, "Sunday",
                            np.where(clean.dayofweek == 5, "Saturday", "Mon-Fri")))

    # ---- features ----------------------------------------------------------
    f = clean.copy()
    f["hour_sin"] = np.sin(2 * np.pi * f.hour / 24)
    f["hour_cos"] = np.cos(2 * np.pi * f.hour / 24)
    f["month_sin"] = np.sin(2 * np.pi * f.month / 12)
    f["month_cos"] = np.cos(2 * np.pi * f.month / 12)
    f["cdd"] = np.clip(f.temperature_c - COOL_BASE, 0, None)
    f["hdd"] = np.clip(HEAT_BASE - f.temperature_c, 0, None)
    for L in (1, 2, 24, 48, 168):
        f[f"lag_{L}"] = f.demand_mw.shift(L)
    f["roll24_lag24"] = f.demand_mw.shift(24).rolling(24).mean()
    f["max24_lag24"] = f.demand_mw.shift(24).rolling(24).max()
    f = f.dropna().reset_index(drop=True)

    train = f[f.timestamp < TRAIN_END]
    val = f[(f.timestamp >= TRAIN_END) & (f.timestamp < VAL_END)]
    test = f[f.timestamp >= VAL_END]
    return dict(truth=truth, raw=raw, clean=clean, feat=f,
                train=train, val=val, test=test)


@st.cache_resource(show_spinner="Training the forecasting models…")
def get_models():
    d = get_data()
    tr, va, te = d["train"], d["val"], d["test"]
    specs = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=300, min_samples_leaf=2,
                                               random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=400, learning_rate=0.06,
                                                       max_depth=4, random_state=42),
    }
    try:
        from xgboost import XGBRegressor
        specs["XGBoost"] = XGBRegressor(n_estimators=600, learning_rate=0.05, max_depth=5,
                                        subsample=0.9, colsample_bytree=0.9,
                                        random_state=42, n_jobs=-1)
    except ImportError:
        pass

    fitted, rows = {}, []
    for nm, m in specs.items():
        m.fit(tr[DAY_AHEAD], tr[TARGET])
        pv = m.predict(va[DAY_AHEAD])
        fitted[nm] = m
        rows.append(dict(model=nm, **metrics(va[TARGET].values, pv)))
    scores = pd.DataFrame(rows).set_index("model")

    best_name = scores.MAE.idxmin()
    best = fitted[best_name]
    bias = float(np.mean(best.predict(va[DAY_AHEAD]) - va[TARGET].values))
    pred = best.predict(te[DAY_AHEAD]) - bias
    pred_raw = best.predict(te[DAY_AHEAD])

    st_model = type(best)(**best.get_params())
    st_model.fit(tr[SHORT_TERM], tr[TARGET])
    st_bias = float(np.mean(st_model.predict(va[SHORT_TERM]) - va[TARGET].values))
    st_pred = st_model.predict(te[SHORT_TERM]) - st_bias

    return dict(fitted=fitted, scores=scores, best_name=best_name, best=best,
                bias=bias, pred=pred, pred_raw=pred_raw,
                st_model=st_model, st_pred=st_pred)


def metrics(y, p):
    y, p = np.asarray(y, float), np.asarray(p, float)
    return dict(MAE=mean_absolute_error(y, p),
                RMSE=float(np.sqrt(mean_squared_error(y, p))),
                MAPE=float(np.mean(np.abs((y - p) / y)) * 100),
                R2=r2_score(y, p), BIAS=float(np.mean(p - y)))


def test_frame():
    """The test period with the corrected forecast and its error attached."""
    d, M = get_data(), get_models()
    t = d["test"].copy()
    t["forecast"] = M["pred"]
    t["err"] = t.forecast - t[TARGET]
    t["abs_err"] = t.err.abs()
    return t


# ============================================================================
# TECHNICAL RENDERERS  (Part 4 of each page)
# ============================================================================
def render_load_data():
    d = get_data()
    raw = d["raw"]
    c = st.columns(4)
    c[0].metric("Rows in the export", f"{len(raw):,}")
    c[1].metric("Hours in the period", f"{17544:,}")
    c[2].metric("Columns", raw.shape[1])
    c[3].metric("Discrepancy", f"+{len(raw)-17544}", delta="unexplained", delta_color="inverse")
    st.caption("The first thing you do with any export: check what actually arrived.")
    st.dataframe(raw.head(8), use_container_width=True, hide_index=True)
    st.info("The row count is already wrong — there are more rows than there are hours in the period "
            "the file covers. Nothing in the file says so. The next page finds out why.")


def render_inspect():
    d = get_data()
    raw = d["raw"]
    miss = raw[["demand_mw", "temperature_c", "humidity_pct"]].isna().sum()
    c = st.columns(4)
    c[0].metric("Missing demand samples", int(miss.demand_mw))
    c[1].metric("Missing weather hours", int(miss.temperature_c))
    c[2].metric("Duplicate timestamps", int(raw.timestamp.duplicated().sum()))
    c[3].metric("Impossible readings", int((raw.demand_mw > 2000).sum()))

    s = raw.demand_mw
    runs = (s != s.shift()).cumsum()
    sizes = s.groupby(runs).size()
    block = raw[runs == sizes.idxmax()]

    which = st.radio("Inspect a fault", ["Frozen meter", "Weather station offline",
                                         "RTU fault codes"], horizontal=True)
    if which == "Frozen meter":
        w = raw[(raw.timestamp >= "2023-11-05") & (raw.timestamp < "2023-11-08")]
        fig = go.Figure(go.Scatter(x=w.timestamp, y=w.demand_mw,
                                   line=dict(color=RED, width=2.5), name="demand"))
        fig.update_layout(title=f"A frozen demand meter — {sizes.max()} identical hours at "
                                f"{block.demand_mw.iloc[0]:.1f} MW")
        st.plotly_chart(style(fig, 400), use_container_width=True)
        st.warning("This is the dangerous one. **Every one of those values passes any range check you "
                   "could write** — they are all perfectly plausible megawatt figures. Only a "
                   "run-length check finds it.")
    elif which == "Weather station offline":
        w = raw[(raw.timestamp >= "2024-05-09") & (raw.timestamp < "2024-05-18")]
        fig = go.Figure(go.Scatter(x=w.timestamp, y=w.temperature_c,
                                   line=dict(color=AMBER, width=2.5), name="temperature"))
        fig.update_layout(title="The weather station offline — 72 consecutive hours, May 2024")
        st.plotly_chart(style(fig, 400), use_container_width=True)
        st.warning("A 72-hour hole. Too long to interpolate across — those hours will be dropped "
                   "rather than invented.")
    else:
        fig = go.Figure(go.Scatter(x=raw.timestamp, y=raw.demand_mw, mode="markers",
                                   marker=dict(size=3, color=CYAN, opacity=0.4), name="demand"))
        fig.add_hline(y=2000, line=dict(color=RED, dash="dash"),
                      annotation_text="network capacity ceiling")
        fig.update_layout(title="Nine readings at 9,999 MW — an RTU fault code passed straight through")
        st.plotly_chart(style(fig, 400), use_container_width=True)
        st.warning("These announce themselves. A network that peaks near 1,180 MW cannot deliver "
                   "9,999 MW — it is a fault code, not a reading.")
    st.info("Diagnosis only. Nothing has been repaired yet — separating the two is what stops you "
            "deleting a real demand event because it looked inconvenient.")


def render_clean():
    d = get_data()
    raw, clean = d["raw"], d["clean"]
    c = st.columns(3)
    c[0].metric("Rows in", f"{len(raw):,}")
    c[1].metric("Rows out", f"{len(clean):,}")
    c[2].metric("Missing values left", int(clean.isna().sum().sum()))

    st.markdown("##### The fill method is the decision, and it is an engineering one")
    med = clean.demand_mw.median()
    at3 = clean[clean.hour == 3].demand_mw.median()
    prof = clean.groupby("hour").demand_mw.median()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=prof.index, y=prof.values, name="actual median demand",
                             line=dict(color=CYAN, width=3)))
    fig.add_hline(y=med, line=dict(color=RED, dash="dash"),
                  annotation_text=f"column median {med:.0f} MW — what a median fill would insert")
    fig.update_layout(title="Why a median fill is wrong for a load series",
                      xaxis_title="hour of day", yaxis_title="demand (MW)")
    st.plotly_chart(style(fig, 400), use_container_width=True)

    c = st.columns(2)
    c[0].metric("Median of the whole column", f"{med:.0f} MW")
    c[1].metric("Median demand at 03:00", f"{at3:.0f} MW",
                delta=f"{med-at3:.0f} MW error at night", delta_color="inverse")
    st.success("Filled **along time** instead: linear interpolation between the surrounding hours, "
               "which respects the load curve. Gaps longer than six hours are dropped rather than "
               "invented — you cannot interpolate across a three-day outage.")


def render_profile():
    d = get_data()
    clean = d["clean"]
    tab1, tab2, tab3 = st.tabs(["Load curve by day type", "Hour × month", "Load duration curve"])

    with tab1:
        fig = go.Figure()
        for dt, col in [("Mon-Fri", CYAN), ("Saturday", AMBER), ("Sunday", GREEN),
                        ("Public holiday", RED)]:
            s = clean[clean.day_type == dt].groupby("hour").demand_mw.mean()
            fig.add_trace(go.Scatter(x=s.index, y=s.values, name=dt, line=dict(color=col, width=3)))
        fig.update_layout(title="Average load curve by day type — two years of history",
                          xaxis_title="hour of day", yaxis_title="mean demand (MW)")
        st.plotly_chart(style(fig, 440), use_container_width=True)
        wk = clean[clean.dayofweek < 5].groupby("hour").demand_mw.mean()
        sun = clean[clean.dayofweek == 6].groupby("hour").demand_mw.mean()
        c = st.columns(3)
        c[0].metric("Weekday evening peak", f"{wk.max():.0f} MW", f"at {wk.idxmax():02d}:00")
        c[1].metric("Sunday evening peak", f"{sun.max():.0f} MW",
                    f"{(sun.max()/wk.max()-1)*100:.0f}% vs weekday")
        c[2].metric("Overnight trough", f"{wk.min():.0f} MW", f"at {wk.idxmin():02d}:00")

    with tab2:
        piv = clean.pivot_table(index="hour", columns="month", values="demand_mw", aggfunc="mean")
        fig = go.Figure(go.Heatmap(z=piv.values, x=piv.columns, y=piv.index,
                                   colorscale="Turbo", colorbar=dict(title="MW")))
        fig.update_layout(title="Mean demand by hour and month — the summer evening block is the problem",
                          xaxis_title="month", yaxis_title="hour of day")
        st.plotly_chart(style(fig, 480), use_container_width=True)
        st.caption("Read the bright block: July–September, 18:00–21:00. That is where the system is "
                   "stressed and where forecast error costs most.")

    with tab3:
        ldc = np.sort(clean.demand_mw.values)[::-1]
        pct = np.arange(1, len(ldc) + 1) / len(ldc) * 100
        top1 = int(len(ldc) * 0.01)
        fig = go.Figure(go.Scatter(x=pct, y=ldc, line=dict(color=CYAN, width=3)))
        fig.add_hline(y=ldc[0], line=dict(color=RED, dash="dash"),
                      annotation_text=f"system peak {ldc[0]:.0f} MW")
        fig.add_hline(y=ldc.mean(), line=dict(color=MUTED, dash="dot"),
                      annotation_text=f"mean {ldc.mean():.0f} MW")
        fig.add_vrect(x0=0, x1=1, fillcolor=RED, opacity=0.15, line_width=0)
        fig.update_layout(title="Load duration curve — every hour of two years, sorted",
                          xaxis_title="% of hours at or above this demand",
                          yaxis_title="demand (MW)")
        st.plotly_chart(style(fig, 440), use_container_width=True)
        c = st.columns(3)
        c[0].metric("System peak", f"{ldc[0]:.0f} MW")
        c[1].metric("Load factor", f"{ldc.mean()/ldc[0]:.3f}", "mean ÷ peak")
        c[2].metric("Capacity used <1% of hours", f"{ldc[0]-ldc[top1]:.0f} MW",
                    f"~{top1/2:.0f} h per year")
        st.info("That last figure is the whole economics of a power system: plant that runs for a few "
                "dozen hours a year still has to be paid for all year.")


def render_weather_link():
    d = get_data()
    clean = d["clean"]
    s = clean.sample(4000, random_state=1)
    fig = go.Figure(go.Scattergl(
        x=s.temperature_c, y=s.demand_mw, mode="markers",
        marker=dict(size=4, color=s.hour, colorscale="Twilight", colorbar=dict(title="hour")),
        hoverinfo="skip", name="hours"))
    bins = np.arange(5, 49, 1.0)
    bm = clean.groupby(pd.cut(clean.temperature_c, bins), observed=True).demand_mw.mean()
    fig.add_trace(go.Scatter(x=bins[:len(bm)] + 0.5, y=bm.values, mode="lines+markers",
                             line=dict(color=RED, width=4), name="mean demand"))
    fig.add_vline(x=HEAT_BASE, line=dict(color=MUTED, dash="dash"),
                  annotation_text=f"heating balance {HEAT_BASE:.0f}°C")
    fig.add_vline(x=COOL_BASE, line=dict(color=MUTED, dash="dash"),
                  annotation_text=f"cooling balance {COOL_BASE:.0f}°C")
    fig.update_layout(title="System demand vs temperature — the V, and its two balance points",
                      xaxis_title="temperature (°C)", yaxis_title="demand (MW)")
    st.plotly_chart(style(fig, 460), use_container_width=True)

    st.markdown("##### The interaction — is humidity worth the same at every temperature?")
    st.caption("Restricted to weekday evening peak hours (17:00–21:00) so the clock is held fixed. "
               "Without that control, humid hours are mostly night hours and the whole effect reverses.")
    ev = clean[(clean.hour >= 17) & (clean.hour <= 21) & (clean.is_weekend == 0)]
    rows = []
    for lo, hi in [(10, 18), (18, 24), (24, 30), (30, 36), (36, 48)]:
        b = ev[(ev.temperature_c >= lo) & (ev.temperature_c < hi)]
        if len(b) < 50:
            continue
        q1, q3 = b.humidity_pct.quantile([0.25, 0.75])
        rows.append(dict(band=f"{lo}–{hi} °C", hours=len(b),
                         low_rh=b[b.humidity_pct <= q1].demand_mw.mean(),
                         high_rh=b[b.humidity_pct >= q3].demand_mw.mean()))
    r = pd.DataFrame(rows)
    r["difference"] = r.high_rh - r.low_rh

    fig = go.Figure(go.Bar(x=r.band, y=r.difference,
                           marker_color=[GREEN if v > 0 else MUTED for v in r.difference],
                           text=[f"{v:+.0f} MW" for v in r.difference], textposition="outside"))
    fig.update_layout(title="Extra demand from high humidity, inside each temperature band",
                      xaxis_title="temperature band", yaxis_title="MW")
    st.plotly_chart(style(fig, 380), use_container_width=True)
    st.success("The same humidity swing is worth almost nothing in the comfort band and tens of "
               "megawatts once it is hot. **That is an interaction** — and it is the clearest single "
               "reason the tree models beat linear regression later.")


def render_calendar_link():
    d = get_data()
    clean = d["clean"]
    ORDER = ["Mon-Fri", "Saturday", "Sunday", "Public holiday"]
    fig = go.Figure()
    for dt, col in zip(ORDER, [CYAN, AMBER, GREEN, RED]):
        fig.add_trace(go.Box(y=clean[clean.day_type == dt].demand_mw, name=dt,
                             marker_color=col, boxmean=True))
    fig.update_layout(title="Demand distribution by day type", yaxis_title="demand (MW)",
                      showlegend=False)
    st.plotly_chart(style(fig, 420), use_container_width=True)

    base = clean[clean.day_type == "Mon-Fri"].demand_mw.mean()
    cols = st.columns(4)
    for col, dt in zip(cols, ORDER):
        v = clean[clean.day_type == dt].demand_mw
        col.metric(dt, f"{v.mean():.0f} MW",
                   f"{(v.mean()/base-1)*100:+.1f}% vs weekday" if dt != "Mon-Fri" else "reference")

    clean = clean.copy()
    clean["week_hour"] = clean.dayofweek * 24 + clean.hour
    wp = clean[clean.is_holiday == 0].groupby("week_hour").demand_mw.mean()
    fig = go.Figure(go.Scatter(x=wp.index, y=wp.values, line=dict(color=CYAN, width=2.5)))
    for dnum, dname in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
        fig.add_vline(x=dnum * 24, line=dict(color="#243039", width=1))
        fig.add_annotation(x=dnum * 24 + 12, y=wp.max() * 1.03, text=dname,
                           showarrow=False, font=dict(size=11, color=MUTED))
    fig.update_layout(title="One average week — the pattern a forecast has to reproduce",
                      xaxis_title="hour of week", yaxis_title="mean demand (MW)")
    st.plotly_chart(style(fig, 400), use_container_width=True)
    st.info(f"Holidays are only **{clean.is_holiday.mean()*100:.1f}%** of all hours — about eleven days "
            "a year. The model sees very few of them, which is exactly why they get an explicit flag "
            "rather than being left to inference.")


def render_degree_hours():
    d = get_data()
    clean, f = d["clean"], d["feat"]
    fig = make_subplots(rows=1, cols=2, subplot_titles=(
        "Raw temperature: a straight line fits badly",
        "Cooling degree hours: the comfort band collapses to zero"))
    bins = np.arange(5, 49, 1.0)
    bm = clean.groupby(pd.cut(clean.temperature_c, bins), observed=True).demand_mw.mean()
    fig.add_trace(go.Scatter(x=bins[:len(bm)] + 0.5, y=bm.values, mode="markers",
                             marker=dict(color=CYAN, size=8)), row=1, col=1)
    cb = np.arange(0, 25, 1.0)
    cm = f.groupby(pd.cut(f.cdd, cb), observed=True).demand_mw.mean()
    fig.add_trace(go.Scatter(x=cb[:len(cm)] + 0.5, y=cm.values, mode="markers",
                             marker=dict(color=AMBER, size=8)), row=1, col=2)
    fig.update_xaxes(title_text="temperature (°C)", row=1, col=1)
    fig.update_xaxes(title_text="cooling degree hours", row=1, col=2)
    fig.update_yaxes(title_text="mean demand (MW)", row=1, col=1)
    fig.update_layout(showlegend=False)
    st.plotly_chart(style(fig, 420), use_container_width=True)

    c = st.columns(3)
    c[0].metric("corr(demand, raw temperature)",
                f"{np.corrcoef(clean.temperature_c, clean.demand_mw)[0,1]:+.3f}")
    c[1].metric("corr(demand, cooling degree hrs)",
                f"{np.corrcoef(f.cdd, f.demand_mw)[0,1]:+.3f}")
    comfort = ((f.cdd == 0) & (f.hdd == 0)).mean() * 100
    c[2].metric("Hours in the comfort band", f"{comfort:.0f}%",
                f"{HEAT_BASE:.0f}–{COOL_BASE:.0f} °C, both features zero")
    st.success("Between the two balance points neither heating nor cooling runs, so demand barely "
               "moves — but raw temperature keeps changing, telling the model something is happening "
               "when nothing is. **Degree hours encode the threshold the engineer already knows.**")


def render_lags():
    d = get_data()
    f = d["feat"]
    maxlag = st.slider("How far back to look (hours)", 48, 336, 192, 24)
    acf = [f.demand_mw.autocorr(lag=k) for k in range(1, maxlag + 1)]
    fig = go.Figure(go.Bar(x=list(range(1, maxlag + 1)), y=acf, marker_color=CYAN))
    for L, lab in [(24, "1 day"), (48, "2 days"), (168, "1 week")]:
        if L <= maxlag:
            fig.add_vline(x=L, line=dict(color=RED, dash="dash"),
                          annotation_text=lab, annotation_position="top")
    fig.update_layout(title="Autocorrelation — how much one hour tells you about a later one",
                      xaxis_title="lag (hours)", yaxis_title="correlation")
    st.plotly_chart(style(fig, 420), use_container_width=True)

    c = st.columns(4)
    for col, L in zip(c, (1, 24, 48, 168)):
        col.metric(f"lag {L} h", f"{f.demand_mw.autocorr(lag=L):+.3f}")
    st.info("The spikes at 24 and 168 hours are the daily and weekly rhythms of the network showing up "
            "as pure arithmetic. Those are the lags worth keeping — and they are what turn a table of "
            "conditions into a **time-series forecasting** problem.")

    st.markdown("##### The features this creates")
    st.dataframe(f[["timestamp", "demand_mw", "lag_1", "lag_24", "lag_168",
                    "roll24_lag24", "max24_lag24"]].head(6).round(1),
                 use_container_width=True, hide_index=True)


def render_split():
    d = get_data()
    tr, va, te, f = d["train"], d["val"], d["test"], d["feat"]
    c = st.columns(3)
    for col, (nm, part, colr) in zip(c, [("Train", tr, CYAN), ("Validation", va, AMBER),
                                         ("Test", te, GREEN)]):
        col.metric(nm, f"{len(part):,} h",
                   f"{part.timestamp.min().date()} → {part.timestamp.max().date()}")

    fig = go.Figure()
    for part, nm, colr in [(tr, "train", CYAN), (va, "validation", AMBER), (te, "test", GREEN)]:
        daily = part.set_index("timestamp").demand_mw.resample("D").max()
        fig.add_trace(go.Scatter(x=daily.index, y=daily.values, name=nm,
                                 line=dict(color=colr, width=1.6)))
    fig.update_layout(title="Daily peak demand — the three periods, in the order they happened",
                      xaxis_title="date", yaxis_title="daily peak (MW)")
    st.plotly_chart(style(fig, 420), use_container_width=True)

    st.markdown("##### What a shuffled split would have told you")
    if st.button("Run both splits and compare", type="primary"):
        with st.spinner("Fitting the same model two ways…"):
            from sklearn.model_selection import train_test_split as _tts
            probe = RandomForestRegressor(n_estimators=120, min_samples_leaf=2,
                                          random_state=42, n_jobs=-1)
            Xs_tr, Xs_te, ys_tr, ys_te = _tts(f[DAY_AHEAD], f[TARGET],
                                              test_size=len(te) / len(f), random_state=42)
            probe.fit(Xs_tr, ys_tr)
            sm = mean_absolute_error(ys_te, probe.predict(Xs_te))
            probe.fit(tr[DAY_AHEAD], tr[TARGET])
            cm = mean_absolute_error(te[TARGET], probe.predict(te[DAY_AHEAD]))
        c = st.columns(2)
        c[0].metric("Random shuffle", f"{sm:.2f} MW", "flattering, and wrong",
                    delta_color="inverse")
        c[1].metric("Chronological", f"{cm:.2f} MW", "what deployment looks like")
        st.error(f"Shuffling makes the same model look **{(1-sm/cm)*100:.0f}% more accurate** than it "
                 f"will be in the control room. It puts 14:00 and 15:00 of the same day on opposite "
                 f"sides of the split — hours that share the weather, the day type and nearly the "
                 f"same demand.")
    else:
        st.caption("Press the button — the gap is not a rounding error.")


def render_scaling():
    d = get_data()
    tr, te = d["train"], d["test"]
    scaler = StandardScaler().fit(tr[DAY_AHEAD])
    raw_lr = LinearRegression().fit(tr[DAY_AHEAD], tr[TARGET])
    scl_lr = LinearRegression().fit(scaler.transform(tr[DAY_AHEAD]), tr[TARGET])
    m_raw = mean_absolute_error(te[TARGET], raw_lr.predict(te[DAY_AHEAD]))
    m_scl = mean_absolute_error(te[TARGET], scl_lr.predict(scaler.transform(te[DAY_AHEAD])))

    c = st.columns(3)
    c[0].metric("Unscaled features", f"{m_raw:.4f} MW")
    c[1].metric("Scaled features", f"{m_scl:.4f} MW")
    c[2].metric("Difference", f"{abs(m_raw-m_scl):.6f} MW")
    st.warning("**Identical, to within floating point.** Rescaling a column rescales its coefficient by "
               "exactly the reciprocal, so plain least squares is unchanged — and a decision tree only "
               "ever asks whether a value is above a threshold. Scaling matters for *regularised* "
               "models, *gradient descent* and *distance-based* methods. Check which case you are in "
               "instead of applying it as a ritual.")

    st.markdown("##### What scaling **is** good for: comparable coefficients")
    coef = pd.DataFrame({"feature": [NICE[f] for f in DAY_AHEAD],
                         "coef": scl_lr.coef_}).sort_values("coef", key=abs, ascending=False)
    fig = go.Figure(go.Bar(x=coef.coef, y=coef.feature, orientation="h",
                           marker_color=[CYAN if c > 0 else AMBER for c in coef.coef],
                           text=[f"{c:+.1f}" for c in coef.coef], textposition="outside"))
    fig.update_layout(title="MW moved per standard deviation of each feature",
                      xaxis_title="MW per standard deviation",
                      yaxis=dict(autorange="reversed"), margin=dict(l=150))
    st.plotly_chart(style(fig, 520), use_container_width=True)


def _model_page(name, extra=None):
    """Shared body for the four model pages: validation score + a week of forecast."""
    d, M = get_data(), get_models()
    if name not in M["fitted"]:
        st.error(f"{name} is not available in this environment (xgboost not installed).")
        return
    m = M["fitted"][name]
    va = d["val"]
    sc = M["scores"].loc[name]
    c = st.columns(4)
    c[0].metric("Validation MAE", f"{sc.MAE:.2f} MW")
    c[1].metric("Validation RMSE", f"{sc.RMSE:.2f} MW")
    c[2].metric("Validation MAPE", f"{sc.MAPE:.2f} %")
    c[3].metric("R²", f"{sc.R2:.4f}")

    pv = m.predict(va[DAY_AHEAD])
    w = va[(va.timestamp >= "2024-05-06") & (va.timestamp < "2024-05-13")]
    i = va.index.get_indexer(w.index)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=w.timestamp, y=w[TARGET], name="actual",
                             line=dict(color=TEXT, width=3)))
    fig.add_trace(go.Scatter(x=w.timestamp, y=pv[i], name=f"{name} forecast",
                             line=dict(color=CYAN, width=2, dash="dash")))
    fig.update_layout(title=f"{name} — one validation week, forecast against outturn",
                      xaxis_title="date", yaxis_title="demand (MW)")
    st.plotly_chart(style(fig, 420), use_container_width=True)
    if extra:
        extra(m, d)


def render_linear():
    def extra(m, d):
        st.markdown("##### Every coefficient, in megawatts per unit")
        co = pd.DataFrame({"feature": [NICE[f] for f in DAY_AHEAD],
                           "MW per unit": m.coef_.round(3)}).sort_values(
            "MW per unit", key=abs, ascending=False)
        st.dataframe(co, use_container_width=True, hide_index=True)
        st.success("You can read every one of these and check it against power system experience. "
                   "That is what makes linear regression the transparent floor — and the gap between "
                   "it and the tree models measures how much of this problem is non-linear.")
    _model_page("Linear Regression", extra)


def render_forest():
    def extra(m, d):
        st.markdown("##### One deliberately tiny tree, so the mechanism is visible")
        from sklearn.tree import DecisionTreeRegressor, export_text
        depth = st.slider("Tree depth", 2, 4, 3)
        demo = DecisionTreeRegressor(max_depth=depth, random_state=42).fit(
            d["train"][DAY_AHEAD], d["train"][TARGET])
        st.code(export_text(demo, feature_names=[NICE[f] for f in DAY_AHEAD], decimals=0))
        st.info("Read any path from top to bottom: it splits on one driver, **then another**. "
                "That nesting is exactly what a single coefficient per feature cannot express — "
                "it is how a tree represents 'it depends'.")
    _model_page("Random Forest", extra)


def render_boosting():
    def extra(m, d):
        st.markdown("##### The correction, stage by stage")
        va = d["val"]
        stages = np.array([mean_absolute_error(va[TARGET], p)
                           for p in m.staged_predict(va[DAY_AHEAD])])
        fig = go.Figure(go.Scatter(x=np.arange(1, len(stages) + 1), y=stages,
                                   line=dict(color=CYAN, width=3)))
        fig.add_hline(y=stages.min(), line=dict(color=GREEN, dash="dot"),
                      annotation_text=f"best {stages.min():.2f} MW at stage {stages.argmin()+1}")
        fig.update_layout(title="Validation error after each boosting stage",
                          xaxis_title="number of trees", yaxis_title="validation MAE (MW)")
        st.plotly_chart(style(fig, 400), use_container_width=True)
        c = st.columns(3)
        c[0].metric("After 1 tree", f"{stages[0]:.1f} MW")
        c[1].metric("After 50 trees", f"{stages[49]:.1f} MW")
        c[2].metric(f"After {len(stages)} trees", f"{stages[-1]:.1f} MW")
        st.info("If this curve turned upward the model would be fitting the measurement noise in the "
                "training years — overfitting, made visible. The learning rate and the tree depth are "
                "what hold it down.")
    _model_page("Gradient Boosting", extra)


def render_xgboost():
    _model_page("XGBoost")
    st.info("Same idea as gradient boosting, with **explicit regularisation** in the objective and "
            "row/column subsampling. Usually a small accuracy gain and a large speed gain — which on "
            "one feeder is a curiosity, and across a few hundred feeders retrained weekly is the "
            "difference between feasible and not.")


def render_compare():
    d, M = get_data(), get_models()
    sc = M["scores"].sort_values("MAE")
    st.markdown("##### Ranked on **validation** — the test set is still closed")
    st.dataframe(sc.round(3), use_container_width=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=sc.index, y=sc.MAE, name="MAE", marker_color=CYAN,
                         text=sc.MAE.round(1), textposition="outside"))
    fig.add_trace(go.Bar(x=sc.index, y=sc.RMSE, name="RMSE", marker_color=AMBER,
                         text=sc.RMSE.round(1), textposition="outside"))
    fig.update_layout(title="Validation error by model — lower is better",
                      yaxis_title="MW", barmode="group")
    st.plotly_chart(style(fig, 420), use_container_width=True)
    st.success(f"Selected on validation: **{M['best_name']}**. Note how close the top two are — on a "
               f"two-month validation window that gap is well inside the noise.")

    st.markdown("##### Now, once: the test set")
    te = d["test"]
    mr = metrics(te[TARGET].values, M["pred_raw"])
    c = st.columns(4)
    c[0].metric("Test MAE", f"{mr['MAE']:.2f} MW")
    c[1].metric("Test RMSE", f"{mr['RMSE']:.2f} MW")
    c[2].metric("Test MAPE", f"{mr['MAPE']:.2f} %")
    c[3].metric("Test bias", f"{mr['BIAS']:+.2f} MW", "consistently LOW", delta_color="inverse")
    st.error("Look at the **bias**, not the MAE. The forecast is not scattered around the truth — it "
             "sits consistently below it, and the offset grows with distance from the training data. "
             "That is a systematic defect, and in this direction it is the expensive one. "
             "**Stage ㉕ diagnoses it.**")


def render_importance():
    d, M = get_data(), get_models()
    from sklearn.inspection import permutation_importance
    va = d["val"]

    @st.cache_data(show_spinner="Scrambling each feature in turn…")
    def _imp():
        pi = permutation_importance(M["best"], va[DAY_AHEAD], va[TARGET], n_repeats=6,
                                    random_state=42, n_jobs=-1,
                                    scoring="neg_mean_absolute_error")
        return pd.DataFrame({"feature": [NICE[f] for f in DAY_AHEAD], "raw": DAY_AHEAD,
                             "MW": pi.importances_mean, "sd": pi.importances_std}
                            ).sort_values("MW", ascending=False).reset_index(drop=True)

    imp = _imp()
    fig = go.Figure(go.Bar(x=imp.MW, y=imp.feature, orientation="h",
                           error_x=dict(array=imp.sd, color=MUTED), marker_color=CYAN,
                           text=imp.MW.round(1), textposition="outside"))
    fig.update_layout(title=f"Permutation importance — extra MW of error when each feature is scrambled",
                      xaxis_title="increase in validation MAE (MW)",
                      yaxis=dict(autorange="reversed"), margin=dict(l=160))
    st.plotly_chart(style(fig, 540), use_container_width=True)

    hrank = int(imp.index[imp.raw == "humidity_pct"][0]) + 1
    c = st.columns(2)
    c[0].metric("Strongest driver", imp.feature.iloc[0], f"{imp.MW.iloc[0]:.1f} MW of damage")
    c[1].metric("Humidity ranks", f"{hrank} of {len(imp)}", "on AVERAGE", delta_color="off")
    st.warning("**Two cautions before reading too much into this ranking.**\n\n"
               "1. It measures what is **irreplaceable**, not what is informative. Cooling degree hours "
               "are computed *from* temperature, and the lag columns all carry the recent level — "
               "scramble one and the model recovers most of it from its neighbours. Correlated features "
               "share, and therefore understate, their importance.\n\n"
               "2. It is an **average over every hour**. Most hours are mild, and humidity then moves "
               "almost nothing. That does not make it unimportant — on the hot evenings when the system "
               "is under strain it is worth tens of megawatts, as the next page shows. "
               "*An average importance hides a driver that only bites at the extremes.*")


def render_sensitivity():
    d, M = get_data(), get_models()
    va = d["val"]
    st.markdown("##### Sweep an input, check the response against the physics")
    c = st.columns(3)
    hour = c[0].slider("Hour of day", 0, 23, 19)
    dow = c[1].selectbox("Day", list(range(7)), index=2,
                         format_func=lambda i: ["Monday", "Tuesday", "Wednesday", "Thursday",
                                                "Friday", "Saturday", "Sunday"][i])
    level = c[2].slider("Recent demand level (MW)", 450, 1000,
                        int(va.roll24_lag24.median()), 10)

    def response(temps, humidity):
        rows = pd.DataFrame({
            "hour_sin": np.sin(2*np.pi*hour/24), "hour_cos": np.cos(2*np.pi*hour/24),
            "month_sin": np.sin(2*np.pi*7/12), "month_cos": np.cos(2*np.pi*7/12),
            "dayofweek": dow, "is_weekend": int(dow >= 5), "is_holiday": 0,
            "temperature_c": temps, "humidity_pct": humidity,
            "cdd": np.clip(temps - COOL_BASE, 0, None),
            "hdd": np.clip(HEAT_BASE - temps, 0, None),
            "lag_24": level, "lag_48": level, "lag_168": level,
            "roll24_lag24": level, "max24_lag24": level * 1.18})
        return M["best"].predict(rows[DAY_AHEAD]) - M["bias"]

    temps = np.linspace(8, 46, 100)
    dry, humid = response(temps, 35.0), response(temps, 85.0)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=temps, y=dry, name="35% RH (dry)", line=dict(color=CYAN, width=3)))
    fig.add_trace(go.Scatter(x=temps, y=humid, name="85% RH (humid)", line=dict(color=RED, width=3)))
    fig.add_trace(go.Scatter(x=np.concatenate([temps, temps[::-1]]),
                             y=np.concatenate([humid, dry[::-1]]),
                             fill="toself", fillcolor="rgba(239,83,80,0.13)",
                             line=dict(width=0), hoverinfo="skip", name="humidity effect"))
    fig.add_vline(x=COOL_BASE, line=dict(color=MUTED, dash="dash"),
                  annotation_text="cooling balance point")
    fig.update_layout(title=f"Temperature response at {hour:02d}:00 — two humidity levels",
                      xaxis_title="temperature (°C)", yaxis_title="forecast demand (MW)")
    st.plotly_chart(style(fig, 460), use_container_width=True)

    rows = []
    for T in (18, 24, 30, 36, 42):
        i = int(np.argmin(np.abs(temps - T)))
        rows.append(dict(temperature=f"{T} °C", dry=f"{dry[i]:.0f} MW",
                         humid=f"{humid[i]:.0f} MW", humidity_worth=f"{humid[i]-dry[i]:+.0f} MW"))
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.success("**The shaded gap is the interaction, recovered from data.** It is near zero through the "
               "comfort band and widens steadily as the temperature climbs. Nobody programmed that in — "
               "the model found it in two years of readings.")
    st.caption("The small negative values in the mild bands are worth understanding rather than "
               "dismissing: in this network humid mild hours are monsoon and overnight hours, which "
               "genuinely run slightly lighter. The model has learnt a real association, not a "
               "physical law.")


def render_bias():
    d, M = get_data(), get_models()
    tr, va, te = d["train"], d["val"], d["test"]
    b_tr = float(np.mean(M["best"].predict(tr[DAY_AHEAD]) - tr[TARGET].values))
    b_va = M["bias"]
    b_te = float(np.mean(M["pred_raw"] - te[TARGET].values))

    fig = go.Figure(go.Bar(x=["Train", "Validation", "Test"], y=[b_tr, b_va, b_te],
                           marker_color=[MUTED, AMBER, RED],
                           text=[f"{v:+.1f} MW" for v in [b_tr, b_va, b_te]],
                           textposition="outside"))
    fig.add_hline(y=0, line=dict(color=TEXT))
    fig.update_layout(title="Mean forecast error by period — it grows with distance from training",
                      yaxis_title="mean error (MW), negative = forecast too low")
    st.plotly_chart(style(fig, 380), use_container_width=True)
    st.error("Zero on training by construction, and growing steadily afterwards. **That is the "
             "signature of distribution shift, not of a badly specified model** — and it affects "
             "linear regression just as much, so it is not a tree-extrapolation problem.")

    st.markdown("##### The cause: the licence area's demand is growing")
    growth = st.slider("Assumed annual load growth (%)", 0.0, 6.0, GROWTH * 100, 0.5)
    yrs = np.linspace(0, 2, 50)
    fig = go.Figure(go.Scatter(x=yrs, y=100 * (1 + growth / 100) ** yrs,
                               line=dict(color=AMBER, width=3)))
    fig.add_vrect(x0=0, x1=1.33, fillcolor=CYAN, opacity=0.10, line_width=0,
                  annotation_text="training period")
    fig.add_vrect(x0=1.5, x1=2.0, fillcolor=GREEN, opacity=0.10, line_width=0,
                  annotation_text="test period")
    fig.update_layout(title="Demand level relative to the start of the record",
                      xaxis_title="years since the record begins", yaxis_title="index (start = 100)")
    st.plotly_chart(style(fig, 360), use_container_width=True)

    st.markdown("##### The tempting fix that does not work")
    dm = tr.set_index("timestamp").demand_mw.resample("D").mean().dropna()
    tyr = (dm.index - dm.index[0]).days / 365.25
    slope = np.polyfit(tyr, np.log(dm.values), 1)[0]
    c = st.columns(2)
    c[0].metric("Trend fitted to the training window", f"{np.expm1(slope)*100:+.2f} %/yr")
    c[1].metric("The utility's actual load growth", f"+{GROWTH*100:.2f} %/yr")
    st.warning("The training window is 16 months, so the **seasonal cycle dominates the fit** and the "
               "trend estimate comes out badly wrong. This is why the correction below is measured as a "
               "*residual on recent data* rather than as a fitted trend.")

    st.markdown("##### The correction: measured on validation, applied to test")
    mr = metrics(te[TARGET].values, M["pred_raw"])
    mf = metrics(te[TARGET].values, M["pred"])
    c = st.columns(4)
    c[0].metric("MAE before", f"{mr['MAE']:.2f} MW")
    c[1].metric("MAE after", f"{mf['MAE']:.2f} MW",
                f"{(1-mf['MAE']/mr['MAE'])*100:.0f}% better")
    c[2].metric("Bias before", f"{mr['BIAS']:+.2f} MW")
    c[3].metric("Bias after", f"{mf['BIAS']:+.2f} MW")

    t = te.copy()
    t["before"], t["after"] = M["pred_raw"] - t[TARGET], M["pred"] - t[TARGET]
    mo = t.groupby(t.timestamp.dt.to_period("M").astype(str))[["before", "after"]].mean()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=mo.index, y=mo.before, name="before correction", marker_color=RED))
    fig.add_trace(go.Bar(x=mo.index, y=mo.after, name="after correction", marker_color=GREEN))
    fig.add_hline(y=0, line=dict(color=TEXT))
    fig.update_layout(title="Mean forecast error by month — a systematic offset, removed",
                      yaxis_title="mean error (MW)", barmode="group")
    st.plotly_chart(style(fig, 380), use_container_width=True)
    st.info("It is a **patch on a real problem, not a cure**. The proper fix is to retrain on recent "
            "data — which is exactly why utilities refit these models every few weeks rather than once. "
            "Critically, the correction is measured on *validation* and applied to *test*; measuring it "
            "on the test set would be marking your own homework.")


def render_metrics():
    d, M = get_data(), get_models()
    te = d["test"]
    mf = metrics(te[TARGET].values, M["pred"])
    pers = metrics(te[TARGET].values, te.lag_24.values)

    c = st.columns(4)
    c[0].metric("MAE", f"{mf['MAE']:.2f} MW", f"{(1-mf['MAE']/pers['MAE'])*100:.0f}% vs persistence")
    c[1].metric("RMSE", f"{mf['RMSE']:.2f} MW", f"{(1-mf['RMSE']/pers['RMSE'])*100:.0f}% vs persistence")
    c[2].metric("MAPE", f"{mf['MAPE']:.2f} %", f"{(1-mf['MAPE']/pers['MAPE'])*100:.0f}% vs persistence")
    c[3].metric("R²", f"{mf['R2']:.4f}")

    st.markdown("| metric | what it is for | why not use it alone |\n|---|---|---|\n"
                "| **MAE** | the operator — the average miss in MW | treats a 200 MW error as ten "
                "times a 20 MW one, when operationally it is far worse |\n"
                "| **RMSE** | reserve sizing — driven by the large misses reserve exists to cover | "
                "harder to interpret, since it is in squared-then-rooted units |\n"
                "| **MAPE** | benchmarking against other utilities | exaggerates errors during the low "
                "overnight hours |\n"
                "| **R²** | the modeller | says nothing about megawatts, and looks good even when the "
                "forecast is biased |")

    err = M["pred"] - te[TARGET].values
    fig = make_subplots(rows=1, cols=2, subplot_titles=(
        "Forecast error distribution", "Forecast vs actual, every test hour"))
    fig.add_trace(go.Histogram(x=err, nbinsx=70, marker_color=CYAN), row=1, col=1)
    fig.add_vline(x=0, line=dict(color=RED, dash="dash"), row=1, col=1)
    s = np.random.default_rng(2).choice(len(te), min(3000, len(te)), replace=False)
    fig.add_trace(go.Scattergl(x=te[TARGET].values[s], y=M["pred"][s], mode="markers",
                               marker=dict(size=4, color=CYAN, opacity=0.5)), row=1, col=2)
    lim = [te[TARGET].min() * 0.95, te[TARGET].max() * 1.02]
    fig.add_trace(go.Scatter(x=lim, y=lim, line=dict(color=RED, dash="dash")), row=1, col=2)
    fig.update_xaxes(title_text="forecast − actual (MW)", row=1, col=1)
    fig.update_xaxes(title_text="actual demand (MW)", row=1, col=2)
    fig.update_yaxes(title_text="forecast demand (MW)", row=1, col=2)
    fig.update_layout(showlegend=False)
    st.plotly_chart(style(fig, 420), use_container_width=True)

    cols = st.columns(4)
    for col, q in zip(cols, (50, 90, 95, 99)):
        col.metric(f"{q}% of hours within", f"{np.percentile(np.abs(err), q):.1f} MW")
    st.info("That 95th-percentile figure is not a statistic for its own sake — it is what sizes the "
            "**operating reserve** in the business case two pages from here.")


def render_error_profile():
    t = test_frame()
    byh = t.groupby("hour").agg(mae=("abs_err", "mean"), mean_mw=(TARGET, "mean"))
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=byh.index, y=byh.mae, name="MAE (MW)", marker_color=CYAN),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=byh.index, y=byh.mean_mw, name="mean demand (MW)",
                             line=dict(color=AMBER, width=3)), secondary_y=True)
    fig.update_layout(title="Forecast error by hour of day — worst where demand is highest",
                      xaxis_title="hour of day")
    fig.update_yaxes(title_text="MAE (MW)", secondary_y=False)
    fig.update_yaxes(title_text="mean demand (MW)", secondary_y=True)
    st.plotly_chart(style(fig, 440), use_container_width=True)

    c = st.columns(3)
    c[0].metric("Easiest hour", f"{byh.mae.idxmin():02d}:00", f"MAE {byh.mae.min():.1f} MW")
    c[1].metric("Hardest hour", f"{byh.mae.idxmax():02d}:00", f"MAE {byh.mae.max():.1f} MW")
    c[2].metric("Peak vs trough", f"{byh.mae.max()/byh.mae.min():.1f}×", "harder to forecast")

    tab1, tab2 = st.tabs(["By day type", "By demand level"])
    with tab1:
        g = t.groupby("day_type").agg(hours=("abs_err", "size"), MAE=("abs_err", "mean"))
        g["MAPE %"] = t.groupby("day_type").apply(
            lambda x: (x.abs_err / x[TARGET]).mean() * 100, include_groups=False)
        st.dataframe(g.round(2), use_container_width=True)
    with tab2:
        t2 = t.copy()
        t2["band"] = pd.qcut(t2[TARGET], 5,
                             labels=["lowest 20%", "low", "middle", "high", "highest 20%"])
        g = t2.groupby("band", observed=True).agg(hours=("abs_err", "size"), MAE=("abs_err", "mean"))
        fig = go.Figure(go.Bar(x=g.index.astype(str), y=g.MAE, marker_color=CYAN,
                               text=g.MAE.round(1), textposition="outside"))
        fig.update_layout(title="Forecast error by demand level", yaxis_title="MAE (MW)")
        st.plotly_chart(style(fig, 360), use_container_width=True)

    peak = t[t[TARGET] >= t[TARGET].quantile(0.90)]
    st.error(f"**The top 10% of hours by demand** ({len(peak)} hours, above "
             f"{t[TARGET].quantile(0.90):.0f} MW): MAE **{peak.abs_err.mean():.1f} MW** against "
             f"{t.abs_err.mean():.1f} MW overall — and they are **under-forecast "
             f"{(peak.err < 0).mean()*100:.0f}% of the time.** "
             f"Under-forecasting the peak is the expensive direction, so quote this number to the "
             f"control room, not the average.")


def render_worst_day():
    t = test_frame()
    daily = t.assign(d=t.timestamp.dt.date).groupby("d").agg(
        mae=("abs_err", "mean"), bias=("err", "mean"), peak=(TARGET, "max"),
        temp=("temperature_c", "mean"), rh=("humidity_pct", "mean"))
    daily["dtemp"] = daily.temp.diff()
    worst = daily.mae.idxmax()
    med = daily.mae.median()

    days = sorted(daily.index)
    pick = st.select_slider(
        "Inspect a day (defaults to the worst in the test period)", options=days,
        value=worst, format_func=lambda x: x.strftime("%d %b %Y"))
    day = t[t.timestamp.dt.date == pick]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=day.hour, y=day[TARGET], name="actual",
                             line=dict(color=CYAN, width=3.5)))
    fig.add_trace(go.Scatter(x=day.hour, y=day.forecast, name="forecast",
                             line=dict(color=RED, width=2.5, dash="dash")))
    fig.add_trace(go.Bar(x=day.hour, y=day.err, name="error", marker_color=AMBER, opacity=0.45))
    fig.update_layout(title=f"{pick} — forecast against outturn, hour by hour",
                      xaxis_title="hour of day", yaxis_title="MW")
    st.plotly_chart(style(fig, 440), use_container_width=True)

    r = daily.loc[pick]
    c = st.columns(4)
    c[0].metric("Daily MAE", f"{r.mae:.1f} MW", f"{r.mae/med:.1f}× the median day")
    c[1].metric("Daily bias", f"{r.bias:+.1f} MW")
    c[2].metric("Mean temperature", f"{r.temp:.1f} °C")
    c[3].metric("Day-on-day swing", f"{r.dtemp:+.1f} °C" if pd.notna(r.dtemp) else "—")

    tq = daily.temp.rank(pct=True).loc[pick] * 100
    cq = daily.dtemp.abs().rank(pct=True).loc[pick] * 100
    st.markdown("##### Was the **day** unusual, or was the **change** unusual?")
    st.caption("These have different fixes. A lag-driven model is hurt by a sharp day-on-day "
               "transition, not by a hot day it has seen many times before.")
    c = st.columns(2)
    c[0].metric("Its own temperature", f"percentile {tq:.0f}")
    c[1].metric("Its day-on-day swing", f"percentile {cq:.0f}")
    if cq > 85:
        st.warning(f"**The day itself was unremarkable — the transition was not.** Temperature moved "
                   f"{r.dtemp:+.1f} °C overnight, so every lag feature the model relies on was "
                   f"describing the previous day. The named next improvement is a feature for the "
                   f"**day-on-day weather change**.")
    elif tq > 90:
        st.warning("A genuinely extreme day, so a larger error is defensible. The answer here is "
                   "better inputs, not a different model.")
    else:
        st.info("An ordinary day and an ordinary transition — the model simply had a bad one. That "
                "points at the feature set rather than at the weather.")

    fig = go.Figure(go.Histogram(x=daily.mae, nbinsx=40, marker_color=CYAN))
    fig.add_vline(x=med, line=dict(color=GREEN, dash="dot"), annotation_text=f"median {med:.1f}")
    fig.add_vline(x=daily.mae.max(), line=dict(color=RED, dash="dash"),
                  annotation_text=f"worst {daily.mae.max():.1f}")
    fig.update_layout(title="Daily mean absolute error across the test period",
                      xaxis_title="daily MAE (MW)", yaxis_title="days")
    st.plotly_chart(style(fig, 360), use_container_width=True)
    st.success(f"The encouraging result is the one that is easy to miss: **there is no catastrophic "
               f"day.** The worst in six months is {daily.mae.max()/med:.1f}× the median, not 10×. A "
               f"system that fails gracefully is worth more to a control room than one with a better "
               f"average and an occasional disaster.")


# ---------------------------------------------------------------------------
# THE INTERACTIVE FORECAST  —  the most important page in the application
# ---------------------------------------------------------------------------
def render_predict():
    d, M = get_data(), get_models()
    te = d["test"]

    st.markdown("##### Set the conditions for the hour you want forecast")
    c = st.columns(3)
    hour = c[0].slider("Time of day", 0, 23, 18, help="The hour being forecast")
    temp = c[1].slider("Temperature (°C)", 8.0, 46.0, 35.0, 0.5)
    hum = c[2].slider("Relative humidity (%)", 20, 98, 72)
    c = st.columns(3)
    dow = c[0].selectbox("Day of week", list(range(7)), index=0,
                         format_func=lambda i: ["Monday", "Tuesday", "Wednesday", "Thursday",
                                                "Friday", "Saturday", "Sunday"][i])
    hol = c[1].radio("Public holiday?", ["No", "Yes"], horizontal=True) == "Yes"
    prev = c[2].slider("Demand at this hour today (MW)", 400, 1200, 820, 10,
                       help="What the system actually drew at this hour today — the lag feature")

    row = pd.DataFrame([{
        "hour_sin": np.sin(2*np.pi*hour/24), "hour_cos": np.cos(2*np.pi*hour/24),
        "month_sin": np.sin(2*np.pi*8/12), "month_cos": np.cos(2*np.pi*8/12),
        "dayofweek": dow, "is_weekend": int(dow >= 5), "is_holiday": int(hol),
        "temperature_c": temp, "humidity_pct": hum,
        "cdd": max(temp - COOL_BASE, 0.0), "hdd": max(HEAT_BASE - temp, 0.0),
        "lag_24": prev, "lag_48": prev, "lag_168": prev,
        "roll24_lag24": prev * 0.92, "max24_lag24": prev * 1.12}])
    mw = float(M["best"].predict(row[DAY_AHEAD])[0]) - M["bias"]
    mae = mean_absolute_error(te[TARGET].values, M["pred"])

    st.markdown("---")
    left, right = st.columns([1.05, 1])
    with left:
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta", value=mw,
            number={"suffix": " MW", "font": {"size": 46}},
            delta={"reference": prev, "suffix": " MW vs today",
                   "increasing": {"color": AMBER}, "decreasing": {"color": CYAN}},
            title={"text": f"Forecast demand at {hour:02d}:00 tomorrow"},
            gauge={"axis": {"range": [400, 1250]},
                   "bar": {"color": CYAN, "thickness": 0.28},
                   "steps": [{"range": [400, 780], "color": "#14301f"},
                             {"range": [780, 900], "color": "#3a3417"},
                             {"range": [900, 1250], "color": "#3d1f1f"}],
                   "threshold": {"line": {"color": RED, "width": 4}, "value": 900}}))
        st.plotly_chart(style(fig, 380), use_container_width=True)
        st.caption("Green = inside committed baseload · amber = ramping territory · "
                   "red = above the peaking trigger (900 MW)")

    with right:
        st.markdown("##### Engineering interpretation")
        notes = []
        if temp > COOL_BASE + 8:
            notes.append(("🌡️", f"**{temp:.0f} °C** drives a heavy cooling load — "
                                f"{temp-COOL_BASE:.0f} degree hours above the balance point."))
        elif temp < HEAT_BASE:
            notes.append(("🔥", f"**{temp:.0f} °C** is below the heating balance point; "
                                f"resistive heating load is switching on."))
        else:
            notes.append(("🌤️", f"**{temp:.0f} °C** sits in the comfort band — little "
                                f"weather-driven load either way."))
        if temp > COOL_BASE + 8 and hum > 65:
            notes.append(("💧", f"**{hum}% humidity** adds to the cooling duty on top of the heat. "
                                f"At a mild temperature this same humidity would be worth almost nothing."))
        if 17 <= hour <= 21:
            notes.append(("📈", "**Evening peak period** — commercial load has not yet gone and "
                                "residential load has arrived."))
        elif hour <= 5:
            notes.append(("🌙", "**Overnight trough** — base load only."))
        else:
            notes.append(("🏭", "**Daytime plateau** — commercial and industrial load dominant."))
        if hol:
            notes.append(("📅", "**Public holiday** — commercial and industrial load largely absent, "
                                "so the day behaves like a Sunday."))
        elif dow == 6:
            notes.append(("📅", "**Sunday** — the lightest day type on this network."))
        elif dow == 5:
            notes.append(("📅", "**Saturday** — a partial working day here."))
        for icon, txt in notes:
            st.markdown(f"{icon} &nbsp; {txt}")

        st.markdown("##### Despatch implication")
        if mw > 900:
            st.error(f"**Prepare peak load units.** {mw:,.0f} MW is above the 900 MW committed-plant "
                     f"trigger. Bring peaking units to standby and hold reserve available.")
        elif mw - prev > 45:
            st.warning(f"**Increase generation capacity.** {mw-prev:+,.0f} MW above today at this hour "
                       f"— schedule additional ramping capacity.")
        elif mw < 480:
            st.info(f"**Charge energy storage / reduce curtailment.** {mw:,.0f} MW is near the must-run "
                    f"minimum; absorb the surplus rather than backing plant down.")
        else:
            st.success(f"**Maintain current generation.** {mw:,.0f} MW is inside committed-plant limits.")
        st.caption(f"Forecast uncertainty: ± {mae:.0f} MW on an average hour "
                   f"(mean absolute error over {len(te):,} unseen test hours). "
                   f"Recommendation only — the despatch engineer commits the schedule.")

    # ---- one variable at a time ------------------------------------------
    st.markdown("---")
    st.markdown("##### What moves the forecast? One variable at a time, from your settings")

    def fc(**kw):
        p = dict(hour=hour, temp=temp, hum=hum, dow=dow, hol=int(hol), prev=prev)
        p.update(kw)
        r = pd.DataFrame([{
            "hour_sin": np.sin(2*np.pi*p["hour"]/24), "hour_cos": np.cos(2*np.pi*p["hour"]/24),
            "month_sin": np.sin(2*np.pi*8/12), "month_cos": np.cos(2*np.pi*8/12),
            "dayofweek": p["dow"], "is_weekend": int(p["dow"] >= 5), "is_holiday": p["hol"],
            "temperature_c": p["temp"], "humidity_pct": p["hum"],
            "cdd": max(p["temp"] - COOL_BASE, 0.0), "hdd": max(HEAT_BASE - p["temp"], 0.0),
            "lag_24": p["prev"], "lag_48": p["prev"], "lag_168": p["prev"],
            "roll24_lag24": p["prev"] * 0.92, "max24_lag24": p["prev"] * 1.12}])
        return float(M["best"].predict(r[DAY_AHEAD])[0]) - M["bias"]

    variations = [
        (f"temperature {temp:.0f} → {min(temp+6,46):.0f} °C", fc(temp=min(temp + 6, 46.0))),
        (f"temperature {temp:.0f} → {max(temp-8,8):.0f} °C", fc(temp=max(temp - 8, 8.0))),
        (f"humidity {hum} → {min(hum+18,98)} %", fc(hum=min(hum + 18, 98))),
        (f"humidity {hum} → {max(hum-30,20)} %", fc(hum=max(hum - 30, 20))),
        ("→ Sunday", fc(dow=6)),
        ("→ public holiday", fc(hol=1)),
        (f"demand today {prev} → {prev+80} MW", fc(prev=prev + 80)),
    ]
    labels = [v[0] for v in variations]
    deltas = [v[1] - mw for v in variations]
    fig = go.Figure(go.Bar(x=deltas, y=labels, orientation="h",
                           marker_color=[AMBER if v > 0 else CYAN for v in deltas],
                           text=[f"{v:+.0f} MW" for v in deltas], textposition="outside"))
    fig.add_vline(x=0, line=dict(color=TEXT))
    fig.update_layout(title="Change in the forecast when one condition changes",
                      xaxis_title="MW", yaxis=dict(autorange="reversed"), margin=dict(l=200))
    st.plotly_chart(style(fig, 400), use_container_width=True)
    st.caption("Note that the hour is deliberately **not** varied here. Changing the clock while "
               "holding 'demand at this hour today' fixed would describe a day that never happened — "
               "04:00 never follows an 820 MW 04:00. To sweep the clock, the lag has to move with it.")


def render_horizon():
    d, M = get_data(), get_models()
    te = d["test"]
    da = metrics(te[TARGET].values, M["pred"])
    stm = metrics(te[TARGET].values, M["st_pred"])
    pers = metrics(te[TARGET].values, te.lag_24.values)

    c = st.columns(3)
    c[0].metric("Day-ahead (issued 23:00)", f"{da['MAE']:.2f} MW", f"MAPE {da['MAPE']:.2f}%")
    c[1].metric("One hour ahead", f"{stm['MAE']:.2f} MW", f"MAPE {stm['MAPE']:.2f}%")
    c[2].metric("Persistence", f"{pers['MAE']:.2f} MW", f"MAPE {pers['MAPE']:.2f}%")

    w = te[(te.timestamp >= "2024-08-05") & (te.timestamp < "2024-08-12")]
    i = te.index.get_indexer(w.index)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=w.timestamp, y=w[TARGET], name="actual",
                             line=dict(color=TEXT, width=3)))
    fig.add_trace(go.Scatter(x=w.timestamp, y=M["pred"][i], name="day-ahead",
                             line=dict(color=CYAN, width=2)))
    fig.add_trace(go.Scatter(x=w.timestamp, y=M["st_pred"][i], name="1 hour ahead",
                             line=dict(color=GREEN, width=2, dash="dot")))
    fig.update_layout(title="One week in August — the same week, two forecast horizons",
                      xaxis_title="date", yaxis_title="demand (MW)")
    st.plotly_chart(style(fig, 440), use_container_width=True)

    st.warning(f"The extra hour of information is worth **{da['MAE']-stm['MAE']:.1f} MW** of accuracy "
               f"({(1-stm['MAE']/da['MAE'])*100:.0f}% lower MAE). But it arrives **23 hours too late** "
               f"to commit a thermal unit — which is why the day-ahead number is the deliverable.")
    c = st.columns(2)
    c[0].info("**Day-ahead** → what do we **START** tomorrow?\n\nDrives unit commitment. Settled "
              "tonight, because a large thermal unit takes 6–12 hours to synchronise.")
    c[1].info("**One hour ahead** → how do we **TRIM** what is already running?\n\nDrives real-time "
              "balancing and automatic generation control on plant that is already synchronised.")
    st.caption("Both are real products. Always quote the horizon alongside the accuracy — a MAPE "
               "figure without one is meaningless.")


def render_reserve():
    d, M = get_data(), get_models()
    te = d["test"]
    st.markdown("##### The unit costs — the assumptions the whole case rests on")
    c = st.columns(3)
    reserve_cost = c[0].slider("Holding reserve ($/MW/h)", 2.0, 15.0, 6.0, 0.5)
    under_cost = c[1].slider("Short — balancing premium ($/MWh)", 10, 120, 25, 5)
    over_cost = c[2].slider("Long — part-load waste ($/MWh)", 2, 40, 8, 1)
    st.caption("The imbalance figures are **spreads** — the extra cost over the day-ahead schedule — "
               "not full energy prices, because the energy itself was going to be bought anyway.")

    y = te[TARGET].values

    def case(name, pred):
        e = np.asarray(pred) - y
        reserve = float(np.percentile(np.abs(e), 95))
        imb = (float(np.clip(-e, 0, None).sum()) * under_cost
               + float(np.clip(e, 0, None).sum()) * over_cost) / len(e) * 8760
        return dict(method=name, reserve_mw=reserve,
                    reserve_cost=reserve * 8760 * reserve_cost, imbalance_cost=imb,
                    total=reserve * 8760 * reserve_cost + imb)

    cases = pd.DataFrame([case("Persistence (today's method)", te.lag_24.values),
                          case(f"{M['best_name']} (day-ahead)", M["pred"])]).set_index("method")
    p, m = cases.iloc[0], cases.iloc[1]
    saving = p.total - m.total

    fig = go.Figure()
    fig.add_trace(go.Bar(x=cases.index, y=cases.reserve_cost, name="holding reserve",
                         marker_color=AMBER))
    fig.add_trace(go.Bar(x=cases.index, y=cases.imbalance_cost, name="imbalance energy",
                         marker_color=RED))
    fig.update_layout(title="Annual cost of forecast error — what the utility pays either way",
                      yaxis_title="$ per year", barmode="stack")
    st.plotly_chart(style(fig, 420), use_container_width=True)

    c = st.columns(3)
    c[0].metric("Reserve — persistence", f"{p.reserve_mw:.0f} MW", "95th percentile of error")
    c[1].metric("Reserve — AI forecast", f"{m.reserve_mw:.0f} MW",
                f"−{p.reserve_mw-m.reserve_mw:.0f} MW released")
    c[2].metric("Annual saving", f"${saving:,.0f}")
    st.success(f"**{p.reserve_mw-m.reserve_mw:.0f} MW of synchronised capacity released.** Forecast "
               f"error does not disappear — it is carried as operating reserve, which means units "
               f"running at part load producing electricity that has not been sold. A better forecast "
               f"is a smaller reserve.")

    pers_mape = metrics(y, te.lag_24.values)["MAPE"]
    now_mape = metrics(y, M["pred"])["MAPE"]
    peak_gw = d["clean"].demand_mw.max() / 1000
    dm = pers_mape - now_mape
    lo, hi = peak_gw * dm * 0.3e6, peak_gw * dm * 1.5e6
    st.markdown("##### Sanity check against the published rule of thumb")
    st.markdown(f"Roughly **$0.3–1.5 M per year, per GW of peak demand, per MAPE point** improved.")
    c = st.columns(3)
    c[0].metric("Peak demand", f"{peak_gw:.2f} GW")
    c[1].metric("MAPE improvement", f"{dm:.2f} points", f"{pers_mape:.2f}% → {now_mape:.2f}%")
    c[2].metric("Rule-of-thumb range", f"${lo/1e6:.1f}–{hi/1e6:.1f} M/yr")
    if saving > hi:
        st.info("This calculation lands **above** the published range, and the reason matters. Those "
                "figures come from utilities replacing an already-competent statistical forecast with a "
                "better one — a fraction of a MAPE point. Here the comparison is against naive "
                "persistence, a jump no real utility has left to make. Read it as the value of "
                "**having** a forecasting system, not of upgrading one.")
    elif saving < lo:
        st.info("This calculation lands **below** the published range — the unit costs assumed here are "
                "conservative. Treat it as a floor.")
    else:
        st.info("This calculation lands **inside** the published range.")
    st.caption("The point of this page is the method, not the total: the benefit is computed from the "
               "measured error distribution and three stated unit costs, any of which a regulator can "
               "challenge line by line. That is what makes it a business case rather than a percentage "
               "on a slide.")


def render_dashboard():
    d, M = get_data(), get_models()
    t = test_frame()
    te = d["test"]
    mf = metrics(te[TARGET].values, M["pred"])
    pers = metrics(te[TARGET].values, te.lag_24.values)
    reserve = float(np.percentile(np.abs(M["pred"] - te[TARGET].values), 95))
    reserve_p = float(np.percentile(np.abs(te.lag_24.values - te[TARGET].values), 95))

    days = sorted(t.timestamp.dt.date.unique())
    pick = st.select_slider("Forecast day", options=days,
                            value=pd.Timestamp("2024-08-09").date()
                            if pd.Timestamp("2024-08-09").date() in days else days[0],
                            format_func=lambda x: x.strftime("%A %d %B %Y"))

    day = t[t.timestamp.dt.date == pick].sort_values("hour")
    fc = day.forecast.values
    sol = story.solar_output(day.hour.values, month=pick.month)
    net = fc - sol
    ramp = np.diff(net, prepend=net[0])

    k = st.columns(5)
    k[0].metric("Forecast peak", f"{fc.max():,.0f} MW", f"at {int(np.argmax(fc)):02d}:00")
    k[1].metric("Forecast minimum", f"{fc.min():,.0f} MW", f"at {int(np.argmin(fc)):02d}:00")
    k[2].metric("Steepest net ramp", f"{ramp.max():,.0f} MW/h")
    k[3].metric("Reserve to carry", f"{reserve:.0f} MW", f"−{reserve_p-reserve:.0f} MW vs persistence")
    k[4].metric("Forecast accuracy", f"{mf['MAPE']:.2f} %", f"vs {pers['MAPE']:.2f}% persistence")

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.09,
                        row_heights=[0.65, 0.35],
                        subplot_titles=(f"{pick} — demand, solar and net load",
                                        "Forecast error, hour by hour"))
    fig.add_trace(go.Scatter(x=day.hour, y=day[TARGET], name="actual demand",
                             line=dict(color=TEXT, width=3)), row=1, col=1)
    fig.add_trace(go.Scatter(x=day.hour, y=fc, name="forecast",
                             line=dict(color=CYAN, width=2, dash="dash")), row=1, col=1)
    fig.add_trace(go.Scatter(x=day.hour, y=net, name="net load (demand − solar)",
                             line=dict(color=RED, width=2.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=day.hour, y=sol, name="solar", fill="tozeroy",
                             line=dict(color=AMBER, width=1)), row=1, col=1)
    fig.add_hline(y=story.PEAK_TRIGGER, line=dict(color=RED, dash="dot"), row=1, col=1)
    fig.add_trace(go.Bar(x=day.hour, y=day.err, name="error",
                         marker_color=[RED if e < 0 else GREEN for e in day.err]), row=2, col=1)
    fig.update_xaxes(title_text="hour of day", row=2, col=1)
    fig.update_yaxes(title_text="MW", row=1, col=1)
    fig.update_yaxes(title_text="MW", row=2, col=1)
    st.plotly_chart(style(fig, 640), use_container_width=True)

    st.markdown("##### Despatch schedule for this day")
    acts = {}
    for h in range(len(fc)):
        ins, why = story.despatch(fc[h], net[h], ramp[h], int(day.hour.values[h]))
        acts.setdefault(ins, []).append(int(day.hour.values[h]))
    COLOR = {"MAINTAIN CURRENT GENERATION": GREEN, "INCREASE GENERATION CAPACITY": AMBER,
             "PREPARE PEAK LOAD UNITS": RED, "CHARGE ENERGY STORAGE": CYAN,
             "REDUCE RENEWABLE CURTAILMENT": TECH}
    for ins, hrs in acts.items():
        st.markdown(
            f"<div class='mimic' style='border-left-color:{COLOR.get(ins, MUTED)}'>"
            f"<b style='color:{COLOR.get(ins, MUTED)}'>{ins}</b> &nbsp;"
            f"<span class='muted'>{story.hour_spans(hrs)} &nbsp;({len(hrs)} h)</span></div>",
            unsafe_allow_html=True)

    st.write("")
    st.markdown(
        f"<div class='scada'>RECOMMENDATION ONLY &nbsp;·&nbsp; the despatch engineer commits the "
        f"schedule &nbsp;·&nbsp; forecast uncertainty <b>± {mf['MAE']:.0f} MW</b> on an average hour "
        f"&nbsp;·&nbsp; model <b>{M['best_name']}</b>, day-ahead, bias-corrected</div>",
        unsafe_allow_html=True)
    st.info("A dashboard that showed only the forecast would invite over-trust. The **recent track "
            "record sits beside it** — if the model had been running 40 MW low all week, that is "
            "something to act on, and it would never show up in an annual MAE. Forecast, outturn, "
            "error and instruction together are what make this a tool rather than an oracle.")


# ============================================================================
# THE COURSE, AS ONE LOAD-FORECASTING PROJECT
# ============================================================================
STAGES = {
    "start": ("⓪ The project — read this first", lambda: bridge.render_start(style, animate)),
    # PHASE 1
    "control-room":  ("① A Monday evening on the grid",
                      lambda: story.render_control_room(demand_for, style, animate)),
    "enter-ai":      ("② The operator and the forecast", lambda: story.render_enter_ai(style)),
    # PHASE 2
    "one-hour":      ("③ One hour, one row",
                      lambda: story.render_one_hour(demand_for, daily_shape, cooling_mw,
                                                    heating_mw, style)),
    "drivers":       ("④ What actually moves demand",
                      lambda: story.render_drivers(demand_for, style)),
    # PHASE 3
    "load-data":     ("⑤ The SCADA export arrives", render_load_data),
    "inspect":       ("⑥ Finding the bad readings", render_inspect),
    "clean":         ("⑦ Repairing the record", render_clean),
    # PHASE 4
    "profile":       ("⑧ The daily load curve", render_profile),
    "weather-link":  ("⑨ Demand against temperature", render_weather_link),
    "calendar-link": ("⑩ Working days, weekends, holidays", render_calendar_link),
    # PHASE 5
    "cyclical":      ("⑪ Midnight is next to 23:00",
                      lambda: story.render_cyclical(get_data, style, animate)),
    "degree-hours":  ("⑫ Cooling and heating degree hours", render_degree_hours),
    "lags":          ("⑬ Demand remembers itself", render_lags),
    # PHASE 6
    "gate":          ("⑭ What is known at 23:00", lambda: story.render_gate(style)),
    "split":         ("⑮ Split by time, never at random", render_split),
    "scaling":       ("⑯ Different units, different magnitudes", render_scaling),
    # PHASE 7
    "persistence":   ("⑰ What the old method achieves",
                      lambda: story.render_persistence(get_data, metrics, style)),
    # PHASE 8
    "linear":        ("⑱ One coefficient per driver", render_linear),
    "forest":        ("⑲ Many operators, one answer", render_forest),
    "boosting":      ("⑳ Correcting the last attempt", render_boosting),
    "xgboost":       ("㉑ The production implementation", render_xgboost),
    "compare":       ("㉒ Which forecast would you sign?", render_compare),
    # PHASE 9
    "importance":    ("㉓ Which drivers carry the forecast", render_importance),
    "sensitivity":   ("㉔ Does it agree with the physics?", render_sensitivity),
    "bias":          ("㉕ Why the forecast drifts low", render_bias),
    # PHASE 10
    "metrics":       ("㉖ How wrong, in megawatts", render_metrics),
    "error-profile": ("㉗ When is it wrong?", render_error_profile),
    "worst-day":     ("㉘ The day it failed", render_worst_day),
    # PHASE 11
    "predict":       ("㉙ Forecast one hour, by hand", render_predict),
    "horizon":       ("㉚ Two forecasts, two jobs", render_horizon),
    # PHASE 12
    "despatch":      ("㉛ From forecast to despatch instruction",
                      lambda: story.render_despatch(test_frame, style, animate)),
    "reserve":       ("㉜ Reserve, and the cost of being wrong", render_reserve),
    "dashboard":     ("㉝ The utility operations dashboard", render_dashboard),
}

ALIASES = {"overview": "control-room", "grid": "control-room", "forecast": "predict",
           "models": "compare", "eda": "profile", "business-case": "reserve"}

stage = st.query_params.get("stage", "start")
stage = ALIASES.get(stage, stage)
if stage not in STAGES:
    stage = "start"

with st.sidebar:
    st.markdown("### ⚡ An Electricity Load Forecasting Problem")
    st.caption("You are running a utility control room, and AI keeps turning out to be the thing that "
               "supplies a number one engineer cannot produce 8,760 times a year.")
    keys = list(STAGES)
    sel = st.selectbox("Where are we in the project?", keys, index=keys.index(stage),
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
            f"<span style='color:#8b98a9'>POWER SYSTEM STEP</span><br>"
            f"<b style='color:#ffb74d'>{step['civil']}</b><br>"
            f"<span style='color:#8b98a9'>IS THE AI CONCEPT</span><br>"
            f"<b style='color:#4fc3f7'>{step['ai']}</b></div>", unsafe_allow_html=True)
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
