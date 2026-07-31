"""
Builds Pavement_Remaining_Life_AI.ipynb from nbformat cells.
Run:  py -3.13 build_nb.py

Same five-part-per-step layout as the Smart Construction / Transformer /
Cutting Tool notebooks. 23 steps, 10 phases.

The domain content is real and standards-based:
  * AASHTO 1993 flexible pavement design equation - allowable 80 kN equivalent
    single axle loads (ESALs) from the structural number SN and the subgrade
    resilient modulus MR.
  * The AASHO Road Test fourth-power law - damage of one axle relative to the
    80 kN standard axle = (P/80)^4.
  * Miner's linear cumulative damage - consumed life is the ratio of applied
    ESALs to allowable ESALs.
Those three are used to GENERATE the condition survey and to CHECK the model,
so the notebook and the design standards never disagree.

APP: set to a deployed Streamlit URL to switch on the per-step links.

NOTE for future editors:
  * step body code is wrapped in r'''...''' so a \"\"\"docstring\"\"\" inside a
    code cell is fine, but a ''' is not.
  * xgboost and ipywidgets are optional; both are guarded so every cell runs.
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

APP = ""

cells = []
def md(t):  cells.append(new_markdown_cell(t.strip("\n")))
def co(t):  cells.append(new_code_cell(t.strip("\n")))
def link(stage, label):
    return f"[{label}]({APP}/?stage={stage})" if APP else label

PHASES = [
    ("The Road Network",     "Thousands of segments, one maintenance budget."),
    ("How Pavements Fail",   "Load and climate — and whichever arrives first."),
    ("The Condition Survey", "An inspection becomes a row of measurements."),
    ("The Survey Export",    "The network file lands and gets checked."),
    ("Preparing The Data",   "Bad records out, the network split by road."),
    ("Learning Deterioration", "The rule the agency runs, then the models that beat it."),
    ("Reading The Model",    "Which factors drive the prediction, and why."),
    ("The Prediction",       "Six measurements in, remaining service life out."),
    ("The Pavement Audit",   "Every prediction checked against what actually happened."),
    ("Maintenance Planning", "One recommendation per segment, and what it is worth."),
]

NUM = ["①","②","③","④","⑤","⑥","⑦","⑧","⑨","⑩",
       "⑪","⑫","⑬","⑭","⑮","⑯","⑰","⑱","⑲","⑳",
       "㉑","㉒","㉓"]

STEPS = []
def step(**kw): STEPS.append(kw)


# ---------------------------------------------- PHASE 1 · THE ROAD NETWORK
step(
    id="road-network", phase=0, icon="🛣️", ai_icon="🤖",
    civil="A Highway Network Under Load", ai="Why Asset Management Needs AI",
    tech="Continuous deterioration vs a periodic inspection cycle",
    site="""A state highway agency maintains 1,500 pavement segments — national highways, state highways and
district roads. Every segment carries traffic every day. Every segment is ageing. The maintenance budget
covers a fraction of them each year.""",
    challenge="""A pavement does not fail on a schedule. It fails when accumulated axle loads and climate exhaust the
structure that was built for it. Two segments built in the same year, to the same drawing, can be eight
years apart in condition because one of them carries loaded trucks and the other does not.

The agency inspects on a cycle and repairs on a cycle. The pavements do not.""",
    ai_link="""Nothing here needs judgement replaced. It needs arithmetic done at scale: combining traffic, structure,
age, climate and observed distress into a **current** estimate of how many years each segment has left, so
the engineer's budget goes to the right segments this year.""",
    bridge=[("Deteriorates continuously", "Assess every segment"),
            ("Inspected on a cycle", "Model the drivers"),
            ("One engineer, 1,500 segments", "Rank the network")],
    body=[("co", r'''
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

RNG = np.random.default_rng(42)

# The course palette - amber is the civil world, cyan the AI world.
AMBER, CYAN, VIOLET = "#ffb74d", "#4fc3f7", "#ba68c8"
GREEN, RED, MUTED, INK = "#66bb6a", "#ef5350", "#8b949e", "#37474f"

# ---------------------------------------------------------------- the network
NETWORK_SEGMENTS = 1500
SEGMENT_KM       = 1.0          # each survey segment is one kilometre
BUDGET_KM_YEAR   = 105          # kilometres the agency can actually treat in a year

print("THE PROBLEM, IN THREE NUMBERS\n")
print(f"  segments in the network                {NETWORK_SEGMENTS:>8,}")
print(f"  kilometres treatable per year          {BUDGET_KM_YEAR:>8,}")
print(f"  share of the network treated per year  {BUDGET_KM_YEAR/NETWORK_SEGMENTS:>8.1%}")
print()
print("So the question is never 'is this road deteriorating'. It always is.")
print("The question is 'which 105 kilometres, this year' - and that is a ranking problem.")
'''),
          ("md", r"""
The consequence of getting the ranking wrong runs in both directions.

| Wrong call | What it costs |
|---|---|
| **Repaired too early** | Sound pavement is milled off. Years of paid-for service life are thrown away. |
| **Repaired too late** | The surface fails, water reaches the base, and a ₹-per-km overlay becomes a reconstruction. |

Both errors are invisible on the day they are made. Both are expensive years later.
""")],
    built="""The framing for everything that follows: this is a ranking problem under a fixed budget, not a
detection problem.""",
    takeaway="""The agency can treat 7% of the network a year — so the whole job is deciding which 7%.""",
)

step(
    id="enter-ai", phase=0, icon="👷", ai_icon="🧭",
    civil="The Highway Engineer Stays In Charge", ai="A Decision Support System",
    tech="The model proposes; the engineer authorises",
    site="""Nothing about the engineering changes. The engineer still walks the section, still reads the cores,
still judges whether a stretch can be closed during harvest season, and still signs the estimate.""",
    challenge="""The usual objection deserves a straight answer. Is this here to replace the pavement engineer? No. A
model cannot see that the drain has been blocked by a new building, cannot know that a quarry is opening
next year, and cannot carry the consequence of a road that fails under traffic.""",
    ai_link="""What the model does is duller and genuinely beyond one person: evaluate every segment in the network,
every survey cycle, against six measurements at once — and say **which one first**, with its reasons
attached.""",
    bridge=[("The engineer stays", "Ranks the network"),
            ("Survey data is added", "Proposes a treatment"),
            ("Nobody is replaced", "You still sign the estimate")],
    body=[("md", r"""
| The engineer stays in charge of | Where one person needs help |
|---|---|
| Reading a core, judging a subgrade | Assessing 1,500 segments every cycle |
| Knowing the drainage was never built | Comparing today against 20 years of records |
| Sequencing work around the monsoon | Weighing six interacting factors at once |
| Signing the estimate | Never having an off week |
| Carrying the consequence | — |

> Four treatments are possible, and they differ by roughly an order of magnitude in cost:
>
> **Continue normal operation** · **Preventive maintenance** · **Major rehabilitation** ·
> **Reconstruction**
>
> The system's job is to propose one of the four, with a predicted remaining life and an engineering
> reason. The engineer's job is to decide.
""")],
    built="""The role of the system, settled before any code is written: it predicts and explains, a person
authorises.""",
    takeaway="""Highway Engineer + AI. The model ranks and explains; the engineer decides and signs.""",
)


# ---------------------------------------------- PHASE 2 · HOW PAVEMENTS FAIL
step(
    id="deterioration", phase=1, icon="🚛", ai_icon="📐",
    civil="Why Pavements Deteriorate", ai="The Physics The Model Must Learn",
    tech="The fourth-power law: damage = (axle load / 80 kN)⁴",
    site="""A flexible pavement fails from the accumulation of individual axle passes. Each pass bends the layers a
little. The bending fatigues the bound layers and permanently deforms the unbound ones.""",
    challenge="""Damage is not proportional to load. It is roughly proportional to the **fourth power** of it — the result
of the AASHO Road Test, and the reason pavement engineering counts axles rather than vehicles.

That single exponent is why traffic *volume* is a weak predictor on its own, and why a road can look
lightly trafficked and still be consumed.""",
    ai_link="""Any model that predicts pavement life must reproduce a strongly non-linear response to load. A model that
can only add up weighted inputs cannot. This is the first concrete reason a straight line will not be
enough — and we will measure exactly how much it costs later.""",
    bridge=[("Fourth-power damage", "A non-linear target"),
            ("Axles, not vehicles", "Feature engineering"),
            ("Standard 80 kN axle", "A common unit — the ESAL")],
    body=[("co", r'''
def esal_factor(axle_kn):
    """Damage of one axle relative to the 80 kN standard axle (AASHO Road Test)."""
    return np.power(np.asarray(axle_kn, float)/80.0, 4.0)

VEHICLES = [("Car (per axle)",             5.0),
            ("Light commercial vehicle",  28.0),
            ("Bus",                       58.0),
            ("2-axle truck, legal",       80.0),
            ("2-axle truck, 25% overloaded", 100.0),
            ("Multi-axle truck, rear axle", 115.0)]

print("THE FOURTH-POWER LAW - damage relative to one standard 80 kN axle\n")
print(f"{'axle':<32}{'load':>8}{'damage':>12}{'= how many cars':>18}")
car = esal_factor(5.0)
for name, kn in VEHICLES:
    d = esal_factor(kn)
    print(f"{name:<32}{kn:>7.0f}kN{d:>12.3f}{d/car:>18,.0f}")

print("\nRead the last column. One legal truck axle does the damage of about 65,000 car axles.")
print("Overload the same truck by 25% and it does 2.4 times the damage it did when legal.")
print("It is why a highway agency counts axles, not vehicles: the small share of the")
print("traffic that is commercial does essentially all of the structural damage.")
'''),
          ("co", r'''
kn = np.linspace(20, 130, 200)
fig = go.Figure()
fig.add_trace(go.Scatter(x=kn, y=esal_factor(kn), mode="lines",
                         line=dict(color=AMBER, width=3), name="damage per axle"))
fig.add_trace(go.Scatter(x=[80], y=[1.0], mode="markers+text", text=["standard axle"],
                         textposition="top left", marker=dict(color=CYAN, size=12),
                         name="80 kN reference"))
fig.add_trace(go.Scatter(x=[100], y=[esal_factor(100)], mode="markers+text",
                         text=["25% overload = 2.4x damage"], textposition="top left",
                         marker=dict(color=RED, size=12), showlegend=False))
fig.update_layout(title="Damage is the fourth power of axle load",
                  xaxis_title="axle load (kN)", yaxis_title="equivalent standard axle loads (ESAL)",
                  template="plotly_white", height=420)
fig.show()
'''),
          ("md", r"""
Traffic is only half of it. The other half is the environment:

- **Rainfall** weakens the unbound layers and the subgrade. Water in the base is the single fastest way to
  destroy a pavement, and the AASHTO method accounts for it explicitly through a **drainage coefficient**.
- **Temperature** ages the bitumen. Hot pavements oxidise, stiffen, and crack even where no truck ever
  runs — which is why a lightly trafficked road still has a finite life.

So a pavement has **two clocks**: one driven by load, one driven by climate. It fails on whichever runs
out first.
""")],
    built="""The load mechanism, quantified: damage rises with the fourth power of axle load, so traffic effects are
strongly non-linear.""",
    takeaway="""Damage goes as load⁴ — a fact no straight-line model can represent.""",
)

step(
    id="service-life", phase=1, icon="📉", ai_icon="🎯",
    civil="What 'Remaining Service Life' Means", ai="Defining The Target Variable",
    tech="AASHTO 1993: allowable ESALs from structural number and subgrade modulus",
    site="""Serviceability falls from about 4.2 on a newly built pavement to a terminal value — commonly 2.5 on a
highway — at which the agency has committed to intervene. **Remaining service life** is the number of
years from today until that terminal condition is reached.""",
    challenge="""It cannot be measured today. It depends on a structure that is buried, a subgrade that was tested once
before construction, traffic that will grow, and weather that has not happened yet.

What *can* be computed is the design capacity — and the AASHTO 1993 equation does exactly that.""",
    ai_link="""This is the number the model will predict: **one continuous value, in years**. A continuous target makes
this a **regression** problem, not a classification problem. That choice drives everything downstream —
which models apply, and which error measures are meaningful.""",
    bridge=[("Remaining years of service", "The target variable, y"),
            ("A continuous quantity", "Regression, not classification"),
            ("Terminal serviceability 2.5", "Where the count stops")],
    body=[("co", r'''
# ------------------------------------------- AASHTO 1993 flexible pavement design
ZR, SO   = -1.282, 0.45      # standard normal deviate at 90% reliability, overall deviation
PSI0     = 4.2               # initial present serviceability index
PSI_TERM = 2.5               # terminal PSI for a highway - the definition of "end of life"

def structural_number(ac_mm, base_mm, subbase_mm, m2=1.0, m3=1.0):
    """AASHTO structural number. Layer coefficients are per inch of thickness.

    0.44 for dense bituminous concrete, 0.14 for a granular base, 0.11 for a
    granular sub-base. m2 and m3 are drainage coefficients on the unbound layers.
    """
    return (0.44*np.asarray(ac_mm, float)/25.4
            + 0.14*np.asarray(base_mm, float)/25.4*m2
            + 0.11*np.asarray(subbase_mm, float)/25.4*m3)

def allowable_esals(sn, mr_psi):
    """AASHTO 1993 design equation solved for W18 - the ESALs the structure can carry."""
    sn = np.asarray(sn, float)
    dpsi  = np.log10((PSI0 - PSI_TERM)/(PSI0 - 1.5))
    denom = 0.40 + 1094.0/np.power(sn + 1.0, 5.19)
    log_w18 = (ZR*SO + 9.36*np.log10(sn + 1.0) - 0.20 + dpsi/denom
               + 2.32*np.log10(np.asarray(mr_psi, float)) - 8.07)
    return np.power(10.0, log_w18)

print("AASHTO 1993 - what a structure can carry, on a 6,000 psi subgrade\n")
print(f"{'asphalt':>9}{'base':>8}{'sub-base':>10}{'SN':>7}{'allowable ESALs':>18}")
for ac in [80, 130, 180, 240, 300]:
    sn = structural_number(ac, 250, 200)
    print(f"{ac:>7}mm{250:>6}mm{200:>8}mm{sn:>7.2f}{allowable_esals(sn, 6000):>18,.0f}")

thin  = allowable_esals(structural_number(180, 250, 200), 6000)
thick = allowable_esals(structural_number(240, 250, 200), 6000)
print(f"\nGoing from 180 mm to 240 mm is 33% more asphalt. It is {thick/thin:.1f} times the capacity.")
print("Capacity rises far faster than thickness - the second non-linearity in this problem.")
'''),
          ("co", r'''
# Two clocks: the load clock and the climate clock. A pavement fails on the first to expire.
years = np.linspace(0, 26, 200)

def psi_curve(life_years, power=2.4):
    """Serviceability decay - slow at first, then accelerating (a standard performance curve)."""
    frac = np.clip(years/life_years, 0, 1.4)
    return PSI0 - (PSI0 - PSI_TERM)*np.power(frac, power)

fig = go.Figure()
fig.add_trace(go.Scatter(x=years, y=psi_curve(9.0),  mode="lines", name="heavy traffic, thin section",
                         line=dict(color=RED, width=3)))
fig.add_trace(go.Scatter(x=years, y=psi_curve(17.0), mode="lines", name="design case",
                         line=dict(color=AMBER, width=3)))
fig.add_trace(go.Scatter(x=years, y=psi_curve(24.0), mode="lines", name="light traffic, dry climate",
                         line=dict(color=GREEN, width=3)))
fig.add_hline(y=PSI_TERM, line_dash="dash", line_color=MUTED,
              annotation_text="terminal serviceability 2.5 - intervention", annotation_position="right")
fig.update_layout(title="Serviceability falls slowly, then quickly",
                  xaxis_title="years since construction", yaxis_title="present serviceability index",
                  yaxis_range=[1.8, 4.4], template="plotly_white", height=430)
fig.show()

print("Remaining service life is the horizontal distance from today to the dashed line.")
print("Note the shape: most of the loss happens in the last third of the life.")
print("A pavement that looks acceptable today can be two years from the dashed line.")
'''),
          ("md", r"""
That curve shape is the reason preventive maintenance exists.

- Treat while the curve is still flat and a thin surface seal restores it.
- Treat after the curve has turned and only structural work will do.

The gap between those two moments is worth several times the cost of the treatment — and it is exactly
the gap this project is trying to find.
""")],
    built="""The target defined and grounded in a design standard: remaining service life in years, ending at a
terminal serviceability of 2.5.""",
    takeaway="""The target is one continuous number — years to terminal condition — which makes this a regression
problem.""",
)


