"""
bridge.py - the Traffic-Engineering -> AI teaching scaffold.
===========================================================
No new concept, no new model. Every technical illustration lives in app.py /
story.py. This module wraps each stage in the same five-part page a student
sees everywhere:

    Traffic Engineering   the on-street context        (open_page)
    The Challenge         why the manual way runs out  (open_page)
    AI Connection         + the bridge figure          (open_page)
    Technical Idea        <- the existing renderer
    Key Takeaway          one sentence                 (close_page)
    In the Notebook       where it lives               (close_page)

Text is short on purpose. The visuals carry the page.

COLOR IS A TEACHING DEVICE. Amber = the street. Cyan = the AI. Violet = the
technical process.
"""
import streamlit as st
import plotly.graph_objects as go

# ---------------------------------------------------------------- palette
BG, PANEL = "#0e1117", "#161b22"
CIVIL = "#ffb74d"      # amber  - the junction / traffic engineering
AISIDE = "#4fc3f7"     # cyan   - the AI
TECH = "#ba68c8"       # violet - the technical process
GREEN, RED = "#66bb6a", "#ef5350"
MUTED, TEXT = "#8b949e", "#e6edf3"

# ---- UTC control-room display language: signal-head chips, lane-marking
# rules, monospace phase readouts. Same palette as the sibling apps, own look.
STEEL = "#141b24"
INK = "#0b0e13"
EDGE = "#2b3440"
MONOF = "ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', monospace"

_CSS = """
<style>
.stApp {
  background-image:
    repeating-linear-gradient(90deg, rgba(255,255,255,.03) 0 26px, transparent 26px 52px);
  background-size: 52px 100%%;
  background-position: 0 0;
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
.op-rule { flex:1; height:2px;
  background:repeating-linear-gradient(90deg,#2b3440 0 14px,transparent 14px 24px); }
.spec { position:relative; background:#141b24; border:1px solid #2b3440;
  border-left:4px solid #ffb74d;
  padding:14px 18px; color:#e6edf3; font-size:16px; line-height:1.65; margin:2px 0; }
.spec.ai { border-left-color:#4fc3f7; }
.spec.tech { border-left-color:#ba68c8; }
.spec.warn { border-left-color:#ef5350; }
.spec.ok { border-left-color:#66bb6a; }
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
  color:#3f4650; border-radius:9px; }
.ph.done { color:#66bb6a; border-color:#2f5233; }
.ph.cur { background:#ffb74d; color:#0b0e13; border-color:#ffb74d; font-weight:700; }
.brief { position:relative; border:1px solid #2b3440; background:#0b0e13; padding:20px 24px;
  border-top:3px solid #66bb6a; }
.brief-bar { font-family:%(MONO)s; font-size:12px; letter-spacing:.16em; color:#66bb6a; margin-bottom:8px; }
.card-ico { display:inline-flex; align-items:center; justify-content:center; width:40px; height:40px;
  border:1px solid #2b3440; border-radius:50%%; font-size:22px; margin-bottom:8px; background:#0b0e13; }
.muted { color:#8b949e; font-size:13px; }
.substep { font-family:%(MONO)s; color:#8b949e; font-size:13px; }
</style>
""" % {"MONO": MONOF}


def inject_css():
    """Load the control-room display language once. Call after set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def _op_header(op, label, color):
    st.markdown(
        f"<div class='op-row'>"
        f"<span class='op-num' style='color:{color};border-color:{color}'>PH·{op}</span>"
        f"<span class='op-label' style='color:{color}'>{label}</span>"
        f"<span class='op-rule'></span></div>", unsafe_allow_html=True)


# ============================================================================
# THE ENGINEERING WORKFLOW
# ============================================================================
PHASES = [
    ("The Junction In Peak",     "Demand rises every afternoon; the signal plan does not."),
    ("One Signal Cycle",         "One cycle of operation becomes a record of what the junction did."),
    ("Instrumenting The Junction", "Detectors are fitted and the approach becomes a data stream."),
    ("Preparing The Data",       "Bad readings out, every channel scaled, the cycles split."),
    ("Delay From The Detectors", "A model predicts queue and delay from the detector log alone."),
    ("The CCTV Wall",            "The camera arrives, and no brightness rule works well enough."),
    ("How A Machine Learns",     "A trained network takes over from the operator's trained eye."),
    ("Reading The Camera",       "A CNN grades a frame that no fixed rule could grade."),
    ("Locating The Queue",       "The CNN finds the queue, and shows which arm it is on."),
    ("The Traffic Audit",        "Every prediction is checked on cycles the model never saw."),
    ("Control & Optimisation",   "Spot the incident, tune the cycle, and let the plan adapt."),
    ("The Business Case",        "Vehicle-hours, fuel, and emissions the network actually keeps."),
]


# ============================================================================
# THE STEPS  (one per page)
# ============================================================================
STEPS = [

# -------------------------------------------------- PHASE 1
dict(
    id='in-peak', phase=0,
    civil='A Junction Under Load', ai='Why Signal Control Needs AI',
    civil_icon='🚦', ai_icon='🤖',
    tech="A fixed plan against demand that moves all day",
    civil_bullets=['Demand moves hourly', 'The plan does not', 'Queues build'],
    ai_bullets=['Read every cycle', 'Predict the delay', 'Retime while it matters'],
    site="""A signalised junction runs a fixed-time plan set from a survey taken years ago. Demand on the main
street peaks in the morning; the cross street peaks in the evening.""",
    challenge="""A plan tuned for the average is wrong at both peaks. Retiming means another manual count, another
study and months of waiting, so most junctions keep running a plan nobody has checked recently.""",
    ai_link="""The junction does not need its engineers replaced. It needs the gap between the count and the retime
closed - every cycle measured, and the delay predicted while the peak is still running.""",
    notebook="""Section 1. Junction delay across the day under one fixed plan.""",
    contributes="""The requirement. If the plan is still retimed from an annual survey, this failed.""",
    takeaway="""Demand changes hourly; a fixed plan cannot. That gap is the whole problem.""",
),

# -------------------------------------------------- PHASE 2
dict(
    id='reading', phase=1,
    civil='One Signal Cycle', ai='Data Collection',
    civil_icon='⏱️', ai_icon='🗄️',
    tech='One cycle → one row of detector readings + delay',
    civil_bullets=['Eight channels', 'Logged every cycle', 'Outcome recorded'],
    ai_bullets=['One row per cycle', 'Eight features', 'Delay as the target'],
    site="""Each cycle the controller records what it saw: flow on both streets, loop occupancy, headway,
pedestrian calls, the time of day, and the cycle and green times it ran.""",
    challenge="""Alone these are eight numbers on a controller screen. No single one says whether that cycle worked,
and comparing thousands of cycles by eye is not work a person can keep up with.""",
    ai_link="""Put them in one row and the cycle becomes a record: eight inputs, and the delay that resulted.
Thousands of those rows are the dataset every model here learns from.""",
    notebook="""Section 2. Build one cycle record from HCM delay, then the whole log.""",
    contributes="""The unit of learning. Everything downstream is rows like this one.""",
    takeaway="""One cycle becomes one row: eight readings in, delay out.""",
),

# -------------------------------------------------- PHASE 3
dict(
    id='load', phase=2,
    civil='The Controller Log Arrives', ai='Loading The Dataset',
    civil_icon='📥', ai_icon='🐼',
    tech='CSV → DataFrame, 1,600 signal cycles',
    civil_bullets=['UTC export', 'One row per cycle', 'A month of peaks'],
    ai_bullets=['read_csv', 'shape and dtypes', 'First look'],
    site="""The urban traffic control system exports a month of cycles as a CSV: one row per cycle, every detector
