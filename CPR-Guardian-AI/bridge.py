"""The teaching registry: one entry per page, in the order the notebook works.

Every entry keeps the same five parts as the notebook's sections, and the same
plain-English house style: short sentences, everyday words.
  scene     - what is happening in the room, with no AI in it
  challenge - why that is hard for the person doing it
  ai_link   - what the AI is actually being asked to do
  tech      - the one-line technical idea
  notebook  - which notebook section this matches
  takeaway  - one sentence to remember

No computed figure is quoted in this prose. Every number on a page is worked
out by that page, so the two can never drift apart.
"""

PHASES = [
    ("The First Four Minutes", "Somebody has collapsed and nobody here is trained."),
    ("Which Sensor Answers What", "The split the whole design is built on."),
    ("Reading The Compressions", "Finding the pushes, then measuring them."),
    ("What The Unit Says", "One message at a time, and a beat to follow."),
    ("The Whole Session", "Tiring, swapping, hands-off time, and the AED."),
    ("The Handover", "The picture a paramedic gets, and what it would get wrong."),
]

STEPS = [
    dict(id="collapse", phase=0, scene="Nobody Here Is Trained", ai="The Real Problem",
         tech="a wall unit with a camera, a pad, a speaker, an AED and three lights",
         site="Someone collapses in a station concourse. A stranger kneels down, phone in one "
              "hand, and pulls a unit off the wall. They have never done this before.",
         challenge="Ambulances take minutes. Whatever happens in those minutes happens because a "
                   "frightened bystander did it, and they have no way of knowing whether what "
                   "they are doing is working.",
         ai_link="The unit is not diagnosing anybody. It is watching one person's technique and "
                 "telling them the single most useful thing to change right now.",
         notebook="The opening - what the unit is and what the four minutes are for.",
         takeaway="Mediocre compressions are enormously better than none. The job is to nudge "
                  "them upward without stopping them."),

    dict(id="sensors", phase=1, scene="Camera, Pad Or AED?", ai="The Sensor Split",
         tech="camera for posture · pad for depth and rate and recoil · AED for rhythm",
         site="The obvious design is to point a camera at the helper and measure everything from "
              "the video. That design is wrong, and it is worth being precise about why.",
         challenge="Turning pixels into centimetres of chest travel depends on lens, angle, "
                   "distance, clothing and body size. A twenty percent error there is the "
                   "difference between effective CPR and useless CPR.",
         ai_link="Give each question to the sensor that can actually answer it, and refuse to "
                 "let the convenient sensor answer the hard question.",
         notebook="The framing table at the top of the notebook.",
         takeaway="Most of the engineering in a safe system is deciding what each part is not "
                  "allowed to do."),

    dict(id="rescue", phase=1, scene="Three And A Half Minutes", ai="The Simulated Session",
         tech="two helpers, one AED pause, two different ways of being wrong",
         site="Rescuer A starts well and tires. The AED interrupts for twelve seconds. Rescuer B "
              "takes over fresh, and starts far too slow.",
         challenge="Real training data comes from a mannequin in a classroom, where nobody is "
                   "frightened and nothing goes wrong by surprise.",
         ai_link="Generate the session instead, so every problem the unit must catch is present "
                 "on purpose and we know the right answer for each one.",
         notebook="Section 2 - simulating the rescue.",
         takeaway="A degrades gradually, which is hard to notice from inside. B is wrong "
                  "immediately, which is easy to fix once somebody says so."),

    dict(id="pad", phase=1, scene="What The Pad Feels", ai="The Depth Signal",
         tech="fifty samples a second of how far the chest is pressed in",
         site="One compression is one push and one release. The pad reports the depth of the "
              "chest continuously, so a compression is a bump in a line.",
         challenge="At the scale of the whole rescue every compression is a single vertical "
                   "stroke and nothing can be read from it at all.",
         ai_link="Zoom in on five seconds and the three failures become visible: lower peaks, "
                 "closer together, and troughs that no longer come back to the floor.",
         notebook="Section 2.1 - the pad signal.",
         takeaway="Nothing in this signal is subtle once you look at the right timescale. The "
                  "helper simply cannot see it while they are doing it."),

    dict(id="camera", phase=1, scene="What The Camera Sees", ai="Pose Keypoints",
         tech="wrist, elbow, shoulder as coordinates in centimetres",
         site="A pose model returns points. Everything the camera contributes is arithmetic on "
              "the positions of three of them.",
         challenge="A camera cannot tell whether the chest went down five centimetres. It can "
                   "tell perfectly well whether the arms are straight and the shoulders are over "
                   "the hands.",
         ai_link="Keep the camera on the questions it is good at, and let the answers steer the "
                 "helper's body rather than measure the patient's chest.",
         notebook="Section 3 - what the camera sees.",
         takeaway="Straight arms mean body weight is doing the work. Bent arms mean the helper "
                  "is, and they will not last two minutes."),

    dict(id="elbow", phase=1, scene="The Angle At The Elbow", ai="Geometry, And Jitter",
         tech="the angle between elbow-to-shoulder and elbow-to-wrist",
         site="Three points, one angle. Straight arms come out close to 180 degrees.",
         challenge="The three points sit almost on a straight line, so a few millimetres of "
                   "keypoint wobble swings the measured angle a long way.",
         ai_link="Average over about half a second. It costs a little lag and buys back most of "
                 "the accuracy.",
         notebook="Section 3.1 - elbow angle from three points.",
         takeaway="If a four-millimetre wobble is degrees of elbow angle, the same wobble is a "
                  "large slice of a five-centimetre compression. That is the depth argument, in "
                  "numbers."),

    dict(id="peaks", phase=2, scene="Counting The Pushes", ai="A Hand-Written Peak Finder",
         tech="deeper than both neighbours · past a floor · not too close to the last one",
         site="Everything the unit says is per compression, so before it can say anything it has "
              "to find them.",
         challenge="Pad noise creates hundreds of tiny local maxima, and two candidates a few "
                   "hundredths of a second apart are the same push counted twice.",
         ai_link="Three lines of rule, written out rather than imported, because seeing how "
                 "compressions get counted is half the lesson.",
         notebook="Section 4 - counting compressions.",
         takeaway="A peak finder is not machine learning and does not need to be. Reach for the "
                  "simplest thing that answers the question."),

    dict(id="release", phase=2, scene="The Number Between The Peaks", ai="Depth Versus Stroke",
         tech="stroke = how deep it got, minus what it never came back up from",
         site="For every compression the unit also records the shallowest point before the next "
              "one - the depth the helper is still leaning on.",
         challenge="A chest that never comes back up cannot refill with blood, and the depth "
                   "number on its own looks completely fine while that is happening.",
         ai_link="Record two numbers per push instead of one. They are equal only when the "
                 "helper releases fully.",
         notebook="Section 4.1 - full release, and the two columns.",
         takeaway="This one extra column is what makes the next four pages work. Without it, the "
                  "fatigue page has nothing to detect."),

    dict(id="rules", phase=3, scene="One Message At A Time", ai="The Feedback Rules",
         tech="nine rules, ordered by cost to the patient, first one wins",
         site="Hands off centre, too shallow, too deep, leaning, too slow, too fast, bent elbows, "
              "shoulders behind the hands - or a green light.",
         challenge="A frightened untrained helper given four instructions at once follows none "
                   "of them.",
         ai_link="Order the rules by how much each fault costs the patient, and speak only the "
                 "first one that fires. Depth and recoil move blood; a bent elbow only makes the "
                 "helper tire sooner.",
         notebook="Section 5 - from measurement to feedback.",
         takeaway="The priority order is the design. Change it and you change what the unit is "
                  "for, without touching a single threshold."),

    dict(id="metronome", phase=3, scene="A Beat To Follow", ai="The Metronome",
         tech="start where the helper is, then walk the beat towards the target",
         site="Told to press faster, a person speeds up briefly and drifts back. Given a beat, "
              "they lock onto it.",
         challenge="A beat that jumps straight to the target is one the helper loses, and a beat "
                   "that follows the helper down out of range is not a reference at all.",
         ai_link="Meet them where they are on the first beat, then move steadily towards the "
                 "middle of the range and never back down out of it.",
         notebook="Section 5.1 - the metronome.",
         takeaway="The beat leads and the helper follows. Any version that chases the helper is "
                  "a mirror, not a metronome."),

    dict(id="fatigue", phase=4, scene="The Helper Who Cannot Feel It", ai="Detecting A Trend",
         tech="the stroke, against this helper's own first twenty compressions",
         site="Rescuer A has been going for a minute. They are pressing shallower, drifting "
              "faster, and starting to rest their weight on the chest between pushes.",
         challenge="The obvious detector watches depth falling - and depth barely moves. As the "
                   "helper stops coming all the way up, each push starts from lower down, so the "
                   "chest still reaches roughly the right depth while doing less and less work.",
         ai_link="Detect on the stroke instead, and compare it against this helper's own opening "
                 "compressions rather than an absolute number.",
         notebook="Section 6.1 - is the helper tiring, and the detector that failed first.",
         takeaway="An absolute threshold fires instantly for a small helper and never for a "
                  "strong one. Everybody's baseline is their own."),

    dict(id="switch", phase=4, scene="Time To Swap", ai="The Switch Plan",
         tech="whichever comes first: two minutes, or quality falling",
         site="Guidelines say swap about every two minutes, because quality falls long before "
              "the helper feels tired.",
         challenge="A swap done badly costs ten seconds with nobody's hands on the chest, and "
                   "every one of those seconds is blood not moving.",
         ai_link="Warn the standby person fifteen seconds early so they are already in position, "
                 "and call the swap on whichever trigger arrives first.",
         notebook="Section 6.2 - calling the switch.",
         takeaway="If the helper is alone, the correct output is keep going, do not stop. Telling "
                  "somebody to swap with nobody only tells them they are failing."),

    dict(id="handsoff", phase=4, scene="Hands Off The Chest", ai="Chest Compression Fraction",
         tech="the share of the whole rescue that somebody was actually compressing",
         site="Add up every second nobody's hands were on the chest: the arrival, the AED, the "
              "swap, the pause while somebody fetches something.",
         challenge="Pauses feel short from inside and are never as short as they feel.",
         ai_link="Measure the fraction from the signal itself, without being told where the "
                 "pauses were - because the real unit is not told.",
         notebook="Section 6.3 - hands-off time.",
         takeaway="This is the single number most strongly tied to whether the patient lives. "
                  "Guidelines want at least sixty percent."),

    dict(id="aed", phase=4, scene="The One Decision The AI Must Not Make", ai="Coaching Around The AED",
         tech="four states, and no branch that decides anything about a shock",
         site="While the AED analyses and delivers a shock, nobody may touch the patient. Then "
              "hands go straight back on.",
         challenge="Every extra second after a shock before compressions restart is where "
                   "rescues are lost, and a stunned helper waits for permission.",
         ai_link="Read the AED's state and coach around it. Enforce stand-clear, then say resume "
                 "louder than anything else the unit ever says.",
         notebook="Section 6.4 - the AED, and the decision the AI must not make.",
         takeaway="Whether to shock belongs to a regulated AED. This state machine has no branch "
                  "that could grow into that decision, and must never be given one."),

    dict(id="timeline", phase=5, scene="The Picture The Paramedic Gets", ai="The Quality Timeline",
         tech="depth, rate, lean, posture and the light bar on one time axis",
         site="The crew arrives. Somebody has to hand over what has been happening for the last "
              "three and a half minutes, and they have about five seconds to do it.",
         challenge="Session averages hide everything. Both rescuers here score about the same "
                   "overall while failing in completely different ways.",
         ai_link="Put every measurement on one shared clock, and colour each compression by what "
                 "the unit said about it.",
         notebook="Section 7 - the CPR quality timeline.",
         takeaway="The same picture is a handover on arrival and a debrief afterwards. Neither "
                  "is possible from a mean."),

    dict(id="limits", phase=5, scene="What This Would Get Wrong", ai="The Honest List",
         tech="invented data · a fragile camera · thresholds that are not people",
         site="A device that coaches a frightened stranger through the worst minutes of their "
              "life earns a harder look than a demo usually gets.",
         challenge="Everything on these pages came from a generator written by somebody who "
                   "already knew what the analysis should find.",
         ai_link="Say what would break, in order, and be specific enough that somebody could "
                 "test each one.",
         notebook="Section 8 - what this would get wrong, and section 9 - your turn.",
         takeaway="Being told you are failing has a cost. Sometimes the output with the highest "
                  "survival value is keep going, help is coming."),
]

BY_ID = {s["id"]: s for s in STEPS}
ORDER = [s["id"] for s in STEPS]
