"""
Story stages for the Smart Construction Site course.
=====================================================
These are the narrative beats that make AI *inevitable* for a Civil Engineering
student who has never met it:

  site        - a Tuesday morning. Hazards overlap. One supervisor cannot cope.
  enter-ai    - Human + AI. Not a replacement: a second pair of eyes.
  inspection  - Morning Site Inspection. Reality BECOMES data.
  two-worlds  - numbers vs images. Can one model do both?
  pixel-problem     - 150,528 numbers. Which one is the helmet? None.
  handmade-features - you build a helmet detector by hand. You watch it fail.
  why-dl      - therefore: Deep Learning.
  supervisor-brain  - how a human decides -> that IS a neuron.
  learning-loop     - mistake -> adjust -> repeat, before any terminology.
  audit       - a site audit. The confusion matrix emerges from it.
  fusion-engine     - the actual product: Worker 18, Tunnel Zone, evacuate.
  pipeline    - the whole engineering workflow, start to finish.
"""
import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

BG, PANEL = "#0e1117", "#161b22"
POS, NEG = "#4fc3f7", "#ff8a65"
GREEN, AMBER, RED = "#66bb6a", "#ffb74d", "#ef5350"
MUTED, TEXT = "#8b949e", "#e6edf3"

HAZARDS = ["☠️  Toxic gas", "🌫️  Dust cloud", "🚜  Worker near machine", "⛑️  No helmet"]
HAZ_COLOR = [RED, AMBER, "#ba68c8", "#4dd0e1"]


