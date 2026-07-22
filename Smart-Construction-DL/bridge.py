"""
bridge.py - the Civil-Engineering -> AI teaching scaffold.
==========================================================
This module does not teach any NEW concept and it does not render any new
model, animation or asset. Every technical illustration in this course still
lives in app.py / story.py, exactly as before.

What this module does is answer, on every single page, the two questions a
Civil Engineering student actually has:

    1. "What is happening on the construction site?"
    2. "What AI concept solves this engineering problem?"

It wraps each existing stage renderer in a five-part structure:

    Civil Engineering   the site context      (bridge.open_page)
    The Challenge       why the manual way runs out (bridge.open_page)
    AI Connection       + the bridge figure   (bridge.open_page)
    Technical Idea      <- the EXISTING renderer, untouched
    Key Takeaway        one sentence          (bridge.close_page)
    In the Notebook     where it lives        (bridge.close_page)

Text is deliberately short: ~120-160 words per page across all prose fields.
Short sentences, active voice, no drama. The visuals carry the page; the text
supports them. Keep it that way when editing STEPS.

It also provides the new opening page (render_start) with the four sections:
the engineering problem, the project goal, the interactive engineering mind
map, and the Engineering-to-AI mapping.

COLOR IS A TEACHING DEVICE HERE. Amber is ALWAYS the construction world.
Cyan is ALWAYS the AI world. Violet is ALWAYS the technical process. That
never varies, on any page, in any figure.
"""
import streamlit as st
import plotly.graph_objects as go

# ---------------------------------------------------------------- palette
BG, PANEL = "#0e1117", "#161b22"
CIVIL = "#ffb74d"      # amber  - the construction site
AISIDE = "#4fc3f7"     # cyan   - the AI
TECH = "#ba68c8"       # violet - the technical process
GREEN, RED = "#66bb6a", "#ef5350"
MUTED, TEXT = "#8b949e", "#e6edf3"


# ============================================================================
# THE ENGINEERING WORKFLOW
# The phases of one construction day. Every AI concept hangs off one of them.
# The last one is not a day's work - it is the ledger the day gets judged by.
# ============================================================================
PHASES = [
    ("The Site",                     "One supervisor watches four hazards across a single shift."),
    ("Morning Inspection",           "Reality is turned into a written record."),
    ("Materials Arrive",             "The delivery lands and is checked in."),
    ("Preparing the Materials",      "Damaged stock is removed, everything is standardized, and the work is split."),
    ("Risk From Instruments",        "The gauges alone are used to predict danger."),
    ("The Visual Wall",              "The camera arrives and hand-written rules stop working."),
    ("Training a Supervisor",        "A competent supervisor learns how to decide."),
    ("Learning From Mistakes",       "The system gets better one wrong call at a time."),
    ("The Inspection Team",          "One inspector becomes a team."),
    ("The Automated Inspector",      "The machine looks, and shows you where it looked."),
    ("The Site Audit",               "We check whether it actually worked."),
    ("Accident Prevention",          "Every signal feeds one control room and one decision."),
    ("The Business Case",            "The system's payback is measured in man-hours."),
]


