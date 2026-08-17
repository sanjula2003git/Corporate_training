"""
Builds CoolBench_Heat_Emergency_Station.ipynb from nbformat cells.
Run:  py -3.13 -X utf8 build_nb.py

House style: SIMPLE ENGLISH. Short sentences, everyday words, and an explanation
next to anything a beginner would not already know - the same style as the
Roadside Beacon and Hospital Alarm-Fatigue notebooks.

The notebook is standalone (Colab): it builds the whole bench inline, so there
is nothing to download and nothing to import from this folder.

NOTE for future editors:
  * inside co(...) cells use only single-line "..." docstrings or # comments. A
    triple-quoted docstring would close the outer r-string and break this script.
  * the prose quotes numbers the cells print. After any change, re-run the cells
    and re-check every number written in markdown.
  * only ONE link goes out to the illustration app, at the top. Colab opens every
    external link in a fresh tab, so twenty links means twenty tabs.
"""
import sys
from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bridge  # noqa: E402

cells = []


def md(t):
    cells.append(new_markdown_cell(t.strip("\n")))


def co(t):
    cells.append(new_code_cell(t.strip("\n")))


COLAB = ("https://colab.research.google.com/github/sanjula2003git/Corporate_training/blob/main/"
         "CoolBench-AI/CoolBench_Heat_Emergency_Station.ipynb")
APP = "https://coolbench.streamlit.app"


def see(stage, label):
    """Point at the matching page of the illustration app - without a link."""
    n = bridge.ORDER.index(stage) + 1
    md(f"🎬 **See it illustrated:** step {n} in the illustration tab — *{label}*.")


# ============================================================ TITLE
md(rf"""
# 🌡️ CoolBench

### Building an AI Heat-Emergency Cooling Station

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({COLAB})

**The problem, in two sentences.**

A bench in a park has a fan, a water mister, a shade cover, cold packs, a battery and a water
tank. This project works out how to use those limited supplies to cool an overheated person
until help arrives, without running out.

---

### The situation the bench is built for

Somebody presses the help button next to a sports ground on a hot afternoon. The bench is told:

| Reading | Value |
|---|---|
| Air temperature | 41 °C |
| Humidity | 32 % |
| Bench surface | 48 °C |
| Responders arrive in | 14 minutes |
| Water in the tank | 8 litres |
| Battery | 61 % |
| Cold packs | 3 |

It has to keep the person as cool as it can for those fourteen minutes, and still have enough
battery left to talk to the dispatcher afterwards.

### What we will build

1. A **heat model** of a person lying in the sun, so we can see where the heat comes from.
2. Four **single tools** tried one at a time: shade, fan, mist, cold packs.
3. A **rule controller** that watches the tank and the battery.
4. A **forecaster** that says where the temperature will be five minutes from now.
5. A **resource-aware controller** that searches every setting and picks the cheapest.
6. A **safety layer** underneath all of it that the AI cannot argue with.

### What it is not

The bench does not decide that anybody is ill. A person or a dispatcher switches it on. It never
names a condition, never says that professional help is unnecessary, and never writes a medical
instruction. A dispatcher can take it away from the AI at any moment.

> ⚠️ **Everything here is simulated.** The weather, the bench and the person are invented so the
> engineering can be studied safely. The body temperature in this notebook is an **educational
> estimate**, not a clinical measurement, and no part of this may be used to decide the care of a
> real person.

### The question the notebook is trying to answer

> Can a controller that forecasts and adapts keep a person just as cool as running everything at
> full power, while using **less water and less battery**?
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

1. A bench with supplies
2. A hot afternoon
3. Where the heat comes from
4. What the bench can measure
5. Doing nothing — the baseline
6. Shade only
7. Fan only — and when a fan is a heater
8. Mist only — cooling per litre
9. Three cold packs
10. Everything at full power
11. Rules that watch the tank
12. Guessing five minutes ahead
13. Writing down what "good" means
14. The resource-aware controller
15. The scoreboard
16. Dry heat and humid heat
17. When something breaks
18. What it still gets wrong
19. The rules that do not move
20. The CoolBench dashboard
""")

# ============================================================ SETUP
md(r"""
## Setup

Colab already has everything we need. If you run this somewhere else, remove the `#` on the
install line. There is no deep-learning library in this notebook — the "small neural network" in
section 12 is scikit-learn's, and it trains in about a second.
""")

co(r"""
# !pip install numpy pandas scikit-learn matplotlib

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error

# One seed, so you get the same afternoon every time you run the notebook.
np.random.seed(7)

plt.rcParams["figure.figsize"] = (9.5, 3.6)
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.25

BLUE, ORANGE, GREEN, RED, GREY, PURPLE = "#1976d2", "#ef6c00", "#2e7d32", "#c62828", "#90a4ae", "#6a1b9a"

print("Ready.")
""")

# ============================================================ 1. THE BENCH
md(r"""
## 1 · A bench with supplies

Picture a heavy public bench at the edge of a sports ground. Bolted to it:

| Part | What it does | What it costs to use |
|---|---|---|
| **Canopy** | slides out and blocks the sun | one push of a small motor |
| **Fan** | blows air across the person | up to 48 watts |
| **Mister** | sprays a fine water mist on the skin | up to 400 mL a minute, and a 28 W pump |
| **Cold packs** | take heat away by touch | one pack, gone for good |
| **Sensors** | air, surface, humidity, thermal camera, seat load, tank float | almost nothing |
| **Radio, screen, speaker** | talk to the dispatcher, show the approved page | 17 watts, never switched off |

The battery holds **60 watt-hours**. That is small. A kettle would empty it in three minutes.

Here is the whole problem in one line of arithmetic. The radio, the screen and the speaker draw
17 W and must keep working. Running the fan and the pump flat out adds another 76 W. At 93 W a
61 % battery lasts **24 minutes** — and the wait is fourteen, with a handover afterwards.

So "cool as fast as possible" is not obviously the right answer. It is one option among several,
and it is the one that leaves the bench mute.
""")

co(r"""
TANK_L        = 8.0        # litres, a full tank
BATTERY_WH    = 60.0       # watt-hours of usable battery
P_ESSENTIAL   = 17.0       # radio 11 W + screen and speaker 6 W, never switched off
PRIME_ML      = 40.0       # water lost every time the pump starts from cold
N_PACKS       = 3

# The settings the controller may choose from.
MIST_LEVELS = {"off": 0.0, "low": 80.0, "medium": 240.0, "high": 400.0}   # mL per minute
FAN_LEVELS  = [0.0, 0.25, 0.50, 0.75, 1.0]


def p_fan(level):
    "Watts the fan draws. Air power grows fast with speed, so the top setting is expensive."
    return 0.0 if level <= 0 else 3.0 + 45.0 * level ** 2.5


def p_pump(mist_ml_min):
    "Watts the mist pump draws."
    return 0.0 if mist_ml_min <= 0 else 8.0 + 0.05 * mist_ml_min


print(f"{'setting':>22}  {'watts':>6}  {'61% battery lasts':>18}")
for f in FAN_LEVELS:
    for name, m in MIST_LEVELS.items():
        if (f, name) in [(0.0, "off"), (0.75, "medium"), (1.0, "high")]:
            w = p_fan(f) + p_pump(m) + P_ESSENTIAL
            print(f"fan {int(f*100):>3}% mist {name:>6}  {w:>6.0f}  "
                  f"{BATTERY_WH*0.61/w*60:>15.0f} min")
""")

md(r"""
Read the last line. **Everything at full power runs the battery down in about 24 minutes**, and
the bench still has to be able to call for help after that.
""")
see("bench", "A bench with supplies")

# ============================================================ 2. THE AFTERNOON
md(r"""
## 2 · A hot afternoon

Before we can cool anybody we need weather. We build one hot day: air temperature, sunshine,
humidity, wind, and the temperature of the bench surface itself.

Two things in the chart below usually surprise people.

**The ground is much hotter than the air.** Dark surfaces in full sun sit 7–9 °C above air
temperature. A person lying on that surface is being warmed by it.

**Humidity moves opposite to temperature.** Warm air holds more water, so as the air heats up
through the day the *relative* humidity falls, even though the amount of water in the air barely
changes.
""")

co(r"""
def day_profile():
    "One hot day, every fifteen minutes."
    h = np.arange(0, 24.01, 0.25)
    swing   = np.cos((h - 15.0) / 24.0 * 2 * np.pi)      # warmest at 3 p.m., coolest at 3 a.m.
    ambient = 34.0 + 7.0 * swing
    solar   = np.clip(980.0 * np.sin(np.pi * (h - 6.0) / 13.0), 0, None)
    rh      = np.clip(0.80 - 0.52 * (ambient - ambient.min()) /
                      (ambient.max() - ambient.min()), 0.15, 0.95)
    wind    = 0.5 + 1.4 * np.clip(np.sin(np.pi * (h - 8.0) / 14.0), 0, None)
    surface = ambient + 9.0 * solar / 980.0
    return pd.DataFrame(dict(hour=h, ambient=ambient, solar=solar, rh=rh,
                             wind=wind, surface=surface))


day = day_profile()

fig, ax = plt.subplots()
ax.plot(day.hour, day.surface, color=RED,    lw=2.5, label="bench surface °C")
ax.plot(day.hour, day.ambient, color=ORANGE, lw=2.5, label="air °C")
ax.plot(day.hour, day.rh * 100, color=BLUE,  lw=2,   label="humidity %")
ax.plot(day.hour, day.solar / 20, color=PURPLE, lw=2, ls=":", label="sunshine ÷ 20")
ax.axvspan(13, 17, color=RED, alpha=0.08)
ax.text(13.3, 12, "the dangerous hours", color=RED, fontsize=9)
ax.set_xlabel("hour of the day"); ax.set_ylabel("°C, %, scaled sun")
ax.set_title("One hot day at the sports ground"); ax.legend(fontsize=8, ncol=2)
plt.tight_layout(); plt.show()

hot = day.iloc[(day.hour - 15.0).abs().idxmin()]
print(f"At 15:00 — air {hot.ambient:.1f} °C, surface {hot.surface:.1f} °C, "
      f"humidity {hot.rh*100:.0f} %, sun {hot.solar:.0f} W/m²")
""")

md(r"""
### Why the air temperature on its own is not enough

Cooling a person mostly means **evaporating water off their skin**. How much water the air can
take depends on how much it is already carrying. That is what humidity measures.

So two afternoons can both read 41 °C and be completely different problems. We will come back to
this with real numbers in section 8, once the physics is in place — but the short version is
that at 41 °C and 20 % humidity the air can carry away about **1150 watts**, and at the same
41 °C and 90 % humidity it can carry away **nothing at all**.

That is why every model in this notebook is given humidity, sunshine and wind, and not just a
thermometer reading.
""")
see("afternoon", "Why the thermometer lies")

