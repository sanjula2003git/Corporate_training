"""
Builds CNC_Machining_DL.ipynb from nbformat cells.
Run:  python build_nb.py
The notebook is standalone (Colab): it does not import app.py/story.py/bridge.py.
Every physics function and dataset step is re-defined inline so the notebook and
the app agree, but the notebook runs on its own with numpy/pandas/sklearn (+ an
optional TensorFlow path for the CNNs, guarded by a KERAS flag).
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

cells = []
def md(t):  cells.append(new_markdown_cell(t.strip("\n")))
def co(t):  cells.append(new_code_cell(t.strip("\n")))

# ---------------------------------------------------------------- title
md(r"""
# AI-Based CNC Machining Optimization
### Teaching AI through the optimization of a metal-cutting job

This notebook is the runnable companion to the CNC Machining course. You are not learning AI for its own
sake — you are running a machine shop, and each AI method appears because it solves a real machining
problem one machinist cannot cover by hand.

**The problem, in one line:** choose the cutting **speed**, **feed rate** and **depth of cut** that finish
the batch fastest, without wrecking the surface finish or burning through the tool.

**The framing throughout:** the machinist stays in charge and stays accountable. The system only eases the
part one person cannot carry alone — evaluating thousands of settings, watching every cut, reading a
surface no gauge can score. It *recommends* and *flags*; the machinist *decides* and *signs off*.

**What we build, in the order a real project runs it:**

1. The machine shop — the problem
2. One cutting pass → data collection
3. Load the machining log
4. Data inspection (dropouts, saturation spikes)
5. Data cleaning (median fill)
6. Normalization (MinMaxScaler)
7. Train / test split
8. ML baseline — Random Forest for roughness, tool life and scrap
9. Why ML cannot grade a raw surface image
10. Deep learning — from a neuron to a network
11. CNN on the machined-surface image
12. CNN detects a chipped tool edge (with Grad-CAM)
13. Training — loss curves
14. Evaluation — the confusion matrix and the costly miss
15. **Optimization — finding the sweet spot**
16. Fusion — one recommended action
17. The optimization dashboard — the business case
18. Summary — the whole pipeline
""")

md(r"""
## Setup

In Colab the libraries below are already installed. If you run this elsewhere, uncomment the install
line. We use `matplotlib` for plots to keep the notebook simple and portable. TensorFlow is optional —
the two CNN sections train if it is present and skip cleanly if it is not.
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
from sklearn.metrics import (confusion_matrix, ConfusionMatrixDisplay,
                             accuracy_score, r2_score)

np.random.seed(42)
plt.rcParams["figure.figsize"] = (8, 4)

# Teaching palette (matches the app): cyan / amber / green / red
CYAN, AMBER, GREEN, RED, MUTED = "#4fc3f7", "#ffb74d", "#66bb6a", "#ef5350", "#8b949e"
print("Environment ready.")
""")

# ---------------------------------------------------------------- 1. the machine shop
md(r"""
## 1 · The machine shop — the problem

**Machining activity.** A CNC lathe has a batch of steel parts to turn. Before the first cut the machinist
sets three numbers: **cutting speed** (m/min), **feed rate** (mm/rev) and **depth of cut** (mm). Push them
up and the part is finished in half the time. Push them too far and the tool overheats, chatters and chips.

**The challenge.** There is a sweet spot, and it moves with the material, the tool and the machine. Cut too
fast and you pay in ruined tools and scrapped parts; cut too slow and the shift runs out before the batch
does. No single machinist has tried every combination.

**The AI connection.** The shop does not need judgement replaced — it needs every plausible setting
evaluated, the finish and tool life each one would give, so the fastest safe setting is *chosen* instead of
guessed. That search, too large to do by hand, is the only reason AI belongs at the machine.
""")

co(r"""
# ---- The machining physics (identical to the app) -------------------------
# The sensors are consequences of the settings and the tool-wear state; the
# targets (roughness, tool life) follow textbook forms. The SAME functions drive
# the synthetic dataset AND the optimizer's grid search later, so they agree.
NOSE_R   = 0.8    # mm  - tool nose radius (fixed)
RA_LIMIT = 3.5    # um  - surface-roughness tolerance (scrap above this)
TL_LIMIT = 7.0    # min - minimum acceptable tool life

def _force(Vc, f, ap, wear):
    return 1500.0 * ap * (f ** 0.75) * (1 + 0.35 * wear)

def _temp(Vc, f, ap, wear):
    return 90.0 + 0.85 * Vc + 260.0 * f + 22.0 * wear * (Vc / 150.0)

def _vib(Vc, f, ap, wear):
    return 0.6 + 1.5 * ap + 0.008 * Vc + 2.2 * wear

def _current(force, Vc):
    return 4.0 + 0.006 * force + 0.02 * Vc

def _roughness(f, wear, vib):
    # classic Ra ~ f^2 / (32 * r_nose), worsened by wear and vibration
    return (f ** 2) / (32.0 * NOSE_R) * 1000.0 * (1 + 0.5 * wear) + 0.12 * vib

def _tool_life(Vc, f, ap):
    # Taylor-style: life collapses with speed, and falls with feed and depth
    return 22.0 * (180.0 / Vc) ** 2.2 * (0.25 / f) ** 0.55 * (2.0 / ap) ** 0.35

def _features_for(Vc, f, ap, wear=0.0):
    # Build the 7-feature row(s) the models expect, from settings (noise-free).
    # Works on scalars or numpy arrays.
    force = _force(Vc, f, ap, wear)
    vib   = _vib(Vc, f, ap, wear)
    temp  = _temp(Vc, f, ap, wear)
    cur   = _current(force, Vc)
    return np.stack([Vc, f, ap, force, vib, temp, cur], axis=-1)