# ============================================================================
# THE STEPS  (one per page; len(STEPS) is the count - do not hardcode it)
#
# Each entry is one page of the course.
#   civil / ai     - the two names of the same idea (amber name, cyan name)
#   tech           - what is actually computed (violet)
#   site           - Civil Engineering. NO AI in this text. Ever. 2-4 sentences.
#   challenge      - The Challenge. Why the manual way runs out of road.
#   ai_link        - AI Connection. Why this AI concept is therefore required.
#   takeaway       - Key Takeaway. ONE sentence. The thing to leave with.
#   notebook       - In the Notebook. Where this lives in the Colab notebook.
#   contributes    - In the Notebook. What this step contributes to the system.
# ============================================================================
STEPS = [

# ---------------------------------------------- PHASE 1 - THE SITE
dict(
    id='site', phase=0,
    civil='A Tuesday On Site', ai='Why Automation Exists At All',
    civil_icon='🏗️', ai_icon='🤖',
    tech="Hazard timeline vs one supervisor's attention",
    civil_bullets=['Four live hazards', 'One supervisor', 'Nine hours'],
    ai_bullets=['Watches every area', 'All nine hours', 'Flags what is missed'],
    site="""The problem from the project brief, now as a timeline. Four hazards run at once across the
tunnel, the yard and the decks, and one supervisor can only be in one place at a time.""",
    challenge="""We already know one person cannot cover four hazards for nine hours. The question here is what
to do about it — not a better supervisor, but a way to watch the areas the supervisor cannot be in.""",
    ai_link="""That is the fix: a second set of eyes on the other three areas while the supervisor handles the
one in front of them. The supervisor stays in charge; AI simply eases the watching one person cannot
carry alone.""",
    notebook="""Act 1. The shift as an array, and a count of what one supervisor misses.""",
    contributes="""The requirement the system is measured against. If the missed-hazard count does not fall, it
failed.""",
    takeaway="""One person cannot cover four hazards for nine hours — so AI carries the extra watching.""",
),
dict(
    id='enter-ai', phase=0,
    civil='A Second Pair Of Eyes', ai='Continuous Monitoring',
    civil_icon='👁️', ai_icon='📡',
    tech='Same hazard timeline, watched continuously',
    civil_bullets=['Supervisor stays', 'Machine watches too', 'Nobody is replaced'],
    ai_bullets=['Watches all the time', 'It only flags', 'The human decides'],
    site="""Nothing on the site changes. Same eighteen workers, same excavator, same heat. The supervisor
still runs the job and still stops the work. Instruments and a camera are added, watching all four
hazards while the supervisor deals with one.""",
    challenge="""Every engineer meets the objection: is this here to replace me? No. A machine that sees only
numbers cannot walk over, smell the gas, or read a face. It can only notice.""",
    ai_link="""This fixes the role of AI for the whole project. The machine raises a flag. A human decides. Every
later design decision, especially the Phase 11 audit, follows from that split.""",
    notebook="""No code. This step is the argument, not the arithmetic.""",
    contributes="""Defines the system's output: an alert to a human, not an automated shutdown.""",
    takeaway="""The machine notices. The human decides.""",
),

# ---------------------------------------------- PHASE 2 - MORNING INSPECTION
dict(
    id='inspection', phase=1,
    civil='Morning Site Inspection', ai='Data Collection',
    civil_icon='📋', ai_icon='🗄️',
    tech='One shift -> one row of seven numbers + one image',
    civil_bullets=['Walk the site', 'Read the gauges', 'Write the record'],
    ai_bullets=['Each sensor is a column', 'Each moment is a row', 'Rows stack into a table'],
    site="""You walk the works with a clipboard. Gas meter in the tunnel: read it, write it. Noise, dust,
plant proximity: read, write. A three-dimensional site becomes a sheet of numbers.""",
    challenge="""Whoever reads that sheet next week does not get the site. Not the smell in the tunnel, not the
meter that was playing up. They get the numbers. Wrong record, wrong conclusion.""",
    ai_link="""An AI never sees your site and cannot walk out to check. One row of numbers is all it gets, so a
wrong row gives a wrong answer with no way to catch it. That is why the next four steps are about the
record.""",
    notebook="""The `SENSORS` list and one shift's row - the whole world, as the AI receives it.""",
    contributes="""Every prediction is computed from a row like this. It is the system's only contact with reality.""",
    takeaway="""The record is the AI's entire world. Wrong record, wrong model.""",
),
dict(
    id='two-worlds', phase=1,
    civil='Two Kinds Of Site Record', ai='Structured vs Unstructured Data',
    civil_icon='📊', ai_icon='🖼️',
    tech='7 named columns vs 150,528 unnamed pixels',
    civil_bullets=['Gauge readings', 'Camera footage', 'Same site, two records'],
    ai_bullets=['Columns a human named', 'Pixels nobody named', 'One AI for both?'],
    site="""Your site produces two kinds of record. The instrument log: gas, dust, temperature, humidity,
noise, acceleration, proximity - seven columns a human named and gave units. The tunnel camera:
light that fell on a sensor, with nothing in it named.""",
    challenge="""Gas at 420 means something before anyone analyzes it, because an engineer defined what it means.
The footage means nothing until a human watches it - nine hours per camera per day, six cameras.
It gets reviewed after an incident, which is too late.""",
    ai_link="""One site, two kinds of record, one question that decides the rest of the course: can one kind of
AI handle both? Phase 5 and Phase 6 answer it by building one and watching where it fails.""",
    notebook="""No code. Seven named columns set beside one image.""",
    contributes="""The two branches of the finished system. Everything runs down one or the other until Phase 12
fuses them.""",
    takeaway="""Named columns and raw pixels are two different problems.""",
),

# ---------------------------------------------- PHASE 3 - MATERIALS ARRIVE
dict(
    id='load', phase=2,
    civil='Material Delivery', ai='Loading The Dataset',
    civil_icon='🚚', ai_icon='📥',
    tech='pd.read_csv -> 1,220 shifts x 9 columns',
    civil_bullets=['Lorry arrives', 'Check the docket', 'Count what came'],
    ai_bullets=['Read the file', 'Check the header', 'Count the rows'],
    site="""The lorry backs on and the delivery is dropped. Before anything goes into the works you check the
docket against what is on the ground. How many pallets? Is this the grade ordered? Does the count
match?""",
    challenge="""The temptation is to skip it. The delivery looks fine, the programme is tight, the gang is
waiting. That is how a site discovers three weeks later that half a delivery was the wrong grade,
with the pour already cured.""",
    ai_link="""Loading a dataset is that delivery check, skipped for the same reason and with the same
consequences. Establish what arrived: how many shifts, how many columns, what type each is. A
model trained on the wrong data does not error. It trains without complaint and gives wrong answers.""",
    notebook="""`pd.read_csv` on the sensor log, then the row and column count.""",
    contributes="""The intake gate for the sensor branch. Every number the ANN learns from enters here.""",
    takeaway="""Check what arrived before you build with it.""",
),
dict(
    id='inspect', phase=2,
    civil='Material Quality Inspection', ai='Data Inspection',
    civil_icon='🔍', ai_icon='📉',
    tech='Missing-value counts, distributions, outliers',
    civil_bullets=['Open the bags', 'Look for damage', 'Diagnose before acting'],
    ai_bullets=['Count the gaps', 'Plot the spread', 'Diagnose before cleaning'],
    site="""Now open the delivery. Cut a bag and look at the cement. Walk the brick stack for frost damage and
cracks. You are diagnosing, not fixing. What you throw away depends on what you find.""",
    challenge="""You cannot eyeball 1,220 shifts the way you eyeball a brick stack. A gas sensor that dropped out
for an hour leaves a hole that looks like nothing. A thermometer stuck at 30.0 looks reasonable.
The damage is invisible at this scale.""",
    ai_link="""So inspect the record with counts and distributions instead of eyes. Count missing readings per
sensor and the failed device announces itself. Plot each column's spread and the stuck one spikes.
Diagnosis only - nothing is repaired here.""",
    notebook="""Missing-value counts per sensor, plus the per-column distribution plots.""",
    contributes="""Tells the next step what to remove. Skip it and you clean blind.""",
    takeaway="""Diagnose the data before you repair it.""",
),

# ---------------------------------------------- PHASE 4 - PREPARING THE MATERIALS
dict(
    id='clean', phase=3,
    civil='Removing The Broken Bricks', ai='Data Cleaning',
    civil_icon='🧱', ai_icon='🧹',
    tech='Drop duplicates, fill or drop missing readings',
    civil_bullets=['Cracked bricks out', 'Duplicate pallets out', 'Only sound stock builds'],
    ai_bullets=['Duplicate shifts out', 'Missing readings handled', 'Only sound rows train'],
    site="""Act on the diagnosis. Frost-damaged bricks go in the skip. The pallet booked in twice is struck
off. The half-empty bags need a judgement: top them up, or bin them.""",
    challenge="""That judgement is hard, and it is where inexperience shows. Throw away every flawed pallet and you
have nothing to build with. Use everything and you have built in a defect. No rule decides it for
you.""",
    ai_link="""A duplicated shift is the double-booked pallet: it teaches the model that one Tuesday mattered
twice. A missing gas reading is the half-empty bag - fill with the median, or drop the shift? Drop
too much and there is nothing to train on. Fill carelessly and the model believes readings that
never happened.""",
    notebook="""The duplicate drop and missing-value handling, with row counts before and after.""",
    contributes="""The ANN, the audit and the fusion engine inherit whatever you decide here.""",
    takeaway="""Cleaning is a judgement call, and everything downstream inherits it.""",
),
dict(
    id='normalize', phase=3,
    civil='Standardizing The Materials', ai='Normalization',
    civil_icon='📏', ai_icon='⚖️',
    tech='MinMaxScaler -> every sensor onto 0..1',
    civil_bullets=['Different units', 'One common standard', 'Now comparable'],
    ai_bullets=['ppm vs °C vs dB', 'All scaled 0..1', 'No column dominates'],
    site="""Materials arrive in whatever units their supplier used. Cement in kilograms, aggregate in cubic
metres, rebar in millimetres. Before any of it enters a mix design, it is converted onto one
common standard.""",
    challenge="""Raw magnitudes lie about importance. Gas runs into the hundreds of ppm. Acceleration runs 0 to 2
g. Side by side, gas looks two hundred times more significant because of a unit chosen decades
ago. A 2 g jolt is a machine strike.""",
    ai_link="""A neural network cannot tell a big number from an important one. It sees magnitude. Feed it raw
columns and it learns the unit, not the physics. Normalization puts every sensor on 0 to 1, so
importance is learned from the data.""",
    notebook="""`MinMaxScaler`, fitted on the sensor columns.""",
    contributes="""Without this the ANN trains badly and blames the wrong sensor. The scaler must ship with the
model.""",
    takeaway="""Scale the columns, or the network learns the units.""",
),
dict(
    id='split', phase=3,
    civil='Practice Work vs The Final Audit', ai='Train / Test Split',
    civil_icon='🧪', ai_icon='✂️',
    tech='train_test_split -> practice shifts vs unseen shifts',
    civil_bullets=['Trial panel', 'Sign-off inspection', 'Never the same panel'],
    ai_bullets=['Training set', 'Test set', 'Never the same rows'],
    site="""No competent site signs off the works using the trial panel. The trial panel is where the gang
practises and makes its mistakes. The final inspection happens on the actual structure, which they
have never built before.""",
    challenge="""An inspector who tested the works on the trial panel the gang had spent a fortnight perfecting
would certify nothing. They had learned that panel by heart. The inspection was a recital.""",
    ai_link="""The same holds if you test a model on the rows it trained on. It memorised them, scores
brilliantly, and proves nothing - the first new shift exposes it. So the shifts are split: some to
practise on, some locked away until the Phase 11 audit.""",
    notebook="""`train_test_split`, producing the practice shifts and the sealed final inspection.""",
    contributes="""This is what makes the Phase 11 audit mean anything. Break it and every result is a recital.""",
    takeaway="""The only fair score comes from shifts the model has never seen.""",
),

# ---------------------------------------------- PHASE 5 - RISK FROM INSTRUMENTS
dict(
    id='ml-baseline', phase=4,
    civil='Predicting Site Risk From The Instruments', ai='Machine Learning',
    civil_icon='📈', ai_icon='🌲',
    tech='RandomForestClassifier on 7 named sensors',
    civil_bullets=['Engineer names the factors', 'Machine weighs them', 'Risk score out'],
    ai_bullets=['Humans name the inputs', 'Random Forest', 'Good on columns'],
    site="""Every experienced engineer carries a risk model in their head. High gas, confined space, worker
nearby: stop the work. It is not written down, not consistent between two engineers, and not
available at three in the morning.""",
    challenge="""So write it down. Gas above what, exactly? Does the threshold move at thirty-eight degrees, and by
how much if the dust is up and the man is inside the tunnel? It is not a rule. It is thousands of
weighted interactions the engineer cannot articulate.""",
    ai_link="""This is the job machine learning does well. You do not state the thresholds. You state the factors
- and a human already did that at the morning inspection. Given seven named columns and 1,220
outcomes, the Random Forest works out the weighting itself. Phase 6 hands the same idea an image.""",
    notebook="""`RandomForestClassifier`, trained on the scaled sensors, scored on the sealed shifts.""",
    contributes="""The sensor branch of the system, and the benchmark Phase 11 uses.""",
    takeaway="""Name the factors; let the machine weigh them.""",
),

# ---------------------------------------------- PHASE 6 - THE VISUAL WALL
dict(
    id='pixel-problem', phase=5,
    civil='What The Site Camera Actually Sends', ai='Raw Pixels As Input',
    civil_icon='📷', ai_icon='🔢',
    tech='One frame = 224 x 224 x 3 = 150,528 numbers',
    civil_bullets=['You see a worker', 'Wearing a helmet', 'You just know it'],
    ai_bullets=['A grid of pixels', '150,528 numbers', "None says 'helmet'"],
    site="""Look at a frame from the tunnel portal camera. There is a worker, and he is wearing a hard hat.
You knew before you finished the sentence, without effort, and you have never had to explain how.""",
    challenge="""Now explain it - precisely enough that somebody who has never seen a helmet could follow the
instructions. What measurement, on what part of the image, at what threshold?""",
    ai_link="""The camera delivers a grid of 150,528 brightness values. Not one is named. Not one is the helmet.
At the morning inspection an engineer had already named gas, dust and proximity, which is why the
Random Forest could weigh them. Here nobody named anything, so there is nothing to weigh. This is
the wall.""",
    notebook="""The image loaded, its shape printed, then one pixel's actual value.""",
    contributes="""The input to the vision branch. Knowing what it is not is what makes Phase 10 make sense.""",
    takeaway="""A camera sends numbers, not objects, and none of them is named.""",
),
dict(
    id='handmade-features', phase=5,
    civil='Writing The Inspection Rule By Hand', ai='Hand-Crafted Feature Engineering',
    civil_icon='✍️', ai_icon='🧯',
    tech='yellow_fraction() + a threshold you tune yourself',
    civil_bullets=['Count the yellow', 'Call it a helmet', 'Watch it fail'],
    ai_bullets=['One rule by hand', 'Misses red and white', 'Each fix breaks two'],
    site="""No AI on this page. This is you, an engineering rule, and a threshold you control. Helmets are
yellow, so count the yellow: if there is enough, call it a helmet.""",
    challenge="""Every frame in that table contains a helmet. Your rule finds the yellow ones and is blind to the
red and the white, and no threshold fixes that. Add red: it flags the toolbox and the hoarding.
Add white: the sky and the vans. Demand roundness: wheels, buckets and bollards. Each fix invents
two new false alarms.""",
    ai_link="""A helmet is not a single color, shape or area. It is a pattern of thousands of relationships that
no human can write down by hand. So instead of writing features by hand, let the machine find
them.""",
    notebook="""`yellow_fraction`, then `looks_like_helmet` - switch the extra rules on and watch the false alarms
arrive.""",
    contributes="""Nothing, deliberately. Proving this is a dead end is what earns the CNN its place.""",
    takeaway="""Hand-written visual rules do not scale. Each fix breaks two other things.""",
),
dict(
    id='why-dl', phase=5,
    civil='Why The Rulebook Ran Out', ai='Learned Features: Deep Learning',
    civil_icon='🧠', ai_icon='🌊',
    tech='Human writes the features -> machine finds the features',
    civil_bullets=['Rules cannot scale', 'Patterns beat rules', 'Let it find them'],
    ai_bullets=['Nobody names features', 'It learns from examples', 'Layers build meaning'],
    site="""A new site engineer does not learn defects from a document. They walk the works with somebody
experienced, see a few hundred examples, and after a while they see it - and still cannot explain
what they saw.""",
    challenge="""You proved the alternative two pages ago. A helmet cannot be hand-written, not for want of
cleverness, but because it is not writable. Cracking, spalling, honeycombing and missing PPE have
the same character.""",
    ai_link="""Deep learning is not a fancier machine learning. It answers the question you just asked: if a
human cannot name the features, who does? You supply examples and outcomes, and the machine
constructs its own - edges, then shapes, then objects, layer by layer. That is what deep means.
Layered, not clever.""",
    notebook="""No code. The hinge of the notebook, stated straight after your rule failed.""",
    contributes="""Splits the project: named columns to machine learning, raw pixels to deep learning.""",
    takeaway="""When nobody can name the features, the machine learns them.""",
),

# ---------------------------------------------- PHASE 7 - TRAINING A SUPERVISOR
dict(
    id='supervisor-brain', phase=6,
    civil='A Supervisor Making A Safety Decision', ai='The Neuron',
    civil_icon='👷', ai_icon='⚪',
    tech='inputs x weights, summed, against a threshold',
    civil_bullets=['Notices a few things', 'Some worry more', 'Acts past a limit'],
    ai_bullets=['Take the inputs', 'Weigh each one', 'Fire past a limit'],
    site="""Watch a human think. A supervisor reaches a location and in two seconds asks a handful of
questions. Is the gas high? Is that man too near the excavator? They do not count those equally -
gas terrifies them, noise less so. They add up the worry and compare it against a private
threshold.""",
    challenge="""That threshold is the most valuable asset on the site, and it sits inside one person's head. It
walks off site at six o'clock, cannot be handed to the night shift or audited, and it retires in
eight years.""",
    ai_link="""Write down what they just did, in their language. What they notice: inputs. How much each worries
them: weights. The threshold before they act: bias. Adding up the worry: the weighted sum. The
call: the activation. You did not build something like a neuron. You built a neuron.""",
    notebook="""The supervisor's judgement as a dict, before the word neuron is used.""",
    contributes="""The unit the ANN is built from. Every neuron in Phase 9 is one of these supervisors.""",
    takeaway="""A neuron is a supervisor who only sees numbers and never tires.""",
),
dict(
    id='neuron', phase=6,
    civil='Weighing Each Warning Sign', ai='Weights, Bias, Weighted Sum',
    civil_icon='⚖️', ai_icon='∑',
    tech='z = Σ(wᵢxᵢ) + b, then σ(z)',
    civil_bullets=['Gas worries you most', 'Noise, less', 'Sum the worry'],
    ai_bullets=['Weigh each input', 'Add them up', 'Add a bias'],
    site="""Make the supervisor's judgement explicit. Gas kills: weight it heavily. Proximity to plant:
heavily too. Noise matters, but nobody died of noise this afternoon: weight it lightly. Sum the
worry, then compare it against how twitchy this supervisor is today.""",
    challenge="""Two supervisors with the same readings make different calls, and both can defend theirs. Their
weights differ because their careers differ. Neither can tell you their numbers, so neither can be
improved systematically.""",
    ai_link="""Written down, that judgement is the weighted sum plus a bias, and there is nothing else in it. The
weights are how much each reading worries this supervisor. The bias is how eager they are to act
before any reading arrives. Drag a weight here and you are hiring a different supervisor.""",
    notebook="""`sigmoid(z)` and the weighted sum, computed on one real shift.""",
    contributes="""These weights are what training changes. Phase 8 is machinery for choosing them.""",
    takeaway="""Weights are worry. Bias is eagerness to act.""",
),
dict(
    id='activation', phase=6,
    civil='The Stop-Work Threshold', ai='Activation Function',
    civil_icon='🛑', ai_icon='📐',
    tech='sigmoid / ReLU / tanh - the decision switch',
    civil_bullets=['Worry rises smoothly', 'The call is yes or no', 'It flips at a point'],
    ai_bullets=['Low score, no', 'High score, yes', 'A smooth switch'],
    site="""Concern on a site is smooth. It creeps up as the gas climbs and the crew tires. The decision is
not smooth. At some point the supervisor stops the work. There is no such thing as stopping the
work 43%.""",
    challenge="""It does not flip linearly either. A supervisor barely reacts through the safe range, goes from
relaxed to evacuating across a narrow band, then cannot get more alarmed than everybody out. Both
ends flat. The middle steep.""",
    ai_link="""That S-shape is the activation function, and it does two jobs. It turns continuous worry into a
decision. And it is the only non-linear thing in the network: strip it out and a thousand stacked
layers collapse algebraically into one neuron. No depth, no learned features, no Phase 10.""",
    notebook="""The sigmoid, ReLU and tanh curves plotted together.""",
    contributes="""No activation, no deep learning - literally. This is what lets the CNN build edges into helmets.""",
    takeaway="""The activation is what makes depth mean anything.""",
),

# ---------------------------------------------- PHASE 8 - LEARNING FROM MISTAKES
dict(
    id='learning-loop', phase=7,
    civil='Improving After Every Mistake', ai='The Training Loop',
    civil_icon='🔁', ai_icon='♻️',
    tech='predict -> compare -> adjust -> repeat',
    civil_bullets=['Make the call', 'Find out you were wrong', 'Adjust and go again'],
    ai_bullets=['Make a guess', 'Measure the error', 'Nudge the weights'],
    site="""A new supervisor makes a call: that looks fine, carry on. By lunchtime there is a near-miss where
they cleared. Nobody sacks them. They look at what they missed, nudge how much that sign worries
them, and walk the site again tomorrow.""",
    challenge="""The loop is right. The timescale is brutal. It takes twenty years, and the feedback is rare and
expensive, because the only way to learn you were wrong is for something to go wrong. None of it
transfers when they retire.""",
    ai_link="""Training is that loop with the timescale removed. Make a call. Find out you were wrong. Nudge the
weights. Repeat. A machine runs it against 1,220 recorded shifts in nine seconds, and nobody gets
hurt to generate the feedback - the outcome is already in the incident log.""",
    notebook="""No code. The loop in plain English, before a single symbol.""",
    contributes="""The mechanism by which both models come to exist. Nothing is programmed. Everything is nudged.""",
    takeaway="""Predict, measure the error, nudge, repeat.""",
),
dict(
    id='loss', phase=7,
    civil='How Wrong Was The Call?', ai='Loss Function',
    civil_icon='📛', ai_icon='📉',
    tech='Binary cross-entropy: -[y·log p + (1-y)·log(1-p)]',
    civil_bullets=['Sure and wrong: worst', 'Unsure and wrong: bad', 'Right costs nothing'],
    ai_bullets=['One number: how wrong', 'Sure and wrong hurts', 'Training drives it down'],
    site="""After a near-miss the site does not only ask whether the supervisor was wrong. It asks how wrong.
Someone who hesitated and said probably fine is not the same as someone who declared the tunnel
safe, confidently, in writing.""",
    challenge="""Being told you were wrong is useless for improvement. It gives no direction and no magnitude, so
it cannot tell you whether to nudge your judgement or overhaul it.""",
    ai_link="""The loss function measures how wrong, as one number. Look at its shape: as a confident prediction
turns out wrong, the loss does not rise gently - it goes vertical. Confidently wrong is punished
savagely, hesitantly wrong mildly, and being right costs nothing. That is your site review,
written as maths.""",
    notebook="""`bce(y_true, p)` - binary cross-entropy, plotted so you can watch the penalty go vertical.""",
    contributes="""The number training minimizes. Choose it badly and the system optimizes the wrong thing.""",
    takeaway="""Loss measures how wrong, not whether wrong.""",
),
dict(
    id='gradient-descent', phase=7,
    civil='Adjusting Your Inspection Strategy', ai='Gradient Descent',
    civil_icon='🏔️', ai_icon='⬇️',
    tech='w ← w − lr · ∂L/∂w',
    civil_bullets=['Which way is better?', 'Take a step', 'Repeat'],
    ai_bullets=['Slope of the loss', 'Step downhill', 'Until the bottom'],
    site="""Your inspection strategy is not right. Which way do you change it - worry more about gas, or less?
You lean one way and see whether the near-misses go up or down. That gives the direction. Then
keep going while things improve.""",
    challenge="""On a real site that experiment costs months. You change one thing at a time and see one outcome
per shift. With seven sensors interacting you would need a career, and the site would be built
before you finished.""",
    ai_link="""Gradient descent is that feel-your-way-downhill, except the slope is computed exactly, for every
weight at once, in one pass. Picture the loss as a valley: high ground is bad weights, the bottom
is the best ones. Step against the slope, then look again.""",
    notebook="""The valley `loss(w) = (w - 2.0) ** 2 + 1`, with the descent traced step by step.""",
    contributes="""Every weight in both models arrived at its value through this rule.""",
    takeaway="""The gradient is the answer to which way is downhill.""",
),
dict(
    id='learning-rate', phase=7,
    civil='How Big Should Each Improvement Be?', ai='Learning Rate',
    civil_icon='👣', ai_icon='🎚️',
    tech='the lr in w ← w − lr · ∂L/∂w',
    civil_bullets=['Tiny changes: too slow', 'Huge changes: chaos', 'Sensible: steady'],
    ai_bullets=['Too small: crawls', 'Too big: overshoots', 'The key setting'],
    site="""You know the direction. How hard do you swing? Tighten your gas threshold by a hair and progress
is far too slow. React to one incident by shutting the tunnel at any detectable reading and the
programme grinds to a halt.""",
    challenge="""Overreaction is worse than doing nothing. Swing hard after every incident and the strategy
oscillates: too tight, then too loose after the complaints, then too tight again. You never
settle, and you fight the last accident instead of the next one.""",
    ai_link="""That is the learning rate, the most consequential number you will set. Too small and training
crawls and never arrives. Too large and it overshoots the valley floor and bounces up the far
side, exactly like the organization that lurches from crisis to crisis.""",
    notebook="""Three panels: one rate too small, one about right, one that diverges off the chart.""",
    contributes="""Almost every model-will-not-train problem in your career is this number.""",
    takeaway="""Right direction, wrong step size, no result.""",
),
dict(
    id='optimizer', phase=7,
    civil='Choosing The Improvement Strategy', ai='Optimizers',
    civil_icon='🧭', ai_icon='🚀',
    tech='SGD vs Momentum vs Adam',
    civil_bullets=['Same step everywhere?', 'Or build momentum?', 'Or adapt per-issue?'],
    ai_bullets=['SGD: uniform', 'Momentum: carries speed', 'Adam: per-weight'],
    site="""There is more than one way to run an improvement programme. Review everything by the same amount
every month: simple, fair, slow. Or notice you have corrected the same drift for six months and
move faster on it. Or spend effort where it is needed.""",
    challenge="""Uniform stepping is simple but inefficient. It creeps along the gentle drift you should be
striding down, and takes the same cautious step on the issue that needs a decisive correction.""",
    ai_link="""That is SGD, momentum and Adam. SGD steps the same everywhere. Momentum builds speed while the
direction keeps being confirmed. Adam gives every weight its own step size, so settled weights
barely move and the problem weight gets a proper correction. Adam is the practical default - a
management strategy, not a magic word.""",
    notebook="""No code of its own. `optimizer='adam'` in `ann.compile()` is where you pick one.""",
    contributes="""Turns `optimizer='adam'` into a decision you can defend.""",
    takeaway="""Optimizers decide how the step size is chosen, per weight.""",
),

# ---------------------------------------------- PHASE 9 - THE INSPECTION TEAM
dict(
    id='network', phase=8,
    civil='The Inspection Team', ai='The Neural Network',
    civil_icon='👥', ai_icon='🕸️',
    tech='7 inputs -> hidden (8, 6) -> 1 risk output',
    civil_bullets=['Specialists first', 'Then a lead', 'Then one call'],
    ai_bullets=['Input layer', 'Hidden layers', 'Output'],
    site="""No serious project runs on one person. A gas specialist lives in the tunnel and thinks about
ventilation. A plant supervisor watches slewing radii. An environmental officer covers dust and
noise. Each is narrow and excellent, and none makes the final call.""",
    challenge="""One person cannot hold all of it. Expertise is depth, and depth is narrow. Ask one person to be
all four specialists and you get four mediocrities in one head.""",
    ai_link="""That structure is the network. The input layer is the seven gauges. The first hidden layer is your
specialists, each neuron watching a few sensors. The second is the lead: it never sees a gauge,
only the specialists' opinions, which is why it can spot hot AND high-gas AND worker-close. Depth
is a reporting structure.""",
    notebook="""The Keras `Sequential` model - seven inputs, hidden layers, one sigmoid output.""",
    contributes="""The sensor-branch model the fusion engine consults in Phase 12.""",
    takeaway="""Depth is a reporting structure, not complexity for its own sake.""",
),
dict(
    id='training', phase=8,
    civil='Training The New Recruits', ai='Training & Epochs',
    civil_icon='🎓', ai_icon='📊',
    tech='model.fit - loss falling epoch by epoch',
    civil_bullets=['Walk the archive', 'Get corrected', 'Walk it again'],
    ai_bullets=['One epoch = one pass', 'Loss falls', 'Watch for overfitting'],
    site="""Sit the team down with the site's incident archive - every shift, every reading, and what really
happened. Let them call each one. Correct every mistake. Then walk them through the archive again,
and again. Nobody gets good on one pass.""",
    challenge="""Drill a team on the same hundred case studies long enough and they stop learning to judge and
start learning the answer sheet. They recite your archive and fall apart on a shift they have not
seen.""",
    ai_link="""One full pass through the archive is an epoch, and training repeats it while the loss falls. Watch
the two curves. While both fall together, the team is learning. When the practice curve keeps
falling and the unseen curve turns back up, they have started memorising. That gap is overfitting.""",
    notebook="""`ann.fit(...)` with validation data - the two curves that tell you learned or memorised.""",
    contributes="""Turns the Phase 9 architecture into a model that predicts anything.""",
    takeaway="""When the unseen curve turns up, it is memorising, not learning.""",
),

# ---------------------------------------------- PHASE 10 - THE AUTOMATED INSPECTOR
dict(
    id='cnn-journey', phase=9,
    civil='How An Engineer Actually Sees', ai='CNN Feature Maps',
    civil_icon='🔬', ai_icon='🧩',
    tech='Real VGG16: edges -> textures -> objects',
    civil_bullets=['Edges first', 'Then shapes', "Then 'that is PPE'"],
    ai_bullets=['Early layers: edges', 'Mid: textures/parts', 'Deep: whole objects'],
    site="""Watch your own eyes work. You do not perceive a worker in a helmet in one go. Something registers
edges and boundaries first. Those edges assemble into shapes: a curve, a rim, a shoulder. Only at
the top does it become a man in a hard hat.""",
    challenge="""In Phase 6 you tried to jump from raw pixels to helmet in one leap, with a color rule, and it
collapsed. The leap is too big. Nobody, human or machine, gets from brightness values to a named
object in a single step.""",
    ai_link="""The CNN builds up in small steps. These are real VGG16 feature maps: the early layers found
edges, the middle layers textures and parts, the deep layers whole objects. Detail is reduced while
meaning grows, and the network learns these filters from examples.""",
    notebook="""VGG16 loaded, the three depths extracted, plus the real `block1_conv1` kernels.""",
    contributes="""The vision branch, and the direct answer to the wall you hit in Phase 6.""",
    takeaway="""Edges, then parts, then objects. Depth is layered abstraction.""",
),
dict(
    id='gradcam', phase=9,
    civil='Which Part Of The Worker Decided It', ai='Grad-CAM',
    civil_icon='🔦', ai_icon='🌡️',
    tech='Gradient-weighted class activation heat map',
    civil_bullets=['Show me the defect', 'Not just the verdict', 'Or I cannot sign'],
    ai_bullets=['Heat map of evidence', 'Shows where it looked', 'You can check it'],
    site="""An inspector tells you the panel has failed. Your response is the same three words every time:
show me where. A verdict without evidence cannot be acted on, signed off, or defended. You cannot
rework a defect you cannot locate.""",
    challenge="""The model fails that standard. It reports no helmet, 94% confident. Show me where. It cannot. And
a model can be right for the wrong reason - flagging the tunnel because tunnel shots are dark -
and score well until the lighting changes.""",
    ai_link="""Grad-CAM is show me where, answered. It traces which regions drove the decision and paints them as
heat. If it flags a missing helmet, the heat should be on the head. Heat on the scaffolding means
you have caught a fraud the accuracy score would have hidden.""",
    notebook="""`block5_conv3` and the gradient-weighted map, then the interpretation markdown.""",
    contributes="""Makes the vision branch auditable. An unauditable safety model is not deployable, whatever it
scores.""",
    takeaway="""Demand the evidence, not just the verdict.""",
),

# ---------------------------------------------- PHASE 11 - THE SITE AUDIT
dict(
    id='audit', phase=10,
    civil='The Construction Safety Audit', ai='Confusion Matrix',
    civil_icon='📁', ai_icon='🔲',
    tech='TN / FP / FN / TP on the sealed test shifts',
    civil_bullets=['Line up every claim', 'Against what happened', 'Four possible outcomes'],
    ai_bullets=['Two right boxes', 'Two wrong boxes', 'One miss matters most'],
    site="""Audit this the way you would audit a subcontractor who claimed the work was done. A hundred shifts
happened. The incident log says what really happened on every one. The system made a call on every
one. Line them up and count.""",
    challenge="""Four things can happen, and lumping them together hides the one that matters. Said safe, was
safe: fine. Said risk, there was an incident: caught it. Said risk, nothing happened: a false alarm,
ten minutes of a supervisor's time. Said safe, when there was actually a risk: the costly miss - the
box that lets an incident through.""",
    ai_link="""Put those four boxes in a square and you have built the confusion matrix - you did not learn it,
you audited a site and it fell out. Never quote accuracy alone for a safety system: a model that
says safe to everything scores extremely well while missing every real risk.""",
    notebook="""The test-set predictions, `ConfusionMatrixDisplay`, and the warning that follows.""",
    contributes="""The acceptance test, run on the shifts sealed away in Phase 4.""",
    takeaway="""Accuracy hides the one box that matters most - the missed risk.""",
),
dict(
    id='proof', phase=10,
    civil='Instruments vs Eyes: The Verdict', ai='Where Deep Learning Actually Wins',
    civil_icon='⚖️', ai_icon='🏁',
    tech='RF vs ANN on sensors; rules vs CNN on pixels',
    civil_bullets=['Gauges: both fine', 'Camera: only one works', 'Right tool, right job'],
    ai_bullets=['Numbers: both work', 'Images: only DL', 'Pick the right tool'],
    site="""The verdict, and it is not the one a vendor would give you. On the seven instrument columns a
human engineer named, machine learning and deep learning perform about the same. Not close. The
same.""",
    challenge="""So if deep learning does not win on the gauges, why did you learn it? Because of the camera. Your
hand-written rule failed and no threshold saved it. Random Forest cannot be pointed at 150,528
unnamed numbers at all - there is nothing for it to weigh.""",
    ai_link="""Here is the thesis of the course, proved rather than asserted. Deep learning does not dig deeper
into your columns. It digs where there are no columns. When a human has named the features, use
machine learning - simpler, faster, easier to defend. When nobody can name them, deep learning is
the only option.""",
    notebook="""Random Forest against the ANN on sensors, and the pixel task neither could touch.""",
    contributes="""Justifies two branches instead of one model - and stops you reaching for deep learning on a
spreadsheet.""",
    takeaway="""Deep learning wins where nobody can name the features.""",
),

# ---------------------------------------------- PHASE 12 - ACCIDENT PREVENTION
dict(
    id='fusion-engine', phase=11,
    civil='The Site Control Room', ai='AI Fusion',
    civil_icon='🎛️', ai_icon='🔗',
    tech='CNN + ANN + RFID + zone -> one named alert',
    civil_bullets=['Every feed lands here', 'Compared side by side', 'One clear action'],
    ai_bullets=['One signal: weak', 'All combined: an alert', 'This is the product'],
    site="""Every serious site has a control room. The gas panel on one wall, the CCTV bank on another, the
RFID log in the corner. The person in the middle does not read any one feed. Their job is to
cross-reference them.""",
    challenge="""Each feed alone is close to noise. The camera says a helmet is missing - he might be in the site
office. The gas sensor says 45 ppm - there may be nobody within fifty metres. The access log says
Tunnel Zone - he might be fully kitted out. A system that alarms on any one gets switched off in a
fortnight.""",
    ai_link="""Now fuse them. Worker 18, identified by his RFID tag, is in the Tunnel Zone, a confined space,
with no helmet, breathing 45 ppm. That is not four weak signals. That is an emergency with a name
attached. Several models, several sensors, one decision, one human who acts.""",
    notebook="""`fusion_engine(helmet, vest, gas_ppm, zone, worker)` - the control room as a function. Note how
little of it is AI.""",
    contributes="""This is the product. Everything before it was a component.""",
    takeaway="""Weak signals, fused, become one actionable alert.""",
),
dict(
    id='pipeline', phase=11,
    civil='The Complete Intelligent Construction Site', ai='The AI Engineering Pipeline',
    civil_icon='🏙️', ai_icon='🛤️',
    tech='Site → data → models → fusion → alert → human',
    civil_bullets=['Started with a site', 'Ended with a site', 'Somebody goes home safe'],
    ai_bullets=['One box is a network', 'The rest is engineering', 'Most of it is not AI'],
    site="""Look at the day you have walked through. Morning inspection. Materials checked in. Damaged stock
skipped, the rest standardized. Risk predicted from the instruments. The visual inspection defeats
the rulebook. The audit is run properly. The control room sends somebody to the tunnel.""",
    challenge="""Now count the boxes in that pipeline, and count how many were a neural network. One. The sensors,
the cleaning, the standardizing, the splitting, the fusion and the human at the end are where real
systems are won and lost. Most AI courses teach the one box.""",
    ai_link="""Artificial intelligence is an engineering pipeline, not a neural network. You did not learn AI on
top of Civil Engineering - you did Civil Engineering, and AI turned out to be the part a human
could not do fast enough. Deep learning exists because of the wall you hit trying to hand-write
helmet.""",
    notebook="""The closing markdown - the whole pipeline, with the network shown as the one box it is.""",
    contributes="""The finished system, and the answer to Phase 1: one human, with this pipeline behind them, can.""",
    takeaway="""AI is a pipeline. The network is one box in it.""",
),

# ---------------------------------------------- PHASE 13 - THE BUSINESS CASE
dict(
    id='manpower', phase=12,
    civil='The Manpower Ledger', ai='Quantifying The Benefit',
    civil_icon='📋', ai_icon='📊',
    tech='Man-hours before − man-hours after = the business case',
    civil_bullets=['Hours are the currency', 'Count them carefully', "Redeploy, don't sack"],
    ai_bullets=['Hours before', 'Hours after', 'The difference is the case'],
    site="""Every project ends in front of the person who signs for it, and they do not care that the network
learned its own features. A safety officer costs money by the hour. Patrolling four zones costs
hours. Writing the shift log costs hours.""",
    challenge="""The answer has to be in hours, not accuracy. And the real answer is never that the work
vanished. Somebody still walks out when the system shouts. Somebody still reads what it wrote.
Somebody still wipes the lens.""",
    ai_link="""This page is that answer: the safety work of one shift, by hand and with the system, and the
difference. Set the crew, the shift and the month to your own site. The bottom bar never reaches
zero, because automation moves work rather than deleting it.""",
    notebook="""No notebook cell. The ledger is a site calculation, not a model - put your own timesheet numbers
in it.""",
    contributes="""What gets the system funded, and Phase 1's question answered in hours.""",
    takeaway="""Automation moves work. It does not delete it.""",
),
]

