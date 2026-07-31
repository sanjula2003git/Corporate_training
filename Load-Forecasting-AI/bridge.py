"""
bridge.py - the Power-Systems-Engineering -> AI teaching scaffold.
=================================================================
This module does not teach any NEW concept and it does not render any new
model, animation or asset. Every technical illustration lives in app.py /
story.py. This module wraps each stage renderer in a five-part structure so an
Electrical / Power Systems Engineering student always sees, on every page:

    Power System Engineering   the control-room context   (bridge.open_page)
    The Challenge              why the manual way runs out (bridge.open_page)
    AI Connection              + the bridge figure         (bridge.open_page)
    Technical Idea             <- the EXISTING renderer, untouched
    Key Takeaway               one sentence                (bridge.close_page)
    In the Notebook            where it lives              (bridge.close_page)

Text is deliberately short and professional. Short sentences, active voice, no
drama. The visuals carry the page; the text supports them.

COLOR IS A TEACHING DEVICE. Amber is ALWAYS the grid / power system world.
Cyan is ALWAYS the AI world. Violet is ALWAYS the technical process.

The display language here is a CONTROL ROOM MIMIC PANEL: busbar rules, alarm
banners, monospace SCADA readouts and a despatch-schedule progress rail. It is
deliberately distinct from the sibling apps' looks.
"""
import streamlit as st
import plotly.graph_objects as go

# ---------------------------------------------------------------- palette
BG, PANEL = "#0b0f14", "#131a22"
CIVIL = "#ffb74d"      # amber  - the grid / power system engineering
AISIDE = "#4fc3f7"     # cyan   - the AI
TECH = "#ba68c8"       # violet - the technical process
GREEN, RED = "#66bb6a", "#ef5350"
MUTED, TEXT = "#8b98a9", "#e6edf3"

MIMIC = "#101820"      # mimic-panel fill
INK = "#080c11"        # deep readout background
EDGE = "#25313d"       # hairline borders
MONOF = "ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', monospace"

_CSS = """
<style>
.stApp {
  background-image: repeating-linear-gradient(
     0deg, rgba(255,255,255,.016) 0 1px, transparent 1px 4px);
}
hr { border-color:#25313d !important; }
[data-testid="stCaptionContainer"] p { font-family:%(MONO)s; letter-spacing:.02em; }
.stButton>button {
  border-radius:3px; border:1px solid #33424f; background:#131a22;
  text-transform:uppercase; letter-spacing:.08em; font-size:12px; font-weight:600;
}
.stButton>button:hover { border-color:#ffb74d; color:#ffb74d; }
[data-testid="stMetric"] {
  background:#101820; border:1px solid #25313d; border-left:3px solid #4fc3f7;
  border-radius:3px; padding:10px 12px;
}
[data-testid="stMetricValue"] { font-family:%(MONO)s; }

/* busbar section header */
.bus-row { display:flex; align-items:center; gap:11px; margin:24px 0 12px; }
.bus-tag { font-family:%(MONO)s; font-size:12px; font-weight:700; border:1px solid;
  padding:2px 8px; border-radius:3px; letter-spacing:.05em; white-space:nowrap; }
.bus-label { font-family:%(MONO)s; text-transform:uppercase; letter-spacing:.15em;
  font-size:13px; font-weight:700; white-space:nowrap; }
.bus-line { flex:1; height:3px; border-top:1px solid #25313d; border-bottom:1px solid #25313d; }

/* mimic panel block */
.mimic { position:relative; background:#101820; border:1px solid #25313d;
  border-left:4px solid #ffb74d; padding:14px 18px; color:#e6edf3;
  font-size:16px; line-height:1.65; margin:2px 0; border-radius:0 3px 3px 0; }
.mimic.ai   { border-left-color:#4fc3f7; }
.mimic.tech { border-left-color:#ba68c8; }
.mimic.warn { border-left-color:#ef5350; }
.mimic.ok   { border-left-color:#66bb6a; }

/* SCADA status strip */
.scada { font-family:%(MONO)s; background:#080c11; border:1px solid #25313d;
  padding:8px 14px; font-size:12px; letter-spacing:.06em; color:#8b98a9;
  border-radius:3px; }
.scada b { color:#ffb74d; }

/* despatch schedule rail */
.rail { display:flex; flex-wrap:wrap; align-items:center; gap:5px; background:#080c11;
  border:1px solid #25313d; border-radius:3px; padding:9px 12px; }
.raillab { font-family:%(MONO)s; font-size:11px; letter-spacing:.12em; color:#8b98a9;
  margin-right:4px; }
.blk { font-family:%(MONO)s; font-size:11px; padding:2px 7px; border:1px solid #25313d;
  color:#3b4652; border-radius:2px; }
.blk.done { color:#ffb74d; border-color:#5a4a2a; }
.blk.cur  { background:#ffb74d; color:#080c11; border-color:#ffb74d; font-weight:700; }

.step-card { font-family:%(MONO)s; text-align:center; border:1px solid #ffb74d;
  border-radius:3px; background:#080c11; padding:6px 4px; font-size:11px;
  color:#8b98a9; line-height:1.5; }
.step-card b { color:#ffb74d; font-size:13px; }

/* landing brief */
.brief { position:relative; border:1px solid #25313d; background:#080c11;
  border-top:3px solid #ffb74d; padding:22px 26px; border-radius:0 0 3px 3px; }
.brief-bar { font-family:%(MONO)s; font-size:12px; letter-spacing:.16em;
  color:#ffb74d; margin-bottom:8px; }
.card-ico { display:inline-flex; align-items:center; justify-content:center;
  width:40px; height:40px; border:1px solid #25313d; border-radius:3px;
  font-size:22px; margin-bottom:8px; background:#080c11; }
.muted { color:#8b98a9; font-size:13px; }
.substep { font-family:%(MONO)s; color:#8b98a9; font-size:13px; }
</style>
""" % {"MONO": MONOF}


def inject_css():
    """Load the control-room display language once. Call after st.set_page_config."""
    st.markdown(_CSS, unsafe_allow_html=True)


def _bus_header(tag, label, color):
    st.markdown(
        f"<div class='bus-row'>"
        f"<span class='bus-tag' style='color:{color};border-color:{color}'>{tag}</span>"
        f"<span class='bus-label' style='color:{color}'>{label}</span>"
        f"<span class='bus-line'></span></div>", unsafe_allow_html=True)


# ============================================================================
# THE ENGINEERING WORKFLOW
# The phases of a utility's load forecasting project. Every AI concept hangs
# off one of them. The last one is the ledger the work gets judged by.
# ============================================================================
PHASES = [
    ("The Grid At Work",         "Generation must equal demand, and demand never holds still."),
    ("One Hour Of Demand",       "A metered hour becomes a row somebody else has to trust."),
    ("Instrumenting The Network", "The SCADA and weather export lands, and gets checked."),
    ("Reading The Demand",       "Look at the load curve before modelling it."),
    ("Feature Engineering",      "Turn power system knowledge into columns."),
    ("The Forecast Gate",        "What is known at the moment the forecast is issued."),
    ("The Bar To Clear",         "A naive forecast is not zero. Beat it or go home."),
    ("The Forecasting Models",   "Four regressors on the same honest problem."),
    ("Reading The Model",        "What drives the forecast, and where it is biased."),
    ("The Forecast Audit",       "Every claim checked on weeks the model never saw."),
    ("The Operator's Desk",      "Change the conditions, watch the forecast move."),
    ("Despatch & The Case",      "Reserve, fuel, and the cost of being wrong."),
]