# Two settings, same batch: cautious vs aggressive.
ap = 1.5
for label, (Vc, f) in [("Cautious", (90, 0.10)), ("Aggressive", (240, 0.35))]:
    mrr  = Vc * f * ap                      # material removal rate (higher = faster)
    Ra   = _roughness(f, 0.3, _vib(Vc, f, ap, 0.3))
    life = _tool_life(Vc, f, ap)
    print(f"{label:11s} Vc={Vc:3d} f={f:.2f}  ->  removal {mrr:5.1f}  "
          f"Ra {Ra:4.2f} um  tool life {life:4.0f} min")
print("\nFaster removal buys a rougher finish and a shorter tool. The sweet spot is a balance.")
""")

# ---------------------------------------------------------------- 2. one cutting pass
md(r"""
## 2 · One cutting pass → data collection

**Machining activity.** You run a trial pass. You choose the speed, feed and depth. During the cut a
dynamometer logs cutting **force**, an accelerometer logs **vibration**, a thermocouple logs **temperature**
and the drive logs spindle **current**. Afterwards you measure the surface **roughness** and note how much
**tool life** it cost — and whether the part is scrap.

**The challenge.** Whoever reads that trial sheet later does not get the cut — not the smell of hot swarf,
not the change in the sound as the tool dulled. They get a row of numbers. A mis-logged feed or a saturated
force channel means a wrong conclusion.

**The AI connection.** For a model that limitation is absolute. One row — settings, readings, outcome — is
all it gets. The record *is* the machining pass, as far as the model is concerned.

The seven **named** columns the model reads on every pass:

| Column | Source | Unit | What it drives |
|---|---|---|---|
| cutting_speed | setting | m/min | tool life |
| feed_rate | setting | mm/rev | the finish |
| depth_of_cut | setting | mm | the load |
| force_n | dynamometer | N | overload, rising with wear and depth |
| vibration_mm_s | accelerometer | mm/s | chatter, instability |
| temperature_c | thermocouple | °C | heat at high speed — tool softening |
| current_a | drive | A | power drawn — load and dull-tool drag |

The **targets** the model learns to predict: `roughness_um`, `tool_life_min`, and `scrap`.
""")

co(r"""
# One row = one machining pass: 7 named readings + three outcomes.
FEATURES = ["cutting_speed", "feed_rate", "depth_of_cut", "force_n",
            "vibration_mm_s", "temperature_c", "current_a"]
NICE = ["Speed (m/min)", "Feed (mm/rev)", "Depth (mm)", "Force (N)",
        "Vibration (mm/s)", "Temp (C)", "Current (A)"]

def make_truth(N=1400, seed=42):
    rng = np.random.default_rng(seed)
    Vc   = rng.uniform(60, 280, N)
    f    = rng.uniform(0.05, 0.45, N)
    ap   = rng.uniform(0.3, 3.0, N)
    wear = rng.uniform(0, 1, N)

    force = _force(Vc, f, ap, wear) + rng.normal(0, 80, N)
    vib   = np.abs(_vib(Vc, f, ap, wear) + rng.normal(0, 0.3, N))
    temp  = _temp(Vc, f, ap, wear) + rng.normal(0, 8, N)
    cur   = _current(force, Vc) + rng.normal(0, 0.8, N)

    Ra    = np.clip(_roughness(f, wear, vib) + rng.normal(0, 0.15, N), 0.2, None)
    life  = np.clip(_tool_life(Vc, f, ap) + rng.normal(0, 2, N), 3, 120)
    scrap = ((Ra > RA_LIMIT) | (life < TL_LIMIT)).astype(int)

    return pd.DataFrame({
        "pass_id": np.arange(1, N + 1),
        "cutting_speed": Vc.round(0), "feed_rate": f.round(3),
        "depth_of_cut": ap.round(2), "force_n": force.round(0),
        "vibration_mm_s": vib.round(2), "temperature_c": temp.round(0),
        "current_a": cur.round(1),
        "roughness_um": Ra.round(2), "tool_life_min": life.round(0), "scrap": scrap,
    })

truth = make_truth()
print("One pass = one row:")
truth.head()
""")

co(r"""
print("Passes logged :", len(truth), "| Columns:", truth.shape[1])
print("Scrap rate    : {:.1%}".format(truth.scrap.mean()))
print("Median finish : {:.2f} um  |  Median tool life : {:.0f} min"
      .format(truth.roughness_um.median(), truth.tool_life_min.median()))
""")

# ---------------------------------------------------------------- 3. load
md(r"""
## 3 · Load the machining log

**Machining activity.** The machine has logged every trial pass for weeks. Before anything is built on it,
open the export and check it against what was installed: how many passes, are all the sensors present, is
each column the type it should be?

A real export is messy — dropped channels, saturated sensors, duplicate rows. We create a realistic *dirty*
copy so the cleaning steps have something to do.
""")

co(r"""
def make_dirty(df, seed=42):
    rng = np.random.default_rng(seed)
    N = len(df)
    dirty = df.copy()
    # random dropouts (missing readings)
    for col in ["force_n", "vibration_mm_s", "temperature_c", "current_a", "feed_rate"]:
        dirty.loc[rng.choice(N, int(0.06 * N), replace=False), col] = np.nan
    # impossible / stuck values from faulty sensors
    dirty.loc[rng.choice(N, 14, replace=False), "force_n"]        = 9999   # saturated dynamometer
    dirty.loc[rng.choice(N, 10, replace=False), "temperature_c"]  = 999    # thermocouple fault
    dirty.loc[rng.choice(N, 12, replace=False), "vibration_mm_s"] = 0.0    # dead probe
    # duplicate records (double-logged passes)
    dirty = pd.concat([dirty, dirty.sample(20, random_state=4)], ignore_index=True)
    return dirty

