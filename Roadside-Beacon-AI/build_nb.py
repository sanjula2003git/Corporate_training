"""
Builds Roadside_First_Response_Beacon.ipynb from nbformat cells.
Run:  py -3.13 -X utf8 build_nb.py

House style: SIMPLE ENGLISH. Short sentences, everyday words, and an explanation
next to anything a beginner would not already know - the same style as the
Hospital Alarm-Fatigue notebook.

The notebook is standalone (Colab): it builds the whole virtual junction inline,
so there is no video to download and nothing to import from this folder.

NOTE for future editors:
  * inside co(...) cells use only single-line "..." docstrings or # comments. A
    triple-quoted docstring would close the outer r-string and break this script.
  * the prose quotes numbers the cells print. After any change, re-run the cells
    and re-check every number written in markdown.
  * only ONE link goes out to the illustration app, at the top. Colab opens every
    external link in a fresh tab, so sixteen links means sixteen tabs.
"""
import sys
from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bridge  # noqa: E402

cells = []
def md(t):  cells.append(new_markdown_cell(t.strip("\n")))
def co(t):  cells.append(new_code_cell(t.strip("\n")))

COLAB = ("https://colab.research.google.com/github/sanjula2003git/Corporate_training/blob/main/"
         "Roadside-Beacon-AI/Roadside_First_Response_Beacon.ipynb")
APP = "https://roadside-beacon.streamlit.app"


def see(stage, label):
    """Point at the matching page of the illustration app - without a link."""
    n = bridge.ORDER.index(stage) + 1
    md(f"🎬 **See it illustrated:** step {n} in the illustration tab — *{label}*.")


# ============================================================ TITLE
md(rf"""
# 🚨 The Golden Minutes

### Building an AI Roadside First-Response Beacon

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({COLAB})

A motorcycle goes down at a junction at 8:42 in the evening.

Twenty people see it happen. Several take out their phones. The first call to the emergency number
is made **two minutes later**, by somebody who is not certain which junction they are standing at.
Nobody moves the traffic. Two people lift the rider by the arms, which is the one thing nobody
should do. The ambulance is eleven minutes away.

The camera on the pole above them saw all of it, at five frames a second, from the first second.
Today that footage is used **after** the event, for the file.

**This notebook asks what that camera should do in the four minutes before the ambulance arrives.**

---

### What we will build

A camera watching one junction, and everything that hangs off it:

1. A **detector** that knows a crash from a red light, a near miss, and a mechanic under a van.
2. A **dispatch packet** that goes out the second the alarm is confirmed, not when the AI is sure.
3. A **hazard map** and a safe way in, so nobody is sent across a live lane.
4. A **public screen** that shows one approved instruction at a time and checks it was followed.
5. An honest **benchmark**: the same crash with and without the beacon.

### What it is not

It is not an AI doctor. It never names an injury. It never invents a first-aid instruction. A
human dispatcher can take the screen away from it at any moment, and that branch is checked first
in the code.

> ⚠️ **Everything here is simulated.** The traffic, the crashes and the people are invented so the
> ideas can be studied safely. Nothing in this notebook is a medical device, and no part of it may
> be used to decide the care of a real person.
""")

md(f"""
🎬 **The illustrated version.**
<a href="{APP}/?stage=start" target="illustration">Open the illustration app once, in a second tab</a>,
and leave it open beside this notebook.

Each section below says which **step** to show over there. Move that tab with the **◀ ▶** buttons
at the foot of its page, or jump straight to any step from the **Learning journey** list on its
front page. That way you finish with two tabs open, not twenty.
""")

md(r"""
### Contents

1. The golden minutes
2. What a camera actually gives you
3. Building the virtual junction
4. Five ways to lie in a road
5. The clues that only exist in time
6. **Model 1** — one frame, one rule
7. **Model 2** — a six-second rule
8. **Model 3** — a forest over a window
9. **Model 4** — a network on the raw six seconds
10. How long to wait before believing
11. Red lights outnumber crashes
12. The call that cannot wait
13. Reading the danger
14. The safe way in
15. One instruction at a time
16. Watching the helper
17. Giving the crowd jobs
18. Did it help?
19. What it still gets wrong
20. The rules that do not move
""")

# ============================================================ SETUP
md(r"""
## Setup

Colab already has everything we need. If you run this somewhere else, remove the `#` on the
install line.

TensorFlow is used once, in section 9, for the sequence network. If it is missing the notebook
uses a smaller network from scikit-learn instead, so **every section still produces a result**.
""")

co(r"""
# !pip install numpy pandas scikit-learn matplotlib tensorflow

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier

# One seed, so you get the same junction every time you run the notebook.
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
    keras.utils.set_random_seed(7)
    # Ask TensorFlow to give the same answer every run, so your numbers match the text.
    tf.config.experimental.enable_op_determinism()
    KERAS = True
except Exception:
    KERAS = False
    print("TensorFlow not found - a smaller scikit-learn network will be used instead.")

print("Ready.  Deep learning library available:", KERAS)
""")

# ============================================================ 1. GOLDEN MINUTES
md(r"""
## 1 · The golden minutes

An ambulance in a large city takes somewhere between **8 and 12 minutes** to arrive. That is a
good service. It is also far longer than several things can wait.

- A blocked airway is measured in **minutes**.
- Heavy bleeding from a leg can empty a person in **three to five minutes**.
- A rider lying face down in a live lane is in danger from the next vehicle, not from the crash.

So the useful question is not "how do we get the ambulance there faster". It is **"what happens in
the first four minutes"** — and the answer today is that twenty people stand in a circle, several
of them filming, while nobody does the four things that matter.

The chart below is the shape everyone in emergency medicine works to. It is drawn, not measured —
the exact curve depends on what happened. The point is only that it falls steeply and early.
""")

co(r"""
minutes = np.arange(0, 11, 0.25)
# A drawn curve, not data: the chance of a good outcome falls fastest at the start.
chance = 100 * np.exp(-minutes / 4.5)

fig, ax = plt.subplots()
ax.plot(minutes, chance, color=BLUE, lw=2.5)
ax.axvspan(0, 4, color=GREEN, alpha=0.12)
ax.text(1.2, 55, "before anyone\nprofessional arrives", color=GREEN, fontsize=9)
ax.set_xlabel("minutes after the crash")
ax.set_ylabel("relative chance of a good outcome")
ax.set_title("Why the first four minutes are the whole problem")
plt.tight_layout(); plt.show()

print("The camera is already on the pole. It saw the crash at second zero.")
print("Everything in this notebook happens inside the green band.")
""")

md(r"""
**Read it like this.** Nothing we build makes the ambulance faster. Everything we build moves work
into the green band: the call, the traffic, the safe approach, and the first pair of hands.
""")
see("golden", "Why seconds are the whole problem")

# ============================================================ 2. THE CAMERA
md(r"""
## 2 · What a camera actually gives you

It is easy to imagine the camera "seeing a crash". It does not. A modern traffic camera with a
detector and a tracker gives you this, five times a second:

| What comes out | Example |
|---|---|
| A **box** around each object | `car`, `motorcycle`, `person`, `bus` |
| A **class** for the box | with a confidence, which is often wrong at distance |
| An **id** that follows the object | so box 14 in this frame is box 14 in the next |
| A **position** on the road | after correcting for the camera angle |

Everything else has to be worked out. From boxes and ids we can compute ten numbers per frame, and
those ten numbers are all any model in this notebook is allowed to see:

| Signal | Meaning | How it is really obtained |
|---|---|---|
| `person_road` | is anybody inside the carriageway | the box centre falls in the lane area |
| `person_low` | is anybody lying down | the box is wider than it is tall |
| `low_still` | is that person moving | the id barely moves between frames |
| `crowd` | people within about 6 m of them | count of person boxes nearby |
| `veh_stopped` | vehicles halted in the lane | tracks whose speed is near zero |
| `min_gap` | closest two tracks came, in metres | distance between box centres |
| `closing` | how fast they were closing, m/s | change in that distance |
| `decel_max` | hardest braking seen, m/s² | change in a vehicle's speed |
| `smoke` | smoke or fire, 0 to 1 | a separate small image classifier |
| `flow` | average speed of moving traffic | mean of the vehicle speeds |

**Two honest problems, built in from the start.**

*Posture guessed from a box is wrong now and then.* A person bending over a bag looks like a person
lying down for a frame or two. We flip about 4 % of these on purpose.

*A person behind a van does not exist.* About 3 % of the time the detector simply does not report
the person at all. No amount of clever modelling recovers a frame that was never seen.
""")
see("camera", "Boxes, tracks and signals")

