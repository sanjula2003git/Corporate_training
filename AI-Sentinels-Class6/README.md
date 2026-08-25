# The Sentinels of Nova City

**An AI input-and-output assessment for Class 6.** A three-minute narrated comic,
then twelve questions. Roughly 15-20 minutes per student. No internet, no server,
no login, nothing leaves the child's browser.

---

## Running it

**One file (easiest).** Give the student `AI-Sentinels-Assessment.html`. Email it,
put it on a USB stick, drop it on the desktop. Double-click and it runs — the
narration audio and all the artwork are inside that single file (3.7 MB).

**The folder version.** `index.html` next to `scenes.js`, `app.js` and
`narration.mp3`. Double-click `index.html`. Keep the four files together.
This is the one to edit; re-run `python -X utf8 bundle.py` to rebuild the
single file afterwards.

Works in Chrome, Edge, Firefox and Safari, on a laptop or a tablet. Headphones
or a speaker are needed — the story is narrated.

---

## What the student does

1. **Types their name**, class and roll number.
2. **Watches the story.** Three minutes. The questions stay locked until it
   finishes once. After that they can replay it any time, including from inside
   the questions — this is a comprehension test, not a memory test.
3. **Answers twelve questions.** They can move around freely and change answers.
   There is no timer.
4. **Sees their score** with every answer explained, and saves an answer file for
   the teacher.

---

## The story

Four heroes protect Nova City, and each one is plainly an AI: **Captain Echo**
turns sound into words, **Iris** turns a picture into a name, **Nova** turns
numbers into a warning, and **Rex** the robot dog turns a typed question into a
spoken answer. Different powers, same three steps: something goes in, they work
on it, something comes out.

The villain, **the Static**, never fights anybody. He corrupts what the heroes
are *given* — he paints stripes on the dam so Iris reports "zebra", plays a
recording so Echo hears the wrong voice, feeds Nova last summer's numbers. Three
heroes, three wrong answers, and not one of them broken.

A girl called **Meera** works out why: *bad input, bad output*. So the Sentinels
clean their inputs instead of fighting, and the right answers come out.

That last part is the point of the whole assessment. Children meet AI as
something that is either magic or broken; the story gives them a third and truer
idea — that it is a machine whose answer depends on what you hand it.

---

## The twelve questions

| # | Type | What it tests |
|---|------|---------------|
| 1-4 | Sort three cards into **INPUT / OUTPUT / THE MACHINE** | Can they separate the three, hero by hero |
| 5-8 | Multiple choice on the story | Did they follow why the wrong answers happened |
| 9-10 | A school gate camera, **not in the story** | Can they transfer the idea to something new |
| 11 | Odd one out | Can they spot a thing that is *not* an input |
| 12 | Written, two lines | Can they say it in their own words |

**Marks: 19 automatic + 2 from the teacher = 21.** Each sorting card is worth one
mark, so questions 1-4 carry three marks each.

### The misconception this is built to catch

The commonest Class 6 error is answering *"the input is the camera"* — confusing
the machine with the thing you give it. That is why every sorting question has a
third bin, **THE MACHINE**, holding a card that is neither input nor output
(her helmet, Iris's camera eye, Nova herself, the robot dog's body). Question 9
sets the same trap in multiple-choice form, with "The camera" sitting right next
to the correct answer.

A student who scores well on 5-8 but badly on the third card of 1-4 has followed
the story without getting the concept. That is the pattern worth looking for.

### Answer key

| Q | Answer |
|---|--------|
| 1 | shout = INPUT, words on visor = OUTPUT, helmet = THE MACHINE |
| 2 | photo = INPUT, the word CRACK = OUTPUT, camera eye = THE MACHINE |
| 3 | rainfall/river numbers = INPUT, the flood warning = OUTPUT, Nova herself = THE MACHINE |
| 4 | typed question = INPUT, spoken answer = OUTPUT, the dog's body = THE MACHINE |
| 5 | The Static had painted stripes on the wall |
| 6 | The inputs the heroes were given |
| 7 | They gave their machines fresh, correct inputs |
| 8 | An AI's answer can only be as good as what it is given |
| 9 | The picture of the person standing at the gate |
| 10 | The decision to open the gate |
| 11 | The answer that appears on your screen |
| 12 | input = the photo of the medicine strip; output = the spoken name of the medicine |

---

## Collecting the work

On the result screen the student can:

- **Save my answer file** — writes `sentinels-<name>.json` to their Downloads
  folder: name, class, roll, both timestamps, the automatic score, and every
  answer with the correct one beside it. Have them hand these in.
- **Print / Save as PDF** — a clean printable sheet, buttons removed.

Question 12 is printed on both, with the expected answer underneath, ready to
mark. There are two marks in it.

Answers are also kept in the browser's own storage, so a closed tab or a flat
battery does not lose the work — reopening the page brings it back. **The same
browser profile therefore resumes the same student.** Before the next child
starts, press **New student** on the result screen, or use a fresh browser
profile or a private window per student.

---

## Editing it

Everything lives in three plain files. No build step, no framework, no npm.

- **`app.js`** — the questions are the `QUESTIONS` array at the very top. Add a
  sorting question by copying one of the first four and changing `cards`; add a
  multiple-choice by copying one of the middle ones and setting `ans` to the
  index of the right option (0-3). The score totals recalculate themselves.
- **`scenes.js`** — the artwork (drawn as SVG, no image files) and `LINES`, the
  caption track: `[scene, caption, seconds]`.
- **`index.html`** — the styling.

After any edit, rebuild the single-file copy:

```
python -X utf8 bundle.py
```

### Two traps, if you touch the artwork

- **Never put an animation class on an SVG group that also has a `transform`
  attribute.** A CSS transform replaces the attribute, and the art snaps to the
  top-left corner. Position on an outer `<g>`, animate on an inner one.
- **Nothing readable goes below about `y=560`** in the 1280x720 scene. The
  caption band covers the bottom of the stage.

### Re-recording the narration

The voice is ElevenLabs "George", generated through vidIQ, at 178 seconds.
If you replace `narration.mp3`, the caption times in `scenes.js` scale to the new
length automatically, but they were hand-aligned to the pauses in *this*
recording (mean error 0.3 s) and a different reading will drift. For a fresh
recording, re-measure: find the silent gaps in the new file and re-anchor each
line to the pause in front of it.