# ---------------------------------------------------------------- short labels
# The full civil names are the page titles, and they collide at mind-map scale.
# These are the same activity, named tightly enough to sit on a node.
SHORT = {
    "site": "Tuesday on site",              "enter-ai": "Second pair of eyes",
    "inspection": "Morning inspection",     "two-worlds": "Two site records",
    "load": "Material delivery",            "inspect": "Quality inspection",
    "clean": "Broken bricks out",           "normalize": "Standardize",
    "split": "Practice vs audit",           "ml-baseline": "Risk from gauges",
    "pixel-problem": "The site camera",     "handmade-features": "Rule by hand",
    "why-dl": "Rulebook fails",             "supervisor-brain": "Supervisor decides",
    "neuron": "Weighing warnings",          "activation": "Stop-work threshold",
    "learning-loop": "Learn from mistakes", "loss": "How wrong?",
    "gradient-descent": "Adjust strategy",  "learning-rate": "How big a step",
    "optimizer": "Which strategy",          "network": "Inspection team",
    "training": "Train the recruits",       "cnn-journey": "How engineers see",
    "gradcam": "Show me where",             "audit": "Safety audit",
    "proof": "The verdict",                 "fusion-engine": "Control room",
    "pipeline": "The whole site",         "manpower": "The manpower ledger",
}
for _s in STEPS:
    _s["short"] = SHORT[_s["id"]]

