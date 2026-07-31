"""
Builds Power_Source_Selection_AI.ipynb from nbformat cells.
Run:  py -3.13 build_nb.py

Standalone (Colab): the microgrid model, the optimiser and the controllers are all defined
inline so the notebook and any future app always agree.

APP and COLAB are the two places to change once the material is published.

NOTE for future editors:
  * inside co(...) cells use only single-line "..." docstrings or # comments. A triple-quoted
    docstring would close the outer r\"\"\" string and break this build script.
  * xgboost and ipywidgets are optional; both are guarded so every cell runs without them.
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

# ----------------------------------------------------------------- placeholders
APP   = "https://power-source-selection.streamlit.app"               # <- update after the Streamlit app is deployed
COLAB = "https://colab.research.google.com/REPLACE-ME"   # <- update after this notebook is pushed

cells = []
def md(t):  cells.append(new_markdown_cell(t.strip("\n")))
def co(t):  cells.append(new_code_cell(t.strip("\n")))
def link(stage, label):
    """A deep link into the illustration app for this stage."""
    return f"🎬 **See it illustrated:** [{label}]({APP}/?stage={stage})"


# ---------------------------------------------------------------- title
md(rf"""
# AI for Power Source Selection
### A decision support system for a campus microgrid

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({COLAB})

This notebook is the runnable companion to the Power Source Selection course. You are not learning Machine
Learning for its own sake — you are building a **decision support system** for a microgrid, and every method
appears because a real energy-management problem required it.

**The framing throughout:** the power systems engineer stays in charge and stays accountable. A model cannot
be told about the maintenance crew working on the LV panel, cannot judge whether tonight's forecast is
trustworthy, and cannot sign off islanding a campus. The system only eases the part one person cannot carry
alone — re-deciding, every fifteen minutes, across five sources whose costs all move at once. It
*recommends*; the engineer *decides*.

**The one idea this notebook proves:**

> **Machine Learning can evaluate many operating conditions at once and recommend the most suitable power
> source, helping engineers make better energy management decisions.**

Do not take that on trust. Section 17 measures it in rupees, in kilograms of CO₂, and against two
opponents: the rule the plant already runs, and a perfect-foresight optimum that no real system can reach.

**Three honest questions this notebook refuses to skip.** Most "AI decision support" projects fail on one of
them, silently:

1. **Where do the labels come from?** If you invent a rule, label your data with it, then train a model to
   reproduce it, you have built a slower copy of your own rule. Section 11 demonstrates this happening.
2. **How do you split time-series data?** Split 15-minute readings at random and consecutive, nearly
   identical rows land on both sides. Section 8 measures how much that inflates the score.
3. **Is accuracy the right score?** No. Some wrong answers cost two rupees and some start a diesel engine.
   Section 16 replaces accuracy with cost regret.

**What we build, in the order a real project runs it:**

1. The microgrid at 06:00 — the problem
2. Five sources, and what each one really costs
3. One interval → data collection
4. Load the SCADA export
5. Data inspection — the meter health check
6. Data cleaning
7. Preparing the inputs — scaling, cyclical time, forecasts
8. The split that does not lie — by day, not by row
9. The rule the plant already runs
10. Where the labels come from — the perfect-foresight optimiser
11. The trap — learning your own rule back
12. The decision model — tree, forest, boosting
13. Feature importance — what drives the decision
14. Explaining one decision
15. The live recommendation — try it yourself
16. Why decision accuracy is the wrong score
17. Closed-loop evaluation — a month of test days
18. When it is wrong — the confusion matrix that costs money
19. Grid outage — reliability, and why the diesel stays
20. The decision engine — one recommendation, with its reasons
21. The energy management dashboard — the business case
22. Summary — the whole system

{link('start', 'The project overview')}
""")

md(r"""
## Setup

In Colab everything below is already installed. We use `matplotlib` rather than Plotly, to match the other
notebooks in this series and so every cell runs identically in Colab, Jupyter or a plain script.

`xgboost` and `ipywidgets` are optional — both are guarded, and the notebook falls back gracefully if they
are missing.
""")

co(r"""
# !pip install numpy pandas scikit-learn matplotlib xgboost ipywidgets

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (confusion_matrix, ConfusionMatrixDisplay,
                             accuracy_score, classification_report)

np.random.seed(42)
plt.rcParams["figure.figsize"] = (9, 4)

# The course palette
SOLAR, WIND, BATT, GRID, DIESEL_C = "#ffb74d", "#4fc3f7", "#66bb6a", "#ba68c8", "#ef5350"
MUTED, INK = "#8b949e", "#37474f"

try:
    from xgboost import XGBClassifier
    XGB = True
except Exception:                                   # noqa: BLE001
    XGB = False
    print("xgboost not available — Gradient Boosting will stand in for it.")

try:
    import ipywidgets as widgets
    from IPython.display import display
    WIDGETS = True
except Exception:                                   # noqa: BLE001
    WIDGETS = False

print("Environment ready.  xgboost:", XGB, " ipywidgets:", WIDGETS)
""")

# ---------------------------------------------------------------- 1. the problem
md(rf"""
## 1 · The microgrid at 06:00 — the problem

**Engineering context.** A manufacturing campus runs its own microgrid: a 400 kW rooftop solar array, a
250 kW wind turbine, a 500 kWh battery, a utility connection on a time-of-use tariff, and a 300 kW diesel
generator for when the grid fails.

**The engineering challenge.** Every fifteen minutes, something has changed. A cloud crosses the array.
The tariff steps into the evening peak. The battery is at 46% and the shift is about to start. The engineer
must decide, right now, which source or combination carries the load — and the decision they make at 14:00
changes what is possible at 19:00, because a battery spent early is a battery that is empty when power is
most expensive.

That is 96 decisions a day, each one coupled to all the others, with five interacting variables. It is not
that engineers cannot make this decision. It is that they cannot make it **ninety-six times a day, every
day, while also running a plant**.

**The AI connection.** A decision support system watches the conditions continuously and proposes the
source. The engineer approves it, overrides it, or ignores it — and stays responsible for the result.

{link('microgrid', 'A campus microgrid at dawn')}
""")

co(r"""
# ---- the physical plant --------------------------------------------------
DT        = 0.25            # hours per interval (15 minutes)
STEPS     = 96              # intervals per day
PV_KW     = 400.0           # solar array peak
WT_KW     = 250.0           # wind turbine rating
CAP_KWH   = 500.0           # battery energy capacity
P_BAT     = 200.0           # battery power limit, charge or discharge
SOC_MIN   = 20.0            # never go below - warranty and reserve
SOC_MAX   = 95.0
ETA_C     = 0.9487          # charge efficiency   (0.90 round trip, split evenly)
ETA_D     = 0.9487          # discharge efficiency
DEGRADE   = 1.20            # Rs/kWh of battery throughput - a battery cycle is NOT free
DIESEL_KW = 300.0
DIESEL_RS = 21.0            # Rs/kWh - fuel plus O&M
VOLL      = 500.0           # Rs/kWh value of lost load: the cost of not supplying the campus

# carbon intensity, kg CO2 per kWh
CO2 = dict(solar=0.04, wind=0.01, grid=0.71, diesel=0.80)

def tariff(hour):
    "Industrial time-of-use tariff, Rs/kWh."
    h = np.asarray(hour, float) % 24
    p = np.full(h.shape, 8.00)                 # normal
    p[(h >= 22) | (h < 6)] = 4.50              # off-peak
    p[(h >= 18) & (h < 22)] = 11.50            # evening peak
    return p

hours = np.arange(0, 24, DT)
plt.figure(figsize=(9.5, 3.2))
plt.step(hours, tariff(hours), where="post", color=GRID, lw=2.5)
plt.fill_between(hours, 0, tariff(hours), step="post", color=GRID, alpha=0.15)
plt.ylabel("Rs / kWh"); plt.xlabel("hour of day"); plt.ylim(0, 13)
plt.title("the tariff the engineer is deciding against")
plt.tight_layout(); plt.show()

print("Off-peak 4.50   Normal 8.00   Evening peak 11.50 Rs/kWh")
print()
print("Everything in this notebook follows from one fact: the same kilowatt-hour is worth")
print("two and a half times as much at 19:00 as it is at 03:00. A battery is not a backup")
print("device. It is a way of moving energy from a cheap hour to an expensive one.")
""")

# ---------------------------------------------------------------- 2. five sources
md(rf"""
## 2 · Five sources, and what each one really costs

**Engineering context.** Each source has a different job, a different cost and a different constraint.

| Source | Marginal cost | CO₂ | The constraint that actually binds |
|---|---|---|---|
| Solar | ~₹0.30/kWh (O&M only) | 0.04 kg/kWh | Only available when the sun is up |
| Wind | ~₹0.35/kWh (O&M only) | 0.01 kg/kWh | Available or not — you do not control it |
| Battery | ₹1.20/kWh of throughput | inherits its charge | Finite energy, and using it now means not later |
| Utility grid | ₹4.50–11.50/kWh | 0.71 kg/kWh | Price changes by time of day; can fail entirely |
| Diesel | ₹21/kWh | 0.80 kg/kWh | Expensive and dirty — it exists for when the grid is gone |

**The engineering challenge.** Read that table and one thing should already be obvious, and it quietly
rewrites the whole problem:

> **You never choose between solar and the grid.**

Solar and wind cost almost nothing at the margin. Turning them down to buy grid power instead is never
correct. So renewables are *always* taken first, and the real decision is narrower and much sharper:

> **What covers the part renewables cannot?**

**The AI connection.** That reframing gives us five genuine decision classes — not five sources, but five
*strategies*:

| Class | What it means |
|---|---|
| `RENEWABLE` | Solar and wind cover the load. Any surplus charges the battery |
| `RENEWABLE + BATTERY` | Renewables plus battery discharge cover the load |
| `RENEWABLE + GRID` | Renewables plus grid import cover the load |
| `GRID + CHARGE` | Import from the grid *and* charge the battery — buying cheap energy for later |
| `DIESEL` | The grid is down and the battery cannot carry the load |

