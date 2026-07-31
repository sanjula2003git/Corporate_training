"""
Builds Transformer_HotSpot_Temperature_AI.ipynb from nbformat cells.
Run:  py -3.13 build_nb.py

Same five-part-per-step layout as the Smart Construction / Building Energy
notebooks: one intro block (problem -> what we build -> workflow ->
Engineering-to-AI map), then 30 steps, each rendered as

    header + Part 1 (electrical engineering) + Part 2 (the challenge)
    Part 3 (where the AI comes in) + the bridge table + Part 4 header
    the code
    Part 5 (what you just built) + a one-line key takeaway

The engineering is standards-based and is used BOTH to generate the substation
log and to check the model, so the notebook and the standard never disagree:

  * IEEE C57.91 clause 7 - top-oil rise  DTO_r * ((K^2 R + 1)/(R+1))^n
                           winding gradient  DTH_r * K^(2m)
  * IEEE C57.91 clause 5 - ageing acceleration factor
                           F_AA = exp(15000/383 - 15000/(theta_h + 273))
  * IEEE C57.91 table 8  - hot-spot limits 110 / 120 / 140 C

Every number quoted in the markdown was measured by running the notebook. If you
change a constant here, re-run the smoke test and re-read the prose.

APP: set to a deployed Streamlit URL to switch on the per-step links. Left as ""
the notebook is built with no links at all, rather than dead ones.
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

APP = ""          # e.g. "https://transformer-hotspot.streamlit.app"

cells = []
def md(t):  cells.append(new_markdown_cell(t.strip("\n")))
def co(t):  cells.append(new_code_cell(t.strip("\n")))

def link(stage, label):
    return f"[{label}]({APP}/?stage={stage})" if APP else label


# ============================================================================
# THE PHASES  (one substation, one year, in the order a real project runs it)
# ============================================================================
PHASES = [
    ("The Transformer In Service", "Why a transformer heats, and why the hot spot decides its life."),
    ("One Hour Of Operation",      "The thermal model, and the temperature nobody measures."),
    ("The Monitoring Log",         "The historian export lands and gets checked."),
    ("Preparing The Data",         "Bad readings out, physics in, the year split honestly."),
    ("The First Prediction",       "The standard's own model, then a straight line."),
    ("Models That Bend",           "Three ensembles on the same columns."),
    ("Reading The Model",          "Which sensors earn their place, and how the prediction moves."),
    ("The Monitoring Dashboard",   "Predicted against measured, where it matters."),
    ("What The Model Does Not Know", "The limit, measured rather than asserted."),
    ("Decision Support",           "One temperature, one recommendation, one fleet view."),
]

NUM = ["①","②","③","④","⑤","⑥","⑦","⑧","⑨","⑩",
       "⑪","⑫","⑬","⑭","⑮","⑯","⑰","⑱","⑲","⑳",
       "㉑","㉒","㉓","㉔","㉕","㉖","㉗","㉘","㉙","㉚"]


# ============================================================================
# THE STEPS
#   Each entry drives four cells. `body` is a list of ('md', text) / ('co', code)
#   items making up Part 4 - most steps have exactly one code cell.
# ============================================================================
STEPS = []
def step(**kw):
    STEPS.append(kw)


# ------------------------------------ PHASE 1 - THE TRANSFORMER IN SERVICE
step(
    id="the-asset", phase=0, icon="⚡", ai_icon="\U0001f916",
    ee="A Transformer Under Load", ai="Why Thermal Monitoring Needs AI",
    tech="Four units, 35,040 hourly readings, one year",
    site="""Ashgrove substation. Four 40 MVA 132/33 kV power transformers, feeding a mixed industrial and
domestic network.

- Each unit is 3, 9, 16 and 22 years old.
- Each carries between 240 A and 980 A on the 33 kV side.
- None of them has an installed spare.
- Replacement lead time is measured in months. Replacement cost is measured in millions.

They run continuously, and they run hot.""",
    challenge="""A transformer is not damaged by heat. It is damaged by **time spent hot**.

- Insulation paper degrades chemically, and the rate roughly doubles every 6 °C.
- The damage is cumulative and cannot be undone.
- Nothing visible happens until the day the unit fails.

The engineer needs to know the internal temperature **now**, on every unit, every hour. Four units,
8,760 hours each, is 35,040 assessments a year. Nobody does that by hand.""",
    ai_link="""Be clear about what is being asked for. Not judgement, and not autonomy. Something duller:

- A way to turn the measurements the substation **already produces** into the one temperature it does not
  measure.
- Continuously, on every unit, without anybody watching.

The engineer still decides what to do about it.""",
    bridge=[("Four transformers, continuously loaded", "35,040 labelled examples"),
            ("Sensors that already exist", "The input features"),
            ("The temperature inside the winding", "The prediction target")],
    body=[("co", r'''
# The fleet. Every constant below is a nameplate value and is used consistently
# for the rest of the notebook - to build the log, to run the standard's thermal
# model, and to check the machine learning against both.

I_RATED = 700.0     # A    rated current, 33 kV side of a 40 MVA unit
V_RATED = 132.0     # kV   rated voltage, 132 kV side
DTO_R   = 32.0      # K    top-oil rise over ambient at rated load, fans running
DTH_R   = 24.0      # K    hot-spot rise over top oil at rated load
R_RATIO = 6.0       #      ratio of load loss to no-load loss at rated load
N_EXP   = 0.9       #      oil exponent          (IEEE C57.91, ONAF)
M_EXP   = 0.8       #      winding exponent      (IEEE C57.91, ONAF)

FLEET = pd.DataFrame({
    "unit_id":  ["T1", "T2", "T3", "T4"],
    "age_years": [3, 9, 16, 22],
    "mva":       [40, 40, 40, 40],
    "cooling":   ["ONAN/ONAF"] * 4,
})

print("Ashgrove substation")
print(FLEET.to_string(index=False))
print()
print(f"Rated current (33 kV side): {I_RATED:.0f} A")
print(f"A year of hourly readings:  {4 * 8760:,} rows")
''')],
    built="""The fleet, and the nameplate constants the whole notebook runs on.

- `I_RATED` converts a current in amps into **per-unit load**, `K`. Every thermal equation uses `K`, not amps.
- `DTO_R` and `DTH_R` are the two temperature rises the manufacturer guarantees at rated load.
- `R_RATIO`, `N_EXP` and `M_EXP` describe how those rises change when the load is not rated.""",
    takeaway="A transformer's life is set by the temperature inside it, and nobody can track that by hand on four units for 8,760 hours.",
)

step(
    id="why-heat", phase=0, icon="\U0001f525", ai_icon="\U0001f4c8",
    ee="Where The Heat Comes From", ai="A Non-Linear Relationship",
    tech="Load loss ~ K², no-load loss ~ V²",
    site="""A transformer converts voltage, not power. The power it does not pass on becomes heat.

Two sources:

- **Load loss** — current through winding resistance, `I²R`. It rises with the **square** of load.
- **No-load loss** — hysteresis and eddy currents in the core. Roughly constant, and set by voltage, not
  by load.

At rated load these four units run about 6:1 load loss to no-load loss.""",
    challenge="""The square is the whole problem.

- Take a transformer from 50 % to 100 % load and the current doubles.
- The load loss goes up **four times**, not two.
- Push to 120 % and load loss is nearly six times the half-load figure.

The load doubles; the heat does not. Every intuition built on straight lines is wrong here, and the error
is largest exactly where it matters — at high load.""",
    ai_link="""This is the first reason a straight-line model will not do.

- The relationship between load and heat is a **power law**, not a proportion.
- Cooling stages switch in and out, which puts steps in the curve.
- Ambient conditions shift the whole curve up and down.

Machine learning is not needed because the physics is unknown. It is needed because the **combination** of
these effects, on a real unit that has drifted from its nameplate, has no clean closed form.""",
    bridge=[("Load loss rising with K²", "A non-linear target"),
            ("Cooling stages switching", "A discontinuity in the curve"),
            ("Total loss = load + no-load", "Feature interaction")],
    body=[("co", r'''
# Losses across the loading range, in per-unit of the total loss at rated load.

K = np.linspace(0.2, 1.4, 200)
load_loss  = K**2 * R_RATIO / (R_RATIO + 1.0)   # copper: rises with the square of load
no_load    = np.full_like(K, 1.0 / (R_RATIO + 1.0))  # core: set by voltage, near constant
total_loss = load_loss + no_load

fig = go.Figure()
fig.add_trace(go.Scatter(x=K, y=no_load,    name="No-load (core) loss", line=dict(color=MUTED, width=2)))
fig.add_trace(go.Scatter(x=K, y=load_loss,  name="Load (copper) loss",  line=dict(color=AMBER, width=2)))
fig.add_trace(go.Scatter(x=K, y=total_loss, name="Total loss",          line=dict(color=RED, width=3)))
fig.add_vline(x=1.0, line=dict(color=MUTED, dash="dot"),
              annotation_text="rated load", annotation_position="top left")
fig.update_layout(title="Transformer losses become heat, and load loss rises with the square of load",
                  xaxis_title="Load K (per unit of rated)", yaxis_title="Loss (per unit of total at rated)",
                  height=420, template="plotly_white")
fig.show()

for k in (0.5, 1.0, 1.2):
    tot = k**2 * R_RATIO / (R_RATIO + 1.0) + 1.0 / (R_RATIO + 1.0)
    print(f"K = {k:.1f}  ->  load loss {k**2 * R_RATIO / (R_RATIO + 1.0):.2f} pu, total {tot:.2f} pu")
print()
print(f"Half load to full load: total heat rises {(1.0**2 * R_RATIO + 1) / (0.5**2 * R_RATIO + 1):.2f} times.")
''')],
    built="""The loss curve, in per-unit so it applies to any rating.

- No-load loss is the flat line. It is there whenever the transformer is energised, loaded or not.
- Load loss is the parabola. It overtakes no-load loss at about 41 % load and dominates from there.
- Total heat rises **2.8 times** between half load and full load.""",
    takeaway="Heat rises with the square of load, so the last 20 % of loading costs far more than the first 20 %.",
)

step(
    id="hot-spot", phase=0, icon="\U0001f321️", ai_icon="\U0001f3af",
    ee="Why The Hot Spot, Not The Oil", ai="Choosing The Target Variable",
    tech="F_AA = exp(15000/383 − 15000/(θ_h + 273))",
    site="""Three temperatures matter inside a transformer, and they are not the same number.

| Temperature | Typical value at full load | Measured? |
|---|---|---|
| Ambient air | 30 °C | Yes, cheaply |
| Top oil | 62 °C | Yes, by a dial thermometer on every unit |
| **Winding hot spot** | **89 °C** | **Rarely** |

The hot spot is the hottest point of the winding, near the top of the coil where the oil is already warm
and the leakage flux is highest. It is typically **25–30 °C above the top oil**.""",
    challenge="""Insulation ageing is governed by the hot spot, and it is governed **exponentially**.

IEEE C57.91 defines the ageing acceleration factor:

`F_AA = exp(15000/383 − 15000/(θ_h + 273))`

- At 110 °C, `F_AA = 1`. The insulation ages at its design rate.
- At 98 °C, `F_AA = 0.28`. It ages roughly four times slower.
- At 120 °C, `F_AA = 2.7`.
- At 140 °C, `F_AA = 17`.

An hour at 140 °C costs the same insulation life as **17 hours** at 110 °C. Watching the oil temperature
and assuming the winding follows is how transformers get quietly destroyed.""",
    ai_link="""Choosing what to predict is an engineering decision, not a modelling one.

- Predicting **top oil** would be easy and nearly useless — it is already measured.
- Predicting **hot spot** is useful precisely because it is not measured on most units.

So the target variable is `hotspot_temp_c`. Everything else in the log is an input.""",
    bridge=[("The hottest point in the winding", "The target variable, y"),
            ("Ageing that doubles every 6 °C", "Why a 2 °C error matters"),
            ("Oil temperature, already measured", "An input feature, not the answer")],
    body=[("co", r'''
# The IEEE C57.91 ageing acceleration factor, and what it does to a 2 C error.

def ageing_factor(theta_h):
    "IEEE C57.91 clause 5: relative rate of insulation ageing at hot-spot temperature theta_h."
    return np.exp(15000.0 / 383.0 - 15000.0 / (np.asarray(theta_h, dtype=float) + 273.0))

t = np.linspace(70, 150, 300)
fig = go.Figure()
fig.add_trace(go.Scatter(x=t, y=ageing_factor(t), name="F_AA",
                         line=dict(color=RED, width=3), fill="tozeroy",
                         fillcolor="rgba(239,83,80,0.12)"))
for limit, label in [(110, "110 °C  normal life expectancy"),
                     (120, "120 °C  planned loading beyond nameplate"),
                     (140, "140 °C  long-time emergency loading")]:
    fig.add_vline(x=limit, line=dict(color=MUTED, dash="dot"),
                  annotation_text=label, annotation_textangle=-90)
fig.update_layout(title="Insulation ageing against hot-spot temperature (IEEE C57.91)",
                  xaxis_title="Hot-spot temperature (°C)",
                  yaxis_title="Ageing acceleration factor F_AA", yaxis_type="log",
                  height=430, template="plotly_white")
fig.show()

print("Hot spot   F_AA    meaning")
for th in (86, 98, 104, 110, 116, 122, 140):
    print(f"  {th:3d} °C   {ageing_factor(th):6.2f}   1 hour here costs {ageing_factor(th):5.2f} hours of design life")

print()
print("Why a small error in °C is not a small error in life:")
for th in (100, 110, 120):
    under = 100 * (1 - ageing_factor(th - 2) / ageing_factor(th))
    print(f"  predicting {th - 2} °C when the truth is {th} °C understates the ageing rate by {under:.0f} %")
''')],
    built="""The ageing curve, and the cost of being slightly wrong.

- The vertical axis is logarithmic. A straight line on that plot is an exponential.
- A **2 °C** under-prediction understates the ageing rate by about **19 %**, anywhere in the range.
- That is why the evaluation section later checks the error **in the hot band separately**, not just on
  average.""",
    takeaway="The hot spot is the temperature that decides transformer life, and it is the one temperature most transformers do not measure.",
)

step(
    id="enter-ai", phase=0, icon="\U0001f9e0", ai_icon="\U0001f91d",
    ee="Why This Needs Machine Learning", ai="Supervised Regression",
    tech="Learn f(sensors) → θ_h from recorded examples",
    site="""There is already a standard way to estimate the hot spot. IEEE C57.91 gives it in closed form,
from the load and the measured oil temperature.

It is a good model. It is also a **nameplate** model:

- It assumes the hot-spot factor stated at the factory test.
- It assumes clean radiators and oil in its original condition.
- It assumes the thermometer reads the top oil, immediately.

None of those stay true for twenty-two years in service.""",
    challenge="""Every unit drifts away from its nameplate, and drifts differently.

- Radiators foul. Oil degrades. Cooling capacity falls a few percent per decade.
- Winding design and oil-duct geometry differ, so the real hot-spot factor differs unit to unit.
- The oil thermometer sits in a pocket and lags the actual top oil by an hour or more.

Nobody re-derives a thermal model per unit per year. So the standard's model is used as printed, and the
error is simply accepted.""",
    ai_link="""This is exactly what supervised regression is for.

- **Inputs:** the sensor readings the substation already logs.
- **Output:** the hot-spot temperature.
- **Training data:** a year of both, from units that do have a fibre-optic probe fitted.

The model learns *this fleet's* actual behaviour, including everything the nameplate does not describe. The
standard's model becomes the **baseline to beat**, not the answer.""",
    bridge=[("The IEEE C57.91 thermal model", "The baseline"),
            ("Drift the nameplate cannot describe", "What the model learns"),
            ("A year of logged readings", "The training set")],
    body=[("co", r'''
# The claim this notebook has to prove, stated before any model is fitted.

promise = pd.DataFrame({
    "Method": ["IEEE C57.91 nameplate model",
               "Machine learning, raw sensors",
               "Machine learning, engineering features"],
    "Knows about": ["The design, as tested at the factory",
                    "This fleet, as it actually runs",
                    "This fleet, plus the physics we can write down"],
    "Measured in": ["Step 14", "Step 15", "Step 20"],
})
print(promise.to_string(index=False))
print()
print("Nothing above is assumed. Each row is fitted and scored on readings the model never saw.")
''')],
    built="""The claim, on the table before anything is fitted.

- The standard's model is not a straw man. It is genuinely good, and it is what the industry uses.
- The question is whether a model that has **seen this fleet** does better than one that has only seen the
  design.
- Step 20 answers it with numbers.""",
    takeaway="Machine learning is not replacing the thermal standard — it is learning the part of each transformer's behaviour the standard was never given.",
)


