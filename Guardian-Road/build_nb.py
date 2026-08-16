"""Build Guardian_Road_AI_Safety_Shield.ipynb. Run with: py -3 -X utf8 build_nb.py"""
from pathlib import Path
import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

ROOT=Path(__file__).resolve().parent
cells=[]
def md(s): cells.append(new_markdown_cell(s.strip()))
def co(s): cells.append(new_code_cell(s.strip()))

md(r"""
# 🛣️ Guardian Road
### Building an AI Safety Shield Around a Fallen Rider

A motorcycle falls in the centre lane. The road is wet. Traffic is arriving at 72 km/h, and the
closest vehicle is 118 metres away.

**This notebook asks how the road itself can prevent the next collision.** It decides where warnings
begin, how speed falls, where vehicles merge, and how to preserve safe routes for helpers and an
ambulance.

> ⚠️ Everything here is simulated. It is not a traffic controller, medical device or emergency
> system. It detects a road obstruction—not an injury—and may not control a real road.

### Research question

Can a physics-guided AI controller reduce simulated secondary-collision risk while producing less
severe braking and less traffic delay than a fixed-distance warning system?

### What we will build

1. A three-lane synthetic road and imperfect traffic.
2. A temporal fallen-rider detector with honest lookalikes.
3. A physics floor for safe warning distance.
4. Cost-sensitive regressors that may add—but never remove—safety margin.
5. Dynamic studs, speed limits, merge control, safe paths and ambulance access.
6. A seven-controller benchmark, sensor-failure test and staged reopening procedure.
""")

md(r"""
### Contents

1. Build the road
2. Simulate normal traffic
3. Introduce the crash
4. Detect the fallen rider over time
5. Calculate stopping distance
6. Test a fixed warning
7. Predict dynamic warning distance
8. Make late warnings cost more
9. Control connected road studs
10. Model imperfect drivers
11. Choose the merge direction
12. Preserve ambulance access
13. Find a safe bystander path
14. Test multiple hazards and failures
15. Restore normal traffic
""")

md("## Setup\n\nThe notebook is standalone. It contains the simulation source inline and uses fixed seeds so the figures and prose agree each time.")
co(r"""
# !pip install numpy pandas plotly scikit-learn nbformat
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.neural_network import MLPRegressor, MLPClassifier

np.random.seed(7)
print("Ready.")
""")

# The teaching notebook remains standalone by carrying the tested domain module inline.
source=(ROOT/"guardian.py").read_text(encoding="utf-8")
co("# Guardian Road simulation core — kept in guardian.py in the project\n"+source)

md(r"""
## 1 · Build the road

The road is 650 metres long and has three lanes. The rider is the origin: every approaching vehicle
has a positive upstream distance. This makes the most important measurement readable—how much road
remains before the obstruction.

The drawing is not decoration. Its warning boundary, studs, lanes and vehicles are generated from
the same controller state used in the score table.
""")
co(r"""
scene = Scene()
action = controller(scene, "Safe AI + ambulance")
fig_road(scene, action).show()
pd.DataFrame([asdict(scene)]).T.rename(columns={0:"value"})
""")
md("**Read it like this.** The red area is local. The amber warning begins far upstream. A safe design creates time gradually instead of demanding sudden braking beside the rider.")