**Key takeaway:** the first job of an engineer on an AI project is to work out what the decision actually
is. Ours has five options, and none of them is "solar".

{link('sources', 'The five sources')}
""")

co(r"""
CLASSES = ["RENEWABLE", "RENEWABLE + BATTERY", "RENEWABLE + GRID", "GRID + CHARGE", "DIESEL"]
CLASS_COL = {"RENEWABLE": SOLAR, "RENEWABLE + BATTERY": BATT, "RENEWABLE + GRID": GRID,
             "GRID + CHARGE": "#7986cb", "DIESEL": DIESEL_C}

# What one kWh costs from each source, at each hour. The battery line is the interesting one:
# it is the cost of the energy that charged it, PLUS the wear of the cycle.
off_peak_charge = 4.50
plt.figure(figsize=(9.5, 4))
plt.step(hours, tariff(hours), where="post", color=GRID, lw=2.5, label="grid (time-of-use)")
plt.axhline(DIESEL_RS, color=DIESEL_C, lw=2.5, label=f"diesel ({DIESEL_RS:.0f})")
plt.axhline(0.30, color=SOLAR, lw=2.5, label="solar (0.30, when available)")
plt.axhline(0.35, color=WIND, lw=2.5, ls="--", label="wind (0.35, when available)")
plt.axhline(off_peak_charge / (ETA_C * ETA_D) + DEGRADE, color=BATT, lw=2.5,
            label=f"battery charged off-peak ({off_peak_charge/(ETA_C*ETA_D)+DEGRADE:.2f})")
plt.ylabel("Rs / kWh delivered"); plt.xlabel("hour of day"); plt.ylim(0, 23)
plt.legend(fontsize=8, ncol=2); plt.title("what a delivered kilowatt-hour costs, by source")
plt.tight_layout(); plt.show()

b_cost = off_peak_charge / (ETA_C * ETA_D) + DEGRADE
print(f"Battery discharge really costs: {off_peak_charge:.2f} to buy the energy,")
print(f"  divided by {ETA_C*ETA_D:.2f} round-trip efficiency = {off_peak_charge/(ETA_C*ETA_D):.2f},")
print(f"  plus {DEGRADE:.2f} of cycle wear  ->  {b_cost:.2f} Rs/kWh delivered.")
print()
print(f"So discharging into the {11.50:.2f} peak SAVES {11.50-b_cost:.2f} Rs/kWh.")
print(f"Discharging into the {8.00:.2f} normal rate saves only {8.00-b_cost:.2f}.")
print(f"Discharging into the {4.50:.2f} off-peak rate LOSES {b_cost-4.50:.2f} Rs/kWh.")
print()
print("A battery is not 'free stored energy'. Every one of those three lines is a decision,")
print("and getting them the wrong way round is the most common error in microgrid operation.")
""")

# ---------------------------------------------------------------- 3. data collection
md(rf"""
## 3 · One interval → data collection

**Engineering context.** Every fifteen minutes the SCADA system writes one row: what the campus drew, what
the array and turbine produced, where the battery sits, what the grid costs, and whether the grid is there
at all.

**The engineering challenge.** On their own these are eleven numbers on eleven screens. No single one tells
you what to do.

**The AI connection.** Put them in one row and the interval becomes a record. Thousands of those rows, each
paired with the decision that turned out to be best, are a dataset.

| Channel | Source | Unit | Why the decision needs it |
|---|---|---|---|
| Demand | Campus main meter | kW | The load that must be covered |
| Solar generation | Inverter | kW | Free energy, taken first |
| Wind generation | Turbine controller | kW | Free energy, taken first |
| Net load | Derived | kW | **demand − solar − wind.** The number the decision is really about |
| Battery SoC | BMS | % | How much room to manoeuvre is left |
| Grid price | Tariff schedule | ₹/kWh | What the alternative costs right now |
| Max price next 4 h | Tariff schedule | ₹/kWh | Whether it is worth *saving* the battery |
| Solar forecast, next 2 h | Weather service | kW | Whether free energy is coming |
| Hour of day | Clock | — | Encoded as a circle, not a number (Section 7) |
| Weekend | Calendar | 0/1 | A different load shape entirely |
| Grid available | Protection relay | 0/1 | Whether the grid is even an option |
| Ambient temperature | Weather station | °C | Drives cooling load and PV efficiency |

Two of those deserve attention now, because they are what make this a *decision* problem rather than a
description problem: **max price in the next four hours** and **solar forecast**. Both look forward. Without
them a model can only react to now, and the battery decision is never about now.

{link('reading', 'One SCADA interval')}
""")

co(r"""
def solar_profile(hour, cloud=1.0):
    "Clear-sky bell curve between about 06:30 and 18:30, scaled by a cloud factor."
    h = np.asarray(hour, float)
    x = np.clip((h - 6.5) / 12.0, 0, 1)
    return PV_KW * np.where((h > 6.5) & (h < 18.5), np.sin(np.pi * x) ** 1.3, 0.0) * cloud

def demand_profile(hour, weekend, rng=None):
    "Campus load: a night baseline plus a day shift, smaller at the weekend."
    h = np.asarray(hour, float)
    shift = np.exp(-((h - 13.0) ** 2) / (2 * 3.4 ** 2))          # broad working-day hump
    lunch = 0.18 * np.exp(-((h - 13.2) ** 2) / (2 * 0.5 ** 2))   # canteen dip
    base  = 150.0 + 300.0 * (shift - lunch) * (0.45 if weekend else 1.0)
    return np.maximum(base, 110.0)

hrs = np.arange(0, 24, DT)
fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
ax[0].plot(hrs, demand_profile(hrs, False), color=INK, lw=2, label="demand — weekday")
ax[0].plot(hrs, demand_profile(hrs, True), color=INK, lw=2, ls="--", label="demand — weekend")
ax[0].plot(hrs, solar_profile(hrs, 0.85), color=SOLAR, lw=2, label="solar (light cloud)")
ax[0].axhline(90, color=WIND, lw=2, ls=":", label="wind (a steady day)")
ax[0].set_ylabel("kW"); ax[0].legend(fontsize=8, ncol=2)
ax[0].set_title("a weekday on the campus microgrid")
net = demand_profile(hrs, False) - solar_profile(hrs, 0.85) - 90.0
ax[1].axhline(0, color=MUTED, lw=1)
ax[1].fill_between(hrs, 0, net, where=net > 0, color=DIESEL_C, alpha=0.30, label="must be bought or discharged")
ax[1].fill_between(hrs, 0, net, where=net <= 0, color=BATT, alpha=0.35, label="surplus — store it")
ax[1].plot(hrs, net, color=INK, lw=2)
ax[1].set_ylabel("net load (kW)"); ax[1].set_xlabel("hour of day"); ax[1].legend(fontsize=8)
ax[1].set_title("net load = demand - solar - wind:  the number the decision is actually about")
plt.tight_layout(); plt.show()

print("Note where the surplus sits (midday) and where the expensive hours sit (18:00-22:00).")
print("They do not overlap. That gap is the entire business case for the battery.")
""")

md(r"""
### The historian export

A real project starts by pulling a few months of logged intervals. We generate them here so the notebook is
self-contained and reproducible — same relationships, same faults you would meet on a real site.
""")

co(r"""
N_DAYS = 120

def make_history(n_days=N_DAYS, seed=42):
    "Four months of 15-minute intervals, as the SCADA historian would export them."
    rng = np.random.default_rng(seed)
    rows = []
    for d in range(n_days):
        weekend = (d % 7) in (5, 6)
        cloud_day = float(np.clip(rng.beta(5, 2), 0.15, 1.0))      # mostly clear, sometimes not
        wind_day  = float(np.clip(rng.weibull(2.0) * 0.55, 0.02, 1.0))
        temp_day  = float(rng.normal(29, 4))
        # grid outages: rare, and they last a while when they happen
        out_start = int(rng.integers(0, STEPS)) if rng.random() < 0.05 else -1
        out_len   = int(rng.integers(4, 14)) if out_start >= 0 else 0

        for k in range(STEPS):
            h = k * DT
            cloud = float(np.clip(cloud_day + rng.normal(0, 0.10), 0.05, 1.0))
            solar = float(solar_profile(h, cloud))
            wind  = float(np.clip(WT_KW * wind_day * (1 + 0.25 * rng.normal()), 0, WT_KW))
            dem   = float(demand_profile(h, weekend) * (1 + 0.05 * rng.normal()))
            gridok = not (out_start >= 0 and out_start <= k < out_start + out_len)
            rows.append(dict(day=d, step=k, hour=h, weekend=int(weekend),
                             demand_kw=dem, solar_kw=solar, wind_kw=wind,
                             grid_price=float(tariff(h)), grid_available=int(gridok),
                             temp_c=float(temp_day + 5 * np.sin(np.pi * (h - 7) / 14)),
                             cloud=cloud))
    df = pd.DataFrame(rows)
    df["net_load_kw"] = df.demand_kw - df.solar_kw - df.wind_kw

    # the faults every real export carries
    n = len(df)
    for c in ["demand_kw", "solar_kw", "wind_kw", "temp_c"]:
        df.loc[rng.choice(n, int(0.004 * n), replace=False), c] = np.nan
    df.loc[rng.choice(n, 40, replace=False), "solar_kw"]  = -6.0      # inverter night offset
    df.loc[rng.choice(n, 30, replace=False), "demand_kw"] = 0.0       # meter comms dropout
    df.loc[rng.choice(n, 25, replace=False), "wind_kw"]   = 9999.0    # anemometer spike
    return df

raw = make_history()
raw.to_csv("microgrid_history.csv", index=False)
print(f"wrote microgrid_history.csv — {len(raw):,} intervals over {N_DAYS} days")
raw.head()
""")

# ---------------------------------------------------------------- 4. load
md(rf"""
## 4 · Load the SCADA export

**Engineering context.** The export arrives as a CSV: one row per 15-minute interval.

**The engineering challenge.** An export is not a dataset. Inverters report small negative values at night,
meters drop out during comms failures, and an anemometer occasionally reports its full-scale value.

