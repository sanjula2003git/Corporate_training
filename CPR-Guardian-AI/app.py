"""AI CPR Guardian - the illustration app for the notebook.

One page per teaching step, routed by ?stage=<id>. The rescue, the rules and
the detectors are the notebook's, unchanged: at the default sidebar settings
every number on every page is the notebook's number.

WRITTEN FOR SOMEBODY WITH NO MEDICAL BACKGROUND. Every clinical word is spelled
out where it first appears - 'AED' is 'the defibrillator', 'sternum' is 'the
breastbone', 'recoil' is 'letting the chest come back up'. The prose lives in
bridge.py; this file only renders it.

Every page has the same six parts:
    1 in the room · 2 why it is hard · 3 where the AI comes in
    4 what it looks like (the chart or table)
    5 what the picture shows, and what to look for in it
    6 in the notebook, the takeaway, and the question the next page answers

Navigation is by button, never by markdown link: Streamlit renders every
markdown link with target="_blank", so a link would open a new browser tab on
every click and a student walking the sixteen steps would finish with sixteen
tabs.
"""
import html

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
table.ht{width:100%;border-collapse:collapse;font-size:.92rem;margin:.2rem 0 1rem}
table.ht th{text-align:left;padding:.5rem .7rem;border-bottom:1px solid #30363d;color:#8b949e;
    font-weight:600}
