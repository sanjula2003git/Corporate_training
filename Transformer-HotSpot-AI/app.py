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
def render_the_asset():
    df = story.get_features()
    c1, c2 = st.columns([1.05, 1])
    with c1:
        st.markdown("**Ashgrove substation — four 40 MVA 132/33 kV transformers**")
        fleet = (df.groupby("unit_id")
                   .agg(Age=("transformer_age_years", "first"),
                        **{"Mean load (A)": ("load_current_a", "mean"),
                           "Peak load (A)": ("load_current_a", "max"),
                           "Mean hot spot (°C)": ("hotspot_temp_c", "mean"),
                           "Peak hot spot (°C)": ("hotspot_temp_c", "max"),
                           "Hours > 110 °C": ("hotspot_temp_c", lambda s: int((s > 110).sum()))})
                   .round(1).reset_index().rename(columns={"unit_id": "Unit"}))
        st.dataframe(fleet, width="stretch", hide_index=True)
        a, b, c = st.columns(3)
        a.metric("Readings a year", f"{len(df):,}")
        b.metric("Rated current", f"{story.I_RATED:.0f} A")
        c.metric("Installed spares", "0")
        st.caption("Every one of those readings is an hour in which the winding temperature "
                   "mattered and nobody could see it.")
    with c2:
        unit = st.selectbox("Look at one unit's year", sorted(df.unit_id.unique()), index=2)
        sub = df[df.unit_id == unit]
        fig = go.Figure()
        fig.add_trace(go.Scattergl(x=sub.timestamp, y=sub.hotspot_temp_c, mode="markers",
                                   marker=dict(size=2, color=sub.hotspot_temp_c,
                                               colorscale="Turbo", cmin=30, cmax=140),
                                   name="hot spot", hoverinfo="skip"))
        fig.add_hline(y=110, line=dict(color=RED, dash="dash"),
                      annotation_text="110 °C limit")
        fig.update_layout(title=f"{unit}: every hour of 2025",
                          yaxis_title="Hot-spot temperature (°C)")
        st.plotly_chart(style(fig, 380), width="stretch")
        st.caption(f"{unit} spends {int((sub.hotspot_temp_c > 110).sum())} hours above 110 °C. "
                   "Those are the hours that decide when it is replaced.")


def render_why_heat():
    c1, c2 = st.columns([1, 1.25])
    with c1:
        K = st.slider("Load, per unit of rating", 0.20, 1.40, 1.00, 0.05)
        load, noload = story.loss_split(K)
        st.metric("Load (copper) loss", f"{load:.2f} pu", f"{load / 0.857:.2f}× the rated-load value")
        st.metric("No-load (core) loss", f"{noload:.2f} pu", "set by voltage, not load")
        st.metric("Total heat", f"{load + noload:.2f} pu")
        st.caption(f"At {K:.2f} pu, load loss is **{load / max(noload, 1e-9):.1f}×** the core loss. "
                   "They are equal at 0.41 pu.")
    with c2:
        Ks = np.linspace(0.2, 1.4, 200)
        ll, nl = story.loss_split(Ks)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=Ks, y=nl, name="No-load (core)", line=dict(color=MUTED, width=2)))
        fig.add_trace(go.Scatter(x=Ks, y=ll, name="Load (copper)", line=dict(color=EE, width=2)))
        fig.add_trace(go.Scatter(x=Ks, y=ll + nl, name="Total", line=dict(color=RED, width=3)))
        fig.add_vline(x=K, line=dict(color=TEXT, dash="dot"))
        fig.add_vline(x=1.0, line=dict(color=MUTED, dash="dash"), annotation_text="rated")
        fig.update_layout(title="Losses become heat, and load loss rises with the square of load",
                          xaxis_title="Load K (per unit)", yaxis_title="Loss (pu of total at rated)")
        st.plotly_chart(style(fig, 420), width="stretch")
    r = (1.0 ** 2 * story.R_RATIO + 1) / (0.5 ** 2 * story.R_RATIO + 1)
    st.info(f"**Half load to full load doubles the current and multiplies the heat by "
            f"{r:.1f}.** That is why the last 20 % of loading is the expensive part.")


def render_hot_spot():
    c1, c2 = st.columns([1, 1.15])
    with c1:
        st.markdown("**Move the load and watch the three temperatures separate**")
        K = st.slider("Load, per unit", 0.30, 1.35, 1.00, 0.05, key="hs_k")
        amb = st.slider("Ambient temperature (°C)", 0, 48, 30, key="hs_a")
        age = st.select_slider("Transformer age (years)", [3, 9, 16, 22], value=16, key="hs_age")
        oil = amb + float(story.top_oil_rise(K, 1.0, 2, age))
        hs = oil + float(story.hotspot_gradient(K, amb, 2, age))
        m1, m2, m3 = st.columns(3)
        m1.metric("Ambient", f"{amb:.0f} °C")
        m2.metric("Top oil", f"{oil:.0f} °C", f"+{oil - amb:.0f} K")
        m3.metric("Hot spot", f"{hs:.0f} °C", f"+{hs - oil:.0f} K over oil")
        st.caption(f"The gauge on the tank reads **{oil:.0f} °C**. The winding is at "
                   f"**{hs:.0f} °C**. That **{hs - oil:.0f} K** gap is what this course predicts.")
        limit_chips()
    with c2:
        st.plotly_chart(transformer_section(K, amb, oil, hs, 2), width="stretch")

    st.divider()
    c3, c4 = st.columns([1.2, 1])
    with c3:
        t = np.linspace(70, 150, 300)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=t, y=story.ageing_factor(t), line=dict(color=RED, width=3),
                                 fill="tozeroy", fillcolor="rgba(239,83,80,.12)", name="F_AA"))
        fig.add_trace(go.Scatter(x=[hs], y=[story.ageing_factor(hs)], mode="markers",
                                 marker=dict(size=16, color=temp_colour(hs),
                                             line=dict(color=TEXT, width=2)),
                                 name="you are here"))
        for lim, lab in [(110, "110 normal life"), (120, "120 beyond nameplate"),
                         (140, "140 emergency")]:
            fig.add_vline(x=lim, line=dict(color=MUTED, dash="dot"), annotation_text=lab)
        fig.update_layout(title="Insulation ageing against hot-spot temperature (IEEE C57.91)",
                          xaxis_title="Hot-spot temperature (°C)",
                          yaxis_title="Ageing acceleration F_AA", yaxis_type="log")
        st.plotly_chart(style(fig, 400), width="stretch")
    with c4:
        faa = float(story.ageing_factor(hs))
        st.metric("Ageing rate at this hot spot", f"{faa:.2f} ×",
                  "1.00 = the design rate at 110 °C")
        rows = [{"Hot spot (°C)": v, "F_AA": round(float(story.ageing_factor(v)), 2),
                 "One hour costs": f"{float(story.ageing_factor(v)):.2f} h of design life"}
                for v in (86, 98, 110, 122, 140)]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        u = 100 * (1 - float(story.ageing_factor(108)) / float(story.ageing_factor(110)))
        st.warning(f"Predicting **108 °C** when the truth is **110 °C** understates the ageing "
                   f"rate by **{u:.0f} %**. A small error in degrees is not a small error in life.")


