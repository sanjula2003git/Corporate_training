"""
Builds Transformer_Maintenance_DL.ipynb from nbformat cells.
Run:  py -3.13 build_nb.py

Same five-part-per-step layout as the Smart Construction / Building Energy /
Cutting Tool notebooks. 20 steps, 9 phases.

The domain content is real and standards-based:
  * IEEE C57.91 loading guide  - hot-spot temperature and the ageing acceleration
    factor F_AA = exp(15000/383 - 15000/(theta_h + 273))
  * Duval Triangle 1 (IEC 60599) - fault-type diagnosis from CH4 / C2H4 / C2H2
Both are used to GENERATE the fleet log and to CHECK the model, so the notebook
and the standards never disagree.

APP: set to a deployed Streamlit URL to switch on the per-step links.
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

APP = "https://transformer-maintenance-dl.streamlit.app"

cells = []
def md(t):  cells.append(new_markdown_cell(t.strip("\n")))
def co(t):  cells.append(new_code_cell(t.strip("\n")))
def link(stage, label):
    return f"[{label}]({APP}/?stage={stage})" if APP else label

PHASES = [
    ("The Asset",            "One transformer, twenty thousand customers, no spare."),
    ("One Inspection",       "A condition assessment becomes a written record."),
    ("The Fleet Log",        "The asset-management export lands and gets checked."),
    ("Preparing The Data",   "Faulty readings out, the fleet split by unit."),
    ("Health From Sensors",  "The rulebook, then the model that extends it."),
    ("The Image Wall",       "The infrared survey arrives and the rulebook collapses."),
    ("Reading The Heat",     "A CNN grades a thermal survey no rule could grade."),
    ("The Maintenance Audit", "Every recommendation checked against the engineer's decision."),
    ("Decision Support",     "One recommendation, with its reasoning and its confidence."),
]

NUM = ["①","②","③","④","⑤","⑥","⑦","⑧","⑨","⑩",
       "⑪","⑫","⑬","⑭","⑮","⑯","⑰","⑱","⑲","⑳"]

STEPS = []
def step(**kw): STEPS.append(kw)


# ---------------------------------------------- PHASE 1
step(
    id="the-asset", phase=0, icon="⚡", ai_icon="🤖",
    civil="A Transformer In Service", ai="Why Condition Monitoring Needs AI",
    tech="Continuous degradation vs an annual oil sample",
    site="""A 40 MVA 132/33 kV grid transformer has been in service for twenty-two years. It feeds twenty thousand
customers. It has no installed spare, a replacement lead time measured in months, and a replacement cost
in the millions. It runs continuously.""",
    challenge="""Its condition changes every hour — loading, ambient temperature, insulation ageing, moisture ingress,
oil degradation. It is assessed by an **oil sample once or twice a year** and a visual inspection. A
fault that develops in March is discovered in October, if it is discovered at all.""",
    ai_link="""Before anybody says machine learning, be clear what is being asked for. Not judgement. Something duller:
a way to combine every measurement the fleet already produces into a **current** assessment of each unit,
so the engineer's attention goes to the right transformer this week.""",
    bridge=[("Degrades continuously", "Assess every reading"),
            ("Sampled twice a year", "Model the drivers"),
            ("One engineer, many units", "Rank the fleet")],
    body=[("co", r'''
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

np.random.seed(42)
CYAN, AMBER, GREEN, RED, MUTED = "#4fc3f7", "#ffb74d", "#66bb6a", "#ef5350", "#8b949e"

# ---------------------------------------------------------------- IEEE C57.91
# Hot-spot temperature, and how fast the insulation is ageing at that temperature.
D_TOP_RATED, D_HS_RATED = 45.0, 22.0     # K rise at rated load (top oil, hot spot over oil)
THETA_REF = 110.0                        # C - the reference hot spot for a 65 K rise unit

def top_oil_c(ambient_c, load_pu):
    "Top-oil temperature. Rise follows load to the power 0.8 (IEEE C57.91)."
    return ambient_c + D_TOP_RATED*np.power(np.clip(load_pu, 0.05, None), 0.8)

def hotspot_c(ambient_c, load_pu):
    "Winding hot-spot temperature. The gradient over oil follows load to the power 1.6."
    return top_oil_c(ambient_c, load_pu) + D_HS_RATED*np.power(np.clip(load_pu, 0.05, None), 1.6)

def ageing_factor(theta_hs_c):
    """IEEE C57.91 ageing acceleration factor.

    F_AA = 1 at the reference hot spot of 110 C. Above it the insulation ages faster,
    and the exponential is steep: roughly a doubling for every 6-7 K.
    """
    return np.exp(15000.0/383.0 - 15000.0/(np.asarray(theta_hs_c, float) + 273.0))

print("Hot-spot temperature and insulation ageing, at 30 C ambient:\n")
print(f"{'load':>6}{'top oil':>10}{'hot spot':>11}{'ageing rate':>14}")
for k in [0.5, 0.8, 1.0, 1.1, 1.2, 1.3]:
    th = hotspot_c(30, k)
    print(f"{k:>6.1f}{top_oil_c(30, k):>9.1f}C{th:>10.1f}C{ageing_factor(th):>13.2f}x")

print("\nRead the last column. At 1.0 per-unit the insulation ages at its design rate.")
print("At 1.2 per-unit it ages about six times faster - a day of overload costs a week of life.")
print("That is why loading history matters as much as the current reading.")
''')],
    built="""The reason this asset class gets its own maintenance philosophy: degradation is exponential in
temperature, and temperature is set by decisions made hours earlier.""",
    takeaway="""Insulation ages exponentially with hot-spot temperature — so history matters, not just today's reading.""",
)

step(
    id="enter-ai", phase=0, icon="📡", ai_icon="🛰️",
    civil="Continuous Condition Monitoring", ai="A Decision Support System",
    tech="Every reading assessed, not one sample a year",
    site="""Nothing about the transformer changes. Same core, same windings, same oil. The maintenance engineer
still walks the compound, still reads the Buchholz relay, still signs the switching programme. What is
added is instrumentation: online DGA, fibre-optic winding temperature, bushing monitors, moisture, and a
scheduled infrared survey.""",
    challenge="""The usual objection: is this here to replace the maintenance engineer? No. A model cannot smell hot
oil, hear a core hum change, judge whether an outage can be taken this week, or carry the consequence of
being wrong about a unit feeding a hospital.""",
    ai_link="""A decision support system ranks the fleet and proposes an action **with its reasoning attached**. The
engineer accepts it, defers it, or overrides it. In this asset class that division is not a courtesy —
it is how the work is actually authorised.""",
    bridge=[("The engineer stays", "Ranks the fleet"),
            ("Instrumentation added", "Proposes an action"),
            ("Nobody is replaced", "You still sign the programme")],
    body=[("md", r"""
| The engineer stays in charge of | Where one person needs help |
|---|---|
| Smelling hot oil, hearing the core | Watching 400 units continuously |
| Judging whether an outage can be taken | Comparing today against 20 years of records |
| Balancing risk against network security | Combining DGA, thermal, moisture and PD at once |
| Signing the switching programme | Never having an off week |
| Carrying the consequence | — |

> Four actions are possible, and they differ by orders of magnitude in cost and disruption:
>
> **Continue normal operation** · **Schedule routine maintenance** · **Immediate inspection required** ·
> **Plan replacement**
>
> The system's job is to propose one of those four and say why. The engineer's job is to decide.
""")],
    built="""The role of the system, settled before any code: it proposes and explains, a person authorises.""",
    takeaway="""The system ranks the fleet and explains itself. The engineer authorises the work.""",
)

# ---------------------------------------------- PHASE 2
step(
    id="one-record", phase=1, icon="📋", ai_icon="🗄️",
    civil="One Condition Assessment", ai="Data Collection",
    tech="One assessment → one row of measurements + a health index",
    site="""A condition assessment pulls together everything known about a unit at one moment: the electrical
loading, the thermal picture, the dissolved gas analysis, the oil quality, the moisture, the partial
discharge activity, and the age.""",
    challenge="""These arrive from different places at different times — the SCADA historian, the oil laboratory, the
bushing monitor, the survey report. No single number tells you the condition, and four hundred units is
too many to hold in one head.""",
    ai_link="""Written as one row, an assessment becomes a record: sixteen measurements in, and the health the unit was
subsequently judged to have. Thousands of those rows are a fleet's accumulated experience.""",
    bridge=[("Sixteen measurements", "One row per assessment"),
            ("From four sources", "Sixteen features"),
            ("Judged condition", "One target class")],
    body=[("md", r"""
| Measurement | Why it is taken | Unit |
|---|---|---|
| 🌡️ Top-oil / hot-spot temperature | Drives insulation ageing exponentially | °C |
| 🌤️ Ambient temperature | The datum the rises are measured from | °C |
| ⚡ Load | Sets the temperature rise; overload is cumulative damage | p.u. |
| 🔌 Voltage deviation, load current | Electrical stress on the insulation | %, A |
| 🧪 **H₂** hydrogen | Partial discharge, and the earliest gas to appear | ppm |
| 🧪 **CH₄** methane, **C₂H₆** ethane | Low-temperature thermal fault | ppm |
| 🧪 **C₂H₄** ethylene | High-temperature thermal fault (>700 °C) | ppm |
| 🧪 **C₂H₂** acetylene | Arcing. The gas nobody wants to see. | ppm |
| 🧪 **CO** carbon monoxide | Cellulose (paper insulation) degradation | ppm |
| 💧 Moisture in oil | Reduces dielectric strength, accelerates ageing | ppm |
| ⚡ Partial discharge | Incipient insulation breakdown | pC |
| 🛢️ Oil breakdown voltage | Whether the oil can still hold off the volts | kV |
| 📅 Age | Cumulative everything | years |

The five gases in the middle are **Dissolved Gas Analysis**. They are the closest thing this industry has
to a blood test: different faults decompose the oil in different ways and leave different gas signatures.
"""),
          ("co", r'''
# ------------------------------------------------- the fault physics
# Each fault type decomposes oil differently. These ratios are the basis of every
# DGA diagnostic method, including the Duval Triangle used in the next few steps.
FAULT_GAS = {
    # name : (H2,  CH4,  C2H6, C2H4, C2H2)  relative generation rates
    "normal":       (1.0, 0.6, 0.5, 0.3, 0.02),
    "PD":           (9.0, 1.4, 0.3, 0.2, 0.05),   # partial discharge - hydrogen dominates
    "T1":           (1.2, 3.0, 2.2, 1.0, 0.05),   # thermal fault < 300 C
    "T2":           (1.4, 3.2, 1.6, 4.0, 0.10),   # thermal fault 300-700 C
    "T3":           (1.6, 2.4, 0.9, 9.0, 0.30),   # thermal fault > 700 C
    "D1":           (5.0, 1.6, 0.5, 2.0, 4.5),    # low-energy discharge - acetylene appears
    "D2":           (6.0, 2.2, 0.7, 4.5, 9.0),    # high-energy arcing
}
FAULT_NAMES = list(FAULT_GAS)

print("Relative gas generation by fault type (the basis of every DGA method):\n")
print(pd.DataFrame(FAULT_GAS, index=["H2", "CH4", "C2H6", "C2H4", "C2H2"]).T.to_string())
print("\nRead the C2H2 column. Acetylene needs an arc to form - it barely appears otherwise.")
print("Read the C2H4 column. Ethylene means heat, and a lot of it.")
print("That is the whole idea: the gas mixture tells you WHAT is wrong, not just THAT something is.")
''')],
    built="""The measurement set, and the physical reason the gas ratios carry a diagnosis rather than just an
alarm.""",
    takeaway="""One assessment is one row: sixteen measurements in, one judged condition out.""",
)

