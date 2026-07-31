"""
bridge.py — the Electrical-Engineering -> AI teaching content.
==============================================================
All the machinery lives in scaffold.py. This module only declares WHAT this
project teaches: its phases, its steps, its quiz and its opening page.
"""
import sys
import scaffold

THEME = dict(
    title="AI for Power Source Selection",
    icon="🔌",
    dwg="MG-DSP-001",
    civil_label="Electrical Engineering",
    civil_kicker="ON THE MICROGRID",
    station="⟨MICROGRID·CAMPUS⟩",
    rail="DAY",
    start_button="▶  Start: 06:00 in the plant room",
    sidebar_title="A Dispatch Problem",
    sidebar_note="You are choosing where the next fifteen minutes of power comes from — 96 times a day.",
    backdrop=("linear-gradient(rgba(255,255,255,.02) 1px, transparent 1px),"
              "linear-gradient(90deg, rgba(255,255,255,.02) 1px, transparent 1px)"),
)

PHASES = [
    ("The Microgrid",          "Five sources, one campus, and a decision every fifteen minutes."),
    ("One Interval",           "One interval of operation becomes one row of observable numbers."),
    ("The Historian Export",   "Four months of SCADA lands, and gets checked."),
    ("Preparing The Data",     "Bad readings out, the right columns in, and a split that does not lie."),
    ("The Rule And The Optimum", "What the plant already runs, and what was actually best."),
    ("The Decision Model",     "A model that chooses the source, and explains why."),
    ("Scoring It Properly",    "Rupees, not accuracy — and a whole month run closed-loop."),
    ("Reliability",            "The grid fails, and the diesel earns its keep."),
    ("The System",             "One recommendation, and what it is worth per year."),
]