**The AI connection.** Loading it into a DataFrame is the first step — shape, types, and a first look.

{link('load', 'The historian export arrives')}
""")

co(r"""
df = pd.read_csv("microgrid_history.csv")
print("shape:", df.shape)
print(f"days: {df.day.nunique()}   intervals per day: {df.step.nunique()}")
print(f"grid unavailable in {100*(1-df.grid_available.mean()):.2f}% of intervals")
print()
print(df[["demand_kw", "solar_kw", "wind_kw", "net_load_kw", "grid_price"]].describe().T.round(1))
""")

# ---------------------------------------------------------------- 5. inspect
md(rf"""
## 5 · Data inspection — the meter health check

**Engineering context.** Before trusting four months of readings, an engineer checks the instruments.

**The engineering challenge.** A faulty channel does not report "faulty". It reports a number. A string
inverter reads a small **negative** power at night (it draws its own auxiliaries). A meter that loses comms
writes **0.0 kW** — and a campus never draws zero.

**The AI connection.** In a decision support system these matter more than usual: a wrong reading does not
produce a wrong *report*, it produces a wrong *action*. A demand meter stuck at 0 kW tells the controller
there is nothing to supply.

{link('inspect', 'Meter health check')}
""")

co(r"""
CHECK = ["demand_kw", "solar_kw", "wind_kw", "temp_c"]
print("Missing readings per channel")
print(df[CHECK].isna().sum(), "\n")
print(df[CHECK].describe().T[["min", "max"]])

fig, ax = plt.subplots(1, 3, figsize=(14, 3.4))
ax[0].bar(CHECK, df[CHECK].isna().sum().values, color=SOLAR)
ax[0].set_title("dropouts per channel"); ax[0].tick_params(axis="x", rotation=25)
night = df[(df.hour < 5) | (df.hour > 20)]
ax[1].hist(night.solar_kw.dropna(), bins=40, color=SOLAR)
ax[1].set_title("solar at night — should be zero"); ax[1].set_xlabel("kW")
ax[2].hist(df.demand_kw.dropna(), bins=60, color=INK)
ax[2].set_title("campus demand"); ax[2].set_xlabel("kW")
plt.tight_layout(); plt.show()

print(f"\nSolar below zero      : {int((df.solar_kw < 0).sum())} intervals")
print(f"Demand exactly zero   : {int((df.demand_kw == 0).sum())} intervals")
print(f"Wind above nameplate  : {int((df.wind_kw > WT_KW).sum())} intervals  (rating is {WT_KW:.0f} kW)")
print()
print("Each of those is a valid number and a fault at the same time. A turbine cannot exceed its")
print("own rating, and a campus with the lights on cannot draw zero.")
""")

# ---------------------------------------------------------------- 6. clean
md(rf"""
## 6 · Data cleaning

**Engineering context.** A faulty instrument is corrected or discounted before its readings drive anything.

**The engineering challenge.** Deleting whole intervals breaks the time series — and this dataset is a time
series, where the row before and the row after both matter.

**The AI connection.** So repair in place: clip what is physically impossible, and fill short gaps by
**interpolating in time** rather than with a global median. For a smooth quantity like demand, the value
fifteen minutes either side is a far better estimate than the average of four months.

{link('clean', 'Repairing the record')}
""")

co(r"""
clean = df.copy()

clean.loc[clean.solar_kw < 0, "solar_kw"] = 0.0                  # inverter auxiliary draw
clean.loc[clean.solar_kw > PV_KW * 1.05, "solar_kw"] = np.nan    # impossible irradiance
clean.loc[clean.wind_kw > WT_KW, "wind_kw"] = np.nan             # above nameplate
clean.loc[clean.demand_kw <= 1.0, "demand_kw"] = np.nan          # comms dropout

before_na = int(clean[CHECK].isna().sum().sum())
# interpolate WITHIN each day, so a gap at midnight never borrows from the previous evening
clean = clean.sort_values(["day", "step"]).reset_index(drop=True)
for c in CHECK:
    clean[c] = clean.groupby("day")[c].transform(
        lambda s: s.interpolate(limit_direction="both"))
    clean[c] = clean[c].fillna(clean[c].median())
clean["net_load_kw"] = clean.demand_kw - clean.solar_kw - clean.wind_kw

print(f"values repaired: {before_na}   still missing: {int(clean[CHECK].isna().sum().sum())}")

d0 = df[df.day == int(df.loc[df.demand_kw.isna(), 'day'].iloc[0])]
c0 = clean[clean.day == d0.day.iloc[0]]
plt.figure(figsize=(10, 3.4))
plt.plot(c0.hour, c0.demand_kw, color=BATT, lw=2.5, label="after — interpolated in time")
plt.plot(d0.hour, d0.demand_kw, color=DIESEL_C, lw=1.5, label="before — gaps and dropouts")
plt.ylabel("demand (kW)"); plt.xlabel("hour"); plt.legend(fontsize=8)
plt.title("one day, before and after cleaning")
plt.tight_layout(); plt.show()

print("Interpolating in time keeps the SHAPE of the day. Filling with a global median would")
print("have punched a flat step into the middle of the morning ramp — and the shape is what")
print("every decision from Section 10 onwards is made from.")
""")

# ---------------------------------------------------------------- 7. features
md(rf"""
## 7 · Preparing the inputs — scaling, cyclical time, forecasts

**Engineering context.** The model has to read conditions in the units they arrive in: kilowatts, percent,
rupees, hours.

**The engineering challenge.** Three problems, and the middle one catches nearly everybody.

1. **Scale.** Demand runs to 450, price to 11.5, SoC to 95. A model that measures distance lets the biggest
   number win. Standardise.
2. **Hour of day is a circle, not a line.** Hour 23 and hour 0 are fifteen minutes apart, but as plain
   numbers they are as far apart as it is possible to be. Feed the raw hour in and the model learns a false
   cliff at midnight. Encode it as `sin` and `cos` of the angle instead — then 23:45 and 00:00 sit next to
   each other, as they should.
3. **Looking forward.** The decision to save the battery is a decision about the *next four hours*. So the
   tariff schedule (known exactly, published in advance) and the solar forecast (available from any weather
   service, with error) become inputs.

**The AI connection.** Feature preparation is where engineering knowledge enters the model. Nothing here is
a statistical trick; every line is a physical fact about the plant written in a form a model can use.

{link('features', 'Encoding the conditions')}
""")

co(r"""
def add_features(d, rng=None):
    "Everything the controller can legitimately observe at decision time."
    rng = rng or np.random.default_rng(0)
    d = d.copy()
    ang = 2 * np.pi * d.hour / 24.0
    d["hour_sin"], d["hour_cos"] = np.sin(ang), np.cos(ang)

    # the tariff is PUBLISHED, so perfect knowledge of future price is legitimate
    fwd = np.arange(1, 17) * DT                       # the next 4 hours
    d["price_max_next4h"] = np.max(
        [tariff(d.hour.values + f) for f in fwd], axis=0)

    # the solar forecast is NOT perfect. A weather service gets it roughly right.
    fc_err = rng.normal(1.0, 0.18, len(d))
    fc = np.mean([solar_profile(d.hour.values + f, 1.0) for f in np.arange(1, 9) * DT], axis=0)
    d["solar_fc_next2h"] = np.clip(fc * d.cloud.values * fc_err, 0, PV_KW)
    return d

FEATURES = ["demand_kw", "solar_kw", "wind_kw", "net_load_kw", "battery_soc",
            "grid_price", "price_max_next4h", "solar_fc_next2h",
            "hour_sin", "hour_cos", "weekend", "grid_available", "temp_c"]

feat = add_features(clean)
print("Why the hour has to be a circle:")
for a, b in [(23.75, 0.0), (11.75, 12.0)]:
    plain = abs(a - b)
    circ  = np.hypot(np.sin(2*np.pi*a/24) - np.sin(2*np.pi*b/24),
                     np.cos(2*np.pi*a/24) - np.cos(2*np.pi*b/24))
    print(f"  {a:5.2f}h to {b:5.2f}h — as a plain number {plain:5.2f} apart, on the circle {circ:.3f}")
print("\nBoth pairs are 15 minutes apart in reality. Only the circular encoding agrees.")

fig, ax = plt.subplots(1, 2, figsize=(11, 3.4))
ax[0].plot(feat[feat.day == 3].hour, feat[feat.day == 3].grid_price, color=GRID, lw=2, label="price now")
ax[0].plot(feat[feat.day == 3].hour, feat[feat.day == 3].price_max_next4h, color=DIESEL_C, lw=2,
           ls="--", label="max price in the next 4 h")
ax[0].set_xlabel("hour"); ax[0].set_ylabel("Rs/kWh"); ax[0].legend(fontsize=8)
ax[0].set_title("the feature that lets a model SAVE the battery")
ax[1].plot(feat[feat.day == 3].hour, feat[feat.day == 3].solar_kw, color=SOLAR, lw=2, label="solar now")
ax[1].plot(feat[feat.day == 3].hour, feat[feat.day == 3].solar_fc_next2h, color=INK, lw=2,
           ls="--", label="forecast, next 2 h (imperfect)")
ax[1].set_xlabel("hour"); ax[1].set_ylabel("kW"); ax[1].legend(fontsize=8)
ax[1].set_title("the forecast is wrong, and still useful")
plt.tight_layout(); plt.show()
""")

# ---------------------------------------------------------------- 8. split
md(rf"""
## 8 · The split that does not lie — by day, not by row

**Engineering context.** We need to test on data the model has not seen.

**The engineering challenge.** Here is the trap. Split 15-minute readings **at random** and 14:00 goes into
training while 14:15 goes into test. Those two rows are nearly identical — same weather, same shift, same
tariff, battery barely moved. The model does not have to generalise; it only has to remember its neighbour.

The reported accuracy will be excellent. It will also be **fiction**, and you will only find out after the
system is commissioned.

**The AI connection.** Split by **whole days**. Every interval of a test day is unseen, exactly as it will
be on a live plant tomorrow morning. Below we measure how large the lie is.

