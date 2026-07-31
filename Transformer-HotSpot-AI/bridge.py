"""
bridge.py - the Electrical-Engineering -> AI teaching scaffold.
===============================================================
This module teaches no new concept and renders no model. Every technical
illustration lives in app.py / story.py. This wraps each stage renderer in a
five-part structure so a Power Systems student always sees, on every page:

    Electrical Engineering   the substation context      (bridge.open_page)
    The Challenge            why the manual way runs out (bridge.open_page)
    AI Connection            + the bridge figure         (bridge.open_page)
    Technical Idea           <- the stage renderer in app.py, untouched
    Key Takeaway             one sentence                (bridge.close_page)
    In the Notebook          where it lives              (bridge.close_page)

Text is short and professional. Short sentences, active voice, no drama. The
visuals carry the page; the text supports them.

COLOUR IS A TEACHING DEVICE AND MUST NEVER VARY.
    amber  = the substation / electrical engineering world
    cyan   = the AI world
    violet = the technical process
    red    = above a limit;  green = within limits
"""
import streamlit as st
import plotly.graph_objects as go

# ---------------------------------------------------------------- palette
BG, PANEL = "#0e1117", "#161b22"
EE = "#ffb74d"        # amber  - the substation
AISIDE = "#4fc3f7"    # cyan   - the AI
TECH = "#ba68c8"      # violet - the technical process
GREEN, RED = "#66bb6a", "#ef5350"
AMBERHOT = "#ff7043"  # the hot-spot accent
MUTED, TEXT = "#8b949e", "#e6edf3"
STEEL, INK, EDGE = "#141b24", "#0b0e13", "#2b3440"
MONOF = "ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', monospace"

# Protection-panel display language: busbar rules, relay-style cards, a thermal
# rail for the phase indicator. Deliberately distinct from the sibling apps.
_CSS = """
<style>
.stApp { background-image:
  radial-gradient(circle at 12% 0%, rgba(255,183,77,.05), transparent 42%),
  radial-gradient(circle at 88% 4%, rgba(79,195,247,.05), transparent 42%); }
hr { border-color:#2b3440 !important; }
.stButton>button { border-radius:2px; border:1px solid #3a4655; background:#141b24;
  text-transform:uppercase; letter-spacing:.07em; font-size:12px; font-weight:600; }
.stButton>button:hover { border-color:#ffb74d; color:#ffb74d; }
[data-testid="stMetric"] { background:#141b24; border:1px solid #2b3440;
  border-left:3px solid #ffb74d; border-radius:2px; padding:10px 12px; }
[data-testid="stMetricValue"] { font-family:__MONO__; }
[data-testid="stCaptionContainer"] p { font-family:__MONO__; letter-spacing:.02em; }

/* ---- busbar section header ---- */
.bus { display:flex; align-items:center; gap:11px; margin:24px 0 12px; }
.bus-tag { font-family:__MONO__; font-size:11px; font-weight:700; letter-spacing:.1em;
  border:1px solid; padding:2px 8px; border-radius:2px; white-space:nowrap; }
.bus-lab { font-family:__MONO__; text-transform:uppercase; letter-spacing:.16em;
  font-size:13px; font-weight:700; white-space:nowrap; }
.bus-bar { flex:1; height:5px; border-top:1px solid #2b3440; border-bottom:1px solid #2b3440; }

/* ---- relay card ---- */
.relay { position:relative; background:#141b24; border:1px solid #2b3440;
  border-left:3px solid #ffb74d; padding:14px 18px; color:#e6edf3;
  font-size:16px; line-height:1.65; margin:2px 0; }
.relay.ai { border-left-color:#4fc3f7; }
.relay.tech { border-left-color:#ba68c8; }
.relay.warn { border-left-color:#ef5350; }
.relay.ok { border-left-color:#66bb6a; }

/* ---- telemetry bar ---- */
.tele { font-family:__MONO__; background:#0b0e13; border:1px solid #2b3440;
  border-left:3px solid #ffb74d; padding:8px 14px; font-size:12px;
  letter-spacing:.06em; color:#8b949e; border-radius:2px; }
.pos { font-family:__MONO__; text-align:center; border:1px solid #ffb74d; border-radius:2px;
  background:#0b0e13; padding:6px 4px; font-size:11px; color:#8b949e; line-height:1.5; }
.pos b { color:#ffb74d; font-size:13px; }

/* ---- thermal rail (phase progress) ---- */
.rail { display:flex; flex-wrap:wrap; align-items:center; gap:4px; background:#0b0e13;
  border:1px solid #2b3440; border-radius:2px; padding:9px 12px; }
.rail-lab { font-family:__MONO__; font-size:11px; letter-spacing:.12em; color:#8b949e; margin-right:5px; }
.seg { font-family:__MONO__; font-size:11px; padding:2px 7px; border:1px solid #2b3440;
  color:#3f4650; border-radius:2px; }
.seg.done { color:#ffb74d; border-color:#5a4a2a; }
.seg.cur { background:#ffb74d; color:#0b0e13; border-color:#ffb74d; font-weight:700; }

/* ---- landing page ---- */
.brief { position:relative; border:1px solid #2b3440; background:#0b0e13; padding:20px 24px; }
.brief::before,.brief::after { content:''; position:absolute; width:16px; height:16px; border-color:#ffb74d; }
.brief::before { top:-1px; left:-1px; border-top:2px solid; border-left:2px solid; }
.brief::after { bottom:-1px; right:-1px; border-bottom:2px solid; border-right:2px solid; }
.brief-bar { font-family:__MONO__; font-size:12px; letter-spacing:.16em; color:#ffb74d; margin-bottom:8px; }
.ico { display:inline-flex; align-items:center; justify-content:center; width:40px; height:40px;
  border:1px solid #2b3440; border-radius:2px; font-size:22px; margin-bottom:8px; background:#0b0e13; }
.muted { color:#8b949e; font-size:13px; }
.sub { font-family:__MONO__; color:#8b949e; font-size:13px; }
.limit { font-family:__MONO__; font-size:12px; padding:3px 9px; border-radius:2px;
  border:1px solid; display:inline-block; margin-right:6px; }
</style>
""".replace("__MONO__", MONOF)


def inject_css():
    """Load the protection-panel display language once. Call after set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def _bus(tag, label, color):
    st.markdown(
        f"<div class='bus'>"
        f"<span class='bus-tag' style='color:{color};border-color:{color}'>{tag}</span>"
        f"<span class='bus-lab' style='color:{color}'>{label}</span>"
        f"<span class='bus-bar'></span></div>", unsafe_allow_html=True)


# ============================================================================
# THE ENGINEERING WORKFLOW
# One substation, one year, in the order a real condition-monitoring project
# runs it. Every AI concept hangs off one of these.
# ============================================================================
PHASES = [
    ("The Transformer In Service",   "Why a transformer heats, and why the hot spot decides its life."),
    ("One Hour Of Operation",        "The thermal model, and the temperature nobody measures."),
    ("The Monitoring Log",           "The historian export lands and gets checked."),
    ("Preparing The Data",           "Bad readings out, physics in, the year split honestly."),
    ("The First Prediction",         "The standard's own model, then a straight line."),
    ("Models That Bend",             "Three ensembles on the same columns."),
    ("Reading The Model",            "Which sensors earn their place, and how the prediction moves."),
    ("The Monitoring Dashboard",     "Predicted against measured, where it matters."),
    ("What The Model Does Not Know", "The limit, measured rather than asserted."),
    ("Decision Support",             "One temperature, one recommendation, one fleet view."),
]


# ============================================================================
# THE STEPS  (one per page; len(STEPS) is the count - never hardcode it)
#   ee / ai      - the two names of the same idea (amber name, cyan name)
#   tech         - what is actually computed (violet)
#   site         - Electrical Engineering. NO AI in this text.
#   challenge    - The Challenge. Why the manual way runs out of road.
#   ai_link      - AI Connection. Why this AI concept is therefore required.
#   takeaway     - Key Takeaway. ONE sentence.
#   notebook     - In the Notebook. Which step of the Colab notebook.
#   contributes  - What this step contributes to the finished system.
# ============================================================================
STEPS = [

# ------------------------------------ PHASE 1 - THE TRANSFORMER IN SERVICE
dict(
    id="the-asset", phase=0, ee_icon="⚡", ai_icon="🤖",
    ee="A Transformer Under Load", ai="Why Thermal Monitoring Needs AI",
    tech="Four units, 35,040 hourly readings, one year",
    ee_bullets=["40 MVA, 132/33 kV", "No installed spare", "Runs continuously"],
    ai_bullets=["35,040 examples", "Sensors already fitted", "One unmeasured target"],
    site="""Ashgrove substation: four 40 MVA 132/33 kV transformers aged 3, 9, 16 and 22 years. Each carries