channel, plus the delay that cycle produced.""",
    challenge="""An export is not a dataset. Loops drop out when a cabinet resets, a failed detector writes a constant,
and the same cycle can appear twice after a comms retry.""",
    ai_link="""Loading the file into a DataFrame is the first step. It gives shape, column types and a first look -
what every later assumption rests on.""",
    notebook="""Section 3. `pd.read_csv`, `.shape`, `.head()`.""",
    contributes="""The dataset every later step reads from.""",
    takeaway="""The export is raw material. Loading it is where the data work starts.""",
),
dict(
    id='inspect', phase=2,
    civil='Detector Health Check', ai='Data Inspection',
    civil_icon='🔍', ai_icon='📊',
    tech='Count gaps, stuck loops and impossible values',
    civil_bullets=['Did it report?', 'Is it stuck?', 'Is it possible?'],
    ai_bullets=['isna().sum()', 'describe()', 'duplicated()'],
    site="""Before trusting a month of counts, a traffic engineer checks the detectors. Did every loop report? Is a
channel stuck at a constant? Is anything physically impossible?""",
    challenge="""A failed loop reads 0 veh/h - a valid number that happens to be a lie. A saturated counter writes 9999.
Averaged into a peak profile, both quietly corrupt the retiming that follows.""",
    ai_link="""Inspection is that detector check, in code: missing values per channel, minimum and maximum, and which
rows repeat. It finds what a daily average hides.""",
    notebook="""Section 4. `.isna().sum()`, `.describe()`, `.duplicated()`.""",
    contributes="""The fault list the cleaning step works from.""",
    takeaway="""Check the loops before trusting the counts - 0 and 9999 are faults, not data.""",
),

# -------------------------------------------------- PHASE 4
dict(
    id='clean', phase=3,
    civil='Dropouts And Stuck Loops', ai='Data Cleaning',
    civil_icon='🧹', ai_icon='🧼',
    tech='Drop duplicates, null the impossible, fill with the median',
    civil_bullets=['Repair the channel', 'Keep the cycle', 'Never average a fault'],
    ai_bullets=['drop_duplicates', 'Mask impossibles', 'fillna(median)'],
    site="""A faulty detector is repaired or discounted before its counts reach a report. Nobody averages a stuck
loop into a peak-hour flow and then defends the retiming.""",
    challenge="""Deleting every affected row throws away good readings from the other channels in that cycle. Keeping
them poisons the average. Neither extreme survives a design review.""",
    ai_link="""Cleaning does both: drop exact duplicates, mark impossible values as missing rather than deleting the
row, then fill the gaps with the channel's median.""",
    notebook="""Section 5. `drop_duplicates`, mask the impossible, `fillna(median)`.""",
    contributes="""A dataset where every remaining number is physically possible.""",
    takeaway="""Repair the channel, not the cycle: mark the impossible, fill with the median.""",
),
dict(
    id='normalize', phase=3,
    civil='Common Units', ai='Normalization',
    civil_icon='📐', ai_icon='⚖️',
    tech='Min-max every channel to 0-1',
    civil_bullets=['veh/h vs % vs s', 'Different magnitudes', 'One channel wins'],
    ai_bullets=['Rescale to 0-1', 'Units disappear', 'Data decides weight'],
    site="""The channels do not share a scale. Main-street flow runs to 1,900 veh/h, occupancy is a percentage,
headway is a couple of seconds.""",
    challenge="""A model that adds weighted inputs has the same problem. The largest-numbered channel dominates the sum
because its units are bigger, not because it matters more.""",
    ai_link="""Normalization rescales every channel to 0-1 using its own range. Units disappear, and importance is
decided by the data rather than by the choice of unit.""",
    notebook="""Section 6. `MinMaxScaler().fit_transform`.""",
    contributes="""Comparable channels, so learned weights mean something.""",
    takeaway="""Rescale every channel to 0-1 so units stop deciding importance.""",
),
dict(
    id='split', phase=3,
    civil='Known Cycles vs Sealed Cycles', ai='Train / Test Split',
    civil_icon='🗂️', ai_icon='✂️',
    tech='70 / 15 / 15, stratified',
    civil_bullets=['Tune on one set', 'Prove on another', 'Never the same one'],
    ai_bullets=['Train 70%', 'Validate 15%', 'Test 15%, sealed'],
    site="""A signal plan is not validated on the same count that produced it. You prove performance on traffic the
plan has never been tuned against.""",
    challenge="""A model checked on the cycles it learned from will look excellent and mean nothing. It can memorise the
log completely and still fail next Monday.""",
    ai_link="""The split seals part of the data away: 70% to train, 15% to tune, and 15% untouched until the audit.
Only that sealed part gives an honest number.""",
    notebook="""Section 7. `train_test_split`, stratified, applied twice.""",
    contributes="""The sealed set the final audit runs on.""",
    takeaway="""Seal cycles away. A score on data the model has seen is not a score.""",
),

# -------------------------------------------------- PHASE 5
dict(
    id='ml-baseline', phase=4,
    civil='Delay From The Detectors', ai='Machine Learning Baseline',
    civil_icon='📉', ai_icon='🌲',
    tech='Random Forest: 8 readings → delay, queue, LOS flag',
    civil_bullets=['What delay is this?', 'Will it fail LOS?', 'From the log alone'],
    ai_bullets=['Threshold questions', 'Many trees averaged', 'Regression + class'],
    site="""The first question is simple: given this cycle's detector readings, what delay per vehicle did it
produce, how long was the queue, and did the junction fall below its level-of-service target?""",
    challenge="""A Webster spreadsheet gets the order of magnitude right and the details wrong. Flow, split, occupancy
and pedestrian calls interact, and one hand-written formula does not track them together.""",
    ai_link="""A Random Forest learns that relationship from the log. It asks threshold questions on the named channels
and averages many such trees into a delay, a queue and a level-of-service flag.""",
    notebook="""Section 8. `RandomForestRegressor` for delay and queue, `RandomForestClassifier` for the LOS flag.""",
    contributes="""The numeric half of the system, and the baseline the CNN is compared against.""",
    takeaway="""Machine Learning predicts delay well - from named columns only.""",
),
dict(
    id='drivers', phase=4,
    civil='What Drives Congestion', ai='Feature Importance',
    civil_icon='📈', ai_icon='🎚️',
    tech='Which channel moves the delay prediction most',
    civil_bullets=['Which lever?', 'Split or cycle?', 'Rank the causes'],
    ai_bullets=['feature_importances_', 'A priority list', 'Check against theory'],
    site="""Knowing a cycle failed is not actionable. The engineer needs to know which lever to pull: the cycle
length, the green split, the pedestrian stage, or the demand itself.""",
    challenge="""The channels move together. Flow rises, occupancy rises, headway falls. A correlation table shows what
moved with what, not what mattered to the outcome.""",
    ai_link="""Feature importance ranks how much each channel changes the prediction. It turns a black box into an
engineering priority list that can be checked against signal theory.""",
    notebook="""Section 8. `.feature_importances_`, sorted and plotted.""",
    contributes="""The ranking the decision engine issues recommendations from.""",
    takeaway="""A ranked driver list turns a prediction into a decision about what to change.""",
),

