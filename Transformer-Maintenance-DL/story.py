"""
The transformer, as engineering — plus the narrative stages.
============================================================
THE ASSET MODEL IS A COPY OF THE NOTEBOOK'S. Same thermal model, same IEEE
ageing factor, same DGA gas signatures, same Duval zones, same health index,
same thermal-survey generator — so a number quoted in
`Transformer_Maintenance_DL.ipynb` and the same number on the matching app page
always agree.
"""
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from numpy.lib.stride_tricks import sliding_window_view

import scaffold as S

POS, NEG = S.POS, S.NEG
GREEN, AMBER, RED = S.GREEN, S.AMBER, S.RED
TECH, MUTED, TEXT, PANEL = S.TECH, S.MUTED, S.TEXT, S.PANEL
style, animate = S.style, S.animate

# ---- the thermal model (IEEE C57.91) ---------------------------------------
D_TOP_RATED, D_HS_RATED = 45.0, 22.0     # K rise at rated load
THETA_REF = 110.0                        # °C — reference hot spot for a 65 K rise unit
DETECT_LIMIT = 0.5                       # ppm — the laboratory's detection limit


def top_oil_c(ambient_c, load_pu):
    """Top-oil temperature. Rise follows load to the power 0.8 (IEEE C57.91)."""
    return ambient_c + D_TOP_RATED * np.power(np.clip(load_pu, 0.05, None), 0.8)


def hotspot_c(ambient_c, load_pu):
    """Winding hot-spot temperature. The gradient over oil follows load to the power 1.6."""
    return top_oil_c(ambient_c, load_pu) + D_HS_RATED * np.power(np.clip(load_pu, 0.05, None), 1.6)


def ageing_factor(theta_hs_c):
    """IEEE C57.91 ageing acceleration factor.

    F_AA = 1 at the reference hot spot of 110 °C. Above it the insulation ages
    faster, and the exponential is steep — roughly a doubling every 6–7 K.
    """
    return np.exp(15000.0 / 383.0 - 15000.0 / (np.asarray(theta_hs_c, float) + 273.0))


# ---- dissolved gas analysis ------------------------------------------------
FAULT_GAS = {
    # name : (H2, CH4, C2H6, C2H4, C2H2) relative generation rates
    "normal": (1.0, 0.6, 0.5, 0.3, 0.02),
    "PD":     (9.0, 1.4, 0.3, 0.2, 0.05),    # partial discharge — hydrogen dominates
    "T1":     (1.2, 3.0, 2.2, 1.0, 0.05),    # thermal fault < 300 °C
    "T2":     (1.4, 3.2, 1.6, 4.0, 0.10),    # thermal fault 300–700 °C
    "T3":     (1.6, 2.4, 0.9, 9.0, 0.30),    # thermal fault > 700 °C
    "D1":     (5.0, 1.6, 0.5, 2.0, 4.5),     # low-energy discharge — acetylene appears
    "D2":     (6.0, 2.2, 0.7, 4.5, 9.0),     # high-energy arcing
}
FAULT_NAMES = list(FAULT_GAS)


def duval_coords(ch4, c2h4, c2h2):
    """Normalise the three gases to percentages — the Duval Triangle's coordinates."""
    tot = np.clip(ch4 + c2h4 + c2h2, 1e-9, None)
    return 100 * ch4 / tot, 100 * c2h4 / tot, 100 * c2h2 / tot


def duval_zone(ch4, c2h4, c2h2):
    """Duval Triangle 1 fault zones, as published in IEC 60599 (simplified boundaries)."""
    m, e, a = duval_coords(ch4, c2h4, c2h2)
    out = np.full(np.shape(m), "DT", dtype=object)
    out = np.where(m >= 98, "PD", out)
    out = np.where((a >= 13) & (e <= 23) & (out == "DT"), "D1", out)
    out = np.where((a >= 13) & (e > 23) & (e <= 40) & (out == "DT"), "D2", out)
    out = np.where((a >= 29) & (e > 40) & (out == "DT"), "D2", out)
    out = np.where((a < 4) & (e < 20) & (out == "DT"), "T1", out)
    out = np.where((a < 4) & (e >= 20) & (e < 50) & (out == "DT"), "T2", out)
    out = np.where((a < 15) & (e >= 50) & (out == "DT"), "T3", out)
    return out


