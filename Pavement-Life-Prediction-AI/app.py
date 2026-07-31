"""
AI for Pavement Remaining Service Life Prediction — the interactive learning app.
================================================================================
A conceptual companion to the Colab notebook, and completely independent of it.
The notebook teaches implementation. This app teaches understanding.

Nothing here reads the notebook's CSV. The survey is regenerated in-app from the
same published relationships (AASHTO 1993, the AASHO fourth-power law, Miner's
rule), so the two deliverables always tell the same story without being coupled.

Run:  streamlit run app.py
Deep link a stage:  ?stage=<id>   (ids are bridge.ORDER)
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.tree import DecisionTreeRegressor, export_text
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.inspection import permutation_importance

import bridge

# ----------------------------------------------------------------------------
# THEME  (identical language to the sibling apps)
# ----------------------------------------------------------------------------
BG, PANEL = "#0e1117", "#161b22"
CIVIL, AISIDE, TECH = "#ffb74d", "#4fc3f7", "#ba68c8"
GREEN, AMBER, RED = "#66bb6a", "#ffb74d", "#ef5350"
MUTED, TEXT = "#8b949e", "#e6edf3"
INK, STEEL, EDGE = "#0b0e13", "#141b24", "#2b3440"

FEATURES = ["traffic_volume_vpd", "pavement_thickness_mm", "pavement_age_years",
            "rainfall_mm_year", "avg_temperature_c", "crack_density_pct"]
NICE = ["Traffic (veh/day)", "Thickness (mm)", "Age (years)",
        "Rainfall (mm/yr)", "Temperature (°C)", "Cracking (%)"]
TARGET = "remaining_life_years"

ACTIONS = ["Continue normal operation", "Schedule preventive maintenance",
           "Major rehabilitation required", "Reconstruction recommended"]
ACT_COLORS = [GREEN, AISIDE, AMBER, RED]

# Treatment costs, rupees per lane-kilometre — the agency's schedule of rates.
COST_PREVENTIVE, COST_REHAB, COST_RECON = 1_800_000, 6_500_000, 22_000_000
SERVICE_LIFE = 20.0
BUDGET_KM_YEAR = 105

st.set_page_config(page_title="AI for Pavement Life Prediction", page_icon="🛣️",
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
    x, y = np.asarray(x), np.asarray(y)
    n = len(x)
    ks = sorted(set(list(range(2, n + 1, max(1, n // nf))) + [n]))
    return [go.Frame(data=[go.Scatter(x=x[:k], y=y[:k], mode="lines",
                                      line=dict(color=color, width=width))], name=str(k))
            for k in ks]


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


# ============================================================================
# THE PAVEMENT MODEL
# The same published relationships the notebook uses. They generate the survey
# AND drive every "try it" tool on these pages, so the two never disagree.
# ============================================================================
ZR, SO = -1.282, 0.45          # 90% reliability, overall standard deviation
PSI0, PSI_TERM = 4.2, 2.5      # initial and terminal serviceability
LANE_F, DIR_F = 0.90, 0.50


def esal_factor(axle_kn):
    """Damage of one axle relative to the 80 kN standard axle (AASHO Road Test)."""
    return np.power(np.asarray(axle_kn, float) / 80.0, 4.0)


def structural_number(ac_mm, base_mm, subbase_mm, m2=1.0, m3=1.0):
    """AASHTO 1993 structural number. Layer coefficients are per inch."""
    return (0.44 * np.asarray(ac_mm, float) / 25.4
            + 0.14 * np.asarray(base_mm, float) / 25.4 * m2
            + 0.11 * np.asarray(subbase_mm, float) / 25.4 * m3)


def allowable_esals(sn, mr_psi):
    """AASHTO 1993 design equation solved for W18 — the ESALs the structure carries."""
    sn = np.asarray(sn, float)
    dpsi = np.log10((PSI0 - PSI_TERM) / (PSI0 - 1.5))
    denom = 0.40 + 1094.0 / np.power(sn + 1.0, 5.19)
    log_w18 = (ZR * SO + 9.36 * np.log10(sn + 1.0) - 0.20 + dpsi / denom
               + 2.32 * np.log10(np.asarray(mr_psi, float)) - 8.07)
    return np.power(10.0, log_w18)


def annual_esals(aadt, truck_pct, truck_factor):
    return aadt * (truck_pct / 100.0) * truck_factor * 365.0 * LANE_F * DIR_F


def env_multiplier(temp_c, rain_mm):
    """How much faster this climate consumes the structure than the design assumption."""
    hot = 1.0 + 0.030 * (temp_c - 25.0)
    wet = 1.0 + 0.20 * np.clip((rain_mm - 800.0) / 1800.0, 0, 1)
    return hot * wet


def climate_life(temp_c, rain_mm, quality=1.0):
    """Years to terminal condition from ageing alone, with no traffic at all."""
    return (24.5 - 0.30 * (temp_c - 24.0) - 2.5 * (rain_mm - 900.0) / 1000.0) * quality


def remaining_years(capacity, consumed, esal_year_eff, growth):
    rem = np.maximum(capacity - consumed, 0.0)
    return np.log1p(growth * rem / esal_year_eff) / np.log1p(growth)


CLASSES = {
    "National Highway": dict(n=42, aadt=(18000, 46000), truck=(12, 18), tf=(3.8, 4.6),
                             ac=(210, 310), growth=(0.035, 0.055)),
    "State Highway":    dict(n=54, aadt=(6000, 20000), truck=(7, 13), tf=(2.8, 3.6),
                             ac=(140, 225), growth=(0.025, 0.045)),
    "District Road":    dict(n=54, aadt=(800, 7000), truck=(4, 9), tf=(1.8, 2.6),
                             ac=(70, 140), growth=(0.015, 0.035)),
}
ZONES = {"Arid": dict(rain=(300, 750), temp=(27, 38)),
         "Moderate": dict(rain=(750, 1500), temp=(21, 32)),
         "Wet": dict(rain=(1500, 3000), temp=(22, 33))}
DISTRICTS = ["Anantpur", "Bilaspur", "Chittoor", "Dharwad", "Erode", "Kadapa", "Latur", "Nashik"]


@st.cache_data(show_spinner="Running the network condition survey…")
def get_survey():
    """The agency's survey export — clean version, plus the raw faults for the
    inspection and cleaning pages."""
    rng = np.random.default_rng(42)
    rows, rid = [], 0
    for cls, spec in CLASSES.items():
        for _ in range(spec["n"]):
            rid += 1
            zone = rng.choice(list(ZONES), p=[0.30, 0.42, 0.28])
            z = ZONES[zone]
            road = f"{cls.split()[0][:2].upper()}-{rid:03d}"

            aadt_road = rng.uniform(*spec["aadt"])
            truck_pct = rng.uniform(*spec["truck"])
            tf = rng.uniform(*spec["tf"])
            growth = rng.uniform(*spec["growth"])
            ac_road = rng.uniform(*spec["ac"])
            base_mm = rng.uniform(230, 290)
            subbase = rng.uniform(190, 260)
            mr_psi = rng.uniform(6000, 10000) * (0.90 if zone == "Wet" else 1.0)
            drainage = rng.uniform(0.60, 1.0)
            quality = rng.uniform(0.90, 1.10)
            rater = rng.uniform(0.90, 1.12)
            age_road = rng.uniform(1.0, 23.0)
            rain = rng.uniform(*z["rain"])
            temp = rng.uniform(*z["temp"])
            district = rng.choice(DISTRICTS)
            m = float(np.clip(1.20 - 0.30 * (rain / 3000.0) - 0.25 * (1.0 - drainage), 0.70, 1.20))

            for seg in range(1, int(rng.integers(7, 14)) + 1):
                ac = max(45.0, ac_road + rng.normal(0, 11))
                aadt = aadt_road * rng.uniform(0.85, 1.15)
                age = max(0.5, age_road + rng.normal(0, 0.6))
                rn = max(150.0, rain + rng.normal(0, 60))
                tp = temp + rng.normal(0, 0.8)

                sn = float(structural_number(ac, base_mm, subbase, m, m))
                cap = float(allowable_esals(sn, mr_psi)) * quality
                env = float(env_multiplier(tp, rn))
                e_now = annual_esals(aadt, truck_pct, tf)
                e_0 = e_now / np.power(1.0 + growth, age)
                used = env * (e_now - e_0) / growth

                rsl_load = remaining_years(cap, used, e_now * env, growth)
                life_env = float(climate_life(tp, rn, quality))
                rsl = float(np.clip(min(rsl_load, life_env - age), 0.0, 25.0))

                dmg_load = used / cap
                dmg = float(np.clip(max(dmg_load, age / life_env), 0.0, 1.6))
                fatigue = 46.0 * float(np.clip(dmg_load, 0.0, 1.5)) ** 2.2
                thermal = (0.60 * max(0.0, age - 6.0) * (1.0 + 0.05 * (tp - 27.0))
                           * (1.25 if rn < 700 else 1.0))
                crack = (fatigue + thermal) * (2.0 - quality) * rater + rng.normal(0, 2.2)
                iri = (1.8 + 3.4 * dmg + (0.6 if cls == "District Road" else 0.0)
                       + rng.normal(0, 0.22))
                defl = ((0.12 + 1.0 / sn) * np.sqrt(7000.0 / mr_psi) * (1.0 + 0.40 * dmg_load)
                        + rng.normal(0, 0.025))

                rows.append(dict(
                    segment_id=f"{road}/{seg:02d}", road_id=road, road_class=cls,
                    district=district, climate_zone=zone,
                    traffic_volume_vpd=round(aadt, -1),
                    pavement_thickness_mm=round(ac, 1),
                    pavement_age_years=round(age, 1),
                    rainfall_mm_year=round(rn, 0),
                    avg_temperature_c=round(tp, 1),
                    crack_density_pct=round(float(np.clip(crack, 0.2, 72.0)), 1),
                    surface_roughness_iri=round(float(np.clip(iri, 1.4, 9.0)), 2),
                    deflection_mm=round(float(np.clip(defl, 0.12, 2.2)), 3),
                    remaining_life_years=round(rsl, 2)))
    clean = pd.DataFrame(rows)

    # the same file before anybody corrected it
    raw = clean.copy()
    n = len(raw)
    raw.loc[rng.choice(n, 18, replace=False), "crack_density_pct"] = -1.0
    raw.loc[rng.choice(n, 14, replace=False), "pavement_thickness_mm"] = 0.0
    raw.loc[rng.choice(n, 26, replace=False), "rainfall_mm_year"] = np.nan
    raw.loc[rng.choice(n, 9, replace=False), "traffic_volume_vpd"] = 0.0
    idx = rng.choice(n, 11, replace=False)
    raw.loc[idx, "pavement_age_years"] = -raw.loc[idx, "pavement_age_years"]
    kad = raw["district"] == "Kadapa"
    raw.loc[kad, "avg_temperature_c"] = (raw.loc[kad, "avg_temperature_c"] * 9 / 5 + 32).round(1)
    dup = raw.loc[rng.choice(n, 12, replace=False)]
    raw = pd.concat([raw, dup], ignore_index=True)
    return clean, raw


@st.cache_resource(show_spinner="Fitting the deterioration models…")
def get_models():
    clean, _ = get_survey()
    X = clean[FEATURES].to_numpy(float)
    y = clean[TARGET].to_numpy(float)
    groups = clean["road_id"].to_numpy()

    tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.30, random_state=42)
                  .split(X, y, groups))
    scaler = StandardScaler().fit(X[tr])

    lin = LinearRegression().fit(scaler.transform(X[tr]), y[tr])
    rf = RandomForestRegressor(n_estimators=220, min_samples_leaf=2,
                               random_state=42, n_jobs=-1).fit(X[tr], y[tr])
    gb = GradientBoostingRegressor(n_estimators=300, learning_rate=0.06, max_depth=4,
                                   subsample=0.9, random_state=42).fit(X[tr], y[tr])

    preds = {"Linear Regression": lin.predict(scaler.transform(X[te])),
             "Random Forest": rf.predict(X[te]),
             "Gradient Boosting": gb.predict(X[te])}
    age_te = X[te][:, FEATURES.index("pavement_age_years")]
    preds["Fixed 20-year cycle"] = np.clip(20.0 - age_te, 0, 25)

    scores = {k: dict(mae=mean_absolute_error(y[te], v),
                      rmse=float(np.sqrt(np.mean((y[te] - v) ** 2))),
                      r2=r2_score(y[te], v)) for k, v in preds.items()}
    best = min(("Linear Regression", "Random Forest", "Gradient Boosting"),
               key=lambda k: scores[k]["mae"])
    return dict(clean=clean, X=X, y=y, tr=tr, te=te, scaler=scaler,
                lin=lin, rf=rf, gb=gb, preds=preds, scores=scores, best=best)


def predict_life(row, name=None):
    """Predicted remaining service life (years) for one segment given the six inputs."""
    M = get_models()
    name = M["best"] if name is None else name
    x = np.array([[row[f] for f in FEATURES]], float)
    if name == "Linear Regression":
        return float(np.clip(M["lin"].predict(M["scaler"].transform(x))[0], 0, 25))
    mdl = M["rf"] if name == "Random Forest" else M["gb"]
    return float(np.clip(mdl.predict(x)[0], 0, 25))


def recommend(years, crack, thickness, traffic):
    """Treatment and reasons for one segment. Overrides may only escalate."""
    act = 0 if years > 10 else 1 if years > 5 else 2 if years > 2 else 3
    why = [f"{years:.1f} years of predicted life remaining" if years > 10 else
           f"{years:.1f} years left — inside the preventive window" if years > 5 else
           f"{years:.1f} years left — past the preventive window" if years > 2 else
           f"{years:.1f} years left — at or near terminal condition"]
    if crack >= 60:
        act = max(act, 3); why.append(f"cracking {crack:.0f}% — surface integrity lost")
    elif crack >= 45:
        act = max(act, 2); why.append(f"cracking {crack:.0f}% — water reaching the base")
    elif crack >= 25 and act == 0:
        act = max(act, 1); why.append(f"cracking {crack:.0f}% — seal before it propagates")
    if thickness < 100 and traffic > 15000:
        act = min(act + 1, 3)
        why.append(f"{thickness:.0f} mm under {traffic:,.0f} vpd — structurally under-designed")
    return ACTIONS[act], act, " · ".join(why)


SEGMENT = dict(traffic_volume_vpd=22000, pavement_thickness_mm=240, pavement_age_years=12,
               rainfall_mm_year=1100, avg_temperature_c=31.0, crack_density_pct=18.0)


def physical_crack(traffic, thickness, age, rain, temp, truck_pct=12.0,
                   tf=3.4, growth=0.035, base=250.0, subbase=200.0, mr=8000.0):
    """The crack density this structure WOULD show, from the same physics that built
    the survey. Used where holding cracking fixed would be physically incoherent."""
    sn = float(structural_number(thickness, base, subbase))
    cap = float(allowable_esals(sn, mr))
    env = float(env_multiplier(temp, rain))
    e_now = annual_esals(traffic, truck_pct, tf)
    used = env * (e_now - e_now / (1.0 + growth) ** age) / growth
    dmg_load = used / cap
    fatigue = 46.0 * float(np.clip(dmg_load, 0.0, 1.5)) ** 2.2
    thermal = (0.60 * max(0.0, age - 6.0) * (1.0 + 0.05 * (temp - 27.0))
               * (1.25 if rain < 700 else 1.0))
    return float(np.clip(fatigue + thermal, 0.2, 72.0))


# ============================================================================
# SHARED FIGURES
# ============================================================================
def cross_section_fig(ac, base, subbase, title="Pavement cross-section"):
    """An interactive layer diagram, drawn to scale in millimetres."""
    fig = go.Figure()
    layers = [("Bituminous layers", ac, "#37474f", CIVIL),
              ("Granular base", base, "#4e342e", "#a1887f"),
              ("Granular sub-base", subbase, "#3e2723", "#8d6e63")]
    y = 0.0
    for name, t, fill, edge in layers:
        fig.add_shape(type="rect", x0=0, x1=10, y0=y, y1=y + t,
                      fillcolor=fill, line=dict(color=edge, width=2), layer="below")
        fig.add_annotation(x=5, y=y + t / 2, text=f"<b>{name}</b> — {t:.0f} mm",
                           showarrow=False, font=dict(size=13, color=TEXT))
        y += t
    fig.add_shape(type="rect", x0=0, x1=10, y0=-160, y1=0,
                  fillcolor="#2d2016", line=dict(color="#6d4c41", width=2), layer="below")
    fig.add_annotation(x=5, y=-80, text="<b>Subgrade</b> — the soil everything rests on",
                       showarrow=False, font=dict(size=13, color=MUTED))
    # a wheel load on the surface
    fig.add_annotation(x=5, y=y + 95, text="🚛", showarrow=False, font=dict(size=40))
    for dx in (-0.9, 0.9):
        fig.add_annotation(x=5 + dx, y=y + 8, ax=5 + dx, ay=y + 70,
                           xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1.3, arrowwidth=3,
                           arrowcolor=RED, text="")
    fig.update_xaxes(visible=False, range=[-0.4, 10.4])
    fig.update_yaxes(title="depth (mm)", range=[-170, y + 150], gridcolor="#222933")
    fig.update_layout(title=title)
    return style(fig, 460)


def _score_table():
    M = get_models()
    order = ["Fixed 20-year cycle", "Linear Regression", "Random Forest", "Gradient Boosting"]
    return pd.DataFrame([dict(model=k, **M["scores"][k]) for k in order]).set_index("model")


# ============================================================================
# PHASE 1 — THE ROAD NETWORK
# ============================================================================
def render_road_network():
    clean, _ = get_survey()
    st.subheader("The network, and the budget that has to cover it")

    c = st.columns(3)
    segments = c[0].slider("Segments in the network", 400, 3000, 1500, 100)
    budget_km = c[1].slider("Kilometres treatable per year", 30, 400, BUDGET_KM_YEAR, 5)
    cycle = c[2].slider("Inspection cycle (years)", 1, 6, 3, 1)

    k = st.columns(4)
    k[0].metric("Segments", f"{segments:,}")
    k[1].metric("Treatable per year", f"{budget_km} km")
    k[2].metric("Share of network", f"{budget_km/segments:.1%}")
    k[3].metric("Years to cover it once", f"{segments/budget_km:,.0f}")

    st.info(f"At **{budget_km} km a year** it takes **{segments/budget_km:,.0f} years** to touch the "
            f"whole network once, while the pavements deteriorate continuously and get inspected only "
            f"every **{cycle} years**. That gap is the problem this course is about.")

    st.divider()
    st.markdown("##### Two segments, built the same year, to the same drawing")
    years = np.linspace(0, 25, 120)

    def psi(life):
        return PSI0 - (PSI0 - PSI_TERM) * np.clip(years / life, 0, 1.45) ** 2.4

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=psi(9.5), mode="lines", name="carries loaded trucks",
                             line=dict(color=RED, width=3)))
    fig.add_trace(go.Scatter(x=years, y=psi(21.0), mode="lines", name="carries cars",
                             line=dict(color=GREEN, width=3)))
    fig.add_hline(y=PSI_TERM, line_dash="dash", line_color=MUTED,
                  annotation_text="terminal condition — intervention")
    fig.update_layout(title="the same drawing, eight years apart in condition")
    fig.update_xaxes(title="years since construction")
    fig.update_yaxes(title="present serviceability index", range=[1.8, 4.4])
    style(fig, 400)
    animate(fig, [go.Frame(data=[
        go.Scatter(x=years[:k2], y=psi(9.5)[:k2], mode="lines", line=dict(color=RED, width=3)),
        go.Scatter(x=years[:k2], y=psi(21.0)[:k2], mode="lines", line=dict(color=GREEN, width=3)),
    ]) for k2 in range(2, len(years) + 1, 4)], ms=60)
    st.plotly_chart(fig, use_container_width=True, key="rn_psi")
    st.caption("▶ Press Play. A fixed maintenance cycle gives both of these segments the same answer.")

    st.divider()
    st.markdown("##### The real network, right now")
    fig = go.Figure()
    for cls, colr in zip(CLASSES, [RED, AMBER, AISIDE]):
        sub = clean[clean["road_class"] == cls]
        fig.add_trace(go.Histogram(x=sub[TARGET], name=cls, marker_color=colr,
                                   opacity=0.75, nbinsx=40))
    fig.update_layout(barmode="overlay", title="remaining service life across the network")
    fig.update_xaxes(title="remaining service life (years)")
    fig.update_yaxes(title="segments")
    st.plotly_chart(style(fig, 380), use_container_width=True, key="rn_hist")
    st.caption(f"{(clean[TARGET] <= 0.05).mean():.0%} of the network is already at or past terminal "
               f"condition. The median segment has {clean[TARGET].median():.1f} years left.")


def render_enter_ai():
    st.subheader("Who decides what")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='sign'><b style='color:{CIVIL}'>👷 The engineer stays in charge of</b>"
                    f"<ul style='margin:8px 0 0 -12px'>"
                    f"<li>Reading a core, judging a subgrade</li>"
                    f"<li>Knowing the drainage was never built</li>"
                    f"<li>Sequencing work around the monsoon</li>"
                    f"<li>Signing the estimate</li>"
                    f"<li>Carrying the consequence</li></ul></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='sign ai'><b style='color:{AISIDE}'>🤖 Where one person needs help</b>"
                    f"<ul style='margin:8px 0 0 -12px'>"
                    f"<li>Assessing 1,500 segments every cycle</li>"
                    f"<li>Comparing today against 20 years of records</li>"
                    f"<li>Weighing six interacting factors at once</li>"
                    f"<li>Never having an off week</li>"
                    f"<li>—</li></ul></div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("##### The four treatments, and why the timing decision matters")
    costs = [0, COST_PREVENTIVE, COST_REHAB, COST_RECON]
    fig = go.Figure(go.Bar(x=ACTIONS, y=[c / 1e5 for c in costs], marker_color=ACT_COLORS,
                           text=[("—" if c == 0 else f"₹{c/1e5:.0f} lakh/km") for c in costs],
                           textposition="outside"))
    fig.update_layout(title="cost per lane-kilometre, by treatment", showlegend=False)
    fig.update_yaxes(title="₹ lakh per km")
    style(fig, 400)
    animate(fig, _bars_grow([dict(x=ACTIONS, y=[c / 1e5 for c in costs], color=CIVIL,
                                  text=[("—" if c == 0 else f"₹{c/1e5:.0f} lakh/km")
                                        for c in costs])]), ms=90)
    st.plotly_chart(fig, use_container_width=True, key="ea_costs")
    st.warning(f"A reconstruction costs about **{COST_RECON/COST_PREVENTIVE:.0f}×** a preventive "
               f"treatment. The whole value of predicting remaining life is arriving while the cheap "
               f"treatment still works.")


# ============================================================================
# PHASE 2 — HOW PAVEMENTS FAIL
# ============================================================================
def render_deterioration():
    st.subheader("The fourth-power law — move the axle load")
    c = st.columns(2)
    axle = c[0].slider("Axle load (kN)", 20, 130, 100, 5)
    legal = c[1].slider("Legal axle limit (kN)", 60, 120, 80, 5)

    d = float(esal_factor(axle))
    d_legal = float(esal_factor(legal))
    k = st.columns(3)
    k[0].metric("Damage, this axle", f"{d:.2f} ESAL")
    k[1].metric("Damage, a legal axle", f"{d_legal:.2f} ESAL")
    k[2].metric("Overload penalty", f"{d/max(d_legal,1e-9):.2f}×")

    kn = np.linspace(20, 130, 200)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=kn, y=esal_factor(kn), mode="lines", name="damage per axle",
                             line=dict(color=CIVIL, width=3)))
    fig.add_trace(go.Scatter(x=[legal], y=[d_legal], mode="markers+text", text=["legal axle"],
                             textposition="top left", marker=dict(color=AISIDE, size=13),
                             showlegend=False))
    fig.add_trace(go.Scatter(x=[axle], y=[d], mode="markers+text", text=[f"{d:.2f} ESAL"],
                             textposition="top left", marker=dict(color=RED, size=15),
                             showlegend=False))
    fig.update_layout(title="damage is the fourth power of axle load")
    fig.update_xaxes(title="axle load (kN)")
    fig.update_yaxes(title="equivalent standard axle loads (ESAL)")
    st.plotly_chart(style(fig, 420), use_container_width=True, key="det_curve")

    if axle > legal:
        st.error(f"**{axle} kN is {axle/legal-1:.0%} over the limit — and does "
                 f"{d/d_legal:.1f}× the damage.** Enforcement is a pavement preservation measure, not "
                 f"just a traffic one.")
    else:
        st.success(f"At or under the limit. Push the slider past {legal} kN and watch the penalty run "
                   f"away from the overload.")

    st.divider()
    st.markdown("##### The second cause: climate")
    c = st.columns(2)
    temp = c[0].slider("Mean annual temperature (°C)", 18, 40, 31, 1, key="det_t")
    rain = c[1].slider("Annual rainfall (mm)", 300, 3000, 1100, 50, key="det_r")
    env = float(env_multiplier(temp, rain))
    life = float(climate_life(temp, rain))
    k = st.columns(3)
    k[0].metric("Damage rate multiplier", f"{env:.2f}×")
    k[1].metric("Life from ageing alone", f"{life:.1f} years")
    k[2].metric("vs a 24 °C, 900 mm baseline", f"{env/float(env_multiplier(24,900)):+.0%}")
    st.caption("Heat oxidises the binder. Water weakens the unbound layers. A pavement therefore has "
               "**two clocks** — one driven by load, one by climate — and it fails on whichever runs out "
               "first.")


def render_service_life():
    st.subheader("Build a pavement, and see what it can carry")
    c = st.columns(4)
    ac = c[0].slider("Bituminous layers (mm)", 60, 320, 240, 10)
    base = c[1].slider("Granular base (mm)", 150, 350, 250, 10)
    subbase = c[2].slider("Sub-base (mm)", 100, 350, 200, 10)
    mr = c[3].slider("Subgrade modulus MR (psi)", 3000, 14000, 6000, 500)

    sn = float(structural_number(ac, base, subbase))
    cap = float(allowable_esals(sn, mr))

    k = st.columns(3)
    k[0].metric("Structural number SN", f"{sn:.2f}")
    k[1].metric("Allowable load", f"{cap/1e6:,.1f} M ESAL")
    k[2].metric("vs a 150 mm section", f"{cap/float(allowable_esals(structural_number(150,base,subbase),mr)):,.1f}×")

    st.plotly_chart(cross_section_fig(ac, base, subbase,
                                      f"Your section — SN {sn:.2f}, {cap/1e6:,.1f} M ESAL capacity"),
                    use_container_width=True, key="sl_xsec")
    st.caption("Thickness is not a linear purchase. Add 60 mm of asphalt and the capacity does not rise "
               "33% — it multiplies. That is the second non-linearity in this problem.")

    st.divider()
    st.markdown("##### Where the pavement is on its curve")
    c = st.columns(2)
    life = c[0].slider("Total service life for this segment (years)", 5, 30, 17, 1)
    age = c[1].slider("Age today (years)", 0, 25, 12, 1)

    years = np.linspace(0, max(life * 1.4, age + 2), 200)
    psi = PSI0 - (PSI0 - PSI_TERM) * np.clip(years / life, 0, 1.45) ** 2.4
    rsl = max(life - age, 0.0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=psi, mode="lines", line=dict(color=CIVIL, width=3),
                             name="serviceability"))
    fig.add_hline(y=PSI_TERM, line_dash="dash", line_color=MUTED,
                  annotation_text="terminal serviceability 2.5")
    today = PSI0 - (PSI0 - PSI_TERM) * np.clip(age / life, 0, 1.45) ** 2.4
    fig.add_trace(go.Scatter(x=[age], y=[today], mode="markers+text", text=["today"],
                             textposition="top right", marker=dict(color=AISIDE, size=15),
                             showlegend=False))
    if rsl > 0:
        fig.add_shape(type="rect", x0=age, x1=life, y0=PSI_TERM, y1=today,
                      fillcolor="rgba(79,195,247,.12)", line=dict(width=0), layer="below")
        fig.add_annotation(x=(age + life) / 2, y=(PSI_TERM + today) / 2,
                           text=f"<b>{rsl:.1f} years left</b>", showarrow=False,
                           font=dict(size=15, color=AISIDE))
    fig.update_layout(title="remaining service life is the distance to the dashed line")
    fig.update_xaxes(title="years since construction")
    fig.update_yaxes(title="present serviceability index", range=[1.8, 4.4])
    style(fig, 430)
    animate(fig, _line_grow(years, psi, CIVIL), ms=45)
    st.plotly_chart(fig, use_container_width=True, key="sl_psi")

    if today > 3.4:
        st.success(f"Serviceability {today:.2f} — the curve is still flat. A thin surface seal restores "
                   f"it, and that is the cheap window.")
    elif today > PSI_TERM:
        st.warning(f"Serviceability {today:.2f} — the curve has turned. Preventive treatment is closing; "
                   f"structural work is coming.")
    else:
        st.error(f"Serviceability {today:.2f} — past terminal. This is rehabilitation or reconstruction, "
                 f"not maintenance.")
    st.caption("Note the shape: most of the loss happens in the last third of the life. That is why "
               "preventive maintenance exists, and why arriving late is so expensive.")


# ============================================================================
# PHASE 3 — THE CONDITION SURVEY
# ============================================================================
def render_inspection():
    st.subheader("Four sources, six model inputs")
    src = [("🚐 Survey vehicle", ["Crack density (%)", "Roughness IRI"], CIVIL),
           ("🔢 Traffic counter", ["Traffic volume (veh/day)"], AMBER),
           ("🧱 Core log / as-built", ["Thickness (mm)", "Age (years)"], "#a1887f"),
           ("🌦️ Met station", ["Rainfall (mm/yr)", "Temperature (°C)"], AISIDE)]
    cols = st.columns(4)
    for col, (name, items, colr) in zip(cols, src):
        with col:
            st.markdown(f"<div class='sign' style='border-left-color:{colr};height:100%'>"
                        f"<b>{name}</b><br><span class='muted'>"
                        + "<br>".join("› " + i for i in items) + "</span></div>",
                        unsafe_allow_html=True)
    st.write("")
    st.info("**Six of these are the model inputs.** Roughness and deflection are recorded but "
            "deliberately held back — we return to them once feature importance can say whether they "
            "are worth the survey cost.")

    st.divider()
    st.markdown("##### What each source actually knows about remaining life")
    clean, _ = get_survey()
    cols_all = FEATURES + ["surface_roughness_iri", "deflection_mm"]
    corr = clean[cols_all + [TARGET]].corr()[TARGET].drop(TARGET)
    labels = NICE + ["Roughness IRI", "Deflection (mm)"]
    order = np.argsort(corr.values)
    fig = go.Figure(go.Bar(x=corr.values[order], y=[labels[i] for i in order], orientation="h",
                           marker_color=[RED if v < 0 else GREEN for v in corr.values[order]]))
    fig.update_layout(title="correlation with remaining service life", showlegend=False)
    fig.update_xaxes(title="correlation coefficient")
    st.plotly_chart(style(fig, 400), use_container_width=True, key="insp_corr")
    st.caption("Every one of these is a measurement a highway agency already collects. Correlation is "
               "only a first look — it says nothing about interactions, which is where the real "
               "structure of this problem lives.")


def render_one_record():
    st.subheader("One kilometre becomes one row")
    c = st.columns(3)
    seg = c[0].text_input("Segment", "SH-021/07")
    cls = c[1].selectbox("Road class", list(CLASSES), index=1)
    c[2].caption("Change the values below and watch the row rebuild.")

    cc = st.columns(3)
    row = dict(SEGMENT)
    row["traffic_volume_vpd"] = cc[0].slider("Traffic (veh/day)", 500, 45000, 22000, 500, key="or_t")
    row["pavement_thickness_mm"] = cc[1].slider("Thickness (mm)", 60, 320, 240, 5, key="or_h")
    row["pavement_age_years"] = cc[2].slider("Age (years)", 0, 25, 12, 1, key="or_a")
    cc = st.columns(3)
    row["rainfall_mm_year"] = cc[0].slider("Rainfall (mm/yr)", 300, 3000, 1100, 50, key="or_r")
    row["avg_temperature_c"] = cc[1].slider("Temperature (°C)", 18.0, 40.0, 31.0, 0.5, key="or_c")
    row["crack_density_pct"] = cc[2].slider("Cracking (%)", 0.0, 65.0, 18.0, 1.0, key="or_k")

    # every cell a string — a mixed-type object column cannot be serialised for display
    frame = pd.DataFrame({"value": [seg, cls] + [f"{row[f]:,.1f}" for f in FEATURES]},
                         index=["segment_id", "road_class"] + FEATURES)
    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.markdown("**The record, as the model sees it**")
        st.dataframe(frame, use_container_width=True)
    with c2:
        st.markdown("**What each part is**")
        st.markdown(f"""
