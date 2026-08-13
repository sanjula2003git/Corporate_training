"""Hospital Alarm-Fatigue Manager - the illustration app for the notebook.

One page per teaching step, routed by ?stage=<id>. The ward, the models and the
five actions are the notebook's, trimmed to fit a 1 GB Streamlit Cloud container.
"""
import numpy as np
import pandas as pd
import streamlit as st

import bridge
import story

st.set_page_config(page_title="Hospital Alarm-Fatigue Manager", page_icon="🏥", layout="wide")
st.markdown("""<style>
.stApp{background:#0e1117;color:#e6edf3}
.block-container{max-width:1200px}
.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}
.ward{color:#ffb74d}.ai{color:#4fc3f7}
/* the navigation buttons, dressed as list rows rather than form buttons */
.stButton button,div[data-testid="stButton"] button{background:transparent;border:1px solid #30363d;
    color:#e6edf3;justify-content:flex-start;text-align:left;font-weight:400}
.stButton button:hover,div[data-testid="stButton"] button:hover{border-color:#4fc3f7;color:#4fc3f7;
    background:#161b22}
</style>""", unsafe_allow_html=True)


# --------------------------------------------------------------- controls
with st.sidebar:
    st.header("Ward settings")
    budget = st.slider("Alerts allowed per hour", 1, 15, 5,
                       help="The whole ward, not per patient.")
    n_nurses = st.slider("Nurses on shift", 1, 4, 2,
                         help="Each has 60 minutes of attention per hour.")
    glitches = st.slider("Sensor glitches per patient per day", 4, 40, 26,
                         help="Slipped probes, movement, loose leads.")
    st.caption("Change any of these and every page below re-runs.")


@st.cache_data(show_spinner="Building the ward...")
def get_ward(glitches):
    return story.build_ward(glitches=glitches)


@st.cache_resource(show_spinner="Training the forest...")
def get_forest(glitches):
    return story.train_forest(get_ward(glitches))


@st.cache_data(show_spinner="Running the ward...")
def get_run(glitches, budget, n_nurses):
    ward = get_ward(glitches)
    forest = get_forest(glitches)

    tune = ward[ward.day.isin(story.TUNE_DAYS)].reset_index(drop=True)
    test = ward[ward.day.isin(story.TEST_DAYS)].reset_index(drop=True)
    for frame in (tune, test):
        frame["risk_rf"] = forest.predict_proba(frame[story.FEATURES].to_numpy(np.float32))[:, 1]
    test["score"] = story.risk_score(test)
    test["score01"] = test["score"] / 20.0

    events = story.event_table(ward, story.TEST_DAYS)
    tune_events = story.event_table(ward, story.TUNE_DAYS)
    hours = len(story.TEST_DAYS) * 24
    tune_hours = len(story.TUNE_DAYS) * 24

    levels = story.levels_from_tuning(tune, tune_hours, budget)
    rf_level = story.pick_sensitive_level(tune, "risk_rf", tune_events, catch=0.75)

    alerts = {}
    alerts["1. Simple limits"] = story.to_alerts(test, story.breaks_limits(test))
    a2 = story.to_alerts(test, (test["score"] >= 5).to_numpy())
    if len(a2):
        a2.loc[test["score"].to_numpy()[a2["row"].to_numpy()] >= 7, "action"] = "urgent"
    alerts["2. Risk score"] = a2
    alerts["3. Random forest"] = story.to_alerts(test, (test["risk_rf"] >= rf_level).to_numpy())

    decisions = story.run_manager(test, levels, budget)
    alerts["5. Attention budget"] = (decisions[decisions.action.isin(["notify", "urgent"])]
                                     .reset_index(drop=True))

    board = pd.DataFrame([story.score(k, v, test, events, hours, n_nurses)
                          for k, v in alerts.items()])
    return dict(ward=ward, test=test, events=events, hours=hours, levels=levels,
                rf_level=rf_level, alerts=alerts, decisions=decisions, board=board)


ward = get_ward(glitches)
forest = get_forest(glitches)
run = get_run(glitches, budget, n_nurses)
test, events, board = run["test"], run["events"], run["board"]
stage = st.query_params.get("stage", "start")

DISCLAIMER = ("Educational simulation on invented patients. Nothing here is a medical device, and no "
              "part of it may be used to decide the care of a real person.")


