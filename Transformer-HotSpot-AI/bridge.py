"""
bridge.py - the Electrical-Engineering -> AI teaching scaffold.
===============================================================
This module teaches no new concept and renders no model. Every technical
illustration lives in app.py / story.py. This wraps each stage renderer in a
five-part structure so a Power Systems student always sees, on every page:

    Electrical Engineering   the substation context      (bridge.open_page)
    The Challenge            why the manual way runs out (bridge.open_page)
    AI Connection            + the bridge figure         (bridge.open_page)
    Technical Idea           <- the stage renderer in app.py, untouched
    Key Takeaway             one sentence                (bridge.close_page)
    In the Notebook          where it lives              (bridge.close_page)

Text is short and professional. Short sentences, active voice, no drama. The
visuals carry the page; the text supports them.

COLOUR IS A TEACHING DEVICE AND MUST NEVER VARY.
    amber  = the substation / electrical engineering world
    cyan   = the AI world
    violet = the technical process
    red    = above a limit;  green = within limits
"""
import streamlit as st
import plotly.graph_objects as go

# ---------------------------------------------------------------- palette
BG, PANEL = "#0e1117", "#161b22"
EE = "#ffb74d"        # amber  - the substation
AISIDE = "#4fc3f7"    # cyan   - the AI
TECH = "#ba68c8"      # violet - the technical process
GREEN, RED = "#66bb6a", "#ef5350"
AMBERHOT = "#ff7043"  # the hot-spot accent
MUTED, TEXT = "#8b949e", "#e6edf3"
STEEL, INK, EDGE = "#141b24", "#0b0e13", "#2b3440"
MONOF = "ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', monospace"