- The two rows at the top are **identifiers**. The model never sees them.
- The six below are the **features, X** — what was known on survey day.
- The **label, y** is not here. It comes from the works file: the year this segment
  actually reached terminal condition, recorded years later.
""")
        st.markdown(f"<div class='sign ai'>If the label ever came from the same formula as the "
                    f"features, the model would only be learning your own assumption back. It does "
                    f"not here.</div>", unsafe_allow_html=True)


# ============================================================================
# PHASE 4 — THE SURVEY EXPORT
# ============================================================================
def render_collect():
    clean, raw = get_survey()
    st.subheader("The network condition survey")
    k = st.columns(4)
    k[0].metric("Segments", f"{len(raw):,}")
    k[1].metric("Roads", f"{raw['road_id'].nunique():,}")
    k[2].metric("Columns", f"{raw.shape[1]}")
    k[3].metric("Climate zones", f"{raw['climate_zone'].nunique()}")

    st.dataframe(raw.head(12), use_container_width=True)
    st.caption("This is the file as it arrives — assembled from four systems by four teams. Some of it "
               "is typed by hand; some is exported by instruments that report their own error codes as "
               "ordinary numbers.")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        counts = raw["road_class"].value_counts()
        fig = go.Figure(go.Bar(x=counts.index, y=counts.values,
                               marker_color=[RED, AMBER, AISIDE][:len(counts)]))
        fig.update_layout(title="segments by road class", showlegend=False)
        st.plotly_chart(style(fig, 340), use_container_width=True, key="col_cls")
    with c2:
        counts = raw["climate_zone"].value_counts()
        fig = go.Figure(go.Bar(x=counts.index, y=counts.values, marker_color=AISIDE))
        fig.update_layout(title="segments by climate zone", showlegend=False)
        st.plotly_chart(style(fig, 340), use_container_width=True, key="col_zone")

    st.info("**Load it first, look at it second, believe it third.** The next page is the looking.")


def render_inspect_data():
    clean, raw = get_survey()
    st.subheader("The survey health check")

    LIMITS = {"traffic_volume_vpd": (100, 60000, "vehicles/day"),
              "pavement_thickness_mm": (40, 400, "mm"),
              "pavement_age_years": (0, 40, "years"),
              "rainfall_mm_year": (100, 4000, "mm/year"),
              "avg_temperature_c": (5, 45, "°C"),
              "crack_density_pct": (0, 80, "% area")}
    rows = []
    for col, (lo, hi, unit) in LIMITS.items():
        rows.append(dict(column=col, plausible_range=f"{lo} – {hi} {unit}",
                         outside=int(((raw[col] < lo) | (raw[col] > hi)).sum()),
                         missing=int(raw[col].isna().sum())))
    faults = pd.DataFrame(rows).set_index("column")
    faults["verdict"] = np.where((faults["outside"] + faults["missing"]) > 0, "⚠️ CHECK", "✅ ok")
    st.dataframe(faults, use_container_width=True)
    st.caption(f"Duplicated segment IDs: **{int(raw['segment_id'].duplicated().sum())}** — the same "
               f"kilometre cannot appear twice in one survey.")

    st.divider()
    st.markdown("##### One of these districts is not like the others")
    byd = raw.groupby("district")["avg_temperature_c"].median().sort_values()
    fig = go.Figure(go.Bar(x=byd.index, y=byd.values,
                           marker_color=[RED if v > 55 else AISIDE for v in byd.values],
                           text=[f"{v:.1f}" for v in byd.values], textposition="outside"))
    fig.add_hline(y=45, line_dash="dash", line_color=MUTED,
                  annotation_text="physically plausible ceiling for a mean annual temperature")
    fig.update_layout(title="median reported temperature by district", showlegend=False)
    fig.update_yaxes(title="reported °C")
    st.plotly_chart(style(fig, 400), use_container_width=True, key="idata_dist")

    st.error("**This is the dangerous fault.** Every Kadapa value is individually plausible as a number. "
             "Only the comparison across districts exposes it as **degrees Fahrenheit**. A model trained "
             "on it would conclude that hot districts have long-lived pavements.")
    st.markdown("""