# ------------------------------------------ PHASE 2 - ONE HOUR OF OPERATION
step(
    id="thermal-model", phase=1, icon="\U0001f4d0", ai_icon="⚙️",
    ee="The Thermal Model", ai="Domain Knowledge As Code",
    tech="θ_h = θ_oil + Δθ_h,r · K^(2m)",
    site="""IEEE C57.91 builds the hot-spot temperature in two steps.

**Step one — top-oil rise over ambient**

`Δθ_oil = Δθ_oil,rated · ((K²R + 1) / (R + 1))^n`

The `K²R + 1` term is total loss: load loss rising with `K²`, plus constant core loss.

**Step two — hot-spot rise over top oil**

`Δθ_hs = Δθ_hs,rated · K^(2m)`

With `m = 0.8`, that is `K^1.6`. The winding gradient grows faster than load but slower than loss.

`θ_hotspot = θ_ambient + Δθ_oil + Δθ_hs`""",
    challenge="""The equations are simple. The conditions they run under are not.

- The oil has a time constant of about **three hours**. It never reaches the steady state the formula
  describes, because the load has already changed.
- Cooling fans switch in stages, which changes the exponents mid-operation.
- Cold oil is more viscous, so the winding gradient is *larger* on a cold day at the same load.

The formula gives the answer for a transformer that has been sitting at constant load forever. Real ones
never do.""",
    ai_link="""Write the physics down anyway.

- It becomes the baseline the model has to beat.
- It becomes the source of the **engineered features** — `K`, `K^1.6`, oil rise over ambient.
- It becomes the sanity check: if the model disagrees with the physics at high load, the model is wrong.

Domain knowledge does not compete with machine learning here. It feeds it.""",
    bridge=[("Δθ_oil = f(K²R + 1)", "A feature: load_pu squared"),
            ("Δθ_hs = f(K^1.6)", "A feature: load_pu_16"),
            ("Cooling stage changes the exponent", "A categorical feature")],
    body=[("co", r'''
# IEEE C57.91 clause 7, written once and used everywhere in this notebook.

STAGE_OIL = {0: 1.35, 1: 1.10, 2: 1.00}   # top-oil rise multiplier: fans off / stage 1 / stage 2
STAGE_HS  = {0: 1.00, 1: 1.10, 2: 1.18}   # hot-spot factor: better oil circulation, hotter winding gradient

def top_oil_rise(K, v_pu=1.0, stage=2, age_years=0.0):
    "Steady-state top-oil rise over ambient, K. IEEE C57.91 clause 7."
    fouling = 1.0 + 0.0045 * age_years          # radiators foul, cooling capacity falls with age
    loss_pu = (np.asarray(K, float)**2 * R_RATIO + np.asarray(v_pu, float)**2) / (R_RATIO + 1.0)
    return DTO_R * loss_pu**N_EXP * STAGE_OIL[stage] * fouling

def hotspot_gradient(K, ambient_c=25.0, stage=2, age_years=0.0, h_factor=1.0):
    "Hot-spot rise above top oil, K. Grows as K^(2m) = K^1.6."
    viscosity = np.clip(1.0 + 0.0045 * (25.0 - np.asarray(ambient_c, float)), 0.93, 1.12)
    fouling   = 1.0 + 0.0025 * age_years
    return DTH_R * np.asarray(K, float)**(2 * M_EXP) * STAGE_HS[stage] * viscosity * fouling * h_factor

# One hour on T3: 720 A, 36 C ambient, oil reading 68 C, fans at stage 2, 16 years old.
K_now = 720.0 / I_RATED
grad  = hotspot_gradient(K_now, ambient_c=36.0, stage=2, age_years=16)

print(f"Load                 {720:.0f} A  =  {K_now:.3f} pu")
print(f"Ambient              36.0 °C")
print(f"Top oil (measured)   68.0 °C   (rise over ambient: {68 - 36:.1f} K)")
print(f"Winding gradient     {grad:.1f} K   = {DTH_R} × {K_now:.3f}^1.6 × stage and condition factors")
print(f"Hot spot             {68 + grad:.1f} °C")
print()
print(f"Steady-state top-oil rise at this load: {top_oil_rise(K_now, 1.0, 2, 16):.1f} K")
print("The measured rise is lower - the oil has a three-hour time constant and is still catching up.")
''')],
    built="""The standard's thermal model, as two functions.

- `top_oil_rise` is used to build the log and is available for what-if work later.
- `hotspot_gradient` is the piece that matters: it turns a load and a measured oil temperature into a
  hot-spot temperature.
- The worked hour lands at **97 °C**, and the measured oil rise is already below the steady-state value.
  That gap is the three-hour oil time constant, and it is the first thing the standard's model cannot see.""",
    takeaway="The physics is worth writing down even when you plan to use machine learning, because it becomes both the baseline and the features.",
)

step(
    id="the-target", phase=1, icon="\U0001f50e", ai_icon="\U0001f4cb",
    ee="The Temperature Nobody Measures", ai="Labels, And Where They Come From",
    tech="Fibre-optic probe on the reference units",
    site="""Direct hot-spot measurement needs a **fibre-optic probe** installed between the winding discs at
manufacture.

- It cannot be retrofitted without untanking the transformer.
- It costs a small fraction of the unit when specified new, and a large fraction when added later.
- The great majority of transformers in service do not have one.

Ashgrove's four units do — they were specified with probes as a condition-monitoring pilot.""",
    challenge="""So the fleet has a year of true hot-spot readings, and the rest of the network has none.

That is the whole opportunity, and the whole limitation:

- **Opportunity:** four instrumented units can teach a model that then runs on units without probes.
- **Limitation:** the model can only be trusted on transformers that behave like the four it learned from.

Step 27 measures exactly how far that trust extends.""",
    ai_link="""In supervised learning the measured hot-spot readings are the **labels**.

- Labels are almost always the expensive part of a dataset. Here they need a probe installed at manufacture.
- The inputs are cheap: current, voltage, ambient, humidity, oil temperature, fan status.
- A model is worth building precisely when the inputs are cheap and the label is expensive.

That asymmetry is the business case, stated in one line.""",
    bridge=[("Fibre-optic probe readings", "The labels, y"),
            ("Current, voltage, ambient, oil", "The features, X"),
            ("Units without a probe", "Where the model gets deployed")],
    body=[("co", r'''
# What the substation records, and what it costs to record it.

catalogue = pd.DataFrame([
    ("load_current_a",        "Current transformer, 33 kV side",  "Input",  "Already fitted"),
    ("voltage_kv",            "Voltage transformer, 132 kV side", "Input",  "Already fitted"),
    ("ambient_temp_c",        "Substation weather station",       "Input",  "Already fitted"),
    ("humidity_pct",          "Substation weather station",       "Input",  "Already fitted"),
    ("oil_temp_c",            "Top-oil dial thermometer",         "Input",  "Already fitted"),
    ("cooling_stage",         "Fan contactor auxiliary contacts",  "Input",  "Already fitted"),
    ("transformer_age_years", "Asset register",                   "Input",  "Free"),
    ("hotspot_temp_c",        "Fibre-optic winding probe",        "TARGET", "Factory-fit only"),
], columns=["Column", "Where it comes from", "Role", "Cost to obtain"])

print(catalogue.to_string(index=False))
print()
print("Seven cheap inputs, one expensive label. That asymmetry is why this model is worth building.")
''')],
    built="""The column catalogue, with the role and the cost of each.

- Seven inputs, all from instrumentation that is already on the transformer or already in the asset register.
- One target, from an instrument most transformers will never have.
- The model's job is to replace the expensive instrument with arithmetic on the cheap ones.""",
    takeaway="Build a model when the inputs are cheap and the answer is expensive — that is exactly the case here.",
)


# --------------------------------------------- PHASE 3 - THE MONITORING LOG
step(
    id="log", phase=2, icon="\U0001f4be", ai_icon="\U0001f5c3️",
    ee="The Historian Export", ai="The Raw Dataset",
    tech="35,040 rows × 11 columns, hourly, one year",
    site="""The substation SCADA historian holds every reading it has ever taken. The condition-monitoring
request produces one CSV.

- Four units, hourly, calendar year 2025 — 35,040 readings.
- Slightly more rows than that, because the historian exported part of it twice.
- Exactly what the field instruments reported — including the hours they reported nonsense.

No cleaning has been applied. That is deliberate; the export is the evidence.""",
    challenge="""A historian export is a record of the instrumentation, not of the transformer.

- Communications drop and the value is simply missing.
- A sensor freezes and repeats yesterday's number for fourteen hours.
- A unit is taken out for switching and reads near-zero current while the winding cools to ambient.
- A humidity transmitter fails and reports a raw byte value.

Every one of those is in this file. Finding them is step 10.""",
    ai_link="""The dataset is the input to everything downstream, so this is where the discipline goes.

- Load it, then look at it. Do not clean anything yet.
- Establish what *should* be there before deciding what is wrong.

The cell below stands in for the historian. In a real project you would receive the CSV; here it is
generated so that the true physics is known and the model can be checked honestly against it.""",
    bridge=[("The SCADA historian", "The raw dataset"),
            ("One row per unit per hour", "One training example"),
            ("Instrument faults included", "Data quality work")],
    body=[
        ("md", """> **About the cell below.** It is the substation simulator: weather, loading, the IEEE thermal
> model, the fan control, sensor noise and the instrument faults. You do not need to read it to follow the
> notebook — in a real project this is the part somebody hands you as a CSV. It is included so every
> number later on can be checked against a known truth."""),
        ("co", r'''
# ---------------------------------------------------------------------------
# THE SUBSTATION SIMULATOR - stands in for a year of SCADA history.
# Skip this cell on a first read. It writes substation_thermal_log.csv.
# ---------------------------------------------------------------------------
UNITS     = [("T1", 3), ("T2", 9), ("T3", 16), ("T4", 22)]
H_UNIT    = {"T1": 1.00, "T2": 1.13, "T3": 0.93, "T4": 1.21}  # real per-unit hot-spot factors
UNIT_LOAD = {"T1": 0.92, "T2": 1.00, "T3": 1.06, "T4": 0.96}  # feeder loading, relative
TAU_OIL, TAU_POCKET = 3.0, 1.6   # h: oil time constant, and the thermometer-pocket lag

HOURS = 8760
_idx  = pd.date_range("2025-01-01", periods=HOURS, freq="h")
_doy, _hod, _dow = _idx.dayofyear.to_numpy(), _idx.hour.to_numpy(), _idx.dayofweek.to_numpy()
_rng  = np.random.default_rng(42)

# weather: season + day/night + a slow synoptic wander
_w = np.zeros(HOURS); _e = _rng.normal(0, 1.0, HOURS)
for _t in range(1, HOURS):
    _w[_t] = 0.93 * _w[_t - 1] + _e[_t]
_ambient  = 25.5 + 7.0*np.sin(2*np.pi*(_doy-110)/365) + 6.0*np.sin(2*np.pi*(_hod-9)/24) + _w
_humidity = np.clip(92 - 1.35*(_ambient - 18) + _rng.normal(0, 6, HOURS), 22, 99)
_cloud    = np.clip((_humidity - 45)/45.0, 0, 1)
_solar    = np.clip(np.sin(np.pi*(_hod - 6)/12), 0, None) * (1 - 0.75*_cloud)
_wind     = np.clip(_rng.gamma(2.0, 1.3, HOURS), 0, 9)

# network demand: morning and evening peaks, summer air conditioning, quieter weekends
_daily  = 0.60 + 0.32*np.exp(-0.5*((_hod-10)/2.6)**2) + 0.46*np.exp(-0.5*((_hod-20)/2.4)**2)
_season = 0.90 + 0.24*np.clip(np.sin(2*np.pi*(_doy-110)/365), -0.4, 1)
_week   = np.where(_dow >= 5, 0.88, 1.0)

def _simulate(unit, age, seed):
    rng = np.random.default_rng(seed)
    n = np.zeros(HOURS); ee = rng.normal(0, 0.030, HOURS)
    for t in range(1, HOURS):
        n[t] = 0.75*n[t-1] + ee[t]
    K = _daily * _season * _week * UNIT_LOAD[unit] * (1 + n)
    for _ in range(22):                       # contingency transfers from a sibling unit
        s = rng.integers(0, HOURS - 30)
        K[s:s + rng.integers(4, 26)] *= rng.uniform(1.14, 1.34)
    K = np.clip(K, 0.22, 1.38)
    v_pu = np.clip(1.0 - 0.035*(K - 0.8) + rng.normal(0, 0.010, HOURS), 0.94, 1.06)

    # slow drift the nameplate cannot describe: radiator dust, oil condition, sun angle
    d = np.zeros(HOURS); de = rng.normal(0, 0.50, HOURS); phi = np.exp(-1/12)
    for t in range(1, HOURS):
        d[t] = phi*d[t-1] + de[t]

    amb = _ambient + rng.normal(0, 0.4, HOURS)
    oil_true = np.zeros(HOURS); oil_meas = np.zeros(HOURS)
    hs = np.zeros(HOURS); stage = np.zeros(HOURS, dtype=int)
    oil_true[0] = oil_meas[0] = amb[0] + 18
    st, a_oil, a_pkt = 0, np.exp(-1/TAU_OIL), np.exp(-1/TAU_POCKET)
    for t in range(HOURS):
        prev = oil_meas[t-1] if t else oil_meas[0]
        # fan control acts on the measured oil temperature and load, with hysteresis
        if st == 0 and (prev > 55 or K[t] > 0.70):
            st = 1
        elif st == 1:
            if prev > 68 or K[t] > 0.92:  st = 2
            elif prev < 50 and K[t] < 0.62: st = 0
        elif st == 2 and prev < 63 and K[t] < 0.85:
            st = 1
        stage[t] = st
        target = amb[t] + top_oil_rise(K[t], v_pu[t], st, age) + 2.6*_solar[t] - 0.32*_wind[t]
        oil_true[t] = target if t == 0 else a_oil*oil_true[t-1] + (1-a_oil)*target
        oil_meas[t] = oil_true[t] if t == 0 else a_pkt*oil_meas[t-1] + (1-a_pkt)*oil_true[t]
        hs[t] = (oil_true[t]
                 + hotspot_gradient(K[t], amb[t], st, age, H_UNIT[unit])
                 + 1.8*_solar[t] + d[t])
    return pd.DataFrame({
        "timestamp": _idx, "unit_id": unit, "cooling_type": "ONAN/ONAF",
        "load_current_a": np.round(K*I_RATED*(1 + rng.normal(0, 0.005, HOURS)), 1),
        "voltage_kv":     np.round(v_pu*V_RATED*(1 + rng.normal(0, 0.003, HOURS)), 2),
        "ambient_temp_c": np.round(amb + rng.normal(0, 0.6, HOURS), 1),
        "humidity_pct":   np.round(np.clip(_humidity + rng.normal(0, 2.0, HOURS), 20, 100), 1),
        "oil_temp_c":     np.round(oil_meas + rng.normal(0, 1.4, HOURS), 1),
        "cooling_stage":  stage, "transformer_age_years": age,
        "hotspot_temp_c": np.round(hs + rng.normal(0, 0.6, HOURS), 1),
    })

_log = pd.concat([_simulate(u, a, 100 + i) for i, (u, a) in enumerate(UNITS)], ignore_index=True)

# ---- and now the instrumentation faults a real export would contain -------
_f = np.random.default_rng(7)
_log.loc[_f.choice(len(_log), 380, replace=False), "oil_temp_c"] = np.nan      # comms dropouts
_log.loc[_f.choice(len(_log), 120, replace=False), "hotspot_temp_c"] = np.nan  # probe outages
_log.loc[_f.choice(len(_log), 95,  replace=False), "humidity_pct"] = 255.0     # failed RH transmitter
for _u in ("T1", "T3"):                                                        # frozen ambient sensor
    _s = _log.index[_log.unit_id == _u][_f.integers(2000, 6000)]
    _log.loc[_s:_s + 13, "ambient_temp_c"] = _log.loc[_s, "ambient_temp_c"]
for _u in ("T2", "T4"):                                                        # unit switched out
    _s = _log.index[_log.unit_id == _u][_f.integers(2000, 6000)]
    _log.loc[_s:_s + 9, ["load_current_a", "cooling_stage"]] = [3.2, 0]
    _log.loc[_s:_s + 9, "oil_temp_c"] = _log.loc[_s:_s + 9, "ambient_temp_c"] + 1.5
    _log.loc[_s:_s + 9, "hotspot_temp_c"] = _log.loc[_s:_s + 9, "ambient_temp_c"] + 2.0
_log = pd.concat([_log, _log.sample(60, random_state=3)], ignore_index=True)    # historian re-export

_log.to_csv("substation_thermal_log.csv", index=False)
print(f"substation_thermal_log.csv written: {len(_log):,} rows")
'''),
        ("co", r'''
# From here on, treat the CSV as something that arrived by email.

log = pd.read_csv("substation_thermal_log.csv", parse_dates=["timestamp"])

print(f"{len(log):,} rows × {log.shape[1]} columns")
print(f"{log.timestamp.min():%Y-%m-%d} to {log.timestamp.max():%Y-%m-%d}, units: {sorted(log.unit_id.unique())}")
print()
print(log.head(4).to_string(index=False))
'''),
    ],
    built="""A year of substation history, as a table.

- Every row is one transformer for one hour.
- Every column is either something an instrument reported or something the asset register knows.
- Nothing has been corrected. The next three steps establish what is in it before anything is changed.""",
    takeaway="The raw export is evidence — look at it before you clean it, or you will clean away the thing you needed to see.",
)

step(
    id="inspect", phase=2, icon="\U0001f50d", ai_icon="\U0001f9ea",
    ee="Checking The Export", ai="Data Inspection",
    tech="dtypes, ranges, missing counts, duplicates",
    site="""Before any engineering conclusion, an engineer checks the instrument.

The same questions apply to a data export:

- Are the units what they claim to be — amps, kilovolts, degrees Celsius?
- Are the ranges physically possible for this plant?
- How much is missing, and is it missing evenly?
- Is anything repeated?""",
    challenge="""Impossible values do not announce themselves in a summary table.

- A humidity of 255 % is obvious once you look at the maximum.
- A load current of 3 A on a 700 A transformer looks like a rounding error until you realise the unit was
  de-energised.
- A frozen ambient sensor produces perfectly plausible numbers in a perfectly implausible sequence.

The summary catches the first. The other two need a plot or a check written on purpose.""",
    ai_link="""In machine learning this step has a specific consequence: every fault here becomes a training
example if you leave it in.

- A model trained on de-energised hours learns that low current means winding at ambient. It then
  under-predicts every genuinely lightly loaded hour.
- A model trained on 255 % humidity learns a relationship that does not exist.

Inspection is not paperwork. It is the difference between a model that works and one that does not.""",
    bridge=[("Checking the instrument", "Data inspection"),
            ("A physically impossible reading", "An outlier to remove"),
            ("A sensor that stopped updating", "A repeated-value check")],
    body=[("co", r'''
print(log.dtypes.to_string())
print()
print(log.describe().T[["min", "mean", "max"]].round(2).to_string())
print()
print("Missing values")
print(log.isna().sum()[lambda s: s > 0].to_string())
print()
print(f"Exact duplicate rows: {log.duplicated().sum()}")
print(f"Constant columns:     {[c for c in log.columns if log[c].nunique(dropna=True) == 1]}")
print()

# Three checks written on purpose, because the summary above does not reveal them.
print(f"Humidity above 100 %:                {(log.humidity_pct > 100).sum()} rows")
print(f"Load current below 10 A (de-energised): {(log.load_current_a < 10).sum()} rows")
_amb = log.sort_values(["unit_id", "timestamp"]).groupby("unit_id", sort=False).ambient_temp_c
_runs = _amb.transform(lambda s: s.groupby((s != s.shift()).cumsum()).transform("size"))
print(f"Ambient sensor unchanged for 6+ hours:  {int((_runs >= 6).sum())} rows")
''')],
    built="""Four faults, all of them real and all of them found before a model was fitted.

- Missing oil-temperature and hot-spot readings, from comms and probe outages.
- Humidity of 255 %, from a failed transmitter reporting a raw byte.
- Near-zero current, from hours when the unit was switched out.
- A frozen ambient sensor, invisible in the summary and obvious in the sequence.

Plus a constant `cooling_type` column and a block of duplicate rows from the historian re-export.""",
    takeaway="Some faults show up in a summary table and some only in a sequence — write the check for both.",
)

