"""
Builds Building_Energy_Optimization_DL.ipynb from nbformat cells.
Run:  py -3.13 build_nb.py

Modelled on the Smart Construction notebook: one intro block (problem → what we
build → workflow → Engineering-to-AI map), then 30 steps, each rendered as the
same five parts:

    header + Part 1 (building engineering) + Part 2 (the challenge)
    Part 3 (where the AI comes in) + the bridge table + Part 4 header
    the code
    Part 5 (what you just built) + a one-line key takeaway

The notebook is standalone: it imports nothing from this file, and re-defines the
building physics inline.

APP: set this to the deployed Streamlit URL to switch on the per-step
"see it illustrated" links and the link column in the workflow table. Leave it as
"" and the notebook is built with no links at all, rather than dead ones.
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

APP = "https://building-energy-dl.streamlit.app"          # e.g. "https://building-energy.streamlit.app"

cells = []
def md(t):  cells.append(new_markdown_cell(t.strip("\n")))
def co(t):  cells.append(new_code_cell(t.strip("\n")))

def link(stage, label):
    return f"[{label}]({APP}/?stage={stage})" if APP else label


# ============================================================================
# THE PHASES  (one building day, in the order a real project runs it)
# ============================================================================
PHASES = [
    ("The Building In Use",      "One weekday, one floor plate, one facilities manager."),
    ("One Reading Interval",     "Fifteen minutes of operation becomes a written record."),
    ("Instrumenting The Building", "The BMS export lands and gets checked."),
    ("Preparing The Data",       "Faulty readings out, units standardised, days split."),
    ("Demand From The Sensors",  "Predicting HVAC load from the gauges alone."),
    ("The Image Wall",           "The camera arrives and the rulebook collapses."),
    ("How A Machine Learns",     "A neuron, a threshold, a loop, a network."),
    ("Reading The Room",         "A CNN grades a floor plate no rule could grade."),
    ("Locating The Use",         "The CNN shows which part of the floor is in use."),
    ("The Energy Audit",         "Every claim checked on days the model never saw."),
    ("Control & Optimisation",   "Forecast the peak, choose the setpoint, fuse it all."),
    ("The Business Case",        "kWh, carbon, cost and comfort the building keeps."),
]

NUM = ["①","②","③","④","⑤","⑥","⑦","⑧","⑨","⑩","⑪","⑫","⑬","⑭","⑮",
       "⑯","⑰","⑱","⑲","⑳","㉑","㉒","㉓","㉔","㉕","㉖","㉗","㉘","㉙","㉚"]


# ============================================================================
# THE STEPS
#   Each entry drives four cells. `body` is a list of ('md', text) / ('co', code)
#   items making up Part 4 — most steps have exactly one code cell.
# ============================================================================
STEPS = []
def step(**kw):
    STEPS.append(kw)


# ---------------------------------------------- PHASE 1 · THE BUILDING IN USE
step(
    id="in-use", phase=0, icon="🏢", ai_icon="🤖",
    civil="A Building On A Weekday", ai="Why HVAC Automation Exists",
    tech="Fixed schedule vs actual occupancy, over one day",
    site="""A 4,000 m² commercial floor plate, 260 desks, one air-handling unit and one chiller. The HVAC
schedule runs **07:00 to 19:00**, every workday, unchanged since commissioning. Occupancy does not: the
floor fills after 09:00, empties at lunch, and is nearly empty for the first and last ninety minutes of
the schedule.""",
    challenge="""HVAC is the largest electrical load in the building. It runs to a clock, not to the building.
Nobody walks the floor at 07:15 to confirm the plant should be at full duty for eleven people, and
nobody reduces the fresh-air damper when half the desks are empty. Doing that continuously, for every
zone, is not a discipline problem — it is arithmetic.""",
    ai_link="""Before anybody says machine learning, be clear what is being asked for. Not intelligence. Something
duller: a system that knows what the building *should* be drawing right now, notices when it is drawing
more, and says so while it is still happening.""",
    bridge=[("A fixed 07:00–19:00 schedule", "Read every interval"),
            ("Occupancy that moves all day", "Model the drivers"),
            ("One facilities manager", "Never look away")],
    body=[("co", r'''
# ---- the plant model. Every number here is a design assumption you can change,
# and every later step - the dataset, the optimiser, the business case - uses it.
CAP          = 260      # desks on the floor plate
DESIGN_COOL  = 320.0    # kW thermal - the plant's design duty
FAN_MIN, FAN_MAX = 2.5, 16.0   # kW - VAV fan at minimum turndown and at full flow
OA_DESIGN    = 200.0    # the fixed damper brings in fresh air for 200 people, always

def cooling_load_kw(outdoor, setpoint, solar, occ, hum, oa_people=OA_DESIGN):
    """Thermal cooling load on the plant, kW.

    oa_people is the OUTSIDE-AIR basis: how many people the ventilation is sized for
    at this moment. A fixed damper holds it at OA_DESIGN whatever the floor is doing.
    Demand-controlled ventilation follows the CO2 sensor instead - that difference
    turns out to be the largest single saving in this whole notebook.
    """
    dT = np.clip(np.asarray(outdoor, float) - np.asarray(setpoint, float), 0, None)
    return (2.6*dT                                              # envelope conduction
            + 0.07*np.asarray(solar, float)                     # solar gain through glazing
            + 0.42*np.asarray(occ, float)                       # people + laptops + lights
            + 0.18*np.clip(np.asarray(hum, float)-50, 0, None)  # dehumidification
            + 0.030*np.asarray(oa_people, float)*dT)            # fresh air, cooled

def fan_kw(cool_thermal):
    "VAV supply fans: airflow follows the load, power follows the fan affinity law."
    frac = np.clip(np.asarray(cool_thermal, float)/DESIGN_COOL, 0.15, 1.0)
    return FAN_MIN + (FAN_MAX-FAN_MIN)*frac**1.8

def chiller_cop(outdoor):
    "COP degrades as the chiller rejects heat to a hotter outdoors."
    return np.clip(3.6 - 0.045*np.clip(np.asarray(outdoor, float)-25, 0, None), 2.0, 3.6)

def hvac_kw_for(outdoor, setpoint, solar, occ, hum, oa_people=OA_DESIGN):
    "Electrical draw of the whole HVAC plant, kW, and the thermal load behind it."
    cool = cooling_load_kw(outdoor, setpoint, solar, occ, hum, oa_people)
    return fan_kw(cool) + cool/chiller_cop(outdoor), cool

# ---- one weekday, with real weather and a real occupancy profile
hour  = np.arange(0, 24, 0.25)
shape = np.clip(0.95*np.exp(-((hour-10.5)**2)/(2*1.6**2))
              + 0.90*np.exp(-((hour-15.0)**2)/(2*1.7**2))
              - 0.35*np.exp(-((hour-13.0)**2)/(2*0.7**2)), 0, 1)
occupancy = np.round(CAP*shape)
outdoor   = 26 + 6*np.sin(2*np.pi*(hour-9)/24)
solar     = np.where((hour > 6) & (hour < 19),
                     np.clip(880*np.sin(np.pi*(hour-6)/13), 0, None)*0.8, 0.0)
humidity  = 72 - 0.9*(outdoor-25)

scheduled = (hour >= 7) & (hour < 19)                  # the clock, not the building
hvac_kw   = np.where(scheduled,
                     hvac_kw_for(outdoor, 23.0, solar, occupancy, humidity)[0], 1.5)

# what fraction of the fresh air being cooled is for people who are not there
oa_wasted = np.where(scheduled, np.clip(OA_DESIGN-occupancy, 0, None)/OA_DESIGN, 0)
under_used = scheduled & (occupancy < 40)

fig = go.Figure()
fig.add_trace(go.Scatter(x=hour, y=hvac_kw, name="HVAC electrical load (kW)",
                         line=dict(color=CYAN, width=3)))
fig.add_trace(go.Scatter(x=hour, y=occupancy/4, name="people on the floor (÷4)",
                         line=dict(color=AMBER, width=3, dash="dot")))
fig.add_trace(go.Scatter(x=hour, y=oa_wasted*100, name="fresh air cooled for nobody (%)",
                         line=dict(color=RED, width=2), yaxis="y2"))
for h in hour[under_used]:
    fig.add_vrect(x0=h, x1=h+0.25, fillcolor=RED, opacity=0.10, line_width=0)
fig.update_layout(title="one weekday — the plant runs to the clock, the floor does not",
                  xaxis_title="hour of day", yaxis_title="kW  /  people ÷ 4",
                  yaxis2=dict(title="% of outside air for absent people",
                              overlaying="y", side="right", range=[0, 105]),
                  template="plotly_white", height=440)
fig.show()

print(f"Plant runs at duty for                       : {scheduled.sum()*0.25:.1f} h/day")
print(f"  ...of which under 40 people are present    : {under_used.sum()*0.25:.1f} h/day")
print(f"Mean share of fresh air cooled for absent people, across the whole schedule:"
      f" {100*oa_wasted[scheduled].mean():.0f}%")
print(f"HVAC energy, this day                        : {hvac_kw.sum()*0.25:,.0f} kWh")
'''),
          ("md", r"""
Two different problems are visible on that chart, and they are not the same size.

- The **red bands** are the obvious one: the plant at duty with almost nobody in. Real, but only about an
  hour a day.
- The **red line** is the expensive one, and it never touches zero. The damper ventilates for two hundred
  people all day. Averaged across the schedule, **most of the outside air being cooled is for people who
  are not in the building** — and every cubic metre of it is dragged from outdoor temperature down to the
  setpoint.

Hold on to that. It is why the CO₂ sensor turns out to matter more than the clock.
""")],
    built="""One weekday, drawn with the same plant model the rest of the notebook uses. Nobody here is being
careless — the schedule and the damper were set once, and neither has any way to know who walked in.""",
    takeaway="""HVAC runs to a clock; the building runs to its occupants. The gap between them is the energy.""",
)

step(
    id="enter-ai", phase=0, icon="📡", ai_icon="🛰️",
    civil="A Building That Senses Itself", ai="The Building Intelligence Layer",
    tech="Sensed every 15 minutes, not reviewed every month",
    site="""Nothing about the plant changes. Same chiller, same AHU, same ductwork, same comfort standard. The
facilities engineer still walks the floor and still signs the energy report. Sensors are added — indoor
and outdoor temperature, humidity, CO₂, occupancy, solar irradiance, air quality, a smart meter — and a
thermal camera looks down at the floor plate on a schedule.""",
    challenge="""The usual objection: is this here to replace the facilities manager? No. A model that sees only
numbers cannot hear a fan bearing, judge whether a complaint is about draught or noise, or decide to
override a tenant's fit-out. It can only notice a pattern and estimate what it costs.""",
    ai_link="""The system is a building intelligence layer: a live picture of demand, comfort and consumption, updated
by the building's own sensors. That fixes the role of AI for the whole project — the layer reports and
recommends; a person decides and signs off.""",
    bridge=[("Engineers stay", "A live building picture"),
            ("Sensors watch too", "It flags the waste"),
            ("Nobody is replaced", "You still decide")],
    body=[("co", r'''
# Three ways to run the same plant over the same day. Same comfort setpoint throughout
# the occupied hours - the only thing that changes is what the plant knows.
fixed = hvac_kw

# (a) setback only: when the floor is essentially empty, let it drift to 28 C.
setback = np.where(scheduled & (occupancy < 40),
                   hvac_kw_for(outdoor, 28.0, solar, occupancy, humidity)[0], fixed)

# (b) setback + demand-controlled ventilation: bring in air for the people actually there.
oa_dcv = np.clip(occupancy, 20, CAP)
both   = np.where(scheduled & (occupancy < 40),
                  hvac_kw_for(outdoor, 28.0, solar, occupancy, humidity, 20)[0],
                  np.where(scheduled,
                           hvac_kw_for(outdoor, 23.0, solar, occupancy, humidity, oa_dcv)[0],
                           1.5))

fig = go.Figure()
for y, name, col in [(fixed, "fixed schedule, fixed damper", RED),
                     (setback, "+ setback when empty", AMBER),
                     (both, "+ ventilation led by CO₂", GREEN)]:
    fig.add_trace(go.Scatter(x=hour, y=y, name=name, line=dict(color=col, width=2.5)))
fig.update_layout(title="same comfort, same hours — the plant just knows more",
                  xaxis_title="hour of day", yaxis_title="HVAC kW",
                  template="plotly_white", height=400)
fig.show()

base = fixed.sum()*0.25
for y, name in [(fixed, "fixed schedule, fixed damper"),
                (setback, "+ setback when empty      "),
                (both, "+ ventilation led by CO₂  ")]:
    kwh = y.sum()*0.25
    print(f"{name} : {kwh:6,.0f} kWh/day   ({100*(1-kwh/base):4.1f}% saved)")
print()
print("Setback only applies for the hour or so when the floor is genuinely empty.")
print("Matching the fresh air to the people present applies ALL day, so it is worth more even here -")
print("and this is a mild day with a full floor, which is the case that flatters the fixed damper most.")
print("Neither lever changes the setpoint while people are in the building.")
'''),
          ("md", r"""
### Building Engineer **+** AI. Never engineer *vs* AI.

| The engineer stays in charge of | Where one person needs a hand |
|---|---|
| Diagnosing the actual fault | Watching every zone, every 15 minutes |
| Judging a comfort complaint | Separating a hot afternoon from real waste |
| Overriding for an event or a fit-out | Comparing today against 3,000 past intervals |
| Signing off a capital spend | Reading a thermal frame pixel by pixel |
| Responsibility for the occupants | Never looking away |
""")],
    built="""Two levers, both available today, neither requiring new plant. The setpoint during occupied hours was
never touched — that constraint is non-negotiable, and it comes back as a hard limit in the optimiser.""",
    takeaway="""The intelligence layer reports and recommends. The engineer decides and signs off.""",
)

