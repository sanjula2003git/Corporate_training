"""
bridge.py — the Electrical-Power-Engineering -> AI teaching content.
====================================================================
All the machinery lives in scaffold.py. This module only declares WHAT this
project teaches: its phases, its steps, its quiz and its opening page.
"""
import sys
import scaffold

THEME = dict(
    title="AI for Transformer Maintenance Decision Support",
    icon="⚡",
    dwg="AM-TX-001",
    civil_label="Electrical Power Engineering",
    civil_kicker="IN THE SUBSTATION",
    station="⟨FLEET·TX094⟩",
    rail="ASSET",
    start_button="▶  Start: walk into the substation",
    sidebar_title="An Asset Management Problem",
    sidebar_note="You are ranking four hundred transformers by risk — and no model may de-energise one.",
    backdrop=("linear-gradient(rgba(255,255,255,.02) 1px, transparent 1px),"
              "linear-gradient(90deg, rgba(255,255,255,.02) 1px, transparent 1px)"),
)

PHASES = [
    ("The Asset",             "One transformer, twenty thousand customers, no spare."),
    ("One Inspection",        "A condition assessment becomes a written record."),
    ("The Fleet Log",         "The asset-management export lands and gets checked."),
    ("Preparing The Data",    "Faulty readings out, the fleet split by unit."),
    ("Health From Sensors",   "The rulebook, then the model that extends it."),
    ("The Image Wall",        "The infrared survey arrives and the rulebook collapses."),
    ("Reading The Heat",      "A CNN grades a thermal survey no rule could grade."),
    ("The Maintenance Audit", "Every recommendation checked against the engineer's decision."),
    ("Decision Support",      "One recommendation, with its reasoning and its confidence."),
]

