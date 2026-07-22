"""
Builds Bridge_Digital_Twin_DL.ipynb from nbformat cells.
Run:  python build_nb.py
The notebook is standalone (Colab): it does not import app.py/story.py/bridge.py.
It re-defines the structural physics and the synthetic crack images inline so the
notebook and the app agree.
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

cells = []
def md(t):  cells.append(new_markdown_cell(t.strip("\n")))
def co(t):  cells.append(new_code_cell(t.strip("\n")))

# ---------------------------------------------------------------- title
md(r"""
# AI-Based Bridge Digital Twin
### Teaching AI through the structural health monitoring of a highway bridge

This notebook is the runnable companion to the Bridge Digital Twin course. You are not learning AI for
its own sake — you are standing up a **digital twin** of a bridge, and each AI method appears because it
solves a real structural-health-monitoring problem one inspector cannot cover by hand.

**The framing throughout:** the inspector stays in charge and stays accountable. A model that sees only
numbers cannot tap a pier and hear it, judge whether a spall is cosmetic, or decide to close a lane. The
twin only eases the part one person cannot carry alone — watching every span, continuously, between
inspections that happen once every year or two. The twin *reports and forecasts*; the engineer *decides*.

**What we build, in the order a real project runs it:**

1. The bridge in service — the problem
2. One sensor sweep → data collection
3. Load the monitoring log
4. Data inspection (dropouts, stuck channels)
5. Data cleaning (median fill)
6. Normalization (one common scale)
7. Train / test split
8. ML baseline — Random Forest for the condition rating
9. Why ML cannot grade a raw crack image
10. Deep learning — from a neuron to a network
11. CNN on the crack image
12. Locating the crack — Grad-CAM
13. Training — the loss curves
14. Evaluation — the confusion matrix and the costly miss
15. Anomaly detection — normal for the weather
16. RUL forecast — how long until it needs work
17. Fusion — one prioritized alert
18. The predictive-maintenance dashboard — the business case
19. Summary — the whole digital twin
""")

md(r"""
## Setup

In Colab the libraries below are already installed. If you run this elsewhere, uncomment the install
line. We use `matplotlib` for plots to keep the notebook simple and portable. TensorFlow/Keras is used
for the CNN — the notebook detects whether it is present and skips the CNN training gracefully if not,
so every non-CNN cell runs anywhere.
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
                             accuracy_score, r2_score)

np.random.seed(42)
plt.rcParams["figure.figsize"] = (8, 4)

# The course palette (same hex the app uses)
CYAN, AMBER, GREEN, RED, MUTED = "#4fc3f7", "#ffb74d", "#66bb6a", "#ef5350", "#8b949e"
print("Environment ready.")
""")

# ---------------------------------------------------------------- 1. the bridge in service
md(r"""
## 1 · The bridge in service — the problem

**Structural activity.** A highway bridge carries tens of thousands of vehicles a day. Every crossing
adds a stress cycle; wind, heat, frost, moisture and de-icing salt work on it around the clock. It cannot
be closed whenever an engineer wants a look, so it is inspected by eye once every one or two years.

**The challenge.** Deterioration is continuous; inspection is not. Between two visits, micro-cracks grow,
reinforcement corrodes, fatigue accumulates and bearings wear. A bridge can pass a visual inspection
while hidden damage keeps progressing — and by the time it is visible the repair is expensive, or the
bridge closes.

**The AI connection.** The bridge does not need its inspectors replaced. It needs the *gap between
inspections* covered — the structure watched continuously and its future condition estimated before
damage is visible. That continuous watch, impossible to keep by eye, is the only reason AI belongs here.
""")

co(r"""
# The deterioration curve: condition falls continuously, the eye only checks every year or two.
FREQ0     = 3.30    # Hz - healthy natural frequency of the deck
INTERVENE = 55.0    # condition rating below which a component needs work
D_FAIL    = 1.0 - INTERVENE / 100.0   # latent damage at the intervention line (0.45)

def _condition(damage):
    "Health index 0..100 from latent damage 0..1 (higher rating = healthier)."
    return np.clip(100.0 * (1.0 - damage), 0, 100)

months = 96                                   # 8 years
t = np.arange(months)
damage_t = np.clip(0.010 * t + 0.00055 * t**2, 0, 1.2)   # slow drift that accelerates
cond_t = _condition(damage_t)
onset = int(np.argmax(cond_t < INTERVENE))    # month the condition crosses the line

interval = 24                                 # inspected every 2 years
insp = np.arange(0, months, interval)
seen = insp[insp >= onset]
detected = int(seen[0]) if len(seen) else months

plt.figure(figsize=(9, 4))
plt.plot(t, cond_t, color=CYAN, lw=2.5, label="true condition")
plt.axhline(INTERVENE, color=RED, ls="--", label="intervention level")
plt.scatter(insp, cond_t[np.clip(insp, 0, months-1)], color=AMBER, marker="v",
            s=90, zorder=5, label="visual inspection")
plt.axvspan(onset, detected, color=RED, alpha=0.12)
plt.text((onset+detected)/2, INTERVENE-12, "damage present,\nunseen", color=RED,
         ha="center", fontsize=9)
plt.title("Condition over 8 years, with inspections marked")
plt.xlabel("month"); plt.ylabel("condition rating (100 = healthy)")
plt.legend(); plt.tight_layout(); plt.show()

print(f"Damage crosses the line in month {onset}.")
print(f"The next inspection is not until month {detected}, so it hides for {detected-onset} months.")
print("Halving the interval doubles inspection cost and STILL misses damage that appears the day after")
print("a visit. The calendar cannot track a process that never pauses.")
""")

# ---------------------------------------------------------------- 2. one sensor sweep
md(r"""
## 2 · One sensor sweep → data collection

**Structural activity.** At one instant the system reads every channel at once: the deck's natural
frequency from the accelerometers, strain in a girder, vibration, tilt at a pier, the width of a
monitored crack, corrosion in the rebar, the temperature, and the weight of traffic crossing. Together
they describe the bridge right then, and we record the component's **condition rating** with them.

