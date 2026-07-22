"""
Builds Predictive_Maintenance_DL.ipynb from nbformat cells.
Run:  python build_nb.py
The notebook is standalone (Colab): it does not import app.py/story.py/bridge.py.
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

cells = []
def md(t):  cells.append(new_markdown_cell(t.strip("\n")))
def co(t):  cells.append(new_code_cell(t.strip("\n")))

# ---------------------------------------------------------------- title
md(r"""
# Intelligent Predictive Maintenance System
### Teaching AI through the maintenance of rotating machinery

This notebook is the runnable companion to the Predictive Maintenance course. You are not learning AI
for its own sake — you are running a plant on predictive maintenance, and each AI method appears
because it solves a real maintenance problem one engineer cannot cover by hand.

**The framing throughout:** the maintenance engineer stays in charge and stays accountable. The system
only eases the part one person cannot carry alone — watching every machine, continuously, between
rounds. It *notices*; the engineer *decides*.

**What we build, in the order a real project runs it:**

1. The factory floor — the problem
2. Machine inspection → data collection
3. Load the sensor log
4. Data inspection (dropouts, spikes)
5. Data cleaning
6. Normalization
7. Train / test split
8. ML baseline — Random Forest on the 7 named sensors
9. Why ML cannot read a raw vibration signal
10. Deep learning — from a neuron to a network
11. CNN on the raw vibration signal
12. LSTM on the degradation trend → Remaining Useful Life
13. Training (loss curves)
14. Evaluation — the confusion matrix and the missed-failure box
15. Fusion — one prioritized work order
16. The predictive maintenance dashboard — the business case
""")

md(r"""
## Setup

In Colab the libraries below are already installed. If you run this elsewhere, uncomment the install
line. We use `matplotlib` for plots to keep the notebook simple and portable.
""")

co(r"""
# !pip install numpy pandas scikit-learn tensorflow matplotlib

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, accuracy_score

np.random.seed(42)
plt.rcParams["figure.figsize"] = (8, 4)
print("Environment ready.")
""")

# ---------------------------------------------------------------- 1. factory floor
md(r"""
## 1 · The factory floor — the problem

**Mechanical activity.** A plant runs ~40 rotating machines across three shifts: motors, pumps,
compressors, CNC spindles. A bearing or seal does not fail all at once — it heats, vibrates and draws
more current for days before it seizes.

**The challenge.** One maintenance engineer walks the rounds only a few times a shift. Between rounds a
machine can drift from healthy to failed with nobody watching. Fixed-interval servicing either
replaces good parts too early or misses the one about to go.

**The AI connection.** The plant does not need judgement replaced — it needs the readings watched
continuously, so early drift is caught between rounds. That steady, tireless watching is the only
reason AI belongs on the floor.
""")

# ---------------------------------------------------------------- 2. inspection / data collection
md(r"""
## 2 · Machine inspection → data collection

**Mechanical activity.** You inspect a machine and read every instrument: bearing temperature,
discharge pressure, vibration, shaft speed, motor current, oil condition, hours run.

**The challenge.** Whoever reads that sheet later does not get the machine — only seven numbers. A wrong
or missing reading means a wrong conclusion.

**The AI connection.** For a model this limitation is absolute: one row of readings is all it gets. The
record *is* the machine, as far as the model is concerned.

The seven sensors we monitor on every machine:

| Sensor | Measures | Unit | Failure mode it catches |
|---|---|---|---|
| Temperature | bearing / casing temperature | °C | friction, lubrication loss |
| Pressure | discharge / line pressure | bar | blockage, seal leak |
| Vibration | RMS velocity | mm/s | bearing / imbalance / misalignment |
| Speed | shaft speed | RPM | load and duty context |
| Current | motor current draw | A | rising mechanical load |
| Oil quality | lubricant condition index | 0–100 | wear debris, degradation |
| Runtime | hours since last service | h | wear-out with age |
""")

co(r"""
# ---- Synthetic sensor log (same generation as the app) --------------------
# One row = one machine at one moment: 7 named readings + a failure outcome.
FEATURES = ["temperature_c", "pressure_bar", "vibration_mm_s", "rpm",
            "current_a", "oil_quality", "runtime_h"]

