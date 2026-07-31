"""
Builds Electricity_Load_Forecasting_AI.ipynb from nbformat cells.
Run:  py -3.13 build_nb.py

Modelled on the Building Energy / Smart Construction notebooks: one intro block
(problem -> what we build -> workflow -> Engineering-to-AI map), then N steps,
each rendered as the same five parts:

    header + Part 1 (power system engineering) + Part 2 (the challenge)
    Part 3 (where the AI comes in) + the bridge table + Part 4 header
    the code
    Part 5 (what you just built) + a one-line key takeaway

The notebook is standalone: it imports nothing from this file, and re-defines the
demand model inline.

APP: set this to the deployed Streamlit URL to switch on the per-step
"see it illustrated" links and the link column in the workflow table. Leave it as
"" and the notebook is built with no links at all, rather than dead ones.
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

APP = ""          # e.g. "https://load-forecasting.streamlit.app"

cells = []
def md(t):  cells.append(new_markdown_cell(t.strip("\n")))
def co(t):  cells.append(new_code_cell(t.strip("\n")))

def link(stage, label):
    return f"[{label}]({APP}/?stage={stage})" if APP else label


# ============================================================================
# THE PHASES  (one utility's forecasting project, in the order it is run)
# ============================================================================
PHASES = [
    ("The Grid At Work",        "One control room, one evening, and a balance that cannot slip."),
    ("One Hour Of Demand",      "A metered hour becomes a row somebody else has to trust."),
    ("Instrumenting The Network", "The SCADA and weather export lands, and gets checked."),
    ("Reading The Demand",      "Look at the load curve before modelling it."),
    ("Feature Engineering",     "Turn power system knowledge into columns."),
    ("The Forecast Gate",       "What is actually known at the moment the forecast is issued."),
    ("The Bar To Clear",        "A naive forecast is not zero. Beat it or go home."),
    ("The Forecasting Models",  "Four regressors on the same honest problem."),
    ("Reading The Model",       "What drives the forecast, and where it is biased."),
    ("The Forecast Audit",      "Every claim checked on weeks the model never saw."),
    ("The Operator's Desk",     "Change the conditions, watch the forecast move."),
    ("Despatch & The Business Case", "Reserve, fuel, and the cost of being wrong."),
]

NUM = ["①","②","③","④","⑤","⑥","⑦","⑧","⑨","⑩","⑪","⑫","⑬","⑭","⑮","⑯","⑰",
       "⑱","⑲","⑳","㉑","㉒","㉓","㉔","㉕","㉖","㉗","㉘","㉙","㉚","㉛","㉜","㉝"]


# ============================================================================
# THE STEPS
#   Each entry drives four cells. `body` is a list of ('md', text) / ('co', code)
#   items making up Part 4 — most steps have exactly one code cell.
# ============================================================================
STEPS = []
def step(**kw):
    STEPS.append(kw)


# ---------------------------------------------- PHASE 1 · THE GRID AT WORK
step(
    id="control-room", phase=0, icon="🏭", ai_icon="🤖",
    civil="A Monday Evening On The Grid", ai="Why Load Forecasting Exists",
    tech="One day of demand, and the ramp the generators have to follow",
    site="""A regional distribution utility. Roughly **1.2 million consumers**, a peak demand near
**1,180 MW**, and a control room staffed around the clock. Its job is one sentence long: **generation must
equal demand, every second of every day.** Not on average, not by the end of the month. Continuously.""",
    challenge="""Demand never holds still. It falls to about **480 MW** at four in the morning and reached
**1,181 MW** on the worst August evening of the last two years. Between five and seven in the evening it
can rise more than **60 MW in a single hour** — an entire mid-size generating unit, called for in sixty minutes. Large
thermal plant takes **six to twelve hours** to start. So the decision about what runs tomorrow evening is
taken *tonight*, before anybody knows what tomorrow's demand will be.""",
    ai_link="""That is the whole problem, and it is not a control problem — it is a **prediction** problem.
The operator does not need a faster switch. They need to know, tonight, what the demand will be at 19:00
tomorrow, closely enough to commit the right generators to it. Everything in this notebook exists to put a
number on that.""",
    bridge=[("Generation must equal demand", "A regression target in MW"),
            ("Demand moves every hour", "A time series, not a static table"),
            ("Units start hours ahead", "The forecast must run ahead of the need")],
    body=[("co", r'''
# ---- the utility, and the physics behind its demand ----------------------
# Every number here is a design assumption about the licence area. The dataset,
# the models and the business case later all follow from this one block.
BASE_MW   = 620.0    # MW   - the always-on floor: industry, water pumping, traction, losses
GROWTH    = 0.035    # /yr  - demand growth in the licence area
COOL_BASE = 24.0     # degC - cooling balance point: above this, air conditioning comes on
HEAT_BASE = 16.0     # degC - heating balance point: below this, heating comes on

def daily_shape(hour, weekend=False):
    """Fraction-of-base demand by hour of day.

    Two peaks, which is what most mixed residential/commercial networks look like:
    a morning rise as shops, offices and industry start, and a larger evening peak
    as households come home while commercial load has not yet gone. The deep trough
    is the small hours.
    """
    h = np.asarray(hour, float)
    morning = 0.14 * np.exp(-((h - 10.0) ** 2) / (2 * 3.2 ** 2))
    evening = 0.36 * np.exp(-((h - 19.5) ** 2) / (2 * 1.8 ** 2))
    night   = 0.15 * np.exp(-((h -  3.2) ** 2) / (2 * 2.8 ** 2))
    morning = np.where(weekend, morning * 0.45, morning)   # no shift start at the weekend
    return 0.86 + morning + evening - night

def cooling_mw(T, H):
    """Air-conditioning demand, MW.

    Two things matter and BOTH are non-linear:
      1. Demand rises with the SQUARE-ish of how far above the balance point it is,
         because more units switch on AND each runs a longer duty cycle.
      2. Humidity only matters when it is already hot - a humid 18 degC night calls
         for no cooling at all. That INTERACTION is the hardest part of the job.
    """
    cdd = np.clip(np.asarray(T, float) - COOL_BASE, 0, None)
    hum = 1.0 + 0.009 * np.clip(np.asarray(H, float) - 45.0, 0, None)
    return 5.4 * cdd ** 1.32 * hum

def heating_mw(T):
    "Resistive heating demand, MW. Milder and closer to linear than cooling."
    hdd = np.clip(HEAT_BASE - np.asarray(T, float), 0, None)
    return 3.6 * hdd ** 1.15

def daytype_factor(dayofweek, holiday=0):
    """How much of a normal weekday's load this calendar day draws.
    Saturday is a partial working day here; Sunday and holidays are not."""
    dow = np.asarray(dayofweek)
    f = np.where(dow == 6, 0.875, np.where(dow == 5, 0.945, 1.00))   # Sun / Sat / weekday
    return np.where(np.asarray(holiday) == 1, 0.845, f)

def demand_for(hour, T, H, dayofweek=0, holiday=0, years_in=0.0):
    "Total system demand, MW, for the given hour and conditions."
    shape = daily_shape(hour, np.asarray(dayofweek) >= 5)
    trend = (1 + GROWTH) ** np.asarray(years_in, float)
    return (BASE_MW * shape * daytype_factor(dayofweek, holiday) * trend
            + cooling_mw(T, H) * (0.80 + 0.20 * shape)
            + heating_mw(T))

# ---- two days a year apart, on the same axes -----------------------------
hours = np.arange(24)

# a hot August weekday: 32 degC at dawn, 43 degC mid-afternoon, humid
T_aug = 37.5 - 5.5 * np.cos(2 * np.pi * (hours - 4) / 24)
H_aug = np.full(24, 74.0)
d_aug = demand_for(hours, T_aug, H_aug)

# a cool January weekday: 11 degC at dawn, 22 degC mid-afternoon, dry
T_jan = 16.5 - 5.5 * np.cos(2 * np.pi * (hours - 4) / 24)
H_jan = np.full(24, 40.0)
d_jan = demand_for(hours, T_jan, H_jan)

fig = go.Figure()
fig.add_trace(go.Scatter(x=hours, y=d_aug, name="hot August weekday",
                         line=dict(color=RED, width=3)))
fig.add_trace(go.Scatter(x=hours, y=d_jan, name="cool January weekday",
                         line=dict(color=CYAN, width=3)))
fig.update_layout(title="One utility, two days — the load curve it has to follow",
                  xaxis_title="hour of day", yaxis_title="system demand (MW)",
                  template="plotly_white", height=420)
fig.show()

ramp = np.diff(d_aug)
print(f"August  peak {d_aug.max():6.0f} MW at {d_aug.argmax():02d}:00   "
      f"trough {d_aug.min():6.0f} MW at {d_aug.argmin():02d}:00")
print(f"January peak {d_jan.max():6.0f} MW at {d_jan.argmax():02d}:00   "
      f"trough {d_jan.min():6.0f} MW at {d_jan.argmin():02d}:00")
print(f"Steepest August ramp: {ramp.max():.0f} MW in the hour ending "
      f"{ramp.argmax()+1:02d}:00")
print(f"Peak-to-trough swing in August: {d_aug.max() - d_aug.min():.0f} MW "
      f"({d_aug.max()/d_aug.min():.2f}x)")
'''.strip("\n"))],
    built="""A demand model with the two things every load curve has: a **shape** set by the clock, and a
**weather-driven addition** on top of it. The same August hour and January hour differ by hundreds of
megawatts, and neither is unusual.""",
    takeaway="""Demand is a moving target set by the clock and the weather, and the generators that follow it
must be committed hours before it arrives.""",
)

step(
    id="enter-ai", phase=0, icon="👷", ai_icon="🛰️",
    civil="The Operator And The Forecast", ai="What AI Is Actually For Here",
    tech="8,760 hourly numbers a year, each needed before the hour arrives",
    site="""Nothing about the control room changes. The same operators, the same despatch instructions, the
same statutory responsibility for security of supply. What changes is that a demand number for **every
hour of tomorrow** is on the desk at 23:00 tonight, instead of being sketched from last week's figures.""",
    challenge="""The usual objection: is this here to replace the operator? No — and it is worth being precise
about why. A model sees demand, temperature and a calendar. It does not know a substation is on outage,
that a large steel consumer has scheduled a shutdown, or that a cyclone warning has been issued. It
cannot be held accountable when the lights go out. It produces **one number with an error bar**.""",
    ai_link="""So the split is fixed here and holds for the rest of the notebook: **the model forecasts, the
operator despatches.** The system's output is a recommendation with a stated accuracy. Every later design
choice — especially the audit and the reserve calculation — follows from that split.""",
    bridge=[("8,760 hours a year", "One prediction per hour"),
            ("Each needed hours ahead", "A forecast, not a measurement"),
            ("The operator signs the despatch", "The model recommends, never commits")],
    body=[("co", r'''
# The size of the task, stated plainly. This is the argument, not the arithmetic
# that follows - but the arithmetic is the argument.
HOURS_PER_YEAR = 365 * 24
print(f"Hourly demand values needed per year : {HOURS_PER_YEAR:,}")
print(f"Each one needed                      : the evening BEFORE the day it applies to")
print(f"Time to start a large thermal unit   : 6-12 hours")
print(f"Time an operator has to think        : none of it is spare")

print()
print("What the operator brings that the model cannot:")
for t in ["a substation on planned outage",
          "a large industrial consumer's shutdown notice",
          "a cyclone warning and the evacuation that follows",
          "statutory accountability for security of supply"]:
    print(f"   - {t}")

print()
print("What the model brings that the operator cannot:")
for t in ["8,760 forecasts a year, none of them skipped",
          "every driver weighted at once, consistently",
          "an error bar that can be turned into a reserve requirement"]:
    print(f"   - {t}")
'''.strip("\n"))],
    built="""No model yet — a definition of the job. The system produces a number and an honest accuracy.
A person decides what generation to commit against it.""",
    takeaway="""The forecast informs the despatch decision; the operator still makes it and still owns it.""",
)


# ---------------------------------------------- PHASE 2 · ONE HOUR OF DEMAND
step(
    id="one-hour", phase=1, icon="⏱️", ai_icon="🗄️",
    civil="One Hour, One Row", ai="Data Collection",
    tech="One metered hour -> one row of conditions + one demand value",
    site="""At the top of every hour the SCADA system records the system demand in megawatts. The weather
desk records temperature and relative humidity at the reference station. The calendar supplies the date,
the day of the week and whether it is a public holiday. That is one hour, closed and filed.""",
    challenge="""Whoever reads that row next year does not get the hour. Not the fact that it was the first
genuinely hot evening of the season, not the cricket final that kept the city indoors. They get eight
numbers. If the meter was reading low, or the temperature came from a station on the wrong side of the
city, nothing in the row says so.""",
    ai_link="""For a model that limitation is absolute. It never stands in the control room and cannot re-run
the hour. **One row — conditions in, demand out — is all it gets.** A wrong row produces a confident wrong
forecast with nothing to flag it. That is why the next three steps are entirely about the record.""",
    bridge=[("A metered hour", "One row of the dataset"),
            ("Temperature, humidity, clock", "The input features"),
            ("The demand in MW", "The regression target")],
    body=[("co", r'''
# The eight fields that describe one hour. Five of them are INPUTS the forecaster
# will know in advance; one is the TARGET it has to predict.
INPUTS = ["temperature_c", "humidity_pct", "hour", "dayofweek", "is_holiday"]
TARGET = "demand_mw"

# 2024-08-19 was a Monday. Take the 19:00 hour - the evening peak on a hot day.
h, T, H = 19, 38.4, 71.0
one_hour = pd.DataFrame([{
    "timestamp":     pd.Timestamp("2024-08-19 19:00"),
    "temperature_c": T,
    "humidity_pct":  H,
    "hour":          h,
    "dayofweek":     0,          # Monday
    "is_holiday":    0,
    "demand_mw":     round(float(demand_for(h, T, H, years_in=1.6)), 1),
}])

print("One hour, as the model receives it:")
display(one_hour)

print()
print("Where that demand came from:")
base = BASE_MW * daily_shape(h) * (1 + GROWTH) ** 1.6
cool = cooling_mw(T, H) * (0.80 + 0.20 * daily_shape(h))
heat = heating_mw(T)
print(f"   base load x evening shape : {base:7.1f} MW")
print(f"   air conditioning          : {cool:7.1f} MW   <- weather driven")
print(f"   heating                   : {heat:7.1f} MW")
print(f"   {'total':26s}: {base + cool + heat:7.1f} MW")
print()
print(f"The cooling term is {cool / (base + cool + heat) * 100:.0f}% of the demand in this "
      f"one hour, and it is the part that moves most between days.")
'''.strip("\n"))],
    built="""The unit of the whole dataset. Five inputs known ahead of time, one target measured afterwards —
and a decomposition showing which part of the demand the weather actually controls.""",
    takeaway="""The row is the model's entire hour; a wrong row gives a wrong forecast with nothing to flag it.""",
)

step(
    id="drivers", phase=1, icon="🔀", ai_icon="📐",
    civil="What Actually Moves Demand", ai="Feature Selection",
    tech="Sweep each driver across its real range, measure the megawatts it moves",
    site="""Before collecting two years of anything, decide what is worth collecting. A power system engineer
already knows the candidates: time of day, temperature, humidity, day of week, holidays, and the recent
history of the load itself. What is not obvious is their **relative size**.""",
    challenge="""Intuition ranks these badly. Everyone knows air conditioning matters; few would guess that on a
mild day the hour of the clock outweighs the temperature by a factor of three, or that humidity is worth
almost nothing until the temperature passes the balance point. Guessing wrong means instrumenting the
wrong thing for two years.""",
    ai_link="""So measure it. Hold everything at a reference condition, sweep one driver across its real
operating range, and record the megawatts it moves. This is a **sensitivity study** — the engineering
version of feature selection, done before a single model exists.""",
    bridge=[("Which drivers matter", "Which features to collect"),
            ("Sweep one, hold the rest", "One-at-a-time sensitivity"),
            ("Megawatts moved", "Expected feature importance")],
    body=[("co", r'''
# Reference condition: a Wednesday, 15:00, 30 degC, 55% RH - unremarkable.
REF = dict(hour=15, T=30.0, H=55.0, dow=2, holiday=0)

def d_at(**kw):
    p = {**REF, **kw}
    return float(demand_for(p["hour"], p["T"], p["H"], p["dow"], p["holiday"]))

sweeps = {
    "Hour of day (00 -> 19)":        (d_at(hour=0),           d_at(hour=19)),
    "Temperature (24 -> 42 degC)":   (d_at(T=24.0),           d_at(T=42.0)),
    "Humidity (35 -> 85 %) at 38C":  (d_at(T=38.0, H=35.0),   d_at(T=38.0, H=85.0)),
    "Humidity (35 -> 85 %) at 20C":  (d_at(T=20.0, H=35.0),   d_at(T=20.0, H=85.0)),
    "Weekday -> Sunday":             (d_at(),                 d_at(dow=6)),
    "Weekday -> public holiday":     (d_at(),                 d_at(holiday=1)),
}

names = list(sweeps)
spans = [abs(hi - lo) for lo, hi in sweeps.values()]
order = np.argsort(spans)

fig = go.Figure(go.Bar(
    x=[spans[i] for i in order], y=[names[i] for i in order], orientation="h",
    marker_color=[AMBER if "Humidity" in names[i] else CYAN for i in order],
    text=[f"{spans[i]:.0f} MW" for i in order], textposition="outside"))
fig.update_layout(title="How many megawatts each driver moves, across its real range",
                  xaxis_title="change in system demand (MW)", template="plotly_white",
                  height=420, margin=dict(l=220))
fig.show()

for i in reversed(order):
    print(f"{names[i]:32s} {spans[i]:6.1f} MW")
print()
print("Note the two humidity rows. The SAME humidity swing is worth "
      f"{spans[names.index('Humidity (35 -> 85 %) at 38C')]:.0f} MW on a hot day and "
      f"{spans[names.index('Humidity (35 -> 85 %) at 20C')]:.0f} MW on a mild one.")
print("A model that adds up its inputs independently cannot represent that. Hold on to it.")
'''.strip("\n"))],
    built="""A ranked list of demand drivers in megawatts, and the first sighting of the problem that decides
which model wins later: **humidity's effect depends on temperature.**""",
    takeaway="""Every driver is worth collecting, but they are not worth the same — and one of them only
matters in combination with another.""",
)


