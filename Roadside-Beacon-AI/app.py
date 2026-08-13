"""Roadside AI First-Response Beacon - the illustration app for the notebook.

One page per teaching step, routed by ?stage=<id>. The junction, the detectors
and the screen logic are the notebook's, trimmed to fit a 1 GB Streamlit Cloud
container: fewer clips, a smaller forest, and no TensorFlow.

Navigation is by button, never by markdown link: Streamlit renders every
markdown link with target="_blank", so a link would open a new browser tab on
every click.
"""
import numpy as np
import pandas as pd
import streamlit as st

import bridge
import story

st.set_page_config(page_title="Roadside AI First-Response Beacon", page_icon="🚨",
                   layout="wide")
st.markdown("""<style>
.stApp{background:#0e1117;color:#e6edf3}
.block-container{max-width:1200px}
.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}
.scene{color:#ffb74d}.ai{color:#4fc3f7}
.stButton button,div[data-testid="stButton"] button{background:transparent;border:1px solid #30363d;
    color:#e6edf3;justify-content:flex-start;text-align:left;font-weight:400}
.stButton button:hover,div[data-testid="stButton"] button:hover{border-color:#4fc3f7;color:#4fc3f7;
    background:#161b22}
</style>""", unsafe_allow_html=True)

DISCLAIMER = ("Educational simulation on invented traffic. Nothing here is a medical device or "
              "an emergency system, and no part of it may be used to decide real care.")

# --------------------------------------------------------------- controls
with st.sidebar:
    st.header("Beacon settings")
    wait = st.slider("Seconds the system waits before believing itself", 0, 5, 3,
                     help="The alarm must hold this long before anyone is called.")
    level = st.slider("How sure it has to be", 0.30, 0.90, 0.50, 0.05,
                      help="The probability at which the window model calls it an incident.")
    st.caption("Change either and every page below re-runs.")


@st.cache_data(show_spinner="Building the junction...")
def get_clips():
    frames, meta = story.build_clips(scale=3)
    return story.add_time_features(frames), meta


@st.cache_resource(show_spinner="Learning from old clips...")
def get_forest(train_ids_key):
    f, meta = get_clips()
    train = f[f["clip_id"].isin(get_split()[0])]
    return story.train_forest(train)


@st.cache_data
def get_split():
    _, meta = get_clips()
    return story.split_clips(meta)


@st.cache_data(show_spinner=False)
def get_risk():
    f, _ = get_clips()
    forest = get_forest("v1")
    return forest.predict_proba(f[story.WINDOW_FEATURES].to_numpy(np.float32))[:, 1]


@st.cache_data(show_spinner=False)
def get_curve(level):
    f, meta = get_clips()
    _, _, test = get_split()
    risk = get_risk()
    rows = []
    for w in range(0, 7):
        r = story.score_detector(f, story.confirm(risk >= level, f, w), meta, test)
        rows.append(dict(wait=w, seconds=r["seconds"], false_per_hour=r["false_per_hour"],
                         missed=r["missed"], caught=r["caught"]))
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def get_board(level, wait):
    f, meta = get_clips()
    _, _, test = get_split()
    risk = get_risk()
    rows = []
    for name, fire in (("1. One frame", story.alarm_single_frame(f)),
                       ("2. Six-second rule", story.alarm_rules(f)),
                       ("3. Window model", story.confirm(risk >= level, f, wait))):
        r = story.score_detector(f, fire, meta, test)
        rows.append({"Detector": name, "Incidents missed": r["missed"],
                     "Seconds lost": r["seconds"], "False alarms/hour": r["false_per_hour"],
                     "Quiet clips called in": f"{r['false_clips']} of {r['benign_clips']}"})
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def get_by_scenario(level, wait):
    f, meta = get_clips()
    _, _, test = get_split()
    risk = get_risk()
    test_set = set(test)
    fires = [("One frame", story.alarm_single_frame(f)),
             ("Six seconds", story.alarm_rules(f)),
             ("Window model", story.confirm(risk >= level, f, wait))]
    rows = []
    for kind, spec in story.SCENARIOS.items():
        clips = [c for c in meta.loc[meta["kind"] == kind, "clip_id"] if c in test_set]
        row = {"Clip": spec["tag"], "Real incident": "yes" if spec["incident"] else "no",
               "In the exam set": len(clips)}
        for name, fire in fires:
            r = story.score_detector(f, fire, meta, clips)
            row[name] = (f"missed {r['missed']}" if spec["incident"]
                         else f"called {r['false_clips']}")
        rows.append(row)
    return pd.DataFrame(rows)


