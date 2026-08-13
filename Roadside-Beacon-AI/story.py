"""The virtual intersection, the four detectors, and the figures the app draws.

This is a trimmed version of the notebook's model, sized to run inside a 1 GB
Streamlit Cloud container: fewer clips, a smaller forest, and no TensorFlow
(the sequence network is illustrated rather than trained live). The scenarios,
the features and the thresholds are the notebook's.

Nothing here is a medical or safety device. It is a teaching simulation.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestClassifier

BG = "#0e1117"
CYAN = "#4fc3f7"
AMBER = "#ffb74d"
RED = "#ef5350"
GREEN = "#66bb6a"
VIOLET = "#ba68c8"
GREY = "#8b949e"

# --------------------------------------------------------------- the world
FPS = 5                      # frames per second the edge box actually looks at
CLIP_SECS = 24
FRAMES = FPS * CLIP_SECS
ROAD_X = 60.0                # metres of road in view
ROAD_Y = 20.0                # metres across, footpath to footpath
LANE = (6.0, 14.0)           # the carriageway: everything between these is traffic
LANE_MID = (8.0, 12.0)       # the middle of each of the two lanes
WIN = 6 * FPS                # a six second window is what the sequence models see

# Which scenarios are a real incident, what a bystander sees, and - the number
# that turned out to matter most - how often each one belongs in the pile. A
# camera on a junction sees hundreds of red lights for every crash. Train on a
# tidy 50/50 mix and the model learns that stopped traffic means a crash.
SCENARIOS = {
    "normal":       dict(incident=0, mix=8, tag="Traffic flows"),
    "crossing":     dict(incident=0, mix=5, tag="Someone crosses the road"),
    "hard_brake":   dict(incident=0, mix=4, tag="A car brakes hard, and misses"),
    "shoe_tie":     dict(incident=0, mix=3, tag="Someone crouches at the kerb"),
    "worker":       dict(incident=0, mix=2, tag="A mechanic lies under a van"),
    "poster":       dict(incident=0, mix=2, tag="A fallen board that looks like a person"),
    "bus_crowd":    dict(incident=0, mix=3, tag="A crowd builds at the bus stop"),
    "red_light":    dict(incident=0, mix=8, tag="The signal turns red and traffic waits"),
    "jam":          dict(incident=0, mix=5, tag="Slow rush-hour crawl"),
    "collision_down": dict(incident=1, mix=4, tag="Motorcycle down, rider not moving"),
    "collision_up":   dict(incident=1, mix=3, tag="Motorcycle down, rider walks off"),
    "ped_fall":     dict(incident=1, mix=3, tag="A pedestrian is knocked down"),
    "rollover":     dict(incident=1, mix=2, tag="A van rolls over, smoke rising"),
    "occluded":     dict(incident=1, mix=2, tag="A crash behind a stopped bus"),
}
BENIGN = [k for k, v in SCENARIOS.items() if not v["incident"]]
REAL = [k for k, v in SCENARIOS.items() if v["incident"]]

# What the perception layer reports for every frame. A real system reads these
# off boxes and tracks; here we simulate them directly.
SIGNALS = ["person_road", "person_low", "low_still", "crowd", "veh_stopped",
           "min_gap", "closing", "decel_max", "smoke", "flow"]


def _noise(rng, n, sd, k=5):
    """Slow drifting noise, so signals wander instead of jumping every frame."""
    w = rng.normal(0, sd, n + k)
    return np.convolve(w, np.ones(k) / k, mode="same")[:n] * np.sqrt(k)


def _clip(rng, kind):
    """One 24-second clip of what the camera's tracker reports, frame by frame."""
    n = FRAMES
    t = np.arange(n) / FPS
    s = {k: np.zeros(n) for k in SIGNALS}
    s["flow"] += rng.uniform(9.5, 12.5) + _noise(rng, n, 0.35)
    s["min_gap"] += rng.uniform(14, 22) + _noise(rng, n, 1.2)
    s["closing"] += rng.uniform(0.5, 2.5) + np.abs(_noise(rng, n, 0.6))
    s["decel_max"] += np.abs(rng.normal(0.9, 0.45, n))
    s["crowd"] += rng.integers(0, 2, n)
    impact = np.nan

    def down(start, still=True, until=n, low=1.0):
        """A person is on the carriageway and low from `start` onwards."""
        idx = np.arange(int(start), int(until))
        s["person_road"][idx] = 1
        s["person_low"][idx] = low
        s["low_still"][idx] = 1.0 if still else 0.0

    def ramp(start, secs):
        """0 before `start`, sliding up to 1 over `secs` seconds.

        Nothing in a crash scene appears instantly. Traffic takes a few seconds
        to come to a stop, a crowd takes ten or more to gather, smoke builds.
        Building that in is what gives the detectors something to wait for -
        and what makes 'seconds until the alarm' an honest number.
        """
        return np.clip((np.arange(n) - start) / max(1.0, secs * FPS), 0, 1)

    def hit(f, gap=None, close=9.0, decel=7.5):
        """The half second in which two tracks meet - or nearly meet."""
        gap = rng.uniform(0.25, 1.30) if gap is None else gap
        idx = np.arange(int(f), min(n, int(f) + 3))
        # a distance measured from a camera 30 m away is not measured well
        s["min_gap"][idx] = max(0.05, gap + rng.normal(0, 0.35))
        s["closing"][idx] = close + rng.uniform(-1.5, 1.5)
        s["decel_max"][idx] = decel + rng.uniform(-1.5, 2.0)

    if kind == "normal":
        pass

    elif kind == "crossing":
        a = rng.integers(20, 60)
        idx = np.arange(a, min(n, a + rng.integers(20, 35)))
        s["person_road"][idx] = 1
        s["veh_stopped"][idx] = rng.integers(1, 3)
        s["flow"][idx] *= 0.35
        s["min_gap"][idx] = rng.uniform(3.0, 6.0)

    elif kind == "hard_brake":
        # The near miss. Everything an impact has, except the impact. The gap and
        # the braking overlap the real collisions on purpose - from 30 metres up
        # a pole, a miss by half a metre and a hit look the same for one instant.
        a = int(rng.integers(25, 70))
        hit(a)                                   # exactly a collision's signature
        # Traffic stops the same way it stops for a crash, and then - the only
        # difference in the whole clip - it starts moving again, five seconds
        # later, with nobody lying in the road and no crowd walking over.
        stop = ramp(a, rng.uniform(1.5, 2.5)) * (1 - ramp(a + int(2.5 * FPS), rng.uniform(2, 3)))
        s["flow"] *= (1 - 0.75 * stop)
        s["veh_stopped"] += rng.uniform(2, 4) * ramp(a + FPS, 1.5) * \
            (1 - ramp(a + 3 * FPS, 2.5))
        # Half of these are a pedestrian stepping out, half a car cutting in. If
        # every near miss had a pedestrian in it, "was someone on the road just
        # before the bang" would separate a miss from a hit on its own, and the
        # detectors would look far cleverer than they are.
        if rng.random() < 0.5:
            p = np.arange(max(0, a - 8), min(n, a + 14))
            s["person_road"][p] = 1

    elif kind == "shoe_tie":
        a = int(rng.integers(10, 55))
        down(a, still=True, until=min(n, a + rng.integers(35, 70)), low=1.0)
        s["low_still"][:] = np.where(s["person_low"] > 0, rng.uniform(0.6, 1.0), 0)

    elif kind == "worker":
        # A mechanic under a van at the edge of the lane, there before we looked.
        down(0, still=True, until=n)
        s["veh_stopped"][:] = 1
        s["flow"] *= 0.8

    elif kind == "poster":
        # A fallen board. The detector calls it a person on most frames.
        keep = rng.random(n) < 0.72
        s["person_road"][keep] = 1
        s["person_low"][keep] = 1
        s["low_still"][keep] = 1

    elif kind == "bus_crowd":
        a = int(rng.integers(10, 50))
        idx = np.arange(a, n)
        s["crowd"][idx] = np.clip(np.linspace(1, rng.uniform(6, 9), len(idx)), 0, 12)

    elif kind == "red_light":
        # The most important quiet clip in the set. Traffic stops dead and stays
        # stopped for twenty seconds, several times an hour, all day long. Any
        # detector that reads "traffic has stopped" as "crash" calls the control
        # centre every cycle of every signal in the city.
        a = int(rng.integers(10, 45))
        hold = int(rng.uniform(14, 22) * FPS)
        stop = ramp(a, rng.uniform(2, 3.5)) * (1 - ramp(a + hold, 3.0))
        s["flow"] *= (1 - 0.92 * stop)
        s["veh_stopped"] += rng.uniform(4, 8) * stop

    elif kind == "jam":
        s["flow"] *= rng.uniform(0.18, 0.35)
        s["veh_stopped"] += rng.uniform(1, 4) * np.clip(_noise(rng, n, 0.5) + 1, 0, 2)

    elif kind in ("collision_down", "collision_up"):
        a = int(rng.integers(30, 70))
        impact = a / FPS
        hit(a)
        s["flow"] *= (1 - 0.80 * ramp(a, rng.uniform(2.5, 4.5)))
        s["veh_stopped"] += rng.uniform(3, 6) * ramp(a + 2 * FPS, rng.uniform(3, 6))
        s["crowd"] += rng.uniform(3.5, 7.5) * ramp(a + 4 * FPS, rng.uniform(8, 14))
        if kind == "collision_down":
            down(a + 3, still=True)              # the rider slides, then stops
        else:
            # The rider is up in a few seconds and walks to the kerb. Still an
            # incident: a blocked lane, a shaken rider, a bike in the road.
            up = a + int(rng.integers(8, 18))
            down(a + 3, still=True, until=up)
            s["person_road"][np.arange(up, min(n, up + 20))] = 1

    elif kind == "ped_fall":
        a = int(rng.integers(30, 70))
        impact = a / FPS
        hit(a, gap=rng.uniform(0.3, 1.0), close=rng.uniform(4.5, 7.0),
            decel=rng.uniform(5.0, 8.0))
        s["flow"] *= (1 - 0.70 * ramp(a, rng.uniform(2.5, 5.0)))
        s["veh_stopped"] += rng.uniform(2, 5) * ramp(a + 2 * FPS, rng.uniform(3, 6))
        s["crowd"] += rng.uniform(2.5, 6.0) * ramp(a + 5 * FPS, rng.uniform(8, 15))
        s["person_road"][np.arange(max(0, a - 10), a)] = 1     # they were crossing
        down(a + 2, still=True)

    elif kind == "rollover":
        # Nobody is visible on the road at all. The van is on its side.
        a = int(rng.integers(30, 70))
        impact = a / FPS
        hit(a, gap=rng.uniform(0.4, 1.2), close=rng.uniform(5.0, 8.0),
            decel=rng.uniform(6.0, 9.5))
        s["flow"] *= (1 - 0.75 * ramp(a, rng.uniform(3.0, 5.0)))
        s["veh_stopped"] += rng.uniform(2, 5) * ramp(a + 2 * FPS, rng.uniform(3, 6))
        s["smoke"] += rng.uniform(0.55, 0.95) * ramp(a + 3 * FPS, rng.uniform(5, 9))
        s["crowd"] += rng.uniform(1.5, 4.0) * ramp(a + 6 * FPS, rng.uniform(8, 15))

    elif kind == "occluded":
        # The crash happens behind a bus that has just pulled in. The camera can
        # see that traffic has stopped, and nothing else at all, until the bus
        # pulls away about ten seconds later. No model can fix a blocked view.
        a = int(rng.integers(25, 55))
        impact = a / FPS
        clear = a + int(rng.uniform(9, 13) * FPS)
        s["flow"] *= (1 - 0.80 * ramp(a, rng.uniform(2.0, 4.0)))
        s["veh_stopped"] += rng.uniform(3, 6) * ramp(a + FPS, rng.uniform(2, 4))
        if clear < n:
            down(clear, still=True)
            s["crowd"] += rng.uniform(3.0, 6.0) * ramp(clear, rng.uniform(2, 5))

    # ---------- the detector is not perfect ----------
    flip = rng.random(n) < 0.04                       # posture read from a box is noisy
    s["person_low"] = np.where(flip, 1 - s["person_low"], s["person_low"])
    miss = rng.random(n) < 0.03                       # the person is not found at all
    s["person_road"] = np.where(miss, 0, s["person_road"])
    s["person_low"] = np.where(miss, 0, s["person_low"])
    s["crowd"] = np.clip(s["crowd"] + rng.integers(-1, 2, n), 0, 15)
    s["smoke"] = np.clip(s["smoke"] + rng.normal(0, 0.03, n), 0, 1)
    s["flow"] = np.clip(s["flow"] + _noise(rng, n, 0.3), 0, 25)

    out = pd.DataFrame(s)
    out.insert(0, "t", t)
    out.insert(0, "frame", np.arange(n))
    out["incident"] = SCENARIOS[kind]["incident"]
    out["impact_t"] = impact
    # The truth we score against: from the moment of impact onwards.
    out["truth"] = ((out["incident"] == 1) & (out["t"] >= (impact if impact == impact else 1e9))).astype(int)
    return out


