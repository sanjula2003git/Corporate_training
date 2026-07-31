# Unusual Machine Behaviour Detection — Industrial Condition Monitoring

An educational AI project that teaches **AI through the vibration and temperature of a rotating machine**,
for mechanical, maintenance and reliability engineering students with little or no AI background.

It shares the philosophy and five-part page structure of the other `*-DL` projects, but it asks a
**different question**, and that difference is the whole point.

## How this differs from Predictive-Maintenance-DL

`Predictive-Maintenance-DL` is a **supervised** project: recognise known fault classes and forecast
remaining useful life from labelled failure histories.

This project is **anomaly detection**. You have thousands of healthy hours, a handful of labelled faults,
and — the part that matters — **no example of the failure that has not happened yet**. The two projects can
be taught back to back; this one is the answer to "what happens when the fault is new?"

| | Predictive Maintenance | This project |
|---|---|---|
| Question | Which known fault is this, and how long have I got? | Is this the machine I know? |
| Needs | Labelled examples of every fault | Examples of normal |
| Trains on | All classes | Healthy readings only |
| New fault type | Silently mislabelled | Flagged as unlike normal |
| Signature model | CNN / LSTM | **Autoencoder** |

## The problem

A 75 kW motor drives a gearbox and pump. A fitter walks the line weekly with a handheld meter and writes one
overall vibration number on a clipboard. Faults announce themselves for weeks before they break — quietly,
in frequencies the overall number does not notice.

| Stream | Role | Model |
|---|---|---|
| 8 named channels (RMS, kurtosis, 1×, 2×, temp, current…) | Odd combinations of known indicators | **ML** — Isolation Forest |
| → the traditional comparison | Single-channel limit | 3σ control chart |
| → learn the shape of normal | Rebuild error as anomaly score | Dense autoencoder |
| Raw 512-bin averaged spectrum | Find the fault nobody labelled | **DL** — spectrum autoencoder |
| → say *what* changed | Per-bin error → frequency → shaft order | The autoencoder's answer to Grad-CAM |

## The central promise

> **Machine Learning detects unusual behaviour using the features an engineer already knows how to measure.
> Deep Learning learns the shape of "normal" directly from the raw signal, and flags anything unlike it —
> including the fault nobody thought to name.**

Section 19 measures it. The measured result, per fault (detection rate; the `healthy` row is the false-alarm
rate):

| fault | Control chart | Isolation Forest | AE (8 features) | AE (raw spectrum) |
|---|---|---|---|---|
| healthy | 0.0% | 4.8% | 1.0% | 1.0% |
| imbalance | 58.0% | 86.4% | 88.6% | 76.1% |
| misalignment | 87.5% | 90.9% | 100.0% | 100.0% |
| bearing | 31.8% | 94.1% | 69.4% | 100.0% |
| **gear (never labelled)** | **0.0%** | **16.7%** | **0.0%** | **100.0%** |

Note the third column. Swapping Isolation Forest for a neural network on the *same eight features* gained
nothing and went backwards on bearing damage. The same autoencoder on the raw spectrum caught everything.
**The representation mattered more than the model** — that is the lesson the table is built to deliver.

## The two walls

Most notebooks in this series have one wall. This one has two, and they are mirror images:

- **Section 10 — the classifier wall.** A supervised Random Forest trained on healthy / imbalance /
  misalignment / bearing is shown a gear fault it has never seen. It calls it **healthy 49 times out of 54,
  at 94% mean confidence.** It has no box for "I don't recognise this", so it cannot use one.
- **Section 20 — the drift wall.** The anomaly detector's own failure mode. A perfectly healthy machine
  across a year of seasonal ambient swing produces **90% false alarms in January and July, 0% in March**.
  A classifier fails on faults it has not met; an anomaly detector fails when *normal* is something it has
  not met.

## The synthetic machine

Every burst is synthesised from rotating-machinery physics: shaft-order harmonics, an outer-race impulse
train ringing an 800 Hz housing resonance, and a gear mesh tone at 20 × shaft with ±1× sidebands.

Three modelling decisions are load-bearing and should not be casually changed:

1. **The gear fault is tonal and low-energy.** It moves overall RMS by ~4% and kurtosis by ~12%, so it hides
   inside normal variation on every named channel. This is not a trick — overall vibration severity
   (ISO 10816) is genuinely insensitive to early gear and bearing defects.
2. **Spectra are linear-averaged over 8 bursts**, as a real analyser does. With a single burst the gear peak
   stands ~2σ clear of healthy; averaged over 8 it stands ~9σ clear. Section 16 does not work without this.
3. **Each spectrum bin is standardised against healthy**, not min-max scaled. Otherwise the naturally noisy
   bins dominate the rebuild error and the error spectrum points at random high frequencies instead of the
   mesh sidebands.

## Honest numbers

- The business case applies the same **two-consecutive-readings** rule as the lead-time section. Without it,
  a 1.0% per-reading false-alarm rate on hourly data means ~5,000 investigations a year and **86% of the
  net benefit disappears**. The notebook shows both figures.
- The false-alarm independence assumption is flagged as optimistic — Section 20 has just demonstrated that
  false alarms arrive in correlated seasonal blocks, not independently.
- The sensitivity chart makes the point that net benefit is close to linear in *share of warnings actually
  acted on* — an organisational number, not a technical one.

## Files

| File | Purpose |
|---|---|
| `build_nb.py` | Generates the notebook from nbformat cells. Run `py -3.13 build_nb.py`. |
| `Unusual_Machine_Behaviour_DL.ipynb` | The runnable Colab notebook (60 cells, 25 code, 24 sections). |

Editing notes: inside `co(...)` cells use only single-line `"..."` docstrings or `#` comments — a
triple-quoted docstring would close the generator's own `r"""` string. Build Keras models with the
**functional API**; under Keras 3 a `Sequential` has no defined `.output`.

## Placeholders to fill in

Both live at the top of `build_nb.py`; rebuild after changing them.

```python
APP   = "https://REPLACE-ME.streamlit.app"                # the illustration app, once deployed
COLAB = "https://colab.research.google.com/REPLACE-ME"    # this notebook, once pushed
```

## Running the notebook

Colab has everything preinstalled. Elsewhere:

```
pip install numpy pandas scikit-learn tensorflow matplotlib
```

TensorFlow is optional here — unlike the other projects, this notebook falls back to a scikit-learn
autoencoder rather than skipping sections, so **every section produces a result either way**.