| Fault | Evidence | What it actually is |
|---|---|---|
| `crack_density_pct = -1` | below a physical floor of 0 | the survey vehicle's error code |
| `pavement_thickness_mm = 0` | a road cannot be 0 mm thick | the core record was never entered |
| `rainfall_mm_year` blank | genuinely absent | a gap in the met station series |
| Kadapa temperatures in the 70s–80s | median 50°+ above every other district | **degrees Fahrenheit** |
""")


def render_clean():
    clean, raw = get_survey()
    st.subheader("Four faults, four different treatments")

    st.markdown("**Choose what to do with each fault, then read the row count.**")
    c = st.columns(4)
    a = c[0].radio("Fahrenheit district", ["Convert", "Delete the rows"], key="cl_f")
    b = c[1].radio("Missing rainfall", ["Impute from district", "Delete the rows"], key="cl_r")
    d = c[2].radio("Missing thickness", ["Delete the rows", "Impute from network"], key="cl_h")
    e = c[3].radio("Duplicate segments", ["Deduplicate", "Keep them"], key="cl_d")

    n0 = len(raw)
    lost = 0
    notes = []
    if a == "Convert":
        notes.append(("✅", f"{int((raw['district']=='Kadapa').sum())} records converted °F → °C — "
                            "one line of code, a whole climate zone kept"))
    else:
        lost += int((raw["district"] == "Kadapa").sum())
        notes.append(("❌", "a whole district — and a whole climate zone — deleted over a unit error"))
    if b == "Impute from district":
        notes.append(("✅", "26 rainfall values filled from the district median — a value you could "
                            "have looked up"))
    else:
        lost += 26
        notes.append(("⚠️", "26 usable segments deleted for a variable that was never in doubt"))
    if d == "Delete the rows":
        lost += 14
        notes.append(("✅", "14 records without a core dropped — thickness is whatever that contractor "
                            "laid, and no median knows it"))
    else:
        notes.append(("❌", "14 structures invented from a network median — they may not exist"))
    if e == "Deduplicate":
        lost += 12
        notes.append(("✅", "12 repeated segment records removed"))
    else:
        notes.append(("❌", "12 kilometres counted twice — they will land on both sides of the split"))

    k = st.columns(3)
    k[0].metric("Records in", f"{n0:,}")
    k[1].metric("Records out", f"{n0-lost:,}")
    k[2].metric("Removed", f"{lost/n0:.1%}")

    for icon, note in notes:
        st.markdown(f"{icon} &nbsp; {note}")

    st.divider()
    st.success("**The rule.** Impute a value you could have looked up. Drop a value only a measurement "
               "could have supplied. Cleaning is not deletion — four faults need four different "
               "answers, and the choice between them is engineering, not statistics.")


# ============================================================================
# PHASE 5 — PREPARING THE DATA
# ============================================================================
def render_features():
    clean, _ = get_survey()
    st.subheader("Six units, one scale")

    X = clean[FEATURES].to_numpy(float)
    desc = pd.DataFrame({"feature": NICE, "mean": X.mean(0), "std dev": X.std(0),
                         "min": X.min(0), "max": X.max(0)}).set_index("feature").round(1)
    st.dataframe(desc, use_container_width=True)
    ratio = X[:, 0].std() / X[:, 5].std()
    st.caption(f"Traffic volume varies about **{ratio:,.0f}×** as widely as crack density in raw units. "
               f"Nothing about pavement engineering says it is that many times more important.")

    scaled = StandardScaler().fit_transform(X)
    show = st.radio("Show", ["Raw units", "Standardised"], horizontal=True, key="feat_scale")
    data = X if show == "Raw units" else scaled
    fig = go.Figure()
    for i, name in enumerate(NICE):
        fig.add_trace(go.Box(y=data[:, i], name=name, marker_color=CIVIL, boxpoints=False))
    fig.update_layout(title=f"the six inputs — {show.lower()}", showlegend=False)
    if show == "Standardised":
        fig.update_yaxes(title="standard deviations from the mean")
    st.plotly_chart(style(fig, 420), use_container_width=True, key="feat_box")

    if show == "Raw units":
        st.warning("Traffic dwarfs everything. To a coefficient-based model that is a claim about "
                   "importance — one nobody made.")
    else:
        st.success("Now every feature is in the same currency: standard deviations from its own mean. "
                   "Coefficients can finally be read against each other.")

    st.divider()
    st.markdown("##### What we are predicting")
    fig = go.Figure(go.Histogram(x=clean[TARGET], marker_color=AISIDE, nbinsx=50))
    fig.update_layout(title="remaining service life across the network", showlegend=False)
    fig.update_xaxes(title="years")
    fig.update_yaxes(title="segments")
    st.plotly_chart(style(fig, 340), use_container_width=True, key="feat_y")
    st.caption(f"Median {clean[TARGET].median():.1f} years · "
               f"{(clean[TARGET] <= 0.05).mean():.0%} already at terminal condition · "
               f"a continuous target, so this is **regression**.")


def render_split():
    clean, _ = get_survey()
    st.subheader("Split by road, never by row")

    X = clean[FEATURES].to_numpy(float)
    y = clean[TARGET].to_numpy(float)
    groups = clean["road_id"].to_numpy()

    @st.cache_data(show_spinner="Comparing the two splits…")
    def compare():
        tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.30, random_state=42)
                      .split(X, y, groups))
        rtr, rte = train_test_split(np.arange(len(y)), test_size=0.30, random_state=42)
        out = {}
        for name, (a, b) in [("Random rows (leaks)", (rtr, rte)), ("Grouped by road", (tr, te))]:
            m = RandomForestRegressor(n_estimators=220, min_samples_leaf=2,
                                      random_state=42, n_jobs=-1).fit(X[a], y[a])
            p = m.predict(X[b])
            out[name] = (r2_score(y[b], p), mean_absolute_error(y[b], p))
        return out, tr, te

    out, tr, te = compare()
    k = st.columns(4)
    k[0].metric("Training segments", f"{len(tr):,}")
    k[1].metric("Testing segments", f"{len(te):,}")
    k[2].metric("Roads in both sets",
                f"{len(set(clean.iloc[tr]['road_id']) & set(clean.iloc[te]['road_id']))}")
    k[3].metric("Test roads", f"{clean.iloc[te]['road_id'].nunique()}")

    names = list(out)
    fig = make_subplots(rows=1, cols=2, subplot_titles=["R² reported", "MAE reported (years)"])
    fig.add_trace(go.Bar(x=names, y=[out[n][0] for n in names], marker_color=[RED, GREEN],
                         text=[f"{out[n][0]:.3f}" for n in names], textposition="outside",
                         showlegend=False), row=1, col=1)
    fig.add_trace(go.Bar(x=names, y=[out[n][1] for n in names], marker_color=[RED, GREEN],
                         text=[f"{out[n][1]:.2f}" for n in names], textposition="outside",
                         showlegend=False), row=1, col=2)
    fig.update_layout(title="the same model, two ways of splitting the same data")
    st.plotly_chart(style(fig, 400), use_container_width=True, key="split_bars")

    st.error(f"The random split reports **R² {out[names[0]][0]:.3f}** where the honest split delivers "
             f"**{out[names[1]][0]:.3f}** — and claims "
             f"**{out[names[1]][1]-out[names[0]][1]:.2f} years less error** than it will actually "
             f"achieve on a road nobody has surveyed.")
    st.caption("Kilometre 6 and kilometre 7 of the same highway share a subgrade, a climate, a "
               "contractor, a construction year and a traffic stream. Split at random and a segment's "
               "near-twin lands on the other side of the wall.")


# ============================================================================
# PHASE 6 — LEARNING DETERIORATION
# ============================================================================
def render_baseline():
    M = get_models()
    clean = M["clean"]
    y_te = M["y"][M["te"]]
    age_te = M["X"][M["te"]][:, FEATURES.index("pavement_age_years")]
    crack_te = M["X"][M["te"]][:, FEATURES.index("crack_density_pct")]

    st.subheader("The rule the agency already runs")
    c = st.columns(2)
    design = c[0].slider("Assumed design life (years)", 10, 30, 20, 1)
    trigger = c[1].slider("Cracking trigger (%) — 0 turns it off", 0, 60, 0, 5)

    pred = np.clip(design - age_te, 0, 25)
    if trigger > 0:
        pred = np.where(crack_te > trigger, np.minimum(pred, 3.0), pred)

    mae = mean_absolute_error(y_te, pred)
    r2 = r2_score(y_te, pred)
    k = st.columns(3)
    k[0].metric("MAE", f"{mae:.2f} years")
    k[1].metric("R²", f"{r2:.3f}")
    k[2].metric("Wrong by >4 years", f"{np.mean(np.abs(pred-y_te)>4):.0%}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=y_te, y=pred, mode="markers",
                             marker=dict(color=AMBER, size=6, opacity=0.45), showlegend=False))
    fig.add_trace(go.Scatter(x=[0, 25], y=[0, 25], mode="lines",
                             line=dict(color=MUTED, dash="dash"), showlegend=False))
    fig.update_layout(title=f"the fixed {design}-year cycle, on roads it has never seen")
    fig.update_xaxes(title="actual remaining life (years)")
    fig.update_yaxes(title="the rule's answer (years)")
    st.plotly_chart(style(fig, 430), use_container_width=True, key="base_scatter")

    st.warning(f"The rule is wrong by **{mae:.1f} years** on average. Look at the vertical stripes: "
               f"every segment of the same age gets the same answer, whether it carries 40,000 vehicles "
               f"a day or 900. Traffic, thickness and climate are not in the rule at all.")
    st.caption("Move the sliders. No design life makes this rule good — because the error is not a "
               "calibration problem, it is a missing-information problem.")


def render_linear():
    M = get_models()
    st.subheader("Everything adds up — the straight-line model")
    lin = M["lin"]
    coef = lin.coef_
    order = np.argsort(coef)

    fig = go.Figure(go.Bar(x=coef[order], y=[NICE[i] for i in order], orientation="h",
                           marker_color=[RED if v < 0 else GREEN for v in coef[order]],
                           text=[f"{v:+.2f}" for v in coef[order]], textposition="outside"))
    fig.update_layout(title="years of remaining life per standard deviation of each input",
                      showlegend=False)
    fig.update_xaxes(title="years")
    st.plotly_chart(style(fig, 400), use_container_width=True, key="lin_coef")

    st.success("**Every sign is engineering-correct.** Age, traffic, cracking, rainfall and temperature "
               "all subtract life; thickness adds it. Nobody told the model that — it recovered all six "
               "from the survey.")
    st.caption("Temperature comes out smallest. That is not evidence heat is harmless: most of what "
               "temperature does has already been recorded in the crack density column, so little is "
               "left for its own coefficient to explain. **A coefficient is not an effect — it is what "
               "is left of an effect after every other column has taken its share.**")

    st.divider()
    st.markdown("##### Where the straight line goes wrong")
    y_te = M["y"][M["te"]]
    p = M["preds"]["Linear Regression"]
    resid = y_te - p
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=["predicted vs actual", "error against actual"])
    fig.add_trace(go.Scatter(x=y_te, y=p, mode="markers",
                             marker=dict(color=TECH, size=6, opacity=0.45), showlegend=False),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=[0, 25], y=[0, 25], mode="lines",
                             line=dict(color=MUTED, dash="dash"), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=y_te, y=resid, mode="markers",
                             marker=dict(color=RED, size=6, opacity=0.45), showlegend=False),
                  row=1, col=2)
    fig.add_hline(y=0, line_color=MUTED, row=1, col=2)
    fig.update_xaxes(title_text="actual (years)", row=1, col=1)
    fig.update_yaxes(title_text="predicted (years)", row=1, col=1)
    fig.update_xaxes(title_text="actual (years)", row=1, col=2)
    fig.update_yaxes(title_text="actual − predicted (years)", row=1, col=2)
    st.plotly_chart(style(fig, 420), use_container_width=True, key="lin_resid")

    st.error("**Three things a straight line is forced to claim.** One traffic coefficient for the whole "
             "network — the same years-per-vehicle on a district road as on a national highway. No "
             "interaction between thickness and traffic. And a straight-line response to cracking, when "
             "the serviceability curve is anything but straight.")


def render_forest():
    M = get_models()
    st.subheader("Letting the data split itself")
    depth = st.slider("Tree depth to display", 2, 4, 3, 1)

    tree = DecisionTreeRegressor(max_depth=depth, random_state=42).fit(
        M["X"][M["tr"]], M["y"][M["tr"]])
    st.code(export_text(tree, feature_names=FEATURES, decimals=1), language="text")
    st.caption("Read that as an engineer's rulebook, not as code. The first split is the single most "
               "informative question about a pavement's future. Every branch below it asks a "
               "**different** next question — and that is exactly what an interaction is.")

    st.divider()
    n_trees = st.slider("Trees in the forest", 1, 220, 220, 1)

    @st.cache_data(show_spinner=False)
    def forest_curve():
        out = []
        for n in [1, 2, 3, 5, 8, 12, 20, 35, 60, 100, 160, 220]:
            m = RandomForestRegressor(n_estimators=n, min_samples_leaf=2,
                                      random_state=42, n_jobs=-1).fit(M["X"][M["tr"]], M["y"][M["tr"]])
            out.append((n, mean_absolute_error(M["y"][M["te"]], m.predict(M["X"][M["te"]]))))
        return pd.DataFrame(out, columns=["trees", "mae"])

    curve = forest_curve()
    here = float(np.interp(n_trees, curve["trees"], curve["mae"]))
    k = st.columns(3)
    k[0].metric("Trees", f"{n_trees}")
    k[1].metric("MAE", f"{here:.2f} years")
    k[2].metric("vs one tree", f"{curve['mae'].iloc[0]-here:+.2f} years")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=curve["trees"], y=curve["mae"], mode="lines+markers",
                             line=dict(color=GREEN, width=3), name="held-out MAE"))
    fig.add_trace(go.Scatter(x=[n_trees], y=[here], mode="markers",
                             marker=dict(color=AISIDE, size=15), showlegend=False))
    fig.update_layout(title="averaging more trees — and where it stops paying")
    fig.update_xaxes(title="trees in the forest", type="log")
    fig.update_yaxes(title="MAE on held-out roads (years)")
    st.plotly_chart(style(fig, 400), use_container_width=True, key="for_curve")
    st.info("One tree over-fits its own sample. Averaging hundreds of them on random subsets cancels "
            "that out — and the curve flattens quickly, which is why nobody tunes this number hard.")


def render_boosting():
    M = get_models()
    st.subheader("Every predictor, on the same held-out roads")
    res = _score_table()

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=["mean absolute error (years) — lower is better",
                                        "R² — higher is better"])
    cols = [MUTED, TECH, GREEN, AISIDE]
    fig.add_trace(go.Bar(x=res.index, y=res["mae"], marker_color=cols,
                         text=res["mae"].round(2), textposition="outside", showlegend=False),
                  row=1, col=1)
    fig.add_trace(go.Bar(x=res.index, y=res["r2"], marker_color=cols,
                         text=res["r2"].round(3), textposition="outside", showlegend=False),
                  row=1, col=2)
    st.plotly_chart(style(fig, 430), use_container_width=True, key="boost_bars")

    rule, linm, best = (res.loc["Fixed 20-year cycle", "mae"],
                        res.loc["Linear Regression", "mae"], res["mae"].min())
    ml = res.loc[["Linear Regression", "Random Forest", "Gradient Boosting"], "mae"].sort_values()
    k = st.columns(3)
    k[0].metric("Rule → simplest model", f"{rule-linm:.2f} years")
    k[1].metric("Simplest → best model", f"{linm-best:.2f} years")
    k[2].metric("Best → second best", f"{ml.iloc[1]-ml.iloc[0]:.2f} years")

    st.dataframe(res.round(3), use_container_width=True)
    st.info(f"**Read the three step sizes.** Going from the agency's rule to the simplest model, and "
            f"from that to the best one, both remove real error. Going from the best model to the "
            f"second best removes almost none. Most of the value came from using traffic, structure and "
            f"climate **at all** — and from letting the model bend — not from which ensemble won.")
    st.warning("**Diminishing returns arrive quickly.** That is the normal shape of these projects, and "
               "it is worth telling a client before they ask for a neural network. The next honest "
               "improvement on this problem is better data, not a bigger model.")


# ============================================================================
# PHASE 7 — READING THE MODEL
# ============================================================================
def render_importance():
    M = get_models()
    st.subheader("Which measurements the model actually uses")

    @st.cache_data(show_spinner="Shuffling each column in turn…")
    def perm():
        mdl = {"Random Forest": M["rf"], "Gradient Boosting": M["gb"]}.get(M["best"], M["rf"])
        r = permutation_importance(mdl, M["X"][M["te"]], M["y"][M["te"]], n_repeats=10,
                                   random_state=42, scoring="neg_mean_absolute_error")
        return pd.DataFrame({"feature": NICE, "gain": r.importances_mean,
                             "sd": r.importances_std}).sort_values("gain")

    imp = perm()
    fig = go.Figure(go.Bar(x=imp["gain"], y=imp["feature"], orientation="h", marker_color=AISIDE,
                           error_x=dict(type="data", array=imp["sd"], color=MUTED),
                           text=[f"{v:.2f}" for v in imp["gain"]], textposition="outside"))
    fig.update_layout(title=f"permutation importance ({M['best']}) — "
                            f"extra error when a column is shuffled", showlegend=False)
    fig.update_xaxes(title="added mean absolute error (years)")
    st.plotly_chart(style(fig, 420), use_container_width=True, key="imp_bars")

    st.success("**Crack density and age lead, well clear of the rest.** Both are correct. Cracking is "
               "the observed summary of everything that has already happened — *including damage from "
               "causes no other column recorded*: the blocked drain, the weak subgrade, the bad "
               "construction batch. Age says how quickly it got there.")
    st.warning("**Permutation importance under-credits correlated features.** Shuffling thickness alone "
               "barely hurts, because traffic, age and cracking between them still imply roughly what "
               "the structure must be. Read this chart as *what is uniquely mine*, not *what I am "
               "worth*.")
    st.caption("Temperature comes out last. Its effect reaches the model through two other columns — "
               "cracking, which already contains the thermal cracking it caused, and rainfall, which "
               "largely identifies the climate zone. A feature at the bottom of this chart is not "
               "automatically one to delete.")


def render_explain():
    st.subheader("Why does THIS kilometre have the life it does?")
    c = st.columns(3)
    row = dict(SEGMENT)
    row["traffic_volume_vpd"] = c[0].slider("Traffic (veh/day)", 500, 45000, 22000, 500, key="ex_t")
    row["pavement_thickness_mm"] = c[1].slider("Thickness (mm)", 60, 320, 240, 5, key="ex_h")
    row["pavement_age_years"] = c[2].slider("Age (years)", 0, 25, 12, 1, key="ex_a")
    c = st.columns(3)
    row["rainfall_mm_year"] = c[0].slider("Rainfall (mm/yr)", 300, 3000, 1100, 50, key="ex_r")
    row["avg_temperature_c"] = c[1].slider("Temperature (°C)", 18.0, 40.0, 31.0, 0.5, key="ex_c")
    row["crack_density_pct"] = c[2].slider("Cracking (%)", 0.0, 65.0, 18.0, 1.0, key="ex_k")

    base = predict_life(row)
    st.metric("Predicted remaining service life", f"{base:.1f} years")

    STEPS_OAT = {"traffic_volume_vpd": (-12000, 12000, NICE[0]),
                 "pavement_thickness_mm": (-60, 60, NICE[1]),
                 "pavement_age_years": (-5, 5, NICE[2]),
                 "rainfall_mm_year": (-600, 600, NICE[3]),
                 "avg_temperature_c": (-5, 5, NICE[4]),
                 "crack_density_pct": (-10, 10, NICE[5])}
    rows = []
    for f, (dn, up, label) in STEPS_OAT.items():
        lo, hi = dict(row), dict(row)
        lo[f] = max(lo[f] + dn, 0)
        hi[f] += up
        rows.append(dict(feature=label, low=predict_life(lo) - base, high=predict_life(hi) - base,
                         change=f"{dn:+g} / {up:+g}"))
    sens = pd.DataFrame(rows)
    sens["span"] = sens["high"].abs() + sens["low"].abs()
    sens = sens.sort_values("span")

    fig = go.Figure()
    fig.add_trace(go.Bar(y=sens["feature"], x=sens["low"], orientation="h",
                         marker_color=GREEN, name="input decreased"))
    fig.add_trace(go.Bar(y=sens["feature"], x=sens["high"], orientation="h",
                         marker_color=RED, name="input increased"))
    fig.add_vline(x=0, line_color=MUTED)
    fig.update_layout(barmode="relative", title=f"what moves this segment's {base:.1f} years")
    fig.update_xaxes(title="change in predicted remaining life (years)")
    st.plotly_chart(style(fig, 430), use_container_width=True, key="ex_tornado")

    top = sens.iloc[-1]["feature"]
    st.info(f"**On this segment the binding constraint is {top.lower()}.** That is the sentence that "
            f"goes in the review file — and every clause in it is traceable to a bar in this chart.")
    st.caption("**Where a bar is flat, that is information too.** A tree ensemble is piecewise "
               "constant: it predicts in bands, so a small change can land in the same leaves and "
               "register nothing. The engineering reading is that on *this* segment, at *these* values, "
               "that factor is not what limits the life. For the general claim, quote the network-level "
               "importance instead — and say which one you are quoting.")
    st.warning("""
