"""
bridge.py — the Manufacturing-Engineering -> AI teaching content.
=================================================================
All the machinery lives in scaffold.py. This module only declares WHAT this
project teaches: its phases, its steps, its quiz and its opening page.
"""
import sys
import scaffold

THEME = dict(
    title="AI Cutting Tool Recommendation System",
    icon="🛠️",
    dwg="TR-SEL-001",
    civil_label="Manufacturing Engineering",
    civil_kicker="IN THE TOOL ROOM",
    station="⟨TOOL ROOM·CELL 4⟩",
    rail="JOB",
    start_button="▶  Start: a job card lands on the desk",
    sidebar_title="A Tool Selection Problem",
    sidebar_note="You are choosing a tool, a coating, a coolant, a speed and a feed — 4,200 times a year.",
    backdrop=("repeating-linear-gradient(45deg, rgba(255,255,255,.016) 0 2px,"
              " transparent 2px 22px)"),
)

PHASES = [
    ("The Job Arrives",      "A drawing lands in the tool room and something has to be chosen."),
    ("One Job, One Record",  "A completed job becomes a written record with an outcome."),
    ("The Tool-Room Log",    "The ERP export lands and gets checked."),
    ("Preparing The Data",   "Words become numbers, and the jobs are split."),
    ("The Recommendation",   "Predicting the tool, the coating, the speed and the feed."),
    ("The Image Wall",       "The insert goes under the camera and the rulebook collapses."),
    ("Reading The Wear",     "A CNN grades a wear land no rule could grade."),
    ("The Tool-Room Audit",  "Every recommendation checked on jobs never seen."),
    ("The System",           "Fusion, and what it is worth per year."),
]

