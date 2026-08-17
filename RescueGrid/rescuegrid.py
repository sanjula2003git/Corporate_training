"""Deterministic teaching simulation for RescueGrid.

The system organizes space. It does not diagnose or select treatment.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
import plotly.graph_objects as go

EMPTY, OBSTACLE, PERSON, HELPER, EQUIPMENT, ACCESS_PATH = range(6)
COLORS = dict(bg="#0e1117", panel="#161b22", green="#66bb6a", red="#ef5350",
              yellow="#ffee58", blue="#42a5f5", white="#f5f7fa", amber="#ffb74d",
              purple="#ba68c8", grey="#8b949e", cyan="#4fc3f7")
ROLES = ("primary", "secondary", "replacement", "equipment", "communicator",
         "crowd_controller", "responder_guide")


@dataclass
class Scene:
    width: int = 12
    height: int = 12
    entrance: str = "East"
    helpers: int = 4
    crowd: int = 18
    obstacle_ratio: float = .10
    access_width: int = 1
    mat_fraction: float = 1.0
    sensor_failure: float = 0.0
    seed: int = 7


def _door(scene: Scene):
    return {"North": (0, scene.width//2), "South": (scene.height-1, scene.width//2),
            "West": (scene.height//2, 0), "East": (scene.height//2, scene.width-1)}[scene.entrance]


def neighbours(node, shape):
    r,c=node
    for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
        q=(r+dr,c+dc)
        if 0<=q[0]<shape[0] and 0<=q[1]<shape[1]: yield q


def manhattan(a,b): return abs(a[0]-b[0])+abs(a[1]-b[1])


def build_scene(scene: Scene):
    """Return base grid plus semantic positions."""
    rng=np.random.default_rng(scene.seed)
    grid=np.zeros((scene.height,scene.width),dtype=int)
    person=(scene.height//2,scene.width//2)
    door=_door(scene)
    grid[person]=PERSON
    # One bench creates a realistic local obstruction.
    bench_row=max(1,person[0]-3)
    for c in range(max(1,person[1]-3),min(scene.width-1,person[1]+2)): grid[bench_row,c]=OBSTACLE
    candidates=[(r,c) for r in range(1,scene.height-1) for c in range(1,scene.width-1)
                if grid[r,c]==EMPTY and manhattan((r,c),person)>2]
    n_extra=max(0,int(scene.obstacle_ratio*scene.width*scene.height)-int((grid==OBSTACLE).sum()))
    for i in rng.choice(len(candidates),min(n_extra,len(candidates)),replace=False): grid[candidates[int(i)]]=OBSTACLE
    grid[door]=EMPTY
    free=[p for p in candidates if grid[p]==EMPTY]
    helper_positions=free[-scene.helpers:] if scene.helpers else []
    cabinet=(1,1 if scene.entrance!="West" else scene.width-2)
    grid[cabinet]=EQUIPMENT
    # Mat loss is represented as unusable tiles, biased toward the outer edge.
    missing=set()
    usable=[(r,c) for r in range(scene.height) for c in range(scene.width)
            if (r,c) not in (person,door,cabinet) and grid[r,c]==EMPTY]
    miss=int((1-scene.mat_fraction)*len(usable))
    if miss:
        for i in rng.choice(len(usable),miss,replace=False): missing.add(usable[int(i)])
    return dict(grid=grid,person=person,entrance=door,cabinet=cabinet,
                helpers=helper_positions,missing=missing)


def shortest_path(grid,start,goal,blocked=(),cost=None):
    blocked=set(blocked); pq=[(0,0,start)]; prev={}; dist={start:0}; counter=0
    while pq:
        _,d,node=heapq.heappop(pq)
        if d!=dist[node]: continue
        if node==goal: break
        for nxt in neighbours(node,grid.shape):
            if grid[nxt]==OBSTACLE or nxt in blocked: continue
            nd=d+(1 if cost is None else float(cost[nxt]))
            if nd<dist.get(nxt,math.inf):
                dist[nxt]=nd; prev[nxt]=node; counter+=1
                heuristic=manhattan(nxt,goal)
                heapq.heappush(pq,(nd+heuristic*.001,nd,nxt))
    if goal not in dist: return []
    path=[goal]; node=goal
    while node!=start: node=prev[node]; path.append(node)
    return path[::-1]


def candidate_tiles(world, radius=3):
    grid,person=world["grid"],world["person"]
    return [(r,c) for r in range(grid.shape[0]) for c in range(grid.shape[1])
            if grid[r,c]==EMPTY and (r,c) not in world["missing"] and
            manhattan((r,c),person)<=radius]


def rule_layout(world):
    """Nearest-free rules, intentionally ignorant of the access route."""
    person=world["person"]; tiles=sorted(candidate_tiles(world),key=lambda p:manhattan(p,person))
    names=("primary","secondary","equipment","replacement","communicator")
    return {name:tiles[i] for i,name in enumerate(names[:len(tiles)])}


def access_path(world,layout=None,crowd_tiles=()):
    blocked=set(world["missing"])|set(crowd_tiles)
    if layout:
        blocked|={p for k,p in layout.items() if k not in ("responder_guide",)}
    goals=[p for p in neighbours(world["person"],world["grid"].shape)
           if world["grid"][p]!=OBSTACLE and p not in blocked]
    paths=[shortest_path(world["grid"],world["entrance"],g,blocked) for g in goals]
    paths=[p for p in paths if p]
    return min(paths,key=len) if paths else []


def layout_metrics(world,layout,previous=None,crowd_tiles=()):
    person=world["person"]; vals=list(layout.values()); path=access_path(world,layout,crowd_tiles)
    conflicts=len(vals)-len(set(vals))
    hazards=sum(world["grid"][p]==OBSTACLE or p in world["missing"] for p in vals)
    primary=layout.get("primary",(-99,-99)); equipment=layout.get("equipment",(-99,-99))
    role_conflict=conflicts+int(manhattan(primary,person)>1)
    equipment_distance=manhattan(equipment,primary) if equipment[0]>=0 else 20
    blockage=0 if path else 1
    unassigned=sum(r not in layout for r in ("primary","equipment","replacement","communicator"))
    moved=0 if previous is None else sum(previous.get(k)!=v for k,v in layout.items())
    movement=sum(manhattan(world["helpers"][i],p) for i,(k,p) in
                 enumerate([(k,v) for k,v in layout.items() if k!="equipment"][:len(world["helpers"])]))
    cost=40*role_conflict+150*blockage+2*movement+5*equipment_distance+180*hazards+35*unassigned+18*moved
    return dict(layout_cost=float(cost),role_conflicts=role_conflict,blocked_path=bool(blockage),
                movement_tiles=int(movement),equipment_distance=int(equipment_distance),
                hazard_occupations=int(hazards),unassigned_roles=int(unassigned),people_moved=int(moved),
                path_length=len(path),access_clear=bool(path))


def optimize_layout(world,previous=None,crowd_tiles=()):
    """Small exhaustive constrained search around the person."""
    person=world["person"]
    newly_blocked=set(crowd_tiles)
    near=[p for p in candidate_tiles(world,3) if manhattan(p,person)<=2 and p not in newly_blocked]
    equip=[p for p in candidate_tiles(world,4) if p not in newly_blocked]
    best=None
    for primary in near:
        if manhattan(primary,person)>1: continue
        for secondary in near:
            if secondary==primary: continue
            for equipment in equip:
                if equipment in (primary,secondary) or manhattan(equipment,primary)>2: continue
                remaining=[p for p in near if p not in (primary,secondary,equipment)]
                if not remaining: continue
                replacement=min(remaining,key=lambda p:manhattan(p,primary))
                layout=dict(primary=primary,secondary=secondary,equipment=equipment,replacement=replacement)
                path=access_path(world,layout,crowd_tiles)
                if not path: continue
                # Place communicator and guide away from the care space, beside clear route endpoints.
                outer=[p for p in candidate_tiles(world,6) if p not in layout.values() and p not in path]
                if outer:
                    layout["communicator"]=max(outer,key=lambda p:manhattan(p,person))
                metrics=layout_metrics(world,layout,previous,crowd_tiles)
                score=metrics["layout_cost"]
                if best is None or score<best[0]: best=(score,layout,metrics,path)
    if best: return dict(layout=best[1],metrics=best[2],path=best[3],fallback=False)
    return dict(layout={},metrics=layout_metrics(world,{},previous,crowd_tiles),path=[],fallback=True)


def manual_layout(world):
    p=world["person"]
    return dict(primary=(p[0],max(0,p[1]-1)),secondary=(p[0],min(world["grid"].shape[1]-1,p[1]+1)),
                equipment=(p[0]+1,p[1]),replacement=(p[0]+2,p[1]))


def assign_roles(helpers):
    roles=["primary","equipment_retriever","communicator","crowd_controller","responder_guide","replacement"]
    rows=[]; used=set()
    for role in roles:
        choices=[]
        for h in helpers:
            if h["id"] in used: continue
            # Training is self-declared/verified; appearance is never an input.
            training_penalty=0 if (role!="primary" or h.get("training_verified",False)) else 35
            mobility_penalty=20 if h.get("mobility")=="limited" and role in ("equipment_retriever","responder_guide") else 0
            carry_bonus=-12 if role=="equipment_retriever" and h.get("carrying_equipment") else 0
            score=10*h.get("fatigue",0)+training_penalty+mobility_penalty+carry_bonus
            choices.append((score,h))
        if choices:
            score,h=min(choices,key=lambda x:x[0]); used.add(h["id"])
            rows.append(dict(role=role,helper=h["id"],assignment_cost=score))
        else: rows.append(dict(role=role,helper="UNASSIGNED",assignment_cost=50))
    return pd.DataFrame(rows)


def sensor_stream(world,layout,n=100,seed=7,failure_rate=.0):
    rng=np.random.default_rng(seed); assigned={v:k for k,v in layout.items()}
    rows=[]
    for i in range(n):
        if assigned and rng.random()<.72: tile=list(assigned)[int(rng.integers(len(assigned)))]
        else: tile=(int(rng.integers(world["grid"].shape[0])),int(rng.integers(world["grid"].shape[1])))
        failure=rng.random()<failure_rate
        pressure=float(rng.normal(620,55)) if not failure else float(rng.choice([0,1400]))
        expected=assigned.get(tile,"none")
        rows.append(dict(timestamp=round(i*.2,1),tile=tile,pressure=pressure,occupied=pressure>120,
                         expected_zone=expected,sensor_fault=failure or pressure>1100))
    return pd.DataFrame(rows)


def feedback(world,result,events=None,crowd_violations=0):
    """Return exactly one highest-priority instruction."""
    if result["metrics"]["blocked_path"]: return "STOP — KEEP THE ACCESS LANE CLEAR"
    if events is not None and len(events) and bool(events.sensor_fault.iloc[-1]): return "SENSOR FAULT — USE VERIFIED SAFE ZONES"
    if crowd_violations: return "CROWD — MOVE BEHIND THE AMBER BOUNDARY"
    if result["metrics"]["equipment_distance"]>2: return "PLACE THE KIT INSIDE THE BLUE OUTLINE"
    if result["layout"]: return "MOVE TO THE GREEN FOOTPRINTS"
    return "WAIT FOR DISPATCHER INSTRUCTIONS"


def compare_controllers(scene: Scene):
    world=build_scene(scene); rng=np.random.default_rng(scene.seed)
    modes=[]
    random_tiles=candidate_tiles(world,5)
    no={r:random_tiles[int(rng.integers(len(random_tiles)))] for r in ("primary","secondary","equipment","replacement")}
    static=manual_layout(world); rule=rule_layout(world); opt=optimize_layout(world)
    for name,layout in (("No mat",no),("Static printed mat",static),("Rule-based illuminated mat",rule)):
        m=layout_metrics(world,layout); modes.append(dict(controller=name,**m))
    modes.append(dict(controller="Optimized mat",**opt["metrics"]))
    dynamic=optimize_layout(world,previous=opt["layout"])
    modes.append(dict(controller="Intelligent dynamic mat",**dynamic["metrics"]))
    return pd.DataFrame(modes)


def environment_scene(name,seed=7):
    specs={
      "Airport hall":(16,14,"East",.08,1.0),"Railway platform":(18,7,"East",.14,.9),
      "Classroom":(12,10,"South",.22,1.0),"Bus aisle":(16,5,"North",.18,.72),
      "Small office":(9,8,"West",.20,.85),"Sports field":(16,16,"North",.02,1.0),
      "Lift lobby":(9,9,"East",.16,.8),"Shopping centre":(15,12,"West",.10,1.0),
      "Roadside shoulder":(18,6,"East",.08,.65)}
    w,h,e,o,m=specs[name]
    return Scene(width=w,height=h,entrance=e,obstacle_ratio=o,mat_fraction=m,seed=seed)


def _layout(fig,height=500,**kw):
    fig.update_layout(height=height,paper_bgcolor=COLORS["bg"],plot_bgcolor=COLORS["bg"],
                      font_color=COLORS["white"],margin=dict(l=45,r=20,t=55,b=45),
                      legend=dict(bgcolor="rgba(0,0,0,0)"),**kw)
    fig.update_xaxes(gridcolor="#21262d"); fig.update_yaxes(gridcolor="#21262d")
    return fig


def fig_grid(world,result=None,title="The mat organizes space, not treatment"):
    grid=world["grid"].astype(float).copy(); text=np.full(grid.shape,"",object)
    grid[grid==OBSTACLE]=1; grid[world["person"]]=2; text[world["person"]]="PERSON"
    text[world["entrance"]]="ENTRY"; grid[world["entrance"]]=7
    text[world["cabinet"]]="KIT"; grid[world["cabinet"]]=4
    for p in world["missing"]: grid[p]=8; text[p]="×"
    if result:
        for p in result.get("path",[]): grid[p]=5; text[p]="⇢"
        code={"primary":3,"secondary":6,"replacement":6,"equipment":4,"communicator":9}
        label={"primary":"P","secondary":"S","replacement":"R","equipment":"KIT","communicator":"COM"}
        for role,p in result.get("layout",{}).items(): grid[p]=code.get(role,3); text[p]=label.get(role,role[:1].upper())
    scale=[[0,COLORS["panel"]],[.12,COLORS["panel"]],[.13,COLORS["grey"]],[.24,COLORS["grey"]],
           [.25,COLORS["red"]],[.36,COLORS["red"]],[.37,COLORS["green"]],[.48,COLORS["green"]],
           [.49,COLORS["blue"]],[.60,COLORS["blue"]],[.61,COLORS["white"]],[.72,COLORS["white"]],
           [.73,COLORS["yellow"]],[.84,COLORS["yellow"]],[.85,COLORS["amber"]],[1,COLORS["purple"]]]
    fig=go.Figure(go.Heatmap(z=grid,text=text,texttemplate="%{text}",colorscale=scale,zmin=0,zmax=9,
                             showscale=False,xgap=2,ygap=2,hovertemplate="tile (%{y}, %{x})<extra></extra>"))
    fig.update_yaxes(autorange="reversed",scaleanchor="x",title="row")
    fig.update_xaxes(title="column")
    return _layout(fig,max(420,world["grid"].shape[0]*34),title=title)


def fig_controller_bars(table):
    fig=go.Figure()
    fig.add_bar(x=table.controller,y=table.layout_cost,name="layout cost",marker_color=COLORS["cyan"])
    fig.add_bar(x=table.controller,y=table.blocked_path.astype(int)*100,name="blocked path ×100",marker_color=COLORS["red"])
    return _layout(fig,420,barmode="group",title="Adaptive layouts protect access with less conflict",yaxis_title="cost / indicator")


def fig_sensor(events):
    colours=np.where(events.sensor_fault,COLORS["red"],np.where(events.expected_zone!="none",COLORS["green"],COLORS["amber"]))
    fig=go.Figure(go.Scatter(x=events.timestamp,y=events.pressure,mode="markers+lines",
                             marker=dict(color=colours,size=7),line=dict(color=COLORS["grey"]),
                             text=events.expected_zone,hovertemplate="%{x:.1f}s · %{y:.0f} · %{text}<extra></extra>"))
    fig.add_hline(y=1100,line_dash="dash",line_color=COLORS["red"],annotation_text="fault threshold")
    return _layout(fig,360,title="Pressure events verify positions and reveal bad sensors",
                   xaxis_title="seconds",yaxis_title="pressure reading")