# ---------------------------------------------- PHASE 3 · INSTRUMENTING
step(
    id="load-data", phase=2, icon="🗂️", ai_icon="📥",
    civil="The SCADA Export Arrives", ai="Loading The Dataset",
    tech="Two years of hourly records, exactly as the historian exports them",
    site="""You ask the data team for the last two years. What arrives is a CSV: hourly system demand from
the SCADA historian, joined to hourly temperature and humidity from the weather desk, with the calendar
fields filled in. **17,544 rows**, one per hour, 2023 and 2024.""",
    challenge="""An export is not a dataset. Historians drop samples when a comms link fails, meters freeze and
repeat their last value, and a joined weather feed can arrive with duplicated timestamps after a clock
change. None of that announces itself in the file. The row count looks right, so it looks fine.""",
    ai_link="""A model trained on a broken export does not error. It trains happily, reports a good score, and
forecasts wrongly forever. **Loading is a commissioning check**: establish what actually arrived before
building anything on it.""",
    bridge=[("Two years of history", "17,544 labelled examples"),
            ("An export, not a dataset", "Nothing is trusted yet"),
            ("Check what arrived", "Shape, types, range")],
    body=[("co", r'''
# ---- generate the two-year history ---------------------------------------
# In a real project this is a CSV from the historian. Here it is generated from
# the demand model of step 1 so the notebook is standalone and reproducible.
HOLIDAYS = {"01-26", "03-08", "03-29", "04-14", "05-01", "08-15",
            "10-02", "10-24", "11-12", "11-13", "12-25"}

def make_history(seed=42, start="2023-01-01", years=2):
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, periods=years * 366 * 24, freq="h")
    idx = idx[idx.year < pd.Timestamp(start).year + years]
    n = len(idx)

    doy  = idx.dayofyear.to_numpy()
    hour = idx.hour.to_numpy().astype(float)
    dow  = idx.dayofweek.to_numpy()                     # Monday = 0
    holiday = np.isin(idx.strftime("%m-%d").to_numpy(), list(HOLIDAYS)).astype(int)

    # --- weather: a seasonal mean, a daily cycle, and a slow-moving anomaly.
    #     The anomaly is AR(1) - hot spells last several days, as they do in life.
    ndays = n // 24 + 1
    anom = np.zeros(ndays)
    for d in range(1, ndays):
        anom[d] = 0.76 * anom[d - 1] + rng.normal(0, 2.1)

    Tm = 27.0 + 9.0 * np.sin(2 * np.pi * (doy - 105) / 365.0)      # Jan ~18C, Jul ~36C
    T  = np.clip(Tm - 5.5 * np.cos(2 * np.pi * (hour - 4) / 24.0)
                 + anom[np.arange(n) // 24] + rng.normal(0, 0.6, n), 5.0, 48.0)

    Hm = 56.0 + 23.0 * np.sin(2 * np.pi * (doy - 150) / 365.0)     # monsoon peak in Aug
    H  = np.clip(Hm - 0.9 * (T - Tm) + rng.normal(0, 4.0, n), 18.0, 98.0)

    # --- demand, from the model of step 1
    weekend = dow >= 5
    yrs = (idx - idx[0]).days / 365.25
    load = demand_for(hour, T, H, dow, holiday, yrs)

    # --- measurement noise, autocorrelated: consecutive hours err together
    e = np.zeros(n)
    for t in range(1, n):
        e[t] = 0.72 * e[t - 1] + rng.normal(0, 7.5)

    return pd.DataFrame({
        "timestamp": idx, "demand_mw": (load + e).round(1),
        "temperature_c": T.round(1), "humidity_pct": H.round(1),
        "hour": hour.astype(int), "dayofweek": dow, "month": idx.month,
        "is_weekend": weekend.astype(int), "is_holiday": holiday,
    })

def damage_export(df, seed=7):
    """What the historian actually hands over. Four faults, all realistic,
    none of them announced anywhere in the file."""
    rng = np.random.default_rng(seed)
    d = df.copy()
    n = len(d)

    # 1. comms dropouts: isolated missing demand samples
    d.loc[rng.choice(n, 180, replace=False), "demand_mw"] = np.nan
    # 2. a weather station offline for three days in May 2024
    off = (d.timestamp >= "2024-05-12") & (d.timestamp < "2024-05-15")
    d.loc[off, ["temperature_c", "humidity_pct"]] = np.nan
    # 3. a frozen meter: 14 hours repeating the same value
    fz = d.index[(d.timestamp >= "2023-11-06 08:00") & (d.timestamp < "2023-11-06 22:00")]
    d.loc[fz, "demand_mw"] = d.loc[fz[0], "demand_mw"]
    # 4. telemetry spikes: impossible readings the RTU let through
    d.loc[rng.choice(n, 9, replace=False), "demand_mw"] = 9999.0
    # 5. duplicated rows from a re-run of the export job
    d = pd.concat([d, d.sample(24, random_state=3)], ignore_index=True)
    return d.sort_values("timestamp").reset_index(drop=True)

raw = damage_export(make_history())

print(f"rows      : {len(raw):,}")
print(f"columns   : {raw.shape[1]}")
print(f"period    : {raw.timestamp.min()}  ->  {raw.timestamp.max()}")
print(f"expected  : {int((raw.timestamp.max() - raw.timestamp.min()).total_seconds() // 3600) + 1:,} hourly rows")
print()
display(raw.head(6))
print()
print(raw.dtypes.to_string())
'''.strip("\n"))],
    built="""The export, loaded and described — and a first discrepancy already visible: the file has more rows
than there are hours in the period it covers.""",
    takeaway="""A plausible-looking export is not a verified one; the row count is the first thing that lies.""",
)

step(
    id="inspect", phase=2, icon="🔎", ai_icon="🩺",
    civil="Finding The Bad Readings", ai="Data Inspection",
    tech="Missing counts, repeated values, impossible magnitudes, duplicate timestamps",
    site="""Before anything is repaired, find out what is wrong. In a metering context that means four
specific checks: **dropouts** (samples the historian never received), **frozen channels** (a meter
repeating its last good value), **out-of-range values** (an RTU passing through a fault code), and
**duplicate timestamps** (an export job that ran twice).""",
    challenge="""You cannot eyeball 17,568 rows. And each fault hides differently: a dropout is a gap, a frozen
meter is a perfectly plausible number repeated, and a duplicate timestamp is invisible unless you
specifically look for it. A frozen meter is the dangerous one — every individual value passes any range
check you could write.""",
    ai_link="""So each fault needs its own detector. This step **diagnoses only** — nothing is repaired here.
Separating diagnosis from repair is what stops you quietly deleting a real demand event because it looked
inconvenient.""",
    bridge=[("Dropouts and frozen meters", "Missing and constant values"),
            ("An RTU fault code", "An out-of-range outlier"),
            ("An export run twice", "Duplicate index entries")],
    body=[("co", r'''
print("--- 1. missing values per column ---")
miss = raw.isna().sum()
print(miss[miss > 0].to_string())

print()
print("--- 2. duplicate timestamps ---")
dups = raw.timestamp.duplicated().sum()
print(f"{dups} duplicated timestamps")

print()
print("--- 3. impossible magnitudes ---")
hi = raw[raw.demand_mw > 2000]
print(f"{len(hi)} readings above 2,000 MW (the network cannot deliver that)")
print(f"    values seen: {sorted(hi.demand_mw.unique())}")

print()
print("--- 4. frozen meter: the longest run of identical consecutive values ---")
s = raw.demand_mw
runs = (s != s.shift()).cumsum()
longest = s.groupby(runs).size()
k = longest.idxmax()
block = raw[runs == k]
print(f"longest run = {longest.max()} consecutive hours at {block.demand_mw.iloc[0]:.1f} MW")
print(f"    from {block.timestamp.iloc[0]}  to  {block.timestamp.iloc[-1]}")
print("    every one of those values would pass a range check. That is what makes it dangerous.")

# ---- show the three-day weather outage and the frozen meter ---------------
fig = make_subplots(rows=2, cols=1, shared_xaxes=False, vertical_spacing=0.18,
                    subplot_titles=("A frozen demand meter — 2023-11-06",
                                    "The weather station offline — May 2024"))
w1 = raw[(raw.timestamp >= "2023-11-05") & (raw.timestamp < "2023-11-08")]
fig.add_trace(go.Scatter(x=w1.timestamp, y=w1.demand_mw, line=dict(color=RED, width=2),
                         name="demand (MW)"), row=1, col=1)
w2 = raw[(raw.timestamp >= "2024-05-09") & (raw.timestamp < "2024-05-18")]
fig.add_trace(go.Scatter(x=w2.timestamp, y=w2.temperature_c, line=dict(color=AMBER, width=2),
                         name="temperature (degC)"), row=2, col=1)
fig.update_layout(height=560, template="plotly_white", showlegend=False,
                  title="Two faults you would never find by scrolling the file")
fig.show()
'''.strip("\n"))],
    built="""Four detectors, four findings: **180 dropouts**, a **72-hour weather outage**, a **frozen meter**,
**9 fault-code spikes** and **24 duplicated rows**. Diagnosis complete; nothing repaired yet.""",
    takeaway="""The frozen meter is the one that matters — every value it reports is individually plausible.""",
)

step(
    id="clean", phase=2, icon="🧹", ai_icon="🛠️",
    civil="Repairing The Record", ai="Data Cleaning",
    tech="Drop duplicates, void the faults, interpolate in TIME — not with a median",
    site="""Now repair, and the choices are engineering judgements. Duplicated rows are dropped outright.
Fault-code spikes and the frozen block are **voided** — marked missing, because a wrong number is worse
than no number. Then the gaps are filled.""",
    challenge="""How you fill them matters more than it looks. The reflex from tabular work is to fill with the
column median. For a load time series that is **wrong**: the median of the whole year is about 640 MW, so
a gap at 03:00 gets filled with a value 170 MW above what the network was actually drawing. You would be
teaching the model that four in the morning is a busy hour.""",
    ai_link="""A time series must be filled **along time**, not from the column as a whole. Linear interpolation
between the surrounding hours respects the load curve, because demand at 03:00 genuinely is close to the
average of 02:00 and 04:00. Long gaps get a different treatment — you cannot interpolate across a
three-day outage, so those hours are dropped.""",
    bridge=[("A wrong number beats no number? No", "Void, then fill"),
            ("The load curve is continuous", "Interpolate along time"),
            ("A three-day outage", "Too long to fill — drop it")],
    body=[("co", r'''
clean = raw.drop_duplicates(subset="timestamp", keep="first").copy()
print(f"dropped {len(raw) - len(clean)} duplicated timestamps -> {len(clean):,} rows")

# --- void the faults (do not repair a value you know is wrong) -------------
clean.loc[clean.demand_mw > 2000, "demand_mw"] = np.nan

s = clean.demand_mw
runs = (s != s.shift()).cumsum()
sizes = clean.groupby(runs).demand_mw.transform("size")
frozen = sizes >= 6                      # 6+ identical consecutive hours is not real demand
clean.loc[frozen, "demand_mw"] = np.nan
print(f"voided {int(frozen.sum())} frozen-meter hours and 9 fault-code spikes")

# --- why the median fill would be wrong, in one number ---------------------
med = clean.demand_mw.median()
at3 = clean[clean.hour == 3].demand_mw.median()
print(f"\ncolumn median = {med:.0f} MW, but the median 03:00 demand is {at3:.0f} MW "
      f"— a median fill would be {med - at3:.0f} MW too high at night.")

# --- fill along TIME ------------------------------------------------------
clean = clean.set_index("timestamp").sort_index()
clean = clean.asfreq("h")                                # expose any missing hours
for c in ["demand_mw", "temperature_c", "humidity_pct"]:
    clean[c] = clean[c].interpolate(method="time", limit=6)   # up to 6 h only

before = len(clean)
clean = clean.dropna(subset=["demand_mw", "temperature_c", "humidity_pct"])
print(f"dropped {before - len(clean)} hours inside gaps too long to interpolate "
      f"(the May 2024 weather outage)")

# calendar columns are never missing - rebuild them from the index to be sure
clean["hour"] = clean.index.hour
clean["dayofweek"] = clean.index.dayofweek
clean["month"] = clean.index.month
clean["is_weekend"] = (clean.index.dayofweek >= 5).astype(int)
clean["is_holiday"] = np.isin(clean.index.strftime("%m-%d").to_numpy(),
                              list(HOLIDAYS)).astype(int)
clean = clean.reset_index()

print(f"\nclean dataset: {len(clean):,} hours, {clean.isna().sum().sum()} missing values")
print(f"demand range : {clean.demand_mw.min():.0f} - {clean.demand_mw.max():.0f} MW")
display(clean.head(4))
'''.strip("\n"))],
    built="""A continuous hourly record with no duplicates, no fault codes, no frozen block and no gaps —
repaired **along the time axis**, which is the only way a load series can be repaired.""",
    takeaway="""Fill a time series along time; a column median would have taught the model that 03:00 is busy.""",
)


# ---------------------------------------------- PHASE 4 · READING THE DEMAND
step(
    id="profile", phase=3, icon="📈", ai_icon="🔍",
    civil="The Daily Load Curve", ai="Exploratory Data Analysis",
    tech="Mean demand by hour and day type, and the load duration curve",
    site="""The load curve is the most-looked-at chart in any control room. Average the demand by hour of
day and the network's routine appears: the overnight trough, the morning rise, the midday plateau, the
evening peak. Split it by day type and three distinct curves appear where there seemed to be one.""",
    challenge="""Averages hide the thing planners actually care about — the **extremes**. The system has to be
built for the highest hour of the year, not the average one, and that hour is expensive: plant that runs
for a few dozen hours a year still has to be paid for all year. A mean load curve says nothing about how
often the peak is approached.""",
    ai_link="""So look at the data two ways before modelling it. The **load curve** shows the routine a model
must reproduce. The **load duration curve** — every hour of the year sorted from highest to lowest —
shows how much of the year the expensive top end is actually needed. Together they tell you what the
forecast has to get right, and where being wrong costs most.""",
    bridge=[("The daily load curve", "The pattern the model must learn"),
            ("Weekday vs Saturday vs Sunday", "A categorical driver worth encoding"),
            ("The load duration curve", "Where forecast error is expensive")],
    body=[("co", r'''
# ---- 1. the load curve, by day type --------------------------------------
wk  = clean[clean.dayofweek < 5].groupby("hour").demand_mw.mean()
sat = clean[clean.dayofweek == 5].groupby("hour").demand_mw.mean()
sun = clean[clean.dayofweek == 6].groupby("hour").demand_mw.mean()

fig = go.Figure()
for series, name, col in [(wk, "Mon-Fri", CYAN), (sat, "Saturday", AMBER),
                          (sun, "Sunday", GREEN)]:
    fig.add_trace(go.Scatter(x=series.index, y=series.values, name=name,
                             line=dict(color=col, width=3)))
fig.update_layout(title="Average load curve by day type — two years of history",
                  xaxis_title="hour of day", yaxis_title="mean demand (MW)",
                  template="plotly_white", height=420)
fig.show()

print(f"Weekday evening peak : {wk.max():.0f} MW at {wk.idxmax():02d}:00")
print(f"Sunday evening peak  : {sun.max():.0f} MW at {sun.idxmax():02d}:00  "
      f"({(1 - sun.max()/wk.max())*100:.0f}% below the weekday peak)")
print(f"Overnight trough     : {wk.min():.0f} MW at {wk.idxmin():02d}:00")

# ---- 2. hour x month, as a heatmap ---------------------------------------
piv = clean.pivot_table(index="hour", columns="month", values="demand_mw", aggfunc="mean")
fig = go.Figure(go.Heatmap(z=piv.values, x=piv.columns, y=piv.index, colorscale="Turbo",
                           colorbar=dict(title="MW")))
fig.update_layout(title="Mean demand by hour and month — the summer evening block is the problem",
                  xaxis_title="month", yaxis_title="hour of day",
                  template="plotly_white", height=460)
fig.show()

# ---- 3. the load duration curve ------------------------------------------
ldc = np.sort(clean.demand_mw.values)[::-1]
pct = np.arange(1, len(ldc) + 1) / len(ldc) * 100

fig = go.Figure(go.Scatter(x=pct, y=ldc, line=dict(color=CYAN, width=3), name="demand"))
fig.add_hline(y=ldc[0], line=dict(color=RED, dash="dash"),
              annotation_text=f"system peak {ldc[0]:.0f} MW")
fig.add_hline(y=ldc.mean(), line=dict(color=MUTED, dash="dot"),
              annotation_text=f"mean {ldc.mean():.0f} MW")
fig.update_layout(title="Load duration curve — every hour of two years, sorted highest to lowest",
                  xaxis_title="% of hours at or above this demand",
                  yaxis_title="demand (MW)", template="plotly_white", height=420)
fig.show()

top1 = int(len(ldc) * 0.01)
print(f"\nSystem peak            : {ldc[0]:.0f} MW")
print(f"Mean demand            : {ldc.mean():.0f} MW")
print(f"Load factor (mean/peak): {ldc.mean()/ldc[0]:.3f}")
print(f"Demand exceeded in only the top 1% of hours ({top1} h/2yr): {ldc[top1]:.0f} MW")
print(f"So {ldc[0]-ldc[top1]:.0f} MW of capacity exists for about {top1/2:.0f} hours a year.")
'''.strip("\n"))],
    built="""Three views of the same two years: the load curve the model has to reproduce, the seasonal block
where demand is highest, and the duration curve showing how few hours the top of the system is needed
for.""",
    takeaway="""The average hour is easy and cheap; the notebook exists for the few hundred hours near the peak.""",
)

