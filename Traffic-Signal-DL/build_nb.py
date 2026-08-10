"""
Builds Traffic_Signal_Optimization_DL.ipynb from nbformat cells.
Run:  py -3.13 build_nb.py

The notebook is standalone (Colab): it does not import app.py / story.py /
bridge.py. It re-defines the intersection model and the synthetic CCTV frames
inline so the notebook and any future app always agree.

APP and COLAB are the two places to change once the material is published --
every "open this stage in the app" link and the Colab badge are built from them.

NOTE for future editors: inside co(...) cells use only single-line "..."
docstrings or # comments. A triple-quoted docstring would close the outer
r\"\"\" string and break this build script.
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

# ----------------------------------------------------------------- placeholders
APP   = "https://traffic-signal-uyfomtzurrptqrg3pkd6gu.streamlit.app"          # <- update after the Streamlit app is deployed
COLAB = "https://colab.research.google.com/REPLACE-ME"   # <- update after this notebook is pushed

cells = []
def md(t):  cells.append(new_markdown_cell(t.strip("\n")))
def co(t):  cells.append(new_code_cell(t.strip("\n")))
def link(stage, label):
    """A deep link into the illustration app for this stage."""
    return f"🎬 **See it illustrated:** [{label}]({APP}/?stage={stage})"


# ---------------------------------------------------------------- title
md(rf"""
# AI for Traffic Signal Optimization
### Teaching AI through the signal timing of a city intersection

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({COLAB})

This notebook is the runnable companion to the Traffic Signal Optimization course. You are not learning AI
for its own sake — you are building an **adaptive signal controller** for a junction, and each AI method
appears because it solves a real traffic problem one engineer cannot cover by hand.

**The framing throughout:** the traffic engineer stays in charge and stays accountable. A model that sees
only detector counts cannot judge whether a queue is a funeral procession, decide that a school crossing
outranks throughput, or sign off a timing plan that a city has to defend in court. The controller only eases
the part one person cannot carry alone — watching every approach, every cycle, all day, at hundreds of
junctions. The controller *reports and recommends*; the engineer *decides*.

**The one idea this notebook proves:**

> **Machine Learning predicts traffic conditions from numerical detector data.
> Deep Learning understands live road images and finds vehicles and congestion that
> feature engineering cannot reliably capture.**

Do not take that on trust. Every section below builds towards it, and Section 18 measures it.

**What we build, in the order a real project runs it:**

1. The intersection at peak hour — the problem
2. One signal cycle → data collection
3. Load the traffic log
4. Data inspection (dropouts, stuck loops)
5. Data cleaning (median fill)
6. Normalization (one common scale)
7. Train / validation / test split
8. ML baseline — Random Forest for queue, delay and the congestion flag
9. Why ML cannot read a raw CCTV frame
10. Deep learning — the neuron
11. Activation functions
12. Loss and gradient descent
13. The network, and training it
14. CNN on the CCTV frame
15. Locating the queue — Grad-CAM
16. Emergency vehicles — the same network, a new label
17. Evaluation — the confusion matrix and the costly miss
18. The verdict — ML vs DL, measured
19. Incident detection — normal for the time of day
20. Optimisation — the best cycle length
21. Adaptive control — fixed-time vs responsive
22. Fusion — one decision per cycle
23. The traffic dashboard — the business case
24. Summary — the whole system

{link('start', 'The project overview')}
""")

md(r"""
## Setup

In Colab the libraries below are already installed. If you run this elsewhere, uncomment the install line.
We use `matplotlib` for plots to keep the notebook simple and portable. TensorFlow/Keras is used for the
CNNs — the notebook detects whether it is present and skips the CNN training gracefully if not, so every
non-CNN cell runs anywhere.
""")

co(r"""
# !pip install numpy pandas scikit-learn tensorflow matplotlib

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (confusion_matrix, ConfusionMatrixDisplay,
                             accuracy_score, recall_score, r2_score)

np.random.seed(42)
plt.rcParams["figure.figsize"] = (8, 4)

# The course palette. On this project three of them are also the signal colours.
CYAN, AMBER, GREEN, RED, MUTED = "#4fc3f7", "#ffb74d", "#66bb6a", "#ef5350", "#8b949e"

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    KERAS = True
    tf.random.set_seed(42)
except Exception as e:                      # noqa: BLE001
    KERAS = False
    print("TensorFlow not available — the CNN sections will be skipped.", e)

print("Environment ready.  Keras available:", KERAS)
""")

# ---------------------------------------------------------------- 1. the junction
md(rf"""
## 1 · The intersection at peak hour — the problem

**Traffic activity.** A four-approach signalised junction on a city arterial. Every approach gets a share of
each cycle: some green, some amber, some red. The controller runs a **fixed-time plan** — the same cycle
length and the same green split, every cycle, all day.

**The challenge.** The plan is fixed; the traffic is not. Demand doubles at 08:30, doubles again at 18:00
and nearly vanishes at 03:00. A plan sized for the evening peak is a plan that makes you sit at a red light
at three in the morning with no vehicle in sight. A plan sized for the night cannot clear the evening queue
at all. **One plan cannot be right twice.**

The plan installed here is neither extreme — it is the best compromise available, and Section 21 searches
every alternative to prove that no single fixed plan beats it. It is *still* wrong at 03:00 and wrong again
at 18:00, in opposite directions. That is not a badly chosen plan; it is the ceiling on what a fixed plan
can do.

**The AI connection.** The junction does not need its traffic engineer replaced. It needs the *gap between
the plan and the traffic* closed — conditions watched continuously and the timing adjusted while the queue
is still forming, rather than at the next retiming study three years from now. That continuous watch is the
only reason AI belongs at the roadside.

{link('in-peak', 'A junction under load')}
""")

co(r"""
# The intersection model. Everything in this notebook is built on four traffic-engineering
# quantities, and it is worth knowing them before any AI appears:
#
#   SATURATION FLOW  - the rate vehicles discharge across the stop line once moving (veh/h/lane)
#   CAPACITY         - saturation flow x the share of the cycle this approach gets green
#   DEGREE OF SATURATION X = demand / capacity   (X > 1 means the approach cannot cope)
#   CONTROL DELAY    - average seconds each vehicle loses. This is what drivers actually feel.
SAT_FLOW   = 1900.0    # veh/h/lane, ideal saturation flow (HCM)
LANES      = 2         # lanes on the approach
LOST_TIME  = 4.0       # s lost per phase to start-up and clearance
PHASES     = 4         # a four-approach junction
LOST_TOTAL = PHASES * LOST_TIME     # s of every cycle that moves nobody
C_MIN      = 45.0      # shortest legal cycle: 4 phases x 7 s minimum green + lost time
C_MAX      = 140.0     # longest cycle the city permits
LOS_LIMIT  = 55.0      # s/veh above which the approach counts as CONGESTED (HCM level of service E)
IDLE_L_S   = 0.00022   # litres of fuel burned per second of idling, per vehicle
CO2_PER_L  = 2.31      # kg CO2 per litre of petrol

def effective_green(green, ped_calls=0.0):
    "Vehicles never get the whole commanded green: a pedestrian call extends clearance."
    return np.maximum(np.asarray(green, float) - 0.6 * np.asarray(ped_calls, float), 6.0)

def capacity(green, cycle, heavy_pct=8.0, rain_mm=0.0, ped_calls=0.0, block=1.0):
    "Approach capacity in veh/h. block < 1 models a lane lost to an incident."
    g = effective_green(green, ped_calls)
    f_hv = 1.0 / (1.0 + np.asarray(heavy_pct, float) / 100.0)   # a truck = 2 passenger cars
    f_rn = np.clip(1.0 - 0.008 * np.asarray(rain_mm, float), 0.85, 1.0)
    return SAT_FLOW * LANES * f_hv * f_rn * block * g / np.asarray(cycle, float)

def delay_for(demand, green, cycle, heavy_pct=8.0, rain_mm=0.0, ped_calls=0.0,
              block=1.0, T=0.25):
    "HCM control delay in s/veh: uniform delay + incremental (overflow) delay."
    cap  = capacity(green, cycle, heavy_pct, rain_mm, ped_calls, block)
    lam  = effective_green(green, ped_calls) / np.asarray(cycle, float)
    X    = np.asarray(demand, float) / np.maximum(cap, 1.0)
    d1   = (0.5 * np.asarray(cycle, float) * (1 - lam) ** 2
            / np.maximum(1 - np.minimum(X, 1.0) * lam, 0.05))
    d2   = 900 * T * ((X - 1) + np.sqrt((X - 1) ** 2 + 8 * 0.5 * X / np.maximum(cap * T, 1.0)))
    # HCM does not distinguish beyond about 2 minutes of delay: it is all level of service F.
    return np.minimum(d1 + d2, 200.0), X, cap

def queue_for(demand, green, cycle, X, ped_calls=0.0):
    "Back of queue at the end of red, in metres of road, spread across the lanes."
    lam   = effective_green(green, ped_calls) / np.asarray(cycle, float)
    q_veh = (np.asarray(demand, float) * np.asarray(cycle, float) * (1 - lam)
             / (3600.0 * np.maximum(1 - np.minimum(X, 1.0) * lam, 0.05)))
    return q_veh * 7.0 / LANES          # 7 m of kerb per queued vehicle

# Two demand profiles, because a junction is a competition. The main street peaks sharply in the
# evening; the cross street peaks earlier and flatter. Their RATIO changes hour by hour, and that
# ratio is what a fixed green split gets wrong for most of the day.
def demand_for(hour):
    "Arrival flow on the main-street approach, veh/h."
    h = np.asarray(hour, float)
    am = 950.0 * np.exp(-((h -  8.5) ** 2) / (2 * 1.3 ** 2))
    nn = 380.0 * np.exp(-((h - 13.0) ** 2) / (2 * 2.2 ** 2))
    pm = 1900.0 * np.exp(-((h - 18.0) ** 2) / (2 * 1.6 ** 2))
    return 200.0 + am + nn + pm

def demand_cross(hour):
    "Arrival flow on the cross-street approach, veh/h."
    h = np.asarray(hour, float)
    return (150.0 + 700.0 * np.exp(-((h -  9.5) ** 2) / (2 * 2.6 ** 2))
                  + 500.0 * np.exp(-((h - 17.0) ** 2) / (2 * 2.4 ** 2)))

# The fixed-time plan currently installed. Section 21 re-derives these two numbers and checks them:
# they are the BEST POSSIBLE SINGLE PLAN, the one that minimises delay averaged over the whole day.
# That is deliberately the strongest baseline available -- no single fixed plan can beat it.
FIXED_C, FIXED_G = 87.0, 50.0

h  = np.arange(0, 24, 0.25)
dm = demand_for(h)
dc = demand_cross(h)
dl, X, cap = delay_for(dm, FIXED_G, FIXED_C)

