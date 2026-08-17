# 🟩 RescueGrid — an intelligent first-aid coordination mat

A teaching project about organizing helpers, equipment and responder access in a crowded emergency scene.
Everything is simulated. The system organizes space; it does not diagnose or select treatment.

## Files

| File | Purpose |
|---|---|
| `RescueGrid_First_Aid_Coordination_Mat.ipynb` | 15-phase standalone Colab notebook |
| `build_nb.py` | Canonical notebook builder |
| `build_nb.mjs` | Local fallback builder when Python is unavailable |
| `rescuegrid.py` | Grid, graph, optimization, sensors, metrics and figures |
| `bridge.py` | Shared teaching registry |
| `app.py` | Interactive engineering-illustration app |

Build the notebook with `py -3 -X utf8 build_nb.py` or `node build_nb.mjs`.

Run the app with `py -3 -m streamlit run app.py`.

## Safety architecture

Dispatcher-approved mode → required non-clinical roles and access rules → sensing → optimization →
deterministic safety validation → illuminated guidance → pressure verification → dispatcher override.
