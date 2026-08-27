"""
Builds Foundation_Settlement_Risk_AI.ipynb from nbformat cells.
Run:  python -X utf8 build_nb.py

Ten phases, one per stage of a real machine-learning project. Every phase is a
level-1 heading and every step a level-2 heading, so Colab's Table of contents
panel on the left lists the whole course and scrolls to any step.

House rule for this build: SHORT text. A phase gets two sentences, a step gets
one, and the figure does the teaching.

The geotechnics is standards-based and is used BOTH to generate the monitoring
records AND to check the model, so the notebook and the textbook never disagree:

  * Terzaghi 1-D consolidation      s_c = Cc/(1+e0) * H * log10((s'0+ds)/s'0)
  * Consolidation rate              Tv = cv*t/Hdr^2,  U from the Tv-U series
  * 2:1 stress distribution         ds = q*B*L/((B+z)(L+z))
  * Meyerhof (1965) SPT settlement  s = 1.9q/N  |  2.84(q/N)(B/(B+0.3))^2
  * Bjerrum / Skempton-MacDonald    angular distortion limits 1/500, 1/300, 1/150
  * Clough & O'Rourke               excavation settlement trough, exp decay

Every number quoted in the markdown was measured by running the notebook. If you
change a constant, re-run run_notebook.py and re-read the prose.
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

cells = []
def md(t):  cells.append(new_markdown_cell(t.strip("\n")))
def co(t):  cells.append(new_code_cell(t.strip("\n")))

NUM = ["①","②","③","④","⑤","⑥","⑦","⑧","⑨","⑩"]

PHASES = [
    ("The Problem",        "A building is sinking unevenly, and nobody can see why."),
    ("The Data",           "Five separate records that have never been in one table."),
    ("Exploring The Data", "Look before touching. What is real, and what is a broken sensor."),
    ("Preparing The Data", "Cleaning, and filling in the ground between the boreholes."),
    ("How Learning Works", "The words, and the honest test."),
    ("The First Model",    "The hand calculation every engineer already does."),
    ("Training A Model",   "Models that bend, and the split that decides the score."),
    ("Scoring It",         "The average miss, and the number that actually matters."),
    ("Where It Fails",     "Found on purpose: the grey zones and the tail."),
    ("Using It",           "Risk map, probable cause, forecast, next borehole."),
]

def phase(n, intro, away_prev=None):
    if away_prev:
        md("> **Key takeaway.** " + away_prev)
    name, sub = PHASES[n - 1]
    md(f"""
---

# {NUM[n-1]} {name}

**Phase {n} of 10** · *{sub}*

{intro.strip()}
""")

def step(icon, title, lead):
    md(f"""
## {icon} {title}

{lead.strip()}
""")


# ============================================================ TITLE / CONTENTS
md(r"""
# 🏗️ Foundation Settlement Risk AI

### Predicting where a building will sink, and explaining why

A building settles because the ground under it compresses. That is normal. The problem is when one part
settles more than another — **differential settlement** — because that is what bends and cracks a
structure.

This notebook builds a system that reads the records a site already has (boreholes, SPT, piezometers,
settlement sensors, column loads) and returns three things: **where** settlement is likely, **why**, and
**where to investigate next**.

---

### Contents

Use the **Table of contents** panel on the left (☰ icon) to jump between phases.

| | Phase | What you leave with |
|---|---|---|
| ① | **The Problem** | Why 25 mm in one corner is worse than 40 mm everywhere |
| ② | **The Data** | Five records joined into one table |
| ③ | **Exploring The Data** | The pattern, and four broken sensors |
| ④ | **Preparing The Data** | The ground map between the boreholes |
| ⑤ | **How Learning Works** | Why the split must be by building |
| ⑥ | **The First Model** | The hand method, and where it fails |
| ⑦ | **Training A Model** | Forest, boosting, and a leakage trap |
| ⑧ | **Scoring It** | Angular distortion, not millimetres |
| ⑨ | **Where It Fails** | Grey zones, and the tail it under-reads |
| ⑩ | **Using It** | Risk map, cause, forecast, next borehole |

---

> **About the data.** No real building's records are used. Every site in this notebook is generated from
> the standard soil-mechanics equations listed in the setup cell, which means we know the true ground
> conditions and can check the model against them — something you can never do on a real site.
""")

md(r"""
---