**The challenge.** Whoever reads that record later was not on the bridge. They get a row of numbers. A
frozen accelerometer or a mislabelled strain channel means a wrong picture of a sound bridge — or a sound
picture of a failing one.

**The AI connection.** For a model that limitation is absolute. It never stands on the deck. One row —
readings plus the condition at that moment — is all it gets. The record *is* the bridge, as far as the
model is concerned.

The eight named channels we monitor on every sweep:

| Channel | Sensor | Unit | What it tells you |
|---|---|---|---|
| Natural frequency | accelerometers | Hz | **Drops** as stiffness is lost — the key early sign |
| Strain | strain gauges | µε | Rises under load as a section weakens |
| Vibration RMS | accelerometers | m/s² | Grows with damage and heavy traffic |
| Tilt | inclinometers | ° | Settlement and rotation at piers |
| Crack width | crack sensors | mm | Direct opening of a monitored crack |
| Corrosion | corrosion probes | % | Section loss in the reinforcement |
| Temperature | weather station | °C | Shifts frequency — must be separated from damage |
| Traffic load | weigh-in-motion | t | The live load crossing at that moment |

Notice the physics: **frequency falls** with damage (and shifts with temperature); everything else
**rises**. The same function drives the synthetic dataset below, so the data and the app agree.
""")

co(r"""
# ---- The structural physics (identical to the app's _sensors_for) ----------
FEATURES = ["nat_freq_hz", "strain_ue", "accel_rms", "tilt_deg",
            "crack_width_mm", "corrosion_pct", "temperature_c", "traffic_load_t"]
NICE = ["Frequency (Hz)", "Strain (ue)", "Vibration (m/s2)", "Tilt (deg)",
        "Crack (mm)", "Corrosion (%)", "Temp (C)", "Load (t)"]

def _sensors_for(damage, temp, load):
    "Build the 8-channel row(s) the models expect, from latent damage and the environment (noise-free)."
    freq   = FREQ0 * (1 - 0.30 * damage) - 0.015 * (temp - 20.0)   # stiffness + thermal
    strain = 90.0 + 480.0 * damage + 5.5 * load                    # ue
    accel  = 0.12 + 1.15 * damage + 0.018 * load                   # m/s^2 RMS
    tilt   = 0.02 + 0.85 * damage                                  # degrees
    crack  = 0.05 + 2.6 * damage                                   # mm
    corr   = 1.5 + 47.0 * damage                                   # %
    return np.stack([freq, strain, accel, tilt, crack, corr, temp, load], axis=-1)

def generate_truth(N=1500, seed=42):
    "One sweep = one row: 8 readings + the condition rating + a needs-intervention label."
    rng = np.random.default_rng(seed)
    damage = rng.uniform(0.0, 0.9, N)
    temp   = rng.uniform(2.0, 38.0, N)
    load   = rng.uniform(3.0, 40.0, N)
    base = _sensors_for(damage, temp, load)
    freq   = base[:, 0] + rng.normal(0, 0.03, N)
    strain = np.abs(base[:, 1] + rng.normal(0, 12, N))
    accel  = np.abs(base[:, 2] + rng.normal(0, 0.06, N))
    tilt   = np.abs(base[:, 3] + rng.normal(0, 0.03, N))
    crack  = np.abs(base[:, 4] + rng.normal(0, 0.12, N))
    corr   = np.clip(base[:, 5] + rng.normal(0, 2.0, N), 0, None)
    cond    = _condition(damage)
    damaged = (cond < INTERVENE).astype(int)      # 1 = needs intervention
    return pd.DataFrame({
        "sweep_id": np.arange(1, N + 1),
        "nat_freq_hz": freq.round(3), "strain_ue": strain.round(0),
        "accel_rms": accel.round(3), "tilt_deg": tilt.round(3),
        "crack_width_mm": crack.round(2), "corrosion_pct": corr.round(1),
        "temperature_c": temp.round(1), "traffic_load_t": load.round(1),
        "condition": cond.round(1), "damaged": damaged,
    })

truth = generate_truth()
print("One bridge, one moment = one row:")
truth.head()
""")

co(r"""
print("Sweeps:", len(truth), "| Columns:", truth.shape[1])
print("Needs-intervention rate: {:.1%}".format(truth.damaged.mean()))
print("Condition range: {:.0f} .. {:.0f}".format(truth.condition.min(), truth.condition.max()))
""")

# ---------------------------------------------------------------- 3. load
md(r"""
## 3 · Load the monitoring log

**Structural activity.** The monitoring system has logged the bridge every few minutes for months. Before
anything is built on it, open the export and check it against what was installed: how many sweeps, all the
sensors present, each column the type it should be.

**The challenge.** A real export is messy — a knocked cable leaves a gap, a debonded gauge saturates, a
duplicate sweep is double-logged. We create a realistically *dirty* copy so the cleaning steps have
something to do. A model trained on the wrong data does not error; it trains without complaint and gives
wrong answers.
""")

co(r"""
def make_dirty(df, seed=42):
    rng = np.random.default_rng(seed)
    N = len(df)
    dirty = df.copy()
    # random dropouts (a knocked cable leaves a gap)
    for col in ["nat_freq_hz", "strain_ue", "accel_rms", "tilt_deg",
                "crack_width_mm", "corrosion_pct", "temperature_c"]:
        dirty.loc[rng.choice(N, int(0.06 * N), replace=False), col] = np.nan
    # impossible / stuck values from faulty sensors
    dirty.loc[rng.choice(N, 13, replace=False), "strain_ue"]     = 9999   # saturated gauge
    dirty.loc[rng.choice(N, 10, replace=False), "temperature_c"] = 999    # thermocouple fault
    dirty.loc[rng.choice(N, 12, replace=False), "accel_rms"]     = 0.0    # dead accelerometer
    dirty.loc[rng.choice(N, 11, replace=False), "nat_freq_hz"]   = 0.0    # frozen frequency channel
    # duplicate records (double-logged)
    dirty = pd.concat([dirty, dirty.sample(20, random_state=4)], ignore_index=True)
    return dirty

dirty = make_dirty(truth)
print("Sweeps in the raw export:", len(dirty), "| Sensor channels:", len(FEATURES))
dirty.head(8)
""")

# ---------------------------------------------------------------- 4. inspection
md(r"""
## 4 · Data inspection — dropouts and stuck channels