# ---------------------------------------------- PHASE 3 · THE CONDITION SURVEY
step(
    id="inspection", phase=2, icon="🔍", ai_icon="📊",
    civil="One Pavement Inspection", ai="Where The Data Comes From",
    tech="Six measurements per segment, collected four different ways",
    site="""A network survey vehicle covers the section at traffic speed. Behind it, or alongside it, sit four
independent data sources — and they arrive on four different schedules.""",
    challenge="""No single instrument sees the whole problem. The roughness profiler says nothing about the structure
underneath. The traffic counter says nothing about condition. The core log is five years old. The engineer
holds all of them together mentally; the file does not.""",
    ai_link="""Machine learning starts here, not at the model. Each measurement becomes a **feature** — a named column
that describes one segment. Getting the columns right matters more than the choice of algorithm.""",
    bridge=[("Survey vehicle run", "Condition features"),
            ("Traffic count", "Loading features"),
            ("Core log & met station", "Structural and climate features")],
    body=[("md", r"""
| Where it comes from | Measurement | Why it matters |
|---|---|---|
| 🚐 **Survey vehicle** | Crack density (%), roughness IRI | The observed damage — the summary of everything that has already happened |
| 🔢 **Traffic counter** | Traffic volume (vehicles/day) | The load that is consuming the structure |
| 🧱 **Core log / as-built** | Pavement thickness (mm), age (years) | The capacity that was built, and how long it has been spending it |
| 🌦️ **Met station** | Rainfall (mm/year), temperature (°C) | The second clock — moisture in the base, oxidation of the binder |
| 📉 **Deflectometer** *(optional)* | Central deflection (mm) | A direct measurement of structural stiffness |

**Six of these are the model inputs.** Deflection and roughness are recorded but deliberately held back —
we return to them once feature importance tells us whether they are worth the survey cost.
""")],
    built="""The measurement inventory: what is collected, by whom, and what engineering quantity each one stands
for.""",
    takeaway="""Every feature in this project is a measurement a highway agency already collects.""",
)

step(
    id="one-record", phase=2, icon="📋", ai_icon="🗂️",
    civil="One Segment Becomes One Row", ai="Structured Data",
    tech="One kilometre of road → one labelled record",
    site="""Segment SH-021/07: kilometre 7 of a state highway. Constructed 12 years ago, 240 mm of bituminous
layers, carrying 22,000 vehicles a day in a moderate climate. Last survey recorded 18% crack density.""",
    challenge="""An engineer reads that paragraph and forms a judgement. A computer cannot read a paragraph. It needs the
same facts as numbers in fixed positions, so that a thousand segments can be compared on identical terms.""",
    ai_link="""This is what *structured data* means, and it is why pavement management is a natural machine learning
problem: the agency has been recording exactly these columns, in exactly this shape, for decades.""",
    bridge=[("A segment inspection", "One row"),
            ("Each measurement", "One column, one feature"),
            ("What actually happened", "The label, y")],
    body=[("co", r'''
one_segment = pd.Series({
    "segment_id":            "SH-021/07",
    "road_class":            "State Highway",
    "traffic_volume_vpd":    22000,
    "pavement_thickness_mm": 240,
    "pavement_age_years":    12,
    "rainfall_mm_year":      1100,
    "avg_temperature_c":     31.0,
    "crack_density_pct":     18.0,
})
print("ONE SEGMENT, AS THE MODEL SEES IT\n")
print(one_segment.to_string())
print("\nInputs  (X): the six engineering measurements below the class name.")
print("Output  (y): remaining service life in years - to be predicted.")
'''),
          ("md", r"""
### Where the label comes from

This is the question most projects skip, and it decides whether any of this is real.

The label is **not** a prediction and **not** an opinion. The agency has twenty years of records. For a
segment that has since been rehabilitated, the year it reached terminal condition is known from the works
file. Remaining service life at the time of any past survey is then simple subtraction.

- The **features** are what was known on the survey date.
- The **label** is what actually happened afterwards.

If those two ever come from the same source, the project is measuring its own assumptions. They do not
here.
""")],
    built="""A single inspection expressed as a row of features plus one honestly sourced label.""",
    takeaway="""Features are what you knew on survey day; the label is what the works file recorded afterwards.""",
)


# ---------------------------------------------- PHASE 4 · THE SURVEY EXPORT
step(
    id="collect", phase=3, icon="🗃️", ai_icon="💾",
    civil="The Network Condition Survey", ai="Data Collection",
    tech="1,500 segments across 150 roads, three climate zones",
    site="""The full survey export lands: every segment on the network, with its structure, its traffic, its climate
and its measured distress, plus the outcome recorded for each one in the works file.""",
    challenge="""It is not a clean file. It has been assembled from four systems by four teams, some of it typed by hand,
some of it exported by instruments that report their own error codes as numbers.""",
    ai_link="""Load it first, look at it second, believe it third. The order matters — most of the damage done by
machine learning in engineering is done by trusting a file that nobody opened.""",
    bridge=[("Years of survey records", "read_csv"),
            ("Every segment on the network", "One row per sample"),
            ("The works file outcome", "The label column")],
    body=[("md", r"""
The cell below assembles the agency's export. It uses the AASHTO relationships already defined — a
segment's outcome follows from its structure, its traffic and its climate, exactly as the design standard
says it should.

You do not need to read it. Read the file it produces.
"""),
          ("co", r'''
# ============================================================================
#  Builds the agency's survey export.  You will only ever LOAD the file below.
# ============================================================================
CLASSES = {
    "National Highway": dict(n=42, aadt=(18000, 46000), truck=(12, 18), tf=(3.8, 4.6),
                             ac=(210, 310), growth=(0.035, 0.055)),
    "State Highway":    dict(n=54, aadt=(6000, 20000),  truck=(7, 13),  tf=(2.8, 3.6),
                             ac=(140, 225), growth=(0.025, 0.045)),
    "District Road":    dict(n=54, aadt=(800, 7000),    truck=(4, 9),   tf=(1.8, 2.6),
                             ac=(70, 140),  growth=(0.015, 0.035)),
}
ZONES = {"Arid":     dict(rain=(300, 750),   temp=(27, 38)),
         "Moderate": dict(rain=(750, 1500),  temp=(21, 32)),
         "Wet":      dict(rain=(1500, 3000), temp=(22, 33))}
DISTRICTS = ["Anantpur", "Bilaspur", "Chittoor", "Dharwad", "Erode", "Kadapa", "Latur", "Nashik"]

LANE_F, DIR_F = 0.90, 0.50      # lane distribution and directional split

def annual_esals(aadt, truck_pct, truck_factor):
    """Equivalent standard axle loads applied per year in the design lane."""
    return aadt*(truck_pct/100.0)*truck_factor*365.0*LANE_F*DIR_F

def env_multiplier(temp_c, rain_mm):
    """How much faster the climate consumes the structure than the design assumption."""
    hot = 1.0 + 0.030*(temp_c - 25.0)                          # binder oxidation, rutting
    wet = 1.0 + 0.20*np.clip((rain_mm - 800.0)/1800.0, 0, 1)   # moisture in the unbound layers
    return hot*wet

def climate_life(temp_c, rain_mm, quality):
    """Years to terminal condition from ageing alone, with no traffic at all."""
    return (24.5 - 0.30*(temp_c - 24.0) - 2.5*(rain_mm - 900.0)/1000.0)*quality

def remaining_years(capacity, consumed, esal_year_eff, growth):
    """Years until cumulative damage reaches capacity, allowing for traffic growth."""
    rem = np.maximum(capacity - consumed, 0.0)
    return np.log1p(growth*rem/esal_year_eff)/np.log1p(growth)

def build_survey():
    rows, rid = [], 0
    for cls, spec in CLASSES.items():
        for _ in range(spec["n"]):
            rid += 1
            zone = RNG.choice(list(ZONES), p=[0.30, 0.42, 0.28])
            z    = ZONES[zone]
            road = f"{cls.split()[0][:2].upper()}-{rid:03d}"

            # --- road-level properties, none of which reach the model -------
            aadt_road = RNG.uniform(*spec["aadt"])
            truck_pct = RNG.uniform(*spec["truck"])
            tf        = RNG.uniform(*spec["tf"])
            growth    = RNG.uniform(*spec["growth"])
            ac_road   = RNG.uniform(*spec["ac"])
            base_mm   = RNG.uniform(230, 290)
            subbase   = RNG.uniform(190, 260)
            mr_psi    = RNG.uniform(6000, 10000)*(0.90 if zone == "Wet" else 1.0)
            drainage  = RNG.uniform(0.60, 1.0)          # quality of the side drains
            quality   = RNG.uniform(0.90, 1.10)         # construction and material quality
            rater     = RNG.uniform(0.90, 1.12)         # this survey crew's rating bias
            age_road  = RNG.uniform(1.0, 23.0)
            rain      = RNG.uniform(*z["rain"])
            temp      = RNG.uniform(*z["temp"])
            district  = RNG.choice(DISTRICTS)

            m = float(np.clip(1.20 - 0.30*(rain/3000.0) - 0.25*(1.0 - drainage), 0.70, 1.20))

            for seg in range(1, RNG.integers(7, 14) + 1):
                ac    = max(45.0, ac_road + RNG.normal(0, 11))
                aadt  = aadt_road*RNG.uniform(0.85, 1.15)
                age   = max(0.5, age_road + RNG.normal(0, 0.6))
                rn    = max(150.0, rain + RNG.normal(0, 60))
                tp    = temp + RNG.normal(0, 0.8)

                sn    = float(structural_number(ac, base_mm, subbase, m, m))
                cap   = float(allowable_esals(sn, mr_psi))*quality
                env   = float(env_multiplier(tp, rn))
                e_now = annual_esals(aadt, truck_pct, tf)
                e_0   = e_now/np.power(1.0 + growth, age)
                used  = env*(e_now - e_0)/growth              # Miner's rule, with growth

                rsl_load = remaining_years(cap, used, e_now*env, growth)
                life_env = float(climate_life(tp, rn, quality))
                rsl      = float(np.clip(min(rsl_load, life_env - age), 0.0, 25.0))

                # observed distress: whichever mechanism has consumed more
                dmg_load = used/cap
                dmg      = float(np.clip(max(dmg_load, age/life_env), 0.0, 1.6))

                # Two kinds of cracking, and only one of them is structural.
                #   fatigue - load associated, the surface expression of consumed capacity
                #   thermal - block cracking from binder oxidation: it ages the surface,
                #             not the structure, and it is worst where it is hot and dry
                fatigue = 46.0*float(np.clip(dmg_load, 0.0, 1.5))**2.2
                thermal = (0.60*max(0.0, age - 6.0)*(1.0 + 0.05*(tp - 27.0))
                           * (1.25 if rn < 700 else 1.0))
                crack   = ((fatigue + thermal)*(2.0 - quality)*rater + RNG.normal(0, 2.2))
                iri   = (1.8 + 3.4*dmg + (0.6 if cls == "District Road" else 0.0)
                         + RNG.normal(0, 0.22))
                defl  = ((0.12 + 1.0/sn)*np.sqrt(7000.0/mr_psi)*(1.0 + 0.40*dmg_load)
                         + RNG.normal(0, 0.025))

                rows.append(dict(
                    segment_id=f"{road}/{seg:02d}", road_id=road, road_class=cls,
                    district=district, climate_zone=zone, chainage_km=float(seg),
                    traffic_volume_vpd=round(aadt, -1),
                    pavement_thickness_mm=round(ac, 1),
                    pavement_age_years=round(age, 1),
                    rainfall_mm_year=round(rn, 0),
                    avg_temperature_c=round(tp, 1),
                    crack_density_pct=round(float(np.clip(crack, 0.2, 72.0)), 1),
                    surface_roughness_iri=round(float(np.clip(iri, 1.4, 9.0)), 2),
                    deflection_mm=round(float(np.clip(defl, 0.12, 2.2)), 3),
                    years_since_maintenance=int(min(age, RNG.integers(1, 10))),
                    remaining_life_years=round(rsl, 2)))
    return pd.DataFrame(rows)

survey = build_survey()

# --- the file is not clean, and neither is any real one ---------------------
def spoil(df):
    df = df.copy()
    n  = len(df)
    df.loc[RNG.choice(n, 18, replace=False), "crack_density_pct"]     = -1.0    # survey van error code
    df.loc[RNG.choice(n, 14, replace=False), "pavement_thickness_mm"] = 0.0     # core record missing
    df.loc[RNG.choice(n, 26, replace=False), "rainfall_mm_year"]      = np.nan  # met station gap
    df.loc[RNG.choice(n,  9, replace=False), "traffic_volume_vpd"]    = 0.0     # counter failure
    idx = RNG.choice(n, 11, replace=False)
    df.loc[idx, "pavement_age_years"] = -df.loc[idx, "pavement_age_years"]      # construction-year typo
    kad = df["district"] == "Kadapa"                                            # reported in Fahrenheit
    df.loc[kad, "avg_temperature_c"] = (df.loc[kad, "avg_temperature_c"]*9/5 + 32).round(1)
    dup = df.loc[RNG.choice(n, 12, replace=False)]                              # surveyed twice
    return pd.concat([df, dup], ignore_index=True).sample(frac=1.0, random_state=7).reset_index(drop=True)

spoil(survey).to_csv("pavement_condition_survey.csv", index=False)
print("pavement_condition_survey.csv written -", len(survey), "segments")
'''),
          ("co", r'''
df = pd.read_csv("pavement_condition_survey.csv")

print(f"{len(df):,} records  x  {df.shape[1]} columns\n")
df.head(8)
''')],
    built="""The agency's condition survey, loaded — every segment on the network with its structure, loading,
climate, measured distress and recorded outcome.""",
    takeaway="""The dataset is a network survey export: one row per kilometre, assembled from four separate systems.""",
)

