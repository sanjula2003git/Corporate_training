# Building an Intelligent Construction Site

Teaching **Machine Learning vs Deep Learning** to Civil Engineering students, on one problem: a smart
construction site. Sensors → ANN (accident risk), helmet camera → CNN (missing helmet), plus AI Fusion.

**The teaching principle:** a student should never feel they are attending an AI lecture. They should
feel they are solving a construction engineering problem, and AI keeps turning out to be the part a
human cannot do. Every AI concept in this course *emerges from* a Civil Engineering activity, and is
never introduced before the engineering problem that requires it.

## Contents
- `Smart_Construction_Site_DL.ipynb` — the Colab notebook (open in Google Colab, run top to bottom).
- `app.py` — the Streamlit companion app: the router plus every technical illustration.
- `story.py` — the narrative-beat renderers (the site, the wall, the audit, the fusion engine).
- `bridge.py` — **the teaching scaffold**: the Civil-Engineering → AI content for all 29 steps, the
  project overview page, the engineering mind map and the Engineering-to-AI mapping.
- `construction_site_sensors.csv` — the site's (synthetic) sensor logs, loaded by the notebook.
- `helmets/`, `site/` — camera images for the CNN section and the site backdrop.
- `audio/` — narration mp3s + transcripts, one per step.
- `cnn_assets/` — precomputed real VGG16 feature maps and Grad-CAM.

## How a page is built

Every step page is assembled from five parts. Only Part 4 is a technical illustration:

| Part | Content | Rendered by |
|---|---|---|
| 1 | **On the construction site** — what happens, why engineers do it (no AI mentioned) | `bridge.open_page` |
| 2 | **The engineering challenge** — why the manual approach runs out of road | `bridge.open_page` |
| 3 | **Where the AI comes in** — plus the animated site → AI bridge figure | `bridge.open_page` |
| 4 | **The technical explanation** — terminology, maths, interactive visualization | the stage renderer in `app.py` / `story.py` |
| 5 | **In the notebook** — how you implement it, what it contributes to the system | `bridge.close_page` |

To add or reword a step's teaching content, edit its entry in `bridge.STEPS`. **Nothing in `app.py`
or `story.py` needs to change** — the renderers are Part 4 and are wrapped automatically.

**Color is a teaching device and never varies:** amber `#ffb74d` is always the construction world,
cyan `#4fc3f7` is always the AI world, violet `#ba68c8` is always the technical process.

## The engineering workflow — one construction day, 12 phases, 29 steps

| # | Phase | Steps (`?stage=`) |
|---|---|---|
| 1 | The Site | `site` · `enter-ai` |
| 2 | Morning Inspection | `inspection` · `two-worlds` |
| 3 | Materials Arrive | `load` · `inspect` |
| 4 | Preparing the Materials | `clean` · `normalize` · `split` |
| 5 | Risk From Instruments | `ml-baseline` |
| 6 | The Visual Wall | `pixel-problem` · `handmade-features` · `why-dl` |
| 7 | Training a Supervisor | `supervisor-brain` · `neuron` · `activation` |
| 8 | Learning From Mistakes | `learning-loop` · `loss` · `gradient-descent` · `learning-rate` · `optimizer` |
| 9 | The Inspection Team | `network` · `training` |
| 10 | The Automated Inspector | `cnn-journey` · `gradcam` |
| 11 | The Site Audit | `audit` · `proof` |
| 12 | Accident Prevention | `fusion-engine` · `pipeline` |

Plus `start` — the project overview (the problem, the goal, the clickable mind map, the mapping).
It is the default landing page.

Older `?stage=` links (`overview`, `compare`, `what-is-dl`, `cnn-input`, `feature-maps`, `evaluate`,
`compare-proof`, `fusion`) still resolve via the `ALIASES` table in `app.py`.

## Run the Streamlit app locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Then open a specific step with a query param, e.g.:
```
http://localhost:8501/                    # the project overview
http://localhost:8501/?stage=neuron
http://localhost:8501/?stage=clean
```
The sidebar shows which engineering phase you are in and which AI concept it maps to.
Requires **Streamlit ≥ 1.35** — the mind map's click-to-open uses `st.plotly_chart(on_select=...)`.
On older versions the map still renders; only the clicking degrades.

## Deploy (free) on Streamlit Community Cloud
1. Push this folder to a GitHub repo.
2. Go to https://share.streamlit.io → **New app** → pick the repo.
3. Set **Main file path** to `app.py` (or `Smart-Construction-DL/app.py` if the repo root is one level up).
4. Deploy. You'll get a URL like `https://<name>.streamlit.app`.
5. In the notebook, replace the `smartsite-dl.streamlit.app` placeholders with your real URL.

## Notes
- Visual style: dark, 3Blue1Brown-inspired, fully interactive (no rendered video).
- The CNN stages show **real VGG16** feature maps + Grad-CAM, precomputed offline into
  `cnn_assets/`. The deployed app just displays those PNGs — **no torch needed at runtime**.

## Regenerating the CNN assets (only if you change the images)
`tools/precompute_cnn.py` runs VGG16 over `helmets/` and writes `cnn_assets/`.
It needs PyTorch on **Python 3.13** (torch has no 3.14 wheels), and is not required by the app:
```bash
py -3.13 -m pip install torch torchvision matplotlib pillow --index-url https://download.pytorch.org/whl/cpu
py -3.13 tools/precompute_cnn.py
```

## Regenerating the narration
`tools/generate_narration.py` (edge-tts, voice `en-US-AriaNeural`) writes `audio/*.mp3` +
`audio/narration.json`.