step(
    id="explore", phase=2, icon="\U0001f4ca", ai_icon="\U0001f517",
    ee="Reading The Fleet", ai="Exploratory Analysis",
    tech="Trends, scatter, correlation",
    site="""What the log looks like when you plot it.

Three things an engineer wants to see immediately:

- The **daily shape** — when the network peaks and when the transformers get hot.
- The **load-to-temperature relationship** — how steep it is, and whether it is straight.
- The **fleet comparison** — whether one unit runs hotter than the others.""",
    challenge="""The scatter of load against hot spot is not a line, and it is not even a single curve.

- It fans out. At the same load, the hot spot varies by 25 °C or more.
- The spread is caused by ambient temperature, cooling stage, and how long the unit has been at that load.
- No single variable explains it.

That fan is the reason this is a multi-input problem rather than a lookup table.""",
    ai_link="""Exploratory analysis decides what the model is allowed to be.

- If load alone explained the hot spot, a lookup table would do and no model would be needed.
- Because the relationship fans out, the model needs several inputs at once.
- The correlation matrix says which inputs are worth having, and which are near-copies of each other.""",
    bridge=[("A week of trend recordings", "A time-series plot"),
            ("Load against temperature", "A scatter plot"),
            ("Which sensors move together", "The correlation matrix")],
    body=[("co", r'''
wk = log[(log.unit_id == "T3") &
         (log.timestamp >= "2025-06-09") & (log.timestamp < "2025-06-16")]

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=wk.timestamp, y=wk.load_current_a, name="Load current (A)",
                         line=dict(color=CYAN, width=2)), secondary_y=True)
for col, colour, nm in [("ambient_temp_c", MUTED, "Ambient (°C)"),
                        ("oil_temp_c", AMBER, "Top oil (°C)"),
                        ("hotspot_temp_c", RED, "Hot spot (°C)")]:
    fig.add_trace(go.Scatter(x=wk.timestamp, y=wk[col], name=nm,
                             line=dict(color=colour, width=2)), secondary_y=False)
fig.update_yaxes(title_text="Temperature (°C)", secondary_y=False)
fig.update_yaxes(title_text="Load current (A)", secondary_y=True, showgrid=False)
fig.update_layout(title="T3, one week in June — load leads, oil follows, hot spot follows the winding",
                  height=430, template="plotly_white", hovermode="x unified")
fig.show()
'''),
           ("co", r'''
samp = log.dropna(subset=["hotspot_temp_c"]).sample(4000, random_state=1)
fig = px.scatter(samp, x="load_current_a", y="hotspot_temp_c", color="ambient_temp_c",
                 color_continuous_scale="Turbo", opacity=0.55,
                 labels={"load_current_a": "Load current (A)",
                         "hotspot_temp_c": "Hot-spot temperature (°C)",
                         "ambient_temp_c": "Ambient (°C)"},
                 title="Same load, 25 °C of spread — the missing variable is mostly ambient temperature")
fig.add_hline(y=110, line=dict(color=RED, dash="dash"),
              annotation_text="110 °C — normal life expectancy limit")
fig.update_layout(height=470, template="plotly_white")
fig.show()

num = log.select_dtypes("number").drop(columns=["transformer_age_years"])
print("Correlation with hot-spot temperature")
print(num.corr()["hotspot_temp_c"].drop("hotspot_temp_c").sort_values(ascending=False).round(3).to_string())
print()
band = log[(log.load_current_a.between(680, 720)) & log.hotspot_temp_c.notna()].hotspot_temp_c
print(f"At 680–720 A the hot spot ranges from {band.min():.0f} °C to {band.max():.0f} °C "
      f"({band.max() - band.min():.0f} °C of spread at essentially the same load).")
'''),
           ("co", r'''
per_unit = (log.dropna(subset=["hotspot_temp_c"])
              .groupby("unit_id")
              .agg(age=("transformer_age_years", "first"),
                   mean_load=("load_current_a", "mean"),
                   mean_hotspot=("hotspot_temp_c", "mean"),
                   peak_hotspot=("hotspot_temp_c", "max"),
                   hours_over_98=("hotspot_temp_c", lambda s: int((s > 98).sum())),
                   hours_over_110=("hotspot_temp_c", lambda s: int((s > 110).sum())),
                   hours_over_120=("hotspot_temp_c", lambda s: int((s > 120).sum())))
              .round(1))
print(per_unit.to_string())
print()
print(f"Fleet total: {int(per_unit.hours_over_98.sum()):,} hours above 98 °C, "
      f"{int(per_unit.hours_over_110.sum())} above 110 °C, "
      f"{int(per_unit.hours_over_120.sum())} above 120 °C.")
print()
print("T3 carries the most load and spends the most time above 110 °C.")
print("But note T4: older, less loaded than T3, and almost as many hours over 110 °C.")
'''),
    ],
    built="""Three views of the same year.

- **The week trend.** Load peaks in the evening; the oil lags it by hours; the hot spot tracks the winding
  almost immediately. That lag is a real thermal effect and it matters later.
- **The scatter.** Hold the load between 680 and 720 A and the hot spot still spans **36 °C**, from 75 °C
  to 110 °C, driven mostly by ambient temperature, cooling stage and which unit it is.
- **The fleet table.** Load current and oil temperature correlate almost equally with the hot spot — 0.91
  each. Neither is sufficient on its own, and step 15 shows why.""",
    takeaway="At one fixed load the hot spot still spans tens of degrees, which is exactly why one sensor is not enough.",
)


# --------------------------------------------- PHASE 4 - PREPARING THE DATA
step(
    id="clean", phase=3, icon="\U0001f9f9", ai_icon="✅",
    ee="Removing Invalid Readings", ai="Data Cleaning",
    tech="Filter, deduplicate, drop unusable rows",
    site="""Each fault found in step 8 gets a decision, and the decision is an engineering one.

| Fault | Decision | Reason |
|---|---|---|
| Duplicate rows | Remove | The historian exported them twice |
| `cooling_type` constant | Drop the column | One value tells the model nothing |
| Humidity = 255 % | Set to missing, then fill | The transmitter failed, the weather did not |
| Missing oil temperature | Interpolate over the gap | Oil moves slowly; an hour's gap is safe to bridge |
| Missing hot-spot reading | **Drop the row** | No label, no training example |
| Load current < 10 A | **Drop the row** | The unit was de-energised — different physics |
| Frozen ambient sensor | **Drop the block** | The readings are not measurements |""",
    challenge="""Two of those decisions are the ones that matter, and both are counter-intuitive.

- **Interpolating oil temperature is safe.** It has a three-hour time constant, so an hour's gap really is
  bridgeable. Interpolating *load current* would not be — it can double in an hour.
- **De-energised hours must be deleted, not repaired.** A cooling transformer obeys different physics from
  a loaded one. Keeping those rows teaches the model that low current means winding-at-ambient, and it will
  then under-predict every genuinely light-load hour.

The rule: interpolate what moves slowly, delete what is not a measurement of the thing you are modelling.""",
    ai_link="""Cleaning is where most of a model's real accuracy is won or lost.

- Every row left in the file is a statement to the model: *this is what normal looks like*.
- A hundred de-energised hours is a hundred statements that are wrong.
- The model has no way to know they are wrong. It will fit them.""",
    bridge=[("Removing an invalid reading", "Dropping a row"),
            ("A sensor that failed, not weather that changed", "Imputation"),
            ("Physics that does not apply", "Out-of-scope data")],
    body=[("co", r'''
clean = log.copy()
before = len(clean)
report = []

clean = clean.drop_duplicates()
report.append(("Duplicate rows removed", before - len(clean)))

const_cols = [c for c in clean.columns if clean[c].nunique(dropna=True) == 1]
clean = clean.drop(columns=const_cols)
report.append((f"Constant columns dropped {const_cols}", len(const_cols)))

n = (clean.humidity_pct > 100).sum()
clean.loc[clean.humidity_pct > 100, "humidity_pct"] = np.nan
report.append(("Impossible humidity set to missing", int(n)))

clean = clean.sort_values(["unit_id", "timestamp"]).reset_index(drop=True)

# frozen ambient sensor: a run of six or more identical readings is not weather
def frozen_run(s, min_len=6):
    "True for every reading inside a run of min_len or more identical consecutive values."
    block = (s != s.shift()).cumsum()
    return s.groupby(block).transform("size") >= min_len

frozen = clean.groupby("unit_id", sort=False).ambient_temp_c.transform(frozen_run)
n = int(frozen.sum()); clean = clean[~frozen]
report.append(("Frozen-ambient-sensor rows dropped", n))

n = int((clean.load_current_a < 10).sum())
clean = clean[clean.load_current_a >= 10]
report.append(("De-energised rows dropped", n))

# oil temperature and humidity move slowly - an hour's gap can be bridged
for col in ("oil_temp_c", "humidity_pct"):
    n = int(clean[col].isna().sum())
    clean[col] = clean.groupby("unit_id")[col].transform(
        lambda s: s.interpolate(limit=3).ffill().bfill())
    report.append((f"{col} gaps interpolated", n))

n = int(clean.hotspot_temp_c.isna().sum())
clean = clean.dropna(subset=["hotspot_temp_c"])
report.append(("Rows with no hot-spot label dropped", n))

clean = clean.reset_index(drop=True)
print(pd.DataFrame(report, columns=["Action", "Rows / columns"]).to_string(index=False))
print()
print(f"{before:,} rows in  ->  {len(clean):,} rows out  ({100*(before-len(clean))/before:.1f} % removed)")
print(f"Remaining missing values: {int(clean.isna().sum().sum())}")
''')],
    built="""A cleaning log, not just a clean file.

- Under **1 %** of the export was dropped, and a few hundred more readings were repaired in place.
- Every action is recorded with a count, so the decision can be audited later.
- Nothing was silently fixed. If a reviewer disagrees with the de-energised rule, they can find it.""",
    takeaway="Interpolate what moves slowly, delete what is not a measurement of the thing you are modelling.",
)

step(
    id="features", phase=3, icon="\U0001f527", ai_icon="\U0001f4a1",
    ee="Turning Readings Into Engineering Quantities", ai="Feature Engineering",
    tech="load_pu, load_pu^1.6, oil rise, ramps, 3 h rolling load",
    site="""A raw sensor reading is rarely the quantity an engineer reasons with.

- Nobody thinks in amps. They think in **per-unit load**, `K = I / I_rated`.
- Nobody compares oil temperatures across seasons. They compare **oil rise over ambient**.
- Nobody looks at one instant. They look at where the load has been for the **last few hours**.

Feature engineering is writing those conversions down.""",
    challenge="""Two of the new columns exist because of physics the raw sensors cannot express.

- **`load_pu_16` = K^1.6.** The winding gradient grows with `K^1.6`, from IEEE C57.91. A model given only
  `K` has to discover that exponent from data. Given `K^1.6` it does not have to.
- **`load_roll3` — the 3-hour mean load.** The oil has a three-hour time constant, and the thermometer
  pocket adds more lag. So the *measured* oil temperature describes the transformer as it was an hour or
  two ago. The recent load history is what fills that gap.

`load_roll3` turns out to be the single most important feature in the whole model. That is not obvious in
advance, and it is not a machine learning insight — it is a thermal one.""",
    ai_link="""Feature engineering is where domain knowledge enters a model.

- The algorithm can only combine the columns it is given.
- Give it `K^1.6` and a straight line can represent a power law.
- Give it a rolling mean and a model with no memory can see the recent past.

This is usually worth more than changing the algorithm. Step 20 measures both, side by side.""",
    bridge=[("Current in amps", "load_pu — per unit of rating"),
            ("The K^1.6 winding law", "load_pu_16 — the physics, as a column"),
            ("A three-hour oil time constant", "load_roll3 — the recent past")],
    body=[("co", r'''
df = clean.sort_values(["unit_id", "timestamp"]).reset_index(drop=True)
g  = df.groupby("unit_id", sort=False)

df["load_pu"]      = df.load_current_a / I_RATED          # per-unit load, K
df["volt_pu"]      = df.voltage_kv / V_RATED              # per-unit voltage
df["load_pu_16"]   = df.load_pu ** 1.6                    # IEEE C57.91 winding law, K^(2m)
df["oil_rise_c"]   = df.oil_temp_c - df.ambient_temp_c    # what the cooling system is achieving
df["oil_ramp_1h"]  = g.oil_temp_c.diff().fillna(0.0)      # is the oil still rising?
df["load_ramp_1h"] = g.load_pu.diff().fillna(0.0)         # has the load just stepped?
df["load_roll3"]   = g.load_pu.transform(lambda s: s.rolling(3, min_periods=1).mean())
df["hour"]         = df.timestamp.dt.hour                 # a weak proxy for sun on the tank

RAW_FEATURES = ["load_current_a", "ambient_temp_c", "oil_temp_c", "voltage_kv", "humidity_pct"]
ENG_FEATURES = RAW_FEATURES + ["cooling_stage", "transformer_age_years", "load_pu_16",
                               "oil_rise_c", "oil_ramp_1h", "load_ramp_1h", "load_roll3", "hour"]
TARGET = "hotspot_temp_c"

print(f"{len(RAW_FEATURES)} raw sensor columns  ->  {len(ENG_FEATURES)} columns after engineering")
print()
print(df[["load_pu", "load_pu_16", "oil_rise_c", "load_roll3", "load_ramp_1h"]].describe().T.round(3).to_string())
print()
print("Absolute correlation with the hot spot, all columns:")
cors = df[ENG_FEATURES + [TARGET]].corr()[TARGET].drop(TARGET).abs().sort_values(ascending=False)
print(cors.round(3).to_string())
''')],
    built="""Thirteen columns, of which eight did not exist in the export.

- `load_roll3` correlates with the hot spot about as strongly as the instantaneous current — and carries
  different information, because it describes the thermal state rather than the electrical one.
- `oil_rise_c` separates *how hard the transformer is working* from *how hot the day is*.
- `hour` is deliberately weak. It is a proxy for solar heating on the tank, and step 21 shows how little
  it earns.""",
    takeaway="Feature engineering is where the thermal standard enters the model — and it is usually worth more than changing the algorithm.",
)

step(
    id="scale", phase=3, icon="\U0001f4cf", ai_icon="\U0001f39a️",
    ee="Putting Quantities On A Common Scale", ai="Normalisation",
    tech="StandardScaler: z = (x − μ) / σ",
    site="""The columns are in wildly different units.

| Column | Typical range | Span |
|---|---|---|
| `load_current_a` | 240 – 980 | 740 |
| `voltage_kv` | 124 – 140 | 16 |
| `load_pu_16` | 0.1 – 1.7 | 1.6 |

Current is measured in hundreds. Per-unit load in fractions. Nothing about the physics says current is
four hundred times more important than per-unit load — but to an algorithm that measures distance, it is.""",
    challenge="""Only some algorithms care, and knowing which is the point.

- **Linear regression** with regularisation, and anything distance-based, are affected by scale.
- **Decision trees** are not. A tree splits on `load_current_a > 640`, and that split is identical whether
  the column is in amps or per unit.

So the same pipeline needs scaling on one branch and not on the other. Applying it everywhere is harmless;
not knowing why is not.""",
    ai_link="""Normalisation is not a cleaning step and it is not optional decoration.

- Fit the scaler on the **training set only**.
- Apply the same fitted scaler to the test set.
- Fitting it on everything leaks the test set's mean and standard deviation into training.

That last rule is the one people break.""",
    bridge=[("Amps, kilovolts, degrees, per-unit", "Features on different scales"),
            ("Converting to per-unit", "Standardisation"),
            ("Train first, then apply", "No leakage from the test set")],
    body=[("co", r'''
from sklearn.preprocessing import StandardScaler

demo = df[["load_current_a", "voltage_kv", "load_pu_16", "ambient_temp_c"]]
print("Before scaling")
print(demo.describe().T[["mean", "std", "min", "max"]].round(2).to_string())
print()
print("After scaling (mean 0, standard deviation 1)")
print(pd.DataFrame(StandardScaler().fit_transform(demo), columns=demo.columns)
        .describe().T[["mean", "std", "min", "max"]].round(2).to_string())
print()
print("Trees are unaffected: 'load_current_a > 640' and 'load_pu > 0.914' are the same split.")
print("The scaler is fitted in the next step - on the training rows only.")
''')],
    built="""The same four columns, before and after standardisation.

- After scaling every column has mean 0 and standard deviation 1.
- The *relationships* are untouched — only the units change.
- The scaler itself is not fitted here, because the training set has not been defined yet. That ordering
  is the whole point of the next step.""",
    takeaway="Scale the features linear models need scaled, fit the scaler on training data only, and know that trees do not care either way.",
)

