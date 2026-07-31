"""
bridge.py - the Manufacturing-Engineering -> AI teaching scaffold.
==================================================================
This module does not teach any NEW concept and it does not render any new
model, animation or asset. Every technical illustration lives in app.py /
story.py. This module wraps each stage renderer in a five-part structure so a
Mechanical / Manufacturing Engineering student always sees, on every page:

    Manufacturing Engineering  the on-plant context        (bridge.open_page)
    The Challenge              why the manual way runs out (bridge.open_page)
    AI Connection              + the bridge figure         (bridge.open_page)
    Technical Idea             <- the EXISTING renderer, untouched
    Key Takeaway               one sentence                (bridge.close_page)
    In the Notebook            where it lives              (bridge.close_page)

Text is deliberately short and professional. Short sentences, active voice, no
drama. The visuals carry the page; the text supports them.

COLOR IS A TEACHING DEVICE. Amber is ALWAYS the manufacturing / plant world.
Cyan is ALWAYS the AI world. Violet is ALWAYS the technical process.
"""
import streamlit as st
import plotly.graph_objects as go

# ---------------------------------------------------------------- palette
BG, PANEL = "#0e1117", "#161b22"
CIVIL = "#ffb74d"      # amber  - the plant / manufacturing engineering
AISIDE = "#4fc3f7"     # cyan   - the AI
TECH = "#ba68c8"       # violet - the technical process
GREEN, RED = "#66bb6a", "#ef5350"
MUTED, TEXT = "#8b949e", "#e6edf3"

