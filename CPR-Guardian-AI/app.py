"""AI CPR Guardian - the illustration app for the notebook.

One page per teaching step, routed by ?stage=<id>. The rescue, the rules and
the detectors are the notebook's, unchanged: at the default sidebar settings
every number on every page is the notebook's number.

Navigation is by button, never by markdown link: Streamlit renders every
markdown link with target="_blank", so a link would open a new browser tab on
every click and a student walking the sixteen steps would finish with sixteen
tabs.
"""
import numpy as np
import pandas as pd
import streamlit as st

import bridge
import story

st.set_page_config(page_title="AI CPR Guardian", page_icon="🫀", layout="wide")
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

DISCLAIMER = ("Educational simulation on invented data. Nothing here is a medical device, it has "
              "not been tested on anybody, and no part of it may be used to guide real "
              "resuscitation. The real thing is a regulated medical device.")


# --------------------------------------------------------------- controls
with st.sidebar:
    st.header("Rescue settings")
    patient = st.radio("Who is on the floor?", ["Adult (5-6 cm)", "Child (4-5 cm)"],
                       help="The depth band every rule below is measured against.")
    tire = st.slider("How hard rescuer A tires", 0.0, 1.5, 1.0, 0.1,
                     help="1.0 is the notebook. At 0 rescuer A never tires at all.")
    drift = st.slider("Pad slipping (cm per minute)", 0.0, 1.0, 0.0, 0.05,
                      help="A pad sliding on the chest reports more depth than there is.")
    alone = st.checkbox("The helper is alone", value=False,
                        help="Nobody else is here to take over.")
    st.caption("Change any of these and every page below re-runs.")

DEPTH_MIN, DEPTH_MAX = ((story.DEPTH_MIN, story.DEPTH_MAX) if patient.startswith("Adult")
                        else (story.CHILD_MIN, story.CHILD_MAX))


@st.cache_data(show_spinner="Running the rescue...")
def get_session(tire, drift, depth_min, depth_max):
    return story.build_session(tire=tire, drift=drift, depth_min=depth_min, depth_max=depth_max)


s = get_session(tire, drift, DEPTH_MIN, DEPTH_MAX)
pad, comp, peaks = s["pad"], s["comp"], s["peaks"]
stage = st.query_params.get("stage", "start")


def when_tired(who="A"):
    """When the working detector fired for this rescuer, or None."""
    part = comp[(comp.rescuer == who) & comp.tiring]
    return float(part.t.iloc[0]) if len(part) else None


# --------------------------------------------------------------- page frame
def goto(target, label, key, where=None):
    """One step of navigation, inside this browser tab."""
    if (where or st).button(label, key=key, width="stretch"):
        st.query_params["stage"] = target
        st.rerun()