_S = lambda **k: k
STEPS = [
_S(id='job-card', phase=0, civil='A Job Card Arrives', ai='Why Tool Selection Needs AI',
   civil_icon='📐', ai_icon='🤖', tech='120 discrete combinations, plus two continuous settings',
   civil_bullets=['A drawing, a material', 'A batch and a finish', 'Something must be chosen'],
   ai_bullets=['Learn from past jobs', 'Recover the shop logic', 'Recommend, with a reason'],
   site="""A job card lands: a material, a machine, an operation, a batch quantity and a required surface
finish. Before a chip is cut, somebody chooses a tool, a coating, a coolant, a speed and a feed.""",
   challenge="""That is 120 discrete combinations before the two continuous settings, and the speed choice
is unforgiving — Taylor's equation means running 25% fast can cost most of the edge's life.""",
   ai_link="""The shop already holds thousands of completed jobs with their outcomes. Nobody can read four
thousand records before lunch; that reading is what AI takes off the setter.""",
   notebook="""Section 1. The machining model: reference speeds, Taylor's equation, and Ra ≈ f²/32r.""",
   contributes="""The requirement, and the physics every later page is checked against.""",
   takeaway="""Tool life falls steeply with speed. That is why the choice is worth getting right."""),
_S(id='memory', phase=0, civil="The Tool Room's Memory", ai='The Dataset Already Exists',
   civil_icon='🗄️', ai_icon='📚', tech='4,000 completed jobs with their outcomes',
   civil_bullets=['Two experienced setters', 'A catalogue for ideal conditions', 'Memory that walks out'],
   ai_bullets=['Thousands of records', 'Outcomes included', 'Including the bad ones'],
   site="""The ERP holds every completed job: what was machined, with what, at what speed — and how long
the edge lasted, what finish came off, and whether the part was scrapped.""",
   challenge="""None of it is read. The shop relies on one or two experienced setters and a catalogue
written for ideal conditions, and that knowledge leaves when they do.""",
   ai_link="""A model that recovers the shop's own selection logic from its own records is not replacing
judgement — it is writing it down so a new starter does not have to rediscover it.""",
   notebook="""Section 1. What the log contains, and what it is worth.""",
   contributes="""The argument for the project, before any code.""",
   takeaway="""The knowledge is not missing. It is unread."""),
_S(id='reading', phase=1, civil='One Completed Job', ai='Data Collection',
   civil_icon='📋', ai_icon='🗄️', tech='inputs known before cutting vs outcomes known after',
   civil_bullets=['Six job-card facts', 'Five choices', 'Two outcomes'],
   ai_bullets=['One row per job', 'Features vs targets', 'Never mix them'],
   site="""Each completed job becomes a record: the facts from the card, the choices the setter made, and
what resulted — tool life and measured Ra.""",
   challenge="""Some columns are known before cutting and some only after. Tool life is an outcome; feeding
it in as an input would let a model predict the tool from the life it produced.""",
   ai_link="""Separating inputs from outcomes is the first modelling decision, and it is made before any
model is chosen. Get it wrong and every score afterwards is meaningless.""",
   notebook="""Section 2. Build one job record, then the whole log.""",
   contributes="""The unit of learning, and the input/outcome boundary.""",
   takeaway="""Tool life is an outcome, not an input. Nobody has it when the job card lands."""),
_S(id='two-records', phase=1, civil='Job Card vs Insert Photo', ai='Two Kinds Of Data',
   civil_icon='🧾', ai_icon='🔀', tech='Six named fields, or 4,096 unnamed pixels',
   civil_bullets=['The job card', 'The insert photo', 'Same job, two views'],
   ai_bullets=['Named columns → ML', 'Raw pixels → DL', 'The fork in the road'],
   site="""Two records leave every job: the card with six named fields, and a presetter photograph of the
insert edge afterwards.""",
   challenge="""Both describe the same job. The card says what was chosen; the photo says what it cost the
edge. Neither is complete alone.""",
   ai_link="""Named columns suit Machine Learning — including the words, once encoded. Raw pixels do not,
and that difference is the whole argument of this course.""",
   notebook="""Section 2. Print one row, then show one insert image as an array.""",
   contributes="""The fork: fields go to ML, pixels go to DL.""",
   takeaway="""Fields arrive with names; pixels do not. That splits ML from DL."""),
_S(id='load', phase=2, civil='The Tool-Room Log Arrives', ai='Loading The Dataset',
   civil_icon='📥', ai_icon='🐼', tech='CSV → DataFrame, 4,000 jobs',
   civil_bullets=['ERP export', 'One row per job', 'Several years'],
   ai_bullets=['read_csv', 'shape and dtypes', 'First look'],
   site="""The ERP exports the job history as a CSV: one row per completed job, with the choices made and
the outcomes measured.""",
   challenge="""An export is not a dataset. Setup sheets get typed in wrong, impossible speeds appear, and
the same job is booked twice.""",
   ai_link="""Loading it is the first step: shape, column types, and how often each material and tool
actually appears — which is the first hint of how unbalanced this problem is.""",
   notebook="""Section 3. `pd.read_csv`, `.shape`, `.head()`.""",
   contributes="""The dataset every later step reads from.""",
   takeaway="""The export is raw material. Loading it is where the data work starts."""),
_S(id='inspect', phase=2, civil='Checking The Records', ai='Data Inspection',
   civil_icon='🔍', ai_icon='📊', tech='Count gaps, impossible values and duplicates',
   civil_bullets=['Is the speed possible?', 'Did anyone measure Ra?', 'Is the job booked twice?'],
   ai_bullets=['isna().sum()', 'describe()', 'duplicated()'],
   site="""Before trusting a few thousand records, check them. A cutting speed of 5,000 m/min on titanium
did not happen. A tool life of zero minutes means nobody filled the field in.""",
   challenge="""Typed-in data fails differently from sensor data: it is not noisy, it is *wrong* — a decimal
point in the wrong place, a unit confused, a default left in.""",
   ai_link="""Inspection is that check in code, and here it also reveals the class imbalance: some tool
materials appear in a handful of jobs, which decides what the model can be expected to learn.""",
   notebook="""Section 4. `.isna().sum()`, `.describe()`, `.value_counts()`.""",
   contributes="""The fault list, and the imbalance the audit has to account for.""",
   takeaway="""Typed data is not noisy — it is wrong in specific, findable ways."""),
_S(id='clean', phase=2, civil='Removing The Bad Records', ai='Data Cleaning',
   civil_icon='🧹', ai_icon='🧼', tech='Drop duplicates, remove the impossible',
   civil_bullets=['Repair or discard', 'Keep the good columns', 'Never invent a job'],
   ai_bullets=['drop_duplicates', 'Mask impossibles', 'Document what went'],
   site="""A record that could not have happened is removed before it reaches a report. Nobody averages a
5,000 m/min titanium job into a recommended speed and defends it.""",
   challenge="""Dropping whole jobs loses good information from the other columns — and with only a handful
of jobs on some tool materials, every deletion matters.""",
   ai_link="""So mark impossible values rather than deleting the row where possible, drop exact duplicates,
and record what was removed so the audit can account for it.""",
   notebook="""Section 5. `drop_duplicates`, physical range checks.""",
   contributes="""A dataset where every remaining record could physically have happened.""",
   takeaway="""Remove what could not have happened, and write down what you removed."""),
_S(id='encoding', phase=3, civil='Materials Are Names, Not Numbers', ai='Categorical Encoding',
   civil_icon='🔤', ai_icon='🔢', tech='one-hot, not a numbered list',
   civil_bullets=['Titanium is not "6"', 'Steel is not "3"', 'They do not add up'],
   ai_bullets=['One column per material', 'No false ordering', 'The model cannot average them'],
   site="""Three of the most important job-card fields are words: the workpiece material, the machine and
the operation.""",
   challenge="""Numbering them 1–7 tells the model that inconel is 'more' than aluminium and that the average
of brass and titanium is cast iron. None of that is true, and a model will use it.""",
   ai_link="""One-hot encoding gives each value its own column, so no ordering is implied. The cost is width;
the benefit is that the model cannot invent a relationship the shop does not have.""",
   notebook="""Section 6. `pd.get_dummies`, and the wrong way shown once for contrast.""",
   contributes="""Inputs the model cannot misread.""",
   takeaway="""Numbering categories invents an order. One-hot encoding refuses to."""),
_S(id='split', phase=3, civil='Known Jobs vs Sealed Jobs', ai='Train / Test Split',
   civil_icon='🗂️', ai_icon='✂️', tech='stratified, because some tools are rare',
   civil_bullets=['Prove on new jobs', 'Not on old ones', 'Keep the rare tools in both'],
   ai_bullets=['Train 70%', 'Test 30%', 'Stratified by tool'],
   site="""A recommendation is validated on jobs it was not built from — the same discipline as proving a
process on a first-off rather than on the sample that set it.""",
   challenge="""Some tool materials appear in only a few dozen jobs. A careless split can leave none of them
in the test set, and the score then says nothing about the cases that matter most.""",
   ai_link="""Stratify the split by tool material so every class appears in both halves in proportion.""",
   notebook="""Section 7. `train_test_split(..., stratify=y)`.""",
   contributes="""The sealed jobs the audit runs on.""",
   takeaway="""Stratify, or the rare tool that matters most will not appear in the test set at all."""),
_S(id='tool-model', phase=4, civil='Which Tool For This Job?', ai='Multi-Class Classification',
   civil_icon='🛠️', ai_icon='🌲', tech='job card → tool material, coating, coolant',
   civil_bullets=['Six tool materials', 'Five coatings', 'Four coolants'],
   ai_bullets=['One classifier each', 'Probabilities, not just a class', 'Recovered from the log'],
   site="""The first question: given this job card, which tool material, coating and coolant would this
shop have chosen?""",
   challenge="""The shop's own logic is not written down anywhere, and it is not perfectly consistent — a
different setter, a stock-out or a customer preference deviates on a few per cent of jobs.""",
   ai_link="""A classifier recovers that logic from the log, inconsistencies and all. Its probabilities are
useful: a confident call means the shop agrees with itself, a split one means it does not.""",
   notebook="""Section 8. `RandomForestClassifier` for each of the three choices.""",
   contributes="""The discrete half of the recommendation.""",
   takeaway="""The model recovers the shop's own selection logic — including where the shop disagrees with itself."""),
_S(id='speed-feed', phase=4, civil='What Speed And What Feed?', ai='Regression, Checked Against Physics',
   civil_icon='⚡', ai_icon='📐', tech='predict vc and f, then check Taylor and Ra',
   civil_bullets=['Speed sets tool life', 'Feed sets finish', 'Both are continuous'],
   ai_bullets=['Two regressors', 'Compare to the equations', 'Physics is the referee'],
   site="""Speed and feed are numbers, not choices from a list. Speed decides how long the edge lasts; feed
decides the finish that comes off.""",
   challenge="""A regressor will happily predict a feed that cannot hold the required Ra, because nothing in
the loss function knows about Ra ≈ f²/32r.""",
   ai_link="""Predict both, then check them against the physics: does the feed hold the finish, and does the
speed give a sensible life under Taylor? Where they disagree, the physics wins.""",
   notebook="""Section 9. Regressors for speed and feed, checked against the two equations.""",
   contributes="""The continuous half of the recommendation, with a physical guard on it.""",
   takeaway="""A learned speed that contradicts Taylor's equation is wrong, however good its R²."""),
_S(id='drivers', phase=4, civil='What Actually Decides The Tool', ai='Feature Importance',
   civil_icon='🎚️', ai_icon='📈', tech='which job-card field moves the choice',
   civil_bullets=['Material or batch?', 'Machine or finish?', 'Rank them'],
   ai_bullets=['feature_importances_', 'Check against practice', 'A sanity test'],
   site="""A setter asked why a tool was chosen will name one or two facts — usually the material, sometimes
the batch size.""",
   challenge="""Several fields move together, and the model may key on the wrong one: the machine correlates
with the material because certain jobs only run on certain machines.""",
   ai_link="""Feature importance ranks how much each field changes the choice, and it is the first place the
model can be checked against what the tool room already knows.""",
   notebook="""Section 10. `.feature_importances_`, sorted and plotted.""",
   contributes="""The sanity check that gets the model past a shop-floor review.""",
   takeaway="""If the ranking disagrees with the setter, one of the two is wrong — go and find out which."""),
_S(id='insert-problem', phase=5, civil='The Insert Under The Camera', ai='The Raw Image',
   civil_icon='📷', ai_icon='🖼️', tech='a 64x64 grid of pixels, no named columns',
   civil_bullets=['A bright wear land', 'A bright built-up edge', 'Both look bright'],
   ai_bullets=['4,096 numbers', 'No column names', 'Nothing to weight'],
   site="""The presetter photographs the insert edge. ISO 3685 measures VB, the width of the flank wear
land — the bright polished band below the cutting edge.""",
   challenge="""The camera does not output "VB = 0.28 mm". It outputs 4,096 brightness values, and two things
that are not wear — built-up edge and coolant stain — sit in the same part of the frame.""",
   ai_link="""This is where Machine Learning runs out. Before reaching for a new method, it is worth building
the wear feature by hand and watching exactly what happens.""",
   notebook="""Section 11. Build an insert image as an array and display it.""",
   contributes="""The data type that forces the second half of the course.""",
   takeaway="""An insert photo is 4,096 unnamed numbers, and two of the bright things in it are not wear."""),
_S(id='handmade', phase=5, civil='Measuring Wear By Brightness', ai='Hand-Made Features',
   civil_icon='✋', ai_icon='🔢', tech='count the bright pixels — and what it loses',
   civil_bullets=['Wear is polished', 'So count bright pixels', 'Exactly as before'],
   ai_bullets=['One feature', 'One threshold', 'It misses'],
   site="""The obvious workaround: a wear land is polished and bright, so count the pixels above a
brightness threshold and call that the wear.""",
   challenge="""Built-up edge is workpiece metal welded onto a perfectly good edge — brighter and larger than
a real wear land. The count reads it as heavy wear and scraps a fresh insert.""",
   ai_link="""And a coolant stain darkens a genuinely worn edge, so the count falls and a finished insert
stays in the machine. The feature was hand-made and it was the wrong feature.""",
   notebook="""Section 12. Bright-pixel fraction across fresh, worn, stained and built-up-edge images.""",
   contributes="""The failed baseline that justifies the CNN.""",
   takeaway="""Built-up edge is brighter than wear and is not wear. A brightness count cannot know that."""),
_S(id='cnn-journey', phase=6, civil='Grading The Wear Land', ai='Convolution & Feature Maps',
   civil_icon='🧩', ai_icon='🔬', tech='filters → feature maps → three wear classes',
   civil_bullets=['A band of a width', 'Below the edge line', 'Shape, not brightness'],
   ai_bullets=['Filters slide', 'Edges → bands', 'Filters are learned'],
   site="""An inspector does not count bright pixels. They look for a band of a particular width immediately
below the edge, and measure it.""",
   challenge="""That band cannot be captured by any single pixel value, and it moves — every insert sits in
the fixture slightly differently.""",
   ai_link="""A convolution slides a small filter over the image and reports where its pattern occurs. A wear
land is bounded by two horizontal edges a fixed distance apart, and that distance is VB.""",
   notebook="""Section 13. Convolve an insert image by hand, then train a small CNN.""",
   contributes="""The visual half of the system: a wear class for every edge.""",
   takeaway="""A wear land is a band with a lower boundary; built-up edge is a lump without one."""),
_S(id='wear-locate', phase=6, civil='Where Is The Wear?', ai='Grad-CAM',
   civil_icon='📍', ai_icon='🗺️', tech='class-weighted feature maps → heat map',
   civil_bullets=['Which part of the edge?', 'How wide?', 'Against the standard'],
   ai_bullets=['Weight the maps', 'Project onto the image', 'Show the evidence'],
   site="""A grade of "replace" does not scrap an insert on its own. The setter wants to see the wear land
that produced the grade, and check its width against ISO 3685.""",
   challenge="""A classifier outputs a class. On an edge with built-up edge on it, a confident "replace" with
no visible reasoning is exactly the answer a setter will overrule.""",
   ai_link="""Grad-CAM projects the evidence back onto the image. When the map stays on the band below the
edge and ignores the lump, the grade becomes checkable.""",
   notebook="""Section 14. Grad-CAM over the trained CNN.""",
   contributes="""The evidence that makes the grade auditable.""",
   takeaway="""Grad-CAM turns a confident grade into a checkable measurement."""),
_S(id='audit', phase=7, civil='The Tool-Room Audit', ai='Confusion Matrix',
   civil_icon='🧮', ai_icon='✅', tech='TP / FP / FN / TN and what each costs',
   civil_bullets=['Recommended vs chosen', 'On sealed jobs', 'Every claim checked'],
   ai_bullets=['Four outcomes', 'Costs are not equal', 'Look at the hard alloys'],
   site="""Every recommendation is audited against what the shop actually did, on jobs the model was never
allowed to see.""",
   challenge="""Accuracy across all materials hides what matters. Getting aluminium right is easy and cheap;
getting inconel wrong scraps a part worth more than the whole insert stock.""",
   ai_link="""The confusion matrix separates the outcomes, and here it has to be read **per material** — the
difficult alloys are where the errors are both rarer and far more expensive.""",
   notebook="""Section 15. Confusion matrix, overall and on the hard alloys.""",
   contributes="""The honest performance number the project is judged on.""",
   takeaway="""Report accuracy on the difficult alloys separately, or the easy ones will hide the failures."""),
_S(id='proof', phase=7, civil='The Verdict', ai='ML vs DL, Proven',
   civil_icon='⚔️', ai_icon='🏁', tech='the same shop, both methods, measured',
   civil_bullets=['Two data types', 'Two methods', 'One tool room'],
   ai_bullets=['Forest wins on the card', 'CNN wins on the photo', 'Neither replaces the other'],
   site="""Two models, two data types, one tool room. Time to state plainly what each can and cannot do.""",
   challenge="""It is tempting to declare the CNN the better method. It cannot choose a tool at all — it has
never seen a job card.""",
   ai_link="""Run both on both. The forest recovers the selection logic from named fields and cannot read an
insert photo. The CNN grades the edge and cannot read a job card. Each belongs to its data type.""",
   notebook="""Section 16. The comparison table, filled in from measured results.""",
   contributes="""The course's central claim, demonstrated rather than asserted.""",
   takeaway="""ML weights the fields you name; DL finds the patterns you cannot name."""),
_S(id='fusion-engine', phase=8, civil='The Setup Sheet', ai='AI Fusion',
   civil_icon='🖥️', ai_icon='🔗', tech='choices + settings + edge grade → one sheet',
   civil_bullets=['Every decision', 'On one page', 'With the reason'],
   ai_bullets=['Combine the outputs', 'Check against physics', 'Attach the evidence'],
   site="""By now the system produces three discrete choices, two settings, an expected tool life and a
grade for the insert going into the machine.""",
   challenge="""Seven separate outputs is seven chances to miss a contradiction — a feed that cannot hold the
finish, or a fresh-looking edge that the camera says is finished.""",
   ai_link="""Fusion assembles them into one setup sheet with the reason beside each line, and the two
physics checks visible, so a setter can sign it off rather than take it on trust.""",
   notebook="""Section 17. The setup sheet, assembled from every model output.""",
   contributes="""The product — one page a setter can act on.""",
   takeaway="""A recommendation with a reason is a setup sheet; one without is a guess with a decimal point."""),
_S(id='dashboard', phase=8, civil='What It Is Worth', ai='Inserts, Scrap & Time',
   civil_icon='💷', ai_icon='📉', tech='insert cost, scrap events, spindle hours',
   civil_bullets=['Approve a spend', 'Against a saving', 'Read it carefully'],
   ai_bullets=['Fewer scrap events', 'Better edge use', 'The obvious case does not survive'],
   site="""The works manager approves a spend against a saving: inserts, scrapped parts and spindle time.""",
   challenge="""The obvious business case — "the model picks better tools, so tool cost falls" — does not
survive contact with the data. Inserts are cheap; a scrapped titanium part is not.""",
   ai_link="""So the saving is not in the tool crib. It is in the small number of expensive mistakes on
difficult alloys, and in setters not rediscovering what the shop already knew.""",
   notebook="""Section 18. The business case, and why the obvious version is wrong.""",
   contributes="""The reason the previous steps get funded.""",
   takeaway="""The saving is not cheaper inserts. It is the scrapped part that never happened."""),
]