step(
    id="inspect-data", phase=3, icon="🧐", ai_icon="🔎",
    civil="Checking The Survey Before Trusting It", ai="Data Inspection",
    tech="Range checks, missing values, duplicates, units",
    site="""Before a design office uses a survey, it checks it. Are the thicknesses credible? Is any segment listed
twice? Did the met station report every month? Did a district submit in the wrong units?""",
    challenge="""Instruments do not report 'missing'. They report a number — `-1`, `0`, `999` — and a spreadsheet cannot
tell that apart from a measurement. A crack density of −1% is obviously wrong to an engineer and perfectly
acceptable to a model, which will happily learn from it.""",
    ai_link="""Data inspection is the engineering judgement stage of machine learning. Every check below is a check a
pavement engineer already knows how to make; the only new part is doing it in code, on every column, every
time.""",
    bridge=[("Verify the survey", "describe(), isna()"),
            ("Impossible values", "Range checks"),
            ("Wrong units", "Distribution by district")],
    body=[("co", r'''
FEATURES = ["traffic_volume_vpd", "pavement_thickness_mm", "pavement_age_years",
            "rainfall_mm_year", "avg_temperature_c", "crack_density_pct"]
TARGET   = "remaining_life_years"

df[FEATURES + [TARGET]].describe().T.round(2)
'''),
          ("co", r'''
print("SURVEY HEALTH CHECK\n")

LIMITS = {"traffic_volume_vpd":    (100,  60000, "vehicles/day"),
          "pavement_thickness_mm": (40,   400,   "mm of bituminous layers"),
          "pavement_age_years":    (0,    40,    "years"),
          "rainfall_mm_year":      (100,  4000,  "mm/year"),
          "avg_temperature_c":     (5,    45,    "deg C"),
          "crack_density_pct":     (0,    80,    "% of surface area")}

for col, (lo, hi, unit) in LIMITS.items():
    bad  = int(((df[col] < lo) | (df[col] > hi)).sum())
    miss = int(df[col].isna().sum())
    flag = "  <-- CHECK" if bad or miss else ""
    print(f"  {col:<24} {bad:>4} outside [{lo}, {hi}] {unit:<24} {miss:>4} missing{flag}")

dups = int(df["segment_id"].duplicated().sum())
print(f"\n  duplicated segment_id                                                {dups:>4}")

print("\nTemperature by district - one of these is not like the others:")
print(df.groupby("district")["avg_temperature_c"].agg(["min", "median", "max"]).round(1).to_string())
'''),
          ("md", r"""
Four distinct faults, and each needs a different response:

| Fault | Evidence | What it actually is |
|---|---|---|
| `crack_density_pct = -1` | below a physical floor of 0 | the survey vehicle's error code |
| `pavement_thickness_mm = 0` | a road cannot be 0 mm thick | the core record was never entered |
| `rainfall_mm_year` blank | genuinely absent | a gap in the met station series |
| Kadapa temperatures in the 70s and 80s | median more than 50° above every other district | **degrees Fahrenheit** |

The last one is the dangerous one. Every value is individually plausible. Only the comparison across
districts exposes it — and a model trained on it would conclude that hot districts have long-lived
pavements.
""")],
    built="""A documented health check of the survey, with every fault identified and named before a single model
was fitted.""",
    takeaway="""An instrument never reports 'missing' — it reports a number, and only a range check catches it.""",
)

step(
    id="clean", phase=4, icon="🧹", ai_icon="🧼",
    civil="Correcting The Record", ai="Data Cleaning",
    tech="Convert, repair, impute, or drop — one decision per fault",
    site="""The design office does not throw away a survey because six columns have problems. It corrects what can
be corrected and excludes what cannot, and it writes down which it did.""",
    challenge="""The temptation is to delete every imperfect row. On this file that would discard the Kadapa district
entirely — a whole climate zone — because of a unit conversion that takes one line to fix.""",
    ai_link="""Cleaning is not deletion. Four different faults get four different treatments, and the choice between
them is an engineering judgement about **what the missing value would have been**.""",
    bridge=[("Fahrenheit submission", "Convert the units"),
            ("Missing rainfall", "Impute from the district"),
            ("Missing core record", "Drop — cannot be guessed"),
            ("Segment surveyed twice", "Deduplicate")],
    body=[("co", r'''
raw_n = len(df)
clean = df.copy()
log   = []

# 1. Units. A median above 55 can only be Fahrenheit - convert, do not delete.
for dist, grp in clean.groupby("district"):
    if grp["avg_temperature_c"].median() > 55:
        clean.loc[clean["district"] == dist, "avg_temperature_c"] = \
            ((grp["avg_temperature_c"] - 32.0)*5.0/9.0).round(1)
        log.append(f"{dist}: {len(grp)} records converted from Fahrenheit to Celsius")

# 2. Error codes become honest missing values.
clean.loc[clean["crack_density_pct"] < 0, "crack_density_pct"]        = np.nan
clean.loc[clean["pavement_thickness_mm"] <= 0, "pavement_thickness_mm"] = np.nan
clean.loc[clean["traffic_volume_vpd"] <= 0, "traffic_volume_vpd"]     = np.nan
clean.loc[clean["pavement_age_years"] < 0, "pavement_age_years"]      = np.nan

# 3. Duplicates. The same kilometre cannot appear twice in one survey.
before = len(clean)
clean  = clean.drop_duplicates(subset="segment_id", keep="first")
log.append(f"deduplicated: {before - len(clean)} repeated segment records removed")

# 4. Impute what climate can supply; drop what only a core can supply.
miss_rain = int(clean["rainfall_mm_year"].isna().sum())
clean["rainfall_mm_year"] = clean.groupby("district")["rainfall_mm_year"] \
                                 .transform(lambda s: s.fillna(s.median()))
log.append(f"imputed: {miss_rain} rainfall values filled from the district median")

before = len(clean)
clean  = clean.dropna(subset=["pavement_thickness_mm", "traffic_volume_vpd",
                              "pavement_age_years", "crack_density_pct"])
log.append(f"dropped: {before - len(clean)} records with no recoverable structure, traffic, age or condition")

print("CLEANING LOG\n")
for entry in log:
    print("  *", entry)
print(f"\n  {raw_n:,} records in  ->  {len(clean):,} records out  "
      f"({(raw_n - len(clean))/raw_n:.1%} removed)")
'''),
          ("md", r"""
### Why rainfall was imputed and thickness was not

Both were missing. They were treated differently, and the reason is engineering, not statistics.

- **Rainfall is a district property.** Every segment in Chittoor sees roughly the same rainfall, so the
  district median is a defensible estimate of a value that was never in doubt.
- **Thickness is a segment property.** It is whatever that contractor laid on that kilometre. The network
  median tells you nothing about it, and filling it in would invent a structure that may not exist.

Impute a value you could have looked up. Drop a value only a measurement could have supplied.
""")],
    built="""A clean, deduplicated survey with every correction logged and every deletion justified.""",
    takeaway="""Impute what you could have looked up; drop what only a measurement could have told you.""",
)


# ---------------------------------------------- PHASE 5 · PREPARING THE DATA
step(
    id="features", phase=4, icon="📏", ai_icon="⚖️",
    civil="Putting Measurements On Comparable Scales", ai="Feature Scaling",
    tech="StandardScaler: subtract the mean, divide by the standard deviation",
    site="""The six inputs are measured in six units. Traffic runs to tens of thousands. Temperature sits near
thirty. Crack density is a percentage.""",
    challenge="""To an engineer this is trivial — everyone knows 22,000 vehicles and 31 °C are not comparable numbers.
To a distance-based or coefficient-based algorithm they are just numbers, and the largest one dominates
simply because it is large.""",
    ai_link="""Scaling puts every feature in the same currency: standard deviations from its own mean. Linear
Regression needs it if the coefficients are to be read against each other. Trees do not — they split on
order, not magnitude — which is itself worth knowing.""",
    bridge=[("Six different units", "Six different scales"),
            ("Standardise the record", "StandardScaler"),
            ("Compare like with like", "Comparable coefficients")],
    body=[("co", r'''
from sklearn.preprocessing import StandardScaler

X_all = clean[FEATURES].to_numpy(float)
y_all = clean[TARGET].to_numpy(float)

print("BEFORE SCALING - the six inputs are not on comparable scales\n")
print(f"{'feature':<24}{'mean':>12}{'std dev':>12}{'min':>10}{'max':>10}")
for i, f in enumerate(FEATURES):
    c = X_all[:, i]
    print(f"{f:<24}{c.mean():>12,.1f}{c.std():>12,.1f}{c.min():>10,.1f}{c.max():>10,.1f}")

ratio = X_all[:, FEATURES.index("traffic_volume_vpd")].std()/X_all[:, FEATURES.index("crack_density_pct")].std()
print(f"\nTraffic volume varies about {ratio:,.0f} times as widely as crack density, in raw units.")
print("Nothing about pavement engineering says it is that many times more important.")
'''),
          ("co", r'''
fig = make_subplots(rows=2, cols=3, subplot_titles=[f.replace("_", " ") for f in FEATURES])
for i, f in enumerate(FEATURES):
    fig.add_trace(go.Histogram(x=clean[f], marker_color=AMBER, nbinsx=40, showlegend=False),
                  row=i//3 + 1, col=i % 3 + 1)
fig.update_layout(height=520, template="plotly_white",
                  title="The six model inputs across the cleaned network")
fig.show()

fig = go.Figure(go.Histogram(x=clean[TARGET], marker_color=CYAN, nbinsx=50))
fig.update_layout(title="What we are predicting: remaining service life",
                  xaxis_title="remaining service life (years)", yaxis_title="segments",
                  template="plotly_white", height=340)
fig.show()

print(f"remaining service life:  median {clean[TARGET].median():.1f} years, "
      f"mean {clean[TARGET].mean():.1f}, range {clean[TARGET].min():.1f} to {clean[TARGET].max():.1f}")
print(f"segments already at or past terminal condition (0 years): "
      f"{(clean[TARGET] <= 0.05).mean():.1%} of the network")
''')],
    built="""The six inputs profiled, and the target distribution seen for the first time — including the segments
that are already out of life.""",
    takeaway="""Scaling makes coefficients comparable; it does not make features important.""",
)

step(
    id="split", phase=4, icon="✂️", ai_icon="🧪",
    civil="Holding Back Roads, Not Rows", ai="The Train/Test Split",
    tech="GroupShuffleSplit by road_id — segments of one road never straddle the split",
    site="""To know whether the model works, it must be tested on segments it has never seen. The obvious way is to
hold back a random 30% of the rows.""",
    challenge="""The obvious way is wrong here. Kilometre 6 and kilometre 7 of the same highway share a subgrade, a
climate, a contractor, a construction year and a traffic stream. They are nearly the same pavement.

Split at random and one goes into training while its near-twin goes into testing. The score that comes
back measures memory, not prediction.""",
    ai_link="""Split by **road**, not by segment. Every kilometre of a given road lands entirely in training or
entirely in testing — which is exactly the situation the model faces in service, where it is asked about a
road nobody has surveyed yet.""",
    bridge=[("Adjacent kilometres are alike", "Grouped samples"),
            ("Hold back whole roads", "GroupShuffleSplit"),
            ("A road you have not surveyed", "The honest test set")],
    body=[("co", r'''
from sklearn.model_selection import GroupShuffleSplit, train_test_split

groups = clean["road_id"].to_numpy()
gss    = GroupShuffleSplit(n_splits=1, test_size=0.30, random_state=42)
tr, te = next(gss.split(X_all, y_all, groups))

X_tr, X_te = X_all[tr], X_all[te]
y_tr, y_te = y_all[tr], y_all[te]

scaler = StandardScaler().fit(X_tr)          # fitted on TRAIN only - the test set is unseen
X_tr_s, X_te_s = scaler.transform(X_tr), scaler.transform(X_te)

print("THE SPLIT\n")
print(f"  training   {len(tr):>6,} segments   on {clean.iloc[tr]['road_id'].nunique():>4} roads")
print(f"  testing    {len(te):>6,} segments   on {clean.iloc[te]['road_id'].nunique():>4} roads")
print(f"  roads appearing in both sets: "
      f"{len(set(clean.iloc[tr]['road_id']) & set(clean.iloc[te]['road_id']))}")
'''),
          ("co", r'''
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error

# How much would the random-row split have flattered us? Measure it, do not assume it.
Xr_tr, Xr_te, yr_tr, yr_te = train_test_split(X_all, y_all, test_size=0.30, random_state=42)

probe_random = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1).fit(Xr_tr, yr_tr)
probe_group  = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1).fit(X_tr, y_tr)

r2_random = r2_score(yr_te, probe_random.predict(Xr_te))
r2_group  = r2_score(y_te,  probe_group.predict(X_te))
mae_random = mean_absolute_error(yr_te, probe_random.predict(Xr_te))
mae_group  = mean_absolute_error(y_te,  probe_group.predict(X_te))

print("THE SAME MODEL, TWO WAYS OF SPLITTING THE SAME DATA\n")
print(f"{'split':<34}{'R2':>10}{'MAE (years)':>16}")
print(f"{'random rows (leaks)':<34}{r2_random:>10.3f}{mae_random:>16.2f}")
print(f"{'grouped by road (honest)':<34}{r2_group:>10.3f}{mae_group:>16.2f}")
print(f"\nThe random split flatters the same model by {r2_random - r2_group:+.3f} R2, and reports")
print(f"{mae_group - mae_random:.2f} years less error than it will actually deliver on a new road.")
print("Every number from here on uses the grouped split.")
''')],
    built="""An honest test set: 30% of the *roads* held back entirely, and a measurement of how much the naive
split would have overstated performance.""",
    takeaway="""Adjacent kilometres are near-duplicates — split by road or the score measures memory.""",
)


