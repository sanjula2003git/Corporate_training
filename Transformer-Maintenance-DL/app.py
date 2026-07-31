"""
AI for Transformer Maintenance Decision Support - illustration app
==================================================================
One project, 20 stage pages, taught as one asset-management project.
Each notebook step links here with ?stage=<id>.

THE ASSET MODEL IS THE NOTEBOOK'S, imported from story.py.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from sklearn.model_selection import GroupShuffleSplit
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import r2_score

import scaffold as S
import common
import story
import bridge

POS, NEG = S.POS, S.NEG
GREEN, AMBER, RED = S.GREEN, S.AMBER, S.RED
TECH, MUTED, TEXT, PANEL = S.TECH, S.MUTED, S.TEXT, S.PANEL
style, animate = S.style, S.animate

st.set_page_config(page_title="AI for Transformer Maintenance", page_icon="⚡", layout="wide")
bridge.inject_css()

SENSORS = ["age_years", "ambient_c", "load_pu", "top_oil_c", "hotspot_c", "ageing_rate",
           "voltage_dev_pct", "load_current_a", "h2_ppm", "ch4_ppm", "c2h6_ppm",
           "c2h4_ppm", "c2h2_ppm", "co_ppm", "moisture_ppm", "pd_pc", "oil_bdv_kv"]
NICE = ["Age (yr)", "Ambient (°C)", "Load (pu)", "Top oil (°C)", "Hot spot (°C)", "Ageing rate",
        "Voltage dev (%)", "Current (A)", "H₂", "CH₄", "C₂H₆", "C₂H₄", "C₂H₂", "CO",
        "Moisture", "PD (pC)", "BDV (kV)"]
HEALTH_CLASSES = story.HEALTH_CLASSES


# ----------------------------------------------------------------------------
# DATA  (the fleet log — same generator as the notebook)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="Generating the fleet condition history…")
def get_data(n_units=400, seed=42):
    rng = np.random.default_rng(seed)
    rows = []
    for u in range(n_units):
        age = float(np.clip(rng.gamma(4.0, 5.5), 1, 48))
        p_fault = np.clip(0.05 + age / 70.0, 0, 0.65)
        for _ in range(int(rng.integers(2, 5))):
            fault = ("normal" if rng.random() > p_fault
                     else str(rng.choice(story.FAULT_NAMES[1:], p=[.18, .22, .20, .16, .14, .10])))
            sev = 0.0 if fault == "normal" else float(rng.uniform(0.25, 1.0))
            amb = float(rng.normal(24, 9))
            load = float(np.clip(rng.normal(0.78, 0.20), 0.25, 1.35))
            th_top, th_hs = story.top_oil_c(amb, load), story.hotspot_c(amb, load)
            f_aa = float(story.ageing_factor(th_hs))

            base = 18.0 + 2.2 * age
            r = story.FAULT_GAS[fault]
            scale = base * (1.0 + 14.0 * sev)
            h2, ch4, c2h6, c2h4, c2h2 = [
                float(abs(rng.normal(scale * g / 4.0, scale * g / 12.0 + 1.5))) for g in r]
            co_ppm = float(abs(rng.normal(220 + 26 * age + 400 * sev * (fault in ("T1", "T2", "T3")),
                                          90)))
            moisture = float(np.clip(rng.normal(9 + 0.55 * age + 8 * sev, 4), 2, 55))
            bdv = float(np.clip(rng.normal(62 - 0.45 * age - 12 * sev, 5), 18, 78))
            pd_pc = float(np.clip(rng.lognormal(
                np.log(45 + 900 * sev * (fault in ("PD", "D1", "D2"))), 0.7), 5, 20000))
            gas_sev = float(np.clip(0.55 * sev + 0.45 * np.clip(
                (h2 + ch4 + c2h4 + 6 * c2h2) / 900.0, 0, 1), 0, 1))
            hi = float(story.health_index(gas_sev, moisture, pd_pc, bdv, age, f_aa))

            rows.append(dict(unit_id=f"TX{u:03d}", fault=fault, severity=round(sev, 3),
                             age_years=round(age, 1), ambient_c=round(amb, 1),
                             load_pu=round(load, 3), top_oil_c=round(th_top, 1),
                             hotspot_c=round(th_hs, 1), ageing_rate=round(f_aa, 3),
                             voltage_dev_pct=round(float(rng.normal(0, 2.2)), 2),
                             load_current_a=round(load * 175 * float(rng.normal(1, .03)), 1),
                             h2_ppm=round(h2, 1), ch4_ppm=round(ch4, 1), c2h6_ppm=round(c2h6, 1),
                             c2h4_ppm=round(c2h4, 1), c2h2_ppm=round(c2h2, 2),
                             co_ppm=round(co_ppm, 1), moisture_ppm=round(moisture, 1),
                             pd_pc=round(pd_pc, 1), oil_bdv_kv=round(bdv, 1),
                             health_index=round(hi, 1)))
    df = pd.DataFrame(rows)
    df["health_class"] = story.health_class(df.health_index.values)

    # the faults every real asset-management export carries
    dirty = df.copy()
    n = len(dirty)
    for c in ["h2_ppm", "ch4_ppm", "moisture_ppm", "pd_pc"]:
        dirty.loc[rng.choice(n, int(0.03 * n), replace=False), c] = np.nan
    dirty.loc[rng.choice(n, 30, replace=False), "c2h2_ppm"] = -1.0     # below detection limit
    dirty.loc[rng.choice(n, 18, replace=False), "oil_bdv_kv"] = 0.0    # test not performed
    dirty = pd.concat([dirty, dirty.sample(25, random_state=4)], ignore_index=True)

    clean = dirty.drop_duplicates().copy()
    # laboratory convention: a result below the detection limit becomes DL/2
    clean.loc[clean.c2h2_ppm < 0, "c2h2_ppm"] = story.DETECT_LIMIT / 2
    clean.loc[clean.oil_bdv_kv <= 5, "oil_bdv_kv"] = np.nan
    for c in SENSORS:
        clean[c] = clean[c].fillna(clean[c].median())
    clean = clean.reset_index(drop=True)

    X = clean[SENSORS].values
    y_cls = clean.health_class.values
    y_hi = clean.health_index.values
    gss = GroupShuffleSplit(n_splits=1, test_size=0.30, random_state=42)
    itr, ite = next(gss.split(X, groups=clean.unit_id))
    return dict(truth=df, dirty=dirty, clean=clean, X=X, y_cls=y_cls, y_hi=y_hi,
                itr=itr, ite=ite,
                Xtr=X[itr], Xte=X[ite], ytr=(y_cls[itr] >= 2).astype(int),
                yte=(y_cls[ite] >= 2).astype(int))


@st.cache_resource(show_spinner="Fitting the condition models…")
def get_models():
    d = get_data()
    cls = RandomForestClassifier(n_estimators=250, random_state=42).fit(
        d["X"][d["itr"]], d["y_cls"][d["itr"]])
    reg = RandomForestRegressor(n_estimators=250, random_state=42).fit(
        d["X"][d["itr"]], d["y_hi"][d["itr"]])
    return cls, reg


CFG = dict(
    data=lambda: dict(dirty=get_data()["dirty"], clean=get_data()["clean"]),
    FEATURES=["h2_ppm", "ch4_ppm", "c2h2_ppm", "moisture_ppm", "pd_pc", "oil_bdv_kv"],
    NICE=["H₂ (ppm)", "CH₄ (ppm)", "C₂H₂ (ppm)", "Moisture (ppm)", "PD (pC)", "BDV (kV)"],
    unit="assessment", unit_plural="assessments", pos="at risk", neg="sound",
    export_name="asset-management export",
    faults="An acetylene result below the detection limit written as −1, and a breakdown-voltage test "
           "never performed written as 0 kV, both announce themselves here.",
    fault_example="0 kV breakdown-voltage record",
    titles={"load": "⑤ The fleet log arrives", "inspect": "⑥ Checking the records"},
)


# ============================================================================
# RENDERERS
# ============================================================================
def render_clean():
    st.title("⑦ Removing the faulty readings")
    d = get_data()
    st.caption("Two different repairs, for two different kinds of bad value.")
    st.write("")
    c = st.columns(3)
    c[0].metric("Assessments", f"{len(d['clean']):,}")
    c[1].metric("Below-detection acetylene results", int((d["dirty"].c2h2_ppm < 0).sum()))
    c[2].metric("Missing after", int(d["clean"][SENSORS].isna().sum().sum()))
    st.write("")

    st.markdown("##### Why acetylene gets its own rule")
    st.markdown(f"""
