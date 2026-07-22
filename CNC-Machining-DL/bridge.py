"""
bridge.py - the Machining-Engineering -> AI teaching scaffold.
==============================================================
This module does not teach any NEW concept and it does not render any new
model, animation or asset. Every technical illustration lives in app.py /
story.py. This module wraps each stage renderer in a five-part structure so a
Manufacturing / Mechanical Engineering student always sees, on every page:

    Machining Engineering    the shop-floor context     (bridge.open_page)
    The Challenge            why the manual way runs out (bridge.open_page)
    AI Connection            + the bridge figure         (bridge.open_page)
    Technical Idea           <- the EXISTING renderer, untouched
    Key Takeaway             one sentence                (bridge.close_page)
    In the Notebook          where it lives              (bridge.close_page)

Text is deliberately short and professional. Short sentences, active voice, no
drama. The visuals carry the page; the text supports them.

COLOR IS A TEACHING DEVICE. Amber is ALWAYS the shop / machining world.
Cyan is ALWAYS the AI world. Violet is ALWAYS the technical process.
"""
import streamlit as st
import plotly.graph_objects as go

# ---------------------------------------------------------------- palette
BG, PANEL = "#0e1117", "#161b22"
CIVIL = "#ffb74d"      # amber  - the shop / machining engineering
AISIDE = "#4fc3f7"     # cyan   - the AI
TECH = "#ba68c8"       # violet - the technical process
GREEN, RED = "#66bb6a", "#ef5350"
MUTED, TEXT = "#8b949e", "#e6edf3"

# ---- CNC-specific display language (industrial DRO / blueprint) -------------
# Same amber/cyan/violet theme; a distinct LOOK from the sibling apps: monospace
# readouts, bracketed "operation" labels, corner-tick spec cards, a blueprint
# grid and a shop-traveler progress rail.
STEEL = "#141b24"      # panel variant for cards
INK = "#0b0e13"        # deep panel for readouts
EDGE = "#2b3440"       # hairline borders
MONOF = "ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', monospace"

_CSS = """
<style>
.stApp {
  background-image:
    linear-gradient(rgba(255,255,255,.022) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.022) 1px, transparent 1px);
  background-size: 28px 28px;
}
hr { border-color:#2b3440 !important; }
[data-testid="stCaptionContainer"] p { font-family:%(MONO)s; letter-spacing:.02em; }
.stButton>button {
  border-radius:2px; border:1px solid #3a4655; background:#141b24;
  text-transform:uppercase; letter-spacing:.07em; font-size:12px; font-weight:600;
}
.stButton>button:hover { border-color:#ffb74d; color:#ffb74d; }
[data-testid="stMetric"] {
  background:#141b24; border:1px solid #2b3440; border-left:3px solid #4fc3f7;
  border-radius:2px; padding:10px 12px;
}
[data-testid="stMetricValue"] { font-family:%(MONO)s; }
.op-row { display:flex; align-items:center; gap:10px; margin:22px 0 12px; }
.op-num { font-family:%(MONO)s; font-size:12px; font-weight:700; border:1px solid;
  padding:1px 7px; border-radius:2px; letter-spacing:.04em; white-space:nowrap; }
.op-label { font-family:%(MONO)s; text-transform:uppercase; letter-spacing:.14em;
  font-size:13px; font-weight:700; white-space:nowrap; }
.op-rule { flex:1; height:1px;
  background:repeating-linear-gradient(90deg,#2b3440 0 6px,transparent 6px 12px); }
.spec { position:relative; background:#141b24; border:1px solid #2b3440;
  padding:14px 18px; color:#e6edf3; font-size:16px; line-height:1.65; margin:2px 0; }
.spec::before, .spec::after { content:''; position:absolute; width:11px; height:11px;
  border-color:#ffb74d; }
.spec::before { top:-1px; left:-1px; border-top:2px solid; border-left:2px solid; }
.spec::after { bottom:-1px; right:-1px; border-bottom:2px solid; border-right:2px solid; }
.spec.ai::before,.spec.ai::after { border-color:#4fc3f7; }
.spec.tech::before,.spec.tech::after { border-color:#ba68c8; }
.spec.warn::before,.spec.warn::after { border-color:#ef5350; }
.spec.ok::before,.spec.ok::after { border-color:#66bb6a; }
.dro-bar { font-family:%(MONO)s; background:#0b0e13; border:1px solid #2b3440;
  border-left:3px solid #ffb74d; padding:8px 14px; font-size:12px; letter-spacing:.06em;
  color:#8b949e; border-radius:2px; }
.trav { font-family:%(MONO)s; text-align:center; border:1px solid #ffb74d; border-radius:2px;
  background:#0b0e13; padding:6px 4px; font-size:11px; color:#8b949e; line-height:1.5; }
.trav b { color:#ffb74d; font-size:13px; }
.travbar { display:flex; flex-wrap:wrap; align-items:center; gap:5px; background:#0b0e13;
  border:1px solid #2b3440; border-radius:2px; padding:9px 12px; }
.travlab { font-family:%(MONO)s; font-size:11px; letter-spacing:.12em; color:#8b949e; margin-right:4px; }
.ph { font-family:%(MONO)s; font-size:11px; padding:2px 6px; border:1px solid #2b3440;
  color:#3f4650; border-radius:2px; }
.ph.done { color:#ffb74d; border-color:#5a4a2a; }
.ph.cur { background:#ffb74d; color:#0b0e13; border-color:#ffb74d; font-weight:700; }
.brief { position:relative; border:1px solid #2b3440; background:#0b0e13; padding:20px 24px; }
.brief::before,.brief::after { content:''; position:absolute; width:16px; height:16px;
  border-color:#ffb74d; }
.brief::before { top:-1px; left:-1px; border-top:2px solid; border-left:2px solid; }
.brief::after { bottom:-1px; right:-1px; border-bottom:2px solid; border-right:2px solid; }
.brief-bar { font-family:%(MONO)s; font-size:12px; letter-spacing:.16em; color:#ffb74d; margin-bottom:8px; }
.card-ico { display:inline-flex; align-items:center; justify-content:center; width:40px; height:40px;
  border:1px solid #2b3440; border-radius:2px; font-size:22px; margin-bottom:8px; background:#0b0e13; }
.muted { color:#8b949e; font-size:13px; }
.substep { font-family:%(MONO)s; color:#8b949e; font-size:13px; }
</style>
""" % {"MONO": MONOF}


def inject_css():
    """Load the CNC display language once. Call after st.set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def _op_header(op, label, color):
    st.markdown(
        f"<div class='op-row'>"
        f"<span class='op-num' style='color:{color};border-color:{color}'>OP·{op}</span>"
        f"<span class='op-label' style='color:{color}'>{label}</span>"
        f"<span class='op-rule'></span></div>", unsafe_allow_html=True)


# ============================================================================
# THE ENGINEERING WORKFLOW
# The phases of optimizing a CNC machining job. Every AI concept hangs off one
# of them. The last one is the ledger the work gets judged by.
# ============================================================================
PHASES = [
    ("The Machine Shop",        "A batch needs cutting, and the wrong settings scrap parts or wreck tools."),
    ("The Cutting Trial",       "One pass becomes a record of the settings, forces and finish."),
    ("Instrumenting The Cut",   "Sensors are fitted, and every pass becomes a data stream."),
    ("Preparing The Data",      "Bad readings are removed, every channel is scaled, and the data is split."),
    ("Baseline From Readings",  "A model predicts roughness and tool life from the readings alone."),
    ("The Surface Wall",        "The camera arrives, and no hand-written finish rule works well enough."),
    ("How A Machine Learns",    "A trained network takes over from the machinist's feel."),
    ("Reading The Surface",     "A CNN grades the finish that no fixed rule could grade."),
    ("Inspecting The Tool",     "A CNN finds the chipped edge and shows where it looked."),
    ("The Machining Audit",     "We check every prediction to see if it worked."),
    ("Optimization & Fusion",   "Every signal feeds one screen that recommends a setting."),
    ("The Business Case",       "Cycle time, tool cost and scrap are turned into money saved."),
]


# ============================================================================
# THE STEPS  (one per page; len(STEPS) is the count - do not hardcode it)
#   civil / ai   - the two names of the same idea (amber name, cyan name)
#   tech         - what is actually computed (violet)
#   site         - Machining Engineering. NO AI in this text. 2-4 sentences.
#   challenge    - The Challenge. Why the manual way runs out of road.
#   ai_link      - AI Connection. Why this AI concept is therefore required.
#   takeaway     - Key Takeaway. ONE sentence.
#   notebook     - In the Notebook. Where this lives in the Colab notebook.
#   contributes  - In the Notebook. What this step contributes to the system.
# ============================================================================
STEPS = [

# ---------------------------------------------- PHASE 1 - THE MACHINE SHOP
dict(
    id='shopfloor', phase=0,
    civil='A Batch On The Machine', ai='Why Machining Optimization Exists',
    civil_icon='🛠️', ai_icon='🤖',
    tech="Cut fast and wear the tool vs cut slow and lose the shift",
    civil_bullets=['One batch, one tool', 'Speed, feed, depth', 'Wrong call = scrap'],
    ai_bullets=['Search every setting', 'Predict the outcome', 'Recommend the best'],
    site="""A CNC lathe has a batch of steel parts to turn. Before the first cut the machinist sets three numbers:
cutting speed, feed rate and depth of cut. Push them up and the part is finished in half the time. Push
them too far and the tool overheats, chatters, and chips.""",
    challenge="""There is a sweet spot, and it moves with the material, the tool and the machine. Cut too fast and you
pay in ruined tools and scrapped parts. Cut too slow and the shift runs out before the batch does. No
single machinist has tried every combination.""",
    ai_link="""The shop does not need judgement replaced. It needs every plausible setting evaluated - the finish and