# -------------------------------------------------- PHASE 6
dict(
    id='cctv-problem', phase=5,
    civil='The Junction Camera', ai='The Raw Image',
    civil_icon='📷', ai_icon='🖼️',
    tech='A 64x64 grid of pixels, no named columns',
    civil_bullets=['You see the queue', 'The loop cannot', 'Cameras already exist'],
    ai_bullets=['4,096 numbers', 'No column names', 'Nothing to weight'],
    site="""A camera already looks down every approach. A frame is a grid of brightness values: a standing queue, a
clear road, a wet night with headlight glare.""",
    challenge="""The camera does not output "queue of 14". It outputs 4,096 numbers with no names. There is no column
called queue, and no row an engineer can look up.""",
    ai_link="""This is where Machine Learning runs out - it needs named features and there are none. Before reaching
for a new method, it is worth building those features by hand and watching what happens.""",
    notebook="""Section 9. Build a CCTV frame as an array and display it.""",
    contributes="""The data type that forces the second half of the course.""",
    takeaway="""A camera frame is 4,096 unnamed numbers. Machine Learning has nothing to weight.""",
),
dict(
    id='handmade', phase=5,
    civil='Mean Brightness By Hand', ai='Hand-Made Features',
    civil_icon='✋', ai_icon='🔢',
    tech='One number from 4,096 pixels - and what it loses',
    civil_bullets=['Reduce to a mean', 'Set a threshold', 'Exactly as before'],
    ai_bullets=['One feature', 'One threshold', 'It misses'],
    site="""The obvious workaround is the one every engineer tries first: reduce the frame to average brightness,
then threshold it the way a detector threshold already works.""",
    challenge="""Averaging destroys the evidence. A night frame is dark and clear; a jam is mid-grey; wet glare is
bright and clear. No threshold ordering separates congested from clear.""",
    ai_link="""The feature was hand-made and it was the wrong feature. Ten more - variance, edge count, maximum -
would still be guesses. Deep Learning learns the features from the frames instead.""",
    notebook="""Section 9. Compute mean brightness per frame and try to separate them.""",
    contributes="""The failed baseline that justifies the CNN.""",
    takeaway="""One hand-made number cannot hold a pattern - dark and bright are both clear.""",
),

# -------------------------------------------------- PHASE 7
dict(
    id='operator-brain', phase=6,
    civil="How An Operator Decides", ai='The Neuron, Informally',
    civil_icon='👷', ai_icon='💡',
    tech='Weigh the signals, add them, decide',
    civil_bullets=['Several signals at once', 'Some matter more', 'One call'],
    ai_bullets=['Weights', 'A sum', 'A threshold'],
    site="""A control-room operator watching a junction weighs several things at once - queue length on the screen,
loop occupancy, time of day, how long the last cycle ran - and calls it congested or not.""",
    challenge="""That judgement is fast and good, but it lives in one head, covers one junction at a time, and cannot be
applied to a month of logs overnight.""",
    ai_link="""Write the judgement down and it is arithmetic: multiply each signal by how much it matters, add the
results, act if the total clears a threshold. That is a neuron.""",
    notebook="""Section 11. The weighted-sum decision, before any terminology.""",
    contributes="""The intuition every later network is built on.""",
    takeaway="""A neuron is an operator's judgement written as arithmetic: weigh, add, decide.""",
),
dict(
    id='neuron', phase=6,
    civil='Weighing The Signals', ai='The Neuron',
    civil_icon='⚖️', ai_icon='🔵',
    tech='z = w·x + b',
    civil_bullets=['Occupancy matters a lot', 'Hour matters less', 'Experience = weights'],
    ai_bullets=['Weights are learned', 'Bias sets the baseline', 'Traceable to data'],
    site="""Give each signal a weight. Loop occupancy matters a great deal for congestion. The hour of the day
matters less on its own. An operator's experience is exactly that set of weights.""",
    challenge="""Those weights are guesses, and every operator guesses differently. Nobody can defend "occupancy counts
3.4 times more than headway" from experience alone.""",
    ai_link="""A neuron computes a weighted sum plus a bias. Nobody chooses the weights - they are learned from the
log, so the model's opinion is traceable to data rather than to seniority.""",
    notebook="""Section 11. `z = w·x + b`, computed by hand.""",
    contributes="""The single unit every network here is built from.""",
    takeaway="""A neuron is a weighted sum plus a bias, and the weights come from the data.""",
),
dict(
    id='activation', phase=6,
    civil='The Congestion Threshold', ai='Activation Function',
    civil_icon='🚨', ai_icon='📉',
    tech='sigmoid and ReLU',
    civil_bullets=['Acceptable or not', 'A hard limit is brittle', 'Congestion is graded'],
    ai_bullets=['Sigmoid → 0..1', 'ReLU passes positives', 'Smooth = trainable'],
    site="""An alarm does not report a weighted sum. It reports a state: acceptable, or intervene. Somewhere the
continuous signal has to become a decision.""",
    challenge="""A hard on/off limit is brittle. A cycle a second under the limit is treated as fine, one a second over
triggers an intervention. Real congestion does not step like that.""",
    ai_link="""An activation function does the same job smoothly. Sigmoid turns any sum into a number between 0 and 1
that reads as a probability. That smoothness is also what makes the network trainable.""",
    notebook="""Section 12. Plot sigmoid and ReLU, and pass `z` through both.""",
    contributes="""The step that turns a raw sum into a usable probability.""",
    takeaway="""Activation turns a weighted sum into a graded decision instead of a brittle limit.""",
),
dict(
    id='learning-loop', phase=6,
    civil='Learning From A Bad Peak', ai='The Learning Loop',
    civil_icon='🔁', ai_icon='🎯',
    tech='predict → error → adjust → repeat',
    civil_bullets=['The queue showed the miss', 'Adjust the judgement', 'Better next peak'],
    ai_bullets=['Compare to truth', 'Measure the error', 'Nudge every weight'],
    site="""A peak is misjudged and the cross street backs up. The next day the operator adjusts: weight the
occupancy reading more, the hour less.""",
    challenge="""Done by hand, that correction happens once per incident and depends entirely on who is on shift. Eight
channels and thousands of cycles cannot be tuned that way.""",
    ai_link="""The learning loop is that correction, automated: predict, compare with the recorded truth, measure the
error, adjust every weight a little, repeat.""",
    notebook="""Section 13. The loop, shown before the optimiser has a name.""",
    contributes="""The mechanism that turns a random model into a useful one.""",
    takeaway="""Predict, measure the error, adjust, repeat - that loop is all training is.""",
),
dict(
    id='gradient-descent', phase=6,
    civil='Tuning The Plan', ai='Loss & Gradient Descent',
    civil_icon='🎛️', ai_icon='⛰️',
    tech='loss surface, gradient, learning rate',
    civil_bullets=['Change a split', 'Measure the delay', 'Step again'],
    ai_bullets=['Loss = how wrong', 'Gradient = downhill', 'Rate = step size'],
    site="""Retiming a junction on street is a search. Change the split, measure the delay, keep the change if it
helped, step again in the direction that worked.""",
    challenge="""Step too far and you overshoot and oscillate between the two streets. Step too small and the retiming
takes a season. The step size is the whole difficulty.""",
    ai_link="""Loss measures how wrong the model is. Gradient descent takes the downhill direction and steps along it;
the learning rate is the step size. Same overshoot, same reason.""",
    notebook="""Section 13. A loss surface, and the descent path at three learning rates.""",
    contributes="""How the weights actually change during training.""",
    takeaway="""Training is retiming by search: step downhill on the error, and mind the step size.""",
),
dict(
    id='network', phase=6,
    civil='The Control Room Team', ai='The Neural Network',
    civil_icon='👥', ai_icon='🕸️',
    tech='input → hidden layers → output',
    civil_bullets=['Queue watcher', 'Incident watcher', 'Pedestrian watcher'],
    ai_bullets=['Each neuron, a view', 'Layers combine them', 'One output'],
    site="""No single operator covers everything. One watches queues, one watches incidents, one watches pedestrian
demand. A supervisor combines their calls into one decision.""",
    challenge="""Coordinating them is slow and their reports are inconsistent. Some overlap, some contradict, and nobody
weighs them the same way twice.""",
    ai_link="""A hidden layer is that team. Each neuron learns a different combination of the readings, and the output
neuron weighs their conclusions into one answer.""",
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
    site="""A new operator learns from this junction's own records - a month of cycles where the outcome is known -
not from a manual written for a different city.""",
    challenge="""Learn the records too well and you have memorised them: perfect on last month, useless on next month.
Stop too early and nothing has been learned.""",
    ai_link="""Training runs the learning loop over the training rows for many epochs, and watches the loss on
validation rows it never learns from. When that stops falling, learning has become memorising.""",
    notebook="""Section 14. Loss curves for training and validation.""",
    contributes="""The trained numeric model used in the audit.""",
    takeaway="""Watch the validation curve - where it turns, learning has become memorising.""",
),