## Setup

Everything below is pre-installed in Colab. Charts are Plotly — hover, zoom, and click the legend.
""")

co(r'''
# !pip install numpy pandas scikit-learn plotly

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

pd.set_option("display.width", 150)
pd.set_option("display.max_columns", 40)

# Course palette: amber = the ground, cyan = the AI, and the risk colours.
AMBER, CYAN, VIOLET = "#e8a33d", "#3ba6d6", "#9b6fc7"
GREEN, YELLOW, RED, GREY = "#4caf50", "#f5c542", "#e05252", "#9aa0a6"
INK, MUTED = "#22303f", "#8b949e"

PLT = "plotly_white"

# Soil unit weights (kN/m3) and the standard constants used throughout.
G_FILL, G_SAND, G_CLAY, G_W = 18.0, 19.0, 16.0, 9.81
DF      = 1.2    # founding depth of the pad footings, m
NU      = 0.30   # Poisson's ratio of the bearing sand
I_SHAPE = 0.85   # rigid square footing influence factor
SAND_T  = 2.5    # thickness of the medium-dense sand between fill and clay, m

print("Environment ready.")
''')


# ============================================================ PHASE 1
phase(1, """
A foundation pushes the building's weight into the ground, and the ground compresses. Every building
settles. What damages a building is when **one part settles more than another**.
""")

step("🏭", "The warehouse that moved",
     "A 30-year-old distribution warehouse. Four columns along its south wall, surveyed to the nearest millimetre.")

co(r'''
# The survey record that started the investigation.

survey = pd.DataFrame({
    "column":        ["A", "B", "C", "D"],
    "settlement_mm": [4.0, 6.0, 22.0, 25.0],
})
SPACING_M = 7.5                      # column spacing along the wall

survey["step_mm"] = survey["settlement_mm"].diff()
survey["distortion"] = survey["step_mm"].abs() / (SPACING_M * 1000)
survey["as_fraction"] = ["-" if np.isnan(b) else f"1 in {1/b:,.0f}" for b in survey["distortion"]]

print(survey.to_string(index=False, na_rep="-"))
print()
print(f"Largest total settlement    {survey['settlement_mm'].max():.0f} mm")
print(f"Largest step between columns {survey['step_mm'].abs().max():.0f} mm over {SPACING_M} m")

fig = go.Figure()
fig.add_trace(go.Bar(x=survey["column"], y=-survey["settlement_mm"],
                     marker_color=[GREEN, GREEN, RED, RED], text=survey["settlement_mm"],
                     texttemplate="%{text} mm", textposition="outside", showlegend=False))
fig.update_layout(title="South wall: the ground gives way towards column D",
                  xaxis_title="Column", yaxis_title="Settlement (mm, downwards)",
                  height=380, template=PLT)
fig.update_yaxes(range=[-32, 4])
fig.show()
''')

step("📐", "Total settlement is not the problem",
     "A building that sinks 40 mm evenly is usually fine. One that sinks 25 mm at one end and 4 mm at the other is not.")

co(r'''
# Two buildings. Same ground, same load, different outcome.

def frame(fig, row, col, drops, title):
    x = np.array([0, 7.5, 15.0, 22.5])
    y = -np.array(drops) / 1000.0 * 60          # exaggerate the tilt so it is visible
    fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", line=dict(color=AMBER, width=4),
                             marker=dict(size=11, color=AMBER), showlegend=False), row=row, col=col)
    for xi, yi in zip(x, y):
        fig.add_shape(type="rect", x0=xi-0.9, x1=xi+0.9, y0=yi, y1=yi+2.6,
                      line=dict(color=INK, width=2), fillcolor="rgba(0,0,0,0)", row=row, col=col)
    fig.add_trace(go.Scatter(x=x, y=y+2.6, mode="lines", line=dict(color=INK, width=4),
                             showlegend=False), row=row, col=col)
    fig.add_annotation(x=11, y=3.6, text=title, showarrow=False, row=row, col=col)

fig = make_subplots(rows=1, cols=2, subplot_titles=("Uniform settlement", "Differential settlement"))
frame(fig, 1, 1, [40, 40, 40, 40], "40 mm everywhere · no distortion")
frame(fig, 1, 2, [4, 6, 22, 25],  "4 to 25 mm · the frame is bent")
fig.update_yaxes(range=[-2.4, 4.6], showticklabels=False)
fig.update_xaxes(showticklabels=False)
fig.update_layout(title="The same total movement does very different damage",
                  height=360, template=PLT)
fig.show()
''')

step("📏", "The number that decides it",
     "Angular distortion is the step between two columns divided by the distance between them. Published limits tell you what it costs.")

co(r'''
# Bjerrum / Skempton & MacDonald limiting values of angular distortion.

limits = pd.DataFrame({
    "distortion": [1/750, 1/500, 1/300, 1/150],
    "meaning": ["Safe limit for buildings where cracking is not permitted",
                "Safe limit for frames and load-bearing walls",
                "First cracking in panel walls; doors and windows start to stick",
                "Structural damage to beams and columns"],
})
limits["as_fraction"] = [f"1 in {1/b:,.0f}" for b in limits["distortion"]]
observed = survey["distortion"].max()

print(limits[["as_fraction", "meaning"]].to_string(index=False))
print()
print(f"Observed on the south wall: 1 in {1/observed:,.0f}")

fig = go.Figure()
for b, c, lab in zip(limits["distortion"], [GREEN, YELLOW, "#ef8b3c", RED], limits["as_fraction"]):
    fig.add_vline(x=1/b, line=dict(color=c, width=2, dash="dot"),
                  annotation_text=lab, annotation_position="top")
fig.add_trace(go.Scatter(x=[1/observed], y=[0], mode="markers+text", marker=dict(size=18, color=VIOLET),
                         text=["this warehouse"], textposition="bottom center", showlegend=False))
fig.update_layout(title="Angular distortion: smaller denominator means worse",
                  xaxis_title="1 in N  (log scale, better to the right)",
                  height=320, template=PLT)
fig.update_xaxes(type="log", range=[np.log10(100), np.log10(1200)])
fig.update_yaxes(range=[-1, 1], showticklabels=False)
fig.show()
''')

step("🕳️", "Why nobody saw it coming",
     "Before construction the site was drilled at five points. The soft ground runs between them.")

co(r'''
# The true thickness of soft clay under a site, and the five points that were drilled.

def clay_channel(x, y, x0=52.0, amp=18.0, wl=70.0, width=13.0, hmax=6.2):
    "Metres of soft clay: a buried river channel meandering across the site."
    centre = x0 + amp * np.sin(2 * np.pi * y / wl)
    return np.clip(hmax * np.exp(-((x - centre) / width) ** 2) - 0.5, 0.0, None)

gx, gy = np.meshgrid(np.linspace(0, 100, 120), np.linspace(0, 80, 100))
true_clay = clay_channel(gx, gy)

bh_x = np.array([12.0, 88.0, 15.0, 86.0, 50.0])
bh_y = np.array([12.0, 14.0, 68.0, 66.0, 62.0])
bh_clay = clay_channel(bh_x, bh_y)

fig = go.Figure(go.Heatmap(z=true_clay, x=gx[0], y=gy[:, 0], colorscale="YlOrBr",
                           colorbar=dict(title="Soft clay<br>(m)")))
fig.add_trace(go.Scatter(x=bh_x, y=bh_y, mode="markers+text", marker=dict(size=14, color="white",
                         line=dict(color=INK, width=2), symbol="circle"),
                         text=[f"BH{i+1}<br>{c:.1f} m" for i, c in enumerate(bh_clay)],
                         textposition="top center", showlegend=False))
fig.update_layout(title="Five boreholes on a 100 m x 80 m site. Four of them missed the channel.",
                  xaxis_title="Easting (m)", yaxis_title="Northing (m)", height=470, template=PLT)
fig.show()

print(f"Soft clay found in the boreholes:  max {bh_clay.max():.1f} m")
print(f"Soft clay actually present on site: max {true_clay.max():.1f} m")
sampled = 5 * np.pi * 0.075 ** 2          # five 150 mm holes
print(f"Ground actually sampled: {sampled:.2f} m2 out of {100 * 80:,} m2 "
      f"— one part in {100 * 80 / sampled:,.0f}.")
''')