# ---- Energy-control-room display language (SCADA mimic panel)
# Same amber/cyan/violet theme; a distinct LOOK from the sibling apps: monospace
# telemetry readouts, bracketed station labels, corner-tick spec cards, a faint
# mimic grid and a shift-progress rail.
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
  background-size: 30px 30px;
}
hr { border-color:#2b3440 !important; }
[data-testid="stCaptionContainer"] p { font-family:%(MONO)s; letter-spacing:.02em; }
.stButton>button {
  border-radius:2px; border:1px solid #3a4655; background:#141b24;
  text-transform:uppercase; letter-spacing:.07em; font-size:12px; font-weight:600;
}
.stButton>button:hover { border-color:#ffb74d; color:#ffb74d; }
[data-testid="stMetric"] {
  background:#141b24; border:1px solid #2b3440; border-left:3px solid #66bb6a;
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
  border-color:#66bb6a; }
.brief::before { top:-1px; left:-1px; border-top:2px solid; border-left:2px solid; }
.brief::after { bottom:-1px; right:-1px; border-bottom:2px solid; border-right:2px solid; }
.brief-bar { font-family:%(MONO)s; font-size:12px; letter-spacing:.16em; color:#66bb6a; margin-bottom:8px; }
.card-ico { display:inline-flex; align-items:center; justify-content:center; width:40px; height:40px;
  border:1px solid #2b3440; border-radius:2px; font-size:22px; margin-bottom:8px; background:#0b0e13; }
.muted { color:#8b949e; font-size:13px; }
.substep { font-family:%(MONO)s; color:#8b949e; font-size:13px; }
</style>
""" % {"MONO": MONOF}


def inject_css():
    """Load the energy-console display language once. Call after st.set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def _op_header(op, label, color):
    st.markdown(
        f"<div class='op-row'>"
        f"<span class='op-num' style='color:{color};border-color:{color}'>PT·{op}</span>"
        f"<span class='op-label' style='color:{color}'>{label}</span>"
        f"<span class='op-rule'></span></div>", unsafe_allow_html=True)


# ============================================================================
# THE ENGINEERING WORKFLOW
# The phases of making a production plant measurably more sustainable without
# losing output. Every AI concept hangs off one of them. The last one is the
# ledger the work is judged by.
# ============================================================================
PHASES = [
    ("The Plant In Production",   "Three shifts draw power continuously; the bill arrives once a month."),
    ("One Production Hour",       "One hour of operation becomes a record of what the plant consumed."),
    ("Instrumenting The Plant",   "Meters are fitted, and the factory becomes a continuous data stream."),
    ("Preparing The Data",        "Bad readings are removed, every channel is scaled, and the data is split."),
    ("Energy From The Readings",  "A model predicts energy, carbon and waste from the meter log alone."),
    ("The Thermal Image Wall",    "The camera arrives, and no hand-written temperature rule works well enough."),
    ("How A Machine Learns",      "A trained network takes over from the auditor's trained judgement."),
    ("Reading The Heat Pattern",  "A CNN grades a thermal frame that no fixed rule could grade."),
    ("Locating The Loss",         "A CNN finds the leak and shows where it looked."),
    ("The Sustainability Audit",  "We check every prediction to see whether it worked."),
    ("Prediction & Optimisation", "Learn normal, spot the excess, find the efficient point, fuse it all."),
    ("The Business Case",         "Kilowatt-hours, tonnes of CO2 and money the plant actually keeps."),
]


# ============================================================================
# THE STEPS  (one per page; len(STEPS) is the count - do not hardcode it)
#   civil / ai   - the two names of the same idea (amber name, cyan name)
#   tech         - what is actually computed (violet)
#   site         - Manufacturing Engineering. NO AI in this text. 2-4 sentences.
#   challenge    - The Challenge. Why the manual way runs out of road.
#   ai_link      - AI Connection. Why this AI concept is therefore required.
#   takeaway     - Key Takeaway. ONE sentence.
#   notebook     - In the Notebook. Where this lives in the Colab notebook.
#   contributes  - In the Notebook. What this step contributes to the system.
# ============================================================================
STEPS = [

# ---------------------------------------------- PHASE 1 - THE PLANT IN PRODUCTION
dict(
    id='in-production', phase=0,
    civil='A Plant Under Load', ai='Why Sustainable Manufacturing Needs AI',
    civil_icon='🏭', ai_icon='🤖',
    tech="Continuous consumption vs a monthly energy report",
    civil_bullets=['Three shifts, no pause', 'Waste starts silently', 'Reviewed monthly'],
    ai_bullets=['Watch every hour', 'Model the drivers', 'Flag it while it runs'],
    site="""A production plant runs three shifts. Compressors, motors, ovens, pumps and ventilation draw power
around the clock. Electricity is one of the largest controllable costs on the site, and every kilowatt-hour
carries a carbon figure the company has to report.""",
    challenge="""Consumption is continuous; review is not. The energy bill arrives monthly, long after the waste
happened. A leaking air line, a badly scheduled oven or an idling line can burn power for weeks before
anyone reads about it in a report.""",
    ai_link="""The plant does not need its engineers replaced. It needs the gap between the meter and the report
closed - consumption watched continuously and waste identified while it is still happening. That
continuous watch, impossible to keep by hand across every machine, is why AI belongs on the shop floor.""",
    notebook="""Act 1. The consumption curve, and the gap between when waste starts and when the monthly report shows it.""",
    contributes="""The requirement the system is measured against. If waste is still found on the invoice, it failed.""",
    takeaway="""Energy is wasted every hour; the bill only reports it every month. The system closes that gap.""",
),
dict(
    id='enter-ai', phase=0,
    civil='A Plant That Reports Itself', ai='The Sustainability Monitor',
    civil_icon='📡', ai_icon='🛰️',
    tech='Metered every minute, not reviewed every month',
    civil_bullets=['Engineers stay', 'Meters watch too', 'Nobody is replaced'],
    ai_bullets=['A live energy picture', 'It flags the waste', 'You still decide'],
    site="""Nothing about the process changes. Same machines, same product, same quality plan. The energy engineer
still walks the floor and still signs the report. Meters are added - power, compressed air, temperature,
CO2, flow - and a thermal camera photographs equipment on a schedule.""",
    challenge="""The usual objection: is this here to replace the energy engineer? No. A model that sees only numbers
cannot hear a bearing, judge whether a hot pipe is a design feature, or authorise a shutdown. It can only
notice a change and estimate what it costs.""",
    ai_link="""The system is a sustainability monitor: a live picture of where energy and carbon go, updated by the
plant's own sensors. It fixes the role of AI for the whole project - the monitor reports and recommends;
a person decides and signs off. Every later choice, especially the audit, follows from that split.""",
    notebook="""No code. This step is the argument, not the arithmetic.""",
    contributes="""Defines the system's output: a recommendation to an engineer, not an automatic shutdown.""",
    takeaway="""The monitor reports and recommends. The engineer decides and signs off.""",
),

# ---------------------------------------------- PHASE 2 - ONE PRODUCTION HOUR
dict(
    id='reading', phase=1,
    civil='One Production Hour', ai='Data Collection',
    civil_icon='📏', ai_icon='🗄️',
    tech='One hour → one row of readings + energy and CO2',
    civil_bullets=['Eight channels', 'Logged every hour', 'Outcome recorded'],
    ai_bullets=['One row per hour', 'Eight features', 'Two targets'],
    site="""At the end of every production hour the plant records what it did: machine load, motor temperature,
compressed-air pressure and flow, idle share, units produced, material consumed, and the ambient
temperature in the hall.""",
    challenge="""On their own these are eight scattered readings on eight screens. No single number tells you whether
that hour was efficient, and comparing hours by eye across a month of three-shift operation is not work a
person can keep up with.""",
    ai_link="""Put them in one row and the hour becomes a record: eight inputs, and the energy and CO2 that resulted.
Thousands of those rows are a dataset - the raw material every model in this course learns from.""",
    notebook="""Section 2. Build one row from the plant physics, then the whole log.""",
    contributes="""The unit of learning. Everything downstream is rows like this one.""",
    takeaway="""One production hour becomes one row: eight readings in, energy and carbon out.""",
),
dict(
    id='two-records', phase=1,
    civil='Meter Reading vs Thermal Image', ai='Two Kinds Of Data',
    civil_icon='🧾', ai_icon='🔀',
    tech='Eight named numbers, or 4,096 unnamed pixels',
    civil_bullets=['The meter log', 'The camera frame', 'Same waste, two views'],
    ai_bullets=['Named columns → ML', 'Raw pixels → DL', 'The fork in the road'],
    site="""Two records leave the plant every hour. The meter log - eight named numbers. And a thermal frame from
the camera on the compressor-room wall - a 64x64 grid of surface temperatures with no names at all.""",
    challenge="""Both describe the same waste. The meter says the hour used more power than it should have. The image
says where the heat is going. Neither is complete on its own, and they do not look like each other.""",
    ai_link="""Named columns suit Machine Learning: the engineer chooses the features, the model weights them. Raw
pixels do not - nobody can name 4,096 useful columns. That difference is the whole argument of this
course, and it is why both ML and Deep Learning appear.""",
    notebook="""Section 2. Print one row, then show one thermal frame as an array.""",
    contributes="""The fork in the road: numbers go to ML, images go to DL.""",
    takeaway="""Numbers arrive with names; images do not. That single difference splits ML from DL.""",
),

# ---------------------------------------------- PHASE 3 - INSTRUMENTING THE PLANT
dict(
    id='load', phase=2,
    civil='The Energy Log Arrives', ai='Loading The Dataset',
    civil_icon='📥', ai_icon='🐼',
    tech='CSV → DataFrame, 1,500 production hours',
    civil_bullets=['Historian export', 'One row per hour', 'A month of shifts'],
    ai_bullets=['read_csv', 'shape and dtypes', 'First look'],
    site="""The plant historian exports a month of production hours as a CSV: one row per hour, every meter channel,
plus the energy and CO2 that hour produced.""",
    challenge="""An export is not a dataset. Channels drop out when a gateway restarts, a saturated meter writes a fixed
maximum, and the same hour can appear twice after a resync. Opening the file in a spreadsheet tells you
almost nothing about any of that.""",
    ai_link="""Loading the file into a DataFrame is the first AI step. It gives you shape, column types and a first
look - the basis for everything the models will later assume about the data.""",
    notebook="""Section 3. `pd.read_csv`, `.shape`, `.head()`.""",
    contributes="""The dataset every later step reads from.""",
    takeaway="""The export is only raw material. Loading it is where the data work starts.""",
),
dict(
    id='inspect', phase=2,
    civil='Meter Health Check', ai='Data Inspection',
    civil_icon='🔍', ai_icon='📊',
    tech='Count gaps, stuck channels and impossible values',
    civil_bullets=['Did it report?', 'Is it stuck?', 'Is it possible?'],
    ai_bullets=['isna().sum()', 'describe()', 'duplicated()'],
    site="""Before trusting a month of readings, an engineer checks the instruments. Did the flow meter report all
month? Is the pressure channel stuck at a constant? Is anything physically impossible?""",
    challenge="""Faults hide in plain sight. A dead compressor meter reads 0.0 m3/h - a perfectly valid number that
happens to be a lie. A thermocouple fault writes 999 degrees. Averaged into a month, both quietly corrupt
every conclusion drawn afterwards.""",
    ai_link="""Data inspection is that instrument check, done in code: count missing values per channel, look at the
minimum and maximum, and see which rows repeat. It finds what a monthly average hides.""",
    notebook="""Section 4. `.isna().sum()`, `.describe()`, `.duplicated()`.""",
    contributes="""The fault list the cleaning step works from.""",
    takeaway="""Check the meters before you trust the readings - 0.0 and 999 are both faults, not data.""",
),

# ---------------------------------------------- PHASE 4 - PREPARING THE DATA
dict(
    id='clean', phase=3,
    civil='Dropouts & Stuck Meters', ai='Data Cleaning',
    civil_icon='🧹', ai_icon='🧼',
    tech='Drop duplicates, null the impossible, fill with the median',
    civil_bullets=['Repair the channel', 'Keep the hour', 'Never average a fault'],
    ai_bullets=['drop_duplicates', 'Mask impossibles', 'fillna(median)'],
    site="""A faulty channel is repaired or discounted before its readings reach a report. Nobody averages a stuck
gauge into a monthly figure and then defends the result.""",
    challenge="""Deleting every affected row throws away good readings from the other seven channels in that hour.
Keeping them poisons the average. Neither extreme is acceptable when the output is a capital-spend
recommendation.""",
    ai_link="""Cleaning does both: drop exact duplicates, mark impossible values as missing rather than deleting the
row, then fill the gaps with the channel's median - a value that ignores outliers by construction.""",
    notebook="""Section 5. `drop_duplicates`, mask the impossible, `fillna(median)`.""",
    contributes="""A dataset where every remaining number is physically possible.""",
    takeaway="""Repair the channel, not the hour: mark the impossible, fill with the median, keep the rest.""",
),
dict(
    id='normalize', phase=3,
    civil='Common Units', ai='Normalization',
    civil_icon='📐', ai_icon='⚖️',
    tech='Min-max every channel to 0-1',
    civil_bullets=['m3/h vs bar vs %', 'Different magnitudes', 'One chart, one loser'],
    ai_bullets=['Rescale to 0-1', 'Units disappear', 'Data decides weight'],
    site="""The channels do not share a scale. Air flow runs to 100 m3/h, line pressure sits near 6 bar, idle share
is a percentage. Plot them together and flow buries everything else.""",
    challenge="""A model that adds weighted inputs has the same problem. The largest-numbered channel dominates the sum,
not because it matters most but because its units are bigger. Bar is not smaller than m3/h in any
meaningful engineering sense.""",
    ai_link="""Normalization rescales every channel to 0-1 using its own minimum and maximum. Units disappear, and
importance is then decided by the data instead of by the choice of unit.""",
    notebook="""Section 6. `MinMaxScaler().fit_transform`.""",
    contributes="""Comparable channels, so learned weights mean something.""",
    takeaway="""Rescale every channel to 0-1 so units stop deciding importance.""",
),
dict(
    id='split', phase=3,
    civil='Known Hours vs Sealed Hours', ai='Train / Test Split',
    civil_icon='🗂️', ai_icon='✂️',
    tech='70 / 15 / 15, stratified',
    civil_bullets=['Tune on one set', 'Prove on another', 'Never the same one'],
    ai_bullets=['Train 70%', 'Validate 15%', 'Test 15%, sealed'],
    site="""A commissioning test is not run on the same load case that was used to tune the plant. You prove
performance on a case the settings have never seen.""",
    challenge="""A model checked on the same hours it learned from will look excellent and mean nothing. It can memorise
the log completely and still fail on next week's production.""",
    ai_link="""The split seals part of the data away: 70% to train on, 15% to tune with, and 15% never touched until
the final audit. Only that sealed part gives an honest number.""",
    notebook="""Section 7. `train_test_split`, stratified, applied twice.""",
    contributes="""The sealed set the final audit is run on.""",
    takeaway="""Seal a portion of the log away. A score on data the model has already seen is not a score.""",
),

# ---------------------------------------------- PHASE 5 - ENERGY FROM THE READINGS
dict(
    id='ml-baseline', phase=4,
    civil='Energy From The Readings', ai='Machine Learning Baseline',
    civil_icon='⚡', ai_icon='🌲',
    tech='Random Forest: 8 readings → kWh, CO2, waste flag',
    civil_bullets=['What should it cost?', 'Was it wasteful?', 'From the log alone'],
    ai_bullets=['Threshold questions', 'Many trees averaged', 'Regression + class'],
    site="""The first question the plant asks is simple: given this hour's readings, how much energy and CO2 should
it have produced, and was the hour wasteful?""",
    challenge="""A spreadsheet formula built from machine nameplates gets the order of magnitude right and the details
wrong. Load, idle share, air leaks and ambient heat all interact, and no single hand-written formula
tracks them together across a month.""",
    ai_link="""A Random Forest learns that relationship from the log. It asks a sequence of threshold questions on the
named channels - load above 70%, flow above 60 m3/h - and averages many such trees into a prediction of
kWh, CO2 and a waste flag.""",
    notebook="""Section 8. `RandomForestRegressor` for kWh and CO2, `RandomForestClassifier` for the waste flag.""",
    contributes="""The numeric half of the system, and the baseline Deep Learning has to beat on images.""",
    takeaway="""Machine Learning predicts energy and carbon well - from named columns only.""",
),
dict(
    id='drivers', phase=4,
    civil='What Drives The Bill', ai='Feature Importance',
    civil_icon='📈', ai_icon='🎚️',
    tech='Which channel moves the energy prediction most',
    civil_bullets=['Which lever?', 'Compressor or schedule?', 'Rank the causes'],
    ai_bullets=['feature_importances_', 'A priority list', 'Check against intuition'],
    site="""Knowing that an hour was wasteful is not actionable. The plant needs to know which lever to pull: the
compressors, the production schedule, the ovens, or the ventilation set point.""",
    challenge="""Eight channels move together. Load rises, motor temperature rises, air flow rises. Reading a correlation
table tells you what moved with what, not what actually mattered to the outcome.""",
    ai_link="""Feature importance ranks how much each channel changes the model's prediction. It turns a black box into
an engineering priority list - and it is the first place a model's answer can be checked against plant
intuition.""",
    notebook="""Section 8. `.feature_importances_`, sorted and plotted.""",
    contributes="""The ranking that decides which recommendation the fusion engine issues.""",
    takeaway="""A ranked driver list turns a prediction into a decision about what to fix first.""",
),

# ---------------------------------------------- PHASE 6 - THE THERMAL IMAGE WALL
dict(
    id='thermal-problem', phase=5,
    civil='The Thermal Camera', ai='The Raw Image',
    civil_icon='🌡️', ai_icon='🖼️',
    tech='A 64x64 grid of temperatures, no named columns',
    civil_bullets=['Bright is hot', 'Cold plume = air leak', 'Bright blob = bearing'],
    ai_bullets=['4,096 numbers', 'No column names', 'Nothing to weight'],
    site="""The thermal camera looks at the compressor room. A frame is a grid of surface temperatures: bright is
hot, dark is cold. A leaking air joint shows as a cold plume; a failing bearing shows as a small bright
blob on the motor housing.""",
    challenge="""The camera does not output "leak" or "bearing". It outputs 4,096 numbers with no names. There is no
column called plume, and there is no row an engineer can look up.""",
    ai_link="""This is where Machine Learning runs out. It needs named features and there are none - only pixels.
Before reaching for a new method, it is worth trying to build those features by hand and watching exactly
what happens.""",
    notebook="""Section 9. Build a thermal frame as an array and display it.""",
    contributes="""The data type that forces the second half of the course.""",
    takeaway="""A thermal frame is 4,096 unnamed numbers. Machine Learning has nothing to weight.""",
),
dict(
    id='handmade', phase=5,
    civil='Average Temperature By Hand', ai='Hand-Made Features',
    civil_icon='✋', ai_icon='🔢',
    tech='One number from 4,096 pixels - and what it loses',
    civil_bullets=['Reduce to a mean', 'Set an alarm limit', 'Exactly as before'],
    ai_bullets=['One feature', 'One threshold', 'It misses'],
    site="""The obvious workaround is the one every engineer tries first: reduce the image to a number. Average
surface temperature. Then threshold it, exactly the way an alarm limit already works.""",
    challenge="""Averaging destroys the evidence. A small cold plume moves the mean by a fraction of a degree, while
afternoon sun on the wall moves it by several. The rule fires on the sunlight and misses the leak.""",
    ai_link="""The feature was hand-made, and it was the wrong feature. You could add ten more - variance, maximum,
edge count - and still be guessing. Deep Learning removes the guessing by learning the features from the
images themselves.""",
    notebook="""Section 9. Compute the mean temperature of each frame and try to separate them.""",
    contributes="""The failed baseline that justifies the CNN.""",
    takeaway="""One hand-made number cannot hold a pattern - the mean fires on sunlight and misses the leak.""",
),
dict(
    id='why-dl', phase=5,
    civil='The Rulebook Runs Out', ai='Why Deep Learning',
    civil_icon='🚧', ai_icon='🧠',
    tech='Learn the features instead of naming them',
    civil_bullets=['No threshold works', 'Rules keep breaking', 'Every camera differs'],
    ai_bullets=['Features are learned', 'From labelled frames', 'Not hand-picked'],
    site="""The rulebook has run out. There is no threshold on average temperature, and no combination of two or
three hand-picked numbers, that separates a leak plume from a sunlit wall.""",
    challenge="""You could keep writing rules - a gradient here, a shape factor there - and each new machine, camera
angle or season would break them. That maintenance never ends.""",
    ai_link="""Deep Learning inverts the job. Instead of naming features and letting the model weight them, the model
learns which features matter directly from labelled images. That is the entire difference, and the reason
the second half of this course exists.""",
    notebook="""Section 10. The framing, before any network is built.""",
    contributes="""The decision to use a CNN, made for a reason rather than by default.""",
    takeaway="""Machine Learning weights the features you name. Deep Learning finds the features you cannot name.""",
),

# ---------------------------------------------- PHASE 7 - HOW A MACHINE LEARNS
dict(
    id='engineer-brain', phase=6,
    civil='How An Energy Auditor Decides', ai='The Neuron, Informally',
    civil_icon='👷', ai_icon='💡',
    tech='Weigh the signals, add them, decide',
    civil_bullets=['Several signals at once', 'Some matter more', 'One call'],
    ai_bullets=['Weights', 'A sum', 'A threshold'],
    site="""An energy auditor walking the floor weighs several signals at once - the hiss at a fitting, the pressure
drop on the line, the compressor's duty cycle, the time of day - and calls it a leak or not.""",
    challenge="""That judgement is fast and good, but it lives in one head, works one machine at a time, and cannot be
applied to eight hundred hours of log data overnight.""",
    ai_link="""Write the judgement down and it is arithmetic: multiply each signal by how much it matters, add the
results, and act if the total clears a threshold. That is a neuron - the auditor's rule of thumb, made
explicit and repeatable.""",
    notebook="""Section 11. The weighted-sum decision, before any terminology.""",
    contributes="""The intuition every later network is built on.""",
    takeaway="""A neuron is an auditor's judgement written as arithmetic: weigh, add, decide.""",
),
dict(
    id='neuron', phase=6,
    civil='Weighing The Signals', ai='The Neuron',
    civil_icon='⚖️', ai_icon='🔵',
    tech='z = w·x + b',
    civil_bullets=['Flow matters a lot', 'Ambient matters little', 'Experience = weights'],
    ai_bullets=['Weights are learned', 'Bias sets the baseline', 'Traceable to data'],
    site="""Give each signal a weight. Excess air flow matters a great deal for a leak. Ambient temperature matters a
little. The auditor's experience is exactly that set of weights.""",
    challenge="""Those weights are guesses, and every auditor guesses differently. Nobody can defend a number like "flow
counts 3.4 times more than ambient" from experience alone.""",
    ai_link="""A neuron computes a weighted sum plus a bias. The weights are not chosen by anyone - they are learned
from the log, so the model's opinion is traceable to data instead of to seniority.""",
    notebook="""Section 11. `z = w·x + b`, computed by hand.""",
    contributes="""The single unit every network in the course is built from.""",
    takeaway="""A neuron is a weighted sum plus a bias, and the weights come from the data.""",
),
dict(
    id='activation', phase=6,
    civil='The Alarm Threshold', ai='Activation Function',
    civil_icon='🚨', ai_icon='📉',
    tech='sigmoid and ReLU',
    civil_bullets=['Acceptable or not', 'A hard limit is brittle', 'Reality is graded'],
    ai_bullets=['Sigmoid → 0..1', 'ReLU passes positives', 'Smooth = trainable'],
    site="""An alarm does not report a weighted sum. It reports a state: acceptable, or investigate. Somewhere the
continuous signal has to become a decision.""",
    challenge="""A hard on/off limit is brittle. An hour a hair under the limit is treated as perfectly fine, and one a
hair over triggers a callout. Real plant condition does not step like that.""",
    ai_link="""An activation function does the same job smoothly. Sigmoid turns any sum into a number between 0 and 1
that reads as a probability. ReLU passes positive evidence and blocks the rest. That smoothness is also
what makes the network trainable at all.""",
    notebook="""Section 12. Plot sigmoid and ReLU, and pass `z` through both.""",
    contributes="""The step that turns a raw sum into a usable probability.""",
    takeaway="""Activation turns a weighted sum into a graded decision instead of a brittle limit.""",
),
dict(
    id='learning-loop', phase=6,
    civil='Learning From A Missed Leak', ai='The Learning Loop',
    civil_icon='🔁', ai_icon='🎯',
    tech='predict → error → adjust → repeat',
    civil_bullets=['The bill shows the miss', 'Adjust the judgement', 'Do better next month'],
    ai_bullets=['Compare to truth', 'Measure the error', 'Nudge every weight'],
    site="""A leak is missed. The following month's bill shows it. The auditor adjusts: next time, weight the flow
reading more heavily and the ambient reading less.""",
    challenge="""Done by hand, that correction happens once per bill and depends entirely on who is looking. Eight
channels and thousands of hours cannot be tuned that way.""",
    ai_link="""The learning loop is that correction, automated: predict, compare with the recorded truth, measure the
error, adjust every weight a little, repeat. Thousands of times, on every row.""",
    notebook="""Section 13. The loop, shown before the optimiser has a name.""",
    contributes="""The mechanism that turns a random model into a useful one.""",
    takeaway="""Predict, measure the error, adjust, repeat - that loop is all training is.""",
),
dict(
    id='gradient-descent', phase=6,
    civil='Tuning The Plant', ai='Loss & Gradient Descent',
    civil_icon='🎛️', ai_icon='⛰️',
    tech='loss surface, gradient, learning rate',
    civil_bullets=['Change a set point', 'Measure the result', 'Step again'],
    ai_bullets=['Loss = how wrong', 'Gradient = downhill', 'Rate = step size'],
    site="""Commissioning a plant is a search. Change a set point, measure the result, keep the change if it
improved things, and step again in the direction that helped.""",
    challenge="""Step too far and you overshoot and oscillate. Step too small and commissioning takes a week. The step
size is the whole difficulty, and it is usually chosen by feel.""",
    ai_link="""Loss measures how wrong the model is. Gradient descent takes the downhill direction and steps along it;
the learning rate is the step size. The same overshoot and the same slowness appear, for exactly the same
reason.""",
    notebook="""Section 13. A loss surface, and the descent path at three learning rates.""",
    contributes="""How the weights actually change during training.""",
    takeaway="""Training is commissioning by search: step downhill on the error, and mind the step size.""",
),
dict(
    id='network', phase=6,
    civil='The Energy Team', ai='The Neural Network',
    civil_icon='👥', ai_icon='🕸️',
    tech='input → hidden layers → output',
    civil_bullets=['Air specialist', 'Thermal specialist', 'Schedule specialist'],
    ai_bullets=['Each neuron, a view', 'Layers combine them', 'One output'],
    site="""No single auditor covers everything. One reads the compressed-air system, one the thermal side, one the
production schedule. A supervisor combines their calls into a decision.""",
    challenge="""Coordinating specialists is slow, and their reports are inconsistent. Some overlap, some contradict, and
nobody weighs them the same way twice.""",
    ai_link="""A hidden layer is that team. Each neuron learns a different combination of the readings, and the output
neuron weighs their conclusions into one answer. Depth is what lets a model represent interactions a
single weighted sum cannot.""",
    notebook="""Section 14. `MLPClassifier(hidden_layer_sizes=(12, 6))`.""",
    contributes="""The numeric neural network, ready to be compared with the forest.""",
    takeaway="""A layer is a team of specialists; the output neuron is the supervisor who signs the call.""",
),
dict(
    id='training', phase=6,
    civil='Learning From The Log', ai='Training',
    civil_icon='📚', ai_icon='🏋️',
    tech='epochs, training vs validation loss',
    civil_bullets=['Learn from records', 'Not from a textbook', 'Then prove it'],
    ai_bullets=['Many epochs', 'Watch validation', 'Stop at the turn'],
    site="""A new auditor learns from the site's own records - a month of hours where the outcome is already known -
not from a textbook written for another factory.""",
    challenge="""Learn the records too well and you have memorised them: perfect on last month, useless on next month.
Stop too early and nothing has been learned at all.""",
    ai_link="""Training runs the learning loop over the training rows for many epochs, and watches the loss on
validation rows it never learns from. When validation loss stops falling, learning has become memorising.""",
    notebook="""Section 14. Loss curves for training and validation.""",
    contributes="""The trained numeric model used in the audit.""",
    takeaway="""Watch the validation curve - where it turns, learning has become memorising.""",
),

# ---------------------------------------------- PHASE 8 - READING THE HEAT PATTERN
dict(
    id='cnn-journey', phase=7,
    civil='Reading The Heat Pattern', ai='Convolution & Feature Maps',
    civil_icon='🔥', ai_icon='🧩',
    tech='filters → feature maps → classification',
    civil_bullets=['A cone at a fitting', 'A disc on a housing', 'Shape, not brightness'],
    ai_bullets=['Filters slide', 'Edges → plumes', 'Filters are learned'],
    site="""A thermal frame is not read pixel by pixel. An engineer sees a shape: a cone spreading from a fitting, or
a compact bright disc on a motor housing.""",
    challenge="""Shape cannot be captured by any single pixel value, and it moves. The same leak appears at a different
position, size and angle in every frame the camera takes.""",
    ai_link="""A convolution slides a small filter over the image and reports where its pattern occurs. Early filters
find edges; later ones combine edges into plumes and blobs. The network learns the filters, and because
they slide, the pattern is found anywhere in the frame.""",
    notebook="""Section 15. Convolve a frame by hand, then train a small CNN.""",
    contributes="""The visual half of the system: a grade for every thermal frame.""",
    takeaway="""Convolution learns to find a shape anywhere in the frame, without anyone naming it.""",
),

# ---------------------------------------------- PHASE 9 - LOCATING THE LOSS
dict(
    id='leak-locate', phase=8,
    civil='Where Is The Loss?', ai='Grad-CAM',
    civil_icon='📍', ai_icon='🗺️',
    tech='class-weighted feature maps → heat map',
    civil_bullets=['Which fitting?', 'Which run?', 'Raise a work order'],
    ai_bullets=['Weight the maps', 'Project onto the frame', 'Show the evidence'],
    site="""A grade on its own does not get a work order raised. The maintenance team needs to know which fitting, on
which pipe run, to go and check.""",
    challenge="""A classifier outputs a probability. It gives no location, and an engineer asked to act on a bare number
will - rightly - not trust it.""",
    ai_link="""Grad-CAM weights the last feature maps by how much each contributed to the answer, then projects them
back onto the frame. The result is a heat map showing where the network looked, which is both the
location and the evidence.""",
    notebook="""Section 16. Grad-CAM over the trained CNN.""",
    contributes="""The location and the justification that make the alert actionable.""",
    takeaway="""Grad-CAM shows where the network looked - that is both the location and the evidence.""",
),

# ---------------------------------------------- PHASE 10 - THE SUSTAINABILITY AUDIT
dict(
    id='audit', phase=9,
    civil='The Energy Audit', ai='Confusion Matrix',
    civil_icon='🧮', ai_icon='✅',
    tech='TP / FP / FN / TN and what each costs',
    civil_bullets=['Predicted vs metered', 'On sealed hours', 'Every claim checked'],
    ai_bullets=['Four outcomes', 'False alarm ≠ miss', 'Recall matters'],
    site="""Every energy-saving claim is audited: predicted saving against metered saving, on hours the model was
never allowed to see.""",
    challenge="""A single accuracy figure hides the thing that matters. Predicting "not wasteful" for every hour scores
well on a plant that is efficient most of the time - and finds nothing at all.""",
    ai_link="""The confusion matrix separates the four outcomes. A false alarm costs an engineer an hour of walking the
floor. A missed leak costs a month of compressed air. They are not equal, and the audit has to show both.""",
    notebook="""Section 17. Confusion matrix, accuracy and recall on the sealed set.""",
    contributes="""The honest performance number the whole project is judged on.""",
    takeaway="""Accuracy hides the costly error; the confusion matrix shows the missed leak.""",
),
dict(
    id='proof', phase=9,
    civil='The Verdict', ai='ML vs DL, Proven',
    civil_icon='⚔️', ai_icon='🏁',
    tech='the same task, both methods, measured',
    civil_bullets=['Two data types', 'Two methods', 'One plant'],
    ai_bullets=['Forest wins on numbers', 'CNN wins on pixels', 'Neither replaces the other'],
    site="""Two models, two data types, one plant. Time to state plainly what each one can and cannot do.""",
    challenge="""It is tempting to declare Deep Learning the better method. It is not better - it is different, and on
the meter log the forest is faster, cheaper and far easier to explain to an auditor.""",
    ai_link="""Run both on both. The forest wins on the eight named channels. It cannot take a thermal frame at all.
The CNN grades the frame, and would need those pixels flattened into meaningless columns before it could
touch the log. Each method belongs to its data type.""",
    notebook="""Section 18. The comparison table, filled in from measured results.""",
    contributes="""The course's central claim, demonstrated rather than asserted.""",
    takeaway="""ML weights the columns you name; DL finds the patterns you cannot name. Different data, different tool.""",
),

# ---------------------------------------------- PHASE 11 - PREDICTION & OPTIMISATION
dict(
    id='anomaly', phase=10,
    civil='Normal For This Load', ai='Anomaly Detection',
    civil_icon='📊', ai_icon='🚩',
    tech='expected kWh vs actual → residual → alarm',
    civil_bullets=['Hot day costs more', 'Full schedule costs more', 'That is not waste'],
    ai_bullets=['Learn normal', 'Score the residual', 'Alarm on the excess'],
    site="""Energy use is supposed to rise with machine load and with ambient temperature. A hot afternoon on a full
schedule costs more than a cool night on a light one, and that is not waste.""",
    challenge="""Because normal moves, a fixed kWh alarm limit is useless. Set it high and leaks hide inside a busy
shift; set it low and it cries wolf on every summer afternoon.""",
    ai_link="""Anomaly detection learns what normal looks like for this load and this weather, then scores the residual
- the part of the consumption the conditions do not explain. A leak is exactly that: an unexplained
excess.""",
    notebook="""Section 19. Regress energy on load and ambient, then alarm on the residual.""",
    contributes="""The detector that catches waste no fixed threshold would ever see.""",
    takeaway="""Alarm on the unexplained excess, not on the raw kilowatt-hours.""",
),
dict(
    id='optimize', phase=10,
    civil='The Efficient Operating Point', ai='Optimisation',
    civil_icon='🎯', ai_icon='🧭',
    tech='sweep the load → predict kWh → minimise kWh per unit',
    civil_bullets=['How hard to load?', 'How much idle?', 'When to schedule?'],
    ai_bullets=['Sweep the range', 'Predict each point', 'Read off the minimum'],
    site="""The plant has room to choose how it runs: how hard machines are loaded, how much of the hour they spend
idling, and when the high-draw processes are scheduled.""",
    challenge="""Energy per unit is not lowest at the lowest load. Baseload - lighting, ventilation, standby compressors
- is spread across fewer units, so running gently can cost more carbon per part, not less. Intuition
points the wrong way here.""",
    ai_link="""With a model that predicts kWh from the readings, the operating range can simply be swept and the
specific energy read off. The minimum of that curve is the efficient operating point, and it moves with
leak severity and idle time.""",
    notebook="""Section 20. Sweep the load, predict kWh, plot kWh per unit and find the minimum.""",
    contributes="""The recommendation the dashboard turns into money and carbon.""",
    takeaway="""The greenest operating point is a minimum on a curve, not the lowest setting on the dial.""",
),
dict(
    id='fusion-engine', phase=10,
    civil='The Plant Sustainability Screen', ai='AI Fusion',
    civil_icon='🖥️', ai_icon='🔗',
    tech='ML score + DL grade + anomaly → one ranked action',
    civil_bullets=['Three opinions', 'One shift engineer', 'One action list'],
    ai_bullets=['Combine the outputs', 'Rank by cost', 'Attach the evidence'],
    site="""By now the plant produces three separate opinions every hour: a predicted energy and CO2 figure, an
anomaly score, and a thermal grade with a location.""",
    challenge="""Three screens is three chances to miss something. A shift engineer with a shift to run needs one ranked
list, not three dashboards to correlate by hand at the end of the day.""",
    ai_link="""Fusion combines them into one prioritised recommendation with its evidence attached: the excess in kWh,
the location on the frame, and the action to take. Numbers and images each contribute the part the other
cannot supply.""",
    notebook="""Section 21. A rules layer over both model outputs.""",
    contributes="""The product - one screen a shift engineer can act on.""",
    takeaway="""Numbers say how much is being lost; images say where. Fusion issues one action.""",
),
dict(
    id='pipeline', phase=10,
    civil='The Whole System', ai='The Pipeline',
    civil_icon='🧱', ai_icon='🛤️',
    tech='sensors → data → ML + DL → fusion → dashboard',
    civil_bullets=['Meters and camera', 'Models', 'A screen that acts'],
    ai_bullets=['Every stage feeds one', 'Data quality first', 'One recommendation'],
    site="""Step back and the whole system is visible: meters and a camera on the plant, a data path, two models,
and a screen the shift engineer reads.""",
    challenge="""Every stage depends on the ones before it. A stuck flow meter that survived cleaning becomes a false
recommendation four stages later, and nothing downstream can recover from it.""",
    ai_link="""The pipeline is the engineering drawing of the system. It shows what feeds what, where the two data
types split apart, and where they come back together into a single recommendation.""",
    notebook="""Section 22. The end-to-end run, in one place.""",
    contributes="""The map of everything built so far.""",
    takeaway="""The system is a chain: data quality at the start decides the recommendation at the end.""",
),

# ---------------------------------------------- PHASE 12 - THE BUSINESS CASE
dict(
    id='dashboard', phase=11,
    civil='The Sustainability Dashboard', ai='Energy, Carbon & Money',
    civil_icon='📉', ai_icon='💷',
    tech='kWh, tonnes of CO2 and cost, before and after',
    civil_bullets=['Approve a spend', 'Against a saving', 'With a payback'],
    ai_bullets=['kWh avoided', 'tCO2 avoided', 'Cost at site tariff'],
    site="""The plant manager does not buy a model. They approve a spend against a saving in kilowatt-hours, tonnes
of CO2 and money - with a payback period attached.""",
    challenge="""AI savings are easy to overstate. A recommendation only saves energy if someone acts on it, and only
part of the identified waste is economically worth fixing at all.""",
    ai_link="""The dashboard turns the model outputs into the plant's own units: kWh avoided per month, tonnes of CO2
per year, cost saved at the site tariff, and the share of consumption removed. Every figure is arithmetic
on assumptions the reader can change.""",
    notebook="""Section 23. The sustainability dashboard, computed from the assumptions above.""",
    contributes="""The business case - the reason the previous steps get funded.""",
    takeaway="""Sustainability is approved in kWh, tonnes and currency - not in accuracy percentages.""",
),
]

# ---------------------------------------------------------------- short labels
SHORT = {
    "in-production": "A plant under load",     "enter-ai": "The sustainability monitor",
    "reading": "One production hour",          "two-records": "Reading vs image",
    "load": "Energy log arrives",              "inspect": "Meter health check",
    "clean": "Dropouts & stuck meters",        "normalize": "Common units",
    "split": "Known vs sealed",                "ml-baseline": "Energy from readings",
    "drivers": "What drives the bill",         "thermal-problem": "The raw frame",
    "handmade": "Mean temperature by hand",    "why-dl": "Rulebook runs out",
    "engineer-brain": "Auditor decides",       "neuron": "Weighing signals",
    "activation": "Alarm threshold",           "learning-loop": "Learn from a miss",
    "gradient-descent": "Tune the plant",      "network": "The energy team",
    "training": "Learn from the log",          "cnn-journey": "Read the heat pattern",
    "leak-locate": "Locate the loss",          "audit": "The energy audit",
    "proof": "The verdict",                    "anomaly": "Normal vs excess",
    "optimize": "Efficient operating point",   "fusion-engine": "Sustainability screen",
    "pipeline": "The whole system",            "dashboard": "The dashboard",
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
# Left = the plant (amber). Right = the AI (cyan). Between them an animated
# signal bus, and under it the technical process (violet).
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
    """Mimic-panel registration marks at the four corners of a rect."""
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
    """The manufacturing-activity -> AI-equivalent -> technical-process bridge,
    drawn as an energy-console signal-flow block diagram."""
    fig = go.Figure()
    _card(fig, 0.2, 3.4, CIVIL, step["civil_icon"], step["civil"],
          step["civil_bullets"], "ON THE PLANT")
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

    # a "data packet" token travels the bus from the plant to the AI
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
        f"<div class='dro-bar' style='margin-top:14px'>⟨ECO-PLANT⟩ &nbsp; "
        f"STEP {i+1:02d}/{len(ORDER)} &nbsp;·&nbsp; PHASE {step['phase']+1:02d}/{len(PHASES)} "
        f"&nbsp;·&nbsp; <span style='color:{CIVIL}'>{pname.upper()}</span> "
        f"&nbsp;—&nbsp; {pdesc}</div>", unsafe_allow_html=True)
    st.markdown(f"# {step['civil_icon']}  {step['civil']}")
    st.markdown(
        f"<span class='substep'>▸ this manufacturing step is the AI concept </span>"
        f"<b style='color:{AISIDE}'>{step['ai']}</b>",
        unsafe_allow_html=True)
    st.divider()

    # ---- PT.10  Manufacturing Engineering ---------------------------------
    _op_header("10", "Manufacturing Engineering", CIVIL)
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
    st.caption("▶ Press Play — the data packet travels the bus from the plant into the AI.")
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
        f"<div class='travbar'><span class='travlab'>SHIFT</span>"
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
    'in-production': dict(
        q="The plant's monthly bill looks normal, yet the system still reports waste. Why is that possible?",
        options=["Monthly bills are always wrong",
                 "Consumption is continuous but review is monthly, so waste can start, run for weeks and be averaged into a normal-looking total",
                 "The meters are more accurate than the utility",
                 "Carbon and electricity are unrelated"],
        answer=1,
        why="A month is long enough for a leak to burn a large amount of energy and still disappear inside a normal-looking average."),
    'enter-ai': dict(
        q="What is the system's actual output?",
        options=["An automatic machine shutdown",
                 "A replacement for the energy engineer",
                 "A recommendation with evidence, which an engineer decides on",
                 "A monthly PDF report"],
        answer=2,
        why="The monitor reports and recommends; the engineer decides and signs off. That split governs every later design choice."),
    'reading': dict(
        q="Why is one production hour written as a single row rather than eight separate logs?",
        options=["It saves disk space",
                 "Because a row ties the eight inputs to the energy and CO2 that resulted, which is what a model learns from",
                 "Because meters can only write rows",
                 "So it fits on one screen"],
        answer=1,
        why="The row pairs cause with effect. Thousands of those pairs are the dataset."),
    'two-records': dict(
        q="What makes the meter log suit ML and the thermal frame suit DL?",
        options=["The log is bigger",
                 "Images are always harder",
                 "The log has named columns an engineer chose; the frame is 4,096 unnamed pixels nobody can name usefully",
                 "ML cannot handle decimals"],
        answer=2,
        why="ML weights features you name. Nobody can name 4,096 pixel columns, so the features have to be learned."),
    'load': dict(
        q="Why is a historian export not yet a dataset?",
        options=["It is in the wrong file format",
                 "It contains dropouts, saturated values and duplicate hours that a spreadsheet view will not reveal",
                 "It is too large for pandas",
                 "It has no header row"],
        answer=1,
        why="Loading it is only the first step; what is in it still has to be checked."),
    'inspect': dict(
        q="A compressed-air flow channel reads exactly 0.0 m3/h for 200 hours. What is it?",
        options=["A perfect result — no air used",
                 "A dead or disconnected meter writing a valid-looking number",
                 "Normal for a night shift",
                 "A rounding artefact"],
        answer=1,
        why="A running plant always uses some air. 0.0 is a valid number and a fault at the same time — exactly what inspection is for."),
    'clean': dict(
        q="Why fill a missing reading with the channel's median instead of its mean?",
        options=["The median is faster to compute",
                 "The mean is only valid for whole numbers",
                 "The median ignores the extreme faulty values that are still lurking in the column",
                 "The median is always larger"],
        answer=2,
        why="A single 999 shifts a mean badly. The median barely moves, so it is the safer fill for sensor data."),
    'normalize': dict(
        q="What actually goes wrong if the channels are not rescaled?",
        options=["The code crashes",
                 "The largest-numbered channel dominates the weighted sum because of its unit, not its importance",
                 "The data takes more memory",
                 "The plots look untidy"],
        answer=1,
        why="Bar and m3/h are not comparable magnitudes. Rescaling to 0-1 removes the unit's influence on the weights."),
    'split': dict(
        q="Why keep a sealed test set instead of scoring on all the data?",
        options=["To make training faster",
                 "Because a model scored on hours it learned from can memorise the log and still fail next week",
                 "Because sklearn requires it",
                 "To reduce the file size"],
        answer=1,
        why="Only data the model has never seen gives an honest estimate of what it will do on new production."),
    'ml-baseline': dict(
        q="Why does a Random Forest beat a nameplate spreadsheet formula here?",
        options=["It uses more decimal places",
                 "It learns how load, idle, leaks and ambient heat interact, from the plant's own log",
                 "It works on images too",
                 "It never makes mistakes"],
        answer=1,
        why="The interactions are what a fixed formula misses. The forest learns them from measured hours."),
    'drivers': dict(
        q="Feature importance ranks air flow first. What has it told you?",
        options=["Air flow causes all waste",
                 "The other channels can be deleted",
                 "The model's predictions move most with air flow, which points at the compressed-air system as the first place to look",
                 "The flow meter is broken"],
        answer=2,
        why="Importance is about how much the prediction moves, not proof of cause. It is a priority list, and it still has to be checked on the floor."),
    'thermal-problem': dict(
        q="Why can the Random Forest not simply take the thermal frame as input?",
        options=["The image is too large",
                 "There are no named features — only 4,096 pixel values with no engineering meaning individually",
                 "Forests only accept integers",
                 "The camera resolution is too low"],
        answer=1,
        why="ML weights named columns. A pixel at row 12 column 40 is not a feature anybody can name or defend."),
    'handmade': dict(
        q="Why does thresholding on mean surface temperature fail?",
        options=["The camera is not calibrated",
                 "The mean is computed incorrectly",
                 "A small cold plume barely moves the mean, while sunlight on the wall moves it a lot — so the rule fires on the wrong thing",
                 "Thresholds never work"],
        answer=2,
        why="Averaging discards the spatial pattern, which is the only place the evidence lived."),
    'why-dl': dict(
        q="What is the one-line difference between ML and DL as used here?",
        options=["DL is newer",
                 "DL needs less data",
                 "ML weights features a human names; DL learns the features itself from labelled examples",
                 "DL is always more accurate"],
        answer=2,
        why="That is the whole distinction. It also explains why DL is the wrong choice for the eight-channel meter log."),
    'engineer-brain': dict(
        q="An auditor weighs hiss, pressure drop and duty cycle, then calls a leak. What has been described?",
        options=["A confusion matrix",
                 "A neuron: weighted inputs, summed, compared to a threshold",
                 "A convolution",
                 "A train/test split"],
        answer=1,
        why="The neuron is not a new idea — it is the auditor's rule of thumb written as arithmetic."),
    'neuron': dict(
        q="In z = w·x + b, what does b do?",
        options=["Scales the inputs",
                 "Shifts the baseline, so the neuron can fire without every input being large",
                 "Counts the features",
                 "Selects the activation"],
        answer=1,
        why="The bias sets where the decision sits. Without it, the boundary is forced through the origin."),
    'activation': dict(
        q="Why not just use a hard on/off limit instead of a sigmoid?",
        options=["Sigmoid is faster",
                 "A hard limit treats 'just under' and 'just over' as opposites, and gives training no gradient to follow",
                 "Hard limits are not allowed in Python",
                 "Sigmoid uses less memory"],
        answer=1,
        why="The graded output is more honest about borderline hours, and its smoothness is what makes gradient descent possible."),
    'learning-loop': dict(
        q="What is the essential order of the learning loop?",
        options=["Adjust → predict → measure",
                 "Predict → compare with truth → measure error → adjust weights → repeat",
                 "Measure → stop",
                 "Split → normalize → predict"],
        answer=1,
        why="Every training algorithm in this course is that loop, repeated over the rows."),
    'gradient-descent': dict(
        q="The loss oscillates and never settles. What is the most likely cause?",
        options=["Too little data",
                 "The learning rate is too large, so each step overshoots the minimum",
                 "The loss function is wrong",
                 "Too many features"],
        answer=1,
        why="Same as over-adjusting a set point during commissioning: the correction is bigger than the error it is fixing."),
    'network': dict(
        q="What does adding a hidden layer buy you?",
        options=["Faster training",
                 "Neurons that each learn a different combination of the readings, so interactions a single weighted sum cannot express become representable",
                 "Fewer weights to store",
                 "Automatic data cleaning"],
        answer=1,
        why="One neuron draws one boundary. A layer of them, combined, draws the shape the data actually needs."),
    'training': dict(
        q="Training loss keeps falling but validation loss starts rising. What is happening?",
        options=["The data is corrupt",
                 "The model has started memorising the training hours instead of learning the pattern",
                 "The learning rate is too small",
                 "Training is finished successfully"],
        answer=1,
        why="That turn in the validation curve is where learning becomes memorising. Stop there."),
    'cnn-journey': dict(
        q="Why does a convolution find a leak plume wherever it appears in the frame?",
        options=["Because images are normalized",
                 "Because the same filter slides across every position, so the pattern is detected anywhere",
                 "Because the camera is fixed",
                 "Because the plume is always bright"],
        answer=1,
        why="That sliding is what gives a CNN its position independence — and it is why hand-picked global features fail."),
    'leak-locate': dict(
        q="What does Grad-CAM add to a CNN's probability?",
        options=["A higher accuracy",
                 "A faster prediction",
                 "A heat map of where the network looked, which is both the location to inspect and the evidence for the call",
                 "An automatic work order"],
        answer=2,
        why="A bare probability is not actionable. A location an engineer can verify is."),
    'audit': dict(
        q="A model predicts 'not wasteful' for every hour and scores 78% accuracy. What is wrong?",
        options=["Nothing — 78% is good",
                 "It never finds any waste, which is the entire point of the system; accuracy hides that",
                 "The test set is too small",
                 "Accuracy should be recomputed on the training set"],
        answer=1,
        why="Recall on the wasteful hours is the number that matters. The confusion matrix shows it; accuracy alone does not."),
    'proof': dict(
        q="What does the head-to-head comparison actually prove?",
        options=["Deep Learning is better than Machine Learning",
                 "Machine Learning is obsolete",
                 "Each method belongs to its data type: the forest wins on named channels, the CNN on raw pixels",
                 "Both perform identically"],
        answer=2,
        why="This is the central claim of the course, and it is demonstrated with measured numbers rather than asserted."),
    'anomaly': dict(
        q="Why score the residual instead of alarming on raw kWh?",
        options=["Residuals are smaller numbers",
                 "Because normal consumption moves with load and weather, so a fixed kWh limit either hides leaks or cries wolf",
                 "Because kWh is not measurable",
                 "To avoid using a model"],
        answer=1,
        why="The residual is the consumption the operating conditions do not explain — which is exactly what waste is."),
    'optimize': dict(
        q="Why is the lowest machine load not the greenest operating point?",
        options=["Low load damages machines",
                 "Baseload — lighting, ventilation, standby compressors — is spread over fewer units, so energy per unit rises",
                 "Low load increases scrap only",
                 "It is the greenest point"],
        answer=1,
        why="Specific energy is a curve with a minimum. Finding it is an optimisation, not an intuition."),
    'fusion-engine': dict(
        q="What does fusion add over the three separate model outputs?",
        options=["Higher individual accuracy",
                 "One ranked action with its evidence attached, instead of three screens to correlate by hand",
                 "Faster inference",
                 "Less data storage"],
        answer=1,
        why="Numbers say how much is being lost; the image says where. The value is in issuing one action from both."),
    'pipeline': dict(
        q="Why does a stuck flow meter that survives cleaning matter four stages later?",
        options=["It slows the code down",
                 "It does not — the model corrects it",
                 "Because the pipeline is a chain: a bad reading becomes a bad prediction and then a false recommendation",
                 "It only affects the plots"],
        answer=2,
        why="Nothing downstream can recover information that was wrong at the source. Data quality is a first-stage decision."),
    'dashboard': dict(
        q="Why does the dashboard report kWh, tonnes of CO2 and cost rather than model accuracy?",
        options=["Accuracy is confidential",
                 "Because a plant manager approves spend against savings in the plant's own units, with a payback",
                 "Because accuracy was too low",
                 "Because carbon is easier to measure"],
        answer=1,
        why="Every figure on it is arithmetic on assumptions the reader can change — which is what makes it a business case rather than a claim."),
}


def render_quiz(stage):
    """One check-your-understanding MCQ per stage. Portable across all the
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
    VGAP = 1.5                                   # vertical room per phase row
    ys = {i: (n - 1 - i) * VGAP for i in range(n)}

    for i in range(n - 1):
        fig.add_annotation(x=0, y=ys[i + 1] + 0.55, ax=0, ay=ys[i] - 0.62,
                           xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1.1,
                           arrowwidth=2, arrowcolor=CIVIL, text="")

    GAP = 3.4                                    # column pitch so labels clear
    X0 = 1.7
    maxk = max(len(_phase_steps(pi)) for pi in range(n))

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

    # the x range must cover the widest phase row, or its later steps fall off
    fig.update_xaxes(visible=False, range=[-7.0, X0 + (maxk - 1) * GAP + 2.2])
    fig.update_yaxes(visible=False, range=[-1.0, (n - 1) * VGAP + 0.6])
    return style(fig, h=int((n - 1) * VGAP * 78) + 150)


# ============================================================================
# THE MANUFACTURING-ENGINEERING-TO-AI MAPPING
# Left column: the plant process. Right column: the AI process.
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

    fig.add_annotation(x=0, y=n - 0.35, text="◤ MANUFACTURING ENGINEERING PROCESS",
                       showarrow=False, xanchor="left",
                       font=dict(size=12, color=CIVIL, family=MONOF))
    fig.add_annotation(x=4.6, y=n - 0.35, text="◤ THE AI PROCESS THAT SOLVES IT",
                       showarrow=False, xanchor="left",
                       font=dict(size=12, color=AISIDE, family=MONOF))

    fig.update_xaxes(visible=False, range=[-0.2, 9.0])
    fig.update_yaxes(visible=False, range=[-0.8, n + 0.2])
    return style(fig, h=1200)


# ============================================================================
# THE OPENING PAGE
# ============================================================================
def render_start(style, animate):
    st.markdown(
        f"<div class='brief'>"
        f"<div class='brief-bar'>PROJECT BRIEF · DWG ECO-MFG-001 · REV A · {len(PHASES)} PHASES / {len(STEPS)} STEPS</div>"
        f"<div style='font-size:32px;font-weight:800;color:{TEXT}'>🏭 &nbsp;AI for Sustainable Manufacturing</div>"
        f"</div>",
        unsafe_allow_html=True)
    st.write("")

    # ---------------------------------------------- SECTION 1: THE PROBLEM
    _op_header("01", "The Engineering Problem", CIVIL)
    st.markdown("""
A production plant runs **three shifts**. Compressors, motors, ovens, pumps and ventilation draw power
continuously, and every kilowatt-hour carries a **carbon figure**. Waste is real and ordinary: **compressed-air
leaks, heat loss through poor insulation, machines idling between jobs, scrap material, badly scheduled
high-draw processes.** But consumption is continuous and **review is monthly** — the bill arrives long after
the waste happened. The job: **cut energy, carbon and waste without losing output.**
    """)
    st.divider()

    # ---------------------------------------------- SECTION 2: THE GOAL
    _op_header("02", "What We Are Going To Build", CIVIL)
    st.markdown("An **AI sustainability monitor** for the plant — a live picture of where energy and carbon go. Four parts:")
    c1, c2, c3, c4 = st.columns(4)
    for col, (icon, title, body) in zip(
        (c1, c2, c3, c4),
        [("📡", "Meters read the process",
          "Machine load, motor temperature, compressed-air pressure and flow, idle share, units produced, "
          "material consumed and hall temperature. Logged every hour, on every line."),
         ("🌡️", "The camera reads the heat",
          "Equipment surfaces, where an air leak shows as a cold plume and a failing bearing as a bright "
          "blob — patterns that live in the image, not in any single meter reading."),
         ("🧠", "AI predicts and finds the waste",
          "Predict the energy and CO2 an hour should have produced, flag the unexplained excess, grade the "
          "thermal frame, and find the operating point with the lowest energy per unit."),
         ("🔔", "The engineer gets a priority",
          "Not a black box. A clear call: check this fitting on this line — this excess in kWh, this "
          "location on the frame — with the evidence shown, so a person decides.")]):
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
        f"color:{TEXT};line-height:1.65'>The engineer stays in charge and stays accountable. The system "
        f"handles the part one person cannot do alone: it watches every machine, every hour, and turns "
        f"what it finds into kilowatt-hours and tonnes of CO2. The goal is "
        f"<b>Manufacturing Engineer + AI</b> — a greener plant that still hits its production targets.</div>",
        unsafe_allow_html=True)
    st.divider()

    # ---------------------------------------------- SECTION 3: MIND MAP
    _op_header("03", "The Engineering Workflow", CIVIL)
    st.markdown(
        f"<div style='color:{MUTED};font-size:15px;line-height:1.6'>These are the {len(PHASES)} phases of "
        f"<b>one sustainable-manufacturing project</b>, in the order a real plant runs them — from the "
        f"first meter reading to a recommendation and the carbon it removes. "
        f"Every <b style='color:{CIVIL}'>amber node</b> is a manufacturing activity. Every "
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
        f"<div style='color:{MUTED};font-size:15px;line-height:1.6'><b>Every AI concept here is a "
        f"manufacturing activity you already understand</b> — the same thing, named differently by a "
        f"different profession. Read down the amber column and you have described a plant energy project. "
        f"Read down the cyan column and you have described a deep learning pipeline. They are the same "
        f"column.</div>",
        unsafe_allow_html=True)
    st.write("")
    st.plotly_chart(mapping_figure(style), use_container_width=True, key="mapping")

    st.markdown(
        f"<div style='border-left:3px solid {AISIDE};padding:8px 0 8px 16px;font-size:16px;"
        f"color:{TEXT};line-height:1.65'>Each AI concept shows up because the manufacturing work ran into "
        f"something one engineer could not do by hand. Only then does it get a technical name.</div>",
        unsafe_allow_html=True)
    st.write("")

    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("▶  Start: walk onto the shop floor", use_container_width=True,
                     type="primary"):
            goto("in-production")
    with c2:
        st.caption(f"{len(PHASES)} phases · {len(STEPS)} steps · one sustainable-manufacturing project. "
                   "Every step opens with the manufacturing activity, then the AI it becomes.")