# ============================================================================
# THE STEPS  (one per page; len(STEPS) is the count - do not hardcode it)
#   civil / ai   - the two names of the same idea (amber name, cyan name)
#   tech         - what is actually computed (violet)
#   site         - Power System Engineering. NO AI in this text. 2-4 sentences.
#   challenge    - The Challenge. Why the manual way runs out of road.
#   ai_link      - AI Connection. Why this AI concept is therefore required.
#   takeaway     - Key Takeaway. ONE sentence.
#   notebook     - In the Notebook. Where this lives in the Colab notebook.
#   contributes  - In the Notebook. What this step contributes to the system.
# ============================================================================
STEPS = [

# ------------------------------------------------ PHASE 1 - THE GRID AT WORK
dict(
    id='control-room', phase=0, short='The grid',
    civil='A Monday Evening On The Grid', ai='Why Load Forecasting Exists',
    civil_icon='🏭', ai_icon='🤖',
    tech='One day of demand, and the ramp the generators have to follow',
    civil_bullets=['1.2 M consumers', 'Peak near 1,180 MW', 'No storage, no buffer'],
    ai_bullets=['Predict, do not react', 'Hours ahead of need', 'Every hour, all year'],
    site="""A regional distribution utility. Roughly 1.2 million consumers, a peak demand near 1,180 MW, and a
control room staffed around the clock. Its job is one sentence long: generation must equal demand, every
second of every day.""",
    challenge="""Demand never holds still. It falls to about 480 MW at four in the morning and reached 1,181 MW on
the worst August evening of the last two years. Between five and seven in the evening it can rise more
than 60 MW in a single hour. Large thermal plant takes six to twelve hours to start, so what runs tomorrow
evening is decided tonight.""",
    ai_link="""That is not a control problem, it is a prediction problem. The operator does not need a faster
switch. They need to know, tonight, what demand will be at 19:00 tomorrow, closely enough to commit the
right generators to it.""",
    notebook="""Step 1. The demand model: a daily shape, a cooling term, a heating term.""",
    contributes="""The requirement the whole system is measured against. If the schedule is not better, it failed.""",
    takeaway="""Demand is a moving target set by the clock and the weather, and generation must be committed
hours before it arrives.""",
),
dict(
    id='enter-ai', phase=0, short='Operator + AI',
    civil='The Operator And The Forecast', ai='What AI Is Actually For Here',
    civil_icon='👷', ai_icon='🛰️',
    tech='8,760 hourly numbers a year, each needed before the hour arrives',
    civil_bullets=['Same control room', 'Same despatch authority', 'Nobody is replaced'],
    ai_bullets=['8,760 forecasts a year', 'None of them skipped', 'With a stated error bar'],
    site="""Nothing about the control room changes. The same operators, the same despatch instructions, the same
statutory responsibility for security of supply. What changes is that a demand number for every hour of
tomorrow is on the desk at 23:00 tonight.""",
    challenge="""Is this here to replace the operator? No, and it is worth being precise about why. A model sees
demand, temperature and a calendar. It does not know a substation is on outage, that a steel consumer has
scheduled a shutdown, or that a cyclone warning has been issued. It cannot be held accountable when the
lights go out.""",
    ai_link="""So the split is fixed here and holds for the rest of the course: the model forecasts, the operator
despatches. The system's output is a recommendation with a stated accuracy.""",
    notebook="""Step 2. No modelling — the argument, and the arithmetic behind it.""",
    contributes="""Defines the system's output: a recommendation to an engineer, never an automatic commitment.""",
    takeaway="""The forecast informs the despatch decision; the operator still makes it and still owns it.""",
),

# --------------------------------------------- PHASE 2 - ONE HOUR OF DEMAND
dict(
    id='one-hour', phase=1, short='One hour',
    civil='One Hour, One Row', ai='Data Collection',
    civil_icon='⏱️', ai_icon='🗄️',
    tech='One metered hour -> one row of conditions + one demand value',
    civil_bullets=['SCADA logs the MW', 'Weather desk logs degC, RH', 'The calendar does the rest'],
    ai_bullets=['Conditions are features', 'Demand is the target', 'One hour is one row'],
    site="""At the top of every hour the SCADA system records system demand in megawatts. The weather desk records
temperature and humidity at the reference station. The calendar supplies the date, the day of the week and
whether it is a public holiday. That is one hour, closed and filed.""",
    challenge="""Whoever reads that row next year does not get the hour. Not the first genuinely hot evening of the
season, not the cricket final that kept the city indoors. They get eight numbers. If the meter read low,
nothing in the row says so.""",
    ai_link="""For a model that limitation is absolute. It never stands in the control room and cannot re-run the
hour. One row — conditions in, demand out — is all it gets, so a wrong row produces a confident wrong
forecast with nothing to flag it.""",
    notebook="""Step 3. The `INPUTS` and `TARGET` lists, and one hour decomposed into base, cooling and heating.""",
    contributes="""Every forecast is computed from a row like this. It is the model's only contact with the network.""",
    takeaway="""The row is the model's entire hour; a wrong row gives a wrong forecast with nothing to flag it.""",
),
dict(
    id='drivers', phase=1, short='What moves demand',
    civil='What Actually Moves Demand', ai='Feature Selection',
    civil_icon='🔀', ai_icon='📐',
    tech='Sweep each driver across its real range, measure the megawatts it moves',
    civil_bullets=['Clock, weather, calendar', 'Which is biggest?', 'Measure, do not guess'],
    ai_bullets=['One-at-a-time sweep', 'Megawatts moved', 'Expected importance'],
    site="""Before collecting two years of anything, decide what is worth collecting. A power engineer already
knows the candidates: time of day, temperature, humidity, day of week, holidays, and the recent history of
the load itself. What is not obvious is their relative size.""",
    challenge="""Intuition ranks these badly. Everyone knows air conditioning matters; few would guess that humidity
is worth almost nothing until the temperature passes the balance point. Guessing wrong means instrumenting
the wrong thing for two years.""",
    ai_link="""So measure it. Hold everything at a reference condition, sweep one driver across its operating range,
and record the megawatts it moves. That is a sensitivity study — feature selection done before a single
model exists.""",
    notebook="""Step 4. The `sweeps` dictionary and the tornado chart of megawatts moved.""",
    contributes="""Justifies the feature list, and gives the first sighting of the temperature-humidity interaction.""",
    takeaway="""Every driver is worth collecting, but one of them only matters in combination with another.""",
),

# ------------------------------------------- PHASE 3 - INSTRUMENTING
dict(
    id='load-data', phase=2, short='The export',
    civil='The SCADA Export Arrives', ai='Loading The Dataset',
    civil_icon='🗂️', ai_icon='📥',
    tech='Two years of hourly records, exactly as the historian exports them',
    civil_bullets=['Two years, hourly', '17,544 hours', 'A CSV, not a dataset'],
    ai_bullets=['17,544 labelled rows', 'Nothing trusted yet', 'Check shape and types'],
    site="""You ask the data team for the last two years. What arrives is a CSV: hourly demand from the SCADA
historian, joined to hourly temperature and humidity from the weather desk, with the calendar filled in.
17,544 rows, one per hour.""",
    challenge="""An export is not a dataset. Historians drop samples when a comms link fails, meters freeze and
repeat their last value, and a joined feed can arrive with duplicated timestamps. None of that announces
itself. The row count looks right, so it looks fine.""",
    ai_link="""A model trained on a broken export does not error. It trains happily, reports a good score, and
forecasts wrongly forever. Loading is a commissioning check.""",
    notebook="""Step 5. `make_history()` and `damage_export()` — the file as the historian hands it over.""",
    contributes="""The raw material. Every later step either repairs it or builds on the repair.""",
    takeaway="""A plausible-looking export is not a verified one; the row count is the first thing that lies.""",
),
dict(
    id='inspect', phase=2, short='Bad readings',
    civil='Finding The Bad Readings', ai='Data Inspection',
    civil_icon='🔎', ai_icon='🩺',
    tech='Missing counts, repeated values, impossible magnitudes, duplicate timestamps',
    civil_bullets=['Dropouts', 'Frozen meters', 'RTU fault codes'],
    ai_bullets=['Missing values', 'Constant runs', 'Outliers and duplicates'],
    site="""Before anything is repaired, find out what is wrong. In a metering context that means four checks:
dropouts the historian never received, frozen channels repeating a last good value, out-of-range values
from an RTU fault, and duplicate timestamps from an export job that ran twice.""",
    challenge="""You cannot eyeball 17,568 rows, and each fault hides differently. The frozen meter is the dangerous
one: every individual value it reports is perfectly plausible and passes any range check you could write.""",
    ai_link="""So each fault needs its own detector. This step diagnoses only — nothing is repaired here. Separating
diagnosis from repair is what stops you quietly deleting a real demand event because it looked
inconvenient.""",
    notebook="""Step 6. Four detectors, including the longest-identical-run check that catches the frozen meter.""",
    contributes="""The fault list the cleaning step acts on. Nothing is repaired that was not first diagnosed.""",
    takeaway="""The frozen meter is the one that matters — every value it reports is individually plausible.""",
),
dict(
    id='clean', phase=2, short='Repair',
    civil='Repairing The Record', ai='Data Cleaning',
    civil_icon='🧹', ai_icon='🛠️',
    tech='Drop duplicates, void the faults, interpolate in TIME - not with a median',
    civil_bullets=['Void what is wrong', 'Fill along the curve', 'Drop what is too long'],
    ai_bullets=['NaN beats a wrong value', 'Time-wise interpolation', 'No median fill'],
    site="""Now repair, and the choices are engineering judgements. Duplicated rows are dropped. Fault-code spikes
and the frozen block are voided — marked missing, because a wrong number is worse than no number. Then the
gaps are filled.""",
    challenge="""How you fill them matters more than it looks. The reflex is the column median. For a load series that
is wrong: the median of the whole column sits far above the overnight demand, so a gap at 03:00 gets
filled with a value well over a hundred megawatts higher than the network was actually drawing.""",
    ai_link="""A time series must be filled along time, not from the column as a whole. Linear interpolation between
the surrounding hours respects the load curve. Gaps too long to interpolate — a three-day outage — are
dropped instead.""",
    notebook="""Step 7. `interpolate(method="time", limit=6)`, and the median-fill error quantified.""",
    contributes="""A continuous hourly record. Every feature and every model downstream assumes it.""",
    takeaway="""Fill a time series along time; a column median would have taught the model that 03:00 is busy.""",
),

# ------------------------------------------- PHASE 4 - READING THE DEMAND
dict(
    id='profile', phase=3, short='Load curve',
    civil='The Daily Load Curve', ai='Exploratory Data Analysis',
    civil_icon='📈', ai_icon='🔍',
    tech='Mean demand by hour and day type, and the load duration curve',
    civil_bullets=['Overnight trough', 'Morning rise', 'Evening peak'],
    ai_bullets=['The pattern to learn', 'Day type as a driver', 'Where error is costly'],
    site="""The load curve is the most-looked-at chart in any control room. Average demand by hour and the routine
appears: the overnight trough, the morning rise, the midday plateau, the evening peak. Split it by day
type and three distinct curves appear where there seemed to be one.""",
    challenge="""Averages hide what planners care about — the extremes. The system is built for the highest hour of
the year, not the average one, and that hour is expensive: plant running a few dozen hours a year is paid
for all year.""",
    ai_link="""So look two ways. The load curve shows the routine a model must reproduce. The load duration curve —
every hour sorted highest to lowest — shows how few hours the expensive top end is needed for.""",
    notebook="""Step 8. Load curve by day type, the hour-by-month heatmap, and the load duration curve.""",
    contributes="""Establishes what the forecast has to get right, and where being wrong costs most.""",
    takeaway="""The average hour is easy and cheap; the project exists for the few hundred hours near the peak.""",
),
dict(
    id='weather-link', phase=3, short='Demand vs temp',
    civil='Demand Against Temperature', ai='Non-Linearity And Interaction',
    civil_icon='🌡️', ai_icon='📉',
    tech='Demand vs temperature, and the humidity effect inside temperature bands',
    civil_bullets=['The V-shaped curve', 'Two balance points', 'Humidity, but only when hot'],
    ai_bullets=['A non-linear response', 'Slope changes at a threshold', 'A feature interaction'],
    site="""Plot demand against temperature and the classic shape appears: a V, or in a hot climate a hockey stick.
Demand falls to the comfort zone, flattens, then climbs steeply as air conditioning comes on. The two bends
are the balance points.""",
    challenge="""Two things defeat a simple model. The shape is not a straight line — the slope above the cooling
balance point steepens as it climbs. And humidity's effect is not separable: worth tens of megawatts on a
38 degC evening, almost nothing on a 20 degC one.""",
    ai_link="""That second property is an interaction, and it decides which model wins. A model that adds up its
inputs independently cannot represent 'more humid means more, only when it is already hot'. A tree can,
because it splits on temperature first and humidity second.""",
    notebook="""Step 9. The scatter with both balance points, and the humidity table controlled for hour of day.""",
    contributes="""The single clearest reason the tree models beat linear regression later.""",
    takeaway="""Demand responds to temperature non-linearly, and to humidity only in combination with it.""",
),
dict(
    id='calendar-link', phase=3, short='Day type',
    civil='Working Days, Weekends, Holidays', ai='Categorical Drivers',
    civil_icon='📅', ai_icon='🏷️',
    tech='Demand by day type, and one average week hour by hour',
    civil_bullets=['Offices follow a week', 'Households do not', 'Holidays look like Sundays'],
    ai_bullets=['A categorical feature', 'A rare class, flagged', 'Not a number line'],
    site="""The calendar moves demand as reliably as the weather. Offices, schools and industry follow a working
week; households do not. A public holiday empties commercial and industrial load while leaving residential
load intact, which is why a holiday looks like a Sunday.""",
    challenge="""These are categories, not quantities. 'Sunday' is not seven times 'Monday'. And holidays are rare —
about eleven days a year — so a model sees very few examples of the day type that behaves most unusually.""",
    ai_link="""The fix is to hand the model the distinction rather than hoping it infers it: an explicit is_weekend
flag, an explicit is_holiday flag, and day of week alongside. Naming the category is engineering knowledge
the model would otherwise have to rediscover from very few examples.""",
    notebook="""Step 10. Demand by day type, and the 168-hour average week.""",
    contributes="""Three calendar features, and the reason the rarest of them is explicitly flagged.""",
    takeaway="""Day type is a category with real megawatts attached, and the rarest category matters most.""",
),

# ------------------------------------------- PHASE 5 - FEATURE ENGINEERING
dict(
    id='cyclical', phase=4, short='The clock',
    civil='Midnight Is Next To 23:00', ai='Cyclical Encoding',
    civil_icon='🕐', ai_icon='🔄',
    tech='Map the hour onto a circle: hour_sin and hour_cos',
    civil_bullets=['The clock is a circle', 'The integer is a line', 'Midnight is not far'],
    ai_bullets=['sin and cos of the hour', 'Adjacent in feature space', 'Same for the month'],
    site="""Hour of day is written 0 to 23, and that numbering has a defect every engineer notices and most models
do not: 23:00 and 00:00 are one hour apart, but the numbers are 23 apart. The same is true of December and
January.""",
    challenge="""Left alone, this distorts the overnight ramp. A model reading the hour as a plain number believes the
jump from 23:00 to 00:00 is the largest time gap in the day, when it is the smallest — and that is the
trough the system passes through every single night.""",
    ai_link="""The standard fix is to put the hour back on the circle it came from. Represent each hour by its
position on a clock face: hour_sin and hour_cos. Two numbers instead of one, and now midnight sits next to
23:00 exactly as it does in time.""",
    notebook="""Step 11. The four cyclical columns, and the plain-vs-circular distance comparison.""",
    contributes="""Removes an artificial cliff at midnight and at the year boundary.""",
    takeaway="""Encode a cycle as a cycle, or the model will believe midnight is the far side of the day.""",
),
dict(
    id='degree-hours', phase=4, short='Degree hours',
    civil='Cooling And Heating Degree Hours', ai='Domain Feature Engineering',
    civil_icon='🌡️', ai_icon='🧮',
    tech='cdd = max(T - 24, 0) and hdd = max(16 - T, 0)',
    civil_bullets=['The standard energy unit', 'Zero in the comfort band', 'A known threshold'],
    ai_bullets=['A rectified feature', 'Physics handed over', 'Not rediscovered from data'],
    site="""Energy engineers do not correlate demand with raw temperature. They use degree hours: how far the
temperature sits above the cooling balance point or below the heating one, and for how long. It is the
standard unit of weather-driven energy demand.""",
    challenge="""Raw temperature carries the wrong message below the balance point. Between 16 and 24 degC neither
heating nor cooling runs, so a change there moves almost no demand — yet the raw number keeps changing,
telling the model something is happening when nothing is.""",
    ai_link="""So compute what the engineer would compute. cdd is zero through the comfort band and rises only when
cooling actually starts; hdd does the same for heating. That is domain feature engineering — encoding a
known physical threshold so the model does not have to find it.""",
    notebook="""Step 12. The `cdd` and `hdd` columns, and the correlation before and after.""",
    contributes="""Two features carrying a physical threshold, which is why the models need less data to find it.""",
    takeaway="""Give the model the balance point rather than making it rediscover the laws of your own field.""",
),
dict(
    id='lags', phase=4, short='Memory',
    civil='Demand Remembers Itself', ai='Lag And Rolling Features',
    civil_icon='🔁', ai_icon='⏮️',
    tech='lag_1, lag_24, lag_48, lag_168 and the previous day mean and peak',
    civil_bullets=['Today looks like yesterday', 'This Monday like last', 'The recent level matters'],
    ai_bullets=['lag_24, lag_168', 'Rolling mean and max', 'Now a time series'],
    site="""Today's load curve looks a great deal like yesterday's. Same consumers, same shift patterns, same
appliances. Ask a control engineer for tomorrow's 19:00 demand with no tools and they will quote today's
19:00 figure, adjusted a little — and be closer than you expect.""",
    challenge="""That knowledge is not in the dataset. The calendar and weather columns describe the conditions of an
hour; nothing tells the model what the system was actually drawing recently. And the recent level carries
what the weather columns cannot: a new industrial consumer, a tariff change, load growth.""",
    ai_link="""So put the history in as columns. A lag feature is the demand n hours ago. A rolling feature summarises
a window — yesterday's mean and peak. This is what turns a table of conditions into a time-series
forecasting problem.""",
    notebook="""Step 13. The autocorrelation plot, then the five lag columns and two rolling columns.""",
    contributes="""The strongest features in the whole model, and the reason the next phase exists.""",
    takeaway="""The strongest single predictor of tomorrow's demand is what the system drew today.""",
),

# ------------------------------------------- PHASE 6 - THE FORECAST GATE
dict(
    id='gate', phase=5, short='The 23:00 gate',
    civil='What Is Known At 23:00', ai='Preventing Data Leakage',
    civil_icon='🚪', ai_icon='⛔',
    tech='For a forecast issued at 23:00, lag L is usable only if L >= hours ahead',
    civil_bullets=['Issued 23:00 tonight', 'Covers 00:00-23:00 tomorrow', 'Tomorrow has not happened'],
    ai_bullets=['An information cut-off', 'lag_1 is unavailable', 'The legal feature set'],
    site="""Fix the operational moment precisely, because everything depends on it. The forecast is issued at 23:00
tonight and covers 00:00 to 23:00 tomorrow. At that moment the latest measured demand is the hour ending
23:00 today. Tomorrow's weather comes from the met forecast.""",
    challenge="""Now check the lag features against that clock. To forecast 13:00 tomorrow you are standing 14 hours
away from it. lag_1 for that hour means 12:00 tomorrow, which has not happened. It is in the dataset only
because the dataset was assembled after the fact.""",
    ai_link="""Using it anyway is data leakage, and it is the most common way a forecasting project fails. The model
scores brilliantly and cannot be deployed, because in production the column is empty. The rule is
arithmetic: lag L is usable only if L is at least the number of hours ahead.""",
    notebook="""Step 14. The availability table, and the `DAY_AHEAD` / `SHORT_TERM` / `NO_LAGS` feature sets.""",
    contributes="""The feature set the utility can actually run. Everything after this is honest about deployment.""",
    takeaway="""A feature that will not exist at forecast time is not a feature, however well it scores here.""",
),
dict(
    id='split', phase=5, short='Split by time',
    civil='Split By Time, Never At Random', ai='Chronological Train/Val/Test',
    civil_icon='✂️', ai_icon='📆',
    tech='Train to April 2024, validate May-June, test July-December',
    civil_bullets=['A forecast runs forwards', 'Judge on later weeks', 'Never on shuffled hours'],
    ai_bullets=['Split on a date', 'Three periods, not two', 'Test opened once'],
    site="""The model must be judged on weeks it has never seen — and in forecasting, 'never seen' has a direction.
A forecast is always made forwards. So the split is a date, not a random selection: train on the earliest
period, validate on the next, test on the most recent.""",
    challenge="""The reflex is a shuffled split, and in a time series it is quietly catastrophic. Shuffling puts 14:00
on 3 August in training and 15:00 on 3 August in test. Those hours share the weather, the day type and
nearly the same demand.""",
    ai_link="""So split chronologically, and use three periods. Train fits the models. Validation chooses between them
and measures the bias correction — decisions must be made on data the test set never touches. Test is
opened once, at the end.""",
    notebook="""Step 15. The three periods, and the shuffled-vs-chronological comparison measured.""",
    contributes="""The evaluation discipline that makes every later number believable.""",
    takeaway="""Shuffling a time series tests the model on hours it has already been shown.""",
),
dict(
    id='scaling', phase=5, short='Scaling',
    civil='Different Units, Different Magnitudes', ai='Feature Scaling',
    civil_icon='📏', ai_icon='⚖️',
    tech='StandardScaler, and an honest test of whether it changes anything',
    civil_bullets=['MW, degC, flags', 'Wildly different scales', 'Does it matter?'],
    ai_bullets=['Trees do not care', 'Nor does plain OLS', 'Comparable coefficients'],
    site="""The sixteen features are in wildly different units. Demand lags are in hundreds of megawatts,
temperature in tens of degrees, degree hours in single digits, and the flags are 0 or 1. 'One unit' means
something different in every column.""",
    challenge="""The standard advice is 'always scale', repeated so often that almost nobody checks whether it is true
for the model they are using. For ordinary least squares it is not — rescaling a column rescales its
coefficient by the reciprocal. For decision trees it is not either.""",
    ai_link="""So test it rather than assume it. Scaling matters for regularised models, for gradient descent, and for
distance-based methods. For these four it changes nothing about accuracy — but standardised coefficients
are comparable, which tells you which driver moves demand most per standard deviation.""",
    notebook="""Step 16. The unscaled-vs-scaled MAE comparison, and the standardised coefficient chart.""",
    contributes="""A habit of measuring instead of ritualising, and a readable ranking of the linear drivers.""",
    takeaway="""Scale features when the model needs it, not as a ritual — and check which case you are in.""",
),

# ------------------------------------------- PHASE 7 - THE BAR TO CLEAR
dict(
    id='persistence', phase=6, short='The baseline',
    civil='What The Old Method Achieves', ai='The Naive Baseline',
    civil_icon='📋', ai_icon='🎯',
    tech='Forecast = same hour yesterday, and = same hour last week',
    civil_bullets=['The method in use today', 'Same hour, recent day', 'Adjust for weather by eye'],
    ai_bullets=['The benchmark to beat', 'Not zero error', 'Beat it or do not deploy'],
    site="""Before machine learning, this forecast was made by hand, and the method was sound: take the same hour on
a comparable recent day and adjust it for the weather. On a stable system it works. It is called a
persistence forecast.""",
    challenge="""It has two failure modes and no way to handle either. It cannot see a weather change — if today was
30 degC and tomorrow is 39 degC, yesterday's figure is badly wrong. And it cannot handle a day-type change,
so Monday is a poor guide to a public holiday.""",
    ai_link="""This is the bar. Any model that does not beat persistence is not worth deploying, whatever its R².
Scoring the naive method first is what keeps everything afterwards honest.""",
    notebook="""Step 17. Three naive baselines scored, and the day persistence fails hardest.""",
    contributes="""The reference every later score is quoted against. Absolute numbers mean nothing without it.""",
    takeaway="""The benchmark is not zero error, it is the method the utility already uses.""",
),

# ------------------------------------------- PHASE 8 - THE MODELS
dict(
    id='linear', phase=7, short='Linear',
    civil='One Coefficient Per Driver', ai='Linear Regression',
    civil_icon='📐', ai_icon='➗',
    tech='demand = w1*f1 + w2*f2 + ... + b, fitted by least squares',
    civil_bullets=['MW per degree', 'MW per Sunday', 'Add them up'],
    ai_bullets=['One weight per feature', 'Effects that add', 'Readable and checkable'],
    site="""The first model is the one an engineer would write by hand: give every driver a coefficient in megawatts
per unit, multiply, and add. So many MW per cooling degree hour, so many MW off for a Sunday, so many MW
carried over from yesterday's level.""",
    challenge="""Its assumption is that the drivers add up independently, and this network has already shown that they
do not. Humidity's effect depends on temperature. A single coefficient per feature cannot express 'it
depends'.""",
    ai_link="""Fit it anyway, for two reasons. It sets a transparent floor you can check against engineering sense. And
when the tree models beat it, the size of the gap measures how much of this problem is non-linear.""",
    notebook="""Step 18. `fit_and_validate`, and the coefficients read back as engineering quantities.""",
    contributes="""The interpretable floor, and the yardstick for how much non-linearity is worth.""",
    takeaway="""Linear regression is the floor — readable, checkable, and blind to anything that depends on
something else.""",
),
dict(
    id='forest', phase=7, short='Forest',
    civil='Many Operators, One Answer', ai='Random Forest Regression',
    civil_icon='🌳', ai_icon='🌲',
    tech='Hundreds of decision trees on random subsets, averaged',
    civil_bullets=['Above 32 degC?', 'A weekday?', 'Yesterday above 900 MW?'],
    ai_bullets=['A decision tree', 'Many, on random subsets', 'Averaged'],
    site="""A different way to forecast: ask a series of yes/no questions. Is it above 32 degC? Is it a weekday? Was
yesterday's peak above 900 MW? Each answer narrows the range until a demand figure remains. That is a
decision tree, and it is close to how an experienced operator reasons.""",
    challenge="""One tree is unstable. Grown deep it memorises the training years including the measurement noise;
grown shallow it is too crude to capture the evening peak. Neither depth is right.""",
    ai_link="""A random forest removes the choice. Grow hundreds of trees, each on a random subset of rows and columns,
and average. The errors largely cancel; the shared signal survives. And because each tree splits on one
feature and then another, it represents interactions natively.""",
    notebook="""Step 19. The 300-tree forest, plus one depth-3 tree printed in full.""",
    contributes="""The first model that can express 'it depends', and the mechanism made visible.""",
    takeaway="""Trees split on one driver and then another, which is how they capture 'it depends'.""",
),
dict(
    id='boosting', phase=7, short='Boosting',
    civil='Correcting The Last Attempt', ai='Gradient Boosting Regression',
    civil_icon='🪜', ai_icon='📶',
    tech='Each new tree is fitted to the errors the previous trees left behind',
    civil_bullets=['Make a rough forecast', 'See where it was wrong', 'Build a stage to fix it'],
    ai_bullets=['Fit the residuals', 'Small steps, many stages', 'Rate and depth restrain it'],
    site="""A forest builds every tree independently and averages. Boosting works the way a commissioning team works:
make a first rough forecast, look at where it was wrong, and build the next stage specifically to fix those
errors. Repeat several hundred times.""",
    challenge="""The risk is the opposite of the forest's. Because every stage chases the leftover errors, a boosted
model eventually starts fitting the measurement noise, and its forecasts on new weeks get worse while its
training score keeps improving.""",
    ai_link="""Two controls hold it back. The learning rate shrinks each correction so no stage dominates, and the tree
depth limits how intricate each correction can be. Together they are why gradient boosting is usually the
strongest model on tabular problems.""",
    notebook="""Step 20. The staged validation-error curve, so overfitting would be visible if it happened.""",
    contributes="""Usually the winning model, and a picture of what 'more trees' actually buys.""",
    takeaway="""Boosting improves by fitting its own leftover errors, which is powerful and needs restraining.""",
),
dict(
    id='xgboost', phase=7, short='XGBoost',
    civil='The Production Implementation', ai='XGBoost Regression',
    civil_icon='⚙️', ai_icon='🚀',
    tech='Regularised gradient boosting with column and row subsampling',
    civil_bullets=['Retrained weekly', 'Hundreds of feeders', 'Speed is a constraint'],
    ai_bullets=['Explicit regularisation', 'Row/column subsampling', 'The vendor standard'],
    site="""XGBoost is gradient boosting rebuilt for production use, and it is what most utilities and forecasting
vendors actually run. Same idea — stages of trees correcting previous stages — with the engineering
tightened up.""",
    challenge="""Two problems remain in plain boosting. It can still overfit, and across several years of hourly data on
many feeders it is slow to fit and slow to re-fit. A system retrained weekly cannot afford either.""",
    ai_link="""XGBoost adds explicit regularisation in the objective, penalising complexity directly rather than relying
on depth limits, plus row and column subsampling so each tree sees a different slice. Usually a small
accuracy gain and a large speed gain.""",
    notebook="""Step 21. The guarded import, and a timing comparison against the sklearn implementation.""",
    contributes="""The implementation a utility would actually deploy, and the reason why.""",
    takeaway="""XGBoost is the same idea as gradient boosting, regularised and engineered to be retrained often.""",
),
dict(
    id='compare', phase=7, short='Shoot-out',
    civil='Which Forecast Would You Sign?', ai='Model Selection',
    civil_icon='🏁', ai_icon='📊',
    tech='Rank on validation, choose one, then open the test set once',
    civil_bullets=['One number goes on the schedule', 'And a reason for it', 'Not four forecasts'],
    ai_bullets=['Select on validation', 'Report on test', 'Test opened once'],
    site="""Four models, one validation period, one decision. The despatch engineer does not want four forecasts —
they want the one number that goes on the schedule, and a reason for choosing it.""",
    challenge="""The temptation is to fit all four, score them all on test, and report the best. That is selection on the
test set, and it quietly turns the test score into an optimistic one: you have used the test data to make a
decision, so it is no longer untouched.""",
    ai_link="""So the order matters. Rank on validation, pick the winner, then open the test set once. Whatever it says
is what you report. An ablation with the lag features removed then measures what the time-series columns
are actually worth.""",
    notebook="""Step 22. The validation table, the single test opening, and the no-lags ablation.""",
    contributes="""One selected model, and the first sighting of the bias that the next phase diagnoses.""",
    takeaway="""Choose the model on validation and open the test set once, or the score you report is not the
score you will get.""",
),

# ------------------------------------------- PHASE 9 - READING THE MODEL
dict(
    id='importance', phase=8, short='Importance',
    civil='Which Drivers Carry The Forecast', ai='Feature Importance',
    civil_icon='🔬', ai_icon='📶',
    tech='Permutation importance: shuffle one column, measure the damage',
    civil_bullets=['Why is it high?', 'Which input drives it?', 'Answer, or be overridden'],
    ai_bullets=['Break one input', 'Measure the damage', 'On unseen weeks'],
    site="""A forecast the operator cannot interrogate is a forecast they will override. The first question in any
control room is why — why is tomorrow evening 70 MW above today's, and which input is driving that.""",
    challenge="""A tree ensemble has hundreds of trees and thousands of splits. There is no coefficient to read. The
importances that come free with the model count how often each feature was split on, which over-credits
continuous features simply for having many distinct values.""",
    ai_link="""Permutation importance avoids that. Shuffle one column so it carries no information, and measure how
much the error grows. It is computed on validation, so it reflects what the model relies on to forecast
unseen weeks — but it is an average, and averages hide drivers that only matter at the extremes.""",
    notebook="""Step 23. `permutation_importance` on validation, with the two cautions about how to read it.""",
    contributes="""The explanation layer. Without it the forecast is a number nobody in the control room trusts.""",
    takeaway="""A feature matters if breaking it breaks the forecast — but an average can hide a driver that
only bites at the extremes.""",
),
dict(
    id='sensitivity', phase=8, short='Response curves',
    civil='Does It Agree With The Physics?', ai='Model Response Curves',
    civil_icon='🎚️', ai_icon='📈',
    tech='Hold everything fixed, sweep one input, plot the model response',
    civil_bullets=['Sweep the input', 'Check the response', 'Against known physics'],
    ai_bullets=['A partial dependence sweep', 'Validation, not scoring', 'The interaction recovered'],
    site="""Importance says which inputs matter. It does not say how. An engineer commissioning any instrument sweeps
its input across the range and checks the response against what the physics says it should be. A
forecasting model deserves the same treatment.""",
    challenge="""A model can be accurate on average and still wrong where it matters. If its demand falls as temperature
rises above 35 degC — because few such hours existed in training — it fails precisely on the days the
system is most stressed, while its overall MAE looks fine.""",
    ai_link="""So sweep it. Fix a representative hour, vary temperature across the operating range, and plot what the
model predicts, at two humidity levels. If it has genuinely learnt the interaction, the two curves diverge
as it gets hotter. That is the physics, recovered from data.""",
    notebook="""Step 24. The `response()` sweep, at 35% and 85% humidity, with the divergence tabulated.""",
    contributes="""Confirmation that the model learnt the physics rather than a coincidence in the training years.""",
    takeaway="""A model that is accurate on average can still be wrong where it matters; sweep it and look.""",
),
dict(
    id='bias', phase=8, short='The drift',
    civil='Why The Forecast Drifts Low', ai='Distribution Shift',
    civil_icon='📉', ai_icon='🧭',
    tech='Measure the mean residual on validation, subtract it from the forecast',
    civil_bullets=['Demand grows 3.5%/yr', 'The relationship goes stale', 'Wrong in one direction'],
    ai_bullets=['Distribution shift', 'A level correction', 'Measured on validation'],
    site="""The model is not just less accurate on the test period — it is consistently low, by roughly the same
amount every hour. A random error is tolerable. A systematic one is a different kind of defect, and in this
direction it is the expensive one.""",
    challenge="""The cause is ordinary: demand in the licence area is growing at about 3.5% a year. The model was fitted
mostly on 2023, and 2023's relationship between conditions and megawatts no longer holds in late 2024.
Nothing in the feature set encodes the year.""",
    ai_link="""This is distribution shift, and the standard remedy is a level correction: measure the mean residual on
the most recent data before the forecast period — validation — and subtract it. Critically it is measured
on validation and applied to test. Measuring it on test would be marking your own homework.""",
    notebook="""Step 25. Train/validation/test bias, the failed trend-fitting alternative, and the correction.""",
    contributes="""An unbiased forecast, and the reason utilities retrain every few weeks rather than once.""",
    takeaway="""A forecast wrong in the same direction every hour has a cause worth finding, not a constant
worth tuning.""",
),

# ------------------------------------------- PHASE 10 - THE AUDIT
dict(
    id='metrics', phase=9, short='Metrics',
    civil='How Wrong, In Megawatts', ai='Regression Metrics',
    civil_icon='📑', ai_icon='🧾',
    tech='MAE, RMSE, MAPE and R2 - and what each one is for',
    civil_bullets=['Not a score out of one', 'Megawatts', 'More than one number'],
    ai_bullets=['MAE for the operator', 'RMSE for reserve', 'MAPE for benchmarking'],
    site="""The despatch engineer needs the forecast's accuracy in the units they schedule generation in. Not a score
out of one — megawatts. And more than one number, because 'wrong by 15 MW every hour' and 'right all month
except one 400 MW evening' are completely different operational risks.""",
    challenge="""Each metric hides something. MAE is the average miss, easy to act on, but treats a 200 MW error as ten
times a 20 MW one when operationally it is far worse. RMSE squares the errors so large misses dominate.
MAPE is comparable across utilities but exaggerates errors during the low overnight hours.""",
    ai_link="""So report all four and know what each is for. MAE for the operator, RMSE for the reserve calculation
because it is driven by the large errors reserve exists to cover, MAPE for benchmarking, R² for the
modeller. None of them is 'the' accuracy.""",
    notebook="""Step 26. All four metrics, the percentile table, and the comparison against persistence.""",
    contributes="""The percentile table the reserve calculation in the last phase is built on.""",
    takeaway="""Report the average miss, the large misses and the percentage — they answer different questions.""",
),
dict(
    id='error-profile', phase=9, short='When it fails',
    civil='When Is It Wrong?', ai='Error Analysis By Segment',
    civil_icon='🕰️', ai_icon='🔎',
    tech='Break the error down by hour of day, day type and demand level',
    civil_bullets=['Flat overnight', 'Steep at the peak', 'Reserve is thinnest then'],
    ai_bullets=['Error by segment', 'Conditional analysis', 'Where accuracy is worth most'],
    site="""An average error across 4,416 hours tells the operator nothing about when to trust the forecast.
Overnight, demand is flat and predictable. During the evening ramp it moves 60 MW an hour and the reserve
margin is thinnest. The same MAE means very different things in those two hours.""",
    challenge="""And there is an unwelcome possibility to check for: forecast error tends to be largest exactly when the
system is most stressed. If the model is least accurate at the peak, the headline MAE is hiding the risk
rather than describing it.""",
    ai_link="""So segment the error — by hour, by day type, by demand level — and look specifically at the top decile of
hours. This is where a model gets accepted or rejected by the people who have to use it.""",
    notebook="""Step 27. Error by hour against mean demand, by day type, by demand quintile, and the top decile.""",
    contributes="""The honest statement of when the forecast can be trusted, which is what the control room asks for.""",
    takeaway="""The forecast is least accurate exactly when the system can least afford it, so quote the peak
error, not the average.""",
),
dict(
    id='worst-day', phase=9, short='Worst day',
    civil='The Day It Failed', ai='Residual Diagnosis',
    civil_icon='🚨', ai_icon='🔧',
    tech='Find the worst day and explain it from the inputs',
    civil_bullets=['Every system has one', 'The operator remembers it', 'Explain it first'],
    ai_bullets=['Residual diagnosis', 'Unusual day or missing feature?', 'Two different fixes'],
    site="""Every forecasting system has a worst day, and the operator will remember it long after they have
forgotten the annual MAE. Find it, plot it against what actually happened, and work out which input misled
the model.""",
    challenge="""Two possibilities look identical in the metrics and need different responses. If the day was genuinely
unusual, the model behaved reasonably and the answer is better inputs. If the day was ordinary and the
model still missed it, there is a gap in the feature set.""",
    ai_link="""This is residual diagnosis, and it turns a score into an improvement. The right question is not 'was the
day extreme' but 'was the CHANGE extreme' — a lag-driven model is hurt by a sharp day-on-day swing, not by
a hot day it has seen before.""",
    notebook="""Step 28. The worst day plotted hour by hour, and the day-on-day change tested against the day itself.""",
    contributes="""The named next improvement: a feature for the day-on-day weather change.""",
    takeaway="""A forecasting system is judged on its worst day, so find it before the operator does.""",
),

# ------------------------------------------- PHASE 11 - THE OPERATOR'S DESK
dict(
    id='predict', phase=10, short='Forecast one hour',
    civil='Forecast One Hour, By Hand', ai='Inference On New Conditions',
    civil_icon='🎛️', ai_icon='🖥️',
    tech='Assemble one feature row from stated conditions, call predict',
    civil_bullets=['State the conditions', 'Get a demand figure', 'And a reason'],
    ai_bullets=['Assemble a feature row', 'Model inference', 'Attribution the operator can check'],
    site="""This is the system in use. The despatch engineer states the conditions for an hour — the clock,
tomorrow's forecast temperature and humidity, the day type, and what the system drew at that hour today —
and receives a demand figure with an engineering explanation attached.""",
    challenge="""A number on its own will not be trusted, and should not be. '1,042 MW' means nothing without 'because
it is 4 degC hotter and it is a working day'. Without the reasoning the operator cannot tell a sensible
forecast from a broken sensor feeding a confident model.""",
    ai_link="""So the inference function returns both. Change any input and the forecast moves for a reason you can
state in a sentence. This is the same sensitivity measured earlier, now one hour at a time.""",
    notebook="""Step 29. `forecast_hour()`, the one-variable-at-a-time table, and a full forecast day.""",
    contributes="""The deliverable an operator actually touches. Everything before it exists to make this trustworthy.""",
    takeaway="""A forecast an operator can interrogate is a forecast an operator will use.""",
),
dict(
    id='horizon', phase=10, short='Horizon',
    civil='Two Forecasts, Two Jobs', ai='Forecast Horizon',
    civil_icon='⏳', ai_icon='🎚️',
    tech='Day-ahead (lag_24 onwards) vs one-hour-ahead (lag_1 available)',
    civil_bullets=['Day-ahead: what to START', '1-hour: what to TRIM', 'Different decisions'],
    ai_bullets=['Different information', 'Different accuracy', 'Quote the horizon'],
    site="""Utilities do not run one forecast, they run several, each matched to a decision. Day-ahead drives unit
commitment: which generators are synchronised tomorrow, settled tonight. One-hour-ahead drives real-time
balancing and automatic generation control.""",
    challenge="""These have different information available and therefore different achievable accuracy. The
one-hour-ahead model may use lag_1, the most informative column in the dataset. Its accuracy is far better,
and it is tempting to quote that number.""",
    ai_link="""It would be dishonest to. A one-hour-ahead forecast cannot commit a generator that takes eight hours to
start. Quote the horizon with the accuracy, always.""",
    notebook="""Step 30. Both horizons built on the identical pipeline, so the comparison isolates the extra hour.""",
    contributes="""The habit of stating a horizon, without which an accuracy figure means nothing.""",
    takeaway="""Accuracy without a stated horizon is meaningless — the useful forecast is the one that arrives
before the decision.""",
),

# ------------------------------------------- PHASE 12 - DESPATCH & THE CASE
dict(
    id='despatch', phase=11, short='Despatch',
    civil='From Forecast To Despatch Instruction', ai='Decision Support',
    civil_icon='🎚️', ai_icon='🧠',
    tech='Net load = forecast - solar; rules over level, ramp and reserve margin',
    civil_bullets=['Demand minus solar', 'The ramp, not just the level', 'Must-run minimum'],
    ai_bullets=['Net load is the target', 'Auditable rules', 'A reason with each instruction'],
    site="""A demand figure is not yet an instruction. The control room acts on net load — demand minus what
non-dispatchable generation contributes — and on the ramp. With solar on the system the evening ramp gets
steeper, not gentler: the sun sets as the residential peak arrives.""",
    challenge="""The decisions are conditional on several things at once. A 1,050 MW peak with warning is routine; the
same peak 90 minutes early is not. A deep overnight trough is fine unless it drops below the must-run
minimum, at which point the choice is to curtail renewables or find somewhere to put the energy.""",
    ai_link="""So the forecast feeds a small set of explicit rules producing a recommendation with a reason. The rules
are not machine learning and should not be — they encode the utility's operating policy, which must stay
readable and auditable. The AI supplies the number; the policy turns it into an action.""",
    notebook="""Step 31. `solar_output()` and `despatch()`, run across a full forecast day.""",
    contributes="""The instruction layer, and the duck-curve argument for forecasting net load rather than demand.""",
    takeaway="""The forecast supplies the number; auditable operating policy turns it into an instruction.""",
),
dict(
    id='reserve', phase=11, short='The business case',
    civil='Reserve, And The Cost Of Being Wrong', ai='Quantifying The Benefit',
    civil_icon='💰', ai_icon='📐',
    tech='Reserve sized from the error distribution; cost from asymmetric penalties',
    civil_bullets=['Error becomes reserve', 'Reserve is not free', 'Short costs more than long'],
    ai_bullets=['P95 of the error', 'Asymmetric loss', 'A measured business case'],
    site="""Forecast error does not disappear — it is carried as operating reserve. The utility holds enough spare
synchronised capacity to cover the difference between what it scheduled and what arrives. That means units
running at part load, at a worse heat rate, producing electricity that has not been sold.""",
    challenge="""And the two directions do not cost the same. Under-forecasting means buying at balancing prices or
starting peaking plant, and at the limit shedding load. Over-forecasting means committed plant backed down.
The first costs several times the second, which is why an unbiased forecast matters as much as an accurate
one.""",
    ai_link="""So the benefit is calculated, not claimed. Size the reserve from the 95th percentile of the error
distribution under each method, price the residual imbalance with the asymmetric penalties, and compare
against the published rule of thumb.""",
    notebook="""Step 32. `business_case()`, the stated unit costs, and the sanity check against published figures.""",
    contributes="""The number that justifies the project, computed from measured error rather than asserted.""",
    takeaway="""Better forecasting pays for itself in released reserve, and the amount can be calculated rather
than claimed.""",
),
dict(
    id='dashboard', phase=11, short='The dashboard',
    civil='The Utility Operations Dashboard', ai='The Deployed System',
    civil_icon='🖥️', ai_icon='📊',
    tech='Forecast, actual, error and instruction on one screen',
    civil_bullets=["Tomorrow's schedule", 'Yesterday performance', 'What to do about it'],
    ai_bullets=['The forecast curve', 'Rolling accuracy', 'The instruction'],
    site="""Everything from the previous 32 steps, on one screen, in the form the control room would actually see it:
tomorrow's forecast curve, how yesterday's forecast performed, the current accuracy, and the despatch
instruction for each hour.""",
    challenge="""A dashboard that only shows the forecast invites over-trust. The operator needs the recent track record
beside it — if the model has been running 40 MW low all week, that is something to act on, and it will not
show up in an annual MAE.""",
    ai_link="""So the deployed system reports forecast, outturn, error and instruction together, with the rolling
accuracy in view. That combination is what makes it a tool rather than an oracle.""",
    notebook="""Step 33. The multi-panel dashboard and the printed despatch summary.""",
    contributes="""The end of the project: the screen the utility runs, and the case for having built it.""",
    takeaway="""A deployed forecast shows its own track record beside its prediction, which is what makes it a
tool rather than an oracle.""",
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
# THE BRIDGE FIGURE
# Left = the grid (amber). Right = the AI (cyan). Between them an animated
# arrow, and under it the technical process (violet).
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


def _busbar(fig, x0, x1, y, color):
    """A short double-line busbar under a card title."""
    for dy in (0.03, -0.03):
        fig.add_shape(type="line", x0=x0, y0=y + dy, x1=x1, y1=y + dy,
                      line=dict(color=color, width=2), layer="above")


def _card(fig, x0, x1, color, icon, title, bullets, kicker):
    fig.add_shape(type="rect", x0=x0, x1=x1, y0=0.8, y1=5.35,
                  line=dict(color=EDGE, width=1), fillcolor=MIMIC, layer="below")
    fig.add_shape(type="line", x0=x0, y0=0.8, x1=x0, y1=5.35,
                  line=dict(color=color, width=4), layer="above")
    cx = (x0 + x1) / 2
    fig.add_annotation(x=cx, y=4.98, text=kicker, showarrow=False,
                       font=dict(size=11, color=color, family=MONOF), xanchor="center")
    fig.add_annotation(x=cx, y=4.18, text=icon, showarrow=False,
                       font=dict(size=34), xanchor="center")
    fig.add_annotation(x=cx, y=3.30, text=f"<b>{_wrap(title)}</b>", showarrow=False,
                       font=dict(size=14, color=TEXT), xanchor="center", align="center")
    _busbar(fig, x0 + 0.5, x1 - 0.5, 2.85, color)
    for i, b in enumerate(bullets):
        fig.add_annotation(x=cx, y=2.45 - i * 0.52, text=f"› {b}", showarrow=False,
                           font=dict(size=12, color=MUTED, family=MONOF), xanchor="center")


def bridge_figure(step, style, animate):
    """The grid-activity -> AI-equivalent -> technical-process bridge, drawn as
    a transmission line carrying a pulse from the network into the model."""
    fig = go.Figure()
    _card(fig, 0.2, 3.4, CIVIL, step["civil_icon"], step["civil"],
          step["civil_bullets"], "◄ ON THE NETWORK")
    _card(fig, 6.6, 9.8, AISIDE, step["ai_icon"], step["ai"],
          step["ai_bullets"], "IN THE MODEL ►")

    # a transmission line between the blocks, with two pylon ticks
    fig.add_shape(type="line", x0=3.45, y0=3.0, x1=6.35, y1=3.0,
                  line=dict(color=EDGE, width=2), layer="below")
    for px in (4.35, 5.65):
        fig.add_shape(type="line", x0=px, y0=2.86, x1=px, y1=3.14,
                      line=dict(color=EDGE, width=2), layer="below")
    fig.add_annotation(x=6.55, y=3.0, ax=6.3, ay=3.0, xref="x", yref="y",
                       axref="x", ayref="y", showarrow=True, arrowhead=2,
                       arrowsize=1.6, arrowwidth=2.5, arrowcolor=AISIDE, text="")
    fig.add_annotation(x=5.0, y=3.55, text="⟶ ENERGISE ⟶", showarrow=False,
                       font=dict(size=11, color=MUTED, family=MONOF))

    # the compute block (violet)
    fig.add_shape(type="rect", x0=3.5, x1=6.5, y0=1.25, y1=2.15,
                  line=dict(color=EDGE, width=1), fillcolor=INK, layer="below")
    fig.add_shape(type="line", x0=3.5, y0=1.25, x1=3.5, y1=2.15,
                  line=dict(color=TECH, width=3), layer="above")
    fig.add_annotation(x=5.0, y=1.98, text="⌁ COMPUTED AS", showarrow=False,
                       font=dict(size=9, color=TECH, family=MONOF))
    fig.add_annotation(x=5.0, y=1.56, text=_wrap(step["tech"], 46), showarrow=False,
                       font=dict(size=10, color=TEXT, family=MONOF),
                       xanchor="center", align="center")
    fig.add_annotation(x=5.0, y=2.42, text="▼", showarrow=False,
                       font=dict(size=13, color=TECH))

    # a pulse of load travels the line from the network into the model
    fig.add_trace(go.Scatter(x=[3.5], y=[3.0], mode="markers",
                             marker=dict(size=13, color=CIVIL, symbol="diamond",
                                         line=dict(color=INK, width=1)),
                             hoverinfo="skip", showlegend=False))
    frames = []
    for i in range(24):
        t = i / 23
        x = 3.5 + t * 2.85
        c = CIVIL if t < 0.45 else (TEXT if t < 0.55 else AISIDE)
        frames.append(go.Frame(data=[go.Scatter(
            x=[x], y=[3.0], mode="markers",
            marker=dict(size=13, color=c, symbol="diamond",
                        line=dict(color=INK, width=1)))]))
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
            f"<div class='step-card'>▐ STEP {i+1:02d} / {len(ORDER):02d} ▌"
            f"<br><b>{step['civil']}</b></div>", unsafe_allow_html=True)
    with c3:
        if next_s:
            if st.button(f"{next_s['civil']}  ▶", key=f"next_{key}", use_container_width=True):
                goto(next_s["id"])
        else:
            if st.button("Back to the overview  ▶", key=f"next_{key}", use_container_width=True):
                goto("start")


# ============================================================================
# open_page  -  Parts 1, 2 and 3, rendered ABOVE the existing stage renderer
# ============================================================================
def open_page(stage, style, animate):
    step = BY_ID.get(stage)
    if step is None:
        return
    pname, pdesc = PHASES[step["phase"]]

    _nav_strip(step, "top")
    i = ORDER.index(stage)
    st.markdown(
        f"<div class='scada' style='margin-top:14px'>⟨LOAD-FCST⟩ &nbsp; "
        f"STEP {i+1:02d}/{len(ORDER)} &nbsp;·&nbsp; PHASE {step['phase']+1:02d}/{len(PHASES)} "
        f"&nbsp;·&nbsp; <b>{pname.upper()}</b> &nbsp;—&nbsp; {pdesc}</div>",
        unsafe_allow_html=True)
    st.markdown(f"# {step['civil_icon']}  {step['civil']}")
    st.markdown(
        f"<span class='substep'>▸ this power system step is the AI concept </span>"
        f"<b style='color:{AISIDE}'>{step['ai']}</b>", unsafe_allow_html=True)
    st.divider()

    _bus_header("PART 1", "Power System Engineering", CIVIL)
    st.markdown(f"<div class='mimic'>{step['site']}</div>", unsafe_allow_html=True)
    st.write("")

    _bus_header("PART 2", "The Engineering Challenge", RED)
    st.markdown(f"<div class='mimic warn'>{step['challenge']}</div>", unsafe_allow_html=True)
    st.write("")

    _bus_header("PART 3", "AI Connection", AISIDE)
    st.markdown(f"<div class='mimic ai'>{step['ai_link']}</div>", unsafe_allow_html=True)
    st.plotly_chart(bridge_figure(step, style, animate), use_container_width=True,
                    key=f"bridge_{stage}")
    st.caption("▶ Press Play — the load pulse travels the line from the network into the model.")
    st.divider()

    _bus_header("PART 4", "The Technical Concept", TECH)
    st.caption(f"{step['tech']} — interactive. Change things and watch what happens.")


# ============================================================================
# close_page  -  Part 5, rendered BELOW the existing stage renderer
# ============================================================================
def close_page(stage):
    step = BY_ID.get(stage)
    if step is None:
        return
    st.divider()

    _bus_header("PART 5", "Notebook Connection", "#8bc34a")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Where you implement it**\n\n{step['notebook']}")
    with c2:
        st.markdown(f"**What it contributes**\n\n{step['contributes']}")
    st.write("")

    _bus_header("KEY", "Key Takeaway", GREEN)
    st.markdown(f"<div class='mimic ok' style='font-size:19px;font-weight:600;line-height:1.5'>"
                f"{step['takeaway']}</div>", unsafe_allow_html=True)

    render_quiz(stage)

    st.write("")
    segs = []
    for i, (pname, _) in enumerate(PHASES):
        cls = "cur" if i == step["phase"] else ("done" if i < step["phase"] else "")
        segs.append(f"<span class='blk {cls}' title='{pname}'>{i+1:02d}</span>")
    st.markdown(
        f"<div class='rail'><span class='raillab'>SCHEDULE</span>" + "".join(segs)
        + f"<span class='raillab' style='margin-left:auto'>PH {step['phase']+1:02d}/{len(PHASES)}"
        f" · {PHASES[step['phase']][0].upper()}</span></div>", unsafe_allow_html=True)
    st.write("")
    _nav_strip(step, "bottom")


# ============================================================================
# CHECK-YOUR-UNDERSTANDING QUIZ  (one question per stage, shown by close_page)
# ============================================================================
QUIZ = {
 'control-room': dict(
   q="Why must tomorrow evening's generation be committed tonight?",
   options=["Because electricity prices are set overnight",
            "Because large thermal plant takes six to twelve hours to synchronise, and electricity cannot be stored at grid scale",
            "Because the control room is unstaffed overnight",
            "Because demand is constant and easy to predict in advance"],
   answer=1,
   why="Generation must equal demand continuously and there is no buffer. A unit that takes 6-12 hours to start has to be committed against a demand nobody has measured yet."),
 'enter-ai': dict(
   q="Once the forecasting system is running, who decides what generation is committed?",
   options=["The model, automatically",
            "Whichever model reports the highest confidence",
            "The despatch engineer — the model only forecasts and states its likely error",
            "The weather desk"],
   answer=2,
   why="A model sees demand, temperature and a calendar. It does not know about outages, industrial shutdowns or cyclone warnings, and it cannot be held accountable for security of supply."),
 'one-hour': dict(
   q="What does the forecasting model actually receive from one metered hour?",
   options=["A live SCADA feed",
            "One row: the conditions, and the demand that resulted",
            "The operator's notes on that hour",
            "A recording of the whole hour"],
   answer=1,
   why="The model never stands in the control room and cannot re-run the hour. One row is all it gets, so a wrong row gives a confident wrong forecast with nothing to flag it."),
 'drivers': dict(
   q="Why is humidity's effect on demand so much harder to model than temperature's?",
   options=["Humidity sensors are less accurate",
            "Humidity has no effect on electricity demand",
            "Because it only matters when it is already hot — its effect depends on temperature",
            "Because humidity is measured as a percentage"],
   answer=2,
   why="The same humidity swing is worth tens of megawatts on a 38 degC evening and essentially nothing on a 20 degC one. That interaction is what a purely additive model cannot represent."),
 'load-data': dict(
   q="Why check the raw export before building anything on it?",
   options=["To reduce the file size",
            "Because a model trained on a broken export does not error — it trains happily and forecasts wrongly forever",
            "Because regulations require it",
            "To remove duplicate substations"],
   answer=1,
   why="Loading is a commissioning check. The row count looked right and there were still 24 duplicated rows in the file."),
 'inspect': dict(
   q="Which metering fault is hardest to catch, and why?",
   options=["A comms dropout, because the value is missing",
            "An RTU fault code, because 9999 MW is obviously wrong",
            "A frozen meter, because every value it reports is individually plausible",
            "A duplicated timestamp, because it doubles the row count"],
   answer=2,
   why="A frozen meter repeats its last good value. Each value passes any range check you could write; only a run-length check finds it."),
 'clean': dict(
   q="Why is filling a gap in a load series with the column median wrong?",
   options=["Because medians are less accurate than means",
            "Because the median of the whole column is far above the overnight demand, so a 03:00 gap gets filled well over a hundred MW too high",
            "Because pandas cannot compute a median on hourly data",
            "It is not wrong; it is the standard method"],
   answer=1,
   why="A time series must be filled along time. Interpolating between neighbouring hours respects the load curve; a column median teaches the model that 03:00 is a busy hour."),
 'profile': dict(
   q="What does the load duration curve show that the daily load curve does not?",
   options=["The average demand for each hour",
            "How many hours of the year the expensive top end of the system is actually needed for",
            "The weather on each day",
            "Which generators were running"],
   answer=1,
   why="Sorting every hour highest to lowest shows the top ~150 MW of capacity exists for under a hundred hours a year — which is where forecast error is most expensive."),
 'weather-link': dict(
   q="Why does the demand-vs-temperature relationship defeat linear regression?",
   options=["Because temperature is measured in degrees",
            "Because it is V-shaped with slopes that steepen, and humidity's effect depends on temperature",
            "Because there are too many data points",
            "Because temperature and demand are uncorrelated"],
   answer=1,
   why="Two failures at once: a non-linear response with two balance points, and an interaction a purely additive model cannot express."),
 'calendar-link': dict(
   q="Why give the model an explicit is_holiday flag instead of just the date?",
   options=["Because dates cannot be stored as numbers",
            "Because holidays are about eleven days a year — a rare class the model would otherwise have to infer from very few examples",
            "Because holidays have higher demand than weekdays",
            "Because the calendar changes every year"],
   answer=1,
   why="A holiday runs about 16% below a weekday, closer to a Sunday. Naming the category is engineering knowledge the model would otherwise have to rediscover from ~500 hours."),
 'cyclical': dict(
   q="What goes wrong if the hour is fed to a model as the plain integer 0-23?",
   options=["Nothing — models handle integers correctly",
            "The model believes 23:00 and midnight are the furthest apart hours in the day, when they are the closest",
            "The model cannot read values above 12",
            "The forecast is always one hour late"],
   answer=1,
   why="The clock is a circle and the integer is a line. Encoding the hour as sin and cos puts midnight back next to 23:00 — which is the trough the system passes through every night."),
 'degree-hours': dict(
   q="Why use cooling degree hours instead of raw temperature?",
   options=["Because degrees Celsius are not an SI unit",
            "Because raw temperature keeps changing through the comfort band where almost no demand moves",
            "Because it makes the numbers smaller",
            "Because it removes the need for a humidity feature"],
   answer=1,
   why="Between 16 and 24 degC neither heating nor cooling runs. cdd is zero there and rises only when cooling starts — a known physical threshold handed to the model rather than rediscovered."),
 'lags': dict(
   q="What do lag features add that weather and calendar columns cannot?",
   options=["They make the model train faster",
            "The recent LEVEL of the system — load growth, a new industrial consumer, a tariff change",
            "They remove the need for cleaning",
            "They encode the hour of day"],
   answer=1,
   why="Weather and calendar describe the conditions of an hour. Only the lags say what the network was actually drawing, which is the strongest single predictor of tomorrow."),
 'gate': dict(
   q="Why is lag_1 excluded from the day-ahead feature set?",
   options=["Because it is weakly correlated with demand",
            "Because at the 23:00 issue time it exists for exactly one hour of the 24 being forecast",
            "Because it duplicates lag_24",
            "Because it makes the model too slow"],
   answer=1,
   why="lag_1 is the single most informative column in the dataset — and for 13:00 tomorrow it means 12:00 tomorrow, which has not happened. Using it is data leakage."),
 'split': dict(
   q="Why is a shuffled train/test split wrong for a load series?",
   options=["Because shuffling is computationally expensive",
            "Because 14:00 and 15:00 on the same day are near-copies, so the model is tested on hours it has effectively seen",
            "Because the data must stay sorted for pandas",
            "Because random splits produce uneven class balance"],
   answer=1,
   why="Adjacent hours share the weather, the day type and nearly the same demand. Measured here, shuffling made the same model look 29% more accurate than it will be in the control room."),
 'scaling': dict(
   q="What did scaling the features actually change for these models?",
   options=["It improved accuracy by about 10%",
            "Nothing — the MAE was identical to six decimal places; scaling matters for regularised and gradient-descent models, not plain OLS or trees",
            "It made the trees faster",
            "It removed the need for the bias correction"],
   answer=1,
   why="Rescaling a column rescales its coefficient by the reciprocal; trees only ask whether a value is above a threshold. What scaling DOES buy is comparable coefficients."),
 'persistence': dict(
   q="Why score the naive persistence forecast before building any model?",
   options=["To fill space in the report",
            "Because it is the method the utility uses today — any model that does not beat it is not worth deploying",
            "Because it is more accurate than machine learning",
            "Because it requires no data"],
   answer=1,
   why="The benchmark is not zero error. Persistence scored 7.5% MAPE here, and every later number is quoted against that rather than against nothing."),
 'linear': dict(
   q="What is linear regression genuinely good for in this project?",
   options=["Being the most accurate forecast",
            "A transparent floor whose coefficients you can check against engineering sense, and a measure of how non-linear the problem is",
            "Handling the temperature-humidity interaction",
            "Forecasting without any features"],
   answer=1,
   why="You can read every coefficient in MW per unit and sanity-check it. And the gap between it and the tree models measures how much of the problem is non-linear."),
 'forest': dict(
   q="Why does a random forest handle the humidity-when-hot effect that linear regression cannot?",
   options=["Because it uses more memory",
            "Because each tree splits on one feature and then another, so 'humid AND hot' is a natural branch",
            "Because it scales the features first",
            "Because it has more coefficients"],
   answer=1,
   why="A tree can split on temperature first and humidity second. That nesting IS an interaction, which a single coefficient per feature cannot express."),
 'boosting': dict(
   q="What is each new tree in a gradient boosting model fitted to?",
   options=["The original demand values",
            "The errors the previous trees left behind",
            "A random subset of the features",
            "The validation set"],
   answer=1,
   why="Boosting works like a commissioning team: make a rough forecast, look at where it was wrong, build the next stage to fix that. The learning rate and depth stop it chasing noise."),
 'xgboost': dict(
   q="Beyond a small accuracy gain, why do utilities run XGBoost in production?",
   options=["It is free and sklearn is not",
            "Speed — across hundreds of feeders retrained weekly, fitting time is the difference between feasible and not",
            "It needs no feature engineering",
            "It cannot overfit"],
   answer=1,
   why="Measured here it fitted the same configuration far faster than the sklearn implementation. On one feeder that is a curiosity; on a few hundred, retrained weekly, it is the constraint."),
 'compare': dict(
   q="Why rank the models on validation rather than on the test set?",
   options=["Because the test set is smaller",
            "Because choosing on test uses the test data to make a decision, which turns its score into an optimistic one",
            "Because validation data is cleaner",
            "Because the test set has no labels"],
   answer=1,
   why="Select on validation, open test once, report what it says. Otherwise the number you publish is not the number you will get in the control room."),
 'importance': dict(
   q="Permutation importance ranked humidity near the bottom. What does that mean?",
   options=["Humidity should be removed from the model",
            "Humidity is irrelevant to electricity demand",
            "It is an AVERAGE over all hours, and most hours are mild — humidity still matters greatly on hot evenings",
            "The importance calculation failed"],
   answer=2,
   why="An average importance hides a driver that only bites at the extremes. The response curves show humidity worth tens of megawatts at 42 degC. Correlated features also share, and so understate, their importance."),
 'sensitivity': dict(
   q="Why sweep the model's inputs when the error metrics are already good?",
   options=["To make the notebook longer",
            "Because a model can be accurate on average and still wrong at the extremes — exactly where the system is most stressed",
            "To retrain the model",
            "To find missing values"],
   answer=1,
   why="This is commissioning, not scoring: sweep the input and check the response against known physics. The two humidity curves diverging as it heats up is the interaction, recovered from data."),
 'bias': dict(
   q="Why was the forecast consistently LOW on the test period?",
   options=["The model was underfitted",
            "Demand in the licence area grows about 3.5% a year, so relationships learnt on older data understate the newer level",
            "The test set had a data error",
            "Because trees cannot extrapolate"],
   answer=1,
   why="Distribution shift. In-sample bias was 0.00 and grew with distance from the training data — and it affected linear regression too, so it is not a tree-extrapolation problem."),
 'metrics': dict(
   q="Why report MAE, RMSE, MAPE and R² rather than picking one?",
   options=["To make the results look better",
            "Because they answer different questions: MAE for the operator, RMSE for reserve sizing, MAPE for benchmarking",
            "Because regulators require all four",
            "Because they are all the same number in different units"],
   answer=1,
   why="'Wrong by 15 MW every hour' and 'right all month except one 400 MW evening' are completely different operational risks, and a single metric cannot separate them."),
 'error-profile': dict(
   q="What did segmenting the error by hour of day reveal?",
   options=["The forecast is equally accurate at all hours",
            "The error is largest in the evening peak — the hours with the least reserve and the highest cost of being wrong",
            "The overnight hours are hardest to forecast",
            "Weekends are impossible to forecast"],
   answer=1,
   why="The evening peak is materially harder than the trough, and the top decile of hours is under-forecast most of the time — which is the expensive direction."),
 'worst-day': dict(
   q="What actually caused the worst forecast day?",
   options=["An extreme temperature the model had never seen",
            "A sharp day-on-day temperature swing, which left every lag feature describing a much hotter previous day",
            "A missing data point",
            "A public holiday the calendar missed"],
   answer=1,
   why="The day itself was unremarkable — its own temperature sat at the 82nd percentile. The day-on-day CHANGE sat at the 92nd. A lag-driven model is hurt by transitions, not by levels it has seen."),
 'predict': dict(
   q="Why does the forecast function return reasoning as well as a number?",
   options=["To make the output longer",
            "Because without it an operator cannot tell a sensible forecast from a broken sensor feeding a confident model",
            "Because the model requires it",
            "To satisfy a reporting standard"],
   answer=1,
   why="A forecast an operator cannot interrogate is a forecast they will override. '1,042 MW' means nothing without 'because it is 4 degC hotter and it is a working day'."),
 'horizon': dict(
   q="The one-hour-ahead model is far more accurate. Why is the day-ahead model the deliverable?",
   options=["Because it is cheaper to run",
            "Because a one-hour-ahead forecast cannot commit a generator that takes eight hours to start",
            "Because one-hour-ahead forecasts are not allowed",
            "Because the day-ahead model uses more features"],
   answer=1,
   why="Both are real products answering different questions: day-ahead decides what to START, one-hour-ahead decides how to TRIM what is already running. Always quote the horizon with the accuracy."),
 'despatch': dict(
   q="Why does the control room despatch against NET load rather than demand?",
   options=["Because net load is easier to forecast",
            "Because solar output falls to zero as the residential peak arrives, so the net evening ramp is far steeper than the demand ramp",
            "Because demand is not measured",
            "Because net load is always lower"],
   answer=1,
   why="Measured here, the peak demand ramp and the peak net-load ramp differ by roughly a factor of two. That gap is the whole operational argument for forecasting net load."),
 'reserve': dict(
   q="How is the benefit of a better forecast actually turned into money?",
   options=["By multiplying the accuracy by the electricity price",
            "By sizing operating reserve from the 95th percentile of the error distribution and pricing the released capacity and residual imbalance",
            "By counting the hours saved by the operator",
            "By comparing against other utilities' published figures"],
   answer=1,
   why="Forecast error does not disappear, it is carried as reserve. Reserve fell from about 128 MW to 38 MW here — the released synchronised capacity is where the saving comes from."),
 'dashboard': dict(
   q="Why does the operations dashboard show the recent track record beside the forecast?",
   options=["To fill the screen",
            "Because a dashboard showing only the forecast invites over-trust — a model running 40 MW low all week will not show up in an annual MAE",
            "Because regulators require it",
            "To help retrain the model"],
   answer=1,
   why="Forecast, outturn, error and instruction together are what make the system a tool rather than an oracle."),
}


def render_quiz(stage):
    """One check-your-understanding MCQ per stage. Portable across all the apps."""
    q = QUIZ.get(stage)
    if not q:
        return
    st.write("")
    st.markdown("##### 📝 Check your understanding")
    st.markdown(f"**{q['q']}**")
    choice = st.radio("Select an answer", q['options'], index=None,
                      key=f"quiz_{stage}", label_visibility="collapsed")
    if choice is not None:
        correct = q['options'][q['answer']]
        if choice == correct:
            st.success(f"✅ Correct. {q['why']}")
        else:
            st.error(f"❌ Not quite — the answer is **{correct}**.\n\n{q['why']}")


# ============================================================================
# THE INTERACTIVE ENGINEERING MIND MAP
# A vertical spine of the project's phases. Every node opens that learning page.
# ============================================================================
def mind_map(style):
    fig = go.Figure()
    n = len(PHASES)
    ROW = 1.9
    ys = {i: (n - 1 - i) * ROW for i in range(n)}

    for i in range(n - 1):
        fig.add_annotation(x=0, y=ys[i + 1] + 0.55, ax=0, ay=ys[i] - 0.75,
                           xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1.1,
                           arrowwidth=2, arrowcolor=CIVIL, text="")

    GAP, X0 = 3.6, 1.8
    sx, sy, stext, scustom, shover = [], [], [], [], []
    for pi, (pname, pdesc) in enumerate(PHASES):
        kids = _phase_steps(pi)
        for k, s in enumerate(kids):
            fig.add_shape(type="line", x0=0.25, y0=ys[pi], x1=X0 + k * GAP, y1=ys[pi],
                          line=dict(color="#243039", width=1.2, dash="dot"), layer="below")
        fig.add_annotation(x=0, y=ys[pi], text=f"<b>{pi+1:02d}</b>", showarrow=False,
                           font=dict(size=11, color=BG, family=MONOF),
                           bgcolor=CIVIL, bordercolor=CIVIL, borderpad=5, borderwidth=2)
        fig.add_annotation(x=-0.7, y=ys[pi], text=f"<b>{pname}</b>", showarrow=False,
                           xanchor="right", font=dict(size=13, color=CIVIL))
        fig.add_annotation(x=-0.7, y=ys[pi] - 0.42, text=_wrap(pdesc, 30),
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

    fig.update_xaxes(visible=False, range=[-6.4, X0 + 2 * GAP + 2.4])
    fig.update_yaxes(visible=False, range=[-1.4, (n - 1) * ROW + 1.1])
    return style(fig, h=int(n * ROW * 78))


# ============================================================================
# THE POWER-SYSTEMS-TO-AI MAPPING
# ============================================================================
def mapping_figure(style):
    fig = go.Figure()
    n = len(STEPS)
    for i, s in enumerate(STEPS):
        y = (n - 1 - i) * 1.0
        fig.add_shape(type="rect", x0=0, x1=3.6, y0=y - 0.36, y1=y + 0.36,
                      line=dict(color=EDGE, width=1), fillcolor=MIMIC, layer="below")
        fig.add_shape(type="line", x0=0, y0=y - 0.36, x1=0, y1=y + 0.36,
                      line=dict(color=CIVIL, width=3), layer="above")
        fig.add_annotation(x=0.18, y=y, text=f"{s['civil_icon']} {s['civil']}",
                           showarrow=False, xanchor="left", font=dict(size=11.5, color=TEXT))
        fig.add_annotation(x=4.1, y=y, text="»", showarrow=False,
                           font=dict(size=16, color=MUTED, family=MONOF))
        fig.add_shape(type="rect", x0=4.6, x1=8.2, y0=y - 0.36, y1=y + 0.36,
                      line=dict(color=EDGE, width=1), fillcolor=MIMIC, layer="below")
        fig.add_shape(type="line", x0=8.2, y0=y - 0.36, x1=8.2, y1=y + 0.36,
                      line=dict(color=AISIDE, width=3), layer="above")
        fig.add_annotation(x=4.78, y=y, text=f"{s['ai_icon']} {s['ai']}",
                           showarrow=False, xanchor="left", font=dict(size=11.5, color=TEXT))
        fig.add_annotation(x=8.4, y=y, text=f"P{s['phase']+1:02d}", showarrow=False,
                           xanchor="left", font=dict(size=9, color="#3b4652", family=MONOF))

    fig.add_annotation(x=0, y=n - 0.35, text="◄ POWER SYSTEM ENGINEERING PROCESS",
                       showarrow=False, xanchor="left",
                       font=dict(size=12, color=CIVIL, family=MONOF))
    fig.add_annotation(x=4.6, y=n - 0.35, text="THE AI PROCESS THAT SOLVES IT ►",
                       showarrow=False, xanchor="left",
                       font=dict(size=12, color=AISIDE, family=MONOF))

    fig.update_xaxes(visible=False, range=[-0.2, 9.0])
    fig.update_yaxes(visible=False, range=[-0.8, n + 0.2])
    return style(fig, h=int(n * 36 + 60))


# ============================================================================
# THE OPENING PAGE
# ============================================================================
def render_start(style, animate):
    st.markdown(
        f"<div class='brief'>"
        f"<div class='brief-bar'>PROJECT BRIEF · LOAD-FCST-001 · REV A · "
        f"{len(PHASES)} PHASES / {len(STEPS)} STEPS</div>"
        f"<div style='font-size:32px;font-weight:800;color:{TEXT}'>⚡ &nbsp;An Electricity Load "
        f"Forecasting Problem</div>"
        f"<div style='color:{MUTED};font-size:16px;line-height:1.6;margin-top:8px'>"
        f"Generation must equal demand every second, and the generators that follow demand have to be "
        f"committed hours before it arrives. AI shows up here because the power system work needs it."
        f"</div></div>", unsafe_allow_html=True)
    st.write("")

    # ---------------------------------------------- SECTION 1: THE PROBLEM
    _bus_header("01", "The Engineering Problem", CIVIL)
    st.markdown("""
It is 23:00 on a Sunday in the control room of a regional distribution utility — 1.2 million consumers,
a peak demand near 1,180 MW.

The despatch engineer has to decide **what generation runs tomorrow**. Not tomorrow morning — now. A large
thermal unit takes **six to twelve hours** to synchronise, so tomorrow evening's peak must be committed
tonight, against a demand nobody has measured yet.

**Electricity cannot be stored economically at grid scale.** There is no buffer and no catching up later.
""")
    c1, c2, c3, c4 = st.columns(4)
    for col, (icon, title, body, color) in zip(
        (c1, c2, c3, c4),
        [("📉", "Demand changes every hour",
          "About 480 MW at 04:00, over 1,180 MW on a hot August evening. Between 17:00 and 19:00 it can "
          "rise more than 60 MW in a single hour.", CIVIL),
         ("⚖️", "Supply and demand must balance",
          "Continuously, not on average. Frequency is the evidence: if generation and demand diverge, "
          "the whole system feels it within seconds.", CIVIL),
         ("💸", "Overestimating wastes energy",
          "Committed units run at part load, burning fuel at a worse heat rate to produce electricity "
          "nobody needs.", RED),
         ("🔌", "Underestimating risks outages",
          "Buy at balancing prices, start expensive peaking plant — and at the limit, shed load.", RED)]):
        with col:
            cls = "warn" if color == RED else ""
            st.markdown(
                f"<div class='mimic {cls}' style='height:100%'>"
                f"<div class='card-ico'>{icon}</div>"
                f"<b style='color:{TEXT}'>{title}</b><br>"
                f"<span class='muted'>{body}</span></div>", unsafe_allow_html=True)
    st.write("")
    st.markdown(
        f"<div style='border-left:3px solid {CIVIL};padding:8px 0 8px 16px;font-size:16px;"
        f"color:{TEXT};line-height:1.65'>One despatch engineer is responsible for "
        f"<b>8,760 of these numbers a year</b>, each needed before the hour it describes. "
        f"That is not a diligence problem. It is arithmetic.</div>", unsafe_allow_html=True)
    st.divider()

    # ---------------------------------------------- SECTION 2: THE GOAL
    _bus_header("02", "The Project Goal", AISIDE)
    st.markdown(
        "**AI forecasts future electricity demand so the utility can schedule generation efficiently and "
        "maintain a reliable supply.** Concretely, four parts:")
    c1, c2, c3, c4 = st.columns(4)
    for col, (icon, title, body) in zip(
        (c1, c2, c3, c4),
        [("📟", "The historical record",
          "Two years of hourly demand from the SCADA historian, joined to temperature, humidity and the "
          "calendar — inspected, cleaned and repaired along the time axis."),
         ("🔧", "Engineered features",
          "Cooling and heating degree hours, a cyclical clock, and lagged demand. Power system knowledge, "
          "turned into columns a model can use."),
         ("🧠", "Four regression models",
          "Linear Regression, Random Forest, Gradient Boosting and XGBoost — all judged on weeks they "
          "have never seen, against the method in use today."),
         ("🔔", "A despatch recommendation",
          "Not a number on its own. Forecast 1,042 MW at 19:00 tomorrow, above the committed-plant "
          "trigger — bring the peaking units to standby.")]):
        with col:
            st.markdown(
                f"<div class='mimic ai' style='height:100%'>"
                f"<div class='card-ico'>{icon}</div>"
                f"<b style='color:{TEXT}'>{title}</b><br>"
                f"<span class='muted'>{body}</span></div>", unsafe_allow_html=True)
    st.write("")
    st.markdown(
        f"<div style='border-left:3px solid {GREEN};padding:8px 0 8px 16px;font-size:16px;"
        f"color:{TEXT};line-height:1.65'>The goal is <b>not automation</b>. The despatch engineer stays "
        f"in charge, stays accountable, and still owns security of supply. The system does the one thing "
        f"a person cannot: it produces every hourly forecast, consistently, weighting every driver at "
        f"once, and <b>states how wrong it is likely to be</b>. The aim is a "
        f"<b>cheaper, more reliable</b> control room — not an unmanned one.</div>",
        unsafe_allow_html=True)
    st.divider()

    # ---------------------------------------------- SECTION 3: MIND MAP
    _bus_header("03", "Interactive Engineering Mind Map", CIVIL)
    st.markdown(
        f"<div style='color:{MUTED};font-size:15px;line-height:1.6'>These are the {len(PHASES)} phases of "
        f"<b>one load forecasting project</b>, in the order a real project runs them — from the grid at "
        f"work to a despatch instruction and the reserve it releases. "
        f"Every <b style='color:{CIVIL}'>amber node</b> is a power system activity. Every "
        f"<b style='color:{AISIDE}'>step hanging off it</b> is a learning page. "
        f"<b>Click any step to open it.</b></div>", unsafe_allow_html=True)
    st.write("")

    fig = mind_map(style)
    try:
        ev = st.plotly_chart(fig, use_container_width=True, key="mindmap",
                             on_select="rerun", selection_mode="points")
        pts = (ev or {}).get("selection", {}).get("points", [])
        if pts:
            cd = pts[0].get("customdata")
            target = cd[0] if isinstance(cd, list) else cd
            if target in BY_ID:
                goto(target)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, key="mindmap_static")
        st.info("Click-to-open needs Streamlit ≥ 1.35. Use the sidebar to jump to a step.")
    st.divider()

    # ---------------------------------------------- SECTION 4: THE MAPPING
    _bus_header("04", "Engineering → AI Mapping", AISIDE)
    st.markdown(
        f"<div style='color:{MUTED};font-size:15px;line-height:1.6'><b>Every AI concept here is a power "
        f"system activity you already understand</b> — the same thing, named differently by a different "
        f"profession. Read down the amber column and you have described a load forecasting project. Read "
        f"down the cyan column and you have described a complete machine learning pipeline. "
        f"<b>They are the same column.</b></div>", unsafe_allow_html=True)
    st.write("")
    st.plotly_chart(mapping_figure(style), use_container_width=True, key="mapping")

    st.markdown(
        f"<div style='border-left:3px solid {AISIDE};padding:8px 0 8px 16px;font-size:16px;"
        f"color:{TEXT};line-height:1.65'>Each AI concept shows up because the power system work ran into "
        f"something one engineer could not do by hand. Only then does it get a technical name.</div>",
        unsafe_allow_html=True)
    st.write("")

    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("▶  Start: walk into the control room", use_container_width=True,
                     type="primary"):
            goto("control-room")
    with c2:
        st.caption(f"{len(PHASES)} phases · {len(STEPS)} steps · one load forecasting project. "
                   "Every step opens with the power system activity, then the AI it becomes.")
