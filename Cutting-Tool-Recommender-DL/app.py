"""
AI Cutting Tool Recommendation System - illustration app
========================================================
One project, 20 stage pages, taught as one tool-selection project.
Each notebook step links here with ?stage=<id>.

THE MACHINING MODEL IS THE NOTEBOOK'S, imported from story.py.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from sklearn.model_selection import train_test_split
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

st.set_page_config(page_title="AI Cutting Tool Recommendation", page_icon="🛠️", layout="wide")
bridge.inject_css()

CAT_IN = ["workpiece", "machine", "operation"]
NUM_IN = ["batch_qty", "required_ra_um", "nose_r_mm", "tool_dia_mm",
          "machine_power_kw", "machine_max_rpm", "machine_rigidity"]
NICE_NUM = ["Batch qty", "Ra required (µm)", "Nose radius (mm)", "Tool dia (mm)",
            "Machine power (kW)", "Machine max rpm", "Machine rigidity"]


# ----------------------------------------------------------------------------
# DATA  (the tool-room log — same generator as the notebook)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="Generating the tool-room job log…")
def get_data(n=4000, seed=42):
    rng = np.random.default_rng(seed)
    mats = list(story.BASE_VC)
    machs = list(story.MACHINES)
    ops = ["roughing", "semi_finish", "finishing"]
    rows = []
    for _ in range(n):
        mat = str(rng.choice(mats, p=[0.20, 0.08, 0.24, 0.12, 0.18, 0.10, 0.08]))
        mach = str(rng.choice(machs, p=[0.30, 0.34, 0.22, 0.14]))
        op = str(rng.choice(ops, p=[0.38, 0.30, 0.32]))
        qty = int(rng.choice([5, 15, 40, 120, 300, 800, 2000],
                             p=[0.10, 0.14, 0.20, 0.22, 0.16, 0.12, 0.06]))
        nose = float(rng.choice([0.4, 0.8, 1.2]))
        ra_req = float(rng.choice([0.8, 1.6, 3.2, 6.3],
                                  p=[0.18, 0.34, 0.30, 0.18] if op != "roughing"
                                  else [0.05, 0.20, 0.40, 0.35]))
        dia = float(rng.choice([6, 10, 16, 25, 40]))

        tool = story.choose_tool(mat, op, qty, rng)
        coat = story.choose_coating(mat, tool, rng)
        cool = story.choose_coolant(mat, op, rng)

        vc_ref = story.vc_ref_for(mat, tool, op)
        m = story.MACHINES[mach]
        vc = vc_ref * m["rigidity"] * rng.normal(1.0, 0.07)
        vc = float(np.clip(vc, 5, m["max_rpm"] * np.pi * dia / 1000.0))
        feed = float(np.clip(story.feed_for_ra(ra_req, nose) * rng.normal(0.92, 0.06), 0.02, 0.6))
        life = float(story.taylor_life(vc, vc_ref, tool) * rng.normal(1.0, 0.15))
        ra = float(story.ra_for_feed(feed, nose) * rng.normal(1.0, 0.10))

        rows.append(dict(workpiece=mat, machine=mach, operation=op, batch_qty=qty,
                         required_ra_um=ra_req, nose_r_mm=nose, tool_dia_mm=dia,
                         tool_material=tool, coating=coat, coolant=cool,
                         cutting_speed_m_min=round(vc, 1), feed_mm_rev=round(feed, 4),
                         tool_life_min=round(life, 1), measured_ra_um=round(ra, 2)))
    df = pd.DataFrame(rows)

    # the faults a typed-in ERP export carries
    dirty = df.copy()
    dirty.loc[rng.choice(n, 30, replace=False), "cutting_speed_m_min"] = 5000.0   # keying error
    dirty.loc[rng.choice(n, 25, replace=False), "tool_life_min"] = 0.0            # never filled in
    dirty.loc[rng.choice(n, 20, replace=False), "measured_ra_um"] = np.nan        # not measured
    dirty.loc[rng.choice(n, 15, replace=False), "feed_mm_rev"] = 0.0              # default left in
    dirty = pd.concat([dirty, dirty.sample(35, random_state=4)], ignore_index=True)

    clean = dirty.drop_duplicates().copy()
    clean = clean[clean.cutting_speed_m_min.between(3, 1600)]
    clean = clean[clean.tool_life_min > 0.5]
    clean = clean[clean.feed_mm_rev > 0.01]
    clean = clean.dropna(subset=["measured_ra_um"]).reset_index(drop=True)

    # the machine is named on the card, so its capability is a legitimate input
    for c, k in [("machine_power_kw", "power_kw"), ("machine_max_rpm", "max_rpm"),
                 ("machine_rigidity", "rigidity")]:
        clean[c] = clean.machine.map(lambda mm: story.MACHINES[mm][k])

    X = pd.get_dummies(clean[CAT_IN + NUM_IN], columns=CAT_IN).astype(float)
    cols = list(X.columns)
    itr, ite = train_test_split(np.arange(len(clean)), test_size=0.30, random_state=42,
                                stratify=clean.tool_material)
    return dict(truth=df, dirty=dirty, clean=clean, X=X.values, cols=cols, itr=itr, ite=ite)


@st.cache_resource(show_spinner="Fitting the recommendation models…")
def get_models():
    d = get_data()
    c, X, itr = d["clean"], d["X"], d["itr"]
    out = {}
    for tgt in ["tool_material", "coating", "coolant"]:
        out[tgt] = RandomForestClassifier(n_estimators=200, random_state=42).fit(
            X[itr], c[tgt].values[itr])
    for tgt in ["cutting_speed_m_min", "feed_mm_rev"]:
        out[tgt] = RandomForestRegressor(n_estimators=200, random_state=42).fit(
            X[itr], c[tgt].values[itr])
    return out


CFG = dict(
    data=lambda: dict(dirty=get_data()["dirty"], clean=get_data()["clean"]),
    FEATURES=["cutting_speed_m_min", "feed_mm_rev", "tool_life_min", "measured_ra_um"],
    NICE=["Speed (m/min)", "Feed (mm/rev)", "Tool life (min)", "Measured Ra (µm)"],
    unit="job", unit_plural="jobs", pos="mismatched", neg="matched",
    export_name="ERP export",
    faults="A keying error (5,000 m/min on titanium), a tool-life field never filled in (0 min), an "
           "unmeasured Ra and a default feed left at 0 all announce themselves here.",
    fault_example="5,000 m/min keying error",
    titles={"load": "⑤ The tool-room log arrives", "inspect": "⑥ Checking the records"},
)


# ============================================================================
# RENDERERS
# ============================================================================
def render_clean():
    st.title("⑦ Removing the bad records")
    d = get_data()
    before, after = len(d["dirty"]), len(d["clean"])
    c = st.columns(3)
    c[0].metric("Records before", f"{before:,}")
    c[1].metric("Records after", f"{after:,}", f"-{before-after}")
    c[2].metric("Removed", f"{(before-after)/before*100:.1f} %", delta_color="off")
    st.caption("Duplicates dropped, then records that could not physically have happened.")
    st.write("")

    checks = [
        ("Duplicate bookings", int(d["dirty"].duplicated().sum())),
        ("Impossible cutting speed", int((~d["dirty"].cutting_speed_m_min.between(3, 1600)).sum())),
        ("Tool life never recorded", int((d["dirty"].tool_life_min <= 0.5).sum())),
        ("Feed left at the default", int((d["dirty"].feed_mm_rev <= 0.01).sum())),
        ("Ra not measured", int(d["dirty"].measured_ra_um.isna().sum())),
    ]
    fig = go.Figure(go.Bar(x=[c_[0] for c_ in checks], y=[c_[1] for c_ in checks],
                           marker_color=AMBER, text=[c_[1] for c_ in checks],
                           textposition="outside"))
    fig.update_layout(title="what was removed, and why")
    fig.update_yaxes(title="records")
    style(fig, 360)
    animate(fig, S.bars_grow([dict(x=[c_[0] for c_ in checks], y=[c_[1] for c_ in checks],
                                   color=AMBER, text=[c_[1] for c_ in checks])]), ms=80)
    st.plotly_chart(fig, use_container_width=True)
    st.write("")

    st.markdown("##### What each removal costs")
    counts = d["clean"].tool_material.value_counts()
    st.dataframe(pd.DataFrame({"Tool material": counts.index, "Jobs remaining": counts.values}),
                 use_container_width=True, hide_index=True)
    st.warning(f"**Look at the smallest class.** With only a few dozen jobs on some tool materials, every "
               f"deleted record removes a meaningful share of the evidence for it. That is why records are "
               f"removed on **physical impossibility**, not on looking unusual.")
    st.info("And it is why the removals are counted and reported. A cleaning step nobody documented is a "
            "cleaning step nobody can audit.")


def render_encoding():
    st.title("⑧ Materials are names, not numbers")
    d = get_data()
    st.write("")
    st.markdown("##### The wrong way, shown once so the reason is concrete")
    mats = list(story.BASE_VC)
    st.dataframe(pd.DataFrame({
        "Material": mats, "Numbered 1–7": list(range(1, len(mats) + 1)),
        "What that implies": ["—", "brass = 2 × aluminium", "mild steel = 3 × aluminium",
                              "cast iron is 'between' steel and stainless",
                              "the average of brass and titanium is cast iron",
                              "titanium > stainless in some ordering", "inconel is the 'largest'"],
    }), use_container_width=True, hide_index=True)
    st.error("None of that is true, and a model will happily use all of it. A tree will split at "
             "'material ≤ 3.5' and thereby group aluminium, brass and mild steel — which is a real "
             "grouping by luck, not by design, and it falls apart the moment the list is reordered.")
    st.write("")

    st.markdown("##### One-hot encoding: one column per value, no ordering implied")
    ex = pd.get_dummies(pd.DataFrame({"workpiece": mats[:4]}), columns=["workpiece"]).astype(int)
    st.dataframe(ex, use_container_width=True, hide_index=True)
    c = st.columns(3)
    c[0].metric("Original columns", len(CAT_IN))
    c[1].metric("After encoding", int(d["X"].shape[1] - len(NUM_IN)))
    c[2].metric("Total model inputs", d["X"].shape[1])
    st.write("")
    st.success("The cost is width — three fields become fourteen columns. The benefit is that the model "
               "cannot invent a relationship the shop does not have.")
    st.info("**When would numbering be right?** When the categories genuinely are ordered and evenly "
            "spaced — roughing, semi-finish, finishing is arguably one such case. Materials are not.")


def render_split():
    st.title("⑨ Known jobs vs sealed jobs")
    d = get_data()
    c_ = d["clean"]
    st.info("🧪 **Some tool materials appear in only a few dozen jobs.** A careless random split can leave "
            "none of them in the test set — and the score would then say nothing about the cases that "
            "matter most.")
    st.write("")
    rows = []
    for t in story.TOOL_MATERIALS:
        tr = int((c_.tool_material.values[d["itr"]] == t).sum())
        te = int((c_.tool_material.values[d["ite"]] == t).sum())
        rows.append([t, tr, te, f"{te/max(tr+te,1)*100:.0f}%"])
    st.dataframe(pd.DataFrame(rows, columns=["Tool material", "Train", "Test", "Test share"]),
                 use_container_width=True, hide_index=True)
    st.write("")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[r[0] for r in rows], y=[r[1] for r in rows], name="train",
                         marker_color=POS))
    fig.add_trace(go.Bar(x=[r[0] for r in rows], y=[r[2] for r in rows], name="test",
                         marker_color=GREEN))
    fig.update_layout(barmode="stack", title="stratified: every tool material appears in both halves")
    fig.update_yaxes(title="jobs")
    st.plotly_chart(style(fig, 360), use_container_width=True)
    st.success("Every class appears in both halves in roughly the same proportion. That is what `stratify=` "
               "buys, and it costs nothing.")


def render_tool_model():
    st.title("⑩ Which tool for this job?")
    d = get_data()
    M = get_models()
    c_, X, ite = d["clean"], d["X"], d["ite"]
    st.write("")
    accs = []
    for tgt, label in [("tool_material", "Tool material"), ("coating", "Coating"),
                       ("coolant", "Coolant")]:
        accs.append([label, f"{float((M[tgt].predict(X[ite]) == c_[tgt].values[ite]).mean()):.1%}",
                     c_[tgt].nunique()])
    st.dataframe(pd.DataFrame(accs, columns=["Decision", "Accuracy on sealed jobs", "Classes"]),
                 use_container_width=True, hide_index=True)
    st.write("")

    st.markdown("##### Try a job card")
    c = st.columns(4)
    mat = c[0].selectbox("Workpiece", list(story.BASE_VC), index=5)
    mach = c[1].selectbox("Machine", list(story.MACHINES), index=2)
    op = c[2].selectbox("Operation", ["roughing", "semi_finish", "finishing"], index=2)
    qty = c[3].select_slider("Batch", [5, 15, 40, 120, 300, 800, 2000], value=120)
    c2 = st.columns(3)
    ra_req = c2[0].select_slider("Ra required (µm)", [0.8, 1.6, 3.2, 6.3], value=1.6)
    nose = c2[1].select_slider("Nose radius (mm)", [0.4, 0.8, 1.2], value=0.8)
    dia = c2[2].select_slider("Tool diameter (mm)", [6, 10, 16, 25, 40], value=16)

    m = story.MACHINES[mach]
    row = dict(batch_qty=qty, required_ra_um=ra_req, nose_r_mm=nose, tool_dia_mm=dia,
               machine_power_kw=m["power_kw"], machine_max_rpm=m["max_rpm"],
               machine_rigidity=m["rigidity"])
    x = pd.DataFrame([row]).reindex(columns=d["cols"], fill_value=0.0)
    for f, v in [("workpiece", mat), ("machine", mach), ("operation", op)]:
        col = f"{f}_{v}"
        if col in x.columns:
            x[col] = 1.0
    x = x.values.astype(float)
    st.write("")

    cols = st.columns(3)
    for col, tgt, label in zip(cols, ["tool_material", "coating", "coolant"],
                               ["Tool material", "Coating", "Coolant"]):
        pred = M[tgt].predict(x)[0]
        proba = M[tgt].predict_proba(x)[0].max()
        col.markdown(f"<div style='background:{PANEL};border-left:4px solid {POS};border-radius:4px;"
                     f"padding:14px'><span style='color:{MUTED};font-size:12px;letter-spacing:.1em'>"
                     f"{label.upper()}</span><br><b style='color:{TEXT};font-size:20px'>{pred}</b><br>"
                     f"<span style='color:{MUTED};font-size:13px'>confidence {proba:.0%}</span></div>",
                     unsafe_allow_html=True)
    st.write("")

    rng = np.random.default_rng(0)
    shop = story.choose_tool(mat, op, qty, rng)
    st.caption(f"The shop's own rule for this card would give **{shop}**.")
    st.info("**An 88% accurate classifier is not a failed one here.** The shop itself deviates on a few "
            "per cent of jobs — a different setter, a stock-out, a customer preference — so perfect "
            "agreement would mean the model had memorised the noise as well as the logic.")
    st.warning("Watch the confidence when you pick a difficult alloy with a small batch. A split "
               "probability is the model telling you the shop does not agree with itself on that case — "
               "which is useful information, not a defect.")


def render_speed_feed():
    st.title("⑪ What speed and what feed?")
    d = get_data()
    M = get_models()
    c_, X, ite = d["clean"], d["X"], d["ite"]
    st.write("")
    c = st.columns(2)
    c[0].metric("Speed R² on sealed jobs",
                f"{r2_score(c_.cutting_speed_m_min.values[ite], M['cutting_speed_m_min'].predict(X[ite])):.3f}")
    c[1].metric("Feed R² on sealed jobs",
                f"{r2_score(c_.feed_mm_rev.values[ite], M['feed_mm_rev'].predict(X[ite])):.3f}")
    st.write("")

    st.markdown("##### The physics the regressors are checked against")
    cc = st.columns(3)
    mat = cc[0].selectbox("Workpiece", list(story.BASE_VC), index=2)
    tool = cc[1].selectbox("Tool material", story.TOOL_MATERIALS, index=2)
    nose = cc[2].select_slider("Nose radius (mm)", [0.4, 0.8, 1.2], value=0.8)
    ra_req = st.select_slider("Required Ra (µm)", [0.8, 1.6, 3.2, 6.3], value=1.6)

    vc_ref = story.vc_ref_for(mat, tool, "semi_finish")
    vcs = np.linspace(vc_ref * 0.4, vc_ref * 1.8, 150)
    life = story.taylor_life(vcs, vc_ref, tool)
    feeds = np.linspace(0.02, 0.5, 150)
    ras = story.ra_for_feed(feeds, nose)
    f_max = float(story.feed_for_ra(ra_req, nose))

    a, b = st.columns(2)
    with a:
        fig = go.Figure(go.Scatter(x=vcs, y=life, mode="lines", line=dict(color=POS, width=3)))
        fig.add_vline(x=vc_ref, line=dict(color=GREEN, dash="dash"),
                      annotation_text=f"catalogue {vc_ref:.0f}")
        fig.update_layout(title=f"Taylor: V·T^{story.TAYLOR_N[tool]:.2f} = C")
        fig.update_xaxes(title="cutting speed (m/min)")
        fig.update_yaxes(title="tool life (min)", type="log")
        st.plotly_chart(style(fig, 340), use_container_width=True)
    with b:
        fig2 = go.Figure(go.Scatter(x=feeds, y=ras, mode="lines", line=dict(color=AMBER, width=3)))
        fig2.add_hline(y=ra_req, line=dict(color=RED, dash="dash"),
                       annotation_text=f"required Ra {ra_req} µm")
        fig2.add_vline(x=f_max, line=dict(color=GREEN, dash="dash"),
                       annotation_text=f"largest feed {f_max:.3f}")
        fig2.update_layout(title="Ra ≈ f² / (32 · r)")
        fig2.update_xaxes(title="feed (mm/rev)"); fig2.update_yaxes(title="Ra (µm)", range=[0, 10])
        st.plotly_chart(style(fig2, 340), use_container_width=True)
    st.write("")

    m = st.columns(3)
    m[0].metric("Reference speed", f"{vc_ref:.0f} m/min")
    m[1].metric("Largest feed for that finish", f"{f_max:.3f} mm/rev")
    m[2].metric("Life at reference speed", f"{float(story.taylor_life(vc_ref, vc_ref, tool)):.0f} min")
    st.write("")

    st.success("**Both of these are geometry and physics, not fits.** Ra ≈ f²/32r comes from the shape the "
               "nose radius leaves behind; Taylor's equation is a century of measured tool life. They do "
               "not need a model — they are what the model gets checked against.")
    st.warning("If the regressor predicts a feed above the green line, it has recommended a finish the "
               "part cannot hold. The correct response is to **take the physics and overrule the model**, "
               "not to retrain with more trees.")


def render_drivers():
    st.title("⑫ What actually decides the tool")
    d = get_data()
    M = get_models()
    imp = M["tool_material"].feature_importances_
    names = d["cols"]
    order = np.argsort(imp)[::-1][:12]
    fig = go.Figure(go.Bar(x=[names[i] for i in order], y=imp[order], marker_color=POS,
                           text=[f"{imp[i]:.2f}" for i in order], textposition="outside"))
    fig.update_layout(title="which job-card field moves the tool choice most")
    fig.update_yaxes(title="importance")
    style(fig, 400)
    animate(fig, S.bars_grow([dict(x=[names[i] for i in order], y=list(imp[order]), color=POS,
                                   text=[f"{imp[i]:.2f}" for i in order])]), ms=70)
    st.plotly_chart(fig, use_container_width=True)
    st.success(f"**{names[int(order[0])]}** moves the choice more than anything else.")
    st.write("")
    st.markdown("##### Check it against the tool room before believing it")
    st.markdown("""