step(
    id="split", phase=3, icon="✂️", ai_icon="\U0001f4d0",
    ee="Holding Back A Fair Test", ai="Train / Test Split",
    tech="Whole weeks held out, and why R² moves",
    site="""The model has to be scored on readings it has never seen. How you choose those readings is an
engineering decision.

Three options, all defensible, all giving different answers:

- **Random rows.** Simple, and it puts 2 p.m. Tuesday in training with 3 p.m. Tuesday in test.
- **Whole weeks.** Every fourth week held out. Seasons stay represented in both sets.
- **The last three months.** The strictest test: can a model trained on one part of the year work on
  another?""",
    challenge="""The third option exposes something that looks like a failure and is not.

Hold out October–December instead of every fourth week, and R² drops sharply — while the mean absolute
error barely moves.

The model did not get worse. The **test set** got narrower. Autumn has less temperature variation than a
full year, and R² is the fraction of the target's variance a model explains. Shrink that variance and R²
falls even when every prediction is exactly as accurate as before.

Both splits are fitted and scored in step 23, so this is measured rather than asserted. It is worth
internalising now: **R² is a property of the test set as much as of the model.**""",
    ai_link="""The choice made here is whole weeks, every fourth one.

- It prevents adjacent hours from sitting on both sides of the split.
- It keeps summer and winter in both sets, so the hot band is testable.
- It gives a 75 / 25 split without cherry-picking.

The pure-future split is run again in step 23, where there is a model to score with it.""",
    bridge=[("Holding back a fair test", "The test set"),
            ("Adjacent hours are nearly the same", "Blocked, not random, splitting"),
            ("A narrower test set", "R² falls without the model changing")],
    body=[("co", r'''
week = df.timestamp.dt.isocalendar().week.astype(int)
test_mask = (week % 4 == 0)                       # every fourth calendar week

X_train, X_test = df.loc[~test_mask, ENG_FEATURES], df.loc[test_mask, ENG_FEATURES]
y_train, y_test = df.loc[~test_mask, TARGET],       df.loc[test_mask, TARGET]

scaler = StandardScaler().fit(X_train)            # fitted on training rows ONLY
X_train_s, X_test_s = scaler.transform(X_train), scaler.transform(X_test)

print(f"Train {len(X_train):,} rows   Test {len(X_test):,} rows   ({100*test_mask.mean():.1f} % held out)")
print()
print("                       train    test")
print(f"  hot spot mean       {y_train.mean():6.2f}  {y_test.mean():6.2f}  °C")
print(f"  hot spot std dev    {y_train.std():6.2f}  {y_test.std():6.2f}  °C")
print(f"  hours above 110 °C  {int((y_train>110).sum()):6d}  {int((y_test>110).sum()):6d}")
print()
print("Both sets span the whole year, so the hot band is present in both. That matters in step 26.")
''')],
    built="""A held-out quarter of the year, chosen in whole weeks.

- **26,000 training rows, 8,700 test rows.**
- The test set contains hours above 110 °C, which a naive chronological split would have concentrated in
  one season.
- The scaler was fitted on training rows only. From here on, `X_test` is untouched until it is scored.""",
    takeaway="Split by whole weeks so adjacent hours cannot leak, and remember that R² depends on how wide the test set is.",
)


# ------------------------------------------- PHASE 5 - THE FIRST PREDICTION
step(
    id="baseline", phase=4, icon="\U0001f4dc", ai_icon="\U0001f4cf",
    ee="The Standard's Own Model", ai="The Baseline",
    tech="θ_h = θ_oil,measured + Δθ_h,r · K^1.6 · stage factor",
    site="""Before fitting anything, run the model the industry already uses.

IEEE C57.91, with nameplate values and the measured oil temperature:

`θ_hotspot = θ_oil + 24 · K^1.6 · (cooling stage factor)`

No fitting. No training data. Just the standard, the nameplate, and two readings.""",
    challenge="""It is a genuinely good model, and it is what every loading assessment in the industry is based
on. It also has no way to know:

- that T4's real hot-spot factor is 21 % above nameplate and T3's is 7 % below;
- that twenty-two years of radiator fouling has cost a few percent of cooling;
- that the oil thermometer is reading an hour behind the actual top oil.

Those are not errors in the standard. They are things the standard was never given.""",
    ai_link="""This is the number every later model must beat.

- Quoting an R² of 0.99 means nothing on its own.
- Quoting an R² of 0.99 **against a baseline that already achieves 0.95** is an engineering result.

A model that cannot beat the closed-form standard is not worth deploying, whatever its score looks like in
isolation.""",
    bridge=[("The IEEE C57.91 loading guide", "The baseline model"),
            ("Nameplate values", "Parameters that were never fitted"),
            ("Scored on the same held-out weeks", "A fair comparison")],
    body=[("co", r'''
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def score(y_true, y_pred, name):
    "MAE (°C), RMSE (°C) and R² for one model, as a dict."
    return {"Model": name,
            "MAE (°C)":  mean_absolute_error(y_true, y_pred),
            "RMSE (°C)": mean_squared_error(y_true, y_pred) ** 0.5,
            "R²":        r2_score(y_true, y_pred)}

results = []

# The standard, applied exactly as printed: nameplate gradient, measured oil.
stage_factor = df.cooling_stage.map(STAGE_HS).to_numpy()
ieee_pred_all = df.oil_temp_c.to_numpy() + DTH_R * df.load_pu.to_numpy()**1.6 * stage_factor
ieee_pred = ieee_pred_all[test_mask.to_numpy()]

results.append(score(y_test, ieee_pred, "IEEE C57.91 (nameplate, no fitting)"))
print(pd.DataFrame(results).round(3).to_string(index=False))
print()

print("Mean error per unit — the nameplate model assumes all four are identical:")
bias = ieee_pred - y_test.to_numpy()
for u in ["T1", "T2", "T3", "T4"]:
    m = (df.loc[test_mask, "unit_id"] == u).to_numpy()
    direction = "over-predicts" if bias[m].mean() > 0 else "under-predicts"
    print(f"  {u}: {bias[m].mean():+6.2f} °C   the standard {direction} this unit all year")
''')],
    built="""The baseline: **MAE 3.18 °C, R² 0.946**, with nothing fitted at all.

Look at the per-unit errors. They are not noise — they are **biases**, and they point in opposite
directions:

- The standard over-predicts on one unit and under-predicts on another, consistently, all year.
- That is the per-unit hot-spot factor, and it is exactly the information a fitted model can pick up.

A 3.18 °C average error may sound acceptable. At 110 °C, being 3 °C low understates the ageing rate by
about 27 %.""",
    takeaway="Beat the standard, not zero — a model that cannot outperform the closed-form thermal model is not worth deploying.",
)

step(
    id="linear", phase=4, icon="\U0001f4c9", ai_icon="\U0001f4d0",
    ee="A Straight Line Through The Data", ai="Linear Regression",
    tech="θ_h = w₀ + w₁·I + w₂·θ_a + w₃·θ_oil + w₄·V + w₅·RH",
    site="""The simplest possible fitted model: give each of the five raw sensors a weight, add them up.

The engineering reading of that is a **sensitivity coefficient per sensor**: how many degrees the hot spot
moves per amp of load, per degree of ambient, per degree of oil.

It is the most interpretable model there is. Every coefficient can be argued with.""",
    challenge="""It is fitted on the five raw sensors only, and it inherits every limitation of a straight
line.

- Heat rises with `K²` and the winding gradient with `K^1.6`. A line cannot bend.
- Cooling stages put steps in the curve. A line cannot step.
- Cold oil is more viscous, so ambient and load interact. A line cannot multiply two inputs together.

It will still beat the nameplate baseline, because it has at least been fitted to this fleet.""",
    ai_link="""Linear regression is the right first model, always.

- It is fast, it cannot overfit thirteen columns of thirty-five thousand rows, and its coefficients are
  readable.
- It establishes how much of the problem is genuinely simple.
- Anything more complicated now has to justify itself against it.""",
    bridge=[("Degrees of hot spot per amp", "A regression coefficient"),
            ("A sensitivity study", "Fitting the weights"),
            ("A relationship that bends", "What a line cannot represent")],
    body=[("co", r'''
from sklearn.linear_model import LinearRegression

# The five raw sensors, scaled, and nothing else.
Xtr_raw = df.loc[~test_mask, RAW_FEATURES]
Xte_raw = df.loc[test_mask,  RAW_FEATURES]
raw_scaler = StandardScaler().fit(Xtr_raw)

lin_raw = LinearRegression().fit(raw_scaler.transform(Xtr_raw), y_train)
pred_lin_raw = lin_raw.predict(raw_scaler.transform(Xte_raw))
results.append(score(y_test, pred_lin_raw, "Linear regression (5 raw sensors)"))

print("Coefficients, in °C of hot spot per standard deviation of the sensor:")
coefs = pd.Series(lin_raw.coef_, index=RAW_FEATURES).sort_values(key=abs, ascending=False)
print(coefs.round(3).to_string())
print()
print(pd.DataFrame(results).round(3).to_string(index=False))
'''),
           ("co", r'''
# And the same model given the engineered columns as well.
lin_eng = LinearRegression().fit(X_train_s, y_train)
pred_lin_eng = lin_eng.predict(X_test_s)
results.append(score(y_test, pred_lin_eng, "Linear regression (engineered)"))

print(pd.DataFrame(results).round(3).to_string(index=False))
print()
imp = pd.Series(lin_eng.coef_, index=ENG_FEATURES).sort_values(key=abs, ascending=False)
print("Largest coefficients after engineering:")
print(imp.head(6).round(3).to_string())
print()
print("The engineered columns alone cut the error by about 17 %, with the same algorithm.")
''')],
    built="""Two linear models, and the gap between them is the point.

- **Raw sensors: MAE 2.41 °C.** Already better than the nameplate standard's 3.18 °C, purely from having
  been fitted to this fleet.
- **Engineered columns: MAE 2.00 °C.** The algorithm did not change. `K^1.6` and the rolling load did.

The coefficients read as engineering. Load current comes first at **9.2 °C per standard deviation**, oil
temperature second at **7.3**, ambient a distant third. Humidity is near zero and voltage is **exactly
zero** — the model has decided those two sensors tell it nothing. That is a finding, not a disappointment,
and step 21 tests it properly.""",
    takeaway="A straight line already beats the nameplate model, because it has at least seen this fleet run.",
)

step(
    id="residuals", phase=4, icon="\U0001f50e", ai_icon="\U0001f4c9",
    ee="Where The Line Fails", ai="Residual Analysis",
    tech="error = predicted − measured, plotted against the inputs",
    site="""A residual is a prediction error. Plotting residuals against each input is the standard way to
find out what a model has missed.

The rule is simple: **residuals should look like noise.** If they show a pattern, the pattern is signal
the model failed to use.""",
    challenge="""The linear model's residuals are not noise.

- Plotted against load, they curve. The line under-predicts at low load and again at high load, because it
  is fitting a straight line through a `K^1.6` relationship.
- Grouped by cooling stage, they sit at different levels. The line has no way to step.

Both patterns are physics the model was given but could not represent.""",
    ai_link="""Residual analysis tells you **which kind** of model you need next.

- Curvature in the residuals means the relationship bends — so use a model that can bend.
- Level shifts by category mean interactions — so use a model that can split.

Tree ensembles do both, natively. That is why the next phase uses them, rather than because they are
fashionable.""",
    bridge=[("A systematic error, not scatter", "Structure in the residuals"),
            ("Under-prediction at high load", "Unmodelled curvature"),
            ("A step at each cooling stage", "An unmodelled interaction")],
    body=[("co", r'''
resid = pd.DataFrame({
    "load_pu":       df.loc[test_mask, "load_pu"].to_numpy(),
    "cooling_stage": df.loc[test_mask, "cooling_stage"].to_numpy(),
    "measured":      y_test.to_numpy(),
    "error":         pred_lin_raw - y_test.to_numpy(),
})

fig = make_subplots(rows=1, cols=2, subplot_titles=(
    "Residual against load — it curves, so the relationship bends",
    "Residual by cooling stage — it steps, so there is an interaction"))
binned = resid.groupby(pd.cut(resid.load_pu, 25), observed=True).agg(
    x=("load_pu", "mean"), e=("error", "mean")).dropna()
fig.add_trace(go.Scatter(x=resid.load_pu, y=resid.error, mode="markers",
                         marker=dict(size=3, color=MUTED, opacity=0.25),
                         name="every test hour"), row=1, col=1)
fig.add_trace(go.Scatter(x=binned.x, y=binned.e, mode="lines+markers",
                         line=dict(color=RED, width=3), name="mean error"), row=1, col=1)
for st, colour in zip([0, 1, 2], [CYAN, AMBER, RED]):
    fig.add_trace(go.Box(y=resid.loc[resid.cooling_stage == st, "error"],
                         name=f"stage {st}", marker_color=colour, boxpoints=False),
                  row=1, col=2)
fig.add_hline(y=0, line=dict(color="black", dash="dot"))
fig.update_yaxes(title_text="Prediction error (°C)", row=1, col=1)
fig.update_xaxes(title_text="Load (per unit)", row=1, col=1)
fig.update_layout(height=430, template="plotly_white", showlegend=False,
                  title="Linear model residuals are not noise")
fig.show()

print("Mean error by load band (linear model, raw sensors):")
for lo, hi in [(0.2, 0.5), (0.5, 0.7), (0.7, 0.9), (0.9, 1.1), (1.1, 1.5)]:
    m = (resid.load_pu >= lo) & (resid.load_pu < hi)
    if m.sum():
        print(f"  K {lo:.1f}–{hi:.1f}  n={int(m.sum()):5d}   mean error {resid.error[m].mean():+6.2f} °C")
print()
print("Mean error by cooling stage:")
for st in sorted(resid.cooling_stage.unique()):
    m = resid.cooling_stage == st
    print(f"  stage {st}  n={int(m.sum()):5d}   mean error {resid.error[m].mean():+6.2f} °C")
''')],
    built="""Two diagnostic plots, and both show structure.

- The mean error **swings across the loading range** instead of sitting on zero. That is the `K^1.6` curve
  the line could not follow.
- The error **differs by cooling stage**. That is an interaction: the effect of load on the hot spot
  depends on whether the fans are running.

Neither is a tuning problem. A straight line cannot fix either of them, no matter how it is fitted.""",
    takeaway="Structure in the residuals tells you what kind of model to reach for next — curvature means bend, steps mean split.",
)


# ------------------------------------------------ PHASE 6 - MODELS THAT BEND
step(
    id="forest", phase=5, icon="\U0001f333", ai_icon="\U0001f333",
    ee="Many Small Rules Instead Of One Equation", ai="Random Forest Regressor",
    tech="300 trees, each on a different sample and subset of columns",
    site="""An experienced engineer does not carry one equation. They carry rules.

- *Above 0.9 per unit with fans at stage 1, add about ten degrees.*
- *On a cold morning the gradient runs a little higher than the tables say.*
- *T4 always sits a couple of degrees above its sisters.*

A decision tree is that, written down: a chain of thresholds ending in a number.""",
    challenge="""One tree memorises. Ask it about an hour it has seen and it is perfect; ask about a new
one and it is brittle.

A random forest fixes that by disagreement:

- Build 300 trees, each on a different random sample of the rows.
- At each split, let each tree choose from a random subset of the columns.
- Average the 300 answers.

No tree sees the whole picture, so no tree can memorise it. The average is stable.""",
    ai_link="""Trees solve exactly the two problems the residuals exposed.

- A tree approximates a curve with steps, so `K^1.6` is no longer a problem.
- A tree splits on cooling stage and then splits differently on load underneath it — that is an
  interaction, for free.

They also need no scaling, which is why `X_train` is passed unscaled below.""",
    bridge=[("A rule of thumb with a threshold", "A decision tree split"),
            ("Asking several engineers", "An ensemble"),
            ("Averaging their answers", "Bagging")],
    body=[("co", r'''
from sklearn.ensemble import RandomForestRegressor

rf = RandomForestRegressor(n_estimators=300, min_samples_leaf=2,
                           n_jobs=-1, random_state=42).fit(X_train, y_train)
pred_rf = rf.predict(X_test)
results.append(score(y_test, pred_rf, "Random Forest (300 trees)"))

print(pd.DataFrame(results).round(3).to_string(index=False))
print()
print(f"Trees in the forest:       {len(rf.estimators_)}")
print(f"Mean depth of a tree:      {np.mean([t.get_depth() for t in rf.estimators_]):.1f}")
print(f"Mean leaves per tree:      {np.mean([t.get_n_leaves() for t in rf.estimators_]):,.0f}")
print()
print("One example rule, from the first three splits of tree 0:")
t0 = rf.estimators_[0].tree_
for node in (0, t0.children_left[0], t0.children_left[t0.children_left[0]]):
    if t0.children_left[node] != -1:
        print(f"  if {ENG_FEATURES[t0.feature[node]]} <= {t0.threshold[node]:.2f}")
''')],
    built="""**MAE 1.53 °C** — a 24 % improvement on the best linear model, on the same columns.

- The forest fixed the curvature and the cooling-stage steps without being told they existed.
- It needed no scaling and no feature selection.
- Its trees are deep and there are 300 of them, so it is no longer a model you can read as an equation.
  Step 21 recovers some of that interpretability.""",
    takeaway="A forest of disagreeing trees handles curvature and interactions natively — which is exactly what the residuals asked for.",
)