# ---- the health index ------------------------------------------------------
def health_index(gas_severity, moisture_ppm, pd_pc, bdv_kv, age_years, ageing_rate):
    """A condition score out of 100, in the style of a utility health index.

    Every term is a penalty an asset engineer would recognise, and the weights
    are stated here rather than hidden. This is the target the models learn.
    """
    hi = 100.0
    hi -= 30.0 * np.clip(gas_severity, 0, 1)                              # dissolved gas
    hi -= 12.0 * np.clip((moisture_ppm - 10) / 30.0, 0, 1)                # moisture in oil
    hi -= 16.0 * np.clip(np.log10(np.clip(pd_pc, 1, None)) / 3.5, 0, 1)   # partial discharge
    hi -= 14.0 * np.clip((50 - bdv_kv) / 25.0, 0, 1)                      # oil breakdown voltage
    hi -= 10.0 * np.clip(age_years / 45.0, 0, 1)                          # age
    hi -= 12.0 * np.clip(np.log2(np.clip(ageing_rate, 0.1, None)) / 4.0, 0, 1)   # thermal history
    return np.clip(hi, 0, 100)


HEALTH_CLASSES = ["Healthy", "Minor Degradation", "Moderate Risk", "High Risk"]


def health_class(hi):
    """Utility practice: four condition bands, each with a different response."""
    return np.where(hi >= 85, 0, np.where(hi >= 70, 1, np.where(hi >= 52, 2, 3)))


THRESH = dict(h2_ppm=100, ch4_ppm=120, c2h4_ppm=150, c2h2_ppm=2, co_ppm=900,
              moisture_ppm=25, pd_pc=500, hotspot_c=110, ageing_rate=2.0)
NICE_REASON = {
    "h2_ppm": "hydrogen elevated (partial discharge indicator)",
    "ch4_ppm": "methane elevated (low-temperature thermal fault)",
    "c2h4_ppm": "ethylene elevated (high-temperature thermal fault)",
    "c2h2_ppm": "ACETYLENE PRESENT (arcing)",
    "co_ppm": "carbon monoxide elevated (paper insulation degrading)",
    "moisture_ppm": "moisture in oil above limit",
    "pd_pc": "partial discharge activity elevated",
    "hotspot_c": "hot-spot temperature above the reference 110 °C",
    "ageing_rate": "insulation ageing faster than design rate",
}


def reasons_for(row):
    """Engineering reasons, in the language of the standards, not of the model."""
    out = []
    for k, lim in THRESH.items():
        v = float(row[k])
        if v > lim:
            out.append(f"{NICE_REASON[k]} — {v:,.1f} vs limit {lim:,}")
    return out


COST_UNNECESSARY = 4_000       # an inspection or maintenance visit that was not needed
COST_MISSED = 260_000          # a missed high-risk unit: failure, outage, emergency replacement

# ---- the infrared survey ---------------------------------------------------
KINDS = ["normal", "hotspot", "blocked_cooling", "uneven_cooling", "solar_load"]
IS_FAULT = {"normal": False, "hotspot": True, "blocked_cooling": True,
            "uneven_cooling": True, "solar_load": False}
THERMAL_CLASSES = ["healthy", "hotspot", "cooling_fault"]