# -------------------------------------------------- PHASE 8
dict(
    id='cnn-journey', phase=7,
    civil='Reading The Camera', ai='Convolution & Feature Maps',
    civil_icon='🧩', ai_icon='🔬',
    tech='filters → feature maps → classification',
    civil_bullets=['A line of vehicles', 'Gaps between them', 'Shape, not brightness'],
    ai_bullets=['Filters slide', 'Edges → queues', 'Filters are learned'],
    site="""A frame is not read pixel by pixel. An engineer sees a shape: a line of vehicles nose to tail, or a road
with gaps in it.""",
    challenge="""Shape cannot be captured by any single pixel value, and it moves. The same queue appears at a different
position, length and angle in every frame.""",
    ai_link="""A convolution slides a small filter over the frame and reports where its pattern occurs. Early filters
find edges; later ones combine edges into vehicles and queues. The network learns the filters.""",
    notebook="""Section 15. Convolve a frame by hand, then train a small CNN.""",
    contributes="""The visual half of the system: a grade for every camera frame.""",
    takeaway="""Convolution finds a shape anywhere in the frame, without anyone naming it.""",
),

# -------------------------------------------------- PHASE 9
dict(
    id='queue-locate', phase=8,
    civil='Which Arm Is Blocked?', ai='Grad-CAM',
    civil_icon='📍', ai_icon='🗺️',
    tech='class-weighted feature maps → heat map',
    civil_bullets=['Which approach?', 'How far back?', 'Give green to it'],
    ai_bullets=['Weight the maps', 'Project onto the frame', 'Show the evidence'],
    site="""A congestion grade on its own does not change a signal plan. The controller needs to know which approach
is blocked, and how far the queue extends.""",
    challenge="""A classifier outputs a probability. It gives no location, and an operator asked to reallocate green on
a bare number will - rightly - not do it.""",
    ai_link="""Grad-CAM weights the last feature maps by how much each contributed to the answer and projects them
back onto the frame. The bright region is the queue, and the evidence for the call.""",
    notebook="""Section 16. Grad-CAM over the trained CNN.""",
    contributes="""The location that makes the alert actionable.""",
    takeaway="""Grad-CAM shows where the network looked - that is both the arm and the evidence.""",
),
dict(
    id='emergency', phase=8,
    civil='Emergency Preemption', ai='Detection With A Cost',
    civil_icon='🚑', ai_icon='⏱️',
    tech='detect → preempt → recover',
    civil_bullets=['Seconds matter', 'Others wait', 'The plan recovers'],
    ai_bullets=['Detect on the frame', 'Grant the phase', 'Price the disruption'],
    site="""An ambulance approaches on the main street. Preemption gives it green immediately and holds the other
arms, then the plan recovers over the following cycles.""",
    challenge="""Preemption is not free. Every second granted is a second the cross street waits, and a false detection
disrupts the junction for nothing.""",
    ai_link="""The camera model detects the vehicle and the controller grants the phase. The interesting engineering is
not the detection - it is showing what the preemption costs everyone else.""",
    notebook="""Section 16. Detection, preemption, and the recovery cycles.""",
    contributes="""The clearest case where a model output changes the signal directly.""",
    takeaway="""Preemption buys seconds for one vehicle and charges them to everyone else.""",
),

# -------------------------------------------------- PHASE 10
dict(
    id='audit', phase=9,
    civil='The Traffic Audit', ai='Confusion Matrix',
    civil_icon='🧮', ai_icon='✅',
    tech='TP / FP / FN / TN and what each costs',
    civil_bullets=['Predicted vs measured', 'On sealed cycles', 'Every claim checked'],
    ai_bullets=['Four outcomes', 'False alarm ≠ miss', 'Recall matters'],
    site="""Every claim is audited: predicted congestion against measured delay, on cycles the model was never
allowed to see.""",
    challenge="""A single accuracy figure hides what matters. Predicting "not congested" for every cycle scores well on
a junction that flows most of the day - and finds nothing.""",
    ai_link="""The confusion matrix separates the four outcomes. A false alarm wastes green on an empty arm. A missed
peak leaves a queue growing. They are not equal.""",
    notebook="""Section 17. Confusion matrix, accuracy and recall on the sealed set.""",
    contributes="""The honest performance number the project is judged on.""",
    takeaway="""Accuracy hides the costly error; the confusion matrix shows the missed peak.""",
),
dict(
    id='proof', phase=9,
    civil='The Verdict', ai='ML vs DL, Proven',
    civil_icon='⚔️', ai_icon='🏁',
    tech='the same task, both methods, measured',
    civil_bullets=['Two data types', 'Two methods', 'One junction'],
    ai_bullets=['Forest wins on numbers', 'CNN wins on pixels', 'Neither replaces the other'],
    site="""Two models, two data types, one junction. Time to state plainly what each can and cannot do.""",
    challenge="""It is tempting to declare Deep Learning the better method. It is not better - it is different, and on
the detector log the forest is faster, cheaper and far easier to defend.""",
    ai_link="""Run both on both. The forest wins on the eight named channels and cannot take a camera frame at all.
The CNN grades the frame. Each method belongs to its data type.""",
    notebook="""Section 18. The comparison table, filled in from measured results.""",
    contributes="""The course's central claim, demonstrated rather than asserted.""",
    takeaway="""ML weights the columns you name; DL finds the patterns you cannot name.""",
),