**Structural activity.** Inspect the log the way you inspect the instruments. A cable knocked loose leaves
a gap; a strain gauge that debonded reads a flat maximum; an accelerometer that came unstuck reads a
frozen zero.

**The challenge.** You cannot eyeball months of sweeps the way you check one gauge on site. A channel that
dropped out for a week leaves a hole that looks like nothing; a stuck sensor looks perfectly reasonable.
The fault is invisible at this scale.

**The AI connection.** So inspect with counts and distributions instead of eyes. Count missing readings
per channel and the failed sensor announces itself; plot each column's spread and the stuck one spikes.
Diagnosis only — nothing is repaired yet.
""")

co(r"""
print("Missing readings per channel:")
print(dirty[FEATURES].isna().sum())
""")

co(r"""
fig, axes = plt.subplots(1, 3, figsize=(12, 3.2))
for ax, col in zip(axes, ["nat_freq_hz", "strain_ue", "temperature_c"]):
    ax.hist(dirty[col].dropna(), bins=50, color=CYAN)
    ax.set_title(col)
axes[1].annotate("saturation spike\n(9999 ue)", xy=(9999, 1), color=RED, fontsize=8)
plt.suptitle("Values far from the pack are sensor faults, not bridge states")
plt.tight_layout(); plt.show()
print("A saturated strain gauge (9999 ue), a faulted thermocouple (999 C), a dead accelerometer (0 m/s2)")
print("and a frozen frequency channel (0 Hz) all announce themselves here.")
""")

# ---------------------------------------------------------------- 5. cleaning
md(r"""
## 5 · Data cleaning

**Structural activity.** Act on the diagnosis. A strain of 9,999 µε is a saturated gauge and comes out. A
natural frequency of zero on a bridge under traffic is a dead accelerometer, not a still structure. A
sweep logged twice is struck off.

**The challenge — a judgement call.** Drop every flawed sweep and a slow degradation trend loses its
history. Keep everything and a dead-gauge zero teaches the model that a loaded girder can read no strain.
No rule decides it for you.

**The AI connection.** We drop duplicates, turn impossible values into gaps, then fill the gaps with the
channel's **median**. Why the median, not the mean? The mean is dragged by a 9,999 µε saturation spike;
the median — the middle value — barely notices it, so the filled-in reading stays realistic.
""")

co(r"""
def clean_log(dirty):
    clean = dirty.drop_duplicates().copy()
    clean.loc[clean.strain_ue    > 5000, "strain_ue"]     = np.nan   # impossible -> gap
    clean.loc[clean.temperature_c > 200, "temperature_c"] = np.nan
    clean.loc[clean.accel_rms   <= 0,    "accel_rms"]     = np.nan
    clean.loc[clean.nat_freq_hz <= 0.5,  "nat_freq_hz"]   = np.nan
    for col in FEATURES:
        clean[col] = clean[col].fillna(clean[col].median())          # median fill
    return clean

clean = clean_log(dirty)
print("Sweeps before:", len(dirty), "-> after:", len(clean),
      "| Missing after:", int(clean[FEATURES].isna().sum().sum()))

# The mean vs median argument, made concrete on the strain channel:
raw_strain = dirty["strain_ue"]
print(f"\nstrain_ue  mean of raw (with 9999 spikes): {raw_strain.mean():8.1f} ue")
print(f"strain_ue  median of raw                  : {raw_strain.median():8.1f} ue  <- the fill value")
""")

# ---------------------------------------------------------------- 6. normalization
md(r"""
## 6 · Normalization

**Structural activity.** Every channel reports in its own unit — hertz, microstrain, m/s², degrees, mm,
percent, °C, tonnes. Put them all on one common scale before comparing them.

**The challenge.** Raw magnitudes lie about importance. Strain runs into the hundreds; frequency sits near
three. Side by side, strain looks a hundred times more significant because of a unit — when a **0.2 Hz
drop** in natural frequency is the strongest early sign of lost stiffness.

**The AI connection.** A neural network sees magnitude, not meaning. `MinMaxScaler` puts every channel on
0–1, so importance is learned from the data, not from the unit. The fitted scaler ships with the model.
""")

co(r"""
scaler = MinMaxScaler()
norm = clean.copy()
norm[FEATURES] = scaler.fit_transform(clean[FEATURES])
norm[FEATURES].describe().loc[["min", "max"]].round(3)
""")

# ---------------------------------------------------------------- 7. split
md(r"""
## 7 · Train / test split

**Structural activity.** No engineer signs off a condition model using the very sweeps it was tuned on.
Tuning happens on known sweeps whose true condition is recorded; acceptance is proven on sweeps the model
has not seen.

**The challenge.** A model checked on the sweeps it trained on just repeats what it memorised — it scores
brilliantly and proves nothing about the bridge's next reading.

**The AI connection.** Split the sweeps: train, validation, and a sealed test set opened only at the
safety audit. Only a score on unseen sweeps says anything about the bridge tomorrow. We stratify on the
damage label so the intervention rate stays balanced across all three splits.
""")

co(r"""
X    = norm[FEATURES].values
ydmg = norm["damaged"].values          # classification target: needs intervention?
ycon = clean["condition"].values       # regression target: 0..100 condition rating

idx = np.arange(len(X))
itr, itmp = train_test_split(idx, test_size=0.30, random_state=42, stratify=ydmg)
ival, ite = train_test_split(itmp, test_size=0.50, random_state=42, stratify=ydmg[itmp])

Xtr, Xval, Xte = X[itr], X[ival], X[ite]
ytr, yval, yte = ydmg[itr], ydmg[ival], ydmg[ite]
ConTr, ConTe   = ycon[itr], ycon[ite]
print(f"Train {len(ytr)}  |  Validation {len(yval)}  |  Test (sealed) {len(yte)}")
""")

# ---------------------------------------------------------------- 8. ml baseline
md(r"""
## 8 · ML baseline — Random Forest on the named readings

