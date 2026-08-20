# AI for Transformer Hot-Spot Temperature Prediction — Electrical Power Engineering

An educational AI project that teaches **machine learning through transformer thermal condition
monitoring**, for Electrical Engineering students with little or no AI background. Every AI concept appears
because a real power-systems problem required it — not because it is on a syllabus.

## Two independent deliverables

| | Deliverable | Teaches | Entry point |
|---|---|---|---|
| 📓 | **Colab notebook** | **Implementation** — runnable code, 10 phases, 44 code cells | `Transformer_HotSpot_Temperature_AI.ipynb` |
| 🖥️ | **Streamlit application** | **Conceptual understanding** — 10 interactive pages | `streamlit run app.py` |

They tell the same educational story and are **completely independent**: the app imports nothing from the
notebook and reads none of its files. Both reproduce the same IEEE C57.91 engineering from scratch, which
is why their numbers agree — the baseline (3.18 °C), the best model (1.35 °C), the 58 % headline, the
error bands, the ageing concentration and the hold-out biases are all identical.

Two deliberate differences, both so the app stays inside a 1 GB Streamlit Cloud container:

- The app's Random Forest uses **150 trees with `min_samples_leaf=4`** against the notebook's 300 and 2.
  That reads **1.55 °C** instead of 1.53 °C, and cuts the fitted forest from 207 MB to 72 MB.
- The app substitutes `HistGradientBoostingRegressor` for the notebook's `GradientBoostingRegressor`.
  Same algorithm, binned — it lands at 1.347 °C against the notebook's 1.348 °C.

Both deliverables are **ten phases, one per stage of a real machine-learning project**, and the app
gives each phase exactly one page. Every phase ends with a question and the next opens by answering it, so
the course reads as one argument rather than ten topics. Sub-topics sit behind tabs in the app and behind
short step headings in the notebook.

The writing rule is that a non-electrical reader has to be able to follow it: every piece of jargon is
glossed where it first appears, and page length is budgeted (`text_budget.py`) rather than left to taste.

## The problem

A power transformer converts voltage, not power — everything it fails to pass on becomes heat. The heat is
not the problem; **time spent hot** is. Insulating paper degrades chemically at a rate that roughly
**doubles every 6 °C**, cumulatively and irreversibly, with nothing visible until the unit fails.

The temperature that governs this is the **winding hot spot**, typically **25–30 °C above** the top-oil
temperature on the dial thermometer. **Almost no transformer in service measures it** — direct measurement
needs a fibre-optic probe installed between the winding discs at manufacture.

So the industry estimates it from IEEE C57.91 using nameplate values, which assume clean radiators, oil in
its original condition, an instantaneous thermometer, and a hot-spot factor measured in a factory test
years ago.

| Stream | Role | Method |
|---|---|---|
| Load current, ambient, top oil, voltage, humidity, fan stage, age | Predict the hot spot | **Regression** |
| → IEEE C57.91 with nameplate values | The baseline to beat | closed form, nothing fitted |
| → the same five sensors, fitted | Learn this fleet | Linear regression |
| → plus `K^1.6`, oil rise, rolling load | Physics as columns | feature engineering |
| → curvature and cooling-stage interaction | Models that bend | Random Forest / Gradient Boosting / XGBoost |
| → which instruments earn their place | Sensor justification | importance + instrument-level refitting |
| → error where the consequence is | Segmented evaluation | error by temperature band, converted to ageing |
| → where it stops working | Generalisation | hold out an entire transformer |
| All of it | One recommendation per unit | IEEE limits + hand-written engineering rules |

## The central promise

> **Machine Learning learns the relationship between transformer operating conditions and hot-spot
> temperature, so engineers can predict overheating before it happens and protect the asset.**

The notebook never simply states this. It is set up in phase 1, **measured against the industry-standard
thermal model** at the leaderboard (step 20), and its **limit is measured** at step 27.

## The headline result

Every model scored on the same held-out quarter of the year (whole weeks, every fourth one):

| Model | MAE | RMSE | R² |
|---|---|---|---|
| IEEE C57.91, nameplate, nothing fitted | 3.18 °C | 4.06 | 0.946 |
| Linear regression, 5 raw sensors | 2.41 °C | 3.04 | 0.970 |
| Linear regression, engineered columns | 2.01 °C | 2.52 | 0.979 |
| Random Forest, 300 trees | 1.53 °C | 1.92 | 0.988 |
| Gradient Boosting, 300 trees | 1.35 °C | 1.69 | 0.991 |
| XGBoost, 600 trees | 1.35 °C | 1.69 | 0.991 |

**A 58 % reduction in mean error against the thermal model the industry currently uses.** The three levers —
fitting to this fleet at all, engineering the features, and changing the algorithm — contribute 0.77, 0.41
and 0.66 °C. None of them dominates.

## The learning journey

Ten phases, one substation, one year. Each row's question is answered by the row below it.

