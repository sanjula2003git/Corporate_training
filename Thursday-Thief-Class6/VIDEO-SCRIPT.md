# The Thursday Thief — video generation script

A shot-by-shot script for generating the story film. **Every timing here comes
straight out of `scenes.js`** — the player's caption track is built from the
same numbers, so if the finished video matches these in and out points, the
captions line up with no re-timing.

Total runtime: **228 seconds (3:48)**, 19 scenes, 29 shots.

---

## 0. What to send back

| | |
|---|---|
| **Format** | MP4, H.264 |
| **Size** | 1280 x 720 (16:9). Bigger is fine as long as it is 16:9 |
| **Length** | as close to 228 s as it lands — it does not have to be exact |
| **Audio** | narration voice baked in is ideal. Music or room tone optional, kept low |
| **On-screen text** | **none.** No captions, no titles, no signs, no letters anywhere in frame |
| **Drop it at** | `Thursday-Thief-Class6/story.mp4` |

Three things that matter more than they look:

1. **No burned-in text.** The page draws its own caption band over the bottom of
   the picture. Any text the generator paints in will collide with it, and AI
   video renders lettering as garbage anyway.
2. **Nothing important in the bottom sixth of the frame.** That strip is covered
   by the caption band. Keep faces, hands and the crow above it.
3. **No teaching vocabulary anywhere** — not spoken, not implied. The words
   *observation*, *pattern*, *evidence*, *memory*, *reasoning*, *intelligence*
   must not appear. The whole assessment depends on students meeting those words
   for the first time **after** the story, in the questions. This is the one rule
   that, if broken, makes the quiz measure nothing.

If the total comes out longer or shorter than 228 s, that is fine — tell me the
real duration and I will scale the caption track to it. The player already has
the hook for that (`STORY.track(duration)`).

---

## 1. Style block — paste at the top of every shot prompt

> 2D hand-drawn comic-book animation. Thick near-black ink outlines, flat warm
> poster colours, chunky simplified shapes, light paper grain. An Indian
> government-style primary school. Limited, gentle animation — small bobs,
> blinks, cloth sway — locked-off camera or one slow push, never handheld. Warm
> afternoon light. No text, no letters, no numbers, no signage anywhere in the
> frame. 16:9.

Illustrated style is not a preference here. Photoreal video of children is both
harder to get generated and wrong for a Class 6 comic. Keep it drawn.

---

## 2. Characters — repeat verbatim in every prompt they appear in

| Who | Description |
|---|---|
| **TANVI** | girl, 11, mid-brown skin, black hair in one long plait, white shirt, navy skirt, red school tie. Quiet, watchful, steady eyes |
| **IMRAN** | boy, 11, deeper brown skin, short black hair, white shirt, navy shorts, red tie. New to the school, chin slightly down, says nothing |
| **YASH** | boy, 11, light tan skin, short dark brown hair, white shirt, navy shorts, red tie. Loud, certain of himself |
| **KID1 / KID2** | two background classmates, same uniform — one girl with a plait, one boy |
| **MISS RAO** | woman, 40s, magenta-pink kurta, dark plum dupatta, black hair tied back. Calm, unhurried |
| **RAMESH** | man, 50s, the school gardener, green shirt, olive trousers, grey-flecked hair |
| **THURSDAY** | a glossy black house crow, grey collar, one bright yellow eye, head cocked to one side. Never sinister — busy, and pleased with itself |

**Room 6B:** mustard-cream wall, dark green blackboard with a wooden chalk
ledge, brown plank floor, wooden two-seater desks, a brown door with a brass
knob, a tall steel-grey cupboard, and a window with a wide sill and a latch that
is visibly bent outward.

---

## 3. Shot list

Each shot gives its in and out point, its length, and the narration spoken over
it. If your generator caps clips at 8 seconds, split at the sentence break — the
`/` in the narration marks where.

---

### Scene 1 — ROOM

**S01 · 0:00.0 → 0:09.1 · 9.1 s**

> *VO:* "Room 6B, Nandini Public School, twenty minutes past eleven on a
> Thursday. / Miss Rao opened the cupboard, and stopped."

