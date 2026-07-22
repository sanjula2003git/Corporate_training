"""
bridge.py - the Structural-Engineering -> AI teaching scaffold.
===============================================================
This module does not teach any NEW concept and it does not render any new
model, animation or asset. Every technical illustration lives in app.py /
story.py. This module wraps each stage renderer in a five-part structure so a
Civil / Structural Engineering student always sees, on every page:

    Structural Engineering   the on-bridge context       (bridge.open_page)
    The Challenge            why the manual way runs out  (bridge.open_page)
    AI Connection            + the bridge figure          (bridge.open_page)
    Technical Idea           <- the EXISTING renderer, untouched
    Key Takeaway             one sentence                 (bridge.close_page)
    In the Notebook          where it lives               (bridge.close_page)

Text is deliberately short and professional. Short sentences, active voice, no
drama. The visuals carry the page; the text supports them.

COLOR IS A TEACHING DEVICE. Amber is ALWAYS the structural / civil world.
Cyan is ALWAYS the AI world. Violet is ALWAYS the technical process.
"""
import streamlit as st
import plotly.graph_objects as go

# ---------------------------------------------------------------- palette
BG, PANEL = "#0e1117", "#161b22"
CIVIL = "#ffb74d"      # amber  - the bridge / structural engineering
AISIDE = "#4fc3f7"     # cyan   - the AI
TECH = "#ba68c8"       # violet - the technical process
GREEN, RED = "#66bb6a", "#ef5350"
MUTED, TEXT = "#8b949e", "#e6edf3"

# ---- Digital-twin display language (monitoring console / structural blueprint)
# Same amber/cyan/violet theme; a distinct LOOK from the sibling apps: monospace
# telemetry readouts, bracketed monitoring-station labels, corner-tick spec
# cards, a faint blueprint grid and a survey-run progress rail.
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
    """Load the digital-twin display language once. Call after st.set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def _op_header(op, label, color):
    st.markdown(
        f"<div class='op-row'>"
        f"<span class='op-num' style='color:{color};border-color:{color}'>PT·{op}</span>"
        f"<span class='op-label' style='color:{color}'>{label}</span>"
        f"<span class='op-rule'></span></div>", unsafe_allow_html=True)


# ============================================================================
# THE ENGINEERING WORKFLOW
# The phases of standing up a bridge digital twin for predictive SHM. Every AI
# concept hangs off one of them. The last one is the ledger the work is judged by.
# ============================================================================
PHASES = [
    ("The Bridge In Service",     "Traffic never stops, deterioration never stops, and inspection is once every year or two."),
    ("A Single Reading",          "One sensor sweep becomes a record of the bridge's state at that instant."),
    ("Instrumenting The Bridge",  "Sensors are fitted, and the structure becomes a continuous data stream."),
    ("Preparing The Data",        "Bad readings are removed, every channel is scaled, and the data is split."),
    ("Condition From Readings",   "A model estimates component condition from the sensor readings alone."),
    ("The Crack Image Wall",      "The drone arrives, and no hand-written crack rule works well enough."),
    ("How A Machine Learns",      "A trained network takes over from the inspector's trained eye."),
    ("Reading The Crack",         "A CNN grades a crack image that no fixed rule could grade."),
    ("Locating The Damage",       "A CNN finds the crack and shows where it looked."),
    ("The Safety Audit",          "We check every prediction to see whether it worked."),
    ("Prediction & The Twin",     "Learn normal, spot the deviation, forecast the future, fuse it all."),
    ("The Business Case",         "Downtime, repairs and safety are turned into money and risk avoided."),
]


# ============================================================================
# THE STEPS  (one per page; len(STEPS) is the count - do not hardcode it)
#   civil / ai   - the two names of the same idea (amber name, cyan name)
#   tech         - what is actually computed (violet)
#   site         - Structural Engineering. NO AI in this text. 2-4 sentences.
#   challenge    - The Challenge. Why the manual way runs out of road.
#   ai_link      - AI Connection. Why this AI concept is therefore required.
#   takeaway     - Key Takeaway. ONE sentence.
#   notebook     - In the Notebook. Where this lives in the Colab notebook.
#   contributes  - In the Notebook. What this step contributes to the system.
# ============================================================================
STEPS = [

# ---------------------------------------------- PHASE 1 - THE BRIDGE IN SERVICE
dict(
    id='in-service', phase=0,
    civil='A Bridge Under Load', ai='Why Predictive SHM Exists',
    civil_icon='🌉', ai_icon='🤖',
    tech="Continuous damage vs a once-a-year inspection",
    civil_bullets=['Millions of crossings', 'Damage grows daily', 'Inspected rarely'],
    ai_bullets=['Watch it always', 'Model the trend', 'Warn before it shows'],
    site="""A highway bridge carries tens of thousands of vehicles a day. Every crossing adds a stress cycle. Wind,
heat, frost, moisture and de-icing salt work on it around the clock. It cannot be closed whenever an
engineer wants a look, so it is inspected by eye once every one or two years.""",
    challenge="""Deterioration is continuous; inspection is not. Between two visits, micro-cracks grow, reinforcement
corrodes, fatigue accumulates and bearings wear. A bridge can pass a visual inspection while hidden
damage keeps progressing, and by the time it is visible the repair is expensive - or the bridge closes.""",
    ai_link="""The bridge does not need its inspectors replaced. It needs the gap between inspections covered - the
structure watched continuously and its future condition estimated before damage is visible. That
continuous watch and forecast, impossible to do by eye, is the only reason AI belongs on the bridge.""",
    notebook="""Act 1. The deterioration curve, and the gap between when damage starts and when an inspection sees it.""",
    contributes="""The requirement the system is measured against. If damage is still found late, it failed.""",
    takeaway="""Damage grows every day; the eye only checks every year or two. The system closes that gap.""",
),
dict(
    id='enter-ai', phase=0,
    civil='A Bridge That Reports Itself', ai='The Digital Twin',
    civil_icon='📡', ai_icon='🛰️',
    tech='Sensed every minute, not inspected every year',
    civil_bullets=['Inspectors stay', 'Sensors watch too', 'Nobody is replaced'],
    ai_bullets=['A live digital copy', 'It flags a problem', 'You still decide'],
    site="""Nothing about the structure changes. Same deck, girders, piers and bearings. The inspector still walks
the bridge, still reads the cracks, still signs the report. Sensors are added - strain, vibration, tilt,
crack width, corrosion, temperature, traffic - and a drone photographs the surfaces on a schedule.""",
    challenge="""The usual objection: is this here to replace the inspector? No. A model that sees only numbers cannot
tap a pier and hear it, judge whether a spall is cosmetic or serious, or decide to close a lane. It can
only notice a change and estimate where it is heading.""",
    ai_link="""A digital twin is a live virtual copy of the bridge, updated by its sensors. It fixes the role of AI for
the whole project: the twin reports and forecasts; a person decides and signs off. Every later choice,
especially the safety audit, follows from that split.""",
    notebook="""No code. This step is the argument, not the arithmetic.""",
    contributes="""Defines the system's output: a recommendation to an engineer, not an automatic verdict.""",
    takeaway="""The twin reports and forecasts. The engineer decides and signs off.""",
),