step(
    id="two-records", phase=1, icon="🧾", ai_icon="🔀",
    civil="Test Report vs Thermal Survey", ai="Two Kinds Of Data",
    tech="Sixteen named measurements, or 4,096 unnamed pixels",
    site="""Two records exist for every assessment. The test report — named quantities with units, every one of them
chosen by an engineer and traceable to a standard. And the infrared survey — a thermal image of the tank,
radiators and bushings.""",
    challenge="""The test report tells you what is happening **inside** the tank. The survey tells you what is happening
**outside** it: a hot bushing connection, a radiator bank that has stopped circulating, a cooling fan
that has failed. Neither sees what the other sees.""",
    ai_link="""Named columns suit Machine Learning: the engineer chose the quantities, the model weights them. Raw
pixels do not — nobody can name 4,096 useful columns. That difference is why this notebook has two
halves.""",
    bridge=[("The test report", "Named columns → ML"),
            ("The thermal survey", "Raw pixels → DL"),
            ("Inside vs outside", "The fork in the road")],
    body=[("co", r'''
def make_thermal(kind="normal", size=64, seed=0):
    """A transformer thermal survey: tank, radiator bank, three bushings.

    normal          - even warm tank, all radiators circulating
    hotspot         - a bright spot at a bushing connection      (FAULT)
    blocked_cooling - one radiator bank COLD: oil not circulating (FAULT)
    uneven_cooling  - alternate radiators cold: fans/pumps failing (FAULT)
    solar_load      - the whole unit warm from sun on the tank    (NOT a fault)

    Note the physics: a cooling fault makes part of the unit COLDER, not hotter.
    That is what defeats every 'alarm above X degrees' rule.
    """
    KS = {"normal": 0, "hotspot": 1, "blocked_cooling": 2,
          "uneven_cooling": 3, "solar_load": 4}
    rng = np.random.default_rng(seed*7 + KS[kind])
    Y, X = np.mgrid[0:size, 0:size]
    img = 0.22 + rng.normal(0, 0.02, (size, size))               # cool background

    tank = (Y > 20) & (Y < 52) & (X > 8) & (X < 40)              # the main tank
    img[tank] += 0.34
    img += 0.05*np.exp(-((Y-24)**2)/(2*6.0**2))*(X > 8)*(X < 40) # warm at the top, as oil rises

    rad_x = [44, 49, 54, 59]                                     # radiator bank
    rad_hot = [0.30]*4
    if kind == "blocked_cooling":
        rad_hot = [0.30, 0.05, 0.04, 0.30]                       # two banks not circulating
    elif kind == "uneven_cooling":
        rad_hot = [0.30, 0.08, 0.30, 0.07]
    for rx, hot in zip(rad_x, rad_hot):
        img += hot*np.exp(-((X-rx)**2)/(2*1.6**2))*((Y > 22) & (Y < 50))

    for bx in (14, 24, 34):                                      # three bushings on top
        img += 0.18*np.exp(-(((Y-14)**2 + (X-bx)**2)/(2*2.6**2)))

    if kind == "hotspot":
        img += 0.55*np.exp(-(((Y-14)**2 + (X-24)**2)/(2*2.4**2)))   # centre bushing running hot
    elif kind == "solar_load":
        img += 0.13                                              # sun on everything, no fault

    return np.clip(img, 0, 1)

def show(z, title="", h=340, cs="Inferno"):
    f = go.Figure(go.Heatmap(z=z, colorscale=cs, showscale=False, zmin=0, zmax=1))
    f.update_layout(title=title, height=h, template="plotly_white",
                    margin=dict(l=10, r=10, t=50, b=10))
    f.update_xaxes(visible=False)
    f.update_yaxes(visible=False, autorange="reversed", scaleanchor="x")
    return f

report = pd.DataFrame([{"top_oil_c": 78.4, "hotspot_c": 96.1, "load_pu": 0.92,
                        "h2_ppm": 148, "ch4_ppm": 62, "c2h4_ppm": 191, "c2h2_ppm": 3,
                        "moisture_ppm": 18, "pd_pc": 320, "oil_bdv_kv": 44, "age_years": 22}])
print("THE TEST REPORT — named quantities, each traceable to a standard:")
print(report.T.to_string(header=False))

im = make_thermal("hotspot")
print(f"\nTHE THERMAL SURVEY — {im.size:,} unnamed numbers. None of them is called 'hotspot'.")
show(im, "infrared survey · 64 × 64 · tank, radiators, bushings").show()
''')],
    built="""The two data types, and the reason a transformer needs both: the oil tells you about the core and
windings, the camera tells you about everything bolted to the outside.""",
    takeaway="""The test report arrives with names; the thermal survey does not. That splits ML from DL.""",
)

# ---------------------------------------------- PHASE 3
step(
    id="load", phase=2, icon="📥", ai_icon="🐼",
    civil="The Fleet Log Arrives", ai="Loading The Dataset",
    tech="Asset-management export → DataFrame, 400 units",
    site="""The asset management system exports every condition assessment on record: 400 transformers, several
assessments each, with the measurements and the condition the engineer subsequently assigned.""",
    challenge="""An export is not a dataset. Laboratories report below-detection-limit gases as zero or as blank
inconsistently, a bushing monitor that lost supply logs a flat zero, and assessments get duplicated when
a unit is re-tested.""",
    ai_link="""Loading it into a DataFrame is the first step: shape, types, and a first look at what actually
arrived.""",
    bridge=[("Years of assessments", "read_csv"),
            ("400 units", "shape and dtypes"),
            ("Condition assigned", "First look")],
    body=[("co", r'''
def health_index(gas_severity, moisture_ppm, pd_pc, bdv_kv, age_years, ageing_rate):
    """A condition score out of 100, in the style of a utility health index.

    Every term is a penalty an asset engineer would recognise, and the weights are
    stated here rather than hidden. This is the target the models learn to predict.
    """
    hi = 100.0
    hi -= 30.0*np.clip(gas_severity, 0, 1)                    # dissolved gas
    hi -= 12.0*np.clip((moisture_ppm - 10)/30.0, 0, 1)        # moisture in oil
    hi -= 16.0*np.clip(np.log10(np.clip(pd_pc, 1, None))/3.5, 0, 1)   # partial discharge
    hi -= 14.0*np.clip((50 - bdv_kv)/25.0, 0, 1)              # oil breakdown voltage
    hi -= 10.0*np.clip(age_years/45.0, 0, 1)                  # age
    hi -= 12.0*np.clip(np.log2(np.clip(ageing_rate, 0.1, None))/4.0, 0, 1)  # thermal history
    return np.clip(hi, 0, 100)

HEALTH_CLASSES = ["Healthy", "Minor Degradation", "Moderate Risk", "High Risk"]

def health_class(hi):
    "Utility practice: four condition bands, each with a different maintenance response."
    return np.where(hi >= 85, 0, np.where(hi >= 70, 1, np.where(hi >= 52, 2, 3)))

def make_fleet(n_units=400, seed=42):
    rng = np.random.default_rng(seed)
    rows = []
    for u in range(n_units):
        age  = float(np.clip(rng.gamma(4.0, 5.5), 1, 48))
        # older units are likelier to have developed a fault
        p_fault = np.clip(0.05 + age/70.0, 0, 0.65)
        for _ in range(int(rng.integers(2, 5))):              # a few assessments per unit
            fault = ("normal" if rng.random() > p_fault
                     else str(rng.choice(FAULT_NAMES[1:], p=[.18, .22, .20, .16, .14, .10])))
            sev   = 0.0 if fault == "normal" else float(rng.uniform(0.25, 1.0))

            amb  = float(rng.normal(24, 9))
            load = float(np.clip(rng.normal(0.78, 0.20), 0.25, 1.35))
            th_top, th_hs = top_oil_c(amb, load), hotspot_c(amb, load)
            f_aa = float(ageing_factor(th_hs))

            # gases: a base level that grows with age, plus the fault signature
            base = 18.0 + 2.2*age
            r    = FAULT_GAS[fault]
            scale = base*(1.0 + 14.0*sev)
            h2, ch4, c2h6, c2h4, c2h2 = [
                float(abs(rng.normal(scale*g/4.0, scale*g/12.0 + 1.5))) for g in r]
            co_ppm = float(abs(rng.normal(220 + 26*age + 400*sev*(fault in ("T1","T2","T3")), 90)))

            moisture = float(np.clip(rng.normal(9 + 0.55*age + 8*sev, 4), 2, 55))
            bdv      = float(np.clip(rng.normal(62 - 0.45*age - 12*sev, 5), 18, 78))
            pd_pc    = float(np.clip(rng.lognormal(np.log(45 + 900*sev*(fault in ("PD","D1","D2"))), 0.7),
                                     5, 20000))

            gas_sev = float(np.clip((0.55*sev + 0.45*np.clip(
                (h2 + ch4 + c2h4 + 6*c2h2)/900.0, 0, 1)), 0, 1))
            hi = float(health_index(gas_sev, moisture, pd_pc, bdv, age, f_aa))

            rows.append(dict(unit_id=f"TX{u:03d}", age_years=round(age, 1),
                             ambient_c=round(amb, 1), load_pu=round(load, 3),
                             top_oil_c=round(th_top, 1), hotspot_c=round(th_hs, 1),
                             ageing_rate=round(f_aa, 3),
                             voltage_dev_pct=round(float(rng.normal(0, 2.2)), 2),
                             load_current_a=round(load*175*float(rng.normal(1, .03)), 1),
                             h2_ppm=round(h2, 1), ch4_ppm=round(ch4, 1), c2h6_ppm=round(c2h6, 1),
                             c2h4_ppm=round(c2h4, 1), c2h2_ppm=round(c2h2, 2),
                             co_ppm=round(co_ppm, 1), moisture_ppm=round(moisture, 1),
                             pd_pc=round(pd_pc, 1), oil_bdv_kv=round(bdv, 1),
                             fault_type=fault, health_index=round(hi, 1),
                             health_class=int(health_class(hi))))
    df = pd.DataFrame(rows)

    # the faults a real export carries
    m = len(df)
    df.loc[rng.choice(m, 40, replace=False), "pd_pc"]        = 0.0    # monitor lost supply
    df.loc[rng.choice(m, 30, replace=False), "oil_bdv_kv"]   = np.nan # sample not tested
    df.loc[rng.choice(m, 25, replace=False), "moisture_ppm"] = np.nan
    df.loc[rng.choice(m, 20, replace=False), "c2h2_ppm"]     = -1.0   # below detection, keyed as -1
    return pd.concat([df, df.sample(35, random_state=1)], ignore_index=True)

make_fleet().to_csv("transformer_fleet.csv", index=False)
df = pd.read_csv("transformer_fleet.csv")
print("shape:", df.shape, " units:", df.unit_id.nunique())
df.head()
''')],
    built="""A fleet log generated from the standards themselves — IEEE thermal ageing, DGA fault signatures, and a
stated health index — with the reporting inconsistencies a real export carries.""",
    takeaway="""The export is raw material. Loading it is where the data work starts.""",
)