step(
    id="weather-link", phase=3, icon="🌡️", ai_icon="📉",
    civil="Demand Against Temperature", ai="Non-Linearity And Interaction",
    tech="Demand vs temperature, and the humidity effect inside temperature bands",
    site="""Plot demand against temperature and the classic shape appears: a **V**, or in a hot climate a
hockey stick. Demand falls as temperature rises to the comfort zone, flattens through it, then climbs
steeply as air conditioning comes on. The two bends are the **balance points** — the temperatures at
which heating and cooling start.""",
    challenge="""Two things about this shape defeat a simple model. First it is **not a straight line** — the
slope above the cooling balance point is far steeper than below it, and it steepens further as the
temperature climbs. Second, the effect of humidity is **not separable**: on a 38 °C evening a humidity
swing is worth tens of megawatts, and on a 20 °C evening it is worth almost nothing.""",
    ai_link="""That second property is called an **interaction**, and it decides which model wins later. A model
that adds up its inputs independently — like linear regression — can represent 'hotter means more' and
'more humid means more', but it cannot represent 'more humid means more *only when it is already hot*'.
Tree-based models can, because a tree can split on temperature first and then on humidity.""",
    bridge=[("The V-shaped demand curve", "A non-linear response"),
            ("Heating and cooling balance points", "Where the slope changes"),
            ("Humidity only matters when hot", "A feature interaction")],
    body=[("co", r'''
# ---- 1. the V, coloured by hour of day -----------------------------------
s = clean.sample(4000, random_state=1)
fig = go.Figure(go.Scattergl(
    x=s.temperature_c, y=s.demand_mw, mode="markers",
    marker=dict(size=4, color=s.hour, colorscale="Twilight",
                colorbar=dict(title="hour")),
    hoverinfo="skip"))

# the binned mean makes the two balance points obvious
bins = np.arange(5, 49, 1.0)
mids = bins[:-1] + 0.5
bm = clean.groupby(pd.cut(clean.temperature_c, bins), observed=True).demand_mw.mean()
fig.add_trace(go.Scatter(x=mids[:len(bm)], y=bm.values, mode="lines+markers",
                         line=dict(color=RED, width=4), name="mean demand"))
fig.add_vline(x=HEAT_BASE, line=dict(color=MUTED, dash="dash"),
              annotation_text=f"heating balance {HEAT_BASE:.0f}C")
fig.add_vline(x=COOL_BASE, line=dict(color=MUTED, dash="dash"),
              annotation_text=f"cooling balance {COOL_BASE:.0f}C")
fig.update_layout(title="System demand vs temperature — the V, and its two balance points",
                  xaxis_title="temperature (degC)", yaxis_title="demand (MW)",
                  template="plotly_white", height=440, showlegend=False)
fig.show()

# ---- 2. the interaction, stated numerically ------------------------------
# NOTE the control. Humidity and temperature move in opposite directions across
# a day, so humid hours are disproportionately NIGHT hours - which have low
# demand for reasons that have nothing to do with humidity. Comparing raw
# humidity against demand would therefore show humidity REDUCING demand.
# Restricting to the evening peak window holds the clock roughly fixed, so what
# is left is the weather effect.
ev = clean[(clean.hour >= 17) & (clean.hour <= 21) & (clean.is_weekend == 0)]
print(f"Effect of humidity INSIDE each temperature band")
print(f"(evening peak hours 17:00-21:00, weekdays only, so the clock is held fixed)\n")
print(f"{'temperature band':>18s} {'hours':>7s} {'low RH':>9s} {'high RH':>9s} {'difference':>11s}")
for lo, hi in [(10, 18), (18, 24), (24, 30), (30, 36), (36, 48)]:
    b = ev[(ev.temperature_c >= lo) & (ev.temperature_c < hi)]
    if len(b) < 50:
        continue
    q1, q3 = b.humidity_pct.quantile([0.25, 0.75])
    lo_rh = b[b.humidity_pct <= q1].demand_mw.mean()
    hi_rh = b[b.humidity_pct >= q3].demand_mw.mean()
    print(f"{f'{lo}-{hi} degC':>18s} {len(b):7,d} {lo_rh:8.0f}MW {hi_rh:8.0f}MW "
          f"{hi_rh - lo_rh:+10.0f}MW")

print()
print("The same humidity swing is worth very different megawatts depending on the")
print("temperature band it happens in. That is an INTERACTION, and it is the")
print("clearest single reason the tree models beat linear regression later.")
print()
print("The control matters. Without restricting to a fixed window, humid hours are")
print("mostly night hours and the table would show humidity LOWERING demand - a")
print("textbook confound, and one that would have quietly reversed the conclusion.")
'''.strip("\n"))],
    built="""The demand–temperature relationship, with both balance points visible, and a numerical
demonstration that humidity's effect depends entirely on the temperature band it occurs in.""",
    takeaway="""Demand responds to temperature non-linearly, and to humidity only in combination with it.""",
)

step(
    id="calendar-link", phase=3, icon="📅", ai_icon="🏷️",
    civil="Working Days, Weekends, Holidays", ai="Categorical Drivers",
    tech="Demand by day type, and one average week hour by hour",
    site="""The calendar moves demand as reliably as the weather. Offices, schools, workshops and industrial
consumers follow a working week; households do not. A public holiday empties the commercial and
industrial load while leaving residential load largely intact — which is why a holiday looks like a
Sunday, not like a quiet weekday.""",
    challenge="""These are **categories, not quantities**. 'Sunday' is not seven times 'Monday'. Encoding day of
week as the number 0–6 invites a model to treat Wednesday as halfway between Monday and Friday, which
happens to be roughly true, and Sunday as six times Monday, which is nonsense. Holidays are rarer still —
about eleven days a year — so a model sees very few examples.""",
    ai_link="""The fix is to hand the model the distinction directly rather than hoping it infers it: an
explicit **`is_weekend` flag**, an explicit **`is_holiday` flag**, and day of week alongside. Naming the
category is engineering knowledge the model would otherwise have to rediscover from very few examples.""",
    bridge=[("Working day vs holiday", "A categorical feature"),
            ("Eleven holidays a year", "A rare class, explicitly flagged"),
            ("The weekly rhythm", "Day-of-week as a driver")],
    body=[("co", r'''
# ---- demand by day type --------------------------------------------------
def day_type(r):
    if r.is_holiday:      return "Public holiday"
    if r.dayofweek == 6:  return "Sunday"
    if r.dayofweek == 5:  return "Saturday"
    return "Mon-Fri"

clean["day_type"] = clean.apply(day_type, axis=1)
ORDER = ["Mon-Fri", "Saturday", "Sunday", "Public holiday"]

fig = go.Figure()
for dt, col in zip(ORDER, [CYAN, AMBER, GREEN, RED]):
    v = clean[clean.day_type == dt].demand_mw
    fig.add_trace(go.Box(y=v, name=dt, marker_color=col, boxmean=True))
fig.update_layout(title="Demand distribution by day type",
                  yaxis_title="demand (MW)", template="plotly_white",
                  height=420, showlegend=False)
fig.show()

base = clean[clean.day_type == "Mon-Fri"].demand_mw.mean()
print(f"{'day type':>16s} {'hours':>8s} {'mean MW':>9s} {'vs weekday':>11s}")
for dt in ORDER:
    v = clean[clean.day_type == dt].demand_mw
    print(f"{dt:>16s} {len(v):8,d} {v.mean():9.0f} {(v.mean()/base - 1)*100:+10.1f}%")

# ---- one average week, hour by hour --------------------------------------
clean["week_hour"] = clean.dayofweek * 24 + clean.hour
wkprof = clean[clean.is_holiday == 0].groupby("week_hour").demand_mw.mean()

fig = go.Figure(go.Scatter(x=wkprof.index, y=wkprof.values,
                           line=dict(color=CYAN, width=2.5)))
for dnum, dname in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
    fig.add_vline(x=dnum * 24, line=dict(color="#dddddd", width=1))
    fig.add_annotation(x=dnum * 24 + 12, y=wkprof.max() * 1.02, text=dname,
                       showarrow=False, font=dict(size=11, color=MUTED))
fig.update_layout(title="One average week — the pattern a forecast has to reproduce",
                  xaxis_title="hour of week", yaxis_title="mean demand (MW)",
                  template="plotly_white", height=400)
fig.show()

print(f"\nA holiday runs {(clean[clean.day_type=='Public holiday'].demand_mw.mean()/base - 1)*100:.1f}% "
      f"below a weekday — closer to a Sunday than to a working day.")
print(f"Holidays are {clean.is_holiday.sum():,} hours out of {len(clean):,} "
      f"({clean.is_holiday.mean()*100:.1f}%). The model sees very few of them.")
'''.strip("\n"))],
    built="""The calendar effect, quantified: Saturdays, Sundays and holidays each sit at a different level,
and holidays are rare enough that the model needs to be told about them rather than left to infer them.""",
    takeaway="""Day type is a category with real megawatts attached, and the rarest category matters most.""",
)


# ---------------------------------------------- PHASE 5 · FEATURE ENGINEERING
step(
    id="cyclical", phase=4, icon="🕐", ai_icon="🔄",
    civil="Midnight Is Next To 23:00", ai="Cyclical Encoding",
    tech="Map the hour onto a circle: hour_sin and hour_cos",
    site="""Hour of day is written 0 to 23, and that numbering has a defect every engineer notices and most
models do not: **23:00 and 00:00 are one hour apart, but the numbers are 23 apart.** The same is true of
December and January. The clock is a circle; the integer is a line.""",
    challenge="""Left alone, this distorts the overnight demand ramp. A model reading hour as a plain number
believes the jump from 23:00 to 00:00 is the largest time gap in the day, when it is actually the
smallest. Every hour near midnight — the trough the system passes through every single night — is
modelled on a false premise.""",
    ai_link="""The standard fix is to put the hour back on the circle it came from. Represent each hour by its
**position on a clock face**: `hour_sin` and `hour_cos`. Two numbers instead of one, and now 23:00 and
00:00 sit next to each other, exactly as they do in time. The same encoding is applied to the month.""",
    bridge=[("The clock is a circle", "Sine and cosine of the hour"),
            ("23:00 is next to 00:00", "Adjacent in feature space"),
            ("The seasonal cycle", "The same encoding for month")],
    body=[("co", r'''
feat = clean.copy()
feat["hour_sin"]  = np.sin(2 * np.pi * feat.hour / 24)
feat["hour_cos"]  = np.cos(2 * np.pi * feat.hour / 24)
feat["month_sin"] = np.sin(2 * np.pi * feat.month / 12)
feat["month_cos"] = np.cos(2 * np.pi * feat.month / 12)

# ---- the defect, and the repair, in one comparison -----------------------
def raw_gap(a, b):    return abs(a - b)
def circ_gap(a, b):
    return float(np.hypot(np.sin(2*np.pi*a/24) - np.sin(2*np.pi*b/24),
                          np.cos(2*np.pi*a/24) - np.cos(2*np.pi*b/24)))

print(f"{'hours':>14s} {'plain integer':>15s} {'on the clock face':>19s}")
for a, b in [(23, 0), (11, 12), (6, 18), (2, 3)]:
    print(f"{f'{a:02d}:00 -> {b:02d}:00':>14s} {raw_gap(a,b):15.2f} {circ_gap(a,b):19.2f}")
print()
print("Read the first row. As a plain integer, 23:00 and midnight are the FURTHEST")
print("apart of any two hours in the day. On the clock face they are the closest,")
print("which is what they actually are.")

# ---- the clock face, with mean demand ------------------------------------
hm = clean.groupby("hour").demand_mw.mean()
ang = 2 * np.pi * hm.index / 24
fig = go.Figure(go.Scatter(
    x=np.sin(ang), y=np.cos(ang), mode="markers+text",
    text=[f"{h:02d}" for h in hm.index], textposition="top center",
    marker=dict(size=np.interp(hm.values, (hm.min(), hm.max()), (9, 30)),
                color=hm.values, colorscale="Turbo", colorbar=dict(title="mean MW"))))
fig.update_layout(title="The 24 hours placed on a circle — marker size and colour are mean demand",
                  template="plotly_white", height=520,
                  xaxis=dict(title="hour_sin", scaleanchor="y", zeroline=True),
                  yaxis=dict(title="hour_cos", zeroline=True))
fig.show()
'''.strip("\n"))],
    built="""Four new columns that place the hour and the month back on the circles they belong to, so the
overnight trough and the December–January boundary stop being artificial cliffs.""",
    takeaway="""Encode a cycle as a cycle, or the model will believe midnight is the far side of the day.""",
)

step(
    id="degree-hours", phase=4, icon="🌡️", ai_icon="🧮",
    civil="Cooling And Heating Degree Hours", ai="Domain Feature Engineering",
    tech="cdd = max(T - 24, 0) and hdd = max(16 - T, 0)",
    site="""Energy engineers do not usually correlate demand with raw temperature. They use **degree hours**:
how far the temperature sits above the cooling balance point, or below the heating one, and for how long.
It is the standard unit of weather-driven energy demand and it appears in every utility's planning
documents.""",
    challenge="""Raw temperature carries the wrong message below the balance point. Between 16 °C and 24 °C
neither heating nor cooling runs, so a change in temperature there moves almost no demand at all — yet
the raw number keeps changing, telling the model that something is happening when nothing is.""",
    ai_link="""So compute what the engineer would compute. **`cdd = max(T − 24, 0)`** is zero all through the
comfort band and rises only when cooling actually starts. **`hdd = max(16 − T, 0)`** does the same for
heating. This is **domain feature engineering** — encoding a known physical threshold so the model does
not have to discover it from data.""",
    bridge=[("Cooling degree hours", "A rectified, thresholded feature"),
            ("The comfort band", "A region where the feature is zero"),
            ("A known balance point", "Physics handed to the model")],
    body=[("co", r'''
feat["cdd"] = np.clip(feat.temperature_c - COOL_BASE, 0, None)   # cooling degree hours
feat["hdd"] = np.clip(HEAT_BASE - feat.temperature_c, 0, None)   # heating degree hours

fig = make_subplots(rows=1, cols=2, subplot_titles=(
    "Raw temperature: a straight line fits badly",
    "Cooling degree hours: the comfort band collapses to zero"))

bins = np.arange(5, 49, 1.0)
bm = clean.groupby(pd.cut(clean.temperature_c, bins), observed=True).demand_mw.mean()
fig.add_trace(go.Scatter(x=bins[:len(bm)] + 0.5, y=bm.values, mode="markers",
                         marker=dict(color=CYAN, size=8)), row=1, col=1)

cb = np.arange(0, 25, 1.0)
cm = feat.groupby(pd.cut(feat.cdd, cb), observed=True).demand_mw.mean()
fig.add_trace(go.Scatter(x=cb[:len(cm)] + 0.5, y=cm.values, mode="markers",
                         marker=dict(color=AMBER, size=8)), row=1, col=2)

fig.update_xaxes(title_text="temperature (degC)", row=1, col=1)
fig.update_xaxes(title_text="cooling degree hours (degC above 24)", row=1, col=2)
fig.update_yaxes(title_text="mean demand (MW)", row=1, col=1)
fig.update_layout(template="plotly_white", height=420, showlegend=False)
fig.show()

r_raw = np.corrcoef(clean.temperature_c, clean.demand_mw)[0, 1]
r_cdd = np.corrcoef(feat.cdd, feat.demand_mw)[0, 1]
print(f"correlation of demand with raw temperature  : {r_raw:+.3f}")
print(f"correlation of demand with cooling degree hrs: {r_cdd:+.3f}")
print()
print(f"Hours inside the comfort band ({HEAT_BASE:.0f}-{COOL_BASE:.0f} degC), where both features are zero: "
      f"{int(((feat.cdd == 0) & (feat.hdd == 0)).sum()):,} "
      f"({((feat.cdd == 0) & (feat.hdd == 0)).mean()*100:.0f}% of all hours)")
'''.strip("\n"))],
    built="""Two features carrying a physical threshold the model would otherwise have to infer, and a measured
improvement in how tightly demand tracks the weather variable.""",
    takeaway="""Give the model the balance point rather than making it rediscover the laws of your own field.""",
)

step(
    id="lags", phase=4, icon="🔁", ai_icon="⏮️",
    civil="Demand Remembers Itself", ai="Lag And Rolling Features",
    tech="lag_1, lag_24, lag_48, lag_168 and the previous day's mean and peak",
    site="""Today's load curve looks a great deal like yesterday's. The same consumers, the same shift
patterns, the same appliances. Ask any control engineer for tomorrow's 19:00 demand with no tools and
they will tell you today's 19:00 figure, adjusted a little — and they will be closer than you expect.""",
    challenge="""That knowledge is not in the dataset. The calendar and weather columns describe the
*conditions* of an hour; nothing tells the model what the system was actually drawing recently. And the
recent level carries everything the weather columns cannot: an industrial consumer's new plant, a
tariff change, a festival week, load growth.""",
    ai_link="""So put the history in as columns. A **lag feature** is simply the demand *n* hours ago:
`lag_24` is the same hour yesterday, `lag_168` the same hour last week. A **rolling feature** summarises a
window — the previous day's mean and peak. This is what turns a table of conditions into a **time-series
forecasting** problem.""",
    bridge=[("Today looks like yesterday", "lag_24 as a feature"),
            ("Last Monday looks like this Monday", "lag_168 as a feature"),
            ("The recent level of the system", "Rolling mean and max")],
    body=[("co", r'''
# ---- how far back does demand remember itself? ---------------------------
acf = [feat.demand_mw.autocorr(lag=k) for k in range(1, 193)]
fig = go.Figure(go.Bar(x=list(range(1, 193)), y=acf, marker_color=CYAN))
for L, lab in [(24, "1 day"), (48, "2 days"), (168, "1 week")]:
    fig.add_vline(x=L, line=dict(color=RED, dash="dash"),
                  annotation_text=lab, annotation_position="top")
fig.update_layout(title="Autocorrelation of system demand — how much an hour tells you about a later one",
                  xaxis_title="lag (hours)", yaxis_title="correlation",
                  template="plotly_white", height=420)
fig.show()

for L in (1, 24, 48, 168):
    print(f"correlation with demand {L:3d} hours earlier : {acf[L-1]:+.3f}")
print()
print("The spikes at 24, 48 and 168 hours are the daily and weekly rhythms of the")
print("network showing up as pure arithmetic. Those are the lags worth keeping.")

# ---- build the lag and rolling features ----------------------------------
feat = feat.sort_values("timestamp").reset_index(drop=True)
for L in (1, 2, 24, 48, 168):
    feat[f"lag_{L}"] = feat.demand_mw.shift(L)
feat["roll24_lag24"] = feat.demand_mw.shift(24).rolling(24).mean()   # yesterday's mean
feat["max24_lag24"]  = feat.demand_mw.shift(24).rolling(24).max()    # yesterday's peak

before = len(feat)
feat = feat.dropna().reset_index(drop=True)
print(f"\nlag features cost the first {before - len(feat)} hours (one week of history "
      f"has to exist before lag_168 does). {len(feat):,} usable hours remain.")
display(feat[["timestamp", "demand_mw", "lag_1", "lag_24", "lag_168",
              "roll24_lag24", "max24_lag24"]].head(3))
'''.strip("\n"))],
    built="""The features that turn this from a regression on conditions into a genuine time-series forecast:
the same hour yesterday, the day before, last week, and yesterday's mean and peak.""",
    takeaway="""The strongest single predictor of tomorrow's demand is what the system drew today.""",
)


