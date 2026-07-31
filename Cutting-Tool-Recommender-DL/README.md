# AI Cutting Tool Recommendation System — Manufacturing / Production Engineering

Ninth in the ML-vs-DL teaching series. Same five-part-per-step layout as the Smart Construction and
Building Energy notebooks. **20 steps · 9 phases · 91 cells (21 code).**

## The problem

A job card lands: Inconel 718, 5-axis centre, finishing, Ra 0.8 µm, batch of 240. Five coupled decisions
follow — **tool material · coating · coolant · cutting speed · feed rate** — and the knowledge that makes
them lives with whoever has been in the tool room longest.

| Input (job card) | Output (recommendation) | Method |
|---|---|---|
| Workpiece, machine, operation, required Ra, batch qty, nose radius, previous tool life | Tool material / coating / coolant | 3 × RandomForestClassifier |
| | Cutting speed Vc, feed f | 2 × RandomForestRegressor |
| Insert photograph (the tool history no field holds) | Wear grade + wear-land location | CNN + Grad-CAM |

## Grounded in two real machining laws

Both are used to generate the log, to check the recommendations, and to price the result — so the
notebook and the physics never disagree:

- **Taylor's tool life equation** — `V · Tⁿ = C`
- **Theoretical surface finish** — `Ra ≈ f² / (32·r)`

## Measured results (sealed jobs, 800 of 4,000)

| | |
|---|---|
| Tool material | 94.9% (baseline 41.4%) · 96.9% in top-2 |
| Coating / coolant | 94.2% / 95.8% |
| Cutting speed | MAE 19.5 m/min · R² 0.867 |
| Feed rate | MAE 0.009 mm/rev · R² 0.987 |
| Feed holds the required Ra | 100% of sealed jobs |
| Impossible combinations issued | 0 coated-PCD, 0 CBN-on-Inconel |
| CNN wear grade | 96.8%, errors at the VB 0.15 / 0.30 boundaries |

## The finding that changed the ending

The obvious business case — "the recommender extends tool life" — **does not survive the data.** It
learned from the shop's own speeds, so the best it can do is reproduce them, and because Taylor is
**convex** a symmetric error in Vc turns into a net *loss* of life. Measured: **−5.0%**.

The notebook reports that plainly and makes the cause the lesson:

- At `n = 0.28`, **+10% on cutting speed costs 29% of tool life** (HSS: 55%). That is why the setup sheet
  issues Vc as a proposal the setter trims, and why the audit reports MAE in m/min rather than only R².
- The value is instead in **not choosing the wrong tool**: on Ti / Inconel / stainless (39% of the log)
  the wrong-tool rate falls from 46.9% to 3.5%. Each avoided event is a scrapped part and lost spindle
  time.

## Four engineering judgements, not ML

1. **One-hot encoding** — numbering materials 0–6 claims Inconel and aluminium average to cast iron.
2. **Stratified split** — otherwise the rare, expensive tools vanish from the audit.
3. **Checking the combination** — three accurate classifiers can still jointly issue a coated PCD insert.
4. **Checking the feed against `Ra = f²/32r`** — average error says nothing about passing inspection.

A fifth, in the images: **bright is not worn.** Built-up edge is brighter than a genuinely worn insert
(0.103 vs 0.085 bright fraction), so every brightness threshold either scraps good inserts or misses dead
ones. That is the CNN's justification, demonstrated rather than asserted.

## Run it

Open `Cutting_Tool_Recommendation_DL.ipynb` in Colab and run all cells. Plotly charts, interactive.
TensorFlow is needed only for the CNN and Grad-CAM steps and is guarded.

Regenerate: `py -3.13 build_nb.py`

## Companion app

Not built. `APP = ""` at the top of `build_nb.py` suppresses per-step links; set it to a deployed URL and
rebuild to switch on 20 `?stage=` deep links.
