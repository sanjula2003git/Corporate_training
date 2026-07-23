"""
bridge.py - the Mechanical-Engineering -> AI teaching scaffold.
===============================================================
This module does not teach any NEW concept and it does not render any new
model, animation or asset. Every technical illustration lives in app.py /
story.py. This module wraps each stage renderer in a five-part structure so a
Mechanical Engineering student always sees, on every page:

    Mechanical Engineering   the plant context        (bridge.open_page)
    The Challenge            why the manual way runs out (bridge.open_page)
    AI Connection            + the bridge figure       (bridge.open_page)
    Technical Idea           <- the EXISTING renderer, untouched
    Key Takeaway             one sentence              (bridge.close_page)
    In the Notebook          where it lives            (bridge.close_page)

Text is deliberately short and professional. Short sentences, active voice, no
drama. The visuals carry the page; the text supports them.

COLOR IS A TEACHING DEVICE. Amber is ALWAYS the plant / mechanical world.
Cyan is ALWAYS the AI world. Violet is ALWAYS the technical process.
"""
import streamlit as st
import plotly.graph_objects as go

# ---------------------------------------------------------------- palette
BG, PANEL = "#0e1117", "#161b22"
CIVIL = "#ffb74d"      # amber  - the plant / mechanical engineering
AISIDE = "#4fc3f7"     # cyan   - the AI
TECH = "#ba68c8"       # violet - the technical process
GREEN, RED = "#66bb6a", "#ef5350"
MUTED, TEXT = "#8b949e", "#e6edf3"


# ============================================================================
# THE ENGINEERING WORKFLOW
# The phases of running a plant on predictive maintenance. Every AI concept
# hangs off one of them. The last one is the ledger the work gets judged by.
# ============================================================================
PHASES = [
    ("The Factory Floor",       "Machines run, and a failure stays hidden until the line stops."),
    ("Machine Inspection",      "Machine health is turned into a written record."),
    ("Condition Monitoring",    "Sensors are commissioned, and reality becomes a data stream."),
    ("Preparing the Data",      "Bad readings are removed, every sensor is scaled, and the data is split."),
    ("Baseline From Readings",  "A first model predicts failure risk from the sensor summary alone."),
    ("The Raw Signal Wall",     "The accelerometer is added, and threshold rules stop working."),
    ("How a Machine Learns",    "A trained network takes over from one engineer's judgement."),
    ("Reading the Vibration",   "A CNN reads the raw signal that fixed rules could not."),
    ("Reading the Trend",       "A sequence model reads the degradation curve over time."),
    ("The Reliability Audit",   "We check whether every prediction was actually right."),
    ("Fusion & Prevention",     "Every signal feeds one control room that raises a work order."),
    ("The Business Case",       "Avoided downtime is measured in machine-hours and cost."),
]


