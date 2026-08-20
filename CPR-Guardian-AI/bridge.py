"""The teaching registry: one entry per page, in the order the notebook works.

Every entry keeps the same parts, and the same plain-English house style: short
sentences, everyday words, and no term used before it is explained.
  doing     - what we do on this page, and why we do it here
  scene     - what is happening in the room, with no computer in it
  challenge - why that is hard for the person doing it
  ai_link   - what the unit is actually being asked to do
  tech      - the one-line technical idea
  plain     - the technical name in everyday words, for a first-time reader
  figure    - what the picture on the page shows
  watch     - what changed in that picture, and what hovering it tells you
  notebook  - which notebook section this matches
  takeaway  - one sentence to remember
  next_q    - the question this page leaves open, answered by the next page

THE PHASES ARE THE METHOD. There is one spine, not two: each of the ten phases
is a step of an ordinary data project - understand the problem, decide what to
measure, collect, explore and clean, build features, build the decision logic,
evaluate, act, report, admit the limits - and the pages inside a phase are that
step done on this problem. The page titles stay about the emergency; the phase
name is what the student is actually learning.

`plain` exists because every heading carries a term of art - "pose keypoints",
"compression fraction", "peak finder". A student meeting those for the first
time should never have to guess.

`next_q` exists because a student who finishes a page and clicks 'next' with no
idea why that page comes next is reading a list, not following an argument.

MEDICAL WORDS ARE SPELLED OUT, EVERY TIME. This is taught to engineering
students, not clinicians. 'AED' is written as 'the defibrillator' and explained
where it first appears; 'sternum' is 'the breastbone'; 'recoil' is 'letting the
chest come back up'. Any future edit should keep that rule.

No computed figure is quoted in this prose. Every number on a page is worked
out by that page, so the two can never drift apart.
"""

# Said once, plainly, under the phase table on the landing page. A student who
# has met other apps in this series will look for the training phase and needs
# to be told why there is not one, rather than assume it was forgotten.
WORKFLOW_NOTE = (
    "One thing is deliberately missing from that list: **nothing here is trained**. There is "
    "no model that learned anything from data. The push counter is three lines of ordinary "
    "code, and the decision logic is a checklist in a fixed order. That is the honest answer "
    "for this problem, and knowing when you do *not* need a trained model is as much a part "
    "of the job as building one.")

# ONE SPINE, TEN PHASES. Each phase is a step of an ordinary data project, and
# the pages inside it are that step done on this problem. There used to be two
# numbering systems - six story phases and eleven workflow steps, both printed
# on every header - which meant a reader had to hold two positions at once.
#
# Phases must stay CONTIGUOUS in page order, because the header prints
# "PHASE n OF 10": a page order that jumps 7, 8, 7, 8 reads as a mistake. That
# constraint is what moved 'Hands Off The Chest' up next to the fatigue page.
PHASES = [

    ("Understand The Problem",
     "What is actually going wrong, before any data or any code."),
    ("Decide What To Measure",
     "Which piece of hardware is allowed to answer which question."),
    ("Collect The Data",
     "No recording of a real emergency exists, so we make one."),
    ("Explore And Clean The Data",
     "Look at both sensors as they come, then deal with the wobble."),
    ("Feature Engineering",
     "Turn a wiggly line into one row per push, then build the column that matters."),
    ("Build The Decision Logic",
     "Where a model would normally be trained. Here it is a ranked checklist."),
    ("Evaluate The Whole Session",
     "Two ways of catching the same fault, and the cost of every pause."),
    ("Turn Numbers Into Actions",
     "A measurement is not an instruction. This is where it becomes one."),
    ("Report The Result",
     "Three and a half minutes, handed over in about five seconds."),
    ("Be Honest About The Limits",
     "What would break in a real room, exact enough to go and test."),
]