# ---------------------------------------------- PHASE 6 · THE FORECAST GATE
step(
    id="gate", phase=5, icon="🚪", ai_icon="⛔",
    civil="What Is Known At 23:00", ai="Preventing Data Leakage",
    tech="For a forecast issued at 23:00 for tomorrow, lag L is usable only if L >= hours ahead",
    site="""Fix the operational moment precisely, because everything depends on it. The forecast is
**issued at 23:00 tonight** and covers **00:00 to 23:00 tomorrow**. At that moment the latest measured
demand is the hour ending 23:00 today. Tomorrow's weather comes from the met forecast. The calendar is
known indefinitely.""",
    challenge="""Now check the lag features against that clock. To forecast 13:00 tomorrow you are standing
14 hours away from it. `lag_1` for that hour means 12:00 tomorrow — **which has not happened yet.** It is
in the dataset, because the dataset was assembled after the fact, but it would not be on the desk at the
moment the forecast is due.""",
    ai_link="""Using it anyway is called **data leakage**, and it is the most common way a forecasting project
fails. The model scores brilliantly in the notebook and cannot be deployed, because in production the
column is empty. The rule is arithmetic: for a target hour *h* hours ahead, **lag `L` is usable only if
`L >= h`.** Apply it and `lag_1` and `lag_2` fall out of the day-ahead feature set.""",
    bridge=[("The 23:00 issue time", "The information cut-off"),
            ("Tomorrow has not happened", "lag_1 is unavailable"),
            ("What is on the desk", "The legal feature set")],
    body=[("co", r'''
# The forecast is issued at 23:00 for the 24 hours of tomorrow.
# Target hour h of tomorrow is (h + 1) hours after the issue time.
print("Forecast issued 23:00 today, covering 00:00-23:00 tomorrow.")
print(f"\n{'target hour':>12s} {'hours ahead':>12s} {'lag_1':>8s} {'lag_2':>8s} "
      f"{'lag_24':>8s} {'lag_48':>8s} {'lag_168':>9s}")
for h in [0, 1, 2, 7, 13, 19, 23]:
    ahead = h + 1
    row = "".join(f"{'yes' if L >= ahead else 'NO':>8s}" for L in (1, 2, 24, 48))
    print(f"{f'{h:02d}:00':>12s} {ahead:12d}{row}{'yes' if 168 >= ahead else 'NO':>9s}")

print()
print("lag_1 survives for exactly one hour of the 24 - and a feature that is")
print("available 1/24th of the time is not a feature. It leaves the day-ahead set.")

# ---- the two feature sets, fixed here and used for the rest of the notebook
F_CALENDAR = ["hour_sin", "hour_cos", "month_sin", "month_cos",
              "dayofweek", "is_weekend", "is_holiday"]
F_WEATHER  = ["temperature_c", "humidity_pct", "cdd", "hdd"]
F_LAGS_DA  = ["lag_24", "lag_48", "lag_168", "roll24_lag24", "max24_lag24"]
F_LAGS_ST  = ["lag_1", "lag_2"]

DAY_AHEAD  = F_CALENDAR + F_WEATHER + F_LAGS_DA     # the honest operational problem
SHORT_TERM = DAY_AHEAD + F_LAGS_ST                  # 1 hour ahead only - step 30
NO_LAGS    = F_CALENDAR + F_WEATHER                 # for comparison in step 22
TARGET     = "demand_mw"

print(f"\nDAY-AHEAD feature set ({len(DAY_AHEAD)} features):")
for f in DAY_AHEAD:
    print(f"   {f}")
print(f"\nExcluded as unavailable at issue time: {', '.join(F_LAGS_ST)}")
'''.strip("\n"))],
    built="""The feature set the utility can actually run — sixteen columns, every one of which would genuinely
be on the desk at 23:00 tonight. Two tempting columns deliberately left out.""",
    takeaway="""A feature that will not exist at forecast time is not a feature, however well it scores here.""",
)

step(
    id="split", phase=5, icon="✂️", ai_icon="📆",
    civil="Split By Time, Never At Random", ai="Chronological Train/Validation/Test",
    tech="Train to April 2024, validate May-June, test July-December",
    site="""The model must be judged on weeks it has never seen — and in forecasting, 'never seen' has a
direction. A forecast is always made **forwards**. So the split is a date, not a random selection: train
on the earliest period, validate on the next, test on the most recent.""",
    challenge="""The reflex is `train_test_split(shuffle=True)`, and in a time series it is quietly
catastrophic. Shuffling puts 14:00 on 3 August in the training set and 15:00 on 3 August in the test set.
Those two hours share the weather, the day type, and nearly the same demand — and `lag_24` of one is
almost `lag_24` of the other. The model is being tested on hours it has effectively already seen.""",
    ai_link="""So split chronologically, and use **three** periods rather than two. **Train** fits the models.
**Validation** is used to choose between them and, in step 25, to measure a correction — decisions have to
be made on data the test set never touches. **Test** is opened once, at the end, and reported honestly.""",
    bridge=[("A forecast runs forwards", "Split on a date"),
            ("Adjacent hours are near-copies", "Shuffling leaks"),
            ("Choose the model on one period", "Validation, not test")],
    body=[("co", r'''
TRAIN_END, VAL_END = "2024-05-01", "2024-07-01"

train = feat[feat.timestamp <  TRAIN_END]
val   = feat[(feat.timestamp >= TRAIN_END) & (feat.timestamp < VAL_END)]
test  = feat[feat.timestamp >= VAL_END]

for nm, part in [("train", train), ("validation", val), ("test", test)]:
    print(f"{nm:11s} {len(part):6,d} h   {part.timestamp.min().date()} -> "
          f"{part.timestamp.max().date()}   peak {part.demand_mw.max():.0f} MW")

fig = go.Figure()
for part, nm, col in [(train, "train", CYAN), (val, "validation", AMBER), (test, "test", GREEN)]:
    daily = part.set_index("timestamp").demand_mw.resample("D").max()
    fig.add_trace(go.Scatter(x=daily.index, y=daily.values, name=nm,
                             line=dict(color=col, width=1.6)))
fig.update_layout(title="Daily peak demand — the three periods, in the order they happened",
                  xaxis_title="date", yaxis_title="daily peak demand (MW)",
                  template="plotly_white", height=420)
fig.show()

# ---- what shuffling would have told you ----------------------------------
from sklearn.model_selection import train_test_split as _tts
probe = RandomForestRegressor(n_estimators=120, min_samples_leaf=2,
                              random_state=42, n_jobs=-1)

Xs_tr, Xs_te, ys_tr, ys_te = _tts(feat[DAY_AHEAD], feat[TARGET],
                                  test_size=len(test) / len(feat), random_state=42)
probe.fit(Xs_tr, ys_tr)
shuf_mae = mean_absolute_error(ys_te, probe.predict(Xs_te))
shuf_r2  = r2_score(ys_te, probe.predict(Xs_te))

probe.fit(train[DAY_AHEAD], train[TARGET])
chron_mae = mean_absolute_error(test[TARGET], probe.predict(test[DAY_AHEAD]))
chron_r2  = r2_score(test[TARGET], probe.predict(test[DAY_AHEAD]))

print(f"\n{'split method':>26s} {'MAE (MW)':>10s} {'R2':>8s}")
print(f"{'random shuffle':>26s} {shuf_mae:10.2f} {shuf_r2:8.4f}   <- flattering, and wrong")
print(f"{'chronological':>26s} {chron_mae:10.2f} {chron_r2:8.4f}   <- what deployment looks like")
print(f"\nShuffling makes the same model look {(1 - shuf_mae/chron_mae)*100:.0f}% more accurate "
      f"than it will be in the control room.")
'''.strip("\n"))],
    built="""Three chronological periods, and a measurement of exactly how much a shuffled split would have
flattered the result. The gap is not a rounding error.""",
    takeaway="""Shuffling a time series tests the model on hours it has already been shown.""",
)

step(
    id="scaling", phase=5, icon="📏", ai_icon="⚖️",
    civil="Different Units, Different Magnitudes", ai="Feature Scaling",
    tech="StandardScaler, and an honest test of whether it changes anything",
    site="""The sixteen features are in wildly different units. Demand lags are in the hundreds of megawatts,
temperature in tens of degrees, degree hours in single digits, and the flags are 0 or 1. A change of
'one unit' means something completely different in each column.""",
    challenge="""The standard advice is 'always scale your features', and it is repeated so often that almost
nobody checks whether it is true for the model they are using. For ordinary least squares it is **not**:
rescaling a column rescales its coefficient by exactly the reciprocal, and the predictions come out
identical. For decision trees it is also not, because a tree only ever asks 'is this value above that
threshold?'.""",
    ai_link="""So test it rather than assume it. Scaling genuinely matters for **regularised** models, for
anything trained by **gradient descent**, and for **distance-based** methods. For the four models in this
notebook it changes nothing about accuracy — but it does something else that is useful: standardised
coefficients are directly comparable, so they tell you which driver moves demand most per standard
deviation.""",
    bridge=[("Megawatts, degrees, flags", "Features on different scales"),
            ("Does it change the answer?", "Measure, do not assume"),
            ("Which driver matters most", "Standardised coefficients")],
    body=[("co", r'''
scaler = StandardScaler().fit(train[DAY_AHEAD])
Xtr_s = scaler.transform(train[DAY_AHEAD])
Xte_s = scaler.transform(test[DAY_AHEAD])

raw_lr = LinearRegression().fit(train[DAY_AHEAD], train[TARGET])
scl_lr = LinearRegression().fit(Xtr_s, train[TARGET])

mae_raw = mean_absolute_error(test[TARGET], raw_lr.predict(test[DAY_AHEAD]))
mae_scl = mean_absolute_error(test[TARGET], scl_lr.predict(Xte_s))
print(f"Linear regression, unscaled features : MAE {mae_raw:.4f} MW")
print(f"Linear regression, scaled features   : MAE {mae_scl:.4f} MW")
print(f"difference                           : {abs(mae_raw - mae_scl):.6f} MW")
print("\nIdentical, to within floating point. Scaling did not improve the model,")
print("and any tutorial that claims otherwise for plain least squares is wrong.")

# ---- what scaling IS good for -------------------------------------------
coef = pd.DataFrame({"feature": DAY_AHEAD, "standardised_coef": scl_lr.coef_})
coef["abs"] = coef.standardised_coef.abs()
coef = coef.sort_values("abs", ascending=False)

fig = go.Figure(go.Bar(
    x=coef.standardised_coef, y=coef.feature, orientation="h",
    marker_color=[CYAN if c > 0 else AMBER for c in coef.standardised_coef],
    text=[f"{c:+.1f}" for c in coef.standardised_coef], textposition="outside"))
fig.update_layout(title="Standardised coefficients — MW moved per standard deviation of each feature",
                  xaxis_title="MW per standard deviation", template="plotly_white",
                  height=520, yaxis=dict(autorange="reversed"), margin=dict(l=140))
fig.show()

print(f"\nStrongest single driver in the linear model: {coef.feature.iloc[0]} "
      f"({coef.standardised_coef.iloc[0]:+.1f} MW per standard deviation)")
'''.strip("\n"))],
    built="""A scaler, and a measured demonstration that for these models it changes nothing about accuracy —
plus the thing it is genuinely useful for: comparable coefficients that rank the drivers.""",
    takeaway="""Scale features when the model needs it, not as a ritual — and check which case you are in.""",
)


# ---------------------------------------------- PHASE 7 · THE BAR TO CLEAR
step(
    id="persistence", phase=6, icon="📋", ai_icon="🎯",
    civil="What The Old Method Achieves", ai="The Naive Baseline",
    tech="Forecast = same hour yesterday, and = same hour last week",
    site="""Before machine learning, this forecast was made by hand, and the method was sound: take the same
hour on a comparable recent day and adjust it for the weather. On a stable system it works. It is called
a **persistence forecast**, and it is what the utility does today.""",
    challenge="""It has two known failure modes and no way to handle either. It cannot see a **weather change**
— if today was 30 °C and tomorrow is 39 °C, yesterday's figure is badly wrong. And it cannot handle a
**day-type change** — Monday's figure is a poor guide to a public holiday.""",
    ai_link="""This is the bar. Any model that does not beat persistence is not worth deploying, whatever its
R². Scoring the naive method first is what keeps the rest of the notebook honest: every number that
follows is compared against it, not against zero.""",
    bridge=[("Yesterday, same hour", "The persistence baseline"),
            ("The method in use today", "The benchmark to beat"),
            ("Beat it or do not deploy", "Relative, not absolute, scoring")],
    body=[("co", r'''
def report(name, y, p, store=None):
    y, p = np.asarray(y, float), np.asarray(p, float)
    m = dict(model=name,
             MAE=mean_absolute_error(y, p),
             RMSE=float(np.sqrt(mean_squared_error(y, p))),
             MAPE=float(np.mean(np.abs((y - p) / y)) * 100),
             R2=r2_score(y, p),
             BIAS=float(np.mean(p - y)))
    if store is not None:
        store.append(m)
    print(f"{name:34s} MAE {m['MAE']:6.2f} MW   RMSE {m['RMSE']:6.2f} MW   "
          f"MAPE {m['MAPE']:5.2f}%   R2 {m['R2']:.4f}   bias {m['BIAS']:+6.2f} MW")
    return m

SCORES = []
y_test = test[TARGET].values

print("Scored on the test period only — hours no model has seen.\n")
report("Persistence: same hour yesterday", y_test, test.lag_24.values, SCORES)
report("Persistence: same hour last week", y_test, test.lag_168.values, SCORES)
report("Flat: yesterday's mean all day",   y_test, test.roll24_lag24.values, SCORES)

# ---- where persistence fails, shown on the worst day ---------------------
t = test.copy()
t["pers_err"] = t.lag_24.values - t[TARGET].values
worst = t.assign(d=t.timestamp.dt.date).groupby("d").pers_err.apply(
    lambda s: s.abs().mean()).idxmax()
day = t[t.timestamp.dt.date == worst]

fig = go.Figure()
fig.add_trace(go.Scatter(x=day.timestamp, y=day[TARGET], name="actual demand",
                         line=dict(color=CYAN, width=3)))
fig.add_trace(go.Scatter(x=day.timestamp, y=day.lag_24, name="persistence forecast",
                         line=dict(color=RED, width=2.5, dash="dash")))
fig.update_layout(title=f"Persistence on its worst day in the test period — {worst}",
                  xaxis_title="hour", yaxis_title="demand (MW)",
                  template="plotly_white", height=400)
fig.show()

print(f"\nOn {worst} persistence was wrong by {day.pers_err.abs().mean():.0f} MW on average, "
      f"peaking at {day.pers_err.abs().max():.0f} MW.")
print(f"Temperature moved from {t[t.timestamp.dt.date == worst].temperature_c.mean():.1f} degC mean "
      f"that day; the previous day averaged "
      f"{t[t.timestamp.dt.date == (pd.Timestamp(worst) - pd.Timedelta(days=1)).date()].temperature_c.mean():.1f} degC.")
print("Persistence has no mechanism for that. Every model from here on does.")
'''.strip("\n"))],
    built="""Three naive baselines scored on the test period, and a worked example of the day persistence
fails hardest — a weather change it has no way to see.""",
    takeaway="""The benchmark is not zero error, it is the method the utility already uses.""",
)


# ---------------------------------------------- PHASE 8 · THE MODELS
step(
    id="linear", phase=7, icon="📐", ai_icon="➗",
    civil="One Coefficient Per Driver", ai="Linear Regression",
    tech="demand = w1*f1 + w2*f2 + ... + b, fitted by least squares",
    site="""The first model is the one an engineer would write by hand: give every driver a coefficient in
megawatts per unit, multiply, and add. So many MW per cooling degree hour, so many MW off for a Sunday, so
many MW carried over from yesterday's level.""",
    challenge="""Its assumption is that the drivers **add up independently**, and this network has already
shown that they do not. Humidity's effect depends on temperature. The evening peak's size depends on the
season. A single coefficient per feature cannot express 'it depends'.""",
    ai_link="""Fit it anyway, and for two good reasons. It sets a **transparent floor** — you can read every
coefficient and check it against engineering sense. And when the tree models beat it later, the size of
the gap is a direct measurement of **how much of this problem is non-linear**.""",
    bridge=[("MW per degree, MW per Sunday", "One coefficient per feature"),
            ("Effects that add up", "A linear model's core assumption"),
            ("A readable, checkable model", "The interpretable floor")],
    body=[("co", r'''
FITTED, VAL_SCORES = {}, []

def fit_and_validate(name, model, features=None):
    """Fit on train, score on VALIDATION. The test set stays closed until step 22."""
    features = features or DAY_AHEAD
    model.fit(train[features], train[TARGET])
    p = model.predict(val[features])
    FITTED[name] = (model, features)
    return report(name, val[TARGET].values, p, VAL_SCORES)

fit_and_validate("Linear Regression", LinearRegression())

# ---- read the coefficients as engineering quantities ---------------------
lr = FITTED["Linear Regression"][0]
co_tbl = pd.DataFrame({"feature": DAY_AHEAD, "MW per unit": lr.coef_}).round(3)
display(co_tbl.sort_values("MW per unit", key=abs, ascending=False).head(8))

def coef_of(name):
    return float(co_tbl.loc[co_tbl.feature == name, "MW per unit"].iloc[0])

print(f"\nIntercept: {lr.intercept_:.1f} MW")
print(f"Each cooling degree hour adds {coef_of('cdd'):.1f} MW.")
print(f"A weekend takes {abs(coef_of('is_weekend')):.1f} MW off.")
print(f"A holiday takes {abs(coef_of('is_holiday')):.1f} MW off.")
print(f"Every MW the system drew at this hour yesterday carries "
      f"{coef_of('lag_24'):.2f} MW into today.")
print("\nThose read like sensible engineering numbers, which is exactly the point of")
print("this model: you can check it against what you already know.")
'''.strip("\n"))],
    built="""A transparent baseline model whose every coefficient can be read in megawatts and sanity-checked
against power system experience.""",
    takeaway="""Linear regression is the floor — readable, checkable, and blind to anything that depends on
something else.""",
)

step(
    id="forest", phase=7, icon="🌳", ai_icon="🌲",
    civil="Many Operators, One Answer", ai="Random Forest Regression",
    tech="Hundreds of decision trees on random subsets, averaged",
    site="""A different way to forecast: ask a series of yes/no questions. *Is it above 32 °C? Is it a
weekday? Was yesterday's peak above 900 MW? Is the hour between 17:00 and 21:00?* Each answer narrows the
range until a demand figure remains. That is a **decision tree**, and it is close to how an experienced
operator actually reasons.""",
    challenge="""One tree is unstable. Grown deep enough it memorises the training years — including the
measurement noise — and forecasts new weeks badly. Grown shallow it is too crude to capture the evening
peak. Neither depth is right.""",
    ai_link="""A **random forest** removes the choice. Grow hundreds of trees, each on a random subset of the
rows and columns, and average them. The individual errors are largely independent and cancel; the shared
signal survives. And because each tree splits on one feature and *then* another, the forest represents
**interactions natively** — the humidity-only-when-hot effect that linear regression could not reach.""",
    bridge=[("A chain of yes/no checks", "A decision tree"),
            ("One expert can be idiosyncratic", "A single tree overfits"),
            ("Ask many, average the answer", "Ensemble averaging")],
    body=[("co", r'''
fit_and_validate("Random Forest", RandomForestRegressor(
    n_estimators=300, min_samples_leaf=2, random_state=42, n_jobs=-1))

# ---- one shallow tree, so the mechanism is visible ------------------------
from sklearn.tree import DecisionTreeRegressor, export_text
demo = DecisionTreeRegressor(max_depth=3, random_state=42).fit(
    train[DAY_AHEAD], train[TARGET])
print("A single depth-3 tree, in words — this is the mechanism, not the model:\n")
print(export_text(demo, feature_names=list(DAY_AHEAD), decimals=0))
'''.strip("\n"))],
    built="""A forest of 300 trees, and one deliberately tiny tree printed in full so the branching logic is
visible rather than asserted.""",
    takeaway="""Trees split on one driver and then another, which is how they capture 'it depends'.""",
)