STEPS = [
dict(
    id='microgrid', phase=0,
    civil='The Microgrid At 06:00', ai='Why Dispatch Needs AI',
    civil_icon='⚡', ai_icon='🤖',
    tech='96 decisions a day, each one about a price four hours away',
    civil_bullets=['Five sources', 'One campus', 'A decision every 15 min'],
    ai_bullets=['Learn the best choice', 'From the data available', 'Every interval'],
    site="""A campus microgrid has solar, wind, a battery, a grid connection and a diesel set. Every fifteen
minutes somebody decides where the next block of energy comes from.""",
    challenge="""There are 96 of those decisions a day. Each depends on the price now, the price in four hours,
the state of charge, the forecast and whether the grid is up. Nobody gets that right 35,000 times a year.""",
    ai_link="""The best choice can be worked out exactly *after* the fact. A model can learn that mapping and
apply it in real time, from what is observable at the moment of the decision.""",
    notebook="""Section 1. The tariff, the profiles, and the net load the decision is about.""",
    contributes="""The requirement. If the plant still runs on a fixed rule, this failed.""",
    takeaway="""The same kilowatt-hour is worth 2.5× more at 19:00 than at 03:00. Everything follows from that.""",
),
dict(
    id='sources', phase=0,
    civil='Five Sources, Five Real Costs', ai='The Cost Function',
    civil_icon='🔋', ai_icon='🧮',
    tech='Rs/kWh per source, including round-trip loss and wear',
    civil_bullets=['Solar and wind are free', 'The grid varies', 'Diesel never does'],
    ai_bullets=['Cost is the objective', 'Wear is part of it', 'No cycle is free'],
    site="""Solar and wind cost nothing once built. The grid costs 4.50, 8.00 or 11.50 Rs/kWh depending on
the hour. Diesel costs 21 Rs/kWh whenever you use it.""",
    challenge="""The battery has no tariff of its own. What it delivers costs whatever charged it, divided by
round-trip efficiency, plus the wear of the cycle — so the same discharge can be a saving or a loss.""",
    ai_link="""That cost function is the objective everything else is judged against. Get it wrong and the
model optimises the wrong thing very efficiently.""",
    notebook="""Section 2. Cost per kWh from every source, at every hour.""",
    contributes="""The objective the optimiser minimises and the dashboard reports.""",
    takeaway="""A battery cycle is never free — charge price ÷ efficiency, plus wear.""",
),
dict(
    id='reading', phase=1,
    civil='One Interval', ai='Data Collection',
    civil_icon='📏', ai_icon='🗄️',
    tech='One interval → one row of observable numbers',
    civil_bullets=['Thirteen readings', 'Every 15 minutes', 'Decision recorded'],
    ai_bullets=['One row per interval', 'Only what is knowable', 'One label'],
    site="""Every fifteen minutes the SCADA system records demand, solar, wind, state of charge, the tariff,
grid availability and temperature.""",
    challenge="""Alone those are numbers on a mimic panel. No single one says which source to use, and the right
answer depends on hours that have not happened yet.""",
    ai_link="""Put them in one row, add the two things that *are* legitimately knowable about the future — the
published tariff and a weather forecast — and the interval becomes a training example.""",
    notebook="""Section 3. Build one interval from the plant model, then four months of them.""",
    contributes="""The unit of learning. Everything downstream is rows like this one.""",
    takeaway="""One interval becomes one row — and only what was knowable at the time may go in it.""",
),
dict(
    id='load', phase=2,
    civil='The SCADA Export Arrives', ai='Loading The Dataset',
    civil_icon='📥', ai_icon='🐼',
    tech='CSV → DataFrame, 120 days × 96 intervals',
    civil_bullets=['Historian export', 'One row per interval', 'Four months'],
    ai_bullets=['read_csv', 'shape and dtypes', 'First look'],
    site="""The historian exports four months of fifteen-minute intervals: one row each, every channel, plus
the tariff that applied.""",
    challenge="""An export is not a dataset. An inverter writes a small negative at night, a meter drops out to
zero, an anemometer spikes.""",
    ai_link="""Loading it is the first step: shape, column types, and a first look at what actually arrived.""",
    notebook="""Section 4. `pd.read_csv`, `.shape`, `.head()`.""",
    contributes="""The dataset every later step reads from.""",
    takeaway="""The export is raw material. Loading it is where the data work starts.""",
),
dict(
    id='inspect', phase=2,
    civil='The Meter Health Check', ai='Data Inspection',
    civil_icon='🔍', ai_icon='📊',
    tech='Count gaps, negatives and impossible values',
    civil_bullets=['Did it report?', 'Is it possible?', 'Is it stuck?'],
    ai_bullets=['isna().sum()', 'describe()', 'Range checks'],
    site="""Before trusting four months of readings, check the instruments. Solar cannot be negative. Campus
demand cannot be zero. Wind cannot exceed the turbine rating.""",
    challenge="""Each of those faults writes a perfectly valid number. A −6 kW inverter offset at night looks
like a small export; a zero demand looks like a holiday.""",
    ai_link="""Inspection is that check in code, and it matters here because the label comes from an optimiser:
a bad input produces a confidently wrong *training example*, not just a bad row.""",
    notebook="""Section 5. `.isna().sum()`, `.describe()`, range checks per channel.""",
    contributes="""The fault list the cleaning step works from.""",
    takeaway="""A bad reading here does not just corrupt a prediction — it corrupts the label you learn from.""",
),
dict(
    id='clean', phase=3,
    civil='Correcting The Record', ai='Data Cleaning',
    civil_icon='🧹', ai_icon='🧼',
    tech='Clip the impossible, interpolate short gaps',
    civil_bullets=['Repair the channel', 'Keep the interval', 'Never invent a day'],
    ai_bullets=['Mask impossibles', 'Interpolate in time', 'Then re-derive net load'],
    site="""A faulty channel is corrected before it reaches a report. Nobody averages an anemometer spike into
a monthly wind yield and then defends the figure.""",
    challenge="""Dropping affected intervals breaks the *sequence*, and this problem is about sequences — a
battery decision at 19:00 depends on what happened at 03:00.""",
    ai_link="""So repair in place: mask the impossible, interpolate short gaps in time order, then re-derive net
load so it stays consistent with its parts.""",
    notebook="""Section 6. Mask, interpolate, and recompute `net_load_kw`.""",
    contributes="""A continuous record the optimiser can be run over.""",
    takeaway="""Repair in time order — deleting an interval breaks the sequence the battery lives in.""",
),
dict(
    id='features', phase=3,
    civil='Preparing The Inputs', ai='Feature Engineering',
    civil_icon='🔧', ai_icon='⚙️',
    tech='cyclical hour, published price ahead, imperfect forecast',
    civil_bullets=['23:45 is next to 00:00', 'The tariff is published', 'The forecast is not certain'],
    ai_bullets=['sin & cos of hour', 'price_max_next4h', 'solar_fc_next2h'],
    site="""Two things about the future are legitimately knowable at decision time: the tariff, because it is
published, and the weather, approximately, because there is a forecast.""",
    challenge="""Hour-of-day as a plain number tells the model that 23:45 and 00:00 are 24 units apart, when they
are fifteen minutes apart. And a *perfect* solar forecast would be cheating.""",
    ai_link="""Encode the hour as a point on a circle, add the published price for the next four hours, and add
a solar forecast with realistic error in it. That last column is why a model can save the battery for a
peak that has not arrived.""",
    notebook="""Section 7. Cyclical encoding, forward price, and a noisy forecast.""",
    contributes="""The columns that let a model beat a rule which sees only the present.""",
    takeaway="""Only what is knowable at decision time may be a feature — including the future, where it is published.""",
),
dict(
    id='split', phase=3,
    civil='Split By Day, Not By Row', ai='Honest Validation',
    civil_icon='✂️', ai_icon='🗂️',
    tech='whole days held out, never shuffled intervals',
    civil_bullets=['A day is the unit', 'Intervals are not independent', 'Hold out whole days'],
    ai_bullets=['Group split', 'No leakage', 'An honest score'],
    site="""Consecutive intervals are almost identical: the sun does not move much in fifteen minutes, and the
battery carries its state across.""",
    challenge="""Shuffle rows at random and 19:00 lands in training while 19:15 lands in test. The model has
effectively seen the answer, and the score becomes meaningless — flatteringly so.""",
    ai_link="""Split by **day**. Whole days go to training or to test, never both. The score then measures what
the controller would do on a day it has never seen.""",
    notebook="""Section 8. `GroupShuffleSplit` on the day index.""",
    contributes="""The sealed days the closed-loop evaluation runs on.""",
    takeaway="""Split by day. A random row split leaks tomorrow into today and flatters everything.""",
),
dict(
    id='rule', phase=4,
    civil='The Rule The Plant Already Runs', ai='The Baseline',
    civil_icon='📋', ai_icon='📐',
    tech='if peak and charged: discharge; if cheap and empty: charge',
    civil_bullets=['Simple', 'Defensible', 'Sees only now'],
    ai_bullets=['The bar to clear', 'Honest comparison', 'Often good enough'],
    site="""The controller a plant engineer would write, and it is a good one: at peak price with charge
available, discharge; at off-peak with room, charge; otherwise buy.""",
    challenge="""It is **myopic** — it sees only this interval. It will happily empty the battery at 8.00 Rs/kWh
at 16:00 and have nothing left when the price hits 11.50 at 19:00.""",
    ai_link="""This is the bar. Anything more complicated has to beat it in rupees, not in accuracy, and it must
be implemented properly before it is dismissed.""",
    notebook="""Section 9. The rule, run across a representative day.""",
    contributes="""The baseline every later number is compared against.""",
    takeaway="""A myopic rule spends the battery on the wrong hour, and no tuning fixes that.""",
),
dict(
    id='optimiser', phase=4,
    civil='What Was Actually Best', ai='Where The Labels Come From',
    civil_icon='🎯', ai_icon='🧠',
    tech='backward dynamic programming over state of charge',
    civil_bullets=['Whole day known', 'Exact answer', 'Impossible in real time'],
    ai_bullets=['Not an opinion', 'The training label', 'Perfect foresight'],
    site="""To train a model to make good decisions you need examples of good decisions. So: what *was* the
best thing to do at 14:00 last Tuesday?""",
    challenge="""That question has an exact answer, but only in hindsight — it needs the whole day in advance,
which no controller has.""",
    ai_link="""Dynamic programming solves each past day exactly, backwards from midnight over every state of
charge. The result is a provably cheapest schedule, and it becomes the label.""",
    notebook="""Section 10. `solve_day`, then a label for every interval.""",
    contributes="""The training target — and the yardstick regret is measured against.""",
    takeaway="""The label is not an expert's opinion. It is the provably cheapest action, computed in hindsight.""",
),
dict(
    id='trap', phase=4,
    civil='Learning Your Own Rule Back', ai='The Label Trap',
    civil_icon='🪤', ai_icon='⚠️',
    tech='train on rule labels vs optimiser labels',
    civil_bullets=['The rule is easy to copy', 'And it is wrong', 'Copying it locks it in'],
    ai_bullets=['99% accuracy', 'Zero improvement', 'The score lies'],
    site="""The tempting shortcut: label the history with what the existing controller did, and train on that.
The data is free and already there.""",
    challenge="""The model then learns the rule — including its mistakes — and scores near-perfect accuracy,
because copying a deterministic rule is easy. It has improved nothing.""",
    ai_link="""Label from the **optimiser** instead. Accuracy against those labels is lower, and the money saved
is higher. That gap is the single most important idea in this project.""",
    notebook="""Section 11. Train on both label sets and compare accuracy against cost.""",
    contributes="""The reason the optimiser exists at all.""",
    takeaway="""Learn from what was best, not from what was done — or you automate the mistakes at 99% accuracy.""",
),
dict(
    id='models', phase=5,
    civil='The Decision Model', ai='Tree, Forest, Boosting',
    civil_icon='🌳', ai_icon='🌲',
    tech='three classifiers on the same honest split',
    civil_bullets=['Which source?', 'From this row', 'Every interval'],
    ai_bullets=['One tree, readable', 'A forest, stronger', 'Boosting, strongest'],
    site="""The decision is a choice between five named options, so it is a classification problem — the same
shape as any other selection an engineer makes from measurements.""",
    challenge="""A single tree is readable but brittle. A forest is stronger but harder to explain, and an
operator will not accept a setpoint they cannot argue with.""",
    ai_link="""Fit all three on the same honest split and compare. The readable model is worth keeping even if
it loses slightly, because the readable one is the one that gets commissioned.""",
    notebook="""Section 12. Decision tree, random forest, gradient boosting.""",
    contributes="""The controller the rest of the project evaluates.""",
    takeaway="""The most accurate model is not automatically the one that gets installed.""",
),
dict(
    id='importance', phase=5,
    civil='What Drives The Decision', ai='Feature Importance',
    civil_icon='🎚️', ai_icon='📈',
    tech='which column moves the choice most',
    civil_bullets=['Price or charge?', 'Now or later?', 'Rank them'],
    ai_bullets=['feature_importances_', 'Check against physics', 'A sanity test'],
    site="""An engineer will ask what the model is actually keying on before letting it set anything.""",
    challenge="""Several columns move together — price, hour and net load all peak in the evening — so a
correlation table cannot separate them.""",
    ai_link="""Feature importance ranks how much each column changes the decision, and it is the first place
the model can be checked against what a power engineer already knows.""",
    notebook="""Section 13. `.feature_importances_`, sorted and plotted.""",
    contributes="""The sanity check that gets the model past a design review.""",
    takeaway="""If the ranking disagrees with the physics, trust the physics and go and find the leak.""",
),
dict(
    id='explain', phase=5,
    civil='Explaining One Decision', ai='The Decision Path',
    civil_icon='🔬', ai_icon='🧾',
    tech='the path a single row takes through the tree',
    civil_bullets=['Why this source?', 'At this instant?', 'In words'],
    ai_bullets=['Read the splits', 'One row, one path', 'Auditable'],
    site="""An operator asked to accept a setpoint at 19:15 will ask why. "The model said so" ends the
conversation badly.""",
    challenge="""A ranking explains the model in general. It does not explain *this* decision, at *this*
instant, which is what is actually being questioned.""",
    ai_link="""A tree's path for one row is a chain of plain conditions — price above 11, charge above 60 — and
reads back as an argument an engineer can agree or disagree with.""",
    notebook="""Section 14. Walk the decision path for a single interval.""",
    contributes="""The justification that makes a recommendation acceptable.""",
    takeaway="""A decision an operator cannot interrogate is a decision they will override.""",
),
dict(
    id='live', phase=5,
    civil='The Live Recommendation', ai='Inference',
    civil_icon='🎛️', ai_icon='⚡',
    tech='thirteen inputs → one recommended source',
    civil_bullets=['Set the conditions', 'Read the call', 'See the cost'],
    ai_bullets=['One row in', 'One class out', 'Plus the runner-up'],
    site="""This is what the controller does in service: take the current row and return a source.""",
    challenge="""A bare class is not enough for a control room. The operator needs the cost of the choice and
how close the second-best option was.""",
    ai_link="""Return the class, the probability, and the cost of every alternative in the same interval, so the
size of the decision is visible.""",
    notebook="""Section 15. `recommend()`, with the alternatives priced.""",
    contributes="""The interface the fusion screen is built on.""",
    takeaway="""Show what the alternatives would have cost, and the recommendation explains itself.""",
),
dict(
    id='regret', phase=6,
    civil='Why Accuracy Is The Wrong Score', ai='Regret In Rupees',
    civil_icon='💸', ai_icon='📉',
    tech='cost of the chosen action − cost of the best action',
    civil_bullets=['Some errors are free', 'Some are expensive', 'Accuracy cannot tell'],
    ai_bullets=['Score in money', 'Not in classes', 'Regret per interval'],
    site="""Two of the five classes often cost within a rupee of each other. Two others differ by hundreds.""",
    challenge="""Accuracy treats every mistake as equal. A model can be 92% accurate and expensive, or 84%
accurate and cheap, and the accuracy number will not tell you which is which.""",
    ai_link="""Score **regret**: what the chosen action cost, minus what the optimum would have cost. That is
the only number the plant actually experiences.""",
    notebook="""Section 16. Regret per interval, and accuracy against cost.""",
    contributes="""The metric everything after this is judged by.""",
    takeaway="""Score in rupees. Accuracy counts mistakes; regret prices them.""",
),
dict(
    id='closed-loop', phase=6,
    civil='A Month, Run Properly', ai='Closed-Loop Evaluation',
    civil_icon='🔄', ai_icon='🧪',
    tech='the controller drives the battery, its own errors compound',
    civil_bullets=['State carries over', 'Mistakes compound', 'Run the whole day'],
    ai_bullets=['Not row-by-row', 'Feed back the SOC', 'The honest test'],
    site="""In service the controller changes the state of charge, and that state is the input to the next
decision. Its own mistakes are its next inputs.""",
    challenge="""Scoring interval by interval against the optimiser hides that entirely: every row is handed the
*correct* state of charge, which the real controller would not have.""",
    ai_link="""Run the whole month closed-loop — the controller's own action sets the next state — for the rule,
the model and the optimum. Only that comparison is honest.""",
    notebook="""Section 17. `run_day` for each controller, over the sealed days.""",
    contributes="""The headline saving the business case uses.""",
    takeaway="""A controller must be tested driving its own state, or an early mistake is quietly forgiven.""",
),
dict(
    id='confusion', phase=6,
    civil='When It Is Wrong', ai='The Confusion Matrix That Costs Money',
    civil_icon='🧮', ai_icon='✅',
    tech='which confusions happen, and what each costs',
    civil_bullets=['Some swaps are harmless', 'One is not', 'Know which'],
    ai_bullets=['Confusion matrix', 'Weighted by cost', 'Not by count'],
    site="""Every wrong call is audited on the sealed days: which class was chosen, which was best, and what
the difference cost.""",
    challenge="""The usual confusion matrix counts mistakes. Here two of the confusions are nearly free and one
— discharging into a normal hour and having nothing at peak — is not.""",
    ai_link="""Plot the same matrix twice: once by count, once by rupees. They do not look alike, and the second
one is what the plant experiences.""",
    notebook="""Section 18. Confusion matrix by count and by cost.""",
    contributes="""The failure mode to watch in service.""",
    takeaway="""Count the confusions, then price them — the biggest cell is rarely the most expensive one.""",
),
dict(
    id='outage', phase=7,
    civil='When The Grid Fails', ai='The Rare Class',
    civil_icon='🛢️', ai_icon='🚨',
    tech='reliability, reserve, and value of lost load',
    civil_bullets=['Rare', 'Expensive', 'Non-negotiable'],
    ai_bullets=['Few examples', 'Huge cost', 'Never optimise it away'],
    site="""The grid goes down a few times a year. The battery covers some of it; past that, the diesel runs
or the campus goes dark.""",
    challenge="""Outages are 1% of the data, so a model optimising average cost will barely notice them — and a
model that learns to keep the battery empty at peak has no reserve when one arrives.""",
    ai_link="""Value of lost load makes the cost function reflect reality: not supplying is priced far above any
fuel. The reserve then has to be earned, not assumed.""",
    notebook="""Section 19. Outage days scored separately, with the reserve floor.""",
    contributes="""The constraint that keeps the recommendation safe as well as cheap.""",
    takeaway="""A rare class with a huge cost must be priced, not counted — or it optimises itself away.""",
),
dict(
    id='engine', phase=8,
    civil='The Dispatch Recommendation', ai='The Product',
    civil_icon='🖥️', ai_icon='🔗',
    tech='class + reason + rupees, per interval',
    civil_bullets=['One instruction', 'One reason', 'One number'],
    ai_bullets=['Model output', 'Decision path', 'Regret against optimum'],
    site="""By now every interval produces a recommended source, the path that produced it, and what the
alternatives would have cost.""",
    challenge="""A class on its own does not get accepted in a control room. An operator overrides what they
cannot interrogate.""",
    ai_link="""Fusion presents all three together: the setpoint, the plain-language reason, and the saving —
so the operator can agree, argue or override with the numbers in front of them.""",
    notebook="""Section 20. The recommendation screen.""",
    contributes="""The product — one screen an operator can act on.""",
    takeaway="""The class is the answer; the reason is what gets it accepted.""",
),
dict(
    id='dashboard', phase=8,
    civil='What It Is Worth', ai='Rupees & Carbon',
    civil_icon='📉', ai_icon='💷',
    tech='annual saving, diesel hours, carbon',
    civil_bullets=['Approve a spend', 'Against a saving', 'With a payback'],
    ai_bullets=['Saving vs the rule', 'Not vs doing nothing', 'Assumptions visible'],
    site="""The site manager does not buy a model. They approve a spend against a saving, with a payback.""",
    challenge="""The honest comparison is against the **existing rule**, not against an unmanaged microgrid.
Most of the saving is already being captured by the rule the plant runs today.""",
    ai_link="""The dashboard reports the closed-loop saving against the rule, in rupees and in litres of diesel
— every figure arithmetic on assumptions the reader can change.""",
    notebook="""Section 21. The business case, computed from the closed-loop result.""",
    contributes="""The reason the previous steps get funded.""",
    takeaway="""Report the saving against the rule you are replacing, not against doing nothing.""",
),
]

