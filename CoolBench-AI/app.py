"""CoolBench - the illustration app for the notebook.

One page per teaching step, routed by ?stage=<id>. The bench, the heat model
and the controllers are the notebook's, trimmed to fit a 1 GB Streamlit Cloud
container: fewer training episodes and a smaller forest.

Navigation is by button, never by markdown link: Streamlit renders every
markdown link with target="_blank", so a link would open a new browser tab on
every click.
"""
import numpy as np
import pandas as pd
import streamlit as st

import bridge
import story

st.set_page_config(page_title="CoolBench heat-emergency station", page_icon="🌡️", layout="wide")
st.markdown("""<style>
.stApp{background:#0e1117;color:#e6edf3}
.block-container{max-width:1200px}
.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}
.scene{color:#ffb74d}.ai{color:#4fc3f7}
.stButton button,div[data-testid="stButton"] button{background:transparent;border:1px solid #30363d;
    color:#e6edf3;justify-content:flex-start;text-align:left;font-weight:400}
.stButton button:hover,div[data-testid="stButton"] button:hover{border-color:#ffb74d;color:#ffb74d;
    background:#161b22}
</style>""", unsafe_allow_html=True)

DISCLAIMER = ("Educational simulation on an invented emergency. The body temperature in it is a "
              "teaching estimate, not a measurement. Nothing here is a medical device, and no "
              "part of it may be used to decide the care of a real person.")

# --------------------------------------------------------------- controls
with st.sidebar:
    st.header("The afternoon")
    ambient = st.slider("Air temperature °C", 32.0, 46.0, 41.0, 0.5)
    rh = st.slider("Humidity %", 10, 90, 32, 2) / 100.0
    solar = st.slider("Sunshine W/m²", 200, 1000, 880, 20)
    wind = st.slider("Wind m/s", 0.0, 3.0, 0.6, 0.1)
    st.header("The bench")
    water_l = st.slider("Water in the tank, litres", 0.5, 8.0, 8.0, 0.5)
    battery_pct = st.slider("Battery %", 10, 100, 61, 1)
    packs = st.slider("Cold packs", 0, 3, 3)
    eta = st.slider("Minutes until responders arrive", 6, 30, 14)
    st.caption("Change anything and every page below re-runs.")

SC_KEY = (ambient, rh, solar, wind, water_l, battery_pct, packs, eta)


def scenario(**kw):
    base = dict(ambient=ambient, rh=rh, solar=solar, wind=wind, water_l=water_l,
                battery_pct=float(battery_pct), packs=packs, eta=float(eta))
    base.update(kw)
    return story.make_scenario(**base)


AIR = dict(ambient=ambient, rh=rh, solar=solar, wind=wind)


@st.cache_data(show_spinner="Playing a few hundred emergencies...")
def get_data():
    return story.build_dataset(200)


@st.cache_resource(show_spinner="Learning what each setting does...")
def get_models():
    d = get_data()
    return story.fit_models(d[d.episode < 150])


@st.cache_data(show_spinner=False)
def get_scores():
    d = get_data()
    te = d[d.episode >= 150]
    return story.model_scores(get_models(), te), story.rollout_error(get_models(), te)


@st.cache_data(show_spinner=False)
def get_runs(key, which=None, **kw):
    """Every controller on one scenario. `key` only exists to bust the cache."""
    sc = scenario(**kw)
    forest = get_models()["random forest"]
    setups = dict(story.CONTROLLERS)
    setups["predictive AI"] = (story.make_ai(False), True)
    setups["resource-aware AI"] = (story.make_ai(True), True)
    out = {}
    for name, (ctrl, safe) in setups.items():
        if which and name not in which:
            continue
        out[name] = story.run(ctrl, sc, safety=safe, model=forest)
    return out, sc


def board_of(runs, sc):
    rows = []
    for name, df in runs.items():
        s = story.score(df, sc)
        rows.append({"Controller": name, "Change °C": s["change"], "Peak °C": s["peak"],
                     "Lowest °C": s["lowest"], "Heat burden": s["burden"],
                     "Minutes over 40 °C": s["over_warn"], "Water used L": s["water"],
                     "Battery left %": s["battery_left"], "Packs used": s["packs"],
                     "Radio minutes left": s["radio_min"], "Commands blocked": s["blocked"]})
    return pd.DataFrame(rows)