SHORT = {
    "job-card": "A job card arrives",   "memory": "The tool room's memory",
    "reading": "One completed job",     "two-records": "Card vs photo",
    "load": "The log arrives",          "inspect": "Checking the records",
    "clean": "Removing bad records",    "encoding": "Materials are names",
    "split": "Known vs sealed jobs",    "tool-model": "Which tool?",
    "speed-feed": "What speed and feed", "drivers": "What decides the tool",
    "insert-problem": "The insert photo", "handmade": "Wear by brightness",
    "cnn-journey": "Grading the wear",  "wear-locate": "Where is the wear",
    "audit": "The tool-room audit",     "proof": "The verdict",
    "fusion-engine": "The setup sheet", "dashboard": "What it is worth",
}
for _s in STEPS:
    _s["short"] = SHORT[_s["id"]]

_q = lambda q, o, a, w: dict(q=q, options=o, answer=a, why=w)
QUIZ = {
    'job-card': _q("Why is a 25% increase in cutting speed such an expensive decision?",
                   ["It uses more power", "Taylor's equation is a power law — a modest speed rise costs a large share of the edge's life",
                    "It always ruins the finish", "It has no effect"], 1,
                   "V·Tⁿ = C with n around 0.28 means life falls far faster than speed rises."),
    'memory': _q("What is the actual argument for this project?",
                 ["AI chooses tools better than an experienced setter",
                  "The shop's knowledge already exists in thousands of job records that nobody reads, and it leaves when the setter does",
                  "Catalogues are wrong", "Setters are too slow"], 1,
                 "The claim is that unread knowledge is recoverable, not that the setter is replaceable."),
    'reading': _q("Why must tool life never be used as an input feature?",
                  ["It is measured in minutes", "Because it is an OUTCOME — nobody has it when the job card lands, so a model using it could not be deployed",
                   "It is often missing", "It is correlated with speed"], 1,
                  "Using an outcome as an input is the most common way a model scores brilliantly and is useless."),
    'two-records': _q("What makes the job card suit ML and the insert photo suit DL?",
                      ["The card is smaller", "Images are always harder",
                       "The card has named fields an engineer chose; the photo is 4,096 unnamed pixels", "ML cannot handle words"], 2,
                      "Words are fine once encoded. Unnamed pixels are not."),
    'load': _q("Why is an ERP export not yet a dataset?",
               ["Wrong file format", "It contains typing errors, impossible values and jobs booked twice",
                "It is too large", "It has no header row"], 1,
               "Typed data fails differently from sensor data — it is wrong, not noisy."),
    'inspect': _q("A record shows 5,000 m/min on titanium. What is it?",
                  ["An unusually fast machine", "A typing error — that speed is physically impossible on that alloy",
                   "A new tool material", "A rounding artefact"], 1,
                  "Titanium's reference speed is around 65 m/min. Two orders of magnitude out is a keying error."),
    'clean': _q("Why is deleting whole records more costly here than in a sensor project?",
                ["Records are expensive", "Because some tool materials appear in only a few dozen jobs, so every deletion removes a large share of a rare class",
                 "Because ERP data cannot be edited", "It is not more costly"], 1,
                "With a rare class, each lost row is a large fraction of the evidence for it."),
    'encoding': _q("Why not simply number the materials 1 to 7?",
                   ["It uses more memory", "Because it tells the model inconel is 'more than' aluminium and that their average is another material",
                    "Because numbers are slower", "Because the ERP uses text"], 1,
                   "A numbered category invents an ordering and a midpoint, and a model will use both."),
    'split': _q("Why stratify the split by tool material?",
                ["To make training faster", "Because some tool materials are rare — a careless split can leave none of them in the test set",
                 "Because sklearn requires it", "To reduce the file size"], 1,
                "An unstratified split can silently exclude the very cases that matter most."),
    'tool-model': _q("The classifier is only 88% accurate. Is that a failure?",
                     ["Yes — it should be near 100%", "Not necessarily: the shop itself deviates on a few per cent of jobs, so perfect agreement would mean the model had memorised the noise",
                      "Yes, because tools are expensive", "It cannot be judged"], 1,
                     "The ceiling is the shop's own consistency, not 100%."),
    'speed-feed': _q("The regressor predicts a feed that cannot hold the required Ra. What do you do?",
                     ["Accept it — the model has more data", "Take the physics: Ra ≈ f²/32r is a geometric fact, and the model's loss function knows nothing about it",
                      "Retrain with more trees", "Increase the nose radius silently"], 1,
                     "Where a learned value contradicts a physical relation, the physics wins."),
    'drivers': _q("The model ranks 'machine' above 'material'. What is the likely explanation?",
                  ["The machine really does decide the tool", "Certain jobs only run on certain machines, so machine is standing in for material — a correlation, not a cause",
                   "The model is broken", "Materials do not matter"], 1,
                  "Importance points at what moves the prediction, which is not always what causes the outcome."),
    'insert-problem': _q("Why can the Random Forest not grade the insert photo?",
                         ["The image is too large", "There are no named features — only 4,096 pixel values with no individual meaning",
                          "Forests only accept integers", "The camera resolution is too low"], 1,
                         "A pixel at row 30 column 40 is not a feature anybody can name or defend."),
    'handmade': _q("Why does counting bright pixels fail on a fresh insert with built-up edge?",
                   ["The camera is out of focus", "Because built-up edge is workpiece metal welded onto a good edge — brighter and larger than real wear, so a fresh insert is scrapped",
                    "Because BUE is dark", "Thresholds never work"], 1,
                   "The count measures brightness; the standard measures a band of a particular width and position."),
    'cnn-journey': _q("What distinguishes a wear land from built-up edge in the feature maps?",
                      ["Wear is brighter", "A wear land is a band bounded by two horizontal edges a fixed distance apart; built-up edge is a rounded lump with no lower boundary",
                       "BUE is always smaller", "Nothing — they are the same"], 1,
                      "That distance between the boundaries is VB, which is exactly what ISO 3685 measures."),
    'wear-locate': _q("Why does Grad-CAM matter more here than in a purely predictive project?",
                      ["It improves accuracy", "Because a confident 'replace' on an edge with built-up edge on it is exactly the answer a setter will overrule — the map makes it checkable",
                       "It is faster", "It reduces model size"], 1,
                      "The map turns an assertion into a measurement the standard can be applied to."),
    'audit': _q("Overall accuracy is 91%. Why is that not the number to report?",
                ["It is too low", "Because the easy materials dominate the average — the difficult alloys, where a mistake scraps an expensive part, must be reported separately",
                 "Accuracy is never useful", "The test set is too small"], 1,
                "An average over unequal costs hides the expensive failures."),
    'proof': _q("What does the head-to-head comparison prove?",
                ["Deep Learning is better", "Machine Learning is obsolete",
                 "Each method belongs to its data type: the forest recovers the selection logic, the CNN grades the edge, and neither can do the other's job", "Both perform identically"], 2,
                "The CNN has never seen a job card; the forest has never seen a pixel."),
    'fusion-engine': _q("Why does the setup sheet show the reason beside each line?",
                        ["To fill the page", "Because a setter who cannot check the reasoning will not sign it off — and the two physics lines are exactly what they can check",
                         "Regulations require it", "To slow them down"], 1,
                        "A recommendation with a reason is a setup sheet; one without is a guess with a decimal point."),
    'dashboard': _q("Why does the obvious business case — cheaper tooling — not survive?",
                    ["Tools are getting more expensive", "Because inserts are cheap relative to a scrapped part: the saving is in the rare expensive mistakes on difficult alloys, not in the tool crib",
                     "Because the model picks the same tools", "Because tool cost cannot be measured"], 1,
                    "Counting insert cost alone makes the project look marginal and misses where the money actually is."),
}

