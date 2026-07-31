"""
bridge.py - the Highway-Engineering -> AI teaching scaffold.
============================================================
This module teaches no NEW concept and renders no model. Every technical
illustration lives in app.py. This module wraps each stage renderer in a
five-part structure, so a Civil Engineering student always sees, on every page:

    Civil Engineering   the on-network context        (bridge.open_page)
    The Challenge       why the manual way runs out   (bridge.open_page)
    AI Connection       + the bridge figure           (bridge.open_page)
    Technical Idea      <- the stage renderer         (app.py)
    Key Takeaway        one sentence                  (bridge.close_page)
    In the Notebook     where it lives                (bridge.close_page)

Content edits go in STEPS below. app.py needs no changes.

Text is deliberately short and professional. Short sentences, active voice, no
drama. The visuals carry the page; the text supports them.

COLOR IS A TEACHING DEVICE. Amber is ALWAYS the highway / civil world. Cyan is
ALWAYS the AI world. Violet is ALWAYS the technical process.
"""
import streamlit as st
import plotly.graph_objects as go

# ---------------------------------------------------------------- palette
BG, PANEL = "#0e1117", "#161b22"
CIVIL = "#ffb74d"      # amber  - the road / civil engineering
AISIDE = "#4fc3f7"     # cyan   - the AI
TECH = "#ba68c8"       # violet - the technical process
GREEN, RED = "#66bb6a", "#ef5350"
MUTED, TEXT = "#8b949e", "#e6edf3"

# ---- Road-survey display language.
# Same amber/cyan/violet theme, a distinct LOOK from the sibling apps: chainage
# readouts, lane-marking rules, reflective signboard cards, and a survey-run rail.
STEEL = "#141b24"      # panel variant for cards
INK = "#0b0e13"        # deep panel for readouts
EDGE = "#2b3440"       # hairline borders
MONOF = "ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', monospace"

_CSS = """
<style>
.stApp {
  background-image:
    repeating-linear-gradient(90deg, rgba(255,255,255,.03) 0 34px, transparent 34px 78px);
  background-size: 100% 3px;
  background-repeat: no-repeat;
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
  background:#141b24; border:1px solid #2b3440; border-left:3px solid #ffb74d;
  border-radius:2px; padding:10px 12px;
}
[data-testid="stMetricValue"] { font-family:%(MONO)s; }
.ch-row { display:flex; align-items:center; gap:10px; margin:22px 0 12px; }
.ch-num { font-family:%(MONO)s; font-size:12px; font-weight:700; border:1px solid;
  padding:1px 7px; border-radius:2px; letter-spacing:.04em; white-space:nowrap; }
.ch-label { font-family:%(MONO)s; text-transform:uppercase; letter-spacing:.14em;
  font-size:13px; font-weight:700; white-space:nowrap; }
.ch-rule { flex:1; height:3px;
  background:repeating-linear-gradient(90deg,#2b3440 0 14px,transparent 14px 26px); }
.sign { position:relative; background:#141b24; border:1px solid #2b3440;
  border-left:4px solid #ffb74d; padding:14px 18px; color:#e6edf3;
  font-size:16px; line-height:1.65; margin:2px 0; border-radius:2px; }
.sign.ai   { border-left-color:#4fc3f7; }
.sign.tech { border-left-color:#ba68c8; }
.sign.warn { border-left-color:#ef5350; }
.sign.ok   { border-left-color:#66bb6a; }
.km-bar { font-family:%(MONO)s; background:#0b0e13; border:1px solid #2b3440;
  border-left:3px solid #ffb74d; padding:8px 14px; font-size:12px; letter-spacing:.06em;
  color:#8b949e; border-radius:2px; }
.marker { font-family:%(MONO)s; text-align:center; border:1px solid #ffb74d; border-radius:2px;
  background:#0b0e13; padding:6px 4px; font-size:11px; color:#8b949e; line-height:1.5; }
.marker b { color:#ffb74d; font-size:13px; }
.runbar { display:flex; flex-wrap:wrap; align-items:center; gap:5px; background:#0b0e13;
  border:1px solid #2b3440; border-radius:2px; padding:9px 12px; }
.runlab { font-family:%(MONO)s; font-size:11px; letter-spacing:.12em; color:#8b949e; margin-right:4px; }
.ph { font-family:%(MONO)s; font-size:11px; padding:2px 6px; border:1px solid #2b3440;
  color:#3f4650; border-radius:2px; }
.ph.done { color:#ffb74d; border-color:#5a4a2a; }
.ph.cur { background:#ffb74d; color:#0b0e13; border-color:#ffb74d; font-weight:700; }
.brief { position:relative; border:1px solid #2b3440; background:#0b0e13; padding:20px 24px;
  border-radius:2px; }
.brief::after { content:''; position:absolute; left:0; right:0; bottom:0; height:4px;
  background:repeating-linear-gradient(90deg,#ffb74d 0 24px,transparent 24px 44px); }
.brief-bar { font-family:%(MONO)s; font-size:12px; letter-spacing:.16em; color:#ffb74d; margin-bottom:8px; }
.card-ico { display:inline-flex; align-items:center; justify-content:center; width:40px; height:40px;
  border:1px solid #2b3440; border-radius:2px; font-size:22px; margin-bottom:8px; background:#0b0e13; }
.muted { color:#8b949e; font-size:13px; }
.substep { font-family:%(MONO)s; color:#8b949e; font-size:13px; }
</style>
""".replace("%(MONO)s", MONOF)   # not %-formatting: the CSS contains literal '%' (100%)


def inject_css():
    """Load the road-survey display language once. Call after st.set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def _ch_header(ch, label, color):
    st.markdown(
        f"<div class='ch-row'>"
        f"<span class='ch-num' style='color:{color};border-color:{color}'>CH·{ch}</span>"
        f"<span class='ch-label' style='color:{color}'>{label}</span>"
        f"<span class='ch-rule'></span></div>", unsafe_allow_html=True)


# ============================================================================
# THE ENGINEERING WORKFLOW
# The phases of a pavement management programme. Every AI concept hangs off one
# of them. The last one is the programme the work is judged by.
# ============================================================================
PHASES = [
    ("The Road Network",       "Thousands of segments, one maintenance budget."),
    ("How Pavements Fail",     "Load and climate — and whichever arrives first."),
    ("The Condition Survey",   "An inspection becomes a row of measurements."),
    ("The Survey Export",      "The network file lands and gets checked."),
    ("Preparing The Data",     "Bad records out, the network split by road."),
    ("Learning Deterioration", "The rule the agency runs, then the models that beat it."),
    ("Reading The Model",      "Which factors drive the prediction, and why."),
    ("The Prediction",         "Six measurements in, remaining service life out."),
    ("The Pavement Audit",     "Every prediction checked against what happened."),
    ("Maintenance Planning",   "One recommendation per segment, and what it is worth."),
]


# ============================================================================
# THE STEPS  (one per page; len(STEPS) is the count - never hardcode it)
#   civil / ai   - the two names of the same idea (amber name, cyan name)
#   tech         - what is actually computed (violet)
#   site         - Civil Engineering. NO AI in this text. 2-4 sentences.
#   challenge    - The Challenge. Why the manual way runs out of road.
#   ai_link      - AI Connection. Why this AI concept is therefore required.
#   takeaway     - Key Takeaway. ONE sentence.
#   notebook     - In the Notebook. Where this lives in the Colab notebook.
#   contributes  - In the Notebook. What this step contributes to the system.
#   short        - the mind-map label.
# ============================================================================
STEPS = [

# ---------------------------------------------- PHASE 1 - THE ROAD NETWORK
dict(
    id='road-network', phase=0, short='The network',
    civil='A Highway Network Under Load', ai='Why Asset Management Needs AI',
    civil_icon='🛣️', ai_icon='🤖',
    tech='Continuous deterioration vs a periodic inspection cycle',
    civil_bullets=['1,500 segments', 'All deteriorating', 'One budget'],
    ai_bullets=['Assess every segment', 'Model the drivers', 'Rank the network'],
    site="""A state highway agency maintains 1,500 pavement segments — national highways, state highways and