def generate_sensor_log(N=1200, seed=42):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "machine_id":     np.arange(1, N + 1),
        "temperature_c":  rng.normal(65, 12, N).round(1),
        "pressure_bar":   rng.normal(6.0, 1.4, N).round(2),
        "vibration_mm_s": np.abs(rng.normal(2.6, 1.5, N)).round(2),
        "rpm":            rng.normal(1500, 280, N).round(0),
        "current_a":      rng.normal(30, 7, N).round(1),
        "oil_quality":    np.clip(rng.normal(70, 15, N), 0, 100).round(0),
        "runtime_h":      rng.uniform(0, 20000, N).round(0),
    })
    # The failure label. This is the physics the model must recover from data:
    # trouble is several conditions at once, not any single reading.
    risk = ((df.vibration_mm_s > 5).astype(int)
            + (df.temperature_c > 85).astype(int)
            + (df.oil_quality < 45).astype(int)
            + (df.current_a > 44).astype(int)
            + (df.runtime_h > 15000).astype(int)
            + ((df.pressure_bar > 9) | (df.pressure_bar < 3)).astype(int))
    df["failure"] = (risk >= 2).astype(int)
    return df

truth = generate_sensor_log()
print("One machine, one moment = one row:")
truth.head()
""")

co(r"""
print("Records:", len(truth), "| Columns:", truth.shape[1])
print("Failure rate: {:.1%}".format(truth.failure.mean()))
""")

# ---------------------------------------------------------------- 3. load
md(r"""
## 3 · Load the sensor log

**Mechanical activity.** The condition-monitoring system has logged every machine for months. Before
building anything, check what actually arrived: how many records, how many columns, what type each is.

A real export is messy — dropped channels, saturated sensors, duplicate rows. We create a realistic
*dirty* copy so the cleaning steps have something to do.
""")

co(r"""
def make_dirty(df, seed=42):
    rng = np.random.default_rng(seed)
    N = len(df)
    dirty = df.copy()
    # random dropouts (missing readings)
    for col in ["temperature_c", "pressure_bar", "vibration_mm_s", "oil_quality", "current_a"]:
        dirty.loc[rng.choice(N, int(0.06 * N), replace=False), col] = np.nan
    # impossible / stuck values from faulty sensors
    dirty.loc[rng.choice(N, 14, replace=False), "temperature_c"] = 300   # thermocouple saturation
    dirty.loc[rng.choice(N, 10, replace=False), "pressure_bar"]  = -3     # clogged line
    dirty.loc[rng.choice(N, 12, replace=False), "vibration_mm_s"] = 0.0   # dead probe
    # duplicate records (double-logged)
    dirty = pd.concat([dirty, dirty.sample(20, random_state=4)], ignore_index=True)
    return dirty

dirty = make_dirty(truth)
print("Rows in the raw export:", len(dirty))
dirty.head()
""")

# ---------------------------------------------------------------- 4. inspection
md(r"""
## 4 · Data inspection — dropouts and spikes

**Mechanical activity.** Inspect the log the way you inspect the sensors. You cannot eyeball 1,200
records, so use counts and distributions instead of eyes.

**The challenge.** A channel that dropped out leaves a hole that looks like nothing; a stuck channel
looks reasonable. The fault is invisible at scale.

**The AI connection.** Count missing readings per sensor and the failed channel announces itself. This
step only *diagnoses* — nothing is repaired yet.
""")

co(r"""
print("Missing readings per sensor:")
print(dirty[FEATURES].isna().sum())
""")

co(r"""
fig, axes = plt.subplots(1, 3, figsize=(12, 3.2))
for ax, col in zip(axes, ["temperature_c", "pressure_bar", "vibration_mm_s"]):
    ax.hist(dirty[col].dropna(), bins=50, color="#4fc3f7")
    ax.set_title(col)
axes[0].annotate("saturation spike\n(300 C)", xy=(300, 1), color="#ef5350")
plt.suptitle("The values far from the pack are sensor faults, not machine states")
plt.tight_layout(); plt.show()
""")

# ---------------------------------------------------------------- 5. cleaning
md(r"""
## 5 · Data cleaning

**Mechanical activity.** Act on the diagnosis. Impossible values come out; a dead-probe zero on a
running machine is a fault, not a healthy reading. A record logged twice is struck off.

**The challenge — a judgement call.** Drop every flawed record and little is left to learn from. Keep
everything and a dead-probe zero teaches the model that a running machine can read zero.

