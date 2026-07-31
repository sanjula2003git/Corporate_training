"""
Builds Unusual_Machine_Behaviour_DL.ipynb from nbformat cells.
Run:  py -3.13 build_nb.py

The notebook is standalone (Colab): it re-defines the machine vibration model inline so the
notebook and any future app always agree.

APP and COLAB are the two places to change once the material is published.

NOTE for future editors:
  * inside co(...) cells use only single-line "..." docstrings or # comments. A triple-quoted
    docstring would close the outer r\"\"\" string and break this build script.
  * build Keras models with the FUNCTIONAL api. Under Keras 3 a Sequential model has no defined
    .output until it is called, which breaks any second model built from its layers.
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

# ----------------------------------------------------------------- placeholders
APP   = "https://machine-anomaly-dl.streamlit.app"               # <- update after the Streamlit app is deployed
COLAB = "https://colab.research.google.com/REPLACE-ME"   # <- update after this notebook is pushed

cells = []
def md(t):  cells.append(new_markdown_cell(t.strip("\n")))
def co(t):  cells.append(new_code_cell(t.strip("\n")))
def link(stage, label):
    """A deep link into the illustration app for this stage."""
    return f"🎬 **See it illustrated:** [{label}]({APP}/?stage={stage})"


# ---------------------------------------------------------------- title
md(rf"""
# Unusual Machine Behaviour Detection
### Teaching AI through the vibration and temperature of a rotating machine

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({COLAB})

This notebook is the runnable companion to the Unusual Machine Behaviour course. You are not learning AI for
its own sake — you are building a **condition monitor** for an industrial machine, and each AI method
appears because a real maintenance problem required it.

**The framing throughout:** the maintenance engineer stays in charge and stays accountable. A model that
sees only sensor traces cannot hear the machine, cannot feel a loose foot through a boot sole, and cannot
authorise a shutdown that stops a production line. The monitor only eases the part one person cannot carry
alone — watching every machine, every hour, on every shift, when a fault announces itself for six weeks
before it breaks. The monitor *reports*; the engineer *decides*.

**The one idea this notebook proves:**

> **Machine Learning detects unusual behaviour using the features an engineer already knows how to measure.
> Deep Learning learns the shape of "normal" directly from the raw signal, and flags anything unlike it —
> including the fault nobody thought to name.**

That last clause is the whole point, and Section 19 measures it. Every other notebook in this series asks a
model to *recognise* something. This one asks a model to notice that something is **new**, which is a
different and harder question.

**What we build, in the order a real project runs it:**

1. The machine that fails without warning — the problem
2. One measurement → data collection
3. Load the condition-monitoring log
4. Data inspection (dropouts, dead channels)
5. Data cleaning
6. Normalization — and why it is fitted on healthy data only
7. The split that defines anomaly detection
8. The traditional baseline — the control chart
9. ML anomaly detection — Isolation Forest on the named features
10. **The wall** — a classifier cannot catch a fault it has never seen
11. Deep learning — the neuron
12. Activation functions
13. Loss and gradient descent
14. The autoencoder — learning to rebuild "normal"
15. Reconstruction error, and where to put the threshold
16. The autoencoder on the raw vibration spectrum
17. Which frequency is to blame
18. Evaluation — precision, recall, and the cost of being wrong
19. The verdict — ML vs DL, measured
20. Drift — when "normal" itself moves
21. Lead time — how early did we catch it?
22. Fusion — one prioritised work order
23. The reliability dashboard — the business case
24. Summary — the whole system

{link('start', 'The project overview')}
""")

md(r"""
## Setup

In Colab the libraries below are already installed. If you run this elsewhere, uncomment the install line.
TensorFlow/Keras is used for the autoencoders — the notebook detects whether it is present and falls back to
a scikit-learn autoencoder if not, so **every section produces a result either way**.
""")

co(r"""
# !pip install numpy pandas scikit-learn tensorflow matplotlib

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.neural_network import MLPRegressor
from sklearn.covariance import EmpiricalCovariance
from sklearn.metrics import (confusion_matrix, ConfusionMatrixDisplay, roc_curve, auc,
                             accuracy_score, recall_score, precision_score)

np.random.seed(42)
plt.rcParams["figure.figsize"] = (8, 4)

# The course palette
CYAN, AMBER, GREEN, RED, MUTED = "#4fc3f7", "#ffb74d", "#66bb6a", "#ef5350", "#8b949e"
PURPLE = "#ba68c8"

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    KERAS = True
    tf.random.set_seed(42)
except Exception as e:                      # noqa: BLE001
    KERAS = False
    print("TensorFlow not available — a scikit-learn autoencoder will be used instead.", e)

print("Environment ready.  Keras available:", KERAS)
""")

# ---------------------------------------------------------------- 1. the machine
md(rf"""
## 1 · The machine that fails without warning — the problem

**Maintenance activity.** A 75 kW motor drives a gearbox and a pump through two rolling-element bearings.
It runs three shifts. A fitter walks the line once a week with a handheld vibration meter and writes an
overall reading on a clipboard.

**The challenge.** Machines rarely fail suddenly. A spalled bearing, a loosening coupling or a chipped gear
tooth announces itself for **weeks** before it breaks — in vibration long before it appears in temperature,
and in temperature long before it appears in a noise a person can hear. But the announcement is quiet, the
walkround is weekly, and the reading written down is a single number.

**The AI connection.** The machine does not need its engineers replaced. It needs the *gap between the
sensor and the clipboard* closed — the signal watched continuously and the change reported while it is still
small. That continuous watch is the only reason AI belongs on a machine.

{link('breakdown', 'A machine that stops without warning')}
""")

co(r"""
# The cost curve that justifies the whole project. A fault caught early is a planned job;
# the same fault caught late is a breakdown, and the ratio is not small.
days   = np.arange(0, 61)
sever  = 0.02 * np.exp(days / 11.0)              # damage grows exponentially once it starts
sever  = np.clip(sever, 0, 1.6)

planned_cost   = 1_200.0                          # bearing, labour, planned stop at a changeover
breakdown_cost = 46_000.0                         # unplanned stop: lost output, secondary damage, overtime
cost = planned_cost + (breakdown_cost - planned_cost) * np.clip((sever - 0.15) / 1.1, 0, 1) ** 1.5

weekly = np.arange(0, 61, 7)                      # the fitter's walkround
detect_hand = 42                                  # a handheld overall reading notices it here
detect_ai   = 16                                  # a continuous monitor notices the change here

plt.figure(figsize=(9.5, 4.2))
plt.plot(days, cost, color=RED, lw=2, label="cost of repairing it on this day")
plt.axvline(detect_ai,   color=GREEN, ls="--", lw=2, label=f"continuous monitor notices (day {detect_ai})")
plt.axvline(detect_hand, color=AMBER, ls="--", lw=2, label=f"weekly walkround notices (day {detect_hand})")
for w in weekly:
    plt.plot(w, planned_cost, "|", color=MUTED, ms=10)
plt.yscale("log"); plt.xlabel("days since the fault started"); plt.ylabel("repair cost (log scale)")
plt.title("the same fault, repaired on two different days")
plt.legend(fontsize=8); plt.tight_layout(); plt.show()

c_ai   = float(np.interp(detect_ai,   days, cost))
c_hand = float(np.interp(detect_hand, days, cost))
print(f"Repaired on day {detect_ai:2d}: {c_ai:8,.0f}")
print(f"Repaired on day {detect_hand:2d}: {c_hand:8,.0f}")
print(f"Difference on ONE fault, on ONE machine: {c_hand - c_ai:,.0f}")
print()
print("Note what the monitor is NOT claiming. It does not prevent the fault, does not repair")
print("anything, and does not extend the bearing's life by a single hour. It buys DAYS OF")
print("WARNING, and days of warning are what turn a breakdown into a planned job.")
""")

# ---------------------------------------------------------------- 2. one measurement
md(rf"""
## 2 · One measurement → data collection

**Maintenance activity.** An accelerometer on the bearing housing, a thermocouple in it, and a current clamp
on the motor supply. Every hour the gateway records a short vibration burst and the slow channels alongside
it.

**The challenge.** A vibration burst is **2,048 numbers**. Nobody reads that. So for fifty years the
industry has reduced it to a handful of scalars an engineer can put a limit on.

**The AI connection.** Those scalars are the *named features*, and they are the first half of this course.
The burst they were computed from is the second half.

The eight named channels, and what each one is for:

| Channel | Source | Unit | What it is sensitive to |
|---|---|---|---|
| RMS velocity | Accelerometer, integrated | mm/s | Overall severity — the ISO 10816 number on the clipboard |
| Peak acceleration | Accelerometer | g | The largest single impact in the burst |
| Kurtosis | Computed from the burst | — | *Impulsiveness*. Rises early for bearing damage |
| Crest factor | Peak ÷ RMS | — | Also impulsiveness, and it falls again as damage spreads |
| 1× amplitude | Spectrum at shaft speed | mm/s | **Imbalance** |
| 2× amplitude | Spectrum at twice shaft speed | mm/s | **Misalignment** |
| Bearing temperature | Thermocouple | °C | Friction and lubrication — a *late* indicator |
| Motor current | Current clamp | A | Load, and anything that makes the motor work harder |

Read that table again and notice something. Every channel was designed **by someone who already knew which
fault they were looking for.** Keep that in mind until Section 10.

{link('sensors', 'Where the sensors sit')}
""")

co(r"""
# --- the machine, as physics ------------------------------------------------
FS        = 5000.0          # sampling rate, Hz
NSAMP     = 2048            # samples per burst  -> 0.41 s, 2.44 Hz resolution
SHAFT_HZ  = 25.0            # 1500 rpm
GEAR_TEETH = 20
GEAR_HZ   = SHAFT_HZ * GEAR_TEETH     # gear mesh frequency, 500 Hz
BPFO_HZ   = SHAFT_HZ * 3.6            # outer-race ball pass frequency, 90 Hz
NBINS     = 512                        # keep 0 .. 1248 Hz of the spectrum
TVEC      = np.arange(NSAMP) / FS
FREQS     = np.arange(NBINS) * FS / NSAMP

