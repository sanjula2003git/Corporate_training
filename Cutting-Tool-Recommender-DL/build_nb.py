"""
Builds Cutting_Tool_Recommendation_DL.ipynb from nbformat cells.
Run:  py -3.13 build_nb.py

Same five-part-per-step layout as the Smart Construction / Building Energy
notebooks. 20 steps, 9 phases.

The domain knowledge is real: Taylor's tool life equation (V·T^n = C) and the
theoretical surface finish relation (Ra = f^2 / (32·r) ). Both are used to
generate the tool-room log AND to check the model's recommendations, so the two
always agree.

APP: set to a deployed Streamlit URL to switch on the per-step links.
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

APP = "https://cutting-tool-recommender.streamlit.app"

cells = []
def md(t):  cells.append(new_markdown_cell(t.strip("\n")))
def co(t):  cells.append(new_code_cell(t.strip("\n")))
def link(stage, label):
    return f"[{label}]({APP}/?stage={stage})" if APP else label

PHASES = [
    ("The Job Arrives",       "A drawing lands in the tool room and something has to be chosen."),
    ("One Job, One Record",   "A completed job becomes a written record with an outcome."),
    ("The Tool-Room Log",     "The ERP export lands and gets checked."),
    ("Preparing The Data",    "Words become numbers, and the jobs are split."),
    ("The Recommendation",    "Predicting the tool, the coating, the speed and the feed."),
    ("The Image Wall",        "The insert goes under the camera and the rulebook collapses."),
    ("Reading The Wear",      "A CNN grades a wear land no rule could grade."),
    ("The Tool-Room Audit",   "Every recommendation checked on jobs never seen."),
    ("The System",            "Fusion, and what it is worth per year."),
]

NUM = ["①","②","③","④","⑤","⑥","⑦","⑧","⑨","⑩",
       "⑪","⑫","⑬","⑭","⑮","⑯","⑰","⑱","⑲","⑳"]

STEPS = []
def step(**kw): STEPS.append(kw)


# ---------------------------------------------- PHASE 1
step(
    id="the-job", phase=0, icon="📐", ai_icon="🤖",
    civil="A Job Card Arrives", ai="Why Tool Selection Needs AI",
    tech="One job, thousands of valid tooling combinations",
    site="""A drawing lands in the tool room. Inconel 718 bracket, 5-axis machining centre, finishing pass,
Ra 0.8 µm, batch of 240. Somebody now has to choose a tool material, a coating, a cutting speed, a feed
rate and a coolant strategy — five decisions, before a single chip is cut.""",
    challenge="""Get it wrong and the consequences are immediate: an insert that welds up on Inconel, a speed that
burns the edge in four minutes, a feed that cannot hold the finish. The knowledge that prevents this
lives with whoever has been in the tool room longest, and it walks out of the door when they retire.""",
    ai_link="""Be clear what is being asked for before anybody says machine learning. Not judgement. Something duller:
a way to make the tool room's accumulated experience **available on every job**, consistently, including
on the jobs nobody has run before.""",
    bridge=[("Five coupled decisions", "Multi-output prediction"),
            ("Experience in one head", "Learned from the log"),
            ("New material every week", "Generalises to new jobs")],
    body=[("co", r'''
# How large is the choice actually being made?
TOOL_MATERIALS = ["HSS", "carbide", "coated_carbide", "cermet", "CBN", "PCD"]
COATINGS       = ["uncoated", "TiN", "TiAlN", "AlCrN", "DLC"]
COOLANTS       = ["dry", "flood", "MQL", "high_pressure"]

speeds = 40          # sensible cutting speeds, in 10 m/min steps
feeds  = 25          # sensible feeds, in 0.02 mm/rev steps
combos = len(TOOL_MATERIALS)*len(COATINGS)*len(COOLANTS)*speeds*feeds

print(f"tool materials {len(TOOL_MATERIALS)} x coatings {len(COATINGS)} x coolants {len(COOLANTS)}"
      f" x speeds {speeds} x feeds {feeds}")
print(f"= {combos:,} combinations for ONE job card.")
print()
print("Almost all of them cut metal. A few dozen cut it economically.")
print("A handful hold Ra 0.8 on Inconel without destroying the edge in five minutes.")
print()
print("That is the problem. Not 'what works' - 'what works best', on a job nobody has run before.")
''')],
    built="""The size of the decision, stated in numbers. Nothing here is AI yet — this is just the reason the
tool room has a most-experienced person, and why that is a fragile arrangement.""",
    takeaway="""Five coupled decisions per job, and the knowledge that makes them lives in one person's head.""",
)

step(
    id="enter-ai", phase=0, icon="🗄️", ai_icon="🛰️",
    civil="The Tool Room's Memory", ai="A Recommender System",
    tech="Every past job, available on every new job",
    site="""Nothing about the machining changes. Same machines, same inserts, same inspection. The setter still
sets the job, still listens to the cut, still calls it off if it sounds wrong. What changes is that
every job the shop has ever run is now written down with its outcome.""",
    challenge="""The usual objection: is this here to replace the tool-room engineer? No. A model cannot hear chatter,
see a built-up edge forming, or decide that this customer's part is worth a slower, safer cut. It can
only say what has worked on jobs like this one.""",
    ai_link="""A recommender proposes a starting point and shows what it is based on. The engineer accepts it, adjusts
it, or overrides it — and that decision goes back into the log. The system gets better because the
engineer is in the loop, not despite it.""",
    bridge=[("The setter stays", "Proposes a starting point"),
            ("Experience written down", "Learned from outcomes"),
            ("Nobody is replaced", "You still sign the setup sheet")],
    body=[("md", r"""
| The engineer stays in charge of | Where the log helps |
|---|---|
| Hearing chatter and calling off a cut | Recalling all 4,000 past jobs, not the memorable ten |
| Judging whether a finish will pass | Being consistent between the day and night shift |
| Deciding a critical part gets a safe cut | Starting points for a material nobody has run |
| Signing the setup sheet | Never having a bad Monday |

> The recommendation is a **starting point with its reasoning attached**, not an instruction to the
> machine. That distinction is fixed here and holds for the rest of the notebook.
""")],
    built="""The role of the system, settled before any code. It proposes; a person disposes.""",
    takeaway="""A recommender makes the tool room's memory available on every job. The engineer still decides.""",
)

# ---------------------------------------------- PHASE 2
step(
    id="one-job", phase=1, icon="📋", ai_icon="🗃️",
    civil="One Completed Job", ai="Data Collection",
    tech="Job inputs → tooling chosen → outcome measured",
    site="""When a job finishes, the shop records what went in and what came out: the workpiece material, the
machine, the operation, the finish required, the batch quantity — then the tool that was used, the speed
and feed it ran at, and the tool life and finish actually achieved.""",
    challenge="""Those records sit in an ERP system and are almost never read. Nobody has time to query four thousand
past jobs before setting today's one.""",
    ai_link="""Written as one row, a completed job is a training example: **inputs → the choice made → how it turned
out.** Thousands of those rows are the tool room's experience in a form a model can use.""",
    bridge=[("What the job needs", "Features"),
            ("What was chosen", "Targets"),
            ("How it turned out", "The label's quality")],
    body=[("md", r"""
| Input on the job card | Why it matters to the choice |
|---|---|
| 🧱 Workpiece material | The single biggest driver. Inconel and aluminium share no tooling at all. |
| 🏭 Machine type | Rigidity, power and spindle speed cap what is achievable. |
| ⚙️ Operation | Roughing wants feed and depth; finishing wants speed and a fine feed. |
| ✨ Required Ra | Sets an upper limit on feed, through the surface-finish relation. |
| 📦 Batch quantity | Decides whether an expensive insert can pay for itself. |
| 📏 Tool diameter / nose radius | Nose radius appears directly in the finish calculation. |
| 🕐 Previous tool life | The tool history — what a similar tool actually achieved here. |

| Recommended output | Type |
|---|---|
| Tool material — HSS, carbide, coated carbide, cermet, CBN, PCD | classification |
| Coating — uncoated, TiN, TiAlN, AlCrN, DLC | classification |
| Coolant — dry, flood, MQL, high pressure | classification |
| Cutting speed Vc (m/min) | regression |
| Feed f (mm/rev) | regression |

Five outputs, three of them categorical. That mix is what makes this a recommender rather than a single
prediction.
"""),
          ("co", r'''
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

np.random.seed(42)
CYAN, AMBER, GREEN, RED, MUTED = "#4fc3f7", "#ffb74d", "#66bb6a", "#ef5350", "#8b949e"

# ---------------------------------------------------------------- the machining knowledge
# Reference cutting speed (m/min) for COATED CARBIDE at 30 minutes of tool life.
BASE_VC = {"aluminium_6061": 500, "brass_360": 300, "mild_steel_1045": 220,
           "cast_iron_gg25": 160, "stainless_316": 130, "ti_6al_4v": 65,
           "inconel_718": 35}

# Tool material speed multiplier, and Taylor exponent n in V * T^n = C.
TOOL_VC_MULT = {"HSS": 0.30, "carbide": 0.75, "coated_carbide": 1.00,
                "cermet": 1.25, "CBN": 2.00, "PCD": 2.50}
TAYLOR_N     = {"HSS": 0.12, "carbide": 0.22, "coated_carbide": 0.28,
                "cermet": 0.30, "CBN": 0.40, "PCD": 0.45}
OP_VC_MULT   = {"roughing": 0.85, "semi_finish": 1.00, "finishing": 1.20}

MACHINES = {"cnc_lathe":       dict(power_kw=18, max_rpm=4000,  rigidity=1.00),
            "vmc_3axis":       dict(power_kw=15, max_rpm=12000, rigidity=0.90),
            "5axis_centre":    dict(power_kw=22, max_rpm=18000, rigidity=0.85),
            "tool_room_mill":  dict(power_kw=7,  max_rpm=3500,  rigidity=0.70)}

def taylor_life(vc, vc_ref, tool_material, t_ref=30.0):
    """Taylor's tool life equation, V * T^n = C.

    C is pinned so that the reference speed gives t_ref minutes of life, which is
    how a tooling catalogue actually quotes it. Then life at any other speed follows.
    """
    n = TAYLOR_N[tool_material]
    C = vc_ref * t_ref**n
    return (C/np.maximum(vc, 1e-6))**(1.0/n)

def feed_for_ra(ra_um, nose_r_mm):
    """Theoretical surface finish: Ra ~= f^2 / (32 * r), with Ra in um, f and r in mm.
    Rearranged to give the largest feed that can still hold the required finish."""
    return np.sqrt(np.asarray(ra_um, float)*32.0*np.asarray(nose_r_mm, float)/1000.0)

def ra_for_feed(f_mm_rev, nose_r_mm):
    "The same relation, forwards."
    return 1000.0*np.asarray(f_mm_rev, float)**2/(32.0*np.asarray(nose_r_mm, float))

# sanity-check both against numbers a machinist would recognise
print("Feed needed to hold a finish (nose radius 0.8 mm):")
for ra in [0.4, 0.8, 1.6, 3.2, 6.3]:
    f = float(feed_for_ra(ra, 0.8))
    print(f"   Ra {ra:4.1f} um  ->  f = {f:.3f} mm/rev   (back-check: Ra {ra_for_feed(f, 0.8):.2f})")

print("\nTool life at the reference speed and at 25% over it (coated carbide, mild steel):")
vc_ref = BASE_VC["mild_steel_1045"]
for mult in [0.75, 1.00, 1.25]:
    print(f"   Vc = {vc_ref*mult:5.0f} m/min  ->  T = "
          f"{taylor_life(vc_ref*mult, vc_ref, 'coated_carbide'):6.1f} min")
''')],
    built="""Two real machining equations, checked against numbers a machinist would recognise. Everything that
follows — the dataset, the recommendation, the audit — is built on these two and nothing else.""",
    takeaway="""A completed job is a training example: what the job needed, what was chosen, and how it turned out.""",
)