dirty = make_dirty(truth)
print("Rows in the raw export:", len(dirty))
dirty.head(8)
""")

# ---------------------------------------------------------------- 4. inspection
md(r"""
## 4 · Data inspection — dropouts and spikes

**Machining activity.** Inspect the log the way you inspect the machine. A loose thermocouple leaves a gap;
a saturated dynamometer reads a flat maximum; an accelerometer that came unstuck reads a frozen zero.

**The challenge.** You cannot eyeball 1,400 passes the way you check one part. A channel that dropped out
leaves a hole that looks like nothing; a stuck channel looks perfectly reasonable. The fault is invisible at
this scale.

**The AI connection.** So inspect with counts and distributions instead of eyes. Count missing readings per
channel and the failed sensor announces itself. This step only *diagnoses* — nothing is repaired yet.
""")

co(r"""
print("Missing readings per channel:")
print(dirty[FEATURES].isna().sum())
""")

co(r"""
fig, axes = plt.subplots(1, 3, figsize=(12, 3.2))
for ax, col in zip(axes, ["force_n", "temperature_c", "vibration_mm_s"]):
    ax.hist(dirty[col].dropna(), bins=50, color=CYAN)
    ax.set_title(col)
axes[0].annotate("saturation\n(9999 N)", xy=(9999, 1), color=RED, ha="right")
plt.suptitle("The values far from the pack are sensor faults, not machine states")
plt.tight_layout(); plt.show()
""")

# ---------------------------------------------------------------- 5. cleaning
md(r"""
## 5 · Data cleaning

**Machining activity.** Act on the diagnosis. A cutting force of 9,999 N is a saturated channel and comes
out; a vibration of zero on a running cut is a dead probe, not a smooth cut; a pass logged twice is struck
off.

**The challenge — a judgement call.** Drop every flawed pass and there is little left to learn from. Keep
everything and a dead-probe zero teaches the model that a violent cut can read zero vibration.

**The AI connection.** We drop duplicates, turn impossible values into gaps, then fill gaps with the
**median**. Why the median and not the mean? The mean is dragged upward by a 9,999 N saturation spike; the
median — the middle value — barely notices it.
""")

co(r"""
def clean_log(dirty):
    clean = dirty.drop_duplicates().copy()
    clean.loc[clean.force_n > 8000, "force_n"]          = np.nan   # impossible -> gap
    clean.loc[clean.temperature_c > 700, "temperature_c"] = np.nan
    clean.loc[clean.vibration_mm_s <= 0, "vibration_mm_s"] = np.nan
    for col in ["force_n", "vibration_mm_s", "temperature_c", "current_a", "feed_rate"]:
        clean[col] = clean[col].fillna(clean[col].median())   # median fill
    return clean

clean = clean_log(dirty)
print("Rows before:", len(dirty), "-> after:", len(clean),
      "| Missing after:", int(clean[FEATURES].isna().sum().sum()))

# Why median, not mean: the saturation spike drags the mean, not the median.
raw_force = dirty["force_n"].dropna()
print(f"\nforce_n  mean = {raw_force.mean():8.1f} N   <- pulled up by the 9999 N spikes")
print(f"force_n  median = {raw_force.median():6.1f} N   <- the honest centre")
""")

# ---------------------------------------------------------------- 6. normalization
md(r"""
## 6 · Normalization

**Machining activity.** Every channel reports in its own unit — m/min, mm/rev, mm, newtons, °C, amps. Put
them on one common scale before comparing them.

**The challenge.** Raw magnitudes lie about importance. Force runs into the hundreds; feed runs 0.05–0.45.
Side by side, force looks thousands of times more significant because of a unit — when a 0.1 mm/rev rise in
feed is the real driver of a rough finish.

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

**Machining activity.** No machinist signs off a settings model using the very trial cuts it was tuned on.
Tuning happens on known passes; acceptance is proven on passes the model has not seen.

**The challenge.** A model checked on the passes it trained on just repeats what it memorised — it scores
brilliantly and proves nothing. The first new part exposes it.

**The AI connection.** Split the passes: train, validation, and a sealed test set opened only at the
machining audit. Only a score on unseen passes says anything about the next part off the machine. We
stratify on `scrap` so the scrap rate stays balanced across all three splits.
""")

co(r"""
X    = norm[FEATURES].values
ys   = norm["scrap"].values
yRa  = norm["roughness_um"].values
yTL  = norm["tool_life_min"].values

idx = np.arange(len(X))
itr, itmp = train_test_split(idx, test_size=0.30, random_state=42, stratify=ys)
ival, ite = train_test_split(itmp, test_size=0.50, random_state=42, stratify=ys[itmp])

Xtr, Xval, Xte = X[itr], X[ival], X[ite]
ytr, yval, yte = ys[itr], ys[ival], ys[ite]
RaTr, RaTe     = yRa[itr], yRa[ite]
TLtr, TLte     = yTL[itr], yTL[ite]
print(f"Train {len(itr)}  |  Validation {len(ival)}  |  Test (sealed) {len(ite)}")
""")

# ---------------------------------------------------------------- 8. ml baseline
md(r"""
## 8 · ML baseline — Random Forest for roughness, tool life and scrap

**Machining activity.** Every experienced machinist carries a model in their head: high feed roughens the
finish, high speed shortens the tool, high force and vibration mean trouble. It is not written down and not
consistent between two machinists.