**The AI connection.** We drop duplicates, turn impossible values into gaps, then fill gaps with the
**median** — the mean would be dragged by a 300 °C saturation spike, the median barely notices it.
""")

co(r"""
def clean_log(dirty):
    clean = dirty.drop_duplicates().copy()
    clean.loc[clean.temperature_c > 200, "temperature_c"] = np.nan   # impossible -> gap
    clean.loc[clean.pressure_bar < 0,   "pressure_bar"]   = np.nan
    clean.loc[clean.vibration_mm_s <= 0, "vibration_mm_s"] = np.nan
    for col in ["temperature_c", "pressure_bar", "vibration_mm_s", "oil_quality", "current_a"]:
        clean[col] = clean[col].fillna(clean[col].median())   # median fill
    return clean

clean = clean_log(dirty)
print("Rows before:", len(dirty), "-> after:", len(clean),
      "| Missing after:", int(clean[FEATURES].isna().sum().sum()))
""")

# ---------------------------------------------------------------- 6. normalization
md(r"""
## 6 · Normalization

**Mechanical activity.** Every sensor reports in its own unit — °C, bar, mm/s, RPM, amps. Put them on
one common scale before comparing them.

**The challenge.** Raw magnitudes lie about importance. RPM runs into the thousands; vibration runs
0–10 mm/s. Side by side, RPM looks a thousand times more significant because of a unit — when a 2 mm/s
rise in vibration is the real warning.

**The AI connection.** A neural network sees magnitude, not meaning. `MinMaxScaler` puts every sensor on
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

**Mechanical activity.** No engineer signs off a new machine's health model using the very unit it was
tuned on. Tuning happens on known machines; acceptance is proven on machines the model has not seen.

**The challenge.** A model tested on the records it trained on just repeats what it memorised — it
scores brilliantly and proves nothing.

**The AI connection.** Split the records: train, validation, and a sealed test set opened only at the
audit. Only a score on unseen machines says anything about the plant tomorrow.
""")

co(r"""
X, y = norm[FEATURES].values, norm["failure"].values
X_tr, X_tmp, y_tr, y_tmp = train_test_split(X, y, test_size=0.30, random_state=42, stratify=y)
X_val, X_te, y_val, y_te = train_test_split(X_tmp, y_tmp, test_size=0.50, random_state=42, stratify=y_tmp)
print(f"Train {len(y_tr)}  |  Validation {len(y_val)}  |  Test (sealed) {len(y_te)}")
""")

# ---------------------------------------------------------------- 8. ml baseline
md(r"""
## 8 · ML baseline — Random Forest on the named sensors

**Mechanical activity.** Every experienced engineer carries a failure model in their head: hot bearing,
high vibration, degraded oil, long runtime → pull it for service. It is not written down and not
consistent between two engineers.

**The challenge.** Write it as a rule and you cannot. It is thousands of weighted interactions — does
the vibration limit move when the oil is old, and by how much after 10,000 hours?

**The AI connection.** Machine learning does exactly this job. You do not state thresholds — you state
the factors, which an engineer already named at inspection. Given 7 columns and 1,200 outcomes, the
Random Forest works out the weighting itself.
""")

co(r"""
rf = RandomForestClassifier(n_estimators=200, random_state=42).fit(X_tr, y_tr)
print("Random Forest accuracy on sealed test machines: {:.1%}".format(rf.score(X_te, y_te)))

imp = pd.Series(rf.feature_importances_, index=FEATURES).sort_values()
imp.plot.barh(color="#4fc3f7")
plt.title("What the model learned to weigh (you never set these)")
plt.tight_layout(); plt.show()
""")

# ---------------------------------------------------------------- 9. why ML can't read a signal
md(r"""
## 9 · Why ML cannot read a raw vibration signal

**Mechanical activity.** Listen to a failing bearing and you know. But the diagnosis is in the *raw
accelerometer waveform* — thousands of amplitude samples a second — not in any single gauge reading.

**The challenge.** The Random Forest needs named columns. A raw window is 2,048 unnamed numbers; none of
them is "fault". The standard fix — reduce the window to one number (RMS) — throws away the shape where
the fault actually lives.

