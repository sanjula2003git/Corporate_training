"""
story.py - the substation, its physics, its data and its models.
=================================================================
Everything numeric in the app comes from here. The app never fabricates a
number in a caption: it asks this module and prints what it gets back.

This module is INDEPENDENT of the Colab notebook - it shares no code and reads
no file from it. It reproduces the same engineering so the two deliverables
tell the same story:

  * IEEE C57.91 clause 7 - top-oil rise and the K^1.6 winding gradient
  * IEEE C57.91 clause 5 - ageing acceleration factor F_AA
  * IEEE C57.91 table 8  - hot-spot limits 110 / 120 / 140 C

Everything is cached. The year of substation history is simulated once per
session; the models are fitted once per session.
"""
import numpy as np
import pandas as pd
import streamlit as st

# ============================================================================
# NAMEPLATE  -  a 40 MVA 132/33 kV ONAN/ONAF transformer
# ============================================================================
I_RATED = 700.0     # A   rated current, 33 kV side
V_RATED = 132.0     # kV  rated voltage, 132 kV side
DTO_R   = 32.0      # K   top-oil rise over ambient at rated load, fans running
DTH_R   = 24.0      # K   hot-spot rise over top oil at rated load
R_RATIO = 6.0       #     load loss / no-load loss at rated
N_EXP   = 0.9       #     oil exponent
M_EXP   = 0.8       #     winding exponent -> gradient ~ K^1.6
TAU_OIL, TAU_POCKET = 3.0, 1.6      # h  oil time constant, thermometer-pocket lag

STAGE_OIL = {0: 1.35, 1: 1.10, 2: 1.00}   # top-oil rise multiplier by cooling stage
STAGE_HS  = {0: 1.00, 1: 1.10, 2: 1.18}   # hot-spot factor by cooling stage

UNITS     = [("T1", 3), ("T2", 9), ("T3", 16), ("T4", 22)]
H_UNIT    = {"T1": 1.00, "T2": 1.13, "T3": 0.93, "T4": 1.21}   # real hot-spot factors
UNIT_LOAD = {"T1": 0.92, "T2": 1.00, "T3": 1.06, "T4": 0.96}   # feeder loading

# IEEE C57.91 table 8
LIMIT_NORMAL, LIMIT_PLANNED, LIMIT_EMERGENCY = 110.0, 120.0, 140.0

RAW_FEATURES = ["load_current_a", "ambient_temp_c", "oil_temp_c", "voltage_kv", "humidity_pct"]
ENG_FEATURES = RAW_FEATURES + ["cooling_stage", "transformer_age_years", "load_pu_16",
                               "oil_rise_c", "oil_ramp_1h", "load_ramp_1h", "load_roll3", "hour"]
TARGET = "hotspot_temp_c"

FEATURE_LABELS = {
    "load_current_a": "Load current (A)", "ambient_temp_c": "Ambient (°C)",
    "oil_temp_c": "Top oil (°C)", "voltage_kv": "Voltage (kV)",
    "humidity_pct": "Humidity (%)", "cooling_stage": "Cooling stage",
    "transformer_age_years": "Age (years)", "load_pu_16": "K^1.6 (winding law)",
    "oil_rise_c": "Oil rise over ambient (K)", "oil_ramp_1h": "Oil change, 1 h (K)",
    "load_ramp_1h": "Load change, 1 h (pu)", "load_roll3": "Load, 3 h mean (pu)",
    "hour": "Hour of day",
}


# ============================================================================
# THE PHYSICS  (IEEE C57.91)
# ============================================================================
def top_oil_rise(K, v_pu=1.0, stage=2, age_years=0.0):
    """Steady-state top-oil rise over ambient, in kelvin. IEEE C57.91 clause 7."""
    fouling = 1.0 + 0.0045 * age_years           # radiators foul, cooling falls with age
    loss_pu = (np.asarray(K, float) ** 2 * R_RATIO + np.asarray(v_pu, float) ** 2) / (R_RATIO + 1.0)
    return DTO_R * loss_pu ** N_EXP * STAGE_OIL[int(stage)] * fouling