Wide establishing shot of Room 6B. Dark green blackboard on the left, a round
wall clock high on the right with its hands at eleven-twenty, a brown door with
a brass knob. Two children in white-and-navy uniform sit at wooden desks in the
foreground, heads bobbing very slightly. Late-morning light across the floor.
Very slow push in toward the room. Empty, ordinary, calm.

---

### Scene 2 — CUPBOARD

**S02a · 0:09.1 → 0:16.4 · 7.3 s**

> *VO:* "The steel compass was gone. / So was the silver whistle, and the little
> round mirror from the science box."

Close on a tall steel-grey cupboard, both doors standing open, lit dimmer than
the rest of the room. Three shelves. A red tin box and a green box sit on the
top shelf, a blue box below — and between them two clean rectangles of dust
where something used to stand. Camera drifts slowly across the empty dust
outlines. Nobody in frame.

**S02b · 0:16.4 → 0:19.6 · 3.2 s**

> *VO:* "That made four Thursdays in a row."

Hold on the same open cupboard, pulling back a little. MISS RAO's hand rests on
the open door at the edge of frame. Stillness.

---

### Scene 3 — ACCUSE

**S03a · 0:19.6 → 0:29.0 · 9.4 s**

> *VO:* "Yash did not wait for Miss Rao to ask. / 'It is Imran,' he said. 'He
> sits nearest the cupboard. He only joined in July.'"

YASH stands at his desk in the middle of the room, arm thrown out, pointing hard
toward the back of the classroom, mouth open mid-sentence. KID1 and KID2 at
desks beside him, faces flat. Deep in the background, small, IMRAN sits alone at
the back desk with his chin down. Camera low, favouring Yash.

**S03b · 0:29.0 → 0:32.6 · 3.6 s**

> *VO:* "Twenty-six heads turned to the back of the room."

A fast whip of attention — a room of children all turning their heads together
toward the back of the class in one movement. Shot from behind Imran's shoulder,
so we see the whole room facing us. He does not turn.

---

### Scene 4 — IMRAN

**S04 · 0:32.6 → 0:41.0 · 8.4 s**

> *VO:* "Imran did not say anything. / He was new, and he had already learned
> that saying anything only made it longer."

IMRAN alone at the back desk, close, filling the right of frame, dim light. His
eyes are down on the desk. The rest of the class is small, blurred and turned
away at the far end of the room. He breathes. He does not speak. Hold long
enough that it becomes uncomfortable.

---

### Scene 5 — LUNCH

**S05a · 0:41.0 → 0:49.2 · 8.2 s**

> *VO:* "At lunch he sat by himself, the way he had all week. / Three tables
> away, Tanvi felt something go cold."

Warm-lit school lunch hall, two long wooden tables. IMRAN sits at the far end of
the right-hand table alone with a steel tiffin box, head down. Far away on the
left table, TANVI sits with KID2; KID2 is chatting, TANVI is not — she is
looking across at Imran, her face falling. Wide, both tables in frame, the gap
between them very visible.

**S05b · 0:49.2 → 0:54.6 · 5.4 s**

> *VO:* "Because she had thought it was him too. On Tuesday. Without checking."

Push in slowly on TANVI's face. She stops eating. Shame arriving.

---

### Scene 6 — LIST

**S06a · 0:54.6 → 1:04.6 · 10.0 s**

> *VO:* "That evening she wrote down everything that had gone missing. / A
> compass. A whistle. A key ring. A mirror. Miss Rao's steel pen."

Overhead shot of an open ruled notebook on a desk in lamplight, a pencil beside
it. Instead of writing, small drawn objects appear on the page one at a time,
left to right — a steel compass, a silver whistle, a key ring, a round mirror, a
steel pen — each landing with a tiny pop and a glint. **No words on the page, no
letters, no handwriting** — only the five objects.

**S06b · 1:04.6 → 1:13.4 · 8.8 s**

> *VO:* "Not one storybook. Not one pencil. Not one rupee from anybody's bag. /
> Every single thing on that list was shiny."

Same overhead page. A storybook, a pencil and a coin fade in below the row and
then dissolve away, leaving only the five metal objects. The five catch the
lamplight one after another — glint, glint, glint. Slow push in on the shine.

---

### Scene 7 — WINDOW