**The AI connection.** A hand-made feature is a rule you wrote and must maintain, and it discards most of
the signal. We show below that a single RMS threshold cannot separate an *early* fault from a
rough-running healthy machine.
""")

co(r"""
def make_vibration(fault=False, severity=1.0, n=2048, seed=3):
    # Healthy = shaft rotation (two sines) + noise.
    # Faulty  = plus a periodic bearing impact: an impulse train ringing a
    #           decaying resonance every ~96 samples (once per revolution).
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    base = 0.6*np.sin(2*np.pi*6*t/n) + 0.3*np.sin(2*np.pi*17*t/n)
    sig = base + rng.normal(0, 0.25, n)
    if fault:
        ring = np.exp(-np.arange(40)/7.0) * np.sin(2*np.pi*0.28*np.arange(40))
        impacts = np.zeros(n)
        for start in range(20, n-40, 96):
            impacts[start:start+40] += ring
        sig = sig + severity*5.0*impacts
    return sig

healthy = make_vibration(fault=False, seed=1)
faulty  = make_vibration(fault=True,  seed=3)

fig, ax = plt.subplots(2, 1, figsize=(9, 4), sharex=True)
ax[0].plot(healthy[:512], color="#66bb6a", lw=0.8); ax[0].set_title("Healthy window")
ax[1].plot(faulty[:512],  color="#ef5350", lw=0.8); ax[1].set_title("Faulty window (periodic bearing impacts)")
plt.tight_layout(); plt.show()
print("One window =", len(faulty), "unnamed samples. None of them is labelled 'fault'.")
""")

co(r"""
# The hand-made rulebook: reduce each window to its RMS and set one threshold.
def rms(x): return float(np.sqrt(np.mean(x**2)))

cases = {
    "Healthy":                 rms(make_vibration(False, seed=1)),
    "Rough-running (healthy)": rms(make_vibration(False, seed=9) * 1.7),
    "Early bearing fault":     rms(make_vibration(True, severity=0.35, seed=2)),
    "Severe fault":            rms(make_vibration(True, severity=1.2,  seed=3)),
}
threshold = 0.85
for name, v in cases.items():
    verdict = "ALARM" if v >= threshold else "ok"
    print(f"{name:26s} RMS={v:4.2f}  ->  {verdict}")
print("\nRMS is dominated by broadband roughness, not by the periodic bearing impacts.")
print("So a rough-but-HEALTHY machine reads HIGHER than an EARLY fault:")
print("  - the rough healthy machine false-alarms")
print("  - the early bearing fault slips under the threshold and is missed")
print("One hand-picked number throws away the periodic shape where the fault lives.")
""")

# ---------------------------------------------------------------- 10. DL intro
md(r"""
## 10 · Deep learning — from a neuron to a network

Deep learning changes the question. Instead of *you* writing the rule, you supply labelled examples and
the network learns the features that separate them.

- **A neuron** weighs each input, sums them, adds a bias, and passes the result through an activation
  function: `output = activation(w · x + b)`. That is exactly how an engineer weighs signals into one
  call — the weights are what experience becomes.
- **A network** stacks neurons in layers. One neuron draws a straight line; layers bend the boundary
  around real failure patterns (hot *and* high-vibration means one thing; hot *and* low-vibration
  another). **Training** sets the weights by the learning loop: predict → measure error → adjust →
  repeat.

We first confirm a small neural net matches the Random Forest on the named readings — deep learning
does **not** beat ML here. Its value comes later, on the raw signal ML cannot read.
""")

co(r"""
ann = MLPClassifier(hidden_layer_sizes=(12, 6), max_iter=800, random_state=42).fit(X_tr, y_tr)
print("Random Forest test accuracy : {:.1%}".format(rf.score(X_te, y_te)))
print("Neural net   test accuracy : {:.1%}".format(ann.score(X_te, y_te)))
print("\nOn named readings, ML and DL are about the same. Named features -> use the simpler tool.")
""")

# ---------------------------------------------------------------- 11. CNN
md(r"""
## 11 · CNN on the raw vibration signal

**Mechanical activity.** A vibration analyst does not read 2,048 numbers — they look for repeating
features (the spacing of impacts, the sidebands) wherever they appear in the trace.

**The AI connection.** A **1-D convolutional neural network** slides small learned filters along the
signal; each fires on a pattern wherever it occurs. Early filters find simple shapes, later layers
combine them into a fault signature. The features are *learned* from labelled windows — the detector
the hand-made threshold could not be.