def hotspot_gradient(K, ambient_c=25.0, stage=2, age_years=0.0, h_factor=1.0, solar=0.0):
    """Hot-spot rise above top oil, in kelvin. Grows as K^(2m) = K^1.6."""
    viscosity = np.clip(1.0 + 0.0045 * (25.0 - np.asarray(ambient_c, float)), 0.93, 1.12)
    fouling = 1.0 + 0.0025 * age_years
    return (DTH_R * np.asarray(K, float) ** (2 * M_EXP) * STAGE_HS[int(stage)]
            * viscosity * fouling * h_factor + 1.8 * solar)


def ageing_factor(theta_h):
    """IEEE C57.91 clause 5: relative rate of insulation ageing. 1.0 at 110 C."""
    return np.exp(15000.0 / 383.0 - 15000.0 / (np.asarray(theta_h, float) + 273.0))


def fan_stage_for(oil_c, K):
    """What the fan controller would be doing at this oil temperature and load."""
    if oil_c > 68 or K > 0.92:
        return 2
    if oil_c > 55 or K > 0.70:
        return 1
    return 0


def loss_split(K, v_pu=1.0):
    """Load loss and no-load loss, per unit of total loss at rated load.

    No-load loss is broadcast to the shape of K so both returns plot as series.
    """
    K = np.asarray(K, float)
    load = K ** 2 * R_RATIO / (R_RATIO + 1.0)
    no_load = np.broadcast_to(np.asarray(v_pu, float) ** 2 / (R_RATIO + 1.0),
                              load.shape).copy()
    return load, no_load


# ============================================================================
# THE YEAR OF SUBSTATION HISTORY
# ============================================================================
HOURS = 8760