def build_clips(scale=3, seed=7):
    """A pile of short clips from one camera, mixed the way the road mixes them."""
    rng = np.random.default_rng(seed)
    parts, meta, cid = [], [], 0
    for kind in SCENARIOS:
        for _ in range(SCENARIOS[kind]["mix"] * scale):
            df = _clip(rng, kind)
            df.insert(0, "clip_id", cid)
            df.insert(1, "kind", kind)
            parts.append(df)
            meta.append(dict(clip_id=cid, kind=kind, incident=SCENARIOS[kind]["incident"],
                             impact_t=df["impact_t"].iloc[0]))
            cid += 1
    frames = pd.concat(parts, ignore_index=True)
    return frames, pd.DataFrame(meta)


# --------------------------------------------------------------- time features
def add_time_features(frames):
    """The clues that do not exist in a single frame."""
    f = frames.copy()
    # Is somebody lying in the road? Read frame by frame this flickers, because a
    # posture guessed from a box is wrong now and then. Take the middle value of
    # the last second before believing it - otherwise every rule below breaks on
    # noise rather than on its own logic.
    raw = ((f["person_low"] > 0) & (f["person_road"] > 0)).astype(float)
    f["lying"] = (raw.groupby(f["clip_id"], sort=False)
                  .transform(lambda s: s.rolling(FPS, min_periods=1).median())
                  .round().astype(int))
    secs = []
    for _, part in f.groupby("clip_id", sort=False):
        run, out = 0, []
        for v in part["lying"].to_numpy():
            run = run + 1 if v else 0
            out.append(run / FPS)
        secs.extend(out)
    f["down_secs"] = secs
    g = f.groupby("clip_id", sort=False)
    f["crowd_growth"] = g["crowd"].transform(lambda s: s - s.shift(3 * FPS)).fillna(0)
    f["flow_drop"] = g["flow"].transform(lambda s: s.shift(4 * FPS) - s).fillna(0)
    f["decel_peak"] = g["decel_max"].transform(lambda s: s.rolling(WIN, min_periods=1).max())
    f["gap_min"] = g["min_gap"].transform(lambda s: s.rolling(WIN, min_periods=1).min())
    f["close_max"] = g["closing"].transform(lambda s: s.rolling(WIN, min_periods=1).max())
    f["smoke_max"] = g["smoke"].transform(lambda s: s.rolling(WIN, min_periods=1).max())
    f["still_frac"] = g["low_still"].transform(lambda s: s.rolling(WIN, min_periods=1).mean())
    f["road_frac"] = g["person_road"].transform(lambda s: s.rolling(WIN, min_periods=1).mean())
    f["stopped_max"] = g["veh_stopped"].transform(lambda s: s.rolling(WIN, min_periods=1).max())
    return f