# ============================================================ 3. HEAT BALANCE
md(r"""
## 3 · Where the heat comes from

We now write down a **heat balance**: everything warming the person, minus everything cooling
them. If the total is positive they are getting hotter.

$$
m\,c_p\,\frac{dT}{dt}
= Q_{\text{body}} + Q_{\text{sun}} + Q_{\text{ground}} + Q_{\text{air}}
- Q_{\text{evaporation}} - Q_{\text{packs}}
$$

- $m\,c_p$ — how many joules it takes to warm the whole body by one degree. For 75 kg of mostly
  water, about **262 500 J per °C**. That is why bodies change temperature slowly.
- $Q_{\text{body}}$ — heat the person makes themselves. Even lying still this is 110 W, and it is
  higher just after exercise.
- $Q_{\text{sun}}$ — sunshine absorbed. The biggest single term outdoors.
- $Q_{\text{ground}}$ — infrared heat radiating up from hot paving.
- $Q_{\text{air}}$ — heat carried by the air. **This can go either way.** If the air is cooler
  than the skin it takes heat away. If the air is hotter than the skin it brings heat in.
- $Q_{\text{evaporation}}$ — water leaving the skin. Always cooling, and by far the strongest
  tool the bench has.
- $Q_{\text{packs}}$ — cold packs pressed against the skin.

> ⚠️ **This is an educational approximation, not a physiological model.** A real body has a core,
> a shell, blood flow that changes with temperature, and a person attached to it. This model has
> one lump of warm water and a fixed mass. Every temperature it produces is a number about the
> simulation.

### Two ideas that do most of the work

**Skin is cooler than the core**, by about a degree when dry. When you wet it, evaporation pulls
the skin down further — about another degree and a half on the afternoon in this notebook, and
more in drier air. That matters more than it sounds, and section 4 is entirely about why.

**Wetness saturates.** Skin can only be *so* wet. We track a number `w` from 0 (bone dry) to 1
(as wet as skin gets). A collapsed person in heat illness has often stopped sweating, so we start
`w` at 0.10. The mister raises it. Once `w` reaches 1.00, **more water changes nothing at all** —
it runs on to the ground.
""")

co(r"""
BODY_MASS, CP_BODY = 75.0, 3500.0
C_BODY = BODY_MASS * CP_BODY          # joules to warm the whole body by 1 degree
A_CONV, A_SUN, A_RAD = 1.5, 0.70, 0.80    # m² of skin: to the air, to the sun, to the ground
ALPHA, EPS, SIGMA = 0.70, 0.95, 5.67e-8   # sunlight absorbed, emissivity, Stefan-Boltzmann
LATENT = 2.43e6                       # joules to evaporate one kg of water
F_CLO_C, F_CLO_E = 0.80, 0.60         # clothes slow the air, and slow the vapour harder
W_NAT = 0.10                          # a collapsed person has often stopped sweating
SKIN_GAP = 1.0                        # dry skin sits about a degree below the core
DELIVERY = 0.09                       # share of misted water that lands and stays on skin

print(f"It takes {C_BODY:,.0f} joules to warm this body by one degree.")
print(f"A 1000 W heater would take {C_BODY/1000/60:.1f} minutes to do it.")
""")

co(r"""
def p_sat(t_c):
    "How much water vapour saturated air holds, in kPa. Tetens' formula."
    return 0.6108 * np.exp(17.27 * t_c / (t_c + 237.3))


def skin_drop(e_evap):
    "How much cooler wet skin runs than dry skin, on the same body."
    return min(3.0, e_evap / 700.0)


def skin_state(T, air, fan, mist_ml):
    "Skin temperature, how wet it is, and how fast water leaves it."
    # Wetting the skin cools it; cooler skin holds less vapour, which slows the
    # evaporation down again. Those two chase each other, so we let them settle
    # over a few passes instead of solving it properly.
    v   = max(air["wind"], 4.0 * fan)              # air speed at the skin, m/s
    h_c = 8.3 * v ** 0.6 * F_CLO_C                 # W per m² per °C
    h_e = 16.5 * (h_c / F_CLO_C) * F_CLO_E         # W per m² per kPa (the Lewis relation)
    p_a = air["rh"] * p_sat(air["ambient"])        # vapour already in the air
    water_W = mist_ml * DELIVERY / 60.0 * 1e-3 * LATENT   # what the mist could evaporate
    T_sk = T - SKIN_GAP
    for _ in range(6):
        e_max = h_e * A_CONV * max(0.0, p_sat(T_sk) - p_a)   # all this air could ever take
        w     = min(1.0, W_NAT + (water_W / e_max if e_max > 1.0 else 5.0))
        e_evap = w * e_max
        T_sk  = T - SKIN_GAP - skin_drop(e_evap)
    return T_sk, w, e_evap, e_max, h_c


def net_watts(T, air, act, packs, t_min):
    "The whole heat balance, in watts. Positive means the body is warming."
    T_sk, w, e_evap, e_max, h_c = skin_state(T, air, act["fan"], act["mist"])
    q_met   = (110 + 150 * np.exp(-t_min / 8.0)) * 1.07 ** (T - 37.0)
    q_solar = ALPHA * A_SUN * air["solar"] * (1 - (0.88 if act["canopy"] else 0.0))
    t_surf  = air["ambient"] + (2.0 if act["canopy"] else 7.0)
    q_rad   = EPS * SIGMA * A_RAD * ((t_surf + 273.15) ** 4 - (T_sk + 273.15) ** 4)
    q_conv  = h_c * A_CONV * (T_sk - air["ambient"])     # negative means the air heats the body
    q_pack  = sum(2.2 * max(0.0, (T - SKIN_GAP) - p["temp"]) for p in packs if p["on"])
    net = q_met + q_solar + q_rad - q_conv - e_evap - q_pack
    return net, dict(T_sk=T_sk, w=w, e_max=e_max, q_met=q_met, q_solar=q_solar,
                     q_rad=q_rad, q_conv=q_conv, q_evap=e_evap, q_pack=q_pack)


AIR = dict(ambient=41.0, rh=0.32, solar=880.0, wind=0.6)
NOTHING = dict(canopy=0, fan=0.0, mist=0.0)

net, p = net_watts(39.8, AIR, NOTHING, [], 0.0)
print(f"A person at 39.8 °C, lying in full sun, with the bench doing nothing:")
print(f"  their own body heat      {p['q_met']:+7.0f} W")
print(f"  sunshine                 {p['q_solar']:+7.0f} W")
print(f"  hot ground               {p['q_rad']:+7.0f} W")
print(f"  the air                  {-p['q_conv']:+7.0f} W   (positive = the air is heating them)")
print(f"  evaporation              {-p['q_evap']:+7.0f} W")
print(f"  ------------------------------------")
print(f"  net                      {net:+7.0f} W  =  {net/C_BODY*60:+.3f} °C every minute")
""")

md(r"""
Look at the size of the sunshine term. It is bigger than everything else put together. That one
number is why the very first thing the bench does is slide the canopy out — it costs one push of
a motor and removes the largest heat source in the sum.
""")

co(r"""
def show_balance(T, air, act, title):
    "Draw the heat balance as bars: above zero warms, below zero cools."
    net, p = net_watts(T, air, act, [], 0.0)
    names = ["body's own\nheat", "sunshine", "hot ground", "the air", "evaporation"]
    vals  = [p["q_met"], p["q_solar"], p["q_rad"], -p["q_conv"], -p["q_evap"]]
    fig, ax = plt.subplots(figsize=(9.5, 3.2))
    ax.bar(names, vals, color=[RED if v > 0 else BLUE for v in vals])
    span = max(abs(v) for v in vals) or 1.0
    for i, v in enumerate(vals):
        ax.text(i, v + 0.05 * span * (1 if v > 0 else -1), f"{v:+.0f}", ha="center",
                va="bottom" if v > 0 else "top", fontsize=9)
    ax.axhline(0, color="black", lw=1)
    ax.set_ylim(min(0, min(vals)) - 0.28 * span, max(0, max(vals)) + 0.22 * span)
    ax.set_ylabel("watts")
    ax.set_title(f"{title} — net {net:+.0f} W, {net/C_BODY*60:+.3f} °C/min")
    plt.tight_layout(); plt.show()


show_balance(39.8, AIR, NOTHING, "Full sun, bench doing nothing")
show_balance(39.8, AIR, dict(canopy=1, fan=0.0, mist=0.0), "Canopy out, nothing else")
show_balance(39.8, AIR, dict(canopy=1, fan=0.75, mist=240.0), "Canopy, fan 75 %, medium mist")
""")
see("heat", "One sum, six terms")

# ============================================================ 4. SENSORS
md(r"""
## 4 · What the bench can measure

| Sensor | What it honestly gives you |
|---|---|
| Air thermometer | air temperature, ±0.4 °C |
| Surface thermometer | how hot the bench and paving are |
| Humidity sensor | relative humidity, ±2 % |
| **Thermal camera** | the temperature of the **skin surface** |
| Load cell in the seat | is anybody still there |
| Tank float | litres left |
| Battery monitor | watt-hours left |

Notice what is **not** in that list: the temperature inside the person. Nothing on a park bench
can measure that. A thermal camera reads the outside of the skin, and the outside of the skin is
not the inside of a person.

### The trap that this creates

The moment the mister comes on, the skin gets wet, evaporation starts, and the skin temperature
**drops by about a degree and a half within a minute**. The person inside has barely changed.

A bench that reads its camera and adds a degree — because dry skin sits about a degree below the
core — would now believe the person had cooled down enormously, and would stop cooling.

The fix is not a better camera. It is that **the bench knows what it switched on**. It can work
out how much of the skin's coolness is its own mist, and add that back.
""")

md(r"""
Before we can show that, we need the simulator itself: something that plays one emergency out,
minute by minute. It is a loop.

Every minute it reads the sensors, asks a controller what to do, passes the answer through a
**safety layer** (section 19 explains every rule in it), and then runs the physics forward in
ten-second steps.
""")

co(r"""
PACK_LATENT, PACK_C, PACK_U, PACK_START = 45000.0, 1050.0, 2.2, 0.5
READ_NOISE  = 0.05        # the camera averages a minute of frames, so the reading is steady
STOP_COOL, RESUME_COOL = 38.5, 38.9   # stop cooling here, start again here
WARN_TEMP   = 40.0        # the simulated warning line
WATER_FLOOR = 0.30        # never run the pump below this
DT = 10.0                 # seconds per physics step


def make_scenario(**kw):
    "One emergency, with everything that can differ between them."
    s = dict(ambient=41.0, rh=0.32, solar=880.0, wind=0.6, start_temp=39.8, eta=14.0,
             water_l=8.0, battery_pct=61.0, packs=3, pump_fail_at=None, fan_fail_at=None,
             humidity_jump_at=None, humidity_jump_to=0.80, eta_extends_at=None,
             eta_new=25.0, leaves_at=None, minutes=None)
    s.update(kw)
    if s["minutes"] is None:
        s["minutes"] = int(round(max(s["eta"],
                                     s["eta_new"] if s["eta_extends_at"] is not None else 0.0)))
    return s


def air_at(sc, t_min):
    rh = sc["rh"]
    if sc["humidity_jump_at"] is not None and t_min >= sc["humidity_jump_at"]:
        rh = sc["humidity_jump_to"]
    return dict(ambient=sc["ambient"], rh=rh, solar=sc["solar"], wind=sc["wind"])
""")

co(r"""
def apply_limits(act, obs, air):
    "The deterministic limits under the AI. Returns what is allowed, and what it stopped."
    # Every rule here is explained in section 19. They are checked in a fixed
    # order, and the AI has no way to switch any of them off.
    a = dict(act)
    a["stop_packs"] = False
    stopped = []
    if not obs["occupied"]:
        if a["mist"] or a["fan"] or a["release_pack"] or obs["packs_active"]:
            stopped.append("nobody is on the bench")
        a["fan"], a["mist"], a["release_pack"], a["stop_packs"] = 0.0, 0.0, False, True
        return a, stopped
    if obs["cooling_locked"]:
        if a["mist"] > 0 or a["release_pack"] or obs["packs_active"]:
            stopped.append("cool enough - active cooling stopped")
        a["mist"], a["release_pack"], a["stop_packs"] = 0.0, False, True
        a["fan"] = min(a["fan"], 0.25)
    if not obs["pump_ok"] and a["mist"] > 0:
        stopped.append("the pump has failed")
        a["mist"] = 0.0
    if obs["water_l"] <= WATER_FLOOR and a["mist"] > 0:
        stopped.append("tank empty - the pump is protected")
        a["mist"] = 0.0
    if not obs["fan_ok"] and a["fan"] > 0:
        stopped.append("the fan has failed")
        a["fan"] = 0.0
    if obs["battery_wh"] <= obs["reserve_wh"] and (a["fan"] > 0 or a["mist"] > 0):
        stopped.append("battery is down to the radio reserve")
        a["fan"], a["mist"] = 0.0, 0.0
    if a["fan"] > 0:
        # Moving air only cools skin that is wet. On dry skin, in air hotter than
        # the skin, a fan is a heater. Section 7 is about this one.
        blow, _  = net_watts(obs["body_est"], air,
                             dict(canopy=a["canopy"], fan=a["fan"], mist=a["mist"]), [], obs["t"])
        still, _ = net_watts(obs["body_est"], air,
                             dict(canopy=a["canopy"], fan=0.0, mist=a["mist"]), [], obs["t"])
        if blow > still + 1.0:
            stopped.append("the fan would add more heat than it removes")
            a["fan"] = 0.0
    return a, stopped
""")

