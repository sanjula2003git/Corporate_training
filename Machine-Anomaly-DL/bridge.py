"""
bridge.py — the Maintenance-Engineering -> AI teaching content.
===============================================================
All the machinery lives in scaffold.py. This module only declares WHAT this
project teaches: its phases, its steps, its quiz and its opening page. Text is
short on purpose — the visuals carry the page.

COLOR IS A TEACHING DEVICE. Amber is the machine, cyan is the AI, violet is the
technical process.
"""
import sys
import scaffold

THEME = dict(
    title="AI for Unusual Machine Behaviour",
    icon="📉",
    dwg="CBM-VIB-001",
    civil_label="Maintenance Engineering",
    civil_kicker="ON THE MACHINE",
    station="⟨CBM·MACHINE 07⟩",
    rail="RUN",
    start_button="▶  Start: walk up to the machine",
    sidebar_title="A Condition Monitoring Problem",
    sidebar_note="You are trying to catch a fault nobody has labelled, before it becomes a breakdown.",
    backdrop=("repeating-linear-gradient(0deg, rgba(255,255,255,.02) 0 1px,"
              " transparent 1px 34px)"),
)

PHASES = [
    ("The Machine In Service",  "One machine, no spare, and a failure that arrives without warning."),
    ("Instrumenting It",        "An accelerometer, a thermocouple and a current clamp go on."),
    ("The Monitoring Log",      "Months of hourly readings land, and get checked."),
    ("Preparing The Data",      "Dead channels out, every channel scaled, and normal set aside."),
    ("The Rulebook",            "Every classical method, tried honestly, until each one runs out."),
    ("How A Machine Learns",    "A neuron, a threshold, a loop — before any network is built."),
    ("The Autoencoder",         "Learn normal so well that abnormal cannot be rebuilt."),
    ("Reading The Spectrum",    "The same idea on 512 frequency bins, and which one moved."),
    ("The Monitoring Audit",    "Every alarm checked on readings the model never saw."),
    ("Living With It",          "Normal moves, and warning is only worth what it buys."),
    ("The System",              "One work order, the whole pipeline, and what it is worth."),
]