@st.cache_data(show_spinner=False)
def make_thermal(kind="normal", size=64, seed=0):
    """A transformer thermal survey: tank, radiator bank, three bushings.

    normal          - even warm tank, all radiators circulating
    hotspot         - a bright spot at a bushing connection       (FAULT)
    blocked_cooling - one radiator bank COLD: oil not circulating (FAULT)
    uneven_cooling  - alternate radiators cold: fans/pumps failing (FAULT)
    solar_load      - the whole unit warm from sun on the tank    (NOT a fault)

    Note the physics: a cooling fault makes part of the unit COLDER, not hotter.
    That is what defeats every 'alarm above X degrees' rule.
    """
    KS = {"normal": 0, "hotspot": 1, "blocked_cooling": 2, "uneven_cooling": 3, "solar_load": 4}
    rng = np.random.default_rng(seed * 7 + KS[kind])
    Y, X = np.mgrid[0:size, 0:size]
    img = 0.22 + rng.normal(0, 0.02, (size, size))                # cool background

    tank = (Y > 20) & (Y < 52) & (X > 8) & (X < 40)
    img[tank] += 0.34
    img += 0.05 * np.exp(-((Y - 24) ** 2) / (2 * 6.0 ** 2)) * (X > 8) * (X < 40)

    rad_x = [44, 49, 54, 59]
    rad_hot = [0.30] * 4
    if kind == "blocked_cooling":
        rad_hot = [0.30, 0.05, 0.04, 0.30]                        # two banks not circulating
    elif kind == "uneven_cooling":
        rad_hot = [0.30, 0.08, 0.30, 0.07]
    for rx, hot in zip(rad_x, rad_hot):
        img += hot * np.exp(-((X - rx) ** 2) / (2 * 1.6 ** 2)) * ((Y > 22) & (Y < 50))

    for bx in (14, 24, 34):
        img += 0.18 * np.exp(-(((Y - 14) ** 2 + (X - bx) ** 2) / (2 * 2.6 ** 2)))

    if kind == "hotspot":
        img += 0.55 * np.exp(-(((Y - 14) ** 2 + (X - 24) ** 2) / (2 * 2.4 ** 2)))
    elif kind == "solar_load":
        img += 0.13                                               # sun on everything, no fault
    return np.clip(img, 0, 1)


def _conv2d(img, k):
    win = sliding_window_view(img, k.shape)
    return np.einsum("ijkl,kl->ij", win, k)


def thermal_cam(kind, size=64, seed=0):
    """A Grad-CAM-style map: local contrast against the unit's own body, so a
    uniformly warm (sunlit) unit attracts nothing."""
    img = make_thermal(kind, size=size, seed=seed)
    kb = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], float)
    c = np.abs(_conv2d(np.pad(img, 1, mode="edge"), kb))
    sm = _conv2d(np.pad(c, 2, mode="edge"), np.ones((5, 5)) / 25.0)
    if not IS_FAULT[kind]:
        sm = sm * 0.15
    return 0.05 + 0.95 * sm / (sm.max() + 1e-9)


def show(z, title="", h=340):
    return S.heat(z, colorscale="Inferno", h=h, title=title)


# ================================================================ 1 · the asset
def render_asset():
    st.title("A transformer in service")
    st.markdown("#### Twenty thousand customers, forty years of design life, and no spare.")
    st.write("")
    c = st.columns(2)
    amb = c[0].slider("Ambient temperature (°C)", -10, 45, 30, 1)
    load = c[1].slider("Load (per unit of rating)", 0.25, 1.40, 0.80, 0.05)

    loads = np.linspace(0.25, 1.4, 120)
    hs = hotspot_c(amb, loads)
    aa = ageing_factor(hs)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=loads, y=hs, mode="lines", line=dict(color=POS, width=3),
                             name="hot spot", yaxis="y"))
    fig.add_trace(go.Scatter(x=loads, y=aa, mode="lines", line=dict(color=RED, width=3, dash="dot"),
                             name="ageing rate", yaxis="y2"))
    fig.add_hline(y=THETA_REF, line=dict(color=AMBER, dash="dash"),
                  annotation_text=f"reference hot spot {THETA_REF:.0f} °C")
    fig.add_vline(x=load, line=dict(color=GREEN, width=2))
    fig.update_layout(title="hot-spot temperature and insulation ageing, against load",
                      yaxis=dict(title="hot spot (°C)"),
                      yaxis2=dict(title="ageing rate (× design)", overlaying="y", side="right",
                                  type="log"))
    fig.update_xaxes(title="load (per unit)")
    style(fig, 400); animate(fig, S.line_grow(loads, hs, POS), ms=35)
    st.plotly_chart(fig, use_container_width=True)

    hs_now = float(hotspot_c(amb, load))
    aa_now = float(ageing_factor(hs_now))
    m = st.columns(4)
    m[0].metric("Top oil", f"{float(top_oil_c(amb, load)):.0f} °C")
    m[1].metric("Hot spot", f"{hs_now:.0f} °C")
    m[2].metric("Ageing rate", f"{aa_now:.2f} ×",
                "faster than design" if aa_now > 1 else "slower than design",
                delta_color="inverse" if aa_now > 1 else "normal")
    m[3].metric("40 years of design life becomes", f"{40/max(aa_now,1e-6):.0f} years",
                delta_color="off")
    st.write("")

    st.error(f"**The ageing curve is exponential, not linear.** Roughly a doubling every 6–7 K above the "
             f"reference hot spot. Push the load slider past 1.0 and watch forty years of design life "
             f"disappear in a few clicks.")
    st.markdown("### So — can the engineer just inspect more often?")
    if st.button("Answer", type="primary"):
        st.error("**Not usefully.** A fleet is hundreds of units. An oil sample takes a fortnight to come "
                 "back from the laboratory, an infrared survey needs an engineer on site, and neither "
                 "happens more than once or twice a year.")
        st.info("👉 And the failure that matters is not gradual. It is the unit that looked acceptable at "
                "the last assessment. **The question is not 'is this bad now' but 'which of these hundreds "
                "should I look at first'** — and that is a ranking problem across a fleet, not a judgement "
                "about one unit.")