co(r"""
def run(controller, sc, seed=0, safety=True, model=None):
    "Play one emergency out, minute by minute."
    rng   = np.random.default_rng(seed)
    T     = sc["start_temp"]
    water = sc["water_l"]
    batt  = BATTERY_WH * sc["battery_pct"] / 100.0
    packs = [dict(on=False, absorbed=0.0, temp=PACK_START, used=False) for _ in range(sc["packs"])]
    act   = dict(canopy=0, fan=0.0, mist=0.0, release_pack=False)
    canopy, pump_on, prev_read, locked, blocked, reasons = 0, False, None, False, 0, []
    eta, rows = sc["eta"], []

    for minute in range(sc["minutes"] + 1):
        air = air_at(sc, minute)
        if sc["eta_extends_at"] is not None and minute >= sc["eta_extends_at"]:
            eta = sc["eta_new"]
        eta_left = max(0.0, eta - minute)
        occupied = not (sc["leaves_at"]    is not None and minute >= sc["leaves_at"])
        pump_ok  = not (sc["pump_fail_at"] is not None and minute >= sc["pump_fail_at"])
        fan_ok   = not (sc["fan_fail_at"]  is not None and minute >= sc["fan_fail_at"])

        # What the thermal camera sees is the skin as it is right now - wet and
        # cool if we have been misting it. It is not the core temperature.
        _, _, e_evap_now, _, _ = skin_state(T, air, act["fan"], act["mist"])
        read      = T - SKIN_GAP - skin_drop(e_evap_now) + rng.normal(0, READ_NOISE)
        body_est  = read + SKIN_GAP + skin_drop(e_evap_now)   # add our own cooling back on
        naive_est = read + SKIN_GAP                           # a bench that forgot to
        slope     = 0.0 if prev_read is None else read - prev_read
        prev_read = read

        # Hysteresis: stop cooling at 38.5, and do not start again until 38.9.
        # Without the gap the bench switches on and off every other minute, and
        # each restart costs 40 mL of water priming the pump.
        if body_est <= STOP_COOL:
            locked = True
        elif body_est > RESUME_COOL:
            locked = False

        obs = dict(thermal=read, slope=slope, body_est=body_est, naive_est=naive_est,
                   ambient=air["ambient"] + rng.normal(0, 0.4),
                   rh=float(np.clip(air["rh"] + rng.normal(0, 0.02), 0.02, 1.0)),
                   solar=air["solar"], wind=air["wind"], water_l=water, battery_wh=batt,
                   battery_pct=100 * batt / BATTERY_WH,
                   packs_left=sum(1 for p in packs if not p["used"]),
                   packs_active=sum(1 for p in packs if p["on"]),
                   eta_left=eta_left, t=minute, pump_ok=pump_ok, fan_ok=fan_ok,
                   occupied=occupied, cooling_locked=locked,
                   reserve_wh=P_ESSENTIAL * (eta_left + 20.0) / 60.0)

        asked = controller(obs, model)
        asked.setdefault("release_pack", False)
        if safety:
            act, stopped = apply_limits(asked, obs, air)
        else:
            act, stopped = dict(asked), []
            act["stop_packs"] = False
        blocked += len(stopped)
        reasons.extend(stopped)

        if act["stop_packs"]:
            for p in packs:
                p["on"] = False
        if act["release_pack"]:
            for p in packs:
                if not p["used"]:
                    p["used"], p["on"] = True, True
                    break
        for p in packs:                       # a pack warmer than this is taken off
            if p["on"] and p["temp"] > 25.0:
                p["on"] = False

        if act["canopy"] and not canopy:
            batt -= 0.15
        canopy = act["canopy"]

        watts, parts = net_watts(T, air, act, packs, minute)
        rows.append(dict(minute=minute, body=T, thermal=read, naive_est=naive_est,
                         body_est=body_est, ambient=air["ambient"], rh=air["rh"],
                         solar=air["solar"], wind=air["wind"], canopy=canopy, slope=slope,
                         fan=act["fan"], mist=act["mist"],
                         packs_active=sum(1 for p in packs if p["on"]),
                         packs_left=sum(1 for p in packs if not p["used"]), water_l=water,
                         battery_pct=100 * batt / BATTERY_WH, battery_wh=batt,
                         eta_left=eta_left, net_w=watts, blocked=len(stopped), **parts))
        if minute == sc["minutes"]:
            break

        if act["mist"] > 0 and not pump_on:
            water = max(0.0, water - PRIME_ML / 1000.0)      # priming the line costs water
        pump_on = act["mist"] > 0

        for _ in range(int(60 / DT)):                        # one minute of physics
            watts, _ = net_watts(T, air, act, packs, minute)
            T += watts * DT / C_BODY
            for p in packs:
                if p["on"]:
                    q = PACK_U * max(0.0, (T - SKIN_GAP) - p["temp"])
                    p["absorbed"] += q * DT
                    p["temp"] = (PACK_START if p["absorbed"] < PACK_LATENT
                                 else PACK_START + (p["absorbed"] - PACK_LATENT) / PACK_C)
            water = max(0.0, water - act["mist"] * DT / 60.0 / 1000.0)
            if water <= 0.0:
                act["mist"] = 0.0
            batt -= (p_fan(act["fan"]) + p_pump(act["mist"]) + P_ESSENTIAL) * DT / 3600.0
            if batt <= 0.0:
                batt, act["fan"], act["mist"] = 0.0, 0.0, 0.0

    out = pd.DataFrame(rows)
    out.attrs["blocked"] = blocked
    out.attrs["reasons"] = reasons
    return out


def score(df, sc):
    "Everything we are allowed to claim about one run."
    left_wh = float(df["battery_wh"].iloc[-1])
    return dict(
        change=round(float(df["body"].iloc[-1] - df["body"].iloc[0]), 2),
        peak=round(float(df["body"].max()), 2),
        lowest=round(float(df["body"].min()), 2),
        burden=round(float(np.maximum(0.0, df["body"] - STOP_COOL).sum()), 1),
        over_warn=int((df["body"] > WARN_TEMP).sum()),
        water=round(float(sc["water_l"] - df["water_l"].iloc[-1]), 2),
        battery_left=round(float(df["battery_pct"].iloc[-1]), 1),
        packs=int(sc["packs"] - df["packs_left"].iloc[-1]),
        radio_min=int(left_wh / P_ESSENTIAL * 60),
        blocked=int(df.attrs.get("blocked", 0)))


print("Simulator ready.")
""")

md(r"""
Now the trap, drawn. We run everything at full power and plot four lines: the true simulated body
temperature, what the camera reads, what a bench that just adds a degree would believe, and what
the corrected estimate says.
""")

co(r"""
def c_max(obs, model=None):
    "Everything at full power. Three lines of code, and the first thing anybody writes."
    return dict(canopy=1, fan=1.0, mist=MIST_LEVELS["high"], release_pack=obs["packs_left"] > 0)


demo = run(c_max, make_scenario(), safety=False)

fig, ax = plt.subplots()
ax.plot(demo.minute, demo.body,      color=RED,   lw=3,   label="true simulated body temperature")
ax.plot(demo.minute, demo.thermal,   color=BLUE,  lw=2,   label="what the thermal camera reads")
ax.plot(demo.minute, demo.naive_est, color=GREY,  lw=2, ls="--", label="camera + 1 °C  (wrong)")
ax.plot(demo.minute, demo.body_est,  color=GREEN, lw=2, ls=":",  label="corrected estimate")
ax.axhline(STOP_COOL, color=ORANGE, ls=":", lw=1)
ax.text(0.2, STOP_COOL + 0.05, "stop cooling here", color=ORANGE, fontsize=8)
ax.set_xlabel("minutes"); ax.set_ylabel("°C")
ax.set_title("The camera sees wet skin, not the inside of a person")
ax.legend(fontsize=8)
plt.tight_layout(); plt.show()

gap = (demo.body - demo.naive_est).max()
err = (demo.body - demo.body_est).abs().mean()
print(f"Worst gap between the true temperature and 'camera + 1 °C':  {gap:.2f} °C")
print(f"Average error of the corrected estimate:                     {err:.2f} °C")
first_wrong = demo[demo.naive_est <= STOP_COOL].minute.min()
print(f"A bench using 'camera + 1 °C' would stop cooling at minute {first_wrong:.0f}, "
      f"when the person is really at {demo[demo.minute == first_wrong].body.iloc[0]:.2f} °C.")
""")

md(r"""
That is the whole lesson of this section: **never trust a sensor reading without subtracting your
own effect on it.** The bench is changing the very thing it is measuring.
""")
see("sensors", "And what it cannot")

# ============================================================ 5. BASELINE
md(r"""
## 5 · Doing nothing — the baseline

Before any strategy can be called good, we need the number it has to beat. So: switch the bench
on, and tell it to do nothing. No shade, no fan, no mist, no packs. Fourteen minutes in full sun.

Everything later in this notebook is a claim against this line. If the baseline is wrong,
everything built on it is wrong too.
""")

co(r"""
def c_none(obs, model=None):
    return dict(canopy=0, fan=0.0, mist=0.0, release_pack=False)


SC = make_scenario()          # the emergency from the front page
base = run(c_none, SC, safety=False)
s = score(base, SC)

fig, ax = plt.subplots()
ax.plot(base.minute, base.body, color=RED, lw=3)
ax.axhline(WARN_TEMP, color=RED, ls="--", lw=1)
ax.text(0.2, WARN_TEMP + 0.05, "simulated warning line", color=RED, fontsize=8)
ax.set_xlabel("minutes"); ax.set_ylabel("simulated body temperature °C")
ax.set_title("Nothing at all — the baseline")
plt.tight_layout(); plt.show()

print(f"Start        {base.body.iloc[0]:.2f} °C")
print(f"After {SC['minutes']} min  {base.body.iloc[-1]:.2f} °C   ({s['change']:+.2f} °C)")
print(f"Minutes above {WARN_TEMP} °C: {s['over_warn']} of {SC['minutes']+1}")
print(f"Water used {s['water']:.2f} L,  battery left {s['battery_left']:.1f} %")
""")

md(r"""
Note the last line. Doing nothing still spends battery, because the radio, the screen and the
speaker never switch off. **There is no zero-cost option.**
""")
see("nothing", "The baseline")

# ============================================================ 6. SHADE
md(r"""
## 6 · Shade only

Slide the canopy out. Nothing else changes.

The canopy does two things. It blocks about 88 % of the sunshine falling on the person, and it
shades the paving, so the surface underneath cools from about 48 °C to about 43 °C and radiates
less heat upward.

It costs one push of a small motor — call it 0.15 watt-hours, which is a quarter of one percent
of the battery — and **no water at all**.
""")