tool life each one would give - so the fastest safe setting is chosen instead of guessed. That search,
too large to do by hand, is the only reason AI belongs at the machine.""",
    notebook="""Act 1. The three cutting parameters, and the trade-off between cycle time and tool cost.""",
    contributes="""The requirement the system is measured against. If cycle time or scrap does not fall, it failed.""",
    takeaway="""There is one fast, safe setting hidden among thousands - too many to try by hand.""",
),
dict(
    id='enter-ai', phase=0,
    civil='A Second Set Of Senses', ai='Continuous Cut Monitoring',
    civil_icon='📡', ai_icon='🛰️',
    tech='Same machine, sensed every second instead of spot-checked',
    civil_bullets=['Machinist stays', 'Sensors watch too', 'Nobody is replaced'],
    ai_bullets=['Every cut, always', 'Flags, not decisions', 'Machinist acts'],
    site="""Nothing about the machining changes. Same lathe, same tool, same steel. The machinist still sets the
job, still reads the first part, still signs it off. Sensors are added that report force, vibration,
temperature and spindle current on every cut, and a camera checks each finished surface.""",
    challenge="""The usual objection: is this here to replace the machinist? No. A model that sees only numbers cannot
feel a hot chuck, hear the change when a tool starts to rub, or judge whether a part is fit to ship. It
can only notice a change and estimate an outcome.""",
    ai_link="""This fixes the role of AI for the whole project. The system recommends and flags; a person decides and
signs off. Every later design choice, especially the machining audit, follows from that split.""",
    notebook="""No code. This step is the argument, not the arithmetic.""",
    contributes="""Defines the system's output: a recommendation to a machinist, not an automatic override.""",
    takeaway="""The system recommends and flags. The machinist decides and signs off.""",
),

# ---------------------------------------------- PHASE 2 - THE CUTTING TRIAL
dict(
    id='trial', phase=1,
    civil='One Cutting Pass', ai='Data Collection',
    civil_icon='🔧', ai_icon='🗄️',
    tech='One pass, one part -> one row of settings + readings + outcome',
    civil_bullets=['Set the parameters', 'Make the cut', 'Measure the result'],
    ai_bullets=['Each reading is a column', 'Each pass is a row', 'Rows stack into a table'],
    site="""You run a trial pass. You choose the speed, feed and depth. During the cut a dynamometer logs cutting
force, an accelerometer logs vibration, a thermocouple logs temperature and the drive logs spindle
current. Afterwards you measure the surface roughness and note how much tool life it cost.""",
    challenge="""Whoever reads that trial sheet later does not get the cut. Not the smell of hot swarf, not the note in
the sound as the tool dulled. They get a row of numbers. A mis-logged feed or a saturated force channel
means a wrong conclusion.""",
    ai_link="""For a model that limitation is absolute. It never stands at the machine and cannot re-run the cut. One
row - settings, readings, outcome - is all it gets, so a wrong row gives a wrong prediction with no way
to notice. That is why the next steps are all about the record.""",
    notebook="""The `PARAMS` and `SENSORS` lists and one pass's row - the whole cut, as the model receives it.""",
    contributes="""Every prediction is computed from a row like this. It is the system's only contact with the machine.""",
    takeaway="""The record is the model's entire cut. Wrong record, wrong prediction.""",
),
dict(
    id='two-records', phase=1,
    civil='A Reading vs A Surface Photo', ai='Structured vs Image Data',
    civil_icon='📊', ai_icon='🖼️',
    tech='7 named readings vs a grid of unnamed pixels',
    civil_bullets=['Sensor summaries', 'A photo of the finish', 'Same part, two records'],
    ai_bullets=['Columns an engineer named', 'Pixels nobody named', 'One model for both?'],
    site="""One machined part produces two kinds of record. The instrument summary: speed, feed, depth, force,
vibration, temperature, current - values an engineer named and gave units. And the camera image of the
finished surface: a grid of thousands of pixels, with nothing in it named.""",
    challenge="""A roughness of 3.2 microns already means something, because a standard defines it. The surface photo
means nothing until it is processed - and a chatter mark or a tear hides in the pattern of the pixels,
not in any single number a gauge reports.""",
    ai_link="""One part, two kinds of record, one question that shapes the course: can one kind of model handle both?
The tabular ML baseline and the image CNN answer it by building on each and watching where each fails.""",
    notebook="""No code. Seven named readings set beside one surface image.""",
    contributes="""The two branches of the finished system: tabular readings, and the camera image.""",
    takeaway="""Named readings and a surface image are two different problems.""",
),

# ---------------------------------------------- PHASE 3 - INSTRUMENTING THE CUT
dict(
    id='load', phase=2,
    civil='Commissioning The Machining Log', ai='Loading The Dataset',
    civil_icon='🚚', ai_icon='📥',
    tech='pd.read_csv -> 1,400 machining passes x columns',
    civil_bullets=['Log file arrives', 'Check the header', 'Count the passes'],
    ai_bullets=['Read the file', 'Check the header', 'Count the rows'],
    site="""The machine has logged every trial pass for weeks. Before anything is built on it, you open the export
and check it against what was installed. How many passes? Are all the sensors present? Is each column the
type it should be?""",
    challenge="""The temptation is to skip the check and start modeling. That is how a project discovers weeks later
that feed was logged in the wrong unit, or half the passes came from a run where the dynamometer had
drifted.""",
    ai_link="""Loading a dataset is that commissioning check. Establish what arrived: how many passes, how many
columns, what type each is. A model trained on the wrong data does not error - it trains without
complaint and gives wrong answers.""",
    notebook="""`pd.read_csv` on the machining log, then the row and column count.""",
    contributes="""The intake gate for the sensor branch. Every number the model learns from enters here.""",
    takeaway="""Check what the machine actually logged before you build on it.""",
),
dict(
    id='inspect', phase=2,
    civil='Sensor Health Check', ai='Data Inspection',
    civil_icon='🔍', ai_icon='📉',
    tech='Missing-value counts, distributions, out-of-range readings',
    civil_bullets=['Open every channel', 'Look for dropouts', 'Diagnose before acting'],
    ai_bullets=['Count the gaps', 'Plot the spread', 'Diagnose before cleaning'],
    site="""Now inspect the log the way you would inspect the machine. A loose thermocouple leaves a gap. A
dynamometer that saturated reads a flat maximum. An accelerometer that came unstuck reads a frozen
zero.""",
    challenge="""You cannot eyeball 1,400 passes the way you check one part. A channel that dropped out for a run leaves
a hole that looks like nothing. A stuck sensor looks perfectly reasonable. The fault is invisible at
this scale.""",
    ai_link="""So inspect the record with counts and distributions instead of eyes. Count missing readings per channel
and the failed sensor announces itself. Plot each column's spread and the stuck one spikes. Diagnosis
only - nothing is repaired here.""",
    notebook="""Missing-value counts per sensor, plus per-column distribution plots.""",
    contributes="""Tells the next step what to remove. Skip it and you clean blind.""",
    takeaway="""Diagnose the data before you repair it.""",
),

# ---------------------------------------------- PHASE 4 - PREPARING THE DATA
dict(
    id='clean', phase=3,
    civil='Dropouts And Spikes', ai='Data Cleaning',
    civil_icon='🧹', ai_icon='🧽',
    tech='Drop duplicates, remove impossible values, fill gaps',
    civil_bullets=['Sensor faults out', 'Duplicate passes out', 'Only sound rows train'],
    ai_bullets=['Duplicate records out', 'Impossible values handled', 'Only clean rows train'],
    site="""Act on the diagnosis. A cutting force of 9,999 N is a saturated channel and comes out. A vibration of
zero on a running cut is a dead probe, not a smooth cut. A pass logged twice is struck off.""",
    challenge="""That judgement is where inexperience shows. Drop every flawed pass and there is little left to learn
from. Keep everything and a dead-probe zero teaches the model that a violent cut can read zero
vibration. No rule decides it for you.""",
    ai_link="""A duplicated pass is the double-logged trial: it teaches the model one cut mattered twice. A missing
temperature is a judgement - fill with the median, or drop the row? Drop too much and there is nothing
to train on. Fill carelessly and the model believes readings that never happened.""",
    notebook="""The duplicate drop and missing-value handling, with row counts before and after.""",
    contributes="""The tabular model, the CNN and the fusion engine all inherit whatever you decide here.""",
    takeaway="""Cleaning is a judgement call, and everything downstream inherits it.""",
),
dict(
    id='normalize', phase=3,
    civil='One Common Scale', ai='Normalization',
    civil_icon='📏', ai_icon='⚖️',
    tech='MinMaxScaler -> every channel onto 0..1',
    civil_bullets=['Different units', 'One common scale', 'Now comparable'],
    ai_bullets=['N vs mm/rev vs °C', 'All scaled 0..1', 'No column dominates'],
    site="""Every channel reports in its own unit. Cutting force in the hundreds of newtons, feed in fractions of a
millimetre per revolution, temperature in the hundreds of degrees. Before they can be compared, they
are put on one common scale.""",
    challenge="""Raw magnitudes lie about importance. Force runs into the thousands; feed runs 0.05 to 0.45. Side by
side, force looks thousands of times more significant because of a unit, when a 0.1 mm/rev rise in feed
is the real driver of a rough finish.""",
    ai_link="""A neural network cannot tell a big number from an important one. It sees magnitude. Feed it raw columns
and it learns the unit, not the physics. Normalization puts every channel on 0 to 1, so importance is
learned from the data.""",
    notebook="""`MinMaxScaler`, fitted on the parameter and sensor columns.""",
    contributes="""Without this the model trains badly and blames the wrong channel. The scaler ships with the model.""",
    takeaway="""Scale the columns, or the network learns the units.""",
),
dict(
    id='split', phase=3,
    civil='Trial Cuts vs The Acceptance Run', ai='Train / Test Split',
    civil_icon='🧪', ai_icon='✂️',
    tech='train_test_split -> practice passes vs unseen passes',
    civil_bullets=['Tune on trial cuts', 'Prove on new cuts', 'Never the same pass'],
    ai_bullets=['Training set', 'Test set', 'Never the same rows'],
    site="""No machinist signs off a settings model using the very trial cuts it was tuned on. Tuning happens on
known passes. Acceptance is proven on passes the model has not seen.""",
    challenge="""Never test someone on the exact work they practised on. A model checked on the passes it trained on just
repeats what it memorised, scores brilliantly, and proves nothing. The first new part exposes it.""",
    ai_link="""So the passes are split: some to train on, some sealed away until the machining audit. Only a score on
unseen passes says anything about the next part off the machine.""",
    notebook="""`train_test_split`, producing the training passes and the sealed acceptance set.""",
    contributes="""This is what makes the machining audit mean anything. Break it and every result is a recital.""",
    takeaway="""The only fair score comes from cuts the model has never seen.""",
),

