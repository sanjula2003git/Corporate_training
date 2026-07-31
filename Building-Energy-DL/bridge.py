"""
bridge.py — the Building-Services-Engineering -> AI teaching content.
=====================================================================
All the machinery lives in scaffold.py. This module only declares WHAT this
project teaches: its phases, its steps, its quiz and its opening page.
"""
import sys
import scaffold

THEME = dict(
    title="AI for Building Energy Optimization",
    icon="🏢",
    dwg="BMS-HVAC-001",
    civil_label="Building Services Engineering",
    civil_kicker="IN THE BUILDING",
    station="⟨BMS·FLOOR 6⟩",
    rail="DAY",
    start_button="▶  Start: walk onto the floor plate",
    sidebar_title="A Building Energy Problem",
    sidebar_note="You are cutting HVAC energy without a single comfort complaint — and comfort has a veto.",
    backdrop=("linear-gradient(rgba(255,255,255,.02) 1px, transparent 1px),"
              "linear-gradient(90deg, rgba(255,255,255,.02) 1px, transparent 1px)"),
)

PHASES = [
    ("The Building In Use",        "One weekday, one floor plate, one facilities manager."),
    ("One Reading Interval",       "Fifteen minutes of operation becomes a written record."),
    ("Instrumenting The Building", "The BMS export lands and gets checked."),
    ("Preparing The Data",         "Faulty readings out, units standardised, days split."),
    ("Demand From The Sensors",    "Predicting HVAC load from the gauges alone."),
    ("The Image Wall",             "The camera arrives and the rulebook collapses."),
    ("How A Machine Learns",       "A neuron, a threshold, a loop, a network."),
    ("Reading The Room",           "A CNN grades a floor plate no rule could grade."),
    ("Locating The Use",           "The CNN shows which part of the floor is in use."),
    ("The Energy Audit",           "Every claim checked on days the model never saw."),
    ("Control & Optimisation",     "Forecast the peak, choose the setpoint, fuse it all."),
    ("The Business Case",          "kWh, carbon, cost and comfort the building keeps."),
]