# ============================================================ 3. BUILD
md(r"""
## 3 · Building the virtual junction

We cannot use real crash footage, so we build a junction that behaves like one. Each clip is
**24 seconds** long at **5 frames a second**, which is what a small edge computer on a pole can
actually process.

Fourteen kinds of clip. Nine of them are ordinary, and that is deliberate — a junction is quiet
almost all of the time, and every one of these quiet clips is a way for a detector to embarrass
itself:

| Quiet clip | Why it is in here |
|---|---|
| Traffic flows | the baseline |
| Someone crosses the road | a person in the carriageway, perfectly fine |
| **A car brakes hard and misses** | the near miss: an impact signature with no impact |
| Someone crouches at the kerb | a person low, close to the road |
| **A mechanic lies under a van** | low, still, in the road, for the whole clip |
| A fallen advertising board | the detector calls it a person, and it never moves |
| A crowd builds at the bus stop | people gathering, nothing wrong |
| **The signal turns red** | traffic stops dead for twenty seconds, all day long |
| Rush-hour crawl | slow traffic that is not a crash |

And five that are real:

| Incident | What makes it different |
|---|---|
| Motorcycle down, rider still | the textbook case |
| **Motorcycle down, rider gets up** | still an incident: blocked lane, shaken rider, bike in the road |
| A pedestrian is knocked down | the victim was already in the road, crossing |
| A van rolls over, smoke rising | **nobody is visible on the road at all** |
| **A crash behind a stopped bus** | the camera cannot see it for about ten seconds |

The bold rows are the ones that decide whether a detector is any good.

### Three rules the generator follows

**Nothing appears instantly.** Traffic takes two to five seconds to come to a stop. A crowd takes
ten seconds or more to gather. Smoke builds. This matters more than it sounds: if the aftermath
appeared on the impact frame, every model would look like it detects crashes in zero seconds, and
"seconds until the alarm" would be a meaningless number.

**A near miss has exactly a crash's impact signature.** Same gap between the tracks, same braking,
same closing speed. From 30 metres up a pole, a miss by half a metre and a hit look the same for
that instant. The *only* difference is what happens in the next few seconds — the traffic starts
moving again, and nobody is left lying in the road.

**The mix is not balanced.** There are eight red lights for every four rider-down crashes, because
that is roughly what a camera sees. Section 11 is about what happened when we got that wrong.
""")

co(r"""
FPS        = 5                     # frames a second the edge box looks at
CLIP_SECS  = 24
FRAMES     = FPS * CLIP_SECS
WIN        = 6 * FPS               # a six second window of history
LANE       = (6.0, 14.0)           # the carriageway, in metres across a 20 m view

# incident: is this a real emergency.  mix: how many clips of this kind, per unit of scale.
SCENARIOS = {
    "normal":         dict(incident=0, mix=8, tag="Traffic flows"),
    "crossing":       dict(incident=0, mix=5, tag="Someone crosses the road"),
    "hard_brake":     dict(incident=0, mix=4, tag="A car brakes hard, and misses"),
    "shoe_tie":       dict(incident=0, mix=3, tag="Someone crouches at the kerb"),
    "worker":         dict(incident=0, mix=2, tag="A mechanic lies under a van"),
    "poster":         dict(incident=0, mix=2, tag="A fallen board that looks like a person"),
    "bus_crowd":      dict(incident=0, mix=3, tag="A crowd builds at the bus stop"),
    "red_light":      dict(incident=0, mix=8, tag="The signal turns red and traffic waits"),
    "jam":            dict(incident=0, mix=5, tag="Slow rush-hour crawl"),
    "collision_down": dict(incident=1, mix=4, tag="Motorcycle down, rider not moving"),
    "collision_up":   dict(incident=1, mix=3, tag="Motorcycle down, rider walks off"),
    "ped_fall":       dict(incident=1, mix=3, tag="A pedestrian is knocked down"),
    "rollover":       dict(incident=1, mix=2, tag="A van rolls over, smoke rising"),
    "occluded":       dict(incident=1, mix=2, tag="A crash behind a stopped bus"),
}

# The ten numbers the camera produces every frame.
SIGNALS = ["person_road", "person_low", "low_still", "crowd", "veh_stopped",
           "min_gap", "closing", "decel_max", "smoke", "flow"]

print(f"{len(SCENARIOS)} kinds of clip, {sum(v['incident'] for v in SCENARIOS.values())} of them real incidents.")
print(f"Each clip: {CLIP_SECS} s at {FPS} frames a second = {FRAMES} frames of {len(SIGNALS)} numbers.")
""")

co(r"""
def wander(n, sd, k=5):
    "Slow drifting noise. Real signals wander; they do not jump at every frame."
    w = rng.normal(0, sd, n + k)
    return np.convolve(w, np.ones(k) / k, mode="same")[:n] * np.sqrt(k)


def make_clip(kind):
    "One 24-second clip of what the camera's tracker reports, frame by frame."
    n = FRAMES
    s = {k: np.zeros(n) for k in SIGNALS}
    s["flow"]      += rng.uniform(9.5, 12.5) + wander(n, 0.35)
    s["min_gap"]   += rng.uniform(14, 22) + wander(n, 1.2)
    s["closing"]   += rng.uniform(0.5, 2.5) + np.abs(wander(n, 0.6))
    s["decel_max"] += np.abs(rng.normal(0.9, 0.45, n))
    s["crowd"]     += rng.integers(0, 2, n)
    impact = np.nan

    def down(start, until=n, still=True):
        "Somebody is on the carriageway and low, from `start` onwards."
        idx = np.arange(int(start), int(until))
        s["person_road"][idx] = 1
        s["person_low"][idx] = 1
        s["low_still"][idx] = 1.0 if still else 0.0

    def ramp(start, secs):
        "0 before `start`, sliding up to 1 over `secs` seconds. Nothing appears instantly."
        return np.clip((np.arange(n) - start) / max(1.0, secs * FPS), 0, 1)

    def hit(frame, gap=None, close=9.0, decel=7.5):
        "The half second in which two tracks meet - or nearly meet."
        gap = rng.uniform(0.25, 1.30) if gap is None else gap
        idx = np.arange(int(frame), min(n, int(frame) + 3))
        # a distance measured from a camera 30 m away is not measured well
        s["min_gap"][idx]   = max(0.05, gap + rng.normal(0, 0.35))
        s["closing"][idx]   = close + rng.uniform(-1.5, 1.5)
        s["decel_max"][idx] = decel + rng.uniform(-1.5, 2.0)

    if kind == "normal":
        pass

    elif kind == "crossing":
        a = rng.integers(20, 60)
        idx = np.arange(a, min(n, a + rng.integers(20, 35)))
        s["person_road"][idx] = 1
        s["veh_stopped"][idx] = rng.integers(1, 3)
        s["flow"][idx] *= 0.35
        s["min_gap"][idx] = rng.uniform(3.0, 6.0)

    elif kind == "hard_brake":
        a = int(rng.integers(25, 70))
        hit(a)                                    # exactly a collision's signature
        # traffic stops the way it stops for a crash - and then starts again
        stop = ramp(a, rng.uniform(1.5, 2.5)) * (1 - ramp(a + int(2.5 * FPS), rng.uniform(2, 3)))
        s["flow"] *= (1 - 0.75 * stop)
        s["veh_stopped"] += rng.uniform(2, 4) * ramp(a + FPS, 1.5) * (1 - ramp(a + 3 * FPS, 2.5))
        # half are a pedestrian stepping out, half a car cutting in
        if rng.random() < 0.5:
            s["person_road"][np.arange(max(0, a - 8), min(n, a + 14))] = 1

    elif kind == "shoe_tie":
        a = int(rng.integers(10, 55))
        down(a, until=min(n, a + rng.integers(35, 70)))
        s["low_still"][:] = np.where(s["person_low"] > 0, rng.uniform(0.6, 1.0), 0)

    elif kind == "worker":
        down(0)                                   # there before we started looking
        s["veh_stopped"][:] = 1
        s["flow"] *= 0.8

    elif kind == "poster":
        keep = rng.random(n) < 0.72                # the detector calls it a person most frames
        s["person_road"][keep] = 1
        s["person_low"][keep] = 1
        s["low_still"][keep] = 1

    elif kind == "bus_crowd":
        a = int(rng.integers(10, 50))
        idx = np.arange(a, n)
        s["crowd"][idx] = np.clip(np.linspace(1, rng.uniform(6, 9), len(idx)), 0, 12)

    elif kind == "red_light":
        a = int(rng.integers(10, 45))
        hold = int(rng.uniform(14, 22) * FPS)
        stop = ramp(a, rng.uniform(2, 3.5)) * (1 - ramp(a + hold, 3.0))
        s["flow"] *= (1 - 0.92 * stop)
        s["veh_stopped"] += rng.uniform(4, 8) * stop

    elif kind == "jam":
        s["flow"] *= rng.uniform(0.18, 0.35)
        s["veh_stopped"] += rng.uniform(1, 4) * np.clip(wander(n, 0.5) + 1, 0, 2)

    elif kind in ("collision_down", "collision_up"):
        a = int(rng.integers(30, 70))
        impact = a / FPS
        hit(a)
        s["flow"] *= (1 - 0.80 * ramp(a, rng.uniform(2.5, 4.5)))
        s["veh_stopped"] += rng.uniform(3, 6) * ramp(a + 2 * FPS, rng.uniform(3, 6))
        s["crowd"]       += rng.uniform(3.5, 7.5) * ramp(a + 4 * FPS, rng.uniform(8, 14))
        if kind == "collision_down":
            down(a + 3)                           # the rider slides, then stops
        else:
            up = a + int(rng.integers(8, 18))     # up in a few seconds, walks to the kerb
            down(a + 3, until=up)
            s["person_road"][np.arange(up, min(n, up + 20))] = 1

    elif kind == "ped_fall":
        a = int(rng.integers(30, 70))
        impact = a / FPS
        hit(a, gap=rng.uniform(0.3, 1.0), close=rng.uniform(4.5, 7.0), decel=rng.uniform(5.0, 8.0))
        s["flow"] *= (1 - 0.70 * ramp(a, rng.uniform(2.5, 5.0)))
        s["veh_stopped"] += rng.uniform(2, 5) * ramp(a + 2 * FPS, rng.uniform(3, 6))
        s["crowd"]       += rng.uniform(2.5, 6.0) * ramp(a + 5 * FPS, rng.uniform(8, 15))
        s["person_road"][np.arange(max(0, a - 10), a)] = 1      # they were crossing
        down(a + 2)

    elif kind == "rollover":
        a = int(rng.integers(30, 70))
        impact = a / FPS
        hit(a, gap=rng.uniform(0.4, 1.2), close=rng.uniform(5.0, 8.0), decel=rng.uniform(6.0, 9.5))
        s["flow"] *= (1 - 0.75 * ramp(a, rng.uniform(3.0, 5.0)))
        s["veh_stopped"] += rng.uniform(2, 5) * ramp(a + 2 * FPS, rng.uniform(3, 6))
        s["smoke"]       += rng.uniform(0.55, 0.95) * ramp(a + 3 * FPS, rng.uniform(5, 9))
        s["crowd"]       += rng.uniform(1.5, 4.0) * ramp(a + 6 * FPS, rng.uniform(8, 15))

    elif kind == "occluded":
        # the crash happens behind a bus that has just pulled in
        a = int(rng.integers(25, 55))
        impact = a / FPS
        clear = a + int(rng.uniform(9, 13) * FPS)
        s["flow"] *= (1 - 0.80 * ramp(a, rng.uniform(2.0, 4.0)))
        s["veh_stopped"] += rng.uniform(3, 6) * ramp(a + FPS, rng.uniform(2, 4))
        if clear < n:
            down(clear)
            s["crowd"] += rng.uniform(3.0, 6.0) * ramp(clear, rng.uniform(2, 5))

    # ---------- the detector is not perfect ----------
    flip = rng.random(n) < 0.04                   # posture read from a box is noisy
    s["person_low"]  = np.where(flip, 1 - s["person_low"], s["person_low"])
    miss = rng.random(n) < 0.03                   # the person is not found at all
    s["person_road"] = np.where(miss, 0, s["person_road"])
    s["person_low"]  = np.where(miss, 0, s["person_low"])
    s["crowd"] = np.clip(s["crowd"] + rng.integers(-1, 2, n), 0, 15)
    s["smoke"] = np.clip(s["smoke"] + rng.normal(0, 0.03, n), 0, 1)
    s["flow"]  = np.clip(s["flow"] + wander(n, 0.3), 0, 25)

    out = pd.DataFrame(s)
    out.insert(0, "t", np.arange(n) / FPS)
    out["incident"] = SCENARIOS[kind]["incident"]
    out["impact_t"] = impact
    # the truth we score against: from the moment of impact onwards
    out["truth"] = ((out["incident"] == 1) &
                    (out["t"] >= (impact if impact == impact else 1e9))).astype(int)
    return out


def build_clips(scale=6, counts=None):
    "A pile of clips from one camera, mixed the way the road mixes them."
    parts, meta, cid = [], [], 0
    for kind, spec in SCENARIOS.items():
        for _ in range(counts[kind] if counts else spec["mix"] * scale):
            df = make_clip(kind)
            df.insert(0, "clip_id", cid)
            df.insert(1, "kind", kind)
            parts.append(df)
            meta.append(dict(clip_id=cid, kind=kind, incident=spec["incident"],
                             impact_t=df["impact_t"].iloc[0]))
            cid += 1
    return pd.concat(parts, ignore_index=True), pd.DataFrame(meta)


clips, meta = build_clips(scale=6)
print(f"{len(meta)} clips, {int(meta.incident.sum())} of them real incidents.")
print(f"{len(clips):,} frames in total - about {len(clips) / FPS / 60:.0f} minutes of camera time.")
print()
print(meta.groupby("kind", sort=False).size().to_string())
""")