# Protection-panel display language: busbar rules, relay-style cards, a thermal
# rail for the phase indicator. Deliberately distinct from the sibling apps.
_CSS = """
<style>
.stApp { background-image:
  radial-gradient(circle at 12% 0%, rgba(255,183,77,.05), transparent 42%),
  radial-gradient(circle at 88% 4%, rgba(79,195,247,.05), transparent 42%); }
hr { border-color:#2b3440 !important; }
.stButton>button { border-radius:2px; border:1px solid #3a4655; background:#141b24;
  text-transform:uppercase; letter-spacing:.07em; font-size:12px; font-weight:600; }
.stButton>button:hover { border-color:#ffb74d; color:#ffb74d; }
[data-testid="stMetric"] { background:#141b24; border:1px solid #2b3440;
  border-left:3px solid #ffb74d; border-radius:2px; padding:10px 12px; }
[data-testid="stMetricValue"] { font-family:__MONO__; }
[data-testid="stCaptionContainer"] p { font-family:__MONO__; letter-spacing:.02em; }

/* ---- busbar section header ---- */
.bus { display:flex; align-items:center; gap:11px; margin:24px 0 12px; }
.bus-tag { font-family:__MONO__; font-size:11px; font-weight:700; letter-spacing:.1em;
  border:1px solid; padding:2px 8px; border-radius:2px; white-space:nowrap; }
.bus-lab { font-family:__MONO__; text-transform:uppercase; letter-spacing:.16em;
  font-size:13px; font-weight:700; white-space:nowrap; }
.bus-bar { flex:1; height:5px; border-top:1px solid #2b3440; border-bottom:1px solid #2b3440; }

/* ---- relay card ---- */
.relay { position:relative; background:#141b24; border:1px solid #2b3440;
  border-left:3px solid #ffb74d; padding:14px 18px; color:#e6edf3;
  font-size:16px; line-height:1.65; margin:2px 0; }
.relay.ai { border-left-color:#4fc3f7; }
.relay.tech { border-left-color:#ba68c8; }
.relay.warn { border-left-color:#ef5350; }
.relay.ok { border-left-color:#66bb6a; }

/* ---- telemetry bar ---- */
.tele { font-family:__MONO__; background:#0b0e13; border:1px solid #2b3440;
  border-left:3px solid #ffb74d; padding:8px 14px; font-size:12px;
  letter-spacing:.06em; color:#8b949e; border-radius:2px; }
.pos { font-family:__MONO__; text-align:center; border:1px solid #ffb74d; border-radius:2px;
  background:#0b0e13; padding:6px 4px; font-size:11px; color:#8b949e; line-height:1.5; }
.pos b { color:#ffb74d; font-size:13px; }

/* ---- thermal rail (phase progress) ---- */
.rail { display:flex; flex-wrap:wrap; align-items:center; gap:4px; background:#0b0e13;
  border:1px solid #2b3440; border-radius:2px; padding:9px 12px; }
.rail-lab { font-family:__MONO__; font-size:11px; letter-spacing:.12em; color:#8b949e; margin-right:5px; }
.seg { font-family:__MONO__; font-size:11px; padding:2px 7px; border:1px solid #2b3440;
  color:#3f4650; border-radius:2px; }
.seg.done { color:#ffb74d; border-color:#5a4a2a; }
.seg.cur { background:#ffb74d; color:#0b0e13; border-color:#ffb74d; font-weight:700; }

/* ---- landing page ---- */
.brief { position:relative; border:1px solid #2b3440; background:#0b0e13; padding:20px 24px; }
.brief::before,.brief::after { content:''; position:absolute; width:16px; height:16px; border-color:#ffb74d; }
.brief::before { top:-1px; left:-1px; border-top:2px solid; border-left:2px solid; }
.brief::after { bottom:-1px; right:-1px; border-bottom:2px solid; border-right:2px solid; }
.brief-bar { font-family:__MONO__; font-size:12px; letter-spacing:.16em; color:#ffb74d; margin-bottom:8px; }
.ico { display:inline-flex; align-items:center; justify-content:center; width:40px; height:40px;
  border:1px solid #2b3440; border-radius:2px; font-size:22px; margin-bottom:8px; background:#0b0e13; }
.muted { color:#8b949e; font-size:13px; }
.sub { font-family:__MONO__; color:#8b949e; font-size:13px; }
.limit { font-family:__MONO__; font-size:12px; padding:3px 9px; border-radius:2px;
  border:1px solid; display:inline-block; margin-right:6px; }

/* ---- the question chain ---- */
.answering { border-left:3px solid #ba68c8; background:#141019; padding:9px 14px; margin:14px 0 4px 0;
  font-size:14.5px; color:#cbb6d6; }
.answering-tag { font-family:__MONO__; font-size:10.5px; letter-spacing:.16em; color:#ba68c8;
  display:block; margin-bottom:3px; }
.qcard { position:relative; border:1px solid #2b3440; border-left:3px solid #4fc3f7; background:#0b1116;
  padding:14px 18px; margin-bottom:10px; }
.qcard-tag { font-family:__MONO__; font-size:10.5px; letter-spacing:.16em; color:#4fc3f7;
  display:block; margin-bottom:5px; }
.qcard-q { font-size:19px; font-weight:600; color:#e6edf3; line-height:1.45; }

/* ---- beginner glossary ---- */
.term { border:1px solid #2b3440; background:#0b0e13; padding:10px 14px; margin-bottom:8px; }
.term-w { color:#4fc3f7; font-weight:700; font-size:14.5px; }
.term-p { color:#c9d1d9; font-size:14px; line-height:1.5; }
.term-e { color:#8b949e; font-size:13px; font-style:italic; }

/* ---- figure labels ---- */
.figlab { font-family:__MONO__; font-size:11.5px; letter-spacing:.10em; color:#8b949e;
  border-top:1px solid #2b3440; padding-top:5px; margin-top:2px; }
.figlab b { color:#ba68c8; letter-spacing:.14em; }

/* ---- what is wrong on a chart ---- */
.wrongkey { font-size:13px; color:#c9d1d9; border-left:3px solid #ff5252; background:#160f10;
  padding:8px 13px; margin-top:6px; }
.wrongkey b { color:#ff5252; }
</style>
""".replace("__MONO__", MONOF)