md(r"""
## 2 · Simulate normal traffic

Every driver has position, speed, reaction delay, a braking limit and a willingness to change lane.
Real traffic is heterogeneous: a truck cannot copy a motorcycle's braking, and a distracted driver
does not react like a connected vehicle.
""")
co(r"""
rng=np.random.default_rng(7)
profiles={
 "alert":(1.0,.94), "distracted":(2.1,.58), "elderly":(1.7,.82),
 "connected autonomous":(.35,.99), "heavy-truck":(1.65,.78),
 "aggressive":(1.2,.48), "following too closely":(1.45,.72)}
normal=[]
for i in range(90):
    driver=str(rng.choice(list(profiles)))
    reaction,compliance=profiles[driver]
    kind="truck" if driver=="heavy-truck" else str(rng.choice(["car","car","car","bus","motorcycle"]))
    normal.append(dict(vehicle_id=i,type=kind,lane=int(rng.integers(0,3)),
        position_m=float(rng.uniform(40,650)),speed_mps=float(rng.normal(20,3)),
        reaction_time_s=float(max(.3,rng.normal(reaction,.16))),
        max_safe_decel=VEHICLES[kind]["decel"],connected=driver=="connected autonomous",
        compliance_probability=compliance,driver=driver))
traffic=pd.DataFrame(normal).sort_values("position_m")
traffic.head(10)
""")
co(r"""
traffic["headway_s"] = traffic.groupby("lane")["position_m"].diff().abs() / traffic.speed_mps
traffic.groupby("lane").agg(vehicles=("vehicle_id","count"),mean_speed=("speed_mps","mean"),
                             median_headway=("headway_s","median"))
""")
md("**The important imperfection.** Compliance is a probability, not a switch. Later experiments must survive drivers who respond late or refuse the first merge opportunity.")

md(r"""
## 3 · Introduce the crash

At three seconds the rider and motorcycle separate. The rider remains in the centre lane while
traffic continues upstream. Camera signals are noisy, and useful evidence appears at different
times—not on one magical impact frame.
""")
co(r"""
incident=detection_signals("fallen_rider")
incident.head(25).tail(8)
""")
co(r"""
fig=go.Figure()
for name,colour in zip(["person_road","horizontal","still","separation","trajectory_change"],
                       [COLORS["cyan"],COLORS["amber"],COLORS["green"],COLORS["red"],COLORS["violet"]]):
    fig.add_scatter(x=incident.t,y=incident[name],name=name.replace("_"," "),line=dict(color=colour))
_layout(fig,title="What the camera can honestly report",xaxis_title="seconds",yaxis_title="noisy signal").show()
""")

md(r"""
## 4 · Detect the fallen rider over time

A fallen rider, debris, a worker, a crossing pedestrian and a shadow can share one frame. The
sequence matters: separation from a motorcycle, persistent road occupancy, stillness, horizontal
orientation and nearby trajectory change.

The output is an **obstruction probability**. The medical condition remains unknown.
""")
co("fig_detection().show()")
co(r"""
det=[]
for kind in ["fallen_rider","debris","crossing","worker","shadow"]:
    d=detection_signals(kind)
    one_frame=((d.person_road>.7)&(d.horizontal>.5)).astype(float)
    temporal=((d.person_road.rolling(12,min_periods=1).mean()>.55)&
              (d.still.rolling(12,min_periods=1).mean()>.45)).astype(float)
    sequence=detection_probability(d)
    det.append(dict(scene=kind,one_frame=float(one_frame.max()),fixed_rule=float(temporal.max()),
                    sequence_peak=float(sequence.max()),confirmed=bool((sequence>.72).rolling(5).sum().max()>=5)))
pd.DataFrame(det).set_index("scene")
""")
md("**Why call before certainty?** A conservative traffic warning is reversible. Waiting for a medical conclusion is both unnecessary and outside the system's authority.")

md(r"""
## 5 · Calculate stopping distance

The engineering baseline is a sum—not a subtraction:

\[
D_{stop}=D_{reaction}+D_{braking},\quad D_{reaction}=vt_r,\quad
D_{braking}=\frac{v^2}{2\mu g}
\]

Wet friction, visibility, vehicle type, density, slope and uncertainty add margin. This physical
minimum remains below every learned controller.
""")
co(r"""
d=required_warning(scene)
pd.Series(d,name="metres").round(1)
""")
co(r"""
rows=[]
for speed in [30,50,70,90]:
    for weather in WEATHER:
        s=Scene(speed_kmh=speed,weather=weather)
        rows.append(dict(speed_kmh=speed,weather=weather,required_m=required_warning(s)["required_m"]))
stop_table=pd.DataFrame(rows)
stop_table.pivot(index="speed_kmh",columns="weather",values="required_m").round(0)
""")