md(r"""
Here are the first two seconds of one crash clip, exactly as the models will see it. Nothing in
these columns says "collision". That word has to be worked out.
""")

co(r"""
one = clips[clips.clip_id == meta[meta.kind == "collision_down"].clip_id.iloc[0]]
imp = one.impact_t.iloc[0]
print(f"impact at t = {imp} s")
print(one[(one.t >= imp - 0.6) & (one.t <= imp + 1.4)][
    ["t"] + SIGNALS].round(2).to_string(index=False))
""")
see("camera", "Boxes, tracks and signals")

# ============================================================ 4. LOOKALIKES
md(r"""
## 4 · Five ways to lie in a road

Take a single photograph of somebody lying near the kerb. Which of these is it?

1. A rider who has just been knocked off a motorcycle.
2. A pedestrian who has been struck by a car.
3. Somebody crouching to tie a lace.
4. A mechanic working under a van.
5. A large advertising board that has blown over.

In one frame, **these are the same picture**. There is nothing in the pixels that separates them.
A person who has been lying there for two minutes looks exactly like one who arrived two seconds
ago.

The chart below shows the one thing that does separate them: how the situation *arrived*. The
mechanic and the board are already there when the clip starts. The crash cases go from nothing to
somebody down in the space of one second.
""")

co(r"""
def lying_seconds(part):
    "How long somebody has been lying in the road, in seconds, at each frame."
    # Believe the posture only after taking the middle value of the last second - a posture
    # guessed from a box flickers, and every rule below would break on that flicker.
    raw = ((part.person_low > 0) & (part.person_road > 0)).astype(float)
    smooth = raw.rolling(FPS, min_periods=1).median().round().to_numpy()
    run, out = 0, []
    for v in smooth:
        run = run + 1 if v else 0
        out.append(run / FPS)
    return np.array(out)


fig, ax = plt.subplots(figsize=(9.5, 3.8))
for kind, colour in zip(["shoe_tie", "worker", "poster", "collision_down", "ped_fall"],
                        [GREY, ORANGE, PURPLE, RED, BLUE]):
    part = clips[clips.clip_id == meta[meta.kind == kind].clip_id.iloc[0]]
    ax.plot(part.t, lying_seconds(part), color=colour, lw=2, label=SCENARIOS[kind]["tag"])
ax.axhline(6, color="black", ls="--", lw=1)
ax.text(0.3, 6.4, "a six-second rule fires above this line", fontsize=9)
ax.set_xlabel("seconds into the clip"); ax.set_ylabel("seconds lying in the road")
ax.set_title("Every line here is a person lying in a road. Two of them are hurt.")
ax.legend(fontsize=8, loc="upper left")
plt.tight_layout(); plt.show()
""")

md(r"""
**Read it like this.** The mechanic's line climbs from the very first frame and never comes down —
he was already under the van before we started looking. The two crash lines sit at zero, stay at
zero, and then start climbing part-way through the clip: that is the moment somebody went from
upright to down.

The board's line is the odd one, and it is worth a second look. It climbs, drops to zero, climbs
again — a sawtooth. Nothing moved. The detector simply loses a fallen board every few seconds, the
count starts over, and a six-second rule fires only when it happens to hold on long enough. **A
detector that behaves differently depending on whether it noticed something is not a detector you
can reason about**, and that is a bigger problem than the false alarm itself.

A rule that only asks *"is somebody lying there"* cannot separate any of these. A rule that asks
*"did somebody go from upright to down, just now, while the traffic stopped"* can.
""")
see("lookalike", "Why one frame cannot decide")

# ============================================================ 5. TIME FEATURES
md(r"""
## 5 · The clues that only exist in time

Ask somebody watching the screen what they saw, and they will not describe boxes. They will say:

> "The traffic stopped, and it stayed stopped. Somebody went down. People started walking towards
> one spot."

Not one of those sentences can be read from a single frame. Each needs the last few seconds held in
memory. So we build eleven numbers over a **six-second window**, and hand those to the models
instead of the raw picture:

| Feature | The question it answers |
|---|---|
| `down_secs` | how long has somebody been lying still in the road |
| `crowd` / `crowd_growth` | how many people are there, and how fast is that growing |
| `flow_drop` | how much has the traffic slowed compared with four seconds ago |
| `decel_peak` | hardest braking anywhere in the window |
| `gap_min` | closest two tracks came in the window |
| `close_max` | fastest they were closing |
| `smoke_max` | worst smoke reading in the window |
| `still_frac` | what share of the window somebody was motionless |
| `road_frac` | what share of the window somebody was in the carriageway |
| `stopped_max` | most vehicles halted at once |

Note the one that is **missing on purpose**: the plain traffic speed. An early version included it,
and the model quietly learned *"this clip is a bit slower than average, so it is a crash"* — which
is a fact about our clips, not about crashes. Only the **change** in flow survived.
""")