co(r"""
def c_shade(obs, model=None):
    return dict(canopy=1, fan=0.0, mist=0.0, release_pack=False)


shade = run(c_shade, SC, safety=False)


def compare(runs, title, ylim=None):
    "Draw several strategies on the same axes."
    colours = [GREY, PURPLE, BLUE, "#00838f", RED, ORANGE, GREEN, "#ad1457", "#00695c"]
    fig, ax = plt.subplots()
    for (name, df), c in zip(runs.items(), colours):
        ax.plot(df.minute, df.body, color=c, lw=2.5, label=name)
    ax.axhline(WARN_TEMP, color=RED,   ls="--", lw=1)
    ax.axhline(STOP_COOL, color=GREEN, ls=":",  lw=1)
    ax.set_xlabel("minutes"); ax.set_ylabel("simulated body temperature °C")
    ax.set_title(title); ax.legend(fontsize=8)
    if ylim:
        ax.set_ylim(*ylim)
    plt.tight_layout(); plt.show()


def table(runs, sc):
    rows = []
    for name, df in runs.items():
        s = score(df, sc)
        rows.append({"strategy": name, "change °C": s["change"], "peak °C": s["peak"],
                     "lowest °C": s["lowest"], "heat burden": s["burden"],
                     "min over 40": s["over_warn"], "water L": s["water"],
                     "battery %": s["battery_left"], "packs": s["packs"],
                     "radio min": s["radio_min"], "blocked": s["blocked"]})
    return pd.DataFrame(rows).set_index("strategy")


compare({"no cooling": base, "shade only": shade}, "What a piece of cloth is worth")
print(table({"no cooling": base, "shade only": shade}, SC).to_string())
""")

md(r"""
Shade takes a rise of **+2.18 °C** down to **+0.88 °C** — it removes about 60 % of the problem —
for no water and essentially no power.

But read the "change" column again: it is still **positive**. Shade does not cool anybody. It
only slows the heating down. That is the honest limit of a passive tool, and it is also why shade
is the one action the controller should take every single time and never ration.
""")
see("shade", "The cheapest big win")

# ============================================================ 7. FAN
md(r"""
## 7 · Fan only — and when a fan is a heater

Everybody's instinct on a hot day is a fan. Let us test it properly.

A fan does two things at once:

1. It **speeds up evaporation**, because moving air carries vapour away from the skin. This
   cools.
2. It **speeds up heat exchange with the air**. This cools *only if the air is cooler than the
   skin*. If the air is hotter than the skin, faster air delivers heat faster.

On a 41 °C afternoon the skin is around 38 °C, so the air is already warmer than the skin. The
fan is bringing heat in. Whether it is worth running depends entirely on whether evaporation can
beat that.

And there is the problem: **a person in heat illness has often stopped sweating.** Dry skin has
almost nothing to evaporate. So the fan delivers heat and gets very little back.
""")

co(r"""
def c_fan(obs, model=None):
    return dict(canopy=1, fan=1.0, mist=0.0, release_pack=False)


fan_only = run(c_fan, SC, safety=False)
compare({"no cooling": base, "shade only": shade, "fan only": fan_only},
        "The fan, on dry skin, in dry heat")
print(table({"shade only": shade, "fan only": fan_only}, SC).to_string())
""")

md(r"""
On this afternoon the fan helps a little — **+0.71 °C** against shade's **+0.88 °C** — and costs
19 points of battery to do it. The person still gets hotter.

Now change the weather and watch the sign flip.
""")

co(r"""
def fan_benefit(ambient, rh, mist=0.0, T=39.8, wind=0.6):
    "Watts the fan removes. A negative answer means the fan is adding heat."
    air = dict(ambient=ambient, rh=rh, solar=880.0, wind=wind)
    off = net_watts(T, air, dict(canopy=1, fan=0.0, mist=mist), [], 0.0)[0]
    on  = net_watts(T, air, dict(canopy=1, fan=1.0, mist=mist), [], 0.0)[0]
    return off - on


temps = np.arange(32, 46.1, 0.5)
hums  = np.arange(0.10, 0.91, 0.025)

fig, axes = plt.subplots(1, 2, figsize=(11, 3.6))
for ax, mist, label in zip(axes, [0.0, MIST_LEVELS["medium"]], ["dry skin", "skin kept wet"]):
    z = np.array([[fan_benefit(a, r, mist) for a in temps] for r in hums])
    lim = np.abs(z).max()
    im = ax.pcolormesh(temps, hums * 100, z, cmap="RdBu", vmin=-lim, vmax=lim)
    ax.contour(temps, hums * 100, z, levels=[0], colors="black", linewidths=1.5)
    ax.set_xlabel("air temperature °C"); ax.set_ylabel("humidity %")
    ax.set_title(f"Fan at full power, {label}", fontsize=10)
    plt.colorbar(im, ax=ax, label="watts removed")
plt.tight_layout(); plt.show()

print("Watts the fan removes (negative means it is a heater):")
for a, r, name in [(41, 0.32, "dry heat 41 °C / 32 %"),
                   (41, 0.78, "humid heat 41 °C / 78 %"),
                   (44, 0.30, "very hot dry 44 °C / 30 %")]:
    print(f"  {name:26s} dry skin {fan_benefit(a, r):+7.0f} W   "
          f"wet skin {fan_benefit(a, r, MIST_LEVELS['medium']):+7.0f} W")

print()
print("On DRY skin, the fan turns into a heater above:")
for r in (0.10, 0.30, 0.50, 0.70, 0.90):
    over = [a for a in np.arange(32, 46.01, 0.1) if fan_benefit(a, r) < 0]
    print(f"  {int(r*100):>2} % humidity   {over[0]:.1f} °C" if over
          else f"  {int(r*100):>2} % humidity   never, below 46 °C")
""")

md(r"""
Read the left panel. The black line is where the fan stops helping, and where it sits depends on
the humidity as much as on the temperature: at 10 % humidity the fan keeps helping until 45.7 °C,
but at 90 % humidity it turns into a heater at **39.4 °C** — which is an ordinary summer day in
many places.

Now read the right panel. Once the skin is wet, the fan is useful nearly everywhere — the black
line moves right and up, and the red corner shrinks to a sliver. (The two panels have their own
colour scales, so compare the black lines, not the shades of blue.) That is the rule worth
remembering:

> **A fan is not a cooler. It is a multiplier for evaporation.**

This is one of the deterministic limits in `apply_limits`. Before the fan is allowed to run, the
bench computes the heat balance with the fan on and with it off, and refuses the fan if it would
add heat. The AI has no way to override it.
""")

co(r"""
print("How often the limit stops a 'fan at full power' controller, over a 14 minute run:")
for name, sc in [("dry heat 41 °C / 32 %",     make_scenario()),
                 ("humid heat 41 °C / 78 %",   make_scenario(rh=0.78)),
                 ("very hot dry 44 °C / 30 %", make_scenario(ambient=44.0, rh=0.30, solar=950.0))]:
    df = run(c_fan, sc, safety=True)
    print(f"  {name:26s} blocked {df.attrs['blocked']:2d} times, "
          f"final change {score(df, sc)['change']:+.2f} °C")
""")
see("fan", "When airflow is a heater")

# ============================================================ 8. MIST
md(r"""
## 8 · Mist only — cooling per litre

Evaporation is the strongest tool the bench has, by a very long way. Turning one kilogram of
water into vapour absorbs **2.43 million joules**. The whole body only needs 262 500 joules to
change by a degree, so in principle a few hundred millilitres could do an enormous amount.

In practice it cannot, for two reasons.

**Most of the water never evaporates off the skin.** It runs off, or it evaporates into the air
before it lands. We assume only 9 % of what the pump sends actually stays on the skin and
evaporates from it. That is the `DELIVERY` constant.

**Skin can only get so wet.** Once `w` reaches 1.00 the skin is fully covered and evaporation is
limited by the air, not by the water. Every extra millilitre after that point is watering the
pavement.

So the interesting number is not "how much cooling" — it is **how much cooling per litre**.
""")

co(r"""
def water_curve(air, fan=0.75, T=39.8):
    "Cooling bought per litre of water, at each mist rate."
    base_w = net_watts(T, air, dict(canopy=1, fan=fan, mist=0.0), [], 0.0)[0]
    rows = []
    for m in [0, 40, 80, 120, 160, 200, 240, 300, 400, 500]:
        net, p = net_watts(T, air, dict(canopy=1, fan=fan, mist=float(m)), [], 0.0)
        lph   = m * 60 / 1000.0
        extra = (base_w - net) / C_BODY * 60.0          # extra °C per minute removed
        rows.append({"mist mL/min": m, "skin wetness": round(p["w"], 2),
                     "evaporation W": round(p["q_evap"]),
                     "°C per minute": round(net / C_BODY * 60, 3),
                     "litres per hour": round(lph, 1),
                     "°C per litre": round(extra / lph * 60, 2) if lph else 0.0})
    return pd.DataFrame(rows)


wc = water_curve(AIR)
print(wc.to_string(index=False))

fig, ax = plt.subplots()
ax.bar(wc["mist mL/min"], wc["°C per litre"], width=25, color=BLUE, label="°C of cooling per litre")
ax2 = ax.twinx()
ax2.plot(wc["mist mL/min"], -wc["°C per minute"], color=ORANGE, lw=3, marker="o",
         label="cooling rate")
ax2.axhline(0, color=GREY, lw=1)
ax.set_xlabel("mist rate, mL per minute"); ax.set_ylabel("°C per litre")
ax2.set_ylabel("°C per minute removed\n(below zero = still warming)"); ax2.grid(False)
ax.set_title("More water stops buying more cooling")
ax.legend(loc="lower left", fontsize=8); ax2.legend(loc="lower right", fontsize=8)
plt.tight_layout(); plt.show()
""")

md(r"""
Read the table. Up to **240 mL/min** every litre buys the same **0.79 °C**. At 240 the skin
wetness hits 1.00. After that the cooling rate stops improving completely, and the value per
litre collapses — 0.46 °C at 400 mL/min, 0.37 °C at 500.

**400 mL/min gives exactly the same cooling as 240 mL/min and uses 1.7 times the water.** On an
8 litre tank that is the difference between 33 minutes of misting and 20.

The exact position of that cliff moves with the weather. In humid air the air can take less
vapour, so the skin saturates at a much lower mist rate — and the cooling you get for it is far
smaller.
""")

co(r"""
print("Six afternoons that all read 41 °C on a thermometer (canopy out, fan 75 %):")
print(f"  {'humidity':>9}  {'air can take':>13}  {'skin fully wet at':>18}  {'best cooling':>13}")
for r in (0.20, 0.32, 0.50, 0.65, 0.78, 0.90):
    air = dict(ambient=41.0, rh=r, solar=880.0, wind=0.6)
    cap = skin_state(39.8, air, 0.75, MIST_LEVELS["medium"])[3]
    w   = water_curve(air)
    sat = w[w["skin wetness"] >= 1.0]["mist mL/min"]
    sat = int(sat.iloc[0]) if len(sat) else 500
    print(f"  {int(r*100):>8} %  {cap:>11.0f} W  {sat:>15d} mL/min  "
          f"{w['°C per minute'].min():>+10.3f} °C/min")
""")

md(r"""
That table is the answer to "why not just use the air temperature". **41 °C at 20 % humidity and
41 °C at 90 % humidity are not the same afternoon.** In the first the air can carry away over a
kilowatt. In the last it can carry away nothing at all, and no amount of water will change that.

Two more things are hiding in there.

**Every litre that evaporates is worth the same.** The value per litre is 0.79 °C in all of these
— latent heat is latent heat. What changes is the *ceiling*: in humid air the skin is already
fully wet at 80 mL/min, and there is simply nowhere for more water to go.

**Above about 60 % humidity, mist and fan alone cannot bring the temperature down at all.** At
65 % the best they manage is +0.012 °C a minute — they slow the rise, they do not reverse it.
That is where the cold packs stop being a backup and become the main tool.

Now run mist on its own, with no fan, and see what it does to the tank.
""")