md(r"""
## 6 · Test a fixed warning

Now give every incident the same answer: warn at 150 m, reduce to 40 km/h and close the centre lane.
It is simple and explainable. It is also blind to the road in front of it.
""")
co(r"""
tests=[Scene(speed_kmh=90,weather="Wet",vehicle_type="truck",reaction_s=2.0),
       Scene(speed_kmh=72,weather="Heavy rain",reaction_s=1.8),
       Scene(speed_kmh=50,weather="Dry",reaction_s=1.0,density=8),
       Scene(speed_kmh=70,weather="Fog",reaction_s=1.5,density=68)]
fixed=[]
for s in tests:
    a=controller(s,"Fixed 150 m"); o=outcome(s,a)
    fixed.append(dict(speed=s.speed_kmh,weather=s.weather,vehicle=s.vehicle_type,
                      physics_min=a["physics_min_m"],warning=a["warning_m"],
                      unsafe=a["warning_m"]<a["physics_min_m"],risk=o["collision_probability"],delay=o["traffic_delay_s"]))
pd.DataFrame(fixed)
""")
md("**Two opposite failures.** A fixed boundary can be dangerously late for a wet-road truck and wastefully early for light, slow, dry traffic.")

md(r"""
## 7 · Predict dynamic warning distance

We generate thousands of synthetic situations from the same physical world. Four regressors predict
the required distance. The split is made before fitting, and the held-out test pile is touched only
for the final table.
""")
co(r"""
data=build_warning_dataset(3500)
features=["speed_kmh","weather","reaction_s","vehicle_type","density","left_occupancy",
          "right_occupancy","closest_m","gradient_pct","detection_confidence"]
cat=["weather","vehicle_type"]; num=[c for c in features if c not in cat]
X_train,X_test,y_train,y_test=train_test_split(data[features],data.required_m,test_size=.25,random_state=7)
prep=ColumnTransformer([("num",StandardScaler(),num),("cat",OneHotEncoder(handle_unknown="ignore"),cat)])
models={"linear":LinearRegression(),"tree":DecisionTreeRegressor(max_depth=8,min_samples_leaf=18,random_state=7),
        "forest":RandomForestRegressor(n_estimators=140,max_depth=14,min_samples_leaf=4,n_jobs=-1,random_state=7),
        "neural network":MLPRegressor(hidden_layer_sizes=(48,24),max_iter=350,early_stopping=True,random_state=7)}
predictions={}; fitted={}
for name,model in models.items():
    pipe=make_pipeline(prep,model); pipe.fit(X_train,y_train)
    fitted[name]=pipe; predictions[name]=pipe.predict(X_test)
pd.DataFrame([{"model":n,"MAE metres":mean_absolute_error(y_test,p),
               "unsafe predictions":int((p<y_test).sum()),
               "worst underprediction":float(np.max(y_test-p))} for n,p in predictions.items()]).set_index("model").round(2)
""")

md(r"""
## 8 · Make late warnings cost more

MAE says 20 m early and 20 m late are equal. The road does not. We use

\[
L=\begin{cases}\alpha|e|,&\text{warning too late}\\\beta|e|,&\text{warning too early}\end{cases},
\quad \alpha=8,\ \beta=1.
\]

A deployment controller then applies a physical guard: `max(model prediction, physics minimum)`.
""")
co(r"""
rows=[]
physics_floor=np.array([required_warning(Scene(speed_kmh=r.speed_kmh,weather=r.weather,
 reaction_s=r.reaction_s,vehicle_type=r.vehicle_type,density=r.density,left_occupancy=r.left_occupancy,
 right_occupancy=r.right_occupancy,closest_m=r.closest_m,gradient_pct=r.gradient_pct,
 detection_confidence=r.detection_confidence))["required_m"] for r in X_test.itertuples()])
for name,p in predictions.items():
    guarded=np.maximum(p,physics_floor)
    rows.append(dict(model=name,MAE=mean_absolute_error(y_test,p),asymmetric=asymmetric_loss(y_test,p),
                     unsafe_before=int((p<physics_floor).sum()),unsafe_after=int((guarded<physics_floor).sum())))
pd.DataFrame(rows).set_index("model").round(2)
""")
co(r"""
# Cost-sensitive calibration: use a training residual quantile, not the test answers.
# alpha/(alpha+beta)=8/9 asks for a deliberately conservative prediction quantile.
alpha,beta=8,1
base=fitted["forest"]
train_pred=base.predict(X_train)
safety_offset=float(np.quantile(y_train-train_pred,alpha/(alpha+beta)))
raw=predictions["forest"]
cost_sensitive=raw+safety_offset
guarded=np.maximum(cost_sensitive,physics_floor)
pd.Series({"learned safety offset (m)":safety_offset,
           "raw asymmetric loss":asymmetric_loss(y_test,raw,alpha,beta),
           "cost-sensitive asymmetric loss":asymmetric_loss(y_test,cost_sensitive,alpha,beta),
           "unsafe after physical guard":int((guarded<physics_floor).sum())}).round(2)
""")
md("**The guard is the architecture.** Better training can reduce error. It cannot replace the minimum stopping-distance constraint.")

