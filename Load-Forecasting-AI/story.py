"""
Story stages for the Electricity Load Forecasting course.
=========================================================
The narrative beats that make AI inevitable for an Electrical / Power Systems
Engineering student who has never met it:

  control-room - a grid on a hot evening. Generation must follow demand, exactly.
  enter-ai     - operator + forecast. Not a replacement: 8,760 numbers a year.
  one-hour     - one metered hour. Reality BECOMES a row of numbers.
  drivers      - which driver moves the most megawatts? Measure, do not guess.
  cyclical     - the clock is a circle and the integer is a line.
  gate         - what is actually on the desk at 23:00. lag_1 dies here.
  persistence  - the method in use today, and the day it fails.
  despatch     - net load, the evening ramp, and the instruction that follows.

Everything is drawn with numpy + Plotly. No image assets and no trained model
in this file except where one is passed in.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BG, PANEL = "#0b0f14", "#131a22"
CYAN, AMBER = "#4fc3f7", "#ffb74d"
GREEN, RED, TECH = "#66bb6a", "#ef5350", "#ba68c8"
MUTED, TEXT = "#8b98a9", "#e6edf3"

COOL_BASE, HEAT_BASE = 24.0, 16.0

# ---- the generation fleet, as an operating policy (shared with the dashboard)
MUST_RUN = 430.0        # MW    - minimum stable generation overnight
PEAK_TRIGGER = 900.0    # MW    - above this, peaking units to standby
RAMP_LIMIT = 45.0       # MW/h  - what committed plant can follow unaided
SOLAR_MW = 220.0        # MW    - installed solar capacity


def solar_output(hour, month=8):
    "Assumed clear-sky solar contribution, MW."
    h = np.asarray(hour, float)
    seasonal = 0.75 + 0.25 * np.sin(2 * np.pi * (month - 4) / 12)
    return SOLAR_MW * np.clip(np.sin(np.pi * (h - 6.5) / 11.0), 0, None) * seasonal


def despatch(forecast_mw, net_mw, ramp_mw, hour):
    "Return (instruction, reason). Operating policy, not a model."
    if net_mw > PEAK_TRIGGER:
        return ("PREPARE PEAK LOAD UNITS",
                f"net load {net_mw:,.0f} MW exceeds the {PEAK_TRIGGER:,.0f} MW committed-plant "
                f"trigger — bring peaking units to standby now")
    if ramp_mw > RAMP_LIMIT:
        return ("INCREASE GENERATION CAPACITY",
                f"net load rising {ramp_mw:,.0f} MW/h, above the {RAMP_LIMIT:,.0f} MW/h that "
                f"committed plant can follow — schedule additional ramping capacity")
    if net_mw < MUST_RUN:
        return ("CHARGE ENERGY STORAGE",
                f"net load {net_mw:,.0f} MW is below the {MUST_RUN:,.0f} MW must-run minimum — "
                f"absorb the surplus rather than backing plant down")
    if net_mw < MUST_RUN * 1.12 and solar_output(hour) > 60:
        return ("REDUCE RENEWABLE CURTAILMENT",
                f"solar contributing {solar_output(hour):,.0f} MW into a light net load — shift "
                f"flexible demand into this window instead of curtailing")
    return ("MAINTAIN CURRENT GENERATION",
            f"net load {net_mw:,.0f} MW and ramp {ramp_mw:+,.0f} MW/h are both inside "
            f"committed-plant limits")


def hour_spans(hrs):
    "Collapse a sorted hour list into contiguous runs: [0,1,2,7] -> 00:00-02:00, 07:00"
    if not hrs:
        return "—"
    runs, start, prev = [], hrs[0], hrs[0]
    for h in list(hrs[1:]) + [None]:
        if h != prev + 1:
            runs.append(f"{start:02d}:00" if start == prev else f"{start:02d}:00–{prev:02d}:00")
            start = h
        prev = h
    return ", ".join(runs)


# ================================================================ 1 · the grid
def render_control_room(demand_for, style, animate):
    st.markdown("#### Generation must equal demand — every second, with no buffer")
    st.caption("Move the slider to walk through the day. The mimic diagram shows what the network is "
               "doing at that hour; the curve below shows the whole day it belongs to.")

    c = st.columns(3)
    season = c[0].radio("Day", ["Hot August weekday", "Cool January weekday"], horizontal=False)
    hour = c[1].slider("Hour of day", 0, 23, 19)
    daytype = c[2].radio("Day type", ["Weekday", "Sunday"], horizontal=False)

    hours = np.arange(24)
    if season.startswith("Hot"):
        T = 37.5 - 5.5 * np.cos(2 * np.pi * (hours - 4) / 24)
        H = np.full(24, 74.0)
    else:
        T = 16.5 - 5.5 * np.cos(2 * np.pi * (hours - 4) / 24)
        H = np.full(24, 40.0)
    dow = 6 if daytype == "Sunday" else 0
    d = demand_for(hours, T, H, dow, 0, 1.6)
    now = float(d[hour])

    # ---------------------------------------------------------- mimic diagram
    fig = go.Figure()
    stations = [("⚛️", "Baseload", 0.55), ("🔥", "Thermal", 0.28), ("☀️", "Solar", 0.10),
                ("💨", "Wind", 0.07)]
    ys = [3.6, 2.6, 1.6, 0.6]
    for (icon, name, share), y in zip(stations, ys):
        mw = now * share
        fig.add_shape(type="rect", x0=0.1, x1=1.9, y0=y - 0.32, y1=y + 0.32,
                      line=dict(color="#25313d", width=1), fillcolor="#101820", layer="below")
        fig.add_shape(type="line", x0=0.1, y0=y - 0.32, x1=0.1, y1=y + 0.32,
                      line=dict(color=AMBER, width=3), layer="above")
        fig.add_annotation(x=0.3, y=y, text=f"{icon} {name}", showarrow=False, xanchor="left",
                           font=dict(size=12, color=TEXT))
        fig.add_annotation(x=1.8, y=y, text=f"{mw:,.0f} MW", showarrow=False, xanchor="right",
                           font=dict(size=12, color=AMBER, family="monospace"))
        fig.add_annotation(x=3.0, y=y, ax=1.95, ay=y, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.6,
                           arrowcolor="#33424f", text="")

    # the busbar
    fig.add_shape(type="rect", x0=3.0, x1=3.25, y0=0.3, y1=3.9,
                  line=dict(color=AMBER, width=2), fillcolor="#2a2214", layer="below")
    fig.add_annotation(x=3.13, y=4.15, text="<b>400 kV BUS</b>", showarrow=False,
                       font=dict(size=11, color=AMBER, family="monospace"))

    fig.add_annotation(x=5.4, y=2.1, ax=3.3, ay=2.1, xref="x", yref="y", axref="x", ayref="y",
                       showarrow=True, arrowhead=2, arrowsize=1.4, arrowwidth=3,
                       arrowcolor=CYAN, text="")
    fig.add_annotation(x=4.35, y=2.45, text="TRANSMISSION", showarrow=False,
                       font=dict(size=10, color=MUTED, family="monospace"))

    loads = [("🏠", "Residential", 0.46), ("🏢", "Commercial", 0.31), ("🏭", "Industrial", 0.23)]
    for (icon, name, share), y in zip(loads, [3.2, 2.1, 1.0]):
        mw = now * share
        fig.add_shape(type="rect", x0=5.5, x1=7.4, y0=y - 0.32, y1=y + 0.32,
                      line=dict(color="#25313d", width=1), fillcolor="#101820", layer="below")
        fig.add_shape(type="line", x0=7.4, y0=y - 0.32, x1=7.4, y1=y + 0.32,
                      line=dict(color=CYAN, width=3), layer="above")
        fig.add_annotation(x=5.7, y=y, text=f"{icon} {name}", showarrow=False, xanchor="left",
                           font=dict(size=12, color=TEXT))
        fig.add_annotation(x=7.3, y=y, text=f"{mw:,.0f} MW", showarrow=False, xanchor="right",
                           font=dict(size=12, color=CYAN, family="monospace"))
        fig.add_annotation(x=5.45, y=y, ax=5.42, ay=2.1, xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=0.9, arrowwidth=1.4,
                           arrowcolor="#33424f", text="")

    fig.add_annotation(x=4.35, y=0.35,
                       text=f"<b>GENERATION {now:,.0f} MW  ≡  DEMAND {now:,.0f} MW</b>",
                       showarrow=False, font=dict(size=13, color=GREEN, family="monospace"))
    fig.add_annotation(x=4.35, y=0.02, text="50.00 Hz — the balance, as the network reports it",
                       showarrow=False, font=dict(size=10, color=MUTED))
    fig.update_xaxes(visible=False, range=[0, 7.7])
    fig.update_yaxes(visible=False, range=[-0.2, 4.5])
    st.plotly_chart(style(fig, 420), use_container_width=True)

    # ---------------------------------------------------------- the day curve
    ramp = np.diff(d, prepend=d[0])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hours, y=d, mode="lines", line=dict(color=CYAN, width=3),
                             name="system demand"))
    fig.add_trace(go.Scatter(x=[hour], y=[now], mode="markers",
                             marker=dict(size=18, color=AMBER, line=dict(color=TEXT, width=2)),
                             name="the hour above"))
    frames = [go.Frame(data=[go.Scatter(x=hours, y=d, mode="lines",
                                        line=dict(color=CYAN, width=3)),
                             go.Scatter(x=[h], y=[d[h]], mode="markers",
                                        marker=dict(size=18, color=AMBER,
                                                    line=dict(color=TEXT, width=2)))])
              for h in range(24)]
    animate(fig, frames, ms=220)
    fig.update_layout(title=f"{season} — the load curve the generators have to follow",
                      xaxis_title="hour of day", yaxis_title="system demand (MW)")
    st.plotly_chart(style(fig, 400), use_container_width=True)

    c = st.columns(4)
    c[0].metric("Peak", f"{d.max():,.0f} MW", f"at {int(d.argmax()):02d}:00")
    c[1].metric("Trough", f"{d.min():,.0f} MW", f"at {int(d.argmin()):02d}:00")
    c[2].metric("Peak-to-trough swing", f"{d.max()-d.min():,.0f} MW",
                f"{d.max()/d.min():.2f}× ratio")
    c[3].metric("Steepest ramp", f"{ramp.max():,.0f} MW/h",
                f"hour ending {int(ramp.argmax()):02d}:00")

    st.error(f"**That steepest ramp is the problem.** {ramp.max():,.0f} MW called for in sixty minutes "
             f"is an entire mid-size generating unit. A large thermal unit takes **six to twelve hours "
             f"to synchronise** — so the decision to start it was taken last night, against a demand "
             f"nobody had measured yet.")
    st.info("Compare the two days with the radio button. Same network, same consumers, same calendar "
            "position in the week — and hundreds of megawatts apart, entirely because of the weather.")


# ================================================================ 2 · operator + AI
def render_enter_ai(style):
    st.markdown("#### Nothing about the control room changes")
    st.caption("Same operators, same despatch instructions, same statutory responsibility for "
               "security of supply. What changes is that a number is on the desk before it is needed.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"<div class='mimic' style='height:100%'>"
            f"<b style='color:{AMBER}'>WHAT THE OPERATOR BRINGS</b><br>"
            f"<span class='muted'>Things no model in this course can see.</span><br><br>"
            f"› a substation on planned outage<br>"
            f"› a large industrial consumer's shutdown notice<br>"
            f"› a cyclone warning and the evacuation that follows<br>"
            f"› a plant tripping without warning<br>"
            f"› <b>statutory accountability for security of supply</b>"
            f"</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(
            f"<div class='mimic ai' style='height:100%'>"
            f"<b style='color:{CYAN}'>WHAT THE MODEL BRINGS</b><br>"
            f"<span class='muted'>Things one person cannot do 8,760 times a year.</span><br><br>"
            f"› a forecast for every hour, none of them skipped<br>"
            f"› every driver weighted at once, consistently<br>"
            f"› the same answer at 03:00 as at 15:00<br>"
            f"› no fatigue, no optimism, no bad week<br>"
            f"› <b>an error bar that becomes a reserve requirement</b>"
            f"</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown("##### The size of the task")
    per_day = st.slider("Forecasts issued per day", 1, 48, 24,
                        help="One per hour of tomorrow is the standard day-ahead product")
    feeders = st.slider("Feeders forecast separately", 1, 200, 1,
                        help="Aggregate system demand is one series. A distribution utility has many.")
    total = per_day * 365 * feeders
    c = st.columns(3)
    c[0].metric("Forecasts per year", f"{total:,}")
    c[1].metric("At 2 minutes of thought each", f"{total*2/60:,.0f} hours")
    c[2].metric("Full-time engineers to do it by hand", f"{total*2/60/1800:.1f}")

    fig = go.Figure(go.Bar(
        x=["By hand, 2 min each", "Working hours available (1 engineer)"],
        y=[total * 2 / 60, 1800],
        marker_color=[RED if total * 2 / 60 > 1800 else GREEN, MUTED],
        text=[f"{total*2/60:,.0f} h", "1,800 h"], textposition="outside"))
    fig.update_layout(title="Hours of work required against hours of engineer available, per year",
                      yaxis_title="hours per year")
    st.plotly_chart(style(fig, 360), use_container_width=True)

    st.success("**This fixes the role of AI for the whole course.** The model forecasts; the operator "
               "despatches. The system's output is a recommendation with a stated accuracy — never an "
               "automatic commitment. Every later design choice, especially the audit and the reserve "
               "calculation, follows from that split.")


# ================================================================ 3 · one hour
def render_one_hour(demand_for, daily_shape, cooling_mw, heating_mw, style):
    st.markdown("#### One metered hour, as the model receives it")
    c = st.columns(4)
    hour = c[0].slider("Hour", 0, 23, 19)
    temp = c[1].slider("Temperature (°C)", 8.0, 46.0, 38.4, 0.2)
    hum = c[2].slider("Humidity (%)", 20, 98, 71)
    dow = c[3].selectbox("Day", list(range(7)), index=0,
                         format_func=lambda i: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i])

    total = float(demand_for(hour, temp, hum, dow, 0, 1.6))
    shape = float(daily_shape(hour, dow >= 5))
    base = 620.0 * shape * (0.875 if dow == 6 else (0.945 if dow == 5 else 1.0)) * (1.035 ** 1.6)
    cool = float(cooling_mw(temp, hum)) * (0.80 + 0.20 * shape)
    heat = float(heating_mw(temp))

    row = pd.DataFrame([{
        "timestamp": "2024-08-19 " + f"{hour:02d}:00", "temperature_c": temp,
        "humidity_pct": hum, "hour": hour, "dayofweek": dow, "is_holiday": 0,
        "demand_mw": round(total, 1)}])
    st.dataframe(row, use_container_width=True, hide_index=True)
    st.caption("Five inputs known in advance, one target measured afterwards. That is the whole row.")

    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["relative", "relative", "relative", "total"],
        x=["Base load × shape", "Air conditioning", "Heating", "Total demand"],
        y=[base, cool, heat, 0],
        text=[f"{base:,.0f}", f"{cool:,.0f}", f"{heat:,.0f}", f"{total:,.0f}"],
        textposition="outside",
        connector={"line": {"color": "#33424f"}},
        increasing={"marker": {"color": AMBER}},
        totals={"marker": {"color": CYAN}}))
    fig.update_layout(title="Where that hour's demand comes from",
                      yaxis_title="MW")
    st.plotly_chart(style(fig, 420), use_container_width=True)

    c = st.columns(3)
    c[0].metric("Total demand", f"{total:,.0f} MW")
    c[1].metric("Weather-driven share", f"{(cool+heat)/total*100:.0f} %",
                "the part that moves between days")
    c[2].metric("Clock-driven share", f"{base/total*100:.0f} %", "the part that repeats")

    st.warning("**Whoever reads that row next year does not get the hour.** Not that it was the first "
               "genuinely hot evening of the season, not the cricket final that kept the city indoors. "
               "They get the numbers above. For a model that limitation is absolute — it never stands "
               "in the control room and cannot re-run the hour, so a wrong row produces a confident "
               "wrong forecast with nothing to flag it.")


# ================================================================ 4 · drivers
def render_drivers(demand_for, style):
    st.markdown("#### Sweep one driver at a time and measure the megawatts it moves")
    st.caption("Everything else is held at a reference condition. This is a sensitivity study — "
               "feature selection done before a single model exists.")

    c = st.columns(3)
    ref_hour = c[0].slider("Reference hour", 0, 23, 15)
    ref_T = c[1].slider("Reference temperature (°C)", 10.0, 44.0, 30.0, 0.5)
    ref_H = c[2].slider("Reference humidity (%)", 20, 95, 55)

    def d_at(hour=None, T=None, H=None, dow=2, hol=0):
        return float(demand_for(ref_hour if hour is None else hour,
                                ref_T if T is None else T,
                                ref_H if H is None else H, dow, hol))

    sweeps = {
        "Hour of day (00 → 19)": (d_at(hour=0), d_at(hour=19)),
        "Temperature (24 → 42 °C)": (d_at(T=24.0), d_at(T=42.0)),
        "Humidity (35 → 85 %) — on a 38 °C day": (d_at(T=38.0, H=35), d_at(T=38.0, H=85)),
        "Humidity (35 → 85 %) — on a 20 °C day": (d_at(T=20.0, H=35), d_at(T=20.0, H=85)),
        "Weekday → Sunday": (d_at(), d_at(dow=6)),
        "Weekday → public holiday": (d_at(), d_at(hol=1)),
    }
    names = list(sweeps)
    spans = [abs(hi - lo) for lo, hi in sweeps.values()]
    order = np.argsort(spans)

    fig = go.Figure(go.Bar(
        x=[spans[i] for i in order], y=[names[i] for i in order], orientation="h",
        marker_color=[AMBER if "Humidity" in names[i] else CYAN for i in order],
        text=[f"{spans[i]:.0f} MW" for i in order], textposition="outside"))
    fig.update_layout(title="Megawatts moved by each driver across its real operating range",
                      xaxis_title="change in system demand (MW)", margin=dict(l=290))
    st.plotly_chart(style(fig, 440), use_container_width=True)

    hot = spans[names.index("Humidity (35 → 85 %) — on a 38 °C day")]
    mild = spans[names.index("Humidity (35 → 85 %) — on a 20 °C day")]
    c = st.columns(2)
    c[0].metric("Humidity swing on a hot day", f"{hot:.0f} MW")
    c[1].metric("The same swing on a mild day", f"{mild:.0f} MW")
    st.error("**Look at those two rows.** The identical humidity change is worth a substantial number "
             "of megawatts when it is hot and essentially nothing when it is mild. A model that adds "
             "up its inputs independently — one coefficient per feature — cannot represent that. "
             "Hold on to it: it decides which model wins later.")


# ================================================================ 11 · cyclical
def render_cyclical(get_data, style, animate):
    st.markdown("#### The clock is a circle. The integer 0–23 is a line.")
    d = get_data()
    hm = d["clean"].groupby("hour").demand_mw.mean()

    c1, c2 = st.columns(2)
    a = c1.select_slider("First hour", options=list(range(24)), value=23,
                         format_func=lambda h: f"{h:02d}:00")
    b = c2.select_slider("Second hour", options=list(range(24)), value=0,
                         format_func=lambda h: f"{h:02d}:00")
    plain = abs(a - b)
    circ = float(np.hypot(np.sin(2*np.pi*a/24) - np.sin(2*np.pi*b/24),
                          np.cos(2*np.pi*a/24) - np.cos(2*np.pi*b/24)))
    true_gap = min(abs(a - b), 24 - abs(a - b))

    c = st.columns(3)
    c[0].metric("True distance in time", f"{true_gap} h")
    c[1].metric("As a plain integer", f"{plain:.0f}",
                "wrong" if abs(plain - true_gap) > 0.01 else "correct",
                delta_color="inverse" if abs(plain - true_gap) > 0.01 else "normal")
    c[2].metric("On the clock face", f"{circ:.2f}", "proportional to the true gap")

    ang = 2 * np.pi * hm.index / 24
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=np.sin(ang), y=np.cos(ang), mode="markers+text",
        text=[f"{h:02d}" for h in hm.index], textposition="top center",
        textfont=dict(size=10, color=TEXT),
        marker=dict(size=np.interp(hm.values, (hm.min(), hm.max()), (9, 30)),
                    color=hm.values, colorscale="Turbo", colorbar=dict(title="mean MW")),
        name="hours"))
    for h, col in [(a, AMBER), (b, GREEN)]:
        fig.add_trace(go.Scatter(x=[np.sin(2*np.pi*h/24)], y=[np.cos(2*np.pi*h/24)],
                                 mode="markers", marker=dict(size=26, color=col, opacity=0.45),
                                 showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[np.sin(2*np.pi*a/24), np.sin(2*np.pi*b/24)],
                             y=[np.cos(2*np.pi*a/24), np.cos(2*np.pi*b/24)],
                             mode="lines", line=dict(color=TEXT, width=2, dash="dot"),
                             showlegend=False, hoverinfo="skip"))
    fig.update_layout(title="The 24 hours placed on a circle — size and colour are mean demand",
                      xaxis=dict(title="hour_sin", scaleanchor="y", zeroline=True),
                      yaxis=dict(title="hour_cos", zeroline=True))
    st.plotly_chart(style(fig, 540), use_container_width=True)

    st.info("Set the sliders to **23:00 and 00:00**. As a plain integer they are 23 apart — the "
            "furthest of any two hours in the day. In time they are one hour apart, the closest. "
            "That false cliff sits exactly on the overnight trough the system passes through "
            "**every single night**.")
    st.success("The fix is to put the hour back on the circle it came from: `hour_sin` and `hour_cos`. "
               "Two numbers instead of one, and now midnight sits next to 23:00 exactly as it does in "
               "time. The same encoding is applied to the month, for the December–January boundary.")


# ================================================================ 14 · the gate
def render_gate(style):
    st.markdown("#### The forecast is issued at 23:00 tonight, for 00:00–23:00 tomorrow")
    issue = st.select_slider("Issue time tonight", options=list(range(18, 24)), value=23,
                             format_func=lambda h: f"{h:02d}:00")
    st.caption(f"At {issue:02d}:00 the latest measured demand is the hour ending {issue:02d}:00 today. "
               f"Target hour *h* of tomorrow is therefore {24-issue} + h hours away.")

    lags = [1, 2, 6, 24, 48, 168]
    hours = list(range(24))
    z = np.zeros((len(lags), 24))
    for li, L in enumerate(lags):
        for h in hours:
            ahead = (24 - issue) + h
            z[li, h] = 1 if L >= ahead else 0

    fig = go.Figure(go.Heatmap(
        z=z, x=[f"{h:02d}" for h in hours], y=[f"lag_{L}" for L in lags],
        colorscale=[[0, "#3d1f1f"], [1, "#14301f"]], showscale=False,
        text=[["known" if v else "NOT YET" for v in row] for row in z],
        texttemplate="%{text}", textfont=dict(size=9)))
    fig.update_layout(title="Which lag features actually exist when the forecast is issued",
                      xaxis_title="target hour of tomorrow", yaxis_title="")
    st.plotly_chart(style(fig, 380), use_container_width=True)

    surviving = [L for L in lags if all(L >= (24 - issue) + h for h in hours)]
    partial = [L for L in lags if L not in surviving and any(L >= (24 - issue) + h for h in hours)]
    c = st.columns(3)
    c[0].metric("Usable for all 24 hours", ", ".join(f"lag_{L}" for L in surviving) or "none")
    c[1].metric("Usable for only some hours", ", ".join(f"lag_{L}" for L in partial) or "none")
    c[2].metric("lag_1 covers", f"{int(z[0].sum())} of 24 hours")

    st.error("**A feature available for one hour in twenty-four is not a feature.** `lag_1` is the "
             "single most informative column in the entire dataset — and it is deleted from the "
             "day-ahead model, because at 23:00 tonight the 12:00 reading you would need to forecast "
             "13:00 tomorrow has not happened yet.")
    st.warning("Using it anyway is **data leakage**, and it is the most common way a forecasting "
               "project fails. The model scores brilliantly in the notebook and cannot be deployed, "
               "because in production the column is empty. The rule is arithmetic: lag `L` is usable "
               "only if `L` is at least the number of hours ahead.")
    st.success("**The day-ahead feature set: 16 columns**, every one of which would genuinely be on "
               "the desk tonight — seven calendar, four weather, five lag and rolling.")


# ================================================================ 17 · persistence
def render_persistence(get_data, metrics, style):
    d = get_data()
    te = d["test"]
    y = te["demand_mw"].values

    st.markdown("#### The method the utility uses today")
    st.caption("Take the same hour on a comparable recent day and adjust it by eye. On a stable "
               "system it works — which is exactly why it is the bar to clear.")

    rows = []
    for nm, p in [("Same hour yesterday", te.lag_24.values),
                  ("Same hour last week", te.lag_168.values),
                  ("Yesterday's mean, flat all day", te.roll24_lag24.values)]:
        rows.append(dict(method=nm, **metrics(y, p)))
    tbl = pd.DataFrame(rows).set_index("method").round(2)
    st.dataframe(tbl, use_container_width=True)

    c = st.columns(3)
    c[0].metric("Best naive MAE", f"{tbl.MAE.min():.1f} MW")
    c[1].metric("Best naive MAPE", f"{tbl.MAPE.min():.2f} %")
    c[2].metric("Hours scored", f"{len(te):,}")

    st.info("Note that **'same hour last week' beats 'same hour yesterday'.** The weekly rhythm of the "
            "network — a Tuesday resembling last Tuesday — is a stronger signal than yesterday, "
            "because yesterday might have been a Sunday. That is a real finding, and it is why "
            "`lag_168` earns its place in the feature set.")

    # ---- the day persistence fails ----------------------------------------
    t = te.copy()
    t["pers"] = t.lag_24
    t["err"] = t.pers - t.demand_mw
    daily = t.assign(dd=t.timestamp.dt.date).groupby("dd").agg(
        mae=("err", lambda s: s.abs().mean()), temp=("temperature_c", "mean"))
    worst = daily.mae.idxmax()
    day = t[t.timestamp.dt.date == worst]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=day.hour, y=day.demand_mw, name="actual demand",
                             line=dict(color=CYAN, width=3.5)))
    fig.add_trace(go.Scatter(x=day.hour, y=day.pers, name="persistence forecast",
                             line=dict(color=RED, width=2.5, dash="dash")))
    fig.update_layout(title=f"Persistence on its worst day in the test period — {worst}",
                      xaxis_title="hour of day", yaxis_title="demand (MW)")
    st.plotly_chart(style(fig, 400), use_container_width=True)

    prev = worst - pd.Timedelta(days=1)
    c = st.columns(3)
    c[0].metric("Error that day", f"{day.err.abs().mean():.0f} MW", "average across the day")
    c[1].metric("Worst single hour", f"{day.err.abs().max():.0f} MW")
    if prev in daily.index:
        c[2].metric("Temperature moved", f"{daily.loc[worst,'temp']-daily.loc[prev,'temp']:+.1f} °C",
                    "day on day")
    st.error("**Persistence has no mechanism for a weather change.** If today was 30 °C and tomorrow "
             "is 39 °C, yesterday's figure is simply wrong and nothing in the method can notice. It "
             "cannot handle a day-type change either — Monday is a poor guide to a public holiday.")
    st.success("This is the bar. Any model that does not beat these numbers is not worth deploying, "
               "whatever its R². Every accuracy figure later in this course is quoted against them, "
               "not against zero.")


# ================================================================ 31 · despatch
def render_despatch(test_frame, style, animate):
    st.markdown("#### A demand figure is not yet an instruction")
    st.caption("The control room acts on net load — demand minus what non-dispatchable generation "
               "contributes — and on the ramp, the rate at which that net load changes.")

    t = test_frame()
    days = sorted(t.timestamp.dt.date.unique())
    default = pd.Timestamp("2024-08-08").date()
    c = st.columns(3)
    pick = c[0].select_slider("Forecast day", options=days,
                              value=default if default in days else days[0],
                              format_func=lambda x: x.strftime("%d %b %Y"))
    solar_cap = c[1].slider("Installed solar (MW)", 0, 600, int(SOLAR_MW), 20)
    trigger = c[2].slider("Peaking trigger (MW)", 700, 1100, int(PEAK_TRIGGER), 10)

    day = t[t.timestamp.dt.date == pick].sort_values("hour")
    fc = day.forecast.values
    hours = day.hour.values
    sol = solar_output(hours, month=pick.month) * (solar_cap / SOLAR_MW if SOLAR_MW else 0)
    net = fc - sol
    ramp = np.diff(net, prepend=net[0])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hours, y=sol, name="solar output", fill="tozeroy",
                             line=dict(color=AMBER, width=1)))
    fig.add_trace(go.Scatter(x=hours, y=fc, name="forecast demand",
                             line=dict(color=CYAN, width=3)))
    fig.add_trace(go.Scatter(x=hours, y=net, name="net load (demand − solar)",
                             line=dict(color=RED, width=3)))
    fig.add_hline(y=trigger, line=dict(color=RED, dash="dash"),
                  annotation_text="peaking trigger")
    fig.add_hline(y=MUST_RUN, line=dict(color=MUTED, dash="dot"),
                  annotation_text="must-run minimum")
    fig.update_layout(title=f"{pick} — the duck curve the control room actually despatches",
                      xaxis_title="hour of day", yaxis_title="MW")
    st.plotly_chart(style(fig, 460), use_container_width=True)

    c = st.columns(4)
    c[0].metric("Peak demand ramp", f"{np.diff(fc).max():,.0f} MW/h")
    c[1].metric("Peak NET load ramp", f"{ramp.max():,.0f} MW/h",
                f"{ramp.max()-np.diff(fc).max():+,.0f} MW/h worse")
    c[2].metric("Peak net load", f"{net.max():,.0f} MW", f"at {int(hours[np.argmax(net)]):02d}:00")
    c[3].metric("Minimum net load", f"{net.min():,.0f} MW", f"at {int(hours[np.argmin(net)]):02d}:00")

    st.error("**Solar makes the evening ramp worse, not better.** The sun sets exactly as the "
             "residential peak arrives, so the net load the generators have to follow rises far more "
             "steeply than demand does. Push the solar slider up and watch the gap widen — that is "
             "the whole operational argument for forecasting **net load**, not demand.")

    st.markdown("##### The despatch schedule this produces")
    COLOR = {"MAINTAIN CURRENT GENERATION": GREEN, "INCREASE GENERATION CAPACITY": AMBER,
             "PREPARE PEAK LOAD UNITS": RED, "CHARGE ENERGY STORAGE": CYAN,
             "REDUCE RENEWABLE CURTAILMENT": TECH}

    def _despatch(f_mw, n_mw, r_mw, h):
        if n_mw > trigger:
            return ("PREPARE PEAK LOAD UNITS",
                    f"net load {n_mw:,.0f} MW exceeds the {trigger:,.0f} MW committed-plant trigger "
                    f"— bring peaking units to standby now")
        return despatch(f_mw, n_mw, r_mw, h)

    rows = []
    for k in range(len(fc)):
        ins, why = _despatch(fc[k], net[k], ramp[k], int(hours[k]))
        rows.append(dict(hour=f"{int(hours[k]):02d}:00", forecast=round(fc[k]),
                         solar=round(sol[k]), net=round(net[k]),
                         ramp=round(ramp[k]), instruction=ins))
    sched = pd.DataFrame(rows)
    st.dataframe(sched, use_container_width=True, hide_index=True, height=300)

    acts = {}
    for r in rows:
        acts.setdefault(r["instruction"], []).append(int(r["hour"][:2]))
    for ins, hrs in acts.items():
        st.markdown(
            f"<div class='mimic' style='border-left-color:{COLOR.get(ins, MUTED)}'>"
            f"<b style='color:{COLOR.get(ins, MUTED)}'>{ins}</b> &nbsp;"
            f"<span class='muted'>{hour_spans(sorted(hrs))} &nbsp;({len(hrs)} h)</span></div>",
            unsafe_allow_html=True)

    st.write("")
    with st.expander("The reasoning behind three of those instructions"):
        for k in [4, 12, 19]:
            if k < len(fc):
                ins, why = _despatch(fc[k], net[k], ramp[k], int(hours[k]))
                st.markdown(f"**{int(hours[k]):02d}:00 — {ins}**  \n{why}")

    st.info("These rules are **not machine learning, and should not be.** They encode the utility's own "
            "operating policy, which has to stay readable and auditable — a regulator can challenge "
            "every threshold on this page. The AI supplies the number; the policy turns it into an "
            "action.")