def inject_css():
    """Load the protection-panel display language once. Call after set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def _bus(tag, label, color):
    st.markdown(
        f"<div class='bus'>"
        f"<span class='bus-tag' style='color:{color};border-color:{color}'>{tag}</span>"
        f"<span class='bus-lab' style='color:{color}'>{label}</span>"
        f"<span class='bus-bar'></span></div>", unsafe_allow_html=True)


# ============================================================================
# THE TEN PHASES
# One page each, in the order a real machine-learning project runs.
# Every page ends with a question. The next page answers it.
# ============================================================================
PHASES = [
    ("The Problem",        "What is going wrong, in plain English."),
    ("The Data",           "What the substation actually records."),
    ("Exploring The Data", "Looking before touching. What is odd, and what is wrong."),
    ("Preparing The Data", "Cleaning, encoding, scaling - getting it fit to learn from."),
    ("How Learning Works", "The words, and the honest test."),
    ("The First Model",    "The simplest thing that could work, and where it breaks."),
    ("Training A Model",   "Models that bend, and why we picked this one."),
    ("Scoring It",         "The marks out of ten, and which one matters here."),
    ("Where It Fails",     "The errors that count, found on purpose."),
    ("Using It",           "One temperature, one decision."),
]


# ============================================================================
# THE STEPS  (one per phase; len(STEPS) is the count - never hardcode it)
#   ee / ai      - the two names of the same idea (amber name, cyan name)
#   tech         - what is actually computed (violet)
#   intro        - TWO SENTENCES MAX. Plain English. No jargon left unexplained.
#   question     - the question this page ends on; the next page answers it
#   takeaway     - ONE sentence
#   notebook     - which notebook phase implements it
# ============================================================================
STEPS = [

dict(
    id="problem", phase=0, ee_icon="\u26a1", ai_icon="\U0001f916",
    ee="The Problem", ai="Why This Needs Machine Learning",
    tech="One temperature, needed 35,040 times",
    ee_bullets=["Paper insulation cooks", "Damage adds up", "Nothing looks wrong"],
    ai_bullets=["Predict the unseen", "From sensors already fitted", "Every hour"],
    intro="""A transformer is a large electrical device that sits in a substation and quietly runs hot. Its
hottest point is buried deep inside, wrapped in paper that slowly cooks - and almost nobody can measure
that point, because the sensor has to be built in at the factory.""",
    question="If we cannot measure the hot spot, what <i>can</i> we measure?",
    takeaway="""The temperature that decides how long a transformer lives is the one nobody measures.""",
    notebook="""Phase 1 - the asset, the physics, and the target.""",
),
dict(
    id="data", phase=1, ee_icon="\U0001f4be", ai_icon="\U0001f5c3\ufe0f",
    ee="The Data", ai="The Dataset",
    tech="4 transformers x 8,760 hours x 8 sensors",
    ee_bullets=["Four transformers", "One year, hourly", "Ordinary sensors"],
    ai_bullets=["35,040 rows", "8 input columns", "1 answer column"],
    intro="""Every substation already logs a few ordinary readings once an hour - how much current is
flowing, how warm the air is, how warm the oil is. We have a year of that for four transformers.""",
    question="What does a whole year of these readings actually look like?",
    takeaway="""The inputs are cheap sensors already fitted; the answer column is the expensive one.""",
    notebook="""Phase 2 - loading the monitoring log.""",
),
dict(
    id="explore", phase=2, ee_icon="\U0001f50d", ai_icon="\U0001f4ca",
    ee="Exploring The Data", ai="Exploratory Data Analysis (EDA)",
    tech="Distributions, relationships, and things that cannot be true",
    ee_bullets=["Look before you touch", "Find the broken sensors", "Learn the daily rhythm"],
    ai_bullets=["EDA", "Outliers", "Correlation"],
    intro="""Before building anything, look at the data. That is <b>EDA</b> - exploratory data analysis -
which means plotting it and asking what is strange. Some of what you find is real, and some of it is a
broken sensor.""",
    question="Some of these readings are impossible. How do we get the data fit to learn from?",
    takeaway="""Every dataset arrives with faults in it, and plotting is how you find them.""",
    notebook="""Phase 3 - inspecting and exploring the export.""",
),
dict(
    id="prepare", phase=3, ee_icon="\U0001f9f9", ai_icon="\u2705",
    ee="Preparing The Data", ai="Cleaning, Encoding and Scaling",
    tech="Drop the impossible, number the categories, level the ranges",
    ee_bullets=["Bad readings out", "Categories to numbers", "Physics in"],
    ai_bullets=["Data cleaning", "Encoding", "Standardisation"],
    intro="""Raw data is never ready to use. Three jobs: throw out readings that cannot be true, turn
word-columns into numbers, and put every column on a comparable scale so none of them dominates just
because its numbers happen to be bigger.""",
    question="How do we know a model has actually learned, rather than memorised?",
    takeaway="""Preparation is most of the work, and skipping any of the three quietly ruins the result.""",
    notebook="""Phase 4 - cleaning, feature engineering, encoding and scaling.""",
),
dict(
    id="learning", phase=4, ee_icon="\U0001f4d0", ai_icon="\U0001f9ea",
    ee="How Learning Works", ai="Features, Labels and the Train / Test Split",
    tech="Learn on most of the year, mark on weeks it never saw",
    ee_bullets=["Study, then sit the exam", "Never mark your own paper", "Hold weeks back"],
    ai_bullets=["Feature and label", "Training", "Overfitting"],
    intro="""A model learns by being shown examples: these readings went with that temperature. To find out