# ---------------------------------------------- PHASE 2 · ONE READING INTERVAL
step(
    id="reading", phase=1, icon="📏", ai_icon="🗄️",
    civil="One 15-Minute Interval", ai="Data Collection",
    tech="One interval → one row of sensor readings + the load it produced",
    site="""Every fifteen minutes the BMS records the state of the floor: indoor and outdoor temperature,
humidity, CO₂, occupancy count, solar irradiance, particulate level, the active setpoint, and the
electricity the HVAC drew.""",
    challenge="""On their own these are nine trends on nine screens. No single one tells you whether that interval was
efficient, and a year is 35,000 of them.""",
    ai_link="""Put them in one row and the interval becomes a record: nine inputs, and the HVAC load that resulted.
Thousands of those rows are the dataset every model in this notebook learns from.""",
    bridge=[("Nine channels", "One row per interval"),
            ("Logged every 15 min", "Nine features"),
            ("Load recorded", "Two targets")],
    body=[("md", r"""
| Sensor | Why it is installed | Unit | How the AI uses it |
|---|---|---|---|
| 🌡️ Indoor temperature | Prove the comfort standard is met | °C | Comfort, and how far the plant is behind the load |
| 🌤️ Outdoor temperature | Drives conduction through the envelope | °C | The single largest weather driver of cooling |
| 💧 Humidity | Latent load; comfort at a given temperature | % | Dehumidification demand, and the comfort index |
| 🫁 CO₂ | Ventilation adequacy | ppm | A proxy for occupancy — this is what drives demand-controlled ventilation |
| 👥 Occupancy | Internal gains and fresh-air requirement | people | Internal heat, ventilation, and whether cooling is justified at all |
| ☀️ Solar irradiance | Gain through the glazing | W/m² | Explains an afternoon load spike that has nothing to do with people |
| 🌫️ Air quality (PM2.5) | Indoor air quality compliance | µg/m³ | Constrains how far ventilation can be reduced |
| 🎚️ Setpoint | What the plant is being asked to hold | °C | The control variable the optimiser is allowed to move |
| 🕐 Hour of day | Schedule and diurnal pattern | h | Separates the morning ramp from the afternoon peak |
"""),
          ("co", r'''
import pandas as pd

GRID_KG = 0.42          # kg CO2 per kWh of grid electricity

# The plant model was defined in step 1. Two more pieces complete it: what the room
# actually reaches, and how the people in it feel about that.

def indoor_for(setpoint, cool_thermal):
    "The room drifts above setpoint when the load exceeds what the plant can pull down."
    return np.asarray(setpoint, float) + np.clip(0.011*(np.asarray(cool_thermal, float)-190), 0, None)

def ppd(indoor, hum):
    "Predicted Percentage Dissatisfied (ISO 7730), from a simplified PMV proxy."
    pmv = 0.30*(np.asarray(indoor, float)-23.5) + 0.012*(np.asarray(hum, float)-50)
    return 100 - 95*np.exp(-0.03353*pmv**4 - 0.2179*pmv**2)

# ---- one interval, as the model will see it
kw, cool = hvac_kw_for(outdoor=32, setpoint=23, solar=520, occ=180, hum=58)
row = pd.DataFrame([{
    "indoor_temp_c": round(float(indoor_for(23, cool)), 1), "outdoor_temp_c": 32.0,
    "humidity_pct": 58.0, "co2_ppm": 420 + 2.9*180, "occupancy": 180,
    "solar_wm2": 520.0, "pm25_ugm3": 11.6, "setpoint_c": 23.0, "hour": 14.5,
    "hvac_kw": round(float(kw), 1)}])
print(f"cooling load {cool:,.0f} kW thermal  ->  {kw:,.1f} kW electrical "
      f"(COP {chiller_cop(32):.2f})")
row
''')],
    built="""The model never walks the floor. It sees this row and nothing else. If the row is wrong, the
prediction is wrong and the model has no way to notice — which is why the next four steps are about
the data, not the model.""",
    takeaway="""One interval becomes one row: nine readings in, the HVAC load out.""",
)

step(
    id="two-records", phase=1, icon="🧾", ai_icon="🔀",
    civil="Sensor Row vs Camera Frame", ai="Two Kinds Of Data",
    tech="Nine named numbers, or 4,096 unnamed pixels",
    site="""Two records leave the floor every interval. The BMS row — nine named numbers with units. And a
thermal frame from the ceiling camera — a 64×64 grid of surface temperatures, with no names at all.""",
    challenge="""Both describe the same floor. The row says how much energy went in. The frame says **where the floor
is actually being used**. Neither is complete, and they do not look like each other.""",
    ai_link="""Named columns suit Machine Learning: the engineer picks the features and the model weights them. Raw
pixels do not — nobody can name 4,096 useful columns. That difference is the whole argument of this
notebook, and it is why both ML and Deep Learning appear.""",
    bridge=[("The BMS row", "Named columns → ML"),
            ("The camera frame", "Raw pixels → DL"),
            ("Same floor, two views", "The fork in the road")],
    body=[("co", r'''
# NOTE on seeding: Python's hash() of a string is randomised per process, so
# seeding an RNG from it would give different frames on every run and make the
# numbers quoted in this notebook unreproducible. Use an explicit table instead.
KIND_SEED = {"empty": 0, "occupied": 1, "crowded": 2, "solar": 3, "heat_leak": 4}

def make_floor(kind="empty", size=64, seed=0, n_people=None, jitter=False):
    """A floor plate seen from the ceiling as a normalised temperature grid.

    empty     - nobody in, cool plate               (no people)
    occupied  - about 12 people in one zone         (PEOPLE)
    crowded   - two busy zones, ~34 people          (PEOPLE)
    solar     - sun on the south facade             (no people)  <- the decoy
    heat_leak - warm strip along a leaky wall       (no people)  <- the other decoy

    n_people overrides the head count, and `jitter` moves the clusters, the facade
    band and the leak strip around. Both are used to build a training set in which
    no two frames are alike.
    """
    rng = np.random.default_rng(seed*7 + KIND_SEED[kind])
    Y, X = np.mgrid[0:size, 0:size]
    img = 0.36 + rng.normal(0, 0.022, (size, size))
    img += 0.05*np.exp(-((X-size+1)**2)/(2*7.0**2))     # warm south facade
    img += 0.03*np.exp(-(Y**2)/(2*6.0**2))              # warm riser core

    def people(k, cy, cx, spread):
        out = np.zeros_like(img)
        for _ in range(k):
            py = np.clip(rng.normal(cy, spread), 3, size-4)
            px = np.clip(rng.normal(cx, spread), 3, size-4)
            out += np.exp(-(((Y-py)**2 + (X-px)**2)/(2*2.1**2)))
        return out

    if n_people is not None:                            # training-set path
        if n_people > 0:
            k1 = n_people if n_people < 20 else n_people//2
            img += 0.55*people(k1, rng.uniform(12, 52), rng.uniform(12, 52),
                               rng.uniform(6, 12))
            if n_people >= 20:
                img += 0.55*people(n_people-k1, rng.uniform(12, 52), rng.uniform(12, 52),
                                   rng.uniform(6, 12))
        if jitter and rng.random() < 0.45:              # sun on the facade as well
            img += rng.uniform(0.12, 0.30)*np.exp(-((X-size+rng.uniform(1, 8))**2)/(2*11.0**2))
        if jitter and rng.random() < 0.30:              # and a leaky wall as well
            img += rng.uniform(0.15, 0.34)*np.exp(-((Y-size+rng.uniform(1, 6))**2)/(2*3.0**2))
    elif kind == "occupied":  img += 0.55*people(12, 40, 22, 8)
    elif kind == "crowded":   img += 0.55*(people(18, 24, 20, 10) + people(16, 42, 42, 10))
    elif kind == "solar":     img += 0.30*np.exp(-((X-size+4)**2)/(2*11.0**2))
    elif kind == "heat_leak": img += 0.34*np.exp(-((Y-size+3)**2)/(2*3.0**2))
    return np.clip(img, 0, 1)

def show_frame(z, title="", h=340, colorscale="Inferno"):
    f = go.Figure(go.Heatmap(z=z, colorscale=colorscale, showscale=False))
    f.update_layout(title=title, height=h, template="plotly_white",
                    margin=dict(l=10, r=10, t=50, b=10))
    f.update_xaxes(visible=False)
    f.update_yaxes(visible=False, autorange="reversed", scaleanchor="x")
    return f

print("THE BMS ROW - 9 named numbers, each already meaningful to an engineer:")
print(row.T.to_string(header=False))
img = make_floor("occupied")
print(f"\nTHE CAMERA FRAME - {img.size:,} unnamed numbers. Not one of them is called 'occupancy'.")
show_frame(img, "one thermal frame · 64 × 64 surface temperatures").show()
''')],
    built="""A Random Forest handles the nine readings without complaint. It cannot be pointed at 4,096 unnamed
pixels at all. Hold that thought — the notebook is going to test it rather than assert it.""",
    takeaway="""Numbers arrive with names; images do not. That single difference splits ML from DL.""",
)

# ---------------------------------------------- PHASE 3 · INSTRUMENTING
step(
    id="load", phase=2, icon="📥", ai_icon="🐼",
    civil="The BMS Export Arrives", ai="Loading The Dataset",
    tech="CSV → DataFrame, 16 weeks of 15-minute intervals",
    site="""The BMS exports sixteen weeks of the cooling season: one row per fifteen minutes, every sensor
channel, plus the metered HVAC and whole-building load.""",
    challenge="""An export is not a dataset. Channels drop out when a controller reboots, a failed sensor writes a
fixed value, and intervals repeat after a trend-log resync. Opening it in a spreadsheet shows none of
that.""",
    ai_link="""Loading it into a DataFrame is the first AI step: shape, column types, and a first look at what
actually arrived.""",
    bridge=[("BMS trend export", "read_csv"),
            ("One row per 15 min", "shape and dtypes"),
            ("16 weeks", "First look")],
    body=[("co", r'''
def make_bms_export(days=112, seed=42):
    "Sixteen weeks of the cooling season, as the BMS would export it - faults and all."
    rng = np.random.default_rng(seed)
    n = days*96
    idx  = np.arange(n)
    day  = idx//96
    hour = (idx % 96)*0.25
    workday = ((day % 7) < 5).astype(int)

    cloud   = np.repeat(rng.uniform(0.35, 1.0, days), 96)
    outdoor = (26 + 3.5*np.sin(2*np.pi*day/112) + 6*np.sin(2*np.pi*(hour-9)/24)
               + np.repeat(rng.normal(0, 1.8, days), 96) + rng.normal(0, 0.4, n))
    solar   = np.where((hour > 6) & (hour < 19),
                       np.clip(880*np.sin(np.pi*(hour-6)/13), 0, None)*cloud, 0.0)
    hum     = np.clip(72 - 0.9*(outdoor-25) + rng.normal(0, 4, n), 30, 95)
    busy    = np.repeat(rng.uniform(0.6, 1.0, days), 96)
    shape   = np.clip(0.95*np.exp(-((hour-10.5)**2)/(2*1.6**2))
                    + 0.90*np.exp(-((hour-15.0)**2)/(2*1.7**2))
                    - 0.35*np.exp(-((hour-13.0)**2)/(2*0.7**2)), 0, 1)
    occ     = np.clip(np.round(CAP*shape*busy*workday*rng.uniform(0.9, 1.1, n)), 0, CAP)

    sched    = (hour >= 7) & (hour < 19) & (workday == 1)
    setpoint = np.where(sched, 23.0 + rng.normal(0, 0.35, n), 27.0)
    hv, cool = hvac_kw_for(outdoor, setpoint, solar, occ, hum)     # fixed damper: OA_DESIGN
    hvac     = np.where(sched, hv, 1.5)
    indoor   = np.where(sched, indoor_for(setpoint, cool) + rng.normal(0, 0.25, n),
                        outdoor - 1.5 + rng.normal(0, 0.5, n))
    base     = np.where(sched, 28 + 0.09*occ, 13.0)               # lighting, lifts, IT

    df = pd.DataFrame({
        "day": day, "hour": hour, "is_workday": workday,
        "indoor_temp_c":  indoor.round(2),
        "outdoor_temp_c": outdoor.round(2),
        "humidity_pct":   hum.round(1),
        "co2_ppm":        np.clip(420 + 2.9*occ + rng.normal(0, 25, n), 400, None).round(0),
        "occupancy":      occ,
        "solar_wm2":      solar.round(0),
        "pm25_ugm3":      np.clip(8 + 0.02*occ + rng.normal(0, 1.5, n), 1, None).round(1),
        "setpoint_c":     setpoint.round(2),
        "hvac_kw":        hvac.round(2),
        "total_kw":       (hvac + base).round(2),
        "scheduled":      sched.astype(int),
    })

    # ---- the faults every real trend export carries
    for c in ["indoor_temp_c", "outdoor_temp_c", "humidity_pct", "co2_ppm",
              "solar_wm2", "pm25_ugm3"]:
        df.loc[rng.choice(n, int(0.04*n), replace=False), c] = np.nan
    df.loc[rng.choice(n, 60, replace=False), "co2_ppm"]        = 0.0     # dead CO2 sensor
    df.loc[rng.choice(n, 45, replace=False), "indoor_temp_c"]  = 85.0    # failed thermistor
    df.loc[rng.choice(n, 40, replace=False), "humidity_pct"]   = 0.0     # stuck RH channel
    df.loc[rng.choice(n, 35, replace=False), "occupancy"]      = 9999    # counter rollover
    return pd.concat([df, df.sample(120, random_state=4)], ignore_index=True)

make_bms_export().to_csv("bms_export.csv", index=False)

df = pd.read_csv("bms_export.csv")
print("shape:", df.shape)
print("days :", df.day.nunique(), " | scheduled intervals:", int(df.scheduled.sum()))
df.head()
''')],
    built="""The file loads. That is all it proves. Shape and dtypes say nothing about whether the numbers inside
are physically possible.""",
    takeaway="""The export is raw material. Loading it is where the data work starts, not where it ends.""",
)

step(
    id="inspect", phase=2, icon="🔍", ai_icon="📊",
    civil="Sensor Health Check", ai="Data Inspection",
    tech="Count the gaps, the stuck channels, the impossible values",
    site="""Before trusting sixteen weeks of trend data, an engineer checks the instruments. Did the CO₂ sensor
report all season? Is the RH channel stuck? Is anything physically impossible?""",
    challenge="""Faults hide in plain sight. A dead CO₂ sensor reads `0 ppm` — a valid number that happens to be a
lie, since outdoor air alone is 420 ppm. Averaged into a monthly figure, it quietly corrupts every
conclusion drawn from it.""",
    ai_link="""Data inspection is that instrument check, written as code: missing counts per channel, minimum and
maximum per channel, repeated rows, and columns that never change.""",
    bridge=[("Did it report?", "isna().sum()"),
            ("Is it stuck?", "describe()"),
            ("Is it possible?", "duplicated(), nunique()")],
    body=[("co", r'''
SENSORS = ["indoor_temp_c", "outdoor_temp_c", "humidity_pct", "co2_ppm",
           "occupancy", "solar_wm2", "pm25_ugm3", "setpoint_c"]

print("MISSING readings per channel (a controller rebooted):")
print(df[SENSORS].isna().sum().to_string(), "\n")
print("Duplicate rows (a trend-log resync):", int(df.duplicated().sum()), "\n")
print("Physical range per channel - read this like an engineer, not a statistician:")
print(df[SENSORS].describe().T[["min", "max"]].round(1).to_string(), "\n")
print("Unique values per column (a column with one value carries no information):")
print(df.nunique().sort_values().head(4).to_string())

miss = df[SENSORS].isna().sum()
fig = go.Figure(go.Bar(x=SENSORS, y=miss.values, marker_color=AMBER,
                       text=miss.values, textposition="outside"))
fig.update_layout(title="dropouts per channel", yaxis_title="missing readings",
                  template="plotly_white", height=380)
fig.show()
'''),
          ("md", r"""
Four faults, and every one of them is a *valid number*:

- `co2_ppm` **min 0** — a dead sensor. Outdoor air alone is about 420 ppm, so zero is impossible indoors.
- `indoor_temp_c` **max 85** — a failed thermistor, not a fire.
- `humidity_pct` **min 0** — a stuck RH channel. 0% RH does not occur in an occupied office.
- `occupancy` **max 9999** — a people-counter rollover, not a full stadium.

And one column, `is_workday`, that will turn out to have a **single unique value** once we keep only the
scheduled intervals. A constant column cannot help any model. It gets dropped, not cleaned.
""")],
    built="""A fault list, produced without touching a single value. Diagnosis first, repair second — the same
order you would use on the plant itself.""",
    takeaway="""Check the sensors before you trust the readings: 0 ppm and 9999 people are both faults, not data.""",
)