# A rotating machine is never silent. Even in perfect health it shows its shaft speed,
# a little of the second harmonic, the gear mesh tone, and a broadband noise floor.
def waveform(kind="healthy", load=0.70, seed=0, sev=1.0):
    rng = np.random.default_rng(seed)
    t   = TVEC
    ph  = lambda: rng.uniform(0, 2 * np.pi)
    a1  = 0.55 + 0.25 * load                       # residual imbalance, grows a little with load
    x   = rng.normal(0, 0.10 + 0.03 * load, NSAMP) # broadband floor
    x  += a1   * np.sin(2 * np.pi * SHAFT_HZ * t + ph())
    x  += 0.16 * np.sin(2 * np.pi * 2 * SHAFT_HZ * t + ph())
    x  += 0.07 * np.sin(2 * np.pi * 3 * SHAFT_HZ * t + ph())
    x  += 0.05 * np.sin(2 * np.pi * GEAR_HZ * t + ph())      # healthy gear mesh tone

    if kind == "imbalance":
        x += sev * 1.30 * np.sin(2 * np.pi * SHAFT_HZ * t + ph())
    elif kind == "misalignment":
        x += sev * 0.95 * np.sin(2 * np.pi * 2 * SHAFT_HZ * t + ph())
        x += sev * 0.45 * np.sin(2 * np.pi * 3 * SHAFT_HZ * t + ph())
    elif kind == "bearing":
        # spalled outer race: a repeating IMPACT that rings the housing resonance at 800 Hz
        imp = np.zeros(NSAMP)
        imp[::max(int(FS / BPFO_HZ), 1)] = 1.0
        ring = np.exp(-TVEC[:220] * 250.0) * np.sin(2 * np.pi * 800.0 * TVEC[:220])
        x += sev * 1.10 * np.convolve(imp, ring)[:NSAMP]
    elif kind == "gear":
        # a chipped tooth: the mesh tone grows and picks up +/- 1x sidebands.
        # It is TONAL, not impulsive, and it carries very little energy -- which is exactly
        # why the overall RMS on the clipboard does not move. Section 10 depends on this.
        x += sev * 0.13 * np.sin(2 * np.pi * GEAR_HZ * t + ph())
        x += sev * 0.07 * np.sin(2 * np.pi * (GEAR_HZ - SHAFT_HZ) * t + ph())
        x += sev * 0.07 * np.sin(2 * np.pi * (GEAR_HZ + SHAFT_HZ) * t + ph())
    return x

def raw_spectrum(x):
    "Single-sided amplitude spectrum of ONE burst, first NBINS bins."
    return np.abs(np.fft.rfft(x * np.hanning(NSAMP)))[:NBINS] * 2.0 / NSAMP

# A real vibration analyser does not store one spectrum. It linear-averages 8 or 16 of them,
# because a single burst carries a lot of random noise and averaging cancels what is random
# while leaving what is periodic. That is not a detail -- a gear peak that stands 9 standard
# deviations clear of normal in an 8-average spectrum stands barely 2 clear in a single one,
# and Section 16 does not work without it.
NAVG = 8

def avg_spectrum(kind, load, rng, sev=1.0, navg=NAVG):
    "NAVG bursts, linear-averaged — what the analyser actually stores."
    return np.mean([raw_spectrum(waveform(kind, load, int(rng.integers(1e9)), sev))
                    for _ in range(navg)], axis=0)

FAULTS = ["healthy", "imbalance", "misalignment", "bearing", "gear"]
rng0 = np.random.default_rng(3)
fig, ax = plt.subplots(2, 5, figsize=(16, 5))
for j, k in enumerate(FAULTS):
    x = waveform(k, seed=3)
    s = avg_spectrum(k, 0.7, rng0)
    ax[0, j].plot(TVEC[:400], x[:400], color=CYAN, lw=0.8)
    ax[0, j].set_title(k, fontsize=10); ax[0, j].set_ylim(-4, 4)
    ax[1, j].semilogy(FREQS, s + 1e-5, color=PURPLE, lw=0.8)
    ax[1, j].set_ylim(1e-4, 1)
    ax[1, j].set_xlabel("Hz", fontsize=8)
    if j == 0:
        ax[0, j].set_ylabel("waveform"); ax[1, j].set_ylabel("spectrum")
plt.tight_layout(); plt.show()
print("Top row: what the accelerometer records. Bottom row: the same burst as a spectrum.")
print("Look at 'gear' in the bottom row and remember what it looks like. It matters in Section 10.")
""")

md(r"""
### From a burst to eight numbers

This is the step the whole condition-monitoring industry is built on, and it is worth being conscious that
it **throws information away**. That is not a criticism — 2,048 numbers an hour per machine is not something
a person can review. It is simply the trade we are about to examine.
""")

co(r"""
FEATURES = ["rms_mm_s", "peak_g", "kurtosis", "crest_factor",
            "amp_1x", "amp_2x", "bearing_temp_c", "motor_current_a"]
NICE = ["RMS (mm/s)", "Peak (g)", "Kurtosis", "Crest factor",
        "1x amp", "2x amp", "Temp (C)", "Current (A)"]

def bin_at(hz):
    "Index of the spectrum bin nearest a frequency."
    return int(np.argmin(np.abs(FREQS - hz)))

def features_from(x, kind, load, ambient, rng, sev=1.0):
    "The eight named channels an engineer would compute from one burst."
    s    = raw_spectrum(x)
    rms  = float(np.sqrt(np.mean(x ** 2)))
    peak = float(np.max(np.abs(x)))
    kurt = float(np.mean((x - x.mean()) ** 4) / (x.var() ** 2 + 1e-12))
    # temperature and current are SLOW channels: they respond to friction and load, and they
    # are the last things to move. Only the bearing fault heats the housing.
    temp = ambient + 22.0 + 14.0 * load + (9.0 * sev if kind == "bearing" else 0.0)
    curr = 42.0 + 46.0 * load + (3.0 * sev if kind == "misalignment" else 0.0)
    return [rms, peak, kurt, peak / (rms + 1e-9),
            float(s[bin_at(SHAFT_HZ)]), float(s[bin_at(2 * SHAFT_HZ)]),
            temp + rng.normal(0, 0.4), curr + rng.normal(0, 0.6)]

def measure(kind, load, ambient, rng, sev=1.0):
    "One logged measurement: features from a burst, plus the averaged spectrum it came from."
    x = waveform(kind, load, seed=int(rng.integers(1e9)), sev=sev)
    return (features_from(x, kind, load, ambient, rng, sev),
            avg_spectrum(kind, load, rng, sev))

# What the eight numbers say about each fault, at equal severity
rng = np.random.default_rng(0)
rows = [features_from(waveform(k, seed=5), k, 0.7, 21.0, rng) for k in FAULTS]
tab  = pd.DataFrame(rows, index=FAULTS, columns=NICE).round(2)
print(tab.to_string())
print()
base = tab.loc["healthy"]
print("Change from healthy, as a percentage:")
print(((tab - base) / base * 100).round(1).to_string())
""")

md(r"""
Read the second table carefully, because it is the argument of this entire notebook.

- **Imbalance** lights up `1x amp`. **Misalignment** lights up `2x amp`. **Bearing** damage lights up
  `kurtosis` and `peak`. Three faults, three channels, each designed for its job. This is fifty years of
  condition monitoring working exactly as intended.
- **Gear** moves almost nothing. RMS barely shifts. Kurtosis does not rise, because a chipped tooth produces
  a *tonal* vibration, not an impulsive one.

