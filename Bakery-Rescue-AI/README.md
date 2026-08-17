# 🥐 Sell It, Share It, Don’t Waste It

A B.Com/M.Com teaching project about demand forecasting, inventory, marginal costing, transparent
discounts, food-waste reduction and planned donations. Every result is simulated.

| File | Purpose |
|---|---|
| `Bakery_Rescue_AI.ipynb` | Standalone 16-phase Colab notebook |
| `build_nb.py` | Canonical notebook builder |
| `build_nb.mjs` | Local fallback builder |
| `bakery.py` | Demand, accounting, action evaluation and figures |
| `bridge.py` | Teaching registry |
| `app.py` | Interactive illustration/control-room app |

Build with `py -3 -X utf8 build_nb.py` or `node build_nb.mjs`.
Run the app with `py -3 -m streamlit run app.py`.

Hard constraints: one truthful public price, no protected characteristics, no sale or donation after
the safe period, no deceptive scarcity, and no cancellation of promised donations for a tiny late gain.