between 240 A and 980 A on the 33 kV side. None has an installed spare. Replacement lead time runs to
months and replacement cost to millions.""",
    challenge="""A transformer is not damaged by heat. It is damaged by time spent hot. Insulation degrades
chemically, cumulatively, and invisibly until the unit fails. The engineer needs the internal temperature
now, on every unit, every hour. Four units over a year is 35,040 assessments.""",
    ai_link="""Not judgement, and not autonomy. Something duller: a way to turn measurements the substation
already produces into the one temperature it does not measure, continuously, without anybody watching. The
engineer still decides what to do about it.""",
    notebook="""Step 1. The fleet, and the nameplate constants everything else runs on.""",
    contributes="""The requirement the system is measured against: a temperature for every unit, every hour.""",
    takeaway="""A transformer's life is set by the temperature inside it, and nobody tracks that by hand across four units for 8,760 hours.""",
),
dict(
    id="why-heat", phase=0, ee_icon="🔥", ai_icon="📈",
    ee="Where The Heat Comes From", ai="A Non-Linear Relationship",
    tech="Load loss ∝ K², no-load loss ∝ V²",
    ee_bullets=["Copper loss, I²R", "Core loss, near constant", "6:1 at rated"],
    ai_bullets=["A power law", "Steps at each fan stage", "No straight line fits"],
    site="""A transformer converts voltage, not power. What it fails to pass on becomes heat. Load loss is
current through winding resistance and rises with the square of load. No-load loss is core hysteresis and
eddy currents, set by voltage rather than load.""",
    challenge="""The square is the problem. Take a unit from 50 % to 100 % load and load loss rises four times,
not two. Total heat rises 2.8 times. Every intuition built on straight lines is wrong here, and the error is
largest exactly where it matters — at high load.""",
    ai_link="""This is the first reason a straight-line model will not do. The load-to-heat relationship is a power
law, cooling stages put steps in it, and ambient shifts the whole curve. The physics is known; the
combination on a unit that has drifted from its nameplate has no clean closed form.""",
    notebook="""Step 2. The loss curve in per-unit, and the 2.8× figure.""",
    contributes="""The reason the project needs a model that can bend rather than a coefficient.""",
    takeaway="""Heat rises with the square of load, so the last 20 % of loading costs far more than the first 20 %.""",
),
dict(
    id="hot-spot", phase=0, ee_icon="🌡️", ai_icon="🎯",
    ee="Why The Hot Spot, Not The Oil", ai="Choosing The Target Variable",
    tech="F_AA = exp(15000/383 − 15000/(θ_h + 273))",
    ee_bullets=["25–30 K above the oil", "Doubles every 6 °C", "Rarely measured"],
    ai_bullets=["This is y", "Oil is a feature", "Why 2 °C matters"],
    site="""Three temperatures matter and they are not the same number. Ambient, around 30 °C. Top oil, around
62 °C at full load and measured on every unit. The winding hot spot, around 89 °C — the hottest point of the
coil, 25 to 30 K above the oil, and measured almost nowhere.""",
    challenge="""Insulation ageing is governed by the hot spot, exponentially. IEEE C57.91 puts the ageing rate at
1.0 at 110 °C, 0.28 at 98 °C and 17 at 140 °C. One hour at 140 °C costs the same insulation life as
seventeen hours at 110 °C. Watching the oil and assuming the winding follows is how transformers get
quietly destroyed.""",
    ai_link="""Choosing what to predict is an engineering decision. Predicting top oil would be easy and useless —
it is already measured. Predicting the hot spot is useful precisely because it is not. So the hot spot is
the target; everything else in the log is an input.""",
    notebook="""Step 3. The ageing curve, and what a 2 °C error costs.""",
    contributes="""The target variable, and the reason accuracy is worth paying for.""",
    takeaway="""The hot spot decides transformer life, and it is the one temperature most transformers never measure.""",
),
dict(
    id="enter-ai", phase=0, ee_icon="🧠", ai_icon="🤝",
    ee="Why This Needs Machine Learning", ai="Supervised Regression",
    tech="Learn f(sensors) → θ_h from recorded examples",
    ee_bullets=["The standard assumes nameplate", "Radiators foul", "Every unit drifts"],
    ai_bullets=["Cheap inputs", "Expensive label", "Learn this fleet"],
    site="""There is already a standard way to estimate the hot spot. IEEE C57.91 gives it in closed form, from
load and the measured oil temperature. It is a good model, and it is what the industry uses. It is also a
nameplate model.""",
    challenge="""Every unit drifts away from its nameplate, and drifts differently. Radiators foul, oil degrades,
cooling capacity falls a few percent per decade. Winding design differs, so the real hot-spot factor differs
unit to unit. Nobody re-derives a thermal model per unit per year, so the error is simply accepted.""",
    ai_link="""This is what supervised regression is for. Inputs: the readings the substation already logs. Output:
the hot-spot temperature. Training data: a year of both. The model learns this fleet's actual behaviour, and
the standard's model becomes the baseline to beat rather than the answer.""",
    notebook="""Step 4. The claim, stated before anything is fitted.""",
    contributes="""Fixes the role of AI: it extends the thermal standard, it does not replace the engineer.""",
    takeaway="""Machine learning is not replacing the thermal standard — it learns the part of each transformer the standard was never given.""",
),

# ---------------------------------------- PHASE 2 - ONE HOUR OF OPERATION
dict(
    id="thermal-model", phase=1, ee_icon="📐", ai_icon="⚙️",
    ee="The Thermal Model", ai="Domain Knowledge As Code",
    tech="θ_h = θ_oil + Δθ_h,r · K^1.6",
    ee_bullets=["Top-oil rise", "Winding gradient", "Three-hour time constant"],
    ai_bullets=["The baseline", "The features", "The sanity check"],
    site="""IEEE C57.91 builds the hot spot in two steps. Top-oil rise over ambient follows the total loss
term ((K²R + 1)/(R + 1))^n. Hot-spot rise over top oil follows K^(2m), which with m = 0.8 is K^1.6. Add
them to ambient and you have the winding temperature.""",
    challenge="""The equations are simple; the conditions are not. The oil has a three-hour time constant, so it
never reaches the steady state the formula describes. Cooling fans switch in stages and change the exponents
mid-operation. Cold oil is more viscous, so the gradient is larger on a cold day at the same load.""",
    ai_link="""Write the physics down anyway. It becomes the baseline the model must beat, the source of the
engineered features, and the sanity check for the model's response. Domain knowledge does not compete with
machine learning here — it feeds it.""",
    notebook="""Step 5. The two functions, and one worked hour on T3.""",
    contributes="""The equations used to generate the log, build the features, and check the result.""",
    takeaway="""Write the physics down even when you plan to use machine learning — it becomes both the baseline and the features.""",
),
dict(
    id="the-target", phase=1, ee_icon="🔎", ai_icon="📋",
    ee="The Temperature Nobody Measures", ai="Labels, And Where They Come From",
    tech="Fibre-optic probe on the reference units",
    ee_bullets=["Fitted at manufacture", "Cannot be retrofitted", "Most units lack one"],
    ai_bullets=["Seven cheap inputs", "One expensive label", "That gap is the case"],
    site="""Direct hot-spot measurement needs a fibre-optic probe installed between the winding discs at
manufacture. It cannot be retrofitted without untanking the transformer. Most units in service do not have
one. Ashgrove's four do — they were specified as a condition-monitoring pilot.""",
    challenge="""So this fleet has a year of true hot-spot readings and the rest of the network has none. That is
both the opportunity and the limit: four instrumented units can teach a model that then runs on units
without probes, but only if those units behave like the four it learned from.""",
    ai_link="""In supervised learning the probe readings are the labels. Labels are almost always the expensive part
of a dataset. The inputs here are cheap — current, voltage, ambient, humidity, oil temperature, fan status.
A model is worth building exactly when the inputs are cheap and the answer is expensive.""",
    notebook="""Step 6. The column catalogue, with the cost of each.""",
    contributes="""The economic argument for the whole scheme, in one table.""",
    takeaway="""Build a model when the inputs are cheap and the answer is expensive — which is exactly the case here.""",
),