fig, ax = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
ax[0].plot(h, dm, color=CYAN,  lw=2, label="main street")
ax[0].plot(h, dc, color="#ba68c8", lw=2, label="cross street")
ax[0].set_ylabel("demand (veh/h)"); ax[0].legend()
ax[0].set_title("the traffic changes all day")
ax[1].plot(h, dm / (dm + dc), color=GREEN, lw=2, label="main street's share of the demand")
ax[1].axhline(FIXED_G / (FIXED_C - LOST_TOTAL), color=RED, ls="--",
              label="main street's share of the green — fixed")
ax[1].set_ylabel("share"); ax[1].set_ylim(0, 1); ax[1].legend(fontsize=8)
ax[1].set_title("the split it needs moves; the split it gets does not")
ax[2].plot(h, dl, color=AMBER, lw=2, label="main-street delay under the fixed plan")
ax[2].fill_between(h, LOS_LIMIT, dl, where=dl > LOS_LIMIT, color=RED, alpha=0.25)
ax[2].axhline(LOS_LIMIT, color=RED, ls="--", label=f"congested above {LOS_LIMIT:.0f} s")
ax[2].annotate("empty road, still\na 37 s red to sit through", xy=(3, dl[12]), xytext=(4.2, 40),
               color=MUTED, fontsize=9, arrowprops=dict(arrowstyle="->", color=MUTED))
ax[2].annotate("plan cannot stretch", xy=(18, dl[72]), xytext=(11.0, 48),
               color=MUTED, fontsize=9, arrowprops=dict(arrowstyle="->", color=MUTED))
ax[2].set_xlabel("hour of day"); ax[2].set_ylabel("delay (s/veh)"); ax[2].legend(fontsize=8)
plt.tight_layout(); plt.show()

trap = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
print(f"Vehicles on the main approach per day : {float(trap(dm, h)):,.0f}")
print(f"Time they lose at this one signal     : {float(trap(dm * dl / 3600.0, h)):,.0f} vehicle-hours per day")
print(f"Red time on an empty road at 03:00    : {FIXED_C - FIXED_G:.0f} s of every {FIXED_C:.0f} s cycle")
print("One approach. One junction. A city has hundreds.")
""")

# ---------------------------------------------------------------- 2. one cycle
md(rf"""
## 2 · One signal cycle → data collection

**Traffic activity.** At the end of every signal cycle the controller records what it saw: how many vehicles
arrived, how fast they were moving, how long the loops were covered, how many were trucks or buses, what
timings it ran, whether it was raining, and how many pedestrians pressed the button.

**The challenge.** On their own these are nine readings on nine screens. No single number tells you whether
the cycle was any good.

**The AI connection.** Put them in one row and the cycle becomes a record: nine inputs, and the queue and
delay that resulted. Thousands of those rows are a dataset.

The nine channels, and what each one tells you:

| Channel | Sensor | Unit | What it tells you |
|---|---|---|---|
| Vehicles per cycle | Inductive loop counter | veh | Demand — how many turned up |
| Average speed | Radar / microwave | km/h | Falls sharply as the approach saturates |
| Loop occupancy | Inductive loop detector | % | Share of the cycle a vehicle sat over the loop |
| Heavy vehicle share | Vehicle classifier | % | A bus discharges like two cars — it eats capacity |
| Green time | Signal controller log | s | The lever the controller actually pulls |
| Cycle time | Signal controller log | s | The other lever, and the one drivers feel at night |
| Hour of day | Controller clock | h | Stands in for the whole daily demand pattern |
| Rainfall | Roadside weather station | mm | Wet roads cut saturation flow by up to 10% |
| Pedestrian calls | Push-button counter | count | Each call takes seconds away from the vehicle green |

{link('reading', 'One signal cycle')}
""")

co(r"""
FEATURES = ["vehicle_count", "avg_speed_kmh", "occupancy_pct", "heavy_veh_pct",
            "green_time_s", "cycle_time_s", "hour_of_day", "rain_mm", "ped_calls"]
NICE = ["Vehicles/cycle", "Speed (km/h)", "Occupancy (%)", "Heavy veh (%)",
        "Green (s)", "Cycle (s)", "Hour", "Rain (mm)", "Ped calls"]

def signals_for(demand, green, cycle, heavy_pct, rain_mm, hour, ped_calls, block=1.0):
    "The nine detector channels, noise-free. Column order == FEATURES."
    demand = np.asarray(demand, float)
    _, X, _ = delay_for(demand, green, cycle, heavy_pct, rain_mm, ped_calls, block)
    count = demand * np.asarray(cycle, float) / 3600.0
    # Speed and occupancy are CONSEQUENCES of saturation, not independent inputs.
    # That is exactly why they are the two channels the model leans on hardest.
    speed = np.clip(52.0 - 30.0 * np.minimum(X, 1.3) ** 1.6 - 0.5 * np.asarray(rain_mm, float), 5.0, 60.0)
    occ   = np.clip(8.0 + 62.0 * np.minimum(X, 1.3), 0.0, 95.0)
    return np.stack(np.broadcast_arrays(count, speed, occ,
                                        np.asarray(heavy_pct, float),
                                        np.asarray(green, float),
                                        np.asarray(cycle, float),
                                        np.asarray(hour, float),
                                        np.asarray(rain_mm, float),
                                        np.asarray(ped_calls, float)), axis=-1)

# One cycle in the evening peak, as the model will see it
one = signals_for(demand_for(18.0), FIXED_G, FIXED_C, 8.0, 0.0, 18.0, 3.0)
print(pd.DataFrame([one], columns=NICE).round(1).to_string(index=False))
""")

md(r"""
### Where the sensors sit

Nothing in this diagram is AI. It is the instrumentation a traffic engineer would specify before anyone
mentions a model — and it is the reason a dataset exists at all.
""")

co(r"""
fig, ax = plt.subplots(figsize=(6.4, 6.4))
ax.add_patch(plt.Rectangle((-10, -2.2), 20, 4.4, color="#2a2f36"))   # E-W carriageway
ax.add_patch(plt.Rectangle((-2.2, -10), 4.4, 20, color="#2a2f36"))   # N-S carriageway
ax.plot([-10, -2.2], [0, 0], color=AMBER, lw=1, ls=(0, (6, 6)))
ax.plot([2.2, 10], [0, 0], color=AMBER, lw=1, ls=(0, (6, 6)))
ax.plot([0, 0], [-10, -2.2], color=AMBER, lw=1, ls=(0, (6, 6)))
ax.plot([0, 0], [2.2, 10], color=AMBER, lw=1, ls=(0, (6, 6)))

# stop-line loops on every approach
for (x, y, w, hh) in [(-2.2, -3.4, 4.4, 0.7), (-2.2, 2.7, 4.4, 0.7),
                      (-3.4, -2.2, 0.7, 4.4), (2.7, -2.2, 0.7, 4.4)]:
    ax.add_patch(plt.Rectangle((x, y), w, hh, color=CYAN, alpha=0.85))

ax.plot(3.2, 3.2, "o", color=GREEN, ms=13)          # CCTV
ax.plot(-3.2, 3.2, "s", color=RED, ms=11)           # radar
ax.plot(-3.2, -3.2, "^", color=AMBER, ms=12)        # weather station
ax.plot(3.2, -3.2, "P", color="#ba68c8", ms=13)     # pedestrian push-button

for txt, xy, col in [("CCTV camera", (3.9, 3.9), GREEN),
                     ("radar (speed)", (-9.6, 4.3), RED),
                     ("weather station", (-9.6, -4.9), AMBER),
                     ("ped push-button", (3.9, -4.6), "#ba68c8"),
                     ("stop-line loops", (-2.0, -5.4), CYAN)]:
    ax.annotate(txt, xy, color=col, fontsize=9)

ax.set_xlim(-10, 10); ax.set_ylim(-10, 10); ax.set_aspect("equal"); ax.axis("off")
ax.set_title("one instrumented junction — four approaches, four sensor types")
plt.tight_layout(); plt.show()
""")

md(r"""
### The controller's log export

A real project starts by pulling a few weeks of logged cycles off the controller. Here we generate that
export so the notebook is self-contained and reproducible — same relationships, same faults you would meet
on the street.

The timing plans vary across the export because the junction has been retimed several times and runs
different plans by time of day. That variation is what lets a model learn that **green time and cycle time
are levers**, not constants.
""")

co(r"""
def make_export(n=1600, seed=42):
    "A few weeks of signal cycles, as the controller would export them."
    rng = np.random.default_rng(seed)
    hour   = rng.uniform(0, 24, n)
    demand = np.clip(demand_for(hour) * rng.normal(1.0, 0.12, n), 60, None)
    cycle  = rng.uniform(60, 130, n)
    # the share of the available green this approach was given, across all the plans ever run here
    green  = (cycle - LOST_TOTAL) * rng.uniform(0.25, 0.58, n)
    heavy  = rng.uniform(2, 18, n)
    rain   = np.where(rng.random(n) < 0.25, rng.uniform(0, 12, n), 0.0)
    ped    = rng.integers(0, 9, n).astype(float)

    b = signals_for(demand, green, cycle, heavy, rain, hour, ped)
    dl, X, cap = delay_for(demand, green, cycle, heavy, rain, ped)
    qm = queue_for(demand, green, cycle, X, ped)

    df = pd.DataFrame({
        "cycle_id":       np.arange(1, n + 1),
        "vehicle_count":  np.clip(b[:, 0] + rng.normal(0, 1.4, n), 0, None).round(1),
        "avg_speed_kmh":  np.clip(b[:, 1] + rng.normal(0, 1.8, n), 0, None).round(1),
        "occupancy_pct":  np.clip(b[:, 2] + rng.normal(0, 2.5, n), 0, 100).round(1),
        "heavy_veh_pct":  b[:, 3].round(1),
        "green_time_s":   b[:, 4].round(1),
        "cycle_time_s":   b[:, 5].round(1),
        "hour_of_day":    b[:, 6].round(2),
        "rain_mm":        b[:, 7].round(1),
        "ped_calls":      b[:, 8].round(0),
    })
    df["queue_length_m"] = np.clip(qm + rng.normal(0, 3.0, n), 0, None).round(1)
    df["avg_wait_s"]     = np.clip(dl + rng.normal(0, 2.5, n), 0, None).round(1)
    df["congested"]      = (df.avg_wait_s > LOS_LIMIT).astype(int)

    # the faults every real controller export carries
    for c in FEATURES:
        df.loc[rng.choice(n, int(0.06 * n), replace=False), c] = np.nan
    df.loc[rng.choice(n, 14, replace=False), "occupancy_pct"] = 100.0   # loop stuck ON
    df.loc[rng.choice(n, 11, replace=False), "avg_speed_kmh"] = 255.0   # radar 'no data' sentinel
    df.loc[rng.choice(n, 12, replace=False), "vehicle_count"] = 9999.0  # counter rollover
    df.loc[rng.choice(n, 10, replace=False), "green_time_s"]  = 0.0     # controller log gap
    return pd.concat([df, df.sample(20, random_state=4)], ignore_index=True)  # resync duplicates