district roads. Every segment carries traffic every day. Every segment is ageing. The budget covers about
7% of the network a year.""",
    challenge="""A pavement does not fail on a schedule. It fails when accumulated axle loads and climate exhaust the
structure built for it. Two segments built the same year, to the same drawing, can be eight years apart in
condition because one carries loaded trucks and the other does not. The agency inspects on a cycle and
repairs on a cycle. The pavements do not.""",
    ai_link="""Nothing here needs judgement replaced. It needs arithmetic done at scale — combining traffic,
structure, age, climate and observed distress into a current estimate of how many years each segment has
left, so the budget goes to the right segments this year.""",
    notebook="""Step 1. The three numbers that define the problem: segments, kilometres treatable, share per year.""",
    contributes="""The framing for everything after it: this is a ranking problem under a fixed budget.""",
    takeaway="""The agency can treat 7% of the network a year — so the whole job is deciding which 7%.""",
),
dict(
    id='enter-ai', phase=0, short='Engineer + AI',
    civil='The Engineer Stays In Charge', ai='A Decision Support System',
    civil_icon='👷', ai_icon='🧭',
    tech='The model proposes; the engineer authorises',
    civil_bullets=['Reads the core', 'Knows the drain', 'Signs the estimate'],
    ai_bullets=['Ranks the network', 'Proposes a treatment', 'Attaches its reasons'],
    site="""Nothing about the engineering changes. The engineer still walks the section, still reads the cores,
still judges whether a stretch can be closed during harvest season, and still signs the estimate.""",
    challenge="""The usual objection deserves a straight answer. Is this here to replace the pavement engineer? No. A
model cannot see that a drain has been blocked by a new building, cannot know a quarry is opening next
year, and cannot carry the consequence of a road that fails under traffic.""",
    ai_link="""What the model does is duller and genuinely beyond one person: evaluate every segment, every survey
cycle, against six measurements at once — and say which one first, with its reasons attached. Four
treatments are possible, and they differ by roughly an order of magnitude in cost.""",
    notebook="""Step 2. The table of what the engineer keeps and what the system takes on.""",
    contributes="""Fixes the system's output: a recommendation to an engineer, never an automatic work order.""",
    takeaway="""Highway Engineer + AI. The model ranks and explains; the engineer decides and signs.""",
),

# ---------------------------------------------- PHASE 2 - HOW PAVEMENTS FAIL
dict(
    id='deterioration', phase=1, short='Why roads fail',
    civil='Why Pavements Deteriorate', ai='The Physics The Model Must Learn',
    civil_icon='🚛', ai_icon='📐',
    tech='The fourth-power law: damage = (axle load / 80 kN)⁴',
    civil_bullets=['Each axle bends it', 'Damage is not linear', 'Climate is the second cause'],
    ai_bullets=['A non-linear target', 'Count axles, not vehicles', 'One unit: the ESAL'],
    site="""A flexible pavement fails from the accumulation of individual axle passes. Each pass bends the layers a
little. The bending fatigues the bound layers and permanently deforms the unbound ones.""",
    challenge="""Damage is not proportional to load. It is proportional to roughly the fourth power of it — the result of
the AASHO Road Test, and the reason pavement engineers count axles rather than vehicles. One legal truck
axle does the damage of about 65,000 car axles. Overload it by a quarter and it does 2.4 times as much.""",
    ai_link="""Any model predicting pavement life must reproduce a strongly non-linear response to load. A model that
can only add up weighted inputs cannot. That is the first concrete reason a straight line will not be
enough.""",
    notebook="""Step 3. The fourth-power table, and the damage curve from 20 to 130 kN.""",
    contributes="""The load mechanism, quantified — and the first argument for non-linear models.""",
    takeaway="""Damage goes as load⁴ — a fact no straight-line model can represent.""",
),
dict(
    id='service-life', phase=1, short='Remaining life',
    civil="What 'Remaining Service Life' Means", ai='Defining The Target Variable',
    civil_icon='📉', ai_icon='🎯',
    tech='AASHTO 1993: allowable ESALs from structural number and subgrade modulus',
    civil_bullets=['PSI 4.2 when new', 'Terminal at 2.5', 'Years to that point'],
    ai_bullets=['One continuous value', 'Regression, not classes', 'The target, y'],
    site="""Serviceability falls from about 4.2 on a new pavement to a terminal value — commonly 2.5 on a highway —
at which the agency has committed to intervene. Remaining service life is the number of years from today
until that condition is reached.""",
    challenge="""It cannot be measured today. It depends on a structure that is buried, a subgrade tested once before
construction, traffic that will grow, and weather that has not happened yet. What can be computed is the
design capacity, and the AASHTO 1993 equation does exactly that.""",
    ai_link="""This is the number the model predicts: one continuous value, in years. A continuous target makes this a
regression problem, not a classification problem — and that choice drives which models apply and which
error measures mean anything.""",
    notebook="""Step 4. The AASHTO design equation, the capacity table, and the serviceability decay curves.""",
    contributes="""The target variable, grounded in a design standard rather than invented.""",
    takeaway="""The target is one continuous number — years to terminal condition — so this is regression.""",
),

# ---------------------------------------------- PHASE 3 - THE CONDITION SURVEY
dict(
    id='inspection', phase=2, short='The survey run',
    civil='One Pavement Inspection', ai='Where The Data Comes From',
    civil_icon='🔍', ai_icon='📊',
    tech='Six measurements per segment, collected four different ways',
    civil_bullets=['Survey vehicle', 'Traffic counter', 'Core log & met station'],
    ai_bullets=['Condition features', 'Loading features', 'Structure & climate'],
    site="""A network survey vehicle covers the section at traffic speed. Behind it, or alongside it, sit four
independent data sources — and they arrive on four different schedules.""",
    challenge="""No single instrument sees the whole problem. The roughness profiler says nothing about the structure
underneath. The traffic counter says nothing about condition. The core log is five years old. The engineer
holds all of them together mentally; the file does not.""",
    ai_link="""Machine learning starts here, not at the model. Each measurement becomes a feature — a named column
describing one segment. Getting the columns right matters more than the choice of algorithm.""",
    notebook="""Step 5. The measurement inventory: what is collected, by whom, and what it stands for.""",
    contributes="""The six model inputs, and the two optional instruments held back for later.""",
    takeaway="""Every feature in this project is a measurement a highway agency already collects.""",
),
dict(
    id='one-record', phase=2, short='One segment',
    civil='One Segment Becomes One Row', ai='Structured Data',
    civil_icon='📋', ai_icon='🗂️',
    tech='One kilometre of road → one labelled record',
    civil_bullets=['One kilometre', 'Eight recorded facts', 'One known outcome'],
    ai_bullets=['One row', 'Six features', 'One label, y'],
    site="""Segment SH-021/07: kilometre 7 of a state highway. Built 12 years ago, 240 mm of bituminous layers,
carrying 22,000 vehicles a day in a moderate climate. The last survey recorded 18% crack density.""",
    challenge="""An engineer reads that paragraph and forms a judgement. A computer cannot read a paragraph. It needs
the same facts as numbers in fixed positions, so a thousand segments can be compared on identical terms.""",
    ai_link="""That is what structured data means, and it is why pavement management is a natural machine learning
problem: agencies have recorded exactly these columns, in exactly this shape, for decades. The label comes
from the works file — the year the segment actually reached terminal condition — not from a formula.""",
    notebook="""Step 6. One segment printed as the model sees it, and where the label comes from.""",
    contributes="""The unit of learning. Everything downstream is rows like this one.""",
    takeaway="""Features are what you knew on survey day; the label is what the works file recorded afterwards.""",
),