step(
    id="boosting", phase=7, icon="🪜", ai_icon="📶",
    civil="Correcting The Last Attempt", ai="Gradient Boosting Regression",
    tech="Each new tree is fitted to the errors the previous trees left behind",
    site="""A forest builds every tree independently and averages. Boosting works the way a commissioning
team works: make a first rough forecast, look at **where it was wrong**, and build the next stage
specifically to fix those errors. Repeat several hundred times, each stage correcting what remains.""",
    challenge="""The risk is the opposite of the forest's. Because every stage chases the leftover errors, a
boosted model will eventually start fitting the measurement noise in the training years — the frozen-meter
artefacts, the random fluctuation — and its forecasts on new weeks get worse while its training score
keeps improving.""",
    ai_link="""Two controls hold it back. The **learning rate** shrinks each correction so no single stage can
dominate, and the **tree depth** limits how intricate each correction can be. Together they are why
gradient boosting is usually the strongest model on tabular problems like this one.""",
    bridge=[("Fix what the last attempt got wrong", "Fit the residuals"),
            ("Small corrections, many stages", "A low learning rate"),
            ("Do not chase the noise", "Depth and rate as regularisers")],
    body=[("co", r'''
fit_and_validate("Gradient Boosting", GradientBoostingRegressor(
    n_estimators=400, learning_rate=0.06, max_depth=4, random_state=42))

# ---- watch the correction happen, stage by stage --------------------------
gb = FITTED["Gradient Boosting"][0]
stages = np.array([mean_absolute_error(val[TARGET], p)
                   for p in gb.staged_predict(val[DAY_AHEAD])])

fig = go.Figure(go.Scatter(x=np.arange(1, len(stages) + 1), y=stages,
                           line=dict(color=CYAN, width=3)))
fig.add_hline(y=stages.min(), line=dict(color=GREEN, dash="dot"),
              annotation_text=f"best {stages.min():.2f} MW at stage {stages.argmin()+1}")
fig.update_layout(title="Validation error after each boosting stage",
                  xaxis_title="number of trees", yaxis_title="validation MAE (MW)",
                  template="plotly_white", height=400)
fig.show()

print(f"After   1 tree  : {stages[0]:6.2f} MW")
print(f"After  50 trees : {stages[49]:6.2f} MW")
print(f"After 400 trees : {stages[-1]:6.2f} MW")
print(f"\nBest at stage {stages.argmin()+1} ({stages.min():.2f} MW). "
      f"{'The curve is still falling at 400 - more stages would help slightly.' if stages.argmin() > len(stages)-10 else 'Beyond that the curve turns up: that is overfitting, visible.'}")
'''.strip("\n"))],
    built="""A boosted model, and its validation error traced stage by stage so the correction process — and
the point where it stops helping — can be seen rather than taken on trust.""",
    takeaway="""Boosting improves by fitting its own leftover errors, which is powerful and needs restraining.""",
)

step(
    id="xgboost", phase=7, icon="⚙️", ai_icon="🚀",
    civil="The Production Implementation", ai="XGBoost Regression",
    tech="Regularised gradient boosting with column and row subsampling",
    site="""XGBoost is gradient boosting rebuilt for production use, and it is what most utilities and
forecasting vendors actually run. Same idea — stages of trees correcting the previous stages — with the
engineering tightened up.""",
    challenge="""Two problems remain in plain boosting. It can still overfit the training years, and on
several years of hourly data across many feeders it is slow to fit and slow to re-fit. A forecasting
system that has to be retrained weekly cannot afford either.""",
    ai_link="""XGBoost adds **explicit regularisation** in the objective, which penalises complexity directly
rather than relying on depth limits alone, plus **row and column subsampling** so each tree sees a
different slice. The result is usually a small accuracy gain and a large speed gain.""",
    bridge=[("Retrained every week", "Fitting speed matters"),
            ("Do not memorise the history", "Explicit regularisation"),
            ("The vendor standard", "The production implementation")],
    body=[("co", r'''
try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("xgboost is not installed - skipping this model.")
    print("Run:  !pip install xgboost      (it is already present in Colab)")

if HAS_XGB:
    fit_and_validate("XGBoost", XGBRegressor(
        n_estimators=600, learning_rate=0.05, max_depth=5,
        subsample=0.9, colsample_bytree=0.9, random_state=42, n_jobs=-1))

    import time
    t0 = time.perf_counter()
    XGBRegressor(n_estimators=400, learning_rate=0.06, max_depth=4,
                 random_state=42, n_jobs=-1).fit(train[DAY_AHEAD], train[TARGET])
    t_xgb = time.perf_counter() - t0

    t0 = time.perf_counter()
    GradientBoostingRegressor(n_estimators=400, learning_rate=0.06,
                              max_depth=4, random_state=42).fit(train[DAY_AHEAD], train[TARGET])
    t_gb = time.perf_counter() - t0

    print(f"\nSame configuration, {len(train):,} training hours:")
    print(f"   sklearn GradientBoosting : {t_gb:5.2f} s")
    print(f"   XGBoost                  : {t_xgb:5.2f} s   ({t_gb/t_xgb:.1f}x faster)")
    print("\nOn one feeder that is a curiosity. Across a few hundred feeders,")
    print("retrained weekly, it is the difference between feasible and not.")
'''.strip("\n"))],
    built="""The production-grade boosting implementation, scored on the same validation period as the others
and timed against its sklearn equivalent.""",
    takeaway="""XGBoost is the same idea as gradient boosting, regularised and engineered to be retrained often.""",
)

step(
    id="compare", phase=7, icon="🏁", ai_icon="📊",
    civil="Which Forecast Would You Sign?", ai="Model Selection",
    tech="Rank on validation, choose one, then open the test set once",
    site="""Four models, one validation period, one decision. The despatch engineer does not want four
forecasts — they want the one number that goes on the schedule, and a reason for choosing it.""",
    challenge="""The temptation is to fit all four, score them all on the test set, and report the best. That
is **selection on the test set**, and it quietly turns the test score into an optimistic one: you have
used the test data to make a decision, so it is no longer untouched.""",
    ai_link="""So the order matters. Rank on **validation**, pick the winner, and only then open the **test**
set — once. Whatever it says is the number you report. This step also runs the lag features off and on,
which measures directly how much of the accuracy comes from the time-series features versus the weather
and calendar.""",
    bridge=[("Choose on one period", "Validation for selection"),
            ("Report on another", "Test opened once"),
            ("How much do lags buy?", "An ablation study")],
    body=[("co", r'''
tbl = pd.DataFrame(VAL_SCORES).set_index("model").round(3)
display(tbl.sort_values("MAE"))

names = tbl.sort_values("MAE").index.tolist()
fig = go.Figure()
fig.add_trace(go.Bar(x=names, y=tbl.loc[names, "MAE"], name="MAE",
                     marker_color=CYAN, text=tbl.loc[names, "MAE"].round(1),
                     textposition="outside"))
fig.add_trace(go.Bar(x=names, y=tbl.loc[names, "RMSE"], name="RMSE",
                     marker_color=AMBER, text=tbl.loc[names, "RMSE"].round(1),
                     textposition="outside"))
fig.update_layout(title="Validation error by model — lower is better",
                  yaxis_title="MW", barmode="group", template="plotly_white", height=420)
fig.show()

BEST_NAME = tbl.MAE.idxmin()
best_model, best_feats = FITTED[BEST_NAME]
print(f"Selected on validation: {BEST_NAME}")
print("Note how close the top two are. On a two-month validation window that gap is")
print("well inside the noise - either would be a defensible choice.\n")

# ---- now, once: the test set --------------------------------------------
print("=" * 78)
print("Opening the test set for the first time.")
print("=" * 78 + "\n")
pred_raw = best_model.predict(test[best_feats])
TEST_RAW = report(f"{BEST_NAME} on test", y_test, pred_raw)

print(f"\nValidation MAE {tbl.loc[BEST_NAME,'MAE']:.2f} MW  ->  test MAE {TEST_RAW['MAE']:.2f} MW.")
print(f"But look at the bias column: {TEST_RAW['BIAS']:+.2f} MW on test against "
      f"{tbl.loc[BEST_NAME,'BIAS']:+.2f} MW on validation.")
print("The forecast is not scattered around the truth - it sits consistently BELOW it,")
print("and the offset grows with distance from the training data. Step 25 explains why.")

# ---- ablation: how much do the lag features actually buy? ----------------
# Run on the test period because the two-month validation window is a single
# season and too short to compare feature sets on. This is a DIAGNOSTIC, not a
# selection - no model in this notebook was chosen using the test set.
print("\n" + "-" * 78)
print("Diagnostic: the same models trained WITHOUT any lag features")
print("-" * 78 + "\n")
for nm, mk, feats in [
        ("Linear Regression", lambda: LinearRegression(), NO_LAGS),
        ("Random Forest", lambda: RandomForestRegressor(
            n_estimators=300, min_samples_leaf=2, random_state=42, n_jobs=-1), NO_LAGS),
        ("Gradient Boosting", lambda: GradientBoostingRegressor(
            n_estimators=400, learning_rate=0.06, max_depth=4, random_state=42), NO_LAGS)]:
    m_no = mk().fit(train[feats], train[TARGET])
    mae_no = mean_absolute_error(y_test, m_no.predict(test[feats]))
    m_yes = mk().fit(train[DAY_AHEAD], train[TARGET])
    mae_yes = mean_absolute_error(y_test, m_yes.predict(test[DAY_AHEAD]))
    print(f"{nm:20s}  without lags {mae_no:6.2f} MW   with lags {mae_yes:6.2f} MW   "
          f"({(1 - mae_yes/mae_no)*100:+5.1f}%)")

print()
print("Linear regression gains most: with no memory of the recent level it has only")
print("weather and the calendar, and its additive form cannot make those stretch.")
'''.strip("\n"))],
    built="""A ranked comparison on validation, one selected model, an ablation showing what the lag features
are worth, and a first, single look at the test period — which raises a question rather than settling one.""",
    takeaway="""Choose the model on validation and open the test set once, or the score you report is not the
score you will get.""",
)


# ---------------------------------------------- PHASE 9 · READING THE MODEL
step(
    id="importance", phase=8, icon="🔬", ai_icon="📶",
    civil="Which Drivers Carry The Forecast", ai="Feature Importance",
    tech="Permutation importance: shuffle one column, measure the damage",
    site="""A forecast the operator cannot interrogate is a forecast they will override. The first question
in any control room is *why* — why is tomorrow evening 70 MW above today's, and which input is driving
that.""",
    challenge="""A tree ensemble has hundreds of trees and thousands of splits. There is no coefficient to
read. The importances that come free with the model count how often each feature was split on, which
over-credits features with many distinct values — temperature gets flattered simply for being continuous.""",
    ai_link="""**Permutation importance** avoids that. Take the fitted model, shuffle one column so it carries
no information, and measure how much the error grows. A feature the forecast genuinely depends on causes
a large increase; a decorative one causes none. It is measured on **validation**, not on training data,
so it reflects what the model actually relies on to forecast unseen weeks.""",
    bridge=[("Why is the forecast high?", "Feature attribution"),
            ("Break one input, see what happens", "Permutation importance"),
            ("Measured on unseen weeks", "Validation, not training")],
    body=[("co", r'''
from sklearn.inspection import permutation_importance

pi = permutation_importance(best_model, val[best_feats], val[TARGET],
                            n_repeats=8, random_state=42, n_jobs=-1,
                            scoring="neg_mean_absolute_error")
imp = (pd.DataFrame({"feature": best_feats,
                     "MW": pi.importances_mean, "sd": pi.importances_std})
       .sort_values("MW", ascending=False).reset_index(drop=True))

fig = go.Figure(go.Bar(x=imp.MW, y=imp.feature, orientation="h",
                       error_x=dict(array=imp.sd, color=MUTED),
                       marker_color=CYAN,
                       text=imp.MW.round(1), textposition="outside"))
fig.update_layout(title=f"Permutation importance — MW of extra error when each feature is scrambled ({BEST_NAME})",
                  xaxis_title="increase in validation MAE (MW)", template="plotly_white",
                  height=520, yaxis=dict(autorange="reversed"), margin=dict(l=150))
fig.show()

display(imp.round(2).head(8))

top = imp.iloc[0]
print(f"\nStrongest driver: {top.feature} — scrambling it costs {top.MW:.1f} MW of accuracy.")
print(f"Features worth under 1 MW: {', '.join(imp[imp.MW < 1.0].feature) or 'none'}")

print()
print("Two cautions before reading too much into this ranking.")
print()
print("1. It measures what is IRREPLACEABLE, not what is informative. cdd is computed")
print("   FROM temperature, and lag_24, lag_168 and roll24_lag24 all carry the recent")
print("   level. Scramble one and the model recovers most of it from its neighbours,")
print("   so correlated features share - and therefore understate - their importance.")
print()
h_rank = int(imp.index[imp.feature == 'humidity_pct'][0]) + 1
print(f"2. It is an AVERAGE over every test hour. humidity_pct ranks {h_rank} of "
      f"{len(imp)} here,")
print("   because most hours are mild and humidity then moves almost nothing. That")
print("   does NOT mean it is unimportant - on the hot evenings when the system is")
print("   under strain it is worth tens of megawatts. Step 24 shows exactly that.")
print("   An average importance can hide a driver that only matters at the extremes.")
'''.strip("\n"))],
    built="""A ranking of the forecast's real dependencies, measured by damage rather than by split counts, with
error bars from repeated shuffles.""",
    takeaway="""A feature matters if breaking it breaks the forecast — everything else is decoration.""",
)

step(
    id="sensitivity", phase=8, icon="🎚️", ai_icon="📈",
    civil="Does It Agree With The Physics?", ai="Model Response Curves",
    tech="Hold everything fixed, sweep one input, plot the model's response",
    site="""Importance says *which* inputs matter. It does not say *how*. An engineer commissioning any
instrument sweeps its input across the range and checks the response against what the physics says it
should be. A forecasting model deserves exactly the same treatment.""",
    challenge="""A model can be accurate on average and still wrong in a way that matters. If its demand
falls as temperature rises above 35 °C — because few such hours existed in training — then it will fail
precisely on the days the system is most stressed, while its overall MAE looks fine.""",
    ai_link="""So sweep it. Fix a representative hour, vary temperature across the full operating range, and
plot what the model predicts. Then repeat at two humidity levels. If the model has genuinely learnt the
interaction from step 9, the two curves will **diverge as it gets hotter** and sit together when it is
mild. That is the physics, recovered from data.""",
    bridge=[("Sweep the input, check the response", "A partial dependence sweep"),
            ("Compare against known physics", "Model validation, not scoring"),
            ("Two curves that diverge", "The interaction, recovered")],
    body=[("co", r'''
def response(temps, humidity, hour=19, dow=2, holiday=0, level=None):
    """What the model forecasts across a temperature sweep, everything else fixed."""
    level = level if level is not None else val.roll24_lag24.median()
    rows = pd.DataFrame({
        "hour_sin": np.sin(2*np.pi*hour/24), "hour_cos": np.cos(2*np.pi*hour/24),
        "month_sin": np.sin(2*np.pi*7/12),   "month_cos": np.cos(2*np.pi*7/12),
        "dayofweek": dow, "is_weekend": int(dow >= 5), "is_holiday": holiday,
        "temperature_c": temps, "humidity_pct": humidity,
        "cdd": np.clip(temps - COOL_BASE, 0, None),
        "hdd": np.clip(HEAT_BASE - temps, 0, None),
        "lag_24": level, "lag_48": level, "lag_168": level,
        "roll24_lag24": level, "max24_lag24": level * 1.18,
    })
    return best_model.predict(rows[best_feats])

temps = np.linspace(8, 46, 100)

fig = make_subplots(rows=1, cols=2, subplot_titles=(
    "Temperature response at 19:00 — two humidity levels",
    "Hour-of-day response on a hot day and a mild one"))

for rh, col, nm in [(35, CYAN, "35% RH (dry)"), (85, RED, "85% RH (humid)")]:
    fig.add_trace(go.Scatter(x=temps, y=response(temps, rh), name=nm,
                             line=dict(color=col, width=3)), row=1, col=1)
fig.add_vline(x=COOL_BASE, line=dict(color=MUTED, dash="dash"), row=1, col=1)

hrs = np.arange(24)
for T, col, nm in [(38, RED, "38 degC"), (22, CYAN, "22 degC")]:
    ys = [response(np.array([T]), 60.0, hour=h)[0] for h in hrs]
    fig.add_trace(go.Scatter(x=hrs, y=ys, name=nm, line=dict(color=col, width=3)),
                  row=1, col=2)

fig.update_xaxes(title_text="temperature (degC)", row=1, col=1)
fig.update_xaxes(title_text="hour of day", row=1, col=2)
fig.update_yaxes(title_text="forecast demand (MW)", row=1, col=1)
fig.update_layout(template="plotly_white", height=440)
fig.show()

dry, humid = response(temps, 35), response(temps, 85)
print(f"{'temperature':>12s} {'dry (35% RH)':>14s} {'humid (85% RH)':>16s} {'humidity worth':>16s}")
for T in (18, 24, 30, 36, 42):
    i = int(np.argmin(np.abs(temps - T)))
    print(f"{T:9d} degC {dry[i]:11.0f} MW {humid[i]:13.0f} MW {humid[i]-dry[i]:+13.0f} MW")

print()
print("Read the last column downwards. Humidity is worth little or nothing through")
print("the comfort band and grows steadily as the temperature climbs, reaching tens")
print("of megawatts at the top of the range. That is the interaction from step 9,")
print("recovered from two years of readings - nobody programmed it in.")
print()
print("The small NEGATIVE values in the mild bands are worth understanding rather")
print("than dismissing: in this network humid mild hours are monsoon and overnight")
print("hours, which genuinely run slightly lighter. The model has learnt a real")
print("association, not a physical law - a distinction worth keeping in mind before")
print("quoting any single number off a response curve.")
'''.strip("\n"))],
    built="""Response curves swept out of the fitted model and checked against the physics of step 9 — including
the temperature–humidity interaction, recovered from data rather than assumed.""",
    takeaway="""A model that is accurate on average can still be wrong where it matters; sweep it and look.""",
)