# ============================================================================
# THE STEPS  (one per page; len(STEPS) is the count - do not hardcode it)
#   civil / ai   - the two names of the same idea (amber name, cyan name)
#   tech         - what is actually computed (violet)
#   site         - Mechanical Engineering. NO AI in this text. 2-4 sentences.
#   challenge    - The Challenge. Why the manual way runs out of road.
#   ai_link      - AI Connection. Why this AI concept is therefore required.
#   takeaway     - Key Takeaway. ONE sentence.
#   notebook     - In the Notebook. Where this lives in the Colab notebook.
#   contributes  - In the Notebook. What this step contributes to the system.
# ============================================================================
STEPS = [

# ---------------------------------------------- PHASE 1 - THE FACTORY FLOOR
dict(
    id='floor', phase=0,
    civil='A Shift On The Floor', ai='Why Predictive Maintenance Exists',
    civil_icon='🏭', ai_icon='🤖',
    tech="Run-to-failure timeline vs one engineer's rounds",
    civil_bullets=['Forty machines', 'One maintenance engineer', 'Three shifts'],
    ai_bullets=['Watches every machine', 'All the time', 'Flags what drifts'],
    site="""A plant runs forty rotating machines: motors, pumps, compressors, a line of CNC spindles. A
bearing does not fail all at once. It heats, it vibrates, it draws more current for days before it
seizes.""",
    challenge="""One maintenance engineer walks the rounds a few times a shift. Between rounds, a machine can drift
from healthy to failed with nobody watching. Time-based servicing either replaces good parts too
early or misses the one that was about to go.""",
    ai_link="""The plant does not need judgement replaced. It needs the readings watched continuously, so early
drift is caught between rounds. That steady, tireless watching is the only reason AI belongs on the
floor.""",
    notebook="""Act 1. The machine fleet as an array, and a count of failures caught between rounds.""",
    contributes="""The requirement the system is measured against. If unplanned downtime does not fall, it failed.""",
    takeaway="""One engineer cannot watch forty machines between rounds - so the readings are watched instead.""",
),
dict(
    id='enter-ai', phase=0,
    civil='A Second Set Of Senses', ai='Continuous Condition Monitoring',
    civil_icon='📡', ai_icon='🛰️',
    tech='Same fleet, sampled continuously instead of on rounds',
    civil_bullets=['Engineer stays', 'Sensors watch too', 'Nobody is replaced'],
    ai_bullets=['All machines, always', 'Flags, not decisions', 'Engineer acts'],
    site="""Nothing about the machines changes. Same motors, same duty cycle, same plant. The engineer still
diagnoses and still signs the work order. Sensors are added that report every machine's condition
between rounds.""",
    challenge="""The usual objection: is this here to replace the engineer? No. A model that sees only numbers cannot
feel a hot casing, hear a bad bearing, or judge whether a machine can run to the weekend. It can
only notice a change.""",
    ai_link="""This fixes the role of AI for the whole project. The system raises a flag; a human diagnoses and
decides. Every later design choice, especially the reliability audit, follows from that split.""",
    notebook="""No code. This step is the argument, not the arithmetic.""",
    contributes="""Defines the system's output: an alert to an engineer, not an automatic shutdown.""",
    takeaway="""The system notices the change. The engineer decides what to do about it.""",
),

# ---------------------------------------------- PHASE 2 - MACHINE INSPECTION
dict(
    id='inspection', phase=1,
    civil='Machine Health Inspection', ai='Data Collection',
    civil_icon='🔧', ai_icon='🗄️',
    tech='One machine, one moment -> one row of seven readings',
    civil_bullets=['Walk to the machine', 'Read the instruments', 'Log the condition'],
    ai_bullets=['Each sensor is a column', 'Each check is a row', 'Rows stack into a table'],
    site="""You inspect a pump. Bearing temperature from the infrared gun, discharge pressure from the gauge,
vibration from the handheld meter, speed, motor current, oil condition, hours run. Each is read and
written down.""",
    challenge="""Whoever reads that sheet later does not get the machine. Not the smell of hot oil, not the meter
that was drifting. They get seven numbers. A wrong or missing reading means a wrong conclusion.""",
    ai_link="""For a model that limitation is absolute. It never stands at the machine and cannot go back to check.
One row of readings is all it gets, so a wrong row gives a wrong prediction with no way to notice.
That is why the next steps are all about the record.""",
    notebook="""The `SENSORS` list and one machine's row - the whole machine, as the model receives it.""",
    contributes="""Every prediction is computed from a row like this. It is the system's only contact with the plant.""",
    takeaway="""The record is the model's entire machine. Wrong record, wrong prediction.""",
),
dict(
    id='two-signals', phase=1,
    civil='A Reading vs A Waveform', ai='Structured vs Raw-Signal Data',
    civil_icon='📊', ai_icon='🌊',
    tech='7 named readings vs 2,048 unnamed samples per second',
    civil_bullets=['A few gauge numbers', 'A wiggly vibration trace', 'Same machine, two records'],
    ai_bullets=['Named columns of numbers', 'Unnamed raw samples', 'One model for both?'],
    site="""One machine produces two kinds of record. The instrument summary: temperature, pressure, vibration
level, speed, current, oil, runtime - seven values an engineer named and gave units. The raw
accelerometer: thousands of amplitude samples a second, with nothing in it named.""",
    challenge="""A vibration level of 7 mm/s already means something, because a standard defines it. The raw waveform
means nothing until it is processed - and a bearing fault hides in its shape, not its average, which
a single number throws away.""",
    ai_link="""One machine, two kinds of record, one question that shapes the course: can one kind of model handle
both? The ML baseline and the CNN answer it by building on each and watching where each fails.""",
    notebook="""No code. Seven named readings set beside one raw vibration trace.""",
    contributes="""The two branches of the finished system: tabular readings, and the raw signal.""",
    takeaway="""Named readings and a raw waveform are two different problems.""",
),

# ---------------------------------------------- PHASE 3 - CONDITION MONITORING
dict(
    id='load', phase=2,
    civil='Commissioning The Sensor Log', ai='Loading The Dataset',
    civil_icon='🚚', ai_icon='📥',
    tech='pd.read_csv -> 1,200 machine-records x 8 columns',
    civil_bullets=['Log file arrives', 'Check the header', 'Count the records'],
    ai_bullets=['Read the file', 'Check the header', 'Count the rows'],
    site="""The condition-monitoring system has logged every machine for months. Before anything is built on it,
you open the export and check it against what was installed. How many records? Are all seven sensors
present? Is each column the type it should be?""",
    challenge="""The temptation is to skip the check and start modeling. That is how a project discovers weeks later
that one sensor logged in the wrong unit, or half the records came from a machine that was offline.""",
    ai_link="""Loading a dataset is that commissioning check. Establish what arrived: how many records, how many
columns, what type each is. A model trained on the wrong data does not error - it trains without
complaint and gives wrong answers.""",
    notebook="""`pd.read_csv` on the sensor log, then the row and column count.""",
    contributes="""The intake gate for the sensor branch. Every number the model learns from enters here.""",
    takeaway="""Check what the sensors actually logged before you build on it.""",
),
dict(
    id='inspect', phase=2,
    civil='Sensor Health Check', ai='Data Inspection',
    civil_icon='🔍', ai_icon='📉',
    tech='Missing-value counts, distributions, out-of-range readings',
    civil_bullets=['Check every sensor', 'Look for gaps', 'Diagnose before acting'],
    ai_bullets=['Count the gaps', 'Plot the spread', 'Diagnose before cleaning'],
    site="""Now inspect the log the way you would inspect the sensors. A thermocouple that came loose leaves a
gap. A vibration probe that saturated reads a flat maximum. A pressure line that clogged reads a
frozen value.""",
    challenge="""You cannot eyeball 1,200 records the way you eyeball one gauge. A sensor that dropped out for an hour
leaves a hole that looks like nothing. A stuck channel looks perfectly reasonable. The fault is
invisible at this scale.""",
    ai_link="""So inspect the record with counts and distributions instead of eyes. Count missing readings per
sensor and the failed channel announces itself. Plot each column's spread and the stuck one spikes.
Diagnosis only - nothing is repaired here.""",
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
    civil_bullets=['Drop bad readings', 'Drop repeat logs', 'Keep only good rows'],
    ai_bullets=['Drop duplicate rows', 'Drop impossible values', 'Keep only clean rows'],
    site="""Act on the diagnosis. A pressure of -3 bar is impossible and comes out. A vibration reading of zero
on a running machine is a dead probe, not a healthy machine. A record logged twice is struck off.""",
    challenge="""That judgement is where inexperience shows. Drop every flawed record and there is little left to
learn from. Keep everything and a dead-probe zero teaches the model that a running machine can read
zero. No rule decides it for you.""",
    ai_link="""A duplicated record is the double-logged reading: it teaches the model one machine mattered twice. A
missing temperature is a judgement - fill with the median, or drop the row? Drop too much and there
is nothing to train on. Fill carelessly and the model believes readings that never happened.""",
    notebook="""The duplicate drop and missing-value handling, with row counts before and after.""",
    contributes="""The ML model, the CNN and the fusion engine all inherit whatever you decide here.""",
    takeaway="""Cleaning is a judgement call, and everything downstream inherits it.""",
),
dict(
    id='normalize', phase=3,
    civil='One Common Scale', ai='Normalization',
    civil_icon='📏', ai_icon='⚖️',
    tech='MinMaxScaler -> every sensor onto 0..1',
    civil_bullets=['Different units', 'One common scale', 'Now comparable'],
    ai_bullets=['°C vs bar vs mm/s', 'All scaled 0..1', 'No column dominates'],
    site="""Every sensor reports in its own unit. Temperature in the tens of degrees, speed in the thousands of
RPM, vibration in single-digit mm/s. Before they can be compared, they are put on one common scale.""",
    challenge="""Raw magnitudes lie about importance. RPM runs into the thousands; vibration runs 0 to 10 mm/s. Side
by side, RPM looks a thousand times more significant because of a unit, when a 2 mm/s rise in
vibration is the real warning.""",
    ai_link="""A neural network cannot tell a big number from an important one. It sees magnitude. Feed it raw
columns and it learns the unit, not the physics. Normalization puts every sensor on 0 to 1, so
importance is learned from the data.""",
    notebook="""`MinMaxScaler`, fitted on the sensor columns.""",
    contributes="""Without this the model trains badly and blames the wrong sensor. The scaler ships with the model.""",
    takeaway="""Scale the columns, or the network learns the units.""",
),
dict(
    id='split', phase=3,
    civil='Trial Run vs Acceptance Test', ai='Train / Test Split',
    civil_icon='🧪', ai_icon='✂️',
    tech='train_test_split -> practice machines vs unseen machines',
    civil_bullets=['Tune on the rig', 'Sign off on new units', 'Never the same unit'],
    ai_bullets=['Training set', 'Test set', 'Never the same rows'],
    site="""No engineer signs off a new machine's health model using the very unit it was tuned on. Tuning
happens on known machines. Acceptance is proven on machines the model has not seen.""",
    challenge="""Never test someone on the exact work they practised on. A model checked on the records it trained on
just repeats what it memorised, scores brilliantly, and proves nothing. The first new machine
exposes it.""",
    ai_link="""So the records are split: some to train on, some sealed away until the reliability audit. Only a
score on unseen machines says anything about the plant tomorrow.""",
    notebook="""`train_test_split`, producing the training records and the sealed acceptance set.""",
    contributes="""This is what makes the reliability audit mean anything. Break it and every result is a recital.""",
    takeaway="""The only fair score comes from machines the model has never seen.""",
),

# ---------------------------------------------- PHASE 5 - BASELINE FROM READINGS
dict(
    id='ml-baseline', phase=4,
    civil='Predicting Failure From The Readings', ai='Machine Learning',
    civil_icon='📈', ai_icon='🌲',
    tech='RandomForestClassifier on 7 named sensors',
    civil_bullets=['Engineer names the factors', 'Model weighs them', 'Failure risk out'],
    ai_bullets=['You name the factors', 'Random Forest', 'Works on readings'],
    site="""Every experienced engineer carries a failure model in their head. Hot bearing, high vibration, oil
degraded, long runtime: pull it for service. It is not written down, not consistent between two
engineers, and not available at three in the morning.""",
    challenge="""So write it down. Vibration above what, exactly? Does the limit move when the oil is old, and by how
much if the machine has run ten thousand hours? It is not a single rule. It is thousands of weighted
interactions the engineer cannot fully articulate.""",
    ai_link="""This is the job machine learning does well. You do not state the thresholds. You state the factors -
and an engineer already did that at inspection. Given seven named columns and 1,200 outcomes, the
Random Forest works out the weighting itself. The CNN later hands the same idea a raw signal.""",
    notebook="""`RandomForestClassifier`, trained on the scaled sensors, scored on the sealed machines.""",
    contributes="""The tabular branch of the system, and the benchmark the audit uses.""",
    takeaway="""Name the factors; let the model weigh them.""",
),

# ---------------------------------------------- PHASE 6 - THE RAW SIGNAL WALL
dict(
    id='signal-problem', phase=5,
    civil='What The Accelerometer Actually Sends', ai='Raw Signal As Input',
    civil_icon='🌊', ai_icon='🔢',
    tech='One window = 2,048 amplitude samples, none of them named',
    civil_bullets=['You hear a bad bearing', 'You feel the roughness', 'Instantly, free'],
    ai_bullets=['2,048 raw numbers', 'None are named', 'The fault is hidden'],
    site="""Listen to a failing bearing and you know. Put your hand on the housing and you feel it. An
experienced fitter diagnoses the fault from the sound alone, without ever explaining how.""",
    challenge="""Now explain it - precisely enough that someone who has never heard a bearing could follow. Which
sample, at what amplitude, at what spacing? The fault is a faint periodic pattern buried in
thousands of numbers.""",
    ai_link="""The accelerometer delivers 2,048 amplitude samples per window. Not one is named. Not one is the
fault. At inspection an engineer had already named temperature and pressure, which is why the ML
baseline worked. Here there is nothing pre-named to weigh.""",
    notebook="""One raw vibration window plotted, and its length printed: 2,048 unnamed numbers.""",
    contributes="""The input the Random Forest cannot use and the CNN is built for.""",
    takeaway="""A raw signal is thousands of numbers, and none of them is the fault.""",
),
dict(
    id='handmade', phase=5,
    civil='The Vibration Rulebook, By Hand', ai='Hand-Made Features',
    civil_icon='📐', ai_icon='✍️',
    tech='RMS + peak + a hand-tuned threshold on the waveform',
    civil_bullets=['Reduce it to one number', 'Set a limit', 'Watch it miss'],
    ai_bullets=['One number by hand', 'One threshold', 'Breaks easily'],
    site="""So you try the standard approach: reduce the waveform to a number. Compute its RMS level, set a
limit from the ISO chart, and alarm above it. It works for a badly worn machine screaming at 8
mm/s.""",
    challenge="""But an early bearing fault barely lifts the RMS while its shape changes completely. Tighten the limit
and every rough-running healthy machine trips it. Loosen it and the early fault sails through. One
number cannot separate them.""",
    ai_link="""Every hand-made feature is a rule you wrote and must maintain, and each one throws away most of the
signal. What you want is for the useful features to be discovered from the raw waveform, not
guessed. That is exactly what deep learning does.""",
    notebook="""RMS and peak features, one threshold, and the early-fault cases it misses.""",
    contributes="""The motive for the CNN: hand features are brittle and discard the signal's shape.""",
    takeaway="""Reducing a signal to one hand-picked number throws away the fault.""",
),
dict(
    id='why-dl', phase=5,
    civil='The Rulebook Runs Out', ai='Therefore: Deep Learning',
    civil_icon='🧠', ai_icon='🚀',
    tech='Learned features vs hand-written rules',
    civil_bullets=['No threshold works', 'Too many patterns', 'Let it learn'],
    ai_bullets=['Features are learned', 'From examples', 'Not from rules'],
    site="""Step back. You have a task an expert does instantly and cannot put into a rule: hear a bearing and
name the fault. Every threshold you write is either too tight or too loose.""",
    challenge="""The problem is not effort. There is no finite rulebook. The patterns that separate a healthy machine
from an early inner-race fault are subtle, overlapping, and different for every machine type.""",
    ai_link="""Deep learning changes the question. Instead of you writing the rules, you supply labeled examples -
healthy windows and faulty windows - and the network learns the features that separate them. It
does not dig deeper into your readings; it works where there are no named readings at all.""",
    notebook="""No code. The argument that motivates the CNN and the sequence model that follow.""",
    contributes="""The turning point of the course: from named features to learned ones.""",
    takeaway="""When nobody can write the rule, the model learns it from examples.""",
),

# ---------------------------------------------- PHASE 7 - HOW A MACHINE LEARNS
dict(
    id='engineer-brain', phase=6,
    civil="The Engineer's Judgement", ai='The Neuron, Conceptually',
    civil_icon='👷', ai_icon='🧠',
    tech='Weighted evidence -> one decision',
    civil_bullets=['Several signals', 'Each weighted', 'One call'],
    ai_bullets=['Several inputs', 'Each weighted', 'One output'],
    site="""Watch how an engineer actually decides. Vibration matters a lot. Oil condition matters somewhat.
Ambient temperature barely matters. They weigh each signal by how much it usually predicts trouble,
add it up, and make one call: run, or pull it.""",
    challenge="""That weighting is not written down and no two engineers match exactly. It is learned from years of
machines that failed and machines that did not. You cannot hand it to a night-shift technician.""",
    ai_link="""That process - weigh each input, sum, decide - is exactly one artificial neuron. The weights are what
the engineer's experience becomes. Everything that follows is how those weights get set from data.""",
    notebook="""No code. The mental model of a neuron before any mathematics.""",
    contributes="""The intuition every later step builds on: a neuron is weighted evidence to a decision.""",
    takeaway="""An engineer weighing signals into one call is a neuron.""",
),
dict(
    id='neuron', phase=6,
    civil='Weighing The Signals', ai='Weighted Sum + Bias',
    civil_icon='⚙️', ai_icon='➕',
    tech='z = w·x + b',
    civil_bullets=['Weigh each signal', 'Add them up', 'Add a bias'],
    ai_bullets=['Weigh each input', 'Add them up', 'Add a bias'],
    site="""Make the engineer's judgement explicit. Each reading gets a weight: vibration high, oil moderate,
runtime small. Multiply each reading by its weight, add them up, and add a baseline offset for how
cautious this machine's policy is.""",
    challenge="""Set those weights by hand across seven sensors and you are guessing. Too much weight on runtime and
every old-but-healthy machine is condemned. The right weights are not obvious and interact.""",
    ai_link="""This weighted sum plus bias is the whole of a neuron's forward step: z = w·x + b. Slide the weights
below and watch one machine's score cross the line. Learning, next, is just setting these weights
automatically.""",
    notebook="""The dot product `w·x + b` written out for one machine's readings.""",
    contributes="""The single computation every layer of every network repeats.""",
    takeaway="""A neuron multiplies each signal by a weight, sums, and adds a bias.""",
),
dict(
    id='activation', phase=6,
    civil='When To Raise The Alarm', ai='Activation Function',
    civil_icon='🚨', ai_icon='📈',
    tech='sigmoid / ReLU on z',
    civil_bullets=['Weak evidence: quiet', 'Strong evidence: alarm', 'A smooth switch'],
    ai_bullets=['Low score, no', 'High score, yes', 'A smooth switch'],
    site="""A weighted score is not yet an action. The engineer needs a decision: below a level, keep running;
above it, raise the alarm. And it should not flip on a single point of noise - it should turn on
smoothly as evidence builds.""",
    challenge="""A hard cut-off is brittle: one reading either side of the line flips the call. Real judgement ramps
up - a little doubt, then concern, then certainty - and a straight-line score cannot bend like that.""",
    ai_link="""The activation function is that smooth switch. Sigmoid turns any score into a 0-to-1 probability of
failure; ReLU passes strong evidence and blocks the rest. Without it, stacking neurons stays linear
and learns nothing curved.""",
    notebook="""`sigmoid` and `relu` plotted, and the same neuron with and without one.""",
    contributes="""What lets a network bend - the reason depth adds power.""",
    takeaway="""Activation turns a raw score into a decision, and lets the network bend.""",
),
dict(
    id='learning-loop', phase=6,
    civil='Every Breakdown Teaches', ai='The Learning Loop',
    civil_icon='🔁', ai_icon='🔄',
    tech='predict -> measure error -> adjust -> repeat',
    civil_bullets=['Make a call', 'See what happened', 'Adjust the rule'],
    ai_bullets=['Predict', 'Measure error', 'Update weights'],
    site="""How does an engineer get good? They call a machine safe, it fails next week, and they adjust: that
vibration pattern mattered more than they thought. Next time they weigh it heavier. Every breakdown
tunes the internal model.""",
    challenge="""Done by hand this takes a career, and the lessons live in one person's head. A plant cannot wait
years, and cannot lose the model when that person leaves.""",
    ai_link="""Training is that loop, run thousands of times a second. The network predicts, compares to the known
outcome, and nudges every weight to be a little less wrong. Predict, measure, adjust, repeat - that
is all learning is.""",
    notebook="""No code. The loop in plain terms before loss and gradients name its parts.""",
    contributes="""The skeleton of training that the next steps fill in.""",
    takeaway="""Learning is predict, measure the error, adjust, and repeat.""",
),
dict(
    id='gradient-descent', phase=6,
    civil='Adjusting The Threshold', ai='Loss + Gradient Descent',
    civil_icon='🎚️', ai_icon='⬇️',
    tech='minimize loss by stepping downhill in w',
    civil_bullets=['Measure how wrong', 'Which way is better', 'Take a step'],
    ai_bullets=['Loss = how wrong', 'Find the better way', 'Take a small step'],
    site="""To adjust a rule you need two things: a number for how wrong you were, and which direction fixes it.
Called a failure safe and it failed - that is a large, costly error. Nudge the threshold the way
that would have caught it, by a sensible amount.""",
    challenge="""Nudge by hand across seven weights at once and you cannot tell which change helped. Too big a step
and you overshoot into false alarms; too small and it never settles. And there is no time to try
every combination.""",
    ai_link="""Loss measures how wrong the network is; the gradient points to the weights that reduce it fastest.
Gradient descent takes a step downhill, again and again, until the error stops falling. Slide the
step size below and watch it converge or overshoot.""",
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
    site="""One engineer has limits. A reliability team layers expertise: a vibration specialist feeds a machine
lead, who feeds the reliability manager. Each layer combines what the one below noticed into a
higher-level judgement.""",
    challenge="""A single weighted rule can only split the world with one straight line. Real failure patterns are
not linear - hot and high-vibration means one thing, hot and low-vibration another. One neuron
cannot hold that.""",
    ai_link="""Stack neurons into layers and the network composes simple features into complex ones, exactly like
the team. The first layer finds crude patterns; deeper layers combine them. Depth is what lets it
represent any decision boundary.""",
    notebook="""An `MLPClassifier` with hidden layers, and how width and depth change the fit.""",
    contributes="""The architecture the tabular ANN and, later, the CNN and LSTM are all built from.""",
    takeaway="""Layered neurons compose simple signals into complex judgements.""",
),
dict(
    id='training', phase=6,
    civil='Running The Trials', ai='Training The Model',
    civil_icon='🏋️', ai_icon='📉',
    tech='epochs of forward pass + backprop on the training set',
    civil_bullets=['Show known machines', 'Correct each miss', 'Repeat the rounds'],
    ai_bullets=['Show it examples', 'Correct each miss', 'The error drops'],
    site="""Commission the model the way you commission a technician: show it many machines whose outcome is
known, let it call each, correct every miss, and go around again. Each full pass over the examples
is one round of trials.""",
    challenge="""Too few trials and it has not learned the patterns. Too many on the same machines and it memorises
them - brilliant on the training set, useless on a new machine. You need to know when to stop.""",
    ai_link="""Training runs the learning loop over the whole training set for many epochs, watching the loss fall
on data it trains on and on held-out data it does not. When the held-out loss stops improving, you
stop. Watch both curves below.""",
    notebook="""The training loop, the train/validation loss curves, and the early-stopping point.""",
    contributes="""Produces the trained tabular model that the audit then judges.""",
    takeaway="""Training repeats the learning loop until held-out error stops falling.""",
),

# ---------------------------------------------- PHASE 8 - READING THE VIBRATION
dict(
    id='cnn-journey', phase=7,
    civil='How The Signal Is Read', ai='Convolutional Neural Network',
    civil_icon='🌊', ai_icon='🧬',
    tech='filters -> feature maps -> fault class',
    civil_bullets=['Slide a detector', 'Find repeating marks', 'Build up the fault'],
    ai_bullets=['Sliding filters', 'Find the patterns', 'Learned, not coded'],
    site="""A vibration analyst does not read 2,048 numbers. They look for repeating features - the spacing of
impacts, the sidebands around a frequency - and build a diagnosis from those patterns wherever they
appear in the trace.""",
    challenge="""You cannot write down every fault signature by hand, and a fault can appear anywhere in the window.
A fixed rule at a fixed position misses a fault that arrives a moment later.""",
    ai_link="""A CNN slides small learned filters along the signal, each one firing on a pattern - an impact, a
harmonic - wherever it occurs. Early filters find simple shapes; later layers combine them into a
fault signature. The features are learned from labeled windows, not coded.""",
    notebook="""A 1-D CNN on the vibration windows, with its filters and feature maps visualized.""",
    contributes="""The raw-signal branch: the fault detector the hand-made threshold could not be.""",
    takeaway="""A CNN learns the fault patterns in a signal instead of you coding them.""",
),

# ---------------------------------------------- PHASE 9 - READING THE TREND
dict(
    id='lstm', phase=8,
    civil='The Degradation Curve', ai='LSTM / Sequence Model',
    civil_icon='📉', ai_icon='⏳',
    tech='a sequence of readings -> remaining useful life',
    civil_bullets=['One reading: little', 'The trend: everything', 'Order matters'],
    ai_bullets=['Reads readings in order', 'Remembers the trend', 'Predicts time left'],
    site="""A single vibration reading barely tells you anything. The trend does. A level creeping up over two
weeks means a bearing is degrading; the same level, steady for a year, means the machine simply runs
rough. Order and history are the diagnosis.""",
    challenge="""The tabular model sees one row at a time and has no memory of yesterday. It cannot tell a rising
trend from a steady one, because it never sees the sequence - only the latest number.""",
    ai_link="""An LSTM reads readings in order and carries a memory of what came before, so it can separate a rising
trend from a flat one and estimate remaining useful life. It answers not just 'is it failing' but
'how long have we got'.""",
    notebook="""An LSTM on windows of sequential readings, predicting remaining useful life.""",
    contributes="""The time branch: turns a snapshot risk into a countdown to failure.""",
    takeaway="""A sequence model reads the trend, not the snapshot, and predicts how long is left.""",
),

# ---------------------------------------------- PHASE 10 - THE RELIABILITY AUDIT
dict(
    id='audit', phase=9,
    civil='The Reliability Audit', ai='Confusion Matrix',
    civil_icon='📋', ai_icon='🔲',
    tech='TN / FP / FN / TP on the sealed test machines',
    civil_bullets=['Line up every call', 'Against what happened', 'Four outcomes'],
    ai_bullets=['Two right boxes', 'Two wrong boxes', 'The missed one hurts'],
    site="""Audit the model the way you would audit a maintenance contractor. A hundred machine-months happened.
The maintenance log says what really occurred on each. The model made a call on each. Line them up
and count.""",
    challenge="""Four things can happen, and lumping them together hides the one that matters. Called healthy, stayed
healthy: fine. Called failing, it failed: caught it. Called failing, nothing happened: a false alarm
and a wasted callout. Called healthy, and it failed: the costly miss - unplanned downtime.""",
    ai_link="""Put those four boxes in a square and you have the confusion matrix - you did not learn it, you
audited the plant and it fell out. Never quote accuracy alone: a model that calls everything healthy
scores well and misses every real failure.""",
    notebook="""The test-set predictions, `ConfusionMatrixDisplay`, and the warning that follows.""",
    contributes="""The acceptance test, run on the machines sealed away at the split.""",
    takeaway="""Accuracy hides the one box that matters - the missed failure.""",
),
dict(
    id='proof', phase=9,
    civil='Readings vs Signals: The Verdict', ai='Where Deep Learning Earns Its Place',
    civil_icon='⚖️', ai_icon='🏁',
    tech='RF vs ANN on readings; threshold vs CNN on the waveform',
    civil_bullets=['Gauges: both fine', 'Waveform: only one', 'Right tool, right job'],
    ai_bullets=['Numbers: both work', 'Signals: only DL', 'Pick the right tool'],
    site="""Here is the plain verdict. On the seven named readings an engineer defined, machine
learning and deep learning perform about the same.""",
    challenge="""So if deep learning does not win on the gauges, why learn it? Because of the waveform. Your hand-made
threshold failed and no limit saved it, and the Random Forest cannot be pointed at 2,048 unnamed
samples at all.""",
    ai_link="""Here is the thesis, proved rather than claimed. When an engineer has named the features, use machine
learning - simpler, faster, easier to defend. When nobody can name them, as with the raw signal,
deep learning is the option that works. AI does not out-think the engineer; it covers the part no
one can do by hand.""",
    notebook="""Random Forest against the ANN on readings, and the raw-signal task neither hand-rule could touch.""",
    contributes="""Justifies two branches instead of one model - and stops you reaching for DL on a spreadsheet.""",
    takeaway="""Deep learning earns its place only where nobody can name the features.""",
),

# ---------------------------------------------- PHASE 11 - FUSION & PREVENTION
dict(
    id='fusion-engine', phase=10,
    civil='The Maintenance Control Room', ai='AI Fusion',
    civil_icon='🎛️', ai_icon='🔗',
    tech='ANN + CNN + LSTM + asset context -> one work order',
    civil_bullets=['Every feed lands here', 'Compare them all', 'One work order'],
    ai_bullets=['One model: unsure', 'All three agree', 'One work order'],
    site="""Every reliability center has a control room. The gauge readings on one screen, the vibration
analysis on another, the runtime and criticality of each asset in the register. The engineer in the
middle does not act on any one feed - they cross-reference them.""",
    challenge="""Each feed alone is close to noise. The readings say elevated risk - it could be a hot day. The CNN
flags a signal pattern - it could be one rough window. The trend is rising - on a non-critical spare
it can wait. A system that alarms on any one gets switched off in a fortnight.""",
    ai_link="""Now fuse them. Pump P-12, a critical asset, shows rising vibration risk from the readings, a
bearing-fault pattern from the CNN, and a two-week countdown from the trend. That is not three weak
signals. That is one work order with a deadline. Several models, one decision, one engineer who
acts.""",
    notebook="""`fusion_engine(readings, signal, trend, asset)` - the control room as a function.""",
    contributes="""This is the product. Everything before it was a component.""",
    takeaway="""Weak signals, fused with asset context, become one prioritized work order.""",
),
dict(
    id='pipeline', phase=10,
    civil='The Complete Predictive Plant', ai='The AI Engineering Pipeline',
    civil_icon='🏙️', ai_icon='🛤️',
    tech='raw sensors -> models -> fused decision -> work order',
    civil_bullets=['Sensors to decision', 'Every stage in order', 'One flow'],
    ai_bullets=['Load, clean, model', 'Test, then combine', 'Deliver the order'],
    site="""Step back and see the whole plant as one flow: machines sensed, readings logged and cleaned, models
trained and audited, signals fused, and a prioritized work order handed to the engineer - who still
makes the call.""",
    challenge="""Any single stage done well is worthless if the chain breaks. A perfect model on dirty data, or a
great prediction nobody acts on, saves no downtime. The value is in the whole pipeline.""",
    ai_link="""This is the AI engineering pipeline: ingest, clean, prepare, model, evaluate, fuse, serve. Every page
of this course was one stage of it, in the order a real project runs them.""",
    notebook="""The end-to-end pipeline assembled, from raw log to a served work order.""",
    contributes="""Ties every previous step into one deployable system.""",
    takeaway="""The value is the whole pipeline, not any one model in it.""",
),

# ---------------------------------------------- PHASE 12 - THE BUSINESS CASE
dict(
    id='dashboard', phase=11,
    civil='Downtime Avoided', ai='The Predictive Maintenance Dashboard',
    civil_icon='🖥️', ai_icon='🔔',
    tech='fleet health -> avoided downtime, in hours and cost',
    civil_bullets=['Fleet at a glance', 'Ranked by risk', 'Downtime avoided'],
    ai_bullets=['All models, one screen', 'Ranked alerts', 'Hours and cost saved'],
    site="""The control center the plant manager actually opens. Every machine on one screen, colored by health,
ranked by how soon it needs attention, with the projected downtime each early catch avoided.""",
    challenge="""None of the engineering matters to the business until it is a number a manager can act on: which
machine, how urgent, and how many hours of unplanned downtime were avoided this month.""",
    ai_link="""The dashboard is where every model's output becomes a decision and a cost. Move the sliders to your
own fleet size and duty and read off the hours and money that planned intervention saves over
run-to-failure.""",
    notebook="""The fleet health table, the ranking, and the avoided-downtime calculation.""",
    contributes="""The closing view: the whole system as one screen and one business case.""",
    takeaway="""The dashboard turns every model output into a ranked decision and a saved cost.""",
),
]