- **The material columns should dominate.** They do in the shop's own logic, so if they did not here, the
  model would have found some other route to the answer — and that route would break on a new job mix.
- **Batch quantity should matter for the cheap materials only.** It is what decides whether a PCD insert
  pays back on aluminium, and it should be almost irrelevant on inconel.
- **Watch for the machine standing in for the material.** Certain jobs only run on certain machines, so a
  high importance on `machine_*` may be a correlation rather than a cause.
    """)
    st.info("Importance points at what moves the prediction, not at what causes the outcome. Use it to "
            "start a conversation with the setter, not to end one.")


def render_audit():
    st.title("⑰ The tool-room audit")
    d = get_data()
    M = get_models()
    c_, X, ite = d["clean"], d["X"], d["ite"]
    pred = M["tool_material"].predict(X[ite])
    true = c_.tool_material.values[ite]
    mats_te = c_.workpiece.values[ite]
    st.write("")

    overall = float((pred == true).mean())
    hard = np.isin(mats_te, story.HARD)
    acc_hard = float((pred[hard] == true[hard]).mean())
    acc_easy = float((pred[~hard] == true[~hard]).mean())
    m = st.columns(3)
    m[0].metric("Overall accuracy", f"{overall:.1%}")
    m[1].metric("On easy materials", f"{acc_easy:.1%}")
    m[2].metric("On the difficult alloys", f"{acc_hard:.1%}",
                f"{(acc_hard-acc_easy)*100:+.1f} pts", delta_color="normal")
    st.write("")

    labels = story.TOOL_MATERIALS
    z = np.zeros((len(labels), len(labels)))
    for i, t in enumerate(labels):
        for j, p in enumerate(labels):
            z[i, j] = int(np.sum((true == t) & (pred == p)))
    fig = go.Figure(go.Heatmap(z=z, x=labels, y=labels,
                               colorscale=[[0, "#16202b"], [1, POS]], showscale=False,
                               texttemplate="%{z:.0f}", textfont=dict(size=12)))
    fig.update_layout(title="rows = what the shop chose · columns = what the model recommended")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(style(fig, 420), use_container_width=True)
    st.write("")

    st.markdown("### The errors do not cost the same")
    a, b = st.columns(2)
    a.markdown(f"<div style='background:{PANEL};border-left:4px solid {AMBER};border-radius:4px;"
               f"padding:14px'><b style='color:{AMBER}'>Wrong tool on mild steel</b><br>"
               f"<span style='color:{MUTED}'>Coated carbide instead of cermet on a finishing pass. Cost: "
               f"a slightly worse finish and a shorter edge — around "
               f"{story.INSERT_COST:.0f} of insert.</span></div>", unsafe_allow_html=True)
    b.markdown(f"<div style='background:{PANEL};border-left:4px solid {RED};border-radius:4px;"
               f"padding:14px'><b style='color:{RED}'>Wrong tool on inconel</b><br>"
               f"<span style='color:{MUTED}'>PCD instead of carbide: the diamond reacts with the alloy, "
               f"the edge fails in seconds and the part is scrapped. Cost: about "
               f"{story.SCRAP_EVENT:.0f}, plus the spindle time.</span></div>", unsafe_allow_html=True)
    st.write("")
    st.info(f"That is a **{story.SCRAP_EVENT/story.INSERT_COST:.0f}× difference** between two errors that "
            f"a confusion matrix counts identically. Overall accuracy of {overall:.1%} is dominated by the "
            f"easy materials — which is exactly why the difficult alloys are reported separately.")


def render_proof():
    st.title("⑱ The verdict")
    d = get_data()
    M = get_models()
    c_, X, ite = d["clean"], d["X"], d["ite"]
    acc = float((M["tool_material"].predict(X[ite]) == c_.tool_material.values[ite]).mean())
    st.write("")
    c = st.columns(2)
    c[0].metric("Random Forest on the job card", f"{acc:.1%} tool accuracy")
    c[1].metric("CNN on the job card", "impossible", "it has never seen a card", delta_color="off")
    st.write("")
    st.table(pd.DataFrame({
        "": ["Choose tool / coating / coolant from a job card", "Predict speed and feed",
             "Grade a wear land from a photo", "Tell built-up edge from wear",
             "Who names the features?"],
        "ML — Random Forest": ["✅ works", "✅ works", "❌ can't even start", "❌ no", "The engineer"],
        "DL — CNN": ["❌ no job card input", "❌ no", "✅ learns the pattern", "✅ yes",
                     "The network learns them"],
    }))
    st.success("Neither model can do the other's job, and neither is the better method. The forest "
               "recovers the shop's selection logic from named fields; the CNN reads an image nobody can "
               "hand-write a rule for. **Each belongs to its data type.**")
    st.info("AI does not out-think the setter here. It reads four thousand past jobs before every new one, "
            "and it looks at an insert edge without getting tired at four o'clock.")


def render_dashboard():
    st.title("⑳ What it is worth")
    st.caption("Read this one carefully — the obvious business case does not survive contact with the "
               "data.")
    st.write("")
    c = st.columns(3)
    jobs = c[0].slider("Jobs per year", 500, 12000, story.JOBS_PER_YEAR, 100)
    hard_share = c[1].slider("Share of jobs on difficult alloys (%)", 5, 60, 26, 1)
    caught = c[2].slider("Share of wrong-tool events the system prevents (%)", 10, 90, 55, 5)

    # --- the arithmetic, all of it on the assumptions above ------------------
    WRONG_RATE_HARD = 0.04        # how often a difficult alloy currently gets the wrong tool
    WRONG_RATE_EASY = 0.06        # easy materials go wrong more often, and cost far less
    EDGES_PER_JOB = 1.8

    hard_jobs = jobs * hard_share / 100.0
    easy_jobs = jobs - hard_jobs
    scrap_events = hard_jobs * WRONG_RATE_HARD
    scrap_avoided = scrap_events * caught / 100.0
    scrap_money = scrap_avoided * story.SCRAP_EVENT

    insert_events = easy_jobs * WRONG_RATE_EASY
    insert_avoided = insert_events * caught / 100.0
    insert_money = insert_avoided * story.INSERT_COST * EDGES_PER_JOB

    total = scrap_money + insert_money

    k = st.columns(4)
    k[0].metric("Scrap events avoided", f"{scrap_avoided:.0f} / year")
    k[1].metric("Value of avoided scrap", f"{scrap_money:,.0f} / year")
    k[2].metric("Value of saved inserts", f"{insert_money:,.0f} / year")
    k[3].metric("Total", f"{total:,.0f} / year")
    st.write("")

    fig = go.Figure(go.Bar(x=["Saved inserts", "Avoided scrapped parts"],
                           y=[insert_money, scrap_money], marker_color=[AMBER, GREEN],
                           text=[f"{insert_money:,.0f}", f"{scrap_money:,.0f}"],
                           textposition="outside"))
    fig.update_layout(title="where the money actually is", showlegend=False)
    fig.update_yaxes(title="per year")
    style(fig, 380)
    animate(fig, S.bars_grow([dict(x=["Saved inserts", "Avoided scrapped parts"],
                                   y=[insert_money, scrap_money], color=GREEN,
                                   text=[f"{insert_money:,.0f}", f"{scrap_money:,.0f}"])]), ms=90)
    st.plotly_chart(fig, use_container_width=True)
    st.write("")

    ratio = scrap_money / max(insert_money, 1e-9)
    st.error(f"**The obvious business case is the wrong one.** "
             f"'The model picks better tools, so we spend less on tooling' produces the small amber bar: "
             f"about **{insert_money:,.0f} a year**. Inserts cost {story.INSERT_COST:.0f} each. A scrapped "
             f"titanium part costs {story.SCRAP_EVENT:.0f}.")
    st.success(f"The real case is the green bar — **{ratio:.0f}× larger**. The system earns its place by "
               f"preventing a small number of expensive mistakes on difficult alloys, not by shaving the "
               f"tool crib.")
    st.warning("**Read the assumptions, not just the total.** Every figure is arithmetic on the three "
               "sliders. Drag 'difficult alloys' down to 5% and the case largely disappears — which is the "
               "honest answer for a shop that only machines aluminium. **This project is worth doing "
               "because of what this shop cuts, not because it uses AI.**")


# ============================================================================
# THE COURSE, AS ONE TOOL-SELECTION PROJECT
# ============================================================================
STAGES = {
    "start":          ("⓪ The project — read this first", bridge.render_start),
    "job-card":       ("① A job card arrives", story.render_job_card),
    "memory":         ("② The tool room's memory", story.render_memory),
    "reading":        ("③ One completed job", lambda: story.render_reading(get_data)),
    "two-records":    ("④ Job card vs insert photo", story.render_two_records),
    "load":           ("⑤ The tool-room log arrives", lambda: common.render_load(CFG)),
    "inspect":        ("⑥ Checking the records", lambda: common.render_inspect(CFG)),
    "clean":          ("⑦ Removing the bad records", render_clean),
    "encoding":       ("⑧ Materials are names, not numbers", render_encoding),
    "split":          ("⑨ Known jobs vs sealed jobs", render_split),
    "tool-model":     ("⑩ Which tool for this job?", render_tool_model),
    "speed-feed":     ("⑪ What speed and what feed?", render_speed_feed),
    "drivers":        ("⑫ What actually decides the tool", render_drivers),
    "insert-problem": ("⑬ The insert under the camera", story.render_insert_problem),
    "handmade":       ("⑭ Measuring wear by brightness", story.render_handmade),
    "cnn-journey":    ("⑮ Grading the wear land", story.render_cnn_journey),
    "wear-locate":    ("⑯ Where is the wear?", story.render_wear_locate),
    "audit":          ("⑰ The tool-room audit", render_audit),
    "proof":          ("⑱ The verdict", render_proof),
    "fusion-engine":  ("⑲ The setup sheet", story.render_fusion_engine),
    "dashboard":      ("⑳ What it is worth", render_dashboard),
}

ALIASES = {"overview": "job-card", "normalize": "encoding", "ml-baseline": "tool-model",
           "fusion": "fusion-engine", "importance": "drivers", "cnn": "cnn-journey",
           "gradcam": "wear-locate"}

stage = bridge.route(STAGES, ALIASES)

if stage != "start":
    bridge.open_page(stage)

STAGES[stage][1]()

if stage != "start":
    bridge.close_page(stage)

S.footer_nav(STAGES, stage)
