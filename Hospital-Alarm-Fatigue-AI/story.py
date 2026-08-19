"""The virtual ward, the five systems, and the figures the app draws.

This is a trimmed version of the notebook's model, sized to run inside a 1 GB
Streamlit Cloud container: 6 days instead of 12, a smaller forest, and no
TensorFlow (the sequence model is illustrated rather than trained live).
The rules, the thresholds and the actions are the same as the notebook's.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.ensemble import RandomForestClassifier

BG = "#0e1117"
CYAN = "#4fc3f7"
AMBER = "#ffb74d"
RED = "#ef5350"
GREEN = "#66bb6a"
VIOLET = "#ba68c8"
GREY = "#8b949e"

N_PATIENTS = 20
N_DAYS = 6
DT = 2
PER_DAY = 24 * 60 // DT
EVENT_CHANCE = 0.30
REFRACTORY = 30

TRAIN_DAYS = [0, 1, 2]
TUNE_DAYS = [3]
TEST_DAYS = [4, 5]

MEDS = {
    "nebuliser":    dict(hr=+16., rr=+2.0, spo2=+0.5, sbp=0., temp=0.0, lasts=45),
    "beta blocker": dict(hr=-14., rr=0.0, spo2=0.0, sbp=-6., temp=0.0, lasts=240),
    "opioid":       dict(hr=-4., rr=-4.5, spo2=-1.8, sbp=-4., temp=0.0, lasts=150),
    "paracetamol":  dict(hr=-4., rr=0.0, spo2=0.0, sbp=0., temp=-0.8, lasts=180),
    "iv fluids":    dict(hr=-5., rr=0.0, spo2=0.0, sbp=+10., temp=0.0, lasts=120),
}
MED_NAMES = list(MEDS)

TROUBLE = {
    "infection": dict(hr=+38., rr=+12., spo2=-4.0, sbp=-30., temp=+1.7),
    "breathing": dict(hr=+24., rr=+15., spo2=-9.0, sbp=-8., temp=+0.3),
    "bleeding":  dict(hr=+42., rr=+8., spo2=-2.0, sbp=-38., temp=-0.3),
}
TROUBLE_NAMES = list(TROUBLE)

# Six of the twenty patients live permanently near a monitor limit.
CHRONIC = ["fast heart", "low oxygen", "low pressure", "fast heart", "low oxygen", "low pressure"]

ACTIONS = {
    "ignore":  dict(label="Ignore - probably sensor noise", nurse_minutes=0, alerts=False),
    "repeat":  dict(label="Repeat the measurement", nurse_minutes=0, alerts=False),
    "monitor": dict(label="Keep watching", nurse_minutes=0, alerts=False),
    "notify":  dict(label="Notify a nurse", nurse_minutes=8, alerts=True),
    "urgent":  dict(label="Urgent response team", nurse_minutes=20, alerts=True),
}

FEATURES = [
    "hr", "spo2", "rr", "sbp", "temp",
    "hr_smooth", "spo2_smooth", "rr_smooth",
    "hr_off", "spo2_off", "rr_off", "sbp_off", "temp_off",
    "hr_smooth_d30", "spo2_smooth_d30", "rr_smooth_d30", "sbp_d30", "temp_d30",
    "quality", "quality_smooth", "bp_age",
    "mins_since_med", "med_recent",
    "med_speeds_heart", "med_slows_heart", "med_slows_breathing",
    "hour_of_day",
]


# --------------------------------------------------------------- the ward
def _wander(rng, n, sd, k=11):
    w = rng.normal(0, sd, n + k)
    return np.convolve(w, np.ones(k) / k, mode="same")[:n] * np.sqrt(k)


def build_ward(glitches=26, seed=7):
    """Create the whole ward: every patient, every day, every reading."""
    rng = np.random.default_rng(seed)
    parts = []
    minute_of_day = np.arange(PER_DAY) * DT
    clock = minute_of_day / 60.0

    for p in range(N_PATIENTS):
        base = dict(hr=rng.normal(78, 9), spo2=rng.normal(97, 1.0), rr=rng.normal(16, 2.0),
                    sbp=rng.normal(124, 12), temp=rng.normal(36.8, 0.25))
        chronic = CHRONIC[p] if p < len(CHRONIC) else ""
        if chronic == "fast heart":
            base["hr"] = rng.normal(112, 5)
        elif chronic == "low oxygen":
            base["spo2"] = rng.normal(90.5, 0.8)
        elif chronic == "low pressure":
            base["sbp"] = rng.normal(96, 4)
        probe_ok = rng.uniform(0.80, 0.99)

        for d in range(N_DAYS):
            n = PER_DAY
            swing = np.cos(2 * np.pi * (clock - 16) / 24)
            hr = base["hr"] + _wander(rng, n, 2.2) + 5.0 * swing
            spo2 = base["spo2"] + _wander(rng, n, 0.45)
            rr = base["rr"] + _wander(rng, n, 0.9)
            sbp = base["sbp"] + _wander(rng, n, 3.5) + 4.0 * swing
            temp = base["temp"] + _wander(rng, n, 0.12) + 0.25 * swing
            quality = np.clip(probe_ok + _wander(rng, n, 0.02), 0, 1)

            med_name = np.array([""] * n, dtype=object)
            mins_since_med = np.full(n, 999.0)
            for start in sorted(int(s) for s in rng.integers(0, n - 30, size=rng.integers(2, 6))):
                name = MED_NAMES[rng.integers(0, len(MED_NAMES))]
                eff = MEDS[name]
                steps = int(eff["lasts"] / DT)
                idx = np.arange(start, min(n, start + steps))
                shape = np.clip((idx - start) / 5.0, 0, 1) * (1 - (idx - start) / steps)
                hr[idx] += eff["hr"] * shape
                rr[idx] += eff["rr"] * shape
                spo2[idx] += eff["spo2"] * shape
                sbp[idx] += eff["sbp"] * shape
                temp[idx] += eff["temp"] * shape
                med_name[idx] = name
                mins_since_med[idx] = (idx - start) * DT

            trouble = np.zeros(n)
            mins_to_crisis = np.full(n, np.nan)
            kind = ""
            if rng.random() < EVENT_CHANCE:
                kind = TROUBLE_NAMES[rng.integers(0, len(TROUBLE_NAMES))]
                eff = {k: v * rng.uniform(0.45, 1.10) for k, v in TROUBLE[kind].items()}
                length = int(rng.integers(40, 71))
                start = int(rng.integers(30, n - length - 40))
                idx = np.arange(start, start + length)
                ramp = ((idx - start) / length) ** 1.6
                for arr, key in ((hr, "hr"), (rr, "rr"), (spo2, "spo2"), (sbp, "sbp"), (temp, "temp")):
                    arr[idx] += eff[key] * ramp
                trouble[idx] = 1.0
                mins_to_crisis[idx] = (start + length - idx) * DT
                back = np.arange(start + length, min(n, start + length + 30))
                if len(back):
                    fade = 1 - (back - (start + length)) / 30.0
                    for arr, key in ((hr, "hr"), (rr, "rr"), (spo2, "spo2"), (sbp, "sbp"), (temp, "temp")):
                        arr[back] += eff[key] * fade

            artifact = np.zeros(n)
            for _ in range(rng.poisson(glitches)):
                start = int(rng.integers(0, n - 4))
                idx = np.arange(start, start + int(rng.integers(1, 4)))
                which = rng.integers(0, 3)
                if which == 0:
                    spo2[idx] = rng.uniform(62, 86)
                    quality[idx] = rng.uniform(0.05, 0.30)
                elif which == 1:
                    hr[idx] += rng.uniform(35, 75)
                    quality[idx] = rng.uniform(0.15, 0.45)
                else:
                    rr[idx] = rng.uniform(2, 44)
                    quality[idx] = rng.uniform(0.05, 0.35)
                artifact[idx] = 1.0

            keep = np.zeros(n, bool)
            keep[::8] = True
            bad_cuff = keep & (rng.random(n) < 0.03)
            sbp_meas = np.where(keep, sbp, np.nan)
            sbp_meas[bad_cuff] += rng.normal(0, 22, int(bad_cuff.sum()))
            sbp_obs = pd.Series(sbp_meas).ffill().bfill().to_numpy()

            keep_t = np.zeros(n, bool)
            keep_t[::15] = True
            temp_obs = pd.Series(np.where(keep_t, temp, np.nan)).ffill().bfill().to_numpy()

            parts.append(pd.DataFrame(dict(
                patient=p, day=d, chronic=chronic,
                minute=d * 24 * 60 + minute_of_day,
                hour_of_day=(minute_of_day // 60),
                hr=np.clip(hr, 25, 220), spo2=np.clip(spo2, 50, 100), rr=np.clip(rr, 2, 60),
                sbp=np.clip(sbp_obs, 50, 240), temp=temp_obs, quality=quality,
                bp_age=(np.arange(n) % 8) * DT, med=med_name,
                mins_since_med=np.clip(mins_since_med, 0, 999),
                trouble=trouble, kind=kind, mins_to_crisis=mins_to_crisis, artifact=artifact,
            )))
    return add_features(pd.concat(parts, ignore_index=True))


def add_features(df):
    """Turn raw readings into the clues a good nurse uses without noticing."""
    g = df.groupby("patient", sort=False)
    for c in ["hr", "spo2", "rr", "quality"]:
        df[c + "_smooth"] = g[c].transform(lambda s: s.rolling(5, min_periods=1).median())
    g = df.groupby("patient", sort=False)
    for c in ["hr", "spo2", "rr", "sbp", "temp"]:
        df[c + "_usual"] = g[c].transform(lambda s: s.shift(15).rolling(120, min_periods=20).median())
    for c in ["hr", "spo2", "rr"]:
        df[c + "_off"] = df[c + "_smooth"] - df[c + "_usual"]
    for c in ["sbp", "temp"]:
        df[c + "_off"] = df[c] - df[c + "_usual"]
    g = df.groupby("patient", sort=False)
    for c in ["hr_smooth", "spo2_smooth", "rr_smooth", "sbp", "temp"]:
        df[c + "_d30"] = g[c].transform(lambda s: s - s.shift(15))
    df["med_recent"] = (df["mins_since_med"] < 90).astype(int)
    df["med_speeds_heart"] = ((df["med"] == "nebuliser") & (df["mins_since_med"] < 60)).astype(int)
    df["med_slows_heart"] = ((df["med"] == "beta blocker") & (df["mins_since_med"] < 240)).astype(int)
    df["med_slows_breathing"] = ((df["med"] == "opioid") & (df["mins_since_med"] < 150)).astype(int)
    df[FEATURES] = df[FEATURES].fillna(0)
    return df


def event_table(df, days):
    ev = (df[(df.trouble == 1) & (df.day.isin(days))]
          .groupby(["patient", "day"])
          .agg(kind=("kind", "first"), start=("minute", "min"), crisis=("minute", "max"))
          .reset_index())
    ev["crisis"] = ev["crisis"] + DT
    return ev


# --------------------------------------------------------------- the models
def breaks_limits(df):
    return ((df.hr < 45) | (df.hr > 120) | (df.spo2 < 90) | (df.rr < 8) | (df.rr > 26) |
            (df.sbp < 90) | (df.sbp > 180) | (df.temp < 35.0) | (df.temp > 38.5)).to_numpy()


def risk_score(df):
    rr, sp, tp = df.rr.to_numpy(), df.spo2.to_numpy(), df.temp.to_numpy()
    bp, hr = df.sbp.to_numpy(), df.hr.to_numpy()
    s = np.zeros(len(df))
    s += np.select([rr <= 8, rr <= 11, rr <= 20, rr <= 24], [3, 1, 0, 2], default=3)
    s += np.select([sp <= 91, sp <= 93, sp <= 95], [3, 2, 1], default=0)
    s += np.select([tp <= 35.0, tp <= 36.0, tp <= 38.0, tp <= 39.0], [3, 1, 0, 1], default=2)
    s += np.select([bp <= 90, bp <= 100, bp <= 110, bp <= 219], [3, 2, 1, 0], default=3)
    s += np.select([hr <= 40, hr <= 50, hr <= 90, hr <= 110, hr <= 130], [3, 1, 0, 1, 2], default=3)
    return s


def train_forest(ward):
    """A smaller forest than the notebook's, to fit the Cloud container."""
    tr = ward[ward.day.isin(TRAIN_DAYS)]
    forest = RandomForestClassifier(n_estimators=60, max_depth=12, min_samples_leaf=30,
                                    class_weight="balanced_subsample", n_jobs=1, random_state=7)
    forest.fit(tr[FEATURES].to_numpy(np.float32), tr["trouble"].to_numpy().astype(int))
    return forest


