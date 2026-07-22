# Intelligent Predictive Maintenance System — Mechanical Engineering

An educational AI project that teaches **AI through predictive maintenance**, for Mechanical
Engineering students with little or no AI background. Every AI concept appears because a real
maintenance problem required it — not because it is on a syllabus.

It is the mechanical-engineering twin of the Smart Construction DL project: same educational
philosophy, architecture, navigation, and five-part page structure — redesigned end to end for a
manufacturing plant.

## Two deliverables

| File | What it is |
|---|---|
| `app.py` + `bridge.py` + `story.py` | The **Streamlit illustration app** — interactive animations, engineering explanations and AI visualizations. |
| `Predictive_Maintenance_DL.ipynb` | The **Google Colab notebook** — the complete runnable implementation (data → ML → CNN → LSTM → fusion → dashboard). |

## The learning journey (one predictive-maintenance programme)

Factory floor → Machine inspection → Sensor commissioning → Data collection → Cleaning →
Preparation → ML baseline → Why ML cannot read a raw signal → Deep learning → CNN (vibration) →
LSTM (trend / remaining useful life) → Training → Evaluation → Fusion → Predictive-maintenance
control center.

Each page: **mechanical activity → engineering challenge → AI concept → technical illustration →
notebook connection.**

## The synthetic industrial data

Seven sensors per machine — temperature (°C), pressure (bar), vibration (mm/s RMS), speed (RPM),
current (A), oil quality (0–100), runtime (h) — plus raw accelerometer waveforms (bearing-fault
impacts) and degradation trends for remaining-useful-life estimation. All generated in-code; no
external dataset required.

## Run the Streamlit app

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501 (or the port Streamlit prints). Use the sidebar or the clickable
mind map on the landing page to move through the stages.

## Run the notebook

Open `Predictive_Maintenance_DL.ipynb` in Google Colab and run top to bottom. Colab already has
TensorFlow/Keras for the CNN and LSTM.

## Design principles

- Concise, professional engineering language — no dramatic storytelling.
- The engineer stays in charge; AI eases the watching one person cannot cover alone. Never framed
  as "AI does what a human cannot".
- Color is a teaching device: **amber = the plant**, **cyan = the AI**, **violet = the technical
  process** — consistently, on every page.