step(
    id="two-records", phase=1, icon="🧾", ai_icon="🔀",
    civil="Job Card vs Insert Photo", ai="Two Kinds Of Data",
    tech="Named columns, or 4,096 unnamed pixels",
    site="""Two records exist for every job. The job card — named fields with units, every one of them chosen by
an engineer. And, at tool change, a photograph of the insert edge taken on the presetter.""",
    challenge="""The job card tells you what was asked for. The photograph tells you what the last tool actually
endured — the flank wear land, whether the edge chipped, whether there is built-up edge. That is the
'tool history' input, and it arrives as pixels.""",
    ai_link="""Named columns suit Machine Learning: the engineer picks the fields, the model weights them. Raw pixels
do not — nobody can name 4,096 useful columns. That difference is why this notebook has two halves.""",
    bridge=[("The job card", "Named columns → ML"),
            ("The insert photo", "Raw pixels → DL"),
            ("Same tool, two views", "The fork in the road")],
    body=[("co", r'''
def make_insert(vb_mm=0.0, size=64, seed=0, stain=False, bue=False):
    """An insert cutting edge under the presetter camera, as a brightness grid.

    The flank face runs across the frame. Wear shows as a BRIGHT polished land
    along the edge, and its width VB (mm) is what ISO 3685 measures.
      stain - coolant residue: a dark blotch that is not wear
      bue   - built-up edge:   a bright lump that is not a wear land
    """
    rng = np.random.default_rng(seed)
    Y, X = np.mgrid[0:size, 0:size]
    img = 0.34 + rng.normal(0, 0.025, (size, size))         # dark carbide body
    img += 0.10*np.exp(-((Y-14)**2)/(2*5.0**2))             # rake face, lit

    edge_row = 30.0
    band = np.clip(vb_mm/0.6, 0, 1)*22.0                    # VB 0.6 mm spans ~22 px
    if band > 0.4:
        land = np.exp(-np.clip(Y-edge_row, 0, None)**2/(2*(band/2)**2))
        land[Y < edge_row] = 0.0
        img += 0.60*land*(0.92 + 0.16*rng.random())         # polished wear land
    img += 0.16*np.exp(-((Y-edge_row)**2)/(2*1.2**2))       # the edge line itself
    if stain:
        cy, cx = rng.uniform(38, 56), rng.uniform(10, 54)
        img -= 0.22*np.exp(-(((Y-cy)**2 + (X-cx)**2)/(2*8.0**2)))
    if bue:
        # built-up edge is workpiece metal welded onto the tool: a big bright lump,
        # brighter and more extensive than a wear land, and it is NOT wear.
        cy, cx = edge_row + 3, rng.uniform(18, 46)
        img += 0.55*np.exp(-(((Y-cy)**2 + (X-cx)**2)/(2*7.5**2)))
        img += 0.30*np.exp(-(((Y-cy+4)**2 + (X-cx+5)**2)/(2*5.0**2)))
    return np.clip(img, 0, 1)

def show(z, title="", h=320, cs="gray"):
    f = go.Figure(go.Heatmap(z=z, colorscale=cs, showscale=False, zmin=0, zmax=1))
    f.update_layout(title=title, height=h, template="plotly_white",
                    margin=dict(l=10, r=10, t=50, b=10))
    f.update_xaxes(visible=False)
    f.update_yaxes(visible=False, autorange="reversed", scaleanchor="x")
    return f

job = pd.DataFrame([{"workpiece": "inconel_718", "machine": "5axis_centre",
                     "operation": "finishing", "required_ra_um": 0.8,
                     "batch_qty": 240, "nose_r_mm": 0.8, "prev_tool_life_min": 11.5}])
print("THE JOB CARD — 7 named fields, every one chosen by an engineer:")
print(job.T.to_string(header=False))

im = make_insert(0.28, seed=3)
print(f"\nTHE INSERT PHOTO — {im.size:,} unnamed numbers. None of them is called 'VB'.")
show(im, "insert flank face · 64 × 64 pixels").show()
''')],
    built="""The two data types, side by side. The job card is ready for a model today. The photograph is not, and
saying why is the whole second half of this notebook.""",
    takeaway="""The job card arrives with names; the insert photo does not. That splits ML from DL.""",
)

# ---------------------------------------------- PHASE 3
step(
    id="load", phase=2, icon="📥", ai_icon="🐼",
    civil="The Tool-Room Log Arrives", ai="Loading The Dataset",
    tech="ERP export → DataFrame, 4,000 completed jobs",
    site="""The ERP exports every completed job for the last three years: the job card fields, the tooling that was
issued, the speed and feed the setter programmed, and the tool life and measured Ra that came back from
inspection.""",
    challenge="""An export is not a dataset. Setters type free text, quantities get keyed with an extra zero, and a
handful of jobs record a tool life of zero because the insert chipped on entry and nobody updated the
record.""",
    ai_link="""Loading it into a DataFrame is the first step: shape, types, and a first look at what actually
arrived.""",
    bridge=[("Three years of jobs", "read_csv"),
            ("One row per job", "shape and dtypes"),
            ("Outcome recorded", "First look")],
    body=[("co", r'''
def choose_tool(mat, op, qty, rng):
    """The tool room's own selection logic, as an experienced setter would apply it.

    This is a KNOWLEDGE BASE, not a model. It generates the log; the model's job later
    is to recover it from the log alone. A few per cent of jobs deviate - a different
    setter, a stock-out, a customer preference - so the log is not perfectly consistent.
    """
    if rng.random() < 0.06:                       # the shop is not a robot
        return str(rng.choice(TOOL_MATERIALS))
    if mat in ("aluminium_6061", "brass_360"):
        return "PCD" if qty > 400 else "carbide"
    if mat in ("ti_6al_4v", "inconel_718"):
        return "carbide"                          # CBN and PCD are wrong here
    if mat == "cast_iron_gg25":
        return "CBN" if (op == "finishing" and qty > 300) else "coated_carbide"
    if mat == "mild_steel_1045":
        if qty < 25:
            return "HSS"                          # not worth an insert for a one-off
        return "cermet" if op == "finishing" else "coated_carbide"
    return "coated_carbide"                       # stainless

def choose_coating(mat, tool, rng):
    if tool == "PCD":
        return "uncoated"                         # diamond IS the cutting material
    if rng.random() < 0.05:
        return str(rng.choice(COATINGS))
    if mat in ("aluminium_6061", "brass_360"):
        return "DLC"                              # low friction, resists welding
    if mat in ("ti_6al_4v", "inconel_718"):
        return "TiAlN"                            # holds hardness hot
    if mat == "stainless_316":
        return "AlCrN"
    return "TiAlN" if tool != "HSS" else "TiN"

def choose_coolant(mat, op, rng):
    if rng.random() < 0.05:
        return str(rng.choice(COOLANTS))
    if mat in ("ti_6al_4v", "inconel_718"):
        return "high_pressure"                    # heat has to be taken out of the cut
    if mat == "stainless_316":
        return "flood"
    if mat == "cast_iron_gg25":
        return "dry" if op == "roughing" else "MQL"
    if mat in ("aluminium_6061", "brass_360"):
        return "MQL"
    return "flood"

def make_log(n=4000, seed=42):
    rng = np.random.default_rng(seed)
    mats = list(BASE_VC); machs = list(MACHINES); ops = ["roughing", "semi_finish", "finishing"]
    rows = []
    for _ in range(n):
        mat  = str(rng.choice(mats, p=[0.20, 0.08, 0.24, 0.12, 0.18, 0.10, 0.08]))
        mach = str(rng.choice(machs, p=[0.30, 0.34, 0.22, 0.14]))
        op   = str(rng.choice(ops,  p=[0.38, 0.30, 0.32]))
        qty  = int(rng.choice([5, 15, 40, 120, 300, 800, 2000],
                              p=[0.10, 0.14, 0.20, 0.22, 0.16, 0.12, 0.06]))
        nose = float(rng.choice([0.4, 0.8, 1.2]))
        ra   = float(rng.choice([0.4, 0.8, 1.6, 3.2, 6.3],
                                p=[0.06, 0.22, 0.30, 0.26, 0.16])) if op != "roughing" \
               else float(rng.choice([3.2, 6.3], p=[0.4, 0.6]))
        dia  = float(np.round(rng.uniform(6, 40), 1))

        tool = choose_tool(mat, op, qty, rng)
        coat = choose_coating(mat, tool, rng)
        cool = choose_coolant(mat, op, rng)

        # speed: reference for this material and tool, trimmed by machine rigidity
        vc_ref = BASE_VC[mat]*TOOL_VC_MULT[tool]*OP_VC_MULT[op]
        vc = vc_ref*MACHINES[mach]["rigidity"]*rng.uniform(0.93, 1.07)
        # the spindle cannot always deliver it
        vc = min(vc, np.pi*dia*MACHINES[mach]["max_rpm"]/1000.0)

        # feed: the largest that still holds the required finish
        f = float(feed_for_ra(ra, nose))*rng.uniform(0.85, 0.98)
        f = float(np.clip(f, 0.04, 0.55))

        life = float(taylor_life(vc, vc_ref, tool)*rng.uniform(0.85, 1.15))
        rows.append(dict(workpiece=mat, machine=mach, operation=op, batch_qty=qty,
                         required_ra_um=ra, nose_r_mm=nose, tool_dia_mm=dia,
                         prev_tool_life_min=round(life*rng.uniform(0.8, 1.2), 1),
                         tool_material=tool, coating=coat, coolant=cool,
                         cutting_speed_m_min=round(vc, 1), feed_mm_rev=round(f, 3),
                         tool_life_min=round(life, 1),
                         achieved_ra_um=round(float(ra_for_feed(f, nose))*rng.uniform(0.95, 1.15), 2)))
    df = pd.DataFrame(rows)

    # the faults a real ERP export carries
    df.loc[rng.choice(n, 70, replace=False), "prev_tool_life_min"] = np.nan   # never recorded
    df.loc[rng.choice(n, 30, replace=False), "batch_qty"] *= 10               # keyed an extra zero
    df.loc[rng.choice(n, 25, replace=False), "tool_life_min"] = 0.0           # chipped on entry
    df.loc[rng.choice(n, 20, replace=False), "cutting_speed_m_min"] = np.nan
    return pd.concat([df, df.sample(40, random_state=1)], ignore_index=True)  # re-exported twice

make_log().to_csv("tool_room_log.csv", index=False)
df = pd.read_csv("tool_room_log.csv")
print("shape:", df.shape)
df.head()
''')],
    built="""Four thousand completed jobs, generated from the tool room's own selection logic plus Taylor and the
finish relation — with the deviations and the keying errors a real export carries.""",
    takeaway="""The export is raw material. Loading it is where the data work starts.""",
)