# What the window model is allowed to look at. Note what is NOT here: the plain
# traffic speed. A first version included it, and the forest quietly learned
# "this clip is a bit slower than average, so it is a crash" - a fact about our
# clips, not about crashes. Only the *change* in flow survives.
WINDOW_FEATURES = ["down_secs", "crowd", "crowd_growth", "flow_drop",
                   "decel_peak", "gap_min", "close_max", "smoke_max",
                   "still_frac", "road_frac", "stopped_max"]


# --------------------------------------------------------------- the detectors
def alarm_single_frame(f):
    """Model 1. One picture, one rule: a person is lying in the road."""
    return ((f["person_low"] > 0) & (f["person_road"] > 0)).to_numpy()


def alarm_rules(f, hold_secs=6.0, smoke_level=0.5):
    """Model 2. The same rule, but it has to hold, plus a smoke rule."""
    return ((f["down_secs"] >= hold_secs) | (f["smoke_max"] >= smoke_level)).to_numpy()


def confirm(fire, f, secs=2.0):
    """Only believe an alarm once the evidence has held for `secs` seconds.

    This is the dial that matters. Fire the instant something looks wrong and
    you catch every crash and also every near miss; wait three seconds and the
    near misses drive away by themselves - but the crash is three seconds older.
    """
    k = int(round(secs * FPS))
    fire = np.asarray(fire)
    if k <= 1:
        return fire.copy()
    out = np.zeros(len(fire), bool)
    for _, part in f.groupby("clip_id", sort=False):
        idx = part.index.to_numpy()
        run, o = 0, np.zeros(len(idx), bool)
        for i, x in enumerate(fire[idx]):
            run = run + 1 if x else 0
            o[i] = run >= k
        out[idx] = o
    return out