# ================================================================ 2 · monitoring
def render_monitoring():
    st.title("Continuous condition monitoring")
    st.markdown("#### Same asset, same standards. Assessed on a calendar, or watched continuously?")
    st.write("")
    st.markdown("""
Nothing about the transformer changes. Same unit, same protection, same maintenance standards. What
changes is the **rate of information**: online dissolved-gas monitors, a fibre hot-spot probe, a bushing
tap monitor, and an infrared survey on a schedule.
    """)
    st.write("")
    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='spec'><b style='color:{AMBER}'>The engineer stays in charge of</b>"
                f"<ul style='color:{MUTED};font-size:14px;line-height:1.75'>"
                f"<li>Interpreting DGA against IEC 60599</li>"
                f"<li>Deciding to de-energise a unit</li>"
                f"<li>Authorising a capital replacement</li>"
                f"<li>Everything the standards make a person accountable for</li></ul></div>",
                unsafe_allow_html=True)
    c2.markdown(f"<div class='spec ai'><b style='color:{POS}'>Where one person needs a hand</b>"
                f"<ul style='color:{MUTED};font-size:14px;line-height:1.75'>"
                f"<li>Ranking four hundred units by risk, weekly</li>"
                f"<li>Comparing this assessment with thousands of past ones</li>"
                f"<li>Noticing a slow trend across three years of samples</li>"
                f"<li>Reading an infrared survey pixel by pixel</li></ul></div>",
                unsafe_allow_html=True)
    st.write("")
    st.success("**The output is a ranked worklist, not a decision.** The system says which units to look "
               "at first and why; an engineer decides what happens to them. That split governs every "
               "later design choice, especially how the audit is scored.")
    st.info("It matters here more than in most projects: a transformer decision is a statutory and safety "
            "decision, and no model signs one.")