# ------------------------------------------ PHASE 3 - THE MONITORING LOG
dict(
    id="log", phase=2, ee_icon="💾", ai_icon="🗃️",
    ee="The Historian Export", ai="The Raw Dataset",
    tech="35,040 rows × 11 columns, hourly, one year",
    ee_bullets=["SCADA historian", "One row per unit-hour", "Nothing corrected"],
    ai_bullets=["The raw dataset", "One training example", "Faults included"],
    site="""The substation SCADA historian holds every reading it has taken. The condition-monitoring request
produces one CSV: four units, hourly, calendar year 2025. Exactly what the field instruments reported.""",
    challenge="""A historian export is a record of the instrumentation, not of the transformer. Communications drop
and values go missing. A sensor freezes and repeats yesterday's number. A unit is switched out and reads
near-zero current while the winding cools to ambient. A humidity transmitter fails and reports a raw byte.""",
    ai_link="""The dataset is the input to everything downstream, so the discipline goes here. Load it, then look at
it. Establish what should be there before deciding what is wrong. Do not clean anything yet.""",
    notebook="""Step 7. The simulator writes the CSV; the notebook then reads it back.""",
    contributes="""The evidence every later step works from.""",
    takeaway="""The raw export is evidence — look at it before you clean it, or you clean away what you needed to see.""",
),
dict(
    id="inspect", phase=2, ee_icon="🔍", ai_icon="🧪",
    ee="Checking The Export", ai="Data Inspection",
    tech="dtypes, ranges, missing counts, duplicates",
    ee_bullets=["Are the units right?", "Are the ranges possible?", "What is repeated?"],
    ai_bullets=["describe()", "isna().sum()", "A check written on purpose"],
    site="""Before any engineering conclusion, an engineer checks the instrument. The same questions apply to an
export. Are the units what they claim to be? Are the ranges physically possible for this plant? How much is
missing, and is anything repeated?""",
    challenge="""Impossible values do not announce themselves. A humidity of 255 % is obvious in a summary. A load
current of 3 A on a 700 A transformer looks like rounding until you realise the unit was de-energised. A
frozen ambient sensor produces plausible numbers in an implausible sequence — and no summary shows that.""",
    ai_link="""Every fault left in the file becomes a training example. A model trained on de-energised hours learns
that low current means winding-at-ambient, then under-predicts every genuinely light-load hour. Inspection
is the difference between a model that works and one that does not.""",
    notebook="""Step 8. Four faults found before a model is fitted.""",
    contributes="""The fault list the cleaning step works from.""",
    takeaway="""Some faults show up in a summary and some only in a sequence — write the check for both.""",
),
dict(
    id="explore", phase=2, ee_icon="📊", ai_icon="🔗",
    ee="Reading The Fleet", ai="Exploratory Analysis",
    tech="Trends, scatter, correlation",
    ee_bullets=["The daily shape", "Load against temperature", "Unit against unit"],
    ai_bullets=["Time series", "Scatter", "Correlation matrix"],
    site="""Three things an engineer wants to see immediately: when the network peaks and when the transformers
get hot, how steep the load-to-temperature relationship is, and whether one unit runs hotter than the
others.""",
    challenge="""The scatter of load against hot spot is not a line and not even a single curve. Hold the load between
680 and 720 A and the hot spot still spans 36 °C. The spread comes from ambient, cooling stage, and which
unit it is. No single variable explains it.""",
    ai_link="""Exploratory analysis decides what the model is allowed to be. If load alone explained the hot spot, a
lookup table would do. Because the relationship fans out, the model needs several inputs at once — and the
correlation matrix says which are worth having.""",
    notebook="""Step 9. A week of trend, the scatter, and the fleet table.""",
    contributes="""The evidence that this is a multi-input problem, not a lookup.""",
    takeaway="""At one fixed load the hot spot still spans tens of degrees, which is why one sensor is never enough.""",
),

# ------------------------------------------ PHASE 4 - PREPARING THE DATA
dict(
    id="clean", phase=3, ee_icon="🧹", ai_icon="✅",
    ee="Removing Invalid Readings", ai="Data Cleaning",
    tech="Filter, deduplicate, drop unusable rows",
    ee_bullets=["Interpolate slow signals", "Delete non-measurements", "Log every decision"],
    ai_bullets=["Imputation", "Row removal", "An audit trail"],
    site="""Each fault found in the last step gets a decision, and each decision is an engineering one. Duplicates
go. The constant column goes. Impossible humidity becomes missing, then filled. Missing oil temperature is
interpolated. Rows with no hot-spot label are dropped.""",
    challenge="""Two decisions matter and both are counter-intuitive. Interpolating oil temperature is safe, because
it has a three-hour time constant — interpolating load current would not be, since it can double in an
hour. And de-energised hours must be deleted, not repaired: a cooling transformer obeys different physics
from a loaded one.""",
    ai_link="""Every row left in the file is a statement to the model that this is what normal looks like. A hundred
de-energised hours is a hundred wrong statements, and the model has no way to know. It will fit them.""",
    notebook="""Step 10. The cleaning log, with a count against every action.""",
    contributes="""A dataset in which every remaining row is a measurement of the thing being modelled.""",
    takeaway="""Interpolate what moves slowly, delete what is not a measurement of the thing you are modelling.""",
),
dict(
    id="features", phase=3, ee_icon="🔧", ai_icon="💡",
    ee="Turning Readings Into Engineering Quantities", ai="Feature Engineering",
    tech="load_pu, K^1.6, oil rise, ramps, 3 h rolling load",
    ee_bullets=["Per-unit, not amps", "Rise, not temperature", "Recent history"],
    ai_bullets=["The physics as a column", "Undo the sensor lag", "Worth more than the algorithm"],
    site="""A raw reading is rarely the quantity an engineer reasons with. Nobody thinks in amps; they think in
per-unit load. Nobody compares oil temperatures across seasons; they compare oil rise over ambient. Nobody
looks at one instant; they look at the last few hours.""",
    challenge="""Two new columns exist because of physics the raw sensors cannot express. K^1.6 is the winding law
from IEEE C57.91 — give it to the model and it need not discover the exponent. The 3-hour mean load fills
the gap left by the oil thermometer, which lags the actual top oil by an hour or more.""",
    ai_link="""Feature engineering is where domain knowledge enters a model. The algorithm can only combine the
columns it is given. Give it K^1.6 and a straight line can represent a power law. This is usually worth more
than changing the algorithm — and here it is worth almost as much.""",
    notebook="""Step 11. Five raw columns become thirteen.""",
    contributes="""0.41 °C of the total improvement, from domain knowledge alone.""",
    takeaway="""Feature engineering is where the thermal standard enters the model, and it is usually worth more than a fancier algorithm.""",
),
dict(
    id="scale", phase=3, ee_icon="📏", ai_icon="🎚️",
    ee="Putting Quantities On A Common Scale", ai="Normalisation",
    tech="StandardScaler: z = (x − μ) / σ",
    ee_bullets=["Amps in hundreds", "Per-unit in fractions", "Same physics"],
    ai_bullets=["Linear models care", "Trees do not", "Fit on train only"],
    site="""The columns are in wildly different units. Current runs to 980, voltage to 140, per-unit load to 1.4.
Nothing in the physics says current is four hundred times more important than per-unit load — but to an
algorithm that measures distance, it is.""",
    challenge="""Only some algorithms care, and knowing which is the point. Linear and distance-based models are
affected by scale. Decision trees are not: a split at 640 A is the same split whether the column is in amps
or per unit. Applying scaling everywhere is harmless; not knowing why is not.""",
    ai_link="""Fit the scaler on the training set only, then apply it to the test set. Fitting it on everything leaks
the test set's mean and standard deviation into training. That is the rule people break.""",
    notebook="""Step 12. Four columns, before and after standardisation.""",
    contributes="""Comparable inputs, so the linear model's coefficients mean something.""",
    takeaway="""Scale what needs scaling, fit the scaler on training data only, and know that trees do not care either way.""",
),
dict(
    id="split", phase=3, ee_icon="✂️", ai_icon="📐",
    ee="Holding Back A Fair Test", ai="Train / Test Split",
    tech="Whole weeks held out, and why R² moves",
    ee_bullets=["A commissioning test", "On a case never tuned on", "Chosen deliberately"],
    ai_bullets=["Blocked, not random", "Both seasons in both sets", "R² depends on the set"],
    site="""The model has to be scored on readings it has never seen, and how you choose those readings is an
engineering decision. Random rows are simple. Whole weeks keep the seasons in both sets. The last three
months is the strictest test of all.""",
    challenge="""The third option exposes something that looks like a failure and is not. Hold out October to December
and R² drops sharply while the mean absolute error barely moves. The model did not get worse — the test set
got narrower, and R² is measured against the test set's own variation.""",
    ai_link="""The choice here is whole weeks, every fourth one. It stops adjacent hours sitting on both sides of the
split, keeps summer and winter in both sets so the hot band is testable, and gives a 75/25 split without
cherry-picking.""",
    notebook="""Step 13. 26,164 training rows, 8,708 test rows.""",
    contributes="""The held-out quarter every score in this course is measured on.""",
    takeaway="""Split by whole weeks so adjacent hours cannot leak, and remember R² depends on how wide the test set is.""",
),