step(
    id="inspect", phase=2, icon="🔍", ai_icon="📊",
    civil="Checking The Records", ai="Data Inspection",
    tech="Missing, impossible, duplicated — and the class balance",
    site="""Before trusting years of assessments, check them the way you would check a laboratory certificate: is
anything missing, is anything physically impossible, is anything repeated?""",
    challenge="""Two traps here are specific to this data. A partial-discharge reading of `0 pC` is not a quiet
transformer — it is a monitor that lost supply. And acetylene keyed as `-1` means *below detection
limit*, which is the best possible result, recorded as an impossible number.""",
    ai_link="""Inspection covers both the usual checks and the **class balance of the target**, because most of a
healthy fleet is healthy — and a model that only ever says 'Healthy' would score well while finding
nothing.""",
    bridge=[("Missing, impossible", "isna, describe"),
            ("0 pC is a dead monitor", "Domain-specific checks"),
            ("Most units are fine", "Class imbalance")],
    body=[("co", r'''
SENSORS = ["age_years", "ambient_c", "load_pu", "top_oil_c", "hotspot_c", "ageing_rate",
           "voltage_dev_pct", "load_current_a", "h2_ppm", "ch4_ppm", "c2h6_ppm",
           "c2h4_ppm", "c2h2_ppm", "co_ppm", "moisture_ppm", "pd_pc", "oil_bdv_kv"]

print("MISSING values:")
print(df[SENSORS].isna().sum()[df[SENSORS].isna().sum() > 0].to_string(), "\n")
print("Duplicate rows:", int(df.duplicated().sum()), "\n")
print("Physically impossible or misleading:")
print(f"  pd_pc == 0        : {int((df.pd_pc == 0).sum()):3d}   a monitor that lost supply, not a silent unit")
print(f"  c2h2_ppm < 0      : {int((df.c2h2_ppm < 0).sum()):3d}   'below detection limit', keyed as -1\n")

cnt = df.health_class.value_counts().sort_index()
fig = make_subplots(rows=1, cols=2, subplot_titles=[
    "condition classes across the fleet", "fault types found"])
fig.add_trace(go.Bar(x=[HEALTH_CLASSES[i] for i in cnt.index], y=cnt.values,
                     marker_color=[GREEN, CYAN, AMBER, RED], showlegend=False), row=1, col=1)
fc = df.fault_type.value_counts()
fig.add_trace(go.Bar(x=fc.index, y=fc.values, marker_color=MUTED, showlegend=False), row=1, col=2)
fig.update_layout(height=360, template="plotly_white")
fig.show()

share = df.health_class.value_counts(normalize=True).sort_index()
for i, s in share.items():
    print(f"  {HEALTH_CLASSES[i]:20s} {s:6.1%}")
print(f"\nA model that always says '{HEALTH_CLASSES[int(share.idxmax())]}' would already score "
      f"{share.max():.1%}.")
print("Remember that number. It is the bar every result later in this notebook has to clear.")
''')],
    built="""A fault list, two domain-specific traps caught, and the baseline accuracy every later result has to
beat.""",
    takeaway="""0 pC is a dead monitor and −1 ppm is a clean sample: know your instruments before you trust the data.""",
)

# ---------------------------------------------- PHASE 4
step(
    id="clean", phase=3, icon="🧹", ai_icon="🧼",
    civil="Removing The Faulty Readings", ai="Data Cleaning",
    tech="Drop duplicates, fix the coding, fill with the median",
    site="""A laboratory result that was never taken is not a zero. A monitor that lost supply did not measure a
quiet transformer. Both have to be dealt with before anything is built on them.""",
    challenge="""And the below-detection acetylene is the opposite problem: `-1` is not missing data, it is a **good
result** recorded badly. Deleting those rows would throw away the healthiest units in the fleet and bias
everything that follows.""",
    ai_link="""Cleaning therefore does three different things: drop exact duplicates, **recode** below-detection to a
small positive value, and fill genuinely missing measurements with the column median.""",
    bridge=[("Never tested ≠ zero", "Mark as missing"),
            ("Below detection = good", "Recode, do not delete"),
            ("Keep the rest", "fillna(median)")],
    body=[("co", r'''
clean = df.drop_duplicates().copy()

# below detection limit is a RESULT, not a gap - recode to half the detection limit
DETECT_LIMIT = 0.5
n_bdl = int((clean.c2h2_ppm < 0).sum())
clean.loc[clean.c2h2_ppm < 0, "c2h2_ppm"] = DETECT_LIMIT/2

# a dead monitor is a gap, not a measurement
clean.loc[clean.pd_pc <= 0, "pd_pc"] = np.nan

for c in SENSORS:
    clean[c] = clean[c].fillna(clean[c].median())

print(f"rows {len(df):,} -> {len(clean):,} after de-duplication")
print(f"below-detection acetylene recoded to {DETECT_LIMIT/2} ppm : {n_bdl} rows")
print(f"missing left: {int(clean[SENSORS].isna().sum().sum())}\n")
print("Why this matters, in one number:")
print(f"  mean acetylene if -1 had been left in : {df.c2h2_ppm.mean():7.2f} ppm")
print(f"  mean acetylene after recoding         : {clean.c2h2_ppm.mean():7.2f} ppm")
print("  Acetylene is the gas that means arcing. Getting its baseline wrong is not a rounding error.")
''')],
    built="""A log where a clean laboratory result reads as a clean result, and a dead instrument reads as missing.""",
    takeaway="""Below detection is a result, not a gap — recode it; a dead monitor is a gap, not a quiet transformer.""",
)

step(
    id="split", phase=3, icon="🗂️", ai_icon="✂️",
    civil="Known Units vs Sealed Units", ai="Train / Test Split",
    tech="Split by UNIT, not by assessment",
    site="""You would not validate a diagnostic method on the same transformer you tuned it on. You would try it on
a unit it has never seen.""",
    challenge="""Here the usual random split is actively wrong. The same transformer appears two to four times in the
log. Shuffle the rows and the model is tested on the March assessment of a unit whose September
assessment it memorised — same age, same oil, nearly the same gases.""",
    ai_link="""Split by **unit**: 75% of transformers to train on, 25% sealed. That is also how it would be deployed —
trained on the fleet you know, run on the one that just arrived.""",
    bridge=[("A unit it has not seen", "Group the split by unit"),
            ("Not another sample of the same one", "No unit in both sets"),
            ("Judge on the unseen", "Score only there")],
    body=[("co", r'''
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

units = clean.unit_id.unique()
u_tr, u_te = train_test_split(units, test_size=0.25, random_state=42)
tr = clean.unit_id.isin(u_tr).values
te = clean.unit_id.isin(u_te).values
y  = clean.health_class.values

print(f"units {len(u_tr)} train / {len(u_te)} sealed")
print(f"rows  {tr.sum()} train / {te.sum()} sealed")
print(f"overlap between the two sets of units: {len(set(u_tr) & set(u_te))}\n")

# prove the leak is real
Xq = clean[SENSORS].values
i1, i2 = train_test_split(np.arange(len(clean)), test_size=0.25, random_state=0)
a_shuf = accuracy_score(y[i2], RandomForestClassifier(n_estimators=200, random_state=1)
                        .fit(Xq[i1], y[i1]).predict(Xq[i2]))
a_unit = accuracy_score(y[te], RandomForestClassifier(n_estimators=200, random_state=1)
                        .fit(Xq[tr], y[tr]).predict(Xq[te]))
print(f"shuffled assessments -> accuracy {a_shuf:.1%}   <- flattering, and wrong")
print(f"split by unit        -> accuracy {a_unit:.1%}   <- what a new transformer will look like")
''')],
    built="""A sealed set of transformers, and a demonstration that the easy split would have overstated the
result.""",
    takeaway="""Group the split by asset — repeated assessments of one transformer leak the answer.""",
)