**Structural activity.** Every experienced bridge engineer carries a model in their head: a dropping
natural frequency means lost stiffness, rising strain under the same load means a weakening section,
growing tilt means settlement. It is not written down and not consistent between two engineers.

**The challenge.** Write it down and you cannot. Condition falls as frequency drops — but by how much, and
how much worse when corrosion is also high? It is many weighted interactions the engineer cannot fully
articulate.

**The AI connection.** This is the job machine learning does well. You do not state the equations — you
state the factors, which an engineer already named at inspection. Given eight columns and 1,500 outcomes,
the **Random Forest** works out the mapping to a condition rating itself. We also train a damaged/sound
**classifier** on the same readings, which the safety audit later grades.
""")

co(r"""
# Regressor: estimate the 0..100 condition rating from the eight readings.
con = RandomForestRegressor(n_estimators=200, random_state=42).fit(Xtr, ConTr)
pred_con = con.predict(Xte)
print("Condition R2 on sealed test sweeps: {:.2f}".format(r2_score(ConTe, pred_con)))

# Classifier: needs-intervention or sound (used at the safety audit).
rf = RandomForestClassifier(n_estimators=200, random_state=42).fit(Xtr, ytr)
print("Damaged/sound accuracy on sealed test sweeps: {:.1%}".format(rf.score(Xte, yte)))

imp = pd.Series(con.feature_importances_, index=NICE).sort_values()
imp.plot.barh(color=CYAN)
plt.title("What the model learned to weigh (you never set these)")
plt.tight_layout(); plt.show()
print("Frequency, crack width and corrosion dominate - exactly what an engineer would tell you, but here")
print("it was learned from 1,500 sweeps, not stated as a rule.")
""")

co(r"""
# Predicted vs recorded condition on the sealed sweeps.
plt.figure(figsize=(5.2, 5))
plt.scatter(ConTe, pred_con, s=14, color=CYAN, alpha=0.55, edgecolors="none")
plt.plot([0, 100], [0, 100], ls="--", color=MUTED)
plt.xlabel("recorded condition"); plt.ylabel("predicted condition")
plt.title("Predicted vs recorded condition (sealed sweeps)")
plt.tight_layout(); plt.show()
""")

# ---------------------------------------------------------------- 9. why ML can't grade an image
md(r"""
## 9 · Why ML cannot grade a raw crack image

**Structural activity.** Look at a photo of a concrete soffit and you know. A sound surface is an even
grey; a defect shows a dark hairline, a map-cracked patch, a rust stain. An experienced inspector grades
it at a glance, without ever explaining how.

**The challenge.** The Random Forest needs named columns. A drone image is a grid of **thousands of
unnamed pixels** — not one of them is "crack". The standard shortcut, reduce the image to one number
(average brightness) and set a threshold, throws away the pattern where the crack actually lives.

**The AI connection.** We show below that a single brightness threshold cannot separate a *hairline* crack
from a harmless *wet patch*: the hairline barely moves the average, while the wet patch drags it right
down. Every hand-made image feature is a rule you must maintain, and each discards most of the picture.
""")

co(r"""
# Synthetic concrete surfaces as a brightness grid (same physics as the app's make_crack).
# Means are kept similar between sound and hairline so brightness alone cannot grade it.
def make_crack(kind="sound", size=64, seed=0):
    rng = np.random.default_rng(seed)
    Y, X = np.mgrid[0:size, 0:size]
    img = 0.62 + rng.normal(0, 0.05, (size, size))          # grey concrete + speckle
    img += 0.03 * np.sin(2 * np.pi * X / 21.0)              # faint form-work shading

    def draw_line(img, x0, drift, width, depth):
        col = x0 + drift * (Y - size / 2)
        band = np.exp(-((X - col) ** 2) / (2 * width ** 2))
        return img - depth * band

    if kind == "hairline":
        img = draw_line(img, 30, 0.25, 0.9, 0.42)          # one thin, low-contrast dark line
    elif kind == "map":
        img = draw_line(img, 22, 0.40, 1.1, 0.40)          # a branching network of lines
        img = draw_line(img, 40, -0.30, 1.0, 0.38)
        img = draw_line(img, 32, 0.10, 0.8, 0.30)
    elif kind == "wet":
        cy, cx = 34, 30                                    # a darker but UNDAMAGED patch
        img -= 0.16 * np.exp(-(((Y - cy) ** 2 + (X - cx) ** 2) / (2 * 20.0 ** 2)))
    return np.clip(img, 0, 1)

fig, axes = plt.subplots(1, 3, figsize=(11, 3.6))
for ax, kind in zip(axes, ["sound", "hairline", "map"]):
    ax.imshow(make_crack(kind), cmap="gray", vmin=0, vmax=1)
    ax.set_title(kind); ax.axis("off")
plt.suptitle("One surface = 64 x 64 = 4,096 unnamed pixel values. None of them is labelled 'crack'.")
plt.tight_layout(); plt.show()
""")

co(r"""
# The hand-made rulebook: reduce each image to its average brightness and set one threshold.
cases = {
    "Sound surface":            (make_crack("sound",    seed=1), "sound"),
    "Sound (wet patch)":        (make_crack("wet",      seed=2), "sound"),
    "Hairline crack (defect)":  (make_crack("hairline", seed=3), "defect"),
    "Map-cracking (defect)":    (make_crack("map",      seed=4), "defect"),
}
threshold = 0.58
print(f"Flag any image darker than average brightness {threshold}:\n")
missed, false_alarm = [], []
for name, (img, truth_lbl) in cases.items():
    b = float(img.mean())
    verdict = "FLAG (defect)" if b < threshold else "ok (sound)"
    print(f"{name:26s} brightness={b:4.2f}  ->  {verdict}")
    if truth_lbl == "defect" and b >= threshold: missed.append(name)
    if truth_lbl == "sound"  and b <  threshold: false_alarm.append(name)
print(f"\nDefects missed : {missed or 'none'}")
print(f"Sound flagged  : {false_alarm or 'none'}")
print("A hairline barely moves the average brightness (one thin line among thousands of grey pixels),")
print("while a harmless wet patch drags it down. One number throws away the pattern that separates them.")
""")

# ---------------------------------------------------------------- 10. DL intro
md(r"""
## 10 · Deep learning — from a neuron to a network