table.ht td{padding:.5rem .7rem;border-bottom:1px solid #21262d;vertical-align:top}
table.ht td.name{white-space:nowrap;color:#4fc3f7;font-family:ui-monospace,SFMono-Regular,
    Consolas,monospace;border-bottom:1px dotted #4fc3f7;cursor:help}
.adv{border:1px solid #30363d;border-radius:12px;background:#161b22;padding:.85rem 1rem;
    height:100%}
.adv h4{margin:0 0 .45rem;font-size:.98rem;color:#4fc3f7}
.adv .no{color:#ff8a65;font-size:.87rem;margin:0 0 .4rem}
.adv .yes{color:#e6edf3;font-size:.87rem;margin:0}
</style>""", unsafe_allow_html=True)

# Kept for the honest-limits page, which is where a warning of this kind belongs.
# It is deliberately NOT on the landing page: the first thing a student meets
# should be the problem, not a legal notice.
DISCLAIMER = ("Educational simulation on invented data. Nothing here is a medical device, it has "
              "not been tested on anybody, and no part of it may be used to guide real "
              "resuscitation. The real thing is a regulated medical device.")


# --------------------------------------------------------------- controls
with st.sidebar:
    st.header("Rescue settings")
    patient = st.radio("Who is on the floor?", ["Adult (5-6 cm)", "Child (4-5 cm)"],
                       help="How far down a push should go. Every rule in the app is measured "
                            "against this band, and a child's chest needs a shallower one.")
    tire = st.slider("How much helper A tires", 0.0, 1.5, 1.0, 0.1,
                     help="1.0 is the notebook's setting. At 0 helper A never tires at all; "
                          "above 1.0 they fade faster than in the notebook.")
    drift = st.slider("Pad slipping (cm per minute)", 0.0, 1.0, 0.0, 0.05,
                      help="A pad sliding off the breastbone reports more depth than there "
                           "really is, and nothing in the unit notices.")
    alone = st.checkbox("The helper is alone", value=False,
                        help="There is nobody else in the room to take over the pushing.")
    st.caption("Change any of these and every page in the app re-runs with the new setting.")

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


def lines(column, value):
    """Short bullets, not a paragraph.

    Three columns of prose side by side is a wall of text at the top of every
    page. The registry holds these as tuples of short fragments; a plain string
    still renders, so a page left as prose does not break.
    """
    if isinstance(value, (list, tuple)):
        column.markdown("\n".join(f"- {line}" for line in value))
    else:
        column.write(value)


def helped(df):
    """Hover text for every column heading we have a plain-English definition for.

    Streamlit shows `help` as a tooltip on the column header, so a reader who
    does not know what 'Full recoil' means finds out by pointing at it instead
    of leaving the page.
    """
    return {c: st.column_config.Column(help=bridge.COLUMN_HELP[c])
            for c in df.columns if c in bridge.COLUMN_HELP}


def hover_table(rows, headers, tip_from=None):
    """A table whose first cell in each row carries a hover tooltip.

    st.dataframe cannot put a tooltip on a *cell* - column_config.help only
    reaches the header - and the thing a student wants to point at here is the
    measurement's own name. So these tables are plain HTML with a title
    attribute, which every browser turns into a tooltip on hover.

    Nothing is hidden behind the tooltip: the same explanation is still in the
    visible columns. The hover is a second way in, not the only way in.
    """
    tip_from = tip_from or (lambda r: r[1])
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = ""
    for r in rows:
        cells = f'<td class="name" title="{html.escape(str(tip_from(r)))}">{html.escape(str(r[0]))}</td>'
        cells += "".join(f"<td>{html.escape(str(c))}</td>" for c in r[1:])
        body += f"<tr>{cells}</tr>"
    st.markdown(f'<table class="ht"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>',
                unsafe_allow_html=True)


def header(st_):
    p = bridge.PHASES[st_["phase"]]
    # .get, not [...]: Streamlit can hot-reload app.py while still holding an
    # older bridge in memory, and a page that half-crashes in front of a class
    # is worse than one missing its badge. A reboot restores the full page.
    step = st_.get("step", "")
    badge = f" &nbsp;·&nbsp; DATA-SCIENCE STEP {step.upper()}" if step else ""
    st.markdown(
        f"<div class='hero'><small>PHASE {st_['phase'] + 1} OF {len(bridge.PHASES)} · {p[0]}"
        f"{badge}</small>"
        f"<h1>🫀 {st_['scene']}</h1><h3><span class='scene'>{st_['scene']}</span> → "
        f"<span class='ai'>{st_['ai']}</span></h3></div>", unsafe_allow_html=True)
    if st_.get("doing"):
        st.markdown(f"**What we are doing on this page, and why.** {st_['doing']}")
    a, b, c = st.columns(3)
    a.markdown("#### 1 · In the room")
    lines(a, st_["site"])
    b.markdown("#### 2 · Why it is hard")
    lines(b, st_["challenge"])
    c.markdown("#### 3 · Where the AI comes in")
    lines(c, st_["ai_link"])
    if st_.get("plain"):
        st.info(f"**In plain words.** {st_['plain']}")
    st.markdown(f"#### 4 · What it looks like — `{st_['tech']}`")


def picture(st_):
    """What the chart above actually shows, and what changed in it.

    A chart with no words under it is decoration. Every page with a picture says
    in two lines what is being drawn, then points at the thing the student is
    meant to notice - which is usually the thing going wrong - and says what
    hovering it will tell them.
    """
    if not st_.get("figure"):
        return
    st.markdown("#### 5 · What the picture shows")
    st.write(st_["figure"])
    if st_.get("watch"):
        st.warning(f"**What changed, and what to look for.** {st_['watch']}")


def footer(st_):
    st.markdown("#### 6 · In the notebook")
    st.write(st_["notebook"])
    st.success(st_["takeaway"])
    if st_.get("next_q"):
        st.markdown("##### Before you click next")
        st.info(st_["next_q"])
    i = bridge.ORDER.index(st_["id"])
    cols = st.columns(3)
    if i:
        goto(bridge.ORDER[i - 1], f"◀ {bridge.STEPS[i - 1]['scene']}", f"prev_{st_['id']}", cols[0])
    goto("start", "Overview", f"home_{st_['id']}", cols[1])
    if i < len(bridge.STEPS) - 1:
        goto(bridge.ORDER[i + 1], f"{bridge.STEPS[i + 1]['scene']} ▶", f"next_{st_['id']}", cols[2])


def measure_tables():
    """Every column one compression produces, in words a first-time reader can read.

    Rendered open rather than behind collapsed expanders: these names are the
    app's whole vocabulary, and a student who has to click four times to find
    out what `residual_cm` means will simply not click.
    """
    st.markdown(f"#### The {bridge.MEASURE_COUNT} numbers we take from every single push")
    st.caption("The pad and the camera both report fifty times a second. All of that is boiled "
               "down to one row per push, with these columns on it. Hover any name in blue to "
               "see what it means again.")
    for g in bridge.MEASURE_GROUPS:
        st.markdown(f"##### {g['name']}  ·  {len(g['rows'])} column"
                    f"{'s' if len(g['rows']) > 1 else ''}")
        a, b = st.columns(2)
        a.markdown(f"**What it is.** {g['idea']}")
        b.markdown(f"**What we do with it.** {g['plan']}")
        hover_table(g["rows"], ["Column", "What it is", "What the coach does with it"])


def report_table():
    df = story.report(comp, DEPTH_MIN, DEPTH_MAX).set_index("Rescuer")
    st.dataframe(df, width="stretch", column_config=helped(df))


# --------------------------------------------------------------- landing
if stage == "start":
    st.title("🫀 AI CPR Guardian")
    st.markdown(
        "Someone's heart has stopped in a public place. Until the ambulance arrives, the only "
        "thing keeping their blood moving is a stranger pushing hard and fast on their chest — "
        "and most strangers have never been shown how.\n\n"
        "This is a unit on the wall that watches that stranger and coaches them, using a "
        "camera, a pressure pad on the patient's chest, a speaker and three lights. Beside it "
        "sits a **defibrillator**: the box that reads the heart and decides by itself whether "
        "an electric shock is needed.\n\n"
        "**The unit never touches that decision.** It answers one question only — *what is the "
        "single most useful thing to tell this person right now?*")

    fired = when_tired("A")
    a, b, c, d = st.columns(4)
    a.metric("Pushes counted", len(comp),
             help="Every compression the unit found in the signal, over three and a half "
                  "minutes.")
    b.metric("Hands on the chest", f"{100 * s['ccf']:.0f}%",
             delta=f"{100 * s['ccf'] - 60:+.0f} vs the 60% floor",
             help="The share of the whole emergency during which somebody was actually "
                  "pushing. Guidelines want at least 60%.")
    c.metric("Green light", f"{100 * (comp.light == 'green').mean():.0f}%",
             help="The share of pushes the unit was completely happy with - nothing to correct.")
    d.metric("Fading caught at", f"{fired:.0f} s" if fired else "never",
             help="When the unit first noticed helper A was tiring, measured against that "
                  "helper's own opening pushes.")

    st.plotly_chart(story.fig_minutes(), width="stretch")
    st.caption("Every minute that passes with nobody pushing costs the patient roughly a tenth "
               "of the chance they have left. Green is what a bystander who starts and keeps "
               "going is worth. This one picture is drawn to explain that idea — every other "
               "number in the app comes from the simulated rescue.")

    st.subheader("The session, at your current settings")
    st.markdown(
        "**One row per helper, scoring everything they did.** Read the two rows against each "
        "other: they end up at roughly the same green share while failing at completely "
        "different things — A never lets the chest come back up, B pushes far too slowly. "
        "That is the point of the whole project, and it is why the unit judges push by push "
        "rather than reporting an average.")
    report_table()
    st.caption("Hover any column heading for what it means.")

    workflow = getattr(bridge, "WORKFLOW", [])
    if workflow:
        st.subheader("What this app actually does, step by step")
        st.markdown(
            "Underneath the emergency story this is an ordinary data project, done in the "
            "ordinary order. Every page below belongs to one of these steps and says which "
            "one it is at the top.")
        wf = pd.DataFrame([
            dict(Step=name, **{"What happens here": what,
                               "Pages": ", ".join(bridge.BY_ID[i]["scene"] for i in ids
                                                  if i in bridge.BY_ID)})
            for name, what, ids in workflow])
        st.dataframe(wf, hide_index=True, width="stretch", height=36 * len(workflow) + 44,
                     column_config={"Step": st.column_config.TextColumn("Step", width="medium"),
                                    "What happens here": st.column_config.TextColumn(width="large")})
        note = getattr(bridge, "WORKFLOW_NOTE", "")
        if note:
            st.info(note)

    st.subheader("Learning journey")
    st.caption("Sixteen pages, in order. Each has the same six parts: what we are doing and "
               "why, what is happening in the room, why it is hard, where the AI comes in, "
               "what the picture shows, and the question the next page answers.")
    for i, step in enumerate(bridge.STEPS, 1):
        label = f"**{i}. {step['scene']}** — {step['ai']}"
        if step.get("step"):
            label += f"  ·  _{step['step']}_"
        goto(step["id"], label, f"jump_{step['id']}")

    advantages = getattr(bridge, "ADVANTAGES", [])
    if advantages:
        st.subheader("What the finished project is worth")
        st.markdown(
            "Seven things the unit adds, each next to what actually happens without it. The "
            "four numbers at the top of this page are the measured version of the same claim, "
            "on the session your sidebar is currently describing.")
        a, b, c, d = st.columns(4)
        a.metric("Pushes measured", len(comp),
                 help="Nobody in the room counts these. The unit counts every one.")
        b.metric("Instructions spoken at once", "1",
                 help="Eight faults can be true at the same time. Only the most costly one is "
                      "ever said out loud.")
        c.metric("Fading caught at", f"{fired:.0f} s" if fired else "never",
                 help="How early the helper's decline was noticed - long before they could "
                      "feel it themselves.")
        d.metric("Shock decisions taken by the AI", "0",
                 help="That decision belongs to the defibrillator alone. There is no branch "
                      "anywhere in the code that could make it.")
        for row in range(0, len(advantages), 2):
            cols = st.columns(2)
            for col, adv in zip(cols, advantages[row:row + 2]):
                col.markdown(
                    f"<div class='adv'><h4>{html.escape(adv['name'])}</h4>"
                    f"<p class='no'><b>Without the unit.</b> {html.escape(adv['without'])}</p>"
                    f"<p class='yes'><b>With it.</b> {html.escape(adv['with_unit'])}</p></div>",
                    unsafe_allow_html=True)
            st.write("")

    st.subheader("The notebook")
    st.markdown(
        "[Open the full teaching notebook in Colab]"
        "(https://colab.research.google.com/github/sanjula2003git/Corporate_training/blob/main/"
        "CPR-Guardian-AI/AI_CPR_Guardian.ipynb)")

else:
    step = bridge.BY_ID.get(stage, bridge.STEPS[0])
    header(step)

    if step["id"] == "collapse":
        st.plotly_chart(story.fig_minutes(), width="stretch")
        a, b, c = st.columns(3)
        a.metric("The rescue, start to finish", f"{story.RESCUE_SECONDS} s")
        b.metric("Pushes in that time", len(comp))
        c.metric("Chances the helper gets", "one")
        picture(step)
        st.info("The unit has one job, and it is not working out what is wrong with the "
                "patient. It watches how somebody is pushing and says the most useful "
                "sentence available, once.")

    elif step["id"] == "sensors":
        st.dataframe(pd.DataFrame([
            {"Question": "Is the body in the right shape — arms, shoulders, hand position?",
             "Answered by": "Camera",
             "Why not the other one": "A pad cannot see arms, or a second person arriving"},
            {"Question": "How far down does each push go?", "Answered by": "Pressure pad",
             "Why not the other one": "A camera measures pixels, and turning pixels into "
                                      "centimetres depends on the lens, the angle, the "
                                      "distance, the clothing and the size of the person"},
            {"Question": "How fast, and does the chest come back up?",
             "Answered by": "Pressure pad",
             "Why not the other one": "Same reason — it is a question about physical distance"},
            {"Question": "Would an electric shock help this heart?",
             "Answered by": "The defibrillator",
             "Why not the other one": "This is the defibrillator's own regulated job"},
            {"Question": "Should a shock be delivered?",
             "Answered by": "The defibrillator. Only ever the defibrillator.",
             "Why not the other one": "The coaching AI must never make, override or influence "
                                      "this decision"},
        ]).set_index("Question"), width="stretch")
        st.error("**The boundary that does not move.** Nothing in this app or the notebook "
                 "decides about a shock. There is no branch anywhere in the code that could "
                 "grow into one, and adding one would be a different and regulated project.")
        st.markdown(
            "Six pages from now we measure the angle at somebody's elbow to within about a "
            "degree, from dots that wobble by a few millimetres. Hold that wobble next to a "
            "five-centimetre push and the argument above stops being an opinion.")

    elif step["id"] == "rescue":
        st.dataframe(pd.DataFrame([
            {"Time": "0 – 7 s", "What is happening": "Helper arrives and the unit powers up. "
                                                     "Nobody is pushing yet."},
            {"Time": "7 – 100 s", "What is happening": "Helper A. Starts well, then tires: "
                                                       "shallower, faster, leaning on the "
                                                       "chest, arms bending."},
            {"Time": "100 – 112 s", "What is happening": "The defibrillator checks the heart "
                                                         "and delivers a shock. Nobody may "
                                                         "touch the patient."},
            {"Time": "112 – 210 s", "What is happening": "Helper B, fresh. Good depth, far too "
                                                         "slow — until the beat pulls them up."},
        ]).set_index("Time"), width="stretch")
        st.plotly_chart(story.fig_whole_rescue(pad, DEPTH_MIN, DEPTH_MAX), width="stretch")
        picture(step)

    elif step["id"] == "pad":
        st.plotly_chart(story.fig_zoom(pad, DEPTH_MIN, DEPTH_MAX), width="stretch")
        a, b = st.columns(2)
        early = comp[(comp.t >= 20) & (comp.t < 25)]
        late = comp[(comp.t >= 92) & (comp.t < 97)]
        a.metric("Weight left on the chest at 20 s", f"{early.residual_cm.mean():.2f} cm",
                 help="How far down the chest still is between pushes while the helper is "
                      "fresh. It should be close to zero.")
        b.metric("Weight left on the chest at 92 s", f"{late.residual_cm.mean():.2f} cm",
                 delta=f"{late.residual_cm.mean() - early.residual_cm.mean():+.2f}",
                 delta_color="inverse",
                 help="The same measurement a minute later. Bigger is worse: the chest is "
                      "never getting all the way back up.")
        picture(step)
        st.markdown("That is one tired person, a minute and a half into the worst day of "
                    "somebody else's life. They cannot feel any of it happening.")

    elif step["id"] == "camera":
        st.plotly_chart(story.fig_posture(s["wrist"], s["elbow_pt"], s["shoulder"],
                                          s["elbow_smooth"]), width="stretch")
        picture(step)
        st.markdown(
            "Note what the camera is *not* being asked to do. It never reports a depth. It "
            "reports where three joints are, and all the arithmetic happens after that.")

    elif step["id"] == "elbow":
        st.plotly_chart(story.fig_elbow_error(pad, s["curves"]["elbow"], s["elbow_measured"],
                                              s["elbow_smooth"]), width="stretch")
        raw_err = float(np.abs(s["elbow_measured"] - s["curves"]["elbow"]).mean())
        sm_err = float(np.abs(s["elbow_smooth"] - s["curves"]["elbow"]).mean())
        a, b, c = st.columns(3)
        a.metric("How much the dots wobble", "4 mm",
                 help="How far each dot moves at random from one camera frame to the next, "
                      "while the arm itself is still.")
        b.metric("Error before smoothing", f"{raw_err:.2f}°",
                 help="How far the angle from the raw dots is from the arm's real angle, on "
                      "average.")
        c.metric("Error after smoothing", f"{sm_err:.2f}°",
                 delta=f"{sm_err - raw_err:.2f}°", delta_color="inverse",
                 help="The same error after averaging the angle over about half a second. "
                      "Smaller is better.")
        picture(step)
        st.markdown(
            "The elbow sits nearly on a straight line between shoulder and wrist, so a small "
            "sideways wobble swings the angle a long way. Averaging over half a second costs a "
            "little lag and buys back most of the accuracy.\n\n"
            "**Now hold those two numbers next to a push.** The same few millimetres that cost "
            "a degree of elbow angle would be a serious fraction of five centimetres of chest "
            "travel. That is the whole reason depth comes from the pad.")

    elif step["id"] == "peaks":
        st.plotly_chart(story.fig_peaks(pad, comp), width="stretch")
        a, b, c = st.columns(3)
        a.metric("Pushes found", len(comp),
                 help="How many compressions the three-line rule picked out of the signal.")
        b.metric("Time actually pushing", f"{s['hands_on']:.0f} s",
                 help="Total seconds with somebody's hands working on the chest.")
        c.metric("Average speed over that time",
                 f"{len(comp) / (s['hands_on'] / 60):.0f} /min",
                 help="Pushes per minute across the whole rescue. The guideline range is 100 "
                      "to 120.")
        picture(step)
        st.code(
            "higher = (d[1:-1] > d[:-2]) & (d[1:-1] >= d[2:])   # deeper than both neighbours\n"
            "cands  = np.where(higher & (d[1:-1] > 1.5))[0] + 1  # past a floor\n"
            "#  ... then keep the deeper of any two closer than a quarter of a second",
            language="python")
        st.info("Three lines of rule and no library. Not everything that reads a signal has to "
                "be a model.")
        st.divider()
        measure_tables()

    elif step["id"] == "release":
        st.plotly_chart(story.fig_depth_vs_stroke(comp, DEPTH_MIN, DEPTH_MAX), width="stretch")
        picture(step)
        st.markdown("**Each helper's averages.** One row per person, so the two can be "
                    "compared. Hover any column heading for what it means.")
        avg = (comp.groupby("rescuer")[["depth_cm", "stroke_cm", "residual_cm",
                                        "rate_cpm", "elbow_deg"]].mean().round(2)
               .rename(columns=bridge.MEASURE_LABELS))
        st.dataframe(avg, width="stretch", column_config=helped(avg))
        st.markdown(
            "**Depth and travel are not the same number, and the gap between them is the most "
            "important thing on this page.**\n\n"
            "- **Depth** — how far down the chest got. This is what the guidelines mean, and "
            "what the pad reports.\n"
            "- **Travel** — how far the chest actually *moved*: the depth, minus the point "
            "that push started from.\n\n"
            "They are equal only when the helper lets the chest come all the way back up. "
            "Helper A does not, so A's chest keeps reaching roughly the right depth while "
            "every push does less work.")

    elif step["id"] == "rules":
        rules = pd.DataFrame(
            [{"The unit sees": a, "Light": b, "It says": c, "Why it ranks here": d}
             for a, b, c, d in story.RULE_ORDER]).set_index("The unit sees")
        st.dataframe(rules, width="stretch")
        st.caption("Read top to bottom: the first line that matches is the one spoken, and "
                   "everything below it is ignored for that push.")
        st.plotly_chart(story.fig_messages(comp), width="stretch")
        st.plotly_chart(story.fig_lights(comp), width="stretch")
        picture(step)
        st.info("The list is in priority order, top to bottom, and only the first rule that "
                "fires is spoken. Reorder it and you have built a different device.")

    elif step["id"] == "metronome":
        st.plotly_chart(story.fig_metronome(comp), width="stretch")
        b_first = comp[comp.rescuer == "B"].head(1)
        a, b, c = st.columns(3)
        if len(b_first):
            a.metric("Helper B's first speed", f"{b_first.rate_cpm.iloc[0]:.0f} /min",
                     help="How fast helper B was pushing on their very first push, before the "
                          "beat had done anything.")
            b.metric("The first beat they hear", f"{b_first.beat_cpm.iloc[0]:.0f} /min",
                     help="Deliberately close to their own speed, so the first beat is one "
                          "they can already match.")
        c.metric("Where the beat is heading", f"{story.TARGET_CPM} /min",
                 help="The middle of the guideline range, which the beat walks towards and "
                      "then holds.")
        picture(step)
        st.markdown(
            "The beat starts as close to the helper's own speed as the guideline floor allows, "
            "so the first beat they hear is one they can already match. Then it walks steadily "
            "towards the middle of the range.\n\n"
            "**What it deliberately does not do is chase them.** An earlier version added a "
            "correction proportional to how far off the helper was, which runs away and parks "
            "on the bottom of the range — a beat that follows the helper down is a mirror, not "
            "a reference.")

    elif step["id"] == "fatigue":
        st.plotly_chart(story.fig_fatigue(comp, DEPTH_MIN, DEPTH_MAX), width="stretch")
        fat = story.fatigue_summary(comp).set_index("Rescuer")
        st.dataframe(fat, width="stretch", column_config=helped(fat))
        st.caption("Hover any column heading for what it means.")
        a_part = comp[comp.rescuer == "A"]
        a, b, c = st.columns(3)
        a.metric("Helper A's depth fell",
                 f"{a_part.depth_cm.head(20).mean() - a_part.depth_cm.tail(20).mean():.2f} cm",
                 help="Last twenty pushes against their first twenty. This barely moves, "
                      "which is why the obvious detector fails.")
        b.metric("Helper A's travel fell",
                 f"{a_part.stroke_cm.head(20).mean() - a_part.stroke_cm.tail(20).mean():.2f} cm",
                 help="The same comparison for how far the chest actually moved. This is the "
                      "number that falls, and the one the working detector watches.")
        fired = when_tired("A")
        c.metric("Caught at", f"{fired:.0f} s" if fired else "never",
                 help="When the working detector first raised the alarm.")
        picture(step)
        st.markdown(
            "**The left panel is a detector that does not work, kept here on purpose.** "
            "Watching depth alone, helper A's decline barely registers: it crosses the line "
            "late in the shift, or never crosses it at all. Watching the travel catches the "
            "same fading with most of the shift still to run. The table has both times at "
            "your current settings.\n\n"
            "The cause is physically real. As the helper tires they stop letting the chest "
            "come all the way back up, so each push starts from lower down and the chest still "
            "reaches about the same depth while doing less work.\n\n"
            "The threshold is set against **that helper's own first twenty pushes**, not an "
            "absolute number. An absolute number fires immediately for a physically small "
            "helper and never for a strong one.")
        st.caption("Turn the tiring dial in the sidebar down to zero and both panels should go "
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
        st.dataframe(pd.DataFrame(rows).set_index("Rescuer"), width="stretch",
                     column_config={
                         "Warn the standby": st.column_config.Column(
                             help="When the second person is told to get into position — "
                                  "fifteen seconds before the swap itself."),
                         "Call the swap": st.column_config.Column(
                             help="When the unit actually tells them to change over."),
                         "Why": st.column_config.Column(
                             help="Which of the two triggers fired first: the two-minute clock, "
                                  "or the fading detector from the previous page.")})
        if alone:
            st.error("**Nobody else is here.** A unit that says *you are tiring, swap with "
                     "somebody* to a person who is completely alone has issued an instruction "
                     "that cannot be followed, and the only thing it achieves is telling them "
                     "they are failing. The correct output is to keep the beat going and say "
                     "so.")
        else:
            st.markdown(
                "The standby person is asked to get into position **fifteen seconds before** "
                "the swap is called, so the changeover costs a couple of seconds rather than "
                "ten. Every one of those seconds is blood not moving.")
            st.caption("Tick *the helper is alone* in the sidebar to see what the unit should "
                       "say instead.")
        st.markdown(f"The swap is called on whichever comes first: **{story.SWITCH_SECONDS} "
                    "seconds** on the clock, or the fading detector from the previous page.")

    elif step["id"] == "handsoff":
        st.plotly_chart(story.fig_ccf(s["compressing"], s["hands_on"]), width="stretch")
        found, ccf_found = story.pauses_found(pad, peaks)
        a, b, c = st.columns(3)
        a.metric("Hands on the chest", f"{s['hands_on']:.0f} s",
                 help="Total seconds somebody was actually pushing.")
        b.metric("Hands off", f"{story.RESCUE_SECONDS - s['hands_on']:.0f} s",
                 help="Total seconds nobody was pushing, added up across every pause.")
        c.metric("Share of the time pushing", f"{100 * s['ccf']:.0f}%",
                 delta=f"{100 * s['ccf'] - 60:+.0f} vs the 60% floor",
                 help="Hands-on time as a share of the whole emergency. Guidelines want at "
                      "least 60%.")
        picture(step)
        st.markdown("**Found from the signal alone**, without being handed the list of pauses "
                    "— because the real unit is not handed one:")
        st.dataframe(pd.DataFrame(
            [{"Pause": f"{a_:.1f} s", "Until": f"{b_:.1f} s", "Length": f"{b_ - a_:.1f} s"}
             for a_, b_ in found]).set_index("Pause"), width="stretch")
        st.caption(f"That gives {100 * ccf_found:.1f}% against the {100 * s['ccf']:.1f}% we get "
                   "from knowing where the pauses were. A peak is the *bottom* of a push, so "
                   "measuring gaps peak-to-peak counts part of a push into each pause at both "
                   "ends. It reads slightly pessimistic, which is the direction you want to be "
                   "wrong in.")

    elif step["id"] == "aed":
        hands = st.checkbox("Somebody still has their hands on the patient", value=True)
        rows = []
        for state in story.AED_STATES:
            light, message = story.aed_coach(state, hands)
            rows.append({"What the defibrillator is doing": state, "Light": light.upper(),
                         "What the unit says": message})
        st.dataframe(pd.DataFrame(rows).set_index("What the defibrillator is doing"),
                     width="stretch")
        st.error("**There is no fifth state, and there never will be.** Nothing above decides "
                 "whether to shock. It reads what the defibrillator is doing and coaches "
                 "around it. Whether a heart needs a shock, and whether to deliver one, "
                 "belongs to the regulated defibrillator — and the coaching AI must never "
                 "make, override or influence that call.")
        st.markdown(
            "The loudest thing this state machine ever says is **start pushing again**, "
            "because the seconds after a shock — while a frightened helper waits for "
            "permission — are where rescues are lost.")
        st.plotly_chart(story.fig_ccf(s["compressing"], s["hands_on"]), width="stretch")
        picture(step)

    elif step["id"] == "timeline":
        st.plotly_chart(story.fig_timeline(comp, DEPTH_MIN, DEPTH_MAX), width="stretch")
        picture(step)
        report_table()
        st.caption("Hover any column heading for what it means.")
        st.markdown(
            "**Read the two rows of the table against each other.** Both helpers land at about "
            "the same green share while failing at completely different things — A on letting "
            "the chest come back up, B on speed. Neither set of averages looks disastrous, "
            "which is exactly why the unit works push by push instead of reporting means.")

    elif step["id"] == "limits":
        st.markdown(
            "**The data is invented.** Every number in this app came from a generator written "
            "by somebody who already knew what the analysis should find. Real helpers fail in "
            "ways nobody thought to simulate.\n\n"
            "**The camera is the weakest link.** The elbow page measured an angle to within "
            "about a degree *because the dots were generated cleanly*. In a real room the "
            "helper's back is to the camera, somebody walks through the frame, the patient is "
            "on their side in a stairwell, and the lighting is a phone torch. Vision models "
            "get much worse under exactly those conditions, and none of it is represented "
            "here.\n\n"
            "**Thresholds are not people.** Five centimetres is guidance for an adult. It is "
            "wrong for a child and wrong for a frail elderly chest. Shouting *press deeper* at "
            "somebody pushing correctly on an eighty-year-old is an instruction to cause "
            "harm.\n\n"
            "**A pad has to be placed correctly to measure anything.** Every depth number "
            "assumes the pad is on the breastbone and not sliding. A pad that has slipped "
            "reports confident nonsense, and nothing here notices.\n\n"
            "**Being told you are failing has a cost.** A helper who gets a red light every "
            "second may stop, and mediocre pushing is enormously better than none.")
        st.info("Two of those are dials in the sidebar. **Who is on the floor** switches the "
                "depth band to a child's, and **pad slipping** slides the pad. Turn either one "
                "and watch the green share below collapse — the unit has no idea anything has "
                "changed.")
        a, b, c = st.columns(3)
        a.metric("Green light now", f"{100 * (comp.light == 'green').mean():.0f}%",
                 help="The share of pushes the unit was happy with, at your current sidebar "
                      "settings.")
        b.metric("Told to press deeper", int((comp.message == "Press deeper").sum()),
                 help="How many pushes the unit called too shallow.")
        c.metric("Told to ease off", int((comp.message == "Ease off - too deep").sum()),
                 help="How many pushes the unit called too deep.")
        st.plotly_chart(story.fig_messages(comp), width="stretch")
        picture(step)
        st.error("**And the boundary that does not move:** the coach never decides about a "
                 "shock. That belongs to a regulated defibrillator, and this project models "
                 "only the stand-clear state around it.")
        st.warning(DISCLAIMER)

    footer(step)