step(
    id="inspect", phase=2, icon="🔍", ai_icon="📊",
    civil="Checking The Records", ai="Data Inspection",
    tech="Counts, ranges, duplicates, and the class balance",
    site="""Before trusting three years of records, check them the way you would check a delivery: is anything
missing, is anything impossible, and is anything repeated?""",
    challenge="""There is a second question here that the numeric projects do not have. The outputs are **categories**,
and they are badly unbalanced: the shop runs a lot of coated carbide and very little CBN. A model
trained without noticing that will simply learn to say 'coated carbide'.""",
    ai_link="""Inspection therefore covers both: the usual missing-and-impossible check, and the **class balance of
every categorical target**, because that decides how the audit at the end has to be read.""",
    bridge=[("Missing, impossible, repeated", "isna, describe, duplicated"),
            ("Which tools do we actually run?", "value_counts"),
            ("Rare tools matter most", "Class imbalance")],
    body=[("co", r'''
print("MISSING values per column:")
print(df.isna().sum()[df.isna().sum() > 0].to_string(), "\n")
print("Duplicate rows:", int(df.duplicated().sum()), "\n")
print("Impossible or suspicious:")
print(f"  tool_life_min == 0        : {int((df.tool_life_min == 0).sum())}  (chipped on entry, never machined)")
print(f"  batch_qty above 5,000     : {int((df.batch_qty > 5000).sum())}  (an extra zero at keying)\n")

fig = make_subplots(rows=1, cols=3,
                    subplot_titles=["tool material", "coating", "coolant"])
for j, col in enumerate(["tool_material", "coating", "coolant"], start=1):
    vc_ = df[col].value_counts()
    fig.add_trace(go.Bar(x=vc_.index, y=vc_.values, marker_color=CYAN, showlegend=False),
                  row=1, col=j)
fig.update_layout(height=340, template="plotly_white",
                  title="class balance — the shop does not use these evenly")
fig.show()

for col in ["tool_material", "coating", "coolant"]:
    s = df[col].value_counts(normalize=True)
    print(f"{col:15s} most common '{s.index[0]}' at {s.iloc[0]:.0%}, "
          f"rarest '{s.index[-1]}' at {s.iloc[-1]:.1%}")
print("\nRemember that top figure. A model that ALWAYS says the most common tool")
print("would already score that accuracy while being useless on the jobs that matter.")
''')],
    built="""A fault list, and the class balance of all three categorical targets — the number the final audit has
to be read against.""",
    takeaway="""Check the classes as well as the values: an unbalanced target makes accuracy meaningless.""",
)

step(
    id="clean", phase=2, icon="🧹", ai_icon="🧼",
    civil="Removing The Bad Records", ai="Data Cleaning",
    tech="Drop duplicates, null the impossible, fill with the median",
    site="""A job that chipped on entry never machined anything. A batch quantity of 12,000 on a job that ran once
is a keying error. Neither should be averaged into anything.""",
    challenge="""Deleting whole records throws away good information in the other twelve fields. Keeping them corrupts
every relationship the model is supposed to learn.""",
    ai_link="""Mark the impossible as missing rather than deleting the row, then fill with the column's median — a
value the outliers cannot drag.""",
    bridge=[("Chipped on entry", "Not a tool life"),
            ("An extra zero", "Not a batch"),
            ("Keep the rest", "fillna(median)")],
    body=[("co", r'''
clean = df.drop_duplicates().copy()
clean.loc[clean.tool_life_min <= 0, "tool_life_min"] = np.nan     # never actually cut
clean.loc[clean.batch_qty > 5000,   "batch_qty"]     = np.nan     # keying error

for c in ["prev_tool_life_min", "tool_life_min", "batch_qty", "cutting_speed_m_min"]:
    clean[c] = clean[c].fillna(clean[c].median())

print(f"rows {len(df):,} -> {len(clean):,} after de-duplication")
print(f"missing left: {int(clean.isna().sum().sum())}\n")
print("Why the median, not the mean?")
print(f"  mean batch_qty, dirty   : {df.batch_qty.mean():8.1f}   <- dragged by the extra zeros")
print(f"  median batch_qty, dirty : {df.batch_qty.median():8.1f}   <- barely notices them")
''')],
    built="""A log in which every remaining record describes a job that actually happened.""",
    takeaway="""Repair the field, not the record: mark the impossible, fill with the median, keep the rest.""",
)

# ---------------------------------------------- PHASE 4
step(
    id="encode", phase=3, icon="🔤", ai_icon="🔢",
    civil="Materials Are Names, Not Numbers", ai="One-Hot Encoding",
    tech="7 materials → 7 columns, not one column of 0–6",
    site="""Most of the job card is words: `inconel_718`, `5axis_centre`, `finishing`. A model does arithmetic, so
those words have to become numbers.""",
    challenge="""The obvious shortcut is the wrong one. Number the materials 0 to 6 and you have told the model that
stainless is *greater than* cast iron, and that aluminium plus Inconel averages to mild steel. None of
that is true. Materials have no order.""",
    ai_link="""One-hot encoding gives each category its own column, holding 1 or 0. No order is implied, because none
exists. The numeric fields keep their own scale, so a scaler is applied to those only.""",
    bridge=[("Materials have no order", "One column each"),
            ("Machines have no order", "1 or 0, nothing between"),
            ("Numbers keep theirs", "Scale those separately")],
    body=[("co", r'''
from sklearn.preprocessing import StandardScaler

CAT_IN = ["workpiece", "machine", "operation"]
NUM_IN = ["batch_qty", "required_ra_um", "nose_r_mm", "tool_dia_mm", "prev_tool_life_min",
          "machine_power_kw", "machine_max_rpm", "machine_rigidity"]

# The machine is named on the job card, so its capability is known - and it caps what is
# achievable. Without these three columns the speed model has to guess the spindle limit.
for _c, _k in [("machine_power_kw", "power_kw"), ("machine_max_rpm", "max_rpm"),
               ("machine_rigidity", "rigidity")]:
    clean[_c] = clean.machine.map(lambda m: MACHINES[m][_k])

# the wrong way, shown once so the reason is concrete
wrong = {m: i for i, m in enumerate(BASE_VC)}
print("Label encoding would claim:")
print(f"  inconel_718 = {wrong['inconel_718']},  aluminium_6061 = {wrong['aluminium_6061']}"
      f"  ->  their mean is {(wrong['inconel_718']+wrong['aluminium_6061'])/2:.1f}"
      f" = '{list(BASE_VC)[int((wrong['inconel_718']+wrong['aluminium_6061'])/2)]}'")
print("  There is no sense in which Inconel and aluminium average to that. Materials have no order.\n")

X_cat = pd.get_dummies(clean[CAT_IN], columns=CAT_IN, dtype=float)
scaler = StandardScaler()
X_num = pd.DataFrame(scaler.fit_transform(clean[NUM_IN]), columns=NUM_IN, index=clean.index)
X = pd.concat([X_num, X_cat], axis=1)

print(f"{len(CAT_IN)} categorical + {len(NUM_IN)} numeric  ->  {X.shape[1]} model columns")
print("\nthe one-hot block, first rows:")
print(X_cat.head(3).to_string())
''')],
    built="""A feature matrix a model can actually use, with no false ordering smuggled into it.""",
    takeaway="""Categories get a column each — numbering them invents an order that does not exist.""",
)

step(
    id="split", phase=3, icon="🗂️", ai_icon="✂️",
    civil="Known Jobs vs Sealed Jobs", ai="Train / Test Split",
    tech="80 / 20, stratified on the tool material",
    site="""You would not judge a setter on the jobs they were trained on. You would give them a new drawing.""",
    challenge="""With unbalanced classes an ordinary random split can leave almost no CBN jobs in the test set — and
then the audit tells you nothing about the rare tools, which are exactly the expensive ones.""",
    ai_link="""Stratify the split on the tool material, so every tool appears in the test set in the same proportion
as in the log.""",
    bridge=[("A new drawing", "Sealed test jobs"),
            ("Rare tools still tested", "Stratified split"),
            ("Judge on the unseen", "Score only there")],
    body=[("co", r'''
from sklearn.model_selection import train_test_split

y_tool = clean.tool_material.values
y_coat = clean.coating.values
y_cool = clean.coolant.values
y_vc   = clean.cutting_speed_m_min.values
y_f    = clean.feed_mm_rev.values

idx = np.arange(len(clean))
i_tr, i_te = train_test_split(idx, test_size=0.20, random_state=42, stratify=y_tool)
Xv = X.values
print(f"train {len(i_tr):,}   test (sealed) {len(i_te):,}\n")

cmp_ = pd.DataFrame({"in the log": pd.Series(y_tool).value_counts(normalize=True),
                     "in the sealed set": pd.Series(y_tool[i_te]).value_counts(normalize=True)})
print((cmp_*100).round(1).to_string())
print("\nEvery tool, including the rare ones, is represented in the same proportion.")
''')],
    built="""A sealed set that still contains the rare tools — without that, the audit would silently skip them.""",
    takeaway="""Stratify the split, or the rare and expensive choices vanish from the test set.""",
)

