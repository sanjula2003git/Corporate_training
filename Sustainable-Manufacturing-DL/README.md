# AI for Sustainable Manufacturing — Mechanical / Manufacturing Engineering

An educational AI project that teaches **AI through the energy and carbon performance of a production
plant**, for Mechanical and Manufacturing Engineering students with little or no AI background. Every AI
concept appears because a real plant problem required it — not because it is on a syllabus.

It is the manufacturing-sustainability sibling of the Smart Construction DL, Predictive Maintenance DL,
CNC Machining DL and Bridge Digital Twin DL projects: same educational philosophy, architecture,
navigation and five-part page structure — redesigned end to end for a sustainability problem.

## The problem

A plant runs **three shifts**. Compressors, motors, ovens, pumps and ventilation draw power around the
clock, and every kilowatt-hour carries a carbon figure. Waste is ordinary and real: compressed-air leaks,
heat loss through failed lagging, machines idling between jobs, scrap material, badly scheduled high-draw
processes. But consumption is **continuous** and review is **monthly** — the bill arrives long after the
waste happened. Instrument the plant, and learn to **predict, explain and reduce** its energy and carbon
without losing output.

| Stream | Role | Model |
|---|---|---|
| Load, motor temp, air pressure, air flow, idle share, units, material, ambient | Read the process | **ML** |
| → predict the hour's kWh and kg CO₂ | Sustainability metrics | RandomForestRegressor |
| → flag a wasteful hour (kWh per unit above the limit) | Waste classification | RandomForest / MLP |
| → rank the drivers | What to fix first | Feature importance |
| → learn normal-for-the-conditions, score the residual | Anomaly detection | regression + residual |
| → sweep the operating range, minimise kWh per unit | Efficient operating point | model sweep |
| Thermal camera → grade a frame (leak / hotspot / lagging / sound) | Visual loss detection | **CNN** |
| Thermal camera → locate the loss, show where it looked | Location + "show me why" | **CNN + Grad-CAM** |
| Energy + CO₂ + anomaly + thermal grade | One prioritised action | **AI fusion** |

## The central promise

> **Machine Learning predicts sustainability metrics from sensor measurements.
> Deep Learning discovers hidden patterns in images that feature engineering cannot easily capture.**

The course never simply states this. It is set up in phase 2, hit head-on at the thermal-image wall
(phase 6), and **measured** at the verdict page (phase 10).

## The learning journey (one sustainability programme)

The plant in production → one production hour → instrumenting the plant → cleaning & preparing the data →
an ML baseline (energy and carbon from the readings) → the thermal frame the readings cannot describe →
how a machine learns (neuron → activation → gradient descent → network → training) → a CNN reads the heat
pattern → a CNN locates the loss (Grad-CAM) → the sustainability audit → **prediction & optimisation
(anomaly detection + the efficient operating point)** → fusion → the business case.

**12 phases · 30 steps.** Each page: **manufacturing activity → engineering challenge → AI concept →
technical illustration → key takeaway → notebook connection**, and ends with a multiple-choice check.

## The synthetic plant data

Every production hour is generated in-code from an approximate plant energy model — baseload is paid
whatever you make, useful work rises with load, and losses grow faster than output at high load; a hidden
waste level (leaks, failed lagging) raises air flow and motor temperature while dropping line pressure.
The **same** functions drive the dataset, the trained models and the "try an hour" tools, so they always
agree. No external dataset required. The thermal frames are synthetic numpy grids rendered as heatmaps —
no image assets and no deep-learning framework at app runtime.

The frames are deliberately arranged so that **no threshold on mean temperature can work**: the air leak
is *colder* than sound equipment, and failed lagging sits on top of harmless sunlight. That is the proof
the CNN is needed, not an assertion.

## Two independent deliverables

| | Teaches | Runs |
|---|---|---|
| `Sustainable_Manufacturing_DL.ipynb` | **implementation** — runnable code, real models, measured results | Google Colab |
| `app.py` (Streamlit) | **understanding** — interactive diagrams, animations, mind map | Streamlit |

They tell the same story and share no code. The notebook links out to the app with `?stage=<id>`; nothing
is connected programmatically.

## Run the Streamlit app

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501. Use the sidebar or the clickable mind map on the landing page to move
through the 30 stages. Every stage is also directly addressable: `?stage=optimize`, `?stage=anomaly`, …

## Run the notebook

Open `Sustainable_Manufacturing_DL.ipynb` in Google Colab and run all cells. TensorFlow/Keras is used for
the CNN and Grad-CAM; the notebook detects whether it is present and **skips those cells cleanly** if not,
so every other cell runs anywhere.

Regenerate the notebook after editing the builder:

```bash
py -3.13 build_nb.py
```

## Files

| File | What it holds |
|---|---|
| `bridge.py` | The Manufacturing→AI scaffold: `PHASES`, `STEPS` (all prose), `QUIZ`, the mind map, the mapping figure, the landing page. **Content edits go here.** |
| `story.py` | The 14 narrative renderers + the synthetic thermal frames |
| `app.py` | The plant energy model, the data, the 16 technical renderers, and the router |
| `build_nb.py` | Builds the Colab notebook (standalone — imports none of the above) |

## Design principles

- Concise, professional engineering language — no dramatic storytelling, no motivational language.
- Every page **begins with manufacturing engineering**, never with AI.
- The engineer stays in charge; AI eases the continuous watch one person cannot keep across three shifts.
  Never framed as replacing anyone — the goal is **Manufacturing Engineer + AI**.
- Colour is a teaching device: **amber = the plant**, **cyan = the AI**, **violet = the technical
  process** — consistently, on every page.
- The business case is arithmetic on assumptions the student sets, never a measurement, and the "after"
  bar never reaches zero.

## Deploy (to get a public link)

1. Push this folder to a GitHub repo.
2. On [share.streamlit.io](https://share.streamlit.io), create an app pointing at the repo, main file
   `Sustainable-Manufacturing-DL/app.py`.
3. Deploy. You get a URL like `https://<name>.streamlit.app`.
4. Set `APP` at the top of `build_nb.py` to that URL and re-run `py -3.13 build_nb.py` — all 31 notebook
   deep links follow it.
