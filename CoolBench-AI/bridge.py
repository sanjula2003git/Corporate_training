"""The teaching registry: one entry per page, in the order the notebook works.

Every entry keeps the same five parts as the notebook's sections, and the same
plain-English house style: short sentences, everyday words, an explanation next
to anything a beginner would not already know.
  site      - what is happening at the bench, with no AI in it
  challenge - why that is hard
  ai_link   - what the AI is actually being asked to do
  tech      - the one-line technical idea
  notebook  - which notebook section this matches
  takeaway  - one sentence to remember
"""

PHASES = [
    ("A Bench In The Sun", "What is standing there before any software runs."),
    ("What It Can Feel", "Sensors, and a heat sum that explains the rest."),
    ("One Thing At A Time", "Shade, then air, then water, then ice."),
    ("Everything At Once", "The obvious answer, and why it empties the bench."),
    ("Learning And Choosing", "A forecast, a cost, and a controller built on both."),
    ("Does It Hold Up?", "Different weather, and things that break."),
    ("The Lines", "What the bench must never do."),
]

STEPS = [
    dict(id="bench", phase=0, scene="A Bench With Supplies", ai="The Problem In Two Sentences",
         tech="8 litres of water · 60 Wh of battery · 3 cold packs · one fan",
         site="A bench in a park has a fan, a water mister, a shade cover, cold packs, a "
              "battery and a water tank. Somebody presses the help button because a person "
              "on the ground is overheating.",
         challenge="The supplies are small and the wait is long. Using everything at full "
                   "power empties the bench before help arrives, and leaves no power for the "
                   "radio.",
         ai_link="The bench does not decide that anybody is ill. A person or a dispatcher "
                 "switches it on. Everything the AI does is about spending supplies well.",
         notebook="Section 1 - the bench, and what it is for.",
         takeaway="This is a resource problem wearing a first-aid coat."),

    dict(id="afternoon", phase=0, scene="A Hot Afternoon", ai="Why The Thermometer Lies",
         tech="air 41 °C · ground 48 °C · humidity 32 % · sun 880 W/m²",
         site="The air is 41 °C. The bench surface is 48 °C. The sun is straight overhead "
              "and there is almost no wind.",
         challenge="Two afternoons can both read 41 °C and be completely different. What "
                   "matters is how much heat the air can carry away, and that depends on "
                   "humidity as much as on temperature.",
         ai_link="Every model in this project gets humidity, sun and wind, not just the air "
                 "temperature. It is the single most useful thing we hand it.",
         notebook="Section 2 - a hot afternoon.",
         takeaway="Air temperature alone tells you almost nothing about how fast a person "
                  "can cool down."),

    dict(id="heat", phase=1, scene="Where The Heat Comes From", ai="One Sum, Six Terms",
         tech="body heat + sun + hot ground + hot air − evaporation − cold packs",
         site="A person lying in the sun is being heated from four directions at once, and "
              "cooled from two. Add them up and you know which way the temperature is going.",
         challenge="The biggest single term is the sun, not the air. The second biggest is "
                   "the person's own body heat, which nothing on the bench can switch off.",
         ai_link="This sum is the simulator. It is an educational approximation and it is "
                 "labelled as one everywhere it appears.",
         notebook="Section 3 - the heat balance.",
         takeaway="Shade removes the largest term for almost no energy. Start there."),

    dict(id="sensors", phase=1, scene="What The Bench Can Measure", ai="And What It Cannot",
         tech="thermal camera reads skin · nobody reads the inside of a person",
         site="Air and surface thermometers, a humidity sensor, a thermal camera, a load cell "
              "in the seat, a water float and a battery monitor.",
         challenge="The thermal camera sees skin. Wet skin runs about a degree and a half "
                   "cooler than dry skin on the same body, so the moment the mist comes on "
                   "the reading drops and the person has barely changed.",
         ai_link="The bench knows what it has switched on, so it can add its own cooling back "
                 "on to the reading. A bench that forgets to do that stops cooling far too "
                 "early.",
         notebook="Section 4 - the sensors, and the gap the camera cannot see across.",
         takeaway="Never trust a sensor reading without subtracting your own effect on it."),

    dict(id="nothing", phase=2, scene="Doing Nothing", ai="The Baseline",
         tech="no shade, no fan, no mist, no packs",
         site="The bench is switched on but told to do nothing. The person lies in full sun "
              "for fourteen minutes.",
         challenge="Every claim later in the project is a claim against this line. If the "
                   "baseline is wrong, everything built on it is wrong too.",
         ai_link="No AI at all. This is the number every controller has to beat, and the "
                 "reason we can say anything about the others.",
         notebook="Section 5 - the untreated case.",
         takeaway="Measure the do-nothing case first, and honestly."),

    dict(id="shade", phase=2, scene="Pull The Canopy Out", ai="The Cheapest Big Win",
         tech="blocks about 88 % of the sun · costs a few joules once",
         site="A cloth cover slides out over the bench. Nothing else changes.",
         challenge="Shade does not actively cool anyone. It only stops the largest heat "
                   "source. On its own, the person still gets hotter, only slower.",
         ai_link="Shade uses almost no battery and no water at all, so it is the one action "
                 "the controller should take every time and never ration.",
         notebook="Section 6 - shade only.",
         takeaway="The best move costs nothing. Take it before you argue about the rest."),

    dict(id="fan", phase=2, scene="Turn The Fan Up", ai="When Airflow Is A Heater",
         tech="air hotter than skin + dry skin = the fan brings heat in",
         site="A fan blows across the bench. On a warm day this feels wonderful. On a 44 °C "
              "day, on dry skin, it is a hot-air gun.",
         challenge="Moving air only cools if water can leave the skin. If the skin is dry "
                   "and the air is hotter than the skin, faster air just delivers more heat.",
         ai_link="A fixed rule under the AI compares the fan on against the fan off and "
                 "switches it off when it would add heat. The AI cannot overrule it.",
         notebook="Section 7 - fan only, and the airflow limit.",
         takeaway="A fan is not a cooler. It is a multiplier for evaporation."),

    dict(id="mist", phase=2, scene="Spray Water On The Skin", ai="Cooling Per Litre",
         tech="wetness saturates at 1.0 · past that, extra water is runoff",
         site="A fine mist wets the skin. Water taking heat away as it evaporates is by far "
              "the strongest tool the bench has.",
         challenge="Once the skin is fully wet, more water does nothing at all. The extra "
                   "runs on to the ground. The tank still empties at the same rate.",
         ai_link="The curve of cooling-per-litre is flat and then falls off a cliff. Finding "
                 "where the cliff is, in this weather, is most of the optimisation.",
         notebook="Section 8 - mist only, and litres per degree.",
         takeaway="There is a mist rate above which you are watering the pavement."),

    dict(id="packs", phase=2, scene="Three Cold Packs", ai="Spend Now Or Keep One",
         tech="about 45 kJ each · roughly ten useful minutes · then it is warm",
         site="Three chemical cold packs in a compartment. Once a pack is opened it cannot "
              "be closed again.",
         challenge="A pack is strongest in its first minutes and useless after about ten. "
                   "Opening all three at once wastes two of them if the wait is long.",
         ai_link="Packs need no water and no battery, which makes them the answer when the "
                 "pump fails, the tank is empty, or the air is too humid to evaporate.",
         notebook="Section 9 - cold packs.",
         takeaway="Stagger the packs. Three opened together do not last three times as long."),

    dict(id="maxout", phase=3, scene="Everything At Full Power", ai="The Obvious Answer",
         tech="fan 100 % · mist 400 mL/min · all three packs · no limits",
         site="Fan at maximum, mist at maximum, every pack open. Three lines of code, and it "
              "cools faster than anything else in this project.",
         challenge="It also empties the tank, flattens the battery, and keeps cooling past "
                   "the point where cooling should stop. A cooled-too-far person is a new "
                   "emergency.",
         ai_link="This is the strategy every honest comparison has to include, because it is "
                 "the one a team writes first.",
         notebook="Section 10 - maximum fixed cooling.",
         takeaway="Fastest is not best when the supplies have to last and the radio has to "
                  "work."),

    dict(id="rules", phase=3, scene="Rules That Watch The Tank", ai="An Interpretable Controller",
         tech="if humidity is high, do not spend water · keep the radio's share back",
         site="A short list of thresholds: how much water is left, how long the wait is, "
              "whether the air can take any vapour, how much battery the radio needs.",
         challenge="A simple budget spreads water evenly across the wait. That is the wrong "
                   "shape - cooling early is worth more, because the body is hottest then.",
         ai_link="Every rule here can be read, argued with and signed off by a person who "
                 "has never trained a model. That is worth a lot.",
         notebook="Section 11 - the rule-based controller.",
         takeaway="Write the rules first. They are the thing the AI has to beat."),

    dict(id="forecast", phase=4, scene="Guessing Five Minutes Ahead", ai="Three Forecasters",
         tech="linear regression · random forest · a small neural network",
         site="Given the weather, the readings and the settings, where will the temperature "
              "be one minute from now, and five?",
         challenge="Predicting the level scores 0.99 for every model - and for a model that "
                   "predicts no change at all. Only predicting the change is an honest test.",
         ai_link="All three end up within a hundredth of a degree of each other five minutes "
                 "out. The extra accuracy of the forest is in the noise, not in the trend.",
         notebook="Section 12 - predicting the next five minutes.",
         takeaway="Score the thing you actually need, or every model looks excellent."),

    dict(id="cost", phase=4, scene="Writing Down What Good Means", ai="The Cost Function",
         tech="J = heat above 38.5 °C + water + energy + risk + blocked commands",
         site="Five things we care about, five weights, one number to make small. Change a "
              "weight and the bench behaves differently.",
         challenge="The heat term is squared, because being two degrees too hot is much worse "
                   "than being one degree too hot twice. That single choice changes how the "
                   "controller behaves in humid air.",
         ai_link="The weights are a policy decision, not a technical one. They belong to the "
                 "service that runs the bench, not to the person who wrote the code.",
         notebook="Section 13 - the cost function.",
         takeaway="If you cannot write down what good means, the AI will choose for you."),

    dict(id="adaptive", phase=4, scene="The Resource-Aware Controller", ai="Search, Predict, Score",
         tech="32 settings · roll each forward 5 minutes · keep the cheapest",
         site="Every minute the bench tries every combination of fan, mist and pack, asks the "
              "forecaster where each one leads, adds up the cost, and picks one.",
         challenge="It has to keep enough battery for the radio, enough water for the rest of "
                   "the wait, and stop cooling when the person is cool enough.",
         ai_link="The cost includes commands the safety layer would refuse, so the controller "
                 "learns not to ask for a mist it will not be given.",
         notebook="Section 14 - the adaptive controller.",
         takeaway="Search plus a forecast plus an honest cost beats a clever rule."),

    dict(id="board", phase=5, scene="The Scoreboard", ai="Eight Strategies Compared",
         tech="temperature · water · battery · packs · radio minutes · blocked commands",
         site="All eight strategies, on the same emergency, with the same weather and the "
              "same supplies.",
         challenge="On an easy afternoon almost every sensible strategy lands in the same "
                   "place. The differences only appear when something is short.",
         ai_link="The honest claim: the same useful cooling as full power, on roughly a third "
                 "of the water and with the radio still alive.",
         notebook="Section 15 - the scoreboard.",
         takeaway="Report the cost next to the result, or the result means nothing."),

    dict(id="weather", phase=5, scene="Dry Heat And Humid Heat", ai="Two Different Problems",
         tech="41 °C at 32 % vs 41 °C at 78 % · same thermometer, a fifth of the cooling",
         site="The same emergency on two afternoons that read the same on a thermometer.",
         challenge="In humid air, water barely evaporates. Misting hard spends the tank for "
                   "almost no benefit, and the fan actively adds heat.",
         ai_link="In humid air the controller switches strategy: shade, cold packs, less "
                 "water. Nobody told it to. The cost function made it.",
         notebook="Section 16 - dry heat and humid heat.",
         takeaway="The right strategy is not a property of the bench. It is a property of "
                  "the afternoon."),

    dict(id="surprises", phase=5, scene="When Something Breaks", ai="Failing Safely",
         tech="pump fails · fan fails · battery at 25 % · ambulance 8 → 25 minutes",
         site="The pump seizes at minute four. The ambulance is held up. The tank was only "
              "half full when somebody pressed the button.",
         challenge="Full-power cooling with a delayed ambulance ends with an empty tank, a "
                   "flat battery and a bench that cannot call anybody.",
         ai_link="The bench falls back to what it still has - shade and cold packs - and "
                 "tells the dispatcher what it has lost.",
         notebook="Section 17 - unexpected events.",
         takeaway="A system that keeps its radio alive is worth more than one that cools "
                  "half a degree faster."),

    dict(id="limits", phase=6, scene="What It Must Never Do", ai="The Boundaries",
         tech="no diagnosis · no invented instruction · a person can take it back",
         site="A bench with a screen, a speaker and a radio, in a public park, next to "
              "somebody who is unwell.",
         challenge="Every one of these limits is a place where a keen team would be tempted "
                   "to add one more feature.",
         ai_link="It never decides that somebody has heatstroke, and it never decides that "
                 "an ambulance is unnecessary. It manages supplies, and it says what it "
                 "cannot see.",
         notebook="Sections 18 and 19 - what it gets wrong, and the rules that do not move.",
         takeaway="The AI chooses the fan speed. Clinicians choose the care."),
]

BY_ID = {s["id"]: s for s in STEPS}
ORDER = [s["id"] for s in STEPS]
