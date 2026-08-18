"""The teaching registry: one entry per page, in the order the notebook works.

Every entry keeps the same five parts as the notebook's sections, and the same
plain-English house style: short sentences, everyday words, an explanation next
to anything a beginner would not already know.
  scene     - what is happening on the road, with no AI in it
  challenge - why that is hard for people
  ai_link   - what the AI is actually being asked to do
  tech      - the one-line technical idea
  plain     - the technical name in everyday words, for a first-time reader
  notebook  - which notebook section this matches
  takeaway  - one sentence to remember

'plain' exists because every page heading carries a term of art - "state
machine", "random forest", "1D CNN", "Dijkstra". A student meeting those for
the first time should never have to guess, so each page says what its own
jargon means before it uses it.
"""

PHASES = [
    ("A Junction At 8:42 p.m.", "Everything that matters happens in the first few minutes."),
    ("What The Camera Can See", "Boxes and tracks, and nothing more than that."),
    ("Rules People Write", "One frame, and then a timer."),
    ("Models That Learn", "Six seconds of history, and how long to wait."),
    ("Calling For Help", "The packet, the danger map, and the way in."),
    ("The Screen", "One instruction at a time, and only approved ones."),
    ("Did It Help?", "And the lines it must never cross."),
]

STEPS = [
    dict(id="golden", phase=0, scene="The Golden Minutes", ai="Why Seconds Are The Problem",
         tech="an ambulance takes 8-12 minutes · a blocked airway takes 4",
         site="A motorcycle goes down at a junction. Twenty people see it. The first call to "
              "112 is made two minutes later, by someone who is not sure where they are.",
         challenge="Nobody is in charge. Everyone assumes somebody else has called. The people "
                   "closest to the rider are the least likely to have training.",
         ai_link="The camera on the pole already saw it. The only question is whether it does "
                 "anything with what it saw.",
         plain="The 'golden minutes' are the first few minutes after an injury, when what a bystander "
               "does matters more than anything that happens later in hospital.",
         notebook="Section 1 - the golden minutes.",
         takeaway="The camera is already there. Everything in this project is about the "
                  "minutes before the ambulance arrives."),

    dict(id="camera", phase=1, scene="What The Camera Actually Sees", ai="Boxes, Tracks, Signals",
         tech="a box per object, an id that follows it, five frames a second",
         site="The camera does not see a crash. It sees rectangles: car, motorcycle, person, "
              "bus. A tracker gives each one a number and keeps it from frame to frame.",
         challenge="A posture guessed from the shape of a box is wrong now and then. A person "
                   "behind a van does not exist at all. Nothing about this is certain.",
         ai_link="Everything downstream is built on ten numbers per frame: who is on the road, "
                 "who is lying down, how close two tracks came, how fast traffic is moving.",
         plain="A 'box' is the rectangle a detector draws around something it recognises. A 'track' is "
               "an id number that stays with that box as it moves, so the system knows it is the same "
               "motorcycle a second later.",
         notebook="Sections 2 and 3 - the camera, and the virtual junction.",
         takeaway="Build the whole system on what a box can honestly tell you, and no more."),

    dict(id="lookalike", phase=1, scene="Five Ways To Lie In A Road", ai="Why One Frame Cannot Decide",
         tech="a still picture has no past, and a crash is a change",
         site="Somebody is lying near the kerb. They might be hurt. They might be tying a lace, "
              "working under a van, or be a fallen advertising board.",
         challenge="In a single photograph these are the same picture. A person who has been "
                   "there for two minutes looks exactly like one who arrived two seconds ago.",
         ai_link="This is the argument for time. The question is never 'what is in this frame', "
                 "it is 'what changed, and in what order'.",
         plain="'One frame' means a single still picture, five of which arrive every second. The point "
               "of this page is that a still picture has no past, and a crash is entirely about what "
               "changed.",
         notebook="Section 4 - five ways to be lying in a road.",
         takeaway="A crash is not a shape. It is a sequence."),

    dict(id="clues", phase=1, scene="Clues That Only Exist In Time", ai="Feature Engineering",
         tech="seconds lying still · crowd growth · did the traffic start moving again",
         site="A person watching the screen would not describe boxes. They would say the traffic "
              "stopped and stayed stopped, and people started walking towards one spot.",
         challenge="None of those sentences can be read off one frame. Each needs the last few "
                   "seconds held in memory.",
         ai_link="We build eleven numbers over a six-second window and hand those to the model, "
                 "instead of the raw picture.",
         plain="'Feature engineering' means building better numbers out of the raw ones. The camera "
               "reports what is true right now; we work out what has been true for the last six seconds.",
         notebook="Section 5 - the clues that only exist in time.",
         takeaway="Most of the work in a camera system is deciding what to remember."),

    dict(id="frame_rule", phase=2, scene="The One-Frame Rule", ai="Model 1",
         tech="if a person is lying in the carriageway, raise the alarm",
         site="The simplest system anyone would build, and the one most cameras actually run: "
              "look at this frame, and if somebody is down, call it in.",
         challenge="It calls the control centre for every crouching pedestrian, every mechanic, "
                   "and a fallen board. It never sees a rollover, because nobody is on the road.",
         ai_link="Useful as a floor to measure against, not as a system. Every later model has "
                 "to beat it on both counts, not one.",
         plain="A 'baseline' is the simplest thing that could possibly work, built on purpose so later "
               "models have something honest to beat. It is not meant to be good.",
         notebook="Section 6 - model 1, one frame.",
         takeaway="A rule with no memory is loud about the wrong things and silent about the "
                  "right ones."),

    dict(id="timer_rule", phase=2, scene="The Six-Second Rule", ai="Model 2",
         tech="lying still, in the road, for six seconds · or smoke",
         site="The obvious fix. Do not believe it until it has held for six seconds, and add a "
              "second rule for smoke so the rollover is not missed.",
         challenge="Six seconds is also how long a lace takes to tie. The mechanic never moves "
                   "at all. And the rider who stands up and walks to the kerb never counts as "
                   "an incident, although the lane is blocked and he is in shock.",
         ai_link="A timer buys accuracy with time. It cannot tell two identical pictures apart, "
                 "however long it stares at them.",
         plain="A 'rule-based' model is one a person wrote out as if-this-then-that. Nothing is learned "
               "from data: every number in it was chosen by a human being.",
         notebook="Section 7 - model 2, a timer.",
         takeaway="Waiting longer fixes noise. It does not fix a rule that was asking the "
                  "wrong question."),

    dict(id="forest", phase=3, scene="Learning From Old Clips", ai="Model 3 · Random Forest",
         tech="eleven window features · hundreds of past clips · a probability",
         site="Instead of writing the rule, we show the model a few hundred clips from this "
              "junction and let it work out which combinations mean trouble.",
         challenge="It has to separate a crash from a near miss when the first half second of "
                   "both is identical, and from a red light, which stops the traffic just as hard.",
         ai_link="A random forest over the eleven window features. It catches every incident, "
                 "including the rollover with nobody visible and the rider who stands up.",
         plain="A 'random forest' is a crowd of simple yes/no flowcharts, each shown a different slice "
               "of the old clips. They vote, and the share of votes becomes the probability.",
         notebook="Section 8 - model 3, a forest over a window.",
         takeaway="Give a model the right few seconds of history and it beats every rule we "
                  "wrote by hand."),

    dict(id="sequence", phase=3, scene="Reading The Whole Six Seconds", ai="Model 4 · A 1D CNN",
         tech="thirty frames x ten signals, straight into a small network",
         site="The forest only sees numbers we invented - how long someone has been down, how "
              "much the crowd grew. A network can be handed the raw six seconds instead.",
         challenge="It was told nothing about roads, and it still raises about half as many "
                   "false alarms as the forest. It is also half a second slower every time.",
         ai_link="Neither one wins. The forest is quicker off the mark, the network is calmer. "
                 "The real difference is that nobody had to invent the network's features.",
         plain="A '1D CNN' slides a small pattern-detector along a strip of time, the way you might run "
               "a finger along a line of text. It learns the shapes worth noticing instead of being told "
               "them.",
         notebook="Section 10 - model 4, a sequence network.",
         takeaway="The question is not which model is better. It is which mistake you would "
                  "rather make."),

    dict(id="wait", phase=3, scene="How Long To Wait Before Believing", ai="The Confirmation Dial",
         tech="the alarm must hold for N seconds before anyone is called",
         site="A near miss and a crash look the same at the moment of the bang. Three seconds "
              "later one of them has driven away and the other has a crowd around it.",
         challenge="Every second of waiting is a second of the golden minutes. Every second "
                   "saved is more false calls to a control room that has other work.",
         ai_link="One dial, and the whole system's character is set by it. This page lets you "
                 "move it and watch both costs at once.",
         plain="'Confirmation' means refusing to act on the first sign of something. The dial sets how "
               "many seconds the alarm must stay on before anybody is actually called.",
         notebook="Section 10 - the waiting dial.",
         takeaway="There is no correct setting. There is a choice, and it should be made by "
                  "the people who answer the calls."),

    dict(id="mix", phase=3, scene="Red Lights Outnumber Crashes", ai="The Training Mix",
         tech="what the camera sees all day has to be in the training pile",
         site="A signal turns red every ninety seconds. Traffic stops dead and stays stopped "
              "for twenty seconds. That happens hundreds of times between crashes.",
         challenge="Our first training pile had one red light for every crash. The model "
                   "learned that stopped traffic means a crash, and called the control centre "
                   "at every signal cycle.",
         ai_link="Nothing about the model changed to fix it. The mix of clips changed, to look "
                 "like the road instead of a tidy dataset.",
         plain="The 'training mix' is which examples you put in the pile the model learns from. Get the "
               "proportions wrong and the model learns your pile instead of the road.",
         notebook="Section 11 - why we kept eight red lights for every four crashes.",
         takeaway="A model trained on a balanced pile learns a world that does not exist."),

    dict(id="dispatch", phase=4, scene="The Call That Cannot Wait", ai="The Dispatch Packet",
         tech="location, time, what is visible, a short clip · faces blurred",
         site="The moment the alarm is confirmed, the control centre gets the junction, the "
              "time, how many people are involved, whether there is smoke, and which lanes "
              "are blocked.",
         challenge="Everything useful about a clip is also a privacy problem. Uninvolved faces "
                   "and number plates have no business in a control room recording.",
         ai_link="The AI never waits to be certain before calling. It calls, says what it is "
                 "unsure about, and lets a person decide.",
         plain="A 'packet' is just the bundle of information sent with the call - where, when, how many "
               "people, what is visible. Nothing here is a medical opinion.",
         notebook="Section 12 - the dispatch packet.",
         takeaway="Call first, and be honest about what you cannot see."),

    dict(id="hazards", phase=4, scene="Reading The Danger", ai="The Hazard Map",
         tech="a cost for every square metre: traffic, smoke, fuel, glass, wires",
         site="Before anyone is asked to help, the scene is scored. Live lanes are dangerous. "
              "Smoke and spilled fuel are worse. A fallen cable makes a whole area untouchable.",
         challenge="The most dangerous instruction a screen can give is 'go and help' to "
                   "someone standing on the wrong side of moving traffic.",
         ai_link="A grid of costs, drawn on the screen in red, before a single first-aid word "
                 "is shown.",
         plain="A 'cost map' scores every square metre by how dangerous it is. High cost means keep out, "
               "and the routing step below reads these numbers rather than distances.",
         notebook="Section 13 - the hazard map.",
         takeaway="The first job is not first aid. It is not creating a second casualty."),

    dict(id="path", phase=4, scene="The Safe Way In", ai="Shortest Path By Danger",
         tech="Dijkstra, where the cost is risk rather than distance",
         site="The screen shows one green route from where the helper is standing to where the "
              "rider is lying, and a second route kept clear for the ambulance.",
         challenge="The shortest way is almost always across the live lane. The safe way is "
                   "longer, and has to be shown, not described.",
         ai_link="The same algorithm a map app uses, with danger in place of minutes.",
         plain="'Dijkstra' is the classic shortest-route method a maps app uses. Feed it danger instead "
               "of minutes and 'shortest' turns into 'safest'.",
         notebook="Section 14 - the safe way in.",
         takeaway="Show the route. Nobody follows a paragraph while panicking."),

    dict(id="modules", phase=5, scene="One Instruction At A Time", ai="A State Machine",
         tech="guards checked in a fixed order · every screen is pre-approved",
         site="The screen shows one step. It waits. It checks. Then it shows the next one. "
              "Scene safety always comes before anything else.",
         challenge="A generative model that invents medical instructions under stress is the "
                   "worst possible thing to put on a public screen.",
         ai_link="The AI chooses between approved videos. It does not write them. A dispatcher "
                 "can take the screen at any moment, and that branch is checked first.",
         plain="A 'state machine' is a system that is always in exactly one named step, with fixed rules "
               "for which step may come next. It cannot wander, and it cannot invent a step.",
         notebook="Section 15 - choosing an approved module.",
         takeaway="The AI picks the page. Clinicians wrote the page."),

    dict(id="helper", phase=5, scene="Watching The Helper", ai="Red, Amber, Green",
         tech="approach side · moving the casualty · helmet · crowd · lane",
         site="A camera can honestly see where a helper is standing, whether they are dragging "
              "the rider, whether the helmet is being pulled off, and whether the lane is "
              "blocked.",
         challenge="It cannot see how hard someone is pressing, or how deep a compression is. "
                   "Pixels to centimetres depends on the lens, the angle and the clothing.",
         ai_link="Feedback only on what is visible. Depth and pressure need an instrumented "
                 "mat or pad, not a camera.",
         plain="'Feedback' here means the screen reacting to what the bystander is doing. The hard part "
               "is being honest about which of those things a camera can genuinely see.",
         notebook="Section 16 - watching the helper, and what the camera cannot measure.",
         takeaway="Give feedback only on what you can actually see."),

    dict(id="roles", phase=5, scene="Giving The Crowd Jobs", ai="Assignment",
         tech="nearest able person to each job, most urgent job first",
         site="Twelve people are standing around. One should be talking to the dispatcher, one "
              "warning traffic, one fetching the box, one waving the ambulance in.",
         challenge="A crowd with no instructions crowds. Named jobs turn onlookers into a "
                   "response team, and 'somebody call an ambulance' into 'you, in the red "
                   "jacket, press this button'.",
         ai_link="A small assignment problem on the screen, solved by distance.",
         plain="An 'assignment problem' is the job of matching people to tasks at the lowest total cost. "
               "Ours is small enough to solve by asking who is nearest to what.",
         notebook="Section 17 - giving the crowd jobs.",
         takeaway="Four named jobs beat twenty willing strangers."),

    dict(id="outcome", phase=6, scene="Did It Help?", ai="The Benchmark",
         tech="time to notice · time to call · time to safe help · harmful actions",
         site="The same crash, played four hundred times, with the beacon and without it. Not "
              "survival - the honest measures are time and mistakes.",
         challenge="Improvements that come from assumptions must be labelled as assumptions. "
                   "The delays without a beacon are our estimates, and a student should argue "
                   "with them.",
         ai_link="What the system can honestly claim: the call goes out sooner, the lane clears "
                 "sooner, and fewer people move a rider who should not be moved.",
         plain="A 'benchmark' is running the same situation many times, with and without the system, and "
               "comparing. It measures the change, not whether anybody survived.",
         notebook="Section 18 - did it help.",
         takeaway="Measure the minutes you can change, not the outcomes you cannot."),

    dict(id="limits", phase=6, scene="What It Must Never Do", ai="The Boundaries",
         tech="no diagnosis · no invented procedure · dispatcher above the AI · call first",
         site="A blocked view is a blocked view. Behind a stopped bus the system is three "
              "seconds late at best, and blind at worst.",
         challenge="Every one of these limits is a place where a keen team would be tempted to "
                   "add one more feature.",
         ai_link="It says what it cannot see. It never says what is wrong with a person. It "
                 "never delays the call while it thinks.",
         plain="A 'boundary' is a rule the system is not allowed to cross even when crossing it would "
               "help. These are decided once, in advance, and never at runtime.",
         notebook="Sections 19 and 20 - what it gets wrong, and the rules that do not move.",
         takeaway="A system that knows what it cannot see is safer than one that is usually "
                  "right."),
]