@st.cache_data(show_spinner="Simulating a year of substation history…")
def get_raw_log():
    """The historian export, faults and all. One row per unit per hour."""
    idx = pd.date_range("2025-01-01", periods=HOURS, freq="h")
    doy, hod, dow = idx.dayofyear.to_numpy(), idx.hour.to_numpy(), idx.dayofweek.to_numpy()
    rng = np.random.default_rng(42)

    w = np.zeros(HOURS); e = rng.normal(0, 1.0, HOURS)
    for t in range(1, HOURS):
        w[t] = 0.93 * w[t - 1] + e[t]
    ambient = 25.5 + 7.0 * np.sin(2 * np.pi * (doy - 110) / 365) \
        + 6.0 * np.sin(2 * np.pi * (hod - 9) / 24) + w
    humidity = np.clip(92 - 1.35 * (ambient - 18) + rng.normal(0, 6, HOURS), 22, 99)
    cloud = np.clip((humidity - 45) / 45.0, 0, 1)
    solar = np.clip(np.sin(np.pi * (hod - 6) / 12), 0, None) * (1 - 0.75 * cloud)
    wind = np.clip(rng.gamma(2.0, 1.3, HOURS), 0, 9)

    daily = 0.60 + 0.32 * np.exp(-0.5 * ((hod - 10) / 2.6) ** 2) \
        + 0.46 * np.exp(-0.5 * ((hod - 20) / 2.4) ** 2)
    season = 0.90 + 0.24 * np.clip(np.sin(2 * np.pi * (doy - 110) / 365), -0.4, 1)
    week = np.where(dow >= 5, 0.88, 1.0)

    frames = []
    for i, (unit, age) in enumerate(UNITS):
        r = np.random.default_rng(100 + i)
        n = np.zeros(HOURS); ee = r.normal(0, 0.030, HOURS)
        for t in range(1, HOURS):
            n[t] = 0.75 * n[t - 1] + ee[t]
        K = daily * season * week * UNIT_LOAD[unit] * (1 + n)
        for _ in range(22):                        # contingency feeder transfers
            s = r.integers(0, HOURS - 30)
            K[s:s + r.integers(4, 26)] *= r.uniform(1.14, 1.34)
        K = np.clip(K, 0.22, 1.38)
        v_pu = np.clip(1.0 - 0.035 * (K - 0.8) + r.normal(0, 0.010, HOURS), 0.94, 1.06)

        # slow drift the nameplate cannot describe: radiator dust, oil condition
        d = np.zeros(HOURS); de = r.normal(0, 0.50, HOURS); phi = np.exp(-1 / 12)
        for t in range(1, HOURS):
            d[t] = phi * d[t - 1] + de[t]

        amb = ambient + r.normal(0, 0.4, HOURS)
        oil_true = np.zeros(HOURS); oil_meas = np.zeros(HOURS)
        hs = np.zeros(HOURS); stage = np.zeros(HOURS, dtype=int)
        oil_true[0] = oil_meas[0] = amb[0] + 18
        st_, a_oil, a_pkt = 0, np.exp(-1 / TAU_OIL), np.exp(-1 / TAU_POCKET)
        for t in range(HOURS):
            prev = oil_meas[t - 1] if t else oil_meas[0]
            if st_ == 0 and (prev > 55 or K[t] > 0.70):
                st_ = 1
            elif st_ == 1:
                if prev > 68 or K[t] > 0.92:
                    st_ = 2
                elif prev < 50 and K[t] < 0.62:
                    st_ = 0
            elif st_ == 2 and prev < 63 and K[t] < 0.85:
                st_ = 1
            stage[t] = st_
            target = amb[t] + top_oil_rise(K[t], v_pu[t], st_, age) \
                + 2.6 * solar[t] - 0.32 * wind[t]
            oil_true[t] = target if t == 0 else a_oil * oil_true[t - 1] + (1 - a_oil) * target
            oil_meas[t] = oil_true[t] if t == 0 else a_pkt * oil_meas[t - 1] + (1 - a_pkt) * oil_true[t]
            hs[t] = oil_true[t] + hotspot_gradient(K[t], amb[t], st_, age,
                                                   H_UNIT[unit], solar[t]) + d[t]
        frames.append(pd.DataFrame({
            "timestamp": idx, "unit_id": unit, "cooling_type": "ONAN/ONAF",
            "load_current_a": np.round(K * I_RATED * (1 + r.normal(0, 0.005, HOURS)), 1),
            "voltage_kv": np.round(v_pu * V_RATED * (1 + r.normal(0, 0.003, HOURS)), 2),
            "ambient_temp_c": np.round(amb + r.normal(0, 0.6, HOURS), 1),
            "humidity_pct": np.round(np.clip(humidity + r.normal(0, 2.0, HOURS), 20, 100), 1),
            "oil_temp_c": np.round(oil_meas + r.normal(0, 1.4, HOURS), 1),
            "cooling_stage": stage, "transformer_age_years": age,
            "hotspot_temp_c": np.round(hs + r.normal(0, 0.6, HOURS), 1),
        }))

    log = pd.concat(frames, ignore_index=True)

    # ---- the instrumentation faults a real export contains -----------------
    f = np.random.default_rng(7)
    log.loc[f.choice(len(log), 380, replace=False), "oil_temp_c"] = np.nan
    log.loc[f.choice(len(log), 120, replace=False), "hotspot_temp_c"] = np.nan
    log.loc[f.choice(len(log), 95, replace=False), "humidity_pct"] = 255.0
    for u in ("T1", "T3"):                                   # frozen ambient sensor
        s = log.index[log.unit_id == u][f.integers(2000, 6000)]
        log.loc[s:s + 13, "ambient_temp_c"] = log.loc[s, "ambient_temp_c"]
    for u in ("T2", "T4"):                                   # unit switched out
        s = log.index[log.unit_id == u][f.integers(2000, 6000)]
        log.loc[s:s + 9, ["load_current_a", "cooling_stage"]] = [3.2, 0]
        log.loc[s:s + 9, "oil_temp_c"] = log.loc[s:s + 9, "ambient_temp_c"] + 1.5
        log.loc[s:s + 9, "hotspot_temp_c"] = log.loc[s:s + 9, "ambient_temp_c"] + 2.0
    log = pd.concat([log, log.sample(60, random_state=3)], ignore_index=True)
    return log