def to_alerts(df, fire, refractory=REFRACTORY):
    out = []
    for p, part in df.groupby("patient", sort=False):
        rows, mins = part.index.to_numpy(), part["minute"].to_numpy()
        last = -10 ** 9
        for i in np.flatnonzero(fire[rows]):
            if mins[i] - last >= refractory:
                out.append((mins[i], p, rows[i], "notify"))
                last = mins[i]
    return pd.DataFrame(out, columns=["minute", "patient", "row", "action"])


def pick_level(df, risk, per_hour, hours):
    lo, hi = 0.0, 1.0
    for _ in range(18):
        mid = (lo + hi) / 2.0
        if len(to_alerts(df, risk >= mid)) / hours > per_hour:
            lo = mid
        else:
            hi = mid
    return round(hi, 4)


def pick_sensitive_level(df, risk_col, evs, catch=0.75):
    peaks = []
    for e in evs.itertuples():
        part = df[(df.patient == e.patient) & (df.minute >= e.start) & (df.minute <= e.crisis)]
        if len(part):
            peaks.append(float(part[risk_col].max()))
    if not peaks:
        return 0.5
    return float(np.sort(np.array(peaks))[int((1 - catch) * len(peaks))])


def levels_from_tuning(tune, hours, budget):
    """The five risk levels, worked out on the dial-setting day only."""
    r = tune["risk_rf"].to_numpy()
    return dict(
        watch=pick_level(tune, r, budget * 3.0, hours),
        easy=pick_level(tune, r, budget * 1.6, hours),
        normal=pick_level(tune, r, budget * 1.0, hours),
        strict=pick_level(tune, r, budget * 0.4, hours),
        urgent=pick_level(tune, r, budget * 0.12, hours),
    )