**Two bars here will surprise you, and they are not errors.** Thickness and age can point the 'wrong'
way, because this chart moves **one input while holding the other five fixed — including cracking.**

Read them conditionally and they are correct engineering:

- *A thicker section showing this much cracking* is in more trouble than a thin one showing the same. It
  should not have cracked at that thickness.
- *A younger pavement showing this much cracking* is deteriorating faster, so it has less life left than
  an older one at the same distress.

Cracking is a **consequence** of the other five, so holding it fixed changes the question being asked.
The prediction page shows the same comparison done properly — with cracking allowed to follow.""")


def render_instrumentation():
    M = get_models()
    st.subheader("Is a deflection survey worth buying?")

    @st.cache_data(show_spinner="Re-fitting with the extra instruments…")
    def gains():
        clean = M["clean"]
        y, tr, te = M["y"], M["tr"], M["te"]
        base_mae = mean_absolute_error(y[te], M["rf"].predict(M["X"][te]))
        out = {}
        for label, extra in [("+ roughness (IRI)", ["surface_roughness_iri"]),
                             ("+ deflection (FWD)", ["deflection_mm"]),
                             ("+ both", ["surface_roughness_iri", "deflection_mm"])]:
            Xs = clean[FEATURES + extra].to_numpy(float)
            m = RandomForestRegressor(n_estimators=220, min_samples_leaf=2,
                                      random_state=42, n_jobs=-1).fit(Xs[tr], y[tr])
            out[label] = mean_absolute_error(y[te], m.predict(Xs[te]))
        # the noise floor: hold back a DIFFERENT 30% of the roads, five times
        groups = clean["road_id"].to_numpy()
        spread = []
        for s in [42, 7, 13, 21, 99]:
            a, b = next(GroupShuffleSplit(n_splits=1, test_size=0.30, random_state=s)
                        .split(M["X"], y, groups))
            m = RandomForestRegressor(n_estimators=220, min_samples_leaf=2,
                                      random_state=42, n_jobs=-1).fit(M["X"][a], y[a])
            spread.append(mean_absolute_error(y[b], m.predict(M["X"][b])))
        return base_mae, out, float(np.std(spread)), spread

    base_mae, out, noise, spread = gains()
    cost = st.slider("Deflection survey cost (₹ per km)", 2000, 30000, 9000, 500)

    labels = ["the six survey measurements"] + list(out)
    maes = [base_mae] + [out[k] for k in out]
    gain = [0.0] + [base_mae - out[k] for k in out]

    fig = go.Figure(go.Bar(x=labels, y=gain,
                           marker_color=[MUTED] + [GREEN if g > 2 * noise else RED for g in gain[1:]],
                           text=[("baseline" if i == 0 else f"{g:+.3f}") for i, g in enumerate(gain)],
                           textposition="outside"))
    fig.add_hline(y=noise, line_dash="dash", line_color=AMBER,
                  annotation_text=f"noise floor ±{noise:.3f} yr — a different sample of roads")
    fig.add_hline(y=2 * noise, line_dash="dot", line_color=RED,
                  annotation_text="the bar a real gain has to clear")
    fig.update_layout(title="accuracy gained, in years — against the noise floor", showlegend=False)
    fig.update_yaxes(title="reduction in MAE (years)")
    st.plotly_chart(style(fig, 430), use_container_width=True, key="inst_bars")

    g_defl = base_mae - out["+ deflection (FWD)"]
    k = st.columns(3)
    k[0].metric("Deflection gain", f"{g_defl:+.3f} years")
    k[1].metric("Noise floor (1σ)", f"±{noise:.3f} years")
    k[2].metric("Cost per year of accuracy",
                f"₹{cost/max(g_defl,1e-6):,.0f}" if g_defl > 0 else "—")

    st.caption(f"Holding back a different 30% of the **roads** moves the six-column model's MAE between "
               f"{min(spread):.3f} and {max(spread):.3f} years all on its own. Any 'gain' smaller than "
               f"that is a different sample of roads, not a better model.")
    if g_defl > 2 * noise:
        st.success(f"**The gain clears the noise floor.** Price ₹{cost/g_defl:,.0f} per year of accuracy "
                   f"against the cost of a year of mistimed treatment before recommending the purchase.")
    else:
        st.error(f"**Verdict: do not buy it — on this network.** The gain sits inside the noise floor. "
                 f"A study that comes back 'no' has saved the price of the equipment, which is a result, "
                 f"not a failure.")
    st.warning("Read that as an answer about **this network**, not a law about deflectometers. Here the "
               "base, sub-base and subgrade are relatively uniform, so thickness is already a good proxy "
               "for capacity. On old, variable, poorly documented pavements the answer would differ — "
               "and the value of this step is that it tells you which network you are on.")


# ============================================================================
# PHASE 8 — THE PREDICTION
# ============================================================================
def render_predict():
    st.subheader("Six measurements in, remaining service life out")
    c = st.columns(3)
    row = dict(SEGMENT)
    row["traffic_volume_vpd"] = c[0].slider("Traffic volume (veh/day)", 500, 45000, 22000, 500,
                                            key="pr_t")
    row["pavement_thickness_mm"] = c[1].slider("Pavement thickness (mm)", 60, 320, 240, 5, key="pr_h")
    row["pavement_age_years"] = c[2].slider("Pavement age (years)", 0, 25, 12, 1, key="pr_a")
    c = st.columns(3)
    row["rainfall_mm_year"] = c[0].slider("Rainfall (mm/year)", 300, 3000, 1100, 50, key="pr_r")
    row["avg_temperature_c"] = c[1].slider("Temperature (°C)", 18.0, 40.0, 31.0, 0.5, key="pr_c")
    row["crack_density_pct"] = c[2].slider("Crack density (%)", 0.0, 65.0, 18.0, 1.0, key="pr_k")

    yrs = predict_life(row)
    action, rank, reasons = recommend(yrs, row["crack_density_pct"],
                                      row["pavement_thickness_mm"], row["traffic_volume_vpd"])

    c1, c2 = st.columns([1, 1])
    with c1:
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=yrs,
            number=dict(suffix=" yrs", font=dict(size=46, color=TEXT)),
            title=dict(text="Predicted remaining service life", font=dict(size=15, color=MUTED)),
            gauge=dict(
                axis=dict(range=[0, 25], tickcolor=MUTED),
                bar=dict(color=ACT_COLORS[rank], thickness=0.7),
                bgcolor=INK, borderwidth=1, bordercolor=EDGE,
                steps=[dict(range=[0, 2], color="rgba(239,83,80,.22)"),
                       dict(range=[2, 5], color="rgba(255,183,77,.20)"),
                       dict(range=[5, 10], color="rgba(79,195,247,.16)"),
                       dict(range=[10, 25], color="rgba(102,187,106,.14)")])))
        st.plotly_chart(style(fig, 330), use_container_width=True, key="pr_gauge")
    with c2:
        st.markdown(f"<div class='sign' style='border-left-color:{ACT_COLORS[rank]};margin-top:28px'>"
                    f"<span class='muted'>RECOMMENDED TREATMENT</span><br>"
                    f"<b style='font-size:22px;color:{ACT_COLORS[rank]}'>{action}</b><br><br>"
                    f"<span class='muted'>ENGINEERING REASONS</span><br>{reasons}</div>",
                    unsafe_allow_html=True)
        st.caption("The band comes from the predicted life. The extra reasons are engineering "
                   "overrides — they can only escalate the recommendation, never soften it.")

    st.divider()
    st.markdown("##### Why the prediction moves — 1. as cracking rises")
    cracks = np.linspace(0, 60, 50)
    ys = [predict_life({**row, "crack_density_pct": ck}) for ck in cracks]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cracks, y=ys, mode="lines", line=dict(color=AMBER, width=3),
                             name="your segment"))
    fig.add_vline(x=row["crack_density_pct"], line_dash="dash", line_color=MUTED,
                  annotation_text="surveyed cracking")
    fig.update_layout(title="remaining life against measured cracking")
    fig.update_xaxes(title="crack density (%)")
    fig.update_yaxes(title="predicted remaining life (years)")
    st.plotly_chart(style(fig, 380), use_container_width=True, key="pr_curves")

    e5, e15, e35, e45 = (predict_life({**row, "crack_density_pct": v}) for v in (5, 15, 35, 45))
    k = st.columns(3)
    k[0].metric("Cracking 5% → 15% costs", f"{e5-e15:.2f} years")
    k[1].metric("Cracking 35% → 45% costs", f"{e35-e45:.2f} years")
    k[2].metric("Same ten points, different price", f"{abs((e5-e15)-(e35-e45)):.2f} yr apart")
    st.caption("**The response is a curve, not a line** — which is exactly what a straight-line model "
               "could never represent. The steps are real too: a tree ensemble predicts in bands, so "
               "small changes sometimes register nothing at all.")

    st.divider()
    st.markdown("##### Why the prediction moves — 2. as the structure changes")
    st.markdown(
        "Now try the obvious experiment: **make the pavement thicker and watch the life go up.** "
        "There is a trap in it, and it is worth more than the answer.")
    mode = st.radio(
        "When you change the thickness, what happens to the surveyed cracking?",
        ["Let cracking follow the physics (what really happens)",
         "Hold cracking fixed at the surveyed value"],
        key="pr_mode")
    trucks = st.slider("Commercial vehicles (% of traffic)", 3, 25, 12, 1, key="pr_tr")

    ages = np.linspace(0, 25, 60)
    fig = go.Figure()
    for thick, colr in [(150, RED), (240, AMBER), (300, GREEN)]:
        ys = []
        for a in ages:
            if mode.startswith("Let"):
                ck = physical_crack(row["traffic_volume_vpd"], thick, a,
                                    row["rainfall_mm_year"], row["avg_temperature_c"],
                                    truck_pct=trucks)
            else:
                ck = row["crack_density_pct"]
            ys.append(predict_life({**row, "pavement_thickness_mm": thick,
                                    "pavement_age_years": a, "crack_density_pct": ck}))
        fig.add_trace(go.Scatter(x=ages, y=ys, mode="lines", name=f"{thick} mm section",
                                 line=dict(color=colr, width=3)))
    fig.add_vline(x=row["pavement_age_years"], line_dash="dash", line_color=MUTED,
                  annotation_text="your segment's age")
    fig.update_layout(title="predicted remaining life against age, for three structures")
    fig.update_xaxes(title="pavement age (years)")
    fig.update_yaxes(title="predicted remaining life (years)")
    st.plotly_chart(style(fig, 420), use_container_width=True, key="pr_thick")

    if mode.startswith("Let"):
        st.success("**This is the honest comparison, and it behaves as an engineer expects.** A thicker "
                   "section carries more load before it cracks, so at any given age it shows less "
                   "distress and has more life left. Push the commercial-vehicle slider up and watch "
                   "the thin section collapse first — that is the fourth-power law arriving.")
    else:
        st.error("**Look what happened: the thick section is no better, and may be worse.** The model "
                 "is not broken. You asked it an incoherent question.")
    st.warning("""