# ---------------------------------------- PHASE 5 - THE FIRST PREDICTION
dict(
    id="baseline", phase=4, ee_icon="📜", ai_icon="📏",
    ee="The Standard's Own Model", ai="The Baseline",
    tech="θ_h = θ_oil + 24 · K^1.6 · stage factor",
    ee_bullets=["IEEE C57.91", "Nameplate values", "Nothing fitted"],
    ai_bullets=["The number to beat", "A per-unit bias", "Not a straw man"],
    site="""Before fitting anything, run the model the industry already uses. IEEE C57.91 with nameplate values
and the measured oil temperature: hot spot equals oil plus 24 K times K^1.6 times a cooling-stage factor. No
training data required.""",
    challenge="""It is genuinely good, and it has no way to know that one unit's real hot-spot factor is 21 % above
nameplate and another's is 7 % below, that twenty-two years of fouling has cost some cooling, or that the
oil thermometer reads an hour behind. Those are not errors in the standard — they are things it was never
given.""",
    ai_link="""This is the number every later model must beat. An R² of 0.99 means nothing alone. An R² of 0.99
against a baseline that already achieves 0.95 is an engineering result. A model that cannot beat the
closed-form standard is not worth deploying.""",
    notebook="""Step 14. MAE 3.18 °C, R² 0.946, and the per-unit bias.""",
    contributes="""The baseline. Every later claim is measured against this, not against zero.""",
    takeaway="""Beat the standard, not zero — a model that cannot outperform the closed-form thermal model is not worth deploying.""",
),
dict(
    id="linear", phase=4, ee_icon="📉", ai_icon="📐",
    ee="A Straight Line Through The Data", ai="Linear Regression",
    tech="One weight per sensor, added up",
    ee_bullets=["A sensitivity per sensor", "Every coefficient arguable", "Fitted to this fleet"],
    ai_bullets=["The right first model", "Cannot overfit here", "Sets the bar"],
    site="""The simplest fitted model: give each sensor a weight and add them up. The engineering reading is a
sensitivity coefficient per sensor — how many degrees the hot spot moves per amp of load, per degree of
ambient, per degree of oil. Every coefficient can be argued with.""",
    challenge="""It inherits every limitation of a straight line. Heat rises with K² and the gradient with K^1.6, and
a line cannot bend. Cooling stages put steps in the curve, and a line cannot step. Cold oil is more viscous,
so ambient and load interact, and a line cannot multiply two inputs together.""",
    ai_link="""Linear regression is the right first model, always. It is fast, it cannot overfit thirteen columns of
thirty-five thousand rows, and its coefficients are readable. Anything more complicated now has to justify
itself against it.""",
    notebook="""Step 15. 2.41 °C on raw sensors, 2.01 °C with the engineered columns.""",
    contributes="""Proof that fitting to this fleet at all is worth 0.77 °C.""",
    takeaway="""A straight line already beats the nameplate model, because it has at least seen this fleet run.""",
),
dict(
    id="residuals", phase=4, ee_icon="🔎", ai_icon="📉",
    ee="Where The Line Fails", ai="Residual Analysis",
    tech="error = predicted − measured, against the inputs",
    ee_bullets=["A systematic error", "Not scatter", "Physics it cannot express"],
    ai_bullets=["Curvature → bend", "Steps → split", "Which model comes next"],
    site="""A residual is a prediction error. Plotting residuals against each input is the standard way to find
what a model has missed. The rule is simple: residuals should look like noise. If they show a pattern, the
pattern is signal the model failed to use.""",
    challenge="""These residuals are not noise. Plotted against load they swing from −1.3 °C at light load to +0.4 °C
in the middle and −2.2 °C at overload — the K^1.6 curve the line could not follow. Grouped by cooling stage
they sit at different levels, which is an interaction.""",
    ai_link="""Residual analysis tells you which kind of model you need next. Curvature means the relationship bends,
so use a model that can bend. Level shifts by category mean interactions, so use a model that can split.
Tree ensembles do both natively — which is why the next phase uses them.""",
    notebook="""Step 16. Two diagnostic plots, both showing structure.""",
    contributes="""The reason for choosing ensembles, measured rather than assumed.""",
    takeaway="""Structure in the residuals tells you what model to reach for next — curvature means bend, steps mean split.""",
),