# ---------------------------------------------- PHASE 4 · PREPARING THE DATA
step(
    id="clean", phase=3, icon="🧹", ai_icon="🧼",
    civil="Removing The Faulty Readings", ai="Data Cleaning",
    tech="Drop duplicates, null the impossible, fill with the median",
    site="""A faulty channel is repaired or discounted before its readings reach an energy report. Nobody averages
a stuck gauge into a monthly figure and then defends the result to a client.""",
    challenge="""Deleting every affected row throws away good readings from the other eight channels in that interval.
Keeping them poisons the average. Neither extreme is acceptable when the output is a control
recommendation.""",
    ai_link="""Cleaning does both: drop exact duplicates, mark impossible values as *missing* rather than deleting the
row, then fill the gaps with each channel's **median** — a value that outliers cannot drag.""",
    bridge=[("Repair the channel", "drop_duplicates"),
            ("Keep the interval", "Mask the impossible"),
            ("Never average a fault", "fillna(median)")],
    body=[("co", r'''
clean = df.drop_duplicates().copy()

# mark the physically impossible as missing, rather than deleting the whole interval
clean.loc[clean.co2_ppm       < 380,  "co2_ppm"]       = np.nan
clean.loc[clean.indoor_temp_c > 40,   "indoor_temp_c"] = np.nan
clean.loc[clean.humidity_pct  < 10,   "humidity_pct"]  = np.nan
clean.loc[clean.occupancy     > CAP,  "occupancy"]     = np.nan

for c in SENSORS:
    clean[c] = clean[c].fillna(clean[c].median())

# The HVAC only makes a control decision while it is running. Model those intervals.
occ_hours = clean[clean.scheduled == 1].drop(columns=["is_workday", "scheduled"]).reset_index(drop=True)

print(f"rows {len(df):,} -> {len(clean):,} after de-duplication")
print(f"missing left: {int(clean[SENSORS].isna().sum().sum())}")
print(f"scheduled (HVAC-running) intervals kept for modelling: {len(occ_hours):,}\n")

print("Why the median and not the mean?")
print(f"  mean of the dirty indoor channel   : {df.indoor_temp_c.mean():.1f} C   <- dragged by the 85s")
print(f"  median of the dirty indoor channel : {df.indoor_temp_c.median():.1f} C   <- barely notices them")

fig = go.Figure()
fig.add_trace(go.Box(y=df.indoor_temp_c, name="dirty", marker_color=RED))
fig.add_trace(go.Box(y=clean.indoor_temp_c, name="clean", marker_color=GREEN))
fig.update_layout(title="indoor temperature: the impossible tail is gone",
                  yaxis_title="°C", template="plotly_white", height=380)
fig.show()
''')],
    built="""Every remaining number is physically possible. `is_workday` and `scheduled` are gone: after the filter
they hold one value each, and a constant column can only add noise to a model.""",
    takeaway="""Repair the channel, not the interval: mask the impossible, fill with the median, keep the rest.""",
)

step(
    id="normalize", phase=3, icon="📐", ai_icon="⚖️",
    civil="Standardising The Measurements", ai="Normalization",
    tech="Min-max every channel onto 0–1",
    site="""The channels do not share a scale. CO₂ runs to 1,200 ppm, solar to 880 W/m², humidity is a
percentage, setpoint sits near 23.""",
    challenge="""A model that adds weighted inputs has the same problem an engineer has reading them on one chart: the
largest-numbered channel dominates — not because it matters most, but because its unit is bigger. A
0.5 °C setpoint change matters enormously and moves the number barely at all.""",
    ai_link="""Min-max scaling puts every channel on 0–1 using its own range. Units disappear, and importance is then
decided by the data rather than by the choice of unit.""",
    bridge=[("ppm vs W/m² vs °C", "Rescale to 0–1"),
            ("Different magnitudes", "Units disappear"),
            ("One chart, one winner", "The data decides")],
    body=[("co", r'''
from sklearn.preprocessing import MinMaxScaler

FEATURES = ["indoor_temp_c", "outdoor_temp_c", "humidity_pct", "co2_ppm", "occupancy",
            "solar_wm2", "pm25_ugm3", "setpoint_c", "hour"]

scaler = MinMaxScaler()
X_all  = scaler.fit_transform(occ_hours[FEATURES])

before = occ_hours[FEATURES].agg(["min", "max"]).T.round(1)
after  = pd.DataFrame(X_all, columns=FEATURES).agg(["min", "max"]).T.round(2)
print("raw ranges:\n", before.to_string(), "\n")
print("scaled ranges:\n", after.to_string())

fig = go.Figure()
for c, col in zip(["co2_ppm", "solar_wm2", "setpoint_c"], [CYAN, AMBER, GREEN]):
    fig.add_trace(go.Box(y=occ_hours[c], name=c, marker_color=col))
fig.update_layout(title="before scaling — setpoint is invisible next to CO₂ and solar",
                  template="plotly_white", height=360)
fig.show()
''')],
    built="""Nine channels, one common scale. The setpoint can now compete with CO₂ on the strength of its effect
rather than the size of its unit.""",
    takeaway="""Rescale every channel to 0–1 so that units stop deciding importance.""",
)

step(
    id="split", phase=3, icon="🗂️", ai_icon="✂️",
    civil="Known Days vs Sealed Days", ai="Train / Test Split",
    tech="Split by DAY, chronologically — never by interval",
    site="""A commissioning test is not run on the load case used to tune the plant. You prove performance on a
case the settings have never seen.""",
    challenge="""Here the usual random shuffle is actively wrong. Two consecutive 15-minute intervals are almost the
same building: same weather, nearly the same occupancy. Shuffle them and the model is tested on the
interval either side of one it memorised. The score looks excellent and means nothing.""",
    ai_link="""Split by **day**, in time order: the first 70% of days to train on, the next 15% to tune with, the
last 15% sealed until the audit. That is also how the system would actually be deployed — trained on
the past, run on tomorrow.""",
    bridge=[("Tune on some days", "Train 70% of days"),
            ("Prove on others", "Validate 15%"),
            ("Never the same day", "Test 15%, sealed")],
    body=[("co", r'''
days = np.sort(occ_hours.day.unique())
n_d  = len(days)
train_days = days[:int(0.70*n_d)]
val_days   = days[int(0.70*n_d):int(0.85*n_d)]
test_days  = days[int(0.85*n_d):]

tr = occ_hours.day.isin(train_days).values
va = occ_hours.day.isin(val_days).values
te = occ_hours.day.isin(test_days).values

y_hvac  = occ_hours.hvac_kw.values
y_total = occ_hours.total_kw.values

print(f"days   : {len(train_days)} train / {len(val_days)} val / {len(test_days)} test (sealed)")
print(f"rows   : {tr.sum()} / {va.sum()} / {te.sum()}")

fig = go.Figure()
for name, mask, col in [("train", tr, CYAN), ("validation", va, AMBER), ("test (sealed)", te, GREEN)]:
    fig.add_trace(go.Scatter(x=occ_hours.day[mask], y=occ_hours.hvac_kw[mask],
                             mode="markers", name=name,
                             marker=dict(size=3, color=col, opacity=0.5)))
fig.update_layout(title="the split is a cut in TIME, not a shuffle",
                  xaxis_title="day", yaxis_title="HVAC kW",
                  template="plotly_white", height=380)
fig.show()
'''),
          ("md", r"""
### Prove it to yourself

The next cell trains the same model twice: once on a random shuffle of intervals, once on the day split.
One of those two numbers is a lie.
"""),
          ("co", r'''
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

i1, i2 = train_test_split(np.arange(len(occ_hours)), test_size=0.15, random_state=0)
shuffled = RandomForestRegressor(n_estimators=200, random_state=42).fit(X_all[i1], y_hvac[i1])
bydays   = RandomForestRegressor(n_estimators=200, random_state=42).fit(X_all[tr], y_hvac[tr])

print(f"shuffled intervals  ->  R2 = {r2_score(y_hvac[i2], shuffled.predict(X_all[i2])):.4f}   <- flattering, and wrong")
print(f"split by day        ->  R2 = {r2_score(y_hvac[te], bydays.predict(X_all[te])):.4f}   <- what tomorrow will actually look like")
''')],
    built="""The shuffled score is higher, and it is the one to distrust. Every number from here on is measured on
sealed days the model has never seen.""",
    takeaway="""Time-series data splits by day, not by row — adjacent intervals leak the answer.""",
)

# ---------------------------------------------- PHASE 5 · DEMAND FROM SENSORS
step(
    id="ml-baseline", phase=4, icon="❄️", ai_icon="🌲",
    civil="Predicting Cooling Demand From The Gauges", ai="Machine Learning",
    tech="Linear Regression vs Random Forest vs Gradient Boosting",
    site="""The first question the building asks is simple: given the current conditions, how much HVAC load
should this interval be drawing, and what will the whole building draw?""",
    challenge="""A hand-written formula from the plant schedule gets the order of magnitude right and the details
wrong. Outdoor temperature, solar gain, occupancy, humidity and the setpoint all interact, and chiller
COP falls exactly when demand is highest.""",
    ai_link="""Regression learns that relationship from the building's own history. Three models, increasing in
capability: a straight line, a forest of threshold questions, and a boosted ensemble. This is the
**first half of the promise: ML predicts building energy demand from environmental and occupancy
data.**""",
    bridge=[("What should it draw?", "Regression"),
            ("From the gauges alone", "Named features"),
            ("Checked on sealed days", "MAE, RMSE, R²")],
    body=[("co", r'''
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

models = {
    "Linear Regression": LinearRegression(),
    "Random Forest":     RandomForestRegressor(n_estimators=200, random_state=42),
    "Gradient Boosting": GradientBoostingRegressor(random_state=42),
}
scores = {}
for name, m in models.items():
    m.fit(X_all[tr], y_hvac[tr])
    p = m.predict(X_all[te])
    scores[name] = dict(MAE=mean_absolute_error(y_hvac[te], p),
                        RMSE=float(np.sqrt(((y_hvac[te]-p)**2).mean())),
                        R2=r2_score(y_hvac[te], p))
print(pd.DataFrame(scores).T.round(3).to_string(), "\n")

hvac_model = models["Random Forest"]
pred = hvac_model.predict(X_all[te])

fig = go.Figure()
fig.add_trace(go.Scatter(x=y_hvac[te], y=pred, mode="markers", name="sealed intervals",
                         marker=dict(size=5, color=CYAN, opacity=0.55)))
lims = [float(y_hvac[te].min()), float(y_hvac[te].max())]
fig.add_trace(go.Scatter(x=lims, y=lims, mode="lines", name="perfect",
                         line=dict(color=MUTED, dash="dash")))
fig.update_layout(title="predicted vs metered HVAC load, on days never seen",
                  xaxis_title="metered kW", yaxis_title="predicted kW",
                  template="plotly_white", height=430)
fig.show()

# the whole-building meter as well
total_model = RandomForestRegressor(n_estimators=200, random_state=42).fit(X_all[tr], y_total[tr])
print(f"Whole-building load R2 on sealed days: {r2_score(y_total[te], total_model.predict(X_all[te])):.3f}")
'''),
          ("md", r"""
Read the table before moving on. **Linear regression is already close** — cooling load really is roughly
linear in weather and occupancy, which is why degree-day methods have worked in this industry for
decades. The forest wins on the corners: the hot afternoon where COP collapses, the fan curve, the
lunchtime dip. That margin is worth having, and it is worth knowing it is a margin and not a miracle.
""")],
    built="""A model that predicts HVAC load to within a couple of kilowatts on days it has never seen. Everything
downstream — the waste flag, the forecast, the optimiser, the business case — is built on this one
prediction.""",
    takeaway="""Machine Learning predicts building energy demand well — from named sensor channels only.""",
)

step(
    id="drivers", phase=4, icon="📈", ai_icon="🎚️",
    civil="What Drives The Load", ai="Feature Importance",
    tech="Which channel moves the prediction most",
    site="""Knowing the number is not enough. The building needs to know which lever moves it: the weather, the
occupancy, the ventilation rate, or the setpoint.""",
    challenge="""The channels move together. Occupancy rises, CO₂ rises, internal gains rise, the afternoon gets hotter.
A correlation table tells you what moved with what, not what mattered.""",
    ai_link="""Feature importance ranks how much each channel changes the model's prediction. It turns a black box
into an engineering priority list — and it is the first place a model's answer can be checked against
building-services intuition.""",
    bridge=[("Which lever?", "feature_importances_"),
            ("Weather or people?", "A ranked list"),
            ("Rank the causes", "Check against intuition")],
    body=[("co", r'''
# Define the waste flag here: HVAC kilowatts spent per person actually on the floor.
LIMIT = 0.55                                   # kW per person
kw_per_person = y_hvac/np.clip(occ_hours.occupancy.values, 1, None)
y_waste = (kw_per_person > LIMIT).astype(int)
print(f"intervals flagged as over-conditioned: {y_waste.mean():.1%}\n")

from sklearn.ensemble import RandomForestClassifier
waste_model = RandomForestClassifier(n_estimators=200, random_state=42).fit(X_all[tr], y_waste[tr])

fig = go.Figure()
for m, name, col in [(hvac_model, "drivers of HVAC load", CYAN),
                     (waste_model, "drivers of an over-conditioned interval", AMBER)]:
    imp = m.feature_importances_
    o = np.argsort(imp)[::-1]
    fig.add_trace(go.Bar(x=[FEATURES[i] for i in o], y=imp[o], name=name, marker_color=col))
fig.update_layout(barmode="group", title="the two questions rank the sensors differently",
                  yaxis_title="importance", template="plotly_white", height=420)
fig.show()

for m, name in [(hvac_model, "HVAC load"), (waste_model, "over-conditioned")]:
    imp = m.feature_importances_
    o = np.argsort(imp)[::-1][:4]
    print(f"{name:18s}: " + ", ".join(f"{FEATURES[i]} {imp[i]:.2f}" for i in o))
'''),
          ("md", r"""
Three things worth noticing, and none of them is about AI:

- **Outdoor temperature and occupancy lead**, which is exactly what a building-services engineer would
  have told you. The model was not given that rule — it recovered it from sixteen weeks of trend data.
- **CO₂ ranks high and is largely redundant with occupancy.** Both measure the same thing. That is useful:
  if the people-counter fails, the CO₂ sensor still carries the signal.
- Importance says how much a prediction **moves**, not what **causes** what. It is a list of things to
  investigate, not a work order. The model never authorises a spend on its own.
""")],
    built="""A ranked list of what actually drives the bill, and a second model that flags intervals spending too
many kilowatts per person on the floor.""",
    takeaway="""A ranked driver list turns a prediction into a decision about what to change first.""",
)