co(r"""
def add_time_features(df):
    "The clues that do not exist in a single frame."
    f = df.copy()
    raw = ((f.person_low > 0) & (f.person_road > 0)).astype(float)
    f["lying"] = (raw.groupby(f.clip_id, sort=False)
                     .transform(lambda s: s.rolling(FPS, min_periods=1).median())
                     .round().astype(int))
    secs = []
    for _, part in f.groupby("clip_id", sort=False):
        run, out = 0, []
        for v in part.lying.to_numpy():
            run = run + 1 if v else 0
            out.append(run / FPS)
        secs.extend(out)
    f["down_secs"] = secs

    g = f.groupby("clip_id", sort=False)
    f["crowd_growth"] = g["crowd"].transform(lambda s: s - s.shift(3 * FPS)).fillna(0)
    f["flow_drop"]    = g["flow"].transform(lambda s: s.shift(4 * FPS) - s).fillna(0)
    f["decel_peak"]   = g["decel_max"].transform(lambda s: s.rolling(WIN, min_periods=1).max())
    f["gap_min"]      = g["min_gap"].transform(lambda s: s.rolling(WIN, min_periods=1).min())
    f["close_max"]    = g["closing"].transform(lambda s: s.rolling(WIN, min_periods=1).max())
    f["smoke_max"]    = g["smoke"].transform(lambda s: s.rolling(WIN, min_periods=1).max())
    f["still_frac"]   = g["low_still"].transform(lambda s: s.rolling(WIN, min_periods=1).mean())
    f["road_frac"]    = g["person_road"].transform(lambda s: s.rolling(WIN, min_periods=1).mean())
    f["stopped_max"]  = g["veh_stopped"].transform(lambda s: s.rolling(WIN, min_periods=1).max())
    return f


FEATURES = ["down_secs", "crowd", "crowd_growth", "flow_drop", "decel_peak", "gap_min",
            "close_max", "smoke_max", "still_frac", "road_frac", "stopped_max"]

data = add_time_features(clips)
print(f"{len(FEATURES)} window features over {len(data):,} frames.")

# What separates a real crash from the clips that look most like one? Compare the six
# seconds after the busiest moment of each clip - the impact for a crash, and the hardest
# braking or the deepest traffic stop for a quiet clip. Comparing a crash's worst six
# seconds against a whole quiet clip would flatter the model and prove nothing.
def profile(kind, secs_after=6):
    rows = []
    for c in data[data.kind == kind].clip_id.unique():
        part = data[data.clip_id == c]
        if SCENARIOS[kind]["incident"]:
            t0 = part.impact_t.iloc[0]
        else:
            # a quiet clip's "impact" is its hardest braking moment
            t0 = float(part.t.iloc[int(np.argmax(part.decel_max.to_numpy()))])
        rows.append(part[(part.t >= t0) & (part.t <= t0 + secs_after)][FEATURES].mean())
    return pd.concat(rows, axis=1).mean(axis=1)

look = pd.DataFrame({
    "real crash": profile("collision_down"),
    "near miss":  profile("hard_brake"),
    "red light":  profile("red_light"),
    "mechanic":   profile("worker"),
}).round(2)
print()
print(look.to_string())
""")

md(r"""
**Read the table one row at a time.**

The crash and the near miss are **identical at the moment of the bang**: `decel_peak` 7.6 against
7.9, `gap_min` 0.9 against 0.8, `close_max` 8.85 against 8.86. There is nothing there to tell them
apart, and no cleverer model would find any, because we built them that way on purpose.

They separate on what came **next**: `down_secs` 2.2 against 0.0, `still_frac` 0.44 against 0.00,
`road_frac` 0.43 against 0.14. Somebody is on the ground after one of them and not after the other.

Look at `stopped_max` while you are there: the near miss scores *higher* than the crash (2.2 against
1.4), because the crash's traffic is still coming to a halt during those six seconds. The single
most obvious clue — "the traffic stopped" — points the wrong way here, and points hardest of all at
the red light (4.8), which is not an incident at all.

**No single one of these features solves the problem. The combination does.**
""")
see("clues", "Feature engineering")

# ============================================================ 6. MODEL 1
md(r"""
## 6 · Model 1 — one frame, one rule

The simplest system anybody would build, and the one a lot of cameras actually run:

> If a person is lying in the carriageway, raise the alarm.

Before we can score it we need to agree on what a good detector means. Three numbers, and they
pull against each other:

- **Incidents missed** — a real crash where no alarm was ever raised. The worst failure.
- **Seconds to the alarm** — measured from the moment of impact, not from the start of the clip.
- **False alarms per hour** — a control-room operator watching a video call for a lace being tied.

We split the clips into three piles, **inside each kind** so that no scenario is missing from the
exam: half to learn from, a fifth to set the dials on, and the rest to be judged on.
""")

co(r"""
def split_clips(meta, seed=7):
    "Three piles of clips: to learn from, to set the dial, to be judged on."
    r = np.random.default_rng(seed)
    train, tune, test = [], [], []
    for kind in SCENARIOS:
        ids = meta.loc[meta.kind == kind, "clip_id"].to_numpy().copy()
        r.shuffle(ids)
        n = len(ids)
        train.extend(ids[:int(0.5 * n)])
        tune.extend(ids[int(0.5 * n):int(0.7 * n)])
        test.extend(ids[int(0.7 * n):])
    return np.array(train), np.array(tune), np.array(test)


TRAIN, TUNE, TEST = split_clips(meta)
print(f"{len(TRAIN)} clips to learn from, {len(TUNE)} to set dials, {len(TEST)} to be judged on.")
print(f"The exam pile holds {int(meta[meta.clip_id.isin(TEST)].incident.sum())} real incidents "
      f"and {int((~meta[meta.clip_id.isin(TEST)].incident.astype(bool)).sum())} quiet clips.")


def score(fire, clips_to_use, name=""):
    "Seconds lost, incidents missed, and false alarms per hour of quiet footage."
    fire = np.asarray(fire)
    lag, missed, caught, false_clips, benign = [], 0, 0, 0, 0
    for c in clips_to_use:
        row = meta[meta.clip_id == c].iloc[0]
        part = data[data.clip_id == c]
        times = part.t.to_numpy()[np.flatnonzero(fire[part.index])]
        if row.incident:
            after = times[times >= row.impact_t]
            if len(after):
                caught += 1
                lag.append(after[0] - row.impact_t)
            else:
                missed += 1
        else:
            benign += 1
            false_clips += int(len(times) > 0)
    hours = benign * CLIP_SECS / 3600
    return {"Detector": name, "Incidents missed": missed,
            "Seconds to alarm": round(float(np.median(lag)), 1) if lag else np.nan,
            "False alarms/hour": round(false_clips / hours, 1) if hours else np.nan,
            "Quiet clips called in": f"{false_clips} of {benign}"}


model1 = ((data.person_low > 0) & (data.person_road > 0)).to_numpy()
r1 = score(model1, TEST, "1. One frame")
print()
for k, v in r1.items():
    print(f"  {k:24s} {v}")
""")

md(r"""
Now look at *which* clips it called in, because the average hides the story.
""")

co(r"""
def by_scenario(fires):
    "For each kind of clip: incidents missed, or quiet clips wrongly called in."
    rows = []
    for kind, spec in SCENARIOS.items():
        ids = [c for c in meta[meta.kind == kind].clip_id if c in set(TEST)]
        row = {"clip": spec["tag"], "real": "yes" if spec["incident"] else "no", "n": len(ids)}
        for name, fire in fires.items():
            s = score(fire, ids)
            row[name] = s["Incidents missed"] if spec["incident"] else \
                int(s["Quiet clips called in"].split()[0])
        rows.append(row)
    return pd.DataFrame(rows)


print(by_scenario({"model 1": model1}).to_string(index=False))
""")

md(r"""
**Two failures, and they are opposite failures.**

It calls in the crouching pedestrian, the mechanic and the fallen board — every single time. And it
never sees the rollover, because in a rollover **nobody is lying on the road at all**; the driver
is inside the vehicle.

That is the shape of every naive detector: loud about the things that do not matter, silent about
the thing that does.
""")
see("frame_rule", "Model 1")

# ============================================================ 7. MODEL 2
md(r"""
## 7 · Model 2 — a six-second rule

The obvious fix. Do not believe it straight away:

> If somebody has been lying still in the carriageway for **six seconds**, raise the alarm.
> Also raise it if there is smoke.

The smoke rule is there specifically to catch the rollover that model 1 could not see. This is a
genuinely better system, and it is what a careful engineer writes on the second afternoon.
""")

co(r"""
model2 = ((data.down_secs >= 6.0) | (data.smoke_max >= 0.5)).to_numpy()
r2 = score(model2, TEST, "2. Six-second rule")
print(pd.DataFrame([r1, r2]).to_string(index=False))
print()
print(by_scenario({"model 1": model1, "model 2": model2}).to_string(index=False))
""")

md(r"""
**What got better.** The smoke rule catches the rollover. The near miss and the pedestrian crossing
stop causing alarms, because neither leaves anybody on the ground.

**What did not.** Six seconds is also how long it takes to tie a lace. The mechanic never moves at
all, so he is reported every time. And there is a failure that no amount of waiting can fix:

> **The rider who gets up.** A motorcycle is knocked over, the rider is down for three seconds,
> then stands and walks to the kerb. The lane is blocked, the bike is in the road, and a person who
> has just been hit is standing at the roadside in shock. The six-second rule never fires. Not once.

That is the point where hand-written rules run out. The rule was not too slow — it was asking the
wrong question. It asked *"is somebody lying down"*. The question that matters is *"did something
happen here"*.
""")
see("timer_rule", "Model 2")

# ============================================================ 8. MODEL 3
md(r"""
## 8 · Model 3 — a forest over a window

Instead of writing the rule, we show a model a few hundred clips from this junction and let it work
out which combinations of the eleven features mean trouble.

A **random forest** is a few hundred decision trees. Each tree is grown on a different random slice
of the clips and asks a different sequence of yes/no questions (`stopped_max > 3.1?`,
`down_secs > 1.4?`). To score a frame, every tree votes, and the share of trees voting "incident"
is used as a probability between 0 and 1.

Two reasons it suits this problem:

- It handles **combinations** naturally — "stopped traffic *and* somebody down *and* a growing
  crowd" is three questions deep in a tree, and no human has to guess the thresholds.
- The trees can be read afterwards, which matters when a public authority asks why the machine
  called them out.
""")