# --------------------------------------------------------------- lookups
BY_ID = {s["id"]: s for s in STEPS}
ORDER = [s["id"] for s in STEPS]


def _phase_steps(pi):
    return [s for s in STEPS if s["phase"] == pi]


def goto(stage):
    st.query_params["stage"] = stage
    st.rerun()


# ============================================================================
# THE BRIDGE FIGURE
# Left = the construction site (amber). Right = the AI (cyan).
# Between them an animated arrow, and under it the technical process (violet).
# This is the one visual that appears on every single page of the course.
# ============================================================================
def _wrap(text, width=24):
    """Break a title onto as many lines as it needs. Card widths are fixed;
    titles are not, and 'The Complete Intelligent Construction Site' is real."""
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


def _card(fig, x0, x1, color, icon, title, bullets, kicker):
    fig.add_shape(type="rect", x0=x0, x1=x1, y0=0.4, y1=5.5,
                  line=dict(color=color, width=2), fillcolor=PANEL, layer="below")
    cx = (x0 + x1) / 2
    fig.add_annotation(x=cx, y=5.05, text=f"<b>{kicker}</b>", showarrow=False,
                       font=dict(size=11, color=color), xanchor="center")
    fig.add_annotation(x=cx, y=4.25, text=icon, showarrow=False,
                       font=dict(size=34), xanchor="center")
    fig.add_annotation(x=cx, y=3.25, text=f"<b>{_wrap(title)}</b>", showarrow=False,
                       font=dict(size=14, color=TEXT), xanchor="center", align="center")
    for i, b in enumerate(bullets):
        fig.add_annotation(x=cx, y=2.25 - i * 0.55, text=f"• {b}", showarrow=False,
                           font=dict(size=12, color=MUTED), xanchor="center")