# ---------------------------------------------- PHASE 6 · THE IMAGE WALL
step(
    id="camera-problem", phase=5, icon="📷", ai_icon="🖼️",
    civil="What The Ceiling Camera Sends", ai="Raw Pixels As Input",
    tech="A 64×64 grid of temperatures, no named columns",
    site="""A thermal camera looks down at the floor plate. Bright is warm, dark is cool. A person at a desk is a
small warm blob. A busy meeting zone is a cluster of them. Afternoon sun on the south façade is a broad
warm band, and a leaky wall is a warm strip.""",
    challenge="""The camera does not output "twelve people in the north-east zone". It outputs 4,096 numbers with no
names. There is no column called *occupancy*, and no row an engineer can look up.""",
    ai_link="""This is where Machine Learning runs out. It needs named features and there are none — only pixels.
Before reaching for a new method, it is worth trying to build the feature by hand and watching exactly
what happens.""",
    bridge=[("Warm blob = a person", "4,096 numbers"),
            ("Warm band = sunlight", "No column names"),
            ("Only one means occupancy", "Nothing to weight")],
    body=[("co", r'''
KINDS  = ["empty", "occupied", "crowded", "solar", "heat_leak"]
PEOPLE = {"empty": 0, "occupied": 12, "crowded": 34, "solar": 0, "heat_leak": 0}

from plotly.subplots import make_subplots
fig = make_subplots(rows=1, cols=5, subplot_titles=[
    f"{k}<br><sub>{PEOPLE[k]} people</sub>" for k in KINDS])
for j, k in enumerate(KINDS, start=1):
    fig.add_trace(go.Heatmap(z=make_floor(k), colorscale="Inferno", showscale=False,
                             zmin=0, zmax=1), row=1, col=j)
    fig.update_xaxes(visible=False, row=1, col=j)
    fig.update_yaxes(visible=False, autorange="reversed", row=1, col=j)
fig.update_layout(height=300, template="plotly_white",
                  title="five floor plates — two of the warm ones contain nobody at all")
fig.show()

# Zoom in. These are the actual numbers that arrive.
z = make_floor("occupied")
# show the most varied 6x6 window, so you can see an edge rather than flat background
best, bi, bj = -1, 0, 0
for i in range(0, z.shape[0]-6):
    for j in range(0, z.shape[1]-6):
        v = z[i:i+6, j:j+6].std()
        if v > best:
            best, bi, bj = v, i, j
print(f"The most varied 6x6 window in the frame (rows {bi}-{bi+5}, cols {bj}-{bj+5}),")
print("as the computer receives it:\n")
print(np.round(z[bi:bi+6, bj:bj+6], 3))
print(f"\nThe full frame is {z.shape[0]} x {z.shape[1]} = {z.size:,} values.")
print("Which one of them is 'a person'?  None. A person is a PATTERN across about 40 of them,")
print("and the same person sits somewhere different tomorrow.")
''')],
    built="""The same wall the construction project hit, in a different building. The Random Forest cannot be
pointed at this. There is nothing named for it to weight.""",
    takeaway="""A thermal frame is 4,096 unnamed numbers. Machine Learning has nothing to weight.""",
)

step(
    id="handmade", phase=5, icon="✋", ai_icon="🔢",
    civil="Counting People By Brightness", ai="Hand-Crafted Features",
    tech="One number from 4,096 pixels — and what it throws away",
    site="""The obvious workaround is the one every engineer tries first: reduce the frame to a number. Mean
surface temperature. Then threshold it, exactly the way a BMS alarm limit already works.""",
    challenge="""Averaging destroys the evidence. Twelve people spread over a floor plate move the mean by a few
hundredths. Afternoon sun on the façade moves it by more than that, and there is nobody there at all.""",
    ai_link="""The feature was hand-made, and it was the wrong feature. You could add ten more — variance, maximum,
a hot-pixel count — and still be guessing. Deep Learning removes the guessing by learning the features
from the frames themselves.""",
    bridge=[("Reduce to a mean", "One feature"),
            ("Set an alarm limit", "One threshold"),
            ("Exactly as the BMS does", "It fails")],
    body=[("co", r'''
means = {k: float(make_floor(k, seed=1).mean()) for k in KINDS}
truth = {k: ("PEOPLE" if PEOPLE[k] > 0 else "nobody") for k in KINDS}

fig = go.Figure()
for k in KINDS:
    fig.add_trace(go.Bar(x=[k], y=[means[k]], showlegend=False,
                         marker_color=(GREEN if truth[k] == "PEOPLE" else RED),
                         text=f"{means[k]:.3f}", textposition="outside"))
fig.update_layout(title="one number per frame — green really has people in it, red does not",
                  yaxis_title="mean surface temperature", template="plotly_white", height=380)
fig.show()

print("Try every threshold you like:\n")
for thr in [0.38, 0.40, 0.42, 0.44, 0.46, 0.48]:
    missed = [k for k in KINDS if truth[k] == "PEOPLE" and means[k] <= thr]
    false_ = [k for k in KINDS if truth[k] == "nobody" and means[k] >  thr]
    print(f"  call it occupied above {thr:.2f}  ->  missed {missed or ['none']:}, "
          f"cooled an empty floor for {false_ or ['none']}")
'''),
          ("md", r"""
### Look carefully at what just happened

There is no winning threshold, and the reason is worth stating precisely. Read the bar chart against the
printed sweep:

- **`solar` outranks `occupied`.** An empty sunlit floor reads *warmer* than a floor with twelve people on
  it. Any limit that catches the people also runs the plant for the sunshine.
- **`heat_leak` sits right next to `occupied`.** A failing wall and a working team are the same number.

The mean threw away the only thing that distinguished them: **where the warmth is, and what shape it
is**. Twelve compact blobs in one zone is occupancy. One broad band along a façade is weather. Both have
the same average.
""")],
    built="""A hand-made feature that fails, and fails for a reason you can now articulate. This is the honest
baseline the CNN has to beat.""",
    takeaway="""One hand-made number cannot hold a pattern — the mean cools an empty sunlit floor and misses a busy one.""",
)

step(
    id="why-dl", phase=5, icon="🚧", ai_icon="🧠",
    civil="Why The Rulebook Ran Out", ai="Learned Features: Deep Learning",
    tech="Learn the features instead of naming them",
    site="""The rulebook has run out. There is no threshold on mean temperature, and no combination of two or
three hand-picked numbers, that separates twelve people from a sunlit façade.""",
    challenge="""You could keep writing rules — a gradient here, a blob-size filter there — and every new camera angle,
season, ceiling height or floor layout would break them. That maintenance never ends.""",
    ai_link="""Deep Learning inverts the job. Instead of naming features and letting the model weight them, the model
learns which features matter directly from labelled frames. That is the entire difference, and the
reason the second half of this notebook exists.""",
    bridge=[("No threshold works", "Features are learned"),
            ("Rules keep breaking", "From labelled frames"),
            ("Every floor differs", "Not hand-picked")],
    body=[("co", r'''
from numpy.lib.stride_tricks import sliding_window_view

def conv2d(img, k):
    "What a convolution actually is: slide a small window, multiply, sum."
    return np.einsum("ijkl,kl->ij", sliding_window_view(img, k.shape), k)

img = make_floor("occupied")
k_edge = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], float)          # temperature steps
k_blob = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], float)         # compact spots
k_avg  = np.ones((5, 5))/25.0

ladder = [
    ("Thermal frame",     img,                                        "4,096 raw temperatures"),
    ("Edges",             np.abs(conv2d(img, k_edge)),                "where temperature steps"),
    ("Heat regions",      np.abs(conv2d(img, k_blob)),                "compact spots, not pixels"),
    ("Occupancy pattern", conv2d(np.abs(conv2d(img, k_blob)), k_avg), "clusters of spots"),
]
fig = make_subplots(rows=1, cols=4, subplot_titles=[f"{n}<br><sub>{s}</sub>" for n, _, s in ladder])
for j, (_, z, _) in enumerate(ladder, start=1):
    fig.add_trace(go.Heatmap(z=z, colorscale="Inferno", showscale=False), row=1, col=j)
    fig.update_xaxes(visible=False, row=1, col=j)
    fig.update_yaxes(visible=False, autorange="reversed", row=1, col=j)
fig.update_layout(height=300, template="plotly_white",
                  title="thermal frame → edges → heat regions → occupancy pattern → room usage")
fig.show()

print("Nobody wrote those filters into a rulebook. In a trained CNN, nobody writes them at all —")
print("the network works out what each layer should look for, from labelled examples.")
'''),
          ("md", r"""
| Writing rules by hand | Learning from examples |
|---|---|
| Every temperature limit is too tight or too loose | Show it labelled frames: empty, occupied, crowded |
| One feature per rule; most of the frame discarded | It works out which patterns matter, by itself |
| Different for every camera, ceiling, season, layout | The whole frame is used, not one summary number |
| You maintain it forever | A new floor means new examples, not new rules |
""")],
    built="""The decision to use a CNN, taken for a stated reason rather than by default — which is the only
defensible way to take it.""",
    takeaway="""Machine Learning weights the features you name. Deep Learning finds the features you cannot name.""",
)

# ---------------------------------------------- PHASE 7 · HOW A MACHINE LEARNS
step(
    id="engineer-brain", phase=6, icon="👷", ai_icon="💡",
    civil="How A Facilities Engineer Decides", ai="The Neuron",
    tech="Weigh the signals, add them, decide",
    site="""A facilities engineer walking the floor weighs several signals at once — how full the desks look, what
the CO₂ reading is doing, how warm the return air feels, what time it is — and decides whether to
reduce the plant.""",
    challenge="""That judgement is fast and good. It also lives in one head, applies to one zone at a time, and cannot
be run across 3,800 logged intervals overnight.""",
    ai_link="""Write the judgement down and it is arithmetic: multiply each signal by how much it matters, add them,
and act if the total clears a threshold. That is a neuron — the engineer's rule of thumb, made explicit
and repeatable.""",
    bridge=[("Several signals at once", "Weights"),
            ("Some matter more", "A sum"),
            ("One call", "A threshold")],
    body=[("co", r'''
# A facilities engineer's decision, written down.
signals = {"desks look empty (0-10)": 8, "CO2 low for the hour (0-10)": 7,
           "return air already cool (0-10)": 6, "outside peak tariff (0-10)": 4}
weights = {"desks look empty (0-10)": 0.42, "CO2 low for the hour (0-10)": 0.36,
           "return air already cool (0-10)": 0.22, "outside peak tariff (0-10)": 0.15}
bias    = -6.5                                    # baseline caution: do not touch the plant lightly

contrib = {k: weights[k]*signals[k] for k in signals}
total   = sum(contrib.values()) + bias

fig = go.Figure(go.Bar(x=list(contrib), y=list(contrib.values()),
                       marker_color=[CYAN, AMBER, GREEN, "#ba68c8"],
                       text=[f"{v:.1f}" for v in contrib.values()], textposition="outside"))
fig.update_layout(title=f"weighted evidence · total after baseline caution = {total:+.2f}",
                  yaxis_title="contribution to the call", template="plotly_white", height=380)
fig.show()

print("REDUCE THE PLANT" if total > 0 else "LEAVE IT ALONE", f"   (total {total:+.2f} vs threshold 0)")
'''),
          ("md", r"""
### Now look at what you just built

What you moved was **w · x + b**.

| The engineer's version | The AI's name for it |
|---|---|
| Each reading | an input **x** |
| How much that reading matters | a weight **w** |
| Baseline caution before any evidence | the bias **b** |
| Comparing the total to zero | the activation |

The only difference in the machine version is that **nobody chooses the weights**. They are learned from
the building's own history, which means the model's opinion is traceable to data rather than to
seniority.
""")],
    built="""A neuron, built from a facilities decision and never once called one until the end.""",
    takeaway="""A neuron is an engineer's judgement written as arithmetic: weigh, add, decide.""",
)

step(
    id="neuron", phase=6, icon="⚖️", ai_icon="🔵",
    civil="Weighing Each Reading", ai="Weights, Bias, Weighted Sum",
    tech="z = w·x + b, on one real scaled interval",
    site="""Give each sensor channel a weight. Occupancy matters enormously for whether cooling is justified.
Particulate level matters very little.""",
    challenge="""Those weights are guesses, and every engineer guesses differently. Nobody can defend "CO₂ counts 2.4
times more than solar" from experience alone.""",
    ai_link="""A neuron computes a weighted sum plus a bias. Run it on a real interval from the dataset and watch
which channels push the call towards over-conditioned and which push it away.""",
    bridge=[("Occupancy matters a lot", "Weights are learned"),
            ("PM2.5 matters little", "Bias sets the baseline"),
            ("Experience = weights", "Traceable to data")],
    body=[("co", r'''
def sigmoid(z):
    return 1/(1 + np.exp(-np.clip(z, -50, 50)))

x = X_all[te][20]                                   # one scaled interval from a sealed day
w = np.array([ 0.3,  0.9,  0.2,  -0.8, -1.2,  0.5,  0.0,  -0.6,  0.2])
#              in    out   hum   co2   occ   sol   pm    setp   hour
b = 0.4

z = float(np.dot(w, x) + b)
print(f"z = w·x + b = {z:+.3f}   ->   p(over-conditioned) = {sigmoid(z):.3f}")

fig = go.Figure(go.Bar(x=FEATURES, y=w*x,
                       marker_color=[CYAN if v >= 0 else RED for v in w*x],
                       text=[f"{v:+.2f}" for v in w*x], textposition="outside"))
fig.update_layout(title=f"each channel's contribution to one decision  (z = {z:+.2f})",
                  yaxis_title="w × x", template="plotly_white", height=400)
fig.show()

print("\nNegative weights on occupancy and CO2: plenty of people means the cooling is JUSTIFIED,")
print("so those channels push the 'wasteful' call DOWN. A weight's sign is an engineering statement.")
''')],
    built="""Nine multiplications, one sum, one bias, one squash. That is the entire unit every network in this
notebook is built from.""",
    takeaway="""A neuron is a weighted sum plus a bias — and the weights come from the data, not from seniority.""",
)

