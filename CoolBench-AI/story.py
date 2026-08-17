"""The cooling bench, the heat model, the controllers, and the figures the app draws.

This is the notebook's model, trimmed to run inside a 1 GB Streamlit Cloud
container: fewer training episodes and a smaller forest. The physics, the
thresholds and the controllers are the notebook's.

Nothing here is a medical device. It is a teaching simulation, and the body
temperature in it is an educational estimate, not a clinical measurement.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

BG = "#0e1117"
CYAN = "#4fc3f7"
AMBER = "#ffb74d"
RED = "#ef5350"
GREEN = "#66bb6a"
VIOLET = "#ba68c8"
GREY = "#8b949e"
BLUE = "#5c8fdb"

# ---------------------------------------------------------------- the body
# An educational lump of warm water with a heart in it. Not a person.
BODY_MASS, CP_BODY = 75.0, 3500.0     # kg, J per kg per degree
C_BODY = BODY_MASS * CP_BODY          # joules to warm the whole body by 1 degree
A_CONV, A_SUN, A_RAD = 1.5, 0.70, 0.80    # m2 of skin: to the air, to the sun, to the ground
ALPHA, EPS, SIGMA = 0.70, 0.95, 5.67e-8   # how much sun is absorbed; emissivity; Stefan-Boltzmann
LATENT = 2.43e6                       # joules to evaporate one kg of water
F_CLO_C, F_CLO_E = 0.80, 0.60         # clothes slow the air down, and the vapour down harder
W_NAT = 0.10                          # a collapsed person often stops sweating
SKIN_GAP = 1.0                        # dry skin sits about a degree below the core
DELIVERY = 0.09                       # share of misted water that lands and stays on skin

# ---------------------------------------------------------------- the bench
TANK_L = 8.0
BATTERY_WH = 60.0                     # a small solar bench, not a car
P_ESSENTIAL = 17.0                    # radio 11 W + screen and speaker 6 W, never switched off
PRIME_ML = 40.0                       # water lost every time the pump starts from cold
PACK_LATENT, PACK_C, PACK_U, PACK_START = 45000.0, 1050.0, 2.2, 0.5
READ_NOISE = 0.05                     # the thermal camera averages a minute of frames

STOP_COOL, RESUME_COOL = 38.5, 38.9   # stop actively cooling here; start again here
WARN_TEMP = 40.0                      # the simulated warning line
WATER_FLOOR = 0.30                    # never run the pump below this
MIST_LEVELS = {"off": 0.0, "low": 80.0, "medium": 240.0, "high": 400.0}   # mL per minute
FAN_LEVELS = [0.0, 0.25, 0.50, 0.75, 1.0]
DT = 10.0                             # seconds per physics step


# ---------------------------------------------------------------- physics
def p_sat(t_c):
    """How much water vapour saturated air holds, in kPa (Tetens' formula)."""
    return 0.6108 * np.exp(17.27 * t_c / (t_c + 237.3))


def skin_drop(e_evap):
    """How much cooler wet skin runs than dry skin, on the same body."""
    return min(3.0, e_evap / 700.0)


def skin_state(T, air, fan, mist_ml):
    """Skin temperature, how wet it is, and how fast water leaves it.

    Wetting the skin cools it, and cooler skin holds less vapour, which slows
    evaporation down again. Those two chase each other, so we let them settle
    with a few passes instead of solving it properly.
    """
    v = max(air["wind"], 4.0 * fan)
    h_c = 8.3 * v ** 0.6 * F_CLO_C                 # W per m2 per degree
    h_e = 16.5 * (h_c / F_CLO_C) * F_CLO_E         # W per m2 per kPa (Lewis relation)
    p_a = air["rh"] * p_sat(air["ambient"])
    water_W = mist_ml * DELIVERY / 60.0 * 1e-3 * LATENT
    T_sk = T - SKIN_GAP
    for _ in range(6):
        e_max = h_e * A_CONV * max(0.0, p_sat(T_sk) - p_a)   # all the air can take
        w = min(1.0, W_NAT + (water_W / e_max if e_max > 1.0 else 5.0))
        e_evap = w * e_max
        T_sk = T - SKIN_GAP - skin_drop(e_evap)
    return T_sk, w, e_evap, e_max, h_c


def net_watts(T, air, act, packs, t_min):
    """The whole heat balance, in watts. Positive means the body is warming."""
    T_sk, w, e_evap, e_max, h_c = skin_state(T, air, act["fan"], act["mist"])
    q_met = (110 + 150 * np.exp(-t_min / 8.0)) * 1.07 ** (T - 37.0)
    q_solar = ALPHA * A_SUN * air["solar"] * (1 - (0.88 if act["canopy"] else 0.0))
    t_surf = air["ambient"] + (2.0 if act["canopy"] else 7.0)
    q_rad = EPS * SIGMA * A_RAD * ((t_surf + 273.15) ** 4 - (T_sk + 273.15) ** 4)
    q_conv = h_c * A_CONV * (T_sk - air["ambient"])          # negative means air heats the body
    q_pack = sum(PACK_U * max(0.0, (T - SKIN_GAP) - p["temp"]) for p in packs if p["on"])
    net = q_met + q_solar + q_rad - q_conv - e_evap - q_pack
    return net, dict(T_sk=T_sk, w=w, e_max=e_max, q_met=q_met, q_solar=q_solar, q_rad=q_rad,
                     q_conv=q_conv, q_evap=e_evap, q_pack=q_pack, t_surf=t_surf)


def p_fan(level):
    return 0.0 if level <= 0 else 3.0 + 45.0 * level ** 2.5


def p_pump(mist):
    return 0.0 if mist <= 0 else 8.0 + 0.05 * mist


# ---------------------------------------------------------------- the day
def day_profile():
    """One hot day at the sports ground, minute by minute is overkill - use 15 min."""
    h = np.arange(0, 24.01, 0.25)
    swing = np.cos((h - 15.0) / 24.0 * 2 * np.pi)      # warmest at 3 p.m., coolest at 3 a.m.
    ambient = 34.0 + 7.0 * swing
    solar = np.clip(980.0 * np.sin(np.pi * (h - 6.0) / 13.0), 0, None)
    rh = np.clip(0.80 - 0.52 * (ambient - ambient.min()) / (ambient.max() - ambient.min()),
                 0.15, 0.95)
    wind = 0.5 + 1.4 * np.clip(np.sin(np.pi * (h - 8.0) / 14.0), 0, None)
    surface = ambient + 9.0 * solar / 980.0
    cap, danger = [], []
    for a, r, s, wnd in zip(ambient, rh, solar, wind):
        air = dict(ambient=float(a), rh=float(r), solar=float(s), wind=float(wnd))
        cap.append(skin_state(39.5, air, 0.75, MIST_LEVELS["medium"])[3])
        # what an untreated person lying on the ground would be gaining, in watts
        danger.append(net_watts(39.5, air, dict(canopy=0, fan=0.0, mist=0.0), [], 0.0)[0])
    return pd.DataFrame(dict(hour=h, ambient=ambient, solar=solar, rh=rh, wind=wind,
                             surface=surface, air_can_take=cap, untreated_w=danger))


# ---------------------------------------------------------------- scenarios
def make_scenario(**kw):
    """One emergency, with everything that can differ between them."""
    s = dict(name="a hot afternoon", ambient=41.0, rh=0.32, solar=880.0, wind=0.6,
             start_temp=39.8, eta=14.0, water_l=8.0, battery_pct=61.0, packs=3,
             pump_fail_at=None, fan_fail_at=None, comms_fail_at=None,
             humidity_jump_at=None, humidity_jump_to=0.80,
             eta_extends_at=None, eta_new=25.0, leaves_at=None, minutes=None)
    s.update(kw)
    if s["minutes"] is None:
        s["minutes"] = int(round(max(s["eta"],
                                     s["eta_new"] if s["eta_extends_at"] is not None else 0.0)))
    return s


def air_at(sc, t_min):
    rh = sc["rh"]
    if sc["humidity_jump_at"] is not None and t_min >= sc["humidity_jump_at"]:
        rh = sc["humidity_jump_to"]
    return dict(ambient=sc["ambient"], rh=rh, solar=sc["solar"], wind=sc["wind"])


# ---------------------------------------------------------------- safety layer
def apply_limits(act, obs, air):
    """The deterministic limits that sit under the AI. Returns what is allowed."""
    a = dict(act)
    a["stop_packs"] = False
    stopped = []
    if not obs["occupied"]:
        if a["mist"] or a["fan"] or a["release_pack"] or obs["packs_active"]:
            stopped.append("nobody is on the bench")
        a["fan"], a["mist"], a["release_pack"], a["stop_packs"] = 0.0, 0.0, False, True
        return a, stopped
    if obs["cooling_locked"]:
        if a["mist"] > 0 or a["release_pack"] or obs["packs_active"]:
            stopped.append("cool enough - active cooling stopped")
        a["mist"], a["release_pack"], a["stop_packs"] = 0.0, False, True
        a["fan"] = min(a["fan"], 0.25)
    if not obs["pump_ok"] and a["mist"] > 0:
        stopped.append("the pump has failed")
        a["mist"] = 0.0
    if obs["water_l"] <= WATER_FLOOR and a["mist"] > 0:
        stopped.append("tank empty - the pump is protected")
        a["mist"] = 0.0
    if not obs["fan_ok"] and a["fan"] > 0:
        stopped.append("the fan has failed")
        a["fan"] = 0.0
    if obs["battery_wh"] <= obs["reserve_wh"] and (a["fan"] > 0 or a["mist"] > 0):
        stopped.append("battery is down to the radio reserve")
        a["fan"], a["mist"] = 0.0, 0.0
    if a["fan"] > 0:
        # Moving air only cools skin that is wet. On dry skin, in air hotter than
        # the skin, a fan is a heater. This limit is pure physics, and it is the
        # reason the notebook never says "more airflow is always better".
        blow, _ = net_watts(obs["body_est"], air,
                            dict(canopy=a["canopy"], fan=a["fan"], mist=a["mist"]), [], obs["t"])
        still, _ = net_watts(obs["body_est"], air,
                             dict(canopy=a["canopy"], fan=0.0, mist=a["mist"]), [], obs["t"])
        if blow > still + 1.0:
            stopped.append("the fan would add more heat than it removes")
            a["fan"] = 0.0
    return a, stopped


# ---------------------------------------------------------------- the run
def run(controller, sc, seed=0, safety=True, model=None):
    """Play one emergency out, minute by minute."""
    rng = np.random.default_rng(seed)
    T = sc["start_temp"]
    water, batt = sc["water_l"], BATTERY_WH * sc["battery_pct"] / 100.0
    packs = [dict(on=False, absorbed=0.0, temp=PACK_START, used=False) for _ in range(sc["packs"])]
    act = dict(canopy=0, fan=0.0, mist=0.0, release_pack=False)
    canopy, pump_on, prev_read, locked, blocked, reasons = 0, False, None, False, 0, []
    eta = sc["eta"]
    rows = []
    for minute in range(sc["minutes"] + 1):
        air = air_at(sc, minute)
        if sc["eta_extends_at"] is not None and minute >= sc["eta_extends_at"]:
            eta = sc["eta_new"]
        eta_left = max(0.0, eta - minute)
        occupied = not (sc["leaves_at"] is not None and minute >= sc["leaves_at"])
        pump_ok = not (sc["pump_fail_at"] is not None and minute >= sc["pump_fail_at"])
        fan_ok = not (sc["fan_fail_at"] is not None and minute >= sc["fan_fail_at"])
        comms_ok = not (sc["comms_fail_at"] is not None and minute >= sc["comms_fail_at"])

        # What the thermal camera sees is the skin as it is right now - wet and
        # cool if we have been misting it. It is not the core temperature.
        _, _, e_evap_now, _, _ = skin_state(T, air, act["fan"], act["mist"])
        read = T - SKIN_GAP - skin_drop(e_evap_now) + rng.normal(0, READ_NOISE)
        body_est = read + SKIN_GAP + skin_drop(e_evap_now)   # add our own cooling back
        naive_est = read + SKIN_GAP                          # what a bench that forgot would say
        slope = 0.0 if prev_read is None else read - prev_read
        prev_read = read

        if body_est <= STOP_COOL:
            locked = True
        elif body_est > RESUME_COOL:
            locked = False

        obs = dict(thermal=read, slope=slope, body_est=body_est, naive_est=naive_est,
                   ambient=air["ambient"] + rng.normal(0, 0.4),
                   rh=float(np.clip(air["rh"] + rng.normal(0, 0.02), 0.02, 1.0)),
                   solar=air["solar"], wind=air["wind"], water_l=water, battery_wh=batt,
                   battery_pct=100 * batt / BATTERY_WH,
                   packs_left=sum(1 for p in packs if not p["used"]),
                   packs_active=sum(1 for p in packs if p["on"]),
                   eta_left=eta_left, t=minute, pump_ok=pump_ok, fan_ok=fan_ok,
                   comms_ok=comms_ok, occupied=occupied, cooling_locked=locked,
                   reserve_wh=P_ESSENTIAL * (eta_left + 20.0) / 60.0)

        asked = controller(obs, model)
        asked.setdefault("release_pack", False)
        if safety:
            act, stopped = apply_limits(asked, obs, air)
        else:
            act, stopped = dict(asked), []
            act["stop_packs"] = False
        blocked += len(stopped)
        reasons.extend(stopped)

        if act["stop_packs"]:
            for p in packs:
                p["on"] = False
        if act["release_pack"]:
            for p in packs:
                if not p["used"]:
                    p["used"], p["on"] = True, True
                    break
        for p in packs:                      # a pack warmer than this is taken off
            if p["on"] and p["temp"] > 25.0:
                p["on"] = False

        if act["canopy"] and not canopy:
            batt -= 0.15
        canopy = act["canopy"]

        watts, parts = net_watts(T, air, act, packs, minute)
        rows.append(dict(minute=minute, body=T, thermal=read, naive_est=naive_est,
                         body_est=body_est, slope=slope, ambient=air["ambient"], rh=air["rh"],
                         solar=air["solar"], wind=air["wind"], canopy=canopy, fan=act["fan"],
                         mist=act["mist"], packs_active=sum(1 for p in packs if p["on"]),
                         packs_left=sum(1 for p in packs if not p["used"]), water_l=water,
                         battery_pct=100 * batt / BATTERY_WH, battery_wh=batt,
                         eta_left=eta_left, net_w=watts, blocked=len(stopped),
                         reserve_wh=obs["reserve_wh"], occupied=int(occupied),
                         power_w=p_fan(act["fan"]) + p_pump(act["mist"]) + P_ESSENTIAL, **parts))
        if minute == sc["minutes"]:
            break

        if act["mist"] > 0 and not pump_on:
            water = max(0.0, water - PRIME_ML / 1000.0)     # priming the line costs water
        pump_on = act["mist"] > 0
        for _ in range(int(60 / DT)):
            watts, _ = net_watts(T, air, act, packs, minute)
            T += watts * DT / C_BODY
            for p in packs:
                if p["on"]:
                    q = PACK_U * max(0.0, (T - SKIN_GAP) - p["temp"])
                    p["absorbed"] += q * DT
                    p["temp"] = (PACK_START if p["absorbed"] < PACK_LATENT
                                 else PACK_START + (p["absorbed"] - PACK_LATENT) / PACK_C)
            water = max(0.0, water - act["mist"] * DT / 60.0 / 1000.0)
            if water <= 0.0:
                act["mist"] = 0.0
            batt -= (p_fan(act["fan"]) + p_pump(act["mist"]) + P_ESSENTIAL) * DT / 3600.0
            if batt <= 0.0:
                batt, act["fan"], act["mist"] = 0.0, 0.0, 0.0
    out = pd.DataFrame(rows)
    out.attrs["blocked"] = blocked
    out.attrs["reasons"] = reasons
    return out


def score(df, sc):
    """Everything we are allowed to claim about one run."""
    left_wh = float(df["battery_wh"].iloc[-1])
    return dict(
        change=round(float(df["body"].iloc[-1] - df["body"].iloc[0]), 2),
        peak=round(float(df["body"].max()), 2),
        lowest=round(float(df["body"].min()), 2),
        burden=round(float(np.maximum(0.0, df["body"] - STOP_COOL).sum()), 1),
        over_warn=int((df["body"] > WARN_TEMP).sum()),
        water=round(float(sc["water_l"] - df["water_l"].iloc[-1]), 2),
        battery_left=round(float(df["battery_pct"].iloc[-1]), 1),
        packs=int(sc["packs"] - df["packs_left"].iloc[-1]),
        radio_min=int(left_wh / P_ESSENTIAL * 60),
        blocked=int(df.attrs.get("blocked", 0)))


# ---------------------------------------------------------------- controllers
def c_none(obs, model=None):
    return dict(canopy=0, fan=0.0, mist=0.0, release_pack=False)


def c_shade(obs, model=None):
    return dict(canopy=1, fan=0.0, mist=0.0, release_pack=False)


def c_fan(obs, model=None):
    return dict(canopy=1, fan=1.0, mist=0.0, release_pack=False)


def c_mist(obs, model=None):
    return dict(canopy=1, fan=0.0, mist=MIST_LEVELS["high"], release_pack=False)


def c_max(obs, model=None):
    return dict(canopy=1, fan=1.0, mist=MIST_LEVELS["high"], release_pack=obs["packs_left"] > 0)


def c_rules(obs, model=None):
    """Thresholds a person can read, argue with, and sign off."""
    a = dict(canopy=1 if obs["solar"] > 200 else 0, fan=0.0, mist=0.0, release_pack=False)
    if obs["cooling_locked"]:
        return a
    free_wh = obs["battery_wh"] - obs["reserve_wh"]
    budget = max(0.0, (obs["water_l"] - 0.5) * 1000.0) / max(1.0, obs["eta_left"])
    air = dict(ambient=obs["ambient"], rh=obs["rh"], solar=obs["solar"], wind=obs["wind"])
    e_max = skin_state(obs["body_est"], air, 0.75, MIST_LEVELS["medium"])[3]
    if obs["pump_ok"] and free_wh > 2.0 and e_max > 150.0:
        for name in ("medium", "low"):
            if MIST_LEVELS[name] <= budget:
                a["mist"] = MIST_LEVELS[name]
                break
    if a["mist"] > 0 and obs["fan_ok"] and free_wh > 3.0:
        a["fan"] = 0.75
    if obs["packs_left"] > 0 and obs["packs_active"] == 0 and obs["body_est"] > 39.0:
        a["release_pack"] = True
    return a


CONTROLLERS = {
    "no cooling": (c_none, False),
    "shade only": (c_shade, False),
    "fan only": (c_fan, False),
    "mist only": (c_mist, False),
    "maximum fixed": (c_max, False),
    "rule based": (c_rules, True),
}


# ---------------------------------------------------------------- learning
FEATURES = ["body_est", "slope", "ambient", "rh", "solar", "wind",
            "fan", "mist", "packs_active", "canopy"]
W_BURDEN, W_WATER, W_ENERGY, W_RISK, W_UNSAFE = 1.0, 0.45, 0.06, 0.30, 5.0
HORIZON = 5

CANDIDATES = [dict(canopy=1, fan=f, mist=m, release_pack=bool(p))
              for f in (0.0, 0.5, 0.75, 1.0)
              for m in MIST_LEVELS.values()
              for p in (0, 1)]


def random_scenarios(n, seed=1):
    rng = np.random.default_rng(seed)
    return [make_scenario(
        ambient=float(rng.uniform(33, 45)), rh=float(rng.uniform(0.15, 0.85)),
        solar=float(rng.uniform(250, 980)), wind=float(rng.uniform(0.2, 2.5)),
        start_temp=float(rng.uniform(38.6, 41.0)), eta=float(rng.uniform(8, 26)),
        water_l=float(rng.uniform(1.5, 8.0)), battery_pct=float(rng.uniform(25, 100)),
        packs=int(rng.integers(0, 4))) for _ in range(n)]


def build_dataset(n_episodes=250, seed=1):
    """Settings picked at random, so the model sees bad choices as well as good ones."""
    rows = []
    for i, sc in enumerate(random_scenarios(n_episodes, seed)):
        rng = np.random.default_rng(1000 + i)

        def ctrl(obs, model=None, rng=rng):
            return dict(canopy=int(rng.random() < 0.75), fan=float(rng.choice(FAN_LEVELS)),
                        mist=float(rng.choice(list(MIST_LEVELS.values()))),
                        release_pack=bool(rng.random() < 0.12))
        df = run(ctrl, sc, seed=i, safety=False).copy()
        df["episode"] = i
        df["next_body"] = df["body_est"].shift(-1)
        df["delta"] = df["next_body"] - df["body_est"]
        rows.append(df.dropna(subset=["next_body"]))
    return pd.concat(rows, ignore_index=True)


def fit_models(train, seed=7, trees=60):
    from sklearn.linear_model import LinearRegression
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.neural_network import MLPRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    X = train[FEATURES].to_numpy(np.float32)
    y = train["delta"].to_numpy(np.float32)
    models = {
        "linear regression": make_pipeline(StandardScaler(), LinearRegression()),
        "random forest": RandomForestRegressor(n_estimators=trees, min_samples_leaf=8,
                                               random_state=seed, n_jobs=1),
        "small neural net": make_pipeline(
            StandardScaler(), MLPRegressor(hidden_layer_sizes=(48, 32), max_iter=900,
                                           random_state=seed, early_stopping=True)),
    }
    for m in models.values():
        m.fit(X, y)
    return models


def make_ai(resource_aware=True, horizon=HORIZON):
    """Try every setting, roll the forecast forward five minutes, keep the cheapest."""
    n = len(CANDIDATES)
    fan = np.array([c["fan"] for c in CANDIDATES], np.float32)
    mist = np.array([c["mist"] for c in CANDIDATES], np.float32)
    rel = np.array([c["release_pack"] for c in CANDIDATES], np.float32)
    power = np.array([p_fan(f) + p_pump(m) + P_ESSENTIAL for f, m in zip(fan, mist)], np.float32)

    def controller(obs, model=None):
        if obs["cooling_locked"]:
            return dict(canopy=1 if obs["solar"] > 200 else 0, fan=0.0, mist=0.0,
                        release_pack=False)
        X = np.zeros((n, len(FEATURES)), np.float32)
        X[:, 1] = obs["slope"]
        X[:, 2], X[:, 3] = obs["ambient"], obs["rh"]
        X[:, 4], X[:, 5] = obs["solar"], obs["wind"]
        X[:, 6], X[:, 7] = fan, mist
        X[:, 8] = obs["packs_active"] + rel * (obs["packs_left"] > 0)
        X[:, 9] = 1.0
        T = np.full(n, obs["body_est"], np.float32)
        burden = np.zeros(n, np.float32)
        for _ in range(horizon):
            X[:, 0] = T
            d = model.predict(X).astype(np.float32)
            X[:, 1] = d
            T = T + d
            # squared, because being two degrees too hot is far worse than twice
            # being one degree too hot
            burden += np.maximum(0.0, T - STOP_COOL) ** 2
        j = W_BURDEN * burden
        if resource_aware:
            litres = mist * horizon / 1000.0
            wh = power * horizon / 60.0
            water_min = np.where(mist > 0, (obs["water_l"] - 0.3) * 1000.0
                                 / np.maximum(mist, 1e-9), np.inf)
            batt_min = (obs["battery_wh"] - obs["reserve_wh"]) * 60.0 / power
            shortfall = np.maximum(0.0, obs["eta_left"] - np.minimum(water_min, batt_min))
            air = dict(ambient=obs["ambient"], rh=obs["rh"], solar=obs["solar"],
                       wind=obs["wind"])
            nblock = np.array([len(apply_limits(dict(c), obs, air)[1]) for c in CANDIDATES],
                              np.float32)
            j = j + W_WATER * litres + W_ENERGY * wh + W_RISK * shortfall + W_UNSAFE * nblock
        j = np.where((rel == 0) | (obs["packs_left"] > 0), j, np.inf)
        return dict(CANDIDATES[int(np.argmin(j))])
    return controller


def model_scores(models, test):
    from sklearn.metrics import r2_score, mean_absolute_error
    X = test[FEATURES].to_numpy(np.float32)
    y = test["delta"].to_numpy(np.float32)
    rows = []
    for name, m in models.items():
        p = m.predict(X)
        rows.append({"Model": name, "R² on the change": round(r2_score(y, p), 3),
                     "Average error °C": round(mean_absolute_error(y, p), 4),
                     "R² on the level": round(r2_score(test["next_body"],
                                                       test["body_est"] + p), 4)})
    rows.append({"Model": "assume nothing changes", "R² on the change": round(r2_score(y, y * 0), 3),
                 "Average error °C": round(mean_absolute_error(y, y * 0), 4),
                 "R² on the level": round(r2_score(test["next_body"], test["body_est"]), 4)})
    return pd.DataFrame(rows)


def rollout_error(models, test, steps=5):
    """How far out is the forecast five minutes later, when errors pile up?"""
    seqs, truth = [], []
    for _, g in test.groupby("episode"):
        g = g.reset_index(drop=True)
        for i in range(len(g) - steps):
            seqs.append(g.loc[i:i + steps - 1, FEATURES].to_numpy(np.float32))
            truth.append(float(g["body_est"][i + steps]))
    if not seqs:
        return pd.DataFrame()
    seqs, truth = np.stack(seqs), np.array(truth)
    rows = []
    for name, m in models.items():
        T, slope = seqs[:, 0, 0].copy(), seqs[:, 0, 1].copy()
        for k in range(steps):
            X = seqs[:, k, :].copy()
            X[:, 0], X[:, 1] = T, slope
            d = m.predict(X).astype(np.float32)
            T, slope = T + d, d
        rows.append({"Model": name, "Error 5 minutes out °C": round(float(np.mean(np.abs(
            T - truth))), 3)})
    rows.append({"Model": "assume nothing changes",
                 "Error 5 minutes out °C": round(float(np.mean(np.abs(seqs[:, 0, 0] - truth))), 3)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- little tables
def water_curve(air, fan=0.75, T=39.8):
    """Cooling bought per litre of water, at each mist rate."""
    base = net_watts(T, air, dict(canopy=1, fan=fan, mist=0.0), [], 0.0)[0]
    rows = []
    for m in [0, 40, 80, 120, 160, 200, 240, 300, 400, 500]:
        net, parts = net_watts(T, air, dict(canopy=1, fan=fan, mist=float(m)), [], 0.0)
        lph = m * 60 / 1000.0
        extra = (base - net) / C_BODY * 60.0        # extra degrees per minute removed
        rows.append({"mist mL/min": m, "skin wetness": round(parts["w"], 2),
                     "evaporation W": round(parts["q_evap"]),
                     "°C per minute": round(net / C_BODY * 60, 3),
                     "litres per hour": round(lph, 1),
                     "°C per litre": round(extra / lph * 60, 2) if lph else 0.0})
    return pd.DataFrame(rows)


def fan_map(mist=0.0, T=39.8, wind=0.6):
    """Where does moving air help, and where is it a heater?"""
    temps = np.arange(32, 46.1, 0.5)
    hums = np.arange(0.10, 0.91, 0.025)
    z = np.zeros((len(hums), len(temps)))
    for i, r in enumerate(hums):
        for j, a in enumerate(temps):
            air = dict(ambient=float(a), rh=float(r), solar=880.0, wind=wind)
            off = net_watts(T, air, dict(canopy=1, fan=0.0, mist=mist), [], 0.0)[0]
            on = net_watts(T, air, dict(canopy=1, fan=1.0, mist=mist), [], 0.0)[0]
            z[i, j] = off - on                       # positive = the fan helps
    return temps, hums, z


def heat_terms(T, air, act):
    _, parts = net_watts(T, air, act, [], 0.0)
    return parts


# ---------------------------------------------------------------- figures
def _layout(fig, height=400, **kw):
    fig.update_layout(height=height, paper_bgcolor=BG, plot_bgcolor=BG, font_color="white",
                      margin=dict(l=55, r=25, t=50, b=45),
                      legend=dict(bgcolor="rgba(0,0,0,0)"), **kw)
    fig.update_xaxes(gridcolor="#21262d")
    fig.update_yaxes(gridcolor="#21262d")
    return fig


def fig_day(d=None):
    d = day_profile() if d is None else d
    fig = go.Figure()
    fig.add_scatter(x=d.hour, y=d.surface, name="bench surface °C", line=dict(color=RED, width=2.5))
    fig.add_scatter(x=d.hour, y=d.ambient, name="air °C", line=dict(color=AMBER, width=2.5))
    fig.add_scatter(x=d.hour, y=d.rh * 100, name="humidity %", line=dict(color=CYAN, width=2))
    fig.add_scatter(x=d.hour, y=d.solar / 20, name="sunshine (W/m² ÷ 20)",
                    line=dict(color=VIOLET, width=2, dash="dot"))
    fig.add_vrect(x0=13, x1=17, fillcolor=RED, opacity=0.10, line_width=0,
                  annotation_text="the dangerous hours", annotation_font_color="white")
    return _layout(fig, xaxis_title="hour of the day", yaxis_title="°C, %, scaled sun",
                   title="One hot day at the sports ground")


def fig_air_capacity(d=None):
    """The danger is not the thermometer. It is the sun and the ground under it."""
    d = day_profile() if d is None else d
    fig = go.Figure()
    fig.add_scatter(x=d.hour, y=d.untreated_w, name="heat piling into an untreated person",
                    line=dict(color=RED, width=3), fill="tozeroy",
                    fillcolor="rgba(239,83,80,0.15)")
    fig.add_scatter(x=d.hour, y=(d.ambient - 27) / 14 * 800, name="air temperature (scaled)",
                    line=dict(color=AMBER, width=2, dash="dash"))
    fig.add_hline(y=0, line_color=GREY)
    return _layout(fig, xaxis_title="hour of the day", yaxis_title="watts",
                   title="The danger peaks with the sun, not with the thermometer")


def fig_same_temperature():
    """Same thermometer reading, very different afternoon."""
    rows = []
    for rh in (0.20, 0.32, 0.50, 0.65, 0.78, 0.90):
        air = dict(ambient=41.0, rh=rh, solar=880.0, wind=0.6)
        rows.append((rh * 100, skin_state(39.8, air, 0.75, MIST_LEVELS["medium"])[3]))
    fig = go.Figure(go.Bar(x=[f"{int(r)}%" for r, _ in rows], y=[c for _, c in rows],
                           marker_color=[GREEN if c > 600 else AMBER if c > 300 else RED
                                         for _, c in rows]))
    return _layout(fig, height=350, xaxis_title="humidity, at 41 °C every time",
                   yaxis_title="watts the air can carry away",
                   title="41 °C is not one weather. It is six.")


def fig_balance(T=39.8, air=None, act=None):
    air = air or dict(ambient=41.0, rh=0.32, solar=880.0, wind=0.6)
    act = act or dict(canopy=0, fan=0.0, mist=0.0)
    p = heat_terms(T, air, act)
    names = ["body's own heat", "sunshine", "hot ground", "air", "evaporation", "cold packs"]
    vals = [p["q_met"], p["q_solar"], p["q_rad"], -p["q_conv"], -p["q_evap"], -p["q_pack"]]
    fig = go.Figure(go.Bar(x=names, y=vals,
                           marker_color=[RED if v > 0 else CYAN for v in vals],
                           text=[f"{v:+.0f} W" for v in vals], textposition="outside"))
    fig.add_hline(y=0, line_color=GREY)
    return _layout(fig, height=380, yaxis_title="watts (above zero warms the body)",
                   title=f"Where the heat comes from · net {sum(vals):+.0f} W")


def fig_water_curve(air=None):
    air = air or dict(ambient=41.0, rh=0.32, solar=880.0, wind=0.6)
    d = water_curve(air)
    fig = go.Figure()
    fig.add_bar(x=d["mist mL/min"], y=d["°C per litre"], name="°C of cooling per litre",
                marker_color=CYAN)
    fig.add_scatter(x=d["mist mL/min"], y=-d["°C per minute"] * 10, name="cooling rate (×10)",
                    line=dict(color=AMBER, width=3), yaxis="y")
    return _layout(fig, height=380, xaxis_title="mist rate, mL per minute",
                   yaxis_title="°C per litre  ·  cooling rate ×10",
                   title="More water stops buying more cooling")


def fig_fan_map(mist=0.0):
    temps, hums, z = fan_map(mist)
    fig = go.Figure(go.Heatmap(z=z, x=temps, y=hums * 100, colorscale="RdBu", zmid=0,
                               colorbar=dict(title="watts")))
    return _layout(fig, height=400, xaxis_title="air temperature °C", yaxis_title="humidity %",
                   title=("Blue: the fan removes heat.  Red: the fan is a heater."
                          + ("  (skin wet)" if mist else "  (skin dry)")))


def fig_runs(runs, title="Simulated body temperature"):
    """runs: dict of name -> dataframe."""
    colours = [GREY, VIOLET, BLUE, CYAN, RED, AMBER, GREEN, "#f06292", "#4db6ac"]
    fig = go.Figure()
    for (name, df), c in zip(runs.items(), colours):
        fig.add_scatter(x=df.minute, y=df.body, name=name, line=dict(color=c, width=2.5))
    fig.add_hline(y=WARN_TEMP, line_dash="dash", line_color=RED,
                  annotation_text="simulated warning line", annotation_font_color="white")
    fig.add_hline(y=STOP_COOL, line_dash="dot", line_color=GREEN,
                  annotation_text="stop cooling here", annotation_font_color="white")
    return _layout(fig, xaxis_title="minutes since the bench was switched on",
                   yaxis_title="simulated body temperature °C", title=title)


def fig_resources(runs):
    fig = go.Figure()
    colours = [AMBER, CYAN, GREEN, VIOLET, RED, GREY]
    for (name, df), c in zip(runs.items(), colours):
        fig.add_scatter(x=df.minute, y=df.water_l, name=f"{name} · water",
                        line=dict(color=c, width=2.5))
        fig.add_scatter(x=df.minute, y=df.battery_pct / 12.5, name=f"{name} · battery ÷12.5",
                        line=dict(color=c, width=2, dash="dot"))
    return _layout(fig, xaxis_title="minutes", yaxis_title="litres  ·  battery % ÷ 12.5",
                   title="What each strategy spends")


def fig_camera_gap(df):
    fig = go.Figure()
    fig.add_scatter(x=df.minute, y=df.body, name="true simulated body temperature",
                    line=dict(color=RED, width=3))
    fig.add_scatter(x=df.minute, y=df.thermal, name="what the thermal camera reads",
                    line=dict(color=CYAN, width=2))
    fig.add_scatter(x=df.minute, y=df.naive_est, name="camera reading + 1 °C (wrong)",
                    line=dict(color=GREY, width=2, dash="dash"))
    fig.add_scatter(x=df.minute, y=df.body_est, name="corrected estimate the bench uses",
                    line=dict(color=GREEN, width=2, dash="dot"))
    fig.add_hline(y=STOP_COOL, line_dash="dot", line_color=AMBER,
                  annotation_text="stop cooling here", annotation_font_color="white")
    return _layout(fig, xaxis_title="minutes", yaxis_title="°C",
                   title="The camera sees wet skin, not the inside of a person")


def fig_packs(minutes=25):
    """One cold pack, opened at minute zero."""
    pack = dict(on=True, absorbed=0.0, temp=PACK_START)
    t, power, temp = [], [], []
    for step in range(minutes * 6):
        q = PACK_U * max(0.0, 38.8 - pack["temp"])
        pack["absorbed"] += q * DT
        pack["temp"] = (PACK_START if pack["absorbed"] < PACK_LATENT
                        else PACK_START + (pack["absorbed"] - PACK_LATENT) / PACK_C)
        t.append(step * DT / 60.0)
        power.append(q)
        temp.append(pack["temp"])
    fig = go.Figure()
    fig.add_scatter(x=t, y=power, name="cooling from the pack, W", line=dict(color=CYAN, width=3))
    fig.add_scatter(x=t, y=temp, name="pack temperature °C", line=dict(color=AMBER, width=2))
    fig.add_vline(x=PACK_LATENT / (PACK_U * 38.3) / 60.0, line_dash="dash", line_color=GREEN,
                  annotation_text="the ice has melted", annotation_font_color="white")
    return _layout(fig, height=350, xaxis_title="minutes after the pack is opened",
                   yaxis_title="watts  ·  °C", title="A cold pack is not a battery you can refill")


def fig_models(table, column="R² on the change"):
    d = table.sort_values(column)
    fig = go.Figure(go.Bar(x=d[column], y=d["Model"], orientation="h",
                           marker_color=[GREY if "nothing" in m else CYAN for m in d["Model"]],
                           text=[f"{v:.3f}" for v in d[column]], textposition="outside"))
    return _layout(fig, height=330, xaxis_title=column,
                   title="Judged on the change, not on the level")


def fig_board(board):
    fig = go.Figure()
    fig.add_bar(x=board["Controller"], y=board["Water used L"], name="water, litres",
                marker_color=CYAN, yaxis="y")
    fig.add_bar(x=board["Controller"], y=board["Battery left %"] / 10, name="battery left % ÷10",
                marker_color=GREEN)
    fig.add_scatter(x=board["Controller"], y=board["Change °C"], name="temperature change °C",
                    line=dict(color=AMBER, width=3), mode="lines+markers")
    return _layout(fig, height=420, barmode="group",
                   title="What each strategy achieved, and what it cost")


def fig_j_terms(df):
    fig = go.Figure()
    fig.add_scatter(x=df.minute, y=np.maximum(0, df.body - STOP_COOL), name="how far above 38.5 °C",
                    line=dict(color=RED, width=3))
    fig.add_scatter(x=df.minute, y=df.mist / 100, name="mist ÷100 mL/min",
                    line=dict(color=CYAN, width=2))
    fig.add_scatter(x=df.minute, y=df.fan * 2, name="fan ×2", line=dict(color=AMBER, width=2))
    fig.add_scatter(x=df.minute, y=df.packs_active, name="packs on the person",
                    line=dict(color=VIOLET, width=2, dash="dot"))
    return _layout(fig, height=380, xaxis_title="minutes", yaxis_title="scaled",
                   title="What the controller chose, minute by minute")


def fig_thermal(scene="hot"):
    """A pretend thermal picture of the bench, the person and the ground."""
    nx, ny = 64, 40
    x = np.linspace(0, 3.2, nx)
    y = np.linspace(0, 2.0, ny)
    X, Y = np.meshgrid(x, y)
    ground = 48.0 - 2.0 * Y
    mask = np.exp(-(((X - 1.6) / 0.75) ** 8 + ((Y - 1.0) / 0.28) ** 8))
    z = ground * (1 - mask) + (36.5 if scene == "cool" else 39.0) * mask
    if scene == "cool":
        z -= 6.0 * np.exp(-(((X - 1.6) / 1.4) ** 4 + ((Y - 1.0) / 0.6) ** 4))
    fig = go.Figure(go.Heatmap(z=z, x=x, y=y, colorscale="Inferno",
                               colorbar=dict(title="°C"), zmin=30, zmax=52))
    return _layout(fig, height=300, xaxis_title="metres", yaxis_title="metres",
                   title=("Under the canopy, misting" if scene == "cool"
                          else "Full sun, before the bench does anything"))
