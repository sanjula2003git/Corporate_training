"""
The Northgate 11 kV network, as engineering — plus the narrative stages.
=======================================================================
THE NETWORK MODEL IS A COPY OF THE NOTEBOOK'S. Same buses, same impedances,
same backward/forward sweep, same restoration search — so a number quoted in
`Self_Healing_Grid_AI.ipynb` and the same number on the matching app page always
agree. Change one and you must change both.

Narrative beats:
  network   - 02:14, a fault, and a feeder in the dark.
  zones     - what a switch actually buys you.
  reading   - one fault becomes one row of measurements.
  engine    - the product: one switching plan, with its reasons.
"""
import itertools
from collections import defaultdict

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

import scaffold as S

POS, NEG = S.POS, S.NEG
GREEN, AMBER, RED = S.GREEN, S.AMBER, S.RED
TECH, MUTED, TEXT, PANEL = S.TECH, S.MUTED, S.TEXT, S.PANEL
style, animate = S.style, S.animate

# ============================================================================
# 1 · THE NETWORK
# ============================================================================
KV = 11.0                    # line voltage, kV
SBASE = 1000.0               # kVA base
ZBASE = KV ** 2 * 1000.0 / SBASE          # 121 ohm
VPH = KV * 1000.0 / np.sqrt(3)            # phase voltage, V
VMIN, VMAX = 0.94, 1.05                   # statutory limits, pu
MAX_OPS = 4                               # remote operations allowed in one plan

# id, name, kW, kvar, class, PV kWp, battery kW, battery kWh
BUSES = [
    (0,  "Northgate A busbar",    0,   0,   "source",   0,   0,   0),
    (1,  "Mill Street",           165, 72,  "normal",   0,   0,   0),
    (2,  "Foundry Estate",        285, 130, "priority", 0,   0,   0),
    (3,  "Canal Road",            140, 60,  "normal",   0,   0,   0),
    (4,  "Riverside Flats",       190, 82,  "normal",   150, 0,   0),
    (5,  "Packing Works",         250, 112, "priority", 0,   0,   0),
    (6,  "Elm Avenue",            130, 54,  "normal",   0,   0,   0),
    (7,  "Hospital Approach",     155, 66,  "normal",   0,   0,   0),
    (8,  "District Hospital",     380, 165, "critical", 0,   0,   0),
    (9,  "Beech Park",            175, 76,  "normal",   0,   200, 400),
    (10, "Orchard Lane",          155, 66,  "normal",   0,   0,   0),
    (11, "Willow Grove",          165, 72,  "normal",   120, 0,   0),
    (12, "Telecom Exchange",      130, 48,  "critical", 0,   0,   0),
    (13, "Kiln Row",              140, 60,  "normal",   0,   0,   0),

    (14, "Eastfield B busbar",    0,   0,   "source",   0,   0,   0),
    (15, "Station Road",          175, 76,  "normal",   0,   0,   0),
    (16, "Textile Mill",          270, 124, "priority", 0,   0,   0),
    (17, "Church Street",         140, 60,  "normal",   0,   0,   0),
    (18, "Meadow View",           165, 72,  "normal",   180, 0,   0),
    (19, "Water Pumping Stn",     300, 135, "critical", 0,   0,   0),
    (20, "Highfield",             175, 76,  "normal",   0,   150, 300),
    (21, "Brick Lane",            155, 66,  "normal",   0,   0,   0),
    (22, "Moor End",              165, 72,  "normal",   100, 0,   0),

    (23, "Southcross C busbar",   0,   0,   "source",   0,   0,   0),
    (24, "Market Square",         190, 82,  "normal",   0,   0,   0),
    (25, "Fire & Ambulance Stn",  165, 72,  "critical", 0,   0,   0),
    (26, "Chapel Hill",           140, 60,  "normal",   0,   0,   0),
    (27, "Cold Store",            290, 133, "priority", 0,   0,   0),
    (28, "Vale Road",             155, 66,  "normal",   0,   0,   0),
    (29, "Quarry Side",           165, 72,  "normal",   140, 0,   0),
    (30, "Fell View",             140, 60,  "normal",   0,   0,   0),
    (31, "Grain Dryers",          210, 95,  "priority", 0,   0,   0),
    (32, "Longmoor",              175, 76,  "normal",   160, 0,   0),
]
NB = len(BUSES)
SOURCES = [0, 14, 23]
FEEDER_NAME = {0: "A · Northgate", 14: "B · Eastfield", 23: "C · Southcross"}
SRC_MVA = {0: 3.4, 14: 2.8, 23: 2.8}        # firm transformer rating
WEIGHT = {"critical": 20.0, "priority": 4.0, "normal": 1.0, "source": 0.0}
CUSTOMERS_PER_100KW = 42                     # for customer-minutes lost

R_OHM_KM, X_OHM_KM = 0.36, 0.34
TRUNK, LAT, TIEA = 300.0, 210.0, 200.0       # conductor ampacity, A

