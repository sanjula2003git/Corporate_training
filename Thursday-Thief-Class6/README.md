# The Thursday Thief

**A Class 6 assessment for AI Unit 1, "What is Intelligence?"** A four-minute
narrated comic, then three rounds of questions. Roughly 20 minutes per student.
No internet, no server, no login, nothing leaves the child's browser.

---

## Running it

**One file (easiest).** Give the student `Thursday-Thief-Assessment.html`. Email
it, put it on a USB stick, drop it on the desktop. Double-click and it runs —
all the artwork is inside that single file (~100 KB).

**The folder version.** `index.html` next to `scenes.js` and `app.js`.
Double-click `index.html`. Keep the files together. This is the one to edit;
re-run `python -X utf8 bundle.py` to rebuild the single file afterwards.

Works in Chrome, Edge, Firefox and Safari, on a laptop or a tablet. **No
headphones are needed** — the story runs as a read-along, with the words
appearing under the picture at reading pace. See *Adding a voice* at the bottom
if you would rather it were spoken aloud.

---

## The story tells a story. It does not teach.

This is the central design decision, and it is worth not undoing.

The narration is pure drama: an empty cupboard, four Thursdays in a row, and a
boy the whole class has already decided about. It never says the words
*observation*, *pattern*, *memory* or *reason*. It never explains anything. It
just shows what happened.

Nobody in it is a villain. Yash is not lying when he says it is Imran — he sits
nearest, he is new, and that is enough for twenty-six people. Tanvi is not
cleverer than the rest; she had thought it was Imran too, on the Tuesday, and
the story says so. What she does differently is small and completely repeatable:
she writes down what actually went missing, notices that all five things were
shiny, checks the dates, remembers a whistle from June, and then sits still in
an empty room for nineteen minutes.

It is a crow. It comes in through a latch that does not shut, on the one day of
the week the room is empty for forty minutes.

At the end, asked in assembly how she worked it out, Tanvi does not say anything
clever:

> *"Everyone was looking at Imran. I was the only one looking at the window."*

That line is the whole idea, and it arrives as a story beat rather than a
lesson. **The teaching happens in the questions**, where each skill is named and
practised. A child who watches the story has seen the concepts six or seven
times without being told any of them once — which is exactly what makes the
questions land.

---

## The three rounds

Unit 1 is a survey — it covers thinking, learning, observation, memory,
decisions, patterns, prediction, comparison, classification, reasoning and
responsibility. The assessment deliberately spreads across the whole unit rather
than drilling one idea.

### Part 1 — Drag & Drop (8 marks)

The same three steps every single time:

```
   THE SITUATION   →   THE THINKING SKILL   →   THE SMART ACTION
```

A worked example is shown first, filled in, on the round's intro screen — the
school bus that arrives at 7:30 every day, straight out of the unit's own
Mini Drill 29. Then four patterns arrive with two boxes empty and four cards to
choose from. The student drags a card into a box — or, on a tablet, taps the
card and then taps the box. Both work everywhere. Tapping a filled box takes the
card back out.

Repeating one unchanging shape is what does the teaching. By the fourth one the
child is completing it from the shape alone. The four are filled from four
different corners of the unit:

| # | The thinking skill | Where it comes from in Unit 1 |
|---|---|---|
| 1 | Finding what things have in common | *Intelligence Uses Comparison* / *Classification* |
| 2 | Spotting the day that keeps repeating | *Recognizing Patterns*, *Patterns Help Us Predict* |
| 3 | Using something learned before | *Memory and Intelligence*, *Learning from Experience* |
| 4 | Thinking about what is safe | *Making Decisions*, *Intelligence and Responsibility* |

### Part 2 — Multiple Choice (6 marks)

Four answers, one best. Three questions are about the story, and three are about
situations that never appear in it, so the second half is transfer rather than
recall.

| # | Tests | Unit 1 source |
|---|---|---|
| 1 | Observation vs guessing | *Observation vs Guessing*, Mini Drill 13 |
| 2 | Prediction vs random guess | *Prediction vs Random Guess*, Mini Drill 21 |
| 3 | Responsible, safe choices | *Intelligence and Responsibility*, Mini Drill 34 |
| 4 | Short-term vs long-term memory | *Short-Term and Long-Term Memory*, Mini Drill 15 |
| 5 | What machines cannot do | *Human Intelligence vs Machine Actions*, Mini Drill 23 |
| 6 | Relevant vs irrelevant information | *Relevant and Irrelevant Information*, Mini Drill 27 |