step(
    id="bias", phase=8, icon="📉", ai_icon="🧭",
    civil="Why The Forecast Drifts Low", ai="Distribution Shift And Bias Correction",
    tech="Measure the mean residual on validation, subtract it from the forecast",
    site="""Step 22 left a loose end. The selected model is not just less accurate on the test period than on
validation — it is **consistently low**, by roughly the same amount every hour. A random error is
tolerable. A systematic one is a different kind of defect, and in this direction it is the expensive one.""",
    challenge="""The cause is ordinary and unavoidable: **the licence area's demand is growing**, at about
3.5% a year. The model was fitted mostly on 2023, and 2023's relationship between conditions and megawatts
no longer holds in late 2024. Nothing in the feature set encodes the year, and the lag features carry the
new level only partly — the model blends them with weather and calendar relationships learnt at the old
one, and reverts toward it.""",
    ai_link="""This is **distribution shift**, and the standard remedy is a **level correction**: measure the
mean residual on the most recent data available before the forecast period — the validation set — and
subtract it. Critically, it is measured on validation and applied to test. Measuring it on the test set
would be marking your own homework.""",
    bridge=[("Demand grows every year", "The training distribution goes stale"),
            ("The forecast sits low", "A systematic bias, not noise"),
            ("Correct from recent history", "Bias measured on validation")],
    body=[("co", r'''
# ---- 1. show that the bias is a shift, not a modelling failure -----------
b_train = float(np.mean(best_model.predict(train[best_feats]) - train[TARGET].values))
b_val   = float(np.mean(best_model.predict(val[best_feats])   - val[TARGET].values))
b_test  = float(np.mean(pred_raw - y_test))
print(f"mean error on TRAIN      : {b_train:+7.2f} MW   (fitted here, so ~0 by construction)")
print(f"mean error on VALIDATION : {b_val:+7.2f} MW")
print(f"mean error on TEST       : {b_test:+7.2f} MW")
print("\nIt grows the further the period sits from the training data. That is the")
print("signature of drift, not of a badly specified model.")

# ---- 2. the honest failure of the obvious alternative --------------------
dm = train.set_index("timestamp").demand_mw.resample("D").mean().dropna()
tyr = (dm.index - dm.index[0]).days / 365.25
slope = np.polyfit(tyr, np.log(dm.values), 1)[0]
print(f"\nA tempting fix: estimate the trend by regressing demand on time.")
print(f"   estimate from the {len(dm)}-day training window : {np.expm1(slope)*100:+.2f} %/yr")
print(f"   the utility's actual load growth                : +{GROWTH*100:.2f} %/yr")
print("   The training window is 16 months, so the seasonal cycle dominates the fit")
print("   and the trend estimate is badly wrong. This is why the correction below is")
print("   measured as a RESIDUAL on recent data instead of as a fitted trend.")

# ---- 3. the correction ---------------------------------------------------
BIAS_CORRECTION = b_val
pred_final = pred_raw - BIAS_CORRECTION

print(f"\nCorrection applied: {-BIAS_CORRECTION:+.2f} MW on every forecast hour")
print(f"(measured on validation: {val.timestamp.min().date()} to {val.timestamp.max().date()})\n")
TEST_FINAL = report(f"{BEST_NAME} + bias correction", y_test, pred_final, SCORES)

print(f"\nMAE  {TEST_RAW['MAE']:.2f} -> {TEST_FINAL['MAE']:.2f} MW   "
      f"({(1 - TEST_FINAL['MAE']/TEST_RAW['MAE'])*100:.0f}% better)")
print(f"bias {TEST_RAW['BIAS']:+.2f} -> {TEST_FINAL['BIAS']:+.2f} MW")

# ---- 4. before and after, month by month --------------------------------
t = test.copy()
t["err_raw"], t["err_fix"] = pred_raw - y_test, pred_final - y_test
mo = t.groupby(t.timestamp.dt.to_period("M").astype(str))[["err_raw", "err_fix"]].mean()

fig = go.Figure()
fig.add_trace(go.Bar(x=mo.index, y=mo.err_raw, name="before correction", marker_color=RED))
fig.add_trace(go.Bar(x=mo.index, y=mo.err_fix, name="after correction", marker_color=GREEN))
fig.add_hline(y=0, line=dict(color=MUTED))
fig.update_layout(title="Mean forecast error by month — a systematic offset, removed",
                  yaxis_title="mean error (MW), negative = forecast too low",
                  barmode="group", template="plotly_white", height=400)
fig.show()

print("\nThe correction is a patch on a real problem, not a cure. The proper fix is to")
print("RETRAIN on recent data - which is exactly why utilities refit these models")
print("every few weeks rather than once.")
'''.strip("\n"))],
    built="""A diagnosis of the low drift as load growth rather than a modelling error, a demonstration that the
obvious trend-fitting fix does not work on a 16-month window, and a validation-measured level correction
that removes most of it.""",
    takeaway="""A forecast that is wrong in the same direction every hour has a cause worth finding, not a
constant worth tuning.""",
)


# ---------------------------------------------- PHASE 10 · THE FORECAST AUDIT
step(
    id="metrics", phase=9, icon="📑", ai_icon="🧾",
    civil="How Wrong, In Megawatts", ai="Regression Metrics",
    tech="MAE, RMSE, MAPE and R2 — and what each one is for",
    site="""The despatch engineer needs the forecast's accuracy in the units they schedule generation in.
Not a score out of one — **megawatts**. And they need more than one number, because 'wrong by 15 MW every
hour' and 'right all month except one 400 MW evening' are completely different operational risks.""",
    challenge="""Each metric hides something. **MAE** is the average miss in MW, easy to act on, but it treats
a 200 MW error as ten times a 20 MW one — when operationally it is far worse than that. **RMSE** squares
the errors so large misses dominate, which matches the cost but is harder to interpret. **MAPE** is a
percentage, comparable across utilities, but it exaggerates errors during the low overnight hours.""",
    ai_link="""So report all four and know what each is for. **MAE** for the operator. **RMSE** for the
reserve calculation, because it is driven by the large errors reserve exists to cover. **MAPE** for
benchmarking against other utilities. **R²** for the modeller. None of them is 'the' accuracy.""",
    bridge=[("Average miss in MW", "MAE"),
            ("Large misses cost more", "RMSE"),
            ("Comparable between utilities", "MAPE")],
    body=[("co", r'''
err = pred_final - y_test

print(f"Test period: {test.timestamp.min().date()} to {test.timestamp.max().date()} "
      f"({len(test):,} hours)\n")
print(f"MAE  {TEST_FINAL['MAE']:7.2f} MW    the average hour is wrong by this much")
print(f"RMSE {TEST_FINAL['RMSE']:7.2f} MW    larger misses weighted more heavily")
print(f"MAPE {TEST_FINAL['MAPE']:7.2f} %     as a share of the demand being forecast")
print(f"R2   {TEST_FINAL['R2']:7.4f}       share of demand variation explained")
print(f"\nRMSE/MAE ratio: {TEST_FINAL['RMSE']/TEST_FINAL['MAE']:.2f}  "
      f"(1.00 = every error identical; above ~1.3 means a tail of large misses)")

print(f"\nAgainst the method in use today:")
pers = [s for s in SCORES if s["model"] == "Persistence: same hour yesterday"][0]
for k, unit in [("MAE", " MW"), ("RMSE", " MW"), ("MAPE", " %")]:
    print(f"   {k:5s} {pers[k]:7.2f}{unit} -> {TEST_FINAL[k]:6.2f}{unit}   "
          f"({(1 - TEST_FINAL[k]/pers[k])*100:.0f}% better)")

# ---- the error distribution ---------------------------------------------
fig = make_subplots(rows=1, cols=2, subplot_titles=(
    "Forecast error distribution", "Forecast vs actual, every test hour"))
fig.add_trace(go.Histogram(x=err, nbinsx=70, marker_color=CYAN, name="error"),
              row=1, col=1)
fig.add_vline(x=0, line=dict(color=RED, dash="dash"), row=1, col=1)

s = test.sample(min(3000, len(test)), random_state=2).index
fig.add_trace(go.Scattergl(x=y_test[test.index.get_indexer(s)],
                           y=pred_final[test.index.get_indexer(s)],
                           mode="markers", marker=dict(size=4, color=CYAN, opacity=0.5),
                           name="hours"), row=1, col=2)
lim = [y_test.min() * 0.95, y_test.max() * 1.02]
fig.add_trace(go.Scatter(x=lim, y=lim, line=dict(color=RED, dash="dash"),
                         name="perfect"), row=1, col=2)
fig.update_xaxes(title_text="forecast - actual (MW)", row=1, col=1)
fig.update_xaxes(title_text="actual demand (MW)", row=1, col=2)
fig.update_yaxes(title_text="forecast demand (MW)", row=1, col=2)
fig.update_layout(template="plotly_white", height=420, showlegend=False)
fig.show()

for q in (50, 90, 95, 99):
    print(f"{q}% of hours are forecast within {np.percentile(np.abs(err), q):6.1f} MW")
print(f"worst single hour: {np.abs(err).max():.0f} MW")
'''.strip("\n"))],
    built="""The forecast's accuracy in four complementary units, compared against the method it replaces, plus
the error distribution and the percentile table the reserve calculation will use.""",
    takeaway="""Report the average miss, the large misses and the percentage — they answer different questions.""",
)

step(
    id="error-profile", phase=9, icon="🕰️", ai_icon="🔎",
    civil="When Is It Wrong?", ai="Error Analysis By Segment",
    tech="Break the error down by hour of day, day type and demand level",
    site="""An average error across 4,416 hours tells the operator nothing about *when* to trust the
forecast. Overnight, demand is flat and predictable and a large error is unlikely. During the evening
ramp, demand moves 60 MW an hour and the reserve margin is thinnest. The same MAE means very different
things in those two hours.""",
    challenge="""And there is an unwelcome possibility to check for: forecast error tends to be **largest
exactly when the system is most stressed**. Peak hours have the most volatile weather response, the
steepest ramps and the least slack — and if the model is also least accurate there, the headline MAE is
hiding the risk rather than describing it.""",
    ai_link="""So segment the error. Break it down by hour of day, by day type, and by demand level, and look
specifically at the top decile of hours. This is where a model gets accepted or rejected by the people who
have to use it.""",
    bridge=[("When can I trust it?", "Error by segment"),
            ("The peak is the risky hour", "Conditional error analysis"),
            ("Thin reserve at the peak", "Where accuracy is worth most")],
    body=[("co", r'''
t = test.copy()
t["forecast"] = pred_final
t["err"] = t.forecast - t[TARGET]
t["abs_err"] = t.err.abs()

byh = t.groupby("hour").agg(mae=("abs_err", "mean"), mean_mw=(TARGET, "mean"))
byh["pct"] = byh.mae / byh.mean_mw * 100

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Bar(x=byh.index, y=byh.mae, name="MAE (MW)", marker_color=CYAN),
              secondary_y=False)
fig.add_trace(go.Scatter(x=byh.index, y=byh.mean_mw, name="mean demand (MW)",
                         line=dict(color=AMBER, width=3)), secondary_y=True)
fig.update_layout(title="Forecast error by hour of day — worst where demand is highest",
                  xaxis_title="hour of day", template="plotly_white", height=430)
fig.update_yaxes(title_text="MAE (MW)", secondary_y=False)
fig.update_yaxes(title_text="mean demand (MW)", secondary_y=True)
fig.show()

print(f"best  hour : {byh.mae.idxmin():02d}:00   MAE {byh.mae.min():5.2f} MW "
      f"({byh.pct.min():.2f}% of demand)")
print(f"worst hour : {byh.mae.idxmax():02d}:00   MAE {byh.mae.max():5.2f} MW "
      f"({byh.loc[byh.mae.idxmax(),'pct']:.2f}% of demand)")
print(f"The evening peak is {byh.mae.max()/byh.mae.min():.1f}x harder to forecast than the trough.")

# ---- by day type and by demand level ------------------------------------
print(f"\n{'segment':>22s} {'hours':>7s} {'MAE (MW)':>9s} {'MAPE':>7s}")
for dt in ORDER:
    g = t[t.day_type == dt]
    if len(g):
        print(f"{dt:>22s} {len(g):7,d} {g.abs_err.mean():9.2f} "
              f"{(g.abs_err/g[TARGET]).mean()*100:6.2f}%")

t["band"] = pd.qcut(t[TARGET], 5, labels=["lowest 20%", "low", "middle", "high", "highest 20%"])
print()
for b, g in t.groupby("band", observed=True):
    print(f"{str(b):>22s} {len(g):7,d} {g.abs_err.mean():9.2f} "
          f"{(g.abs_err/g[TARGET]).mean()*100:6.2f}%")

peak_hours = t[t[TARGET] >= t[TARGET].quantile(0.90)]
print(f"\nTop 10% of hours by demand ({len(peak_hours)} hours, above "
      f"{t[TARGET].quantile(0.90):.0f} MW):")
print(f"   MAE {peak_hours.abs_err.mean():.2f} MW vs {t.abs_err.mean():.2f} MW overall")
print(f"   under-forecast in {(peak_hours.err < 0).mean()*100:.0f}% of them "
      f"— and under-forecasting the peak is the expensive direction.")
'''.strip("\n"))],
    built="""The error broken down by hour, day type and demand level, showing plainly that accuracy is worst in
the evening peak — the hours with the least reserve and the highest cost of being wrong.""",
    takeaway="""The forecast is least accurate exactly when the system can least afford it, so quote the peak
error, not the average.""",
)

step(
    id="worst-day", phase=9, icon="🚨", ai_icon="🔧",
    civil="The Day It Failed", ai="Residual Diagnosis",
    tech="Find the worst day in the test period and explain it from the inputs",
    site="""Every forecasting system has a worst day, and the operator will remember it long after they have
forgotten the annual MAE. Find it, plot it against what actually happened, and work out which input
misled the model.""",
    challenge="""Two possibilities look identical in the metrics and need completely different responses. If
the day was **genuinely unusual** — an unforecast weather change, an unlisted local holiday — then the
model behaved reasonably and the answer is better inputs. If the day was **ordinary and the model still
missed it**, there is a gap in the feature set.""",
    ai_link="""This is **residual diagnosis**, and it is the step that turns a score into an improvement. It
is also what makes the system trustworthy: an operator who has seen the worst case explained will use the
forecast on the other 364 days.""",
    bridge=[("What went wrong that day?", "Residual diagnosis"),
            ("Unusual day or missing feature?", "Two different fixes"),
            ("Explaining the worst case", "How the forecast earns trust")],
    body=[("co", r'''
daily = t.assign(d=t.timestamp.dt.date).groupby("d").agg(
    mae=("abs_err", "mean"), bias=("err", "mean"),
    peak=(TARGET, "max"), temp=("temperature_c", "mean"),
    rh=("humidity_pct", "mean"))
worst_day = daily.mae.idxmax()

fig = go.Figure()
day = t[t.timestamp.dt.date == worst_day]
fig.add_trace(go.Scatter(x=day.hour, y=day[TARGET], name="actual",
                         line=dict(color=CYAN, width=3.5)))
fig.add_trace(go.Scatter(x=day.hour, y=day.forecast, name="forecast",
                         line=dict(color=RED, width=2.5, dash="dash")))
fig.add_trace(go.Bar(x=day.hour, y=day.err, name="error", marker_color=AMBER, opacity=0.45))
fig.update_layout(title=f"The worst day in the test period — {worst_day}",
                  xaxis_title="hour of day", yaxis_title="MW",
                  template="plotly_white", height=440)
fig.show()

prev = worst_day - pd.Timedelta(days=1)
pd_row = daily.loc[prev] if prev in daily.index else None
med = daily.mae.median()
print(f"worst day     : {worst_day}   MAE {daily.mae.max():.1f} MW, "
      f"bias {daily.loc[worst_day,'bias']:+.1f} MW")
print(f"typical day   : MAE {med:.1f} MW   "
      f"(the worst day is {daily.mae.max()/med:.1f}x the median)")
print(f"\nconditions on {worst_day}: mean {daily.loc[worst_day,'temp']:.1f} degC, "
      f"{daily.loc[worst_day,'rh']:.0f}% RH, peak {daily.loc[worst_day,'peak']:.0f} MW")
if pd_row is not None:
    dT = daily.loc[worst_day, 'temp'] - pd_row.temp
    print(f"the day before : mean {pd_row.temp:.1f} degC, {pd_row.rh:.0f}% RH, "
          f"peak {pd_row.peak:.0f} MW   (temperature moved {dT:+.1f} degC)")

# Was it an unusual DAY, or an unusual TRANSITION? Those have different fixes.
# The lag features describe yesterday, so what hurts a lag-driven model is not an
# extreme day - it is a big day-on-day CHANGE, which is what makes yesterday a
# bad guide to today.
daily["dtemp"] = daily.temp.diff()
tq = daily.temp.rank(pct=True).loc[worst_day] * 100
pq = daily.peak.rank(pct=True).loc[worst_day] * 100
cq = daily.dtemp.abs().rank(pct=True).loc[worst_day] * 100

print(f"\nWas the day itself unusual, or was the CHANGE unusual?")
print(f"   its own mean temperature     : percentile {tq:3.0f} of the test period")
print(f"   its own peak demand          : percentile {pq:3.0f}")
print(f"   day-on-day temperature swing : percentile {cq:3.0f}  "
      f"({daily.dtemp.loc[worst_day]:+.1f} degC)")

if cq > 85:
    hi_lo = "high" if daily.loc[worst_day, "bias"] > 0 else "low"
    print("\nVerdict: the day itself was unremarkable — the TRANSITION was not.")
    print(f"   Temperature moved {daily.dtemp.loc[worst_day]:+.1f} degC overnight, so every lag feature the")
    print(f"   model relies on was describing the previous day. The forecast came in")
    print(f"   {abs(daily.loc[worst_day,'bias']):.0f} MW {hi_lo}, which is exactly what a lag-driven model does when")
    print("   yesterday stops being a good guide to today.")
    print("   The fix is not more trees. It is a feature for the day-on-day weather change.")
elif max(tq, pq) > 90:
    print("\nVerdict: a genuinely extreme day, so a larger error is defensible.")
else:
    print("\nVerdict: an ordinary day and an ordinary transition — the model simply had")
    print("   a bad one. That points at the feature set rather than at the weather.")

print(f"\nHow rare is a day this bad?")
for thr in (1.2, 1.4, 1.6):
    n = int((daily.mae > med * thr).sum())
    print(f"   days worse than {thr:.1f}x the median ({med*thr:5.1f} MW): {n:3d} of {len(daily)} "
          f"({n/len(daily)*100:4.1f}%)")
print(f"\nThe encouraging result is the one that is easy to miss: there is no")
print(f"catastrophic day. The worst day in six months is {daily.mae.max()/med:.1f}x the median,")
print(f"not 10x. A forecasting system that fails gracefully is worth more to a")
print(f"control room than one with a better average and an occasional disaster.")

fig = go.Figure(go.Histogram(x=daily.mae, nbinsx=40, marker_color=CYAN))
fig.add_vline(x=daily.mae.median(), line=dict(color=GREEN, dash="dot"),
              annotation_text=f"median {daily.mae.median():.1f}")
fig.add_vline(x=daily.mae.max(), line=dict(color=RED, dash="dash"),
              annotation_text=f"worst {daily.mae.max():.1f}")
fig.update_layout(title="Daily mean absolute error across the test period",
                  xaxis_title="daily MAE (MW)", yaxis_title="days",
                  template="plotly_white", height=380)
fig.show()
'''.strip("\n"))],
    built="""The single worst day in six months, plotted hour by hour against the actual demand and explained
from the conditions that produced it — plus how often a day that bad occurs.""",
    takeaway="""A forecasting system is judged on its worst day, so find it before the operator does.""",
)


