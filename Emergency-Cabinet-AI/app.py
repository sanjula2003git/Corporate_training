"""One Door Opens - the illustration app for the emergency-cabinet notebook.

One page per teaching step, routed by ?stage=<id>. The cabinet, the models and
the safety checks are the notebook's, with the same seeds, so at the default
sidebar settings the numbers match.

Navigation is by button, never by markdown link: Streamlit renders every
markdown link with target="_blank", so a link would open a new browser tab on
every click.
"""
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.model_selection import train_test_split

import bridge
import story

st.set_page_config(page_title="One Door Opens", page_icon="🧰", layout="wide")
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

DISCLAIMER = ("Educational simulation on invented emergencies. Nothing here is a medical device, "
              "and no part of it may be used to decide what happens to a real person.")


# --------------------------------------------------------------- controls
with st.sidebar:
    st.header("The call")
    incident = st.selectbox("What was reported", story.INCIDENTS, index=0)
    bleeding = st.checkbox("Bleeding mentioned", value=True)
    fire = st.checkbox("Fire", value=False)
    water = st.checkbox("Water", value=False)
    traffic = st.checkbox("Traffic hazard", value=True)
    responsive = st.selectbox("Is the person responding?", ["yes", "no", "unknown"], index=2)
    people = st.slider("People affected", 1, 4, 1)
    dispatcher = st.checkbox("Dispatcher has confirmed", value=True)

    st.header("The cabinet")
    fill = st.slider("How full the shelves are", 0.1, 1.0, 1.0, 0.1)
    st.caption("Change anything here and every page below re-runs.")

REPORT = dict(incident=incident, reported_bleeding=int(bleeding), fire_present=int(fire),
              water_incident=int(water), traffic_hazard=int(traffic), people_affected=people,
              person_responsive=responsive, dispatcher_confirmed=int(dispatcher))


@st.cache_data(show_spinner="Making up four thousand emergencies...")
def get_cases():
    return story.make_cases()


@st.cache_resource(show_spinner="Learning from past calls...")
def get_model():
    reports, answers = get_cases()
    X = story.to_numbers(reports)[story.FEATURES]
    X_train, X_test, Y_train, Y_test = train_test_split(
        X, answers[story.MODELLED], test_size=0.30, random_state=42)
    return story.train_forest(X_train, Y_train), X_train.index, X_test.index


@st.cache_data(show_spinner=False)
def get_scores():
    reports, answers = get_cases()
    model, _, test_index = get_model()
    X = story.to_numbers(reports)[story.FEATURES]

    test_reports = reports.loc[test_index]
    test_answers = answers.loc[test_index]
    rules = np.array([[story.rule_cabinet(r)[c] for c in story.COMPARTMENTS]
                      for r in test_reports.to_dict("records")])

    predicted = pd.DataFrame(model.predict(X.loc[test_index]),
                             columns=story.MODELLED, index=test_index)
    for name in story.ALWAYS_OPEN:
        predicted[name] = 1
    model_opened = predicted[story.COMPARTMENTS].to_numpy()

    board = pd.DataFrame([story.score_system(rules, test_answers, "Rules"),
                          story.score_system(model_opened, test_answers, "Random forest")])
    return board, rules, model_opened, test_answers


@st.cache_data(show_spinner="Running a whole day, four times over...")
def get_days():
    _, answers = get_cases()
    model, _, _ = get_model()
    share = answers.mean().to_dict()
    fills = [1.0, 0.7, 0.5, 0.3]
    return {(s, f): story.run_day(s, model, share, fill=f)
            for s, _ in story.STRATEGIES for f in fills}, fills


@st.cache_data(show_spinner=False)
def get_anomaly():
    return story.build_anomaly()


reports, answers = get_cases()
model, _, _ = get_model()
cabinet = story.fresh_cabinet(fill=fill)
neighbour = {"burns", "flotation"}
chances, states, notes, restock = story.cabinet_decides(REPORT, cabinet, model, neighbour)
stage = st.query_params.get("stage", "start")


# --------------------------------------------------------------- page frame
def goto(target, label, key, where=None):
    """One step of navigation, inside this browser tab."""
    if (where or st).button(label, key=key, width="stretch"):
        st.query_params["stage"] = target
        st.rerun()