**S07a · 1:13.4 → 1:22.8 · 9.4 s**

> *VO:* "The next morning she came in early and stood at the cupboard. / The
> window beside it did not shut properly. The latch was bent outward."

Early morning, empty classroom, warm low light. TANVI stands small at the right
of frame looking at a tall window beside the steel cupboard. Camera moves in on
the window's metal latch — clearly bent outward, not closing. The frame stirs
slightly in the breeze.

**S07b · 1:22.8 → 1:27.8 · 5.0 s**

> *VO:* "And on the sill, stuck in the paint, there was one black feather."

Very close on the wide window sill. A single glossy black feather stuck upright
in a bead of dried paint. Shallow, still, quiet. Everything else out of focus.

---

### Scene 8 — CALENDAR

**S08 · 1:27.8 → 1:37.3 · 9.5 s**

> *VO:* "She checked the dates. All four of them were Thursdays. / Thursday was
> games. The room stood empty for forty minutes."

A paper wall calendar in dim light — a plain grid of squares, **no words, no
numbers, no letters**, just an empty grid. Four red circles are drawn onto it
one at a time, and every one of them lands in the same vertical column. Then cut
wide to the classroom, completely empty, desks abandoned, sunlight moving across
the floor.

---

### Scene 9 — MEMORY

**S09a · 1:37.3 → 1:47.0 · 9.7 s**

> *VO:* "And then she remembered something from June. / A whistle had gone
> missing that month too, and turned up a week later on the roof."

A faded, over-warm remembered image, colours washed toward sepia and gold: the
flat concrete roof of the school under a high June sun, a low parapet wall. A
single silver whistle lies on the concrete, catching the light. Slight dreamy
drift to the camera, edges soft.

**S09b · 1:47.0 → 1:50.7 · 3.7 s**

> *VO:* "Nobody had ever asked how it got up there."

Hold on the whistle on the empty roof. Pull back to show how high it is and that
there is no way up. Fade the sepia out.

---

### Scene 10 — ASK

**S10 · 1:50.7 → 2:00.7 · 10.0 s**

> *VO:* "On Thursday morning, Tanvi asked Miss Rao if she could miss games. Just
> once. / Miss Rao looked at her for a moment, and said yes."

Warm classroom. MISS RAO sits behind her wooden table on the right. TANVI stands
facing her on the left, one hand half raised, asking. Miss Rao looks at her for
a long beat — reading her — then nods once. No fuss. Tanvi's shoulders drop with
relief.

---

### Scene 11 — WAIT

**S11 · 2:00.7 → 2:08.8 · 8.1 s**

> *VO:* "So Tanvi sat alone in an empty classroom with her hands in her lap, /
> and did not move for nineteen minutes."

Wide, dim, absolutely still. Five empty desks. TANVI sits alone at one of them,
hands folded in her lap, back straight, not fidgeting. The wall clock's second
hand is the only thing moving in the frame. Hold the shot without a single cut.

---

### Scene 12 — CROW

**S12a · 2:08.8 → 2:18.1 · 9.3 s**

> *VO:* "At twenty past eleven, the bent latch swung open. / Something black
> came in off the water tank and hopped along the sill,"

The bent latch swings loose and the window opens by itself. THURSDAY the crow
drops onto the wide sill from outside and hops along it, once, twice, three
times. Dim room, bright rectangle of daylight behind the bird, so it reads
almost as a silhouette. TANVI's small still shape watches from the far left,
mouth open.

**S12b · 2:18.1 → 2:23.8 · 5.7 s**

> *VO:* "put its head on one side, and looked at the room with a bright yellow
> eye."

Close on the crow. It stops. It tilts its head over to one side and looks
directly down the lens with one bright yellow eye. Hold. This is the shot the
whole film turns on — give it room.

---

### Scene 13 — STEAL

**S13 · 2:23.8 → 2:31.4 · 7.6 s**

> *VO:* "It took the silver foil off somebody's leftover chocolate, / and went
> straight back out of the window."

A crumpled square of silver foil sits on a desk, catching the light. The crow
drops down, snatches the foil in its beak, and flies straight back out through
the open window in one unbroken movement — camera panning with it, up and out
into the daylight. Quick, confident, businesslike.

---