### Part 3 — Guessing Game (4 marks)

A row of empty letter boxes and one clue. The student types a guess. Wrong
guesses cost nothing and can be repeated. "Another clue" reveals a second and
then a third, each more generous than the last, ending with the letter count and
the first letter.

The four words are **OBSERVATION**, **PATTERN**, **MEMORY** and **REASON** —
four of the words from the unit's own Vocabulary Recap board, chosen from four
different parts of it. Each word's second clue is really a comprehension
question about the story wearing a disguise.

**Total: 18 marks**, all automatically marked.

### The misconception this is built to catch

The commonest Class 6 error in this unit is treating a **guess as an
observation** — answering from what you already believe rather than from what
anybody actually noticed. It is the error the whole class makes about Imran.

Every drag round puts two decoys in the tray, and one of them is always that
error in card form: *"Imran was new, so it was probably him"*, *"she hoped she
would be lucky"*, *"she felt sure about it without checking anything"*, *"she
climbed the wall quickly before anyone could see"*. The second decoy is always a
thing rather than a thinking skill — a clock, a ladder, a water tank — which is
the unit's other standing trap (*a thing can be useful without being
intelligent*, Mini Drill 11 and Mini Drill 24). MCQ questions 1 and 2 set the
same trap in prose.

**A student who does well on the story questions but drops the decoy cards into
the boxes has followed the plot without getting the idea.** That is the pattern
to look for.

### Answer key

**Part 1** — in every pattern: what was true at the time goes in THE SITUATION,
and what she did about it goes in THE SMART ACTION. The two leftover cards are
always a guess made without checking, and an object that does not think.

1. *every missing thing was small and shiny* → *she stopped looking at people
   and looked at the window*
2. *all four of them happened on a Thursday* → *she asked to stay back in the
   room next Thursday*
3. (skill) *using something she had learned before* → *she looked upward, at the
   ledge under the water tank*
4. *the ledge was high up with nothing safe to hold on to* → *she got down off
   the chair and went to find Miss Rao*

**Part 2** — 1: B. 2: C. 3: B. 4: B. 5: C. 6: B.

**Part 3** — OBSERVATION, PATTERN, MEMORY, REASON.

---

## Collecting the work

On the result screen the student can:

- **Save my answer file** — writes `thursday-thief-<name>.json` to their
  Downloads folder: name, class, roll, both timestamps, the score broken down by
  round, and every answer with the correct one beside it. For the guessing game
  it also records how many clues were used and what wrong words were tried,
  which is often more interesting than the mark.
- **Print / Save as PDF** — a clean printable sheet, buttons removed.

Answers are also kept in the browser's own storage, so a closed tab or a flat
battery does not lose the work. **The same browser profile therefore resumes the
same student.** Before the next child starts, press **New student** on the
result screen, or use a fresh browser profile or a private window per student.

---

## Editing it

Everything lives in three plain files. No build step, no framework, no npm.

- **`app.js`** — the `QUESTIONS` array at the top holds all three rounds, each
  entry tagged `part: 'drag' | 'mcq' | 'guess'`. Copy an existing entry to add
  one; the totals recalculate themselves.
  - a **drag** entry needs `slots` (three, each either `fixed` text or an
    `answer` id) and a `tray` of cards, two of which should be decoys.
  - a **guess** entry needs `answer`, an `accept` list of spellings to allow,
    and three clues that get progressively kinder.
- **`scenes.js`** — the artwork (SVG drawn in code, no image files) and `LINES`,
  the caption track: `[scene, caption, seconds]`.
- **`index.html`** — the styling.

After any edit, rebuild the single-file copy:

```
python -X utf8 bundle.py
```

### How the picture stays alive

The story is nineteen still drawings, and three things stop it looking like
nineteen still drawings.

**The camera cuts.** Nineteen drawings held for eight to nineteen seconds each
is a slideshow, however prettily the camera drifts across them. `SHOTS` in
`scenes.js` gives one framing per caption line — `z` is how far in, `(x, y)` is
what sits in the middle of the frame — so the same nineteen drawings become
**51 shots**: the wide classroom, then the empty shelf where the compass was,
then the bent latch, then the crow's eye filling the screen. Between one line
and the next the camera cuts; inside a line it drifts.

