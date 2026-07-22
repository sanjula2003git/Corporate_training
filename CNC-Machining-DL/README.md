# AI-Based CNC Machining Optimization — Manufacturing Engineering

An educational AI project that teaches **AI through CNC machining optimization**, for Manufacturing /
Mechanical Engineering students with little or no AI background. Every AI concept appears because a real
machining problem required it — not because it is on a syllabus.

It is the machining twin of the Smart Construction DL and Predictive Maintenance DL projects: same
educational philosophy, architecture, navigation, and five-part page structure — redesigned end to end
for a CNC turning cell.

## The problem

Choose the **cutting speed, feed rate and depth of cut** that finish a batch fastest without wrecking
the tool or the surface finish. Push too hard: chatter, overheating, chipped tools, scrap. Cut too
soft: the shift runs out before the batch does. The sweet spot is real, and it moves with the material,
the tool and the machine.

| Stream | Role | Model |
|---|---|---|
| Force, vibration, temperature, current sensors | Read the cut | **ML** |
| → predict surface roughness (Ra) | Quality prediction | RandomForestRegressor |
| → predict tool life | Wear prediction | RandomForestRegressor |
| → recommend the optimal speed / feed / depth | Constrained optimization | grid search over the models |
| Camera → grade the machined surface | Visual quality inspection | **CNN** |
| Camera → detect a chipped tool edge | Defect detection + "show me where" | **CNN + Grad-CAM** |

## The learning journey (one machining-optimization programme)

The machine shop → one cutting trial → instrumenting the cut → cleaning & preparing the data → an ML
baseline (roughness & tool life from the readings) → the surface image the readings cannot describe →
how a machine learns (neuron → activation → gradient descent → network → training) → a CNN reads the
surface → a CNN finds the chipped tool → the machining audit → **the sweet spot (optimization)** →
fusion → the business case.

Each page: **machining activity → engineering challenge → AI concept → technical illustration →
notebook connection.**

## The synthetic machining data

Every pass is generated in-code from approximate machining physics (Kienzle-style cutting force,
Taylor-style tool life, the classic Ra ≈ f²/32r finish model), so the dataset, the trained models and
the optimizer's grid search all stay consistent. No external dataset required. The surface and
tool-edge images are synthetic numpy grids rendered as heatmaps — no image assets and no PyTorch at
runtime.

## Run the Streamlit app

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501 (or the port Streamlit prints). Use the sidebar or the clickable mind
map on the landing page to move through the 28 stages.

## Design principles

- Concise, professional engineering language — no dramatic storytelling.
- The machinist stays in charge; AI eases the search and the watching one person cannot cover alone.
  Never framed as "AI does what a human cannot".
- Color is a teaching device: **amber = the shop**, **cyan = the AI**, **violet = the technical
  process** — consistently, on every page.

## Deploy (to get a public link)

1. Push this folder to a GitHub repo.
2. On [share.streamlit.io](https://share.streamlit.io), create an app pointing at the repo, main file
   `app.py`.
3. Deploy. You get a URL like `https://<name>.streamlit.app`.