_S = lambda **k: k
STEPS = [
_S(id='in-use', phase=0, civil='A Building On A Weekday', ai='Why Building Energy Needs AI',
   civil_icon='🏢', ai_icon='🤖', tech='A plant sized for 260 people, serving 40',
   civil_bullets=['Occupancy moves hourly', 'The plant does not', 'The bill arrives monthly'],
   ai_bullets=['Read every interval', 'Predict the demand', 'Act while it matters'],
   site="""A floor plate is designed for 260 desks. HVAC is the largest single electrical load in the
building, and it runs to a clock rather than to who is actually in.""",
   challenge="""Turning the plant down by hand risks a comfort complaint, and complaints are what get energy
initiatives cancelled. There are 96 intervals a day across every zone.""",
   ai_link="""The gap between the meter and the floor has to close: demand predicted from what the building
already measures, so a setback is proposed with evidence rather than guessed at.""",
   notebook="""Section 1. The plant model, a weekday, and what it draws.""",
   contributes="""The requirement. If energy is still found on the monthly invoice, this failed.""",
   takeaway="""The building is conditioned for the people it was designed for, not the ones in it."""),
_S(id='enter-ai', phase=0, civil='A Building That Senses Itself', ai='The Sensing Layer',
   civil_icon='📡', ai_icon='🛰️', tech='Fixed damper vs ventilating for the people present',
   civil_bullets=['Engineers stay', 'Sensors watch too', 'Nobody is replaced'],
   ai_bullets=['A live picture', 'It flags the waste', 'You still decide'],
   site="""Nothing about the plant changes. Same chillers, same fans, same comfort standard. Sensors are
added — temperature, humidity, CO2, occupancy, solar — and a camera looks at the plate.""",
   challenge="""The usual objection: is this here to replace the facilities engineer? No. A model cannot judge
a complaint, authorise a setback or sign a statutory air-change record.""",
   ai_link="""The system is a sensing layer that reports and recommends; a person decides. That split governs
every later design choice, especially the comfort veto at fusion.""",
   notebook="""No code. This step is the argument, not the arithmetic.""",
   contributes="""Defines the output: a recommendation to an engineer, never an automatic setback.""",
   takeaway="""The fixed damper ventilates for 200 people all day. That one assumption is the biggest saving here."""),
_S(id='reading', phase=1, civil='One 15-Minute Interval', ai='Data Collection',
   civil_icon='📏', ai_icon='🗄️', tech='One interval → one row of readings + kW',
   civil_bullets=['Eight channels', 'Every 15 minutes', 'Outcome recorded'],
   ai_bullets=['One row per interval', 'Eight features', 'One target'],
   site="""Every fifteen minutes the BMS records indoor and outdoor temperature, humidity, CO2, occupancy,
solar, particulates and the setpoint it was holding.""",
   challenge="""On their own these are eight trends on eight screens. No single one says whether that interval
was efficient, and there are 96 of them a day.""",
   ai_link="""Put them in one row and the interval becomes a record: eight inputs and the kW that resulted.
Thousands of those rows are the dataset every model here learns from.""",
   notebook="""Section 2. Build one row from the plant model, then sixteen weeks of them.""",
   contributes="""The unit of learning.""",
   takeaway="""One interval becomes one row: eight readings in, kilowatts out."""),
_S(id='two-records', phase=1, civil='Sensor Row vs Camera Frame', ai='Two Kinds Of Data',
   civil_icon='🧾', ai_icon='🔀', tech='Eight named numbers, or 4,096 unnamed pixels',
   civil_bullets=['The BMS row', 'The camera frame', 'Same interval, two views'],
   ai_bullets=['Named columns → ML', 'Raw pixels → DL', 'The fork in the road'],
   site="""Two records leave the floor every interval: eight named numbers, and a 64x64 grid of surface
temperatures from the ceiling camera with no names at all.""",
   challenge="""Both describe the same floor. The row says how much power was drawn; the frame says whether
anybody was there to need it. Neither is complete alone.""",
   ai_link="""Named columns suit Machine Learning. Raw pixels do not — nobody can name 4,096 useful columns.
That difference is the whole argument of this course.""",
   notebook="""Section 2. Print one row, then show one plate as an array.""",
   contributes="""The fork: numbers go to ML, images go to DL.""",
   takeaway="""Numbers arrive with names; images do not. That difference splits ML from DL."""),
_S(id='load', phase=2, civil='The BMS Export Arrives', ai='Loading The Dataset',
   civil_icon='📥', ai_icon='🐼', tech='CSV → DataFrame, 16 weeks × 96 intervals',
   civil_bullets=['Trend-log export', 'One row per interval', 'A cooling season'],
   ai_bullets=['read_csv', 'shape and dtypes', 'First look'],
   site="""The BMS exports sixteen weeks of the cooling season: one row per fifteen minutes, every channel,
plus the kW the plant drew.""",
   challenge="""An export is not a dataset. A controller reboot leaves gaps, a failed sensor writes a constant,
and a trend-log resync duplicates rows.""",
   ai_link="""Loading it is the first step: shape, column types and a first look — the basis for everything
the models later assume.""",
   notebook="""Section 3. `pd.read_csv`, `.shape`, `.head()`.""",
   contributes="""The dataset every later step reads from.""",
   takeaway="""The export is raw material. Loading it is where the data work starts."""),
_S(id='inspect', phase=2, civil='Sensor Health Check', ai='Data Inspection',
   civil_icon='🔍', ai_icon='📊', tech='Count gaps, stuck channels and impossible values',
   civil_bullets=['Did it report?', 'Is it stuck?', 'Is it possible?'],
   ai_bullets=['isna().sum()', 'describe()', 'duplicated()'],
   site="""Before trusting a season of trend logs, an engineer checks the instruments. Did the CO2 sensor
report all season? Is a zone temperature stuck at a constant?""",
   challenge="""Faults hide in plain sight. A drifted CO2 sensor reading 400 ppm all day looks like an empty
floor; a failed occupancy count reads zero.""",
   ai_link="""Inspection is that check in code: missing values per channel, minimum and maximum, and which
rows repeat. It finds what a monthly average hides.""",
   notebook="""Section 4. `.isna().sum()`, `.describe()`, `.duplicated()`.""",
   contributes="""The fault list the cleaning step works from.""",
   takeaway="""A drifted CO2 sensor does not read 'faulty'. It reads 400 ppm, which looks like an empty floor."""),
_S(id='clean', phase=3, civil='Removing The Faulty Readings', ai='Data Cleaning',
   civil_icon='🧹', ai_icon='🧼', tech='Drop duplicates, null the impossible, fill with the median',
   civil_bullets=['Repair the channel', 'Keep the interval', 'Never average a fault'],
   ai_bullets=['drop_duplicates', 'Mask impossibles', 'fillna(median)'],
   site="""A faulty sensor is recalibrated or discounted before its readings reach an energy report.""",
   challenge="""Deleting every affected row throws away good readings from the other seven channels. Keeping
them poisons the baseline that savings are measured against.""",
   ai_link="""Cleaning does both: drop duplicates, mark impossible values as missing rather than deleting the
row, then fill with the channel's median.""",
   notebook="""Section 5. `drop_duplicates`, mask the impossible, `fillna(median)`.""",
   contributes="""A dataset where every remaining number is physically possible.""",
   takeaway="""Repair the channel, not the interval: mark the impossible, fill with the median."""),
_S(id='normalize', phase=3, civil='Standardising The Measurements', ai='Normalization',
   civil_icon='📐', ai_icon='⚖️', tech='Min-max every channel to 0-1',
   civil_bullets=['ppm vs °C vs W/m²', 'Different magnitudes', 'One channel wins'],
   ai_bullets=['Rescale to 0-1', 'Units disappear', 'Data decides weight'],
   site="""The channels do not share a scale. CO2 runs to 1,400 ppm, solar to 880 W/m², indoor temperature
sits near 24 °C.""",
   challenge="""A model that adds weighted inputs lets the largest-numbered channel dominate — not because it
matters most, but because its units are bigger.""",
   ai_link="""Normalization rescales every channel to 0-1 using its own range. Units disappear, and importance
is decided by the data.""",
   notebook="""Section 6. `MinMaxScaler().fit_transform`.""",
   contributes="""Comparable channels, so learned weights mean something.""",
   takeaway="""Rescale every channel to 0-1 so units stop deciding importance."""),
_S(id='split', phase=3, civil='Known Days vs Sealed Days', ai='Train / Test Split',
   civil_icon='🗂️', ai_icon='✂️', tech='split by DAY, never by interval',
   civil_bullets=['A day is the unit', 'Intervals are not independent', 'Hold out whole days'],
   ai_bullets=['Group split', 'No leakage', 'An honest score'],
   site="""Consecutive intervals are almost identical: the sun does not move much in fifteen minutes and the
floor fills gradually.""",
   challenge="""Shuffle rows at random and 14:00 lands in training while 14:15 lands in test. The model has
effectively seen the answer, and the score becomes flatteringly meaningless.""",
   ai_link="""Split by **day**. Whole days go to training or to test, never both. Only then does the score
measure what the model would do on a day it has never seen.""",
   notebook="""Section 7. Group split on the day index.""",
   contributes="""The sealed days the audit runs on.""",
   takeaway="""Split by day. A random interval split leaks the afternoon into the morning."""),
_S(id='ml-baseline', phase=4, civil='Predicting Cooling Demand', ai='Machine Learning Baseline',
   civil_icon='❄️', ai_icon='🌲', tech='Random Forest: 9 readings → HVAC kW',
   civil_bullets=['What should it draw?', 'Was it over-conditioned?', 'From the gauges alone'],
   ai_bullets=['Threshold questions', 'Many trees averaged', 'Regression + class'],
   site="""The first question: given this interval's readings, how much power should the plant have drawn,
and was the floor over-conditioned for the people in it?""",
   challenge="""A design-load spreadsheet gets the order of magnitude right and the details wrong. Outdoor
temperature, solar, occupancy and humidity interact, and one formula does not track them together.""",
   ai_link="""A Random Forest learns that relationship from the trend log — threshold questions on the named
channels, averaged over many trees.""",
   notebook="""Section 8. `RandomForestRegressor` for kW, `RandomForestClassifier` for the waste flag.""",
   contributes="""The numeric half of the system, and the excess the fusion screen reports.""",
   takeaway="""Machine Learning predicts HVAC demand well — from named columns only."""),
_S(id='drivers', phase=4, civil='What Drives The Load', ai='Feature Importance',
   civil_icon='📈', ai_icon='🎚️', tech='Which channel moves the kW prediction most',
   civil_bullets=['Which lever?', 'Setpoint or damper?', 'Rank the causes'],
   ai_bullets=['feature_importances_', 'A priority list', 'Check against physics'],
   site="""Knowing an interval was wasteful is not actionable. The engineer needs to know which lever:
setpoint, ventilation rate, blinds, or the schedule.""",
   challenge="""The channels move together — outdoor temperature, solar and occupancy all peak in the
afternoon — so a correlation table shows what moved with what, not what mattered.""",
   ai_link="""Feature importance ranks how much each channel changes the prediction, and it is the first place
the model can be checked against building physics.""",
   notebook="""Section 8. `.feature_importances_`, sorted and plotted.""",
   contributes="""The ranking that decides which recommendation is issued.""",
   takeaway="""A ranked driver list turns a prediction into a decision about which lever to pull."""),
_S(id='camera-problem', phase=5, civil='What The Ceiling Camera Sends', ai='The Raw Image',
   civil_icon='📷', ai_icon='🖼️', tech='A 64x64 grid of temperatures, no named columns',
   civil_bullets=['Warm blob = person', 'Warm band = sunlight', 'Both are just warm'],
   ai_bullets=['4,096 numbers', 'No column names', 'Nothing to weight'],
   site="""A ceiling camera looks at the plate. A frame is a grid of surface temperatures: people show as
small compact warm blobs, sunlight as a broad band down the façade.""",
   challenge="""The camera does not output "twelve people". It outputs 4,096 numbers with no names. There is
no column called person.""",
   ai_link="""This is where Machine Learning runs out — it needs named features and there are none. Before
reaching for a new method, it is worth building the feature by hand and watching what happens.""",
   notebook="""Section 9. Build a plate as an array and display it.""",
   contributes="""The data type that forces the second half of the course.""",
   takeaway="""A plate is 4,096 unnamed numbers. Machine Learning has nothing to weight."""),
_S(id='handmade', phase=5, civil='Counting People By Brightness', ai='Hand-Made Features',
   civil_icon='✋', ai_icon='🔢', tech='One number from 4,096 pixels — and what it loses',
   civil_bullets=['Reduce to a mean', 'Set a threshold', 'Exactly as before'],
   ai_bullets=['One feature', 'One threshold', 'It misses'],
   site="""The obvious workaround: average the plate's temperature and call anything warm 'occupied'.""",
   challenge="""Averaging destroys the evidence. A sunlit empty façade is warmer than a lightly occupied
floor, so any threshold that catches twelve people also fires on an empty room.""",
   ai_link="""The feature was hand-made and it was the wrong feature. Deep Learning removes the guessing by
learning the features from the plates themselves.""",
   notebook="""Section 9. Mean plate temperature, and the threshold sweep that fails.""",
   contributes="""The failed baseline that justifies the CNN.""",
   takeaway="""A sunlit empty floor is warmer than a busy one. No brightness threshold survives that."""),
_S(id='why-dl', phase=5, civil='Why The Rulebook Ran Out', ai='Why Deep Learning',
   civil_icon='🚧', ai_icon='🧠', tech='Learn the features instead of naming them',
   civil_bullets=['No threshold works', 'Rules keep breaking', 'Every façade differs'],
   ai_bullets=['Features are learned', 'From labelled plates', 'Not hand-picked'],
   site="""There is no threshold on mean temperature, and no combination of two or three hand-picked numbers,
that separates a busy floor from a sunlit empty one.""",
   challenge="""You could keep writing rules — a gradient here, a shape factor there — and every new façade,
season and camera angle would break them.""",
   ai_link="""Deep Learning inverts the job: the model learns which features matter directly from labelled
images. That is the entire difference.""",
   notebook="""Section 10. The framing, before any network is built.""",
   contributes="""The decision to use a CNN, made for a reason.""",
   takeaway="""Machine Learning weights the features you name. Deep Learning finds the features you cannot name."""),
_S(id='engineer-brain', phase=6, civil='How A Facilities Engineer Decides', ai='The Neuron, Informally',
   civil_icon='👷', ai_icon='💡', tech='Weigh the signals, add them, decide',
   civil_bullets=['Several signals at once', 'Some matter more', 'One call'],
   ai_bullets=['Weights', 'A sum', 'A threshold'],
   site="""An engineer deciding whether a zone can be set back weighs CO2, indoor temperature, the hour and
how many complaints came in this week — and makes one call.""",
   challenge="""That judgement is fast and good, but it lives in one head, covers one zone at a time, and
cannot be applied to sixteen weeks of trend logs overnight.""",
   ai_link="""Write it down and it is arithmetic: multiply each signal by how much it matters, add, act if the
total clears a threshold. That is a neuron.""",
   notebook="""Section 11. The weighted-sum decision, before any terminology.""",
   contributes="""The intuition every later network is built on.""",
   takeaway="""A neuron is an engineer's judgement written as arithmetic: weigh, add, decide."""),
_S(id='neuron', phase=6, civil='Weighing Each Reading', ai='The Neuron',
   civil_icon='⚖️', ai_icon='🔵', tech='z = w·x + b',
   civil_bullets=['CO2 matters a lot', 'PM2.5 matters little', 'Experience = weights'],
   ai_bullets=['Weights are learned', 'Bias sets the baseline', 'Traceable to data'],
   site="""Give each reading a weight. CO2 matters a great deal for whether anyone is in. Particulates matter
little. An engineer's experience is exactly that set of weights.""",
   challenge="""Those weights are guesses, and every engineer guesses differently. Nobody can defend a number
like "CO2 counts 3.4 times more than solar" from experience alone.""",
   ai_link="""A neuron computes a weighted sum plus a bias, and the weights are learned from the trend log
rather than chosen by seniority.""",
   notebook="""Section 11. `z = w·x + b`, computed by hand.""",
   contributes="""The single unit every network here is built from.""",
   takeaway="""A neuron is a weighted sum plus a bias, and the weights come from the data."""),
_S(id='activation', phase=6, civil='The Setpoint Threshold', ai='Activation Function',
   civil_icon='🚨', ai_icon='📉', tech='sigmoid and ReLU',
   civil_bullets=['Acceptable or not', 'A hard limit is brittle', 'Comfort is graded'],
   ai_bullets=['Sigmoid → 0..1', 'ReLU passes positives', 'Smooth = trainable'],
   site="""A control action reports a state, not a weighted sum. Somewhere the continuous signal has to
become a decision.""",
   challenge="""A hard on/off limit is brittle. An interval a hair under is treated as fine and one a hair over
triggers a setback. Comfort does not step like that.""",
   ai_link="""An activation function does the same job smoothly, and that smoothness is what makes the network
trainable at all.""",
   notebook="""Section 12. Plot sigmoid and ReLU, and pass `z` through both.""",
   contributes="""The step that turns a raw sum into a usable probability.""",
   takeaway="""Activation turns a weighted sum into a graded decision instead of a brittle limit."""),
_S(id='learning-loop', phase=6, civil='Improving After Every Bad Day', ai='The Learning Loop',
   civil_icon='🔁', ai_icon='🎯', tech='predict → error → adjust → repeat',
   civil_bullets=['The meter shows the miss', 'Adjust the judgement', 'Better tomorrow'],
   ai_bullets=['Compare to truth', 'Measure the error', 'Nudge every weight'],
   site="""A setback is judged wrong and the floor overheats. The next day the engineer adjusts: weight
occupancy more, the clock less.""",
   challenge="""Done by hand that correction happens once a day and depends on who is on shift. Nine channels
and thousands of intervals cannot be tuned that way.""",
   ai_link="""The learning loop is that correction automated: predict, compare with the meter, measure the
error, adjust every weight a little, repeat.""",
   notebook="""Section 13. The loop, before the optimiser has a name.""",
   contributes="""The mechanism that turns a random model into a useful one.""",
   takeaway="""Predict, measure the error, adjust, repeat — that loop is all training is."""),
_S(id='gradient-descent', phase=6, civil='Commissioning The Controls', ai='Loss & Gradient Descent',
   civil_icon='🎛️', ai_icon='⛰️', tech='loss surface, gradient, learning rate',
   civil_bullets=['Change a setpoint', 'Measure the result', 'Step again'],
   ai_bullets=['Loss = how wrong', 'Gradient = downhill', 'Rate = step size'],
   site="""Commissioning is a search: change a setpoint, measure, keep the change if it helped, step again in
the direction that worked.""",
   challenge="""Step too far and the zone oscillates. Step too small and commissioning takes a season. The step
size is the whole difficulty, and it is usually chosen by feel.""",
   ai_link="""Loss measures how wrong the model is; gradient descent steps downhill and the learning rate is
the step size. Same overshoot, same reason.""",
   notebook="""Section 13. A loss surface and the descent path at three learning rates.""",
   contributes="""How the weights actually change during training.""",
   takeaway="""Training is commissioning by search: step downhill on the error, and mind the step size."""),
_S(id='network', phase=6, civil='The Facilities Team', ai='The Neural Network',
   civil_icon='👥', ai_icon='🕸️', tech='input → hidden layers → output',
   civil_bullets=['Comfort specialist', 'Energy specialist', 'Air-quality specialist'],
   ai_bullets=['Each neuron, a view', 'Layers combine them', 'One output'],
   site="""No single engineer covers everything. One watches comfort, one energy, one indoor air quality. A
manager combines their calls.""",
   challenge="""Coordinating specialists is slow and their reports conflict — the energy view and the comfort
view routinely disagree.""",
   ai_link="""A hidden layer is that team. Each neuron learns a different combination of the readings, and the
output neuron weighs their conclusions into one answer.""",
   notebook="""Section 14. `MLPClassifier(hidden_layer_sizes=(12, 6))`.""",
   contributes="""The numeric neural network, ready to be compared with the forest.""",
   takeaway="""A layer is a team of specialists; the output neuron is the manager who signs the call."""),
_S(id='training', phase=6, civil='Training The New Recruits', ai='Training',
   civil_icon='📚', ai_icon='🏋️', tech='epochs, training vs validation loss',
   civil_bullets=['Learn from records', 'Not from a textbook', 'Then prove it'],
   ai_bullets=['Many epochs', 'Watch validation', 'Stop at the turn'],
   site="""A new engineer learns from this building's own trend logs, not from a manual written for another
site.""",
   challenge="""Learn them too well and you have memorised last season: perfect on it, useless on the next.
Stop too early and nothing has been learned.""",
   ai_link="""Training runs the learning loop for many epochs and watches the loss on validation days it never
learns from. When that stops falling, learning has become memorising.""",
   notebook="""Section 14. Loss curves for training and validation.""",
   contributes="""The trained numeric model used in the audit.""",
   takeaway="""Watch the validation curve — where it turns, learning has become memorising."""),
_S(id='cnn-journey', phase=7, civil='Reading The Floor Plate', ai='Convolution & Feature Maps',
   civil_icon='🔥', ai_icon='🧩', tech='filters → feature maps → classification',
   civil_bullets=['A compact blob', 'A broad band', 'Shape, not warmth'],
   ai_bullets=['Filters slide', 'Edges → clusters', 'Filters are learned'],
   site="""A plate is not read pixel by pixel. An engineer sees a shape: compact warm blobs where people sit,
a broad band where the sun falls.""",
   challenge="""Shape cannot be captured by any single pixel value, and it moves. The same twelve people sit
somewhere different in every frame.""",
   ai_link="""A convolution slides a small filter over the plate and reports where its pattern occurs. Early
filters find edges; later ones separate compact blobs from broad bands.""",
   notebook="""Section 15. Convolve a plate by hand, then train a small CNN.""",
   contributes="""The visual half of the system: an occupancy class for every plate.""",
   takeaway="""Convolution separates a compact blob from a broad band — which is exactly a person from sunlight."""),
_S(id='occupancy-locate', phase=8, civil='Which Part Of The Floor Is In Use', ai='Grad-CAM',
   civil_icon='📍', ai_icon='🗺️', tech='class-weighted feature maps → heat map',
   civil_bullets=['Which zone?', 'How many?', 'Set back the rest'],
   ai_bullets=['Weight the maps', 'Project onto the plate', 'Show the evidence'],
   site="""A whole-floor class is not enough. A floor with one busy corner should not be set back entirely,
and should not be conditioned entirely either.""",
   challenge="""A classifier outputs a class. It gives no location, and an engineer asked to set back a zone on
a bare class will — rightly — not do it.""",
   ai_link="""Grad-CAM weights the last feature maps by how much each contributed and projects them back onto
the plate. The bright region is the occupied zone, and the evidence.""",
   notebook="""Section 16. Grad-CAM over the trained CNN.""",
   contributes="""The location that makes zone-level control possible.""",
   takeaway="""A class sets back a floor; a location sets back the empty half of it."""),
_S(id='audit', phase=9, civil='The Building Energy Audit', ai='Confusion Matrix',
   civil_icon='🧮', ai_icon='✅', tech='TP / FP / FN / TN and what each costs',
   civil_bullets=['Predicted vs metered', 'On sealed days', 'Every claim checked'],
   ai_bullets=['Four outcomes', 'False alarm ≠ miss', 'Recall matters'],
   site="""Every saving claim is audited: predicted against metered, on days the model was never allowed to
see.""",
   challenge="""A single accuracy figure hides what matters. Predicting "not wasteful" for every interval
scores well on a building that is mostly fine — and finds nothing.""",
   ai_link="""The confusion matrix separates the four outcomes, and here the two costs are of completely
different kinds: money on one side, a comfort complaint on the other.""",
   notebook="""Section 17. Confusion matrix, accuracy and recall on the sealed days.""",
   contributes="""The honest performance number the project is judged on.""",
   takeaway="""One error costs kilowatt-hours; the other costs a complaint. They are not interchangeable."""),
_S(id='proof', phase=9, civil='The Verdict', ai='ML vs DL, Proven',
   civil_icon='⚔️', ai_icon='🏁', tech='the same task, both methods, measured',
   civil_bullets=['Two data types', 'Two methods', 'One building'],
   ai_bullets=['Forest wins on numbers', 'CNN wins on pixels', 'Neither replaces the other'],
   site="""Two models, two data types, one building. Time to state plainly what each can and cannot do.""",
   challenge="""It is tempting to declare Deep Learning better. It is not better — it is different, and on the
BMS row the forest is faster, cheaper and far easier to defend to an auditor.""",
   ai_link="""Run both on both. The forest wins on the nine named channels and cannot take a plate at all. The
CNN grades the plate. Each method belongs to its data type.""",
   notebook="""Section 18. The comparison table, filled in from measured results.""",
   contributes="""The course's central claim, demonstrated rather than asserted.""",
   takeaway="""ML weights the columns you name; DL finds the patterns you cannot name."""),
_S(id='forecast', phase=10, civil="Tomorrow's Peak", ai='Forecasting',
   civil_icon='📅', ai_icon='🔮', tech='predict the peak interval before it happens',
   civil_bullets=['Pre-cool early', 'Shave the peak', 'Avoid the charge'],
   ai_bullets=['Forecast the day', 'Act in advance', 'Measure the shave'],
   site="""Many tariffs charge on the highest half-hour of the month. A single bad afternoon can cost more
than a week of ordinary running.""",
   challenge="""By the time the peak is visible on the meter it has already been set. Acting on it requires
knowing it is coming.""",
   ai_link="""Feed tomorrow's weather and the occupancy pattern into the demand model and the peak interval
falls out — early enough to pre-cool into the building's own thermal mass.""",
   notebook="""Section 19. Forecast the day, then shave the peak.""",
   contributes="""The action that pays for the project on a demand-charge tariff.""",
   takeaway="""A peak you can predict is a peak you can pre-cool away."""),
_S(id='setpoint', phase=10, civil='Choosing The Setpoint', ai='Constrained Optimisation',
   civil_icon='🎯', ai_icon='🧭', tech='sweep the setpoint → kW falls, PPD rises',
   civil_bullets=['Warmer is cheaper', 'Always', 'Comfort decides how far'],
   ai_bullets=['Sweep the range', 'Two curves', 'The limit is the answer'],
   site="""The engineer chooses a cooling setpoint. Raising it always saves energy — there is no interior
minimum on that curve.""",
   challenge="""So the optimisation is not "where is the cheapest setpoint". It is "how far can I go before
comfort fails" — a **constraint**, not a minimum.""",
   ai_link="""Sweep the setpoint, predict kW at each one, and compute PPD alongside. The answer is where the
comfort curve crosses its limit, not where the energy curve bottoms out.""",
   notebook="""Section 20. Sweep the setpoint against kW and PPD together.""",
   contributes="""The recommendation the dashboard prices.""",
   takeaway="""Energy has no optimum setpoint — comfort supplies the limit that makes one exist."""),
_S(id='fusion-engine', phase=10, civil='The Building Intelligence Engine', ai='AI Fusion',
   civil_icon='🖥️', ai_icon='🔗', tech='ML excess + CNN class + PPD veto → one action',
   civil_bullets=['Three opinions', 'One engineer', 'One action list'],
   ai_bullets=['Combine the outputs', 'Rank by kW', 'Comfort can veto'],
   site="""By now every zone produces three outputs each interval: a predicted kW, a camera class with a
location, and a comfort index.""",
   challenge="""Three screens is three chances to miss something — and two of them routinely disagree, because
the cheapest action and the most comfortable one are rarely the same.""",
   ai_link="""Fusion combines them into one ranked recommendation with the evidence attached, and gives
comfort a **veto**: it can block a saving but never create one.""",
   notebook="""Section 21. A rules layer over both model outputs, with the comfort veto.""",
   contributes="""The product — one screen a facilities engineer can act on.""",
   takeaway="""Numbers say how much; the camera says whether anyone is there; comfort says whether you may act."""),
_S(id='pipeline', phase=10, civil='The Whole System', ai='The Pipeline',
   civil_icon='🧱', ai_icon='🛤️', tech='sensors → data → ML + DL → fusion → dashboard',
   civil_bullets=['Sensors and camera', 'Models', 'A screen that acts'],
   ai_bullets=['Every stage feeds one', 'Data quality first', 'One recommendation'],
   site="""Step back and the whole system is visible: sensors and a camera on the floor, a data path, two
models, and a screen the engineer reads.""",
   challenge="""Every stage depends on the ones before it. A stuck CO2 sensor that survives cleaning becomes a
false setback four stages later — and a comfort complaint the week after.""",
   ai_link="""The pipeline is the engineering drawing: what feeds what, where the two data types split, and
where the comfort veto sits.""",
   notebook="""Section 22. The end-to-end run, in one place.""",
   contributes="""The map of everything built so far.""",
   takeaway="""The system is a chain: data quality at the start decides the setback at the end."""),
_S(id='dashboard', phase=11, civil='The Smart Building Dashboard', ai='kWh, Carbon & Comfort',
   civil_icon='📉', ai_icon='💷', tech='kWh, tCO2, cost and PPD, before and after',
   civil_bullets=['Approve a spend', 'Against a saving', 'Without a complaint'],
   ai_bullets=['kWh avoided', 'tCO2 avoided', 'Comfort held'],
   site="""The building owner does not buy a model. They approve a spend against a saving in kWh, carbon and
money — and against a comfort standard that must not slip.""",
   challenge="""Energy savings are easy to overstate, and a saving that produces complaints is withdrawn within
a month. Both numbers have to be reported together.""",
   ai_link="""The dashboard reports kWh avoided, carbon, cost **and** the comfort index — every figure
arithmetic on assumptions the reader can change.""",
   notebook="""Section 23. The dashboard, computed from the assumptions above.""",
   contributes="""The business case — the reason the previous steps get funded.""",
   takeaway="""Report the comfort index next to the saving, or the saving will not survive its first month."""),
]

