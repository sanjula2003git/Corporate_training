# AI for Building Energy Optimization — Mechanical / Civil / Building Engineering

An educational AI project that teaches **AI through the energy and comfort performance of a commercial
building**, for Mechanical, Civil and Building Services students with little or no AI background. Every AI
concept appears because a real building-services problem required it — not because it is on a syllabus.

Structurally this follows the **Smart Construction** notebook: one intro block (problem → what we build →
workflow → Engineering-to-AI map), then 30 steps, each written as the same five parts.

## The problem

It is 07:15. The AHU and chiller started at 07:00, as they have since commissioning: 23 °C setpoint,
fresh-air damper at its design position, ventilating for two hundred people. **Eleven people are in the
building.** By 09:30 there will be two hundred and the plant will be exactly right; at 17:30 the floor
empties and it will be wrong again. HVAC is the largest electrical load in the building, and one
facilities manager is responsible for every zone, every fifteen minutes.

| Stream | Role | Method |
|---|---|---|
| Indoor/outdoor temp, humidity, CO₂, occupancy, solar, PM2.5, setpoint, hour | Read the conditions | **ML** |
| → predict HVAC load and whole-building load | Energy forecasting | Linear / Random Forest / Gradient Boosting |
| → flag an over-conditioned interval | kW per person above the limit | RandomForestClassifier |
| → rank the drivers | What to change first | Feature importance |
| → forecast tomorrow's profile and peak | Demand-charge management | the same regression, run forward |
| → choose the setpoint | Energy subject to PPD ≤ 10% | constrained sweep |
| Ceiling thermal camera → grade the floor plate | empty / occupied / crowded | **CNN** |
| Ceiling thermal camera → locate the use | Which zone, with the evidence | **CNN + Grad-CAM** |
| All of it | One ranked action per zone | **AI fusion** |

## The central promise

> **Machine Learning predicts building energy demand from environmental and occupancy data.
> Deep Learning understands occupancy and thermal images to detect how spaces are actually being used,
> enabling smarter HVAC control.**

The notebook never simply states this. It is set up in phase 2, hit head-on at the image wall (phase 6),
and **measured** at the verdict step (step 25).

## The learning journey

12 phases · 30 steps · one building, one cooling season:

the building in use → one 15-minute interval → the BMS export → cleaning and preparing →
an ML baseline (cooling demand from the gauges) → the thermal frame the gauges cannot describe →
how a machine learns (neuron → activation → loop → gradient descent → network → training) →
a CNN reads the floor plate → Grad-CAM locates the use → the energy audit → forecasting, setpoint
optimisation and fusion → the business case.

Each step: **Part 1 in the building → Part 2 the engineering challenge → Part 3 where the AI comes in
(with the Engineering↔AI bridge table) → Part 4 the technical explanation (runnable code) → Part 5 what
you just built + a one-line key takeaway.**

## Four places the engineering discipline shows, not the ML

These are the moments worth teaching, and each is verified in the notebook output:

1. **Split by day, not by row.** Adjacent 15-minute intervals are nearly the same building. The shuffled
   split reports a *better* R² and is wrong; the notebook trains both and prints the two numbers.
2. **Drop a constant column** instead of cleaning it. `is_workday` has one unique value once the schedule
   filter is applied.
3. **Comfort is a constraint, not an objective.** The optimiser takes the highest setpoint satisfying
   PPD ≤ 10% (ISO 7730), and the dashboard recomputes comfort under the proposed control rather than
   asserting it.
4. **The business case is a counterfactual** — the recorded season re-run under the proposed control —
   not a percentage from a brochure.

## The synthetic building data

Sixteen weeks of 15-minute intervals generated from a stated plant model: envelope conduction, solar gain,
internal gains, dehumidification and ventilation load; VAV fan power on the affinity law; chiller COP that
degrades as it rejects heat to a hotter outdoors. **The same functions drive the dataset, the optimiser
and the business case**, so they always agree. The export carries the faults a real trend log carries —
dropouts, a dead CO₂ sensor at 0 ppm, a failed thermistor at 85 °C, a stuck RH channel, a people-counter
rollover, and resync duplicates.

The key modelling choice: the baseline has a **fixed outside-air damper** ventilating for 200 people
whatever the floor is doing. That is what makes demand-controlled ventilation the largest single saving in
the notebook, and it is the reason the CO₂ sensor matters more than the clock.

Thermal frames are synthetic numpy grids. Head count is drawn from a **continuum** (0–40) with the class
boundaries cutting across it, so `occupied` vs `crowded` is genuinely ambiguous near 19 people — the CNN's
errors land there, as they should. Two decoys — sun on the façade and a leaking wall — are arranged so
that **no threshold on mean temperature can work**: `solar` reads warmer than a floor with twelve people
on it, and `heat_leak` sits next to `occupied`.

## Run it

Open `Building_Energy_Optimization_DL.ipynb` in Google Colab and run all cells. Charts are Plotly, so
they are interactive. TensorFlow is needed only for the CNN and Grad-CAM steps; those cells detect whether
it is present and skip cleanly if not, so every other cell runs anywhere.

Regenerate after editing the builder:

```bash
py -3.13 build_nb.py
```

## Measured results

Everything below is printed by the notebook itself, on **sealed days the models never saw**:

| | |
|---|---|
| HVAC load, Random Forest | MAE 2.3 kW · RMSE 3.6 kW · R² 0.954 (mean load 41 kW) |
| Whole-building load | R² 0.967 |
| Day split vs shuffled split | R² 0.954 vs 0.962 — the shuffled one is the lie |
| Over-conditioned classifier | 96% accuracy, ~80% recall — against a 86% "never wasteful" baseline |
| CNN, 3 classes | ~92% accuracy; `empty` perfect; errors cluster at the 19-person boundary |
| Peak forecast, 12 sealed days | MAE ~2.0 kW |
| Counterfactual HVAC saving | ~17%, comfort maintained at 100% of occupied intervals, peak 107 → 99 kW |

## Companion Streamlit app

Not built. The notebook is written so the app can be added without rework: set `APP` at the top of
`build_nb.py` to the deployed URL and rebuild, and every step gains a "see it illustrated" link plus a
link column in the workflow table. With `APP = ""` (the current setting) no links are emitted at all,
rather than dead ones.