STEPS = [
# ---------------------------------------------- PHASE 1
dict(
    id='breakdown', phase=0,
    civil='A Machine That Stops Without Warning', ai='Why Monitoring Needs AI',
    civil_icon='💥', ai_icon='🤖',
    tech='Time to failure vs time to the next inspection',
    civil_bullets=['No spare', 'Monthly route', 'Failure is sudden'],
    ai_bullets=['Listen every hour', 'Learn what normal is', 'Flag the drift early'],
    site="""A critical machine runs continuously. Condition monitoring is a monthly route: an analyst walks
round with a meter, writes down an overall vibration level, and moves on.""",
    challenge="""A bearing spall can go from first crack to seizure in under three weeks. A monthly route can
miss the whole event, and the overall level barely moves until it is far too late.""",
    ai_link="""The gap between reading and failure has to close. That means listening continuously and knowing
what this machine's normal sounds like — which is a watch no analyst can keep on every machine.""",
    notebook="""Section 1. The failure curve, and where the monthly route lands on it.""",
    contributes="""The requirement. If the fault is still found by a breakdown, this failed.""",
    takeaway="""Failure is fast and inspection is slow. Everything here exists to close that gap.""",
),
# ---------------------------------------------- PHASE 2
dict(
    id='sensors', phase=1,
    civil='Where The Sensors Sit', ai='Data Collection',
    civil_icon='📡', ai_icon='🗄️',
    tech='One burst → eight named channels + a 512-bin spectrum',
    civil_bullets=['Accelerometer', 'Thermocouple', 'Current clamp'],
    ai_bullets=['Eight features', 'One spectrum', 'Two kinds of record'],
    site="""An accelerometer on the bearing housing, a thermocouple in it, and a clamp on the motor supply.
Every hour the analyser records a short burst of vibration and reduces it to a few numbers.""",
    challenge="""That reduction throws almost everything away. 2,048 samples become eight values, and the
evidence for a chipped gear tooth lives in the part that was discarded.""",
    ai_link="""Keep both records: the eight named channels an engineer can defend, and the raw spectrum nobody
can name. The whole course is about what each one can and cannot do.""",
    notebook="""Section 2. Build a burst from physics, then its spectrum, then the eight features.""",
    contributes="""The unit of learning, and the fork between ML and DL.""",
    takeaway="""Eight numbers are convenient. The spectrum is complete. They are not the same record.""",
),
# ---------------------------------------------- PHASE 3
dict(
    id='load', phase=2,
    civil='The Monitoring Log Arrives', ai='Loading The Dataset',
    civil_icon='📥', ai_icon='🐼',
    tech='CSV + spectra array, 1,400 hourly readings',
    civil_bullets=['Analyser export', 'One row per reading', 'Months of running'],
    ai_bullets=['read_csv', 'shape and dtypes', 'First look'],
    site="""The analyser exports months of hourly readings: one row per measurement, plus the averaged
spectrum each row came from.""",
    challenge="""An export is not a dataset. Channels drop out, a detached accelerometer keeps writing, and the
same reading appears twice after a resync.""",
    ai_link="""Loading it is the first step: shape, column types, and how often each state actually appears —
which is the first hint that this problem is unbalanced.""",
    notebook="""Section 3. `pd.read_csv`, `np.load` for the spectra, `.head()`.""",
    contributes="""The dataset every later step reads from.""",
    takeaway="""The export is raw material. Loading it is where the data work starts.""",
),
dict(
    id='inspect', phase=2,
    civil='Sensor Health Check', ai='Data Inspection',
    civil_icon='🔍', ai_icon='📊',
    tech='Count gaps, dead channels and impossible values',
    civil_bullets=['Is it still glued on?', 'Is the thermocouple open?', 'Is the clamp saturated?'],
    ai_bullets=['isna().sum()', 'describe()', 'duplicated()'],
    site="""Before trusting months of readings, check the instruments. A dead sensor does not report
"dead" — it reports a number.""",
    challenge="""An open thermocouple reads about −50 °C. A detached accelerometer reads 0.0 mm/s. A saturated
clamp reads full scale. All three are valid numbers and all three are lies.""",
    ai_link="""This matters more here than anywhere else in the series: an anomaly detector's whole job is to
flag what looks unlike normal, and **a broken sensor is the most unusual thing in the file**.""",
    notebook="""Section 4. `.isna().sum()`, `.describe()`, `.duplicated()`.""",
    contributes="""The fault list the cleaning step works from.""",
    takeaway="""Leave a dead sensor in and the monitor will confidently report instrument faults forever.""",
),
# ---------------------------------------------- PHASE 4
dict(
    id='clean', phase=3,
    civil='Dead Channels And Dropouts', ai='Data Cleaning',
    civil_icon='🧹', ai_icon='🧼',
    tech='Drop duplicates, null the impossible, fill with the median',
    civil_bullets=['Repair the channel', 'Keep the reading', 'Never average a fault'],
    ai_bullets=['drop_duplicates', 'Mask impossibles', 'fillna(median)'],
    site="""A faulty channel is repaired or discounted before its readings reach a report. Nobody averages a
detached accelerometer into a trend and then defends the conclusion.""",
    challenge="""Deleting every affected row throws away good readings from the other seven channels. Keeping
them poisons the baseline that everything downstream is measured against.""",
    ai_link="""Cleaning does both: drop duplicates, mark impossible values as missing rather than deleting the
row, then fill with the channel's median — a value outliers cannot move.""",
    notebook="""Section 5. `drop_duplicates`, mask the impossible, `fillna(median)`.""",
    contributes="""A dataset where every remaining number is physically possible.""",
    takeaway="""Repair the channel, not the reading: mark the impossible, fill with the median.""",
),
dict(
    id='normalize', phase=3,
    civil='Common Units', ai='Normalization',
    civil_icon='📐', ai_icon='⚖️',
    tech='Standardise every channel against healthy',
    civil_bullets=['mm/s vs °C vs A', 'Different magnitudes', 'One channel wins'],
    ai_bullets=['Rescale', 'Units disappear', 'Data decides weight'],
    site="""The channels do not share a scale. Current runs to 90 A, temperature sits near 45 °C, RMS
velocity is under 3 mm/s, kurtosis is a bare number.""",
    challenge="""A rebuild error summed across raw channels is dominated by current, purely because its numbers
are bigger. The channel that actually moves first would never be noticed.""",
    ai_link="""Scaling every channel against **healthy** readings puts the error in units of "healthy standard
deviations", which is what a vibration analyst already thinks in.""",
    notebook="""Section 6. Fit the scaler on healthy rows only, then transform everything.""",
    contributes="""Comparable channels, so the rebuild error means something.""",
    takeaway="""Scale against normal, and the error is measured in standard deviations of normal.""",
),
dict(
    id='split', phase=3,
    civil='Train On Normal Only', ai='The Unsupervised Split',
    civil_icon='🗂️', ai_icon='✂️',
    tech='Healthy rows train; everything is tested',
    civil_bullets=['Plenty of healthy hours', 'Very few faults', 'Some never seen'],
    ai_bullets=['Fit on normal', 'Score everything', 'No fault labels used'],
    site="""A working machine is healthy nearly all the time. Months of running give thousands of healthy
readings and a handful of faulty ones — and no guarantee that the next fault resembles any of them.""",
    challenge="""That imbalance breaks supervised learning. You cannot train a classifier on six examples of a
fault, and you certainly cannot train it on a fault that has not happened yet.""",
    ai_link="""So invert the problem. Train only on **normal**, and treat anything the model cannot reproduce as
suspicious. No fault labels are used anywhere in training.""",
    notebook="""Section 7. Split the healthy rows; keep every faulty row for the test set.""",
    contributes="""The sealed set the audit runs on, and the reason this project is unsupervised.""",
    takeaway="""Learn normal, not faults — because the next fault is one you have never seen.""",
),
# ---------------------------------------------- PHASE 5
dict(
    id='control-chart', phase=4,
    civil='The 3-Sigma Limit', ai='The Statistical Baseline',
    civil_icon='📏', ai_icon='📈',
    tech='mean ± 3σ on one channel',
    civil_bullets=['One number', 'One limit', 'Decades of use'],
    ai_bullets=['Fit on healthy', 'Flag the outliers', 'Honest baseline'],
    site="""The classical method, and it works: take overall RMS velocity, compute its mean and spread on
healthy running, and alarm above three standard deviations. ISO 10816 is built on this idea.""",
    challenge="""One channel at a time is one question at a time. A fault that moves two channels a little,
and neither past its own limit, passes every chart on the wall.""",
    ai_link="""This is the baseline the rest of the course has to beat, and it must be tried properly before it
is dismissed. Most of the time, it is enough.""",
    notebook="""Section 8. Control limits from healthy readings, then scored on everything.""",
    contributes="""The honest baseline. Anything more complex has to earn its place against it.""",
    takeaway="""A control chart asks one question at a time — which is exactly when it fails.""",
),
dict(
    id='isolation-forest', phase=4,
    civil='Isolating The Odd One Out', ai='Isolation Forest',
    civil_icon='🌲', ai_icon='🧭',
    tech='random splits; anomalies isolate in fewer cuts',
    civil_bullets=['All channels at once', 'No fault labels', 'Still a shallow view'],
    ai_bullets=['Random splits', 'Short path = odd', 'Unsupervised'],
    site="""Eight channels move together on a real machine. The next step is to look at all of them at once
instead of one chart at a time.""",
    challenge="""A multivariate limit is hard to draw by hand and harder to defend. Nobody can picture an
eight-dimensional envelope, let alone justify one to a reliability review.""",
    ai_link="""An isolation forest cuts the data at random and asks how few cuts it takes to isolate a point.
Odd points fall out quickly. It uses no labels, and it handles all eight channels together.""",
    notebook="""Section 9. `IsolationForest`, fitted on healthy readings only.""",
    contributes="""The multivariate baseline, and a real improvement on the control chart.""",
    takeaway="""Looking at all channels at once beats looking at one — but it is still only the eight.""",
),
dict(
    id='classifier-wall', phase=4,
    civil='The Fault It Was Never Taught', ai='Why Supervised Learning Ends',
    civil_icon='🚧', ai_icon='🧱',
    tech='train on four states, test on a fifth',
    civil_bullets=['A new failure mode', 'No examples of it', 'It still has to be caught'],
    ai_bullets=['Confident wrong answers', 'No "none of these"', 'The wall'],
    site="""Train a perfectly good classifier on the faults the plant has already seen — imbalance,
misalignment, bearing — and it performs well on all of them.""",
    challenge="""Then a chipped gear tooth appears, which was never in the training set. The classifier has no
option for "something else", so it confidently assigns the nearest label it knows.""",
    ai_link="""That is the wall. A supervised model can only return a class it was taught. Catching the unknown
means asking a different question: not *which fault is this?* but *is this normal at all?*""",
    notebook="""Section 10. Train on four states, score the fifth, read the confusion.""",
    contributes="""The failure that justifies the autoencoder.""",
    takeaway="""A classifier cannot say "I have never seen this". An anomaly detector only says that.""",
),
# ---------------------------------------------- PHASE 6
dict(
    id='analyst-brain', phase=5,
    civil="How An Analyst Decides", ai='The Neuron, Informally',
    civil_icon='👷', ai_icon='💡',
    tech='Weigh the signals, add them, decide',
    civil_bullets=['Several signals at once', 'Some matter more', 'One call'],
    ai_bullets=['Weights', 'A sum', 'A threshold'],
    site="""A vibration analyst weighs several things at once — the level, how spiky the trace is, the housing
temperature, how long since the last overhaul — and calls it healthy or not.""",
    challenge="""That judgement is fast and good, but it lives in one head, works one machine at a time, and
cannot be applied to forty thousand logged readings overnight.""",
    ai_link="""Write it down and it is arithmetic: multiply each signal by how much it matters, add the
results, act if the total clears a threshold. That is a neuron.""",
    notebook="""Section 11. The weighted-sum decision, before any terminology.""",
    contributes="""The intuition every later network is built on.""",
    takeaway="""A neuron is an analyst's judgement written as arithmetic: weigh, add, decide.""",
),
dict(
    id='neuron', phase=5,
    civil='Weighing The Signals', ai='The Neuron',
    civil_icon='⚖️', ai_icon='🔵',
    tech='z = w·x + b',
    civil_bullets=['Kurtosis matters a lot', 'Current matters little', 'Experience = weights'],
    ai_bullets=['Weights are learned', 'Bias sets the baseline', 'Traceable to data'],
    site="""Give each channel a weight. Kurtosis matters a great deal for an impacting bearing. Motor current
matters little. An analyst's experience is exactly that set of weights.""",
    challenge="""Those weights are guesses, and every analyst guesses differently. Nobody can defend "kurtosis
counts 3.4 times more than temperature" from experience alone.""",
    ai_link="""A neuron computes a weighted sum plus a bias, and nobody chooses the weights — they are learned,
so the model's opinion is traceable to data rather than to seniority.""",
    notebook="""Section 11. `z = w·x + b`, computed by hand.""",
    contributes="""The single unit every network here is built from.""",
    takeaway="""A neuron is a weighted sum plus a bias, and the weights come from the data.""",
),
dict(
    id='activation', phase=5,
    civil='The Alarm Threshold', ai='Activation Function',
    civil_icon='🚨', ai_icon='📉',
    tech='sigmoid and ReLU',
    civil_bullets=['Acceptable or not', 'A hard limit is brittle', 'Condition is graded'],
    ai_bullets=['Sigmoid → 0..1', 'ReLU passes positives', 'Smooth = trainable'],
    site="""An alarm reports a state, not a weighted sum. Somewhere the continuous signal has to become a
decision.""",
    challenge="""A hard on/off limit is brittle. A reading a hair under is treated as perfectly fine and one a
hair over triggers a callout. Machine condition does not step like that.""",
    ai_link="""An activation function does the same job smoothly, and that smoothness is also what makes the
network trainable at all.""",
    notebook="""Section 12. Plot sigmoid and ReLU, and pass `z` through both.""",
    contributes="""The step that turns a raw sum into a usable score.""",
    takeaway="""Activation turns a weighted sum into a graded decision instead of a brittle limit.""",
),
dict(
    id='gradient-descent', phase=5,
    civil='Tuning By Trial', ai='Loss & Gradient Descent',
    civil_icon='🎛️', ai_icon='⛰️',
    tech='loss surface, gradient, learning rate',
    civil_bullets=['Change a setting', 'Measure the result', 'Step again'],
    ai_bullets=['Loss = how wrong', 'Gradient = downhill', 'Rate = step size'],
    site="""Commissioning anything is a search: change a setting, measure, keep the change if it helped, step
again in the direction that worked.""",
    challenge="""Step too far and you overshoot and oscillate. Step too small and it takes a week. The step size
is the whole difficulty, and it is usually chosen by feel.""",
    ai_link="""Loss measures how wrong the model is; gradient descent steps downhill on it and the learning rate
is the step size. Same overshoot, same reason.""",
    notebook="""Section 13. A loss surface, and the descent path at three learning rates.""",
    contributes="""How the weights actually change during training.""",
    takeaway="""Training is commissioning by search: step downhill on the error, and mind the step size.""",
),
# ---------------------------------------------- PHASE 7
dict(
    id='autoencoder', phase=6,
    civil='The Hourglass', ai='The Autoencoder',
    civil_icon='⏳', ai_icon='🕸️',
    tech='8 → 3 → 8, trained to reproduce its own input',
    civil_bullets=['Learn normal', 'Squeeze it', 'Rebuild it'],
    ai_bullets=['Bottleneck', 'Rebuild error', 'No fault labels'],
    site="""An experienced analyst can sketch what a healthy trace from this machine looks like. That sketch
is compression: everything essential about normal, in far less than eight numbers.""",
    challenge="""Nobody can write that sketch down as a formula, and it is different for every machine, mounting
and speed.""",
    ai_link="""An autoencoder squeezes eight channels through three, then rebuilds them, and is trained only on
healthy readings. It becomes very good at rebuilding normal — and bad at anything else. The rebuild
error is the anomaly score, and no fault was ever labelled.""",
    notebook="""Section 14. Build the 8 → 3 → 8 network and train it on healthy rows.""",
    contributes="""The detector that does not need to have seen the fault.""",
    takeaway="""Learn normal so well that abnormal cannot be rebuilt. The failure to rebuild is the alarm.""",
),
dict(
    id='threshold', phase=6,
    civil='Where To Draw The Line', ai='Setting The Threshold',
    civil_icon='📍', ai_icon='🎚️',
    tech='percentile of healthy error vs missed faults',
    civil_bullets=['False alarm costs hours', 'Missed fault costs the machine', 'Not equal'],
    ai_bullets=['Set on healthy only', 'Pick a false-alarm rate', 'Then measure recall'],
    site="""A score is not an alarm. Somebody has to say how high is too high, and that is a business
decision, not a statistical one.""",
    challenge="""A false alarm opens a healthy machine and costs a few hours and a little credibility. Spend
that credibility too often and the alarms get muted — which is how monitoring projects really die.""",
    ai_link="""Set the threshold on **held-out healthy data**, at the false-alarm rate the plant will tolerate,
and only then measure how many real faults it catches. Never the other way round.""",
    notebook="""Section 15. Sweep the percentile and read the two error rates.""",
    contributes="""The alarm level the whole system runs at.""",
    takeaway="""The threshold is chosen from what a false alarm costs, not from what makes the score look good.""",
),
# ---------------------------------------------- PHASE 8
dict(
    id='spectrum-ae', phase=7,
    civil='Rebuilding The Spectrum', ai='The Same Idea, 512 Inputs',
    civil_icon='🌊', ai_icon='🧩',
    tech='512 bins → 16 → 512, per-bin standardised',
    civil_bullets=['The eight numbers missed it', 'The spectrum did not', 'Nothing was named'],
    ai_bullets=['Same architecture', 'Wider input', 'Learned features'],
    site="""The chipped gear tooth barely moves overall RMS — it is tonal, not impulsive, and it carries very
little energy. On the eight channels it is close to invisible.""",
    challenge="""In the spectrum it is obvious to an analyst: the mesh tone grows and picks up sidebands. But
there is no column called "mesh tone", only 512 unnamed bins.""",
    ai_link="""Point the same autoencoder at the spectrum. Standardise each bin against healthy first, so a new
peak in a normally quiet bin is not drowned by the naturally noisy ones.""",
    notebook="""Section 16. Log-magnitude spectra, per-bin scaling, then a 512 → 16 → 512 autoencoder.""",
    contributes="""The detector that catches the fault the eight features cannot.""",
    takeaway="""The features an engineer names discard the evidence. The spectrum keeps it.""",
),
dict(
    id='which-frequency', phase=7,
    civil='Reading The Error Spectrum', ai='Explaining The Score',
    civil_icon='🔎', ai_icon='🗺️',
    tech='per-bin rebuild error → the frequency that moved',
    civil_bullets=['Which frequency?', 'Therefore which part?', 'Raise the work order'],
    ai_bullets=['Error per bin', 'Peak → diagnosis', 'Show the evidence'],
    site="""A score does not get a work order raised. The fitter needs to know which component, and a
vibration analyst identifies it from the frequency the energy appeared at.""",
    challenge="""The autoencoder returns one number. On its own it says something is wrong and nothing about
what.""",
    ai_link="""The rebuild error is per bin. Plot it against frequency and the peak names the fault: shaft
speed is imbalance, twice shaft is misalignment, the mesh tone is a gear, a high-frequency ring is a
bearing. That is the location and the evidence together.""",
    notebook="""Section 17. Per-bin error, and the frequency map that reads it.""",
    contributes="""The diagnosis that makes the alert actionable.""",
    takeaway="""The frequency that failed to rebuild is the component that is failing.""",
),
# ---------------------------------------------- PHASE 9
dict(
    id='audit', phase=8,
    civil='The Monitoring Audit', ai='Confusion Matrix',
    civil_icon='🧮', ai_icon='✅',
    tech='TP / FP / FN / TN and what each costs',
    civil_bullets=['Predicted vs actual', 'On sealed readings', 'Every alarm checked'],
    ai_bullets=['Four outcomes', 'False alarm ≠ miss', 'Recall matters'],
    site="""Every alarm is audited against what the machine actually turned out to be, on readings the model
was never allowed to see.""",
    challenge="""A single accuracy figure hides the thing that matters. Calling everything healthy scores 90% on
a machine that is healthy 90% of the time — and finds nothing.""",
    ai_link="""The confusion matrix separates the four outcomes, and lets the two costs be compared honestly
instead of averaged away.""",
    notebook="""Section 18. Confusion matrix, precision and recall on the sealed set.""",
    contributes="""The honest performance number the project is judged on.""",
    takeaway="""Accuracy hides the costly error; the confusion matrix shows the missed fault.""",
),
dict(
    id='proof', phase=8,
    civil='The Verdict', ai='Every Method, Measured',
    civil_icon='⚔️', ai_icon='🏁',
    tech='control chart vs forest vs classifier vs autoencoder',
    civil_bullets=['Four methods', 'One machine', 'One unseen fault'],
    ai_bullets=['Simple wins where it can', 'Only one catches the unknown', 'Say which and why'],
    site="""Four methods have now been tried on the same machine. Time to state plainly what each can and
cannot do.""",
    challenge="""It is tempting to declare the deep method the winner. On the faults it has seen, the control
chart is faster, cheaper and far easier to defend at a reliability review.""",
    ai_link="""Score all four on the same sealed readings, including the fault none of them was trained on.
The difference is not accuracy in general — it is whether the method can flag something it has never
been shown.""",
    notebook="""Section 19. The comparison table, filled in from measured results.""",
    contributes="""The course's central claim, demonstrated rather than asserted.""",
    takeaway="""Use the simplest method that catches your fault; use the autoencoder for the one you cannot name.""",
),
# ---------------------------------------------- PHASE 10
dict(
    id='drift', phase=9,
    civil='When Normal Moves', ai='Model Drift',
    civil_icon='📆', ai_icon='♻️',
    tech='score over months after an overhaul',
    civil_bullets=['Bearings bed in', 'Seasons change', 'Overhauls reset it'],
    ai_bullets=['Normal is not fixed', 'Rebaseline deliberately', 'Never silently'],
    site="""Normal is not a constant. A rebuilt machine runs differently, new bearings bed in over weeks, and
ambient temperature swings with the seasons.""",
    challenge="""A monitor baselined once will slowly fill with false alarms, and the usual response — raise the
threshold — quietly destroys the sensitivity that justified the project.""",
    ai_link="""Retrain on a fresh window of healthy running after any deliberate change, and log when and why.
A rebaseline is a maintenance action with a date, not a slider somebody nudges.""",
    notebook="""Section 20. Score across months, then rebaseline after the overhaul.""",
    contributes="""The operating procedure that keeps the system alive past year one.""",
    takeaway="""Normal drifts. Rebaseline on purpose, or the threshold gets raised until nothing alarms.""",
),
dict(
    id='lead-time', phase=9,
    civil='Days Of Warning', ai='What Detection Is Worth',
    civil_icon='⏱️', ai_icon='💡',
    tech='first alarm vs failure date',
    civil_bullets=['Order the part', 'Plan the outage', 'Avoid the breakdown'],
    ai_bullets=['Earlier alarm', 'More warning', 'Only if acted on'],
    site="""Warning is only worth what it buys. Fourteen days lets you order a bearing and schedule an outage;
two days means a rushed repair with whatever is in the store.""",
    challenge="""A lower threshold buys days of warning and costs false alarms. The trade cannot be avoided, only
chosen deliberately.""",
    ai_link="""Score a run-to-failure history, take the first sustained alarm, and count the days to failure.
That number — not accuracy — is what the plant actually buys.""",
    notebook="""Section 21. Simulated degradation, first alarm, days of warning per method.""",
    contributes="""The figure the business case is built from.""",
    takeaway="""Lead time, not accuracy, is what condition monitoring is bought for.""",
),
# ---------------------------------------------- PHASE 11
dict(
    id='fusion-engine', phase=10,
    civil='The Work Order', ai='From Score To Action',
    civil_icon='🖥️', ai_icon='🔗',
    tech='score + frequency + lead time → one instruction',
    civil_bullets=['Which machine', 'Which part', 'By when'],
    ai_bullets=['Combine the outputs', 'Rank by severity', 'Attach the evidence'],
    site="""By now each machine produces a score, a frequency that failed to rebuild, and an estimate of how
long there is.""",
    challenge="""Three numbers on three screens is three chances to miss something. A planner needs one ranked
list with a date on it.""",
    ai_link="""Fusion turns them into one work order: the machine, the suspected component from the frequency,
the severity in standard deviations, and the window before failure.""",
    notebook="""Section 22. A rules layer over the model outputs.""",
    contributes="""The product — one screen a planner can act on.""",
    takeaway="""The score says something is wrong; the frequency says what. Fusion issues one work order.""",
),
dict(
    id='pipeline', phase=10,
    civil='The Whole System', ai='The Pipeline',
    civil_icon='🧱', ai_icon='🛤️',
    tech='sensors → data → features + spectrum → autoencoder → work order',
    civil_bullets=['Sensors', 'Models', 'A screen that acts'],
    ai_bullets=['Every stage feeds one', 'Data quality first', 'One recommendation'],
    site="""Step back and the whole system is visible: sensors on the machine, a data path, two detectors and
a screen the planner reads.""",
    challenge="""Every stage depends on the ones before it. A dead channel that survives cleaning becomes a
confident false alarm four stages later.""",
    ai_link="""The pipeline is the engineering drawing of the system: what feeds what, where the two data types
split, and where they come back together.""",
    notebook="""Section 22. The end-to-end run, in one place.""",
    contributes="""The map of everything built so far.""",
    takeaway="""The system is a chain: data quality at the start decides the work order at the end.""",
),
dict(
    id='dashboard', phase=10,
    civil='The Reliability Dashboard', ai='Downtime & Money',
    civil_icon='📉', ai_icon='💷',
    tech='breakdowns avoided, downtime, cost',
    civil_bullets=['Approve a spend', 'Against a saving', 'With a payback'],
    ai_bullets=['Breakdowns avoided', 'Hours of downtime', 'Cost at plant rates'],
    site="""A plant manager does not buy a model. They approve a spend against avoided downtime, with a
payback attached.""",
    challenge="""Monitoring savings are easy to overstate. A warning only saves anything if somebody acts on it,
and only some failure modes are detectable at all.""",
    ai_link="""The dashboard turns the detector's performance into the plant's own units: breakdowns avoided,
hours of downtime, and cost — every figure arithmetic on assumptions the reader can change.""",
    notebook="""Section 23. The business case, computed from the assumptions above.""",
    contributes="""The reason the previous steps get funded.""",
    takeaway="""Monitoring is approved in avoided downtime and money — not in accuracy percentages.""",
),
]