# ---------------------------------------------- PHASE 4 - THE SURVEY EXPORT
dict(
    id='collect', phase=3, short='The export',
    civil='The Network Condition Survey', ai='Data Collection',
    civil_icon='🗃️', ai_icon='💾',
    tech='1,500 segments across 150 roads, three climate zones',
    civil_bullets=['Four systems', 'Four teams', 'One file'],
    ai_bullets=['read_csv', 'One row per segment', 'The label column'],
    site="""The full survey export lands: every segment on the network, with its structure, traffic, climate and
measured distress, plus the outcome recorded for each one in the works file.""",
    challenge="""It is not a clean file. It has been assembled from four systems by four teams, some typed by hand, some
exported by instruments that report their own error codes as ordinary numbers.""",
    ai_link="""Load it first, look at it second, believe it third. The order matters — most of the damage done by
machine learning in engineering is done by trusting a file nobody opened.""",
    notebook="""Step 7. The survey is built from the AASHTO relationships, written to CSV, then loaded back.""",
    contributes="""The dataset every later step reads from.""",
    takeaway="""An export is raw material, not a dataset. Loading it is where the data work starts.""",
),
dict(
    id='inspect-data', phase=3, short='Health check',
    civil='Checking The Survey First', ai='Data Inspection',
    civil_icon='🧐', ai_icon='🔎',
    tech='Range checks, missing values, duplicates, units',
    civil_bullets=['Credible thicknesses?', 'Any segment twice?', 'Right units?'],
    ai_bullets=['describe()', 'Range checks', 'Distribution by district'],
    site="""Before a design office uses a survey, it checks it. Are the thicknesses credible? Is any segment listed
twice? Did the met station report every month? Did a district submit in the wrong units?""",
    challenge="""Instruments do not report 'missing'. They report a number — −1, 0, 999 — and a spreadsheet cannot tell
that apart from a measurement. A crack density of −1% is obviously wrong to an engineer and perfectly
acceptable to a model, which will happily learn from it.""",
    ai_link="""Data inspection is the engineering judgement stage of machine learning. Every check here is one a
pavement engineer already knows how to make. The only new part is doing it in code, on every column, every
time.""",
    notebook="""Step 8. `describe()`, a range check per column, duplicate count, temperature by district.""",
    contributes="""The fault list the cleaning step works from.""",
    takeaway="""An instrument never reports 'missing' — it reports a number, and only a range check catches it.""",
),
dict(
    id='clean', phase=4, short='Cleaning',
    civil='Correcting The Record', ai='Data Cleaning',
    civil_icon='🧹', ai_icon='🧼',
    tech='Convert, repair, impute, or drop — one decision per fault',
    civil_bullets=['Convert the units', 'Fill what you could look up', 'Drop what only a core knows'],
    ai_bullets=['Unit conversion', 'Group median impute', 'Deduplicate'],
    site="""The design office does not throw away a survey because six columns have problems. It corrects what can
be corrected, excludes what cannot, and writes down which it did.""",
    challenge="""The temptation is to delete every imperfect row. On this file that would discard a whole district — and
a whole climate zone — over a unit conversion that takes one line to fix.""",
    ai_link="""Cleaning is not deletion. Four faults get four different treatments, and the choice between them is an
engineering judgement about what the missing value would have been. Impute a value you could have looked
up. Drop a value only a measurement could have supplied.""",
    notebook="""Step 9. The cleaning log: converted, deduplicated, imputed, dropped — with counts.""",
    contributes="""A clean, deduplicated survey with every correction justified.""",
    takeaway="""Impute what you could have looked up; drop what only a measurement could have told you.""",
),

# ---------------------------------------------- PHASE 5 - PREPARING THE DATA
dict(
    id='features', phase=4, short='Scaling',
    civil='Putting Measurements On One Scale', ai='Feature Scaling',
    civil_icon='📏', ai_icon='⚖️',
    tech='StandardScaler: subtract the mean, divide by the standard deviation',
    civil_bullets=['Traffic in tens of thousands', 'Temperature near thirty', 'Cracking a percentage'],
    ai_bullets=['Standard deviations', 'Comparable coefficients', 'Trees do not need it'],
    site="""The six inputs are measured in six units. Traffic runs to tens of thousands. Temperature sits near
thirty. Crack density is a percentage of surface area.""",
    challenge="""To an engineer this is trivial — nobody thinks 22,000 vehicles and 31 °C are comparable numbers. To an
algorithm they are just numbers, and the largest one dominates simply because it is large.""",
    ai_link="""Scaling puts every feature in the same currency: standard deviations from its own mean. Linear
regression needs it if the coefficients are to be read against each other. Tree models do not — they split
on order, not magnitude — which is itself worth knowing.""",
    notebook="""Step 10. The before-scaling table, the six input distributions, and the target distribution.""",
    contributes="""Inputs a coefficient-based model can be read from.""",
    takeaway="""Scaling makes coefficients comparable; it does not make features important.""",
),
dict(
    id='split', phase=4, short='Split by road',
    civil='Holding Back Roads, Not Rows', ai='The Train/Test Split',
    civil_icon='✂️', ai_icon='🧪',
    tech='GroupShuffleSplit by road — segments of one road never straddle the split',
    civil_bullets=['Same subgrade', 'Same contractor', 'Same traffic stream'],
    ai_bullets=['Grouped samples', 'GroupShuffleSplit', 'An honest test set'],
    site="""To know whether the model works, it must be tested on segments it has never seen. The obvious way is to
hold back a random 30% of the rows.""",
    challenge="""The obvious way is wrong here. Kilometre 6 and kilometre 7 of the same highway share a subgrade, a
climate, a contractor, a construction year and a traffic stream. They are nearly the same pavement. Split
at random and one goes into training while its near-twin goes into testing.""",
    ai_link="""Split by road, not by segment. Every kilometre of a road lands entirely in training or entirely in
testing — which is the situation the model faces in service, where it is asked about a road nobody has
surveyed yet. The notebook measures exactly how much the naive split would have flattered the score.""",
    notebook="""Step 11. GroupShuffleSplit by road_id, then the same model scored both ways.""",
    contributes="""An honest test set, and a number for the cost of getting the split wrong.""",
    takeaway="""Adjacent kilometres are near-duplicates — split by road or the score measures memory.""",
),