# ---------------------------------------------- PHASE 5 - BASELINE FROM READINGS
dict(
    id='ml-baseline', phase=4,
    civil='Predicting Finish And Tool Life', ai='Machine Learning',
    civil_icon='📈', ai_icon='🌲',
    tech='RandomForestRegressor on settings + sensor readings',
    civil_bullets=['Engineer names the factors', 'Model weighs them', 'Roughness & life out'],
    ai_bullets=['You name the factors', 'A Random Forest', 'Works on readings'],
    site="""Every experienced machinist carries a model in their head. High feed roughens the finish, high speed
shortens the tool, high force and vibration mean trouble. It is not written down, not consistent between
two machinists, and not available on the night shift.""",
    challenge="""So write it down. Roughness rises with feed - but by how much, and how much worse when the tool is
worn? It is not a single rule. It is thousands of weighted interactions the machinist cannot fully
articulate.""",
    ai_link="""This is the job machine learning does well. You do not state the equations. You state the factors - and
an engineer already named them: speed, feed, depth, force, vibration, temperature, current. Given those
columns and 1,400 outcomes, the Random Forest works out the mapping to roughness and tool life itself.""",
    notebook="""`RandomForestRegressor` for roughness and tool life, trained on the scaled readings, scored on the sealed passes.""",
    contributes="""The tabular branch of the system, and the predictor the optimizer searches over.""",
    takeaway="""Name the factors; let the model learn the finish and the tool life.""",
),

# ---------------------------------------------- PHASE 6 - THE SURFACE WALL
dict(
    id='surface-problem', phase=5,
    civil='What The Camera Actually Sends', ai='Raw Image As Input',
    civil_icon='🖼️', ai_icon='🔢',
    tech='One photo = a grid of pixels, none of them named',
    civil_bullets=['You see a bad finish', 'You spot the chatter', 'In one glance'],
    ai_bullets=['Thousands of pixels', 'None of them named', "None of them 'defect'"],
    site="""Look at a machined surface and you know. A good finish shows fine, even feed marks. A bad one shows
chatter bands, tearing or a smeared edge. An experienced machinist grades it at a glance, without ever
explaining how.""",
    challenge="""Now explain it - precisely enough that someone who has never seen a lathe could follow. Which pixel, at
what brightness, at what spacing? The defect is a pattern spread across the whole image, not a value in
any one place.""",
    ai_link="""The camera delivers a grid of pixels per part. Not one is named. Not one is the defect. At the trial an
engineer had already named force and feed, which is why the ML baseline worked. Here there is nothing
pre-named to weigh.""",
    notebook="""One surface image plotted, and its shape printed: a grid of unnamed pixel values.""",
    contributes="""The input the Random Forest cannot use and the CNN is built for.""",
    takeaway="""An image is thousands of pixels, and none of them is the defect.""",
),
dict(
    id='handmade', phase=5,
    civil='The Finish Rulebook, By Hand', ai='Hand-Made Features',
    civil_icon='📐', ai_icon='✍️',
    tech='One brightness threshold on the surface image',
    civil_bullets=['Measure average brightness', 'Set a limit', 'Watch it miss'],
    ai_bullets=['One number by hand', 'One cut-off line', 'It breaks easily'],
    site="""So you try the standard approach: reduce the image to a number. Take the average brightness, or the
overall contrast, set a limit, and reject anything past it. It works for a surface that is obviously
torn and dark.""",
    challenge="""But a chatter fault can have the same average brightness as a good finish while its pattern is
completely different. Tighten the limit and every slightly-shaded good part trips it. Loosen it and the
chatter sails through. One number cannot separate them.""",
    ai_link="""Every hand-made image feature is a rule you wrote and must maintain, and each one throws away most of
the picture. What you want is for the useful features to be discovered from the raw pixels, not guessed.
That is exactly what deep learning does.""",
    notebook="""An average-brightness feature, one threshold, and the chatter cases it misses.""",
    contributes="""The motive for the CNN: hand features are brittle and discard the pattern.""",
    takeaway="""Reducing an image to one hand-picked number throws away the defect.""",
),
dict(
    id='why-dl', phase=5,
    civil='The Rulebook Runs Out', ai='Therefore: Deep Learning',
    civil_icon='🧠', ai_icon='🚀',
    tech='Learned features vs hand-written rules',
    civil_bullets=['No threshold works', 'Too many patterns', 'Let it learn'],
    ai_bullets=['It learns the patterns', 'From examples', 'Not from rules'],
    site="""Step back. You have a task an expert does instantly and cannot put into a rule: look at a surface and
grade it, glance at a tool and see the chip. Every threshold you write is either too tight or too
loose.""",
    challenge="""The problem is not effort. There is no finite rulebook. The patterns that separate a good finish from
early chatter are subtle, overlapping, and different for every material and tool.""",
    ai_link="""Deep learning changes the question. Instead of you writing the rules, you supply labeled examples -
good surfaces and defective ones, intact tools and chipped ones - and the network learns the features
that separate them. It does not dig deeper into your readings; it works where there are no named
readings at all.""",
    notebook="""No code. The argument that motivates the two CNNs that follow.""",
    contributes="""The turning point of the course: from named features to learned ones.""",
    takeaway="""When nobody can write the rule, the model learns it from examples.""",
),

# ---------------------------------------------- PHASE 7 - HOW A MACHINE LEARNS
dict(
    id='machinist-brain', phase=6,
    civil="The Machinist's Judgement", ai='The Neuron, Conceptually',
    civil_icon='👷', ai_icon='🧠',
    tech='Weighted evidence -> one decision',
    civil_bullets=['Several signals', 'Each weighted', 'One call'],
    ai_bullets=['Several inputs', 'Each weighted', 'One output'],
    site="""Watch how a machinist actually decides whether to trust a setting. Vibration matters a lot. Cutting
force matters somewhat. Ambient temperature barely matters. They weigh each signal by how much it
usually predicts trouble, add it up, and make one call: run it, or back it off.""",
    challenge="""That weighting is not written down and no two machinists match exactly. It is learned from years of
cuts that went well and cuts that scrapped a part. You cannot hand it to a new starter.""",
    ai_link="""That process - weigh each input, sum, decide - is exactly one artificial neuron. The weights are what
the machinist's experience becomes. Everything that follows is how those weights get set from data.""",
    notebook="""No code. The mental model of a neuron before any mathematics.""",
    contributes="""The intuition every later step builds on: a neuron is weighted evidence to a decision.""",
    takeaway="""A machinist weighing signals into one call is a neuron.""",
),
dict(
    id='neuron', phase=6,
    civil='Weighing The Signals', ai='Weighted Sum + Bias',
    civil_icon='⚙️', ai_icon='➕',
    tech='z = w·x + b',
    civil_bullets=['Weigh each signal', 'Add them up', 'Add a baseline'],
    ai_bullets=['Weigh each input', 'Add them up', 'Add a bias'],
    site="""Make the machinist's judgement explicit. Each reading gets a weight: vibration high, force moderate,
speed small. Multiply each reading by its weight, add them up, and add a baseline offset for how
cautious this job's tolerance is.""",
    challenge="""Set those weights by hand across seven channels and you are guessing. Too much weight on speed and every
fast-but-fine cut is condemned. The right weights are not obvious and interact.""",
    ai_link="""This weighted sum plus bias is the whole of a neuron's forward step: z = w·x + b. Slide the weights
below and watch one cut's score cross the line. Learning, next, is just setting these weights
automatically.""",
    notebook="""The dot product `w·x + b` written out for one pass's readings.""",
    contributes="""The single computation every layer of every network repeats.""",
    takeaway="""A neuron multiplies each signal by a weight, sums, and adds a bias.""",
),
dict(
    id='activation', phase=6,
    civil='When To Reject The Cut', ai='Activation Function',
    civil_icon='🚨', ai_icon='📈',
    tech='sigmoid / ReLU on z',
    civil_bullets=['Weak signal: accept', 'Strong signal: reject', 'Ramps up smoothly'],
    ai_bullets=['Low score, no', 'High score, yes', 'A smooth switch'],
    site="""A weighted score is not yet a decision. The machinist needs a call: below a level, the cut is fine;
above it, reject the part. And it should not flip on a single point of noise - it should turn on
smoothly as evidence builds.""",
    challenge="""A hard cut-off is brittle: one reading either side of the line flips the call. Real judgement ramps up -
a little doubt, then concern, then certainty - and a straight-line score cannot bend like that.""",
    ai_link="""The activation function is that smooth switch. Sigmoid turns any score into a 0-to-1 probability of a
bad part; ReLU passes strong evidence and blocks the rest. Without it, stacking neurons stays linear and
learns nothing curved.""",
    notebook="""`sigmoid` and `relu` plotted, and the same neuron with and without one.""",
    contributes="""What lets a network bend - the reason depth adds power.""",
    takeaway="""Activation turns a raw score into a decision, and lets the network bend.""",
),
dict(
    id='learning-loop', phase=6,
    civil='Every Scrapped Part Teaches', ai='The Learning Loop',
    civil_icon='🔁', ai_icon='🔄',
    tech='predict -> measure error -> adjust -> repeat',
    civil_bullets=['Make a call', 'See the part', 'Adjust the rule'],
    ai_bullets=['Predict', 'Measure error', 'Update weights'],
    site="""How does a machinist get good? They call a setting safe, the part comes off rough, and they adjust:
that feed mattered more than they thought. Next time they weigh it heavier. Every scrapped part tunes
the internal model.""",
    challenge="""Done by hand this takes a career, and the lessons live in one person's head. A shop cannot wait years,
and cannot lose the model when that person leaves.""",
    ai_link="""Training is that loop, run thousands of times a second. The network predicts, compares to the measured
outcome, and nudges every weight to be a little less wrong. Predict, measure, adjust, repeat - that is
all learning is.""",
    notebook="""No code. The loop in plain terms before loss and gradients name its parts.""",
    contributes="""The skeleton of training that the next steps fill in.""",
    takeaway="""Learning is predict, measure the error, adjust, and repeat.""",
),
dict(
    id='gradient-descent', phase=6,
    civil='Dialling In The Setting', ai='Loss + Gradient Descent',
    civil_icon='🎚️', ai_icon='⬇️',
    tech='minimize loss by stepping downhill in w',
    civil_bullets=['See how wrong', 'Which way is better', 'Take a small step'],
    ai_bullets=['Loss = how wrong', 'Gradient = the way', 'Take a small step'],
    site="""To dial in a setting you need two things: a number for how wrong you were, and which direction fixes it.
Called a finish good and it came off rough - that is a large, costly error. Nudge the feed the way that
would have caught it, by a sensible amount.""",
    challenge="""Nudge by hand across seven weights at once and you cannot tell which change helped. Too big a step and
you overshoot into rejecting good parts; too small and it never settles. And there is no time to try
every combination.""",
    ai_link="""Loss measures how wrong the network is; the gradient points to the weights that reduce it fastest.
Gradient descent takes a step downhill, again and again, until the error stops falling. Slide the step
size below and watch it converge or overshoot.""",
    notebook="""The loss curve over epochs, and the effect of the learning rate on convergence.""",
    contributes="""The engine of training - how every weight in the network actually moves.""",
    takeaway="""Loss says how wrong; the gradient says which way; the step size says how far.""",
),
dict(
    id='network', phase=6,
    civil='From One Expert To A Team', ai='The Neural Network',
    civil_icon='👥', ai_icon='🕸️',
    tech='layers of neurons feeding forward',
    civil_bullets=['One expert: limited', 'A team: layered', 'Specialists combine'],
    ai_bullets=['One neuron: a line', 'Layers bend it', 'Together: real patterns'],
    site="""One machinist has limits. A process team layers expertise: a tooling specialist feeds a cell leader, who
feeds the process engineer. Each layer combines what the one below noticed into a higher-level
judgement.""",
    challenge="""A single weighted rule can only split the world with one straight line. Real defect patterns are not
linear - fast and light means one thing, fast and deep another. One neuron cannot hold that.""",
    ai_link="""Stack neurons into layers and the network composes simple features into complex ones, exactly like the
team. The first layer finds crude patterns; deeper layers combine them. Depth is what lets it represent
any decision boundary.""",
    notebook="""An `MLPClassifier` with hidden layers, and how width and depth change the fit.""",
    contributes="""The architecture the tabular ANN and, later, the surface and tool CNNs are all built from.""",
    takeaway="""Layered neurons compose simple signals into complex judgements.""",
),
dict(
    id='training', phase=6,
    civil='Running The Trials', ai='Training The Model',
    civil_icon='🏋️', ai_icon='📉',
    tech='epochs of forward pass + backprop on the training set',
    civil_bullets=['Show it examples', 'Correct each miss', 'Go around again'],
    ai_bullets=['Show it examples', 'Correct each miss', 'The error drops'],
    site="""Commission the model the way you qualify a new hand: show it many cuts whose outcome is known, let it
call each, correct every miss, and go around again. Each full pass over the examples is one round of
trials.""",
    challenge="""Too few trials and it has not learned the patterns. Too many on the same passes and it memorises them -
brilliant on the training cuts, useless on a new part. You need to know when to stop.""",
    ai_link="""Training runs the learning loop over the whole training set for many epochs, watching the loss fall on
data it trains on and on held-out data it does not. When the held-out loss stops improving, you stop.
Watch the curve below.""",
    notebook="""The training loop, the loss curve, and the early-stopping point.""",
    contributes="""Produces the trained tabular model that the audit then judges.""",
    takeaway="""Training repeats the learning loop until held-out error stops falling.""",
),