STEPS = [
    dict(id="collapse", phase=0, scene="Nobody Here Is Trained", ai="The Real Problem",
         doing="Work out what is actually going wrong, before choosing anything clever. "
               "Everything else in this app exists because of what is on this page.",
         tech="a wall unit with a camera, a pressure pad, a speaker and three lights",
         site=("Someone collapses in a busy station.",
               "A stranger kneels down to help.",
               "They have never done this before."),
         challenge=("The ambulance is still minutes away.",
                    "Whatever happens in those minutes is down to this stranger.",
                    "And nobody tells them whether it is working."),
         ai_link=("The unit does not try to work out what is wrong with the patient.",
                  "It watches how this one person is pushing.",
                  "Then it says the one thing most worth changing."),
         plain="'Chest compressions' means pushing down hard and fast in the middle of "
               "someone's chest to keep their blood moving while their heart has stopped. "
               "Anyone can do it, and most people who end up doing it have never been taught.",
         figure="Two lines, both showing how the chance of surviving falls as the minutes "
                "pass. Red is nobody pushing at all. Green is a bystander pushing and keeping "
                "going. The shaded band is roughly how long an ambulance takes to arrive.",
         watch="Look at the gap between the two lines at the edge of the shaded band. Almost "
               "all of that gap was created by an untrained stranger, before any professional "
               "arrived. Hover either line to read its number at that minute.",
         notebook="The opening - what the unit is and what the four minutes are for.",
         next_q="So the unit has to judge how well this stranger is pushing. It has a camera "
                "on the wall and a pressure pad on the patient's chest. **Which of the two "
                "should measure how far down the chest goes?** The obvious answer is the "
                "camera, and the next page is about why that answer is wrong."),

    dict(id="sensors", phase=1, scene="Camera, Pad Or Defibrillator?", ai="The Sensor Split",
         doing="Decide which piece of hardware is allowed to answer which question. Get this "
               "wrong here and everything built on top of it is worthless.",
         tech="camera for the body - pad for depth, speed and release - defibrillator for the heart",
         site=("The easy idea: point one camera at everything.",
               "One camera, one wire, every answer.",
               "It does not work."),
         challenge=("A camera sees pixels, not centimetres.",
                    "Turning one into the other is a sum.",
                    "That sum changes with the lens, the angle, and the size of the person.",
                    "Get it wrong by a fifth and the pushing does nothing."),
         ai_link=("Ask each part only what it can actually answer.",
                  "Camera: where the arms and shoulders are.",
                  "Pad: how far the chest moves."),
         plain="A 'sensor' is anything that measures the world and turns it into numbers - a "
               "camera, a pressure pad, a thermometer. The whole question on this page is "
               "which of those numbers you are entitled to believe.",
         notebook="The framing table at the top of the notebook.",
         takeaway="Most of the engineering in a safe system is deciding what each part is not "
                  "allowed to do.",
         next_q="We now know which sensor answers what. But we have no recording of a real "
                "emergency to test any of it on, and we are never going to get one. **So "
                "where does the data come from?**"),

    dict(id="rescue", phase=2, scene="Three And A Half Minutes", ai="The Simulated Session",
         doing="Get the data. Since no real recording exists, we write code that generates "
               "one, with every fault we need to catch deliberately put inside it.",
         tech="two helpers, one pause for the defibrillator, two different ways of being wrong",
         site=("Helper A starts well, then gets tired.",
               "The defibrillator stops everything for twelve seconds.",
               "Helper B takes over, and pushes far too slowly."),
         challenge=("Nobody films real emergencies for us to study.",
                    "The only practice data comes from a dummy in a classroom.",
                    "Nothing goes wrong there, so there is nothing to learn from."),
         ai_link=("So we write code that invents the three and a half minutes.",
                  "We put every fault in ourselves, on purpose.",
                  "That way we always know the right answer."),
         plain="'Simulated' means every number in this app was produced by code, not recorded "
               "from a real person. It lets us study the method without ever touching "
               "anybody's medical records.",
         figure="The whole three and a half minutes as the pressure pad felt it. Every push is "
                "one thin vertical spike. The green band is how far down a push should go. The "
                "red blocks are the seconds when nobody was pushing at all.",
         watch="Look at the two red blocks - the first is the helper arriving, the second is "
               "the defibrillator. Then notice you cannot read a single push at this zoom, "
               "which is exactly what the next page fixes. Hover a red block to see how long "
               "that pause lasted.",
         notebook="Section 2 - simulating the rescue.",
         takeaway="A degrades gradually, which is hard to notice from inside. B is wrong "
                  "immediately, which is easy to fix once somebody says so.",
         next_q="We have the recording. But at this zoom every push is one thin line, and a "
                "good push looks exactly like a bad one. **What does a single compression "
                "actually look like, close up?**"),

    dict(id="pad", phase=3, scene="What The Pad Feels", ai="The Depth Signal",
         doing="Look at the raw signal before doing anything to it. Zoom in until one push is "
               "readable, and see what changes as the helper tires.",
         tech="fifty readings a second of how far the chest is pressed in",
         site=("Push down, let go. That is one compression.",
               "The pad measures the chest fifty times a second.",
               "Drawn out, one push is one bump."),
         challenge=("Zoomed out, hundreds of bumps are squashed together.",
                    "You cannot tell a good one from a bad one.",
                    "The sensor is fine. The zoom is the problem."),
         ai_link=("Zoom in on five seconds instead.",
                  "Now three faults are obvious at once.",
                  "Lower bumps, closer together, never coming back to the top."),
         plain="The 'depth signal' is one number, fifty times a second: how far down the chest "
               "is at this instant. Everything the unit ever says is worked out from that "
               "single wiggly line.",
         figure="The same helper twice, one minute apart. Left is fresh at 20 seconds, right "
                "is tired at 92 seconds. The green band is the right depth. The dotted red "
                "line is where the chest should return to between pushes.",
         watch="On the right the peaks are lower, they sit closer together, and the bottoms of "
               "the line never come back down to the dotted red line - the helper is resting "
               "their weight on the chest. Hover any peak to read its exact depth and time.",
         notebook="Section 2.1 - the pad signal.",
         takeaway="Nothing in this signal is subtle once you look at the right timescale. The "
                  "helper simply cannot see it while they are doing it.",
         next_q="The pad tells us how far the chest moved. It cannot see the helper's arms at "
                "all. **So how does the unit know whether they are pushing with straight arms "
                "or bent ones?**"),

    dict(id="camera", phase=3, scene="What The Camera Sees", ai="Pose Keypoints",
         doing="Look at the other sensor, and see exactly what a camera does and does not "
               "hand us.",
         tech="wrist, elbow and shoulder, as positions in centimetres",
         site=("The camera puts dots on the body it can see.",
               "We use only three: wrist, elbow, shoulder.",
               "Everything else is maths on those three dots."),
         challenge=("The camera cannot tell you the chest moved five centimetres.",
                    "It can easily tell you the arms are bent.",
                    "Two very different questions."),
         ai_link=("Only ask it the question it is good at.",
                  "Its answers fix the helper's own arms and shoulders.",
                  "They never touch the patient's chest."),
         plain="'Pose keypoints' are the dots a vision model puts on a body - shoulder, elbow, "
               "wrist and so on. The computer does not see a person. It sees a handful of "
               "labelled dots and where each one is.",
         figure="Three snapshots of the same stick figure - wrist, elbow and shoulder joined "
                "up. The white cross is the middle of the breastbone, where the hands belong. "
                "The dotted line runs straight up from it.",
         watch="In the middle panel, the tired helper, the arm has bent and the shoulder has "
               "slipped back off the dotted line, so the arms are doing work the body weight "
               "should be doing. Hover any dot to read its position in centimetres.",
         notebook="Section 3 - what the camera sees.",
         takeaway="Straight arms mean body weight is doing the work. Bent arms mean the helper "
                  "is, and they will not last two minutes.",
         next_q="Those dots wobble by a few millimetres every frame, because no camera is "
                "perfectly steady. **How much does a few millimetres of wobble actually "
                "matter?** The answer is the reason depth comes from the pad."),

    dict(id="elbow", phase=3, scene="The Angle At The Elbow", ai="Geometry, And Jitter",
         doing="Turn raw dots into a usable number, then deal with the noise that comes with "
               "them. This is the cleaning step every data project has.",
         tech="the angle between elbow-to-shoulder and elbow-to-wrist",
         site=("Three dots, one angle.",
               "A straight arm measures about 180 degrees.",
               "A bent arm measures less."),
         challenge=("The three dots sit almost in a straight line.",
                    "So a tiny sideways shift swings the angle a long way.",
                    "The number jumps about while the arm is holding still."),
         ai_link=("Average the angle over half a second.",
                  "The reading now lags slightly behind the arm.",
                  "In return, most of the jumping goes away."),
         plain="'Jitter' is the small random wobble in a measurement from one moment to the "
               "next. The dots are never perfectly still, so any angle worked out from them is "
               "never perfectly still either.",
         figure="Three lines over ten seconds. Grey is the angle straight from the raw dots. "
                "Blue is the same angle after averaging. The dashed purple line is what the "
                "arm was really doing. Below the dotted red line the arms are bending.",
         watch="The grey line jumps several degrees while the purple line barely moves - all "
               "of that jumping is camera wobble, not the helper. Blue sits almost on top of "
               "purple. Hover any point to compare the raw and the smoothed angle at that "
               "instant.",
         notebook="Section 3.1 - elbow angle from three points.",
         takeaway="If a four-millimetre wobble is degrees of elbow angle, the same wobble is a "
                  "large slice of a five-centimetre compression. That is the depth argument, "
                  "in numbers.",
         next_q="A four-millimetre wobble cost us degrees of angle, which is why depth has to "
                "come from the pad. **But how do we find where the pushes are in that pad "
                "line at all?**"),

    dict(id="peaks", phase=4, scene="Counting The Pushes", ai="A Hand-Written Peak Finder",
         doing="Turn a continuous wiggly line into one row per push. Nothing else in the app "
               "can happen until this part works.",
         tech="deeper than both neighbours - past a floor - not too close to the last one",
         site=("Every message the unit gives is about one push.",
               "So the code has to find the pushes first.",
               "Fifty readings a second, hundreds of pushes."),
         challenge=("The signal is not smooth. It has hundreds of tiny bumps.",
                    "Most of those bumps are not pushes.",
                    "And one real push can easily get counted twice."),
         ai_link=("Three lines of ordinary code, written out in full.",
                  "A push is deeper than the readings either side.",
                  "Big enough to count, and not too close to the last one.",
                  "No model. No training. No training data."),
         plain="A 'peak finder' walks along the signal and marks every point that is deeper "
               "than the point before it and the point after it. It is ordinary code - there "
               "is no learning and no model anywhere in it.",
         figure="Four seconds of the pad line. Orange triangles pointing down are the pushes "
                "the code found. Purple triangles pointing up are the shallowest point after "
                "each push. The dotted grey line is the floor below which a bump is too small "
                "to count as a push at all.",
         watch="Every orange triangle sits on a peak, and no peak has two - that is the whole "
               "test. Then notice the purple triangles do not reach the top of the chart: the "
               "chest is not coming all the way back up. Hover a triangle to see which push it "
               "is and how deep it went.",
         notebook="Section 4 - counting compressions.",
         takeaway="A peak finder is not machine learning and does not need to be. Reach for "
                  "the simplest thing that answers the question.",
         next_q="We now have a depth for every push. But look at those purple triangles again "
                "- the chest is not returning to the top. **Is 'how deep it got' really the "
                "same thing as 'how far it travelled'?**"),

    dict(id="release", phase=4, scene="The Number Between The Peaks", ai="Depth Versus Travel",
         doing="Build a better column out of the raw ones. This single extra number is what "
               "makes four later pages possible.",
         tech="travel = how deep it got, minus what it never came back up from",
         site=("After each push we note how far back up the chest gets.",
               "If the helper is leaning, it never gets all the way.",
               "That number should be almost zero."),
         challenge=("A chest held down cannot refill with blood.",
                    "But the depth reading still looks fine.",
                    "So the fault hides behind the obvious number."),
         ai_link=("Keep two numbers per push instead of one.",
                  "How deep it went, and how far it really moved.",
                  "They match only when the helper lets go properly."),
         plain="'Letting the chest come back up' between pushes is what lets the heart refill. "
               "It sounds like a detail. It is the difference between blood moving and blood "
               "not moving.",
         figure="One dot per push across the whole rescue. Blue is how deep the chest got. "
                "Orange is how far it actually travelled. The green band is the right depth.",
         watch="The two colours start on top of each other and pull apart as helper A tires - "
               "blue stays inside the green band while orange drops out of it. That growing "
               "gap is the fault nobody can feel. Hover any dot to read both numbers for that "
               "push.",
         notebook="Section 4.1 - full release, and the two columns.",
         takeaway="This one extra column is what makes the next four pages work. Without it, "
                  "the fatigue page has nothing to detect.",
         next_q="We can now measure every push properly. **So what should the unit actually "
                "say out loud?** Eight things can be wrong at once, and a frightened person "
                "can only act on one of them."),

    dict(id="rules", phase=5, scene="One Message At A Time", ai="The Feedback Rules",
         doing="Turn measurements into something to say. This is the point where a model "
               "would normally be trained - and here, deliberately, none is.",
         tech="nine rules, ordered by cost to the patient, first one wins",
         site=("Eight things can go wrong: hands off centre, too shallow, too deep, leaning.",
               "Too slow, too fast, bent arms, shoulders too far back.",
               "Or nothing is wrong, and the light turns green."),
         challenge=("Give a frightened person four instructions and they follow none of them.",
                    "Say everything and you have said nothing.",
                    "So the unit gets one sentence at a time."),
         ai_link=("Put the eight faults in order of what each one costs the patient.",
                  "Say the first one on the list that is true. Ignore the rest.",
                  "Depth and letting go move blood. A bent arm only tires the helper."),
         plain="A 'rule engine' is a checklist tried in a fixed order, where the first match "
               "wins and the rest are ignored. Nothing here is learned from data: a person "
               "decided both the rules and the order they are tried in.",
         figure="Two charts. The first counts how often the unit chose each sentence across "
                "the whole rescue. The second counts the three lights, for each helper "
                "separately.",
         watch="The two helpers end up with a similar number of green lights while the "
               "sentences they were given are completely different - A is told to release, B "
               "is told to speed up. Hover any bar to read the exact count.",
         notebook="Section 5 - from measurement to feedback.",
         takeaway="The priority order is the design. Change it and you change what the unit is "
                  "for, without touching a single threshold.",
         next_q="Telling somebody 'faster' works for about three pushes and then they drift "
                "back to where they were. **What would actually hold their speed steady?**"),

    dict(id="metronome", phase=5, scene="A Beat To Follow", ai="The Metronome",
         doing="Replace an instruction with something a person can follow without thinking - "
               "then look at the trap hiding in the obvious version of it.",
         tech="start where the helper is, then walk the beat towards the target",
         site=("Tell someone to speed up and they do, for about three pushes.",
               "Give them a beat and they follow it without thinking.",
               "There is nothing to remember."),
         challenge=("A beat that starts at the target is too far away to catch.",
                    "A beat that slows down to match them is no use at all.",
                    "It has to lead, and still stay within reach."),
         ai_link=("Start the beat near the helper's own speed.",
                  "Then move it slowly to where it should be.",
                  "And never let it follow them back down."),
         plain="A 'metronome' is the steady click musicians practise to. Ours is adaptive: it "
               "starts where the helper already is, and walks them to where they should be.",
         figure="The helper's actual speed in blue, and the beat the unit is playing in "
                "orange, across the whole rescue. The green band is the safe range of 100 to "
                "120 pushes a minute.",
         watch="Watch helper B just after the changeover: blue starts well below the green "
               "band, orange starts near them rather than at the target, and then blue follows "
               "orange up into the band. Hover any point to compare the beat and the helper at "
               "that second.",
         notebook="Section 5.1 - the metronome.",
         takeaway="The beat leads and the helper follows. Any version that chases the helper "
                  "is a mirror, not a metronome.",
         next_q="The unit can now correct one push at a time. But helper A is getting worse "
                "slowly, over a whole minute. **Can a system that only ever looks at the "
                "current push notice that?**"),

    dict(id="fatigue", phase=6, scene="The Helper Who Cannot Feel It", ai="Detecting A Trend",
         doing="Test two ways of catching the same fault, and keep the one that failed right "
               "there on the page so you can see why it failed.",
         tech="the travel, against this helper's own first twenty pushes",
         site=("Helper A has been pushing for a minute.",
               "Shallower, faster, leaning more weight on the chest.",
               "They cannot feel any of it."),
         challenge=("The obvious check watches the depth drop. The depth barely drops.",
                    "They stop letting go, so each push starts from further down.",
                    "The chest still reaches the right place, on much less work."),
         ai_link=("Watch how far the chest moves instead.",
                  "Compare it with this helper's own first twenty pushes.",
                  "Not with a fixed number that fits nobody."),
         plain="A 'trend' is the direction a number is moving over time, rather than its value "
               "right now. Somebody tiring looks fine on any single push and clearly worse "
               "across fifty of them.",
         figure="The same fatigue, with two detectors side by side. The left panel watches how "
                "deep the chest got. The right panel watches how far it travelled. The orange "
                "dashed line marks where each detector first raised the alarm.",
         watch="The left line barely dips and often says 'never fired'; the right line falls "
               "clearly and catches it with most of the shift still to run. The failed "
               "detector is kept here on purpose. Hover either line to read the running "
               "average at that second.",
         notebook="Section 6.1 - is the helper tiring, and the detector that failed first.",
         takeaway="An absolute threshold fires instantly for a small helper and never for a "
                  "strong one. Everybody's baseline is their own.",
         next_q="The unit knows helper A is fading, and the obvious fix is to swap in "
                "somebody fresh. But a swap means a pause, with nobody pushing at all. "
                "**Before we call one: how much does a pause actually cost?**"),

    dict(id="handsoff", phase=6, scene="Hands Off The Chest", ai="Compression Fraction",
         doing="Score the whole session on the one number most strongly tied to whether the "
               "patient lives.",
         tech="the share of the whole rescue that somebody was actually pushing",
         site=("Add up every second nobody was pushing.",
               "The helper arriving, the defibrillator, the changeover.",
               "And the pause while somebody fetches something."),
         challenge=("Pauses feel short from the inside.",
                    "They are never as short as they feel.",
                    "And nobody in the room is counting."),
         ai_link=("Work the share out from the signal on its own.",
                  "Nobody hands the code a list of the pauses.",
                  "Because nobody would hand the real unit one either."),
         plain="'Compression fraction' is simply the share of the whole emergency during which "
               "somebody was actually pushing. Every second nobody is pushing, blood is not "
               "moving.",
         figure="The whole rescue drawn as one long bar. Green is somebody pushing. Red is "
                "nobody pushing.",
         watch="There are three red stretches - the helper arriving, the defibrillator, and "
               "the changeover - and together they are the entire reason the score is not "
               "100%. Hover any block to read exactly when it started and how long it lasted.",
         notebook="Section 6.3 - hands-off time.",
         takeaway="This is the single number most strongly tied to whether the patient lives. "
                  "Guidelines want at least sixty percent.",
         next_q="So a pause is expensive, and we can now put a number on one. **Is it worth "
                "stopping to swap helpers at all** - and if it is, when?"),

    dict(id="switch", phase=7, scene="Time To Swap", ai="The Switch Plan",
         doing="Turn a detection into an instruction - and work out what that instruction "
               "costs before issuing it.",
         tech="whichever comes first: two minutes, or quality falling",
         site=("The advice is to swap helpers every two minutes.",
               "Quality drops long before anyone feels tired.",
               "So the clock matters as much as how they feel."),
         challenge=("A messy swap costs ten seconds with nobody pushing.",
                    "Every one of those seconds is blood not moving.",
                    "So the swap has to be set up before it is called."),
         ai_link=("Tell the second person to get into position fifteen seconds early.",
                  "Call the swap on whichever comes first: the clock, or the fading.",
                  "If there is nobody else in the room, say something completely different."),
         plain="'Swapping helpers' means handing the pushing over to a second person before "
               "the first one fades, rather than after. The cost is a pause, so when to call "
               "it is a genuine trade-off.",
         notebook="Section 6.2 - calling the switch.",
         takeaway="If the helper is alone, the correct output is keep going, do not stop. "
                  "Telling somebody to swap with nobody only tells them they are failing.",
         next_q="The unit works to keep every pause as short as it can. There is exactly "
                "one pause it is not allowed to shorten. **Whose decision is a shock - and "
                "what may the unit say while it happens?**"),

    dict(id="aed", phase=7, scene="The One Decision The AI Must Not Make",
         ai="Coaching Around The Defibrillator",
         doing="Draw the line around what this system is allowed to decide, and show that the "
               "code has no way of crossing it.",
         tech="four states, and no branch that decides anything about a shock",
         site=("While the defibrillator works, nobody may touch the patient.",
               "The second it finishes, hands go straight back on.",
               "Somebody has to say both of those out loud."),
         challenge=("The seconds after a shock are where rescues are lost.",
                    "A frightened helper waits to be told it is safe to touch them.",
                    "Nobody in the room tells them."),
         ai_link=("Watch what the defibrillator is doing and work around it.",
                  "Keep everybody's hands off while it works.",
                  "Then say 'start pushing' louder than anything else."),
         plain="A 'defibrillator' - often written AED, for automated external defibrillator - "
               "is the box that reads the heart's rhythm and decides on its own whether an "
               "electric shock will help. It makes that decision. Our unit only says when to "
               "stand back, and when to start pushing again.",
         figure="The same rescue bar from the hands-off page. The second red block is the "
                "pause the defibrillator costs, priced in seconds.",
         watch="That block is about twelve seconds long, and it is the one pause on the chart "
               "the unit is not allowed to shorten - all it can do is make sure pushing "
               "restarts the instant it ends. Hover the block to read its exact length.",
         notebook="Section 6.4 - the AED, and the decision the AI must not make.",
         takeaway="Whether to shock belongs to a regulated defibrillator. This state machine "
                  "has no branch that could grow into that decision, and must never be given "
                  "one.",
         next_q="The emergency is over and the ambulance crew is walking in. They have about "
                "five seconds of attention. **What do you show them?**"),

    dict(id="timeline", phase=8, scene="The Picture The Paramedic Gets",
         ai="The Quality Timeline",
         doing="Put everything measured onto one shared clock, so three and a half minutes can "
               "be handed over in about five seconds.",
         tech="depth, speed, lean, posture and the light bar on one time axis",
         site=("The ambulance crew arrives.",
               "Somebody has to explain three and a half minutes.",
               "They have about five seconds to do it."),
         challenge=("An average hides everything.",
                    "Both helpers score about the same overall.",
                    "They went wrong in completely different ways."),
         ai_link=("Put every measurement on one shared clock.",
                  "Colour each push by what the unit said about it.",
                  "Summarise nothing away."),
         plain="A 'handover' is the moment the ambulance crew takes charge. Everything on this "
               "page exists so their questions can be answered by pointing at something, "
               "rather than from memory.",
         figure="Five stacked panels sharing one clock: how deep each push went, the speed "
                "against the beat, how far the helper is leaning with the travel on its own "
                "axis, the elbow angle, and a colour bar of what the unit said.",
         watch="Compare the first half with the second: helper A's lean panel climbs steadily "
               "while B's stays flat, and B's speed panel starts below the green band. Same "
               "overall score, opposite failures. Hover anywhere to read every measurement at "
               "that second.",
         notebook="Section 7 - the CPR quality timeline.",
         takeaway="The same picture is a handover on arrival and a debrief afterwards. Neither "
                  "is possible from a mean.",
         next_q="Everything so far has worked. **Now the hard question: what would this get "
                "wrong in a real room?** The next page is the one a demo usually leaves out."),

    dict(id="limits", phase=9, scene="What This Would Get Wrong", ai="The Honest List",
         doing="Write down what the system genuinely cannot do. The dangerous version of this "
               "app is the one without this page.",
         tech="invented data - a fragile camera - thresholds that are not people",
         site=("A device that coaches a frightened stranger deserves a hard look.",
               "Every number here was invented by code.",
               "The person who wrote that code already knew what it should find."),
         challenge=("Real helpers go wrong in ways nobody thought to invent.",
                    "Real rooms have bad light, bad angles, people walking through.",
                    "None of that is in here."),
         ai_link=("List what would break, worst first.",
                  "Be exact enough that somebody could go and test each one.",
                  "Two of them are dials in the sidebar, so you can break it yourself."),
         plain="A 'limitation' is something the system genuinely cannot do, written down "
               "honestly rather than hidden. Every real project has a page like this, and the "
               "ones that skip it are the ones to worry about.",
         figure="How often the unit chose each sentence, at whatever the sidebar is set to "
                "right now.",
         watch="Switch the patient to a child, or slide the pad, and watch this chart fill up "
               "with 'press deeper' - the unit has no idea anything has changed and keeps "
               "confidently correcting a helper who is doing it right. Hover any bar to read "
               "the count.",
         notebook="Section 8 - what this would get wrong, and section 9 - your turn.",
         takeaway="Being told you are getting it wrong has a cost. Sometimes the most "
                  "useful thing the unit can say is keep going, help is on its way."),
]