# ---------------------------------------------- PHASE 6 - LEARNING DETERIORATION
dict(
    id='baseline', phase=5, short='The fixed cycle',
    civil='The Rule The Agency Already Runs', ai='The Baseline',
    civil_icon='📅', ai_icon='📏',
    tech='Remaining life = design life − age',
    civil_bullets=['Assume a design life', 'Subtract the age', 'Resurface at zero'],
    ai_bullets=['The baseline predictor', 'Its error, in years', 'The bar to clear'],
    site="""Most agencies run a fixed cycle: assume a design life, subtract the age, and resurface when the number
reaches zero. Some add a condition trigger — resurface early if cracking passes a threshold.""",
    challenge="""The rule ignores traffic, thickness and climate entirely. Two segments of the same age get the same
answer whether one carries 40,000 vehicles a day and the other carries 900.""",
    ai_link="""Before claiming a model helps, measure what it must beat. A baseline that is never computed is a
baseline that is always beaten — in the presentation, if nowhere else.""",
    notebook="""Step 12. The fixed cycle and the cracking-triggered rule, both scored on the held-out roads.""",
    contributes="""The bar every later model is measured against, in the same units.""",
    takeaway="""The fixed cycle ignores traffic, structure and climate — and its error says so.""",
),
dict(
    id='linear', phase=5, short='Linear regression',
    civil='A First Model: Everything Adds Up', ai='Linear Regression',
    civil_icon='📈', ai_icon='🧮',
    tech='ŷ = b₀ + b₁·traffic + b₂·thickness + … + b₆·cracking',
    civil_bullets=['Thicker adds life', 'Older subtracts it', 'Fixed effect each'],
    ai_bullets=['One coefficient each', 'No interactions', 'Least squares'],
    site="""The first honest attempt: assume each factor contributes a fixed number of years per unit, independent
of everything else. Thicker adds life. Older subtracts it. More cracking subtracts more.""",
    challenge="""Pavement deterioration is not additive. Damage goes as load to the fourth power, capacity rises far
faster than thickness, and the governing mechanism itself changes — a district road fails from ageing, a
national highway fails from trucks. A straight line has one coefficient per factor. It cannot say
'traffic matters here and not there'.""",
    ai_link="""Fit it anyway, and read the coefficients. They are interpretable in engineering units — years of life
per standard deviation of each input — and that interpretability is why linear regression is still the
right place to start.""",
    notebook="""Step 13. The fitted coefficients, then the residual plot that shows what the straight line costs.""",
    contributes="""An interpretable first model, and the evidence that a curve is needed.""",
    takeaway="""Linear regression gets every sign right and still misses, because deterioration is not additive.""",
),
dict(
    id='forest', phase=5, short='Random forest',
    civil='Letting The Data Split Itself', ai='Random Forest Regression',
    civil_icon='🌲', ai_icon='🌳',
    tech='Many decision trees on random subsets, averaged',
    civil_bullets=['Engineers reason in cases', 'Thin under trucks', 'Thick in a wet district'],
    ai_bullets=['Tree splits', 'Interactions, learned', 'Averaged over trees'],
    site="""A pavement engineer does not apply one formula to the whole network. They reason in cases: thin section
under heavy trucks is one case, thick section in a wet district is another, and each has its own rule of
thumb.""",
    challenge="""Writing those cases down as a rulebook fails for the same reason the fixed cycle fails — the thresholds
differ for every road class, climate zone and structure, and nobody can enumerate them.""",
    ai_link="""A decision tree discovers the cases from the data: it repeatedly splits the network on whichever
measurement best separates long-lived from short-lived segments. A random forest grows hundreds of such
trees on random subsets and averages them, which stops any one tree from over-fitting its own sample.""",
    notebook="""Step 14. The forest, then one tree printed three levels deep as an engineer's rulebook.""",
    contributes="""The first model that can represent an interaction between structure and loading.""",
    takeaway="""Trees earn their keep by asking a different next question in every branch — that is an interaction.""",
),
dict(
    id='boosting', phase=5, short='Boosting',
    civil='Correcting The Previous Estimate', ai='Gradient Boosting & XGBoost',
    civil_icon='🪜', ai_icon='🚀',
    tech='Each new tree is fitted to the error the previous trees left behind',
    civil_bullets=['First estimate goes out', 'Reviewer marks the misses', 'Next revision corrects them'],
    ai_bullets=['Fit the residual', 'Sequential trees', 'Learning rate'],
    site="""A design office revises. The first estimate goes out, the reviewer marks where it was optimistic, and
the next revision corrects exactly those cases.""",
    challenge="""A random forest cannot do that. Its trees are grown independently and averaged — none of them knows
where the others were wrong.""",
    ai_link="""Gradient boosting builds trees in sequence, each fitted to the residual error of everything before it.
On structured engineering tables with strong interactions this is usually the strongest model family
available, and XGBoost is its most used implementation.""",
    notebook="""Step 15. Gradient Boosting and XGBoost, then every predictor compared on the same held-out roads.""",
    contributes="""The model that goes forward, and the evidence for how much the choice was worth.""",
    takeaway="""The big win is using the engineering data at all; the choice of algorithm is the small win.""",
),

# ---------------------------------------------- PHASE 7 - READING THE MODEL
dict(
    id='importance', phase=6, short='What drives it',
    civil='Which Factors Drive Pavement Life', ai='Feature Importance',
    civil_icon='🧭', ai_icon='📊',
    tech='Permutation importance: shuffle one column, measure the damage',
    civil_bullets=['Does it match the standard?', 'Can it be defended?', 'Would an auditor accept it?'],
    ai_bullets=['Shuffle one column', 'Measure the error rise', 'Rank the six'],
    site="""An engineer reviewing this system asks one question before any other: does it agree with what we know
about pavements? If it ranks temperature above cracking, it has learned something wrong.""",
    challenge="""A model that is accurate but inexplicable cannot be signed off. Somebody has to defend the maintenance
programme in front of an audit committee, and 'the model said so' is not a defence.""",
    ai_link="""Permutation importance is the honest measure. Shuffle one column in the test set, destroying its
information while leaving everything else intact, and see how much the error rises. Big rise, important
feature. Read it as 'what is uniquely mine' — correlated features share credit and are under-credited.""",
    notebook="""Step 16. Permutation importance on the held-out roads, checked against the design standard.""",
    contributes="""The defensible ranking that lets an engineer sign the programme.""",
    takeaway="""Cracking dominates because it carries information about the causes nobody measured.""",
),
dict(
    id='explain', phase=6, short='One segment',
    civil="Explaining One Segment's Prediction", ai='Local Sensitivity',
    civil_icon='🔬', ai_icon='🕵️',
    tech='Vary one input at a time, hold the rest at their surveyed values',
    civil_bullets=['Why this kilometre?', 'What would change it?', 'A sentence to defend'],
    ai_bullets=['One-at-a-time', 'Local, not network', 'Reasons attached'],
    site="""Network-level importance does not answer the question an engineer actually asks in a review: why does
this kilometre have five years and that one twelve?""",
    challenge="""The two segments differ on all six inputs at once. Attribution needs the effects separated, on this
segment, at these values — not on the network average.""",
    ai_link="""Hold the segment fixed and move one input at a time. The change in predicted life is that input's local
contribution. It is simple, exact for the model, and produces a sentence an engineer can check against
their own experience. Where the response is flat, that is information too.""",
    notebook="""Step 17. The worked segment, then a one-at-a-time sensitivity chart for all six inputs.""",
    contributes="""A per-segment explanation that turns a number into reasons.""",
    takeaway="""A prediction an engineer cannot interrogate is a prediction they cannot sign.""",
),
dict(
    id='instrumentation', phase=6, short='Buy the FWD?',
    civil='Is More Survey Equipment Worth Buying?', ai='Feature Selection, Priced',
    civil_icon='📡', ai_icon='➕',
    tech='Re-fit with roughness and deflection added; measure the gain',
    civil_bullets=['A deflectometer is slow', 'It stops traffic', 'It is a capital decision'],
    ai_bullets=['Add a feature, re-fit', 'Change in held-out error', 'Beat the noise floor'],
    site="""The survey already records roughness from the profiler. A falling weight deflectometer measures
structural stiffness directly — but it is slow, expensive, and stops traffic.""",
    challenge="""The agency has to decide whether to fund a deflection survey across the network. That is a capital
decision, and 'more data is better' is not an argument that survives a budget meeting.""",
    ai_link="""Feature selection answers it numerically. Fit the same model with the extra column and compare the
error on the same held-out roads. Crucially, compare the gain against the noise floor — hold back a
different 30% of the roads and the score moves on its own. A gain smaller than that is not a gain.""",
    notebook="""Step 18. Roughness and deflection added, each gain judged against the resampling noise floor.""",
    contributes="""A priced, evidence-based answer to a capital question.""",
    takeaway="""'More data is better' is a claim you can measure — so measure it before you buy the equipment.""",
),