SHORT = {
    "breakdown": "Stops without warning",  "sensors": "Where the sensors sit",
    "load": "The log arrives",            "inspect": "Sensor health check",
    "clean": "Dead channels out",         "normalize": "Common units",
    "split": "Train on normal only",      "control-chart": "The 3σ limit",
    "isolation-forest": "Isolate the odd", "classifier-wall": "The unseen fault",
    "analyst-brain": "Analyst decides",   "neuron": "Weighing signals",
    "activation": "Alarm threshold",      "gradient-descent": "Tuning by trial",
    "autoencoder": "The hourglass",       "threshold": "Where to draw the line",
    "spectrum-ae": "Rebuild the spectrum", "which-frequency": "Which frequency moved",
    "audit": "The monitoring audit",      "proof": "The verdict",
    "drift": "When normal moves",         "lead-time": "Days of warning",
    "fusion-engine": "The work order",    "pipeline": "The whole system",
    "dashboard": "The dashboard",
}
for _s in STEPS:
    _s["short"] = SHORT[_s["id"]]

QUIZ = {
    'breakdown': dict(
        q="Why does a monthly route miss a bearing spall?",
        options=["Routes are always done badly",
                 "The failure develops in under three weeks, and overall level barely moves until the end",
                 "Bearings never fail slowly",
                 "The meter is not accurate enough"],
        answer=1,
        why="The whole event can fit between two inspections, and the summary number moves last."),
    'sensors': dict(
        q="Why keep the spectrum as well as the eight features?",
        options=["It compresses better",
                 "Because reducing 2,048 samples to eight numbers throws away evidence some faults live in",
                 "Because spectra are easier to plot",
                 "The features are always wrong"],
        answer=1,
        why="The gear fault is tonal and low-energy: it is visible in the spectrum and nearly invisible in the summary features."),
    'load': dict(
        q="Why is an analyser export not yet a dataset?",
        options=["Wrong file format",
                 "It contains dropouts, dead sensors and duplicate readings a spreadsheet view will not reveal",
                 "It is too large",
                 "It has no header row"],
        answer=1,
        why="Loading it is only the first step; what is in it still has to be checked."),
    'inspect': dict(
        q="Why does a dead sensor matter more in an anomaly project than anywhere else?",
        options=["It does not — it is the same",
                 "Because the detector flags whatever looks unlike normal, and a broken sensor is the most unusual thing in the file",
                 "Because sensors are expensive",
                 "Because it changes the file size"],
        answer=1,
        why="Leave them in and the monitor spends its life reporting instrument faults with total confidence."),
    'clean': dict(
        q="Why fill a missing reading with the channel's median rather than its mean?",
        options=["It is faster",
                 "The median ignores the extreme faulty values still lurking in the column",
                 "The mean only works on integers",
                 "The median is always larger"],
        answer=1,
        why="A single −50 °C open thermocouple shifts a mean badly. The median barely moves."),
    'normalize': dict(
        q="Why scale each channel against HEALTHY readings specifically?",
        options=["It is quicker to compute",
                 "So the rebuild error is measured in standard deviations of normal — the unit an analyst already thinks in",
                 "Because faults have no variance",
                 "To make the plots symmetrical"],
        answer=1,
        why="Scaling on everything would let the faults define what 'normal spread' means."),
    'split': dict(
        q="Why train on healthy readings only?",
        options=["Healthy data is cheaper",
                 "Because faults are rare and the next one may be a mode that has never occurred — so the model learns normal instead",
                 "Because faults are hard to measure",
                 "To make training faster"],
        answer=1,
        why="You cannot train a classifier on a fault that has not happened yet. You can train on normal."),
    'control-chart': dict(
        q="When does a 3σ control chart fail?",
        options=["Whenever the machine is loaded",
                 "When a fault moves two channels a little, and neither passes its own limit",
                 "It never fails",
                 "Only at night"],
        answer=1,
        why="One chart asks one question. A pattern spread across channels passes all of them."),
    'isolation-forest': dict(
        q="What does an isolation forest add over a control chart?",
        options=["Higher accuracy on one channel",
                 "It looks at all channels together, so a combination that is odd overall is caught even when no single channel is",
                 "It uses fault labels",
                 "It is faster"],
        answer=1,
        why="Multivariate, unsupervised, and no hand-drawn envelope required."),
    'classifier-wall': dict(
        q="A classifier trained on three faults meets a fourth. What does it do?",
        options=["Reports 'unknown'",
                 "Confidently assigns the nearest label it was taught, because it has no other option",
                 "Refuses to predict",
                 "Retrains itself"],
        answer=1,
        why="A supervised model can only return a class it has seen. That is the wall."),
    'analyst-brain': dict(
        q="An analyst weighs level, spikiness and temperature, then calls it. What is that?",
        options=["A confusion matrix",
                 "A neuron: weighted inputs, summed, compared to a threshold",
                 "A convolution",
                 "A train/test split"],
        answer=1,
        why="The neuron is the analyst's rule of thumb written as arithmetic."),
    'neuron': dict(
        q="In z = w·x + b, what does b do?",
        options=["Scales the inputs",
                 "Shifts the baseline, so the neuron can fire without every input being large",
                 "Counts the features",
                 "Selects the activation"],
        answer=1,
        why="The bias sets where the decision sits."),
    'activation': dict(
        q="Why not a hard on/off limit instead of a sigmoid?",
        options=["Sigmoid is faster",
                 "A hard limit treats 'just under' and 'just over' as opposites and gives training no gradient to follow",
                 "Hard limits are not allowed in Python",
                 "Sigmoid uses less memory"],
        answer=1,
        why="The graded output is more honest, and the smoothness is what makes gradient descent possible."),
    'gradient-descent': dict(
        q="The loss oscillates and never settles. Why?",
        options=["Too little data",
                 "The learning rate is too large, so each step overshoots the minimum",
                 "The loss function is wrong",
                 "Too many features"],
        answer=1,
        why="The correction is bigger than the error it is fixing."),
    'autoencoder': dict(
        q="Why is a bottleneck essential to an autoencoder?",
        options=["It makes training faster",
                 "Without it the network could copy its input straight through and learn nothing about normal",
                 "It reduces file size",
                 "It prevents overfitting to the test set"],
        answer=1,
        why="The squeeze forces it to keep only what normal readings have in common."),
    'threshold': dict(
        q="How should the alarm threshold be chosen?",
        options=["Whatever maximises accuracy",
                 "From the false-alarm rate the plant will tolerate, set on held-out healthy data — then measure recall",
                 "Three sigma, always",
                 "Whatever catches every fault"],
        answer=1,
        why="It is a business decision about the cost of a false alarm, not a statistical optimum."),
    'spectrum-ae': dict(
        q="Why does the spectrum autoencoder catch the gear fault when the eight features do not?",
        options=["It has more layers",
                 "Because the fault is a small tonal peak that the summary features average away, but the spectrum keeps",
                 "Because it was shown gear examples",
                 "Because spectra are less noisy"],
        answer=1,
        why="Neither model was shown a gear fault. Only one kept the evidence in its input."),
    'which-frequency': dict(
        q="What does the per-bin rebuild error give you that the score does not?",
        options=["A higher score",
                 "The frequency that failed to rebuild — which names the component",
                 "A faster prediction",
                 "An automatic shutdown"],
        answer=1,
        why="Shaft speed, twice shaft, mesh tone and a high-frequency ring each point at a different part."),
    'audit': dict(
        q="A monitor calls everything healthy and scores 90% accuracy. What is wrong?",
        options=["Nothing — 90% is good",
                 "It never finds a fault, which is the entire point; accuracy hides that",
                 "The test set is too small",
                 "Accuracy should be computed on training data"],
        answer=1,
        why="Recall on the faulty readings is the number that matters."),
    'proof': dict(
        q="What does the four-method comparison actually prove?",
        options=["Deep learning is best",
                 "Simple methods win on faults you have seen; only the autoencoder flags the one nobody trained on",
                 "Control charts are obsolete",
                 "All four are equivalent"],
        answer=1,
        why="The difference is not accuracy in general — it is whether the method can flag the unknown."),
    'drift': dict(
        q="Alarms slowly increase after an overhaul. What is the correct response?",
        options=["Raise the threshold",
                 "Rebaseline deliberately on a fresh window of healthy running, and log when and why",
                 "Ignore them",
                 "Retrain on the alarms"],
        answer=1,
        why="Raising the threshold quietly destroys the sensitivity that justified the project."),
    'lead-time': dict(
        q="Why is lead time reported instead of accuracy?",
        options=["Accuracy is confidential",
                 "Because days of warning is what actually buys the part and schedules the outage",
                 "Because accuracy is always 100%",
                 "Because lead time is easier to compute"],
        answer=1,
        why="A perfectly accurate alarm two hours before failure buys almost nothing."),
    'fusion-engine': dict(
        q="What does fusion add over the raw anomaly score?",
        options=["Higher accuracy",
                 "One ranked work order with the suspected component and a date, instead of a bare number",
                 "Faster inference",
                 "Less storage"],
        answer=1,
        why="The score says something is wrong; the frequency says what; lead time says by when."),
    'pipeline': dict(
        q="Why does a dead channel that survives cleaning matter four stages later?",
        options=["It slows the code",
                 "It does not — the model corrects it",
                 "Because the pipeline is a chain: a bad reading becomes a confident false alarm",
                 "It only affects the plots"],
        answer=2,
        why="Nothing downstream can recover information that was wrong at the source."),
    'dashboard': dict(
        q="Why report avoided downtime rather than model accuracy?",
        options=["Accuracy is confidential",
                 "Because a plant manager approves spend against savings in the plant's own units, with a payback",
                 "Because accuracy was too low",
                 "Because downtime is easier to measure"],
        answer=1,
        why="Every figure on it is arithmetic on assumptions the reader can change."),
}

