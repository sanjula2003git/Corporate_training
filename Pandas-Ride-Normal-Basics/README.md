# Pandas Basics — Normally Distributed Ride Data

An exact teaching-style replica of `Pandas-Student-Basics`, using fictitious visitors with three supplied columns: `person`, `height_cm`, and `weight_kg`.

Height and weight are generated from normal distributions. The notebook teaches why mean and median are close for symmetric data, uses mean imputation for missing numeric values, retains valid tail observations for inspection, and derives `allowed` from simulated classroom ride limits.

The simulated limits—145–190 cm and at most 90 kg—are not the policy of a real Hong Kong attraction.

- `pandas_ride_normal_basics.ipynb`: executed Colab notebook.
- `app.py`: 16-step Streamlit illustration app.
- `story.py`: generator, cleaning pipeline and figures.
- `bridge.py`: matching lesson registry.
- `smoke_test.py`: app/data smoke checks.

App URL name: `pandas-ride-normal-basics` → `https://pandas-ride-normal-basics.streamlit.app`.