# ---------------------------------------------- PHASE 8 - THE PREDICTION
dict(
    id='predict', phase=7, short='Predict a segment',
    civil='Predicting A Segment You Just Surveyed', ai='Inference',
    civil_icon='🎛️', ai_icon='🔮',
    tech='Six numbers in, one remaining-life estimate out',
    civil_bullets=['Crew returns', 'Six measurements', 'Estimate before the draft'],
    ai_bullets=['One inference', 'Move an input', 'Watch the answer move'],
    site="""A survey crew returns from a section. Six measurements go into the system. The engineer wants the
predicted remaining life before the estimate is drafted.""",
    challenge="""The value of a prediction is not the number. It is understanding why it moves — because that is what
tells the engineer which intervention would actually extend the life.""",
    ai_link="""This is inference: the trained model applied to a segment it has never seen. Change one input and watch
the answer move, and the deterioration relationships stop being abstract. Note the response is a curve,
not a line — and a tree model predicts in bands, so it has flat steps.""",
    notebook="""Step 19. Six scenarios, the cracking response curves, and interactive sliders.""",
    contributes="""The working predictor, with its response surface visible rather than assumed.""",
    takeaway="""The number matters less than the slope — what moves it is what tells you which treatment helps.""",
),

# ---------------------------------------------- PHASE 9 - THE PAVEMENT AUDIT
dict(
    id='audit', phase=8, short='The audit',
    civil='The Pavement Performance Audit', ai='Regression Metrics',
    civil_icon='📑', ai_icon='✅',
    tech='MAE, RMSE, R² and the error distribution, on held-out roads',
    civil_bullets=['Roads it never saw', 'Against the works file', 'Report the disagreement'],
    ai_bullets=['MAE — typical error', 'RMSE — the bad misses', 'R² — better than guessing'],
    site="""An agency does not adopt a method because it sounds reasonable. It audits it: take the roads the model
never saw, compare every prediction against what the works file recorded, and report the disagreement.""",
    challenge="""'Accurate' is not a number. A model wrong by six months on a twenty-year pavement is excellent. The
same six months on a segment with one year left is the difference between a seal and a reconstruction.""",
    ai_link="""Three measures, each answering a different question, plus the shape of the errors — which is where the
useful information usually hides. Watch the bias by band: a model can have an excellent overall score and
still be systematically optimistic about the segments that are nearly finished.""",
    notebook="""Step 20. The three metrics, predicted-vs-actual, the error distribution and bias by band.""",
    contributes="""The evidence base for every claim the business case later makes.""",
    takeaway="""One overall accuracy figure hides the only errors that matter: the optimistic ones near end of life.""",
),
dict(
    id='errors', phase=8, short='Error costs',
    civil='The Two Errors Do Not Cost The Same', ai='Asymmetric Loss',
    civil_icon='⚠️', ai_icon='💸',
    tech='Price each year of error by the treatment it triggers',
    civil_bullets=['Too early: asset wasted', 'Too late: it escalates', 'Not the same money'],
    ai_bullets=['Pessimistic error', 'Optimistic error', 'A cost, not a score'],
    site="""A prediction error becomes a cost when it changes the treatment. Predict too little life and sound
pavement is milled off early. Predict too much and the surface fails before the crew arrives.""",
    challenge="""Those two mistakes are not symmetric, and no statistical measure knows that. MAE treats a year of
optimism and a year of pessimism as identical. The works department does not.""",
    ai_link="""Convert years of error into currency using the agency's own treatment costs. The result is a single
number a finance committee understands, and a ratio that tells the engineer which way to lean when the
model is uncertain: where it is unsure, treat early.""",
    notebook="""Step 21. The cost of a year of each error, then the total timing cost of the rule vs the model.""",
    contributes="""The reason accuracy is not the score this project is judged on.""",
    takeaway="""Late costs several times more than early — so where the model is unsure, treat early.""",
),

# ---------------------------------------------- PHASE 10 - MAINTENANCE PLANNING
dict(
    id='decision', phase=9, short='The work list',
    civil='From A Number To A Treatment', ai='The Decision Support Layer',
    civil_icon='🧾', ai_icon='🤝',
    tech='Life bands, plus engineering overrides the model does not get a vote on',
    civil_bullets=['Four treatments', 'Standard practice applies', 'Reasons in the file'],
    ai_bullets=['Model output', 'Hard overrides', 'Recommendation + reasons'],
    site="""A predicted remaining life is not a work instruction. It becomes one when it is mapped to a treatment,
with the reasons written in language a works engineer can check.""",
    challenge="""Some knowledge belongs in a rule, not in a weight. A segment with 55% cracking needs structural
investigation whatever the model predicts, because water is already reaching the base — and that is
standard practice, not a statistical finding.""",
    ai_link="""So the decision layer has two parts: the model's prediction, and hard overrides written by engineers.
The overrides can only escalate a recommendation, never soften one. That asymmetry is deliberate — if the
two disagree, the conservative answer wins.""",
    notebook="""Step 22. The banding function with its overrides, then the ranked work list with reasons.""",
    contributes="""The product: a ranked work list an engineer can act on.""",
    takeaway="""Some knowledge belongs in a rule, not in a weight — and the rule always wins upward.""",
),
dict(
    id='dashboard', phase=9, short='The programme',
    civil='The Maintenance Planning Dashboard', ai='The Business Case',
    civil_icon='📊', ai_icon='💰',
    tech='Network programme and avoided cost, computed from the audit',
    civil_bullets=['Kilometres per treatment', 'What it costs', 'What is deferred'],
    ai_bullets=['Grouped predictions', 'Rate × quantity', 'Value from the audit'],
    site="""The output the agency actually uses: how many kilometres need each treatment, what the programme costs,
and what is deferred when the budget runs out.""",
    challenge="""The saving is easy to overstate, and infrastructure has heard it overstated before. The only honest way
is to compute it from the audit already performed on the held-out roads, with every assumption named and
visible.""",
    ai_link="""Two figures, both derived from the audit: reconstructions avoided by arriving before escalation, and
sound pavement not milled off early. Nothing else is counted. The model does not enlarge the budget — it
changes which kilometres it is spent on.""",
    notebook="""Step 23. The network programme, the business case from the audit, and the assumptions behind it.""",
    contributes="""The number the programme is approved or refused on.""",
    takeaway="""The model does not enlarge the budget; it changes which kilometres it is spent on.""",
),
]

BY_ID = {s["id"]: s for s in STEPS}
ORDER = [s["id"] for s in STEPS]


def _phase_steps(pi):
    return [s for s in STEPS if s["phase"] == pi]


def goto(stage):
    st.query_params["stage"] = stage
    st.rerun()