# ---------------------------------------------- PHASE 5
step(
    id="duval", phase=4, icon="🔺", ai_icon="📖",
    civil="The Duval Triangle", ai="The Expert Rulebook",
    tech="%CH₄, %C₂H₄, %C₂H₂ → a fault type",
    site="""The industry already has a diagnostic method, and it is a good one. The **Duval Triangle** (IEC 60599)
takes three gases — methane, ethylene and acetylene — normalises them to percentages, plots the point on
a triangle, and reads the fault type off the zone it lands in.""",
    challenge="""It is a *fault-type* method, not a *condition* method. It tells you the fault is thermal rather than
electrical. It says nothing about **how bad it is**, and it ignores moisture, partial discharge, oil
quality, loading history and age entirely. Two units in the same zone can need completely different
actions.""",
    ai_link="""So the rulebook is not replaced — it is the baseline that has to be beaten, and the explanation the
engineer will check the model against. Build it first, then measure exactly where it runs out.""",
    bridge=[("Three gases", "A published rule"),
            ("Read off the zone", "Fault type, not severity"),
            ("Nothing else counted", "The baseline to beat")],
    body=[("co", r'''
def duval_coords(ch4, c2h4, c2h2):
    "Normalise the three gases to percentages - the Duval Triangle's coordinates."
    tot = np.clip(ch4 + c2h4 + c2h2, 1e-9, None)
    return 100*ch4/tot, 100*c2h4/tot, 100*c2h2/tot

def duval_zone(ch4, c2h4, c2h2):
    """Duval Triangle 1 fault zones, as published in IEC 60599 (simplified boundaries).

    PD  partial discharge      D1 low-energy discharge    D2 high-energy arcing
    T1  thermal < 300 C        T2 thermal 300-700 C       T3 thermal > 700 C
    DT  mixed thermal/electrical
    """
    m, e, a = duval_coords(ch4, c2h4, c2h2)
    out = np.full(np.shape(m), "DT", dtype=object)
    out = np.where(m >= 98, "PD", out)
    out = np.where((a >= 13) & (e <= 23) & (out == "DT"), "D1", out)
    out = np.where((a >= 13) & (e > 23) & (e <= 40) & (out == "DT"), "D2", out)
    out = np.where((a >= 29) & (e > 40) & (out == "DT"), "D2", out)
    out = np.where((a < 4) & (e < 20) & (out == "DT"), "T1", out)
    out = np.where((a < 4) & (e >= 20) & (e < 50) & (out == "DT"), "T2", out)
    out = np.where((a < 15) & (e >= 50) & (out == "DT"), "T3", out)
    return out

clean["duval"] = duval_zone(clean.ch4_ppm.values, clean.c2h4_ppm.values, clean.c2h2_ppm.values)

# how often does the published rule name the fault that is actually present?
known = clean.fault_type != "normal"
agree = float((clean.duval[known] == clean.fault_type[known]).mean())
print(f"Duval names the correct fault type on {agree:.1%} of the units that actually have one.")
print("(the rest land in DT or a neighbouring zone - real DGA is genuinely ambiguous)\n")

# and the point of this step: does the zone tell you the CONDITION?
piv = pd.crosstab(clean.duval, clean.health_class, normalize="index")
piv.columns = [HEALTH_CLASSES[c] for c in piv.columns]
print("Condition, given the Duval zone (row-normalised):")
print((piv*100).round(1).to_string())

m, e, a = duval_coords(clean.ch4_ppm.values, clean.c2h4_ppm.values, clean.c2h2_ppm.values)
fig = go.Figure(go.Scatterternary(
    a=m, b=e, c=a, mode="markers",
    marker=dict(size=5, color=clean.health_class,
                colorscale=[[0, GREEN], [0.33, CYAN], [0.66, AMBER], [1, RED]],
                showscale=True, colorbar=dict(title="condition", tickvals=[0, 1, 2, 3],
                                              ticktext=HEALTH_CLASSES)),
    text=clean.duval, hovertemplate="%{text}<extra></extra>"))
fig.update_layout(title="the Duval Triangle — colour is the CONDITION, position is the fault TYPE",
                  ternary=dict(sum=100,
                               aaxis=dict(title="%CH₄"), baxis=dict(title="%C₂H₄"),
                               caxis=dict(title="%C₂H₂")),
                  height=520, template="plotly_white")
fig.show()
'''),
          ("md", r"""
Look at the colours on that triangle. **Every zone contains all four conditions.**

That is the finding this whole step exists to produce. The Duval Triangle is doing its job correctly — it
answers *what kind of fault is this?* — and the maintenance question is a different one: *how bad is it,
and what should we do this week?*

Answering that needs moisture, partial discharge, oil breakdown voltage, loading history and age, none of
which the triangle takes as input. That is the gap the model fills, and it is why the model has to be an
**addition** to the rulebook rather than a replacement for it.
""")],
    built="""The published diagnostic method, implemented and measured — including the precise respect in which it
does not answer the maintenance question.""",
    takeaway="""The Duval Triangle names the fault type; it cannot tell you the condition or the action.""",
)

step(
    id="ml-baseline", phase=4, icon="🩺", ai_icon="🌲",
    civil="Health From The Measurements", ai="Classification",
    tech="Decision Tree vs Random Forest vs Gradient Boosting",
    site="""The question the asset manager actually asks: given everything measured on this unit, which of the four
condition bands is it in?""",
    challenge="""Sixteen measurements interact. A hot unit with clean oil is different from a cool unit with acetylene.
Age matters, but only in combination with what the oil is doing. No threshold table captures that, which
is why condition assessment has always needed an experienced engineer.""",
    ai_link="""Classification learns those interactions from the fleet's own history. Three models of increasing
capability, all scored on **sealed units** — and all measured against both the always-say-Healthy
baseline and the Duval rulebook.""",
    bridge=[("Which condition band?", "Classification"),
            ("Sixteen interacting inputs", "Learned from the fleet"),
            ("Beat the rulebook", "Scored on sealed units")],
    body=[("co", r'''
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import classification_report, r2_score, mean_absolute_error
from sklearn.ensemble import GradientBoostingClassifier

X = clean[SENSORS].values
models = {
    "Decision Tree":     DecisionTreeClassifier(max_depth=6, random_state=42,
                                                class_weight="balanced"),
    "Random Forest":     RandomForestClassifier(n_estimators=300, random_state=42,
                                                class_weight="balanced_subsample"),
    "Gradient Boosting": GradientBoostingClassifier(random_state=42),
}
base = clean.health_class.value_counts(normalize=True).max()
for name, m in models.items():
    m.fit(X[tr], y[tr])
    print(f"{name:19s} accuracy {accuracy_score(y[te], m.predict(X[te])):.1%}")
print(f"{'always say Healthy':19s} accuracy {base:.1%}   <- the bar\n")

health_model = models["Random Forest"]
pred = health_model.predict(X[te])
print(classification_report(y[te], pred, target_names=HEALTH_CLASSES, digits=3, zero_division=0))

# the health index itself, as a number rather than a band
hi_model = RandomForestRegressor(n_estimators=300, random_state=42).fit(
    X[tr], clean.health_index.values[tr])
hi_pred = hi_model.predict(X[te])
print(f"health index (0-100)  MAE {mean_absolute_error(clean.health_index.values[te], hi_pred):.2f}"
      f"   R2 {r2_score(clean.health_index.values[te], hi_pred):.3f}")

fig = go.Figure(go.Scatter(x=clean.health_index.values[te], y=hi_pred, mode="markers",
                           marker=dict(size=6, color=y[te],
                                       colorscale=[[0, GREEN], [0.33, CYAN],
                                                   [0.66, AMBER], [1, RED]], opacity=0.7)))
fig.add_trace(go.Scatter(x=[0, 100], y=[0, 100], mode="lines",
                         line=dict(color=MUTED, dash="dash"), showlegend=False))
fig.update_layout(title="predicted vs assessed health index, on transformers never seen",
                  xaxis_title="assessed health index", yaxis_title="predicted",
                  template="plotly_white", height=430)
fig.show()
''')],
    built="""A condition classifier and a health-index regressor, both scored on transformers the models have never
seen, and both compared against the naive baseline.""",
    takeaway="""Machine Learning assesses transformer condition from the measurements — the part the rulebook could not do.""",
)

step(
    id="drivers", phase=4, icon="🎚️", ai_icon="📊",
    civil="What Drives The Assessment", ai="Explainable AI",
    tech="Global importance, and the reasons for one unit",
    site="""No asset engineer will act on a condition score they cannot interrogate. The first question will be:
*why does it say that?*""",
    challenge="""Sixteen correlated inputs. Hot units are often heavily loaded and often old. A number on its own —
however accurate — will not authorise an outage.""",
    ai_link="""Two levels of explanation. **Global** importance says what drives the assessment across the fleet, and
is checkable against engineering intuition. **Local** reasons say why *this* unit scored what it did, and
that is what goes on the recommendation.""",
    bridge=[("Why does it say that?", "feature_importances_"),
            ("For the fleet", "Global explanation"),
            ("For this unit", "Local reasons")],
    body=[("co", r'''
imp = health_model.feature_importances_
o = np.argsort(imp)[::-1]
fig = go.Figure(go.Bar(x=[SENSORS[i] for i in o[:10]], y=imp[o[:10]],
                       marker_color=CYAN, text=[f"{imp[i]:.2f}" for i in o[:10]],
                       textposition="outside"))
fig.update_layout(title="what drives the condition assessment, across the whole fleet",
                  yaxis_title="importance", template="plotly_white", height=400)
fig.show()
print("top drivers: " + ", ".join(f"{SENSORS[i]} {imp[i]:.2f}" for i in o[:5]), "\n")

# --- local explanation: why did THIS unit score what it did?
THRESH = dict(h2_ppm=100, ch4_ppm=120, c2h4_ppm=150, c2h2_ppm=2, co_ppm=900,
              moisture_ppm=25, pd_pc=500, hotspot_c=110, ageing_rate=2.0)
NICE_REASON = {
    "h2_ppm": "hydrogen elevated (partial discharge indicator)",
    "ch4_ppm": "methane elevated (low-temperature thermal fault)",
    "c2h4_ppm": "ethylene elevated (high-temperature thermal fault)",
    "c2h2_ppm": "ACETYLENE PRESENT (arcing)",
    "co_ppm": "carbon monoxide elevated (paper insulation degrading)",
    "moisture_ppm": "moisture in oil above limit",
    "pd_pc": "partial discharge activity elevated",
    "hotspot_c": "hot-spot temperature above the reference 110 C",
    "ageing_rate": "insulation ageing faster than design rate",
}

def reasons_for(row):
    "Engineering reasons, in the language of the standards, not of the model."
    out = []
    for k, lim in THRESH.items():
        v = float(row[k])
        if v > lim:
            out.append(f"{NICE_REASON[k]} ({v:,.1f} vs {lim:,.0f})")
    if float(row["oil_bdv_kv"]) < 40:
        out.append(f"oil breakdown voltage low ({row['oil_bdv_kv']:.0f} kV vs 40 kV)")
    if float(row["age_years"]) > 30:
        out.append(f"unit is {row['age_years']:.0f} years old")
    return out

worst = clean[te].sort_values("health_index").iloc[0]
print(f"Unit {worst.unit_id} — assessed {HEALTH_CLASSES[int(worst.health_class)]} "
      f"(health index {worst.health_index:.0f}), Duval zone {worst.duval}")
print("Reasons a report would give:")
for r_ in reasons_for(worst):
    print("  ·", r_)
'''),
          ("md", r"""
Check the global ranking against what a transformer engineer would say:

- **Gas concentrations and partial discharge lead.** They should: they are the only measurements that see
  inside the tank.
- **Ageing rate** ranks above raw temperature, which is the right answer — 95 °C on a cold day and 95 °C
  on a hot day mean different things about the loading that produced them.
- **Age** matters, but less than what the oil is doing. An old transformer in good condition is a good
  transformer.

The local reasons are deliberately written in the language of **IEC 60599 and IEEE C57.104 limits**, not in
the language of the model. "Acetylene present" is a sentence an engineer can act on. "Feature 12
contributed 0.31" is not.
""")],
    built="""Two levels of explanation: a fleet-wide ranking that can be checked against intuition, and per-unit
reasons written in the language of the standards.""",
    takeaway="""A condition score nobody can interrogate will not authorise an outage — explain it in standards, not features.""",
)