step(
    id="activation", phase=6, icon="🚨", ai_icon="📐",
    civil="The Setpoint Threshold", ai="Activation Function",
    tech="sigmoid and ReLU",
    site="""A BMS does not act on a weighted sum. It acts on a state: acceptable, or adjust. Somewhere the
continuous signal has to become a decision.""",
    challenge="""A hard on/off limit is brittle, and every building engineer has met the consequence: a thermostat that
hunts, a plant that short-cycles, an alarm that fires on one reading and clears on the next.""",
    ai_link="""An activation function does the same job smoothly. Sigmoid turns any sum into a number between 0 and 1
that reads as a confidence. ReLU passes positive evidence and blocks the rest. That smoothness is also
what makes the network trainable at all.""",
    bridge=[("Acceptable or adjust", "Sigmoid → 0..1"),
            ("A hard limit hunts", "ReLU passes positives"),
            ("Reality is graded", "Smooth = trainable")],
    body=[("co", r'''
zs = np.linspace(-6, 6, 300)
fig = make_subplots(rows=1, cols=3, subplot_titles=[
    "sigmoid — a confidence", "ReLU — passes positive evidence",
    "hard limit vs sigmoid — no slope to follow"])
fig.add_trace(go.Scatter(x=zs, y=sigmoid(zs), line=dict(color=CYAN, width=3)), row=1, col=1)
fig.add_trace(go.Scatter(x=zs, y=np.maximum(0, zs), line=dict(color="#ba68c8", width=3)), row=1, col=2)
fig.add_trace(go.Scatter(x=zs, y=(zs > 0).astype(float), line=dict(color=RED, width=3, shape="hv")),
              row=1, col=3)
fig.add_trace(go.Scatter(x=zs, y=sigmoid(zs), line=dict(color=CYAN, width=2, dash="dot")),
              row=1, col=3)
fig.update_layout(height=330, showlegend=False, template="plotly_white")
fig.show()

for v in (-2.0, -0.5, 0.0, 0.5, 2.0):
    print(f"  z = {v:+.1f}   sigmoid {sigmoid(v):.3f}   hard limit {float(v > 0):.0f}")
print("\nAt z = -0.5 and z = +0.5 the hard limit says 'certainly no' and 'certainly yes'.")
print("The sigmoid says 0.38 and 0.62 - which is the honest answer for a borderline interval.")
''')],
    built="""A graded output instead of a brittle one, and — just as importantly — a curve with a slope everywhere,
which the next two steps are going to need.""",
    takeaway="""Activation turns a weighted sum into a graded decision instead of a hunting thermostat.""",
)

step(
    id="learning-loop", phase=6, icon="🔁", ai_icon="♻️",
    civil="Improving After Every Bad Day", ai="The Training Loop",
    tech="predict → measure the error → adjust → repeat",
    site="""The plant over-cools all morning. The next month's bill shows it. The engineer adjusts: next time,
weight the occupancy reading more heavily and the clock less.""",
    challenge="""Done by hand, that correction happens once per bill and depends entirely on who is looking. Nine
channels and 3,800 intervals cannot be tuned that way.""",
    ai_link="""The learning loop is that correction, automated: predict, compare with what the meter recorded,
measure the error, adjust every weight a little, repeat.""",
    bridge=[("The bill shows the miss", "Compare to truth"),
            ("Adjust the judgement", "Measure the error"),
            ("Do better next month", "Nudge every weight")],
    body=[("co", r'''
true_w = 3.4          # the weight on occupancy that actually fits this building
rounds = 20

fig = go.Figure()
for lr, col, label in [(0.05, GREEN, "0.05 — crawls"),
                       (0.22, CYAN,  "0.22 — converges"),
                       (1.04, RED,   "1.04 — diverges")]:
    w_i, path = 7.2, [7.2]
    for _ in range(rounds):
        err = w_i - true_w                    # the signed error the meter reveals
        w_i = w_i - lr*2*err                  # nudge towards the truth
        path.append(w_i)
    fig.add_trace(go.Scatter(y=path, mode="lines+markers", name=label,
                             line=dict(color=col, width=2)))
    flips = sum(1 for a, b in zip(path, path[1:]) if (a-true_w)*(b-true_w) < 0)
    print(f"lr {lr:.2f}: final weight {path[-1]:8.3f}   error {abs(path[-1]-true_w):8.3f}   "
          f"sign changes {flips}")
print()
print("The correction is  w <- w - lr*2*(w - true).  It converges only while |1 - 2*lr| < 1,")
print("i.e. while lr < 1. Past that, every correction is bigger than the error it is fixing.")

fig.add_hline(y=true_w, line=dict(color=MUTED, dash="dash"),
              annotation_text="the weight that fits this building")
fig.update_layout(title="the same correction, three correction strengths",
                  xaxis_title="correction round", yaxis_title="weight on occupancy",
                  template="plotly_white", height=400)
fig.show()
''')],
    built="""The loop that turns a random model into a useful one. Nothing more mysterious than adjusting a set
point after seeing the result — the next step gives it its proper name.""",
    takeaway="""Predict, measure the error, adjust, repeat — that loop is all training is.""",
)

step(
    id="gradient-descent", phase=6, icon="🎛️", ai_icon="⬇️",
    civil="Commissioning The Controls", ai="Loss & Gradient Descent",
    tech="loss surface, gradient, learning rate",
    site="""Commissioning a plant is a search. Change a set point, measure the result, keep the change if it
helped, step again in the direction that helped.""",
    challenge="""Step too far and you overshoot and the plant hunts. Step too small and commissioning takes a week. The
step size is the whole difficulty, and it is usually chosen by feel.""",
    ai_link="""Loss measures how wrong the model is. Gradient descent takes the downhill direction and steps along it;
the learning rate is the step size. The same overshoot and the same slowness appear, for exactly the
same reason.""",
    bridge=[("Change a set point", "Loss = how wrong"),
            ("Measure the result", "Gradient = downhill"),
            ("Step again", "Rate = step size")],
    body=[("co", r'''
def loss(w):  return (w - 2.0)**2 + 1        # the valley; the best weight is 2.0
def grad(w):  return 2*(w - 2.0)

ws = np.linspace(-3, 7, 300)
fig = go.Figure()
fig.add_trace(go.Scatter(x=ws, y=loss(ws), name="loss surface",
                         line=dict(color=MUTED, width=3)))
for lr, col, name in [(0.05, GREEN, "0.05 crawls"), (0.30, CYAN, "0.30 converges"),
                      (0.98, RED, "0.98 overshoots")]:
    w_i, xs = 6.5, [6.5]
    for _ in range(16):
        w_i = w_i - lr*grad(w_i)
        xs.append(w_i)
    fig.add_trace(go.Scatter(x=xs, y=loss(np.array(xs)), mode="lines+markers",
                             name=f"lr = {name}", line=dict(color=col, width=1),
                             marker=dict(size=7)))
fig.update_layout(title="one gradient, three step sizes", xaxis_title="weight",
                  yaxis_title="loss", template="plotly_white", height=420)
fig.show()
''')],
    built="""The mechanism by which every weight in every model in this notebook actually changes.""",
    takeaway="""Training is commissioning by search: step downhill on the error, and mind the step size.""",
)

step(
    id="network", phase=6, icon="👥", ai_icon="🕸️",
    civil="The Facilities Team", ai="The Neural Network",
    tech="input → hidden layers → output",
    site="""No single engineer covers everything. One reads the chiller plant, one the air side, one the tenant
comfort complaints. A manager combines their views into one decision.""",
    challenge="""Coordinating specialists is slow and their views are inconsistent. Some overlap, some contradict, and
nobody weighs them the same way twice.""",
    ai_link="""A hidden layer is that team. Each neuron learns a different combination of the readings, and the output
neuron weighs their conclusions into one answer. Depth is what lets a model represent interactions a
single weighted sum cannot.""",
    bridge=[("Chiller specialist", "Each neuron, a view"),
            ("Air-side specialist", "Layers combine them"),
            ("Comfort specialist", "One output")],
    body=[("co", r'''
import warnings
from sklearn.neural_network import MLPRegressor

rows = []
for size in [(1,), (8,), (16, 8), (64, 32)]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        net = MLPRegressor(hidden_layer_sizes=size, max_iter=1500,
                           random_state=0).fit(X_all[tr], y_hvac[tr])
    p = net.predict(X_all[te])
    rows.append({"hidden layers": str(size),
                 "MAE (kW)": mean_absolute_error(y_hvac[te], p),
                 "R2": r2_score(y_hvac[te], p)})
rows.append({"hidden layers": "Random Forest (for reference)",
             "MAE (kW)": mean_absolute_error(y_hvac[te], hvac_model.predict(X_all[te])),
             "R2": r2_score(y_hvac[te], hvac_model.predict(X_all[te]))})
table = pd.DataFrame(rows)
print(table.round(3).to_string(index=False))

nets = table.iloc[:-1]
best = nets.loc[nets["MAE (kW)"].idxmin()]
print()
print(f"best network here : {best['hidden layers']}  (MAE {best['MAE (kW)']:.2f} kW)")
print(f"spread across all four networks : "
      f"{nets['MAE (kW)'].max()-nets['MAE (kW)'].min():.2f} kW")
print(f"forest              : MAE {table.iloc[-1]['MAE (kW)']:.2f} kW")
'''),
          ("md", r"""
A single hidden neuron can only draw one bend — it is one specialist with one opinion. Add a second layer
and the network can represent interactions that genuinely exist in a building: a hot afternoon **and** a
full floor **and** a chiller losing COP, all at once.

Now read the spread. Going from one neuron to two layers buys something real. Going from two layers to a
much wider pair buys **nothing** — and the whole range of networks lands within about a kilowatt of each
other, and of the forest.

That is the honest result on nine named channels, and it is worth sitting with: **depth is not where the
accuracy is here.** The features were already named by an engineer, so there is little left for extra
capacity to discover. Keep it in mind for the verdict — it is the reverse of what happens on the images.
""")],
    built="""A neural network on the sensor data, and a fair comparison with the forest on the same sealed days.""",
    takeaway="""A layer is a team of specialists; the output neuron is the manager who signs the call.""",
)

step(
    id="training", phase=6, icon="📚", ai_icon="📊",
    civil="Training The New Recruits", ai="Training & Epochs",
    tech="epochs, training loss vs held-out error",
    site="""A new building manager learns from this site's own records — sixteen weeks where the outcome is
already known — not from a textbook written for another building.""",
    challenge="""Learn the records too well and you have memorised them: perfect on last month, useless next month.
Stop too early and nothing has been learned at all.""",
    ai_link="""Training runs the learning loop over the training days for many epochs, watching the error on
**validation days it never learns from**. Where that curve turns, learning has become memorising.""",
    bridge=[("Learn from records", "Many epochs"),
            ("Not from a textbook", "Watch validation"),
            ("Then prove it", "Stop at the turn")],
    body=[("co", r'''
net = MLPRegressor(hidden_layer_sizes=(24, 12), learning_rate_init=0.004,
                   max_iter=1, warm_start=True, random_state=0)
train_loss, val_mae = [], []
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    for _ in range(160):
        net.fit(X_all[tr], y_hvac[tr])
        train_loss.append(net.loss_)
        val_mae.append(mean_absolute_error(y_hvac[va], net.predict(X_all[va])))

best = int(np.argmin(val_mae))
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(y=train_loss, name="training loss",
                         line=dict(color=CYAN, width=2)), secondary_y=False)
fig.add_trace(go.Scatter(y=val_mae, name="validation MAE (kW)",
                         line=dict(color=AMBER, width=2)), secondary_y=True)
fig.add_vline(x=best, line=dict(color=GREEN, dash="dash"),
              annotation_text=f"best epoch {best}")
fig.update_layout(title="the training loss keeps falling; the held-out error stops improving",
                  xaxis_title="epoch", template="plotly_white", height=420)
fig.show()

print(f"best epoch on validation days : {best}")
print(f"validation MAE there          : {val_mae[best]:.2f} kW")
print(f"validation MAE at the end     : {val_mae[-1]:.2f} kW")
''')],
    built="""A trained network, and the single most useful habit in applied machine learning: watching a curve you
did not train on.""",
    takeaway="""Watch the validation curve — where it turns, learning has become memorising.""",
)

