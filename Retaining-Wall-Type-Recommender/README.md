# Retaining Wall Type Recommendation Using an MLP and Cost Optimization

An educational Civil Engineering + Deep Learning project containing:

- a Colab-ready notebook with nine linked Part 1–5 lessons;
- an MLP that ranks Gravity, Cantilever RCC, Anchored, and MSE wall concepts;
- a transparent suitability-versus-cost decision layer;
- a Streamlit companion with 32 registered technical illustration scenes.

The project uses simulated labels based on declared educational tendencies. It is a concept-screening demonstration, not a retaining-wall design or safety approval.

## Run locally

```text
pip install -r requirements.txt
streamlit run app.py
```

Replace the placeholder Streamlit URL in `tools/build_notebook.py`, then rerun that script to rebuild notebook links for deployment.
