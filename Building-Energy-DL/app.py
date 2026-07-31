"""
AI for Building Energy Optimization - Deep Learning illustration app
====================================================================
One project, 30 stage pages, taught as one building energy project.
Each notebook step links here with ?stage=<id>.

The problem: a floor plate designed for 260 desks, conditioned to a clock, with
a damper that ventilates for 200 people all day. Cut the energy without a
single comfort complaint.
  Sensors : indoor/outdoor temperature, humidity, CO2, occupancy, solar, PM2.5,
            setpoint, hour.
  ML      : predict the interval's HVAC kW; flag an over-conditioned interval.
  DL      : grade a ceiling plate for occupancy, locate the busy zone (Grad-CAM).
  System  : peak forecast + setpoint limit + fusion with a COMFORT VETO.

THE PLANT MODEL IS THE NOTEBOOK'S, imported from story.py.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import r2_score

import scaffold as S
import common
import story
import bridge

POS, NEG = S.POS, S.NEG
GREEN, AMBER, RED = S.GREEN, S.AMBER, S.RED
TECH, MUTED, TEXT, PANEL = S.TECH, S.MUTED, S.TEXT, S.PANEL
style, animate = S.style, S.animate

st.set_page_config(page_title="AI for Building Energy Optimization", page_icon="🏢", layout="wide")
bridge.inject_css()

CAP, OA_DESIGN = story.CAP, story.OA_DESIGN
GRID_KG, TARIFF, LIMIT = story.GRID_KG, story.TARIFF, story.LIMIT

SENSORS = ["indoor_temp_c", "outdoor_temp_c", "humidity_pct", "co2_ppm",
           "occupancy", "solar_wm2", "pm25_ugm3", "setpoint_c"]
FEATURES = SENSORS + ["hour"]
NICE = ["Indoor (°C)", "Outdoor (°C)", "Humidity (%)", "CO₂ (ppm)", "Occupancy",
        "Solar (W/m²)", "PM2.5", "Setpoint (°C)", "Hour"]


# ----------------------------------------------------------------------------
# DATA  (the BMS export — same generator as the notebook)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="Generating sixteen weeks of BMS trend logs…")
def get_data(days=112, seed=42):
    rng = np.random.default_rng(seed)
    n = days * 96
    idx = np.arange(n)
    day = idx // 96
    hour = (idx % 96) * 0.25
    workday = ((day % 7) < 5).astype(int)

    cloud = np.repeat(rng.uniform(0.35, 1.0, days), 96)
    outdoor = (26 + 3.5 * np.sin(2 * np.pi * day / days) + 6 * np.sin(2 * np.pi * (hour - 9) / 24)
               + np.repeat(rng.normal(0, 1.8, days), 96) + rng.normal(0, 0.4, n))
    solar = np.where((hour > 6) & (hour < 19),
                     np.clip(880 * np.sin(np.pi * (hour - 6) / 13), 0, None) * cloud, 0.0)
    hum = np.clip(72 - 0.9 * (outdoor - 25) + rng.normal(0, 4, n), 30, 95)
    busy = np.repeat(rng.uniform(0.6, 1.0, days), 96)
    occ = np.clip(np.round(CAP * story.occ_shape(hour) * busy * workday
                           * rng.uniform(0.9, 1.1, n)), 0, CAP)

    sched = (hour >= 7) & (hour < 19) & (workday == 1)
    setpoint = np.where(sched, 23.0 + rng.normal(0, 0.35, n), 27.0)
    hv, cool = story.hvac_kw_for(outdoor, setpoint, solar, occ, hum)   # fixed damper
    hvac = np.where(sched, hv, 1.5)
    indoor = np.where(sched, story.indoor_for(setpoint, cool) + rng.normal(0, 0.25, n),
                      outdoor - 1.5 + rng.normal(0, 0.5, n))
    co2 = np.clip(420 + 3.1 * occ + rng.normal(0, 25, n), 400, 1600)
    pm25 = np.clip(14 + 6 * np.sin(2 * np.pi * day / 40) + rng.normal(0, 3, n), 2, 60)

    df = pd.DataFrame(dict(
        day=day, hour=hour, workday=workday,
        indoor_temp_c=indoor.round(2), outdoor_temp_c=outdoor.round(2),
        humidity_pct=hum.round(1), co2_ppm=co2.round(0), occupancy=occ,
        solar_wm2=solar.round(0), pm25_ugm3=pm25.round(1), setpoint_c=setpoint.round(2),
        hvac_kw=hvac.round(2), ppd_pct=story.ppd(indoor, hum).round(2), sched=sched.astype(int)))

    # the faults every real trend log carries
    dirty = df.copy()
    for c in SENSORS:
        dirty.loc[rng.choice(n, int(0.02 * n), replace=False), c] = np.nan
    dirty.loc[rng.choice(n, 60, replace=False), "co2_ppm"] = 400.0        # drifted CO2 sensor
    dirty.loc[rng.choice(n, 40, replace=False), "indoor_temp_c"] = 0.0    # failed zone sensor
    dirty.loc[rng.choice(n, 30, replace=False), "occupancy"] = -1.0       # counter fault
    dirty.loc[rng.choice(n, 25, replace=False), "solar_wm2"] = 9999.0     # pyranometer spike
    dirty = pd.concat([dirty, dirty.sample(40, random_state=4)], ignore_index=True)

    clean = dirty.drop_duplicates().copy()
    clean.loc[clean.indoor_temp_c < 10, "indoor_temp_c"] = np.nan
    clean.loc[clean.occupancy < 0, "occupancy"] = np.nan
    clean.loc[clean.solar_wm2 > 1200, "solar_wm2"] = np.nan
    for c in SENSORS:
        clean[c] = clean[c].fillna(clean[c].median())
    clean = clean.reset_index(drop=True)

    # only OCCUPIED hours are modelled — an empty building at setback teaches nothing
    occ_hours = clean[clean.sched == 1].reset_index(drop=True)
    scaler = MinMaxScaler()
    X = scaler.fit_transform(occ_hours[FEATURES])
    y_kw = occ_hours.hvac_kw.values
    kw_per_person = y_kw / np.clip(occ_hours.occupancy.values, 1, None)
    y_waste = (kw_per_person > LIMIT).astype(int)

    norm = occ_hours.copy()
    norm[FEATURES] = X

    gss = GroupShuffleSplit(n_splits=1, test_size=0.30, random_state=42)
    itr, itmp = next(gss.split(X, groups=occ_hours.day))
    gss2 = GroupShuffleSplit(n_splits=1, test_size=0.50, random_state=42)
    iv, ite = next(gss2.split(X[itmp], groups=occ_hours.day.values[itmp]))
    ival, iteh = itmp[iv], itmp[ite]

    return dict(dirty=dirty, clean=clean, occ_hours=occ_hours, norm=norm, scaler=scaler,
                X=X, y_kw=y_kw, y_waste=y_waste,
                Xtr=X[itr], Xval=X[ival], Xte=X[iteh],
                ytr=y_waste[itr], yval=y_waste[ival], yte=y_waste[iteh],
                KwTr=y_kw[itr], KwTe=y_kw[iteh],
                itr=itr, ival=ival, ite=iteh)


@st.cache_resource(show_spinner=False)
def get_models():
    d = get_data()
    rf = RandomForestClassifier(n_estimators=200, random_state=42).fit(d["Xtr"], d["ytr"])
    from sklearn.neural_network import MLPClassifier
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mlp = MLPClassifier(hidden_layer_sizes=(12, 6), max_iter=800,
                            random_state=42).fit(d["Xtr"], d["ytr"])
    return rf, mlp


@st.cache_resource(show_spinner=False)
def get_regressor():
    d = get_data()
    return RandomForestRegressor(n_estimators=200, random_state=42).fit(d["Xtr"], d["KwTr"])


CFG = dict(
    data=get_data, models=get_models, FEATURES=SENSORS, NICE=NICE[:8],
    unit="interval", unit_plural="intervals", pos="over-conditioned", neg="matched",
    export_name="BMS trend-log export",
    faults="A drifted CO₂ sensor (400 ppm all week), a failed zone sensor (0 °C), a broken people counter "
           "(−1) and a pyranometer spike (9,999 W/m²) all announce themselves here.",
    fault_example="9,999 W/m² pyranometer spike",
    scale_examples=[("CO₂ reads", "780 ppm"), ("Solar reads", "520 W/m²"), ("Indoor reads", "24.1 °C")],
    scale_note="Same interval, same instant. To a raw model, CO₂ looks **thirty times more important than "
               "indoor temperature** — purely because of its unit.",
    neuron_w=[0.8, 0.9, 0.4, 0.7, 1.0, 0.6, 0.1, -0.9, 0.2],
    net_pair=("occupancy", "outdoor_temp_c"),
    net_note="the low-occupancy, high-outdoor-temperature corner, where the plant works hardest for the "
             "fewest people",
    fp_cost="A zone is set back when it should not have been. Cost: a comfort complaint — and complaints "
            "are what get energy initiatives cancelled.",
    fn_cost="An empty floor keeps being conditioned for 200 people. Cost: kilowatt-hours, all day, every "
            "day, invisibly.",
    titles={"load": "⑤ The BMS export arrives", "inspect": "⑥ Sensor health check",
            "clean": "⑦ Removing the faulty readings", "normalize": "⑧ Standardising the measurements",
            "neuron": "⑯ Weighing each reading", "activation": "⑰ The setpoint threshold",
            "gradient-descent": "⑲ Commissioning the controls", "network": "⑳ The facilities team",
            "training": "㉑ Training the new recruits", "audit": "㉔ The building energy audit"},
)


# ============================================================================
# RENDERERS specific to this project
# ============================================================================
def render_split():
    st.title("⑨ Known days vs sealed days")
    d = get_data()
    st.info("🧪 **Consecutive intervals are almost identical.** The sun does not move much in fifteen "
            "minutes and the floor fills gradually. Shuffle rows and 14:00 lands in training while 14:15 "
            "lands in test — the model has effectively been shown the answer.")
    st.write("")
    oh = d["occ_hours"]
    tr = set(np.unique(oh.day.values[d["itr"]]).tolist())
    va = set(np.unique(oh.day.values[d["ival"]]).tolist())
    days = sorted(oh.day.unique().tolist())
    fig = go.Figure(go.Bar(x=days, y=[1] * len(days),
                           marker_color=[POS if x in tr else (AMBER if x in va else GREEN)
                                         for x in days], showlegend=False))
    fig.update_layout(title="whole days go to train (blue) / validate (amber) / test (green)")
    fig.update_xaxes(title="day"); fig.update_yaxes(visible=False)
    st.plotly_chart(style(fig, 260), use_container_width=True)
    c = st.columns(4)
    c[0].metric("Training days", len(tr))
    c[1].metric("Validation days", len(va))
    c[2].metric("Test days (sealed)", len(days) - len(tr) - len(va))
    c[3].metric("Over-conditioned rate", f"{d['y_waste'].mean():.1%}")
    st.write("")
    st.success("The score now measures what the model would do **on a day it has never seen**.")


def render_ml_baseline():
    st.title("⑩ Predicting cooling demand from the gauges")
    d = get_data()
    reg = get_regressor()
    pred = reg.predict(d["Xte"])
    lo, hi = float(min(d["KwTe"].min(), pred.min())), float(max(d["KwTe"].max(), pred.max()))
    fig = go.Figure(go.Scatter(x=d["KwTe"], y=pred, mode="markers",
                               marker=dict(size=5, color=POS, opacity=0.5)))
    fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines",
                             line=dict(color=MUTED, dash="dash"), showlegend=False))
    fig.update_layout(title="predicted vs metered HVAC power, on sealed days")
    fig.update_xaxes(title="metered kW"); fig.update_yaxes(title="predicted kW")
    st.plotly_chart(style(fig, 380), use_container_width=True)
    c = st.columns(2)
    c[0].metric("R² on sealed days", f"{r2_score(d['KwTe'], pred):.3f}")
    c[1].metric("Mean error", f"{np.mean(np.abs(d['KwTe']-pred)):.2f} kW")
    st.write("")

    st.markdown("##### Try an interval")
    c = st.columns(4)
    outdoor = c[0].slider("Outdoor (°C)", 24.0, 42.0, 32.0, 0.5)
    occ = c[1].slider("People on the floor", 0, CAP, 180, 5)
    solar = c[2].slider("Solar (W/m²)", 0.0, 900.0, 520.0, 20.0)
    sp = c[3].slider("Setpoint (°C)", 21.0, 27.0, 23.0, 0.5)
    hum = 58.0
    kw, cool = story.hvac_kw_for(outdoor, sp, solar, occ, hum)
    indoor = float(story.indoor_for(sp, cool))
    row = np.array([[indoor, outdoor, hum, 420 + 3.1 * occ, occ, solar, 14.0, sp, 14.0]])
    pred_kw = float(reg.predict(d["scaler"].transform(row))[0])
    per = pred_kw / max(occ, 1)
    st.write("")
    m = st.columns(4)
    m[0].metric("Predicted", f"{pred_kw:.1f} kW", f"true {float(kw):.1f}")
    m[1].metric("Indoor reached", f"{indoor:.1f} °C")
    m[2].metric("kW per person", f"{per:.2f}", f"limit {LIMIT:.2f}", delta_color="off")
    m[3].metric("PPD", f"{float(story.ppd(indoor, hum)):.1f} %")
    st.write("")
    ok = per <= LIMIT
    st.markdown(f"<div style='padding:14px;border-radius:4px;text-align:center;font-size:18px;"
                f"font-weight:700;background:{GREEN if ok else RED};color:#0e1117'>"
                f"{'✅ matched to the load' if ok else '❌ over-conditioned for the people present'}</div>",
                unsafe_allow_html=True)
    st.write("")
    st.info("Drop the occupancy to 40 without changing anything else. The kW barely moves — because the "
            "fixed damper is still bringing in fresh air for 200 people. **That is the waste this project "
            "exists to find**, and no amount of setpoint tuning removes it.")


def render_drivers():
    st.title("⑪ What drives the load")
    reg = get_regressor()
    imp = reg.feature_importances_
    order = np.argsort(imp)[::-1]
    fig = go.Figure(go.Bar(x=[NICE[i] for i in order], y=imp[order], marker_color=POS,
                           text=[f"{imp[i]:.2f}" for i in order], textposition="outside"))
    fig.update_layout(title="which channel moves the kW prediction most")
    fig.update_yaxes(title="importance")
    style(fig, 380)
    animate(fig, S.bars_grow([dict(x=[NICE[i] for i in order], y=list(imp[order]), color=POS,
                                   text=[f"{imp[i]:.2f}" for i in order])]), ms=70)
    st.plotly_chart(fig, use_container_width=True)
    st.success(f"**{NICE[int(order[0])]}** moves the prediction more than anything else.")
    st.write("")
    st.markdown("##### Importance is not the same as leverage")
    st.markdown("""