# -------------------------------------------- PHASE 6 - MODELS THAT BEND
dict(
    id="forest", phase=5, ee_icon="🌳", ai_icon="🌳",
    ee="Many Small Rules Instead Of One Equation", ai="Random Forest Regressor",
    tech="200 trees, each on a different sample and subset",
    ee_bullets=["Rules, not equations", "Ask several engineers", "Average the answers"],
    ai_bullets=["A split is a threshold", "Bagging", "No scaling needed"],
    site="""An experienced engineer does not carry one equation, they carry rules. Above 0.9 per unit with fans at
stage 1, add about ten degrees. On a cold morning the gradient runs higher than the tables say. T4 always
sits a couple of degrees above its sisters. A decision tree is exactly that, written down.""",
    challenge="""One tree memorises. Ask it about an hour it has seen and it is perfect; ask about a new one and it is
brittle. A random forest fixes that by disagreement: many trees, each on a different random sample of rows
and a random subset of columns, and the answers averaged.""",
    ai_link="""Trees solve both problems the residuals exposed. A tree approximates a curve with steps, so K^1.6 stops
being a problem. A tree splits on cooling stage and then splits differently on load underneath it — that is
an interaction, for free.""",
    notebook="""Step 17. MAE 1.53 °C, a 24 % improvement on the best linear model.""",
    contributes="""The first model that handles curvature and interaction without being told they exist.""",
    takeaway="""A forest of disagreeing trees handles curvature and interactions natively — exactly what the residuals asked for.""",
),
dict(
    id="boosting", phase=5, ee_icon="📈", ai_icon="🔁",
    ee="Correcting The Previous Attempt", ai="Gradient Boosting Regressor",
    tech="300 shallow trees, each fitted to what is left over",
    ee_bullets=["Take the last result", "Measure what is left", "Correct it"],
    ai_bullets=["Fit the residual", "Small learning rate", "Sequential, not parallel"],
    site="""A commissioning engineer does not start from scratch after each test — they take the previous result and
correct it. Boosting is that loop: make a rough prediction, measure the residual, fit a small tree to it,
add a fraction of that tree, and repeat.""",
    challenge="""The direction of the work is what differs from a forest. A forest builds independent trees and
averages them, so errors cancel. Boosting builds dependent trees, each aimed at the last mistake, so errors
are attacked. It reaches a lower error on tabular data and takes far longer, because the trees cannot be
built in parallel.""",
    ai_link="""Two settings control it and both are trade-offs. The learning rate is how much of each correction to
accept — small means slow and stable. The number of trees is how long to keep correcting. Halve the learning
rate and you need roughly twice the trees.""",
    notebook="""Step 18. MAE 1.35 °C, and the error curve against tree count.""",
    contributes="""The best accuracy in the course, and the slowest cell in the notebook.""",
    takeaway="""Boosting attacks its own errors one tree at a time and beats the forest on tabular data, at the cost of a fit that cannot be parallelised.""",
),
dict(
    id="xgboost", phase=5, ee_icon="⚡", ai_icon="🚀",
    ee="The Same Answer, Fast Enough To Retrain", ai="XGBoost Regressor",
    tech="600 trees, histogram splits, parallel and regularised",
    ee_bullets=["New units arrive", "Probes get fitted", "Refit when data changes"],
    ai_bullets=["Binned splits", "Uses every core", "Built-in regularisation"],
    site="""A condition-monitoring model is not fitted once. It is refitted as the fleet changes — new units, new
probes, a year of fresh readings. If refitting takes an hour it happens annually. If it takes a second it
happens whenever the data changes.""",
    challenge="""XGBoost is gradient boosting with the implementation problems solved. Continuous columns are bucketed
once, so each split is a lookup instead of a sort. It uses every core. It penalises tree complexity
explicitly, so more trees is safer.""",
    ai_link="""The comparison is not about accuracy. The two land within 0.01 °C of each other and differ by an order
of magnitude in fit time. When two models are equally accurate, choose on the properties that are not
accuracy: fit time, memory, deployability, and whether anyone can retrain it without booking an afternoon.""",
    notebook="""Step 19. Same MAE, a fraction of the time.""",
    contributes="""The model carried into the dashboard.""",
    takeaway="""When two models are equally accurate, pick on fit time and deployability — those are engineering criteria too.""",
),
dict(
    id="leaderboard", phase=5, ee_icon="🏁", ai_icon="📊",
    ee="Which Model Goes Into Service", ai="Model Comparison",
    tech="Six models, one held-out quarter of the year",
    ee_bullets=["The same test for each", "Against the standard", "Not against zero"],
    ai_bullets=["Three separate levers", "None dominates", "R² does not discriminate"],
    site="""Every model so far, on the same held-out weeks, scored the same way. The table answers two separate
questions that should not be confused: does machine learning beat the standard's thermal model, and does the
algorithm matter as much as the features?""",
    challenge="""The second answer is the surprising one. Nameplate to fitted straight line is 0.77 °C. Raw sensors to
engineered columns, same algorithm, is 0.41 °C. Linear to gradient boosting, same columns, is 0.66 °C. All
three levers are real and comparable in size — and a great deal more published effort goes into the third
than the second.""",
    ai_link="""Read it as an engineer, not a scoreboard. The total improvement is 3.18 °C to 1.35 °C, a 58 % cut
against the model the industry currently uses. At 110 °C that is the difference between understating the
ageing rate by 27 % and by 13 %. Every R² in the table is above 0.94, which is why R² cannot choose for you.""",
    notebook="""Step 20. The leaderboard, and the three levers measured separately.""",
    contributes="""The headline result of the whole project.""",
    takeaway="""Machine learning cut the hot-spot error by 58 % against the industry-standard thermal model, and feature engineering delivered nearly as much of that as the algorithm.""",
),

# ------------------------------------------ PHASE 7 - READING THE MODEL
dict(
    id="importance", phase=6, ee_icon="📋", ai_icon="🔎",
    ee="Which Sensors Are Earning Their Place", ai="Feature Importance",
    tech="Rankings, then drop the instrument and refit",
    ee_bullets=["Every sensor costs", "Cable, telemetry, calibration", "For the whole life"],
    ai_bullets=["Rankings disagree", "Columns are redundant", "Refitting decides"],
    site="""A monitoring scheme costs money per sensor: the instrument, the cabling, the telemetry channel and the
calibration for the rest of the transformer's life. So the question is not academic. Which of these
measurements is actually contributing?""",
    challenge="""Two of the five specified sensors contribute almost nothing. Humidity has a negligible effect on
oil-to-air heat transfer. Voltage moves only core loss, which is one seventh of total loss, and it varies by
±5 %. That is not a failure of the model — it is the model reporting a real result about the plant.""",
    ai_link="""There are two traps. Two models rank the same columns differently, so a ranking describes the model and
not the transformer. And removing one column proves nothing, because the columns are redundant by
construction. Remove everything derived from an instrument, refit, and measure — that has an answer in
degrees.""",
    notebook="""Step 21. Two rankings side by side, then the instrument-level test.""",
    contributes="""The sensor justification, in degrees, for whoever pays for the instrumentation.""",
    takeaway="""Importance rankings disagree between models and hide redundancy — to test an instrument, remove everything derived from it and refit.""",
),
dict(
    id="sensitivity", phase=6, ee_icon="🎛️", ai_icon="📈",
    ee="How The Prediction Responds", ai="Sensitivity Analysis",
    tech="Vary one input, hold the rest, plot the response",
    ee_bullets=["Push it, do not read it", "Check against the physics", "A loading chart"],
    ai_bullets=["One-at-a-time", "The response surface", "Sanity-check the model"],
    site="""An engineer trusts a model by pushing it, not by reading its score. Take a realistic operating point,
move one input at a time, and check the response is the shape the physics requires. More load must mean a
hotter winding, and the curve must steepen.""",
    challenge="""A model can score well on average and still be wrong where it matters. If it flattens above 1.2 per
unit it under-predicts every overload — the only hours anybody cares about. If it responds to ambient with a
slope of 0.3 instead of about 1.0 it fails in a heatwave. Average error reveals neither.""",
    ai_link="""This is also how the model gets explained to somebody who will not read a metric. A curve of predicted
hot spot against load, at three ambient temperatures, is a loading chart — and engineers have used loading
charts for a century. The model produced a familiar artefact.""",
    notebook="""Step 22. The loading chart, produced from data.""",
    contributes="""The evidence that the model agrees with the standard across the whole range.""",
    takeaway="""Push the model one input at a time and check it against the physics — a good score is not the same as a correct response.""",
),