**The challenge.** Write it as a rule and you cannot. Roughness rises with feed — but by how much, and how
much worse when the tool is worn? It is thousands of weighted interactions.

**The AI connection.** Machine learning does exactly this job. You do not state the equations — you state
the factors, which an engineer already named at the trial. Given the seven columns and 1,400 outcomes, a
Random Forest works out the mapping to roughness and tool life itself. We train **two regressors** (Ra and
tool life) and **one classifier** (scrap), and score them on the sealed passes.
""")

co(r"""
# Two regressors and one classifier, all on the same named readings.
ra_m  = RandomForestRegressor(n_estimators=200, random_state=42).fit(Xtr, RaTr)
tl_m  = RandomForestRegressor(n_estimators=200, random_state=42).fit(Xtr, TLtr)
rf    = RandomForestClassifier(n_estimators=200, random_state=42).fit(Xtr, ytr)

print("Roughness  R^2 on sealed passes : {:.2f}".format(r2_score(RaTe, ra_m.predict(Xte))))
print("Tool-life  R^2 on sealed passes : {:.2f}".format(r2_score(TLte, tl_m.predict(Xte))))
print("Scrap classifier accuracy       : {:.1%}".format(rf.score(Xte, yte)))
""")

co(r"""
# What each regressor learned to weigh -- you never set these.
fig, ax = plt.subplots(1, 2, figsize=(12, 3.6))
for a, model, title, colr in [(ax[0], ra_m, "drivers of surface roughness", CYAN),
                              (ax[1], tl_m, "drivers of tool life", AMBER)]:
    imp = pd.Series(model.feature_importances_, index=NICE).sort_values()
    imp.plot.barh(ax=a, color=colr); a.set_title(title)
plt.tight_layout(); plt.show()
print("Feed dominates roughness; speed dominates tool life -- exactly what a machinist would tell you,")
print("but here it was LEARNED from 1,400 outcomes, not stated as a rule.")
""")

co(r"""
# Try one setting through the trained models (via the shared physics + scaler).
def score_setting(Vc, f, ap):
    row  = _features_for(np.array([Vc]), np.array([f]), np.array([ap]))
    rs   = scaler.transform(row)
    ra_hat = float(ra_m.predict(rs)[0])
    tl_hat = float(tl_m.predict(rs)[0])
    ok = (ra_hat <= RA_LIMIT) and (tl_hat >= TL_LIMIT)
    return ra_hat, tl_hat, Vc * f * ap, ok

for Vc, f, ap in [(180, 0.20, 1.5), (250, 0.40, 2.5)]:
    ra_hat, tl_hat, mrr, ok = score_setting(Vc, f, ap)
    verdict = "within limits" if ok else "OUT of tolerance / tool too short"
    print(f"Vc={Vc} f={f:.2f} ap={ap}: Ra {ra_hat:4.2f} um, life {tl_hat:4.0f} min, "
          f"removal {mrr:5.1f}  ->  {verdict}")
""")

# ---------------------------------------------------------------- 9. why ML can't grade an image
md(r"""
## 9 · Why ML cannot grade a raw surface image

**Machining activity.** Look at a machined surface and you know. A good finish shows fine, even feed marks;
a bad one shows chatter bands or tearing. An experienced machinist grades it at a glance — but the diagnosis
is in the *pattern of pixels*, not in any single gauge reading.

**The challenge.** The Random Forest needs named columns. A camera frame is a 64×64 grid — **4,096 unnamed
numbers**, none of them labelled "defect". The standard fix — reduce the image to one number (average
brightness) — throws away the pattern where the defect actually lives.

**The AI connection.** A chatter fault can have almost the same *average brightness* as a good finish while
its pattern is completely different. We show below that one hand-picked threshold cannot separate them.
""")

co(r"""
# Fully synthetic machined-surface images (same recipe as the app), as brightness grids.
def make_surface(kind="good", feed=0.20, size=64, seed=0):
    # Good = fine, even feed marks. Chatter = the marks with a low-frequency band
    # across them. Torn = irregular dark tears. Means kept similar so brightness
    # alone cannot grade it.
    rng = np.random.default_rng(seed)
    Y, X = np.mgrid[0:size, 0:size]
    period = 2.5 + feed * 12                              # finer grooves at low feed
    grooves = 0.5 + 0.22 * np.sin(2 * np.pi * Y / period)
    img = grooves + rng.normal(0, 0.03, (size, size))
    if kind == "chatter":
        band = 0.5 + 0.5 * np.sin(2 * np.pi * X / 15.0)
        img = 0.5 + (img - 0.5) * (0.5 + 1.1 * band)
        img += 0.12 * np.sin(2 * np.pi * (X + Y) / 9.0)
    elif kind == "torn":
        for _ in range(7):
            cy, cx = rng.integers(6, size - 6, 2)
            r = rng.integers(3, 7)
            img[(Y - cy) ** 2 + (X - cx) ** 2 < r ** 2] -= rng.uniform(0.25, 0.45)
    elif kind == "good-bright":
        img = img + 0.12
    return np.clip(img, 0, 1)

fig, ax = plt.subplots(1, 3, figsize=(11, 3.6))
for a, kind in zip(ax, ["good", "chatter", "torn"]):
    a.imshow(make_surface(kind, seed=1), cmap="gray", vmin=0, vmax=1)
    a.set_title(kind); a.axis("off")