# ---------------------------------------------- PHASE 6
step(
    id="thermal-problem", phase=5, icon="📷", ai_icon="🖼️",
    civil="The Infrared Survey", ai="Raw Pixels As Input",
    tech="A 64×64 grid of temperatures, no named columns",
    site="""Thermographic survey of the compound. The camera sees the tank, the radiator bank, the bushings and the
cooling fans — everything the oil sample cannot see, because it is all outside the tank.""",
    challenge="""Three faults matter here, and only one of them is *hot*. A bushing connection running hot is bright. A
**blocked radiator is cold** — oil has stopped circulating through it. Failed cooling fans leave
**alternate radiators cold**. And a tank in full sun is warm everywhere and perfectly healthy.""",
    ai_link="""So the image cannot be reduced to a temperature. Machine Learning needs named features and there are
none — only 4,096 pixels. Before reaching for a CNN, it is worth trying to build the feature by hand.""",
    bridge=[("Hot bushing = fault", "4,096 numbers"),
            ("COLD radiator = fault", "No column names"),
            ("Warm in the sun = fine", "Nothing to weight")],
    body=[("co", r'''
KINDS = ["normal", "hotspot", "blocked_cooling", "uneven_cooling", "solar_load"]
IS_FAULT = {"normal": False, "hotspot": True, "blocked_cooling": True,
            "uneven_cooling": True, "solar_load": False}

fig = make_subplots(rows=1, cols=5, subplot_titles=[
    f"{k}<br><sub>{'FAULT' if IS_FAULT[k] else 'healthy'}</sub>" for k in KINDS])
for j, k in enumerate(KINDS, start=1):
    fig.add_trace(go.Heatmap(z=make_thermal(k), colorscale="Inferno", showscale=False,
                             zmin=0, zmax=1), row=1, col=j)
    fig.update_xaxes(visible=False, row=1, col=j)
    fig.update_yaxes(visible=False, autorange="reversed", row=1, col=j)
fig.update_layout(height=300, template="plotly_white",
                  title="five surveys — one fault is hot, two are COLD, and one warm unit is fine")
fig.show()

z = make_thermal("blocked_cooling")
print(f"The survey is {z.shape[0]} x {z.shape[1]} = {z.size:,} temperature values.")
print("Which one of them is 'blocked radiator'?  None.")
print("It is the ABSENCE of heat in two of four radiator banks - a pattern, not a value.")
''')],
    built="""The image problem, and the detail that makes it interesting: in this asset class, two of the three
faults are colder than a healthy unit.""",
    takeaway="""A cooling fault is colder than a healthy transformer — there is no 'alarm above X' that finds it.""",
)

step(
    id="handmade", phase=5, icon="✋", ai_icon="🔢",
    civil="Setting A Temperature Alarm", ai="Hand-Crafted Features",
    tech="One number from 4,096 pixels — and what it misses",
    site="""The standard approach, and the one every thermography programme starts with: take the maximum (or mean)
temperature in the frame and alarm above a threshold.""",
    challenge="""It cannot work here, and the reason is physical rather than statistical. The blocked radiator and the
failed fans **reduce** the temperature. Sun on the tank **raises** it with nothing wrong. The alarm fires
on the sunshine and stays silent on the cooling failure.""",
    ai_link="""The feature was hand-made and it measures the wrong thing. What matters is the *pattern* — one bushing
hotter than its two neighbours, or two radiators colder than the other two. That is a comparison between
regions, which no single global statistic can hold.""",
    bridge=[("Alarm above a limit", "One feature"),
            ("Cooling faults are cold", "One threshold"),
            ("Sun is warm and fine", "It fails both ways")],
    body=[("co", r'''
stats = []
for k in KINDS:
    im = make_thermal(k, seed=1)
    stats.append(dict(survey=k, fault=IS_FAULT[k],
                      mean=round(float(im.mean()), 3), max=round(float(im.max()), 3)))
st = pd.DataFrame(stats)
print(st.to_string(index=False), "\n")

print("Try every threshold you like, on either statistic:\n")
for stat in ["mean", "max"]:
    for thr in np.round(np.linspace(st[stat].min()+0.01, st[stat].max()-0.005, 4), 3):
        missed = [r.survey for r in st.itertuples() if r.fault and getattr(r, stat) <= thr]
        false_ = [r.survey for r in st.itertuples() if not r.fault and getattr(r, stat) > thr]
        print(f"  alarm on {stat} > {thr:.3f}  ->  missed {missed or ['none']}, "
              f"false alarm on {false_ or ['none']}")
    print()

fig = go.Figure()
for stat, col in [("mean", CYAN), ("max", AMBER)]:
    fig.add_trace(go.Bar(x=st.survey, y=st[stat], name=stat, marker_color=col))
fig.update_layout(barmode="group", title="one number per survey — green bars are healthy units",
                  template="plotly_white", height=380,
                  xaxis=dict(ticktext=[f"{s}<br>{'FAULT' if f else 'healthy'}"
                                       for s, f in zip(st.survey, st.fault)],
                             tickvals=list(st.survey)))
fig.show()

print("The cooling faults sit BELOW the healthy unit on the mean, and the sunlit healthy unit")
print("sits above it. No threshold on either statistic separates fault from healthy, because")
print("the fault is a relationship between regions - not a level.")
''')],
    built="""A hand-made feature that fails in **both** directions, for a reason that is physical and can be stated
in one sentence.""",
    takeaway="""The fault is a relationship between regions, not a temperature — no global statistic can hold it.""",
)

# ---------------------------------------------- PHASE 7
step(
    id="cnn", phase=6, icon="🧩", ai_icon="🧠",
    civil="Reading The Thermal Pattern", ai="Convolution & Feature Maps",
    tech="filters → feature maps → a fault class",
    site="""A thermographer does not read a survey as a temperature. They compare: is this bushing hotter than the
other two? Are all four radiator banks the same? Is the top of the tank warmer than the bottom, as it
should be?""",
    challenge="""Every one of those is a **comparison between places in the image**. No pixel holds it, and no average
holds it.""",
    ai_link="""A convolution is exactly that comparison, done everywhere at once: a small filter slides over the frame
and reports where its pattern occurs. Early filters find edges and gradients; later ones combine them
into 'a hot region among cool ones'. The network learns the filters from labelled surveys.""",
    bridge=[("Compare bushing to bushing", "Filters slide"),
            ("Compare bank to bank", "Edges → regions"),
            ("Everywhere at once", "Filters are learned")],
    body=[("co", r'''
from numpy.lib.stride_tricks import sliding_window_view

def conv2d(img, k):
    return np.einsum("ijkl,kl->ij", sliding_window_view(img, k.shape), k)

img = make_thermal("blocked_cooling")
k_vert = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], float)     # vertical edges
k_blob = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], float)    # local contrast
ladder = [("Thermal survey", img, "4,096 raw values"),
          ("Edges", np.abs(conv2d(img, k_vert)), "where temperature steps"),
          ("Temperature regions", np.abs(conv2d(img, k_blob)), "local contrast, not level"),
          ("Heat pattern", conv2d(np.abs(conv2d(img, k_blob)), np.ones((5, 5))/25),
           "which banks differ")]
fig = make_subplots(rows=1, cols=4, subplot_titles=[f"{n}<br><sub>{s}</sub>" for n, _, s in ladder])
for j, (_, z, _) in enumerate(ladder, start=1):
    fig.add_trace(go.Heatmap(z=z, colorscale="Inferno", showscale=False), row=1, col=j)
    fig.update_xaxes(visible=False, row=1, col=j)
    fig.update_yaxes(visible=False, autorange="reversed", row=1, col=j)
fig.update_layout(height=300, template="plotly_white",
                  title="thermal survey → edges → temperature regions → heat pattern → fault")
fig.show()
print("Local contrast survives where the raw level did not: the cold banks stand out")
print("precisely BECAUSE their neighbours are warm. That is a comparison, and it is what")
print("a convolution computes.")
'''),
          ("co", r'''
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    KERAS = True
    tf.random.set_seed(42)
except Exception as e:                                  # noqa: BLE001
    KERAS = False
    print("TensorFlow not available - the CNN cells will skip.", e)
print("Keras available:", KERAS)
'''),
          ("co", r'''
# Three classes an inspection actually distinguishes, because each has a different action.
THERMAL_CLASSES = ["healthy", "hotspot", "cooling_fault"]
THERMAL_LABEL = {"normal": 0, "solar_load": 0, "hotspot": 1,
                 "blocked_cooling": 2, "uneven_cooling": 2}

def make_survey_set(n=1500, seed=0):
    rng = np.random.default_rng(seed)
    pool = KINDS
    p = [0.24, 0.26, 0.18, 0.16, 0.16]
    Xi, yi = [], []
    for _ in range(n):
        k = pool[int(rng.choice(len(pool), p=p))]
        im = make_thermal(k, seed=int(rng.integers(1e6)))
        # emissivity, camera gain and sun vary between surveys
        im = np.clip(im*rng.uniform(0.88, 1.14) + rng.normal(0, 0.02) + rng.normal(0, 0.015,
                                                                                   im.shape), 0, 1)
        Xi.append(im); yi.append(THERMAL_LABEL[k])
    return np.array(Xi)[..., None].astype("float32"), np.array(yi)

Xi, yi = make_survey_set(1500, seed=1)
Xi_tr, Xi_te, yi_tr, yi_te = train_test_split(Xi, yi, test_size=0.25,
                                              random_state=42, stratify=yi)
print("surveys:", Xi.shape, " class balance:", (np.bincount(yi)/len(yi)).round(3))

if KERAS:
    inp = keras.Input(shape=(64, 64, 1))
    x = layers.Conv2D(16, 3, activation="relu", padding="same")(inp)
    x = layers.MaxPooling2D()(x)
    x = layers.Conv2D(32, 3, activation="relu", padding="same")(x)
    x = layers.MaxPooling2D()(x)
    x = layers.Conv2D(64, 3, activation="relu", padding="same", name="last_conv")(x)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(32, activation="relu")(x)
    out = layers.Dense(3, activation="softmax")(x)
    cnn = keras.Model(inp, out)
    cnn.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    cw = {i: float(len(yi_tr)/(3*c)) for i, c in enumerate(np.bincount(yi_tr))}
    hist = cnn.fit(Xi_tr, yi_tr, validation_split=0.2, epochs=25, batch_size=32,
                   class_weight=cw, verbose=0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=hist.history["loss"], name="training loss",
                             line=dict(color=CYAN, width=2)))
    fig.add_trace(go.Scatter(y=hist.history["val_loss"], name="validation loss",
                             line=dict(color=AMBER, width=2)))
    fig.update_layout(title="CNN training", xaxis_title="epoch", yaxis_title="loss",
                      template="plotly_white", height=360)
    fig.show()

    cnn_acc = float(cnn.evaluate(Xi_te, yi_te, verbose=0)[1])
    from sklearn.metrics import confusion_matrix as _cm
    print(f"CNN accuracy on held-out surveys: {cnn_acc:.1%}\n")
    print(pd.DataFrame(_cm(yi_te, cnn.predict(Xi_te, verbose=0).argmax(1)),
                       index=THERMAL_CLASSES, columns=THERMAL_CLASSES).to_string())
    print("\nthe two cases that defeated the temperature alarm:")
    for k in ["solar_load", "blocked_cooling"]:
        p = cnn.predict(make_thermal(k, seed=77)[None, ..., None].astype("float32"), verbose=0)[0]
        print(f"  {k:16s} (truth: {THERMAL_CLASSES[THERMAL_LABEL[k]]:13s}) "
              f"-> CNN says '{THERMAL_CLASSES[int(p.argmax())]}' ({p.max():.0%})")
else:
    cnn_acc = None
''')],
    built="""A thermal fault classifier that separates a sunlit healthy transformer from a genuine cooling failure —
which no threshold on temperature could do.""",
    takeaway="""Convolution compares regions, which is what a thermographer does and what a threshold cannot.""",
)