# ---------------------------------------------- PHASE 6 · LEARNING DETERIORATION
step(
    id="baseline", phase=5, icon="📅", ai_icon="📏",
    civil="The Rule The Agency Already Runs", ai="The Baseline",
    tech="Remaining life = design life − age",
    site="""Most agencies run a fixed cycle: assume a design life, subtract the age, and resurface when the number
reaches zero. Some add a condition trigger — resurface early if cracking passes a threshold.""",
    challenge="""The rule ignores traffic, thickness and climate entirely. Two segments the same age get the same answer
whether one carries 40,000 vehicles a day and the other carries 900.""",
    ai_link="""Before claiming a model helps, measure what it must beat. A baseline that is never computed is a
baseline that is always beaten — in the presentation, if nowhere else.""",
    bridge=[("The fixed cycle", "The baseline predictor"),
            ("Its error, in years", "MAE"),
            ("The bar to clear", "Every later model is compared to it")],
    body=[("co", r'''
DESIGN_LIFE = 20.0

age_te   = X_te[:, FEATURES.index("pavement_age_years")]
crack_te = X_te[:, FEATURES.index("crack_density_pct")]

rule_age  = np.clip(DESIGN_LIFE - age_te, 0, 25)
rule_cond = np.where(crack_te > 25.0, np.minimum(rule_age, 3.0), rule_age)

def score(name, pred, truth=y_te):
    mae  = mean_absolute_error(truth, pred)
    rmse = float(np.sqrt(np.mean((truth - pred)**2)))
    r2   = r2_score(truth, pred)
    print(f"{name:<38}{mae:>9.2f}{rmse:>9.2f}{r2:>9.3f}")
    return dict(model=name, mae=mae, rmse=rmse, r2=r2)

print("THE RULES THE AGENCY ALREADY HAS\n")
print(f"{'predictor':<38}{'MAE':>9}{'RMSE':>9}{'R2':>9}")
results = [score("fixed 20-year cycle", rule_age),
           score("fixed cycle + cracking trigger", rule_cond)]

print(f"\nThe fixed cycle is wrong by {results[0]['mae']:.1f} years on average.")
print("On a 20-year asset that is not a rounding error - it is the difference between")
print("a surface seal and a reconstruction.")
''')],
    built="""A measured baseline in the same units as everything that follows, so later claims can be checked
rather than asserted.""",
    takeaway="""The fixed cycle ignores traffic, structure and climate — and its error says so.""",
)

step(
    id="linear", phase=5, icon="📈", ai_icon="🧮",
    civil="A First Model: Everything Adds Up", ai="Linear Regression",
    tech="ŷ = b₀ + b₁·traffic + b₂·thickness + … + b₆·cracking",
    site="""The first honest attempt: assume each factor contributes a fixed number of years per unit, independent
of everything else. Thicker adds life. Older subtracts it. More cracking subtracts more.""",
    challenge="""Pavement deterioration is not additive. Damage goes as load to the fourth power. Capacity rises far
faster than thickness. And the *governing mechanism itself changes* — a district road fails from ageing,
a national highway fails from trucks.

A straight line has one coefficient per factor. It cannot say 'traffic matters here and not there'.""",
    ai_link="""Fit it anyway, and read the coefficients. They are interpretable in engineering units — years of life
per standard deviation of each input — and that interpretability is exactly why linear regression is
still the right place to start.""",
    bridge=[("Each factor adds or subtracts", "One coefficient each"),
            ("Effects are independent", "No interaction terms"),
            ("Fit the best straight line", "Least squares")],
    body=[("co", r'''
from sklearn.linear_model import LinearRegression

lin = LinearRegression().fit(X_tr_s, y_tr)
pred_lin = lin.predict(X_te_s)

print(f"{'predictor':<38}{'MAE':>9}{'RMSE':>9}{'R2':>9}")
results.append(score("Linear Regression", pred_lin))

print("\nCOEFFICIENTS - years of remaining life per standard deviation of each input\n")
order = np.argsort(-np.abs(lin.coef_))
for i in order:
    print(f"  {FEATURES[i]:<26}{lin.coef_[i]:>+8.2f} years")
print(f"  {'(intercept)':<26}{lin.intercept_:>+8.2f} years")
'''),
          ("md", r"""
**Every one of the six signs is engineering-correct**, and that is worth pausing on. Age, traffic,
cracking, rainfall and temperature all subtract life; thickness adds it. Nobody told the model any of
that — it recovered all six from the survey, and between them they are the demand side and the capacity
side of the AASHTO equation.

Temperature comes out smallest. That is not evidence that heat is harmless. Most of what temperature does
to a pavement has **already been recorded in the crack density column**, which the model can read
directly — so there is little left for the temperature coefficient to explain.

> A coefficient is not an effect. It is what is left of an effect after every other column has taken its
> share.

Now look at what the straight line is forced to claim:

- **One** traffic coefficient for the entire network — the same years-per-vehicle on a district road as on
  a national highway.
- **No** interaction between thickness and traffic, so a thin pavement under heavy trucks is treated as
  the simple sum of 'thin' and 'heavy'.
- A straight-line response to cracking, when the serviceability curve is anything but straight.

The residual plot below shows what that costs.
"""),
          ("co", r'''
resid = y_te - pred_lin
fig = make_subplots(rows=1, cols=2, subplot_titles=[
    "Linear Regression: predicted vs actual", "Where it goes wrong"])
fig.add_trace(go.Scatter(x=y_te, y=pred_lin, mode="markers",
                         marker=dict(color=VIOLET, size=5, opacity=0.45), showlegend=False),
              row=1, col=1)
fig.add_trace(go.Scatter(x=[0, 25], y=[0, 25], mode="lines",
                         line=dict(color=MUTED, dash="dash"), showlegend=False), row=1, col=1)
fig.add_trace(go.Scatter(x=y_te, y=resid, mode="markers",
                         marker=dict(color=RED, size=5, opacity=0.45), showlegend=False), row=1, col=2)
fig.add_hline(y=0, line_color=MUTED, row=1, col=2)
fig.update_xaxes(title_text="actual remaining life (years)", row=1, col=1)
fig.update_yaxes(title_text="predicted (years)", row=1, col=1)
fig.update_xaxes(title_text="actual remaining life (years)", row=1, col=2)
fig.update_yaxes(title_text="error (years)", row=1, col=2)
fig.update_layout(height=420, template="plotly_white")
fig.show()

lo = y_te < 5
hi = y_te > 15
print(f"mean error on segments with under 5 years left : {resid[lo].mean():+.2f} years")
print(f"mean error on segments with over 15 years left : {resid[hi].mean():+.2f} years")
print("\nA positive error means the model is optimistic - it promises life the pavement does not have.")
''')],
    built="""A fitted, interpretable linear model — with its coefficients in engineering units and its structural
weakness visible in the residuals.""",
    takeaway="""Linear regression gets every sign right and still misses, because deterioration is not additive.""",
)

step(
    id="forest", phase=5, icon="🌲", ai_icon="🌳",
    civil="Letting The Data Split Itself", ai="Random Forest Regression",
    tech="Many decision trees on random subsets, averaged",
    site="""A pavement engineer does not apply one formula to the whole network. They reason in cases: *thin section
under heavy trucks* is one case, *thick section in a wet district* is another, and each has its own rule
of thumb.""",
    challenge="""Writing those cases down as a rulebook fails for the same reason the fixed cycle fails — the thresholds
are different for every road class, every climate zone and every structure, and nobody can enumerate
them.""",
    ai_link="""A decision tree discovers the cases from the data: it repeatedly splits the network on whichever
measurement separates long-lived from short-lived segments best. A **random forest** grows hundreds of
such trees on random subsets and averages them, which stops any one tree from over-fitting its own
sample.""",
    bridge=[("Reasoning in cases", "Tree splits"),
            ("Different rules per road type", "Interactions, learned"),
            ("A second opinion", "Averaging many trees")],
    body=[("co", r'''
rf = RandomForestRegressor(n_estimators=400, min_samples_leaf=2,
                           random_state=42, n_jobs=-1).fit(X_tr, y_tr)
pred_rf = rf.predict(X_te)

print(f"{'predictor':<38}{'MAE':>9}{'RMSE':>9}{'R2':>9}")
results.append(score("Random Forest", pred_rf))

print(f"\nAgainst the fixed cycle : {results[0]['mae'] - results[-1]['mae']:.2f} years less error")
print(f"Against linear regression: {results[2]['mae'] - results[-1]['mae']:.2f} years less error")
print("\nNo feature engineering was added. The same six columns, read differently.")
'''),
          ("co", r'''
# One tree, three levels deep - the cases a tree actually finds.
from sklearn.tree import DecisionTreeRegressor, export_text

small = DecisionTreeRegressor(max_depth=3, random_state=42).fit(X_tr, y_tr)
print("ONE TREE, THREE LEVELS DEEP - read it as an engineer's rulebook\n")
print(export_text(small, feature_names=FEATURES, decimals=1))
'''),
          ("md", r"""
Read that rulebook as an engineer, not as a programmer.

- The first split is the single most informative question about a pavement's future.
- Every branch below it asks a **different** next question. That is an interaction: the relevance of
  traffic depends on what the structure and the cracking already said.
- The value at each leaf is the average remaining life of the training segments that landed there.

This is why the forest beats the straight line. It is not a better formula — it is the freedom to stop
using one formula everywhere.
""")],
    built="""A random forest that discovers deterioration cases from the survey itself and cuts the prediction error
against both the agency rule and the linear model.""",
    takeaway="""Trees earn their keep by asking a different next question in every branch — that is an interaction.""",
)

step(
    id="boosting", phase=5, icon="🪜", ai_icon="🚀",
    civil="Correcting The Previous Estimate", ai="Gradient Boosting & XGBoost",
    tech="Each new tree is fitted to the error the previous trees left behind",
    site="""A design office revises. The first estimate goes out, the reviewer marks where it was optimistic, the
next revision corrects exactly those cases.""",
    challenge="""A random forest cannot do that. Its trees are grown independently and averaged — none of them knows
where the others were wrong.""",
    ai_link="""Gradient boosting builds trees **in sequence**, each one fitted to the residual error of everything
before it. On structured engineering tables with strong interactions, this is usually the strongest model
family available, and XGBoost is its most used implementation.""",
    bridge=[("Revise the estimate", "Fit the residual"),
            ("Correct the known misses", "Sequential trees"),
            ("Stop when it stops improving", "Learning rate + n_estimators")],
    body=[("co", r'''
from sklearn.ensemble import GradientBoostingRegressor

gb = GradientBoostingRegressor(n_estimators=400, learning_rate=0.06, max_depth=4,
                               subsample=0.9, random_state=42).fit(X_tr, y_tr)
pred_gb = gb.predict(X_te)

print(f"{'predictor':<38}{'MAE':>9}{'RMSE':>9}{'R2':>9}")
results.append(score("Gradient Boosting", pred_gb))

try:
    from xgboost import XGBRegressor
    xgb = XGBRegressor(n_estimators=600, learning_rate=0.05, max_depth=5,
                       subsample=0.9, colsample_bytree=0.9, random_state=42,
                       n_jobs=-1, verbosity=0).fit(X_tr, y_tr)
    pred_xgb = xgb.predict(X_te)
    results.append(score("XGBoost", pred_xgb))
    HAVE_XGB = True
except Exception as exc:                                    # noqa: BLE001
    print(f"\nxgboost not installed ({type(exc).__name__}) - Gradient Boosting stands in for it.")
    xgb, pred_xgb, HAVE_XGB = gb, pred_gb, False
'''),
          ("co", r'''
res = pd.DataFrame(results).set_index("model").round(3)

fig = make_subplots(rows=1, cols=2, subplot_titles=[
    "mean absolute error (years) - lower is better", "R2 - higher is better"])
colors = [MUTED, MUTED, VIOLET, GREEN, CYAN, AMBER][:len(res)]
fig.add_trace(go.Bar(x=res.index, y=res["mae"], marker_color=colors,
                     text=res["mae"].round(2), textposition="outside", showlegend=False), row=1, col=1)
fig.add_trace(go.Bar(x=res.index, y=res["r2"], marker_color=colors,
                     text=res["r2"].round(3), textposition="outside", showlegend=False), row=1, col=2)
fig.update_layout(height=430, template="plotly_white",
                  title="Every predictor, on the same held-out roads")
fig.show()

best = res["mae"].idxmin()
print(res.to_string())
print(f"\nBest on held-out roads: {best}")

rule_mae, lin_mae, best_mae = (res.loc["fixed 20-year cycle", "mae"],
                               res.loc["Linear Regression", "mae"], res.loc[best, "mae"])
ml_spread = res.loc[["Linear Regression", "Random Forest",
                     "Gradient Boosting", "XGBoost"], "mae"]
print(f"  rule -> the simplest model      {rule_mae - lin_mae:>6.2f} years of error removed")
print(f"  simplest model -> the best one  {lin_mae - best_mae:>6.2f} years")
print(f"  best model -> second best       {ml_spread.nsmallest(2).diff().iloc[-1]:>6.2f} years")
print(f"\n  total, rule -> best             {rule_mae - best_mae:>6.2f} years")
'''),
          ("md", r"""
Two things in that chart are worth more than the winner.

1. **Read the three step sizes printed above.** Going from the agency's rule to the *simplest* model, and
   from that to the best one, both remove real error. Going from the best model to the second best removes
   almost none. Most of the value in this project came from using traffic, structure and climate at all —
   and from letting the model bend — not from which ensemble won.
2. **Diminishing returns are visible, and they arrive quickly.** That is the normal shape of these
   projects, and it is a useful thing to tell a client before they ask for a neural network. The next
   honest improvement on this problem is better data, not a bigger model — which is exactly what the
   instrumentation step goes on to test.
""")],
    built="""A sequential-correction model and a like-for-like comparison of every predictor on the same held-out
roads.""",
    takeaway="""The big win is using the engineering data at all; the choice of algorithm is the small win.""",
)


