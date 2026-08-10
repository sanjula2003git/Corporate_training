# Dam Flood Protection and Water Security

A Civil Engineering + Deep Learning teaching project. An MLP predicts reservoir level six hours after a forecast storm using six summarized inputs. A separate transparent decision layer proposes a pre-release and caps it according to downstream river condition.

## Safety boundary

This is an educational decision-support simulation. It does not authorize, automate, or recommend operation of a real dam. Real reservoir operation requires approved rule curves, calibrated hydrology and hydraulics, forecast ensembles, instrumentation, emergency action plans, qualified operators, responsible authorities, and regulatory compliance.

## Files

- `Dam_Flood_Water_Security_MLP.ipynb`: runnable Colab notebook.
- `app.py`: interactive Streamlit companion.
- `bridge.py`: shared eight-stage teaching registry.
- `story.py`: reservoir and scenario illustrations.
- `tools/build_notebook.py`: notebook generator.

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notebook illustration links

The Streamlit companion contains a catalog of 32 dedicated technical illustration scenes distributed across all teaching stages.

Every notebook stage links to its matching Streamlit page using `?stage=<id>`. After deployment,
replace `https://dam-flood-water-security.streamlit.app` in `tools/build_notebook.py` with the live
Streamlit URL and rebuild the notebook.