step(
    id="boosting", phase=5, icon="\U0001f4c8", ai_icon="\U0001f501",
    ee="Correcting The Previous Attempt", ai="Gradient Boosting Regressor",
    tech="300 shallow trees, each fitted to what is left over",
    site="""A commissioning engineer does not start from scratch after each test. They take the previous
result and correct it.

Gradient boosting is that loop:

1. Make a rough prediction.
2. Measure what is left over — the residual.
3. Fit a small tree to the residual.
4. Add a fraction of it to the prediction.
5. Repeat, 300 times.

Each tree is deliberately weak. The sequence is strong.""",
    challenge="""The difference from a forest is the direction of the work.

- A **forest** builds 300 independent trees and averages them. Errors cancel.
- **Boosting** builds 300 dependent trees, each aimed at the previous mistake. Errors are attacked.

Boosting reaches a lower error on structured tabular data like this. It also takes far longer to fit,
because the trees cannot be built in parallel — each one needs the one before it.""",
    ai_link="""Two settings control it, and both are engineering trade-offs.

- **Learning rate (0.06).** How much of each correction to accept. Small means slow and stable.
- **Number of trees (300).** Too few and it has not finished correcting; too many and it starts fitting
  the noise.

The two trade against each other: halve the learning rate and you need roughly twice the trees.""",
    bridge=[("Correcting the previous result", "Fitting the residual"),
            ("Small, cautious adjustments", "The learning rate"),
            ("Repeating until it settles", "The number of estimators")],
    body=[("md", """> **This is the slowest cell in the notebook** — around 30–60 seconds. The trees are built one after
> another, which is exactly why the next step exists."""),
           ("co", r'''
from sklearn.ensemble import GradientBoostingRegressor
import time

t0 = time.time()
gb = GradientBoostingRegressor(n_estimators=300, learning_rate=0.06, max_depth=4,
                               subsample=0.8, random_state=42).fit(X_train, y_train)
gb_seconds = time.time() - t0
pred_gb = gb.predict(X_test)
results.append(score(y_test, pred_gb, "Gradient Boosting (300 trees)"))

print(pd.DataFrame(results).round(3).to_string(index=False))
print()
print(f"Fitted in {gb_seconds:.1f} seconds.")
print()

# What the sequence of corrections actually looks like.
stages = np.array([mean_absolute_error(y_test, p) for p in gb.staged_predict(X_test)])
fig = go.Figure(go.Scatter(x=np.arange(1, len(stages) + 1), y=stages,
                           line=dict(color=AMBER, width=3), name="test MAE"))
fig.add_hline(y=results[2]["MAE (°C)"], line=dict(color=MUTED, dash="dash"),
              annotation_text="linear regression, engineered")
fig.add_hline(y=results[3]["MAE (°C)"], line=dict(color=CYAN, dash="dash"),
              annotation_text="random forest")
fig.update_layout(title="Each tree corrects the one before it",
                  xaxis_title="Trees added", yaxis_title="Test MAE (°C)",
                  height=400, template="plotly_white")
fig.show()

for n in (25, 50, 100, 200, 300):
    print(f"After {n:3d} trees: MAE {stages[n-1]:.2f} °C")
print()
for label, target in [("linear regression (engineered)", results[2]["MAE (°C)"]),
                      ("the random forest", results[3]["MAE (°C)"])]:
    passed = np.argmax(stages < target) + 1
    print(f"  passes {label:30s} after {passed:3d} trees")
print()
print(f"Over the last 50 trees the test error still fell, {stages[-51]:.4f} -> {stages[-1]:.4f} °C.")
print("It is flattening, not turning upwards, so this is not yet overfitting - more trees")
print("would help slightly, and the argument for stopping here is fitting time, not accuracy.")
''')],
    built="""**MAE 1.35 °C**, the best result so far.

The curve is the useful part:

- The first few dozen trees are **worse than the linear model** — boosting starts from a crude guess and
  works towards the answer, so an early stop would have been a disaster.
- It passes the linear model at about **50** trees and the random forest at about **90**.
- It is still improving at 300, so it is not yet overfitting. The reason to stop is fitting time.

The cost is time. This one cell takes longer than every other model in the notebook combined.""",
    takeaway="Boosting attacks its own errors one tree at a time, and beats the forest on tabular data — at the cost of a fit that cannot be parallelised.",
)

step(
    id="xgboost", phase=5, icon="⚡", ai_icon="\U0001f680",
    ee="The Same Answer, Fast Enough To Retrain", ai="XGBoost Regressor",
    tech="600 trees, histogram splits, parallel and regularised",
    site="""A condition-monitoring model is not fitted once. It is refitted as the fleet changes — new units,
new probes, a year of fresh readings, a retap.

If refitting takes an hour, it happens annually. If it takes two seconds, it happens whenever the data
changes.

That is an operational property, and it is worth as much as accuracy.""",
    challenge="""XGBoost is gradient boosting with the implementation problems solved.

- **Histogram splits.** Continuous columns are bucketed once, so each split is a fast lookup instead of a
  full sort.
- **Parallel and cache-aware.** It uses every core on the machine.
- **Built-in regularisation.** Explicit penalties on tree complexity, so more trees is safer.

Same algorithm. Same answer. **One to two orders of magnitude faster**, depending on the machine.""",
    ai_link="""The comparison below is the point of this step, and it is not about accuracy.

- Gradient boosting and XGBoost land within 0.01 °C of each other.
- One takes tens of seconds. The other takes about one.

When two models are equally accurate, choose on the properties that are not accuracy: fit time, memory,
how easily it is deployed, and whether anyone can retrain it without booking an afternoon.""",
    bridge=[("Refitting when the fleet changes", "Training time as a requirement"),
            ("The same physics, computed faster", "An optimised implementation"),
            ("Choosing between equal models", "Non-accuracy criteria")],
    body=[("co", r'''
try:
    from xgboost import XGBRegressor
    HAVE_XGB = True
except ImportError:                       # not installed in this environment
    HAVE_XGB = False
    print("xgboost not installed - run:  !pip install xgboost")

if HAVE_XGB:
    t0 = time.time()
    xgb = XGBRegressor(n_estimators=600, learning_rate=0.05, max_depth=6,
                       subsample=0.9, colsample_bytree=0.9,
                       random_state=42, n_jobs=-1).fit(X_train, y_train)
    xgb_seconds = time.time() - t0
    pred_xgb = xgb.predict(X_test)
    results.append(score(y_test, pred_xgb, "XGBoost (600 trees)"))

    print(pd.DataFrame(results).round(3).to_string(index=False))
    print()
    print(f"Gradient Boosting : {gb_seconds:6.1f} s   MAE {results[4]['MAE (°C)']:.2f} °C")
    print(f"XGBoost           : {xgb_seconds:6.1f} s   MAE {results[5]['MAE (°C)']:.2f} °C")
    print(f"                    {gb_seconds/xgb_seconds:.0f}× faster, for the same accuracy.")
    best_model, best_pred, best_name = xgb, pred_xgb, "XGBoost"
else:
    best_model, best_pred, best_name = gb, pred_gb, "Gradient Boosting"

print()
print(f"Model carried forward into the dashboard: {best_name}")
''')],
    built="""Two models, indistinguishable on accuracy, and far apart on fit time.

- **MAE 1.35 °C** for both, agreeing to three decimal places.
- The fit time differs by roughly an order of magnitude on the same data and the same machine.

That is the model carried into the dashboard. The cell falls back to gradient boosting if XGBoost is not
installed, so nothing downstream depends on it being available.""",
    takeaway="When two models are equally accurate, pick on fit time and deployability — those are engineering criteria too.",
)

step(
    id="leaderboard", phase=5, icon="\U0001f3c1", ai_icon="\U0001f4ca",
    ee="Which Model Goes Into Service", ai="Model Comparison",
    tech="Six models, one held-out quarter of the year",
    site="""Every model so far, on the same held-out weeks, scored the same way.

The comparison answers two separate questions, and they should not be confused:

- **Does machine learning beat the standard's thermal model?**
- **Does the choice of algorithm matter as much as the choice of features?**""",
    challenge="""The second answer is the surprising one.

- Nameplate standard → fitted straight line: **3.18 → 2.41 °C**. That is the value of having seen the fleet.
- Raw sensors → engineered columns, same algorithm: **2.41 → 2.00 °C**.
- Linear → gradient boosting, same columns: **2.00 → 1.35 °C**.

Both levers are real, and they are roughly comparable in size. A great deal of published effort goes into
the third one and rather less into the second.""",
    ai_link="""Read the table as an engineer, not as a scoreboard.

- The **total** improvement is 3.18 °C to 1.35 °C — a 58 % reduction in mean error against the model the
  industry currently uses.
- At 110 °C, that is the difference between understating the ageing rate by roughly 27 % and by roughly
  13 %.

That is the result worth reporting. Every R² in the table is above 0.94, which is precisely why R² is a
poor way to choose between them.""",
    bridge=[("Choosing plant for service", "Model selection"),
            ("The same test for every candidate", "A held-out set"),
            ("Deciding what 'good enough' is", "An engineering threshold")],
    body=[("co", r'''
board = pd.DataFrame(results).sort_values("MAE (°C)").reset_index(drop=True)
board["vs standard"] = (100 * (1 - board["MAE (°C)"] / results[0]["MAE (°C)"])).round(0).astype(int).astype(str) + " %"
print(board.round(3).to_string(index=False))
print()

fig = go.Figure()
fig.add_trace(go.Bar(x=board["Model"], y=board["MAE (°C)"],
                     marker_color=[GREEN if m < 1.6 else AMBER if m < 2.2 else RED
                                   for m in board["MAE (°C)"]],
                     text=board["MAE (°C)"].round(2), textposition="outside"))
fig.add_hline(y=results[0]["MAE (°C)"], line=dict(color=RED, dash="dash"),
              annotation_text="IEEE C57.91 nameplate model — the number to beat")
fig.update_layout(title="Mean absolute error on the held-out weeks (lower is better)",
                  yaxis_title="MAE (°C)", height=460, template="plotly_white",
                  xaxis_tickangle=-20, margin=dict(b=140))
fig.show()

print("Two separate levers, measured:")
print(f"  fitting to this fleet at all : {results[0]['MAE (°C)'] - results[1]['MAE (°C)']:.2f} °C")
print(f"  engineering the features     : {results[1]['MAE (°C)'] - results[2]['MAE (°C)']:.2f} °C")
print(f"  changing the algorithm       : {results[2]['MAE (°C)'] - board['MAE (°C)'].min():.2f} °C")
''')],
    built="""The leaderboard, against a baseline rather than against zero.

- Best model: **1.35 °C mean absolute error**, down from **3.18 °C** for the nameplate standard.
- Every fitted model beats the standard. Even the straight line does, by 24 %.
- The three levers — fit at all, engineer the features, change the algorithm — contribute **0.77, 0.41 and
  0.66 °C**. None of them dominates, and the middle one costs nothing but domain knowledge.""",
    takeaway="Machine learning cut the hot-spot error by 58 % against the industry-standard thermal model, and feature engineering delivered nearly as much of that as the algorithm did.",
)


# ---------------------------------------------- PHASE 7 - READING THE MODEL
step(
    id="importance", phase=6, icon="\U0001f4cb", ai_icon="\U0001f50e",
    ee="Which Sensors Are Earning Their Place", ai="Feature Importance",
    tech="Split-based importance, then drop-and-remeasure",
    site="""A condition-monitoring scheme costs money per sensor: the instrument, the cabling, the telemetry
channel, and the calibration for the rest of the transformer's life.

So the question is not academic. **Which of these measurements is actually contributing to the answer?**""",
    challenge="""Two of the five sensors specified for this scheme contribute almost nothing.

- **Humidity** ranks near the bottom. Ambient humidity has a negligible effect on oil-to-air heat transfer.
  What little it contributes is as a proxy for cloud cover.
- **Voltage** ranks near the bottom too. It only moves core loss, which is one seventh of total loss, and
  it only varies by ±5 %.

That is not a failure of the model. It is the model reporting a genuine result about the plant — and it is
worth knowing before the next scheme is specified.""",
    ai_link="""Importance rankings need care in how they are read, and there are two traps.

- **Two models rank the same columns differently.** The ranking describes how one model carved up the
  information, not what the transformer is doing.
- **Removing one column proves nothing**, because the columns are redundant by construction. Drop
  `oil_temp_c` and the model rebuilds it from `oil_rise_c` plus `ambient_temp_c`.

So the test that matters is: **remove every column derived from an instrument, refit, and measure.** That
is a question about the monitoring scheme, and it has an answer in degrees.""",
    bridge=[("Justifying a sensor's cost", "Feature importance"),
            ("Removing an instrument entirely", "Dropping a group of features"),
            ("Two columns from one sensor", "Redundant features")],
    body=[("co", r'''
# Two models, the same columns, two different rankings.
ranks = pd.DataFrame({
    best_name: pd.Series(best_model.feature_importances_, index=ENG_FEATURES),
    "Random Forest": pd.Series(rf.feature_importances_, index=ENG_FEATURES),
}).sort_values(best_name)

fig = go.Figure()
fig.add_trace(go.Bar(x=ranks[best_name], y=ranks.index, orientation="h",
                     name=best_name, marker_color=CYAN))
fig.add_trace(go.Bar(x=ranks["Random Forest"], y=ranks.index, orientation="h",
                     name="Random Forest", marker_color=AMBER))
fig.update_layout(title="Which columns each model leans on — the two do not agree",
                  xaxis_title="Relative importance", height=560, template="plotly_white",
                  barmode="group", legend=dict(orientation="h", y=1.06))
fig.show()

print(ranks.sort_values(best_name, ascending=False).round(4).to_string())
print()
print(f"{best_name} puts '{ranks[best_name].idxmax()}' first; "
      f"the forest puts '{ranks['Random Forest'].idxmax()}' first.")
print("Same data, same columns, different answer. Neither ranking is the truth about the plant -")
print("they describe how each model happened to carve up the same information.")
'''),
           ("co", r'''
# The ranking suggests. Removing the column and refitting decides.
def refit_without(cols):
    feats = [c for c in ENG_FEATURES if c not in cols]
    m = GradientBoostingRegressor(n_estimators=300, learning_rate=0.06, max_depth=4,
                                  subsample=0.8, random_state=42
                                  ).fit(df.loc[~test_mask, feats], y_train)
    return mean_absolute_error(y_test, m.predict(df.loc[test_mask, feats])), len(feats)

base_mae, _ = refit_without([])
print(f"Baseline, all {len(ENG_FEATURES)} columns: MAE {base_mae:.3f} °C")
print()
print("Dropping ONE column at a time:")
for drop in (["humidity_pct"], ["voltage_kv"], ["humidity_pct", "voltage_kv"],
             ["load_roll3"], ["oil_temp_c"], ["cooling_stage"]):
    mae, n = refit_without(drop)
    print(f"  without {str(drop):36s} MAE {mae:.3f} °C  ({mae - base_mae:+.3f})")
print()
print("Almost nothing changes - even removing the top-ranked column. The columns are")
print("redundant: oil_rise_c reconstructs oil_temp_c, load_pu_16 reconstructs load_roll3.")
print("To find out whether an INSTRUMENT matters, remove everything derived from it.")
print()
print("Dropping a whole instrument:")
instruments = {
    "the humidity sensor":     ["humidity_pct"],
    "the voltage transformer": ["voltage_kv"],
    "the fan status contacts": ["cooling_stage"],
    "the oil thermometer":     ["oil_temp_c", "oil_rise_c", "oil_ramp_1h"],
    "the current transformer": ["load_current_a", "load_pu_16", "load_roll3", "load_ramp_1h"],
}
for label, cols in instruments.items():
    mae, n = refit_without(cols)
    print(f"  without {label:26s} MAE {mae:.3f} °C  ({mae - base_mae:+.3f})  {n} columns left")
print()
print("That is the ranking that means something to a condition-monitoring scheme.")
''')],
    built="""The ranking, the disagreement, and then the test that actually answers the question.

- **The two models rank the columns differently.** XGBoost leans hardest on `cooling_stage`; the forest
  leans on `load_roll3` and `oil_temp_c`. Both are equally accurate. A ranking describes how one model
  carved up the information, not what the transformer is doing.
- **Dropping any single column barely moves the error** — even the top-ranked one. The thirteen columns
  encode the same physics several times over.
- **Dropping a whole instrument is the meaningful test**, and it separates the sensors cleanly:

| Instrument removed | MAE | Penalty |
|---|---|---|
| Humidity sensor | 1.361 °C | +0.013 |
| Voltage transformer | 1.354 °C | +0.006 |
| Fan status contacts | 1.357 °C | +0.009 |
| **Top-oil thermometer** | 1.608 °C | **+0.260** |
| **Current transformer** | 2.350 °C | **+1.001** |

That is the ranking to put in front of whoever is paying for the instrumentation. Two of the five specified
sensors contribute nothing the model can use; the current transformer alone carries three quarters of a
degree.""",
    takeaway="Importance rankings disagree between models and hide redundancy — to find out whether an instrument earns its place, remove everything derived from it and refit.",
)

step(
    id="sensitivity", phase=6, icon="\U0001f39b️", ai_icon="\U0001f4c8",
    ee="How The Prediction Responds", ai="Sensitivity Analysis",
    tech="Vary one input, hold the rest, plot the response",
    site="""An engineer trusts a model by pushing it, not by reading its score.

Take a realistic operating point. Move one input at a time. Check that the response is the shape the
physics says it should be:

- More load must mean a hotter winding, and the curve must **steepen**.
- Hotter ambient must shift the whole curve up, roughly one-for-one.
- Starting the fans must produce a **step down**, not a smooth slope.""",
    challenge="""A model can score well on average and still be wrong in a way that matters.

- If it flattens above 1.2 per unit, it will under-predict every overload — the only hours anybody cares
  about.
- If it responds to ambient with a slope of 0.3 instead of about 1.0, it will fail in a heatwave.

Average error will not reveal either. The sensitivity plot will.""",
    ai_link="""This is also how the model gets explained to somebody who will not read a confusion matrix.

- A curve of predicted hot spot against load, at three ambient temperatures, is a **loading chart**.
- Engineers have used loading charts for a century.

The model has produced a familiar artefact. That is what makes it usable.""",
    bridge=[("A commissioning sensitivity test", "One-at-a-time analysis"),
            ("A transformer loading chart", "The model's response surface"),
            ("Checking against the physics", "Sanity-checking a model")],
    body=[("co", r'''
def operating_point(load_a, ambient_c, oil_c, volt_kv=132.0, humidity=60.0,
                    stage=None, age=16, hour=15, roll3=None):
    "One row of features from a set of readings, for asking the model a question."
    K = load_a / I_RATED
    if stage is None:                       # the fan controller's own logic
        stage = 2 if (oil_c > 68 or K > 0.92) else (1 if (oil_c > 55 or K > 0.70) else 0)
    return pd.DataFrame([{
        "load_current_a": load_a, "ambient_temp_c": ambient_c, "oil_temp_c": oil_c,
        "voltage_kv": volt_kv, "humidity_pct": humidity, "cooling_stage": stage,
        "transformer_age_years": age, "load_pu_16": K**1.6,
        "oil_rise_c": oil_c - ambient_c, "oil_ramp_1h": 0.0, "load_ramp_1h": 0.0,
        "load_roll3": K if roll3 is None else roll3, "hour": hour,
    }])[ENG_FEATURES]

fig = make_subplots(rows=1, cols=2, subplot_titles=(
    "Response to load, at three ambient temperatures",
    "Response to ambient temperature, at 700 A"))

loads = np.arange(300, 960, 10)
for amb, colour in [(15, CYAN), (30, AMBER), (42, RED)]:
    # top oil follows the load through the standard's own model, as it would in service
    oils = amb + top_oil_rise(loads / I_RATED, 1.0, 2, 16)
    p = [best_model.predict(operating_point(l, amb, o))[0] for l, o in zip(loads, oils)]
    fig.add_trace(go.Scatter(x=loads, y=p, name=f"ambient {amb} °C",
                             line=dict(color=colour, width=3)), row=1, col=1)

ambs = np.arange(5, 48, 1)
oils = ambs + top_oil_rise(700 / I_RATED, 1.0, 2, 16)
p = [best_model.predict(operating_point(700, a, o))[0] for a, o in zip(ambs, oils)]
fig.add_trace(go.Scatter(x=ambs, y=p, name="700 A", line=dict(color=GREEN, width=3)), row=1, col=2)

for c in (1, 2):
    fig.add_hline(y=110, line=dict(color=RED, dash="dash"), row=1, col=c)
fig.update_xaxes(title_text="Load current (A)", row=1, col=1)
fig.update_xaxes(title_text="Ambient temperature (°C)", row=1, col=2)
fig.update_yaxes(title_text="Predicted hot spot (°C)")
fig.update_layout(height=440, template="plotly_white",
                  title="Sensitivity: the model reproduced the transformer loading chart")
fig.show()

print("Checks against the physics:")
lo = best_model.predict(operating_point(400, 30, 30 + top_oil_rise(400/I_RATED, 1, 2, 16)))[0]
mid = best_model.predict(operating_point(700, 30, 30 + top_oil_rise(700/I_RATED, 1, 2, 16)))[0]
hi = best_model.predict(operating_point(900, 30, 30 + top_oil_rise(900/I_RATED, 1, 2, 16)))[0]
print(f"  400 -> 700 A at 30 °C ambient : +{mid-lo:5.1f} °C  ({(mid-lo)/300*100:.2f} °C per 100 A)")
print(f"  700 -> 900 A at 30 °C ambient : +{hi-mid:5.1f} °C  ({(hi-mid)/200*100:.2f} °C per 100 A)")
print("  The second 100 A costs more than the first. The curve steepens, as K^1.6 requires.")
print()
a1 = best_model.predict(operating_point(700, 15, 15 + top_oil_rise(1.0, 1, 2, 16)))[0]
a2 = best_model.predict(operating_point(700, 35, 35 + top_oil_rise(1.0, 1, 2, 16)))[0]
print(f"  +20 °C of ambient at 700 A    : +{a2-a1:5.1f} °C  (slope {(a2-a1)/20:.2f} — cooling is to ambient)")
''')],
    built="""A loading chart, produced by a machine learning model.

- The load curves **steepen**, as `K^1.6` requires. The second 100 A costs 18 °C per 100 A against 11 °C
  for the first.
- Ambient shifts the curves up with a slope of **0.88** — close to one-for-one, which is correct, because
  the transformer cools to ambient and every degree of air temperature is a degree the oil cannot lose.
- The 110 °C line shows where each ambient condition runs out of headroom.

Nothing in the model was told any of this. It came out of the data, and it agrees with the standard.""",
    takeaway="Push the model one input at a time and check it against the physics — a good score is not the same as a correct response.",
)