def run_manager(df, lv, budget):
    """Walk the ward minute by minute and choose one of the five actions per patient."""
    minutes = df["minute"].to_numpy()
    pats = df["patient"].to_numpy()
    risk = df["risk_rf"].to_numpy()
    qual = df["quality_smooth"].to_numpy()
    rows = df.index.to_numpy()
    order = np.argsort(minutes, kind="stable")

    tokens = float(budget)
    refill = budget * DT / 60.0
    last_alert, last_action, hold_until = {}, {}, {}
    log, now = [], None

    for i in order:
        t, p, r, q = minutes[i], pats[i], risk[i], qual[i]
        if t != now:
            tokens, now = min(budget, tokens + refill), t
        since = t - last_alert.get(p, -10 ** 9)

        if r >= lv["urgent"] and (since >= REFRACTORY or last_action.get(p) != "urgent"):
            action = "urgent"
        elif since < REFRACTORY:
            action = "monitor"
        elif t < hold_until.get(p, -10 ** 9):
            action = "monitor"
        elif q < 0.5 and r < lv["normal"]:
            action = "ignore"
        else:
            level = lv["easy"] if tokens >= 4 else (lv["normal"] if tokens >= 2 else lv["strict"])
            if r >= level and tokens >= 1:
                action = "notify"
            elif r >= lv["watch"]:
                action = "repeat"
            else:
                action = "monitor"

        if action in ("notify", "urgent"):
            tokens -= 1
            last_alert[p] = t
            last_action[p] = action
        elif action == "repeat":
            hold_until[p] = t + 6

        log.append((t, p, rows[i], action, r))
    return pd.DataFrame(log, columns=["minute", "patient", "row", "action", "risk"])