- A result of **"< {story.DETECT_LIMIT} ppm"** is not zero and it is not missing. The gas was looked for
  and not found above the limit — which is a genuine, informative measurement.
- Recording it as **0** claims the gas is definitely absent. That is stronger than the laboratory said,
  and acetylene is the gas whose presence changes the whole classification.
- Recording it as **missing** and then filling with the column median is worse still: it would insert a
  typical acetylene level into a unit that demonstrably had almost none.
- The laboratory convention is **half the detection limit — {story.DETECT_LIMIT/2} ppm**. It is arbitrary,
  it is standard, and the important thing is that it is *written down*.
    """)
    st.write("")
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=d["clean"].c2h2_ppm.clip(0, 20), nbinsx=60, marker_color=POS))
    fig.add_vline(x=story.DETECT_LIMIT / 2, line=dict(color=GREEN, dash="dash"),
                  annotation_text=f"DL/2 = {story.DETECT_LIMIT/2}")
    fig.add_vline(x=story.THRESH["c2h2_ppm"], line=dict(color=RED, dash="dash"),
                  annotation_text=f"limit {story.THRESH['c2h2_ppm']} ppm")
    fig.update_layout(title="acetylene after the substitution — most units are near the floor")
    fig.update_xaxes(title="C₂H₂ (ppm)"); fig.update_yaxes(title="assessments")
    st.plotly_chart(style(fig, 380), use_container_width=True)
    st.warning("The two dashed lines are close together, and that is the point: **the difference between "
               "'not detected' and 'over the limit' is a few parts per million.** How the censored values "
               "are handled is therefore a decision with consequences, not a formality.")


def render_split():
    st.title("⑧ Known units vs sealed units")
    d = get_data()
    c_ = d["clean"]
    st.info("🧪 **Each transformer contributes several assessments.** Two assessments of the same unit six "
            "months apart are far more alike than two assessments of different units — so splitting by "
            "assessment lets the model recognise the *unit* rather than the condition.")
    st.write("")
    tr_u = set(c_.unit_id.values[d["itr"]])
    te_u = set(c_.unit_id.values[d["ite"]])
    c = st.columns(4)
    c[0].metric("Units in training", len(tr_u))
    c[1].metric("Units sealed", len(te_u))
    c[2].metric("Units in both", len(tr_u & te_u))
    c[3].metric("Assessments sealed", len(d["ite"]))
    st.write("")
    fig = go.Figure()
    for i, name in enumerate(HEALTH_CLASSES):
        fig.add_trace(go.Bar(x=["train", "test"],
                             y=[int((d["y_cls"][d["itr"]] == i).sum()),
                                int((d["y_cls"][d["ite"]] == i).sum())],
                             name=name,
                             marker_color=[GREEN, POS, AMBER, RED][i]))
    fig.update_layout(barmode="stack", title="condition bands in each half")
    fig.update_yaxes(title="assessments")
    st.plotly_chart(style(fig, 360), use_container_width=True)
    st.success("**Zero units appear in both halves.** The score now answers the real question: what would "
               "this say about a transformer it has never seen?")


def render_duval():
    st.title("⑨ The Duval Triangle")
    st.caption("How the industry reads dissolved gas: normalise three gases to percentages, plot the "
               "point, read the fault zone. IEC 60599.")
    st.write("")
    d = get_data()
    c_ = d["clean"]
    zones = story.duval_zone(c_.ch4_ppm.values, c_.c2h4_ppm.values, c_.c2h2_ppm.values)
    m, e, a = story.duval_coords(c_.ch4_ppm.values, c_.c2h4_ppm.values, c_.c2h2_ppm.values)

    fig = go.Figure(go.Scatterternary(
        a=m, b=e, c=a, mode="markers",
        marker=dict(size=5, opacity=0.55,
                    color=[{"PD": 0, "T1": 1, "T2": 2, "T3": 3, "D1": 4, "D2": 5, "DT": 6}[z]
                           for z in zones],
                    colorscale="Turbo", showscale=False),
        text=[f"{z}" for z in zones], hovertemplate="zone %{text}<extra></extra>"))
    fig.update_layout(title="the fleet, on Duval Triangle 1",
                      ternary=dict(sum=100,
                                   aaxis=dict(title="CH₄ %", color=TEXT),
                                   baxis=dict(title="C₂H₄ %", color=TEXT),
                                   caxis=dict(title="C₂H₂ %", color=TEXT),
                                   bgcolor=S.BG),
                      paper_bgcolor=S.BG, font_color=TEXT, height=470,
                      margin=dict(l=40, r=40, t=60, b=40))
    st.plotly_chart(fig, use_container_width=True)
    st.write("")

    vc = pd.Series(zones).value_counts()
    st.dataframe(pd.DataFrame({"Duval zone": vc.index, "Assessments": vc.values,
                               "Meaning": [{"PD": "partial discharge",
                                            "T1": "thermal fault < 300 °C",
                                            "T2": "thermal fault 300–700 °C",
                                            "T3": "thermal fault > 700 °C",
                                            "D1": "low-energy discharge",
                                            "D2": "high-energy arcing",
                                            "DT": "mixed thermal / electrical"}[z] for z in vc.index]}),
                 use_container_width=True, hide_index=True)
    st.write("")
    st.success("**This is a good method, and the model does not replace it.** It is published, it is "
               "understood, and an engineer can defend it in a report.")
    st.error("**Its two limits.** It uses **three of the seven gases** and ignores moisture, breakdown "
             "voltage, age and thermal history entirely. And it names a *fault type* without saying how "
             "**urgent** the unit is — a T1 on a new transformer and a T1 on a forty-year-old one get the "
             "same label and need completely different responses.")
    st.info("So the model extends Duval rather than competing with it: the same gases plus the other "
            "fourteen measurements, producing a **condition band** rather than a fault name.")


def render_health_model():
    st.title("⑩ Health from the measurements")
    d = get_data()
    cls, reg = get_models()
    ite = d["ite"]
    st.write("")
    c = st.columns(3)
    c[0].metric("Health index R²", f"{r2_score(d['y_hi'][ite], reg.predict(d['X'][ite])):.3f}")
    c[1].metric("Condition band accuracy",
                f"{float((cls.predict(d['X'][ite]) == d['y_cls'][ite]).mean()):.1%}")
    c[2].metric("Sealed assessments", len(ite))
    st.write("")

    st.markdown("##### Try an assessment")
    cc = st.columns(4)
    age = cc[0].slider("Age (years)", 1, 48, 26, 1)
    load = cc[1].slider("Load (pu)", 0.25, 1.35, 0.85, 0.05)
    amb = cc[2].slider("Ambient (°C)", -10, 45, 28, 1)
    c2h2 = cc[3].slider("Acetylene (ppm)", 0.0, 20.0, 0.3, 0.1)
    c2 = st.columns(3)
    h2 = c2[0].slider("Hydrogen (ppm)", 0.0, 600.0, 60.0, 5.0)
    moisture = c2[1].slider("Moisture (ppm)", 2.0, 55.0, 14.0, 1.0)
    bdv = c2[2].slider("Breakdown voltage (kV)", 18.0, 78.0, 58.0, 1.0)

    th_hs = float(story.hotspot_c(amb, load))
    f_aa = float(story.ageing_factor(th_hs))
    gas_sev = float(np.clip(0.45 * np.clip((h2 + 6 * c2h2) / 400.0, 0, 1) + 0.2, 0, 1))
    hi_true = float(story.health_index(gas_sev, moisture, 60.0, bdv, age, f_aa))

    row = np.array([[age, amb, load, float(story.top_oil_c(amb, load)), th_hs, f_aa,
                     0.5, load * 175, h2, 70.0, 30.0, 45.0, c2h2, 420.0, moisture, 60.0, bdv]])
    hi_pred = float(reg.predict(row)[0])
    band = int(cls.predict(row)[0])
    proba = cls.predict_proba(row)[0]
    st.write("")

    m = st.columns(4)
    m[0].metric("Hot spot", f"{th_hs:.0f} °C")
    m[1].metric("Ageing rate", f"{f_aa:.2f} ×")
    m[2].metric("Predicted health index", f"{hi_pred:.0f}", f"formula gives {hi_true:.0f}")
    m[3].metric("Confidence in the band", f"{proba.max():.0%}")
    st.write("")
    col = [GREEN, POS, AMBER, RED][band]
    st.markdown(f"<div style='padding:16px;border-radius:4px;text-align:center;font-size:20px;"
                f"font-weight:800;background:{col};color:#0e1117'>{HEALTH_CLASSES[band]}</div>",
                unsafe_allow_html=True)
    st.write("")

    fig = go.Figure(go.Bar(x=HEALTH_CLASSES, y=proba, marker_color=[GREEN, POS, AMBER, RED],
                           text=[f"{p:.0%}" for p in proba], textposition="outside"))
    fig.update_layout(title="how confident the classifier is")
    fig.update_yaxes(range=[0, 1.15], title="probability")
    st.plotly_chart(style(fig, 320), use_container_width=True)

    st.write("")
    if proba.max() < 0.6:
        st.warning("**This is a borderline call, and the screen says so.** The band boundaries are "
                   "conventions — a unit at 69 and one at 71 are not really different — so a split "
                   "probability is the model asking an engineer to look, not failing.")
    else:
        st.info("Raise the acetylene slider past 2 ppm and watch the band jump. That single gas carries "
                "more weight than any other because it cannot form without an arc.")


def render_drivers():
    st.title("⑪ What drives the assessment")
    cls, _ = get_models()
    imp = cls.feature_importances_
    order = np.argsort(imp)[::-1]
    fig = go.Figure(go.Bar(x=[NICE[i] for i in order], y=imp[order], marker_color=POS,
                           text=[f"{imp[i]:.2f}" for i in order], textposition="outside"))
    fig.update_layout(title="which measurement moves the condition band most")
    fig.update_yaxes(title="importance")
    style(fig, 400)
    animate(fig, S.bars_grow([dict(x=[NICE[i] for i in order], y=list(imp[order]), color=POS,
                                   text=[f"{imp[i]:.2f}" for i in order])]), ms=70)
    st.plotly_chart(fig, use_container_width=True)
    st.success(f"**{NICE[int(order[0])]}** moves the classification more than anything else.")
    st.write("")
    st.markdown("##### Check it against IEC 60599 before believing it")
    st.markdown("""