START = dict(
    project_line="one tool-selection project",
    problem="""
A job card lands in the tool room: a **material**, a **machine**, an **operation**, a **batch quantity**
and a **required surface finish**. Before a chip is cut somebody must choose a **tool material, a coating,
a coolant, a cutting speed and a feed** — 120 discrete combinations plus two continuous settings, about
**4,200 times a year**. Get the speed 25% wrong and Taylor's equation takes most of the edge's life. The
knowledge to get it right exists — in thousands of completed job records **that nobody reads**, and in one
or two setters who will eventually leave. The job: **write that knowledge down.**
""",
    build_intro="A **tool recommendation system** for the tool room. Four parts:",
    cards=[
        ("📋", "The ERP holds the history",
         "Every completed job: material, machine, operation, batch, finish — the choices made, and the "
         "tool life and Ra that resulted."),
        ("🌲", "A model recovers the shop's logic",
         "Classifiers for tool, coating and coolant; regressors for speed and feed — trained on what this "
         "shop actually did, deviations and all."),
        ("📐", "Physics is the referee",
         "Taylor's V·Tⁿ = C and Ra ≈ f²/32r are geometric and physical facts. Where a learned value "
         "disagrees with them, the physics wins."),
        ("📷", "The camera grades the edge",
         "A CNN reads the flank wear land and tells it from built-up edge and coolant stain — which a "
         "brightness count cannot do."),
    ],
    promise="""The setter stays in charge and stays accountable. The system handles the part one person
cannot: it reads four thousand past jobs before every new one and turns them into a setup sheet with a
reason beside every line. The goal is <b>Manufacturing Engineer + AI</b> — a tool room whose knowledge
outlives its best setter.""",
    map_note="""<b>Every AI concept here is a tool-room activity you already understand</b> — the same
thing, named differently by a different profession. Read down the amber column and you have described
process planning. Read down the cyan column and you have described a supervised learning pipeline. They
are the same column.""",
)

_m = sys.modules[__name__]
BY_ID, ORDER = scaffold.lookups(_m)
inject_css = lambda: scaffold.inject_css(_m)
open_page = lambda stage: scaffold.open_page(_m, stage)
close_page = lambda stage: scaffold.close_page(_m, stage)
render_start = lambda: scaffold.render_start(_m)
route = lambda STAGES, ALIASES=None: scaffold.route(_m, STAGES, ALIASES)