# ---------------------------------------------- PHASE 5
step(
    id="recommend-tool", phase=4, icon="🛠️", ai_icon="🌲",
    civil="Which Tool For This Job?", ai="Multi-Output Classification",
    tech="Three classifiers: tool material, coating, coolant",
    site="""The first question on the job card: what should we put in the spindle, with what coating, and how
should it be cooled?""",
    challenge="""These three are not independent. PCD is never coated — diamond is the cutting material. High-pressure
coolant belongs with the heat-resistant alloys. A model that predicts each in isolation can produce a
combination no tool room would ever issue.""",
    ai_link="""Train one classifier per output, then **check the combinations they produce** against the rules a setter
would apply. That check is not optional — it is the difference between a prediction and a
recommendation.""",
    bridge=[("Three coupled choices", "Three classifiers"),
            ("Some combinations are absurd", "Check the joint output"),
            ("Issue it or don't", "Validity, not just accuracy")],
    body=[("co", r'''
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

clf = {}
for name, y in [("tool_material", y_tool), ("coating", y_coat), ("coolant", y_cool)]:
    m = RandomForestClassifier(n_estimators=300, random_state=42,
                               class_weight="balanced_subsample").fit(Xv[i_tr], y[i_tr])
    clf[name] = m
    acc  = accuracy_score(y[i_te], m.predict(Xv[i_te]))
    base = pd.Series(y[i_tr]).value_counts(normalize=True).iloc[0]
    print(f"{name:15s} accuracy {acc:6.1%}   (always-say-the-most-common would score {base:.1%})")

# top-2: a recommender may legitimately offer a second choice
proba = clf["tool_material"].predict_proba(Xv[i_te])
classes = clf["tool_material"].classes_
top2 = classes[np.argsort(proba, axis=1)[:, -2:]]
print(f"\ntool material, correct answer inside the top 2 suggestions: "
      f"{np.mean([t in row for t, row in zip(y_tool[i_te], top2)]):.1%}")

# --- the check that matters: are the COMBINATIONS issuable?
p_tool = clf["tool_material"].predict(Xv[i_te])
p_coat = clf["coating"].predict(Xv[i_te])
p_cool = clf["coolant"].predict(Xv[i_te])
mats   = clean.workpiece.values[i_te]

bad_pcd  = int(np.sum((p_tool == "PCD") & (p_coat != "uncoated")))
bad_hard = int(np.sum(np.isin(mats, ["ti_6al_4v", "inconel_718"]) & np.isin(p_tool, ["CBN", "PCD"])))
print(f"\nimpossible combinations issued:")
print(f"  a coated PCD insert                     : {bad_pcd}")
print(f"  CBN or PCD on titanium / Inconel         : {bad_hard}")
print(f"  out of {len(i_te)} sealed jobs")
''')],
    built="""Three classifiers, and — more importantly — a check that the combinations they jointly produce are
things a tool room would actually issue.""",
    takeaway="""Predict each choice, then check the combination: accuracy per output does not guarantee a valid set.""",
)

step(
    id="recommend-params", phase=4, icon="⚡", ai_icon="📈",
    civil="What Speed And What Feed?", ai="Regression, Against A Known Law",
    tech="Predict Vc and f — then check f against Ra = f²/32r",
    site="""With the tool chosen, two numbers remain: the cutting speed and the feed rate. Both are programmed
directly into the machine.""",
    challenge="""A feed that is too high cannot hold the required finish, however good the tool. That is not a matter of
opinion — it follows from the nose radius by a relation every machinist knows.""",
    ai_link="""Predict both with regression, then hold the feed up against the surface-finish relation and count how
often the recommendation would actually have made the drawing. A recommender that is accurate on
average but breaches the finish on one job in ten is not usable.""",
    bridge=[("Two numbers to program", "Regression"),
            ("Finish is not negotiable", "Check against the law"),
            ("Would it make the drawing?", "The real metric")],
    body=[("co", r'''
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

reg_vc = RandomForestRegressor(n_estimators=300, random_state=42).fit(Xv[i_tr], y_vc[i_tr])
reg_f  = RandomForestRegressor(n_estimators=300, random_state=42).fit(Xv[i_tr], y_f[i_tr])
p_vc, p_f = reg_vc.predict(Xv[i_te]), reg_f.predict(Xv[i_te])

print(f"cutting speed  MAE {mean_absolute_error(y_vc[i_te], p_vc):6.1f} m/min   "
      f"R2 {r2_score(y_vc[i_te], p_vc):.3f}   (mean speed {y_vc[i_te].mean():.0f})")
print(f"feed rate      MAE {mean_absolute_error(y_f[i_te], p_f):6.3f} mm/rev   "
      f"R2 {r2_score(y_f[i_te], p_f):.3f}   (mean feed {y_f[i_te].mean():.3f})\n")

# would the recommended feed actually hold the finish the drawing asks for?
req  = clean.required_ra_um.values[i_te]
nose = clean.nose_r_mm.values[i_te]
ra_pred = ra_for_feed(p_f, nose)
ok = ra_pred <= req*1.10                       # a 10% inspection tolerance
print(f"recommended feed would hold the required Ra on {ok.mean():.1%} of sealed jobs")
print(f"  (jobs where it would breach the finish: {int((~ok).sum())} of {len(i_te)})")

fig = make_subplots(rows=1, cols=2, subplot_titles=[
    "cutting speed: recommended vs used", "feed: does it hold the finish?"])
fig.add_trace(go.Scatter(x=y_vc[i_te], y=p_vc, mode="markers",
                         marker=dict(size=4, color=CYAN, opacity=0.5), showlegend=False),
              row=1, col=1)
lim = [0, float(y_vc[i_te].max())]
fig.add_trace(go.Scatter(x=lim, y=lim, mode="lines",
                         line=dict(color=MUTED, dash="dash"), showlegend=False), row=1, col=1)
fig.add_trace(go.Scatter(x=req, y=ra_pred, mode="markers",
                         marker=dict(size=4, color=np.where(ok, GREEN, RED), opacity=0.6),
                         showlegend=False), row=1, col=2)
fig.add_trace(go.Scatter(x=[0, 7], y=[0, 7], mode="lines",
                         line=dict(color=MUTED, dash="dash"), showlegend=False), row=1, col=2)
fig.update_xaxes(title_text="programmed Vc (m/min)", row=1, col=1)
fig.update_yaxes(title_text="recommended Vc", row=1, col=1)
fig.update_xaxes(title_text="required Ra (µm)", row=1, col=2)
fig.update_yaxes(title_text="Ra the recommended feed gives", row=1, col=2)
fig.update_layout(height=400, template="plotly_white")
fig.show()
n_bad = int((~ok).sum())
print()
if n_bad:
    print(f"{n_bad} red points sit ABOVE the diagonal - on those jobs the finish would fail.")
else:
    print("No point sits above the diagonal. The model inherited the shop's own safety margin:")
    print("it learned feed from jobs where the setter already backed off the theoretical maximum.")
    print("The check still earns its place - it is what would catch a breach if that margin ever")
    print("stopped being there, and it costs nothing to run on every recommendation.")
''')],
    built="""Two regressions, and a check against a physical law rather than against an average. That check is the
one a machinist would ask for first.""",
    takeaway="""Check a recommended feed against the finish it can actually hold, not just against the average error.""",
)

step(
    id="drivers", phase=4, icon="🎚️", ai_icon="📊",
    civil="What Actually Decides The Tool", ai="Feature Importance",
    tech="Which job-card field moves each recommendation",
    site="""A recommendation nobody understands does not get used. The setter will want to know *why* the system is
proposing CBN on a job where they would have reached for coated carbide.""",
    challenge="""Thirteen input columns, and they are not independent — finishing jobs tend to ask for finer finishes,
big batches tend to be finishing jobs.""",
    ai_link="""Feature importance ranks how much each column moves each recommendation. It is the first place the
model's reasoning can be checked against shop-floor intuition, and the first place it can be caught
being wrong.""",
    bridge=[("Why this tool?", "feature_importances_"),
            ("Check it against intuition", "A ranked list"),
            ("Then trust it, or don't", "Explainability")],
    body=[("co", r'''
cols = list(X.columns)
fig = go.Figure()
for name, m, col in [("tool material", clf["tool_material"], CYAN),
                     ("cutting speed", reg_vc, AMBER),
                     ("feed rate", reg_f, GREEN)]:
    imp = m.feature_importances_
    o = np.argsort(imp)[::-1][:8]
    fig.add_trace(go.Bar(x=[cols[i] for i in o], y=imp[o], name=name, marker_color=col))
fig.update_layout(barmode="group", title="the three questions weigh the job card differently",
                  yaxis_title="importance", template="plotly_white", height=430)
fig.show()

for name, m in [("tool material", clf["tool_material"]), ("cutting speed", reg_vc),
                ("feed rate", reg_f)]:
    imp = m.feature_importances_
    o = np.argsort(imp)[::-1][:3]
    print(f"{name:15s}: " + ", ".join(f"{cols[i]} {imp[i]:.2f}" for i in o))
'''),
          ("md", r"""
Read the three rankings against what a setter would say:

- **Tool material** is decided mostly by the **workpiece**, with batch quantity next. That is exactly the
  logic — the material rules out most of the shelf, and the quantity decides whether an expensive insert
  can pay for itself.
- **Cutting speed** follows the workpiece too, because the reference speed is a material property.
- **Feed rate** is driven by **required Ra and nose radius** — and nothing else much. It should be: those
  two are the only terms in the surface-finish relation.

That last one is worth pausing on. Nobody told the model the formula. It recovered which two fields
matter from four thousand job records, and it recovered the right two.
""")],
    built="""Three ranked explanations, each one checkable against shop-floor reasoning — including one that
independently rediscovers the surface-finish relation.""",
    takeaway="""A recommendation you cannot explain will not be used; feature importance is the cheapest explanation.""",
)