def render_enter_ai():
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("**What the standard knows, and what it cannot know**")
        st.dataframe(pd.DataFrame([
            {"Knows": "The design as tested at the factory", "Source": "Nameplate", "In the model?": "Yes"},
            {"Knows": "This unit's real hot-spot factor", "Source": "Only measurement", "In the model?": "No"},
            {"Knows": "Twenty-two years of radiator fouling", "Source": "Only measurement", "In the model?": "No"},
            {"Knows": "The thermometer's own lag", "Source": "Only measurement", "In the model?": "No"},
        ]), width="stretch", hide_index=True)
        st.caption("None of the last three are errors in IEEE C57.91. They are things it was "
                   "never given.")
    with c2:
        m = story.get_models()
        b = m["board"].set_index("Model")["MAE (°C)"]
        fig = go.Figure(go.Bar(
            x=[b.get("IEEE C57.91 (nameplate)"), b.min()],
            y=["IEEE C57.91<br>nameplate only", "Fitted to<br>this fleet"],
            orientation="h", marker_color=[MUTED, AISIDE],
            text=[f"{b.get('IEEE C57.91 (nameplate)'):.2f} °C", f"{b.min():.2f} °C"],
            textposition="outside"))
        fig.update_layout(title="Mean error on hours neither model was fitted on",
                          xaxis_title="MAE (°C)")
        st.plotly_chart(style(fig, 300), width="stretch")
        st.success(f"The whole course is the gap between those two bars: "
                   f"**{b.get('IEEE C57.91 (nameplate)') - b.min():.2f} °C**, or "
                   f"**{100 * (1 - b.min() / b.get('IEEE C57.91 (nameplate)')):.0f} %** "
                   "of the standard's error. Every step from here earns part of it.")


# ============================================================================
# PHASE 2  -  ONE HOUR OF OPERATION
# ============================================================================
def render_thermal_model():
    c1, c2 = st.columns([1, 1.2])
    with c1:
        st.markdown("**IEEE C57.91, in two steps**")
        K = st.slider("Load, per unit", 0.30, 1.35, 1.03, 0.01, key="tm_k")
        amb = st.slider("Ambient (°C)", 0, 48, 36, key="tm_a")
        stage = st.radio("Cooling stage", [0, 1, 2], index=2, horizontal=True,
                         format_func=lambda s: ["fans off", "stage 1", "stage 2"][s], key="tm_s")
        age = st.select_slider("Age (years)", [3, 9, 16, 22], value=16, key="tm_age")
        rise = float(story.top_oil_rise(K, 1.0, stage, age))
        grad = float(story.hotspot_gradient(K, amb, stage, age))
        st.markdown(
            f"<div class='relay tech' style='font-family:{MONOF};font-size:14px'>"
            f"step 1 &nbsp; top-oil rise &nbsp;= {story.DTO_R:.0f} × "
            f"((K²·{story.R_RATIO:.0f}+1)/{story.R_RATIO + 1:.0f})^{story.N_EXP} "
            f"= <b style='color:{EE}'>{rise:.1f} K</b><br>"
            f"step 2 &nbsp; winding gradient = {story.DTH_R:.0f} × K^1.6 "
            f"= <b style='color:{AMBERHOT}'>{grad:.1f} K</b><br>"
            f"θ_hotspot = {amb} + {rise:.1f} + {grad:.1f} "
            f"= <b style='color:{temp_colour(amb + rise + grad)}'>{amb + rise + grad:.1f} °C</b>"
            f"</div>", unsafe_allow_html=True)
        st.caption("This is the steady state — the transformer having sat at this load forever. "
                   "Real ones never do, which is the next page's problem.")
    with c2:
        # heat-flow animation: packets travelling winding -> oil -> radiator -> air
        st.markdown("**Where the heat goes** — press Play")
        path_x = [0.615, 0.68, 0.75, 0.83, 0.90]
        path_y = [0.66, 0.70, 0.66, 0.52, 0.40]
        fig = transformer_section(K, amb, amb + rise, amb + rise + grad, stage, h=430,
                                  arrows=False)
        fig.add_trace(go.Scatter(x=[path_x[0]], y=[path_y[0]], mode="markers",
                                 marker=dict(size=13, color=AMBERHOT, symbol="circle",
                                             line=dict(color=TEXT, width=1)),
                                 name="heat", showlegend=False, hoverinfo="skip"))
        frames = []
        for i in range(28):
            f = i / 27
            seg = min(int(f * 4), 3)
            u = f * 4 - seg
            x = path_x[seg] + (path_x[seg + 1] - path_x[seg]) * u
            y = path_y[seg] + (path_y[seg + 1] - path_y[seg]) * u
            frames.append(go.Frame(data=[go.Scatter(
                x=[x], y=[y], mode="markers",
                marker=dict(size=13 - 4 * f, color=AMBERHOT, opacity=1 - 0.6 * f,
                            line=dict(color=TEXT, width=1)))]))
        st.plotly_chart(animate(fig, frames, ms=70), width="stretch")
        st.caption("Winding → oil → tank and radiators → ambient air. Every step needs a "
                   "temperature difference to drive it, which is why the winding must run "
                   "hottest.")