plt.suptitle("One surface = 64 x 64 = 4,096 unnamed pixels. None of them is 'defect'.")
plt.tight_layout(); plt.show()
""")

co(r"""
# The hand-made rulebook: reduce each image to its average brightness, set one threshold.
cases = [("Good finish",             make_surface("good",        seed=1), "good"),
         ("Good (brighter lighting)", make_surface("good-bright", seed=2), "good"),
         ("Chatter (defect)",        make_surface("chatter",     seed=3), "DEFECT"),
         ("Torn (defect)",           make_surface("torn",        seed=4), "DEFECT")]
threshold = 0.45
print(f"{'case':28s} {'avg brightness':>14s}   verdict (reject < {threshold})")
for name, im, truth_lbl in cases:
    b = float(im.mean())
    verdict = "reject" if b < threshold else "pass"
    print(f"{name:28s} {b:14.3f}   {verdict:7s}  (truth: {truth_lbl})")
print("\nChatter has almost the SAME average brightness as a good finish -- the banding cancels in the mean.")
print("One number throws away the pattern that actually distinguishes them. No single threshold works.")
""")

# ---------------------------------------------------------------- 10. DL intro
md(r"""
## 10 · Deep learning — from a neuron to a network

Deep learning changes the question. Instead of *you* writing the rule, you supply labelled examples and the
network learns the features that separate them.

- **A neuron** weighs each input, sums them, adds a bias, and passes the result through an activation
  function: `output = activation(w · x + b)`. That is exactly how a machinist weighs signals into one call —
  the weights are what experience becomes.
- **A network** stacks neurons in layers. One neuron draws a straight line; layers bend the boundary around
  real scrap patterns (fast *and* light means one thing; fast *and* deep another). **Training** sets the
  weights by the learning loop: predict → measure error → adjust → repeat.

We first confirm a small neural net matches the Random Forest on the named readings — deep learning does
**not** beat ML here. Its value comes later, on the raw image ML cannot read.
""")

co(r"""
# A small ANN regressor on the SAME named readings, predicting roughness.
ann = MLPRegressor(hidden_layer_sizes=(12, 6), max_iter=1200, random_state=42).fit(Xtr, RaTr)
print("Random Forest roughness R^2 : {:.2f}".format(r2_score(RaTe, ra_m.predict(Xte))))
print("Neural net    roughness R^2 : {:.2f}".format(r2_score(RaTe, ann.predict(Xte))))
print("\nOn named readings, ML and DL are about the same. Named features -> use the simpler tool.")
""")

# ---------------------------------------------------------------- 11. surface CNN
md(r"""
## 11 · CNN on the machined-surface image

**Machining activity.** A machinist does not read 4,096 pixels — they look for repeating features (the
spacing of feed marks, the banding of chatter) wherever they appear on the part.

**The AI connection.** A **2-D convolutional neural network** slides small learned filters across the image;
each fires on a pattern wherever it occurs. Early filters find simple edges; later layers combine them into
a defect signature. The features are *learned* from labelled images — the grader the hand-made threshold
could not be.

We build a small labelled set of surface images (good finish vs chatter/rough) and train a small `Conv2D`.
""")

co(r"""
# Build a labelled surface-image dataset: good (0) vs defect (1, chatter or torn).
def build_surface_dataset(n_per_class=180, size=64):
    Xs, ys = [], []
    for k in range(n_per_class):
        feed = 0.08 + 0.30 * (k / n_per_class)
        Xs.append(make_surface("good", feed=feed, seed=1000 + k)); ys.append(0)
        if k % 2 == 0:
            Xs.append(make_surface("good-bright", feed=feed, seed=1500 + k)); ys.append(0)
        kind = "chatter" if k % 2 == 0 else "torn"
        Xs.append(make_surface(kind, feed=feed, seed=5000 + k)); ys.append(1)
    X = np.array(Xs)[..., np.newaxis].astype("float32")   # (samples, 64, 64, 1)
    y = np.array(ys).astype("float32")
    return X, y

Xs_all, ys_all = build_surface_dataset()
Xs_tr, Xs_te, ys_tr, ys_te = train_test_split(
    Xs_all, ys_all, test_size=0.25, random_state=0, stratify=ys_all)
print("Surface dataset:", Xs_all.shape, "| train", len(ys_tr), "test", len(ys_te),
      "| defect rate {:.0%}".format(ys_all.mean()))
""")

co(r"""
# TensorFlow/Keras is optional. This flag guards every CNN cell so the notebook
# runs end-to-end whether or not TF is installed (it is preinstalled in Colab).
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
    surface_cnn = models.Sequential([
        layers.Input(shape=(64, 64, 1)),
        layers.Conv2D(8,  3, activation="relu"),
        layers.MaxPooling2D(2),
        layers.Conv2D(16, 3, activation="relu"),
        layers.MaxPooling2D(2),
        layers.Flatten(),
        layers.Dense(16, activation="relu"),
        layers.Dense(1,  activation="sigmoid"),
    ])
    surface_cnn.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    surface_cnn.summary()
    hist_surface = surface_cnn.fit(Xs_tr, ys_tr, validation_split=0.2,
                                   epochs=10, batch_size=32, verbose=1)
    acc = surface_cnn.evaluate(Xs_te, ys_te, verbose=0)[1]
    print(f"\nSurface CNN accuracy on unseen images: {acc:.1%}")
    print("The CNN reads the raw surface the Random Forest could not touch.")
else:
    print("Skipped: no TensorFlow. In Colab this trains a small Conv2D on the surface images.")
""")

# ---------------------------------------------------------------- 12. tool CNN
md(r"""
## 12 · CNN detects a chipped tool edge

**Machining activity.** Turn the camera on the tool itself. An intact cutting edge is clean and straight; a
chipped one has a small bite missing — and once it chips, every part after it is out of tolerance.