md(r"""
## 9 · Control connected road studs

One distance becomes five visible zones: awareness, speed reduction, merge, exclusion and rider
protection. The road changes shape when the sidebar conditions—or the code below—change.
""")
co("road_zones(action)")
co("fig_road(scene,action).show()")

md(r"""
## 10 · Model imperfect drivers

Perfect compliance makes every controller look safe. We replay driver profiles with different
reaction distributions, braking limits, headways and compliance probabilities.
""")
co(r"""
rng=np.random.default_rng(11); driver_rows=[]
for driver,(mean_rt,compliance) in profiles.items():
    risks=[]
    for _ in range(250):
        typ="truck" if driver=="heavy-truck" else "car"
        s=Scene(reaction_s=max(.3,rng.normal(mean_rt,.18)),vehicle_type=typ,
                density=rng.uniform(15,60),weather=str(rng.choice(list(WEATHER))))
        a=controller(s,"Safe AI")
        if rng.random()>compliance: a["warning_m"]*=.68
        risks.append(outcome(s,a)["collision_probability"])
    driver_rows.append(dict(driver=driver,mean_risk=np.mean(risks),p95_risk=np.quantile(risks,.95)))
pd.DataFrame(driver_rows).set_index("driver").round(3)
""")

md(r"""
## 11 · Choose the merge direction

Closing the centre lane does not automatically mean “merge left.” The receiving lane needs capacity,
a usable gap and no conflict with the responder plan. If neither side is safe, stopping traffic is a
valid answer.
""")
co(r"""
merge_tests=[]
for left,right,eta in [(.25,.82,9),(.84,.22,9),(.42,.47,9),(.95,.96,9),(.25,.82,3)]:
    s=Scene(left_occupancy=left,right_occupancy=right,ambulance_eta_min=eta)
    choice,reason=merge_choice(s)
    merge_tests.append(dict(left_occupancy=left,right_occupancy=right,ambulance_eta=eta,choice=choice,reason=reason))
pd.DataFrame(merge_tests)
""")

md(r"""
## 12 · Preserve ambulance access

When the ambulance is dispatched, the objective adds access time and route-blockage risk. The safe
controller reserves a lane early instead of trying to empty it when blue lights are already at the queue.
""")
co(r"""
amb=[]
for density in [15,35,55,70]:
    s=Scene(density=density,left_occupancy=min(.92,density/80),ambulance_eta_min=4)
    for mode in ["Safe AI","Safe AI + ambulance"]:
        a=controller(s,mode); o=outcome(s,a)
        amb.append(dict(density=density,plan=mode,reserved=a["reserve_ambulance"],
                        blockage_probability=o["ambulance_blockage"],traffic_delay=o["traffic_delay_s"]))
pd.DataFrame(amb).pivot(index="density",columns="plan",values="blockage_probability").round(3)
""")