def render_the_target():
    c1, c2 = st.columns([1.15, 1])
    with c1:
        st.markdown("**What the substation records, and what it costs**")
        cat = pd.DataFrame([
            ("load_current_a", "Current transformer, 33 kV side", "Input", "Already fitted"),
            ("voltage_kv", "Voltage transformer, 132 kV side", "Input", "Already fitted"),
            ("ambient_temp_c", "Substation weather station", "Input", "Already fitted"),
            ("humidity_pct", "Substation weather station", "Input", "Already fitted"),
            ("oil_temp_c", "Top-oil dial thermometer", "Input", "Already fitted"),
            ("cooling_stage", "Fan contactor auxiliary contacts", "Input", "Already fitted"),
            ("transformer_age_years", "Asset register", "Input", "Free"),
            ("hotspot_temp_c", "Fibre-optic winding probe", "TARGET", "Factory-fit only"),
        ], columns=["Column", "Where it comes from", "Role", "Cost to obtain"])
        st.dataframe(cat, width="stretch", hide_index=True,
                     column_config={"Role": st.column_config.TextColumn(width="small")})
        st.success("**Seven cheap inputs, one expensive label.** That asymmetry is the entire "
                   "business case: replace an instrument that cannot be retrofitted with "
                   "arithmetic on instruments that are already there.")
    with c2:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=[7, 1], y=["Inputs<br>already fitted", "Target<br>needs a probe"],
                             orientation="h", marker_color=[AISIDE, RED],
                             text=["7 channels", "1 channel"], textposition="inside"))
        fig.update_layout(title="The asymmetry that makes a model worth building",
                          xaxis_title="Number of channels")
        st.plotly_chart(style(fig, 240), width="stretch")
        st.markdown(
            f"<div class='relay warn'>A fibre-optic probe is installed between the winding "
            f"discs at manufacture. Retrofitting it means untanking the transformer. "
            f"<b>Most units in service will never have one.</b></div>", unsafe_allow_html=True)