def simulate_nurses(alerts, test, n_nurses=2):
    """Play the alerts through a ward with a fixed number of nurses."""
    import heapq
    if len(alerts) == 0:
        return alerts.assign(wait=[], seen=[]), 0.0
    t0, t1 = int(test.minute.min()), int(test.minute.max()) + 1
    arriving = {}
    for a in alerts.itertuples():
        arriving.setdefault(int(a.minute), []).append(a)
    queue, free_at, waits, busy, seq = [], [t0] * n_nurses, {}, 0, 0
    for t in range(t0, t1):
        for a in arriving.get(t, []):
            seq += 1
            heapq.heappush(queue, (0 if a.action == "urgent" else 1, t, seq, a.Index, a.action))
        for k in range(n_nurses):
            if free_at[k] <= t and queue:
                _, at, _, key, act = heapq.heappop(queue)
                mins = ACTIONS[act]["nurse_minutes"]
                free_at[k] = t + mins
                busy += mins
                waits[key] = t - at
    out = alerts.copy()
    out["wait"] = [waits.get(i, t1 - int(m)) for i, m in zip(out.index, out.minute)]
    out["seen"] = [i in waits for i in out.index]
    hours = (t1 - t0) / 60.0
    return out, busy / hours


def score(name, alerts, test, events, hours, n_nurses=2):
    truth = test["trouble"].to_numpy()
    real = truth[alerts["row"].to_numpy()] == 1 if len(alerts) else np.zeros(0, bool)
    served, delivered = simulate_nurses(alerts, test, n_nurses)

    lead, missed, reached = [], 0, 0
    for e in events.itertuples():
        hit = alerts[(alerts.patient == e.patient) &
                     (alerts.minute >= e.start) & (alerts.minute <= e.crisis)]
        if len(hit) == 0:
            missed += 1
            continue
        lead.append(e.crisis - hit.minute.min())
        s_hit = served[(served.patient == e.patient) &
                       (served.minute >= e.start) & (served.minute <= e.crisis)]
        if len(s_hit) and bool(((s_hit["minute"] + s_hit["wait"]) <= e.crisis).any()):
            reached += 1

    real_served = served[truth[served["row"].to_numpy()] == 1] if len(served) else served
    return dict(
        Model=name,
        **{"Alerts/hr": round(len(alerts) / hours, 1),
           "Never alerted": missed,
           "Nurse arrived in time": reached,
           "Early warning (min)": int(np.median(lead)) if lead else 0,
           "False alarms": int((~real).sum()),
           "Nurse min/hr": round(sum(ACTIONS[a]["nurse_minutes"] for a in alerts["action"]) / hours, 1),
           "Response (min)": int(np.median(real_served["wait"])) if len(real_served) else 0})