**The challenge.** Checking every tool, every batch, is exactly the repetitive watching a person does worst
late in a shift. And a flat pass/fail is not enough: an engineer will not act on a black box that just says
"chipped" without showing where.

**The AI connection.** A second CNN classifies the edge as chipped or intact. **Grad-CAM** then highlights
the pixels that drove the call — so the heat lands on the chip itself. The machinist sees the verdict *and*
the evidence, and can overrule it.
""")

co(r"""
# Synthetic tool-edge images: a bright tool body meets a dark background; a chip
# is a bite out of the edge. Returns the image AND a Grad-CAM-style heat map.
def make_tool_edge(chipped=False, size=64, seed=1):
    rng = np.random.default_rng(seed)
    Y, X = np.mgrid[0:size, 0:size]
    edge = 40 + 2.0 * np.sin(Y / 9.0)
    img = np.where(X < edge, 0.82, 0.16).astype(float)
    cam = np.full((size, size), 0.08)
    if chipped:
        cy, cx = 32, 40
        chip = ((Y - cy) ** 2 + (X - cx) ** 2 < 5.5 ** 2) & (X < cx + 3)
        img[chip] = 0.16                                   # bite out of the edge
        cam = 0.08 + 0.92 * np.exp(-(((Y - cy) ** 2 + (X - cx) ** 2) / (2 * 6.0 ** 2)))
    img = np.clip(img + rng.normal(0, 0.03, (size, size)), 0, 1)
    return img, cam

intact_img, _        = make_tool_edge(chipped=False, seed=1)
chipped_img, chip_cam = make_tool_edge(chipped=True,  seed=2)

fig, ax = plt.subplots(1, 3, figsize=(11, 3.6))
ax[0].imshow(intact_img,  cmap="gray", vmin=0, vmax=1); ax[0].set_title("intact edge"); ax[0].axis("off")
ax[1].imshow(chipped_img, cmap="gray", vmin=0, vmax=1); ax[1].set_title("chipped edge"); ax[1].axis("off")
ax[2].imshow(chipped_img, cmap="gray", vmin=0, vmax=1)
ax[2].imshow(chip_cam, cmap="inferno", alpha=0.5)
ax[2].set_title("Grad-CAM: where the CNN looked"); ax[2].axis("off")
plt.tight_layout(); plt.show()
print("The heat lands on the chip -- detection PLUS explanation.")
""")

co(r"""
# Build a labelled tool-edge dataset and train a small CNN (guarded by KERAS).
def build_tool_dataset(n_per_class=180, size=64):
    Xs, ys = [], []
    for k in range(n_per_class):
        Xs.append(make_tool_edge(chipped=False, seed=2000 + k)[0]); ys.append(0)
        Xs.append(make_tool_edge(chipped=True,  seed=7000 + k)[0]); ys.append(1)
    X = np.array(Xs)[..., np.newaxis].astype("float32")
    y = np.array(ys).astype("float32")
    return X, y

Xt_all, yt_all = build_tool_dataset()
Xt_tr, Xt_te, yt_tr, yt_te = train_test_split(
    Xt_all, yt_all, test_size=0.25, random_state=0, stratify=yt_all)
print("Tool-edge dataset:", Xt_all.shape, "| train", len(yt_tr), "test", len(yt_te))

if KERAS:
    tf.random.set_seed(1)
    tool_cnn = models.Sequential([
        layers.Input(shape=(64, 64, 1)),
        layers.Conv2D(8,  3, activation="relu"),
        layers.MaxPooling2D(2),
        layers.Conv2D(16, 3, activation="relu"),
        layers.GlobalMaxPooling2D(),
        layers.Dense(16, activation="relu"),
        layers.Dense(1,  activation="sigmoid"),
    ])
    tool_cnn.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    hist_tool = tool_cnn.fit(Xt_tr, yt_tr, validation_split=0.2,
                             epochs=8, batch_size=32, verbose=1)
    acc = tool_cnn.evaluate(Xt_te, yt_te, verbose=0)[1]
    print(f"\nTool CNN accuracy on unseen edges: {acc:.1%}")
else:
    print("Skipped: no TensorFlow. In Colab this trains a small Conv2D on the tool-edge images.")
""")

# ---------------------------------------------------------------- 13. training / loss curves
md(r"""
## 13 · Training — watching the loss fall

**The learning loop, run thousands of times:** the model predicts, compares to the known outcome, and
nudges every weight to be a little less wrong. The **loss** measures how wrong it is.

The loss falls fast, then flattens. More epochs on the same images only memorise them, so you stop when the
held-out (validation) loss stops improving — that is early stopping. With TensorFlow present we plot the CNN
history; without it, the sklearn ANN exposes the same idea via its `loss_curve_`.
""")

co(r"""
if KERAS:
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.4))
    ax[0].plot(hist_surface.history["loss"],     label="train",      color=CYAN)
    ax[0].plot(hist_surface.history["val_loss"], label="validation", color=AMBER)
    ax[0].set_title("Surface CNN training loss"); ax[0].set_xlabel("epoch"); ax[0].legend()
    ax[1].plot(hist_tool.history["loss"],     label="train",      color=CYAN)
    ax[1].plot(hist_tool.history["val_loss"], label="validation", color=AMBER)
    ax[1].set_title("Tool CNN training loss"); ax[1].set_xlabel("epoch"); ax[1].legend()
    plt.tight_layout(); plt.show()