# ---------------------------------------------- PHASE 2 - A SINGLE READING
dict(
    id='reading', phase=1,
    civil='One Sensor Sweep', ai='Data Collection',
    civil_icon='📏', ai_icon='🗄️',
    tech='One sweep → one row of readings + condition',
    civil_bullets=['Read every sensor', 'Stamp the moment', 'Note the state'],
    ai_bullets=['Each sensor is a column', 'Each sweep is a row', 'Rows stack into a table'],
    site="""At one instant the system reads every channel at once: the deck's natural frequency from the
accelerometers, strain in a girder, tilt at a pier, the width of a monitored crack, corrosion in the
rebar, the temperature, and the weight of traffic crossing. Together they describe the bridge right then.""",
    challenge="""Whoever reads that record later was not on the bridge. They do not feel the wind or see the queue of
trucks. They get a row of numbers. A frozen accelerometer or a mislabelled strain channel means a wrong
picture of a sound bridge - or a sound picture of a failing one.""",
    ai_link="""For a model that limitation is absolute. It never stands on the deck and cannot re-take the reading. One
row - readings plus the condition at that moment - is all it gets, so a wrong row gives a wrong estimate
with no way to notice. That is why the next steps are all about the record.""",
    notebook="""The `SENSORS` list and one sweep's row - the whole state of the bridge, as the model receives it.""",
    contributes="""Every estimate is computed from a row like this. It is the system's only contact with the structure.""",
    takeaway="""The record is the model's entire bridge. Wrong record, wrong estimate.""",
),
dict(
    id='two-records', phase=1,
    civil='A Reading vs A Crack Photo', ai='Structured vs Image Data',
    civil_icon='📊', ai_icon='🖼️',
    tech='8 named readings vs a grid of unnamed pixels',
    civil_bullets=['Sensor numbers', 'A drone photo', 'Same span, two records'],
    ai_bullets=['Named columns', 'Unnamed pixels', 'One model for both?'],
    site="""One span produces two kinds of record. The sensor summary: frequency, strain, vibration, tilt, crack
width, corrosion, temperature, traffic load - values an engineer named and gave units. And the drone
image of the concrete surface: a grid of thousands of pixels, with nothing in it named.""",
    challenge="""A tilt of 0.4 degrees already means something, because a design limit defines it. The drone photo means
nothing until it is processed - and a hairline crack or a rust bloom hides in the pattern of the pixels,
not in any single number a gauge reports.""",
    ai_link="""One span, two kinds of record, one question that shapes the course: can one kind of model handle both?
The tabular ML baseline and the image CNN answer it by building on each and watching where each fails.""",
    notebook="""No code. Eight named readings set beside one crack image.""",
    contributes="""The two branches of the finished system: tabular readings, and the drone image.""",
    takeaway="""Named readings and a crack photo are two different problems.""",
),

# ---------------------------------------------- PHASE 3 - INSTRUMENTING THE BRIDGE
dict(
    id='load', phase=2,
    civil='Commissioning The Monitoring Log', ai='Loading The Dataset',
    civil_icon='🚚', ai_icon='📥',
    tech='read_csv → thousands of sweeps × columns',
    civil_bullets=['Export arrives', 'Check the header', 'Count the sweeps'],
    ai_bullets=['Read the file', 'Check the header', 'Count the rows'],
    site="""The monitoring system has logged the bridge every few minutes for months. Before anything is built on
it, you open the export and check it against what was installed. How many sweeps? Are all the sensors
present? Is each column the type it should be?""",
    challenge="""The temptation is to skip the check and start modeling. That is how a project discovers weeks later that
strain was logged in the wrong unit, or half the record came from a spell when the accelerometer array
had drifted.""",
    ai_link="""Loading a dataset is that commissioning check. Establish what arrived: how many sweeps, how many
channels, what type each is. A model trained on the wrong data does not error - it trains without
complaint and gives wrong answers.""",
    notebook="""`pd.read_csv` on the monitoring log, then the row and column count.""",
    contributes="""The intake gate for the sensor branch. Every number the model learns from enters here.""",
    takeaway="""Check what the bridge actually logged before you build on it.""",
),
dict(
    id='inspect', phase=2,
    civil='Sensor Health Check', ai='Data Inspection',
    civil_icon='🔍', ai_icon='📉',
    tech='Missing values, distributions, out-of-range',
    civil_bullets=['Open every channel', 'Look for dropouts', 'Diagnose before acting'],
    ai_bullets=['Count the gaps', 'Plot the spread', 'Diagnose before cleaning'],
    site="""Now inspect the log the way you would inspect the instruments. A cable knocked loose leaves a gap. A
strain gauge that debonded reads a flat maximum. An accelerometer that came unstuck reads a frozen zero.
A corrosion probe at end of life reads noise.""",
    challenge="""You cannot eyeball months of sweeps the way you check one gauge on site. A channel that dropped out for a
week leaves a hole that looks like nothing. A stuck sensor looks perfectly reasonable. The fault is
invisible at this scale.""",
    ai_link="""So inspect the record with counts and distributions instead of eyes. Count missing readings per channel
and the failed sensor announces itself. Plot each column's spread and the stuck one spikes. Diagnosis
only - nothing is repaired here.""",
    notebook="""Missing-value counts per channel, plus per-column distribution plots.""",
    contributes="""Tells the next step what to remove. Skip it and you clean blind.""",
    takeaway="""Diagnose the data before you repair it.""",
),

# ---------------------------------------------- PHASE 4 - PREPARING THE DATA
dict(
    id='clean', phase=3,
    civil='Dropouts And Spikes', ai='Data Cleaning',
    civil_icon='🧹', ai_icon='🧽',
    tech='Drop duplicates, remove impossible values, fill gaps',
    civil_bullets=['Sensor faults out', 'Duplicate sweeps out', 'Only sound rows train'],
    ai_bullets=['Duplicate rows out', 'Impossible values out', 'Only clean rows train'],
    site="""Act on the diagnosis. A strain of 9,999 microstrain is a saturated gauge and comes out. A natural
frequency of zero on a bridge under traffic is a dead accelerometer, not a still structure. A sweep
logged twice is struck off.""",
    challenge="""That judgement is where inexperience shows. Drop every flawed sweep and a slow degradation trend loses
its history. Keep everything and a dead-gauge zero teaches the model that a loaded girder can read no
strain. No rule decides it for you.""",
    ai_link="""A duplicated sweep is the double-logged reading: it teaches the model one moment mattered twice. A missing
temperature is a judgement - fill with the median, or drop the row? Drop too much and the trend breaks.
Fill carelessly and the model believes readings that never happened.""",
    notebook="""The duplicate drop and missing-value handling, with row counts before and after.""",
    contributes="""The tabular model, the CNN and the twin all inherit whatever you decide here.""",
    takeaway="""Cleaning is a judgement call, and everything downstream inherits it.""",
),
dict(
    id='normalize', phase=3,
    civil='One Common Scale', ai='Normalization',
    civil_icon='📐', ai_icon='⚖️',
    tech='MinMaxScaler → every channel onto 0–1',
    civil_bullets=['Different units', 'One common scale', 'Now comparable'],
    ai_bullets=['Different units in', 'All scaled 0 to 1', 'No column dominates'],
    site="""Every channel reports in its own unit. Strain in the hundreds of microstrain, natural frequency around a
few hertz, corrosion in percent, temperature in tens of degrees, traffic in tonnes. Before they can be
compared, they are put on one common scale.""",
    challenge="""Raw magnitudes lie about importance. Strain runs into the hundreds; frequency sits near three. Side by
side, strain looks a hundred times more significant because of a unit, when a 0.2 Hz drop in natural
frequency is the strongest early sign of lost stiffness.""",
    ai_link="""A neural network cannot tell a big number from an important one. It sees magnitude. Feed it raw columns
and it learns the unit, not the structural meaning. Normalization puts every channel on 0 to 1, so
importance is learned from the data.""",
    notebook="""`MinMaxScaler`, fitted on the sensor columns.""",
    contributes="""Without this the model trains badly and blames the wrong channel. The scaler ships with the model.""",
    takeaway="""Scale the columns, or the network learns the units.""",
),
dict(
    id='split', phase=3,
    civil='Monitored Spans vs A Sealed Span', ai='Train / Test Split',
    civil_icon='🧪', ai_icon='✂️',
    tech='train_test_split → practice vs unseen sweeps',
    civil_bullets=['Tune on known sweeps', 'Prove on new sweeps', 'Never the same sweep'],
    ai_bullets=['Training set', 'Test set', 'Never the same rows'],
    site="""No engineer signs off a condition model using the very sweeps it was tuned on. Tuning happens on known
sweeps whose true condition is recorded. Acceptance is proven on sweeps the model has not seen.""",
    challenge="""Never test someone on the exact work they practised on. A model checked on the sweeps it trained on just
repeats what it memorised, scores brilliantly, and proves nothing about the next reading off the bridge.""",
    ai_link="""So the sweeps are split: some to train on, some sealed away until the safety audit. Only a score on unseen
sweeps says anything about the bridge's next reading.""",
    notebook="""`train_test_split`, producing the training sweeps and the sealed acceptance set.""",
    contributes="""This is what makes the safety audit mean anything. Break it and every result is a recital.""",
    takeaway="""The only fair score comes from sweeps the model has never seen.""",
),