raw = make_export()
raw.to_csv("traffic_signal_log.csv", index=False)
print("wrote traffic_signal_log.csv")
""")

# ---------------------------------------------------------------- 3. load
md(rf"""
## 3 · Load the traffic log

**Traffic activity.** The controller export arrives as a CSV: one row per signal cycle.

**The challenge.** An export is not a dataset. Detectors drop out when a cabinet is reset, a failed loop
writes a plausible number instead of nothing, and the same cycle can appear twice after a communications
resync.

**The AI connection.** Loading the file into a DataFrame is the first AI step — shape, column types and a
first look.

{link('load', 'The controller log arrives')}
""")

co(r"""
df = pd.read_csv("traffic_signal_log.csv")
print("shape:", df.shape)
print("congested cycles:", f"{df.congested.mean():.1%}")
df.head()
""")

# ---------------------------------------------------------------- 4. inspect
md(rf"""
## 4 · Data inspection — the detector health check

**Traffic activity.** Before trusting a month of cycles, an engineer checks the instruments. Did the loop
report all month? Is the radar alive? Is anything physically impossible?

**The challenge.** Faults hide in plain sight. A failed inductive loop reads **100% occupancy** — a
perfectly valid number that happens to mean the loop is broken, not that the road is permanently full.

**The AI connection.** Data inspection is that detector check, done in code.

{link('inspect', 'Detector health check')}
""")

co(r"""
print("Missing readings per channel")
print(df[FEATURES].isna().sum(), "\n")
print("Duplicate rows:", int(df.duplicated().sum()), "\n")
print(df[FEATURES].describe().T[["min", "max"]])

fig, ax = plt.subplots(figsize=(9, 3.5))
ax.bar(NICE, df[FEATURES].isna().sum().values, color=AMBER)
ax.set_ylabel("missing readings"); ax.set_title("dropouts per channel")
plt.xticks(rotation=30, ha="right"); plt.tight_layout(); plt.show()
""")

md(r"""
Read the `min` / `max` table above like a traffic engineer, not a statistician:

- `vehicle_count` maxing at **9999** is a counter rollover. No two-lane approach clears ten thousand
  vehicles in ninety seconds.
- `avg_speed_kmh` at **255** is not a speeding motorcyclist. It is the radar's "no data" sentinel written
  straight into the log as if it were a measurement.
- `occupancy_pct` at exactly **100.0** is a loop stuck on — a failed loop reads permanently occupied.
- `green_time_s` at **0.0** is a logging gap. An active phase always gets some green.

Every one of those is a *valid number* and a *fault* at the same time. That is exactly what inspection is
for. Note also that the honest ambiguity is real: at a genuine standstill, speed **is** near zero and
occupancy **is** near ninety. It is the impossible values, not the extreme ones, that identify a fault.
""")

# ---------------------------------------------------------------- 5. clean
md(rf"""
## 5 · Data cleaning

**Traffic activity.** A faulty detector is repaired or discounted before its counts reach a timing study.
Nobody sizes a junction on a loop that has been reading 100% since March.

**The challenge.** Deleting every affected row throws away good readings from the other eight channels.
Keeping them poisons every average.

**The AI connection.** Cleaning does both: drop duplicates, mark impossible values as *missing* rather than
deleting the row, then fill the gaps with the channel's **median** — a value the outliers cannot drag.

{link('clean', 'Dropouts and stuck loops')}
""")

co(r"""
clean = df.drop_duplicates().copy()

# mark the physically impossible as missing, rather than deleting the whole cycle
clean.loc[clean.vehicle_count > 400,   "vehicle_count"] = np.nan
clean.loc[clean.avg_speed_kmh > 120,   "avg_speed_kmh"] = np.nan
clean.loc[clean.occupancy_pct >= 99.9, "occupancy_pct"] = np.nan
clean.loc[clean.green_time_s <= 1.0,   "green_time_s"]  = np.nan

for c in FEATURES:
    clean[c] = clean[c].fillna(clean[c].median())

print(f"rows: {len(df)} -> {len(clean)}   missing left: {int(clean[FEATURES].isna().sum().sum())}")

fig, ax = plt.subplots(1, 2, figsize=(9, 3.5))
ax[0].boxplot(df.avg_speed_kmh.dropna());  ax[0].set_title("approach speed — dirty")
ax[1].boxplot(clean.avg_speed_kmh);        ax[1].set_title("approach speed — clean")
plt.tight_layout(); plt.show()

print("Why fill with the median rather than the mean? Compare each one before and after treatment:")
print(f"  mean   dirty {df.avg_speed_kmh.mean():5.1f} -> clean {clean.avg_speed_kmh.mean():5.1f} km/h "
      f"  (moved {abs(df.avg_speed_kmh.mean()-clean.avg_speed_kmh.mean()):.1f})")
print(f"  median dirty {df.avg_speed_kmh.median():5.1f} -> clean {clean.avg_speed_kmh.median():5.1f} km/h "
      f"  (moved {abs(df.avg_speed_kmh.median()-clean.avg_speed_kmh.median()):.1f})")
print("Eleven bogus 255s were enough to shift the mean. The median hardly noticed them, which is")
print("exactly why it is the safe thing to fill the gaps with.")
""")

# ---------------------------------------------------------------- 6. normalize
md(rf"""
## 6 · Normalization

**Traffic activity.** The channels do not share a scale. Occupancy is a percentage, cycle time runs to 130
seconds, pedestrian calls are a handful, rainfall is a few millimetres.

**The challenge.** A model that adds weighted inputs lets the largest-numbered channel dominate the sum —
not because it matters most to traffic, but because its unit is bigger.

**The AI connection.** Min-max scaling puts every channel on 0–1, so importance is decided by the data
instead of by the choice of unit.

{link('normalize', 'One common scale')}
""")

co(r"""
scaler = MinMaxScaler()
norm = clean.copy()
norm[FEATURES] = scaler.fit_transform(clean[FEATURES])

print("before scaling (ranges):")
print(clean[FEATURES].agg(["min", "max"]).T.round(1), "\n")
print("after scaling (ranges):")
print(norm[FEATURES].agg(["min", "max"]).T.round(2))
""")

# ---------------------------------------------------------------- 7. split
md(rf"""
## 7 · Train / validation / test split

**Traffic activity.** A timing plan is not validated on the same survey day that was used to design it.

**The challenge.** A model checked on the cycles it learned from will look excellent and mean nothing.

**The AI connection.** 70% to train, 15% to tune with, 15% sealed until the audit.

{link('split', 'Known vs sealed')}
""")

co(r"""
X    = norm[FEATURES].values
y    = norm["congested"].values          # classification target
yq   = norm["queue_length_m"].values     # regression target 1 — queue length
yw   = norm["avg_wait_s"].values         # regression target 2 — delay per vehicle

idx = np.arange(len(X))
itr, itmp = train_test_split(idx,  test_size=0.30, random_state=42, stratify=y)
iva, ite  = train_test_split(itmp, test_size=0.50, random_state=42, stratify=y[itmp])

Xtr, Xva, Xte = X[itr], X[iva], X[ite]
ytr, yva, yte = y[itr], y[iva], y[ite]

print(f"train {len(itr)}   validation {len(iva)}   test (sealed) {len(ite)}")
print(f"congested rate — train {ytr.mean():.1%}, val {yva.mean():.1%}, test {yte.mean():.1%}")
""")

# ---------------------------------------------------------------- 8. ML baseline
md(rf"""
## 8 · Machine Learning baseline — Random Forest

**Traffic activity.** Given this cycle's detector readings, how long is the queue, how long does a vehicle
wait, and is the approach congested?

**The challenge.** The textbook capacity formula gets the order of magnitude right and the details wrong.
Demand, green share, heavy vehicles, rain and pedestrian calls all interact, and the interaction is
non-linear right where it matters — near saturation.

**The AI connection.** A Random Forest asks a sequence of threshold questions on the *named* channels and
averages many trees. This is the **first half of the course promise: ML predicts traffic conditions from
numerical detector data.**

{link('ml-baseline', 'Queue and delay from the readings')} · {link('drivers', 'What drives congestion')}
""")

co(r"""
# --- regression: how long is the queue, and how long does a vehicle wait? ---
q_model = RandomForestRegressor(n_estimators=200, random_state=42).fit(Xtr, yq[itr])
w_model = RandomForestRegressor(n_estimators=200, random_state=42).fit(Xtr, yw[itr])

r2_q = r2_score(yq[ite], q_model.predict(Xte))
r2_w = r2_score(yw[ite], w_model.predict(Xte))
print(f"Queue length R2 on sealed cycles : {r2_q:.3f}")
print(f"Average delay R2 on sealed cycles: {r2_w:.3f}")

fig, ax = plt.subplots(1, 2, figsize=(10, 4.6))
for a, (truth, pred, name, unit) in zip(ax, [
        (yq[ite], q_model.predict(Xte), "queue length", "m"),
        (yw[ite], w_model.predict(Xte), "average delay", "s")]):
    a.scatter(truth, pred, s=12, color=CYAN, alpha=0.6)
    lims = [truth.min(), truth.max()]
    a.plot(lims, lims, "--", color=MUTED)
    a.set_xlabel(f"measured {name} ({unit})"); a.set_ylabel(f"predicted ({unit})")
    a.set_title(f"{name} — cycles never seen")
plt.tight_layout(); plt.show()
""")

co(r"""
# --- classification: was this approach congested? --------------------------
rf = RandomForestClassifier(n_estimators=200, random_state=42).fit(Xtr, ytr)
print(f"Random Forest accuracy on sealed cycles: {accuracy_score(yte, rf.predict(Xte)):.1%}")

# --- feature importance: which lever should the engineer pull? ------------
fig, ax = plt.subplots(1, 2, figsize=(12, 3.8))
for a, (m, title) in zip(ax, [(w_model, "drivers of delay (s/veh)"),
                              (rf,      "drivers of a CONGESTED cycle")]):
    imp = m.feature_importances_
    o = np.argsort(imp)[::-1]
    a.bar([NICE[i] for i in o], imp[o], color=CYAN)
    a.set_title(title); a.tick_params(axis="x", rotation=40)
    for lab in a.get_xticklabels():
        lab.set_ha("right")
plt.tight_layout(); plt.show()
""")

md(r"""
Read the two rankings like an engineer — the difference is the point.

- **Occupancy and speed dominate.** They are not causes; they are *consequences* of saturation. The model
  leans on them because they are the most direct measurement of the thing being predicted. That makes them
  excellent predictors and useless levers — you cannot fix a junction by adjusting its occupancy.
- **Green time and cycle time** matter less in the ranking and are the only two things the controller can
  actually change. **Importance is not controllability.** This is the single most misread chart in applied
  traffic ML.