whether it really learned, you hide some weeks from it and test on those - the same reason you do not
revise from the exam paper.""",
    question="What is the simplest model that could possibly work?",
    takeaway="""A score on data the model has already seen is not a score, it is a memory test.""",
    notebook="""Phase 5 - the honest train / test split.""",
),
dict(
    id="baseline", phase=5, ee_icon="\U0001f4dc", ai_icon="\U0001f4c9",
    ee="The First Model", ai="Baseline and Linear Regression",
    tech="The industry standard, then a straight line",
    ee_bullets=["The standard's own sum", "A straight-line fit", "Where it bends wrong"],
    ai_bullets=["Baseline", "Linear regression", "Residuals"],
    intro="""Always start with the simplest thing that works, so you know what "good" means. Here that is the
industry standard's own hand calculation, and then a <b>straight line</b> fitted through the data.""",
    question="The relationship curves, and a straight line cannot follow it. What can?",
    takeaway="""Without a baseline, any accuracy number sounds impressive and means nothing.""",
    notebook="""Phase 6 - the baseline and the linear model.""",
),
dict(
    id="training", phase=6, ee_icon="\U0001f333", ai_icon="\U0001f680",
    ee="Training A Model", ai="Ensembles, and Choosing One",
    tech="Many small rules, each fixing the last",
    ee_bullets=["Rules, not equations", "Each corrects the last", "Pick one for service"],
    ai_bullets=["Random Forest", "Gradient Boosting", "Model selection"],
    intro="""Instead of one equation, these models build hundreds of small yes/no rules and combine them.
That lets them follow a curve no straight line can, without anybody having to write the curve down.""",
    question="Three models, three sets of predictions. How do we say which one is best?",
    takeaway="""Tree models bend to the shape of the data, which is why they beat the straight line here.""",
    notebook="""Phase 7 - training the ensembles and comparing them.""",
),
dict(
    id="scoring", phase=7, ee_icon="\U0001f9ee", ai_icon="\U0001f4cf",
    ee="Scoring It", ai="MAE, RMSE and R\u00b2",
    tech="Three ways to be wrong, one that matters here",
    ee_bullets=["Average miss, in °C", "Punishes big misses", "Fraction explained"],
    ai_bullets=["MAE", "RMSE", "R\u00b2"],
    intro="""There is more than one way to measure "wrong", and each answers a different question. Pick the
wrong one and a bad model looks fine. For this job the one that matters is <b>MAE</b> - the average miss,
in degrees.""",
    question="The average is good. But is it good <i>where it matters</i>?",
    takeaway="""A single accuracy number hides where the model fails, and it always fails somewhere.""",
    notebook="""Phase 8 - the evaluation metrics and what each one hides.""",
),
dict(
    id="limits", phase=8, ee_icon="\u26a0\ufe0f", ai_icon="\U0001f4c9",
    ee="Where It Fails", ai="Segmented Evaluation and Generalisation",
    tech="The hot hours, and a transformer it has never seen",
    ee_bullets=["Hot hours do the damage", "Weakest exactly there", "A new unit is worse"],
    ai_bullets=["Segmented evaluation", "Bias", "Generalisation"],
    intro="""An average hides its worst days. The hottest 5 % of hours cause most of the damage here, so
that is exactly where the model has to be checked - not where it is easiest.""",
    question="Knowing all that, how should an engineer actually use it?",
    takeaway="""Find the model's weak spot yourself, before it finds you.""",
    notebook="""Phase 9 - segmented evaluation and the unseen-unit test.""",
),
dict(
    id="use", phase=9, ee_icon="\U0001f6a6", ai_icon="\U0001f3af",
    ee="Using It", ai="Prediction and Decision Support",
    tech="A temperature, a limit, and a recommended action",
    ee_bullets=["Predict now", "Compare to the limit", "Recommend, not act"],
    ai_bullets=["Live prediction", "Decision rules", "Human in charge"],
    intro="""A temperature on its own is not useful. It becomes useful when it is compared against a limit
and turned into a recommendation - which a person then accepts or overrules.""",
    question="",
    takeaway="""The model estimates; the engineer decides. That boundary is the whole design.""",
    notebook="""Phase 10 - live prediction and the decision rules.""",
),
]