We build a labelled set of vibration windows (healthy / faulty, varied severity) and train a small CNN.
""")

co(r"""
# Build a labelled signal dataset: ~800 windows, healthy vs faulty at varied severity.
def build_signal_dataset(n_per_class=400, n=2048):
    Xs, ys = [], []
    for k in range(n_per_class):
        Xs.append(make_vibration(fault=False, seed=1000 + k)); ys.append(0)
        sev = 0.3 + 1.0 * (k / n_per_class)          # early -> severe faults
        Xs.append(make_vibration(fault=True, severity=sev, seed=5000 + k)); ys.append(1)
    X = np.array(Xs)[..., np.newaxis].astype("float32")   # (samples, 2048, 1)
    y = np.array(ys).astype("float32")
    return X, y

Xsig, ysig = build_signal_dataset()
# per-window standardisation keeps amplitude out of it, so shape does the work
Xsig = (Xsig - Xsig.mean(axis=1, keepdims=True)) / (Xsig.std(axis=1, keepdims=True) + 1e-6)
Xs_tr, Xs_te, ys_tr, ys_te = train_test_split(Xsig, ysig, test_size=0.25, random_state=0, stratify=ysig)
print("Signal dataset:", Xsig.shape, "| train", len(ys_tr), "test", len(ys_te))
""")

co(r"""
try:
    import tensorflow as tf
    from tensorflow.keras import layers, models
    KERAS = True
except Exception as e:
    KERAS = False
    print("TensorFlow/Keras not available here:", e)
    print("This cell runs as-is in Google Colab. Skipping CNN/LSTM training locally.")
""")

co(r"""
if KERAS:
    tf.random.set_seed(0)
    cnn = models.Sequential([
        layers.Input(shape=(2048, 1)),
        layers.Conv1D(8,  kernel_size=16, strides=4, activation="relu"),
        layers.MaxPooling1D(4),
        layers.Conv1D(16, kernel_size=8,  activation="relu"),
        layers.GlobalMaxPooling1D(),
        layers.Dense(16, activation="relu"),
        layers.Dense(1,  activation="sigmoid"),
    ])
    cnn.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    cnn.summary()
    hist_cnn = cnn.fit(Xs_tr, ys_tr, validation_split=0.2, epochs=8, batch_size=32, verbose=1)
    acc = cnn.evaluate(Xs_te, ys_te, verbose=0)[1]
    print(f"\nCNN accuracy on unseen vibration windows: {acc:.1%}")
    print("The CNN reads the raw signal the Random Forest could not touch.")
""")

# ---------------------------------------------------------------- 12. LSTM
md(r"""
## 12 · LSTM on the degradation trend → Remaining Useful Life

**Mechanical activity.** A single vibration reading barely tells you anything. The **trend** does: a
level creeping up over two weeks means a bearing is degrading; the same level, steady for a year, means
the machine just runs rough. Order and history are the diagnosis.

**The challenge.** The tabular model sees one row and has no memory of yesterday — it cannot tell a
rising trend from a flat one.

**The AI connection.** An **LSTM** reads readings in order and carries a memory of what came before, so
it answers not just *is it failing* but *how long have we got* — the remaining useful life.
""")

co(r"""
def make_degradation(weeks=40, seed=11):
    # flat, then accelerating rise toward the failure limit
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, weeks)
    trend = 2.0 + 0.4*t + 6.0*(t**3.2) + rng.normal(0, 0.18, weeks)
    return trend

LIMIT = 8.0   # failure threshold, mm/s
WEEKS = 40
WIN   = 6     # weeks of history per sequence

def build_rul_dataset(n_machines=300, seed=0):
    rng = np.random.default_rng(seed)
    Xs, ys = [], []
    for m in range(n_machines):
        trend = make_degradation(WEEKS, seed=int(rng.integers(0, 1e6)))
        fail_wk = np.argmax(trend >= LIMIT) if (trend >= LIMIT).any() else WEEKS
        for start in range(0, fail_wk - WIN):
            Xs.append(trend[start:start + WIN])
            ys.append(fail_wk - (start + WIN))       # weeks of useful life left
    X = np.array(Xs)[..., np.newaxis].astype("float32")
    y = np.array(ys).astype("float32")
    return X, y

