# AI for Electricity Load Forecasting — Electrical & Power Systems Engineering

An educational AI project that teaches **Machine Learning through short-term electricity load
forecasting**, for Electrical and Power Systems Engineering students with little or no AI background.
Every AI concept appears because a real grid operations problem required it — not because it is on a
syllabus.

It is the power-systems sibling of the Building Energy, Traffic Signal and Machine Anomaly projects:
same educational philosophy, same five-part page structure, redesigned end to end for a utility control
room.

## Two independent deliverables

| | Deliverable | Teaches | Files |
|---|---|---|---|
| 📓 | **Google Colab notebook** | **implementation** — runnable code, 136 cells, 33 steps | `build_nb.py` → `Electricity_Load_Forecasting_AI.ipynb` |
| 🖥️ | **Streamlit learning app** | **conceptual understanding** — 33 interactive stage pages | `app.py`, `story.py`, `bridge.py` |

They tell the same educational story and share the same demand model and random seed, so **every number
agrees between them** — but there is **no programmatic connection**: the app imports nothing from the
notebook and the notebook imports nothing from the app.

## The problem

It is 23:00 on a Sunday. The despatch engineer must decide **what generation runs tomorrow**. A large
thermal unit takes six to twelve hours to synchronise, so tomorrow evening's peak has to be committed
tonight, against a demand nobody has measured yet. Electricity cannot be stored economically at grid
scale, so generation must equal demand continuously — there is no buffer and no catching up later.

- **Under-forecast** → buy at balancing prices, start peaking plant, at the limit shed load.
- **Over-forecast** → committed units run at part load, burning fuel at a worse heat rate for nothing.

| Stream | Role | Method |
|---|---|---|
| Hourly demand from the SCADA historian | The target | **Regression** |
| Temperature, humidity from the weather desk | Weather-driven load | Cooling / heating degree hours |
| Day of week, weekends, public holidays | Calendar-driven load | Categorical flags |
| Demand 24 / 48 / 168 hours ago | The system's own memory | **Lag & rolling features** |
| → forecast demand for every hour of tomorrow | Day-ahead unit commitment | LinearRegression · RandomForest · GradientBoosting · XGBoost |
| → net load, ramp, reserve | Despatch instruction | Rule-based operating policy |

## The learning journey (one utility, two years of history)

The grid at work → one metered hour → instrumenting the network → reading the load curve →
feature engineering (cyclical clock, degree hours, lags) → **the forecast gate** → the persistence
baseline → four regression models → reading the model → the forecast audit → the operator's desk →
despatch and the business case.

**12 phases · 33 steps · 136 cells.** Each step follows the same five parts:

**Part 1** power system context → **Part 2** the engineering challenge → **Part 3** where the AI comes in
→ **Part 4** the runnable implementation → **Part 5** what you built + a one-line key takeaway.

## Results (test period: July–December 2024, 4,416 hours never seen in training)

| Method | MAE | RMSE | MAPE | R² |
|---|---|---|---|---|
| Persistence — same hour yesterday *(the method in use today)* | 49.4 MW | 63.8 MW | 7.52% | 0.811 |
| Persistence — same hour last week | 45.1 MW | 60.3 MW | 6.65% | 0.831 |
| **Gradient Boosting, day-ahead, bias-corrected** | **15.3 MW** | **19.4 MW** | **2.32%** | **0.983** |
| Gradient Boosting, one hour ahead *(different job — real-time balancing)* | 10.3 MW | 13.5 MW | 1.55% | 0.992 |

**Business case:** operating reserve sized at the 95th percentile of forecast error falls from
**128 MW to 38 MW** — 90 MW of synchronised capacity released — worth about **$9.4 M per year** at the
stated unit costs. The notebook sanity-checks that against the published rule of thumb and explains
honestly why it lands at the top of the range.

## The synthetic dataset

Two years of hourly data (17,544 rows) generated in-code from a demand model defined in step 1: a
double-peaked daily shape, day-type factors, a convex cooling response with a **temperature–humidity
interaction**, a milder heating response, 3.5%/yr load growth, and AR(1) measurement noise. Seasonal
weather is generated with autocorrelated anomalies, so hot spells last several days as they do in life.

The export is then **deliberately damaged** — comms dropouts, a three-day weather-station outage, a
frozen meter, RTU fault codes and duplicated rows — so the inspection and cleaning steps have something
real to find. No external dataset required, fully reproducible from `np.random.default_rng(42)`.