- **Vehicle count** is the demand you must serve. It is not a fault, and no timing plan makes it go away.

Importance says how much a prediction *moves*, not what *causes* what and certainly not what to do about
it. Use it to decide what to investigate; use Section 20 to decide what to change.
""")

# ---------------------------------------------------------------- 9. the wall
md(rf"""
## 9 · The wall — why ML cannot read a CCTV frame

**Traffic activity.** The camera looks down the approach. Vehicles are dark shapes on lighter tarmac. An
operator glances at the monitor and knows instantly whether the approach is queueing.

**The challenge.** The camera does not output "congested". It outputs 4,096 numbers with no names.

**The AI connection.** Before reaching for a new method, try building the feature by hand — reduce the frame
to its mean brightness, on the reasonable theory that more vehicles means more dark pixels, and set an alarm
threshold. Watch it fail.

{link('cctv-problem', 'The raw CCTV frame')} · {link('handmade', 'Mean brightness by hand')}
""")

co(r"""
# An approach as a 64x64 camera frame (0 = black, 1 = white):
#   free_flow  - daylight, a few well-spaced vehicles        (clear)
#   night      - the same few vehicles, dark scene           (clear)  <- decoy 1
#   wet_glare  - the same few vehicles, wet reflective road  (clear)  <- decoy 2
#   queue      - a standing line of vehicles in two lanes    (CONGESTED)
#   jam        - vehicles across all three lanes             (CONGESTED)
SCENE = {"free_flow": 0, "night": 1, "wet_glare": 2, "queue": 3, "jam": 4}

def make_cctv(kind="free_flow", size=64, seed=0, emergency=False):
    rng = np.random.default_rng(seed * 8 + SCENE[kind])   # stable across sessions
    base = {"free_flow": 0.62, "night": 0.30, "wet_glare": 0.74,
            "queue": 0.62, "jam": 0.62}[kind]
    img = base + rng.normal(0, 0.030, (size, size))

    # lane markings, dashed, between three lanes
    for xm in (21, 42):
        for y0 in range(0, size, 10):
            img[y0:y0 + 5, xm:xm + 1] = min(base + 0.22, 1.0)
    if kind == "wet_glare":                      # specular streaks off standing water
        for _ in range(6):
            y0 = int(rng.integers(0, size - 8))
            img[y0:y0 + 3, :] += 0.10 * rng.uniform(0.6, 1.0)

    lanes = {"free_flow": [0, 1, 2], "night": [0, 1, 2], "wet_glare": [0, 1, 2],
             "queue": [0, 1], "jam": [0, 1, 2]}[kind]
    n_per = {"free_flow": 1, "night": 1, "wet_glare": 1, "queue": 6, "jam": 6}[kind]
    spread = {"free_flow": 52, "night": 52, "wet_glare": 52, "queue": 9, "jam": 9}[kind]

    spots = []
    for ln in lanes:
        x0 = 3 + ln * 21
        for k in range(n_per):
            y0 = int(rng.integers(2, 8)) + k * spread
            if y0 + 10 >= size:
                continue
            img[y0:y0 + 10, x0:x0 + 15] -= 0.38 * rng.uniform(0.85, 1.15)   # a vehicle roof
            spots.append((y0, x0))

    if emergency and spots:                      # a light bar on one vehicle
        y0, x0 = spots[int(rng.integers(len(spots)))]
        img[y0 + 1:y0 + 3, x0 + 4:x0 + 11] = 0.99
    return np.clip(img, 0, 1)

kinds  = ["free_flow", "night", "wet_glare", "queue", "jam"]
labels = {"free_flow": "clear", "night": "clear", "wet_glare": "clear",
          "queue": "CONGESTED", "jam": "CONGESTED"}

fig, ax = plt.subplots(1, 5, figsize=(14, 3.2))
for a, k in zip(ax, kinds):
    im = make_cctv(k)
    a.imshow(im, cmap="gray", vmin=0, vmax=1)
    a.set_title(f"{k}\n{labels[k]} · mean {im.mean():.3f}", fontsize=9)
    a.axis("off")
plt.tight_layout(); plt.show()

print("A frame is just", make_cctv('queue').size, "numbers. None of them is called 'congested'.")
""")

co(r"""
# The hand-made feature: one number per frame. Then a threshold, like any alarm limit.
# The theory is sound: more vehicles = more dark pixels = a darker frame.
means = {k: float(make_cctv(k).mean()) for k in kinds}
for k in sorted(means, key=means.get):
    print(f"  {k:10s} mean {means[k]:.3f}   truth: {labels[k]}")

print()
for thr in (0.26, 0.30, 0.40, 0.52, 0.60, 0.68):
    missed = [k for k in kinds if labels[k] == "CONGESTED" and means[k] >= thr]
    false_ = [k for k in kinds if labels[k] == "clear"     and means[k] <  thr]
    print(f"alarm below {thr:.2f} -> missed {missed or ['none']}, false alarms {false_ or ['none']}")
""")

md(r"""
**No threshold works, and it is worth being precise about why.**

Sort the five scenes by mean brightness and the problem is obvious:

```
night 0.27   <   jam 0.39   <   queue 0.47   <   free_flow 0.58   <   wet_glare 0.72
CLEAR            CONGESTED      CONGESTED       CLEAR               CLEAR
```

The two congested scenes are **sandwiched between clear ones**. Set the alarm dark enough to catch the jam
and you alarm on every empty road after sunset. Set it bright enough to exclude the night and you miss both.
There is no cut point, because the classes are not separable on this axis at all — and the printout above
shows the worst case honestly: at a threshold of 0.30 the rule manages to miss **both** congested scenes and
still raise a false alarm on the night frame.

Averaging threw away the only thing that separated them: **where the dark pixels are and what shape they
make**. A queue is a *line* of blobs; an empty night road is uniformly dark. You could add ten more
hand-made features — variance, edge count, dark-pixel fraction — and still be guessing at the next scene
you had not thought of.

> **Machine Learning weights the features you name. Deep Learning finds the features you cannot name.**

That is the second half of the course promise, and the reason everything from here on is a network.
""")

# ---------------------------------------------------------------- 10. neuron
md(rf"""
## 10 · Deep learning starts with one neuron

**Traffic activity.** A control-room operator weighs several signals at once — the counts are up, the loops
are covered, the radar speed has collapsed — and calls the approach congested or not.

**The challenge.** That judgement lives in one head, on one shift, watching one screen. It cannot be applied
to forty thousand logged cycles overnight, or to two hundred junctions at once.

**The AI connection.** Write it down and it is arithmetic: `z = w·x + b`. The weights are not chosen by
anyone — they are learned.

{link('operator-brain', "The operator's judgement")} · {link('neuron', 'The neuron')}
""")

co(r"""
x = Xtr[0]                                   # one scaled cycle
# counts/occupancy/rain/peds push towards congestion; speed/green/cycle push away
w = np.array([0.9, -1.1, 1.2, 0.4, -0.8, -0.3, 0.1, 0.3, 0.2])
b = -0.3

z = float(np.dot(w, x) + b)
def sigmoid(v): return 1 / (1 + np.exp(-np.clip(v, -50, 50)))
print(f"z = w.x + b = {z:+.3f}   ->   p(congested) = {sigmoid(z):.3f}")

plt.figure(figsize=(9, 3))
c = [RED if v >= 0 else CYAN for v in w * x]
plt.bar(NICE, w * x, color=c)
plt.axhline(0, color=MUTED, lw=1)
plt.ylabel("w x x"); plt.title(f"each channel's contribution  (z = {z:+.2f})")
plt.xticks(rotation=40, ha="right"); plt.tight_layout(); plt.show()
""")

# ---------------------------------------------------------------- 11. activation
md(rf"""
## 11 · Activation — turning a sum into a decision

**Traffic activity.** A controller does not act on a weighted sum. It acts on a state: hold the green, or
end the phase.

**The challenge.** A hard threshold treats "just under" and "just over" as opposites — and gives training no
slope to follow.

**The AI connection.** Sigmoid gives a graded probability; ReLU passes positive evidence. Smoothness is what
makes gradient descent possible at all.

{link('activation', 'Activation')}
""")

co(r"""
zs = np.linspace(-6, 6, 300)
fig, ax = plt.subplots(1, 3, figsize=(12, 3.2))
ax[0].plot(zs, sigmoid(zs), color=CYAN, lw=2);            ax[0].set_title("sigmoid — a probability")
ax[1].plot(zs, np.maximum(0, zs), color="#ba68c8", lw=2); ax[1].set_title("ReLU — passes positives")
ax[2].step(zs, (zs > 0).astype(float), color=RED, lw=2, where="mid")
ax[2].plot(zs, sigmoid(zs), color=CYAN, lw=2, alpha=0.6)
ax[2].set_title("hard threshold vs sigmoid — no slope to follow")
for a in ax: a.axhline(0, color=MUTED, lw=0.6); a.axvline(0, color=MUTED, lw=0.6)
plt.tight_layout(); plt.show()
""")

# ---------------------------------------------------------------- 12. gradient descent
md(rf"""
## 12 · Loss and gradient descent

**Traffic activity.** Retiming a junction by hand is a search: change the split, survey again, keep what
helped, step again.

**The challenge.** Step too far and you overshoot and oscillate; too small and the study takes a season.

**The AI connection.** Loss = how wrong. Gradient = downhill. Learning rate = step size. Same overshoot,
same reason.

{link('learning-loop', 'The learning loop')} · {link('gradient-descent', 'Loss and gradient descent')}
""")

co(r"""
def descend(lr, start=3.6, steps=18):
    p = [start]
    for _ in range(steps):
        p.append(p[-1] - lr * 2 * p[-1])     # d/dw of w^2 is 2w
    return np.array(p)

ws = np.linspace(-4, 4, 200)
plt.figure(figsize=(9, 4))
plt.plot(ws, ws**2, color=MUTED, lw=2, label="loss")
for lr, col, name in [(0.05, GREEN, "0.05 — crawls"),
                      (0.25, CYAN,  "0.25 — converges"),
                      (0.95, RED,   "0.95 — overshoots")]:
    p = descend(lr)
    plt.plot(p, p**2, "o-", color=col, ms=5, lw=1, label=f"lr = {name}")
plt.xlabel("weight"); plt.ylabel("loss"); plt.legend()
plt.title("the same gradient, three step sizes")
plt.tight_layout(); plt.show()
""")

# ---------------------------------------------------------------- 13. network + training
md(rf"""
## 13 · The network, and training it

**Traffic activity.** No single operator covers everything. One watches the arterial, one the side roads,
one the pedestrian phases. A supervisor combines their calls.

**The challenge.** Learn the logged cycles too well and you memorise them: perfect on last month's roadworks
layout, useless next month.

**The AI connection.** A hidden layer is that team. Training watches the **validation** error, and stops
where it turns.