def train_forest(train, n_estimators=60, seed=7):
    forest = RandomForestClassifier(n_estimators=n_estimators, max_depth=10,
                                    min_samples_leaf=25, class_weight="balanced_subsample",
                                    n_jobs=1, random_state=seed)
    forest.fit(train[WINDOW_FEATURES].to_numpy(np.float32), train["truth"].to_numpy())
    return forest


def split_clips(meta, seed=7):
    """Three piles of clips: to learn from, to set the dial, to be judged on.

    Split inside each scenario, not across the whole pile. Otherwise a rare
    scenario - the rollover, say - can miss the exam set completely, and the
    scoreboard quietly stops testing the case it was built for.
    """
    rng = np.random.default_rng(seed)
    train, tune, test = [], [], []
    for kind in SCENARIOS:
        ids = meta.loc[meta["kind"] == kind, "clip_id"].to_numpy().copy()
        rng.shuffle(ids)
        n = len(ids)
        train.extend(ids[: int(0.5 * n)])
        tune.extend(ids[int(0.5 * n): int(0.7 * n)])
        test.extend(ids[int(0.7 * n):])
    return np.array(train), np.array(tune), np.array(test)


# --------------------------------------------------------------- scoring
def score_detector(f, fire, meta, clips):
    """Seconds lost, false alarms per hour, and incidents never seen."""
    fire = np.asarray(fire)
    lat, false_clips, missed, caught = [], 0, 0, 0
    for c in clips:
        row = meta[meta["clip_id"] == c].iloc[0]
        part = f[f["clip_id"] == c]
        hit_idx = np.flatnonzero(fire[part.index])
        t_first = float(part["t"].to_numpy()[hit_idx[0]]) if len(hit_idx) else np.nan
        if row.incident:
            if np.isnan(t_first) or t_first < row.impact_t:
                # an alarm before the impact is not a detection of it
                after = [tt for tt in part["t"].to_numpy()[hit_idx] if tt >= row.impact_t]
                t_first = after[0] if after else np.nan
            if np.isnan(t_first):
                missed += 1
            else:
                caught += 1
                lat.append(t_first - row.impact_t)
        else:
            false_clips += int(len(hit_idx) > 0)
    benign = [c for c in clips if not meta[meta["clip_id"] == c].iloc[0].incident]
    hours = len(benign) * CLIP_SECS / 3600.0
    return dict(
        caught=caught, missed=missed,
        seconds=round(float(np.median(lat)), 1) if lat else np.nan,
        false_clips=false_clips, benign_clips=len(benign),
        false_per_hour=round(false_clips / hours, 1) if hours else np.nan)


