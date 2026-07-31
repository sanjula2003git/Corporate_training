"""
Builds Sustainable_Manufacturing_DL.ipynb from nbformat cells.
Run:  py -3.13 build_nb.py

The notebook is standalone (Colab): it does not import app.py / story.py /
bridge.py. It re-defines the plant energy model and the synthetic thermal frames
inline so the notebook and the app always agree.

APP is the one place to change after the Streamlit app is deployed — every
"open this stage in the app" link is built from it.
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

APP = "https://sustainable-manufacturing.streamlit.app"   # <- update after deployment

cells = []
def md(t):  cells.append(new_markdown_cell(t.strip("\n")))
def co(t):  cells.append(new_code_cell(t.strip("\n")))
def link(stage, label):
    """A deep link into the illustration app for this stage."""
    return f"🎬 **See it illustrated:** [{label}]({APP}/?stage={stage})"


# ---------------------------------------------------------------- title
md(rf"""
# AI for Sustainable Manufacturing
### Teaching AI through the energy and carbon performance of a production plant

This notebook is the runnable companion to the Sustainable Manufacturing course. You are not learning AI
for its own sake — you are building a **sustainability monitor** for a factory, and each AI method appears
because it solves a real plant problem one engineer cannot cover by hand.

**The framing throughout:** the engineer stays in charge and stays accountable. A model that sees only
numbers cannot hear a bearing, judge whether a hot pipe is a design feature, or authorise a shutdown. The
monitor only eases the part one person cannot carry alone — watching every machine, every hour, across
three shifts, against a bill that arrives once a month. The monitor *reports and recommends*; the engineer
*decides*.

**The one idea this notebook proves:**

> **Machine Learning predicts sustainability metrics from sensor measurements.
> Deep Learning discovers hidden patterns in images that feature engineering cannot easily capture.**

Do not take that on trust. Every section below builds towards it, and Section 18 measures it.

**What we build, in the order a real project runs it:**

1. The plant in production — the problem
2. One production hour → data collection
3. Load the energy log
4. Data inspection (dropouts, stuck meters)
5. Data cleaning (median fill)
6. Normalization (one common scale)
7. Train / validation / test split
8. ML baseline — Random Forest for kWh, CO₂ and the waste flag
9. Why ML cannot grade a raw thermal frame
10. Deep learning — the neuron
11. Activation functions
12. Loss and gradient descent
13. The network, and training it
14. CNN on the thermal frame
15. Locating the loss — Grad-CAM
16. Evaluation — the confusion matrix and the costly miss
17. The verdict — ML vs DL, measured
18. Anomaly detection — normal for the conditions
19. Optimisation — the efficient operating point
20. Fusion — one prioritised action
21. The sustainability dashboard — the business case
22. Summary — the whole system

{link('start', 'The project overview')}
""")

md(r"""
## Setup

In Colab the libraries below are already installed. If you run this elsewhere, uncomment the install line.
We use `matplotlib` for plots to keep the notebook simple and portable. TensorFlow/Keras is used for the
CNN — the notebook detects whether it is present and skips the CNN training gracefully if not, so every
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

# The course palette (the same hex the app uses)
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

# ---------------------------------------------------------------- 1. the plant
md(rf"""
## 1 · The plant in production — the problem

**Manufacturing activity.** A production plant runs three shifts. Compressors, motors, ovens, pumps and
ventilation draw power around the clock. Electricity is one of the largest controllable costs on the site,
and every kilowatt-hour carries a carbon figure the company has to report.

**The challenge.** Consumption is continuous; review is not. The energy bill arrives monthly, long after
the waste happened. A leaking air line, a badly scheduled oven or an idling line can burn power for weeks
before anyone reads about it in a report.

**The AI connection.** The plant does not need its engineers replaced. It needs the *gap between the meter
and the report* closed — consumption watched continuously and waste identified while it is still
happening. That continuous watch is the only reason AI belongs on the shop floor.

{link('in-production', 'A plant under load')} · {link('enter-ai', 'The sustainability monitor')}
""")

co(r"""
# The plant energy model. Three parts, and the third is what makes Section 19 interesting:
#   BASELOAD          - lighting, ventilation, standby air. Paid whatever you make.
#   LOAD_LIN * load   - the useful work, proportional to output.
#   LOAD_SQ  * load^2 - losses that grow FASTER than output: drives pushed past their
#                       best-efficiency point, extra cooling, more scrap.
BASELOAD   = 36.0      # kW drawn before any machine is loaded
LOAD_LIN   = 0.30      # kW per % load
LOAD_SQ    = 0.0135    # kW per (% load)^2
GRID_KG    = 0.72      # kg CO2 per kWh from the grid
SPEC_LIMIT = 2.00      # kWh per unit above which an hour counts as WASTEFUL

def units_for(load, idle):
    "Units produced in the hour, from machine load (%) and idle share (%)."
    return 1.35 * np.asarray(load, float) * (1.0 - np.asarray(idle, float) / 100.0)

def energy_for(waste, load, idle, ambient):
    "Electricity drawn in the hour, kWh."
    load = np.asarray(load, float)
    return (BASELOAD + LOAD_LIN * load + LOAD_SQ * load**2
            + 42.0 * np.asarray(waste, float)
            + 0.22 * np.asarray(idle, float)
            + 0.55 * np.clip(np.asarray(ambient, float) - 24.0, 0, None))

# A compressed-air leak opens up part-way through the month and grows.
hours = 720
t     = np.arange(hours)
leak  = np.clip((t - 180) * 0.0016, 0, 0.9)
kwh   = energy_for(leak, 70.0, 8.0, 24.0)
base  = float(energy_for(0.0, 70.0, 8.0, 24.0))

onset    = int(np.argmax(leak > 0.05))
reviews  = np.arange(0, hours, 720)          # reviewed once, with the monthly bill
detected = int(reviews[reviews >= onset][0]) if (reviews >= onset).any() else hours
unseen   = float(np.sum(kwh[onset:detected] - base))

plt.figure(figsize=(9, 4))
plt.plot(t, kwh, color=CYAN, lw=2, label="metered kWh")
plt.axhline(base, color=GREEN, ls="--", label="what the hour should cost")
plt.axvspan(onset, detected, color=RED, alpha=0.12)
plt.xlabel("hour of the month"); plt.ylabel("kWh per hour")
plt.title("consumption is continuous; the review is monthly")
plt.legend(); plt.tight_layout(); plt.show()

print(f"Leak opens at hour {onset}; nobody reads about it until hour {detected}.")
print(f"Energy burned unseen: {unseen:,.0f} kWh  ->  {unseen*GRID_KG/1000:,.1f} t CO2")
""")