def header(st_):
    p = bridge.PHASES[st_["phase"]]
    st.markdown(
        f"<div class='hero'><small>PHASE {st_['phase'] + 1} OF {len(bridge.PHASES)} · {p[0]}</small>"
        f"<h1>🫀 {st_['scene']}</h1><h3><span class='scene'>{st_['scene']}</span> → "
        f"<span class='ai'>{st_['ai']}</span></h3></div>", unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.markdown("#### 1 · In the room")
    a.write(st_["site"])
    b.markdown("#### 2 · Why it is hard")
    b.write(st_["challenge"])
    c.markdown("#### 3 · Where the AI comes in")
    c.write(st_["ai_link"])
    st.markdown(f"#### 4 · What it looks like — `{st_['tech']}`")


def footer(st_):
    st.markdown("#### 5 · In the notebook")
    st.write(st_["notebook"])
    st.success(st_["takeaway"])
    i = bridge.ORDER.index(st_["id"])
    cols = st.columns(3)
    if i:
        goto(bridge.ORDER[i - 1], f"◀ {bridge.STEPS[i - 1]['scene']}", f"prev_{st_['id']}", cols[0])
    goto("start", "Overview", f"home_{st_['id']}", cols[1])
    if i < len(bridge.STEPS) - 1:
        goto(bridge.ORDER[i + 1], f"{bridge.STEPS[i + 1]['scene']} ▶", f"next_{st_['id']}", cols[2])


def report_table():
    st.dataframe(story.report(comp, DEPTH_MIN, DEPTH_MAX).set_index("Rescuer"),
                 use_container_width=True)


# --------------------------------------------------------------- landing
if stage == "start":
    st.title("🫀 AI CPR Guardian")
    st.warning(DISCLAIMER)
    st.markdown(
        "A wall-mounted unit coaches an **untrained bystander** through chest compressions: "
        "camera, speaker, pressure pad, AED, an emergency-call link and three lights.\n\n"
        "It never decides anything about a shock. **That belongs to the AED, and only to the "
        "AED.** Everything on these pages is about the one question the unit does answer: "
        "*what is the single most useful thing to tell this person right now?*")

    fired = when_tired("A")
    a, b, c, d = st.columns(4)
    a.metric("Compressions counted", len(comp))
    b.metric("Hands on the chest", f"{100 * s['ccf']:.0f}%",
             delta=f"{100 * s['ccf'] - 60:+.0f} vs the 60% floor")
    c.metric("Green light", f"{100 * (comp.light == 'green').mean():.0f}%")
    d.metric("Fatigue caught at", f"{fired:.0f} s" if fired else "never",
             help="Rescuer A, detected on the stroke against their own opening compressions.")

    st.plotly_chart(story.fig_minutes(), use_container_width=True)
    st.caption("This curve is the rule of thumb every resuscitation course teaches, drawn out. "
               "It is illustration — no part of it comes from the simulation below.")

    st.subheader("The session, at your current settings")
    report_table()
    st.caption("Two rescuers, two completely different failures, and roughly the same score. "
               "That is the point of the whole project.")

    st.subheader("Learning journey")
    for i, step in enumerate(bridge.STEPS, 1):
        goto(step["id"], f"**{i}. {step['scene']}** — {step['ai']}", f"jump_{step['id']}")

    st.subheader("The notebook")
    st.markdown(
        "[Open the full teaching notebook in Colab]"
        "(https://colab.research.google.com/github/sanjula2003git/Corporate_training/blob/main/"
        "CPR-Guardian-AI/AI_CPR_Guardian.ipynb)")

else:
    step = bridge.BY_ID.get(stage, bridge.STEPS[0])
    header(step)

    if step["id"] == "collapse":
        st.plotly_chart(story.fig_minutes(), use_container_width=True)
        a, b, c = st.columns(3)
        a.metric("The rescue, start to finish", f"{story.RESCUE_SECONDS} s")
        b.metric("Compressions in that time", len(comp))
        c.metric("Chances the helper gets", "one")
        st.info("The unit has one job and it is not diagnosis. It watches how somebody is "
                "pressing and says the most useful sentence available, once.")

    elif step["id"] == "sensors":
        st.dataframe(pd.DataFrame([
            {"Question": "Is the posture right — elbows, shoulders, hand placement?",
             "Answered by": "Camera",
             "Why not the other one": "A pad cannot see arms, or a second person arriving"},
            {"Question": "How deep is each compression?", "Answered by": "Pressure pad",
             "Why not the other one": "A camera measures pixels, and pixels-to-centimetres "
                                      "depends on lens, angle, distance, clothing and body size"},
            {"Question": "How fast, and does the chest recoil?", "Answered by": "Pressure pad",
             "Why not the other one": "Same reason — it is a physical displacement question"},
            {"Question": "Is this rhythm shockable?", "Answered by": "AED",
             "Why not the other one": "This is the AED's regulated function"},
            {"Question": "Should a shock be delivered?", "Answered by": "The AED. Only ever the AED.",
             "Why not the other one": "The coaching AI must never make, override or influence "
                                      "this decision"},
        ]).set_index("Question"), use_container_width=True)
        st.error("**The boundary that does not move.** Nothing in this app or the notebook "
                 "decides about a shock. There is no branch anywhere in the code that could grow "
                 "into one, and adding one would be a different and regulated project.")
        st.markdown(
            "The elbow page later on measures an angle to within about a degree from keypoints "
            "that wobble by a few millimetres. Hold that number next to a five-centimetre "
            "compression and the depth argument stops being an opinion.")

    elif step["id"] == "rescue":
        st.dataframe(pd.DataFrame([
            {"Time": "0 – 7 s", "What is happening": "Helper arrives, unit powers up. No "
                                                     "compressions yet."},
            {"Time": "7 – 100 s", "What is happening": "Rescuer A. Starts well, then tires: "
                                                       "shallower, faster, leaning on the chest, "
                                                       "elbows bending."},
            {"Time": "100 – 112 s", "What is happening": "AED analysing, then a shock. Nobody may "
                                                         "touch the patient."},
            {"Time": "112 – 210 s", "What is happening": "Rescuer B, fresh. Good depth, far too "
                                                         "slow — until the beat pulls them up."},
        ]).set_index("Time"), use_container_width=True)
        st.plotly_chart(story.fig_whole_rescue(pad, DEPTH_MIN, DEPTH_MAX),
                        use_container_width=True)
        st.caption("At this zoom every compression is one vertical stroke. The next page zooms "
                   "in far enough to read one.")

    elif step["id"] == "pad":
        st.plotly_chart(story.fig_zoom(pad, DEPTH_MIN, DEPTH_MAX), use_container_width=True)
        st.markdown(
            "Read the two panels against each other. On the right the peaks are **lower**, they "
            "are **closer together**, and the troughs no longer come back down to the floor — "
            "the helper is resting their weight on the chest between pushes.\n\n"
            "That is one tired person, a minute and a half into the worst day of somebody "
            "else's life. They cannot feel any of it happening.")
        a, b = st.columns(2)
        early = comp[(comp.t >= 20) & (comp.t < 25)]
        late = comp[(comp.t >= 92) & (comp.t < 97)]
        a.metric("Lean between pushes at 20 s", f"{early.residual_cm.mean():.2f} cm")
        b.metric("Lean between pushes at 92 s", f"{late.residual_cm.mean():.2f} cm",
                 delta=f"{late.residual_cm.mean() - early.residual_cm.mean():+.2f}",
                 delta_color="inverse")

    elif step["id"] == "camera":
        st.plotly_chart(story.fig_posture(s["wrist"], s["elbow_pt"], s["shoulder"],
                                          s["elbow_smooth"]), use_container_width=True)
        st.markdown(
            "The cross is the centre of the sternum, where the hands belong. The dotted line is "
            "straight up from it: with good technique the shoulder sits on that line, directly "
            "over the hands, so the helper's **weight** does the work instead of their arms.\n\n"
            "Note what the camera is *not* being asked. It never reports a depth. It reports "
            "where three joints are, and the arithmetic happens after that.")

    elif step["id"] == "elbow":
        st.plotly_chart(story.fig_elbow_error(pad, s["curves"]["elbow"], s["elbow_measured"],
                                              s["elbow_smooth"]), use_container_width=True)
        raw_err = float(np.abs(s["elbow_measured"] - s["curves"]["elbow"]).mean())
        sm_err = float(np.abs(s["elbow_smooth"] - s["curves"]["elbow"]).mean())
        a, b, c = st.columns(3)
        a.metric("Keypoint wobble", "4 mm", help="Camera jitter, per joint, per frame.")
        b.metric("Error before smoothing", f"{raw_err:.2f}°")
        c.metric("Error after smoothing", f"{sm_err:.2f}°",
                 delta=f"{sm_err - raw_err:.2f}°", delta_color="inverse")
        st.markdown(
            "The elbow sits nearly on a straight line between shoulder and wrist, so a small "
            "sideways wobble swings the angle a long way. Averaging over half a second costs a "
            "little lag and buys back most of the accuracy.\n\n"
            "**Now hold those two numbers next to a compression.** The same few millimetres that "
            "cost a degree of elbow angle would be a serious fraction of five centimetres of "
            "chest travel. That is the whole reason depth comes from the pad.")

    elif step["id"] == "peaks":
        st.plotly_chart(story.fig_peaks(pad, comp), use_container_width=True)
        a, b, c = st.columns(3)
        a.metric("Compressions found", len(comp))
        b.metric("Time actually compressing", f"{s['hands_on']:.0f} s")
        c.metric("Average rate over that time",
                 f"{len(comp) / (s['hands_on'] / 60):.0f} /min")
        st.code(
            "higher = (d[1:-1] > d[:-2]) & (d[1:-1] >= d[2:])   # deeper than both neighbours\n"
            "cands  = np.where(higher & (d[1:-1] > 1.5))[0] + 1  # past a floor\n"
            "#  ... then keep the deeper of any two closer than a quarter of a second",
            language="python")
        st.info("Three lines of rule and no library. Not everything that reads a signal has to "
                "be a model.")

    elif step["id"] == "release":
        st.plotly_chart(story.fig_depth_vs_stroke(comp, DEPTH_MIN, DEPTH_MAX),
                        use_container_width=True)
        st.dataframe(comp.groupby("rescuer")[["depth_cm", "stroke_cm", "residual_cm",
                                              "rate_cpm", "elbow_deg"]].mean().round(2),
                     use_container_width=True)
        st.markdown(
            "**`depth` and `stroke` are not the same number, and the gap between them is the "
            "most important thing on this page.**\n\n"
            "- `depth` — how far down the chest got. This is what the guidelines mean, and what "
            "the pad reports.\n"
            "- `stroke` — how far the chest actually *travelled*: the peak, minus the point that "
            "push started from.\n\n"
            "They are equal only when the helper releases fully. Rescuer A does not, so A's "
            "chest keeps reaching roughly the right depth while every push does less work.")

    elif step["id"] == "rules":
        st.dataframe(pd.DataFrame(
            [{"The unit sees": a, "Light": b, "It says": c, "Why it ranks here": d}
             for a, b, c, d in story.RULE_ORDER]).set_index("The unit sees"),
            use_container_width=True)
        st.plotly_chart(story.fig_messages(comp), use_container_width=True)
        st.plotly_chart(story.fig_lights(comp), use_container_width=True)
        st.info("The list is in priority order, top to bottom, and only the first rule that "
                "fires is spoken. Reorder it and you have built a different device.")

    elif step["id"] == "metronome":
        st.plotly_chart(story.fig_metronome(comp), use_container_width=True)
        b_first = comp[comp.rescuer == "B"].head(1)
        a, b, c = st.columns(3)
        if len(b_first):
            a.metric("Rescuer B's first rate", f"{b_first.rate_cpm.iloc[0]:.0f} /min")
            b.metric("The first beat they hear", f"{b_first.beat_cpm.iloc[0]:.0f} /min")
        c.metric("Where the beat is heading", f"{story.TARGET_CPM} /min")
        st.markdown(
            "The beat starts as close to the helper's own rate as the guideline floor allows, so "
            "the first beat they hear is one they can already match. Then it walks steadily "
            "towards the middle of the range.\n\n"
            "**What it deliberately does not do is chase them.** An earlier version added a "
            "correction proportional to how far off the helper was, which runs away and parks on "
            "the bottom of the range — a beat that follows the helper down is a mirror, not a "
            "reference.")

    elif step["id"] == "fatigue":
        st.plotly_chart(story.fig_fatigue(comp, DEPTH_MIN, DEPTH_MAX), use_container_width=True)
        st.dataframe(story.fatigue_summary(comp).set_index("Rescuer"), use_container_width=True)
        a_part = comp[comp.rescuer == "A"]
        a, b, c = st.columns(3)
        a.metric("Rescuer A's peak depth fell",
                 f"{a_part.depth_cm.head(20).mean() - a_part.depth_cm.tail(20).mean():.2f} cm")
        b.metric("Rescuer A's stroke fell",
                 f"{a_part.stroke_cm.head(20).mean() - a_part.stroke_cm.tail(20).mean():.2f} cm")
        fired = when_tired("A")
        c.metric("Caught at", f"{fired:.0f} s" if fired else "never")
        st.markdown(
            "**The left panel is a detector that does not work, kept here on purpose.** Watching "
            "peak depth, rescuer A's decline barely registers: it crosses the line late in the "
            "stint, or never crosses it at all. Watching the stroke catches the same fatigue "
            "with most of the stint still to run. The table has both times at your current "
            "settings.\n\n"
            "The cause is physically real. As the helper tires they stop releasing fully, so "
            "each push starts from lower down and the chest still reaches about the same depth "
            "while doing less work.\n\n"
            "The threshold is against **that helper's own first twenty compressions**, not an "
            "absolute number. An absolute threshold fires immediately for a physically small "
            "helper and never for a strong one.")
        st.caption("Turn the fatigue dial in the sidebar down to zero and both panels should go "
                   "quiet. Turn it up and watch which panel notices first.")

    elif step["id"] == "switch":
        events = story.switch_plan(comp, second_person_available=not alone)
        rows = []
        for who, warn, call, reason in events:
            rows.append({
                "Rescuer": who,
                "Warn the standby": f"{warn:.0f} s" if warn is not None else "—",
                "Call the swap": f"{call:.0f} s" if call is not None else "—",
                "Why": reason})
        st.dataframe(pd.DataFrame(rows).set_index("Rescuer"), use_container_width=True)
        if alone:
            st.error("**Nobody else is here.** A unit that says *you are tiring, swap with "
                     "somebody* to a person who is completely alone has issued an instruction "
                     "that cannot be followed, and the only thing it achieves is telling them "
                     "they are failing. The correct output is to keep the beat going and say so.")
        else:
            st.markdown(
                "The standby person is asked to get into position **fifteen seconds before** the "
                "swap is called, so the changeover costs a couple of seconds rather than ten. "
                "Every one of those seconds is blood not moving.")
            st.caption("Tick *the helper is alone* in the sidebar to see what the unit should say "
                       "instead.")
        st.markdown(f"The swap is called on whichever comes first: **{story.SWITCH_SECONDS} "
                    "seconds** on the clock, or the fatigue detector from the previous page.")

    elif step["id"] == "handsoff":
        st.plotly_chart(story.fig_ccf(s["compressing"], s["hands_on"]), use_container_width=True)
        found, ccf_found = story.pauses_found(pad, peaks)
        a, b, c = st.columns(3)
        a.metric("Hands on the chest", f"{s['hands_on']:.0f} s")
        b.metric("Hands off", f"{story.RESCUE_SECONDS - s['hands_on']:.0f} s")
        c.metric("Compression fraction", f"{100 * s['ccf']:.0f}%",
                 delta=f"{100 * s['ccf'] - 60:+.0f} vs the 60% floor")
        st.markdown("**Found from the signal alone**, without being handed the list of pauses — "
                    "because the real unit is not handed one:")
        st.dataframe(pd.DataFrame(
            [{"Pause": f"{a_:.1f} s", "Until": f"{b_:.1f} s", "Length": f"{b_ - a_:.1f} s"}
             for a_, b_ in found]).set_index("Pause"), use_container_width=True)
        st.caption(f"That gives {100 * ccf_found:.1f}% against the {100 * s['ccf']:.1f}% we get "
                   "from knowing where the pauses were. A peak is the *bottom* of a push, so "
                   "measuring gaps peak-to-peak counts part of a compression cycle into each "
                   "pause at both ends. It reads slightly pessimistic, which is the direction "
                   "you want to be wrong in.")

    elif step["id"] == "aed":
        hands = st.checkbox("Somebody still has their hands on the patient", value=True)
        rows = []
        for state in story.AED_STATES:
            light, message = story.aed_coach(state, hands)
            rows.append({"AED state": state, "Light": light.upper(), "What the unit says": message})
        st.dataframe(pd.DataFrame(rows).set_index("AED state"), use_container_width=True)
        st.error("**There is no fifth state, and there never will be.** Nothing above decides "
                 "whether to shock. It reads what the AED is doing and coaches around it. "
                 "Whether a rhythm is shockable, and whether to deliver, belongs to a regulated "
                 "AED — and the coaching AI must never make, override or influence that call.")
        st.markdown(
            "The loudest thing this state machine ever says is **resume**, because the seconds "
            "after a shock — while a stunned helper waits for permission — are where rescues "
            "are lost.")
        st.plotly_chart(story.fig_ccf(s["compressing"], s["hands_on"]), use_container_width=True)
        st.caption("The second red block is that AED pause, priced in seconds.")

    elif step["id"] == "timeline":
        st.plotly_chart(story.fig_timeline(comp, DEPTH_MIN, DEPTH_MAX), use_container_width=True)
        report_table()
        st.markdown(
            "Top to bottom: depth with each compression coloured by what the unit said, rate "
            "against the beat, the lean between pushes with the stroke on its own axis, the "
            "elbow angle, and the light bar.\n\n"
            "**Read the two rows of the table against each other.** Both rescuers land at about "
            "the same green share while failing at completely different things — A on recoil, B "
            "on rate. Neither session average looks disastrous, which is exactly why the unit "
            "works compression by compression instead of reporting means.")

    elif step["id"] == "limits":
        st.markdown(
            "**The data is invented.** Every number in this app came from a generator written by "
            "somebody who already knew what the analysis should find. Real helpers fail in ways "
            "nobody thought to simulate.\n\n"
            "**The camera is the weakest link.** The elbow page measured an angle to within about "
            "a degree *because the keypoints were generated cleanly*. In a real room the helper's "
            "back is to the camera, somebody walks through the frame, the patient is on their "
            "side in a stairwell, and the lighting is a phone torch. Pose models degrade sharply "
            "under exactly those conditions, and none of it is represented here.\n\n"
            "**Thresholds are not people.** Five centimetres is guidance for an adult. It is "
            "wrong for a child and wrong for a frail elderly chest. Shouting *press deeper* at "
            "somebody compressing an eighty-year-old correctly is an instruction to cause harm.\n\n"
            "**A pad has to be placed correctly to measure anything.** Every depth number assumes "
            "the pad is on the sternum and not sliding. A displaced pad reports confident "
            "nonsense, and nothing here detects that.\n\n"
            "**Being told you are failing has a cost.** A helper who gets a red light every "
            "second may stop, and mediocre compressions are enormously better than none.")
        st.info("Two of those are dials in the sidebar. **Patient** switches the depth band to a "
                "child's, and **pad slipping** slides the pad. Turn either one and watch the "
                "green share on this page collapse — the unit has no idea anything has changed.")
        a, b, c = st.columns(3)
        a.metric("Green light now", f"{100 * (comp.light == 'green').mean():.0f}%")
        b.metric("Told to press deeper", int((comp.message == "Press deeper").sum()))
        c.metric("Told to ease off", int((comp.message == "Ease off - too deep").sum()))
        st.plotly_chart(story.fig_messages(comp), use_container_width=True)
        st.error("**And the boundary that does not move:** the coach never decides about a "
                 "shock. That belongs to a regulated AED, and this project models only the "
                 "stand-clear state around it.")
        st.warning(DISCLAIMER)

    footer(step)