# ============================================================================
# CHECK YOUR UNDERSTANDING - one MCQ per stage
# ============================================================================
QUIZ = {
    "road-network": dict(
        q="The agency can treat about 7% of its network each year. What does that make the core problem?",
        options=["Detecting which roads are deteriorating",
                 "Ranking segments so the budget goes to the right ones",
                 "Measuring pavement thickness more accurately"],
        answer=1,
        why="Every segment is deteriorating — that is never in doubt. The scarce thing is budget, so the "
            "problem is ordering the network, not detecting damage."),
    "enter-ai": dict(
        q="Which of these stays with the engineer rather than the model?",
        options=["Comparing 1,500 segments against six factors each",
                 "Recomputing the ranking every survey cycle",
                 "Knowing the side drain was never actually built"],
        answer=2,
        why="The model only sees the columns it was given. Local knowledge that never reached the file — "
            "and the consequence of being wrong — stay with the engineer."),
    "deterioration": dict(
        q="An axle is overloaded by 25%, from 80 kN to 100 kN. Roughly how much more damage does it do?",
        options=["About 25% more", "About twice as much", "About 2.4 times as much"],
        answer=2,
        why="Damage goes as the fourth power of load: 1.25⁴ ≈ 2.44. That exponent is why traffic effects "
            "are strongly non-linear."),
    "service-life": dict(
        q="Remaining service life is measured in years and can take any value. What kind of problem is that?",
        options=["Classification", "Regression", "Clustering"],
        answer=1,
        why="A continuous target means regression — which decides the models that apply and the error "
            "measures that mean anything."),
    "inspection": dict(
        q="Why are four separate data sources needed for one segment?",
        options=["No single instrument sees condition, loading, structure and climate at once",
                 "Because agencies like redundancy",
                 "To make the dataset larger"],
        answer=0,
        why="The profiler says nothing about the buried structure; the counter says nothing about "
            "condition. Each source covers a different part of the problem."),
    "one-record": dict(
        q="Where does the label — the actual remaining life — come from?",
        options=["The same AASHTO formula that produced the features",
                 "The works file: the year the segment actually reached terminal condition",
                 "The engineer's opinion at survey time"],
        answer=1,
        why="If the label came from the same formula as the features, the model would only be learning "
            "your own assumption back. It comes from what actually happened."),
    "collect": dict(
        q="What is the right order when a survey export arrives?",
        options=["Believe it, load it, look at it", "Load it, look at it, believe it",
                 "Load it, believe it, look at it"],
        answer=1,
        why="Most of the damage done by machine learning in engineering is done by trusting a file nobody "
            "opened."),
    "inspect-data": dict(
        q="A crack density column contains the value −1. What is it?",
        options=["A very lightly cracked segment", "The survey vehicle's error code",
                 "A rounding artefact"],
        answer=1,
        why="Instruments do not report 'missing' — they report a number. Only a physical range check "
            "separates an error code from a measurement."),
    "clean": dict(
        q="Rainfall was imputed from the district median, but thickness was dropped. Why the difference?",
        options=["Rainfall matters less to the model",
                 "Rainfall is a district property you could have looked up; thickness is whatever that "
                 "contractor laid",
                 "Thickness had more missing values"],
        answer=1,
        why="Impute a value you could have looked up. Drop a value only a measurement could have "
            "supplied — filling it in would invent a structure that may not exist."),
    "features": dict(
        q="Which model actually needs the inputs scaled?",
        options=["Random Forest", "Linear Regression", "Both equally"],
        answer=1,
        why="Trees split on order, not magnitude, so scale does not affect them. Coefficients are only "
            "comparable to each other once the inputs share a scale."),
    "split": dict(
        q="Why must the split be by road rather than by row?",
        options=["Roads are easier to count",
                 "Adjacent kilometres share subgrade, climate, contractor and traffic — they are "
                 "near-duplicates",
                 "It produces a larger test set"],
        answer=1,
        why="Split at random and a segment's near-twin lands on the other side. The score then measures "
            "memory, not prediction."),
    "baseline": dict(
        q="Why compute the agency's existing fixed-cycle rule at all?",
        options=["To use it as a fallback if the model fails",
                 "So the model's value is measured rather than asserted",
                 "Because regulations require it"],
        answer=1,
        why="A baseline that is never computed is a baseline that is always beaten — in the presentation, "
            "if nowhere else."),
    "linear": dict(
        q="What can a linear model NOT represent about pavement deterioration?",
        options=["That cracking reduces life",
                 "That thickness increases life",
                 "That traffic matters on a highway but barely on a district road"],
        answer=2,
        why="One coefficient per factor means one effect everywhere. A changing relationship — an "
            "interaction — needs a model that can branch."),
    "forest": dict(
        q="What does a decision tree do that a straight line cannot?",
        options=["Ask a different next question in each branch",
                 "Fit the data more exactly",
                 "Use more input columns"],
        answer=0,
        why="That is exactly what an interaction is: the relevance of traffic depends on what the "
            "structure and the cracking already said."),
    "boosting": dict(
        q="How does gradient boosting differ from a random forest?",
        options=["It uses more trees",
                 "Each tree is fitted to the error the previous trees left behind",
                 "It scales the inputs first"],
        answer=1,
        why="Forest trees are grown independently and averaged. Boosted trees are sequential — each one "
            "is a revision of the last estimate."),
    "importance": dict(
        q="Crack density has by far the highest permutation importance. Why is that engineering-correct?",
        options=["Cracking is the only thing that causes pavement failure",
                 "It summarises damage from causes no other column recorded — drainage, subgrade, batch "
                 "quality",
                 "It is measured most accurately"],
        answer=1,
        why="Cracking is the observed consequence of everything that has already happened, including the "
            "things nobody wrote down."),
    "explain": dict(
        q="On one segment, thickness barely moves the prediction. What does that mean?",
        options=["Thickness is unimportant to pavement life",
                 "The model is broken",
                 "On this segment, at this thickness, structure is not the binding constraint"],
        answer=2,
        why="Local flatness is a statement about this segment, not about pavements. Quote network-level "
            "importance for the general claim."),
    "instrumentation": dict(
        q="A new instrument improves the model's error by less than the resampling noise floor. What follows?",
        options=["Buy it — any improvement is an improvement",
                 "The improvement is not distinguishable from a different sample of roads",
                 "Retrain with more trees"],
        answer=1,
        why="Hold back a different 30% of the roads and the score moves by more than that on its own. "
            "A gain smaller than the noise is not a gain."),
    "predict": dict(
        q="The predicted-life curve against cracking has flat steps. Why?",
        options=["The data is too coarse",
                 "A tree ensemble is piecewise constant — it predicts in bands",
                 "The model has not converged"],
        answer=1,
        why="Trees split the input space into regions and predict a constant in each. Small changes that "
            "stay inside a region register nothing."),
    "audit": dict(
        q="Which error would worry a maintenance engineer most?",
        options=["Pessimistic on segments with 20 years left",
                 "Optimistic on segments with under 2 years left",
                 "A slightly lower R²"],
        answer=1,
        why="Optimism near end of life means the programme arrives late on the segments least able to "
            "wait — which is exactly what the programme exists to prevent."),
    "errors": dict(
        q="Arriving a year late costs several times more than arriving a year early. What should the "
          "engineer do where the model is uncertain?",
        options=["Treat early", "Treat late", "Wait for a better model"],
        answer=0,
        why="With an asymmetric cost, the cheaper mistake is the one to make deliberately."),
    "decision": dict(
        q="A segment at 55% cracking is predicted to have 8 years left. What does the decision layer do?",
        options=["Follow the model — 8 years means preventive maintenance",
                 "Escalate: cracking that high means water is reaching the base",
                 "Ignore the segment until the next survey"],
        answer=1,
        why="Overrides can only escalate, never soften. Where standard practice and the model disagree, "
            "the conservative answer wins."),
    "dashboard": dict(
        q="What does the business case actually claim the model does?",
        options=["It reduces the total maintenance need",
                 "It changes which kilometres the fixed budget is spent on",
                 "It replaces the need for surveys"],
        answer=1,
        why="The model does not make the network younger or the budget larger. It reorders the "
            "programme — which is where the value comes from."),
}