# id, from, to, km, kind, label, ampacity
LINES = [
    (0,  0,  1,  0.6, "switch", "CB-A",  TRUNK),
    (1,  1,  2,  0.7, "fixed",  "",      TRUNK),
    (2,  2,  3,  0.8, "switch", "SW-A1", TRUNK),
    (3,  3,  4,  0.7, "fixed",  "",      TRUNK),
    (4,  4,  5,  0.9, "switch", "SW-A2", TRUNK),
    (5,  5,  6,  0.8, "fixed",  "",      TRUNK),
    (6,  6,  7,  0.9, "switch", "SW-A3", TRUNK),
    (7,  7,  8,  0.7, "fixed",  "",      TRUNK),
    (8,  8,  9,  0.8, "fixed",  "",      LAT),
    (9,  3,  10, 0.8, "switch", "SW-A4", LAT),
    (10, 10, 11, 0.9, "fixed",  "",      LAT),
    (11, 6,  12, 0.9, "switch", "SW-A5", LAT),
    (12, 12, 13, 0.8, "fixed",  "",      LAT),

    (13, 14, 15, 0.6, "switch", "CB-B",  TRUNK),
    (14, 15, 16, 0.8, "fixed",  "",      TRUNK),
    (15, 16, 17, 0.9, "switch", "SW-B1", TRUNK),
    (16, 17, 18, 0.8, "fixed",  "",      TRUNK),
    (17, 18, 19, 0.9, "switch", "SW-B2", TRUNK),
    (18, 19, 20, 0.8, "fixed",  "",      LAT),
    (19, 17, 21, 0.9, "switch", "SW-B3", LAT),
    (20, 21, 22, 0.8, "fixed",  "",      LAT),

    (21, 23, 24, 0.6, "switch", "CB-C",  TRUNK),
    (22, 24, 25, 0.8, "fixed",  "",      TRUNK),
    (23, 25, 26, 0.9, "switch", "SW-C1", TRUNK),
    (24, 26, 27, 0.8, "fixed",  "",      TRUNK),
    (25, 27, 28, 0.9, "switch", "SW-C2", TRUNK),
    (26, 26, 29, 0.9, "switch", "SW-C3", LAT),
    (27, 29, 30, 0.8, "fixed",  "",      LAT),
    (28, 28, 31, 0.8, "fixed",  "",      LAT),
    (29, 31, 32, 0.9, "fixed",  "",      LAT),

    (30, 9,  20, 1.8, "tie", "TIE-1", TIEA),
    (31, 13, 22, 1.6, "tie", "TIE-2", TIEA),
    (32, 20, 32, 2.0, "tie", "TIE-3", TIEA),
    (33, 11, 24, 1.7, "tie", "TIE-4", TIEA),
    (34, 30, 8,  2.1, "tie", "TIE-5", TIEA),
]
NL = len(LINES)

TIES = [l[0] for l in LINES if l[4] == "tie"]
SECTIONALISERS = [l[0] for l in LINES if l[4] == "switch"]
SWITCHES = SECTIONALISERS + TIES
FIXED = [l[0] for l in LINES if l[4] == "fixed"]
LABEL = {l[0]: l[5] for l in LINES}
KM = np.array([l[3] for l in LINES], float)
AMP = np.array([l[6] for l in LINES], float)
EU = np.array([l[1] for l in LINES])
EV = np.array([l[2] for l in LINES])
ZL = np.array([complex(l[3] * R_OHM_KM, l[3] * X_OHM_KM) for l in LINES])   # ohm
ZPU = ZL / ZBASE

P_KW = np.array([b[2] for b in BUSES], float)
Q_KVAR = np.array([b[3] for b in BUSES], float)
CLS = [b[4] for b in BUSES]
W_KW = np.array([WEIGHT[c] for c in CLS])
PV_KWP = np.array([b[5] for b in BUSES], float)
BATT_KW = np.array([b[6] for b in BUSES], float)
NAME = {b[0]: b[1] for b in BUSES}

# short-circuit source data
ZG = complex(0.12, 0.28)      # 33 kV grid, referred to 11 kV, ohm/phase
ZT = complex(0.14, 0.53)      # substation transformer, ohm/phase
NORMAL_OPEN = frozenset(TIES)


# ---------------------------------------------------------------- zones
def _zone_partition():
    """A zone is what lies between switches — the smallest piece you can isolate."""
    parent = list(range(NB))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i in FIXED:
        ra, rb = find(EU[i]), find(EV[i])
        if ra != rb:
            parent[ra] = rb
    groups = defaultdict(list)
    for n in range(NB):
        groups[find(n)].append(n)
    return sorted(groups.values(), key=lambda g: g[0])


ZONES = _zone_partition()
NZ = len(ZONES)
ZONE_OF = {n: zi for zi, zb in enumerate(ZONES) for n in zb}
FAULT_ZONES = [zi for zi, zb in enumerate(ZONES)
               if not (len(zb) == 1 and zb[0] in SOURCES)]
ZONE_NAME = {zi: " / ".join(NAME[n] for n in zb) for zi, zb in enumerate(ZONES)}


def zone_switches(zi):
    """Every switch on the boundary of zone zi — what must open to isolate it."""
    return [i for i in SWITCHES if ZONE_OF[EU[i]] == zi or ZONE_OF[EV[i]] == zi]


def _line_zone(i):
    """A line belongs to the zone it feeds (switch lines feed the far zone)."""
    zu, zv = ZONE_OF[EU[i]], ZONE_OF[EV[i]]
    if zu == zv:
        return zu
    return zv if _depth(EV[i]) > _depth(EU[i]) else zu


# ---------------------------------------------------------------- normal topology
def _normal_tree():
    adj = defaultdict(list)
    for i in range(NL):
        if i in NORMAL_OPEN:
            continue
        adj[EU[i]].append((EV[i], i))
        adj[EV[i]].append((EU[i], i))
    par_e, par_n, depth, root = {}, {}, {}, {}
    order = []
    for s in SOURCES:
        par_e[s], par_n[s], depth[s], root[s] = -1, -1, 0, s
        q = [s]
        order.append(s)
        while q:
            n = q.pop(0)
            for m, e in adj[n]:
                if m in par_e:
                    continue
                par_e[m], par_n[m] = e, n
                depth[m], root[m] = depth[n] + 1, root[n]
                order.append(m)
                q.append(m)
    return par_e, par_n, depth, root, order


_PE, _PN, _DEPTH, _ROOT, _ORDER = _normal_tree()


def _depth(n):
    return _DEPTH[n]


def path_edges(bus):
    """Edges from the bus's own substation down to it, in the normal configuration."""
    out = []
    n = bus
    while _PE[n] >= 0:
        out.append(_PE[n])
        n = _PN[n]
    return out[::-1]


PATH_Z = {n: sum(ZL[e] for e in path_edges(n)) if path_edges(n) else 0j
          for n in range(NB)}