# ---------------------------------------------- PHASE 7 · READING THE MODEL
step(
    id="importance", phase=6, icon="🧭", ai_icon="📊",
    civil="Which Factors Actually Drive Pavement Life", ai="Feature Importance",
    tech="Permutation importance: shuffle one column, measure the damage",
    site="""An engineer reviewing this system will ask one question before any other: does it agree with what we
know about pavements? If it ranks temperature above cracking, it has learned something wrong.""",
    challenge="""A model that is accurate but inexplicable cannot be signed off. Somebody has to defend the maintenance
programme in front of an audit committee, and 'the model said so' is not a defence.""",
    ai_link="""Permutation importance is the honest measure. Shuffle one column in the test set, destroying its
information while leaving everything else intact, and see how much the error rises. Big rise, important
feature.""",
    bridge=[("Which factor governs?", "Feature importance"),
            ("Does it match the standard?", "Sanity check against AASHTO"),
            ("Defend the programme", "An explainable ranking")],
    body=[("co", r'''
from sklearn.inspection import permutation_importance

best_name  = res["mae"].idxmin()
model      = {"Linear Regression": lin, "Random Forest": rf,
              "Gradient Boosting": gb, "XGBoost": xgb}.get(best_name, rf)
X_best     = X_te_s if best_name == "Linear Regression" else X_te
X_best_tr  = X_tr_s if best_name == "Linear Regression" else X_tr

perm = permutation_importance(model, X_best, y_te, n_repeats=12,
                              random_state=42, scoring="neg_mean_absolute_error")
imp = pd.DataFrame({"feature": FEATURES,
                    "extra_error_years": perm.importances_mean,
                    "sd": perm.importances_std}).sort_values("extra_error_years")

fig = go.Figure(go.Bar(x=imp["extra_error_years"], y=imp["feature"].str.replace("_", " "),
                       orientation="h", marker_color=CYAN,
                       error_x=dict(type="data", array=imp["sd"], color=MUTED)))
fig.update_layout(title=f"Permutation importance ({best_name}) - extra error when a column is shuffled",
                  xaxis_title="added mean absolute error (years)", template="plotly_white", height=400)
fig.show()

print("HOW MUCH EACH MEASUREMENT IS WORTH, IN YEARS OF ACCURACY\n")
for _, r in imp.sort_values("extra_error_years", ascending=False).iterrows():
    print(f"  {r['feature']:<26}{r['extra_error_years']:>7.2f} years")
'''),
          ("md", r"""
### Does it agree with pavement engineering?

Check the ranking against the design standard, not against intuition.

- **Crack density and age lead, close together, and well clear of the rest.** Both are correct. Cracking
  is the observed summary of all damage that has already occurred, *including damage from causes no other
  column recorded* — the blocked drain, the weak subgrade, the bad construction batch. Age sets how much
  of the life has been spent. Between them they carry most of the answer, and neither is sufficient alone:
  cracking says how far gone the pavement is, age says how quickly it got there.
- **Rainfall, traffic and thickness contribute much less individually.** That is not the same as being
  unimportant, and the reason is the standard caveat on this method:

> **Permutation importance under-credits correlated features.** Shuffling thickness alone barely hurts,
> because traffic, age and cracking between them still imply roughly what the structure must be. Shuffle
> the *group* and the error would rise sharply. Read this chart as "what is uniquely mine", not "what I am
> worth".

- **Temperature comes out last.** Its effect reaches the model through two other columns: crack density,
  which already contains the thermal cracking it caused, and rainfall, which in this network largely
  identifies the climate zone. A feature at the bottom of this chart is not a feature to delete on sight —
  it may simply be one whose job is being done by its neighbours.

Nothing in that ranking would surprise a pavement engineer. That is the point: it is the evidence that
the model learned deterioration rather than an artefact of the survey.
""")],
    built="""A defensible ranking of the six measurements by how much accuracy each one contributes, cross-checked
against the design standard.""",
    takeaway="""Cracking dominates because it carries information about the causes nobody measured.""",
)

step(
    id="explain", phase=6, icon="🔬", ai_icon="🕵️",
    civil="Explaining One Segment's Prediction", ai="Local Sensitivity",
    tech="Vary one input at a time, hold the rest at their surveyed values",
    site="""Network-level importance does not answer the question an engineer actually asks in a review: *why does
this kilometre have five years and that one has twelve?*""",
    challenge="""The two segments differ on all six inputs at once. Attribution needs the effects separated, on this
segment, at these values — not on the network average.""",
    ai_link="""Hold the segment fixed and move one input at a time. The change in predicted life is that input's local
contribution. It is simple, it is exact for the model, and it produces a sentence an engineer can check
against their own experience.""",
    bridge=[("Why this kilometre?", "Local explanation"),
            ("Change one thing", "One-at-a-time sensitivity"),
            ("A defensible sentence", "Reasons attached to the number")],
    body=[("co", r'''
def predict_life(row_dict, mdl=None, name=None):
    """Predicted remaining service life (years) for one segment given the six inputs."""
    mdl  = model if mdl is None else mdl
    name = best_name if name is None else name
    x    = np.array([[row_dict[f] for f in FEATURES]], float)
    if name == "Linear Regression":
        x = scaler.transform(x)
    return float(np.clip(mdl.predict(x)[0], 0.0, 25.0))

SEGMENT = dict(traffic_volume_vpd=22000, pavement_thickness_mm=240, pavement_age_years=12,
               rainfall_mm_year=1100, avg_temperature_c=31.0, crack_density_pct=18.0)

base = predict_life(SEGMENT)
print("SEGMENT SH-021/07\n")
for k, v in SEGMENT.items():
    print(f"  {k:<26}{v:>10,.1f}")
print(f"\n  predicted remaining service life{base:>17.1f} years")
'''),
          ("co", r'''
STEPS_OAT = {"traffic_volume_vpd":    (-12000, +12000, "vehicles/day"),
             "pavement_thickness_mm": (-60,    +60,    "mm"),
             "pavement_age_years":    (-5,     +5,     "years"),
             "rainfall_mm_year":      (-600,   +600,   "mm/year"),
             "avg_temperature_c":     (-5,     +5,     "deg C"),
             "crack_density_pct":     (-10,    +10,    "%")}

rows = []
for f, (dn, up, unit) in STEPS_OAT.items():
    lo_case, hi_case = dict(SEGMENT), dict(SEGMENT)
    lo_case[f] += dn
    hi_case[f] += up
    rows.append(dict(feature=f, unit=unit, change=f"{dn:+g} / {up:+g}",
                     low=predict_life(lo_case) - base, high=predict_life(hi_case) - base))
sens = pd.DataFrame(rows)

fig = go.Figure()
fig.add_trace(go.Bar(y=sens["feature"].str.replace("_", " "), x=sens["low"], orientation="h",
                     marker_color=GREEN, name="input decreased"))
fig.add_trace(go.Bar(y=sens["feature"].str.replace("_", " "), x=sens["high"], orientation="h",
                     marker_color=RED, name="input increased"))
fig.update_layout(barmode="relative", template="plotly_white", height=420,
                  title=f"What moves this segment's {base:.1f} years",
                  xaxis_title="change in predicted remaining life (years)")
fig.show()

print("LOCAL SENSITIVITY - this segment only\n")
print(sens.round(2).to_string(index=False))
'''),
          ("md", r"""
Two things to read off that table, and the second one is the more important.

**1. Cracking and age are the binding constraints on this segment.** Move either and the prediction moves
by years. That is the sentence that goes in the review file:

> *SH-021/07 is predicted at the value printed above. Cracking and age are binding; a further 10
> percentage points of cracking removes the years shown in the chart. At 240 mm the structure is not the
> constraint. The segment is a candidate for preventive treatment before the deterioration curve turns.*

**2. Some rows are flat, and one or two may point the 'wrong' way. Neither is a bug.**

The flat ones first. A tree ensemble is **piecewise constant** — it predicts in bands, so a small change
can land in the same leaves and register almost nothing, while a large change crosses a threshold and
jumps.

The inverted ones matter more, and they are the single most important caveat in this notebook. This table
moves one input **while holding the other five fixed — including cracking**. But crack density is not an
independent input. It is a **consequence** of thickness, traffic, age and climate. Holding it fixed
changes the question being asked:

- *A thicker section showing this much cracking* is in more trouble than a thin one showing the same. It
  should not have cracked at that thickness.
- *A younger pavement showing this much cracking* is deteriorating faster, so it has less life left than
  an older one at the same distress.

Both readings are correct engineering. Statisticians call the mistake **conditioning on a mediator**, and
it is why the next step repeats the thickness comparison properly — letting cracking follow the physics
instead of pinning it.
""")],
    built="""A local, per-segment explanation that converts one predicted number into reasons an engineer can
challenge.""",
    takeaway="""A prediction an engineer cannot interrogate is a prediction they cannot sign.""",
)

step(
    id="instrumentation", phase=6, icon="📡", ai_icon="➕",
    civil="Is More Survey Equipment Worth Buying?", ai="Feature Selection, Priced",
    tech="Re-fit with roughness and deflection added; measure the gain",
    site="""The survey already records roughness (IRI) from the profiler. A falling weight deflectometer measures
structural stiffness directly — but it is slow, expensive, and stops traffic.""",
    challenge="""The agency has to decide whether to fund a deflection survey across the network. That is a capital
decision, and 'more data is better' is not an argument that survives a budget meeting.""",
    ai_link="""Feature selection answers it numerically. Fit the same model with the extra columns and compare the
error on the same held-out roads. The improvement, in years of accuracy, is what the equipment buys.""",
    bridge=[("Buy a deflectometer?", "Add a feature, re-fit"),
            ("What does it buy?", "Change in held-out MAE"),
            ("Justify the capital", "An evidence-based answer")],
    body=[("co", r'''
EXTRA = ["surface_roughness_iri", "deflection_mm"]

Xx_all = clean[FEATURES + EXTRA].to_numpy(float)
Xx_tr, Xx_te = Xx_all[tr], Xx_all[te]

rf_plus = RandomForestRegressor(n_estimators=400, min_samples_leaf=2,
                                random_state=42, n_jobs=-1).fit(Xx_tr, y_tr)
mae_plus = mean_absolute_error(y_te, rf_plus.predict(Xx_te))
mae_six  = mean_absolute_error(y_te, rf.predict(X_te))

# And each addition on its own.
singles = {}
for extra in EXTRA:
    cols = FEATURES + [extra]
    Xs   = clean[cols].to_numpy(float)
    m    = RandomForestRegressor(n_estimators=400, min_samples_leaf=2,
                                 random_state=42, n_jobs=-1).fit(Xs[tr], y_tr)
    singles[extra] = mean_absolute_error(y_te, m.predict(Xs[te]))

# How big does a gain have to be before it is a gain at all? Hold back a DIFFERENT set of
# roads five times over and refit the same six-column model. The spread of that score is
# the uncertainty any claimed improvement has to beat.
def six_col_mae(seed):
    a, b = next(GroupShuffleSplit(n_splits=1, test_size=0.30,
                                  random_state=seed).split(X_all, y_all, groups))
    m = RandomForestRegressor(n_estimators=400, min_samples_leaf=2,
                              random_state=42, n_jobs=-1).fit(X_all[a], y_all[a])
    return mean_absolute_error(y_all[b], m.predict(X_all[b]))

resample = [six_col_mae(s) for s in [42, 7, 13, 21, 99]]
noise    = float(np.std(resample))

print("WHAT EXTRA INSTRUMENTATION BUYS, IN YEARS OF ACCURACY\n")
print(f"{'inputs':<44}{'MAE (years)':>14}{'gain':>10}{'verdict':>16}")
print(f"{'the six survey measurements':<44}{mae_six:>14.3f}{'-':>10}{'baseline':>16}")

def verdict(gain):
    return "real" if gain > 2*noise else ("marginal" if gain > noise else "not measurable")

for k, v in singles.items():
    print(f"{'  + ' + k:<44}{v:>14.3f}{mae_six - v:>+10.3f}{verdict(mae_six - v):>16}")
print(f"{'  + both':<44}{mae_plus:>14.3f}{mae_six - mae_plus:>+10.3f}"
      f"{verdict(mae_six - mae_plus):>16}")

print(f"\nHolding back a different 30% of the ROADS moves the six-column model's MAE")
print(f"between {min(resample):.3f} and {max(resample):.3f} years, a spread of "
      f"+/- {noise:.3f}.")
print("Any 'gain' smaller than that is a different sample of roads, not a better model.")
print()
FWD_SURVEY_COST = 9_000            # rupees per km to run a deflection survey
gain_defl = mae_six - singles["deflection_mm"]
if gain_defl > 2*noise:
    print(f"A deflection survey buys {gain_defl:+.3f} years of accuracy per segment.")
    print(f"At Rs {FWD_SURVEY_COST:,}/km that is Rs "
          f"{FWD_SURVEY_COST/gain_defl:,.0f} per year of accuracy gained - price it")
    print("against the cost of a year of mistimed treatment before recommending it.")
else:
    print(f"VERDICT: on this network, a deflection survey buys {gain_defl:+.3f} years -")
    print(f"inside the {noise:.3f}-year noise floor. It is not worth Rs "
          f"{FWD_SURVEY_COST:,}/km of survey.")
    print("That is a real answer, and it is the one the budget meeting needed.")
'''),
          ("md", r"""
### Why the noise floor came first

The most common mistake in a study like this is to add a column, watch the error drop a few hundredths of
a year, and report an improvement. Hold back a different 30% of the roads and the score moves by more than
that on its own. Nothing was learned.

So the comparison is made against **the spread across resampled road splits**, and only a gain several
times larger than it counts as a gain. Note which noise this is: not the model's randomness, which is
tiny, but the sampling of *which roads you happened to test on*, which is not.

### Reading the verdict

Whatever the table says, read it as an engineering answer about **this network**, not a universal law
about deflectometers:

- **Roughness overlaps with cracking.** Both describe the observed surface. A second opinion on a
  question already answered adds little.
- **Deflection measures the buried layers**, which none of the six can see — but only where the buried
  layers actually *vary*. In this network the base, sub-base and subgrade are relatively uniform, so
  thickness is already a good proxy for capacity and the deflectometer confirms what the file implies.

**On a network with old, variable, poorly documented pavements, the answer would come out differently** —
and the value of this step is that it tells you which network you are on, instead of guessing. A study
that comes back "do not buy it" has saved the price of the equipment, which is a result, not a failure.

""")],
    built="""A priced answer to a capital question: what each additional instrument is worth in years of predictive
accuracy.""",
    takeaway="""'More data is better' is a claim you can measure — so measure it before you buy the equipment.""",
)


