"""
Rebuild Smart_Construction_Site_DL.ipynb with the Civil-Engineering -> AI scaffold.
===================================================================================
    py -3.13 tools/rebuild_notebook.py

WHAT THIS DOES NOT DO: it does not touch a single line of code. Every code cell in
the source notebook is copied through by index, byte for byte, in its original
order, and so is every interstitial markdown cell that carries a teaching payoff
(the "which of these 150,528 numbers is the helmet? None." cell, the "you just
built a neuron" table, the "never quote accuracy alone" warning, and so on).

WHAT IT DOES: it replaces each stage's *header* and *trailer-link* markdown with
the five-part structure, and appends a Part 5. The teaching text is imported from
bridge.STEPS - the SAME registry the Streamlit app renders - so the notebook and
the app can never drift apart. Edit bridge.STEPS, re-run this, both update.

Cell layout produced per stage:

    [ Part 1 + Part 2 ]   generated   (site context, then the challenge)
    [ Part 3 + link   ]   generated   (the AI connection, the bridge table, the 🎬 link)
    [ code / payoff md ]  VERBATIM    (Part 4 - the technical explanation)
    [ Part 5           ]  generated   (notebook connection, phase trail, prev/next)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
sys.path.insert(0, BASE)

import bridge  # noqa: E402  - the single source of truth for all teaching content

NB = os.path.join(BASE, "Smart_Construction_Site_DL.ipynb")
APP = "https://smartsite-dl.streamlit.app"   # placeholder host; swapped after deploy

# ----------------------------------------------------------------------------
# THE SPEC
# (stage_id, header_cell_to_drop, [cells to copy through VERBATIM])
#
# header=None means the stage had no header cell of its own in the source
# notebook. 'neuron' is the case: its lead-in was cell 48, which is really
# supervisor-brain's payoff (the "you just built a neuron" table), so cell 48
# is KEPT under supervisor-brain and neuron gets a freshly generated opener.
#
# The anchor cell (the old 🎬 link line) is always header+1 and is always
# regenerated, so it is never listed here.
# ----------------------------------------------------------------------------
SPEC = [
    ("site",              0,    [2]),
    ("enter-ai",          3,    []),
    ("inspection",        5,    [7, 8, 9]),
    ("two-worlds",        10,   []),
    ("load",              12,   [14]),
    ("inspect",           15,   [17]),
    ("clean",             18,   [20]),
    ("normalize",         21,   [23]),
    ("split",             24,   [26]),
    ("ml-baseline",       27,   [29, 30]),
    ("pixel-problem",     31,   [33, 34, 35, 36]),
    ("handmade-features", 37,   [39, 40, 41, 42]),
    ("why-dl",            43,   []),
    ("supervisor-brain",  45,   [47, 48]),
    ("neuron",            None, [50]),          # anchor 49; see note above
    ("activation",        51,   [53]),
    ("learning-loop",     54,   []),
    ("loss",              56,   [57]),          # no 🎬 anchor in the source
    ("gradient-descent",  58,   [59]),          # no 🎬 anchor in the source
    ("learning-rate",     60,   [61]),          # no 🎬 anchor in the source
    ("optimizer",         62,   []),
    ("network",           64,   [66]),
    ("training",          67,   [69]),
    ("cnn-journey",       70,   [72, 73, 74, 75, 76]),
    ("gradcam",           77,   [79, 80]),
    ("audit",             81,   [83, 84, 85, 86]),
    ("proof",             87,   [89]),
    ("fusion-engine",     90,   [92, 93]),
    ("pipeline",          94,   []),
]

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕㉖㉗㉘㉙"


def flow(text):
    """Triple-quoted source -> one markdown paragraph."""
    return " ".join(text.split())


def md(*chunks):
    body = "\n".join(chunks)
    return {"cell_type": "markdown", "metadata": {}, "source": body.splitlines(True)}


def phase_trail(pi):
    bits = []
    for i, (pname, _) in enumerate(bridge.PHASES):
        if i < pi:
            bits.append(f"✅ {pname}")
        elif i == pi:
            bits.append(f"🔶 **{pname}** ← you are here")
        else:
            bits.append(f"⬜ {pname}")
    return " · ".join(bits)


def part12(step, n):
    pname, pdesc = bridge.PHASES[step["phase"]]
    return md(
        "---",
        "",
        f"# {CIRCLED[n]} {step['civil_icon']} {step['civil']}",
        f"### Phase {step['phase']+1} of 12 · {pname} — *{pdesc}*",
        "",
        f"> The engineering activity on this page is also, exactly, the AI concept "
        f"**{step['ai']}**. Here is why.",
        "",
        "## Part 1 · On the construction site",
        "",
        flow(step["site"]),
        "",
        "## Part 2 · The engineering challenge",
        "",
        flow(step["challenge"]),
    )


def part3(step):
    rows = "\n".join(
        f"| {c} | → | {a} |"
        for c, a in zip(step["civil_bullets"], step["ai_bullets"]))
    return md(
        "## Part 3 · Where the AI comes in",
        "",
        flow(step["ai_link"]),
        "",
        f"| {step['civil_icon']} **On the site** | → | {step['ai_icon']} **In the AI** |",
        "|---|:-:|---|",
        rows,
        "",
        f"**{step['civil']}** → *becomes* → **{step['ai']}** → *which is computed as* → "
        f"`{step['tech']}`",
        "",
        f"> 🎬 **See this animated, with narration:** "
        f"[`smartsite-dl.streamlit.app/?stage={step['id']}`]({APP}/?stage={step['id']})",
        "",
        "## Part 4 · The technical explanation",
        "",
        f"You now know what **{step['civil']}** is, why it is hard, and why it needs "
        f"**{step['ai']}**. Only now, the mechanism.",
    )


def part5(step, i):
    prev_s = bridge.BY_ID[bridge.ORDER[i - 1]] if i > 0 else None
    next_s = bridge.BY_ID[bridge.ORDER[i + 1]] if i < len(bridge.ORDER) - 1 else None
    nav = []
    if prev_s:
        nav.append(f"◀ *Previous engineering step:* "
                   f"[{prev_s['civil']}]({APP}/?stage={prev_s['id']})")
    nav.append(f"**You are here: {step['civil']}**")
    if next_s:
        nav.append(f"*Next engineering step:* "
                   f"[{next_s['civil']}]({APP}/?stage={next_s['id']}) ▶")
    return md(
        "## Part 5 · What you just built",
        "",
        f"**Where you implement it** — {flow(step['notebook'])}",
        "",
        f"**What it contributes to the finished system** — {flow(step['contributes'])}",
        "",
        f"<sub>{phase_trail(step['phase'])}</sub>",
        "",
        " &nbsp;|&nbsp; ".join(nav),
    )


def opening():
    """The four sections of the project overview, as the notebook's first cells."""
    mapping = "\n".join(
        f"| {s['civil_icon']} {s['civil']} | → | {s['ai_icon']} {s['ai']} | {s['phase']+1} |"
        for s in bridge.STEPS)

    workflow = []
    for pi, (pname, pdesc) in enumerate(bridge.PHASES):
        kids = bridge._phase_steps(pi)
        links = " · ".join(f"[{k['short']}]({APP}/?stage={k['id']})" for k in kids)
        workflow.append(f"| **{pi+1}. {pname}** | {pdesc} | {links} |")

    c1 = md(
        "# 🏗️ Building an Intelligent Construction Site",
        "## Machine Learning vs Deep Learning, for Civil Engineers",
        "",
        "> You are not here to learn Artificial Intelligence. You are here to solve a "
        "**construction engineering problem** — one that is genuinely unsolvable by a human "
        "being, for reasons that are arithmetic rather than effort. AI is going to turn up in "
        "the middle of it, because the engineering requires it. Not before.",
        "",
        "---",
        "",
        "## 1 · The engineering problem",
        "",
        "It is 07:40 on a Tuesday. This is not a dramatic day. This is a completely ordinary one.",
        "",
        "**Eighteen workers** are on site, spread across four areas that cannot be seen from one "
        "another: a confined-space tunnel drive, an open yard, and two upper working decks "
        "reached by a single hoist. They are not in one gang. They arrive, badge in, and disperse "
        "within about nine minutes.",
        "",
        "**Six machines** are live. A 20-tonne excavator is slewing near the hoarding, and its "
        "counterweight sweeps through a space that people walk through. A concrete pour is running "
        "on Deck 2. There is a cutting station in the yard, a tower crane over all of it, two "
        "dumpers on the haul road.",
        "",
        "**The hazards do not queue.** Gas is seeping in the tunnel — the meter reads 45 ppm and "
        "drifting up. The cutting station is throwing dust across the yard, so visibility at the "
        "far end is poor. A banksman has stepped inside the excavator's slew radius, and he is "
        "looking at his feet, because the ground is bad. It is 38°C, which is the temperature at "
        "which people quietly take their helmet off, and two people already have.",
        "",
        "**And nobody can hear anything.** The ambient noise is such that a shout carries perhaps "
        "fifteen metres. The radio helps, if the person you need is holding theirs and is not "
        "inside the tunnel.",
        "",
        "**There is one supervisor.** Not a careless one — a good one, twenty years on sites, the "
        "person you would want. And here is the entire problem, in one sentence: they have one "
        "pair of eyes and can stand in exactly one place.",
        "",
        "> Every minute that supervisor spends watching the tunnel is a minute not spent watching "
        "the excavator. This is not a training problem, an attitude problem, or something a "
        "toolbox talk fixes. It is arithmetic: one observer, four simultaneous hazards, nine "
        "hours.",
        ">",
        "> ### Can one human being watch all of this?",
        "",
        "You already know the answer, and it is no. Not because they are bad at their job. Because "
        "of arithmetic. Hold that thought — everything in this notebook exists to serve it.",
    )

    c2 = md(
        "---",
        "",
        "## 2 · What we are going to build",
        "",
        "An **intelligent construction monitoring system**. Concretely, four parts:",
        "",
        "| | Part | What it does |",
        "|---|---|---|",
        "| 📡 | **Sensors observe the conditions** | Gas, dust, temperature, humidity, noise, "
        "vibration, proximity to plant — read continuously, on every shift, whether or not "
        "anybody is standing there. |",
        "| 📷 | **Cameras observe the workers** | The tunnel portal, the decks, the yard. Watching "
        "for the thing no gauge can measure: is that person wearing their helmet? |",
        "| 🔗 | **AI combines both** | Neither stream means much alone. A missing helmet in the "
        "site office is nothing. A missing helmet in a gas-filled tunnel is an emergency. Only "
        "the combination is a decision. |",
        "| 🔔 | **The supervisor gets an alert** | Not a dashboard. Not a report next week. A "
        "specific, named, actionable call: worker 18, tunnel zone, no helmet, 45 ppm, get him "
        "out. |",
        "",
        "> **Be clear about the goal, because it is not automation.** Nothing here replaces the "
        "supervisor, and nothing here stops the works by itself. The supervisor is still in "
        "charge, still accountable, still the one who walks over and looks a crew in the eye. "
        "The system does the one thing a human cannot: **it never looks away.** "
        "The goal is not an automated site. The goal is a **safer** site.",
    )

    c3 = md(
        "---",
        "",
        "## 3 · The engineering workflow",
        "",
        "This is not a syllabus, and these are not chapters. This is **one construction day**, "
        "from the morning inspection to the moment an accident does not happen — twelve phases, "
        "in the order a real project actually runs them. Every AI concept in this notebook hangs "
        "off one of them.",
        "",
        "| Phase | On the site | Steps (click for the animated version) |",
        "|---|---|---|",
        *workflow,
        "",
        "*Run this notebook top to bottom and you walk that day in order.*",
    )

    c4 = md(
        "---",
        "",
        "## 4 · Engineering → AI, the whole map",
        "",
        "This is the most important table in the project, so spend a minute on it before you "
        "start. **Every single AI concept in this notebook is a construction activity you "
        "already understand.** Not 'similar to'. Not 'a useful analogy for'. The same thing, "
        "given a different name by a different profession.",
        "",
        "Read down the left column and you have described a construction day. Read down the right "
        "column and you have described a complete deep learning pipeline. **They are the same "
        "column.**",
        "",
        "| 🏗️ Civil Engineering process | → | 🤖 The AI process that solves it | Phase |",
        "|---|:-:|---|:-:|",
        *mapping.splitlines(),
        "",
        "> Notice what that means for how you read the rest of this notebook. You will never be "
        "asked to learn an AI concept because it is on a syllabus. Every one of them shows up "
        "because the construction day ran into something a human could not do — and then, and "
        "only then, does it get a technical name.",
        "",
        "---",
        "",
        "### Now: it is Tuesday morning.",
    )
    return [c1, c2, c3, c4]