stage = st.query_params.get("stage", "start")


# --------------------------------------------------------------- page frame
def goto(target, label, key, where=None):
    if (where or st).button(label, key=key, width="stretch"):
        st.query_params["stage"] = target
        st.rerun()


def header(s):
    p = bridge.PHASES[s["phase"]]
    st.markdown(
        f"<div class='hero'><small>PHASE {s['phase'] + 1} OF {len(bridge.PHASES)} · {p[0]}</small>"
        f"<h1>🌡️ {s['scene']}</h1><h3><span class='scene'>{s['scene']}</span> → "
        f"<span class='ai'>{s['ai']}</span></h3></div>", unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.markdown("#### 1 · At the bench")
    a.write(s["site"])
    b.markdown("#### 2 · Why it is hard")
    b.write(s["challenge"])
    c.markdown("#### 3 · Where the AI comes in")
    c.write(s["ai_link"])
    st.markdown(f"#### 4 · What it looks like — `{s['tech']}`")


def footer(s):
    st.markdown("#### 5 · In the notebook")
    st.write(s["notebook"])
    st.success(s["takeaway"])
    i = bridge.ORDER.index(s["id"])
    cols = st.columns(3)
    if i:
        goto(bridge.ORDER[i - 1], f"◀ {bridge.STEPS[i - 1]['scene']}", f"prev_{s['id']}", cols[0])
    goto("start", "Overview", f"home_{s['id']}", cols[1])
    if i < len(bridge.STEPS) - 1:
        goto(bridge.ORDER[i + 1], f"{bridge.STEPS[i + 1]['scene']} ▶", f"next_{s['id']}", cols[2])


# --------------------------------------------------------------- landing
if stage == "start":
    st.title("🌡️ CoolBench — an AI heat-emergency cooling station")
    st.warning(DISCLAIMER)
    st.markdown(
        "A bench in a park has a fan, a water mister, a shade cover, cold packs, a battery and "
        "a water tank. **This project works out how to use those limited supplies to cool an "
        "overheated person until help arrives, without running out.**")

    runs, sc = get_runs(SC_KEY)
    board = board_of(runs, sc)
    none_row = board[board["Controller"] == "no cooling"].iloc[0]
    ai_row = board[board["Controller"] == "resource-aware AI"].iloc[0]
    mx_row = board[board["Controller"] == "maximum fixed"].iloc[0]
    a, b, c, d = st.columns(4)
    a.metric("Doing nothing", f"{none_row['Change °C']:+.2f} °C")
    b.metric("Full power", f"{mx_row['Change °C']:+.2f} °C", f"{mx_row['Water used L']} L used",
             delta_color="off")
    c.metric("Resource-aware AI", f"{ai_row['Change °C']:+.2f} °C",
             f"{ai_row['Water used L']} L used", delta_color="off")
    d.metric("Radio minutes left", f"{ai_row['Radio minutes left']}",
             f"vs {mx_row['Radio minutes left']} at full power")

    st.plotly_chart(story.fig_runs(runs), width="stretch")
    st.caption("Every line is the same emergency. Only the strategy differs.")

    st.subheader("The scoreboard, at your settings")
    st.dataframe(board.set_index("Controller"), width="stretch")

    st.subheader("Learning journey")
    for i, s in enumerate(bridge.STEPS, 1):
        goto(s["id"], f"**{i}. {s['scene']}** — {s['ai']}", f"jump_{s['id']}")

    st.subheader("The notebook")
    st.markdown(
        "[Open the full teaching notebook in Colab]"
        "(https://colab.research.google.com/github/sanjula2003git/Corporate_training/blob/main/"
        "CoolBench-AI/CoolBench_Heat_Emergency_Station.ipynb)")

else:
    s = bridge.BY_ID.get(stage, bridge.STEPS[0])
    header(s)

    # ----------------------------------------------------------- per stage
    if s["id"] == "bench":
        a, b, c, d = st.columns(4)
        a.metric("Water", f"{water_l:.1f} L")
        b.metric("Battery", f"{battery_pct} %", f"{story.BATTERY_WH * battery_pct / 100:.0f} Wh")
        c.metric("Cold packs", packs)
        d.metric("Responders in", f"{eta} min")
        st.dataframe(pd.DataFrame([
            {"Part": "Canopy", "What it does": "blocks about 88 % of the sun",
             "Costs": "one push of the motor"},
            {"Part": "Fan", "What it does": "moves air across the skin",
             "Costs": f"up to {story.p_fan(1.0):.0f} W"},
            {"Part": "Mister", "What it does": "keeps the skin wet so water can evaporate",
             "Costs": "up to 400 mL a minute, plus a 28 W pump"},
            {"Part": "Cold packs", "What it does": "take heat away by touch",
             "Costs": "one pack, gone for good"},
            {"Part": "Radio, screen, speaker", "What it does": "talk to the dispatcher",
             "Costs": f"{story.P_ESSENTIAL:.0f} W, never switched off"},
        ]).set_index("Part"), width="stretch")
        st.info("The radio's share of the battery is not negotiable. Every other number on "
                "this page is.")

    elif s["id"] == "afternoon":
        st.plotly_chart(story.fig_day(), width="stretch")
        st.plotly_chart(story.fig_same_temperature(), width="stretch")
        cap = story.skin_state(39.8, AIR, 0.75, story.MIST_LEVELS["medium"])[3]
        a, b, c = st.columns(3)
        a.metric("Air temperature", f"{ambient:.1f} °C")
        b.metric("Bench surface", f"{ambient + 7:.1f} °C")
        c.metric("Watts the air can carry away", f"{cap:.0f} W")

    elif s["id"] == "heat":
        c1, c2 = st.columns(2)
        canopy = c1.checkbox("Canopy out", value=False)
        fan = c1.select_slider("Fan", story.FAN_LEVELS, value=0.0)
        mist = c2.select_slider("Mist, mL/min", list(story.MIST_LEVELS.values()), value=0.0)
        temp = c2.slider("Simulated body temperature °C", 38.0, 41.5, 39.8, 0.1)
        act = dict(canopy=int(canopy), fan=float(fan), mist=float(mist))
        st.plotly_chart(story.fig_balance(temp, AIR, act), width="stretch")
        p = story.heat_terms(temp, AIR, act)
        net = story.net_watts(temp, AIR, act, [], 0.0)[0]
        a, b, c = st.columns(3)
        a.metric("Net heat", f"{net:+.0f} W", f"{net / story.C_BODY * 60:+.3f} °C a minute",
                 delta_color="off")
        b.metric("Skin temperature", f"{p['T_sk']:.1f} °C")
        c.metric("Skin wetness", f"{p['w']:.2f}", "1.00 is as wet as skin gets",
                 delta_color="off")

    elif s["id"] == "sensors":
        c1, c2 = st.columns(2)
        c1.plotly_chart(story.fig_thermal("hot"), width="stretch")
        c2.plotly_chart(story.fig_thermal("cool"), width="stretch")
        runs, sc = get_runs(SC_KEY, which=["maximum fixed"])
        df = runs["maximum fixed"]
        st.plotly_chart(story.fig_camera_gap(df), width="stretch")
        gap = float((df["body"] - df["naive_est"]).max())
        st.error(f"At its worst the uncorrected reading is **{gap:.1f} °C** below the real "
                 "simulated body temperature. A bench that believed it would stop cooling "
                 "while the person was still dangerously hot.")

    elif s["id"] in ("nothing", "shade", "fan", "mist", "packs"):
        want = {"nothing": ["no cooling"], "shade": ["no cooling", "shade only"],
                "fan": ["no cooling", "shade only", "fan only"],
                "mist": ["shade only", "fan only", "mist only"],
                "packs": ["no cooling", "shade only", "mist only"]}[s["id"]]
        runs, sc = get_runs(SC_KEY, which=want)
        st.plotly_chart(story.fig_runs(runs), width="stretch")
        st.dataframe(board_of(runs, sc).set_index("Controller"), width="stretch")
        if s["id"] == "fan":
            wet = st.checkbox("Wet the skin first (mist on)", value=False)
            st.plotly_chart(story.fig_fan_map(story.MIST_LEVELS["medium"] if wet else 0.0),
                            width="stretch")
            off = story.net_watts(39.8, AIR, dict(canopy=1, fan=0.0, mist=0.0), [], 0.0)[0]
            on = story.net_watts(39.8, AIR, dict(canopy=1, fan=1.0, mist=0.0), [], 0.0)[0]
            st.metric("Fan at full power, on dry skin, in your weather",
                      f"{off - on:+.0f} W of cooling",
                      "a negative number means the fan is a heater", delta_color="off")
        if s["id"] == "mist":
            st.plotly_chart(story.fig_water_curve(AIR), width="stretch")
            st.dataframe(story.water_curve(AIR).set_index("mist mL/min"), width="stretch")
        if s["id"] == "packs":
            st.plotly_chart(story.fig_packs(), width="stretch")

    elif s["id"] == "maxout":
        runs, sc = get_runs(SC_KEY, which=["no cooling", "maximum fixed", "resource-aware AI"])
        st.plotly_chart(story.fig_runs(runs), width="stretch")
        st.plotly_chart(story.fig_resources({k: v for k, v in runs.items()
                                             if k != "no cooling"}), width="stretch")
        st.dataframe(board_of(runs, sc).set_index("Controller"), width="stretch")
        mx = story.score(runs["maximum fixed"], sc)
        st.warning(f"Full power took the simulated temperature down to **{mx['lowest']} °C** — "
                   f"past the {story.STOP_COOL} °C at which cooling should stop — and spent "
                   f"**{mx['water']} L** doing it.")

    elif s["id"] == "rules":
        runs, sc = get_runs(SC_KEY, which=["rule based", "maximum fixed", "resource-aware AI"])
        st.plotly_chart(story.fig_runs(runs), width="stretch")
        st.plotly_chart(story.fig_j_terms(runs["rule based"]), width="stretch")
        st.dataframe(board_of(runs, sc).set_index("Controller"), width="stretch")
        st.code("""if cooling is no longer needed:            do nothing
budget      = (water - 0.5 L) / minutes left
free_energy = battery - what the radio needs
if the pump works and free_energy > 2 Wh and the air can take vapour:
    mist = the largest level the budget allows, never above medium
if misting and the fan works and free_energy > 3 Wh:
    fan = 75 %
if a pack is left, none is on, and the person is above 39.0 C:
    open one pack""", language="python")

    elif s["id"] == "forecast":
        scores, rollout = get_scores()
        st.dataframe(scores.set_index("Model"), width="stretch")
        st.plotly_chart(story.fig_models(scores), width="stretch")
        st.markdown("**Five minutes out, where the errors have had time to pile up:**")
        st.dataframe(rollout.set_index("Model"), width="stretch")
        forest = get_models()["random forest"]
        imp = pd.Series(forest.feature_importances_, index=story.FEATURES).sort_values()
        import plotly.graph_objects as go
        fig = go.Figure(go.Bar(x=imp.values, y=imp.index, orientation="h",
                               marker_color=story.CYAN))
        st.plotly_chart(story._layout(fig, height=380,
                                      xaxis_title="how much the forest leans on this",
                                      title="What the forecaster actually uses"),
                        width="stretch")
        st.info("Humidity is the second most useful thing on that list, above the air "
                "temperature and far above the current body temperature.")

    elif s["id"] == "cost":
        st.latex(r"J = w_1 A_T + w_2 W + w_3 E + w_4 R + w_5 U")
        st.dataframe(pd.DataFrame([
            {"Term": "A_T  heat burden", "What it counts":
             "how far above 38.5 °C, squared, added up over the next five minutes",
             "Weight": story.W_BURDEN},
            {"Term": "W  water", "What it counts": "litres the setting would use",
             "Weight": story.W_WATER},
            {"Term": "E  energy", "What it counts": "watt-hours the setting would use",
             "Weight": story.W_ENERGY},
            {"Term": "R  risk", "What it counts":
             "minutes the supplies would fall short of the wait", "Weight": story.W_RISK},
            {"Term": "U  unsafe", "What it counts":
             "commands the safety layer would refuse", "Weight": story.W_UNSAFE},
        ]).set_index("Term"), width="stretch")
        runs, sc = get_runs(SC_KEY, which=["resource-aware AI"])
        st.plotly_chart(story.fig_j_terms(runs["resource-aware AI"]), width="stretch")
        st.info("The heat term is squared on purpose. Without that, in humid air the "
                "controller saves its water and lets the person sit above 40 °C.")

    elif s["id"] == "adaptive":
        runs, sc = get_runs(SC_KEY, which=["rule based", "predictive AI", "resource-aware AI",
                                           "maximum fixed"])
        st.plotly_chart(story.fig_runs(runs), width="stretch")
        st.plotly_chart(story.fig_resources(runs), width="stretch")
        st.dataframe(board_of(runs, sc).set_index("Controller"), width="stretch")
        st.dataframe(runs["resource-aware AI"][
            ["minute", "body", "body_est", "fan", "mist", "packs_active", "water_l",
             "battery_pct", "blocked"]].round(2).set_index("minute"), width="stretch")

    elif s["id"] == "board":
        runs, sc = get_runs(SC_KEY)
        board = board_of(runs, sc)
        st.dataframe(board.set_index("Controller"), width="stretch")
        st.plotly_chart(story.fig_board(board), width="stretch")
        st.plotly_chart(story.fig_runs(runs), width="stretch")

    elif s["id"] == "weather":
        c1, c2 = st.columns(2)
        for col, hum, label in ((c1, 0.32, "Dry heat · 32 % humidity"),
                                (c2, 0.78, "Humid heat · 78 % humidity")):
            runs, sc = get_runs(SC_KEY + (hum,), rh=hum)
            col.markdown(f"#### {label}")
            col.plotly_chart(story.fig_runs(runs, label), width="stretch")
            col.dataframe(board_of(runs, sc).set_index("Controller")[
                ["Change °C", "Minutes over 40 °C", "Water used L", "Battery left %"]],
                width="stretch")
        st.info("Same air temperature, same bench, same supplies. The controller spends its "
                "water very differently, because the air can only take a fifth as much.")

    elif s["id"] == "surprises":
        which = st.selectbox("What goes wrong", [
            "the pump fails after 4 minutes", "the fan fails after 5 minutes",
            "the battery starts at 25 %", "responders slip from 8 to 25 minutes",
            "the tank is half full and the wait is 25 minutes",
            "humidity jumps to 85 % after 6 minutes", "the person walks away after 8 minutes"])
        kw = {"the pump fails after 4 minutes": dict(pump_fail_at=4),
              "the fan fails after 5 minutes": dict(fan_fail_at=5),
              "the battery starts at 25 %": dict(battery_pct=25.0),
              "responders slip from 8 to 25 minutes": dict(eta=8.0, eta_extends_at=6,
                                                           eta_new=25.0),
              "the tank is half full and the wait is 25 minutes": dict(water_l=4.0, eta=25.0),
              "humidity jumps to 85 % after 6 minutes": dict(humidity_jump_at=6,
                                                             humidity_jump_to=0.85),
              "the person walks away after 8 minutes": dict(leaves_at=8)}[which]
        runs, sc = get_runs(SC_KEY + (which,), **kw)
        st.plotly_chart(story.fig_runs(runs, which), width="stretch")
        st.dataframe(board_of(runs, sc).set_index("Controller"), width="stretch")
        st.markdown("**What the safety layer stopped, for the resource-aware controller:**")
        reasons = pd.Series(runs["resource-aware AI"].attrs["reasons"])
        st.write(reasons.value_counts().to_dict() if len(reasons)
                 else "nothing — it never asked for anything it could not have")

    elif s["id"] == "limits":
        runs, sc = get_runs(SC_KEY, which=["resource-aware AI"])
        s_ai = story.score(runs["resource-aware AI"], sc)
        a, b, c = st.columns(3)
        a.metric("Radio minutes left at handover", s_ai["radio_min"])
        b.metric("Commands the limits refused", s_ai["blocked"])
        c.metric("Lowest simulated temperature", f"{s_ai['lowest']} °C")
        st.markdown("""
**The lines that do not move.**

- A person or a dispatcher switches the bench on. It never decides that somebody is ill.
- It never names a condition. "The surface reading is high" is as far as it goes.
- It never decides that professional help is unnecessary, and never cancels a call.
- Nothing generative writes an instruction. The screen shows pages a clinician approved.
- A dispatcher can take the screen, the fan and the mist at any moment, and that branch is
  checked before anything else.
- The radio's share of the battery is reserved before any cooling is allowed.
- Cooling stops at 38.5 °C, whatever the AI would prefer, because cooling too far is a new
  emergency.
- It never runs the fan when the fan would add heat, and never runs the pump dry.
- When it cannot see, it says so, rather than guessing.
""")
        st.warning("What it still gets wrong: the body model is one lump of warm water with a "
                   "fixed mass. It has no age, no clothing detail, no illness and no "
                   "medication. Every number in this project is a number about the simulation.")

    footer(s)