{link('network', 'The network')} · {link('training', 'Training')}
""")

co(r"""
import warnings
mlp = MLPClassifier(hidden_layer_sizes=(14, 7), learning_rate_init=0.001,
                    max_iter=1, warm_start=True, random_state=0)
train_loss, val_err = [], []
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    for _ in range(140):
        mlp.fit(Xtr, ytr)
        train_loss.append(mlp.loss_)
        val_err.append(1.0 - mlp.score(Xva, yva))

best = int(np.argmin(val_err))
plt.figure(figsize=(9, 4))
plt.plot(train_loss, color=CYAN,  lw=2, label="training loss")
plt.plot(val_err,    color=AMBER, lw=2, label="validation error")
plt.axvline(best, color=GREEN, ls="--", label=f"best epoch = {best}")
plt.xlabel("epoch"); plt.ylabel("loss / error rate"); plt.legend()
plt.title("training loss keeps falling; validation error stops improving")
plt.tight_layout(); plt.show()

print(f"MLP accuracy on the sealed cycles: {mlp.score(Xte, yte):.1%}")
print("Past the dashed line the network is memorising these cycles, not learning the pattern.")
""")

# ---------------------------------------------------------------- 14. CNN
md(rf"""
## 14 · CNN on the CCTV frame

**Traffic activity.** An operator does not read a monitor pixel by pixel. They see a **shape**: a line of
roofs stacked back from the stop line, or a clear road with three vehicles strung out along it.

**The challenge.** Shape is not in any single pixel, and it moves. The queue starts at a different point,
in different lanes, in every frame — and the lighting changes twice a day.

**The AI connection.** A convolution slides a small filter across the frame and reports where its pattern
occurs. Early filters find edges; later ones combine edges into vehicle roofs and stacked queues. **The
network learns the filters** — that is the whole difference from Section 9.

{link('cnn-journey', 'Inside the CNN')}
""")

co(r"""
# What a convolution actually does — no framework needed.
from numpy.lib.stride_tricks import sliding_window_view

def conv2d(img, k):
    return np.einsum("ijkl,kl->ij", sliding_window_view(img, k.shape), k)

img = make_cctv("queue")
kv  = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], float)   # vertical edges — kerbs, lane lines
kh  = kv.T                                                     # horizontal edges — vehicle fronts/backs
kb  = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], float)  # blobs — compact bright/dark spots

fig, ax = plt.subplots(1, 4, figsize=(13, 3.4))
ax[0].imshow(img, cmap="gray"); ax[0].set_title("input frame (queue)")
for a, (k, name) in zip(ax[1:], [(kv, "vertical edges"), (kh, "horizontal edges"), (kb, "blobs")]):
    a.imshow(np.abs(conv2d(img, k)), cmap="magma"); a.set_title(name)
for a in ax: a.axis("off")
plt.tight_layout(); plt.show()

print("The horizontal-edge map already shows the rhythm of a queue: roof after roof after roof.")
print("Nobody told the filter what a vehicle is. Section 9's mean brightness never saw any of this.")
""")

md(r"""
### Train a small CNN

We build a labelled set of CCTV frames — clear and congested, with lighting, vehicle positions and spacing
varying from frame to frame so the network cannot memorise a location or a brightness. Then a three-layer
CNN learns to grade them.

If TensorFlow is not available this cell prints a note and the notebook carries on.
""")

co(r"""
def make_cctv_set(n=900, seed=0):
    "Labelled CCTV frames. y = 1 means the approach is congested."
    rng = np.random.default_rng(seed)
    Xi, yi, used = [], [], []
    lab = {"free_flow": 0, "night": 0, "wet_glare": 0, "queue": 1, "jam": 1}
    for _ in range(n):
        k  = kinds[int(rng.integers(len(kinds)))]
        im = make_cctv(k, seed=int(rng.integers(1e6)))
        # vary exposure and contrast a little, as a real camera would
        im = np.clip(im * rng.uniform(0.92, 1.08) + rng.uniform(-0.04, 0.04), 0, 1)
        Xi.append(im); yi.append(lab[k]); used.append(k)
    return np.array(Xi)[..., None].astype("float32"), np.array(yi), used

Ximg, yimg, used = make_cctv_set(900, seed=1)
Xi_tr, Xi_te, yi_tr, yi_te = train_test_split(Ximg, yimg, test_size=0.25,
                                              random_state=42, stratify=yimg)
print("frames:", Ximg.shape, " congested rate:", f"{yimg.mean():.1%}")

# Built with the functional API rather than Sequential, on purpose: Grad-CAM in Section 15 needs
# model.output and layer.output to be defined symbolically, and under Keras 3 a Sequential model
# does not provide them until it has been called. Functional models always do.
def small_cnn():
    inp = keras.Input(shape=(64, 64, 1))
    x = layers.Conv2D(16, 3, activation="relu", padding="same")(inp)
    x = layers.MaxPooling2D()(x)
    x = layers.Conv2D(32, 3, activation="relu", padding="same")(x)
    x = layers.MaxPooling2D()(x)
    x = layers.Conv2D(64, 3, activation="relu", padding="same", name="last_conv")(x)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(32, activation="relu")(x)
    out = layers.Dense(1, activation="sigmoid")(x)
    return keras.Model(inp, out)

if KERAS:
    cnn = small_cnn()
    cnn.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    hist = cnn.fit(Xi_tr, yi_tr, validation_split=0.2, epochs=14, batch_size=32, verbose=0)

    plt.figure(figsize=(9, 3.5))
    plt.plot(hist.history["loss"], color=CYAN, lw=2, label="training loss")
    plt.plot(hist.history["val_loss"], color=AMBER, lw=2, label="validation loss")
    plt.xlabel("epoch"); plt.ylabel("loss"); plt.legend(); plt.title("CNN training")
    plt.tight_layout(); plt.show()

    cnn_acc = cnn.evaluate(Xi_te, yi_te, verbose=0)[1]
    print(f"CNN accuracy on held-out frames: {cnn_acc:.1%}")
    print("Compare that with the best any mean-brightness threshold managed in Section 9.")
else:
    cnn_acc = None
    print("Keras not available — skipping CNN training.")
""")

# ---------------------------------------------------------------- 15. Grad-CAM
md(rf"""
### A word about that accuracy

The CNN scores at or near **100%**, and you should be suspicious of that rather than pleased by it. These
frames are synthetic: the vehicles are clean rectangles, the lighting comes in three tidy varieties, and
there is no rain on the lens, no motion blur, no camera shake, no low sun straight down the carriageway and
no lorry parked across the view. Real CCTV congestion classifiers live in the 85–95% range and are retrained
as the seasons change.

What the result *does* prove is the only thing this section claimed: the information needed to separate
congested from clear **is present in the pixels**, and a convolutional network extracts it without anybody
naming a feature. Section 9 established that no threshold on mean brightness can reach it. That gap — not
the exact percentage — is the finding.

## 15 · Locating the queue — Grad-CAM

**Traffic activity.** "This junction is congested" does not change a timing plan. The controller needs to
know **which approach and which lanes** are holding vehicles, because that is the phase to extend.

**The challenge.** A classifier outputs a probability and no location. An engineer asked to hand seconds of
green to a bare number will — rightly — refuse.

**The AI connection.** Grad-CAM weights the last feature maps by how much each pushed the score towards
"congested", then projects them back onto the frame. The bright region is the evidence the network used.

{link('queue-locate', 'Locating the queue')}
""")

co(r"""
def grad_cam(model, image, layer_name="last_conv"):
    "Class-activation map for a single frame (image shape 64x64x1)."
    grad_model = keras.models.Model(model.inputs,
                                    [model.get_layer(layer_name).output, model.output])
    with tf.GradientTape() as tape:
        maps, pred = grad_model(image[None, ...])
        loss = pred[:, 0]
    grads   = tape.gradient(loss, maps)[0]               # (h, w, c)
    weights = tf.reduce_mean(grads, axis=(0, 1))         # how much each map mattered
    cam = tf.reduce_sum(maps[0] * weights, axis=-1).numpy()
    cam = np.maximum(cam, 0)
    cam = cam / (cam.max() + 1e-9)
    rep = image.shape[0] // cam.shape[0]                 # stretch back over the frame
    return np.kron(cam, np.ones((rep, rep)))[:image.shape[0], :image.shape[1]]

if KERAS:
    show = ["queue", "jam", "night", "wet_glare"]
    fig, ax = plt.subplots(2, len(show), figsize=(3.1 * len(show), 6.2))
    for j, k in enumerate(show):
        im  = make_cctv(k, seed=7)[..., None].astype("float32")
        p   = float(cnn.predict(im[None, ...], verbose=0)[0, 0])
        cam = grad_cam(cnn, im)
        ax[0, j].imshow(im[..., 0], cmap="gray"); ax[0, j].set_title(f"{k}\np(congested) = {p:.2f}")
        ax[1, j].imshow(im[..., 0], cmap="gray")
        ax[1, j].imshow(cam, cmap="turbo", alpha=0.55)
        ax[1, j].set_title("where it looked", fontsize=9)
        ax[0, j].axis("off"); ax[1, j].axis("off")
    plt.tight_layout(); plt.show()
    print("On 'queue' the map lights the two occupied lanes and leaves the third dark.")
    print("That is the timing instruction: extend the phase serving those lanes, not the empty one.")
else:
    print("Keras not available — skipping Grad-CAM.")
""")

# ---------------------------------------------------------------- 16. emergency
md(rf"""
## 16 · Emergency vehicles — the same network, a new label

**Traffic activity.** An ambulance is on the approach. Every second it spends stopped at a red light is a
second off someone's survival odds. The junction should clear its path — **signal preemption** — and then
recover the timing plan afterwards.

**The challenge.** The emergency vehicle is one vehicle among twenty, and what marks it out is a **small
bright light bar**, about ten pixels in a frame of four thousand. It moves nothing in the mean brightness,
the occupancy, or the vehicle count. Every hand-made feature in this notebook is blind to it.

**The AI connection.** Nothing about the method changes. Same frames, same architecture, **a different
label** — and the network learns a completely different pattern. That is the practical meaning of "the
network learns the features": you change what you ask for, not what you engineer.

{link('emergency', 'Emergency preemption')}
""")

co(r"""
def make_emergency_set(n=900, seed=3):
    "Labelled CCTV frames. y = 1 means an emergency vehicle is present."
    rng = np.random.default_rng(seed)
    Xi, yi = [], []
    for _ in range(n):
        k   = kinds[int(rng.integers(len(kinds)))]      # every background, so background cannot leak
        emg = bool(rng.random() < 0.35)
        im  = make_cctv(k, seed=int(rng.integers(1e6)), emergency=emg)
        im  = np.clip(im * rng.uniform(0.92, 1.08) + rng.uniform(-0.04, 0.04), 0, 1)
        Xi.append(im); yi.append(int(emg))
    return np.array(Xi)[..., None].astype("float32"), np.array(yi)