SHORT = {
    "microgrid": "The microgrid at 06:00", "sources": "Five sources, five costs",
    "reading": "One interval",            "load": "SCADA export arrives",
    "inspect": "Meter health check",      "clean": "Correcting the record",
    "features": "Preparing the inputs",   "split": "Split by day",
    "rule": "The rule already run",       "optimiser": "What was actually best",
    "trap": "The label trap",             "models": "The decision model",
    "importance": "What drives it",       "explain": "Explaining one decision",
    "live": "The live recommendation",    "regret": "Regret in rupees",
    "closed-loop": "A month, closed-loop", "confusion": "When it is wrong",
    "outage": "When the grid fails",      "engine": "The recommendation",
    "dashboard": "What it is worth",
}
for _s in STEPS:
    _s["short"] = SHORT[_s["id"]]

QUIZ = {
    'microgrid': dict(
        q="Why can a plant engineer not simply make each dispatch decision by hand?",
        options=["The decisions are too technical",
                 "There are 96 a day, and each depends on a price four hours away, the state of charge and a forecast",
                 "SCADA does not allow manual control",
                 "The battery decides for itself"],
        answer=1, why="35,000 decisions a year, each needing information about hours that have not happened yet."),
    'sources': dict(
        q="Why is a battery discharge not free even though the stored energy was cheap?",
        options=["Batteries are always expensive",
                 "Because it costs the charge price ÷ round-trip efficiency, plus per-kWh wear on the cells",
                 "Because discharging needs the grid",
                 "It is free"],
        answer=1, why="Charge at 8.00 instead of 4.50 and the saving against an 11.50 peak nearly vanishes."),
    'reading': dict(
        q="Which of these may legitimately be a feature at decision time?",
        options=["The actual solar output over the next two hours",
                 "The published tariff for the next four hours",
                 "Tomorrow's measured demand",
                 "The optimiser's answer"],
        answer=1, why="The tariff is published, so knowing it is not cheating. Actual future output is."),
    'load': dict(
        q="Why is a SCADA export not yet a dataset?",
        options=["Wrong file format",
                 "It contains negative solar, zero demand and anemometer spikes — all valid-looking numbers",
                 "It is too large",
                 "It has no header row"],
        answer=1, why="Each fault writes a plausible number, which is exactly why they must be looked for."),
    'inspect': dict(
        q="Why does a bad reading matter more in this project than in a pure prediction project?",
        options=["It does not",
                 "Because the training label comes from an optimiser run on the data — a bad input produces a confidently wrong label",
                 "Because SCADA is expensive",
                 "Because it changes the file size"],
        answer=1, why="You are not just corrupting a prediction; you are corrupting what the model learns is correct."),
    'clean': dict(
        q="Why interpolate a bad interval instead of dropping it?",
        options=["Interpolation is more accurate",
                 "Because dropping it breaks the sequence, and the battery carries state from one interval to the next",
                 "Because pandas requires it",
                 "To keep the file size constant"],
        answer=1, why="This is a sequential control problem; a hole in the day is not a neutral omission."),
    'features': dict(
        q="Why encode the hour as sine and cosine?",
        options=["It compresses better",
                 "So that 23:45 sits next to 00:00 instead of 24 units away from it",
                 "Because trees need continuous inputs",
                 "To remove the units"],
        answer=1, why="Both 23:45→00:00 and 11:45→12:00 are fifteen minutes apart. Only the circular encoding agrees."),
    'split': dict(
        q="Why split by day rather than by row?",
        options=["Days are easier to count",
                 "Because 19:00 and 19:15 are nearly identical — a random split puts the answer in training and flatters the score",
                 "Because sklearn requires it",
                 "To balance the classes"],
        answer=1, why="Consecutive intervals are not independent, so a row split leaks."),
    'rule': dict(
        q="What is the flaw in the plant's existing rule?",
        options=["It is too complicated",
                 "It is myopic: it sees only this interval, so it can empty the battery before the expensive hour arrives",
                 "It ignores the battery",
                 "It uses too much diesel"],
        answer=1, why="No amount of tuning fixes a controller that cannot look ahead."),
    'optimiser': dict(
        q="Why is dynamic programming used to make the labels rather than an expert's judgement?",
        options=["It is faster",
                 "Because given the whole day it computes the provably cheapest schedule — the label is a fact, not an opinion",
                 "Because experts are unavailable",
                 "Because it works in real time"],
        answer=1, why="It needs perfect hindsight, which is exactly why it cannot be the controller — only the teacher."),
    'trap': dict(
        q="A model trained on the existing rule's decisions scores 99% accuracy. What has been achieved?",
        options=["An excellent controller",
                 "Nothing — it has learned to copy the rule, including its mistakes, and saves no money",
                 "A faster version of the rule",
                 "A more accurate optimiser"],
        answer=1, why="Copying a deterministic rule is easy and improves nothing. Label from the optimum instead."),
    'models': dict(
        q="Why might the single decision tree be preferred over the more accurate forest?",
        options=["It trains faster",
                 "Because an operator can read its decision path and argue with it — and a setpoint nobody can interrogate gets overridden",
                 "It uses less memory",
                 "Forests cannot classify"],
        answer=1, why="The most accurate model is not automatically the one that gets commissioned."),
    'importance': dict(
        q="Feature importance ranks state of charge above price. What should you do?",
        options=["Accept it — the model knows best",
                 "Check it against the physics: if it disagrees with what a power engineer expects, look for a leak or a labelling error",
                 "Delete the price column",
                 "Retrain with fewer features"],
        answer=1, why="Importance is a sanity check, not a proof. Disagreement with physics is a signal."),
    'explain': dict(
        q="What does the decision path add over feature importance?",
        options=["Higher accuracy",
                 "It explains THIS decision at THIS instant, which is what the operator is actually questioning",
                 "A faster prediction",
                 "A smaller model"],
        answer=1, why="Importance explains the model in general; the path explains the one call being argued about."),
    'live': dict(
        q="Why show what the alternatives would have cost?",
        options=["To fill the screen",
                 "Because it shows the SIZE of the decision — a close call and an obvious one look completely different",
                 "Because the model is unreliable",
                 "To slow the operator down"],
        answer=1, why="If second-best costs a rupee more, an override is harmless. If it costs 600, it is not."),
    'regret': dict(
        q="Why is regret in rupees a better score than decision accuracy?",
        options=["Rupees are easier to compute",
                 "Because some class confusions cost almost nothing and others cost hundreds — accuracy treats them as equal",
                 "Because accuracy is always wrong",
                 "Because managers prefer money"],
        answer=1, why="A 92%-accurate expensive controller and an 84%-accurate cheap one score the same on accuracy."),
    'closed-loop': dict(
        q="Why must the evaluation be closed-loop?",
        options=["It is faster",
                 "Because the controller changes the state of charge, so its own mistakes become its next inputs — interval scoring hands it the correct state it would not have",
                 "Because the optimiser needs it",
                 "To use the whole dataset"],
        answer=1, why="Open-loop scoring quietly forgives every early mistake."),
    'confusion': dict(
        q="Why plot the confusion matrix by cost as well as by count?",
        options=["It looks better",
                 "Because the most frequent confusion is often nearly free, while a rare one is very expensive",
                 "Because counts are unreliable",
                 "To fill the page"],
        answer=1, why="The plant experiences the cost matrix, not the count matrix."),
    'outage': dict(
        q="Why price value of lost load so high?",
        options=["To make the numbers larger",
                 "Because outages are 1% of the data — without a large cost the optimiser learns to keep no reserve and the model copies that",
                 "Because diesel is expensive",
                 "Regulations require it"],
        answer=1, why="A rare class with a real cost must be priced, or an average-cost objective optimises it away."),
    'engine': dict(
        q="What does the recommendation screen add over the raw class?",
        options=["Higher accuracy",
                 "The reason and the rupee figure — the two things that decide whether an operator accepts or overrides it",
                 "Faster inference",
                 "Less storage"],
        answer=1, why="A class is the answer; the reason is what gets it accepted."),
    'dashboard': dict(
        q="What should the annual saving be measured against?",
        options=["An unmanaged microgrid with no controller",
                 "The existing rule the plant already runs, because most of the easy saving is already being captured",
                 "The perfect-foresight optimum",
                 "Diesel-only operation"],
        answer=1, why="Comparing against doing nothing overstates the benefit of the model by a wide margin."),
}