# ---------------------------------------------- PHASE 8 · THE PREDICTION
step(
    id="predict", phase=7, icon="🎛️", ai_icon="🔮",
    civil="Predicting A Segment You Have Just Surveyed", ai="Inference",
    tech="Six numbers in, one remaining-life estimate out",
    site="""A survey crew returns from a section. Six measurements go into the system. The engineer wants the
predicted remaining life before the estimate is drafted.""",
    challenge="""The value of a prediction is not the number. It is understanding **why it moves** — because that is
what tells the engineer which intervention would actually extend the life.""",
    ai_link="""This is inference: the trained model applied to a segment it has never seen. Change one input and watch
the answer move, and the deterioration relationships stop being abstract.""",
    bridge=[("A newly surveyed section", "One inference"),
            ("Change an input", "Watch the prediction move"),
            ("Which intervention helps", "Read it off the response")],
    body=[("co", r'''
SCENARIOS = [
    ("New national highway, heavy traffic",
     dict(traffic_volume_vpd=32000, pavement_thickness_mm=285, pavement_age_years=2,
          rainfall_mm_year=900, avg_temperature_c=29.0, crack_density_pct=1.0)),
    ("SH-021/07 - the worked example",
     dict(traffic_volume_vpd=22000, pavement_thickness_mm=240, pavement_age_years=12,
          rainfall_mm_year=1100, avg_temperature_c=31.0, crack_density_pct=18.0)),
    ("Same cracking on a 150 mm section",
     dict(traffic_volume_vpd=22000, pavement_thickness_mm=150, pavement_age_years=12,
          rainfall_mm_year=1100, avg_temperature_c=31.0, crack_density_pct=18.0)),
    ("Same segment, in a wet district",
     dict(traffic_volume_vpd=22000, pavement_thickness_mm=240, pavement_age_years=12,
          rainfall_mm_year=2400, avg_temperature_c=31.0, crack_density_pct=18.0)),
    ("Ageing district road, light traffic",
     dict(traffic_volume_vpd=2200, pavement_thickness_mm=95, pavement_age_years=17,
          rainfall_mm_year=800, avg_temperature_c=33.0, crack_density_pct=31.0)),
    ("Old highway, heavy cracking",
     dict(traffic_volume_vpd=28000, pavement_thickness_mm=210, pavement_age_years=19,
          rainfall_mm_year=1600, avg_temperature_c=32.0, crack_density_pct=48.0)),
]

rows = []
for label, s in SCENARIOS:
    rows.append(dict(scenario=label, **{k: v for k, v in s.items()},
                     predicted_years=round(predict_life(s), 1)))
pd.set_option("display.width", 200)
print("PREDICTED REMAINING SERVICE LIFE\n")
pd.DataFrame(rows).set_index("scenario")
'''),
          ("co", r'''
# The response surface: how remaining life moves with cracking, at three thicknesses.
cracks = np.linspace(0, 55, 60)
fig = go.Figure()
for thick, colr in [(180, RED), (240, AMBER), (300, GREEN)]:
    ys = [predict_life({**SEGMENT, "pavement_thickness_mm": thick, "crack_density_pct": c})
          for c in cracks]
    fig.add_trace(go.Scatter(x=cracks, y=ys, mode="lines", name=f"{thick} mm section",
                             line=dict(color=colr, width=3)))
fig.add_vline(x=SEGMENT["crack_density_pct"], line_dash="dash", line_color=MUTED,
              annotation_text="surveyed cracking")
fig.update_layout(title="Remaining life against measured cracking, for three structures",
                  xaxis_title="crack density (%)", yaxis_title="predicted remaining life (years)",
                  template="plotly_white", height=430)
fig.show()

def at(thick, crack):
    return predict_life({**SEGMENT, "pavement_thickness_mm": thick, "crack_density_pct": crack})

early = at(240, 5) - at(240, 15)        # what the first 10 points of cracking cost
late  = at(240, 35) - at(240, 45)       # what the same 10 points cost later
gap_lo, gap_hi = at(300, 5) - at(180, 5), at(300, 45) - at(180, 45)

print("READ THE CHART WITH THESE THREE NUMBERS\n")
print(f"  1. Cracking 5% -> 15%  costs {early:5.2f} years")
print(f"     Cracking 35% -> 45% costs {late:5.2f} years")
print("     The same ten points of cracking are not worth the same number of years.")
print("     The response is a curve, not a line - which is what a straight-line model")
print("     could never represent.")
print()
print(f"  2. At 5% cracking,  300 mm is worth {gap_lo:5.2f} years more than 180 mm")
print(f"     At 45% cracking, 300 mm is worth {gap_hi:5.2f} years more than 180 mm")
print(f"     Structure is worth {'more' if gap_lo > gap_hi else 'less'} while the surface is still "
      "sound. Once it is broken,")
print("     water is reaching the base and the extra asphalt above it matters less.")
print()
print("  3. The curves have flat steps. A tree ensemble predicts in bands, not on a")
print("     smooth surface - so small input changes can register nothing at all.")
'''),
          ("md", r"""
### The trap in that chart, and how to avoid it

Look at the three thickness curves again. They barely separate — and depending on where you read them, the
thick section may even sit *below* the thin one. Every instinct says that is wrong.

It is not. **The question was incoherent.** Those three curves all hold crack density fixed while changing
the structure, and crack density is not an independent variable — it is what the structure, the traffic
and the climate *produced*. Pinning it asks: *given that this pavement cracked this much anyway, does
thickness help?* And the honest answer is no. A 300 mm section already showing 18% cracking is in more
trouble than a 150 mm section showing the same, because it should not have cracked at all.

The comparison an engineer actually means is: **build it thicker, and let everything downstream follow.**
That is the cell below.
"""),
          ("co", r'''
def physical_crack(traffic, thickness, age, rain, temp, truck_pct=12.0, tf=3.4,
                   growth=0.035, base=250.0, subbase=200.0, mr=8000.0):
    """The crack density this structure WOULD show, from the same physics that built the survey."""
    sn    = float(structural_number(thickness, base, subbase))
    cap   = float(allowable_esals(sn, mr))
    env   = float(env_multiplier(temp, rain))
    e_now = annual_esals(traffic, truck_pct, tf)
    used  = env*(e_now - e_now/np.power(1.0 + growth, age))/growth
    dmg   = used/cap
    fatigue = 46.0*float(np.clip(dmg, 0.0, 1.5))**2.2
    thermal = (0.60*max(0.0, age - 6.0)*(1.0 + 0.05*(temp - 27.0))
               * (1.25 if rain < 700 else 1.0))
    return float(np.clip(fatigue + thermal, 0.2, 72.0))

ages = np.linspace(0, 25, 60)
fig  = go.Figure()
print("THE SAME COMPARISON, DONE PROPERLY - cracking follows the structure\n")
print(f"{'age':>5}" + "".join(f"{t:>12} mm" for t in (150, 240, 300)))
for thick, colr in [(150, RED), (240, AMBER), (300, GREEN)]:
    ys = []
    for a in ages:
        ck = physical_crack(SEGMENT["traffic_volume_vpd"], thick, a,
                            SEGMENT["rainfall_mm_year"], SEGMENT["avg_temperature_c"])
        ys.append(predict_life({**SEGMENT, "pavement_thickness_mm": thick,
                                "pavement_age_years": a, "crack_density_pct": ck}))
    fig.add_trace(go.Scatter(x=ages, y=ys, mode="lines", name=f"{thick} mm section",
                             line=dict(color=colr, width=3)))
for a in (4, 8, 12, 16, 20):
    row_txt = f"{a:>5}"
    for thick in (150, 240, 300):
        ck = physical_crack(SEGMENT["traffic_volume_vpd"], thick, a,
                            SEGMENT["rainfall_mm_year"], SEGMENT["avg_temperature_c"])
        row_txt += f"{predict_life({**SEGMENT, 'pavement_thickness_mm': thick, 'pavement_age_years': a, 'crack_density_pct': ck}):>12.1f}y"
    print(row_txt)

fig.add_vline(x=SEGMENT["pavement_age_years"], line_dash="dash", line_color=MUTED,
              annotation_text="this segment's age")
fig.update_layout(title="Remaining life against age, when cracking follows the structure",
                  xaxis_title="pavement age (years)",
                  yaxis_title="predicted remaining life (years)",
                  template="plotly_white", height=430)
fig.show()

print("\nNow it behaves the way an engineer expects: at every age the thicker section")
print("has more life left, because it cracked less on the way there.")
print("The 150 mm section under 22,000 vehicles a day is simply under-designed -")
print("it is consumed long before the climate ever becomes the governing mechanism.")
'''),
          ("md", r"""
**The rule this establishes, and it applies far beyond pavements:** when you change something upstream,
let everything downstream of it change too. A model trained on observational data will answer whatever
question your inputs actually pose — including the one you did not mean to ask.
"""),
          ("co", r'''
# Interactive version. Colab: Runtime -> Run all, then move the sliders.
try:
    import ipywidgets as widgets
    from IPython.display import display

    def show(traffic, thickness, age, rainfall, temperature, cracking):
        s = dict(traffic_volume_vpd=traffic, pavement_thickness_mm=thickness,
                 pavement_age_years=age, rainfall_mm_year=rainfall,
                 avg_temperature_c=temperature, crack_density_pct=cracking)
        yrs = predict_life(s)
        band = ("Continue normal operation" if yrs > 10 else
                "Schedule preventive maintenance" if yrs > 5 else
                "Major rehabilitation required" if yrs > 2 else
                "Reconstruction recommended")
        print(f"predicted remaining service life : {yrs:5.1f} years")
        print(f"indicated action                 : {band}")

    widgets.interact(
        show,
        traffic=widgets.IntSlider(min=500, max=45000, step=500, value=22000, description="veh/day"),
        thickness=widgets.IntSlider(min=60, max=320, step=5, value=240, description="thickness mm"),
        age=widgets.IntSlider(min=0, max=25, step=1, value=12, description="age yrs"),
        rainfall=widgets.IntSlider(min=300, max=3000, step=50, value=1100, description="rain mm"),
        temperature=widgets.FloatSlider(min=18, max=38, step=0.5, value=31.0, description="temp C"),
        cracking=widgets.FloatSlider(min=0, max=60, step=1.0, value=18.0, description="cracks %"))
except Exception as exc:                                    # noqa: BLE001
    print(f"ipywidgets unavailable ({type(exc).__name__}) - the table above covers the same ground.")
''')],
    built="""A working predictor: six surveyed measurements in, a remaining-life estimate out, with the response
surface visible rather than assumed.""",
    takeaway="""The number matters less than the slope — what moves it is what tells you which treatment helps.""",
)