{link('split', 'Splitting time properly')}
""")

co(r"""
all_days   = np.arange(N_DAYS)
train_days = all_days[:int(0.70 * N_DAYS)]
val_days   = all_days[int(0.70 * N_DAYS):int(0.80 * N_DAYS)]
test_days  = all_days[int(0.80 * N_DAYS):]

print(f"train days {train_days[0]:3d}-{train_days[-1]:3d}   ({len(train_days)} days)")
print(f"val   days {val_days[0]:3d}-{val_days[-1]:3d}   ({len(val_days)} days)")
print(f"test  days {test_days[0]:3d}-{test_days[-1]:3d}   ({len(test_days)} days)")
print()
print("Note that the test days come LAST, not from the middle. A model deployed on Monday is")
print("asked about Tuesday — never about a Tuesday that sits between two days it already knows.")
""")

# ---------------------------------------------------------------- 9. the rule
md(rf"""
## 9 · The rule the plant already runs

**Engineering context.** Before any AI, this is what a real microgrid controller does: a short ladder of
`if` statements, written by an experienced engineer, tuned once, and left alone for years.

**The engineering challenge.** The rule is **myopic**. It can only see the present interval. It cannot
know that the battery it is about to spend at 15:00 on ₹8 energy would have been worth ₹11.50 at 19:00.

**The AI connection.** This rule is not the enemy. It is the **baseline**, and it is a strong one — it is
simple, auditable, and it has kept the campus running. Anything we build has to beat it in rupees, not in
accuracy.

{link('rule', 'The controller that exists today')}
""")

co(r"""
def rule_decision(net, soc, price, gridok, price_max4):
    "The myopic controller a plant engineer would write. It sees only this interval."
    if not gridok:
        return "RENEWABLE + BATTERY" if (soc > SOC_MIN + 12 and net > 0) else (
               "DIESEL" if net > 0 else "RENEWABLE")
    if net <= 0:
        return "RENEWABLE"                            # surplus: store it
    if price >= 11.0 and soc > 40:
        return "RENEWABLE + BATTERY"                  # peak: use the battery
    if price <= 5.0 and soc < 80:
        return "GRID + CHARGE"                        # off-peak: fill up
    return "RENEWABLE + GRID"

# What the rule does across one representative day
d = feat[feat.day == 3].reset_index(drop=True)
soc, seq = 55.0, []
for _, r in d.iterrows():
    seq.append(rule_decision(r.net_load_kw, soc, r.grid_price, bool(r.grid_available),
                             r.price_max_next4h))
    soc = float(np.clip(soc + (-r.net_load_kw * DT / CAP_KWH * 100) * 0.3, SOC_MIN, SOC_MAX))

plt.figure(figsize=(11, 2.4))
for i, s in enumerate(seq):
    plt.axvspan(d.hour[i], d.hour[i] + DT, color=CLASS_COL[s], alpha=0.9)
plt.xlim(0, 24); plt.yticks([]); plt.xlabel("hour of day")
plt.title("the rule's decisions across one day")
handles = [plt.Rectangle((0, 0), 1, 1, color=CLASS_COL[c]) for c in CLASSES]
plt.legend(handles, CLASSES, fontsize=7, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.45))
plt.tight_layout(); plt.show()

print(pd.Series(seq).value_counts().to_string())
""")

# ---------------------------------------------------------------- 10. the optimiser
md(rf"""
## 10 · Where the labels come from — the perfect-foresight optimiser

**Engineering context.** To train a model to make good decisions, we need examples of good decisions. So:
what *was* the best thing to do at 14:00 last Tuesday?

**The engineering challenge.** That question has an exact answer, and it is not an opinion. Given the whole
day — every kW of solar, every rupee of tariff — the cheapest feasible way to run the microgrid can be
**computed**. The only difficulty is that the battery couples every interval to every other one, so you
cannot decide each interval separately.

**The AI connection.** **Dynamic programming** solves exactly this. Work backwards from midnight: for each
possible battery state, at each interval, record the cheapest way to finish the day. Then walk forwards from
the morning's actual state and read off the decisions.

The result is the **perfect-foresight optimum** — a controller that knew the future exactly. No real system
can achieve it. That is the point: it is the **unreachable lower bound** that tells us how much room for
improvement actually exists.

> The labels are not somebody's opinion of the right answer. They are the arithmetic of the right answer.

{link('optimiser', 'Working backwards from midnight')}
""")

co(r"""
SOC_LEVELS = np.linspace(SOC_MIN, SOC_MAX, 61)          # 1.25 % steps
SOC_STEP   = SOC_LEVELS[1] - SOC_LEVELS[0]
ACTIONS    = np.linspace(-P_BAT, P_BAT, 17)             # kW, positive = discharge

# battery power -> change in state of charge (%), including efficiency both ways
_d = np.where(ACTIONS > 0, -(ACTIONS * DT / ETA_D) / CAP_KWH * 100.0,
                           -(ACTIONS * DT * ETA_C) / CAP_KWH * 100.0)
_new = SOC_LEVELS[:, None] + _d[None, :]
_ok  = (_new >= SOC_MIN - 1e-9) & (_new <= SOC_MAX + 1e-9)
_idx = np.clip(np.round((_new - SOC_MIN) / SOC_STEP).astype(int), 0, len(SOC_LEVELS) - 1)

def interval_cost(net, price, gridok):
    "Cost of every candidate battery action in one interval, Rs. Returns (A,) arrays."
    supply = net - ACTIONS                       # what still has to come from somewhere
    need   = np.maximum(supply, 0.0)
    if gridok:
        grid, dies = need, np.zeros_like(need)
    else:
        grid, dies = np.zeros_like(need), np.minimum(need, DIESEL_KW)
    unserved = need - grid - dies
    cost = (grid * price + dies * DIESEL_RS + unserved * VOLL) * DT \
           + np.abs(ACTIONS) * DT * DEGRADE
    return cost, grid, dies

def solve_day(net, price, gridok, soc0=55.0):
    "Exact cheapest dispatch for one whole day, by backward dynamic programming."
    T = len(net)
    V   = np.zeros((T + 1, len(SOC_LEVELS)))
    POL = np.zeros((T, len(SOC_LEVELS)), dtype=int)
    for t in range(T - 1, -1, -1):
        c, _, _ = interval_cost(net[t], price[t], bool(gridok[t]))
        tot = np.where(_ok, c[None, :] + V[t + 1][_idx], np.inf)
        POL[t] = np.argmin(tot, axis=1)
        V[t]   = tot[np.arange(len(SOC_LEVELS)), POL[t]]

    s = int(np.clip(round((soc0 - SOC_MIN) / SOC_STEP), 0, len(SOC_LEVELS) - 1))
    out = []
    for t in range(T):
        a = POL[t, s]
        c, g, dsl = interval_cost(net[t], price[t], bool(gridok[t]))
        out.append(dict(bat_kw=ACTIONS[a], grid_kw=g[a], diesel_kw=dsl[a],
                        cost=c[a], soc=SOC_LEVELS[s]))
        s = _idx[s, a]
    return pd.DataFrame(out)

def label_of(bat_kw, grid_kw, diesel_kw):
    "Turn a dispatch into one of the five decision classes."
    if diesel_kw > 1.0:            return "DIESEL"
    if bat_kw < -1.0 and grid_kw > 1.0: return "GRID + CHARGE"
    if bat_kw > 1.0:               return "RENEWABLE + BATTERY"
    if grid_kw > 1.0:              return "RENEWABLE + GRID"
    return "RENEWABLE"

# Solve every day in the history
sol = []
for d_i in range(N_DAYS):
    g = feat[feat.day == d_i]
    s = solve_day(g.net_load_kw.values, g.grid_price.values, g.grid_available.values)
    s["day"], s["step"] = d_i, g.step.values
    sol.append(s)
sol = pd.concat(sol, ignore_index=True)
sol["label"] = [label_of(b, g, x) for b, g, x in
                zip(sol.bat_kw, sol.grid_kw, sol.diesel_kw)]

data = feat.merge(sol[["day", "step", "label", "soc", "cost"]], on=["day", "step"])
data = data.rename(columns={"soc": "battery_soc"})
print("Optimal decisions across", N_DAYS, "days:")
print(data.label.value_counts().to_string())
print(f"\nPerfect-foresight cost: Rs {sol.cost.sum():,.0f} over {N_DAYS} days "
      f"(Rs {sol.cost.sum()/N_DAYS:,.0f}/day)")
""")

co(r"""
# What the optimum actually does on one clear day — this is the behaviour we want a model to learn
d_i = 3
g   = data[data.day == d_i].reset_index(drop=True)
s   = sol[sol.day == d_i].reset_index(drop=True)

fig, ax = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
ax[0].plot(g.hour, g.demand_kw, color=INK, lw=2, label="demand")
ax[0].fill_between(g.hour, 0, g.solar_kw, color=SOLAR, alpha=0.55, label="solar")
ax[0].fill_between(g.hour, g.solar_kw, g.solar_kw + g.wind_kw, color=WIND, alpha=0.55, label="wind")
ax[0].set_ylabel("kW"); ax[0].legend(fontsize=8, ncol=3); ax[0].set_title("supply and demand")
ax[1].axhline(0, color=MUTED, lw=1)
ax[1].fill_between(g.hour, 0, s.bat_kw, where=s.bat_kw > 0, color=BATT, alpha=0.7, label="discharging")
ax[1].fill_between(g.hour, 0, s.bat_kw, where=s.bat_kw < 0, color="#7986cb", alpha=0.7, label="charging")
ax[1].plot(g.hour, s.soc, color=INK, lw=2, label="state of charge (%)")
ax[1].set_ylabel("kW  /  %"); ax[1].legend(fontsize=8, ncol=3)
ax[1].set_title("the battery: charged when energy is cheap, spent when it is dear")
ax[2].step(g.hour, g.grid_price, where="post", color=GRID, lw=2)
for i in range(len(g)):
    ax[2].axvspan(g.hour[i], g.hour[i] + DT, color=CLASS_COL[g.label[i]], alpha=0.30)