## The six engineering-discipline moments

These are the point of the notebook, and each is **measured rather than asserted**:

1. **Interpolating along time**, not with a column median — the median would have taught the model that
   03:00 is a busy hour (a 170 MW error at night).
2. **Voiding the frozen meter**, whose every individual value passes any range check you could write.
3. **The forecast gate** — `lag_1` is the most informative column in the dataset and is deleted, because
   at 23:00 it exists for exactly one hour of the 24.
4. **Chronological three-way split** — a shuffled split makes the same model look **29% more accurate**
   than it will be in the control room.
5. **Testing whether scaling helps** instead of applying it as a ritual — for OLS and trees it changes
   the answer by 0.000000 MW.
6. **Diagnosing the low drift as load growth**, not tuning a constant. The obvious fix — regressing
   demand on time — returns **+0.31 %/yr against a true 3.5 %/yr**, because a 16-month window is
   dominated by the seasonal cycle. The correction is measured as a residual on validation instead, and
   cuts MAE by 18%.

## The Streamlit application

A visual, conceptual counterpart to the notebook: **33 stage pages plus a landing page**, every one built
from the same five parts — *power system context → engineering challenge → AI connection → interactive
technical concept → notebook connection*, closed by a one-line key takeaway and a check-your-understanding
question.

**The landing page** has the four required sections: the engineering problem, the project goal, a
**clickable engineering mind map** (click any node to open that learning page), and the full
**Engineering → AI mapping** table.

Highlights:

- **Interactive grid mimic diagram** — generation fleet, 400 kV busbar and consumer classes, with the
  megawatts flowing at whichever hour you select, plus an animated 24-hour load curve.
- **The live forecast page** (`?stage=predict`) — sliders for time of day, temperature, humidity, day
  type, holiday and yesterday's demand, driving a **prediction gauge**, an engineering interpretation of
  *why* the forecast moved, a despatch implication, and a one-variable-at-a-time sensitivity chart.
- **Duck-curve despatch page** — net load = demand − solar, with an installed-solar slider that visibly
  worsens the evening ramp, and the despatch schedule it produces.
- **Operations dashboard** — forecast vs outturn, hourly error, reserve released, and the day's
  instructions colour-coded by type.
- Feature-importance, response-curve, error-segmentation and business-case pages, all recomputed live.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the printed URL. First load trains the four models (~30 s) and caches them.

`common.py` and `scaffold.py` are shared boilerplate synced in from the sibling teaching apps. **This app
does not use them** — it is self-contained in `app.py` / `story.py` / `bridge.py`.

## Run the notebook

**Colab:** upload `Electricity_Load_Forecasting_AI.ipynb` and run all. Everything needed is preinstalled.

**Locally:**

```bash
pip install numpy pandas scikit-learn plotly xgboost nbformat
jupyter notebook Electricity_Load_Forecasting_AI.ipynb
```

XGBoost is used in one step and is guarded by a `try/except`, so the notebook runs end to end without it.

**Rebuilding the notebook.** Never edit the `.ipynb`. Edit the `STEPS` registry in `build_nb.py` and
rebuild:

```bash
py -3.13 build_nb.py
```

Every code cell has been executed and verified, and every app stage has been rendered headlessly; the
prose quotes the computed numbers, so re-verify both after any change to the demand model.

## Design principles

- Concise, professional engineering language — no dramatic storytelling.
- The **Electrical Engineering concept comes before the AI concept**, on every page.
- Every prediction is explained with engineering reasoning, never as a bare number.
- **Power System Operator + AI.** The model forecasts and states how wrong it is likely to be; the
  despatch engineer commits the schedule and remains accountable for security of supply. AI is never
  presented as replacing engineers.

## Linking the two after deployment

The two deliverables are deliberately independent, but the notebook can *point* at the app once it is
deployed. Set `APP` at the top of `build_nb.py` to the deployed URL and rebuild:

```python
APP = "https://your-app.streamlit.app"
```

That switches on a "see this illustrated" link on all 33 notebook steps plus a link column in the workflow
table. **The stage ids already match** — `?stage=control-room`, `?stage=predict`, `?stage=reserve`, and so
on — so no other change is needed. Left as `""`, the notebook is built with no links rather than dead ones.