Deep learning changes the question. Instead of *you* writing the rule, you supply labelled examples and
the network learns the features that separate them.

- **A neuron** weighs each input, sums them, adds a bias, and passes the result through an activation
  function: `output = activation(w·x + b)`. That is exactly how an inspector weighs signals into one call
  — a dropping frequency matters a lot, a warm afternoon barely matters — and the weights are what
  experience becomes.
- **A network** stacks neurons in layers. One neuron draws a straight line; layers bend the boundary
  around real damage patterns (low frequency *and* high strain means one thing; low frequency alone in
  the cold means another). **Training** sets the weights by the learning loop: predict → measure error →
  adjust → repeat.

We first confirm a small neural net matches the Random Forest on the named readings — deep learning does
**not** beat ML here. Its value comes next, on the raw crack image ML cannot read.
""")

co(r"""
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")     # silence convergence chatter for the demo
    ann = MLPRegressor(hidden_layer_sizes=(16, 8), max_iter=1200, random_state=0).fit(Xtr, ConTr)

r_rf  = r2_score(ConTe, con.predict(Xte))
r_ann = r2_score(ConTe, ann.predict(Xte))
print("Random Forest - condition R2 : {:.2f}".format(r_rf))
print("Neural net    - condition R2 : {:.2f}".format(r_ann))
print("\nOn the eight NAMED readings, ML and DL estimate condition about equally well - because the")
print("engineer already named the factors. Named features -> reach for the simpler, more defensible tool.")
""")

# ---------------------------------------------------------------- 11. CNN
md(r"""
## 11 · CNN on the crack image

**Structural activity.** An inspector does not read 4,096 pixels — they look for *features*: the thin dark
line of a crack, the branching of map-cracking, wherever it appears on the surface.

**The AI connection.** A **2-D convolutional neural network** slides small learned filters across the
image; each fires on a pattern wherever it occurs. Early filters find simple edges, later layers combine
them into a crack signature. The features are *learned* from labelled images — the detector the hand-made
threshold could not be.

We build a small labelled set of synthetic crack vs sound surfaces and train a small `Conv2D`. The cell
is guarded by a `KERAS` flag: it runs fully in Colab and skips cleanly where TensorFlow is absent.
""")

co(r"""
# Build a labelled image dataset: sound vs cracked surfaces at varied severity.
def build_image_dataset(n_per_class=200, size=64):
    Xs, ys = [], []
    for k in range(n_per_class):
        # sound: even grey, plus some harmless wet patches so brightness alone won't separate it
        kind = "sound" if k % 4 else "wet"
        Xs.append(make_crack(kind, size=size, seed=1000 + k)); ys.append(0)
        # cracked: hairline or map-cracking
        kind = "hairline" if k % 2 else "map"
        Xs.append(make_crack(kind, size=size, seed=5000 + k)); ys.append(1)
    Ximg = np.array(Xs)[..., np.newaxis].astype("float32")   # (samples, 64, 64, 1)
    yimg = np.array(ys).astype("float32")
    # per-image standardisation keeps overall brightness out of it, so SHAPE does the work
    Ximg = (Ximg - Ximg.mean(axis=(1, 2), keepdims=True)) / (Ximg.std(axis=(1, 2), keepdims=True) + 1e-6)
    return Ximg, yimg

Ximg, yimg = build_image_dataset()
Xi_tr, Xi_te, yi_tr, yi_te = train_test_split(Ximg, yimg, test_size=0.25,
                                              random_state=0, stratify=yimg)
print("Image dataset:", Ximg.shape, "| train", len(yi_tr), "test", len(yi_te))
""")

co(r"""
try:
    import tensorflow as tf
    from tensorflow.keras import layers, models
    KERAS = True
except Exception as e:
    KERAS = False
    print("TensorFlow/Keras not available here:", e)
    print("This cell runs as-is in Google Colab. Skipping CNN training locally.")
""")

co(r"""
if KERAS:
    tf.random.set_seed(0)
    cnn = models.Sequential([
        layers.Input(shape=(64, 64, 1)),
        layers.Conv2D(8,  (3, 3), activation="relu"),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(16, (3, 3), activation="relu"),
        layers.MaxPooling2D((2, 2)),
        layers.Conv2D(16, (3, 3), activation="relu"),
        layers.GlobalAveragePooling2D(),
        layers.Dense(16, activation="relu"),
        layers.Dense(1,  activation="sigmoid"),
    ])
    cnn.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    cnn.summary()
    hist_cnn = cnn.fit(Xi_tr, yi_tr, validation_split=0.2, epochs=10, batch_size=32, verbose=1)
    acc = cnn.evaluate(Xi_te, yi_te, verbose=0)[1]
    print(f"\nCNN accuracy on unseen surfaces: {acc:.1%}")
    print("The CNN reads the raw image the Random Forest could not touch.")
else:
    print("CNN skipped (no TensorFlow). Run this notebook in Colab to train it.")
""")

# ---------------------------------------------------------------- 12. Grad-CAM
md(r"""
## 12 · Locating the crack — Grad-CAM

**Structural activity.** Point the drone at a whole deck soffit. Most of it is sound; somewhere a crack
runs across it. The inspector's job is not only to say a defect exists but to mark exactly **where**, so
the repair crew and the next report can find it.

**The challenge.** A flat cracked/sound answer is not enough — an engineer will not act on a black box.

**The AI connection.** **Grad-CAM** highlights the pixels that drove the call, so the heat lands on the
crack itself. Below we render a cracked deck region and its heat-map: the illustration always runs
(numpy), and if TensorFlow is present we compute a *real* Grad-CAM from the trained CNN's last conv layer.
The engineer sees the verdict *and* the evidence, marks the location, and can overrule it.
""")

co(r"""
# A deck-soffit region with a diagonal crack, and a heat map along the crack (same as make_deck).
def make_deck(cracked=True, size=72, seed=1):
    rng = np.random.default_rng(seed)
    Y, X = np.mgrid[0:size, 0:size]
    img = 0.62 + rng.normal(0, 0.045, (size, size))
    img += 0.025 * np.sin(2 * np.pi * Y / 26.0)
    cam = np.full((size, size), 0.06)
    if cracked:
        path_x = 0.7 * Y + 10 + 4.0 * np.sin(Y / 8.0)          # a diagonal, meandering crack
        band = np.exp(-((X - path_x) ** 2) / (2 * 1.3 ** 2))
        img = img - 0.42 * band
        cam = 0.06 + 0.94 * np.exp(-((X - path_x) ** 2) / (2 * 4.0 ** 2))
    return np.clip(img, 0, 1), cam