ax[2].set_ylabel("Rs/kWh"); ax[2].set_xlabel("hour of day")
ax[2].set_title("tariff, shaded by the optimal decision")
plt.tight_layout(); plt.show()

print("Read the middle panel. The optimum charges through the cheap night and the solar surplus,")
print("holds through the middle of the day, and spends the battery into the evening peak.")
print("Nobody told it the tariff structure. It worked the schedule out from the arithmetic.")
""")

# ---------------------------------------------------------------- 11. the trap
md(rf"""
## 11 · The trap — learning your own rule back

**Engineering context.** Here is the shortcut almost every "AI decision support" project takes, and it is
worth watching it fail before we do it properly.

You have no labelled history of good decisions. So you write a sensible rule, run it over your data to
generate labels, and train a model on those labels. The model scores 99%. Everybody is delighted.

**The engineering challenge.** Think about what that 99% means. The model has learned to reproduce the rule
— **including every mistake the rule makes.** It cannot be better than the rule, because the rule defined
what "correct" means. You have replaced twelve auditable lines of `if` with a black box that does the same
thing slightly less reliably, and paid for a GPU to do it.

**The AI connection.** Accuracy against your own labels measures *agreement*, not *quality*. This is why
Section 10 went to the trouble of computing a real optimum: it is the one label source that is not simply
our own opinion reflected back at us.

{link('trap', 'The circular project')}
""")

co(r"""
# Label the same data two ways: with the rule, and with the optimiser
rule_labels = [rule_decision(r.net_load_kw, r.battery_soc, r.grid_price,
                             bool(r.grid_available), r.price_max_next4h)
               for _, r in data.iterrows()]
data["rule_label"] = rule_labels

tr = data[data.day.isin(train_days)]
te = data[data.day.isin(test_days)]

m_rule = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
m_rule.fit(tr[FEATURES], tr.rule_label)
acc_rule = accuracy_score(te.rule_label, m_rule.predict(te[FEATURES]))

m_opt = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
m_opt.fit(tr[FEATURES], tr.label)
acc_opt = accuracy_score(te.label, m_opt.predict(te[FEATURES]))

print(f"Model trained on the RULE's labels    — accuracy vs the rule      : {acc_rule:.1%}")
print(f"Model trained on the OPTIMISER's labels — accuracy vs the optimum : {acc_opt:.1%}")
print()
print("The first number is higher. It is also worth nothing: a model that agrees with the rule")
print(f"{acc_rule:.0%} of the time saves, at absolute best, {0:.0f} rupees — because the rule is")
print("already running. The most it can do is imitate what the plant does today.")
print()
print("The second number is lower BECAUSE the target is harder. It is the only one of the two")
print("that can lead to a saving, and Section 17 measures what that saving actually is.")
print()
print("How often does the rule already agree with the optimum?")
print(f"  {accuracy_score(data.label, data.rule_label):.1%} of intervals.")
print("  Every point of disagreement is money the plant is currently leaving on the table.")
""")

# ---------------------------------------------------------------- 12. the model
md(rf"""
## 12 · The decision model — tree, forest, boosting

**Engineering context.** Now we train a model to map observable conditions to the decision the optimiser
would have made.

**The engineering challenge.** The model has a genuine handicap and it is important to be honest about it:
the optimiser **knew the future**; the model does not. It sees the published tariff and an imperfect solar
forecast. It is being asked to imitate a controller with information it will never have. Perfect agreement
is not possible, and would be suspicious if it appeared.

**The AI connection.** Three models, deliberately in order of transparency:

- **Decision Tree** — a flowchart. You can print it and hand it to an engineer.
- **Random Forest** — hundreds of trees voting. More accurate, less readable.
- **Gradient Boosting / XGBoost** — trees that each fix the previous one's errors.

And here we settle the split question from Section 8, by measuring it.

{link('models', 'Three ways to learn a decision')}
""")

co(r"""
Xtr, ytr = tr[FEATURES], tr.label
Xte, yte = te[FEATURES], te.label

models = {
    "Decision Tree (depth 5)": DecisionTreeClassifier(max_depth=5, random_state=42),
    "Decision Tree (full)":    DecisionTreeClassifier(random_state=42),
    "Random Forest":           RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1),
    "Gradient Boosting":       GradientBoostingClassifier(random_state=42),
}
if XGB:
    models["XGBoost"] = XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1,
                                      tree_method="hist", random_state=42)

codes = {c: i for i, c in enumerate(CLASSES)}
fitted, scores = {}, {}
for name, m in models.items():
    if name == "XGBoost":
        m.fit(Xtr, ytr.map(codes))
        p = pd.Series(m.predict(Xte)).map({i: c for c, i in codes.items()}).values
    else:
        m.fit(Xtr, ytr); p = m.predict(Xte)
    fitted[name], scores[name] = m, accuracy_score(yte, p)
    print(f"{name:26s} agreement with the optimum: {scores[name]:.1%}")

best_name = max(scores, key=scores.get)
clf = fitted[best_name]
print(f"\nBest: {best_name}")
""")

co(r"""
# --- how big is the random-split lie? (Section 8, measured) ----------------
from sklearn.model_selection import train_test_split as tts
r_tr, r_te = tts(data, test_size=0.30, random_state=42, shuffle=True)     # WRONG: splits rows
m_bad = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1)
m_bad.fit(r_tr[FEATURES], r_tr.label)
acc_bad = accuracy_score(r_te.label, m_bad.predict(r_te[FEATURES]))

acc_good = scores["Random Forest"]
print(f"Random Forest, rows split at random : {acc_bad:.1%}   <- the number that gets reported")
print(f"Random Forest, split by whole days  : {acc_good:.1%}   <- the number that is true")
print(f"Inflation from leakage              : {100*(acc_bad-acc_good):.1f} percentage points")
print()
print("Same model, same data, same code. The only difference is that in the first split,")
print("14:00 was in training while 14:15 was in test — and fifteen minutes apart on a")
print("microgrid, almost nothing has changed. The model was graded on its own notes.")

plt.figure(figsize=(7.5, 3.4))
plt.barh(["split by day\n(honest)", "split by row\n(leaks)"], [acc_good, acc_bad],
         color=[BATT, DIESEL_C])
plt.xlim(0, 1); plt.xlabel("reported accuracy")
for i, v in enumerate([acc_good, acc_bad]):
    plt.text(v + 0.01, i, f"{v:.1%}", va="center")
plt.title("the same model, scored two ways")
plt.tight_layout(); plt.show()
""")

# ---------------------------------------------------------------- 13. importance
md(rf"""
## 13 · Feature importance — what drives the decision

**Engineering context.** An engineer asked to trust a recommendation will first ask what it is looking at.

**The engineering challenge.** If the model's priorities do not match engineering sense, either the model is
wrong or your understanding is — and you must find out which **before** commissioning, not after.

**The AI connection.** Feature importance ranks how much each input moves the decision. Read it as a
sanity check, not as physics.

{link('importance', 'What the model watches')}
""")

co(r"""
rf = fitted["Random Forest"]
imp = pd.Series(rf.feature_importances_, index=FEATURES).sort_values(ascending=False)

plt.figure(figsize=(9, 4))
plt.barh(imp.index[::-1], imp.values[::-1], color=GRID)
plt.xlabel("importance"); plt.title("what the decision model watches")
plt.tight_layout(); plt.show()
print(imp.round(3).to_string())
""")

md(r"""
Read the ranking against engineering sense:

- **Net load** near the top is exactly right. It *is* the decision variable — the kilowatts that renewables
  cannot cover.
- **Battery state of charge** matters because it decides which options are even legal. At 21% the battery is
  not an option at any price.
- **Price now** and **max price in the next four hours** both appear, and the second is the interesting one.
  It is the model learning to *wait* — to leave the battery alone at ₹8 because ₹11.50 is coming.
- **Grid availability** looks unimportant because it is almost always 1. Importance is driven by how often a
  feature changes an answer, not by how much it matters when it does. When the grid fails, that one bit
  overrides everything else — see Section 19.

**Key takeaway:** importance tells you what the model uses, never what causes what — and a feature that is
rarely used can still be the most critical one on the plant.
""")

# ---------------------------------------------------------------- 14. explaining
md(rf"""
## 14 · Explaining one decision

**Engineering context.** "Discharge the battery" is not an instruction an engineer will follow from a black
box. They will ask why.

**The engineering challenge.** A recommendation that cannot be explained will be overridden — and a
decision support system that is always overridden is just an expensive screen.

**The AI connection.** A shallow decision tree is a flowchart. Print it, and the reasoning is right there.
This is why we keep a depth-5 tree in the lineup even though the forest scores higher: **the tree is what
you show the plant manager.**

{link('explain', 'Reading the decision path')}
""")

co(r"""
tree = fitted["Decision Tree (depth 5)"]
plt.figure(figsize=(17, 8))
plot_tree(tree, feature_names=FEATURES, class_names=tree.classes_,
          filled=True, rounded=True, fontsize=7, max_depth=3, impurity=False, proportion=True)
plt.title("the decision tree, top three levels — the whole policy on one page")
plt.tight_layout(); plt.show()

def explain_path(model, row):
    "Walk one sample down the tree and print the tests it passed."
    t = model.tree_
    node, steps = 0, []
    while t.children_left[node] != -1:
        f, thr = FEATURES[t.feature[node]], t.threshold[node]
        v = float(row[f])
        if v <= thr:
            steps.append(f"{f} = {v:.1f}  <=  {thr:.1f}"); node = t.children_left[node]
        else:
            steps.append(f"{f} = {v:.1f}   >  {thr:.1f}"); node = t.children_right[node]
    return steps, model.classes_[int(np.argmax(t.value[node][0]))]

peak = te[(te.grid_price > 11) & (te.battery_soc > 60)]
sample = peak.iloc[0] if len(peak) else te.iloc[0]
steps, leaf = explain_path(tree, sample)
print("One interval, and the exact reasoning behind its recommendation:\n")
for i, s in enumerate(steps, 1):
    print(f"  {i}. {s}")