def pick_level(f, risk, meta, clips, per_hour=1.0):
    """The alarm level that keeps false alarms under a budget, on tuning clips."""
    lo, hi = 0.0, 1.0
    for _ in range(20):
        mid = (lo + hi) / 2
        r = score_detector(f, risk >= mid, meta, clips)
        if r["false_per_hour"] > per_hour:
            lo = mid
        else:
            hi = mid
    return round(hi, 4)


# --------------------------------------------------------------- the scene
GRID = (24, 8)          # 2.5 m cells across a 60 m x 20 m view


def hazard_grid(smoke=False, glass=True, wire=False):
    """Cost of standing in each cell. High cost is a place nobody should walk.

    Rows 0-1 and 6-7 are footpath, rows 2-5 are the road. The number is not a
    distance - it is how much we do not want a person there, and the gap between
    the footpath (1) and a live lane (25) is the whole point.
    """
    nx, ny = GRID
    cost = np.ones((ny, nx))
    cost[2:4, :] = 2.0                     # the crash lane: blocked, nothing moves through it
    cost[4:6, :] = 25.0                    # the opposite lane: still moving
    cost[4:6, 16:21] = 2.0                 # except by the junction, where the signal holds it
    if glass:
        cost[2:5, 11:14] = np.maximum(cost[2:5, 11:14], 9.0)
    if smoke:
        cost[3:6, 14:19] = 60.0
    if wire:
        cost[:, 20:23] = 90.0
    return cost