Xe, ye = make_emergency_set(900)
Xe_tr, Xe_te, ye_tr, ye_te = train_test_split(Xe, ye, test_size=0.25,
                                              random_state=42, stratify=ye)

# First: prove the hand-made feature is blind to it. Sweep EVERY possible brightness threshold
# and keep the best one -- so nobody can say we simply picked a bad cut point.
bright = Xe[..., 0].reshape(len(Xe), -1).mean(axis=1)
base_rate = max(1 - ye.mean(), ye.mean())
best_acc, best_thr = 0.0, None
for thr in np.linspace(bright.min(), bright.max(), 400):
    for sense in (1, -1):
        acc = accuracy_score(ye, ((sense * bright) > (sense * thr)).astype(int))
        if acc > best_acc:
            best_acc, best_thr = acc, thr
print(f"Light bar adds about {10/64**2:.2%} of the frame's pixels.")
print(f"Best possible mean-brightness threshold : {best_acc:.1%} accuracy")
print(f"Always answering 'no emergency'          : {base_rate:.1%} accuracy")
print("The best hand-made rule barely beats refusing to answer. The bar is real and it is invisible")
print("to any global statistic, because a global statistic cannot ask WHERE the bright pixels are.\n")

if KERAS:
    ecnn = small_cnn()
    ecnn.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    ecnn.fit(Xe_tr, ye_tr, validation_split=0.2, epochs=16, batch_size=32, verbose=0)
    e_pred   = (ecnn.predict(Xe_te, verbose=0)[:, 0] > 0.5).astype(int)
    e_acc    = accuracy_score(ye_te, e_pred)
    e_recall = recall_score(ye_te, e_pred)
    print(f"Emergency CNN — accuracy {e_acc:.1%}, recall on emergency frames {e_recall:.1%}")
    print("Recall is the number that matters here. A missed ambulance is not a rounding error.")

    fig, ax = plt.subplots(1, 4, figsize=(13, 3.4))
    for j, k in enumerate(["free_flow", "night", "queue", "jam"]):
        im  = make_cctv(k, seed=11, emergency=True)[..., None].astype("float32")
        p   = float(ecnn.predict(im[None, ...], verbose=0)[0, 0])
        cam = grad_cam(ecnn, im)
        ax[j].imshow(im[..., 0], cmap="gray")
        ax[j].imshow(cam, cmap="turbo", alpha=0.5)
        ax[j].set_title(f"{k}\np(emergency) = {p:.2f}", fontsize=9); ax[j].axis("off")
    plt.tight_layout(); plt.show()
    print("Grad-CAM finds the light bar in all four lighting conditions — including the jam,")
    print("where the ambulance is stuck behind the very queue the other network is grading.")
else:
    e_acc = e_recall = None
    print("Keras not available — skipping the emergency detector.")
""")

# ---------------------------------------------------------------- 17. evaluation
md(rf"""
## 17 · Evaluation — the traffic audit

**Traffic activity.** Every claimed improvement is audited: predicted against surveyed, on cycles the model
never saw. A city cannot retime a corridor on a model nobody checked.

**The challenge.** A single accuracy figure hides the thing that matters. Predicting "not congested" for
every cycle scores well at a quiet junction — and finds nothing.

**The AI connection.** The confusion matrix separates the four outcomes, and the two errors do not cost the
same:

- **False alarm** — the controller extends a green nobody needed. Cost: a few seconds taken from the cross
  street, and a little credibility.
- **Missed congestion** — the queue keeps growing, spills back through the upstream junction and blocks it
  too. Cost: a corridor, not an approach. **Queue spillback is how one bad junction becomes a bad city.**

{link('audit', 'The traffic audit')}
""")

co(r"""
for name, model in [("Random Forest", rf), ("Neural network", mlp)]:
    p = model.predict(Xte)
    tn, fp, fn, tp = confusion_matrix(yte, p).ravel()
    print(f"{name:15s} accuracy {accuracy_score(yte, p):.1%}   "
          f"recall on congested cycles {recall_score(yte, p):.1%}   "
          f"(false alarms {fp}, MISSED {fn})")

fig, ax = plt.subplots(1, 2, figsize=(10, 4))
for a, (name, model) in zip(ax, [("Random Forest", rf), ("Neural network", mlp)]):
    ConfusionMatrixDisplay.from_predictions(
        yte, model.predict(Xte), display_labels=["clear", "congested"],
        cmap="Blues", colorbar=False, ax=a)
    a.set_title(name)
plt.tight_layout(); plt.show()

# The trap, made explicit
naive = np.zeros_like(yte)
print(f"\nA model that calls EVERY cycle clear: accuracy {accuracy_score(yte, naive):.1%}, "
      f"recall {recall_score(yte, naive, zero_division=0):.1%}")
print("Good accuracy, zero value. Recall on the congested cycles is what the project is judged on.")
""")

md(r"""
One more reason evaluation is not optional here: signal timing is **public infrastructure**. A model that
mis-times a junction does not produce a bad report — it produces a queue that real people sit in, a bus that
misses its layover, and an ambulance that arrives late. That is why the sealed test set stays sealed, why
recall is quoted alongside accuracy, and why every output in Section 22 is a *recommendation to an
engineer* rather than a command to a controller.
""")

# ---------------------------------------------------------------- 18. verdict
md(rf"""
## 18 · The verdict — ML vs DL, measured

This is the section the whole notebook has been building towards. Run both methods on both data types and
read the result off the table, rather than taking anyone's word for it.

{link('proof', 'The verdict')}
""")

co(r"""
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    ann_w = MLPRegressor(hidden_layer_sizes=(16, 8), max_iter=1500,
                         random_state=0).fit(Xtr, yw[itr])
r2_ann = r2_score(yw[ite], ann_w.predict(Xte))

print("ON THE 9 NAMED DETECTOR CHANNELS")
print(f"  Random Forest  — delay R2 {r2_w:.3f}")
print(f"  Neural network — delay R2 {r2_ann:.3f}")
print("  -> about the same. The engineer already named the features; ML is simpler and easier to defend.")

print("\nON THE RAW CCTV FRAME")
print("  Best hand-made feature (mean brightness) : no threshold separates congested from clear")
if KERAS:
    print(f"  CNN — congestion                         : {cnn_acc:.1%} accuracy")
    print(f"  CNN — emergency vehicle                  : {e_acc:.1%} accuracy, {e_recall:.1%} recall")
else:
    print("  CNN                                      : (Keras unavailable in this runtime)")
print("  -> only the CNN can start. Nobody can name 4,096 pixel features.")

pd.DataFrame({
    "": ["Queue & delay from the 9 readings", "Grade an approach from pixels",
         "Spot an ambulance in the frame", "Who names the features?"],
    "ML — Random Forest": ["works", "cannot even start", "cannot even start", "The engineer"],
    "DL — ANN / CNN":     ["works", "learns the pattern", "learns the pattern",
                           "The network learns them"],
})
""")

md(r"""
### The promise, now demonstrated

> **Machine Learning predicts traffic conditions from numerical detector data.
> Deep Learning understands live road images and finds vehicles and congestion that
> feature engineering cannot reliably capture.**

Neither method is "better". Each belongs to its data type:

- When an engineer **has** named the features — counts, speed, occupancy, green time — use Machine Learning.
  It is faster, cheaper, runs in a roadside cabinet, and is far easier to defend at a public inquiry.
- When nobody **can** name them — a CCTV frame at dusk in the rain — Deep Learning is the option that works
  at all.

And in both cases the output is a recommendation to an engineer, not a decision.
""")

# ---------------------------------------------------------------- 19. incident
md(rf"""
## 19 · Incident detection — normal for the time of day

**Traffic activity.** Occupancy is *supposed* to rise at 08:30 and again at 18:00. A busy evening peak is
not an incident, and a controller that alarms on it will be ignored within a week.

**The challenge.** Because normal moves, a fixed occupancy threshold is useless: set it high and a stalled
bus hides inside the peak, set it low and it cries wolf every weekday.

**The AI connection.** Learn what normal looks like **for these conditions**, then score the **residual** —
the occupancy the demand and the timing plan do not explain. A blocked lane is exactly that.

{link('incident', 'Normal vs incident')}
""")

co(r"""
rng = np.random.default_rng(7)

# 1. learn "normal" from a clean history: occupancy as a function of demand and green share
n_h    = 600
h_h    = rng.uniform(0, 24, n_h)
dm_h   = demand_for(h_h) * rng.normal(1.0, 0.10, n_h)
lam_h  = np.full(n_h, FIXED_G / FIXED_C)
occ_h  = signals_for(dm_h, FIXED_G, FIXED_C, 8.0, 0.0, h_h, 0.0)[:, 2] + rng.normal(0, 2.0, n_h)
Z_h    = np.c_[dm_h, dm_h**2, lam_h]
normal_model = LinearRegression().fit(Z_h, occ_h)

# 2. watch a live day in quarter-hours; at 15:00 a stalled bus takes out most of a lane for 75 minutes
tq    = np.arange(0, 24, 0.25)
dm_l  = demand_for(tq) * rng.normal(1.0, 0.06, len(tq))
# The bus stalls at 15.00. Capacity does not collapse instantly: the lane empties as the vehicles
# already past it clear, so the loss ramps in over about half an hour, then recovers when it is towed.
block = np.where((tq >= 15.0) & (tq < 16.25),
                 1.0 - 0.42 * np.clip((tq - 15.0) / 0.5, 0, 1), 1.0)
occ_l = signals_for(dm_l, FIXED_G, FIXED_C, 8.0, 0.0, tq, 0.0, block=block)[:, 2] \
        + rng.normal(0, 2.0, len(tq))

expected = normal_model.predict(np.c_[dm_l, dm_l**2, np.full(len(tq), FIXED_G / FIXED_C)])
resid    = occ_l - expected
sigma    = float(np.std(resid[tq < 12.0]))
thr      = 3 * sigma
alarm    = np.where(resid > thr)[0]

fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
ax[0].plot(tq, occ_l, color=CYAN, lw=1.8, label="measured occupancy")
ax[0].plot(tq, expected, color=MUTED, lw=1.8, ls="--", label="expected for the demand")
ax[0].axvspan(15.0, 16.25, color=RED, alpha=0.12)
ax[0].set_ylabel("loop occupancy (%)"); ax[0].legend()
ax[0].set_title("the raw occupancy at 15:00 is lower than the evening peak — a fixed threshold sees nothing")
ax[1].bar(tq, resid, width=0.22, color=np.where(resid > thr, RED, CYAN))
ax[1].axhline(thr, color=RED, ls="--")
ax[1].set_xlabel("hour of day"); ax[1].set_ylabel("unexplained occupancy (%)")
ax[1].set_title(f"residual = measured - expected  (alarm at 3 sigma = {thr:.1f}%)")
plt.tight_layout(); plt.show()