- **Outdoor temperature** usually ranks near the top and is **not a lever** — you cannot change the
  weather. It tells you when to expect a hard day, not what to do about it.
- **Setpoint and ventilation rate are the only two things you can actually change.** A lever with a
  modest importance score still beats a large score you cannot move.
- Occupancy and CO₂ move together, because CO₂ *is* a proxy for people. They are two views of one thing,
  and the camera later gives a third that neither can supply: **where** those people are.
    """)
    st.info("Use the ranking to decide what to investigate, then confirm on site. The model never "
            "authorises a setback on its own.")


def render_proof():
    st.title("㉕ The verdict")
    d = get_data()
    reg = get_regressor()
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mlp = MLPRegressor(hidden_layer_sizes=(16, 8), max_iter=1000,
                           random_state=0).fit(d["Xtr"], d["KwTr"])
    r_rf = r2_score(d["KwTe"], reg.predict(d["Xte"]))
    r_ann = r2_score(d["KwTe"], mlp.predict(d["Xte"]))
    c = st.columns(2)
    c[0].metric("Random Forest — kW R²", f"{r_rf:.3f}")
    c[1].metric("Neural network — kW R²", f"{r_ann:.3f}", f"{r_ann-r_rf:+.3f} vs RF")
    st.write("")
    st.table(pd.DataFrame({
        "": ["HVAC kW from the 9 readings", "Tell a busy floor from a sunlit empty one",
             "Say WHICH zone is in use", "Who names the features?"],
        "ML — Random Forest": ["✅ works", "❌ can't even start", "❌ no", "The engineer"],
        "DL — ANN / CNN": ["✅ works", "✅ learns the pattern", "✅ Grad-CAM", "The network learns them"],
    }))
    st.success("On the nine named channels both tools predict demand about equally well, because the "
               "engineer already named the factors. On the raw plate — where nobody can hand-write the "
               "rule — the CNN takes that part off the engineer's plate.")
    st.info("Use machine learning where an engineer has named the features: simpler, faster, easier to "
            "defend to an auditor. Use deep learning where nobody can.")


def render_forecast():
    st.title("㉖ Tomorrow's peak")
    st.caption("Many tariffs charge on the highest half-hour of the month. By the time the peak is visible "
               "on the meter it has already been set.")
    st.write("")
    hour = np.arange(0, 24, 0.25)
    c = st.columns(3)
    peak_out = c[0].slider("Tomorrow's peak outdoor temperature (°C)", 26, 42, 36, 1)
    busy = c[1].slider("Expected occupancy factor", 0.3, 1.0, 0.85, 0.05)
    precool = c[2].slider("Pre-cool by how much, from 06:00 (°C)", 0.0, 2.5, 1.5, 0.25)

    occ = np.round(CAP * story.occ_shape(hour) * busy)
    outdoor = (peak_out - 6) + 6 * np.sin(2 * np.pi * (hour - 9) / 24)
    solar = np.where((hour > 6) & (hour < 19),
                     np.clip(880 * np.sin(np.pi * (hour - 6) / 13), 0, None) * 0.85, 0.0)
    hum = np.clip(72 - 0.9 * (outdoor - 25), 30, 95)
    sched = (hour >= 7) & (hour < 19)

    sp_base = np.where(sched, 23.0, 27.0)
    kw_base, _ = story.hvac_kw_for(outdoor, sp_base, solar, occ, hum)
    kw_base = np.where(sched, kw_base, 1.5)

    # pre-cool early (cheaper, cooler outdoors), then coast up through the peak
    sp_pre = sp_base.copy()
    early = (hour >= 6) & (hour < 11)
    late = (hour >= 13) & (hour < 17)
    sp_pre = np.where(early, 23.0 - precool, sp_pre)
    sp_pre = np.where(late, 23.0 + precool * 0.8, sp_pre)
    kw_pre, cool_pre = story.hvac_kw_for(outdoor, sp_pre, solar, occ, hum)
    kw_pre = np.where(sched | early, kw_pre, 1.5)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hour, y=kw_base, mode="lines", name="run to the clock",
                             line=dict(color=NEG, width=3)))
    fig.add_trace(go.Scatter(x=hour, y=kw_pre, mode="lines", name="pre-cool, then coast",
                             line=dict(color=GREEN, width=3)))
    fig.add_hline(y=float(kw_base.max()), line=dict(color=RED, dash="dash"),
                  annotation_text=f"peak that sets the charge: {kw_base.max():.0f} kW")
    fig.update_layout(title="the demand profile, with and without pre-cooling")
    fig.update_xaxes(title="hour of day"); fig.update_yaxes(title="HVAC kW")
    style(fig, 400); animate(fig, S.line_grow(hour, kw_pre, GREEN), ms=45)
    st.plotly_chart(fig, use_container_width=True)

    e_base = float(np.sum(kw_base) * 0.25); e_pre = float(np.sum(kw_pre) * 0.25)
    m = st.columns(4)
    m[0].metric("Peak, to the clock", f"{kw_base.max():.0f} kW")
    m[1].metric("Peak, pre-cooled", f"{kw_pre.max():.0f} kW",
                f"{kw_pre.max()-kw_base.max():+.0f} kW")
    m[2].metric("Energy, to the clock", f"{e_base:,.0f} kWh")
    m[3].metric("Energy, pre-cooled", f"{e_pre:,.0f} kWh", f"{e_pre-e_base:+,.0f} kWh")
    st.write("")

    if e_pre > e_base:
        st.warning(f"**Read both numbers.** Pre-cooling shaves the peak by "
                   f"**{kw_base.max()-kw_pre.max():.0f} kW** and uses **{e_pre-e_base:,.0f} kWh more "
                   f"energy** doing it. On a demand-charge tariff that trade can be strongly worth "
                   f"making; on a flat tariff it is simply a loss. **The tariff decides, not the model.**")
    else:
        st.success(f"Here pre-cooling shaves the peak **and** uses less energy, because the plant is doing "
                   f"its work when the outdoor temperature — and so the chiller COP — is more favourable.")
    st.info("This is why the peak has to be *forecast*. Acting after the meter shows it is too late: the "
            "charge for the whole month is already set.")


def render_setpoint():
    st.title("㉗ Choosing the setpoint")
    st.caption("Raising the setpoint always saves energy. There is no interior minimum — so comfort has to "
               "supply the limit.")
    st.write("")
    c = st.columns(3)
    occ = c[0].slider("People on the floor", 0, CAP, 180, 5)
    outdoor = c[1].slider("Outdoor (°C)", 26, 42, 32, 1)
    dcv = c[2].toggle("Ventilate for the people present (not for 200)", value=False)

    oa = float(np.clip(occ, 20, OA_DESIGN)) if dcv else None
    sps, kw, cm = story.sweep(occ, outdoor=outdoor, oa=oa)
    ok = cm <= 10.0
    best = float(sps[ok][-1]) if ok.any() else float(sps[0])
    kw_at_best = float(np.interp(best, sps, kw))
    kw_at_23 = float(np.interp(23.0, sps, kw))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sps, y=kw, mode="lines", name="HVAC kW",
                             line=dict(color=POS, width=3), yaxis="y"))
    fig.add_trace(go.Scatter(x=sps, y=cm, mode="lines", name="PPD %",
                             line=dict(color=AMBER, width=3, dash="dot"), yaxis="y2"))
    fig.add_hline(y=10, line=dict(color=RED, dash="dash"),
                  annotation_text="comfort limit: PPD = 10%", yref="y2")
    fig.add_vline(x=best, line=dict(color=GREEN, width=2),
                  annotation_text=f"as far as you may go: {best:.2f} °C")
    fig.update_layout(title="energy falls the whole way; comfort decides where to stop",
                      yaxis=dict(title="HVAC kW"),
                      yaxis2=dict(title="PPD %", overlaying="y", side="right", range=[0, 40]))
    fig.update_xaxes(title="cooling setpoint (°C)")
    st.plotly_chart(style(fig, 420), use_container_width=True)

    m = st.columns(4)
    m[0].metric("At 23.0 °C", f"{kw_at_23:.1f} kW")
    m[1].metric("At the comfort limit", f"{kw_at_best:.1f} kW", f"{kw_at_best-kw_at_23:+.1f} kW")
    m[2].metric("Setpoint you may reach", f"{best:.2f} °C")
    m[3].metric("Saving", f"{(kw_at_23-kw_at_best)/max(kw_at_23,1e-9)*100:.0f} %")
    st.write("")

    st.markdown("##### What the two curves are telling you")
    st.markdown("""