# ---------------------------------------------- PHASE 8 - READING THE SURFACE
dict(
    id='cnn-journey', phase=7,
    civil='How The Surface Is Read', ai='Convolutional Neural Network',
    civil_icon='🖼️', ai_icon='🧬',
    tech='filters -> feature maps -> finish grade',
    civil_bullets=['Slide a detector', 'Find repeating marks', 'Build up the grade'],
    ai_bullets=['Filters slide across', 'Build up feature maps', 'Learned, not coded'],
    site="""A machinist does not read pixels. They look for repeating features - the spacing of the feed marks, the
banding of chatter, the direction of a tear - and grade the finish from those patterns wherever they
appear on the part.""",
    challenge="""You cannot write down every defect signature by hand, and a defect can appear anywhere on the surface. A
fixed rule at a fixed position misses a mark that shows up in the next frame.""",
    ai_link="""A CNN slides small learned filters across the image, each one firing on a pattern - a feed groove, a
chatter band - wherever it occurs. Early filters find simple edges; later layers combine them into a
defect signature. The features are learned from labeled images, not coded.""",
    notebook="""A 2-D CNN on the surface images, with its filters and feature maps visualized.""",
    contributes="""The first image branch: the finish grader the hand-made threshold could not be.""",
    takeaway="""A CNN learns the defect patterns in an image instead of you coding them.""",
),

# ---------------------------------------------- PHASE 9 - INSPECTING THE TOOL
dict(
    id='tool-chipping', phase=8,
    civil='Finding The Chipped Edge', ai='CNN Detection + Grad-CAM',
    civil_icon='🔩', ai_icon='🎯',
    tech='classify chipped / intact, then show where it looked',
    civil_bullets=['Look at the edge', 'Spot the missing bite', 'Point to it'],
    ai_bullets=['Chipped vs intact', 'Heat-map the evidence', 'Show your working'],
    site="""Turn the camera on the tool itself. An intact cutting edge is clean and straight. A chipped one has a
small bite missing - and once it chips, every part after it is out of tolerance. The machinist checks
the edge between batches by eye.""",
    challenge="""Checking every tool, every batch, is exactly the repetitive watching a person does worst late in a
shift. And a flat pass/fail is not enough: an engineer will not act on a black box that just says
'chipped' without showing where.""",
    ai_link="""A CNN classifies the edge as chipped or intact, and Grad-CAM highlights the pixels that drove the call -
so the heat lands on the chip. The engineer sees not just the verdict but the evidence, and can
overrule it. Detection plus explanation.""",
    notebook="""A CNN on tool-edge images, plus a Grad-CAM overlay locating the chip.""",
    contributes="""The second image branch: catches the failing tool before it scraps the batch.""",
    takeaway="""A CNN can both call the chip and show you where it saw it.""",
),

# ---------------------------------------------- PHASE 10 - THE MACHINING AUDIT
dict(
    id='audit', phase=9,
    civil='The Machining Audit', ai='Confusion Matrix',
    civil_icon='📋', ai_icon='🔲',
    tech='TN / FP / FN / TP on the sealed test passes',
    civil_bullets=['Line up every call', 'Against the measured part', 'Four outcomes'],
    ai_bullets=['Two right boxes', 'Two wrong boxes', 'One miss ships scrap'],
    site="""Audit the model the way you would audit a first-article inspection. A hundred passes happened. The
measured parts say what really came off the machine. The model made a call on each - good part, or
scrap. Line them up and count.""",
    challenge="""Four things can happen, and lumping them together hides the one that matters. Called good, was good:
fine. Called scrap, was scrap: caught it. Called scrap, was actually good: a false reject and a wasted
part. Called good, was scrap: the costly miss - scrap shipped to the customer.""",
    ai_link="""Put those four boxes in a square and you have the confusion matrix - you did not learn it, you audited
the run and it fell out. Never quote accuracy alone: a model that calls everything good scores well and
misses every real defect.""",
    notebook="""The test-set predictions, `ConfusionMatrixDisplay`, and the warning that follows.""",
    contributes="""The acceptance test, run on the passes sealed away at the split.""",
    takeaway="""Accuracy hides the one box that matters - the scrap called good.""",
),
dict(
    id='proof', phase=9,
    civil='Readings vs Images: The Verdict', ai='Where Deep Learning Earns Its Place',
    civil_icon='⚖️', ai_icon='🏁',
    tech='RF vs ANN on readings; threshold vs CNN on the image',
    civil_bullets=['Readings: both fine', 'Image: only one', 'Right tool, right job'],
    ai_bullets=['Numbers: both work', 'Images: only DL', 'Pick the right tool'],
    site="""The verdict, and it is not a vendor's pitch. On the seven named readings an engineer defined, machine
learning and deep learning perform about the same. Not close - the same.""",
    challenge="""So if deep learning does not win on the readings, why learn it? Because of the image. Your hand-made
brightness threshold failed and no limit saved it, and the Random Forest cannot be pointed at a grid of
raw pixels at all.""",
    ai_link="""Here is the thesis, proved rather than claimed. When an engineer has named the features, use machine
learning - simpler, faster, easier to defend. When nobody can name them, as with the surface image, deep
learning is the option that works. AI does not out-think the machinist; it covers the part no one can do
by hand.""",
    notebook="""Random Forest against the ANN on readings, and the image task neither hand-rule could touch.""",
    contributes="""Justifies two branches instead of one model - and stops you reaching for DL on a spreadsheet.""",
    takeaway="""Deep learning earns its place only where nobody can name the features.""",
),