BY_ID = {s["id"]: s for s in STEPS}
ORDER = [s["id"] for s in STEPS]


def goto(stage):
    st.query_params["stage"] = stage
    st.rerun()


def phase_steps(pi):
    return [s for s in STEPS if s["phase"] == pi]


# ============================================================================
# THE BRIDGE FIGURE  -  the substation card, the busbar, the AI card
# ============================================================================
def _wrap(text, width=22):
    out, line = [], ""
    for w in text.split():
        if len(line) + len(w) + 1 > width:
            out.append(line); line = w
        else:
            line = f"{line} {w}".strip()
    out.append(line)
    return "<br>".join(out)


def _card(fig, x0, x1, color, icon, title, bullets, kicker):
    fig.add_shape(type="rect", x0=x0, x1=x1, y0=0.10, y1=0.92, xref="x", yref="y",
                  line=dict(color=color, width=1.4), fillcolor=INK, layer="below")
    fig.add_shape(type="rect", x0=x0, x1=x0 + 0.012 * (x1 - x0) * 6, y0=0.10, y1=0.92,
                  line=dict(width=0), fillcolor=color, opacity=0.85, layer="below")
    cx = (x0 + x1) / 2
    fig.add_annotation(x=cx, y=0.84, text=f"<span style='font-size:26px'>{icon}</span>",
                       showarrow=False, font=dict(size=26))
    fig.add_annotation(x=cx, y=0.70, text=f"<b>{_wrap(title, 24)}</b>", showarrow=False,
                       font=dict(size=14, color=color), align="center")
    fig.add_annotation(x=cx, y=0.44, text="<br>".join(f"· {b}" for b in bullets),
                       showarrow=False, font=dict(size=12, color=TEXT), align="center")
    fig.add_annotation(x=cx, y=0.17, text=kicker, showarrow=False,
                       font=dict(size=10, color=MUTED, family=MONOF))


def bridge_figure(step, style, animate):
    """Substation card → busbar → AI card, with a packet that travels across."""
    fig = go.Figure()
    _card(fig, 0.02, 0.36, EE, step["ee_icon"], step["ee"], step["ee_bullets"],
          "IN THE SUBSTATION")
    _card(fig, 0.64, 0.98, AISIDE, step["ai_icon"], step["ai"], step["ai_bullets"],
          "IN THE AI")

    # the busbar between them
    for y in (0.55, 0.47):
        fig.add_shape(type="line", x0=0.38, x1=0.62, y0=y, y1=y,
                      line=dict(color=EDGE, width=2))
    fig.add_annotation(x=0.50, y=0.68, text="<b>IS THE SAME THING AS</b>", showarrow=False,
                       font=dict(size=11, color=MUTED, family=MONOF))
    fig.add_annotation(x=0.50, y=0.33, text=_wrap(step["tech"], 26), showarrow=False,
                       font=dict(size=11, color=TECH, family=MONOF), align="center")

    fig.add_trace(go.Scatter(x=[0.38], y=[0.51], mode="markers",
                             marker=dict(size=15, color=EE, symbol="diamond",
                                         line=dict(color=TEXT, width=1)),
                             hoverinfo="skip", showlegend=False))
    frames = []
    for i in range(24):
        f = i / 23
        frames.append(go.Frame(data=[go.Scatter(
            x=[0.38 + 0.24 * f], y=[0.51], mode="markers",
            marker=dict(size=15, symbol="diamond",
                        color=EE if f < 0.5 else AISIDE,
                        line=dict(color=TEXT, width=1)))]))
    fig.frames = frames
    fig.update_xaxes(visible=False, range=[0, 1])
    fig.update_yaxes(visible=False, range=[0, 1])
    fig.update_layout(margin=dict(l=6, r=6, t=6, b=6))
    return animate(style(fig, 300), frames, ms=55)