# ---------------------------------------------- PHASE 9 · THE PAVEMENT AUDIT
step(
    id="audit", phase=8, icon="📑", ai_icon="✅",
    civil="The Pavement Performance Audit", ai="Regression Metrics",
    tech="MAE, RMSE, R² and the error distribution, on held-out roads",
    site="""An agency does not adopt a method because it sounds reasonable. It audits it: take the roads the model
never saw, compare every prediction against what the works file actually recorded, and report the
disagreement.""",
    challenge="""'Accurate' is not a number. A model wrong by six months on a twenty-year pavement is excellent. The same
six months on a segment with one year left is the difference between a seal and a reconstruction.""",
    ai_link="""Three measures, each answering a different question, plus the shape of the errors — which is where the
useful information usually hides.""",
    bridge=[("Typical error", "MAE — mean absolute error"),
            ("Are there bad misses?", "RMSE — punishes large errors"),
            ("Better than guessing?", "R² — variance explained")],
    body=[("co", r'''
# A pavement cannot have negative remaining life. That bound is physics, not statistics,
# so it is imposed on the output rather than hoped for from the model.
pred_best = np.clip(model.predict(X_best), 0.0, 25.0)
err       = pred_best - y_te

mae  = mean_absolute_error(y_te, pred_best)
rmse = float(np.sqrt(np.mean(err**2)))
r2   = r2_score(y_te, pred_best)
naive = float(np.mean(np.abs(y_te - y_tr.mean())))

print(f"PAVEMENT PERFORMANCE AUDIT - {best_name}, "
      f"{len(y_te):,} segments on {clean.iloc[te]['road_id'].nunique()} unseen roads\n")
print(f"  MAE   mean absolute error        {mae:>8.2f} years")
print(f"  RMSE  root mean squared error    {rmse:>8.2f} years")
print(f"  R2    variance explained         {r2:>8.3f}")
print()
print(f"  predicting the network average would give MAE {naive:.2f} years")
print(f"  within 1 year of the outcome     {np.mean(np.abs(err) <= 1.0):>8.1%} of segments")
print(f"  within 2 years of the outcome    {np.mean(np.abs(err) <= 2.0):>8.1%} of segments")
print(f"  wrong by more than 4 years       {np.mean(np.abs(err) > 4.0):>8.1%} of segments")
print()
shape = ("mostly uniform" if rmse/mae < 1.3 else
         "concentrated - a minority of segments carry the error")
print(f"  RMSE is {rmse/mae:.2f}x the MAE, so the errors are {shape}.")
print("  A ratio near 1.25 is the uniform case; above about 1.5, a few bad misses dominate.")
'''),
          ("co", r'''
fig = make_subplots(rows=1, cols=3, subplot_titles=[
    "predicted vs actual", "error distribution", "bias across the range"])

fig.add_trace(go.Scatter(x=y_te, y=pred_best, mode="markers",
                         marker=dict(color=CYAN, size=5, opacity=0.45), showlegend=False), row=1, col=1)
fig.add_trace(go.Scatter(x=[0, 25], y=[0, 25], mode="lines",
                         line=dict(color=MUTED, dash="dash"), showlegend=False), row=1, col=1)

fig.add_trace(go.Histogram(x=err, nbinsx=50, marker_color=AMBER, showlegend=False), row=1, col=2)

bins   = [0, 2, 5, 10, 15, 26]
labels = ["0-2", "2-5", "5-10", "10-15", "15+"]
band   = pd.cut(y_te, bins=bins, labels=labels, right=False)
bias   = pd.DataFrame({"band": band, "err": err}).groupby("band", observed=False)["err"].mean()
fig.add_trace(go.Bar(x=bias.index.astype(str), y=bias.values,
                     marker_color=[RED if v > 0 else GREEN for v in bias.values],
                     showlegend=False), row=1, col=3)

fig.update_xaxes(title_text="actual (years)", row=1, col=1)
fig.update_yaxes(title_text="predicted (years)", row=1, col=1)
fig.update_xaxes(title_text="prediction - actual (years)", row=1, col=2)
fig.update_xaxes(title_text="actual remaining life (years)", row=1, col=3)
fig.update_yaxes(title_text="mean error (years)", row=1, col=3)
fig.update_layout(height=420, template="plotly_white",
                  title=f"{best_name}: the audit in three views")
fig.show()

per_band = pd.DataFrame({"band": band, "abs_err": np.abs(err), "err": err}) \
             .groupby("band", observed=False).agg(segments=("err", "size"),
                                                  mae=("abs_err", "mean"),
                                                  bias=("err", "mean")).round(2)
per_band.columns = ["segments", "MAE (years)", "bias (years)"]
print("ERROR BY REMAINING-LIFE BAND   (positive bias = optimistic = arrives late)\n")
print(per_band.to_string())

low_bias = float(per_band.loc[["0-2", "2-5"], "bias (years)"].max())
print(f"\nWorst optimism in the two lowest bands: {low_bias:+.2f} years.")
print("This is the number to watch every time the model is retrained. Optimism here")
print("means the programme arrives late on the segments least able to wait.")
'''),
          ("md", r"""
### Reading the third chart

The bias panel is the one that matters operationally. A model can have an excellent overall MAE and still
be **systematically optimistic about the segments that are nearly finished** — which are precisely the
segments a maintenance programme exists to catch.

Positive bars mean the model promises more life than the pavement had. If those appear in the `0-2` and
`2-5` bands, the programme will arrive late on the roads it could least afford to be late on. Read the
printed table against the chart before accepting the headline R².
""")],
    built="""A full audit on unseen roads — three metrics, the error distribution, and a bias check across the
remaining-life range.""",
    takeaway="""One overall accuracy figure hides the only errors that matter: the optimistic ones near end of life.""",
)

step(
    id="errors", phase=8, icon="⚠️", ai_icon="💸",
    civil="The Two Errors Do Not Cost The Same", ai="Asymmetric Loss",
    tech="Price each year of error by the treatment it triggers",
    site="""A prediction error becomes a cost when it changes the treatment. Predict too little life and sound
pavement is milled off early. Predict too much and the surface fails before the crew arrives.""",
    challenge="""Those two mistakes are not symmetric, and no statistical measure knows that. MAE treats a year of
optimism and a year of pessimism as identical. The works department does not.""",
    ai_link="""Convert years of error into currency using the agency's own treatment costs. The result is a single
number a finance committee understands, and a ratio that tells the engineer which way to lean when the
model is uncertain.""",
    bridge=[("Too early: asset wasted", "Pessimistic error"),
            ("Too late: escalation", "Optimistic error"),
            ("They differ by a factor", "Asymmetric loss")],
    body=[("co", r'''
# Treatment costs, in rupees per lane-kilometre. Change these to your own schedule of rates.
COST_PREVENTIVE = 1_800_000        # crack sealing, fog seal, thin functional overlay
COST_REHAB      = 6_500_000        # mill and structural overlay
COST_RECON      = 22_000_000       # full-depth reconstruction
SERVICE_LIFE    = 20.0             # years of service a rehabilitation restores

def error_cost(pred, actual):
    """Rupees per km of getting the timing wrong, from the agency's rate schedule."""
    early = np.maximum(actual - pred, 0.0)        # treated too soon: life thrown away
    late  = np.maximum(pred - actual, 0.0)        # treated too late: the job escalates
    waste = early*(COST_REHAB/SERVICE_LIFE)
    esc   = np.clip(late/5.0, 0, 1)*(COST_RECON - COST_REHAB)
    return waste + esc, waste, esc

cost_model, waste_m, esc_m = error_cost(pred_best, y_te)
cost_rule,  waste_r, esc_r = error_cost(rule_age,  y_te)

print("WHAT A YEAR OF ERROR COSTS, PER LANE-KILOMETRE\n")
print(f"  one year too early (asset wasted)        Rs {COST_REHAB/SERVICE_LIFE:>12,.0f}")
print(f"  one year too late  (escalation risk)     Rs {(COST_RECON - COST_REHAB)/5.0:>12,.0f}")
print(f"  ratio                                    {((COST_RECON - COST_REHAB)/5.0)/(COST_REHAB/SERVICE_LIFE):>13.1f} : 1")
print()
print(f"MEAN COST OF TIMING ERROR ACROSS {len(y_te):,} HELD-OUT SEGMENTS\n")
print(f"{'predictor':<32}{'Rs / km':>16}{'of which too early':>22}{'of which too late':>21}")
print(f"{'fixed 20-year cycle':<32}{cost_rule.mean():>16,.0f}{waste_r.mean():>22,.0f}{esc_r.mean():>21,.0f}")
print(f"{best_name:<32}{cost_model.mean():>16,.0f}{waste_m.mean():>22,.0f}{esc_m.mean():>21,.0f}")
print(f"\n  reduction per kilometre                 Rs {cost_rule.mean() - cost_model.mean():>12,.0f}")
'''),
          ("md", r"""
### What the ratio tells the engineer

Being late is several times more expensive than being early, per year. That has a direct operational
consequence, and it is an engineering decision rather than a modelling one:

- **Where the model is uncertain, lean pessimistic.** Bring the treatment forward rather than back.
- **Never accept a model whose bias is positive in the low bands.** Check that chart from the audit step
  before this one, every time the model is retrained.
- **The costs above are assumptions, not measurements.** They are the agency's schedule of rates and they
  should be replaced with yours. The ratio, not the absolute number, is what survives that substitution.
""")],
    built="""The prediction error converted into the agency's own currency, with the asymmetry between early and
late treatment made explicit.""",
    takeaway="""Late costs several times more than early — so where the model is unsure, treat early.""",
)


# ---------------------------------------------- PHASE 10 · MAINTENANCE PLANNING
step(
    id="decision", phase=9, icon="🧾", ai_icon="🤝",
    civil="From A Number To A Treatment", ai="The Decision Support Layer",
    tech="Life bands, plus engineering overrides the model does not get a vote on",
    site="""A predicted remaining life is not a work instruction. It becomes one when it is mapped to a treatment,
with the reasons written in language a works engineer can check.""",
    challenge="""Some knowledge belongs in a rule, not in a weight. A segment with 55% cracking needs structural
investigation whatever the model predicts, because water is already reaching the base — and that is
standard practice, not a statistical finding.""",
    ai_link="""So the decision layer has two parts: the model's prediction, and hard overrides written by engineers.
The overrides can only escalate a recommendation, never soften one. That asymmetry is deliberate.""",
    bridge=[("Predicted years", "Model output"),
            ("Standard practice", "Hard overrides"),
            ("A signed work order", "Recommendation + reasons")],
    body=[("co", r'''
ACTIONS = ["Continue normal operation", "Schedule preventive maintenance",
           "Major rehabilitation required", "Reconstruction recommended"]

def recommend(years, crack, thickness, traffic):
    """Treatment and reasons for one segment. Overrides may only escalate."""
    if   years > 10: act = 0
    elif years >  5: act = 1
    elif years >  2: act = 2
    else:            act = 3

    why = []
    if   years > 10: why.append(f"{years:.1f} years of predicted life remaining")
    elif years >  5: why.append(f"{years:.1f} years left - inside the preventive window")
    elif years >  2: why.append(f"{years:.1f} years left - past the preventive window")
    else:            why.append(f"{years:.1f} years left - at or near terminal condition")

    if crack >= 60:
        act = max(act, 3); why.append(f"cracking {crack:.0f}% - surface integrity lost")
    elif crack >= 45:
        act = max(act, 2); why.append(f"cracking {crack:.0f}% - water reaching the base")
    elif crack >= 25 and act == 0:
        act = max(act, 1); why.append(f"cracking {crack:.0f}% - seal before it propagates")

    if thickness < 100 and traffic > 15000:
        act = min(act + 1, 3)
        why.append(f"{thickness:.0f} mm under {traffic:,.0f} vpd - structurally under-designed")

    return ACTIONS[act], act, " · ".join(why)

test = clean.iloc[te].copy()
test["predicted_years"] = pred_best
recs = [recommend(r.predicted_years, r.crack_density_pct,
                  r.pavement_thickness_mm, r.traffic_volume_vpd) for r in test.itertuples()]
test["action"]      = [a for a, _, _ in recs]
test["action_rank"] = [k for _, k, _ in recs]
test["reasons"]     = [w for _, _, w in recs]

pd.set_option("display.max_colwidth", 78)
print("THE WORK LIST - the twelve most urgent ROADS on the unseen network\n")
print("One entry per road: its worst segment. An agency programmes a road, not a")
print("stray kilometre, and twelve consecutive kilometres of one bad road are one job.\n")
test.sort_values(["action_rank", "predicted_years"], ascending=[False, True]) \
    .drop_duplicates(subset="road_id", keep="first") \
    .head(12)[["segment_id", "road_class", "pavement_age_years", "crack_density_pct",
               "predicted_years", "action", "reasons"]] \
    .set_index("segment_id")
'''),
          ("md", r"""
This is the product. Every earlier step existed to fill in these columns.

Two properties are worth naming:

- **The list is ordered by predicted remaining life, not by cracking.** A heavily cracked segment on a
  thick structure in a dry district does not appear at the top, and it should not.
- **An override escalates and never softens.** The model cannot talk the system out of investigating a
  segment at 55% cracking. If the two disagree, the conservative answer wins.

And what the system never does: close a lane, issue a work order, or commit a rupee. It orders the
engineer's programme.
""")],
    built="""A decision layer that turns predicted years into a ranked work list, with engineering overrides that
can only escalate.""",
    takeaway="""Some knowledge belongs in a rule, not in a weight — and the rule always wins upward.""",
)