# --------------------------------------------------------------- the 11 clues
# story.WINDOW_FEATURES is a bare list of column names, and "close_max" teaches
# nobody anything. Every feature the forest is given is named here in three
# parts - the column, what it actually is, and what it is FOR.
# The camera runs at 5 frames a second and the window is 6 seconds, so
# "the window" below always means the last 30 frames.
WINDOW_FEATURE_GROUPS = [
    dict(name="Is somebody down, and for how long?",
         idea="The camera's guess at posture, cleaned up and then timed.",
         plan="Turn a flickering yes/no into a stopwatch. A crash is not somebody being down; "
              "it is somebody being down and staying down.",
         rows=[
             ("down_secs", "Seconds somebody has been lying in the road without a break.",
              "The single most important clue, and the one every hand-written rule is built on."),
             ("still_frac", "What share of the last 6 seconds that person did not move at all.",
              "Separates an injured rider from somebody who fell and is already getting up."),
             ("road_frac", "What share of the last 6 seconds a person was inside the carriageway.",
              "Throws away everyone on the pavement, who are not our problem."),
         ]),
    dict(name="What the people around them are doing",
         idea="A headcount near the spot, and how fast that headcount is changing.",
         plan="People walking towards one point is the signal a human watcher would name first, "
              "and it costs nothing to compute.",
         rows=[
             ("crowd", "How many people are standing near the person on the ground, right now.",
              "A crowd forms around a crash; it does not form around a mechanic."),
             ("crowd_growth", "How much that headcount has grown in the last 3 seconds.",
              "A bus queue is large but steady. A crash crowd appears from nothing."),
         ]),
    dict(name="What the traffic is doing",
         idea="How much the traffic has slowed, and how many vehicles have stopped.",
         plan="Deliberately the *change* in flow, never the raw speed. An early version fed in "
              "plain speed and the forest learned 'this clip is slowish, so it is a crash' - a "
              "fact about our clips, not about crashes.",
         rows=[
             ("flow_drop", "How much average traffic speed has fallen over the last 4 seconds.",
              "Traffic stops for a blockage - and for a red light, which is why it cannot decide alone."),
             ("stopped_max", "The most vehicles seen stopped at once during the window.",
              "Confirms the lane is genuinely blocked rather than merely slow."),
         ]),
    dict(name="The moment of the impact itself",
         idea="The most violent thing the tracker saw in the last 6 seconds.",
         plan="These three are what tell a crash from a near miss, which look identical for the "
              "first half second and then diverge completely.",
         rows=[
             ("decel_peak", "The hardest braking seen during the window, in m/s squared.",
              "Emergency braking happens just before a collision, and just before a near miss."),
             ("gap_min", "The smallest gap two road users came to, in metres.",
              "A gap near zero means they touched; a small gap means they nearly did."),
             ("close_max", "The fastest two tracks were closing on each other, in m/s.",
              "How hard the impact would have been - the difference between a scare and an injury."),
         ]),
    dict(name="Fire and debris",
         idea="How much smoke or dust is visible, scored 0 to 1.",
         plan="The one clue that works when nobody is visible at all, which is exactly the case "
              "the person-based rules miss completely.",
         rows=[
             ("smoke_max", "The most smoke or dust seen at any point in the window.",
              "Catches the rollover where the rider is still inside the vehicle."),
         ]),
]

WINDOW_FEATURE_COUNT = sum(len(g["rows"]) for g in WINDOW_FEATURE_GROUPS)


BY_ID = {s["id"]: s for s in STEPS}
ORDER = [s["id"] for s in STEPS]