PATH_KM = {n: float(sum(KM[e] for e in path_edges(n))) for n in range(NB)}
LINE_ZONE = {i: _line_zone(i) for i in range(NL)}
ZONE_KM = {zi: float(sum(KM[i] for i in range(NL) if LINE_ZONE[i] == zi and i not in TIES))
           for zi in range(NZ)}


# ============================================================================
# 2 · THE POWER FLOW  (backward / forward sweep, BIBC form)
# ============================================================================
_TOPO = {}


def topology(open_set):
    """Path matrix M[bus, line] = 1 if the line lies between a source and the bus.

    Returns None when the configuration is not radial — two sources joined, or a
    loop closed. That check is the radiality constraint, and it is free.
    """
    key = frozenset(open_set)
    if key in _TOPO:
        return _TOPO[key]
    adj = defaultdict(list)
    for i in range(NL):
        if i in key:
            continue
        adj[EU[i]].append((EV[i], i))
        adj[EV[i]].append((EU[i], i))
    par_e = np.full(NB, -1)
    par_n = np.full(NB, -1)
    seen = np.zeros(NB, bool)
    order, loop = [], False
    for s in SOURCES:
        if seen[s]:
            loop = True
            continue
        seen[s] = True
        q = [s]
        order.append(s)
        while q:
            n = q.pop(0)
            for m, e in adj[n]:
                if e == par_e[n]:
                    continue
                if seen[m]:
                    loop = True
                else:
                    seen[m] = True
                    par_e[m], par_n[m] = e, n
                    order.append(m)
                    q.append(m)
    if loop:
        _TOPO[key] = None
        return None
    M = np.zeros((NB, NL))
    for n in order:
        e = par_e[n]
        if e < 0:
            continue
        M[n] = M[par_n[n]]
        M[n, e] = 1.0
    out = (M, seen, par_e, par_n)
    _TOPO[key] = out
    return out


def load_state(hour, weekday=True):
    """Network-wide load multiplier and PV multiplier for an hour of the day."""
    h = np.asarray(hour, float) % 24
    shape = (0.55 + 0.45 * np.exp(-((h - 12.5) ** 2) / (2 * 4.2 ** 2))
             + 0.42 * np.exp(-((h - 19.5) ** 2) / (2 * 1.9 ** 2)))
    lm = shape * (1.0 if weekday else 0.86)
    pv = np.maximum(0.0, np.sin(np.pi * np.clip((h - 6.3) / 11.6, 0, 1)) ** 1.25)
    return float(lm), float(pv)


def power_flow(open_set, load_mult, pv_mult, batt=0.0):
    """Backward / forward sweep. Returns |V| per bus, |I| per line, energised mask."""
    t = topology(open_set)
    if t is None:
        return None
    M, seen, par_e, par_n = t
    p = P_KW * load_mult - PV_KWP * pv_mult - BATT_KW * batt
    s = (p + 1j * Q_KVAR * load_mult) / SBASE
    s = np.where(seen, s, 0.0)
    v = np.ones(NB, complex)
    for _ in range(20):
        ibr = M.T @ np.conj(s / v)
        vn = 1.0 - M @ (ZPU * ibr)
        if np.max(np.abs(vn - v)) < 1e-8:
            v = vn
            break
        v = vn
    ibr = M.T @ np.conj(s / v)
    iamp = np.abs(ibr) * SBASE / (np.sqrt(3) * KV)
    src = {}
    for sb in SOURCES:
        kids = [par_e[n] for n in range(NB) if par_n[n] == sb and par_e[n] >= 0]
        src[sb] = float(sum(abs(v[sb] * np.conj(ibr[e])) for e in kids) * SBASE)
    return np.abs(v), iamp, seen, src


def check(open_set, load_mult, pv_mult, batt=0.0):
    """Is this configuration legal, and how much weighted load does it serve?"""
    r = power_flow(open_set, load_mult, pv_mult, batt)
    if r is None:
        return dict(radial=False, ok=False, why="not radial", served=-1.0)
    v, i, live, src = r
    vmin = float(v[live].min())
    closed = np.array([e not in open_set for e in range(NL)])
    iload = float(np.max(np.where(closed, i / AMP, 0.0)))
    txload = max(src[s] / (SRC_MVA[s] * 1000.0) for s in SOURCES)
    why = []
    if vmin < VMIN:
        why.append(f"voltage {vmin:.3f} pu")
    if iload > 1.0:
        why.append(f"line {iload:.0%} of rating")
    if txload > 1.0:
        why.append(f"transformer {txload:.0%}")
    return dict(radial=True, ok=not why, why=" · ".join(why) or "within every limit",
                vmin=vmin, iload=iload, txload=txload, live=live, V=v, I=i, src=src,
                served=float(np.sum((W_KW * P_KW * load_mult)[live])),
                kw_live=float(np.sum((P_KW * load_mult)[live])))


# ============================================================================
# 3 · ISOLATION AND RESTORATION
# ============================================================================
def isolate(zone):
    """The switches that must open. Nothing about this step is learned."""
    return set(zone_switches(zone))


def dead_mask(open_set):
    t = topology(open_set)
    return None if t is None else ~t[1]


def candidate_plans(zone, max_ops=MAX_OPS):
    """Every switching plan worth checking.

    The rule that shapes this set is an operating rule, not a modelling
    convenience: **restoration may only operate switches inside the
    de-energised region.** A plan that blacks out a healthy customer to
    reconnect another one is not a restoration, and no control room signs it.
    """
    iso = isolate(zone)
    base = set(NORMAL_OPEN) | iso
    dead = dead_mask(base)
    faulted = set(ZONES[zone])
    ties = [t for t in TIES if t not in iso and dead[EU[t]] != dead[EV[t]]
            and EU[t] not in faulted and EV[t] not in faulted]
    secs = [s for s in SECTIONALISERS if s not in iso and dead[EU[s]] and dead[EV[s]]
            and EU[s] not in faulted and EV[s] not in faulted]
    out = []
    for k in range(min(len(ties), max_ops) + 1):
        for ts in itertools.combinations(ties, k):
            for j in range(min(len(secs), max_ops - k) + 1):
                for os_ in itertools.combinations(secs, j):
                    out.append(dict(open=(base - set(ts)) | set(os_), ops=k + j,
                                    close_ties=ts, open_secs=os_))
    return iso, out, dead