# ---------------------------------------------- PHASE 11 - OPTIMIZATION & FUSION
dict(
    id='optimize', phase=10,
    civil='Finding The Sweet Spot', ai='Constrained Optimization',
    civil_icon='🎯', ai_icon='🧭',
    tech='search speed x feed x depth -> max MRR s.t. finish & tool limits',
    civil_bullets=['Sweep every setting', 'Predict finish & life', 'Pick the fastest safe one'],
    ai_bullets=['Try every setting', 'Score each one', 'Pick the fastest safe cut'],
    site="""Back to the first question. Of all the speed, feed and depth combinations, which one finishes the batch
fastest without breaking the finish tolerance or wearing the tool out early? Trying them on real steel
would cost days and a drawer of tools.""",
    challenge="""The three settings trade off against each other, and the outcome is not obvious. Faster removal usually
means a rougher finish and a shorter tool life. The best point is a balance no single rule gives you,
and it moves with every tolerance you are handed.""",
    ai_link="""Now the trained models earn their keep. Sweep a grid of settings, let the roughness and tool-life models
score every one, keep only those inside your limits, and pick the one with the highest removal rate.
That is constrained optimization - the recommendation the whole system exists to make.""",
    notebook="""A grid search over the parameters, scored by the trained models, returning the optimal setting.""",
    contributes="""Turns prediction into a decision: the actual speed, feed and depth to run.""",
    takeaway="""Search every setting with the model, then pick the fastest one still inside the limits.""",
),
dict(
    id='fusion-engine', phase=10,
    civil='The Machining Control Screen', ai='AI Fusion',
    civil_icon='🎛️', ai_icon='🔗',
    tech='readings + surface CNN + tool CNN -> one recommendation',
    civil_bullets=['Every signal lands here', 'Cross-referenced', 'One call'],
    ai_bullets=['Each model alone: weak', 'Combined: a decision', 'This is the product'],
    site="""Every cell has a control screen. The force and vibration readings on one side, the surface grade from
the camera on another, the tool-edge check beside it. The machinist in the middle does not act on any
one feed - they cross-reference them.""",
    challenge="""Each feed alone is close to noise. The readings say elevated risk - it could be one hard spot in the
bar. The surface CNN flags a mark - it could be one bad frame. The tool looks worn - on a roughing pass
it may be fine. A system that alarms on any one gets switched off in a week.""",
    ai_link="""Now fuse them. Elevated force and vibration, a chatter grade from the surface CNN, and a chip flag from
the tool CNN together are not three weak signals. That is one clear call: back off the feed and change
the tool. Several models, one decision, one machinist who acts.""",
    notebook="""`fusion(readings, surface, tool)` - the control screen as a function.""",
    contributes="""This is the product. Everything before it was a component.""",
    takeaway="""Weak signals, fused, become one clear machining recommendation.""",
),
dict(
    id='pipeline', phase=10,
    civil='The Complete Optimized Cell', ai='The AI Engineering Pipeline',
    civil_icon='🏭', ai_icon='🛤️',
    tech='raw sensors + camera -> models -> fused decision -> setting',
    civil_bullets=['Sensors to setting', 'Every stage in order', 'One flow'],
    ai_bullets=['Load -> clean -> model', '-> evaluate -> fuse', '-> serve'],
    site="""Step back and see the whole cell as one flow: the cut sensed and photographed, readings logged and
cleaned, models trained and audited, signals fused, and a recommended setting handed to the machinist -
who still makes the call.""",
    challenge="""Any single stage done well is worthless if the chain breaks. A perfect model on dirty data, or a great
recommendation nobody acts on, saves no time and no tools. The value is in the whole pipeline.""",
    ai_link="""This is the AI engineering pipeline: ingest, clean, prepare, model, evaluate, fuse, serve. Every page of
this course was one stage of it, in the order a real project runs them.""",
    notebook="""The end-to-end pipeline assembled, from raw log to a served recommendation.""",
    contributes="""Ties every previous step into one deployable system.""",
    takeaway="""The value is the whole pipeline, not any one model in it.""",
),

# ---------------------------------------------- PHASE 12 - THE BUSINESS CASE
dict(
    id='dashboard', phase=11,
    civil='Time, Tools And Scrap Saved', ai='The Optimization Dashboard',
    civil_icon='🖥️', ai_icon='🔔',
    tech='optimized vs baseline -> cycle time, tool cost, scrap in money',
    civil_bullets=['Batch at a glance', 'Fastest safe setting', 'Money saved'],
    ai_bullets=['Every model, one screen', 'Ranked recommendation', 'The business case'],
    site="""The screen the shop manager actually opens. The batch on one view: the setting the system recommends,
the cycle time it gives, the tool life it costs, and the scrap it avoids against how the job was run
before.""",
    challenge="""None of the engineering matters to the business until it is a number a manager can act on: how much
faster the batch runs, how many tools it saves, and how much scrap it prevents this month.""",
    ai_link="""The dashboard is where every model's output becomes a decision and a cost. Move the sliders to your own
batch size and rates and read off the hours, tools and money the optimized setting saves over the
cautious one.""",
    notebook="""The optimized-vs-baseline comparison and the saved-cost calculation.""",
    contributes="""The closing view: the whole system as one screen and one business case.""",
    takeaway="""The dashboard turns every model output into a recommended setting and a saved cost.""",
),
]


# ---------------------------------------------------------------- short labels
SHORT = {
    "shopfloor": "A batch to cut",      "enter-ai": "Continuous monitoring",
    "trial": "One cutting pass",        "two-records": "Reading vs image",
    "load": "Machining log arrives",    "inspect": "Sensor health check",
    "clean": "Dropouts & spikes",       "normalize": "Standardize units",
    "split": "Trial vs acceptance",     "ml-baseline": "Finish & tool life",
    "surface-problem": "The raw image", "handmade": "Threshold by hand",
    "why-dl": "Rulebook fails",         "machinist-brain": "Machinist decides",
    "neuron": "Weighing signals",       "activation": "Reject threshold",
    "learning-loop": "Learn from scrap", "gradient-descent": "Dial it in",
    "network": "Process team",          "training": "Run the trials",
    "cnn-journey": "Read the surface",  "tool-chipping": "Find the chip",
    "audit": "Machining audit",         "proof": "The verdict",
    "optimize": "The sweet spot",       "fusion-engine": "Control screen",
    "pipeline": "The whole cell",       "dashboard": "Savings ledger",
}
for _s in STEPS:
    _s["short"] = SHORT[_s["id"]]

# --------------------------------------------------------------- lookups
BY_ID = {s["id"]: s for s in STEPS}
ORDER = [s["id"] for s in STEPS]


def _phase_steps(pi):
    return [s for s in STEPS if s["phase"] == pi]


def goto(stage):
    st.query_params["stage"] = stage
    st.rerun()


# ============================================================================
# THE BRIDGE FIGURE
# Left = the shop (amber). Right = the AI (cyan). Between them an animated
# arrow, and under it the technical process (violet).
# ============================================================================
def _wrap(text, width=24):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if len(t) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return "<br>".join(lines)


def _corner_ticks(fig, x0, x1, y0, y1, color, dx=0.16, dy=0.22):
    """Blueprint registration marks at the four corners of a rect."""
    for cx, sx in ((x0, 1), (x1, -1)):
        for cy, sy in ((y0, 1), (y1, -1)):
            fig.add_shape(type="line", x0=cx, y0=cy, x1=cx + sx * dx, y1=cy,
                          line=dict(color=color, width=2), layer="above")
            fig.add_shape(type="line", x0=cx, y0=cy, x1=cx, y1=cy + sy * dy,
                          line=dict(color=color, width=2), layer="above")


def _card(fig, x0, x1, color, icon, title, bullets, kicker):
    fig.add_shape(type="rect", x0=x0, x1=x1, y0=0.8, y1=5.35,
                  line=dict(color=EDGE, width=1), fillcolor=STEEL, layer="below")
    _corner_ticks(fig, x0, x1, 0.8, 5.35, color)
    cx = (x0 + x1) / 2
    fig.add_annotation(x=cx, y=4.98, text=f"◤ {kicker}", showarrow=False,
                       font=dict(size=11, color=color, family=MONOF), xanchor="center")
    fig.add_annotation(x=cx, y=4.18, text=icon, showarrow=False,
                       font=dict(size=34), xanchor="center")
    fig.add_annotation(x=cx, y=3.28, text=f"<b>{_wrap(title)}</b>", showarrow=False,
                       font=dict(size=14, color=TEXT), xanchor="center", align="center")
    for i, b in enumerate(bullets):
        fig.add_annotation(x=cx, y=2.45 - i * 0.52, text=f"› {b}", showarrow=False,
                           font=dict(size=12, color=MUTED, family=MONOF), xanchor="center")


def bridge_figure(step, style, animate):
    """The machining-activity -> AI-equivalent -> technical-process bridge,
    drawn as an industrial signal-flow block diagram."""
    fig = go.Figure()
    _card(fig, 0.2, 3.4, CIVIL, step["civil_icon"], step["civil"],
          step["civil_bullets"], "ON THE MACHINE")
    _card(fig, 6.6, 9.8, AISIDE, step["ai_icon"], step["ai"],
          step["ai_bullets"], "IN THE AI")

    # a double-line signal bus between the blocks
    for yy in (3.06, 2.94):
        fig.add_shape(type="line", x0=3.45, y0=yy, x1=6.35, y1=yy,
                      line=dict(color=EDGE, width=1.5), layer="below")
    fig.add_annotation(x=6.55, y=3.0, ax=6.3, ay=3.0, xref="x", yref="y",
                       axref="x", ayref="y", showarrow=True, arrowhead=2,
                       arrowsize=1.6, arrowwidth=2.5, arrowcolor=AISIDE, text="")
    fig.add_annotation(x=4.9, y=3.55, text="⇒ TRANSFORM ⇒", showarrow=False,
                       font=dict(size=11, color=MUTED, family=MONOF))

    # the compute block (violet), with corner ticks
    fig.add_shape(type="rect", x0=3.5, x1=6.5, y0=1.25, y1=2.15,
                  line=dict(color=EDGE, width=1), fillcolor=INK, layer="below")
    _corner_ticks(fig, 3.5, 6.5, 1.25, 2.15, TECH, dx=0.14, dy=0.14)
    fig.add_annotation(x=5.0, y=1.98, text="⌗ COMPUTE", showarrow=False,
                       font=dict(size=9, color=TECH, family=MONOF))
    fig.add_annotation(x=5.0, y=1.58, text=step["tech"], showarrow=False,
                       font=dict(size=10, color=TEXT, family=MONOF), xanchor="center", align="center")
    fig.add_annotation(x=5.0, y=2.42, text="▼", showarrow=False,
                       font=dict(size=13, color=TECH))

    # a machined "chip" token travels the bus from shop to AI
    fig.add_trace(go.Scatter(x=[3.5], y=[3.0], mode="markers",
                             marker=dict(size=13, color=CIVIL, symbol="square",
                                         line=dict(color=INK, width=1)),
                             hoverinfo="skip", showlegend=False))
    frames = []
    for i in range(24):
        t = i / 23
        x = 3.5 + t * 2.85
        c = CIVIL if t < 0.45 else (TEXT if t < 0.55 else AISIDE)
        frames.append(go.Frame(data=[go.Scatter(
            x=[x], y=[3.0], mode="markers",
            marker=dict(size=13, color=c, symbol="square", line=dict(color=INK, width=1)))]))
    animate(fig, frames, ms=90)

    fig.update_xaxes(visible=False, range=[0, 10])
    fig.update_yaxes(visible=False, range=[0.5, 5.85])
    return style(fig, h=360)