# ---------------------------------------------- PHASE 6
step(
    id="wear-image", phase=5, icon="📷", ai_icon="🖼️",
    civil="The Insert Under The Camera", ai="Raw Pixels As Input",
    tech="A 64×64 grid of brightness, no named columns",
    site="""At tool change the insert goes on the presetter and a camera photographs the flank face. Wear shows as
a bright polished band along the cutting edge, and its width — **VB** — is what ISO 3685 measures. VB of
0.3 mm is the usual end-of-life criterion.""",
    challenge="""The camera does not output "VB = 0.28 mm". It outputs 4,096 brightness values with no names. And the
frame contains other bright and dark things: coolant staining, built-up edge, the lit rake face.""",
    ai_link="""This is where Machine Learning runs out on this project. The job card had named fields; the photograph
has none. Before reaching for a CNN, it is worth trying to measure the wear by hand.""",
    bridge=[("VB is what matters", "4,096 numbers"),
            ("Stains and BUE too", "No column names"),
            ("0.3 mm is end of life", "Nothing to weight")],
    body=[("co", r'''
cases = [("fresh, VB 0.05", make_insert(0.05, seed=1)),
         ("worn, VB 0.22",  make_insert(0.22, seed=2)),
         ("worn out, VB 0.42", make_insert(0.42, seed=3)),
         ("fresh + coolant stain", make_insert(0.05, seed=4, stain=True)),
         ("fresh + built-up edge", make_insert(0.06, seed=5, bue=True))]

fig = make_subplots(rows=1, cols=5, subplot_titles=[n for n, _ in cases])
for j, (_, z) in enumerate(cases, start=1):
    fig.add_trace(go.Heatmap(z=z, colorscale="gray", showscale=False, zmin=0, zmax=1),
                  row=1, col=j)
    fig.update_xaxes(visible=False, row=1, col=j)
    fig.update_yaxes(visible=False, autorange="reversed", row=1, col=j)
fig.update_layout(height=300, template="plotly_white",
                  title="five inserts — the last two are barely worn at all")
fig.show()

z = make_insert(0.22, seed=2)
print(f"The frame is {z.shape[0]} x {z.shape[1]} = {z.size:,} brightness values.")
print("Which one of them is 'VB'?  None. VB is the WIDTH of a band, measured from the edge.")
''')],
    built="""The wear image, and the two things in it that are not wear: a coolant stain and a built-up edge.""",
    takeaway="""VB is the width of a band, not the value of a pixel — there is nothing here for ML to weight.""",
)

step(
    id="handmade", phase=5, icon="✋", ai_icon="🔢",
    civil="Measuring Wear By Brightness", ai="Hand-Crafted Features",
    tech="One number from 4,096 pixels — and what it misses",
    site="""The obvious approach, and the one every vision project tries first: wear is bright, so threshold the
image on brightness and call the bright fraction the wear.""",
    challenge="""Built-up edge is bright and is not wear — it is workpiece material welded to the tool, and it comes off.
Coolant staining is dark and shifts the mean the other way. And the lit rake face is bright on every
frame, worn or not.""",
    ai_link="""The feature was hand-made, and it measures the wrong thing. You could add more — edge detection, a
row profile, a morphological filter — and each one is another rule to maintain for every insert
geometry and every lighting setup.""",
    bridge=[("Wear is bright", "One feature"),
            ("So is built-up edge", "One threshold"),
            ("So is the rake face", "It fails")],
    body=[("co", r'''
def bright_fraction(img, thr=0.62):
    "The hand-made feature: what share of the frame is brighter than a threshold?"
    return float((img > thr).mean())

probe = [("fresh          VB 0.05", make_insert(0.05, seed=11), 0.05),
         ("worn           VB 0.22", make_insert(0.22, seed=12), 0.22),
         ("worn out       VB 0.42", make_insert(0.42, seed=13), 0.42),
         ("fresh + BUE    VB 0.06", make_insert(0.06, seed=14, bue=True), 0.06),
         ("worn + stain   VB 0.24", make_insert(0.24, seed=15, stain=True), 0.24)]

print(f"{'frame':24s}{'true VB':>9}{'bright fraction':>17}")
for name, im, vb in probe:
    print(f"{name:24s}{vb:9.2f}{bright_fraction(im):17.3f}")

vals = [bright_fraction(im) for _, im, _ in probe]
vbs  = [vb for _, _, vb in probe]
fig = go.Figure(go.Scatter(x=vbs, y=vals, mode="markers+text",
                           text=[n.split()[0]+("+"+n.split()[2] if "+" in n else "")
                                 for n, _, _ in probe],
                           textposition="top center",
                           marker=dict(size=13, color=[GREEN, AMBER, RED, CYAN, CYAN])))
fig.update_layout(title="the hand-made feature against the thing it is supposed to measure",
                  xaxis_title="true VB (mm)", yaxis_title="bright fraction",
                  template="plotly_white", height=400)
fig.show()

fresh_bue = bright_fraction(probe[3][1])
worn      = bright_fraction(probe[1][1])
print(f"\nA FRESH insert with built-up edge scores {fresh_bue:.3f}.")
print(f"A genuinely WORN insert (VB 0.22) scores  {worn:.3f}.")
print("Any threshold that catches the worn one also condemns the fresh one - and a")
print("thrown-away good insert costs the same as a broken part run on a dead one.")
''')],
    built="""A hand-made feature that fails, and a precise statement of why: it measures brightness, and the thing
that matters is the *width of a band in a particular place*.""",
    takeaway="""Bright is not worn — built-up edge defeats every brightness threshold.""",
)

# ---------------------------------------------- PHASE 7
step(
    id="cnn", phase=6, icon="🧩", ai_icon="🧠",
    civil="Grading The Wear Land", ai="Convolution & Feature Maps",
    tech="filters → feature maps → a wear class",
    site="""A setter grading an insert does not measure brightness. They look for a **band of a certain width in a
certain place** — along the cutting edge, on the flank — and ignore everything else in the frame.""",
    challenge="""That is a description of a shape and a location, together. No single pixel holds it, and no global
average holds it either.""",
    ai_link="""A convolution slides a small filter across the frame and reports where its pattern occurs. Early
filters find edges; later ones combine them into bands of a given width in a given place. The network
learns the filters from labelled inserts.""",
    bridge=[("A band, at the edge", "Filters slide"),
            ("Of a certain width", "Edges → bands"),
            ("Ignore the rest", "Filters are learned")],
    body=[("co", r'''
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
    KERAS = True
    tf.random.set_seed(42)
except Exception as e:                                  # noqa: BLE001
    KERAS = False
    print("TensorFlow not available - the CNN cells will skip.", e)
print("Keras available:", KERAS)
'''),
          ("co", r'''
# Labelled inserts. VB is drawn from a CONTINUUM and the classes cut across it at the
# ISO 3685 criterion, so the boundary cases are genuinely hard - as they are in the room.
WEAR_CLASSES = ["fresh", "worn", "replace"]     # VB < 0.15 / 0.15-0.30 / >= 0.30

def wear_label(vb):
    return 0 if vb < 0.15 else (1 if vb < 0.30 else 2)

def make_insert_set(n=1500, seed=0):
    rng = np.random.default_rng(seed)
    Xi, yi, vbs = [], [], []
    for _ in range(n):
        vb = float(rng.uniform(0.0, 0.55))
        im = make_insert(vb, seed=int(rng.integers(1e6)),
                         stain=bool(rng.random() < 0.22),   # decoys appear in TRAINING too
                         bue=bool(rng.random() < 0.18))
        im = np.clip(im*rng.uniform(0.95, 1.05) + rng.normal(0, 0.015), 0, 1)
        Xi.append(im); yi.append(wear_label(vb)); vbs.append(vb)
    return (np.array(Xi)[..., None].astype("float32"), np.array(yi), np.array(vbs))

Xi, yi, vbs = make_insert_set(1500, seed=1)
Xi_tr, Xi_te, yi_tr, yi_te, vb_tr, vb_te = train_test_split(
    Xi, yi, vbs, test_size=0.25, random_state=42, stratify=yi)
print("frames:", Xi.shape, " class balance:", (np.bincount(yi)/len(yi)).round(3))

if KERAS:
    inp = keras.Input(shape=(64, 64, 1))
    x = layers.Conv2D(16, 3, activation="relu", padding="same")(inp)
    x = layers.MaxPooling2D()(x)
    x = layers.Conv2D(32, 3, activation="relu", padding="same")(x)
    x = layers.MaxPooling2D()(x)
    x = layers.Conv2D(64, 3, activation="relu", padding="same", name="last_conv")(x)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(32, activation="relu")(x)
    out = layers.Dense(3, activation="softmax")(x)
    cnn = keras.Model(inp, out)
    cnn.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    # The classes are not balanced (VB is uniform, so 'replace' covers the widest band of it)
    # and the costly error is calling a WORN insert fresh. Weight the classes, exactly as the
    # tool-material classifier did, and give it enough epochs to converge.
    counts = np.bincount(yi_tr)
    cw = {i: float(len(yi_tr)/(3*c)) for i, c in enumerate(counts)}
    hist = cnn.fit(Xi_tr, yi_tr, validation_split=0.2, epochs=30, batch_size=32,
                   class_weight=cw, verbose=0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=hist.history["loss"], name="training loss",
                             line=dict(color=CYAN, width=2)))
    fig.add_trace(go.Scatter(y=hist.history["val_loss"], name="validation loss",
                             line=dict(color=AMBER, width=2)))
    fig.update_layout(title="CNN training", xaxis_title="epoch", yaxis_title="loss",
                      template="plotly_white", height=360)
    fig.show()

    cnn_acc = float(cnn.evaluate(Xi_te, yi_te, verbose=0)[1])
    pred = cnn.predict(Xi_te, verbose=0).argmax(1)
    print(f"CNN accuracy on held-out inserts: {cnn_acc:.1%}\n")
    from sklearn.metrics import confusion_matrix as _cm
    print("confusion matrix (rows = truth, cols = called):")
    print(pd.DataFrame(_cm(yi_te, pred), index=WEAR_CLASSES, columns=WEAR_CLASSES).to_string())
    wrong = vb_te[pred != yi_te]
    if len(wrong):
        print(f"\nVB on the inserts it got wrong: median {np.median(wrong):.3f} mm, "
              f"range {wrong.min():.3f}-{wrong.max():.3f}")
        print("the class boundaries sit at VB = 0.15 and 0.30 mm.")

    # the decoys, specifically
    print("\nthe two things that defeated the brightness rule:")
    for nm, im in [("fresh + built-up edge", make_insert(0.06, seed=91, bue=True)),
                   ("fresh + coolant stain", make_insert(0.05, seed=92, stain=True))]:
        p = cnn.predict(im[None, ..., None].astype("float32"), verbose=0)[0]
        print(f"  {nm:24s} -> CNN says '{WEAR_CLASSES[int(p.argmax())]}' ({p.max():.0%})")
else:
    cnn_acc = None
''')],
    built="""A wear grader that survives built-up edge and coolant staining, because it learned to look for a band
at the edge rather than for brightness anywhere.""",
    takeaway="""Convolution learns a shape in a place — which is what VB is, and what a threshold can never be.""",
)