print(f"\n  -> recommendation: {leaf}")
print(f"     (the optimiser's answer for this interval was: {sample.label})")
""")

# ---------------------------------------------------------------- 15. live demo
md(rf"""
## 15 · The live recommendation — try it yourself

**Engineering context.** This is the decision support system as an engineer would meet it: current
conditions in, a recommendation and its reasoning out.

**The engineering challenge.** A recommendation without its reasoning is an order. Engineers do not take
orders from software, and they are right not to.

**The AI connection.** Every recommendation below comes with the model's confidence, the expected cost, and
an engineering explanation assembled from the conditions that drove it.

Change the numbers in the call and re-run. If `ipywidgets` is available, sliders appear too.

{link('live', 'The recommendation panel')}
""")

co(r"""
def recommend(demand_kw=320.0, solar_kw=280.0, wind_kw=40.0, battery_soc=85.0,
              hour=14.0, weekend=0, grid_available=1, temp_c=31.0, cloud=0.9,
              model=None, verbose=True):
    "The decision support system: conditions in, recommendation and reasoning out."
    model = model or rf
    net   = demand_kw - solar_kw - wind_kw
    price = float(tariff(hour))
    pmax4 = float(np.max([tariff(hour + f) for f in np.arange(1, 17) * DT]))
    fc    = float(np.mean([solar_profile(hour + f, cloud) for f in np.arange(1, 9) * DT]))
    row = pd.DataFrame([{
        "demand_kw": demand_kw, "solar_kw": solar_kw, "wind_kw": wind_kw, "net_load_kw": net,
        "battery_soc": battery_soc, "grid_price": price, "price_max_next4h": pmax4,
        "solar_fc_next2h": fc, "hour_sin": np.sin(2*np.pi*hour/24),
        "hour_cos": np.cos(2*np.pi*hour/24), "weekend": weekend,
        "grid_available": grid_available, "temp_c": temp_c}])[FEATURES]

    pred = model.predict(row)[0]
    conf = float(np.max(model.predict_proba(row)))

    # engineering reasoning, assembled from the conditions that actually drove it
    why = []
    if net <= 0:
        why.append(f"renewables exceed demand by {-net:.0f} kW — free energy, take it first")
    else:
        why.append(f"renewables leave a {net:.0f} kW gap that must be covered")
    if price >= 11.0:  why.append(f"grid is at peak tariff ({price:.2f} Rs/kWh) — avoid importing")
    elif price <= 5.0: why.append(f"grid is off-peak ({price:.2f} Rs/kWh) — cheapest time to buy")
    else:              why.append(f"grid is at the normal rate ({price:.2f} Rs/kWh)")
    if pmax4 > price:  why.append(f"a more expensive window ({pmax4:.2f}) arrives within 4 h — worth saving charge")
    if battery_soc < SOC_MIN + 10: why.append(f"battery at {battery_soc:.0f}% — too low to rely on")
    elif battery_soc > 70:         why.append(f"battery at {battery_soc:.0f}% — plenty of headroom")
    if not grid_available:         why.append("GRID IS DOWN — islanded operation")

    usable = max(battery_soc - SOC_MIN, 0) / 100 * CAP_KWH
    cost_map = {"RENEWABLE": 0.30, "RENEWABLE + BATTERY": price*0 + off_peak_charge/(ETA_C*ETA_D)+DEGRADE,
                "RENEWABLE + GRID": price, "GRID + CHARGE": price, "DIESEL": DIESEL_RS}
    if verbose:
        print(f"CONDITIONS  demand {demand_kw:.0f} kW | solar {solar_kw:.0f} | wind {wind_kw:.0f} | "
              f"net {net:+.0f} kW | SoC {battery_soc:.0f}% | {price:.2f} Rs/kWh | {hour:.2f} h")
        print(f"\n  RECOMMENDATION : {pred}")
        print(f"  CONFIDENCE     : {conf:.0%}")
        print(f"  MARGINAL COST  : ~{cost_map[pred]:.2f} Rs/kWh")
        print(f"  BATTERY USABLE : {usable:.0f} kWh above the {SOC_MIN:.0f}% floor")
        print("\n  WHY:")
        for w in why:
            print(f"    - {w}")
        print("\n  The engineer approves, overrides, or ignores this. It is a recommendation.")
    return pred, conf, why

# The worked example from the course brief
recommend(demand_kw=320, solar_kw=280, wind_kw=20, battery_soc=85, hour=14.0)
""")

co(r"""
print("=" * 78)
print("The same system, four hours later — nothing changed but the sun and the tariff")
print("=" * 78)
recommend(demand_kw=320, solar_kw=0, wind_kw=20, battery_soc=85, hour=19.0)

if WIDGETS:
    widgets.interact(
        lambda demand, solar, wind, soc, hour, grid: recommend(
            demand_kw=demand, solar_kw=solar, wind_kw=wind,
            battery_soc=soc, hour=hour, grid_available=int(grid)),
        demand=widgets.FloatSlider(min=100, max=500, step=10, value=320, description="Demand kW"),
        solar=widgets.FloatSlider(min=0, max=400, step=10, value=280, description="Solar kW"),
        wind=widgets.FloatSlider(min=0, max=250, step=10, value=20, description="Wind kW"),
        soc=widgets.FloatSlider(min=20, max=95, step=1, value=85, description="SoC %"),
        hour=widgets.FloatSlider(min=0, max=23.75, step=0.25, value=14, description="Hour"),
        grid=widgets.Checkbox(value=True, description="Grid available"))
else:
    print("\n(ipywidgets not available — edit the numbers in the call above and re-run.)")
""")

# ---------------------------------------------------------------- 16. wrong score
md(rf"""
## 16 · Why decision accuracy is the wrong score

**Engineering context.** Every number so far has been "agreement with the optimum". A plant manager does not
buy agreement.

**The engineering challenge.** Consider two mistakes the model can make:

- It says `RENEWABLE + GRID` when the optimum said `GRID + CHARGE`. Both import from the grid at the same
  price. The difference is a little battery positioning. Cost of being wrong: **a few rupees.**
- It says `RENEWABLE + BATTERY` when the battery is nearly flat and the grid is down. Cost of being wrong:
  **the diesel starts, or the campus goes dark.**

Accuracy counts those as one error each. They are not the same error.

**The AI connection.** Replace accuracy with **cost regret** — how many more rupees did this decision cost
than the optimum would have? Regret is measured in the units the plant actually cares about, and it
automatically weights each mistake by how much it matters.

{link('regret', 'Not all mistakes cost the same')}
""")

co(r"""
# What each confusion actually costs, per interval, in rupees
def dispatch_cost(action, net, soc, price, gridok):
    "Execute a decision class and return (rupees, new soc, kW from each source)."
    room_dis = max(soc - SOC_MIN, 0) / 100 * CAP_KWH * ETA_D / DT     # kW available to discharge
    room_chg = max(SOC_MAX - soc, 0) / 100 * CAP_KWH / ETA_C / DT     # kW of charging headroom
    b = 0.0
    if action == "RENEWABLE":
        b = -min(max(-net, 0.0), P_BAT, room_chg)                     # store any surplus
    elif action == "RENEWABLE + BATTERY":
        b = min(max(net, 0.0), P_BAT, room_dis)
    elif action == "RENEWABLE + GRID":
        b = -min(max(-net, 0.0), P_BAT, room_chg) if net < 0 else 0.0
    elif action == "GRID + CHARGE":
        b = -min(P_BAT, room_chg)
    elif action == "DIESEL":
        b = min(max(net, 0.0), P_BAT, room_dis)
    need = max(net - b, 0.0)
    if gridok:
        grid, dies = need, 0.0
    else:
        grid, dies = 0.0, min(need, DIESEL_KW)
    unserved = need - grid - dies
    cost = (grid * price + dies * DIESEL_RS + unserved * VOLL) * DT + abs(b) * DT * DEGRADE
    dsoc = (-(b * DT / ETA_D) if b > 0 else -(b * DT * ETA_C)) / CAP_KWH * 100
    return cost, float(np.clip(soc + dsoc, SOC_MIN, SOC_MAX)), grid, dies, b

# Regret of every possible confusion, averaged over the test intervals
reg = pd.DataFrame(0.0, index=CLASSES, columns=CLASSES)
sample = te.sample(min(600, len(te)), random_state=0)
for _, r in sample.iterrows():
    base, *_ = dispatch_cost(r.label, r.net_load_kw, r.battery_soc, r.grid_price, bool(r.grid_available))
    for c in CLASSES:
        alt, *_ = dispatch_cost(c, r.net_load_kw, r.battery_soc, r.grid_price, bool(r.grid_available))
        reg.loc[r.label, c] += (alt - base)
reg /= len(sample)

fig, ax = plt.subplots(figsize=(7.6, 5.6))
im = ax.imshow(reg.values, cmap="Reds")
ax.set_xticks(range(5)); ax.set_xticklabels(CLASSES, rotation=40, ha="right", fontsize=8)
ax.set_yticks(range(5)); ax.set_yticklabels(CLASSES, fontsize=8)
ax.set_xlabel("what the model said"); ax.set_ylabel("what was optimal")
for i in range(5):
    for j in range(5):
        ax.text(j, i, f"{reg.values[i,j]:.1f}", ha="center", va="center", fontsize=8,
                color="white" if reg.values[i, j] > reg.values.max()*0.55 else "black")
ax.set_title("average regret per interval, in Rs\n(0 on the diagonal — those are the right answers)")
plt.colorbar(im, ax=ax, shrink=0.8); plt.tight_layout(); plt.show()

flat = reg.where(~np.eye(5, dtype=bool)).stack()
print("Cheapest mistakes to make:")
print(flat.nsmallest(3).round(2).to_string())
print("\nMost expensive mistakes to make:")
print(flat.nlargest(3).round(2).to_string())
print("\nAccuracy treats every one of these as a single error. The plant does not.")
""")

# ---------------------------------------------------------------- 17. closed loop
md(rf"""
## 17 · Closed-loop evaluation — a month of test days

**Engineering context.** The real test is not "did it pick the same label". It is: **run the plant with this
controller for a month and count the money.**

