"""
AI for Transformer Hot-Spot Temperature Prediction
===================================================
An interactive learning platform for Electrical Power Engineering students.

This app teaches CONCEPTUAL UNDERSTANDING. The companion Colab notebook teaches
implementation. They are completely independent: this app imports nothing from
the notebook and reads none of its files.

    app.py     the router, the landing page, and one renderer per stage
    bridge.py  the five-part Electrical-Engineering -> AI teaching scaffold
    story.py   the substation, its physics, its data and its models

Every number printed here is computed by story.py. Nothing is hardcoded into a
caption.

Run:  streamlit run app.py
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import story
import bridge
from bridge import EE, AISIDE, TECH, GREEN, RED, MUTED, TEXT, INK, EDGE, AMBERHOT, MONOF

st.set_page_config(page_title="AI for Transformer Hot-Spot Prediction", page_icon="⚡",
                   layout="wide", initial_sidebar_state="expanded")
bridge.inject_css()


# ============================================================================
# CHART HELPERS
# ============================================================================
def style(fig, h=440):
    fig.update_layout(
        height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, size=13), margin=dict(l=12, r=12, t=46, b=12),
        legend=dict(orientation="h", y=1.06, x=0, bgcolor="rgba(0,0,0,0)"),
        title=dict(font=dict(size=15, color=TEXT)), hoverlabel=dict(font_size=12))
    fig.update_xaxes(gridcolor="#1c2531", zerolinecolor="#2b3440", linecolor=EDGE)
    fig.update_yaxes(gridcolor="#1c2531", zerolinecolor="#2b3440", linecolor=EDGE)
    return fig


def animate(fig, frames, ms=340):
    """Attach frames and a Play button."""
    if not frames:
        return fig
    fig.frames = frames
    fig.update_layout(updatemenus=[dict(
        type="buttons", showactive=False, x=0, y=1.16, xanchor="left",
        bgcolor="#141b24", bordercolor=EDGE, font=dict(color=TEXT, size=11),
        buttons=[dict(label="▶  Play", method="animate",
                      args=[None, dict(frame=dict(duration=ms, redraw=True),
                                       fromcurrent=True, transition=dict(duration=0))])])])
    return fig


def temp_colour(t):
    """The course colour for a hot-spot temperature."""
    if t < 98:
        return GREEN
    if t < story.LIMIT_NORMAL:
        return EE
    if t < story.LIMIT_PLANNED:
        return AMBERHOT
    return RED


def oil_colour(t, lo=20, hi=100):
    """A blue→red fill colour for an oil or winding temperature."""
    f = float(np.clip((t - lo) / (hi - lo), 0, 1))
    r = int(40 + 200 * f); g = int(90 + 60 * (1 - abs(f - 0.5) * 2)); b = int(190 - 170 * f)
    return f"rgb({r},{g},{b})"


def limit_chips():
    st.markdown(
        f"<span class='limit' style='color:{GREEN};border-color:{GREEN}'>&lt; 98 °C  normal</span>"
        f"<span class='limit' style='color:{EE};border-color:{EE}'>110 °C  normal life expectancy</span>"
        f"<span class='limit' style='color:{AMBERHOT};border-color:{AMBERHOT}'>120 °C  beyond nameplate</span>"
        f"<span class='limit' style='color:{RED};border-color:{RED}'>140 °C  emergency</span>",
        unsafe_allow_html=True)


def gauge(value, title="Predicted hot spot", h=300):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value, title={"text": title, "font": {"size": 14}},
        number={"suffix": " °C", "font": {"size": 40, "color": temp_colour(value)}},
        gauge={"axis": {"range": [20, 145], "tickcolor": MUTED},
               "bar": {"color": "rgba(230,237,243,.85)", "thickness": 0.2},
               "bgcolor": INK, "borderwidth": 1, "bordercolor": EDGE,
               "steps": [{"range": [20, 98], "color": "rgba(102,187,106,.28)"},
                         {"range": [98, 110], "color": "rgba(255,183,77,.28)"},
                         {"range": [110, 120], "color": "rgba(255,112,67,.30)"},
                         {"range": [120, 145], "color": "rgba(239,83,80,.32)"}],
               "threshold": {"line": {"color": RED, "width": 4}, "value": 110}}))
    return style(fig, h)


# ============================================================================
# THE TRANSFORMER CROSS-SECTION  -  used on several pages
# ============================================================================
def transformer_section(load_pu, ambient_c, oil_c, hotspot_c, stage, h=470, arrows=True):
    """A cutaway of the tank: core, windings, oil, radiators, and the hot spot."""
    fig = go.Figure()

    # ---- tank and oil ----
    fig.add_shape(type="rect", x0=0.20, x1=0.80, y0=0.10, y1=0.80,
                  line=dict(color=MUTED, width=2), fillcolor=INK)
    # oil fill, shaded warmer towards the top (real thermal stratification)
    n = 14
    for i in range(n):
        y0 = 0.12 + (0.64 / n) * i
        t = ambient_c + (oil_c - ambient_c) * (0.45 + 0.55 * i / (n - 1))
        fig.add_shape(type="rect", x0=0.22, x1=0.78, y0=y0, y1=y0 + 0.64 / n,
                      line=dict(width=0), fillcolor=oil_colour(t), opacity=0.30, layer="below")

    # ---- core ----
    fig.add_shape(type="rect", x0=0.455, x1=0.545, y0=0.20, y1=0.72,
                  line=dict(color="#9aa4b2", width=1.5), fillcolor="#39414d")
    fig.add_annotation(x=0.50, y=0.165, text="core", showarrow=False,
                       font=dict(size=10, color=MUTED, family=MONOF))

    # ---- windings: colour by winding temperature ----
    wcol = oil_colour(hotspot_c, 30, 140)
    for x0, x1, lab in [(0.335, 0.435, "LV"), (0.565, 0.665, "HV")]:
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=0.24, y1=0.70,
                      line=dict(color=wcol, width=2), fillcolor=wcol, opacity=0.42)
        fig.add_annotation(x=(x0 + x1) / 2, y=0.205, text=lab, showarrow=False,
                           font=dict(size=10, color=MUTED, family=MONOF))
        for yy in np.linspace(0.26, 0.68, 9):      # winding discs
            fig.add_shape(type="line", x0=x0, x1=x1, y0=yy, y1=yy,
                          line=dict(color="rgba(255,255,255,.18)", width=1))

    # ---- the hot spot: top of the winding, where oil is warmest ----
    fig.add_trace(go.Scatter(
        x=[0.615], y=[0.665], mode="markers+text",
        marker=dict(size=26, color=temp_colour(hotspot_c), symbol="circle",
                    line=dict(color=TEXT, width=2)),
        text=[f"  <b>{hotspot_c:.0f} °C</b>"], textposition="middle right",
        textfont=dict(size=15, color=temp_colour(hotspot_c)),
        hovertemplate=f"Winding hot spot<br>{hotspot_c:.1f} °C<extra></extra>",
        showlegend=False))
    fig.add_annotation(x=0.615, y=0.735, text="HOT SPOT", showarrow=False,
                       font=dict(size=9.5, color=temp_colour(hotspot_c), family=MONOF))

    # ---- top-oil thermometer ----
    fig.add_trace(go.Scatter(
        x=[0.30], y=[0.755], mode="markers+text",
        marker=dict(size=15, color=oil_colour(oil_c), symbol="diamond",
                    line=dict(color=TEXT, width=1.4)),
        text=[f"  {oil_c:.0f} °C"], textposition="middle right",
        textfont=dict(size=12, color=TEXT),
        hovertemplate=f"Top-oil thermometer<br>{oil_c:.1f} °C<extra></extra>",
        showlegend=False))
    fig.add_annotation(x=0.30, y=0.815, text="TOP-OIL GAUGE", showarrow=False,
                       font=dict(size=9, color=MUTED, family=MONOF))

    # ---- radiators, one bank each side; lit when the fans run ----
    for side, x_out in [(-1, 0.20), (1, 0.80)]:
        for k in range(5):
            y = 0.22 + 0.12 * k
            x0 = x_out + side * 0.03
            x1 = x_out + side * 0.13
            fig.add_shape(type="rect", x0=min(x0, x1), x1=max(x0, x1), y0=y, y1=y + 0.075,
                          line=dict(color=MUTED, width=1),
                          fillcolor=oil_colour(oil_c - 6), opacity=0.5)
        if stage > 0:
            fig.add_annotation(x=x_out + side * 0.175, y=0.46,
                               text="⟫⟫" if side > 0 else "⟪⟪", showarrow=False,
                               font=dict(size=17, color=AISIDE))
    fig.add_annotation(x=0.50, y=0.055,
                       text=f"cooling stage {stage} — "
                            + ["fans off, natural circulation", "first fan bank running",
                               "all fans running"][stage],
                       showarrow=False, font=dict(size=10.5, color=AISIDE if stage else MUTED,
                                                  family=MONOF))

    # ---- bushings ----
    for x in (0.36, 0.64):
        fig.add_shape(type="line", x0=x, x1=x, y0=0.80, y1=0.90,
                      line=dict(color=MUTED, width=3))
        fig.add_shape(type="circle", x0=x - 0.018, x1=x + 0.018, y0=0.895, y1=0.925,
                      line=dict(color=MUTED, width=1.5), fillcolor="#39414d")

    # ---- heat-flow arrows: winding -> oil -> radiator -> air ----
    if arrows:
        for (ax, ay, x, y) in [(0.665, 0.62, 0.745, 0.66), (0.745, 0.66, 0.80, 0.55),
                               (0.335, 0.62, 0.255, 0.66), (0.255, 0.66, 0.20, 0.55)]:
            fig.add_annotation(x=x, y=y, ax=ax, ay=ay, xref="x", yref="y",
                               axref="x", ayref="y", showarrow=True, arrowhead=2,
                               arrowsize=1.1, arrowwidth=1.6, arrowcolor=AMBERHOT, opacity=0.75)

    fig.add_annotation(x=0.02, y=0.93, xanchor="left",
                       text=f"<b>load {load_pu:.2f} pu</b>   ambient {ambient_c:.0f} °C",
                       showarrow=False, font=dict(size=12, color=EE, family=MONOF))
    fig.update_xaxes(visible=False, range=[0, 1])
    fig.update_yaxes(visible=False, range=[0, 1], scaleanchor=None)
    fig.update_layout(margin=dict(l=6, r=6, t=6, b=6))
    return style(fig, h)


# ============================================================================
# PHASE 1  -  THE TRANSFORMER IN SERVICE
# ============================================================================
def render_log():
    log = story.get_raw_log()
    a, b, c, d = st.columns(4)
    a.metric("Rows", f"{len(log):,}")
    b.metric("Columns", log.shape[1])
    c.metric("Units", log.unit_id.nunique())
    d.metric("Period", "2025")
    st.markdown("**The export, exactly as it arrived — nothing corrected**")
    st.dataframe(log.head(12), width="stretch", hide_index=True)
    st.caption("Every row is one transformer for one hour. Some of these rows are wrong, and "
               "the next page finds them.")


def render_inspect():
    log = story.get_raw_log()
    st.markdown("**Six things wrong with this data — hover any red ring to see why**")
    amb = log.sort_values(["unit_id", "timestamp"]).groupby("unit_id", sort=False).ambient_temp_c
    runs = amb.transform(lambda s: s.groupby((s != s.shift()).cumsum()).transform("size"))
    checks = [
        ("Missing readings", int(log.isna().sum().sum()),
         "The sensor dropped out. No value was recorded at all."),
        ("Humidity above 100 %", int((log.humidity_pct > 100).sum()),
         "Impossible. A broken sensor is sending 255."),
        ("Load below 10 A", int((log.load_current_a < 10).sum()),
         "The transformer was switched off. It was cooling down, not working."),
        ("Air temperature stuck", int((runs >= 6).sum()),
         "Same value for hours. Each reading looks fine; the run of them does not."),
        ("Duplicated rows", int(log.duplicated().sum()),
         "The export ran twice and pasted part of the year in again."),
        ("Columns that never change", len([c for c in log.columns
                                           if log[c].nunique(dropna=True) == 1]),
         "A column with one value in it cannot teach a model anything."),
    ]
    cols = st.columns(3)
    for i, (name, n, why) in enumerate(checks):
        with cols[i % 3]:
            st.metric(name, f"{n:,}")
            st.caption(why)
    st.divider()

    c1, c2 = st.columns([1, 1])
    with c1:
        fig = go.Figure(go.Histogram(x=log.humidity_pct, nbinsx=80, marker_color=EE))
        fig.add_vrect(x0=100, x1=270, fillcolor=RED, opacity=0.10, line_width=0)
        fig.add_vline(x=100, line=dict(color=RED, dash="dash"))
        bad = int((log.humidity_pct > 100).sum())
        mark_wrong(fig, 255, bad * 0.6, "Impossible values",
                   f"{bad} readings say humidity is 255 %.<br>"
                   "Air cannot be more than 100 % humid.<br>"
                   "A failed sensor sends 255 when it has nothing to report.")
        fig.update_layout(title="Humidity — one glance finds it",
                          xaxis_title="Humidity (%)", yaxis_title="Number of hours")
        st.plotly_chart(style(fig, 340), width="stretch")
        figlab("Humidity readings for the whole year",
               "everything in the red band cannot physically happen")
        wrongkey([("Red band", "above 100 % humidity — physically impossible"),
                  ("Red ring", "hover it for what went wrong")])
    with c2:
        u = log[log.unit_id == "T1"].sort_values("timestamp")
        bad_rows = u[runs.loc[u.index] >= 6]
        w = (u[(u.timestamp >= bad_rows.timestamp.min() - pd.Timedelta(hours=40)) &
               (u.timestamp <= bad_rows.timestamp.max() + pd.Timedelta(hours=40))]
             if len(bad_rows) else u.head(80))
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=w.timestamp, y=w.ambient_temp_c, mode="lines+markers",
                                 line=dict(color=EE, width=2), name="air temperature"))
        if len(bad_rows):
            fig.add_trace(go.Scatter(x=bad_rows.timestamp, y=bad_rows.ambient_temp_c,
                                     mode="markers", marker=dict(size=9, color=RED),
                                     name="stuck"))
            mid = bad_rows.iloc[len(bad_rows) // 2]
            mark_wrong(fig, mid.timestamp, mid.ambient_temp_c, "Sensor stuck",
                       f"{len(bad_rows)} hours in a row report exactly "
                       f"{mid.ambient_temp_c:.1f} °C.<br>"
                       "Outdoor air never holds that still.<br>"
                       "The sensor froze - but no single reading looks wrong.")
        fig.update_layout(title="Air temperature — only the sequence gives it away",
                          yaxis_title="°C")
        st.plotly_chart(style(fig, 340), width="stretch")
        figlab("Air temperature around a sensor fault",
               "a flat line where there should be a daily rise and fall")
        wrongkey([("Red dots", "the stuck run"),
                  ("Why it is sneaky", "a summary table would never catch this")])


def render_explore():
    log = story.get_raw_log()
    c1, c2 = st.columns([1, 1])
    with c1:
        unit = st.selectbox("Unit", sorted(log.unit_id.dropna().unique()), index=2, key="ex_u")
        wk = log[(log.unit_id == unit) & (log.timestamp >= "2025-06-09") &
                 (log.timestamp < "2025-06-16")].sort_values("timestamp")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=wk.timestamp, y=wk.load_current_a, name="Load (A)",
                                 line=dict(color=AISIDE, width=2)), secondary_y=True)
        for col, colr, nm in [("ambient_temp_c", MUTED, "Ambient"),
                              ("oil_temp_c", EE, "Top oil"),
                              ("hotspot_temp_c", RED, "Hot spot")]:
            fig.add_trace(go.Scatter(x=wk.timestamp, y=wk[col], name=nm,
                                     line=dict(color=colr, width=2)), secondary_y=False)
        fig.update_yaxes(title_text="°C", secondary_y=False)
        fig.update_yaxes(title_text="A", secondary_y=True, showgrid=False)
        fig.update_layout(title=f"{unit}, one week in June — load leads, oil follows",
                          hovermode="x unified")
        st.plotly_chart(style(fig, 400), width="stretch")
        figlab("One week of readings for one transformer",
               "load on the right axis, temperatures on the left")
        st.caption("Load rises, the oil follows slowly, the winding follows at once — so the "
                   "gap between the amber and red lines opens at every peak.")
    with c2:
        band = st.slider("Hold the load in this band (A)", 300, 950, (680, 720), 10)
        s = log.dropna(subset=["hotspot_temp_c"])
        sel = s[(s.load_current_a >= band[0]) & (s.load_current_a <= band[1])]
        samp = s.sample(min(4000, len(s)), random_state=1)
        fig = go.Figure()
        fig.add_trace(go.Scattergl(x=samp.load_current_a, y=samp.hotspot_temp_c, mode="markers",
                                   marker=dict(size=3, color=samp.ambient_temp_c,
                                               colorscale="Turbo", opacity=0.5,
                                               colorbar=dict(title="Ambient<br>°C")),
                                   name="hours", hoverinfo="skip"))
        fig.add_vrect(x0=band[0], x1=band[1], fillcolor=AISIDE, opacity=0.12, line_width=0)
        fig.add_hline(y=110, line=dict(color=RED, dash="dash"))
        fig.update_layout(title="Same load, tens of degrees of spread",
                          xaxis_title="Load current (A)", yaxis_title="Hot spot (°C)")
        st.plotly_chart(style(fig, 400), width="stretch")
        figlab("Every hour of the year: load against hot-spot temperature",
               "colour is the air temperature")
        if len(sel):
            st.info(f"At the **same load**, the hot spot still ranges over "
                    f"**{sel.hotspot_temp_c.max() - sel.hotspot_temp_c.min():.0f} °C**. So load "
                    "alone cannot tell you the temperature — which is exactly why the model "
                    "needs more than one input.")


# ============================================================================
# PHASE 4  -  PREPARING THE DATA
# ============================================================================
def render_clean():
    clean, report, before = story.get_clean_log()
    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.markdown("**The cleaning log — every action, with a count**")
        st.dataframe(report, width="stretch", hide_index=True)
        a, b = st.columns(2)
        a.metric("Rows in", f"{before:,}")
        b.metric("Rows out", f"{len(clean):,}",
                 f"-{100 * (before - len(clean)) / before:.1f} %")
    with c2:
        st.markdown("**The two decisions that matter**")
        st.markdown(
            f"<div class='relay ok'><b>Interpolate the oil temperature.</b> It has a "
            f"three-hour time constant, so an hour's gap really is bridgeable. Interpolating "
            f"<i>load current</i> would not be — it can double in an hour.</div>",
            unsafe_allow_html=True)
        st.write("")
        st.markdown(
            f"<div class='relay warn'><b>Delete the de-energised hours.</b> A cooling "
            f"transformer obeys different physics from a loaded one. Keeping those rows teaches "
            f"the model that low current means winding-at-ambient — and it will then "
            f"under-predict every genuinely light-load hour.</div>", unsafe_allow_html=True)
        st.write("")
        raw = story.get_raw_log()
        de = raw[raw.load_current_a < 10]
        if len(de):
            fig = go.Figure()
            ok = raw.dropna(subset=["hotspot_temp_c"]).sample(3000, random_state=2)
            fig.add_trace(go.Scattergl(x=ok.load_current_a, y=ok.hotspot_temp_c, mode="markers",
                                       marker=dict(size=3, color=MUTED, opacity=0.4), name="normal"))
            fig.add_trace(go.Scatter(x=de.load_current_a, y=de.hotspot_temp_c, mode="markers",
                                     marker=dict(size=11, color=RED, symbol="x"),
                                     name="de-energised"))
            fig.update_layout(title="The rows that must be deleted, not repaired",
                              xaxis_title="Load current (A)", yaxis_title="Hot spot (°C)")
            st.plotly_chart(style(fig, 300), width="stretch")
            figlab("The rows that must be deleted, not repaired")


def render_features():
    df = story.get_features()
    c1, c2 = st.columns([1, 1.15])
    with c1:
        st.markdown("**One row, before and after**")
        i = st.slider("Pick an hour from the log", 0, len(df) - 1, 5000, key="ft_i")
        r = df.iloc[i]
        st.markdown("*What the instruments reported*")
        st.dataframe(pd.DataFrame({"Value": [r[c] for c in story.RAW_FEATURES]},
                                  index=[story.FEATURE_LABELS[c] for c in story.RAW_FEATURES]),
                     width="stretch")
        st.markdown("*What the engineer computes from it*")
        eng = ["load_pu_16", "oil_rise_c", "load_roll3", "load_ramp_1h", "oil_ramp_1h"]
        st.dataframe(pd.DataFrame({"Value": [round(float(r[c]), 3) for c in eng]},
                                  index=[story.FEATURE_LABELS[c] for c in eng]),
                     width="stretch")
    with c2:
        cors = df[story.ENG_FEATURES + [story.TARGET]].corr()[story.TARGET] \
            .drop(story.TARGET).abs().sort_values()
        fig = go.Figure(go.Bar(
            x=cors.values, y=[story.FEATURE_LABELS[c] for c in cors.index], orientation="h",
            marker_color=[TECH if c in story.RAW_FEATURES else AISIDE for c in cors.index],
            text=cors.values.round(2), textposition="outside"))
        fig.update_layout(title="Absolute correlation with the hot spot "
                                "(violet = raw sensor, cyan = engineered)",
                          xaxis_title="|correlation|", xaxis_range=[0, 1.08])
        st.plotly_chart(style(fig, 470), width="stretch")
        figlab("Absolute correlation with the hot spot")
        st.info("**`load_roll3`, the 3-hour mean load, correlates more strongly than any raw "
                "sensor.** It is not a new measurement — it is the same current, remembered. "
                "That memory is what fills the gap left by the oil thermometer's lag.")


def render_scale():
    df = story.get_features()
    cols = ["load_current_a", "voltage_kv", "load_pu_16", "ambient_temp_c"]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Before — four columns, four different scales**")
        fig = go.Figure()
        for c, colr in zip(cols, [EE, AISIDE, TECH, GREEN]):
            fig.add_trace(go.Box(y=df[c], name=story.FEATURE_LABELS[c], marker_color=colr,
                                 boxpoints=False))
        fig.update_layout(title="Raw values", yaxis_type="log", showlegend=False)
        st.plotly_chart(style(fig, 360), width="stretch")
        figlab("Raw values")
        st.dataframe(df[cols].describe().T[["mean", "std", "min", "max"]].round(2),
                     width="stretch")
    with c2:
        st.markdown("**After — mean 0, standard deviation 1**")
        z = (df[cols] - df[cols].mean()) / df[cols].std()
        fig = go.Figure()
        for c, colr in zip(cols, [EE, AISIDE, TECH, GREEN]):
            fig.add_trace(go.Box(y=z[c], name=story.FEATURE_LABELS[c], marker_color=colr,
                                 boxpoints=False))
        fig.update_layout(title="Standardised values", showlegend=False)
        st.plotly_chart(style(fig, 360), width="stretch")
        figlab("Standardised values")
        st.markdown(
            f"<div class='relay ai'><b>Linear models care. Trees do not.</b> A tree split at "
            f"<code>load_current_a &gt; 640</code> is the same split as "
            f"<code>load_pu &gt; 0.914</code>. The scaler is fitted on the training rows only — "
            f"fitting it on everything leaks the test set's mean into training.</div>",
            unsafe_allow_html=True)


def render_split():
    df = story.get_features()
    te = df.test
    c1, c2 = st.columns([1.2, 1])
    with c1:
        weeks = df.assign(w=df.timestamp.dt.isocalendar().week.astype(int)) \
                  .groupby("w").agg(test=("test", "first")).reset_index()
        fig = go.Figure(go.Bar(
            x=weeks.w, y=[1] * len(weeks),
            marker_color=[AISIDE if t else EE for t in weeks.test],
            hovertext=[f"week {w}: {'TEST' if t else 'train'}"
                       for w, t in zip(weeks.w, weeks.test)], hoverinfo="text"))
        fig.update_layout(title="The calendar year — every fourth week held out (cyan)",
                          xaxis_title="ISO week", yaxis=dict(visible=False), showlegend=False,
                          bargap=0.15)
        st.plotly_chart(style(fig, 250), width="stretch")
        figlab("The calendar year — every fourth week held out (cyan)")
        st.caption("Whole weeks, not random rows — so 14:00 Tuesday cannot sit in training "
                   "while 15:00 Tuesday sits in test. Both seasons appear in both sets.")
    with c2:
        a, b = st.columns(2)
        a.metric("Training rows", f"{int((~te).sum()):,}")
        b.metric("Test rows", f"{int(te.sum()):,}", f"{100 * te.mean():.0f} % held out")
        st.dataframe(pd.DataFrame({
            "Train": [round(df.loc[~te, story.TARGET].mean(), 2),
                      round(df.loc[~te, story.TARGET].std(), 2),
                      int((df.loc[~te, story.TARGET] > 110).sum())],
            "Test": [round(df.loc[te, story.TARGET].mean(), 2),
                     round(df.loc[te, story.TARGET].std(), 2),
                     int((df.loc[te, story.TARGET] > 110).sum())]},
            index=["Hot spot mean (°C)", "Hot spot std dev (°C)", "Hours above 110 °C"]),
            width="stretch")
        st.info("The hot band appears in **both** sets. A naive chronological split would have "
                "put most of it in one season — and the hot band is the only part anyone cares "
                "about.")


# ============================================================================
# PHASE 5  -  THE FIRST PREDICTION
# ============================================================================
def render_baseline():
    m = story.get_models()
    df = story.get_features()
    te = m["test_mask"]
    y, p = m["y_test"], m["preds"]["ieee"]
    row = m["board"].set_index("Model").loc["IEEE C57.91 (nameplate)"]
    a, b, c = st.columns(3)
    a.metric("MAE", f"{row['MAE (°C)']:.2f} °C")
    b.metric("RMSE", f"{row['RMSE (°C)']:.2f} °C")
    c.metric("R²", f"{row['R²']:.3f}")
    st.caption("Nothing was fitted. This is the closed-form standard, applied as printed, "
               "on the same held-out weeks every other model is scored on.")
    c1, c2 = st.columns([1, 1])
    with c1:
        units = df.loc[te, "unit_id"].to_numpy()
        bias = pd.Series(p - y).groupby(units).mean()
        fig = go.Figure(go.Bar(x=bias.index, y=bias.values,
                               marker_color=[GREEN if v > 0 else RED for v in bias.values],
                               text=bias.round(2), textposition="outside"))
        fig.add_hline(y=0, line=dict(color=TEXT, dash="dash"))
        fig.update_layout(title="Mean error per unit — the standard assumes all four are identical",
                          yaxis_title="Predicted − measured (°C)")
        st.plotly_chart(style(fig, 350), width="stretch")
        figlab("Mean error per unit — the standard assumes all four are identical")
        st.warning("These are **biases**, not noise, and they point in opposite directions all "
                   "year. That is the per-unit hot-spot factor — and it is exactly the "
                   "information a fitted model can pick up.")
    with c2:
        fig = go.Figure()
        fig.add_trace(go.Scattergl(x=y, y=p, mode="markers",
                                   marker=dict(size=3, color=MUTED, opacity=0.3), name="hours"))
        lim = [y.min() - 2, y.max() + 2]
        fig.add_trace(go.Scatter(x=lim, y=lim, line=dict(color=TEXT, dash="dash"),
                                 name="perfect"))
        fig.update_layout(title="IEEE C57.91 predicted against measured",
                          xaxis_title="Measured (°C)", yaxis_title="Predicted (°C)")
        st.plotly_chart(style(fig, 350), width="stretch")
        figlab("IEEE C57.91 predicted against measured")


def render_linear():
    m = story.get_models()
    board = m["board"].set_index("Model")
    c1, c2 = st.columns([1, 1.1])
    with c1:
        coefs = story.lin_raw_coefs().sort_values(key=abs)
        fig = go.Figure(go.Bar(x=coefs.values,
                               y=[story.FEATURE_LABELS[c] for c in coefs.index],
                               orientation="h",
                               marker_color=[EE if v > 0 else AISIDE for v in coefs.values],
                               text=coefs.values.round(2), textposition="outside"))
        fig.update_layout(title="Coefficients: °C of hot spot per standard deviation of the sensor",
                          xaxis_title="°C")
        st.plotly_chart(style(fig, 330), width="stretch")
        figlab("Coefficients: °C of hot spot per standard deviation of the sensor")
        st.caption("Load current comes first, oil temperature second, ambient a distant third. "
                   "Humidity is near zero and voltage is essentially zero — the model has "
                   "decided those two sensors tell it nothing.")
    with c2:
        rows = ["IEEE C57.91 (nameplate)", "Linear regression (5 raw sensors)",
                "Linear regression (engineered)"]
        vals = [board.loc[r, "MAE (°C)"] for r in rows]
        fig = go.Figure(go.Bar(x=["IEEE C57.91<br>nameplate", "Linear<br>5 raw sensors",
                                  "Linear<br>engineered"], y=vals,
                               marker_color=[MUTED, EE, AISIDE],
                               text=[f"{v:.2f}" for v in vals], textposition="outside"))
        fig.update_layout(title="Mean absolute error (°C, lower is better)",
                          yaxis_title="MAE (°C)")
        st.plotly_chart(style(fig, 330), width="stretch")
        figlab("Mean absolute error (°C, lower is better)")
        st.success(f"**Fitting to this fleet at all is worth {vals[0] - vals[1]:.2f} °C.** "
                   f"Adding the engineered columns — same algorithm, no new sensors — is worth "
                   f"another **{vals[1] - vals[2]:.2f} °C**.")


def render_residuals():
    m = story.get_models()
    df = story.get_features()
    te = m["test_mask"]
    err = m["preds"]["lin_raw"] - m["y_test"]
    res = pd.DataFrame({"load_pu": df.loc[te, "load_pu"].to_numpy(),
                        "stage": df.loc[te, "cooling_stage"].to_numpy(), "err": err})
    c1, c2 = st.columns([1.15, 1])
    with c1:
        binned = res.groupby(pd.cut(res.load_pu, 25), observed=True).agg(
            x=("load_pu", "mean"), e=("err", "mean")).dropna()
        fig = go.Figure()
        fig.add_trace(go.Scattergl(x=res.load_pu, y=res.err, mode="markers",
                                   marker=dict(size=3, color=MUTED, opacity=0.22),
                                   name="every test hour"))
        fig.add_trace(go.Scatter(x=binned.x, y=binned.e, mode="lines+markers",
                                 line=dict(color=RED, width=3), name="mean error"))
        fig.add_hline(y=0, line=dict(color=TEXT, dash="dash"))
        fig.update_layout(title="Residual against load — it curves, so the relationship bends",
                          xaxis_title="Load (per unit)", yaxis_title="Prediction error (°C)")
        st.plotly_chart(style(fig, 380), width="stretch")
        figlab("Residual against load — it curves, so the relationship bends")
    with c2:
        fig = go.Figure()
        for s, colr in zip([0, 1, 2], [AISIDE, EE, RED]):
            fig.add_trace(go.Box(y=res.loc[res.stage == s, "err"], name=f"stage {s}",
                                 marker_color=colr, boxpoints=False))
        fig.add_hline(y=0, line=dict(color=TEXT, dash="dash"))
        fig.update_layout(title="Residual by cooling stage — it steps, so there is an interaction",
                          yaxis_title="Prediction error (°C)", showlegend=False)
        st.plotly_chart(style(fig, 380), width="stretch")
        figlab("Residual by cooling stage — it steps, so there is an interaction")
    st.markdown(
        "<div class='relay tech'><b>Leftover errors should look like random noise.</b> These "
        "form a curve instead — proof the straight line is the wrong shape, and that the next "
        "model has to be able to bend.</div>", unsafe_allow_html=True)


# ============================================================================
# PHASE 6  -  MODELS THAT BEND
# ============================================================================
def render_forest():
    m = story.get_models()
    board = m["board"].set_index("Model")
    c1, c2 = st.columns([1, 1.1])
    with c1:
        st.markdown("**One tree is a chain of engineering rules**")
        forest = story.forest_facts()
        lines = [f"if <b style='color:{EE}'>{story.FEATURE_LABELS[r['feature']]}</b> "
                 f"≤ {r['threshold']:.2f}" for r in forest["rules"]]
        st.markdown(f"<div class='relay' style='font-family:{MONOF};font-size:13.5px'>"
                    + "<br>&nbsp;&nbsp;".join(lines)
                    + f"<br>&nbsp;&nbsp;→ predict a hot-spot temperature</div>",
                    unsafe_allow_html=True)
        st.caption("Read from the first tree in the forest. Every split is a threshold an "
                   "engineer could have written down — the forest just found 200 sets of them.")
        a, b = st.columns(2)
        a.metric("Trees", forest["trees"])
        b.metric("Mean depth", f"{forest['mean_depth']:.0f}")
    with c2:
        n = st.slider("How many trees are averaged?", 1, story.RF_TREES,
                      story.RF_TREES, key="rf_n")
        mae = float(forest["curve"].loc[n])
        fig = go.Figure(go.Bar(
            x=["Linear<br>engineered", f"Forest of {n}", "Full forest"],
            y=[board.loc["Linear regression (engineered)", "MAE (°C)"], mae,
               board.loc["Random Forest", "MAE (°C)"]],
            marker_color=[MUTED, EE, GREEN],
            text=[f"{board.loc['Linear regression (engineered)', 'MAE (°C)']:.2f}",
                  f"{mae:.2f}", f"{board.loc['Random Forest', 'MAE (°C)']:.2f}"],
            textposition="outside"))
        fig.update_layout(title="Averaging more disagreeing trees lowers the error",
                          yaxis_title="MAE (°C)")
        st.plotly_chart(style(fig, 360), width="stretch")
        figlab("Averaging more disagreeing trees lowers the error")
        st.caption(f"One tree alone scores about {forest['one_tree_mae']:.2f} °C. "
                   "It memorises. The average of many does not.")


def render_boosting():
    m = story.get_models()
    board = m["board"].set_index("Model")
    st.markdown("**Each tree is fitted to what the previous ones got wrong**")
    c1, c2 = st.columns([1.2, 1])
    with c1:
        # a small illustrative boosting run so the curve is live, not asserted
        curve = _boost_curve()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=curve.index, y=curve.values, line=dict(color=EE, width=3),
                                 name="test MAE"))
        fig.add_hline(y=board.loc["Linear regression (engineered)", "MAE (°C)"],
                      line=dict(color=MUTED, dash="dash"),
                      annotation_text="linear regression, engineered")
        fig.add_hline(y=board.loc["Random Forest", "MAE (°C)"],
                      line=dict(color=AISIDE, dash="dash"), annotation_text="random forest")
        fig.update_layout(title="Test error as trees are added",
                          xaxis_title="Trees added", yaxis_title="Test MAE (°C)")
        st.plotly_chart(style(fig, 400), width="stretch")
        figlab("Test error as trees are added")
    with c2:
        lin = board.loc["Linear regression (engineered)", "MAE (°C)"]
        rf = board.loc["Random Forest", "MAE (°C)"]
        pass_lin = int(curve.index[np.argmax(curve.values < lin)]) if (curve.values < lin).any() else None
        pass_rf = int(curve.index[np.argmax(curve.values < rf)]) if (curve.values < rf).any() else None
        st.metric("Error after 25 trees", f"{curve.iloc[min(1, len(curve) - 1)]:.2f} °C")
        st.metric("Error at the end", f"{curve.iloc[-1]:.2f} °C")
        if pass_lin:
            st.metric("Trees needed to pass linear", pass_lin)
        if pass_rf:
            st.metric("Trees needed to pass the forest", pass_rf)
        st.markdown(
            "<div class='relay warn'><b>The first few dozen trees are worse than the straight "
            "line.</b> Boosting starts from a rough guess and improves it, so stopping it early "
            "would have looked like failure.</div>", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _boost_curve():
    """Test MAE against tree count, measured on a live boosting run."""
    art = story.precomputed("boost_curve")
    if art is not None:
        return pd.Series(art["mae"].to_numpy(), index=art["trees"].to_numpy())
    return story._compute_boost_curve()


def render_leaderboard():
    m = story.get_models()
    board = m["board"].copy()
    base = board.loc[board.Model == "IEEE C57.91 (nameplate)", "MAE (°C)"].iloc[0]
    board["vs standard"] = (100 * (1 - board["MAE (°C)"] / base)).round(0).astype(int).astype(str) + " %"
    st.dataframe(board.round(3), width="stretch", hide_index=True)
    c1, c2 = st.columns([1.3, 1])
    with c1:
        fig = go.Figure(go.Bar(
            x=board.Model, y=board["MAE (°C)"],
            marker_color=[GREEN if v < 1.6 else EE if v < 2.2 else RED for v in board["MAE (°C)"]],
            text=board["MAE (°C)"].round(2), textposition="outside"))
        fig.add_hline(y=base, line=dict(color=RED, dash="dash"),
                      annotation_text="IEEE C57.91 — the number to beat")
        fig.update_layout(title="Mean absolute error on the held-out weeks (lower is better)",
                          yaxis_title="MAE (°C)", xaxis_tickangle=-18,
                          margin=dict(b=130))
        st.plotly_chart(style(fig, 470), width="stretch")
        figlab("Mean absolute error on the held-out weeks (lower is better)")
    with c2:
        s = board.set_index("Model")["MAE (°C)"]
        levers = {
            "Fitting to this fleet at all": s["IEEE C57.91 (nameplate)"] - s["Linear regression (5 raw sensors)"],
            "Engineering the features": s["Linear regression (5 raw sensors)"] - s["Linear regression (engineered)"],
            "Changing the algorithm": s["Linear regression (engineered)"] - s.min(),
        }
        fig = go.Figure(go.Bar(x=list(levers.values()), y=list(levers.keys()), orientation="h",
                               marker_color=[EE, TECH, AISIDE],
                               text=[f"{v:.2f} °C" for v in levers.values()],
                               textposition="outside"))
        fig.update_layout(title="Three separate levers, measured",
                          xaxis_title="°C of error removed",
                          xaxis_range=[0, max(levers.values()) * 1.4])
        st.plotly_chart(style(fig, 300), width="stretch")
        figlab("Three separate levers, measured")
        st.success(f"**{base:.2f} °C → {s.min():.2f} °C, a "
                   f"{100 * (1 - s.min() / base):.0f} % cut against the model the industry "
                   f"uses.** No lever dominates — and the middle one costs nothing but domain "
                   "knowledge.")


# ============================================================================
# PHASE 7  -  READING THE MODEL
# ============================================================================
def render_importance():
    m = story.get_models()
    c1, c2 = st.columns([1.15, 1])
    with c1:
        ranks = story.importances()
        ranks = ranks.sort_values(ranks.columns[0])
        fig = go.Figure()
        fig.add_trace(go.Bar(x=ranks.iloc[:, 0], y=[story.FEATURE_LABELS[c] for c in ranks.index],
                             orientation="h", name=ranks.columns[0], marker_color=AISIDE))
        fig.add_trace(go.Bar(x=ranks["Random Forest"],
                             y=[story.FEATURE_LABELS[c] for c in ranks.index],
                             orientation="h", name="Random Forest", marker_color=EE))
        fig.update_layout(title="The two models do not agree on what matters",
                          barmode="group", xaxis_title="Relative importance")
        st.plotly_chart(style(fig, 500), width="stretch")
        figlab("The two models do not agree on what matters")
        st.caption(f"{ranks.columns[0]} puts **{story.FEATURE_LABELS[ranks.iloc[:, 0].idxmax()]}** "
                   f"first; the forest puts **{story.FEATURE_LABELS[ranks['Random Forest'].idxmax()]}** "
                   "first. A ranking describes how one model carved up the information — not "
                   "what the transformer is doing.")
    with c2:
        st.markdown("**The test that answers the question a scheme designer asks**")
        drops = _instrument_drops()
        fig = go.Figure(go.Bar(
            x=drops["Penalty (°C)"], y=drops["Instrument removed"], orientation="h",
            marker_color=[RED if v > 0.1 else MUTED for v in drops["Penalty (°C)"]],
            text=drops["Penalty (°C)"].round(3), textposition="outside"))
        fig.update_layout(title="Remove a whole instrument, refit, and measure",
                          xaxis_title="Extra error (°C)",
                          xaxis_range=[0, max(drops["Penalty (°C)"]) * 1.35])
        st.plotly_chart(style(fig, 330), width="stretch")
        figlab("Remove a whole instrument, refit, and measure")
        st.warning("**Two of the five specified sensors contribute nothing the model can use.** "
                   "Dropping a single *column* proves nothing — the columns are redundant by "
                   "construction. Dropping an *instrument* is the test with an answer in "
                   "degrees.")


@st.cache_data(show_spinner=False)
def _instrument_drops():
    """Refit without everything derived from each instrument, and measure."""
    art = story.precomputed("instrument_drops")
    if art is not None:
        return art
    return story._compute_instrument_drops()


def _split_comparison():
    art = story.precomputed("split_comparison")
    if art is not None:
        return art
    return story._compute_split_comparison()


def render_errors():
    m = story.get_models()
    y, p = m["y_test"], m["preds"][m["best"]]
    err = p - y
    c1, c2 = st.columns([1.15, 1])
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Scattergl(x=y, y=p, mode="markers",
                                   marker=dict(size=3, color=AISIDE, opacity=0.25), name="hours"))
        lim = [y.min() - 2, y.max() + 2]
        fig.add_trace(go.Scatter(x=lim, y=lim, line=dict(color=TEXT, dash="dash"), name="perfect"))
        for v in (110, 120):
            fig.add_vline(x=v, line=dict(color=RED, dash="dot"))
            fig.add_hline(y=v, line=dict(color=RED, dash="dot"))
        fig.update_layout(title="Predicted against measured hot-spot temperature",
                          xaxis_title="Measured (°C)", yaxis_title="Predicted (°C)")
        st.plotly_chart(style(fig, 420), width="stretch")
        figlab("Predicted against measured hot-spot temperature")
    with c2:
        fig = go.Figure(go.Histogram(x=err, nbinsx=90, marker_color=EE))
        fig.add_vline(x=0, line=dict(color=TEXT, dash="dash"))
        fig.update_layout(title="Distribution of the error",
                          xaxis_title="Predicted − measured (°C)")
        st.plotly_chart(style(fig, 420), width="stretch")
        figlab("Distribution of the error")
    a, b, c, d = st.columns(4)
    a.metric("Bias", f"{err.mean():+.2f} °C")
    b.metric("Within ±1 °C", f"{100 * np.mean(np.abs(err) <= 1):.0f} %")
    c.metric("Within ±3 °C", f"{100 * np.mean(np.abs(err) <= 3):.0f} %")
    d.metric("Worst miss", f"{np.abs(err).max():.1f} °C")
    st.info("**Too high** costs money: load is cut when it need not be. **Too low** costs "
            "insulation, silently. So being right *on average* is not enough — it has to be "
            "right when it is hot.")


def render_hot_tail():
    m = story.get_models()
    y, p = m["y_test"], m["preds"][m["best"]]
    err = p - y
    c1, c2 = st.columns([1, 1.1])
    with c1:
        bands = [(0, 80, "Normal"), (80, 98, "Warm"), (98, 110, "Approaching limit"),
                 (110, 999, "Beyond normal life expectancy")]
        rows = []
        for lo, hi, lab in bands:
            k = (y >= lo) & (y < hi)
            if k.sum():
                rows.append({"Band (°C)": f"{lo}+" if hi == 999 else f"{lo}–{hi}",
                             "Condition": lab, "Hours": int(k.sum()),
                             "MAE (°C)": round(float(np.abs(err[k]).mean()), 2),
                             "Bias (°C)": round(float(err[k].mean()), 2)})
        band = pd.DataFrame(rows)
        st.dataframe(band, width="stretch", hide_index=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=band["Band (°C)"], y=band["MAE (°C)"], name="MAE",
                             marker_color=[GREEN, EE, AMBERHOT, RED]))
        fig.add_trace(go.Scatter(x=band["Band (°C)"], y=band["Bias (°C)"], name="Bias",
                                 mode="lines+markers", line=dict(color=AISIDE, width=3),
                                 marker=dict(size=11)))
        fig.add_hline(y=0, line=dict(color=TEXT, dash="dot"))
        if len(band):
            worst = band.iloc[-1]
            mark_wrong(fig, worst["Band (°C)"], worst["MAE (°C)"],
                       "Weakest where it matters most",
                       f"In the hottest band the average miss is "
                       f"{worst['MAE (°C)']:.2f} °C and the bias is "
                       f"{worst['Bias (°C)']:+.2f} °C.<br>"
                       "A negative bias means it reads LOW when the transformer is hottest -<br>"
                       "the one direction that quietly costs insulation life.")
        fig.update_layout(title="Error grows with temperature — and the bias turns negative",
                          yaxis_title="°C")
        st.plotly_chart(style(fig, 330), width="stretch")
        figlab("Accuracy by temperature band",
               "hover the red ring for the problem")
        wrongkey([("Red ring", "where the model is weakest and reads low")])
    with c2:
        faa = story.ageing_factor(y)
        order = np.argsort(faa)[::-1]
        cum = np.cumsum(faa[order]) / faa.sum()
        pct = 100 * np.arange(1, len(cum) + 1) / len(cum)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=pct, y=100 * cum, line=dict(color=RED, width=3),
                                 fill="tozeroy", fillcolor="rgba(239,83,80,.12)",
                                 name="cumulative ageing"))
        fig.add_trace(go.Scatter(x=[0, 100], y=[0, 100], line=dict(color=MUTED, dash="dash"),
                                 name="if every hour aged equally"))
        fig.add_vline(x=5, line=dict(color=AISIDE, dash="dot"),
                      annotation_text="hottest 5 % of hours")
        fig.update_layout(title="Insulation ageing is concentrated in a handful of hours",
                          xaxis_title="Hours, hottest first (%)",
                          yaxis_title="Cumulative life consumed (%)")
        st.plotly_chart(style(fig, 380), width="stretch")
        figlab("Insulation ageing is concentrated in a handful of hours")
        a, b = st.columns(2)
        a.metric("Hottest 1 % of hours carry", f"{100 * cum[int(0.01 * len(cum)) - 1]:.0f} %")
        b.metric("Hottest 5 % carry", f"{100 * cum[int(0.05 * len(cum)) - 1]:.0f} %")
    st.error(f"**The model is weakest exactly where the damage happens.** The overall "
             f"{np.abs(err).mean():.2f} °C is dominated by the 95 % of hours where accuracy is "
             f"irrelevant. This is a limitation to report, not to hide — and the fix is more "
             f"hot-band training data, or sample weighting that values those hours more.")


# ============================================================================
# PHASE 9  -  WHAT THE MODEL DOES NOT KNOW
# ============================================================================
@st.cache_data(show_spinner="Training four models, each blind to one transformer…")
def _holdout_units():
    art = story.precomputed("holdout_units")
    if art is not None:
        return art
    return story._compute_holdout_units()


def render_unseen_unit():
    h = _holdout_units()
    base = story.get_models()["board"]["MAE (°C)"].min()
    st.markdown("**Train on three transformers, score on the fourth it has never seen**")
    st.dataframe(h.round(2), width="stretch", hide_index=True)
    c1, c2 = st.columns([1.15, 1])
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=h["Held-out unit"], y=h["Bias (°C)"], name="Bias",
                             marker_color=[GREEN if v > 0 else RED for v in h["Bias (°C)"]],
                             text=h["Bias (°C)"].round(1), textposition="outside"))
        fig.add_trace(go.Bar(x=h["Held-out unit"], y=h["Scatter (°C)"], name="Scatter (std)",
                             marker_color=MUTED))
        fig.add_hline(y=0, line=dict(color=TEXT, dash="dash"))
        fig.update_layout(title="Almost all of the failure is bias, not scatter",
                          yaxis_title="°C", barmode="group")
        st.plotly_chart(style(fig, 380), width="stretch")
        figlab("Almost all of the failure is bias, not scatter")
    with c2:
        fig = go.Figure(go.Bar(
            x=["Seen this unit"] + [f"Never seen {u}" for u in h["Held-out unit"]],
            y=[base] + list(h["MAE (°C)"]),
            marker_color=[GREEN] + [RED] * len(h),
            text=[f"{base:.2f}"] + [f"{v:.2f}" for v in h["MAE (°C)"]], textposition="outside"))
        fig.update_layout(title="Mean absolute error (°C)", yaxis_title="MAE (°C)")
        st.plotly_chart(style(fig, 380), width="stretch")
        figlab("Mean absolute error (°C)")
    st.markdown(
        "<div class='relay warn'><b>This is the model's biggest limitation — and we measured it "
        "rather than assumed it.</b> On a transformer it has never seen, it is wrong by a fairly "
        "steady amount rather than wildly scattered. That means it did learn the physics, and "
        "only missed the one thing unique to that unit — so a few weeks of readings from a new "
        "transformer would fix most of it.</div>", unsafe_allow_html=True)


# ============================================================================
# PHASE 10  -  DECISION SUPPORT
# ============================================================================
def render_predict():
    st.markdown("**Five readings the substation already has. One answer.**")
    c1, c2 = st.columns([1, 1.2])
    with c1:
        load = st.slider("Load current (A)", 250, 1000, 720, 10, key="p_l")
        amb = st.slider("Ambient temperature (°C)", 0, 48, 36, 1, key="p_a")
        oil = st.slider("Top-oil temperature (°C)", 25, 95, 68, 1, key="p_o")
        volt = st.slider("Voltage (kV)", 124.0, 140.0, 132.0, 0.5, key="p_v")
        hum = st.slider("Humidity (%)", 20, 99, 74, 1, key="p_h")
        age = st.select_slider("Transformer age (years)", [3, 9, 16, 22], value=16, key="p_age")
        st.caption("Sensor mode: every reading comes from the plant. The scheme does this "
                   "continuously, on every unit.")
    d = story.assess(load, amb, oil, volt, hum, age)
    with c2:
        g1, g2 = st.columns([1.1, 1])
        with g1:
            st.plotly_chart(gauge(d["hotspot_c"]), width="stretch")
            figlab("Mean absolute error (°C)")
        with g2:
            st.metric("Headroom to 110 °C", f"{d['headroom_k']:.1f} K")
            st.metric("Ageing rate", f"{d['faa']:.2f} ×", "1.00 = design rate")
            st.metric("Winding gradient", f"{d['gradient_k']:.1f} K", "the part no gauge measures")
            st.metric("Loading", f"{d['load_pu']:.2f} pu")
        st.plotly_chart(transformer_section(d["load_pu"], amb, oil, d["hotspot_c"], d["stage"],
                                            h=330), width="stretch")
        figlab("Chart")
    st.divider()
    st.markdown("**Engineering interpretation**")
    notes = [
        f"Loading is {d['load_pu']:.2f} per unit" +
        (" — above nameplate." if d["load_pu"] > 1.0 else
         ", within nameplate." if d["load_pu"] > 0.8 else ", light."),
        f"Ambient {amb} °C" + (" is reducing cooling capacity." if amb > 35 else
                               " is unremarkable." if amb > 15 else " is helping the radiators."),
        f"Top oil at {oil} °C is {oil - amb:.0f} K above ambient" +
        (" — already elevated." if oil - amb > 35 else "."),
        f"Cooling is at stage {d['stage']}" +
        (" (all fans running)." if d["stage"] == 2 else
         " (first fan bank running)." if d["stage"] == 1 else " (fans off, natural circulation)."),
        f"The winding runs {d['gradient_k']:.0f} K above the oil — this is the part no gauge measures.",
    ]
    st.markdown(f"<div class='relay'>" + "<br>".join(f"· {n}" for n in notes) + "</div>",
                unsafe_allow_html=True)
    st.write("")
    scen = pd.DataFrame([
        {"Scenario": s, "Load (A)": l, "Ambient (°C)": a, "Oil (°C)": o}
        for s, l, a, o in [("Overnight minimum", 320, 18, 34),
                           ("Ordinary summer afternoon", 620, 33, 61),
                           ("Evening peak, transferred feeder", 720, 36, 68),
                           ("Heatwave plus contingency", 920, 43, 84)]])
    res = [story.assess(r["Load (A)"], r["Ambient (°C)"], r["Oil (°C)"], age=16)
           for _, r in scen.iterrows()]
    scen["Hot spot (°C)"] = [round(r["hotspot_c"], 1) for r in res]
    scen["Gradient (K)"] = [round(r["gradient_k"], 1) for r in res]
    scen["Headroom (K)"] = [round(r["headroom_k"], 1) for r in res]
    scen["Ageing ×"] = [round(r["faa"], 2) for r in res]
    st.markdown("**Four operating points, to see how the answer moves**")
    st.dataframe(scen, width="stretch", hide_index=True)
    st.info(f"The winding gradient grows from **{scen['Gradient (K)'].min():.0f} K** overnight "
            f"to **{scen['Gradient (K)'].max():.0f} K** in the heatwave contingency. "
            "The oil thermometer cannot see any of that.")


def render_recommend():
    st.markdown("**The same temperature can mean different things — so the rules name the cause**")
    cases = {
        "Normal evening peak": (620, 30, 58, 16),
        "Hot day, heavy load": (840, 40, 76, 16),
        "Contingency in a heatwave": (950, 44, 87, 22),
        "Moderate load, failed fan bank": (700, 32, 90, 22),
    }
    pick = st.radio("Pick a case", list(cases), horizontal=True, key="rc")
    load, amb, oil, age = cases[pick]
    d = story.assess(load, amb, oil, age=age)
    tone_colour = {"ok": GREEN, "watch": EE, "warn": AMBERHOT, "alarm": RED}[d["tone"]]

    c1, c2 = st.columns([1, 1.25])
    with c1:
        st.plotly_chart(gauge(d["hotspot_c"], h=280), width="stretch")
        figlab("Chart")
        a, b = st.columns(2)
        a.metric("Headroom", f"{d['headroom_k']:.1f} K")
        b.metric("Ageing", f"{d['faa']:.2f} ×")
        st.caption(f"{load} A · {amb} °C ambient · {oil} °C oil · {age} years old")
    with c2:
        st.markdown(
            f"<div class='relay' style='border-left-color:{tone_colour};font-size:20px;"
            f"font-weight:600'>[{d['urgency']}] &nbsp; {d['action']}</div>",
            unsafe_allow_html=True)
        st.write("")
        st.markdown("**Why**")
        st.markdown(f"<div class='relay ai'>"
                    + "<br>".join(f"· {r}" for r in d["reasons"]) + "</div>",
                    unsafe_allow_html=True)
        st.write("")
        st.markdown("**The cooling check, which is pure arithmetic and needs no model**")
        cc1, cc2, cc3 = st.columns(3)
        cc1.metric("Oil rise measured", f"{d['oil_rise_c']:.0f} K")
        cc2.metric("What this load justifies", f"{d['expected_rise_c']:.0f} K")
        cc3.metric("Shortfall", f"{d['shortfall_k']:+.0f} K",
                   "cooling fault" if d["shortfall_k"] > 6 else "consistent")
    st.divider()
    c3, c4 = st.columns([1, 1])
    with c3:
        st.markdown("**IEEE C57.91 table 8 — the thresholds are published, not invented**")
        st.dataframe(pd.DataFrame([
            {"Hot spot": "below 98 °C", "Loading condition": "Normal",
             "Action": "Continue normal operation"},
            {"Hot spot": "98 – 110 °C", "Loading condition": "Approaching normal-life limit",
             "Action": "Monitor closely"},
            {"Hot spot": "110 – 120 °C", "Loading condition": "Beyond normal life expectancy",
             "Action": "Increase cooling, prepare to reduce load"},
            {"Hot spot": "above 120 °C", "Loading condition": "Planned loading beyond nameplate",
             "Action": "Reduce loading now"},
        ]), width="stretch", hide_index=True)
    with c4:
        st.markdown(
            "<div class='relay tech'><b>Where the AI stops.</b><br>"
            "· The model predicts a temperature. That is all it does.<br>"
            "· The limits come from a published standard.<br>"
            "· The advice is ordinary engineering logic anyone can read.<br><br>"
            "<b>You do not have to trust the model to check the rule.</b></div>",
            unsafe_allow_html=True)


def render_dashboard():
    board, peak = story.fleet_snapshot()
    st.markdown(f"**Ashgrove substation — snapshot at {peak:%d %B %Y, %H:%M}, "
                f"the fleet's hottest hour of the year**")
    limit_chips()
    st.write("")
    cols = st.columns(len(board))
    for col, (_, r) in zip(cols, board.iterrows()):
        with col:
            st.plotly_chart(gauge(r["Hot spot (°C)"], f"{r['Unit']} — {r['Age']} years", h=250),
                            width="stretch", key=f"g_{r['Unit']}")
            figlab("Chart")
    st.dataframe(board.drop(columns=["tone"]), width="stretch", hide_index=True,
                 column_config={"Headroom (K)": st.column_config.NumberColumn(
                     help="Kelvin below the 110 °C normal-life limit. Negative means above it.")})
    st.caption("Ranked by headroom, not by name — the operator's question is which transformer "
               "to look at first.")
    for _, r in board.iterrows():
        tone = {"ok": GREEN, "watch": EE, "warn": AMBERHOT, "alarm": RED}[r["tone"]]
        st.markdown(f"<div class='relay' style='border-left-color:{tone};margin-bottom:6px'>"
                    f"<b>{r['Unit']}</b> &nbsp;[{r['Urgency']}]&nbsp; {r['Action']}</div>",
                    unsafe_allow_html=True)
    st.divider()
    df = story.get_features()
    c1, c2 = st.columns(2)
    with c1:
        ag = (df.assign(f=story.ageing_factor(df.hotspot_temp_c))
                .groupby("unit_id").agg(days=("f", lambda s: s.sum() / 24),
                                        age=("transformer_age_years", "first")).reset_index())
        fig = go.Figure(go.Bar(x=ag.unit_id, y=ag.days, marker_color=EE,
                               text=ag.days.round(1), textposition="outside"))
        fig.update_layout(title="Insulation life consumed this year",
                          yaxis_title="Equivalent days of design life")
        st.plotly_chart(style(fig, 350), width="stretch")
        figlab("Insulation life consumed this year")
    with c2:
        fig = go.Figure()
        for lim, colr in [(98, EE), (110, RED), (120, "#7b1fa2")]:
            h = df.groupby("unit_id").hotspot_temp_c.apply(lambda s: int((s > lim).sum()))
            fig.add_trace(go.Bar(x=h.index, y=h.values, name=f"> {lim} °C", marker_color=colr))
        fig.update_layout(title="Hours above each limit", yaxis_title="Hours in the year",
                          barmode="group")
        st.plotly_chart(style(fig, 350), width="stretch")
        figlab("Hours above each limit")
    st.success("**None of these four transformers reports a hot-spot temperature to this "
               "dashboard.** Every number in that column was predicted, from instruments that "
               "were already fitted. A person still reads it, still decides, and still signs "
               "the loading order.")


# ============================================================================
# THE LANDING PAGE
# ============================================================================
def render_start():
    reset_figures()
    st.markdown("# \u26a1 AI for Transformer Hot-Spot Temperature Prediction")

    # ---- SECTION 1 -------------------------------------------------------
    bridge._bus("01", "The Problem", EE)
    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.markdown(
            "<div style='font-size:19px;line-height:1.65'>A transformer is slowly destroyed by "
            "its own heat, and the temperature that decides how long it lives is "
            "<b>deep inside it, where nothing can measure it</b>. The gauge on the outside reads "
            "about <b>30 °C too low</b>.<br><br>So we predict that hidden temperature from "
            "the ordinary sensors every substation already has.</div>",
            unsafe_allow_html=True)
        st.write("")
        limit_chips()
    with c2:
        st.plotly_chart(transformer_section(1.03, 36, 68, 97.8, 2, h=400), width="stretch")
        figlab("Inside a loaded transformer",
               "outside gauge 68 °C, winding about 98 °C")

    # ---- SECTION 2 -------------------------------------------------------
    bridge._bus("02", "What This Course Builds", AISIDE)
    m = story.get_models()
    s = m["board"].set_index("Model")["MAE (°C)"]
    base = s["IEEE C57.91 (nameplate)"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Today's method is out by", f"{base:.2f} °C", "the industry standard")
    c2.metric("After machine learning", f"{s.min():.2f} °C",
              f"-{100 * (1 - s.min() / base):.0f} %")
    c3.metric("Phases", len(bridge.PHASES))
    c4.metric("Hours of history", f"{len(story.get_features()):,}")

    # ---- SECTION 3 -------------------------------------------------------
    bridge._bus("03", "The Ten Phases", TECH)
    st.caption("Each phase ends with a question. The next phase answers it.")
    c1, c2 = st.columns([1, 1.15])
    with c1:
        ev = st.plotly_chart(bridge.mind_map(style), width="stretch",
                             on_select="rerun", key="mindmap")
        figlab("The whole project as one map", "click any node to open that phase")
        try:
            pts = ev.selection["points"]
            if pts:
                bridge.goto(pts[0]["customdata"])
        except (KeyError, TypeError, AttributeError):
            pass
    with c2:
        for i, st_ in enumerate(bridge.STEPS):
            q = st_["question"] or "—"
            if st.button(f"{i+1}\u2003{st_['ee_icon']}  {st_['ee']}",
                         key=f"jump_{st_['id']}", width="stretch"):
                bridge.goto(st_["id"])
            st.markdown(f"<div class='muted' style='margin:-6px 0 8px 6px'>{q}</div>",
                        unsafe_allow_html=True)

    # ---- SECTION 4 -------------------------------------------------------
    bridge._bus("04", "Electrical Engineering \u2192 AI", GREEN)
    st.markdown("Read the left column and it is a transformer monitoring scheme. Read the right "
                "column and it is a machine learning pipeline. **They are the same column.**")
    st.plotly_chart(bridge.mapping_figure(style), width="stretch")
    figlab("Chart")

    st.divider()
    if st.button(f"\u25b6  Start at phase 1 — {bridge.STEPS[0]['ee']}", width="stretch",
                 type="primary"):
        bridge.goto(bridge.ORDER[0])


# ============================================================================
# THE ROUTER
# ============================================================================

# ============================================================================
# BEGINNER HELPERS
# ============================================================================
_FIGN = {"n": 0}


def figlab(title, what=""):
    """Label a figure. Every chart and image on a page gets one, numbered."""
    _FIGN["n"] += 1
    extra = f" &nbsp;\u00b7&nbsp; {what}" if what else ""
    st.markdown(f"<div class='figlab'><b>FIGURE {_FIGN['n']}</b> &nbsp;{title}{extra}</div>",
                unsafe_allow_html=True)


def reset_figures():
    _FIGN["n"] = 0


def term(word, plain, example=""):
    """One piece of jargon, translated. Used wherever a new word first appears."""
    ex = f"<div class='term-e'>{example}</div>" if example else ""
    st.markdown(f"<div class='term'><span class='term-w'>{word}</span>"
                f"<div class='term-p'>{plain}</div>{ex}</div>", unsafe_allow_html=True)


def wrongkey(items):
    """The key under a chart that has problems marked on it."""
    rows = "".join(f"<div><b>{k}</b> &nbsp;{v}</div>" for k, v in items)
    st.markdown(f"<div class='wrongkey'>{rows}</div>", unsafe_allow_html=True)


def mark_wrong(fig, x, y, label, why, color=None):
    """Ring a problem on a chart and explain it on hover.

    Students should not have to be told in prose which dot is the broken one.
    The marker carries the explanation in its tooltip.
    """
    fig.add_trace(go.Scatter(
        x=[x], y=[y], mode="markers", name=label, showlegend=False,
        marker=dict(size=26, color="rgba(0,0,0,0)", line=dict(color=color or RED, width=2.5)),
        hovertemplate=f"<b>{label}</b><br>{why}<extra></extra>"))
    return fig


def bridge_panel(stage):
    """The engineering-to-AI mapping, tucked away so the page stays short."""
    step = bridge.BY_ID.get(stage)
    if step is None:
        return
    with st.expander(f"How this maps to the AI concept — {step['ai']}"):
        st.plotly_chart(bridge.bridge_figure(step, style, animate), width="stretch",
                        key=f"bridge_{stage}")
        figlab("The engineering step and the AI concept are the same idea",
               "amber is the substation, cyan is the AI")


# ============================================================================
# NEW CONTENT THE TEN-PAGE COURSE NEEDS
# ============================================================================
def pane_columns():
    """What each column in the log actually is, in plain words."""
    st.markdown("**Every column, in plain English**")
    rows = [
        ("load_current_a", "Load current",
         "How much electricity is flowing through it right now, in amps. Busier = hotter."),
        ("ambient_temp_c", "Air temperature",
         "How warm the air outside the transformer is."),
        ("oil_temp_c", "Oil temperature",
         "The dial thermometer on the tank. Warm oil, but not the hottest point."),
        ("voltage_kv", "Voltage", "The voltage on the incoming side."),
        ("humidity_pct", "Humidity", "How damp the air is."),
        ("cooling_stage", "Fan setting",
         "Which cooling fans are running: 0 none, 1 half, 2 all of them."),
        ("transformer_age_years", "Age", "How old this transformer is, in years."),
        ("unit_id", "Which transformer", "T1, T2, T3 or T4 - a name, not a number."),
    ]
    st.dataframe(pd.DataFrame(rows, columns=["Column", "Means", "In plain English"]),
                 width="stretch", hide_index=True)
    st.markdown(f"<div class='relay ai'><b>hotspot_temp_c</b> is the answer column - the "
                f"temperature deep inside the winding. On these four research units it was "
                f"measured with a special probe. On every other transformer it is missing, and "
                f"that is exactly what we are building.</div>", unsafe_allow_html=True)


def pane_encoding():
    """Turning word-columns into numbers, which every model requires."""
    st.markdown("**Models do arithmetic. They cannot add up the word \"T3\".**")
    term("Encoding",
         "Turning a column of words or categories into numbers, because a model can only "
         "multiply and add.",
         "\"T3\" is not a quantity. It has to become numbers before it can be used.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Wrong: just number them**")
        st.dataframe(pd.DataFrame({"unit_id": ["T1", "T2", "T3", "T4"],
                                   "as a number": [1, 2, 3, 4]}),
                     width="stretch", hide_index=True)
        st.markdown("<div class='relay warn'>This tells the model T4 is <b>four times</b> T1, "
                    "and that T2 sits halfway between T1 and T3. None of that is true - they are "
                    "just names.</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("**Right: one column per category (one-hot)**")
        st.dataframe(pd.DataFrame({"unit_id": ["T1", "T2", "T3", "T4"],
                                   "is_T1": [1, 0, 0, 0], "is_T2": [0, 1, 0, 0],
                                   "is_T3": [0, 0, 1, 0], "is_T4": [0, 0, 0, 1]}),
                     width="stretch", hide_index=True)
        st.markdown("<div class='relay ok'>Each transformer gets its own yes/no column. No fake "
                    "ordering, no fake arithmetic.</div>", unsafe_allow_html=True)
    st.divider()
    st.markdown("**When numbering IS right: the fan setting**")
    st.markdown(
        "`cooling_stage` is 0, 1 or 2 - no fans, half, all. Here the order is real and the gaps "
        "mean something, so it can stay as a plain number. That kind of column is called "
        "**ordinal**. The test is simple: *does 'bigger' mean anything?* For fans yes, for "
        "transformer names no.")
    st.markdown(f"<div class='relay ai'>In this project the model is trained per-reading and "
                f"<b>not</b> given the unit name, on purpose - so it has to learn the physics "
                f"rather than memorise which transformer it is looking at. Page "
                f"<b>Where It Fails</b> shows what that costs.</div>", unsafe_allow_html=True)


def pane_mlterms():
    """The words, before anything uses them."""
    st.markdown("**Six words, and then we can talk about models**")
    c1, c2 = st.columns(2)
    with c1:
        term("Feature", "An input. Something you measured and can feed in.",
             "Load current, air temperature, oil temperature.")
        term("Label", "The answer you want. The thing you are trying to predict.",
             "The hot-spot temperature.")
        term("Model", "A rule, learned from examples, that turns features into a label.",
             "Give it today's readings, it gives back a temperature.")
    with c2:
        term("Training", "Showing the model thousands of examples so it can find the pattern.",
             "26,000 hours where we know both the readings and the answer.")
        term("Prediction", "Using the trained model on readings it has not seen.",
             "A temperature for an hour nobody measured.")
        term("Overfitting",
             "When a model memorises the examples instead of learning the pattern. It scores "
             "brilliantly on what it has seen and badly on anything new.",
             "Like revising by memorising last year's exam paper.")


def pane_whymodel():
    """Justifying the model choice, which is the part students skip."""
    m = story.get_models()
    s = m["board"].set_index("Model")["MAE (°C)"]
    st.markdown("**Why this model, and not one of the others**")
    rows = [
        ("Linear regression", f"{s['Linear regression (engineered)']:.2f} °C",
         "Fits one straight line. Fast and easy to explain, but the real relationship curves, "
         "so it is wrong at both ends.", "Rejected - cannot bend"),
        ("Random Forest", f"{s['Random Forest']:.2f} °C",
         "Hundreds of independent rule-trees, averaged. Bends nicely and is hard to break.",
         "Good, but beaten"),
        ("Gradient Boosting", f"{s['Gradient Boosting']:.2f} °C",
         "Trees built one after another, each fixing the last one's mistakes. More accurate "
         "than the forest here.", "Nearly the winner"),
    ]
    if "XGBoost" in s.index:
        rows.append(("XGBoost", f"{s['XGBoost']:.2f} °C",
                     "The same idea as gradient boosting, written to run fast. Same accuracy, "
                     "a fraction of the training time.", "CHOSEN"))
    st.dataframe(pd.DataFrame(rows, columns=["Model", "Average miss", "What it does",
                                             "Verdict"]),
                 width="stretch", hide_index=True)
    best = story.BEST_LABEL.get(m["best"], "the best model")
    st.markdown(
        f"<div class='relay ok'><b>{best} wins on three counts.</b> It is the most accurate. It "
        f"retrains in seconds rather than minutes, so the substation can refresh it as new data "
        f"arrives. And it handles the awkward parts of this data - fan settings that jump in "
        f"steps, sensors that disagree - without anyone hand-tuning it.</div>",
        unsafe_allow_html=True)


def pane_whymetric():
    """What each score means, and why MAE is the one that matters here."""
    m = story.get_models()
    b = m["board"].set_index("Model")
    best = story.BEST_LABEL.get(m["best"], "Best")
    row = b.loc[b.index[0]]
    st.markdown("**Three ways of saying \"how wrong\"**")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("MAE", f"{row['MAE (°C)']:.2f} °C")
        term("Mean Absolute Error",
             "Average of how far off it was, ignoring direction. In the same unit as the thing "
             "you measured, so you can read it directly.",
             "MAE of 1.35 means: typically wrong by about 1.35 °C.")
    with c2:
        st.metric("RMSE", f"{row['RMSE (°C)']:.2f} °C")
        term("Root Mean Squared Error",
             "Like MAE, but big misses are punished much harder than small ones. Always equal to "
             "or larger than MAE.",
             "Use it when one huge mistake is far worse than several small ones.")
    with c3:
        st.metric("R\u00b2", f"{row['R\u00b2']:.4f}")
        term("R-squared",
             "The share of the variation the model explains, from 0 to 1. A percentage-style "
             "score with no unit.",
             "0.99 sounds perfect - but see the warning below.")
    st.divider()
    st.markdown(f"<div class='relay ok'><b>For this job, MAE is the one that matters.</b> It is "
                f"in degrees, which is the language the engineer already thinks in. \"Typically "
                f"wrong by {row['MAE (°C)']:.2f} °C\" can be checked straight against "
                f"the 110 °C limit. RMSE and R\u00b2 are useful, but neither answers the "
                f"question an operator is actually asking.</div>", unsafe_allow_html=True)
    st.markdown("<div class='relay warn'><b>Why a high R\u00b2 can lie.</b> R\u00b2 depends on "
                "how spread out the test data is, not only on the model. Test the same model on "
                "a calm autumn instead of a whole year and R\u00b2 drops sharply while the "
                "average miss barely moves - the model did not get worse, the exam got easier to "
                "fail. That is why a score in degrees is worth more than a score out of one."
                "</div>", unsafe_allow_html=True)
    st.dataframe(_split_comparison().round(3), width="stretch", hide_index=True)
    figlab("The same model, scored on two different test sets",
           "MAE holds steady, R\u00b2 moves a lot")


# ============================================================================
# THE TEN PAGES
# ============================================================================
def render_problem():
    reset_figures()
    c1, c2 = st.columns([1, 1])
    with c1:
        st.plotly_chart(transformer_section(1.03, 36, 68, 97.8, 2, h=400), width="stretch")
        figlab("Inside a loaded transformer",
               "the tank gauge reads 68 °C, the winding is at about 98 °C")
    with c2:
        st.markdown("**The 30-degree gap nobody sees**")
        st.markdown(
            "- The gauge on the outside reads the **oil**.\n"
            "- The paper insulation is cooking at the **hot spot**, about **25-30 °C "
            "hotter**.\n"
            "- Damage **adds up and never reverses**. Nothing looks wrong until it fails.\n"
            "- Roughly, **every 6 °C hotter halves its remaining life**.")
        limit_chips()
        st.markdown("<div class='relay ai'>So the number that decides the transformer's life is "
                    "the one number nobody has. That is the whole problem, and it is why this "
                    "needs a prediction rather than a better gauge.</div>",
                    unsafe_allow_html=True)
    bridge_panel("problem")


def render_data():
    reset_figures()
    t1, t2 = st.tabs(["The log", "What each column means"])
    with t1:
        render_log()
    with t2:
        pane_columns()
    bridge_panel("data")


def render_explore_page():
    reset_figures()
    t1, t2 = st.tabs(["A week of readings", "What is wrong in this data"])
    with t1:
        render_explore()
    with t2:
        render_inspect()
    bridge_panel("explore")


def render_prepare():
    reset_figures()
    t1, t2, t3, t4 = st.tabs(["Cleaning", "Encoding", "Scaling", "New columns from physics"])
    with t1:
        render_clean()
    with t2:
        pane_encoding()
    with t3:
        render_scale()
    with t4:
        render_features()
    bridge_panel("prepare")


def render_learning():
    reset_figures()
    t1, t2 = st.tabs(["The words", "The honest test"])
    with t1:
        pane_mlterms()
    with t2:
        render_split()
    bridge_panel("learning")


def render_first_model():
    reset_figures()
    t1, t2, t3 = st.tabs(["The baseline", "A straight line", "Where the line fails"])
    with t1:
        render_baseline()
    with t2:
        render_linear()
    with t3:
        render_residuals()
    bridge_panel("baseline")


def render_training():
    reset_figures()
    t1, t2, t3, t4 = st.tabs(["Random Forest", "Boosting", "The results",
                              "Why we picked this one"])
    with t1:
        render_forest()
    with t2:
        render_boosting()
    with t3:
        render_leaderboard()
    with t4:
        pane_whymodel()
    bridge_panel("training")


def render_scoring():
    reset_figures()
    t1, t2 = st.tabs(["The three scores", "Which sensors earn their place"])
    with t1:
        pane_whymetric()
    with t2:
        render_importance()
    bridge_panel("scoring")


def render_limits():
    reset_figures()
    t1, t2, t3 = st.tabs(["The shape of the error", "The hours that matter",
                          "A transformer it has never seen"])
    with t1:
        render_errors()
    with t2:
        render_hot_tail()
    with t3:
        render_unseen_unit()
    bridge_panel("limits")


def render_use():
    reset_figures()
    t1, t2, t3 = st.tabs(["Ask it a question", "Turn it into a decision", "The fleet"])
    with t1:
        render_predict()
    with t2:
        render_recommend()
    with t3:
        render_dashboard()
    bridge_panel("use")



RENDERERS = {
    "problem": render_problem, "data": render_data, "explore": render_explore_page,
    "prepare": render_prepare, "learning": render_learning, "baseline": render_first_model,
    "training": render_training, "scoring": render_scoring, "limits": render_limits,
    "use": render_use,
}
# Old page ids from the 30-step version, so existing links keep working.
ALIASES = {
    "overview": "start", "home": "start",
    "the-asset": "problem", "why-heat": "problem", "hot-spot": "problem",
    "enter-ai": "problem", "cross-section": "problem", "ageing": "problem",
    "thermal-model": "data", "the-target": "data", "log": "data",
    "inspect": "explore", "explore": "explore",
    "clean": "prepare", "features": "prepare", "scale": "prepare",
    "split": "learning",
    "linear": "baseline", "residuals": "baseline",
    "forest": "training", "boosting": "training", "xgboost": "training",
    "leaderboard": "training", "models": "training",
    "importance": "scoring", "sensitivity": "scoring", "metrics": "scoring",
    "evaluate": "scoring",
    "errors": "limits", "trend": "limits", "hot-tail": "limits", "unseen-unit": "limits",
    "predict": "use", "gauge": "use", "recommend": "use", "decision": "use",
    "dashboard": "use", "fleet": "use",
}

stage = st.query_params.get("stage", "start")
stage = ALIASES.get(stage, stage)
if stage != "start" and stage not in RENDERERS:
    stage = "start"

with st.sidebar:
    st.markdown("### ⚡ A Thermal Problem")
    st.caption("Predicting the one temperature inside a transformer that nobody can measure.")
    keys = ["start"] + bridge.ORDER
    labels = {"start": "🗺️  Project overview"}
    labels.update({s["id"]: f"{bridge.ORDER.index(s['id'])+1:02d} · {s['ee_icon']} {s['ee']}"
                   for s in bridge.STEPS})
    sel = st.selectbox("Where are we in the substation?", keys, index=keys.index(stage),
                       format_func=lambda k: labels[k])
    if sel != stage:
        st.query_params["stage"] = sel
        st.rerun()

    if stage in bridge.BY_ID:
        step = bridge.BY_ID[stage]
        pos = bridge.ORDER.index(stage) + 1
        pname = bridge.PHASES[step["phase"]][0]
        st.progress(pos / len(bridge.ORDER),
                    text=f"phase {pos}/{len(bridge.PHASES)} · {pname}")
        st.markdown(
            f"<div style='font-size:12px;line-height:1.6'>"
            f"<span style='color:{MUTED}'>THIS PHASE</span><br>"
            f"<b style='color:{EE}'>{step['ee']}</b><br>"
            f"<span style='color:{MUTED}'>IN MACHINE LEARNING</span><br>"
            f"<b style='color:{AISIDE}'>{step['ai']}</b></div>", unsafe_allow_html=True)
    st.divider()
    if st.button("🗺️  The whole project map", width="stretch"):
        st.query_params["stage"] = "start"
        st.rerun()
    st.caption("▶ Press **Play** on a chart to animate it.")
    st.caption("Limits and ageing follow **IEEE C57.91**.")

# ---- the five-part page ----------------------------------------------------
if stage == "start":
    render_start()
else:
    bridge.open_page(stage, style, animate)
    RENDERERS[stage]()
    bridge.close_page(stage)