# --------------------------------------------------------------- figures
def _layout(fig, height=400, **kw):
    fig.update_layout(height=height, paper_bgcolor=BG, plot_bgcolor=BG, font_color="white",
                      margin=dict(l=45, r=20, t=45, b=40), legend=dict(bgcolor="rgba(0,0,0,0)"), **kw)
    fig.update_xaxes(gridcolor="#21262d")
    fig.update_yaxes(gridcolor="#21262d")
    return fig


def fig_fatigue():
    a = np.arange(1, 41)
    real = 100 * np.clip(0.35 / a, 0, 1)
    checked = 100 * np.exp(-a / 9.0)
    fig = go.Figure()
    fig.add_scatter(x=a, y=real, name="% of alarms that are real", line=dict(color=CYAN, width=3),
                    hovertemplate="At %{x} alarms an hour<br>only <b>%{y:.0f}%</b> of them are a "
                                  "real emergency<extra></extra>")
    fig.add_scatter(x=a, y=checked, name="% a nurse still checks", line=dict(color=RED, width=3),
                    hovertemplate="At %{x} alarms an hour<br>a nurse still walks over to "
                                  "<b>%{y:.0f}%</b> of them<extra></extra>")
    # The part that is going wrong, marked on the picture rather than left to the caption.
    fig.add_vrect(x0=15, x1=40, fillcolor=RED, opacity=0.10, line_width=0,
                  annotation_text="the alarm has stopped working here",
                  annotation_position="top right", annotation_font_color="white")
    fig.add_annotation(x=3, y=real[2], ax=60, ay=-45, text="quiet ward: worth checking",
                       font_color="white", arrowcolor=CYAN)
    return _layout(fig, xaxis_title="alarms per hour on the ward", yaxis_title="percent",
                   hovermode="x unified")