co(r"""
def c_mist(obs, model=None):
    return dict(canopy=1, fan=0.0, mist=MIST_LEVELS["high"], release_pack=False)


mist_only = run(c_mist, SC, safety=False)
compare({"no cooling": base, "shade only": shade, "fan only": fan_only, "mist only": mist_only},
        "Water, with no air moving over it")
print(table({"fan only": fan_only, "mist only": mist_only}, SC).to_string())
""")

md(r"""
Mist alone is the first strategy that actually holds the line: **−0.19 °C** instead of a rise, and
**zero** minutes above the warning temperature. It costs **5.64 litres** of an 8 litre tank to do
it, with no fan to help the vapour leave.

Fan and mist together will do much better than either. That is the whole point of the right-hand
panel in section 7.
""")
see("mist", "Cooling per litre")

# ============================================================ 9. PACKS
md(r"""
## 9 · Three cold packs

A chemical cold pack in the compartment. Squeeze it, it goes cold, press it against the neck or
the armpits. It uses **no water and no battery**, which makes it the answer when the pump fails,
the tank is empty, or the air is too humid to evaporate anything.

It also cannot be undone. Once a pack is opened it is spent.

A pack holds about **45 000 joules** in its melting, plus a bit more as it warms up afterwards.
Divide by the roughly 84 watts it can pull through the skin contact, and you get its useful life.
""")

co(r"""
pack = dict(on=True, absorbed=0.0, temp=PACK_START)
t, power, temp = [], [], []
for step in range(25 * 6):
    q = PACK_U * max(0.0, 38.8 - pack["temp"])
    pack["absorbed"] += q * DT
    pack["temp"] = (PACK_START if pack["absorbed"] < PACK_LATENT
                    else PACK_START + (pack["absorbed"] - PACK_LATENT) / PACK_C)
    t.append(step * DT / 60.0); power.append(q); temp.append(pack["temp"])

fig, ax = plt.subplots()
ax.plot(t, power, color=BLUE, lw=3, label="cooling from the pack, W")
ax.plot(t, temp, color=ORANGE, lw=2, label="pack temperature °C")
ax.axvline(PACK_LATENT / (PACK_U * 38.3) / 60.0, color=GREEN, ls="--", lw=1)
ax.text(PACK_LATENT / (PACK_U * 38.3) / 60.0 + 0.3, 60, "the ice has melted",
        color=GREEN, fontsize=8)
ax.set_xlabel("minutes after the pack is opened"); ax.set_ylabel("watts  ·  °C")
ax.set_title("A cold pack is not a battery you can refill"); ax.legend(fontsize=8)
plt.tight_layout(); plt.show()

print(f"Steady while melting:  {power[10]:.0f} W")
print(f"After 10 minutes:      {power[60]:.0f} W")
print(f"After 15 minutes:      {power[90]:.0f} W")
print(f"Three packs together:  {3*power[10]:.0f} W  — for about nine minutes, and then not.")
""")

md(r"""
That flat section is the ice melting. It is the useful part, and it lasts about **nine minutes**.
After that the pack warms quickly and its cooling falls away.

Which raises the real decision: with three packs and a fourteen-minute wait, do you open all
three now, or stagger them? Opening all three gives you 250 W for nine minutes and then nothing.
Staggering gives you 84 W for nearly half an hour. Neither is obviously right — it depends on how
long the wait turns out to be, which nobody knows at the start.

The controller in section 14 is allowed to open one pack per minute and works this out for
itself.
""")
see("packs", "Spend now or keep one")

# ============================================================ 10. MAXIMUM
md(r"""
## 10 · Everything at full power

This is the strategy every team writes first:

```python
fan_speed  = 1.0
mist_rate  = 1.0
canopy_open = True
release all the packs
```

It is not a stupid idea. It cools faster than anything else in this notebook. The question is
what it costs, and whether it knows when to stop.
""")

co(r"""
maxed = run(c_max, SC, safety=False)          # safety=False: the raw version, no limits
compare({"no cooling": base, "mist only": mist_only, "maximum fixed": maxed},
        "Everything at full power, with no limits underneath")
print(table({"mist only": mist_only, "maximum fixed": maxed}, SC).to_string())

fig, axes = plt.subplots(1, 2, figsize=(11, 3.2))
# Both run the mist at 400 mL/min, so their water lines sit exactly on top of
# each other - "mist only" is dashed so you can see that they do.
for df, name, c, ls in [(mist_only, "mist only", BLUE, "--"), (maxed, "maximum fixed", RED, "-")]:
    axes[0].plot(df.minute, df.water_l, color=c, lw=2.5, ls=ls, label=name)
    axes[1].plot(df.minute, df.battery_pct, color=c, lw=2.5, ls=ls, label=name)
axes[0].set_ylabel("litres in the tank"); axes[1].set_ylabel("battery %")
for ax in axes:
    ax.set_xlabel("minutes"); ax.legend(fontsize=8)
plt.tight_layout(); plt.show()
""")

md(r"""
Full power takes the person from 39.80 °C down to **37.26 °C**. That is not a triumph. It is
**1.24 °C past the point at which cooling should stop**, and cooling somebody too far is a new
emergency, not a solved one.

It also spends **5.64 litres** and leaves the battery at **24.6 %**, which is 52 minutes of radio.

The stop line matters enough to be worth stating plainly. Emergency cooling is normally stopped
somewhere around 38.5–39 °C, precisely because the cooling does not stop when you switch the
equipment off — the person keeps losing heat for a while afterwards. Overshooting is a real
risk, not a theoretical one.

So: full power is fast, it overshoots, it empties the tank, and it flattens the battery. Every
controller from here on has to beat that on **all four** counts, not one.
""")

co(r"""
maxed_safe = run(c_max, SC, safety=True)      # the same controller, with the limits switched on
print(table({"maximum fixed, no limits": maxed, "maximum fixed, with limits": maxed_safe},
            SC).to_string())
print()
print("What the limits stopped:")
print(pd.Series(maxed_safe.attrs["reasons"]).value_counts().to_string())
""")

md(r"""
The same three lines of code, with the safety layer switched on, stop at **38.30 °C** instead of
37.26 and use **3.24 litres** instead of 5.64. The controller did not get any cleverer. The
limits underneath it did the work.
""")
see("maxout", "The obvious answer")

# ============================================================ 11. RULES
md(r"""
## 11 · Rules that watch the tank

Now a real controller — a short list of thresholds that a person can read, argue with and sign
off. No model, no training data.

It needs to know four things:

1. **How much battery the radio needs.** We reserve enough for the rest of the wait plus twenty
   minutes of handover. Everything above that line is spendable.
2. **How much water it can afford per minute.** Take what is in the tank, keep half a litre back,
   and divide by the minutes left.
3. **Whether the air can take any vapour at all.** If not, spending water is pointless.
4. **Whether a pack is already on the person.** If not, and the person is hot, open one.

And one piece of knowledge from section 8, written straight into the code: **never go above
medium mist**, because above that the water stops buying anything.
""")

co(r"""
def c_rules(obs, model=None):
    "Engineering thresholds. Every line can be read and argued with."
    a = dict(canopy=1 if obs["solar"] > 200 else 0, fan=0.0, mist=0.0, release_pack=False)
    if obs["cooling_locked"]:
        return a                                     # cool enough - shade only

    free_wh = obs["battery_wh"] - obs["reserve_wh"]  # what we may spend on cooling
    budget  = max(0.0, (obs["water_l"] - 0.5) * 1000.0) / max(1.0, obs["eta_left"])

    air   = dict(ambient=obs["ambient"], rh=obs["rh"], solar=obs["solar"], wind=obs["wind"])
    e_max = skin_state(obs["body_est"], air, 0.75, MIST_LEVELS["medium"])[3]

    if obs["pump_ok"] and free_wh > 2.0 and e_max > 150.0:
        for name in ("medium", "low"):                # never above medium - section 8
            if MIST_LEVELS[name] <= budget:
                a["mist"] = MIST_LEVELS[name]
                break
    if a["mist"] > 0 and obs["fan_ok"] and free_wh > 3.0:
        a["fan"] = 0.75                               # the fan is only worth it on wet skin
    if obs["packs_left"] > 0 and obs["packs_active"] == 0 and obs["body_est"] > 39.0:
        a["release_pack"] = True                      # one at a time, so they last
    return a


ruled = run(c_rules, SC, safety=True)
compare({"no cooling": base, "maximum fixed": maxed, "rule based": ruled},
        "Thresholds against brute force")
print(table({"maximum fixed": maxed, "rule based": ruled}, SC).to_string())
""")

md(r"""
The rule controller lands at **−1.11 °C** using **2.44 litres** and leaving **41.7 %** of the
battery — 88 minutes of radio, against full power's 52. It never goes past the stop line.

It is not perfect, and section 17 shows exactly where it breaks: its water budget spreads the
tank **evenly** across the wait. That is the wrong shape. The body is hottest at the start, and
cooling early is worth more than cooling late, because the heat burden is added up over time.
""")

co(r"""
fig, axes = plt.subplots(1, 2, figsize=(11, 3.2))
axes[0].step(ruled.minute, ruled.mist, color=BLUE, lw=2, where="post", label="mist mL/min")
axes[0].step(ruled.minute, ruled.fan * 400, color=ORANGE, lw=2, where="post", label="fan × 400")
axes[0].set_ylabel("mL per minute"); axes[0].legend(fontsize=8)
axes[1].step(ruled.minute, ruled.packs_active, color=PURPLE, lw=2, where="post",
             label="packs on the person")
axes[1].plot(ruled.minute, ruled.body, color=RED, lw=2, label="body °C")
axes[1].axhline(STOP_COOL, color=GREEN, ls=":", lw=1)
axes[1].legend(fontsize=8)
for ax in axes:
    ax.set_xlabel("minutes")
plt.suptitle("What the rule controller chose, minute by minute", y=1.02)
plt.tight_layout(); plt.show()
""")
see("rules", "An interpretable controller")

# ============================================================ 12. FORECAST
md(r"""
## 12 · Guessing five minutes ahead

To choose well, the bench needs to answer a question: *if I set the fan here and the mist there,
where will the temperature be in five minutes?*

We could answer it with the physics we already wrote. A real bench cannot, because it does not
know the person's mass, their clothing, how much they have been exerting themselves, or whether
they are still sweating. So we learn the answer from data instead.

### Where the training data comes from

We play **400 emergencies**, each with different weather, a different starting temperature, a
different tank and battery, and — this is the important part — **randomly chosen settings every
minute**. If the training data only contained good decisions, the model would never learn what a
bad one does.

### What we ask it to predict

Not the temperature. The **change** in temperature over the next minute.

That distinction turns out to matter enormously, and it is worth its own paragraph. If you ask a
model to predict the temperature one minute from now, it can score 0.98 by simply repeating the
current temperature back at you. Bodies change slowly. Predicting the *change* is the only test
that shows whether the model has learned anything.
""")

co(r"""
FEATURES = ["body_est", "slope", "ambient", "rh", "solar", "wind",
            "fan", "mist", "packs_active", "canopy"]


def random_scenarios(n, seed=1):
    rng = np.random.default_rng(seed)
    return [make_scenario(
        ambient=float(rng.uniform(33, 45)), rh=float(rng.uniform(0.15, 0.85)),
        solar=float(rng.uniform(250, 980)), wind=float(rng.uniform(0.2, 2.5)),
        start_temp=float(rng.uniform(38.6, 41.0)), eta=float(rng.uniform(8, 26)),
        water_l=float(rng.uniform(1.5, 8.0)), battery_pct=float(rng.uniform(25, 100)),
        packs=int(rng.integers(0, 4))) for _ in range(n)]


def build_dataset(n_episodes=400, seed=1):
    "Settings picked at random, so the model sees bad choices as well as good ones."
    rows = []
    for i, sc in enumerate(random_scenarios(n_episodes, seed)):
        rng = np.random.default_rng(1000 + i)

        def ctrl(obs, model=None, rng=rng):
            return dict(canopy=int(rng.random() < 0.75),
                        fan=float(rng.choice(FAN_LEVELS)),
                        mist=float(rng.choice(list(MIST_LEVELS.values()))),
                        release_pack=bool(rng.random() < 0.12))

        df = run(ctrl, sc, seed=i, safety=False).copy()
        df["episode"]   = i
        df["next_body"] = df["body_est"].shift(-1)
        df["delta"]     = df["next_body"] - df["body_est"]
        rows.append(df.dropna(subset=["next_body"]))
    return pd.concat(rows, ignore_index=True)


data  = build_dataset(400)
train = data[data.episode < 300]
test  = data[data.episode >= 300]

print(f"{len(data):,} minutes of simulated emergency, from {data.episode.nunique()} episodes.")
print(f"Learning from {len(train):,}, judged on {len(test):,} it has never seen.")
print()
print(data[["body_est", "ambient", "rh", "fan", "mist", "packs_active", "delta"]]
      .describe().round(3).to_string())
""")