# ------------------------------------- PHASE 8 - THE MONITORING DASHBOARD
step(
    id="metrics", phase=7, icon="\U0001f4d0", ai_icon="\U0001f9ee",
    ee="Stating The Accuracy", ai="MAE, RMSE and R²",
    tech="Three numbers, and what each one hides",
    site="""An accuracy claim on a monitoring scheme has to survive a design review. Three numbers are
normally quoted, and they answer different questions.

| Metric | Question it answers | Units |
|---|---|---|
| **MAE** | How wrong is a typical prediction? | °C |
| **RMSE** | How wrong are the worst predictions? | °C |
| **R²** | What fraction of the variation is explained? | none |

RMSE exceeds MAE whenever errors are unevenly sized. The ratio is a warning sign in itself.""",
    challenge="""R² is the one that gets misread, and the pure-future split proves it.

- Score on every fourth week: **R² 0.991**.
- Score on October to December: **R² 0.978**.
- Mean absolute error in both cases: about **1.35 °C**.

The predictions are equally good. R² fell because autumn's hot-spot temperatures vary less than the full
year's, and R² is measured against that variation.

**Quote MAE in °C to an engineer.** Quote R² only alongside the standard deviation of the test set.""",
    ai_link="""Choose the metric that matches the decision.

- The decision here is *how close is the winding to 110 °C*. That is a question in degrees, so **MAE and
  RMSE are the operative metrics** and R² is context.
- If the decision were *rank the fleet by risk*, a correlation measure would be the right one instead.

The metric is part of the engineering specification, not an afterthought.""",
    bridge=[("A stated measurement accuracy", "MAE in °C"),
            ("Worst-case error", "RMSE"),
            ("A dimensionless score", "R², and its dependence on the test set")],
    body=[("co", r'''
mae  = mean_absolute_error(y_test, best_pred)
rmse = mean_squared_error(y_test, best_pred) ** 0.5
r2   = r2_score(y_test, best_pred)

print(f"{best_name} on {len(y_test):,} held-out hours")
print(f"  MAE   {mae:5.2f} °C   half of all predictions are within {np.median(np.abs(best_pred - y_test)):.2f} °C")
print(f"  RMSE  {rmse:5.2f} °C   ratio to MAE {rmse/mae:.2f} — errors are fairly evenly sized")
print(f"  R²    {r2:6.4f}   on a test set with standard deviation {y_test.std():.2f} °C")
print(f"  95 % of errors fall within ±{np.percentile(np.abs(best_pred - y_test), 95):.2f} °C")
print()

# The same model, scored on a pure-future split instead. R2 moves; MAE does not.
future = df.timestamp >= "2025-10-01"
fut = GradientBoostingRegressor(n_estimators=300, learning_rate=0.06, max_depth=4,
                                subsample=0.8, random_state=42
                                ).fit(df.loc[~future, ENG_FEATURES], df.loc[~future, TARGET])
fp, fy = fut.predict(df.loc[future, ENG_FEATURES]), df.loc[future, TARGET]

comparison = pd.DataFrame([
    {"Test set": "Every 4th week (all seasons)", "n": int(test_mask.sum()),
     "y std dev (°C)": y_test.std(), "MAE (°C)": mean_absolute_error(y_test, pred_gb),
     "R²": r2_score(y_test, pred_gb)},
    {"Test set": "October–December only", "n": int(future.sum()),
     "y std dev (°C)": fy.std(), "MAE (°C)": mean_absolute_error(fy, fp),
     "R²": r2_score(fy, fp)},
])
print(comparison.round(3).to_string(index=False))
print()
print("Same accuracy in degrees. Different R², because the second test set is narrower.")
''')],
    built="""Three numbers, and the demonstration that one of them moves for reasons that have nothing to do
with the model.

- **MAE 1.35 °C.** This is the number to put in a specification.
- **RMSE 1.69 °C.** The ratio to MAE is 1.25, so there is no small group of catastrophic errors. 95 % of
  hours land within ±3.3 °C.
- **R² 0.991** on the seasonal split against **0.978** on the autumn-only split — while MAE moves from
  1.35 °C to 1.37 °C. The test set's standard deviation fell from 17.4 °C to 11.5 °C, and that is the
  entire explanation.""",
    takeaway="Quote the error in degrees; R² changes when the test set changes even though the model has not.",
)

step(
    id="errors", phase=7, icon="\U0001f4c8", ai_icon="\U0001f4ca",
    ee="The Shape Of The Error", ai="Error Distribution",
    tech="Predicted against measured, and the residual histogram",
    site="""A single accuracy figure hides the shape. Two plots are standard on any monitoring
commissioning report.

- **Predicted against measured.** Points should sit on the 45° line. Departures show where.
- **The error histogram.** It should be centred on zero and symmetric.

A systematic offset means the model is biased. A long tail on one side means it fails in one direction.""",
    challenge="""For a thermal model, the direction of the error is not symmetric in consequence.

- Predicting **too high** costs money. Loading is restricted that did not need to be.
- Predicting **too low** costs insulation life, silently, and nobody finds out for years.

So a histogram centred on zero is necessary but not sufficient. It has to be centred on zero **in the hot
band as well**, which is what the next step checks.""",
    ai_link="""These two plots are how a model gets accepted or rejected in a review.

- A score is a claim. A predicted-against-measured plot is evidence.
- Anyone can read it, including people who will never read the code.

Plot it before quoting the metric, not after.""",
    bridge=[("A calibration check", "Predicted against measured"),
            ("Instrument bias", "A non-zero mean error"),
            ("A one-sided failure", "A skewed residual distribution")],
    body=[("co", r'''
err = best_pred - y_test.to_numpy()

fig = make_subplots(rows=1, cols=2, column_widths=[0.55, 0.45], subplot_titles=(
    "Predicted against measured hot-spot temperature", "Distribution of the error"))
fig.add_trace(go.Scattergl(x=y_test, y=best_pred, mode="markers",
                           marker=dict(size=3, color=CYAN, opacity=0.25), name="test hours"),
              row=1, col=1)
lims = [y_test.min() - 2, y_test.max() + 2]
fig.add_trace(go.Scatter(x=lims, y=lims, mode="lines",
                         line=dict(color="black", dash="dash"), name="perfect"), row=1, col=1)
for lim in (110, 120):
    fig.add_vline(x=lim, line=dict(color=RED, dash="dot"), row=1, col=1)
    fig.add_hline(y=lim, line=dict(color=RED, dash="dot"), row=1, col=1)
fig.add_trace(go.Histogram(x=err, nbinsx=90, marker_color=AMBER, name="error"), row=1, col=2)
fig.add_vline(x=0, line=dict(color="black", dash="dash"), row=1, col=2)
fig.update_xaxes(title_text="Measured (°C)", row=1, col=1)
fig.update_yaxes(title_text="Predicted (°C)", row=1, col=1)
fig.update_xaxes(title_text="Predicted − measured (°C)", row=1, col=2)
fig.update_layout(height=460, template="plotly_white", showlegend=False,
                  title=f"{best_name}: {len(y_test):,} held-out hours")
fig.show()

print(f"  mean error (bias)      {err.mean():+.3f} °C")
print(f"  median error           {np.median(err):+.3f} °C")
print(f"  standard deviation     {err.std():.3f} °C")
print(f"  within ±1 °C           {100*np.mean(np.abs(err) <= 1):.1f} % of hours")
print(f"  within ±3 °C           {100*np.mean(np.abs(err) <= 3):.1f} % of hours")
print(f"  worst over-prediction  {err.max():+.2f} °C")
print(f"  worst under-prediction {err.min():+.2f} °C")
''')],
    built="""The evidence behind the metric.

- The scatter sits on the 45° line across the whole range, including above 110 °C where the points thin out.
- The histogram is close to symmetric, with a small negative bias of **−0.16 °C**.
- **About 45 % of hours** are predicted within 1 °C and **93 %** within 3 °C. The worst single miss in 8,708
  hours is under 7 °C.

The overall bias looks harmless. The next step shows that the overall figure is hiding where it lives.""",
    takeaway="A predicted-against-measured plot is evidence; a metric is only a claim about it.",
)

step(
    id="trend", phase=7, icon="\U0001f4c9", ai_icon="⏱️",
    ee="Following A Real Week", ai="Time-Series Comparison",
    tech="Predicted and measured, hour by hour",
    site="""The scatter plot treats every hour as independent. Operations does not.

An engineer wants to see the model **follow the plant**:

- Does it track the daily peak, or lag it?
- Does it catch the evening rise before it happens or after?
- When the load steps, does the prediction step with it?""",
    challenge="""A week of real operation contains the events that matter.

- A contingency transfer, when a sibling unit goes out and this one picks up the feeder.
- The hottest afternoon of the summer.
- The overnight recovery, when the oil cools slowly and the winding cools quickly.

Any of these could be where the model breaks, and none of them are visible in an average.""",
    ai_link="""This is the plot that gets shown to an operations manager.

- No metrics. No axes anybody has to be taught to read.
- Two lines that should sit on top of each other, and a shaded band showing the error.

If the model is going to be trusted, this is the plot that does it.""",
    bridge=[("A trend recording", "A time-series plot"),
            ("Tracking the plant", "Prediction against measurement over time"),
            ("A contingency event", "The hours that test the model")],
    body=[("co", r'''
test_rows = df.loc[test_mask].copy()
test_rows["predicted"] = best_pred

# pick the hottest test week on the busiest unit
hot_unit = test_rows.groupby("unit_id").hotspot_temp_c.max().idxmax()
sub = test_rows[test_rows.unit_id == hot_unit]
peak = sub.loc[sub.hotspot_temp_c.idxmax(), "timestamp"]
window = sub[(sub.timestamp >= peak - pd.Timedelta(days=3)) &
             (sub.timestamp <= peak + pd.Timedelta(days=3))].sort_values("timestamp")

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.68, 0.32],
                    vertical_spacing=0.07,
                    subplot_titles=(f"{hot_unit}: predicted against measured hot-spot temperature",
                                    "Prediction error (°C)"))
fig.add_trace(go.Scatter(x=window.timestamp, y=window.hotspot_temp_c, name="Measured (probe)",
                         line=dict(color=RED, width=3)), row=1, col=1)
fig.add_trace(go.Scatter(x=window.timestamp, y=window.predicted, name="Predicted (model)",
                         line=dict(color=CYAN, width=2, dash="dot")), row=1, col=1)
fig.add_trace(go.Scatter(x=window.timestamp, y=window.oil_temp_c, name="Top oil (measured)",
                         line=dict(color=AMBER, width=1.5)), row=1, col=1)
fig.add_hline(y=110, line=dict(color=RED, dash="dash"),
              annotation_text="110 °C", row=1, col=1)
fig.add_trace(go.Bar(x=window.timestamp, y=window.predicted - window.hotspot_temp_c,
                     marker_color=MUTED, name="error"), row=2, col=1)
fig.update_yaxes(title_text="Temperature (°C)", row=1, col=1)
fig.update_yaxes(title_text="Error (°C)", row=2, col=1)
fig.update_layout(height=620, template="plotly_white", hovermode="x unified",
                  legend=dict(orientation="h", y=1.09))
fig.show()

w_err = (window.predicted - window.hotspot_temp_c)
print(f"{hot_unit}, {window.timestamp.min():%d %b} to {window.timestamp.max():%d %b}")
print(f"  measured peak   {window.hotspot_temp_c.max():.1f} °C")
print(f"  predicted peak  {window.predicted.max():.1f} °C")
print(f"  MAE this week   {w_err.abs().mean():.2f} °C")
print(f"  largest miss    {w_err.abs().max():.2f} °C")
print()
print("Note the gap between the amber and red lines - that is the winding gradient,")
print("the thing being predicted, and it widens exactly when the transformer is working hardest.")
''')],
    built="""Six days across the hottest hours of the test set — T2, in early August.

- The predicted line sits on the measured one through the daily cycle and the overnight recovery. Mean
  error across the week is **1.6 °C**.
- **The peak is the exception.** Measured 135.8 °C, predicted 132.1 °C — an under-prediction of
  nearly 4 °C at the single hour that matters most in the whole year.

That miss is not bad luck. It is the same effect the next step measures deliberately, and it points the
same way every time: the model is weakest, and biased low, exactly at the top.""",
    takeaway="The model tracks the plant closely all week and then under-reads the annual peak by nearly 4 °C — which is the one hour you cannot afford to under-read.",
)

step(
    id="hot-tail", phase=7, icon="\U0001f321️", ai_icon="⚠️",
    ee="The Errors That Actually Matter", ai="Segmented Evaluation",
    tech="Error by temperature band, converted to ageing",
    site="""95 % of the year, these transformers run between 40 °C and 90 °C hot spot. Nothing is at stake in
those hours.

The hours that matter are the other 5 %. Across the fleet's year:

- **1,753 hours** above 98 °C.
- **482 hours** above 110 °C.
- **113 hours** above 120 °C.

The average error is dominated by the 33,000 hours where accuracy is irrelevant.""",
    challenge="""Segment the error by temperature and the model looks different.

| Band | Error | Bias |
|---|---|---|
| Below 80 °C | 1.3 °C | −0.1 °C |
| 80 – 98 °C | 1.4 °C | −0.4 °C |
| 98 – 110 °C | 1.6 °C | −0.6 °C |
| Above 110 °C | **2.1 °C** | **−0.5 °C** |

The error grows where it matters, and it grows **in the dangerous direction** — the model under-predicts
the hottest hours. There are fewer training examples up there, and the model regresses towards the middle.

Reporting only the 1.35 °C average would hide this completely.""",
    ai_link="""The consequence has to be stated in engineering units, not statistical ones.

- The hottest **1 %** of hours carry **38 %** of the insulation ageing.
- The hottest **5 %** carry **71 %**.
- A 2 °C under-prediction at 110 °C understates the ageing rate by about 19 %.

So a model that is slightly worse in the top 5 % is worse where nearly all of the damage happens. That is
the honest way to report this model, and it points directly at the fix: weight the training towards the
hot band, or gather more hot-band data.""",
    bridge=[("Loading beyond nameplate", "The tail of the distribution"),
            ("Where the damage happens", "Segmented evaluation"),
            ("Degrees, converted to life", "A cost-weighted metric")],
    body=[("co", r'''
bands = [(0, 80, "Normal"), (80, 98, "Warm"), (98, 110, "Approaching limit"),
         (110, 999, "Beyond normal life expectancy")]
rows = []
for lo, hi, label in bands:
    m = (y_test.to_numpy() >= lo) & (y_test.to_numpy() < hi)
    if m.sum():
        rows.append({"Band (°C)": f"{lo}+" if hi == 999 else f"{lo}-{hi}", "Condition": label,
                     "Hours": int(m.sum()), "MAE (°C)": np.abs(err[m]).mean(),
                     "Bias (°C)": err[m].mean()})
print(pd.DataFrame(rows).round(2).to_string(index=False))
print()
print("The error grows with temperature, and the bias turns negative - the model")
print("under-predicts the hottest hours, which is the dangerous direction.")
'''),
           ("co", r'''
# What that means in insulation life, which is the unit the decision is actually made in.
faa_measured  = ageing_factor(y_test.to_numpy())
faa_predicted = ageing_factor(best_pred)

print(f"Over the {len(y_test):,} held-out hours:")
print(f"  ageing consumed, measured   {faa_measured.sum():8.0f} equivalent hours")
print(f"  ageing consumed, predicted  {faa_predicted.sum():8.0f} equivalent hours")
print(f"  the model reports {100*(faa_predicted.sum()/faa_measured.sum() - 1):+.1f} % of the true ageing")
print()

order = np.argsort(faa_measured)[::-1]
cum = np.cumsum(faa_measured[order]) / faa_measured.sum()
for pct in (0.01, 0.05, 0.10):
    n = int(pct * len(order))
    print(f"  the hottest {100*pct:4.0f} % of hours ({n:4d}) carry {100*cum[n-1]:4.1f} % of the ageing")
print()

fig = go.Figure(go.Scatter(x=100*np.arange(1, len(cum)+1)/len(cum), y=100*cum,
                           line=dict(color=RED, width=3), fill="tozeroy",
                           fillcolor="rgba(239,83,80,0.12)", name="cumulative ageing"))
fig.add_trace(go.Scatter(x=[0, 100], y=[0, 100], line=dict(color=MUTED, dash="dash"),
                         name="if every hour aged equally"))
fig.add_vline(x=5, line=dict(color=CYAN, dash="dot"), annotation_text="hottest 5 % of hours")
fig.update_layout(title="Insulation ageing is concentrated in a handful of hours",
                  xaxis_title="Hours, hottest first (%)",
                  yaxis_title="Cumulative insulation life consumed (%)",
                  height=430, template="plotly_white")
fig.show()
''')],
    built="""The model's real performance profile, and the argument for why it matters.

- Error rises from **1.3 °C** in the normal band to **2.1 °C** above 110 °C, and the bias is negative in
  every band above 80 °C.
- The hottest **5 %** of hours carry **71 %** of the year's insulation ageing. The hottest 10 % carry 83 %.
- Over the whole test set the model reports **4 % less** ageing than actually occurred — a small-sounding
  figure that is entirely produced by those few hundred hot hours.

This is a limitation to report, not to hide. The fix is more hot-band training data, or sample weighting
that values those hours more.""",
    takeaway="Report the error where the consequence is, not where the data is — 71 % of the ageing happens in 5 % of the hours, and that is where the model is weakest.",
)