def header(s):
    p = bridge.PHASES[s["phase"]]
    st.markdown(
        f"<div class='hero'><small>PHASE {s['phase'] + 1} OF {len(bridge.PHASES)} · {p[0]}</small>"
        f"<h1>🏥 {s['ward']}</h1><h3><span class='ward'>{s['ward']}</span> → "
        f"<span class='ai'>{s['ai']}</span></h3></div>", unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.markdown("#### 1 · On the ward")
    a.write(s["site"])
    b.markdown("#### 2 · Why it is hard")
    b.write(s["challenge"])
    c.markdown("#### 3 · Where the AI comes in")
    c.write(s["ai_link"])
    st.markdown(f"#### 4 · What it looks like — `{s['tech']}`")


def goto(target, label, key, where=None):
    """One step of navigation, inside this browser tab.

    Never a link. Streamlit renders every markdown link with target="_blank",
    so [text](?stage=x) opened a fresh tab on each click and a student walking
    the fifteen steps finished with fifteen tabs. A button reruns the script in
    place; the query parameter is still written, so the URL stays shareable and
    the notebook's deep links keep working.
    """
    if (where or st).button(label, key=key, width="stretch"):
        st.query_params["stage"] = target
        st.rerun()


def footer(s):
    st.markdown("#### 5 · In the notebook")
    st.write(s["notebook"])
    st.success(s["takeaway"])
    i = bridge.ORDER.index(s["id"])
    cols = st.columns(3)
    if i:
        goto(bridge.ORDER[i - 1], f"◀ {bridge.STEPS[i - 1]['ward']}", f"prev_{s['id']}", cols[0])
    goto("start", "Overview", f"home_{s['id']}", cols[1])
    if i < len(bridge.STEPS) - 1:
        goto(bridge.ORDER[i + 1], f"{bridge.STEPS[i + 1]['ward']} ▶", f"next_{s['id']}", cols[2])


def scoreboard_table():
    st.dataframe(board.set_index("Model"), use_container_width=True)


# --------------------------------------------------------------- landing
if stage == "start":
    st.title("🏥 Hospital Alarm-Fatigue Manager")
    st.warning(DISCLAIMER)
    st.markdown(
        "A nurse has a limited amount of attention. We may interrupt that nurse "
        f"**{budget} times an hour** for the whole ward. **Which {budget}?**  \n"
        "That question — not predicting who gets sick — is what this app is about.")

    best = board.sort_values(["Nurse arrived in time", "Early warning (min)"],
                             ascending=False).iloc[0]
    a, b, c, d = st.columns(4)
    a.metric("Patients on the ward", story.N_PATIENTS)
    b.metric("Deteriorations to catch", len(events))
    c.metric("Alerts allowed per hour", budget)
    d.metric("Best method reaches", f"{int(best['Nurse arrived in time'])} of {len(events)}",
             help=f"{best['Model']}")

    st.plotly_chart(story.fig_fatigue(), use_container_width=True)
    st.caption("Being louder does not create more emergencies. It only buries the ones you have.")

    st.subheader("The scoreboard, at your current settings")
    scoreboard_table()

    st.subheader("Learning journey")
    for i, s in enumerate(bridge.STEPS, 1):
        goto(s["id"], f"**{i}. {s['ward']}** — {s['ai']}", f"jump_{s['id']}")

    st.subheader("The notebook")
    st.markdown(
        "[Open the full teaching notebook in Colab]"
        "(https://colab.research.google.com/github/sanjula2003git/Corporate_training/blob/main/"
        "Hospital-Alarm-Fatigue-AI/Hospital_Alarm_Fatigue_Manager.ipynb)")

else:
    s = bridge.BY_ID.get(stage, bridge.STEPS[0])
    header(s)

    if s["id"] == "flood":
        st.plotly_chart(story.fig_fatigue(), use_container_width=True)
        lim = board[board.Model == "1. Simple limits"].iloc[0]
        a, b, c = st.columns(3)
        a.metric("Alerts an hour from fixed limits", lim["Alerts/hr"])
        b.metric("Of those, false alarms", int(lim["False alarms"]))
        c.metric("Nurse minutes needed per hour", lim["Nurse min/hr"],
                 delta=f"{lim['Nurse min/hr'] - 60 * n_nurses:+.0f} vs available",
                 delta_color="inverse")

    elif s["id"] == "ward":
        quiet = (ward.groupby(["patient", "day"])
                 .agg(trouble=("trouble", "max"), art=("artifact", "sum")).reset_index())
        calm = quiet[quiet.trouble == 0].sort_values("art").iloc[0]
        st.plotly_chart(story.fig_patient_day(ward, int(calm.patient), int(calm.day),
                                              f"Patient {int(calm.patient)} — an ordinary day"),
                        use_container_width=True)
        st.markdown("**Every spike here is a sensor, not a patient.**")
        st.dataframe(ward[["patient", "chronic"]].drop_duplicates()
                     .rename(columns={"chronic": "lives near a limit"})
                     .set_index("patient").T, use_container_width=True)

    elif s["id"] == "noise":
        ev = events.iloc[0]
        st.plotly_chart(story.fig_patient_day(ward, int(ev.patient), int(ev.day),
                                              f"Patient {int(ev.patient)} — real deterioration ({ev.kind})"),
                        use_container_width=True)
        st.plotly_chart(story.fig_noise_vs_illness(test), use_container_width=True)
        st.markdown("During real deterioration several signals move together and **sensor quality stays "
                    "high**. During a glitch the numbers are extreme but **quality collapses**, and the "
                    "other measurements do not agree.")

    elif s["id"] == "actions":
        st.dataframe(pd.DataFrame([
            dict(Action=a["label"], **{"Nurse minutes": a["nurse_minutes"],
                                       "Uses the budget": "yes" if a["alerts"] else "no"})
            for a in story.ACTIONS.values()]).set_index("Action"), use_container_width=True)
        counts = run["decisions"].action.value_counts()
        st.markdown("#### What the manager actually chose, across every reading")
        st.dataframe(counts.rename("times chosen").to_frame().T, use_container_width=True)
        st.info("Three of the five cost nobody anything. That is what makes the budget survivable.")

    elif s["id"] == "budget":
        readings = story.N_PATIENTS * 60 // story.DT
        a, b, c = st.columns(3)
        a.metric("Readings per hour", readings)
        b.metric("Alerts allowed", budget)
        c.metric("Nurse minutes available", 60 * n_nurses)
        st.markdown(
            f"`{budget} alerts × 8 minutes = {budget * 8} minutes` of the "
            f"`{60 * n_nurses}` a shift of {n_nurses} has. "
            f"That is **{100 * budget * 8 / (60 * n_nurses):.0f}%** of the ward's staff time, "
            "before anything else on the ward gets done.")
        st.plotly_chart(story.fig_bucket(run["alerts"]["5. Attention budget"], test, budget),
                        use_container_width=True)

    elif s["id"] == "limits":
        rows = run["alerts"]["1. Simple limits"]["row"].to_numpy()
        if len(rows):
            trouble = test["trouble"].to_numpy()[rows] == 1
            art = (test["artifact"].to_numpy()[rows] == 1) & ~trouble
            chron = (test["chronic"].to_numpy()[rows] != "") & ~art & ~trouble
            med = (test["mins_since_med"].to_numpy()[rows] < 60) & ~art & ~trouble & ~chron
            st.plotly_chart(story.fig_alarm_sources({
                "Real deterioration": int(trouble.sum()),
                "Sensor glitch": int(art.sum()),
                "A patient who always looks like this": int(chron.sum()),
                "Just after a medicine": int(med.sum()),
                "Everything else": int((~trouble & ~art & ~chron & ~med).sum()),
            }), use_container_width=True)
        st.dataframe(board[board.Model == "1. Simple limits"].set_index("Model"),
                     use_container_width=True)

    elif s["id"] == "score":
        st.dataframe(board[board.Model.isin(["1. Simple limits", "2. Risk score"])].set_index("Model"),
                     use_container_width=True)
        st.markdown("The score buys quiet by demanding that several measurements agree — and pays for it "
                    "in timing, because points only arrive once a number is already clearly abnormal.")

    elif s["id"] == "clues":
        st.plotly_chart(story.fig_importance(forest), use_container_width=True)
        st.markdown("The clues at the top are mostly **distance from this patient's own normal** and "
                    "**direction of travel** — not the raw readings a fixed limit looks at.")

    elif s["id"] == "forest":
        st.metric("Alert level chosen on the dial-setting day", f"{run['rf_level']:.3f}")
        st.dataframe(board[board.Model.isin(["2. Risk score", "3. Random forest"])].set_index("Model"),
                     use_container_width=True)
        st.markdown("Almost everything the forest says is worth hearing. But a level chosen once, on one "
                    "day, is **wrong in both directions**: too high on a quiet night, too low on a bad "
                    "one. Move the sidebar sliders and watch it fail in each direction.")

    elif s["id"] == "sequence":
        xs = np.linspace(-6, 6, 200)
        import plotly.graph_objects as go
        fig = go.Figure(go.Scatter(x=xs, y=1 / (1 + np.exp(-xs)), line=dict(color=story.VIOLET, width=3)))
        st.plotly_chart(story._layout(fig, height=300, title="The squash: any number in, 0 to 1 out",
                                      xaxis_title="weighted sum", yaxis_title="risk"),
                        use_container_width=True)
        st.markdown(
            "A neuron multiplies each input by a weight, adds them up, and squashes the result to a "
            "number between 0 and 1. An **LSTM** does that repeatedly along an hour of readings, keeping "
            "a small memory and learning what to forget — a two-minute spike gets dropped, a slow lean "
            "gets kept.\n\n"
            "**Model 4 is the one model this app does not run.** The notebook trains it; here TensorFlow "
            "would not fit in a free Streamlit container. That is why the scoreboard jumps from 3 to 5. "
            "No great loss: the honest result in the notebook was that the forest ranks patients better "
            "than the LSTM on this problem anyway.")

    elif s["id"] == "ranking":
        st.plotly_chart(story.fig_budget_curve(test, events, run["hours"], budget),
                        use_container_width=True)
        st.markdown("Read only the budget line, and read upward. The gap between the curves **there** is "
                    "the real value of a better model.\n\n"
                    "One catch: this chart picks each level using the exam days themselves. In real life "
                    "you do not get that hindsight — which is exactly why a fixed level disappoints.")

    elif s["id"] == "manager":
        a, b, c, d, e = st.columns(5)
        for col, key, label in ((a, "watch", "repeat above"), (b, "easy", "notify (bucket full)"),
                                (c, "normal", "notify (normal)"), (d, "strict", "notify (nearly out)"),
                                (e, "urgent", "urgent above")):
            col.metric(label, f"{run['levels'][key]:.3f}")
        st.plotly_chart(story.fig_bucket(run["alerts"]["5. Attention budget"], test, budget),
                        use_container_width=True)
        scoreboard_table()
        st.info("Models 3 and 4 use the identical forest and the identical risk numbers. Only the "
                "decision changed.")

    elif s["id"] == "patient":
        caught = [e for e in events.itertuples()
                  if len(run["alerts"]["5. Attention budget"].query(
                      "patient == @e.patient and minute >= @e.start and minute <= @e.crisis"))]
        if caught:
            ev = st.selectbox("Which patient?", caught,
                              format_func=lambda e: f"Patient {e.patient}, day {e.day} — {e.kind}")
            st.plotly_chart(story.fig_patient_trace(test, run["decisions"], ev, run["levels"]),
                            use_container_width=True)
            st.caption("Blue dots are free re-checks that interrupt nobody. Orange is a nurse being "
                       "told. A star is the emergency team, which ignores the budget.")
        else:
            st.warning("At these settings the manager caught no event on the exam days. "
                       "Raise the alert budget in the sidebar.")

    elif s["id"] == "nurses":
        st.dataframe(board.set_index("Model")[["Alerts/hr", "Nurse min/hr", "Response (min)",
                                               "Nurse arrived in time"]], use_container_width=True)
        st.markdown(
            f"{n_nurses} nurse(s) have **{60 * n_nurses} minutes** of attention per hour. Any method "
            "asking for more than that builds a queue it can never clear — and the alerts that were "
            "right end up waiting behind the ones that were not.\n\n"
            "**Nurse arrived in time** counts deteriorations where somebody physically reached the "
            "bedside before the crisis. It is the only column a patient would recognise as mattering.")

    elif s["id"] == "scoreboard":
        st.plotly_chart(story.fig_scoreboard(board, budget, len(events)), use_container_width=True)
        scoreboard_table()
        st.markdown(
            "**What it still gets wrong.** The ward is invented, and every number is a statement about "
            "the simulator rather than about a hospital. The budget is a real cost that somebody pays. "
            "Patterns that appear twice a year will not be learned, which is why the fixed limits stay "
            "switched on underneath. And the system only chooses *who to tell* — a nurse who is worried "
            "should always win an argument with it.")
        st.warning(DISCLAIMER)

    footer(s)