Xr, yr = build_rul_dataset()
Xr_tr, Xr_te, yr_tr, yr_te = train_test_split(Xr, yr, test_size=0.25, random_state=0)
print("RUL dataset:", Xr.shape, "| target = weeks of useful life remaining")
""")

co(r"""
if KERAS:
    tf.random.set_seed(0)
    lstm = models.Sequential([
        layers.Input(shape=(WIN, 1)),
        layers.LSTM(24),
        layers.Dense(16, activation="relu"),
        layers.Dense(1),                       # regression: weeks remaining
    ])
    lstm.compile(optimizer="adam", loss="mse", metrics=["mae"])
    hist_lstm = lstm.fit(Xr_tr, yr_tr, validation_split=0.2, epochs=15, batch_size=32, verbose=1)
    mae = lstm.evaluate(Xr_te, yr_te, verbose=0)[1]
    print(f"\nLSTM mean error on remaining useful life: {mae:.1f} weeks")
""")

# ---------------------------------------------------------------- 13. training / loss curves
md(r"""
## 13 · Training — watching the loss fall

**The learning loop, run thousands of times:** the model predicts, compares to the known outcome, and
nudges every weight to be a little less wrong. The **loss** measures how wrong it is.

The loss falls fast, then flattens. More epochs on the same machines only memorise them, so you stop
when the held-out (validation) loss stops improving — that is early stopping.
""")

co(r"""
if KERAS:
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.4))
    ax[0].plot(hist_cnn.history["loss"], label="train", color="#4fc3f7")
    ax[0].plot(hist_cnn.history["val_loss"], label="validation", color="#ffb74d")
    ax[0].set_title("CNN training loss"); ax[0].set_xlabel("epoch"); ax[0].legend()
    ax[1].plot(hist_lstm.history["loss"], label="train", color="#4fc3f7")
    ax[1].plot(hist_lstm.history["val_loss"], label="validation", color="#ffb74d")
    ax[1].set_title("LSTM training loss"); ax[1].set_xlabel("epoch"); ax[1].legend()
    plt.tight_layout(); plt.show()
else:
    # sklearn ANN exposes a loss curve too — same idea, no TensorFlow needed
    plt.plot(ann.loss_curve_, color="#4fc3f7")
    plt.title("Neural-net training loss (sklearn ANN)"); plt.xlabel("epoch"); plt.ylabel("loss")
    plt.tight_layout(); plt.show()
""")

# ---------------------------------------------------------------- 14. evaluation
md(r"""
## 14 · Evaluation — the confusion matrix

**Mechanical activity.** Audit the model the way you would audit a maintenance contractor: line up every
call against what actually happened, and count.

**The challenge.** Four outcomes, and lumping them together hides the one that matters:

- Called healthy, stayed healthy — fine
- Called failing, it failed — caught it
- Called failing, nothing happened — a false alarm, a wasted callout
- **Called healthy, and it failed — the costly miss: unplanned downtime**

**The AI connection.** Never quote accuracy alone. A model that calls everything healthy scores well on
accuracy and misses every real failure. The bottom-left box is what the whole system exists to prevent.
""")

co(r"""
pred = rf.predict(X_te)
cm = confusion_matrix(y_te, pred)
tn, fp, fn, tp = cm.ravel()

ConfusionMatrixDisplay(cm, display_labels=["healthy", "failure"]).plot(cmap="Blues", colorbar=False)
plt.title("Reliability audit on the sealed test machines"); plt.show()

print(f"Overall accuracy      : {accuracy_score(y_te, pred):.1%}")
print(f"Missed failures (FN)  : {fn}   <- the costly box: unplanned downtime")
print(f"False alarms   (FP)   : {fp}   <- wasted callouts")
""")

# ---------------------------------------------------------------- 15. fusion
md(r"""
## 15 · Fusion — one prioritized work order

**Mechanical activity.** Every reliability centre has a control room. The engineer in the middle does
not act on any one feed — they cross-reference the readings, the vibration analysis, and the asset's
criticality.

**The challenge.** Each feed alone is close to noise. A rising reading may be a hot day; a signal
pattern may be one rough window; a trend on a non-critical spare can wait. A system that alarms on any
one gets switched off in a fortnight.

**The AI connection.** Fuse them. Elevated tabular risk **and** a bearing-fault pattern **and** a
two-week trend on a **critical** asset is not three weak signals — it is one work order with a deadline.
Several models, one decision, one engineer who acts.
""")

co(r"""
def fusion_engine(reading_risk, cnn_fault, rul_weeks, criticality):
    # Combine the branches into one prioritized action.
    #   reading_risk : 0..1 failure probability from the tabular ANN/RF
    #   cnn_fault    : bool, CNN flagged a fault pattern in the raw signal
    #   rul_weeks    : estimated remaining useful life (weeks) from the LSTM
    #   criticality  : 'Critical' | 'Standard' | 'Spare'
    crit_w = {"Critical": 1.0, "Standard": 0.7, "Spare": 0.4}[criticality]
    urgency = (0.4*reading_risk + 0.3*(1.0 if cnn_fault else 0.0)
               + 0.3*(1 - min(rul_weeks, 26)/26)) * crit_w
    if urgency > 0.60:
        action = f"WORK ORDER - raise now (act within {rul_weeks:.0f} weeks)"
    elif urgency > 0.35:
        action = "PLAN - schedule inspection at next planned stop"
    else:
        action = "MONITOR - keep watching"
    return round(urgency, 2), action

