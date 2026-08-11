# Pandas Basics — Student Data

A short teaching build on the smallest interesting table there is: three columns,
sixty students, and every problem a real dataset arrives with.

| Column | Meaning |
|---|---|
| `study_hours` | Hours studied per week |
| `attendance` | Class attendance, in percent |
| `result` | `Pass` or `Fail` |

No model is trained anywhere in this project. It is pandas, and pictures of pandas.

## The two deliverables

**`pandas_student_basics.ipynb`** — the notebook, 47 cells, all executed with their
figures embedded. Run it top to bottom in Colab; the messy CSV is written by the
first cell, so nothing needs uploading.

**`app.py`** — the illustration app. Sixteen pages, one per teaching step, routed by
`?stage=<id>` and following the same five-part layout as the other builds in this
repo. The sidebar lets a student *break the file on purpose* — add empty cells, glue
on duplicates, plant decimal-slip typos, choose median or mean — and every later page
reacts. The IQR multiplier is deliberately **not** a control: it is fixed at the
notebook's 1.5, and the page explains that the number is a convention rather than
letting a student dial it.

```
streamlit run app.py
```

## What it covers

| Phase | Pages |
|---|---|
| The file you were sent | the raw messy table |
| The first look | `head` / `tail`, `info`, `describe` / `value_counts`, and plotting it early |
| Cleaning | duplicates, finding the holes, drop-or-fill |
| Distribution | reading a boxplot, the 1.5 × IQR rule, what removal costs |
| Selecting rows | `iloc`, `loc`, and `loc` as a writer |
| The payoff | what the cleaned table finally says |

## Files

| File | What it is |
|---|---|
| `pandas_student_basics.ipynb` | The notebook, executed |
| `app.py` | The Streamlit app — routing and per-page content |
| `bridge.py` | The teaching registry: one entry per page |
| `story.py` | The data generator, the cleaning pipeline, and every figure |
| `smoke_test.py` | Walks every page and every slider edge; `python smoke_test.py` |
| `requirements.txt` | streamlit, numpy, pandas, plotly |

## Notes for whoever teaches this

- **The `iloc` / `loc` pages draw the selection onto a grid of the actual cells.** That
  picture is the point of those two pages — the end-included-versus-excluded difference
  is visible rather than asserted.
- **The "after the IQR filter" page deliberately still shows outliers.** Removing the
  extremes shrinks the IQR, so the fence moves inwards and the next-most-unusual
  students fall outside it. The page says so. Do not let anyone loop the rule.
- **The median-versus-mean argument needs the extremes dial.** At the notebook's
  default of three planted typos the two differ by about 0.13 hours, which proves
  nothing. Push the sidebar to eight and the gap opens to roughly 0.94.
- The students are invented. Nothing here says anything about any real class.
