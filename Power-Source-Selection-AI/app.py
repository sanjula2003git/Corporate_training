"""
AI for Power Source Selection - decision-support illustration app
=================================================================
One project, 21 stage pages, taught as one microgrid dispatch study.
Each notebook step links here with ?stage=<id>.

The problem: a campus microgrid must choose between solar, wind, battery, grid
and diesel every fifteen minutes — 96 decisions a day, each one about a price
four hours away.
  Data      : demand, solar, wind, net load, SOC, tariff, price ahead, forecast,
              cyclical hour, grid availability, temperature.
  Labels    : a perfect-foresight dynamic-programming optimiser, run on history.
  Model     : tree / forest / boosting, scored in RUPEES rather than accuracy.
  System    : closed-loop evaluation, cost-weighted confusion, outages, business case.

THE MICROGRID MODEL IS THE NOTEBOOK'S, imported from story.py.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from sklearn.model_selection import GroupShuffleSplit
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

import scaffold as S
import common
import story
import bridge

POS, NEG = S.POS, S.NEG
GREEN, AMBER, RED = S.GREEN, S.AMBER, S.RED
TECH, MUTED, TEXT, PANEL = S.TECH, S.MUTED, S.TEXT, S.PANEL
style, animate = S.style, S.animate

st.set_page_config(page_title="AI for Power Source Selection", page_icon="🔌", layout="wide")
bridge.inject_css()

DT, STEPS_PER_DAY = story.DT, story.STEPS
CLASSES, CLASS_COL = story.CLASSES, story.CLASS_COL
N_DAYS = 120

FEATURES = ["demand_kw", "solar_kw", "wind_kw", "net_load_kw", "battery_soc",
            "grid_price", "price_max_next4h", "solar_fc_next2h",
            "hour_sin", "hour_cos", "weekend", "grid_available", "temp_c"]
NICE = ["Demand (kW)", "Solar (kW)", "Wind (kW)", "Net load (kW)", "SOC (%)",
        "Price now", "Max price 4 h", "Solar fc 2 h",
        "hour sin", "hour cos", "Weekend", "Grid up", "Temp (°C)"]
CHECK = ["demand_kw", "solar_kw", "wind_kw", "temp_c"]


# ----------------------------------------------------------------------------
# DATA  (the historian export — same generator as the notebook)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="Generating four months of microgrid history…")
def get_data(n_days=N_DAYS, seed=42):
    rng = np.random.default_rng(seed)
    rows = []
    for d in range(n_days):
        weekend = (d % 7) in (5, 6)
        cloud_day = float(np.clip(rng.beta(5, 2), 0.15, 1.0))
        wind_day = float(np.clip(rng.weibull(2.0) * 0.55, 0.02, 1.0))
        temp_day = float(rng.normal(29, 4))
        # grid outages: rare, and they last a while when they happen
        out_start = int(rng.integers(0, STEPS_PER_DAY)) if rng.random() < 0.05 else -1
        out_len = int(rng.integers(4, 14)) if out_start >= 0 else 0

        for k in range(STEPS_PER_DAY):
            h = k * DT
            cloud = float(np.clip(cloud_day + rng.normal(0, 0.10), 0.05, 1.0))
            gridok = not (out_start >= 0 and out_start <= k < out_start + out_len)
            rows.append(dict(
                day=d, step=k, hour=h, weekend=int(weekend),
                demand_kw=float(story.demand_profile(h, weekend) * (1 + 0.05 * rng.normal())),
                solar_kw=float(story.solar_profile(h, cloud)),
                wind_kw=float(np.clip(story.WT_KW * wind_day * (1 + 0.25 * rng.normal()),
                                      0, story.WT_KW)),
                grid_price=float(story.tariff(h)), grid_available=int(gridok),
                temp_c=float(temp_day + 5 * np.sin(np.pi * (h - 7) / 14)), cloud=cloud))
    df = pd.DataFrame(rows)
    df["net_load_kw"] = df.demand_kw - df.solar_kw - df.wind_kw

    # the faults every real export carries
    dirty = df.copy()
    n = len(dirty)
    for c in CHECK:
        dirty.loc[rng.choice(n, int(0.004 * n), replace=False), c] = np.nan
    dirty.loc[rng.choice(n, 40, replace=False), "solar_kw"] = -6.0      # inverter night offset
    dirty.loc[rng.choice(n, 30, replace=False), "demand_kw"] = 0.0      # meter comms dropout
    dirty.loc[rng.choice(n, 25, replace=False), "wind_kw"] = 9999.0     # anemometer spike

    # --- cleaning: mask the impossible, interpolate IN TIME, re-derive net load
    clean = dirty.copy()
    clean.loc[clean.solar_kw < 0, "solar_kw"] = np.nan
    clean.loc[clean.demand_kw < 50, "demand_kw"] = np.nan
    clean.loc[clean.wind_kw > story.WT_KW * 1.05, "wind_kw"] = np.nan
    for c in CHECK:
        clean[c] = clean[c].interpolate(limit_direction="both")
    clean["net_load_kw"] = clean.demand_kw - clean.solar_kw - clean.wind_kw

    # --- features the controller can legitimately observe at decision time
    feat = clean.copy()
    ang = 2 * np.pi * feat.hour / 24.0
    feat["hour_sin"], feat["hour_cos"] = np.sin(ang), np.cos(ang)
    fwd = np.arange(1, 17) * DT                             # the next 4 hours
    feat["price_max_next4h"] = np.max([story.tariff(feat.hour.values + f) for f in fwd], axis=0)
    fc_err = rng.normal(1.0, 0.18, len(feat))               # the forecast is NOT perfect
    fc = np.mean([story.solar_profile(feat.hour.values + f, 1.0)
                  for f in np.arange(1, 9) * DT], axis=0)
    feat["solar_fc_next2h"] = np.clip(fc * feat.cloud.values * fc_err, 0, story.PV_KW)

    # --- the perfect-foresight optimum for every day, and the SOC it implies
    sols, labels, socs = [], [], []
    for d_i in range(n_days):
        g = feat[feat.day == d_i]
        s = story.solve_day(g.net_load_kw.values, g.grid_price.values, g.grid_available.values)
        sols.append(s)
        labels.extend([story.label_of(b, gr, x)
                       for b, gr, x in zip(s.bat_kw, s.grid_kw, s.diesel_kw)])
        socs.extend(s.soc.tolist())
    sol = pd.concat(sols, ignore_index=True)
    feat["battery_soc"] = socs               # the state the optimum actually visits
    feat["label"] = labels
    feat["opt_cost"] = sol.cost.values

    # the rule's own decision on the same rows, for the label-trap page
    rule_lab, soc = [], 55.0
    for r in feat.itertuples():
        rule_lab.append(story.rule_decision(r.net_load_kw, soc, r.grid_price,
                                            bool(r.grid_available), r.price_max_next4h))
        _, soc, _ = story.dispatch_cost(rule_lab[-1], r.net_load_kw, soc, r.grid_price,
                                        bool(r.grid_available))
    feat["rule_label"] = rule_lab

    # --- the split that does not lie: whole DAYS, never shuffled intervals
    gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    itr, ite = next(gss.split(feat, groups=feat.day))
    return dict(dirty=dirty, clean=clean, feat=feat, sol=sol,
                itr=itr, ite=ite,
                train_days=sorted(feat.day.values[itr].tolist()[:1] +
                                  list(np.unique(feat.day.values[itr]))),
                test_days=list(np.unique(feat.day.values[ite])))


@st.cache_resource(show_spinner="Fitting the decision models…")
def get_models():
    d = get_data()
    f = d["feat"]
    Xtr, ytr = f[FEATURES].values[d["itr"]], f["label"].values[d["itr"]]
    tree = DecisionTreeClassifier(max_depth=5, random_state=0).fit(Xtr, ytr)
    forest = RandomForestClassifier(n_estimators=200, random_state=0).fit(Xtr, ytr)
    boost = GradientBoostingClassifier(random_state=0).fit(Xtr, ytr)
    return tree, forest, boost


@st.cache_resource(show_spinner=False)
def get_trap_model():
    """The same model, trained on what the RULE did instead of what was best."""
    d = get_data()
    f = d["feat"]
    return RandomForestClassifier(n_estimators=200, random_state=0).fit(
        f[FEATURES].values[d["itr"]], f["rule_label"].values[d["itr"]])


CFG = dict(
    data=lambda: dict(dirty=get_data()["dirty"], clean=get_data()["clean"]),
    FEATURES=CHECK, NICE=["Demand (kW)", "Solar (kW)", "Wind (kW)", "Temp (°C)"],
    unit="interval", unit_plural="intervals", pos="expensive", neg="cheap",
    export_name="SCADA export",
    faults="An inverter night offset (−6 kW of solar), a meter comms dropout (0 kW of campus demand) and "
           "an anemometer spike (9,999 kW of wind) all announce themselves here.",
    fault_example="9,999 kW anemometer spike",
    titles={"load": "④ The SCADA export arrives", "inspect": "⑤ The meter health check"},
)


# ============================================================================
# RENDERERS
# ============================================================================
def render_load():
    common.render_load(CFG)


def render_inspect():
    common.render_inspect(CFG)


def render_clean():
    st.title("⑥ Correcting the record")
    d = get_data()
    st.caption("Impossible values masked, then interpolated **in time order** — because this is a "
               "sequential control problem and a hole in the day is not a neutral omission.")
    st.write("")
    c = st.columns(3)
    c[0].metric("Intervals", f"{len(d['clean']):,}")
    c[1].metric("Impossible values masked",
                int((d["dirty"].solar_kw < 0).sum() + (d["dirty"].demand_kw < 50).sum()
                    + (d["dirty"].wind_kw > story.WT_KW * 1.05).sum()))
    c[2].metric("Missing after", int(d["clean"][CHECK].isna().sum().sum()))
    st.write("")

    day = st.slider("Look at one day", 0, N_DAYS - 1, 3, 1)
    a = d["dirty"][d["dirty"].day == day]
    b = d["clean"][d["clean"].day == day]
    ch = st.selectbox("Channel", CHECK, index=1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=a.hour, y=a[ch], mode="lines+markers", name="dirty",
                             line=dict(color=NEG, width=1.5), marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=b.hour, y=b[ch], mode="lines", name="clean",
                             line=dict(color=GREEN, width=2.5)))
    fig.update_layout(title=f"{ch} on day {day} — the impossible points are gone")
    fig.update_xaxes(title="hour of day")
    st.plotly_chart(style(fig, 380), use_container_width=True)
    st.info("**Net load is re-derived after cleaning**, not carried over. If demand is repaired and net "
            "load is not, every downstream decision is made against a number that no longer matches its "
            "own parts.")


def render_features():
    st.title("⑦ Preparing the inputs")
    d = get_data()
    f = d["feat"]
    st.write("")

    st.markdown("##### Why the hour has to be a circle")
    rows = []
    for a, b in [(23.75, 0.0), (11.75, 12.0)]:
        plain = abs(a - b)
        circ = float(np.hypot(np.sin(2*np.pi*a/24) - np.sin(2*np.pi*b/24),
                              np.cos(2*np.pi*a/24) - np.cos(2*np.pi*b/24)))
        rows.append([f"{a:.2f} h → {b:.2f} h", "15 minutes", f"{plain:.2f}", f"{circ:.3f}"])
    st.dataframe(pd.DataFrame(rows, columns=[
        "Pair", "Actually apart", "As a plain number", "On the circle"]),
        use_container_width=True, hide_index=True)
    st.caption("Both pairs are fifteen minutes apart in reality. Only the circular encoding agrees.")
    st.write("")

    day = st.slider("Day to inspect", 0, N_DAYS - 1, 3, 1)
    g = f[f.day == day]
    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=g.hour, y=g.grid_price, mode="lines", name="price now",
                                 line=dict(color=POS, width=2.5), line_shape="hv"))
        fig.add_trace(go.Scatter(x=g.hour, y=g.price_max_next4h, mode="lines",
                                 name="max price, next 4 h",
                                 line=dict(color=RED, width=2.5, dash="dash")))
        fig.update_layout(title="the feature that lets a model SAVE the battery")
        fig.update_xaxes(title="hour"); fig.update_yaxes(title="Rs/kWh")
        st.plotly_chart(style(fig, 340), use_container_width=True)
    with c2:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=g.hour, y=g.solar_kw, mode="lines", name="solar now",
                                  line=dict(color="#ffd54f", width=2.5)))
        fig2.add_trace(go.Scatter(x=g.hour, y=g.solar_fc_next2h, mode="lines",
                                  name="forecast, next 2 h (imperfect)",
                                  line=dict(color=TEXT, width=2, dash="dash")))
        fig2.update_layout(title="the forecast is wrong, and still useful")
        fig2.update_xaxes(title="hour"); fig2.update_yaxes(title="kW")
        st.plotly_chart(style(fig2, 340), use_container_width=True)
    st.write("")

    st.success("**`price_max_next4h` is the important column.** At 16:00 the price is 8.00 and the rule "
               "sees no reason to hold charge. This column says 11.50 is coming, which is exactly the "
               "information that makes saving the battery the right call.")
    st.warning("**And the forecast deliberately has error in it.** A perfect solar forecast would be "
               "cheating: the controller would be given information no real site has, and every number "
               "afterwards would be optimistic.")


def render_split():
    st.title("⑧ Split by day, not by row")
    d = get_data()
    f = d["feat"]
    st.write("")

    st.info("🧪 **Consecutive intervals are almost identical.** The sun does not move much in fifteen "
            "minutes and the battery carries its state across. Shuffle rows and 19:00 lands in training "
            "while 19:15 lands in test — the model has effectively been shown the answer.")
    st.write("")

    tr_days = np.unique(f.day.values[d["itr"]])
    te_days = np.unique(f.day.values[d["ite"]])
    fig = go.Figure()
    fig.add_trace(go.Bar(x=list(range(N_DAYS)),
                         y=[1] * N_DAYS,
                         marker_color=[POS if i in set(tr_days.tolist()) else GREEN
                                       for i in range(N_DAYS)],
                         showlegend=False))
    fig.update_layout(title="whole days go to training (blue) or to test (green) — never both")
    fig.update_xaxes(title="day"); fig.update_yaxes(visible=False)
    st.plotly_chart(style(fig, 260), use_container_width=True)

    c = st.columns(4)
    c[0].metric("Training days", len(tr_days))
    c[1].metric("Test days (sealed)", len(te_days))
    c[2].metric("Training intervals", f"{len(d['itr']):,}")
    c[3].metric("Test intervals", f"{len(d['ite']):,}")
    st.write("")
    st.success("The score now measures what the controller would do **on a day it has never seen**, which "
               "is the only question the plant is actually asking.")


def render_rule():
    st.title("⑨ The rule the plant already runs")
    st.caption("A good controller, written by a plant engineer, and implemented properly before it is "
               "criticised.")
    st.write("")
    st.code("""if grid is down:      battery if charged, else diesel