# ---------------------------------------------- PHASE 5 - CONDITION FROM READINGS
dict(
    id='ml-baseline', phase=4,
    civil='Estimating Component Condition', ai='Machine Learning',
    civil_icon='📈', ai_icon='🌲',
    tech='RandomForest on readings → condition rating',
    civil_bullets=['Engineer names factors', 'Model weighs them', 'Condition rating out'],
    ai_bullets=['You name the columns', 'Random Forest', 'Good on readings'],
    site="""Every experienced bridge engineer carries a model in their head. A dropping natural frequency means lost
stiffness, rising strain under the same load means a weakening section, growing tilt means settlement. It
is not written down, not consistent between two engineers, and not watching at 3 a.m.""",
    challenge="""So write it down. Condition falls as frequency drops - but by how much, and how much worse when corrosion
is also high? It is not a single rule. It is many weighted interactions the engineer cannot fully
articulate.""",
    ai_link="""This is the job machine learning does well. You do not state the equations. You state the factors - and an
engineer already named them: frequency, strain, vibration, tilt, crack width, corrosion, temperature,
traffic. Given those columns and thousands of outcomes, the Random Forest works out the mapping to a
condition rating itself.""",
    notebook="""`RandomForestRegressor` for the condition rating, trained on the scaled readings, scored on the sealed sweeps.""",
    contributes="""The tabular branch of the system, and the estimator the forecast and fusion build on.""",
    takeaway="""Name the factors; let the model learn the condition rating.""",
),

# ---------------------------------------------- PHASE 6 - THE CRACK IMAGE WALL
dict(
    id='crack-problem', phase=5,
    civil='What The Drone Actually Sends', ai='Raw Image As Input',
    civil_icon='🖼️', ai_icon='🔢',
    tech='One photo = a grid of pixels, none of them named',
    civil_bullets=['You see a crack', 'You trace it at once', 'No effort at all'],
    ai_bullets=['Thousands of pixels', 'None of them named', "None of them 'crack'"],
    site="""Look at a photo of a concrete soffit and you know. A sound surface is an even grey. A defect shows a
dark hairline, a map-cracked patch, a rust stain bleeding from the steel. An experienced inspector grades
it at a glance, without ever explaining how.""",
    challenge="""Now explain it - precisely enough that someone who has never seen a bridge could follow. Which pixel, at
what brightness, along what path? The crack is a thin curve spread across the whole image, not a value in
any one place.""",
    ai_link="""The drone delivers a grid of pixels per surface. Not one is named. Not one is the crack. At the reading an
engineer had already named strain and frequency, which is why the ML baseline worked. Here there is
nothing pre-named to weigh.""",
    notebook="""One crack image plotted, and its shape printed: a grid of unnamed pixel values.""",
    contributes="""The input the Random Forest cannot use and the CNN is built for.""",
    takeaway="""An image is thousands of pixels, and none of them is the crack.""",
),
dict(
    id='handmade', phase=5,
    civil='The Crack Rulebook, By Hand', ai='Hand-Made Features',
    civil_icon='📝', ai_icon='✍️',
    tech='One brightness threshold on the crack image',
    civil_bullets=['Measure the brightness', 'Set a limit', 'Watch it miss'],
    ai_bullets=['One number by hand', 'One cut-off line', 'Breaks easily'],
    site="""So you try the standard approach: reduce the image to a number. Take the average brightness, or the
overall darkness, set a limit, and flag anything past it. It works for a surface that is obviously
map-cracked and dark.""",
    challenge="""But a hairline crack barely moves the average brightness of the whole image, while a wet stain or a
shadow drags it right down. Tighten the limit and every damp patch trips it. Loosen it and the hairline
sails through. One number cannot separate them.""",
    ai_link="""Every hand-made image feature is a rule you wrote and must maintain, and each one throws away most of the
picture. What you want is for the useful features to be discovered from the raw pixels, not guessed. That
is exactly what deep learning does.""",
    notebook="""An average-brightness feature, one threshold, and the hairline cases it misses.""",
    contributes="""The motive for the CNN: hand features are brittle and discard the pattern.""",
    takeaway="""Reducing an image to one hand-picked number throws away the crack.""",
),
dict(
    id='why-dl', phase=5,
    civil='The Rulebook Runs Out', ai='Therefore: Deep Learning',
    civil_icon='🧠', ai_icon='🚀',
    tech='Learned features vs hand-written rules',
    civil_bullets=['No threshold works', 'Too many patterns', 'Let it learn'],
    ai_bullets=['Features are learned', 'From examples', 'Not from rules'],
    site="""Step back. You have a task an expert does instantly and cannot put into a rule: look at a surface and
grade it, glance at a joint and see the corrosion. Every threshold you write is either too tight or too
loose.""",
    challenge="""The problem is not effort. There is no finite rulebook. The patterns that separate a sound surface from
an early hairline are subtle, overlapping, and different for every material, lighting and camera angle.""",
    ai_link="""Deep learning changes the question. Instead of you writing the rules, you supply labeled examples - sound
surfaces and cracked ones, clean steel and corroded - and the network learns the features that separate
them. It does not dig deeper into your readings; it works where there are no named readings at all.""",
    notebook="""No code. The argument that motivates the two CNNs that follow.""",
    contributes="""The turning point of the course: from named features to learned ones.""",
    takeaway="""When nobody can write the rule, the model learns it from examples.""",
),