# --------------------------------------------------- what the project is worth
# Shown as a dashboard at the foot of the landing page. Each row is something
# the unit adds that a bystander standing alone does not have, paired with what
# actually happens without it. Nothing here is a claim about a real device: it
# is what this build measures, on this simulated session.
ADVANTAGES = [
    dict(name="Every push is counted",
         without="A helper counts nothing. Anyone reviewing it afterwards has an impression "
                 "of how it went, not a record.",
         with_unit="One row per push, carrying depth, travel, speed and posture - so the "
                   "200th push can be compared with the 20th."),
    dict(name="Fading is caught while it can still be fixed",
         without="Quality falls for a minute or more before anybody feels tired, and the "
                 "person doing it is the last to know.",
         with_unit="The travel detector raises it partway through the shift, measured against "
                   "that helper's own opening pushes rather than a fixed number."),
    dict(name="One instruction at a time",
         without="A bystander is shouted at by several people at once, or by nobody at all.",
         with_unit="Eight possible faults, ranked by cost to the patient, and only the first "
                   "one is ever spoken."),
    dict(name="Speed is set by a beat, not a word",
         without="'Faster' works for about three pushes, then the helper drifts back to their "
                 "own natural speed.",
         with_unit="A beat that starts where the helper already is and walks them into the "
                   "safe range, without ever chasing them back down."),
    dict(name="Pauses are visible and priced",
         without="Every pause feels shorter from the inside than it was, and nobody in the "
                 "room is counting seconds.",
         with_unit="Hands-off time found from the signal alone, and turned into one share of "
                   "the whole emergency."),
    dict(name="The handover is a picture, not a memory",
         without="Three and a half minutes summarised from memory by somebody who has just "
                 "had the worst five minutes of their year.",
         with_unit="Every measurement on one clock, with each push coloured by what the unit "
                   "said about it."),
    dict(name="The dangerous decision is walled off",
         without="A design that lets the convenient sensor answer the hard question, or lets "
                 "the coach reason about shocks.",
         with_unit="Depth only ever comes from the pad, and no branch anywhere in the code "
                   "decides anything about a shock."),
]