**The trap — and it catches real projects.** Crack density is not an independent input. It is a
**consequence** of thickness, traffic, age and climate. Holding it fixed while you change the structure
asks the model: *given that this pavement has cracked this much anyway, does thickness help?* And the
answer is genuinely no — a 300 mm section already showing 18% cracking is in more trouble than a 150 mm
section showing the same, because it should not have cracked at all.

Statisticians call this **conditioning on a mediator**. The rule for using this system: when you change
something upstream, let everything downstream of it change too.""")


# ============================================================================
# PHASE 9 — THE PAVEMENT AUDIT
# ============================================================================
def render_audit():
    M = get_models()
    st.subheader("The pavement performance audit")
    name = st.radio("Predictor", ["Fixed 20-year cycle", "Linear Regression",
                                  "Random Forest", "Gradient Boosting"],
                    index=3, horizontal=True, key="au_m")
    y_te = M["y"][M["te"]]
    p = np.clip(M["preds"][name], 0, 25)
    err = p - y_te
    mae = mean_absolute_error(y_te, p)
    rmse = float(np.sqrt(np.mean(err ** 2)))

    k = st.columns(4)
    k[0].metric("MAE", f"{mae:.2f} years")
    k[1].metric("RMSE", f"{rmse:.2f} years")
    k[2].metric("R²", f"{r2_score(y_te, p):.3f}")
    k[3].metric("Within 2 years", f"{np.mean(np.abs(err)<=2):.0%}")

    bins, labels = [0, 2, 5, 10, 15, 26], ["0-2", "2-5", "5-10", "10-15", "15+"]
    band = pd.cut(y_te, bins=bins, labels=labels, right=False)
    tab = (pd.DataFrame({"band": band, "abs": np.abs(err), "err": err})
           .groupby("band", observed=False)
           .agg(segments=("err", "size"), mae=("abs", "mean"), bias=("err", "mean")).round(2))

    fig = make_subplots(rows=1, cols=3, subplot_titles=[
        "predicted vs actual", "error distribution", "bias across the range"])
    fig.add_trace(go.Scatter(x=y_te, y=p, mode="markers",
                             marker=dict(color=AISIDE, size=6, opacity=0.45), showlegend=False),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=[0, 25], y=[0, 25], mode="lines",
                             line=dict(color=MUTED, dash="dash"), showlegend=False), row=1, col=1)
    fig.add_trace(go.Histogram(x=err, nbinsx=45, marker_color=AMBER, showlegend=False), row=1, col=2)
    fig.add_trace(go.Bar(x=tab.index.astype(str), y=tab["bias"],
                         marker_color=[RED if v > 0 else GREEN for v in tab["bias"]],
                         showlegend=False), row=1, col=3)
    fig.update_xaxes(title_text="actual (years)", row=1, col=1)
    fig.update_yaxes(title_text="predicted (years)", row=1, col=1)
    fig.update_xaxes(title_text="predicted − actual (years)", row=1, col=2)
    fig.update_xaxes(title_text="actual remaining life (years)", row=1, col=3)
    fig.update_yaxes(title_text="mean error (years)", row=1, col=3)
    st.plotly_chart(style(fig, 420), use_container_width=True, key="au_three")

    tab.columns = ["segments", "MAE (years)", "bias (years)"]
    st.dataframe(tab, use_container_width=True)

    low = float(tab.loc[["0-2", "2-5"], "bias (years)"].max())
    if low > 0.5:
        st.error(f"**Worst optimism in the two lowest bands: {low:+.2f} years.** The model promises life "
                 f"the pavement does not have, on exactly the segments least able to wait.")
    else:
        st.success(f"**Worst optimism in the two lowest bands: {low:+.2f} years.** Acceptable — but this "
                   f"is the number to re-check every time the model is retrained.")
    st.caption("The bias panel is the one that matters operationally. A model can have an excellent "
               "overall score and still be systematically optimistic about the segments that are nearly "
               "finished — which are precisely the ones a maintenance programme exists to catch.")


def render_errors():
    M = get_models()
    st.subheader("The two errors do not cost the same")
    c = st.columns(3)
    c_prev = c[0].slider("Preventive treatment (₹ lakh/km)", 5, 60, int(COST_PREVENTIVE / 1e5), 1)
    c_reh = c[1].slider("Rehabilitation (₹ lakh/km)", 20, 150, int(COST_REHAB / 1e5), 5)
    c_rec = c[2].slider("Reconstruction (₹ lakh/km)", 80, 400, int(COST_RECON / 1e5), 10)
    cost_reh, cost_rec = c_reh * 1e5, c_rec * 1e5

    early_rate = cost_reh / SERVICE_LIFE
    late_rate = (cost_rec - cost_reh) / 5.0

    k = st.columns(3)
    k[0].metric("One year too early", f"₹{early_rate:,.0f}/km")
    k[1].metric("One year too late", f"₹{late_rate:,.0f}/km")
    k[2].metric("Ratio", f"{late_rate/max(early_rate,1):.1f} : 1")

    def cost_of(pred, actual):
        early = np.maximum(actual - pred, 0.0) * early_rate
        late = np.clip(np.maximum(pred - actual, 0.0) / 5.0, 0, 1) * (cost_rec - cost_reh)
        return early, late

    y_te = M["y"][M["te"]]
    rows = []
    for name in ["Fixed 20-year cycle", "Linear Regression", "Random Forest", "Gradient Boosting"]:
        e, l = cost_of(np.clip(M["preds"][name], 0, 25), y_te)
        rows.append(dict(model=name, too_early=e.mean(), too_late=l.mean(), total=(e + l).mean()))
    cf = pd.DataFrame(rows).set_index("model")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=cf.index, y=cf["too_early"] / 1e5, name="treated too early — asset wasted",
                         marker_color=AISIDE))
    fig.add_trace(go.Bar(x=cf.index, y=cf["too_late"] / 1e5, name="treated too late — escalation",
                         marker_color=RED))
    fig.update_layout(barmode="stack", title="mean cost of a timing error, per lane-kilometre")
    fig.update_yaxes(title="₹ lakh per km")
    st.plotly_chart(style(fig, 430), use_container_width=True, key="err_cost")

    saved = cf.loc["Fixed 20-year cycle", "total"] - cf["total"].min()
    st.success(f"The best model cuts the mean timing cost by **₹{saved:,.0f} per kilometre** against the "
               f"fixed cycle. Note the composition: almost all of it is the **red** part — arriving "
               f"late.")
    st.warning(f"**What the {late_rate/max(early_rate,1):.1f}:1 ratio tells the engineer.** Where the "
               f"model is uncertain, lean pessimistic — bring the treatment forward rather than back. "
               f"And never accept a model whose bias is positive in the low bands. The costs above are "
               f"the agency's schedule of rates, not measurements: substitute your own. The **ratio**, "
               f"not the absolute number, is what survives that substitution.")


# ============================================================================
# PHASE 10 — MAINTENANCE PLANNING
# ============================================================================
def render_decision():
    M = get_models()
    clean = M["clean"]
    st.subheader("From a predicted number to a work list")

    test = clean.iloc[M["te"]].copy()
    test["predicted_years"] = np.clip(M["preds"][M["best"]], 0, 25)
    recs = [recommend(r.predicted_years, r.crack_density_pct,
                      r.pavement_thickness_mm, r.traffic_volume_vpd) for r in test.itertuples()]
    test["action"] = [a for a, _, _ in recs]
    test["rank"] = [k for _, k, _ in recs]
    test["reasons"] = [w for _, _, w in recs]

    st.markdown("##### The banding, and the overrides")
    c1, c2 = st.columns([1.15, 1])
    with c1:
        fig = go.Figure()
        edges = [(10, 25, 0), (5, 10, 1), (2, 5, 2), (0, 2, 3)]
        for lo, hi, r in edges:
            fig.add_shape(type="rect", x0=lo, x1=hi, y0=0, y1=1, fillcolor=ACT_COLORS[r],
                          opacity=0.35, line=dict(width=0))
            fig.add_annotation(x=(lo + hi) / 2, y=0.5, text=ACTIONS[r].replace(" ", "<br>"),
                               showarrow=False, font=dict(size=11, color=TEXT))
        fig.update_xaxes(title="predicted remaining service life (years)", range=[0, 25])
        fig.update_yaxes(visible=False, range=[0, 1])
        fig.update_layout(title="the treatment bands")
        st.plotly_chart(style(fig, 260), use_container_width=True, key="dec_bands")
    with c2:
        st.markdown(f"""