def bridge_figure(step, style, animate):
    """The engineering-activity -> AI-equivalent -> technical-process bridge."""
    fig = go.Figure()
    _card(fig, 0.2, 3.4, CIVIL, step["civil_icon"], step["civil"],
          step["civil_bullets"], "ON THE SITE")
    _card(fig, 6.6, 9.8, AISIDE, step["ai_icon"], step["ai"],
          step["ai_bullets"], "IN THE AI")

    # the arrow between the two worlds
    fig.add_annotation(x=6.45, y=3.0, ax=3.55, ay=3.0, xref="x", yref="y",
                       axref="x", ayref="y", showarrow=True, arrowhead=2,
                       arrowsize=1.4, arrowwidth=2.5, arrowcolor=MUTED, text="")
    fig.add_annotation(x=5.0, y=3.5, text="<b>becomes</b>", showarrow=False,
                       font=dict(size=12, color=MUTED))

    # the technical process, under the arrow (sits in the gap, never on a card)
    fig.add_shape(type="rect", x0=3.5, x1=6.5, y0=1.3, y1=2.15,
                  line=dict(color=TECH, width=1.5), fillcolor=PANEL, layer="below")
    fig.add_annotation(x=5.0, y=1.96, text="<b>WHICH IS COMPUTED AS</b>", showarrow=False,
                       font=dict(size=9, color=TECH))
    fig.add_annotation(x=5.0, y=1.58, text=step["tech"], showarrow=False,
                       font=dict(size=10, color=TEXT), xanchor="center", align="center")
    fig.add_annotation(x=5.0, y=2.45, text="↓", showarrow=False,
                       font=dict(size=18, color=TECH))

    # the travelling pulse: this is what makes the bridge read as a direction
    fig.add_trace(go.Scatter(x=[3.6], y=[3.0], mode="markers",
                             marker=dict(size=15, color=CIVIL,
                                         line=dict(color=TEXT, width=1)),
                             hoverinfo="skip", showlegend=False))
    frames = []
    for i in range(24):
        t = i / 23
        x = 3.6 + t * 2.8
        # the pulse literally changes color as it crosses: amber -> cyan
        c = CIVIL if t < 0.45 else (TEXT if t < 0.55 else AISIDE)
        frames.append(go.Frame(data=[go.Scatter(
            x=[x], y=[3.0], mode="markers",
            marker=dict(size=15, color=c, line=dict(color=TEXT, width=1)))]))
    animate(fig, frames, ms=90)

    fig.update_xaxes(visible=False, range=[0, 10])
    fig.update_yaxes(visible=False, range=[0.2, 5.7])
    return style(fig, h=360)