# ============================================================================
# NAVIGATION
# ============================================================================
def _nav(step, key):
    i = ORDER.index(step["id"])
    prev_s = BY_ID[ORDER[i - 1]] if i > 0 else None
    next_s = BY_ID[ORDER[i + 1]] if i < len(ORDER) - 1 else None
    c1, c2, c3 = st.columns([1, 1.25, 1])
    with c1:
        if prev_s:
            if st.button(f"◀  {prev_s['ee']}", key=f"prev_{key}", width="stretch"):
                goto(prev_s["id"])
        elif st.button("◀  The project overview", key=f"prev_{key}", width="stretch"):
            goto("start")
    with c2:
        st.markdown(f"<div class='pos'>▐ PHASE {i+1:02d} / {len(ORDER):02d} ▌"
                    f"<br><b>{step['ee']}</b></div>", unsafe_allow_html=True)
    with c3:
        if next_s:
            if st.button(f"{next_s['ee']}  ▶", key=f"next_{key}", width="stretch"):
                goto(next_s["id"])
        elif st.button("Back to the overview  ▶", key=f"next_{key}", width="stretch"):
            goto("start")


# ============================================================================
# open_page  -  Parts 1, 2 and 3, rendered ABOVE the stage renderer
# ============================================================================
def prev_question(stage):
    """The question the previous page ended on, which this page answers."""
    i = ORDER.index(stage)
    return STEPS[i - 1]["question"] if i > 0 else ""


def open_page(stage, style, animate):
    step = BY_ID.get(stage)
    if step is None:
        return
    pname, pdesc = PHASES[step["phase"]]
    i = ORDER.index(stage)

    _nav(step, "top")
    st.markdown(
        f"<div class='tele' style='margin-top:14px'>\u27e8ASHGROVE 132/33kV\u27e9 &nbsp; "
        f"PHASE {step['phase']+1:02d}/{len(PHASES)} "
        f"&nbsp;\u00b7&nbsp; <span style='color:{EE}'>{pname.upper()}</span> "
        f"&nbsp;—&nbsp; {pdesc}</div>", unsafe_allow_html=True)
    st.markdown(f"# {step['ee_icon']}  {step['ee']}")
    st.markdown(f"<span class='sub'>\u25b8 in machine learning this is called </span>"
                f"<b style='color:{AISIDE}'>{step['ai']}</b>", unsafe_allow_html=True)

    # ---- the answer half of the question chain ----------------------------
    q = prev_question(stage)
    if q:
        st.markdown(f"<div class='answering'><span class='answering-tag'>ANSWERING</span>"
                    f"{q}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='relay'>{step['intro']}</div>", unsafe_allow_html=True)
    st.divider()


# ============================================================================
# close_page  -  the takeaway and the question that opens the next page
# ============================================================================
def close_page(stage):
    step = BY_ID.get(stage)
    if step is None:
        return
    i = ORDER.index(stage)
    st.divider()

    _bus("KEY TAKEAWAY", "", GREEN)
    st.markdown(f"<div class='relay ok' style='font-size:18px;font-weight:600;line-height:1.5'>"
                f"{step['takeaway']}</div>", unsafe_allow_html=True)
    st.write("")

    # ---- the question half of the question chain --------------------------
    if step["question"]:
        nxt = STEPS[i + 1]
        st.markdown(f"<div class='qcard'><span class='qcard-tag'>THE QUESTION THIS LEAVES</span>"
                    f"<div class='qcard-q'>{step['question']}</div></div>",
                    unsafe_allow_html=True)
        if st.button(f"Answer it  \u2192  {nxt['ee_icon']}  {nxt['ee']}",
                     key=f"chain_{stage}", width="stretch", type="primary"):
            goto(nxt["id"])
    else:
        st.markdown("<div class='qcard'><span class='qcard-tag'>THAT IS THE COURSE</span>"
                    "<div class='qcard-q'>Ten questions, ten answers, one working "
                    "system.</div></div>", unsafe_allow_html=True)

    st.write("")
    st.caption(f"In the notebook: {step['notebook']}")
    segs = []
    for j, (pn, _) in enumerate(PHASES):
        cls = "cur" if j == step["phase"] else ("done" if j < step["phase"] else "")
        segs.append(f"<span class='seg {cls}' title='{pn}'>{j+1:02d}</span>")
    st.markdown(f"<div class='rail'><span class='rail-lab'>PHASE</span>" + "".join(segs)
                + f"<span class='rail-lab' style='margin-left:auto'>"
                f"{step['phase']+1:02d}/{len(PHASES)} \u00b7 {PHASES[step['phase']][0].upper()}"
                + "</span></div>", unsafe_allow_html=True)
    st.write("")
    _nav(step, "bottom")


