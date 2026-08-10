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
| `app.py` | the Streamlit illustration app — one page per teaching step |
| `bridge.py` | the teaching registry: one entry per page. **Content edits go here** |
| `story.py` | the ward, the models and the figures the app draws |
| `requirements.txt` | the **app's** dependencies (see the note below) |

Rebuild the notebook with:

```
py -3.13 build_nb.py
```

Run the app locally with:

```
streamlit run app.py
```

## The app

Deployed at **https://hospital-alarm-fatigue.streamlit.app**, and every step of the notebook links into it
with `?stage=<id>`. Sixteen pages, each following the notebook's five-part shape: what happens on the ward,
why it is hard, where the AI comes in, the illustration, and the takeaway.

Three sidebar sliders — alerts allowed per hour, nurses on shift, sensor glitches per patient — re-run the
whole ward. That is the thing the notebook cannot do: drop the budget to 2 or push the glitch rate to 40 and
watch which metric breaks first.

Two deliberate differences from the notebook, both forced by the 1 GB free container:

- **Six days of ward instead of twelve**, and a 60-tree forest instead of 150. Steady-state memory is about
  230 MB.
- **No LSTM.** `requirements.txt` has no TensorFlow, because installing it would not fit. The sequence model
  is explained on its page rather than trained, so the app's scoreboard runs 1, 2, 3 and 5. The notebook
  trains all five — and found the forest ranks patients better than the LSTM anyway.

To run the **notebook** outside Colab you also need `tensorflow-cpu`; it is left out of `requirements.txt` on
purpose so the deployed app stays inside its container.

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

## Running the notebook

Colab has everything — use the badge at the top of the notebook. Locally you need the app's requirements
plus `tensorflow-cpu`.

TensorFlow is optional even there: without it the notebook substitutes a scikit-learn network for the LSTM
and every section still runs. A full run takes a couple of minutes, most of it the LSTM.

## A note on the data

The ward is simulated, and deliberately busier than a real one so there are enough events to compare methods
fairly. The numbers in the notebook are statements about the simulator, not about any hospital. The method
transfers; the results do not.
