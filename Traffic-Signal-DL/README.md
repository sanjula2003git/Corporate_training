# AI for Traffic Signal Optimization — Smart City Engineering

An educational AI project that teaches **AI through the signal timing of a city intersection**, for civil,
transport and smart-city engineering students with little or no AI background. Every AI concept appears
because a real traffic problem required it — not because it is on a syllabus.

It is the smart-city sibling of the Smart Construction, Predictive Maintenance, CNC Machining, Bridge
Digital Twin and Sustainable Manufacturing projects: same educational philosophy, same five-part page
structure, redesigned end to end for a signalised junction.

## The problem

A four-approach junction runs a **fixed-time plan**: the same cycle length and the same green split, every
cycle, all day. The traffic is not fixed. Demand on the main street peaks sharply in the evening; the cross
street peaks earlier and flatter; at 03:00 both nearly vanish. One plan cannot be right twice — it is too
long at night and too short at the peak, in opposite directions at the same time.

| Stream | Role | Model |
|---|---|---|
| Loops, radar, weather station, push-buttons (9 channels) | Read the cycle | **ML** |
| → predict queue length and average delay | Condition prediction | RandomForestRegressor |
| → flag a congested cycle | Level-of-service classification | RandomForestClassifier / MLP |
| → score the unexplained queue | Incident detection | LinearRegression + residual in σ |
| CCTV → grade the approach | Congestion detection | **CNN** |
| CCTV → locate the queue | "Which lanes get the green?" | **CNN + Grad-CAM** |
| CCTV → spot an ambulance | Signal preemption | **CNN** (same architecture, new label) |
| → choose cycle length and green split | Constrained optimisation | delay sweep + Webster's `C_opt` |

## The learning journey (24 sections, one traffic-management programme)

The junction at peak → one signal cycle → where the sensors sit → cleaning and preparing the log → an ML
baseline (queue and delay from the readings) → **the wall** (the CCTV frame the readings cannot describe) →
how a machine learns (neuron → activation → gradient descent → network → training) → a CNN reads the
approach → Grad-CAM locates the queue → the same network finds the ambulance → the traffic audit → the
measured ML-vs-DL verdict → incident detection → **the best cycle length** → **adaptive vs fixed-time,
simulated** → fusion → the business case.

Each page: **traffic activity → engineering challenge → AI connection → technical concept → notebook
connection.**

## The central promise

> **Machine Learning predicts traffic conditions from numerical detector data.
> Deep Learning understands live road images and finds vehicles and congestion that
> feature engineering cannot reliably capture.**

Section 18 measures it rather than asserting it.

## The synthetic traffic data

Every cycle is generated in-code from standard traffic engineering, so the numbers survive inspection by a
transport engineer:

- **Capacity** from saturation flow (1900 veh/h/lane), the green ratio, heavy-vehicle and rain adjustment
  factors.
- **Control delay** from the HCM uniform + incremental (overflow) delay formulation.
- **Back of queue** from the uniform queue accumulated over the red.
- **Optimal cycle** by sweeping the delay curve, cross-checked against Webster's `C_opt = (1.5L + 5)/(1 − Y)`.

The CCTV frames are engineered so that **no mean-brightness threshold can separate congested from clear** —
the two congested scenes sit between a dark clear scene (night) and two bright ones (daylight, wet glare).
That is what makes the wall in Section 9 a demonstration rather than an assertion.

## Honest numbers

The adaptive controller in Section 21 is measured against the **best possible single fixed plan**, found by
exhaustive search over every cycle length and split. It wins by ~29% in vehicle-hours of delay. The notebook
says plainly that this is an isolated junction against a single fixed plan, and that published SCOOT/SCATS
results against properly timed networks are nearer 10–20%.

## Files

| File | Purpose |
|---|---|
| `build_nb.py` | Generates the notebook from nbformat cells. Run `py -3.13 build_nb.py`. |
| `Traffic_Signal_Optimization_DL.ipynb` | The runnable Colab notebook (67 cells, 29 code). |

Editing note: inside `co(...)` code cells use only single-line `"..."` docstrings or `#` comments — a
triple-quoted docstring would close the generator's own `r"""` string.

## Placeholders to fill in

Both live at the top of `build_nb.py`; rebuild after changing them.

```python
APP   = "https://REPLACE-ME.streamlit.app"          # the illustration app, once deployed
COLAB = "https://colab.research.google.com/REPLACE-ME"   # this notebook, once pushed
```

`APP` drives all 30-odd "See it illustrated" deep links (`{APP}/?stage=<stage>`). `COLAB` drives the
Open-in-Colab badge in the title cell.

## Running the notebook

Colab has everything preinstalled. Elsewhere:

```
pip install numpy pandas scikit-learn tensorflow matplotlib
```

TensorFlow is optional — the notebook detects it and skips the three CNN sections gracefully, so every
non-CNN cell runs anywhere.