# ---------------------------------------------------------------- short labels
SHORT = {
    "floor": "A shift on the floor",   "enter-ai": "Continuous monitoring",
    "inspection": "Health inspection", "two-signals": "Reading vs signal",
    "load": "Sensor log arrives",      "inspect": "Sensor health check",
    "clean": "Dropouts & spikes",      "normalize": "Standardize units",
    "split": "Trial vs acceptance",    "ml-baseline": "Risk from gauges",
    "signal-problem": "The raw waveform", "handmade": "Threshold by hand",
    "why-dl": "Rulebook fails",        "engineer-brain": "Engineer decides",
    "neuron": "Weighing signals",      "activation": "Alarm threshold",
    "learning-loop": "Learn from failures", "gradient-descent": "Tune the strategy",
    "network": "Diagnostic team",      "training": "Run the trials",
    "cnn-journey": "Read the vibration", "lstm": "Read the trend",
    "audit": "Reliability audit",      "proof": "The verdict",
    "fusion-engine": "Control room",   "pipeline": "The whole plant",
    "dashboard": "Downtime ledger",
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


def _card(fig, x0, x1, color, icon, title, bullets, kicker):
    fig.add_shape(type="rect", x0=x0, x1=x1, y0=0.7, y1=5.5,
                  line=dict(color=color, width=2), fillcolor=PANEL, layer="below")
    cx = (x0 + x1) / 2
    fig.add_annotation(x=cx, y=5.05, text=f"<b>{kicker}</b>", showarrow=False,
                       font=dict(size=11, color=color), xanchor="center")
    fig.add_annotation(x=cx, y=4.30, text=icon, showarrow=False,
                       font=dict(size=34), xanchor="center")
    fig.add_annotation(x=cx, y=3.25, text=f"<b>{_wrap(title)}</b>", showarrow=False,
                       font=dict(size=14, color=TEXT), xanchor="center", align="center")
    for i, b in enumerate(bullets):
        fig.add_annotation(x=cx, y=2.20 - i * 0.55, text=f"• {b}", showarrow=False,
                           font=dict(size=12, color=MUTED), xanchor="center")


def bridge_figure(step, style, animate):
    """The mechanical-activity -> AI-equivalent -> technical-process bridge."""
    fig = go.Figure()
    _card(fig, 0.2, 3.4, CIVIL, step["civil_icon"], step["civil"],
          step["civil_bullets"], "IN THE PLANT")
    _card(fig, 6.6, 9.8, AISIDE, step["ai_icon"], step["ai"],
          step["ai_bullets"], "IN THE AI")

    fig.add_annotation(x=6.45, y=3.0, ax=3.55, ay=3.0, xref="x", yref="y",
                       axref="x", ayref="y", showarrow=True, arrowhead=2,
                       arrowsize=1.4, arrowwidth=2.5, arrowcolor=MUTED, text="")
    fig.add_annotation(x=5.0, y=3.5, text="<b>becomes</b>", showarrow=False,
                       font=dict(size=12, color=MUTED))

    fig.add_shape(type="rect", x0=3.5, x1=6.5, y0=1.3, y1=2.15,
                  line=dict(color=TECH, width=1.5), fillcolor=PANEL, layer="below")
    fig.add_annotation(x=5.0, y=1.96, text="<b>WHICH IS COMPUTED AS</b>", showarrow=False,
                       font=dict(size=9, color=TECH))
    fig.add_annotation(x=5.0, y=1.58, text=step["tech"], showarrow=False,
                       font=dict(size=10, color=TEXT), xanchor="center", align="center")
    fig.add_annotation(x=5.0, y=2.45, text="↓", showarrow=False,
                       font=dict(size=18, color=TECH))

    fig.add_trace(go.Scatter(x=[3.6], y=[3.0], mode="markers",
                             marker=dict(size=15, color=CIVIL,
                                         line=dict(color=TEXT, width=1)),
                             hoverinfo="skip", showlegend=False))
    frames = []
    for i in range(24):
        t = i / 23
        x = 3.6 + t * 2.8
        c = CIVIL if t < 0.45 else (TEXT if t < 0.55 else AISIDE)
        frames.append(go.Frame(data=[go.Scatter(
            x=[x], y=[3.0], mode="markers",
            marker=dict(size=15, color=c, line=dict(color=TEXT, width=1)))]))
    animate(fig, frames, ms=90)

    fig.update_xaxes(visible=False, range=[0, 10])
    fig.update_yaxes(visible=False, range=[0.4, 5.8])
    return style(fig, h=370)


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
            f"<div style='text-align:center;padding:6px 4px;border:1px solid {CIVIL};"
            f"border-radius:8px;background:{PANEL}'>"
            f"<span style='color:{MUTED};font-size:11px'>YOU ARE HERE · STEP {i+1} OF {len(ORDER)}</span><br>"
            f"<b style='color:{CIVIL}'>{step['civil']}</b></div>",
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
    st.markdown(
        f"<div style='margin-top:14px;color:{MUTED};font-size:13px'>"
        f"PHASE {step['phase']+1} OF {len(PHASES)} · <b style='color:{CIVIL}'>{pname}</b>"
        f" — {pdesc}</div>", unsafe_allow_html=True)
    st.markdown(f"# {step['civil_icon']}  {step['civil']}")
    st.markdown(
        f"<span style='color:{MUTED}'>This engineering activity is the AI concept </span>"
        f"<b style='color:{AISIDE}'>{step['ai']}</b>.",
        unsafe_allow_html=True)
    st.divider()

    # ---- Part 1 -----------------------------------------------------------
    st.markdown(f"### <span style='color:{CIVIL}'>Mechanical Engineering</span>",
                unsafe_allow_html=True)
    st.markdown(
        f"<div style='border-left:3px solid {CIVIL};padding:2px 0 2px 16px;"
        f"color:{TEXT};font-size:16px;line-height:1.65'>{step['site']}</div>",
        unsafe_allow_html=True)
    st.write("")

    # ---- Part 2 -----------------------------------------------------------
    st.markdown(f"### <span style='color:{CIVIL}'>The Challenge</span>",
                unsafe_allow_html=True)
    st.markdown(
        f"<div style='border-left:3px solid {RED};padding:2px 0 2px 16px;"
        f"color:{TEXT};font-size:16px;line-height:1.65'>{step['challenge']}</div>",
        unsafe_allow_html=True)
    st.write("")

    # ---- Part 3 -----------------------------------------------------------
    st.markdown(f"### <span style='color:{AISIDE}'>AI Connection</span>",
                unsafe_allow_html=True)
    st.markdown(
        f"<div style='border-left:3px solid {AISIDE};padding:2px 0 2px 16px;"
        f"color:{TEXT};font-size:16px;line-height:1.65'>{step['ai_link']}</div>",
        unsafe_allow_html=True)
    st.plotly_chart(bridge_figure(step, style, animate), use_container_width=True,
                    key=f"bridge_{stage}")
    st.caption("▶ Press Play to watch the engineering activity cross into the AI.")
    st.divider()

    # ---- Part 4 header ----------------------------------------------------
    st.markdown(f"### <span style='color:{TECH}'>Technical Idea</span>",
                unsafe_allow_html=True)
    st.caption(f"{step['tech']} — interactive. Change things and watch what happens.")


# ============================================================================
# close_page  -  Part 5, rendered BELOW the existing stage renderer
# ============================================================================
def close_page(stage):
    step = BY_ID.get(stage)
    if step is None:
        return
    st.divider()

    st.markdown(
        f"<div style='background:{PANEL};border-left:4px solid {AISIDE};border-radius:8px;"
        f"padding:14px 18px'>"
        f"<div style='color:{MUTED};font-size:11px;letter-spacing:.8px'>KEY TAKEAWAY</div>"
        f"<div style='color:{TEXT};font-size:19px;font-weight:600;line-height:1.5'>"
        f"{step['takeaway']}</div></div>", unsafe_allow_html=True)
    st.write("")

    st.markdown("### <span style='color:#8bc34a'>In the Notebook</span>",
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Where you implement it**\n\n{step['notebook']}")
    with c2:
        st.markdown(f"**What it contributes**\n\n{step['contributes']}")

    render_quiz(stage)

    st.write("")
    dots = []
    for i, (pname, _) in enumerate(PHASES):
        if i == step["phase"]:
            dots.append(f"<span style='color:{CIVIL};font-weight:700'>● {pname}</span>")
        elif i < step["phase"]:
            dots.append(f"<span style='color:#3f4650'>● {pname}</span>")
        else:
            dots.append(f"<span style='color:#3f4650'>○ {pname}</span>")
    st.markdown(
        f"<div style='background:{PANEL};border-radius:8px;padding:10px 14px;font-size:12px;"
        f"line-height:2.1'><span style='color:{MUTED}'>THE BUILD SO FAR &nbsp;</span>"
        + " &nbsp;→&nbsp; ".join(dots) + "</div>", unsafe_allow_html=True)
    st.write("")
    _nav_strip(step, "bottom")


# ============================================================================
# CHECK-YOUR-UNDERSTANDING QUIZ  (one question per stage, shown by close_page)
# Each entry: q = question, options = choices, answer = index of the correct
# option, why = the explanation shown after any answer is picked.
# ============================================================================
QUIZ = {
    'floor': dict(
        q="Why isn't a fixed time-based servicing schedule enough for the plant's rotating machines?",
        options=["Machines never actually fail on schedule",
                 "A bearing degrades gradually and unpredictably, so a fixed calendar either replaces healthy parts too early or misses the one about to seize",
                 "Servicing is not allowed without sensors",
                 "The engineer works too slowly"],
        answer=1,
        why="A bearing heats, vibrates and draws more current for days before it seizes. One engineer on rounds cannot watch forty machines continuously, so the readings are watched instead."),
    'enter-ai': dict(
        q="When continuous condition monitoring is added, what changes about the engineer's role?",
        options=["The engineer is replaced by the model",
                 "Nothing about the role — the engineer still diagnoses and signs the work order; the sensors only watch between rounds",
                 "The sensors shut machines down automatically",
                 "The engineer now only reads dashboards"],
        answer=1,
        why="The system raises a flag; a human diagnoses and decides. A model that sees only numbers cannot feel a hot casing or judge whether a machine can run to the weekend."),
    'inspection': dict(
        q="What does the model actually receive about the pump it will assess?",
        options=["A live view of the running machine",
                 "One row of readings — the model never stands at the machine and cannot go back to re-check",
                 "The engineer's intuition about the machine",
                 "A continuous video of the maintenance history"],
        answer=1,
        why="The record is the model's only contact with the plant. A wrong or missing reading gives a wrong prediction, with no way for the model to notice."),
    'two-signals': dict(
        q="Why does the raw accelerometer waveform need different treatment from the seven gauge readings?",
        options=["The waveform is simply measured in different units",
                 "A bearing fault hides in the waveform's shape, not in any single named value, so an averaged number throws it away",
                 "The waveform has far fewer data points",
                 "Gauges are always more accurate than accelerometers"],
        answer=1,
        why="Seven values an engineer named and gave units, versus thousands of unnamed samples where the fault lives in the shape — two different problems, answered by the ML baseline and the CNN."),
    'load': dict(
        q="Why open the exported log and check its shape and column types before building any model?",
        options=["To make the file smaller",
                 "A model trained on wrong data does not error — it trains happily and returns wrong answers, so silent problems must be caught at intake",
                 "Because a regulation requires it",
                 "To rename the machines in the file"],
        answer=1,
        why="Loading a dataset is a commissioning check: how many records, how many columns, what type each is. A wrong unit or an offline machine's records slip through silently otherwise."),
    'inspect': dict(
        q="How do you find a stuck or dropped-out sensor hidden across 1,200 records?",
        options=["Read every row by eye",
                 "Count missing values per sensor and plot each column's spread — the failed channel spikes or flat-lines",
                 "Trust the sensor's own status light",
                 "Delete the dataset and start over"],
        answer=1,
        why="You cannot eyeball 1,200 records. Counts and distributions make a dropout or a frozen channel announce itself. This step diagnoses only — nothing is repaired yet."),
    'clean': dict(
        q="A vibration reading of zero appears for a running machine. What is it, and why does keeping it hurt?",
        options=["A healthy machine; keep it as-is",
                 "A dead probe, not a still machine — kept in, it teaches the model that a running machine can read zero",
                 "A duplicate record with no effect",
                 "A harmless rounding error"],
        answer=1,
        why="Cleaning is a judgement call. Drop too much and there is little left to learn from; keep impossible values and the model learns nonsense. The ML model, CNN and fusion engine all inherit the decision."),
    'normalize': dict(
        q="Why put every sensor on a common 0–1 scale before training a neural network?",
        options=["To save memory",
                 "A network reads magnitude, not meaning — unscaled RPM in the thousands would swamp a 2 mm/s vibration rise that matters far more",
                 "Because 0–1 numbers look tidier",
                 "So the columns fit on the screen"],
        answer=1,
        why="A neural network cannot tell a big number from an important one. Scaling lets importance be learned from the data, not handed to whichever sensor happens to use large units."),
    'split': dict(
        q="Why must the model be scored on machines it never trained on?",
        options=["To use up the spare data",
                 "A model tested on its training records just recites what it memorised and proves nothing about the next machine",
                 "Because the test set is cleaner",
                 "It is unnecessary when accuracy is already high"],
        answer=1,
        why="Never test someone on the exact work they practised on. Only a score on sealed, unseen machines says anything about the plant tomorrow — it is what makes the reliability audit mean anything."),
    'ml-baseline': dict(
        q="What do you give the Random Forest, and what does it work out for itself?",
        options=["The exact failure thresholds; it just applies them",
                 "The named factors (temperature, vibration, oil, runtime…) plus 1,200 outcomes; it learns the weighting to a failure risk itself",
                 "A recording of the machine; it listens for faults",
                 "Nothing — it guesses randomly"],
        answer=1,
        why="You state the factors an engineer already named at inspection, not the thresholds. Given seven named columns and the outcomes, the model learns the weighted interactions no engineer can fully articulate."),
    'signal-problem': dict(
        q="In a 2,048-sample vibration window, where is the bearing fault?",
        options=["In one specific sample",
                 "In a sample labelled 'fault'",
                 "In a faint periodic pattern spread across thousands of samples, named by no single number",
                 "It is not present in the raw signal at all"],
        answer=2,
        why="The fault is a pattern, not a value. Nothing in the raw window is pre-named — unlike the gauges an engineer had already named — so there is nothing to weigh directly."),
    'handmade': dict(
        q="Why does alarming on the waveform's RMS level fail to catch early bearing faults?",
        options=["RMS is impossible to compute",
                 "An early fault barely lifts the RMS while its shape changes completely — one number cannot separate it from a merely rough healthy machine",
                 "The accelerometer is broken",
                 "RMS is always exactly zero"],
        answer=1,
        why="Reducing a waveform to one hand-picked number discards the shape that distinguishes an early fault. Every hand-made feature is a brittle rule you must maintain, keeping only a sliver of the signal."),
    'why-dl': dict(
        q="When does deep learning earn its place over machine learning?",
        options=["Whenever there is a lot of data",
                 "When nobody can name the features — as with the raw vibration signal, where you supply labelled examples and the network learns what separates them",
                 "Always; DL beats ML at everything",
                 "Only when the model must run fast"],
        answer=1,
        why="DL does not dig deeper into named readings — ML already handles those. It works where there are no named features at all, learning them from healthy and faulty examples."),
    'engineer-brain': dict(
        q="An engineer weighs vibration heavily, oil moderately, ambient temperature barely, sums it, and makes one call. That process is essentially…",
        options=["A spreadsheet formula",
                 "A single artificial neuron",
                 "A database lookup",
                 "A random guess"],
        answer=1,
        why="Weigh each input, sum, decide — that is exactly one neuron. The weights are what the engineer's years of experience become."),
    'neuron': dict(
        q="What is a neuron's forward step, z = w·x + b?",
        options=["A weighted sum of the inputs plus a bias offset",
                 "The average of the inputs",
                 "The largest single reading",
                 "A random number"],
        answer=0,
        why="Each reading is multiplied by its weight, the products are summed, and a bias is added for how cautious the machine's policy is. This single computation is what every layer repeats."),
    'activation': dict(
        q="Why pass the neuron's score z through a non-linear activation like sigmoid?",
        options=["To slow training down",
                 "It turns the raw score into a smooth 0–1 probability of failure and lets stacked neurons bend — without it the network stays a straight line",
                 "To round the score to an integer",
                 "It has no real effect"],
        answer=1,
        why="A hard cut-off flips on one noisy reading; sigmoid ramps up smoothly as evidence builds. And without a non-linearity, stacking neurons learns nothing curved."),
    'learning-loop': dict(
        q="Stripped of terminology, what is 'learning'?",
        options=["Memorising every example perfectly",
                 "Predict, measure the error against what actually happened, adjust to be less wrong, and repeat",
                 "Copying another model",
                 "Adding more sensors"],
        answer=1,
        why="Done by hand this loop takes a career and lives in one person's head. Training runs the same loop thousands of times a second, and the lesson lives in the weights."),
    'gradient-descent': dict(
        q="During gradient descent, what does the learning rate (step size) control?",
        options=["How many sensors are used",
                 "How big a step each weight takes downhill — too big overshoots into false alarms, too small never settles",
                 "The number of layers",
                 "The colour of the loss curve"],
        answer=1,
        why="The gradient always points to the weights that reduce error fastest; the art is the step size. Too large and it bounces past the minimum; too small and it crawls."),
    'network': dict(
        q="Why stack neurons into layers rather than use a single one?",
        options=["To use more memory",
                 "One neuron can only split the world with a straight line; layers compose simple signals into the curved patterns real failures make",
                 "Layers make the maths simpler",
                 "There is no reason; one neuron always suffices"],
        answer=1,
        why="Hot with high vibration means one thing; hot with low vibration another. Depth lets the network hold decisions one straight-line neuron cannot, exactly as a reliability team layers expertise."),
    'training': dict(
        q="Training loss keeps falling on the training machines. Why not simply run many more epochs?",
        options=["The model gets steadily better forever",
                 "On the same machines it starts memorising them — overfitting — while held-out error stops improving",
                 "The sensors recalibrate",
                 "The loss becomes negative"],
        answer=1,
        why="Too many epochs on the same records only memorise them — brilliant on the training set, useless on a new machine. You stop when the held-out loss stops falling."),
    'cnn-journey': dict(
        q="Where do a CNN's fault-detecting filters come from?",
        options=["An engineer writes each filter by hand",
                 "They are learned from labelled vibration windows during training",
                 "They are fixed and identical in every CNN",
                 "They come preset from the accelerometer"],
        answer=1,
        why="The CNN slides small learned filters along the signal, each firing on a pattern — an impact, a harmonic — wherever it occurs. The features are learned from examples, the rule the hand-made threshold could not be."),
    'lstm': dict(
        q="Why can an LSTM answer 'how long have we got' when the tabular model cannot?",
        options=["The LSTM uses more sensors",
                 "It reads readings in order and carries a memory of what came before, so it separates a rising trend from a steady one and estimates remaining useful life",
                 "It simply runs faster",
                 "It ignores the history entirely"],
        answer=1,
        why="A single reading barely tells you anything; the trend does. The tabular model sees one row with no memory of yesterday, so it cannot tell a two-week climb from a flat rough-runner."),
    'audit': dict(
        q="On the confusion matrix, which outcome is the costly one, and why not quote accuracy alone?",
        options=["False alarms; they waste a callout",
                 "Called healthy but it failed — the miss that becomes unplanned downtime; a model calling everything healthy scores high on accuracy yet catches no failures",
                 "Called failing and it failed; it means the model works",
                 "There is no costly box"],
        answer=1,
        why="Accuracy hides the false-negative box. That missed failure is the whole reason the system exists, so it must be reported separately from a plausible-looking overall score."),
    'proof': dict(
        q="What did comparing ML and DL on the two record types actually prove?",
        options=["Deep learning always wins",
                 "On the seven named readings ML and DL perform about the same; DL earns its place only on the raw waveform, where no one can name the features",
                 "Machine learning always wins",
                 "Neither works on rotating machinery"],
        answer=1,
        why="When an engineer has named the features, use ML — simpler, faster, easier to defend. When nobody can, as with the 2,048 unnamed samples, deep learning is the option that works."),
    'fusion-engine': dict(
        q="Why fuse the readings, the CNN's signal verdict, the trend and asset context instead of alarming on each feed?",
        options=["To reduce the number of sensors",
                 "Each feed alone is close to noise and a system that alarms on any one gets switched off; fused with asset criticality they become one prioritized work order",
                 "Fusion makes each model more accurate on its own",
                 "So that only one model has to run"],
        answer=1,
        why="A hot day, one rough window, or a rising trend on a non-critical spare can each trip a single feed. Together on a critical asset — rising risk, a bearing-fault pattern, a two-week countdown — they are one work order with a deadline."),
    'pipeline': dict(
        q="Where does the value of the predictive-maintenance system actually live?",
        options=["In the single best model",
                 "In the whole pipeline — ingest, clean, prepare, model, evaluate, fuse, serve — because a break anywhere prevents no failure",
                 "In having the most sensors",
                 "In the dashboard's colours"],
        answer=1,
        why="A perfect model on dirty data, or a great prediction nobody acts on, saves no downtime. Any single stage done well is worthless if the chain breaks."),
    'dashboard': dict(
        q="How does the dashboard turn the models into a business case the plant manager can act on?",
        options=["By never repairing anything",
                 "By ranking machines by how soon they need attention and showing the unplanned downtime each early catch avoids over run-to-failure",
                 "By reducing the fleet size",
                 "By inspecting every machine every week"],
        answer=1,
        why="None of the engineering matters to the business until it is a number a manager can act on — which machine, how urgent, and how many machine-hours of downtime were avoided this month."),
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
# A vertical spine of the plant's phases. Every node opens that learning page.
# ============================================================================
def mind_map(style):
    fig = go.Figure()
    n = len(PHASES)
    ROW_H = 2.05                       # vertical spacing between phase rows
    ys = {i: (n - 1 - i) * ROW_H for i in range(n)}

    # left spine: short amber arrows linking one phase down to the next
    for i in range(n - 1):
        fig.add_annotation(x=0, y=ys[i + 1] + 0.72, ax=0, ay=ys[i] - 0.72,
                           xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1.1,
                           arrowwidth=2, arrowcolor=CIVIL, text="")

    GAP = 3.9                          # horizontal spacing between step nodes
    X0 = 3.4                           # x of the first node in every row
    maxk = max(len(_phase_steps(pi)) for pi in range(n))

    sx, sy, stext, scustom, shover = [], [], [], [], []
    for pi, (pname, pdesc) in enumerate(PHASES):
        kids = _phase_steps(pi)
        # one connector line from the badge out to the last node in the row
        last_x = X0 + (len(kids) - 1) * GAP
        fig.add_shape(type="line", x0=0.45, y0=ys[pi], x1=last_x, y1=ys[pi],
                      line=dict(color="#2b323c", width=1.5), layer="below")
        fig.add_annotation(x=0, y=ys[pi], text=f"<b>{pi+1}</b>", showarrow=False,
                           font=dict(size=13, color=BG),
                           bgcolor=CIVIL, bordercolor=CIVIL, borderpad=6, borderwidth=2)
        fig.add_annotation(x=-0.7, y=ys[pi] + 0.22, text=f"<b>{pname}</b>", showarrow=False,
                           xanchor="right", font=dict(size=13, color=CIVIL))
        fig.add_annotation(x=-0.7, y=ys[pi] - 0.42, text=_wrap(pdesc, 26), showarrow=False,
                           xanchor="right", align="right", font=dict(size=10, color=MUTED))
        for k, s in enumerate(kids):
            sx.append(X0 + k * GAP)
            sy.append(ys[pi])
            stext.append(_wrap(f"{s['civil_icon']} {s['short']}", 15))
            scustom.append(s["id"])
            shover.append(f"<b>{s['civil']}</b><br>"
                          f"<span style='color:{AISIDE}'>= {s['ai']}</span><br>"
                          f"<i>click to open</i>")

    fig.add_trace(go.Scatter(
        x=sx, y=sy, mode="markers+text", text=stext, textposition="top center",
        textfont=dict(size=10, color=TEXT), customdata=scustom,
        marker=dict(size=18, color=PANEL, line=dict(color=AISIDE, width=2),
                    symbol="circle"),
        cliponaxis=False,
        hovertemplate="%{hovertext}<extra></extra>", hovertext=shover,
        showlegend=False))

    fig.update_xaxes(visible=False, range=[-7.0, X0 + (maxk - 1) * GAP + 2.4])
    fig.update_yaxes(visible=False, range=[-1.2, (n - 1) * ROW_H + 1.3])
    return style(fig, h=1620)


# ============================================================================
# THE MECHANICAL-ENGINEERING-TO-AI MAPPING
# Left column: the mechanical process. Right column: the AI process.
# ============================================================================
def mapping_figure(style):
    fig = go.Figure()
    n = len(STEPS)
    for i, s in enumerate(STEPS):
        y = (n - 1 - i) * 1.0
        fig.add_shape(type="rect", x0=0, x1=3.6, y0=y - 0.36, y1=y + 0.36,
                      line=dict(color=CIVIL, width=1.2), fillcolor=PANEL, layer="below")
        fig.add_annotation(x=0.16, y=y, text=f"{s['civil_icon']} {s['civil']}",
                           showarrow=False, xanchor="left",
                           font=dict(size=11.5, color=TEXT))
        fig.add_annotation(x=4.5, y=y, ax=3.7, ay=y, xref="x", yref="y",
                           axref="x", ayref="y", showarrow=True, arrowhead=2,
                           arrowsize=1.1, arrowwidth=1.6, arrowcolor=MUTED, text="")
        fig.add_shape(type="rect", x0=4.6, x1=8.2, y0=y - 0.36, y1=y + 0.36,
                      line=dict(color=AISIDE, width=1.2), fillcolor=PANEL, layer="below")
        fig.add_annotation(x=4.76, y=y, text=f"{s['ai_icon']} {s['ai']}",
                           showarrow=False, xanchor="left",
                           font=dict(size=11.5, color=TEXT))
        fig.add_annotation(x=8.4, y=y, text=f"{s['phase']+1}", showarrow=False,
                           xanchor="left", font=dict(size=9, color="#3f4650"))

    fig.add_annotation(x=0, y=n - 0.35, text="<b>MECHANICAL ENGINEERING PROCESS</b>",
                       showarrow=False, xanchor="left", font=dict(size=12, color=CIVIL))
    fig.add_annotation(x=4.6, y=n - 0.35, text="<b>THE AI PROCESS THAT SOLVES IT</b>",
                       showarrow=False, xanchor="left", font=dict(size=12, color=AISIDE))

    fig.update_xaxes(visible=False, range=[-0.2, 9.0])
    fig.update_yaxes(visible=False, range=[-0.8, n + 0.2])
    return style(fig, h=1100)


# ============================================================================
# THE OPENING PAGE
# ============================================================================
def render_start(style, animate):
    st.markdown("# 🏭  A Reliability Engineering Problem")
    st.markdown(
        f"<div style='color:{MUTED};font-size:17px;line-height:1.6'>"
        f"Keeping forty machines running is more than one engineer can watch every minute. "
        f"AI shows up here because the job needs it.</div>",
        unsafe_allow_html=True)
    st.divider()

    # ---------------------------------------------- SECTION 1: THE PROBLEM
    st.markdown(f"## <span style='color:{CIVIL}'>1 · The engineering problem</span>",
                unsafe_allow_html=True)
    st.markdown("""
A plant runs forty machines across three shifts. A bearing does not fail all at once — it heats up,
vibrates and pulls more current for days first. One engineer can only walk the rounds a few times a
shift and cannot watch forty machines every minute in between, so a machine can drift from healthy to
failed between rounds with nobody watching the early signs.
    """)
    st.divider()

    # ---------------------------------------------- SECTION 2: THE GOAL
    st.markdown(f"## <span style='color:{CIVIL}'>2 · What we are going to build</span>",
                unsafe_allow_html=True)
    st.markdown("An **intelligent predictive maintenance system**. Concretely, four parts:")
    c1, c2, c3, c4 = st.columns(4)
    for col, (icon, title, body) in zip(
        (c1, c2, c3, c4),
        [("📡", "Sensors read the condition",
          "Temperature, pressure, vibration, speed, current, oil quality, runtime. Sampled continuously, "
          "on every machine, between rounds."),
         ("🌊", "Signals capture the fault",
          "The raw accelerometer trace, where a bearing fault hides in the shape of the waveform - not in "
          "any single gauge reading."),
         ("🔗", "AI combines both",
          "Neither stream decides alone. A rising reading may be a hot day; a signal pattern on a critical "
          "asset with a two-week trend is a work order."),
         ("🔔", "The engineer gets an alert",
          "Not a dashboard nobody reads. A ranked, actionable call: pump P-12, bearing fault, act within "
          "two weeks.")]):
        with col:
            st.markdown(
                f"<div style='background:{PANEL};border-radius:10px;padding:14px;height:100%;"
                f"border-top:3px solid {CIVIL}'><div style='font-size:26px'>{icon}</div>"
                f"<b style='color:{TEXT}'>{title}</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>{body}</span></div>",
                unsafe_allow_html=True)
    st.write("")
    st.markdown(
        f"<div style='border-left:3px solid {GREEN};padding:8px 0 8px 16px;font-size:16px;"
        f"color:{TEXT};line-height:1.65'><b>The engineer stays in charge.</b> The system does not "
        f"replace anyone or stop a machine by itself. It simply keeps watching every machine, all shift, "
        f"without a break — easing the part one person cannot carry alone, for a <b>more reliable</b> "
        f"plant.</div>", unsafe_allow_html=True)
    st.divider()

    # ---------------------------------------------- SECTION 3: MIND MAP
    st.markdown(f"## <span style='color:{CIVIL}'>3 · The engineering workflow</span>",
                unsafe_allow_html=True)
    st.markdown(
        f"<div style='color:{MUTED};font-size:15px;line-height:1.6'>"
        f"<b>One predictive-maintenance project</b>, from commissioning the sensors to a served work "
        f"order and the downtime it avoids — {len(PHASES)} phases, in the order a real project runs them. "
        f"Every <b style='color:{CIVIL}'>amber node</b> is a mechanical-engineering activity. Every "
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
    st.markdown(f"## <span style='color:{AISIDE}'>4 · Engineering → AI, the whole map</span>",
                unsafe_allow_html=True)
    st.markdown(
        f"<div style='color:{MUTED};font-size:15px;line-height:1.6'><b>Every AI concept here "
        f"is a maintenance activity you already understand</b> — the same thing, named "
        f"differently by a different profession. Read down the amber column and you have described a "
        f"predictive-maintenance project. Read down the cyan column and you have described a deep "
        f"learning pipeline. They are the same column.</div>", unsafe_allow_html=True)
    st.write("")
    st.plotly_chart(mapping_figure(style), use_container_width=True, key="mapping")

    st.markdown(
        f"<div style='border-left:3px solid {AISIDE};padding:8px 0 8px 16px;font-size:16px;"
        f"color:{TEXT};line-height:1.65'>Each AI concept here shows up because the maintenance work ran "
        f"into something one engineer could not do by hand. Only then does it get a technical "
        f"name.</div>", unsafe_allow_html=True)
    st.write("")

    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("▶  Start: walk onto the floor", use_container_width=True,
                     type="primary"):
            goto("floor")
    with c2:
        st.caption(f"{len(PHASES)} phases · {len(STEPS)} steps · one predictive-maintenance project. "
                   "Every step opens with the plant activity, then the AI it becomes.")