co(r"""
forest = RandomForestClassifier(n_estimators=150, max_depth=10, min_samples_leaf=25,
                                class_weight="balanced_subsample", n_jobs=-1, random_state=7)
train = data[data.clip_id.isin(TRAIN)]
forest.fit(train[FEATURES].to_numpy(np.float32), train.truth.to_numpy())

risk = forest.predict_proba(data[FEATURES].to_numpy(np.float32))[:, 1]
data["risk"] = risk
print("Trained on", f"{len(train):,}", "frames from", len(TRAIN), "clips.")

imp = pd.Series(forest.feature_importances_, index=FEATURES).sort_values()
fig, ax = plt.subplots(figsize=(9.5, 3.6))
ax.barh(imp.index, imp.values, color=BLUE)
ax.set_xlabel("how much the forest leans on this clue")
ax.set_title("What the window model actually uses")
plt.tight_layout(); plt.show()
""")

md(r"""
Before scoring it we need one more piece — and it turns out to be the most important design
decision in the whole detector.
""")
see("forest", "Model 3, a random forest")

# ============================================================ 9. THE WAIT
md(r"""
## 9 · How long to wait before believing

At the instant of the bang, a near miss and a crash are the same event. We built them that way on
purpose, because from a camera on a pole they *are* the same event.

Three seconds later they are not. One of them has driven away. The other has a stopped lane, a
person on the ground and people walking towards them.

So the detector gets one more dial: **the alarm must hold for N seconds before anybody is called.**

This single number sets the character of the whole system:

- Wait **zero** seconds and you alarm on every near miss.
- Wait **five** and you are almost never wrong, and you have spent five of the golden minutes'
  seconds doing nothing.

There is no correct setting. There is a choice, and it belongs to the people who answer the calls.
""")

co(r"""
def confirm(fire, secs):
    "Only believe an alarm once the evidence has held for `secs` seconds."
    k = int(round(secs * FPS))
    fire = np.asarray(fire)
    if k <= 1:
        return fire.copy()
    out = np.zeros(len(fire), bool)
    for _, part in data.groupby("clip_id", sort=False):
        idx = part.index.to_numpy()
        run, o = 0, np.zeros(len(idx), bool)
        for i, x in enumerate(fire[idx]):
            run = run + 1 if x else 0
            o[i] = run >= k
        out[idx] = o
    return out


rows = [score(confirm(risk >= 0.5, w), TEST, f"{w} s wait") for w in range(6)]
waits = pd.DataFrame(rows)
print(waits.to_string(index=False))

fig, ax = plt.subplots()
ax.plot(range(6), waits["Seconds to alarm"], "o-", color=BLUE, lw=2, label="seconds to the alarm")
ax.plot(range(6), waits["False alarms/hour"], "s-", color=ORANGE, lw=2, label="false alarms per hour")
ax.set_xlabel("seconds the system waits before believing itself")
ax.set_ylabel("cost")
ax.set_title("One dial, two costs, pulling in opposite directions")
ax.legend()
plt.tight_layout(); plt.show()
""")

co(r"""
WAIT = 3                                   # the setting this notebook goes with
model3 = confirm(risk >= 0.5, WAIT)
r3 = score(model3, TEST, "3. Window model")
print(pd.DataFrame([r1, r2, r3]).to_string(index=False))
print()
print(by_scenario({"model 1": model1, "model 2": model2, "model 3": model3}).to_string(index=False))
""")

md(r"""
**Three seconds is the setting this notebook goes with**, and the reasoning is worth stating out
loud: an incident that is never detected costs a life; a false alarm costs a control-room operator
twenty seconds of looking at a video feed. Those are not comparable costs, so the dial sits where
nothing is missed and the false alarms are rare enough that people still trust it.

Notice what the window model does that neither rule could:

- It catches the **rider who gets up**, which model 2 missed every time.
- It catches the **rollover** with nobody on the road, which model 1 could not see.
- It catches the crash **behind the bus** — late, but it catches it, from the traffic behaviour
  alone.
- It stops calling in the mechanic, the board and the crouching pedestrian.
""")
see("wait", "The confirmation dial")

# ============================================================ 10. MODEL 4
md(r"""
## 10 · Model 4 — a network on the raw six seconds

The forest only sees numbers **we invented**. Somebody had to decide that "seconds lying still" was
worth computing. If we missed a clue, the forest cannot use it.

A neural network can be handed the six seconds themselves: a 30 × 10 grid — thirty frames, ten
signals — with no features at all.

We use a small **1D convolutional network**. A 1D convolution slides a short filter along the time
axis and learns patterns like "this signal rises sharply and then stays high". That is exactly the
shape of a crash aftermath, and it is exactly what `down_secs` and `flow_drop` were hand-built to
capture.

**This is the fair version of the deep-learning question:** given the same clips, does learning the
features beat inventing them?
""")

co(r"""
def windows(ids):
    "Every frame becomes a 30 x 10 picture of the six seconds behind it."
    X, y, idx = [], [], []
    for c in ids:
        part = data[data.clip_id == c]
        arr, tru = part[SIGNALS].to_numpy(np.float32), part.truth.to_numpy()
        for i in range(WIN, len(part)):
            X.append(arr[i - WIN:i]); y.append(tru[i]); idx.append(part.index[i])
    return np.array(X), np.array(y), np.array(idx)


Xtr, ytr, _ = windows(TRAIN)
Xte, yte, ite = windows(TEST)
mu = Xtr.reshape(-1, len(SIGNALS)).mean(0)
sd = Xtr.reshape(-1, len(SIGNALS)).std(0) + 1e-6
print("training windows:", Xtr.shape, " -> thirty frames of ten signals each")

if KERAS:
    inp = keras.Input(shape=(WIN, len(SIGNALS)))
    x = layers.Conv1D(24, 5, activation="relu")(inp)
    x = layers.MaxPooling1D(2)(x)
    x = layers.Conv1D(24, 3, activation="relu")(x)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(24, activation="relu")(x)
    out = layers.Dense(1, activation="sigmoid")(x)
    net = keras.Model(inp, out)
    net.compile(optimizer=keras.optimizers.Adam(1e-3), loss="binary_crossentropy")
    net.fit((Xtr - mu) / sd, ytr, epochs=6, batch_size=256, verbose=0)
    p_te = net.predict((Xte - mu) / sd, verbose=0).ravel()
    net.summary()
else:
    from sklearn.neural_network import MLPClassifier
    net = MLPClassifier(hidden_layer_sizes=(48, 24), max_iter=60, random_state=7)
    flat = lambda X: ((X - mu) / sd).reshape(len(X), -1)
    net.fit(flat(Xtr), ytr)
    p_te = net.predict_proba(flat(Xte))[:, 1]
    print("scikit-learn network used instead of TensorFlow.")

risk_net = np.zeros(len(data))
risk_net[ite] = p_te
""")

co(r"""
net_rows = []
for w in (0, 2, 3, 4, 5):
    a = score(confirm(risk >= 0.5, w), TEST, f"forest, {w} s wait")
    b = score(confirm(risk_net >= 0.5, w), TEST, f"network, {w} s wait")
    net_rows += [a, b]
print(pd.DataFrame(net_rows).to_string(index=False))
""")

md(r"""
**This is not the result the notebook expected, so read it carefully.**

At every setting of the waiting dial the network is **quieter than the forest, or level with it** —
about half as many false alarms at the settings anybody would actually use — and it was told
nothing at all about roads. No feature list. No idea what "lying down" means. From ten raw traces
it worked out that a stopped lane which stays stopped, with somebody on the ground, is different
from a stopped lane that clears.

And at every setting it is **0.6 seconds slower**, because a convolution needs to see a bit
of the pattern before it responds, while `down_secs` starts counting immediately. At a five-second
wait it also starts missing incidents, which the forest does not.

So neither wins. They trade: the forest is quicker off the mark, the network is calmer. That is a
real engineering choice, and it is the honest version of the deep-learning question — not "which is
better" but "which mistake would you rather make".

**One thing is not a trade, though.** Somebody had to sit down and invent `down_secs`,
`crowd_growth` and `flow_drop` for the forest. If we had failed to think of one of them, the forest
could never use it. The network found what it needed on its own, from 160 clips. Give it a thousand
junctions and three years of footage, and that is the difference that grows.
""")
see("sequence", "Model 4, a 1D CNN")

# ============================================================ 11. THE MIX
md(r"""
## 11 · Red lights outnumber crashes

This section is the mistake we made, kept in on purpose, because it is the most useful thing in the
notebook.

The first version of this detector was built the way most teaching examples are built: roughly the
same number of clips of each kind. It scored beautifully on the exam pile. Then somebody asked what
it would do at 6 p.m. on an ordinary Tuesday.

A signal turns red every ninety seconds. Traffic stops dead and stays stopped for twenty seconds.
The model had learned — correctly, from the pile we gave it — that **stopped traffic means a
crash**, because in that pile the only thing that reliably stopped traffic *was* a crash.

Below we train the same model on a balanced pile and score it on the same exam clips.
""")