def _frozen_run(s, min_len=6):
    """True for every reading inside a run of min_len or more identical values."""
    block = (s != s.shift()).cumsum()
    return s.groupby(block).transform("size") >= min_len


@st.cache_data(show_spinner=False)
def get_clean_log():
    """The export after cleaning, plus the audit trail of what was done."""
    log = get_raw_log()
    clean = log.copy()
    before = len(clean)
    report = []

    clean = clean.drop_duplicates()
    report.append(("Duplicate rows removed", before - len(clean)))

    const = [c for c in clean.columns if clean[c].nunique(dropna=True) == 1]
    clean = clean.drop(columns=const)
    report.append((f"Constant column dropped ({', '.join(const)})", len(const)))

    n = int((clean.humidity_pct > 100).sum())
    clean.loc[clean.humidity_pct > 100, "humidity_pct"] = np.nan
    report.append(("Impossible humidity set to missing", n))

    clean = clean.sort_values(["unit_id", "timestamp"]).reset_index(drop=True)

    frozen = clean.groupby("unit_id", sort=False).ambient_temp_c.transform(_frozen_run)
    n = int(frozen.sum()); clean = clean[~frozen]
    report.append(("Frozen-ambient-sensor rows dropped", n))

    n = int((clean.load_current_a < 10).sum())
    clean = clean[clean.load_current_a >= 10]
    report.append(("De-energised rows dropped", n))

    for col in ("oil_temp_c", "humidity_pct"):
        n = int(clean[col].isna().sum())
        clean[col] = clean.groupby("unit_id")[col].transform(
            lambda s: s.interpolate(limit=3).ffill().bfill())
        report.append((f"{col} gaps interpolated", n))

    n = int(clean.hotspot_temp_c.isna().sum())
    clean = clean.dropna(subset=["hotspot_temp_c"])
    report.append(("Rows with no hot-spot label dropped", n))

    return clean.reset_index(drop=True), pd.DataFrame(report, columns=["Action", "Rows"]), before


@st.cache_data(show_spinner=False)
def get_features():
    """The cleaned log with the engineering features added, and the week-block split."""
    df, _, _ = get_clean_log()
    df = df.sort_values(["unit_id", "timestamp"]).reset_index(drop=True)
    g = df.groupby("unit_id", sort=False)
    df["load_pu"] = df.load_current_a / I_RATED
    df["volt_pu"] = df.voltage_kv / V_RATED
    df["load_pu_16"] = df.load_pu ** 1.6
    df["oil_rise_c"] = df.oil_temp_c - df.ambient_temp_c
    df["oil_ramp_1h"] = g.oil_temp_c.diff().fillna(0.0)
    df["load_ramp_1h"] = g.load_pu.diff().fillna(0.0)
    df["load_roll3"] = g.load_pu.transform(lambda s: s.rolling(3, min_periods=1).mean())
    df["hour"] = df.timestamp.dt.hour
    df["test"] = df.timestamp.dt.isocalendar().week.astype(int) % 4 == 0
    return df


# ============================================================================
# THE MODELS
# ============================================================================
def _metrics(y, p):
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    return {"MAE (°C)": mean_absolute_error(y, p),
            "RMSE (°C)": mean_squared_error(y, p) ** 0.5,
            "R²": r2_score(y, p)}