step(
    id="gradcam", phase=6, icon="📍", ai_icon="🗺️",
    civil="Which Part Of The Transformer?", ai="Grad-CAM",
    tech="class-weighted feature maps → a heat map",
    site="""A fault class alone does not raise a work order. The team needs to know **which bushing**, or **which
radiator bank** — those are different jobs, different outages and different spares.""",
    challenge="""A classifier outputs a probability. In this industry that is not enough to authorise an outage on a unit
feeding twenty thousand customers.""",
    ai_link="""Grad-CAM weights the last feature maps by how much each pushed the score towards the predicted class and
projects them back onto the survey. On a hotspot it should light the offending bushing; on a cooling
fault it should light the **cold** banks.""",
    bridge=[("Which bushing?", "Weight the maps"),
            ("Which radiator bank?", "Project onto the survey"),
            ("Before an outage", "Show the evidence")],
    body=[("co", r'''
def grad_cam(model, image, layer_name="last_conv"):
    grad_model = keras.Model(model.inputs,
                             [model.get_layer(layer_name).output, model.output])
    with tf.GradientTape() as tape:
        maps, pred = grad_model(image[None, ...])
        ci = int(tf.argmax(pred[0]))
        score = pred[:, ci]
    grads = tape.gradient(score, maps)[0]
    w = tf.reduce_mean(grads, axis=(0, 1))
    cam = tf.reduce_sum(maps[0]*w, axis=-1).numpy()
    cam = np.maximum(cam, 0); cam = cam/(cam.max() + 1e-9)
    rep = image.shape[0]//cam.shape[0]
    return np.kron(cam, np.ones((rep, rep)))[:image.shape[0], :image.shape[1]], ci

if KERAS:
    show_set = ["hotspot", "blocked_cooling", "uneven_cooling", "solar_load"]
    fig = make_subplots(rows=2, cols=4, vertical_spacing=0.14, subplot_titles=[""]*8)
    titles = []
    for j, k in enumerate(show_set, start=1):
        im = make_thermal(k, seed=31)[..., None].astype("float32")
        cam, ci = grad_cam(cnn, im)
        p = cnn.predict(im[None, ...], verbose=0)[0]
        titles.append(f"{k}<br><sub>called '{THERMAL_CLASSES[ci]}' ({p[ci]:.0%})</sub>")
        fig.add_trace(go.Heatmap(z=im[..., 0], colorscale="Inferno", showscale=False,
                                 zmin=0, zmax=1), row=1, col=j)
        fig.add_trace(go.Heatmap(z=cam, colorscale="Turbo", showscale=False), row=2, col=j)
        for r in (1, 2):
            fig.update_xaxes(visible=False, row=r, col=j)
            fig.update_yaxes(visible=False, autorange="reversed", row=r, col=j)
    for a, t in zip(fig.layout.annotations[:4], titles):
        a.text = t
    for a in fig.layout.annotations[4:]:
        a.text = "where it looked"
    fig.update_layout(height=600, template="plotly_white",
                      title="Grad-CAM — the evidence behind each thermal call")
    fig.show()
    print("On the hotspot survey the heat sits on the offending bushing.")
    print("On the cooling faults it sits on the radiator bank - and note what that means:")
    print("the network learned to attend to a region because it is COLDER than its neighbours.")
else:
    print("Keras not available - skipping Grad-CAM.")
''')],
    built="""A location as well as a class — the bushing or the radiator bank — which is what turns a probability
into a work order.""",
    takeaway="""Grad-CAM names the component, and that is what an outage request actually needs.""",
)

# ---------------------------------------------- PHASE 8
step(
    id="audit", phase=7, icon="🧮", ai_icon="✅",
    civil="The Maintenance Audit", ai="Precision, Recall & The Cost Matrix",
    tech="AI recommendation vs the engineer's decision",
    site="""Before any of this reaches a maintenance plan, it is audited against what the engineer actually decided,
on transformers the model has never seen.""",
    challenge="""Accuracy is close to useless here. The classes are unbalanced and — far more importantly — the two ways
of being wrong differ by three orders of magnitude in cost. An unnecessary inspection costs a few
thousand. A missed high-risk unit costs a failure, an outage and a replacement.""",
    ai_link="""Report **recall on the High Risk class** as the headline, precision alongside it, and put money on the
confusion matrix with an explicit cost per error type.""",
    bridge=[("Compared to the engineer", "Precision & recall"),
            ("Two very unequal errors", "A cost matrix"),
            ("Recall on High Risk", "The headline number")],
    body=[("co", r'''
from sklearn.metrics import confusion_matrix, precision_score, recall_score

cm = confusion_matrix(y[te], pred)
fig = go.Figure(go.Heatmap(z=cm, x=HEALTH_CLASSES, y=HEALTH_CLASSES, colorscale="Blues",
                           showscale=False, text=cm, texttemplate="%{text}"))
fig.update_layout(title="AI assessment (columns) vs the engineer's decision (rows), sealed units",
                  xaxis_title="AI recommended", yaxis_title="engineer assessed",
                  height=430, template="plotly_white")
fig.update_yaxes(autorange="reversed")
fig.show()

hr = len(HEALTH_CLASSES)-1
print(f"overall accuracy                    {accuracy_score(y[te], pred):.1%}")
print(f"recall on '{HEALTH_CLASSES[hr]}'            {recall_score(y[te], pred, labels=[hr], average='macro', zero_division=0):.1%}"
      "   <- the number that matters")
print(f"precision on '{HEALTH_CLASSES[hr]}'         {precision_score(y[te], pred, labels=[hr], average='macro', zero_division=0):.1%}")
print(f"macro recall across all four        {recall_score(y[te], pred, average='macro', zero_division=0):.1%}\n")

# --- put money on the errors
COST_UNNECESSARY = 4_000      # an inspection or maintenance visit that was not needed
COST_MISSED      = 260_000    # a missed high-risk unit: failure, outage, emergency replacement
over  = int(np.sum(pred > y[te]))                      # more cautious than the engineer
under = int(np.sum(pred < y[te]))                      # less cautious than the engineer
missed_hr = int(np.sum((y[te] == hr) & (pred < hr)))   # called a high-risk unit something milder

print(f"more cautious than the engineer : {over:4d} assessments  (cost {over*COST_UNNECESSARY:,})")
print(f"less cautious than the engineer : {under:4d} assessments")
print(f"  of which HIGH RISK downgraded : {missed_hr:4d}  (exposure {missed_hr*COST_MISSED:,})")
print(f"\nfailure prevention rate (high-risk units correctly escalated): "
      f"{1 - missed_hr/max(int((y[te] == hr).sum()), 1):.1%}")
'''),
          ("md", r"""
### The errors do not cost the same, and the model should not pretend they do

| Error | What happens | Order of cost |
|---|---|---|
| **More cautious than the engineer** | A unit is inspected and found to be fine. | thousands |
| **Less cautious, by one band** | A routine job is deferred a quarter. | recoverable |
| **A High Risk unit called Healthy** | It runs until it fails. Outage, emergency replacement, possibly a fire. | hundreds of thousands |

That asymmetry is why `class_weight="balanced"` was set back at the model, why **recall on High Risk** is
the headline rather than accuracy, and why the system is built to **propose** rather than to decide.

It is also the honest limit of the whole project: a model tuned to miss almost nothing will
over-recommend, and an engineer who is sent to twenty healthy transformers will stop reading the
recommendations. The operating point is an engineering decision, not a hyperparameter.
""")],
    built="""An audit in the units this industry manages by: recall on the class that matters, and money on both
kinds of error.""",
    takeaway="""Accuracy hides the only error that matters — report recall on High Risk, and price both mistakes.""",
)

step(
    id="proof", phase=7, icon="⚔️", ai_icon="🏁",
    civil="The Verdict", ai="Rulebook vs ML vs DL",
    tech="three methods, measured on the same sealed units",
    site="""Three approaches have now been built on the same fleet: the published Duval rulebook, a classifier on
the measurements, and a CNN on the thermal surveys. Time to say plainly what each can and cannot do.""",
    challenge="""It is tempting to declare the CNN the clever part. It is not the point. The condition assessment — the
thing the asset manager actually asks for — comes from the measurements.""",
    ai_link="""Each method answers a different question, and none of them answers all three. That is why the final
system fuses them rather than picking one.""",
    bridge=[("Rulebook → fault type", "Published, explainable"),
            ("ML → condition", "Learned from the fleet"),
            ("DL → external faults", "Learned from pixels")],
    body=[("co", r'''
print("THE SAME SEALED TRANSFORMERS, THREE METHODS\n")
print(f"  Duval Triangle  — names the fault type            : {agree:.1%} of faulted units")
print(f"                  — assesses the CONDITION           : it cannot. No severity input.")
print(f"  Random Forest   — condition class                  : {accuracy_score(y[te], pred):.1%}")
print(f"                  — health index (0-100)             : MAE "
      f"{mean_absolute_error(clean.health_index.values[te], hi_pred):.1f}")
print(f"                  — external cooling fault           : it cannot. It never sees the survey.")
print(f"  CNN             — thermal fault from the survey    : "
      f"{f'{cnn_acc:.1%}' if cnn_acc else '(Keras unavailable here)'}")
print(f"                  — condition from measurements      : it cannot. No named features.\n")

pd.DataFrame({
    "question": ["What KIND of fault is it?", "How BAD is the condition?",
                 "Is a bushing or radiator failing?", "Who provides the features?",
                 "Explainable to a regulator?"],
    "Duval Triangle":  ["yes, from 3 gases", "no", "no", "the standard", "fully — it is published"],
    "ML on measurements": ["indirectly", "yes", "no", "the engineer", "feature importance + limits"],
    "DL on surveys":   ["no", "no", "yes, with the location", "the network", "Grad-CAM shows the region"],
})
'''),
          ("md", r"""
### The promise, demonstrated

> **Machine Learning evaluates transformer health from structured sensor data.
> Deep Learning discovers fault patterns in thermal images that feature engineering cannot capture.
> Together they provide a maintenance recommendation an engineer can act on.**

Note where each one fails, because that is the part worth remembering:

- The **rulebook** cannot rank severity — every Duval zone contained all four conditions.
- The **classifier** cannot see outside the tank — a blocked radiator produces no dissolved gas at all.
- The **CNN** cannot assess condition — it never sees the oil.

Three blind spots, three methods, and none of them redundant.
""")],
    built="""The central claim, measured — and, more usefully, a clear statement of what each method cannot do.""",
    takeaway="""Rulebook, measurements and images answer three different questions; the system needs all three.""",
)