# ============================================================================
# NAVIGATION - previous / current / next ENGINEERING step
# ============================================================================
def _nav_strip(step, key):
    i = ORDER.index(step["id"])
    prev_s = BY_ID[ORDER[i - 1]] if i > 0 else None
    next_s = BY_ID[ORDER[i + 1]] if i < len(ORDER) - 1 else None
    c1, c2, c3 = st.columns([1, 1.25, 1])
    with c1:
        if prev_s:
            if st.button(f"◀  {prev_s['civil']}", key=f"prev_{key}",
                         use_container_width=True):
                goto(prev_s["id"])
        else:
            if st.button("◀  The project overview", key=f"prev_{key}",
                         use_container_width=True):
                goto("start")
    with c2:
        st.markdown(
            f"<div class='trav'>▐ STEP {i+1:02d} / {len(ORDER):02d} ▌"
            f"<br><b>{step['civil']}</b></div>",
            unsafe_allow_html=True)
    with c3:
        if next_s:
            if st.button(f"{next_s['civil']}  ▶", key=f"next_{key}",
                         use_container_width=True):
                goto(next_s["id"])
        else:
            if st.button("Back to the overview  ▶", key=f"next_{key}",
                         use_container_width=True):
                goto("start")


# ============================================================================
# open_page  -  Parts 1, 2 and 3, rendered ABOVE the existing stage renderer
# ============================================================================
def open_page(stage, style, animate):
    step = BY_ID.get(stage)
    if step is None:
        return
    pname, pdesc = PHASES[step["phase"]]

    _nav_strip(step, "top")
    i = ORDER.index(stage)
    st.markdown(
        f"<div class='dro-bar' style='margin-top:14px'>⟨CNC-OPT⟩ &nbsp; "
        f"STEP {i+1:02d}/{len(ORDER)} &nbsp;·&nbsp; PHASE {step['phase']+1:02d}/{len(PHASES)} "
        f"&nbsp;·&nbsp; <span style='color:{CIVIL}'>{pname.upper()}</span> "
        f"&nbsp;—&nbsp; {pdesc}</div>", unsafe_allow_html=True)
    st.markdown(f"# {step['civil_icon']}  {step['civil']}")
    st.markdown(
        f"<span class='substep'>▸ this machining step is the AI concept </span>"
        f"<b style='color:{AISIDE}'>{step['ai']}</b>",
        unsafe_allow_html=True)
    st.divider()

    # ---- OP.10  Machining Engineering -------------------------------------
    _op_header("10", "Machining Engineering", CIVIL)
    st.markdown(f"<div class='spec civil'>{step['site']}</div>", unsafe_allow_html=True)
    st.write("")

    # ---- OP.20  The Challenge ---------------------------------------------
    _op_header("20", "The Challenge", RED)
    st.markdown(f"<div class='spec warn'>{step['challenge']}</div>", unsafe_allow_html=True)
    st.write("")

    # ---- OP.30  AI Connection ---------------------------------------------
    _op_header("30", "AI Connection", AISIDE)
    st.markdown(f"<div class='spec ai'>{step['ai_link']}</div>", unsafe_allow_html=True)
    st.plotly_chart(bridge_figure(step, style, animate), use_container_width=True,
                    key=f"bridge_{stage}")
    st.caption("▶ Press Play — the machined token travels the bus from the machine into the AI.")
    st.divider()

    # ---- OP.40  Technical Idea header -------------------------------------
    _op_header("40", "Technical Idea", TECH)
    st.caption(f"{step['tech']} — interactive. Change things and watch what happens.")


# ============================================================================
# close_page  -  Part 5, rendered BELOW the existing stage renderer
# ============================================================================
def close_page(stage):
    step = BY_ID.get(stage)
    if step is None:
        return
    st.divider()

    _op_header("50", "Key Takeaway", GREEN)
    st.markdown(f"<div class='spec ok' style='font-size:19px;font-weight:600;line-height:1.5'>"
                f"{step['takeaway']}</div>", unsafe_allow_html=True)
    st.write("")

    _op_header("60", "In the Notebook", "#8bc34a")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Where you implement it**\n\n{step['notebook']}")
    with c2:
        st.markdown(f"**What it contributes**\n\n{step['contributes']}")

    render_quiz(stage)

    st.write("")
    segs = []
    for i, (pname, _) in enumerate(PHASES):
        cls = "cur" if i == step["phase"] else ("done" if i < step["phase"] else "")
        segs.append(f"<span class='ph {cls}' title='{pname}'>{i+1:02d}</span>")
    st.markdown(
        f"<div class='travbar'><span class='travlab'>TRAVELER</span>"
        + "".join(segs)
        + f"<span class='travlab' style='margin-left:auto'>PH {step['phase']+1:02d}/{len(PHASES)}"
        f" · {PHASES[step['phase']][0].upper()}</span></div>", unsafe_allow_html=True)
    st.write("")
    _nav_strip(step, "bottom")