# ------------------------------------ PHASE 8 - THE MONITORING DASHBOARD
dict(
    id="metrics", phase=7, ee_icon="📐", ai_icon="🧮",
    ee="Stating The Accuracy", ai="MAE, RMSE and R²",
    tech="Three numbers, and what each one hides",
    ee_bullets=["Survives a design review", "Quoted in degrees", "Matched to the decision"],
    ai_bullets=["MAE: typical error", "RMSE: worst errors", "R²: test-set dependent"],
    site="""An accuracy claim has to survive a design review. Three numbers are normally quoted and they answer
different questions. MAE is how wrong a typical prediction is, in degrees. RMSE is how wrong the worst ones
are. R² is what fraction of the variation is explained.""",
    challenge="""R² is the one that gets misread. Score on every fourth week and it is 0.991; score on October to
December and it is 0.978 — with the same 1.35 °C mean error both times. The test set's standard deviation
fell from 17.4 °C to 11.5 °C, and that is the entire explanation.""",
    ai_link="""Choose the metric that matches the decision. The decision here is how close the winding is to 110 °C,
which is a question in degrees — so MAE and RMSE are the operative metrics and R² is context. The metric is
part of the specification, not an afterthought.""",
    notebook="""Step 23. Both splits fitted and scored, side by side.""",
    contributes="""The accuracy figure that goes into the scheme specification.""",
    takeaway="""Quote the error in degrees; R² changes when the test set changes even though the model has not.""",
),
dict(
    id="errors", phase=7, ee_icon="📈", ai_icon="📊",
    ee="The Shape Of The Error", ai="Error Distribution",
    tech="Predicted against measured, and the residual histogram",
    ee_bullets=["A calibration check", "Evidence, not a claim", "Readable by anyone"],
    ai_bullets=["The 45° line", "Centred on zero", "Symmetric or not"],
    site="""A single accuracy figure hides the shape. Two plots are standard on any commissioning report. Predicted
against measured — points should sit on the 45° line. And the error histogram — it should be centred on zero
and symmetric.""",
    challenge="""For a thermal model the direction of the error is not symmetric in consequence. Predicting too high
costs money, because loading is restricted that need not have been. Predicting too low costs insulation
life, silently, and nobody finds out for years.""",
    ai_link="""These two plots are how a model gets accepted or rejected in a review. A score is a claim; a
predicted-against-measured plot is evidence. Anyone can read it, including people who will never read the
code. Plot it before quoting the metric.""",
    notebook="""Step 24. The scatter, the histogram, and the error percentiles.""",
    contributes="""The evidence behind the accuracy claim.""",
    takeaway="""A predicted-against-measured plot is evidence; a metric is only a claim about it.""",
),
dict(
    id="trend", phase=7, ee_icon="📉", ai_icon="⏱️",
    ee="Following A Real Week", ai="Time-Series Comparison",
    tech="Predicted and measured, hour by hour",
    ee_bullets=["Does it track the peak?", "Does it lag?", "The contingency hours"],
    ai_bullets=["No metrics needed", "Two lines", "The plot that earns trust"],
    site="""The scatter plot treats every hour as independent; operations does not. An engineer wants to see the
model follow the plant. Does it track the daily peak or lag it? When the load steps, does the prediction
step with it?""",
    challenge="""A real week contains the events that matter — a contingency transfer, the hottest afternoon of the
summer, the overnight recovery when the oil cools slowly and the winding cools fast. Any of these could be
where the model breaks, and none of them show up in an average.""",
    ai_link="""This is the plot shown to an operations manager. No metrics, no axes anybody has to be taught to read,
two lines that should sit on top of each other. If the model is going to be trusted, this is what does it.""",
    notebook="""Step 25. Six days across the hottest hours of the test set.""",
    contributes="""The trust argument — and the first sight of the peak being under-read.""",
    takeaway="""The model tracks the plant closely all week and then under-reads the annual peak by nearly 4 °C — the one hour you cannot afford to under-read.""",
),
dict(
    id="hot-tail", phase=7, ee_icon="🌡️", ai_icon="⚠️",
    ee="The Errors That Actually Matter", ai="Segmented Evaluation",
    tech="Error by temperature band, converted to ageing",
    ee_bullets=["95 % of hours are free", "482 hours above 110 °C", "That is where life goes"],
    ai_bullets=["Segment the error", "Weight by consequence", "Report the limitation"],
    site="""For 95 % of the year these transformers run between 40 °C and 90 °C hot spot, and nothing is at stake.
The hours that matter are the other 5 %: 1,753 hours above 98 °C, 482 above 110 °C, and 113 above 120 °C
across the fleet's year.""",
    challenge="""Segment the error by temperature and the model looks different. It rises from 1.3 °C in the normal
band to 2.1 °C above 110 °C, and the bias turns negative — the model under-predicts the hottest hours. There
are fewer training examples up there, so it regresses towards the middle. The 1.35 °C average hides this
completely.""",
    ai_link="""State the consequence in engineering units. The hottest 1 % of hours carry 38 % of the insulation
ageing and the hottest 5 % carry 71 %. So a model that is worse in the top 5 % is worse where nearly all the
damage happens. That is the honest way to report it, and it points at the fix.""",
    notebook="""Step 26. Error by band, and the ageing concentration curve.""",
    contributes="""The limitation that has to be declared with the accuracy figure.""",
    takeaway="""Report the error where the consequence is — 71 % of the ageing happens in 5 % of the hours, and that is where the model is weakest.""",
),

# --------------------------- PHASE 9 - WHAT THE MODEL DOES NOT KNOW
dict(
    id="unseen-unit", phase=8, ee_icon="🚫", ai_icon="📉",
    ee="A Transformer It Has Never Seen", ai="Generalisation, Measured",
    tech="Train on three units, test on the fourth",
    ee_bullets=["The scheme targets un-probed units", "Different winding designs", "Testable right now"],
    ai_bullets=["Out-of-distribution", "Bias, not variance", "A fixable offset"],
    site="""The whole point of the scheme is to run this model on transformers without a probe. So the real question
is not how well it predicts these four units. It is how well it predicts a fifth — a unit it has never seen,
of a different vintage and winding design.""",
    challenge="""It fails, and it fails in a diagnosable way. Held-out MAE rises from 1.35 °C to between 2.4 and
5.6 °C, and almost all of it is bias. Trained without one unit the model over-predicts it by 5.6 °C all
year; without another it under-predicts by 4.8 °C. Those units genuinely have different hot-spot factors.""",
    ai_link="""This is the most important limitation in the project and it must be measured, not assumed. The model
interpolates within the fleet it learned; it does not extrapolate to new designs. The deployable version is
therefore: fit probes to a representative sample of designs, and accept a calibration period on any type not
represented.""",
    notebook="""Step 27. Four hold-out runs, with bias and scatter separated.""",
    contributes="""The honest boundary of the scheme, in the same units as the accuracy claim.""",
    takeaway="""This model knows these four transformers, not transformers in general — and the failure is a fixable offset, not a broken model.""",
),

