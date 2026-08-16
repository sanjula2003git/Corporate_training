"""Deterministic teaching simulation for Guardian Road.

Everything here is synthetic. It is not a traffic controller or safety system.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
import plotly.graph_objects as go

G = 9.81
LANES = ("Left", "Centre", "Right")
COLORS = dict(bg="#0e1117", panel="#161b22", cyan="#4fc3f7", amber="#ffb74d",
              red="#ef5350", green="#66bb6a", blue="#42a5f5", violet="#ba68c8",
              grey="#8b949e", white="#e6edf3")
VEHICLES = {
    "motorcycle": dict(length=2.2, decel=7.2, reaction=1.05, mass_factor=.85),
    "car": dict(length=4.5, decel=6.5, reaction=1.30, mass_factor=1.00),
    "bus": dict(length=12.0, decel=4.3, reaction=1.55, mass_factor=1.28),
    "truck": dict(length=15.0, decel=4.0, reaction=1.65, mass_factor=1.38),
}
WEATHER = {
    "Dry": dict(mu=.78, visibility=900, margin=1.00),
    "Wet": dict(mu=.48, visibility=500, margin=1.14),
    "Fog": dict(mu=.58, visibility=170, margin=1.24),
    "Night": dict(mu=.68, visibility=320, margin=1.12),
    "Heavy rain": dict(mu=.38, visibility=130, margin=1.34),
}


@dataclass
class Scene:
    speed_kmh: float = 72
    weather: str = "Wet"
    reaction_s: float = 1.4
    vehicle_type: str = "car"
    density: float = 34
    left_occupancy: float = .32
    right_occupancy: float = .78
    closest_m: float = 118
    gradient_pct: float = 0
    ambulance_eta_min: float = 9
    detection_confidence: float = .97
    radar_ok: bool = True
    camera_ok: bool = True
    studs_ok: float = 1.0
    communications_ok: bool = True


def stopping_distance(speed_kmh, reaction_s, mu, gradient_pct=0, vehicle_type="car"):
    """Reaction + friction-limited braking distance on a gentle grade."""
    v = speed_kmh / 3.6
    spec = VEHICLES[vehicle_type]
    grade = gradient_pct / 100
    effective_mu = max(.12, mu + grade)
    reaction = v * reaction_s
    friction_decel = effective_mu * G
    decel = min(friction_decel, spec["decel"])
    braking = v * v / (2 * decel)
    return reaction, braking, reaction + braking


def required_warning(scene: Scene, quantile_margin=1.0):
    w = WEATHER[scene.weather]
    reaction, braking, stop = stopping_distance(scene.speed_kmh, scene.reaction_s,
                                                w["mu"], scene.gradient_pct,
                                                scene.vehicle_type)
    density_margin = 1 + .0035 * max(scene.density - 18, 0)
    heavy_margin = VEHICLES[scene.vehicle_type]["mass_factor"]
    visibility_margin = 1 + max(0, 350 - w["visibility"]) / 900
    uncertainty = 18 + 18 * (1 - scene.detection_confidence)
    total = (stop * w["margin"] * density_margin * heavy_margin * visibility_margin
             * quantile_margin + uncertainty)
    return dict(reaction_m=reaction, braking_m=braking, base_stop_m=stop,
                required_m=float(np.clip(total, 60, 650)))


def merge_choice(scene: Scene):
    left = 1 - scene.left_occupancy
    right = 1 - scene.right_occupancy
    if scene.ambulance_eta_min <= 5:
        left -= .32  # preserve the left lane for the ambulance
    if max(scene.left_occupancy, scene.right_occupancy) > .92:
        return "Stop all traffic", "Neither adjacent lane has a safe receiving gap."
    if abs(left - right) < .08:
        return "Split traffic", "The two adjacent lanes have similar spare capacity."
    if left > right:
        return "Merge left", "The left lane has more usable capacity."
    return "Merge right", "The right lane has more usable capacity."


def controller(scene: Scene, mode="Safe AI + ambulance"):
    physics = required_warning(scene)
    fallback = (not scene.camera_ok or not scene.radar_ok or
                not scene.communications_ok or scene.detection_confidence < .72 or
                scene.studs_ok < .65)
    if mode == "No warning":
        warning = 0
    elif mode == "Static sign":
        warning = 80
    elif mode == "Fixed 150 m":
        warning = 150
    elif mode == "Physics minimum":
        warning = physics["required_m"]
    else:
        # Surrogate for a conservative, physics-guided learned residual.
        nonlinear = 14 * (scene.density / 60) ** 2 + 12 * scene.right_occupancy
        warning = max(physics["required_m"], physics["required_m"] + nonlinear - 6)
    direction, why = merge_choice(scene)
    if fallback:
        warning = max(warning, 420)
        direction, why = "Stop all traffic", "Sensor confidence is poor: conservative fallback."
    reserve = mode == "Safe AI + ambulance" and scene.ambulance_eta_min <= 10
    speed_limit = 30 if fallback else (40 if scene.weather in ("Wet", "Fog", "Heavy rain") else 50)
    if scene.speed_kmh <= 50 and not fallback:
        speed_limit = 30 if scene.weather == "Heavy rain" else 40
    return dict(mode=mode, warning_m=int(math.ceil(warning / 10) * 10),
                speed_limit=speed_limit, closed_lane="Centre", merge=direction,
                merge_reason=why, exclusion_m=45 if fallback else 30,
                reserve_ambulance=reserve, fallback=fallback,
                upstream_red=fallback or scene.closest_m < physics["required_m"] * .7,
                physics_min_m=round(physics["required_m"], 1))


def outcome(scene: Scene, action):
    req = required_warning(scene)["required_m"]
    deficit = max(req - action["warning_m"], 0)
    surplus = max(action["warning_m"] - req, 0)
    risk = 1 / (1 + np.exp(-(deficit / 22 - 2.2)))
    if action["upstream_red"]:
        risk *= .35
    decel = min(9.0, 2.0 + 7.0 * deficit / max(req, 1))
    disruption = surplus * .10 + scene.density * (1.2 if action["upstream_red"] else .32)
    if action["merge"] == "Stop all traffic":
        disruption += 48
    blockage = .08 + .38 * scene.left_occupancy
    if action["reserve_ambulance"]:
        blockage *= .22
    return dict(collision_probability=float(np.clip(risk, .004, .98)),
                max_deceleration=float(decel), traffic_delay_s=float(disruption),
                ambulance_blockage=float(np.clip(blockage, 0, 1)),
                minimum_clearance_m=float(max(scene.closest_m - req, -20)))


def build_warning_dataset(n=3500, seed=7):
    rng = np.random.default_rng(seed)
    kinds = np.array(list(VEHICLES))
    weather = np.array(list(WEATHER))
    rows = []
    for _ in range(n):
        s = Scene(speed_kmh=rng.uniform(30, 105), weather=str(rng.choice(weather)),
                  reaction_s=np.clip(rng.normal(1.45, .35), .7, 2.8),
                  vehicle_type=str(rng.choice(kinds, p=[.10, .67, .08, .15])),
                  density=rng.uniform(5, 70), left_occupancy=rng.uniform(.05, .98),
                  right_occupancy=rng.uniform(.05, .98), closest_m=rng.uniform(70, 650),
                  gradient_pct=rng.uniform(-4, 5), detection_confidence=rng.uniform(.72, 1))
        d = asdict(s)
        d.update(required_warning(s, quantile_margin=rng.uniform(.96, 1.12)))
        rows.append(d)
    return pd.DataFrame(rows)


def asymmetric_loss(y_true, y_pred, alpha=8, beta=1):
    err = np.asarray(y_true) - np.asarray(y_pred)
    return np.mean(np.where(err > 0, alpha * err, beta * -err))


def compare_controllers(scene: Scene):
    modes = ["No warning", "Static sign", "Fixed 150 m", "Physics minimum",
             "ML predictor", "Safe AI", "Safe AI + ambulance"]
    rows = []
    for mode in modes:
        a = controller(scene, mode)
        o = outcome(scene, a)
        rows.append(dict(Controller=mode, **a, **o))
    return pd.DataFrame(rows)


def detection_signals(kind="fallen_rider", seconds=16, fps=5, seed=7):
    rng = np.random.default_rng(seed)
    t = np.arange(0, seconds, 1 / fps)
    impact = 3.0
    after = t >= impact
    person_road = np.zeros_like(t)
    horizontal = np.zeros_like(t)
    still = np.zeros_like(t)
    separation = np.zeros_like(t)
    trajectory_change = np.zeros_like(t)
    if kind == "fallen_rider":
        person_road[after], horizontal[after], separation[after] = .94, .9, .96
        still[t >= 4], trajectory_change[t >= 3.3] = .94, .72
    elif kind == "debris":
        horizontal[after], still[after], trajectory_change[t >= 4] = .6, .98, .55
    elif kind == "crossing":
        person_road[(t >= 3) & (t < 7)] = .92
        horizontal[(t >= 3) & (t < 7)] = .12
    elif kind == "worker":
        person_road[after], horizontal[after], still[after] = .82, .56, .60
    elif kind == "shadow":
        horizontal[(t >= 3) & (t < 4.2)] = .7
    noise = lambda: rng.normal(0, .045, len(t))
    df = pd.DataFrame(dict(t=t, person_road=np.clip(person_road + noise(), 0, 1),
                           horizontal=np.clip(horizontal + noise(), 0, 1),
                           still=np.clip(still + noise(), 0, 1),
                           separation=np.clip(separation + noise(), 0, 1),
                           trajectory_change=np.clip(trajectory_change + noise(), 0, 1)))
    df["kind"] = kind
    return df


def detection_probability(df):
    z = (-5 + 1.4 * df.person_road + 1.25 * df.horizontal + 1.6 * df.still
         + 2.0 * df.separation + 1.15 * df.trajectory_change)
    raw = 1 / (1 + np.exp(-z))
    return raw.rolling(5, min_periods=1).mean()


def road_zones(action):
    w = action["warning_m"]
    return pd.DataFrame([
        ("Awareness", w, max(w - 150, 0), "AMBER FLASHING"),
        ("Reduce speed", max(w - 150, 0), 250, f"LIMIT {action['speed_limit']}"),
        ("Merge", min(250, w), 100, action["merge"].upper()),
        ("Exclusion", 100, action["exclusion_m"], "CENTRE LANE CLOSED"),
        ("Rider protection", action["exclusion_m"], 0, "RED SHIELD"),
    ], columns=["zone", "upstream_m", "downstream_m", "pattern"])


def hazard_grid(active_lanes=(0, 1, 2), rider=(8, 22), reserve_lane=0):
    rows, cols = 18, 36
    cost = np.ones((rows, cols))
    for lane in active_lanes:
        y0 = 3 + lane * 4
        cost[y0:y0 + 4, :] = 60
    cost[rider[0]-2:rider[0]+3, rider[1]-3:rider[1]+4] = 400
    cost[3 + reserve_lane * 4:7 + reserve_lane * 4, :] = 25
    cost[:3, :] = 2
    cost[15:, :] = 2
    return cost


def plan_path(cost, start=(17, 2), goal=(8, 22)):
    pq = [(0, start)]
    prev, dist = {}, {start: 0}
    while pq:
        d, node = heapq.heappop(pq)
        if node == goal:
            break
        if d != dist[node]:
            continue
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nxt = node[0] + dr, node[1] + dc
            if not (0 <= nxt[0] < cost.shape[0] and 0 <= nxt[1] < cost.shape[1]):
                continue
            nd = d + float(cost[nxt])
            if nd < dist.get(nxt, math.inf):
                dist[nxt], prev[nxt] = nd, node
                heapq.heappush(pq, (nd, nxt))
    if goal not in dist:
        return []
    path, node = [goal], goal
    while node != start:
        node = prev[node]
        path.append(node)
    return path[::-1]


def _layout(fig, height=420, **kwargs):
    fig.update_layout(height=height, paper_bgcolor=COLORS["bg"], plot_bgcolor=COLORS["bg"],
                      font_color=COLORS["white"], margin=dict(l=45,r=20,t=55,b=40),
                      legend=dict(bgcolor="rgba(0,0,0,0)"), **kwargs)
    fig.update_xaxes(gridcolor="#21262d")
    fig.update_yaxes(gridcolor="#21262d")
    return fig


def fig_road(scene: Scene, action, closest=None):
    closest = scene.closest_m if closest is None else closest
    w = max(action["warning_m"], 200)
    fig = go.Figure()
    for lane in range(3):
        y0 = lane
        fig.add_shape(type="rect", x0=0, x1=w, y0=y0, y1=y0+1,
                      fillcolor="#161b22", line=dict(color="#30363d"))
    for x in np.arange(20, w, 25):
        colour = COLORS["amber"] if x > 100 else COLORS["red"]
        fig.add_scatter(x=[x], y=[1.5], mode="markers", marker=dict(color=colour, size=8),
                        showlegend=False, hovertext="connected road stud")
    fig.add_scatter(x=[0], y=[1.5], mode="markers+text", text=["fallen rider"],
                    textposition="top center", marker=dict(color=COLORS["red"], size=18),
                    name="rider")
    xs = [min(closest, w*.94), min(closest+55, w*.98), min(closest+105, w*.99)]
    ys = [1.5, .5, 2.5]
    fig.add_scatter(x=xs, y=ys, mode="markers+text", text=[f"{scene.speed_kmh:.0f} km/h","car","truck"],
                    textposition="top center", marker=dict(color=COLORS["cyan"], size=[15,12,18]),
                    name="approaching traffic")
    fig.add_vrect(x0=0, x1=action["exclusion_m"], fillcolor=COLORS["red"], opacity=.18,
                  annotation_text="exclusion", annotation_font_color="white")
    fig.add_vline(x=action["warning_m"], line_color=COLORS["amber"], line_dash="dash",
                  annotation_text="warning begins", annotation_font_color="white")
    fig.update_yaxes(tickvals=[.5,1.5,2.5], ticktext=list(LANES), range=[0,3])
    fig.update_xaxes(autorange="reversed", title="metres upstream from rider")
    return _layout(fig, 360, title=f"{action['merge']} · centre lane closed · limit {action['speed_limit']} km/h")


def fig_tradeoff(scene: Scene):
    rows=[]
    req=required_warning(scene)["required_m"]
    for d in np.arange(50, 501, 10):
        a=controller(scene, "Safe AI")
        a["warning_m"]=d
        o=outcome(scene,a)
        rows.append((d,o["collision_probability"],o["max_deceleration"],o["traffic_delay_s"]))
    df=pd.DataFrame(rows,columns=["warning","risk","braking","delay"])
    fig=go.Figure()
    fig.add_scatter(x=df.warning,y=df.risk,name="collision probability",line=dict(color=COLORS["red"],width=3))
    fig.add_scatter(x=df.warning,y=df.delay/100,name="traffic delay (÷100)",line=dict(color=COLORS["amber"],width=3))
    fig.add_vline(x=req,line_dash="dash",line_color=COLORS["green"],annotation_text="physics minimum")
    return _layout(fig,title="Safety improves with distance; disruption grows",xaxis_title="warning distance (m)")


def fig_detection():
    fig=go.Figure()
    for kind,colour in zip(("fallen_rider","debris","crossing","worker","shadow"),
                           (COLORS["red"],COLORS["violet"],COLORS["green"],COLORS["amber"],COLORS["grey"])):
        d=detection_signals(kind)
        fig.add_scatter(x=d.t,y=detection_probability(d),name=kind.replace("_"," "),line=dict(color=colour,width=2.4))
    fig.add_hline(y=.72,line_dash="dash",line_color="white",annotation_text="confirmation threshold")
    return _layout(fig,title="A sequence separates the fallen rider from lookalikes",xaxis_title="seconds",yaxis_title="obstruction probability")


def fig_hazard(cost, path):
    fig=go.Figure(go.Heatmap(z=np.log10(cost),colorscale="Inferno",showscale=False))
    if path:
        fig.add_scatter(x=[p[1] for p in path],y=[p[0] for p in path],mode="lines",
                        line=dict(color=COLORS["green"],width=5),name="protected bystander route")
    return _layout(fig,360,title="Route shown only after traffic protection is established",
                   xaxis_title="distance along segment",yaxis_title="across the road")