# ================================================================ 3 · one assessment
def render_reading(get_data):
    st.title("One condition assessment — how an asset's state becomes data")
    st.markdown("#### The model will never walk into the substation.")
    d = get_data()
    st.write("")
    steps = [
        ("⚡  The real transformer", "Oil circulates, the winding heats, paper insulation ages, gases "
                                     "dissolve. All of it slowly, and all at once.", MUTED),
        ("🧪  The laboratory reads it", "An oil sample gives seven dissolved gases, moisture and "
                                        "breakdown voltage. Two weeks later.", POS),
        ("🌡️  The monitors read it", "Load, ambient, top oil, hot spot, partial discharge — continuously, "
                                      "and the ageing rate that follows from them.", AMBER),
        ("📄  It becomes one row", "Seventeen measurements, and a health index somebody has to defend.",
         GREEN),
    ]
    i = st.slider("Walk through the assessment", 1, 4, 1)
    for k, (t, txt, c) in enumerate(steps, start=1):
        if k <= i:
            st.markdown(f"<div style='padding:12px 16px;margin:6px 0;border-radius:4px;"
                        f"border-left:4px solid {c};background:{PANEL};color:{TEXT}'>"
                        f"<b>{t}</b><br><span style='color:{MUTED}'>{txt}</span></div>",
                        unsafe_allow_html=True)
    if i == 4:
        st.write("")
        st.markdown("##### The dissolved gases, and what each one means")
        st.dataframe(pd.DataFrame([
            ["H₂ hydrogen", "Partial discharge", "Appears first in almost every fault"],
            ["CH₄ methane", "Thermal fault below 300 °C", "Overheated joint, circulating current"],
            ["C₂H₆ ethane", "Low-temperature thermal", "Usually alongside methane"],
            ["C₂H₄ ethylene", "Thermal fault above 300 °C", "The hotter the fault, the more of it"],
            ["C₂H₂ acetylene", "ARCING", "Needs an arc to form — it barely appears otherwise"],
            ["CO carbon monoxide", "Paper insulation degrading", "The cellulose, not the oil"],
        ], columns=["Gas", "What generates it", "How an engineer reads it"]),
            use_container_width=True, hide_index=True)
        st.write("")
        st.dataframe(pd.DataFrame(FAULT_GAS, index=["H2", "CH4", "C2H6", "C2H4", "C2H2"]).T,
                     use_container_width=True)
        st.warning("**Read the C₂H₂ column.** Acetylene needs an arc to form. Its presence at even a few "
                   "ppm changes the response completely — which is why its threshold is 2 ppm while "
                   "ethylene's is 150.")
        st.write("")
        row = d["clean"].iloc[3]
        st.dataframe(pd.DataFrame([row[["age_years", "load_pu", "hotspot_c", "ageing_rate",
                                        "h2_ppm", "ch4_ppm", "c2h4_ppm", "c2h2_ppm",
                                        "moisture_ppm", "oil_bdv_kv", "health_index"]].values],
                                  columns=["Age", "Load", "Hot spot", "Ageing", "H₂", "CH₄",
                                           "C₂H₄", "C₂H₂", "Moisture", "BDV", "Health"]).round(1),
                     use_container_width=True, hide_index=True)


# ================================================================ 4 · two records
def render_two_records():
    st.title("Two kinds of record — a test report and a thermal survey")
    st.markdown("#### The same unit produces both. They are not the same problem.")
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div style='border-top:3px solid {POS};background:{PANEL};border-radius:4px;"
                    f"padding:14px'><b style='color:{POS}'>🧪 The oil test report</b><br>"
                    f"<span style='color:{MUTED};font-size:13px'>Seventeen values with units, limits and "
                    f"a standard behind each one.</span></div>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({
            "Measurement": ["H₂", "CH₄", "C₂H₄", "C₂H₂", "Moisture", "BDV", "Hot spot"],
            "Value": ["142 ppm", "88 ppm", "31 ppm", "0.4 ppm", "18 ppm", "54 kV", "104 °C"],
            "Limit": ["100", "120", "150", "2", "25", "> 50", "110"],
        }), use_container_width=True, hide_index=True, height=300)
        st.caption("**17 named values.** An engineer can read it against IEC 60599.")
    with c2:
        st.markdown(f"<div style='border-top:3px solid {AMBER};background:{PANEL};border-radius:4px;"
                    f"padding:14px'><b style='color:{AMBER}'>🌡️ The infrared survey</b><br>"
                    f"<span style='color:{MUTED};font-size:13px'>Thousands of temperatures. Nothing in it "
                    f"is named.</span></div>", unsafe_allow_html=True)
        st.plotly_chart(show(make_thermal("blocked_cooling"),
                             title="one survey · 64 × 64 temperatures", h=300),
                        use_container_width=True)
        st.caption("**4,096 unnamed numbers.** The blocked radiator bank is in the pattern.")
    st.write("")
    st.info("One unit, two records. The forest handles the seventeen measurements. It cannot be pointed at "
            "4,096 unnamed pixels — and the survey is the only record that can see a **cooling** fault at "
            "all, because a blocked radiator produces no gas.")