# ---------------------------------------------- PHASE 11 · THE OPERATOR'S DESK
step(
    id="predict", phase=10, icon="🎛️", ai_icon="🖥️",
    civil="Forecast One Hour, By Hand", ai="Inference On New Conditions",
    tech="Assemble one feature row from stated conditions, call predict",
    site="""This is the system in use. The despatch engineer states the conditions for an hour — the clock,
tomorrow's forecast temperature and humidity, the day type, and what the system drew at that hour today —
and receives a demand figure with an engineering explanation attached.""",
    challenge="""A number on its own will not be trusted, and should not be. *1,042 MW* means nothing without
*220 MW above today, because it is 4 °C hotter and it is a working day*. Without the reasoning the
operator cannot tell a sensible forecast from a broken sensor feeding a confident model.""",
    ai_link="""So the inference function returns both. Change any input and the forecast moves for a reason you
can state in a sentence. Work through the scenarios below and watch which inputs move it most — this is
the same sensitivity you measured in step 24, now one hour at a time.""",
    bridge=[("State the conditions", "Assemble a feature row"),
            ("Get a demand figure", "Model inference"),
            ("And a reason for it", "Attribution the operator can check")],
    body=[("co", r'''
def forecast_hour(hour, temperature_c, humidity_pct, dayofweek=2, is_holiday=0,
                  demand_yesterday=None, month=8, explain=True):
    """Day-ahead forecast for one hour, with the reasoning attached.

    demand_yesterday: what the system drew at this same hour today. If you do not
    have it, the test-period median for this hour is used.
    """
    if demand_yesterday is None:
        demand_yesterday = float(test[test.hour == hour][TARGET].median())

    row = pd.DataFrame([{
        "hour_sin": np.sin(2*np.pi*hour/24),   "hour_cos": np.cos(2*np.pi*hour/24),
        "month_sin": np.sin(2*np.pi*month/12), "month_cos": np.cos(2*np.pi*month/12),
        "dayofweek": dayofweek, "is_weekend": int(dayofweek >= 5), "is_holiday": is_holiday,
        "temperature_c": temperature_c, "humidity_pct": humidity_pct,
        "cdd": max(temperature_c - COOL_BASE, 0.0),
        "hdd": max(HEAT_BASE - temperature_c, 0.0),
        "lag_24": demand_yesterday, "lag_48": demand_yesterday,
        "lag_168": demand_yesterday, "roll24_lag24": demand_yesterday * 0.92,
        "max24_lag24": demand_yesterday * 1.12,
    }])
    mw = float(best_model.predict(row[best_feats])[0]) - BIAS_CORRECTION

    if explain:
        change = mw - demand_yesterday
        notes = []
        if temperature_c > COOL_BASE + 8:
            notes.append(f"{temperature_c:.0f} degC drives a heavy cooling load "
                         f"({max(temperature_c-COOL_BASE,0):.0f} degree hours above the balance point)")
        elif temperature_c < HEAT_BASE:
            notes.append(f"{temperature_c:.0f} degC is below the heating balance point")
        else:
            notes.append(f"{temperature_c:.0f} degC sits in the comfort band — little weather-driven load")
        if temperature_c > COOL_BASE + 8 and humidity_pct > 65:
            notes.append(f"{humidity_pct:.0f}% humidity adds to the cooling duty on top of the heat")
        if 17 <= hour <= 21:
            notes.append("evening peak period — commercial load has not yet gone and residential has arrived")
        elif hour <= 5:
            notes.append("overnight trough — base load only")
        if is_holiday:
            notes.append("public holiday: commercial and industrial load largely absent")
        elif dayofweek >= 5:
            notes.append("weekend: reduced commercial and industrial load")
        print(f"Forecast demand at {hour:02d}:00  ->  {mw:,.0f} MW   "
              f"({change:+,.0f} MW vs the same hour today)")
        for n in notes:
            print(f"    - {n}")
    return mw

# ---- the worked example ---------------------------------------------------
print("=" * 74)
print("SCENARIO  18:00 tomorrow · 35 degC · 72% RH · Monday · not a holiday · 820 MW today")
print("=" * 74)
forecast_hour(hour=18, temperature_c=35, humidity_pct=72, dayofweek=0,
              is_holiday=0, demand_yesterday=820)

# ---- change one thing at a time ------------------------------------------
print("\n" + "=" * 74)
print("ONE VARIABLE AT A TIME, from that same starting point")
print("=" * 74)
BASECASE = dict(hour=18, temperature_c=35, humidity_pct=72, dayofweek=0,
                is_holiday=0, demand_yesterday=820)
ref = forecast_hour(**BASECASE, explain=False)
print(f"{'variation':<44s} {'MW':>8s} {'change':>9s}")
print(f"{'(base case)':<44s} {ref:8,.0f} {'':>9s}")
for label, kw in [
    ("temperature 35 -> 41 degC",        dict(temperature_c=41)),
    ("temperature 35 -> 27 degC",        dict(temperature_c=27)),
    ("humidity 72 -> 90 %",              dict(humidity_pct=90)),
    ("humidity 72 -> 40 %",              dict(humidity_pct=40)),
    ("Monday -> Sunday",                 dict(dayofweek=6)),
    ("working day -> public holiday",    dict(is_holiday=1)),
    ("yesterday 820 -> 900 MW",          dict(demand_yesterday=900)),
]:
    mw = forecast_hour(**{**BASECASE, **kw}, explain=False)
    print(f"{label:<44s} {mw:8,.0f} {mw - ref:+9,.0f}")

# NOTE: the hour is deliberately NOT varied in that table. Changing the clock
# while holding "yesterday at this hour = 820 MW" fixed describes a day that
# never happened - 04:00 never follows an 820 MW 04:00. To sweep the clock you
# have to move the lag with it, which is what the full-day forecast below does.

# ---- a whole forecast day, with the lags moving hour by hour --------------
prof = test.groupby("hour")[TARGET].median()          # what yesterday looked like
day_fc = [forecast_hour(hour=h, temperature_c=float(37.5 - 5.5*np.cos(2*np.pi*(h-4)/24)),
                        humidity_pct=74, dayofweek=0, is_holiday=0,
                        demand_yesterday=float(prof[h]), explain=False)
          for h in range(24)]

fig = go.Figure()
fig.add_trace(go.Scatter(x=list(range(24)), y=prof.values, name="yesterday (median day)",
                         line=dict(color=MUTED, width=2, dash="dot")))
fig.add_trace(go.Scatter(x=list(range(24)), y=day_fc, name="forecast: hot August Monday",
                         line=dict(color=CYAN, width=3)))
fig.update_layout(title="A full forecast day — the lags move with the clock",
                  xaxis_title="hour of day", yaxis_title="demand (MW)",
                  template="plotly_white", height=400)
fig.show()

print(f"\nForecast peak {max(day_fc):,.0f} MW at {int(np.argmax(day_fc)):02d}:00, "
      f"trough {min(day_fc):,.0f} MW at {int(np.argmin(day_fc)):02d}:00")
print(f"Steepest ramp {max(np.diff(day_fc)):,.0f} MW in the hour ending "
      f"{int(np.argmax(np.diff(day_fc)))+1:02d}:00")
'''.strip("\n"))],
    built="""A single-call forecasting function that takes stated conditions and returns a demand figure with the
engineering reasoning behind it — plus a one-variable-at-a-time table showing what moves the forecast.""",
    takeaway="""A forecast an operator can interrogate is a forecast an operator will use.""",
)

step(
    id="horizon", phase=10, icon="⏳", ai_icon="🎚️",
    civil="Two Forecasts, Two Jobs", ai="Forecast Horizon",
    tech="Day-ahead (lag_24 onwards) vs one-hour-ahead (lag_1 available)",
    site="""Utilities do not run one forecast, they run several, each matched to a decision. **Day-ahead**
drives unit commitment: which generators are synchronised tomorrow, settled tonight. **One-hour-ahead**
drives real-time balancing and automatic generation control: trimming output minute by minute.""",
    challenge="""These have different information available and therefore different achievable accuracy. The
one-hour-ahead model may use `lag_1` — the demand an hour ago — which is the single most informative
column in the dataset. Its accuracy is far better, and it is tempting to quote that number.""",
    ai_link="""It would be dishonest to. **A one-hour-ahead forecast cannot commit a generator that takes eight
hours to start.** Quote the horizon with the accuracy, always. Here both are built on the identical
pipeline, so the comparison isolates exactly what the extra hour of information is worth.""",
    bridge=[("Unit commitment", "The day-ahead horizon"),
            ("Real-time balancing", "The one-hour-ahead horizon"),
            ("Different decisions", "Different feature sets")],
    body=[("co", r'''
st_model = type(best_model)(**best_model.get_params())
st_model.fit(train[SHORT_TERM], train[TARGET])
st_bias = float(np.mean(st_model.predict(val[SHORT_TERM]) - val[TARGET].values))
st_pred = st_model.predict(test[SHORT_TERM]) - st_bias

print(f"Same model type ({BEST_NAME}), same pipeline, same test period.\n")
report("Day-ahead   (issued 23:00 for tomorrow)", y_test, pred_final)
report("1-hour-ahead (issued at the top of the hour)", y_test, st_pred)
report("Persistence  (same hour yesterday)", y_test, test.lag_24.values)

fig = go.Figure()
wk = test[(test.timestamp >= "2024-08-05") & (test.timestamp < "2024-08-12")]
i = test.index.get_indexer(wk.index)
fig.add_trace(go.Scatter(x=wk.timestamp, y=wk[TARGET], name="actual",
                         line=dict(color="#222", width=3)))
fig.add_trace(go.Scatter(x=wk.timestamp, y=pred_final[i], name="day-ahead",
                         line=dict(color=CYAN, width=2)))
fig.add_trace(go.Scatter(x=wk.timestamp, y=st_pred[i], name="1-hour-ahead",
                         line=dict(color=GREEN, width=2, dash="dot")))
fig.update_layout(title="One week in August — the same week, two forecast horizons",
                  xaxis_title="date", yaxis_title="demand (MW)",
                  template="plotly_white", height=430)
fig.show()

da = mean_absolute_error(y_test, pred_final)
st = mean_absolute_error(y_test, st_pred)
print(f"\nThe extra hour of information is worth {da - st:.1f} MW of accuracy "
      f"({(1 - st/da)*100:.0f}% lower MAE).")
print("But it arrives 23 hours too late to commit a thermal unit, which is why the")
print("day-ahead number is the one this notebook has been building all along.")
print("\nBoth are real products. They answer different questions:")
print("   day-ahead    -> what do we START tomorrow?")
print("   1-hour-ahead -> how do we TRIM what is already running?")
'''.strip("\n"))],
    built="""Two forecasts from one pipeline, differing only in what information was available when they were
issued, with the value of that extra hour measured in megawatts.""",
    takeaway="""Accuracy without a stated horizon is meaningless — the useful forecast is the one that arrives
before the decision.""",
)


# ---------------------------------------------- PHASE 12 · DESPATCH & THE CASE
step(
    id="despatch", phase=11, icon="🎚️", ai_icon="🧠",
    civil="From Forecast To Despatch Instruction", ai="Decision Support",
    tech="Net load = forecast - solar; rules over level, ramp and reserve margin",
    site="""A demand figure is not yet an instruction. The control room acts on **net load** — demand minus
what non-dispatchable generation will contribute — and on the **ramp**, the rate at which that net load
changes. With solar on the system the evening ramp gets steeper, not gentler: the sun sets as the
residential peak arrives.""",
    challenge="""The decisions are conditional on several things at once. A 1,050 MW peak with plenty of
warning is routine; the same peak arriving 90 minutes early is not. A deep overnight trough is not a
problem unless it drops below the must-run minimum, at which point the choice is to curtail renewables or
find somewhere to put the energy.""",
    ai_link="""So the forecast feeds a small set of explicit rules that produce a **recommendation with a
reason**. The rules are not machine learning and should not be — they encode the utility's own operating
policy, which must stay readable and auditable. The AI supplies the number; the policy turns it into an
action.""",
    bridge=[("Demand minus solar", "Net load, the real target"),
            ("How fast it changes", "The ramp constraint"),
            ("A reason with the instruction", "Auditable decision rules")],
    body=[("co", r'''
# ---- the generation fleet, as an operating policy ------------------------
MUST_RUN     = 430.0   # MW - minimum stable generation that cannot be shut down overnight
BASE_COMMIT  = 780.0   # MW - capacity available from committed baseload plant
PEAK_TRIGGER = 900.0   # MW - above this, peaking units must be brought to standby
RAMP_LIMIT   = 45.0    # MW/h - what committed plant can follow without extra units
SOLAR_MW     = 220.0   # MW - installed solar capacity on the system

def solar_output(hour, month=8):
    "Assumed clear-sky solar contribution, MW."
    h = np.asarray(hour, float)
    seasonal = 0.75 + 0.25 * np.sin(2 * np.pi * (month - 4) / 12)
    return SOLAR_MW * np.clip(np.sin(np.pi * (h - 6.5) / 11.0), 0, None) * seasonal

def despatch(forecast_mw, net_mw, ramp_mw, hour):
    "Return (instruction, reason). This is operating policy, not a model."
    if net_mw > PEAK_TRIGGER:
        return ("PREPARE PEAK LOAD UNITS",
                f"net load {net_mw:,.0f} MW exceeds the {PEAK_TRIGGER:,.0f} MW committed-plant "
                f"trigger — bring peaking units to standby now")
    if ramp_mw > RAMP_LIMIT:
        return ("INCREASE GENERATION CAPACITY",
                f"net load rising {ramp_mw:,.0f} MW/h, above the {RAMP_LIMIT:,.0f} MW/h that "
                f"committed plant can follow — schedule additional ramping capacity")
    if net_mw < MUST_RUN:
        return ("CHARGE ENERGY STORAGE",
                f"net load {net_mw:,.0f} MW is below the {MUST_RUN:,.0f} MW must-run minimum — "
                f"absorb the surplus rather than backing plant down")
    if net_mw < MUST_RUN * 1.12 and solar_output(hour) > 60:
        return ("REDUCE RENEWABLE CURTAILMENT",
                f"solar contributing {solar_output(hour):,.0f} MW into a light net load — "
                f"shift flexible demand into this window instead of curtailing")
    return ("MAINTAIN CURRENT GENERATION",
            f"net load {net_mw:,.0f} MW and ramp {ramp_mw:+,.0f} MW/h are both inside "
            f"committed-plant limits")

# ---- run the policy over one forecast day --------------------------------
DAY = "2024-08-08"
day = t[t.timestamp.dt.date == pd.Timestamp(DAY).date()].sort_values("hour")
fc = day.forecast.values
sol = solar_output(day.hour.values, month=8)
net = fc - sol
ramp = np.diff(net, prepend=net[0])

fig = go.Figure()
fig.add_trace(go.Scatter(x=day.hour, y=fc, name="forecast demand",
                         line=dict(color=CYAN, width=3)))
fig.add_trace(go.Scatter(x=day.hour, y=net, name="net load (demand - solar)",
                         line=dict(color=RED, width=3)))
fig.add_trace(go.Scatter(x=day.hour, y=sol, name="solar output",
                         fill="tozeroy", line=dict(color=AMBER, width=1)))
fig.add_hline(y=PEAK_TRIGGER, line=dict(color=RED, dash="dash"),
              annotation_text="peaking trigger")
fig.add_hline(y=MUST_RUN, line=dict(color=MUTED, dash="dot"),
              annotation_text="must-run minimum")
fig.update_layout(title=f"Forecast day {DAY} — demand, solar, and the net load the control room despatches",
                  xaxis_title="hour of day", yaxis_title="MW",
                  template="plotly_white", height=460)
fig.show()

print(f"{'hour':>5s} {'forecast':>9s} {'solar':>7s} {'net':>8s} {'ramp':>7s}   instruction")
print("-" * 108)
for k in range(24):
    ins, why = despatch(fc[k], net[k], ramp[k], k)
    print(f"{k:02d}:00 {fc[k]:9,.0f} {sol[k]:7,.0f} {net[k]:8,.0f} {ramp[k]:+7,.0f}   {ins}")

print()
print("The evening: solar falls to zero while demand is still climbing, so the NET")
print(f"load ramps far harder than demand does. Peak demand ramp "
      f"{np.diff(fc).max():,.0f} MW/h; peak NET load ramp {ramp.max():,.0f} MW/h.")
print("That gap is the whole operational argument for forecasting net load, not demand.")

print(f"\nExample instructions in full:")
for k in [4, 12, 19]:
    ins, why = despatch(fc[k], net[k], ramp[k], k)
    print(f"\n   {k:02d}:00  {ins}")
    print(f"          {why}")
'''.strip("\n"))],
    built="""A despatch layer that converts each forecast hour into a named instruction with a stated reason,
running on net load so the solar-driven evening ramp appears where the control room actually sees it.""",
    takeaway="""The forecast supplies the number; auditable operating policy turns it into an instruction.""",
)