co(r"""
balanced_counts = {k: 12 for k in SCENARIOS}          # one of everything, tidy and wrong
clips_b, meta_b = build_clips(counts=balanced_counts)
data_b = add_time_features(clips_b)

forest_b = RandomForestClassifier(n_estimators=150, max_depth=10, min_samples_leaf=25,
                                  class_weight="balanced_subsample", n_jobs=-1, random_state=7)
forest_b.fit(data_b[FEATURES].to_numpy(np.float32), data_b.truth.to_numpy())

risk_b = forest_b.predict_proba(data[FEATURES].to_numpy(np.float32))[:, 1]
model3_b = confirm(risk_b >= 0.5, WAIT)

print(pd.DataFrame([
    score(model3,   TEST, "trained on a road-like mix"),
    score(model3_b, TEST, "trained on a balanced pile"),
]).to_string(index=False))

red = [c for c in meta[meta.kind == "red_light"].clip_id if c in set(TEST)]
jam = [c for c in meta[meta.kind == "jam"].clip_id if c in set(TEST)]
print()
print("Red-light clips called in:  road-like mix",
      score(model3, red)["Quiet clips called in"], " | balanced pile",
      score(model3_b, red)["Quiet clips called in"])
print("Rush-hour crawls called in: road-like mix",
      score(model3, jam)["Quiet clips called in"], " | balanced pile",
      score(model3_b, jam)["Quiet clips called in"])
""")

md(r"""
**Nothing about the model was changed to fix this.** Same features, same forest, same thresholds,
same eleven numbers. The only change was the pile of clips it learned from: eight red lights for
every four rider-down crashes, because that is closer to what the camera on that pole actually
sees. The balanced model still catches every incident — it simply also calls in **nine of the
fifteen red lights**, which is four times the false-alarm rate for no gain at all.

> **The rule to take away.** A training set is a claim about the world. If your claim is "crashes
> are as common as red lights", your model will believe you, and it will call the control centre
> every ninety seconds for the rest of its life.
""")
see("mix", "The training mix")

# ============================================================ 12. DISPATCH
md(r"""
## 12 · The call that cannot wait

The moment the alarm is confirmed, one thing happens before anything else: **the control centre is
told.** Not when the AI is confident. Not when the scene has been analysed. Immediately.

This ordering is not a detail. Every extra check before the call is time taken from the four
minutes, and every one of those checks can fail. The system's job is to call, and then to be
honest about what it does not know.

What goes in the packet, and what is deliberately left out:
""")

co(r"""
def dispatch_packet(clip_id, fire, confidence):
    "What goes to the control centre the moment an alarm is confirmed."
    part = data[data.clip_id == clip_id]
    hit = part[fire[part.index]]
    at = float(hit.t.iloc[0]) if len(hit) else np.nan
    now = part[part.t <= at + 1]
    return {
        "junction":       "NH-44 / Ring Road, camera 12",
        "location":       [17.4501, 78.3812],
        "seconds_into_clip": round(at, 1),
        "confidence":     round(float(confidence), 2),
        "person_on_road": bool(now.person_road.iloc[-1] > 0),
        "person_not_moving": bool(now.down_secs.iloc[-1] > 1.0),
        "people_nearby":  int(now.crowd.iloc[-1]),
        "smoke_or_fire":  bool(now.smoke.iloc[-1] > 0.3),
        "traffic_stopped": bool(now.veh_stopped.iloc[-1] >= 1),
        "clip":           "15 s before the alarm, faces and plates blurred",
        "NOT_known":      ["is the rider breathing", "is anyone trapped",
                           "how badly anyone is hurt"],
    }


example = int(meta[(meta.kind == "collision_down") & (meta.clip_id.isin(TEST))].clip_id.iloc[0])
part = data[data.clip_id == example]
conf = part.risk[model3[part.index]].iloc[0] if model3[part.index].any() else 0
packet = dispatch_packet(example, model3, conf)
for k, v in packet.items():
    print(f"  {k:20s} {v}")
""")

md(r"""
**The `NOT_known` field is the most important line in the packet.** A system that reports what it
cannot see is safer than one that is usually right, because the dispatcher can then ask the right
question of the person on the screen.

**Privacy is not an afterthought here.** The clip is fifteen seconds long, not fifteen minutes.
Faces and number plates of people who are not involved are blurred before it leaves the pole. The
system keeps the shortest clip that lets a dispatcher understand the scene, and nothing else.
""")
see("dispatch", "The dispatch packet")

# ============================================================ 13. HAZARDS
md(r"""
## 13 · Reading the danger

Now the second half of the project, which has nothing to do with detection.

Somebody is about to walk towards a person lying in a road. **The most dangerous thing a screen can
do is say "go and help" to a person standing on the wrong side of moving traffic.** Bystanders are
hit at crash scenes; it is one of the standard ways a single-casualty incident becomes a
double-casualty incident.

So before a single word of first aid is shown, the scene is scored. We lay a grid over the junction
and give every cell a cost — how bad it would be to stand there:

| Where | Cost | Why |
|---|---|---|
| Footpath | 1 | the baseline |
| The crash lane | 2 | the crash has closed it, so nothing is moving through it |
| **The opposite lane, still moving** | **25** | this is the one that hurts bystanders |
| The opposite lane, held at the signal | 2 | for as long as the signal holds it |
| Broken glass and debris | 9 | walkable, but not barefoot and not while carrying somebody |
| Smoke or spilled fuel | 60 | do not enter, at all |
| A fallen cable | 90 | do not enter, and keep everybody else out |

The numbers are not distances. They are **how much we do not want a person there**, and the gap
between 1 and 25 is the whole point: a live lane is not "a bit worse" than a footpath.
""")

co(r"""
GRID = (24, 8)                     # 2.5 m cells over a 60 m x 20 m view
ROAD_X, ROAD_Y = 60.0, 20.0


def hazard_grid(smoke=False, glass=True, wire=False):
    "Cost of standing in each cell. High cost is a place nobody should walk."
    nx, ny = GRID                          # rows 0-1 and 6-7 are footpath, rows 2-5 are road
    cost = np.ones((ny, nx))               # footpath
    cost[2:4, :] = 2.0                     # the crash lane: blocked, so nothing moves through it
    cost[4:6, :] = 25.0                    # the opposite lane: still moving, and this is the killer
    cost[4:6, 16:21] = 2.0                 # except by the junction, where the signal holds it
    if glass:
        cost[2:5, 11:14] = np.maximum(cost[2:5, 11:14], 9.0)     # debris around the crash
    if smoke:
        cost[3:6, 14:19] = 60.0                                  # smoke and spilled fuel
    if wire:
        cost[:, 20:23] = 90.0                                    # a cable down across everything
    return cost


def show_grid(cost, ax, title):
    # Both panels share one colour scale (vmin/vmax). Without that, matplotlib scales
    # each panel to its own maximum and the same live lane comes out a different
    # colour in each picture - which is exactly the wrong lesson for a danger map.
    im = ax.imshow(np.log10(cost), cmap="inferno", origin="lower", vmin=0, vmax=2,
                   extent=[0, ROAD_X, 0, ROAD_Y], aspect="auto")
    ax.set_title(title, fontsize=10)
    ax.set_ylabel("metres across")
    ax.grid(False)
    return im


fig, axes = plt.subplots(2, 1, figsize=(9.5, 5.6), constrained_layout=True)
show_grid(hazard_grid(), axes[0], "A motorcycle down: one lane blocked, the other still moving")
im = show_grid(hazard_grid(smoke=True, wire=True), axes[1],
               "The same junction with smoke and a cable down (bright = do not enter)")
axes[1].set_xlabel("metres along the road")
fig.colorbar(im, ax=axes, label="log10 of the cost", fraction=0.04)
plt.show()

print("Cost of standing on the footpath: ", hazard_grid()[7, 2])
print("Cost of standing in the live lane:", hazard_grid()[5, 2])
print("The screen never draws a route through anything above 50.")
""")
see("hazards", "The hazard map")

# ============================================================ 14. PATH
md(r"""
## 14 · The safe way in

With a cost for every cell, "the safest way in" becomes an ordinary shortest-path problem — the
same algorithm a map app uses, with **danger in place of minutes**.

Dijkstra's algorithm starts at the helper, repeatedly steps to the cheapest cell it has not settled
yet, and remembers where each cell was reached from. When it settles the casualty's cell, walking
the "where from" links backwards gives the route.

Watch where it decides to cross. It does **not** cross at the helper's feet, which is what a person
does. It walks along the footpath to the junction, crosses where the signal is holding the traffic,
and comes back down the far side. That is longer, and it is the advice a traffic officer would
give.

The screen shows that route in green. It does not describe it. Nobody follows a paragraph while
panicking.
""")