| # | Phase | Ends by asking |
|---|---|---|
| 1 | The Problem | If we cannot measure the hot spot, what *can* we measure? |
| 2 | The Data | What does a whole year of these readings look like? |
| 3 | Exploring The Data (EDA) | Some readings are impossible. How do we make the data fit to learn from? |
| 4 | Preparing The Data | How do we know a model learned rather than memorised? |
| 5 | How Learning Works | What is the simplest model that could work? |
| 6 | The First Model | The relationship curves. What can follow it? |
| 7 | Training A Model | Three models. How do we say which is best? |
| 8 | Scoring It | The average is good — but is it good *where it matters*? |
| 9 | Where It Fails | Knowing that, how should an engineer use it? |
| 10 | Using It | — |

Phases 3, 4, 5, 7 and 8 carry the beginner material the original build assumed you already had: EDA,
cleaning, **encoding** (one-hot for names, integers for ordered categories, and why numbering categories
is wrong), standardisation, a glossary of the six ML words before anything uses them, the justification for
the chosen model, and what each evaluation metric means with the case for MAE here.

## Five places the engineering discipline shows, not the ML

Each is verified in the notebook output:

1. **Choosing the target.** Predicting top oil would have been easy and useless — it is already measured.
   The hot spot is worth predicting precisely because it is not.
2. **Deleting the de-energised hours** rather than repairing them. A cooling transformer obeys different
   physics from a loaded one; keeping those rows teaches the model that low current means winding-at-ambient.
3. **Comparing against IEEE C57.91, not against zero.** A model that cannot beat the closed-form standard is
   not worth deploying whatever its R² looks like in isolation.
4. **Scoring the hot band separately.** The overall 1.35 °C is dominated by hours where accuracy is
   irrelevant. In the 110 °C+ band the error is 2.1 °C and **biased low** — and the hottest 5 % of hours
   carry **71 %** of the year's insulation ageing.
5. **Measuring the limit rather than asserting it.** Holding out an entire transformer raises MAE to
   2.4–5.6 °C, almost all of it a **constant offset** — the per-unit hot-spot factor the model could not
   learn from its siblings.

## Two more findings worth teaching

- **Feature importance disagrees between models and hides redundancy.** XGBoost ranks `cooling_stage`
  first, the Random Forest ranks `load_roll3` first, and dropping *any* single column barely moves the
  error because the thirteen columns encode the same physics several times over. The test that means
  something is dropping a whole **instrument**: humidity +0.013 °C, voltage +0.006 °C, top-oil thermometer
  +0.260 °C, current transformer **+1.001 °C**.
- **R² is a property of the test set as much as of the model.** Swap the seasonal split for an
  October–December holdout and R² falls 0.991 → 0.978 while MAE moves 1.35 → 1.37 °C. The test set's
  standard deviation fell from 17.4 °C to 11.5 °C; that is the entire explanation.

## The engineering, and where it comes from

Real and standards-based. The same equations generate the substation log **and** check the model, so the
notebook and the standard never disagree:

- **IEEE C57.91 clause 7** — top-oil rise `Δθ_oil,r · ((K²R + 1)/(R + 1))^n` and winding gradient
  `Δθ_hs,r · K^(2m)`, with `R = 6`, `n = 0.9`, `m = 0.8`.
- **IEEE C57.91 clause 5** — ageing acceleration `F_AA = exp(15000/383 − 15000/(θ_h + 273))`.
- **IEEE C57.91 table 8** — hot-spot limits 110 / 120 / 140 °C, used as the recommendation thresholds.

The simulated fleet is four 40 MVA 132/33 kV ONAN/ONAF units aged 3, 9, 16 and 22 years, hourly for one
year (35,040 readings). Each unit carries its own hot-spot factor, radiator fouling grows with age, the oil
has a three-hour time constant and the thermometer pocket adds more lag — which is exactly what the
nameplate model cannot see and the fitted model can.

## The Streamlit application

11 pages: a landing page plus one per phase, routed by `?stage=<id>` so every page is linkable. The
old 30-step ids are aliased onto the ten pages, so links written against the previous version still land
somewhere sensible.

**The landing page** has the four sections the brief asks for — the engineering problem (with the
interactive cutaway), the project goal, a **clickable mind map** that opens any page, and the
Electrical-Engineering → AI mapping.

**Every learning page** is the same five parts: `01 Electrical Engineering` → `02 The Challenge` →
`03 AI Connection` (with an animated substation → busbar → AI bridge figure) → `04 Technical Idea` (the
interactive renderer) → `05 Key Takeaway` + `06 In the Notebook`, then a phase rail and prev/next
navigation.

Visuals built for this app:

- **An interactive transformer cutaway** — tank, core, LV/HV windings with discs, stratified oil shading,
  radiator banks that light up with the fan stage, bushings, and a hot-spot marker that changes colour with
  temperature. Reused on four pages, driven by live sliders.