def restore(zone, load_mult, pv_mult, batt=0.0, max_ops=MAX_OPS):
    """Exhaustive search for the best legal switching plan. No model involved."""
    iso, cands, dead = candidate_plans(zone, max_ops)
    best, n_radial, n_feasible = None, 0, 0
    for c in cands:
        r = check(c["open"], load_mult, pv_mult, batt)
        if not r["radial"]:
            continue
        n_radial += 1
        if not r["ok"]:
            continue
        n_feasible += 1
        key = (round(r["served"], 3), -c["ops"])
        if best is None or key > best[0]:
            best = (key, c, r)
    return dict(isolate=iso, best=None if best is None else best[1],
                result=None if best is None else best[2],
                n_candidates=len(cands), n_radial=n_radial, n_feasible=n_feasible,
                dead_after_isolation=dead)


# ============================================================================
# 4 · THE FAULT, AND WHAT THE NETWORK MEASURES
# ============================================================================
FPI_SWITCHES = [0, 13, 21, 4, 15, 23]          # CB-A/B/C, SW-A2, SW-B1, SW-C1
MONITORS = [2, 9, 16, 27]                       # power-quality monitors

_FEEDER_OF = {n: _ROOT[n] for n in range(NB)}


def subtree(bus):
    """Buses fed through this bus in the normal configuration."""
    out, stack = set(), [bus]
    while stack:
        n = stack.pop()
        out.add(n)
        stack += [m for m in range(NB) if _PN[m] == n]
    return out


SUBTREE = {n: subtree(n) for n in range(NB)}


def downstream_of(line):
    far = EV[line] if _DEPTH[EV[line]] > _DEPTH[EU[line]] else EU[line]
    return SUBTREE[far]


DOWNSTREAM = {i: downstream_of(i) for i in range(NL) if i not in TIES}
FPI_COVERS = {i: DOWNSTREAM[i] for i in FPI_SWITCHES}
INV_LIMIT = 1.6          # inverters ride through at ~1.6 x rated current


def fault_measurements(line, km_along, rf, load_mult, pv_mult, batt, rng):
    """What the relays and monitors record in the first two cycles of a fault.

    A short circuit is a voltage divider, so how much current flows says how far
    away it is. Two things spoil that. Fault resistance adds impedance the relay
    cannot tell from line impedance — which is why relays measure *reactance*,
    not magnitude. And any generation beyond the fault feeds it too, so the
    relay no longer sees the whole fault current, and the resistance it cannot
    see leaks into the reactance it can. Distributed solar breaks the classical
    fault locator, and it is the same solar that makes restoration possible.
    """
    up = EU[line] if _DEPTH[EU[line]] < _DEPTH[EV[line]] else EV[line]
    down = EV[line] if up == EU[line] else EU[line]
    src = _FEEDER_OF[up]
    z_line = complex(km_along * R_OHM_KM, km_along * X_OHM_KM)
    z_path = PATH_Z[up] + z_line               # relay busbar to the fault
    z_src = ZG + ZT

    # generation beyond the fault, as a current source in phase with the busbar
    beyond = SUBTREE[down]
    der_kw = float(np.sum(PV_KWP[list(beyond)]) * pv_mult
                   + np.sum(BATT_KW[list(beyond)]) * batt)
    i_der = INV_LIMIT * der_kw * 1000.0 / (np.sqrt(3) * KV * 1000.0)      # A, angle 0

    i_relay = (VPH - rf * i_der) / (z_src + z_path + rf)
    v_relay = VPH - i_relay * z_src
    z_app = v_relay / i_relay                  # what the relay computes
    v33 = 1.0 - (i_relay * ZG) / VPH

    sags = []
    for m in MONITORS:
        if _FEEDER_OF[m] != src:
            vm = v33
        else:
            common = set(path_edges(m)) & set(path_edges(up))
            zc = sum(ZL[e] for e in common) if common else 0j
            if line in path_edges(m):
                zc += z_line                   # the monitor sits beyond the fault point
            vm = (v_relay - i_relay * zc) / VPH
        sags.append(float(np.clip(1.0 - abs(vm), 0.0, 1.0)))

    # the switch sits at the upstream end of its own line, so a fault anywhere
    # along that line is downstream of it
    fpis = []
    for sw in FPI_SWITCHES:
        passed = (sw == line) or (sw in path_edges(up))
        if passed and rng.random() < 0.015:
            passed = False                      # comms failure — it saw it, nobody heard
        elif (not passed) and rng.random() < 0.005:
            passed = True                       # spurious operation
        fpis.append(int(passed))

    return dict(i_fault_ka=abs(i_relay) / 1000.0 * float(rng.normal(1.0, 0.03)),
                x_app_ohm=float(z_app.imag) * float(rng.normal(1.0, 0.03)),
                r_app_ohm=float(z_app.real) * float(rng.normal(1.0, 0.03)),
                v33=float(abs(v33)), sags=[float(np.clip(s * rng.normal(1.0, 0.02), 0, 1))
                                           for s in sags],
                fpis=fpis, src=src, der_kw=der_kw)


def fpi_candidates(fpis, src):
    """What pure logic can conclude from the fault-passage indicators alone."""
    live = {sw: f for sw, f in zip(FPI_SWITCHES, fpis)}
    zs = []
    for zi in FAULT_ZONES:
        rep = ZONES[zi][0]
        if _FEEDER_OF[rep] != src:
            continue
        ok = True
        for sw in FPI_SWITCHES:
            if _FEEDER_OF[EU[sw]] != src and _FEEDER_OF[EV[sw]] != src:
                continue
            covered = any(b in FPI_COVERS[sw] for b in ZONES[zi])
            if bool(live[sw]) != covered:
                ok = False
                break
        if ok:
            zs.append(zi)
    return zs or [zi for zi in FAULT_ZONES if _FEEDER_OF[ZONES[zi][0]] == src]