def fig_patient_day(ward, patient, day, title):
    part = ward[(ward.patient == patient) & (ward.day == day)]
    hours = (part.minute.to_numpy() - part.minute.min()) / 60.0
    fig = go.Figure()
    for col, name, colour, unit in ((part.hr, "heart rate", RED, "beats/min"),
                                    (part.rr * 4, "breaths/min (x4)", GREEN, "x4"),
                                    (part.spo2, "SpO2 %", CYAN, "%")):
        fig.add_scatter(x=hours, y=col, name=name, line=dict(color=colour, width=1.2),
                        hovertemplate=f"{name}: %{{y:.0f}} {unit}<br>hour %{{x:.1f}}<extra></extra>")

    # Mark the readings the equipment got wrong. Without this the student is told
    # "every spike is a sensor" and has to take it on trust.
    art = part.artifact.to_numpy() == 1 if "artifact" in part else np.zeros(len(part), bool)
    if art.any():
        # A tick along the top, not a marker on the heart-rate line: the glitch
        # can be in any of the three signals, and pinning it to one of them puts
        # the mark on a perfectly ordinary reading.
        top = float(max(part.hr.max(), (part.rr * 4).max(), part.spo2.max())) * 1.04
        fig.add_scatter(x=hours[art], y=np.full(int(art.sum()), top), mode="markers",
                        name="equipment glitch, not the patient",
                        marker=dict(color=AMBER, symbol="triangle-down", size=10),
                        hovertemplate="<b>Equipment glitch at hour %{x:.1f}</b><br>a clip or pad "
                                      "slipped, so one of the lines below jumps<br>the patient was "
                                      "fine<extra></extra>")
    tr = part.trouble.to_numpy()
    if tr.any():
        fig.add_vrect(x0=hours[tr == 1].min(), x1=hours[tr == 1].max(),
                      fillcolor=RED, opacity=0.14, line_width=0,
                      annotation_text="the patient really was getting worse here",
                      annotation_font_color="white")
    return _layout(fig, title=title, xaxis_title="hour of the day", yaxis_title="value")


def fig_alarm_sources(counts):
    values, labels = list(counts.values()), list(counts.keys())
    total = max(sum(values), 1)
    share = [100 * v / total for v in values]
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h", marker_color=[GREEN, AMBER, AMBER, GREY, GREY],
        customdata=share,
        hovertemplate="%{y}<br><b>%{x} alerts</b> - %{customdata:.0f}% of everything it "
                      "sent<extra></extra>"))
    fig.add_annotation(x=values[0], y=labels[0], ax=90, ay=0, font_color="white", arrowcolor=GREEN,
                       text="only this bar is a patient")
    return _layout(fig, height=330, xaxis_title="number of alerts",
                   title="What a fixed-limit monitor was actually beeping about")


def fig_noise_vs_illness(test):
    """The EDA chart: five measurements, averaged twice - once during a real
    deterioration, once during a false reading.

    Two panels, not one. Signal quality is a 0-1 number and the other four run
    to 20-odd, so drawn on a single axis the one pair that carries the lesson is
    two invisible slivers on the floor of the chart. Traces are added before any
    annotation: a shape or annotation attached to a subplot that has no trace
    yet is silently dropped.
    """
    sick = test[(test.trouble == 1) & (test.mins_to_crisis < 30)]
    glitch = test[(test.artifact == 1) & (test.trouble == 0)]
    off = ["hr_off", "rr_off", "spo2_off", "hr_smooth_d30"]
    off_labels = ["heart rate vs<br>own normal", "breathing vs<br>own normal",
                  "oxygen vs<br>own normal", "heart rate change<br>over 30 min"]
    series = [("real deterioration", sick, RED), ("false reading (equipment)", glitch, GREY)]

    fig = make_subplots(rows=1, cols=2, column_widths=[0.72, 0.28], horizontal_spacing=0.12,
                        subplot_titles=("How far from this patient's own normal",
                                        "How good the signal was"))
    for name, frame, colour in series:
        fig.add_bar(x=off_labels, y=frame[off].mean().values, name=name, marker_color=colour,
                    legendgroup=name,
                    hovertemplate=f"<b>{name}</b><br>%{{x}}<br>average: %{{y:.2f}}<extra></extra>",
                    row=1, col=1)
    for name, frame, colour in series:
        fig.add_bar(x=["signal quality"], y=[frame["quality"].mean()], name=name, marker_color=colour,
                    legendgroup=name, showlegend=False,
                    hovertemplate=f"<b>{name}</b><br>signal quality: %{{y:.2f}} out of 1<br>"
                                  f"1 means the sensor was perfectly attached<extra></extra>",
                    row=1, col=2)

    gap = float(sick["quality"].mean() - glitch["quality"].mean())
    fig.add_annotation(row=1, col=2, x=0, y=max(sick["quality"].mean(), glitch["quality"].mean()),
                       ay=-40, font_color="white", arrowcolor=AMBER,
                       text=f"<b>this is the one that separates them</b><br>"
                            f"quality holds up in real illness and collapses<br>"
                            f"in a false reading - a gap of {abs(gap):.2f} out of 1")
    fig.update_yaxes(range=[0, 1.15], row=1, col=2)
    fig.update_yaxes(title_text="distance from normal", row=1, col=1)
    fig = _layout(fig, barmode="group", height=470,
                  title="Real deterioration or a loose wire? The five clues, side by side")
    # The two subplot titles sit where the main title would land, so it needs its
    # own strip of margin rather than overlapping them.
    fig.update_layout(margin_t=95)
    return fig