if net load <= 0:     RENEWABLE            # surplus — store it
if price >= 11.0 and soc > 40:  RENEWABLE + BATTERY   # peak — discharge
if price <= 5.0  and soc < 80:  GRID + CHARGE         # off-peak — fill up
otherwise:            RENEWABLE + GRID""", language="python")
    st.write("")

    d = get_data()
    day = st.slider("Day to run it on", 0, N_DAYS - 1, 3, 1)
    g = d["feat"][d["feat"].day == day].reset_index(drop=True)

    fig = go.Figure()
    for c in CLASSES:
        m = g.rule_label == c
        fig.add_trace(go.Bar(x=g.hour[m], y=[1] * int(m.sum()), name=c,
                             marker_color=CLASS_COL[c], width=DT))
    fig.update_layout(barmode="stack", title="the rule's decisions across one day")
    fig.update_xaxes(title="hour of day", range=[0, 24]); fig.update_yaxes(visible=False)
    st.plotly_chart(style(fig, 300), use_container_width=True)

    fig2 = go.Figure()
    for c in CLASSES:
        m = g.label == c
        fig2.add_trace(go.Bar(x=g.hour[m], y=[1] * int(m.sum()), name=c,
                              marker_color=CLASS_COL[c], width=DT, showlegend=False))
    fig2.update_layout(barmode="stack", title="what the perfect-foresight optimum did, same day")
    fig2.update_xaxes(title="hour of day", range=[0, 24]); fig2.update_yaxes(visible=False)
    st.plotly_chart(style(fig2, 300), use_container_width=True)
    st.write("")

    agree = float((g.rule_label == g.label).mean())
    st.metric("Rule agrees with the optimum on this day", f"{agree:.0%}")
    st.write("")
    st.error("**The rule is myopic** — it sees only this interval. Look for hours where the optimum is "
             "charging or holding and the rule is not: those are the hours the rule spends charge it "
             "will want later, or leaves the battery empty into the peak.")
    st.info("No amount of tuning fixes that. The rule cannot look ahead, and the whole saving lives in "
            "looking ahead.")


def render_optimiser():
    st.title("⑩ What was actually best")
    st.caption("Dynamic programming, backwards from midnight, over every state of charge. Not an opinion — "
               "the provably cheapest schedule for that day.")
    st.write("")
    d = get_data()
    day = st.slider("Day to solve", 0, N_DAYS - 1, 3, 1)
    g = d["feat"][d["feat"].day == day].reset_index(drop=True)
    s = story.solve_day(g.net_load_kw.values, g.grid_price.values, g.grid_available.values)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=g.hour, y=g.net_load_kw, mode="lines", name="net load",
                             line=dict(color=TEXT, width=2)))
    fig.add_trace(go.Scatter(x=g.hour, y=s.bat_kw, mode="lines", name="battery (+ discharge)",
                             line=dict(color=GREEN, width=2.5)))
    fig.add_trace(go.Scatter(x=g.hour, y=s.grid_kw, mode="lines", name="grid",
                             line=dict(color=POS, width=2)))
    fig.add_hline(y=0, line=dict(color=MUTED, width=1))
    fig.update_layout(title="the cheapest dispatch for this day")
    fig.update_xaxes(title="hour of day"); fig.update_yaxes(title="kW")
    st.plotly_chart(style(fig, 360), use_container_width=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=g.hour, y=s.soc, mode="lines", line=dict(color=AMBER, width=3),
                              name="state of charge"))
    fig2.add_hline(y=story.SOC_MIN, line=dict(color=RED, dash="dash"),
                   annotation_text="reserve floor")
    fig2.add_vrect(x0=18, x1=22, fillcolor=RED, opacity=0.10, line_width=0,
                   annotation_text="evening peak", annotation_position="top left")
    fig2.update_layout(title="and the state of charge it implies")
    fig2.update_xaxes(title="hour of day"); fig2.update_yaxes(title="SOC (%)", range=[0, 100])
    style(fig2, 320); animate(fig2, S.line_grow(g.hour.values, s.soc.values, AMBER), ms=40)
    st.plotly_chart(fig2, use_container_width=True)

    c = st.columns(3)
    c[0].metric("Day cost, optimum", f"Rs {s.cost.sum():,.0f}")
    c[1].metric("Battery throughput", f"{np.abs(s.bat_kw).sum() * DT:,.0f} kWh")
    c[2].metric("Diesel used", f"{s.diesel_kw.sum() * DT:,.0f} kWh")
    st.write("")

    st.success("Watch the state of charge fill through the cheap hours and empty **into the evening peak**. "
               "Nobody wrote that behaviour as a rule — it fell out of minimising cost with the whole day "
               "known.")
    st.warning("**This is not a controller.** It needs perfect hindsight. Its only job is to say what was "
               "best, so a model can learn that mapping from information a real controller does have.")


def render_trap():
    st.title("⑪ The trap — learning your own rule back")
    st.caption("The tempting shortcut: label the history with what the existing controller did. The data is "
               "free and already there.")
    st.write("")
    d = get_data()
    f = d["feat"]
    trap = get_trap_model()
    tree, forest, boost = get_models()
    ite = d["ite"]

    X = f[FEATURES].values[ite]
    acc_trap = float(np.mean(trap.predict(X) == f["rule_label"].values[ite]))
    acc_opt = float(np.mean(forest.predict(X) == f["label"].values[ite]))

    # cost each controller in the same intervals
    def _cost(pred):
        soc, tot = 55.0, 0.0
        for p, r in zip(pred, f.iloc[ite].itertuples()):
            c, soc, _ = story.dispatch_cost(p, r.net_load_kw, soc, r.grid_price,
                                            bool(r.grid_available))
            tot += c
        return tot

    c_trap = _cost(trap.predict(X))
    c_opt = _cost(forest.predict(X))

    c1, c2 = st.columns(2)
    c1.metric("Trained on the RULE's decisions", f"{acc_trap:.1%} accuracy",
              f"Rs {c_trap:,.0f} over the test days", delta_color="off")
    c2.metric("Trained on the OPTIMISER's decisions", f"{acc_opt:.1%} accuracy",
              f"Rs {c_opt:,.0f} over the test days", delta_color="off")
    st.write("")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=["trained on the rule", "trained on the optimum"],
                         y=[acc_trap * 100, acc_opt * 100], name="accuracy (%)",
                         marker_color=AMBER, yaxis="y"))
    fig.add_trace(go.Scatter(x=["trained on the rule", "trained on the optimum"],
                             y=[c_trap, c_opt], name="cost (Rs)", yaxis="y2",
                             mode="lines+markers", line=dict(color=RED, width=3),
                             marker=dict(size=14)))
    fig.update_layout(title="the two numbers point in opposite directions",
                      yaxis=dict(title="accuracy (%)", range=[0, 105]),
                      yaxis2=dict(title="cost over the test days (Rs)", overlaying="y",
                                  side="right"))
    st.plotly_chart(style(fig, 400), use_container_width=True)
    st.write("")

    st.error("**Near-perfect accuracy, zero improvement.** Copying a deterministic rule is easy — the model "
             "learned the rule, *including its mistakes*, and automated them. The score looks excellent "
             "precisely because nothing was learned.")
    st.success("Label from the optimiser and accuracy goes **down** while the money saved goes **up**. That "
               "gap is the single most important idea in this project: **learn from what was best, not "
               "from what was done.**")


def render_models():
    st.title("⑫ The decision model")
    st.write("")
    d = get_data()
    f = d["feat"]
    tree, forest, boost = get_models()
    ite = d["ite"]
    X, y = f[FEATURES].values[ite], f["label"].values[ite]

    rows = []
    for name, m in [("Decision tree (depth 5)", tree), ("Random forest", forest),
                    ("Gradient boosting", boost)]:
        rows.append([name, f"{float(np.mean(m.predict(X) == y)):.1%}",
                     "✅ readable path" if name.startswith("Decision") else "⚠️ harder to read"])
    st.dataframe(pd.DataFrame(rows, columns=["Model", "Accuracy on sealed days", "Explainability"]),
                 use_container_width=True, hide_index=True)
    st.write("")

    fig = go.Figure()
    for name, m, col in [("tree", tree, AMBER), ("forest", forest, POS), ("boosting", boost, GREEN)]:
        acc = [float(np.mean(m.predict(X)[y == c] == c)) for c in CLASSES]
        fig.add_trace(go.Bar(x=CLASSES, y=acc, name=name, marker_color=col))
    fig.update_layout(title="recall per decision class — the rare classes are the hard ones")
    fig.update_yaxes(title="share correct", range=[0, 1.1])
    st.plotly_chart(style(fig, 400), use_container_width=True)
    st.write("")

    st.info("Look at the rare classes. **DIESEL** appears in about 1% of intervals and every model is "
            "weakest there — which matters, because that is the class that keeps the campus supplied "
            "during an outage.")
    st.success("The tree loses a little accuracy and keeps something the others do not: a decision path an "
               "operator can read and argue with. **The most accurate model is not automatically the one "
               "that gets commissioned.**")


def render_importance():
    st.title("⑬ What drives the decision")
    st.write("")
    _, forest, _ = get_models()
    imp = forest.feature_importances_
    order = np.argsort(imp)[::-1]
    fig = go.Figure(go.Bar(x=[NICE[i] for i in order], y=imp[order], marker_color=POS,
                           text=[f"{imp[i]:.2f}" for i in order], textposition="outside"))
    fig.update_layout(title="which column moves the decision most")
    fig.update_yaxes(title="importance")
    style(fig, 400)
    animate(fig, S.bars_grow([dict(x=[NICE[i] for i in order], y=list(imp[order]), color=POS,
                                   text=[f"{imp[i]:.2f}" for i in order])]), ms=70)
    st.plotly_chart(fig, use_container_width=True)

    st.success(f"**{NICE[int(order[0])]}** moves the decision more than anything else.")
    st.write("")
    st.markdown("##### Check it against the physics before believing it")
    st.markdown("""
