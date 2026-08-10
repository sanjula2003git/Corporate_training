"""
Builds Hospital_Alarm_Fatigue_Manager.ipynb from nbformat cells.
Run:  py -3.13 build_nb.py

House style for this one: SIMPLE ENGLISH. Short sentences, everyday words, and an
explanation next to anything a beginner would not already know. It is deliberately
plainer than the Smart Construction notebook.

The notebook is standalone (Colab): it builds the whole virtual ward inline, so
there is no CSV to download and nothing to import from this file.

NOTE for future editors:
  * inside co(...) cells use only single-line "..." docstrings or # comments. A
    triple-quoted docstring would close the outer r-string and break this script.
  * build Keras models with the FUNCTIONAL api (Keras 3 Sequential has no .output).
  * the prose quotes numbers the cells print. After any change, re-run the smoke
    test and re-check every number written in markdown.
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

cells = []
def md(t):  cells.append(new_markdown_cell(t.strip("\n")))
def co(t):  cells.append(new_code_cell(t.strip("\n")))


# ============================================================ TITLE
md(r"""
# Hospital Alarm-Fatigue Manager

### Teaching AI through the alarms on a hospital ward

A patient monitor beeps. A nurse walks over. Nothing is wrong. The probe had slipped off the finger.

This happens again, and again, and again. On a real ward a monitored patient can set off **hundreds of
alarms a day**, and the large majority of them need no action at all. After a while people stop reacting.
That is called **alarm fatigue**, and it is dangerous, because somewhere inside all that noise there is one
alarm that really matters.

**The problem we are solving is not "can we predict who gets sick".**
It is harder and more useful:

> A nurse has a limited amount of attention. We are allowed to interrupt that nurse **five times an hour**
> for the whole ward. Which five?

That question is what this notebook answers.

---

### What we will build

A virtual ward of **20 patients**. Every 2 minutes each patient gives us seven pieces of information:

| What we measure | What it means in plain words |
|---|---|
| Heart rate | how many times the heart beats in a minute |
| Oxygen saturation (SpO₂) | how full of oxygen the blood is, as a percentage |
| Respiratory rate | how many breaths the patient takes in a minute |
| Blood pressure | the pressure in the arteries when the heart squeezes |
| Temperature | body temperature in °C |
| Sensor quality | how much we trust the reading right now, from 0 to 1 |
| Recent medicine | what drug was given, and how long ago |

Then we build **five systems** that watch that ward, and we measure which one a nurse would actually want.

| # | System | The idea in one line |
|---|---|---|
| 1 | Simple limits | beep whenever a number goes outside a fixed range |
| 2 | Risk score | add up points for each abnormal number, alert on the total |
| 3 | Random forest | let a machine learn the pattern from past days |
| 4 | LSTM | a deep learning model that reads the last hour as a story |
| 5 | Attention-budget optimizer | rank everything, then spend five alerts an hour wisely |

### How we will judge them

Five measurements, all of them things a ward sister would ask about:

1. **Critical events missed** — how many patients got seriously ill with no alert. The number that matters most.
2. **Early warning** — how many minutes before the crisis did the first alert arrive.
3. **False alarms** — how many alerts went out about a patient who was fine.
4. **Nurse workload** — alerts per hour, and minutes of nurse time per hour.
5. **Response time** — how long a patient waited from the alert until a nurse actually arrived.

### The order we work in

1. The problem: too many alarms
2. Our ward, and the seven numbers
3. Building the virtual ward
4. A first look at three patients
5. The five actions the system can choose
6. The rule that changes everything: five alerts an hour
7. The four days we will judge on
8. **Model 1** — simple limits
9. Where all those false alarms come from
10. Turning raw readings into useful clues
11. **Model 2** — a risk score
12. **Model 3** — a random forest
13. What deep learning adds
14. **Model 4** — an LSTM
15. Which model ranks the risk best
16. **Model 5** — the attention-budget optimizer
17. Watching one patient, minute by minute
18. The nurse's shift: workload and response time
19. The scoreboard
20. What the system still gets wrong
21. Summary
""")


# ============================================================ SETUP
md(r"""
## Setup

Colab already has everything we need. If you run this somewhere else, remove the `#` on the install line.

TensorFlow is used for the LSTM in section 14. If it is missing, the notebook uses a smaller neural network
from scikit-learn instead, so **every section still produces a result**.
""")

co(r"""
# !pip install numpy pandas scikit-learn matplotlib tensorflow

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score

# One seed, so you get the same ward every time you run the notebook.
np.random.seed(7)
rng = np.random.default_rng(7)

plt.rcParams["figure.figsize"] = (9.5, 3.4)
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.25

# The colours used all the way through.
BLUE, ORANGE, GREEN, RED, GREY, PURPLE = "#1976d2", "#ef6c00", "#2e7d32", "#c62828", "#90a4ae", "#6a1b9a"

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    tf.random.set_seed(7)
    keras.utils.set_random_seed(7)
    # Ask TensorFlow to give the same answer every run, so your numbers match the text.
    tf.config.experimental.enable_op_determinism()
    KERAS = True
except Exception as err:
    KERAS = False
    print("TensorFlow not found - a smaller scikit-learn network will be used instead.")

print("Ready.  Deep learning library available:", KERAS)
""")


# ============================================================ 1. THE PROBLEM
md(r"""
## 1 · The problem: too many alarms

Here is the shape of the problem, before any AI.

A monitor is built to be **safe on its own**. It does not know the patient, so it beeps at anything unusual.
That is the right choice for one patient in an operating theatre. It is the wrong choice for twenty patients
on a ward with two nurses, because the alarms arrive faster than anyone can check them.

Three things go wrong at once:

- **Noise.** A finger probe slips, an ECG sticker peels off, the patient scratches their nose. The number on
  the screen jumps, the monitor beeps, and the patient is completely fine.
- **Medicine.** A patient is given a nebuliser for their breathing. That drug speeds the heart up on purpose.
  The monitor does not know a drug was given, so it beeps.
- **Real illness, arriving slowly.** A patient with an infection gets gradually worse over two hours. Every
  single reading looks *almost* normal. The monitor sees nothing wrong until the patient is already in trouble.

So the monitor is loud about the things that do not matter, and quiet about the thing that does.

The chart below is the whole notebook in one picture: as alarms per hour goes up, the share that are real
goes down, and the chance a nurse actually walks over goes down with it.
""")

co(r"""
# A simple illustration of alarm fatigue. These are not measurements - they are drawn to show the shape
# of the problem before we build anything.
alarms_per_hour = np.arange(1, 41)

# The real emergencies do not become more common just because the monitor is louder.
real_per_hour = 0.35
share_real = np.clip(real_per_hour / alarms_per_hour, 0, 1)

# The more often people are interrupted for nothing, the less they trust the next beep.
trust = np.exp(-alarms_per_hour / 9.0)

fig, ax = plt.subplots(1, 2, figsize=(11, 3.4))
ax[0].plot(alarms_per_hour, 100 * share_real, color=BLUE, lw=2)
ax[0].set_title("Share of alarms that are real")
ax[0].set_xlabel("alarms per hour on the ward")
ax[0].set_ylabel("% of alarms that matter")

ax[1].plot(alarms_per_hour, 100 * trust, color=RED, lw=2)
ax[1].set_title("Chance a nurse checks the next beep")
ax[1].set_xlabel("alarms per hour on the ward")
ax[1].set_ylabel("% checked")
plt.tight_layout()
plt.show()

print("The goal of this notebook: stay on the left of both charts, without missing anyone.")
""")

md(r"""
**Read it like this.** Being louder does not create more emergencies. It only buries the ones you have.
A system that sends 40 alerts an hour is not 8 times safer than one that sends 5. It is usually less safe.
""")


# ============================================================ 2. THE WARD
md(r"""
## 2 · Our ward, and the seven numbers

Twenty patients. Each one is wired to a monitor that reports every 2 minutes for 12 days.

Before we write any code, it helps to know what each number means and roughly what counts as normal.

| Measurement | Normal range for an adult | Why it changes |
|---|---|---|
| **Heart rate** | 60–100 beats/min | goes up with fever, pain, fear, blood loss, some drugs |
| **SpO₂** | 95–100 % | goes down when the lungs are struggling |
| **Respiratory rate** | 12–20 breaths/min | the *earliest* warning sign of nearly everything |
| **Blood pressure** | about 110–140 (top number) | falls late, when the body can no longer compensate |
| **Temperature** | 36.1–37.5 °C | goes up with infection |

Two extra pieces of information are what make this problem solvable at all:

- **Sensor quality (0 to 1).** The monitor knows when a signal looks poor — weak pulse, too much movement,
  a lead that has come off. A frightening number with poor quality behind it is usually not a frightening patient.
- **Recent medicine.** If a nurse gave a drug 10 minutes ago that is *supposed* to speed the heart up, then a
  fast heart is expected, not alarming.

A plain monitor ignores both. Our models will not.

### Two details we keep, because real wards have them

- **Blood pressure is not continuous.** A cuff inflates about every 16 minutes. In between, the number on the
  screen is old. We keep track of *how old* it is.
- **Respiratory rate is the best early warning and the worst measured.** It comes from a chest sticker that
  comes loose often. So the most useful number is also the noisiest one.
""")

co(r"""
N_PATIENTS   = 20          # patients on the ward
N_DAYS       = 12          # days of monitoring
DT           = 2           # minutes between readings
PER_DAY      = 24 * 60 // DT
EVENT_CHANCE = 0.30        # chance a patient starts to get seriously ill on a given day
ALERT_BUDGET = 5           # alerts we are allowed to send per hour, for the whole ward

print(f"{N_PATIENTS} patients, {N_DAYS} days, one reading every {DT} minutes.")
print(f"That is {N_PATIENTS * N_DAYS * PER_DAY:,} rows of vital signs in total.")
print(f"Every hour the ward produces {N_PATIENTS * 60 // DT} readings, and we may send {ALERT_BUDGET} alerts.")
""")


# ============================================================ 3. BUILD THE WARD
md(r"""
## 3 · Building the virtual ward

We cannot use real patient data, so we build a ward that behaves like one. Everything below is written to
copy something that actually happens on a hospital ward.

**Each patient has their own normal.** One person sits at 62 beats per minute all week, another at 88. Both
are healthy. This matters: a fixed limit of "120" is far away for one patient and close for the other.

**Six patients live permanently near a limit.** Two have a fast, irregular heart that sits around 112 all
week. Two have long-term lung disease and live at 90 % oxygen. Two simply run a low blood pressure and always
have. **None of them is ill.** Every ward has these patients, and every ward has quietly learned to ignore
their bed — which is the most dangerous habit in the building, because those are the patients whose real
deterioration nobody notices.

**Vital signs wander, they do not jump.** Real readings drift up and down slowly. So we build the noise by
smoothing random numbers, instead of using fresh random numbers at every step.

**There is a day/night rhythm.** Heart rate and temperature are lowest around 4 a.m. and highest in the
afternoon. A monitor that ignores this will alarm at the wrong times.

**Medicines change the numbers on purpose.** Five drugs appear on the ward:

| Drug | What it does to the numbers |
|---|---|
| Nebuliser (for breathing) | pushes the **heart rate up** by around 16 |
| Beta blocker | pulls the **heart rate down** by around 14 |
| Opioid pain relief | **slows breathing** and drops SpO₂ slightly |
| Paracetamol | brings the **temperature down** |
| IV fluids | brings the **blood pressure up** |

**Sensors misbehave.** Three kinds of glitch, roughly two dozen times a day per patient — which sounds a lot
until you remember that a monitored patient in a real hospital can set off hundreds of alarms in a day:

| Glitch | What the screen shows | Sensor quality |
|---|---|---|
| Finger probe slips | SpO₂ suddenly reads 62–86 % | drops to about 0.1 |
| Patient moves | heart rate jumps by 35–75 | drops to about 0.3 |
| Breathing lead loose | respiratory rate reads anything from 2 to 44 | drops to about 0.2 |

These last a few minutes and then fix themselves. **This is where most false alarms come from.**

**Some patients genuinely get worse.** On about 30 % of patient-days, one patient begins to deteriorate. It
builds slowly over 80 to 140 minutes and ends at a **crisis point** — the moment the patient needs a doctor
now. Not every one is dramatic: each event gets a random **strength** between 0.45 and 1.10, so some patients
crash hard and others slide gently. The gentle ones are the ones that get missed on a real ward, and they are
in here on purpose. Three patterns:

| Pattern | What happens |
|---|---|
| Infection | temperature up, heart rate up, breathing fast, blood pressure falling |
| Breathing failure | SpO₂ falling, breathing very fast, heart rate up |
| Bleeding | heart rate up sharply, blood pressure falling sharply, SpO₂ normal |

Notice the last one. **A bleeding patient can have a perfect oxygen level.** Any system that watches only
SpO₂ will miss them completely.

> **One honest note.** A real general ward has far fewer emergencies than this. We made the ward busier on
> purpose, so that there are enough events to compare methods fairly. Everything else is built to behave
> realistically.
""")

co(r"""
# --- what each drug does to the numbers, and how long the effect lasts (minutes) ---
MEDS = {
    "nebuliser":    dict(hr=+16., rr=+2.0, spo2=+0.5, sbp=  0., temp= 0.0, lasts= 45),
    "beta blocker": dict(hr=-14., rr= 0.0, spo2= 0.0, sbp= -6., temp= 0.0, lasts=240),
    "opioid":       dict(hr= -4., rr=-4.5, spo2=-1.8, sbp= -4., temp= 0.0, lasts=150),
    "paracetamol":  dict(hr= -4., rr= 0.0, spo2= 0.0, sbp=  0., temp=-0.8, lasts=180),
    "iv fluids":    dict(hr= -5., rr= 0.0, spo2= 0.0, sbp=+10., temp= 0.0, lasts=120),
}
MED_NAMES = list(MEDS)

# --- how much each vital sign moves by the time the patient reaches the crisis point ---
TROUBLE = {
    "infection": dict(hr=+38., rr=+12., spo2=-4.0, sbp=-30., temp=+1.7),
    "breathing": dict(hr=+24., rr=+15., spo2=-9.0, sbp= -8., temp=+0.3),
    "bleeding":  dict(hr=+42., rr= +8., spo2=-2.0, sbp=-38., temp=-0.3),
}
TROUBLE_NAMES = list(TROUBLE)

# Six of the twenty patients are permanently close to a monitor limit.
CHRONIC = ["fast heart", "low oxygen", "low pressure", "fast heart", "low oxygen", "low pressure"]


def wander(n, sd, k=11):
    "Slow drifting noise. Real vital signs wander; they do not jump at every reading."
    w = rng.normal(0, sd, n + k)
    return np.convolve(w, np.ones(k) / k, mode="same")[:n] * np.sqrt(k)