`cameraCSS()` generates one `@keyframes` per scene from that list, and `frame()`
clamps every framing so the edge of the drawing can never walk into shot. The
move runs on the `<svg>` element itself, never on a group inside the art, so it
can never collide with a `transform` attribute. `--hold` is the length of the
move and `--tin` is how far into the scene the story already is, both written by
`app.js`; `--tin` is what makes dragging the bar land in the middle of a move
instead of restarting it.

**The children act.** Arms hinge at the shoulder, heads turn on the neck, eyes
blink out of step with each other, and a mouth drawn open is a mouth in the
middle of saying something rather than one hanging open for nineteen seconds.
The pivot for each part is a corner of its own bounding box — an arm that hangs
down has its shoulder at the TOP of its box, one that is raised or pointing has
it at the BOTTOM — and getting that backwards makes an arm swing from the hand.
Plaits are deliberately left outside the turning head group, because their
bounding box would drag the pivot down to the hair tips.

**Reveals are hung on sentences, not on a stopwatch.** A `.pop` element carries
a beat class: `b0` is the second the scene opens, `b1` the next caption line of
that scene, `b2` the one after, and `b1x1`–`b1x4` are four steps in between, for
staggering a group of things across one long line. The real delays are
generated from `LINES` by `beatCSS()`, so retiming the story retimes the artwork
with it. This is why the five stolen things arrive one at a time as she names
them, and why the crow does not appear until the sentence that lets it in.
`d1`–`d5` still exist for quick decorative staggers that belong to no line.

**Everything holds still when the story is paused.** Idle loops are gated on
`.scene.live`, so eighteen off-screen scenes animate nothing, and the stage
loses its `playing` class on pause, which freezes the camera and everything
drawn inside it. Art that keeps drifting under a frozen caption looks broken.

Captions arrive a word at a time (`setCaption` in `app.js`), which is the
difference between a line being spoken and a line being pasted up. The DOM
still reads back as one plain sentence, which is what the tests check.
`prefers-reduced-motion` turns all of it off.

### Traps, if you touch the artwork

- **Never put an animation class on an SVG group that also has a `transform`
  attribute.** A CSS transform replaces the attribute and the art snaps to the
  top-left corner. Position on an outer `<g>`, animate on an inner one. Every
  speech bubble in this file was invisible until that was fixed — and the
  screenshot test walked into the same trap from the other side, by putting
  `transform:none` on `.scene *` to freeze a frame.
- **Nothing readable goes below about `y=560`** in the 1280x720 scene. The
  caption band covers the bottom of the stage.
- **A label has to be inside the shot it was written for.** Once the camera
  cuts to a close-up, most of the drawing is off screen — that is the point —
  but a caption label stranded outside its own shot is simply never seen, and
  nothing about watching the story tells you it is missing. `tests/story.mjs`
  drives every scene to both ends of every one of its shots and measures the
  text belonging to that shot against the edge of the stage. It caught six
  labels the first time it ran.
- **A regex inside a JS template literal needs its backslashes doubled.**
  `/^b\d+$/` written inside a `` ` `` string arrives in the browser as
  `/^bd+$/`, matches nothing, and reports no error — which is how the shot
  sheet quietly kept showing every label at once.
- **Keep teaching words out of the scenes.** The pictures say "MISSING" and
  "ALL FOUR. SAME DAY.", never "observation" or "pattern". If the vocabulary
  appears before Part 1, the assessment stops measuring anything.

### Adding a voice

The story is written to be spoken — the caption times in `scenes.js` are a
reading of about 228 seconds. Drop a `narration.mp3` next to `index.html` and it
takes over automatically: `app.js` checks whether the audio is actually
readable, uses it if it is, and falls back to its own clock if it is not. The
caption times scale to the real length of the recording, so a voiceover of a
slightly different length still lines up roughly.

For a tight fit, re-measure rather than relying on the scaling: decode the mp3
in a browser, find the silent gaps, and re-fit each caption boundary to the
pause in front of it. Then re-run `bundle.py`, which folds the mp3 into the
single file as base64.
