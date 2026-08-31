# The Leaf Machine — Class 6 assessment

**Unit 2 — Introduction to Artificial Intelligence.** A three-minute narrated
story, then three rounds: draw, guess, speak. **40 marks, all auto-marked.**

> This file contains the answer key. It is deleted from the published copy by
> the Pages workflow — do not hand it to students.

---

## Running it

Two builds, same assessment:

| | |
|---|---|
| **`index.html`** | the editable version — needs `scenes.js`, `pictures.js`, `app.js` beside it |
| **`Leaf-Machine-Assessment.html`** | one file, ~103 KB, nothing else needed. Email it, put it on a USB stick, open it off the desktop |

Rebuild the single file after editing **any** source file:

```
python -X utf8 bundle.py
```

The `-X utf8` is not optional on Windows — without it every apostrophe and
dash in the story turns to mojibake inside the captions.

### One thing to know before the lesson

**Round 3 needs a microphone, and a microphone needs a real web address.**
Chrome reports a `file://` page as a secure context, so the "Unmute and answer"
button still appears on a desktop copy — but the permission prompt is usually
refused there and the recogniser cannot reach the network. The page detects
this and says so.

Every question has a **typed answer box worth exactly the same 2 marks**, so a
lab with no microphones, no internet, or a `file://` copy loses nothing but the
speaking. If you want the speaking round to actually speak, serve the folder
over http or use the Pages URL. Speech recognition also needs the internet —
Chrome sends the audio to Google to transcribe it.

---

## The story

*Ganga Vidyalaya, four days before the science exhibition.* A crate arrives
holding a second-hand box with one glass eye and a screen made of **sixty-four
dots**. Arjun feeds it fifty photographs of the neem tree by the gate — same
tree, same bench, same four o'clock light. On Tuesday it names the neem
instantly. On Wednesday it calls the judge's tulsi NEEM. And a chair. And a
shoe. And the headmaster's umbrella. Devu, who never speaks, has 240 pictures
of leaves from a whole year — wet, yellow, torn, tiny. They feed it those
overnight. On Friday it names real leaves correctly, then confidently calls a
plastic leaf from a shop PEEPAL. Meher writes four words on a card and sticks
it to the glass: **ASK A PERSON TOO.**

**The narration never teaches.** It never says data, pattern, model, training,
output, prediction, domain, feedback or automation — an automated check in the
test suite enforces this. It is a situation, not a lesson. If the vocabulary
appears before Round 1, the assessment stops measuring understanding and starts
measuring who was paying attention to a definition.

The questions **unlock only after the story has run to the end once**, but
replay is unlimited — there is a "Watch the story again" button inside Round 1.

---

## Round 1 — Draw the dots (4 × 3 = **12**)

The child reproduces what the machine's screen showed by filling squares on an
8 × 8 grid. Drag to fill, drag across filled squares to rub out.

**Every square must match.** Marking:

- exact on the **first** Check — **3**
- exact after more tries — **2**
- exact after asking for the hint (which puts the answer faintly behind the
  grid) — **1**

| Q | Asked | Answer | Why |
|---|---|---|---|
| 1 | What came up when Meher first switched it on | **question mark** | recall |
| 2 | What the dots showed for the judge's **tulsi** | **the neem leaf** | comprehension — it had only ever seen one tree, so it answered neem for everything |
| 3 | What the dots showed for the **plastic** leaf | **the peepal leaf** | comprehension — more data made it better, not perfect; it still answered confidently about something that was never a leaf |
| 4 | What it put up for the curry leaf on Friday | **the tick** | recall |

Q2 and Q3 are the two worth arguing about in class. A child who has understood
the story draws the *wrong* leaf on purpose, because that is what the machine
actually showed.

The answers are **not written in `app.js`**. They are read from `STORY.icons`
in `scenes.js` — the same eight-row strings the machine's screen draws in the
video. One source of truth: change the artwork and the answer changes with it.

---

## Round 2 — The picture word (6 × 2 = **12**)

Each picture gives one letter — the letter its name starts with. Correct = 2;
correct after any hint (a hint names one picture) = 1.

| # | Word | Pictures |
|---|---|---|
| 1 | **MYTH** | Moon, Yak, Tent, Hat |
| 2 | **MODEL** | Moon, Owl, Drum, Egg, Leaf |
| 3 | **INPUT** | Igloo, Nest, Pen, Umbrella, Tap |
| 4 | **OUTPUT** | Owl, Umbrella, Tree, Pen, Umbrella, Tap |
| 5 | **DOMAIN** | Drum, Owl, Moon, Apple, Igloo, Nest |
| 6 | **FEEDBACK** | Fish, Egg, Egg, Drum, Ball, Apple, Cup, Kite |

**None of these six words is an answer in Round 3.** That is deliberate and the
test enforces it — an early draft used DATA, PATTERN and VISION here, which
would have handed over three spoken answers before they were asked for.

---

## Round 3 — Say it out loud (8 × 2 = **16**)

Press the button, allow the microphone, say the answer. Typing scores the same.
Retries are free.

| # | Question | Accepted |
|---|---|---|
| 1 | Information an AI system learns from | **data** |
| 2 | The thing that repeats, which AI looks for | **pattern / patterns** |
| 3 | A smart guess made from data | **prediction / predictions** |
| 4 | The domain for images and videos | **computer vision / vision** |
| 5 | The domain for human language | **natural language processing / NLP** |
| 6 | Fixed thirty-minute wash — AI or automation? | **automation / automatic** |
| 7 | One thing never to share with an unknown app | **password, phone number, home address, OTP, bank, location, school ID, date of birth, personal photos** |
| 8 | AI gives medical advice — trust it, or check? | **check / doctor / verify / ask an adult** |

Matching is a contains-match on the transcript, plus a near-miss allowance for
long single words only. Short words must be exact — otherwise "date" passes for
"data", which the test checks for by name.

---

## Marks

| Round | Marks |
|---|---|
| 1 · Draw the dots | 12 |
| 2 · The picture word | 12 |
| 3 · Say it out loud | 16 |
| **Total** | **40** |

The result page shows every question, the child's 8 × 8 grid beside the correct
one, and what they said or typed. **Download my answers** writes a JSON file to
their own Downloads folder; **Print / Save as PDF** gives a marking sheet.
Nothing is uploaded anywhere.

---

## Two children, one computer

Answers persist in `localStorage`, so **the same browser profile resumes the
same child**. Press **New student** on the result page (or the welcome page)
before the next one starts. A separate browser profile per child is safer in a
shared lab.

Answers are readable in `app.js` by anyone who views source. That is inherent
to a client-side quiz with no backend and is accepted for Class 6.

---

## For whoever edits this next

- **Never put an animation class on an SVG `<g>` that also has a `transform`
  attribute.** The CSS transform replaces the attribute and the artwork snaps
  to the top-left corner. Position on an outer group, animate on an inner one.
- **Nothing readable goes below y ≈ 560** in a scene. The caption band covers it.
- Scene timing is driven by the **real speech events**, not a stopwatch, so the
  captions and the voice cannot drift apart however fast the browser's voice is.
  With the voice off, each scene falls back to its own `dur`.
- The narration currently uses the **browser's built-in voice**. To swap in a
  recorded track, drop `narration.mp3` in and time the scenes against it —
  `bundle.py` has a note on where that would hook in.
- The test suite (`e2e.mjs` in the session scratchpad) drives a whole student
  run with **real mouse input** over CDP — 76 checks, including painting each
  8 × 8 answer by dragging. Synthetic events do not reproduce a drag; that is
  the only way the paint-and-rub-out path gets exercised.