START = dict(
    project_line="one condition-monitoring project",
    problem="""
A critical machine runs continuously and **there is no spare**. Condition monitoring is a **monthly route**:
somebody walks round with a meter, writes down an overall vibration level, and moves on. But a bearing
spall can go from first crack to seizure in **under three weeks**, and the overall level barely moves until
it is far too late. Worse, the next failure may be a mode this plant has never seen — so there is nothing
to train a classifier on. The job: **catch a fault nobody has labelled, early enough to plan the repair.**
""",
    build_intro="An **unsupervised condition monitor** for the machine. Four parts:",
    cards=[
        ("📡", "Sensors read the machine",
         "An accelerometer on the bearing housing, a thermocouple in it, and a clamp on the motor supply. "
         "Every hour: eight named channels, and the 512-bin spectrum they were reduced from."),
        ("⏳", "The model learns normal",
         "An autoencoder squeezes healthy readings through a bottleneck and rebuilds them. It is never "
         "shown a fault. What it cannot rebuild is, by definition, not normal."),
        ("🔎", "The error names the part",
         "The rebuild error is per frequency bin. Shaft speed means imbalance, twice shaft means "
         "misalignment, the mesh tone means a gear, a high-frequency ring means a bearing."),
        ("🔔", "The planner gets a date",
         "Not a black box. A work order: this machine, this suspected component, this severity, this "
         "many days before it fails — with the evidence shown, so a person decides."),
    ],
    promise="""The analyst stays in charge and stays accountable. The system handles the part one person
cannot do alone: it listens to every machine, every hour, and turns what it hears into days of warning.
The goal is <b>Maintenance Engineer + AI</b> — a machine that reports its own condition before it stops.""",
    map_note="""<b>Every AI concept here is a maintenance activity you already understand</b> — the same
thing, named differently by a different profession. Read down the amber column and you have described a
condition-monitoring programme. Read down the cyan column and you have described an unsupervised deep
learning pipeline. They are the same column.""",
)

# ---- bind the scaffold to this content module ------------------------------
_m = sys.modules[__name__]
BY_ID, ORDER = scaffold.lookups(_m)
inject_css = lambda: scaffold.inject_css(_m)
open_page = lambda stage: scaffold.open_page(_m, stage)
close_page = lambda stage: scaffold.close_page(_m, stage)
render_start = lambda: scaffold.render_start(_m)
route = lambda STAGES, ALIASES=None: scaffold.route(_m, STAGES, ALIASES)