step(
    id="reserve", phase=11, icon="💰", ai_icon="📐",
    civil="Reserve, And The Cost Of Being Wrong", ai="Quantifying The Benefit",
    tech="Reserve sized from the error distribution; cost from the asymmetric penalties",
    site="""Forecast error does not disappear — it is **carried as operating reserve**. The utility holds
enough spare synchronised capacity to cover the difference between what it scheduled and what arrives.
Reserve is not free: it means units running at part load, at a worse heat rate, producing electricity
that has not been sold.""",
    challenge="""And the two directions do not cost the same. **Under-forecasting** means buying at balancing
prices or starting peaking plant, and at the limit shedding load. **Over-forecasting** means committed
plant backed down, burning fuel inefficiently. The first costs several times the second, which is why a
forecast that is unbiased matters as much as one that is accurate.""",
    ai_link="""So the benefit is calculated, not claimed. Size the reserve from the **95th percentile of the
error distribution** under each forecasting method, price the residual imbalance with the asymmetric
penalties, and compare. This is the number that justifies the project.""",
    bridge=[("Error becomes reserve", "The error distribution sets the MW"),
            ("Short costs more than long", "Asymmetric loss"),
            ("Is it worth doing?", "The measured business case")],
    body=[("co", r'''
# Unit costs. These are the assumptions the whole business case rests on, so they
# are stated here rather than buried, and they are deliberately CONSERVATIVE.
# The imbalance figures are SPREADS - the extra cost over the day-ahead schedule -
# not full energy prices, because the energy itself was going to be bought anyway.
RESERVE_COST = 6.0     # $/MW/h  - holding spinning reserve (part-load heat rate + opportunity)
UNDER_COST   = 25.0    # $/MWh   - balancing-market premium when short
OVER_COST    = 8.0     # $/MWh   - part-load fuel waste when long

def business_case(name, pred):
    e = np.asarray(pred) - y_test
    reserve = float(np.percentile(np.abs(e), 95))
    hours = len(e)
    under = float(np.clip(-e, 0, None).sum()) * UNDER_COST
    over  = float(np.clip(e, 0, None).sum()) * OVER_COST
    imbalance_yr = (under + over) / hours * 8760
    reserve_yr = reserve * 8760 * RESERVE_COST
    return dict(method=name, reserve_mw=reserve,
                reserve_cost=reserve_yr, imbalance_cost=imbalance_yr,
                total=reserve_yr + imbalance_yr)

cases = pd.DataFrame([
    business_case("Persistence (today's method)", test.lag_24.values),
    business_case(f"{BEST_NAME} (day-ahead)", pred_final),
]).set_index("method")

display(cases.round(0))

pers_c, ml_c = cases.iloc[0], cases.iloc[1]
saving = pers_c.total - ml_c.total

fig = go.Figure()
fig.add_trace(go.Bar(x=cases.index, y=cases.reserve_cost, name="holding reserve",
                     marker_color=AMBER))
fig.add_trace(go.Bar(x=cases.index, y=cases.imbalance_cost, name="imbalance energy",
                     marker_color=RED))
fig.update_layout(title="Annual cost of forecast error — what the utility pays either way",
                  yaxis_title="$ per year", barmode="stack",
                  template="plotly_white", height=420)
fig.show()

print(f"Reserve needed to cover 95% of hours:")
print(f"   persistence : {pers_c.reserve_mw:6.1f} MW")
print(f"   {BEST_NAME:<12s}: {ml_c.reserve_mw:6.1f} MW")
print(f"   released    : {pers_c.reserve_mw - ml_c.reserve_mw:6.1f} MW of synchronised capacity")
print()
print(f"Annual cost of forecast error:")
print(f"   persistence : ${pers_c.total:12,.0f}")
print(f"   {BEST_NAME:<12s}: ${ml_c.total:12,.0f}")
print(f"   saving      : ${saving:12,.0f} per year")

# ---- sanity-check against the published rule of thumb --------------------
pers_mape = [s for s in SCORES if s["model"] == "Persistence: same hour yesterday"][0]["MAPE"]
peak_gw = clean.demand_mw.max() / 1000
d_mape = pers_mape - TEST_FINAL["MAPE"]
lo, hi = peak_gw * d_mape * 0.3e6, peak_gw * d_mape * 1.5e6
print(f"\nSanity check. The published rule of thumb is roughly $0.3-1.5 M per year,")
print(f"per GW of peak demand, per percentage point of MAPE improvement.")
print(f"   peak demand         : {peak_gw:.2f} GW")
print(f"   MAPE improvement    : {pers_mape:.2f}% -> {TEST_FINAL['MAPE']:.2f}%  "
      f"({d_mape:.2f} points)")
print(f"   rule-of-thumb range : ${lo:,.0f} - ${hi:,.0f} /yr")
print(f"   this calculation    : ${saving:,.0f} /yr")

print()
if saving > hi:
    print("This calculation lands ABOVE the published range, and the reason matters.")
    print("Those figures come from utilities replacing an already-competent statistical")
    print("forecast with a better one - a fraction of a MAPE point. Here the comparison")
    print(f"is against naive persistence, a {d_mape:.1f} point jump no real utility has")
    print("left to make. Read this number as the value of HAVING a forecasting system,")
    print("not as the gain from upgrading one.")
elif saving < lo:
    print("This calculation lands BELOW the published range - the unit costs assumed")
    print("here are conservative. Treat it as a floor.")
else:
    print("This calculation lands inside the published range.")
print()
print("Either way, the point of the step is the method, not the total: the benefit was")
print("computed from the measured error distribution and three stated unit costs, any")
print("of which a regulator can challenge line by line. That is what makes it a")
print("business case rather than a percentage on a slide.")
'''.strip("\n"))],
    built="""The business case, computed from the measured error distribution rather than asserted: megawatts of
reserve released, dollars of imbalance avoided, and an independent cross-check against the industry rule of
thumb.""",
    takeaway="""Better forecasting pays for itself in released reserve, and the amount can be calculated rather
than claimed.""",
)

step(
    id="dashboard", phase=11, icon="🖥️", ai_icon="📊",
    civil="The Utility Operations Dashboard", ai="The Deployed System",
    tech="Forecast, actual, error and instruction on one screen",
    site="""Everything from the previous 32 steps, on one screen, in the form the control room would
actually see it: tomorrow's forecast curve, how yesterday's forecast performed, the current accuracy, and
the despatch instruction for each hour.""",
    challenge="""A dashboard that only shows the forecast invites over-trust. The operator needs the recent
track record beside it — if the model has been running 40 MW low all week, that is something to act on,
and it will not show up in an annual MAE.""",
    ai_link="""So the deployed system reports **forecast, outturn, error and instruction together**, with the
rolling accuracy in view. That combination is what makes it a tool rather than an oracle, and it is where
this project ends.""",
    bridge=[("Tomorrow's schedule", "The forecast curve"),
            ("How did yesterday go?", "Rolling accuracy"),
            ("What do I do about it?", "The instruction")],
    body=[("co", r'''
WINDOW = t[(t.timestamp >= "2024-08-05") & (t.timestamp < "2024-08-12")].copy()
WINDOW["solar"] = solar_output(WINDOW.hour.values, month=8)
WINDOW["net"] = WINDOW.forecast - WINDOW.solar

fig = make_subplots(
    rows=3, cols=2,
    specs=[[{"colspan": 2}, None], [{"colspan": 2}, None],
           [{"type": "indicator"}, {"type": "indicator"}]],
    row_heights=[0.42, 0.28, 0.30], vertical_spacing=0.10,
    subplot_titles=("Forecast vs outturn — the operating week",
                    "Hourly forecast error", "", ""))

fig.add_trace(go.Scatter(x=WINDOW.timestamp, y=WINDOW[TARGET], name="actual",
                         line=dict(color="#222", width=3)), row=1, col=1)
fig.add_trace(go.Scatter(x=WINDOW.timestamp, y=WINDOW.forecast, name="forecast",
                         line=dict(color=CYAN, width=2, dash="dash")), row=1, col=1)
fig.add_trace(go.Scatter(x=WINDOW.timestamp, y=WINDOW.net, name="net load",
                         line=dict(color=AMBER, width=1.5)), row=1, col=1)
fig.add_trace(go.Bar(x=WINDOW.timestamp, y=WINDOW.err, name="error (MW)",
                     marker_color=[RED if e < 0 else GREEN for e in WINDOW.err]),
              row=2, col=1)

fig.add_trace(go.Indicator(
    mode="gauge+number", value=TEST_FINAL["MAPE"],
    title={"text": "forecast MAPE (%)"},
    gauge={"axis": {"range": [0, 8]}, "bar": {"color": CYAN},
           "steps": [{"range": [0, 2], "color": "#d8f5dd"},
                     {"range": [2, 4], "color": "#fdf0d5"},
                     {"range": [4, 8], "color": "#fbdcd9"}],
           "threshold": {"line": {"color": RED, "width": 4}, "value": pers_mape}}),
    row=3, col=1)
fig.add_trace(go.Indicator(
    mode="number+delta", value=ml_c.reserve_mw,
    title={"text": "reserve required (MW)"},
    delta={"reference": pers_c.reserve_mw, "increasing": {"color": RED},
           "decreasing": {"color": GREEN}}),
    row=3, col=2)

fig.update_layout(height=900, template="plotly_white",
                  title_text="Utility Operations Dashboard — short-term load forecasting")
fig.show()

# ---- the summary the control room reads ----------------------------------
tomorrow = t[t.timestamp.dt.date == pd.Timestamp("2024-08-09").date()].sort_values("hour")
tf = tomorrow.forecast.values
tsol = solar_output(tomorrow.hour.values, month=8)
tnet = tf - tsol
tramp = np.diff(tnet, prepend=tnet[0])
pk = int(np.argmax(tf))

print("=" * 74)
print(f"  DESPATCH SUMMARY  —  forecast day {tomorrow.timestamp.dt.date.iloc[0]}")
print("=" * 74)
print(f"  Forecast peak demand   : {tf.max():,.0f} MW at {pk:02d}:00")
print(f"  Forecast minimum       : {tf.min():,.0f} MW at {int(np.argmin(tf)):02d}:00")
print(f"  Peak net load          : {tnet.max():,.0f} MW at {int(np.argmax(tnet)):02d}:00")
print(f"  Steepest net load ramp : {tramp.max():,.0f} MW/h")
print(f"  Reserve to carry (P95) : {ml_c.reserve_mw:,.0f} MW")
print(f"  Forecast accuracy      : MAE {TEST_FINAL['MAE']:.1f} MW, MAPE {TEST_FINAL['MAPE']:.2f}%")
print("-" * 74)
def hour_spans(hrs):
    "Collapse a sorted hour list into contiguous runs, e.g. [0,1,2,7] -> 00:00-02:00, 07:00"
    runs, start, prev = [], hrs[0], hrs[0]
    for h in hrs[1:] + [None]:
        if h != prev + 1:
            runs.append(f"{start:02d}:00" if start == prev else f"{start:02d}:00-{prev:02d}:00")
            start = h
        prev = h
    return ", ".join(runs)

acts = {}
for k in range(24):
    ins, why = despatch(tf[k], tnet[k], tramp[k], k)
    acts.setdefault(ins, []).append(k)
for ins, hrs in acts.items():
    print(f"  {ins:<30s} {hour_spans(hrs)}  ({len(hrs)} h)")
print("=" * 74)
print("  Recommendation only. The despatch engineer commits the schedule.")
print("=" * 74)
'''.strip("\n"))],
    built="""The whole project on one screen: the operating week's forecast against outturn, the hourly error,
the accuracy gauge against the old method, the reserve released, and the day's despatch instructions.""",
    takeaway="""A deployed forecast shows its own track record beside its prediction, which is what makes it a
tool rather than an oracle.""",
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
# ⚡ AI for Electricity Load Forecasting
## Machine Learning for Electrical and Power Systems Engineers

> You are not here to learn Artificial Intelligence. You are here to solve a **power system operations
> problem** — one a person genuinely cannot solve by hand, for reasons that are arithmetic rather than
> effort. AI turns up in the middle of it, because the engineering requires it. Not before.

---

## 1 · The engineering problem

It is 23:00 on a Sunday in the control room of a regional distribution utility. Roughly 1.2 million
consumers, a peak demand near 1,180 MW.

The despatch engineer has to decide **what generation runs tomorrow**. Not tomorrow morning — now. A large
thermal unit takes **six to twelve hours** to synchronise, so tomorrow evening's peak has to be committed
tonight, against a demand nobody has measured yet.

**Electricity cannot be stored economically at grid scale.** Generation must equal demand continuously.
There is no buffer, no inventory, no catching up later.

Get it wrong in either direction and it costs:

- **Under-forecast** → not enough generation committed. Buy at balancing-market prices, start expensive
  peaking plant, and in the worst case shed load.
- **Over-forecast** → too much committed. Units run at part load, burning fuel at a worse heat rate to
  produce electricity nobody needs.

And the target never holds still:

- Demand falls to about **480 MW** at 04:00 and reached **1,181 MW** on the hottest August evening in the record.
- Between 17:00 and 19:00 it can rise **more than 60 MW in a single hour**.
- Air-conditioning load depends on temperature **and** humidity — but humidity only matters once it is hot.
- Saturdays differ from weekdays, Sundays differ from Saturdays, and public holidays differ from all of them.

One despatch engineer is responsible for **8,760 of these numbers a year**, each needed before the hour it
describes. That is not a diligence problem. It is arithmetic.

---

## 2 · What we are going to build

A **short-term load forecasting system**. Four parts:

| | Part | What it does |
|---|---|---|
| 📟 | **The historical record** | Two years of hourly demand from the SCADA historian, joined to temperature, humidity and the calendar — inspected, cleaned and repaired along the time axis. |
| 🔧 | **Engineered features** | Cooling and heating degree hours, cyclical clock encodings, and lagged demand. Power system knowledge, turned into columns a model can use. |
| 🧠 | **Four regression models** | Linear Regression, Random Forest, Gradient Boosting and XGBoost, all judged on weeks they have never seen. |
| 🔔 | **A despatch recommendation** | Not a number on its own. *Forecast 1,042 MW at 19:00 tomorrow — above the committed-plant trigger, so bring the peaking units to standby.* |

> **Be clear about the goal, because it is not automation.** Nothing here replaces the despatch engineer
> and nothing here commits a generator by itself. The operator stays in charge, stays accountable, and
> still owns security of supply. The system does the one thing a person cannot: **it produces every hourly
> forecast, consistently, weighting every driver at once, and states how wrong it is likely to be.** The
> goal is not an unmanned control room. It is a **cheaper, more reliable** one.

---

## 3 · The engineering workflow

Not a syllabus, and not chapters. **One utility, two years of history**, in the order a real forecasting
project runs — twelve phases. Every AI concept in this notebook hangs off one of them.

| Phase | In the power system | Steps |
|---|---|---|
{phase_rows()}

---

## 4 · Engineering → AI, the whole map

Spend a minute on this table before starting. **Every AI concept in this notebook is a power system
engineering activity you already understand.** Not 'similar to'. The same thing, given a different name by
a different profession.

Read down the left column and you have described a load forecasting project. Read down the right column and
you have described a complete machine learning pipeline. **They are the same column.**

| ⚡ Power system engineering process | → | 🤖 The AI process that solves it | Phase |
|---|:-:|---|:-:|
{mapping_rows()}

---

## The one idea this notebook proves

> **Machine Learning learns historical demand patterns and environmental conditions to accurately forecast
> future electricity demand, helping engineers operate the power grid more efficiently.**

Do not take that on trust. Step {[s['id'] for s in STEPS].index('reserve')+1} measures it, in megawatts of
reserve and in dollars.
""")

md(r"""
---

## Setup

In Colab everything below is already installed. If you are running elsewhere, uncomment the install line.
Charts are Plotly, so they are interactive — hover, zoom, and toggle series from the legend.

XGBoost is used in one step. That cell detects whether it is present and skips cleanly if it is not, so
every other cell runs anywhere.
""")

co(r"""
# !pip install numpy pandas scikit-learn plotly xgboost

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

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

> The power system engineering activity on this page is also, exactly, the AI concept
> **{s['ai']}**. Here is why.

## Part 1 · In the power system

{s['site'].strip()}

## Part 2 · The engineering challenge

{s['challenge'].strip()}
""")

    md(rf"""
## Part 3 · Where the AI comes in

{s['ai_link'].strip()}

| ⚡ **In the power system** | → | 🤖 **In the AI** |
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
  SCADA HISTORIAN ──┐
  demand, hourly    │
                    ├─► inspect ─► clean ─► FEATURE ENGINEERING ─┐
  WEATHER DESK ─────┤   (voids,    (time-    degree hours        │
  temperature, RH   │    freezes,  wise      cyclical clock      │
                    │    dupes)    fill)     lags 24/48/168      │
  CALENDAR ─────────┘                                            │
  day type, holidays                                             │
                                                                 ▼
                              ┌──────────────────────────────────────────┐
                              │  THE FORECAST GATE                       │
                              │  issued 23:00 → lag_1 is not available   │
                              └──────────────────┬───────────────────────┘
                                                 ▼
   chronological split ─► TRAIN ─► 4 REGRESSORS ─► validate ─► select ─► bias
   train / val / test                                                 correction
                                                 │
                                                 ▼
                          DAY-AHEAD DEMAND FORECAST (MW, per hour)
                                                 │
                        ┌────────────────────────┴────────────────────────┐
                        ▼                                                 ▼
              NET LOAD = demand − solar                          FORECAST AUDIT
              ramp, peak, trough                                 MAE · RMSE · MAPE · R²
                        │                                        error by hour, worst day
                        ▼                                                 │
              DESPATCH INSTRUCTION  ◄───────────────────────────────────┘
              maintain / increase / peakers / storage / curtailment
                        │
                        ▼
              RESERVE RELEASED  ·  $ SAVED PER YEAR
```

## What was built

| Stage | Method | Output |
|---|---|---|
| Repair the historian export | Time-wise interpolation, fault voiding | A continuous hourly record |
| Encode the clock | Cyclical sine/cosine features | Midnight adjacent to 23:00 |
| Encode the weather | Cooling and heating degree hours | The balance points, handed over |
| Encode the memory | Lag 24/48/168 and rolling day statistics | A time-series problem |
| Enforce the horizon | The 23:00 forecast gate | A deployable feature set |
| Forecast demand | Linear / Random Forest / Gradient Boosting / XGBoost | MW for every hour of tomorrow |
| Rank the drivers | Permutation importance | What the forecast depends on |
| Check the physics | Response sweeps | The temperature–humidity interaction, recovered |
| Correct the drift | Validation-measured bias correction | An unbiased forecast |
| Audit it | MAE, RMSE, MAPE, R², error by segment | Accuracy where it matters |
| Turn it into an action | Net load and operating policy | A despatch instruction with a reason |
| Justify the spend | Reserve sizing from the error distribution | MW released and $ per year |

## The three things worth remembering

1. **Historical demand and weather → Machine Learning.** The engineer names the features — degree hours,
   day type, lagged demand — and the model weights them. On sixteen named columns, gradient boosting beats
   linear regression by a wide margin, and the reason is a single physical fact: humidity only matters when
   it is already hot.
2. **The horizon is part of the answer.** A one-hour-ahead forecast is far more accurate and cannot commit
   a generator that takes eight hours to start. Accuracy quoted without a horizon is not accuracy.
3. **Power System Operator + AI.** The model produces 8,760 forecasts a year and states how wrong it is
   likely to be. A despatch engineer decides what runs, signs the schedule, and remains accountable for
   security of supply.

## Where the engineering discipline showed up

Six moments in this notebook were engineering judgements, not machine learning:

- **Interpolating along time** instead of filling with the column median, which would have taught the model
  that 03:00 is a busy hour.
- **Voiding the frozen meter** rather than trusting values that individually passed every range check.
- **Applying the forecast gate** and deleting `lag_1`, the single most informative column in the dataset,
  because it will not exist at 23:00.
- **Splitting chronologically** into three periods, and measuring exactly how much a shuffled split would
  have flattered the result.
- **Testing whether scaling helps** instead of applying it as a ritual — it changes nothing for these models.
- **Diagnosing the low drift as load growth** and correcting it from validation data, rather than tuning a
  constant until the test score improved.

Those six are what separate a model from a load forecasting project.

---

## Where to take it next

- **Retrain on a rolling window.** The bias correction in step 25 is a patch; refitting every few weeks is
  the cure.
- **Forecast per feeder, not per system.** Aggregate demand is the easiest series in the network; the
  distribution level is where the errors and the value both are.
- **Add a probabilistic forecast.** Quantile regression gives P10/P50/P90 instead of one number, and
  reserve sizing then falls straight out of the model.
- **Bring in the real drivers you have and this notebook did not.** Large industrial consumers' schedules,
  planned outages, and local event calendars are usually worth more than another model.
""")





nb = new_notebook(cells=cells, metadata={
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"},
    "colab": {"provenance": []},
})
nbf.validate(nb)
with open("Electricity_Load_Forecasting_AI.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"wrote Electricity_Load_Forecasting_AI.ipynb — {len(cells)} cells, "
      f"{sum(1 for c in cells if c.cell_type == 'code')} code, {len(STEPS)} steps")