# ---------------------------------------------------------------- 2. one hour
md(rf"""
## 2 · One production hour → data collection

**Manufacturing activity.** At the end of every production hour the plant records what it did: machine
load, motor temperature, compressed-air pressure and flow, idle share, units produced, material consumed
and the ambient temperature in the hall.

**The challenge.** On their own these are eight scattered readings on eight screens. No single number tells
you whether the hour was efficient.

**The AI connection.** Put them in one row and the hour becomes a record: eight inputs, and the energy and
CO₂ that resulted. Thousands of those rows are a dataset.

The eight channels, and what each one tells you:

| Channel | Source | Unit | What it tells you |
|---|---|---|---|
| Machine load | Drive / PLC tag | % | How hard the line is working — the biggest driver of draw |
| Motor temperature | Thermocouple | °C | Rises with load, and with a compressor fighting a leak |
| Air pressure | Line pressure sensor | bar | Falls when compressed air escapes |
| Air flow | Flow meter | m³/h | Rises at constant load when there is a leak |
| Idle share | Machine runtime log | % | Power drawn while producing nothing |
| Units produced | Production counter | units/h | The output the energy is supposed to buy |
| Material used | Weighing / MES | kg | Input mass — scrap shows up here |
| Ambient temperature | Hall sensor | °C | Drives ventilation load — must be separated from waste |

{link('reading', 'One production hour')} · {link('two-records', 'Reading vs thermal frame')}
""")

co(r"""
FEATURES = ["load_pct", "motor_temp_c", "air_pressure_bar", "air_flow_m3h",
            "idle_pct", "units_per_hr", "material_kg", "ambient_temp_c"]
NICE = ["Load (%)", "Motor temp (C)", "Air pressure (bar)", "Air flow (m3/h)",
        "Idle (%)", "Units/hour", "Material (kg)", "Ambient (C)"]

def signals_for(waste, load, idle, ambient):
    '''The eight metered channels, noise-free. Column order == FEATURES.

    A hidden 'waste' level (air leaks, failed lagging, poor scheduling) shows up
    on several channels at once: the compressor works harder (motor temperature),
    line pressure sags, air flow rises, and scrap grows.
    '''
    waste, load = np.asarray(waste, float), np.asarray(load, float)
    idle, ambient = np.asarray(idle, float), np.asarray(ambient, float)
    motor = ambient + 14.0 + 0.30 * load + 22.0 * waste
    press = 6.8 - 1.6 * waste
    flow  = 28.0 + 70.0 * waste + 0.35 * load
    units = units_for(load, idle)
    mat   = 0.90 * units * (1.0 + 0.35 * waste)
    return np.stack([load, motor, press, flow, idle, units, mat, ambient], axis=-1)

def co2_for(energy_kwh, material_kg):
    "kg CO2: grid electricity plus the embodied carbon of the material consumed."
    return GRID_KG * np.asarray(energy_kwh, float) + 0.05 * np.asarray(material_kg, float)

# One hour, as the model will see it
one = signals_for(0.35, 70, 8, 26)
print(pd.DataFrame([one], columns=NICE).round(1).to_string(index=False))
""")

md(r"""
### The plant's historian export

A real project starts by downloading a month of logged hours. Here we generate that export so the notebook
is self-contained and reproducible — same relationships, same faults you would meet on site.
""")

co(r"""
def make_export(n=1500, seed=42):
    "One month of production hours, as the plant historian would export them."
    rng = np.random.default_rng(seed)
    waste   = rng.uniform(0.0, 0.9, n)     # hidden inefficiency — never measured directly
    load    = rng.uniform(30.0, 100.0, n)
    idle    = rng.uniform(0.0, 35.0, n)
    ambient = rng.uniform(12.0, 38.0, n)

    b = signals_for(waste, load, idle, ambient)
    df = pd.DataFrame({
        "hour_id":          np.arange(1, n + 1),
        "load_pct":         np.clip(b[:, 0] + rng.normal(0, 1.2, n), 0, None).round(1),
        "motor_temp_c":     (b[:, 1] + rng.normal(0, 1.5, n)).round(1),
        "air_pressure_bar": (b[:, 2] + rng.normal(0, 0.08, n)).round(2),
        "air_flow_m3h":     np.abs(b[:, 3] + rng.normal(0, 3.0, n)).round(1),
        "idle_pct":         np.clip(b[:, 4] + rng.normal(0, 1.0, n), 0, None).round(1),
        "units_per_hr":     np.abs(b[:, 5] + rng.normal(0, 2.0, n)).round(0),
        "material_kg":      np.abs(b[:, 6] + rng.normal(0, 2.5, n)).round(1),
        "ambient_temp_c":   ambient.round(1),
    })
    energy = energy_for(waste, load, idle, ambient) + rng.normal(0, 1.5, n)
    df["energy_kwh"]   = energy.round(1)
    df["co2_kg"]       = co2_for(energy, df.material_kg.values).round(1)
    df["kwh_per_unit"] = (energy / np.clip(df.units_per_hr.values, 1e-6, None)).round(3)
    df["wasteful"]     = (df.kwh_per_unit > SPEC_LIMIT).astype(int)

    # the faults every real export carries
    for c in FEATURES:
        df.loc[rng.choice(n, int(0.06 * n), replace=False), c] = np.nan
    df.loc[rng.choice(n, 13, replace=False), "air_flow_m3h"]     = 0.0     # dead flow meter
    df.loc[rng.choice(n, 10, replace=False), "motor_temp_c"]     = 999.0   # thermocouple fault
    df.loc[rng.choice(n, 12, replace=False), "air_pressure_bar"] = 0.0     # frozen channel
    df.loc[rng.choice(n, 11, replace=False), "load_pct"]         = 9999.0  # saturated drive tag
    return pd.concat([df, df.sample(20, random_state=4)], ignore_index=True)  # resync duplicates

raw = make_export()
raw.to_csv("plant_energy_log.csv", index=False)
print("wrote plant_energy_log.csv")
""")

# ---------------------------------------------------------------- 3. load
md(rf"""
## 3 · Load the energy log

**Manufacturing activity.** The historian export arrives as a CSV: one row per hour.

**The challenge.** An export is not a dataset. Channels drop out when a gateway restarts, a saturated meter
writes a fixed maximum, and the same hour can appear twice after a resync.

**The AI connection.** Loading the file into a DataFrame is the first AI step — shape, column types and a
first look.

{link('load', 'The energy log arrives')}
""")