# --------------------------------------------- PHASE 10 - DECISION SUPPORT
dict(
    id="predict", phase=9, ee_icon="🎚️", ai_icon="🔮",
    ee="Asking The Model A Question", ai="Interactive Prediction",
    tech="Five readings in, one temperature out",
    ee_bullets=["What the control room sees", "Five gauges", "One answer"],
    ai_bullets=["Model inference", "With an interpretation", "Not just a number"],
    site="""This is the scheme from the control room. Five readings the substation already has — load current,
ambient temperature, top-oil temperature, voltage and humidity — and one answer: the hot-spot temperature,
and what it means.""",
    challenge="""The answer alone is not useful. 97 °C tells an operator nothing they can act on. They need how far
it is from 110 °C, what is driving it, how fast insulation is being consumed, and whether anything needs
doing. A number without an interpretation is not decision support.""",
    ai_link="""Two different questions get asked and they are not interchangeable. In sensor mode all five readings
come from the plant now, and this is what the scheme does continuously. In what-if mode the engineer sets a
load and the oil temperature is estimated — that is a forecast, and it inherits the thermal model's
assumptions.""",
    notebook="""Step 28. The `assess()` function and the slider demonstration.""",
    contributes="""The interactive core of the whole system.""",
    takeaway="""A predicted temperature is not decision support until it arrives with the headroom, the ageing rate, and the reason.""",
),
dict(
    id="recommend", phase=9, ee_icon="🚦", ai_icon="🧭",
    ee="Turning A Temperature Into An Action", ai="Decision Rules On Top Of A Model",
    tech="IEEE C57.91 table 8 limits, as thresholds",
    ee_bullets=["110 / 120 / 140 °C", "Published, not invented", "Name the cause"],
    ai_bullets=["Model gives the number", "Standard gives the limit", "Rules give the reason"],
    site="""The limits are not invented. IEEE C57.91 sets them: below 98 °C continue normal operation, 98 to 110 °C
monitor closely, 110 to 120 °C increase cooling and prepare to reduce load, above 120 °C reduce loading now.
The model supplies the temperature; the standard supplies the thresholds.""",
    challenge="""The recommendation has to name the cause or it will be ignored. Telling an operator to reduce load on
a transformer whose fans have failed is the wrong instruction — the cooling should be fixed. So the rules
check whether the oil rise is larger than the load justifies, and whether there is any cooling left to add.""",
    ai_link="""Note where the machine learning stops. The model predicts a temperature and nothing else. The
thresholds come from a published standard. The cause diagnosis is engineering logic, written by hand and
readable by anyone. Keeping the three separate is what makes the system auditable.""",
    notebook="""Step 29. The rule engine, in about forty lines.""",
    contributes="""The output an operator actually acts on.""",
    takeaway="""The model gives a temperature, the standard gives the threshold, and hand-written logic gives the reason — keeping them separate is what makes the system auditable.""",
),
dict(
    id="dashboard", phase=9, ee_icon="📺", ai_icon="🎯",
    ee="The Substation Monitoring Dashboard", ai="The Deployed System",
    tech="Four units, live prediction, ranked by risk",
    ee_bullets=["Which unit first?", "Headroom, not temperature", "Reason beside the action"],
    ai_bullets=["Ranked by risk", "Cumulative ageing", "One line to act on"],
    site="""Everything from the previous twenty-nine steps on one screen. For each transformer: the current
readings, the predicted hot spot against the 110 °C limit, the insulation life consumed this year, and the
recommended action with its reason.""",
    challenge="""The dashboard has to answer the operator's real question, which is not what the temperature is. It is
which transformer to look at first and what to do about it. That means ranking by risk rather than by name,
and showing headroom rather than raw temperature.""",
    ai_link="""Cheap sensors that were already fitted feed a model trained on four instrumented units, which feeds
thresholds from a published standard, which feeds one line of text an operator can act on. The machine
learning is one component of four — the one that supplies the number nobody can measure.""",
    notebook="""Step 30. The fleet panel, the gauges, and the ageing chart.""",
    contributes="""The finished system, and the end of the course.""",
    takeaway="""The output of the whole project is one ranked screen telling an operator which transformer to look at first, and why.""",
),
]

BY_ID = {s["id"]: s for s in STEPS}
ORDER = [s["id"] for s in STEPS]


def goto(stage):
    st.query_params["stage"] = stage
    st.rerun()


def phase_steps(pi):
    return [s for s in STEPS if s["phase"] == pi]


# ============================================================================
# THE BRIDGE FIGURE  -  the substation card, the busbar, the AI card
# ============================================================================
def _wrap(text, width=22):
    out, line = [], ""
    for w in text.split():
        if len(line) + len(w) + 1 > width:
            out.append(line); line = w
        else:
            line = f"{line} {w}".strip()
    out.append(line)
    return "<br>".join(out)


def _card(fig, x0, x1, color, icon, title, bullets, kicker):
    fig.add_shape(type="rect", x0=x0, x1=x1, y0=0.10, y1=0.92, xref="x", yref="y",
                  line=dict(color=color, width=1.4), fillcolor=INK, layer="below")
    fig.add_shape(type="rect", x0=x0, x1=x0 + 0.012 * (x1 - x0) * 6, y0=0.10, y1=0.92,
                  line=dict(width=0), fillcolor=color, opacity=0.85, layer="below")
    cx = (x0 + x1) / 2
    fig.add_annotation(x=cx, y=0.84, text=f"<span style='font-size:26px'>{icon}</span>",
                       showarrow=False, font=dict(size=26))
    fig.add_annotation(x=cx, y=0.70, text=f"<b>{_wrap(title, 24)}</b>", showarrow=False,
                       font=dict(size=14, color=color), align="center")
    fig.add_annotation(x=cx, y=0.44, text="<br>".join(f"· {b}" for b in bullets),
                       showarrow=False, font=dict(size=12, color=TEXT), align="center")
    fig.add_annotation(x=cx, y=0.17, text=kicker, showarrow=False,
                       font=dict(size=10, color=MUTED, family=MONOF))


def bridge_figure(step, style, animate):
    """Substation card → busbar → AI card, with a packet that travels across."""
    fig = go.Figure()
    _card(fig, 0.02, 0.36, EE, step["ee_icon"], step["ee"], step["ee_bullets"],
          "IN THE SUBSTATION")
    _card(fig, 0.64, 0.98, AISIDE, step["ai_icon"], step["ai"], step["ai_bullets"],
          "IN THE AI")

    # the busbar between them
    for y in (0.55, 0.47):
        fig.add_shape(type="line", x0=0.38, x1=0.62, y0=y, y1=y,
                      line=dict(color=EDGE, width=2))
    fig.add_annotation(x=0.50, y=0.68, text="<b>IS THE SAME THING AS</b>", showarrow=False,
                       font=dict(size=11, color=MUTED, family=MONOF))
    fig.add_annotation(x=0.50, y=0.33, text=_wrap(step["tech"], 26), showarrow=False,
                       font=dict(size=11, color=TECH, family=MONOF), align="center")

    fig.add_trace(go.Scatter(x=[0.38], y=[0.51], mode="markers",
                             marker=dict(size=15, color=EE, symbol="diamond",
                                         line=dict(color=TEXT, width=1)),
                             hoverinfo="skip", showlegend=False))
    frames = []
    for i in range(24):
        f = i / 23
        frames.append(go.Frame(data=[go.Scatter(
            x=[0.38 + 0.24 * f], y=[0.51], mode="markers",
            marker=dict(size=15, symbol="diamond",
                        color=EE if f < 0.5 else AISIDE,
                        line=dict(color=TEXT, width=1)))]))
    fig.frames = frames
    fig.update_xaxes(visible=False, range=[0, 1])
    fig.update_yaxes(visible=False, range=[0, 1])
    fig.update_layout(margin=dict(l=6, r=6, t=6, b=6))
    return animate(style(fig, 300), frames, ms=55)


# ============================================================================
# NAVIGATION
# ============================================================================
def _nav(step, key):
    i = ORDER.index(step["id"])
    prev_s = BY_ID[ORDER[i - 1]] if i > 0 else None
    next_s = BY_ID[ORDER[i + 1]] if i < len(ORDER) - 1 else None
    c1, c2, c3 = st.columns([1, 1.25, 1])
    with c1:
        if prev_s:
            if st.button(f"◀  {prev_s['ee']}", key=f"prev_{key}", width="stretch"):
                goto(prev_s["id"])
        elif st.button("◀  The project overview", key=f"prev_{key}", width="stretch"):
            goto("start")
    with c2:
        st.markdown(f"<div class='pos'>▐ STEP {i+1:02d} / {len(ORDER):02d} ▌"
                    f"<br><b>{step['ee']}</b></div>", unsafe_allow_html=True)
    with c3:
        if next_s:
            if st.button(f"{next_s['ee']}  ▶", key=f"next_{key}", width="stretch"):
                goto(next_s["id"])
        elif st.button("Back to the overview  ▶", key=f"next_{key}", width="stretch"):
            goto("start")


