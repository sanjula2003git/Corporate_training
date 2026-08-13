# 🚨 The Golden Minutes — an AI Roadside First-Response Beacon

A teaching project about the four minutes between a crash and an ambulance.

A camera on a pole watches a junction. Today it records crashes for the file. This project asks
what it should do **while the crash is still happening**: detect it, call it in, keep bystanders
out of the live lane, and turn the people already standing there into a response team.

Everything here is simulated. Nothing in it is a medical device or an emergency system.

## What is in the folder

| File | What it is |
|---|---|
| `Roadside_First_Response_Beacon.ipynb` | the teaching notebook, 20 sections, runs top to bottom in Colab |
| `build_nb.py` | builds that notebook — **edit this, not the .ipynb** |
| `story.py` | the simulated junction, the detectors and the figures, trimmed for the app |
| `bridge.py` | the teaching registry: 18 steps, five parts each |
| `app.py` | the illustration app, one page per step, routed by `?stage=` |

Rebuild the notebook with:

```
py -3.13 -X utf8 build_nb.py
```

The `-X utf8` matters on Windows: without it every em-dash in the prose is mangled.

## The teaching arc

Fourteen kinds of 24-second clip come off one camera at 5 frames a second — nine ordinary, five
real incidents. The ordinary ones are the interesting half: a red light, a rush-hour crawl, a near
miss, a mechanic under a van, a fallen board that the detector calls a person.

Three detectors are compared on the same exam clips:

| Detector | Incidents missed | Seconds to the alarm | False alarms/hour |
|---|---|---|---|
| One frame: "somebody is lying in the road" | 4 of 28 | 0.6 | 37.5 |
| A six-second timer, plus a smoke rule | 9 of 28 | 6.8 | 23.7 |
| A forest over a six-second window, 3 s wait | **0 of 28** | 2.8 | 7.9 |

A 1D CNN on the raw signals is also trained (section 10). It does **not** simply win: it raises
about half the false alarms of the forest and is 0.6 seconds slower every time.

The second half of the notebook is not about detection at all — the dispatch packet, a hazard map,
a safe route in by Dijkstra, an approved-module state machine, red/amber/green feedback on the
helper, and job assignment for the crowd.

## The three things that took the longest to get right

1. **The near miss has exactly a crash's impact signature.** Same gap, same braking, same closing
   speed. Only what happens in the next few seconds differs. Without that, every model scored
   perfectly and the notebook taught nothing.
2. **Nothing in the scene appears instantly.** Traffic takes seconds to stop, crowds take ten or
   more to gather. Before that was true, alarms could fire on the impact frame itself and "seconds
   to the alarm" was a meaningless 0.0.
3. **The training mix, not the model.** Built with one red light per crash, the forest learned that
   stopped traffic means a crash and called the control centre at every signal cycle. Eight red
   lights per four crashes fixed it, with no change to the model at all. Section 11.

## Running the app

```
py -3.13 -m streamlit run app.py
```

Deep links are `?stage=<id>`, with the ids in `bridge.ORDER`. Navigation inside the app is by
button, never by markdown link — Streamlit renders every markdown link with `target="_blank"`, so
a link opens a new browser tab on every click.