ZONE_KM_RANGE = {}
for _zi in FAULT_ZONES:
    _d = [PATH_KM[n] for n in ZONES[_zi]]
    _up = [PATH_KM[EU[i]] for i in range(NL) if LINE_ZONE.get(i) == _zi and i not in TIES]
    ZONE_KM_RANGE[_zi] = (min(_d + _up), max(_d + _up))


X_PER_KM = X_OHM_KM


def reactance_locator(x_app_ohm, src, candidates):
    """The classical method a real relay uses: reactance to the fault, in km.

    Reactance rather than magnitude, because a fault arc is resistive and would
    otherwise be counted as extra line. It is a good method. It is not enough.
    """
    km = max(0.0, x_app_ohm / X_PER_KM)
    best, bd = candidates[0], 1e9
    for zi in candidates:
        lo, hi = ZONE_KM_RANGE[zi]
        d = 0.0 if lo <= km <= hi else min(abs(km - lo), abs(km - hi))
        if d < bd:
            best, bd = zi, d
    return best, km


# ============================================================================
# 5 · THE EVENT LOG
# ============================================================================
FEATURES = ["i_fault_ka", "x_app_ohm", "r_app_ohm", "v33_pu",
            "sag_1", "sag_2", "sag_3", "sag_4",
            "fpi_1", "fpi_2", "fpi_3", "fpi_4", "fpi_5", "fpi_6",
            "load_mult", "pv_mult", "hour_sin", "hour_cos", "feeder"]
NICE = ["Fault current (kA)", "Apparent X (Ω)", "Apparent R (Ω)", "33 kV sag",
        "Sag · Foundry", "Sag · Beech Park", "Sag · Textile Mill", "Sag · Cold Store",
        "FPI CB-A", "FPI CB-B", "FPI CB-C", "FPI SW-A2", "FPI SW-B1", "FPI SW-C1",
        "Load level", "Solar level", "hour sin", "hour cos", "Feeder"]
CHECK_CH = ["i_fault_ka", "x_app_ohm", "sag_1", "sag_2", "sag_3", "sag_4"]


def make_events(n_events=1500, seed=7):
    """A synthetic fault history: the log a DMS would have after several years."""
    rng = np.random.default_rng(seed)
    faultable = [i for i in range(NL) if i not in TIES]
    wt = np.array([KM[i] for i in faultable], float)
    wt = wt / wt.sum()
    rows = []
    for k in range(n_events):
        line = int(rng.choice(faultable, p=wt))
        km_along = float(rng.random()) * KM[line]
        up = EU[line] if _DEPTH[EU[line]] < _DEPTH[EV[line]] else EV[line]
        rf = float(np.clip(rng.gamma(1.5, 1.3), 0.0, 8.0))
        hour = float(rng.integers(0, 24)) + float(rng.random())
        weekday = bool(rng.random() > 0.28)
        lm, pv = load_state(hour, weekday)
        lm = float(np.clip(lm * float(rng.normal(1.0, 0.045)), 0.45, 1.16))
        batt = 1.0 if (rng.random() < 0.55 and 17.5 <= hour < 22.0) else 0.0
        m = fault_measurements(line, km_along, rf, lm, pv, batt, rng)
        rows.append(dict(
            event=k, line=line, zone=LINE_ZONE[line], km_along=PATH_KM[up] + km_along,
            rf_ohm=rf, hour=hour, weekday=int(weekday), load_mult=lm, pv_mult=pv,
            batt=batt, der_beyond_kw=m["der_kw"], feeder=SOURCES.index(m["src"]),
            i_fault_ka=m["i_fault_ka"], x_app_ohm=m["x_app_ohm"],
            r_app_ohm=m["r_app_ohm"], v33_pu=m["v33"],
            **{f"sag_{j+1}": s for j, s in enumerate(m["sags"])},
            **{f"fpi_{j+1}": f for j, f in enumerate(m["fpis"])}))
    df = pd.DataFrame(rows)
    df["hour_sin"] = np.sin(2 * np.pi * df.hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df.hour / 24)

    # the faults every real event log carries
    n = len(df)
    df.loc[rng.choice(n, int(0.012 * n), replace=False), "i_fault_ka"] = np.nan
    df.loc[rng.choice(n, int(0.008 * n), replace=False), "sag_2"] = np.nan
    df.loc[rng.choice(n, 11, replace=False), "i_fault_ka"] = 99.9      # CT saturation
    df.loc[rng.choice(n, 9, replace=False), "sag_3"] = -0.4            # bad PQ scaling
    df.loc[rng.choice(n, 7, replace=False), "x_app_ohm"] = 0.0         # relay reset
    return df


# ============================================================================
# 6 · SCORING IN THE UNITS OF A UTILITY
# ============================================================================
T_MANUAL_MIN = 68.0      # crew locates and switches by hand
T_AUTO_MIN = 0.9         # FLISR: detect, decide, operate


def customers(kw):
    return kw / 100.0 * CUSTOMERS_PER_100KW


def outage_cost(kw_off, minutes, critical_kw_off=0.0):
    """Energy not supplied plus the interruption cost the regulator recognises."""
    ens_kwh = kw_off * minutes / 60.0
    return dict(ens_kwh=ens_kwh,
                customer_minutes=customers(kw_off) * minutes,
                critical_customer_minutes=customers(critical_kw_off) * minutes)