_S = lambda **k: k
STEPS = [
_S(id='asset', phase=0, civil='A Transformer In Service', ai='Why Asset Management Needs AI',
   civil_icon='⚡', ai_icon='🤖', tech='exponential insulation ageing against load',
   civil_bullets=['No spare', 'Forty-year design life', 'Failure is not gradual'],
   ai_bullets=['Rank the fleet', 'Every week', 'By risk, with a reason'],
   site="""A power transformer serves twenty thousand customers. There is no spare, the lead time on a
replacement is a year, and its insulation ages exponentially with hot-spot temperature.""",
   challenge="""Assessment is a calendar activity: an oil sample takes a fortnight to come back, an infrared
survey needs an engineer on site, and neither happens more than twice a year.""",
   ai_link="""The question is not "is this unit bad" but "which of these four hundred should I look at
first" — a ranking across a fleet, weekly, which no engineer can maintain by hand.""",
   notebook="""Section 1. The IEEE C57.91 thermal model and the ageing acceleration factor.""",
   contributes="""The requirement, and the physics the health index is built on.""",
   takeaway="""Insulation ageing roughly doubles every 6–7 K above the reference hot spot."""),
_S(id='monitoring', phase=0, civil='Continuous Condition Monitoring', ai='The Monitoring Layer',
   civil_icon='📡', ai_icon='🛰️', tech='online DGA, fibre hot spot, scheduled infrared',
   civil_bullets=['Engineers stay', 'Standards stay', 'Nobody is replaced'],
   ai_bullets=['A ranked worklist', 'Not a decision', 'You still sign it'],
   site="""Nothing about the transformer changes. What changes is the rate of information: online
dissolved-gas monitors, a fibre hot-spot probe, and an infrared survey on a schedule.""",
   challenge="""The usual objection: is this here to replace the asset engineer? No. De-energising a unit is
a statutory and safety decision, and no model signs one.""",
   ai_link="""The system produces a ranked worklist with reasons. That split — it recommends, a person
decides — governs every later design choice, especially how the audit is scored.""",
   notebook="""No code. This step is the argument, not the arithmetic.""",
   contributes="""Defines the output: a recommendation, never an automatic switching action.""",
   takeaway="""The output is a ranked worklist with reasons, not a decision."""),
_S(id='reading', phase=1, civil='One Condition Assessment', ai='Data Collection',
   civil_icon='📋', ai_icon='🗄️', tech='seventeen measurements → one health index',
   civil_bullets=['Seven gases', 'Moisture and BDV', 'Thermal history'],
   ai_bullets=['One row per assessment', '17 features', 'One target'],
   site="""An assessment gathers dissolved gases, moisture, breakdown voltage, partial discharge, load and
temperature history — and the ageing rate that follows from them.""",
   challenge="""Seventeen numbers on a laboratory report, each with its own limit in a different standard.
Combining them into one defensible condition score is exactly what takes experience.""",
   ai_link="""Put them in one row with a health index and the assessment becomes a training example.
Thousands of them are a dataset — and the index is a formula whose weights are stated, not hidden.""",
   notebook="""Section 2. The gas signatures, the health index, and one assessment record.""",
   contributes="""The unit of learning, and the target the models predict.""",
   takeaway="""Acetylene needs an arc to form. Its limit is 2 ppm while ethylene's is 150."""),
_S(id='two-records', phase=1, civil='Test Report vs Thermal Survey', ai='Two Kinds Of Data',
   civil_icon='🧾', ai_icon='🔀', tech='17 named values, or 4,096 unnamed pixels',
   civil_bullets=['The oil report', 'The infrared survey', 'Same unit, two views'],
   ai_bullets=['Named columns → ML', 'Raw pixels → DL', 'The fork in the road'],
   site="""Two records describe the same unit: a laboratory report with seventeen named values, and a
thermal survey with 4,096 unnamed temperatures.""",
   challenge="""They see different faults. A blocked radiator bank produces **no gas at all** — the oil
report is blind to it, and the survey is the only record that can see it.""",
   ai_link="""Named columns suit Machine Learning; raw pixels do not. Here the two are not merely different
formats — they detect genuinely different failure modes.""",
   notebook="""Section 2. Print one report, then show one survey as an array.""",
   contributes="""The fork: measurements go to ML, images go to DL.""",
   takeaway="""A cooling fault produces no gas. Only the survey can see it."""),
_S(id='load', phase=2, civil='The Fleet Log Arrives', ai='Loading The Dataset',
   civil_icon='📥', ai_icon='🐼', tech='CSV → DataFrame, 400 units, ~1,200 assessments',
   civil_bullets=['Asset-management export', 'One row per assessment', 'Several per unit'],
   ai_bullets=['read_csv', 'shape and dtypes', 'First look'],
   site="""The asset-management system exports the fleet history: one row per condition assessment, several
assessments per unit, across four hundred transformers.""",
   challenge="""An export is not a dataset. Laboratory results come back below the detection limit as
negatives or blanks, and the same assessment gets loaded twice.""",
   ai_link="""Loading it is the first step: shape, column types, and how the assessments are distributed
across units — which is what decides how the split must be done.""",
   notebook="""Section 3. `pd.read_csv`, `.shape`, `.head()`.""",
   contributes="""The dataset every later step reads from.""",
   takeaway="""Several assessments per unit is not an incidental detail — it decides the split."""),
_S(id='inspect', phase=2, civil='Checking The Records', ai='Data Inspection',
   civil_icon='🔍', ai_icon='📊', tech='Count gaps, negatives and impossible values',
   civil_bullets=['Below detection limit', 'Impossible BDV', 'Duplicated assessments'],
   ai_bullets=['isna().sum()', 'describe()', 'duplicated()'],
   site="""Before trusting a fleet history, check it. A gas below the laboratory's detection limit is not
zero and not missing — it is "less than 0.5 ppm", which is a third kind of value.""",
   challenge="""Recorded as a negative or a blank, it becomes either an impossible measurement or a hole. Both
are wrong, and acetylene — the gas that matters most — is the one usually below the limit.""",
   ai_link="""Inspection finds all three cases. How they are handled is a modelling decision with a real
consequence, because a false acetylene reading changes a unit's whole classification.""",
   notebook="""Section 4. `.isna().sum()`, `.describe()`, `.duplicated()`.""",
   contributes="""The fault list the cleaning step works from.""",
   takeaway="""'Below the detection limit' is not zero and not missing. It is a third kind of value."""),
_S(id='clean', phase=3, civil='Removing The Faulty Readings', ai='Data Cleaning',
   civil_icon='🧹', ai_icon='🧼', tech='half the detection limit; drop the impossible',
   civil_bullets=['Repair the value', 'Keep the assessment', 'Follow the convention'],
   ai_bullets=['DL/2 substitution', 'Mask impossibles', 'Document it'],
   site="""Laboratories have a convention for values below the detection limit: substitute half the limit.
It is arbitrary, it is standard, and it is written down.""",
   challenge="""Substituting zero says the gas is definitely absent, which is stronger than the measurement
supports. Deleting the row throws away sixteen good measurements.""",
   ai_link="""Half the detection limit is the defensible middle. What matters more than the choice is that
the choice is recorded, because it changes borderline acetylene classifications.""",
   notebook="""Section 5. `DETECT_LIMIT/2` substitution and physical range checks.""",
   contributes="""A dataset where every value is either measured or explicitly imputed.""",
   takeaway="""Substitute half the detection limit, and write down that you did."""),
_S(id='split', phase=3, civil='Known Units vs Sealed Units', ai='Grouped Train / Test Split',
   civil_icon='🗂️', ai_icon='✂️', tech='split by UNIT, never by assessment',
   civil_bullets=['A unit is the subject', 'Assessments repeat on it', 'Hold out whole units'],
   ai_bullets=['Group split', 'No leakage', 'An honest score'],
   site="""Each transformer contributes several assessments. Two assessments of the same unit six months
apart are far more alike than two assessments of different units.""",
   challenge="""Split by assessment and the same transformer appears in training and in test. The model
recognises the unit rather than the condition, and the score is flatteringly wrong.""",
   ai_link="""Split by **unit**. Every assessment of a given transformer goes to one side or the other. The
score then answers the real question: what would this say about a unit it has never seen?""",
   notebook="""Section 6. `GroupShuffleSplit` on `unit_id`.""",
   contributes="""The sealed units the audit runs on.""",
   takeaway="""Split by unit. Splitting by assessment lets the model recognise the transformer, not the fault."""),
_S(id='duval', phase=4, civil='The Duval Triangle', ai='The Expert Rulebook',
   civil_icon='🔺', ai_icon='📐', tech='CH4 / C2H4 / C2H2 percentages → a fault zone',
   civil_bullets=['Published in IEC 60599', 'Used everywhere', 'Genuinely good'],
   ai_bullets=['A hand-built classifier', 'The bar to clear', 'And its blind spots'],
   site="""The Duval Triangle is how the industry reads dissolved gas: normalise methane, ethylene and
acetylene to percentages, plot the point, and read the fault zone.""",
   challenge="""It is a good method with two known limits. It uses **three of the seven gases** and ignores
moisture, breakdown voltage, age and thermal history entirely — and it names a fault type without
saying how urgent it is.""",
   ai_link="""So the model is not replacing Duval. It is extending it: same gases, plus the fourteen other
measurements, producing a condition band rather than a fault name.""",
   notebook="""Section 7. `duval_zone`, plotted on the triangle.""",
   contributes="""The expert baseline the model must respect and extend.""",
   takeaway="""Duval names the fault; it does not say how urgent it is or use the other fourteen measurements."""),
_S(id='health-model', phase=4, civil='Health From The Measurements', ai='Classification & Regression',
   civil_icon='🩺', ai_icon='🌲', tech='17 measurements → health index → four condition bands',
   civil_bullets=['One score', 'Four bands', 'Four responses'],
   ai_bullets=['Regress the index', 'Classify the band', 'Probabilities matter'],
   site="""Utility practice puts a unit in one of four bands — healthy, minor degradation, moderate risk,
high risk — and each band has a different maintenance response.""",
   challenge="""The boundaries between bands are conventions, so a unit at 69 and one at 71 get different
responses despite being indistinguishable. That is a real problem, not a modelling artefact.""",
   ai_link="""Predict the index as a number and the band as a class. Where the class is borderline, the
probability says so — and a borderline case is exactly where an engineer should be asked.""",
   notebook="""Section 8. `RandomForestRegressor` for the index, classifier for the band.""",
   contributes="""The numeric half of the system.""",
   takeaway="""Report the band and its confidence: a unit at 69 and one at 71 are not really different."""),
_S(id='drivers', phase=4, civil='What Drives The Assessment', ai='Feature Importance',
   civil_icon='🎚️', ai_icon='📈', tech='which measurement moves the condition band',
   civil_bullets=['Gas or moisture?', 'Age or thermal history?', 'Rank them'],
   ai_bullets=['feature_importances_', 'Check against IEC', 'A sanity test'],
   site="""An engineer will ask which measurement drove a classification before acting on it.""",
   challenge="""The measurements move together — an old unit runs hotter, ages faster and generates more
gas — so a correlation table cannot separate cause from consequence.""",
   ai_link="""Feature importance ranks how much each measurement changes the prediction, and it is the first
place the model can be checked against IEC 60599 and against experience.""",
   notebook="""Section 8. `.feature_importances_`, sorted and plotted.""",
   contributes="""The sanity check that gets the model past an asset review.""",
   takeaway="""If the ranking disagrees with the standard, find out why before trusting either."""),
_S(id='survey-problem', phase=5, civil='The Infrared Survey', ai='The Raw Image',
   civil_icon='📷', ai_icon='🖼️', tech='a 64x64 grid of temperatures, no named columns',
   civil_bullets=['Hot spot = fault', 'COLD radiator = fault', 'Warm all over = sunshine'],
   ai_bullets=['4,096 numbers', 'No column names', 'Nothing to weight'],
   site="""An infrared survey photographs the tank, the radiator bank and the bushings. Bright is hot.""",
   challenge="""The faults point in opposite directions. A hot connection is a bright spot; a blocked
radiator is a **cold** region where a warm one should be; sunshine makes everything warm and is not a
fault at all.""",
   ai_link="""This is where Machine Learning runs out — no named features exist. And it is where the single
most common hand-written rule, a maximum-temperature alarm, is structurally incapable of helping.""",
   notebook="""Section 9. Build a survey as an array and display it.""",
   contributes="""The data type that forces the second half of the course.""",
   takeaway="""A cooling fault is evidence made of ABSENT heat. No maximum can express that."""),
_S(id='handmade', phase=5, civil='Setting A Temperature Alarm', ai='Hand-Made Features',
   civil_icon='✋', ai_icon='🔢', tech='hottest pixel — and what it loses',
   civil_bullets=['Take the maximum', 'Set a limit', 'Exactly as before'],
   ai_bullets=['One feature', 'One threshold', 'It cannot work'],
   site="""The standard shortcut: take the hottest pixel in the survey and alarm above a limit. It is what
every thermographic inspection procedure already says.""",
   challenge="""It works on a glowing connection and is **structurally incapable** of detecting a cooling
fault, at any limit — because the evidence there is the absence of heat.""",
   ai_link="""And raising the limit to exclude a sunlit unit pushes it past the hot bushing too. The feature
was hand-made and it discards the one thing that matters: where the heat is relative to where it
should be.""",
   notebook="""Section 10. Maximum temperature across all five survey types.""",
   contributes="""The failed baseline that justifies the CNN.""",
   takeaway="""No threshold on the hottest pixel can detect a radiator that has gone cold."""),
_S(id='cnn-journey', phase=6, civil='Reading The Thermal Pattern', ai='Convolution & Feature Maps',
   civil_icon='🧩', ai_icon='🔬', tech='filters → feature maps → three classes',
   civil_bullets=['A regular comb of radiators', 'A gap in it', 'A bright spot on a bushing'],
   ai_bullets=['Filters slide', 'Edges → structure', 'Three classes, not two'],
   site="""A thermographer does not read a maximum. They read structure: a healthy radiator bank is a
regular pattern, and a fault is a break in it.""",
   challenge="""That structure cannot be captured by any single pixel value, and it moves — every survey is
taken from a slightly different position.""",
   ai_link="""A convolution reports where its pattern occurs. A healthy radiator bank produces a regular comb
of vertical edges; a blocked bank leaves a gap in that comb.""",
   notebook="""Section 11. Convolve a survey by hand, then train a small CNN.""",
   contributes="""The visual half of the system: three classes for every survey.""",
   takeaway="""The network learns the regular pattern of a healthy bank — so a gap in it becomes evidence."""),
_S(id='thermal-locate', phase=6, civil='Which Part Of The Transformer?', ai='Grad-CAM',
   civil_icon='📍', ai_icon='🗺️', tech='class-weighted feature maps → heat map',
   civil_bullets=['Bushing or radiator?', 'Different trade', 'Different outage'],
   ai_bullets=['Weight the maps', 'Project onto the survey', 'Show the evidence'],
   site="""A hot bushing and a blocked radiator have similar urgency and completely different work: a
different trade, different parts, and a different outage requirement.""",
   challenge="""A classifier outputs a class. Without a location it cannot be planned against, and an engineer
asked to book an outage on a bare class will not do it.""",
   ai_link="""Grad-CAM projects the evidence back onto the survey. On a sunlit unit the map stays flat —
because nothing stands out against its own surroundings, which is exactly the distinction a maximum
cannot make.""",
   notebook="""Section 12. Grad-CAM over the trained CNN.""",
   contributes="""The location that makes the work order plannable.""",
   takeaway="""On a sunlit unit the attention map stays flat. That is the distinction a maximum cannot make."""),
_S(id='audit', phase=7, civil='The Maintenance Audit', ai='Confusion, Weighted By Consequence',
   civil_icon='🧮', ai_icon='✅', tech='over-cautious vs under-cautious, and what each costs',
   civil_bullets=['Recommended vs decided', 'On sealed units', 'Every claim checked'],
   ai_bullets=['Not symmetric', 'One error is 65× the other', 'Recall on High Risk'],
   site="""Every recommendation is audited against what the asset engineer actually decided, on units the
model was never allowed to see.""",
   challenge="""The two errors are not remotely equal. Being more cautious than the engineer costs an
unnecessary visit. Downgrading a high-risk unit risks a failure, an outage and an emergency
replacement.""",
   ai_link="""So the matrix is read as **over-cautious versus under-cautious**, and the number reported is
the share of genuinely high-risk units correctly escalated — not overall accuracy.""",
   notebook="""Section 13. Confusion matrix, and the two costs.""",
   contributes="""The honest performance number the project is judged on.""",
   takeaway="""An unnecessary visit costs thousands; a missed high-risk unit costs hundreds of thousands."""),
_S(id='proof', phase=7, civil='The Verdict', ai='Rulebook vs Model vs CNN',
   civil_icon='⚔️', ai_icon='🏁', tech='the same fleet, three methods, measured',
   civil_bullets=['Duval', 'The model', 'The camera'],
   ai_bullets=['Each sees different faults', 'None is redundant', 'Say which and why'],
   site="""Three methods have now been applied to the same fleet. Time to state plainly what each can and
cannot see.""",
   challenge="""It is tempting to declare the CNN the winner. It cannot detect a developing thermal fault
inside the winding at all — that appears in the oil, months before anything shows on a survey.""",
   ai_link="""Score all three on the same sealed units. Duval names electrical fault types from three gases;
the model ranks condition from seventeen measurements; the CNN sees cooling faults that produce no
gas. **The overlap is small, which is why all three stay.**""",
   notebook="""Section 14. The comparison table, filled in from measured results.""",
   contributes="""The course's central claim, demonstrated rather than asserted.""",
   takeaway="""These methods do not compete — they see different faults. Removing any one creates a blind spot."""),
_S(id='decision-screen', phase=8, civil='The Decision Support Screen', ai='Recommendation With Reasons',
   civil_icon='🎛️', ai_icon='🔗', tech='class + reason + confidence',
   civil_bullets=['What to do', 'Why', 'How sure'],
   ai_bullets=['Model output', 'Threshold breaches', 'Calibrated probability'],
   site="""By now each assessment produces a condition band, a set of measurements outside their limits, and
a thermal grade with a location.""",
   challenge="""A band alone is a number. An engineer accountable under the standards will not act on it, and
should not.""",
   ai_link="""Every row carries three things: the class, the reason in the language of IEC 60599, and the
confidence — so a borderline call looks borderline instead of authoritative.""",
   notebook="""Section 15. `reasons_for`, and the recommendation screen.""",
   contributes="""The product — one screen an asset engineer can act on.""",
   takeaway="""'Acetylene at 6.2 ppm against a limit of 2' is an argument. A health index of 41 is a number."""),
_S(id='fleet', phase=8, civil='The Fleet Screen', ai='Ranking, Not Classifying',
   civil_icon='🖥️', ai_icon='📊', tech='four hundred units, sorted by risk',
   civil_bullets=['Limited budget', 'Limited outages', 'Which ones first?'],
   ai_bullets=['Rank, do not label', 'Top of the list', 'Re-rank every week'],
   site="""The real question is never "is TX094 healthy". It is "I can inspect twelve units this quarter —
which twelve?".""",
   challenge="""A classifier answers a different question. Told that ninety units are 'moderate risk', the
engineer is no further forward than before.""",
   ai_link="""So the fleet screen **ranks** rather than labels: units ordered by predicted risk, with the
budget line drawn across the list. That converts a classification into a plan.""",
   notebook="""Section 16. The fleet, ranked, with an inspection budget applied.""",
   contributes="""The form the output has to take to be used at all.""",
   takeaway="""A ranked list with a budget line is a plan. A pile of 'moderate risk' labels is not."""),
_S(id='dashboard', phase=8, civil='What It Is Worth', ai='Failures Avoided & Cost',
   civil_icon='💷', ai_icon='📉', tech='avoided failures vs unnecessary visits',
   civil_bullets=['Approve a spend', 'Against a saving', 'With the risk stated'],
   ai_bullets=['Failures avoided', 'Visits wasted', 'Both in the total'],
   site="""The asset manager approves a spend against avoided failures — with the cost of the extra
inspections the system generates included, not hidden.""",
   challenge="""It is easy to count avoided failures and quietly ignore the unnecessary visits. A system that
escalates everything avoids every failure and is useless.""",
   ai_link="""The dashboard nets the two off: the value of failures prevented minus the cost of visits that
found nothing — every figure arithmetic on assumptions the reader can change.""",
   notebook="""Section 17. The business case, with both costs.""",
   contributes="""The reason the previous steps get funded.""",
   takeaway="""Subtract the wasted visits, or a system that escalates everything looks perfect."""),
]