co(r"""
df = pd.read_csv("plant_energy_log.csv")
print("shape:", df.shape)
print("wasteful hours:", f"{df.wasteful.mean():.1%}")
df.head()
""")

# ---------------------------------------------------------------- 4. inspect
md(rf"""
## 4 · Data inspection — the meter health check

**Manufacturing activity.** Before trusting a month of readings, an engineer checks the instruments. Did
the flow meter report all month? Is the pressure channel stuck? Is anything physically impossible?

**The challenge.** Faults hide in plain sight. A dead flow meter reads `0.0 m³/h` — a perfectly valid
number that happens to be a lie.

**The AI connection.** Data inspection is that instrument check, done in code.

{link('inspect', 'Meter health check')}
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
Read the `min` / `max` table above like an engineer, not a statistician:

- `load_pct` maxing at **9999** is a saturated drive tag, not a machine running 100× too hard.
- `motor_temp_c` at **999 °C** is a faulted thermocouple.
- `air_flow_m3h` at **0.0** is a dead meter — a running plant always uses some air.
- `air_pressure_bar` at **0.0** is a frozen channel.

Every one of those is a *valid number* and a *fault* at the same time. That is exactly what inspection is
for.
""")

# ---------------------------------------------------------------- 5. clean
md(rf"""
## 5 · Data cleaning

**Manufacturing activity.** A faulty channel is repaired or discounted before its readings reach a report.
Nobody averages a stuck gauge into a monthly figure.

**The challenge.** Deleting every affected row throws away good readings from the other seven channels.
Keeping them poisons the average.

**The AI connection.** Cleaning does both: drop duplicates, mark impossible values as *missing* rather than
deleting the row, then fill the gaps with the channel's **median** — a value the outliers cannot drag.

{link('clean', 'Dropouts and stuck meters')}
""")

co(r"""
clean = df.drop_duplicates().copy()

# mark the physically impossible as missing, rather than deleting the whole hour
clean.loc[clean.load_pct > 150,          "load_pct"]         = np.nan
clean.loc[clean.motor_temp_c > 200,      "motor_temp_c"]     = np.nan
clean.loc[clean.air_flow_m3h <= 0,       "air_flow_m3h"]     = np.nan
clean.loc[clean.air_pressure_bar <= 0.5, "air_pressure_bar"] = np.nan

for c in FEATURES:
    clean[c] = clean[c].fillna(clean[c].median())

print(f"rows: {len(df)} -> {len(clean)}   missing left: {int(clean[FEATURES].isna().sum().sum())}")

fig, ax = plt.subplots(1, 2, figsize=(9, 3.5))
ax[0].boxplot(df.motor_temp_c.dropna());    ax[0].set_title("motor temp — dirty")
ax[1].boxplot(clean.motor_temp_c);          ax[1].set_title("motor temp — clean")
plt.tight_layout(); plt.show()

print("Why the median, not the mean?")
print(f"  mean of the dirty channel   : {df.motor_temp_c.mean():.1f} C   <- dragged by the 999s")
print(f"  median of the dirty channel : {df.motor_temp_c.median():.1f} C   <- barely notices them")
""")

# ---------------------------------------------------------------- 6. normalize
md(rf"""
## 6 · Normalization

**Manufacturing activity.** The channels do not share a scale. Air flow runs to 100 m³/h, line pressure
sits near 6 bar, idle share is a percentage.

**The challenge.** A model that adds weighted inputs lets the largest-numbered channel dominate the sum —
not because it matters most, but because its unit is bigger.

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

**Manufacturing activity.** A commissioning test is not run on the load case used to tune the plant.

**The challenge.** A model checked on the hours it learned from will look excellent and mean nothing.

**The AI connection.** 70% to train, 15% to tune with, 15% sealed until the audit.

{link('split', 'Known vs sealed')}
""")

co(r"""
X    = norm[FEATURES].values
y    = norm["wasteful"].values          # classification target
yen  = norm["energy_kwh"].values        # regression target 1 — kWh
yco2 = norm["co2_kg"].values            # regression target 2 — CO2

idx = np.arange(len(X))
itr, itmp = train_test_split(idx,  test_size=0.30, random_state=42, stratify=y)
iva, ite  = train_test_split(itmp, test_size=0.50, random_state=42, stratify=y[itmp])

Xtr, Xva, Xte = X[itr], X[iva], X[ite]
ytr, yva, yte = y[itr], y[iva], y[ite]

print(f"train {len(itr)}   validation {len(iva)}   test (sealed) {len(ite)}")
print(f"wasteful rate — train {ytr.mean():.1%}, val {yva.mean():.1%}, test {yte.mean():.1%}")
""")

# ---------------------------------------------------------------- 8. ML baseline
md(rf"""
## 8 · Machine Learning baseline — Random Forest

**Manufacturing activity.** Given this hour's readings, how much energy and CO₂ should it have produced,
and was the hour wasteful?

**The challenge.** A nameplate spreadsheet formula gets the order of magnitude right and the details wrong.
Load, idle share, leaks and ambient heat all interact.

**The AI connection.** A Random Forest asks a sequence of threshold questions on the *named* channels and
averages many trees. This is the **first half of the course promise: ML predicts sustainability metrics
from sensor measurements.**

{link('ml-baseline', 'Energy from the readings')} · {link('drivers', 'What drives the bill')}
""")

co(r"""
# --- regression: how many kWh and kg CO2 did this hour cost? ---------------
en_model  = RandomForestRegressor(n_estimators=200, random_state=42).fit(Xtr, yen[itr])
co2_model = RandomForestRegressor(n_estimators=200, random_state=42).fit(Xtr, yco2[itr])

r2_en  = r2_score(yen[ite],  en_model.predict(Xte))
r2_co2 = r2_score(yco2[ite], co2_model.predict(Xte))
print(f"Energy R2 on sealed hours : {r2_en:.3f}")
print(f"CO2    R2 on sealed hours : {r2_co2:.3f}")

plt.figure(figsize=(5, 5))
plt.scatter(yen[ite], en_model.predict(Xte), s=12, color=CYAN, alpha=0.6)
lims = [yen[ite].min(), yen[ite].max()]
plt.plot(lims, lims, "--", color=MUTED)
plt.xlabel("metered kWh"); plt.ylabel("predicted kWh")
plt.title("predicted vs metered, on hours never seen")
plt.tight_layout(); plt.show()
""")