# ---------------------------------------------------------------- the site
@st.cache_data(show_spinner=False)
def hazard_timeline(T=64):
    """A shift's worth of overlapping hazards, and one supervisor trying to watch."""
    rng = np.random.default_rng(7)
    active = np.zeros((4, T), dtype=bool)
    for i in range(4):
        t = int(rng.integers(0, 6))
        while t < T:
            dur = int(rng.integers(3, 8))
            if t + dur < T:
                active[i, t:t + dur] = True
            t += dur + int(rng.integers(3, 10))
    sup = np.array([(t // 8) % 4 for t in range(T)])          # supervisor: one place at a time
    watched = active[sup, np.arange(T)]
    missed = int(active.sum() - watched.sum())
    return active, sup, missed


def _timeline_fig(active, sup, ai=False):
    T = active.shape[1]
    fig = go.Figure()
    for i in range(4):
        fig.add_trace(go.Scatter(x=list(range(T)), y=[i] * T, mode="lines",
                                 line=dict(color="#222933", width=16), hoverinfo="skip",
                                 showlegend=False))
    blocks = []
    for i in range(4):
        fig.add_trace(go.Scatter(x=[], y=[], mode="markers",
                                 marker=dict(size=15, color=HAZ_COLOR[i], symbol="square"),
                                 hoverinfo="skip", showlegend=False))
        blocks.append(len(fig.data) - 1)
    fig.add_trace(go.Scatter(x=[], y=[], mode="markers",
                             marker=dict(size=26, color="rgba(0,0,0,0)",
                                         line=dict(color="#ffffff", width=3)),
                             name="👁 watching", hoverinfo="skip", showlegend=False))
    eye = len(fig.data) - 1
    fig.add_trace(go.Scatter(x=[], y=[], mode="markers",
                             marker=dict(size=17, color="rgba(0,0,0,0)",
                                         line=dict(color=RED, width=3)),
                             hoverinfo="skip", showlegend=False))
    missmark = len(fig.data) - 1

    frames = []
    seen_miss = []
    for t in range(T):
        data = []
        for i in range(4):
            xs = [k for k in range(t + 1) if active[i, k]]
            data.append(go.Scatter(x=xs, y=[i] * len(xs), mode="markers",
                                   marker=dict(size=15, color=HAZ_COLOR[i], symbol="square")))
        if ai:
            data.append(go.Scatter(x=[t] * 4, y=list(range(4)), mode="markers",
                                   marker=dict(size=26, color="rgba(0,0,0,0)",
                                               line=dict(color=GREEN, width=3))))
        else:
            data.append(go.Scatter(x=[t], y=[sup[t]], mode="markers",
                                   marker=dict(size=26, color="rgba(0,0,0,0)",
                                               line=dict(color="#ffffff", width=3))))
        if not ai:
            for i in range(4):
                if active[i, t] and sup[t] != i:
                    seen_miss.append((t, i))
            data.append(go.Scatter(x=[m[0] for m in seen_miss], y=[m[1] for m in seen_miss],
                                   mode="markers", marker=dict(size=17, color="rgba(0,0,0,0)",
                                                               line=dict(color=RED, width=3))))
            title = (f"minute {t}   ·   supervisor is watching <b>{HAZARDS[sup[t]]}</b>"
                     f"   ·   <span style='color:{RED}'>missed elsewhere: {len(seen_miss)}</span>")
        else:
            data.append(go.Scatter(x=[], y=[], mode="markers",
                                   marker=dict(size=17, color="rgba(0,0,0,0)")))
            title = f"minute {t}   ·   <span style='color:{GREEN}'>AI is watching all 4 · missed: 0</span>"
        frames.append(go.Frame(data=data, traces=blocks + [eye, missmark],
                               layout=go.Layout(title=title), name=str(t)))
    fig.update_yaxes(tickmode="array", tickvals=list(range(4)), ticktext=HAZARDS,
                     range=[-0.6, 3.6])
    fig.update_xaxes(title="minutes into the shift", range=[-1, T])
    return fig, frames


def render_site(style, animate):
    st.title("A Tuesday morning on site")
    st.markdown("#### Four things are going wrong. There is one supervisor.")
    active, sup, missed = hazard_timeline()

    fig, frames = _timeline_fig(active, sup, ai=False)
    fig.update_layout(title="minute 0   ·   the shift begins")
    style(fig, 380); animate(fig, frames, ms=90)
    st.plotly_chart(fig, width="stretch")

    st.caption("⬜ = a hazard is happening   ·   ⚪ = where the supervisor is looking   ·   "
               "🔴 = a hazard nobody saw")

    c1, c2, c3 = st.columns(3)
    c1.metric("Hazard-minutes this shift", int(active.sum()))
    c2.metric("The supervisor caught", int(active.sum()) - missed)
    c3.metric("Nobody was watching", missed, "-{} missed".format(missed), delta_color="inverse")

    st.markdown("### So — can one human watch all of this?")
    st.caption("Every minute of every shift. Every worker. Four hazards at once.")
    if st.button("Answer", type="primary"):
        st.error(f"**No.** Not because the supervisor is bad at their job — because they are *one person*. "
                 f"They can be in one place, looking at one thing. "
                 f"This shift, **{missed} hazard-minutes** happened while they were legitimately "
                 f"looking somewhere else. That is not negligence. That is arithmetic.")
        st.info("👉 So the fix is not a better supervisor — it is a second set of eyes that watches the "
                "other three areas while the supervisor handles the one in front of them. The supervisor "
                "stays in charge; AI just carries the watching one person cannot cover alone.")


def render_enter_ai(style, animate):
    st.title("Enter AI — a second pair of eyes")
    st.markdown("#### Same shift. Same hazards. Nothing else changes.")
    active, sup, missed = hazard_timeline()

    fig, frames = _timeline_fig(active, sup, ai=True)
    fig.update_layout(title="minute 0   ·   this time, something is watching every track")
    style(fig, 380); animate(fig, frames, ms=90)
    st.plotly_chart(fig, width="stretch")

    c1, c2 = st.columns(2)
    c1.metric("Missed — supervisor alone", missed, delta_color="inverse")
    c2.metric("Missed — supervisor + AI", 0, f"-{missed}")

    st.markdown("### Human **+** AI. Never human *vs* AI.")
    a, b = st.columns(2)
    a.markdown("**The supervisor stays in charge of**\n\n- deciding what is acceptable risk\n- talking a "
               "worker down\n- knowing the scaffold was signed off this morning\n- being accountable for "
               "a life\n- judgement — which AI has none of")
    b.markdown("**Where one person needs a hand**\n\n- covering 4 areas at the same time\n- keeping an eye "
               "on 40 workers\n- staying alert for 9 hours straight\n- reading gas at 45 ppm\n- watching "
               "without a break")


# ---------------------------------------------------------------- morning inspection
def render_inspection(get_data, style, animate, site_b64=None):
    st.title("Morning Site Inspection — how the site becomes data")
    st.markdown("#### The AI will never see your construction site.")
    d = get_data()
    row = d["dirty"].iloc[5]

    st.markdown("Workers badge in. Sensors start logging. Cameras start capturing. "
                "Watch what actually reaches the computer:")

    steps = [
        ("🏗️  The real site", "A worker walks into a tunnel. Gas is seeping. It is 38°C. "
                              "An excavator swings 1.2 m behind him.", MUTED),
        ("📡  Sensors read it", "Every device reports a number. Nothing else. No context, no meaning.", POS),
        ("📷  The camera captures it", "A grid of pixels. Not a worker — a grid of brightness values.", AMBER),
        ("📄  It becomes one row", "This row, and that image, are the *entire* world as far as the AI "
                                   "is concerned.", GREEN),
    ]
    i = st.slider("Walk through the morning", 1, 4, 1)
    for k, (t, txt, c) in enumerate(steps, start=1):
        if k <= i:
            st.markdown(f"<div style='padding:12px 16px;margin:6px 0;border-radius:10px;"
                        f"border-left:4px solid {c};background:{PANEL};color:{TEXT}'>"
                        f"<b>{t}</b><br><span style='color:{MUTED}'>{txt}</span></div>",
                        unsafe_allow_html=True)
    if i == 4:
        st.markdown("##### What each sensor reads, and why it matters")
        st.caption("The seven instruments on this site, the quantity each one measures, and the hazard it "
                   "is there to catch:")
        st.dataframe(pd.DataFrame([
            ["📡 Gas", "Toxic / flammable gas", "ppm", "Build-up in the confined tunnel"],
            ["🌫️ Dust", "Airborne particulate", "level 0–1", "Cutting and demolition clouds"],
            ["🌡️ Temperature", "Air temperature", "°C", "Heat stress on workers"],
            ["💧 Humidity", "Relative humidity", "%", "Heat-index and slip conditions"],
            ["📳 Acceleration", "Vibration / jolt", "g", "Plant strike or impact"],
            ["📏 Proximity", "Distance to moving plant", "m", "Worker inside a machine's swing"],
            ["🔊 Noise", "Sound level", "dB", "Hearing damage and masked warnings"],
        ], columns=["Sensor", "What it measures", "Unit", "Hazard it catches"]),
            width="stretch", hide_index=True)

        st.markdown("##### One shift = one row of those seven numbers")
        cols = ["gas_ppm", "dust_level", "temperature_c", "humidity", "accel_mag", "proximity_m", "noise_db"]
        st.dataframe(pd.DataFrame([row[cols].values], columns=[
            "Gas (ppm)", "Dust", "Temp (°C)", "Humidity", "Accel (g)", "Proximity (m)", "Noise (dB)"]),
            width="stretch", hide_index=True)
        st.info("The AI never sees your site — only this row. If the row is wrong, the prediction is "
                "wrong, and the model has no way to notice. That is why the next four stages are about "
                "the data, not the model.")


# ---------------------------------------------------------------- two worlds
def render_two_worlds(style):
    st.title("Two worlds on one site")
    st.markdown("#### The site produces two completely different kinds of data.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"<div style='padding:18px;border-radius:12px;border:2px solid {POS};"
                    f"background:{PANEL}'><h4 style='margin:0;color:{POS}'>🔢 World 1 — Numbers</h4>"
                    f"<p style='color:{MUTED};margin:8px 0 0'>Gas · Dust · Temperature · Humidity · "
                    f"Noise · Acceleration · Proximity</p></div>", unsafe_allow_html=True)
        st.markdown("- Tidy. 7 columns.\n- A human already **named** every column.\n"
                    "- “Gas = 420” already *means* something.")
    with c2:
        st.markdown(f"<div style='padding:18px;border-radius:12px;border:2px solid {AMBER};"
                    f"background:{PANEL}'><h4 style='margin:0;color:{AMBER}'>🖼️ World 2 — Images</h4>"
                    f"<p style='color:{MUTED};margin:8px 0 0'>Workers · Helmets · Safety vests · "
                    f"Machinery</p></div>", unsafe_allow_html=True)
        st.markdown("- 150,528 numbers per frame.\n- **No** column is named.\n"
                    "- No single number means anything.")
    st.markdown("### One question decides this whole course")
    st.subheader("Can one kind of AI handle both worlds?")
    st.caption("Hold that question. We are going to answer it by trying.")
    st.info("**The promise:** Machine Learning learns from columns a human defined. "
            "Deep Learning learns useful features directly from raw data.\n\n"
            "We will not tell you which is better. We will make you watch one of them fail.")


# ---------------------------------------------------------------- pixel problem
def render_pixel_problem(cnn_meta, asset, style):
    st.title("The pixel problem")
    imgs, preds = cnn_meta()
    if not imgs:
        st.error("cnn_assets/ not found."); return
    name = imgs[min(3, len(imgs) - 1)]
    from PIL import Image
    im = Image.open(asset(name, "input.png")).convert("RGB").resize((224, 224))
    arr = np.asarray(im)

    st.markdown("#### Here is what *you* see.")
    st.image(arr, width=300, caption="A worker. Wearing a hard hat. Obvious.")

    st.markdown("#### Here is what the computer receives.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Width × Height × Colors", "224 × 224 × 3")
    c2.metric("Total numbers", f"{224*224*3:,}")
    c3.metric("Numbers labeled “helmet”", "0")

    st.markdown("##### Zoom in anywhere and look at the actual values")
    z1, z2 = st.columns(2)
    r = z1.slider("Row", 0, 216, 60)
    c0 = z2.slider("Column", 0, 216, 120)
    patch = arr[r:r + 8, c0:c0 + 8]
    gray = patch.mean(axis=2)
    fig = go.Figure(go.Heatmap(z=gray[::-1], colorscale="gray", showscale=False,
                               text=gray[::-1].astype(int), texttemplate="%{text}",
                               textfont=dict(size=10)))
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
    fig.update_layout(title=f"an 8×8 patch at ({r}, {c0}) — this is literally what arrives")
    style(fig, 380)
    st.plotly_chart(fig, width="stretch")
    px = arr[r, c0]
    st.code(f"pixel({r}, {c0}) = R:{px[0]}  G:{px[1]}  B:{px[2]}")

    st.markdown("### So — which of these 150,528 numbers is the helmet?")
    if st.button("Point at it", type="primary"):
        st.error("**None of them.** Not one. There is no helmet number, no helmet column, no helmet "
                 "anywhere in this data. “Helmet” is not *in* any pixel — it only exists in the "
                 "**relationship between thousands of them**.")
        st.info("A Machine Learning model needs columns. Someone must hand it *“helmet_color”*, "
                "*“helmet_shape”*, *“helmet_area”*. \n\nSo let's do exactly that. Let's build those "
                "columns by hand — the way engineers did for 40 years — and see how far it gets us. →")


# ---------------------------------------------------------------- hand-made features
@st.cache_data(show_spinner=False)
def yellow_fraction(path):
    """Our hand-engineered 'helmet_color' feature: fraction of strong hard-hat yellow.
    Thresholds are strict on purpose — a loose rule just counts skin and beige walls."""
    from PIL import Image
    a = np.asarray(Image.open(path).convert("RGB").resize((224, 224))).astype(float) / 255.0
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return float((((r > 0.65) & (g > 0.55) & (b < 0.30) & ((r + g) / 2 - b > 0.35))).mean())


def render_handmade(cnn_meta, asset, style):
    st.title("Build the helmet detector by hand")
    st.markdown("#### No AI. Just engineering judgement — the way it was done for 40 years.")
    imgs, preds = cnn_meta()
    if not imgs:
        st.error("cnn_assets/ not found."); return

    st.markdown("Helmets are **yellow**. That's a rule. Let's write it: count the yellow pixels, "
                "and if there are enough, call it a helmet. Tune your own threshold — take your time:")
    thr = st.slider("A helmet is present if yellow pixels exceed…", 0.05, 3.0, 0.5, 0.05,
                    format="%.2f%%") / 100.0

    truth = {"helmet_00": True, "helmet_01": True, "helmet_02": True,
             "helmet_03": True, "helmet_04": True}
    note = {"helmet_00": "two yellow hard hats", "helmet_01": "yellow hard hat on a box",
            "helmet_02": "**red** helmet, worn", "helmet_03": "yellow hard hat, worn",
            "helmet_04": "**white** helmet, worn"}
    rows, correct = [], 0
    for n in imgs:
        frac = yellow_fraction(asset(n, "input.png"))
        says = frac > thr
        ok = says == truth.get(n, True)
        correct += ok
        rows.append({"Frame": n, "What it is": note.get(n, ""),
                     "Yellow pixels": f"{frac*100:.2f}%",
                     "Your rule says": "helmet ✅" if says else "no helmet ❌",
                     "Reality": "helmet" if truth.get(n, True) else "no helmet",
                     "": "✅" if ok else "💥 WRONG"})
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    c1, c2 = st.columns(2)
    c1.metric("Your hand-made detector", f"{correct}/{len(imgs)} correct")
    c2.metric("Rules you had to invent", "1", "and it already broke")

    st.error("**Watch it break.** Every frame here contains a helmet. But `helmet_02` is **red** and "
             "`helmet_04` is **white** — your yellow rule is blind to both. There is no threshold you "
             "can drag that fixes this. Go on, try.")

    st.markdown("### So fix it. Add more rules.")
    f1, f2, f3 = st.columns(3)
    f1.checkbox("Add “also detect red”", key="hm_red")
    f2.checkbox("Add “also detect white”", key="hm_white")
    f3.checkbox("Add “must be round”", key="hm_round")
    if st.session_state.get("hm_red"):
        st.warning("🚧 Now it flags the **red toolbox**, the red hoarding, and a worker's red jacket.")
    if st.session_state.get("hm_white"):
        st.warning("🚧 Now it flags **the sky**, white vans, and every painted wall on site.")
    if st.session_state.get("hm_round"):
        st.warning("🚧 “Round” needs edge detection, contour fitting and a size threshold — and it still "
                   "flags wheels, buckets, drums and the top of every bollard.")
    if any(st.session_state.get(k) for k in ["hm_red", "hm_white", "hm_round"]):
        st.info("**This is the trap.** Every rule you add to catch one case creates two new false alarms. "
                "Engineers spent *decades* here. And you still have to write rules for: dusty helmets, "
                "helmets at night, helmets from behind, helmets in shadow, helmets at 30°, "
                "helmets half-hidden by scaffolding…")


def render_why_dl(style):
    st.title("Therefore: Deep Learning")
    st.markdown("#### You just proved it yourself. Nobody had to tell you.")
    st.markdown("""
| | You just tried this | And found |
|---|---|---|
| **On numbers** | Gas, dust, proximity — already named columns | ✅ works fine, ML is happy |
| **On pixels** | Hand-write `helmet_color`, `helmet_shape`… | 💥 broke on the second image |
""")
    st.markdown("### The one idea")
    c1, c2 = st.columns(2)
    c1.markdown(f"<div style='padding:20px;border-radius:12px;border:2px solid {POS};background:{PANEL}'>"
                f"<b style='color:{POS}'>MACHINE LEARNING</b><br><br>A human defines the features.<br>"
                f"The model just weighs them.<br><br><i style='color:{MUTED}'>Only as good as the "
                f"columns you invented.</i></div>", unsafe_allow_html=True)
    c2.markdown(f"<div style='padding:20px;border-radius:12px;border:2px solid {AMBER};background:{PANEL}'>"
                f"<b style='color:{AMBER}'>DEEP LEARNING</b><br><br>The model finds the features.<br>"
                f"Straight from raw data.<br><br><i style='color:{MUTED}'>Nobody names anything. "
                f"It digs them out itself.</i></div>", unsafe_allow_html=True)
    st.info("**Deep learning earns its place right here.** It is the tool for the problem you just "
            "hit: one that has no columns, and that no human can write them for.")
    st.caption("Now it makes sense to ask *how* a machine finds features by itself. →")


# ---------------------------------------------------------------- supervisor brain
def render_supervisor_brain(style):
    st.title("How does a supervisor actually decide?")
    st.markdown("#### Forget AI. Watch a human think for a second.")
    st.caption("A supervisor walks up to a location and asks themselves a few things:")

    c1, c2 = st.columns([1, 1])
    with c1:
        gas = st.checkbox("Is the gas high?", value=True)
        noise = st.checkbox("Is the noise bad?", value=False)
        near = st.checkbox("Is the worker near the excavator?", value=True)
        temp = st.checkbox("Is it dangerously hot?", value=False)
        st.caption("But they don't count these equally…")
        w_gas = st.slider("How much does gas matter?", 0.0, 1.0, 0.9, 0.05)
        w_noise = st.slider("How much does noise matter?", 0.0, 1.0, 0.2, 0.05)
        w_near = st.slider("How much does proximity matter?", 0.0, 1.0, 0.8, 0.05)
        w_temp = st.slider("How much does heat matter?", 0.0, 1.0, 0.4, 0.05)
        thresh = st.slider("How much worry before they act?", 0.0, 2.0, 1.0, 0.05)

    obs = [gas, noise, near, temp]
    ws = [w_gas, w_noise, w_near, w_temp]
    names = ["Gas high", "Noise bad", "Near machine", "Too hot"]
    total = sum(o * w for o, w in zip(obs, ws))

    with c2:
        fig = go.Figure(go.Bar(
            x=[o * w for o, w in zip(obs, ws)], y=names, orientation="h",
            marker_color=[POS if o else "#2b3340" for o in obs],
            text=[f"{o*w:.2f}" for o, w in zip(obs, ws)], textposition="outside"))
        fig.add_vline(x=thresh, line=dict(color=RED, width=3, dash="dash"),
                      annotation_text="acts", annotation_font_color=RED)
        fig.update_xaxes(range=[0, 2.2], title="how much this worries the supervisor")
        fig.update_layout(title=f"total worry = {total:.2f}")
        style(fig, 380)
        st.plotly_chart(fig, width="stretch")
        if total > thresh:
            st.error(f"🚨 **“Stop work.”**  ({total:.2f} > {thresh:.2f})")
        else:
            st.success(f"✅ **“Carry on.”**  ({total:.2f} ≤ {thresh:.2f})")

    st.markdown("### Now look at what you just built")
    st.markdown("""
| The supervisor | The machine calls it |
|---|---|
| The things they notice | **inputs** |
| How much each thing worries them | **weights** |
| How much worry before acting | **bias** (the threshold) |
| Adding up the worry | **weighted sum** |
| Deciding stop / carry on | **activation** |
""")
    st.success("**You just built a neuron.** Not a metaphor for one — the actual thing. "
               "A neuron is a supervisor who only ever looks at numbers, and never gets tired.")
    st.caption("So the maths on the next page isn't new. It's this page, written down. →")


# ---------------------------------------------------------------- learning loop
def render_learning_loop(style, animate):
    st.title("How does it get *better*?")
    st.markdown("#### No maths on this page. Just the idea.")
    st.caption("A new supervisor on their first day has no idea how much gas should worry them. "
               "So how does anyone learn that?")

    loop = ["🤔  Make a guess", "❌  Be wrong", "📏  Measure how wrong",
            "🔧  Adjust a little", "🤔  Guess again", "🙂  Be less wrong"]
    guesses = [0.90, 0.72, 0.55, 0.41, 0.30, 0.22, 0.16, 0.11, 0.08, 0.06, 0.05, 0.04]
    fig = go.Figure(go.Scatter(x=[0], y=[guesses[0]], mode="lines+markers",
                               line=dict(color=RED, width=3), marker=dict(size=9)))
    frames = [go.Frame(data=[go.Scatter(x=list(range(k + 1)), y=guesses[:k + 1],
                                        mode="lines+markers",
                                        line=dict(color=RED if k < 4 else AMBER if k < 8 else GREEN,
                                                  width=3), marker=dict(size=9))],
                       layout=go.Layout(title=f"attempt {k+1} — how wrong we were: {guesses[k]:.2f}"),
                       name=str(k)) for k in range(len(guesses))]
    fig.update_xaxes(title="attempt", range=[-0.3, len(guesses)])
    fig.update_yaxes(title="how wrong we were", range=[0, 1])
    fig.update_layout(title="attempt 1 — how wrong we were: 0.90")
    style(fig, 360); animate(fig, frames, ms=380)
    st.plotly_chart(fig, width="stretch")

    cols = st.columns(6)
    for c, s in zip(cols, loop):
        c.markdown(f"<div style='padding:10px;border-radius:8px;text-align:center;background:{PANEL};"
                   f"color:{TEXT};font-size:12px;height:70px;display:flex;align-items:center;"
                   f"justify-content:center'>{s}</div>", unsafe_allow_html=True)

    st.info("**That's it. That's learning.** Guess, measure the mistake, adjust a little, repeat. "
            "A child learning to catch a ball does this. You did it learning to reverse a truck.")

    st.markdown("### Only now, the four words")
    st.markdown("""
| The idea you just watched | Its official name | Its own stage |
|---|---|---|
| “How wrong were we?” | **Loss function** | [Explore →](?stage=loss) |
| “Which way should I adjust?” | **Gradient descent** | [Explore →](?stage=gradient-descent) |
| “How big an adjustment?” | **Learning rate** | [Explore →](?stage=learning-rate) |
| “What's the smartest way to adjust?” | **Optimizer** | [Explore →](?stage=optimizer) |
""")
    st.caption("Four intimidating words. One simple loop. You understood the loop first — "
               "that was the whole point.")


# ---------------------------------------------------------------- site audit
def render_audit(get_data, get_models, style, animate):
    st.title("The site audit")
    st.markdown("#### Forget metrics. Let's just audit the AI, the way you'd audit a subcontractor.")
    d = get_data(); rf, mlp = get_models()
    from sklearn.metrics import confusion_matrix, accuracy_score
    yte = d["yte"]; pred = mlp.predict(d["Xte"])
    n = min(100, len(yte))
    yt, yp = yte[:n], pred[:n]

    st.caption(f"**{n} shifts** happened on this site. We know what really happened on each one "
               "(the incident log). The AI made a call on each one. Let's line them up.")

    tp = int(((yt == 1) & (yp == 1)).sum()); tn = int(((yt == 0) & (yp == 0)).sum())
    fp = int(((yt == 0) & (yp == 1)).sum()); fn = int(((yt == 1) & (yp == 0)).sum())

    step = st.slider("Walk the audit", 1, 4, 1)
    boxes = [
        ("✅ AI said SAFE — and it was safe", tn, GREEN,
         "Nothing happened. AI said nothing would. Good."),
        ("✅ AI said RISK — and there was an incident", tp, GREEN,
         "The AI called it. A supervisor was sent. This is the win."),
        ("⚠️ AI said RISK — but nothing happened", fp, AMBER,
         "A false alarm. Annoying. The supervisor walked over for nothing. Cost: ten minutes."),
        ("🚨 AI said SAFE — but someone got hurt", fn, RED,
         "The AI missed it. Nobody was sent. **Cost: a person.**"),
    ]
    for k, (t, v, c, why) in enumerate(boxes[:step], start=1):
        st.markdown(f"<div style='padding:14px 18px;margin:6px 0;border-radius:10px;"
                    f"border-left:5px solid {c};background:{PANEL}'>"
                    f"<b style='color:{c}'>{t}</b> &nbsp;→&nbsp; <b style='font-size:20px'>{v}</b> shifts"
                    f"<br><span style='color:{MUTED}'>{why}</span></div>", unsafe_allow_html=True)

    if step == 4:
        st.markdown("##### Put those four boxes in a square, and you've built this:")
        cm = np.array([[tn, fp], [fn, tp]])
        fig = go.Figure(go.Heatmap(z=cm, x=["AI said SAFE", "AI said RISK"],
                                   y=["Really safe", "Really an incident"],
                                   colorscale="Blues", text=cm, texttemplate="%{text}",
                                   textfont=dict(size=22), showscale=False))
        fig.update_layout(title="…this is the confusion matrix. You just derived it.")
        style(fig, 380)
        st.plotly_chart(fig, width="stretch")
        st.success("**You didn't learn a confusion matrix. You built one by auditing a site.**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Accuracy", f"{(tp+tn)/n:.1%}", "how often it was right")
        c2.metric("False alarms", fp, "cost: ten minutes")
        c3.metric("Missed incidents", fn, "cost: a person", delta_color="inverse")
        st.error("**Never quote accuracy alone on a safety system.** A model that says “safe” to "
                 "everything would score well here — and kill someone. The only number that matters "
                 "on this page is the red one.")


# ---------------------------------------------------------------- fusion engine
def render_fusion_engine(style):
    st.title("The Fusion Engine — the actual product")
    st.markdown("#### No single model runs a safe site. This is what you'd actually ship.")

    st.caption("Every real commercial AI system is several models and several sensors, fused. "
               "Set the site conditions and watch the engine reason:")
    c1, c2, c3, c4 = st.columns(4)
    helmet = c1.toggle("Helmet detected", value=False)
    vest = c2.toggle("Safety vest detected", value=True)
    gas = c3.slider("Gas (ppm)", 0, 100, 45)
    zone = c4.selectbox("Zone (GPS)", ["Open ground", "Tunnel Zone", "Crane radius"], index=1)
    worker = st.selectbox("Worker (RFID tag)", [f"Worker {i}" for i in [12, 18, 24, 31]], index=1)

    inputs = [
        ("📷 Camera → CNN", "Helmet: **present**" if helmet else "Helmet: **MISSING**", GREEN if helmet else RED),
        ("📷 Camera → CNN", "Vest: **present**" if vest else "Vest: **MISSING**", GREEN if vest else AMBER),
        ("📡 Gas sensor → ANN", f"**{gas} ppm** " + ("(safe)" if gas < 30 else "(**toxic**)"),
         GREEN if gas < 30 else RED),
        ("🛰️ GPS", f"**{zone}**" + (" — confined space" if zone == "Tunnel Zone" else ""),
         RED if zone == "Tunnel Zone" else MUTED),
        ("🏷️ RFID", f"**{worker}**", MUTED),
    ]
    st.markdown("##### Each model reports, alone and blind to the others")
    for src, val, c in inputs:
        st.markdown(f"<div style='padding:9px 14px;margin:4px 0;border-radius:8px;"
                    f"border-left:4px solid {c};background:{PANEL};color:{TEXT}'>"
                    f"<span style='color:{MUTED}'>{src}</span> &nbsp;→&nbsp; {val}</div>",
                    unsafe_allow_html=True)

    danger = 0
    reasons = []
    if not helmet:
        danger += 2; reasons.append("no helmet")
    if not vest:
        danger += 1; reasons.append("no hi-vis vest")
    if gas >= 30:
        danger += 2; reasons.append(f"toxic gas at {gas} ppm")
    if zone == "Tunnel Zone":
        danger += 1; reasons.append("confined space (tunnel)")
    if zone == "Crane radius":
        danger += 1; reasons.append("inside crane radius")

    st.markdown("##### The Fusion Engine combines them")
    if danger >= 4:
        lvl, col = "🚨 IMMEDIATE EVACUATION", RED
    elif danger >= 2:
        lvl, col = "⚠️ SUPERVISOR DISPATCH", AMBER
    elif danger >= 1:
        lvl, col = "🟡 LOG AND MONITOR", "#c9a227"
    else:
        lvl, col = "✅ ALL CLEAR", GREEN
    st.markdown(
        f"<div style='padding:22px;border-radius:12px;background:{col};color:#0e1117'>"
        f"<div style='font-size:24px;font-weight:800'>{lvl}</div>"
        f"<div style='font-size:17px;margin-top:8px'><b>{worker}</b> · {zone}</div>"
        f"<div style='margin-top:6px'>{' · '.join(reasons) if reasons else 'no hazards detected'}</div>"
        f"</div>", unsafe_allow_html=True)

    st.markdown("### Why fusion is the whole game")
    a, b = st.columns(2)
    a.markdown("**Alone, each model is nearly useless**\n\n"
               "- The camera sees no helmet — *so what? He might be in the site office.*\n"
               "- The gas sensor reads 45 ppm — *so what? Nobody may be there.*\n"
               "- GPS says Tunnel Zone — *so what? He might be perfectly kitted out.*")
    b.markdown("**Together, they are an emergency**\n\n"
               "- **Worker 18**, *identified*\n- in the **Tunnel Zone**, *a confined space*\n"
               "- with **no helmet**\n- breathing **45 ppm** of toxic gas\n\n"
               "→ **Get him out. Now.**")
    st.success("**This is what an AI engineer actually builds.** Not a neural network — a *system*. "
               "Several models, several sensors, one decision, one human who acts on it.")


# ---------------------------------------------------------------- pipeline
def render_pipeline(style):
    st.title("The whole thing, start to finish")
    st.markdown("#### This is what you actually learned. It was never “a neural network”.")
    steps = [
        ("🏗️", "Construction Site", "Real workers. Real hazards. One overwhelmed supervisor.", MUTED),
        ("📡", "Sensors + Cameras", "Instrument the site. Numbers and pixels.", POS),
        ("📄", "Data Collection", "Reality becomes rows. The AI never sees the site itself.", POS),
        ("🧹", "Data Cleaning", "Remove the damaged bricks — dead sensors, impossible values.", POS),
        ("📐", "Data Preparation", "Standardize the materials. Split practice from final inspection.", POS),
        ("🤖", "Machine Learning", "Works beautifully — on the columns a human named.", AMBER),
        ("🧠", "Deep Learning", "Needed the moment there are no columns. Finds features itself.", AMBER),
        ("🔗", "Fusion Engine", "Combine every model and every sensor into one call.", GREEN),
        ("📊", "Risk Prediction", "Worker 18 · Tunnel Zone · no helmet · 45 ppm.", GREEN),
        ("🔔", "Supervisor Alert", "A human is told the three things that matter right now.", GREEN),
        ("🦺", "Safer Construction Site", "Somebody goes home tonight who might not have.", GREEN),
    ]
    for i, (e, t, d, c) in enumerate(steps):
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:14px;padding:11px 16px;margin:3px 0;"
            f"border-radius:10px;border-left:5px solid {c};background:{PANEL}'>"
            f"<span style='font-size:26px'>{e}</span><span><b style='color:{TEXT}'>{t}</b><br>"
            f"<span style='color:{MUTED};font-size:13px'>{d}</span></span></div>",
            unsafe_allow_html=True)
        if i < len(steps) - 1:
            st.markdown(f"<div style='text-align:center;color:{MUTED};margin:-4px 0;font-size:15px'>↓</div>",
                        unsafe_allow_html=True)

    st.markdown("### What to take away")
    st.success("**AI is an engineering pipeline, not a neural network.** The network is one box in the "
               "middle. Everything either side of it — the sensors, the cleaning, the fusion, the human "
               "who acts — is where a real system is won or lost.")
    st.info("If you remember one thing: **Deep Learning exists because of the wall you hit trying to "
            "hand-write “helmet”.** That's all. That's the whole reason. Everything else is detail.")
    st.caption("Human **+** AI. The supervisor was never replaced — they were given eyes everywhere.")