co(r"""
X_tr, y_tr = train[FEATURES].to_numpy(np.float32), train["delta"].to_numpy(np.float32)
X_te, y_te = test[FEATURES].to_numpy(np.float32),  test["delta"].to_numpy(np.float32)

models = {
    "linear regression": make_pipeline(StandardScaler(), LinearRegression()),
    "random forest":     RandomForestRegressor(n_estimators=120, min_samples_leaf=8,
                                               random_state=7, n_jobs=-1),
    "small neural net":  make_pipeline(StandardScaler(),
                                       MLPRegressor(hidden_layer_sizes=(48, 32), max_iter=900,
                                                    random_state=7, early_stopping=True)),
}
for m in models.values():
    m.fit(X_tr, y_tr)

rows = []
for name, m in models.items():
    p = m.predict(X_te)
    rows.append({"model": name,
                 "R² on the change": round(r2_score(y_te, p), 3),
                 "average error °C": round(mean_absolute_error(y_te, p), 4),
                 "R² on the level":  round(r2_score(test["next_body"], test["body_est"] + p), 4)})
rows.append({"model": "assume nothing changes",
             "R² on the change": round(r2_score(y_te, y_te * 0), 3),
             "average error °C": round(mean_absolute_error(y_te, y_te * 0), 4),
             "R² on the level":  round(r2_score(test["next_body"], test["body_est"]), 4)})
scores = pd.DataFrame(rows).set_index("model")
print(scores.to_string())
""")

md(r"""
Read the last two columns against each other.

On the **level**, every model scores about 0.99 — and so does the model that predicts no change
at all, at 0.982. If we had only looked at that column we would have declared victory and gone
home with a model that had learned nothing.

On the **change**, the picture is honest: the forest gets 0.472, the linear model 0.396, the
neural net 0.389, and "assume nothing changes" gets −0.025.

The forest wins. But before we conclude anything, the thing we actually need is a forecast five
minutes out, not one minute out. Errors pile up when you roll a model forward.
""")

co(r"""
def rollout_error(models, test, steps=5):
    "Feed the model its own predictions for five minutes and see how far out it ends up."
    seqs, truth = [], []
    for _, g in test.groupby("episode"):
        g = g.reset_index(drop=True)
        for i in range(len(g) - steps):
            seqs.append(g.loc[i:i + steps - 1, FEATURES].to_numpy(np.float32))
            truth.append(float(g["body_est"][i + steps]))
    seqs, truth = np.stack(seqs), np.array(truth)
    out = []
    for name, m in models.items():
        T, slope = seqs[:, 0, 0].copy(), seqs[:, 0, 1].copy()
        for k in range(steps):
            X = seqs[:, k, :].copy()
            X[:, 0], X[:, 1] = T, slope
            d = m.predict(X).astype(np.float32)
            T, slope = T + d, d
        out.append({"model": name, "error 5 minutes out °C": round(float(np.mean(np.abs(T - truth))), 3)})
    out.append({"model": "assume nothing changes",
                "error 5 minutes out °C": round(float(np.mean(np.abs(seqs[:, 0, 0] - truth))), 3)})
    return pd.DataFrame(out).set_index("model")


print(rollout_error(models, test).to_string())
""")

md(r"""
And there is the result that matters. **Five minutes out, all three models land between 0.109 and
0.111 °C** — within two hundredths of a degree of each other — against 0.231 for assuming nothing
changes.

The forest's advantage at one minute does not survive to five. Whatever it was picking up on was
short-lived detail, not the trend.

That is worth saying out loud, because it is the opposite of what the one-minute table suggested:

> On this problem, **the linear model is as good as the forest at the job we actually need it
> for** — and you can read a linear model, print its coefficients, and explain it to a safety
> reviewer.

We use the forest in the sections below because it is the best one-minute predictor and the
controller re-plans every minute. A team building this for real would have a strong argument for
the linear model instead.
""")

co(r"""
forest = models["random forest"]
imp = pd.Series(forest.feature_importances_, index=FEATURES).sort_values()

fig, ax = plt.subplots(figsize=(9.5, 3.4))
ax.barh(imp.index, imp.values, color=BLUE)
ax.set_xlabel("how much the forest leans on this")
ax.set_title("What the forecaster actually uses")
plt.tight_layout(); plt.show()
print(imp.sort_values(ascending=False).round(3).to_string())
""")

md(r"""
The mist setting comes first, which is no surprise. **Humidity comes second** — above air
temperature, and far above the current body temperature.

Nobody told the model that humidity governs evaporation. It found that out from four hundred
simulated afternoons. It is the clearest sign in this notebook that the model learned the physics
rather than memorising the episodes.
""")
see("forecast", "Three forecasters")

# ============================================================ 13. COST
md(r"""
## 13 · Writing down what "good" means

A forecast on its own decides nothing. We have to say what we are trying to achieve, and we have
to say it in a way that a computer can compare two options with.

$$
J = w_1 A_T + w_2 W + w_3 E + w_4 R + w_5 U
$$

| Term | What it counts | Weight |
|---|---|---|
| $A_T$ | how far above 38.5 °C the person is, **squared**, added up over the next five minutes | 1.00 |
| $W$ | litres of water the setting would use | 0.45 |
| $E$ | watt-hours of battery the setting would use | 0.06 |
| $R$ | minutes by which the supplies would fall short of the wait | 0.30 |
| $U$ | commands the safety layer would refuse | 5.00 |

The controller tries every setting it is allowed and keeps the one with the smallest $J$.

### The one choice in there that changes everything

The heat term is **squared**. Being two degrees too hot is not twice as bad as being one degree
too hot — it is much worse than that.

We built this first without the square, and the controller behaved badly in humid air. Water buys
very little cooling when the air is already full of vapour, so the water term won the argument
and the controller rationed. The person then sat above 40 °C for eleven of the fourteen minutes,
and the controller was, by its own cost function, doing the right thing.

Squaring the heat term fixed it without touching a single other weight. **The bug was not in the
controller. It was in what we told it to want.**

### Who these weights belong to

They are a policy decision, not a technical one. How much water is one degree-minute of fever
worth? That question belongs to the ambulance service that runs the bench, not to whoever wrote
the code. Everything in this notebook can be re-run with different weights.
""")

co(r"""
W_BURDEN, W_WATER, W_ENERGY, W_RISK, W_UNSAFE = 1.0, 0.45, 0.06, 0.30, 5.0
HORIZON = 5

# Every setting the controller is allowed to choose between, once a minute.
CANDIDATES = [dict(canopy=1, fan=f, mist=m, release_pack=bool(p))
              for f in (0.0, 0.5, 0.75, 1.0)
              for m in MIST_LEVELS.values()
              for p in (0, 1)]

print(f"{len(CANDIDATES)} settings to choose between, every minute.")
print("Fan:", [f"{int(f*100)}%" for f in (0.0, 0.5, 0.75, 1.0)])
print("Mist:", list(MIST_LEVELS.keys()))
print("Cold pack: open one, or keep it")
""")
see("cost", "The cost function")

# ============================================================ 14. ADAPTIVE
md(r"""
## 14 · The resource-aware controller

Every minute, the bench does this:

1. Write down all **32 settings** it could choose.
2. For each one, ask the forecaster where the temperature goes over the next five minutes,
   assuming that setting is held.
3. Add up $J$ — heat burden, water, energy, risk of running short, and refused commands.
4. Pick the smallest, do it for one minute, and then do the whole thing again.

This is model-predictive control. It is not clever, it is just thorough: it looks at every option
and it looks a little way ahead.

We build **two** versions, and the difference between them is the whole point of the project:

- The **predictive** controller only cares about temperature. It uses the forecast, but it has no
  idea that water and battery are finite.
- The **resource-aware** controller uses the same forecast and the same search, but its cost
  includes the water, the battery, the risk of running out, and any command the safety layer
  would refuse.
""")

co(r"""
def make_ai(resource_aware=True, horizon=HORIZON):
    "Try every setting, roll the forecast forward five minutes, keep the cheapest."
    n    = len(CANDIDATES)
    fan  = np.array([c["fan"] for c in CANDIDATES], np.float32)
    mist = np.array([c["mist"] for c in CANDIDATES], np.float32)
    rel  = np.array([c["release_pack"] for c in CANDIDATES], np.float32)
    power = np.array([p_fan(f) + p_pump(m) + P_ESSENTIAL for f, m in zip(fan, mist)], np.float32)

    def controller(obs, model=None):
        if obs["cooling_locked"]:
            return dict(canopy=1 if obs["solar"] > 200 else 0, fan=0.0, mist=0.0,
                        release_pack=False)

        # One row per candidate setting, all rolled forward together.
        X = np.zeros((n, len(FEATURES)), np.float32)
        X[:, 1] = obs["slope"]
        X[:, 2], X[:, 3] = obs["ambient"], obs["rh"]
        X[:, 4], X[:, 5] = obs["solar"], obs["wind"]
        X[:, 6], X[:, 7] = fan, mist
        X[:, 8] = obs["packs_active"] + rel * (obs["packs_left"] > 0)
        X[:, 9] = 1.0

        T = np.full(n, obs["body_est"], np.float32)
        burden = np.zeros(n, np.float32)
        for _ in range(horizon):
            X[:, 0] = T
            d = model.predict(X).astype(np.float32)
            X[:, 1] = d
            T = T + d
            burden += np.maximum(0.0, T - STOP_COOL) ** 2      # squared - see section 13

        j = W_BURDEN * burden

        if resource_aware:
            litres = mist * horizon / 1000.0
            wh     = power * horizon / 60.0
            water_min = np.where(mist > 0, (obs["water_l"] - 0.3) * 1000.0
                                 / np.maximum(mist, 1e-9), np.inf)
            batt_min  = (obs["battery_wh"] - obs["reserve_wh"]) * 60.0 / power
            shortfall = np.maximum(0.0, obs["eta_left"] - np.minimum(water_min, batt_min))
            air = dict(ambient=obs["ambient"], rh=obs["rh"], solar=obs["solar"],
                       wind=obs["wind"])
            nblock = np.array([len(apply_limits(dict(c), obs, air)[1]) for c in CANDIDATES],
                              np.float32)
            j = j + W_WATER * litres + W_ENERGY * wh + W_RISK * shortfall + W_UNSAFE * nblock

        j = np.where((rel == 0) | (obs["packs_left"] > 0), j, np.inf)
        return dict(CANDIDATES[int(np.argmin(j))])

    return controller


predictive_ai = make_ai(resource_aware=False)
adaptive_ai   = make_ai(resource_aware=True)

pred = run(predictive_ai, SC, safety=True, model=forest)
adap = run(adaptive_ai,   SC, safety=True, model=forest)

compare({"maximum fixed": maxed, "rule based": ruled, "predictive AI": pred,
         "resource-aware AI": adap}, "The two AI controllers")
print(table({"maximum fixed": maxed, "rule based": ruled, "predictive AI": pred,
             "resource-aware AI": adap}, SC).to_string())
""")