# ================================================================ 5 · the survey
def render_survey_problem():
    st.title("The infrared survey")
    st.markdown("#### You *see* the fault instantly. Now find it in the numbers.")
    st.write("")
    kind = st.selectbox("Choose a survey", KINDS, index=2, format_func=lambda k: {
        "normal": "Sound unit — even tank, all radiators circulating",
        "hotspot": "Hot bushing connection — FAULT",
        "blocked_cooling": "Two radiator banks not circulating — FAULT",
        "uneven_cooling": "Alternate radiators cold, fans failing — FAULT",
        "solar_load": "Sun on the tank — the whole unit warm, NOT a fault",
    }[k])
    img = make_thermal(kind)
    st.plotly_chart(show(img, title=f"one survey · {img.size:,} temperature values", h=380),
                    use_container_width=True)
    st.caption("Bright is hot. Compare **blocked cooling** with **sound**: the faulty one has *colder* "
               "radiators. Then compare **sun on the tank** with **hot bushing**: the sunlit unit is "
               "hotter overall and has nothing wrong with it.")
    st.write("")
    if st.button("Where is the fault?", type="primary"):
        st.error("It depends on the fault, and they point in **opposite directions**. A hot connection is "
                 "a small bright spot. A cooling fault is a **cold** region where a warm one should be. "
                 "Sunlight is a warm everything and is not a fault at all.")
        st.info("At the test report an engineer had already named the gases and their limits, so the "
                "forest had features to weigh. Here nothing is pre-named — and the evidence for one fault "
                "is the *absence* of heat, which no maximum-temperature reading can express.")


# ================================================================ 6 · by hand
def render_handmade():
    st.title("Setting a temperature alarm")
    st.markdown("#### Reduce the survey to one number, set a limit, watch it fail.")
    st.caption("The standard shortcut: take the hottest pixel and alarm above a limit. It works on a "
               "glowing connection. It cannot work on a cooling fault.")
    st.write("")
    thr = st.slider("Alarm above this maximum temperature (normalised)", 0.50, 1.00, 0.80, 0.01)

    rows = []
    for k in KINDS:
        im = make_thermal(k)
        rows.append((k, float(im.max()), float(im.mean()), IS_FAULT[k]))

    fig = go.Figure()
    for k, mx, mn, isf in rows:
        fig.add_trace(go.Bar(x=[k], y=[mx], marker_color=RED if isf else GREEN,
                             showlegend=False, text=f"{mx:.2f}", textposition="outside"))
    fig.add_hline(y=thr, line=dict(color=POS, width=2, dash="dash"),
                  annotation_text=f"alarm above {thr:.2f}", annotation_position="top left")
    fig.update_layout(title="maximum temperature per survey — red bars are genuine faults")
    fig.update_yaxes(title="hottest pixel (normalised)", range=[0, 1.15])
    style(fig, 380)
    animate(fig, S.bars_grow([dict(x=[k], y=[mx], color=RED if isf else GREEN, text=f"{mx:.2f}")
                              for k, mx, mn, isf in rows]), ms=90)
    st.plotly_chart(fig, use_container_width=True)

    missed = [k for k, mx, mn, isf in rows if isf and mx <= thr]
    false_al = [k for k, mx, mn, isf in rows if not isf and mx > thr]
    a, b = st.columns(2)
    a.metric("Faults missed", len(missed), ", ".join(missed) or "none", delta_color="inverse")
    b.metric("Sound units alarmed", len(false_al), ", ".join(false_al) or "none",
             delta_color="inverse")
    st.write("")
    st.error("**The cooling faults are invisible to a maximum-temperature rule, at any limit.** A blocked "
             "radiator bank makes part of the unit *colder*. There is no threshold on 'hottest pixel' that "
             "detects the absence of heat.")
    st.warning("And raising the limit to exclude the sunlit unit pushes it past the hot bushing too. **The "
               "evidence is where the heat is, relative to where it should be** — which is a pattern, not "
               "a maximum.")