step(
    id="dashboard", phase=9, icon="📊", ai_icon="💰",
    civil="The Maintenance Planning Dashboard", ai="The Business Case",
    tech="Network programme and avoided cost, computed from the audit",
    site="""The output the agency actually uses: how many kilometres need each treatment, what the programme costs,
and what is deferred when the budget runs out.""",
    challenge="""The saving is easy to overstate, and infrastructure has heard it overstated before. The only honest way
is to compute it from the audit already performed on the held-out roads, with every assumption named and
visible.""",
    ai_link="""Two figures, both derived from the audit: reconstructions avoided by arriving before escalation, and
sound pavement not milled off early. Nothing else is counted.""",
    bridge=[("Kilometres per treatment", "Grouped predictions"),
            ("Programme cost", "Rate schedule x quantity"),
            ("What it is worth", "Computed from the audit")],
    body=[("co", r'''
# --------------------------------------------------- the network programme
network = clean.copy()
Xn      = network[FEATURES].to_numpy(float)
network["predicted_years"] = np.clip(
    model.predict(scaler.transform(Xn) if best_name == "Linear Regression" else Xn), 0, 25)
nrecs = [recommend(r.predicted_years, r.crack_density_pct,
                   r.pavement_thickness_mm, r.traffic_volume_vpd) for r in network.itertuples()]
network["action"]      = [a for a, _, _ in nrecs]
network["action_rank"] = [k for _, k, _ in nrecs]

RATE = {ACTIONS[0]: 0, ACTIONS[1]: COST_PREVENTIVE,
        ACTIONS[2]: COST_REHAB, ACTIONS[3]: COST_RECON}

plan = (network.groupby("action")
        .agg(segments=("segment_id", "count"))
        .reindex(ACTIONS).fillna(0).astype(int))
plan["km"]   = plan["segments"]*SEGMENT_KM
plan["cost"] = [plan.loc[a, "km"]*RATE[a] for a in plan.index]

print("NETWORK MAINTENANCE PROGRAMME\n")
print(f"{'treatment':<34}{'segments':>10}{'km':>8}{'cost (Rs)':>18}")
for a in ACTIONS:
    print(f"{a:<34}{plan.loc[a, 'segments']:>10,}{plan.loc[a, 'km']:>8,.0f}{plan.loc[a, 'cost']:>18,.0f}")
print(f"{'TOTAL IDENTIFIED NEED':<34}{plan['segments'].sum():>10,}"
      f"{plan['km'].sum():>8,.0f}{plan['cost'].sum():>18,.0f}")
print(f"\n  treatable this year at {BUDGET_KM_YEAR} km      "
      f"{BUDGET_KM_YEAR/max(plan.loc[ACTIONS[1]:, 'km'].sum(), 1):>8.0%} of the identified need")
'''),
          ("co", r'''
# --------------------------------------------------- what the ranking is worth
# Both figures come from the held-out audit, not from an assumption about the model.
late_rule  = np.maximum(rule_age  - y_te, 0.0)
late_model = np.maximum(pred_best - y_te, 0.0)
ESCALATION_YEARS = 3.0        # years past terminal condition at which rehab becomes reconstruction

recon_rule  = float(np.mean(late_rule  > ESCALATION_YEARS))
recon_model = float(np.mean(late_model > ESCALATION_YEARS))
early_rule  = float(np.mean(np.maximum(y_te - rule_age,  0.0)))
early_model = float(np.mean(np.maximum(y_te - pred_best, 0.0)))

km_year          = BUDGET_KM_YEAR
recon_avoided_km = (recon_rule - recon_model)*km_year
value_recon      = recon_avoided_km*(COST_RECON - COST_REHAB)
value_early      = (early_rule - early_model)*km_year*(COST_REHAB/SERVICE_LIFE)

print("BUSINESS CASE - computed from the held-out audit\n")
print(f"  programme size                                  {km_year:>10,.0f} km/year")
print(f"  segments arriving >{ESCALATION_YEARS:.0f} years late, fixed cycle  {recon_rule:>10.1%}")
print(f"  segments arriving >{ESCALATION_YEARS:.0f} years late, with model   {recon_model:>10.1%}")
print(f"  escalations to reconstruction avoided           {recon_avoided_km:>10.1f} km/year")
print(f"    value at Rs {COST_RECON - COST_REHAB:,} per km            Rs {value_recon:>13,.0f} / year")
print()
print(f"  mean years of premature treatment, fixed cycle  {early_rule:>10.2f}")
print(f"  mean years of premature treatment, with model   {early_model:>10.2f}")
print(f"    value of service life retained                Rs {value_early:>13,.0f} / year")
print()
print(f"  TOTAL                                           Rs {value_recon + value_early:>13,.0f} / year")
'''),
          ("co", r'''
fig = make_subplots(rows=1, cols=3, subplot_titles=[
    "network by treatment (km)", "programme cost (Rs crore)", "where the value comes from"],
    specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}]])

cols = [GREEN, CYAN, AMBER, RED]
fig.add_trace(go.Bar(x=[a.split()[0] for a in ACTIONS], y=plan["km"], marker_color=cols,
                     text=plan["km"], textposition="outside", showlegend=False), row=1, col=1)
fig.add_trace(go.Bar(x=[a.split()[0] for a in ACTIONS], y=plan["cost"]/1e7, marker_color=cols,
                     text=(plan["cost"]/1e7).round(1), textposition="outside", showlegend=False),
              row=1, col=2)
fig.add_trace(go.Bar(x=["escalations avoided", "life retained"],
                     y=[value_recon/1e7, value_early/1e7], marker_color=[RED, GREEN],
                     text=[f"{value_recon/1e7:.1f}", f"{value_early/1e7:.1f}"],
                     textposition="outside", showlegend=False), row=1, col=3)
fig.update_yaxes(title_text="kilometres", row=1, col=1)
fig.update_yaxes(title_text="Rs crore", row=1, col=2)
fig.update_yaxes(title_text="Rs crore / year", row=1, col=3)
fig.update_layout(height=430, template="plotly_white",
                  title="Maintenance planning dashboard")
fig.show()

fig = go.Figure()
for a, c in zip(ACTIONS, cols):
    sub = network[network["action"] == a]
    fig.add_trace(go.Scatter(x=sub["pavement_age_years"], y=sub["predicted_years"], mode="markers",
                             name=a, marker=dict(color=c, size=5, opacity=0.5)))
fig.update_layout(title="The whole network, ranked by predicted remaining life",
                  xaxis_title="pavement age (years)", yaxis_title="predicted remaining life (years)",
                  template="plotly_white", height=460)
fig.show()
'''),
          ("md", r"""
### Read the assumptions, not the total

- **`ESCALATION_YEARS = 3`** is the load-bearing assumption and it is a judgement, not a measurement. It
  says a pavement left three years past terminal condition needs reconstruction rather than rehabilitation.
  Change it and the case changes with it.
- **The treatment rates are the agency's, not the model's.** Substitute your own schedule of rates before
  quoting any figure here.
- **Not counted:** road user costs, which are usually larger than the agency's own costs and which improve
  in the same direction; and the engineers' time spent reviewing recommendations, which is a real new cost.
- **The programme is still budget-limited.** The model does not create kilometres. It changes which
  kilometres get the available money.
""")],
    built="""A network maintenance programme with its cost, and a business case computed from the audit rather than
asserted — with the assumption that carries it named.""",
    takeaway="""The model does not enlarge the budget; it changes which kilometres it is spent on.""",
)


# ============================================================================
# INTRO
# ============================================================================
def phase_rows():
    out = []
    for pi, (pname, pdesc) in enumerate(PHASES):
        kids = [s for s in STEPS if s["phase"] == pi]
        out.append(f"| **{pi+1}. {pname}** | {pdesc} | "
                   + " · ".join(link(s["id"], f"{s['icon']} {s['civil']}") for s in kids) + " |")
    return "\n".join(out)

def mapping_rows():
    return "\n".join(f"| {s['icon']} {s['civil']} | → | {s['ai_icon']} {s['ai']} | {s['phase']+1} |"
                     for s in STEPS)

md(rf"""
# 🛣️ AI for Pavement Remaining Service Life Prediction
## Machine Learning for Highway and Pavement Engineers

> You are not here to learn Artificial Intelligence. You are here to solve a **road asset management
> problem** — deciding which kilometres to repair this year, with a fixed budget and consequences that
> arrive years later. AI turns up in the middle of it, because the engineering requires it. Not before.

---

## 1 · The engineering problem

A state highway agency maintains **{1500:,} pavement segments**. Every one of them is deteriorating, every
day, under traffic it did not choose and weather nobody controls.

The budget treats about **7% of the network a year**.

So the question is never *is this road deteriorating*. It always is. The question is **which kilometres,
this year** — and both wrong answers are expensive:

- **Too early** — sound pavement is milled off and years of paid-for service life are thrown away.
- **Too late** — the surface fails, water reaches the base, and an overlay becomes a reconstruction at
  several times the cost.

Traditional practice answers with a fixed cycle: assume a design life, subtract the age, resurface. That
rule ignores traffic, structure and climate entirely — and this notebook measures exactly what that
costs.

---

## 2 · What we are going to build

A **pavement management decision support system**. Four parts:

| | Part | What it does |
|---|---|---|
| 🚐 | **The condition survey** | Traffic, thickness, age, rainfall, temperature and crack density — six measurements per kilometre, from four different systems. |
| 🧹 | **Data preparation** | Unit errors, instrument codes, duplicates and missing records, each handled by the engineering judgement it deserves. |
| 🧠 | **The prediction model** | Linear Regression, Random Forest, Gradient Boosting and XGBoost, all judged on roads they have never seen. |
| 🧾 | **The maintenance programme** | A remaining-life estimate and a recommended treatment for every segment, with reasons attached. |

> **The goal is not an unmanned agency.** The engineer still reads the core, still knows the drain was
> never built, still sequences work around the monsoon, and still signs the estimate. The system does the
> thing one person cannot: assess {1500:,} segments every cycle and say **which one first**.

---

## 3 · The engineering workflow

One network, one maintenance programme, in the order a real project runs it — {len(PHASES)} phases,
{len(STEPS)} steps.

| Phase | On the network | Steps |
|---|---|---|
{phase_rows()}

---

## 4 · Engineering → AI, the whole map

**Every AI concept in this notebook is a highway engineering activity you already understand.** Read down
the left column and you have described a pavement management programme. Read down the right and you have
described a machine learning pipeline. They are the same column.

| 🛣️ Highway engineering process | → | 🤖 The AI process that solves it | Phase |
|---|:-:|---|:-:|
{mapping_rows()}

---

## The one idea this notebook proves

> **Machine Learning learns the relationships between pavement condition, traffic and environmental
> factors to predict the remaining service life of roads — helping engineers plan maintenance at the
> right time.**

Do not take that on trust. Step {[s['id'] for s in STEPS].index('audit')+1} audits it on roads the model
has never seen, and step {[s['id'] for s in STEPS].index('dashboard')+1} prices it.

Three published relationships run through the whole notebook. They generate the survey data, they check
the model, and they supply the language the recommendations are written in:

- **AASHTO 1993 flexible pavement design equation** — allowable standard axle loads from the structural
  number `SN` and the subgrade resilient modulus `MR`
- **The AASHO Road Test fourth-power law** — damage of one axle = `(P / 80 kN)⁴`
- **Miner's linear cumulative damage** — consumed life = applied ESALs ÷ allowable ESALs

## Three honest questions this notebook refuses to skip

1. **Where do the labels come from?** From the works file — the year each segment actually reached
   terminal condition — not from the same formula that produced the features.
2. **How do you split the data?** By **road**, never by row. Adjacent kilometres are near-duplicates, and
   step {[s['id'] for s in STEPS].index('split')+1} measures how much a random split would have flattered
   the result.
3. **Is R² the right score?** No. A year of optimism and a year of pessimism cost different amounts of
   money, and step {[s['id'] for s in STEPS].index('errors')+1} replaces accuracy with rupees.
""")

md(r"""
---

## Setup

In Colab everything below is already installed. Charts are Plotly, so they are interactive — hover, zoom
and toggle series from the legend.

`xgboost` and `ipywidgets` are optional. Both are guarded, and the notebook falls back cleanly if they are
missing.
""")

co(r"""
# !pip install numpy pandas scikit-learn plotly xgboost ipywidgets

print("Imports, the AASHTO design equations and the palette are all in step 1, below.")
""")

# ============================================================================
# EMIT
# ============================================================================
for i, s in enumerate(STEPS):
    pname, pdesc = PHASES[s["phase"]]
    bridge_tbl = "\n".join(f"| {l} | → | {r} |" for l, r in s["bridge"])
    see = (f"\n> 🎬 **See this illustrated:** [{APP}/?stage={s['id']}]({APP}/?stage={s['id']})\n"
           if APP else "")
    md(rf"""
---

# {NUM[i]} {s['icon']} {s['civil']}
### Phase {s['phase']+1} of {len(PHASES)} · {pname} — *{pdesc}*

> The highway engineering activity on this page is also, exactly, the AI concept **{s['ai']}**. Here is
> why.

## Part 1 · On the network

{s['site'].strip()}

## Part 2 · The engineering challenge

{s['challenge'].strip()}
""")
    md(rf"""
## Part 3 · Where the AI comes in

{s['ai_link'].strip()}

| 🛣️ **On the network** | → | 🤖 **In the AI** |
|---|:-:|---|
{bridge_tbl}

**{s['civil']}** → *becomes* → **{s['ai']}** → *which is computed as* → `{s['tech']}`
{see}
## Part 4 · The technical explanation

You now know what **{s['civil']}** is, why it is hard, and why it needs **{s['ai']}**. Only now, the
mechanism.
""")
    for kind, text in s["body"]:
        (md if kind == "md" else co)(text)
    md(rf"""
## Part 5 · What you just built

{s['built'].strip()}

> **Key takeaway.** {s['takeaway'].strip()}
""")

md(r"""
---

# 🏁 The whole system, in one page

```
   CONDITION SURVEY  ──►  clean  ──►  split by ROAD  ──►   REGRESSION   ──┐
   traffic · thickness · age          (never by row)       model          │
   rainfall · temperature                                                 │
   crack density                                          REMAINING       │
                                                          SERVICE LIFE ───┤──►  MAINTENANCE
                                                          in years        │     PROGRAMME
   AASHTO 1993 + fourth-power law ───►  the physics                       │     treatment ·
   the standards behind the data        the model must recover            │     priority ·
                                                                          │     reasons
   ENGINEERING OVERRIDES ──────────────────────────────►  escalate only ──┘
   cracking · under-design
```

## What was built

| Stage | Method | Output |
|---|---|---|
| Load damage | AASHO fourth-power law | ESALs per year |
| Structural capacity | AASHTO 1993 design equation | allowable ESALs from SN and MR |
| Consumed life | Miner's linear damage | damage ratio |
| Data cleaning | Unit conversion, imputation, deduplication | a survey that can be trusted |
| Honest evaluation | GroupShuffleSplit by road | a test set of unseen roads |
| Prediction | Linear · Random Forest · Gradient Boosting · XGBoost | remaining service life in years |
| Explanation | Permutation importance + local sensitivity | reasons an engineer can check |
| Audit | MAE · RMSE · R² · bias by band | where the model fails, not just how often |
| Costing | The agency's schedule of rates | rupees per kilometre of timing error |
| Programme | Life bands + engineering overrides | a ranked, priced work list |

## The three things worth remembering

1. **Pavement deterioration is non-linear and it interacts.** Damage goes as load⁴, capacity rises far
   faster than thickness, and the governing mechanism itself changes between a district road and a
   national highway. That is why tree ensembles beat a straight line here.
2. **Cracking is the most informative measurement** — because it summarises damage from causes nobody
   recorded: the blocked drain, the weak subgrade, the bad batch.
3. **Highway Engineer + AI.** The system ranks the network and explains itself. The engineer decides,
   signs, and carries the consequence.

## Where the engineering discipline showed up

Six moments in this notebook were engineering judgements, not machine learning:

- **Converting the Fahrenheit district** instead of deleting it — that would have removed a whole climate
  zone over a unit error.
- **Imputing rainfall but not thickness** — one is a district property you could have looked up, the other
  is whatever that contractor laid.
- **Splitting by road**, because kilometre 6 and kilometre 7 are nearly the same pavement.
- **Keeping the fixed-cycle rule** as a baseline, so the model's value is measured rather than assumed.
- **Pricing the two errors differently**, because arriving late costs several times more than arriving
  early.
- **Writing overrides that can only escalate** — some knowledge belongs in a rule, not in a weight.
""")

nb = new_notebook(cells=cells, metadata={
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"},
    "colab": {"provenance": []},
})
nbf.validate(nb)
with open("Pavement_Remaining_Life_AI.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"wrote Pavement_Remaining_Life_AI.ipynb  ({len(cells)} cells, "
      f"{sum(1 for c in cells if c.cell_type=='code')} code, {len(STEPS)} steps, {len(PHASES)} phases)")