def fig_importance(forest):
    imp = pd.Series(forest.feature_importances_, index=FEATURES).sort_values()[-12:]
    fig = go.Figure(go.Bar(
        x=imp.values, y=imp.index, orientation="h", marker_color=CYAN,
        hovertemplate="%{y}<br>the forest leans on this <b>%{x:.3f}</b> worth<br>"
                      "(all clues together add up to 1)<extra></extra>"))
    return _layout(fig, height=430, xaxis_title="how much the forest relies on this clue",
                   title="The 12 clues the forest uses most")


def fig_budget_curve(test, events, hours, budget):
    """Events caught against alerts per hour, for every setting of each method.

    The x axis is logarithmic, and on a log axis Plotly reads shape coordinates
    as log10 values - so a line drawn at x=5 lands at 100000 alerts an hour and
    silently stretches the axis over sixty decades. Every shape here is placed
    with log10() for that reason.
    """
    fig = go.Figure()
    widest = budget
    for col, name, colour in (("score01", "Risk score", GREEN), ("risk_rf", "Random forest", CYAN)):
        rate, caught = [], []
        for q in np.linspace(0.95, 0.9999, 18):
            thr = np.quantile(test[col].to_numpy(), q)
            a = to_alerts(test, test[col].to_numpy() >= thr)
            hit = sum(1 for e in events.itertuples()
                      if len(a[(a.patient == e.patient) & (a.minute >= e.start) & (a.minute <= e.crisis)]))
            rate.append(len(a) / hours)
            caught.append(hit)
        widest = max(widest, max(rate))
        fig.add_scatter(x=rate, y=caught, mode="lines+markers", name=name,
                        line=dict(color=colour, width=3),
                        hovertemplate=f"<b>{name}</b><br>allow %{{x:.1f}} alerts an hour<br>"
                                      f"catches %{{y}} of {len(events)} real events<extra></extra>")
    left, right = 0.2, max(widest * 1.6, budget * 2.5)
    fig.add_vline(x=budget, line_dash="dash", line_color="white",
                  annotation_text=f"our budget: {budget} an hour", annotation_font_color="white")
    # Everything right of the budget is a result the ward cannot buy, so it is
    # greyed out rather than left looking like an option.
    fig.add_vrect(x0=budget, x1=right, fillcolor=GREY, opacity=0.16,
                  line_width=0, annotation_text="too noisy to afford",
                  annotation_position="top right", annotation_font_color="white")
    fig.update_xaxes(type="log", range=[np.log10(left), np.log10(right)])
    return _layout(fig, xaxis_title="alerts per hour (log scale)",
                   yaxis_title=f"events caught, out of {len(events)}",
                   title="What each method could catch, for a given amount of noise")


