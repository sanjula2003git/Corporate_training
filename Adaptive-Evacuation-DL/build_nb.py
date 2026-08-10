"""
Builds Adaptive_Emergency_Evacuation_DL.ipynb from nbformat cells.
Run:  py -3.13 build_nb.py

Modelled on the Smart Construction notebook: one intro block (problem -> what we
build -> workflow -> Engineering-to-AI map), then the steps, each rendered as the
same five parts:

    header + Part 1 (fire engineering) + Part 2 (the challenge)
    Part 3 (where the AI comes in) + the bridge table + Part 4 header
    the code
    Part 5 (what you just built) + a one-line key takeaway

The notebook is standalone: it imports nothing from this file, and re-defines the
building, the smoke physics and the crowd model inline.

APP: set this to the deployed Streamlit URL to switch on the per-step
"see it illustrated" links and the link column in the workflow table. Leave it as
"" and the notebook is built with no links at all, rather than dead ones.
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

APP = "https://adaptive-evacuation-dl.streamlit.app"

cells = []
def md(t):  cells.append(new_markdown_cell(t.strip("\n")))
def co(t):  cells.append(new_code_cell(t.strip("\n")))

def link(stage, label):
    return f"[{label}]({APP}/?stage={stage})" if APP else label


# ============================================================================
# THE PHASES  (one fire, in the order a fire engineer would work through it)
# ============================================================================
PHASES = [
    ("The Building At 14:40",     "An ordinary afternoon, 858 people, and a fryer that catches."),
    ("The Building As A Graph",   "Rooms become nodes, corridors become edges with a capacity."),
    ("Smoke In Motion",           "How a fire fills a building, and when a corridor stops being a route."),
    ("The Detection System",      "What the building actually knows about itself, and how it goes blind."),
    ("Preparing The Data",        "Dead loops out, units standardised, and a split that does not cheat."),
    ("Predicting From The Gauges","Forecasting smoke from eight columns a fire engineer can name."),
    ("How A Machine Learns",      "A neuron, a loss, a step downhill, a network."),
    ("Reading The Whole Floor",   "The detector grid becomes an image, and a CNN forecasts the field."),
    ("The Blind Loop",            "The proof: what happens when a detection circuit is cut."),
    ("Four Controllers",          "Static signs, shortest path, risk-aware, and one that predicts."),
    ("The Benchmark",             "Every controller, on fires it has never seen."),
    ("The Fire Safety Case",      "Lives, exposure, and what a fire engineer has to sign."),
]

NUM = ["①","②","③","④","⑤","⑥","⑦","⑧","⑨","⑩","⑪","⑫","⑬","⑭","⑮",
       "⑯","⑰","⑱","⑲","⑳","㉑","㉒","㉓","㉔","㉕","㉖","㉗","㉘","㉙","㉚"]


# ============================================================================
# THE STEPS
#   Each entry drives four cells. `body` is a list of ('md', text) / ('co', code)
#   items making up Part 4 - most steps have exactly one code cell.
# ============================================================================
STEPS = []
def step(**kw):
    STEPS.append(kw)