# ============================================================================
# ================= 1 · THE NETWORK ==========================================
# ============================================================================
def _network_figure(open_set=NORMAL_OPEN, live=None, fault_zone=None, title=""):
    """A schematic of the network — geographic enough to reason about."""
    pos = {
        0: (0.0, 3.0), 1: (1.0, 3.0), 2: (2.0, 3.0), 3: (3.0, 3.0), 4: (4.0, 3.0),
        5: (5.0, 3.0), 6: (6.0, 3.0), 7: (7.0, 3.0), 8: (8.0, 3.0), 9: (9.0, 3.0),
        10: (3.0, 4.1), 11: (4.0, 4.1), 12: (6.0, 4.1), 13: (7.0, 4.1),
        14: (0.0, 0.6), 15: (1.2, 0.6), 16: (2.4, 0.6), 17: (3.6, 0.6),
        18: (4.8, 0.6), 19: (6.0, 0.6), 20: (7.4, 0.6), 21: (3.6, 1.6), 22: (4.9, 1.6),
        23: (0.0, -1.8), 24: (1.2, -1.8), 25: (2.4, -1.8), 26: (3.6, -1.8),
        27: (4.8, -1.8), 28: (6.0, -1.8), 29: (3.6, -2.9), 30: (4.9, -2.9),
        31: (7.2, -1.8), 32: (8.4, -1.8),
    }
    fig = go.Figure()
    for i in range(NL):
        u, v = EU[i], EV[i]
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        is_open = i in open_set
        kind = LINES[i][4]
        if is_open:
            col, dash, wdt = MUTED, "dot", 1.4
        elif live is not None and not (live[u] and live[v]):
            col, dash, wdt = "#3a4250", "solid", 2.0
        elif kind == "tie":
            col, dash, wdt = GREEN, "solid", 3.0
        else:
            col, dash, wdt = POS, "solid", 2.6
        fig.add_trace(go.Scatter(x=[x0, x1], y=[y0, y1], mode="lines",
                                 line=dict(color=col, width=wdt, dash=dash),
                                 hoverinfo="skip", showlegend=False))
        if kind in ("switch", "tie"):
            fig.add_trace(go.Scatter(
                x=[(x0 + x1) / 2], y=[(y0 + y1) / 2], mode="markers",
                marker=dict(size=10, symbol="square",
                            color=("#0e1117" if is_open else (GREEN if kind == "tie" else AMBER)),
                            line=dict(color=(MUTED if is_open else AMBER), width=2)),
                hovertext=f"{LABEL[i]} — {'OPEN' if is_open else 'CLOSED'}",
                hoverinfo="text", showlegend=False))

    for n in range(NB):
        x, y = pos[n]
        c = CLS[n]
        if c == "source":
            mk = dict(size=22, symbol="square", color=TECH, line=dict(color=TEXT, width=2))
        elif c == "critical":
            mk = dict(size=16, symbol="star", color=RED, line=dict(color=TEXT, width=1))
        elif c == "priority":
            mk = dict(size=12, symbol="diamond", color=AMBER)
        else:
            mk = dict(size=9, symbol="circle", color=POS)
        if live is not None and not live[n]:
            mk = dict(mk)
            mk["color"] = "#39414e"
        if fault_zone is not None and ZONE_OF[n] == fault_zone:
            fig.add_trace(go.Scatter(x=[x], y=[y], mode="markers",
                                     marker=dict(size=30, color=RED, opacity=0.28),
                                     hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=[x], y=[y], mode="markers", marker=mk,
                                 hovertext=f"{NAME[n]} · {P_KW[n]:.0f} kW · {c}",
                                 hoverinfo="text", showlegend=False))

    for sb, lab in ((0, "FEEDER A"), (14, "FEEDER B"), (23, "FEEDER C")):
        x, y = pos[sb]
        fig.add_annotation(x=x - 0.15, y=y + 0.45, text=lab, showarrow=False,
                           font=dict(size=10, color=TECH, family=S.MONOF), xanchor="left")
    fig.update_layout(title=title)
    fig.update_xaxes(visible=False, range=[-0.9, 9.7])
    fig.update_yaxes(visible=False, range=[-3.7, 4.9], scaleanchor="x", scaleratio=0.62)
    return style(fig, 470)


def render_network():
    st.title("02:14 — a cable fails, and 2,000 homes go dark")
    st.markdown("#### The network already has everything it needs to heal itself. "
                "Nobody is awake to operate it.")
    st.caption("Three substations, thirty load points, eleven remote switches and five "
               "normally-open ties between feeders.")
    st.write("")

    st.plotly_chart(_network_figure(title="the Northgate 11 kV distribution network, "
                                          "normal running arrangement"),
                    use_container_width=True)
    st.caption("⬛ substation  ★ critical load  ◆ industrial  ● domestic  "
               "🟩 tie switch (normally open)  🟧 sectionaliser (normally closed)")
    st.write("")

    c = st.columns(4)
    c[0].metric("Load points", NB - len(SOURCES))
    c[1].metric("Peak demand", f"{P_KW.sum()/1000:.2f} MW")
    c[2].metric("Remote switches", len(SWITCHES))
    c[3].metric("Critical sites", sum(1 for x in CLS if x == "critical"))
    st.write("")

    st.markdown("### What happens today when a cable fails")
    steps = [
        ("⚡  0 s — the fault", "A cable joint fails. Several thousand amps flow for a "
                                "tenth of a second.", RED),
        ("🔌  0.1 s — the breaker trips", "The substation breaker opens. It has protected "
                                          "the network, and it has just de-energised the "
                                          "**whole feeder** — healthy sections included.", AMBER),
        ("📞  0–20 min — the calls", "The control room learns there is a fault the way it "
                                     "always has: the phone rings.", MUTED),
        ("🚐  20–60 min — the patrol", "A crew drives the route looking for the damage. "
                                       "On a 9 km feeder at night this is the slow part.", MUTED),
        ("🔧  60–70 min — the switching", "The faulted section is isolated by hand and the "
                                          "healthy parts are picked up from a neighbouring "
                                          "feeder.", POS),
    ]
    for t, txt, col in steps:
        st.markdown(f"<div style='padding:12px 16px;margin:6px 0;border-radius:4px;"
                    f"border-left:4px solid {col};background:{PANEL};color:{TEXT}'>"
                    f"<b>{t}</b><br><span style='color:{MUTED}'>{txt}</span></div>",
                    unsafe_allow_html=True)
    st.write("")

    lm, pv = load_state(19.0)
    zone = 2
    iso = isolate(zone)
    sect = check(set(NORMAL_OPEN) | iso, lm, pv)
    base = check(NORMAL_OPEN, lm, pv)
    off_kw = base["kw_live"] - sect["kw_live"]
    feeder_kw = float(np.sum(P_KW[[n for n in range(NB) if _FEEDER_OF[n] == 0]]) * lm)

    st.markdown("### The number that matters")
    c = st.columns(3)
    c[0].metric("Off at the moment of the trip", f"{feeder_kw:,.0f} kW",
                f"≈ {customers(feeder_kw):,.0f} customers", delta_color="off")
    c[1].metric("Still off after 68 minutes", f"{off_kw:,.0f} kW",
                "only the faulted section, once a crew has switched", delta_color="off")
    c[2].metric("Customer-minutes lost", f"{customers(feeder_kw)*T_MANUAL_MIN:,.0f}",
                "one fault, one feeder", delta_color="off")
    st.write("")

    st.error(f"**Almost all of that is avoidable.** Only **{off_kw:,.0f} kW** of the "
             f"**{feeder_kw:,.0f} kW** is actually attached to the broken cable. The rest is "
             f"healthy plant, sitting dark for an hour, waiting for a person to reach a "
             f"switch that could have been operated remotely in a second.")
    st.success("**Self-healing is not a new network. It is the same network, decided faster.** "
               "Every switch in the diagram is already motorised. The only thing missing is the "
               "decision — where is the fault, and what should be closed.")


