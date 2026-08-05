# Spin Reveal · 3 parts

## Assessment v2

The current build adds a student setup screen, seeded question and dataset
randomization, one task per round, limited timed reveals, round countdowns, a
code-answer area, mandatory microphone explanations, focus-change logging, and
an offline submission export. The original implementation remains embedded as
non-executing reference source inside `index.html`; `assessment-v2.js` now runs
the assessment and `assessment-v2.css` supplies the upgraded interface.

Submission export downloads one JSON manifest plus one WebM audio file per
answered question. All recording and export work locally in the browser; no
student data is uploaded.

### Fixed assessment policy

The setup now asks only for student name and email. Difficulty is fixed to the
hardest mode and all students receive all 12 questions. Question parts cannot
be clicked: hold `Ctrl+A`, `Ctrl+D`, or `Ctrl+Q` to make exactly one part
readable, then release to return it to the difficult spin. The code editor is
larger. A detected Print Screen or Windows screenshot shortcut activates a
two-minute local lock; refreshing during an active lock extends it to two and a
half minutes. Browser pages cannot detect every operating-system or external
screenshot method, so this is a best-effort integrity control rather than
absolute screenshot prevention.

Every active assessment is also covered by a repeated forensic watermark with
the student's name, email, and a changing timestamp. This remains visible in
screenshots even when the operating system does not report the screenshot key
to the browser. The enlarged editor is 520 px high, and the next question is
unlocked after both code and audio exist; students can then click **Next
question** or press `Ctrl+Enter`.

Question parts now use a cinematic 3D deck: cards enter from deep perspective,
carry visible edge thickness and moving light, float on the Z-axis while
rotating, and move forward with a glass-like illuminated face while their
keyboard combination is held. The one-readable-part rule is unchanged.

One PPT slide, the question divided into **three parts** stacked down it, every part
turning until a student catches one with a key.

```
 ┌─ PPT slide ─────────────────────────────┐
 │  ┌───────────────────────────────────┐  │
 │  │  Part 1                        →  │  │
 │  └───────────────────────────────────┘  │
 │  ┌───────────────────────────────────┐  │
 │  │  Part 2                        ←  │  │
 │  └───────────────────────────────────┘  │
 │  ┌───────────────────────────────────┐  │
 │  │  Part 3                        →  │  │
 │  └───────────────────────────────────┘  │
 └─────────────────────────────────────────┘
        Ctrl+A      Ctrl+D      Ctrl+Q
```

Nothing in `qp-reveal-puzzle/` is touched — this is its own folder, one file, no build.

## Run it

Double-click `index.html`, or serve the folder and open it (`python -m http.server 5180`).

## Where the questions come from

**A normal PowerPoint.** Press **Open PPT…** or drop a `.pptx` anywhere on the page:
one slide = one question, and the slide's text boxes become the three bands.

* A slide authored with **exactly three text boxes** maps straight across — box 1 is
  part 1, box 2 is part 2, box 3 is part 3.
* Any other number of boxes is packed into three groups in reading order, so an
  ordinary slide still works without being re-authored.
* Prev / Next walk the deck.

A `.pptx` is a zip, and the browser inflates it natively, so the file is read in the
page — no build step, no library, nothing uploaded anywhere.

With no PPT open it falls back to the paper in `pandas aug 30.docx`: part 1 = Students
DataFrame, part 2 = Attendance DataFrame, part 3 = *"Write the code for the following:"*
+ task N, with Prev/Next over all twelve tasks. Question 1 is the reference cut.

## The mechanic

* Each band turns **horizontally** — about its own vertical axis — so it sweeps through
  the 180° mirror and back without ever swinging off the slide the way an in-plane spin
  would.
* Neighbouring bands turn **opposite ways**: part 1 →, part 2 ←, part 3 → at 30 / 38 /
  46 °per second, started 130° apart so they never travel together.
* A band sharpens as it comes face-on and dissolves as it turns away, so timing the key
  is fair rather than luck.
* **A key stops its band dead where it stands.** It does not turn back to face you — a
  band caught at the mirror stays mirrored until the key is pressed again. That is the
  whole puzzle.
* The dock buttons do the same job as the keys (and are the fallback on macOS, where the
  OS eats `Cmd+Q`, and on Linux Chrome, which binds `Ctrl+Q` to quit).
* `Ctrl+F` toggles fullscreen. `Ctrl+A` / `Ctrl+D` are `preventDefault`ed, so they no
  longer select-all or bookmark.

## Look

Same PowerPoint dress as the exam viewer: 1280×720 slide scaled to the window, `#A3CD86`
dotted ground, Calibri bold-italic black text, and the deck's letter cipher
**☆=A ◉=I ◇=T**. Each band sets its own type size down until it fits its lane, so a text
heavy PPT slide still lands on one screen. The PPT's `⚀=1` swap is deliberately left out —
the two DataFrames are mostly numbers, and a ciphered `⚀80` stops being data.

## Verified

Driven over CDP in a real browser: each key freezes only its own band (the other two keep
turning), the frozen angle is whatever it was mid-turn (never snapped back to face-on),
pressing again releases it, the three bands measured at +30 / −38 / +46 °/s, and a `.pptx`
handed to the page came back as 2 slides — the three-box slide mapped one-to-one, the
four-box slide packed into three.