co(r"""
# --- classification: was this hour wasteful? -------------------------------
rf  = RandomForestClassifier(n_estimators=200, random_state=42).fit(Xtr, ytr)
print(f"Random Forest accuracy on sealed hours: {accuracy_score(yte, rf.predict(Xte)):.1%}")

# --- feature importance: which lever should the plant pull? ---------------
fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
for a, (m, title) in zip(ax, [(en_model, "drivers of energy (kWh)"),
                              (rf,       "drivers of a WASTEFUL hour")]):
    imp = m.feature_importances_
    o = np.argsort(imp)[::-1]
    a.bar([NICE[i] for i in o], imp[o], color=CYAN)
    a.set_title(title); a.tick_params(axis="x", rotation=40)
    for lab in a.get_xticklabels():
        lab.set_ha("right")
plt.tight_layout(); plt.show()
""")

md(r"""
Read the two rankings side by side — the difference is the point.

- **Machine load dominates total kWh**, and load is *not waste*. The plant is supposed to be producing.
- The **wasteful-hour** model ranks the channels completely differently: idle share, output, line pressure
  and air flow. Those are the levers worth pulling.
- Air flow **rises** with a leak and pressure **falls** — two views of one fault, not two faults.

Importance says how much a prediction *moves*, not what *causes* what. Use it to decide what to
investigate, then confirm on the floor. The model never authorises a spend on its own.
""")

# ---------------------------------------------------------------- 9. the wall
md(rf"""
## 9 · The wall — why ML cannot grade a thermal frame

**Manufacturing activity.** The thermal camera looks at the compressor room. Bright is hot, dark is cold.
A leaking air joint shows as a **cold plume**; a failing bearing as a small **bright disc**; failed lagging
as a **broad warm patch**.

**The challenge.** The camera does not output "leak". It outputs 4,096 numbers with no names.

**The AI connection.** Before reaching for a new method, try building the feature by hand — reduce the
frame to its mean temperature and set an alarm limit. Watch it fail.

{link('thermal-problem', 'The raw thermal frame')} · {link('handmade', 'Mean temperature by hand')} · {link('why-dl', 'Therefore deep learning')}
""")

co(r"""
def make_thermal(kind="normal", size=64, seed=0):
    '''An equipment surface as a normalised temperature grid (0 = cold, 1 = hot).

    normal     - even warm surface            (sound)
    sunlit     - broad warm patch from the sun(sound)   <- the decoy
    leak       - COLD jet cone from a fitting (defect)
    hotspot    - small BRIGHT disc, a bearing (defect)
    insulation - broad warm patch, failed lagging (defect)
    '''
    # NOTE: Python hashes strings with a per-process random seed, so seeding from
    # hash(kind) would give different frames on every run. Use an explicit table.
    _KS = {"normal": 0, "leak": 1, "hotspot": 2, "insulation": 3, "sunlit": 4}
    rng = np.random.default_rng(seed*7 + _KS.get(kind, 5))
    Y, X = np.mgrid[0:size, 0:size]
    img = 0.50 + rng.normal(0, 0.035, (size, size))
    img += 0.03 * np.sin(2 * np.pi * Y / 40.0)

    if kind == "leak":
        cy, cx = 30.0, 14.0
        dx = np.clip(X - cx, 0, None)
        halfw = 0.9 + 0.30 * dx
        cone = np.exp(-((Y - cy) ** 2) / (2 * halfw ** 2)) * np.exp(-dx / 34.0)
        cone[X < cx] = 0.0
        img = img - 0.50 * cone
    elif kind == "hotspot":
        img = img + 0.46 * np.exp(-(((Y - 26.) ** 2 + (X - 40.) ** 2) / (2 * 5.0 ** 2)))
    elif kind == "insulation":
        img = img + 0.13 * np.exp(-(((Y - 40.) ** 2 + (X - 44.) ** 2) / (2 * 19.0 ** 2)))
    elif kind == "sunlit":
        img = img + 0.14 * np.exp(-(((Y - 20.) ** 2 + (X - 22.) ** 2) / (2 * 20.0 ** 2)))
    return np.clip(img, 0, 1)

kinds = ["normal", "sunlit", "leak", "hotspot", "insulation"]
fig, ax = plt.subplots(1, 5, figsize=(14, 3))
for a, k in zip(ax, kinds):
    im = make_thermal(k)
    a.imshow(im, cmap="inferno", vmin=0, vmax=1)
    a.set_title(f"{k}\nmean {im.mean():.3f}", fontsize=10)
    a.axis("off")
plt.tight_layout(); plt.show()

print("A frame is just", make_thermal('leak').size, "numbers. None of them is called 'leak'.")
""")

co(r"""
# The hand-made feature: one number per frame. Then a threshold, like any alarm limit.
labels = {"normal": "sound", "sunlit": "sound",
          "leak": "DEFECT", "hotspot": "DEFECT", "insulation": "DEFECT"}
means = {k: float(make_thermal(k).mean()) for k in kinds}

for thr in (0.48, 0.51, 0.53, 0.56, 0.58):
    missed = [k for k in kinds if labels[k] == "DEFECT" and means[k] <= thr]
    false_ = [k for k in kinds if labels[k] == "sound"  and means[k] >  thr]
    print(f"alarm above {thr:.2f} -> missed {missed or ['none']}, false alarms {false_ or ['none']}")
""")

md(r"""
**No threshold works, and it is worth being precise about why.**

- The air leak is *colder* than sound equipment (mean 0.454 vs 0.506). An "alarm above X" rule can never
  catch it, whatever X is.
- Failed lagging (0.559) and sunlight (0.566) sit almost on top of each other. Any limit that catches the
  defect also alarms on the sunshine.

Averaging threw away the only thing that separated them: **the shape and position of the pattern**. You
could add ten more hand-made features — variance, maximum, edge count — and still be guessing.

> **Machine Learning weights the features you name. Deep Learning finds the features you cannot name.**

That is the second half of the course promise, and the reason everything from here on is a network.
""")

# ---------------------------------------------------------------- 10. neuron
md(rf"""
## 10 · Deep learning starts with one neuron

**Manufacturing activity.** An energy auditor weighs several signals at once — the hiss at a fitting, the
pressure drop, the compressor duty cycle — and calls it a leak or not.

**The challenge.** That judgement lives in one head and cannot be applied to eight hundred logged hours
overnight.

**The AI connection.** Write it down and it is arithmetic: `z = w·x + b`. The weights are not chosen by
anyone — they are learned.

{link('engineer-brain', "The auditor's judgement")} · {link('neuron', 'The neuron')}
""")

