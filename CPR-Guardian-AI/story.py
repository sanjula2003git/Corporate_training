"""The simulated rescue, the coaching rules, and the figures the app draws.

A straight port of the notebook's generator and rules - same seeds, same
thresholds, same numbers - with four dials the sidebar can turn: how hard
rescuer A tires, a slipping pad, the patient's depth band, and whether a
second person is in the room. At the default settings every page reproduces
the notebook exactly.

The boundary that does not move: the coach never decides anything about a
shock. There is no branch below that could grow into one.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BG = "#0e1117"
CYAN = "#4fc3f7"
AMBER = "#ffb74d"
RED = "#ef5350"
GREEN = "#66bb6a"
VIOLET = "#ba68c8"
TEAL = "#26a69a"
GREY = "#8b949e"

LIGHT = {"green": GREEN, "amber": AMBER, "red": RED}

FS = 50                              # samples per second from the pad and the camera
RESCUE_SECONDS = 210                 # 3 minutes 30
HANDS_OFF = [(0, 7), (100, 112)]     # arrival, then the AED pause
ARM_CM = 58.0                        # shoulder-to-wrist, this helper

# Guideline targets for an adult. Every threshold below refers to these.
DEPTH_MIN, DEPTH_MAX = 5.0, 6.0      # centimetres
CHILD_MIN, CHILD_MAX = 4.0, 5.0
RATE_MIN, RATE_MAX = 100, 120        # compressions per minute
RECOIL_MAX = 0.5                     # cm still pressed in at full release
SWITCH_SECONDS = 120                 # swap rescuers about every 2 minutes
TARGET_CPM = 110
ELBOW_MIN = 165                      # degrees; below this the arms are bending
SHOULDER_MAX = 5.0                   # cm the shoulders may sit behind the hands
HAND_MAX = 2.5                       # cm the hands may sit off the sternum centre

AED_STATES = {
    "idle":      ("green", "Keep compressing. Pads on the bare chest when you can."),
    "analysing": ("amber", "STOP. Hands off. Do not touch the patient."),
    "shock":     ("red",   "STAND CLEAR. Nobody touching the patient."),
    "resume":    ("green", "Start compressions again NOW - do not wait."),
}


# --------------------------------------------------------------- the rescue
def ramp(t, points):
    """Piecewise-linear control curve: points is [(time, value), ...]."""
    return np.interp(t, [p[0] for p in points], [p[1] for p in points])


def technique(t, tire=1.0):
    """The six curves that describe how each rescuer is pressing, over time.

    `tire` scales rescuer A's decline only. At 1.0 these are the notebook's
    numbers exactly; at 0 A never tires and the fatigue detector should stay
    silent all session.
    """
    a_first = t < 106
    return dict(
        # amplitude of the push, in cm
        amp=np.where(a_first,
                     ramp(t, [(7, 5.4), (55, 5.4 - 0.2 * tire), (80, 5.4 - 0.9 * tire),
                              (100, 5.4 - 1.5 * tire)]),
                     ramp(t, [(112, 5.6), (210, 5.2)])),
        # compressions per minute
        rate=np.where(a_first,
                      ramp(t, [(7, 112), (55, 112 + 2 * tire), (100, 112 + 14 * tire)]),
                      ramp(t, [(112, 96), (145, 97), (165, 110), (210, 112)])),
        # depth still pressed in at full release, in cm
        lean=np.where(a_first,
                      ramp(t, [(7, 0.10), (55, 0.10 + 0.05 * tire), (100, 0.10 + 0.85 * tire)]),
                      ramp(t, [(112, 0.12), (210, 0.18)])),
        # angle at the elbow, degrees; 180 is a straight arm
        elbow=np.where(a_first,
                       ramp(t, [(7, 178), (55, 178 - 2 * tire), (100, 178 - 22 * tire)]),
                       ramp(t, [(112, 168), (135, 177), (210, 177)])),
        # how far the shoulders sit behind the hands, cm
        shoulder_off=np.where(a_first,
                              ramp(t, [(7, 1.0), (55, 1.0 + 0.5 * tire), (100, 1.0 + 5.5 * tire)]),
                              ramp(t, [(112, 2.0), (210, 2.4)])),
        # how far the hands sit off the centre of the sternum, cm
        hand_off=np.where(a_first,
                          ramp(t, [(7, 0.5), (55, 0.5 + 0.4 * tire), (100, 0.5 + 2.7 * tire)]),
                          ramp(t, [(112, 0.8), (210, 1.1)])),
    )


def build_pad(tire=1.0, drift=0.0):
    """The pad signal for the whole rescue, plus the curves that produced it.

    `drift` is a slipping pad, in cm per minute of false extra depth. It is
    added only while somebody is pressing, because that is when a pad slides.
    """
    t = np.arange(0, RESCUE_SECONDS, 1 / FS)

    compressing = np.ones_like(t, dtype=bool)
    for start, end in HANDS_OFF:
        compressing[(t >= start) & (t < end)] = False

    rescuer = np.where(t < 106, "A", "B")
    rescuer[~compressing] = "-"

    c = technique(t, tire)

    rng = np.random.default_rng(11)
    phase = np.zeros_like(t)
    for i in range(1, len(t)):
        step = 2 * np.pi * (c["rate"][i] / 60.0) / FS if compressing[i] else 0.0
        phase[i] = phase[i - 1] + step

    push = (1 - np.cos(phase)) / 2                   # 0 at full release, 1 at the bottom
    depth = np.where(compressing, c["lean"] + c["amp"] * push, 0.0)
    if drift:
        depth += np.where(compressing, drift * t / 60.0, 0.0)
    depth += rng.normal(0, 0.03, len(t))             # pad noise
    depth = np.clip(depth, 0, None)

    pad = pd.DataFrame({"t": t, "depth_cm": depth, "compressing": compressing,
                        "rescuer": rescuer})
    return pad, c, compressing


# --------------------------------------------------------------- the camera
def build_keypoints(elbow_deg, shoulder_offset, hand_offset, chest_depth, jitter=0.4, seed=3):
    """Wrist / elbow / shoulder positions in centimetres, in the camera plane.

    x = sideways across the patient's chest, 0 = centre of the sternum
    y = height above the chest, so pressing down lowers everything
    """
    noise = np.random.default_rng(seed)
    wrist = np.stack([hand_offset, -chest_depth], axis=1)

    dx = np.clip(shoulder_offset, -ARM_CM + 1, ARM_CM - 1)
    shoulder = np.stack([wrist[:, 0] + dx,
                         wrist[:, 1] + np.sqrt(ARM_CM ** 2 - dx ** 2)], axis=1)

    # place the elbow off the shoulder-wrist line so the angle comes out at
    # elbow_deg:  offset = (L/2) / tan(angle/2)
    offset = (ARM_CM / 2) / np.tan(np.radians(elbow_deg) / 2)
    along = shoulder - wrist
    along = along / np.linalg.norm(along, axis=1, keepdims=True)
    perp = np.stack([-along[:, 1], along[:, 0]], axis=1)
    elbow = (wrist + shoulder) / 2 + perp * offset[:, None]

    for arr in (wrist, elbow, shoulder):
        arr += noise.normal(0, jitter, arr.shape)
    return wrist, elbow, shoulder


def angle_at(b, a, c):
    """Angle in degrees at point b, formed by a-b-c. Works on arrays of points."""
    v1, v2 = a - b, c - b
    cosine = ((v1 * v2).sum(axis=1) /
              (np.linalg.norm(v1, axis=1) * np.linalg.norm(v2, axis=1)))
    return np.degrees(np.arccos(np.clip(cosine, -1, 1)))


def smooth(x, seconds=0.6):
    w = max(1, int(seconds * FS))
    return pd.Series(x).rolling(w, center=True, min_periods=1).mean().to_numpy()


# --------------------------------------------------------------- compressions
def find_compressions(depth, fs=FS, min_depth=1.5, min_gap_s=0.25):
    """Indices of the bottom of each compression. Three lines of rule, no library."""
    gap = int(min_gap_s * fs)
    higher_than_neighbours = (depth[1:-1] > depth[:-2]) & (depth[1:-1] >= depth[2:])
    candidates = np.where(higher_than_neighbours & (depth[1:-1] > min_depth))[0] + 1

    peaks = []
    for i in candidates:
        if not peaks or i - peaks[-1] >= gap:
            peaks.append(i)
        elif depth[i] > depth[peaks[-1]]:            # keep the deeper of two close candidates
            peaks[-1] = i
    return np.array(peaks, dtype=int)


def compression_table(pad, peaks, elbow_smooth, shoulder, wrist):
    """One row per compression: how deep, how fast, how far it actually travelled."""
    d = pad.depth_cm.to_numpy()
    times = pad.t.to_numpy()
    who = pad.rescuer.to_numpy()

    rows = []
    for n, p in enumerate(peaks):
        nxt = peaks[n + 1] if n + 1 < len(peaks) else len(pad) - 1
        # the trough's own time as well as its depth, so a figure can put the
        # marker where the chest actually came back up rather than under the peak
        j = p + int(np.argmin(d[p:nxt + 1])) if nxt > p else p
        trough = d[j] if nxt > p else 0.0
        gap_s = (peaks[n + 1] - p) / FS if n + 1 < len(peaks) else np.nan
        rows.append(dict(
            n=n + 1, t=times[p], depth_cm=d[p], residual_cm=trough, residual_t=times[j],
            rate_cpm=60 / gap_s if gap_s and gap_s > 0 else np.nan,
            rescuer=who[p], elbow_deg=elbow_smooth[p],
            shoulder_cm=abs(shoulder[p, 0] - wrist[p, 0]),
            hand_cm=abs(wrist[p, 0]),
        ))

    comp = pd.DataFrame(rows)
    # the gap after the last compression before a pause is not a rate, it is a pause
    comp.loc[comp.rate_cpm < 40, "rate_cpm"] = np.nan
    # how far the chest actually travelled, as opposed to how far down it got
    comp["stroke_cm"] = comp.depth_cm - comp.residual_cm
    return comp


# --------------------------------------------------------------- the coaching
def coach(row, depth_min=DEPTH_MIN, depth_max=DEPTH_MAX):
    """Return (light, message) for one compression. First rule that fires wins.

    The order is by cost to the patient, not by how easy the fault is to
    describe. Depth and recoil move blood; a bent elbow only makes the helper
    tire sooner. One message at a time, because a frightened untrained helper
    given four instructions follows none.
    """
    if row.hand_cm > HAND_MAX:
        return "red", "Move your hands to the centre of the chest"
    if row.depth_cm < depth_min:
        return "red", "Press deeper"
    if row.depth_cm > depth_max:
        return "amber", "Ease off - too deep"
    if row.residual_cm > RECOIL_MAX:
        return "red", "Release fully between pushes"
    if pd.notna(row.rate_cpm) and row.rate_cpm < RATE_MIN:
        return "amber", "Faster - follow the beat"
    if pd.notna(row.rate_cpm) and row.rate_cpm > RATE_MAX:
        return "amber", "Slower - follow the beat"
    if row.elbow_deg < ELBOW_MIN:
        return "amber", "Straighten your arms"
    if row.shoulder_cm > SHOULDER_MAX:
        return "amber", "Move your shoulders forward over your hands"
    return "green", "Good compressions - keep going"


RULE_ORDER = [
    ("Hands off the centre of the chest", "red", "Move your hands to the centre of the chest",
     "The push lands on ribs instead of the sternum."),
    ("Compression too shallow", "red", "Press deeper", "Too little blood moves."),
    ("Compression too deep", "amber", "Ease off - too deep", "Risk of injury."),
    ("Incomplete recoil", "red", "Release fully between pushes",
     "The heart cannot refill if the chest never comes back up."),
    ("Too slow", "amber", "Faster - follow the beat", "Fewer pushes per minute."),
    ("Too fast", "amber", "Slower - follow the beat", "Each push gets shallower."),
    ("Elbows bent", "amber", "Straighten your arms", "The helper tires sooner."),
    ("Shoulders behind the hands", "amber", "Move your shoulders forward over your hands",
     "Arms do the work instead of body weight."),
    ("Everything correct", "green", "Good compressions - keep going", "Steady beat, green light."),
]


def metronome(rates, target=TARGET_CPM, pull=0.03):
    """Start at the helper's own rate, then walk the beat towards the target.

    Note what this does NOT do: chase the helper. The beat is the reference
    they follow, so it only ever moves towards the target. It starts where
    they are so the first beat they hear is one they can already match.
    """
    rates = np.asarray(rates)
    beat = np.empty(len(rates))
    current = rates[0] if len(rates) and not np.isnan(rates[0]) else target
    for i in range(len(rates)):
        current += pull * (target - current)
        beat[i] = np.clip(current, RATE_MIN, RATE_MAX)
    return beat


def add_session(comp, fatigue_drop=0.5):
    """The three things only the whole session can answer."""
    comp = comp.copy()
    for col in ("depth_cm", "stroke_cm", "rate_cpm"):
        comp[col.split("_")[0] + "_roll"] = comp.groupby("rescuer")[col].transform(
            lambda s: s.rolling(15, min_periods=5).mean())

    # against this helper's OWN first twenty compressions. An absolute threshold
    # fires instantly for a small helper and never for a strong one.
    baseline = comp.groupby("rescuer").stroke_cm.transform(lambda s: s.head(20).mean())
    comp["baseline_stroke"] = baseline
    comp["stroke_vs_own_start"] = comp.stroke_roll - baseline
    comp["tiring"] = comp.stroke_vs_own_start < -fatigue_drop

    # the detector that does not work, kept beside the one that does
    depth_baseline = comp.groupby("rescuer").depth_cm.transform(lambda s: s.head(20).mean())
    comp["depth_vs_own_start"] = comp.depth_roll - depth_baseline
    comp["tiring_by_depth"] = comp.depth_vs_own_start < -fatigue_drop
    return comp


def switch_plan(comp, second_person_available=True):
    """When to warn the standby rescuer, and when to call the swap."""
    events = []
    for who, part in comp.groupby("rescuer"):
        start = part.t.iloc[0]
        tired = part[part.tiring]
        by_clock = start + SWITCH_SECONDS
        by_quality = tired.t.iloc[0] if len(tired) else np.inf
        call = min(by_clock, by_quality)
        if call > part.t.iloc[-1]:
            events.append((who, None, None, "finished before a switch was needed"))
            continue
        reason = "quality falling" if by_quality <= by_clock else "two minutes elapsed"
        if not second_person_available:
            events.append((who, None, call,
                           f"{reason}, but nobody else is here - keep going, do not stop"))
        else:
            events.append((who, max(call - 15, start), call, reason))
    return events


def aed_coach(state, hands_on_patient):
    """Coaching around the AED. Never decides whether to shock."""
    if state not in AED_STATES:
        raise ValueError(f"unknown AED state: {state}")
    light, message = AED_STATES[state]
    if state in ("analysing", "shock") and hands_on_patient:
        return "red", "HANDS OFF NOW - " + message
    return light, message


# --------------------------------------------------------------- one call
def build_session(tire=1.0, drift=0.0, depth_min=DEPTH_MIN, depth_max=DEPTH_MAX):
    """Everything on one page of the app, from four dials."""
    pad, curves, compressing = build_pad(tire=tire, drift=drift)
    depth = pad.depth_cm.to_numpy()

    wrist, elbow_pt, shoulder = build_keypoints(
        curves["elbow"], curves["shoulder_off"], curves["hand_off"], depth)
    elbow_measured = angle_at(elbow_pt, shoulder, wrist)
    elbow_smooth = smooth(elbow_measured)

    peaks = find_compressions(depth)
    comp = compression_table(pad, peaks, elbow_smooth, shoulder, wrist)
    comp[["light", "message"]] = comp.apply(
        coach, axis=1, result_type="expand", depth_min=depth_min, depth_max=depth_max)
    comp["beat_cpm"] = comp.groupby("rescuer").rate_cpm.transform(metronome)
    comp = add_session(comp)

    hands_on = compressing.sum() / FS
    return dict(
        pad=pad, curves=curves, compressing=compressing, peaks=peaks, comp=comp,
        wrist=wrist, elbow_pt=elbow_pt, shoulder=shoulder,
        elbow_measured=elbow_measured, elbow_smooth=elbow_smooth,
        hands_on=hands_on, ccf=hands_on / RESCUE_SECONDS,
        depth_min=depth_min, depth_max=depth_max,
    )


def report(comp, depth_min=DEPTH_MIN, depth_max=DEPTH_MAX):
    """The per-rescuer table a trainer would replay afterwards."""
    return pd.DataFrame([{
        "Rescuer": who,
        "Compressions": len(part),
        "Mean depth (cm)": round(part.depth_cm.mean(), 2),
        "Mean stroke (cm)": round(part.stroke_cm.mean(), 2),
        "In-range depth": f"{part.depth_cm.between(depth_min, depth_max).mean():.0%}",
        "Mean rate": round(part.rate_cpm.mean(), 1),
        "In-range rate": f"{part.rate_cpm.between(RATE_MIN, RATE_MAX).mean():.0%}",
        "Full recoil": f"{(part.residual_cm <= RECOIL_MAX).mean():.0%}",
        "Green": f"{(part.light == 'green').mean():.0%}",
    } for who, part in comp.groupby("rescuer")])


def fatigue_summary(comp):
    """First twenty compressions against the last twenty, for each rescuer."""
    rows = []
    for who, part in comp.groupby("rescuer"):
        tired = part[part.tiring]
        by_depth = part[part.tiring_by_depth]
        rows.append({
            "Rescuer": who,
            "Peak depth fell (cm)": round(part.depth_cm.head(20).mean()
                                          - part.depth_cm.tail(20).mean(), 2),
            "Stroke fell (cm)": round(part.stroke_cm.head(20).mean()
                                      - part.stroke_cm.tail(20).mean(), 2),
            "Lean grew (cm)": round(part.residual_cm.tail(20).mean()
                                    - part.residual_cm.head(20).mean(), 2),
            "Watching peak depth": (f"caught at {by_depth.t.iloc[0]:.0f} s"
                                    if len(by_depth) else "never fired"),
            "Watching the stroke": (f"caught at {tired.t.iloc[0]:.0f} s"
                                    if len(tired) else "never fired"),
        })
    return pd.DataFrame(rows)


def pauses_found(pad, peaks, min_gap_s=2.0):
    """Every gap longer than two seconds, found from the signal alone.

    The real unit is not handed the HANDS_OFF list; it has to notice.
    """
    times = pad.t.to_numpy()[peaks]
    edges = np.concatenate([[0.0], times, [RESCUE_SECONDS]])
    gaps = np.diff(edges)
    out = [(edges[i], edges[i] + gaps[i]) for i in np.where(gaps >= min_gap_s)[0]]
    off = sum(b - a for a, b in out)
    return out, 1 - off / RESCUE_SECONDS


# --------------------------------------------------------------- figures
def _layout(fig, height=400, top=50, **kw):
    """`top` needs raising on any figure that has subplot titles as well as a
    main title, or the two land on top of each other."""
    fig.update_layout(height=height, paper_bgcolor=BG, plot_bgcolor=BG, font_color="white",
                      margin=dict(l=55, r=20, t=top, b=45),
                      legend=dict(bgcolor="rgba(0,0,0,0)"), **kw)
    # pin the main title to the very top, clear of any subplot titles below it
    fig.update_layout(title_y=1, title_yanchor="top", title_pad_t=12)
    fig.update_xaxes(gridcolor="#21262d", zeroline=False)
    fig.update_yaxes(gridcolor="#21262d", zeroline=False)
    return fig


# Ordering rule for every make_subplots figure below: traces first, bands and
# reference lines afterwards. A shape targeted at a subplot with row=/col= is
# silently dropped if that subplot has no trace yet - plotly resolves the axis
# from the traces already there, and with none it quietly does nothing. The
# figure still builds and still serialises; it just comes out missing its
# guideline bands, which only rendering it will tell you.
def _mark_pauses(fig, row=None, col=None):
    for start, end in HANDS_OFF:
        kw = dict(x0=start, x1=end, fillcolor=RED, opacity=0.16, line_width=0)
        if row is not None:
            fig.add_vrect(row=row, col=col or 1, **kw)
        else:
            fig.add_vrect(**kw)


def fig_minutes():
    """The rule of thumb every resuscitation course teaches, drawn as a curve.

    This is illustration, not a result: it is the widely-taught 'roughly ten
    percent a minute' figure, and no part of it comes from the simulation.
    """
    m = np.linspace(0, 10, 60)
    fig = go.Figure()
    fig.add_scatter(x=m, y=100 * 0.9 ** m, name="nobody starts compressions",
                    line=dict(color=RED, width=3))
    fig.add_scatter(x=m, y=100 * 0.96 ** m, name="a bystander starts, and keeps going",
                    line=dict(color=GREEN, width=3))
    fig.add_vrect(x0=0, x1=4, fillcolor=CYAN, opacity=0.10, line_width=0,
                  annotation_text="before an ambulance arrives",
                  annotation_font_color="white")
    return _layout(fig, height=360, xaxis_title="minutes since the collapse",
                   yaxis_title="chance of survival (relative, %)",
                   title="Why the first four minutes belong to whoever is standing there")


def fig_whole_rescue(pad, depth_min, depth_max):
    fig = go.Figure()
    fig.add_hrect(y0=depth_min, y1=depth_max, fillcolor=GREEN, opacity=0.16, line_width=0,
                  annotation_text=f"guideline depth {depth_min:.0f}-{depth_max:.0f} cm",
                  annotation_font_color="white")
    fig.add_scatter(x=pad.t, y=pad.depth_cm, line=dict(color=CYAN, width=0.7),
                    name="chest depth", showlegend=False)
    _mark_pauses(fig)
    for label, x in (("arrival", 3.5), ("AED", 106)):
        fig.add_annotation(x=x, y=1.0, yref="paper", text=label, showarrow=False,
                           font=dict(color=RED, size=12))
    return _layout(fig, height=360, xaxis_title="seconds into the rescue",
                   yaxis_title="chest depth (cm)", title="The whole rescue, as the pad sees it")


def fig_zoom(pad, depth_min, depth_max):
    windows = [(20, 25, "Rescuer A, fresh (20-25 s)"), (92, 97, "Rescuer A, tired (92-97 s)")]
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True,
                        subplot_titles=[w[2] for w in windows])
    for i, (lo, hi, _) in enumerate(windows, 1):
        part = pad[(pad.t >= lo) & (pad.t < hi)]
        fig.add_scatter(x=part.t, y=part.depth_cm, line=dict(color=CYAN, width=2),
                        showlegend=False, row=1, col=i)
        fig.add_hrect(y0=depth_min, y1=depth_max, fillcolor=GREEN, opacity=0.16,
                      line_width=0, row=1, col=i)
        fig.add_hline(y=RECOIL_MAX, line_dash="dot", line_color=RED, row=1, col=i)
        fig.update_xaxes(title_text="seconds", row=1, col=i)
    fig.update_yaxes(title_text="chest depth (cm)", row=1, col=1)
    return _layout(fig, height=380, top=95,
                   title="Same helper, one minute apart. The dotted line is full release")


def fig_posture(wrist, elbow_pt, shoulder, elbow_smooth, moments=(20, 96, 150)):
    titles = ["Rescuer A at 20 s - good", "Rescuer A at 96 s - tired", "Rescuer B at 150 s - fresh"]
    fig = make_subplots(rows=1, cols=3, shared_yaxes=True,
                        subplot_titles=[
                            f"{ti}<br><sub>elbow {elbow_smooth[m * FS]:.0f}°, "
                            f"shoulders {shoulder[m * FS, 0]:+.1f} cm</sub>"
                            for ti, m in zip(titles, moments)])
    for i, m in enumerate(moments, 1):
        k = m * FS
        pts = np.stack([wrist[k], elbow_pt[k], shoulder[k]])
        colour = GREEN if elbow_smooth[k] >= ELBOW_MIN else RED
        fig.add_scatter(x=pts[:, 0], y=pts[:, 1], mode="lines+markers",
                        line=dict(color=colour, width=5), marker=dict(size=11, color=colour),
                        showlegend=False, row=1, col=i)
        fig.add_vline(x=0, line_dash="dot", line_color=GREY, row=1, col=i)
        fig.add_scatter(x=[0], y=[0], mode="markers", showlegend=False, row=1, col=i,
                        marker=dict(symbol="x", size=13, color="white"))
        fig.update_xaxes(title_text="cm across the chest", range=[-14, 22], row=1, col=i)
    fig.update_yaxes(title_text="cm above the chest", range=[-6, 64], row=1, col=1)
    return _layout(fig, height=470, top=120,
                   title="Wrist, elbow, shoulder. The cross is the centre of the sternum")


def fig_elbow_error(pad, elbow_true, elbow_measured, elbow_smooth, lo=88, hi=98):
    m = (pad.t >= lo) & (pad.t < hi)
    x = pad.t[m]
    fig = go.Figure()
    fig.add_scatter(x=x, y=elbow_measured[m.to_numpy()], name="measured from raw keypoints",
                    line=dict(color=GREY, width=1))
    fig.add_scatter(x=x, y=elbow_smooth[m.to_numpy()], name="after smoothing",
                    line=dict(color=CYAN, width=3))
    fig.add_scatter(x=x, y=elbow_true[m.to_numpy()], name="what the helper's arm is actually doing",
                    line=dict(color=VIOLET, width=2, dash="dash"))
    fig.add_hline(y=ELBOW_MIN, line_dash="dot", line_color=RED,
                  annotation_text="below this line the arms are bending",
                  annotation_font_color="white")
    return _layout(fig, height=360, xaxis_title="seconds", yaxis_title="elbow angle (degrees)",
                   title="A few millimetres of keypoint wobble is several degrees of angle")


def fig_peaks(pad, comp, lo=30, hi=34):
    m = (pad.t >= lo) & (pad.t < hi)
    sel = comp[(comp.t >= lo) & (comp.t < hi)]
    fig = go.Figure()
    fig.add_scatter(x=pad.t[m], y=pad.depth_cm[m], line=dict(color=CYAN, width=2),
                    name="pad signal")
    fig.add_scatter(x=sel.t, y=sel.depth_cm, mode="markers", name="compression found",
                    marker=dict(color=AMBER, size=13, symbol="triangle-down"))
    fig.add_scatter(x=sel.residual_t, y=sel.residual_cm, mode="markers",
                    name="shallowest point after it",
                    marker=dict(color=VIOLET, size=10, symbol="triangle-up"))
    fig.add_hline(y=1.5, line_dash="dot", line_color=GREY,
                  annotation_text="too shallow to be a push at all",
                  annotation_font_color="white")
    return _layout(fig, height=380, xaxis_title="seconds", yaxis_title="chest depth (cm)",
                   title="Every peak is one compression; every trough is what the chest came back to")


def fig_depth_vs_stroke(comp, depth_min, depth_max):
    fig = go.Figure()
    fig.add_hrect(y0=depth_min, y1=depth_max, fillcolor=GREEN, opacity=0.14, line_width=0)
    fig.add_scatter(x=comp.t, y=comp.depth_cm, mode="markers", name="depth reached",
                    marker=dict(color=CYAN, size=4))
    fig.add_scatter(x=comp.t, y=comp.stroke_cm, mode="markers", name="how far the chest travelled",
                    marker=dict(color=AMBER, size=4))
    _mark_pauses(fig)
    return _layout(fig, height=380, xaxis_title="seconds into the rescue",
                   yaxis_title="centimetres",
                   title="The same pushes, measured two ways. They separate as the helper leans")


def fig_lights(comp):
    order = ["green", "amber", "red"]
    fig = go.Figure()
    for who in sorted(comp.rescuer.unique()):
        part = comp[comp.rescuer == who]
        counts = part.light.value_counts().reindex(order).fillna(0)
        fig.add_bar(x=[o.title() for o in order], y=counts.to_numpy(),
                    name=f"rescuer {who} ({len(part)} compressions)")
    fig.update_traces(marker_line_width=0)
    return _layout(fig, height=340, barmode="group", yaxis_title="compressions",
                   title="What the unit said, per rescuer")


def fig_messages(comp):
    counts = comp.message.value_counts().sort_values()
    colour = [LIGHT[comp[comp.message == m].light.iloc[0]] for m in counts.index]
    fig = go.Figure(go.Bar(x=counts.to_numpy(), y=counts.index, orientation="h",
                           marker_color=colour))
    return _layout(fig, height=360, xaxis_title="compressions",
                   title="One message at a time - and this is the one it chose")


def fig_metronome(comp):
    fig = go.Figure()
    fig.add_hrect(y0=RATE_MIN, y1=RATE_MAX, fillcolor=GREEN, opacity=0.16, line_width=0,
                  annotation_text=f"guideline {RATE_MIN}-{RATE_MAX}",
                  annotation_font_color="white")
    fig.add_scatter(x=comp.t, y=comp.rate_cpm, name="the helper's actual rate",
                    line=dict(color=CYAN, width=1.2))
    fig.add_scatter(x=comp.t, y=comp.beat_cpm, name="the beat the unit plays",
                    line=dict(color=AMBER, width=3))
    _mark_pauses(fig)
    return _layout(fig, height=380, xaxis_title="seconds into the rescue",
                   yaxis_title="compressions per minute",
                   title="The beat leads, the helper follows")


def fig_fatigue(comp, depth_min, depth_max):
    panels = [("depth_roll", "Watching peak depth", "tiring_by_depth"),
              ("stroke_roll", "Watching the stroke", "tiring")]
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True,
                        subplot_titles=[p[1] for p in panels])
    for i, (col, _, flag) in enumerate(panels, 1):
        for who, colour in (("A", RED), ("B", CYAN)):
            part = comp[comp.rescuer == who]
            fig.add_scatter(x=part.t, y=part[col], line=dict(color=colour, width=3),
                            name=f"rescuer {who}", showlegend=(i == 1), row=1, col=i)
        fig.add_hrect(y0=depth_min, y1=depth_max, fillcolor=GREEN, opacity=0.14,
                      line_width=0, row=1, col=i)
        fired = comp[comp[flag]]
        if len(fired):
            fig.add_vline(x=fired.t.iloc[0], line_dash="dash", line_color=AMBER, row=1, col=i)
            fig.add_annotation(x=fired.t.iloc[0], y=1.0, yref="y domain", row=1, col=i,
                               text=f"caught at {fired.t.iloc[0]:.0f} s", showarrow=False,
                               font=dict(color=AMBER, size=11), xanchor="right")
        else:
            fig.add_annotation(x=0.5, y=0.06, xref="x domain", yref="y domain", row=1, col=i,
                               text="never fired", showarrow=False, font=dict(color=GREY, size=13))
        fig.update_xaxes(title_text="seconds", row=1, col=i)
    fig.update_yaxes(title_text="centimetres", row=1, col=1)
    return _layout(fig, height=410, top=95,
                   title="The same fatigue, and the two detectors that were tried on it")


def fig_ccf(compressing, hands_on):
    """A strip of the whole rescue: hands on, hands off."""
    t = np.arange(0, RESCUE_SECONDS, 1 / FS)
    fig = go.Figure()
    edges = np.flatnonzero(np.diff(compressing.astype(int))) + 1
    for a, b in zip(np.concatenate([[0], edges]), np.concatenate([edges, [len(t)]])):
        on = bool(compressing[a])
        fig.add_bar(x=[(b - a) / FS], y=["the rescue"], base=[a / FS], orientation="h",
                    marker_color=GREEN if on else RED, showlegend=False,
                    hovertemplate=("hands on" if on else "hands off")
                    + " · %{base:.0f}-%{x:.0f} s<extra></extra>")
    fig.update_xaxes(range=[0, RESCUE_SECONDS])
    return _layout(fig, height=230, barmode="stack", xaxis_title="seconds into the rescue",
                   title=f"Hands on the chest for {hands_on:.0f} of {RESCUE_SECONDS} seconds")


def fig_timeline(comp, depth_min, depth_max):
    fig = make_subplots(rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.035,
                        row_heights=[0.26, 0.22, 0.22, 0.18, 0.12],
                        specs=[[{}], [{}], [{"secondary_y": True}], [{}], [{}]])

    fig.add_scatter(x=comp.t, y=comp.depth_cm, mode="markers", showlegend=False, row=1, col=1,
                    marker=dict(size=5, color=[LIGHT[c] for c in comp.light]), name="depth")
    fig.add_scatter(x=comp.t, y=comp.depth_roll, line=dict(color="white", width=2),
                    showlegend=False, row=1, col=1)
    fig.add_hrect(y0=depth_min, y1=depth_max, fillcolor=GREEN, opacity=0.16, line_width=0,
                  row=1, col=1)

    fig.add_scatter(x=comp.t, y=comp.rate_cpm, line=dict(color=GREY, width=1),
                    showlegend=False, row=2, col=1)
    fig.add_scatter(x=comp.t, y=comp.beat_cpm, line=dict(color=AMBER, width=2, dash="dash"),
                    showlegend=False, row=2, col=1)
    fig.add_hrect(y0=RATE_MIN, y1=RATE_MAX, fillcolor=GREEN, opacity=0.16, line_width=0,
                  row=2, col=1)

    fig.add_scatter(x=comp.t, y=comp.residual_cm, fill="tozeroy", line=dict(color=CYAN, width=1),
                    showlegend=False, row=3, col=1)
    fig.add_hline(y=RECOIL_MAX, line_dash="dot", line_color=RED, row=3, col=1)
    # its own axis, not the lean scale - a shifted curve on a borrowed axis lies
    fig.add_scatter(x=comp.t, y=comp.stroke_roll, line=dict(color=TEAL, width=2),
                    showlegend=False, row=3, col=1, secondary_y=True)

    fig.add_scatter(x=comp.t, y=comp.elbow_deg, line=dict(color=VIOLET, width=2),
                    showlegend=False, row=4, col=1)
    fig.add_hline(y=ELBOW_MIN, line_dash="dot", line_color=RED, row=4, col=1)

    fig.add_scatter(x=comp.t, y=np.zeros(len(comp)), mode="markers", showlegend=False,
                    row=5, col=1, marker=dict(size=9, symbol="square",
                                              color=[LIGHT[c] for c in comp.light]))
    for r in range(1, 6):
        _mark_pauses(fig, row=r)
    fig.update_yaxes(title_text="depth (cm)", row=1, col=1)
    fig.update_yaxes(title_text="rate /min", row=2, col=1)
    fig.update_yaxes(title_text="lean (cm)", row=3, col=1, secondary_y=False)
    fig.update_yaxes(title_text="stroke (cm)", row=3, col=1, secondary_y=True,
                     showgrid=False, color=TEAL)
    fig.update_yaxes(title_text="elbow (°)", row=4, col=1)
    fig.update_yaxes(title_text="light", showticklabels=False, row=5, col=1)
    fig.update_xaxes(title_text="seconds into the rescue", row=5, col=1)
    return _layout(fig, height=760, title="AI CPR Guardian - the session timeline")