co(r"""
print("What the resource-aware controller chose, minute by minute:")
print(adap[["minute", "body", "body_est", "fan", "mist", "packs_active",
            "water_l", "battery_pct", "blocked"]].round(2).to_string(index=False))
""")

md(r"""
Two things in that trace are worth pointing at.

**It picks medium mist, not high.** Nobody wrote that rule for it. The forecaster says high mist
does not cool any faster than medium — because the skin is already fully wet — and the water term
makes high mist more expensive. So it chooses medium and the tank lasts.

**It stops itself.** Once the corrected estimate reaches 38.5 °C the cooling lock comes on, the
mist goes off and the packs come off. It never goes below the stop line.

Compare that with the predictive controller, which uses the same forecast but does not know that
water is finite: it lands in the same place on temperature, and gets there having spent more of
everything.
""")
see("adaptive", "Search, predict, score")

# ============================================================ 15. SCOREBOARD
md(r"""
## 15 · The scoreboard

All eight strategies, on the same emergency, with the same weather and the same supplies.
""")

co(r"""
def run_all(sc, include_raw_max=True):
    "Every strategy on one scenario. Baselines have no safety layer - they are what a student writes."
    out = {}
    out["no cooling"]    = run(c_none,  sc, safety=False)
    out["shade only"]    = run(c_shade, sc, safety=False)
    out["fan only"]      = run(c_fan,   sc, safety=False)
    out["mist only"]     = run(c_mist,  sc, safety=False)
    if include_raw_max:
        out["maximum fixed"] = run(c_max, sc, safety=False)
    out["rule based"]        = run(c_rules,       sc, safety=True)
    out["predictive AI"]     = run(predictive_ai, sc, safety=True, model=forest)
    out["resource-aware AI"] = run(adaptive_ai,   sc, safety=True, model=forest)
    return out


all_runs = run_all(SC)
board = table(all_runs, SC)
print(board.to_string())
compare(all_runs, "Eight strategies, one emergency")
""")

co(r"""
SHORT = {"no cooling": "none", "shade only": "shade", "fan only": "fan", "mist only": "mist",
         "maximum fixed": "max", "rule based": "rules", "predictive AI": "predict",
         "resource-aware AI": "adaptive"}

fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
short = [SHORT[n] for n in board.index]
axes[0].bar(short, board["change °C"], color=[GREEN if v < 0 else RED for v in board["change °C"]])
axes[0].set_title("temperature change °C", fontsize=10); axes[0].axhline(0, color="black", lw=1)
axes[1].bar(short, board["water L"], color=BLUE)
axes[1].set_title("water used, litres", fontsize=10)
axes[2].bar(short, board["radio min"], color=ORANGE)
axes[2].axhline(20, color=RED, ls="--", lw=1)
axes[2].set_title("minutes of radio left", fontsize=10)
for ax in axes:
    ax.tick_params(axis="x", labelsize=8, rotation=45)
    for lab in ax.get_xticklabels():
        lab.set_ha("right")
plt.tight_layout(); plt.show()
""")

md(r"""
### The answer to the question at the top

> Can a controller that forecasts and adapts keep a person just as cool as running everything at
> full power, while using less water and less battery?

On this emergency, yes — and by a wide margin on the cost side.

| | maximum fixed | resource-aware AI |
|---|---|---|
| Where the temperature ended | 37.26 °C — **1.24 °C past the stop line** | 38.51 °C — right on it |
| Minutes above 40 °C | 0 | 0 |
| Water used | 5.64 L | **2.04 L** |
| Battery left | 24.6 % | **42.1 %** |
| Minutes of radio left | 52 | **89** |
| Commands the limits had to refuse | — | **0** |

Same job, **64 % less water**, and 37 more minutes of radio.

Full power does have one honest advantage: it gets the temperature down faster, so its heat
burden is 5.3 against 7.1. If you knew for certain that the wait was exactly fourteen minutes and
that the tank would be refilled afterwards, full power would be the better choice. You do not
know either of those things, and section 17 is about what happens when you assume you do.

### Being careful about what this table means

Every number here is about the simulation. It says nothing about how a real person would respond,
because the model has one lump of warm water where a person should be. What the table *can*
honestly compare is **resource use for a given amount of simulated cooling**, and that is an
engineering claim, not a medical one.
""")
see("board", "Eight strategies compared")

# ============================================================ 16. WEATHER
md(r"""
## 16 · Dry heat and humid heat

Two afternoons. Both read 41 °C. In the first the humidity is 32 %, in the second it is 78 %.
Nothing else changes — same bench, same supplies, same person, same fourteen-minute wait.
""")

co(r"""
dry_runs   = run_all(make_scenario(rh=0.32))
humid_runs = run_all(make_scenario(rh=0.78))

print("=== dry heat, 41 °C / 32 % humidity")
print(table(dry_runs, make_scenario(rh=0.32)).to_string())
print()
print("=== humid heat, 41 °C / 78 % humidity")
print(table(humid_runs, make_scenario(rh=0.78)).to_string())

fig, axes = plt.subplots(1, 2, figsize=(12, 3.4), sharey=True)
for ax, runs, ttl in zip(axes, [dry_runs, humid_runs],
                         ["dry heat 41 °C / 32 %", "humid heat 41 °C / 78 %"]):
    for (name, df), c in zip(runs.items(), [GREY, PURPLE, BLUE, "#00838f", RED, ORANGE, GREEN, "#ad1457"]):
        ax.plot(df.minute, df.body, color=c, lw=2, label=name)
    ax.axhline(WARN_TEMP, color=RED, ls="--", lw=1)
    ax.set_title(ttl, fontsize=10); ax.set_xlabel("minutes")
axes[0].set_ylabel("simulated body temperature °C")
axes[1].legend(fontsize=7, loc="upper right")
plt.tight_layout(); plt.show()
""")

md(r"""
### Experiment 1 — dry heat: is misting more useful than more fan?

Not even close. Fan only ends at **+0.71 °C**; mist only ends at **−0.19 °C**. The fan on its own
cannot cool skin that has nothing to evaporate. The fan is worth having, but only *underneath*
the mist.

### Experiment 2 — humid heat: does the controller waste water?

This is the interesting one. In humid air the air can only take **180 watts** away, against 940
watts in dry air. Water is nearly worthless.

Look at what each controller does with that:

| | maximum fixed | predictive AI | resource-aware AI |
|---|---|---|---|
| Temperature change | −0.21 °C | −0.20 °C | −0.07 °C |
| Water used | 5.64 L | 5.64 L | **3.40 L** |
| Battery left | 24.6 % | 25.6 % | **42.7 %** |
| Minutes of radio left | 52 | 54 | **90** |

The resource-aware controller gives up 0.14 °C — a difference nobody could measure on a real
person — and keeps **2.24 litres** and **36 extra minutes of radio**. In an afternoon where the
water is barely working, it stops spending it.

Nobody wrote a humidity rule for the AI. It came out of the cost function and the forecaster,
which had learned that humidity is the second most important thing on the list.

And notice what everything struggles with here: even full power only manages −0.21 °C. **In
humid heat the honest answer is that a bench like this cannot do very much**, and the useful
things it does are shade, cold packs, and calling for help early.
""")
see("weather", "Two different problems")

# ============================================================ 17. SURPRISES
md(r"""
## 17 · When something breaks

Real benches have failures, and real ambulances get held up. Seven things that go wrong.
""")

co(r"""
SURPRISES = {
    "the pump fails after 4 minutes":        make_scenario(pump_fail_at=4),
    "the fan fails after 5 minutes":         make_scenario(fan_fail_at=5),
    "the battery starts at 25 %":            make_scenario(battery_pct=25.0),
    "responders slip from 8 to 25 minutes":  make_scenario(eta=8.0, eta_extends_at=6,
                                                           eta_new=25.0),
    "half a tank and a 25 minute wait":      make_scenario(water_l=4.0, eta=25.0),
    "humidity jumps to 85 % at minute 6":    make_scenario(humidity_jump_at=6,
                                                           humidity_jump_to=0.85),
    "the person walks away at minute 8":     make_scenario(leaves_at=8),
}

summary = []
for label, sc in SURPRISES.items():
    runs = run_all(sc)
    for name in ["maximum fixed", "rule based", "predictive AI", "resource-aware AI"]:
        s = score(runs[name], sc)
        summary.append({"what happened": label, "strategy": name, "change °C": s["change"],
                        "lowest °C": s["lowest"], "heat burden": s["burden"],
                        "water L": s["water"], "battery %": s["battery_left"],
                        "radio min": s["radio_min"], "blocked": s["blocked"]})
summary = pd.DataFrame(summary)
for label in SURPRISES:
    print(f"=== {label}")
    print(summary[summary["what happened"] == label].drop(columns="what happened")
          .set_index("strategy").to_string())
    print()
""")

md(r"""
### Experiment 3 — the battery starts at 25 %

This is the clearest result in the notebook.

| | maximum fixed | resource-aware AI |
|---|---|---|
| Temperature change | −1.89 °C | −1.07 °C |
| Battery left | **0.0 %** | 10.7 % |
| Minutes of radio left | **0** | 22 |

Full power cools better and **kills the bench**. When the responders arrive there is no radio, no
screen and no speaker. A bench that cannot talk to anybody is not a slightly worse bench; it is a
lump of metal.

The reserve is not a preference. It is calculated — enough watt-hours for the rest of the wait
plus twenty minutes of handover — and the safety layer cuts the fan and the pump the moment the
battery reaches it, whatever the AI wants.

### Experiment 4 — the ambulance slips from 8 to 25 minutes

The bench is told help is 8 minutes away, plans for 8 minutes, and then at minute 6 is told it is
25.

| | maximum fixed | resource-aware AI |
|---|---|---|
| Temperature change | −3.20 °C | −1.06 °C |
| Lowest temperature | **36.46 °C** | 38.54 °C |
| Water used | **8.00 L — the whole tank** | 2.32 L |
| Battery left | **0.2 %** | 35.9 % |
| Minutes of radio left | **0** | 76 |

Full power empties everything and cools the person **two degrees below the stop line**. The
resource-aware controller re-plans the moment the estimate changes, because the wait is one of
the inputs to its cost, and finishes with three-quarters of the tank and an hour of radio.

**Should resources be used aggressively or rationed?** The honest answer from this table: neither.
They should be spent at the rate that gets the person under the stop line and no faster, and the
plan should be redone every time the estimate changes.

### Experiment 5 — the pump fails

The pump seizes at minute four. The mist is gone; only shade, the fan and the cold packs are
left.

Both AI controllers fall back and land in almost the same place — **−0.46 °C** for the
predictive one, **−0.42 °C** for the resource-aware one. What separates them is the last column:

| | commands the safety layer had to refuse |
|---|---|
| predictive AI | **11** |
| resource-aware AI | **0** |

The predictive controller asks for mist every single minute for the rest of the run, and is
refused every single time. The resource-aware one counts refused commands in its cost, so it
stops asking after the first minute and spends its attention on what still works.

That is a small thing on a chart and a large thing in a control room, where every refused command
is a line in a log that somebody has to read.

### The two remaining surprises

**Half a tank and a 25 minute wait** is where the rule controller shows its weakness. Its heat
burden is 21.4 against the predictive controller's 8.2. Its budget works out at 3.5 litres over
25 minutes — 140 mL a minute — which is less than medium, so it drops all the way to the low
setting of 80 and cools slowly for the whole wait. Cooling early is worth more, because the
burden is added up over time, and a flat budget cannot express that.

The resource-aware controller is not blameless on this one either: its burden is **16.8**, twice
the predictive controller's. It is holding water back against a shortfall it has calculated, and
on this run it held back more than it needed to — it finished with 1.8 litres still in the tank.
That is what the risk weight $w_4$ buys, and whether it is worth 8 degree-minutes is exactly the
kind of question the weights exist to make arguable.

**The person walks away at minute 8.** The load cell reports an empty seat. The safety layer shuts
everything off and would tell the dispatcher. The rule controller keeps commanding into thin air
and is blocked **7** times; the resource-aware one is blocked **1**.

A bench that keeps misting an empty seat is not dangerous, but it is spending a tank on nothing,
and it is a very visible sign that nobody checked.
""")
see("surprises", "Failing safely")