# ============================================================================
# ================= 2 · WHAT A SWITCH BUYS YOU ===============================
# ============================================================================
def render_zones():
    st.title("Zones — what a switch actually buys you")
    st.markdown("#### You cannot isolate a fault more finely than your switches allow.")
    st.caption("A zone is the smallest piece of network you can cut out. Faults do not "
               "happen at switches; they happen between them.")
    st.write("")

    zi = st.selectbox("Pick a zone", FAULT_ZONES,
                      format_func=lambda z: f"Zone {z:02d} — {ZONE_NAME[z]}", index=2)
    iso = isolate(zi)
    lm, pv = load_state(19.0)
    sect = check(set(NORMAL_OPEN) | iso, lm, pv)
    base = check(NORMAL_OPEN, lm, pv)

    st.plotly_chart(_network_figure(set(NORMAL_OPEN) | iso, sect["live"], zi,
                                    f"fault in zone {zi:02d} — after isolation, before restoration"),
                    use_container_width=True)
    st.write("")

    zone_kw = float(np.sum(P_KW[ZONES[zi]]) * lm)
    dark_kw = base["kw_live"] - sect["kw_live"]
    c = st.columns(4)
    c[0].metric("Load on the faulted zone", f"{zone_kw:,.0f} kW", "cannot be restored at all",
                delta_color="off")
    c[1].metric("Healthy load left dark", f"{dark_kw - zone_kw:,.0f} kW",
                "restoration exists for this", delta_color="off")
    c[2].metric("Switches to operate", len(iso))
    c[3].metric("Zone circuit length", f"{ZONE_KM[zi]:.1f} km")
    st.write("")

    st.markdown("##### The switches that have to open")
    st.dataframe(pd.DataFrame(
        [[LABEL[i], f"{NAME[EU[i]]} → {NAME[EV[i]]}",
          "tie (already open)" if i in TIES else "sectionaliser"] for i in sorted(iso)],
        columns=["Switch", "Between", "Type"]), use_container_width=True, hide_index=True)
    st.write("")

    if dark_kw - zone_kw < 1:
        st.info("**This zone is a dead end.** Nothing hangs off it, so isolation is the whole "
                "job — there is nothing further to restore. Roughly half of all faults are "
                "like this, and for them the right plan is to stop.")
    else:
        st.warning(f"**{dark_kw - zone_kw:,.0f} kW of healthy network is now dark** purely "
                   f"because it sits behind the fault. Every kilowatt of it is a restoration "
                   f"problem, and the answer is a tie switch on a neighbouring feeder.")
    st.success("**More switches means smaller zones means shorter outages** — and it is the "
               "most expensive sentence in distribution engineering. Each remote switch is real "
               "capital, so the zone map is a budget decision, not a technical one.")