f, meta = get_clips()
train_ids, tune_ids, test_ids = get_split()
risk = get_risk()
stage = st.query_params.get("stage", "start")


# --------------------------------------------------------------- page frame
def goto(target, label, key, where=None):
    """One step of navigation, inside this browser tab."""
    if (where or st).button(label, key=key, width="stretch"):
        st.query_params["stage"] = target
        st.rerun()


def header(s):
    p = bridge.PHASES[s["phase"]]
    st.markdown(
        f"<div class='hero'><small>PHASE {s['phase'] + 1} OF {len(bridge.PHASES)} · {p[0]}</small>"
        f"<h1>🚨 {s['scene']}</h1><h3><span class='scene'>{s['scene']}</span> → "
        f"<span class='ai'>{s['ai']}</span></h3></div>", unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.markdown("#### 1 · On the road")
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


def a_clip(kind):
    """One example clip of a given kind, from the exam pile where possible."""
    ids = meta.loc[meta["kind"] == kind, "clip_id"].to_numpy()
    for c in ids:
        if c in set(test_ids):
            return int(c)
    return int(ids[0])


# --------------------------------------------------------------- landing
if stage == "start":
    st.title("🚨 Roadside AI First-Response Beacon")
    st.warning(DISCLAIMER)
    st.markdown(
        "A camera on a pole watches a junction. Today it records crashes for the file. "
        "**This project asks what it should do in the four minutes before the ambulance "
        "arrives** — detect the crash, call it in, and turn the people already standing there "
        "into a response team.")

    board = get_board(level, wait)
    best = board.iloc[-1]
    a, b, c, d = st.columns(4)
    a.metric("Clips from the junction", len(meta))
    b.metric("Real incidents in them", int(meta["incident"].sum()))
    c.metric("Window model misses", f"{best['Incidents missed']} of "
             f"{int(meta.loc[meta['clip_id'].isin(test_ids), 'incident'].sum())}")
    d.metric("Seconds to the alarm", best["Seconds lost"])

    st.plotly_chart(story.fig_golden_minutes(), width="stretch")
    st.caption("The first minutes are the only ones a bystander can change.")

    st.subheader("The three detectors, at your settings")
    st.dataframe(board.set_index("Detector"), width="stretch")

    st.subheader("Learning journey")
    for i, s in enumerate(bridge.STEPS, 1):
        goto(s["id"], f"**{i}. {s['scene']}** — {s['ai']}", f"jump_{s['id']}")

    st.subheader("The notebook")
    st.markdown(
        "[Open the full teaching notebook in Colab]"
        "(https://colab.research.google.com/github/sanjula2003git/Corporate_training/blob/main/"
        "Roadside-Beacon-AI/Roadside_First_Response_Beacon.ipynb)")

else:
    s = bridge.BY_ID.get(stage, bridge.STEPS[0])
    header(s)

    # ----------------------------------------------------------- per stage
    if s["id"] == "golden":
        st.plotly_chart(story.fig_golden_minutes(), width="stretch")
        a, b, c = st.columns(3)
        a.metric("Typical ambulance, city", "8-12 min")
        b.metric("Minutes that matter most", "4")
        c.metric("People who saw it", "20+")
        st.info("The system never waits to be sure before calling for help. It calls, and "
                "says what it is unsure about.")

    elif s["id"] == "camera":
        st.plotly_chart(story.fig_scene(), width="stretch")
        st.markdown("**The ten numbers the camera produces, five times a second:**")
        st.dataframe(pd.DataFrame({
            "Signal": story.SIGNALS,
            "What it means": [
                "is anyone inside the carriageway", "is anyone lying down",
                "is that person still", "how many people are near them",
                "how many vehicles have stopped", "closest two tracks came, metres",
                "how fast they were closing, m/s", "hardest braking, m/s²",
                "smoke, 0 to 1", "average traffic speed, m/s"],
        }).set_index("Signal"), width="stretch")

    elif s["id"] == "lookalike":
        st.plotly_chart(story.fig_lookalikes(f, meta), width="stretch")
        st.caption("Every line above is a person lying in a road. Only two of them are hurt.")

    elif s["id"] == "clues":
        c1 = a_clip("collision_down")
        c2 = a_clip("worker")
        st.plotly_chart(story.fig_signals(f, c1, "A real crash"), width="stretch")
        st.plotly_chart(story.fig_signals(f, c2, "A mechanic under a van"), width="stretch")

    elif s["id"] in ("frame_rule", "timer_rule", "forest"):
        board = get_board(level, wait)
        st.dataframe(board.set_index("Detector"), width="stretch")
        st.plotly_chart(story.fig_detector_bars(board.to_dict("records")), width="stretch")
        st.markdown("**Clip by clip, on the exam pile**")
        st.dataframe(get_by_scenario(level, wait).set_index("Clip"), width="stretch")
        if s["id"] == "forest":
            forest = get_forest("v1")
            st.plotly_chart(story.fig_importance(forest), width="stretch")

    elif s["id"] == "sequence":
        st.info("This page explains the sequence network rather than training one. "
                "TensorFlow does not fit in the free container this app runs in — the "
                "notebook trains it in about five seconds.")
        st.markdown("""
Measured in the notebook, on the same exam clips, at a **3-second wait**:

| | Random forest, 11 window features | 1D CNN, raw 30 × 10 window |
|---|---|---|
| What it is given | eleven numbers we invented | the six seconds themselves |
| Incidents missed | 0 of 28 | 0 of 28 |
| Seconds to the alarm | **2.8** | 3.4 |
| False alarms per hour | 7.9 | **3.9** |
| Quiet clips called in | 4 of 76 | 2 of 76 |

Neither one wins. The forest is quicker off the mark; the network is calmer, and it was
told nothing about roads at all. At a 5-second wait the network starts missing incidents,
which the forest does not.

The difference that matters is not in this table: somebody had to *invent* `down_secs` and
`crowd_growth` for the forest. The network found what it needed by itself, from 160 clips.
""")

    elif s["id"] == "wait":
        curve = get_curve(level)
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_scatter(x=curve["wait"], y=curve["seconds"], name="seconds to the alarm",
                        line=dict(color=story.CYAN, width=3))
        fig.add_scatter(x=curve["wait"], y=curve["false_per_hour"], name="false alarms per hour",
                        line=dict(color=story.AMBER, width=3))
        fig.add_vline(x=wait, line_dash="dash", line_color="white",
                      annotation_text="your setting", annotation_font_color="white")
        st.plotly_chart(story._layout(fig, xaxis_title="seconds the system waits",
                                      yaxis_title="cost"), width="stretch")
        st.dataframe(curve.set_index("wait"), width="stretch")

    elif s["id"] == "mix":
        mix = pd.DataFrame([{"Clip": v["tag"], "Real incident": "yes" if v["incident"] else "no",
                             "Share of the pile": v["mix"]} for v in story.SCENARIOS.values()])
        st.dataframe(mix.set_index("Clip"), width="stretch")
        st.warning("Built with one red light for every crash, the model learned that stopped "
                   "traffic means a crash — and called the control centre at every signal "
                   "cycle. Nothing about the model was changed to fix it. The pile was.")

    elif s["id"] == "dispatch":
        st.code("""{
  "junction":      "NH-44 / Ring Road, camera 12",
  "location":      [17.4501, 78.3812],
  "time":          "20:42:07",
  "confidence":    0.91,
  "people_visible": 2,
  "person_down":   true,
  "smoke_or_fire": false,
  "lanes_blocked": ["east 1", "east 2"],
  "clip":          "20:41:52 - 20:42:07, faces blurred",
  "not_known":     ["is the rider breathing", "is anyone trapped"]
}""", language="json")
        st.info("What is deliberately not in the packet: any judgement about injuries, any "
                "unblurred face, and any delay while the AI makes up its mind.")

    elif s["id"] == "hazards":
        c1, c2 = st.columns(2)
        smoke = c1.checkbox("Smoke and spilled fuel", value=False)
        wire = c2.checkbox("A cable down across the road", value=False)
        cost = story.hazard_grid(smoke=smoke, wire=wire)
        st.plotly_chart(story.fig_hazard(cost, title="What it costs to stand here"),
                        width="stretch")
        a, b, c = st.columns(3)
        a.metric("Footpath", cost[7, 2])
        b.metric("The blocked crash lane", cost[2, 2])
        c.metric("The lane still moving", cost[5, 2])

    elif s["id"] == "path":
        cost = story.hazard_grid()
        helper_cell, victim_cell = (7, 2), (3, 10)
        path, total = story.plan_path(cost, helper_cell, victim_cell)
        naive = ([(j, helper_cell[1]) for j in range(helper_cell[0], victim_cell[0] - 1, -1)] +
                 [(victim_cell[0], i) for i in range(helper_cell[1] + 1, victim_cell[1] + 1)])
        naive_cost = float(sum(cost[c] for c in naive))
        st.plotly_chart(story.fig_hazard(cost, path, "The way in the screen shows"),
                        width="stretch")
        a, b = st.columns(2)
        a.metric("Straight to the casualty, across the live lane", round(naive_cost, 1))
        b.metric("Round by the signal, where the traffic is held", round(total, 1),
                 delta=f"{round(total - naive_cost, 1)} danger", delta_color="inverse")
        st.caption("The safe route is longer. It crosses where the signal is holding the "
                   "traffic, which is what a traffic officer would tell you to do.")

    elif s["id"] == "modules":
        st.markdown("**Tick what the scene and the dispatcher say, and watch the screen choose.**")
        c1, c2, c3 = st.columns(3)
        scene = dict(
            smoke=c1.checkbox("Smoke or fuel"),
            live_traffic=c1.checkbox("Traffic still moving", value=True),
            wire=c1.checkbox("Fallen cable"),
            trapped=c2.checkbox("Person trapped"),
            vehicle_unstable=c2.checkbox("Vehicle unstable"),
            helmet=c2.checkbox("Helmet on the rider", value=True),
            severe_bleeding_confirmed=c3.checkbox("Dispatcher confirms bleeding"),
            unresponsive_confirmed_by_dispatch=c3.checkbox("Dispatcher confirms no response"),
            dispatcher_override=c3.checkbox("Dispatcher takes the screen"),
        )
        mod, why = story.choose_module(scene)
        st.subheader(story.MODULES[mod])
        st.caption(why)
        st.info("Every branch returns the name of a pre-approved video. The AI chooses between "
                "them. It never writes one.")

    elif s["id"] == "helper":
        st.markdown("**What the camera thinks it can see right now:**")
        c1, c2 = st.columns(2)
        obs = {}
        for i, (key, seen, _) in enumerate(story.CHECKS):
            obs[key] = (c1 if i % 2 == 0 else c2).checkbox(seen, key=f"chk_{key}")
        for v in story.check_helper(obs):
            {"red": st.error, "amber": st.warning, "green": st.success}[v["colour"]](
                f"**{v['colour'].upper()}** — {v['message']}")
        st.info("Compression depth and how hard someone is pressing are missing from that list "
                "on purpose. A camera cannot measure either. Those need an instrumented mat.")

    elif s["id"] == "roles":
        people = [dict(name="Red jacket", x=8.0, y=17.0), dict(name="Scooter rider", x=22.0, y=16.0),
                  dict(name="Shopkeeper", x=5.0, y=18.0), dict(name="Bus passenger", x=40.0, y=15.0),
                  dict(name="Cyclist", x=52.0, y=17.0)]
        st.dataframe(story.assign_roles(people).set_index("job"), width="stretch")
        st.caption("Distance decides. The nearest able person gets the most urgent job.")

    elif s["id"] == "outcome":
        curve = get_curve(level)
        secs = float(curve.loc[curve["wait"] == wait, "seconds"].iloc[0])
        table = story.outcome_table(secs)
        st.dataframe(table.set_index("What we measure"), width="stretch")
        st.plotly_chart(story.fig_outcome(table), width="stretch")
        st.warning("The 'no beacon' delays are this teaching model's assumptions, not "
                   "measurements. The detection time is measured; everything after it is not.")

    elif s["id"] == "limits":
        _, _, test = get_split()
        occl = [c for c in meta.loc[meta["kind"] == "occluded", "clip_id"] if c in set(test)]
        r = story.score_detector(f, story.confirm(risk >= level, f, wait), meta, occl)
        st.metric("Seconds to the alarm when a bus hides the crash", r["seconds"])
        st.markdown("""
**The lines that do not move.**

- It calls the control centre immediately. It never waits for the AI to be certain.
- It never names an injury. "Not visibly responding" is as far as it goes.
- A dispatcher can take the screen, the camera and the speaker at any moment.
- Nothing generative writes a medical instruction. The AI only picks between approved videos.
- It never routes a helper across live traffic.
- It works with the network down, and it blurs faces that are not involved.
- It is tested with mannequins before it is tested with people.
""")

    footer(s)