# ============================================================================
# NAVIGATION - previous / current / next ENGINEERING step
# ============================================================================
def _nav_strip(step, key):
    i = ORDER.index(step["id"])
    prev_s = BY_ID[ORDER[i - 1]] if i > 0 else None
    next_s = BY_ID[ORDER[i + 1]] if i < len(ORDER) - 1 else None
    c1, c2, c3 = st.columns([1, 1.25, 1])
    with c1:
        if prev_s:
            if st.button(f"◀  {prev_s['civil']}", key=f"prev_{key}",
                         use_container_width=True):
                goto(prev_s["id"])
        else:
            if st.button("◀  The project overview", key=f"prev_{key}",
                         use_container_width=True):
                goto("start")
    with c2:
        st.markdown(
            f"<div style='text-align:center;padding:6px 4px;border:1px solid {CIVIL};"
            f"border-radius:8px;background:{PANEL}'>"
            f"<span style='color:{MUTED};font-size:11px'>YOU ARE HERE · STEP {i+1} OF {len(ORDER)}</span><br>"
            f"<b style='color:{CIVIL}'>{step['civil']}</b></div>",
            unsafe_allow_html=True)
    with c3:
        if next_s:
            if st.button(f"{next_s['civil']}  ▶", key=f"next_{key}",
                         use_container_width=True):
                goto(next_s["id"])
        else:
            if st.button("Back to the overview  ▶", key=f"next_{key}",
                         use_container_width=True):
                goto("start")


# ============================================================================
# open_page  -  Parts 1, 2 and 3, rendered ABOVE the existing stage renderer
# ============================================================================
def open_page(stage, style, animate):
    step = BY_ID.get(stage)
    if step is None:
        return
    pname, pdesc = PHASES[step["phase"]]

    _nav_strip(step, "top")
    st.markdown(
        f"<div style='margin-top:14px;color:{MUTED};font-size:13px'>"
        f"PHASE {step['phase']+1} OF {len(PHASES)} · <b style='color:{CIVIL}'>{pname}</b>"
        f" — {pdesc}</div>", unsafe_allow_html=True)
    st.markdown(f"# {step['civil_icon']}  {step['civil']}")
    st.markdown(
        f"<span style='color:{MUTED}'>This engineering activity is the AI concept </span>"
        f"<b style='color:{AISIDE}'>{step['ai']}</b>.",
        unsafe_allow_html=True)
    st.divider()

    # ---- Part 1 -----------------------------------------------------------
    st.markdown(f"### <span style='color:{CIVIL}'>Civil Engineering</span>",
                unsafe_allow_html=True)
    st.markdown(
        f"<div style='border-left:3px solid {CIVIL};padding:2px 0 2px 16px;"
        f"color:{TEXT};font-size:16px;line-height:1.65'>{step['site']}</div>",
        unsafe_allow_html=True)
    st.write("")

    # ---- Part 2 -----------------------------------------------------------
    st.markdown(f"### <span style='color:{CIVIL}'>The Challenge</span>",
                unsafe_allow_html=True)
    st.markdown(
        f"<div style='border-left:3px solid {RED};padding:2px 0 2px 16px;"
        f"color:{TEXT};font-size:16px;line-height:1.65'>{step['challenge']}</div>",
        unsafe_allow_html=True)
    st.write("")

    # ---- Part 3 -----------------------------------------------------------
    st.markdown(f"### <span style='color:{AISIDE}'>AI Connection</span>",
                unsafe_allow_html=True)
    st.markdown(
        f"<div style='border-left:3px solid {AISIDE};padding:2px 0 2px 16px;"
        f"color:{TEXT};font-size:16px;line-height:1.65'>{step['ai_link']}</div>",
        unsafe_allow_html=True)
    st.plotly_chart(bridge_figure(step, style, animate), use_container_width=True,
                    key=f"bridge_{stage}")
    st.caption("▶ Press Play to watch the engineering activity cross into the AI.")
    st.divider()

    # ---- Part 4 header ----------------------------------------------------
    st.markdown(f"### <span style='color:{TECH}'>Technical Idea</span>",
                unsafe_allow_html=True)
    st.caption(f"{step['tech']} — interactive. Change things and watch what happens.")