### Scene 14 — LEDGE

**S14a · 2:31.4 → 2:39.1 · 7.7 s**

> *VO:* "Tanvi stood on her chair to see where it went. / Three metres up, on
> the ledge under the water tank."

TANVI standing on her chair at the window, on tiptoe, craning up. Cut to what
she sees: the outside school wall against a pale blue sky, a narrow ledge
running across it, and a blue water tank on stilts above the ledge. On the
ledge, a rough nest of wire and string with something glinting in it. The crow
stands beside the nest.

**S14b · 2:39.1 → 2:48.4 · 9.3 s**

> *VO:* "The wall below it was wet and green, with nothing to hold on to. / She
> got down off the chair and went to find Miss Rao."

Tilt down the wall from the ledge: the plaster below is damp and streaked green
with algae, blank — no pipe, no foothold, nothing to climb. Cut back inside:
TANVI steps down off the chair and walks straight out of the door. She does not
try to climb.

---

### Scene 15 — LADDER

**S15a · 2:48.4 → 2:58.1 · 9.7 s**

> *VO:* "Ramesh the gardener brought the long ladder. / On the ledge, in a nest
> of wire and string, they found the compass, the whistle,"

Outside, bright day. A long wooden ladder leans against the school wall up to
the ledge. RAMESH the gardener is near the top, one arm reaching over onto the
ledge. Below, TANVI and MISS RAO stand looking up, faces open. Camera cranes up
the ladder to the nest.

**S15b · 2:58.1 → 3:07.5 · 9.4 s**

> *VO:* "two keys, a round mirror, and one steel pen with Miss Rao's name on it.
> / And about forty pieces of silver foil."

Close on the nest: a woven mess of wire and string, and inside it a steel
compass, a silver whistle, two keys, a round mirror, a steel pen — and heaped
all around them a great glittering pile of crumpled silver foil, dozens of
pieces, catching the sun. Slow reveal widening across the hoard.

---

### Scene 16 — SORRY

**S16a · 3:07.5 → 3:17.8 · 10.3 s**

> *VO:* "Before assembly on Monday, Tanvi found Imran at the water cooler. / 'I
> thought it was you as well,' she said. 'On Tuesday. I am sorry.'"

A steel water cooler in a warm-lit corridor. IMRAN is filling his bottle. TANVI
comes up and stops a little way off, awkward, then speaks. She does not make a
speech — a short sentence, eyes up. He looks at her.

**S16b · 3:17.8 → 3:22.4 · 4.6 s**

> *VO:* "Imran shrugged, and moved over so she could fill her bottle."

IMRAN shrugs once, and shifts sideways to make room at the cooler. That is the
whole forgiveness. She steps in beside him. Small, undramatic, warm.

---

### Scene 17 — ASSEMBLY

**S17 · 3:22.4 → 3:31.2 · 8.8 s**

> *VO:* "In assembly, Miss Rao asked her how she had worked it out. / Tanvi
> stood up. She did not say anything clever."

Morning assembly in an open courtyard under a pale sky. Six children sit
cross-legged in rows. MISS RAO stands to one side, speaking. TANVI stands up
among the seated rows — everyone else down, her alone up. Nervous, plain, not
showing off.

---

### Scene 18 — FINALE

**S18 · 3:31.2 → 3:38.4 · 7.2 s**

> *VO:* "'Everyone was looking at Imran. / I was the only one looking at the
> window.'"

A split screen, held on a dark background. **Left:** the classroom, every child
turned and staring at one boy at the back. **Right:** the same room from another
angle, TANVI alone, turned the other way, looking at the window with the bent
latch and the black feather on the sill. Both halves still. Let the two ways of
looking sit side by side without commentary.

---

### Scene 19 — CROWEND

**S19 · 3:38.4 → 3:48.0 · 9.6 s**

> *VO:* "The crow still comes. 6B leave the foil out for it now, on the sill. /
> They named it Thursday."

Warm afternoon. The same window, latch still bent, standing open on purpose.
Three squares of silver foil are laid out neatly on the sill — placed, not
dropped. THURSDAY the crow lands, tilts its head, and takes one. Sunlight. Slow
pull back from the window as the film ends. No people in frame.

---

## 4. Narration, continuous