co(r"""
x = Xtr[0]                                   # one scaled hour
w = np.array([0.2, 0.5, -0.9, 1.0, 0.8, -0.7, 0.2, 0.3])   # flow/idle push up, pressure/units push down
b = -0.3

z = float(np.dot(w, x) + b)
def sigmoid(v): return 1 / (1 + np.exp(-np.clip(v, -50, 50)))
print(f"z = w.x + b = {z:+.3f}   ->   p(wasteful) = {sigmoid(z):.3f}")

plt.figure(figsize=(8, 3))
c = [CYAN if v >= 0 else RED for v in w * x]
plt.bar(NICE, w * x, color=c)
plt.axhline(0, color=MUTED, lw=1)
plt.ylabel("w x x"); plt.title(f"each channel's contribution  (z = {z:+.2f})")
plt.xticks(rotation=40, ha="right"); plt.tight_layout(); plt.show()
""")

# ---------------------------------------------------------------- 11. activation
md(rf"""
## 11 · Activation — turning a sum into a decision

**Manufacturing activity.** An alarm does not report a weighted sum. It reports a state: acceptable, or
investigate.

**The challenge.** A hard on/off limit treats "just under" and "just over" as opposites — and gives
training no slope to follow.

**The AI connection.** Sigmoid gives a graded probability; ReLU passes positive evidence. Smoothness is
what makes gradient descent possible at all.

{link('activation', 'Activation')}
""")

co(r"""
zs = np.linspace(-6, 6, 300)
fig, ax = plt.subplots(1, 3, figsize=(12, 3.2))
ax[0].plot(zs, sigmoid(zs), color=CYAN, lw=2);        ax[0].set_title("sigmoid — a probability")
ax[1].plot(zs, np.maximum(0, zs), color="#ba68c8", lw=2); ax[1].set_title("ReLU — passes positives")
ax[2].step(zs, (zs > 0).astype(float), color=RED, lw=2, where="mid")
ax[2].plot(zs, sigmoid(zs), color=CYAN, lw=2, alpha=0.6)
ax[2].set_title("hard limit vs sigmoid — no slope to follow")
for a in ax: a.axhline(0, color=MUTED, lw=0.6); a.axvline(0, color=MUTED, lw=0.6)
plt.tight_layout(); plt.show()
""")

# ---------------------------------------------------------------- 12. gradient descent
md(rf"""
## 12 · Loss and gradient descent

**Manufacturing activity.** Commissioning a plant is a search: change a set point, measure, keep what
helped, step again.

**The challenge.** Step too far and you overshoot and oscillate; too small and it takes a week.

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

**Manufacturing activity.** No single auditor covers everything. One reads the compressed-air system, one
the thermal side, one the schedule. A supervisor combines their calls.

**The challenge.** Learn the records too well and you memorise them: perfect on last month, useless on
next month.

**The AI connection.** A hidden layer is that team. Training watches the **validation** error, and stops
where it turns.

{link('network', 'The network')} · {link('training', 'Training')}
""")

co(r"""
import warnings
mlp = MLPClassifier(hidden_layer_sizes=(12, 6), learning_rate_init=0.001,
                    max_iter=1, warm_start=True, random_state=0)
train_loss, val_err = [], []
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    for _ in range(120):
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

print(f"MLP accuracy on the sealed hours: {mlp.score(Xte, yte):.1%}")
print("Past the dashed line the network is memorising these hours, not learning the pattern.")
""")

# ---------------------------------------------------------------- 14. CNN
md(rf"""
## 14 · CNN on the thermal frame

**Manufacturing activity.** A thermal frame is not read pixel by pixel. An engineer sees a **shape**: a
cone spreading from a fitting, a compact disc on a housing.

**The challenge.** Shape is not in any single pixel, and it moves. The same leak appears at a different
position and angle in every frame.

**The AI connection.** A convolution slides a small filter across the frame and reports where its pattern
occurs. Early filters find edges; later ones combine edges into plumes and blobs. **The network learns the
filters** — that is the whole difference from Section 9.

{link('cnn-journey', 'Inside the CNN')}
""")

co(r"""
# What a convolution actually does — no framework needed.
from numpy.lib.stride_tricks import sliding_window_view

def conv2d(img, k):
    return np.einsum("ijkl,kl->ij", sliding_window_view(img, k.shape), k)

img = make_thermal("leak")
kv  = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], float)   # vertical edges
kh  = kv.T                                                     # horizontal edges
kb  = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], float)  # blobs / spots

fig, ax = plt.subplots(1, 4, figsize=(13, 3.2))
ax[0].imshow(img, cmap="inferno"); ax[0].set_title("input frame")
for a, (k, name) in zip(ax[1:], [(kv, "vertical edges"), (kh, "horizontal edges"), (kb, "blobs")]):
    a.imshow(np.abs(conv2d(img, k)), cmap="inferno"); a.set_title(name)
for a in ax: a.axis("off")
plt.tight_layout(); plt.show()
""")

md(r"""
### Train a small CNN

We build a labelled set of thermal frames — sound and defective, with the position, size and intensity of
each pattern varying from frame to frame so the network cannot memorise a location. Then a three-layer CNN
learns to grade them.

If TensorFlow is not available this cell prints a note and the notebook carries on.
""")

co(r"""
def make_thermal_set(n=900, seed=0):
    "Labelled thermal frames. y = 1 means an energy-loss defect is present."
    rng = np.random.default_rng(seed)
    Xi, yi, kinds_used = [], [], []
    pool = ["normal", "sunlit", "leak", "hotspot", "insulation"]
    lab  = {"normal": 0, "sunlit": 0, "leak": 1, "hotspot": 1, "insulation": 1}
    for i in range(n):
        k = pool[int(rng.integers(len(pool)))]
        im = make_thermal(k, seed=int(rng.integers(1e6)))
        # vary brightness and contrast a little, as a real camera would
        im = np.clip(im * rng.uniform(0.93, 1.07) + rng.uniform(-0.03, 0.03), 0, 1)
        Xi.append(im); yi.append(lab[k]); kinds_used.append(k)
    return np.array(Xi)[..., None].astype("float32"), np.array(yi), kinds_used

Ximg, yimg, kinds_used = make_thermal_set(900, seed=1)
Xi_tr, Xi_te, yi_tr, yi_te = train_test_split(Ximg, yimg, test_size=0.25,
                                              random_state=42, stratify=yimg)
print("frames:", Ximg.shape, " defect rate:", f"{yimg.mean():.1%}")

if KERAS:
    # Functional API, not Sequential: Grad-CAM in Section 15 needs to build a second
    # model over an intermediate layer, and that is reliable only on a functional graph.
    inp = keras.Input(shape=(64, 64, 1))
    x = layers.Conv2D(16, 3, activation="relu", padding="same")(inp)
    x = layers.MaxPooling2D()(x)
    x = layers.Conv2D(32, 3, activation="relu", padding="same")(x)
    x = layers.MaxPooling2D()(x)
    x = layers.Conv2D(64, 3, activation="relu", padding="same", name="last_conv")(x)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(32, activation="relu")(x)
    out = layers.Dense(1, activation="sigmoid")(x)
    cnn = keras.Model(inp, out)
    cnn.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    hist = cnn.fit(Xi_tr, yi_tr, validation_split=0.2, epochs=12, batch_size=32, verbose=0)

    plt.figure(figsize=(9, 3.5))
    plt.plot(hist.history["loss"], color=CYAN, lw=2, label="training loss")
    plt.plot(hist.history["val_loss"], color=AMBER, lw=2, label="validation loss")
    plt.xlabel("epoch"); plt.ylabel("loss"); plt.legend(); plt.title("CNN training")
    plt.tight_layout(); plt.show()

    cnn_acc = cnn.evaluate(Xi_te, yi_te, verbose=0)[1]
    print(f"CNN accuracy on held-out frames: {cnn_acc:.1%}")
    print("Compare that with the best any mean-temperature threshold managed in Section 9.")
else:
    cnn_acc = None
    print("Keras not available — skipping CNN training.")
""")