def plan_path(cost, start, goal):
    """Cheapest way in, by Dijkstra. Cost is danger, not distance."""
    import heapq
    ny, nx = cost.shape
    dist = np.full((ny, nx), np.inf)
    prev = {}
    sj, si = start
    dist[sj, si] = 0
    q = [(0.0, (sj, si))]
    while q:
        d, (j, i) = heapq.heappop(q)
        if (j, i) == goal:
            break
        if d > dist[j, i]:
            continue
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nj, ni = j + dj, i + di
            if 0 <= nj < ny and 0 <= ni < nx:
                nd = d + cost[nj, ni]
                if nd < dist[nj, ni]:
                    dist[nj, ni] = nd
                    prev[(nj, ni)] = (j, i)
                    heapq.heappush(q, (nd, (nj, ni)))
    if goal not in prev and goal != start:
        return [], np.inf
    path, node = [goal], goal
    while node != start:
        node = prev[node]
        path.append(node)
    return path[::-1], float(dist[goal])


# --------------------------------------------------------------- the procedure
MODULES = {
    "scene_safety": "Make the scene safer first",
    "unresponsive": "Person not responding - approved module",
    "bleeding": "Severe visible bleeding - pressure module",
    "helmet": "Motorcycle rider with a helmet - do not remove it",
    "trapped": "Person trapped or vehicle unstable - wait for the crew",
    "dispatcher": "Live dispatcher, no automatic module",
}


def choose_module(scene):
    """The selector. A short list of guards, checked in a fixed order.

    It is deliberately not a chatbot. Every branch returns the name of a
    pre-approved video, and any branch may be overridden by the dispatcher.
    """
    if scene.get("dispatcher_override"):
        return "dispatcher", "A dispatcher has taken the screen."
    if scene.get("smoke") or scene.get("live_traffic") or scene.get("wire"):
        return "scene_safety", "The scene is not safe to approach yet."
    if scene.get("trapped") or scene.get("vehicle_unstable"):
        return "trapped", "Moving this person could do more harm than waiting."
    if scene.get("severe_bleeding_confirmed"):
        return "bleeding", "Bleeding that a dispatcher has confirmed comes first."
    if scene.get("unresponsive_confirmed_by_dispatch"):
        return "unresponsive", "Confirmed by the dispatcher, not by the camera."
    if scene.get("helmet"):
        return "helmet", "A helmet stays on unless a dispatcher says otherwise."
    return "dispatcher", "Not enough is visible. Connect a person."


# --------------------------------------------------------------- the helper
CHECKS = [
    ("approach_side", "Helper is walking in from the traffic side",
     "STOP - come round from the footpath side"),
    ("moving_victim", "Helper is dragging the rider",
     "STOP - do not move them unless there is fire or traffic"),
    ("helmet_off", "Helper is pulling the helmet off",
     "STOP - leave the helmet on until the dispatcher says"),
    ("crowd_close", "The crowd is standing over the rider",
     "Give them space, and keep the lane clear"),
    ("pressure_released", "Pressure on the wound keeps coming off",
     "Press again, hard, and do not let go"),
    ("lane_blocked", "The ambulance lane is blocked",
     "Move to the footpath, the ambulance needs this lane"),
]


def check_helper(obs):
    """Red, amber and green, for the things a camera can honestly see."""
    out = []
    for key, seen, message in CHECKS:
        if obs.get(key):
            colour = "red" if key in ("approach_side", "moving_victim", "helmet_off") else "amber"
            out.append(dict(colour=colour, seen=seen, message=message))
    if not out:
        out.append(dict(colour="green", seen="Helper is in the position that was shown",
                        message="Good. Keep going, help is on the way."))
    return out


def assign_roles(people):
    """Give the crowd jobs. Nearest able person to each job, most urgent first."""
    jobs = [("Press the help button and talk to the dispatcher", "screen"),
            ("Warn the traffic, upstream of the crash", "upstream"),
            ("Bring the emergency box from the cabinet", "cabinet"),
            ("Wave the ambulance in at the junction", "junction")]
    spots = dict(screen=(6.0, 17.0), upstream=(4.0, 10.0), cabinet=(9.0, 17.5),
                 junction=(56.0, 16.0))
    free = list(people)
    out = []
    for label, spot in jobs:
        if not free:
            out.append(dict(job=label, who=None, walk=np.nan))
            continue
        gx, gy = spots[spot]
        d = [np.hypot(p["x"] - gx, p["y"] - gy) for p in free]
        k = int(np.argmin(d))
        out.append(dict(job=label, who=free[k]["name"], walk=round(float(d[k]), 1)))
        free.pop(k)
    return pd.DataFrame(out)