# -------------------------------------------------- PHASE 11
dict(
    id='incident', phase=10,
    civil='Normal For This Hour', ai='Anomaly Detection',
    civil_icon='📊', ai_icon='🚩',
    tech='expected flow vs actual → residual → alarm',
    civil_bullets=['Peak is busy', 'Night is empty', 'Neither is an incident'],
    ai_bullets=['Learn normal', 'Score the residual', 'Alarm on the excess'],
    site="""Flow is supposed to rise in the peak and fall at night. A busy Tuesday afternoon is not an incident, and
an empty Sunday morning is not a detector fault.""",
    challenge="""Because normal moves with the hour, a fixed flow threshold is useless. Set it high and a blockage hides
inside the peak; set it low and it fires every evening.""",
    ai_link="""Anomaly detection learns normal for this hour and this day type, then scores the residual - the part of
the reading the conditions do not explain. A blockage is exactly that.""",
    notebook="""Section 19. Regress flow on hour and day type, then alarm on the residual.""",
    contributes="""The detector that catches incidents no fixed threshold would see.""",
    takeaway="""Alarm on the unexplained residual, not on the raw flow.""",
),
dict(
    id='optimize', phase=10,
    civil='The Best Cycle Length', ai='Optimisation',
    civil_icon='🎯', ai_icon='🧭',
    tech='sweep the cycle → predict delay → read off the minimum',
    civil_bullets=['How long a cycle?', 'How much green?', 'For this demand'],
    ai_bullets=['Sweep the range', 'Predict each point', 'Read off the minimum'],
    site="""The engineer chooses two things: how long the cycle runs, and how the green is split between the
streets.""",
    challenge="""Delay is not lowest at the shortest cycle. Lost time at every phase change is spread over fewer
seconds of green, so a short cycle can cost more delay, not less. Intuition points the wrong way.""",
    ai_link="""With a model that predicts delay, the range can simply be swept and the delay read off. The minimum of
that curve is the best cycle for this demand, and it moves as demand moves.""",
    notebook="""Section 20. Sweep the cycle, predict delay, find the minimum.""",
    contributes="""The recommendation the dashboard turns into vehicle-hours.""",
    takeaway="""The best cycle is a minimum on a curve, not the shortest setting available.""",
),
dict(
    id='adaptive', phase=10,
    civil='Fixed-Time vs Adaptive', ai='Control From Prediction',
    civil_icon='🔀', ai_icon='♻️',
    tech='one plan all day, or a plan per hour',
    civil_bullets=['AM peaks the main street', 'PM peaks the cross street', 'One plan serves neither'],
    ai_bullets=['Re-split each hour', 'Predict, then act', 'Measure the difference'],
    site="""The main street peaks in the morning, the cross street in the evening. A single fixed plan has to serve
both, so it is tuned for neither.""",
    challenge="""The honest comparison is against the *best possible* fixed plan, found by searching every cycle and
split - not against the poor plan the junction happens to be running.""",
    ai_link="""Adaptive control reallocates green each hour from the predicted demand. Scored as vehicle-weighted
junction delay across a full day, the difference is measurable rather than claimed.""",
    notebook="""Section 21. Best fixed plan by exhaustive search, then hour-by-hour adaptive.""",
    contributes="""The number the business case is built from.""",
    takeaway="""Adaptive control wins by moving green between streets that peak at different times.""",
),
dict(
    id='fusion-engine', phase=10,
    civil='The Decision Engine', ai='AI Fusion',
    civil_icon='🖥️', ai_icon='🔗',
    tech='ML delay + CNN grade + anomaly → one instruction',
    civil_bullets=['Three opinions', 'One operator', 'One action list'],
    ai_bullets=['Combine the outputs', 'Rank by delay', 'Attach the evidence'],
    site="""By now the junction produces three opinions every cycle: a predicted delay, an anomaly score, and a
camera grade with a location.""",
    challenge="""Three screens is three chances to miss something. An operator covering a district needs one ranked
list, not three dashboards to correlate by hand.""",
    ai_link="""Fusion combines them into one prioritised instruction with its evidence attached: the delay in seconds,
the arm on the frame, and the change to make.""",
    notebook="""Section 22. A rules layer over both model outputs.""",
    contributes="""The product - one screen an operator can act on.""",
    takeaway="""Numbers say how bad it is; the camera says which arm. Fusion issues one instruction.""",
),
dict(
    id='pipeline', phase=10,
    civil='The Whole System', ai='The Pipeline',
    civil_icon='🧱', ai_icon='🛤️',
    tech='detectors → data → ML + DL → fusion → dashboard',
    civil_bullets=['Loops and cameras', 'Models', 'A screen that acts'],
    ai_bullets=['Every stage feeds one', 'Data quality first', 'One instruction'],
    site="""Step back and the whole system is visible: loops and cameras on the street, a data path, two models, and
a screen the operator reads.""",
    challenge="""Every stage depends on the ones before it. A stuck loop that survives cleaning becomes a false
instruction four stages later, and nothing downstream can recover from it.""",
    ai_link="""The pipeline is the engineering drawing of the system. It shows what feeds what, where the two data
types split, and where they come back together.""",
    notebook="""Section 22. The end-to-end run, in one place.""",
    contributes="""The map of everything built so far.""",
    takeaway="""The system is a chain: data quality at the start decides the instruction at the end.""",
),

# -------------------------------------------------- PHASE 12
dict(
    id='dashboard', phase=11,
    civil='The Traffic Dashboard', ai='Delay, Fuel & Emissions',
    civil_icon='📉', ai_icon='💷',
    tech='vehicle-hours, fuel and CO2, before and after',
    civil_bullets=['Approve a scheme', 'Against a saving', 'With a payback'],
    ai_bullets=['Vehicle-hours saved', 'Fuel avoided', 'tCO2 avoided'],
    site="""A city does not buy a model. It approves a scheme against a saving in vehicle-hours, fuel and emissions,
with a payback period attached.""",
    challenge="""Traffic savings are easy to overstate. Published adaptive-control results are in the 10-20% range, and
a junction still has to pass the same traffic it did before.""",
    ai_link="""The dashboard turns the model outputs into the city's own units: vehicle-hours saved per year, litres of
fuel, tonnes of CO2 and cost. Every figure is arithmetic on assumptions the reader can change.""",
    notebook="""Section 23. The dashboard, computed from the assumptions above.""",
    contributes="""The business case - the reason the previous steps get funded.""",
    takeaway="""Signal schemes are approved in vehicle-hours and fuel, not in accuracy percentages.""",
),
]