# ---------------------------------------------------------------- 15. Grad-CAM
md(rf"""
## 15 · Locating the loss — Grad-CAM

**Manufacturing activity.** A grade does not get a work order raised. Maintenance needs to know *which
fitting*.

**The challenge.** A classifier outputs a probability and no location. An engineer asked to act on a bare
number will — rightly — not trust it.

**The AI connection.** Grad-CAM weights the last feature maps by how much each pushed the score towards
"defect", then projects them back onto the frame. The bright region is the evidence the network used.

{link('leak-locate', 'Locating the loss')}
""")

co(r"""
def grad_cam(model, image, layer_name="last_conv"):
    "Class-activation map for a single frame (image shape 64x64x1)."
    grad_model = keras.Model(model.inputs,
                             [model.get_layer(layer_name).output, model.output])
    with tf.GradientTape() as tape:
        maps, pred = grad_model(image[None, ...])
        loss = pred[:, 0]
    grads = tape.gradient(loss, maps)[0]                 # (h, w, c)
    weights = tf.reduce_mean(grads, axis=(0, 1))         # how much each map mattered
    cam = tf.reduce_sum(maps[0] * weights, axis=-1).numpy()
    cam = np.maximum(cam, 0)
    cam = cam / (cam.max() + 1e-9)
    # stretch the small feature map back over the frame
    rep = image.shape[0] // cam.shape[0]
    return np.kron(cam, np.ones((rep, rep)))[:image.shape[0], :image.shape[1]]

if KERAS:
    show = ["leak", "hotspot", "insulation", "sunlit"]
    fig, ax = plt.subplots(2, len(show), figsize=(3.1 * len(show), 6))
    for j, k in enumerate(show):
        im = make_thermal(k, seed=7)[..., None].astype("float32")
        p = float(cnn.predict(im[None, ...], verbose=0)[0, 0])
        cam = grad_cam(cnn, im)
        ax[0, j].imshow(im[..., 0], cmap="inferno"); ax[0, j].set_title(f"{k}\np(defect) = {p:.2f}")
        ax[1, j].imshow(im[..., 0], cmap="gray")
        ax[1, j].imshow(cam, cmap="turbo", alpha=0.55)
        ax[1, j].set_title("where it looked", fontsize=9)
        ax[0, j].axis("off"); ax[1, j].axis("off")
    plt.tight_layout(); plt.show()
    print("The heat map is the work order: this fitting, this region, go and check it.")
else:
    print("Keras not available — skipping Grad-CAM.")
""")

# ---------------------------------------------------------------- 16. evaluation
md(rf"""
## 16 · Evaluation — the sustainability audit

**Manufacturing activity.** Every energy-saving claim is audited: predicted against metered, on hours the
model never saw.

**The challenge.** A single accuracy figure hides the thing that matters. Predicting "not wasteful" for
every hour scores well on an efficient plant — and finds nothing.

**The AI connection.** The confusion matrix separates the four outcomes, and the two errors do not cost
the same:

- **False alarm** — an engineer walks the line and finds nothing. Cost: one hour, and a little credibility.
- **Missed waste** — the leak runs until the bill. Cost: weeks of compressed air, and the carbon with it.

{link('audit', 'The energy audit')}
""")

co(r"""
for name, model in [("Random Forest", rf), ("Neural network", mlp)]:
    p = model.predict(Xte)
    tn, fp, fn, tp = confusion_matrix(yte, p).ravel()
    print(f"{name:15s} accuracy {accuracy_score(yte, p):.1%}   "
          f"recall on wasteful hours {recall_score(yte, p):.1%}   "
          f"(false alarms {fp}, MISSED {fn})")

fig, ax = plt.subplots(1, 2, figsize=(10, 4))
for a, (name, model) in zip(ax, [("Random Forest", rf), ("Neural network", mlp)]):
    ConfusionMatrixDisplay.from_predictions(
        yte, model.predict(Xte), display_labels=["efficient", "wasteful"],
        cmap="Blues", colorbar=False, ax=a)
    a.set_title(name)
plt.tight_layout(); plt.show()

# The trap, made explicit
naive = np.zeros_like(yte)
print(f"\nA model that calls EVERY hour efficient: accuracy {accuracy_score(yte, naive):.1%}, "
      f"recall {recall_score(yte, naive, zero_division=0):.1%}")
print("Good accuracy, zero value. Recall on the wasteful hours is what the project is judged on.")
""")

# ---------------------------------------------------------------- 17. verdict
md(rf"""
## 17 · The verdict — ML vs DL, measured

This is the section the whole notebook has been building towards. Run both methods on both data types and
read the result off the table, rather than taking anyone's word for it.

{link('proof', 'The verdict')}
""")