@st.cache_resource(show_spinner="Fitting the models…")
def get_models():
    """Fit every model in the leaderboard. Returns predictions and scores."""
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor

    df = get_features()
    te = df.test.to_numpy()
    y_tr, y_te = df.loc[~te, TARGET], df.loc[te, TARGET]

    out, preds, fitted = [], {}, {}

    # ---- the standard's own model, nothing fitted -------------------------
    stage_f = df.cooling_stage.map(STAGE_HS).to_numpy()
    ieee = df.oil_temp_c.to_numpy() + DTH_R * df.load_pu.to_numpy() ** 1.6 * stage_f
    preds["ieee"] = ieee[te]
    out.append({"Model": "IEEE C57.91 (nameplate)", "Family": "Standard", **_metrics(y_te, ieee[te])})

    # ---- linear regression, raw sensors then engineered -------------------
    for name, feats, key in [("Linear regression (5 raw sensors)", RAW_FEATURES, "lin_raw"),
                             ("Linear regression (engineered)", ENG_FEATURES, "lin_eng")]:
        sc = StandardScaler().fit(df.loc[~te, feats])
        m = LinearRegression().fit(sc.transform(df.loc[~te, feats]), y_tr)
        p = m.predict(sc.transform(df.loc[te, feats]))
        preds[key] = p; fitted[key] = (m, sc, feats)
        out.append({"Model": name, "Family": "Linear", **_metrics(y_te, p)})

    Xtr, Xte = df.loc[~te, ENG_FEATURES], df.loc[te, ENG_FEATURES]

    rf = RandomForestRegressor(n_estimators=200, min_samples_leaf=2,
                               n_jobs=-1, random_state=42).fit(Xtr, y_tr)
    preds["rf"] = rf.predict(Xte); fitted["rf"] = rf
    out.append({"Model": "Random Forest", "Family": "Ensemble", **_metrics(y_te, preds["rf"])})

    # HistGradientBoosting - the same algorithm as the notebook's
    # GradientBoostingRegressor, binned so the app stays responsive.
    gb = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06, max_depth=6,
                                       random_state=42).fit(Xtr, y_tr)
    preds["gb"] = gb.predict(Xte); fitted["gb"] = gb
    out.append({"Model": "Gradient Boosting", "Family": "Ensemble", **_metrics(y_te, preds["gb"])})

    try:
        from xgboost import XGBRegressor
        xgb = XGBRegressor(n_estimators=600, learning_rate=0.05, max_depth=6, subsample=0.9,
                           colsample_bytree=0.9, random_state=42, n_jobs=-1).fit(Xtr, y_tr)
        preds["xgb"] = xgb.predict(Xte); fitted["xgb"] = xgb
        out.append({"Model": "XGBoost", "Family": "Ensemble", **_metrics(y_te, preds["xgb"])})
        best_key = "xgb"
    except Exception:
        best_key = "gb"

    board = pd.DataFrame(out).sort_values("MAE (°C)").reset_index(drop=True)
    return {"board": board, "preds": preds, "fitted": fitted, "best": best_key,
            "y_test": y_te.to_numpy(), "test_mask": te}


def best_model():
    m = get_models()
    return m["fitted"][m["best"]], m["best"]


BEST_LABEL = {"xgb": "XGBoost", "gb": "Gradient Boosting"}


def feature_row(load_a, ambient_c, oil_c, volt_kv=132.0, humidity=60.0,
                stage=None, age=16, hour=15, roll3=None):
    """One feature vector, from a set of substation readings."""
    K = load_a / I_RATED
    if stage is None:
        stage = fan_stage_for(oil_c, K)
    return pd.DataFrame([{
        "load_current_a": load_a, "ambient_temp_c": ambient_c, "oil_temp_c": oil_c,
        "voltage_kv": volt_kv, "humidity_pct": humidity, "cooling_stage": stage,
        "transformer_age_years": age, "load_pu_16": K ** 1.6,
        "oil_rise_c": oil_c - ambient_c, "oil_ramp_1h": 0.0, "load_ramp_1h": 0.0,
        "load_roll3": K if roll3 is None else roll3, "hour": hour,
    }])[ENG_FEATURES]


def predict_hotspot(load_a, ambient_c, oil_c, volt_kv=132.0, humidity=60.0,
                    stage=None, age=16, hour=15):
    """The number the whole app exists to produce."""
    model, _ = best_model()
    return float(model.predict(feature_row(load_a, ambient_c, oil_c, volt_kv,
                                           humidity, stage, age, hour))[0])