# ============================================================================
# THE MIND MAP  -  clickable workflow, one node per phase
# ============================================================================
MAP_NODES = [
    ("The Problem", "problem", 0),
    ("The Data", "data", 1),
    ("Exploring It", "explore", 2),
    ("Preparing It", "prepare", 3),
    ("How Learning Works", "learning", 4),
    ("The First Model", "baseline", 5),
    ("Training A Model", "training", 6),
    ("Scoring It", "scoring", 7),
    ("Where It Fails", "limits", 8),
    ("Using It", "use", 9),
]


def mind_map(style):
    """The clickable workflow. Click a node to open its page."""
    n = len(MAP_NODES)
    ys = [n - i for i in range(n)]
    xs = [0.5] * n
    fig = go.Figure()
    for i in range(n - 1):
        fig.add_annotation(x=0.5, y=ys[i + 1], ax=0.5, ay=ys[i], xref="x", yref="y",
                           axref="x", ayref="y", showarrow=True, arrowhead=2,
                           arrowsize=1.1, arrowwidth=1.6, arrowcolor=EDGE)
    colors = [EE if i < 3 else (TECH if i < 5 else (AISIDE if i < 7 else GREEN))
              for i in range(n)]
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers+text",
        marker=dict(size=34, color=INK, line=dict(color=colors, width=2.4), symbol="square"),
        text=[f"  <b>{lbl}</b>" for lbl, _, _ in MAP_NODES],
        textposition="middle right", textfont=dict(size=14, color=TEXT),
        customdata=[sid for _, sid, _ in MAP_NODES],
        hovertemplate="<b>%{text}</b><br>click to open<extra></extra>", showlegend=False))
    fig.update_xaxes(visible=False, range=[0.35, 1.9])
    fig.update_yaxes(visible=False, range=[0.2, n + 0.8])
    fig.update_layout(margin=dict(l=6, r=6, t=6, b=6), clickmode="event+select")
    return style(fig, 40 * n + 60)


# ============================================================================
# THE ENGINEERING -> AI MAPPING FIGURE
# ============================================================================
def mapping_figure(style):
    """Two columns: read down the left and you have a monitoring scheme;
    read down the right and you have an ML pipeline. Same column."""
    rows = [("Transformer monitoring", "The problem definition"),
            ("Sensor measurements", "The input features"),
            ("Fibre-optic probe reading", "The label"),
            ("Data inspection", "Exploratory analysis"),
            ("Data cleaning", "Removing invalid rows"),
            ("Per-unit and rise quantities", "Feature engineering"),
            ("Common scale", "Normalisation"),
            ("A fair commissioning test", "Train / test split"),
            ("IEEE C57.91 estimate", "The baseline"),
            ("Hot-spot temperature", "The regression output"),
            ("Condition monitoring", "Model evaluation"),
            ("Maintenance decision support", "Rules on top of the model")]
    n = len(rows)
    fig = go.Figure()
    for i, (l, r) in enumerate(rows):
        y = n - i
        fig.add_shape(type="rect", x0=0.02, x1=0.44, y0=y - 0.34, y1=y + 0.34,
                      line=dict(color=EE, width=1), fillcolor=INK, layer="below")
        fig.add_shape(type="rect", x0=0.56, x1=0.98, y0=y - 0.34, y1=y + 0.34,
                      line=dict(color=AISIDE, width=1), fillcolor=INK, layer="below")
        fig.add_annotation(x=0.23, y=y, text=l, showarrow=False,
                           font=dict(size=12.5, color=EE))
        fig.add_annotation(x=0.77, y=y, text=r, showarrow=False,
                           font=dict(size=12.5, color=AISIDE))
        fig.add_annotation(x=0.50, y=y, text="→", showarrow=False,
                           font=dict(size=15, color=MUTED))
    fig.add_annotation(x=0.23, y=n + 0.9, text="<b>⚡ ELECTRICAL ENGINEERING</b>",
                       showarrow=False, font=dict(size=12, color=EE, family=MONOF))
    fig.add_annotation(x=0.77, y=n + 0.9, text="<b>🤖 MACHINE LEARNING</b>",
                       showarrow=False, font=dict(size=12, color=AISIDE, family=MONOF))
    fig.update_xaxes(visible=False, range=[0, 1])
    fig.update_yaxes(visible=False, range=[0.3, n + 1.4])
    fig.update_layout(margin=dict(l=6, r=6, t=6, b=6))
    return style(fig, 42 * n + 70)