SHORT = {
    "asset": "A transformer in service", "monitoring": "Continuous monitoring",
    "reading": "One assessment",         "two-records": "Report vs survey",
    "load": "The fleet log arrives",     "inspect": "Checking the records",
    "clean": "Faulty readings out",      "split": "Known vs sealed units",
    "duval": "The Duval Triangle",       "health-model": "Health from measurements",
    "drivers": "What drives it",         "survey-problem": "The infrared survey",
    "handmade": "A temperature alarm",   "cnn-journey": "Reading the pattern",
    "thermal-locate": "Which part?",     "audit": "The maintenance audit",
    "proof": "The verdict",              "decision-screen": "Decision support",
    "fleet": "The fleet screen",         "dashboard": "What it is worth",
}
for _s in STEPS:
    _s["short"] = SHORT[_s["id"]]

_q = lambda q, o, a, w: dict(q=q, options=o, answer=a, why=w)
QUIZ = {
    'asset': _q("Why is insulation ageing such a steep function of temperature?",
                ["It is linear with load", "The IEEE ageing factor is exponential — roughly a doubling every 6–7 K above 110 °C",
                 "It only matters above 150 °C", "It depends only on age"], 1,
                "A few degrees of sustained overload can consume years of design life."),
    'monitoring': _q("What is the system's actual output?",
                     ["An automatic trip", "A replacement for the asset engineer",
                      "A ranked worklist with reasons, which an engineer decides on", "A monthly report"], 2,
                     "De-energising a transformer is a statutory and safety decision. No model signs one."),
    'reading': _q("Why is acetylene's limit 2 ppm when ethylene's is 150?",
                  ["It is more toxic", "Because acetylene needs an ARC to form — its presence at all indicates a discharge fault",
                   "It is harder to measure", "It is a laboratory convention"], 1,
                  "Thermal faults generate ethylene routinely; only an arc generates acetylene."),
    'two-records': _q("Why can the oil report not detect a blocked radiator bank?",
                      ["The laboratory is too slow", "Because a cooling fault generates no gas at all — there is nothing in the oil to find",
                       "Because radiators are outside the tank", "It can detect it"], 1,
                      "The two records detect genuinely different failure modes, not the same one twice."),
    'load': _q("Why does 'several assessments per unit' matter so much?",
               ["It makes the file larger", "Because it decides how the split must be done — assessments of the same unit are not independent",
                "It slows down training", "It does not matter"], 1,
               "Two assessments of one transformer are far more alike than two of different units."),
    'inspect': _q("A gas result comes back as '< 0.5 ppm'. What kind of value is that?",
                  ["Zero", "Missing", "A third kind: censored — known to be below the detection limit, but not known to be zero",
                   "An error"], 2,
                  "Recording it as zero claims more than the measurement supports; as missing throws it away."),
    'clean': _q("Why substitute half the detection limit?",
                ["It is the most accurate", "Because it is the standard, defensible middle between claiming zero and discarding the row — and because it is written down",
                 "Because zero breaks the model", "It is arbitrary and does not matter"], 1,
                "What matters most is that the convention is recorded, because it changes borderline acetylene calls."),
    'split': _q("Why split by unit rather than by assessment?",
                ["Units are easier to count", "Because the same transformer in both halves lets the model recognise the unit rather than the condition",
                 "Because sklearn requires it", "To balance the classes"], 1,
                "That is leakage, and it flatters the score badly."),
    'duval': _q("What are the Duval Triangle's two main limits?",
                ["It is out of date and inaccurate",
                 "It uses only three of the seven gases and ignores moisture, BDV, age and thermal history — and it names a fault type without saying how urgent it is",
                 "It needs a computer", "It only works on new units"], 1,
                "The model extends Duval rather than replacing it."),
    'health-model': _q("Two units score 69 and 71 and land in different bands. What should the screen do?",
                       ["Nothing — the bands are the bands", "Report the band WITH its confidence, so a borderline call looks borderline",
                        "Round both to 70", "Always escalate"], 1,
                        "The band boundaries are conventions; hiding that behind a confident label misleads the engineer."),
    'drivers': _q("The ranking puts age above dissolved gas. What should you do?",
                  ["Accept it", "Check it against IEC 60599 and experience — age correlates with gas, so the model may be keying on the consequence rather than the cause",
                   "Delete the age column", "Retrain"], 1,
                  "Importance shows what moves the prediction, not what caused the condition."),
    'survey-problem': _q("Why is a cooling fault so hard for a rule to detect?",
                         ["It is too small", "Because the evidence is ABSENT heat — a region colder than it should be — and no maximum-temperature reading can express that",
                          "Because radiators are cold anyway", "Because it needs a better camera"], 1,
                         "The two fault types point in opposite directions on the same scale."),
    'handmade': _q("Why can no maximum-temperature limit work here?",
                   ["The camera is uncalibrated", "Because raising it to exclude a sunlit unit also excludes the hot bushing, and lowering it still cannot see a COLD radiator",
                    "Maximums are always wrong", "The limit is in the wrong units"], 1,
                   "It fails in both directions at once, which is what makes it structural rather than a tuning problem."),
    'cnn-journey': _q("What pattern lets a CNN detect a blocked radiator bank?",
                      ["The bank is brighter", "A healthy bank produces a regular comb of vertical edges; a blocked bank leaves a gap in that regular pattern",
                       "The tank changes colour", "Nothing — it cannot"], 1,
                      "The evidence is structural regularity, which is exactly what convolution is good at."),
    'thermal-locate': _q("Why does the attention map stay flat on a sunlit unit?",
                         ["The image is too bright", "Because nothing stands out against its own surroundings when everything is uniformly warm — which is the distinction a maximum cannot make",
                          "Because sunlight is filtered out", "Because the model ignores warm images"], 1,
                         "Local contrast, not absolute temperature, is what carries the evidence."),
    'audit': _q("Why is overall accuracy the wrong number here?",
                ["It is too low", "Because the two errors differ by about 65× in cost — an unnecessary visit versus a failed transformer",
                 "Because there are four classes", "Because the fleet is small"], 1,
                "The number to report is the share of genuinely high-risk units correctly escalated."),
    'proof': _q("What does comparing Duval, the model and the CNN show?",
                ["The CNN is best", "Duval is obsolete",
                 "They see largely different faults — the overlap is small, so removing any one creates a blind spot", "They are equivalent"], 2,
                "A cooling fault shows only on the survey; a developing winding fault shows only in the oil."),
    'decision-screen': _q("Why must every row carry a reason in the language of the standards?",
                          ["Regulations require a reason", "Because an engineer accountable under the standards cannot act on a bare number — and should not",
                           "To make the screen look fuller", "Because the model is unreliable"], 1,
                          "The reason column is what turns a score into something defensible."),
    'fleet': _q("Why rank the fleet rather than classify it?",
                ["Ranking is more accurate", "Because the real question is 'which twelve do I inspect this quarter' — ninety 'moderate risk' labels answer nothing",
                 "Because classes are hard to compute", "To reduce false alarms"], 1,
                "A ranked list with a budget line drawn across it is a plan; a pile of labels is not."),
    'dashboard': _q("Why subtract the cost of unnecessary visits?",
                    ["To make the number smaller", "Because otherwise a system that escalates every unit avoids every failure and looks perfect while being useless",
                     "Regulations require it", "Because visits are expensive"], 1,
                    "Netting the two costs off is what makes the business case honest."),
}

