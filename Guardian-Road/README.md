# 🛣️ Guardian Road — an AI safety shield around a fallen rider

A standalone teaching project about preventing a second collision after a rider falls in a live lane.
Everything is simulated. Nothing here may control a real road or decide medical care.

## Files

| File | Purpose |
|---|---|
| `Guardian_Road_AI_Safety_Shield.ipynb` | Colab notebook; runs top to bottom |
| `build_nb.py` | Canonical notebook builder; edit this, then rebuild |
| `guardian.py` | Physics, synthetic data, controllers, routes and Plotly figures |
| `bridge.py` | Shared five-part teaching registry |
| `app.py` | Interactive engineering-illustration app |

Build the notebook:

```powershell
py -3 -X utf8 build_nb.py
```

Run the illustrations:

```powershell
py -3 -m streamlit run app.py
```

## Safety architecture

Observation → conservative immediate warning → human verification → AI optimization → physical
constraints → road outputs → emergency-service supervision.

The physics minimum is a hard lower bound. Low sensor confidence activates a conservative fallback.
The controller detects an obstruction; it never diagnoses the rider.