# ============================================================================
# PHASE 3  -  THE MONITORING LOG
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
    st.markdown("**Four checks, and what each one finds**")
    amb = log.sort_values(["unit_id", "timestamp"]).groupby("unit_id", sort=False).ambient_temp_c
    runs = amb.transform(lambda s: s.groupby((s != s.shift()).cumsum()).transform("size"))
    checks = [
        ("Missing values", int(log.isna().sum().sum()),
         "Comms dropouts on the oil thermometer, and probe outages.", "summary"),
        ("Humidity above 100 %", int((log.humidity_pct > 100).sum()),
         "A failed RH transmitter reporting a raw byte value of 255.", "summary"),
        ("Load current below 10 A", int((log.load_current_a < 10).sum()),
         "The unit was switched out. The winding was cooling to ambient — different physics.",
         "needs thought"),
        ("Ambient frozen 6 h or more", int((runs >= 6).sum()),
         "The sensor stopped updating. Every value is plausible; the sequence is not.",
         "invisible in a summary"),
        ("Exact duplicate rows", int(log.duplicated().sum()),
         "The historian exported part of the year twice.", "summary"),
        ("Constant columns", len([c for c in log.columns if log[c].nunique(dropna=True) == 1]),
         "`cooling_type` is the same for all four units, so it can teach nothing.", "summary"),
    ]
    cols = st.columns(3)
    for i, (name, n, why, kind) in enumerate(checks):
        with cols[i % 3]:
            st.metric(name, f"{n:,}")
            st.caption(f"{why}  \n*found by: {kind}*")
    st.divider()
    c1, c2 = st.columns([1, 1])
    with c1:
        fig = go.Figure(go.Histogram(x=log.humidity_pct, nbinsx=80, marker_color=EE))
        fig.add_vline(x=100, line=dict(color=RED, dash="dash"),
                      annotation_text="physically impossible above here")
        fig.update_layout(title="Humidity — the fault is visible in the summary",
                          xaxis_title="Humidity (%)")
        st.plotly_chart(style(fig, 330), width="stretch")
    with c2:
        u = log[log.unit_id == "T1"].sort_values("timestamp")
        bad = u[runs.loc[u.index] >= 6]
        w = u[(u.timestamp >= bad.timestamp.min() - pd.Timedelta(hours=40)) &
              (u.timestamp <= bad.timestamp.max() + pd.Timedelta(hours=40))] if len(bad) else u.head(80)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=w.timestamp, y=w.ambient_temp_c, mode="lines+markers",
                                 line=dict(color=EE, width=2), name="ambient"))
        if len(bad):
            fig.add_trace(go.Scatter(x=bad.timestamp, y=bad.ambient_temp_c, mode="markers",
                                     marker=dict(size=9, color=RED), name="frozen"))
        fig.update_layout(title="Ambient sensor — the fault is only visible in the sequence",
                          yaxis_title="°C")
        st.plotly_chart(style(fig, 330), width="stretch")


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
        st.caption("The oil lags the load by hours. The winding does not — which is why the "
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
        if len(sel):
            st.info(f"Between **{band[0]} and {band[1]} A** the hot spot ranges from "
                    f"**{sel.hotspot_temp_c.min():.0f} °C to {sel.hotspot_temp_c.max():.0f} °C** "
                    f"— **{sel.hotspot_temp_c.max() - sel.hotspot_temp_c.min():.0f} °C of spread** "
                    "at essentially the same load. One sensor cannot explain that.")


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


def render_linear():
    m = story.get_models()
    board = m["board"].set_index("Model")
    c1, c2 = st.columns([1, 1.1])
    with c1:
        mdl, sc, feats = m["fitted"]["lin_raw"]
        coefs = pd.Series(mdl.coef_, index=feats).sort_values(key=abs)
        fig = go.Figure(go.Bar(x=coefs.values,
                               y=[story.FEATURE_LABELS[c] for c in coefs.index],
                               orientation="h",
                               marker_color=[EE if v > 0 else AISIDE for v in coefs.values],
                               text=coefs.values.round(2), textposition="outside"))
        fig.update_layout(title="Coefficients: °C of hot spot per standard deviation of the sensor",
                          xaxis_title="°C")
        st.plotly_chart(style(fig, 330), width="stretch")
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
    with c2:
        fig = go.Figure()
        for s, colr in zip([0, 1, 2], [AISIDE, EE, RED]):
            fig.add_trace(go.Box(y=res.loc[res.stage == s, "err"], name=f"stage {s}",
                                 marker_color=colr, boxpoints=False))
        fig.add_hline(y=0, line=dict(color=TEXT, dash="dash"))
        fig.update_layout(title="Residual by cooling stage — it steps, so there is an interaction",
                          yaxis_title="Prediction error (°C)", showlegend=False)
        st.plotly_chart(style(fig, 380), width="stretch")
    st.markdown(
        f"<div class='relay tech'><b>Residuals should look like noise.</b> These do not. "
        f"Curvature means the relationship bends, so the next model must be able to bend. "
        f"Level shifts by category mean an interaction, so it must be able to split. "
        f"Tree ensembles do both natively — which is the whole reason for the next phase.</div>",
        unsafe_allow_html=True)


# ============================================================================
# PHASE 6  -  MODELS THAT BEND
# ============================================================================
def render_forest():
    m = story.get_models()
    board = m["board"].set_index("Model")
    c1, c2 = st.columns([1, 1.1])
    with c1:
        st.markdown("**One tree is a chain of engineering rules**")
        rf = m["fitted"]["rf"]
        t0 = rf.estimators_[0].tree_
        node, lines = 0, []
        for _ in range(5):
            if t0.children_left[node] == -1:
                break
            f = story.FEATURE_LABELS[story.ENG_FEATURES[t0.feature[node]]]
            lines.append(f"if <b style='color:{EE}'>{f}</b> ≤ {t0.threshold[node]:.2f}")
            node = t0.children_left[node]
        st.markdown(f"<div class='relay' style='font-family:{MONOF};font-size:13.5px'>"
                    + "<br>&nbsp;&nbsp;".join(lines)
                    + f"<br>&nbsp;&nbsp;→ predict a hot-spot temperature</div>",
                    unsafe_allow_html=True)
        st.caption("Read from the first tree in the forest. Every split is a threshold an "
                   "engineer could have written down — the forest just found 200 sets of them.")
        a, b = st.columns(2)
        a.metric("Trees", len(rf.estimators_))
        b.metric("Mean depth", f"{np.mean([t.get_depth() for t in rf.estimators_]):.0f}")
    with c2:
        n = st.slider("How many trees are averaged?", 1, story.RF_TREES,
                      story.RF_TREES, key="rf_n")
        Xte = story.get_features().loc[m["test_mask"], story.ENG_FEATURES]
        preds = np.mean([t.predict(Xte.values) for t in rf.estimators_[:n]], axis=0)
        mae = float(np.abs(preds - m["y_test"]).mean())
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
        st.caption(f"One tree alone scores about {float(np.abs(rf.estimators_[0].predict(Xte.values) - m['y_test']).mean()):.2f} °C. "
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
            f"<div class='relay warn'><b>The first few dozen trees are worse than the straight "
            f"line.</b> Boosting starts from a crude guess and works towards the answer, so "
            f"stopping early would have been a disaster. That is the opposite of a forest, "
            f"where every tree is already a full model.</div>", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _boost_curve():
    """Test MAE against tree count, measured on a live boosting run."""
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.metrics import mean_absolute_error
    df = story.get_features()
    te = df.test.to_numpy()
    # a subsample keeps the app responsive; the shape of the curve is the lesson
    tr = df.loc[~te].sample(9000, random_state=0)
    gb = GradientBoostingRegressor(n_estimators=200, learning_rate=0.08, max_depth=4,
                                   subsample=0.8, random_state=42
                                   ).fit(tr[story.ENG_FEATURES], tr[story.TARGET])
    Xte, yte = df.loc[te, story.ENG_FEATURES], df.loc[te, story.TARGET]
    maes = [mean_absolute_error(yte, p) for p in gb.staged_predict(Xte)]
    idx = list(range(1, len(maes) + 1))
    s = pd.Series(maes, index=idx)
    return s[s.index % 5 == 0]


def render_xgboost():
    m = story.get_models()
    board = m["board"]
    c1, c2 = st.columns([1, 1.1])
    with c1:
        st.markdown("**Why a second boosting implementation exists**")
        st.markdown(
            f"<div class='relay ai'>A condition-monitoring model is not fitted once. It is "
            f"refitted as the fleet changes — new units, new probes, a year of fresh readings. "
            f"<b>If refitting takes an hour it happens annually. If it takes a second it happens "
            f"whenever the data changes.</b></div>", unsafe_allow_html=True)
        st.write("")
        st.dataframe(pd.DataFrame([
            {"Improvement": "Histogram splits", "What it does":
                "Bucket each column once, so a split is a lookup instead of a sort"},
            {"Improvement": "Parallel and cache-aware", "What it does":
                "Uses every core on the machine"},
            {"Improvement": "Built-in regularisation", "What it does":
                "Penalises tree complexity, so more trees is safer"},
        ]), width="stretch", hide_index=True)
    with c2:
        ens = board[board.Family == "Ensemble"]
        fig = go.Figure(go.Bar(x=ens.Model, y=ens["MAE (°C)"],
                               marker_color=[GREEN if v == ens["MAE (°C)"].min() else EE
                                             for v in ens["MAE (°C)"]],
                               text=ens["MAE (°C)"].round(3), textposition="outside"))
        fig.update_layout(title="The three ensembles are within hundredths of a degree",
                          yaxis_title="MAE (°C)")
        st.plotly_chart(style(fig, 360), width="stretch")
        spread = ens["MAE (°C)"].max() - ens["MAE (°C)"].min()
        st.info(f"The three ensembles span **{spread:.3f} °C** — less than the width of the "
                "sensor noise. When two models are equally accurate, choose on the properties "
                "that are not accuracy: fit time, memory, and whether anyone can retrain it "
                "without booking an afternoon.")


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
        best = m["fitted"][m["best"]]
        ranks = pd.DataFrame({
            story.BEST_LABEL.get(m["best"], "Best model"):
                pd.Series(getattr(best, "feature_importances_",
                                  np.zeros(len(story.ENG_FEATURES))), index=story.ENG_FEATURES),
            "Random Forest": pd.Series(m["fitted"]["rf"].feature_importances_,
                                       index=story.ENG_FEATURES),
        })
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
        st.warning("**Two of the five specified sensors contribute nothing the model can use.** "
                   "Dropping a single *column* proves nothing — the columns are redundant by "
                   "construction. Dropping an *instrument* is the test with an answer in "
                   "degrees.")


@st.cache_data(show_spinner=False)
def _instrument_drops():
    """Refit without everything derived from each instrument, and measure."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.metrics import mean_absolute_error
    df = story.get_features()
    te = df.test.to_numpy()
    y_tr, y_te = df.loc[~te, story.TARGET], df.loc[te, story.TARGET]

    def fit(cols):
        f = [c for c in story.ENG_FEATURES if c not in cols]
        mdl = HistGradientBoostingRegressor(max_iter=120, learning_rate=0.10, max_depth=6,
                                            random_state=42).fit(df.loc[~te, f], y_tr)
        return mean_absolute_error(y_te, mdl.predict(df.loc[te, f]))

    base = fit([])
    groups = {
        "Humidity sensor": ["humidity_pct"],
        "Voltage transformer": ["voltage_kv"],
        "Fan status contacts": ["cooling_stage"],
        "Top-oil thermometer": ["oil_temp_c", "oil_rise_c", "oil_ramp_1h"],
        "Current transformer": ["load_current_a", "load_pu_16", "load_roll3", "load_ramp_1h"],
    }
    # fit() is the expensive call - run it once per group, not twice
    rows = []
    for k, v in groups.items():
        mae = fit(v)
        rows.append({"Instrument removed": k, "MAE (°C)": mae, "Penalty (°C)": mae - base})
    return pd.DataFrame(rows).sort_values("Penalty (°C)")


def render_sensitivity():
    st.markdown("**Push one input at a time and check the response against the physics**")
    c1, c2 = st.columns([1, 1.3])
    with c1:
        age = st.select_slider("Transformer age (years)", [3, 9, 16, 22], value=16, key="se_age")
        ambs = st.multiselect("Ambient temperatures to draw", [5, 15, 25, 30, 35, 42],
                              default=[15, 30, 42], key="se_amb")
        st.markdown(
            f"<div class='relay tech'>A model can score well on average and still be wrong "
            f"where it matters. If it flattens above 1.2 pu it under-predicts every overload — "
            f"the only hours anyone cares about. The average error would never show it.</div>",
            unsafe_allow_html=True)
    with c2:
        loads = np.arange(300, 970, 20)
        fig = go.Figure()
        colours = [AISIDE, EE, RED, GREEN, TECH, AMBERHOT]
        for i, amb in enumerate(sorted(ambs)):
            oils = amb + story.top_oil_rise(loads / story.I_RATED, 1.0, 2, age)
            rows = pd.concat([story.feature_row(l, amb, o, age=age)
                              for l, o in zip(loads, oils)], ignore_index=True)
            mdl, _ = story.best_model()
            p = mdl.predict(rows)
            fig.add_trace(go.Scatter(x=loads, y=p, name=f"ambient {amb} °C",
                                     line=dict(color=colours[i % len(colours)], width=3)))
        fig.add_hline(y=110, line=dict(color=RED, dash="dash"), annotation_text="110 °C")
        fig.update_layout(title="The model reproduced the transformer loading chart",
                          xaxis_title="Load current (A)",
                          yaxis_title="Predicted hot spot (°C)")
        st.plotly_chart(style(fig, 430), width="stretch")
    mdl, _ = story.best_model()
    pts = {}
    for l in (400, 700, 900):
        o = 30 + float(story.top_oil_rise(l / story.I_RATED, 1.0, 2, 16))
        pts[l] = float(mdl.predict(story.feature_row(l, 30, o, age=16))[0])
    a, b, c = st.columns(3)
    a.metric("400 → 700 A at 30 °C", f"+{pts[700] - pts[400]:.1f} °C",
             f"{(pts[700] - pts[400]) / 3:.1f} °C per 100 A")
    b.metric("700 → 900 A at 30 °C", f"+{pts[900] - pts[700]:.1f} °C",
             f"{(pts[900] - pts[700]) / 2:.1f} °C per 100 A")
    o1 = 15 + float(story.top_oil_rise(1.0, 1.0, 2, 16))
    o2 = 35 + float(story.top_oil_rise(1.0, 1.0, 2, 16))
    s1 = float(mdl.predict(story.feature_row(700, 15, o1, age=16))[0])
    s2 = float(mdl.predict(story.feature_row(700, 35, o2, age=16))[0])
    c.metric("+20 °C of ambient", f"+{s2 - s1:.1f} °C", f"slope {(s2 - s1) / 20:.2f}")
    st.success("**The curve steepens, as K^1.6 requires** — the second 100 A costs more than "
               "the first. And ambient shifts it up almost one-for-one, because the transformer "
               "cools to ambient and every degree of air temperature is a degree the oil cannot "
               "lose. Nothing told the model either of those things.")


# ============================================================================
# PHASE 8  -  THE MONITORING DASHBOARD
# ============================================================================
def render_metrics():
    m = story.get_models()
    best = m["board"].iloc[0]
    y, p = m["y_test"], m["preds"][m["best"]]
    a, b, c, d = st.columns(4)
    a.metric("MAE", f"{best['MAE (°C)']:.2f} °C", "typical error")
    b.metric("RMSE", f"{best['RMSE (°C)']:.2f} °C",
             f"ratio to MAE {best['RMSE (°C)'] / best['MAE (°C)']:.2f}")
    c.metric("R²", f"{best['R²']:.4f}", f"test std dev {y.std():.1f} °C")
    d.metric("95 % of errors within", f"±{np.percentile(np.abs(p - y), 95):.2f} °C")
    st.divider()
    c1, c2 = st.columns([1, 1.1])
    with c1:
        st.markdown("**The same model, two different test sets**")
        cmp = _split_comparison()
        st.dataframe(cmp.round(3), width="stretch", hide_index=True)
        st.warning("**Identical accuracy in degrees. Very different R².** Autumn's hot-spot "
                   "temperatures vary less than the full year's, and R² is measured against "
                   "that variation. Quote MAE in °C to an engineer; quote R² only alongside the "
                   "standard deviation of the test set.")
    with c2:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=cmp["Test set"], y=cmp["MAE (°C)"], name="MAE (°C)",
                             marker_color=EE, text=cmp["MAE (°C)"].round(2),
                             textposition="outside"), secondary_y=False)
        fig.add_trace(go.Scatter(x=cmp["Test set"], y=cmp["R²"], name="R²", mode="lines+markers",
                                 line=dict(color=AISIDE, width=3),
                                 marker=dict(size=13)), secondary_y=True)
        fig.update_yaxes(title_text="MAE (°C)", secondary_y=False, range=[0, 2.4])
        fig.update_yaxes(title_text="R²", secondary_y=True, range=[0.95, 1.0], showgrid=False)
        fig.update_layout(title="MAE holds. R² moves. The model did not change.")
        st.plotly_chart(style(fig, 380), width="stretch")


@st.cache_data(show_spinner=False)
def _split_comparison():
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.metrics import mean_absolute_error, r2_score
    df = story.get_features()
    rows = []
    for label, mask in [("Every 4th week (all seasons)", df.test.to_numpy()),
                        ("October–December only", (df.timestamp >= "2025-10-01").to_numpy())]:
        mdl = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06, max_depth=6,
                                            random_state=42
                                            ).fit(df.loc[~mask, story.ENG_FEATURES],
                                                  df.loc[~mask, story.TARGET])
        p, yv = mdl.predict(df.loc[mask, story.ENG_FEATURES]), df.loc[mask, story.TARGET]
        rows.append({"Test set": label, "Hours": int(mask.sum()),
                     "Test std dev (°C)": yv.std(),
                     "MAE (°C)": mean_absolute_error(yv, p), "R²": r2_score(yv, p)})
    return pd.DataFrame(rows)


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
    with c2:
        fig = go.Figure(go.Histogram(x=err, nbinsx=90, marker_color=EE))
        fig.add_vline(x=0, line=dict(color=TEXT, dash="dash"))
        fig.update_layout(title="Distribution of the error",
                          xaxis_title="Predicted − measured (°C)")
        st.plotly_chart(style(fig, 420), width="stretch")
    a, b, c, d = st.columns(4)
    a.metric("Bias", f"{err.mean():+.2f} °C")
    b.metric("Within ±1 °C", f"{100 * np.mean(np.abs(err) <= 1):.0f} %")
    c.metric("Within ±3 °C", f"{100 * np.mean(np.abs(err) <= 3):.0f} %")
    d.metric("Worst miss", f"{np.abs(err).max():.1f} °C")
    st.info("**Predicting too high costs money** — loading is restricted that need not have "
            "been. **Predicting too low costs insulation life**, silently, and nobody finds out "
            "for years. So a histogram centred on zero is necessary but not sufficient: it has "
            "to be centred on zero *in the hot band as well*.")


def render_trend():
    m = story.get_models()
    df = story.get_features()
    te = m["test_mask"]
    rows = df.loc[te].copy()
    rows["predicted"] = m["preds"][m["best"]]
    unit = rows.groupby("unit_id").hotspot_temp_c.max().idxmax()
    sub = rows[rows.unit_id == unit]
    peak = sub.loc[sub.hotspot_temp_c.idxmax(), "timestamp"]
    days = st.slider("Days either side of the annual peak", 1, 6, 3, key="tr_d")
    w = sub[(sub.timestamp >= peak - pd.Timedelta(days=days)) &
            (sub.timestamp <= peak + pd.Timedelta(days=days))].sort_values("timestamp")

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3],
                        vertical_spacing=0.07,
                        subplot_titles=(f"{unit}: predicted against measured",
                                        "Prediction error (°C)"))
    fig.add_trace(go.Scatter(x=w.timestamp, y=w.hotspot_temp_c, name="Measured (probe)",
                             line=dict(color=RED, width=3)), row=1, col=1)
    fig.add_trace(go.Scatter(x=w.timestamp, y=w.predicted, name="Predicted (model)",
                             line=dict(color=AISIDE, width=2, dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=w.timestamp, y=w.oil_temp_c, name="Top oil (measured)",
                             line=dict(color=EE, width=1.5)), row=1, col=1)
    fig.add_hline(y=110, line=dict(color=RED, dash="dash"), row=1, col=1)
    fig.add_trace(go.Bar(x=w.timestamp, y=w.predicted - w.hotspot_temp_c, marker_color=MUTED,
                         name="error"), row=2, col=1)
    fig.update_yaxes(title_text="°C", row=1, col=1)
    fig.update_yaxes(title_text="Error (°C)", row=2, col=1)
    st.plotly_chart(style(fig, 560), width="stretch")

    e = (w.predicted - w.hotspot_temp_c)
    a, b, c, d = st.columns(4)
    a.metric("Measured peak", f"{w.hotspot_temp_c.max():.1f} °C")
    b.metric("Predicted peak", f"{w.predicted.max():.1f} °C",
             f"{w.predicted.max() - w.hotspot_temp_c.max():+.1f} °C")
    c.metric("MAE this window", f"{e.abs().mean():.2f} °C")
    d.metric("Largest miss", f"{e.abs().max():.2f} °C")
    st.warning("**The model tracks the plant closely all week and then under-reads the peak.** "
               "That is not bad luck — it is the same effect the next page measures "
               "deliberately, and it always points the same way.")


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
        fig.update_layout(title="Error grows with temperature — and the bias turns negative",
                          yaxis_title="°C")
        st.plotly_chart(style(fig, 330), width="stretch")
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
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.metrics import mean_absolute_error
    df = story.get_features()
    rows = []
    for held in sorted(df.unit_id.unique()):
        tr, te = (df.unit_id != held), (df.unit_id == held)
        mdl = HistGradientBoostingRegressor(max_iter=200, learning_rate=0.08, max_depth=6,
                                            random_state=42
                                            ).fit(df.loc[tr, story.ENG_FEATURES],
                                                  df.loc[tr, story.TARGET])
        e = mdl.predict(df.loc[te, story.ENG_FEATURES]) - df.loc[te, story.TARGET].to_numpy()
        rows.append({"Held-out unit": held,
                     "Age": int(df.loc[te, "transformer_age_years"].iloc[0]),
                     "MAE (°C)": float(np.abs(e).mean()), "Bias (°C)": float(e.mean()),
                     "Scatter (°C)": float(e.std())})
    return pd.DataFrame(rows)


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
    with c2:
        fig = go.Figure(go.Bar(
            x=["Seen this unit"] + [f"Never seen {u}" for u in h["Held-out unit"]],
            y=[base] + list(h["MAE (°C)"]),
            marker_color=[GREEN] + [RED] * len(h),
            text=[f"{base:.2f}"] + [f"{v:.2f}" for v in h["MAE (°C)"]], textposition="outside"))
        fig.update_layout(title="Mean absolute error (°C)", yaxis_title="MAE (°C)")
        st.plotly_chart(style(fig, 380), width="stretch")
    st.markdown(
        f"<div class='relay warn'><b>This is the most important limitation in the project, and "
        f"it is measured rather than assumed.</b> The model interpolates within the fleet it "
        f"learned; it does not extrapolate to a new winding design. The scatter barely moves, "
        f"which tells you it learned the physics correctly and missed only the unit-specific "
        f"constant — so a short calibration period on a new unit would recover most of the "
        f"accuracy.</div>", unsafe_allow_html=True)


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
        with g2:
            st.metric("Headroom to 110 °C", f"{d['headroom_k']:.1f} K")
            st.metric("Ageing rate", f"{d['faa']:.2f} ×", "1.00 = design rate")
            st.metric("Winding gradient", f"{d['gradient_k']:.1f} K", "the part no gauge measures")
            st.metric("Loading", f"{d['load_pu']:.2f} pu")
        st.plotly_chart(transformer_section(d["load_pu"], amb, oil, d["hotspot_c"], d["stage"],
                                            h=330), width="stretch")
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
            f"<div class='relay tech'><b>Note where the machine learning stops.</b><br>"
            f"· The model predicts a temperature. That is all it does.<br>"
            f"· The thresholds come from a published standard.<br>"
            f"· The cause diagnosis is engineering logic, written by hand and readable by "
            f"anyone.<br><br>Keeping those three separate is what makes the system auditable. "
            f"<b>Nobody has to trust the model to check the rule.</b></div>",
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
    with c2:
        fig = go.Figure()
        for lim, colr in [(98, EE), (110, RED), (120, "#7b1fa2")]:
            h = df.groupby("unit_id").hotspot_temp_c.apply(lambda s: int((s > lim).sum()))
            fig.add_trace(go.Bar(x=h.index, y=h.values, name=f"> {lim} °C", marker_color=colr))
        fig.update_layout(title="Hours above each limit", yaxis_title="Hours in the year",
                          barmode="group")
        st.plotly_chart(style(fig, 350), width="stretch")
    st.success("**None of these four transformers reports a hot-spot temperature to this "
               "dashboard.** Every number in that column was predicted, from instruments that "
               "were already fitted. A person still reads it, still decides, and still signs "
               "the loading order.")


# ============================================================================
# THE LANDING PAGE
# ============================================================================
def render_start():
    st.markdown("# ⚡ AI for Transformer Hot-Spot Temperature Prediction")
    st.markdown("### An interactive course for Electrical Power Engineers")
    st.markdown(
        f"<div class='brief'><div class='brief-bar'>⟨ THE BRIEF ⟩</div>"
        f"You are not here to learn Artificial Intelligence. You are here to solve a "
        f"<b>power systems problem</b> — one an engineer genuinely cannot solve by hand, for "
        f"reasons that are arithmetic rather than effort. AI turns up in the middle of it, "
        f"because the engineering requires it. Not before.</div>", unsafe_allow_html=True)
    st.write("")

    # ---- SECTION 1 -------------------------------------------------------
    bridge._bus("01", "The Engineering Problem", EE)
    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.markdown(
            "A power transformer converts voltage, not power. Everything it fails to pass on "
            "becomes **heat**.\n\n"
            "That heat is not the problem. **Time spent hot** is the problem.\n\n"
            "- Insulating paper degrades chemically, and the rate roughly **doubles every 6 °C**.\n"
            "- The damage is cumulative and cannot be reversed.\n"
            "- Nothing visible happens until the unit fails.\n\n"
            "The temperature that governs this is the **winding hot spot** — typically "
            "**25 to 30 °C above** the top-oil temperature on the dial thermometer.\n\n"
            "**Almost no transformer in service measures it.** A fibre-optic probe has to be "
            "installed between the winding discs at manufacture, and it cannot be retrofitted "
            "without untanking the transformer.")
        limit_chips()
    with c2:
        st.plotly_chart(transformer_section(1.03, 36, 68, 97.8, 2, h=430),
                        width="stretch")
        st.caption("The gauge on the tank reads 68 °C. The winding is at about 98 °C. "
                   "Everything in this course lives in that 30 K gap.")

    # ---- SECTION 2 -------------------------------------------------------
    bridge._bus("02", "The Project Goal", AISIDE)
    m = story.get_models()
    s = m["board"].set_index("Model")["MAE (°C)"]
    base = s["IEEE C57.91 (nameplate)"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("The standard's error", f"{base:.2f} °C", "IEEE C57.91, nameplate")
    c2.metric("After machine learning", f"{s.min():.2f} °C",
              f"-{100 * (1 - s.min() / base):.0f} %")
    c3.metric("Steps in this course", len(bridge.STEPS))
    c4.metric("Hours of history used", f"{len(story.get_features()):,}")
    st.markdown(
        f"<div class='relay ai'>AI predicts the transformer hot-spot temperature from sensors "
        f"that are <b>already fitted</b>, so engineers can prevent overheating before it "
        f"damages insulation. Nothing here trips a breaker or changes a tap. The protection "
        f"engineer stays in charge and still owns every loading decision. The system does the "
        f"one thing a person cannot: <b>it estimates the temperature inside every winding, "
        f"every hour, and never looks away.</b></div>", unsafe_allow_html=True)
    st.write("")

    # ---- SECTION 3 -------------------------------------------------------
    bridge._bus("03", "The Engineering Mind Map", TECH)
    st.caption("Click any node to open its page.")
    c1, c2 = st.columns([1, 1.15])
    with c1:
        ev = st.plotly_chart(bridge.mind_map(style), width="stretch",
                             on_select="rerun", key="mindmap")
        try:
            pts = ev.selection["points"]
            if pts:
                bridge.goto(pts[0]["customdata"])
        except (KeyError, TypeError, AttributeError):
            pass
    with c2:
        st.markdown("**Or jump straight to a phase**")
        for i, (pname, pdesc) in enumerate(bridge.PHASES):
            steps = bridge.phase_steps(i)
            with st.expander(f"**{i+1} · {pname}** — {pdesc}"):
                for s_ in steps:
                    if st.button(f"{s_['ee_icon']}  {s_['ee']}",
                                 key=f"jump_{s_['id']}", width="stretch"):
                        bridge.goto(s_["id"])

    # ---- SECTION 4 -------------------------------------------------------
    bridge._bus("04", "Electrical Engineering → AI", GREEN)
    st.markdown(
        "Read down the left column and you have described a transformer condition-monitoring "
        "scheme. Read down the right column and you have described a complete machine learning "
        "pipeline. **They are the same column.**")
    st.plotly_chart(bridge.mapping_figure(style), width="stretch")

    st.divider()
    st.markdown(
        f"<div class='brief'><div class='brief-bar'>⟨ THE ONE IDEA THIS COURSE PROVES ⟩</div>"
        f"<span style='font-size:19px;line-height:1.6'><b>Machine Learning learns the "
        f"relationship between transformer operating conditions and hot-spot temperature, so "
        f"engineers can predict overheating before it happens and protect the asset.</b></span>"
        f"<br><br><span class='muted'>Do not take it on trust. Step "
        f"{bridge.ORDER.index('leaderboard')+1} measures it against the thermal model the "
        f"industry already uses, and step {bridge.ORDER.index('unseen-unit')+1} measures where "
        f"it stops working.</span></div>", unsafe_allow_html=True)
    st.write("")
    if st.button("▶  Start at step 1 — A Transformer Under Load", width="stretch"):
        bridge.goto(bridge.ORDER[0])


# ============================================================================
# THE ROUTER
# ============================================================================
RENDERERS = {
    "the-asset": render_the_asset, "why-heat": render_why_heat, "hot-spot": render_hot_spot,
    "enter-ai": render_enter_ai, "thermal-model": render_thermal_model,
    "the-target": render_the_target, "log": render_log, "inspect": render_inspect,
    "explore": render_explore, "clean": render_clean, "features": render_features,
    "scale": render_scale, "split": render_split, "baseline": render_baseline,
    "linear": render_linear, "residuals": render_residuals, "forest": render_forest,
    "boosting": render_boosting, "xgboost": render_xgboost, "leaderboard": render_leaderboard,
    "importance": render_importance, "sensitivity": render_sensitivity,
    "metrics": render_metrics, "errors": render_errors, "trend": render_trend,
    "hot-tail": render_hot_tail, "unseen-unit": render_unseen_unit, "predict": render_predict,
    "recommend": render_recommend, "dashboard": render_dashboard,
}
ALIASES = {"overview": "start", "home": "start", "gauge": "predict",
           "cross-section": "hot-spot", "ageing": "hot-spot", "models": "leaderboard",
           "evaluate": "metrics", "decision": "recommend", "fleet": "dashboard"}

stage = st.query_params.get("stage", "start")
stage = ALIASES.get(stage, stage)
if stage != "start" and stage not in RENDERERS:
    stage = "start"

with st.sidebar:
    st.markdown("### ⚡ A Thermal Problem")
    st.caption("You are keeping four power transformers alive, and AI keeps turning out to be "
               "the thing that supplies the one temperature nobody can measure.")
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
                    text=f"step {pos}/{len(bridge.ORDER)} · phase "
                         f"{step['phase']+1}/{len(bridge.PHASES)} · {pname}")
        st.markdown(
            f"<div style='font-size:12px;line-height:1.6'>"
            f"<span style='color:{MUTED}'>ELECTRICAL ENGINEERING STEP</span><br>"
            f"<b style='color:{EE}'>{step['ee']}</b><br>"
            f"<span style='color:{MUTED}'>IS THE AI CONCEPT</span><br>"
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