# Pump P-12: a critical asset with three converging signals
print(fusion_engine(reading_risk=0.82, cnn_fault=True, rul_weeks=3, criticality="Critical"))
# A non-critical spare showing mild risk
print(fusion_engine(reading_risk=0.55, cnn_fault=False, rul_weeks=18, criticality="Spare"))
""")

# ---------------------------------------------------------------- 16. dashboard
md(r"""
## 16 · The predictive maintenance dashboard — the business case

**Mechanical activity.** The screen the plant manager opens: every machine, coloured by health, ranked
by how soon it needs attention.

**The business case.** None of the engineering matters to the business until it is a number a manager
acts on: which machine, how urgent, and how many hours of unplanned downtime were avoided. Planned
intervention on an early-caught fault costs a fraction of the unplanned outage it prevents.
""")

co(r"""
# A small live fleet, scored and ranked by priority.
rng = np.random.default_rng(5)
n = 12
types = rng.choice(["Motor", "Pump", "Compressor", "CNC spindle"], n)
vib   = np.round(np.abs(rng.normal(3.5, 2.2, n)), 1)
temp  = np.round(rng.normal(72, 14, n), 0)
oil   = rng.integers(30, 95, n)
rul   = np.clip((8.0 - vib) / 0.35 + rng.normal(0, 3, n), 0.5, 40).round(0)
health = np.clip(100 - vib*9 - (temp-60)*0.6 - (70-oil)*0.5, 2, 99).round(0)
crit  = rng.choice(["Critical", "Standard", "Spare"], n, p=[0.35, 0.45, 0.2])
crit_w = np.array([{"Critical":1.0,"Standard":0.7,"Spare":0.4}[c] for c in crit])

priority = np.round((100-health)/100*crit_w + (1 - rul/40)*0.3, 2)
fleet = pd.DataFrame({
    "Machine": [f"{t[0]}-{i}" for i, t in enumerate(types)],
    "Type": types, "Health": health, "Vibration": vib,
    "RUL_weeks": rul, "Criticality": crit, "Priority": priority,
}).sort_values("Priority", ascending=False).reset_index(drop=True)
fleet
""")

co(r"""
# Downtime-avoided business case
failures_caught_per_month = 6
avg_outage_hours          = 14        # unplanned outage avoided per early catch
downtime_cost_per_hour    = 5000      # $

hours_saved = failures_caught_per_month * avg_outage_hours
money_saved = hours_saved * downtime_cost_per_hour
print(f"Downtime avoided : {hours_saved} h / month")
print(f"Cost avoided     : ${money_saved:,.0f} / month  (${money_saved*12:,.0f} / year)")
""")

md(r"""
## Summary — the whole pipeline

You built a predictive-maintenance system stage by stage: **sense → clean → prepare → model → CNN →
LSTM → evaluate → fuse → serve.** Each AI method appeared because a maintenance task ran into something
one engineer could not do by hand:

- **Machine learning** weighs the seven *named* readings an engineer already defined.
- **The CNN** reads the *raw signal* no one can reduce to a rule.
- **The LSTM** reads the *trend* a single snapshot cannot show, and estimates remaining useful life.
- **Fusion** turns several weak signals into one prioritized work order.

The engineer stays in charge throughout. The system notices; the engineer decides — and the plant runs
more reliably for it.
""")

# ---------------------------------------------------------------- assemble
nb = new_notebook(cells=cells)
nb.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "colab": {"provenance": []},
}
out = "Predictive_Maintenance_DL.ipynb"
with open(out, "w", encoding="utf-8") as f:
    nbf.write(nb, f)

# validate
nb2 = nbf.read(out, as_version=4)
nbf.validate(nb2)
print(f"Wrote {out} | cells: {len(nb2.cells)} | nbformat.validate: OK")