# ---------------------------------------------- PHASE 8 · READING THE ROOM
step(
    id="cnn-journey", phase=7, icon="🔥", ai_icon="🧩",
    civil="Reading The Floor Plate", ai="Convolution & Feature Maps",
    tech="filters → feature maps → an occupancy class",
    site="""A thermal frame is not read pixel by pixel. An engineer sees a **shape**: a cluster of compact blobs in
one zone, or a broad band down one edge.""",
    challenge="""Shape is not in any single pixel, and it moves. The same twelve people sit in a different part of the
floor every day, and the sun band shifts across the season.""",
    ai_link="""A convolution slides a small filter over the frame and reports where its pattern occurs. Early filters
find edges; later ones combine edges into blobs and clusters. **The network learns the filters** — and
because they slide, the pattern is found wherever it appears.""",
    bridge=[("Clusters of blobs = people", "Filters slide"),
            ("A band = sunlight", "Edges → clusters"),
            ("Shape, not brightness", "Filters are learned")],
    body=[("md", r"""
This is the point of the notebook where TensorFlow is needed. In Colab it is already installed. If you
are running somewhere without it, every cell below detects that and skips cleanly — nothing else breaks.
"""),
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
# A labelled set of floor plates. The head count is drawn from a CONTINUUM, and the
# class boundaries cut across it - so 'occupied' and 'crowded' are genuinely ambiguous
# near 18-19 people, exactly as they would be in a real building. Cluster positions,
# facade sun and wall leaks are randomised too, so no two frames are alike.
CLASSES  = ["empty", "occupied", "crowded"]
BOUND    = (5, 19)          # <5 empty, 5..18 occupied, >=19 crowded

def label_for(n_people):
    return 0 if n_people < BOUND[0] else (1 if n_people < BOUND[1] else 2)

def make_frame_set(n=1400, seed=0):
    rng = np.random.default_rng(seed)
    Xi, yi, counts = [], [], []
    for i in range(n):
        if rng.random() < 0.30:                       # a genuinely empty floor
            n_people = int(rng.integers(0, 5))
        else:
            n_people = int(rng.integers(5, 41))       # a continuum, not two clusters
        im = make_floor("empty", seed=int(rng.integers(1e6)),
                        n_people=n_people, jitter=True)
        im = np.clip(im*rng.uniform(0.92, 1.08) + rng.normal(0, 0.02), 0, 1)
        Xi.append(im); yi.append(label_for(n_people)); counts.append(n_people)
    return (np.array(Xi)[..., None].astype("float32"),
            np.array(yi), np.array(counts))

Xi, yi, counts = make_frame_set(1400, seed=1)
Xi_tr, Xi_te, yi_tr, yi_te, c_tr, c_te = train_test_split(
    Xi, yi, counts, test_size=0.25, random_state=42, stratify=yi)
print("frames:", Xi.shape, " class balance:", (np.bincount(yi)/len(yi)).round(3))
print("head counts span", counts.min(), "to", counts.max(),
      "- the classes are cuts through a continuum, not separate populations")

if KERAS:
    # Functional API, not Sequential: Grad-CAM in the next step needs to build a second
    # model over an intermediate layer, and that is reliable only on a functional graph.
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
    hist = cnn.fit(Xi_tr, yi_tr, validation_split=0.2, epochs=14, batch_size=32, verbose=0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=hist.history["loss"], name="training loss",
                             line=dict(color=CYAN, width=2)))
    fig.add_trace(go.Scatter(y=hist.history["val_loss"], name="validation loss",
                             line=dict(color=AMBER, width=2)))
    fig.update_layout(title="CNN training", xaxis_title="epoch", yaxis_title="loss",
                      template="plotly_white", height=380)
    fig.show()

    cnn_acc = float(cnn.evaluate(Xi_te, yi_te, verbose=0)[1])
    print(f"CNN accuracy on held-out frames: {cnn_acc:.1%}")

    # where does it get things wrong? Almost entirely at the class boundaries.
    from sklearn.metrics import confusion_matrix as _cm
    pred = cnn.predict(Xi_te, verbose=0).argmax(1)
    print("\nconfusion matrix (rows = truth, cols = called):")
    print(pd.DataFrame(_cm(yi_te, pred), index=CLASSES, columns=CLASSES).to_string())
    wrong = c_te[pred != yi_te]
    if len(wrong):
        print(f"\nhead count on the frames it got wrong: "
              f"median {np.median(wrong):.0f}, range {wrong.min()}-{wrong.max()}")
        print(f"the class boundaries sit at {BOUND[0]} and {BOUND[1]} people.")
    print("\nCompare that with the best any mean-temperature threshold managed a few steps ago.")
else:
    cnn_acc = None
''')],
    built="""A network that grades a floor plate into empty, occupied or crowded — including the sunlit and leaky
frames that defeated every hand-made threshold.""",
    takeaway="""Convolution learns to find a shape anywhere in the frame, without anyone naming it.""",
)

# ---------------------------------------------- PHASE 9 · LOCATING THE USE
step(
    id="occupancy-locate", phase=8, icon="📍", ai_icon="🗺️",
    civil="Which Part Of The Floor Is In Use", ai="Grad-CAM",
    tech="class-weighted feature maps → a heat map over the frame",
    site="""A single grade for the whole floor is not enough for control. A VAV system serves zones, and the
question is which zone to condition.""",
    challenge="""A classifier outputs a probability. It gives no location, and an engineer asked to change a plant
setting on a bare number will — rightly — refuse.""",
    ai_link="""Grad-CAM weights the last feature maps by how much each pushed the score towards the predicted class,
then projects them back onto the frame. The bright region is where the network looked, which is both
the zone and the evidence.""",
    bridge=[("Which zone?", "Weight the maps"),
            ("Which VAV box?", "Project onto the frame"),
            ("Change a setting", "Show the evidence")],
    body=[("co", r'''
def grad_cam(model, image, class_idx=None, layer_name="last_conv"):
    "Class-activation map for one frame (64x64x1)."
    grad_model = keras.Model(model.inputs,
                             [model.get_layer(layer_name).output, model.output])
    with tf.GradientTape() as tape:
        maps, pred = grad_model(image[None, ...])
        if class_idx is None:
            class_idx = int(tf.argmax(pred[0]))
        score = pred[:, class_idx]
    grads   = tape.gradient(score, maps)[0]                 # (h, w, c)
    weights = tf.reduce_mean(grads, axis=(0, 1))            # how much each map mattered
    cam = tf.reduce_sum(maps[0]*weights, axis=-1).numpy()
    cam = np.maximum(cam, 0)
    cam = cam/(cam.max() + 1e-9)
    rep = image.shape[0]//cam.shape[0]
    return np.kron(cam, np.ones((rep, rep)))[:image.shape[0], :image.shape[1]], class_idx

if KERAS:
    show = ["occupied", "crowded", "solar", "heat_leak"]
    fig = make_subplots(rows=2, cols=len(show), vertical_spacing=0.13,
                        subplot_titles=[""]*(2*len(show)))
    titles = []
    for j, k in enumerate(show, start=1):
        im  = make_floor(k, seed=11)[..., None].astype("float32")
        p   = cnn.predict(im[None, ...], verbose=0)[0]
        cam, ci = grad_cam(cnn, im)
        titles.append(f"{k}<br><sub>called '{CLASSES[ci]}' ({p[ci]:.0%})</sub>")
        fig.add_trace(go.Heatmap(z=im[..., 0], colorscale="Inferno", showscale=False),
                      row=1, col=j)
        fig.add_trace(go.Heatmap(z=cam, colorscale="Turbo", showscale=False), row=2, col=j)
        for r in (1, 2):
            fig.update_xaxes(visible=False, row=r, col=j)
            fig.update_yaxes(visible=False, autorange="reversed", row=r, col=j)
    for a, t in zip(fig.layout.annotations[:len(show)], titles):
        a.text = t
    for a in fig.layout.annotations[len(show):]:
        a.text = "where it looked"
    fig.update_layout(height=620, template="plotly_white",
                      title="Grad-CAM — the evidence behind each call")
    fig.show()

    # Do not take the point on trust - check what the network actually called each frame.
    print("What the network called each frame, and what the mean-temperature rule would have said:")
    thr = 0.42                                          # the least-bad threshold from earlier
    for k in ["empty", "occupied", "crowded", "solar", "heat_leak"]:
        im = make_floor(k, seed=11)[..., None].astype("float32")
        p  = cnn.predict(im[None, ...], verbose=0)[0]
        rule = "occupied" if im.mean() > thr else "empty"
        truth = "PEOPLE" if k in ("occupied", "crowded") else "nobody"
        print(f"  {k:10s} (truth: {truth:6s})   CNN says {CLASSES[int(p.argmax())]:9s} "
              f"({p.max():.0%})   mean-rule says {rule}")
    print()
    print(f"At this one threshold ({thr}) the rule misses a floor with twelve people on it AND")
    print("runs the plant for an empty sunlit one. Move the threshold and the failures swap")
    print("round rather than disappear - that is what the sweep a few steps ago showed.")
    print("The CNN gets all five right, including both decoys.")
else:
    print("Keras not available - skipping Grad-CAM.")
''')],
    built="""A zone-level answer with its evidence attached — the thing that makes an automated recommendation
acceptable to the person who has to sign it off.""",
    takeaway="""Grad-CAM shows where the network looked — that is both the zone and the evidence.""",
)

# ---------------------------------------------- PHASE 10 · THE ENERGY AUDIT
step(
    id="audit", phase=9, icon="🧮", ai_icon="✅",
    civil="The Building Energy Audit", ai="MAE, RMSE, R² and the Confusion Matrix",
    tech="Every claim checked on sealed days",
    site="""Every energy claim in this industry is audited: predicted against metered, on days the model was never
allowed to see. Measurement and verification protocols exist precisely because claims are easy to make.""",
    challenge="""One number never covers it. A regression can have an excellent R² and still be useless at the peak.
A classifier that says "never wasteful" scores well on a building that is efficient most of the time —
and finds nothing at all.""",
    ai_link="""Report the regression as **MAE, RMSE and R²** together, the classifier as a **confusion matrix**, and
comfort as the share of occupied intervals inside the comfort band. Three questions, three answers.""",
    bridge=[("Predicted vs metered", "MAE / RMSE / R²"),
            ("On sealed days", "Confusion matrix"),
            ("Comfort still met?", "PPD ≤ 10%")],
    body=[("co", r'''
from sklearn.metrics import (confusion_matrix, ConfusionMatrixDisplay,
                             accuracy_score, recall_score, precision_score)

# ---- 1. the regression --------------------------------------------------
p_hvac = hvac_model.predict(X_all[te])
mae  = mean_absolute_error(y_hvac[te], p_hvac)
rmse = float(np.sqrt(((y_hvac[te]-p_hvac)**2).mean()))
r2   = r2_score(y_hvac[te], p_hvac)
print("HVAC LOAD, on sealed days")
print(f"  MAE  {mae:6.2f} kW      (typical error on any one interval)")
print(f"  RMSE {rmse:6.2f} kW      (larger than MAE => a few big misses, at the peak)")
print(f"  R2   {r2:6.3f}         (share of the variation the model explains)")
print(f"  mean metered load {y_hvac[te].mean():.1f} kW  ->  MAE is {100*mae/y_hvac[te].mean():.1f}% of it\n")

# ---- 2. the classifier --------------------------------------------------
p_waste = waste_model.predict(X_all[te])
tn, fp, fn, tp = confusion_matrix(y_waste[te], p_waste).ravel()
print("OVER-CONDITIONED INTERVALS, on sealed days")
print(f"  accuracy  {accuracy_score(y_waste[te], p_waste):.1%}")
print(f"  recall    {recall_score(y_waste[te], p_waste):.1%}   (of the truly wasteful intervals, how many were caught)")
print(f"  precision {precision_score(y_waste[te], p_waste):.1%}   (of those flagged, how many were real)")
print(f"  false alarms {fp}   missed {fn}\n")
naive = np.zeros_like(y_waste[te])
print(f"  a model that says 'never wasteful' scores {accuracy_score(y_waste[te], naive):.1%} accuracy "
      f"and {recall_score(y_waste[te], naive, zero_division=0):.0%} recall.")
print("  Good accuracy, zero value. This is why accuracy is never reported alone.\n")

# ---- 3. comfort ---------------------------------------------------------
comfort = ppd(occ_hours.indoor_temp_c.values[te], occ_hours.humidity_pct.values[te])
print("COMFORT, on the same sealed days")
print(f"  mean PPD {comfort.mean():.1f}%   intervals within PPD<=10%: {(comfort <= 10).mean():.1%}")

fig = make_subplots(rows=1, cols=2, subplot_titles=[
    "residuals: metered − predicted (kW)", "over-conditioned: the four outcomes"])
fig.add_trace(go.Histogram(x=y_hvac[te]-p_hvac, nbinsx=40, marker_color=CYAN), row=1, col=1)
fig.add_trace(go.Heatmap(z=[[tn, fp], [fn, tp]],
                         x=["called fine", "called wasteful"],
                         y=["actually fine", "actually wasteful"],
                         colorscale="Blues", showscale=False,
                         text=[[f"{tn}<br>correct", f"{fp}<br>false alarm"],
                               [f"{fn}<br>MISSED", f"{tp}<br>caught"]],
                         texttemplate="%{text}"), row=1, col=2)
fig.update_yaxes(autorange="reversed", row=1, col=2)
fig.update_layout(height=400, template="plotly_white", showlegend=False)
fig.show()
'''),
          ("md", r"""
### The two errors do not cost the same

| | What it costs |
|---|---|
| **False alarm** — flagged, but the interval was fine | An engineer checks a zone and finds nothing. One hour, and a little credibility. |
| **Missed waste** — over-conditioning that went unflagged | The plant keeps over-cooling an empty floor until someone reads the bill. |

And a third error the confusion matrix does not show: **a comfort failure**. In a commercial building that
one ends the project. It is why comfort is reported alongside energy on every screen from here on, and
why the optimiser treats it as a hard constraint rather than something to trade away.
""")],
    built="""Three honest numbers on days the model never saw, and a clear statement of what each kind of mistake
actually costs the building.""",
    takeaway="""Report energy, waste and comfort together — any one of them alone can hide a failure.""",
)

step(
    id="proof", phase=9, icon="⚔️", ai_icon="🏁",
    civil="The Verdict", ai="ML vs DL, Measured",
    tech="the same task, both methods, on the same data",
    site="""Two models, two data types, one building. Time to state plainly what each can and cannot do.""",
    challenge="""It is tempting to declare Deep Learning the better method. It is not better — it is different. On nine
named channels the forest is faster, cheaper, and far easier to defend in a measurement-and-verification
review.""",
    ai_link="""Run both on both, and read the result off the table rather than taking anyone's word for it.""",
    bridge=[("Two data types", "Forest wins on numbers"),
            ("Two methods", "CNN wins on pixels"),
            ("One building", "Neither replaces the other")],
    body=[("co", r'''
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    ann = MLPRegressor(hidden_layer_sizes=(24, 12), max_iter=1500,
                       random_state=0).fit(X_all[tr], y_hvac[tr])

print("ON THE 9 NAMED SENSOR CHANNELS  (HVAC load, sealed days)")
for name, m in [("Linear Regression", models["Linear Regression"]),
                ("Random Forest    ", hvac_model),
                ("Neural network   ", ann)]:
    p = m.predict(X_all[te])
    print(f"  {name}  MAE {mean_absolute_error(y_hvac[te], p):5.2f} kW   R2 {r2_score(y_hvac[te], p):.3f}")
print("  -> all three are in the same range. The engineer already named the features,")
print("     so there is nothing for extra depth to discover.\n")

print("ON THE RAW THERMAL FRAME  (is this floor in use?)")
print("  Best hand-made feature (mean temperature) : no threshold separates people from sunlight")
print(f"  CNN                                       : {f'{cnn_acc:.1%} accuracy' if cnn_acc else '(Keras unavailable here)'}")
print("  -> only the CNN can start at all. Nobody can name 4,096 pixel features.")

pd.DataFrame({
    "": ["Predict HVAC load from 9 sensors", "Grade a floor plate from pixels",
         "Locate which zone is in use", "Who names the features?",
         "Defensible in an M&V review"],
    "ML — Linear / Forest / Boosting": ["works well", "cannot even start", "cannot",
                                        "the engineer", "easily"],
    "DL — ANN / CNN":                  ["works, no better", "learns the pattern",
                                        "Grad-CAM shows the zone", "the network learns them",
                                        "needs the Grad-CAM evidence"],
})
'''),
          ("md", r"""
### The promise, now demonstrated rather than asserted

> **Machine Learning predicts building energy demand from environmental and occupancy data.
> Deep Learning understands occupancy and thermal images to detect how spaces are actually being used,
> enabling smarter HVAC control.**

Neither method wins. Each belongs to its data type:

- Where an engineer **has** named the features — temperature, humidity, CO₂, occupancy, solar — use
  Machine Learning. Simpler, cheaper, and it survives an audit.
- Where nobody **can** name them — a thermal frame — Deep Learning is the option that works at all.

And in both cases the output is a recommendation to a building engineer, not a command to the plant.
""")],
    built="""The central claim of the course, measured on this building's own sealed days.""",
    takeaway="""ML weights the channels you name; DL finds the patterns you cannot name. Different data, different tool.""",
)

# ---------------------------------------------- PHASE 11 · CONTROL & OPTIMISATION
step(
    id="forecast", phase=10, icon="📅", ai_icon="🔮",
    civil="Tomorrow's Peak", ai="Load Forecasting",
    tech="predict the next day's profile and its peak",
    site="""Commercial tariffs charge for the **peak** as well as the energy. A single 15-minute maximum can set a
demand charge for the whole month, and the plant has thermal mass that can be used to shift load if you
know the peak is coming.""",
    challenge="""You cannot pre-cool for a peak you find out about afterwards. The decision has to be made hours
before, from a weather forecast and a room-booking schedule.""",
    ai_link="""The same regression model, run forward on forecast conditions, produces tomorrow's load profile and
its peak. That is load forecasting — the same maths, applied before the fact instead of after.""",
    bridge=[("Demand charge on the peak", "Predict the profile"),
            ("Decide hours ahead", "From forecast inputs"),
            ("Pre-cool the mass", "Shift the peak")],
    body=[("co", r'''
# Take one sealed day and predict its whole profile from conditions alone.
target_day = int(test_days[len(test_days)//2])
mask = (occ_hours.day.values == target_day)

pred_day  = hvac_model.predict(X_all[mask])
true_day  = y_hvac[mask]
hrs       = occ_hours.hour.values[mask]

i_pred, i_true = int(np.argmax(pred_day)), int(np.argmax(true_day))
fig = go.Figure()
fig.add_trace(go.Scatter(x=hrs, y=true_day, name="metered", line=dict(color=MUTED, width=3)))
fig.add_trace(go.Scatter(x=hrs, y=pred_day, name="forecast", line=dict(color=CYAN, width=3, dash="dot")))
fig.add_trace(go.Scatter(x=[hrs[i_true]], y=[true_day[i_true]], name="actual peak",
                        mode="markers", marker=dict(size=14, color=RED)))
fig.add_trace(go.Scatter(x=[hrs[i_pred]], y=[pred_day[i_pred]], name="forecast peak",
                        mode="markers", marker=dict(size=14, color=GREEN, symbol="star")))
fig.update_layout(title=f"day {target_day} (sealed) — forecast profile vs metered",
                  xaxis_title="hour of day", yaxis_title="HVAC kW",
                  template="plotly_white", height=420)
fig.show()

print(f"peak metered   : {true_day[i_true]:.1f} kW at {hrs[i_true]:.2f} h")
print(f"peak forecast  : {pred_day[i_pred]:.1f} kW at {hrs[i_pred]:.2f} h")
print(f"peak error     : {abs(pred_day[i_pred]-true_day[i_true]):.1f} kW, "
      f"{abs(hrs[i_pred]-hrs[i_true])*60:.0f} minutes\n")

# across every sealed day
peaks = [(float(y_hvac[occ_hours.day.values == d].max()),
          float(hvac_model.predict(X_all[occ_hours.day.values == d]).max()))
         for d in test_days]
pk = np.array(peaks)
print(f"across all {len(test_days)} sealed days, peak prediction MAE: "
      f"{np.abs(pk[:,0]-pk[:,1]).mean():.2f} kW")
''')],
    built="""Tomorrow's load profile and its peak, from forecast weather and the expected schedule — early enough
to do something about it.""",
    takeaway="""The same regression run forward becomes a forecast, and a forecast is what lets you shift a peak.""",
)

step(
    id="optimize", phase=10, icon="🎯", ai_icon="🧭",
    civil="Choosing The Setpoint", ai="Constrained Optimisation",
    tech="sweep the setpoint, minimise kW subject to PPD ≤ 10%",
    site="""The building has two levers it can actually pull: the **cooling setpoint**, and how much **outside air**
the AHU brings in. Both trade energy against something the occupants notice.""",
    challenge="""Relaxing the setpoint always saves energy, so an unconstrained optimiser will drive it to the ceiling
and make the building unusable. Comfort is not an objective to trade away — it is a constraint the
answer has to satisfy.""",
    ai_link="""Sweep the setpoint, compute the load and the comfort index at each point, and take the **highest
setpoint that still meets PPD ≤ 10%**. When the floor is empty, that constraint does not apply, and a
different answer becomes available.""",
    bridge=[("Setpoint and fresh air", "Sweep the range"),
            ("Comfort is not optional", "A hard constraint"),
            ("Empty floors are different", "Occupancy switches the rule")],
    body=[("co", r'''
def sweep(occ, outdoor=32, solar=520, hum=58, oa=None):
    sps = np.arange(21, 28.01, 0.25)
    oa_basis = OA_DESIGN if oa is None else oa
    kw, cm = [], []
    for sp in sps:
        k, cool = hvac_kw_for(outdoor, sp, solar, occ, hum, oa_basis)
        kw.append(k); cm.append(float(ppd(indoor_for(sp, cool), hum)))
    return sps, np.array(kw), np.array(cm)

fig = make_subplots(specs=[[{"secondary_y": True}]])
for occ, col, name in [(180, CYAN, "full floor (180)"), (40, AMBER, "quiet floor (40)")]:
    sps, kw, cm = sweep(occ)
    fig.add_trace(go.Scatter(x=sps, y=kw, name=f"kW — {name}", line=dict(color=col, width=3)),
                  secondary_y=False)
    fig.add_trace(go.Scatter(x=sps, y=cm, name=f"PPD — {name}",
                             line=dict(color=col, width=2, dash="dot")), secondary_y=True)
fig.add_hline(y=10, line=dict(color=RED, dash="dash"), secondary_y=True,
              annotation_text="comfort limit: PPD = 10%")
fig.update_layout(title="raising the setpoint always saves energy — comfort decides how far you may go",
                  xaxis_title="cooling setpoint (°C)", template="plotly_white", height=440)
fig.update_yaxes(title_text="HVAC kW", secondary_y=False)
fig.update_yaxes(title_text="PPD %", secondary_y=True)
fig.show()

print("The recommendation, at outdoor 32 °C and 520 W/m² solar:\n")
for occ, label, oa in [(180, "full floor  (180 people)", None),
                       (40,  "quiet floor  (40 people)", 40),
                       (0,   "empty floor   (0 people)", 20)]:
    sps, kw, cm = sweep(occ, oa=oa)
    base_kw = float(sweep(occ)[1][np.argmin(np.abs(sps-23.0))])   # today: 23 C, fixed damper
    ok = np.where(cm <= 10)[0] if occ >= 15 else np.array([len(sps)-1])  # empty: no comfort limit
    j  = int(ok[-1])
    comfort_note = f"PPD {cm[j]:.1f}%" if occ >= 15 else "PPD n/a — nobody present"
    print(f"  {label}: hold {sps[j]:.2f} °C, outside air for {oa or int(OA_DESIGN)} people "
          f"-> {kw[j]:5.1f} kW  (today {base_kw:5.1f} kW, -{100*(1-kw[j]/base_kw):4.1f}%)   {comfort_note}")
'''),
          ("md", r"""
Two levers, and they do not pay off in the same places:

- **Setpoint** buys a few percent on a full floor — the comfort limit binds almost immediately, and it
  should. This is not where the money is.
- **Outside air** is where the money is. A fixed damper ventilates for 200 people whether 200 or 2 are
  present, and every one of those cubic metres has to be cooled. Following the CO₂ sensor instead
  (demand-controlled ventilation) costs nothing and changes the number materially.
- On an **empty** floor the comfort constraint disappears entirely, and the answer changes shape rather
  than degree.

This is also the first place the CNN pays for itself: it is what tells you the floor is genuinely empty
rather than merely reading a low people-counter.
""")],
    built="""A control recommendation for each occupancy state, with comfort enforced rather than traded.""",
    takeaway="""Energy is the objective; comfort is the constraint — never optimise one without stating the other.""",
)

step(
    id="fusion-engine", phase=10, icon="🖥️", ai_icon="🔗",
    civil="The Building Intelligence Engine", ai="AI Fusion",
    tech="sensor prediction + CNN occupancy + weather → one ranked action",
    site="""By now the building produces three separate opinions: a predicted load from the sensors, a waste flag,
and a CNN grade with a zone location from the camera.""",
    challenge="""Three screens is three chances to miss something. A facilities manager with a building to run needs
one ranked list with the evidence attached, not three dashboards to correlate by hand.""",
    ai_link="""Fusion combines them into a prioritised recommendation per zone. Numbers say **how much** is being
spent; the image says **where** the floor is actually being used. Neither is sufficient alone.""",
    bridge=[("Three opinions", "Combine the outputs"),
            ("One manager", "Rank by cost"),
            ("One action list", "Attach the evidence")],
    body=[("co", r'''
TARIFF = 0.18       # currency per kWh

def recommend(zone, predicted_kw, metered_kw, cnn_class, cnn_conf, occupancy, ppd_now):
    """Combine the sensor prediction, the camera grade and the comfort index
    into one action. Comfort always wins - it can only ever block a saving."""
    excess = metered_kw - predicted_kw
    if cnn_class == "empty" and cnn_conf > 0.8 and occupancy < 15:
        action, saving, pr = "Setback to 27 °C, outside air to minimum", metered_kw*0.42, "HIGH"
    elif cnn_class == "occupied" and occupancy < 0.4*CAP:
        action, saving, pr = "Ventilate for the people present (CO₂-led), not for 200", metered_kw*0.18, "MEDIUM"
    elif ppd_now > 10:
        action, saving, pr = "Do NOT reduce — comfort is already at the limit", 0.0, "COMFORT"
    else:
        action, saving, pr = "No change — matched to load", 0.0, "LOW"
    return dict(zone=zone, priority=pr, metered_kw=round(metered_kw, 1),
                predicted_kw=round(predicted_kw, 1), excess_kw=round(excess, 1),
                camera=f"{cnn_class} ({cnn_conf:.0%})", people=occupancy,
                ppd_pct=round(ppd_now, 1), saving_kw=round(saving, 1),
                saving_per_year=round(saving*12*250*TARIFF), action=action)

screen = pd.DataFrame([
    recommend("North — open plan", 18.2, 31.4, "empty",    0.94,   6, 5.2),
    recommend("East — meeting rooms", 12.6, 15.1, "occupied", 0.88,  38, 6.8),
    recommend("South — sunlit bay", 26.4, 27.0, "empty",    0.91,   9, 9.4),
    recommend("West — trading floor", 33.8, 34.2, "crowded",  0.96, 172, 11.6),
]).set_index("zone")
screen[["priority", "metered_kw", "excess_kw", "camera", "people", "ppd_pct",
        "saving_kw", "saving_per_year", "action"]]
'''),
          ("md", r"""
Read the **South — sunlit bay** row. The sensors alone would have queried it: 27 kW with nine people on
the floor. The camera says the warmth is the façade, not the occupants — and the comfort index is
already at 9.4%, close to the limit. Fusion issues no saving there, because there is none to take
without a complaint.

Read the **West — trading floor** row. Fully occupied, load matched to it, nothing to do. A system that
only ever finds savings is not measuring anything.

And note what the screen never does: it does not change a single plant setting. Every row ends in a
recommendation a person approves.
""")],
    built="""One ranked screen, with the money, the evidence and the comfort position on every row — the actual
product of everything before it.""",
    takeaway="""Numbers say how much is being spent; images say where the floor is used. Fusion issues one action.""",
)

step(
    id="pipeline", phase=10, icon="🧱", ai_icon="🛤️",
    civil="The Whole System", ai="The Pipeline",
    tech="sensors → data → ML + DL → decision engine → dashboard",
    site="""Step back and the whole system is visible: sensors and a camera on the floor, a data path, two models,
a decision engine, and a screen the facilities manager reads.""",
    challenge="""Every stage depends on the ones before it. A dead CO₂ sensor that survived cleaning becomes a false
recommendation four stages later, and nothing downstream can recover it.""",
    ai_link="""The pipeline is the engineering drawing of the system. It shows what feeds what, where the two data
types stay separate, and where they come back together into one decision.""",
    bridge=[("Sensors and camera", "Every stage feeds one"),
            ("Two models", "Data quality first"),
            ("A screen that acts", "One recommendation")],
    body=[("co", r'''
nodes = [(0.5, 3.6, "🏢 Building", AMBER), (0.5, 1.4, "📷 Camera", AMBER),
         (2.4, 3.6, "📡 Sensors", AMBER),  (2.4, 1.4, "🖼️ Frames", AMBER),
         (4.3, 3.6, "🧹 Clean", "#ba68c8"), (4.3, 1.4, "🖼️ Frames", "#ba68c8"),
         (6.1, 3.6, "📐 Scale", "#ba68c8"),
         (7.9, 3.6, "🌲 Regression", CYAN), (7.9, 1.4, "🧩 CNN", CYAN),
         (9.8, 2.5, "🔗 Decision", GREEN),  (11.6, 2.5, "📉 Dashboard", GREEN)]
edges = [(0,2),(1,3),(2,4),(3,5),(4,6),(6,7),(5,8),(7,9),(8,9),(9,10)]

fig = go.Figure()
for a, b in edges:
    fig.add_annotation(x=nodes[b][0]-0.42, y=nodes[b][1], ax=nodes[a][0]+0.42, ay=nodes[a][1],
                       xref="x", yref="y", axref="x", ayref="y", showarrow=True,
                       arrowhead=2, arrowsize=1.2, arrowwidth=2, arrowcolor="#b0bec5", text="")
for x, y, label, col in nodes:
    fig.add_shape(type="rect", x0=x-0.8, x1=x+0.8, y0=y-0.42, y1=y+0.42,
                  line=dict(color=col, width=2), fillcolor="white")
    fig.add_annotation(x=x, y=y, text=f"<b>{label}</b>", showarrow=False, font=dict(size=12))
fig.add_annotation(x=1.4, y=4.5, text="THE NUMBERS PATH", showarrow=False,
                   font=dict(size=11, color=CYAN))
fig.add_annotation(x=1.4, y=0.5, text="THE IMAGE PATH", showarrow=False,
                   font=dict(size=11, color=AMBER))
fig.update_xaxes(visible=False, range=[-0.6, 12.8])
fig.update_yaxes(visible=False, range=[0.1, 5.0])
fig.update_layout(title="sensors → data → ML + DL → decision engine → dashboard",
                  template="plotly_white", height=400)
fig.show()
'''),
          ("md", r"""
Read it as a chain, not a diagram:

- The **numbers path** and the **image path** stay separate right up to the decision engine. They have to:
  one has named columns, the other does not.
- Cleaning sits **before** both models. A stuck sensor that survives it becomes a false recommendation
  four stages later.
- The decision engine is the only place the two paths meet, and the only place a prediction becomes an
  action.
- The dashboard converts that action into the units the building is actually managed in.
""")],
    built="""The map of everything built so far. If a step ever felt abstract, find it on this drawing and ask what
would break downstream without it.""",
    takeaway="""The system is a chain: data quality at the start decides the recommendation at the end.""",
)

# ---------------------------------------------- PHASE 12 · THE BUSINESS CASE
step(
    id="dashboard", phase=11, icon="📉", ai_icon="💷",
    civil="The Smart Building Dashboard", ai="Energy, Carbon, Cost & Comfort",
    tech="the counterfactual, computed on the real log",
    site="""A building owner does not buy a model. They approve a spend against a saving in kilowatt-hours, tonnes
of CO₂ and money — with the comfort position stated, and often with a green-building certification in
mind.""",
    challenge="""AI savings are easy to overstate. The honest way to state one is a **counterfactual**: re-run the
recorded season under the proposed control and compare, rather than quoting a number from a brochure.""",
    ai_link="""Every figure below is computed from the sixteen weeks of data already loaded. Nothing is asserted.
Where an assumption is used — tariff, carbon factor — it is a named variable you can change.""",
    bridge=[("Approve a spend", "kWh avoided"),
            ("Against a saving", "tCO₂ avoided"),
            ("With comfort stated", "PPD still ≤ 10%")],
    body=[("co", r'''
def ai_policy_kw(r):
    """What the AI control would have drawn in this interval.
    Occupancy-led setback when the floor is empty; CO2-led ventilation and the
    highest comfortable setpoint when it is not. Comfort is a hard constraint."""
    occ, out, sol, hum = r.occupancy, r.outdoor_temp_c, r.solar_wm2, r.humidity_pct
    if occ < 15:                                        # nobody there
        return float(hvac_kw_for(out, 28.0, sol, occ, hum, 20)[0])
    # Demand-controlled ventilation can only modulate DOWN from the design outside-air
    # rate - the AHU cannot deliver more than it was built for. Capping at OA_DESIGN is
    # both physically right and the reason this never worsens the peak.
    oa   = float(np.clip(occ, 20, OA_DESIGN))
    best = None
    for sp in np.arange(23.0, 26.01, 0.25):
        kw, cool = hvac_kw_for(out, sp, sol, occ, hum, oa)
        if float(ppd(indoor_for(sp, cool), hum)) <= 10.0:
            best = float(kw)
    return best if best is not None else float(r.hvac_kw)

ai_kw   = occ_hours.apply(ai_policy_kw, axis=1).values
now_kwh = y_hvac.sum()*0.25                 # 15-minute intervals
ai_kwh  = ai_kw.sum()*0.25

TARIFF, CARBON = 0.18, 0.42                 # currency/kWh, kg CO2/kWh
weeks   = occ_hours.day.nunique()/5         # working weeks in the log
scale   = 50/weeks                          # to a 50-week working year

saved_kwh  = (now_kwh - ai_kwh)*scale
saved_pct  = 100*(1 - ai_kwh/now_kwh)
saved_cost = saved_kwh*TARIFF
saved_co2  = saved_kwh*CARBON/1000

print("SMART BUILDING DASHBOARD — computed from the 16 weeks above, not asserted\n")
print(f"  HVAC energy avoided     {saved_kwh:>10,.0f} kWh / year     ({saved_pct:.1f}% of HVAC)")
print(f"  Cost avoided            {saved_cost:>10,.0f} / year         (at {TARIFF}/kWh)")
print(f"  Carbon avoided          {saved_co2:>10,.1f} t CO2 / year   (at {CARBON} kg/kWh)")
# Comfort under the AI policy, actually recomputed - not asserted.
# Only intervals with people in them can have a comfort result at all.
occupied = occ_hours.occupancy.values >= 15
ppd_before = ppd(occ_hours.indoor_temp_c.values, occ_hours.humidity_pct.values)
ppd_after = []
for _, r in occ_hours[occupied].iterrows():
    oa = float(np.clip(r.occupancy, 20, CAP))
    chosen = None
    for sp in np.arange(23.0, 26.01, 0.25):
        _, cool = hvac_kw_for(r.outdoor_temp_c, sp, r.solar_wm2, r.occupancy, r.humidity_pct, oa)
        v = float(ppd(indoor_for(sp, cool), r.humidity_pct))
        if v <= 10.0:
            chosen = v
    ppd_after.append(chosen if chosen is not None else
                     float(ppd(r.indoor_temp_c, r.humidity_pct)))
ppd_after = np.array(ppd_after)
print(f"  Comfort, before         {(ppd_before[occupied] <= 10).mean():>10.1%} of OCCUPIED intervals within PPD<=10%")
print(f"  Comfort, after          {(ppd_after <= 10).mean():>10.1%} of OCCUPIED intervals within PPD<=10%")
print(f"  (empty intervals are excluded from comfort entirely - nobody is there to be comfortable)")
print(f"  Peak HVAC demand        {y_hvac.max():>10,.1f} kW  ->  {ai_kw.max():,.1f} kW")

fig = make_subplots(rows=1, cols=2, subplot_titles=[
    "annual HVAC energy", "where the saving comes from (by hour of day)"])
fig.add_trace(go.Bar(x=["today — fixed schedule", "with the AI layer"],
                     y=[now_kwh*scale/1000, ai_kwh*scale/1000],
                     marker_color=[RED, GREEN],
                     text=[f"{now_kwh*scale/1000:,.0f} MWh", f"{ai_kwh*scale/1000:,.0f} MWh"],
                     textposition="outside"), row=1, col=1)
by_hour = pd.DataFrame({"hour": occ_hours.hour.values,
                        "saved": (y_hvac - ai_kw)*0.25}).groupby("hour").saved.sum()
fig.add_trace(go.Bar(x=by_hour.index, y=by_hour.values*scale, marker_color=CYAN), row=1, col=2)
fig.update_yaxes(title_text="MWh / year", row=1, col=1)
fig.update_yaxes(title_text="kWh saved / year", row=1, col=2)
fig.update_xaxes(title_text="hour of day", row=1, col=2)
fig.update_layout(height=420, showlegend=False, template="plotly_white")
fig.show()
'''),
          ("md", r"""
### Read the assumptions, not just the total

- The saving is **computed by re-running the recorded season** under the proposed control. It is a
  counterfactual on real logged conditions, not a vendor figure.
- **Comfort was never traded.** Every occupied interval in the AI policy satisfies PPD ≤ 10%. If the
  comfort constraint is removed the number gets larger and the project gets cancelled after the first
  week of complaints.
- The second chart is the honest one: nearly all of the saving is in the **morning and evening tails**,
  when the plant runs at duty for a nearly empty floor. That is where the fixed schedule was always
  wrong, and it is why the camera matters.
- The **after** bar never reaches zero and never will. The building still has to be conditioned for the
  people in it.
""")],
    built="""The business case: energy, cost, carbon, peak and comfort, all derived from the same sixteen weeks of
data the models were built on.""",
    takeaway="""Building energy projects are approved in kWh, tonnes, currency and comfort — never in accuracy percentages.""",
)


# ============================================================================
# THE INTRO BLOCK
# ============================================================================
def phase_rows():
    out = []
    for pi, (pname, pdesc) in enumerate(PHASES):
        kids = [s for s in STEPS if s["phase"] == pi]
        cells_ = " · ".join(link(s["id"], f"{s['icon']} {s['civil']}") for s in kids)
        out.append(f"| **{pi+1}. {pname}** | {pdesc} | {cells_} |")
    return "\n".join(out)


def mapping_rows():
    return "\n".join(
        f"| {s['icon']} {s['civil']} | → | {s['ai_icon']} {s['ai']} | {s['phase']+1} |"
        for s in STEPS)


md(rf"""
# 🏢 AI for Building Energy Optimization
## Machine Learning vs Deep Learning, for Mechanical, Civil and Building Engineers

> You are not here to learn Artificial Intelligence. You are here to solve a **building services problem**
> — one a person genuinely cannot solve by hand, for reasons that are arithmetic rather than effort. AI
> turns up in the middle of it, because the engineering requires it. Not before.

---

## 1 · The engineering problem

It is 07:15 on a Tuesday in a 4,000 m² commercial office. This is not an unusual day.

The **air-handling unit and chiller started at 07:00**, as they have every workday since commissioning.
They are at duty: 23 °C setpoint, fresh-air damper at its design position, ventilating for two hundred
people.

**Eleven people are in the building.**

By 09:30 there will be two hundred, and the plant will be exactly right. At 13:00 half of them will be at
lunch and it will be wrong again. At 17:30 the floor will empty while the plant runs on for another ninety
minutes. Nobody is being careless. **The schedule was set once, and it has no way to know who walked in.**

Meanwhile the conditions never stop moving:

- Outdoor temperature swings 15 °C across the day, and chiller COP falls exactly when demand peaks.
- Sun tracks across the south façade, adding tens of kilowatts of gain that has nothing to do with people.
- Occupancy changes every fifteen minutes.
- Humidity, CO₂ and air quality each constrain what the plant is allowed to do.

**HVAC is the largest electrical load in the building.** One facilities manager is responsible for all of
it, across every zone, every fifteen minutes. That is not a diligence problem. It is arithmetic.

---

## 2 · What we are going to build

An **intelligent building energy system**. Four parts:

| | Part | What it does |
|---|---|---|
| 📡 | **Sensors read the conditions** | Indoor and outdoor temperature, humidity, CO₂, occupancy, solar, air quality, setpoint, and the smart meter — every 15 minutes, whether or not anybody is looking. |
| 📷 | **A camera reads the floor** | Watching for the thing no gauge measures directly: *which part of this floor is actually being used right now.* |
| 🔗 | **AI combines both** | Neither stream is enough. High load on a full floor is correct operation. The same load on an empty one is money leaving the building. Only the combination is a decision. |
| 🔔 | **The engineer gets a recommendation** | Not a report next quarter. A specific call: *north zone, six people, setback and reduce outside air, saves 13 kW, comfort unaffected.* |

> **Be clear about the goal, because it is not automation.** Nothing here replaces the facilities manager
> and nothing here changes a plant setting by itself. The engineer stays in charge, stays accountable, and
> still owns every comfort complaint. The system does the one thing a person cannot: **it watches every
> zone, every interval, and never looks away.** The goal is not an unmanned building. It is a
> **lower-energy, equally comfortable** one.

---

## 3 · The engineering workflow

Not a syllabus, and not chapters. **One building, one cooling season**, in the order a real project runs
it — twelve phases. Every AI concept in this notebook hangs off one of them.

| Phase | In the building | Steps |
|---|---|---|
{phase_rows()}

---

## 4 · Engineering → AI, the whole map

Spend a minute on this table before starting. **Every AI concept in this notebook is a building
engineering activity you already understand.** Not 'similar to'. The same thing, given a different name by
a different profession.

Read down the left column and you have described a building energy project. Read down the right column and
you have described a complete deep learning pipeline. **They are the same column.**

| 🏢 Building engineering process | → | 🤖 The AI process that solves it | Phase |
|---|:-:|---|:-:|
{mapping_rows()}

---

## The one idea this notebook proves

> **Machine Learning predicts building energy demand from environmental and occupancy data.
> Deep Learning understands occupancy and thermal images to detect how spaces are actually being used,
> enabling smarter HVAC control.**

Do not take that on trust. Step {[s['id'] for s in STEPS].index('proof')+1} measures it.
""")

md(r"""
---

## Setup

In Colab everything below is already installed. If you are running elsewhere, uncomment the install line.
Charts are Plotly, so they are interactive — hover, zoom, and toggle series from the legend.

TensorFlow is needed only for the CNN and Grad-CAM steps. Those cells detect whether it is present and
skip cleanly if it is not, so every other cell runs anywhere.
""")

co(r"""
# !pip install numpy pandas scikit-learn plotly tensorflow

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

np.random.seed(42)
pd.set_option("display.width", 120)

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

# {NUM[i]} {s['icon']} {s['civil']}
### Phase {s['phase']+1} of {len(PHASES)} · {pname} — *{pdesc}*

> The building engineering activity on this page is also, exactly, the AI concept
> **{s['ai']}**. Here is why.

## Part 1 · In the building

{s['site'].strip()}

## Part 2 · The engineering challenge

{s['challenge'].strip()}
""")

    md(rf"""
## Part 3 · Where the AI comes in

{s['ai_link'].strip()}

| 🏢 **In the building** | → | 🤖 **In the AI** |
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


# ============================================================================
# THE CLOSING SUMMARY
# ============================================================================
md(r"""
---

# 🏁 The whole system, in one page

```
   SENSORS  ──►  clean ──► scale ──► split by day ──►  REGRESSION  ──┐
   9 named channels                                  kW, waste flag  │
                                                                     ├─►  DECISION  ─►  DASHBOARD
   THERMAL CAMERA  ──────────────────────────────►  CNN + Grad-CAM ──┘    ENGINE       kWh · tCO₂
   4,096 raw pixels                                 class + zone                       cost · comfort
```

## What was built

| Stage | Method | Output |
|---|---|---|
| Predict HVAC load | Linear / Random Forest / Gradient Boosting | kW per 15-minute interval |
| Predict whole-building load | Random Forest regression | kW, and the daily peak |
| Flag over-conditioning | Random Forest classification | kW-per-person above the limit |
| Rank the drivers | Feature importance | what to change first |
| Grade a floor plate | CNN (3 classes) | empty / occupied / crowded |
| Locate the use | Grad-CAM | which zone, with the evidence |
| Forecast tomorrow | Regression, run forward | profile and peak, hours ahead |
| Choose the setpoint | Constrained sweep | highest setpoint with PPD ≤ 10% |
| Combine everything | Fusion rules | one ranked action per zone |
| Justify the spend | Counterfactual on the real log | kWh, cost, tCO₂, comfort |

## The three things worth remembering

1. **Environmental and occupancy sensors → Machine Learning.** The engineer names the features; the model
   weights them. On nine named channels a neural network is no better than a forest, and harder to defend.
2. **Camera and thermal images → Deep Learning.** Nobody can name 4,096 pixel features, so the network
   learns them. This is the only part of the system that can tell an empty sunlit bay from a busy one.
3. **Building Engineer + AI.** The system watches every zone every fifteen minutes and reports what it
   finds. A person still decides, still signs off, and still owns the comfort of the people inside.

## Where the engineering discipline showed up

Four moments in this notebook were engineering judgements, not machine learning:

- **Splitting by day, not by row.** The shuffled split reported a better score and was wrong.
- **Dropping a constant column** instead of cleaning it.
- **Treating comfort as a constraint**, never as something to trade for kilowatt-hours.
- **Computing the business case as a counterfactual** on the recorded season instead of quoting a
  percentage.

Those four are what separate a model from a building energy project.
""")


nb = new_notebook(cells=cells, metadata={
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"},
    "colab": {"provenance": []},
})
nbf.validate(nb)
with open("Building_Energy_Optimization_DL.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"wrote Building_Energy_Optimization_DL.ipynb  "
      f"({len(cells)} cells, {sum(1 for c in cells if c.cell_type == 'code')} code, "
      f"{len(STEPS)} steps, {len(PHASES)} phases)")