# ------------------------------------------------------- what one push produces
# story.compression_table() emits one row per compression, and the column names
# on that row are the app's real vocabulary: `residual_cm`, `stroke_cm`,
# `hand_cm`. They are shown to students as bare dataframe headers, which teaches
# nobody anything, so each is named here in three parts - the column, what it
# actually is, and what the coach DOES with it.
# The pad and the camera both report 50 times a second.
MEASURE_GROUPS = [
    dict(name="Which push, and when",
         idea="Bookkeeping: enough to put every push in order and attribute it to a person.",
         plan="Never coached on. It is what lets every later chart show change over time "
              "instead of one average that hides everything.",
         rows=[
             ("n", "Which compression this is, counting from 1.",
              "Lets us say 'the 200th push was weaker than the 20th'."),
             ("t", "How many seconds into the emergency this push happened.",
              "The x-axis of every timeline, and how a pause becomes visible."),
             ("rescuer", "Which of the two helpers was pushing, A or B.",
              "Fatigue is per person, so nothing about tiring works without this."),
         ]),
    dict(name="How far the chest moved",
         idea="Three numbers from the same push: the bottom, the top, and the distance between.",
         plan="The heart of the whole app. Depth alone looks fine while the chest is never "
              "allowed back up, and the gap between depth and travel is what exposes that.",
         rows=[
             ("depth_cm", "How far down the chest got at the bottom of the push.",
              "Compared against the 5-6 cm guideline: too little moves no blood, too much injures."),
             ("residual_cm", "How far down the chest still is at the top of the release.",
              "Should be near zero. Anything above 0.5 cm means the chest never came back up."),
             ("stroke_cm", "Depth minus residual - how far the chest actually travelled.",
              "The honest measure of work done. It is the number that falls first as a helper tires."),
         ]),
    dict(name="How fast",
         idea="The gap to the next push, turned into pushes per minute.",
         plan="Drives the beat. Note it is measured from the gap, so the last push before a "
              "pause has no speed at all rather than a very slow one.",
         rows=[
             ("rate_cpm", "Pushes per minute, worked out from the gap to the next push.",
              "Kept between 100 and 120: slower moves too little blood, faster gets shallower."),
         ]),
    dict(name="What the body is doing",
         idea="Three positions read off the camera's dots at the moment of the push.",
         plan="These change how long the helper lasts rather than how good one push is - "
              "which is exactly why they rank below depth in the coaching order.",
         rows=[
             ("elbow_deg", "The angle at the elbow; 180 degrees is a straight arm.",
              "Bent arms mean the arms are doing work the body weight should do, so the helper tires."),
             ("shoulder_cm", "How far the shoulders sit behind the hands.",
              "Being over the hands is what lets body weight, not muscle, do the pushing."),
             ("hand_cm", "How far the hands are from the centre of the breastbone.",
              "The one position fault ranked top: off-centre, the push lands on ribs."),
         ]),
]