co(r"""
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    ann_en = MLPRegressor(hidden_layer_sizes=(16, 8), max_iter=1200,
                          random_state=0).fit(Xtr, yen[itr])
r2_ann = r2_score(yen[ite], ann_en.predict(Xte))

print("ON THE 8 NAMED METER CHANNELS")
print(f"  Random Forest  — energy R2 {r2_en:.3f}")
print(f"  Neural network — energy R2 {r2_ann:.3f}")
print("  -> about the same. The engineer already named the features; ML is simpler and easier to defend.")

print("\nON THE RAW THERMAL FRAME")
print("  Best hand-made feature (mean temperature) : no threshold separates defect from sound")
if KERAS:
    print(f"  CNN                                       : {cnn_acc:.1%} accuracy")
else:
    print("  CNN                                       : (Keras unavailable in this runtime)")
print("  -> only the CNN can start. Nobody can name 4,096 pixel features.")

pd.DataFrame({
    "": ["Energy & CO2 from the 8 readings", "Grade a thermal frame from pixels",
         "Who names the features?"],
    "ML — Random Forest": ["works", "cannot even start", "The engineer"],
    "DL — ANN / CNN":     ["works", "learns the pattern", "The network learns them"],
})
""")

md(r"""
### The promise, now demonstrated

> **Machine Learning predicts sustainability metrics from sensor measurements.
> Deep Learning discovers hidden patterns in images that feature engineering cannot easily capture.**

Neither method is "better". Each belongs to its data type:

- When an engineer **has** named the features — load, flow, pressure, idle — use Machine Learning. It is
  faster, cheaper and far easier to defend in an audit.
- When nobody **can** name them — a thermal frame — Deep Learning is the option that works at all.

And in both cases the output is a recommendation to an engineer, not a decision.
""")

# ---------------------------------------------------------------- 18. anomaly
md(rf"""
## 18 · Anomaly detection — normal for the conditions

**Manufacturing activity.** Energy use is *supposed* to rise with load and with ambient temperature. A hot
afternoon on a full schedule costs more, and that is not waste.

**The challenge.** Because normal moves, a fixed kWh alarm limit is useless: set it high and leaks hide
inside a busy shift, set it low and it cries wolf every summer.

**The AI connection.** Learn what normal looks like for *these conditions*, then score the **residual** —
the consumption the conditions do not explain. A leak is exactly that.

{link('anomaly', 'Normal vs excess')}
""")

co(r"""
rng = np.random.default_rng(7)

# 1. learn "normal" from a clean history
n_tr = 500
load_h = rng.uniform(30, 100, n_tr)
amb_h  = rng.uniform(12, 38, n_tr)
en_h   = energy_for(0.05, load_h, 8.0, amb_h) + rng.normal(0, 1.5, n_tr)
normal_model = LinearRegression().fit(np.c_[load_h, load_h**2, amb_h], en_h)

# 2. watch a live month, with a leak opening at hour 240
H = 480
th   = np.arange(H)
load = 65 + 22 * np.sin(2 * np.pi * th / 24.0) + rng.normal(0, 2.0, H)   # shift pattern
amb  = 24 +  9 * np.sin(2 * np.pi * (th - 6) / 24.0) + rng.normal(0, 1.0, H)
kwh  = energy_for(0.05, load, 8.0, amb) + rng.normal(0, 1.6, H)
kwh += 42.0 * np.clip((th - 240) * 0.0025, 0, 0.55)                      # the leak

expected = normal_model.predict(np.c_[load, load**2, amb])
resid    = kwh - expected
sigma    = float(np.std(resid[:100]))
thr      = 3 * sigma
alarm    = np.where(resid > thr)[0]

fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
ax[0].plot(th, kwh, color=CYAN, lw=1.6, label="metered kWh")
ax[0].plot(th, expected, color=MUTED, lw=1.6, ls="--", label="expected for load & weather")
ax[0].set_ylabel("kWh per hour"); ax[0].legend()
ax[0].set_title("the raw consumption never leaves its daily band")
ax[1].bar(th, resid, color=np.where(resid > thr, RED, CYAN))
ax[1].axhline(thr, color=RED, ls="--")
ax[1].set_xlabel("hour"); ax[1].set_ylabel("unexplained kWh")
ax[1].set_title(f"residual = metered - expected  (alarm at 3 sigma = {thr:.1f} kWh)")
plt.tight_layout(); plt.show()

if len(alarm):
    lost = float(np.sum(np.clip(resid[alarm[0]:], 0, None)))
    print(f"Anomaly first flagged at hour {int(alarm[0])}; the leak opened at hour 240.")
    print(f"Unexplained energy since: {lost:,.0f} kWh  ->  {lost*GRID_KG/1000:.1f} t CO2")
""")

# ---------------------------------------------------------------- 19. optimize
md(rf"""
## 19 · Optimisation — the efficient operating point

**Manufacturing activity.** The plant chooses how hard machines are loaded, how much they idle, and when
high-draw processes run.

**The challenge.** Energy per unit is **not** lowest at the lowest load. Baseload is spread over fewer
units, so running gently can cost more carbon per part. Intuition points the wrong way.

**The AI connection.** With a model that predicts kWh from the readings, sweep the operating range and read
the minimum off the curve.

{link('optimize', 'The efficient operating point')}
""")

co(r"""
def specific_energy_curve(waste, idle, ambient, model=en_model):
    loads = np.linspace(30, 100, 71)
    rows  = signals_for(np.full_like(loads, waste), loads,
                        np.full_like(loads, float(idle)), np.full_like(loads, float(ambient)))
    kwh   = model.predict(scaler.transform(rows))
    units = units_for(loads, idle)
    return loads, kwh / np.clip(units, 1e-6, None)

plt.figure(figsize=(9, 4.2))
for waste, col in [(0.0, GREEN), (0.25, CYAN), (0.6, AMBER), (0.9, RED)]:
    loads, spec = specific_energy_curve(waste, idle=8, ambient=24)
    b = int(np.argmin(spec))
    plt.plot(loads, spec, color=col, lw=2, label=f"waste = {waste:.2f}")
    plt.plot(loads[b], spec[b], "*", color=col, ms=15)
    print(f"waste {waste:.2f} -> efficient load {loads[b]:.0f}%   "
          f"best {spec[b]:.2f} kWh/unit   worst on the curve {spec.max():.2f}")
plt.axhline(SPEC_LIMIT, color=RED, ls="--", label=f"wasteful above {SPEC_LIMIT}")
plt.xlabel("machine load (%)"); plt.ylabel("kWh per unit"); plt.legend()
plt.title("specific energy across the operating range — the star is the efficient point")
plt.tight_layout(); plt.show()
""")

md(r"""
Read the curves as an engineer:

- At **low load** the plant still pays its baseload and spreads it over very few units — high kWh per unit.
- As load rises each unit carries less of that fixed cost, so the curve falls.
- Push further and **losses grow faster than output**: drives run past their best-efficiency point, cooling
  rises, scrap goes up. The curve turns back upward.
- The two effects give a genuine **minimum**, and a leak **lifts the whole curve** while drifting the
  efficient point towards higher load. The curve is a model prediction, so read the trend rather than the
  exact percent.

Two separate recommendations fall out: **run at the efficient point**, and **fix the waste that lifts the
curve**. The dashboard prices both.
""")