# --------------------------------------------------------------- did it help
def outcome_sim(detect_secs, n=400, seed=7, with_beacon=True):
    """One incident, played many times, with and without the beacon.

    The delays without a beacon are the assumptions of this teaching model, not
    measurements. They are written here so a student can argue with them.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        if with_beacon:
            t_detect = max(0.0, rng.normal(detect_secs, 1.2))
            t_call = t_detect + rng.uniform(1.0, 3.0)
            t_help = t_call + rng.uniform(8.0, 30.0)
            unsafe = int(rng.random() < 0.12) + int(rng.random() < 0.10)
            lane_clear = t_call + rng.uniform(20.0, 70.0)
        else:
            t_detect = rng.uniform(5.0, 40.0)
            t_call = t_detect + (rng.uniform(20.0, 120.0) if rng.random() > 0.15
                                 else rng.uniform(150.0, 300.0))
            t_help = t_detect + rng.uniform(10.0, 60.0)
            unsafe = int(rng.random() < 0.40) + int(rng.random() < 0.35)
            lane_clear = t_call + rng.uniform(60.0, 240.0)
        rows.append(dict(detect=t_detect, call=t_call, help=t_help,
                         unsafe=unsafe, lane=lane_clear))
    return pd.DataFrame(rows)


def outcome_table(detect_secs, n=400, seed=7):
    a = outcome_sim(detect_secs, n, seed, with_beacon=False)
    b = outcome_sim(detect_secs, n, seed, with_beacon=True)
    rows = []
    for label, col in (("Seconds to notice", "detect"), ("Seconds to the 112 call", "call"),
                       ("Seconds to first safe help", "help"),
                       ("Seconds until the lane is clear", "lane")):
        rows.append({"What we measure": label,
                     "No beacon": int(np.median(a[col])),
                     "With beacon": int(np.median(b[col]))})
    rows.append({"What we measure": "Harmful actions per incident",
                 "No beacon": round(float(a["unsafe"].mean()), 2),
                 "With beacon": round(float(b["unsafe"].mean()), 2)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------- figures
def _layout(fig, height=400, **kw):
    fig.update_layout(height=height, paper_bgcolor=BG, plot_bgcolor=BG, font_color="white",
                      margin=dict(l=45, r=20, t=45, b=40),
                      legend=dict(bgcolor="rgba(0,0,0,0)"), **kw)
    fig.update_xaxes(gridcolor="#21262d")
    fig.update_yaxes(gridcolor="#21262d")
    return fig


def fig_golden_minutes():
    """Why the first minutes are the whole game."""
    mins = np.arange(0, 11, 0.25)
    survive = 100 * np.exp(-mins / 4.5)
    fig = go.Figure()
    fig.add_scatter(x=mins, y=survive, line=dict(color=CYAN, width=3),
                    name="chance of a good outcome")
    fig.add_vrect(x0=0, x1=4, fillcolor=GREEN, opacity=0.12, line_width=0,
                  annotation_text="before the ambulance arrives",
                  annotation_font_color="white")
    return _layout(fig, xaxis_title="minutes after the crash",
                   yaxis_title="relative chance of a good outcome",
                   title="The shape every emergency service works to")


def fig_scene(kind="collision_down"):
    """A plan view of the intersection the camera watches."""
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, x1=ROAD_X, y0=LANE[0], y1=LANE[1],
                  fillcolor="#161b22", line_width=0)
    fig.add_hline(y=10, line_dash="dash", line_color=GREY)
    for y, label in ((3.0, "footpath"), (17.0, "footpath")):
        fig.add_shape(type="rect", x0=0, x1=ROAD_X, y0=y - 3, y1=y + 3,
                      fillcolor="#0d1117", line=dict(color="#30363d"))
    fig.add_scatter(x=[6], y=[17.5], mode="markers+text", text=["screen"],
                    textposition="top center", marker=dict(color=CYAN, size=16, symbol="square"),
                    name="public screen")
    fig.add_scatter(x=[2], y=[18.5], mode="markers+text", text=["camera"],
                    textposition="top center", marker=dict(color=VIOLET, size=13, symbol="diamond"),
                    name="camera")
    if kind == "collision_down":
        fig.add_scatter(x=[30], y=[9], mode="markers+text", text=["rider down"],
                        textposition="bottom center", marker=dict(color=RED, size=16),
                        name="person on the road")
        fig.add_scatter(x=[33, 27, 31], y=[12, 11, 13], mode="markers",
                        marker=dict(color=AMBER, size=11), name="bystanders")
    fig.update_yaxes(range=[0, ROAD_Y], title="metres across")
    fig.update_xaxes(range=[0, ROAD_X], title="metres along the road")
    return _layout(fig, height=340, title="One intersection, one camera, one screen")


def fig_signals(frames, clip, title):
    part = frames[frames["clip_id"] == clip]
    fig = go.Figure()
    fig.add_scatter(x=part.t, y=part.person_low, name="person lying (0/1)",
                    line=dict(color=RED, width=2))
    fig.add_scatter(x=part.t, y=part.crowd / 8.0, name="crowd (÷8)",
                    line=dict(color=AMBER, width=2))
    fig.add_scatter(x=part.t, y=part.flow / 12.0, name="traffic flow (÷12)",
                    line=dict(color=CYAN, width=2))
    fig.add_scatter(x=part.t, y=part.smoke, name="smoke", line=dict(color=GREY, width=2))
    imp = part.impact_t.iloc[0]
    if imp == imp:
        fig.add_vline(x=imp, line_color="white",
                      annotation_text="impact", annotation_font_color="white")
    return _layout(fig, height=330, title=title, xaxis_title="seconds",
                   yaxis_title="signal (scaled)")


def fig_lookalikes(frames, meta):
    """The five ways to be lying in a road, side by side."""
    picks = ["shoe_tie", "worker", "poster", "collision_down", "ped_fall"]
    fig = go.Figure()
    for kind, colour in zip(picks, [GREY, AMBER, VIOLET, RED, GREEN]):
        c = int(meta[meta["kind"] == kind].iloc[0].clip_id)
        part = frames[frames["clip_id"] == c]
        fig.add_scatter(x=part.t, y=part.down_secs, name=kind.replace("_", " "),
                        line=dict(color=colour, width=2.5))
    fig.add_hline(y=6, line_dash="dash", line_color="white",
                  annotation_text="a six second rule fires here",
                  annotation_font_color="white")
    return _layout(fig, height=360, xaxis_title="seconds into the clip",
                   yaxis_title="seconds lying in the road",
                   title="A timer alone cannot tell these apart")


def fig_detector_bars(rows):
    fig = go.Figure()
    names = [r["Detector"] for r in rows]
    fig.add_bar(x=names, y=[r["False alarms/hour"] for r in rows], name="false alarms per hour",
                marker_color=AMBER)
    fig.add_bar(x=names, y=[r["Incidents missed"] for r in rows], name="incidents missed",
                marker_color=RED)
    fig.add_bar(x=names, y=[r["Seconds lost"] for r in rows], name="seconds to alarm",
                marker_color=CYAN)
    return _layout(fig, height=380, barmode="group",
                   title="What each detector costs, on the exam clips")


def fig_importance(forest):
    imp = pd.Series(forest.feature_importances_, index=WINDOW_FEATURES).sort_values()
    fig = go.Figure(go.Bar(x=imp.values, y=imp.index, orientation="h", marker_color=CYAN))
    return _layout(fig, height=420, xaxis_title="how much the forest leans on this clue",
                   title="What the window model actually uses")


def fig_hazard(cost, path=None, title="The way in"):
    fig = go.Figure(go.Heatmap(z=np.log10(cost), colorscale="Inferno", showscale=False,
                               x=np.arange(cost.shape[1]) * (ROAD_X / cost.shape[1]),
                               y=np.arange(cost.shape[0]) * (ROAD_Y / cost.shape[0])))
    if path:
        px = [i * (ROAD_X / cost.shape[1]) for _, i in path]
        py = [j * (ROAD_Y / cost.shape[0]) for j, _ in path]
        fig.add_scatter(x=px, y=py, mode="lines+markers", name="safe way in",
                        line=dict(color=GREEN, width=4))
    return _layout(fig, height=340, title=title, xaxis_title="metres along the road",
                   yaxis_title="metres across")


def fig_outcome(table):
    rows = table[table["What we measure"].str.startswith("Seconds")]
    fig = go.Figure()
    fig.add_bar(x=rows["What we measure"], y=rows["No beacon"], name="no beacon",
                marker_color=GREY)
    fig.add_bar(x=rows["What we measure"], y=rows["With beacon"], name="with beacon",
                marker_color=GREEN)
    return _layout(fig, height=380, barmode="group", yaxis_title="seconds (median)",
                   title="The same crash, with and without the beacon")