# ============================================================================
# CHECK-YOUR-UNDERSTANDING QUIZ  (one question per stage, shown by close_page)
# Each entry: q = question, options = choices, answer = index of the correct
# option, why = the explanation shown after any answer is picked.
# ============================================================================
QUIZ = {
    'shopfloor': dict(
        q="Why does choosing the cutting speed, feed and depth call for AI rather than a machinist's judgement alone?",
        options=["AI cuts metal more accurately than a lathe",
                 "The fast, safe setting is one point hidden among thousands of combinations — too many to try by hand, and it moves with the material, tool and machine",
                 "Machinists are no longer allowed to set parameters",
                 "AI removes the need for cutting tools"],
        answer=1,
        why="There is one fast, safe setting hidden among thousands. That search is too large to do by hand, which is the only reason AI belongs at the machine."),
    'enter-ai': dict(
        q="Once the sensors and camera are added, who decides whether a part is fit to ship?",
        options=["The AI model, automatically",
                 "The sensors, when a threshold is crossed",
                 "The machinist — the system only recommends and flags",
                 "Whichever model reports the highest confidence"],
        answer=2,
        why="Nothing about the machining changes. The system recommends and flags; a person decides and signs off. That split drives every later choice, especially the machining audit."),
    'trial': dict(
        q="What does the roughness-and-tool-life model actually receive from one trial pass?",
        options=["A live feed from the spindle",
                 "A single row of numbers — the settings, the sensor readings, and the measured outcome",
                 "The machinist's spoken notes about the cut",
                 "A video of the whole cut"],
        answer=1,
        why="The model never stands at the machine and cannot re-run the cut. It gets one row; a mis-logged feed or a saturated force channel gives a wrong prediction with no way to notice."),
    'two-records': dict(
        q="Why does one machined part need two different kinds of model?",
        options=["To make the system run twice as fast",
                 "The seven readings are named columns an engineer defined; the surface photo is thousands of unnamed pixels where a chatter mark lives in the pattern, not in any one number",
                 "Because one model would cost too much",
                 "Because images and numbers use different file formats"],
        answer=1,
        why="One part, two records. A roughness value already means something; the photo means nothing until it is processed. Named readings and a surface image are two different problems."),
    'load': dict(
        q="Why check the raw machining log (row and column counts, types) before building any model?",
        options=["To make the file smaller",
                 "Because a model trained on wrong data does not error — it trains happily and gives wrong answers",
                 "It is required before a CNC job can run",
                 "To delete duplicate machines"],
        answer=1,
        why="Loading a dataset is a commissioning check. Establish what actually arrived — how many passes, what type each column is — because silent bad data produces confidently wrong models."),
    'inspect': dict(
        q="How do you find a stuck or dead sensor hidden in 1,400 machining passes?",
        options=["Read every row by eye",
                 "Count missing values per channel and plot each column's distribution — the fault spikes or flat-lines",
                 "Trust the sensor's own status light",
                 "Retrain the model until it works"],
        answer=1,
        why="You cannot eyeball 1,400 passes. Counts and distributions make a dropout or a frozen channel announce itself. This step diagnoses only — nothing is repaired here."),
    'clean': dict(
        q="Why is deciding what to drop or fill a judgement call rather than a fixed rule?",
        options=["Because cleaning never affects the model",
                 "Drop every flawed pass and little is left to learn from; keep a dead-probe zero and the model learns a violent cut can read zero vibration — everything downstream inherits the choice",
                 "Because the computer decides automatically",
                 "Because all readings are equally trustworthy"],
        answer=1,
        why="A cutting force of 9,999 N is a saturated channel; a vibration of zero on a running cut is a dead probe. No rule decides it for you, and the tabular model, the CNN and the fusion engine all inherit whatever you decide."),
    'normalize': dict(
        q="Why put force, feed and temperature on a common 0–1 scale before training a neural network?",
        options=["To save memory",
                 "A network reads magnitude, not meaning — raw force in the hundreds would swamp a 0.1 mm/rev rise in feed that actually drives the finish",
                 "Because 0–1 numbers look nicer",
                 "So the columns fit on the screen"],
        answer=1,
        why="A network cannot tell a big number from an important one. Scaling every channel to 0–1 lets importance be learned from the data, not from the units."),
    'split': dict(
        q="Why must the model be scored on passes it never trained on?",
        options=["To use up the spare data",
                 "A model tested on its training passes just recites what it memorised and proves nothing about the next part off the machine",
                 "Because the test set is cleaner",
                 "It is not necessary if accuracy is high"],
        answer=1,
        why="Never test someone on the exact work they practised on. Only a score on the sealed acceptance passes says anything about the next cut, and it is what makes the machining audit mean anything."),
    'ml-baseline': dict(
        q="What do you actually give the Random Forest, and what does it work out?",
        options=["The equations for roughness; it just plugs in numbers",
                 "The named factors (speed, feed, depth, force, vibration, temperature, current) plus 1,400 outcomes; it learns the mapping to roughness and tool life itself",
                 "A photo of the part; it reads the finish",
                 "Nothing — it guesses randomly"],
        answer=1,
        why="You state the factors — an engineer already named them — not the equations. Given those columns and thousands of outcomes, the model learns the mapping, and the optimizer later searches over it."),
    'surface-problem': dict(
        q="Where, exactly, is the defect in a surface image?",
        options=["In one specific dark pixel",
                 "In a column labelled 'defect'",
                 "In a pattern — chatter bands or tearing spread across thousands of pixels, held by no single number",
                 "It cannot be seen at all"],
        answer=2,
        why="A defect is a pattern, not a value. Nothing in the raw image is pre-named, which is why the Random Forest cannot use it and the CNN is built for it."),
    'handmade': dict(
        q="Why does rejecting parts on average brightness fail as a finish detector?",
        options=["Brightness is impossible to compute",
                 "A chatter fault can share the same average brightness as a good finish while its pattern is completely different — one number throws away the distinguishing pattern",
                 "The camera is broken",
                 "Averages are always exactly 0.5"],
        answer=1,
        why="Reducing an image to one hand-picked number discards the pattern that separates defect from sound. Every hand-made feature is a brittle rule you must maintain, and each keeps only a sliver of the picture."),
    'why-dl': dict(
        q="When is deep learning the right tool over machine learning?",
        options=["Whenever you have a lot of data",
                 "When nobody can name the features — as with the raw surface image",
                 "Always; DL beats ML on everything",
                 "Only when the model must run fast"],
        answer=1,
        why="DL does not dig deeper into named readings — ML already handles those. It earns its place where there are no named features at all, and it learns them from labelled examples."),
    'machinist-brain': dict(
        q="A machinist weighs vibration, force and temperature, sums them, and makes one call. That process is essentially…",
        options=["A spreadsheet",
                 "A single artificial neuron",
                 "A database query",
                 "A random guess"],
        answer=1,
        why="Weigh each input, sum, decide — that is exactly one neuron. The weights are what the machinist's years of experience become."),
    'neuron': dict(
        q="What is a neuron's forward step, z = w·x + b?",
        options=["A weighted sum of the inputs plus a bias offset",
                 "The average of the inputs",
                 "The largest input value",
                 "A random number generator"],
        answer=0,
        why="Each reading is multiplied by its weight, the products are summed, and a bias is added. This is the single computation every layer of every network repeats."),
    'activation': dict(
        q="Why pass the neuron's score z through a non-linear activation like sigmoid?",
        options=["To make training slower",
                 "It turns a raw score into a smooth 0–1 decision and lets stacked neurons bend — without it the network stays a straight line",
                 "To round the number to an integer",
                 "It has no real effect"],
        answer=1,
        why="A hard cut-off flips on one point of noise; sigmoid ramps up smoothly. And without a non-linearity, stacking neurons learns nothing curved."),
    'learning-loop': dict(
        q="Stripped of terminology, what is 'learning'?",
        options=["Memorising every example perfectly",
                 "Predict, measure the error against the measured outcome, adjust to be less wrong, and repeat",
                 "Copying another model",
                 "Adding more sensors"],
        answer=1,
        why="Done by hand this loop takes a career and lives in one head. Training runs the same loop thousands of times a second, and the lesson lives in the weights."),
    'gradient-descent': dict(
        q="What does the learning rate (step size) control during gradient descent?",
        options=["How many sensors are used",
                 "How big a step each weight takes downhill — too big overshoots, too small crawls",
                 "The number of layers",
                 "The colour of the loss curve"],
        answer=1,
        why="Loss says how wrong; the gradient says which way; the step size says how far. Too large and it bounces past the minimum; too small and it never settles."),
    'network': dict(
        q="Why stack neurons into layers instead of using just one?",
        options=["To use more memory",
                 "One neuron can only split the world with a straight line; layers compose simple signals into the curved patterns real defects make",
                 "Layers make the maths simpler",
                 "There is no reason; one neuron is always enough"],
        answer=1,
        why="Fast-and-light means one thing, fast-and-deep another. Depth lets the network hold decisions one straight-line neuron cannot."),
    'training': dict(
        q="The training loss falls fast, then flattens. What does running many more epochs eventually cause?",
        options=["The model gets steadily better forever",
                 "The model starts memorising the training passes — overfitting — while held-out error stops improving",
                 "The sensors recalibrate",
                 "The loss becomes negative"],
        answer=1,
        why="More epochs on the same passes only memorise them. You stop when the held-out error stops falling, not when the training loss hits zero."),
    'cnn-journey': dict(
        q="Where do a CNN's finish-detecting filters come from?",
        options=["An engineer writes each filter by hand",
                 "They are learned from labelled surface images during training",
                 "They are fixed and identical in every CNN",
                 "They are downloaded from the camera"],
        answer=1,
        why="A CNN slides small learned filters across the image, firing on feed grooves or chatter bands wherever they occur — the rule the hand-made brightness threshold could not be."),
    'tool-chipping': dict(
        q="A CNN already says 'chipped'. What does Grad-CAM add?",
        options=["A higher accuracy score",
                 "It highlights the pixels that drove the call, so the engineer sees the evidence — the heat lands on the chip — and can overrule it",
                 "It removes the chip from the image",
                 "It makes the model run faster"],
        answer=1,
        why="An engineer will not act on a black box that just says 'chipped'. Grad-CAM shows where it looked, giving verdict plus evidence — and it catches the failing tool before it scraps the batch."),
    'audit': dict(
        q="On the confusion matrix, which box is the costly one, and why not quote accuracy alone?",
        options=["False rejects; they waste parts",
                 "Called good but was scrap — the miss that ships scrap to the customer; a model calling everything good scores high on accuracy yet misses every real defect",
                 "Called scrap and was scrap; it means the model works",
                 "There is no costly box"],
        answer=1,
        why="Accuracy hides the false-negative box. Scrap called good is shipped to the customer, so that box must be reported separately from the overall score."),
    'proof': dict(
        q="What did comparing ML and DL prove about when to use each?",
        options=["Deep learning always wins",
                 "On the seven named readings ML and DL perform about the same; DL earns its place only on the image, where no one can name the features",
                 "Machine learning always wins",
                 "Neither works on machined parts"],
        answer=1,
        why="When an engineer has named the features, use ML — simpler, faster, easier to defend. When nobody can, as with the surface image, deep learning is the option that works."),
    'optimize': dict(
        q="How does the system find the best speed, feed and depth to run?",
        options=["It picks the fastest setting regardless of finish or tool wear",
                 "It sweeps a grid of settings, lets the roughness and tool-life models score each, keeps only those inside the finish and tool limits, and picks the one with the highest removal rate",
                 "It reuses whatever setting the last job used",
                 "It averages all the settings that have ever been tried"],
        answer=1,
        why="This is constrained optimization: search every candidate, discard the ones that break a limit, and choose the fastest feasible cut. Trying them on real steel would cost days and a drawer of tools; the trained models do it in software."),
    'fusion-engine': dict(
        q="Why fuse the readings, the surface grade and the tool check instead of alarming on each one?",
        options=["To reduce the number of sensors",
                 "Each feed alone is close to noise and a system that alarms on any one gets switched off; fused, elevated force plus a chatter grade plus a chip flag become one clear call",
                 "Fusion makes each model more accurate on its own",
                 "So only one model has to run"],
        answer=1,
        why="A hard spot in the bar, one bad frame, or a worn roughing tool can each trip a single feed. Together they are not three weak signals — they are one decision: back off the feed and change the tool."),
    'pipeline': dict(
        q="Where does the value of the optimized cell actually live?",
        options=["In the single best model",
                 "In the whole pipeline — ingest, clean, prepare, model, evaluate, fuse, serve — because a break anywhere saves no time and no tools",
                 "In having the most sensors",
                 "In the dashboard colours"],
        answer=1,
        why="A perfect model on dirty data, or a great recommendation nobody acts on, saves nothing. Any single stage done well is worthless if the chain breaks."),
    'dashboard': dict(
        q="What turns the machining models into a business case the shop manager can act on?",
        options=["Reporting the model's accuracy percentage",
                 "Comparing the optimized setting against the old one in money — the cycle time saved, the tools saved, and the scrap prevented this month",
                 "Adding more cameras to the cell",
                 "Running every batch at maximum speed"],
        answer=1,
        why="None of the engineering matters to the business until it is a number a manager can act on. The dashboard turns every model output into a recommended setting and a saved cost."),
}


def render_quiz(stage):
    """One check-your-understanding MCQ per stage. Portable across all four
    apps — self-contained, no theme-specific helpers."""
    q = QUIZ.get(stage)
    if not q:
        return
    st.write("")
    st.markdown("##### 📝 Check your understanding")
    st.markdown(f"**{q['q']}**")
    choice = st.radio("Select an answer", q['options'], index=None,
                      key=f"quiz_{stage}", label_visibility="collapsed")
    if choice is not None:
        correct = q['options'][q['answer']]
        if choice == correct:
            st.success(f"✅ Correct. {q['why']}")
        else:
            st.error(f"❌ Not quite — the answer is **{correct}**.\n\n{q['why']}")