# ============================================================================
# close_page  -  Part 5, rendered BELOW the existing stage renderer
# ============================================================================
def close_page(stage):
    step = BY_ID.get(stage)
    if step is None:
        return
    st.divider()

    # ---- the one sentence to leave with ------------------------------------
    st.markdown(
        f"<div style='background:{PANEL};border-left:4px solid {AISIDE};border-radius:8px;"
        f"padding:14px 18px'>"
        f"<div style='color:{MUTED};font-size:11px;letter-spacing:.8px'>KEY TAKEAWAY</div>"
        f"<div style='color:{TEXT};font-size:19px;font-weight:600;line-height:1.5'>"
        f"{step['takeaway']}</div></div>", unsafe_allow_html=True)
    st.write("")

    st.markdown("### <span style='color:#8bc34a'>In the Notebook</span>",
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Where you implement it**\n\n{step['notebook']}")
    with c2:
        st.markdown(f"**What it contributes**\n\n{step['contributes']}")

    render_quiz(stage)

    # ---- the pipeline reminder: where this step sits in the whole build ----
    st.write("")
    dots = []
    for i, (pname, _) in enumerate(PHASES):
        if i == step["phase"]:
            dots.append(f"<span style='color:{CIVIL};font-weight:700'>● {pname}</span>")
        elif i < step["phase"]:
            dots.append(f"<span style='color:#3f4650'>● {pname}</span>")
        else:
            dots.append(f"<span style='color:#3f4650'>○ {pname}</span>")
    st.markdown(
        f"<div style='background:{PANEL};border-radius:8px;padding:10px 14px;font-size:12px;"
        f"line-height:2.1'><span style='color:{MUTED}'>THE BUILD SO FAR &nbsp;</span>"
        + " &nbsp;→&nbsp; ".join(dots) + "</div>", unsafe_allow_html=True)
    st.write("")
    _nav_strip(step, "bottom")


# ============================================================================
# CHECK-YOUR-UNDERSTANDING QUIZ  (one question per stage, shown by close_page)
# Each entry: q = question, options = choices, answer = index of the correct
# option, why = the explanation shown after any answer is picked.
# ============================================================================
QUIZ = {
    'site': dict(
        q="One supervisor cannot cover four hazards across a nine-hour shift. What is AI's role here?",
        options=["Replace the supervisor with a faster automated one",
                 "Watch the areas the supervisor cannot be in, so nothing goes unwatched",
                 "Reduce the site to fewer than four hazards",
                 "Decide on its own when to stop the works"],
        answer=1,
        why="One person cannot be in four places for nine hours. AI carries the extra watching; the supervisor stays in charge."),
    'enter-ai': dict(
        q="With continuous monitoring added, who acts on a flagged hazard?",
        options=["The machine, by shutting down the work automatically",
                 "Whichever sensor crosses its threshold first",
                 "The human — the machine only notices and raises a flag",
                 "The camera, once it has enough confidence"],
        answer=2,
        why="The machine notices; the human decides. That split defines the system's output as an alert, not an automated shutdown."),
    'inspection': dict(
        q="When the morning inspection becomes a written record, what does the AI actually get?",
        options=["A live view of the whole site",
                 "One row of numbers (plus an image) — with none of the site's context",
                 "The supervisor's memory of the shift",
                 "A three-dimensional model of the tunnel"],
        answer=1,
        why="The AI never walks the site. One row is its entire world, so a wrong record produces a wrong model with no way to catch it."),
    'two-worlds': dict(
        q="Why are the instrument log and the camera footage treated as two different problems?",
        options=["The camera is newer than the sensors",
                 "The log has seven named columns a human defined; the image is thousands of pixels nobody named",
                 "The footage is stored in a different folder",
                 "One is measured in the morning and one in the afternoon"],
        answer=1,
        why="Named columns and raw pixels are different kinds of record, so they need different tools — the branches only fuse at the end."),
    'load': dict(
        q="Why check the delivery — row count, column count, types — before building anything on the data?",
        options=["To make the file open faster",
                 "Because a model trained on wrong data does not error; it trains happily and gives wrong answers",
                 "Because the law requires a data audit",
                 "To remove duplicate sites from the log"],
        answer=1,
        why="Loading is the delivery check. Establish what actually arrived, because silent bad data produces a confidently wrong model."),
    'inspect': dict(
        q="How do you find a sensor that dropped out or stuck, hidden inside 1,220 shifts?",
        options=["Read every row by eye until something looks odd",
                 "Count missing values per sensor and plot each column's spread — the fault announces itself",
                 "Trust each sensor's own status indicator",
                 "Retrain the model until the fault disappears"],
        answer=1,
        why="You cannot eyeball 1,220 shifts. Counts and distributions make a dropout or a stuck reading show up. This step diagnoses only; nothing is repaired yet."),
    'clean': dict(
        q="What makes data cleaning a judgement call rather than a fixed rule?",
        options=["There is one correct threshold that always applies",
                 "Drop too much and there is nothing to train on; fill carelessly and the model believes readings that never happened",
                 "Cleaning never changes the results",
                 "Only duplicate rows ever need attention"],
        answer=1,
        why="Deciding what to drop and what to fill is a judgement, and the ANN, the audit and the fusion engine all inherit whatever you decide."),
    'normalize': dict(
        q="Why put every sensor on a common 0–1 scale before training the network?",
        options=["To use less memory",
                 "Because the network reads magnitude, not meaning — raw gas in the hundreds would swamp a 2 g jolt that matters more",
                 "Because 0–1 numbers are easier to read",
                 "So all the columns fit on one screen"],
        answer=1,
        why="A network cannot tell a big number from an important one. Scaling lets importance be learned from the data, not from the units."),
    'split': dict(
        q="Why must the model be scored on shifts it never trained on?",
        options=["To use up the leftover data",
                 "A model tested on its training shifts just recites what it memorised and proves nothing about the next shift",
                 "Because the test shifts are cleaner",
                 "It is unnecessary as long as accuracy is high"],
        answer=1,
        why="You do not sign off the works on the trial panel the gang perfected. Only a score on sealed, unseen shifts says anything real."),
    'ml-baseline': dict(
        q="What do you give the Random Forest, and what does it work out for itself?",
        options=["The exact risk thresholds; it just applies them",
                 "The seven named factors plus 1,220 outcomes; it learns the weighting to a risk score itself",
                 "A camera frame; it reads the helmets",
                 "Nothing — it guesses at random"],
        answer=1,
        why="You state the factors — a human named them at the morning inspection — not the thresholds. Given those columns and outcomes, the model learns the mapping."),
    'pixel-problem': dict(
        q="What does the site camera actually deliver to the model?",
        options=["A labelled object called 'helmet'",
                 "A grid of 150,528 brightness numbers, not one of them named",
                 "A short written description of the scene",
                 "A single measurement of how safe the frame is"],
        answer=1,
        why="A camera sends numbers, not objects. Nothing in the raw frame is pre-named, so there is nothing for a Random Forest to weigh — this is the wall."),
    'handmade-features': dict(
        q="Why does a hand-written 'count the yellow' rule fail as a helmet detector?",
        options=["Yellow is impossible to measure in an image",
                 "A helmet is not one colour, shape or area — each fix (add red, add white, add roundness) invents two new false alarms",
                 "The camera cannot see yellow",
                 "The rule is too slow to run"],
        answer=1,
        why="Hand-written visual rules do not scale. A helmet is a pattern of thousands of relationships no human can write down by hand."),
    'why-dl': dict(
        q="What does deep learning actually change compared with machine learning?",
        options=["It runs the same rules on a faster computer",
                 "It answers who names the features: when a human cannot, the machine constructs its own, layer by layer",
                 "It always beats machine learning on every task",
                 "It removes the need for any training data"],
        answer=1,
        why="Deep learning is not fancier ML. It earns its place where nobody can name the features — it learns them from examples instead."),
    'supervisor-brain': dict(
        q="A supervisor notices a few signals, worries about each unequally, and acts past a threshold. That is essentially…",
        options=["A spreadsheet formula",
                 "A single artificial neuron",
                 "A database lookup",
                 "A coin toss"],
        answer=1,
        why="Inputs, weights, a bias threshold, a weighted sum and an activation — you did not build something like a neuron, you built a neuron."),
    'neuron': dict(
        q="In a neuron, what do the weights and the bias represent in the supervisor's language?",
        options=["The weights are the sensor units; the bias is the time of day",
                 "The weights are how much each reading worries the supervisor; the bias is how eager they are to act",
                 "The weights are random; the bias is the accuracy",
                 "Both are fixed constants that never change"],
        answer=1,
        why="Weights are worry — how much each reading matters. Bias is eagerness to act before any reading arrives. Training is what changes them."),
    'activation': dict(
        q="Why does a deep network need a non-linear activation function?",
        options=["It makes the numbers smaller",
                 "Without it, a thousand stacked layers collapse algebraically into a single neuron — no depth, no learned features",
                 "It speeds up the computation",
                 "It converts the image into numbers"],
        answer=1,
        why="The activation turns continuous worry into a decision and is the only non-linear part; strip it out and depth means nothing."),
    'learning-loop': dict(
        q="What is the core cycle the training loop repeats?",
        options=["Load, save, delete, repeat",
                 "Predict, measure the error, nudge the weights, repeat",
                 "Guess once and keep the result",
                 "Ask a human for every answer"],
        answer=1,
        why="Training is a new supervisor's learn-from-mistakes loop with the timescale removed — run against recorded shifts, with nobody hurt to generate the feedback."),
    'loss': dict(
        q="What does the loss function measure?",
        options=["Whether the prediction was right or wrong, as a yes/no",
                 "How wrong the prediction was, as one number that punishes confident mistakes savagely",
                 "How fast the model runs",
                 "How many sensors were used"],
        answer=1,
        why="Loss measures how wrong, not whether wrong. A confident wrong call sends the loss vertical; hesitant wrong is mild; being right costs nothing."),
    'gradient-descent': dict(
        q="What question does the gradient answer during training?",
        options=["How many epochs are left",
                 "Which way to change each weight to reduce the loss — the downhill direction",
                 "Which sensor is most expensive",
                 "Whether the data was cleaned"],
        answer=1,
        why="The gradient is the exact answer to 'which way is downhill', computed for every weight at once so the model can step toward lower loss."),
    'learning-rate': dict(
        q="You have the right direction downhill. Why does the learning rate still matter?",
        options=["It decides which sensors to use",
                 "Too small and training crawls and never arrives; too large and it overshoots the valley and bounces up the far side",
                 "It cleans the training data",
                 "It only affects how the results are displayed"],
        answer=1,
        why="Right direction, wrong step size, no result. The learning rate is the most consequential single number you set."),
    'optimizer': dict(
        q="What does choosing an optimizer such as Adam actually decide?",
        options=["Which loss function to minimize",
                 "How the step size is chosen — Adam gives every weight its own step, so settled weights barely move and problem weights get corrected",
                 "How many hidden layers the network has",
                 "Which sensors are named"],
        answer=1,
        why="Optimizers decide how the step size is chosen, per weight. Adam is the practical default — a management strategy, not a magic word."),
    'network': dict(
        q="Why does stacking neurons into hidden layers add power?",
        options=["More layers always memorise faster",
                 "Depth is a reporting structure: specialists watch a few sensors, then a lead combines their opinions to spot combinations",
                 "Each extra layer stores more raw data",
                 "Layers make the network run faster"],
        answer=1,
        why="Depth is a reporting structure, not complexity for its own sake. The second layer sees the specialists' opinions, so it can spot hot AND high-gas AND worker-close."),
    'training': dict(
        q="During training, how do you tell learning apart from memorising?",
        options=["The training loss stops falling",
                 "When the unseen (validation) curve turns back up while the practice curve keeps falling, it has started memorising",
                 "When the model finishes one epoch",
                 "When accuracy reaches exactly 100%"],
        answer=1,
        why="One epoch is one pass through the archive. While both curves fall together it is learning; the gap that opens when the unseen curve rises is overfitting."),
    'cnn-journey': dict(
        q="How does a CNN get from raw pixels to recognising 'a worker in a helmet'?",
        options=["In one leap, using a single colour rule",
                 "In small steps — early layers find edges, middle layers textures and parts, deep layers whole objects",
                 "By comparing the image to a stored photo",
                 "By asking the sensor log"],
        answer=1,
        why="The Phase 6 leap from pixels to helmet was too big. A CNN builds up edges, then parts, then objects — depth is layered abstraction, learned from examples."),
    'gradcam': dict(
        q="Why is Grad-CAM's heat map needed on top of the CNN's verdict?",
        options=["It makes the model run faster",
                 "It shows where the model looked, so a right-for-the-wrong-reason model (e.g. flagging dark tunnel shots) is exposed and the call can be signed off",
                 "It improves the accuracy score directly",
                 "It labels the sensors"],
        answer=1,
        why="Demand the evidence, not just the verdict. Heat on the head confirms a real miss; heat on the scaffolding reveals a fraud the accuracy score would have hidden."),
    'audit': dict(
        q="Why is accuracy alone a dangerous score for a safety model?",
        options=["Accuracy is hard to calculate",
                 "It hides the four outcomes — especially the missed risk (said safe, was dangerous); a model that says 'safe' to everything scores well while missing every real risk",
                 "Accuracy only works on images",
                 "It requires the training set"],
        answer=1,
        why="The confusion matrix splits the calls into four boxes. The one that matters most is the missed risk — the box that lets an incident through."),
    'proof': dict(
        q="On the seven named sensor columns, how do machine learning and deep learning compare — and what does that prove?",
        options=["Deep learning wins easily, so always use it",
                 "They perform about the same on the named columns; deep learning only pulls ahead where nobody can name the features, like the camera image",
                 "Machine learning cannot handle the sensors at all",
                 "Neither works on the sensors"],
        answer=1,
        why="Deep learning does not dig deeper into named columns — ML matches it there. It wins where there are no columns to name, which is exactly the pixel task."),
    'fusion-engine': dict(
        q="Why does the control room fuse the model outputs instead of alarming on any single feed?",
        options=["Fusing is cheaper to compute",
                 "Each feed alone is close to noise — a missing helmet, 45 ppm, and a tunnel zone are weak apart but together are one named emergency",
                 "Only one feed is ever correct",
                 "The models cannot run separately"],
        answer=1,
        why="Weak signals, fused, become one actionable alert. A system that alarms on any single feed gets switched off in a fortnight."),
    'pipeline': dict(
        q="Of all the boxes in the finished pipeline, how many are a neural network — and what is the lesson?",
        options=["All of them; AI is the network",
                 "One — the sensors, cleaning, standardizing, splitting, fusion and the human are engineering; AI is a pipeline, the network is one box",
                 "None; the pipeline uses no AI",
                 "Exactly half"],
        answer=1,
        why="AI is an engineering pipeline, not a neural network. Most of the value lives in the boxes around the one network, and a human still makes the call."),
    'manpower': dict(
        q="When the benefit is measured in man-hours, why does the bottom bar never reach zero?",
        options=["Because the sensors are expensive",
                 "Because automation moves work rather than deleting it — someone still responds, still reads the log, still cleans the lens",
                 "Because the model is never accurate enough",
                 "Because the shift is always nine hours"],
        answer=1,
        why="The honest answer is in hours, not accuracy, and the work never fully vanishes. Automation redeploys people; it does not delete the job."),
}


def render_quiz(stage):
    """One check-your-understanding MCQ per stage. Portable across all four
    apps — self-contained, no theme-specific helpers."""
    q = QUIZ.get(stage)
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


# ============================================================================
# SECTION 3 - THE INTERACTIVE ENGINEERING MIND MAP
# A vertical spine of the twelve engineering phases of one construction day.
# Every node is clickable and opens that learning page.
# ============================================================================
def mind_map(style):
    fig = go.Figure()
    n = len(PHASES)
    ys = {i: (n - 1 - i) * 1.0 for i in range(n)}

    # the spine: the construction day, top to bottom
    for i in range(n - 1):
        fig.add_annotation(x=0, y=ys[i + 1] + 0.42, ax=0, ay=ys[i] - 0.42,
                           xref="x", yref="y", axref="x", ayref="y",
                           showarrow=True, arrowhead=2, arrowsize=1.1,
                           arrowwidth=2, arrowcolor=CIVIL, text="")

    GAP = 2.05          # wide enough that two short labels never touch
    X0 = 1.3

    sx, sy, stext, scustom, shover = [], [], [], [], []
    for pi, (pname, pdesc) in enumerate(PHASES):
        kids = _phase_steps(pi)
        # branch connectors from the spine out to each step
        for k, s in enumerate(kids):
            fig.add_shape(type="line", x0=0.25, y0=ys[pi], x1=X0 + k * GAP, y1=ys[pi],
                          line=dict(color="#2b323c", width=1.5), layer="below")
        # the phase node itself
        fig.add_annotation(x=0, y=ys[pi], text=f"<b>{pi+1}</b>", showarrow=False,
                           font=dict(size=13, color=BG),
                           bgcolor=CIVIL, bordercolor=CIVIL, borderpad=6, borderwidth=2)
        fig.add_annotation(x=-0.32, y=ys[pi], text=f"<b>{pname}</b>", showarrow=False,
                           xanchor="right", font=dict(size=13, color=CIVIL))
        fig.add_annotation(x=-0.32, y=ys[pi] - 0.34, text=_wrap(pdesc, 30), showarrow=False,
                           xanchor="right", align="right", font=dict(size=10, color=MUTED))
        # the clickable step nodes
        for k, s in enumerate(kids):
            sx.append(X0 + k * GAP)
            sy.append(ys[pi])
            stext.append(f"{s['civil_icon']} {s['short']}")
            scustom.append(s["id"])
            shover.append(f"<b>{s['civil']}</b><br>"
                          f"<span style='color:{AISIDE}'>= {s['ai']}</span><br>"
                          f"<i>click to open</i>")

    fig.add_trace(go.Scatter(
        x=sx, y=sy, mode="markers+text", text=stext, textposition="top center",
        textfont=dict(size=10, color=TEXT), customdata=scustom,
        marker=dict(size=17, color=PANEL, line=dict(color=AISIDE, width=2),
                    symbol="circle"),
        hovertemplate="%{hovertext}<extra></extra>", hovertext=shover,
        showlegend=False))

    fig.update_xaxes(visible=False, range=[-4.4, X0 + 4 * GAP + 1.4])
    fig.update_yaxes(visible=False, range=[-0.8, n - 0.2])
    return style(fig, h=1000)


# ============================================================================
# SECTION 4 - THE ENGINEERING-TO-AI MAPPING
# The single most important visualization in the project.
# Left column: the Civil Engineering process. Right column: the AI process.
# ============================================================================
def mapping_figure(style):
    fig = go.Figure()
    n = len(STEPS)
    for i, s in enumerate(STEPS):
        y = (n - 1 - i) * 1.0
        # civil (amber, left)
        fig.add_shape(type="rect", x0=0, x1=3.6, y0=y - 0.36, y1=y + 0.36,
                      line=dict(color=CIVIL, width=1.2), fillcolor=PANEL, layer="below")
        fig.add_annotation(x=0.16, y=y, text=f"{s['civil_icon']} {s['civil']}",
                           showarrow=False, xanchor="left",
                           font=dict(size=11.5, color=TEXT))
        # the arrow: the whole point of the figure
        fig.add_annotation(x=4.5, y=y, ax=3.7, ay=y, xref="x", yref="y",
                           axref="x", ayref="y", showarrow=True, arrowhead=2,
                           arrowsize=1.1, arrowwidth=1.6, arrowcolor=MUTED, text="")
        # ai (cyan, right)
        fig.add_shape(type="rect", x0=4.6, x1=8.2, y0=y - 0.36, y1=y + 0.36,
                      line=dict(color=AISIDE, width=1.2), fillcolor=PANEL, layer="below")
        fig.add_annotation(x=4.76, y=y, text=f"{s['ai_icon']} {s['ai']}",
                           showarrow=False, xanchor="left",
                           font=dict(size=11.5, color=TEXT))
        # phase tag
        fig.add_annotation(x=8.4, y=y, text=f"{s['phase']+1}", showarrow=False,
                           xanchor="left", font=dict(size=9, color="#3f4650"))

    fig.add_annotation(x=0, y=n - 0.35, text="<b>CIVIL ENGINEERING PROCESS</b>",
                       showarrow=False, xanchor="left", font=dict(size=12, color=CIVIL))
    fig.add_annotation(x=4.6, y=n - 0.35, text="<b>THE AI PROCESS THAT SOLVES IT</b>",
                       showarrow=False, xanchor="left", font=dict(size=12, color=AISIDE))

    fig.update_xaxes(visible=False, range=[-0.2, 9.0])
    fig.update_yaxes(visible=False, range=[-0.8, n + 0.2])
    return style(fig, h=980)


# ============================================================================
# THE OPENING PAGE
# ============================================================================
def render_start(style, animate):
    st.markdown("# 🏗️  A Man Management Dilemma")
    st.markdown(
        f"<div style='color:{MUTED};font-size:17px;line-height:1.6'>"
        f"This is a real construction-site safety problem. One person cannot watch everything at once, "
        f"no matter how hard they try. AI shows up here because the site needs it.</div>",
        unsafe_allow_html=True)
    st.divider()

    # ---------------------------------------------- SECTION 1: THE PROBLEM
    st.markdown(f"## <span style='color:{CIVIL}'>1 · The engineering problem</span>",
                unsafe_allow_html=True)
    st.markdown("""
Eighteen workers are spread across four areas, and one supervisor cannot see all of them at once.
Four risks are present at the same time: gas in the tunnel, dust in the yard, an excavator working
near people, and helmets left off in the heat. The supervisor can only be in one place and watch one
thing at a time, so over a nine-hour shift some of these risks go unwatched.
    """)
    st.divider()

    # ---------------------------------------------- SECTION 2: THE GOAL
    st.markdown(f"## <span style='color:{CIVIL}'>2 · What we are going to build</span>",
                unsafe_allow_html=True)
    st.markdown("""
An **intelligent construction monitoring system**. Concretely, four parts:
    """)
    c1, c2, c3, c4 = st.columns(4)
    for col, (icon, title, body) in zip(
        (c1, c2, c3, c4),
        [("📡", "Sensors observe the conditions",
          "Gas, dust, temperature, humidity, noise, vibration, proximity to plant. Read continuously, "
          "whether or not anybody is standing there."),
         ("📷", "Cameras observe the workers",
          "The tunnel portal, the decks, the yard. Watching what no gauge can measure: is that person "
          "wearing their helmet?"),
         ("🔗", "AI combines both",
          "Neither stream means much alone. A missing helmet in the site office is nothing. In a "
          "gas-filled tunnel it is an emergency. Only the combination is a decision."),
         ("🔔", "The supervisor gets an alert",
          "A named, actionable call, right now: worker 18, tunnel zone, no helmet, 45 ppm, get him "
          "out.")]):
        with col:
            st.markdown(
                f"<div style='background:{PANEL};border-radius:10px;padding:14px;height:100%;"
                f"border-top:3px solid {CIVIL}'><div style='font-size:26px'>{icon}</div>"
                f"<b style='color:{TEXT}'>{title}</b><br>"
                f"<span style='color:{MUTED};font-size:13px'>{body}</span></div>",
                unsafe_allow_html=True)
    st.write("")
    st.markdown(
        f"<div style='border-left:3px solid {GREEN};padding:8px 0 8px 16px;font-size:16px;"
        f"color:{TEXT};line-height:1.65'>The supervisor stays in charge and stays accountable. Nothing "
        f"here replaces them or stops the works by itself. The system just keeps watching the other "
        f"areas, all shift, without a break — so the site ends up <b>safer</b>.</div>",
        unsafe_allow_html=True)
    st.divider()

    # ---------------------------------------------- SECTION 3: MIND MAP
    st.markdown(f"## <span style='color:{CIVIL}'>3 · The engineering workflow</span>",
                unsafe_allow_html=True)
    st.markdown(
        f"<div style='color:{MUTED};font-size:15px;line-height:1.6'>These "
        f"{len(PHASES)} phases are <b>one construction day</b>, in the order a real project runs "
        f"them — from the morning inspection through to the safety record that funds it. Every "
        f"<b style='color:{CIVIL}'>amber node</b> is a construction activity. Every "
        f"<b style='color:{AISIDE}'>step hanging off it</b> is a page. "
        f"<b>Click any step to open it.</b></div>", unsafe_allow_html=True)
    st.write("")

    fig = mind_map(style)
    try:
        ev = st.plotly_chart(fig, use_container_width=True, key="mindmap",
                             on_select="rerun", selection_mode="points")
        pts = (ev or {}).get("selection", {}).get("points", [])
        if pts:
            cd = pts[0].get("customdata")
            target = cd[0] if isinstance(cd, list) else cd
            if target in BY_ID:
                goto(target)
    except TypeError:
        # older streamlit: the map still renders, the sidebar still navigates
        st.plotly_chart(fig, use_container_width=True, key="mindmap_static")
        st.info("Click-to-open needs Streamlit ≥ 1.35. Use the sidebar to jump to a step.")
    st.divider()

    # ---------------------------------------------- SECTION 4: THE MAPPING
    st.markdown(f"## <span style='color:{AISIDE}'>4 · Engineering → AI, the whole map</span>",
                unsafe_allow_html=True)
    st.markdown(
        f"<div style='color:{MUTED};font-size:15px;line-height:1.6'><b>Every AI concept here is a "
        f"construction activity you already understand</b> — the same thing, named differently by a "
        f"different profession. Read down the amber column and you have described a construction day. "
        f"Read down the cyan column and you have described a deep learning pipeline. They are the same "
        f"column.</div>", unsafe_allow_html=True)
    st.write("")
    st.plotly_chart(mapping_figure(style), use_container_width=True, key="mapping")

    st.markdown(
        f"<div style='border-left:3px solid {AISIDE};padding:8px 0 8px 16px;font-size:16px;"
        f"color:{TEXT};line-height:1.65'>Each AI concept shows up because the construction day ran "
        f"into something a human could not do. Only then does it get a technical name.</div>",
        unsafe_allow_html=True)
    st.write("")

    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("▶  Start: it is Tuesday morning", use_container_width=True,
                     type="primary"):
            goto("site")
    with c2:
        st.caption(f"{len(PHASES)} phases · {len(STEPS)} steps · one construction day. "
                   "Every step has narration at the bottom of its page.")
