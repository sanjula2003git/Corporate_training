"""
scaffold.py — the shared five-part teaching scaffold.
=====================================================
IDENTICAL COPY IN EVERY TEACHING APP FOLDER. It holds no domain knowledge and
renders no model: it wraps a stage renderer in the page structure every app in
this family uses, and it draws the navigation, the bridge figure, the mind map
and the quiz from whatever `bridge.py` in the same folder declares.

    <Discipline> Engineering   the on-site context      (open_page)
    The Challenge              why the manual way ends  (open_page)
    AI Connection              + the bridge figure      (open_page)
    Technical Idea             <- the app's renderer
    Key Takeaway               one sentence             (close_page)
    In the Notebook            where it lives           (close_page)

A folder's `bridge.py` must expose:
    THEME   dict(title, icon, dwg, civil_label, civil_kicker, station, rail,
                 start_button, project_line)
    PHASES  [(name, description), ...]
    STEPS   [dict(id, phase, civil, ai, civil_icon, ai_icon, tech,
                  civil_bullets, ai_bullets, site, challenge, ai_link,
                  notebook, contributes, takeaway, short), ...]
    QUIZ    {stage_id: dict(q, options, answer, why)}
    START   dict(problem, cards, promise, workflow_note, map_note)

COLOR IS A TEACHING DEVICE. Amber is always the engineering world, cyan is
always the AI, violet is always the technical process.
"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np

# ---------------------------------------------------------------- palette
BG, PANEL = "#0e1117", "#161b22"
CIVIL = "#ffb74d"      # amber  - the engineering discipline
AISIDE = "#4fc3f7"     # cyan   - the AI
TECH = "#ba68c8"       # violet - the technical process
POS, NEG = "#4fc3f7", "#ff8a65"
GREEN, AMBER, RED = "#66bb6a", "#ffb74d", "#ef5350"
MUTED, TEXT = "#8b949e", "#e6edf3"
STEEL, INK, EDGE = "#141b24", "#0b0e13", "#2b3440"
MONOF = "ui-monospace, SFMono-Regular, Consolas, 'Liberation Mono', monospace"

_CSS = """
<style>
.stApp { background-image: BACKDROP; }
hr { border-color:#2b3440 !important; }
[data-testid="stCaptionContainer"] p { font-family:MONO; letter-spacing:.02em; }
.stButton>button {
  border-radius:2px; border:1px solid #3a4655; background:#141b24;
  text-transform:uppercase; letter-spacing:.07em; font-size:12px; font-weight:600;
}
.stButton>button:hover { border-color:#ffb74d; color:#ffb74d; }
[data-testid="stMetric"] {
  background:#141b24; border:1px solid #2b3440; border-left:3px solid #66bb6a;
  border-radius:2px; padding:10px 12px;
}
[data-testid="stMetricValue"] { font-family:MONO; }
.op-row { display:flex; align-items:center; gap:10px; margin:24px 0 12px; }
.op-num { font-family:MONO; font-size:12px; font-weight:700; border:1px solid;
  padding:1px 7px; border-radius:2px; letter-spacing:.04em; white-space:nowrap; }
.op-label { font-family:MONO; text-transform:uppercase; letter-spacing:.14em;
  font-size:13px; font-weight:700; white-space:nowrap; }
.op-rule { flex:1; height:1px;
  background:repeating-linear-gradient(90deg,#2b3440 0 8px,transparent 8px 16px); }
.spec { position:relative; background:#141b24; border:1px solid #2b3440;
  border-left:4px solid #ffb74d;
  padding:15px 19px; color:#e6edf3; font-size:16px; line-height:1.68; margin:4px 0; }
.spec.ai { border-left-color:#4fc3f7; }
.spec.tech { border-left-color:#ba68c8; }
.spec.warn { border-left-color:#ef5350; }
.spec.ok { border-left-color:#66bb6a; }
.dro-bar { font-family:MONO; background:#0b0e13; border:1px solid #2b3440;
  border-left:3px solid #ffb74d; padding:9px 14px; font-size:12px; letter-spacing:.06em;
  color:#8b949e; border-radius:2px; }
.trav { font-family:MONO; text-align:center; border:1px solid #ffb74d; border-radius:2px;
  background:#0b0e13; padding:7px 4px; font-size:11px; color:#8b949e; line-height:1.5; }
.trav b { color:#ffb74d; font-size:13px; }
.travbar { display:flex; flex-wrap:wrap; align-items:center; gap:5px; background:#0b0e13;
  border:1px solid #2b3440; border-radius:2px; padding:10px 13px; }
.travlab { font-family:MONO; font-size:11px; letter-spacing:.12em; color:#8b949e; margin-right:4px; }
.ph { font-family:MONO; font-size:11px; padding:2px 6px; border:1px solid #2b3440;
  color:#3f4650; border-radius:2px; }
.ph.done { color:#66bb6a; border-color:#2f5233; }
.ph.cur { background:#ffb74d; color:#0b0e13; border-color:#ffb74d; font-weight:700; }
.brief { position:relative; border:1px solid #2b3440; background:#0b0e13; padding:22px 26px;
  border-top:3px solid #66bb6a; }
.brief-bar { font-family:MONO; font-size:12px; letter-spacing:.16em; color:#66bb6a; margin-bottom:9px; }
.card-ico { display:inline-flex; align-items:center; justify-content:center; width:40px; height:40px;
  border:1px solid #2b3440; border-radius:2px; font-size:22px; margin-bottom:9px; background:#0b0e13; }
.muted { color:#8b949e; font-size:13px; }
.substep { font-family:MONO; color:#8b949e; font-size:13px; }
</style>
"""

_DEFAULT_BACKDROP = ("linear-gradient(rgba(255,255,255,.022) 1px, transparent 1px),"
                     "linear-gradient(90deg, rgba(255,255,255,.022) 1px, transparent 1px)")


def inject_css(mod):
    """Load this app's display language once. Call after st.set_page_config."""
    backdrop = mod.THEME.get("backdrop", _DEFAULT_BACKDROP)
    css = _CSS.replace("MONO", MONOF).replace("BACKDROP", backdrop)
    extra = mod.THEME.get("extra_css", "")
    st.markdown(css + (f"<style>{extra}</style>" if extra else ""), unsafe_allow_html=True)


def op_header(op, label, color):
    st.markdown(
        f"<div class='op-row'>"
        f"<span class='op-num' style='color:{color};border-color:{color}'>{op}</span>"
        f"<span class='op-label' style='color:{color}'>{label}</span>"
        f"<span class='op-rule'></span></div>", unsafe_allow_html=True)


# ============================================================ shared chart look
def style(fig, h=440):
    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG, font_color=TEXT,
        margin=dict(l=30, r=30, t=60, b=30), height=h,
        template="plotly_dark", legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="#222933", zerolinecolor="#333")
    fig.update_yaxes(gridcolor="#222933", zerolinecolor="#333")
    return fig


def animate(fig, frames, ms=350):
    """Turn a finished chart into a 'press Play' reveal."""
    fig.frames = frames
    fig.update_layout(updatemenus=[dict(
        type="buttons", direction="left", showactive=False,
        x=1.0, y=1.16, xanchor="right", yanchor="top",
        bgcolor=PANEL, bordercolor=MUTED, font=dict(color=TEXT, size=13),
        buttons=[
            dict(label="▶  Play", method="animate",
                 args=[None, dict(frame=dict(duration=ms, redraw=True),
                                  fromcurrent=True, transition=dict(duration=120))]),
            dict(label="⏸  Pause", method="animate",
                 args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")]),
        ])])
    return fig


def line_grow(x, y, color, width=3, nf=26):
    x = np.asarray(x); y = np.asarray(y); n = len(x)
    ks = sorted(set(list(range(2, n + 1, max(1, n // nf))) + [n]))
    return [go.Frame(data=[go.Scatter(x=x[:k], y=y[:k], mode="lines",
                                      line=dict(color=color, width=width))],
                     name=str(k)) for k in ks]


def bars_grow(specs, steps=14):
    frames = []
    for s in range(1, steps + 1):
        t = s / steps
        data = [go.Bar(x=sp["x"], y=list(np.asarray(sp["y"], float) * t),
                       marker_color=sp["color"], name=sp.get("name"),
                       text=(sp.get("text") if s == steps else None),
                       textposition="outside") for sp in specs]
        frames.append(go.Frame(data=data, name=str(s)))
    return frames


def heat(z, colorscale="Inferno", h=320, title="", showscale=False, reverse=False):
    fig = go.Figure(go.Heatmap(z=z, colorscale=colorscale, showscale=showscale,
                               reversescale=reverse))
    fig.update_layout(title=title, paper_bgcolor=BG, plot_bgcolor=BG, font_color=TEXT,
                      margin=dict(l=10, r=10, t=44, b=10), height=h)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, autorange="reversed", scaleanchor="x")
    return fig


def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -50, 50)))


# ============================================================ lookups
def lookups(mod):
    mod.BY_ID = {s["id"]: s for s in mod.STEPS}
    mod.ORDER = [s["id"] for s in mod.STEPS]
    return mod.BY_ID, mod.ORDER


def goto(stage):
    st.query_params["stage"] = stage
    st.rerun()


def _wrap(text, width=24):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if len(t) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return "<br>".join(lines)


# ============================================================ the bridge figure
def _corner_ticks(fig, x0, x1, y0, y1, color, dx=0.16, dy=0.22):
    for cx, sx in ((x0, 1), (x1, -1)):
        for cy, sy in ((y0, 1), (y1, -1)):
            fig.add_shape(type="line", x0=cx, y0=cy, x1=cx + sx * dx, y1=cy,
                          line=dict(color=color, width=2), layer="above")
            fig.add_shape(type="line", x0=cx, y0=cy, x1=cx, y1=cy + sy * dy,
                          line=dict(color=color, width=2), layer="above")


def _card(fig, x0, x1, color, icon, title, bullets, kicker):
    fig.add_shape(type="rect", x0=x0, x1=x1, y0=0.8, y1=5.35,
                  line=dict(color=EDGE, width=1), fillcolor=STEEL, layer="below")
    _corner_ticks(fig, x0, x1, 0.8, 5.35, color)
    cx = (x0 + x1) / 2
    fig.add_annotation(x=cx, y=4.98, text=f"◤ {kicker}", showarrow=False,
                       font=dict(size=11, color=color, family=MONOF), xanchor="center")
    fig.add_annotation(x=cx, y=4.18, text=icon, showarrow=False,
                       font=dict(size=34), xanchor="center")
    fig.add_annotation(x=cx, y=3.28, text=f"<b>{_wrap(title)}</b>", showarrow=False,
                       font=dict(size=14, color=TEXT), xanchor="center", align="center")
    for i, b in enumerate(bullets):
        fig.add_annotation(x=cx, y=2.45 - i * 0.52, text=f"› {b}", showarrow=False,
                           font=dict(size=12, color=MUTED, family=MONOF), xanchor="center")


def bridge_figure(mod, step):
    """The engineering-activity -> AI-equivalent -> technical-process bridge."""
    fig = go.Figure()
    _card(fig, 0.2, 3.4, CIVIL, step["civil_icon"], step["civil"],
          step["civil_bullets"], mod.THEME["civil_kicker"])
    _card(fig, 6.6, 9.8, AISIDE, step["ai_icon"], step["ai"], step["ai_bullets"], "IN THE AI")

    for yy in (3.06, 2.94):
        fig.add_shape(type="line", x0=3.45, y0=yy, x1=6.35, y1=yy,
                      line=dict(color=EDGE, width=1.5), layer="below")
    fig.add_annotation(x=6.55, y=3.0, ax=6.3, ay=3.0, xref="x", yref="y",
                       axref="x", ayref="y", showarrow=True, arrowhead=2,
                       arrowsize=1.6, arrowwidth=2.5, arrowcolor=AISIDE, text="")
    fig.add_annotation(x=4.9, y=3.55, text="⇒ TRANSFORM ⇒", showarrow=False,
                       font=dict(size=11, color=MUTED, family=MONOF))

    fig.add_shape(type="rect", x0=3.5, x1=6.5, y0=1.25, y1=2.15,
                  line=dict(color=EDGE, width=1), fillcolor=INK, layer="below")
    _corner_ticks(fig, 3.5, 6.5, 1.25, 2.15, TECH, dx=0.14, dy=0.14)
    fig.add_annotation(x=5.0, y=2.02, text="⌗ COMPUTE", showarrow=False,
                       font=dict(size=9, color=TECH, family=MONOF))
    fig.add_annotation(x=5.0, y=1.62, text=_wrap(step["tech"], 30), showarrow=False,
                       font=dict(size=9.5, color=TEXT, family=MONOF),
                       xanchor="center", yanchor="middle", align="center")
    fig.add_annotation(x=5.0, y=2.42, text="▼", showarrow=False, font=dict(size=13, color=TECH))

    fig.add_trace(go.Scatter(x=[3.5], y=[3.0], mode="markers",
                             marker=dict(size=13, color=CIVIL, symbol="square",
                                         line=dict(color=INK, width=1)),
                             hoverinfo="skip", showlegend=False))
    frames = []
    for i in range(24):
        t = i / 23
        x = 3.5 + t * 2.85
        c = CIVIL if t < 0.45 else (TEXT if t < 0.55 else AISIDE)
        frames.append(go.Frame(data=[go.Scatter(
            x=[x], y=[3.0], mode="markers",
            marker=dict(size=13, color=c, symbol="square", line=dict(color=INK, width=1)))]))
    animate(fig, frames, ms=90)

    fig.update_xaxes(visible=False, range=[0, 10])
    fig.update_yaxes(visible=False, range=[0.5, 5.85])
    return style(fig, h=360)


# ============================================================ navigation
def _nav_strip(mod, step, key):
    BY_ID, ORDER = mod.BY_ID, mod.ORDER
    i = ORDER.index(step["id"])
    prev_s = BY_ID[ORDER[i - 1]] if i > 0 else None
    next_s = BY_ID[ORDER[i + 1]] if i < len(ORDER) - 1 else None
    c1, c2, c3 = st.columns([1, 1.25, 1])
    with c1:
        if prev_s:
            if st.button(f"◀  {prev_s['civil']}", key=f"prev_{key}", use_container_width=True):
                goto(prev_s["id"])
        else:
            if st.button("◀  The project overview", key=f"prev_{key}", use_container_width=True):
                goto("start")
    with c2:
        st.markdown(f"<div class='trav'>▐ STEP {i+1:02d} / {len(ORDER):02d} ▌"
                    f"<br><b>{step['civil']}</b></div>", unsafe_allow_html=True)
    with c3:
        if next_s:
            if st.button(f"{next_s['civil']}  ▶", key=f"next_{key}", use_container_width=True):
                goto(next_s["id"])
        else:
            if st.button("Back to the overview  ▶", key=f"next_{key}", use_container_width=True):
                goto("start")


# ============================================================ the page
def open_page(mod, stage):
    """Parts 1, 2 and 3 — rendered ABOVE the app's own stage renderer."""
    step = mod.BY_ID.get(stage)
    if step is None:
        return
    pname, pdesc = mod.PHASES[step["phase"]]

    _nav_strip(mod, step, "top")
    i = mod.ORDER.index(stage)
    st.markdown(
        f"<div class='dro-bar' style='margin-top:14px'>{mod.THEME['station']} &nbsp; "
        f"STEP {i+1:02d}/{len(mod.ORDER)} &nbsp;·&nbsp; PHASE {step['phase']+1:02d}/{len(mod.PHASES)} "
        f"&nbsp;·&nbsp; <span style='color:{CIVIL}'>{pname.upper()}</span> "
        f"&nbsp;—&nbsp; {pdesc}</div>", unsafe_allow_html=True)
    st.markdown(f"# {step['civil_icon']}  {step['civil']}")
    st.markdown(f"<span class='substep'>▸ this step is the AI concept </span>"
                f"<b style='color:{AISIDE}'>{step['ai']}</b>", unsafe_allow_html=True)
    st.divider()

    op_header("PT·10", mod.THEME["civil_label"], CIVIL)
    st.markdown(f"<div class='spec'>{step['site']}</div>", unsafe_allow_html=True)
    st.write("")

    op_header("PT·20", "The Challenge", RED)
    st.markdown(f"<div class='spec warn'>{step['challenge']}</div>", unsafe_allow_html=True)
    st.write("")

    op_header("PT·30", "AI Connection", AISIDE)
    st.markdown(f"<div class='spec ai'>{step['ai_link']}</div>", unsafe_allow_html=True)
    st.write("")
    st.plotly_chart(bridge_figure(mod, step), use_container_width=True, key=f"bridge_{stage}")
    st.caption("▶ Press Play — the record travels from the site into the AI.")
    st.divider()

    op_header("PT·40", "Technical Idea", TECH)
    st.caption(f"{step['tech']} — interactive. Change things and watch what happens.")
    st.write("")


def close_page(mod, stage):
    """Part 5 — rendered BELOW the app's own stage renderer."""
    step = mod.BY_ID.get(stage)
    if step is None:
        return
    st.divider()

    op_header("PT·50", "Key Takeaway", GREEN)
    st.markdown(f"<div class='spec ok' style='font-size:19px;font-weight:600;line-height:1.5'>"
                f"{step['takeaway']}</div>", unsafe_allow_html=True)
    st.write("")

    op_header("PT·60", "In the Notebook", "#8bc34a")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Where you implement it**\n\n{step['notebook']}")
    with c2:
        st.markdown(f"**What it contributes**\n\n{step['contributes']}")

    render_quiz(mod, stage)

    st.write("")
    segs = []
    for i, (pname, _) in enumerate(mod.PHASES):
        cls = "cur" if i == step["phase"] else ("done" if i < step["phase"] else "")
        segs.append(f"<span class='ph {cls}' title='{pname}'>{i+1:02d}</span>")
    st.markdown(
        f"<div class='travbar'><span class='travlab'>{mod.THEME['rail']}</span>"
        + "".join(segs)
        + f"<span class='travlab' style='margin-left:auto'>PH {step['phase']+1:02d}"
        f"/{len(mod.PHASES)} · {mod.PHASES[step['phase']][0].upper()}</span></div>",
        unsafe_allow_html=True)
    st.write("")
    _nav_strip(mod, step, "bottom")


def render_quiz(mod, stage):
    """One check-your-understanding MCQ per stage."""
    q = mod.QUIZ.get(stage)
    if not q:
        return
    st.write("")
    st.markdown("##### 📝 Check your understanding")
    st.markdown(f"**{q['q']}**")
    choice = st.radio("Select an answer", q['options'], index=None,
                      key=f"quiz_{stage}", label_visibility="collapsed")
    if choice is not None:
        correct = q['options'][q['answer']]
        if choice == correct:
            st.success(f"✅ Correct. {q['why']}")
        else:
            st.error(f"❌ Not quite — the answer is **{correct}**.\n\n{q['why']}")


# ============================================================ mind map
def mind_map(mod):
    fig = go.Figure()
    n = len(mod.PHASES)
    VGAP = 1.5
    ys = {i: (n - 1 - i) * VGAP for i in range(n)}
    _phase_steps = lambda pi: [s for s in mod.STEPS if s["phase"] == pi]

    for i in range(n - 1):
        fig.add_annotation(x=0, y=ys[i + 1] + 0.55, ax=0, ay=ys[i] - 0.62,
                           xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1.1,
                           arrowwidth=2, arrowcolor=CIVIL, text="")

    GAP, X0 = 3.4, 1.7
    maxk = max(len(_phase_steps(pi)) for pi in range(n))
    sx, sy, stext, scustom, shover = [], [], [], [], []
    for pi, (pname, pdesc) in enumerate(mod.PHASES):
        kids = _phase_steps(pi)
        for k, s in enumerate(kids):
            fig.add_shape(type="line", x0=0.3, y0=ys[pi], x1=X0 + k * GAP, y1=ys[pi],
                          line=dict(color="#2b323c", width=1.2, dash="dot"), layer="below")
        fig.add_annotation(x=0, y=ys[pi], text=f"<b>PH {pi+1:02d}</b>", showarrow=False,
                           font=dict(size=11, color=BG, family=MONOF),
                           bgcolor=CIVIL, bordercolor=CIVIL, borderpad=5, borderwidth=2)
        fig.add_annotation(x=-0.95, y=ys[pi] + 0.14, text=f"<b>{pname}</b>", showarrow=False,
                           xanchor="right", font=dict(size=13, color=CIVIL))
        fig.add_annotation(x=-0.95, y=ys[pi] - 0.16, text=_wrap(pdesc, 32), showarrow=False,
                           xanchor="right", yanchor="top", align="right",
                           font=dict(size=10, color=MUTED))
        for k, s in enumerate(kids):
            sx.append(X0 + k * GAP); sy.append(ys[pi])
            stext.append(f"{s['civil_icon']} {s['short']}")
            scustom.append(s["id"])
            shover.append(f"<b>{s['civil']}</b><br>"
                          f"<span style='color:{AISIDE}'>= {s['ai']}</span><br>"
                          f"<i>click to open</i>")

    fig.add_trace(go.Scatter(
        x=sx, y=sy, mode="markers+text", text=stext, textposition="top center",
        textfont=dict(size=10, color=TEXT), customdata=scustom,
        marker=dict(size=20, color=INK, line=dict(color=AISIDE, width=2), symbol="hexagon"),
        hovertemplate="%{hovertext}<extra></extra>", hovertext=shover, showlegend=False))

    fig.update_xaxes(visible=False, range=[-7.0, X0 + (maxk - 1) * GAP + 2.2])
    fig.update_yaxes(visible=False, range=[-1.0, (n - 1) * VGAP + 0.6])
    return style(fig, h=int((n - 1) * VGAP * 78) + 150)


def mapping_figure(mod):
    fig = go.Figure()
    n = len(mod.STEPS)
    for i, s in enumerate(mod.STEPS):
        y = (n - 1 - i) * 1.0
        fig.add_shape(type="rect", x0=0, x1=3.6, y0=y - 0.36, y1=y + 0.36,
                      line=dict(color=EDGE, width=1), fillcolor=STEEL, layer="below")
        fig.add_shape(type="line", x0=0, y0=y - 0.36, x1=0, y1=y + 0.36,
                      line=dict(color=CIVIL, width=3), layer="above")
        fig.add_annotation(x=0.18, y=y, text=f"{s['civil_icon']} {s['civil']}", showarrow=False,
                           xanchor="left", font=dict(size=11.5, color=TEXT))
        fig.add_annotation(x=4.1, y=y, text="»", showarrow=False,
                           font=dict(size=16, color=MUTED, family=MONOF))
        fig.add_shape(type="rect", x0=4.6, x1=8.2, y0=y - 0.36, y1=y + 0.36,
                      line=dict(color=EDGE, width=1), fillcolor=STEEL, layer="below")
        fig.add_shape(type="line", x0=8.2, y0=y - 0.36, x1=8.2, y1=y + 0.36,
                      line=dict(color=AISIDE, width=3), layer="above")
        fig.add_annotation(x=4.78, y=y, text=f"{s['ai_icon']} {s['ai']}", showarrow=False,
                           xanchor="left", font=dict(size=11.5, color=TEXT))
        fig.add_annotation(x=8.4, y=y, text=f"PH{s['phase']+1:02d}", showarrow=False,
                           xanchor="left", font=dict(size=9, color="#3f4650", family=MONOF))

    fig.add_annotation(x=0, y=n - 0.35, text=f"◤ {mod.THEME['civil_label'].upper()} PROCESS",
                       showarrow=False, xanchor="left",
                       font=dict(size=12, color=CIVIL, family=MONOF))
    fig.add_annotation(x=4.6, y=n - 0.35, text="◤ THE AI PROCESS THAT SOLVES IT",
                       showarrow=False, xanchor="left",
                       font=dict(size=12, color=AISIDE, family=MONOF))
    fig.update_xaxes(visible=False, range=[-0.2, 9.0])
    fig.update_yaxes(visible=False, range=[-0.8, n + 0.2])
    return style(fig, h=max(420, 40 * n))


# ============================================================ the opening page
def render_start(mod):
    T, S = mod.THEME, mod.START
    st.markdown(
        f"<div class='brief'>"
        f"<div class='brief-bar'>PROJECT BRIEF · {T['dwg']} · REV A · "
        f"{len(mod.PHASES)} PHASES / {len(mod.STEPS)} STEPS</div>"
        f"<div style='font-size:32px;font-weight:800;color:{TEXT}'>{T['icon']} &nbsp;{T['title']}</div>"
        f"</div>", unsafe_allow_html=True)
    st.write("")

    op_header("01", "The Engineering Problem", CIVIL)
    st.markdown(S["problem"])
    st.write("")
    st.divider()

    op_header("02", "What We Are Going To Build", CIVIL)
    st.markdown(S["build_intro"])
    st.write("")
    cols = st.columns(len(S["cards"]))
    for col, (icon, title, body) in zip(cols, S["cards"]):
        with col:
            st.markdown(f"<div class='spec' style='height:100%'>"
                        f"<div class='card-ico'>{icon}</div>"
                        f"<b style='color:{TEXT}'>{title}</b><br>"
                        f"<span class='muted'>{body}</span></div>", unsafe_allow_html=True)
    st.write("")
    st.markdown(f"<div style='border-left:3px solid {GREEN};padding:9px 0 9px 16px;font-size:16px;"
                f"color:{TEXT};line-height:1.65'>{S['promise']}</div>", unsafe_allow_html=True)
    st.write("")
    st.divider()

    op_header("03", "The Engineering Workflow", CIVIL)
    st.markdown(
        f"<div style='color:{MUTED};font-size:15px;line-height:1.6'>These are the {len(mod.PHASES)} "
        f"phases of <b>{S['project_line']}</b>, in the order a real project runs them. "
        f"Every <b style='color:{CIVIL}'>amber node</b> is an engineering activity. Every "
        f"<b style='color:{AISIDE}'>step hanging off it</b> is a page. "
        f"<b>Click any step to open it.</b></div>", unsafe_allow_html=True)
    st.write("")

    fig = mind_map(mod)
    try:
        ev = st.plotly_chart(fig, use_container_width=True, key="mindmap",
                             on_select="rerun", selection_mode="points")
        pts = (ev or {}).get("selection", {}).get("points", [])
        if pts:
            cd = pts[0].get("customdata")
            target = cd[0] if isinstance(cd, list) else cd
            if target in mod.BY_ID:
                goto(target)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, key="mindmap_static")
        st.info("Click-to-open needs Streamlit ≥ 1.35. Use the sidebar to jump to a step.")
    st.divider()

    op_header("04", "Engineering → AI, The Whole Map", AISIDE)
    st.markdown(f"<div style='color:{MUTED};font-size:15px;line-height:1.6'>{S['map_note']}</div>",
                unsafe_allow_html=True)
    st.write("")
    st.plotly_chart(mapping_figure(mod), use_container_width=True, key="mapping")
    st.write("")
    st.markdown(f"<div style='border-left:3px solid {AISIDE};padding:9px 0 9px 16px;font-size:16px;"
                f"color:{TEXT};line-height:1.65'>Each AI concept shows up because the engineering work "
                f"ran into something one person could not do by hand. Only then does it get a technical "
                f"name.</div>", unsafe_allow_html=True)
    st.write("")

    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button(T["start_button"], use_container_width=True, type="primary"):
            goto(mod.ORDER[0])
    with c2:
        st.caption(f"{len(mod.PHASES)} phases · {len(mod.STEPS)} steps · {S['project_line']}. "
                   "Every step opens with the engineering activity, then the AI it becomes.")


# ============================================================ the sidebar + router
def route(mod, STAGES, ALIASES=None):
    """Resolve ?stage=, draw the sidebar, and return the active stage id."""
    stage = st.query_params.get("stage", "start")
    stage = (ALIASES or {}).get(stage, stage)
    if stage not in STAGES:
        stage = "start"

    with st.sidebar:
        st.markdown(f"### {mod.THEME['icon']} {mod.THEME['sidebar_title']}")
        st.caption(mod.THEME["sidebar_note"])
        keys = list(STAGES)
        sel = st.selectbox("Where are we in the project?", keys, index=keys.index(stage),
                           format_func=lambda k: STAGES[k][0])
        if sel != stage:
            st.query_params["stage"] = sel
            st.rerun()

        if stage in mod.BY_ID:
            step = mod.BY_ID[stage]
            pos = mod.ORDER.index(stage) + 1
            pname = mod.PHASES[step["phase"]][0]
            st.progress(pos / len(mod.ORDER),
                        text=f"phase {step['phase']+1}/{len(mod.PHASES)} · {pname}")
            st.markdown(f"<div style='font-size:12px;line-height:1.6'>"
                        f"<span style='color:{MUTED}'>ENGINEERING STEP</span><br>"
                        f"<b style='color:{CIVIL}'>{step['civil']}</b><br>"
                        f"<span style='color:{MUTED}'>IS THE AI CONCEPT</span><br>"
                        f"<b style='color:{AISIDE}'>{step['ai']}</b></div>", unsafe_allow_html=True)
        st.divider()
        if st.button("🗺️  The whole project map", use_container_width=True):
            st.query_params["stage"] = "start"
            st.rerun()
        st.caption("▶ Press **Play** on a chart to animate it.")
    return stage


def footer_nav(STAGES, stage):
    st.divider()
    keys = list(STAGES)
    i = keys.index(stage)
    nav1, nav2 = st.columns(2)
    if i > 0:
        nav1.markdown(f"[← {STAGES[keys[i-1]][0]}](?stage={keys[i-1]})")
    if i < len(keys) - 1:
        nav2.markdown(f"<div style='text-align:right'><a href='?stage={keys[i+1]}'>"
                      f"{STAGES[keys[i+1]][0]} →</a></div>", unsafe_allow_html=True)