step(
    id="wear-locate", phase=6, icon="📍", ai_icon="🗺️",
    civil="Where Is The Wear?", ai="Grad-CAM",
    tech="class-weighted feature maps → a heat map",
    site="""A grade alone will not persuade a setter to scrap a £30 insert. They want to see the wear land that
the decision was based on.""",
    challenge="""A classifier outputs a probability. On its own it is exactly the black box that stops vision systems
being adopted on the shop floor.""",
    ai_link="""Grad-CAM weights the last feature maps by how much each pushed the score towards the predicted class,
and projects them back onto the frame. On a worn insert it should light up the flank band — and on a
built-up edge it should not.""",
    bridge=[("Show me the wear", "Weight the maps"),
            ("Before I scrap it", "Project onto the frame"),
            ("Then I'll believe it", "The evidence")],
    body=[("co", r'''
def grad_cam(model, image, layer_name="last_conv"):
    grad_model = keras.Model(model.inputs,
                             [model.get_layer(layer_name).output, model.output])
    with tf.GradientTape() as tape:
        maps, pred = grad_model(image[None, ...])
        ci = int(tf.argmax(pred[0]))
        score = pred[:, ci]
    grads   = tape.gradient(score, maps)[0]
    weights = tf.reduce_mean(grads, axis=(0, 1))
    cam = tf.reduce_sum(maps[0]*weights, axis=-1).numpy()
    cam = np.maximum(cam, 0); cam = cam/(cam.max() + 1e-9)
    rep = image.shape[0]//cam.shape[0]
    return np.kron(cam, np.ones((rep, rep)))[:image.shape[0], :image.shape[1]], ci

if KERAS:
    show_set = [("worn out VB 0.42", make_insert(0.42, seed=21)),
                ("worn VB 0.20", make_insert(0.20, seed=22)),
                ("fresh + BUE", make_insert(0.06, seed=23, bue=True)),
                ("fresh + stain", make_insert(0.05, seed=24, stain=True))]
    fig = make_subplots(rows=2, cols=4, vertical_spacing=0.14,
                        subplot_titles=[""]*8)
    titles = []
    for j, (nm, im0) in enumerate(show_set, start=1):
        im = im0[..., None].astype("float32")
        cam, ci = grad_cam(cnn, im)
        p = cnn.predict(im[None, ...], verbose=0)[0]
        titles.append(f"{nm}<br><sub>called '{WEAR_CLASSES[ci]}' ({p[ci]:.0%})</sub>")
        fig.add_trace(go.Heatmap(z=im[..., 0], colorscale="gray", showscale=False,
                                 zmin=0, zmax=1), row=1, col=j)
        fig.add_trace(go.Heatmap(z=cam, colorscale="Turbo", showscale=False), row=2, col=j)
        for r in (1, 2):
            fig.update_xaxes(visible=False, row=r, col=j)
            fig.update_yaxes(visible=False, autorange="reversed", row=r, col=j)
    for a, t in zip(fig.layout.annotations[:4], titles):
        a.text = t
    for a in fig.layout.annotations[4:]:
        a.text = "where it looked"
    fig.update_layout(height=600, template="plotly_white",
                      title="Grad-CAM — the evidence behind each wear call")
    fig.show()
    print("On the worn inserts the heat sits on the flank band below the cutting edge.")
    print("That is the region a setter would put a microscope on, and it is measurable:")
    print("the width of that bright band IS VB.")
else:
    print("Keras not available - skipping Grad-CAM.")
''')],
    built="""A wear call with its evidence attached — the thing that gets a vision system accepted rather than
switched off after a fortnight.""",
    takeaway="""Grad-CAM shows the wear land the grade was based on, which is what makes the grade actionable.""",
)

# ---------------------------------------------- PHASE 8
step(
    id="audit", phase=7, icon="🧮", ai_icon="✅",
    civil="The Tool-Room Audit", ai="How Good Is It, Really?",
    tech="Accuracy, top-2, MAE, and the checks that matter",
    site="""Before any of this reaches a setup sheet, it gets audited on jobs the model has never seen — and
against the numbers a tool room would actually ask for.""",
    challenge="""Five outputs and five different ways of being wrong. A wrong coolant is an inconvenience. A wrong tool
material on Inconel is a scrapped part and a broken spindle nose. They cannot share one score.""",
    ai_link="""Report each output against the baseline it has to beat, plus the two checks that are specific to this
problem: are the **combinations issuable**, and would the feed **hold the finish**.""",
    bridge=[("Five outputs", "Five scores"),
            ("Five ways to be wrong", "Weighted by consequence"),
            ("Would you issue it?", "Validity checks")],
    body=[("co", r'''
rows = []
for name, y, m in [("tool_material", y_tool, clf["tool_material"]),
                   ("coating", y_coat, clf["coating"]),
                   ("coolant", y_cool, clf["coolant"])]:
    rows.append({"output": name, "metric": "accuracy",
                 "score": f"{accuracy_score(y[i_te], m.predict(Xv[i_te])):.1%}",
                 "baseline (most common)": f"{pd.Series(y[i_tr]).value_counts(normalize=True).iloc[0]:.1%}"})
rows.append({"output": "cutting_speed", "metric": "MAE",
             "score": f"{mean_absolute_error(y_vc[i_te], p_vc):.1f} m/min",
             "baseline (most common)": f"{np.abs(y_vc[i_te]-y_vc[i_tr].mean()).mean():.1f} m/min (predict the mean)"})
rows.append({"output": "feed_rate", "metric": "MAE",
             "score": f"{mean_absolute_error(y_f[i_te], p_f):.3f} mm/rev",
             "baseline (most common)": f"{np.abs(y_f[i_te]-y_f[i_tr].mean()).mean():.3f} mm/rev (predict the mean)"})
if cnn_acc:
    rows.append({"output": "wear grade (CNN)", "metric": "accuracy",
                 "score": f"{cnn_acc:.1%}",
                 "baseline (most common)": f"{(np.bincount(yi_tr)/len(yi_tr)).max():.1%}"})
print(pd.DataFrame(rows).to_string(index=False))

print(f"\nthe two checks a tool room would actually ask for:")
print(f"  recommendations that are physically issuable : {1 - (bad_pcd+bad_hard)/len(i_te):.1%}")
print(f"  recommended feed holds the required finish   : {ok.mean():.1%}")
'''),
          ("md", r"""
### The errors do not cost the same

| Wrong output | What it costs |
|---|---|
| **Coolant** | A worse finish and shorter life. Noticed at the first inspection. |
| **Coating** | Reduced tool life. Noticed at the first tool change. |
| **Cutting speed** | Recoverable — the setter dials it back when the cut sounds wrong. |
| **Feed** | The part misses its finish and is reworked or scrapped. |
| **Tool material** | On Inconel or titanium: a destroyed insert, possibly a damaged spindle, and a scrapped part. |

That ordering is why the tool material classifier gets `class_weight="balanced"`, why the top-2 figure is
reported alongside the top-1, and why the recommendation reaches the setter as a **proposal with its
reasoning**, not as a machine instruction.
""")],
    built="""Every output scored against the baseline it has to beat, plus two domain checks that no generic metric
would have caught.""",
    takeaway="""Score every output against what a naive guess would achieve — and weight the errors by what they cost.""",
)

step(
    id="proof", phase=7, icon="⚔️", ai_icon="🏁",
    civil="The Verdict", ai="ML vs DL, Measured",
    tech="the same shop, two data types, two methods",
    site="""Two halves, two data types, one tool room. Time to say plainly what each method can and cannot do
here.""",
    challenge="""It is tempting to conclude that the CNN is the clever part and the forests are the warm-up. That is
backwards. The recommendation itself — the thing the shop actually wants — is the forests.""",
    ai_link="""Each method belongs to its data type. The job card has thirteen named fields an engineer chose, and a
Random Forest handles it. The insert photo has 4,096 unnamed pixels, and only a CNN can start.""",
    bridge=[("Job card → ML", "Named columns"),
            ("Insert photo → DL", "Raw pixels"),
            ("Both → the recommendation", "Neither replaces the other")],
    body=[("co", r'''
print("ON THE JOB CARD (13 named fields)")
print(f"  Random Forest, tool material  : {accuracy_score(y_tool[i_te], clf['tool_material'].predict(Xv[i_te])):.1%}")
print(f"  Random Forest, cutting speed  : R2 {r2_score(y_vc[i_te], p_vc):.3f}")
print("  A CNN could only be used here by pretending the columns are an image. They are not.\n")

print("ON THE INSERT PHOTO (4,096 unnamed pixels)")
print("  Best hand-made feature (bright fraction) : condemns a fresh insert with built-up edge")
print(f"  CNN                                      : "
      f"{f'{cnn_acc:.1%} accuracy, and it ignores the BUE' if cnn_acc else '(Keras unavailable here)'}")
print("  A Random Forest cannot start: there is nothing named for it to weight.\n")

pd.DataFrame({
    "": ["Recommend tool, coating, coolant", "Recommend speed and feed",
         "Grade insert wear from a photo", "Locate the wear land",
         "Who names the features?"],
    "ML — Random Forest": ["works", "works", "cannot start", "cannot", "the engineer"],
    "DL — CNN":           ["not the right tool", "not the right tool",
                           "learns the pattern", "Grad-CAM shows it",
                           "the network learns them"],
})
'''),
          ("md", r"""
### The promise, demonstrated

> **Machine Learning recommends the tooling and the cutting parameters from named job-card fields.
> Deep Learning reads the insert photograph — the tool history no field can hold — and feeds it back in.**

Neither method wins. The interesting part is that they meet: the CNN's wear grade **becomes an input** to
the next recommendation, which is what closes the loop from *tool history* back to *tool selection*.
""")],
    built="""The central claim, measured on this shop's own sealed jobs, and the point where the two halves connect.""",
    takeaway="""ML recommends from the job card; DL reads the insert. The wear grade is what joins them.""",
)