# ---------------------------------------------------------------- short labels
SHORT = {
    "in-peak": "Junction under load",       "reading": "One signal cycle",
    "load": "Controller log arrives",       "inspect": "Detector health check",
    "clean": "Dropouts & stuck loops",      "normalize": "Common units",
    "split": "Known vs sealed",             "ml-baseline": "Delay from detectors",
    "drivers": "What drives congestion",    "cctv-problem": "The raw frame",
    "handmade": "Brightness by hand",       "operator-brain": "Operator decides",
    "neuron": "Weighing signals",           "activation": "Congestion threshold",
    "learning-loop": "Learn from a peak",   "gradient-descent": "Tune the plan",
    "network": "The control room team",     "training": "Learn from the log",
    "cnn-journey": "Read the camera",       "queue-locate": "Which arm is blocked",
    "emergency": "Emergency preemption",    "audit": "The traffic audit",
    "proof": "The verdict",                 "incident": "Normal vs incident",
    "optimize": "Best cycle length",        "adaptive": "Fixed vs adaptive",
    "fusion-engine": "Decision engine",     "pipeline": "The whole system",
    "dashboard": "The dashboard",
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
    """The street-activity -> AI-equivalent -> technical-process bridge."""
    fig = go.Figure()
    _card(fig, 0.2, 3.4, CIVIL, step["civil_icon"], step["civil"],
          step["civil_bullets"], "ON THE STREET")
    _card(fig, 6.6, 9.8, AISIDE, step["ai_icon"], step["ai"],
          step["ai_bullets"], "IN THE AI")

    for yy in (3.06, 2.94):
        fig.add_shape(type="line", x0=3.45, y0=yy, x1=6.35, y1=yy,
                      line=dict(color=EDGE, width=1.5), layer="below")
    fig.add_annotation(x=6.55, y=3.0, ax=6.3, ay=3.0, xref="x", yref="y",
                       axref="x", ayref="y", showarrow=True, arrowhead=2,
                       arrowsize=1.6, arrowwidth=2.5, arrowcolor=AISIDE, text="")
    fig.add_annotation(x=4.9, y=3.55, text="⇒ TRANSFORM ⇒", showarrow=False,
                       font=dict(size=11, color=MUTED, family=MONOF))

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
# NAVIGATION
# ============================================================================
def _nav_strip(step, key):
    i = ORDER.index(step["id"])
    prev_s = BY_ID[ORDER[i - 1]] if i > 0 else None
    next_s = BY_ID[ORDER[i + 1]] if i < len(ORDER) - 1 else None
    c1, c2, c3 = st.columns([1, 1.25, 1])
    with c1:
        if prev_s:
            if st.button(f"◀  {prev_s['civil']}", key=f"prev_{key}", use_container_width=True):
                goto(prev_s["id"])
        else:
            if st.button("◀  The project overview", key=f"prev_{key}", use_container_width=True):
                goto("start")
    with c2:
        st.markdown(
            f"<div class='trav'>▐ STEP {i+1:02d} / {len(ORDER):02d} ▌"
            f"<br><b>{step['civil']}</b></div>", unsafe_allow_html=True)
    with c3:
        if next_s:
            if st.button(f"{next_s['civil']}  ▶", key=f"next_{key}", use_container_width=True):
                goto(next_s["id"])
        else:
            if st.button("Back to the overview  ▶", key=f"next_{key}", use_container_width=True):
                goto("start")


# ============================================================================
# open_page  -  Parts 1, 2 and 3, ABOVE the stage renderer
# ============================================================================
def open_page(stage, style, animate):
    step = BY_ID.get(stage)
    if step is None:
        return
    pname, pdesc = PHASES[step["phase"]]

    _nav_strip(step, "top")
    i = ORDER.index(stage)
    st.markdown(
        f"<div class='dro-bar' style='margin-top:14px'>⟨UTC·JUNCTION⟩ &nbsp; "
        f"STEP {i+1:02d}/{len(ORDER)} &nbsp;·&nbsp; PHASE {step['phase']+1:02d}/{len(PHASES)} "
        f"&nbsp;·&nbsp; <span style='color:{CIVIL}'>{pname.upper()}</span> "
        f"&nbsp;—&nbsp; {pdesc}</div>", unsafe_allow_html=True)
    st.markdown(f"# {step['civil_icon']}  {step['civil']}")
    st.markdown(
        f"<span class='substep'>▸ this traffic step is the AI concept </span>"
        f"<b style='color:{AISIDE}'>{step['ai']}</b>", unsafe_allow_html=True)
    st.divider()

    _op_header("10", "Traffic Engineering", CIVIL)
    st.markdown(f"<div class='spec'>{step['site']}</div>", unsafe_allow_html=True)
    st.write("")

    _op_header("20", "The Challenge", RED)
    st.markdown(f"<div class='spec warn'>{step['challenge']}</div>", unsafe_allow_html=True)
    st.write("")

    _op_header("30", "AI Connection", AISIDE)
    st.markdown(f"<div class='spec ai'>{step['ai_link']}</div>", unsafe_allow_html=True)
    st.write("")
    st.plotly_chart(bridge_figure(step, style, animate), use_container_width=True,
                    key=f"bridge_{stage}")
    st.caption("▶ Press Play — the data packet travels from the street into the AI.")
    st.divider()

    _op_header("40", "Technical Idea", TECH)
    st.caption(f"{step['tech']} — interactive. Change things and watch what happens.")
    st.write("")


# ============================================================================
# close_page  -  Part 5, BELOW the stage renderer
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
        f"<div class='travbar'><span class='travlab'>ROUTE</span>"
        + "".join(segs)
        + f"<span class='travlab' style='margin-left:auto'>PH {step['phase']+1:02d}/{len(PHASES)}"
        f" · {PHASES[step['phase']][0].upper()}</span></div>", unsafe_allow_html=True)
    st.write("")
    _nav_strip(step, "bottom")


