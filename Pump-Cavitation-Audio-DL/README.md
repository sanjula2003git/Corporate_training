# Pump Cavitation Detection from Sound

A Mechanical Engineering + Signal Processing + Deep Learning teaching project. Four-second pump recordings are converted to log Mel-spectrograms and classified by a 2D CNN as Normal, Mild Cavitation, or Severe Cavitation.

## Safety statement

All operating responses in this project are simulated educational recommendations. They are not instructions for operating real industrial equipment. A real system requires pump-specific testing, instrumentation, hydraulic analysis, qualified engineering review, validated alarm logic, and approved procedures.

## Files

- `Pump_Cavitation_Audio_CNN.ipynb`: runnable Colab notebook.
- `app.py`: Streamlit companion with synthetic audio and interactive illustrations.
- `bridge.py`: shared eight-stage teaching registry.
- `story.py`: pump, waveform, audio, and spectrogram illustrations.
- `tools/build_notebook.py`: reproducible notebook generator.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notebook illustration links

The Streamlit companion contains a catalog of 32 dedicated technical illustration scenes distributed across all teaching stages.

Every notebook stage links to its matching Streamlit page using `?stage=<id>`. After deployment,
replace `https://pump-cavitation-audio.streamlit.app` in `tools/build_notebook.py` with the live
Streamlit URL and rebuild the notebook.
