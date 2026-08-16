"""The cabinet, the emergencies, the models and the figures the app draws.

A port of the notebook's code, with the same seeds and the same thresholds, so
at the app's default settings every number matches the notebook.

The boundary that does not move: nothing here decides what treatment anybody
needs. It chooses which supplies to hand over, from a list an approved protocol
allows, and the fixed safety checks always get the last word.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.multioutput import MultiOutputClassifier

BG = "#0e1117"
CYAN = "#4fc3f7"
AMBER = "#ffb74d"
RED = "#ef5350"
GREEN = "#66bb6a"
VIOLET = "#ba68c8"
GREY = "#8b949e"

COMPARTMENTS = ["protective", "bleeding", "burns", "aed", "traffic", "flotation", "comms"]
NAMES = {
    "protective": "Protective equipment",
    "bleeding": "Bleeding supplies",
    "burns": "Burn supplies",
    "aed": "AED",
    "traffic": "Traffic safety",
    "flotation": "Flotation",
    "comms": "Communication unit",
}
ALWAYS_OPEN = ["protective", "comms"]
MODELLED = [c for c in COMPARTMENTS if c not in ALWAYS_OPEN]
INCIDENTS = ["road_accident", "fall", "fire", "water", "cardiac", "unclear"]

UNLOCKED, LOCKED, WAITING, UNAVAILABLE, ELSEWHERE = (
    "unlocked", "locked", "waiting", "unavailable", "elsewhere")
STATE_COLOUR = {UNLOCKED: GREEN, LOCKED: RED, WAITING: AMBER,
                UNAVAILABLE: GREY, ELSEWHERE: CYAN}
STATE_WORD = {UNLOCKED: "OPEN", LOCKED: "locked", WAITING: "WAITING",
              UNAVAILABLE: "empty", ELSEWHERE: "NEXT CABINET"}

LOW_BATTERY = 25
W_MISSING, W_DELAY, W_SHORTAGE, W_UNSAFE = 10.0, 0.15, 3.0, 100.0
COST_IF_UNNEEDED = {"protective": 0.2, "comms": 0.2, "traffic": 0.8,
                    "bleeding": 1.0, "burns": 1.0, "flotation": 1.5, "aed": 6.0}

AED_NOTE = ("The AED is the only restricted item. It never opens without a dispatcher, and "
            "nothing in this app decides whether a shock should be given - that belongs to the "
            "AED itself.")


# --------------------------------------------------------------- the cabinet
def fresh_cabinet(seed=7, fill=1.0):
    rng = np.random.default_rng(seed)

    def stock(full):
        # No floor of 1 here on purpose: a low fill has to be able to empty a
        # small compartment, or the "nothing usable in there" states can never
        # actually happen. Above fill=0.3 this rounds identically to a floored
        # version, so the notebook's day numbers are unaffected.
        return int(round(full * fill))

    return {
        "protective": dict(quantity=stock(24), sealed=True,
                           days_to_expiry=int(rng.integers(300, 900)),
                           battery=None, consumable=True, restricted=False),
        "bleeding": dict(quantity=stock(10), sealed=True,
                         days_to_expiry=int(rng.integers(200, 800)),
                         battery=None, consumable=True, restricted=False),
        "burns": dict(quantity=stock(6), sealed=True,
                      days_to_expiry=int(rng.integers(-30, 700)),
                      battery=None, consumable=True, restricted=False),
        "aed": dict(quantity=1, sealed=True, days_to_expiry=int(rng.integers(200, 600)),
                    battery=int(rng.integers(35, 100)), consumable=False, restricted=True),
        "traffic": dict(quantity=stock(4), sealed=True, days_to_expiry=9999,
                        battery=None, consumable=False, restricted=False),
        "flotation": dict(quantity=stock(2), sealed=True, days_to_expiry=9999,
                          battery=None, consumable=False, restricted=False),
        "comms": dict(quantity=1, sealed=True, days_to_expiry=9999,
                      battery=int(rng.integers(60, 100)), consumable=False, restricted=False),
    }


def usable(item):
    return item["quantity"] > 0 and item["sealed"] and item["days_to_expiry"] > 0


# --------------------------------------------------------------- emergencies
def make_truth(rng):
    incident = INCIDENTS[rng.integers(0, len(INCIDENTS))]
    truth = dict(incident=incident, bleeding=0, unresponsive=0, fire=0, water=0,
                 traffic=0, people=1)
    if incident == "road_accident":
        truth["bleeding"] = int(rng.random() < 0.75)
        truth["traffic"] = 1
        truth["unresponsive"] = int(rng.random() < 0.15)
    elif incident == "fall":
        truth["bleeding"] = int(rng.random() < 0.55)
        truth["traffic"] = int(rng.random() < 0.30)
    elif incident == "fire":
        truth["fire"] = 1
        truth["bleeding"] = int(rng.random() < 0.20)
    elif incident == "water":
        truth["water"] = 1
        truth["unresponsive"] = int(rng.random() < 0.40)
    elif incident == "cardiac":
        truth["unresponsive"] = 1
    else:
        truth["bleeding"] = int(rng.random() < 0.35)
        truth["unresponsive"] = int(rng.random() < 0.20)
        truth["fire"] = int(rng.random() < 0.10)
        truth["water"] = int(rng.random() < 0.10)
        truth["traffic"] = int(rng.random() < 0.30)
    truth["people"] = 1 + int(rng.random() < 0.20) + int(rng.random() < 0.06)
    return truth


def make_report(truth, rng, vagueness=1.0):
    """What the cabinet is told. `vagueness` scales how damaged the report is."""
    report = dict(
        incident=truth["incident"],
        reported_bleeding=truth["bleeding"],
        fire_present=truth["fire"],
        water_incident=truth["water"],
        traffic_hazard=truth["traffic"],
        people_affected=truth["people"],
        person_responsive="no" if truth["unresponsive"] else "yes",
        dispatcher_confirmed=1,
    )
    if rng.random() < 0.25 * vagueness:
        report["incident"] = "unclear"
    if rng.random() < 0.35 * vagueness:
        report["person_responsive"] = "unknown"
    if truth["traffic"] and rng.random() < 0.30 * vagueness:
        report["traffic_hazard"] = 0
    if rng.random() < 0.10 * vagueness:
        report["reported_bleeding"] = 1 - report["reported_bleeding"]
    if rng.random() < 0.20 * vagueness:
        report["dispatcher_confirmed"] = 0
    return report


def what_is_needed(truth):
    return {"protective": 1, "comms": 1, "bleeding": truth["bleeding"],
            "aed": truth["unresponsive"], "burns": truth["fire"],
            "flotation": truth["water"], "traffic": truth["traffic"]}


def make_cases(n=4000, seed=3, vagueness=1.0):
    rng = np.random.default_rng(seed)
    reports, answers = [], []
    for _ in range(n):
        truth = make_truth(rng)
        reports.append(make_report(truth, rng, vagueness))
        answers.append(what_is_needed(truth))
    return pd.DataFrame(reports), pd.DataFrame(answers)[COMPARTMENTS]


def to_numbers(reports):
    table = pd.get_dummies(reports, columns=["incident", "person_responsive"])
    wanted = ([f"incident_{i}" for i in INCIDENTS]
              + [f"person_responsive_{s}" for s in ["yes", "no", "unknown"]])
    for column in wanted:
        if column not in table.columns:
            table[column] = 0
    return table.astype(float)


FEATURES = sorted(to_numbers(make_cases(20)[0]).columns)


# --------------------------------------------------------------- the systems
def rule_cabinet(report):
    open_now = {c: 0 for c in COMPARTMENTS}
    open_now["protective"] = 1
    open_now["comms"] = 1
    if report["reported_bleeding"]:
        open_now["bleeding"] = 1
    if report["person_responsive"] == "no":
        open_now["aed"] = 1
    if report["fire_present"]:
        open_now["burns"] = 1
    if report["water_incident"]:
        open_now["flotation"] = 1
    if report["traffic_hazard"]:
        open_now["traffic"] = 1
    return open_now


def train_forest(X_train, Y_train):
    model = MultiOutputClassifier(
        RandomForestClassifier(n_estimators=200, min_samples_leaf=5, random_state=42))
    model.fit(X_train, Y_train)
    return model


def probabilities(model, X):
    raw = model.predict_proba(X)
    out = np.column_stack([p[:, 1] for p in raw]) if isinstance(raw, list) else np.asarray(raw)
    table = pd.DataFrame(out, columns=MODELLED, index=X.index)
    for name in ALWAYS_OPEN:
        table[name] = 1.0
    return table[COMPARTMENTS]


def chances_for(model, report):
    row = to_numbers(pd.DataFrame([report])).reindex(columns=FEATURES, fill_value=0.0)
    return probabilities(model, row).iloc[0].to_dict()


def what_is_allowed(cabinet, report):
    """Only physical availability. Whether a restricted item may open yet is
    decided by the safety checks, so the AI is still allowed to ask for it."""
    return {n for n in COMPARTMENTS if usable(cabinet[n])}


def safety_checks(wanted, cabinet, report, neighbour_has=()):
    states, notes, restock = {}, {}, []
    for name in COMPARTMENTS:
        item = cabinet[name]
        asked_for = name in wanted or name == "protective"
        if not asked_for:
            states[name], notes[name] = LOCKED, "not needed for this emergency"
            continue
        if not usable(item):
            why = ("empty" if item["quantity"] <= 0
                   else "package already opened" if not item["sealed"] else "expired")
            restock.append(name)
            if name in neighbour_has:
                states[name] = ELSEWHERE
                notes[name] = f"{why} here - the next cabinet has one"
            else:
                states[name], notes[name] = UNAVAILABLE, why
            continue
        if item["restricted"] and not report["dispatcher_confirmed"]:
            states[name], notes[name] = WAITING, "waiting for the dispatcher to confirm"
            continue
        states[name], notes[name] = UNLOCKED, "open"
        if item["battery"] is not None and item["battery"] < LOW_BATTERY:
            notes[name] = f"open - battery {item['battery']}%, needs replacing"
            restock.append(name)
    return states, notes, restock


def cost_of(kit, chances, cabinet, allowed, expected_later=None):
    expected_later = expected_later or {}
    cost = 0.0
    for name in COMPARTMENTS:
        p = chances[name]
        if name in kit:
            cost += COST_IF_UNNEEDED[name] * (1 - p)
            cost += W_DELAY
            if name not in allowed:
                cost += W_UNSAFE
            if cabinet[name]["consumable"]:
                short_by = expected_later.get(name, 0) - (cabinet[name]["quantity"] - 1)
                if short_by > 0:
                    cost += W_SHORTAGE * short_by
        else:
            cost += W_MISSING * p
    return cost


def best_kit(chances, cabinet, allowed, expected_later=None):
    from itertools import combinations
    best, best_cost = set(), np.inf
    for size in range(len(COMPARTMENTS) + 1):
        for kit in combinations(COMPARTMENTS, size):
            c = cost_of(set(kit), chances, cabinet, allowed, expected_later)
            if c < best_cost:
                best, best_cost = set(kit), c
    return best, best_cost


def cabinet_decides(report, cabinet, model, neighbour_has=(), expected_later=None):
    """model -> allowed -> cheapest kit -> safety checks get the last word."""
    chances = chances_for(model, report)
    kit, _ = best_kit(chances, cabinet, what_is_allowed(cabinet, report), expected_later)

    # What it would have asked for if every shelf were full. Without this, a
    # compartment that is needed but empty comes back as "not needed for this
    # emergency", which is a different and much more misleading statement.
    ideal, _ = best_kit(chances, cabinet, set(COMPARTMENTS), expected_later)

    states, notes, restock = safety_checks(kit | ideal, cabinet, report, neighbour_has)
    return chances, states, notes, restock


def door_opens_above(name, chances, cabinet, allowed):
    for p in np.linspace(0, 1, 201):        # same resolution as the notebook
        trial = dict(chances)
        trial[name] = p
        if name in best_kit(trial, cabinet, allowed)[0]:
            return float(p)
    return None


def score_system(opened, answers, name):
    opened = np.asarray(opened)
    needed = answers[COMPARTMENTS].to_numpy()
    return {"System": name,
            "Missed items": int(((needed == 1) & (opened == 0)).sum()),
            "Extra items": int(((needed == 0) & (opened == 1)).sum()),
            "Got everything needed": f"{(((needed == 1) <= (opened == 1)).all(axis=1)).mean():.0%}",
            "Exactly right": f"{(((needed == 1) == (opened == 1)).all(axis=1)).mean():.0%}"}


# --------------------------------------------------------------- a whole day
N_CABINETS = 5
EMERGENCIES_PER_DAY = 100
STRATEGIES = [("A", "A - open everything"), ("B", "B - the rulebook"),
              ("C", "C - smallest sufficient kit")]


def run_day(strategy, model, share, seed=11, fill=1.0, n=EMERGENCIES_PER_DAY):
    rng = np.random.default_rng(seed)
    cabinets = [fresh_cabinet(seed=20 + i, fill=fill) for i in range(N_CABINETS)]
    handled = [0] * N_CABINETS
    log = []

    for _ in range(n):
        truth = make_truth(rng)
        report = make_report(truth, rng)
        need = what_is_needed(truth)
        which = int(rng.integers(0, N_CABINETS))
        cabinet = cabinets[which]
        neighbour_has = {c for c in COMPARTMENTS
                         for j, other in enumerate(cabinets) if j != which and usable(other[c])}

        if strategy == "A":
            wanted = set(COMPARTMENTS)
        elif strategy == "B":
            wanted = {c for c, v in rule_cabinet(report).items() if v}
        else:
            calls_left = max(0, n / N_CABINETS - handled[which])
            later = {c: share[c] * calls_left for c in COMPARTMENTS}
            wanted, _ = best_kit(chances_for(model, report), cabinet,
                                 what_is_allowed(cabinet, report), later)

        states, _, restock = safety_checks(wanted, cabinet, report, neighbour_has)
        opened = [c for c in COMPARTMENTS if states[c] == UNLOCKED]
        for name in opened:
            if cabinet[name]["consumable"]:
                cabinet[name]["quantity"] -= 1
            elif name != "comms" and rng.random() > 0.85:
                cabinet[name]["quantity"] -= 1

        handled[which] += 1
        log.append(dict(missed=sum(1 for c in COMPARTMENTS if need[c] and states[c] != UNLOCKED),
                        extra=sum(1 for c in COMPARTMENTS if not need[c] and states[c] == UNLOCKED),
                        doors=len(opened),
                        fully_supplied=all(states[c] == UNLOCKED for c in COMPARTMENTS if need[c]),
                        restock=len(restock)))

    left = sum(max(0, c[n_]["quantity"]) for c in cabinets for n_ in COMPARTMENTS)
    return pd.DataFrame(log), left


# --------------------------------------------------------------- sensors
HOUR_WEIGHTS = np.array([1, 1, 1, 1, 1, 2, 4, 8, 12, 13, 13, 13, 13,
                         13, 13, 13, 12, 11, 9, 7, 5, 3, 2, 1], dtype=float)
HOUR_WEIGHTS = HOUR_WEIGHTS / HOUR_WEIGHTS.sum()
SENSOR_COLUMNS = ["weight_change_g", "items_taken", "seconds_open", "hour", "count_change"]

ODD_DAYS = pd.DataFrame([
    dict(what="somebody emptied the shelf", weight_change_g=-1400, items_taken=6,
         seconds_open=44, hour=14, count_change=-6, really_wrong=True),
    dict(what="a busy-hour amount, at three in the morning", weight_change_g=-360,
         items_taken=3, seconds_open=30, hour=3, count_change=-3, really_wrong=True),
    dict(what="door left open twenty minutes", weight_change_g=-120, items_taken=1,
         seconds_open=1200, hour=15, count_change=-1, really_wrong=True),
    dict(what="weight moved, count did not", weight_change_g=-260, items_taken=2,
         seconds_open=30, hour=11, count_change=0, really_wrong=True),
    dict(what="an ordinary call", weight_change_g=-125, items_taken=1,
         seconds_open=33, hour=13, count_change=-1, really_wrong=False),
])


def normal_days(n, seed=5):
    rng = np.random.default_rng(seed)
    hour = rng.choice(np.arange(24), size=n, p=HOUR_WEIGHTS)
    taken = rng.choice([1, 2, 3], size=n, p=[0.65, 0.28, 0.07])
    return pd.DataFrame({"weight_change_g": -taken * rng.normal(120, 18, n),
                         "items_taken": taken,
                         "seconds_open": rng.gamma(6, 6, n) + 8,
                         "hour": hour, "count_change": -taken})


def rules_on_reading(row):
    problems = []
    if row["items_taken"] > 3:
        problems.append("a lot taken at once")
    if row["seconds_open"] > 300:
        problems.append("door left open a long time")
    if row["items_taken"] > 0 and row["count_change"] == 0:
        problems.append("something was taken but the count did not move")
    if row["hour"] < 5 and row["items_taken"] > 1:
        problems.append("several items in the middle of the night")
    return problems


def build_anomaly(false_alarm_rate=0.05):
    detector = IsolationForest(n_estimators=300, contamination="auto",
                               random_state=42).fit(normal_days(4000)[SENSOR_COLUMNS])
    watch = normal_days(800, seed=6)
    scores = -detector.score_samples(watch[SENSOR_COLUMNS])
    line = float(np.quantile(scores, 1 - false_alarm_rate))

    table = ODD_DAYS.copy()
    table["strangeness"] = (-detector.score_samples(table[SENSOR_COLUMNS])).round(3)
    table["forest"] = np.where(table.strangeness > line, "flagged", "looks normal")
    table["rules"] = ["caught" if rules_on_reading(r) else "missed"
                      for _, r in table.iterrows()]
    verdict = []
    for _, row in table.iterrows():
        spotted = row["forest"] == "flagged" or row["rules"] == "caught"
        if row["really_wrong"]:
            verdict.append("caught" if spotted else "MISSED BY BOTH")
        else:
            verdict.append("false alarm" if spotted else "correctly ignored")
    table["result"] = verdict
    return table, line


EVENT_LOG = [
    ("10:42:01", "-", "cabinet activated"),
    ("10:42:04", "protective", "unlocked"),
    ("10:42:07", "protective", "item removed"),
    ("10:42:09", "bleeding", "unlocked"),
    ("10:42:12", "bleeding", "item removed"),
    ("10:42:14", "traffic", "unlocked"),
    ("10:42:16", "burns", "unlocked"),
    ("10:42:19", "traffic", "item removed"),
    ("10:42:25", "aed", "door forced"),
    ("10:42:25", "-", "warning issued"),
    ("10:42:27", "aed", "item removed"),
    ("10:42:31", "comms", "unlocked"),
    ("10:43:35", "bleeding", "seal broken"),
    ("10:55:03", "traffic", "item returned"),
]


def read_events(log=EVENT_LOG):
    findings, unlocked, removed = [], set(), set()
    for _, where, what in log:
        if what == "unlocked":
            unlocked.add(where)
        elif what == "item removed":
            removed.add(where)
            if where not in unlocked:
                findings.append((where, "something was taken from a door that never unlocked"))
        elif what == "door forced":
            findings.append((where, "door opened without being unlocked"))
        elif what == "seal broken":
            findings.append((where, "package no longer sealed - mark unusable"))
    for name in sorted(unlocked - removed):
        if name != "comms":
            findings.append((name, "unlocked but nothing was taken - relock it"))
    returned = {w for _, w, e in log if e == "item returned"}
    for name in sorted(removed - returned):
        if name != "-" and not fresh_cabinet()[name]["consumable"]:
            findings.append((name, "borrowed and not brought back"))
    return findings


# --------------------------------------------------------------- figures
def _layout(fig, height=400, top=55, **kw):
    fig.update_layout(height=height, paper_bgcolor=BG, plot_bgcolor=BG, font_color="white",
                      margin=dict(l=55, r=20, t=top, b=45),
                      legend=dict(bgcolor="rgba(0,0,0,0)"), **kw)
    fig.update_layout(title_y=1, title_yanchor="top", title_pad_t=12)
    fig.update_xaxes(gridcolor="#21262d", zeroline=False)
    fig.update_yaxes(gridcolor="#21262d", zeroline=False)
    return fig


def fig_doors(states, chances, notes):
    """The seven doors, in the five colours. The centrepiece of the app."""
    fig = go.Figure()
    for i, name in enumerate(COMPARTMENTS):
        colour = STATE_COLOUR[states[name]]
        fig.add_shape(type="rect", x0=i + 0.06, x1=i + 0.94, y0=0, y1=1,
                      fillcolor=colour, line=dict(color="#0e1117", width=2), layer="below")
        fig.add_annotation(x=i + 0.5, y=0.86, text=f"<b>{STATE_WORD[states[name]]}</b>",
                           showarrow=False, font=dict(color="white", size=12))
        fig.add_annotation(x=i + 0.5, y=0.55, text=NAMES[name].replace(" ", "<br>"),
                           showarrow=False, font=dict(color="white", size=11))
        fig.add_annotation(x=i + 0.5, y=0.16, text=f"chance {chances[name]:.2f}",
                           showarrow=False, font=dict(color="white", size=10))
        fig.add_trace(go.Scatter(x=[i + 0.5], y=[0.5], mode="markers",
                                 marker=dict(size=1, color=colour), showlegend=False,
                                 hovertemplate=f"{NAMES[name]}<br>{notes[name]}<extra></extra>"))
    fig.update_xaxes(range=[0, len(COMPARTMENTS)], visible=False)
    fig.update_yaxes(range=[0, 1], visible=False)
    return _layout(fig, height=250, top=30)


def fig_needed(answers):
    share = answers.mean().sort_values()
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=["How often each compartment is needed",
                                        "Almost never just one"])
    fig.add_bar(x=100 * share.to_numpy(), y=[NAMES[n] for n in share.index],
                orientation="h", marker_color=CYAN, showlegend=False, row=1, col=1)
    counts = answers.sum(axis=1).value_counts().sort_index()
    fig.add_bar(x=counts.index.astype(str), y=counts.to_numpy(), marker_color=GREEN,
                showlegend=False, row=1, col=2)
    fig.update_xaxes(title_text="% of emergencies", row=1, col=1)
    fig.update_xaxes(title_text="compartments needed at once", row=1, col=2)
    return _layout(fig, height=380, top=70)


def fig_misses(rules_opened, model_opened, answers):
    needed = answers[COMPARTMENTS].to_numpy()
    rules = [int(((needed[:, i] == 1) & (rules_opened[:, i] == 0)).sum())
             for i in range(len(COMPARTMENTS))]
    model = [int(((needed[:, i] == 1) & (model_opened[:, i] == 0)).sum())
             for i in range(len(COMPARTMENTS))]
    fig = go.Figure()
    fig.add_bar(x=[NAMES[c] for c in COMPARTMENTS], y=rules, name="rules", marker_color=RED)
    fig.add_bar(x=[NAMES[c] for c in COMPARTMENTS], y=model, name="random forest",
                marker_color=CYAN)
    return _layout(fig, height=390, barmode="group",
                   yaxis_title="needed, but the door stayed shut",
                   title="Where each system misses things, on the same unseen emergencies")


def fig_thresholds(points):
    order = sorted(points, key=lambda n: points[n] if points[n] is not None else 2)
    fig = go.Figure(go.Bar(
        x=[100 * points[n] if points[n] is not None else 100 for n in order],
        y=[f"{NAMES[n]}<br><sub>costs {COST_IF_UNNEEDED[n]} if unneeded</sub>" for n in order],
        orientation="h", marker_color=[RED if n == "aed" else CYAN for n in order],
        texttemplate="%{x:.0f}%", textposition="outside", cliponaxis=False))
    return _layout(fig, height=400, xaxis_title="how sure it has to be before the door opens (%)",
                   title="The more it costs to be wrong, the surer the cabinet has to be")


def fig_day(days, fills):
    fig = go.Figure()
    for (strategy, label), colour in zip(STRATEGIES, [RED, AMBER, GREEN]):
        fig.add_scatter(x=[100 * f for f in fills],
                        y=[100 * days[(strategy, f)][0].fully_supplied.mean() for f in fills],
                        mode="lines+markers", name=label, line=dict(color=colour, width=3))
    return _layout(fig, height=390, xaxis_title="how full the cabinets started (%)",
                   yaxis_title="emergencies fully supplied (%)",
                   title="The same day, at four different stock levels")


def fig_events(log=EVENT_LOG):
    rows = [(t, w, e) for t, w, e in log]
    colour = {"door forced": RED, "warning issued": RED, "seal broken": AMBER,
              "item returned": GREEN, "unlocked": CYAN, "item removed": VIOLET}
    seconds = [(int(t[3:5]) - 42) * 60 + int(t[6:8]) for t, _, _ in rows]
    fig = go.Figure()
    for (t, where, what), x in zip(rows, seconds):
        fig.add_scatter(x=[x], y=[NAMES.get(where, "the cabinet")], mode="markers",
                        marker=dict(size=13, color=colour.get(what, GREY)),
                        showlegend=False, hovertemplate=f"{t} · {what}<extra></extra>")
    return _layout(fig, height=380, xaxis_title="seconds after the cabinet was activated",
                   title="One call, as the sensors recorded it")
