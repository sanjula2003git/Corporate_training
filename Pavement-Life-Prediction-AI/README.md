# 🛣️ AI for Pavement Remaining Service Life Prediction

Machine Learning for Highway and Pavement Engineers — predicting how many years of service life a pavement
segment has left, and turning that number into a maintenance programme.

**Two independent deliverables, one story.**

| | Deliverable | Teaches | Run it |
|---|---|---|---|
| 📓 | `Pavement_Remaining_Life_AI.ipynb` | **implementation** — runnable code, real data work | open in Colab, Runtime → Run all |
| 🖥️ | `app.py` + `bridge.py` | **understanding** — diagrams, animations, interactive dashboards | `streamlit run app.py` |

They are **not** connected programmatically. The app never reads the notebook's CSV; it regenerates the
survey in-app from the same published relationships, so the two always agree without being coupled.

## The problem

A state highway agency maintains ~1,500 pavement segments and can treat about 7% of the network a year.
Traditional practice resurfaces on a fixed cycle, which ignores traffic, structure and climate entirely.
Repair too early and paid-for service life is milled off; too late and an overlay becomes a
reconstruction.

**The one idea the notebook proves:** Machine Learning learns the relationships between pavement
condition, traffic and environmental factors to predict remaining service life — helping engineers plan
maintenance at the right time. It is audited on roads the model has never seen, then priced.

## Structure

23 steps across 10 phases. Every step follows the same five-part page:

| Part | Heading |
|---|---|
| 1 | On the network — the highway engineering activity |
| 2 | The engineering challenge — why it is hard by hand |
| 3 | Where the AI comes in — the civil → AI mapping table |
| 4 | The technical explanation — runnable code and Plotly charts |
| 5 | What you just built + a one-line key takeaway |

Phases: The Road Network → How Pavements Fail → The Condition Survey → The Survey Export → Preparing The
Data → Learning Deterioration → Reading The Model → The Prediction → The Pavement Audit → Maintenance
Planning.

## Engineering basis

The survey data is generated from published relationships, and the same relationships check the model, so
the notebook and the design standards never disagree:

- **AASHTO 1993 flexible pavement design equation** — allowable ESALs from the structural number `SN` and
  the subgrade resilient modulus `MR`
- **AASHO Road Test fourth-power law** — damage of one axle = `(P / 80 kN)⁴`
- **Miner's linear cumulative damage** — consumed life = applied ESALs ÷ allowable ESALs

Deterioration runs on **two clocks** — a load clock and a climate clock — and a segment fails on whichever
expires first. Cracking is split into load-associated *fatigue* cracking and non-structural *thermal*
block cracking, so the model has to use traffic, structure and climate to tell them apart.

## Model

| | |
|---|---|
| **Inputs** | traffic volume (vpd), pavement thickness (mm), age (years), rainfall (mm/yr), temperature (°C), crack density (%) |
| **Output** | remaining service life, in years (regression) |
| **Models** | Linear Regression · Random Forest · Gradient Boosting · XGBoost |
| **Baseline** | the agency's fixed 20-year cycle, with and without a cracking trigger |
| **Split** | `GroupShuffleSplit` by `road_id` — adjacent kilometres are near-duplicates |

Held-out results (45 unseen roads, 435 segments): the fixed cycle is wrong by **2.98 years** MAE; the best
model by **1.49 years** (R² 0.906). The notebook also measures how much a random-row split would have
flattered the same model.

## The Streamlit app

24 pages — the landing page plus one per step, at `?stage=<id>`. Every learning page follows the same
five-part structure, so the Civil Engineering always comes before the AI:

**Civil Engineering → The Challenge → AI Connection (+ the bridge figure) → Technical Idea (interactive)
→ Key Takeaway → In the Notebook**, then a check-your-understanding question and a phase progress rail.

The landing page has the four required sections: the engineering problem, the project goal, a **clickable
mind map** (every hexagon opens that page), and the full **Engineering → AI mapping**.

Interactive pieces include a pavement cross-section you build layer by layer, animated serviceability
decay, a fourth-power damage explorer, a remaining-life gauge, permutation-importance and tornado charts,
a maintenance timeline, and a network programme dashboard.

Colour is a teaching device and never varies: **amber = the highway world, cyan = the AI world, violet =
the technical process.**

```
pip install -r requirements.txt
streamlit run app.py
```

Content edits go in `bridge.STEPS` — `app.py` needs no changes.

## Files

| File | What it is |
|---|---|
| `Pavement_Remaining_Life_AI.ipynb` | the notebook — open in Colab, Runtime → Run all |
| `build_nb.py` | generates the notebook from an editable `STEPS` registry |
| `app.py` | the Streamlit app: physics, cached data/models, 23 stage renderers, router |
| `bridge.py` | the step registry, the five-part scaffold, mind map, mapping figure, quizzes |
| `requirements.txt` | app dependencies |
| `pavement_condition_survey.csv` | written by the notebook on first run; not checked in |

## Running the notebook

Colab has everything preinstalled. Locally:

```
pip install numpy pandas scikit-learn plotly xgboost ipywidgets nbformat
```

`xgboost` and `ipywidgets` are optional — both are guarded and the notebook falls back cleanly.

## One caveat worth teaching, in both deliverables

Crack density is a **consequence** of thickness, traffic, age and climate — not an independent input. Move
the thickness slider while holding cracking fixed and the thicker pavement looks no better, or worse. That
is not a bug: a 300 mm section already showing 18% cracking is in more trouble than a 150 mm section
showing the same. Both deliverables show the comparison done properly, with cracking allowed to follow the
physics, and name the mistake (**conditioning on a mediator**).

## Three questions it refuses to skip

1. **Where do the labels come from?** The works file — the year each segment actually reached terminal
   condition — not the formula that produced the features.
2. **How do you split the data?** By road, never by row, and the cost of getting that wrong is measured.
3. **Is R² the right score?** No. Arriving late costs about 9.5× more per year than arriving early, so
   accuracy is replaced with rupees.
