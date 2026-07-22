# AI-Based Bridge Digital Twin — Structural / Civil Engineering

An educational AI project that teaches **AI through structural health monitoring (SHM)**, for Civil /
Structural Engineering students with little or no AI background. Every AI concept appears because a real
bridge problem required it — not because it is on a syllabus.

It is the structural twin of the Smart Construction DL, Predictive Maintenance DL and CNC Machining DL
projects: same educational philosophy, architecture, navigation, and five-part page structure —
redesigned end to end for a bridge digital twin.

## The problem

A highway bridge deteriorates **continuously** — every crossing, every frost, every gram of de-icing
salt — but is inspected by eye once every **one or two years**. Damage that appears the day after a
visit can hide for a year. Instrument the bridge, and learn to **estimate and forecast** its condition
so maintenance is planned before the damage is visible.

| Stream | Role | Model |
|---|---|---|
| Frequency, strain, vibration, tilt, crack width, corrosion, temperature, load | Read the structure | **ML** |
| → estimate the condition rating from the readings | Condition assessment | RandomForestRegressor |
| → forecast the Remaining Useful Life (RUL) | Degradation trend | trend fit + extrapolation |
| → learn normal-for-the-weather, flag the deviation | Anomaly detection | residual model |
| Drone camera → grade a crack image | Visual defect grading | **CNN** |
| Drone camera → locate the crack, show where it looked | Defect location + "show me where" | **CNN + Grad-CAM** |
| Condition + crack + anomaly + RUL | One prioritized alert | **AI fusion** |

## The learning journey (one SHM programme)

The bridge in service → one sensor sweep → instrumenting the bridge → cleaning & preparing the data →
an ML baseline (condition from the readings) → the crack image the readings cannot describe → how a
machine learns (neuron → activation → gradient descent → network → training) → a CNN reads the crack →
a CNN locates it (Grad-CAM) → the safety audit → **prediction & the twin (anomaly detection + RUL
forecast)** → fusion → the business case.

Each page: **structural activity → engineering challenge → AI concept → technical illustration →
notebook connection.**

## The synthetic monitoring data

Every sensor sweep is generated in-code from approximate structural physics — natural frequency drops
as stiffness is lost, strain and vibration rise with damage and load, temperature confounds the
frequency — so the dataset, the trained models and the "try a reading" tools all stay consistent. No
external dataset required. The crack and deck-soffit images are synthetic numpy grids rendered as
heatmaps — no image assets and no PyTorch at runtime.

## Run the Streamlit app

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501 (or the port Streamlit prints). Use the sidebar or the clickable mind
map on the landing page to move through the 29 stages.

## Design principles

- Concise, professional engineering language — no dramatic storytelling.
- The inspector stays in charge; AI eases the continuous watch and the forecast one person cannot cover
  across a whole network. Never framed as "AI does what a human cannot".
- Color is a teaching device: **amber = the structural world**, **cyan = the AI**, **violet = the
  technical process** — consistently, on every page.

## Deploy (to get a public link)

1. Push this folder to a GitHub repo.
2. On [share.streamlit.io](https://share.streamlit.io), create an app pointing at the repo, main file
   `app.py`.
3. Deploy. You get a URL like `https://<name>.streamlit.app`.