- The **gases and partial discharge** should dominate, because they are what the health index penalises
  most heavily. If they did not, the model would have found some other route to the answer.
- **Age** correlates with almost everything: an old unit runs hotter, ages faster and generates more gas.
  A high importance on age may be the model keying on the *consequence* rather than the cause.
- **Hot spot and ageing rate** are derived from load and ambient, so they are not independent evidence.
  They tell you what the unit's history has been, not what is wrong with it now.
    """)
    st.info("Importance shows what moves the prediction. Cause is an engineering question, and this chart "
            "is where to start asking it — not where to stop.")


def render_audit():
    st.title("⑯ The maintenance audit")
    st.markdown("#### Recommended against decided, on units the model has never seen.")
    st.write("")
    d = get_data()
    cls, _ = get_models()
    ite = d["ite"]
    pred = cls.predict(d["X"][ite])
    true = d["y_cls"][ite]

    z = np.zeros((4, 4))
    for i in range(4):
        for j in range(4):
            z[i, j] = int(np.sum((true == i) & (pred == j)))
    fig = go.Figure(go.Heatmap(z=z, x=HEALTH_CLASSES, y=HEALTH_CLASSES,
                               colorscale=[[0, "#16202b"], [1, POS]], showscale=False,
                               texttemplate="%{z:.0f}", textfont=dict(size=14)))
    fig.update_layout(title="rows = the engineer's assessment · columns = the model's")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(style(fig, 420), use_container_width=True)

    over = int(np.sum(pred > true))
    under = int(np.sum(pred < true))
    hr = 3
    missed_hr = int(np.sum((true == hr) & (pred < hr)))
    caught_hr = int(np.sum((true == hr) & (pred == hr)))
    st.write("")
    m = st.columns(4)
    m[0].metric("More cautious than the engineer", over, f"cost {over*story.COST_UNNECESSARY:,}",
                delta_color="off")
    m[1].metric("Less cautious", under, delta_color="off")
    m[2].metric("High-risk units downgraded", missed_hr,
                f"exposure {missed_hr*story.COST_MISSED:,}", delta_color="inverse")
    m[3].metric("High-risk correctly escalated",
                f"{caught_hr/max(caught_hr+missed_hr,1):.0%}")
    st.write("")

    a, b = st.columns(2)
    a.markdown(f"<div style='background:{PANEL};border-left:4px solid {AMBER};border-radius:4px;"
               f"padding:14px'><b style='color:{AMBER}'>More cautious than the engineer</b><br>"
               f"<span style='color:{MUTED}'>An inspection or maintenance visit that was not needed. "
               f"About {story.COST_UNNECESSARY:,} each, plus a little credibility.</span></div>",
               unsafe_allow_html=True)
    b.markdown(f"<div style='background:{PANEL};border-left:4px solid {RED};border-radius:4px;"
               f"padding:14px'><b style='color:{RED}'>A high-risk unit downgraded</b><br>"
               f"<span style='color:{MUTED}'>Failure, an outage across twenty thousand customers, and an "
               f"emergency replacement with a year's lead time. About "
               f"{story.COST_MISSED:,}.</span></div>", unsafe_allow_html=True)
    st.write("")
    st.error(f"**That is a {story.COST_MISSED/story.COST_UNNECESSARY:.0f}× difference between two errors "
             f"a confusion matrix counts identically.** Overall accuracy is the wrong headline number "
             f"here, and a model tuned to maximise it would be tuned in the wrong direction.")
    st.success("The number to report is **the share of genuinely high-risk units correctly escalated**. "
               "Everything else is secondary — including being wrong in the safe direction.")


def render_proof():
    st.title("⑰ The verdict")
    st.write("")
    d = get_data()
    cls, _ = get_models()
    c_, ite = d["clean"], d["ite"]
    pred = cls.predict(d["X"][ite])
    true = d["y_cls"][ite]

    # Duval on its own: can it identify the at-risk units?
    zones = story.duval_zone(c_.ch4_ppm.values[ite], c_.c2h4_ppm.values[ite],
                             c_.c2h2_ppm.values[ite])
    duval_flag = np.isin(zones, ["D1", "D2", "T3"])
    at_risk = true >= 2
    st.write("")
    c = st.columns(3)
    c[0].metric("Duval alone — at-risk units flagged",
                f"{float(duval_flag[at_risk].mean()):.0%}")
    c[1].metric("The model — at-risk units flagged",
                f"{float((pred[at_risk] >= 2).mean()):.0%}")
    c[2].metric("Cooling faults either can see", "0 %", "no gas is generated", delta_color="off")
    st.write("")
    st.table(pd.DataFrame({
        "": ["Name an electrical fault type from gas", "Rank a unit's overall condition",
             "Use moisture, BDV, age and thermal history", "See a blocked radiator bank",
             "Tell a sunlit unit from a hot connection"],
        "Duval Triangle": ["✅ yes", "❌ no urgency", "❌ three gases only", "❌ no gas is generated",
                           "❌ n/a"],
        "The condition model": ["⚠️ indirectly", "✅ yes", "✅ all seventeen", "❌ no gas is generated",
                                "❌ n/a"],
        "The CNN on the survey": ["❌ no", "❌ no", "❌ no", "✅ yes", "✅ yes"],
    }))
    st.success("**These three do not compete.** Look down the rows: each method has at least one column "
               "where it is the only one that works. A blocked radiator generates no gas at all, and a "
               "developing winding fault shows in the oil months before anything appears on a survey.")
    st.info("That is the honest conclusion for this project. Not *deep learning wins*, but **the overlap "
            "between these methods is small, so removing any one of them creates a blind spot.**")


def render_fleet():
    st.title("⑲ The fleet screen")
    st.caption("The real question is never 'is TX094 healthy'. It is 'I can inspect twelve units this "
               "quarter — which twelve?'.")
    st.write("")
    d = get_data()
    cls, reg = get_models()
    c_ = d["clean"]
    ite = d["ite"]
    sub = c_.iloc[ite].copy()
    sub["predicted_hi"] = reg.predict(d["X"][ite])
    latest = sub.sort_values("predicted_hi").groupby("unit_id", as_index=False).first()
    latest = latest.sort_values("predicted_hi").reset_index(drop=True)

    budget = st.slider("Inspections you can fund this quarter", 4, 60, 12, 1)
    st.write("")
    fig = go.Figure(go.Bar(x=latest.unit_id[:60], y=latest.predicted_hi[:60],
                           marker_color=[RED if i < budget else MUTED for i in range(60)],
                           showlegend=False))
    fig.add_vline(x=budget - 0.5, line=dict(color=GREEN, width=3),
                  annotation_text=f"budget line — {budget} units")
    fig.update_layout(title="the fleet, ranked by predicted health index (worst first)")
    fig.update_xaxes(title="unit", tickangle=-90)
    fig.update_yaxes(title="predicted health index")
    st.plotly_chart(style(fig, 420), use_container_width=True)
    st.write("")

    st.markdown(f"##### The {budget} units this quarter's budget reaches")
    show = latest.head(budget)[["unit_id", "predicted_hi", "age_years", "c2h2_ppm",
                                "moisture_ppm", "hotspot_c"]].copy()
    show.columns = ["Unit", "Predicted health", "Age (yr)", "C₂H₂", "Moisture", "Hot spot"]
    st.dataframe(show.round(1), use_container_width=True, hide_index=True)
    st.write("")

    st.success("**This is the form the output has to take to be used at all.** A classifier that says "
               "ninety units are 'moderate risk' leaves the engineer exactly where they started. A ranked "
               "list with a budget line drawn across it is a plan.")
    st.info("Move the slider and watch which units cross the line. That is the conversation the tool is "
            "for: not *is this model accurate*, but *given what I can afford, am I looking at the right "
            "units?*")


def render_dashboard():
    st.title("⑳ What it is worth")
    st.caption("Failures avoided, minus the visits that found nothing — because a system that escalates "
               "everything avoids every failure and is useless.")
    st.write("")
    c = st.columns(3)
    fleet = c[0].slider("Transformers in the fleet", 50, 2000, 400, 10)
    base_rate = c[1].slider("Failures per 100 units per year, today", 0.2, 4.0, 1.2, 0.1)
    prevented = c[2].slider("Share of those the system catches in time (%)", 10, 90, 55, 5)

    EXTRA_VISITS_PER_UNIT = 0.35          # additional inspections the system generates, per unit-year
    failures = fleet * base_rate / 100.0
    avoided = failures * prevented / 100.0
    benefit = avoided * story.COST_MISSED
    extra_visits = fleet * EXTRA_VISITS_PER_UNIT
    visit_cost = extra_visits * story.COST_UNNECESSARY
    net = benefit - visit_cost

    k = st.columns(4)
    k[0].metric("Failures avoided", f"{avoided:.1f} / year")
    k[1].metric("Value of those", f"{benefit:,.0f} / year")
    k[2].metric("Extra inspections", f"{extra_visits:,.0f} / year",
                f"-{visit_cost:,.0f}", delta_color="inverse")
    k[3].metric("Net", f"{net:,.0f} / year")
    st.write("")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Failures avoided", "Extra inspections", "Net"],
                         y=[benefit, -visit_cost, net],
                         marker_color=[GREEN, RED, POS],
                         text=[f"{benefit:,.0f}", f"-{visit_cost:,.0f}", f"{net:,.0f}"],
                         textposition="outside"))
    fig.update_layout(title="the business case, with both sides in it", showlegend=False)
    fig.update_yaxes(title="per year")
    style(fig, 380)
    animate(fig, S.bars_grow([dict(x=["Failures avoided", "Extra inspections", "Net"],
                                   y=[benefit, -visit_cost, net], color=POS,
                                   text=[f"{benefit:,.0f}", f"-{visit_cost:,.0f}",
                                         f"{net:,.0f}"])]), ms=90)
    st.plotly_chart(fig, use_container_width=True)
    st.write("")

    st.info(f"With **{fleet} transformers**, **{base_rate:.1f} failures per 100 units per year** and "
            f"**{prevented}%** caught in time, the programme nets about **{net:,.0f} a year**.")
    st.warning("**Read the red bar, not just the green one.** Counting only avoided failures makes any "
               "system look excellent — including one that escalates every unit every week. Drag "
               "'failures per 100 units' down to 0.3 and the case narrows sharply, which is the honest "
               "answer for a young, well-maintained fleet.")
    st.error("And one figure is not on this chart at all: **the outage itself**. Twenty thousand customers "
             "off supply is a regulatory and reputational cost that does not reduce to a number here — "
             "which is a reason to be more cautious than this arithmetic, not less.")


# ============================================================================
# THE COURSE, AS ONE ASSET-MANAGEMENT PROJECT
# ============================================================================
STAGES = {
    "start":           ("⓪ The project — read this first", bridge.render_start),
    "asset":           ("① A transformer in service", story.render_asset),
    "monitoring":      ("② Continuous condition monitoring", story.render_monitoring),
    "reading":         ("③ One condition assessment", lambda: story.render_reading(get_data)),
    "two-records":     ("④ Test report vs thermal survey", story.render_two_records),
    "load":            ("⑤ The fleet log arrives", lambda: common.render_load(CFG)),
    "inspect":         ("⑥ Checking the records", lambda: common.render_inspect(CFG)),
    "clean":           ("⑦ Removing the faulty readings", render_clean),
    "split":           ("⑧ Known units vs sealed units", render_split),
    "duval":           ("⑨ The Duval Triangle", render_duval),
    "health-model":    ("⑩ Health from the measurements", render_health_model),
    "drivers":         ("⑪ What drives the assessment", render_drivers),
    "survey-problem":  ("⑫ The infrared survey", story.render_survey_problem),
    "handmade":        ("⑬ Setting a temperature alarm", story.render_handmade),
    "cnn-journey":     ("⑭ Reading the thermal pattern", story.render_cnn_journey),
    "thermal-locate":  ("⑮ Which part of the transformer?", story.render_thermal_locate),
    "audit":           ("⑯ The maintenance audit", render_audit),
    "proof":           ("⑰ The verdict", render_proof),
    "decision-screen": ("⑱ The decision support screen", story.render_decision_screen),
    "fleet":           ("⑲ The fleet screen", render_fleet),
    "dashboard":       ("⑳ What it is worth", render_dashboard),
}

ALIASES = {"overview": "asset", "ml-baseline": "health-model", "importance": "drivers",
           "fusion-engine": "decision-screen", "fusion": "decision-screen",
           "cnn": "cnn-journey", "gradcam": "thermal-locate", "normalize": "clean",
           "pipeline": "fleet"}

stage = bridge.route(STAGES, ALIASES)

if stage != "start":
    bridge.open_page(stage)

STAGES[stage][1]()

if stage != "start":
    bridge.close_page(stage)

S.footer_nav(STAGES, stage)