def main():
    with open(NB, encoding="utf-8") as f:
        nb = json.load(f)
    src = nb["cells"]

    # sanity: the spec must describe every step, in the app's order
    assert [s[0] for s in SPEC] == bridge.ORDER, "SPEC and bridge.ORDER disagree"

    kept_code = 0
    out = opening()
    for i, (sid, header, keeps) in enumerate(SPEC):
        step = bridge.BY_ID[sid]
        out.append(part12(step, i))
        out.append(part3(step))
        for k in keeps:
            cell = src[k]
            if cell["cell_type"] == "code":
                kept_code += 1
            out.append(cell)          # verbatim, original dict
        out.append(part5(step, i))

    # every code cell in the source must survive
    src_code = sum(1 for c in src if c["cell_type"] == "code")
    assert kept_code == src_code, f"lost code cells: kept {kept_code} of {src_code}"

    nb["cells"] = out
    with open(NB, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
        f.write("\n")

    links = len(re.findall(r"stage=[a-z0-9-]+",
                           "".join("".join(c["source"]) for c in out)))
    print(f"rebuilt {NB}")
    print(f"  cells      : {len(src)} -> {len(out)}")
    print(f"  code cells : {kept_code}/{src_code} preserved verbatim")
    print(f"  stage links: {links}")


if __name__ == "__main__":
    main()