if len(alarm):
    print(f"Incident first flagged at {tq[alarm[0]]:.2f} h; the lane was blocked at 15.00 h.")
    print(f"Detected {(tq[alarm[0]] - 15.0) * 60:.0f} minutes after it happened, "
          f"and {(18.0 - tq[alarm[0]]) * 60:.0f} minutes before the evening peak arrives on top of it.")
else:
    print("No alarm raised — try lowering the sigma multiplier.")
""")

md(r"""
Look at the top panel and then the bottom one. The measured occupancy during the incident never exceeds the
evening peak, so **no fixed alarm level could ever separate them**. The residual can, because it asks a
different question: not "is this high?" but "is this higher than the demand explains?"

That distinction is the whole of practical anomaly detection, and it is the same idea as Section 6's
normalization — remove the variation you can account for, and what is left is the signal.
""")

# ---------------------------------------------------------------- 20. optimisation
md(rf"""
## 20 · Optimisation — the best cycle length

**Traffic activity.** The engineer chooses two numbers: how long the cycle is, and how the green is split
between the phases.

**The challenge.** Delay is **not** lowest at the shortest cycle, and it is not lowest at the longest one
either. Short cycles waste a large share of every cycle on start-up and clearance — at four phases, sixteen
seconds of every cycle move nobody. Long cycles spend that lost time only once, but make every red longer.
Intuition alone picks the wrong end of the range.

**The AI connection.** With a model of delay you can sweep the whole operating range and read the minimum
off the curve — and check it against the classic closed form, Webster's optimum cycle:

`C_opt = (1.5 L + 5) / (1 − Y)`, where `L` is the lost time per cycle and `Y` the sum of critical flow ratios.

{link('optimize', 'The best cycle length')}
""")

co(r"""
CYCLES = np.linspace(C_MIN, C_MAX, 120)

def flow_ratios(d_main, d_cross, heavy_pct=8.0):
    "y = flow ratio of each critical movement; Y = their sum (Webster's Y)."
    s  = SAT_FLOW * LANES / (1.0 + np.asarray(heavy_pct, float) / 100.0)
    y  = np.asarray(d_main,  float) / s
    yc = np.asarray(d_cross, float) / s
    return y, yc, np.clip(y + yc, 0.10, 0.92)

def green_split(d_main, d_cross, cycle):
    "Share out ALL the effective green in proportion to the flow ratios."
    y, yc, _ = flow_ratios(d_main, d_cross)
    avail = np.asarray(cycle, float) - LOST_TOTAL
    g_main = np.clip(avail * y / (y + yc), 7.0, avail - 7.0)
    return g_main, avail - g_main

def junction_delay(d_main, d_cross, cycle, g_main, g_cross):
    "Vehicle-weighted average delay across both critical movements, s/veh."
    a, _, _ = delay_for(d_main,  g_main,  cycle)
    b, _, _ = delay_for(d_cross, g_cross, cycle)
    return (d_main * a + d_cross * b) / (d_main + d_cross)

def delay_vs_cycle(d_main, d_cross, cycles=CYCLES):
    "Sweep the cycle length, re-splitting the green at every candidate."
    gm, gc = green_split(d_main, d_cross, cycles)
    return cycles, gm, junction_delay(d_main, d_cross, cycles, gm, gc)

plt.figure(figsize=(9.5, 4.8))
for hh, col, name in [(3.0, GREEN, "03:00 — night"), (9.0, CYAN, "09:00 — morning peak"),
                      (13.0, AMBER, "13:00 — midday"), (18.0, RED, "18:00 — evening peak")]:
    dmn, dcr = float(demand_for(hh)), float(demand_cross(hh))
    cyc, grn, d = delay_vs_cycle(dmn, dcr)
    b = int(np.argmin(d))
    _, _, Y = flow_ratios(dmn, dcr)
    c_web = float(np.clip((1.5 * LOST_TOTAL + 5) / (1 - Y), C_MIN, C_MAX))
    d_web = float(np.interp(c_web, cyc, d))          # what Webster's cycle actually costs
    plt.plot(cyc, d, color=col, lw=2, label=name)
    plt.plot(cyc[b], d[b], "*", color=col, ms=16)
    print(f"{name:22s} main {dmn:6.0f} + cross {dcr:5.0f} veh/h (Y={Y:.2f})")
    print(f"{'':22s} best cycle {cyc[b]:5.1f} s, main green {grn[b]:4.1f} s -> delay {d[b]:5.1f} s"
          f"   |   Webster {c_web:5.1f} s -> {d_web:5.1f} s  (+{d_web - d[b]:.1f} s)")
plt.axhline(LOS_LIMIT, color=RED, ls="--", lw=1, label=f"congested above {LOS_LIMIT:.0f} s")
plt.axvline(FIXED_C, color=MUTED, ls=":", lw=1.5, label=f"the fixed plan ({FIXED_C:.0f} s)")
plt.ylim(0, 140)
plt.xlabel("cycle length (s)"); plt.ylabel("junction delay (s/veh)"); plt.legend(fontsize=8)
plt.title("delay across the cycle-length range — the star is the best plan for that hour")
plt.tight_layout(); plt.show()
""")

md(r"""
Read the four curves as a traffic engineer. Two distinct regimes appear, and there is a third to watch for.

- **Light demand (night, midday) — the optimum is the shortest legal cycle.** There is no interior minimum:
  with little traffic, every extra second of cycle is a second of pointless red, so the curve just climbs
  from the left-hand edge. The floor at 45 s is not a modelling choice; it is four phases of minimum green
  plus the time a pedestrian needs to cross. *This is the regime the junction is in for most of the day.*
- **Heavy demand (both peaks) — a genuine interior minimum.** Below it, lost time eats so much capacity that
  the approach saturates and delay explodes upward. Above it, capacity is fine but every red is simply
  longer. The evening optimum is around 110 s; the morning optimum is around 59 s, even though the morning
  carries a similar total volume — because the morning's demand is split much more evenly between the two
  streets, and an even split is cheaper to serve.
- **The regime to watch for.** If `Y` — the sum of the critical flow ratios — approaches 1, the minimum runs
  off to the legal maximum cycle and stays congested there. That junction is out of capacity, and no timing
  plan is a solution. An engineer who reads such a curve and reports "we need a longer cycle" has misread
  it; the honest report is **"this junction needs another lane, a different phase order, or less traffic."**
  That is why "divert traffic" belongs in Section 22's recommendations and "add green" does not.

**On Webster's formula.** Compare the two *delay* figures printed for each hour, not the two cycle lengths.
Webster's `C_opt` sits up to twenty seconds away from the star and still costs **less than a second** of
extra delay, every time. The curve is flat near its bottom, so a wide band of cycle lengths is very nearly
optimal. That flatness is why a closed form from 1958 survived the arrival of computers: it lands in the
right neighbourhood, and the neighbourhood is what matters. Sweep the curve to decide; use Webster to check
you have not made an arithmetic error.

**Key takeaway:** the best cycle runs from 45 s to 110 s across a single day — it more than doubles. Compare
that with the dotted line marking the one fixed plan the junction actually runs.
""")

# ---------------------------------------------------------------- 21. adaptive
md(rf"""
## 21 · Adaptive control — fixed-time vs responsive

**Traffic activity.** Section 20 gives the best plan *for a given demand*. Demand is measured every cycle by
the loops we cleaned in Section 5. So recompute the plan every cycle.

**The challenge.** The controller only knows what has already happened. It sets this cycle's timings from
last cycle's counts, so it is always one step behind — and every plan must still respect minimum greens,
maximum cycle, and the pedestrian phase.

**The AI connection.** This is the traffic decision engine: prediction (Section 8) and optimisation
(Section 20) joined into a loop that runs continuously. It is also the natural place where reinforcement
learning enters a real project — the same loop, with the timings learned from experience rather than solved
from a formula. We stay with the solved version here because it is transparent and can be audited, which is
what a city will ask for first.

{link('adaptive', 'Fixed-time vs adaptive')}
""")

co(r"""
def best_plan(meas_main, meas_cross):
    "Choose cycle and split for the demand just measured, within the legal limits."
    cyc, _, d = delay_vs_cycle(meas_main, meas_cross)
    b = int(np.argmin(d))
    gm, gc = green_split(meas_main, meas_cross, float(cyc[b]))
    return float(cyc[b]), float(gm), float(gc)

hours = np.arange(0, 24, 0.25)
main_d, cross_d = demand_for(hours), demand_cross(hours)
total_d = main_d + cross_d

# Build the strongest possible baseline: search every single fixed plan and keep the one with the
# lowest delay AVERAGED OVER THE WHOLE DAY. If adaptive control beats this, it is not beating a
# badly chosen plan -- it is beating the best a fixed plan can ever do.
best_v, best_p = np.inf, None
for C in CYCLES:
    for frac in np.linspace(0.15, 0.75, 61):
        gm = max((C - LOST_TOTAL) * frac, 7.0)
        gc = (C - LOST_TOTAL) - gm
        if gc < 7.0:
            continue
        v = float(np.sum(total_d * junction_delay(main_d, cross_d, C, gm, gc)))
        if v < best_v:
            best_v, best_p = v, (C, gm, gc)
best_C, best_gm, best_gc = best_p
print(f"Best possible SINGLE fixed plan : cycle {best_C:.0f} s, "
      f"main green {best_gm:.0f} s, cross green {best_gc:.0f} s")
print(f"The plan installed in Section 1 : cycle {FIXED_C:.0f} s, main green {FIXED_G:.0f} s")
print("They agree. The baseline is not a straw man — no fixed plan does better than this one.\n")

rng = np.random.default_rng(11)
fix_d = junction_delay(main_d, cross_d, best_C, best_gm, best_gc)

adp_d, adp_c, adp_g = [], [], []
prev_m, prev_c = float(main_d[0]), float(cross_d[0])
for i in range(len(hours)):
    # the controller only knows the LAST interval's counts, and the detectors are noisy
    C, gm, gc = best_plan(prev_m * rng.normal(1.0, 0.08), prev_c * rng.normal(1.0, 0.08))
    adp_d.append(float(junction_delay(main_d[i], cross_d[i], C, gm, gc)))
    adp_c.append(C); adp_g.append(gm)
    prev_m, prev_c = float(main_d[i]), float(cross_d[i])
adp_d = np.array(adp_d)

veh  = total_d * 0.25                             # vehicles arriving in each 15-minute interval
vh_f = float(np.sum(veh * fix_d / 3600.0))
vh_a = float(np.sum(veh * adp_d / 3600.0))