**The engineering challenge.** A controller changes the state it will meet next. Discharge the battery now
and the next interval starts lower. So you cannot score decisions one row at a time — you must simulate the
whole day with the controller **in the loop**, carrying its own consequences.

**The AI connection.** Three controllers, on the same unseen test days:

1. **The rule** — the plant's current controller, and a strong baseline.
2. **The ML model** — recommending from observable conditions only.
3. **Perfect foresight** — the DP optimum. Unreachable, and that is the point: it tells us how much of the
   remaining gap is even winnable.

{link('closed-loop', 'A month, three controllers')}
""")

co(r"""
def run_day(day_df, controller, soc0=55.0):
    "Simulate one day with a controller in the loop. Returns the running record."
    soc, rec = soc0, []
    for _, r in day_df.iterrows():
        act = controller(r, soc)
        cost, soc, grid, dies, b = dispatch_cost(act, r.net_load_kw, soc, r.grid_price,
                                                 bool(r.grid_available))
        ren = max(min(r.solar_kw + r.wind_kw, r.demand_kw), 0.0)
        rec.append(dict(cost=cost, grid_kwh=grid*DT, diesel_kwh=dies*DT, ren_kwh=ren*DT,
                        served=r.demand_kw*DT, soc=soc, action=act,
                        co2=(grid*CO2["grid"] + dies*CO2["diesel"]
                             + r.solar_kw*CO2["solar"] + r.wind_kw*CO2["wind"]) * DT))
    return pd.DataFrame(rec)

ctrl_rule = lambda r, soc: rule_decision(r.net_load_kw, soc, r.grid_price,
                                         bool(r.grid_available), r.price_max_next4h)
def ctrl_ml(r, soc):
    row = r[FEATURES].to_frame().T.astype(float)
    row["battery_soc"] = soc                       # the LIVE soc, not the logged one
    return clf.predict(row[FEATURES])[0] if best_name != "XGBoost" else \
           CLASSES[int(clf.predict(row[FEATURES])[0])]

results = {}
for name, ctrl in [("Rule (today)", ctrl_rule), ("ML decision model", ctrl_ml)]:
    per_day = [run_day(data[data.day == d], ctrl) for d in test_days]
    agg = pd.DataFrame([dict(cost=p.cost.sum(), co2=p.co2.sum(), grid=p.grid_kwh.sum(),
                             diesel=p.diesel_kwh.sum(), ren=p.ren_kwh.sum(),
                             served=p.served.sum()) for p in per_day])
    results[name] = agg

opt_agg = []
for d in test_days:
    g = data[data.day == d]
    s = solve_day(g.net_load_kw.values, g.grid_price.values, g.grid_available.values)
    ren = np.maximum(np.minimum(g.solar_kw.values + g.wind_kw.values, g.demand_kw.values), 0)
    opt_agg.append(dict(cost=s.cost.sum(), grid=s.grid_kw.sum()*DT, diesel=s.diesel_kw.sum()*DT,
                        ren=ren.sum()*DT, served=g.demand_kw.sum()*DT,
                        co2=((s.grid_kw*CO2["grid"] + s.diesel_kw*CO2["diesel"]).values
                             + g.solar_kw.values*CO2["solar"] + g.wind_kw.values*CO2["wind"]).sum()*DT))
results["Perfect foresight"] = pd.DataFrame(opt_agg)

base = results["Rule (today)"].cost.sum()
print(f"{'controller':22s} {'Rs/day':>10s} {'vs rule':>10s} {'renewable':>11s} "
      f"{'kg CO2/day':>12s} {'diesel kWh':>11s}")
for name, a in results.items():
    print(f"{name:22s} {a.cost.mean():10,.0f} {100*(a.cost.sum()-base)/base:+9.1f}% "
          f"{100*a.ren.sum()/a.served.sum():10.1f}% {a.co2.mean():12,.0f} {a.diesel.sum():11,.1f}")

ml_save = base - results["ML decision model"].cost.sum()
op_save = base - results["Perfect foresight"].cost.sum()
print(f"\nOver {len(test_days)} test days:")
print(f"  ML saves               Rs {ml_save:,.0f}  ({100*ml_save/base:.1f}%)")
print(f"  Perfect foresight saves Rs {op_save:,.0f}  ({100*op_save/base:.1f}%)")
if op_save > 0:
    print(f"  ML captured {100*ml_save/op_save:.0f}% of the theoretically available saving.")
""")

co(r"""
fig, ax = plt.subplots(1, 3, figsize=(14, 4))
names = list(results.keys())
cols  = [DIESEL_C, BATT, INK]
ax[0].bar(range(3), [results[n].cost.mean() for n in names], color=cols)
ax[0].set_xticks(range(3)); ax[0].set_xticklabels(names, rotation=20, ha="right", fontsize=8)
ax[0].set_ylabel("Rs per day"); ax[0].set_title("operating cost")
ax[1].bar(range(3), [100*results[n].ren.sum()/results[n].served.sum() for n in names], color=cols)
ax[1].set_xticks(range(3)); ax[1].set_xticklabels(names, rotation=20, ha="right", fontsize=8)
ax[1].set_ylabel("% of demand"); ax[1].set_title("renewable share")
ax[2].bar(range(3), [results[n].co2.mean() for n in names], color=cols)
ax[2].set_xticks(range(3)); ax[2].set_xticklabels(names, rotation=20, ha="right", fontsize=8)
ax[2].set_ylabel("kg per day"); ax[2].set_title("CO2 emissions")
plt.tight_layout(); plt.show()

print("Three things worth noticing before quoting any of this:")
print()
print("1. The renewable share barely moves between controllers. It should not — solar and wind")
print("   are taken first by every controller, including the rule. AI does not create sunshine.")
print("   Anyone promising a large renewable-share gain from a dispatch model is selling something.")
print()
print("2. The saving is in WHEN grid energy is bought, not HOW MUCH. Same kilowatt-hours,")
print("   cheaper hours.")
print()
print("3. Perfect foresight is not achievable. It is the ceiling, and the useful question is")
print("   what share of it a real controller captures.")
""")

# ---------------------------------------------------------------- 18. confusion
md(rf"""
## 18 · When it is wrong — the confusion matrix that costs money

**Engineering context.** Where does the model disagree with the optimum, and does it matter?

**The engineering challenge.** From Section 16 we know the confusions are not equal. Now we combine the two:
which mistakes does this model actually make, and are they the cheap ones or the expensive ones?

**The AI connection.** A model that makes many cheap mistakes and no expensive ones is a good controller
even at modest accuracy. That is the pattern to look for.

{link('confusion', 'Which mistakes it makes')}
""")

co(r"""
pred_te = clf.predict(Xte) if best_name != "XGBoost" else \
          pd.Series(clf.predict(Xte)).map({i: c for c, i in codes.items()}).values

fig, ax = plt.subplots(1, 2, figsize=(14, 5))
ConfusionMatrixDisplay.from_predictions(yte, pred_te, labels=CLASSES, xticks_rotation=40,
                                        cmap="Blues", colorbar=False, ax=ax[0], normalize="true")
ax[0].set_title(f"{best_name} vs the optimum (row-normalised)")
ax[0].tick_params(labelsize=7)

cm = confusion_matrix(yte, pred_te, labels=CLASSES)
weighted = cm * reg.values                       # how many, times what each one costs
im = ax[1].imshow(weighted, cmap="Reds")
ax[1].set_xticks(range(5)); ax[1].set_xticklabels(CLASSES, rotation=40, ha="right", fontsize=7)
ax[1].set_yticks(range(5)); ax[1].set_yticklabels(CLASSES, fontsize=7)
ax[1].set_title("the same errors, priced in Rs")
for i in range(5):
    for j in range(5):
        if weighted[i, j] > 0:
            ax[1].text(j, i, f"{weighted[i,j]:.0f}", ha="center", va="center", fontsize=7,
                       color="white" if weighted[i, j] > weighted.max()*0.55 else "black")
plt.colorbar(im, ax=ax[1], shrink=0.8); plt.tight_layout(); plt.show()

print(classification_report(yte, pred_te, labels=CLASSES, zero_division=0))
print("Compare the two panels. The left one shows where the disagreements are; the right one")
print("shows which of them the plant should care about. They are not the same picture, and the")
print("right-hand one is the one to take to a design review.")
""")

# ---------------------------------------------------------------- 19. outage
md(rf"""
## 19 · Grid outage — reliability, and why the diesel stays

**Engineering context.** The grid fails a few times a month. When it does, every economic argument is
suspended and one question remains: **can the campus keep running?**

**The engineering challenge.** During an outage the battery is the only clean option, and it is finite. A
controller that has been merrily discharging all afternoon to shave a few rupees off the tariff arrives at
the outage with nothing left.

**The AI connection.** This is where a decision support system earns or loses its licence. The value of lost
load in this notebook is ₹500/kWh — more than twenty times diesel — so the optimiser will always start the
generator rather than drop the campus. **That is not the model being clever. It is us having priced
reliability correctly in the objective.** Get that number wrong and the model will confidently make a
catastrophic recommendation.

{link('outage', 'When the grid goes')}
""")

co(r"""
out_days = [d for d in test_days if data[(data.day == d) & (data.grid_available == 0)].shape[0] > 0]
print(f"Test days containing a grid outage: {len(out_days)} of {len(test_days)}")