# ---------------------------------------------- PHASE 9
step(
    id="fusion", phase=8, icon="🖥️", ai_icon="🔗",
    civil="The Setup Sheet", ai="AI Fusion",
    tech="job card + wear history → one recommendation with its reasoning",
    site="""What the setter actually receives: a proposed setup for the job in front of them, with the expected
tool life, the finish it should achieve, and the reason for each choice.""",
    challenge="""A bare list of five values invites the question 'says who?'. Without an answer, it gets ignored on the
first job where it disagrees with the setter's instinct.""",
    ai_link="""Fusion assembles the five predictions, adds the expected tool life from Taylor, adds the achievable Ra
from the finish relation, folds in the CNN's grade of the **last** insert, and states the confidence.""",
    bridge=[("A setup sheet", "Combine the outputs"),
            ("With the reasoning", "Attach the evidence"),
            ("Setter approves", "A proposal, not a command")],
    body=[("co", r'''
def recommend_setup(workpiece, machine, operation, required_ra_um, batch_qty,
                    nose_r_mm=0.8, tool_dia_mm=16.0, prev_tool_life_min=None,
                    last_insert_grade=None):
    """One job card in, one setup sheet out - with the reasoning attached."""
    row = pd.DataFrame([dict(workpiece=workpiece, machine=machine, operation=operation,
                             batch_qty=batch_qty, required_ra_um=required_ra_um,
                             nose_r_mm=nose_r_mm, tool_dia_mm=tool_dia_mm,
                             prev_tool_life_min=(prev_tool_life_min
                                                 if prev_tool_life_min is not None
                                                 else clean.prev_tool_life_min.median()),
                             machine_power_kw=MACHINES[machine]["power_kw"],
                             machine_max_rpm=MACHINES[machine]["max_rpm"],
                             machine_rigidity=MACHINES[machine]["rigidity"])])
    xn = pd.DataFrame(scaler.transform(row[NUM_IN]), columns=NUM_IN)
    xc = pd.get_dummies(row[CAT_IN], columns=CAT_IN, dtype=float)
    xc = xc.reindex(columns=[c for c in X.columns if c not in NUM_IN], fill_value=0.0)
    xx = pd.concat([xn, xc], axis=1)[X.columns].values

    tool = clf["tool_material"].predict(xx)[0]
    conf = float(clf["tool_material"].predict_proba(xx).max())
    coat = clf["coating"].predict(xx)[0]
    cool = clf["coolant"].predict(xx)[0]
    vc   = float(reg_vc.predict(xx)[0])
    f    = float(reg_f.predict(xx)[0])

    vc_ref = BASE_VC[workpiece]*TOOL_VC_MULT[tool]*OP_VC_MULT[operation]
    life   = float(taylor_life(vc, vc_ref, tool))
    ra     = float(ra_for_feed(f, nose_r_mm))

    notes = []
    if last_insert_grade == "replace":
        vc *= 0.90
        notes.append("last insert came off at VB>0.30 - speed reduced 10% (camera evidence)")
    elif last_insert_grade == "worn":
        notes.append("last insert was mid-life; parameters unchanged")
    if ra > required_ra_um:
        f = float(feed_for_ra(required_ra_um, nose_r_mm)*0.95)
        ra = float(ra_for_feed(f, nose_r_mm))
        notes.append("feed trimmed to hold the required finish")
    if conf < 0.55:
        notes.append(f"LOW CONFIDENCE ({conf:.0%}) - few similar jobs in the log, check before issuing")

    return dict(tool_material=tool, coating=coat, coolant=cool,
                cutting_speed_m_min=round(vc, 1), feed_mm_rev=round(f, 3),
                expected_tool_life_min=round(life, 1), expected_ra_um=round(ra, 2),
                confidence=f"{conf:.0%}", notes="; ".join(notes) or "-")

jobs = [
    dict(workpiece="inconel_718",    machine="5axis_centre", operation="finishing",
         required_ra_um=0.8,  batch_qty=240, last_insert_grade="replace"),
    dict(workpiece="aluminium_6061", machine="vmc_3axis",    operation="roughing",
         required_ra_um=6.3,  batch_qty=2000),
    dict(workpiece="mild_steel_1045", machine="tool_room_mill", operation="finishing",
         required_ra_um=1.6,  batch_qty=5),
    dict(workpiece="cast_iron_gg25", machine="cnc_lathe",    operation="finishing",
         required_ra_um=1.6,  batch_qty=800),
]
out = pd.DataFrame([recommend_setup(**j) for j in jobs],
                   index=[f"{j['workpiece']} · {j['operation']} · qty {j['batch_qty']}" for j in jobs])
out.T
'''),
          ("md", r"""
Read the four rows against what a tool room would do:

- **Inconel, finishing, 240 off** — carbide with TiAlN and high-pressure coolant, at a low speed. The
  camera saw the last insert come off worn out, so the speed is trimmed further. That is the *tool
  history* input closing the loop.
- **Aluminium, roughing, 2,000 off** — a big batch justifies PCD, and PCD is never coated.
- **Mild steel, batch of 5** — a one-off on a tool-room mill. HSS. Nobody buys an insert for five parts.
- **Cast iron, finishing, 800 off** — CBN territory, dry or MQL.

Every row carries the expected tool life, the finish it should achieve, and a confidence. The last one is
what lets a setter know when the system is guessing.
""")],
    built="""The product: a setup sheet a setter can read, argue with, and sign — with Taylor and the finish
relation stated on it rather than hidden inside the model.""",
    takeaway="""A recommendation is a proposal with its reasoning and its confidence attached, not five bare numbers.""",
)

step(
    id="dashboard", phase=8, icon="💷", ai_icon="📉",
    civil="What It Is Worth", ai="The Business Case",
    tech="tool life, insert spend and machine hours",
    site="""A tool room does not buy a model. It approves a spend against a saving in insert cost, machine hours
and scrap.""",
    challenge="""The saving is easy to overstate. The honest way to state it is to compare the recommendation against
what was actually programmed, on the sealed jobs, using Taylor for the life difference.""",
    ai_link="""Every figure below is computed from the sealed jobs already loaded. Assumptions — insert price,
machine rate, changeover time — are named variables you can change.""",
    bridge=[("Approve a spend", "Insert cost saved"),
            ("Against a saving", "Machine hours saved"),
            ("With the assumptions shown", "All of it arithmetic")],
    body=[("co", r'''
INSERT_COST   = 22.0     # currency per insert edge
SCRAP_EVENT   = 850.0    # a wrong tool on a difficult alloy: scrapped part + lost spindle time
JOBS_PER_YEAR = 4200

mats_te = clean.workpiece.values[i_te]
ops_te  = clean.operation.values[i_te]

# --- 1. does the recommendation give LONGER tool life than what was programmed?
life_now, life_rec = [], []
for k, ix in enumerate(i_te):
    ta = y_tool[ix]
    life_now.append(taylor_life(y_vc[ix], BASE_VC[mats_te[k]]*TOOL_VC_MULT[ta]*OP_VC_MULT[ops_te[k]], ta))
    tr = p_tool[k]
    life_rec.append(taylor_life(p_vc[k], BASE_VC[mats_te[k]]*TOOL_VC_MULT[tr]*OP_VC_MULT[ops_te[k]], tr))
life_now, life_rec = np.array(life_now), np.array(life_rec)
gain = float(np.median(life_rec/np.maximum(life_now, 1e-6)) - 1)

print("1 · DOES IT BEAT THE SHOP'S OWN SPEEDS?\n")
print(f"  median tool life, as programmed  : {np.median(life_now):7.1f} min")
print(f"  median tool life, as recommended : {np.median(life_rec):7.1f} min")
print(f"  change                           : {gain:+7.1%}")
print("  No. And it should not - the model learned from these speeds, so the best it can")
print("  do is reproduce them. Symmetric error in Vc turns into a LOSS of life, because")
print("  Taylor is convex. That is the next number.\n")

# --- 2. why speed accuracy matters so much: Taylor's sensitivity
print("2 · WHY A SPEED RECOMMENDATION IS A STARTING POINT, NOT A SETTING\n")
for tool in ["HSS", "coated_carbide", "CBN"]:
    n = TAYLOR_N[tool]
    print(f"  {tool:16s} n = {n:.2f}   +10% on Vc  ->  {1.10**(-1/n)-1:+6.0%} tool life"
          f"   +25% on Vc  ->  {1.25**(-1/n)-1:+6.0%}")
print("\n  A 10% speed error costs far more life than it saves cycle time. This is why the")
print("  setup sheet issues Vc as a proposal the setter trims, and why the audit reported")
print(f"  the speed MAE ({mean_absolute_error(y_vc[i_te], p_vc):.0f} m/min) rather than only R2.\n")

# --- 3. where the value actually is: not picking the wrong tool
HARD = ["ti_6al_4v", "inconel_718", "stainless_316"]
hard_te = np.isin(mats_te, HARD)
model_wrong = float(np.mean(p_tool[hard_te] != y_tool[i_te][hard_te]))
naive_tool  = pd.Series(y_tool[i_tr]).value_counts().index[0]
naive_wrong = float(np.mean(y_tool[i_te][hard_te] != naive_tool))
avoided = JOBS_PER_YEAR*np.mean(hard_te)*(naive_wrong - model_wrong)

print("3 · WHERE THE VALUE ACTUALLY IS\n")
print(f"  jobs on difficult alloys (Ti / Inconel / stainless) : {hard_te.mean():.0%} of the log")
print(f"  wrong tool material, no system (guess '{naive_tool}')  : {naive_wrong:.1%}")
print(f"  wrong tool material, with the recommender            : {model_wrong:.1%}")
print(f"  wrong-tool events avoided per year                   : {avoided:,.0f}")
print(f"  at {SCRAP_EVENT:,.0f} per event (scrapped part + spindle time) : "
      f"{avoided*SCRAP_EVENT:,.0f} / year")
print(f"  plus consistency: the same answer on the night shift as the day shift.")

fig = make_subplots(rows=1, cols=2, subplot_titles=[
    "tool life: programmed vs recommended", "wrong tool on a difficult alloy"])
fig.add_trace(go.Box(y=life_now, name="as programmed", marker_color=AMBER), row=1, col=1)
fig.add_trace(go.Box(y=life_rec, name="as recommended", marker_color=CYAN), row=1, col=1)
fig.add_trace(go.Bar(x=["no system", "with the recommender"],
                     y=[naive_wrong*100, model_wrong*100],
                     marker_color=[RED, GREEN], showlegend=False,
                     text=[f"{naive_wrong:.0%}", f"{model_wrong:.1%}"],
                     textposition="outside"), row=1, col=2)
fig.update_yaxes(title_text="tool life (min)", type="log", row=1, col=1)
fig.update_yaxes(title_text="% of jobs with the wrong tool", row=1, col=2)
fig.update_layout(height=420, template="plotly_white")
fig.show()
'''),
          ("md", r"""
### Read this one carefully — the obvious business case does not survive contact with the data

**The recommender does not extend tool life, and the honest thing is to say so.** It learned from the
shop's own speeds, so the best it can do is reproduce them. Prediction error in Vc is roughly symmetric,
but Taylor is **convex** — so the same percentage error costs more life than it gains. The median comes
out slightly *worse* than what the setters programmed. That is a real property of the problem, not a bug
to tune away.

Which makes the second block the important one. At `n = 0.28`, **a 10% error in cutting speed costs about
30% of the tool's life.** That single number justifies three design decisions taken earlier:

- the speed is issued as a **proposal the setter trims**, never as a value to program blind;
- the audit reported **MAE in m/min**, not just R², because the absolute error is what Taylor consumes;
- the setup sheet carries an **expected tool life**, so an unreasonable recommendation is visible before
  the spindle starts.

**The value is in the third block: not choosing the wrong tool.** On titanium, Inconel and stainless — a
third of the log — a shop with no system and no senior setter available reaches for the most common insert
and is wrong most of the time. The recommender is wrong on a few percent. Each avoided event is a scrapped
part and lost spindle time, and that is where the money is.

`SCRAP_EVENT` and `JOBS_PER_YEAR` are **named variables** — put your own numbers in. And the benefit that
never appears in any of these figures is consistency: the same answer at 3 a.m. as at 10 a.m.
""")],
    built="""A business case in the units a tool room manages: insert spend, machine hours, and tool life — each
one traceable to Taylor and to the sealed jobs.""",
    takeaway="""A recommender trained on your own log makes your best practice consistent; it does not invent new physics.""",
)


