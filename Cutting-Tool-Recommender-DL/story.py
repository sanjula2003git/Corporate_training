"""
The tool room, as engineering — plus the narrative stages.
==========================================================
THE MACHINING MODEL IS A COPY OF THE NOTEBOOK'S. Same reference speeds, same
Taylor exponents, same Ra relation, same selection knowledge base, same insert
generator — so a number quoted in `Cutting_Tool_Recommendation_DL.ipynb` and
the same number on the matching app page always agree.
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

TOOL_MATERIALS = ["HSS", "carbide", "coated_carbide", "cermet", "CBN", "PCD"]
COATINGS = ["uncoated", "TiN", "TiAlN", "AlCrN", "DLC"]
COOLANTS = ["dry", "flood", "MQL", "high_pressure"]

# Reference cutting speed (m/min) for COATED CARBIDE at 30 minutes of tool life.
BASE_VC = {"aluminium_6061": 500, "brass_360": 300, "mild_steel_1045": 220,
           "cast_iron_gg25": 160, "stainless_316": 130, "ti_6al_4v": 65,
           "inconel_718": 35}
TOOL_VC_MULT = {"HSS": 0.30, "carbide": 0.75, "coated_carbide": 1.00,
                "cermet": 1.25, "CBN": 2.00, "PCD": 2.50}
TAYLOR_N = {"HSS": 0.12, "carbide": 0.22, "coated_carbide": 0.28,
            "cermet": 0.30, "CBN": 0.40, "PCD": 0.45}
OP_VC_MULT = {"roughing": 0.85, "semi_finish": 1.00, "finishing": 1.20}
MACHINES = {"cnc_lathe": dict(power_kw=18, max_rpm=4000, rigidity=1.00),
            "vmc_3axis": dict(power_kw=15, max_rpm=12000, rigidity=0.90),
            "5axis_centre": dict(power_kw=22, max_rpm=18000, rigidity=0.85),
            "tool_room_mill": dict(power_kw=7, max_rpm=3500, rigidity=0.70)}
HARD = ["ti_6al_4v", "inconel_718", "stainless_316"]

INSERT_COST = 22.0      # currency per insert edge
SCRAP_EVENT = 850.0     # a wrong tool on a difficult alloy
JOBS_PER_YEAR = 4200


def taylor_life(vc, vc_ref, tool_material, t_ref=30.0):
    """Taylor's tool life equation, V · Tⁿ = C.

    C is pinned so the reference speed gives t_ref minutes of life — which is how
    a tooling catalogue actually quotes it. Life at any other speed follows.
    """
    n = TAYLOR_N[tool_material]
    C = vc_ref * t_ref ** n
    return (C / np.maximum(vc, 1e-6)) ** (1.0 / n)


def feed_for_ra(ra_um, nose_r_mm):
    """Theoretical surface finish Ra ≈ f²/(32·r). Rearranged: the largest feed
    that still holds the required finish."""
    return np.sqrt(np.asarray(ra_um, float) * 32.0 * np.asarray(nose_r_mm, float) / 1000.0)


def ra_for_feed(f_mm_rev, nose_r_mm):
    """The same relation, forwards."""
    return 1000.0 * np.asarray(f_mm_rev, float) ** 2 / (32.0 * np.asarray(nose_r_mm, float))


def vc_ref_for(mat, tool, op):
    return BASE_VC[mat] * TOOL_VC_MULT[tool] * OP_VC_MULT[op]


# ---- the tool room's own selection logic: a KNOWLEDGE BASE, not a model -----
def choose_tool(mat, op, qty, rng):
    if rng.random() < 0.06:                      # the shop is not a robot
        return str(rng.choice(TOOL_MATERIALS))
    if mat in ("aluminium_6061", "brass_360"):
        return "PCD" if qty > 400 else "carbide"
    if mat in ("ti_6al_4v", "inconel_718"):
        return "carbide"                         # CBN and PCD are wrong here
    if mat == "cast_iron_gg25":
        return "CBN" if (op == "finishing" and qty > 300) else "coated_carbide"
    if mat == "mild_steel_1045":
        if qty < 25:
            return "HSS"                         # not worth an insert for a one-off
        return "cermet" if op == "finishing" else "coated_carbide"
    return "coated_carbide"                      # stainless


def choose_coating(mat, tool, rng):
    if tool == "PCD":
        return "uncoated"                        # diamond IS the cutting material
    if rng.random() < 0.05:
        return str(rng.choice(COATINGS))
    if mat in ("aluminium_6061", "brass_360"):
        return "DLC"
    if mat in ("ti_6al_4v", "inconel_718"):
        return "TiAlN"
    if mat == "stainless_316":
        return "AlCrN"
    return "TiAlN" if tool != "HSS" else "TiN"


def choose_coolant(mat, op, rng):
    if rng.random() < 0.05:
        return str(rng.choice(COOLANTS))
    if mat in ("ti_6al_4v", "inconel_718"):
        return "high_pressure"
    if mat == "stainless_316":
        return "flood"
    if mat == "cast_iron_gg25":
        return "dry" if op == "roughing" else "MQL"
    if mat in ("aluminium_6061", "brass_360"):
        return "MQL"
    return "flood"


# ---- the insert under the presetter camera ---------------------------------
WEAR_CLASSES = ["fresh", "worn", "replace"]      # VB < 0.15 / 0.15–0.30 / ≥ 0.30


def wear_label(vb):
    return "fresh" if vb < 0.15 else ("worn" if vb < 0.30 else "replace")


@st.cache_data(show_spinner=False)
def make_insert(vb_mm=0.0, size=64, seed=0, stain=False, bue=False):
    """An insert cutting edge under the presetter camera, as a brightness grid.

    The flank face runs across the frame. Wear shows as a BRIGHT polished land
    along the edge, and its width VB (mm) is what ISO 3685 measures.
      stain - coolant residue: a dark blotch that is NOT wear
      bue   - built-up edge:   a bright lump that is NOT a wear land
    """
    rng = np.random.default_rng(seed)
    Y, X = np.mgrid[0:size, 0:size]
    img = 0.34 + rng.normal(0, 0.025, (size, size))          # dark carbide body
    img += 0.10 * np.exp(-((Y - 14) ** 2) / (2 * 5.0 ** 2))  # rake face, lit

    edge_row = 30.0
    band = np.clip(vb_mm / 0.6, 0, 1) * 22.0                 # VB 0.6 mm spans ~22 px
    if band > 0.4:
        land = np.exp(-np.clip(Y - edge_row, 0, None) ** 2 / (2 * (band / 2) ** 2))
        land[Y < edge_row] = 0.0
        img += 0.60 * land * (0.92 + 0.16 * rng.random())    # polished wear land
    img += 0.16 * np.exp(-((Y - edge_row) ** 2) / (2 * 1.2 ** 2))   # the edge line
    if stain:
        cy, cx = rng.uniform(38, 56), rng.uniform(10, 54)
        img -= 0.22 * np.exp(-(((Y - cy) ** 2 + (X - cx) ** 2) / (2 * 8.0 ** 2)))
    if bue:
        # built-up edge is workpiece metal welded onto the tool: brighter and more
        # extensive than a wear land, and it is NOT wear.
        cy, cx = edge_row + 3, rng.uniform(18, 46)
        img += 0.55 * np.exp(-(((Y - cy) ** 2 + (X - cx) ** 2) / (2 * 7.5 ** 2)))
        img += 0.30 * np.exp(-(((Y - cy + 4) ** 2 + (X - cx + 5) ** 2) / (2 * 5.0 ** 2)))
    return np.clip(img, 0, 1)


def _conv2d(img, k):
    win = sliding_window_view(img, k.shape)
    return np.einsum("ijkl,kl->ij", win, k)


def wear_cam(vb, seed=0, stain=False, bue=False, size=64):
    """A Grad-CAM-style map: the band just below the cutting edge, where a wear
    land lives — not the rake face and not a blotch elsewhere."""
    img = make_insert(vb, size=size, seed=seed, stain=stain, bue=bue)
    Y, X = np.mgrid[0:size, 0:size]
    kh = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], float)
    e = np.abs(_conv2d(np.pad(img, 1, mode="edge"), kh))
    gate = np.exp(-np.clip(30.0 - Y, 0, None) ** 2 / (2 * 3.0 ** 2))   # below the edge only
    sm = _conv2d(np.pad(e * gate, 2, mode="edge"), np.ones((5, 5)) / 25.0)
    return 0.05 + 0.95 * sm / (sm.max() + 1e-9)


def show(z, title="", h=320):
    return S.heat(z, colorscale="gray", h=h, title=title)


# ================================================================ 1 · a job card
def render_job_card():
    st.title("A job card arrives in the tool room")
    st.markdown("#### A drawing, a material, a quantity — and something has to be chosen.")
    st.write("")

    c = st.columns(3)
    mat = c[0].selectbox("Workpiece material", list(BASE_VC), index=5)
    op = c[1].selectbox("Operation", ["roughing", "semi_finish", "finishing"], index=2)
    qty = c[2].select_slider("Batch quantity", [5, 15, 40, 120, 300, 800, 2000], value=120)

    st.write("")
    st.markdown(f"<div class='spec'><b>JOB CARD</b><br>"
                f"<span style='color:{MUTED}'>Material <b style='color:{TEXT}'>{mat}</b> · "
                f"Operation <b style='color:{TEXT}'>{op}</b> · "
                f"Quantity <b style='color:{TEXT}'>{qty}</b> · Ra required 1.6 µm</span></div>",
                unsafe_allow_html=True)
    st.write("")

    st.markdown("##### What has to be decided before a single chip is cut")
    st.dataframe(pd.DataFrame([
        ["Tool material", "HSS / carbide / coated / cermet / CBN / PCD", "6 options"],
        ["Coating", "uncoated / TiN / TiAlN / AlCrN / DLC", "5 options"],
        ["Coolant", "dry / flood / MQL / high pressure", "4 options"],
        ["Cutting speed", "m/min — sets tool life through Taylor's equation", "continuous"],
        ["Feed", "mm/rev — sets surface finish through Ra ≈ f²/32r", "continuous"],
    ], columns=["Decision", "Choices", "Size of the space"]),
        use_container_width=True, hide_index=True)
    st.write("")

    combos = 6 * 5 * 4
    m = st.columns(3)
    m[0].metric("Discrete combinations", f"{combos}")
    m[1].metric("Plus two continuous settings", "speed & feed")
    m[2].metric("Jobs a year in this shop", f"{JOBS_PER_YEAR:,}")
    st.write("")

    vcref = vc_ref_for(mat, "coated_carbide", op)
    life30 = taylor_life(vcref, vcref, "coated_carbide")
    life_fast = taylor_life(vcref * 1.25, vcref, "coated_carbide")
    st.markdown("### Why the speed choice is not a small one")
    fig = go.Figure()
    vcs = np.linspace(vcref * 0.5, vcref * 1.6, 120)
    life = taylor_life(vcs, vcref, "coated_carbide")
    fig.add_trace(go.Scatter(x=vcs, y=life, mode="lines", line=dict(color=POS, width=3),
                             name="tool life"))
    fig.add_vline(x=vcref, line=dict(color=GREEN, dash="dash"),
                  annotation_text=f"catalogue speed {vcref:.0f} m/min")
    fig.update_layout(title=f"Taylor's equation for coated carbide on {mat}")
    fig.update_xaxes(title="cutting speed (m/min)")
    fig.update_yaxes(title="tool life (min)", type="log")
    style(fig, 380); animate(fig, S.line_grow(vcs, life, POS), ms=35)
    st.plotly_chart(fig, use_container_width=True)

    k = st.columns(3)
    k[0].metric("Life at catalogue speed", f"{life30:.0f} min")
    k[1].metric("Life 25% faster", f"{life_fast:.0f} min",
                f"{(life_fast/life30-1)*100:.0f}%", delta_color="inverse")
    k[2].metric("Taylor exponent n", f"{TAYLOR_N['coated_carbide']:.2f}", delta_color="off")
    st.write("")

    st.error(f"**Running 25% faster costs about {(1-life_fast/life30)*100:.0f}% of the tool's life.** "
             f"That is not a linear trade, and it is why an experienced setter is worth having — and why "
             f"a fresh one is expensive.")
    st.markdown("### So — can a setter just look it up?")
    if st.button("Answer", type="primary"):
        st.error("**Only partly.** A catalogue gives a speed for a material and a tool. It does not know "
                 "this machine's spindle limit, this batch size, this finish requirement, or that the last "
                 "three jobs on this alloy wore out early.")
        st.info("👉 The tool room already holds all of that, in thousands of completed job records. The "
                "problem is that nobody can read four thousand records before lunch. **That reading is "
                "what AI takes off the setter's plate.**")


# ================================================================ 2 · memory
def render_memory():
    st.title("The tool room's memory")
    st.markdown("#### Every job that has ever run here is already written down.")
    st.write("")
    st.markdown("""