def fig_bucket(alerts, test, budget):
    per_hour = alerts.groupby(alerts.minute // 60).size()
    full = per_hour.reindex(range(int(test.minute.min()) // 60,
                                  int(test.minute.max()) // 60 + 1), fill_value=0)
    x = np.arange(len(full))
    fig = go.Figure(go.Scatter(x=x, y=full.values, mode="lines",
                               line=dict(color=CYAN, width=1.4), name="alerts sent",
                               hovertemplate="hour %{x}<br><b>%{y} alerts</b> sent<extra></extra>"))
    over = full.values > budget
    if over.any():
        fig.add_scatter(x=x[over], y=full.values[over], mode="markers", name="over budget",
                        marker=dict(color=RED, size=9, symbol="circle-open", line=dict(width=2)),
                        hovertemplate="hour %{x}<br><b>%{y} alerts - over the budget</b><br>"
                                      "an emergency is always let through<extra></extra>")
    fig.add_hline(y=budget, line_dash="dash", line_color=RED,
                  annotation_text=f"budget = {budget}/hour", annotation_font_color="white")
    return _layout(fig, height=330, xaxis_title="hour of the exam period", yaxis_title="alerts sent",
                   title="Alerts per hour under the attention budget")


def fig_patient_trace(test, decisions, ev, lv):
    part = test[(test.patient == ev.patient) &
                (test.minute >= ev.start - 120) & (test.minute <= ev.crisis + 30)]
    dec = decisions[decisions.row.isin(part.index)]
    hours = (part.minute.to_numpy() - ev.crisis) / 60.0
    fig = go.Figure()
    fig.add_scatter(x=hours, y=part.risk_rf, name="risk", line=dict(color=VIOLET, width=2.5),
                    hovertemplate="%{x:.1f} hours before the crisis<br>the computer's worry: "
                                  "<b>%{y:.2f}</b><extra></extra>")
    fig.add_hline(y=lv["normal"], line_dash="dot", line_color=AMBER,
                  annotation_text="notify level", annotation_font_color="white")
    fig.add_hline(y=lv["urgent"], line_dash="dot", line_color=RED,
                  annotation_text="urgent level", annotation_font_color="white")
    marks = {"notify": (AMBER, "triangle-up", 13), "urgent": (RED, "star", 16),
             "repeat": (CYAN, "circle", 7), "ignore": (GREY, "x", 8)}
    for act, (colour, symbol, size) in marks.items():
        sel = dec[dec.action == act]
        if len(sel):
            costs = ACTIONS[act]["nurse_minutes"]
            spends = "interrupts a nurse" if ACTIONS[act]["alerts"] else "costs nobody anything"
            fig.add_scatter(x=(sel.minute.to_numpy() - ev.crisis) / 60.0,
                            y=np.full(len(sel), -0.06), mode="markers", name=ACTIONS[act]["label"],
                            marker=dict(color=colour, symbol=symbol, size=size),
                            hovertemplate=f"<b>{ACTIONS[act]['label']}</b><br>{spends} "
                                          f"({costs} nurse-minutes)<br>%{{x:.1f}} hours before the "
                                          f"crisis<extra></extra>")
    fig.add_vrect(x0=(ev.start - ev.crisis) / 60.0, x1=0, fillcolor=RED, opacity=0.12, line_width=0)
    fig.add_vline(x=0, line_color="white")
    return _layout(fig, height=430, xaxis_title="hours before the crisis point", yaxis_title="risk",
                   title=f"Patient {ev.patient} - {ev.kind}.  0 = the crisis point")


def fig_scoreboard(board, budget, n_events):
    cols = [("Nurse arrived in time", GREEN, f"out of {n_events}"),
            ("Alerts/hr", AMBER, f"budget {budget}"),
            ("Early warning (min)", VIOLET, "higher is better"),
            ("Response (min)", CYAN, "lower is better")]
    fig = make_subplots(rows=1, cols=4, subplot_titles=[f"{c}<br><sub>{note}</sub>" for c, _, note in cols])
    names = [m.split(". ")[-1] for m in board["Model"]]
    reading = {"Nurse arrived in time": "patients a nurse reached before the crisis",
               "Alerts/hr": "interruptions an hour",
               "Early warning (min)": "minutes of warning, typically",
               "Response (min)": "minutes a patient waited for a nurse"}
    for i, (c, colour, note) in enumerate(cols, 1):
        fig.add_bar(x=names, y=board[c], marker_color=colour, showlegend=False, row=1, col=i,
                    hovertemplate=f"<b>%{{x}}</b><br>%{{y}} {reading[c]}<br>({note})<extra></extra>")
    fig.update_xaxes(tickangle=-40)
    return _layout(fig, height=380)