# ============================================================================
# THE INTERACTIVE ENGINEERING MIND MAP
# A vertical spine of the shop's phases. Every node opens that learning page.
# ============================================================================
def mind_map(style):
    fig = go.Figure()
    n = len(PHASES)
    ys = {i: (n - 1 - i) * 1.0 for i in range(n)}

    for i in range(n - 1):
        fig.add_annotation(x=0, y=ys[i + 1] + 0.42, ax=0, ay=ys[i] - 0.42,
                           xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1.1,
                           arrowwidth=2, arrowcolor=CIVIL, text="")

    GAP = 2.35
    X0 = 1.4

    sx, sy, stext, scustom, shover = [], [], [], [], []
    for pi, (pname, pdesc) in enumerate(PHASES):
        kids = _phase_steps(pi)
        for k, s in enumerate(kids):
            fig.add_shape(type="line", x0=0.25, y0=ys[pi], x1=X0 + k * GAP, y1=ys[pi],
                          line=dict(color="#2b323c", width=1.2, dash="dot"), layer="below")
        fig.add_annotation(x=0, y=ys[pi], text=f"<b>OP {pi+1:02d}</b>", showarrow=False,
                           font=dict(size=11, color=BG, family=MONOF),
                           bgcolor=CIVIL, bordercolor=CIVIL, borderpad=5, borderwidth=2)
        fig.add_annotation(x=-0.45, y=ys[pi], text=f"<b>{pname}</b>", showarrow=False,
                           xanchor="right", font=dict(size=13, color=CIVIL))
        fig.add_annotation(x=-0.45, y=ys[pi] - 0.30, text=_wrap(pdesc, 30),
                           showarrow=False, xanchor="right", yanchor="top",
                           align="right", font=dict(size=10, color=MUTED))
        for k, s in enumerate(kids):
            sx.append(X0 + k * GAP)
            sy.append(ys[pi])
            stext.append(f"{s['civil_icon']} {s['short']}")
            scustom.append(s["id"])
            shover.append(f"<b>{s['civil']}</b><br>"
                          f"<span style='color:{AISIDE}'>= {s['ai']}</span><br>"
                          f"<i>click to open</i>")

    fig.add_trace(go.Scatter(
        x=sx, y=sy, mode="markers+text", text=stext, textposition="top center",
        textfont=dict(size=10, color=TEXT), customdata=scustom,
        marker=dict(size=20, color=INK, line=dict(color=AISIDE, width=2),
                    symbol="hexagon"),
        hovertemplate="%{hovertext}<extra></extra>", hovertext=shover,
        showlegend=False))

    fig.update_xaxes(visible=False, range=[-5.9, X0 + 6 * GAP + 1.5])
    fig.update_yaxes(visible=False, range=[-0.8, n - 0.05])
    return style(fig, h=1040)


# ============================================================================
# THE MACHINING-ENGINEERING-TO-AI MAPPING
# Left column: the machining process. Right column: the AI process.
# ============================================================================
def mapping_figure(style):
    fig = go.Figure()
    n = len(STEPS)
    for i, s in enumerate(STEPS):
        y = (n - 1 - i) * 1.0
        fig.add_shape(type="rect", x0=0, x1=3.6, y0=y - 0.36, y1=y + 0.36,
                      line=dict(color=EDGE, width=1), fillcolor=STEEL, layer="below")
        fig.add_shape(type="line", x0=0, y0=y - 0.36, x1=0, y1=y + 0.36,
                      line=dict(color=CIVIL, width=3), layer="above")
        fig.add_annotation(x=0.18, y=y, text=f"{s['civil_icon']} {s['civil']}",
                           showarrow=False, xanchor="left",
                           font=dict(size=11.5, color=TEXT))
        fig.add_annotation(x=4.1, y=y, text="»", showarrow=False,
                           font=dict(size=16, color=MUTED, family=MONOF))
        fig.add_shape(type="rect", x0=4.6, x1=8.2, y0=y - 0.36, y1=y + 0.36,
                      line=dict(color=EDGE, width=1), fillcolor=STEEL, layer="below")
        fig.add_shape(type="line", x0=8.2, y0=y - 0.36, x1=8.2, y1=y + 0.36,
                      line=dict(color=AISIDE, width=3), layer="above")
        fig.add_annotation(x=4.78, y=y, text=f"{s['ai_icon']} {s['ai']}",
                           showarrow=False, xanchor="left",
                           font=dict(size=11.5, color=TEXT))
        fig.add_annotation(x=8.4, y=y, text=f"OP{s['phase']+1:02d}", showarrow=False,
                           xanchor="left", font=dict(size=9, color="#3f4650", family=MONOF))

    fig.add_annotation(x=0, y=n - 0.35, text="◤ MACHINING ENGINEERING PROCESS",
                       showarrow=False, xanchor="left",
                       font=dict(size=12, color=CIVIL, family=MONOF))
    fig.add_annotation(x=4.6, y=n - 0.35, text="◤ THE AI PROCESS THAT SOLVES IT",
                       showarrow=False, xanchor="left",
                       font=dict(size=12, color=AISIDE, family=MONOF))

    fig.update_xaxes(visible=False, range=[-0.2, 9.0])
    fig.update_yaxes(visible=False, range=[-0.8, n + 0.2])
    return style(fig, h=1160)


# ============================================================================
# THE OPENING PAGE
# ============================================================================
def render_start(style, animate):
    st.markdown(
        f"<div class='brief'>"
        f"<div class='brief-bar'>PROJECT BRIEF · DWG CNC-OPT-001 · REV A · {len(PHASES)} PHASES / {len(STEPS)} OPS</div>"
        f"<div style='font-size:32px;font-weight:800;color:{TEXT}'>🛠️ &nbsp;A CNC Machining Optimization Problem</div>"
        f"<div style='color:{MUTED};font-size:16px;line-height:1.6;margin-top:8px'>"
        f"Cutting a batch fast without wrecking the tool or the finish means trying more settings than one "
        f"machinist can test by hand. AI shows up here because the machining work needs it.</div></div>",
        unsafe_allow_html=True)
    st.write("")

    # ---------------------------------------------- SECTION 1: THE PROBLEM
    _op_header("01", "The Engineering Problem", CIVIL)
    st.markdown("""
A CNC lathe has a batch of steel parts to cut. Before the first cut, the machinist picks three numbers:
**cutting speed, feed rate and depth of cut**. Set them high and the batch finishes fast; set them too
high and the tool overheats and chips, the finish goes bad, and parts are scrapped. One machinist cannot
try every mix of speed, feed and depth by hand, so the job is to find the setting that cuts fastest
without spoiling the finish or the tool.
    """)
    st.divider()

    # ---------------------------------------------- SECTION 2: THE GOAL
    _op_header("02", "What We Are Going To Build", CIVIL)
    st.markdown("An **AI machining optimization system**. Concretely, four parts:")
    c1, c2, c3, c4 = st.columns(4)
    for col, (icon, title, body) in zip(
        (c1, c2, c3, c4),
        [("📟", "Sensors read the cut",
          "Cutting force, vibration, temperature and spindle current. Sampled continuously, on every "
          "pass, not just the first part."),
         ("📷", "The camera reads the result",
          "The machined surface and the tool edge, where a chatter mark or a chip hides in the image - not "
          "in any single gauge reading."),
         ("🧭", "AI finds the sweet spot",
          "Predict surface roughness and tool life, then search every setting for the one that removes "
          "metal fastest while staying inside the limits."),
         ("🔔", "The machinist gets a recommendation",
          "Not a black box. A clear call: run speed 180, feed 0.18, depth 1.5 - this finish, this tool "
          "life - and a flag when a cut goes bad.")]):
        with col:
            st.markdown(
                f"<div class='spec civil' style='height:100%'>"
                f"<div class='card-ico'>{icon}</div>"
                f"<b style='color:{TEXT}'>{title}</b><br>"
                f"<span class='muted'>{body}</span></div>",
                unsafe_allow_html=True)
    st.write("")
    st.markdown(
        f"<div style='border-left:3px solid {GREEN};padding:8px 0 8px 16px;font-size:16px;"
        f"color:{TEXT};line-height:1.65'>The machinist stays in charge and stays accountable. The system "
        f"handles the part one person cannot do alone: it searches every setting and watches every cut. "
        f"The goal is a <b>more productive</b> shop.</div>", unsafe_allow_html=True)
    st.divider()

    # ---------------------------------------------- SECTION 3: MIND MAP
    _op_header("03", "The Engineering Workflow", CIVIL)
    st.markdown(
        f"<div style='color:{MUTED};font-size:15px;line-height:1.6'>These are the {len(PHASES)} phases of "
        f"<b>one machining-optimization project</b>, in the order a real project runs them — from the first "
        f"trial cut to a recommended setting and the time it saves. "
        f"Every <b style='color:{CIVIL}'>amber node</b> is a machining activity. Every "
        f"<b style='color:{AISIDE}'>step hanging off it</b> is a page. "
        f"<b>Click any step to open it.</b></div>", unsafe_allow_html=True)
    st.write("")

    fig = mind_map(style)
    try:
        ev = st.plotly_chart(fig, use_container_width=True, key="mindmap",
                             on_select="rerun", selection_mode="points")
        pts = (ev or {}).get("selection", {}).get("points", [])
        if pts:
            cd = pts[0].get("customdata")
            target = cd[0] if isinstance(cd, list) else cd
            if target in BY_ID:
                goto(target)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, key="mindmap_static")
        st.info("Click-to-open needs Streamlit ≥ 1.35. Use the sidebar to jump to a step.")
    st.divider()

    # ---------------------------------------------- SECTION 4: THE MAPPING
    _op_header("04", "Engineering → AI, The Whole Map", AISIDE)
    st.markdown(
        f"<div style='color:{MUTED};font-size:15px;line-height:1.6'><b>Every AI concept here is a machining "
        f"activity you already understand</b> — the same thing, named differently by a different "
        f"profession. Read down the amber column and you have described a machining project. Read down the "
        f"cyan column and you have described a deep learning pipeline. They are the same column.</div>",
        unsafe_allow_html=True)
    st.write("")
    st.plotly_chart(mapping_figure(style), use_container_width=True, key="mapping")

    st.markdown(
        f"<div style='border-left:3px solid {AISIDE};padding:8px 0 8px 16px;font-size:16px;"
        f"color:{TEXT};line-height:1.65'>Each AI concept shows up because the machining work ran into "
        f"something one machinist could not do by hand. Only then does it get a technical name.</div>",
        unsafe_allow_html=True)
    st.write("")

    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("▶  Start: walk up to the machine", use_container_width=True,
                     type="primary"):
            goto("shopfloor")
    with c2:
        st.caption(f"{len(PHASES)} phases · {len(STEPS)} steps · one machining-optimization project. "
                   "Every step opens with the machining activity, then the AI it becomes.")