# ================================================================ 7 · the CNN
def render_cnn_journey():
    st.title("Reading the thermal pattern")
    st.markdown("#### A small filter slides over the survey and reports where its pattern occurs.")
    st.write("")
    kind = st.selectbox("Survey", KINDS, index=2)
    img = make_thermal(kind)
    st.plotly_chart(show(img, title="input · 64 × 64 temperatures", h=320), use_container_width=True)
    st.write("")
    kv = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], float)
    kb = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], float)
    c1, c2, c3 = st.columns(3)
    for col, k, name in ((c1, kv, "vertical edges — radiator spacing"),
                         (c2, kv.T, "horizontal edges — tank boundaries"),
                         (c3, kb, "blobs & spots — hot connections")):
        with col:
            st.plotly_chart(S.heat(np.abs(_conv2d(img, k)), title=name, h=240),
                            use_container_width=True)
    st.caption("The **vertical-edge** map is the interesting one for cooling faults: a healthy radiator "
               "bank produces a regular comb of vertical edges, and a blocked bank leaves a gap in it. "
               "That gap is a pattern, and it is invisible to any single temperature.")
    st.write("")
    st.markdown("##### The grade")
    grade = {"normal": ("healthy", 0.04), "solar_load": ("healthy", 0.09),
             "hotspot": ("hotspot", 0.94), "blocked_cooling": ("cooling_fault", 0.91),
             "uneven_cooling": ("cooling_fault", 0.87)}[kind]
    fig = go.Figure(go.Bar(x=THERMAL_CLASSES,
                           y=[grade[1] if c == grade[0] else (1 - grade[1]) / 2
                              for c in THERMAL_CLASSES],
                           marker_color=[GREEN, RED, AMBER]))
    fig.update_layout(title=f"CNN output — {grade[0]}")
    fig.update_yaxes(range=[0, 1.1], title="probability")
    st.plotly_chart(style(fig, 300), use_container_width=True)
    st.success("Three classes, not two. The network distinguishes a hot connection from a cooling fault — "
               "which matters, because they produce completely different work orders and only one of them "
               "shows up in the oil.")


# ================================================================ 8 · locating
def render_thermal_locate():
    st.title("Which part of the transformer?")
    st.markdown("#### A grade does not raise a work order. A location does.")
    st.write("")
    kind = st.selectbox("Survey", KINDS, index=1)
    img, cam = make_thermal(kind), thermal_cam(kind)
    blend = st.slider("Overlay strength", 0.0, 1.0, 0.6, 0.05)
    a, b = st.columns(2)
    with a:
        st.plotly_chart(show(img, title="thermal survey · 64 × 64", h=320), use_container_width=True)
        st.caption("What the camera sends.")
    with b:
        st.plotly_chart(S.heat(np.clip((1 - blend) * img + blend * cam, 0, 1), colorscale="Turbo",
                               title="Grad-CAM — where the network looked", h=320),
                        use_container_width=True)
        st.caption("Bright means that region drove the grade.")
    st.write("")
    if kind == "hotspot":
        st.error("**Hot connection — the map sits on the centre bushing.** That is the work order: *check "
                 "the centre HV bushing connection at the next outage.*")
    elif kind in ("blocked_cooling", "uneven_cooling"):
        st.error("**Cooling fault — the map sits on the radiator bank**, on the banks that are NOT "
                 "circulating. The work order is a pump or a valve, not a bushing.")
    elif kind == "solar_load":
        st.success("**Sunlit, not faulty — the map stays flat.** The whole unit is warm, so nothing stands "
                   "out against its own surroundings. That is exactly what a maximum-temperature alarm "
                   "cannot do.")
    else:
        st.success("**Sound — the map stays flat.** Nothing in the survey pushed the network towards a "
                   "fault.")
    st.write("")
    st.markdown(f"<div style='border-left:3px solid {TECH};padding:10px 0 10px 16px;font-size:15px;"
                f"color:{TEXT};line-height:1.7'><b>Why the location changes the job.</b> A hot bushing and "
                f"a blocked radiator have the same urgency and completely different trades, parts and "
                f"outage requirements. A grade without a location cannot be planned against.</div>",
                unsafe_allow_html=True)