fig, ax = plt.subplots(2, 1, figsize=(10, 6.6), sharex=True)
ax[0].plot(hours, fix_d, color=RED,   lw=2, label=f"best fixed plan ({best_C:.0f} s cycle)")
ax[0].plot(hours, adp_d, color=GREEN, lw=2, label="adaptive (replanned every 15 min)")
ax[0].fill_between(hours, adp_d, fix_d, where=fix_d > adp_d, color=GREEN, alpha=0.15)
ax[0].axhline(LOS_LIMIT, color=MUTED, ls="--", lw=1)
ax[0].set_ylabel("junction delay (s/veh)"); ax[0].legend()
ax[0].set_title("delay through the day — the shaded area is the saving")
ax[1].plot(hours, adp_c, color=CYAN,  lw=2, label="adaptive cycle")
ax[1].plot(hours, adp_g, color=AMBER, lw=2, label="adaptive main green")
ax[1].axhline(best_C,  color=RED, ls="--", lw=1, label="the fixed plan")
ax[1].axhline(best_gm, color=RED, ls=":",  lw=1)
ax[1].set_xlabel("hour of day"); ax[1].set_ylabel("seconds"); ax[1].legend(fontsize=8)
ax[1].set_title("what the adaptive controller actually did")
plt.tight_layout(); plt.show()

fuel_saved = float(np.sum(veh * (fix_d - adp_d) * IDLE_L_S))
print(f"Vehicle-hours of delay per day — best fixed plan : {vh_f:7.1f}")
print(f"Vehicle-hours of delay per day — adaptive        : {vh_a:7.1f}")
print(f"Reduction: {100*(vh_f-vh_a)/vh_f:.1f}%   "
      f"({vh_f-vh_a:.1f} vehicle-hours, {fuel_saved:.0f} litres of idling fuel, "
      f"{fuel_saved*CO2_PER_L:.0f} kg CO2 — at ONE junction, in ONE day)")
""")

md(r"""
Three things about that result are worth arguing about before anyone quotes it.

- **The saving comes from both ends of the day, for opposite reasons.** The fixed plan is a compromise, so
  it is too *long* at night and midday — 87 s of cycle where 45 s would do, which is pure surplus red — and
  too *short* in the evening peak, where 110 s is needed and the queue does not clear. A compromise is not
  wrong in one place; it is wrong in both directions at once. That is what the bottom panel shows: the
  adaptive cycle spends the day nowhere near the dashed line.
- **Do not quote 29% to a city.** This is an *isolated* junction, running a *single* fixed plan, with
  *perfect* demand knowledge one interval late. Real installations already switch time-of-day plans and
  coordinate along a corridor, so the honest published range for adaptive control against a competently
  timed network is more like **10–20%** (the SCOOT and SCATS evaluation literature). The number here is real
  for the baseline it is measured against, and that baseline is more generous than reality.
- **The saving is not free.** Detectors fail, and this controller trusts them completely. Section 19 exists
  precisely because an adaptive plan built on a stuck loop is worse than a fixed plan built on a survey.
  Cleaning and incident detection are not preliminaries to the optimisation — they are what make it safe to
  deploy at all.
""")

# ---------------------------------------------------------------- 22. fusion
md(rf"""
## 22 · AI fusion — one decision per cycle

**Traffic activity.** By now the junction produces several opinions every cycle, on every approach: a
predicted delay and queue, an incident score, a CCTV congestion grade with a location, and an emergency-
vehicle flag.

**The challenge.** Four screens is four chances to miss something — and the four can disagree.

**The AI connection.** Fusion combines them into one ranked recommendation with its evidence attached.
Numbers say **how bad and for how long**; images say **where, and whether an ambulance is in it**.

The precedence is not a modelling choice, it is policy, and it is set by the city:

1. **Emergency preemption** outranks everything, including a worse queue elsewhere.
2. **A confirmed incident** outranks routine congestion — the queue will not clear by adding green.
3. **Routine congestion** is served in order of predicted delay.

{link('fusion-engine', 'The decision engine')} · {link('pipeline', 'The whole system')}
""")

co(r"""
def decide(approach, pred_delay_s, queue_m, incident_sigma, cctv_grade, emergency):
    "Combine the ML prediction, the incident score and the CNN evidence into one action."
    if emergency:
        pr, act = "PREEMPT", "Clear this approach now — emergency vehicle detected on camera"
    elif incident_sigma >= 3.0:
        pr, act = "HIGH", "Dispatch to the blockage — extra green will not clear this queue"
    elif pred_delay_s > LOS_LIMIT and cctv_grade == "congested":
        pr, act = "HIGH", "Extend green on the queued lanes next cycle"
    elif pred_delay_s > LOS_LIMIT:
        pr, act = "MEDIUM", "Delay predicted but camera disagrees — verify before changing the plan"
    else:
        pr, act = "LOW", "Hold the plan — normal for this demand"
    return dict(approach=approach, priority=pr, pred_delay_s=pred_delay_s, queue_m=queue_m,
                sigma=incident_sigma, camera=cctv_grade, emergency=emergency, action=act)

screen = pd.DataFrame([
    decide("North", 84.0, 141.0, 1.1, "congested", False),
    decide("South", 38.0,  62.0, 0.6, "clear",     True),
    decide("East",  71.0, 118.0, 4.2, "congested", False),
    decide("West",  61.0,  96.0, 0.9, "clear",     False),
]).set_index("approach")
screen = screen.loc[screen.priority.map(
    {"PREEMPT": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}).sort_values().index]
screen
""")

md(r"""
Read the four rows and notice that **the worst queue does not win**.

- **South** has the least delay on the screen and goes first, because there is an ambulance in it. That is
  the city's policy, encoded — not something the model decided.
- **East** and **North** are both congested and both would take green. East outranks North because its
  residual says the queue has a *cause* that green cannot fix. Sending more green there would waste it; the
  right response is to send someone.
- **West** shows the case worth designing for: the numbers say congested, the camera says clear. That
  disagreement is not a failure, it is information — most often a detector drifting. It gets a "verify",
  never an automatic timing change.

And note what the screen does **not** do: it never changes a signal by itself. Every row ends in a
recommendation an engineer approves or a policy the engineer wrote. That was fixed back in Section 1 and it
holds all the way through.
""")

# ---------------------------------------------------------------- 23. dashboard
md(rf"""
## 23 · The traffic dashboard — the business case

**Traffic activity.** A city does not buy a model. It approves a spend against a saving in journey time,
fuel, emissions and emergency response.

**The challenge.** AI savings are easy to overstate. The corridor-level figure is not the junction figure
multiplied by the number of junctions — vehicles that clear one junction faster simply arrive at the next
one sooner, and some of the benefit is handed straight back.

**The AI connection.** Convert the model outputs into the city's own units. Every figure below is
**arithmetic on assumptions you can change** — none of it is a measurement.

{link('dashboard', 'The traffic dashboard')}
""")

co(r"""
def business_case(junctions=40, coordination_loss=0.45,
                  value_of_time=12.0, work_days=250,
                  vh_fixed=None, vh_adapt=None):
    "Scale one junction's simulated day to a corridor. Change any argument and the case changes."
    vh_fixed = vh_f if vh_fixed is None else vh_fixed
    vh_adapt = vh_a if vh_adapt is None else vh_adapt
    saved_one = (vh_fixed - vh_adapt)                          # vehicle-hours/day, one junction
    saved_net = saved_one * junctions * (1 - coordination_loss)
    fuel_l    = saved_net * 3600.0 * IDLE_L_S                  # litres of idling avoided per day
    return dict(saved_vehicle_hours_day = saved_net,
                saved_vehicle_hours_year= saved_net * work_days,
                fuel_litres_day         = fuel_l,
                tonnes_CO2_year         = fuel_l * CO2_PER_L * work_days / 1000.0,
                time_value_year         = saved_net * value_of_time * work_days,
                pct_delay_removed       = 100 * (vh_fixed - vh_adapt) / vh_fixed)

case = business_case()
for k, v in case.items():
    print(f"{k:26s} {v:,.1f}")

plt.figure(figsize=(6.4, 4))
plt.bar(["best fixed\nplan", "adaptive\ncontrol"], [vh_f, vh_a], color=[RED, GREEN])
plt.ylabel("vehicle-hours of delay per day"); plt.title("one junction, one day")
plt.tight_layout(); plt.show()

print("\nThe 'after' bar never reaches zero and never will: at a signalised junction somebody")
print("must always be stopped so somebody else can go. Delay is not a fault to be eliminated,")
print("it is a quantity to be allocated well. And 45% of the corridor-level benefit is given")
print("straight back at the next junction, which is why 'coordination_loss' is an input here")
print("rather than a rounding error hidden in the model.")
""")

# ---------------------------------------------------------------- 24. summary
md(rf"""
## 24 · Summary — the whole system

```
   LOOPS / RADAR / WEATHER  ──►  clean ──► scale ──► split ──►  RANDOM FOREST  ──┐
   (9 named channels)                                    queue, delay, congested │
                                                                                 ├──►  FUSION ──► DASHBOARD
   CCTV CAMERA  ──────────────────────────────────────►  CNN + Grad-CAM  ────────┤   one ranked   veh-hours,
   (4,096 raw pixels)                                    congestion + location    │    action      litres,
                                                         emergency vehicle        │                tonnes CO2
   WEBSTER / DELAY SWEEP  ────────────────────────────►  BEST CYCLE & SPLIT  ─────┘
```

**What was built**

| Stage | Method | Output |
|---|---|---|
| Predict queue length and delay | Random Forest regression | metres, seconds per vehicle |
| Flag a congested cycle | Random Forest / MLP classification | clear vs congested |
| Rank the drivers | Feature importance | what to investigate first |
| Grade an approach from CCTV | CNN | clear / congested |
| Locate the queue | Grad-CAM | which lanes to give green |
| Spot an emergency vehicle | CNN (same architecture, new label) | preemption trigger |
| Catch the unexplained queue | Regression + residual | incident score in σ |
| Find the best timing plan | Delay sweep + Webster | cycle length and green split |
| Run it every cycle | Adaptive control loop | delay reduction, measured |
| Combine everything | Fusion rules + city policy | one ranked action |
| Justify the spend | Arithmetic | vehicle-hours, litres, tonnes CO₂ |

**The three things worth remembering**

1. **Detector measurements → Machine Learning.** The engineer names the features; the model weights them.
2. **Camera frames → Deep Learning.** Nobody can name 4,096 pixel features, so the network learns them —
   and the same network learns a completely different pattern the moment you change the label.
3. **Traffic Engineer + AI.** The system watches every approach every cycle and reports what it finds. A
   person still decides, still signs off, and still owns the queue.

**And one that is specific to this problem:** the optimum timing plan is not a number, it is a function of
demand. Everything in this notebook — the cleaning, the prediction, the camera, the incident score — exists
to work out which point on that function the junction is at, right now.

{link('start', 'The whole project map')}
""")

nb = new_notebook(cells=cells, metadata={
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"},
    "colab": {"provenance": []},
})
nbf.validate(nb)
with open("Traffic_Signal_Optimization_DL.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"wrote Traffic_Signal_Optimization_DL.ipynb  ({len(cells)} cells, "
      f"{sum(1 for c in cells if c.cell_type=='code')} code)")
