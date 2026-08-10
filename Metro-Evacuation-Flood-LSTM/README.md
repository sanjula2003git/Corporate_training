# Metro Evacuation Flood Forecasting with LSTM

A Civil Engineering + Deep Learning teaching project. It predicts the water depth on two underground-metro evacuation routes five minutes ahead, then recommends the safer exit.

## Project assumption

For this educational demonstration only:

- Below 10 cm: SAFE
- 10–20 cm: WARNING
- Above 20 cm: UNSAFE

These values are explicit project assumptions, not universal real-world evacuation standards. A real system requires site-specific hydraulic analysis, validation, authority approval, redundancy, fail-safe procedures, and human command.

## Five inputs and one output

Inputs: rainfall intensity, entrance water level, tunnel water level, drainage flow, and current route water level. The LSTM sees the previous ten one-minute measurements and predicts route water depth five minutes later.

## Files

- `Metro_Evacuation_Flood_LSTM.ipynb`: runnable Jupyter/Google Colab notebook.
- `app.py`: Streamlit companion with interactive illustrations.
- `bridge.py`: shared teaching registry used by the notebook generator and app.
- `story.py`: Plotly station, sequence, and forecast illustrations.
- `tools/build_notebook.py`: reproducibly generates the notebook.
- `requirements.txt`: Python dependencies.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Rebuild the notebook with:

```bash
python tools/build_notebook.py
```

## Notebook illustration links

The Streamlit companion contains a catalog of 32 dedicated technical illustration scenes distributed across all teaching stages.

Every notebook stage links to its matching Streamlit page using `?stage=<id>`. After deployment,
replace `https://metro-evacuation-flood.streamlit.app` in `tools/build_notebook.py` with the live
Streamlit URL and rebuild the notebook.