co(r"""
import heapq


def plan_path(cost, start, goal):
    "Cheapest way in, by Dijkstra. Cost is danger, not distance."
    ny, nx = cost.shape
    dist = np.full((ny, nx), np.inf)
    prev = {}
    dist[start] = 0
    q = [(0.0, start)]
    while q:
        d, node = heapq.heappop(q)
        if node == goal:
            break
        if d > dist[node]:
            continue
        j, i = node
        for nj, ni in ((j + 1, i), (j - 1, i), (j, i + 1), (j, i - 1)):
            if 0 <= nj < ny and 0 <= ni < nx and d + cost[nj, ni] < dist[nj, ni]:
                dist[nj, ni] = d + cost[nj, ni]
                prev[(nj, ni)] = node
                heapq.heappush(q, (dist[nj, ni], (nj, ni)))
    path, node = [goal], goal
    while node != start:
        node = prev[node]
        path.append(node)
    return path[::-1], float(dist[goal])


cost = hazard_grid()
helper, victim = (7, 2), (3, 10)          # (row across, column along the road)
route, danger = plan_path(cost, helper, victim)

# What a person actually does: step straight off the kerb and walk to the casualty.
naive = [(j, helper[1]) for j in range(helper[0], victim[0] - 1, -1)] + \
        [(victim[0], i) for i in range(helper[1] + 1, victim[1] + 1)]
naive_danger = sum(cost[c] for c in naive)

cellx, celly = ROAD_X / GRID[0], ROAD_Y / GRID[1]
fig, ax = plt.subplots(figsize=(9.5, 3.4))
ax.imshow(np.log10(cost), cmap="inferno", origin="lower",
          extent=[0, ROAD_X, 0, ROAD_Y], aspect="auto")
ax.plot([i * cellx for _, i in naive], [j * celly for j, _ in naive],
        color="#ff5252", lw=2.5, ls="--", label=f"straight to the casualty, danger {naive_danger:.0f}")
ax.plot([i * cellx for _, i in route], [j * celly for j, _ in route],
        color="#00e676", lw=3.5, label=f"the route the screen shows, danger {danger:.0f}")
ax.plot(helper[1] * cellx, helper[0] * celly, "o", color="white", ms=9)
ax.plot(victim[1] * cellx, victim[0] * celly, "X", color="white", ms=12)
ax.annotate("helper", (helper[1] * cellx, helper[0] * celly), color="white",
            xytext=(4, 6), textcoords="offset points", fontsize=9)
ax.annotate("rider", (victim[1] * cellx, victim[0] * celly), color="white",
            xytext=(4, 6), textcoords="offset points", fontsize=9)
ax.legend(fontsize=8, loc="lower right")
ax.set_title("The route the screen shows, and the one people take")
ax.set_xlabel("metres along the road"); ax.set_ylabel("metres across")
ax.grid(False)
plt.tight_layout(); plt.show()

print(f"Straight to the casualty, across the live lane: danger {naive_danger:.0f}")
print(f"Round by the signal, where the traffic is held:  danger {danger:.0f}")
print(f"The safe route is about {len(route) - len(naive)} cells longer - roughly "
      f"{(len(route) - len(naive)) * cellx:.0f} metres of extra walking.")
""")
see("path", "Shortest path by danger")

# ============================================================ 15. MODULES
md(r"""
## 15 · One instruction at a time

Now the screen itself.

The temptation here is enormous and must be resisted: a language model that generates first-aid
advice on the fly. **No.** A generative model that invents medical instructions, under stress, on a
public screen, with nobody checking it, is the worst idea in this entire project.

What we build instead is a **state machine**: a short list of guards, checked in a fixed order,
where every branch returns the name of a **pre-approved video** that a clinician wrote and a
regional authority signed off.

The order of the guards is the safety argument, so read it top to bottom:

1. **Has a dispatcher taken the screen?** They outrank everything, including the AI.
2. **Is the scene unsafe** — smoke, live traffic, a fallen cable? Then nobody approaches, no matter
   how bad the casualty looks.
3. **Is the person trapped, or the vehicle unstable?** Then waiting is safer than moving them.
4. **Has the dispatcher confirmed severe bleeding?** That is the one thing that beats waiting.
5. **Has the dispatcher confirmed no response?** Note *confirmed*, by a person. The camera never
   decides this.
6. **Is a helmet involved?** Show the "leave it on" module, because pulling a helmet off is the
   classic bystander mistake at a motorcycle crash.
7. **Otherwise** — connect a live dispatcher and show nothing clever.
""")

co(r"""
MODULES = {
    "scene_safety": "Make the scene safer first",
    "unresponsive": "Person not responding - approved module",
    "bleeding":     "Severe visible bleeding - pressure module",
    "helmet":       "Motorcycle rider with a helmet - do not remove it",
    "trapped":      "Person trapped or vehicle unstable - wait for the crew",
    "dispatcher":   "Live dispatcher, no automatic module",
}


def choose_module(scene):
    "A short list of guards, in a fixed order. Not a chatbot."
    if scene.get("dispatcher_override"):
        return "dispatcher", "A dispatcher has taken the screen."
    if scene.get("smoke") or scene.get("live_traffic") or scene.get("wire"):
        return "scene_safety", "The scene is not safe to approach yet."
    if scene.get("trapped") or scene.get("vehicle_unstable"):
        return "trapped", "Moving this person could do more harm than waiting."
    if scene.get("severe_bleeding_confirmed"):
        return "bleeding", "Bleeding that a dispatcher has confirmed comes first."
    if scene.get("unresponsive_confirmed_by_dispatch"):
        return "unresponsive", "Confirmed by the dispatcher, not by the camera."
    if scene.get("helmet"):
        return "helmet", "A helmet stays on unless a dispatcher says otherwise."
    return "dispatcher", "Not enough is visible. Connect a person."


scenes = [
    ("traffic still moving past the rider",      dict(live_traffic=True, helmet=True)),
    ("lane closed, helmet on, nothing confirmed", dict(helmet=True)),
    ("dispatcher confirms no response",          dict(helmet=True, unresponsive_confirmed_by_dispatch=True)),
    ("dispatcher confirms heavy bleeding",       dict(helmet=True, severe_bleeding_confirmed=True)),
    ("rider trapped under the vehicle",          dict(trapped=True, unresponsive_confirmed_by_dispatch=True)),
    ("smoke from the engine bay",                dict(smoke=True, unresponsive_confirmed_by_dispatch=True)),
    ("dispatcher takes the screen",              dict(dispatcher_override=True, smoke=True)),
]
for label, scene in scenes:
    module, why = choose_module(scene)
    print(f"{label:44s} -> {MODULES[module]}")
    print(f"{'':44s}    {why}")
""")

md(r"""
**Read the fifth and sixth rows carefully.** In both, the dispatcher has confirmed the rider is not
responding — the most urgent thing this system can be told. In both, the screen refuses to show the
first-aid module, because the rider is trapped in one and there is smoke in the other. Scene safety
outranks the casualty. That is not the AI being cautious; it is the order in which the guards are
written, and it cannot be reached around.

**And the last row.** The dispatcher's override is checked first, so it wins even against smoke —
because a dispatcher on a radio to a fire crew knows things the camera cannot.
""")
see("modules", "A state machine, not a chatbot")

# ============================================================ 16. HELPER
md(r"""
## 16 · Watching the helper

The camera can give feedback, but only on things it can honestly see.

**It can see:** where a helper is standing, which side they approached from, whether they are
dragging the casualty, whether a helmet is being pulled off, whether the crowd is standing over the
patient, and whether the ambulance lane is blocked.

**It cannot see:** how hard somebody is pressing on a wound, or how deep a chest compression is.
Turning pixels into centimetres depends on the lens, the angle, the distance, the clothing and the
size of the person. A system that guesses at compression depth from a camera and shows a confident
green tick is worse than one that shows nothing.

If depth and pressure matter — and for CPR they matter more than anything else — then the hardware
has to change, not the model. An **instrumented mat** in the roadside cabinet measures depth
directly. A **pressure-sensing bandage** measures the force on a wound. Those are cheap, and they
are honest.
""")

co(r"""
CHECKS = [
    ("approach_side",     "red",   "Helper is walking in from the traffic side",
     "STOP - come round from the footpath side"),
    ("moving_victim",     "red",   "Helper is dragging the rider",
     "STOP - do not move them unless there is fire or traffic"),
    ("helmet_off",        "red",   "Helper is pulling the helmet off",
     "STOP - leave the helmet on until the dispatcher says"),
    ("crowd_close",       "amber", "The crowd is standing over the rider",
     "Give them space, and keep the lane clear"),
    ("pressure_released", "amber", "Pressure on the wound keeps coming off",
     "Press again, hard, and do not let go"),
    ("lane_blocked",      "amber", "The ambulance lane is blocked",
     "Move to the footpath, the ambulance needs this lane"),
]


def check_helper(obs):
    "Red, amber and green, for the things a camera can honestly see."
    out = [(colour, message) for key, colour, _, message in CHECKS if obs.get(key)]
    return out or [("green", "Good. Keep going, help is on the way.")]


moments = [
    ("second 4 - the first bystander moves", dict(approach_side=True)),
    ("second 9 - they come round the front", dict()),
    ("second 20 - two people take an arm each", dict(moving_victim=True, crowd_close=True)),
    ("second 34 - hands off, kneeling beside", dict(lane_blocked=True)),
    ("second 51 - the lane is clear",         dict()),
]
for label, obs in moments:
    for colour, message in check_helper(obs):
        print(f"{label:42s} {colour.upper():5s}  {message}")
""")
see("helper", "Red, amber, green")

# ============================================================ 17. ROLES
md(r"""
## 17 · Giving the crowd jobs

Twelve people are standing around a rider. That is not help; that is a crowd. It blocks the
ambulance, it stops the traffic warning from being seen, and every single person in it believes
somebody else has already called.

The fix is not technology. It is **naming people and giving them one job each**. "Somebody call an
ambulance" achieves nothing. "You, in the red jacket, press this button" works, and every first-aid
course in the world teaches it.

A screen can do exactly that, and it can do it better than a panicking person, because it knows
where everybody is standing. Four jobs, in order of urgency, each given to the nearest person who
does not already have one.
""")