if out_days:
    d_o = out_days[0]
    g   = data[data.day == d_o].reset_index(drop=True)
    rec_ml = run_day(g, ctrl_ml); rec_ru = run_day(g, ctrl_rule)
    ok = g.grid_available.values.astype(bool)

    fig, ax = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    ax[0].plot(g.hour, g.demand_kw, color=INK, lw=2, label="demand")
    ax[0].fill_between(g.hour, 0, g.solar_kw + g.wind_kw, color=SOLAR, alpha=0.5, label="renewables")
    ax[0].axvspan(g.hour[~ok].min(), g.hour[~ok].max(), color=DIESEL_C, alpha=0.20, label="GRID DOWN")
    ax[0].set_ylabel("kW"); ax[0].legend(fontsize=8); ax[0].set_title(f"test day {d_o} — the grid fails")
    ax[1].plot(g.hour, rec_ml.soc, color=BATT, lw=2, label="battery SoC — ML controller")
    ax[1].plot(g.hour, rec_ru.soc, color=GRID, lw=2, ls="--", label="battery SoC — rule")
    ax[1].axhline(SOC_MIN, color=DIESEL_C, ls=":", label=f"floor ({SOC_MIN:.0f}%)")
    ax[1].axvspan(g.hour[~ok].min(), g.hour[~ok].max(), color=DIESEL_C, alpha=0.20)
    ax[1].set_ylabel("SoC (%)"); ax[1].set_xlabel("hour"); ax[1].legend(fontsize=8)
    plt.tight_layout(); plt.show()

    print(f"{'controller':22s} {'diesel kWh':>11s} {'unserved kWh':>13s} {'Rs on the day':>14s}")
    for nm, rc in [("Rule (today)", rec_ru), ("ML decision model", rec_ml)]:
        uns = float((rc.served - rc.ren_kwh - rc.grid_kwh - rc.diesel_kwh).clip(lower=0).sum())
        print(f"{nm:22s} {rc.diesel_kwh.sum():11,.1f} {uns:13,.1f} {rc.cost.sum():14,.0f}")
    print()
    print("The diesel is not a failure of the design. It is the design. A 500 kWh battery cannot")
    print("carry a 350 kW campus through a three-hour outage, and no amount of AI changes that")
    print("arithmetic. What the controller can do is arrive at the outage with charge in hand.")
else:
    print("No outage fell in the test window this run — re-seed make_history() to see one.")
""")

# ---------------------------------------------------------------- 20. decision engine
md(rf"""
## 20 · The decision engine — one recommendation, with its reasons

**Engineering context.** Everything so far becomes one panel on a control-room screen.

**The engineering challenge.** The engineer has fifteen minutes and a plant to run. The panel has to say
what to do, how sure it is, what it will cost, and why — in one glance.

**The AI connection.** Fusion of everything built so far: the model's class, its confidence, the executor's
setpoints, and a reason string assembled from the conditions.

{link('engine', 'The decision engine')}
""")

co(r"""
def decision_engine(r, soc, model=None):
    "The full recommendation for one interval: what, how sure, what it costs, and why."
    model = model or rf
    row = r[FEATURES].to_frame().T.astype(float); row["battery_soc"] = soc
    act  = model.predict(row[FEATURES])[0]
    conf = float(np.max(model.predict_proba(row[FEATURES])))
    cost, new_soc, grid, dies, b = dispatch_cost(act, r.net_load_kw, soc, r.grid_price,
                                                 bool(r.grid_available))
    ren  = max(min(r.solar_kw + r.wind_kw, r.demand_kw), 0.0)
    co2  = (grid*CO2["grid"] + dies*CO2["diesel"] + r.solar_kw*CO2["solar"]
            + r.wind_kw*CO2["wind"]) * DT
    all_grid_co2 = r.demand_kw * CO2["grid"] * DT
    return dict(hour=f"{int(r.hour):02d}:{int(r.hour%1*60):02d}",
                action=act, confidence=f"{conf:.0%}",
                rs_per_kwh=round(cost / max(r.demand_kw*DT, 1e-6), 2),
                renewable_pct=round(100*ren/max(r.demand_kw, 1e-6)),
                co2_cut_pct=round(100*(1 - co2/max(all_grid_co2, 1e-6))),
                battery_kw=round(b), grid_kw=round(grid), soc_after=round(new_soc))

d_show = data[data.day == test_days[0]].reset_index(drop=True)
soc, panel = 55.0, []
for k in range(0, STEPS, 8):                          # every two hours
    row = decision_engine(d_show.iloc[k], soc)
    panel.append(row); soc = row["soc_after"]
pd.DataFrame(panel).set_index("hour")
""")

md(r"""
Read one row and it is a complete engineering statement: the strategy, how sure the model is, the resulting
cost per unit, the renewable share achieved, the carbon avoided against buying everything from the grid, and
the setpoints that follow.

Two things the panel is careful **not** to do:

- It never issues a command. Every row is a recommendation an engineer accepts or overrides.
- It never hides its confidence. A 54% recommendation and a 99% recommendation look different on the screen,
  because they should be treated differently.

**Key takeaway:** a recommendation with its reasoning attached gets followed; a number on its own gets
switched off.
""")

# ---------------------------------------------------------------- 21. dashboard
md(rf"""
## 21 · The energy management dashboard — the business case

**Engineering context.** A plant manager does not buy a model. They approve a spend against a saving.

**The engineering challenge.** Microgrid AI savings are easy to overstate. Three deductions most business
cases quietly skip:

- The baseline is **not** "no controller". It is the rule that is already running, and it is decent.
- Extra battery cycling has a cost, and it is already in every rupee above — but it is worth showing
  separately, because it is the deduction people forget.
- A recommendation nobody follows saves nothing. Engineer acceptance is an input, not an assumption.

**The AI connection.** Convert the closed-loop result into annual terms, with every assumption visible.

{link('dashboard', 'The energy management dashboard')}
""")

co(r"""
def business_case(acceptance=0.80, days_per_year=330, capex=850_000.0,
                  integration=250_000.0, annual_licence=120_000.0):
    "Arithmetic on the closed-loop result. Change any argument and the case changes."
    n = len(test_days)
    daily_saving = (results["Rule (today)"].cost.sum()
                    - results["ML decision model"].cost.sum()) / n
    realised = daily_saving * acceptance * days_per_year
    co2_cut  = (results["Rule (today)"].co2.mean()
                - results["ML decision model"].co2.mean()) * acceptance * days_per_year
    payback  = (capex + integration) / realised if realised > 0 else float("inf")
    return dict(daily_saving_rs=daily_saving, realised_annual_rs=realised,
                annual_cost_rs=annual_licence, net_annual_rs=realised - annual_licence,
                co2_saved_kg_year=co2_cut, payback_years=payback)

case = business_case()
for k, v in case.items():
    print(f"{k:22s} {v:14,.1f}")

fig, ax = plt.subplots(1, 2, figsize=(13, 4))
ax[0].bar(["gross\nsaving", "licence\ncost", "net"],
          [case["realised_annual_rs"], -case["annual_cost_rs"], case["net_annual_rs"]],
          color=[BATT, DIESEL_C, INK])
ax[0].axhline(0, color="k", lw=1); ax[0].set_ylabel("Rs per year")
ax[0].set_title("the case, with the deduction shown")
acc = np.linspace(0.1, 1.0, 40)
ax[1].plot(acc, [business_case(acceptance=a)["net_annual_rs"] for a in acc], color=GRID, lw=2)
ax[1].axhline(0, color="k", lw=1)
ax[1].set_xlabel("share of recommendations the engineer accepts")
ax[1].set_ylabel("net Rs per year"); ax[1].set_title("the assumption the case rests on")
plt.tight_layout(); plt.show()

print()
print("Look at the right-hand chart before quoting the left-hand one. Below a certain acceptance")
print("rate the system costs more than it saves — and acceptance is won by the explanations in")
print("Sections 14 and 20, not by the accuracy in Section 12. That is the whole reason this")
print("notebook spends two sections on explainability.")
""")

# ---------------------------------------------------------------- 22. summary
md(rf"""
## 22 · Summary — the whole system

```
   SMART METERS / INVERTERS / BMS / TARIFF / FORECAST
                        │
                        ▼
              clean ──► encode (circular time, forecasts) ──► split BY DAY
                        │
                        ▼
      ┌── labels from a PERFECT-FORESIGHT OPTIMISER (dynamic programming)
      │                 │
      ▼                 ▼
   RULE (baseline)   DECISION MODEL (tree / forest / boosting)
      │                 │
      └────────► CLOSED-LOOP SIMULATION ◄── perfect foresight (the ceiling)
                        │
                        ▼
              DECISION ENGINE ──► action, confidence, cost, reasons
                        │
                        ▼
                  THE ENGINEER DECIDES
```

**What was built**

| Stage | Method | Output |
|---|---|---|
| Work out what the decision is | Engineering analysis | five strategies, not five sources |
| Repair the record | Time interpolation within each day | a usable time series |
| Encode the conditions | Circular time, forward-looking tariff and forecast | features a model can use |
| Split honestly | By whole day | a score that is not fiction |
| Establish the baseline | Rule-based controller | what the plant already achieves |
| Create the labels | Dynamic programming | the exact cheapest dispatch |
| Learn the policy | Decision Tree / Random Forest / Boosting | a recommendation from observable data |
| Explain it | Tree path, feature importance | reasoning an engineer can audit |
| Score it properly | Cost regret, closed-loop simulation | rupees, CO₂, reliability |
| Present it | Decision engine | action, confidence, cost, reasons |

**The four things worth remembering**

1. **Find the real decision first.** Renewables are never turned down, so "solar vs grid" was never the
   question. The question was what covers the residual, and it has five answers.
2. **Labels decide the ceiling.** Train on your own rule and you can only reproduce your own rule. The
   optimiser gave a target worth aiming at — and an honest measure of how much room there was.
3. **Score in the units of the plant.** Accuracy weights a two-rupee mistake the same as starting a diesel
   engine. Cost regret and closed-loop simulation do not.
4. **Power System Engineer + AI.** The system evaluates ninety-six intervals a day against conditions no
   person can track continuously, and hands over a recommendation with its reasoning. A person still
   decides, still signs off, and still owns the supply.

**And one that is specific to this problem:** the saving did not come from using more renewable energy —
every controller already takes all of it. It came from **buying the same grid energy at better hours.**
Time, not technology, was the resource being managed.

{link('start', 'The whole project map')}
""")

nb = new_notebook(cells=cells, metadata={
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"},
    "colab": {"provenance": []},
})
nbf.validate(nb)
with open("Power_Source_Selection_AI.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"wrote Power_Source_Selection_AI.ipynb  ({len(cells)} cells, "
      f"{sum(1 for c in cells if c.cell_type=='code')} code)")