That last row is not a modelling accident — it is a well-known blind spot. Overall vibration severity
(ISO 10816, the number on the fitter's clipboard) is famously insensitive to early gear and bearing defects,
because those faults are **high in frequency and low in energy**. The overall number is dominated by the
shaft-speed vibration and simply does not notice them.

**Key takeaway:** a named feature can only find the fault it was named for.
""")

# ---------------------------------------------------------------- 3. load
md(rf"""
## 3 · Load the condition-monitoring log

**Maintenance activity.** The gateway has been logging hourly for months. We pull the export.

**The challenge.** An export is not a dataset. Accelerometers come loose, thermocouples open-circuit, and
the same hour appears twice after the historian resyncs.

**The AI connection.** Loading it into a DataFrame is the first AI step — shape, types and a first look.

Note the column `state`: it is here **only so we can grade ourselves at the end**. Nothing between here and
Section 18 is allowed to train on it. On a real machine you would not have it, and pretending you do is the
most common way anomaly-detection projects fool themselves.

{link('load', 'The log arrives')}
""")

co(r"""
def make_export(n=1400, seed=42):
    "Months of hourly measurements. Mostly healthy, as a working machine is."
    rng = np.random.default_rng(seed)
    # A real machine is healthy nearly all the time. The gear fault is DELIBERATELY RARE
    # and deliberately excluded from anything we train on before Section 16.
    kinds = rng.choice(FAULTS, n, p=[0.78, 0.06, 0.06, 0.06, 0.04])
    load  = np.clip(rng.normal(0.70, 0.13, n), 0.25, 1.0)
    amb   = rng.normal(21.0, 2.5, n)
    sev   = rng.uniform(0.45, 1.0, n)

    rowsF, rowsS = [], []
    for i in range(n):
        f, s = measure(kinds[i], load[i], amb[i], rng, sev[i])
        rowsF.append(f); rowsS.append(s)

    df = pd.DataFrame(rowsF, columns=FEATURES).round(4)
    df.insert(0, "reading_id", np.arange(1, n + 1))
    df["load_frac"] = load.round(3)
    df["state"]     = kinds                       # LABEL - for scoring only
    spec = np.array(rowsS)

    # the faults every real export carries
    for c in FEATURES:
        df.loc[rng.choice(n, int(0.05 * n), replace=False), c] = np.nan
    df.loc[rng.choice(n, 11, replace=False), "bearing_temp_c"]  = -50.0   # open thermocouple
    df.loc[rng.choice(n, 9,  replace=False), "rms_mm_s"]        = 0.0     # accelerometer fell off
    df.loc[rng.choice(n, 8,  replace=False), "motor_current_a"] = 9999.0  # clamp saturated
    dup = rng.choice(n, 15, replace=False)
    return (pd.concat([df, df.iloc[dup]], ignore_index=True),
            np.vstack([spec, spec[dup]]))

raw, raw_spec = make_export()
raw.to_csv("machine_condition_log.csv", index=False)
np.save("machine_spectra.npy", raw_spec)
print("wrote machine_condition_log.csv and machine_spectra.npy")

df = pd.read_csv("machine_condition_log.csv")
print("shape:", df.shape, "  spectra:", raw_spec.shape)
print("\nhow often each state appears:")
print(df.state.value_counts().to_string())
df.head()
""")

# ---------------------------------------------------------------- 4. inspect
md(rf"""
## 4 · Data inspection — the sensor health check

**Maintenance activity.** Before trusting months of readings, an engineer checks the instruments. Is the
accelerometer still glued on? Is the thermocouple open-circuit?

**The challenge.** A dead sensor does not report "dead". It reports a number. An open thermocouple reads
about −50 °C; a detached accelerometer reads 0.0 mm/s; a saturated clamp reads its full scale.

**The AI connection.** Here that check matters more than in any other project in this series. An anomaly
detector's entire job is to flag things that look unlike normal — and **a broken sensor is the most unusual
thing in the dataset**. Leave these in and the monitor will spend its life reporting instrument faults with
total confidence.

{link('inspect', 'Sensor health check')}
""")

co(r"""
print("Missing readings per channel")
print(df[FEATURES].isna().sum(), "\n")
print("Duplicate rows:", int(df.duplicated().sum()), "\n")
print(df[FEATURES].describe().T[["min", "max"]])

fig, ax = plt.subplots(1, 2, figsize=(12, 3.6))
ax[0].bar(NICE, df[FEATURES].isna().sum().values, color=AMBER)
ax[0].set_ylabel("missing"); ax[0].set_title("dropouts per channel")
ax[0].tick_params(axis="x", rotation=40)
for lab in ax[0].get_xticklabels():
    lab.set_ha("right")
ax[1].plot(df.bearing_temp_c.values, ".", ms=3, color=CYAN)
ax[1].axhline(-50, color=RED, ls="--", label="open thermocouple")
ax[1].set_title("bearing temperature, as logged"); ax[1].legend(fontsize=8)
plt.tight_layout(); plt.show()
""")

md(r"""
Read the `min` / `max` table like an engineer, not a statistician:

- `bearing_temp_c` at **−50 °C** is an open thermocouple, not a cold bearing.
- `rms_mm_s` at exactly **0.0** is a detached accelerometer. A running machine always vibrates.
- `motor_current_a` at **9999** is a saturated clamp.

Every one of those is a *valid number* and a *fault* at the same time — and every one of them would be the
single most anomalous reading in the file.
""")

# ---------------------------------------------------------------- 5. clean
md(rf"""
## 5 · Data cleaning

**Maintenance activity.** A faulty instrument is repaired or discounted before its readings reach a report.

**The challenge.** Deleting every affected row throws away good readings from the other seven channels.
Keeping them poisons everything downstream.

**The AI connection.** Mark the physically impossible as *missing* rather than deleting the row, then fill
with the channel's **median** — a value the outliers cannot drag.

{link('clean', 'Dead channels and dropouts')}
""")

co(r"""
clean = df.drop_duplicates().copy()

clean.loc[clean.bearing_temp_c < 0,      "bearing_temp_c"]  = np.nan   # open thermocouple
clean.loc[clean.rms_mm_s <= 1e-6,        "rms_mm_s"]        = np.nan   # sensor fell off
clean.loc[clean.motor_current_a > 500,   "motor_current_a"] = np.nan   # clamp saturated
clean.loc[clean.crest_factor > 50,       "crest_factor"]    = np.nan

for c in FEATURES:
    clean[c] = clean[c].fillna(clean[c].median())

print(f"rows: {len(df)} -> {len(clean)}   missing left: {int(clean[FEATURES].isna().sum().sum())}")
print()
print("Why fill with the median rather than the mean? Compare each before and after treatment:")
for c in ["bearing_temp_c", "motor_current_a"]:
    print(f"  {c:17s} mean  {df[c].mean():9.2f} -> {clean[c].mean():8.2f}"
          f"   median {df[c].median():7.2f} -> {clean[c].median():7.2f}")
print()
print("The mean of each dirty channel was meaningless. The median barely moved, which is exactly")
print("why it is the safe thing to fill the gaps with.")
""")

# ---------------------------------------------------------------- 6. normalize
md(rf"""
## 6 · Normalization — fitted on healthy data only

**Maintenance activity.** The channels do not share a scale. Current runs to 90 A, kurtosis sits near 2, and
1× amplitude is a fraction of a millimetre per second.

**The challenge.** Any method that measures a *distance* lets the largest-numbered channel dominate — not
because it matters most, but because its unit is bigger.

**The AI connection.** Standardise every channel. But here comes the difference from every other notebook in
this series, and it is easy to get wrong:

> **The scaler is fitted on healthy readings only.**

If you fit it on everything, the mean and standard deviation it learns already contain the faults. The
anomalies get scaled towards the middle of the range, and you have quietly taught the monitor that they are
ordinary. That is **information leakage**, and in anomaly detection it is the classic own goal — it does not
crash, it does not warn you, it just silently makes your results better than they should be.

{link('normalize', 'One common scale')}
""")

co(r"""
healthy_mask = (clean.state == "healthy").to_numpy(dtype=bool)
Xall_raw     = clean[FEATURES].to_numpy(dtype=float)
labels       = clean.state.astype(str).to_numpy()      # plain numpy, not an extension array

scaler = StandardScaler().fit(Xall_raw[healthy_mask])     # <- HEALTHY ONLY
Xall   = scaler.transform(Xall_raw)

# What leakage would have looked like, so the warning above is not just an assertion
leaky = StandardScaler().fit(Xall_raw)
kurt_i = FEATURES.index("kurtosis")
bad = labels == "bearing"
print("Scaled kurtosis of the BEARING readings — how far from normal do they look?")
print(f"  scaler fitted on healthy only : mean {Xall[bad, kurt_i].mean():5.2f} sigma")
print(f"  scaler fitted on everything   : mean {leaky.transform(Xall_raw)[bad, kurt_i].mean():5.2f} sigma")
print()
print("Same readings, same fault. Fitting the scaler on contaminated data shrinks the bearing")
print("fault towards normal before any model has seen it. The model is not wrong afterwards --")
print("it was handed a rescaled world in which the fault is less unusual than it really is.")
""")

# ---------------------------------------------------------------- 7. split
md(rf"""
## 7 · The split that defines anomaly detection

**Maintenance activity.** You have months of running. Almost all of it was fine.

**The challenge.** Every other notebook in this series splits the data into train and test and lets the
model see examples of both classes. Here you cannot. You have thousands of healthy hours and a handful of
faults, and — the part that matters — **you do not have an example of the fault that will happen next.**

**The AI connection.** So the split changes shape:

- **Train** on healthy readings only. The model's job is to learn what normal *is*.
- **Validate** on held-out healthy readings, to set a threshold.
- **Test** on everything — healthy and every fault — to find out what it catches.

This is not a supervised problem wearing a different hat. It is a different question: not *"which fault is
this?"* but *"is this the machine I know?"*

{link('split', 'Train on normal only')}
""")

co(r"""
idx_h = np.where(healthy_mask)[0]
idx_f = np.where(~healthy_mask)[0]

# healthy split three ways; the faults are never trained on at all
h_tr, h_tmp = train_test_split(idx_h, test_size=0.35, random_state=42)
h_va, h_te  = train_test_split(h_tmp, test_size=0.55, random_state=42)

Xtr = Xall[h_tr]                       # healthy only -- this is all the model learns from
Xva = Xall[h_va]                       # healthy only -- used to place the threshold
ite = np.concatenate([h_te, idx_f])    # the audit set: healthy AND every fault
Xte, yte_state = Xall[ite], labels[ite]
yte = (yte_state != "healthy").astype(int)          # 1 = something is wrong

print(f"train    {len(h_tr):4d} readings — all healthy")
print(f"validate {len(h_va):4d} readings — all healthy")
print(f"test     {len(ite):4d} readings — {int(yte.sum())} faulty, {int((1-yte).sum())} healthy")
print()
print("Test-set composition:")
print(pd.Series(yte_state).value_counts().to_string())
""")

# ---------------------------------------------------------------- 8. control chart
md(rf"""
## 8 · The traditional baseline — the control chart

**Maintenance activity.** Before any AI, this is what a plant actually does: pick the channel everyone
trusts (overall RMS velocity), draw a limit at three standard deviations, and alarm above it. ISO 10816 even
publishes the limits for you.

**The challenge.** It works, and then it does not. Two things break it:

- **One channel sees one kind of fault.** RMS is dominated by shaft-speed vibration.
- **Normal moves.** Vibration and temperature both rise with load. A limit tight enough to catch a fault at
  30% load screams all day at 100% load.

**The AI connection.** Everything that follows is an attempt to fix those two problems: use *all* the
channels, and judge each reading against what is normal **for these conditions**.

{link('control-chart', 'The 3-sigma limit')}
""")

co(r"""
rms_i  = FEATURES.index("rms_mm_s")
rms_h  = Xall_raw[healthy_mask, rms_i]
lim    = rms_h.mean() + 3 * rms_h.std()

rms_te = Xall_raw[ite, rms_i]
fired  = rms_te > lim

print(f"3-sigma limit on RMS velocity: {lim:.3f} mm/s\n")
print("What the control chart catches, fault by fault:")
for k in FAULTS:
    m = yte_state == k
    if m.sum():
        print(f"  {k:14s} {fired[m].sum():3d} / {m.sum():3d} flagged  ({100*fired[m].mean():5.1f}%)")

plt.figure(figsize=(10, 4))
for k, col in zip(FAULTS, [MUTED, CYAN, PURPLE, AMBER, RED]):
    m = yte_state == k
    plt.scatter(np.where(m)[0], rms_te[m], s=14, color=col, label=k, alpha=0.75)
plt.axhline(lim, color=RED, ls="--", lw=2, label="3-sigma limit")
plt.ylabel("RMS velocity (mm/s)"); plt.xlabel("reading"); plt.legend(fontsize=8, ncol=3)
plt.title("one channel, one limit")
plt.tight_layout(); plt.show()
""")

md(r"""
The control chart is not useless — it catches the loud faults, which is why it has survived for fifty years.
But look at the per-fault breakdown. The faults that move shaft-speed vibration are caught. The **gear**
fault is essentially invisible to it, and so is a good share of the bearing damage, because neither of them
puts much energy at 25 Hz.

**Key takeaway:** a single-channel limit finds the faults that are loud, not the faults that are early.
""")

# ---------------------------------------------------------------- 9. Isolation Forest
md(rf"""
## 9 · ML anomaly detection — Isolation Forest on the named features

**Maintenance activity.** Use all eight channels at once instead of one, and stop drawing the limit by hand.

**The challenge.** With eight channels there is no single line to draw. "Normal" is a *region* in eight
dimensions, and a reading can sit inside the normal range of every individual channel while being an
impossible **combination** of them — high temperature at low load, say.

**The AI connection.** An **Isolation Forest** repeatedly splits the data at random. Points in dense regions
need many splits to isolate; unusual points fall out in very few. The average number of splits is the
anomaly score. It learns from healthy readings only, and needs no labels.

This is the **first half of the course promise: ML detects unusual behaviour using the features an engineer
already named.**

{link('isolation-forest', 'Isolating the odd one out')}
""")

co(r"""
iso = IsolationForest(n_estimators=300, contamination="auto", random_state=42).fit(Xtr)

# Higher score = more anomalous. sklearn returns the opposite sign, so negate.
s_va  = -iso.score_samples(Xva)
s_te  = -iso.score_samples(Xte)
thr_i = float(np.quantile(s_va, 0.99))        # allow 1% false alarms on healthy validation data

print(f"Threshold from healthy validation data (99th percentile): {thr_i:.3f}\n")
print("What the Isolation Forest catches, fault by fault:")
iso_hits = {}
for k in FAULTS:
    m = yte_state == k
    if m.sum():
        hit = float((s_te[m] > thr_i).mean())
        iso_hits[k] = hit
        print(f"  {k:14s} {int((s_te[m] > thr_i).sum()):3d} / {m.sum():3d} flagged  ({100*hit:5.1f}%)")

plt.figure(figsize=(10, 4))
for k, col in zip(FAULTS, [MUTED, CYAN, PURPLE, AMBER, RED]):
    m = yte_state == k
    plt.scatter(np.where(m)[0], s_te[m], s=14, color=col, label=k, alpha=0.75)
plt.axhline(thr_i, color=RED, ls="--", lw=2, label="threshold")
plt.ylabel("anomaly score"); plt.xlabel("reading"); plt.legend(fontsize=8, ncol=3)
plt.title("Isolation Forest on the eight named features")
plt.tight_layout(); plt.show()
""")

md(r"""
A clear improvement on the control chart — imbalance, misalignment and bearing damage are all caught far
more often, using no labels at all and nothing but readings the plant already collects.

And the gear fault is still, effectively, missed. Look at the number next to it and then at the healthy
row: it flags roughly one gear reading in six, while already raising false alarms on a few percent of
perfectly healthy ones. At that rate it is not detecting the fault — it is occasionally tripping over noise
and happening to be right. You could not build a work order on it.

That is not the Isolation Forest's failure. It is working perfectly on the data it was given, and **the
eight named features do not contain the gear fault.** No method applied to those eight numbers can find
something that is not in them.

**Key takeaway:** feature engineering sets a ceiling that no amount of modelling can lift.
""")

# ---------------------------------------------------------------- 10. the wall
md(rf"""
## 10 · The wall — a classifier cannot catch a fault it has never seen

**Maintenance activity.** The obvious objection at this point: "we have labelled fault data — why not just
train a classifier to recognise each fault?"

So let us do exactly that, and do it properly. We will train a Random Forest on labelled examples of
**healthy, imbalance, misalignment and bearing** damage. It will be very good.

Then we will show it a **gear** fault — a fault type it has never seen in training, because on a real
machine you never have an example of the failure that has not happened yet.

{link('classifier-wall', 'The fault it was never taught')}
""")

co(r"""
KNOWN = ["healthy", "imbalance", "misalignment", "bearing"]
known_m = np.isin(labels, KNOWN)

Xk, yk = Xall[known_m], labels[known_m]
Xk_tr, Xk_te, yk_tr, yk_te = train_test_split(Xk, yk, test_size=0.3,
                                              random_state=42, stratify=yk)
clf = RandomForestClassifier(n_estimators=300, random_state=42).fit(Xk_tr, yk_tr)
print(f"Supervised classifier accuracy on the faults it WAS taught: "
      f"{accuracy_score(yk_te, clf.predict(Xk_te)):.1%}")
print("Excellent. Now show it the one it was not taught.\n")

gear_m    = labels == "gear"
gear_pred = clf.predict(Xall[gear_m])                       # named so nothing downstream shadows it
gear_conf = clf.predict_proba(Xall[gear_m]).max(axis=1)
gear_said_healthy = int((gear_pred == "healthy").sum())
print(f"{int(gear_m.sum())} gear-fault readings presented to the classifier:")
print(pd.Series(gear_pred).value_counts().to_string())
print(f"\nMean confidence in those (wrong) answers: {gear_conf.mean():.1%}")
print(f"Times it said 'healthy'                 : {gear_said_healthy} of {int(gear_m.sum())}")
print("Not once did it say 'I do not recognise this'. It has no way to say that.")
""")

md(r"""
**Read that result slowly. This is the wall.**

The classifier is not broken. It is doing exactly what it was built to do: sort every reading into one of
the four boxes it was given. It has no box for *"I have not seen this before"*, so it cannot use one. A
damaged gear arrives, and the machine is confidently declared **healthy**.

And notice the confidence figure. It is not hedging. A supervised classifier's probabilities are shares of a
pie that must add to 1 — they say *which of my classes is most likely*, never *whether any of them applies*.
A high number there is not evidence that the answer is right.

This is the structural difference between the two questions:

| | Classification | Anomaly detection |
|---|---|---|
| Question | Which known fault is this? | Is this the machine I know? |
| Needs | Labelled examples of every fault | Examples of normal |
| New fault type | Silently mislabelled | Flagged as unlike normal |
| Fails when | The fault is new | Normal itself changes (Section 20) |

> **You cannot classify a fault you have never seen. So stop trying to recognise faults, and start
> measuring distance from normal.**

Everything from here on is a network that learns what healthy looks like. The remaining question is what you
show it — and Section 9 already proved that eight hand-made numbers are not enough.
""")

# ---------------------------------------------------------------- 11. neuron
md(rf"""
## 11 · Deep learning starts with one neuron

**Maintenance activity.** A vibration analyst weighs several indicators at once — the 1× is up a little, the
kurtosis is up a lot, the temperature has not moved — and forms a judgement.

**The challenge.** That judgement lives in one head. There are perhaps a few thousand people in the world
who can do it well, and there are far more machines than that.

**The AI connection.** Write it down and it is arithmetic: `z = w·x + b`. The weights are not chosen by
anyone — they are learned.

{link('analyst-brain', "The analyst's judgement")} · {link('neuron', 'The neuron')}
""")

co(r"""
x = Xte[np.argmax(s_te)]                     # the most anomalous reading in the audit set
w = np.array([0.8, 0.6, 1.2, 0.7, 0.5, 0.5, 0.9, 0.3])
b = -0.4

z = float(np.dot(w, x) + b)
def sigmoid(v): return 1 / (1 + np.exp(-np.clip(v, -50, 50)))
print(f"z = w.x + b = {z:+.3f}   ->   p(unusual) = {sigmoid(z):.3f}")

plt.figure(figsize=(9, 3))
plt.bar(NICE, w * x, color=[RED if v >= 0 else CYAN for v in w * x])
plt.axhline(0, color=MUTED, lw=1)
plt.ylabel("w x x"); plt.title(f"each channel's contribution  (z = {z:+.2f})")
plt.xticks(rotation=40, ha="right"); plt.tight_layout(); plt.show()
""")

# ---------------------------------------------------------------- 12. activation
md(rf"""
## 12 · Activation — turning a sum into a decision

**Maintenance activity.** A monitor does not report a weighted sum. It reports a state: run on, or inspect.

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
ax[1].plot(zs, np.maximum(0, zs), color=PURPLE, lw=2);    ax[1].set_title("ReLU — passes positives")
ax[2].step(zs, (zs > 0).astype(float), color=RED, lw=2, where="mid")
ax[2].plot(zs, sigmoid(zs), color=CYAN, lw=2, alpha=0.6)
ax[2].set_title("hard threshold vs sigmoid — no slope to follow")
for a in ax: a.axhline(0, color=MUTED, lw=0.6); a.axvline(0, color=MUTED, lw=0.6)
plt.tight_layout(); plt.show()
""")

# ---------------------------------------------------------------- 13. gradient descent
md(rf"""
## 13 · Loss and gradient descent

**Maintenance activity.** Balancing a rotor is a search: add a trial weight, measure, keep what helped, step
again.

**The challenge.** Step too far and you overshoot and oscillate; too small and it takes all shift.

**The AI connection.** Loss = how wrong. Gradient = downhill. Learning rate = step size. Same overshoot,
same reason.

{link('gradient-descent', 'Loss and gradient descent')}
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

# ---------------------------------------------------------------- 14. autoencoder
md(rf"""
## 14 · The autoencoder — learning to rebuild "normal"

**Maintenance activity.** Ask an experienced fitter to describe a healthy machine and they will not recite
eight numbers. They will describe a *pattern*: it hums at this pitch, it warms to about this much, it draws
about this current for that load. They carry a compressed model of normal, and they notice when reality
departs from it.

**The challenge.** How do you write that down without knowing in advance which departures matter?

**The AI connection.** An **autoencoder** is a network shaped like an hourglass. It must squeeze its input
through a narrow middle layer and then rebuild it. The bottleneck makes memorising impossible: to rebuild
eight channels from three numbers it has to learn the *structure* — that current tracks load, that
temperature follows current, that 1× and RMS move together.

Train it on healthy data only, and it becomes very good at rebuilding healthy readings and *only* healthy
readings. Show it something unlike anything it trained on and the rebuild comes out wrong.

**That rebuild error is the anomaly score.** No labels, no fault examples, no assumption about what a fault
looks like.

```
   8 channels ──► 5 ──► 3 ──► 5 ──► 8 channels
                       the bottleneck
   input                                 rebuilt
             error = how different they are
```

{link('autoencoder', 'The hourglass')}
""")

co(r"""
def build_autoencoder(n_in, bottleneck=3, hidden=None):
    "Functional API on purpose -- see the note at the top of the build script."
    hidden = hidden or max(bottleneck * 2, n_in // 2)
    inp = keras.Input(shape=(n_in,))
    e = layers.Dense(hidden, activation="relu")(inp)
    e = layers.Dense(bottleneck, activation="relu", name="bottleneck")(e)
    d = layers.Dense(hidden, activation="relu")(e)
    out = layers.Dense(n_in, activation="linear")(d)
    m = keras.Model(inp, out)
    m.compile(optimizer="adam", loss="mse")
    return m

class SklearnAE:
    "Fallback when TensorFlow is missing: an MLP trained to reproduce its own input."
    def __init__(self, bottleneck=3, hidden=5, seed=0):
        self.m = MLPRegressor(hidden_layer_sizes=(hidden, bottleneck, hidden),
                              activation="relu", max_iter=1200, random_state=seed)
    def fit(self, X):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.m.fit(X, X)
        return self
    def predict(self, X, **kw):
        return self.m.predict(X)

if KERAS:
    ae = build_autoencoder(len(FEATURES), bottleneck=3)
    hist = ae.fit(Xtr, Xtr, validation_data=(Xva, Xva),
                  epochs=120, batch_size=32, verbose=0)
    plt.figure(figsize=(9, 3.4))
    plt.plot(hist.history["loss"], color=CYAN, lw=2, label="training loss")
    plt.plot(hist.history["val_loss"], color=AMBER, lw=2, label="validation loss")
    plt.xlabel("epoch"); plt.ylabel("mean squared rebuild error"); plt.legend()
    plt.title("the autoencoder learning to rebuild healthy readings")
    plt.tight_layout(); plt.show()
else:
    ae = SklearnAE().fit(Xtr)
    print("Trained the scikit-learn fallback autoencoder.")

def rebuild_error(model, X):
    "Mean squared error between each reading and its rebuild."
    return np.mean((X - model.predict(X, verbose=0) if KERAS
                    else X - model.predict(X)) ** 2, axis=1)

e_tr = rebuild_error(ae, Xtr)
print(f"\nRebuild error on healthy training readings : {e_tr.mean():.4f}")
print(f"Rebuild error on the faulty readings       : "
      f"{rebuild_error(ae, Xall[~healthy_mask]).mean():.4f}")
print("The network was never told what a fault is. It is simply worse at rebuilding one.")
""")

# ---------------------------------------------------------------- 15. threshold
md(rf"""
## 15 · Reconstruction error, and where to put the threshold

**Maintenance activity.** A score is not an alarm. Somebody has to say how high is too high, and that
decision is a **business** decision, not a statistical one.

**The challenge.** Two errors, two very different costs:

- **False alarm** — a fitter opens a healthy machine. Cost: a few hours, and a little credibility. Spend
  that credibility too often and the alarms get muted, which is how monitoring projects really die.
- **Missed fault** — the machine runs to failure. Cost: the breakdown from Section 1.

**The AI connection.** Set the threshold on **held-out healthy data**, at the false-alarm rate the plant is
willing to live with. Never on the faults — you would be tuning to the very examples you claim not to have.

{link('threshold', 'Where to draw the line')}
""")

co(r"""
e_va = rebuild_error(ae, Xva)
e_te = rebuild_error(ae, Xte)

print("Choosing the threshold from healthy validation data alone:")
for q in (0.90, 0.95, 0.99, 0.995):
    t = float(np.quantile(e_va, q))
    print(f"  allow {100*(1-q):4.1f}% false alarms -> threshold {t:.4f} "
          f"-> catches {100*(e_te[yte == 1] > t).mean():5.1f}% of faults")

thr_ae = float(np.quantile(e_va, 0.99))

fig, ax = plt.subplots(1, 2, figsize=(13, 4))
ax[0].hist(e_te[yte == 0], bins=40, color=GREEN, alpha=0.75, label="healthy")
ax[0].hist(e_te[yte == 1], bins=40, color=RED,   alpha=0.75, label="faulty")
ax[0].axvline(thr_ae, color="k", ls="--", lw=2, label="threshold")
ax[0].set_xlabel("rebuild error"); ax[0].set_ylabel("readings"); ax[0].legend()
ax[0].set_title("the two populations")
for k, col in zip(FAULTS, [MUTED, CYAN, PURPLE, AMBER, RED]):
    m = yte_state == k
    ax[1].scatter(np.where(m)[0], e_te[m], s=14, color=col, label=k, alpha=0.75)
ax[1].axhline(thr_ae, color="k", ls="--", lw=2)
ax[1].set_xlabel("reading"); ax[1].set_ylabel("rebuild error"); ax[1].legend(fontsize=8, ncol=3)
ax[1].set_title("autoencoder on the eight named features")
plt.tight_layout(); plt.show()

print("\nPer-fault detection, autoencoder on the named features:")
ae_feat_hits = {}
for k in FAULTS:
    m = yte_state == k
    if m.sum():
        ae_feat_hits[k] = float((e_te[m] > thr_ae).mean())
        print(f"  {k:14s} {100*ae_feat_hits[k]:5.1f}%")
""")

md(r"""
Compare that per-fault table with the Isolation Forest's in Section 9. The neural network is a little better
on imbalance and misalignment, clearly **worse** on bearing damage — and the gear fault is missed by both.

That is worth sitting with, because it is the result students expect least. We have just replaced a
classical method with a neural network and gained nothing at all; on one fault we went backwards. **The
method was never the bottleneck.** Both models are reading the same eight numbers, and Section 2 showed that
those eight numbers barely move for a gear fault.

If a neural network is not beating a 2008 algorithm on your problem, the useful question is almost never
"which network should I try next?". It is "what am I feeding it?"

If you want to find a fault that is not in the features, you have to stop using the features.
""")

# ---------------------------------------------------------------- 16. spectrum AE
md(rf"""
## 16 · The autoencoder on the raw vibration spectrum

**Maintenance activity.** Go back to the burst. Not the eight numbers computed from it — the **512-bin
spectrum** itself: how much vibration there is at every frequency.

**The challenge.** Nobody sets limits on 512 numbers. There is no ISO table for it, no clipboard column, and
no engineer with the time to look at one every hour on every machine. This is exactly the data that gets
thrown away in Section 2 because it is unmanageable by hand.

**The AI connection.** An autoencoder does not need it to be manageable by hand. Train it to rebuild healthy
spectra and it learns the machine's whole signature at once — every peak, at every frequency, and how tall
each one normally is. A new peak at a frequency that is normally quiet cannot be rebuilt, because nothing in
training ever looked like that.

**The network is not looking for a gear fault. It does not know what a gear is.** It is reporting that this
spectrum is not one of the spectra it knows how to draw.

{link('spectrum-ae', 'Rebuilding the spectrum')}
""")

co(r"""
# Work in decibels. On a linear scale the 1x peak is so much taller than everything else that
# it would dominate the error and hide exactly the small high-frequency peaks we care about.
# clean.index still carries the original row numbers, so the spectra line up row for row
spec_clean = np.load("machine_spectra.npy")[clean.index.to_numpy()]
# The floor matters. Too small and the log magnifies the random noise in the quiet bins until
# it swamps the peaks we care about; too large and it flattens the peaks themselves.
DB_FLOOR = 1e-3
S_db = 20 * np.log10(spec_clean + DB_FLOOR)

# Standardise EACH BIN against healthy, exactly as Section 6 standardised each channel. Without
# this the naturally noisy bins dominate the rebuild error and drown the quiet ones -- and a new
# peak in a normally quiet bin is precisely the thing we are trying to detect. After this step
# the error is measured in "healthy standard deviations of that frequency", which is the unit
# a vibration analyst already thinks in.
s_scaler = StandardScaler().fit(S_db[healthy_mask])        # HEALTHY ONLY, again
S = np.clip(s_scaler.transform(S_db), -10, 10)

Str, Sva, Ste = S[h_tr], S[h_va], S[ite]
print("spectra:", S.shape, " train:", Str.shape)

if KERAS:
    sae = build_autoencoder(NBINS, bottleneck=16, hidden=96)
    shist = sae.fit(Str, Str, validation_data=(Sva, Sva),
                    epochs=180, batch_size=32, verbose=0)
    plt.figure(figsize=(9, 3.2))
    plt.plot(shist.history["loss"], color=CYAN, lw=2, label="training loss")
    plt.plot(shist.history["val_loss"], color=AMBER, lw=2, label="validation loss")
    plt.xlabel("epoch"); plt.ylabel("rebuild error"); plt.legend()
    plt.title("autoencoder learning the healthy spectrum")
    plt.tight_layout(); plt.show()
else:
    sae = SklearnAE(bottleneck=16, hidden=96).fit(Str)
    print("Trained the scikit-learn fallback autoencoder on the spectra.")

se_va, se_te = rebuild_error(sae, Sva), rebuild_error(sae, Ste)
thr_s = float(np.quantile(se_va, 0.99))

print("\nPer-fault detection, autoencoder on the RAW SPECTRUM:")
spec_hits = {}
for k in FAULTS:
    m = yte_state == k
    if m.sum():
        spec_hits[k] = float((se_te[m] > thr_s).mean())
        print(f"  {k:14s} {100*spec_hits[k]:5.1f}%")

plt.figure(figsize=(10, 4))
for k, col in zip(FAULTS, [MUTED, CYAN, PURPLE, AMBER, RED]):
    m = yte_state == k
    plt.scatter(np.where(m)[0], se_te[m], s=14, color=col, label=k, alpha=0.75)
plt.axhline(thr_s, color="k", ls="--", lw=2, label="threshold")
plt.ylabel("rebuild error"); plt.xlabel("reading"); plt.legend(fontsize=8, ncol=3)
plt.title("autoencoder on the raw spectrum — including the fault nobody labelled")
plt.tight_layout(); plt.show()
""")

# ---------------------------------------------------------------- 17. which frequency
md(rf"""
## 17 · Which frequency is to blame

**Maintenance activity.** "Something is unusual" does not get a work order raised. The planner needs to know
*what to send a fitter to look at*.

**The challenge.** An anomaly score is one number. An engineer asked to strip a gearbox on the strength of
one number will — rightly — refuse.

**The AI connection.** The rebuild error is not one number. It is **one error per frequency bin**, and we
summed it. Do not sum it: plot it. The bins the network could not rebuild are the frequencies that changed,
and in rotating machinery a frequency *is* a diagnosis.

This is the autoencoder's answer to Grad-CAM, and on this problem it is sharper — because unlike a region of
an image, a frequency has an exact physical meaning you can compute from the shaft speed and the tooth
count.

{link('which-frequency', 'Reading the error spectrum')}
""")

co(r"""
def error_spectrum(model, row):
    "Per-bin rebuild error for a single spectrum."
    r = row[None, :]
    rec = model.predict(r, verbose=0)[0] if KERAS else model.predict(r)[0]
    return (row - rec) ** 2, rec

show = ["healthy", "imbalance", "bearing", "gear"]
fig, ax = plt.subplots(2, len(show), figsize=(4.0 * len(show), 6.4))
for j, k in enumerate(show):
    cand = np.where(yte_state == k)[0]
    i = int(cand[np.argmax(se_te[cand])])           # the clearest example of this fault
    err, rec = error_spectrum(sae, Ste[i])
    ax[0, j].plot(FREQS, Ste[i], color=CYAN,  lw=1.0, label="measured")
    ax[0, j].plot(FREQS, rec,    color=AMBER, lw=1.0, label="rebuilt as healthy")
    ax[0, j].set_title(f"{k}\nscore {se_te[i]:.4f}", fontsize=10)
    ax[0, j].legend(fontsize=7)
    ax[1, j].plot(FREQS, err, color=RED, lw=1.0)
    ax[1, j].set_xlabel("Hz", fontsize=8)
    top = FREQS[int(np.argmax(err))]
    ax[1, j].axvline(top, color=MUTED, ls="--", lw=1)
    ax[1, j].set_title(f"largest error at {top:.0f} Hz", fontsize=9)
    if j == 0:
        ax[0, j].set_ylabel("scaled dB"); ax[1, j].set_ylabel("rebuild error")
plt.tight_layout(); plt.show()

# Turn the frequency into a diagnosis, the way an analyst would
gi = np.where(yte_state == "gear")[0]
i  = int(gi[np.argmax(se_te[gi])])
err, _ = error_spectrum(sae, Ste[i])
top3 = FREQS[np.argsort(err)[::-1][:3]]
print("The three frequencies the network could not rebuild on the gear reading:")
for f in top3:
    print(f"  {f:7.1f} Hz  =  {f/SHAFT_HZ:5.2f} x shaft speed")
print(f"\nShaft speed {SHAFT_HZ:.0f} Hz. The gear has {GEAR_TEETH} teeth, so it meshes at "
      f"{GEAR_HZ:.0f} Hz = {GEAR_TEETH} x shaft.")
print(f"The largest errors sit either side of {GEAR_HZ:.0f} Hz, about one shaft order away "
      f"({GEAR_HZ-SHAFT_HZ:.0f} and {GEAR_HZ+SHAFT_HZ:.0f} Hz).")
print()
print("That is worth a moment. The mesh tone at 500 Hz is present in a HEALTHY machine too, so")
print("the network rebuilds it happily and a rise there is only mildly surprising. The sidebands")
print("are new -- nothing in training had energy at those frequencies at all -- so they carry the")
print("error. Sidebands spaced at shaft speed around the mesh frequency is the textbook signature")
print("of a localised tooth defect: one tooth striking once per revolution.")
print()
print("Nobody encoded that rule. The network only reported which bins it could not rebuild.")
print("Reading it as 'a chipped tooth, count the teeth, order the spare' is still the engineer's job.")
""")

# ---------------------------------------------------------------- 18. evaluation
md(rf"""
## 18 · Evaluation — precision, recall, and the cost of being wrong

**Maintenance activity.** Before a monitor is trusted with a production machine, it is audited: how often
does it cry wolf, and how often does it miss?

**The challenge.** Accuracy is worse than useless here. The machine is healthy 78% of the time, so a monitor
that never alarms at all scores 78% and detects nothing. Every anomaly-detection project that reports
accuracy as its headline number is hiding something.

**The AI connection.** Two numbers, and they trade off against each other:

- **Recall** — of the readings that really were faults, what share did we flag? Misses cost breakdowns.
- **Precision** — of the readings we flagged, what share really were faults? False alarms cost credibility.

{link('audit', 'The monitoring audit')}
""")

co(r"""
methods = [("Control chart (RMS)",       (rms_te > lim).astype(int)),
           ("Isolation Forest (8 feat)", (s_te  > thr_i).astype(int)),
           ("Autoencoder (8 feat)",      (e_te  > thr_ae).astype(int)),
           ("Autoencoder (spectrum)",    (se_te > thr_s).astype(int))]

print(f"{'method':28s} {'recall':>8s} {'precision':>10s} {'false alarms':>13s} {'missed':>8s}")
for name, pred in methods:
    tn, fp, fn, tp = confusion_matrix(yte, pred).ravel()
    print(f"{name:28s} {recall_score(yte, pred):7.1%} "
          f"{precision_score(yte, pred, zero_division=0):9.1%} {fp:13d} {fn:8d}")

naive = np.zeros_like(yte)
print(f"\n{'Never alarm at all':28s} {recall_score(yte, naive, zero_division=0):7.1%} "
      f"{'--':>9s} {0:13d} {int(yte.sum()):8d}")
print(f"...and it would score {accuracy_score(yte, naive):.1%} accuracy. That is why accuracy is not")
print("quoted anywhere in this notebook.")

fig, ax = plt.subplots(1, 2, figsize=(12, 4.4))
for name, score in [("Isolation Forest (8 feat)", s_te), ("Autoencoder (8 feat)", e_te),
                    ("Autoencoder (spectrum)", se_te)]:
    fpr, tpr, _ = roc_curve(yte, score)
    ax[0].plot(fpr, tpr, lw=2, label=f"{name}  (AUC {auc(fpr, tpr):.3f})")
ax[0].plot([0, 1], [0, 1], ls="--", color=MUTED)
ax[0].set_xlabel("false alarm rate"); ax[0].set_ylabel("detection rate")
ax[0].set_title("every threshold at once"); ax[0].legend(fontsize=8)
ConfusionMatrixDisplay.from_predictions(yte, (se_te > thr_s).astype(int),
                                        display_labels=["healthy", "unusual"],
                                        cmap="Blues", colorbar=False, ax=ax[1])
ax[1].set_title("Autoencoder on the spectrum")
plt.tight_layout(); plt.show()
""")

# ---------------------------------------------------------------- 19. verdict
md(rf"""
## 19 · The verdict — ML vs DL, measured

This is the section the whole notebook has been building towards. Put every method against every fault and
read the result off the table.

{link('proof', 'The verdict')}
""")

co(r"""
rows = []
for k in FAULTS:
    m = yte_state == k
    if not m.sum():
        continue
    rows.append({
        "fault": k,
        "n": int(m.sum()),
        "Control chart":     f"{100*(rms_te[m] > lim ).mean():5.1f}%",
        "Isolation Forest":  f"{100*(s_te[m]   > thr_i).mean():5.1f}%",
        "AE (8 features)":   f"{100*(e_te[m]   > thr_ae).mean():5.1f}%",
        "AE (raw spectrum)": f"{100*(se_te[m]  > thr_s).mean():5.1f}%",
    })
verdict = pd.DataFrame(rows).set_index("fault")
print(verdict.to_string())
print("\n(The 'healthy' row is the false-alarm rate — lower is better. Every other row is")
print(" detection rate — higher is better.)")

print("\nAnd the supervised classifier from Section 10, on the fault it was never taught:")
print(f"  gear -> called 'healthy' {gear_said_healthy} times out of {int(gear_m.sum())}, "
      f"at {gear_conf.mean():.0%} mean confidence")
verdict
""")

md(r"""
### The promise, now demonstrated

> **Machine Learning detects unusual behaviour using the features an engineer already knows how to measure.
> Deep Learning learns the shape of "normal" directly from the raw signal, and flags anything unlike it —
> including the fault nobody thought to name.**

Read the table one column at a time:

- The **control chart** catches the loud faults. Fifty years of practice is not wrong, it is just limited.
- The **Isolation Forest** on eight named features is a large step up, needs no labels, costs almost nothing
  to run, and would be perfectly defensible in an audit. For imbalance, misalignment and bearing damage it
  is the sensible answer.
- The **autoencoder on the same eight features** does not beat it. Worth saying plainly: on named features,
  deep learning bought nothing here. Reach for it when you have a reason, not by reflex.
- The **autoencoder on the raw spectrum** is the only method that catches the gear fault, because it is the
  only method that ever saw the data the gear fault lives in.

**So the real lesson is not "deep learning wins".** It is that the choice of *representation* mattered far
more than the choice of *model* — the same method moved from blind to reliable purely by being shown richer
data. And underneath that sits the finding from Section 10, which no amount of modelling fixes:

> **A classifier can only find faults you have already met. An anomaly detector can find the ones you
> have not.**
""")

# ---------------------------------------------------------------- 20. drift
md(rf"""
## 20 · Drift — when "normal" itself moves

**Maintenance activity.** Summer arrives. The plant is 9 °C warmer. Nothing is wrong with the machine.

**The challenge.** The monitor learned what normal looked like in **February**. Every reading in July is
unlike its training data, so every reading in July is an anomaly. Within a fortnight the alarm is muted,
and a muted alarm is worth exactly nothing.

This is the failure mode of anomaly detection, and it is the mirror image of the wall in Section 10. A
classifier fails on faults it has not met; an anomaly detector fails when *normal* is something it has not
met.

**The AI connection.** Two honest fixes, and they are not alternatives — mature installations do both:

1. **Give the model the context.** Feed it ambient temperature and load so it can learn *"hot bearing on a
   hot day at full load is normal; hot bearing on a cold night at 30% load is not."*
2. **Retrain on a rolling window** of recent healthy data, so the model's idea of normal ages with the
   machine. Bearings bed in, foundations settle, and a five-year-old machine is legitimately not the machine
   that was commissioned.

{link('drift', 'When normal moves')}
""")

co(r"""
rngd = np.random.default_rng(5)
months  = np.arange(0, 12, 1 / 30.0)                     # a year, daily
ambient = 21.0 + 9.0 * np.sin(2 * np.pi * (months - 3.0) / 12.0)   # seasonal swing

drift_rows = []
for a in ambient:
    ld = float(np.clip(rngd.normal(0.70, 0.10), 0.25, 1.0))
    x  = waveform("healthy", ld, seed=int(rngd.integers(1e6)))
    drift_rows.append(features_from(x, "healthy", ld, a, rngd))
Xd = scaler.transform(np.array(drift_rows))
ed = rebuild_error(ae, Xd)
alarms = ed > thr_ae

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
fa_month = np.array([alarms[(months >= m) & (months < m + 1)].mean() for m in range(12)])
amb_month = np.array([ambient[(months >= m) & (months < m + 1)].mean() for m in range(12)])

fig, ax = plt.subplots(1, 2, figsize=(13, 4.2))
ax[0].plot(months, ed, color=CYAN, lw=1.0, label="rebuild error (machine is HEALTHY all year)")
ax[0].axhline(thr_ae, color=RED, ls="--", lw=2, label="threshold, set at commissioning")
ax[0].fill_between(months, thr_ae, ed, where=alarms, color=RED, alpha=0.25)
ax[0].set_xlabel("month"); ax[0].set_ylabel("rebuild error"); ax[0].legend(fontsize=8)
ax[0].set_title("a perfectly healthy machine, all year")
ax[1].bar(MONTHS, 100 * fa_month, color=[RED if f > 0.2 else GREEN for f in fa_month])
ax[1].set_ylabel("false alarms (%)"); ax[1].set_title("...and what the monitor said about it")
ax[1].tick_params(axis="x", rotation=45)
plt.tight_layout(); plt.show()

train_amb = 21.0
print(f"The model learned 'normal' from readings averaging {train_amb:.0f} C ambient.\n")
print(f"{'month':6s} {'ambient':>8s} {'off training':>13s} {'false alarms':>13s}")
for m in range(12):
    print(f"{MONTHS[m]:6s} {amb_month[m]:7.1f}C {amb_month[m]-train_amb:+12.1f}C "
          f"{100*fa_month[m]:12.1f}%")
best, worst = int(np.argmin(fa_month)), int(np.argmax(fa_month))
print(f"\nQuietest month {MONTHS[best]} ({100*fa_month[best]:.1f}%) — ambient closest to what it was taught.")
print(f"Worst month    {MONTHS[worst]} ({100*fa_month[worst]:.1f}%) — and nothing is wrong with the machine.")
print()
print("Note the shape: false alarms rise at BOTH ends of the year, not just in summer. The model")
print("is not afraid of heat — it is afraid of anything it was not shown. Drift has no preferred")
print("direction, which is why 'we trained it on a whole year' is the fix and 'we trained it on a")
print("hot week' is not.")
print()
print("Nothing changed on the machine. The model's idea of normal simply expired.")
print("A monitor is not a thing you install. It is a thing you keep.")
""")

# ---------------------------------------------------------------- 21. lead time
md(rf"""
## 21 · Lead time — how early did we catch it?

**Maintenance activity.** Everything so far has scored the monitor on *whether* it notices. Maintenance
does not buy that. It buys **notice**: enough days to order the part, book the crane and wait for a
changeover.

**The challenge.** A fault that grows over weeks crosses every method's threshold eventually. The question
is when, and the answer is what the whole business case rests on.

**The AI connection.** Simulate a bearing defect growing from nothing over sixty days and record the day
each method first alarms — then hold it to the rule real plants use: **two consecutive readings**, so a
single noisy sample cannot raise a work order.

{link('lead-time', 'Days of warning')}
""")

co(r"""
rngl = np.random.default_rng(9)
days_l  = np.arange(0, 61)
growth  = np.clip((days_l - 8) / 52.0, 0, 1) ** 1.6      # the defect starts on day 8

feat_l, spec_l = [], []
for g in growth:
    ld = float(np.clip(rngl.normal(0.70, 0.08), 0.3, 1.0))
    kind = "bearing" if g > 0 else "healthy"
    f, s = measure(kind, ld, 21.0, rngl, sev=max(g, 1e-6))
    feat_l.append(f); spec_l.append(s)

Xl = scaler.transform(np.array(feat_l))
Sl = np.clip(s_scaler.transform(20 * np.log10(np.array(spec_l) + DB_FLOOR)), -10, 10)

series = {"Control chart (RMS)":       (np.array(feat_l)[:, rms_i], lim),
          "Isolation Forest (8 feat)": (-iso.score_samples(Xl),     thr_i),
          "Autoencoder (8 feat)":      (rebuild_error(ae, Xl),      thr_ae),
          "Autoencoder (spectrum)":    (rebuild_error(sae, Sl),     thr_s)}

def first_alarm(score, t, consecutive=2):
    "Day of the first of `consecutive` readings above the threshold."
    over = score > t
    for i in range(len(over) - consecutive + 1):
        if over[i:i + consecutive].all():
            return int(days_l[i])
    return None

fig, ax = plt.subplots(figsize=(10, 4.4))
for (name, (sc, t)), col in zip(series.items(), [MUTED, CYAN, AMBER, RED]):
    d = first_alarm(sc, t)
    ax.plot(days_l, sc / t, color=col, lw=1.8, label=name)
    if d is not None:
        ax.plot(d, sc[list(days_l).index(d)] / t, "o", color=col, ms=9)
ax.axhline(1.0, color="k", ls="--", lw=1.5, label="alarm threshold")
ax.axvline(8, color=GREEN, ls=":", lw=1.5, label="defect starts (day 8)")
ax.set_yscale("log"); ax.set_xlabel("day"); ax.set_ylabel("score / threshold")
ax.set_title("a bearing defect growing over 60 days"); ax.legend(fontsize=8)
plt.tight_layout(); plt.show()

FAILS_ON = 60
print(f"{'method':28s} {'first alarm':>12s} {'days of warning':>17s}")
for name, (sc, t) in series.items():
    d = first_alarm(sc, t)
    print(f"{name:28s} {('day ' + str(d)) if d is not None else 'never':>12s} "
          f"{(FAILS_ON - d) if d is not None else 0:>17d}")
print(f"\nAssuming the bearing would have failed on day {FAILS_ON}.")
print("Days of warning is the number to put in front of a maintenance manager. Detection rate is")
print("the number to put in front of an engineer. They are not the same conversation.")
""")

# ---------------------------------------------------------------- 22. fusion
md(rf"""
## 22 · Fusion — one prioritised work order

**Maintenance activity.** By now the monitor produces several opinions for every machine on the line: a
control-chart state, an Isolation Forest score, two rebuild errors, and a dominant fault frequency.

**The challenge.** Five screens is five chances to miss something — and a score with no diagnosis on it
cannot be planned against.

**The AI connection.** Fusion combines them into one ranked work order with its evidence attached. The
named features say **how severe**; the error spectrum says **what and where**.

{link('fusion-engine', 'The work order')} · {link('pipeline', 'The whole system')}
""")

co(r"""
def diagnose(peak_hz):
    "Turn the dominant error frequency into the analyst's shortlist. Order = frequency / shaft speed."
    order = peak_hz / SHAFT_HZ
    if abs(order - 1) < 0.25:   return "1x — imbalance"
    if abs(order - 2) < 0.25:   return "2x — misalignment or looseness"
    if abs(order - GEAR_TEETH) < 1.5: return f"{GEAR_TEETH}x — gear mesh, suspect a tooth defect"
    if order > 25:              return "high-frequency — bearing race defect"
    return f"{order:.1f}x — unassigned, refer to an analyst"

def work_order(machine, sev_sigma, peak_hz, days_warning, running_hours):
    if sev_sigma >= 6:
        pr, act = "URGENT", "Stop at the next shift change — do not run to the weekend"
    elif sev_sigma >= 3:
        pr, act = "HIGH", f"Plan the repair inside {max(days_warning//2, 1)} days"
    elif sev_sigma >= 1.5:
        pr, act = "MEDIUM", "Add to the next planned outage; re-measure weekly"
    else:
        pr, act = "WATCH", "No action — inside normal for these conditions"
    return dict(machine=machine, priority=pr, sigma=round(sev_sigma, 1),
                evidence=diagnose(peak_hz), days_warning=days_warning,
                hours=running_hours, action=act)

board = pd.DataFrame([
    work_order("Pump P-104 motor",  7.4, 500.0, 12, 41_200),
    work_order("Fan F-201 bearing", 3.8, 812.0, 26, 18_600),
    work_order("Mixer M-3 coupling",2.1,  50.0, 40,  9_100),
    work_order("Pump P-107 motor",  0.6,  25.0, 60, 12_400),
]).set_index("machine")
board = board.loc[board.priority.map(
    {"URGENT": 0, "HIGH": 1, "MEDIUM": 2, "WATCH": 3}).sort_values().index]
board
""")

md(r"""
Read the board and notice what it is doing.

- **P-104** is ranked above F-201 despite both being clearly faulty, because 12 days of warning is less
  runway than 26. Severity alone does not order a work list; **severity against available notice** does.
- The `evidence` column is the part that makes it a work order rather than an alert. "20× — gear mesh"
  tells the planner to book a gearbox inspection and order a tooth-count-matched spare. "Anomaly score 7.4"
  tells them nothing they can act on.
- **P-107** is on the board with no action. That is deliberate: a monitor that only speaks when it is
  worried gives you no way to tell "healthy" from "offline".

And note what the board does **not** do: it never stops a machine. Every row ends in a recommendation an
engineer approves. That was fixed in Section 1 and holds all the way through.
""")

# ---------------------------------------------------------------- 23. dashboard
md(rf"""
## 23 · The reliability dashboard — the business case

**Maintenance activity.** A plant manager does not buy a model. They approve a spend against avoided
downtime.

**The challenge.** Condition-monitoring savings are easy to overstate. Three honest deductions that most
business cases quietly skip:

- Not every fault is caught in time, even by a good monitor.
- Not every warning is **acted on** — a warning nobody schedules saves nothing at all.
- False alarms cost real fitter-hours, and they must be subtracted, not ignored.

**The AI connection.** Convert detection rates into the plant's own units, and keep every assumption visible
as an argument you can change.

{link('dashboard', 'The reliability dashboard')}
""")

co(r"""
def business_case(machines=60, faults_per_machine_year=0.8,
                  detection_rate=None, acted_on=0.75,
                  breakdown=46_000.0, planned=1_200.0,
                  false_alarm_rate=None, fitter_hours=4.0, fitter_rate=65.0,
                  readings_per_machine_year=8760, persistence=2):
    "Everything here is arithmetic on the arguments. Change them and the case changes."
    detection_rate   = spec_hits_overall if detection_rate is None else detection_rate
    false_alarm_rate = fa_rate if false_alarm_rate is None else false_alarm_rate

    faults   = machines * faults_per_machine_year
    caught   = faults * detection_rate * acted_on
    avoided  = caught * (breakdown - planned)
    # A work order needs `persistence` consecutive readings over the threshold -- the same rule
    # Section 21 used. Without it, a 1.4% per-reading false-alarm rate on HOURLY data means
    # 123 investigations per machine per year and the whole case collapses.
    fa_count = machines * readings_per_machine_year * false_alarm_rate ** persistence
    fa_cost  = fa_count * fitter_hours * fitter_rate
    return dict(faults_per_year=faults, caught_and_acted_on=caught,
                downtime_avoided=avoided, false_alarms_per_year=fa_count,
                false_alarm_cost=fa_cost, net_benefit=avoided - fa_cost)

spec_hits_overall = float((se_te[yte == 1] > thr_s).mean())
fa_rate           = float((se_te[yte == 0] > thr_s).mean())
case = business_case()
for k, v in case.items():
    print(f"{k:24s} {v:12,.0f}")

p1 = business_case(persistence=1)
print(f"\nWithout the two-reading rule, the same {100*fa_rate:.1f}% per-reading false-alarm rate means")
print(f"{p1['false_alarms_per_year']:,.0f} investigations a year, and the net benefit falls from "
      f"{case['net_benefit']:,.0f} to {p1['net_benefit']:,.0f}")
print(f"— {case['net_benefit'] - p1['net_benefit']:,.0f} of value spent chasing noise"
      + (", and the case goes NEGATIVE." if p1["net_benefit"] < 0 else "."))
print("The alarm logic is not an afterthought. It is most of the engineering.")

fig, ax = plt.subplots(1, 2, figsize=(12, 4))
ax[0].bar(["downtime\navoided", "false-alarm\ncost", "net"],
          [case["downtime_avoided"], -case["false_alarm_cost"], case["net_benefit"]],
          color=[GREEN, RED, CYAN])
ax[0].axhline(0, color="k", lw=1); ax[0].set_ylabel("per year")
ax[0].set_title("the case, with the deductions shown")
sens = np.linspace(0.2, 1.0, 40)
ax[1].plot(sens, [business_case(acted_on=a)["net_benefit"] for a in sens], color=AMBER, lw=2)
ax[1].axhline(0, color="k", lw=1)
ax[1].set_xlabel("share of warnings actually acted on"); ax[1].set_ylabel("net benefit per year")
ax[1].set_title("the assumption the whole case rests on")
plt.tight_layout(); plt.show()

print("\nLook at the right-hand chart before quoting the left-hand one. The benefit is close to")
print("linear in the share of warnings that get scheduled -- an organisational number, not a")
print("technical one. A monitor with a 95% detection rate that nobody acts on is worth less than")
print("a monitor with a 60% detection rate that always gets a work order raised. The hardest part")
print("of this project was never the model.")
""")

# ---------------------------------------------------------------- 24. summary
md(rf"""
## 24 · Summary — the whole system

```
   8 NAMED CHANNELS  ──► clean ──► scale on HEALTHY ──► ISOLATION FOREST ──┐
   (rms, kurtosis, 1x, 2x, temp...)                     AUTOENCODER        │
                                                        severity           ├──► FUSION ──► WORK ORDER
   RAW 512-BIN SPECTRUM ──────────────────────────────► SPECTRUM AUTOENCODER┘     ranked      priority,
   (the data the 8 numbers were computed from)          what changed, and where   by notice   evidence,
                                                                                              days of warning
```

**What was built**

| Stage | Method | Output |
|---|---|---|
| Reduce a burst to eight numbers | Signal features | the clipboard columns |
| The traditional limit | 3σ control chart | catches the loud faults |
| Unusual combinations of features | Isolation Forest | anomaly score, no labels |
| Learn the shape of normal | Autoencoder | rebuild error |
| Find the fault nobody labelled | Autoencoder on the raw spectrum | rebuild error |
| Say what changed | Per-bin error spectrum | the frequency, and its shaft order |
| Place the alarm | Quantile of healthy validation error | threshold at a chosen false-alarm rate |
| Keep it honest over time | Drift monitoring, rolling retrain | it expires; it must be maintained |
| Quantify the value | Lead time to failure | days of warning |
| Combine everything | Fusion rules | one ranked work order |

**The four things worth remembering**

1. **Named features → Machine Learning.** The engineer names the features; the model finds odd combinations
   of them. Cheap, explainable, and correct for the faults those features were designed to see.
2. **Raw signals → Deep Learning.** Learn to rebuild normal, and anything unrebuildable is by definition
   new. The gear fault was found by a network that has never heard of gears.
3. **You cannot classify a fault you have never seen.** That is why this problem is anomaly detection and
   not classification, and it is the one idea to carry out of this notebook.
4. **Maintenance Engineer + AI.** The monitor watches every machine every hour and reports what it finds. A
   person still decides, still signs the permit, and still owns the outcome.

**And one that is specific to this problem:** the representation mattered more than the model. Swapping
Isolation Forest for a neural network on the same eight features changed almost nothing. Showing the *same*
autoencoder the raw spectrum instead changed everything. Before reaching for a bigger model, look at what
you are feeding it.

{link('start', 'The whole project map')}
""")

nb = new_notebook(cells=cells, metadata={
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"},
    "colab": {"provenance": []},
})
nbf.validate(nb)
with open("Unusual_Machine_Behaviour_DL.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"wrote Unusual_Machine_Behaviour_DL.ipynb  ({len(cells)} cells, "
      f"{sum(1 for c in cells if c.cell_type=='code')} code)")