# ============================================================================
# open_page  -  Parts 1, 2 and 3, rendered ABOVE the stage renderer
# ============================================================================
def open_page(stage, style, animate):
    step = BY_ID.get(stage)
    if step is None:
        return
    pname, pdesc = PHASES[step["phase"]]
    i = ORDER.index(stage)

    _nav(step, "top")
    st.markdown(
        f"<div class='tele' style='margin-top:14px'>⟨ASHGROVE 132/33kV⟩ &nbsp; "
        f"STEP {i+1:02d}/{len(ORDER)} &nbsp;·&nbsp; PHASE {step['phase']+1:02d}/{len(PHASES)} "
        f"&nbsp;·&nbsp; <span style='color:{EE}'>{pname.upper()}</span> "
        f"&nbsp;—&nbsp; {pdesc}</div>", unsafe_allow_html=True)
    st.markdown(f"# {step['ee_icon']}  {step['ee']}")
    st.markdown(f"<span class='sub'>▸ this electrical engineering step is the AI concept </span>"
                f"<b style='color:{AISIDE}'>{step['ai']}</b>", unsafe_allow_html=True)
    st.divider()

    _bus("01", "Electrical Engineering", EE)
    st.markdown(f"<div class='relay'>{step['site']}</div>", unsafe_allow_html=True)
    st.write("")

    _bus("02", "The Challenge", RED)
    st.markdown(f"<div class='relay warn'>{step['challenge']}</div>", unsafe_allow_html=True)
    st.write("")

    _bus("03", "AI Connection", AISIDE)
    st.markdown(f"<div class='relay ai'>{step['ai_link']}</div>", unsafe_allow_html=True)
    st.plotly_chart(bridge_figure(step, style, animate), width="stretch",
                    key=f"bridge_{stage}")
    st.caption("▶ Press Play — the reading travels the busbar from the substation into the AI.")
    st.divider()

    _bus("04", "Technical Idea", TECH)
    st.caption(f"{step['tech']} — interactive. Change things and watch what happens.")


# ============================================================================
# close_page  -  Part 5, rendered BELOW the stage renderer
# ============================================================================
def close_page(stage):
    step = BY_ID.get(stage)
    if step is None:
        return
    st.divider()

    _bus("05", "Key Takeaway", GREEN)
    st.markdown(f"<div class='relay ok' style='font-size:19px;font-weight:600;line-height:1.5'>"
                f"{step['takeaway']}</div>", unsafe_allow_html=True)
    st.write("")

    _bus("06", "In the Notebook", "#8bc34a")
    c1, c2 = st.columns(2)
    c1.markdown(f"**Where you implement it**\n\n{step['notebook']}")
    c2.markdown(f"**What it contributes**\n\n{step['contributes']}")

    st.write("")
    segs = []
    for i, (pname, _) in enumerate(PHASES):
        cls = "cur" if i == step["phase"] else ("done" if i < step["phase"] else "")
        segs.append(f"<span class='seg {cls}' title='{pname}'>{i+1:02d}</span>")
    st.markdown(f"<div class='rail'><span class='rail-lab'>PHASE</span>" + "".join(segs)
                + f"<span class='rail-lab' style='margin-left:auto'>"
                f"{step['phase']+1:02d}/{len(PHASES)} · {PHASES[step['phase']][0].upper()}"
                f"</span></div>", unsafe_allow_html=True)
    st.write("")
    _nav(step, "bottom")


# ============================================================================
# THE MIND MAP  -  clickable workflow, one node per phase
# ============================================================================
MAP_NODES = [
    ("Power Transformer", "the-asset", 0),
    ("Sensors", "the-target", 1),
    ("Operating Data", "log", 2),
    ("Data Preparation", "clean", 3),
    ("Feature Engineering", "features", 3),
    ("Machine Learning", "leaderboard", 5),
    ("Temperature Prediction", "predict", 9),
    ("Condition Monitoring", "metrics", 7),
    ("Maintenance Planning", "recommend", 9),
    ("Reliable Power Supply", "dashboard", 9),
]


def mind_map(style):
    """The clickable workflow. Click a node to open its page."""
    n = len(MAP_NODES)
    ys = [n - i for i in range(n)]
    xs = [0.5] * n
    fig = go.Figure()
    for i in range(n - 1):
        fig.add_annotation(x=0.5, y=ys[i + 1], ax=0.5, ay=ys[i], xref="x", yref="y",
                           axref="x", ayref="y", showarrow=True, arrowhead=2,
                           arrowsize=1.1, arrowwidth=1.6, arrowcolor=EDGE)
    colors = [EE if i < 3 else (TECH if i < 5 else (AISIDE if i < 7 else GREEN))
              for i in range(n)]
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers+text",
        marker=dict(size=34, color=INK, line=dict(color=colors, width=2.4), symbol="square"),
        text=[f"  <b>{lbl}</b>" for lbl, _, _ in MAP_NODES],
        textposition="middle right", textfont=dict(size=14, color=TEXT),
        customdata=[sid for _, sid, _ in MAP_NODES],
        hovertemplate="<b>%{text}</b><br>click to open<extra></extra>", showlegend=False))
    fig.update_xaxes(visible=False, range=[0.35, 1.9])
    fig.update_yaxes(visible=False, range=[0.2, n + 0.8])
    fig.update_layout(margin=dict(l=6, r=6, t=6, b=6), clickmode="event+select")
    return style(fig, 40 * n + 60)


# ============================================================================
# THE ENGINEERING -> AI MAPPING FIGURE
# ============================================================================
def mapping_figure(style):
    """Two columns: read down the left and you have a monitoring scheme;
    read down the right and you have an ML pipeline. Same column."""
    rows = [("Transformer monitoring", "The problem definition"),
            ("Sensor measurements", "The input features"),
            ("Fibre-optic probe reading", "The label"),
            ("Data inspection", "Exploratory analysis"),
            ("Data cleaning", "Removing invalid rows"),
            ("Per-unit and rise quantities", "Feature engineering"),
            ("Common scale", "Normalisation"),
            ("A fair commissioning test", "Train / test split"),
            ("IEEE C57.91 estimate", "The baseline"),
            ("Hot-spot temperature", "The regression output"),
            ("Condition monitoring", "Model evaluation"),
            ("Maintenance decision support", "Rules on top of the model")]
    n = len(rows)
    fig = go.Figure()
    for i, (l, r) in enumerate(rows):
        y = n - i
        fig.add_shape(type="rect", x0=0.02, x1=0.44, y0=y - 0.34, y1=y + 0.34,
                      line=dict(color=EE, width=1), fillcolor=INK, layer="below")
        fig.add_shape(type="rect", x0=0.56, x1=0.98, y0=y - 0.34, y1=y + 0.34,
                      line=dict(color=AISIDE, width=1), fillcolor=INK, layer="below")
        fig.add_annotation(x=0.23, y=y, text=l, showarrow=False,
                           font=dict(size=12.5, color=EE))
        fig.add_annotation(x=0.77, y=y, text=r, showarrow=False,
                           font=dict(size=12.5, color=AISIDE))
        fig.add_annotation(x=0.50, y=y, text="→", showarrow=False,
                           font=dict(size=15, color=MUTED))
    fig.add_annotation(x=0.23, y=n + 0.9, text="<b>⚡ ELECTRICAL ENGINEERING</b>",
                       showarrow=False, font=dict(size=12, color=EE, family=MONOF))
    fig.add_annotation(x=0.77, y=n + 0.9, text="<b>🤖 MACHINE LEARNING</b>",
                       showarrow=False, font=dict(size=12, color=AISIDE, family=MONOF))
    fig.update_xaxes(visible=False, range=[0, 1])
    fig.update_yaxes(visible=False, range=[0.3, n + 1.4])
    fig.update_layout(margin=dict(l=6, r=6, t=6, b=6))
    return style(fig, 42 * n + 70)