def header(step):
    phase = bridge.PHASES[step["phase"]]
    st.markdown(
        f"<div class='hero'><small>PHASE {step['phase'] + 1} OF {len(bridge.PHASES)} · "
        f"{phase[0]}</small><h1>🧰 {step['scene']}</h1>"
        f"<h3><span class='scene'>{step['scene']}</span> → "
        f"<span class='ai'>{step['ai']}</span></h3></div>", unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.markdown("#### 1 · At the cabinet")
    a.write(step["site"])
    b.markdown("#### 2 · Why it is hard")
    b.write(step["challenge"])
    c.markdown("#### 3 · Where the AI comes in")
    c.write(step["ai_link"])
    if step.get("plain"):
        st.info(f"**In plain words.** {step['plain']}")
    st.markdown(f"#### 4 · What it looks like — `{step['tech']}`")


def report_feature_tables():
    """Every column the model is given, in words a first-time reader can read.

    Rendered open rather than behind collapsed expanders: on this page the list
    IS the lesson, and a student who has to click four times to find out what
    `person_responsive_unknown` means will simply not click.
    """
    st.markdown(f"#### All {bridge.REPORT_FEATURE_COUNT} columns the model is given")
    st.caption("Every one of them describes what the caller SAID, never what was true. "
               "The model never sees the right answer at the moment it has to decide.")
    for g in bridge.REPORT_FEATURE_GROUPS:
        st.markdown(f"##### {g['name']}  ·  {len(g['rows'])} column"
                    f"{'s' if len(g['rows']) > 1 else ''}")
        a, b = st.columns(2)
        a.markdown(f"**What it is.** {g['idea']}")
        b.markdown(f"**What we do with it.** {g['plan']}")
        st.dataframe(pd.DataFrame(g["rows"],
                                  columns=["Column", "What it is", "What it is for"]
                                  ).set_index("Column"), width="stretch")


def footer(step):
    st.markdown("#### 5 · In the notebook")
    st.write(step["notebook"])
    st.success(step["takeaway"])
    i = bridge.ORDER.index(step["id"])
    cols = st.columns(3)
    if i:
        goto(bridge.ORDER[i - 1], f"◀ {bridge.STEPS[i - 1]['scene']}", f"prev_{step['id']}",
             cols[0])
    goto("start", "Overview", f"home_{step['id']}", cols[1])
    if i < len(bridge.STEPS) - 1:
        goto(bridge.ORDER[i + 1], f"{bridge.STEPS[i + 1]['scene']} ▶", f"next_{step['id']}",
             cols[2])


def show_doors(caption=True):
    st.plotly_chart(story.fig_doors(states, chances, notes), width="stretch")
    if caption:
        st.caption("Green opens · amber is waiting for a person · red stays shut · "
                   "grey has nothing usable · blue means the next cabinet has one. "
                   "Hover a door for the reason.")


def decision_table():
    rows = [{"Compartment": story.NAMES[c], "Door": states[c],
             "Chance it is needed": round(chances[c], 2), "Why": notes[c]}
            for c in story.COMPARTMENTS]
    st.dataframe(pd.DataFrame(rows).set_index("Compartment"), width="stretch")


# --------------------------------------------------------------- landing
if stage == "start":
    st.title("🧰 One Door Opens")
    st.warning(DISCLAIMER)
    st.markdown(
        "An emergency cabinet has seven locked compartments. This app is the part that decides "
        "**which ones to unlock**, using what is known about the emergency and what is left in "
        "the cabinet.\n\n"
        "It never decides what treatment anybody needs. It chooses which supplies to hand over, "
        "and a set of fixed safety checks always gets the last word.")

    show_doors()

    board, _, _, _ = get_scores()
    a, b, c, d = st.columns(4)
    a.metric("Doors opening now", sum(1 for s in states.values() if s == story.UNLOCKED))
    a_wait = sum(1 for s in states.values() if s == story.WAITING)
    b.metric("Waiting for a person", a_wait)
    c.metric("Rules miss", int(board.iloc[0]["Missed items"]),
             help="Items that were needed and stayed shut, on 1200 unseen emergencies.")
    d.metric("The model misses", int(board.iloc[1]["Missed items"]),
             delta=int(board.iloc[1]["Missed items"] - board.iloc[0]["Missed items"]),
             delta_color="inverse")

    st.subheader("The two systems, on the same unseen emergencies")
    st.dataframe(board.set_index("System"), width="stretch")

    st.subheader("Learning journey")
    for i, step in enumerate(bridge.STEPS, 1):
        goto(step["id"], f"**{i}. {step['scene']}** — {step['ai']}", f"jump_{step['id']}")

    st.subheader("The notebook")
    st.markdown(
        "[Open the full teaching notebook in Colab]"
        "(https://colab.research.google.com/github/sanjula2003git/Corporate_training/blob/main/"
        "Emergency-Cabinet-AI/One_Door_Opens_Emergency_Cabinet.ipynb)")

else:
    step = bridge.BY_ID.get(stage, bridge.STEPS[0])
    header(step)

    if step["id"] == "door":
        show_doors()
        st.markdown(
            "Every door above is a decision. A person standing in front of the cabinet has to "
            "make all seven, by reading small labels, in a situation they have never been in.\n\n"
            "The most common mistake is not the one people expect. It is not opening the wrong "
            "door — it is **taking what was said out loud** rather than what is needed. If "
            "nobody said the word *gloves*, nobody takes gloves.")
        a, b = st.columns(2)
        a.metric("Doors to read", len(story.COMPARTMENTS))
        b.metric("Possible combinations", 2 ** len(story.COMPARTMENTS))

    elif step["id"] == "inventory":
        table = pd.DataFrame(cabinet).T
        table.index = [story.NAMES[i] for i in table.index]
        st.dataframe(table, width="stretch")
        unusable = [story.NAMES[c] for c in story.COMPARTMENTS if not story.usable(cabinet[c])]
        if unusable:
            st.error("Nothing usable in: " + ", ".join(unusable))
        else:
            st.info("Everything on the shelves is usable at this stock level. "
                    "Turn the stock slider down and watch that change.")
        st.markdown(
            "Three kinds of thing live in this cabinet, and mixing them up breaks the maths "
            "later:\n\n"
            "- **Used up** — gloves, dressings, burn supplies. Once handed over they are gone.\n"
            "- **Comes back** — traffic markers, the float, the defibrillator.\n"
            "- **Never leaves** — the communication unit is bolted in.")

    elif step["id"] == "report":
        st.plotly_chart(story.fig_needed(answers), width="stretch")
        st.markdown(
            "The right-hand chart is the one that decides what kind of model we need. **Almost "
            "no emergency needs only one compartment.** So the question is never *which one is "
            "this* — it is *which of these seven, all at once*.")
        rng = np.random.default_rng(3)
        rows = []
        for _ in range(2000):
            truth = story.make_truth(rng)
            rep = story.make_report(truth, rng)
            rows.append({
                "responsiveness not known": rep["person_responsive"] == "unknown",
                "traffic hazard not mentioned": bool(truth["traffic"]) and not rep["traffic_hazard"],
                "called unclear": rep["incident"] == "unclear" and truth["incident"] != "unclear",
                "bleeding reported wrongly": rep["reported_bleeding"] != truth["bleeding"],
                "no dispatcher yet": rep["dispatcher_confirmed"] == 0})
        st.markdown("#### How often the report does not match what is really happening")
        st.dataframe((pd.DataFrame(rows).mean() * 100).round(1)
                     .rename("% of calls").to_frame().T, width="stretch")
        st.info("Read that row again before moving on. None of these are bugs — they are what "
                "frightened people on a phone actually sound like, and the model has to be "
                "useful anyway.")
        st.divider()
        report_feature_tables()

    elif step["id"] == "rules":
        opened = [story.NAMES[c] for c, v in story.rule_cabinet(REPORT).items() if v]
        st.markdown("**On the call in the sidebar, the rulebook opens:** " + ", ".join(opened))
        board, rules_opened, model_opened, test_answers = get_scores()
        st.plotly_chart(story.fig_misses(rules_opened, model_opened, test_answers),
                        width="stretch")
        st.markdown(
            "Look at the red bars. On some compartments the rules are **perfect** — nothing "
            "missed at all. On others they fall apart.\n\n"
            "The rules are all the same shape, so the difference is not the rule. It is **how "
            "reliable the report is** for that particular thing. Where the caller says something "
            "clearly, a plain rule cannot be beaten. Where they say *I don't know*, the rule has "
            "nothing to work with.")

    elif step["id"] == "breaks":
        awkward = {
            "Bleeding, and standing in the road": dict(
                incident="road_accident", reported_bleeding=1, fire_present=0, water_incident=0,
                traffic_hazard=1, people_affected=1, person_responsive="yes",
                dispatcher_confirmed=1),
            "A burn, with an empty burn shelf": dict(
                incident="fire", reported_bleeding=0, fire_present=1, water_incident=0,
                traffic_hazard=0, people_affected=1, person_responsive="yes",
                dispatcher_confirmed=1),
            "Collapsed, nobody has confirmed anything": dict(
                incident="unclear", reported_bleeding=0, fire_present=0, water_incident=0,
                traffic_hazard=0, people_affected=1, person_responsive="unknown",
                dispatcher_confirmed=0),
            "The button was pressed by mistake": dict(
                incident="unclear", reported_bleeding=0, fire_present=0, water_incident=0,
                traffic_hazard=0, people_affected=1, person_responsive="yes",
                dispatcher_confirmed=0),
        }
        rows = []
        for title, rep in awkward.items():
            rows.append({"The call": title,
                         "The rulebook opens": ", ".join(
                             story.NAMES[c] for c, v in story.rule_cabinet(rep).items() if v)})
        st.dataframe(pd.DataFrame(rows).set_index("The call"), width="stretch")

        st.markdown("#### The one that matters: `unknown` is not `no`")
        rows = []
        for state in ["yes", "no", "unknown"]:
            rep = dict(REPORT, person_responsive=state)
            rows.append({"Is the person responding?": state,
                         "The rulebook": "opens the AED" if story.rule_cabinet(rep)["aed"]
                                         else "leaves it shut"})
        st.dataframe(pd.DataFrame(rows).set_index("Is the person responding?"),
                     width="stretch")
        st.error("`unknown` and `no` get the same treatment, and they should not. Not knowing "
                 "whether somebody is breathing is not the same as knowing they are fine.")

    elif step["id"] == "model":
        st.markdown("#### What the model says about the call in the sidebar")
        ranked = pd.Series(chances).sort_values(ascending=False)
        st.dataframe(ranked.rename("chance it is needed").to_frame()
                     .rename(index=story.NAMES).T, width="stretch")
        st.markdown(
            "Not a yes or a no — a **ranking, with a number attached**. That is the whole point "
            "of this step. Set *is the person responding* to `unknown` in the sidebar and watch "
            "the AED number sit somewhere in the middle instead of dropping to zero.")
        st.info("**Two compartments do not get a model.** Protective equipment and the "
                "communication unit are needed in every single emergency, so there is nothing "
                "to predict. They are a rule, written where people can see it — a model trained "
                "on a column that never changes cannot be tested and cannot be usefully wrong.")

    elif step["id"] == "gain":
        board, rules_opened, model_opened, test_answers = get_scores()
        st.dataframe(board.set_index("System"), width="stretch")
        st.plotly_chart(story.fig_misses(rules_opened, model_opened, test_answers),
                        width="stretch")
        st.markdown(
            "Two compartments have no bars for either system. Those are the ones the caller "
            "reports reliably, and there the plain rules were already perfect. A model cannot "
            "improve on perfect.\n\n"
            "The gain is concentrated where **something was left out** of the report. The model "
            "picks those up because the missing fact is hinted at elsewhere: somebody who says "
            "*road accident* is probably near traffic even if they never say so.\n\n"
            "And notice the compartment where the model is no better. That is the one we damaged "
            "by **flipping the report at random**. A random flip leaves no trace anywhere else, "
            "so there is nothing for any model to find. Missing information can sometimes be "
            "worked out. Wrong information cannot.")

    elif step["id"] == "safety":
        show_doors()
        decision_table()
        if restock:
            st.warning("Needs restocking: " + ", ".join(story.NAMES[c] for c in set(restock)))
        st.markdown(
            "The checks run **after** the model and can only ever take things away. They never "
            "add a compartment the model did not ask for, and the model can never talk them out "
            "of a decision.\n\n"
            "1. Is there anything usable in there? Empty, opened or expired means the door stays "
            "shut and says so.\n"
            "2. Does a nearby cabinet have one? Then say that, instead of just saying no.\n"
            "3. Is it restricted, and has a person confirmed? If not, the door waits.\n"
            "4. Low battery? Hand it over anyway and raise a flag. A weak defibrillator beats "
            "no defibrillator — that is a maintenance problem, not an emergency decision.\n"
            "5. Protective equipment always opens if there is any.")
        st.info("Turn the stock slider down and watch doors change to grey and blue.")

    elif step["id"] == "waiting":
        collapsed = dict(incident="cardiac", reported_bleeding=0, fire_present=0,
                         water_incident=0, traffic_hazard=0, people_affected=1,
                         person_responsive="no", dispatcher_confirmed=0)
        w_chances, w_states, w_notes, _ = story.cabinet_decides(
            collapsed, story.fresh_cabinet(), model)
        st.plotly_chart(story.fig_doors(w_states, w_chances, w_notes), width="stretch")
        st.caption("Somebody has collapsed and is not responding. No dispatcher on the line yet.")
        st.markdown(
            "Look at the AED. The model is as sure as it ever gets. The shelf has one. It works.\n\n"
            "And the door still did not open. It also did not refuse — it says **waiting**. The "
            "cabinet has asked a person, and until that person answers, it holds.\n\n"
            "Everything else carried on as normal. The protective compartment opened, because "
            "gloves help whatever is happening and cost nothing to be wrong about.")
        st.error(story.AED_NOTE)

    elif step["id"] == "cost":
        st.markdown("#### What the cabinet is trying to avoid, in order")
        st.dataframe(pd.DataFrame([
            {"Weight": story.W_UNSAFE, "What it is avoiding": "opening something unsafe"},
            {"Weight": story.W_MISSING, "What it is avoiding": "missing something needed"},
            {"Weight": story.W_SHORTAGE, "What it is avoiding": "leaving the next emergency short"},
            {"Weight": story.W_DELAY, "What it is avoiding": "each extra door to read"},
        ]).set_index("Weight"), width="stretch")

        allowed = set(story.COMPARTMENTS)
        full = story.fresh_cabinet()
        points = {c: story.door_opens_above(c, {**chances, c: 0.0}, full, allowed)
                  for c in story.COMPARTMENTS}
        st.plotly_chart(story.fig_thresholds(points), width="stretch")
        st.markdown(
            "Handing over a spare pair of gloves costs almost nothing. Handing over **the** "
            "defibrillator costs a great deal — there is exactly one, and it is the only thing "
            "in the cabinet nobody can improvise.\n\n"
            "So that weight is a small table rather than one number, and the result falls out of "
            "it: **the more it costs to be wrong, the surer the cabinet has to be.** Nobody typed "
            "those percentages in. They are what the weights imply.")

    elif step["id"] == "search":
        allowed = story.what_is_allowed(cabinet, REPORT)
        kit, cost = story.best_kit(chances, cabinet, allowed)
        a, b, c = st.columns(3)
        a.metric("Possible kits", 2 ** len(story.COMPARTMENTS))
        b.metric("Doors in the cheapest kit", len(kit))
        c.metric("What it scores", f"{cost:.2f}")
        st.markdown("**The cheapest kit:** " + ", ".join(sorted(story.NAMES[c] for c in kit)))
        st.code(
            "for size in range(8):\n"
            "    for kit in combinations(COMPARTMENTS, size):\n"
            "        score it, keep the cheapest",
            language="python")
        st.info("128 is a small number. Checking all of them takes no time at all, and then the "
                "answer is the best one — there is nothing left to wonder about. Clever search "
                "methods are for when you cannot do this. Here you can.")

    elif step["id"] == "day":
        days, fills = get_days()
        st.plotly_chart(story.fig_day(days, fills), width="stretch")
        rows = []
        for strategy, label in story.STRATEGIES:
            for f in fills:
                log, left = days[(strategy, f)]
                rows.append({"Strategy": label, "Shelves started at": f"{f:.0%}",
                             "Fully supplied": f"{log.fully_supplied.mean():.0%}",
                             "Items missed": int(log.missed.sum()),
                             "Handed over unnecessarily": int(log.extra.sum()),
                             "Items left at the end": int(left)})
        st.dataframe(pd.DataFrame(rows).set_index("Strategy"), width="stretch")
        st.markdown(
            "Follow the green line and the amber line and watch where they separate.\n\n"
            "- **Full shelves.** The lines meet. There is plenty of everything, so being careful "
            "saves things nobody was going to need.\n"
            "- **Partly stocked.** They pull apart, and the careful strategy is on top.\n"
            "- **Nearly empty.** They cross back. Nothing helps any more, and opening a few "
            "extra doors becomes a liability rather than a hedge.\n\n"
            "So the honest claim is narrower than *the AI wins*: **it earns its place when "
            "supplies are tight but not hopeless.** If your cabinets are always full, use the "
            "rulebook and save the money.")
        st.warning("Strategy A opens every door on every call, so on paper it should never miss "
                   "anything. Check the red line. Being generous is not the safe option — every "
                   "item handed out in the morning is one that is not there in the afternoon.")

    elif step["id"] == "sensors":
        st.plotly_chart(story.fig_events(), width="stretch")
        st.dataframe(pd.DataFrame(story.EVENT_LOG,
                                  columns=["Time", "Compartment", "What happened"])
                     .set_index("Time"), width="stretch")
        st.markdown("#### What the cabinet works out from that")
        st.dataframe(pd.DataFrame(
            [{"Compartment": story.NAMES.get(w, w), "Finding": note}
             for w, note in story.read_events()]).set_index("Compartment"),
            width="stretch")
        st.markdown(
            "The forced AED door is the obvious one — never unlocked, opened anyway, and two "
            "seconds later the defibrillator left the cabinet.\n\n"
            "The quiet ones matter too. **A door was unlocked and nothing was taken out of it**, "
            "which means we opened something we did not need to and it is now sitting open. And "
            "the bleeding package's seal broke long after the item was taken — nobody did "
            "anything wrong, but what is left in there is no longer sealed.")

    elif step["id"] == "misuse":
        table, line = get_anomaly()
        st.dataframe(table[["what", "really_wrong", "rules", "forest", "result"]]
                     .set_index("what"), width="stretch")
        st.metric("Anything stranger than this gets flagged", f"{line:.3f}",
                  help="Set by allowing 5% false alarms on days we know were normal — "
                       "not by trying numbers until the answers looked good.")
        st.markdown(
            "Check the last row first. **An ordinary call has to come out as ordinary**, and it "
            "does. A detector that flags everything is not a detector.\n\n"
            "Then look at what the forest misses. That is not a bug. An isolation forest splits "
            "**inside the range of values it has already seen**. It never saw more than three "
            "items taken at once, so no split it learned can separate six from three — the "
            "reading just follows the same branch as the biggest normal days.\n\n"
            "- **Unusual combinations of ordinary values** — what it is good at.\n"
            "- **The same thing, but much more of it** — what it is worst at, and that is most "
            "of what actually goes wrong with a cabinet.")
        st.success("The plain `if` statements do most of the work here. That is the honest "
                   "conclusion, and it is not the one people expect: write the simple check "
                   "first, measure it, and only add the model where the measurement shows a gap.")

    elif step["id"] == "limits":
        st.markdown(
            "**The data is invented.** Every emergency came from a generator written by somebody "
            "who already knew what the analysis should find.\n\n"
            "**The answer key was invented too, and that is worse.** We decided that a fire means "
            "burn supplies and an unresponsive person means the AED. Those are our rules, written "
            "into the data, and then a model learned them back. That is a circle. In real life "
            "the answer key comes from approved medical protocols, and it would not always agree "
            "with us.\n\n"
            "**It has never been tested on a real cabinet.** Sensors drift, doors jam in the "
            "cold, and a weight pad with a puddle on it reports confident nonsense.\n\n"
            "**The weights are a value judgement.** We decided the defibrillator costs six times "
            "more to hand over needlessly than a dressing does. Somebody could reasonably choose "
            "differently and get a different cabinet. That number should be signed off by the "
            "people responsible for the service.\n\n"
            "**One cabinet, one emergency at a time.** Two at once would confuse everything here."
            "\n\n**People are not in the model.** Somebody panicking takes the wrong thing, takes "
            "four of them, or freezes and takes nothing.")
        st.error("**The boundary that does not move:** this chooses *supplies*, from a list an "
                 "approved protocol allows. It never decides what treatment somebody needs, and "
                 "it never decides anything about a shock.")
        st.warning(DISCLAIMER)

    footer(step)