START = dict(
    project_line="one microgrid dispatch project",
    problem="""
A campus microgrid has **solar, wind, a battery, a grid connection and a diesel set**. Every **fifteen
minutes** somebody has to decide where the next block of energy comes from — **96 decisions a day**. The
grid tariff is **4.50 off-peak, 8.00 normal and 11.50 at the evening peak**, diesel is 21 all day, and a
battery cycle costs whatever charged it plus wear. The surplus arrives at midday; the expensive hours are
18:00–22:00. **They do not overlap.** The job: **choose the cheapest source, every interval, without a
crystal ball.**
""",
    build_intro="A **dispatch decision-support system** for the microgrid. Four parts:",
    cards=[
        ("📟", "SCADA reads the microgrid",
         "Demand, solar, wind, state of charge, tariff, grid availability and temperature — every fifteen "
         "minutes, plus the published price ahead and an imperfect solar forecast."),
        ("🎯", "An optimiser says what was best",
         "Dynamic programming solves each past day exactly, backwards over every state of charge. Not an "
         "opinion — the provably cheapest schedule, computed in hindsight."),
        ("🌳", "A model learns that mapping",
         "A classifier over the thirteen observable columns reproduces the optimiser's choice in real "
         "time, from information a controller actually has."),
        ("🔔", "The operator gets a setpoint",
         "Not a black box. A source, the plain-language reason, and what the alternatives would have "
         "cost — so a person can agree, argue or override."),
    ],
    promise="""The plant engineer stays in charge and stays accountable. The system handles the part one
person cannot: it makes a defensible choice 96 times a day, every day, and prices every alternative next to
it. The goal is <b>Electrical Engineer + AI</b> — a microgrid that runs on evidence rather than on a rule
nobody has revisited.""",
    map_note="""<b>Every AI concept here is an electrical activity you already understand</b> — the same
thing, named differently by a different profession. Read down the amber column and you have described a
dispatch study. Read down the cyan column and you have described a supervised learning pipeline. They are
the same column.""",
)

_m = sys.modules[__name__]
BY_ID, ORDER = scaffold.lookups(_m)
inject_css = lambda: scaffold.inject_css(_m)
open_page = lambda stage: scaffold.open_page(_m, stage)
close_page = lambda stage: scaffold.close_page(_m, stage)
render_start = lambda: scaffold.render_start(_m)
route = lambda STAGES, ALIASES=None: scaffold.route(_m, STAGES, ALIASES)