# ------------------------------ PHASE 9 - WHAT THE MODEL DOES NOT KNOW
step(
    id="unseen-unit", phase=8, icon="\U0001f6ab", ai_icon="\U0001f4c9",
    ee="A Transformer It Has Never Seen", ai="Generalisation, Measured",
    tech="Train on three units, test on the fourth",
    site="""The whole point of the scheme is to run this model on transformers **without** a fibre-optic
probe.

So the real question is not how well it predicts T1 to T4. It is how well it predicts **T5** — a unit it
has never seen, of a different vintage, with a different winding design.

That is testable right now: train on three units, score on the fourth.""",
    challenge="""It fails, and it fails in a specific and diagnosable way.

Held-out unit MAE rises from **1.35 °C** to between **2.4 and 5.6 °C**, and almost all of it is **bias**,
not scatter:

- Trained without T3, the model **over-predicts T3 by 5.6 °C**, all year.
- Trained without T4, it **under-predicts T4 by 4.8 °C**, all year.

Those two units genuinely have different hot-spot factors — T4's winding runs hotter relative to its oil
than T3's does. When the model has seen a unit, it learns that offset. When it has not, it applies the
fleet average and is wrong by a constant.""",
    ai_link="""This is the single most important limitation of the whole project, and it must be measured
rather than assumed.

- The model interpolates **within** the fleet it learned. It does not extrapolate **to** new designs.
- A per-unit offset is not something more data from T1–T4 can fix. It needs data from the new unit.

The deployable version of this scheme is therefore: fit probes to a **representative sample** of designs,
train on those, and accept a calibration period on any unit type not represented.""",
    bridge=[("A different transformer design", "Out-of-distribution data"),
            ("A constant offset all year", "Bias, not variance"),
            ("Fitting probes to a sample of designs", "Making the training set representative")],
    body=[("co", r'''
print("Trained on three units, scored on the fourth:")
print()
rows = []
for held in ["T1", "T2", "T3", "T4"]:
    tr, te = (df.unit_id != held), (df.unit_id == held)
    m = GradientBoostingRegressor(n_estimators=300, learning_rate=0.06, max_depth=4,
                                  subsample=0.8, random_state=42
                                  ).fit(df.loc[tr, ENG_FEATURES], df.loc[tr, TARGET])
    p = m.predict(df.loc[te, ENG_FEATURES])
    e = p - df.loc[te, TARGET].to_numpy()
    rows.append({"Held-out unit": held,
                 "Age": int(df.loc[te, "transformer_age_years"].iloc[0]),
                 "MAE (°C)": np.abs(e).mean(), "Bias (°C)": e.mean(),
                 "Scatter, std (°C)": e.std()})
out = pd.DataFrame(rows)
print(out.round(2).to_string(index=False))
print()
print(f"Same-unit baseline (every 4th week held out): MAE {mae:.2f} °C")
print()
print("Look at Bias against Scatter. The scatter is close to the baseline - the model still")
print("tracks the SHAPE of a transformer it has never seen. It just has the wrong offset,")
print("because the hot-spot factor is a property of the winding, not of the readings.")
''')],
    built="""A measured limit, stated in the same units as the accuracy claim.

- On a unit it has seen: **1.35 °C**.
- On a unit it has not: **2.4 to 5.6 °C**, almost all of it a constant offset.
- The **scatter** rises only modestly, from 1.7 °C to between 1.9 and 2.7 °C, while the **bias** jumps to
  ±5 °C. The model learned the physics correctly and missed only the unit-specific constant.

That diagnosis matters. It means a short calibration period on a new unit — a few weeks of any independent
temperature check — would recover most of the accuracy.""",
    takeaway="This model knows these four transformers, not transformers in general — and the failure is a fixable offset, not a broken model.",
)


# --------------------------------------------- PHASE 10 - DECISION SUPPORT
step(
    id="predict", phase=9, icon="\U0001f39a️", ai_icon="\U0001f52e",
    ee="Asking The Model A Question", ai="Interactive Prediction",
    tech="Five readings in, one temperature out",
    site="""This is what the scheme looks like from the control room.

Five readings the substation already has:

- Load current, in amps
- Ambient temperature, in °C
- Top-oil temperature, in °C
- Voltage, in kV
- Humidity, in %

One answer: the hot-spot temperature, and what it means.""",
    challenge="""The answer on its own is not useful. **97 °C** tells an operator nothing they can act on.

What they need alongside it:

- How far from the 110 °C limit.
- What is driving the temperature — load, ambient, or degraded cooling.
- How fast insulation is being consumed at that temperature.
- Whether anything needs to be done.

A number without an interpretation is not decision support.""",
    ai_link="""Two different questions get asked of this model, and they are not interchangeable.

- **Sensor mode.** All five readings come from the plant right now. This is what the monitoring scheme does
  continuously.
- **What-if mode.** The engineer sets a load and an ambient, and the oil temperature is estimated from the
  thermal model. This answers *what would happen if we transferred another feeder onto this unit*.

Sensor mode is a measurement. What-if mode is a forecast, and it inherits the thermal model's assumptions.""",
    bridge=[("Reading the substation gauges", "The feature vector"),
            ("A control-room display", "Model inference"),
            ("Engineering interpretation", "Explaining a prediction")],
    body=[("co", r'''
def assess(load_a, ambient_c, oil_c, volt_kv=132.0, humidity_pct=60.0,
           age_years=16, hour=15, quiet=False):
    "Predict the hot spot from five readings, and explain the answer in engineering terms."
    K = load_a / I_RATED
    stage = 2 if (oil_c > 68 or K > 0.92) else (1 if (oil_c > 55 or K > 0.70) else 0)
    x = operating_point(load_a, ambient_c, oil_c, volt_kv, humidity_pct, stage, age_years, hour)
    theta_h = float(best_model.predict(x)[0])
    faa = float(ageing_factor(theta_h))
    headroom = 110.0 - theta_h

    notes = []
    notes.append(f"Loading is {K:.2f} per unit"
                 + (" — above nameplate." if K > 1.0 else
                    ", within nameplate." if K > 0.8 else ", light."))
    notes.append(f"Ambient {ambient_c:.0f} °C"
                 + (" is reducing cooling capacity." if ambient_c > 35 else
                    " is unremarkable." if ambient_c > 15 else " is helping the radiators."))
    notes.append(f"Top oil at {oil_c:.0f} °C is {oil_c - ambient_c:.0f} K above ambient"
                 + (" — already elevated." if oil_c - ambient_c > 35 else "."))
    notes.append(f"Cooling is at stage {stage}"
                 + (" (all fans running)." if stage == 2 else
                    " (first fan bank running)." if stage == 1 else " (fans off, natural circulation)."))
    notes.append(f"The winding gradient is {theta_h - oil_c:.0f} K above the oil — "
                 "this is the part no gauge measures.")

    if not quiet:
        print(f"  Load current      {load_a:7.0f} A      ({K:.2f} pu)")
        print(f"  Ambient           {ambient_c:7.1f} °C")
        print(f"  Top oil           {oil_c:7.1f} °C")
        print(f"  Voltage           {volt_kv:7.1f} kV")
        print(f"  Humidity          {humidity_pct:7.0f} %")
        print("  " + "-"*46)
        print(f"  HOT SPOT          {theta_h:7.1f} °C   <-- predicted")
        print(f"  Headroom to 110   {headroom:7.1f} K")
        print(f"  Ageing rate       {faa:7.2f} ×      (1.00 = design rate)")
        print()
        print("  Engineering interpretation")
        for n in notes:
            print(f"    - {n}")
    return {"hotspot_c": theta_h, "faa": faa, "headroom_k": headroom,
            "stage": stage, "load_pu": K, "notes": notes}

print("A summer evening on T3, carrying a transferred feeder:")
print()
_ = assess(load_a=720, ambient_c=36, oil_c=68, volt_kv=132, humidity_pct=74)
'''),
           ("co", r'''
# The same call, with sliders. Colab has ipywidgets installed already.
try:
    import ipywidgets as widgets
    from IPython.display import display, clear_output

    controls = {
        "load_a":       widgets.FloatSlider(value=720, min=250, max=1000, step=10,  description="Load (A)"),
        "ambient_c":    widgets.FloatSlider(value=36,  min=0,   max=48,   step=1,   description="Ambient (°C)"),
        "oil_c":        widgets.FloatSlider(value=68,  min=25,  max=95,   step=1,   description="Top oil (°C)"),
        "volt_kv":      widgets.FloatSlider(value=132, min=124, max=140,  step=0.5, description="Voltage (kV)"),
        "humidity_pct": widgets.FloatSlider(value=74,  min=20,  max=99,   step=1,   description="Humidity (%)"),
        "age_years":    widgets.IntSlider(  value=16,  min=0,   max=40,   step=1,   description="Age (years)"),
    }
    for c in controls.values():
        c.style.description_width = "110px"
        c.layout.width = "440px"
    out = widgets.Output()

    def refresh(_=None):
        with out:
            clear_output(wait=True)
            assess(**{k: v.value for k, v in controls.items()})

    for c in controls.values():
        c.observe(refresh, names="value")
    refresh()
    display(widgets.VBox(list(controls.values())), out)
except ImportError:
    print("ipywidgets not available - call assess(...) directly instead, for example:")
    print("  assess(load_a=850, ambient_c=42, oil_c=79)")
'''),
           ("co", r'''
# Four operating points, to see how the answer moves.
scenarios = [
    ("Overnight minimum",          320, 18, 34),
    ("Ordinary summer afternoon",  620, 33, 61),
    ("Evening peak, transferred feeder", 720, 36, 68),
    ("Heatwave plus contingency",  920, 43, 84),
]
rows = []
for name, load, amb, oil in scenarios:
    r = assess(load, amb, oil, quiet=True)
    rows.append({"Scenario": name, "Load (A)": load, "Ambient (°C)": amb, "Oil (°C)": oil,
                 "Hot spot (°C)": round(r["hotspot_c"], 1),
                 "Gradient (K)": round(r["hotspot_c"] - oil, 1),
                 "Headroom (K)": round(r["headroom_k"], 1),
                 "Ageing ×": round(r["faa"], 2)})
print(pd.DataFrame(rows).to_string(index=False))
print()
grads = [r["Gradient (K)"] for r in rows]
print(f"The gradient - the part no gauge measures - grows from {min(grads):.0f} K overnight")
print(f"to {max(grads):.0f} K in the heatwave contingency. That growth is what the model exists to predict,")
print("and no amount of watching the oil thermometer would reveal it.")
''')],
    built="""A working prediction, with the reasoning attached.

The worked example — 720 A, 36 °C ambient, 68 °C oil, 132 kV, 74 % humidity — returns a hot spot of
**97.8 °C**:

- **12 K of headroom** to the 110 °C limit.
- Ageing at **0.28 ×** the design rate, so the insulation is being consumed roughly three and a half
  times more slowly than its design assumption.
- Within limits, and worth watching rather than acting on.

The scenario table shows the winding gradient growing from **7 K** overnight to **45 K** in a heatwave
contingency. The oil thermometer cannot see any of that.""",
    takeaway="A predicted temperature is not decision support until it comes with the headroom, the ageing rate, and the reason.",
)

step(
    id="recommend", phase=9, icon="\U0001f6a6", ai_icon="\U0001f9ed",
    ee="Turning A Temperature Into An Action", ai="Decision Rules On Top Of A Model",
    tech="IEEE C57.91 table 8 limits, as thresholds",
    site="""The limits are not invented. IEEE C57.91 sets them:

| Hot spot | Loading condition | Action |
|---|---|---|
| Below 98 °C | Normal | Continue normal operation |
| 98 – 110 °C | Approaching normal-life limit | Monitor closely |
| 110 – 120 °C | Beyond normal life expectancy | Increase cooling, prepare to reduce load |
| Above 120 °C | Planned loading beyond nameplate | Reduce loading now |

The model supplies the temperature. The standard supplies the thresholds.""",
    challenge="""The recommendation has to name the **cause**, or it will be ignored.

*Reduce loading* on a transformer whose fans have failed is the wrong instruction — the cooling should be
fixed instead. The rule engine therefore checks:

- Is the load itself the problem, or is the ambient?
- Is the oil rise larger than the load justifies, which points at cooling?
- Are the fans already at full stage, so there is no cooling left to add?

Same temperature, different action, depending on what is driving it.""",
    ai_link="""Note where the machine learning stops.

- The model predicts a temperature. That is all it does.
- The thresholds come from a published standard.
- The cause diagnosis is engineering logic, written by hand, and readable by anyone.

Keeping those three separate is what makes the system auditable. Nobody has to trust the model to check
the rule.""",
    bridge=[("IEEE C57.91 loading limits", "Decision thresholds"),
            ("Diagnosing the cause", "Rules on top of the prediction"),
            ("A written instruction", "The system output")],
    body=[("co", r'''
def recommend(reading):
    "Turn a predicted hot spot into an action and a reason. Thresholds: IEEE C57.91 table 8."
    t, K = reading["hotspot_c"], reading["load_pu"]
    expected_rise = float(top_oil_rise(K, 1.0, reading["stage"], reading["age_years"]))
    cooling_shortfall = reading["oil_rise_c"] - expected_rise

    cooling_at_limit = reading["stage"] == 2
    cooling_faulty = cooling_shortfall > 6

    if t < 98:
        action, urgency = "Continue normal operation", "Routine"
    elif t < 110:
        # a cooling fault is a maintenance item at any temperature, not only above the limit
        if cooling_faulty:
            action, urgency = "Investigate cooling system", "Act today"
        else:
            action, urgency = "Monitor closely", "Watch"
    elif t < 120:
        urgency = "Act today"
        # naming the right lever matters more than naming the temperature
        if cooling_faulty:
            action = "Investigate cooling system, then reduce load if unresolved"
        elif cooling_at_limit:
            action = "Cooling is already at maximum — reduce loading"
        else:
            action = "Increase cooling, prepare to reduce load"
    else:
        urgency = "Immediate"
        action = ("Reduce loading now, and investigate cooling" if cooling_faulty
                  else "Reduce loading now")

    reasons = []
    if cooling_faulty:
        reasons.append(f"oil rise is {cooling_shortfall:.0f} K above what this load justifies — check "
                       "fans, radiators and oil condition before restricting load")
    if K > 1.05:
        reasons.append(f"loading is {K:.2f} pu, above nameplate")
    if reading["ambient_c"] > 38:
        reasons.append(f"ambient {reading['ambient_c']:.0f} °C is limiting how much heat the radiators can reject")
    if cooling_at_limit and t > 105:
        reasons.append("cooling is commanded to full stage, so load is the only remaining lever")
    if not reasons:
        reasons.append("temperature is consistent with the load and ambient conditions")

    return {"action": action, "urgency": urgency,
            "hotspot_c": round(t, 1), "headroom_k": round(reading["headroom_k"], 1),
            "ageing_x": round(reading["faa"], 2), "reasons": reasons}


def full_assessment(load_a, ambient_c, oil_c, volt_kv=132.0, humidity_pct=60.0, age_years=16):
    r = assess(load_a, ambient_c, oil_c, volt_kv, humidity_pct, age_years, quiet=True)
    r.update({"ambient_c": ambient_c, "oil_rise_c": oil_c - ambient_c, "age_years": age_years})
    return recommend(r)


cases = [
    ("Normal evening peak",              620, 30, 58, 16),
    ("Hot day, heavy load",              840, 40, 76, 16),
    ("Contingency in a heatwave",        950, 44, 87, 22),
    ("Moderate load, failed fan bank",   700, 32, 90, 22),
]
for name, load, amb, oil, age in cases:
    d = full_assessment(load, amb, oil, age_years=age)
    print(f"{name}")
    print(f"  {load:.0f} A, {amb:.0f} °C ambient, {oil:.0f} °C oil, {age} years old")
    print(f"  Hot spot {d['hotspot_c']} °C   headroom {d['headroom_k']} K   ageing {d['ageing_x']}×")
    print(f"  [{d['urgency']}]  {d['action']}")
    for r in d["reasons"]:
        print(f"     · {r}")
    print()
''')],
    built="""A recommendation engine, in about forty lines of readable rules.

Two cases are worth studying:

- **Case two** is genuinely overloaded on a hot day, with cooling already at full stage. The only lever
  left is load, and the recommendation says so — rather than telling an operator to increase cooling that
  is already at maximum.
- **Case four** is at nameplate load, and by temperature alone it would be filed as *monitor closely*. But
  the oil is sitting **23 K above what that load justifies**, so the rules escalate it to a cooling
  investigation. Restricting load there would make the temperature go away and leave a failed fan bank in
  service.

One honest caveat on case four: a 90 °C oil temperature at 700 A almost never occurs in the training data,
because in a healthy transformer it cannot. The model is extrapolating, and its temperature there is less
trustworthy than the rest. The **rule** that flags the cooling fault does not depend on the model at all —
which is exactly why the two are kept separate.""",
    takeaway="The model gives a temperature, the standard gives the threshold, and hand-written engineering logic gives the reason — keeping them separate is what makes the system auditable.",
)