# ============================================================================
# THE DECISION RULES  (IEEE C57.91 table 8 + engineering logic)
# ============================================================================
def assess(load_a, ambient_c, oil_c, volt_kv=132.0, humidity=60.0, age=16, hour=15):
    """Predict the hot spot, then say what it means and what to do about it."""
    K = load_a / I_RATED
    stage = fan_stage_for(oil_c, K)
    t = predict_hotspot(load_a, ambient_c, oil_c, volt_kv, humidity, stage, age, hour)
    expected_rise = float(top_oil_rise(K, 1.0, stage, age))
    shortfall = (oil_c - ambient_c) - expected_rise
    faulty = shortfall > 6
    at_limit = stage == 2

    if t < 98:
        action, urgency, tone = "Continue normal operation", "Routine", "ok"
    elif t < LIMIT_NORMAL:
        if faulty:
            action, urgency, tone = "Investigate cooling system", "Act today", "warn"
        else:
            action, urgency, tone = "Monitor closely", "Watch", "watch"
    elif t < LIMIT_PLANNED:
        urgency, tone = "Act today", "warn"
        action = ("Investigate cooling system, then reduce load if unresolved" if faulty
                  else "Cooling is already at maximum — reduce loading" if at_limit
                  else "Increase cooling, prepare to reduce load")
    else:
        urgency, tone = "Immediate", "alarm"
        action = ("Reduce loading now, and investigate cooling" if faulty
                  else "Reduce loading now")

    reasons = []
    if faulty:
        reasons.append(f"oil rise is {shortfall:.0f} K above what this load justifies — "
                       "check fans, radiators and oil condition before restricting load")
    if K > 1.05:
        reasons.append(f"loading is {K:.2f} pu, above nameplate")
    if ambient_c > 38:
        reasons.append(f"ambient {ambient_c:.0f} °C is limiting how much heat the radiators can reject")
    if at_limit and t > 105:
        reasons.append("cooling is commanded to full stage, so load is the only remaining lever")
    if not reasons:
        reasons.append("temperature is consistent with the load and the ambient conditions")

    return {"hotspot_c": t, "gradient_k": t - oil_c, "oil_rise_c": oil_c - ambient_c,
            "expected_rise_c": expected_rise, "shortfall_k": shortfall,
            "faa": float(ageing_factor(t)), "headroom_k": LIMIT_NORMAL - t,
            "load_pu": K, "stage": stage, "age": age, "ambient_c": ambient_c,
            "action": action, "urgency": urgency, "tone": tone, "reasons": reasons}


@st.cache_data(show_spinner=False)
def fleet_snapshot():
    """Every unit at the busiest hour of the year - what an operator would see."""
    df = get_features()
    peak = df.groupby("timestamp").hotspot_temp_c.mean().idxmax()
    now = df[df.timestamp == peak]
    ageing = df.assign(f=ageing_factor(df.hotspot_temp_c)).groupby("unit_id").f.sum()
    rows = []
    for _, r in now.iterrows():
        d = assess(r.load_current_a, r.ambient_temp_c, r.oil_temp_c,
                   r.voltage_kv, r.humidity_pct, int(r.transformer_age_years))
        rows.append({"Unit": r.unit_id, "Age": int(r.transformer_age_years),
                     "Load (A)": round(r.load_current_a), "Ambient (°C)": round(r.ambient_temp_c, 1),
                     "Oil (°C)": round(r.oil_temp_c, 1), "Hot spot (°C)": round(d["hotspot_c"], 1),
                     "Headroom (K)": round(d["headroom_k"], 1), "Ageing ×": round(d["faa"], 2),
                     "Life used (days)": round(ageing[r.unit_id] / 24, 1),
                     "Urgency": d["urgency"], "Action": d["action"], "tone": d["tone"]})
    return pd.DataFrame(rows).sort_values("Headroom (K)").reset_index(drop=True), peak