def build_ward():
    "Create the whole ward: every patient, every day, every reading."
    parts = []
    minute_of_day = np.arange(PER_DAY) * DT
    clock = minute_of_day / 60.0                       # hour of the day, 0 to 24

    for p in range(N_PATIENTS):
        # Every patient has their own normal. This is the single most important line in the ward.
        base = dict(hr=rng.normal(78, 9), spo2=rng.normal(97, 1.0), rr=rng.normal(16, 2.0),
                    sbp=rng.normal(124, 12), temp=rng.normal(36.8, 0.25))

        # Six patients live permanently near a monitor limit. Every ward has them, and every
        # ward has learned to ignore their bed. This is where nuisance alarms really come from.
        chronic = CHRONIC[p] if p < len(CHRONIC) else ""
        if chronic == "fast heart":
            base["hr"] = rng.normal(112, 5)            # atrial fibrillation
        elif chronic == "low oxygen":
            base["spo2"] = rng.normal(90.5, 0.8)       # long-term lung disease
        elif chronic == "low pressure":
            base["sbp"] = rng.normal(96, 4)            # runs low, and always has

        probe_ok = rng.uniform(0.80, 0.99)             # some probes simply sit badly all week

        for d in range(N_DAYS):
            n = PER_DAY
            # Day and night rhythm: lowest around 4am, highest in the afternoon.
            swing = np.cos(2 * np.pi * (clock - 16) / 24)
            hr   = base["hr"]   + wander(n, 2.2)  + 5.0 * swing
            spo2 = base["spo2"] + wander(n, 0.45)
            rr   = base["rr"]   + wander(n, 0.9)
            sbp  = base["sbp"]  + wander(n, 3.5)  + 4.0 * swing
            temp = base["temp"] + wander(n, 0.12) + 0.25 * swing
            quality = np.clip(probe_ok + wander(n, 0.02), 0, 1)

            # ---------- medicines ----------
            med_name = np.array([""] * n, dtype=object)
            mins_since_med = np.full(n, 999.0)
            starts = sorted(int(s) for s in rng.integers(0, n - 30, size=rng.integers(2, 6)))
            for start in starts:
                name = MED_NAMES[rng.integers(0, len(MED_NAMES))]
                eff = MEDS[name]
                steps = int(eff["lasts"] / DT)
                idx = np.arange(start, min(n, start + steps))
                grow = np.clip((idx - start) / 5.0, 0, 1)            # takes about 10 minutes to work
                fade = 1 - (idx - start) / steps                     # then slowly wears off
                shape = grow * fade
                hr[idx]   += eff["hr"]   * shape
                rr[idx]   += eff["rr"]   * shape
                spo2[idx] += eff["spo2"] * shape
                sbp[idx]  += eff["sbp"]  * shape
                temp[idx] += eff["temp"] * shape
                med_name[idx] = name
                mins_since_med[idx] = (idx - start) * DT

            # ---------- a patient who genuinely gets worse ----------
            trouble = np.zeros(n)
            mins_to_crisis = np.full(n, np.nan)
            kind = ""
            if rng.random() < EVENT_CHANCE:
                kind = TROUBLE_NAMES[rng.integers(0, len(TROUBLE_NAMES))]
                eff = TROUBLE[kind]
                length = int(rng.integers(40, 71))                   # 80 to 140 minutes
                start = int(rng.integers(30, n - length - 40))
                idx = np.arange(start, start + length)
                # Not every patient crashes hard. Some slide gently, and those are the ones
                # that get missed on a real ward.
                strength = rng.uniform(0.45, 1.10)
                eff = {k: v * strength for k, v in eff.items()}
                # Slow at first, then faster. This is why early warning is hard.
                ramp = ((idx - start) / length) ** 1.6
                hr[idx]   += eff["hr"]   * ramp
                rr[idx]   += eff["rr"]   * ramp
                spo2[idx] += eff["spo2"] * ramp
                sbp[idx]  += eff["sbp"]  * ramp
                temp[idx] += eff["temp"] * ramp
                trouble[idx] = 1.0
                mins_to_crisis[idx] = (start + length - idx) * DT
                # After the crisis the medical team takes over and the patient settles again.
                back = np.arange(start + length, min(n, start + length + 30))
                if len(back):
                    fade = 1 - (back - (start + length)) / 30.0
                    hr[back]   += eff["hr"]   * fade
                    rr[back]   += eff["rr"]   * fade
                    spo2[back] += eff["spo2"] * fade
                    sbp[back]  += eff["sbp"]  * fade
                    temp[back] += eff["temp"] * fade

            # ---------- sensor glitches ----------
            artifact = np.zeros(n)
            for _ in range(rng.poisson(26)):
                start = int(rng.integers(0, n - 4))
                idx = np.arange(start, start + int(rng.integers(1, 4)))
                which = rng.integers(0, 3)
                if which == 0:                                       # finger probe slips off
                    spo2[idx] = rng.uniform(62, 86)
                    quality[idx] = rng.uniform(0.05, 0.30)
                elif which == 1:                                     # patient moves, ECG picks up muscle noise
                    hr[idx] += rng.uniform(35, 75)
                    quality[idx] = rng.uniform(0.15, 0.45)
                else:                                                # breathing lead comes loose
                    rr[idx] = rng.uniform(2, 44)
                    quality[idx] = rng.uniform(0.05, 0.35)
                artifact[idx] = 1.0

            # ---------- blood pressure is measured, not streamed ----------
            keep = np.zeros(n, bool)
            keep[::8] = True                                          # a cuff reading every 16 minutes
            bad_cuff = keep & (rng.random(n) < 0.03)                  # a cuff sometimes reads badly
            sbp_meas = np.where(keep, sbp, np.nan)
            sbp_meas[bad_cuff] += rng.normal(0, 22, int(bad_cuff.sum()))
            sbp_obs = pd.Series(sbp_meas).ffill().bfill().to_numpy()
            bp_age = (np.arange(n) % 8) * DT                          # how old the number on the screen is

            # ---------- temperature is taken every 30 minutes ----------
            keep_t = np.zeros(n, bool)
            keep_t[::15] = True
            temp_obs = pd.Series(np.where(keep_t, temp, np.nan)).ffill().bfill().to_numpy()

            parts.append(pd.DataFrame(dict(
                patient=p, day=d, chronic=chronic,
                minute=d * 24 * 60 + minute_of_day,
                hour_of_day=(minute_of_day // 60),
                hr=np.clip(hr, 25, 220),
                spo2=np.clip(spo2, 50, 100),
                rr=np.clip(rr, 2, 60),
                sbp=np.clip(sbp_obs, 50, 240),
                temp=temp_obs,
                quality=quality,
                bp_age=bp_age,
                med=med_name,
                mins_since_med=np.clip(mins_since_med, 0, 999),
                trouble=trouble,
                kind=kind,
                mins_to_crisis=mins_to_crisis,
                artifact=artifact,
            )))
    return pd.concat(parts, ignore_index=True)


ward = build_ward()
print("Rows of monitoring data:", f"{len(ward):,}")
ward.head()
""")

md(r"""
### What the table holds

Most columns are just the readings. Three of them are the **truth**, and we keep them only so we can mark
the models' homework at the end:

- `trouble` — 1 while the patient is genuinely deteriorating, 0 otherwise.
- `mins_to_crisis` — minutes left until the crisis point.
- `artifact` — 1 while a sensor is misbehaving.

**No model is ever allowed to see these three columns.** In a real hospital nobody knows them in advance.
""")

co(r"""
# How much real trouble is there in this ward, and how much noise?
events = (ward[ward.trouble == 1]
          .groupby(["patient", "day"])
          .agg(kind=("kind", "first"), start=("minute", "min"), crisis=("minute", "max"))
          .reset_index())
events["crisis"] = events["crisis"] + DT

print("Serious deterioration events in 12 days :", len(events))
print("Patient-days on the ward                :", N_PATIENTS * N_DAYS)
print()
print(events["kind"].value_counts().to_string())
print()
print(f"Readings taken while a sensor misbehaved : {int(ward.artifact.sum()):,}"
      f"  ({100 * ward.artifact.mean():.1f}% of all readings)")
print(f"Readings taken during real deterioration : {int(ward.trouble.sum()):,}"
      f"  ({100 * ward.trouble.mean():.1f}% of all readings)")
""")

md(r"""
**This is the heart of the difficulty.** Look at those last two lines. The ward spends about **three times as
long with a misbehaving sensor as with a deteriorating patient**. A system that cannot tell the two apart will
spend most of its attention on loose stickers — and that is before we count the six patients whose normal
readings look alarming all week.
""")


# ============================================================ 4. FIRST LOOK
md(r"""
## 4 · A first look at three patients

Three days from the ward, drawn the way a nurse would see them on the screen. Try to decide, by eye, which
one needs a nurse — before you read the answer underneath.
""")

co(r"""
def plot_day(patient, day, title):
    "Draw one patient's day: heart rate, oxygen and breathing, plus the truth underneath."
    part = ward[(ward.patient == patient) & (ward.day == day)]
    hours = (part.minute.to_numpy() - part.minute.min()) / 60.0

    fig, ax = plt.subplots(3, 1, figsize=(10.5, 5.4), sharex=True)
    ax[0].plot(hours, part.hr, color=RED, lw=1.0);   ax[0].set_ylabel("heart rate")
    ax[1].plot(hours, part.spo2, color=BLUE, lw=1.0); ax[1].set_ylabel("SpO2 %")
    ax[2].plot(hours, part.rr, color=GREEN, lw=1.0);  ax[2].set_ylabel("breaths/min")
    ax[2].set_xlabel("hour of the day")

    # Shade the truth so you can check your own guess.
    tr = part.trouble.to_numpy()
    if tr.any():
        for a in ax:
            a.axvspan(hours[tr == 1].min(), hours[tr == 1].max(), color=RED, alpha=0.12)
    art = part.artifact.to_numpy()
    for a in ax:
        for h in hours[art == 1]:
            a.axvline(h, color=GREY, alpha=0.35, lw=0.8)

    ax[0].set_title(title + "     (red band = real deterioration, grey lines = sensor glitch)")
    plt.tight_layout()
    plt.show()


# A quiet day, a day with a real emergency, and a day with a lot of sensor noise.
quiet = (ward.groupby(["patient", "day"])
              .agg(trouble=("trouble", "max"), art=("artifact", "sum")).reset_index())
q = quiet[quiet.trouble == 0].sort_values("art").iloc[0]
n = quiet[quiet.trouble == 0].sort_values("art").iloc[-1]
e = events.iloc[3]

plot_day(int(q.patient), int(q.day), f"Patient {int(q.patient)} - an ordinary day")
plot_day(int(n.patient), int(n.day), f"Patient {int(n.patient)} - a day of bad sensor contact")
plot_day(int(e.patient), int(e.day), f"Patient {int(e.patient)} - real deterioration ({e.kind})")
""")

md(r"""
### What to notice

**The ordinary day** still has spikes. Every one of them is a sensor, not a patient. A monitor with fixed
limits beeps at several of these.

**The bad-sensor day** looks alarming and is not. The spikes are tall, sudden, and last two to six minutes.
They also come with a **collapse in sensor quality**, which is the clue we will teach the models to use.

**The real deterioration** is the quiet one. Inside the red band the lines are not jumping — they are
*leaning*. No single reading looks dramatic until the very end. That is exactly why people miss it, and
exactly what a model can be good at.

> **The rule of thumb for the rest of the notebook:**
> sensor noise is **tall, sudden and short**. Real illness is **small, slow and persistent**.
""")

# ============================================================ 5. THE FIVE ACTIONS
md(r"""
## 5 · The five actions the system can choose

Most AI examples end with a yes/no answer. This one does not, because "is this patient unwell" is not the
decision a ward actually has to make. The real decision is **what to do about it**, and there are five
choices, each costing a different amount of human attention.

| Action | What it means | Nurse time it costs |
|---|---|---|
| **Ignore** | the reading is almost certainly a sensor problem — say nothing | 0 minutes |
| **Repeat the measurement** | take the reading again in a few minutes before deciding | 0 minutes |
| **Keep watching** | nothing to do now, stay alert | 0 minutes |
| **Notify a nurse** | put this patient on the nurse's list | about 8 minutes |
| **Urgent response** | call the emergency team now | about 20 minutes |

Only the bottom two cost anything, and only the bottom two count against our budget.

**Why the top three matter so much.** They are the escape valve. Without them, every worrying reading has to
become an interruption. With them, the system can be suspicious about a hundred things an hour and still only
interrupt a person five times.

**"Repeat the measurement" is the quiet hero.** A slipped probe fixes itself within a few minutes. If we simply
wait four minutes and look again, the frightening number is gone — and it cost nobody anything. This one action
removes a large share of false alarms.

**"Urgent response" ignores the budget on purpose.** A patient who is already in crisis is never put in a
queue to save alert quota. We will check later how often this pushed us over five per hour.
""")

co(r"""
ACTIONS = {
    "ignore":  dict(label="Ignore - probably sensor noise", nurse_minutes=0,  counts_as_alert=False),
    "repeat":  dict(label="Repeat the measurement",         nurse_minutes=0,  counts_as_alert=False),
    "monitor": dict(label="Keep watching",                  nurse_minutes=0,  counts_as_alert=False),
    "notify":  dict(label="Notify a nurse",                 nurse_minutes=8,  counts_as_alert=True),
    "urgent":  dict(label="Urgent response team",           nurse_minutes=20, counts_as_alert=True),
}

for key, a in ACTIONS.items():
    print(f"{a['label']:<38} costs {a['nurse_minutes']:>2} nurse-minutes    "
          f"uses budget: {'yes' if a['counts_as_alert'] else 'no'}")
""")


# ============================================================ 6. THE BUDGET
md(r"""
## 6 · The rule that changes everything: five alerts an hour

Here is the constraint, and it is worth sitting with for a moment.

The ward produces **600 readings every hour** (20 patients, one reading each every 2 minutes). Out of those
600 readings, we may raise **5 alerts**. That is under 1 in 100.

Why five? Because that is roughly what two nurses can absorb while still doing everything else on the ward:

```
2 nurses  ×  60 minutes            = 120 minutes of nurse time per hour
5 alerts  ×  8 minutes each        =  40 minutes  ->  one third of the ward's staff time
```

Push it to 20 alerts an hour and you need 160 minutes of nurse time inside an hour that only has 120. The
queue never empties, and the wait before anyone attends grows all shift. We will see exactly that in section 18.

### This changes what "a good model" means

Normally we would ask: *is this model accurate?*

Here that question is not enough. Suppose two models both give the ward 40 alerts in an hour. One of them is
slightly more accurate. It does not matter — **both fail**, because 35 of those alerts will never be looked at.

The question becomes: **given that only five things can be said, which five?**

That is a ranking-and-budget problem, not just a prediction problem. Models 1 to 4 answer "who is unwell".
Only model 5 answers the question the ward actually asked.
""")


# ============================================================ 7. THE SPLIT
md(r"""
## 7 · The four days we will judge on

Before building anything, we set the exam. The 12 days are cut into three pieces, and each piece has one job.

- **Days 1 to 7 — learning.** The models may study these as much as they like.
- **Day 8 — setting the dials.** Not for learning. This is where we work out *how high to set an alert
  level* so that the ward gets about five alerts an hour. Choosing that on the exam days would be cheating.
- **Days 9 to 12 — the exam.** Nobody looks until the end. Every method is judged here, on the same four days.

Splitting by **time** rather than at random is important. If we shuffled the readings and split randomly,
a model could learn from 10:02 and be tested on 10:04 of the same patient's deterioration. It would look
brilliant and be useless. Real life only ever gives you the past.

We also fix the alert rules that apply to **every** method, so the comparison is fair:

- **One alert per patient per 30 minutes.** A nurse does not need the same warning six times.
- An alert counts as **true** if the patient really was deteriorating at that moment, and **false** otherwise.
- An event counts as **caught** if any alert about that patient arrived between the start of the
  deterioration and the crisis point. Otherwise it is **missed**.
- **Early warning** is how many minutes before the crisis the first alert arrived.
""")

co(r"""
TRAIN_DAYS = list(range(0, 7))     # learning
TUNE_DAYS  = [7]                   # setting the alert levels
TEST_DAYS  = list(range(8, 12))    # the exam
REFRACTORY = 30                    # minutes: never alert about the same patient twice within this time


def split_ward():
    "Cut the ward into learning days, dial-setting days, and exam days."
    tr = ward[ward.day.isin(TRAIN_DAYS)].reset_index(drop=True)
    tu = ward[ward.day.isin(TUNE_DAYS)].reset_index(drop=True)
    te = ward[ward.day.isin(TEST_DAYS)].reset_index(drop=True)
    return tr, tu, te


TRAIN, TUNE, TEST = split_ward()
TEST_HOURS = len(TEST_DAYS) * 24
TUNE_HOURS = len(TUNE_DAYS) * 24
TEST_EVENTS = events[events.day.isin(TEST_DAYS)].reset_index(drop=True)
TUNE_EVENTS = events[events.day.isin(TUNE_DAYS)].reset_index(drop=True)

print(f"Learning days   : {len(TRAIN):,} readings, "
      f"{len(events[events.day.isin(TRAIN_DAYS)])} deterioration events")
print(f"Dial-setting day: {len(TUNE):,} readings, {len(TUNE_EVENTS)} deterioration events")
print(f"Exam days       : {len(TEST):,} readings, {len(TEST_EVENTS)} deterioration events, "
      f"{TEST_HOURS} hours")
print(f"Alerts allowed on the exam days: {TEST_HOURS} hours x {ALERT_BUDGET} = "
      f"{TEST_HOURS * ALERT_BUDGET}")
""")

co(r"""
def to_alerts(df, fire, refractory=REFRACTORY, action="notify"):
    "Turn a yes/no decision at every reading into a tidy list of alerts."
    # `fire` is a True/False array with one entry per row of `df`.
    out = []
    for p, part in df.groupby("patient", sort=False):
        rows = part.index.to_numpy()
        mins = part["minute"].to_numpy()
        hits = np.flatnonzero(fire[rows])
        last = -10 ** 9
        for i in hits:
            if mins[i] - last >= refractory:
                out.append((mins[i], p, rows[i], action))
                last = mins[i]
    return pd.DataFrame(out, columns=["minute", "patient", "row", "action"])


def summarise(name, alerts):
    "Mark one method's homework on the exam days."
    truth = TEST["trouble"].to_numpy()
    real = truth[alerts["row"].to_numpy()] == 1 if len(alerts) else np.zeros(0, bool)

    lead, missed = [], 0
    for e in TEST_EVENTS.itertuples():
        hit = alerts[(alerts.patient == e.patient) &
                     (alerts.minute >= e.start) & (alerts.minute <= e.crisis)]
        if len(hit) == 0:
            missed += 1
        else:
            lead.append(e.crisis - hit.minute.min())

    return dict(model=name,
                alerts_per_hour=round(len(alerts) / TEST_HOURS, 1),
                total_alerts=len(alerts),
                false_alarms=int((~real).sum()),
                pct_false=round(100 * float((~real).mean()), 1) if len(alerts) else 0.0,
                missed_events=missed,
                caught_events=len(TEST_EVENTS) - missed,
                early_warning_min=int(np.median(lead)) if lead else 0)


ALERTS = {}      # every method's alerts get stored here for the final scoreboard
print("Scoring tools ready.")
""")


# ============================================================ 8. MODEL 1
md(r"""
## 8 · Model 1 — simple limits

This is what almost every monitor in every hospital does today. Set a high and a low limit for each number.
If a reading goes outside, beep.

| Measurement | Beep if below | Beep if above |
|---|---|---|
| Heart rate | 45 | 120 |
| SpO₂ | 90 | — |
| Respiratory rate | 8 | 26 |
| Blood pressure (top number) | 90 | 180 |
| Temperature | 35.0 | 38.5 |

It has real strengths. It is instant, it needs no training, and anyone can explain it to a court. Let us see
what it costs.
""")

co(r"""
def breaks_limits(df):
    "The classic monitor rule: is any single number outside its fixed range right now?"
    return ((df.hr < 45) | (df.hr > 120) |
            (df.spo2 < 90) |
            (df.rr < 8) | (df.rr > 26) |
            (df.sbp < 90) | (df.sbp > 180) |
            (df.temp < 35.0) | (df.temp > 38.5)).to_numpy()


fire_limits = breaks_limits(TEST)
ALERTS["1. Simple limits"] = to_alerts(TEST, fire_limits)

row = summarise("1. Simple limits", ALERTS["1. Simple limits"])
print(f"Readings outside the limits : {int(fire_limits.sum()):,}")
print(f"Alerts sent (after grouping): {row['total_alerts']:,}")
print(f"Alerts per hour             : {row['alerts_per_hour']}      (budget is {ALERT_BUDGET})")
print(f"False alarms                : {row['false_alarms']:,}  ({row['pct_false']}% of all alerts)")
print(f"Events caught               : {row['caught_events']} of {len(TEST_EVENTS)}")
print(f"Median early warning        : {row['early_warning_min']} minutes before the crisis")
""")

md(r"""
### The verdict on fixed limits

Look at the numbers together.

It catches most of the emergencies. It does so by alarming three times above what the ward can absorb, and
the overwhelming majority of those alarms are about patients who are perfectly fine.

**This is alarm fatigue, in numbers.** Nobody designed this badly. Each limit on its own is sensible. The
problem is that "sensible for one patient, one reading, one moment" adds up to an unusable ward.

One number here is a trap, and it is worth spotting now rather than at the end. The **early warning** looks
excellent — better than most of the models we are about to build. That is not insight. When you alarm about
nearly everything, some of those alarms are bound to land early by chance. A stopped clock has an impressive
best-case too.

The way to catch that trick is to stop counting alarms and start counting **patients a nurse actually reached
in time**. We will build exactly that measurement in section 18, and this method does not survive it.
""")


# ============================================================ 9. WHERE FALSE ALARMS COME FROM
md(r"""
## 9 · Where all those false alarms come from

Before trying to be cleverer, it is worth finding out what the false alarms actually are. Because we built
this ward, we know the true answer for every single one.
""")

co(r"""
al = ALERTS["1. Simple limits"]
rows = al["row"].to_numpy()

was_trouble  = TEST["trouble"].to_numpy()[rows] == 1
was_artifact = (TEST["artifact"].to_numpy()[rows] == 1) & ~was_trouble
was_chronic  = (TEST["chronic"].to_numpy()[rows] != "") & ~was_artifact & ~was_trouble
was_med      = (TEST["mins_since_med"].to_numpy()[rows] < 60) & ~was_artifact & ~was_trouble & ~was_chronic
was_other    = ~was_trouble & ~was_artifact & ~was_med & ~was_chronic

counts = pd.Series({
    "Real deterioration": int(was_trouble.sum()),
    "Sensor glitch": int(was_artifact.sum()),
    "A patient who always looks like this": int(was_chronic.sum()),
    "Just after a medicine": int(was_med.sum()),
    "Everything else": int(was_other.sum()),
})

plt.figure(figsize=(8.5, 3.0))
plt.barh(counts.index[::-1], counts.values[::-1],
         color=[GREY, GREY, ORANGE, GREY, GREEN][::-1])
plt.xlabel("number of alerts")
plt.title("What the monitor was actually beeping about")
plt.tight_layout()
plt.show()

print(counts.to_string())
print()
print(f"Share of all alerts that were a real problem: {100 * was_trouble.mean():.1f}%")
""")

md(r"""
### Three clues we are throwing away

Almost every false alarm above has a **clue sitting right next to it in the data**, and the monitor is not
looking at any of them:

1. **Sensor quality.** During a glitch the quality score collapses. The monitor beeps at SpO₂ 68 % without
   ever asking "does this signal look trustworthy?"

2. **The patient's own normal.** For six of our patients the alarm is not news. Their heart has been at 112
   all week. The monitor compares them with a textbook instead of with themselves, and beeps every time.

3. **Recent medicine.** A heart rate of 118 twenty minutes after a nebuliser is the drug doing its job. The
   monitor beeps at the number without asking "did we cause this on purpose?"

There is a fourth clue too, and it is about **shape rather than value**: a glitch is tall, sudden and gone in
minutes; illness leans slowly in one direction and stays. A single reading cannot tell them apart. A few
minutes of history can.

That is the whole plan for the next sections: give the model quality, the patient's own normal, medicine,
and history.
""")


# ============================================================ 10. FEATURES
md(r"""
## 10 · Turning raw readings into useful clues

A model is only as good as what you show it. Right now we have raw numbers. We are going to add columns that
answer the questions a good nurse asks without noticing they are asking them.

| New column | The nurse's question it answers |
|---|---|
| `*_smooth` | *ignoring the last odd blip, what is this number really?* |
| `*_usual` | *what is normal **for this patient**?* |
| `*_off` | *how far from their own normal are they now?* |
| `*_d30` | *which way is it moving, and how fast?* |
| `quality_smooth` | *can I trust this signal at all?* |
| `mins_since_med`, med flags | *did we cause this with a drug?* |
| `bp_age` | *how old is the blood pressure on the screen?* |

Three of these deserve a proper explanation.

**Smoothing with the middle value.** For every reading we take the last 5 readings (10 minutes) and keep the
**middle** one. If four readings say 78, 80, 79, 81 and one says 145, the middle value is about 80. The
average would have been 92. Taking the middle value throws sensor spikes away almost for free, and it is the
single cheapest improvement in the whole notebook.

**Each patient's own normal.** We take the middle value over the last 4 hours, ending 30 minutes ago. The
30-minute gap matters: if a patient is deteriorating right now, we do not want their "normal" to quietly
follow them down. Then `hr_off = hr_smooth − hr_usual` says *how far from yourself you are*. A heart rate of
104 is nothing for a patient who lives at 96, and a warning sign for one who lives at 62. **A fixed limit can
never see this. This one column is most of the difference between model 1 and model 3.**

**Direction and speed.** `hr_d30` is the value now minus the value 30 minutes ago. Deterioration has a
direction; sensor noise does not.
""")

co(r"""
def add_features(df):
    "Add the columns that turn raw readings into clues a model can use."
    # 1. Smooth away the spikes: the middle of the last 5 readings (10 minutes).
    g = df.groupby("patient", sort=False)
    for c in ["hr", "spo2", "rr", "quality"]:
        df[c + "_smooth"] = g[c].transform(lambda s: s.rolling(5, min_periods=1).median())

    # 2. What is normal for THIS patient: the middle of the last 4 hours, ending 30 minutes ago.
    g = df.groupby("patient", sort=False)
    for c in ["hr", "spo2", "rr", "sbp", "temp"]:
        df[c + "_usual"] = g[c].transform(
            lambda s: s.shift(15).rolling(120, min_periods=20).median())

    # 3. How far from their own normal are they right now?
    for c in ["hr", "spo2", "rr"]:
        df[c + "_off"] = df[c + "_smooth"] - df[c + "_usual"]
    for c in ["sbp", "temp"]:
        df[c + "_off"] = df[c] - df[c + "_usual"]

    # 4. Which way is it moving? Value now minus value 30 minutes ago.
    g = df.groupby("patient", sort=False)
    for c in ["hr_smooth", "spo2_smooth", "rr_smooth", "sbp", "temp"]:
        df[c + "_d30"] = g[c].transform(lambda s: s - s.shift(15))

    # 5. Did we cause this with a drug?
    df["med_recent"] = (df["mins_since_med"] < 90).astype(int)
    df["med_speeds_heart"]    = ((df["med"] == "nebuliser")    & (df["mins_since_med"] <  60)).astype(int)
    df["med_slows_heart"]     = ((df["med"] == "beta blocker") & (df["mins_since_med"] < 240)).astype(int)
    df["med_slows_breathing"] = ((df["med"] == "opioid")       & (df["mins_since_med"] < 150)).astype(int)
    return df


ward = add_features(ward)

FEATURES = [
    "hr", "spo2", "rr", "sbp", "temp",                       # what the screen says now
    "hr_smooth", "spo2_smooth", "rr_smooth",                 # with the spikes taken out
    "hr_off", "spo2_off", "rr_off", "sbp_off", "temp_off",   # distance from this patient's own normal
    "hr_smooth_d30", "spo2_smooth_d30", "rr_smooth_d30",     # which way things are moving
    "sbp_d30", "temp_d30",
    "quality", "quality_smooth", "bp_age",                   # can we trust the signal
    "mins_since_med", "med_recent",                          # did a drug cause this
    "med_speeds_heart", "med_slows_heart", "med_slows_breathing",
    "hour_of_day",                                           # night or day
]
ward[FEATURES] = ward[FEATURES].fillna(0)

# Rebuild the three sets now that the ward has its new columns.
TRAIN, TUNE, TEST = split_ward()

print(f"{len(FEATURES)} clues per reading.")
print()
print("A deteriorating patient and a sensor glitch, side by side:")
sick  = TEST[(TEST.trouble == 1) & (TEST.mins_to_crisis < 30)]
glitch = TEST[(TEST.artifact == 1) & (TEST.trouble == 0)]
look = ["hr_off", "rr_off", "spo2_off", "hr_smooth_d30", "quality"]
print(pd.DataFrame({"real deterioration": sick[look].mean().round(2),
                    "sensor glitch": glitch[look].mean().round(2)}).to_string())
""")

md(r"""
### Read that little table

The two columns are the difference between a patient and a loose wire.

During real deterioration, several distances-from-normal move together, and **sensor quality stays high** —
the machine is working properly, the patient is not.

During a glitch, the numbers can be extreme, but **sensor quality falls through the floor**, and the other
measurements do not agree. A patient whose oxygen has genuinely crashed does not keep breathing calmly at 16
breaths a minute.

That is the pattern the next three models get to learn. It was always in the data. Nobody was showing it to
the monitor.
""")


# ============================================================ 11. MODEL 2
md(r"""
## 11 · Model 2 — a risk score

Hospitals already have a better answer than fixed limits, and it does not involve computers at all. It is
called an **early warning score**, and a version of it hangs on the wall of most UK wards.

The idea is simple. Instead of asking "is any one number outside its range", give **points** for how abnormal
each number is, and add them up.

| Points | Meaning |
|---|---|
| 0 | normal |
| 1 | slightly off |
| 2 | clearly off |
| 3 | very abnormal |

Add the five scores. A total of 5 or more means the patient needs looking at. 7 or more means urgent.

**Why this beats fixed limits.** One strange number gives at most 3 points, which is not enough to alert. So a
single slipped probe stays quiet. But a patient who is genuinely deteriorating is usually abnormal in
*several* ways at once — fast breathing **and** fast heart **and** falling pressure — and those points add up.

Requiring agreement between measurements is a real idea, and it costs nothing to compute.
""")

co(r"""
def risk_score(df):
    "A points-based early warning score, in the style of the ones used on real wards."
    rr, sp, tp = df.rr.to_numpy(), df.spo2.to_numpy(), df.temp.to_numpy()
    bp, hr = df.sbp.to_numpy(), df.hr.to_numpy()
    s = np.zeros(len(df))
    s += np.select([rr <= 8, rr <= 11, rr <= 20, rr <= 24], [3, 1, 0, 2], default=3)
    s += np.select([sp <= 91, sp <= 93, sp <= 95], [3, 2, 1], default=0)
    s += np.select([tp <= 35.0, tp <= 36.0, tp <= 38.0, tp <= 39.0], [3, 1, 0, 1], default=2)
    s += np.select([bp <= 90, bp <= 100, bp <= 110, bp <= 219], [3, 2, 1, 0], default=3)
    s += np.select([hr <= 40, hr <= 50, hr <= 90, hr <= 110, hr <= 130], [3, 1, 0, 1, 2], default=3)
    return s


TEST["score"] = risk_score(TEST)
a2 = to_alerts(TEST, (TEST["score"] >= 5).to_numpy())
# A score of 7 or more is treated as an emergency, exactly as it would be on a real ward.
a2.loc[TEST["score"].to_numpy()[a2["row"].to_numpy()] >= 7, "action"] = "urgent"
ALERTS["2. Risk score"] = a2

r1 = summarise("1. Simple limits", ALERTS["1. Simple limits"])
r2 = summarise("2. Risk score", ALERTS["2. Risk score"])
print(pd.DataFrame([r1, r2]).set_index("model").to_string())
""")

md(r"""
### The verdict on the risk score

Compare the two rows carefully, because the result is not a clean win and it is more interesting for that.

**It bought quiet.** Demanding that several measurements agree removes most of the single-sensor false alarms
in one stroke — a large drop in alerts, with no training data and no machine learning at all. It lands close
to the budget rather than miles past it.

**It cost time, and it cost patients.** Points are only awarded once a number is *already* clearly abnormal.
A patient sliding downhill but still inside the normal ranges scores zero. So the score speaks **later** than
fixed limits did, and it **misses more events**, not fewer. Being quieter is not the same as being better.

Both of those come from the same design choice, and you cannot keep one without the other. Waiting for
several measurements to agree is exactly what silences the noise, and exactly what makes it late.

This is the honest ceiling of hand-written rules. To speak earlier we need something that reacts to *small*
changes in *several* places at once — and that is a job for a model that has seen a lot of patients.
""")

# ============================================================ 12. MODEL 3
md(r"""
## 12 · Model 3 — a random forest

Models 1 and 2 were rules written by people. Model 3 is the first one that **learns the rules from the data**.

### What a decision tree is

A decision tree is a list of yes/no questions, like the flowchart at the front of a manual:

```
is rr_off above 3.5 ?
├── no  -> is hr_off above 12 ?
│          ├── no  -> probably fine
│          └── yes -> is quality_smooth below 0.6 ?
│                     ├── yes -> probably a sensor problem
│                     └── no  -> worth a look
└── yes -> is sbp_off below -12 ?
           ├── no  -> worth a look
           └── yes -> this patient is deteriorating
```

Nobody writes those questions. The computer tries every column at every cut point and keeps whichever
question best separates the deteriorating readings from the ordinary ones. Then it does the same again inside
each branch.

### Why a *forest*

One tree learns the training days too literally. It will happily invent a rule like "heart rate 103.7 on a
Tuesday means trouble", because that happened once.

So we grow **150 trees**, each on a random part of the data with a random part of the columns, and let them
vote. One tree's private superstition is outvoted by 149 others. The share of trees voting "deteriorating"
becomes our **risk score, between 0 and 1**.

### What it can do that the rules could not

It sees all 27 clues at once, including the ones the monitor ignored — **sensor quality**, **recent
medicine**, and the one nobody could hand-write: **how far this patient is from their own normal**.

### Where do we put the alert level?

The forest gives a risk between 0 and 1. Somebody still has to pick the line. We do it the way a hospital
would: **set it as high as it will go while still catching the deteriorations we saw on the dial-setting day.**
Missing a patient is the thing a ward will not accept, so sensitivity wins the argument.

To stop one freak case dragging the line to the floor, we aim to catch **three quarters** of the events on
day 8, and we never look at the exam days while choosing.

Watch what that costs.
""")

co(r"""
Xtr, ytr = TRAIN[FEATURES].to_numpy(np.float32), TRAIN["trouble"].to_numpy().astype(int)
Xtu      = TUNE[FEATURES].to_numpy(np.float32)
Xte, yte = TEST[FEATURES].to_numpy(np.float32),  TEST["trouble"].to_numpy().astype(int)

# class_weight tells the forest that deteriorating readings are rare and must not be ignored.
forest = RandomForestClassifier(n_estimators=150, max_depth=14, min_samples_leaf=25,
                                class_weight="balanced_subsample", n_jobs=-1, random_state=7)
forest.fit(Xtr, ytr)

TUNE["risk_rf"] = forest.predict_proba(Xtu)[:, 1]
TEST["risk_rf"] = forest.predict_proba(Xte)[:, 1]


def pick_sensitive_level(df, risk_col, evs, catch=0.75):
    "The highest alert level that still catches this share of the deteriorations on the dial day."
    peaks = []
    for e in evs.itertuples():
        part = df[(df.patient == e.patient) & (df.minute >= e.start) & (df.minute <= e.crisis)]
        if len(part):
            peaks.append(float(part[risk_col].max()))
    if not peaks:
        return 0.5
    peaks = np.sort(np.array(peaks))
    return float(peaks[int((1 - catch) * len(peaks))])


RF_LEVEL = pick_sensitive_level(TUNE, "risk_rf", TUNE_EVENTS, catch=0.75)
print(f"Alert level chosen on the dial-setting day: risk >= {RF_LEVEL:.3f}")
print()

ALERTS["3. Random forest"] = to_alerts(TEST, (TEST["risk_rf"] >= RF_LEVEL).to_numpy())
print(pd.DataFrame([summarise(k, v) for k, v in ALERTS.items()]).set_index("model").to_string())
""")

co(r"""
# Which clues did the forest actually lean on?
imp = pd.Series(forest.feature_importances_, index=FEATURES).sort_values()[-12:]

plt.figure(figsize=(8.5, 4.0))
plt.barh(imp.index, imp.values, color=BLUE)
plt.xlabel("how much the forest relies on this clue")
plt.title("The 12 clues the random forest uses most")
plt.tight_layout()
plt.show()

print(imp[::-1].round(3).to_string())
""")

md(r"""
### Read the importance chart, then read the table

The chart says what the forest learned to care about. The columns near the top are mostly the
**distance-from-own-normal** and **direction-of-travel** clues we built in section 10 — not the raw readings a
fixed limit looks at. The model worked out on its own that *a change in this patient* beats *a number on a
chart*.

Now the table, and the result is not what most people expect.

Look at the false alarms. The forest is **dramatically** more accurate than either rule when it does speak —
almost everything it says is worth hearing. That is the machine learning working.

Now look at the alerts per hour, and compare it with our budget of five. **The forest is barely speaking at
all.** It is using a tiny fraction of the attention the ward set aside for it. And with all that quiet, it
*still* misses events.

This is the failure that fixed alert levels always have, and it is worth being precise about it. The level was
chosen once, on one day, and then never changed. So it is **wrong in both directions**:

- On a quiet night, when the ward has attention to spare, the level is too high. Patients slide past
  unmentioned while the budget sits unused.
- On a terrible night, when everything happens at once, the same level is too low, and the ward gets buried.

A single number cannot be right in both situations, because the right answer does not depend only on the
patient. It depends on **what else is going on**.

Which also means counting a model's alerts at one dial setting tells us almost nothing about the model. The
real question is section 15's: **when this model puts patients in order of risk, are the genuinely sick ones
near the top?** If they are, we can spend our five alerts well. If they are not, no dial setting will save us.
""")


# ============================================================ 13. WHAT DL ADDS
md(r"""
## 13 · What deep learning adds

Before the next model, the shortest useful explanation of deep learning.

### One neuron

A neuron does two things:

1. **Multiply and add.** Each input gets a weight — how much this input matters. Multiply, add them together,
   add one extra number called the bias.
2. **Squash.** Push the result through a curve so the answer comes out between 0 and 1.

That is it. One neuron is a weighted opinion poll among the inputs.

### Learning

At the start the weights are random, so the answer is nonsense. We then show the network thousands of
examples where we know the right answer, and after each batch we nudge every weight a little in the direction
that makes the error smaller. Do that enough times and the weights stop being random and start being useful.

That nudging is all "training" means.

### Why bother, when we already have a forest?

Because of **shape in time**.

The forest sees one row: this patient, right now, plus a few numbers we hand-built to summarise the past
(`_d30`, `_usual`). We had to *decide in advance* that 30 minutes was the interesting gap, and that the middle
of 5 readings was the right smoothing.

A model built for sequences is handed the **raw last 60 minutes, in order**, and works out for itself which
part of that hour matters. It can learn things we never thought to write a column for — "went up, came back
down, then started climbing again" is a pattern no single column of ours describes.

That is the promise. Section 15 checks whether we actually got it.
""")

co(r"""
# One neuron, made concrete. Three clues in, one risk out.
def squash(x):
    "Turn any number into something between 0 and 1."
    return 1 / (1 + np.exp(-x))


inputs  = np.array([3.0, 8.0, 0.95])                 # rr_off, hr_off, sensor quality
weights = np.array([0.9, 0.25, 4.0])                 # learned: fast breathing matters most,
bias    = -5.0                                       # and a trustworthy signal makes it believable

total = float(np.dot(inputs, weights) + bias)
print(f"weighted sum = {total:+.2f}   ->   risk = {squash(total):.2f}")

# Same patient, but the sensor is barely working.
inputs_bad = np.array([3.0, 8.0, 0.15])
total_bad = float(np.dot(inputs_bad, weights) + bias)
print(f"same numbers, poor signal: weighted sum = {total_bad:+.2f}   ->   risk = {squash(total_bad):.2f}")

xs = np.linspace(-6, 6, 200)
plt.figure(figsize=(5.5, 2.6))
plt.plot(xs, squash(xs), color=PURPLE, lw=2)
plt.axhline(0.5, color=GREY, ls=":")
plt.title("The squash: any number in, 0 to 1 out")
plt.tight_layout()
plt.show()
""")

md(r"""
Notice what the weight on sensor quality did. The vital signs are **identical** in both lines. Only the
trustworthiness of the signal changed, and the risk fell sharply. **That single weight is the "ignore probable
sensor noise" action — learned from data rather than written down by us.**
""")


# ============================================================ 14. MODEL 4
md(r"""
## 14 · Model 4 — an LSTM

An **LSTM** is a neural network built to read a sequence. The letters stand for Long Short-Term Memory, and
the idea behind the name is the useful part.

Read the last hour one reading at a time. After each reading, the network updates a small internal note to
itself — a memory. Crucially it also learns **what to forget**. A two-minute spike gets written into the
memory and then dropped. A slow upward lean gets kept, because it keeps being confirmed.

That forgetting is the whole trick, and it is exactly the distinction we drew in section 4: **tall, sudden,
short = throw away. Small, slow, persistent = remember.**

### What we feed it

For every reading, the previous **30 readings — a full hour** — of six numbers: heart rate, SpO₂,
respiratory rate, blood pressure, temperature and sensor quality.

No `_off` columns. No `_d30` columns. No smoothing. **The raw hour, and nothing else.** If deep learning
really can find the shape by itself, this is where it has to prove it.
""")

co(r"""
SEQ = 30                                   # 30 readings x 2 minutes = the last hour
SEQ_COLS = ["hr", "spo2", "rr", "sbp", "temp", "quality"]

# Put every column on a similar scale, using only the learning days.
mu = TRAIN[SEQ_COLS].mean().to_numpy(np.float32)
sd = TRAIN[SEQ_COLS].std().to_numpy(np.float32)


def make_sequences(df, stride=1):
    "Cut each patient's record into overlapping one-hour windows."
    Xs, ys, rows = [], [], []
    for p, part in df.groupby("patient", sort=False):
        arr = (part[SEQ_COLS].to_numpy(np.float32) - mu) / sd
        lab = part["trouble"].to_numpy(np.float32)
        idx = part.index.to_numpy()
        win = np.lib.stride_tricks.sliding_window_view(arr, SEQ, axis=0).transpose(0, 2, 1)
        Xs.append(np.ascontiguousarray(win[::stride]))
        ys.append(lab[SEQ - 1:][::stride])
        rows.append(idx[SEQ - 1:][::stride])
    return np.concatenate(Xs), np.concatenate(ys), np.concatenate(rows)


Xs_tr, ys_tr, _        = make_sequences(TRAIN, stride=3)
Xs_te, ys_te, rows_te  = make_sequences(TEST,  stride=1)
Xs_tu, ys_tu, rows_tu  = make_sequences(TUNE,  stride=1)

print("Training windows:", Xs_tr.shape, "  (windows, readings per window, measurements)")
print("Exam windows    :", Xs_te.shape)
""")

co(r"""
if KERAS:
    inp = keras.Input(shape=(SEQ, len(SEQ_COLS)))
    x = layers.LSTM(32)(inp)                       # reads the hour, keeps a small memory
    x = layers.Dense(16, activation="relu")(x)
    out = layers.Dense(1, activation="sigmoid")(x) # one number: risk from 0 to 1
    net = keras.Model(inp, out)
    net.compile(optimizer=keras.optimizers.Adam(1e-3), loss="binary_crossentropy")
    net.summary()

    hist = net.fit(Xs_tr, ys_tr, epochs=4, batch_size=256,
                   class_weight={0: 1.0, 1: 25.0},   # deterioration is rare, so it counts for more
                   validation_split=0.1, verbose=2)
    risk_te = net.predict(Xs_te, batch_size=1024, verbose=0).ravel()
    risk_tu = net.predict(Xs_tu, batch_size=1024, verbose=0).ravel()
else:
    from sklearn.neural_network import MLPClassifier
    flat = lambda a: a.reshape(len(a), -1)
    net = MLPClassifier(hidden_layer_sizes=(48, 16), max_iter=15, random_state=7)
    net.fit(flat(Xs_tr), ys_tr)
    risk_te = net.predict_proba(flat(Xs_te))[:, 1]
    risk_tu = net.predict_proba(flat(Xs_tu))[:, 1]

# The first 29 readings of each patient have no full hour behind them, so they get a risk of 0.
TEST["risk_lstm"] = 0.0
TEST.loc[rows_te, "risk_lstm"] = risk_te
TUNE["risk_lstm"] = 0.0
TUNE.loc[rows_tu, "risk_lstm"] = risk_tu

# Same rule as the forest: the highest level that still catches 3 in 4 of the dial-day events.
LSTM_LEVEL = pick_sensitive_level(TUNE, "risk_lstm", TUNE_EVENTS, catch=0.75)
print(f"\nAlert level chosen on the dial-setting day: risk >= {LSTM_LEVEL:.3f}")

ALERTS["4. LSTM"] = to_alerts(TEST, (TEST["risk_lstm"] >= LSTM_LEVEL).to_numpy())
print()
print(pd.DataFrame([summarise(k, v) for k, v in ALERTS.items()]).set_index("model").to_string())
""")


# ============================================================ 15. RANKING
md(r"""
## 15 · Which model ranks the risk best

Now the question that actually matters.

Forget thresholds for a moment. Imagine each model hands us a list of all twenty patients, sorted with the
one it is most worried about at the top. **If we could only look at the top of that list, how good would the
list be?**

Two standard measures, both explained plainly:

- **AUC.** Pick one deteriorating reading and one ordinary reading at random. AUC is the chance the model
  gives the deteriorating one the higher risk. 0.5 is a coin toss. 1.0 is perfect.
- **Average precision.** When only about 2 in 100 readings are deterioration, AUC can look flattering.
  Average precision asks the harder question: of the readings the model is most worried about, what share are
  genuinely deteriorating? A model that alerts at random would score about 0.02 here.

Then the picture that ties everything together: **how many of the 24 events would each method catch, at each
possible alert rate?** The budget is a vertical line at 5 alerts an hour. What matters is how high each curve
is *where it crosses that line*.
""")

co(r"""
sources = {
    "Risk score":    TEST["score"].to_numpy() / 20.0,
    "Random forest": TEST["risk_rf"].to_numpy(),
    "LSTM":          TEST["risk_lstm"].to_numpy(),
}

print("How well does each one sort patients by risk?")
print()
for name, r in sources.items():
    print(f"{name:<16}  AUC {roc_auc_score(yte, r):.3f}     "
          f"average precision {average_precision_score(yte, r):.3f}")
""")

co(r"""
def budget_curve(risk):
    "How many events would we catch, at every possible alert rate?"
    rate, caught = [], []
    for q in np.linspace(0.95, 0.99995, 22):
        thr = np.quantile(risk, q)
        s = summarise("x", to_alerts(TEST, risk >= thr))
        rate.append(s["alerts_per_hour"])
        caught.append(s["caught_events"])
    return rate, caught


plt.figure(figsize=(8.5, 4.2))
for (name, r), colour in zip(sources.items(), [GREEN, BLUE, PURPLE]):
    x, y = budget_curve(r)
    plt.plot(x, y, "o-", ms=3, color=colour, label=name)

lim = summarise("x", ALERTS["1. Simple limits"])
plt.plot(lim["alerts_per_hour"], lim["caught_events"], "s", ms=9, color=RED, label="Simple limits")

plt.axvline(ALERT_BUDGET, color="black", ls="--", lw=1.5)
plt.text(ALERT_BUDGET + 0.3, 1, "our budget", rotation=90, fontsize=9)
plt.xscale("log")
plt.xlabel("alerts per hour  (log scale)")
plt.ylabel(f"events caught, out of {len(TEST_EVENTS)}")
plt.title("What each method could catch, for a given amount of noise")
plt.legend()
plt.tight_layout()
plt.show()
""")

md(r"""
### This chart is the argument of the whole notebook

Everything to the right of the dashed line is unaffordable. It does not matter how many events a method
catches at 30 alerts an hour, because a ward cannot answer 30 alerts an hour.

So read only the dashed line, and read upward. The gap between the curves **at that line** is the real value
of a better model. It is not "the forest is more accurate". It is: *for the same five interruptions, this
many more patients are found.*

That is also why the fixed-limits square sits where it does — far to the right, catching a lot, at a price
nobody can pay.

### An important catch, before this chart flatters anybody

Look at the forest's curve and you will notice something awkward: it reaches every event at well under one
alert an hour. So why did model 3, which *is* the forest, miss patients while barely speaking?

Because **this chart is drawn with hindsight.** To place each dot we used the exam days' own risk numbers to
pick the level. In the exam we do not have them. Model 3 had to choose its level in advance, from one
dial-setting day, and the level it chose was too high.

That gap between "the best level, known afterwards" and "the level you can actually pick beforehand" is not a
flaw in the chart. **It is the entire reason a fixed threshold is the wrong tool.** No amount of care in
choosing one number in advance survives contact with days you have not seen.

And nothing here tells us **which** five patients to alert on in a given hour, only how good the ordering is.
Turning a good ordering into good decisions, without hindsight, is section 16.
""")


# ============================================================ 16. MODEL 5
md(r"""
## 16 · Model 5 — the attention-budget optimizer

Here is the last piece, and it is not a new prediction model. It takes the risk numbers we already have and
answers the ward's real question: **who gets the five?**

### The idea: a bucket of tokens

Think of the ward's attention as a bucket holding 5 tokens. Sending an alert costs one token. The bucket
refills steadily, one token every 12 minutes, up to a maximum of 5.

Now the clever part — **how sure we insist on being depends on how full the bucket is**:

| Tokens left | What it means | How sure we must be |
|---|---|---|
| 4 or 5 | quiet hour, attention to spare | a maybe is worth checking |
| 2 to 4 | normal | only send the likely ones |
| under 2 | nearly spent | only send the near-certain ones |
| 0 | spent | nothing goes out except an emergency |

This is exactly how a good senior nurse behaves. On a quiet night they will happily go and check a hunch. At
the worst moment of a bad shift they will only move for something they are sure about. **The threshold is not
a fixed number. It depends on what else is going on.**

### The five actions, in order

For every patient at every reading:

1. **Risk very high?** → **urgent response**, and this one ignores the budget entirely. A patient in crisis is
   never held in a queue to protect a quota. It also ignores the 30-minute rule below: a patient we merely
   *notified* about ten minutes ago, who is now critical, must be able to escalate immediately.
2. **Already alerted in the last 30 minutes?** → keep watching. The nurse knows.
3. **Poor sensor quality and the risk is not high?** → **ignore**. This is the loose probe.
4. **Risk above the level the bucket currently demands, and a token is available?** → **notify a nurse**.
5. **Risk worth watching but not worth an interruption?** → **repeat the measurement**: say nothing, wait six
   minutes, look again. Most spikes are gone by then. If it is real, it will still be there — and it will be
   *worse*, so it will clear the bar next time.
6. **Otherwise** → keep watching.

Step 5 is where the budget is really saved. It is not that we became braver about ignoring things. It is that
we gave ourselves a way to be unsure without spending a nurse.

### Setting the levels

The four risk levels are worked out on **day 8 only** — the dial-setting day. We ask: what risk level would
have produced 15, 8, 5, 2 and 0.6 alerts an hour on that day? Those become our watch, generous, normal,
strict and emergency levels. The exam days are never used to choose them.
""")

co(r"""
def pick_level(df, risk, per_hour, hours):
    "Find the risk level that would have produced about this many alerts per hour."
    lo, hi = 0.0, 1.0
    for _ in range(20):
        mid = (lo + hi) / 2.0
        if len(to_alerts(df, risk >= mid)) / hours > per_hour:
            lo = mid
        else:
            hi = mid
    return round(hi, 4)


risk_tune = TUNE["risk_rf"].to_numpy()
T_WATCH  = pick_level(TUNE, risk_tune, 15.0, TUNE_HOURS)   # worth a repeat measurement
T_EASY   = pick_level(TUNE, risk_tune,  8.0, TUNE_HOURS)   # bucket full: a maybe is worth checking
T_NORMAL = pick_level(TUNE, risk_tune,  5.0, TUNE_HOURS)   # normal
T_STRICT = pick_level(TUNE, risk_tune,  2.0, TUNE_HOURS)   # bucket nearly empty
T_URGENT = pick_level(TUNE, risk_tune,  0.6, TUNE_HOURS)   # call the emergency team

print(f"repeat the measurement above risk : {T_WATCH}")
print(f"notify when attention is plentiful: {T_EASY}")
print(f"notify normally                   : {T_NORMAL}")
print(f"notify when nearly out of budget  : {T_STRICT}")
print(f"urgent response above risk        : {T_URGENT}")
""")

co(r"""
def run_manager(df, risk_col, budget=ALERT_BUDGET):
    "Walk through the ward minute by minute and choose one of the five actions for every patient."
    minutes = df["minute"].to_numpy()
    pats    = df["patient"].to_numpy()
    risk    = df[risk_col].to_numpy()
    qual    = df["quality_smooth"].to_numpy()
    rows    = df.index.to_numpy()
    order   = np.argsort(minutes, kind="stable")

    tokens = float(budget)
    refill = budget * DT / 60.0            # attention comes back as the hour passes
    last_alert, last_action, hold_until = {}, {}, {}
    log, now = [], None

    for i in order:
        t, p, r, q = minutes[i], pats[i], risk[i], qual[i]
        if t != now:
            tokens, now = min(budget, tokens + refill), t
        since = t - last_alert.get(p, -10 ** 9)

        # A patient who was only "notify" ten minutes ago and is now critical must be able to
        # escalate straight away. Waiting out the 30 minutes would be exactly the wrong rule.
        if r >= T_URGENT and (since >= REFRACTORY or last_action.get(p) != "urgent"):
            action = "urgent"                                 # never delayed, never budgeted
        elif since < REFRACTORY:
            action = "monitor"                                # the nurse already knows
        elif t < hold_until.get(p, -10 ** 9):
            action = "monitor"                                # waiting for the repeat reading
        elif q < 0.5 and r < T_NORMAL:
            action = "ignore"                                 # poor signal, no supporting evidence
        else:
            level = T_EASY if tokens >= 4 else (T_NORMAL if tokens >= 2 else T_STRICT)
            if r >= level and tokens >= 1:
                action = "notify"
            elif r >= T_WATCH:
                action = "repeat"
            else:
                action = "monitor"

        if action in ("notify", "urgent"):
            tokens -= 1
            last_alert[p] = t
            last_action[p] = action
        elif action == "repeat":
            hold_until[p] = t + 6

        log.append((t, p, rows[i], action, r))

    return pd.DataFrame(log, columns=["minute", "patient", "row", "action", "risk"])


decisions = run_manager(TEST, "risk_rf")
ALERTS["5. Attention budget"] = decisions[decisions.action.isin(["notify", "urgent"])].reset_index(drop=True)

print("What the manager decided, across", f"{len(decisions):,}", "readings:")
print(decisions.action.value_counts().to_string())
print()
print(pd.DataFrame([summarise(k, v) for k, v in ALERTS.items()]).set_index("model").to_string())
""")

co(r"""
# Was the budget actually respected, hour by hour?
per_hour = (ALERTS["5. Attention budget"]
            .groupby(ALERTS["5. Attention budget"].minute // 60).size())
full = per_hour.reindex(range(TEST.minute.min() // 60, TEST.minute.max() // 60 + 1), fill_value=0)

plt.figure(figsize=(10, 2.8))
plt.plot(np.arange(len(full)), full.values, color=BLUE, lw=0.9)
plt.axhline(ALERT_BUDGET, color=RED, ls="--", label=f"budget = {ALERT_BUDGET}/hour")
plt.xlabel("hour of the exam period")
plt.ylabel("alerts sent")
plt.title("Alerts per hour")
plt.legend()
plt.tight_layout()
plt.show()

over = int((full.values > ALERT_BUDGET).sum())
print(f"Average                : {full.mean():.2f} alerts per hour   (budget {ALERT_BUDGET})")
print(f"Busiest single hour    : {int(full.max())} alerts")
print(f"Hours above {ALERT_BUDGET} alerts  : {over} out of {len(full)}  ({100 * over / len(full):.1f}%)")
print(f"Quiet hours (0 alerts) : {int((full.values == 0).sum())}")
""")

md(r"""
### About those hours above five

Some individual hours go above five, and that is the bucket working as designed rather than a bug.

The bucket holds up to 5 tokens. If the ward is quiet for an hour, the bucket fills right up, and the next
busy hour can spend those saved tokens **on top of** the ones that arrive during it. What we are really
promising is *five an hour on average, with the freedom to save up for a bad patch* — which is how a real
nurse's attention behaves too.

The average across the four days is the number that has to be under five, and it is. On top of that, an
urgent response is always sent, even with an empty bucket. We would rather break the budget for a few minutes
than hold back the emergency team.
""")

md(r"""
### Why not just stop after five?

There is a much simpler way to get a noisy system inside a budget: take the ward's existing monitor, let it
send the first five alerts of every hour, and switch it off until the next hour begins.

It needs no model at all, it is trivial to build, and it is a trap. Here it is, next to the optimizer.
""")

co(r"""
def hard_cap(alerts, budget=ALERT_BUDGET):
    "The naive way to stay in budget: keep the first few alerts of each hour, bin the rest."
    return (alerts.groupby(alerts.minute // 60, group_keys=False)
                  .head(budget).reset_index(drop=True))


naive = hard_cap(ALERTS["1. Simple limits"])
comparison = pd.DataFrame([
    summarise("Simple limits, first 5 each hour", naive),
    summarise("Attention budget", ALERTS["5. Attention budget"]),
]).set_index("model")
print(comparison.to_string())
""")

md(r"""
### The difference is *which* five, not *how many*

Both rows now cost the ward about the same. They are not equally safe.

The naive version spends its five tokens on whatever happens to arrive first, and what arrives first is
almost always a loose probe — glitches are common, deterioration is rare. By the time the patient who is
genuinely sliding downhill needs attention, the hour's budget is gone and the system has switched itself off.
Worse, capping the noise did nothing to fix the noise: the alerts it does send are still overwhelmingly
about nothing.

The optimizer never switches off. It gets **stricter**, which is a completely different thing. It keeps
watching every patient, it keeps re-checking the doubtful ones for free, and it holds an emergency exit open
for anyone who becomes critical.

**This is the sentence to take away from the notebook:** the value was not in predicting better. Models 3 and
5 use the identical random forest and the identical risk numbers. The value was in *spending a fixed amount
of human attention well*.
""")


# ============================================================ 17. ONE PATIENT
md(r"""
## 17 · Watching one patient, minute by minute

Averages hide things. Here is a single patient from the exam days, from the moment they start to deteriorate
until the crisis, with the manager's decision marked on every reading.
""")

co(r"""
# Take an event the manager caught, and replay it.
ev = None
for e in TEST_EVENTS.itertuples():
    hit = ALERTS["5. Attention budget"]
    hit = hit[(hit.patient == e.patient) & (hit.minute >= e.start) & (hit.minute <= e.crisis)]
    if len(hit):
        ev = e
        break

part = TEST[(TEST.patient == ev.patient) &
            (TEST.minute >= ev.start - 120) & (TEST.minute <= ev.crisis + 30)]
dec = decisions[decisions.row.isin(part.index)]
hours = (part.minute.to_numpy() - ev.crisis) / 60.0

fig, ax = plt.subplots(3, 1, figsize=(10.5, 6.4), sharex=True)
ax[0].plot(hours, part.hr, color=RED, lw=1.2, label="heart rate")
ax[0].plot(hours, part.rr * 4, color=GREEN, lw=1.2, label="breaths/min (x4)")
ax[0].legend(loc="upper left", fontsize=8); ax[0].set_ylabel("beats / breaths")

ax[1].plot(hours, part.spo2, color=BLUE, lw=1.2, label="SpO2 %")
ax[1].plot(hours, part.quality * 100, color=GREY, lw=1.0, label="sensor quality x100")
ax[1].legend(loc="lower left", fontsize=8); ax[1].set_ylabel("percent")

ax[2].plot(hours, part.risk_rf, color=PURPLE, lw=1.4)
ax[2].axhline(T_NORMAL, color=ORANGE, ls="--", lw=1, label="notify level")
ax[2].axhline(T_URGENT, color=RED, ls="--", lw=1, label="urgent level")
ax[2].set_ylabel("risk"); ax[2].set_xlabel("hours before the crisis point")
ax[2].legend(loc="upper left", fontsize=8)

marks = {"notify": (ORANGE, "^"), "urgent": (RED, "*"), "repeat": (BLUE, "."), "ignore": (GREY, "x")}
for act, (colour, marker) in marks.items():
    sel = dec[dec.action == act]
    if len(sel):
        xs = (sel.minute.to_numpy() - ev.crisis) / 60.0
        ax[2].plot(xs, np.full(len(sel), -0.05), marker, color=colour, ms=8 if act != "repeat" else 4)

for a in ax:
    a.axvspan((ev.start - ev.crisis) / 60.0, 0, color=RED, alpha=0.08)
    a.axvline(0, color="black", lw=1)

ax[0].set_title(f"Patient {ev.patient}, day {ev.day} - {ev.kind}.  0 = the crisis point")
plt.tight_layout()
plt.show()

print(dec.action.value_counts().to_string())
inside = dec[dec.action.isin(["notify", "urgent"]) &
             (dec.minute >= ev.start) & (dec.minute <= ev.crisis)]
print()
print(f"Deterioration lasted {int(ev.crisis - ev.start)} minutes.")
print(f"First alert once it began: {int(ev.crisis - inside.minute.min())} minutes before the crisis.")
""")

md(r"""
### What just happened

Read the bottom panel from left to right.

Before the red band the risk sits near the floor, with the occasional blue dot — the manager quietly taking a
second look at something and saying nothing to anybody. Those cost nothing.

Inside the red band the risk climbs. It crosses the notify level well before the crisis, and one alert goes
out. After that the patient goes quiet on the alert list for 30 minutes, because the nurse already knows.

If the risk keeps climbing past the urgent level, the emergency team is called regardless of how much budget
is left.

Compare that with what a fixed limit would have done here: nothing at all until the heart rate finally
crossed 120, near the right-hand edge.
""")


# ============================================================ 18. NURSE SHIFT
md(r"""
## 18 · The nurse's shift: workload and response time

Everything so far has counted alerts. Nobody is treated by an alert. Now we put two nurses on the ward and
see what actually reaches a patient.

The rules of the simulation:

- **Two nurses.** Between them they have 120 minutes of attention in every hour.
- A **notify** takes about **8 minutes** — walk over, look, take a fresh set of readings, write it down.
- An **urgent response** takes about **20 minutes**, and jumps the queue.
- If both nurses are busy, alerts **wait in a queue**. Emergencies wait at the front, everything else in the
  order it arrived.

**Response time** is the wait between the alert going out and a nurse getting to that patient.

This is where a flood of alerts stops being an annoyance and starts being a danger. Fifteen alerts an hour, at
eight minutes each, asks for more nurse time than an hour actually contains. Once demand passes supply the
queue can never catch up, so it grows all shift — and the patient who genuinely needs help is somewhere
inside it, behind a hundred loose probes.
""")

co(r"""
import heapq


def simulate_nurses(alerts, n_nurses=2):
    "Play a set of alerts through a ward with two nurses and record who waited how long."
    if len(alerts) == 0:
        return alerts.assign(wait=[]), 0.0
    t0, t1 = int(TEST.minute.min()), int(TEST.minute.max()) + 1
    arriving = {}
    for a in alerts.itertuples():
        arriving.setdefault(int(a.minute), []).append(a)

    queue, free_at, waits, busy, seq = [], [t0] * n_nurses, {}, 0, 0
    for t in range(t0, t1):
        for a in arriving.get(t, []):
            seq += 1
            heapq.heappush(queue, (0 if a.action == "urgent" else 1, t, seq, a.Index, a.action))
        for k in range(n_nurses):
            if free_at[k] <= t and queue:
                _, at, _, key, act = heapq.heappop(queue)
                mins = ACTIONS[act]["nurse_minutes"]
                free_at[k] = t + mins
                busy += mins
                waits[key] = t - at

    out = alerts.copy()
    # Anything still in the queue at the end never got seen.
    out["wait"] = [waits.get(i, t1 - int(m)) for i, m in zip(out.index, out.minute)]
    out["seen"] = [i in waits for i in out.index]
    return out, busy / len(TEST_DAYS) / 24


def full_score(name, alerts):
    "Everything the ward cares about, for one method."
    served, delivered = simulate_nurses(alerts)
    s = summarise(name, alerts)
    demanded = sum(ACTIONS[a]["nurse_minutes"] for a in alerts["action"]) / TEST_HOURS
    truth = TEST["trouble"].to_numpy()
    real = served[truth[served["row"].to_numpy()] == 1] if len(served) else served

    # The bottom line: did a nurse actually get to the patient before the crisis point?
    reached = 0
    for e in TEST_EVENTS.itertuples():
        hit = served[(served.patient == e.patient) &
                     (served.minute >= e.start) & (served.minute <= e.crisis)]
        if len(hit) and bool(((hit["minute"] + hit["wait"]) <= e.crisis).any()):
            reached += 1

    s["nurse_min_needed"] = round(demanded, 1)
    s["nurse_min_given"] = round(delivered, 1)
    s["response_min"] = int(np.median(real["wait"])) if len(real) else 0
    s["never_seen"] = int((~served["seen"]).sum()) if len(served) else 0
    s["reached_in_time"] = reached
    return s


print("Two nurses have 120 minutes of attention per hour. Here is what each method asks of them:")
print()
board = pd.DataFrame([full_score(k, v) for k, v in ALERTS.items()]).set_index("model")
print(board[["alerts_per_hour", "nurse_min_needed", "nurse_min_given",
             "response_min", "never_seen", "reached_in_time"]].to_string())
print()
print(f"(reached_in_time is out of {len(TEST_EVENTS)} deterioration events)")
""")

md(r"""
### Read the two workload columns together

`nurse_min_needed` is what the method asks for. `nurse_min_given` is what two nurses can actually deliver.
When the first number is bigger than the second, the ward is **oversubscribed**: the queue grows, and every
extra alert makes the wait longer for everybody, including the patient who is genuinely deteriorating.

`response_min` is the median wait for alerts about **truly deteriorating patients** — the alerts that were
right. A loud system does not just waste time. It delays the alerts that were correct, because they are stuck
behind the ones that were not.

`never_seen` counts alerts nobody ever got to before the four days ran out.

### And then the column that settles it

`reached_in_time` counts the deteriorations where **a nurse actually arrived at the bedside before the crisis
point**. Not alerted. Arrived.

This is the only number in the notebook that a patient would recognise as mattering. An alert that sits in a
queue for two hours did not help anybody, and up to now we have been counting it as a success.

**This is alarm fatigue expressed as arithmetic.** Nobody ignored anything on purpose. There were simply more
alerts than minutes.
""")


# ============================================================ 19. SCOREBOARD
md(r"""
## 19 · The scoreboard

All five methods, on the same four days, judged on the five things the ward asked about at the start.
""")

co(r"""
show = board.rename(columns={
    "alerts_per_hour": "alerts/hr",
    "missed_events": "never alerted",
    "reached_in_time": "nurse arrived in time",
    "early_warning_min": "early warning (min)",
    "false_alarms": "false alarms",
    "nurse_min_needed": "nurse min/hr",
    "response_min": "response (min)",
})[["alerts/hr", "never alerted", "nurse arrived in time", "early warning (min)",
    "false alarms", "nurse min/hr", "response (min)"]]
print(f"Judged on {len(TEST_EVENTS)} real deterioration events over {TEST_HOURS} hours.")
print(f"The ward can afford {ALERT_BUDGET} alerts an hour and has 120 nurse-minutes an hour.")
print()
print(show.to_string())
""")

co(r"""
fig, ax = plt.subplots(1, 4, figsize=(13, 3.4))
names = [n.split(". ")[1] for n in board.index]
bars = [
    ("Nurse arrived in time", board["reached_in_time"].values, GREEN, f"out of {len(TEST_EVENTS)}"),
    ("Alerts per hour", board["alerts_per_hour"].values, ORANGE, f"budget {ALERT_BUDGET}"),
    ("Early warning (min)", board["early_warning_min"].values, PURPLE, "higher is better"),
    ("Response time (min)", board["response_min"].values, BLUE, "lower is better"),
]
for a, (title, vals, colour, note) in zip(ax, bars):
    a.bar(range(len(names)), vals, color=colour)
    a.set_xticks(range(len(names)))
    a.set_xticklabels(names, rotation=45, ha="right", fontsize=8)
    a.set_title(f"{title}\n({note})", fontsize=10)
    if title == "Alerts per hour":
        a.axhline(ALERT_BUDGET, color="black", ls="--", lw=1)
plt.tight_layout()
plt.show()
""")

md(r"""
### What the scoreboard says

Read it as a story about trade-offs, not a competition with a winner.

**Simple limits** alert about almost everything, and it does not help. They ask for more nurse time than the
ward has, so the queue never empties: alerts go unanswered, the true ones wait behind the false ones, and
patients are reached late or not at all. Being loud is not the same as being safe.

**The risk score** is a genuine, cheap improvement, and it needs no computer at all. It cuts the noise by
demanding that measurements agree. The bill arrives as timing: it waits until several numbers are clearly
abnormal, so it warns later and misses more patients than the crude limits did.

**The random forest** is much the most accurate of the five. When it speaks, it is usually right. But at a
fixed alert level it barely speaks — most of the ward's budget goes unused, and patients still slip past.
Accuracy alone did not solve the problem.

**The LSTM** is handed no hand-built clues at all, only the raw hour, and has to find the shape itself. Judge
it by section 15 rather than by its row here. Where a model's alert level happens to land is partly luck —
retrain this network and its row will move a long way. How well it **sorts** patients is not luck, and on
that comparison the forest is far ahead on both measures.

Deep learning earns its place when the raw signal is rich and the hand-built clues are poor. Here the signal
is six slow numbers and the clues were built with real care, so the simpler model wins — and it trains in
seconds instead of minutes. That is a genuinely useful result to have measured rather than assumed.

**The attention budget** uses the same forest as model 3 and changes nothing whatsoever about the prediction.
It changes only the decision: how sure to insist on being, given how much attention is left, and what to do
when the answer is "not sure". That is where the ward's problem actually lived.

Its false-alarm percentage is not low, and that is worth facing rather than hiding. The right way to read it
is per hour, not per cent: it interrupts the ward under five times an hour, a nurse reaches every deteriorating
patient before their crisis, and the warnings arrive around an hour ahead. That is a ward that can function.
""")


# ============================================================ 20. WHAT IT GETS WRONG
md(r"""
## 20 · What the system still gets wrong

A teaching notebook that ends with a victory chart has taught the wrong lesson. Here is the honest list.
""")

co(r"""
missed = []
for e in TEST_EVENTS.itertuples():
    hit = ALERTS["5. Attention budget"]
    hit = hit[(hit.patient == e.patient) & (hit.minute >= e.start) & (hit.minute <= e.crisis)]
    if len(hit) == 0:
        part = TEST[(TEST.patient == e.patient) & (TEST.minute >= e.start) & (TEST.minute <= e.crisis)]
        missed.append(dict(patient=e.patient, day=e.day, kind=e.kind,
                           highest_risk=round(float(part.risk_rf.max()), 3),
                           needed=T_STRICT))

if missed:
    print("Events the attention manager never alerted on:")
    print(pd.DataFrame(missed).to_string(index=False))
else:
    print("The attention manager alerted on every event in the exam period.")

print()
close = []
for e in TEST_EVENTS.itertuples():
    part = TEST[(TEST.patient == e.patient) & (TEST.minute >= e.start) & (TEST.minute <= e.crisis)]
    hit = ALERTS["5. Attention budget"]
    hit = hit[(hit.patient == e.patient) & (hit.minute >= e.start) & (hit.minute <= e.crisis)]
    close.append(dict(patient=e.patient, kind=e.kind,
                      warning_min=int(e.crisis - hit.minute.min()) if len(hit) else -1,
                      highest_risk=round(float(part.risk_rf.max()), 3),
                      chronic=part.chronic.iloc[0] or "-"))

close = pd.DataFrame(close).sort_values("warning_min")
print("The five closest calls (least warning given):")
print(close.head(5).to_string(index=False))
print()
lead = close[close.warning_min >= 0]["warning_min"].to_numpy()
print(f"Warning time across events: worst {lead.min()} min, middle {int(np.median(lead))} min, "
      f"best {lead.max()} min")
print(f"Events with less than 30 minutes of warning: {int((lead < 30).sum())} of {len(lead)}")
print(f"Events with a risk that never passed the strict level ({T_STRICT}): "
      f"{int((close.highest_risk < T_STRICT).sum())}")
""")

md(r"""
### The five honest limitations

**1. It was tested on a ward we invented.** Our patients deteriorate in three tidy patterns. Real patients do
not. Every number in this notebook is a statement about our simulator, not about a hospital. The *method* is
transferable; the *results* are not.

**2. The budget is a real cost, and somebody pays it.** Every event the system catches late, or misses, is a
patient. Five an hour is a choice made for the nurses. If the ward gets a third nurse the right answer
changes, and the system should be re-tuned, not left alone.

**3. It learned from the past, and wards change.** New drugs, new patient mix, a new brand of oxygen probe —
any of these shift the patterns underneath the model. A model that is never re-checked slowly becomes a model
that is wrong.

**4. Rare things stay hard.** Our forest saw a few dozen deteriorations. A pattern that appears twice a year
will not be learned, and the system will be confidently quiet about it. This is exactly why the fixed limits
should stay switched on underneath as a safety net, however noisy they are.

**5. It never decides anything clinical.** The system chooses *who to tell*. It does not diagnose, it does not
treat, and it cannot be the reason nobody looked at a patient. A nurse who is worried should always win an
argument with it.
""")


# ============================================================ 21. SUMMARY
md(r"""
## 21 · Summary

### What we built

A ward of 20 patients, seven streams of information each, and five systems that had to decide what deserved a
human being's attention.

| Step | What it taught |
|---|---|
| Fixed limits | one number, one rule, and a ward nobody can work on |
| Where false alarms come from | most of them had a clue sitting right next to them |
| Better clues | own normal, direction of travel, sensor quality, recent medicine |
| Risk score | asking measurements to agree removes most single-sensor noise |
| Random forest | let the machine find the pattern in 27 clues at once |
| LSTM | hand it the raw hour and let it find the shape itself |
| Ranking, not thresholds | a model's job is to sort; the threshold is a separate choice |
| Attention budget | the same prediction, spent well |

### The four ideas worth keeping

**1. A prediction is not a decision.** Models 3 and 5 share a brain. They behave completely differently,
because only one of them was asked "and what should we do about it, given what else is going on?"

**2. Attention is the scarce resource.** Not accuracy. Any system that ignores how much attention exists will
be switched off by the people it was built for — and they will be right to switch it off.

**3. Noise is tall, sudden and short. Illness is small, slow and persistent.** Nearly every improvement in
this notebook came from that one observation: the middle-of-five smoothing, the direction columns, the sensor
quality weight, the repeat-measurement action, and the LSTM's forgetting.

**4. Not deciding is a decision, and it is often the best one.** *Ignore*, *repeat the measurement* and *keep
watching* did most of the work here. Being able to be unsure without spending a nurse is what made five
alerts an hour survivable.

### If you want to take this further

- Change `ALERT_BUDGET` to 3 or to 10 and re-run. Watch which metric breaks first.
- Add a night-time rule so that waking a sleeping ward costs more budget than an afternoon alert.
- Give each of the 20 patients a different importance — a post-surgical patient may deserve more of the
  budget than a stable one — and let the optimizer weigh that in.
- Feed the LSTM the same hand-built clues the forest gets, and see whether the deep model finally pulls ahead.
""")


# ============================================================ WRITE
nb = new_notebook(cells=cells, metadata={
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "colab": {"provenance": [], "toc_visible": True},
})

with open("Hospital_Alarm_Fatigue_Manager.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)

print(f"Wrote Hospital_Alarm_Fatigue_Manager.ipynb  ({len(cells)} cells)")