- **Net load** deciding most is expected: it is the sign of net load that separates *store it* from
  *buy it*, and no other column can substitute.
- **Price now and max price in four hours** should both matter. If the forward price ranked near zero,
  the model would be as myopic as the rule — and the whole saving would have vanished.
- **State of charge** must matter, because the same net load calls for a different action at 25% and 90%.
- If any of these disagreed with what a power engineer expects, the right response is to **look for a
  labelling error**, not to accept the ranking.
    """)
    st.info("Importance is a sanity check, not a proof of cause. Several of these columns move together — "
            "price, hour and net load all peak in the evening — so the ranking tells you where to look, "
            "not what caused what.")


def render_explain():
    st.title("⑭ Explaining one decision")
    st.caption("An operator asked to accept a setpoint at 19:15 will ask why. This is the answer.")
    st.write("")
    d = get_data()
    f = d["feat"]
    tree, _, _ = get_models()

    day = st.slider("Day", 0, N_DAYS - 1, 3, 1)
    hour = st.slider("Hour", 0.0, 23.75, 19.25, 0.25)
    g = f[(f.day == day)]
    i = int(np.argmin(np.abs(g.hour.values - hour)))
    row = g.iloc[i]
    x = row[FEATURES].values.astype(float).reshape(1, -1)
    pred = tree.predict(x)[0]

    # walk the decision path
    node_ind = tree.decision_path(x)
    feature = tree.tree_.feature
    threshold = tree.tree_.threshold
    lines = []
    for node_id in node_ind.indices:
        if feature[node_id] < 0:
            continue
        fi = feature[node_id]
        op = "≤" if x[0, fi] <= threshold[node_id] else ">"
        lines.append(f"{NICE[fi]} = {x[0, fi]:.1f}  {op}  {threshold[node_id]:.1f}")

    st.markdown(f"<div style='background:{PANEL};border-left:5px solid {CLASS_COL[pred]};"
                f"border-radius:4px;padding:16px 20px'>"
                f"<b style='color:{CLASS_COL[pred]};font-size:20px'>{pred}</b><br>"
                f"<span style='color:{MUTED};font-size:14px'>day {day}, {row.hour:.2f} h · "
                f"net load {row.net_load_kw:.0f} kW · SOC {row.battery_soc:.0f}% · "
                f"price {row.grid_price:.2f} → {row.price_max_next4h:.2f} in 4 h</span></div>",
                unsafe_allow_html=True)
    st.write("")
    st.markdown("##### Because…")
    for l in lines:
        st.markdown(f"<div style='font-family:ui-monospace,monospace;color:{TEXT};"
                    f"background:#0b0e13;border-left:3px solid {TECH};padding:8px 14px;"
                    f"margin:4px 0'>▸ {l}</div>", unsafe_allow_html=True)
    st.write("")
    st.markdown(f"**The optimum for this interval was:** "
                f"<b style='color:{CLASS_COL[row.label]}'>{row.label}</b>", unsafe_allow_html=True)
    st.write("")
    st.info("Every line is a plain condition an engineer can check against the plant. That is the "
            "difference between a recommendation an operator accepts and one they override.")


def render_live():
    st.title("⑮ The live recommendation")
    st.caption("Set the conditions and read the call — with every alternative priced beside it.")
    st.write("")
    d = get_data()
    _, forest, _ = get_models()

    c = st.columns(4)
    demand = c[0].slider("Demand (kW)", 110.0, 500.0, 320.0, 5.0)
    solar = c[1].slider("Solar (kW)", 0.0, story.PV_KW, 40.0, 5.0)
    wind = c[2].slider("Wind (kW)", 0.0, story.WT_KW, 40.0, 5.0)
    soc = c[3].slider("State of charge (%)", story.SOC_MIN, story.SOC_MAX, 85.0, 1.0)
    c2 = st.columns(3)
    hour = c2[0].slider("Hour of day", 0.0, 23.75, 19.0, 0.25)
    gridok = c2[1].toggle("Grid available", value=True)
    weekend = c2[2].toggle("Weekend", value=False)

    net = demand - solar - wind
    price = float(story.tariff(hour))
    pmax4 = float(np.max([story.tariff(hour + f) for f in np.arange(1, 17) * DT]))
    fcast = float(np.mean([story.solar_profile(hour + f, 1.0) for f in np.arange(1, 9) * DT]))
    row = np.array([[demand, solar, wind, net, soc, price, pmax4, fcast,
                     np.sin(2*np.pi*hour/24), np.cos(2*np.pi*hour/24),
                     int(weekend), int(gridok), 29.0]])
    pred = forest.predict(row)[0]
    proba = forest.predict_proba(row)[0]

    st.write("")
    m = st.columns(4)
    m[0].metric("Net load", f"{net:.0f} kW", "surplus" if net < 0 else "deficit", delta_color="off")
    m[1].metric("Price now", f"Rs {price:.2f}")
    m[2].metric("Max price, next 4 h", f"Rs {pmax4:.2f}")
    m[3].metric("Confidence", f"{proba.max():.0%}")
    st.write("")
    st.markdown(f"<div style='padding:18px;border-radius:4px;text-align:center;font-size:22px;"
                f"font-weight:800;background:{CLASS_COL[pred]};color:#0e1117'>{pred}</div>",
                unsafe_allow_html=True)
    st.write("")

    costs = []
    for cl in CLASSES:
        cost, _, unserved = story.dispatch_cost(cl, net, soc, price, gridok)
        costs.append([cl, f"Rs {cost:,.1f}", "⚠️ load not supplied" if unserved > 1 else "—"])
    best = min(range(len(CLASSES)),
               key=lambda i: story.dispatch_cost(CLASSES[i], net, soc, price, gridok)[0])
    st.markdown("##### What each option would cost, this interval")
    st.dataframe(pd.DataFrame(costs, columns=["Option", "Cost of this interval", "Note"]),
                 use_container_width=True, hide_index=True)
    st.write("")

    if CLASSES[best] == pred:
        st.success(f"The model's call matches the cheapest option for this interval.")
    else:
        st.warning(f"The model chose **{pred}**; the cheapest option *this interval* is "
                   f"**{CLASSES[best]}**. That is not automatically an error — the model is trained on the "
                   f"optimum for the whole **day**, and holding charge for a coming peak costs a little now "
                   f"to save more later.")
    st.info("Showing the alternatives is what makes the recommendation reviewable: if second-best costs a "
            "rupee more, an override is harmless; if it costs six hundred, it is not.")


def render_regret():
    st.title("⑯ Why decision accuracy is the wrong score")
    st.write("")
    d = get_data()
    f = d["feat"]
    ite = d["ite"]
    sub = f.iloc[ite]

    # what each confusion actually costs, in the intervals where it happens
    rows = []
    for cl in CLASSES:
        m = (sub.label == cl).values
        if m.sum() == 0:
            continue
        r = sub[m]
        costs = []
        for alt in CLASSES:
            c1 = np.array([story.dispatch_cost(alt, n, s, p, bool(g))[0]
                           for n, s, p, g in zip(r.net_load_kw, r.battery_soc,
                                                 r.grid_price, r.grid_available)])
            c0 = np.array([story.dispatch_cost(cl, n, s, p, bool(g))[0]
                           for n, s, p, g in zip(r.net_load_kw, r.battery_soc,
                                                 r.grid_price, r.grid_available)])
            costs.append(float(np.mean(c1 - c0)))
        rows.append([cl] + [f"{v:,.1f}" for v in costs])
    st.markdown("##### Average regret (Rs per interval) of choosing the column, when the row was best")
    st.dataframe(pd.DataFrame(rows, columns=["Was best ↓ / chose →"] + CLASSES),
                 use_container_width=True, hide_index=True)
    st.write("")

    st.error("**Read across a row.** Some substitutions cost a rupee or two. Others cost hundreds. "
             "Accuracy counts every one of those as a single identical mistake.")
    st.success("So the score is **regret**: what the chosen action cost, minus what the optimum would have "
               "cost. That is the only number the plant actually experiences, and it is what every page "
               "from here on reports.")


def render_closed_loop():
    st.title("⑰ Closed-loop evaluation — a month run properly")
    st.caption("The controller drives the battery, so its own mistakes become its next inputs. That has to "
               "be in the test.")
    st.write("")
    d = get_data()
    f = d["feat"]
    _, forest, _ = get_models()
    te_days = list(np.unique(f.day.values[d["ite"]]))

    def run(controller, days):
        tot = 0.0
        per = []
        for dd in days:
            g = f[f.day == dd]
            soc = 55.0
            day_cost = 0.0
            if controller == "model":
                preds = forest.predict(g[FEATURES].values)
            for j, r in enumerate(g.itertuples()):
                if controller == "rule":
                    a = story.rule_decision(r.net_load_kw, soc, r.grid_price,
                                            bool(r.grid_available), r.price_max_next4h)
                elif controller == "model":
                    a = preds[j]
                else:
                    a = r.label
                c, soc, _ = story.dispatch_cost(a, r.net_load_kw, soc, r.grid_price,
                                                bool(r.grid_available))
                day_cost += c
            per.append(day_cost); tot += day_cost
        return tot, np.array(per)

    c_rule, p_rule = run("rule", te_days)
    c_model, p_model = run("model", te_days)
    c_opt = float(f.opt_cost.values[d["ite"]].sum())

    m = st.columns(4)
    m[0].metric("The rule", f"Rs {c_rule:,.0f}")
    m[1].metric("The model", f"Rs {c_model:,.0f}", f"{c_model - c_rule:,.0f} vs the rule")
    m[2].metric("Perfect foresight", f"Rs {c_opt:,.0f}", "impossible in real time", delta_color="off")
    m[3].metric("Saving vs the rule", f"{(c_rule - c_model) / c_rule * 100:.1f} %")
    st.write("")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=te_days, y=p_rule, mode="lines+markers", name="rule",
                             line=dict(color=NEG, width=2.5)))
    fig.add_trace(go.Scatter(x=te_days, y=p_model, mode="lines+markers", name="model",
                             line=dict(color=POS, width=2.5)))
    fig.update_layout(title="cost per sealed day, both controllers driving their own battery")
    fig.update_xaxes(title="day"); fig.update_yaxes(title="Rs")
    style(fig, 380); animate(fig, S.line_grow(np.array(te_days), p_model, POS), ms=70)
    st.plotly_chart(fig, use_container_width=True)
    st.write("")

    gap = (c_model - c_opt) / max(c_rule - c_opt, 1e-9)
    st.info(f"The model closes about **{(1-gap)*100:.0f}%** of the gap between the rule and perfect "
            f"foresight. It will never close all of it — the optimum knows the whole day in advance, and "
            f"the controller does not.")
    st.warning("**This is the honest test.** Scoring interval by interval would hand the model the correct "
               "state of charge at every step — the one thing it would not have in service.")


def render_confusion():
    st.title("⑱ When it is wrong")
    st.write("")
    d = get_data()
    f = d["feat"]
    _, forest, _ = get_models()
    ite = d["ite"]
    sub = f.iloc[ite]
    pred = forest.predict(sub[FEATURES].values)
    true = sub.label.values

    counts = np.zeros((len(CLASSES), len(CLASSES)))
    money = np.zeros((len(CLASSES), len(CLASSES)))
    for i, tc in enumerate(CLASSES):
        for j, pc in enumerate(CLASSES):
            m = (true == tc) & (pred == pc)
            counts[i, j] = m.sum()
            if m.sum():
                r = sub[m]
                c1 = np.array([story.dispatch_cost(pc, n, s, p, bool(g))[0]
                               for n, s, p, g in zip(r.net_load_kw, r.battery_soc,
                                                     r.grid_price, r.grid_available)])
                c0 = np.array([story.dispatch_cost(tc, n, s, p, bool(g))[0]
                               for n, s, p, g in zip(r.net_load_kw, r.battery_soc,
                                                     r.grid_price, r.grid_available)])
                money[i, j] = float(np.sum(c1 - c0))

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure(go.Heatmap(z=counts, x=CLASSES, y=CLASSES,
                                   colorscale=[[0, "#16202b"], [1, POS]], showscale=False,
                                   texttemplate="%{z:.0f}", textfont=dict(size=12)))
        fig.update_layout(title="by count — how often")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(style(fig, 400), use_container_width=True)
    with c2:
        fig2 = go.Figure(go.Heatmap(z=money, x=CLASSES, y=CLASSES,
                                    colorscale=[[0, "#16202b"], [1, RED]], showscale=False,
                                    texttemplate="%{z:,.0f}", textfont=dict(size=12)))
        fig2.update_layout(title="by cost — how much (Rs)")
        fig2.update_yaxes(autorange="reversed")
        st.plotly_chart(style(fig2, 400), use_container_width=True)
    st.caption("Rows are what was best; columns are what the model chose.")
    st.write("")

    off = money.copy(); np.fill_diagonal(off, 0)
    i, j = np.unravel_index(np.argmax(off), off.shape)
    st.error(f"**The two pictures are not the same.** The most *frequent* confusion is often nearly free. "
             f"The most *expensive* one here is choosing **{CLASSES[j]}** when **{CLASSES[i]}** was best — "
             f"Rs {off[i, j]:,.0f} across the sealed days.")
    st.info("That is the failure mode to watch in service, and it is invisible on a count-based confusion "
            "matrix — which is the one almost every tutorial shows.")


def render_outage():
    st.title("⑲ When the grid fails")
    st.caption("Rare, expensive, and non-negotiable — the case an average-cost objective will optimise "
               "away if you let it.")
    st.write("")
    d = get_data()
    f = d["feat"]
    out = f[f.grid_available == 0]
    st.write("")
    c = st.columns(3)
    c[0].metric("Intervals with the grid down", f"{len(out):,}",
                f"{len(out)/len(f)*100:.1f}% of the data")
    c[1].metric("Value of lost load", f"Rs {story.VOLL:,.0f}/kWh")
    c[2].metric("Diesel", f"Rs {story.DIESEL_RS:.0f}/kWh")
    st.write("")

    soc0 = st.slider("State of charge when the outage starts (%)", story.SOC_MIN, story.SOC_MAX, 60.0, 1.0)
    net = st.slider("Net load during the outage (kW)", 50.0, 450.0, 260.0, 10.0)
    hours_out = st.slider("How long the outage lasts (hours)", 0.5, 8.0, 3.0, 0.5)

    usable_kwh = (soc0 - story.SOC_MIN) / 100.0 * story.CAP_KWH * story.ETA_D
    battery_hours = usable_kwh / max(net, 1e-6)
    diesel_hours = max(hours_out - battery_hours, 0.0)
    diesel_kwh = diesel_hours * min(net, story.DIESEL_KW)
    unserved_kwh = diesel_hours * max(net - story.DIESEL_KW, 0.0)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Battery", "Diesel", "Not supplied"],
                         y=[min(battery_hours, hours_out) * net, diesel_kwh, unserved_kwh],
                         marker_color=[GREEN, AMBER, RED],
                         text=[f"{min(battery_hours, hours_out)*net:,.0f} kWh",
                               f"{diesel_kwh:,.0f} kWh", f"{unserved_kwh:,.0f} kWh"],
                         textposition="outside"))
    fig.update_layout(title="who supplies the campus during the outage", showlegend=False)
    fig.update_yaxes(title="kWh")
    st.plotly_chart(style(fig, 360), use_container_width=True)

    cost = diesel_kwh * story.DIESEL_RS + unserved_kwh * story.VOLL
    m = st.columns(3)
    m[0].metric("Battery covers", f"{min(battery_hours, hours_out):.1f} h")
    m[1].metric("Cost of the outage", f"Rs {cost:,.0f}")
    m[2].metric("Load not supplied", f"{unserved_kwh:,.0f} kWh",
                delta_color="inverse" if unserved_kwh > 0 else "off")
    st.write("")

    st.warning(f"**Drop the starting state of charge and watch the cost jump.** A controller that has been "
               f"rewarded for emptying the battery every evening has no reserve when this arrives — and "
               f"outages are only **{len(out)/len(f)*100:.1f}%** of the data, so an average-cost objective "
               f"barely notices.")
    st.success(f"Pricing unserved energy at **Rs {story.VOLL:,.0f}/kWh** is what stops that. It makes the "
               f"reserve something the optimiser has to earn rather than something a designer has to "
               f"remember. **A rare class with a real cost must be priced, not counted.**")


def render_dashboard():
    st.title("㉑ What it is worth")
    st.caption("Everything above becomes numbers a site manager can approve — measured against the rule "
               "the plant already runs, not against doing nothing.")
    st.write("")
    d = get_data()
    f = d["feat"]
    _, forest, _ = get_models()
    te_days = list(np.unique(f.day.values[d["ite"]]))

    # closed-loop cost for both controllers on the sealed days
    def run(controller):
        tot = 0.0
        for dd in te_days:
            g = f[f.day == dd]
            soc = 55.0
            preds = forest.predict(g[FEATURES].values) if controller == "model" else None
            for j, r in enumerate(g.itertuples()):
                a = (preds[j] if controller == "model" else
                     story.rule_decision(r.net_load_kw, soc, r.grid_price,
                                         bool(r.grid_available), r.price_max_next4h))
                c, soc, _ = story.dispatch_cost(a, r.net_load_kw, soc, r.grid_price,
                                                bool(r.grid_available))
                tot += c
        return tot

    c_rule, c_model = run("rule"), run("model")
    per_day_saving = (c_rule - c_model) / len(te_days)

    c = st.columns(3)
    sites = c[0].slider("Sites in the programme", 1, 40, 6, 1)
    uptake = c[1].slider("Share of recommendations actually followed (%)", 20, 100, 75, 5)
    capex = c[2].slider("One-off cost per site (Rs lakh)", 1.0, 40.0, 8.0, 0.5)

    annual = per_day_saving * 365 * sites * uptake / 100.0
    capex_total = capex * 1e5 * sites
    payback = capex_total / max(annual, 1e-9)

    k = st.columns(4)
    k[0].metric("Saving per site per day", f"Rs {per_day_saving:,.0f}")
    k[1].metric("Annual saving", f"Rs {annual:,.0f}")
    k[2].metric("One-off cost", f"Rs {capex_total:,.0f}")
    k[3].metric("Payback", f"{payback:.1f} years")
    st.write("")

    fig = go.Figure()
    fig.add_trace(go.Bar(x=["The rule the plant runs today", "The model"],
                         y=[c_rule, c_model], marker_color=[RED, GREEN],
                         text=[f"Rs {c_rule:,.0f}", f"Rs {c_model:,.0f}"], textposition="outside"))
    fig.update_layout(title=f"energy cost over {len(te_days)} sealed days, one site", showlegend=False)
    fig.update_yaxes(title="Rs")
    style(fig, 380)
    animate(fig, S.bars_grow([dict(x=["The rule the plant runs today", "The model"],
                                   y=[c_rule, c_model], color=GREEN,
                                   text=[f"Rs {c_rule:,.0f}", f"Rs {c_model:,.0f}"])]), ms=90)
    st.plotly_chart(fig, use_container_width=True)
    st.write("")

    st.info(f"With **{sites} sites** and **{uptake}%** of recommendations followed, the programme saves "
            f"about **Rs {annual:,.0f} a year** and pays back in **{payback:.1f} years**.")
    st.warning("**Read the comparison, not just the total.** This is measured against the **existing "
               "rule**, which already captures most of the easy saving. Comparing against an unmanaged "
               "microgrid would produce a far bigger number and a far less honest one — and the uptake "
               "slider is the honest part: a recommendation nobody follows saves nothing.")


# ============================================================================
# THE COURSE, AS ONE DISPATCH STUDY
# ============================================================================
STAGES = {
    "start":       ("⓪ The project — read this first", bridge.render_start),
    "microgrid":   ("① The microgrid at 06:00", story.render_microgrid),
    "sources":     ("② Five sources, five real costs", story.render_sources),
    "reading":     ("③ One interval", lambda: story.render_reading(get_data)),
    "load":        ("④ The SCADA export arrives", render_load),
    "inspect":     ("⑤ The meter health check", render_inspect),
    "clean":       ("⑥ Correcting the record", render_clean),
    "features":    ("⑦ Preparing the inputs", render_features),
    "split":       ("⑧ Split by day", render_split),
    "rule":        ("⑨ The rule already run", render_rule),
    "optimiser":   ("⑩ What was actually best", render_optimiser),
    "trap":        ("⑪ The label trap", render_trap),
    "models":      ("⑫ The decision model", render_models),
    "importance":  ("⑬ What drives the decision", render_importance),
    "explain":     ("⑭ Explaining one decision", render_explain),
    "live":        ("⑮ The live recommendation", render_live),
    "regret":      ("⑯ Regret in rupees", render_regret),
    "closed-loop": ("⑰ A month, closed-loop", render_closed_loop),
    "confusion":   ("⑱ When it is wrong", render_confusion),
    "outage":      ("⑲ When the grid fails", render_outage),
    "engine":      ("⑳ The recommendation", story.render_engine),
    "dashboard":   ("㉑ What it is worth", render_dashboard),
}

ALIASES = {"overview": "microgrid", "fusion-engine": "engine", "normalize": "features",
           "ml-baseline": "models", "drivers": "importance", "audit": "confusion",
           "proof": "regret", "pipeline": "closed-loop"}

stage = bridge.route(STAGES, ALIASES)

if stage != "start":
    bridge.open_page(stage)

STAGES[stage][1]()

if stage != "start":
    bridge.close_page(stage)

S.footer_nav(STAGES, stage)