# ---------------------------------------------------------------- 20. fusion
md(rf"""
## 20 · AI fusion — one prioritised action

**Manufacturing activity.** By now the plant produces three opinions every hour: a predicted energy figure,
an anomaly score, and a thermal grade with a location.

**The challenge.** Three screens is three chances to miss something.

**The AI connection.** Fusion combines them into one ranked recommendation with its evidence attached.
Numbers say **how much** is being lost; images say **where**.

{link('fusion-engine', 'The sustainability screen')} · {link('pipeline', 'The whole system')}
""")

co(r"""
def recommend(excess_kwh, anomaly_sigma, cam_finding, tariff=0.16):
    "Combine the ML excess, the anomaly score and the CNN evidence into one action."
    cost_month = excess_kwh * 24 * 30 * tariff
    co2_year   = excess_kwh * 24 * 365 * GRID_KG / 1000.0
    if anomaly_sigma >= 3 and cam_finding != "nothing found":
        pr, act = "HIGH", f"Investigate now — camera shows {cam_finding}"
    elif anomaly_sigma >= 2:
        pr, act = "MEDIUM", "Schedule an inspection at the next changeover"
    else:
        pr, act = "LOW", "No action — within normal for this load"
    return dict(priority=pr, excess_kwh_h=excess_kwh, sigma=anomaly_sigma,
                evidence=cam_finding, cost_per_month=round(cost_month),
                t_co2_per_year=round(co2_year, 1), action=act)

screen = pd.DataFrame([
    recommend(41.0, 4.6, "leak plume at fitting 2"),
    recommend(23.5, 2.9, "broad warm band on the oven door seal"),
    recommend(11.2, 2.1, "bright disc on the drive-end bearing"),
    recommend(6.4,  0.7, "nothing found"),
], index=["Line 3 - compressed air", "Line 1 - curing oven",
          "Line 2 - drive motor", "Line 4 - packing"])
screen
""")

md(r"""
Note what the screen does **not** do: it never isolates a line by itself. Every row ends in a
recommendation an engineer approves. That was fixed back in Section 1 and holds all the way through.
""")

# ---------------------------------------------------------------- 21. dashboard
md(rf"""
## 21 · The sustainability dashboard — the business case

**Manufacturing activity.** A plant manager does not buy a model. They approve a spend against a saving in
kilowatt-hours, tonnes of CO₂ and money.

**The challenge.** AI savings are easy to overstate. A recommendation only saves energy if someone acts on
it, and only part of the identified waste is economic to fix.

**The AI connection.** Convert the model outputs into the plant's own units. Every figure below is
**arithmetic on assumptions you can change** — none of it is a measurement.

{link('dashboard', 'The sustainability dashboard')}
""")

co(r"""
def business_case(machines=18, tariff=0.16, fixed_pct=55,
                  kwh_per_machine_hour=130.0, waste_share=0.14):
    "Everything here is arithmetic on the arguments. Change them and the case changes."
    HOURS         = 24 * 30
    baseline_kwh  = machines * kwh_per_machine_hour * HOURS
    avoidable_kwh = baseline_kwh * waste_share
    saved_kwh     = avoidable_kwh * fixed_pct / 100.0
    return dict(baseline_MWh_month = baseline_kwh / 1000,
                after_MWh_month    = (baseline_kwh - saved_kwh) / 1000,
                saved_MWh_month    = saved_kwh / 1000,
                saved_tCO2_year    = saved_kwh * GRID_KG / 1000 * 12,
                saved_cost_month   = saved_kwh * tariff,
                pct_removed        = saved_kwh / baseline_kwh * 100)

case = business_case()
for k, v in case.items():
    print(f"{k:22s} {v:,.1f}")

plt.figure(figsize=(6, 4))
plt.bar(["before\nmonthly review", "after\ncontinuous monitoring"],
        [case["baseline_MWh_month"], case["after_MWh_month"]], color=[RED, GREEN])
plt.ylabel("MWh per month"); plt.title("monthly plant consumption")
plt.tight_layout(); plt.show()

print("\nThe 'after' bar never reaches zero and never will: the plant still has to make product,")
print("and only part of the waste it finds is economic to fix. A recommendation nobody acts on")
print("saves nothing at all — which is why 'share actually fixed' is an input, not an assumption.")
""")

# ---------------------------------------------------------------- 22. summary
md(rf"""
## 22 · Summary — the whole system

```
   METERS  ──►  clean ──► scale ──► split ──►  RANDOM FOREST  ──┐
   (8 named channels)                          kWh, CO2, waste  │
                                                                ├──►  FUSION  ──►  DASHBOARD
   THERMAL CAMERA  ─────────────────────────►  CNN + Grad-CAM ──┘   one ranked      kWh, tCO2,
   (4,096 raw pixels)                          grade + location      action           money
```

**What was built**

| Stage | Method | Output |
|---|---|---|
| Predict the hour's energy and CO₂ | Random Forest regression | kWh, kg CO₂ |
| Flag a wasteful hour | Random Forest / MLP classification | efficient vs wasteful |
| Rank the drivers | Feature importance | what to investigate first |
| Grade a thermal frame | CNN | leak / hotspot / lagging / sound |
| Locate the loss | Grad-CAM | the fitting to check |
| Catch the unexplained excess | Regression + residual | anomaly score in σ |
| Find the greenest setting | Sweep + minimise | efficient operating point |
| Combine everything | Fusion rules | one ranked action |
| Justify the spend | Arithmetic | MWh, tCO₂, currency |

**The three things worth remembering**

1. **Sensor measurements → Machine Learning.** The engineer names the features; the model weights them.
2. **Images → Deep Learning.** Nobody can name 4,096 pixel features, so the network learns them.
3. **Manufacturing Engineer + AI.** The system watches every machine every hour and reports what it finds.
   A person still decides, still signs off, and still owns the outcome.

{link('start', 'The whole project map')}
""")

nb = new_notebook(cells=cells, metadata={
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"},
    "colab": {"provenance": []},
})
nbf.validate(nb)
with open("Sustainable_Manufacturing_DL.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"wrote Sustainable_Manufacturing_DL.ipynb  ({len(cells)} cells, "
      f"{sum(1 for c in cells if c.cell_type=='code')} code)")