- **A heat-flow animation** — a packet travelling winding → oil → radiator → ambient air.
- **A live hot-spot gauge** with the IEEE C57.91 bands drawn on the dial.
- Plotly temperature trends, prediction-vs-measured scatter, feature-importance comparison, the ageing
  concentration curve, the loading chart, and a four-unit fleet dashboard with a gauge per transformer.

| File | What it is |
|---|---|
| `app.py` | Router, landing page, and one renderer per stage |
| `bridge.py` | The `STEPS` registry (10 entries) + the page scaffold, question chain, mind map and mapping figure |
| `story.py` | The substation: physics, data, models, decision rules. **Every number the app prints comes from here** |
| `prep_artifacts.py` | Builds `artifacts/` — the precomputed data and model results the app loads |
| `artifacts/` | 15 files, 4.9 MB. Committed, and regenerated by the script above |
| `.streamlit/config.toml`, `requirements.txt` | Dark theme, and the deploy manifest |

**Content edits go in `bridge.STEPS`** — `app.py` needs no changes. Colour is a teaching device and must
never vary: amber is the substation, cyan is the AI, violet is the technical process.

Run with `streamlit run app.py`.

### Why the app loads instead of fits

Streamlit Community Cloud gives this app a fraction of one CPU and sleeps the container when nobody is
using it, so *every* wake-up used to re-simulate the year and refit thirteen models. That is what got the
app CPU-throttled on 2026-08-20.

`prep_artifacts.py` now does that work once, offline, into `artifacts/`. Cold start on the landing page
went from **13.9 s to 0.8 s**, and the worst page (`unseen-unit`, which trains four models) from **23.4 s
to 0.7 s** — measured on a full-speed CPU, so the throttled container saves considerably more.

Two rules for working on this app:

- **Anything that changes a number means rebuilding.** Touch the physics, the simulation, the features or
  a model hyper-parameter and you must re-run `python -X utf8 prep_artifacts.py` and commit `artifacts/`,
  or the app keeps showing the old numbers. `verify_artifacts.py` is what catches you forgetting.
- **The fitted Random Forest is never shipped** — it pickles to 72 MB. Only the four things the forest page
  reads off it are precomputed: the first tree's split chain, the tree count, the mean depth, and test MAE
  against the number of trees averaged. The one model that *is* shipped is the best one
  (`best_model.ubj`, 2.6 MB), because four pages predict from live slider values.

Every loader falls back to computing from scratch when `artifacts/` is absent, so a fresh clone runs with
no build step, and deleting the folder restores the original behaviour exactly.

## Files

| File | What it is |
|---|---|
| `build_nb.py` | The notebook generator. **Edit the `STEPS` registry here, never the `.ipynb`.** |
| `Transformer_HotSpot_Temperature_AI.ipynb` | The notebook — 107 cells, 44 code, 34 steps, 10 phases |
| `substation_thermal_log.csv` | Written by the notebook when it runs; a reference copy is kept here |
| `app.py`, `bridge.py`, `story.py` | The Streamlit application |
| `prep_artifacts.py`, `artifacts/` | The offline build and its output |
| `verify_artifacts.py` | Refits everything live and asserts it matches `artifacts/` |
| `smoke_pages.py` | Renders all 11 stages through `AppTest` |
| `text_budget.py` | Counts the words on every page, so "too long" stays a number |
| `run_notebook.py` | Executes all 44 notebook code cells in one namespace |

Rebuild the notebook with `py -3.13 build_nb.py`.

## Verify after any edit

**The notebook.** Every number in the markdown is quoted from the executed output, so a cell that merely
*runs* can still be wrong. After changing `build_nb.py`:

1. Rebuild, then `ast.parse` every code cell (catches broken string literals).
2. Execute every code cell in one namespace with `go.Figure.show` / `pio.show` monkeypatched to no-ops.
3. Read the printed values against every number asserted in the surrounding markdown.

**The app.** Two scripts, both of which must pass:

```
python -X utf8 verify_artifacts.py   # 24 checks: artifacts == live computation
python -X utf8 smoke_pages.py        # all 11 stages render without an exception
python -X utf8 text_budget.py        # no page is a wall of text
python -X utf8 run_notebook.py       # every notebook code cell still runs
```

`verify_artifacts.py` refits every model from scratch and compares the result against what `artifacts/`
returns, to 1e-9. It is the guard against a stale build: change the physics without rebuilding and it
fails. `smoke_pages.py` loops `AppTest` over `["start"] + bridge.ORDER` and asserts `not at.exception`,
which catches a render error that no numeric check would see.

Requires `numpy pandas scikit-learn plotly xgboost ipywidgets nbformat streamlit` on **Python 3.13**
(streamlit does not install on 3.14). The notebook's Gradient Boosting cell takes 30–60 seconds; everything
else is fast.

## Deep links between the two deliverables

`APP = ""` at the top of `build_nb.py` suppresses the per-step links. Set it to the deployed Streamlit URL
and rebuild to switch on 30 `?stage=` deep links from the notebook into the app — the step ids in
`build_nb.STEPS` and `bridge.STEPS` are identical and already match.