# ============================================================================
# CHECK-YOUR-UNDERSTANDING QUIZ
# ============================================================================
QUIZ = {
    'in-peak': dict(
        q="Why does a plan tuned on last year's survey fail at both peaks?",
        options=["Surveys are always wrong",
                 "It is tuned for the average, but the main street peaks in the morning and the cross street in the evening",
                 "Detectors drift over a year",
                 "Drivers change their routes"],
        answer=1,
        why="One fixed split has to serve two different peak shapes, so it is wrong for both."),
    'reading': dict(
        q="Why is one cycle written as a single row rather than eight separate logs?",
        options=["It saves disk space",
                 "Because a row ties the eight inputs to the delay that resulted, which is what a model learns from",
                 "Because controllers can only write rows",
                 "So it fits on one screen"],
        answer=1,
        why="The row pairs cause with effect. Thousands of those pairs are the dataset."),
    'load': dict(
        q="Why is a UTC export not yet a dataset?",
        options=["It is in the wrong format",
                 "It contains dropouts, stuck detectors and duplicate cycles that a spreadsheet view will not reveal",
                 "It is too large for pandas",
                 "It has no header row"],
        answer=1,
        why="Loading it is only the first step; what is in it still has to be checked."),
    'inspect': dict(
        q="A loop reads exactly 0 veh/h for 300 cycles in the afternoon. What is it?",
        options=["A quiet approach",
                 "A failed or disconnected loop writing a valid-looking number",
                 "Normal for a side road",
                 "A rounding artefact"],
        answer=1,
        why="A signalised approach in the afternoon always carries some traffic. 0 is valid and a fault at once."),
    'clean': dict(
        q="Why fill a missing reading with the channel's median instead of its mean?",
        options=["The median is faster",
                 "The mean is only valid for whole numbers",
                 "The median ignores the extreme faulty values still lurking in the column",
                 "The median is always larger"],
        answer=2,
        why="A single 9999 shifts a mean badly. The median barely moves."),
    'normalize': dict(
        q="What goes wrong if the channels are not rescaled?",
        options=["The code crashes",
                 "The largest-numbered channel dominates the weighted sum because of its unit, not its importance",
                 "The data takes more memory",
                 "The plots look untidy"],
        answer=1,
        why="Flow in veh/h and occupancy in percent are not comparable magnitudes until they are rescaled."),
    'split': dict(
        q="Why keep a sealed test set?",
        options=["To make training faster",
                 "Because a model scored on cycles it learned from can memorise the log and still fail next week",
                 "Because sklearn requires it",
                 "To reduce the file size"],
        answer=1,
        why="Only data the model has never seen gives an honest estimate."),
    'ml-baseline': dict(
        q="Why does a Random Forest beat a single Webster spreadsheet here?",
        options=["It uses more decimal places",
                 "It learns how flow, split, occupancy and pedestrian demand interact, from the junction's own log",
                 "It works on images too",
                 "It never makes mistakes"],
        answer=1,
        why="The interactions are what a fixed formula misses."),
    'drivers': dict(
        q="Feature importance ranks occupancy first. What has it told you?",
        options=["Occupancy causes congestion",
                 "The other channels can be deleted",
                 "The prediction moves most with occupancy, so that is the first place to look",
                 "The loop is broken"],
        answer=2,
        why="Importance is about how much the prediction moves, not proof of cause."),
    'cctv-problem': dict(
        q="Why can the Random Forest not take the camera frame as input?",
        options=["The image is too large",
                 "There are no named features — only 4,096 pixel values with no engineering meaning individually",
                 "Forests only accept integers",
                 "The camera resolution is too low"],
        answer=1,
        why="A pixel at row 12 column 40 is not a feature anybody can name or defend."),
    'handmade': dict(
        q="Why does thresholding on mean brightness fail?",
        options=["The camera is not calibrated",
                 "The mean is computed incorrectly",
                 "A dark night frame is clear and a bright glare frame is clear, with congested frames in between — so no threshold ordering works",
                 "Thresholds never work"],
        answer=2,
        why="Congested frames are sandwiched between two clear cases, in both directions."),
    'operator-brain': dict(
        q="An operator weighs queue, occupancy and time of day, then calls it congested. What has been described?",
        options=["A confusion matrix",
                 "A neuron: weighted inputs, summed, compared to a threshold",
                 "A convolution",
                 "A train/test split"],
        answer=1,
        why="The neuron is the operator's rule of thumb written as arithmetic."),
    'neuron': dict(
        q="In z = w·x + b, what does b do?",
        options=["Scales the inputs",
                 "Shifts the baseline, so the neuron can fire without every input being large",
                 "Counts the features",
                 "Selects the activation"],
        answer=1,
        why="The bias sets where the decision sits."),
    'activation': dict(
        q="Why not just use a hard on/off limit instead of a sigmoid?",
        options=["Sigmoid is faster",
                 "A hard limit treats 'just under' and 'just over' as opposites, and gives training no gradient to follow",
                 "Hard limits are not allowed in Python",
                 "Sigmoid uses less memory"],
        answer=1,
        why="The graded output is more honest, and its smoothness is what makes gradient descent possible."),
    'learning-loop': dict(
        q="What is the essential order of the learning loop?",
        options=["Adjust → predict → measure",
                 "Predict → compare with truth → measure error → adjust weights → repeat",
                 "Measure → stop",
                 "Split → normalize → predict"],
        answer=1,
        why="Every training algorithm here is that loop, repeated over the rows."),
    'gradient-descent': dict(
        q="The loss oscillates and never settles. What is the likely cause?",
        options=["Too little data",
                 "The learning rate is too large, so each step overshoots the minimum",
                 "The loss function is wrong",
                 "Too many features"],
        answer=1,
        why="Same as over-adjusting a green split on street: the correction is bigger than the error."),
    'network': dict(
        q="What does adding a hidden layer buy you?",
        options=["Faster training",
                 "Neurons that each learn a different combination of the readings, so interactions a single weighted sum cannot express become representable",
                 "Fewer weights to store",
                 "Automatic data cleaning"],
        answer=1,
        why="One neuron draws one boundary. A layer of them draws the shape the data needs."),
    'training': dict(
        q="Training loss keeps falling but validation loss starts rising. What is happening?",
        options=["The data is corrupt",
                 "The model has started memorising the training cycles instead of learning the pattern",
                 "The learning rate is too small",
                 "Training finished successfully"],
        answer=1,
        why="That turn is where learning becomes memorising. Stop there."),
    'cnn-journey': dict(
        q="Why does a convolution find a queue wherever it appears in the frame?",
        options=["Because images are normalized",
                 "Because the same filter slides across every position, so the pattern is detected anywhere",
                 "Because the camera is fixed",
                 "Because queues are always bright"],
        answer=1,
        why="Sliding is what gives a CNN its position independence."),
    'queue-locate': dict(
        q="What does Grad-CAM add to a CNN's probability?",
        options=["Higher accuracy",
                 "A faster prediction",
                 "A heat map of where the network looked, which is both the blocked arm and the evidence",
                 "An automatic signal change"],
        answer=2,
        why="A bare probability does not tell a controller which arm to give green to."),
    'emergency': dict(
        q="What is the real engineering content of preemption?",
        options=["Detecting the ambulance",
                 "Showing what the granted green costs the other approaches, and how the plan recovers",
                 "Making the cycle shorter",
                 "Turning all signals red"],
        answer=1,
        why="Detection is the easy half. The cost and the recovery are what make it a design decision."),
    'audit': dict(
        q="A model predicts 'not congested' for every cycle and scores 80% accuracy. What is wrong?",
        options=["Nothing — 80% is good",
                 "It never finds congestion, which is the point of the system; accuracy hides that",
                 "The test set is too small",
                 "Accuracy should be recomputed on the training set"],
        answer=1,
        why="Recall on the congested cycles is the number that matters."),
    'proof': dict(
        q="What does the head-to-head comparison prove?",
        options=["Deep Learning is better than Machine Learning",
                 "Machine Learning is obsolete",
                 "Each method belongs to its data type: the forest wins on named channels, the CNN on raw pixels",
                 "Both perform identically"],
        answer=2,
        why="This is the central claim of the course, demonstrated with measured numbers."),
    'incident': dict(
        q="Why score the residual instead of alarming on raw flow?",
        options=["Residuals are smaller numbers",
                 "Because normal flow moves with the hour, so a fixed threshold either hides a blockage in the peak or fires every evening",
                 "Because flow is not measurable",
                 "To avoid using a model"],
        answer=1,
        why="The residual is the part of the reading the conditions do not explain — which is what an incident is."),
    'optimize': dict(
        q="Why is the shortest cycle not the lowest-delay cycle?",
        options=["Short cycles damage controllers",
                 "Lost time at each phase change is spread over fewer seconds of green, so capacity falls and delay rises",
                 "Short cycles only affect pedestrians",
                 "It is the lowest-delay cycle"],
        answer=1,
        why="Delay against cycle length is a curve with a minimum. Finding it is an optimisation."),
    'adaptive': dict(
        q="Why must adaptive control be compared against the *best* fixed plan?",
        options=["To make the comparison look better",
                 "Because beating a badly-tuned plan proves nothing — the honest baseline is the best fixed plan the junction could run",
                 "Because fixed plans are illegal",
                 "Because the best plan is easier to compute"],
        answer=1,
        why="Any adaptive scheme beats a bad plan. Only beating the best fixed plan is evidence."),
    'fusion-engine': dict(
        q="What does fusion add over the three separate outputs?",
        options=["Higher individual accuracy",
                 "One ranked instruction with its evidence attached, instead of three screens to correlate by hand",
                 "Faster inference",
                 "Less data storage"],
        answer=1,
        why="Numbers say how bad; the camera says which arm. The value is in issuing one action."),
    'pipeline': dict(
        q="Why does a stuck loop that survives cleaning matter four stages later?",
        options=["It slows the code down",
                 "It does not — the model corrects it",
                 "Because the pipeline is a chain: a bad reading becomes a bad prediction and then a false instruction",
                 "It only affects the plots"],
        answer=2,
        why="Nothing downstream can recover information that was wrong at the source."),
    'dashboard': dict(
        q="Why report vehicle-hours and fuel rather than model accuracy?",
        options=["Accuracy is confidential",
                 "Because a city approves a scheme against savings in its own units, with a payback",
                 "Because accuracy was too low",
                 "Because fuel is easier to measure"],
        answer=1,
        why="Every figure on it is arithmetic on assumptions the reader can change."),
}