def render_quiz(stage):
    """One check-your-understanding MCQ per stage."""
    q = QUIZ.get(stage)
    if not q:
        return
    st.write("")
    st.markdown("##### 📝 Check your understanding")
    st.markdown(f"**{q['q']}**")
    choice = st.radio("Select an answer", q["options"], index=None,
                      key=f"quiz_{stage}", label_visibility="collapsed")
    if choice is not None:
        correct = q["options"][q["answer"]]
        if choice == correct:
            st.success(f"✅ Correct. {q['why']}")
        else:
            st.error(f"❌ Not quite — the answer is **{correct}**.\n\n{q['why']}")


# ============================================================================
# THE BRIDGE FIGURE
# Left = the road (amber). Right = the AI (cyan). Between them a carriageway
# the survey data travels along, and under it the technical process (violet).
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
    """A reflective signboard: dark panel, coloured post on the near edge."""
    fig.add_shape(type="rect", x0=x0, x1=x1, y0=0.8, y1=5.35,
                  line=dict(color=EDGE, width=1), fillcolor=STEEL, layer="below")
    fig.add_shape(type="line", x0=x0, y0=0.8, x1=x0, y1=5.35,
                  line=dict(color=color, width=4), layer="above")
    cx = (x0 + x1) / 2
    fig.add_annotation(x=cx, y=4.98, text=f"▍{kicker}", showarrow=False,
                       font=dict(size=11, color=color, family=MONOF), xanchor="center")
    fig.add_annotation(x=cx, y=4.18, text=icon, showarrow=False,
                       font=dict(size=34), xanchor="center")
    fig.add_annotation(x=cx, y=3.28, text=f"<b>{_wrap(title)}</b>", showarrow=False,
                       font=dict(size=14, color=TEXT), xanchor="center", align="center")
    for i, b in enumerate(bullets):
        fig.add_annotation(x=cx, y=2.45 - i * 0.52, text=f"› {b}", showarrow=False,
                           font=dict(size=12, color=MUTED, family=MONOF), xanchor="center")