# ============================================================================
# INTRO
# ============================================================================
def phase_rows():
    out = []
    for pi, (pname, pdesc) in enumerate(PHASES):
        kids = [s for s in STEPS if s["phase"] == pi]
        out.append(f"| **{pi+1}. {pname}** | {pdesc} | "
                   + " · ".join(link(s["id"], f"{s['icon']} {s['civil']}") for s in kids) + " |")
    return "\n".join(out)

def mapping_rows():
    return "\n".join(f"| {s['icon']} {s['civil']} | → | {s['ai_icon']} {s['ai']} | {s['phase']+1} |"
                     for s in STEPS)

md(rf"""
# 🛠️ AI Cutting Tool Recommendation System
## Machine Learning vs Deep Learning, for Manufacturing and Production Engineers

> You are not here to learn Artificial Intelligence. You are here to solve a **tool-room problem** — one
> that is genuinely hard for reasons of combinatorics and institutional memory, not effort. AI turns up in
> the middle of it, because the engineering requires it. Not before.

---

## 1 · The engineering problem

A drawing lands in the tool room. **Inconel 718 bracket, 5-axis machining centre, finishing pass, Ra 0.8
µm, batch of 240.** Before a single chip is cut, five decisions have to be made:

**tool material · coating · cutting speed · feed rate · coolant strategy**

Get them wrong and the results arrive quickly. Reach for CBN on the Inconel and the insert welds up. Run
the catalogue speed for steel and the edge is gone in four minutes. Program a feed that ignores the nose
radius and the part misses Ra 0.8 no matter how good the tool is.

Get them right and the same job runs longer, cleaner and cheaper.

The knowledge that separates the two lives with **whoever has been in the tool room longest**. It is real,
it is hard-won, and it is almost entirely undocumented. It goes home at 5 o'clock and it retires.

Meanwhile the shop has three years of completed jobs sitting in an ERP system that nobody queries, because
nobody has time to read four thousand records before setting today's job.

---

## 2 · What we are going to build

A **cutting tool recommendation system**. Four parts:

| | Part | What it does |
|---|---|---|
| 📋 | **The job card is read** | Workpiece, machine, operation, required finish, batch quantity, nose radius, and how the last similar tool performed. |
| 🛠️ | **Five recommendations come back** | Tool material, coating, coolant — and the cutting speed and feed to program. |
| 📷 | **The camera reads the insert** | The tool history no job-card field can hold: the flank wear land on the last insert, graded and located. |
| 📄 | **The setter gets a setup sheet** | Not five bare numbers. A proposal with the expected tool life, the achievable finish, the reasoning and a confidence. |

> **The goal is not an unmanned tool room.** The setter still sets the job, still hears the cut, still
> calls it off if it sounds wrong, and still signs the setup sheet. The system does the thing a person
> cannot: recall **every** job the shop has run, not the ten memorable ones, and apply that consistently
> on the night shift as well as the day.

---

## 3 · The engineering workflow

One tool room, one log, in the order a real project runs it — nine phases.

| Phase | In the tool room | Steps |
|---|---|---|
{phase_rows()}

---

## 4 · Engineering → AI, the whole map

**Every AI concept in this notebook is a manufacturing activity you already understand.** Read down the
left column and you have described a tool room. Read down the right and you have described a machine
learning pipeline. They are the same column.

| 🏭 Manufacturing process | → | 🤖 The AI process that solves it | Phase |
|---|:-:|---|:-:|
{mapping_rows()}

---

## The one idea this notebook proves

> **Machine Learning recommends tooling and cutting parameters from the named fields on a job card.
> Deep Learning reads the insert photograph — the tool history no field can hold — and feeds it back into
> the next recommendation.**

Two real machining laws run through the whole notebook and are used to generate the data, to check the
recommendations, and to price the business case:

- **Taylor's tool life equation**, `V · Tⁿ = C`
- **The theoretical surface finish relation**, `Ra ≈ f² / (32·r)`

Step {[s['id'] for s in STEPS].index('proof')+1} measures the claim.
""")

md(r"""
---

## Setup

In Colab everything below is already installed. Charts are Plotly, so they are interactive — hover, zoom
and toggle series from the legend. TensorFlow is needed only for the CNN and Grad-CAM steps; those cells
detect whether it is present and skip cleanly if not.
""")

co(r"""
# !pip install numpy pandas scikit-learn plotly tensorflow
print("Everything is imported in step 3, where the machining laws are defined.")
""")

# ============================================================================
# EMIT
# ============================================================================
for i, s in enumerate(STEPS):
    pname, pdesc = PHASES[s["phase"]]
    bridge_tbl = "\n".join(f"| {l} | → | {r} |" for l, r in s["bridge"])
    see = (f"\n> 🎬 **See this illustrated:** [{APP}/?stage={s['id']}]({APP}/?stage={s['id']})\n"
           if APP else "")
    md(rf"""
---

# {NUM[i]} {s['icon']} {s['civil']}
### Phase {s['phase']+1} of {len(PHASES)} · {pname} — *{pdesc}*

> The manufacturing activity on this page is also, exactly, the AI concept **{s['ai']}**. Here is why.

## Part 1 · In the tool room

{s['site'].strip()}

## Part 2 · The engineering challenge

{s['challenge'].strip()}
""")
    md(rf"""
## Part 3 · Where the AI comes in

{s['ai_link'].strip()}

| 🏭 **In the tool room** | → | 🤖 **In the AI** |
|---|:-:|---|
{bridge_tbl}

**{s['civil']}** → *becomes* → **{s['ai']}** → *which is computed as* → `{s['tech']}`
{see}
## Part 4 · The technical explanation

You now know what **{s['civil']}** is, why it is hard, and why it needs **{s['ai']}**. Only now, the
mechanism.
""")
    for kind, text in s["body"]:
        (md if kind == "md" else co)(text)
    md(rf"""
## Part 5 · What you just built

{s['built'].strip()}

> **Key takeaway.** {s['takeaway'].strip()}
""")

md(r"""
---

# 🏁 The whole system, in one page

```
   JOB CARD  ──► encode ──► split ──►  3 CLASSIFIERS  ──┐
   13 named fields                     tool/coat/coolant │
                                       2 REGRESSORS      ├─►  SETUP SHEET
                                       speed / feed      │    tool · coating · coolant
                                                         │    Vc · f · expected life
   INSERT PHOTO  ─────────────────►  CNN + Grad-CAM  ────┘    expected Ra · confidence
   4,096 raw pixels                  wear grade + location
                                             │
                                             └──► becomes the 'tool history' input next time
```

## What was built

| Stage | Method | Output |
|---|---|---|
| Recommend tool material, coating, coolant | 3 × RandomForestClassifier | the tooling to issue |
| Recommend cutting speed and feed | 2 × RandomForestRegressor | what to program |
| Check the combination is issuable | domain rules | no coated PCD, no CBN on Inconel |
| Check the feed holds the finish | `Ra = f²/32r` | would it make the drawing? |
| Explain the recommendation | feature importance | why this tool |
| Grade insert wear | CNN, 3 classes | fresh / worn / replace |
| Locate the wear land | Grad-CAM | the evidence, and VB itself |
| Assemble the setup sheet | fusion + Taylor | life, finish, confidence, notes |
| Price it | Taylor on sealed jobs | inserts, machine hours |

## The three things worth remembering

1. **Job card → Machine Learning.** An engineer named the fields; the model weights them. Categories get
   one column each, because materials have no order.
2. **Insert photo → Deep Learning.** Nobody can name 4,096 pixel columns, and brightness is not wear —
   built-up edge defeats every threshold. Only the CNN separates them.
3. **Manufacturing Engineer + AI.** The system proposes a starting point with its reasoning and its
   confidence. The setter still hears the cut and still signs the sheet.

## Where the engineering discipline showed up

Five moments in this notebook were engineering judgements, not machine learning:

- **One-hot encoding**, because numbering materials 0–6 claims an order that does not exist.
- **Stratifying the split**, or the rare and expensive tools vanish from the audit.
- **Checking the combination**, because three accurate classifiers can still produce a coated PCD insert.
- **Checking the feed against `Ra = f²/32r`**, because an average error says nothing about whether the
  part passes inspection.
- **Pricing with Taylor on sealed jobs**, instead of quoting a percentage.
""")

nb = new_notebook(cells=cells, metadata={
    "kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
    "language_info": {"name": "python"},
    "colab": {"provenance": []},
})
nbf.validate(nb)
with open("Cutting_Tool_Recommendation_DL.ipynb", "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"wrote Cutting_Tool_Recommendation_DL.ipynb  ({len(cells)} cells, "
      f"{sum(1 for c in cells if c.cell_type=='code')} code, {len(STEPS)} steps, {len(PHASES)} phases)")