For a text-to-speech pass or a voice artist. Read at an unhurried pace with a
real pause at each blank line — that pacing is what produces the 228 seconds.
Warm, plain, storyteller-to-a-class. Not dramatic. The crow scenes need less
performance, not more.

```
Room 6B, Nandini Public School, twenty minutes past eleven on a Thursday.
Miss Rao opened the cupboard, and stopped.

The steel compass was gone.
So was the silver whistle, and the little round mirror from the science box.
That made four Thursdays in a row.

Yash did not wait for Miss Rao to ask.
"It is Imran," he said. "He sits nearest the cupboard. He only joined in July."
Twenty-six heads turned to the back of the room.

Imran did not say anything.
He was new, and he had already learned that saying anything only made it longer.

At lunch he sat by himself, the way he had all week.
Three tables away, Tanvi felt something go cold.
Because she had thought it was him too. On Tuesday. Without checking.

That evening she wrote down everything that had gone missing.
A compass. A whistle. A key ring. A mirror. Miss Rao's steel pen.
Not one storybook. Not one pencil. Not one rupee from anybody's bag.
Every single thing on that list was shiny.

The next morning she came in early and stood at the cupboard.
The window beside it did not shut properly. The latch was bent outward.
And on the sill, stuck in the paint, there was one black feather.

She checked the dates. All four of them were Thursdays.
Thursday was games. The room stood empty for forty minutes.

And then she remembered something from June.
A whistle had gone missing that month too, and turned up a week later on the roof.
Nobody had ever asked how it got up there.

On Thursday morning, Tanvi asked Miss Rao if she could miss games. Just once.
Miss Rao looked at her for a moment, and said yes.

So Tanvi sat alone in an empty classroom with her hands in her lap,
and did not move for nineteen minutes.

At twenty past eleven, the bent latch swung open.
Something black came in off the water tank and hopped along the sill,
put its head on one side, and looked at the room with a bright yellow eye.

It took the silver foil off somebody's leftover chocolate,
and went straight back out of the window.

Tanvi stood on her chair to see where it went.
Three metres up, on the ledge under the water tank.
The wall below it was wet and green, with nothing to hold on to.
She got down off the chair and went to find Miss Rao.

Ramesh the gardener brought the long ladder.
On the ledge, in a nest of wire and string, they found the compass, the whistle,
two keys, a round mirror, and one steel pen with Miss Rao's name on it.
And about forty pieces of silver foil.

Before assembly on Monday, Tanvi found Imran at the water cooler.
"I thought it was you as well," she said. "On Tuesday. I am sorry."
Imran shrugged, and moved over so she could fill her bottle.

In assembly, Miss Rao asked her how she had worked it out.
Tanvi stood up. She did not say anything clever.

"Everyone was looking at Imran.
I was the only one looking at the window."

The crow still comes. 6B leave the foil out for it now, on the sill.
They named it Thursday.
```

---

## 5. Things that will go wrong, and what to do about them

**The generator refuses to draw children.** Some tools will not animate minors
from a photoreal prompt. Lean harder on "hand-drawn 2D comic illustration,
stylised, non-photoreal" — that usually clears it.

**Characters change face between shots.** Expected. Paste the character line
verbatim every time, and if the tool takes a reference image, generate Tanvi,
Imran and the crow once each and reuse them as references throughout.

**Text appears in the frame anyway.** Regenerate that shot. Do not accept it —
the caption band will sit on top of it, and misspelt English on a school wall in
a Class 6 assessment reads as our mistake, not the generator's.

**A shot lands short or long.** Fine. Note the real length of each shot when you
send it, or just send the assembled film and I will scale the caption track to
whatever the total turns out to be.

**The crow looks frightening.** Push it back toward comic — Thursday is a thief,
not a threat, and the ending only works if the class ends up fond of it.

---

## 6. When you send it back

Drop the file at `Thursday-Thief-Class6/story.mp4` and tell me its real
duration. I will swap the SVG stage for a `<video>` element, drive the existing
caption track off `video.currentTime` so the read-along still works, and keep
the SVG scenes as the fallback for the offline single-file build — that one gets
emailed and carried on USB sticks, so it cannot depend on a video that may not
travel with it.