START = dict(
    project_line="one asset-management project",
    problem="""
A power transformer serves **twenty thousand customers**. There is **no spare**, the lead time on a
replacement is a year, and its paper insulation ages **exponentially** with hot-spot temperature — roughly
a doubling every 6–7 K. Condition assessment is a calendar activity: an oil sample takes a fortnight to
come back from the laboratory, an infrared survey needs an engineer on site, and neither happens more than
twice a year. And the real question is never "is this unit healthy" — it is **"I can inspect twelve units
this quarter, which twelve?"** The job: **rank a fleet of four hundred by risk, with a reason for each.**
""",
    build_intro="A **decision-support system** for the transformer fleet. Four parts:",
    cards=[
        ("🧪", "The laboratory reads the oil",
         "Seven dissolved gases, moisture and breakdown voltage — each with a limit in IEC 60599, and "
         "each pointing at a different kind of fault."),
        ("📡", "The monitors read the thermal history",
         "Load, ambient, top oil and hot spot — and the IEEE C57.91 ageing rate that follows, which is "
         "what actually consumes the asset's life."),
        ("📷", "The camera sees what the oil cannot",
         "An infrared survey. A blocked radiator bank generates no gas at all, so this is the only "
         "record in which a cooling fault exists."),
        ("🔔", "The engineer gets a ranked worklist",
         "Not a black box. A condition band, the measurements that breached their limits in the language "
         "of the standards, and a confidence — so a person decides and signs."),
    ],
    promise="""The asset engineer stays in charge and stays accountable — de-energising a transformer is a
statutory decision and no model signs one. The system handles the part one person cannot: it re-ranks four
hundred units every week and attaches the reason to each. The goal is <b>Power Engineer + AI</b> — a fleet
where the next failure was on somebody's list.""",
    map_note="""<b>Every AI concept here is an asset-management activity you already understand</b> — the
same thing, named differently by a different profession. Read down the amber column and you have described
a condition-monitoring programme. Read down the cyan column and you have described a machine learning
pipeline. They are the same column.""",
)

_m = sys.modules[__name__]
BY_ID, ORDER = scaffold.lookups(_m)
inject_css = lambda: scaffold.inject_css(_m)
open_page = lambda stage: scaffold.open_page(_m, stage)
close_page = lambda stage: scaffold.close_page(_m, stage)
render_start = lambda: scaffold.render_start(_m)
route = lambda STAGES, ALIASES=None: scaffold.route(_m, STAGES, ALIASES)