SHORT = {
    "in-use": "A weekday",                "enter-ai": "A building that senses",
    "reading": "One interval",            "two-records": "Row vs frame",
    "load": "BMS export arrives",         "inspect": "Sensor health check",
    "clean": "Faulty readings out",       "normalize": "Standardising",
    "split": "Known vs sealed days",      "ml-baseline": "Predicting demand",
    "drivers": "What drives the load",    "camera-problem": "The raw plate",
    "handmade": "Counting by brightness", "why-dl": "Rulebook ran out",
    "engineer-brain": "Engineer decides", "neuron": "Weighing each reading",
    "activation": "Setpoint threshold",   "learning-loop": "After a bad day",
    "gradient-descent": "Commissioning",  "network": "The facilities team",
    "training": "Training recruits",      "cnn-journey": "Reading the plate",
    "occupancy-locate": "Which part is used", "audit": "The energy audit",
    "proof": "The verdict",               "forecast": "Tomorrow's peak",
    "setpoint": "Choosing the setpoint",  "fusion-engine": "The intelligence engine",
    "pipeline": "The whole system",       "dashboard": "The dashboard",
}
for _s in STEPS:
    _s["short"] = SHORT[_s["id"]]

_q = lambda q, options, answer, why: dict(q=q, options=options, answer=answer, why=why)
QUIZ = {
    'in-use': _q("Why is the floor plate over-conditioned most of the day?",
                 ["The chiller is oversized", "The plant serves the design population and the schedule, not the people actually in",
                  "The sensors are wrong", "Occupants set it too cold"], 1,
                 "The fixed damper ventilates for 200 people all day, whatever the floor is doing."),
    'enter-ai': _q("What is the system's actual output?",
                   ["An automatic setback", "A replacement for the facilities engineer",
                    "A recommendation with evidence, which an engineer decides on", "A monthly PDF"], 2,
                   "The layer reports and recommends; the engineer decides and signs off."),
    'reading': _q("Why is one interval written as a single row?",
                  ["It saves disk space", "Because the row ties the readings to the kW that resulted, which is what a model learns from",
                   "Because the BMS can only write rows", "So it fits on one screen"], 1,
                  "The row pairs cause with effect. Thousands of those pairs are the dataset."),
    'two-records': _q("What makes the BMS row suit ML and the plate suit DL?",
                      ["The row is bigger", "Images are always harder",
                       "The row has named columns an engineer chose; the plate is 4,096 unnamed pixels", "ML cannot handle decimals"], 2,
                      "Nobody can name 4,096 pixel columns, so the features have to be learned."),
    'load': _q("Why is a BMS export not yet a dataset?",
               ["Wrong file format", "It contains controller-reboot gaps, stuck sensors and resync duplicates",
                "It is too large for pandas", "It has no header row"], 1,
               "Loading it is only the first step; what is in it still has to be checked."),
    'inspect': _q("A CO₂ sensor reads exactly 400 ppm all week. What is it?",
                  ["A very well ventilated floor", "A drifted or failed sensor writing a valid-looking number",
                   "Normal for a weekend", "A rounding artefact"], 1,
                  "An occupied floor always produces some CO₂. 400 is valid and a fault at once — and it looks exactly like an empty floor."),
    'clean': _q("Why fill a missing reading with the channel's median rather than its mean?",
                ["It is faster", "The mean is only valid for whole numbers",
                 "The median ignores the extreme faulty values still in the column", "The median is always larger"], 2,
                "A single stuck maximum shifts a mean badly. The median barely moves."),
    'normalize': _q("What goes wrong without rescaling?",
                    ["The code crashes", "The largest-numbered channel dominates the weighted sum because of its unit, not its importance",
                     "The data takes more memory", "The plots look untidy"], 1,
                    "CO₂ in ppm and temperature in °C are not comparable magnitudes until rescaled."),
    'split': _q("Why split by day rather than by interval?",
                ["Days are easier to count", "Because 14:00 and 14:15 are nearly identical — a random split puts the answer in training",
                 "Because sklearn requires it", "To balance the classes"], 1,
                "Consecutive intervals are not independent, so an interval split leaks and flatters the score."),
    'ml-baseline': _q("Why does a Random Forest beat a design-load spreadsheet?",
                      ["It uses more decimals", "It learns how outdoor temperature, solar, occupancy and humidity interact, from this building's own logs",
                       "It works on images too", "It never makes mistakes"], 1,
                      "The interactions are what a fixed formula misses."),
    'drivers': _q("Feature importance ranks outdoor temperature first. What has it told you?",
                  ["Outdoor temperature causes all waste", "The other channels can be deleted",
                   "The prediction moves most with it — but it is not a lever you can pull, so look at the ones that are",
                   "The sensor is broken"], 2,
                  "A large coefficient you cannot change is less useful than a small one you can."),
    'camera-problem': _q("Why can the Random Forest not take the plate as input?",
                         ["The image is too large", "There are no named features — only 4,096 pixel values with no individual meaning",
                          "Forests only accept integers", "The resolution is too low"], 1,
                         "A pixel at row 12 column 40 is not a feature anybody can name or defend."),
    'handmade': _q("Why does thresholding on mean plate temperature fail?",
                   ["The camera is not calibrated", "The mean is computed incorrectly",
                    "A sunlit empty façade is warmer than a lightly occupied floor, so the rule fires on the wrong thing", "Thresholds never work"], 2,
                   "Averaging discards the spatial pattern, which is the only place the evidence lived."),
    'why-dl': _q("What is the one-line difference between ML and DL here?",
                 ["DL is newer", "DL needs less data",
                  "ML weights features a human names; DL learns the features itself from labelled examples", "DL is always more accurate"], 2,
                 "That is the whole distinction — and why DL is the wrong choice for the nine-channel BMS row."),
    'engineer-brain': _q("An engineer weighs CO₂, temperature and recent complaints, then decides. What is that?",
                         ["A confusion matrix", "A neuron: weighted inputs, summed, compared to a threshold",
                          "A convolution", "A train/test split"], 1,
                         "The neuron is the engineer's rule of thumb written as arithmetic."),
    'neuron': _q("In z = w·x + b, what does b do?",
                 ["Scales the inputs", "Shifts the baseline, so the neuron can fire without every input being large",
                  "Counts the features", "Selects the activation"], 1,
                 "The bias sets where the decision sits."),
    'activation': _q("Why not a hard on/off limit instead of a sigmoid?",
                     ["Sigmoid is faster", "A hard limit treats 'just under' and 'just over' as opposites and gives training no gradient",
                      "Hard limits are not allowed in Python", "Sigmoid uses less memory"], 1,
                     "The graded output is more honest, and the smoothness is what makes gradient descent possible."),
    'learning-loop': _q("What is the essential order of the learning loop?",
                        ["Adjust → predict → measure", "Predict → compare with truth → measure error → adjust weights → repeat",
                         "Measure → stop", "Split → normalize → predict"], 1,
                        "Every training algorithm here is that loop, repeated over the rows."),
    'gradient-descent': _q("The loss oscillates and never settles. Why?",
                           ["Too little data", "The learning rate is too large, so each step overshoots the minimum",
                            "The loss function is wrong", "Too many features"], 1,
                           "Same as over-adjusting a setpoint during commissioning."),
    'network': _q("What does adding a hidden layer buy you?",
                  ["Faster training", "Neurons that each learn a different combination, so interactions a single weighted sum cannot express become representable",
                   "Fewer weights", "Automatic data cleaning"], 1,
                  "One neuron draws one boundary. A layer of them draws the shape the data needs."),
    'training': _q("Training loss falls but validation loss rises. What is happening?",
                   ["The data is corrupt", "The model has started memorising the training days instead of learning the pattern",
                    "The learning rate is too small", "Training finished successfully"], 1,
                   "That turn is where learning becomes memorising. Stop there."),
    'cnn-journey': _q("Why does convolution separate a person from sunlight when a mean cannot?",
                      ["Because people are hotter", "Because a filter responds to LOCAL contrast — a compact blob — while sunlight is a broad band with almost none",
                       "Because the camera is fixed", "Because sunlight is dimmer"], 1,
                      "The evidence is the size and shape of the warm patch, which averaging destroys."),
    'occupancy-locate': _q("What does Grad-CAM add to a CNN's class?",
                           ["Higher accuracy", "A faster prediction",
                            "A heat map of which part of the floor is in use — so the empty half can be set back while the busy half is served", "An automatic setback"], 2,
                           "A whole-floor class would set back a floor with one busy corner."),
    'audit': _q("A model calls every interval 'not wasteful' and scores 78%. What is wrong?",
                ["Nothing — 78% is good", "It never finds waste, which is the point of the system; accuracy hides that",
                 "The test set is too small", "Accuracy should be on the training set"], 1,
                "Recall on the wasteful intervals is the number that matters."),
    'proof': _q("What does the head-to-head comparison prove?",
                ["Deep Learning is better", "Machine Learning is obsolete",
                 "Each method belongs to its data type: the forest wins on named channels, the CNN on raw plates", "Both perform identically"], 2,
                "The central claim of the course, demonstrated with measured numbers."),
    'forecast': _q("Why forecast the peak instead of reacting to it?",
                   ["Forecasting is cheaper", "Because on a demand-charge tariff the peak is already set by the time it is visible on the meter",
                    "Because meters are slow", "To reduce sensor cost"], 1,
                   "Pre-cooling into the building's thermal mass only works if you act before the peak."),
    'setpoint': _q("Why is there no optimum cooling setpoint on the energy curve alone?",
                   ["There is one, at 24 °C", "Because raising the setpoint always saves energy — the curve has no interior minimum, so comfort must supply the limit",
                    "Because the chiller COP is constant", "Because occupancy varies"], 1,
                   "This is a constrained optimisation, not a minimisation — which is a genuinely different shape of problem."),
    'fusion-engine': _q("Why does the comfort index get a veto rather than a weight?",
                        ["It is more accurate", "Because it may only ever block a saving, never create one — a system that trades comfort for kWh gets switched off",
                         "Because PPD is hard to compute", "Because occupants complain anyway"], 1,
                        "Weighting comfort against energy would let the model buy kilowatt-hours with complaints."),
    'pipeline': _q("Why does a stuck CO₂ sensor that survives cleaning matter four stages later?",
                   ["It slows the code", "It does not — the model corrects it",
                    "Because the pipeline is a chain: it looks like an empty floor, so the model recommends a setback on an occupied one", "It only affects the plots"], 2,
                   "Nothing downstream can recover information that was wrong at the source."),
    'dashboard': _q("Why report the comfort index next to the saving?",
                    ["Regulations require it", "Because a saving that produces complaints is withdrawn within a month, so the two numbers only mean something together",
                     "To fill the page", "Because PPD is easier to measure"], 1,
                    "Every figure on it is arithmetic on assumptions the reader can change."),
}

