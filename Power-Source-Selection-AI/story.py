"""
The microgrid, as engineering — plus the narrative stages.
==========================================================
THE MICROGRID MODEL IS A COPY OF THE NOTEBOOK'S. Same tariff, same profiles,
same battery constants, same dynamic-programming optimiser — so a number quoted
in `Power_Source_Selection_AI.ipynb` and the same number on the matching app
page always agree. Change one and you must change both.

Narrative beats:
  microgrid - 06:00 on a campus microgrid, and a decision every 15 minutes.
  sources   - five sources, and what each really costs at each hour.
  reading   - one interval becomes one row.
  engine    - the product: one recommendation, with its reason.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

import scaffold as S

POS, NEG = S.POS, S.NEG
GREEN, AMBER, RED = S.GREEN, S.AMBER, S.RED
TECH, MUTED, TEXT, PANEL = S.TECH, S.MUTED, S.TEXT, S.PANEL
style, animate = S.style, S.animate

# --- the microgrid, as engineering ------------------------------------------
DT = 0.25               # hours per interval
STEPS = 96              # intervals per day
PV_KW = 400.0           # solar array peak
WT_KW = 250.0           # wind turbine rating
CAP_KWH = 500.0         # battery energy capacity
P_BAT = 200.0           # battery power limit, charge or discharge
SOC_MIN = 20.0          # never go below — warranty and reserve
SOC_MAX = 95.0
ETA_C = 0.9487          # charge efficiency    (0.90 round trip, split evenly)
ETA_D = 0.9487          # discharge efficiency
DEGRADE = 1.20          # Rs/kWh of battery throughput — a cycle is NOT free
DIESEL_KW = 300.0
DIESEL_RS = 21.0        # Rs/kWh — fuel plus O&M
VOLL = 500.0            # Rs/kWh value of lost load

CLASSES = ["RENEWABLE", "RENEWABLE + BATTERY", "RENEWABLE + GRID", "GRID + CHARGE", "DIESEL"]
CLASS_COL = {"RENEWABLE": "#ffd54f", "RENEWABLE + BATTERY": "#66bb6a",
             "RENEWABLE + GRID": "#4fc3f7", "GRID + CHARGE": "#7986cb", "DIESEL": "#ef5350"}


def tariff(hour):
    """Industrial time-of-use tariff, Rs/kWh."""
    h = np.asarray(hour, float) % 24
    p = np.full(h.shape, 8.00)                  # normal
    p[(h >= 22) | (h < 6)] = 4.50               # off-peak
    p[(h >= 18) & (h < 22)] = 11.50             # evening peak
    return p


def solar_profile(hour, cloud=1.0):
    """Clear-sky bell curve between about 06:30 and 18:30, scaled by cloud."""
    h = np.asarray(hour, float)
    x = np.clip((h - 6.5) / 12.0, 0, 1)
    return PV_KW * np.where((h > 6.5) & (h < 18.5), np.sin(np.pi * x) ** 1.3, 0.0) * cloud


def demand_profile(hour, weekend, rng=None):
    """Campus load: a night baseline plus a day shift, smaller at the weekend."""
    h = np.asarray(hour, float)
    shift = np.exp(-((h - 13.0) ** 2) / (2 * 3.4 ** 2))
    lunch = 0.18 * np.exp(-((h - 13.2) ** 2) / (2 * 0.5 ** 2))
    base = 150.0 + 300.0 * (shift - lunch) * (0.45 if weekend else 1.0)
    return np.maximum(base, 110.0)


def rule_decision(net, soc, price, gridok, price_max4):
    """The myopic controller a plant engineer would write. It sees only this interval."""
    if not gridok:
        return "RENEWABLE + BATTERY" if (soc > SOC_MIN + 12 and net > 0) else (
            "DIESEL" if net > 0 else "RENEWABLE")
    if net <= 0:
        return "RENEWABLE"                           # surplus: store it
    if price >= 11.0 and soc > 40:
        return "RENEWABLE + BATTERY"                 # peak: use the battery
    if price <= 5.0 and soc < 80:
        return "GRID + CHARGE"                       # off-peak: fill up
    return "RENEWABLE + GRID"


# ---- the perfect-foresight optimiser (backward dynamic programming) ---------
SOC_LEVELS = np.linspace(SOC_MIN, SOC_MAX, 61)       # 1.25 % steps
SOC_STEP = SOC_LEVELS[1] - SOC_LEVELS[0]
ACTIONS = np.linspace(-P_BAT, P_BAT, 17)             # kW, positive = discharge

_d = np.where(ACTIONS > 0, -(ACTIONS * DT / ETA_D) / CAP_KWH * 100.0,
              -(ACTIONS * DT * ETA_C) / CAP_KWH * 100.0)
_new = SOC_LEVELS[:, None] + _d[None, :]
_ok = (_new >= SOC_MIN - 1e-9) & (_new <= SOC_MAX + 1e-9)
_idx = np.clip(np.round((_new - SOC_MIN) / SOC_STEP).astype(int), 0, len(SOC_LEVELS) - 1)


def interval_cost(net, price, gridok):
    """Cost of every candidate battery action in one interval, Rs."""
    supply = net - ACTIONS                      # what still has to come from somewhere
    need = np.maximum(supply, 0.0)
    if gridok:
        grid, dies = need, np.zeros_like(need)
    else:
        grid, dies = np.zeros_like(need), np.minimum(need, DIESEL_KW)
    unserved = need - grid - dies
    cost = (grid * price + dies * DIESEL_RS + unserved * VOLL) * DT \
        + np.abs(ACTIONS) * DT * DEGRADE
    return cost, grid, dies


def solve_day(net, price, gridok, soc0=55.0):
    """Exact cheapest dispatch for one whole day, by backward dynamic programming.

    This is not an opinion: given the whole day in advance it is the provably
    cheapest schedule. It is also impossible in real time — which is the point.
    """
    T = len(net)
    V = np.zeros((T + 1, len(SOC_LEVELS)))
    POL = np.zeros((T, len(SOC_LEVELS)), dtype=int)
    for t in range(T - 1, -1, -1):
        c, _, _ = interval_cost(net[t], price[t], bool(gridok[t]))
        tot = np.where(_ok, c[None, :] + V[t + 1][_idx], np.inf)
        POL[t] = np.argmin(tot, axis=1)
        V[t] = tot[np.arange(len(SOC_LEVELS)), POL[t]]

    s = int(np.clip(round((soc0 - SOC_MIN) / SOC_STEP), 0, len(SOC_LEVELS) - 1))
    out = []
    for t in range(T):
        a = POL[t, s]
        c, g, dsl = interval_cost(net[t], price[t], bool(gridok[t]))
        out.append(dict(bat_kw=ACTIONS[a], grid_kw=g[a], diesel_kw=dsl[a],
                        cost=c[a], soc=SOC_LEVELS[s]))
        s = _idx[s, a]
    return pd.DataFrame(out)


def label_of(bat_kw, grid_kw, diesel_kw):
    """Turn a dispatch into one of the five decision classes."""
    if diesel_kw > 1.0:
        return "DIESEL"
    if bat_kw < -1.0 and grid_kw > 1.0:
        return "GRID + CHARGE"
    if bat_kw > 1.0:
        return "RENEWABLE + BATTERY"
    if grid_kw > 1.0:
        return "RENEWABLE + GRID"
    return "RENEWABLE"


def dispatch_cost(action_class, net, soc, price, gridok):
    """What one interval actually costs if this class is chosen, and the new SOC.

    Decision accuracy is the wrong score for this problem: two classes can cost
    almost the same in one interval and wildly different amounts in another.
    This function is what the closed-loop pages score on instead.
    """
    bat = 0.0
    if action_class == "RENEWABLE + BATTERY":
        bat = min(P_BAT, max(net, 0.0))
        bat = bat if soc > SOC_MIN + 1 else 0.0
    elif action_class == "GRID + CHARGE":
        bat = -min(P_BAT, max(CAP_KWH * (SOC_MAX - soc) / 100.0 / DT, 0.0))
    elif action_class == "RENEWABLE":
        bat = -min(P_BAT, max(-net, 0.0)) if net < 0 else 0.0

    need = max(net - bat, 0.0)
    if action_class == "DIESEL" or not gridok:
        dies = min(need, DIESEL_KW); grid = 0.0
    else:
        grid = need; dies = 0.0
    unserved = max(need - grid - dies, 0.0)
    cost = (grid * price + dies * DIESEL_RS + unserved * VOLL) * DT + abs(bat) * DT * DEGRADE

    dsoc = (-(bat * DT / ETA_D) if bat > 0 else -(bat * DT * ETA_C)) / CAP_KWH * 100.0
    return float(cost), float(np.clip(soc + dsoc, SOC_MIN, SOC_MAX)), float(unserved)


# ================================================================ 1 · the microgrid
def render_microgrid():
    st.title("06:00 on the campus microgrid")
    st.markdown("#### Five ways to supply the next fifteen minutes. One of them is cheapest.")
    st.caption("The same kilowatt-hour is worth two and a half times as much at 19:00 as at 03:00. "
               "Everything here follows from that.")
    st.write("")

    hours = np.arange(0, 24, DT)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hours, y=tariff(hours), mode="lines", line_shape="hv",
                             line=dict(color=POS, width=3), fill="tozeroy", name="grid tariff"))
    fig.add_hline(y=DIESEL_RS, line=dict(color=RED, width=2.5),
                  annotation_text=f"diesel — {DIESEL_RS:.0f} Rs/kWh, all day")
    fig.update_layout(title="the tariff the engineer is deciding against")
    fig.update_xaxes(title="hour of day"); fig.update_yaxes(title="Rs / kWh", range=[0, 24])
    style(fig, 340); animate(fig, S.line_grow(hours, tariff(hours), POS), ms=45)
    st.plotly_chart(fig, use_container_width=True)
    st.write("")

    weekend = st.toggle("Weekend", value=False)
    cloud = st.slider("Cloud factor", 0.15, 1.0, 0.85, 0.05)
    wind = st.slider("Wind output (kW)", 0.0, WT_KW, 90.0, 5.0)

    dem = demand_profile(hours, weekend)
    sol = solar_profile(hours, cloud)
    net = dem - sol - wind

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=hours, y=dem, mode="lines", name="demand",
                              line=dict(color=TEXT, width=2.5)))
    fig2.add_trace(go.Scatter(x=hours, y=sol, mode="lines", name="solar",
                              line=dict(color="#ffd54f", width=2.5)))
    fig2.add_trace(go.Scatter(x=hours, y=np.full_like(hours, wind), mode="lines", name="wind",
                              line=dict(color="#4dd0e1", width=2, dash="dot")))
    fig2.update_layout(title="a day on the campus microgrid")
    fig2.update_xaxes(title="hour of day"); fig2.update_yaxes(title="kW")
    st.plotly_chart(style(fig2, 330), use_container_width=True)

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=hours, y=net, mode="lines", line=dict(color=TEXT, width=2.5),
                              name="net load"))
    fig3.add_trace(go.Scatter(x=hours, y=np.where(net > 0, net, 0), fill="tozeroy",
                              mode="none", fillcolor="rgba(239,83,80,0.30)",
                              name="must be bought or discharged"))
    fig3.add_trace(go.Scatter(x=hours, y=np.where(net <= 0, net, 0), fill="tozeroy",
                              mode="none", fillcolor="rgba(102,187,106,0.35)",
                              name="surplus — store it"))
    fig3.add_hline(y=0, line=dict(color=MUTED, width=1))
    fig3.add_vrect(x0=18, x1=22, fillcolor=RED, opacity=0.10, line_width=0,
                   annotation_text="evening peak", annotation_position="top left")
    fig3.update_layout(title="net load = demand − solar − wind: the number the decision is about")
    fig3.update_xaxes(title="hour of day"); fig3.update_yaxes(title="net load (kW)")
    st.plotly_chart(style(fig3, 340), use_container_width=True)

    surplus_h = float(np.sum(net < 0) * DT)
    c = st.columns(3)
    c[0].metric("Hours of surplus", f"{surplus_h:.1f} h")
    c[1].metric("Peak net load", f"{net.max():.0f} kW")
    c[2].metric("Decisions per day", STEPS)
    st.write("")

    st.markdown("### So — can the engineer just decide each time?")
    if st.button("Answer", type="primary"):
        st.error(f"**{STEPS} decisions a day, every day.** Each one depends on the price now, the price in "
                 f"four hours, the state of charge, the forecast and whether the grid is up. Nobody makes "
                 f"that call correctly 35,000 times a year.")
        st.info("👉 Note where the surplus sits (midday) and where the expensive hours sit (18:00–22:00). "
                "**They do not overlap.** That gap is the entire business case for the battery — and "
                "exploiting it means deciding now for a price four hours from now.")


# ================================================================ 2 · five sources
def render_sources():
    st.title("Five sources, and what each one really costs")
    st.markdown("#### A battery is not a backup device. It is a way of moving energy between hours.")
    st.write("")

    charge_price = st.slider("Price the battery was charged at (Rs/kWh)", 4.0, 12.0, 4.50, 0.25)
    hours = np.arange(0, 24, DT)
    batt_cost = charge_price / (ETA_C * ETA_D) + DEGRADE

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hours, y=tariff(hours), mode="lines", line_shape="hv",
                             line=dict(color=POS, width=3), name="grid (time-of-use)"))
    fig.add_hline(y=DIESEL_RS, line=dict(color=RED, width=2.5),
                  annotation_text=f"diesel {DIESEL_RS:.0f}")
    fig.add_hline(y=batt_cost, line=dict(color=GREEN, width=2.5, dash="dash"),
                  annotation_text=f"battery {batt_cost:.2f}")
    fig.add_hline(y=0.0, line=dict(color="#ffd54f", width=2.5),
                  annotation_text="solar / wind 0.00", annotation_position="bottom left")
    fig.update_layout(title="what one kilowatt-hour costs, from each source, at each hour")
    fig.update_xaxes(title="hour of day"); fig.update_yaxes(title="Rs / kWh", range=[-1, 24])
    st.plotly_chart(style(fig, 400), use_container_width=True)
    st.write("")

    st.dataframe(pd.DataFrame([
        ["☀️ Solar", "0.00", "Free once built — but only when the sun is up, and never at the peak"],
        ["💨 Wind", "0.00", "Free once built — but not controllable, and often absent when needed"],
        ["🔋 Battery", f"{batt_cost:.2f}",
         f"The energy that charged it ÷ {ETA_C*ETA_D:.0%} round-trip efficiency, PLUS "
         f"{DEGRADE:.2f} Rs/kWh of wear. A cycle is never free."],
        ["🔌 Grid", "4.50 / 8.00 / 11.50", "Cheapest at night, most expensive exactly when demand peaks"],
        ["🛢️ Diesel", f"{DIESEL_RS:.2f}", "Always available, always expensive — it exists for outages"],
    ], columns=["Source", "Rs/kWh", "What that number hides"]),
        use_container_width=True, hide_index=True)
    st.write("")

    st.info(f"**Read the battery line carefully.** Charged at off-peak {4.50:.2f} it delivers at "
            f"{4.50/(ETA_C*ETA_D)+DEGRADE:.2f} — clearly worth it against an 11.50 peak. Charged at the "
            f"normal 8.00 rate it delivers at {8.0/(ETA_C*ETA_D)+DEGRADE:.2f}, and the saving nearly "
            f"vanishes. **Drag the slider up and watch the battery line cross the peak tariff.** Past that "
            f"point, discharging loses money.")
    st.success("That is why this cannot be a simple rule. Whether the battery should discharge depends on "
               "what it cost to fill — which happened hours ago.")


# ================================================================ 3 · one interval
def render_reading(get_data):
    st.title("One interval — how a microgrid's state becomes data")
    st.markdown("#### The model will never walk into the plant room.")
    d = get_data()
    st.write("")

    steps = [
        ("⚡  The real microgrid", "Panels generate, the turbine turns, the campus draws, the battery sits "
                                   "at some state of charge. All of it at once.", MUTED),
        ("📟  Meters read it", "Demand, solar, wind, state of charge, tariff, grid availability, "
                               "temperature — each one number.", POS),
        ("🔭  Forecasts are added", "The published tariff for the next four hours, and an *imperfect* "
                                    "solar forecast for the next two.", AMBER),
        ("📄  It becomes one row", "This row is the *entire* microgrid as far as the model is concerned — "
                                   "and the decision has to come out of it.", GREEN),
    ]
    i = st.slider("Walk through the interval", 1, 4, 1)
    for k, (t, txt, c) in enumerate(steps, start=1):
        if k <= i:
            st.markdown(f"<div style='padding:12px 16px;margin:6px 0;border-radius:4px;"
                        f"border-left:4px solid {c};background:{PANEL};color:{TEXT}'>"
                        f"<b>{t}</b><br><span style='color:{MUTED}'>{txt}</span></div>",
                        unsafe_allow_html=True)
    if i == 4:
        st.write("")
        st.markdown("##### What each channel records, and why it matters")
        st.dataframe(pd.DataFrame([
            ["🏫 Demand", "Campus meter", "kW", "What has to be supplied, whatever it costs"],
            ["☀️ Solar", "Inverter", "kW", "Free energy, available only in the middle of the day"],
            ["💨 Wind", "Turbine SCADA", "kW", "Free energy, not controllable"],
            ["➖ Net load", "Computed", "kW", "demand − solar − wind: the number the decision is about"],
            ["🔋 State of charge", "BMS", "%", "How much stored energy there is, and how much room to store"],
            ["💷 Grid price now", "Published tariff", "Rs/kWh", "What buying costs this interval"],
            ["📈 Max price, next 4 h", "Published tariff", "Rs/kWh", "Why saving the battery can be right"],
            ["🔭 Solar forecast, next 2 h", "Weather service", "kW", "Imperfect — and still useful"],
            ["🕐 Hour (as sine & cosine)", "Clock", "—", "So 23:45 sits next to 00:00, not far from it"],
            ["🔌 Grid available", "Protection relay", "0/1", "During an outage the whole decision changes"],
        ], columns=["Channel", "Source", "Unit", "What it tells you"]),
            use_container_width=True, hide_index=True)
        st.write("")

        row = d["feat"].iloc[45]
        show = ["demand_kw", "solar_kw", "wind_kw", "net_load_kw", "battery_soc",
                "grid_price", "price_max_next4h", "solar_fc_next2h", "grid_available"]
        st.markdown("##### One interval = one row of those numbers")
        st.dataframe(pd.DataFrame([row[show].values], columns=[
            "Demand (kW)", "Solar (kW)", "Wind (kW)", "Net load (kW)", "SOC (%)",
            "Price now", "Max price 4 h", "Solar fc 2 h", "Grid up"]).round(1),
            use_container_width=True, hide_index=True)
        st.info("The model never walks into the plant room — it sees only this row. Two of those columns "
                "are about the *future*, and they are the reason a model can beat a rule that only sees "
                "the present.")


# ================================================================ 4 · the engine
def render_engine():
    st.title("The dispatch recommendation")
    st.markdown("#### One instruction per interval, with the reason attached.")
    st.caption("This is the product. Everything before it existed to fill in these rows.")
    st.write("")

    rows = [
        dict(t="19:15", cls="RENEWABLE + BATTERY", why="peak tariff 11.50, SOC 78% — discharge now",
             save="Rs 640 vs buying", pr="ACT"),
        dict(t="02:30", cls="GRID + CHARGE", why="off-peak 4.50, SOC 34%, peak in 16 h — fill up",
             save="Rs 410 banked for tonight", pr="ACT"),
        dict(t="12:45", cls="RENEWABLE", why="net load −180 kW, surplus — store it, buy nothing",
             save="Rs 0 spent", pr="HOLD"),
        dict(t="20:05", cls="DIESEL", why="grid down, SOC at floor 20% — the reserve is gone",
             save="Rs 1,260 — and no lost load", pr="ACT"),
    ]
    colr = {"ACT": GREEN, "HOLD": MUTED}
    for r in rows:
        st.markdown(
            f"<div style='background:{PANEL};border-left:5px solid {CLASS_COL[r['cls']]};"
            f"border-radius:4px;padding:14px 18px;margin:8px 0'>"
            f"<div style='display:flex;justify-content:space-between;align-items:baseline'>"
            f"<b style='color:{TEXT};font-size:17px'>{r['t']} &nbsp;·&nbsp; "
            f"<span style='color:{CLASS_COL[r['cls']]}'>{r['cls']}</span></b>"
            f"<span style='color:{colr[r['pr']]};font-size:12px;letter-spacing:.14em'>{r['pr']}</span>"
            f"</div><span style='color:{MUTED};font-size:14px'>🧭 {r['why']}</span><br>"
            f"<span style='color:{GREEN};font-size:15px'>▸ {r['save']}</span></div>",
            unsafe_allow_html=True)

    st.write("")
    st.divider()
    st.markdown("### Where each column came from")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div style='background:{PANEL};border-top:3px solid {POS};border-radius:4px;padding:14px;"
                f"height:100%'><b style='color:{POS}'>🎯 The class</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>A gradient-boosted tree over the thirteen "
                f"observable columns, trained on the optimiser's answers.</span></div>",
                unsafe_allow_html=True)
    c2.markdown(f"<div style='background:{PANEL};border-top:3px solid {TECH};border-radius:4px;padding:14px;"
                f"height:100%'><b style='color:{TECH}'>🧭 The reason</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>The decision path through the tree, read back "
                f"in plain language. This is the only column an engineer can argue with.</span></div>",
                unsafe_allow_html=True)
    c3.markdown(f"<div style='background:{PANEL};border-top:3px solid {GREEN};border-radius:4px;padding:14px;"
                f"height:100%'><b style='color:{GREEN}'>💷 The saving</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>The regret against the perfect-foresight "
                f"optimum — in rupees, not in accuracy points.</span></div>", unsafe_allow_html=True)
    st.write("")

    st.success("**A class on its own is not a recommendation.** The reason is what gets it accepted, and "
               "the rupee figure is what gets it funded.")
    st.info("Note what the screen does *not* do: it never opens a breaker by itself. Every row is a "
            "setpoint an operator can override, and the diesel row exists because the grid can fail.")