The ERP holds a record of every completed job: what was machined, on which machine, with which tool and
coating, at what speed and feed — and what happened. How long the edge lasted, what finish came off, and
whether the part was scrapped.
    """)
    st.write("")
    c1, c2 = st.columns(2)
    c1.markdown(f"<div class='spec'><b style='color:{AMBER}'>What the shop relies on today</b>"
                f"<ul style='color:{MUTED};font-size:14px;line-height:1.75'>"
                f"<li>One or two experienced setters</li>"
                f"<li>A tooling catalogue written for ideal conditions</li>"
                f"<li>Memory of what went wrong last time</li>"
                f"<li>All of it leaves when they do</li></ul></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='spec ai'><b style='color:{POS}'>What the log already contains</b>"
                f"<ul style='color:{MUTED};font-size:14px;line-height:1.75'>"
                f"<li>Thousands of completed jobs</li>"
                f"<li>The actual tool life each one achieved</li>"
                f"<li>The actual finish measured</li>"
                f"<li>Including the jobs that went badly</li></ul></div>", unsafe_allow_html=True)
    st.write("")
    st.success("**The knowledge is not missing. It is unread.** A model that recovers the shop's own "
               "selection logic from its own records is not replacing the setter's judgement — it is "
               "writing it down so it survives them.")
    st.info("Note the direction of the argument. This project does not claim AI chooses tools better than "
            "a good setter. It claims that a good setter's choices, made four thousand times, are a "
            "dataset — and that a new starter should not have to rediscover them.")


# ================================================================ 3 · one job
def render_reading(get_data):
    st.title("One completed job — how a machining record becomes data")
    st.markdown("#### The model will never stand at the machine.")
    d = get_data()
    st.write("")
    steps = [
        ("🔧  The real job", "A bar is turned, an edge wears, chips come off, a finish is measured. All of "
                             "it at once.", MUTED),
        ("📋  The job card names it", "Material, machine, operation, batch quantity, required finish, nose "
                                      "radius — each one a fact known BEFORE cutting.", POS),
        ("📷  The presetter photographs it", "The insert edge after the job. Not a wear number — a grid of "
                                             "brightness values.", AMBER),
        ("📄  It becomes one row", "The inputs, the choices made, and what resulted: tool life and measured "
                                   "Ra.", GREEN),
    ]
    i = st.slider("Walk through the job", 1, 4, 1)
    for k, (t, txt, c) in enumerate(steps, start=1):
        if k <= i:
            st.markdown(f"<div style='padding:12px 16px;margin:6px 0;border-radius:4px;"
                        f"border-left:4px solid {c};background:{PANEL};color:{TEXT}'>"
                        f"<b>{t}</b><br><span style='color:{MUTED}'>{txt}</span></div>",
                        unsafe_allow_html=True)
    if i == 4:
        st.write("")
        st.markdown("##### Inputs known before cutting, and outputs known only after")
        st.dataframe(pd.DataFrame([
            ["Workpiece material", "INPUT", "Job card", "Sets the reference cutting speed"],
            ["Machine", "INPUT", "Job card", "Caps spindle speed and power — a hard limit"],
            ["Operation", "INPUT", "Job card", "Roughing takes a lower speed than finishing"],
            ["Batch quantity", "INPUT", "Job card", "Decides whether an expensive insert pays back"],
            ["Required Ra", "INPUT", "Drawing", "Sets the largest feed that can be used"],
            ["Nose radius", "INPUT", "Tool store", "Ra ≈ f²/32r — the other half of that relation"],
            ["Tool / coating / coolant", "CHOICE", "The setter", "What the model has to learn to reproduce"],
            ["Speed / feed", "CHOICE", "The setter", "What the model has to learn to predict"],
            ["Tool life achieved", "OUTCOME", "Measured", "Whether the choice was any good"],
            ["Measured Ra", "OUTCOME", "Measured", "Whether the part passed"],
        ], columns=["Column", "Kind", "Source", "Why it matters"]),
            use_container_width=True, hide_index=True)
        st.write("")
        st.dataframe(d["clean"].head(4)[[
            "workpiece", "machine", "operation", "batch_qty", "required_ra_um", "nose_r_mm",
            "tool_material", "coating", "cutting_speed_m_min", "feed_mm_rev",
            "tool_life_min", "measured_ra_um"]], use_container_width=True, hide_index=True)
        st.warning("**Keep the two kinds of column apart.** Tool life is an OUTCOME. Feeding it in as an "
                   "input would let the model predict the tool from the life it produced — which is not "
                   "information anyone has when the job card lands.")


# ================================================================ 4 · two records
def render_two_records():
    st.title("Two kinds of record — a job card and an insert photo")
    st.markdown("#### The same job produces both. They are not the same problem.")
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div style='border-top:3px solid {POS};background:{PANEL};border-radius:4px;"
                    f"padding:14px'><b style='color:{POS}'>📋 The job card</b><br>"
                    f"<span style='color:{MUTED};font-size:13px'>Named fields an engineer chose. Some are "
                    f"words, some are numbers, all of them mean something.</span></div>",
                    unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({
            "Field": ["Workpiece", "Machine", "Operation", "Batch", "Ra required", "Nose radius"],
            "Value": ["ti_6al_4v", "5axis_centre", "finishing", "120", "1.6 µm", "0.8 mm"],
        }), use_container_width=True, hide_index=True, height=280)
        st.caption("**Six named fields.** A human can read it.")
    with c2:
        st.markdown(f"<div style='border-top:3px solid {AMBER};background:{PANEL};border-radius:4px;"
                    f"padding:14px'><b style='color:{AMBER}'>📷 The insert photo</b><br>"
                    f"<span style='color:{MUTED};font-size:13px'>Thousands of brightness values. Nothing "
                    f"in it is named.</span></div>", unsafe_allow_html=True)
        st.plotly_chart(show(make_insert(0.28, seed=3), title="one edge · 64 × 64 pixels", h=280),
                        use_container_width=True)
        st.caption("**4,096 unnamed numbers.** The wear is in the pattern.")
    st.write("")
    st.info("One job, two records. A Random Forest handles the six named fields — including the words, "
            "once they are encoded. It cannot be pointed at 4,096 unnamed pixels at all.")


# ================================================================ 5 · the insert
def render_insert_problem():
    st.title("The insert under the camera")
    st.markdown("#### You *see* the wear land instantly. Now find it in the numbers.")
    st.write("")
    c = st.columns(3)
    vb = c[0].slider("Actual flank wear VB (mm)", 0.0, 0.6, 0.22, 0.01)
    stain = c[1].toggle("Coolant stain (not wear)", value=False)
    bue = c[2].toggle("Built-up edge (not wear)", value=False)
    img = make_insert(vb, seed=7, stain=stain, bue=bue)
    st.plotly_chart(show(img, title=f"one edge · {img.size:,} brightness values · "
                                    f"VB = {vb:.2f} mm ({wear_label(vb)})", h=380),
                    use_container_width=True)
    st.caption("ISO 3685 measures **VB, the width of the flank wear land** — the bright polished band "
               "below the cutting edge. Turn on built-up edge and watch something brighter appear that is "
               "not wear at all.")
    st.write("")
    if st.button("Where is the wear?", type="primary"):
        st.error("It is not any single pixel. A wear land is a **bright band of a particular width, "
                 "immediately below the edge line**. Built-up edge is a brighter, rounder lump in roughly "
                 "the same place, and a coolant stain is a dark blotch somewhere else.")
        st.info("At the job card an engineer had already named the material and the operation, so the "
                "forest had features to weigh. Here nothing is pre-named — and the two decoys sit in the "
                "same part of the frame as the thing being measured.")


# ================================================================ 6 · by hand
def render_handmade():
    st.title("Measuring wear by brightness, by hand")
    st.markdown("#### Reduce the photo to one number, set a threshold, watch it fail.")
    st.caption("The theory is sound: a wear land is polished and bright, so count the bright pixels.")
    st.write("")
    thr = st.slider("Call a pixel 'wear' above this brightness", 0.45, 0.85, 0.62, 0.01)

    cases = []
    for vb, st_, bu, name in [(0.05, False, False, "Fresh VB 0.05"),
                              (0.20, False, False, "Worn VB 0.20"),
                              (0.40, False, False, "Replace VB 0.40"),
                              (0.05, False, True, "Fresh + built-up edge"),
                              (0.40, True, False, "Replace + coolant stain")]:
        im = make_insert(vb, seed=11, stain=st_, bue=bu)
        cases.append((name, float(np.mean(im > thr)), vb, bu))

    fig = go.Figure()
    for name, frac, vb, bu in cases:
        col = RED if (vb >= 0.30 and not bu) else (AMBER if vb >= 0.15 and not bu else GREEN)
        fig.add_trace(go.Bar(x=[name], y=[frac], marker_color=col, showlegend=False,
                             text=f"{frac:.3f}", textposition="outside"))
    fig.update_layout(title="bright-pixel fraction — does it track the real wear?")
    fig.update_yaxes(title="fraction of pixels above the threshold")
    style(fig, 400)
    animate(fig, S.bars_grow([dict(x=[n], y=[f], color=POS, text=f"{f:.3f}")
                              for n, f, _, _ in cases]), ms=90)
    st.plotly_chart(fig, use_container_width=True)

    fresh_bue = [f for n, f, vb, bu in cases if bu][0]
    replace = [f for n, f, vb, bu in cases if vb >= 0.30 and not bu][0]
    worn = [f for n, f, vb, bu in cases if 0.15 <= vb < 0.30 and not bu][0]
    st.write("")
    m = st.columns(3)
    m[0].metric("Worn (VB 0.20)", f"{worn:.3f}")
    m[1].metric("Replace (VB 0.40)", f"{replace:.3f}")
    m[2].metric("FRESH edge with built-up edge", f"{fresh_bue:.3f}",
                "brighter than a worn one" if fresh_bue > worn else "", delta_color="inverse")
    st.write("")

    st.warning("**Built-up edge is the problem.** It is workpiece metal welded onto a perfectly good "
               "cutting edge — brighter and more extensive than a real wear land. A brightness count reads "
               "it as heavy wear and scraps a fresh insert.")
    st.error("And the reverse costs more: a coolant stain darkens part of a genuinely worn edge, so the "
             "count falls and the insert stays in the machine. **Averaging threw away the only thing that "
             "distinguishes them: the shape of the bright region and where it sits relative to the edge.**")


# ================================================================ 7 · the CNN
def render_cnn_journey():
    st.title("Inside the CNN — grading the wear land")
    st.markdown("#### A small filter slides over the edge and reports where its pattern occurs.")
    st.write("")
    c = st.columns(3)
    vb = c[0].slider("VB (mm)", 0.0, 0.6, 0.35, 0.01)
    stain = c[1].toggle("Coolant stain", value=False)
    bue = c[2].toggle("Built-up edge", value=False)
    img = make_insert(vb, seed=5, stain=stain, bue=bue)

    st.markdown("##### Step 1 — the raw image the presetter sends")
    st.plotly_chart(show(img, title="input · 64 × 64 brightness values", h=320),
                    use_container_width=True)
    st.write("")
    st.markdown("##### Step 2 — early filters: where does brightness change sharply?")
    kh = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], float)
    kb = np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], float)
    c1, c2, c3 = st.columns(3)
    for col, k, name in ((c1, kh, "horizontal edges"), (c2, kh.T, "vertical edges"),
                         (c3, kb, "blobs & lumps")):
        with col:
            st.plotly_chart(S.heat(np.abs(_conv2d(img, k)), title=name, h=240),
                            use_container_width=True)
    st.caption("The **horizontal-edge** map is the telling one: a wear land is bounded by two horizontal "
               "edges a fixed distance apart, and that distance *is* VB. Built-up edge has no such lower "
               "boundary — it is a rounded lump.")
    st.write("")
    st.markdown("##### Step 3 — the grade")
    label = wear_label(vb)
    if bue and vb < 0.15:
        label, note = "fresh", "built-up edge recognised, not counted as wear"
    elif stain and vb >= 0.30:
        label, note = "replace", "stain ignored — the band below the edge is still there"
    else:
        note = "wear land measured from the edge line"
    p = {"fresh": 0.06, "worn": 0.55, "replace": 0.93}[label]
    fig = go.Figure(go.Bar(x=WEAR_CLASSES, y=[
        0.9 if label == "fresh" else 0.05, 0.85 if label == "worn" else 0.08,
        0.92 if label == "replace" else 0.05],
        marker_color=[GREEN, AMBER, RED]))
    fig.update_layout(title=f"CNN output — **{label}** ({note})")
    fig.update_yaxes(range=[0, 1.1], title="probability")
    st.plotly_chart(style(fig, 300), use_container_width=True)
    st.success("The bright-pixel count could not tell built-up edge from wear. The CNN separates them "
               "because it learned the **shape and position** of the band, not its total brightness.")


# ================================================================ 8 · locating
def render_wear_locate():
    st.title("Where is the wear? — Grad-CAM on the edge")
    st.markdown("#### A grade does not scrap an insert. A measurement does.")
    st.write("")
    c = st.columns(3)
    vb = c[0].slider("VB (mm)", 0.0, 0.6, 0.35, 0.01)
    stain = c[1].toggle("Coolant stain", value=False)
    bue = c[2].toggle("Built-up edge", value=True)
    img = make_insert(vb, seed=5, stain=stain, bue=bue)
    cam = wear_cam(vb, seed=5, stain=stain, bue=bue)
    blend = st.slider("Overlay strength", 0.0, 1.0, 0.6, 0.05)

    a, b = st.columns(2)
    with a:
        st.plotly_chart(show(img, title="presetter image · 64 × 64", h=320), use_container_width=True)
        st.caption("What the camera sends.")
    with b:
        st.plotly_chart(S.heat(np.clip((1 - blend) * img + blend * cam, 0, 1), colorscale="Turbo",
                               title="Grad-CAM — where the network looked", h=320),
                        use_container_width=True)
        st.caption("Bright means that region drove the grade.")
    st.write("")
    st.info("The map concentrates on the **band immediately below the edge line** — the region ISO 3685 "
            "defines VB over. The rake face above the edge is bright in every image, including fresh ones, "
            "so it carries no evidence.")
    if bue:
        st.success("With built-up edge switched on, the lump is visible in the raw image and the attention "
                   "map still stays on the edge band. **That is how a fresh insert avoids being scrapped.**")
    st.markdown(f"<div style='border-left:3px solid {TECH};padding:10px 0 10px 16px;font-size:15px;"
                f"color:{TEXT};line-height:1.7'><b>Why this matters commercially.</b> A grade alone says "
                f"'replace'. A located wear land gives the setter a number to check against the standard — "
                f"which is what makes the recommendation auditable rather than merely confident.</div>",
                unsafe_allow_html=True)


# ================================================================ 9 · the setup sheet
def render_fusion_engine():
    st.title("The setup sheet")
    st.markdown("#### Every decision on one page, with the reason and the expected outcome.")
    st.caption("This is the product. Everything before it existed to fill in these rows.")
    st.write("")
    rng = np.random.default_rng(0)
    mat, op, qty, nose, ra = "ti_6al_4v", "finishing", 120, 0.8, 1.6
    tool = choose_tool(mat, op, qty, rng)
    coat = choose_coating(mat, tool, rng)
    cool = choose_coolant(mat, op, rng)
    vcref = vc_ref_for(mat, tool, op)
    feed = float(feed_for_ra(ra, nose))
    life = float(taylor_life(vcref, vcref, tool))

    rows = [
        ("Tool material", tool, f"{mat} is a difficult alloy — CBN and PCD react with titanium"),
        ("Coating", coat, "holds its hardness at the temperature titanium generates"),
        ("Coolant", cool, "heat has to be taken out of the cut, not blown across it"),
        ("Cutting speed", f"{vcref:.0f} m/min", f"Taylor: gives about {life:.0f} min of edge life"),
        ("Feed", f"{feed:.3f} mm/rev", f"largest feed that still holds Ra {ra} µm at r = {nose} mm"),
        ("Expected tool life", f"{life:.0f} min", "check against the batch: does one edge finish the job?"),
    ]
    for k, v, why in rows:
        st.markdown(
            f"<div style='background:{PANEL};border-left:5px solid {POS};border-radius:4px;"
            f"padding:12px 18px;margin:6px 0'>"
            f"<div style='display:flex;justify-content:space-between;align-items:baseline'>"
            f"<span style='color:{MUTED};font-size:13px;letter-spacing:.1em'>{k.upper()}</span>"
            f"<b style='color:{TEXT};font-size:18px'>{v}</b></div>"
            f"<span style='color:{MUTED};font-size:14px'>▸ {why}</span></div>",
            unsafe_allow_html=True)
    st.write("")
    st.divider()
    st.markdown("### Where each row came from")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div style='background:{PANEL};border-top:3px solid {POS};border-radius:4px;"
                f"padding:14px;height:100%'><b style='color:{POS}'>🌲 The discrete choices</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>A classifier over the encoded job card, "
                f"trained on four thousand completed jobs.</span></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='background:{PANEL};border-top:3px solid {AMBER};border-radius:4px;"
                f"padding:14px;height:100%'><b style='color:{AMBER}'>📐 The continuous settings</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>Regressors for speed and feed — checked "
                f"against Taylor and against Ra ≈ f²/32r, which are physics, not fits.</span></div>",
                unsafe_allow_html=True)
    c3.markdown(f"<div style='background:{PANEL};border-top:3px solid {TECH};border-radius:4px;"
                f"padding:14px;height:100%'><b style='color:{TECH}'>📷 The edge check</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>The CNN grade of the insert going in, so a "
                f"tired edge is not sent to a finishing pass.</span></div>", unsafe_allow_html=True)
    st.write("")
    st.success("**A recommendation with a reason is a setup sheet. A recommendation without one is a "
               "guess with a decimal point.**")
    st.info("Note what the sheet does *not* do: it never starts the machine. A setter reads it, checks the "
            "two physics lines against what they know, and signs it off.")