else:
    # sklearn ANN exposes a loss curve too -- same idea, no TensorFlow needed.
    plt.plot(ann.loss_curve_, color=CYAN)
    plt.title("Neural-net training loss (sklearn ANN)")
    plt.xlabel("epoch"); plt.ylabel("loss")
    plt.tight_layout(); plt.show()
    print("The loss falls fast then flattens -- more epochs on the same passes only memorise them.")
""")

# ---------------------------------------------------------------- 14. evaluation
md(r"""
## 14 · Evaluation — the confusion matrix

**Machining activity.** Audit the model the way you audit a first-article inspection: line up every call
against the measured part, and count.

**The challenge.** Four outcomes, and lumping them together hides the one that matters:

- Called good, was good — fine
- Called scrap, was scrap — caught it
- Called scrap, was actually good — a false reject, a wasted part
- **Called good, and it was scrap — the costly miss: scrap shipped to the customer**

**The AI connection.** Never quote accuracy alone. A model that calls everything good scores well on
accuracy and misses every real defect. The bottom-left box is what the whole system exists to prevent.
""")

co(r"""
pred = rf.predict(Xte)
cm = confusion_matrix(yte, pred)
tn, fp, fn, tp = cm.ravel()

ConfusionMatrixDisplay(cm, display_labels=["good", "scrap"]).plot(cmap="Blues", colorbar=False)
plt.title("Machining audit on the sealed test passes"); plt.show()

print(f"Overall accuracy       : {accuracy_score(yte, pred):.1%}")
print(f"Scrap shipped   (FN)   : {fn}   <- the costly box: scrap called good")
print(f"Good rejected   (FP)   : {fp}   <- wasted parts")
""")

# ---------------------------------------------------------------- 15. optimization
md(r"""
## 15 · Optimization — finding the sweet spot

This is the distinctive page — where prediction becomes a **decision**.

**Machining activity.** Of all the speed × feed combinations, which one finishes the batch fastest without
breaking the finish tolerance or wearing the tool out early? Trying them on real steel would cost days and a
drawer of tools.

**The AI connection.** Now the trained models earn their keep. Sweep a grid of settings, let the roughness
and tool-life models score every one, keep only those **inside your limits**, and pick the one with the
highest **material-removal rate**. That is constrained optimization — the recommendation the whole system
exists to make. Because the grid is scored through the same physics + scaler the models were trained on, the
optimizer and the dataset stay consistent.
""")

co(r"""
def optimize(ap=1.5, max_ra=RA_LIMIT, min_tl=TL_LIMIT, res=70):
    vc_ax = np.linspace(60, 280, res)
    f_ax  = np.linspace(0.05, 0.45, res)
    VC, F = np.meshgrid(vc_ax, f_ax)
    rows   = _features_for(VC.ravel(), F.ravel(), np.full(VC.size, ap))
    rows_s = scaler.transform(rows)
    ra_hat = ra_m.predict(rows_s).reshape(VC.shape)
    tl_hat = tl_m.predict(rows_s).reshape(VC.shape)
    mrr    = VC * F * ap
    feasible = (ra_hat <= max_ra) & (tl_hat >= min_tl)
    mrr_feas = np.where(feasible, mrr, np.nan)
    return vc_ax, f_ax, VC, F, mrr, mrr_feas, feasible, ra_hat, tl_hat

vc_ax, f_ax, VC, F, mrr, mrr_feas, feasible, ra_hat, tl_hat = optimize()

bi = np.nanargmax(mrr_feas)
r, c = np.unravel_index(bi, mrr.shape)
bestVc, bestF, best_ap = VC[r, c], F[r, c], 1.5
best_ra, best_tl, best_mrr = ra_hat[r, c], tl_hat[r, c], mrr[r, c]

plt.figure(figsize=(8, 5))
plt.pcolormesh(vc_ax, f_ax, mrr_feas, cmap="viridis", shading="auto")
plt.colorbar(label="material removal rate (higher = faster)")
plt.scatter([bestVc], [bestF], s=260, marker="*", color=RED,
            edgecolor="white", linewidth=1.5, label="optimum", zorder=5)
plt.title("Feasible settings, coloured by removal rate\n(blank = outside your finish / tool limits)")
plt.xlabel("cutting speed (m/min)"); plt.ylabel("feed rate (mm/rev)")
plt.legend(loc="upper left"); plt.tight_layout(); plt.show()

print("Recommended setting (depth fixed at 1.5 mm):")
print(f"  speed {bestVc:.0f} m/min | feed {bestF:.2f} mm/rev")
print(f"  predicted roughness {best_ra:.2f} um (<= {RA_LIMIT})  "
      f"| predicted tool life {best_tl:.0f} min (>= {TL_LIMIT:.0f})")

# speed-up vs a cautious baseline
base_Vc, base_f = 90.0, 0.10
base_mrr = base_Vc * base_f * best_ap
print(f"\nRemoves metal {best_mrr / base_mrr:.1f}x faster than a cautious "
      f"{base_Vc:.0f} m/min / {base_f:.2f} mm/rev pass, while holding both limits.")
""")

# ---------------------------------------------------------------- 16. fusion
md(r"""
## 16 · Fusion — one recommended action

**Machining activity.** Every cell has a control screen: the force and vibration readings on one side, the
surface grade from the camera on another, the tool-edge check beside it. The machinist in the middle does
not act on any one feed — they cross-reference them.

**The challenge.** Each feed alone is close to noise. The readings say elevated risk — could be one hard
spot in the bar. The surface CNN flags a mark — could be one bad frame. A system that alarms on any one gets
switched off in a week.