step(
    id="dashboard", phase=9, icon="\U0001f4fa", ai_icon="\U0001f3af",
    ee="The Substation Monitoring Dashboard", ai="The Deployed System",
    tech="Four units, live prediction, ranked by risk",
    site="""Everything from the previous thirty steps, on one screen.

For each of the four transformers:

- The current readings from the plant.
- The predicted hot-spot temperature, against the 110 °C limit.
- Insulation life consumed so far this year.
- The recommended action, and why.

Ranked so the unit needing attention is at the top.""",
    challenge="""The dashboard has to answer the operator's real question, which is not *what is the
temperature*.

It is **which transformer should I look at first, and what should I do about it.**

That means ranking by risk rather than by name, showing headroom rather than raw temperature, and putting
the reason next to the recommendation.""",
    ai_link="""This is where the whole system finally does something.

- Cheap sensors that were already fitted, feeding
- a model trained on four instrumented units, feeding
- thresholds from a published standard, feeding
- one line of text an operator can act on.

The machine learning is one component of four. It is the component that supplies the number nobody can
measure.""",
    bridge=[("The substation control room", "The deployed system"),
            ("Which unit needs attention first", "Ranking by risk"),
            ("A year of accumulated damage", "Cumulative F_AA")],
    body=[("co", r'''
# The fleet at its most demanding hour of the year - the one an operator would be
# looking at. Every unit's readings are taken from the same timestamp.
peak_hour = df.groupby("timestamp").hotspot_temp_c.mean().idxmax()
latest = df[df.timestamp == peak_hour].set_index("unit_id")
year_ageing = df.assign(f=ageing_factor(df.hotspot_temp_c)).groupby("unit_id").f.agg(["sum", "size"])
print(f"Snapshot taken at {peak_hour:%Y-%m-%d %H:%M} — the fleet's hottest hour of the year.")
print()

panel = []
for u, row in latest.iterrows():
    d = full_assessment(row.load_current_a, row.ambient_temp_c, row.oil_temp_c,
                        row.voltage_kv, row.humidity_pct, int(row.transformer_age_years))
    panel.append({"Unit": u, "Age": int(row.transformer_age_years),
                  "Load (A)": round(row.load_current_a), "Ambient (°C)": round(row.ambient_temp_c, 1),
                  "Oil (°C)": round(row.oil_temp_c, 1), "Hot spot (°C)": d["hotspot_c"],
                  "Headroom (K)": d["headroom_k"], "Ageing ×": d["ageing_x"],
                  "Life used this year (equiv. days)": round(year_ageing.loc[u, "sum"] / 24, 1),
                  "Urgency": d["urgency"], "Action": d["action"]})

board = pd.DataFrame(panel).sort_values("Headroom (K)").reset_index(drop=True)
print("ASHGROVE SUBSTATION — hot-spot monitoring, most exposed unit first")
print("=" * 100)
print(board.drop(columns=["Action"]).to_string(index=False))
print()
for _, r in board.iterrows():
    print(f"  {r['Unit']}  [{r['Urgency']}]  {r['Action']}")
'''),
           ("co", r'''
fig = make_subplots(rows=1, cols=4, specs=[[{"type": "indicator"}]*4],
                    subplot_titles=[f"{r['Unit']} — {r['Age']} years" for _, r in board.iterrows()])
for i, (_, r) in enumerate(board.iterrows(), start=1):
    fig.add_trace(go.Indicator(
        mode="gauge+number", value=r["Hot spot (°C)"],
        number={"suffix": " °C", "font": {"size": 26}},
        gauge={"axis": {"range": [30, 140]},
               "bar": {"color": "rgba(0,0,0,0.75)", "thickness": 0.22},
               "steps": [{"range": [30, 98],   "color": "#c8e6c9"},
                         {"range": [98, 110],  "color": "#fff3c4"},
                         {"range": [110, 120], "color": "#ffcc9e"},
                         {"range": [120, 140], "color": "#ef9a9a"}],
               "threshold": {"line": {"color": RED, "width": 4}, "value": 110}}),
        row=1, col=i)
fig.update_layout(height=310, template="plotly_white",
                  title="Predicted winding hot-spot temperature — red line is the 110 °C limit")
fig.show()
'''),
           ("co", r'''
# Insulation life consumed over the year, per unit, and where it was consumed.
fig = make_subplots(rows=1, cols=2, subplot_titles=(
    "Insulation life consumed this year", "Hours above each limit"))
ag = (df.assign(f=ageing_factor(df.hotspot_temp_c)).groupby("unit_id")
        .agg(days=("f", lambda s: s.sum()/24),
             age=("transformer_age_years", "first")).reset_index())
fig.add_trace(go.Bar(x=ag.unit_id, y=ag.days, marker_color=AMBER,
                     text=ag.days.round(1), textposition="outside", name="equivalent days"),
              row=1, col=1)
for lim, colour in [(98, AMBER), (110, RED), (120, "#7b1fa2")]:
    h = df.groupby("unit_id").hotspot_temp_c.apply(lambda s: int((s > lim).sum()))
    fig.add_trace(go.Bar(x=h.index, y=h.values, name=f"> {lim} °C", marker_color=colour),
                  row=1, col=2)
fig.update_yaxes(title_text="Equivalent days of design life", row=1, col=1)
fig.update_yaxes(title_text="Hours in the year", row=1, col=2)
fig.update_layout(height=420, template="plotly_white", barmode="group",
                  title="Where the fleet's insulation life actually went")
fig.show()

print("Ageing is not proportional to age or to average load.")
print(ag.round(1).to_string(index=False))
print()
print("T1 is the youngest and lightest loaded, and consumed the least.")
print("The differences come almost entirely from hours above 110 °C.")
''')],
    built="""The deployed system, on one screen.

- Four transformers, ranked by **headroom to 110 °C** rather than by name.
- A predicted hot spot for each, from sensors that were already fitted.
- Insulation life consumed this year, in equivalent days.
- One recommendation per unit, with the reason next to it.

None of the four transformers reports a hot-spot temperature directly to this dashboard. Every number in
the hot-spot column was predicted.""",
    takeaway="The output of the whole project is one ranked screen that tells an operator which transformer to look at first, and why.",
)


# ============================================================================
# THE INTRO BLOCK
# ============================================================================
def phase_rows():
    rows = []
    for i, (name, desc) in enumerate(PHASES):
        ids = [s for s in STEPS if s["phase"] == i]
        first = STEPS.index(ids[0]) + 1
        last = STEPS.index(ids[-1]) + 1
        span = f"{first}" if first == last else f"{first}–{last}"
        rows.append(f"| **{i+1} · {name}** | {desc} | {span} |")
    return "\n".join(rows)


def mapping_rows():
    return "\n".join(
        f"| {s['icon']} {s['ee']} | → | {s['ai_icon']} {s['ai']} | {s['phase']+1} |"
        for s in STEPS)


md(rf"""
# ⚡ AI for Transformer Hot-Spot Temperature Prediction
## Machine Learning for Electrical Power Engineers

> You are not here to learn Artificial Intelligence. You are here to solve a **power systems problem** —
> one an engineer genuinely cannot solve by hand, for reasons that are arithmetic rather than effort. AI
> turns up in the middle of it, because the engineering requires it. Not before.

---

## 1 · The engineering problem

A power transformer converts voltage, not power. Everything it fails to pass on becomes **heat**.

That heat is not the problem. **Time spent hot** is the problem.

- Insulating paper degrades chemically, and the rate roughly **doubles every 6 °C**.
- The damage is cumulative and cannot be reversed.
- Nothing visible happens until the unit fails.

The temperature that governs this is the **winding hot spot** — the hottest point inside the coil, typically
**25 to 30 °C above the top-oil temperature** that the dial thermometer shows.

**Almost no transformer in service measures it.** Direct measurement needs a fibre-optic probe installed
between the winding discs at manufacture. It cannot be retrofitted without untanking the transformer.

So the industry estimates it, from IEEE C57.91, using nameplate values. That estimate assumes clean
radiators, oil in its original condition, a thermometer that responds instantly, and a hot-spot factor
measured in a factory test years ago. After two decades in service, none of those hold — and the error is
largest at high load, which is exactly when the answer matters.

---

## 2 · What we are going to build

A **hot-spot temperature prediction system** for a four-transformer substation. Four parts:

| | Part | What it does |
|---|---|---|
| 📡 | **Sensors already on the plant** | Load current, voltage, ambient temperature, humidity, top-oil temperature, fan status — hourly, on every unit, whether or not anybody is looking. |
| 🤖 | **A model learns this fleet** | Not the design as tested at the factory. These four transformers, as they actually run, including everything that has drifted since commissioning. |
| 📐 | **The standard supplies the limits** | 110 °C for normal life expectancy, 120 °C beyond nameplate, 140 °C emergency. The thresholds are published, not invented. |
| 🚦 | **The engineer gets a recommendation** | Not a temperature. A specific call: *T3, 4 K of headroom, cooling already at full stage, reduce loading now.* |

> **Be clear about the goal, because it is not automation.** Nothing here trips a breaker or changes a tap.
> The protection engineer stays in charge and still owns every loading decision. The system does the one
> thing a person cannot: **it estimates the temperature inside every winding, every hour, and never looks
> away.** The goal is not an unmanned substation. It is transformers that reach the end of their design
> life instead of failing before it.

---

## 3 · The engineering workflow

Not a syllabus, and not chapters. **One substation, one year**, in the order a real condition-monitoring
project runs it — ten phases. Every AI concept in this notebook hangs off one of them.

| Phase | In the substation | Steps |
|---|---|---|
{phase_rows()}

---

## 4 · Electrical Engineering → AI, the whole map

Spend a minute on this table before starting. **Every AI concept in this notebook is an electrical
engineering activity you already understand.** Not 'similar to'. The same thing, given a different name by
a different profession.

Read down the left column and you have described a transformer condition-monitoring scheme. Read down the
right column and you have described a complete machine learning pipeline. **They are the same column.**

| ⚡ Electrical engineering process | → | 🤖 The AI process that solves it | Phase |
|---|:-:|---|:-:|
{mapping_rows()}

---

## The one idea this notebook proves

> **Machine Learning learns the relationship between transformer operating conditions and hot-spot
> temperature, so engineers can predict overheating before it happens and protect the asset.**

Do not take that on trust. Step {[s['id'] for s in STEPS].index('leaderboard')+1} measures it against the
thermal model the industry already uses, and step
{[s['id'] for s in STEPS].index('unseen-unit')+1} measures where it stops working.
""")

md(r"""
---

## Setup

In Colab everything below is already installed. If you are running elsewhere, uncomment the install line.

Charts are Plotly, so they are interactive — hover, zoom, and toggle series from the legend.

XGBoost is used in one step and the notebook falls back to scikit-learn's gradient boosting if it is not
present, so every cell runs anywhere.
""")

co(r"""
# !pip install numpy pandas scikit-learn plotly xgboost ipywidgets

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

np.random.seed(42)
pd.set_option("display.width", 140)

# The course palette
CYAN, AMBER, GREEN, RED, MUTED = "#4fc3f7", "#ffb74d", "#66bb6a", "#ef5350", "#8b949e"

print("Environment ready.")
""")


# ============================================================================
# EMIT THE STEPS
# ============================================================================
for i, s in enumerate(STEPS):
    pname, pdesc = PHASES[s["phase"]]
    bridge_tbl = "\n".join(f"| {l} | → | {r} |" for l, r in s["bridge"])
    see = ""
    if APP:
        see = (f"\n> 🎬 **See this illustrated:** "
               f"[{APP}/?stage={s['id']}]({APP}/?stage={s['id']})\n")

    md(rf"""
---

# {NUM[i]} {s['icon']} {s['ee']}
### Phase {s['phase']+1} of {len(PHASES)} · {pname} — *{pdesc}*

> The electrical engineering activity on this page is also, exactly, the AI concept
> **{s['ai']}**. Here is why.

## Part 1 · In the substation

{s['site'].strip()}

## Part 2 · The engineering challenge

{s['challenge'].strip()}
""")

    md(rf"""
## Part 3 · Where the AI comes in

{s['ai_link'].strip()}

| ⚡ **In the substation** | → | 🤖 **In the AI** |
|---|:-:|---|
{bridge_tbl}

**{s['ee']}** → *becomes* → **{s['ai']}** → *which is computed as* → `{s['tech']}`
{see}
## Part 4 · The technical explanation

You now know what **{s['ee']}** is, why it is hard, and why it needs **{s['ai']}**. Only now, the
mechanism.
""")

    for kind, text in s["body"]:
        (md if kind == "md" else co)(text)

    md(rf"""
## Part 5 · What you just built

{s['built'].strip()}

> **Key takeaway.** {s['takeaway'].strip()}
""")


# ============================================================================
# THE CLOSING SUMMARY
# ============================================================================
md(r"""
---

# 🏁 The whole system, in one page

```
  SENSORS ALREADY ON THE PLANT              ENGINEERING FEATURES            MODEL
  ────────────────────────────              ────────────────────            ─────
  load current    ─┐                        K = I / I_rated        ─┐
  ambient temp     │                        K^1.6  (IEEE C57.91)    │
  top-oil temp     ├─► clean ─► engineer ─► oil rise over ambient   ├─► GRADIENT ─┐
  voltage          │                        3-hour rolling load     │   BOOSTING  │
  humidity         │                        oil and load ramps      │             │
  fan stage       ─┘                        transformer age        ─┘             │
                                                                                  ▼
                        ┌───────────────────────────────────────────────────────────┐
                        │  PREDICTED WINDING HOT-SPOT TEMPERATURE   (MAE 1.35 °C)    │
                        └───────────────────────────────────────────────────────────┘
                                                                                  │
   IEEE C57.91 limits  ──────►  110 / 120 / 140 °C  ──────►  RECOMMENDATION  ◄─────┘
   Ageing factor F_AA  ──────►  insulation life consumed          │
                                                                  ▼
                                              SUBSTATION MONITORING DASHBOARD
                                              four units, ranked by headroom
```

## What was built

| Stage | Method | Output |
|---|---|---|
| Establish the baseline | IEEE C57.91, nameplate values | MAE 3.18 °C, nothing fitted |
| Predict from raw sensors | Linear regression | MAE 2.41 °C |
| Add the physics as columns | Feature engineering | MAE 2.00 °C, same algorithm |
| Handle curvature and interaction | Random Forest | MAE 1.53 °C |
| Correct the residual, tree by tree | Gradient Boosting | MAE 1.35 °C, tens of seconds |
| The same answer, far faster | XGBoost | MAE 1.35 °C, in a fraction of the time |
| Rank the sensors | Feature importance + refitting | humidity and voltage earn nothing |
| Check the response | Sensitivity analysis | a loading chart, from data |
| Score where it matters | Segmented evaluation | 2.1 °C above 110 °C, biased low |
| Measure the limit | Hold out a whole unit | 2.4–5.6 °C on an unseen design |
| Turn it into an action | IEEE limits + engineering rules | one recommendation per unit |

## The three things worth remembering

1. **The hot spot decides transformer life, and almost nobody measures it.** Insulation ageing doubles
   every 6 °C, and the winding runs 25–30 °C above the oil temperature on the gauge. Predicting that gap is
   the entire problem.
2. **Machine learning did not replace the thermal standard — it learned what the standard was never
   given.** IEEE C57.91 describes the design. The model describes these four transformers as they actually
   run, twenty-two years of radiator fouling included. Error fell 58 %, from 3.18 °C to 1.35 °C.
3. **Power System Engineer + AI.** The model supplies one number. The published standard supplies the
   thresholds. Hand-written engineering logic supplies the reason. A person still decides, still signs the
   loading order, and still owns the consequence.

## Where the engineering discipline showed up

Five moments in this notebook were engineering judgements, not machine learning:

- **Choosing the target.** Predicting top oil would have been easy and useless. It is already measured.
- **Deleting the de-energised hours** instead of repairing them, because a cooling transformer obeys
  different physics from a loaded one.
- **Comparing against IEEE C57.91**, not against zero. A model that cannot beat the closed-form standard is
  not worth deploying whatever its R² looks like.
- **Scoring the hot band separately.** The average error is dominated by hours where accuracy is irrelevant;
  the hottest 5 % of hours carry 71 % of the insulation ageing, and that is where the model is weakest.
- **Measuring the limit rather than asserting it.** Holding out an entire transformer showed the model
  carries a per-unit offset it cannot learn from the others.

Those five are what separate a model from a condition-monitoring scheme.

## What this system cannot do

Stated plainly, because a monitoring scheme that oversells itself gets switched off:

- It **does not transfer to an unseen transformer design** without a calibration period. Step 27 measures
  the penalty: 2.4 to 5.6 °C of constant offset.
- It is **least accurate in the hot band**, and biased low there. That is the opposite of what you want,
  and it is a consequence of having few training hours above 110 °C.
- It **requires a working top-oil thermometer.** Remove that input and the problem becomes substantially
  harder.
- It **predicts the present, not the future.** Forecasting the hot spot hours ahead needs a load forecast
  as well, which is a separate project.
""")


nb = new_notebook(cells=cells, metadata={
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"},
    "colab": {"provenance": []},
})
nbf.validate(nb)
with open("Transformer_HotSpot_Temperature_AI.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"wrote Transformer_HotSpot_Temperature_AI.ipynb  "
      f"({len(cells)} cells, {sum(1 for c in cells if c.cell_type == 'code')} code, "
      f"{len(STEPS)} steps, {len(PHASES)} phases)")
