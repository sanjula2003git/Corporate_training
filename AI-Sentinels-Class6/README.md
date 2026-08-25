# The Sentinels of Nova City

**An AI input-and-output assessment for Class 6.** A three-minute narrated comic,
then three rounds of questions. Roughly 20 minutes per student. No internet, no
server, no login, nothing leaves the child's browser.

---

## Running it

**One file (easiest).** Give the student `AI-Sentinels-Assessment.html`. Email it,
put it on a USB stick, drop it on the desktop. Double-click and it runs — the
narration audio and all the artwork are inside that single file (~4 MB).

**The folder version.** `index.html` next to `scenes.js`, `app.js` and
`narration.mp3`. Double-click `index.html`. Keep the four files together.
This is the one to edit; re-run `python -X utf8 bundle.py` to rebuild the
single file afterwards.

Works in Chrome, Edge, Firefox and Safari, on a laptop or a tablet. Headphones
or a speaker are needed — the story is narrated.

---

## The story tells a story. It does not teach.

This is the central design decision, and it is worth not undoing.

The narration is pure drama: eleven minutes to midnight, nine days of rain, a dam
above the town, and four heroes who all give the wrong answer on the same night.
It never says the words *input*, *output* or *machine*. It never explains
anything. It just shows what happened.

The villain, **the Static**, never throws a punch. It spends nine days painting
stripes on the dam wall, recording the mayor's voice, and swapping one page of
numbers for another. So Iris looks at the wall and says "zebra". Echo listens and
writes that there is nothing to worry about. Nova reads her page and says "safe".
Rex says there is no danger.

Meera, who is eleven and has no cape, is the one who sees the wet paint. At the
end the reporters ask her how four superheroes could all be wrong at once, and
she says: *"They weren't wrong. They were told wrong."*

That line is the whole idea, and it arrives as a story beat rather than a lesson.
**The teaching happens in the questions**, where the pattern is named and
practised. A child who watches the story has seen the concept four times without
being told it once — which is exactly what makes the questions land.

---

## The three rounds

### Part 1 — Drag & Drop (8 marks)

The same pattern every single time:

```
   WHAT GOES IN    →    THE MACHINE    →    WHAT COMES OUT
```

A worked example is shown first, filled in, on the round's intro screen. Then four
patterns arrive with two boxes empty and four cards to choose from. The student
drags a card into a box — or, on a tablet, taps the card and then taps the box.
Both work everywhere. Tapping a filled box takes the card back out.

Repeating one unchanging pattern is what does the teaching. By the fourth one the
child is completing it from the shape alone.

### Part 2 — Multiple Choice (6 marks)

Four answers, one best. Three questions are about the story, and three are about
machines that never appeared in it — a school gate camera, a chatbot, a smart
speaker — so it is transfer, not recall.

### Part 3 — Guessing Game (4 marks)

A row of empty letter boxes and one clue. The student types a guess. Wrong guesses
cost nothing and can be repeated. "Another clue" reveals a second and then a third,
each more generous than the last, ending with the letter count and first letter.

The four words are **INPUT**, **OUTPUT**, **MACHINE** and **STATIC**. The first
three are the vocabulary; the fourth is there because it is fun, and because the
clue for it ("I spent nine days painting a wall") is really a comprehension
question wearing a disguise.

**Total: 18 marks**, all automatically marked.

### The misconception this is built to catch

The commonest Class 6 error is answering *"the input is the camera"* — confusing
the machine with the thing you hand it. Every drag round puts a machine-part card
in the tray as a decoy (Iris's camera eye, Echo's helmet, Rex's antenna tail), and
MCQ question 4 sets the same trap with "The camera" sitting right beside the
correct answer. Part 3's clue for MACHINE names it outright.

A student who does well on the story questions but drops the decoy cards into
INPUT has followed the plot without getting the idea. That is the pattern to look
for.

### Answer key

**Part 1** — in every pattern: the thing handed over goes in WHAT GOES IN, the
hero or device is THE MACHINE, the word or decision they produce is WHAT COMES
OUT. The leftover cards are always either a part of the machine or scenery.

**Part 2** — 1: the wall had stripes painted on it. 2: the things the heroes were
given to work from. 3: they were given the wrong things to work from. 4: the
picture of the person at the gate. 5: the decision to open the gate. 6: the answer
that appears on your screen.

**Part 3** — INPUT, OUTPUT, MACHINE, STATIC.

---

## Collecting the work

On the result screen the student can:

- **Save my answer file** — writes `sentinels-<name>.json` to their Downloads
  folder: name, class, roll, both timestamps, the score broken down by round, and
  every answer with the correct one beside it. For the guessing game it also
  records how many clues were used and what wrong words were tried, which is often
  more interesting than the mark.
- **Print / Save as PDF** — a clean printable sheet, buttons removed.

Answers are also kept in the browser's own storage, so a closed tab or a flat
battery does not lose the work. **The same browser profile therefore resumes the
same student.** Before the next child starts, press **New student** on the result
screen, or use a fresh browser profile or a private window per student.

---

## Editing it

Everything lives in three plain files. No build step, no framework, no npm.

- **`app.js`** — the `QUESTIONS` array at the top holds all three rounds, each
  entry tagged `part: 'drag' | 'mcq' | 'guess'`. Copy an existing entry to add
  one; the totals recalculate themselves.
  - a **drag** entry needs `slots` (three, each either `fixed` text or an
    `answer` id) and a `tray` of cards, at least one of which should be a decoy.
  - a **guess** entry needs `answer`, an `accept` list of spellings to allow, and
    three clues that get progressively kinder.
- **`scenes.js`** — the artwork (SVG drawn in code, no image files) and `LINES`,
  the caption track: `[scene, caption, seconds]`.
- **`index.html`** — the styling.

After any edit, rebuild the single-file copy:

```
python -X utf8 bundle.py
```

### Three traps, if you touch the artwork

- **Never put an animation class on an SVG group that also has a `transform`
  attribute.** A CSS transform replaces the attribute and the art snaps to the
  top-left corner. Position on an outer `<g>`, animate on an inner one.
- **Nothing readable goes below about `y=560`** in the 1280x720 scene. The
  caption band covers the bottom of the stage.
- **Keep teaching words out of the scenes.** The pictures say "SHE HEARS" and
  "SHE WRITES", never "INPUT" and "OUTPUT". If those words appear before Part 1,
  the assessment stops measuring anything.

### Re-recording the narration

The voice is ElevenLabs "George", generated through vidIQ, at 190 seconds. If you
replace `narration.mp3`, the caption times in `scenes.js` scale to the new length
automatically, but they were aligned against the pauses in *this* recording (mean
error 0.24 s) and a different reading will drift. For a fresh recording, re-measure:
decode the mp3 in a browser, find the silent gaps, and re-fit the caption
boundaries to them.