# ---------------------------------------------- PHASE 7 - HOW A MACHINE LEARNS
dict(
    id='engineer-brain', phase=6,
    civil="The Inspector's Judgement", ai='The Neuron, Conceptually',
    civil_icon='👷', ai_icon='🧠',
    tech='Weighted evidence → one decision',
    civil_bullets=['Several signals', 'Each weighted', 'One call'],
    ai_bullets=['Several inputs', 'Each weighted', 'One output'],
    site="""Watch how an inspector actually decides whether a span needs attention. A dropping natural frequency
matters a lot. Rising strain matters somewhat. A warm afternoon barely matters. They weigh each signal by
how much it usually predicts trouble, add it up, and make one call: monitor, or flag for inspection.""",
    challenge="""That weighting is not written down and no two inspectors match exactly. It is learned from years of spans
that held and spans that cracked. You cannot hand it to a new starter.""",
    ai_link="""That process - weigh each input, sum, decide - is exactly one artificial neuron. The weights are what the
inspector's experience becomes. Everything that follows is how those weights get set from data.""",
    notebook="""No code. The mental model of a neuron before any mathematics.""",
    contributes="""The intuition every later step builds on: a neuron is weighted evidence to a decision.""",
    takeaway="""An inspector weighing signals into one call is a neuron.""",
),
dict(
    id='neuron', phase=6,
    civil='Weighing The Signals', ai='Weighted Sum + Bias',
    civil_icon='⚙️', ai_icon='➕',
    tech='z = w·x + b',
    civil_bullets=['Weight each signal', 'Add them up', 'Add a baseline'],
    ai_bullets=['Weigh each input', 'Add them up', 'Add a bias'],
    site="""Make the inspector's judgement explicit. Each reading gets a weight: frequency drop high, strain
moderate, temperature small. Multiply each reading by its weight, add them up, and add a baseline offset
for how conservative this bridge's safety class is.""",
    challenge="""Set those weights by hand across eight channels and you are guessing. Too much weight on temperature and
every hot afternoon is flagged as damage. The right weights are not obvious and they interact.""",
    ai_link="""This weighted sum plus bias is the whole of a neuron's forward step: z = w·x + b. Slide the weights below
and watch one span's score cross the line. Learning, next, is just setting these weights automatically.""",
    notebook="""The dot product `w·x + b` written out for one sweep's readings.""",
    contributes="""The single computation every layer of every network repeats.""",
    takeaway="""A neuron multiplies each signal by a weight, sums, and adds a bias.""",
),
dict(
    id='activation', phase=6,
    civil='When To Raise The Flag', ai='Activation Function',
    civil_icon='🚨', ai_icon='📈',
    tech='sigmoid / ReLU on z',
    civil_bullets=['Weak evidence: monitor', 'Strong evidence: flag', 'A smooth switch'],
    ai_bullets=['Low score, no', 'High score, yes', 'A smooth switch'],
    site="""A weighted score is not yet a decision. The engineer needs a call: below a level, keep monitoring; above
it, flag the span for inspection. And it should not flip on a single noisy reading - it should turn on
smoothly as evidence builds.""",
    challenge="""A hard cut-off is brittle: one reading either side of the line flips the call. Real judgement ramps up - a
little doubt, then concern, then certainty - and a straight-line score cannot bend like that.""",
    ai_link="""The activation function is that smooth switch. Sigmoid turns any score into a 0-to-1 probability of
damage; ReLU passes strong evidence and blocks the rest. Without it, stacking neurons stays linear and
learns nothing curved.""",
    notebook="""`sigmoid` and `relu` plotted, and the same neuron with and without one.""",
    contributes="""What lets a network bend - the reason depth adds power.""",
    takeaway="""Activation turns a raw score into a decision, and lets the network bend.""",
),
dict(
    id='learning-loop', phase=6,
    civil='Every Missed Crack Teaches', ai='The Learning Loop',
    civil_icon='🔁', ai_icon='🔄',
    tech='predict → measure error → adjust → repeat',
    civil_bullets=['Make a call', 'See the true state', 'Adjust the rule'],
    ai_bullets=['Predict', 'Measure error', 'Update weights'],
    site="""How does an inspector get good? They call a span sound, a later probe finds a crack, and they adjust:
that frequency dip mattered more than they thought. Next time they weigh it heavier. Every surprise tunes
the internal model.""",
    challenge="""Done by hand this takes a career, and the lessons live in one person's head. An agency cannot wait years,
and cannot lose the model when that person retires.""",
    ai_link="""Training is that loop, run thousands of times a second. The network predicts, compares to the recorded
condition, and nudges every weight to be a little less wrong. Predict, measure, adjust, repeat - that is
all learning is.""",
    notebook="""No code. The loop in plain terms before loss and gradients name its parts.""",
    contributes="""The skeleton of training that the next steps fill in.""",
    takeaway="""Learning is predict, measure the error, adjust, and repeat.""",
),
dict(
    id='gradient-descent', phase=6,
    civil='Tuning The Judgement', ai='Loss + Gradient Descent',
    civil_icon='🎚️', ai_icon='⬇️',
    tech='minimize loss by stepping downhill in w',
    civil_bullets=['Measure how wrong', 'Which way is better', 'Take a step'],
    ai_bullets=['Loss = how wrong', 'Find the better way', 'Take a small step'],
    site="""To tune a judgement you need two things: a number for how wrong you were, and which direction fixes it.
Called a span sound and a crack was there - that is a large, costly error. Nudge the weighting the way
that would have caught it, by a sensible amount.""",
    challenge="""Nudge by hand across eight weights at once and you cannot tell which change helped. Too big a step and
you overshoot into flagging every sound span; too small and it never settles. And there is no time to try
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
    site="""One inspector has limits. A bridge team layers expertise: a materials specialist feeds a structural
engineer, who feeds the asset manager. Each layer combines what the one below noticed into a higher-level
judgement.""",
    challenge="""A single weighted rule can only split the world with one straight line. Real damage patterns are not
linear - low frequency with high strain means one thing, low frequency alone in the cold means another.
One neuron cannot hold that.""",
    ai_link="""Stack neurons into layers and the network composes simple features into complex ones, exactly like the
team. The first layer finds crude patterns; deeper layers combine them. Depth is what lets it represent
any decision boundary.""",
    notebook="""An `MLPClassifier` with hidden layers, and how width and depth change the fit.""",
    contributes="""The architecture the tabular ANN and, later, the crack CNN are all built from.""",
    takeaway="""Layered neurons compose simple signals into complex judgements.""",
),
dict(
    id='training', phase=6,
    civil='Learning From The Record', ai='Training The Model',
    civil_icon='🏋️', ai_icon='📉',
    tech='epochs of forward pass + backprop',
    civil_bullets=['Show it many sweeps', 'Correct each miss', 'Go around again'],
    ai_bullets=['Show it examples', 'Correct each miss', 'The error drops'],
    site="""Commission the model the way you qualify a new engineer: show it many sweeps whose true condition is
known, let it call each, correct every miss, and go around again. Each full pass over the examples is one
round of training.""",
    challenge="""Too few rounds and it has not learned the patterns. Too many on the same sweeps and it memorises them -
brilliant on the training record, useless on a new reading. You need to know when to stop.""",
    ai_link="""Training runs the learning loop over the whole training set for many epochs, watching the loss fall on
data it trains on and on held-out data it does not. When the held-out loss stops improving, you stop.
Watch the curve below.""",
    notebook="""The training loop, the loss curve, and the early-stopping point.""",
    contributes="""Produces the trained tabular model that the audit then judges.""",
    takeaway="""Training repeats the learning loop until held-out error stops falling.""",
),

# ---------------------------------------------- PHASE 8 - READING THE CRACK
dict(
    id='cnn-journey', phase=7,
    civil='How The Surface Is Read', ai='Convolutional Neural Network',
    civil_icon='🖼️', ai_icon='🧬',
    tech='filters → feature maps → crack grade',
    civil_bullets=['Slide a detector', 'Find crack-like lines', 'Build up the grade'],
    ai_bullets=['Filters slide across', 'Find edges, then cracks', 'Learned, not coded'],
    site="""An inspector does not read pixels. They look for features - the thin dark line of a crack, the branching
of map-cracking, the bleed of a rust stain - and grade the surface from those patterns wherever they
appear on the span.""",
    challenge="""You cannot write down every defect signature by hand, and a crack can appear anywhere on the surface. A
fixed rule at a fixed position misses a hairline that shows up in the next frame.""",
    ai_link="""A CNN slides small learned filters across the image, each one firing on a pattern - a thin edge, a
branching line - wherever it occurs. Early filters find simple edges; later layers combine them into a
crack signature. The features are learned from labeled images, not coded.""",
    notebook="""A 2-D CNN on the crack images, with its filters and feature maps visualized.""",
    contributes="""The first image branch: the crack grader the hand-made threshold could not be.""",
    takeaway="""A CNN learns the crack patterns in an image instead of you coding them.""",
),

# ---------------------------------------------- PHASE 9 - LOCATING THE DAMAGE
dict(
    id='crack-locate', phase=8,
    civil='Locating The Crack', ai='CNN Detection + Grad-CAM',
    civil_icon='🎯', ai_icon='🔦',
    tech='classify cracked / sound, then show where',
    civil_bullets=['Scan the surface', 'Find the damage', 'Point to it'],
    ai_bullets=['Cracked or sound?', 'Heat-map the crack', 'Show where it looked'],
    site="""Point the drone at a whole deck soffit. Most of it is sound; somewhere a crack runs across it. The
inspector's job is not only to say a defect exists but to mark exactly where, so the repair crew and the
next report can find it.""",
    challenge="""Scanning every square metre of every span is exactly the repetitive watching a person does worst. And a
flat cracked/sound answer is not enough: an engineer will not act on a black box that just says
'cracked' without showing where and how bad.""",
    ai_link="""A CNN classifies the surface as cracked or sound, and Grad-CAM highlights the pixels that drove the call -
so the heat lands on the crack itself. The engineer sees not just the verdict but the evidence, and can
overrule it. Detection plus explanation.""",
    notebook="""A CNN on surface images, plus a Grad-CAM overlay locating the crack.""",
    contributes="""The second image capability: locates the damage so a report and a crew can act on it.""",
    takeaway="""A CNN can both call the crack and show you where it saw it.""",
),

# ---------------------------------------------- PHASE 10 - THE SAFETY AUDIT
dict(
    id='audit', phase=9,
    civil='The Safety Audit', ai='Confusion Matrix',
    civil_icon='📋', ai_icon='🔲',
    tech='TN / FP / FN / TP on the sealed test sweeps',
    civil_bullets=['Line up every call', 'Against what was true', 'Four outcomes'],
    ai_bullets=['Two right boxes', 'Two wrong boxes', 'One miss hides damage'],
    site="""Audit the model the way you would audit a batch of inspection reports against reality. Hundreds of sweeps
happened. The recorded condition says what was really going on. The model made a call on each - sound, or
needs intervention. Line them up and count.""",
    challenge="""Four things can happen, and lumping them together hides the one that matters. Called sound, was sound:
fine. Called damaged, was damaged: caught it. Called damaged, was actually sound: a false alarm and a
wasted inspection. Called sound, was damaged: the dangerous miss - real damage left on the bridge.""",
    ai_link="""Put those four boxes in a square and you have the confusion matrix - you did not learn it, you audited the
run and it fell out. Never quote accuracy alone: a model that calls everything sound scores well and
misses every real defect.""",
    notebook="""The test-set predictions, `ConfusionMatrixDisplay`, and the warning that follows.""",
    contributes="""The acceptance test, run on the sweeps sealed away at the split.""",
    takeaway="""Accuracy hides the one box that matters - the damage called sound.""",
),
dict(
    id='proof', phase=9,
    civil='Readings vs Images: The Verdict', ai='Where Deep Learning Earns Its Place',
    civil_icon='⚖️', ai_icon='🏁',
    tech='RF vs ANN on readings; threshold vs CNN',
    civil_bullets=['Readings: both work', 'Image: only DL', 'Right tool for the job'],
    ai_bullets=['Numbers: both work', 'Images: only DL', 'Pick the right tool'],
    site="""The verdict, and it is not a vendor's pitch. On the eight named readings an engineer defined, machine
learning and deep learning estimate condition about equally well. Not close - the same.""",
    challenge="""So if deep learning does not win on the readings, why learn it? Because of the image. Your hand-made
brightness threshold failed and no limit saved it, and the Random Forest cannot be pointed at a grid of
raw pixels at all.""",
    ai_link="""Here is the thesis, proved rather than claimed. When an engineer has named the features, use machine
learning - simpler, faster, easier to defend. When nobody can name them, as with the crack image, deep
learning is the option that works. AI does not out-think the inspector; it covers the part no one can do
by hand.""",
    notebook="""Random Forest against the ANN on readings, and the image task neither hand-rule could touch.""",
    contributes="""Justifies two branches instead of one model - and stops you reaching for DL on a spreadsheet.""",
    takeaway="""Deep learning earns its place only where nobody can name the features.""",
),

# ---------------------------------------------- PHASE 11 - PREDICTION & THE TWIN
dict(
    id='anomaly', phase=10,
    civil='Normal vs Not-Normal Behaviour', ai='Anomaly Detection',
    civil_icon='🌡️', ai_icon='📡',
    tech='learn freq-vs-temp, flag the odd residual',
    civil_bullets=['Frequency swings daily', 'Most swings are weather', 'One is not'],
    ai_bullets=['Learn normal for weather', 'Watch the gap', 'Alarm on the odd drop'],
    site="""A bridge's natural frequency is not constant. It rises in the cold and falls in the heat as the concrete's
stiffness changes, and it dips under heavy traffic. A raw frequency alarm would fire every summer
afternoon. Most change is normal, seasonal, expected behaviour.""",
    challenge="""So a fixed threshold is useless - set it low and weather trips it daily, set it high and real stiffness
loss hides inside the seasonal swing. The damage signal is a small drop that the temperature does not
explain, buried in a large one that it does.""",
    ai_link="""The twin learns the normal relationship between frequency and temperature from history, then predicts the
frequency it expects for today's weather. The residual - observed minus expected - is near zero while the
bridge behaves normally, and spikes the moment stiffness drops for a reason weather cannot account for.
That is anomaly detection.""",
    notebook="""A model of expected frequency given temperature, and the residual that flags the anomaly.""",
    contributes="""The early-warning branch: catches a change in behaviour before any single reading looks alarming.""",
    takeaway="""Learn what is normal for the weather, and alarm only on the change it cannot explain.""",
),
dict(
    id='rul-forecast', phase=10,
    civil='How Long Until It Needs Work', ai='Degradation Trend & RUL',
    civil_icon='⏳', ai_icon='📅',
    tech='fit the condition trend → intervention limit',
    civil_bullets=['Condition falls slowly', 'Draw the trend line', 'Read when it crosses'],
    ai_bullets=['Fit the downward trend', 'Extend it forward', 'Read the months left'],
    site="""The condition rating of a component does not jump - it drifts down over months and years as fatigue,
corrosion and load accumulate. Plot a component's rating over time and there is a trend under the noise,
heading toward the level at which the agency must intervene.""",
    challenge="""Reactive maintenance waits for the rating to cross the line, then scrambles. Schedule-based maintenance
repairs on a fixed calendar whether the bridge needs it or not. Neither answers the question an asset
manager actually asks: how many months until this component needs work?""",
    ai_link="""Fit the degradation trend to the monitored history and extrapolate it to the intervention limit. Where the
projection crosses the line is the estimated date; the gap from today is the Remaining Useful Life. Now
maintenance is planned before the damage is visible - the whole point of predictive SHM.""",
    notebook="""A trend fitted to the condition history, extrapolated to the limit, returning months of RUL.""",
    contributes="""Turns the current estimate into a forecast: the date and the RUL that drive the maintenance plan.""",
    takeaway="""Fit the downward trend, extend it to the limit, and read off the months of life left.""",
),
dict(
    id='fusion-engine', phase=10,
    civil='The Bridge Health Screen', ai='AI Fusion',
    civil_icon='🎛️', ai_icon='🔗',
    tech='readings + CNN + anomaly + RUL → one alert',
    civil_bullets=['Every feed lands here', 'Checked together', 'One call'],
    ai_bullets=['Each model alone: weak', 'Combined: a decision', 'This is the product'],
    site="""Every asset team has a health screen. The condition estimate on one side, the crack grade from the drone
on another, the anomaly residual and the RUL forecast beside them. The engineer in the middle does not
act on any one feed - they cross-reference them.""",
    challenge="""Each feed alone is close to noise. The readings say elevated risk - it could be one cold snap. The crack
CNN flags a mark - it could be a wet patch. The anomaly spikes - it could be one heavy convoy. A system
that alarms on any one gets switched off in a week.""",
    ai_link="""Now fuse them. A dropping condition estimate, a crack graded by the CNN, an anomaly the weather cannot
explain, and a shrinking RUL together are not four weak signals. That is one clear call: inspect this
pier within the month. Several models, one prioritized alert, one engineer who acts.""",
    notebook="""`fusion(readings, crack, anomaly, rul)` - the health screen as a function.""",
    contributes="""This is the product. Everything before it was a component.""",
    takeaway="""Weak signals, fused, become one prioritized maintenance call.""",
),
dict(
    id='pipeline', phase=10,
    civil='The Complete Digital Twin', ai='The AI Engineering Pipeline',
    civil_icon='🏗️', ai_icon='🛤️',
    tech='sensors + drone → models → fused forecast',
    civil_bullets=['Sensors to plan', 'Every stage in order', 'One flow'],
    ai_bullets=['Take in, clean, model', 'Check, forecast, fuse', 'Then serve the plan'],
    site="""Step back and see the whole bridge as one flow: the structure sensed and photographed, readings logged
and cleaned, models trained and audited, behaviour watched for anomalies, condition forecast, signals
fused, and a prioritized plan handed to the engineer - who still makes the call.""",
    challenge="""Any single stage done well is worthless if the chain breaks. A perfect model on dirty data, or a great
forecast nobody acts on, prevents no failure and saves no money. The value is in the whole pipeline.""",
    ai_link="""This is the AI engineering pipeline: ingest, clean, prepare, model, evaluate, forecast, fuse, serve. Every
page of this course was one stage of it, in the order a real project runs them.""",
    notebook="""The end-to-end pipeline assembled, from raw log to a served maintenance recommendation.""",
    contributes="""Ties every previous step into one deployable digital twin.""",
    takeaway="""The value is the whole pipeline, not any one model in it.""",
),

# ---------------------------------------------- PHASE 12 - THE BUSINESS CASE
dict(
    id='dashboard', phase=11,
    civil='Repairs, Downtime And Safety', ai='The Predictive-Maintenance Dashboard',
    civil_icon='🖥️', ai_icon='🔔',
    tech='predictive vs reactive → cost, risk avoided',
    civil_bullets=['Fleet at a glance', 'Fix before failure', 'Money & risk saved'],
    ai_bullets=['Every model, one screen', 'Ranked by months left', 'The business case'],
    site="""The screen the asset manager actually opens. The bridges on one view: each one's condition, its forecast
RUL, and the cost of fixing it early against the cost of a reactive repair or an emergency closure once
the damage is severe.""",
    challenge="""None of the engineering matters to the agency until it is a number a manager can act on: how much a
planned repair saves over an emergency one, how many closures are avoided, and how much catastrophic risk
is taken off the network this year.""",
    ai_link="""The dashboard is where every model's output becomes a decision and a cost. Move the sliders to your own
network and rates and read off the repairs, downtime and risk that catching damage early saves over
waiting for it to show.""",
    notebook="""The predictive-vs-reactive comparison and the saved-cost calculation.""",
    contributes="""The closing view: the whole system as one screen and one business case.""",
    takeaway="""The dashboard turns every forecast into a planned repair and a saved cost.""",
),
]


# ---------------------------------------------------------------- short labels
SHORT = {
    "in-service": "A bridge under load",   "enter-ai": "The digital twin",
    "reading": "One sensor sweep",         "two-records": "Reading vs image",
    "load": "Monitoring log arrives",      "inspect": "Sensor health check",
    "clean": "Dropouts & spikes",          "normalize": "Standardize units",
    "split": "Known vs sealed",            "ml-baseline": "Condition from readings",
    "crack-problem": "The raw image",      "handmade": "Threshold by hand",
    "why-dl": "Rulebook fails",            "engineer-brain": "Inspector decides",
    "neuron": "Weighing signals",          "activation": "Raise-the-flag switch",
    "learning-loop": "Learn from misses",  "gradient-descent": "Tune it in",
    "network": "Bridge team",              "training": "Learn from the record",
    "cnn-journey": "Read the crack",       "crack-locate": "Locate the crack",
    "audit": "Safety audit",               "proof": "The verdict",
    "anomaly": "Normal vs anomaly",        "rul-forecast": "Remaining useful life",
    "fusion-engine": "Health screen",      "pipeline": "The whole twin",
    "dashboard": "Predictive dashboard",
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
# Left = the bridge (amber). Right = the AI (cyan). Between them an animated
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
    """The structural-activity -> AI-equivalent -> technical-process bridge,
    drawn as a monitoring signal-flow block diagram."""
    fig = go.Figure()
    _card(fig, 0.2, 3.4, CIVIL, step["civil_icon"], step["civil"],
          step["civil_bullets"], "ON THE BRIDGE")
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
    fig.add_annotation(x=5.0, y=2.02, text="⌗ COMPUTE", showarrow=False,
                       font=dict(size=9, color=TECH, family=MONOF))
    fig.add_annotation(x=5.0, y=1.62, text=_wrap(step["tech"], 30), showarrow=False,
                       font=dict(size=9.5, color=TEXT, family=MONOF),
                       xanchor="center", yanchor="middle", align="center")
    fig.add_annotation(x=5.0, y=2.42, text="▼", showarrow=False,
                       font=dict(size=13, color=TECH))

    # a "data packet" token travels the bus from bridge to AI
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
        f"<div class='dro-bar' style='margin-top:14px'>⟨SHM-TWIN⟩ &nbsp; "
        f"STEP {i+1:02d}/{len(ORDER)} &nbsp;·&nbsp; PHASE {step['phase']+1:02d}/{len(PHASES)} "
        f"&nbsp;·&nbsp; <span style='color:{CIVIL}'>{pname.upper()}</span> "
        f"&nbsp;—&nbsp; {pdesc}</div>", unsafe_allow_html=True)
    st.markdown(f"# {step['civil_icon']}  {step['civil']}")
    st.markdown(
        f"<span class='substep'>▸ this structural step is the AI concept </span>"
        f"<b style='color:{AISIDE}'>{step['ai']}</b>",
        unsafe_allow_html=True)
    st.divider()

    # ---- PT.10  Structural Engineering ------------------------------------
    _op_header("10", "Structural Engineering", CIVIL)
    st.markdown(f"<div class='spec civil'>{step['site']}</div>", unsafe_allow_html=True)
    st.write("")

    # ---- PT.20  The Challenge ---------------------------------------------
    _op_header("20", "The Challenge", RED)
    st.markdown(f"<div class='spec warn'>{step['challenge']}</div>", unsafe_allow_html=True)
    st.write("")

    # ---- PT.30  AI Connection ---------------------------------------------
    _op_header("30", "AI Connection", AISIDE)
    st.markdown(f"<div class='spec ai'>{step['ai_link']}</div>", unsafe_allow_html=True)
    st.plotly_chart(bridge_figure(step, style, animate), use_container_width=True,
                    key=f"bridge_{stage}")
    st.caption("▶ Press Play — the data packet travels the bus from the bridge into the AI.")
    st.divider()

    # ---- PT.40  Technical Idea header -------------------------------------
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
        f"<div class='travbar'><span class='travlab'>SURVEY</span>"
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
    'in-service': dict(
        q="A bridge passes its visual inspection, yet the system still calls it a problem. Why?",
        options=["Visual inspections are always wrong",
                 "Deterioration is continuous but inspection happens only every 1–2 years, so damage can appear and grow entirely between visits",
                 "The bridge is too old to inspect",
                 "Sensors are more accurate than engineers"],
        answer=1,
        why="Damage grows every day; the eye only checks every year or two. The system exists to close that gap, not to replace the inspector."),
    'enter-ai': dict(
        q="In the digital twin, who makes the final decision to close a lane or schedule a repair?",
        options=["The AI model, automatically",
                 "The sensors, when a threshold is crossed",
                 "The engineer — the twin only reports and forecasts",
                 "Whichever model has the highest confidence"],
        answer=2,
        why="The twin reports and forecasts; a person decides and signs off. That split drives every later choice, especially the safety audit."),
    'reading': dict(
        q="What does the condition model actually receive from one sensor sweep?",
        options=["A live feed from the bridge",
                 "A single row of numbers — the readings plus the condition at that instant",
                 "The engineer's written inspection notes",
                 "A 3-D scan of the whole structure"],
        answer=1,
        why="The model never stands on the deck. It gets one row; if the row is wrong, the estimate is wrong and the model cannot notice."),
    'two-records': dict(
        q="Why can the Random Forest handle the eight readings but not the crack image?",
        options=["The image file is too large",
                 "Images need a faster computer",
                 "The readings are named features an engineer defined; the image is thousands of unnamed pixels with no 'crack' column",
                 "Random Forests only work on text"],
        answer=2,
        why="One span, two records. The RF weighs named columns; it cannot be pointed at 4,096 unnamed pixels, which is why deep learning is needed later."),
    'load': dict(
        q="Why check the raw export (row and column counts, types) before building any model?",
        options=["To make the file smaller",
                 "Because a model trained on wrong data does not error — it trains happily and gives wrong answers",
                 "It is required by law",
                 "To delete duplicate bridges"],
        answer=1,
        why="Loading a dataset is a commissioning check. Establish what actually arrived, because silent bad data produces confidently wrong models."),
    'inspect': dict(
        q="How do you find a stuck or dead sensor hidden in months of sweeps?",
        options=["Read every row by eye",
                 "Count missing values per channel and plot each column's distribution — the fault spikes or flat-lines",
                 "Trust the sensor's own status light",
                 "Retrain the model until it works"],
        answer=1,
        why="You cannot eyeball months of data. Counts and distributions make a dropout or a frozen channel announce itself. Diagnosis only — nothing is repaired here."),
    'clean': dict(
        q="A gap in the strain channel is filled with the median rather than the mean. Why the median?",
        options=["The median is faster to compute",
                 "The mean is dragged by saturation spikes (e.g. 9,999 µε); the median barely notices them",
                 "The mean cannot handle decimals",
                 "It makes no difference"],
        answer=1,
        why="A saturated-gauge spike pulls the mean far off. The median — the middle value — stays realistic, so the filled reading is plausible."),
    'normalize': dict(
        q="Why put every channel on a common 0–1 scale before training a neural network?",
        options=["To save memory",
                 "Because a network reads magnitude, not meaning — raw strain in the hundreds would swamp a 0.2 Hz frequency drop that actually matters more",
                 "Because 0–1 numbers look nicer",
                 "So the columns fit on the screen"],
        answer=1,
        why="A network cannot tell a big number from an important one. Scaling lets importance be learned from the data, not from the units."),
    'split': dict(
        q="Why must the model be scored on sweeps it never trained on?",
        options=["To use up the spare data",
                 "A model tested on its training sweeps just recites what it memorised and proves nothing about the next reading",
                 "Because the test set is cleaner",
                 "It is not necessary if accuracy is high"],
        answer=1,
        why="Never test someone on the exact work they practised on. Only a score on sealed, unseen sweeps says anything about the bridge's next reading."),
    'ml-baseline': dict(
        q="What do you actually give the Random Forest, and what does it work out?",
        options=["The equations for condition; it just plugs in numbers",
                 "The named factors (frequency, strain, tilt, …) plus thousands of outcomes; it learns the mapping to a condition rating itself",
                 "A photo of the bridge; it reads the cracks",
                 "Nothing — it guesses randomly"],
        answer=1,
        why="You state the factors — an engineer already named them — not the equations. Given those columns and outcomes, the model learns the mapping."),
    'crack-problem': dict(
        q="Where, exactly, is the crack in the image?",
        options=["In one specific dark pixel",
                 "In a column labelled 'crack'",
                 "In a thin dark path — a pattern spread across hundreds of pixels, held by no single number",
                 "It cannot be seen at all"],
        answer=2,
        why="A crack is a pattern, not a value. Nothing in the raw image is pre-named, which is why a hand-written pixel rule cannot capture it."),
    'handmade': dict(
        q="Why does flagging on average brightness fail as a crack detector?",
        options=["Brightness is impossible to compute",
                 "A hairline barely moves the average while a harmless wet patch drags it down — one number throws away the distinguishing pattern",
                 "The camera is broken",
                 "Averages are always exactly 0.5"],
        answer=1,
        why="Reducing an image to one number discards the shape that separates defect from sound. Every hand-made feature is a rule you must maintain, and each keeps only a sliver of the picture."),
    'why-dl': dict(
        q="When is deep learning the right tool over machine learning?",
        options=["Whenever you have a lot of data",
                 "When nobody can name the features — as with the raw crack image",
                 "Always; DL beats ML on everything",
                 "Only when the model must run fast"],
        answer=1,
        why="DL does not dig deeper into named readings — ML already handles those. It earns its place where there are no named features at all."),
    'engineer-brain': dict(
        q="An inspector weighs several signals, sums them, and makes one call. That process is essentially…",
        options=["A spreadsheet",
                 "A single artificial neuron",
                 "A database query",
                 "A random guess"],
        answer=1,
        why="Weigh each input, sum, add a baseline, decide — that is exactly one neuron. The weights are what the inspector's experience becomes."),
    'neuron': dict(
        q="What is a neuron's forward step, z = w·x + b?",
        options=["A weighted sum of the inputs plus a bias offset",
                 "The average of the inputs",
                 "The largest input value",
                 "A random number generator"],
        answer=0,
        why="Each reading is multiplied by its weight, the products are summed, and a bias is added. This is the single computation every layer repeats."),
    'activation': dict(
        q="Why pass the neuron's score z through a non-linear activation like sigmoid?",
        options=["To make training slower",
                 "It turns a raw score into a smooth 0–1 decision and lets stacked neurons bend — without it the network stays a straight line",
                 "To round the number to an integer",
                 "It has no real effect"],
        answer=1,
        why="A hard cut-off flips on one noisy reading; sigmoid ramps up smoothly. And without a non-linearity, stacking neurons learns nothing curved."),
    'learning-loop': dict(
        q="Stripped of terminology, what is 'learning'?",
        options=["Memorising every example perfectly",
                 "Predict, measure the error against the truth, adjust to be less wrong, and repeat",
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
        why="The gradient always points downhill; the art is the step size. Too large and it bounces past the minimum; too small and it never settles."),
    'network': dict(
        q="Why stack neurons into layers instead of using just one?",
        options=["To use more memory",
                 "One neuron can only split the world with a straight line; layers compose simple signals into the curved patterns real damage makes",
                 "Layers make the maths simpler",
                 "There is no reason; one neuron is always enough"],
        answer=1,
        why="Low frequency with high strain means one thing; low frequency alone in the cold means another. Depth lets the network hold decisions one neuron cannot."),
    'training': dict(
        q="The training loss falls fast, then flattens. What does running many more epochs eventually cause?",
        options=["The model gets steadily better forever",
                 "The model starts memorising the training sweeps — overfitting — while held-out error stops improving",
                 "The sensors recalibrate",
                 "The loss becomes negative"],
        answer=1,
        why="More epochs on the same sweeps only memorise them. You stop when the held-out error stops falling, not when training loss hits zero."),
    'cnn-journey': dict(
        q="Where do a CNN's crack-detecting filters come from?",
        options=["An engineer writes each filter by hand",
                 "They are learned from labelled images during training",
                 "They are fixed and identical in every CNN",
                 "They are downloaded from the camera"],
        answer=1,
        why="The network learns the filters from examples — the rule the hand-made brightness threshold could not capture. A hairline lights up a line filter a sound surface leaves quiet."),
    'crack-locate': dict(
        q="A CNN already says 'crack'. What does Grad-CAM add?",
        options=["A higher accuracy score",
                 "It highlights the pixels that drove the call, so the engineer sees the evidence and can mark or overrule it",
                 "It removes the crack from the image",
                 "It makes the model run faster"],
        answer=1,
        why="An engineer will not act on a black box. Grad-CAM lands the heat on the crack itself — verdict plus evidence, and a location for the repair crew."),
    'audit': dict(
        q="On the confusion matrix, which box is the dangerous one, and why not quote accuracy alone?",
        options=["False alarms; they waste money",
                 "Called sound but was damaged — the miss that leaves real damage on the bridge; a model calling everything sound scores high on accuracy yet misses every defect",
                 "Called damaged and was damaged; it means the model works",
                 "There is no dangerous box"],
        answer=1,
        why="Accuracy hides the false-negative box. That missed damage is the whole reason the system exists, so it must be reported separately."),
    'proof': dict(
        q="What did comparing ML and DL prove about when to use each?",
        options=["Deep learning always wins",
                 "On the named readings ML and DL are about equal; DL earns its place only on the image, where no one can name the features",
                 "Machine learning always wins",
                 "Neither works on bridges"],
        answer=1,
        why="When an engineer has named the features, use ML — simpler, faster, easier to defend. When nobody can, as with the crack image, deep learning is the option that works."),
    'anomaly': dict(
        q="Why is a fixed natural-frequency threshold a poor damage alarm?",
        options=["Frequency is impossible to measure",
                 "Frequency swings with temperature every day, so a fixed line either trips every summer or hides real stiffness loss inside the seasonal swing",
                 "The alarm is too loud",
                 "Thresholds are never allowed in engineering"],
        answer=1,
        why="The twin learns the normal frequency-for-temperature and scores the residual. The alarm fires only on the change the weather cannot explain — that is anomaly detection."),
    'rul-forecast': dict(
        q="What is the Remaining Useful Life (RUL) of a component?",
        options=["Its age in years",
                 "The months from today until the fitted condition trend is projected to cross the intervention line",
                 "The time since the last inspection",
                 "A fixed number set by the manufacturer"],
        answer=1,
        why="Fit the degradation trend and extrapolate to the intervention limit. The gap from today to that crossing is the RUL — maintenance planned before damage is visible."),
    'fusion-engine': dict(
        q="Why fuse the condition estimate, crack grade, anomaly and RUL instead of alarming on each?",
        options=["To reduce the number of sensors",
                 "Each feed alone is close to noise and a system that alarms on any one gets switched off; fused, they become one prioritized call",
                 "Fusion makes the models more accurate individually",
                 "So only one model has to run"],
        answer=1,
        why="A cold snap, a wet patch, or one heavy convoy can each trip a single feed. Together — dropping condition, a graded crack, an unexplained anomaly, a shrinking RUL — they are one clear call: inspect this pier within the month."),
    'pipeline': dict(
        q="Where does the value of the digital twin actually live?",
        options=["In the single best model",
                 "In the whole pipeline — ingest, clean, prepare, model, evaluate, forecast, fuse, serve — because a break anywhere prevents no failure",
                 "In having the most sensors",
                 "In the dashboard colours"],
        answer=1,
        why="A perfect model on dirty data, or a great forecast nobody acts on, saves nothing. Any single stage is worthless if the chain breaks."),
    'dashboard': dict(
        q="How does predictive maintenance save money over reactive maintenance?",
        options=["By never repairing anything",
                 "By catching damage early so it is a planned repair — avoiding the emergency-repair multiplier and most closures",
                 "By reducing the number of bridges",
                 "By inspecting every bridge every week"],
        answer=1,
        why="Caught early, a repair is planned and cheap; left to show itself, it becomes an emergency repair plus a closure. That gap is the business case."),
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
# A vertical spine of the project's phases. Every node opens that learning page.
# ============================================================================
def mind_map(style):
    fig = go.Figure()
    n = len(PHASES)
    VGAP = 1.5                                   # more vertical room per phase row
    ys = {i: (n - 1 - i) * VGAP for i in range(n)}

    for i in range(n - 1):
        fig.add_annotation(x=0, y=ys[i + 1] + 0.55, ax=0, ay=ys[i] - 0.62,
                           xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1.1,
                           arrowwidth=2, arrowcolor=CIVIL, text="")

    GAP = 3.4                                    # wider column pitch so labels clear
    X0 = 1.7

    sx, sy, stext, scustom, shover = [], [], [], [], []
    for pi, (pname, pdesc) in enumerate(PHASES):
        kids = _phase_steps(pi)
        for k, s in enumerate(kids):
            fig.add_shape(type="line", x0=0.3, y0=ys[pi], x1=X0 + k * GAP, y1=ys[pi],
                          line=dict(color="#2b323c", width=1.2, dash="dot"), layer="below")
        fig.add_annotation(x=0, y=ys[pi], text=f"<b>PH {pi+1:02d}</b>", showarrow=False,
                           font=dict(size=11, color=BG, family=MONOF),
                           bgcolor=CIVIL, bordercolor=CIVIL, borderpad=5, borderwidth=2)
        fig.add_annotation(x=-0.95, y=ys[pi] + 0.14, text=f"<b>{pname}</b>", showarrow=False,
                           xanchor="right", font=dict(size=13, color=CIVIL))
        fig.add_annotation(x=-0.95, y=ys[pi] - 0.16, text=_wrap(pdesc, 32),
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

    fig.update_xaxes(visible=False, range=[-7.0, X0 + 2 * GAP + 2.2])
    fig.update_yaxes(visible=False, range=[-1.0, (n - 1) * VGAP + 0.6])
    return style(fig, h=int((n - 1) * VGAP * 78) + 150)


# ============================================================================
# THE STRUCTURAL-ENGINEERING-TO-AI MAPPING
# Left column: the structural process. Right column: the AI process.
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
        fig.add_annotation(x=8.4, y=y, text=f"PH{s['phase']+1:02d}", showarrow=False,
                           xanchor="left", font=dict(size=9, color="#3f4650", family=MONOF))

    fig.add_annotation(x=0, y=n - 0.35, text="◤ STRUCTURAL ENGINEERING PROCESS",
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
        f"<div class='brief-bar'>PROJECT BRIEF · DWG SHM-DT-001 · REV A · {len(PHASES)} PHASES / {len(STEPS)} STEPS</div>"
        f"<div style='font-size:32px;font-weight:800;color:{TEXT}'>🌉 &nbsp;An AI-Powered Bridge Digital Twin</div>"
        f"</div>",
        unsafe_allow_html=True)
    st.write("")

    # ---------------------------------------------- SECTION 1: THE PROBLEM
    _op_header("01", "The Engineering Problem", CIVIL)
    st.markdown("""
A bridge deteriorates **continuously** — cracks grow, steel corrodes, fatigue builds — but it is inspected
**by eye only once every one or two years**. Hidden damage can progress unseen between inspections, and by
the time it shows, the repair is costly or the bridge closes. The job: **watch it continuously and predict
its future condition before dangerous damage becomes visible.**
    """)
    st.divider()

    # ---------------------------------------------- SECTION 2: THE GOAL
    _op_header("02", "What We Are Going To Build", CIVIL)
    st.markdown("An **AI-powered bridge digital twin** — a live virtual copy of the bridge. Concretely, four parts:")
    c1, c2, c3, c4 = st.columns(4)
    for col, (icon, title, body) in zip(
        (c1, c2, c3, c4),
        [("📡", "Sensors read the structure",
          "Strain, vibration, natural frequency, tilt, crack width, corrosion, temperature and traffic "
          "load. Sampled continuously, on every span, not once every two years."),
         ("🚁", "The drone reads the surface",
          "The concrete and steel surfaces, where a hairline crack or a rust bloom hides in the image — not "
          "in any single gauge reading."),
         ("📅", "AI forecasts the condition",
          "Estimate each component's condition, learn its normal seasonal behaviour, flag deviations, and "
          "forecast the Remaining Useful Life before damage is visible."),
         ("🔔", "The engineer gets a priority",
          "Not a black box. A clear call: inspect this pier within the month — this condition, this "
          "forecast, this crack — with the evidence shown, so a person decides.")]):
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
        f"color:{TEXT};line-height:1.65'>The inspector stays in charge and stays accountable. The system "
        f"handles the part one person cannot do alone: it watches every span, every minute, and forecasts "
        f"where the condition is heading. The goal is a <b>safer, better-maintained</b> network.</div>",
        unsafe_allow_html=True)
    st.divider()

    # ---------------------------------------------- SECTION 3: MIND MAP
    _op_header("03", "The Engineering Workflow", CIVIL)
    st.markdown(
        f"<div style='color:{MUTED};font-size:15px;line-height:1.6'>These are the {len(PHASES)} phases of "
        f"<b>one bridge digital-twin project</b>, in the order a real project runs them — from the first "
        f"sensor reading to a forecast and the maintenance it plans. "
        f"Every <b style='color:{CIVIL}'>amber node</b> is a structural activity. Every "
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
        f"<div style='color:{MUTED};font-size:15px;line-height:1.6'><b>Every AI concept here is a structural "
        f"activity you already understand</b> — the same thing, named differently by a different "
        f"profession. Read down the amber column and you have described a bridge-monitoring project. Read "
        f"down the cyan column and you have described a deep learning pipeline. They are the same column.</div>",
        unsafe_allow_html=True)
    st.write("")
    st.plotly_chart(mapping_figure(style), use_container_width=True, key="mapping")

    st.markdown(
        f"<div style='border-left:3px solid {AISIDE};padding:8px 0 8px 16px;font-size:16px;"
        f"color:{TEXT};line-height:1.65'>Each AI concept shows up because the structural work ran into "
        f"something one engineer could not do by hand. Only then does it get a technical name.</div>",
        unsafe_allow_html=True)
    st.write("")

    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("▶  Start: walk onto the bridge", use_container_width=True,
                     type="primary"):
            goto("in-service")
    with c2:
        st.caption(f"{len(PHASES)} phases · {len(STEPS)} steps · one bridge digital-twin project. "
                   "Every step opens with the structural activity, then the AI it becomes.")