md(r"""
## 13 · Find a safe bystander path

The shortest geometric line crosses moving traffic. Dijkstra instead minimizes accumulated risk.
The path may be displayed only after the controller confirms the relevant traffic protection.
""")
co(r"""
cost=hazard_grid(active_lanes=() if action["upstream_red"] else (0,2),reserve_lane=0)
path=plan_path(cost)
fig_hazard(cost,path).show()
print("Route cells:",len(path),"  accumulated risk cost:",round(sum(cost[p] for p in path),1))
""")
md("**Hard rule.** No green route is shown through an active lane. If traffic protection is unverified, the instruction is to wait on the shoulder.")

md(r"""
## 14 · Test hazards and sensor failures

Heavy rain, occlusion, failed radar, missing communications and dead studs are not rare exceptions;
they are part of the operating world. Poor confidence bypasses optimization and expands the zone.
""")
co(r"""
failures=[("healthy",Scene()),("camera blocked",Scene(camera_ok=False)),
          ("radar lost",Scene(radar_ok=False)),("stud failures",Scene(studs_ok=.45)),
          ("control link lost",Scene(communications_ok=False)),
          ("heavy rain + low confidence",Scene(weather="Heavy rain",detection_confidence=.58))]
rows=[]
for label,s in failures:
    a=controller(s); o=outcome(s,a)
    rows.append(dict(test=label,fallback=a["fallback"],warning_m=a["warning_m"],
                     signal_red=a["upstream_red"],merge=a["merge"],risk=o["collision_probability"]))
pd.DataFrame(rows).set_index("test")
""")
md("**Read the direction of failure.** Missing confidence makes the protected zone larger and the traffic decision more conservative.")

md(r"""
## 15 · Restore normal traffic

Reopening is a guarded state machine:

1. An authorized responder confirms lane clearance.
2. The red exclusion zone is removed.
3. A temporary reduced-speed zone remains.
4. Queued traffic is released gradually.
5. Signals return to normal.
6. Failed studs and sensors are recorded for maintenance.

The optimizer cannot declare the lane clear by itself.
""")
co(r"""
def restoration_state(responder_clear, occupancy, hardware_ok):
    if not responder_clear: return "PROTECTED — wait for authorized clearance"
    if occupancy>.55: return "METERED RELEASE — keep reduced speed"
    if not hardware_ok: return "LIMITED REOPENING — record and isolate failed equipment"
    return "NORMAL — signals restored after gradual release"

pd.DataFrame([{"responder_clear":c,"queue_occupancy":q,"hardware_ok":h,
               "state":restoration_state(c,q,h)}
              for c,q,h in [(False,.8,True),(True,.8,True),(True,.3,False),(True,.3,True)]])
""")

md(r"""
## Final benchmark

Seven controllers face the opening scenario. Secondary-collision probability remains separate from
braking, delay and ambulance blockage so a convenient average cannot hide an unsafe decision.
""")
co(r"""
scoreboard=compare_controllers(scene)
scoreboard[["Controller","warning_m","collision_probability","max_deceleration",
            "traffic_delay_s","ambulance_blockage","fallback"]].set_index("Controller").round(3)
""")
co("fig_tradeoff(scene).show()")

md(r"""
## What this simulation may claim

It can compare controllers inside its invented world. It can show why warning distance must change,
why underprediction deserves a larger loss, why driver diversity matters and why physical constraints
must sit after AI optimization.

It cannot prove that a real deployment prevents collisions. That requires validated sensors, calibrated
vehicle dynamics, human-factors studies, road-authority approval, cybersecurity engineering, field trials
and emergency-service governance.

### Rules that do not move

- Warn conservatively before optimizing.
- Never predict below the physics minimum.
- Never diagnose the rider.
- Never show a bystander path through active traffic.
- Give traffic control and emergency services authority over the optimizer.
- Enter a conservative fallback when observations or actuators are unreliable.
- Reopen only after authorized clearance.
""")

nb=new_notebook(cells=cells,metadata={"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
                                      "language_info":{"name":"python","version":"3"},
                                      "colab":{"name":"Guardian_Road_AI_Safety_Shield.ipynb","provenance":[]}})
out=ROOT/"Guardian_Road_AI_Safety_Shield.ipynb"
nbf.write(nb,out)
print(f"Wrote {out.name}: {len(cells)} cells")