co(r"""
def assign_roles(people):
    "Give the crowd jobs. Nearest free person to each job, most urgent job first."
    jobs = [("Press the help button and talk to the dispatcher", (6.0, 17.0)),
            ("Warn the traffic, upstream of the crash",          (4.0, 10.0)),
            ("Bring the emergency box from the cabinet",         (9.0, 17.5)),
            ("Wave the ambulance in at the junction",            (56.0, 16.0))]
    free, out = list(people), []
    for label, (gx, gy) in jobs:
        if not free:
            out.append(dict(job=label, who="nobody left", walk=np.nan))
            continue
        d = [np.hypot(p["x"] - gx, p["y"] - gy) for p in free]
        k = int(np.argmin(d))
        out.append(dict(job=label, who=free[k]["name"], walk=round(float(d[k]), 1)))
        free.pop(k)
    return pd.DataFrame(out)


crowd = [dict(name="Red jacket",    x=8.0,  y=17.0),
         dict(name="Scooter rider", x=22.0, y=16.0),
         dict(name="Shopkeeper",    x=5.0,  y=18.0),
         dict(name="Bus passenger", x=40.0, y=15.0),
         dict(name="Cyclist",       x=52.0, y=17.0)]
print(assign_roles(crowd).to_string(index=False))
""")
see("roles", "Assignment")

# ============================================================ 18. DID IT HELP
md(r"""
## 18 · Did it help?

Now the hardest section to write honestly.

We cannot claim this saves lives. Nobody can claim that from a simulation, and a project that does
so should not be trusted. What we *can* do is measure the things the beacon actually changes, and
be explicit about which numbers are measured and which are assumed:

| Number | Where it comes from |
|---|---|
| Seconds to notice, **with** the beacon | **measured** — it is the detector's own latency, from section 9 |
| Everything else | **assumed** — our estimates of how people behave |

The assumptions below are written as code so that a student can disagree with them and change them:
without a beacon, somebody notices in 5–40 seconds, the first call comes 20–120 seconds after that
(and in 15 % of runs, nobody calls for two and a half minutes), and a harmful action — moving the
rider, pulling the helmet off — happens in about 40 % of cases. With the beacon those last drop to
12 % and 10 %, because the screen says "do not move them" in the first ten seconds.

**That last assumption is the one to argue about.** It is the whole business case, and it is a
guess until somebody runs a proper trial with mannequins.
""")

co(r"""
def outcome_sim(detect_secs, n=400, with_beacon=True, seed=7):
    "One crash, played many times. Only `detect_secs` is measured; the rest are assumptions."
    r = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        if with_beacon:
            notice = max(0.0, r.normal(detect_secs, 1.2))
            call   = notice + r.uniform(1.0, 3.0)
            help_  = call + r.uniform(8.0, 30.0)
            unsafe = int(r.random() < 0.12) + int(r.random() < 0.10)
            lane   = call + r.uniform(20.0, 70.0)
        else:
            notice = r.uniform(5.0, 40.0)
            call   = notice + (r.uniform(20.0, 120.0) if r.random() > 0.15
                               else r.uniform(150.0, 300.0))
            help_  = notice + r.uniform(10.0, 60.0)
            unsafe = int(r.random() < 0.40) + int(r.random() < 0.35)
            lane   = call + r.uniform(60.0, 240.0)
        rows.append(dict(notice=notice, call=call, help=help_, unsafe=unsafe, lane=lane))
    return pd.DataFrame(rows)


measured = float(waits.loc[WAIT, "Seconds to alarm"])
without = outcome_sim(measured, with_beacon=False)
with_it = outcome_sim(measured, with_beacon=True)

table = pd.DataFrame([
    {"what we measure": "Seconds to notice",            "no beacon": int(without.notice.median()),
     "with beacon": round(with_it.notice.median(), 1)},
    {"what we measure": "Seconds to the emergency call", "no beacon": int(without.call.median()),
     "with beacon": round(with_it.call.median(), 1)},
    {"what we measure": "Seconds to first safe help",    "no beacon": int(without.help.median()),
     "with beacon": round(with_it.help.median(), 1)},
    {"what we measure": "Seconds until the lane is clear", "no beacon": int(without.lane.median()),
     "with beacon": round(with_it.lane.median(), 1)},
    {"what we measure": "Harmful actions per crash",     "no beacon": round(without.unsafe.mean(), 2),
     "with beacon": round(with_it.unsafe.mean(), 2)},
])
print(f"detector latency used: {measured} s (measured in section 9)")
print()
print(table.to_string(index=False))

fig, ax = plt.subplots()
rows = table[table["what we measure"].str.startswith("Seconds")]
y = np.arange(len(rows))
ax.barh(y - 0.2, rows["no beacon"], 0.4, color=GREY, label="no beacon")
ax.barh(y + 0.2, rows["with beacon"], 0.4, color=GREEN, label="with beacon")
ax.set_yticks(y); ax.set_yticklabels([s.replace("Seconds ", "") for s in rows["what we measure"]])
ax.set_xlabel("seconds (median of 400 runs)")
ax.set_title("The same crash, with and without the beacon")
ax.legend()
plt.tight_layout(); plt.show()
""")

md(r"""
**What this chart is allowed to claim.** The emergency call goes out sooner, and the lane is cleared
sooner, because those follow directly from detection and from four named jobs. Those are the two
honest wins.

**What it is not allowed to claim.** Anything about survival. The link from "the call went out 90
seconds earlier" to "the person lived" is real, but it is not ours to measure, and a system that
advertises saved lives from a simulation deserves the scepticism it gets.
""")
see("outcome", "The benchmark")

# ============================================================ 19. WHAT IT GETS WRONG
md(r"""
## 19 · What it still gets wrong

Every section so far has been about what the system does. This one is about where it fails, because
that list is what a public authority will actually ask for.

**A blocked view is a blocked view.** When a bus pulls in and the crash happens behind it, the
camera sees stopped traffic and nothing else. The model still gets there — from traffic behaviour
alone — but it takes **8.2 seconds instead of 2.8**, and those are the most expensive seconds in
the whole event. One junction, one camera, one blind spot; the answer is a second camera on the
opposite pole, not a better model.

**The near miss is genuinely ambiguous.** Everything the system knows in the first second of a hard
brake is also true of a crash. Waiting three seconds fixes most of it, and waiting is not free.

**The mechanic under the van is only solved by luck.** He does not move, and neither does a
seriously injured person. Our model separates them because he was already there when the clip
started. A mechanic who slides under the van *while the camera is watching* would look far more
like a casualty.

**The detector cannot rank severity.** It reports that something happened, not how bad it is. That
is on purpose — but it means the control centre gets the same alarm for a bruised elbow and a
crushed chest.
""")

co(r"""
occl = [c for c in meta[meta.kind == "occluded"].clip_id if c in set(TEST)]
brake = [c for c in meta[meta.kind == "hard_brake"].clip_id if c in set(TEST)]
print("Crash behind a bus:      ", score(model3, occl))
print("Near miss, wrongly called:", score(model3, brake)["Quiet clips called in"])
print()
print("Compare with a clear view:", score(model3,
      [c for c in meta[meta.kind == 'collision_down'].clip_id if c in set(TEST)]))
""")
see("limits", "The boundaries")

# ============================================================ 20. RULES
md(r"""
## 20 · The rules that do not move

If one page of this notebook survives, it should be this one. These are not preferences. They are
the conditions under which a system like this is allowed near a public road.

1. **Call first.** The control centre is told the moment an alarm is confirmed. The AI never waits
   to be certain, and nothing is allowed to run before the call.
2. **Never name an injury.** "Not visibly responding" is as far as the system goes. Not
   "cardiac arrest", not "spinal injury", not "internal bleeding".
3. **The dispatcher outranks the AI.** They can take the screen, the camera and the speaker at any
   moment. That branch is checked before every other branch in the code.
4. **Nothing generative writes a medical instruction.** The AI selects between videos that
   clinicians wrote and a regional authority approved. It does not compose them, summarise them, or
   improvise around them.
5. **Never send anybody into danger.** Scene safety is checked before the casualty's condition,
   even when the casualty looks worse.
6. **Say what you cannot see.** Uncertainty goes in the packet and on the screen.
7. **Work with the network down.** Detection, the screen and the local siren run on the pole. The
   call is what needs the network, and it should have two ways out.
8. **Keep the least footage that works.** Fifteen seconds, faces and plates blurred, and a
   documented retention limit.
9. **Test with mannequins first**, then with staged scenes, then with a clinician watching, and
   only then in public.
10. **Never delay CPR, an AED, or a dispatcher's instructions** while the camera analyses anything.

---

## Summary

We started with a camera that records crashes for the file, and ended with one that:

- knows a crash from a red light, a near miss, a mechanic and a fallen board;
- catches all of the incidents in the exam pile, including the rollover with nobody visible and the
  rider who stands up and walks away;
- calls the control centre in about three seconds, and says what it is unsure about;
- draws a safe route in, gives four people one job each, and shows one approved instruction at a
  time;
- and refuses, by construction, to tell anybody what is wrong with the person on the ground.

### What to try next

- Move `WAIT` to 1 second and read the false-alarm column. Would you sign that off?
- Add a fifteenth scenario — a cyclist who falls and gets straight back up — and see which model
  copes.
- Give the forest the plain `flow` feature back, and watch it start reporting quiet evenings.
- Put a second camera on the opposite pole, and think about what the occlusion case becomes.
""")

nb = new_notebook(cells=cells, metadata={"language_info": {"name": "python"}})
out = Path(__file__).resolve().parent / "Roadside_First_Response_Beacon.ipynb"
nbf.write(nb, str(out))
print(f"Wrote {out.name}  ({len(cells)} cells)")