# ============================================================ 18. WRONG
md(r"""
## 18 · What it still gets wrong

Being clear about this is more useful than any of the results above.

**The person is one lump of warm water.** No core and shell, no blood flow, no age, no weight
that is not 75 kg, no illness, no medication, no clothing beyond one blanket factor. Real
thermoregulation is a large field and this is not in it.

**We assume the skin can be reached.** In public, on a bench, with a person who may be confused,
that is optimistic. Clothing is the single biggest thing between the mister and the skin, and our
one clothing factor does not begin to cover it.

**The starting temperature is given to us.** In real life nobody knows it. The bench cannot
measure core temperature and neither can a bystander. Everything the controller does is built on
a corrected camera reading, and section 4 shows how easily that goes wrong.

**The weather is steady.** Apart from one humidity jump, our afternoons do not have clouds, gusts
or a passing shower — all of which would change the answer.

**The failures are clean.** Pumps fail by stopping. Real pumps fail by running dry, spraying
unevenly, or reporting that they are fine while delivering nothing. A sensor that lies is far more
dangerous than one that stops, and none of ours lie.

**The cost weights are ours.** Change $w_2$ and the whole character of the bench changes. We
picked numbers that produced sensible behaviour, which is not the same as picking correct ones.

**No person is in the loop in the simulation.** In a real deployment a dispatcher is watching the
whole time, and their instructions override everything here.
""")

# ============================================================ 19. RULES
md(r"""
## 19 · The rules that do not move

Everything above is engineering: how to spend eight litres and sixty watt-hours well. This
section is not engineering, and it is not negotiable.

### The order things happen in

```
somebody presses the button, or a dispatcher opens the bench
                    ↓
an approved emergency protocol starts, and help is called
                    ↓
the bench reads its sensors and its own supplies
                    ↓
the AI chooses fan, mist, canopy and packs
                    ↓
deterministic limits check every command
                    ↓
the hardware does what is left
                    ↓
a dispatcher watches, and can take it all back at any moment
```

Note where the AI sits. It is in the middle, and there is a layer above it and a layer below it.

### What the bench must never do

- **It never decides that somebody is ill.** A person or a dispatcher switches it on. There is no
  code path in which the bench activates itself.
- **It never names a condition.** "The surface reading is high" is as far as it goes. It does not
  say heatstroke, and it does not say anything about what is wrong with a person.
- **It never decides that professional help is unnecessary**, and it never cancels a call.
- **Nothing generative writes an instruction.** The screen shows pages a clinician wrote and
  approved. The AI chooses which page. It does not write one.
- **A dispatcher outranks it.** Every control can be taken over, and that branch is checked before
  anything else.
- **The radio's share of the battery is reserved before any cooling is allowed.** Cooling is what
  the bench does with what is left over, not the other way round.
- **Cooling stops at 38.5 °C**, whatever the AI would prefer. Cooling somebody too far is a new
  emergency.
- **It never runs the fan when the fan would add heat**, and never runs the pump dry.
- **When it cannot see, it says so.** An empty seat, a failed pump, a reading it does not trust —
  all of these go to the dispatcher rather than being guessed at.

### Why the limits are separate code

Every one of those rules is a few lines in `apply_limits`, checked in a fixed order, with no model
anywhere near them. That is deliberate. A limit you can only verify by testing a model is not a
limit; it is a hope.
""")

co(r"""
print("Every limit in the layer, in the order it is checked:")
for i, line in enumerate([
        "nobody is on the bench           -> everything off",
        "cool enough (38.5 C)             -> mist off, packs off, fan at most 25 %",
        "the pump has failed              -> mist off",
        "tank at 0.30 L                   -> mist off, the pump is protected",
        "the fan has failed               -> fan off",
        "battery at the radio reserve     -> fan and mist off",
        "the fan would add heat           -> fan off"], 1):
    print(f"  {i}. {line}")
print()
print("On the main emergency, the resource-aware controller was refused",
      adap.attrs["blocked"], "times.")
print("Full power, with the limits switched on, was refused",
      maxed_safe.attrs["blocked"], "times.")
""")
see("limits", "The boundaries")

# ============================================================ 20. DASHBOARD
md(r"""
## 20 · The CoolBench dashboard

Everything in one place. Move a slider and the whole emergency re-runs.

If `ipywidgets` is not available the cell falls back to running one fixed example, so it still
works everywhere.
""")

co(r"""
def dashboard(ambient=41.0, rh=32, solar=880, wind=0.6, water_l=8.0, battery=61,
              packs=3, eta=14, controller="resource-aware AI"):
    "Run one emergency and show everything the bench knows about it."
    sc = make_scenario(ambient=ambient, rh=rh / 100.0, solar=solar, wind=wind,
                       water_l=water_l, battery_pct=float(battery), packs=int(packs),
                       eta=float(eta))
    picks = {"no cooling": (c_none, False), "shade only": (c_shade, False),
             "fan only": (c_fan, False), "mist only": (c_mist, False),
             "maximum fixed": (c_max, False), "rule based": (c_rules, True),
             "predictive AI": (predictive_ai, True),
             "resource-aware AI": (adaptive_ai, True)}
    ctrl, safe = picks[controller]
    df = run(ctrl, sc, safety=safe, model=forest)
    s  = score(df, sc)

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 6))
    ax = axes[0][0]
    ax.plot(df.minute, df.body, color=RED, lw=3, label="simulated body °C")
    ax.plot(df.minute, df.body_est, color=GREEN, lw=1.5, ls=":", label="what the bench believes")
    ax.axhline(WARN_TEMP, color=RED, ls="--", lw=1)
    ax.axhline(STOP_COOL, color=GREEN, ls=":", lw=1)
    ax.set_title("thermal timeline", fontsize=10); ax.legend(fontsize=7)

    ax = axes[0][1]
    ax.step(df.minute, df.mist, color=BLUE, lw=2, where="post", label="mist mL/min")
    ax.step(df.minute, df.fan * 400, color=ORANGE, lw=2, where="post", label="fan × 400")
    ax.step(df.minute, df.canopy * 450, color=GREEN, lw=2, where="post", label="canopy × 450")
    ax.set_title("what the bench is doing", fontsize=10); ax.legend(fontsize=7)

    ax = axes[1][0]
    ax.plot(df.minute, df.water_l, color=BLUE, lw=2.5, label="water, litres")
    ax.plot(df.minute, df.battery_pct / 12.5, color=ORANGE, lw=2.5, label="battery % ÷ 12.5")
    ax.plot(df.minute, df.reserve_wh / BATTERY_WH * 100 / 12.5 if "reserve_wh" in df else [],
            color=RED, lw=1, ls="--", label="radio reserve")
    ax.set_title("supplies", fontsize=10); ax.legend(fontsize=7)

    ax = axes[1][1]
    ax.step(df.minute, df.packs_active, color=PURPLE, lw=2, where="post", label="packs in use")
    ax.step(df.minute, df.packs_left, color=GREY, lw=2, where="post", label="packs still sealed")
    ax.set_title("cold packs", fontsize=10); ax.legend(fontsize=7)
    for row in axes:
        for a in row:
            a.set_xlabel("minutes")
    plt.tight_layout(); plt.show()

    water_min = ((df.water_l.iloc[-1] - 0.3) * 1000 / df.mist.iloc[-1]
                 if df.mist.iloc[-1] > 0 else float("inf"))
    print(f"controller            {controller}")
    print(f"temperature change    {s['change']:+.2f} °C   (peak {s['peak']:.2f}, "
          f"lowest {s['lowest']:.2f})")
    print(f"minutes above {WARN_TEMP} °C  {s['over_warn']}")
    print(f"water used            {s['water']:.2f} L of {water_l:.1f}")
    print(f"battery left          {s['battery_left']:.1f} %")
    print(f"cold packs used       {s['packs']} of {packs}")
    print(f"radio time left       {s['radio_min']} minutes")
    print(f"commands refused      {s['blocked']}")
    print(f"canopy                {'out' if df.canopy.iloc[-1] else 'in'}")
    print(f"water would last      {water_min:.0f} more minutes at the current mist rate"
          if np.isfinite(water_min) else "water would last      not misting")


try:
    import ipywidgets as widgets
    from IPython.display import display
    display(widgets.interactive(
        dashboard,
        ambient=widgets.FloatSlider(min=32, max=46, step=0.5, value=41, description="air °C"),
        rh=widgets.IntSlider(min=10, max=90, step=2, value=32, description="humidity %"),
        solar=widgets.IntSlider(min=200, max=1000, step=20, value=880, description="sun W/m²"),
        wind=widgets.FloatSlider(min=0.0, max=3.0, step=0.1, value=0.6, description="wind m/s"),
        water_l=widgets.FloatSlider(min=0.5, max=8.0, step=0.5, value=8.0, description="water L"),
        battery=widgets.IntSlider(min=10, max=100, step=1, value=61, description="battery %"),
        packs=widgets.IntSlider(min=0, max=3, step=1, value=3, description="cold packs"),
        eta=widgets.IntSlider(min=6, max=30, step=1, value=14, description="help in, min"),
        controller=widgets.Dropdown(options=["no cooling", "shade only", "fan only", "mist only",
                                             "maximum fixed", "rule based", "predictive AI",
                                             "resource-aware AI"],
                                    value="resource-aware AI", description="controller")))
except ImportError:
    print("ipywidgets not available - running one fixed example instead.\n")
    dashboard()
""")

md(r"""
### Things worth trying on the dashboard

1. Put the humidity to **85 %** and watch every strategy struggle. Then compare how much water
   each one spends failing.
2. Set the battery to **20 %** and switch between *maximum fixed* and *resource-aware AI*. Watch
   the radio-time line.
3. Set the wait to **30 minutes** with a **3 litre** tank. There is not enough water. What does
   the controller do with what there is?
4. Set the air to **44 °C** with **20 %** humidity and turn the mist off by choosing *fan only*.
   The fan is a heater.
5. Compare *rule based* and *resource-aware AI* on a long wait. The rule spreads the water evenly;
   the AI front-loads it.

---

## Where to take it next

- **A second casualty.** Two people, one tank. That is an allocation problem on top of the
  control problem, and it is not obvious.
- **Refill and recharge.** The bench has a solar panel. Over a long afternoon, is it worth pausing
  the fan to let the battery come back?
- **Learn the controller instead of searching.** Everything here is a one-minute search over 32
  options. Reinforcement learning would replace the search with a learned policy — and would need
  a much more careful safety story.
- **A thermal-image model.** We use one number from the thermal camera. A small convolutional
  network on the whole image could tell an occupied bench from a bag on a seat, which the load
  cell alone cannot.

> ⚠️ **A closing reminder.** Everything above is a simulation built to teach control engineering
> and resource optimisation. The temperatures are not measurements, the person is not a person,
> and nothing here may be used to make a decision about anybody's care.
""")

# ============================================================ WRITE
nb = new_notebook(cells=cells, metadata={
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11"},
    "colab": {"provenance": [], "toc_visible": True},
})
out = Path(__file__).resolve().parent / "CoolBench_Heat_Emergency_Station.ipynb"
nbf.write(nb, str(out))
print(f"wrote {out}  ({len(cells)} cells: "
      f"{sum(1 for c in cells if c.cell_type == 'markdown')} markdown, "
      f"{sum(1 for c in cells if c.cell_type == 'code')} code)")