# ============================================================================
# ================= 3 · ONE FAULT BECOMES ONE ROW ============================
# ============================================================================
def render_reading(get_data):
    st.title("One fault — how a short circuit becomes data")
    st.markdown("#### Everything the algorithm will ever know arrives in about 40 milliseconds.")
    d = get_data()
    st.write("")

    steps = [
        ("⚡  The fault", "A cable fails somewhere along 9 km of circuit. Nobody sees it "
                          "happen.", MUTED),
        ("📟  The relay measures", "The substation relay records how much current flowed "
                                   "before it tripped. More current means a closer fault — "
                                   "that is the whole basis of impedance location.", POS),
        ("🚦  The indicators report", "Six fault-passage indicators say whether fault current "
                                      "went past them. Six bits, and they are worth more than "
                                      "any single analogue channel.", AMBER),
        ("📉  The monitors record the sag", "Power-quality monitors elsewhere on the network "
                                            "record how far their voltage dipped. The pattern "
                                            "says where in the network the fault sat.", TECH),
        ("📄  It becomes one row", "Seventeen numbers. That is the entire fault, as far as "
                                   "anything downstream is concerned.", GREEN),
    ]
    i = st.slider("Walk through the first two cycles", 1, 5, 1)
    for k, (t, txt, c) in enumerate(steps, start=1):
        if k <= i:
            st.markdown(f"<div style='padding:12px 16px;margin:6px 0;border-radius:4px;"
                        f"border-left:4px solid {c};background:{PANEL};color:{TEXT}'>"
                        f"<b>{t}</b><br><span style='color:{MUTED}'>{txt}</span></div>",
                        unsafe_allow_html=True)
    if i < 5:
        return

    st.write("")
    st.markdown("##### What each channel records, and why it matters")
    st.dataframe(pd.DataFrame([
        ["⚡ Fault current", "Substation relay", "kA", "Distance to the fault — if the fault "
                                                      "resistance is zero, which it never is"],
        ["📉 33 kV sag", "Grid monitor", "pu", "How stiff the fault was, independent of which "
                                               "feeder it was on"],
        ["📉 Sag at four monitors", "PQ monitors", "pu", "The shape of the dip across the "
                                                         "network — a fingerprint of position"],
        ["🚦 Six fault-passage bits", "FPIs on six switches", "0/1", "Which side of each "
                                                                    "indicator the fault was on"],
        ["📊 Load level", "SCADA", "×", "The same fault looks different at 03:00 and 19:00"],
        ["☀️ Solar level", "Inverter telemetry", "×", "Embedded generation feeds the fault too"],
        ["🕐 Hour (sine & cosine)", "Clock", "—", "So 23:45 sits next to 00:00"],
        ["🅰️ Feeder", "Which breaker tripped", "0/1/2", "Free, exact, and never in doubt"],
    ], columns=["Channel", "Source", "Unit", "What it tells you"]),
        use_container_width=True, hide_index=True)
    st.write("")

    row = d["events"].dropna().iloc[3]
    st.markdown("##### One fault = one row of those numbers")
    st.dataframe(pd.DataFrame([[
        f"{row.i_fault_ka:.2f}", f"{row.v33_pu:.3f}",
        f"{row.sag_1:.2f}/{row.sag_2:.2f}/{row.sag_3:.2f}/{row.sag_4:.2f}",
        "".join(str(int(row[f'fpi_{j}'])) for j in range(1, 7)),
        f"{row.load_mult:.2f}", f"{row.pv_mult:.2f}", f"{int(row.feeder)}"]],
        columns=["Fault current kA", "33 kV sag", "Monitor sags", "FPI word",
                 "Load", "Solar", "Feeder"]),
        use_container_width=True, hide_index=True)
    st.info("**Notice what is not in the row: where the fault is.** That is the label, and on "
            "this network it comes from the repair report the crew wrote afterwards — which is "
            "why a utility with no historical fault log has no project until it starts keeping "
            "one.")


# ============================================================================
# ================= 4 · THE PRODUCT ==========================================
# ============================================================================
def render_engine():
    st.title("The restoration plan")
    st.markdown("#### One instruction sequence per fault, with its reasons and its proof.")
    st.caption("This is the product. Everything before it existed to fill in these rows.")
    st.write("")

    rows = [
        dict(t="+0.4 s", act="LOCATE — zone 03, Packing Works / Elm Avenue",
             why="FPI word 100100 narrows it to three zones; 2.7 kA at load 1.09 picks "
                 "this one, 91% confident",
             res="confidence above the 0.80 threshold — isolate one zone, not three",
             col=POS, tag="MODEL"),
        dict(t="+0.6 s", act="ISOLATE — open SW-A2, SW-A3, SW-A5",
             why="the three switches on the boundary of zone 03",
             res="fault confined; 1,070 kW of healthy network now dark",
             col=AMBER, tag="LOGIC"),
        dict(t="+0.9 s", act="RESTORE — close TIE-1 and TIE-2",
             why="picks up the hospital and the telecom exchange from feeder B",
             res="power flow checked: 0.959 pu, 48% of line rating, 99% of transformer",
             col=GREEN, tag="SEARCH"),
        dict(t="+0.9 s", act="HOLD — leave Beech Park on the battery",
             why="closing TIE-5 as well would take feeder C to 104% of firm rating",
             res="295 kW stays off until the repair — and the plan says so out loud",
             col=RED, tag="LIMIT"),
    ]
    for r in rows:
        st.markdown(
            f"<div style='background:{PANEL};border-left:5px solid {r['col']};"
            f"border-radius:4px;padding:14px 18px;margin:8px 0'>"
            f"<div style='display:flex;justify-content:space-between;align-items:baseline'>"
            f"<b style='color:{TEXT};font-size:17px'>{r['t']} &nbsp;·&nbsp; "
            f"<span style='color:{r['col']}'>{r['act']}</span></b>"
            f"<span style='color:{MUTED};font-size:11px;letter-spacing:.14em'>{r['tag']}</span>"
            f"</div><span style='color:{MUTED};font-size:14px'>🧭 {r['why']}</span><br>"
            f"<span style='color:{GREEN};font-size:15px'>▸ {r['res']}</span></div>",
            unsafe_allow_html=True)

    st.write("")
    st.divider()
    st.markdown("### Three different kinds of thing, on one screen")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div style='background:{PANEL};border-top:3px solid {POS};border-radius:4px;"
                f"padding:14px;height:100%'><b style='color:{POS}'>🤖 Learned</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>Only the fault location, and only "
                f"because six indicators cannot resolve fourteen zones. It reports a confidence, "
                f"and the confidence changes what the next step does.</span></div>",
                unsafe_allow_html=True)
    c2.markdown(f"<div style='background:{PANEL};border-top:3px solid {AMBER};border-radius:4px;"
                f"padding:14px;height:100%'><b style='color:{AMBER}'>📐 Logic</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>Isolation is a lookup: the switches "
                f"on the zone boundary. Nobody should learn this, and nothing is gained by "
                f"learning it.</span></div>", unsafe_allow_html=True)
    c3.markdown(f"<div style='background:{PANEL};border-top:3px solid {GREEN};border-radius:4px;"
                f"padding:14px;height:100%'><b style='color:{GREEN}'>🔬 Physics</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>Every restoration plan is proved "
                f"legal by a power flow before it is offered. A model may suggest; only the "
                f"network arithmetic may approve.</span></div>", unsafe_allow_html=True)
    st.write("")

    st.success("**The model is the smallest part of the system, and that is the design working.** "
               "It is used exactly where the instrumentation is genuinely incomplete, and it is "
               "boxed in on both sides — by a confidence threshold in front and a power flow "
               "behind.")
    st.info("Note what the screen never does: it never energises anything it has not first "
            "proved is legal, and it never hides a load it has decided to leave off.")
