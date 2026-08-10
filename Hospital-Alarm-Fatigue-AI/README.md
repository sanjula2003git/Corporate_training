# Hospital Alarm-Fatigue Manager

A teaching Colab notebook about **allocating limited human attention**, not about predicting patient
deterioration.

A virtual ward of 20 patients streams heart rate, oxygen saturation, respiratory rate, blood pressure,
temperature, sensor quality and recent medications every 2 minutes for 12 days. The ward is allowed to
interrupt a nurse **five times an hour**. The notebook builds five systems that have to decide who gets those
five, and measures which one a ward could actually work with.

Written in deliberately plain English — shorter sentences and more explanation than the other notebooks in
this repo.

## Files

| File | What it is |
|---|---|
| `Hospital_Alarm_Fatigue_Manager.ipynb` | the notebook (open this) |
| `build_nb.py` | generates the notebook; edit this, not the `.ipynb` |
| `requirements.txt` | what it needs outside Colab |

Rebuild with:

```
py -3.13 build_nb.py
```

## What it covers

| Section | Content |
|---|---|
| 1–4 | alarm fatigue, the seven data streams, building the ward, three patients by eye |
| 5–7 | the five actions, the five-alerts-an-hour rule, the learn / dial-set / exam split |
| 8–9 | **Model 1** fixed monitor limits, and where the false alarms actually come from |
| 10–11 | feature engineering, **Model 2** a NEWS-style risk score |
| 12 | **Model 3** random forest |
| 13–14 | one neuron explained, **Model 4** an LSTM on the raw hour |
| 15 | ranking quality: AUC, average precision, and events-caught vs alerts-per-hour |
| 16–17 | **Model 5** the attention-budget optimizer (token bucket), and one patient replayed |
| 18–21 | two nurses and a queue, the scoreboard, honest limitations, summary |

## Success metrics

Critical events never alerted, **patients a nurse physically reached before the crisis**, early-warning
minutes, false alarms, nurse workload in minutes per hour, and median response time.

## The point of it

Models 3 and 5 use the **identical** random forest and the identical risk numbers. Model 3 alerts at a fixed
level chosen in advance; model 5 varies how sure it insists on being according to how much attention is left,
and can say *ignore*, *repeat the measurement* or *keep watching* instead of interrupting anybody.

That change alone — no better prediction — is what gets a nurse to every deteriorating patient before their
crisis, inside the budget.

## Running it

Colab has everything. Locally:

```
pip install -r requirements.txt
```

TensorFlow is optional: without it the notebook substitutes a scikit-learn network for the LSTM and every
section still runs. Full run time is a couple of minutes, most of it the LSTM.

## A note on the data

The ward is simulated, and deliberately busier than a real one so there are enough events to compare methods
fairly. The numbers in the notebook are statements about the simulator, not about any hospital. The method
transfers; the results do not.