deck_img, deck_cam = make_deck(cracked=True)

fig, ax = plt.subplots(1, 2, figsize=(9, 4))
ax[0].imshow(deck_img, cmap="gray", vmin=0, vmax=1)
ax[0].set_title("deck-soffit image (what the drone sees)"); ax[0].axis("off")
ax[1].imshow(deck_img, cmap="gray", vmin=0, vmax=1)
ax[1].imshow(deck_cam, cmap="inferno", alpha=0.55)
ax[1].set_title("Grad-CAM - where the CNN looked"); ax[1].axis("off")
plt.tight_layout(); plt.show()
print("The heat lands on the crack itself: the verdict comes with its evidence.")
""")

co(r"""
# A real Grad-CAM from the trained CNN, when TensorFlow is present.
if KERAS:
    # take one cracked test image the CNN has not seen
    sample = Xi_te[np.argmax(yi_te == 1)][np.newaxis, ...]
    last_conv = [l for l in cnn.layers if isinstance(l, layers.Conv2D)][-1]
    grad_model = models.Model(cnn.inputs, [last_conv.output, cnn.output])
    with tf.GradientTape() as tape:
        conv_out, pred = grad_model(sample)
        loss = pred[:, 0]
    grads = tape.gradient(loss, conv_out)[0]
    weights = tf.reduce_mean(grads, axis=(0, 1))
    heat = tf.reduce_sum(conv_out[0] * weights, axis=-1).numpy()
    heat = np.maximum(heat, 0)
    heat = heat / (heat.max() + 1e-9)
    fig, ax = plt.subplots(1, 2, figsize=(9, 4))
    ax[0].imshow(sample[0, :, :, 0], cmap="gray"); ax[0].set_title("CNN input (cracked)"); ax[0].axis("off")
    ax[1].imshow(sample[0, :, :, 0], cmap="gray")
    ax[1].imshow(np.kron(heat, np.ones((64 // heat.shape[0], 64 // heat.shape[1]))),
                 cmap="inferno", alpha=0.55)
    ax[1].set_title(f"real Grad-CAM (p_crack={float(pred[0,0]):.2f})"); ax[1].axis("off")
    plt.tight_layout(); plt.show()
else:
    print("Real Grad-CAM skipped (no TensorFlow). The synthetic heat map above illustrates the idea.")
""")

# ---------------------------------------------------------------- 13. training / loss curves
md(r"""
## 13 · Training — watching the loss fall

**The learning loop, run thousands of times:** the model predicts, compares to the recorded condition, and
nudges every weight to be a little less wrong. The **loss** measures how wrong it is.

The loss falls fast, then flattens. More epochs on the same sweeps only memorise them, so you stop when
the held-out (validation) loss stops improving — that is early stopping. If TensorFlow is present we plot
the CNN's Keras history; otherwise the sklearn ANN exposes the same idea via its `loss_curve_`.
""")

co(r"""
if KERAS:
    plt.figure(figsize=(7, 3.6))
    plt.plot(hist_cnn.history["loss"],     label="train",      color=CYAN)
    plt.plot(hist_cnn.history["val_loss"], label="validation", color=AMBER)
    plt.title("CNN training loss"); plt.xlabel("epoch"); plt.ylabel("loss")
    plt.legend(); plt.tight_layout(); plt.show()
else:
    # sklearn ANN exposes a loss curve too - same idea, no TensorFlow needed
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ann_clf = MLPClassifier(hidden_layer_sizes=(12, 6), max_iter=400,
                                random_state=0).fit(Xtr, ytr)
    plt.figure(figsize=(7, 3.6))
    plt.plot(ann_clf.loss_curve_, color=CYAN)
    plt.title("Neural-net training loss (sklearn ANN)")
    plt.xlabel("epoch"); plt.ylabel("loss")
    plt.tight_layout(); plt.show()
    print("The loss falls fast, then flattens - more epochs on the same sweeps only memorise them.")
""")

# ---------------------------------------------------------------- 14. evaluation
md(r"""
## 14 · Evaluation — the confusion matrix

**Structural activity.** Audit the model the way you would audit a batch of inspection reports against
reality. The model made a call on each sealed sweep — sound, or needs intervention. Line them up and count.

**The challenge.** Four outcomes, and lumping them together hides the one that matters:

- Called sound, was sound — fine
- Called damaged, was damaged — caught it
- Called damaged, was actually sound — a false alarm, a wasted inspection
- **Called sound, and it was damaged — the costly miss: damage left on the bridge**

**The AI connection.** Never quote accuracy alone. A model that calls everything sound scores well on
accuracy and misses every real defect. The bottom-left box is what the whole system exists to prevent.
""")

co(r"""
pred = rf.predict(Xte)
cm = confusion_matrix(yte, pred)
tn, fp, fn, tp = cm.ravel()

ConfusionMatrixDisplay(cm, display_labels=["sound", "damaged"]).plot(cmap="Blues", colorbar=False)
plt.title("Safety audit on the sealed test sweeps"); plt.show()

print(f"Overall accuracy         : {accuracy_score(yte, pred):.1%}")
print(f"Damage called sound (FN) : {fn}   <- the costly box: damage left on the bridge")
print(f"False alarms        (FP) : {fp}   <- wasted inspections")
""")

# ---------------------------------------------------------------- 15. anomaly detection
md(r"""
## 15 · Anomaly detection — normal for the weather

**Structural activity.** A bridge's natural frequency is not constant. It rises in the cold and falls in
the heat as the concrete's stiffness changes. A raw frequency alarm would fire every summer afternoon —
most change is normal, seasonal, expected behaviour.

**The challenge.** So a fixed threshold is useless: set it low and the weather trips it daily; set it high
and real stiffness loss hides inside the seasonal swing. The damage signal is a small drop the temperature
does not explain, buried in a large one it does.

**The AI connection.** The twin learns the **normal** frequency-for-temperature from history with a
`LinearRegression`, then predicts the frequency it expects for today's weather. The **residual** (observed
− expected) sits near zero while the bridge behaves normally, and spikes the moment stiffness drops for a
reason the weather cannot account for. That is anomaly detection — the early-warning branch of the twin.
""")

co(r"""
rng = np.random.default_rng(7)
# 1) learn "normal" from a clean year of history: frequency depends on temperature
t_tr = rng.uniform(2, 38, 400)
f_tr = FREQ0 - 0.015 * (t_tr - 20) + rng.normal(0, 0.02, 400)
lin = LinearRegression().fit(t_tr[:, None], f_tr)

# 2) a synthetic time series with a seasonal temperature swing + an injected stiffness-loss event
months_a = 120
tm = np.arange(months_a)
temp = 20 + 12 * np.sin(2 * np.pi * tm / 12.0) + rng.normal(0, 1.0, months_a)   # seasonal
freq_obs = FREQ0 - 0.015 * (temp - 20) + rng.normal(0, 0.02, months_a)          # normal behaviour
onset_a = 84
freq_obs = freq_obs - np.clip((tm - onset_a) * 0.004, 0, None)                   # slow unexplained loss

# 3) score the residual against what temperature predicts
expected = lin.predict(temp[:, None])
resid = freq_obs - expected
thr = 0.05
alarm = np.where(resid < -thr)[0]

fig, ax = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
ax[0].plot(tm, freq_obs, color=CYAN, marker="o", ms=3, label="observed frequency")
ax[0].plot(tm, expected, color=MUTED, ls="--", label="expected for the weather")
ax[0].set_ylabel("natural frequency (Hz)"); ax[0].legend()
ax[0].set_title("Observed frequency vs what the temperature predicts")
colr = np.where(resid < -thr, RED, CYAN)
ax[1].bar(tm, resid, color=colr)
ax[1].axhline(-thr, color=RED, ls="--", label="alarm threshold")
ax[1].set_xlabel("month"); ax[1].set_ylabel("residual (Hz)"); ax[1].legend()
ax[1].set_title("Residual = observed - expected (near zero when normal)")
plt.tight_layout(); plt.show()

if len(alarm):
    print(f"Anomaly first flagged in month {int(alarm[0])} (the stiffness loss began at month {onset_a}).")
    print("The raw frequency never left its seasonal band, so a fixed alarm would have stayed silent.")
    print("The RESIDUAL - what temperature cannot explain - is what crosses the line.")
""")

# ---------------------------------------------------------------- 16. RUL forecast
md(r"""
## 16 · RUL forecast — how long until it needs work

**Structural activity.** The condition rating of a component does not jump — it drifts down over months and
years as fatigue, corrosion and load accumulate. Under the noise there is a trend, heading toward the
level at which the agency must intervene.

**The challenge.** Reactive maintenance waits for the rating to cross the line, then scrambles;
schedule-based maintenance repairs on a fixed calendar whether it is needed or not. Neither answers the
question an asset manager actually asks: **how many months until this component needs work?**

**The AI connection.** Fit the degradation trend to the monitored history with `np.polyfit`, extrapolate
it to the intervention line, and read off where it crosses. The gap from today is the **Remaining Useful
Life**. Now maintenance is planned before the damage is visible — the whole point of predictive SHM.
""")

co(r"""
rng = np.random.default_rng(3)
horizon = 120
rate = 0.009
obs = 30                      # months of monitored history we have so far

tm = np.arange(horizon)
damage = np.clip(rate * tm + 0.00006 * tm ** 2, 0, 1.2)
cond_true = _condition(damage)
cond_obs = cond_true[:obs] + rng.normal(0, 1.6, obs)          # noisy monitored history

coef  = np.polyfit(np.arange(obs), cond_obs, 2)              # fit an accelerating trend
trend = np.poly1d(coef)
proj  = trend(tm)
below = np.where(proj <= INTERVENE)[0]
cross = int(below[0]) if len(below) else horizon
rul   = max(0, cross - obs)

true_below = np.where(cond_true <= INTERVENE)[0]
true_cross = int(true_below[0]) if len(true_below) else horizon

plt.figure(figsize=(9, 4.5))
plt.plot(tm, cond_true, color=MUTED, ls=":", label="true condition (unseen future)")
plt.scatter(np.arange(obs), cond_obs, s=16, color=CYAN, label="monitored history")
plt.plot(tm[obs-1:cross+1], proj[obs-1:cross+1], color=AMBER, lw=2.5, label="fitted trend, projected")
plt.axhline(INTERVENE, color=RED, ls="--", label="intervention level")
plt.axvline(obs, color="0.4", lw=1)
if cross < horizon:
    plt.scatter([cross], [INTERVENE], marker="x", s=140, color=RED, zorder=5, label="projected crossing")
plt.ylim(0, 105); plt.xlabel("month"); plt.ylabel("condition rating")
plt.title("Condition history, the fitted trend, and where it crosses the line")
plt.legend(fontsize=8); plt.tight_layout(); plt.show()

print(f"Projected crossing : month {cross}")
print(f"Remaining useful life : {rul} months")
print(f"Actual crossing (truth): month {true_cross}  ({cross - true_cross:+d} vs forecast)")
""")

# ---------------------------------------------------------------- 17. fusion
md(r"""
## 17 · Fusion — one prioritized alert

**Structural activity.** Every asset team has a health screen. The condition estimate on one side, the
crack grade from the drone on another, the anomaly residual and the RUL forecast beside them. The engineer
in the middle does not act on any one feed — they cross-reference them.

**The challenge.** Each feed alone is close to noise. The readings say elevated risk — it could be one cold
snap. The crack CNN flags a mark — it could be a wet patch. The anomaly spikes — it could be one heavy
convoy. A system that alarms on any one gets switched off in a week.

**The AI connection.** Fuse them. A dropping condition estimate **and** a crack graded by the CNN **and**
an anomaly the weather cannot explain **and** a shrinking RUL are not four weak signals — they are one
clear call: inspect this component within the month. Several models, one prioritized alert, one engineer
who acts.
""")

co(r"""
def fusion_engine(condition_est, crack_cnn, anomaly_flag, rul_months, criticality):
    # Combine the branches into one prioritized action.
    #   condition_est : 0..100 estimated condition rating from the tabular model
    #   crack_cnn     : bool, the drone CNN graded a crack on the surface
    #   anomaly_flag  : bool, the residual crossed the anomaly threshold
    #   rul_months    : remaining useful life in months from the trend forecast
    #   criticality   : 'Critical' | 'Standard' | 'Spare'
    reading_risk = np.clip((INTERVENE - condition_est) / INTERVENE + 0.5, 0, 1) if condition_est < INTERVENE \
                   else np.clip((100 - condition_est) / 90.0, 0, 1)
    crit_w = {"Critical": 1.0, "Standard": 0.7, "Spare": 0.4}[criticality]
    urgency = (0.35 * reading_risk
               + 0.20 * (1.0 if crack_cnn else 0.0)
               + 0.20 * (1.0 if anomaly_flag else 0.0)
               + 0.25 * (1 - min(rul_months, 24) / 24)) * crit_w
    if urgency > 0.60:
        action = f"URGENT - inspect now (act within {rul_months:.0f} months)"
    elif urgency > 0.35:
        action = "PRIORITISE - add to the near-term plan"
    else:
        action = "MONITOR - keep watching"
    return round(float(urgency), 2), action

# Pier P-7: a critical component with three converging signals
print(fusion_engine(condition_est=48, crack_cnn=True,  anomaly_flag=True,  rul_months=5,  criticality="Critical"))
# A non-critical spare showing only mild risk
print(fusion_engine(condition_est=78, crack_cnn=False, anomaly_flag=False, rul_months=20, criticality="Spare"))
""")

# ---------------------------------------------------------------- 18. dashboard
md(r"""
## 18 · The predictive-maintenance dashboard — the business case

**Structural activity.** The screen the asset manager actually opens: every bridge, coloured by condition,
ranked by how soon it needs attention.

**The business case.** None of the engineering matters to the agency until it is a number a manager can act
on: how much a planned repair saves over an emergency one, how many closures are avoided, and how much
catastrophic risk is taken off the network this year. Catching damage while it is still a planned repair
avoids the emergency-repair multiplier and most of the closures.
""")

co(r"""
# A small live fleet, scored and ranked by priority.
rng = np.random.default_rng(5)
n = 12
names   = [f"BR-{i:02d}" for i in range(n)]
cond_f  = np.clip(rng.normal(72, 18, n), 20, 99).round(0)
rul_f   = np.clip((cond_f - INTERVENE) / 0.6 + rng.normal(0, 4, n), 1, 60).round(0)
crit_f  = rng.choice(["Critical", "Standard", "Spare"], n, p=[0.35, 0.45, 0.2])
crit_w  = np.array([{"Critical": 1.0, "Standard": 0.7, "Spare": 0.4}[c] for c in crit_f])
priority = ((100 - cond_f) / 100 * crit_w + (1 - rul_f / 60) * 0.3).round(2)

fleet = pd.DataFrame({
    "Bridge": names, "Condition": cond_f, "RUL_months": rul_f,
    "Criticality": crit_f, "Priority": priority,
}).sort_values("Priority", ascending=False).reset_index(drop=True)
print("The fleet, ranked by priority:")
print(fleet.to_string(index=False))
""")

co(r"""
# Predictive vs reactive: same network, same year.
bridges        = 40
planned_cost   = 80        # $k per bridge, planned repair
reactive_mult  = 4.0       # emergency repair costs this much more
fail_rate      = 0.12      # bridges developing damage per year
closure_cost   = 300       # $k per emergency closure

at_risk = bridges * fail_rate
reactive_total   = at_risk * planned_cost * reactive_mult + at_risk * 0.40 * closure_cost
predictive_total = at_risk * planned_cost                + at_risk * 0.05 * closure_cost
saved            = reactive_total - predictive_total
closures_avoided = at_risk * (0.40 - 0.05)

labels = ["Reactive\n(wait for damage)", "Predictive\n(the digital twin)"]
plt.figure(figsize=(6.5, 4))
plt.bar(labels, [reactive_total, predictive_total], color=[MUTED, GREEN])
plt.ylabel("$k / year"); plt.title("Reactive vs predictive - same network, same year")
plt.tight_layout(); plt.show()

print(f"Bridges caught early / year : {at_risk:.0f}")
print(f"Emergency closures avoided  : {closures_avoided:.0f}")
print(f"Saved per year              : ${saved:,.0f}k  (${saved*1000:,.0f})")
""")

# ---------------------------------------------------------------- 19. summary
md(r"""
## 19 · Summary — the whole digital twin

You built a bridge digital twin stage by stage: **sense → clean → prepare → model → CNN → locate →
evaluate → detect → forecast → fuse → serve.** Each AI method appeared because a structural-health task
ran into something one inspector could not do by hand:

- **Machine learning** weighs the eight *named* readings an engineer already defined into a condition
  rating.
- **The CNN** grades the *raw crack image* no one can reduce to a brightness rule, and **Grad-CAM** shows
  where it looked.
- **Anomaly detection** learns what frequency is *normal for the weather* and flags only the drop the
  temperature cannot explain.
- **The RUL forecast** fits the *downward trend* a single snapshot cannot show and reads off the months of
  life left.
- **Fusion** turns several weak signals into one prioritized alert.

The inspector stays in charge throughout. The twin reports and forecasts; the engineer decides and signs
off — and the network runs safer, and cheaper, for it.
""")

# ---------------------------------------------------------------- assemble
nb = new_notebook(cells=cells)
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "colab": {"provenance": []},
}
out = "Bridge_Digital_Twin_DL.ipynb"
with open(out, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

# validate
nb2 = nbf.read(out, as_version=4)
nbf.validate(nb2)
print(f"Wrote {out} | cells: {len(nb2.cells)} | nbformat.validate: OK")