MEASURE_COUNT = sum(len(g["rows"]) for g in MEASURE_GROUPS)

# Friendly headers for the one dataframe that shows raw column names to students.
MEASURE_LABELS = {
    "depth_cm": "Depth (cm)",
    "stroke_cm": "Actual travel (cm)",
    "residual_cm": "Still pressed in (cm)",
    "rate_cpm": "Speed (per min)",
    "elbow_deg": "Elbow angle (deg)",
}

# Hover text for every column heading a student can meet in a table. Streamlit
# renders these as a tooltip on the column header, so a reader who does not know
# what 'Full recoil' means can find out without leaving the page.
COLUMN_HELP = {
    # the per-helper averages on the release page
    "Depth (cm)": "How far down the chest got at the bottom of the push, averaged over every "
                  "push this helper made.",
    "Actual travel (cm)": "How far the chest really moved: the depth, minus how far down it "
                          "still was at the top of the release.",
    "Still pressed in (cm)": "How far down the chest still is between pushes. Should be near "
                             "zero; anything above half a centimetre means the helper is "
                             "leaning on the chest.",
    "Speed (per min)": "Pushes per minute, worked out from the gap between one push and the "
                       "next. The guideline range is 100 to 120.",
    "Elbow angle (deg)": "The angle at the elbow, measured from the camera's dots. 180 "
                         "degrees is a completely straight arm.",
    # the session report table
    "Compressions": "How many pushes this helper made in total.",
    "Mean depth (cm)": "Average depth reached, over all of this helper's pushes.",
    "Mean stroke (cm)": "Average distance the chest actually travelled. Lower than the depth "
                        "whenever the helper is leaning on the chest.",
    "In-range depth": "The share of this helper's pushes that landed inside the guideline "
                      "depth band.",
    "Mean rate": "Average pushes per minute.",
    "In-range rate": "The share of pushes made at a speed inside the guideline range of 100 "
                     "to 120 a minute.",
    "Full recoil": "The share of pushes where the chest was allowed all the way back up "
                   "before the next one started.",
    "Green": "The share of pushes the unit was completely happy with - no correction spoken.",
    # the fatigue table
    "Peak depth fell (cm)": "How much shallower this helper's last twenty pushes were than "
                            "their first twenty. The detector that does not work watches this.",
    "Stroke fell (cm)": "How much less the chest travelled on the last twenty pushes than on "
                        "the first twenty. This is what the working detector watches.",
    "Lean grew (cm)": "How much more of their weight the helper was resting on the chest by "
                      "the end than at the start.",
    "Watching peak depth": "When the detector that watches depth alone first raised the "
                           "alarm - often never.",
    "Watching the stroke": "When the detector that watches how far the chest travelled first "
                           "raised the alarm.",
}


BY_ID = {s["id"]: s for s in STEPS}
ORDER = [s["id"] for s in STEPS]

# The landing page's phase table, derived rather than written out. It used to be
# a second hand-maintained list, which is exactly how the two spines drifted
# apart in the first place: there is now one place to change a phase.
WORKFLOW = [(f"{i + 1} - {name}", note, [s["id"] for s in STEPS if s["phase"] == i])
            for i, (name, note) in enumerate(PHASES)]

# Contiguity is what makes "PHASE n OF 10" honest. Asserted at import, so a page
# inserted into the wrong phase fails here rather than looking odd in a lesson.
_seen = [s["phase"] for s in STEPS]
assert _seen == sorted(_seen), f"pages are out of phase order: {_seen}"
assert {s["phase"] for s in STEPS} == set(range(len(PHASES))), "a phase has no pages"