# ---------------------------------------------- PHASE 9
step(
    id="decision", phase=8, icon="🎛️", ai_icon="💡",
    civil="The Decision Support Screen", ai="Explainable Recommendation",
    tech="measurements + survey → action, confidence, reasons",
    site="""This is what the engineer actually receives: one unit, one recommended action, a confidence, and the
engineering reasons behind it.""",
    challenge="""Four actions are possible and they differ enormously in cost and disruption: continue, schedule
routine work, inspect immediately, or plan replacement. A bare class number will not justify any of
them.""",
    ai_link="""The recommendation assembles the condition class, the health index, the Duval fault type, the thermal
call and the standards-based reasons into one screen — and states its confidence so the engineer knows
when the system is unsure.""",
    bridge=[("Four possible actions", "Combine the outputs"),
            ("Very different costs", "State the confidence"),
            ("Justify it", "Reasons from the standards")],
    body=[("co", r'''
ACTIONS = ["Continue normal operation", "Schedule routine maintenance",
           "Immediate inspection required", "Plan replacement"]

def assess_transformer(top_oil_c_v=75, load_pu_v=0.85, ambient_c_v=25, age_years_v=20,
                       h2=60, ch4=45, c2h6=30, c2h4=70, c2h2=0.4, co=500,
                       moisture=14, pd_pc_v=120, bdv=52, voltage_dev=0.5,
                       thermal_survey=None):
    """One transformer in, one recommendation out - with the reasoning attached.

    thermal_survey: one of KINDS, or None if no recent survey exists.
    """
    hs = float(hotspot_c(ambient_c_v, load_pu_v))
    row = {"age_years": age_years_v, "ambient_c": ambient_c_v, "load_pu": load_pu_v,
           "top_oil_c": top_oil_c_v, "hotspot_c": hs,
           "ageing_rate": float(ageing_factor(hs)), "voltage_dev_pct": voltage_dev,
           "load_current_a": load_pu_v*175, "h2_ppm": h2, "ch4_ppm": ch4, "c2h6_ppm": c2h6,
           "c2h4_ppm": c2h4, "c2h2_ppm": c2h2, "co_ppm": co, "moisture_ppm": moisture,
           "pd_pc": pd_pc_v, "oil_bdv_kv": bdv}
    xv = np.array([[row[s] for s in SENSORS]])

    proba = health_model.predict_proba(xv)[0]
    cls   = int(np.argmax(proba))
    hi    = float(hi_model.predict(xv)[0])
    zone  = str(duval_zone(np.array([ch4]), np.array([c2h4]), np.array([c2h2]))[0])
    why   = reasons_for(pd.Series(row))

    action = cls
    thermal = "no recent survey"
    if thermal_survey is not None:
        if KERAS:
            im = make_thermal(thermal_survey, seed=5)[None, ..., None].astype("float32")
            tp = cnn.predict(im, verbose=0)[0]
            tcall = THERMAL_CLASSES[int(tp.argmax())]
            thermal = f"{tcall} ({tp.max():.0%})"
        else:
            tcall = THERMAL_CLASSES[THERMAL_LABEL[thermal_survey]]
            thermal = f"{tcall} (rule-based, Keras unavailable)"
        if tcall != "healthy":
            why.append(f"thermal survey: {tcall} detected on the unit")
            action = max(action, 2)          # a thermal fault always earns an inspection

    if c2h2 > 5:                             # acetylene overrides everything
        action = max(action, 2)
        why.append("acetylene above 5 ppm — arcing suspected, IEC 60599 condition 3")

    return dict(action=ACTIONS[action], condition=HEALTH_CLASSES[cls],
                health_index=round(hi, 1), confidence=f"{proba[cls]:.0%}",
                duval_zone=zone, hot_spot_c=round(hs, 1),
                ageing_rate=f"{ageing_factor(hs):.1f}x", thermal=thermal,
                reasons=" · ".join(why) if why else "all measurements within limits")

scenarios = {
    "A · healthy 12-year unit": dict(top_oil_c_v=62, load_pu_v=0.62, age_years_v=12,
                                     h2=22, ch4=18, c2h4=25, c2h2=0.2, moisture=8,
                                     pd_pc_v=40, bdv=64),
    "B · the brief's example":  dict(top_oil_c_v=88, load_pu_v=0.92, age_years_v=24,
                                     h2=310, ch4=140, c2h4=180, c2h2=3.5, moisture=22,
                                     pd_pc_v=640, bdv=44, thermal_survey="hotspot"),
    "C · arcing suspected":     dict(top_oil_c_v=79, load_pu_v=0.80, age_years_v=31,
                                     h2=480, ch4=160, c2h4=420, c2h2=38, moisture=27,
                                     pd_pc_v=1500, bdv=36),
    "D · cooling failure only": dict(top_oil_c_v=71, load_pu_v=0.75, age_years_v=16,
                                     h2=35, ch4=28, c2h4=40, c2h2=0.3, moisture=11,
                                     pd_pc_v=60, bdv=58, thermal_survey="blocked_cooling"),
}
pd.set_option("display.max_colwidth", 90)
pd.DataFrame({k: assess_transformer(**v) for k, v in scenarios.items()})
'''),
          ("md", r"""
Read the four columns against what an engineer would do:

- **A** — everything inside limits, low load, young unit. Continue, and the reasons field says so
  explicitly rather than being blank.
- **B** — the example from the brief. Elevated hydrogen and ethylene, moisture over limit, partial
  discharge elevated, and a hotspot on the survey. **Immediate inspection**, with four named reasons.
- **C** — 38 ppm acetylene. This is the one case with a hard override: whatever the model's class, arcing
  earns an inspection. Some knowledge belongs in a rule, not in a weight.
- **D** — the oil is *perfect*. Every dissolved gas is normal, because a blocked radiator produces no gas.
  Only the survey found it. Without the CNN this unit would have been reported as healthy and left to
  cook.

Column D is the whole argument for the second half of this notebook, in one transformer.
""")],
    built="""A decision support screen: action, condition, health index, Duval zone, thermal call, confidence, and
reasons written in the language of the standards.""",
    takeaway="""Every recommendation carries its reasons and its confidence — that is what makes it usable.""",
)

step(
    id="fusion", phase=8, icon="🖥️", ai_icon="🔗",
    civil="The Fleet Screen", ai="AI Fusion",
    tech="measurements + DGA + survey + history → a ranked fleet",
    site="""One engineer, four hundred transformers, and a fixed number of outages available this quarter. The
question is not 'is this unit healthy' — it is **which units first**.""",
    challenge="""Ranking by any single measurement produces the wrong list. The hottest unit may simply be the most
heavily loaded. The oldest may be in excellent condition.""",
    ai_link="""Fusion combines the condition class, the health index, the thermal call and the fault type into one
ordered work list — with the reasoning on every row, so the engineer can disagree with any of it.""",
    bridge=[("400 units, few outages", "Rank the fleet"),
            ("Which one first?", "Combine every source"),
            ("With the reasoning", "Engineer can override")],
    body=[("co", r'''
sealed = clean[te].copy()
sealed["pred_class"] = pred
sealed["pred_hi"]    = hi_pred
# a survey exists for a subset of the fleet, as in reality
rng = np.random.default_rng(3)
sealed["survey"] = rng.choice(KINDS + [None]*5, size=len(sealed))

work_list = (sealed.sort_values("pred_hi")
                   .groupby("unit_id", as_index=False).first()
                   .sort_values("pred_hi").head(8))

rows = []
for _, r in work_list.iterrows():
    thermal_note = ""
    if r.survey is not None and THERMAL_LABEL[r.survey] != 0:
        thermal_note = THERMAL_CLASSES[THERMAL_LABEL[r.survey]]
    act = int(r.pred_class)
    if thermal_note:
        act = max(act, 2)
    why = reasons_for(r)[:3]
    if thermal_note:
        why.append(f"survey: {thermal_note}")
    rows.append(dict(unit=r.unit_id, age=f"{r.age_years:.0f}y",
                     health_index=f"{r.pred_hi:.0f}",
                     condition=HEALTH_CLASSES[int(r.pred_class)],
                     duval=r.duval, survey=thermal_note or "-",
                     action=ACTIONS[act],
                     reasons=" · ".join(why) if why else "within limits"))
pd.set_option("display.max_colwidth", 70)
pd.DataFrame(rows).set_index("unit")
'''),
          ("md", r"""
This is the product. Everything earlier existed to fill in these columns.

Two properties are worth naming:

- **The list is ranked by predicted health index, not by any single measurement.** A hot, heavily loaded,
  chemically clean transformer does not appear near the top, and it should not.
- **A thermal fault escalates the action regardless of the oil.** That rule is not learned — it is
  written in, because a failed cooling system will eventually produce gas, and the point is to act before
  it does.

And what it never does: change a tap, trip a breaker, or book an outage. It orders the engineer's week.
""")],
    built="""A ranked work list for the fleet, with the evidence on every row — the actual deliverable of a
condition monitoring programme.""",
    takeaway="""The output is not a score per transformer; it is an ordered list of which ones to visit first.""",
)