def render_quiz(stage):
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
# THE INTERACTIVE MIND MAP
# ============================================================================
def mind_map(style):
    fig = go.Figure()
    n = len(PHASES)
    VGAP = 1.5
    ys = {i: (n - 1 - i) * VGAP for i in range(n)}

    for i in range(n - 1):
        fig.add_annotation(x=0, y=ys[i + 1] + 0.55, ax=0, ay=ys[i] - 0.62,
                           xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1.1,
                           arrowwidth=2, arrowcolor=CIVIL, text="")

    GAP = 3.4
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
        marker=dict(size=20, color=INK, line=dict(color=AISIDE, width=2), symbol="circle"),
        hovertemplate="%{hovertext}<extra></extra>", hovertext=shover,
        showlegend=False))

    fig.update_xaxes(visible=False, range=[-7.0, X0 + (maxk - 1) * GAP + 2.2])
    fig.update_yaxes(visible=False, range=[-1.0, (n - 1) * VGAP + 0.6])
    return style(fig, h=int((n - 1) * VGAP * 78) + 150)


# ============================================================================
# THE TRAFFIC-ENGINEERING-TO-AI MAPPING
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
                           showarrow=False, xanchor="left", font=dict(size=11.5, color=TEXT))
        fig.add_annotation(x=4.1, y=y, text="»", showarrow=False,
                           font=dict(size=16, color=MUTED, family=MONOF))
        fig.add_shape(type="rect", x0=4.6, x1=8.2, y0=y - 0.36, y1=y + 0.36,
                      line=dict(color=EDGE, width=1), fillcolor=STEEL, layer="below")
        fig.add_shape(type="line", x0=8.2, y0=y - 0.36, x1=8.2, y1=y + 0.36,
                      line=dict(color=AISIDE, width=3), layer="above")
        fig.add_annotation(x=4.78, y=y, text=f"{s['ai_icon']} {s['ai']}",
                           showarrow=False, xanchor="left", font=dict(size=11.5, color=TEXT))
        fig.add_annotation(x=8.4, y=y, text=f"PH{s['phase']+1:02d}", showarrow=False,
                           xanchor="left", font=dict(size=9, color="#3f4650", family=MONOF))

    fig.add_annotation(x=0, y=n - 0.35, text="◤ TRAFFIC ENGINEERING PROCESS",
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
        f"<div class='brief-bar'>PROJECT BRIEF · DWG UTC-SIG-001 · REV A · {len(PHASES)} PHASES / {len(STEPS)} STEPS</div>"
        f"<div style='font-size:32px;font-weight:800;color:{TEXT}'>🚦 &nbsp;AI for Traffic Signal Optimization</div>"
        f"</div>", unsafe_allow_html=True)
    st.write("")

    _op_header("01", "The Engineering Problem", CIVIL)
    st.markdown("""
A signalised junction runs a **fixed-time plan** set from a survey taken years ago. Demand is not fixed:
the **main street peaks in the morning**, the **cross street peaks in the evening**, and a school run,
a match or a blocked lane moves it again. A plan tuned for the average is **wrong at both peaks**, and
retiming means another manual count and months of waiting. The job: **cut delay without adding a lane.**
    """)
    st.write("")
    st.divider()

    _op_header("02", "What We Are Going To Build", CIVIL)
    st.markdown("An **adaptive signal control system** for the junction. Four parts:")
    st.write("")
    c1, c2, c3, c4 = st.columns(4)
    for col, (icon, title, body) in zip(
        (c1, c2, c3, c4),
        [("📡", "Detectors read the demand",
          "Flow on both streets, loop occupancy, headway, pedestrian calls, the hour, and the cycle and "
          "green times actually run. Logged every cycle."),
         ("📷", "The camera reads the queue",
          "The approach itself, where a standing queue is a shape in the image and not a number any "
          "loop can report."),
         ("🧠", "AI predicts delay and finds the queue",
          "Predict the delay a cycle will produce, flag the unexplained drop that means an incident, "
          "grade the camera frame, and find the cycle length with the lowest delay."),
         ("🔔", "The operator gets an instruction",
          "Not a black box. A clear call: give this arm more green, this many seconds, this is the "
          "queue on the frame — with the evidence shown, so a person decides.")]):
        with col:
            st.markdown(
                f"<div class='spec' style='height:100%'>"
                f"<div class='card-ico'>{icon}</div>"
                f"<b style='color:{TEXT}'>{title}</b><br>"
                f"<span class='muted'>{body}</span></div>", unsafe_allow_html=True)
    st.write("")
    st.markdown(
        f"<div style='border-left:3px solid {GREEN};padding:8px 0 8px 16px;font-size:16px;"
        f"color:{TEXT};line-height:1.65'>The traffic engineer stays in charge and stays accountable. "
        f"The system handles the part one person cannot: it reads every cycle on every approach and turns "
        f"what it finds into seconds of delay. The goal is <b>Traffic Engineer + AI</b> — a junction that "
        f"keeps up with its own demand.</div>", unsafe_allow_html=True)
    st.write("")
    st.divider()

    _op_header("03", "The Engineering Workflow", CIVIL)
    st.markdown(
        f"<div style='color:{MUTED};font-size:15px;line-height:1.6'>These are the {len(PHASES)} phases of "
        f"<b>one signal-optimisation project</b>, in the order a real scheme runs them. "
        f"Every <b style='color:{CIVIL}'>amber node</b> is a traffic activity. Every "
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

    _op_header("04", "Engineering → AI, The Whole Map", AISIDE)
    st.markdown(
        f"<div style='color:{MUTED};font-size:15px;line-height:1.6'><b>Every AI concept here is a traffic "
        f"activity you already understand</b> — the same thing, named differently by a different "
        f"profession. Read down the amber column and you have described a signal scheme. Read down the "
        f"cyan column and you have described a deep learning pipeline.</div>", unsafe_allow_html=True)
    st.write("")
    st.plotly_chart(mapping_figure(style), use_container_width=True, key="mapping")
    st.write("")

    st.markdown(
        f"<div style='border-left:3px solid {AISIDE};padding:8px 0 8px 16px;font-size:16px;"
        f"color:{TEXT};line-height:1.65'>Each AI concept shows up because the traffic work ran into "
        f"something one engineer could not do by hand. Only then does it get a technical name.</div>",
        unsafe_allow_html=True)
    st.write("")

    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("▶  Start: stand at the junction", use_container_width=True, type="primary"):
            goto("in-peak")
    with c2:
        st.caption(f"{len(PHASES)} phases · {len(STEPS)} steps · one signal-optimisation project. "
                   "Every step opens with the traffic activity, then the AI it becomes.")