START = dict(
    project_line="one building energy project",
    problem="""
A floor plate is designed for **260 desks**. HVAC is the largest single electrical load in the building,
and it runs **to a clock**: fixed schedule, fixed setpoint, and a damper that brings in fresh air for
**200 people all day** whatever the floor is doing. Most of the day, far fewer are in. But turning the
plant down by hand risks a **comfort complaint**, and complaints are what get energy initiatives
cancelled. The job: **cut HVAC energy without a single complaint.**
""",
    build_intro="A **building intelligence layer** for the floor plate. Four parts:",
    cards=[
        ("📟", "Sensors read the building",
         "Indoor and outdoor temperature, humidity, CO₂, occupancy, solar, particulates and the setpoint. "
         "Logged every fifteen minutes, on every zone."),
        ("📷", "The camera reads the floor",
         "A ceiling plate where people are small compact warm blobs and sunlight is a broad warm band — "
         "patterns that live in the image, not in any single sensor reading."),
        ("🧠", "AI predicts demand and finds the waste",
         "Predict the kW an interval should have drawn, flag the excess, grade the plate for occupancy, "
         "forecast tomorrow's peak, and find how far the setpoint may go."),
        ("🔔", "The engineer gets a priority — and comfort can veto",
         "Not a black box. A clear call: set back this zone, this much — with the evidence shown, and a "
         "comfort index that can block the action but never create one."),
    ],
    promise="""The facilities engineer stays in charge and stays accountable. The system handles the part
one person cannot: it reads every zone, every fifteen minutes, and turns what it finds into kilowatt-hours
— while a comfort index holds the veto. The goal is <b>Building Services Engineer + AI</b>: a cheaper
building that nobody complains about.""",
    map_note="""<b>Every AI concept here is a building-services activity you already understand</b> — the
same thing, named differently by a different profession. Read down the amber column and you have described
an energy-management project. Read down the cyan column and you have described a deep learning pipeline.
They are the same column.""",
)

_m = sys.modules[__name__]
BY_ID, ORDER = scaffold.lookups(_m)
inject_css = lambda: scaffold.inject_css(_m)
open_page = lambda stage: scaffold.open_page(_m, stage)
close_page = lambda stage: scaffold.close_page(_m, stage)
render_start = lambda: scaffold.render_start(_m)
route = lambda STAGES, ALIASES=None: scaffold.route(_m, STAGES, ALIASES)