step(
    id="dashboard", phase=8, icon="💷", ai_icon="📉",
    civil="What It Is Worth", ai="The Business Case",
    tech="failures prevented, visits avoided, availability",
    site="""An asset manager approves a monitoring programme against avoided failures, avoided unnecessary
maintenance, and availability — not against accuracy.""",
    challenge="""The saving is easy to overstate, and this industry has heard it overstated before. The honest way is to
compute it from the audit already performed on the sealed units, with every assumption named.""",
    ai_link="""Three figures, all derived from the confusion matrix: high-risk units escalated that a periodic regime
would have missed, routine visits avoided on units confirmed healthy, and the resulting availability.""",
    bridge=[("Avoided failures", "From the confusion matrix"),
            ("Avoided visits", "From the healthy calls"),
            ("Availability", "All of it arithmetic")],
    body=[("co", r'''
FLEET             = 400
ASSESS_PER_YEAR   = 2
COST_FAILURE      = 260_000     # emergency replacement, outage, penalties
COST_VISIT        = 4_000       # a routine maintenance visit
BASELINE_DETECT   = 0.55        # a 6-monthly oil sample catches this share of developing faults
OUTAGE_DAYS       = 21          # unplanned outage after a failure

hr_mask   = (y[te] == hr)
caught    = float(np.mean(pred[hr_mask] >= hr)) if hr_mask.sum() else 0.0
healthy   = float(np.mean(pred[y[te] == 0] == 0)) if (y[te] == 0).sum() else 0.0
hr_rate   = float(hr_mask.mean())

hr_per_year      = FLEET*ASSESS_PER_YEAR*hr_rate
extra_caught     = hr_per_year*max(caught - BASELINE_DETECT, 0)
failures_avoided = extra_caught
visits_avoided   = FLEET*ASSESS_PER_YEAR*float((y[te] == 0).mean())*healthy*0.5

print("TRANSFORMER MAINTENANCE BUSINESS CASE — from the sealed-unit audit\n")
print(f"  fleet                                    {FLEET}")
print(f"  high-risk assessments per year           {hr_per_year:8.0f}")
print(f"  caught by 6-monthly sampling alone       {BASELINE_DETECT:8.0%}")
print(f"  caught by the decision support system    {caught:8.0%}")
print(f"  additional failures prevented per year   {failures_avoided:8.1f}")
print(f"    value at {COST_FAILURE:,} per failure       {failures_avoided*COST_FAILURE:12,.0f} / year")
print(f"  routine visits safely deferred           {visits_avoided:8.0f}")
print(f"    value at {COST_VISIT:,} per visit             {visits_avoided*COST_VISIT:12,.0f} / year")
print(f"  unplanned outage days avoided            {failures_avoided*OUTAGE_DAYS:8.0f} days")
print(f"  TOTAL                                    "
      f"{failures_avoided*COST_FAILURE + visits_avoided*COST_VISIT:12,.0f} / year")

fig = make_subplots(rows=1, cols=2, subplot_titles=[
    "detection of high-risk units", "where the value comes from"])
fig.add_trace(go.Bar(x=["6-monthly sampling", "with decision support"],
                     y=[BASELINE_DETECT*100, caught*100], marker_color=[AMBER, GREEN],
                     text=[f"{BASELINE_DETECT:.0%}", f"{caught:.0%}"],
                     textposition="outside", showlegend=False), row=1, col=1)
fig.add_trace(go.Bar(x=["failures prevented", "visits deferred"],
                     y=[failures_avoided*COST_FAILURE, visits_avoided*COST_VISIT],
                     marker_color=[RED, CYAN], showlegend=False), row=1, col=2)
fig.update_yaxes(title_text="% of high-risk units found", row=1, col=1)
fig.update_yaxes(title_text="currency / year", row=1, col=2)
fig.update_layout(height=400, template="plotly_white")
fig.show()
'''),
          ("md", r"""
### Read the assumptions, not the total

- **`BASELINE_DETECT = 0.55`** is the load-bearing assumption and it is a judgement, not a measurement.
  It says a six-monthly oil sample catches a bit over half of developing faults. Change it and the case
  changes proportionally. If your sampling regime is better than that, the case is smaller — and you
  should say so.
- The failure cost dominates everything. Nearly all of the value is **one column of the confusion
  matrix**: high-risk units correctly escalated. That is why the audit reported recall on that class as
  the headline.
- **Visits deferred is the smaller and riskier number.** Deferring maintenance on the strength of a model
  is a bigger cultural step than adding an inspection, and the figure above already halves it for that
  reason.
- Not counted: the failures that were going to be caught anyway, and the engineer's time spent reviewing
  recommendations. Both are real.

The system does not make the fleet younger. It changes which transformer the engineer visits first.
""")],
    built="""A business case computed from the audit rather than asserted, with the one assumption that carries it
named explicitly.""",
    takeaway="""Nearly all the value sits in one cell of the confusion matrix: the high-risk units you did not miss.""",
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
# ⚡ AI for Transformer Maintenance Decision Support
## Machine Learning vs Deep Learning, for Electrical Power Engineers

> You are not here to learn Artificial Intelligence. You are here to solve an **asset management problem**
> — deciding which transformer to touch this week, with incomplete information and expensive consequences.
> AI turns up in the middle of it, because the engineering requires it. Not before.

---

## 1 · The engineering problem

A 40 MVA 132/33 kV grid transformer, twenty-two years in service, feeding twenty thousand customers.
No installed spare. Replacement lead time in months, replacement cost in the millions.

Its condition changes every hour — loading, ambient temperature, insulation ageing, moisture ingress, oil
degradation, incipient internal faults. It is assessed by an **oil sample once or twice a year** and a
visual inspection.

A fault that begins in March is found in October. If it is found at all.

And the failure modes do not announce themselves the same way:

- An **internal thermal fault** shows up as dissolved gas in the oil, months before anything is visible.
- **Arcing** produces acetylene — a gas that barely exists otherwise, and the one nobody wants to see.
- A **blocked radiator or a failed cooling fan** produces **no gas at all**. The oil sample is perfect. The
  unit cooks quietly until something else fails.

One maintenance engineer is responsible for four hundred of these. That is not a diligence problem. It is
arithmetic.

---

## 2 · What we are going to build

A **maintenance decision support system**. Four parts:

| | Part | What it does |
|---|---|---|
| 📡 | **Sensors read the condition** | Loading, temperatures, dissolved gas analysis, moisture, partial discharge, oil quality, age — sixteen measurements per assessment. |
| 📷 | **The camera reads the outside** | Thermal survey of tank, bushings and radiators — the failure modes that produce no dissolved gas at all. |
| 🧠 | **AI assesses and ranks** | A condition class and a health index for every unit, a fault type from the gas ratios, and a thermal fault call with its location. |
| 📄 | **The engineer gets a recommendation** | One of four actions, with a confidence and the engineering reasons written in the language of the standards. |

> **The goal is not an unmanned substation.** The engineer still walks the compound, still judges whether
> an outage can be taken, still signs the switching programme, and still carries the consequence. The
> system does the thing a person cannot: assess four hundred units continuously and say **which one
> first**.

---

## 3 · The engineering workflow

One fleet, one condition monitoring programme, in the order a real project runs it — nine phases.

| Phase | In the substation | Steps |
|---|---|---|
{phase_rows()}

---

## 4 · Engineering → AI, the whole map

**Every AI concept in this notebook is a power engineering activity you already understand.** Read down the
left column and you have described a condition monitoring programme. Read down the right and you have
described a machine learning pipeline. They are the same column.

| ⚡ Power engineering process | → | 🤖 The AI process that solves it | Phase |
|---|:-:|---|:-:|
{mapping_rows()}

---

## The one idea this notebook proves

> **Machine Learning evaluates transformer health using structured sensor data.
> Deep Learning discovers fault patterns directly from thermal images that feature engineering cannot
> reliably capture. Together they provide intelligent maintenance recommendations for engineers.**

Two published standards run through the whole notebook. They generate the data, they check the models,
and they supply the language the recommendations are written in:

- **IEEE C57.91** — hot-spot temperature and the insulation ageing acceleration factor
  `F_AA = exp(15000/383 − 15000/(θ_h+273))`
- **IEC 60599 / the Duval Triangle** — fault type from the CH₄ / C₂H₄ / C₂H₂ ratios

Step {[s['id'] for s in STEPS].index('proof')+1} measures the claim.
""")

md(r"""
---

## Setup

In Colab everything below is already installed. Charts are Plotly, so they are interactive — hover, zoom
and toggle series from the legend. TensorFlow is needed only for the CNN and Grad-CAM steps; those cells
detect whether it is present and skip cleanly if not.
""")

co(r"""
# !pip install numpy pandas scikit-learn plotly tensorflow
print("Imports and the IEEE C57.91 thermal model are in step 1, below.")
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

> The power engineering activity on this page is also, exactly, the AI concept **{s['ai']}**. Here is why.

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
   SENSORS + DGA  ──► clean ──► split by UNIT ──►  CLASSIFIER  ──┐
   16 named measurements                          condition band │
                                                  HEALTH INDEX   │
   DUVAL TRIANGLE ─────────────────────────────►  fault type ────┤──►  DECISION
   published rule, 3 gas ratios                                  │     SUPPORT
                                                                 │     action ·
   THERMAL SURVEY ─────────────────────────────►  CNN + Grad-CAM ┘     confidence ·
   4,096 raw pixels                               fault + location     reasons
```

## What was built

| Stage | Method | Output |
|---|---|---|
| Hot-spot temperature & ageing | IEEE C57.91 | °C and the ageing acceleration factor |
| Fault type from gas ratios | Duval Triangle (IEC 60599) | PD / D1 / D2 / T1 / T2 / T3 |
| Condition band | Decision Tree / Random Forest / Gradient Boosting | Healthy → High Risk |
| Health index | Random Forest regression | 0–100 |
| Explanation | Feature importance + standards limits | reasons an engineer can check |
| Thermal fault | CNN, 3 classes | healthy / hotspot / cooling fault |
| Which component | Grad-CAM | the bushing or the radiator bank |
| Recommendation | Fusion + hard overrides | one of four actions, with confidence |
| Business case | The sealed-unit audit | failures prevented, visits deferred |

## The three things worth remembering

1. **Sensor and DGA measurements → Machine Learning.** The engineer named the quantities; the model
   weights them and — unlike the rulebook — ranks severity.
2. **Thermal surveys → Deep Learning.** Nobody can name 4,096 pixel columns, and two of the three faults
   here are *colder* than a healthy unit, so no temperature threshold can find them.
3. **Power System Engineer + AI.** The system ranks the fleet and explains itself. The engineer authorises
   the work and carries the consequence.

## Where the engineering discipline showed up

Six moments in this notebook were engineering judgements, not machine learning:

- **Recoding below-detection acetylene** instead of deleting it — those are the healthiest units.
- **Treating 0 pC as a dead monitor**, not a quiet transformer.
- **Splitting by unit**, because the same transformer appears several times in the log.
- **Keeping the Duval Triangle** as a baseline and an explanation, rather than replacing it.
- **A hard override on acetylene** — some knowledge belongs in a rule, not in a weight.
- **Reporting recall on High Risk** rather than accuracy, because the two errors differ by three orders
  of magnitude in cost.
""")

nb = new_notebook(cells=cells, metadata={
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"},
    "colab": {"provenance": []},
})
nbf.validate(nb)
with open("Transformer_Maintenance_DL.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"wrote Transformer_Maintenance_DL.ipynb  ({len(cells)} cells, "
      f"{sum(1 for c in cells if c.cell_type=='code')} code, {len(STEPS)} steps, {len(PHASES)} phases)")