- The **energy curve has no bottom**. It falls all the way to the right, so "optimise the setpoint for
  energy" has no answer on its own — the honest answer would be "switch the plant off".
- The **comfort curve supplies the constraint**. Where PPD crosses 10% is where you must stop, and that
  is what makes an optimum exist at all. This is a *constrained* optimisation, not a minimisation.
- **Now turn on demand-led ventilation** with the toggle above. The whole energy curve drops, and it
  drops *without touching the setpoint* — so it costs no comfort at all.
    """)
    st.success("That is the difference between the two kinds of saving in this project. Raising the "
               "setpoint **spends comfort** to buy kilowatt-hours. Ventilating for the people who are "
               "actually there **spends nothing** — which is why it is the first thing to fix.")


def render_dashboard():
    st.title("㉚ The smart building dashboard")
    st.caption("Everything above becomes numbers an owner can approve — with the comfort index reported "
               "next to the saving, not after it.")
    st.write("")
    c = st.columns(3)
    floors = c[0].slider("Floor plates in the portfolio", 1, 60, 12, 1)
    dcv_share = c[1].slider("Share of hours demand-led ventilation is applied (%)", 0, 100, 70, 5)
    sp_relax = c[2].slider("Setpoint relaxation allowed (°C)", 0.0, 2.0, 0.75, 0.25)

    hour = np.arange(7, 19, 0.25)
    occ = np.round(CAP * story.occ_shape(hour) * 0.7)
    outdoor = 26 + 6 * np.sin(2 * np.pi * (hour - 9) / 24)
    solar = np.clip(880 * np.sin(np.pi * (hour - 6) / 13), 0, None) * 0.8
    hum = np.clip(72 - 0.9 * (outdoor - 25), 30, 95)

    kw_base, cool_b = story.hvac_kw_for(outdoor, 23.0, solar, occ, hum)
    oa = np.where(np.arange(len(hour)) % 100 < dcv_share, np.clip(occ, 20, OA_DESIGN), OA_DESIGN)
    kw_ai, cool_a = story.hvac_kw_for(outdoor, 23.0 + sp_relax, solar, occ, hum, oa)

    day_base = float(np.sum(kw_base) * 0.25)
    day_ai = float(np.sum(kw_ai) * 0.25)
    DAYS = 250
    kwh_saved = (day_base - day_ai) * DAYS * floors
    co2 = kwh_saved * GRID_KG / 1000.0
    money = kwh_saved * TARIFF
    ppd_base = float(np.mean(story.ppd(story.indoor_for(23.0, cool_b), hum)))
    ppd_ai = float(np.mean(story.ppd(story.indoor_for(23.0 + sp_relax, cool_a), hum)))

    k = st.columns(4)
    k[0].metric("Energy avoided", f"{kwh_saved/1000:,.0f} MWh / year")
    k[1].metric("Carbon avoided", f"{co2:,.0f} t CO₂ / year")
    k[2].metric("Cost avoided", f"{money:,.0f} / year")
    k[3].metric("Comfort (PPD)", f"{ppd_ai:.1f} %", f"{ppd_ai-ppd_base:+.1f} vs today",
                delta_color="inverse")
    st.write("")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Before — clock & fixed damper", "After — demand-led"],
                         y=[day_base * DAYS * floors / 1000, day_ai * DAYS * floors / 1000],
                         marker_color=[RED, GREEN],
                         text=[f"{day_base*DAYS*floors/1000:,.0f} MWh",
                               f"{day_ai*DAYS*floors/1000:,.0f} MWh"], textposition="outside"))
    fig.update_layout(title="annual HVAC energy across the portfolio", showlegend=False)
    fig.update_yaxes(title="MWh per year")
    style(fig, 380)
    animate(fig, S.bars_grow([dict(x=["Before — clock & fixed damper", "After — demand-led"],
                                   y=[day_base*DAYS*floors/1000, day_ai*DAYS*floors/1000],
                                   color=GREEN,
                                   text=[f"{day_base*DAYS*floors/1000:,.0f} MWh",
                                         f"{day_ai*DAYS*floors/1000:,.0f} MWh"])]), ms=90)
    st.plotly_chart(fig, use_container_width=True)
    st.write("")

    if ppd_ai > 10:
        st.error(f"**Stop.** The comfort index has gone to **{ppd_ai:.1f}%**, past the 10% limit. This "
                 f"saving will produce complaints and be withdrawn. Reduce the setpoint relaxation until "
                 f"PPD is back under the limit — the ventilation saving costs no comfort and can stay.")
    else:
        st.info(f"With **{floors} floor plates**, demand-led ventilation on **{dcv_share}%** of hours and "
                f"**{sp_relax:.2f} °C** of setpoint relaxation, the portfolio avoids "
                f"**{kwh_saved/1000:,.0f} MWh** and **{co2:,.0f} t CO₂** a year — with PPD at "
                f"**{ppd_ai:.1f}%**, still inside the comfort limit.")
    st.warning("**Read the assumptions, not just the total.** Every figure is arithmetic on the three "
               "sliders. Push the setpoint slider up and watch the saving rise and the comfort metric go "
               "with it — that is the trade this whole project exists to make visible, and the reason "
               "comfort holds the veto.")


# ============================================================================
# THE COURSE, AS ONE BUILDING ENERGY PROJECT
# ============================================================================
STAGES = {
    "start":            ("⓪ The project — read this first", bridge.render_start),
    "in-use":           ("① A building on a weekday", lambda: story.render_in_use(style, animate)),
    "enter-ai":         ("② A building that senses itself", lambda: story.render_enter_ai(style, animate)),
    "reading":          ("③ One 15-minute interval", lambda: story.render_reading(get_data, style, animate)),
    "two-records":      ("④ Sensor row vs camera frame", lambda: story.render_two_records(style, animate)),
    "load":             ("⑤ The BMS export arrives", lambda: common.render_load(CFG)),
    "inspect":          ("⑥ Sensor health check", lambda: common.render_inspect(CFG)),
    "clean":            ("⑦ Removing the faulty readings", lambda: common.render_clean(CFG)),
    "normalize":        ("⑧ Standardising the measurements", lambda: common.render_normalize(CFG)),
    "split":            ("⑨ Known days vs sealed days", render_split),
    "ml-baseline":      ("⑩ Predicting cooling demand", render_ml_baseline),
    "drivers":          ("⑪ What drives the load", render_drivers),
    "camera-problem":   ("⑫ What the ceiling camera sends", lambda: story.render_camera_problem(style, animate)),
    "handmade":         ("⑬ Counting people by brightness", lambda: story.render_handmade(style, animate)),
    "why-dl":           ("⑭ Why the rulebook ran out", lambda: story.render_why_dl(style)),
    "engineer-brain":   ("⑮ How a facilities engineer decides", lambda: story.render_engineer_brain(style)),
    "neuron":           ("⑯ Weighing each reading", lambda: common.render_neuron(CFG)),
    "activation":       ("⑰ The setpoint threshold", lambda: common.render_activation(CFG)),
    "learning-loop":    ("⑱ Improving after every bad day", lambda: story.render_learning_loop(style, animate)),
    "gradient-descent": ("⑲ Commissioning the controls", lambda: common.render_gradient_descent(CFG)),
    "network":          ("⑳ The facilities team", lambda: common.render_network(CFG)),
    "training":         ("㉑ Training the new recruits", lambda: common.render_training(CFG)),
    "cnn-journey":      ("㉒ Reading the floor plate", lambda: story.render_cnn_journey(style, animate)),
    "occupancy-locate": ("㉓ Which part of the floor is in use", lambda: story.render_occupancy_locate(style, animate)),
    "audit":            ("㉔ The building energy audit", lambda: common.render_audit(CFG)),
    "proof":            ("㉕ The verdict", render_proof),
    "forecast":         ("㉖ Tomorrow's peak", render_forecast),
    "setpoint":         ("㉗ Choosing the setpoint", render_setpoint),
    "fusion-engine":    ("㉘ The building intelligence engine", lambda: story.render_fusion_engine(style)),
    "pipeline":         ("㉙ The whole system", lambda: story.render_pipeline(style, animate)),
    "dashboard":        ("㉚ The smart building dashboard", render_dashboard),
}

ALIASES = {"overview": "in-use", "camera": "camera-problem", "fusion": "fusion-engine",
           "importance": "drivers", "cnn": "cnn-journey", "gradcam": "occupancy-locate",
           "optimize": "setpoint", "anomaly": "forecast"}

stage = bridge.route(STAGES, ALIASES)

if stage != "start":
    bridge.open_page(stage)

STAGES[stage][1]()

if stage != "start":
    bridge.close_page(stage)

S.footer_nav(STAGES, stage)