<div class='sign warn'><b>Overrides — they may only escalate</b><br>
› cracking ≥ 60% → reconstruction, whatever the model says<br>
› cracking ≥ 45% → at least major rehabilitation<br>
› cracking ≥ 25% on a 'normal operation' segment → seal it<br>
› under 100 mm carrying over 15,000 vpd → escalate one level
</div>""", unsafe_allow_html=True)
        st.caption("Some knowledge belongs in a rule, not in a weight. If the model and standard "
                   "practice disagree, the conservative answer wins.")

    st.divider()
    st.markdown("##### The work list — one entry per road, its worst segment")
    st.caption("An agency programmes a road, not a stray kilometre: twelve consecutive kilometres of "
               "one bad road are one job.")
    work = (test.sort_values(["rank", "predicted_years"], ascending=[False, True])
            .drop_duplicates(subset="road_id", keep="first").head(14))
    st.dataframe(work[["segment_id", "road_class", "pavement_age_years", "crack_density_pct",
                       "predicted_years", "action", "reasons"]].set_index("segment_id"),
                 use_container_width=True)

    st.markdown("##### When each of these roads is due")
    tl = work.head(10).iloc[::-1]
    fig = go.Figure()
    for _, r in tl.iterrows():
        fig.add_trace(go.Bar(y=[r["segment_id"]], x=[max(r["predicted_years"], 0.15)],
                             orientation="h", marker_color=ACT_COLORS[int(r["rank"])],
                             showlegend=False, hovertext=r["action"], hoverinfo="text+x"))
    for x, lbl, colr in [(2, "reconstruct", RED), (5, "rehabilitate", AMBER),
                         (10, "preventive", AISIDE)]:
        fig.add_vline(x=x, line_dash="dash", line_color=colr, annotation_text=lbl)
    fig.update_layout(title="maintenance timeline — years from today", barmode="stack")
    fig.update_xaxes(title="years until the treatment is due", range=[0, 14])
    st.plotly_chart(style(fig, 430), use_container_width=True, key="dec_timeline")
    st.info("**This is the product.** Everything earlier existed to fill in these columns. And note "
            "what the system never does: close a lane, issue a work order, or commit a rupee. It orders "
            "the engineer's programme.")


def render_dashboard():
    M = get_models()
    clean = M["clean"]
    st.subheader("The maintenance planning dashboard")

    c = st.columns(3)
    budget = c[0].slider("Budget (₹ crore / year)", 20, 400, 120, 10)
    esc_years = c[1].slider("Years past terminal before rehab becomes reconstruction", 1, 6, 3, 1)
    seg_km = c[2].slider("Length of one survey segment (km)", 0.5, 2.0, 1.0, 0.1)

    net = clean.copy()
    Xn = net[FEATURES].to_numpy(float)
    mdl = {"Random Forest": M["rf"], "Gradient Boosting": M["gb"]}.get(M["best"], M["rf"])
    net["predicted_years"] = np.clip(mdl.predict(Xn), 0, 25)
    nrecs = [recommend(r.predicted_years, r.crack_density_pct,
                       r.pavement_thickness_mm, r.traffic_volume_vpd) for r in net.itertuples()]
    net["action"] = [a for a, _, _ in nrecs]

    RATE = dict(zip(ACTIONS, [0, COST_PREVENTIVE, COST_REHAB, COST_RECON]))
    plan = (net.groupby("action").agg(segments=("segment_id", "count"))
            .reindex(ACTIONS).fillna(0).astype(int))
    plan["km"] = plan["segments"] * seg_km
    plan["cost"] = [plan.loc[a, "km"] * RATE[a] for a in plan.index]
    need = plan["cost"].sum()

    k = st.columns(4)
    k[0].metric("Identified need", f"₹{need/1e7:,.0f} crore")
    k[1].metric("Budget", f"₹{budget} crore")
    k[2].metric("Funded share", f"{min(budget*1e7/max(need,1),1):.0%}")
    k[3].metric("Km needing work", f"{plan['km'][1:].sum():,.0f} km")

    fig = make_subplots(rows=1, cols=2, subplot_titles=[
        "network by treatment (km)", "programme cost (₹ crore)"])
    fig.add_trace(go.Bar(x=[a.split()[0] for a in ACTIONS], y=plan["km"], marker_color=ACT_COLORS,
                         text=plan["km"].round(0), textposition="outside", showlegend=False),
                  row=1, col=1)
    fig.add_trace(go.Bar(x=[a.split()[0] for a in ACTIONS], y=plan["cost"] / 1e7,
                         marker_color=ACT_COLORS, text=(plan["cost"] / 1e7).round(1),
                         textposition="outside", showlegend=False), row=1, col=2)
    st.plotly_chart(style(fig, 400), use_container_width=True, key="dash_plan")

    # ---- what the ranking is worth, computed from the held-out audit ----
    y_te = M["y"][M["te"]]
    p_model = np.clip(M["preds"][M["best"]], 0, 25)
    p_rule = M["preds"]["Fixed 20-year cycle"]
    late_rule = float(np.mean(np.maximum(p_rule - y_te, 0) > esc_years))
    late_model = float(np.mean(np.maximum(p_model - y_te, 0) > esc_years))
    early_rule = float(np.mean(np.maximum(y_te - p_rule, 0)))
    early_model = float(np.mean(np.maximum(y_te - p_model, 0)))

    km_year = BUDGET_KM_YEAR
    recon_avoided = (late_rule - late_model) * km_year
    v_recon = recon_avoided * (COST_RECON - COST_REHAB)
    v_early = (early_rule - early_model) * km_year * (COST_REHAB / SERVICE_LIFE)

    st.divider()
    st.markdown("##### What the ranking is worth — computed from the held-out audit")
    k = st.columns(4)
    k[0].metric("Arriving >%d yrs late, fixed cycle" % esc_years, f"{late_rule:.1%}")
    k[1].metric("Arriving >%d yrs late, with model" % esc_years, f"{late_model:.1%}")
    k[2].metric("Escalations avoided", f"{recon_avoided:.1f} km/yr")
    k[3].metric("Total value", f"₹{(v_recon+v_early)/1e7:,.1f} crore/yr")

    fig = go.Figure(go.Bar(x=["escalations avoided", "service life retained"],
                           y=[v_recon / 1e7, v_early / 1e7], marker_color=[RED, GREEN],
                           text=[f"₹{v_recon/1e7:.1f} cr", f"₹{v_early/1e7:.1f} cr"],
                           textposition="outside"))
    fig.update_layout(title="where the value comes from", showlegend=False)
    fig.update_yaxes(title="₹ crore per year")
    style(fig, 380)
    animate(fig, _bars_grow([dict(x=["escalations avoided", "service life retained"],
                                  y=[v_recon / 1e7, v_early / 1e7], color=GREEN,
                                  text=[f"₹{v_recon/1e7:.1f} cr", f"₹{v_early/1e7:.1f} cr"])]), ms=90)
    st.plotly_chart(fig, use_container_width=True, key="dash_value")

    st.warning(f"**Read the assumptions, not the total.** The escalation window of **{esc_years} years** "
               f"is the load-bearing assumption and it is a judgement, not a measurement — change it and "
               f"the case changes with it. The treatment rates are the agency's, not the model's. Not "
               f"counted: road user costs, which are usually larger and move the same way, and the "
               f"engineers' time spent reviewing recommendations, which is a real new cost.")
    st.info("**The programme is still budget-limited.** The model does not create kilometres and does "
            "not enlarge the budget. It changes which kilometres get the available money — and that is "
            "the entire claim.")


# ============================================================================
# THE COURSE, AS ONE MAINTENANCE PROGRAMME
# bridge.open_page() puts the civil context, challenge and AI connection ABOVE
# each renderer; bridge.close_page() puts the notebook connection BELOW.
# ============================================================================
STAGES = {
    "start":           ("⓪ The project — read this first",
                        lambda: bridge.render_start(style, animate)),
    "road-network":    ("① A highway network under load", render_road_network),
    "enter-ai":        ("② The engineer stays in charge", render_enter_ai),
    "deterioration":   ("③ Why pavements deteriorate", render_deterioration),
    "service-life":    ("④ What remaining service life means", render_service_life),
    "inspection":      ("⑤ One pavement inspection", render_inspection),
    "one-record":      ("⑥ One segment becomes one row", render_one_record),
    "collect":         ("⑦ The network condition survey", render_collect),
    "inspect-data":    ("⑧ Checking the survey first", render_inspect_data),
    "clean":           ("⑨ Correcting the record", render_clean),
    "features":        ("⑩ Putting measurements on one scale", render_features),
    "split":           ("⑪ Holding back roads, not rows", render_split),
    "baseline":        ("⑫ The rule the agency already runs", render_baseline),
    "linear":          ("⑬ A first model: everything adds up", render_linear),
    "forest":          ("⑭ Letting the data split itself", render_forest),
    "boosting":        ("⑮ Correcting the previous estimate", render_boosting),
    "importance":      ("⑯ Which factors drive pavement life", render_importance),
    "explain":         ("⑰ Explaining one segment", render_explain),
    "instrumentation": ("⑱ Is more equipment worth buying?", render_instrumentation),
    "predict":         ("⑲ Predicting a segment you just surveyed", render_predict),
    "audit":           ("⑳ The pavement performance audit", render_audit),
    "errors":          ("㉑ The two errors do not cost the same", render_errors),
    "decision":        ("㉒ From a number to a treatment", render_decision),
    "dashboard":       ("㉓ The maintenance planning dashboard", render_dashboard),
}

ALIASES = {"overview": "start", "network": "road-network", "problem": "road-network",
           "data": "collect", "inspect": "inspect-data", "scaling": "features",
           "rf": "forest", "xgboost": "boosting", "gauge": "predict",
           "evaluation": "audit", "cost": "errors", "recommendation": "decision",
           "business-case": "dashboard", "mindmap": "start"}

stage = st.query_params.get("stage", "start")
stage = ALIASES.get(stage, stage)
if stage not in STAGES:
    stage = "start"

with st.sidebar:
    st.markdown("### 🛣️ A Road Asset Problem")
    st.caption("You are deciding which kilometres to repair this year, and AI keeps turning out to be "
               "the thing that covers the watch one engineer cannot keep across 1,500 segments.")
    keys = list(STAGES)
    sel = st.selectbox("Where are we on the network?", keys, index=keys.index(stage),
                       format_func=lambda k: STAGES[k][0])
    if sel != stage:
        st.query_params["stage"] = sel
        st.rerun()

    if stage in bridge.BY_ID:
        step = bridge.BY_ID[stage]
        pos = bridge.ORDER.index(stage) + 1
        pname = bridge.PHASES[step["phase"]][0]
        st.progress(pos / len(bridge.ORDER),
                    text=f"step {pos}/{len(bridge.ORDER)} · phase "
                         f"{step['phase']+1}/{len(bridge.PHASES)} · {pname}")
        st.markdown(
            f"<div style='font-size:12px;line-height:1.6'>"
            f"<span style='color:{MUTED}'>HIGHWAY ENGINEERING STEP</span><br>"
            f"<b style='color:{CIVIL}'>{step['civil']}</b><br>"
            f"<span style='color:{MUTED}'>IS THE AI CONCEPT</span><br>"
            f"<b style='color:{AISIDE}'>{step['ai']}</b></div>", unsafe_allow_html=True)
    st.divider()
    if st.button("🗺️  The whole project map", use_container_width=True):
        st.query_params["stage"] = "start"
        st.rerun()
    st.caption("▶ Press **Play** on a chart to animate it.")
    st.caption("The Colab notebook is the other half of this course — it builds everything you see here.")

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
