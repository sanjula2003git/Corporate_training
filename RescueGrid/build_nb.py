"""Build RescueGrid_First_Aid_Coordination_Mat.ipynb. Run: py -3 -X utf8 build_nb.py"""
from pathlib import Path
import ast
import nbformat as nbf
from nbformat.v4 import new_notebook,new_markdown_cell,new_code_cell
ROOT=Path(__file__).resolve().parent; cells=[]
def md(s): cells.append(new_markdown_cell(s.strip()))
def co(s): cells.append(new_code_cell(s.strip()))
CORE_SOURCE=(ROOT/"rescuegrid.py").read_text(encoding="utf-8")
CORE_LINES=CORE_SOURCE.splitlines()
CORE_TREE=ast.parse(CORE_SOURCE)
CORE_BLOCKS={n.name:"\n".join(CORE_LINES[n.lineno-1:n.end_lineno]) for n in CORE_TREE.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
FIRST_DEF=min(n.lineno for n in CORE_TREE.body if isinstance(n,ast.FunctionDef))
CORE_BLOCKS["__preamble__"]="\n".join(CORE_LINES[:FIRST_DEF-1])
def core(*names): co("\n\n".join(CORE_BLOCKS[n] for n in names))

md(r"""
# 🟩 RescueGrid
### Building an Intelligent First-Aid Coordination Mat

A person collapses in a railway station. Four helpers step forward, equipment approaches from the
north and responders will enter from the east. A bench and a crowd leave only 3.2 × 2.8 metres of
usable space.

**This notebook asks where people, equipment and access lanes should go so trained instructions can
continue without avoidable obstruction.**

> ⚠️ Everything here is simulated. RescueGrid organizes physical space. It does not diagnose,
> choose treatment, invent first-aid procedures, delay emergency contact or override responders.

### Research question

Can an adaptive illuminated mat reduce responder-path blockages, incorrect helper positioning and
equipment-placement time compared with static floor markings in crowded emergency simulations?
""")
md('🎬 **The illustrated version — open it once.**\n\n[Open the RescueGrid illustration app in a second tab](https://rescuegrid.streamlit.app/?stage=start) and leave it open beside this notebook.\n\nEvery lesson below carries a line like *"🎬 Illustration tab → step 4 · *A Layout With Hard Boundaries*"*. That names the page to open from\nthe app\'s **Learning journey** list, then move with its own ◀ ▶ buttons. There is deliberately no second link to click: Colab gives every link click a brand-new browser tab,\nso one anchor here keeps you at two tabs instead of sixty.\n')
md(r"""
### Contents

1. A crowded emergency
2. Place everyone manually
3. Create the first rule-based layout
4. Model the mat as a graph
5. Build a responder-access route
6. Define role-position constraints
7. Optimize the layout
8. Assign people to roles
9. Simulate pressure sensors
10. Show one real-time instruction
11. Replan dynamically
12. Prepare a fatigue handover
13. Test different environments
14. Place multiple equipment items
15. Build the interactive RescueGrid
""")
md("## Setup\n\nThe notebook carries the complete deterministic simulation inline. Fixed seeds make the output repeatable.")
co(r"""
# Colab already includes these. JupyterLite installs the missing pure-Python packages here.
try:
    import plotly.graph_objects as go
except ModuleNotFoundError:
    import micropip
    await micropip.install(["plotly", "ipywidgets", "nbformat"])
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from IPython.display import display,clear_output
import ipywidgets as widgets
np.random.seed(7)
print("Ready.")
""")
core("__preamble__")

md(r"""
## 1 · A crowded emergency

The modular mat becomes a 12 × 12 grid. Each tile is empty, blocked, occupied by the mannequin,
assigned to a helper or equipment, or reserved for access. The door and bench are facts about the
scene—not choices made by the optimizer.
""")
core("_door")
core("neighbours","manhattan")
core("build_scene")
core("_layout")
core("fig_grid")
co(r"""
scene=Scene(); world=build_scene(scene)
fig_grid(world,title="The scene before RescueGrid assigns positions").show()
pd.Series({"room":f"{scene.width} × {scene.height} tiles","helpers":scene.helpers,
           "crowd":scene.crowd,"entrance":scene.entrance,
           "usable graph nodes":int((world["grid"]!=OBSTACLE).sum())})
""")
md("**Read it like this.** Grey tiles are physical obstacles, the red tile is the mannequin and `ENTRY` is the responder entrance. No treatment is encoded in the grid.")

md(r"""
## 2 · Place everyone manually

Before introducing AI, place four functions around the scene and measure what the arrangement costs:
blocked access, movement, equipment reach, role conflicts and path length.
""")
core("shortest_path")
core("candidate_tiles")
core("access_path")
core("layout_metrics")
core("manual_layout")
co(r"""
manual=manual_layout(world)
manual_result={"layout":manual,"metrics":layout_metrics(world,manual),"path":access_path(world,manual)}
fig_grid(world,manual_result,"A hand-written arrangement").show()
pd.Series(manual_result["metrics"])
""")
md("**The average distance is not enough.** One occupied access tile can make an otherwise compact arrangement unusable.")

md(r"""
## 3 · Create the first rule-based layout

The first controller chooses the nearest free tile for each role. It works in an empty room, but it
does not understand that several individually reasonable positions can collectively close a corridor.
""")
core("rule_layout")
co(r"""
rules=rule_layout(world)
rule_result={"layout":rules,"metrics":layout_metrics(world,rules),"path":access_path(world,rules)}
fig_grid(world,rule_result,"Nearest-free rules").show()
pd.DataFrame([manual_result["metrics"],rule_result["metrics"]],index=["manual","nearest-free rules"])
""")

md(r"""
## 4 · Model the mat as a graph

Every usable tile is a node. Up, down, left and right neighbours create edges. Obstacles, missing mat
tiles and forbidden zones remove nodes. A scene is usable only if the relevant regions remain connected.
""")
co(r"""
nodes=[(r,c) for r in range(scene.height) for c in range(scene.width)
       if world["grid"][r,c]!=OBSTACLE and (r,c) not in world["missing"]]
edges=sum(sum(1 for q in neighbours(p,world["grid"].shape) if q in set(nodes)) for p in nodes)//2
print("Nodes:",len(nodes),"Edges:",edges,"Entrance:",world["entrance"],"Person:",world["person"])
""")
co(r"""
sample=world["person"]
print("Node",sample,"has permitted neighbours",list(neighbours(sample,world["grid"].shape)))
""")

md(r"""
## 5 · Build a responder-access route

A* searches from the entrance to a free tile beside the mannequin. Assigned people, equipment,
obstacles, the crowd and missing tiles are forbidden. If no path exists, the layout is rejected.
""")
co(r"""
bare_path=access_path(world)
bare={"layout":{},"metrics":layout_metrics(world,{}),"path":bare_path}
fig_grid(world,bare,"The responder route before role placement").show()
print("Path length:",len(bare_path),"tiles")
""")
md("**A flashing lane is a promise.** It should illuminate only after sensing and validation agree that the route is clear.")

md(r"""
## 6 · Define role-position constraints

Hard constraints are checked before cost:

- The primary helper is at most one tile from the mannequin.
- Equipment is at most two tiles from the primary helper.
- No two assignments share a tile.
- Nobody or nothing occupies the responder route.
- Missing or hazardous tiles are never assigned.

Access blockage and hazard occupation carry the largest penalties.
""")
co(r"""
def constraint_report(world,layout):
    vals=list(layout.values()); p=world["person"]
    return pd.Series({
      "primary close enough":manhattan(layout.get("primary",(-99,-99)),p)<=1,
      "equipment reachable":manhattan(layout.get("equipment",(-99,-99)),layout.get("primary",(99,99)))<=2,
      "all positions unique":len(vals)==len(set(vals)),
      "no missing tile used":not any(x in world["missing"] for x in vals),
      "responder route exists":bool(access_path(world,layout))})
constraint_report(world,rules)
""")

md(r"""
## 7 · Optimize the layout

For this small teaching scene we can examine complete combinations around the mannequin. The optimizer
first rejects broken constraints, then minimizes conflict, movement, equipment distance, hazards,
unassigned roles and later reconfiguration.
""")
core("optimize_layout")
core("compare_controllers")
core("fig_controller_bars")
co(r"""
optimized=optimize_layout(world)
fig_grid(world,optimized,"Lowest-cost valid arrangement").show()
pd.Series(optimized["metrics"])
""")
co(r"""
scoreboard=compare_controllers(scene)
scoreboard.set_index("controller")
""")
co("fig_controller_bars(scoreboard).show()")
md("**The optimizer does not earn points for breaking a safety boundary.** Unsafe layouts are rejected rather than balanced against convenience.")

md(r"""
## 8 · Assign people to roles

Position and role are separate decisions. Helpers declare or verify training, mobility, current task
and fatigue. The matching logic never infers competence from appearance.
""")
core("assign_roles")
co(r"""
helpers=[
 dict(id="H1",training_verified=True,mobility="normal",carrying_equipment=False,fatigue=.2),
 dict(id="H2",training_verified=False,mobility="normal",carrying_equipment=True,fatigue=.1),
 dict(id="H3",training_verified=False,mobility="limited",carrying_equipment=False,fatigue=.3),
 dict(id="H4",training_verified=False,mobility="normal",carrying_equipment=False,fatigue=.55)]
assign_roles(helpers).set_index("role")
""")
md("**Missing information stays missing.** The system may ask a helper or dispatcher; it must not fill the gap with visual inference.")

md(r"""
## 9 · Simulate pressure sensors

Each tile reports time, pressure and occupancy. The controller compares an occupied tile with the
expected zone and detects implausible stuck or saturated readings. Pressure verifies a position; it
does not identify a person or equipment item by itself.
""")
core("sensor_stream")
core("fig_sensor")
co(r"""
events=sensor_stream(world,optimized["layout"],100,seed=7,failure_rate=.08)
fig_sensor(events).show()
events.tail(10)
""")
co(r"""
events.groupby(["expected_zone","sensor_fault"]).size().rename("events").to_frame()
""")

md(r"""
## 10 · Show one real-time instruction

Attention is limited. RescueGrid shows exactly one main instruction, using this order:

1. Immediate scene danger or blocked access
2. Responder obstruction or sensor uncertainty
3. Equipment placement
4. Efficiency and waiting positions

Colour is always paired with words or symbols.
""")
core("feedback")
co(r"""
print(feedback(world,optimized,events,crowd_violations=2))
""")
md("**One instruction is a human-factors constraint.** More simultaneous advice is not more assistance.")

md(r"""
## 11 · Replan dynamically

A chair or person now occupies the middle of the access lane. The new objective includes

\[
J_{new}=J_{layout}+\lambda N_{people\ moved}.
\]

The penalty preserves assignments that remain safe instead of moving every footprint whenever the
scene changes.
""")
co(r"""
obstruction=optimized["layout"].get("secondary",optimized["layout"]["replacement"])
changed_world=dict(world);changed_world["grid"]=world["grid"].copy();changed_world["grid"][obstruction]=OBSTACLE
replanned=optimize_layout(changed_world,previous=optimized["layout"],crowd_tiles=[obstruction])
print("New obstruction:",obstruction,"People moved:",replanned["metrics"]["people_moved"])
fig_grid(world,optimized,"Before: original assignments").show()
fig_grid(changed_world,replanned,"After: minimum-change repair").show()
""")

md(r"""
## 12 · Prepare a fatigue handover

The yellow replacement position is prepared before fatigue becomes severe. RescueGrid may organize
the space for a handover; approved protocols and dispatcher instructions govern treatment timing.
""")
co(r"""
fatigue=np.linspace(0,1,21)
state=np.where(fatigue<.55,"MONITOR",np.where(fatigue<.75,"PREPARE YELLOW POSITION","ASK DISPATCHER TO COORDINATE HANDOVER"))
pd.DataFrame({"fatigue":fatigue,"mat_state":state}).iloc[::4]
""")
co(r"""
fig=go.Figure(go.Scatter(x=fatigue,y=np.clip(1-fatigue**1.7,0,1),line=dict(color=COLORS["yellow"],width=3)))
fig.add_vline(x=.55,line_dash="dash",line_color=COLORS["amber"],annotation_text="prepare replacement")
_layout(fig,340,title="Fatigue changes preparation, not medical instructions",xaxis_title="simulated fatigue",yaxis_title="relative task capacity").show()
""")

md(r"""
## 13 · Test different environments

The constraints remain; geometry changes. A large hall has many valid layouts, while a bus aisle or
railway platform may need a smaller active footprint and stricter access priority.
""")
core("environment_scene")
co(r"""
env_rows=[]
for name in ["Airport hall","Railway platform","Classroom","Bus aisle","Small office","Sports field","Lift lobby","Shopping centre","Roadside shoulder"]:
    s=environment_scene(name); w=build_scene(s); r=optimize_layout(w)
    env_rows.append(dict(environment=name,width=s.width,height=s.height,mat_fraction=s.mat_fraction,
                         fallback=r["fallback"],**r["metrics"]))
pd.DataFrame(env_rows).set_index("environment")[["width","height","mat_fraction","layout_cost","path_length","access_clear","fallback"]]
""")

md(r"""
## 14 · Place multiple equipment items

Equipment has size, required proximity, arrival direction and obstruction rules. An item is not simply
“near the mannequin”; it needs a reachable tile that does not enter the responder lane.
""")
co(r"""
items=pd.DataFrame([
 ("AED training unit",2,1,"North",False),("first-aid kit",2,1,"West",False),
 ("communication unit",4,1,"East",False),("protective equipment",3,1,"South",False),
 ("warning markers",6,2,"East",True),("responder bag",2,2,"East",False)],
 columns=["item","max_distance","size_tiles","arrival","may_obstruct"])
items
""")
co(r"""
occupied=set(optimized["layout"].values())|set(optimized["path"]); person=world["person"]
placements=[]
for row in items.itertuples():
    options=[p for p in candidate_tiles(world,row.max_distance+2) if p not in occupied and manhattan(p,person)<=row.max_distance]
    tile=min(options,key=lambda p:manhattan(p,_door(Scene(width=scene.width,height=scene.height,entrance=row.arrival)))) if options else None
    if tile: occupied.add(tile)
    placements.append(dict(item=row.item,tile=tile,placed=tile is not None))
pd.DataFrame(placements).set_index("item")
""")

md(r"""
## 15 · Build the interactive RescueGrid

Use the controls to regenerate the room, change the entrance, remove part of the mat and introduce
sensor failures. The view recomputes the layout, responder path and single priority instruction.
""")
co(r"""
width_w=widgets.IntSlider(value=12,min=7,max=18,description="Width")
height_w=widgets.IntSlider(value=12,min=7,max=18,description="Height")
entrance_w=widgets.Dropdown(options=["East","North","West","South"],value="East",description="Entrance")
helpers_w=widgets.IntSlider(value=4,min=1,max=7,description="Helpers")
crowd_w=widgets.IntSlider(value=18,min=0,max=45,description="Crowd")
obstacles_w=widgets.FloatSlider(value=.10,min=.02,max=.32,step=.01,description="Obstacles")
mat_w=widgets.FloatSlider(value=1,min=.5,max=1,step=.05,description="Mat working")
failure_w=widgets.FloatSlider(value=0,min=0,max=.35,step=.01,description="Sensor fail")
out=widgets.Output()

def redraw(*_):
    with out:
        clear_output(wait=True)
        s=Scene(width=width_w.value,height=height_w.value,entrance=entrance_w.value,
                helpers=helpers_w.value,crowd=crowd_w.value,obstacle_ratio=obstacles_w.value,
                mat_fraction=mat_w.value,sensor_failure=failure_w.value)
        w=build_scene(s); r=optimize_layout(w); ev=sensor_stream(w,r["layout"],30,failure_rate=s.sensor_failure)
        display(pd.DataFrame({"value":["CLEAR" if r["metrics"]["access_clear"] else "BLOCKED",
             r["metrics"]["layout_cost"],r["metrics"]["equipment_distance"],feedback(w,r,ev,max(0,s.crowd-28))]},
             index=["Access path","Layout cost","Equipment distance","Main instruction"]))
        fig_grid(w,r,"Interactive RescueGrid control room").show()

for w in [width_w,height_w,entrance_w,helpers_w,crowd_w,obstacles_w,mat_w,failure_w]: w.observe(redraw,"value")
display(widgets.VBox([widgets.HBox([width_w,height_w,entrance_w]),widgets.HBox([helpers_w,crowd_w]),
                      widgets.HBox([obstacles_w,mat_w,failure_w])]),out)
redraw()
""")

md(r"""
## Final benchmark and safety boundary

The comparison may claim differences inside this synthetic world: access blockages, role conflicts,
equipment distance, movement and recovery after failure. It cannot claim a medical outcome.

### Rules that do not move

- Emergency contact is never delayed.
- The responder lane and hazard rules outrank efficiency.
- Competence comes only from declared or verified information.
- One main instruction is shown at a time, paired with symbols or text.
- The AI organizes space; it never diagnoses or chooses treatment.
- Dispatcher and trained responders can override the layout.
- Failed or incomplete sensing produces a conservative layout or a request to wait.
""")

# One anchor near the top; each lesson names the step to open in the illustration tab.
# Colab opens a fresh tab per link click, so per-cell links are deliberately NOT emitted.
_STEPS=['A Collapse In A Crowded Station', 'Nearest Is Not Always Safest', 'Every Usable Tile Is A Node', 'A Layout With Hard Boundaries', 'Give People Named Jobs', 'The Mat Checks What Actually Happened', 'Change The Minimum Necessary', 'Prepare The Handover Before It Is Needed', 'One Pattern Does Not Fit Every Place', 'Did The Mat Organize The Scene?']
_SMAP={1: 1, 2: 1, 3: 2, 4: 3, 5: 3, 6: 4, 7: 4, 8: 5, 9: 6, 10: 6, 11: 7, 12: 8, 13: 9, 14: 9, 15: 10}
_FINALS={'Final benchmark and safety boundary': 10}
import re as _re
for _cell in cells:
    if _cell["cell_type"]!="markdown": continue
    _src=_cell["source"] if isinstance(_cell["source"],str) else "".join(_cell["source"])
    _m=_re.match(r"##\s+(\d+)\s+·",_src.lstrip())
    _step=_SMAP.get(int(_m.group(1))) if _m else next(
        (_v for _k,_v in _FINALS.items() if _src.lstrip().startswith("## "+_k)),None)
    if _step:
        _cell["source"]=_src.rstrip()+"\n\n> 🎬 **Illustration tab →** step %d · *%s*\n"%(_step,_STEPS[_step-1])
nb=new_notebook(cells=cells,metadata={"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
 "language_info":{"name":"python","version":"3"},"colab":{"name":"RescueGrid_First_Aid_Coordination_Mat.ipynb","provenance":[]}})
out=ROOT/"RescueGrid_First_Aid_Coordination_Mat.ipynb"; nbf.write(nb,out); print(f"Wrote {out.name}: {len(cells)} cells")