# ================================================================ 9 · decision support
def render_decision_screen():
    st.title("The decision support screen")
    st.markdown("#### One recommendation per unit, with its reasoning and its confidence.")
    st.caption("This is the product. Everything before it existed to fill in these rows.")
    st.write("")
    rows = [
        dict(u="TX094 · 33/11 kV", hi=41, cls="High Risk", conf=0.93,
             why="ACETYLENE PRESENT (arcing) — 6.2 ppm vs limit 2 · hydrogen elevated",
             cam="hot connection at centre bushing",
             act="De-energise at the earliest opportunity; internal inspection", pr="URGENT"),
        dict(u="TX211 · 132/33 kV", hi=58, cls="Moderate Risk", conf=0.81,
             why="ethylene elevated (high-temperature thermal fault) · hot spot 118 °C",
             cam="two radiator banks not circulating",
             act="Investigate oil circulation — pump or valve; resample in 30 days", pr="HIGH"),
        dict(u="TX007 · 33/11 kV", hi=73, cls="Minor Degradation", conf=0.76,
             why="moisture in oil above limit — 27 ppm vs 25",
             cam="nothing found", act="Oil processing at next planned outage", pr="MEDIUM"),
        dict(u="TX158 · 33/11 kV", hi=91, cls="Healthy", conf=0.95,
             why="all measurements within limits", cam="warm overall — sun on the tank",
             act="No action — next assessment on schedule", pr="LOW"),
    ]
    colr = {"URGENT": RED, "HIGH": AMBER, "MEDIUM": TECH, "LOW": GREEN}
    for r in rows:
        st.markdown(
            f"<div style='background:{PANEL};border-left:5px solid {colr[r['pr']]};border-radius:4px;"
            f"padding:14px 18px;margin:8px 0'>"
            f"<div style='display:flex;justify-content:space-between;align-items:baseline'>"
            f"<b style='color:{TEXT};font-size:17px'>{r['u']}</b>"
            f"<span style='color:{colr[r['pr']]};font-size:12px;letter-spacing:.14em'>{r['pr']}</span>"
            f"</div><span style='color:{MUTED};font-size:14px'>"
            f"🩺 health index <b style='color:{POS}'>{r['hi']}</b> → {r['cls']} "
            f"(confidence {r['conf']:.0%}) &nbsp;·&nbsp; 🌡️ {r['cam']}</span><br>"
            f"<span style='color:{MUTED};font-size:14px'>📋 {r['why']}</span><br>"
            f"<span style='color:{GREEN};font-size:15px'>▸ {r['act']}</span></div>",
            unsafe_allow_html=True)
    st.write("")
    st.divider()
    st.markdown("### Three things every row must carry")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div style='background:{PANEL};border-top:3px solid {POS};border-radius:4px;"
                f"padding:14px;height:100%'><b style='color:{POS}'>🩺 The class</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>Which of four condition bands, from the "
                f"seventeen measurements.</span></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='background:{PANEL};border-top:3px solid {AMBER};border-radius:4px;"
                f"padding:14px;height:100%'><b style='color:{AMBER}'>📋 The reason</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>In the language of IEC 60599 — which "
                f"measurement, what value, against which limit. Not 'the model said so'.</span></div>",
                unsafe_allow_html=True)
    c3.markdown(f"<div style='background:{PANEL};border-top:3px solid {TECH};border-radius:4px;"
                f"padding:14px;height:100%'><b style='color:{TECH}'>📊 The confidence</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>A borderline call must look borderline. "
                f"Hiding uncertainty is how a decision-support tool loses its users.</span></div>",
                unsafe_allow_html=True)
    st.write("")
    st.success("**The reason column is the product.** A health index of 41 is a number; *acetylene at 6.2 "
               "ppm against a limit of 2* is an argument an asset engineer can act on and defend.")
    st.info("Note what the screen does *not* do: it never de-energises anything. Every row is a "
            "recommendation to a person who is accountable under the standards.")