def bridge_figure(step, style, animate):
    """The civil-activity -> AI-equivalent -> technical-process bridge, drawn as a
    carriageway with the survey record travelling along it."""
    fig = go.Figure()
    _card(fig, 0.2, 3.4, CIVIL, step["civil_icon"], step["civil"],
          step["civil_bullets"], "ON THE NETWORK")
    _card(fig, 6.6, 9.8, AISIDE, step["ai_icon"], step["ai"],
          step["ai_bullets"], "IN THE AI")

    # the carriageway: two edge lines and a dashed centre line
    for yy in (3.30, 2.70):
        fig.add_shape(type="line", x0=3.45, y0=yy, x1=6.35, y1=yy,
                      line=dict(color=EDGE, width=2), layer="below")
    x = 3.55
    while x < 6.3:
        fig.add_shape(type="line", x0=x, y0=3.0, x1=min(x + 0.22, 6.3), y1=3.0,
                      line=dict(color="#3a4655", width=2), layer="below")
        x += 0.44
    fig.add_annotation(x=6.55, y=3.0, ax=6.3, ay=3.0, xref="x", yref="y",
                       axref="x", ayref="y", showarrow=True, arrowhead=2,
                       arrowsize=1.6, arrowwidth=2.5, arrowcolor=AISIDE, text="")
    fig.add_annotation(x=4.9, y=3.62, text="⇒ BECOMES ⇒", showarrow=False,
                       font=dict(size=11, color=MUTED, family=MONOF))

    # the compute block (violet)
    fig.add_shape(type="rect", x0=3.5, x1=6.5, y0=1.25, y1=2.15,
                  line=dict(color=EDGE, width=1), fillcolor=INK, layer="below")
    fig.add_shape(type="line", x0=3.5, y0=1.25, x1=3.5, y1=2.15,
                  line=dict(color=TECH, width=4), layer="above")
    fig.add_annotation(x=5.0, y=2.02, text="▍COMPUTED AS", showarrow=False,
                       font=dict(size=9, color=TECH, family=MONOF))
    fig.add_annotation(x=5.0, y=1.62, text=_wrap(step["tech"], 30), showarrow=False,
                       font=dict(size=9.5, color=TEXT, family=MONOF),
                       xanchor="center", yanchor="middle", align="center")
    fig.add_annotation(x=5.0, y=2.42, text="▼", showarrow=False,
                       font=dict(size=13, color=TECH))

    # the survey record travels the carriageway from the road into the AI
    fig.add_trace(go.Scatter(x=[3.5], y=[3.0], mode="markers",
                             marker=dict(size=13, color=CIVIL, symbol="square",
                                         line=dict(color=INK, width=1)),
                             hoverinfo="skip", showlegend=False))
    frames = []
    for i in range(24):
        t = i / 23
        xx = 3.5 + t * 2.85
        c = CIVIL if t < 0.45 else (TEXT if t < 0.55 else AISIDE)
        frames.append(go.Frame(data=[go.Scatter(
            x=[xx], y=[3.0], mode="markers",
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
            if st.button(f"◀  {prev_s['civil']}", key=f"prev_{key}", use_container_width=True):
                goto(prev_s["id"])
        else:
            if st.button("◀  The project overview", key=f"prev_{key}", use_container_width=True):
                goto("start")
    with c2:
        st.markdown(
            f"<div class='marker'>▐ STEP {i+1:02d} / {len(ORDER):02d} ▌"
            f"<br><b>{step['civil']}</b></div>", unsafe_allow_html=True)
    with c3:
        if next_s:
            if st.button(f"{next_s['civil']}  ▶", key=f"next_{key}", use_container_width=True):
                goto(next_s["id"])
        else:
            if st.button("Back to the overview  ▶", key=f"next_{key}", use_container_width=True):
                goto("start")


# ============================================================================
# open_page  -  Parts 1, 2 and 3, rendered ABOVE the stage renderer
# ============================================================================
def open_page(stage, style, animate):
    step = BY_ID.get(stage)
    if step is None:
        return
    pname, pdesc = PHASES[step["phase"]]

    _nav_strip(step, "top")
    i = ORDER.index(stage)
    st.markdown(
        f"<div class='km-bar' style='margin-top:14px'>⟨PAVEMENT MANAGEMENT⟩ &nbsp; "
        f"STEP {i+1:02d}/{len(ORDER)} &nbsp;·&nbsp; PHASE {step['phase']+1:02d}/{len(PHASES)} "
        f"&nbsp;·&nbsp; <span style='color:{CIVIL}'>{pname.upper()}</span> "
        f"&nbsp;—&nbsp; {pdesc}</div>", unsafe_allow_html=True)
    st.markdown(f"# {step['civil_icon']}  {step['civil']}")
    st.markdown(
        f"<span class='substep'>▸ this highway engineering step is the AI concept </span>"
        f"<b style='color:{AISIDE}'>{step['ai']}</b>", unsafe_allow_html=True)
    st.divider()

    _ch_header("10", "Civil Engineering", CIVIL)
    st.markdown(f"<div class='sign'>{step['site']}</div>", unsafe_allow_html=True)
    st.write("")

    _ch_header("20", "The Challenge", RED)
    st.markdown(f"<div class='sign warn'>{step['challenge']}</div>", unsafe_allow_html=True)
    st.write("")

    _ch_header("30", "AI Connection", AISIDE)
    st.markdown(f"<div class='sign ai'>{step['ai_link']}</div>", unsafe_allow_html=True)
    st.plotly_chart(bridge_figure(step, style, animate), use_container_width=True,
                    key=f"bridge_{stage}")
    st.caption("▶ Press Play — the survey record travels the carriageway into the AI.")
    st.divider()

    _ch_header("40", "Technical Idea", TECH)
    st.caption(f"{step['tech']} — interactive. Change things and watch what happens.")


# ============================================================================
# close_page  -  Part 5, rendered BELOW the stage renderer
# ============================================================================
def close_page(stage):
    step = BY_ID.get(stage)
    if step is None:
        return
    st.divider()

    _ch_header("50", "Key Takeaway", GREEN)
    st.markdown(f"<div class='sign ok' style='font-size:19px;font-weight:600;line-height:1.5'>"
                f"{step['takeaway']}</div>", unsafe_allow_html=True)
    st.write("")

    _ch_header("60", "In the Notebook", "#8bc34a")
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
        f"<div class='runbar'><span class='runlab'>SURVEY RUN</span>"
        + "".join(segs)
        + f"<span class='runlab' style='margin-left:auto'>PH {step['phase']+1:02d}/{len(PHASES)}"
        f" · {PHASES[step['phase']][0].upper()}</span></div>", unsafe_allow_html=True)


# ============================================================================
# THE INTERACTIVE ENGINEERING MIND MAP
# A vertical spine of the project's phases. Every node opens that learning page.
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

    GAP, X0 = 3.4, 1.7
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
        marker=dict(size=20, color=INK, line=dict(color=AISIDE, width=2), symbol="hexagon"),
        hovertemplate="%{hovertext}<extra></extra>", hovertext=shover, showlegend=False))

    fig.update_xaxes(visible=False, range=[-7.0, X0 + (maxk - 1) * GAP + 2.2])
    fig.update_yaxes(visible=False, range=[-1.0, (n - 1) * VGAP + 0.6])
    return style(fig, h=int((n - 1) * VGAP * 78) + 150)


# ============================================================================
# THE CIVIL-ENGINEERING-TO-AI MAPPING
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

    fig.add_annotation(x=0, y=n - 0.35, text="▍HIGHWAY ENGINEERING PROCESS",
                       showarrow=False, xanchor="left",
                       font=dict(size=12, color=CIVIL, family=MONOF))
    fig.add_annotation(x=4.6, y=n - 0.35, text="▍THE AI PROCESS THAT SOLVES IT",
                       showarrow=False, xanchor="left",
                       font=dict(size=12, color=AISIDE, family=MONOF))

    fig.update_xaxes(visible=False, range=[-0.2, 9.0])
    fig.update_yaxes(visible=False, range=[-0.8, n + 0.2])
    return style(fig, h=60 * n + 120)


# ============================================================================
# THE OPENING PAGE
# ============================================================================
def render_start(style, animate):
    st.markdown(
        f"<div class='brief'>"
        f"<div class='brief-bar'>PROJECT BRIEF · PMS-001 · REV A · "
        f"{len(PHASES)} PHASES / {len(STEPS)} STEPS</div>"
        f"<div style='font-size:32px;font-weight:800;color:{TEXT}'>"
        f"🛣️ &nbsp;AI for Pavement Remaining Service Life Prediction</div>"
        f"<div style='color:{MUTED};font-size:15px;margin-top:6px'>"
        f"A learning platform for Civil Engineering students. The notebook teaches implementation; "
        f"this app teaches the ideas.</div></div>", unsafe_allow_html=True)
    st.write("")

    # ---------------------------------------------- SECTION 1: THE PROBLEM
    _ch_header("01", "The Engineering Problem", CIVIL)
    st.markdown("""
A state highway agency maintains **1,500 pavement segments**. Every one of them deteriorates every day,
under traffic it did not choose and weather nobody controls. The causes are ordinary: **heavy traffic,
axle overloading, thin sections, ageing bitumen, rainfall entering the base, and heat.**

The budget treats about **7% of the network a year**. So the question is never *is this road
deteriorating* — it always is. The question is **which kilometres, this year.**

Both wrong answers are expensive:
""")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div class='sign warn'><b style='color:{RED}'>Repaired too early</b><br>"
                    f"Sound pavement is milled off. Years of paid-for service life are thrown away."
                    f"</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='sign warn'><b style='color:{RED}'>Repaired too late</b><br>"
                    f"The surface fails, water reaches the base, and an overlay becomes a reconstruction."
                    f"</div>", unsafe_allow_html=True)
    st.write("")
    st.caption("Traditional practice answers with a fixed cycle: assume a design life, subtract the age, "
               "resurface. That rule ignores traffic, structure and climate entirely.")
    st.divider()

    # ---------------------------------------------- SECTION 2: THE GOAL
    _ch_header("02", "What We Are Going To Build", CIVIL)
    st.markdown("A **pavement management decision support system**. Four parts:")
    cols = st.columns(4)
    for col, (icon, title, body) in zip(cols, [
        ("🚐", "The condition survey",
         "Traffic, thickness, age, rainfall, temperature and cracking — six measurements per kilometre."),
        ("🧹", "Data preparation",
         "Unit errors, instrument codes, duplicates and gaps, each handled by engineering judgement."),
        ("🧠", "The prediction model",
         "Four regression models, all judged on roads they have never seen."),
        ("🧾", "The maintenance programme",
         "A remaining-life estimate and a recommended treatment for every segment, with reasons."),
    ]):
        with col:
            st.markdown(f"<div class='sign' style='height:100%'>"
                        f"<span class='card-ico'>{icon}</span><br>"
                        f"<b>{title}</b><br><span class='muted'>{body}</span></div>",
                        unsafe_allow_html=True)
    st.write("")
    st.info("**The goal is not an unmanned agency.** The engineer still reads the core, still knows the "
            "drain was never built, still sequences work around the monsoon, and still signs the "
            "estimate. The system does the thing one person cannot: assess 1,500 segments every cycle "
            "and say **which one first**.")
    st.divider()

    # ---------------------------------------------- SECTION 3: THE MIND MAP
    _ch_header("03", "The Engineering Mind Map", CIVIL)
    st.caption(f"The whole course as one maintenance programme — {len(PHASES)} phases, "
               f"{len(STEPS)} steps. **Click any hexagon to open that page.**")
    ev = st.plotly_chart(mind_map(style), use_container_width=True, key="mindmap",
                         on_select="rerun", selection_mode="points")
    try:
        pts = ev["selection"]["points"]
        if pts:
            goto(pts[0]["customdata"])
    except (KeyError, TypeError, IndexError):
        pass

    st.markdown("**Or jump straight to a phase:**")
    for pi, (pname, _) in enumerate(PHASES):
        kids = _phase_steps(pi)
        cols = st.columns(max(len(kids), 4))
        for col, s in zip(cols, kids):
            with col:
                if st.button(f"{s['civil_icon']} {s['short']}", key=f"jump_{s['id']}",
                             use_container_width=True):
                    goto(s["id"])
    st.divider()

    # ---------------------------------------------- SECTION 4: THE MAPPING
    _ch_header("04", "Engineering → AI, The Whole Map", AISIDE)
    st.markdown(
        "**Every AI concept in this course is a highway engineering activity you already understand.** "
        "Read down the left column and you have described a pavement management programme. Read down the "
        "right and you have described a machine learning pipeline. They are the same column.")
    st.plotly_chart(mapping_figure(style), use_container_width=True, key="mapping")

    st.success("**The one idea this course proves.** Machine Learning learns the relationships between "
               "pavement condition, traffic and environmental factors to predict the remaining service "
               "life of roads — helping engineers plan maintenance at the right time.")
    st.caption("Three published relationships run underneath all of it: the AASHTO 1993 design equation, "
               "the AASHO Road Test fourth-power law, and Miner's cumulative damage rule.")