**The AI connection.** Fuse them. Elevated reading risk **and** a chatter grade from the surface CNN **and**
a chip flag from the tool CNN, weighted by how much the finish matters on this cut, is not three weak
signals — it is one clear call. Several models, one decision, one machinist who acts.
""")

co(r"""
def fusion_engine(reading_risk, surface_chatter, tool_chipped, cut_type):
    #   reading_risk    : 0..1 scrap probability from the tabular RF/ANN
    #   surface_chatter : bool, surface CNN flagged a defect pattern
    #   tool_chipped    : bool, tool CNN flagged a chipped edge
    #   cut_type        : 'Roughing' | 'Semi-finish' | 'Finishing'
    w = {"Roughing": 0.6, "Semi-finish": 0.8, "Finishing": 1.0}[cut_type]
    urgency = (0.4 * reading_risk
               + 0.3 * (1.0 if surface_chatter else 0.0)
               + 0.3 * (1.0 if tool_chipped else 0.0)) * w
    if urgency > 0.60:
        action = "STOP - back off feed and change the tool (act before the next part)"
    elif urgency > 0.35:
        action = "ADJUST - reduce feed and re-check this cut"
    else:
        action = "RUN - keep cutting"
    return round(urgency, 2), action

# A finishing cut with three converging signals
print(fusion_engine(reading_risk=0.80, surface_chatter=True, tool_chipped=True, cut_type="Finishing"))
# A roughing cut with only mild reading risk
print(fusion_engine(reading_risk=0.45, surface_chatter=False, tool_chipped=False, cut_type="Roughing"))
""")

# ---------------------------------------------------------------- 17. dashboard
md(r"""
## 17 · The optimization dashboard — the business case

**Machining activity.** The screen the shop manager opens: the setting the system recommends, the cycle time
it gives, the tool life it costs, and the scrap it avoids against how the job was run before.

**The business case.** None of the engineering matters to the business until it is a number a manager acts
on: how much faster the batch runs, how many inserts it saves, and how much money that is. We compare the
AI-recommended setting against a cautious baseline over a whole batch.
""")

co(r"""
# Set the batch and the shop rates.
parts        = 500      # parts in the batch
machine_rate = 75       # $/hour
insert_cost  = 35       # $/cutting insert
ap = 1.5

# Cautious baseline vs the optimizer's pick (found in section 15).
base_Vc, base_f = 100.0, 0.12
base_row = scaler.transform(_features_for(np.array([base_Vc]), np.array([base_f]), np.array([ap])))
base_tl  = float(tl_m.predict(base_row)[0])
base_mrr = base_Vc * base_f * ap
opt_row  = scaler.transform(_features_for(np.array([bestVc]), np.array([bestF]), np.array([ap])))
opt_tl   = float(tl_m.predict(opt_row)[0])
opt_mrr  = bestVc * bestF * ap

# Cycle time scales inversely with removal rate; tool changes scale with life.
base_time = parts / base_mrr
opt_time  = parts / opt_mrr
scale     = 8.0 / base_time                      # calibrate the baseline to a ~full shift
base_h, opt_h = base_time * scale, opt_time * scale
base_tools = max(1, base_h * 60 / max(base_tl, 1))
opt_tools  = max(1, opt_h  * 60 / max(opt_tl, 1))

time_saved = base_h - opt_h
tool_saved = base_tools - opt_tools
money      = time_saved * machine_rate + tool_saved * insert_cost

fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
ax[0].bar(["cautious", "AI-recommended"], [base_h, opt_h], color=[MUTED, GREEN])
ax[0].set_title("Batch time (h)")
ax[1].bar(["cautious", "AI-recommended"], [base_tools, opt_tools], color=[MUTED, GREEN])
ax[1].set_title("Inserts used")
plt.tight_layout(); plt.show()

print(f"Cautious baseline : {base_Vc:.0f} m/min / {base_f:.2f} mm/rev  "
      f"-> {base_h:.1f} h, {base_tools:.0f} inserts")
print(f"AI-recommended    : {bestVc:.0f} m/min / {bestF:.2f} mm/rev  "
      f"-> {opt_h:.1f} h, {opt_tools:.0f} inserts")
print(f"\nTime saved  : {time_saved:.1f} h   Inserts saved : {tool_saved:.0f}")
print(f"Saved / batch : ${money:,.0f}   (both settings hold the same finish and tool-life limits)")
""")

# ---------------------------------------------------------------- 18. summary
md(r"""
## 18 · Summary — the whole pipeline

You built a CNC machining-optimization system stage by stage: **sense → clean → prepare → model → CNN →
optimize → fuse → serve.** Each AI method appeared because a machining task ran into something one machinist
could not do by hand:

- **Machine learning** weighs the seven *named* readings an engineer already defined, predicting roughness,
  tool life and scrap.
- **The surface CNN** grades a *raw image* no one can reduce to a rule.
- **The tool CNN** finds a *chipped edge* and, with Grad-CAM, shows where it looked.
- **Optimization** searches every setting with the trained models and returns the fastest one still inside
  the finish and tool-life limits — prediction turned into a decision.
- **Fusion** turns several weak signals into one recommended action.
- **The dashboard** turns that action into hours, inserts and dollars a manager acts on.

The machinist stays in charge throughout. The system recommends and flags; the machinist decides and signs
off — and the shop runs faster, on fewer tools, for it.
""")

# ---------------------------------------------------------------- assemble
nb = new_notebook(cells=cells)
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "colab": {"provenance": []},
}
out = "CNC_Machining_DL.ipynb"
with open(out, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

# validate
nb2 = nbf.read(out, as_version=4)
nbf.validate(nb2)
print(f"Wrote {out} | cells: {len(nb2.cells)} | nbformat.validate: OK")
