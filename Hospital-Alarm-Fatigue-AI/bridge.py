"""The teaching registry: one entry per page, in the order the notebook works.

Every entry keeps the same parts, and the same plain-English house style: short
sentences, everyday words, and no term used before it is explained.
  step      - where this page sits in an ordinary data-science project
  doing     - what we do on this page and why we do it here
  ward      - what is happening on the ward, with no computer in it
  challenge - why that is hard for people
  ai_link   - what the computer is actually being asked to do
  tech      - the one-line technical idea
  plain     - the technical name in everyday words, for a first-time reader
  figure    - what the picture on the page shows
  watch     - what is wrong in that picture, or what to look at first
  notebook  - which notebook section this matches
  takeaway  - one sentence to remember

`step` exists because the page titles are about a hospital, and a student needs
to see the ordinary shape of a data project underneath: understand the problem,
collect data, explore it, build features, train, evaluate, decide, compare.

`plain` exists because every heading carries a term of art - "action space",
"random forest", "feature engineering". A student meeting those for the first
time should never have to guess, so each page says what its own jargon means
before it uses it.
"""

# The ordinary shape of a data-science project, and the pages that do each part.
# Shown on the landing page so the hospital story never hides the method.
WORKFLOW = [
    ("1 - Understand the problem", "What is actually going wrong, before any data.", ["flood"]),
    ("2 - Collect the data", "What can be measured, how often, and how reliably.", ["ward"]),
    ("3 - Explore the data (EDA)", "Look at it. Find what separates a real event from a false one.",
     ["noise"]),
    ("4 - Decide what the system may do",
     "The moves it is allowed, and the hard limit on interrupting people.", ["actions", "budget"]),
    ("5 - Build a baseline", "The simple methods anything clever has to beat.", ["limits", "score"]),
    ("6 - Feature engineering", "Build better columns out of the raw ones.", ["clues"]),
    ("7 - Train models", "Let the computer learn the patterns instead of us writing them.",
     ["forest", "sequence"]),
    ("8 - Evaluate", "How much does each method catch, for noise we can afford?", ["ranking"]),
    ("9 - Turn predictions into decisions", "A risk number is not an action. This makes it one.",
     ["manager", "patient"]),
    ("10 - Test against the real world", "Only two nurses exist, and they have to walk.", ["nurses"]),
    ("11 - Compare and choose", "The same days, the same patients, one table.", ["scoreboard"]),
]

PHASES = [
    ("The Ward At 3 a.m.", "Too many alarms, and one of them matters."),
    ("What We Can Measure", "Seven signals, two of which everyone throws away."),
    ("The Decision", "Five moves, and only five interruptions an hour."),
    ("Rules People Wrote", "Fixed limits and a points score."),
    ("Models That Learn", "A forest, and a network that reads an hour."),
    ("Spending Attention", "Ranking, budgets, and who a nurse actually reaches."),
]

STEPS = [
    dict(id="flood", phase=0, ward="Too Many Alarms", ai="The Real Problem",
         step="1 - Understand the problem",
         doing="Look at what is actually going wrong, before choosing any model.",
         tech="hundreds of alarms a day, and almost none of them need anybody",
         site=("A machine beeps.",
               "The nurse walks over.",
               "The oxygen clip had slipped off the finger.",
               "The patient was fine."),
         challenge=("Each machine watches one patient.",
                    "It beeps at anything odd.",
                    "Twenty patients, two nurses: it never stops."),
         ai_link=("The machines already spot every odd number.",
                  "We want one that looks at all twenty patients.",
                  "It picks the few beeps worth walking over for."),
         plain="'Alarm fatigue' is what happens when something beeps so often that people stop "
               "noticing it - like a car alarm in your street. You still hear it. You have heard it "
               "a hundred times this month and it was nothing every time, so you carry on with what "
               "you were doing. Nobody is being careless; the beep has simply stopped telling anyone "
               "anything new.",
         figure="Two lines, both against how noisy the ward is. The blue line is the share of alarms "
                "that turn out to be real. The red line is the share a nurse still walks over to "
                "check.",
         watch="Look at the right-hand half. Past about 20 alarms an hour almost none are real, and "
               "almost nobody checks them any more. The alarms are still going off; they have simply "
               "stopped doing anything. Hover any point to read the two numbers at that noise level.",
         notebook="Section 1 - the problem: too many alarms.",
         takeaway="Being louder does not create more emergencies. It only buries the ones you have."),

    dict(id="ward", phase=1, ward="Twenty Patients, Seven Signals", ai="The Input Data",
         step="2 - Collect the data",
         doing="List what can be measured. A model can only use what it is given.",
         tech="heart rate, oxygen, breathing, blood pressure, temperature, signal quality, medicines",
         site=("Each patient is wired to a monitor.",
               "Seven readings arrive every 2 minutes.",
               "Blood pressure is up to 16 minutes old."),
         challenge=("Everyone has a different normal.",
                    "One healthy heart beats 62 a minute, another 88.",
                    "The same number means different things."),
         ai_link=("We add two things the monitor ignores.",
                  "How good the signal is right now.",
                  "Which medicine was just given."),
         plain="'Input data' means everything the model is allowed to look at - as far as the model "
               "is concerned, nothing else in the world exists. Here it is seven measurements per "
               "patient, arriving every 2 minutes.",
         figure="One ordinary day for one patient who never became ill. Three of the seven signals "
                "are drawn: heart rate, breathing rate, and oxygen.",
         watch="Every sharp spike you can see came from the equipment, not from the patient - a clip "
               "slipping, somebody rolling over in bed. A machine watching only for unusual numbers "
               "would have beeped at each one. Hover a spike to see which signal jumped and by how "
               "much.",
         notebook="Sections 2 and 3 - the ward and how it is built.",
         takeaway="A fixed limit compares a patient with a textbook. A useful model compares them "
                  "with themselves."),

    dict(id="noise", phase=1, ward="A Loose Clip Or A Sick Patient?", ai="Real Signal Or False Reading",
         step="3 - Explore the data (EDA)",
         doing="Explore the data: what separates a real emergency from a false alarm?",
         tech="big, sudden and brief = the equipment - small, slow and lasting = the patient",
         site=("A clip slips off a finger.",
               "The number jumps. The machine beeps.",
               "The patient is fine."),
         challenge=("Equipment goes wrong far more often than patients get ill.",
                    "A glitch jumps. Illness drifts slowly.",
                    "The glitch looks worse."),
         ai_link=("Use the monitor's signal-quality number.",
                  "Compare with the same patient 30 minutes ago.",
                  "Together they tell the two apart."),
         plain="When the equipment is the reason a number looks wrong - a clip that slipped, a pad "
               "that peeled off - we call it a false reading. The number really was measured; it "
               "just says nothing about the patient. (In the notebook and in most textbooks this is "
               "called an 'artifact'.)",
         figure="Two pictures. The first is one patient who really did get worse, with the shaded "
                "band marking the hours it was happening. The second is a bar chart: five different "
                "measurements, each shown twice - grey for the average during a false reading, red "
                "for the average during a real deterioration. Taller means further from that "
                "patient's own normal.",
         watch="In the line chart, notice how gentle the real event is: the lines lean rather than "
               "jump, which is why a machine set to catch big changes finds it last. In the bar "
               "chart, look at the last pair. During a real deterioration the signal quality stays "
               "high; during a false reading it collapses. That one column is what lets the computer "
               "ignore a loose wire without ignoring a patient. Hover any bar for its number.",
         notebook="Sections 4 and 9 - three patients, and where the false alarms come from.",
         takeaway="A false reading is big, sudden and brief. Real illness is small, slow and lasting."),

    dict(id="actions", phase=2, ward="Five Things The System Can Do", ai="The Action Space",
         step="4 - Decide what the system may do",
         doing="Decide what moves the system is allowed to make.",
         tech="ignore - measure again - watch that bed - call the nurse - call for emergency help",
         site=("An unsure nurse rarely calls for help.",
               "They take the reading again.",
               "Or check that bed on the next round."),
         challenge=("Alarm or silence is only two choices.",
                    "So every odd reading becomes an interruption."),
         ai_link=("We give the computer five moves.",
                  "Only two interrupt a person.",
                  "The other three are free."),
         plain="The 'action space' is just the list of moves the system is allowed to make, the way "
               "a chess piece has a list of legal moves. Ours has five, and three of them cost "
               "nobody any time.",
         figure="The first table is the list of moves: what each one costs in nurse-minutes, and "
                "whether it uses up one of the five interruptions you allow per hour. The second is "
                "a count of how often the system actually chose each move across every reading in "
                "the test days.",
         watch="Compare the two tables. The moves it picks thousands of times are the free ones; the "
               "two that cost a nurse's time are picked rarely. Being allowed to be unsure without "
               "spending anybody's time is the whole trick.",
         notebook="Section 5 - the five actions.",
         takeaway="Being able to be unsure without spending a nurse is what makes the budget "
                  "survivable."),

    dict(id="budget", phase=2, ward="Five Interruptions An Hour", ai="The Attention Budget",
         step="4 - Decide what the system may do",
         doing="Set a hard limit on interrupting people, before anything is built.",
         tech="600 readings an hour - 5 interruptions allowed - 60 minutes in each nurse's hour",
         site=("An hour is 60 minutes for every nurse.",
               "Two nurses do not make the hour longer.",
               "They mean two jobs at once."),
         challenge=("One alert costs about 8 minutes.",
                    "Twenty an hour is more than two nurses can finish.",
                    "A queue builds and never clears."),
         ai_link=("Attention is treated like money.",
                  "Five interruptions an hour.",
                  "The computer picks which five."),
         plain="An 'attention budget' means what it sounds like. There is only so much of a nurse's "
               "time in an hour, and spending it on one patient is spending it away from another.",
         figure="Four numbers, then a chart. The numbers: how many readings arrive each hour across "
                "the whole ward, how many interruptions you have allowed, how long each nurse's hour "
                "is, and how many nurses are on. The chart counts the alerts actually sent in each "
                "hour of the test days against that budget line.",
         watch="Do the arithmetic in the numbers first: five alerts at 8 minutes each is 40 minutes "
               "of work in an hour, and with two nurses side by side that is about 20 minutes each, "
               "so it fits. In the chart, the red rings are hours that went above the line - the "
               "budget is an average rather than a hard cap, so a quiet spell lets the next hour "
               "burst, and an emergency is sent whatever is left in the bucket. Slide the budget up "
               "in the sidebar and watch the work overtake the hour.",
         notebook="Sections 6 and 7 - the budget, and the days we judge on.",
         takeaway="Any system that ignores how much attention exists will be switched off by the "
                  "people it was built for."),

    dict(id="limits", phase=3, ward="The Monitor On The Wall", ai="Fixed Thresholds",
         step="5 - Build a baseline",
         doing="Build the baseline every hospital already uses, so there is something to beat.",
         tech="beep if any single number leaves its allowed range",
         site=("Each measurement gets a high and a low line.",
               "Cross one and it beeps.",
               "Most monitors still work this way."),
         challenge=("Six of our twenty patients sit near a line all week.",
                    "They are well.",
                    "Their bed beeps, so the ward stops listening."),
         ai_link=("Keep it underneath as a safety net.",
                  "Use its score as the bar anything cleverer must beat."),
         plain="A 'threshold' is a cut-off line. Above it the machine beeps, below it stays quiet, "
               "and nothing else about the patient is taken into account.",
         figure="Every alert this method sent, sorted by what actually caused it: a real "
                "deterioration, a patient who simply lives near one of the lines, or a moment of bad "
                "signal.",
         watch="The bar for real trouble is the shortest one on the chart. Almost everything this "
               "method sends is either a healthy patient who always sits near a line, or a loose "
               "wire. Hover a bar for the exact count.",
         notebook="Section 8 - model 1, simple limits.",
         takeaway="Each limit is sensible on its own; together they make a ward nobody can work on."),

    dict(id="score", phase=3, ward="The Early Warning Score", ai="A Hand-Written Risk Model",
         step="5 - Build a baseline",
         doing="A second baseline: the paper scoring chart from real ward walls.",
         tech="points for each abnormal reading, call a nurse at 5, an emergency at 7",
         site=("Points for how abnormal each reading is.",
               "Add them up.",
               "Act when the total passes 5."),
         challenge=("Points arrive only once a number is clearly abnormal.",
                    "A patient drifting inside the normal range scores zero."),
         ai_link=("Keep the good idea: several signals must agree.",
                  "Try to get it working earlier."),
         plain="'Hand-written model' means a person decided the rules in advance. Nothing is learned "
               "from data: somebody chose the points, and the computer only does the adding up.",
         figure="The same ward, scored by this method: how many alerts it sends per hour, how many "
                "of the real events it reaches, and how much warning it gives compared with the "
                "fixed limits above it.",
         watch="It is far quieter than the fixed limits, which is real progress - but look at the "
               "warning time. Waiting for several numbers to agree is exactly what makes it quiet, "
               "and exactly what makes it late.",
         notebook="Section 11 - model 2, a risk score.",
         takeaway="Waiting for agreement is what silences the noise, and what makes the warning "
                  "late."),

    dict(id="clues", phase=4, ward="What A Good Nurse Notices", ai="Feature Engineering",
         step="6 - Feature engineering",
         doing="Build better columns out of the raw readings.",
         tech="this patient's own normal - which way it is moving - a spike-proof average",
         site=("A good nurse does not read the screen.",
               "They notice this patient changed since an hour ago."),
         challenge=("That is not in the data.",
                    "'Changed since an hour ago' is not a column the monitor gives."),
         ai_link=("So we build it.",
                  "Each patient's own normal.",
                  "The change over 30 minutes.",
                  "An average that drops one-off spikes."),
         plain="'Feature engineering' means making new columns out of the ones you already have. The "
               "monitor gives you a heart rate; we work out whether that heart rate is high for this "
               "particular person.",
         figure="The twelve columns the trained model leans on most heavily. A longer bar means the "
                "model would be more lost without that column.",
         watch="The built columns beat the raw ones. 'How far from this patient's own normal' matters "
               "more than the reading itself, and the signal-quality column sits high up - which is "
               "the same thing the bar chart in the exploring step told us. Hover a bar to see how "
               "much the model relies on it.",
         notebook="Section 10 - turning raw readings into useful clues.",
         takeaway="A model is only as good as what you show it."),

    dict(id="forest", phase=4, ward="Learning From Past Patients", ai="Random Forest",
         step="7 - Train models",
         doing="Train a model: let the computer find the patterns itself.",
         tech="150 simple flowcharts vote on 27 clues at once",
         site=("Show the computer a few days of the ward.",
               "Mark where real trouble happened.",
               "Let it find what came before."),
         challenge=("Far more accurate than the rules.",
                    "But it needs one fixed level of worry.",
                    "No level suits every night."),
         ai_link=("Use it to rank patients by concern.",
                  "Decide separately how far down the list we can afford."),
         plain="A 'random forest' is a crowd of simple yes/no flowcharts, each shown a different "
               "slice of the data. They all vote, and the share of votes becomes the risk number.",
         figure="The alert level this model was given, chosen once on a separate tuning day, and "
                "then the scoreboard rows for the hand-written score and the trained forest side by "
                "side on the same test days.",
         watch="The forest is quieter and its alerts are far more often real - that is the win. Now "
               "move the sidebar sliders: the level was chosen on one day, so on a quieter or "
               "noisier ward the same number is wrong in one direction or the other, and the row "
               "moves with it.",
         notebook="Section 12 - model 3, a random forest.",
         takeaway="A single alert level chosen in advance cannot be right on every kind of night."),

    dict(id="sequence", phase=4, ward="Reading The Whole Hour", ai="LSTM",
         step="7 - Train models",
         doing="Try the deep-learning option, so the comparison is fair.",
         tech="30 readings in order, and learning what to forget",
         site=("A nurse reading an hour of chart sees a shape.",
               "Not a number."),
         challenge=("Our columns assumed 30 minutes was the interesting gap.",
                    "A faster or slower pattern is missed."),
         ai_link=("Give a network the whole hour, in order.",
                  "Let it find the shape itself.",
                  "And learn what to ignore."),
         plain="An 'LSTM' reads readings in order, the way you read a sentence, keeping a small "
               "memory as it goes. That memory is what lets it tell a passing blip from a steady "
               "drift.",
         figure="A single artificial neuron, drawn: every input multiplied by how much it matters, "
                "added up, and squeezed onto a line between 0 and 1 to become a risk number.",
         watch="This is the one model the app does not run - it needs TensorFlow, which does not fit "
               "in a free container - so the honest notebook result is quoted instead: on this "
               "problem the simpler forest ranked patients better. Deep learning is not the reward "
               "for trying hard.",
         notebook="Sections 13 and 14 - one neuron, then model 4.",
         takeaway="Deep learning earns its place when the raw signal is rich and hand-built clues "
                  "are poor. Here neither is true, and the simpler model wins."),

    dict(id="ranking", phase=5, ward="Who Is Top Of The List?", ai="Ranking, Not Thresholds",
         step="8 - Evaluate",
         doing="Evaluate: how much does each method catch, for noise we can afford?",
         tech="events caught, at every possible alert rate",
         site=("Ask each method to sort the ward.",
               "Most worrying patient first."),
         challenge=("One setting tells you nothing.",
                    "Turn it up and it catches more.",
                    "Turn it down and it catches less."),
         ai_link=("Test every setting at once.",
                  "Read all methods at the budget we can afford."),
         plain="'Ranking' asks a different question from alarming. Not 'is this patient in danger?' "
               "but 'of everyone here, who should be looked at first?'",
         figure="One line per method. Going right means allowing more alerts an hour - note the "
                "scale stretches, so each step right is a big jump in noise. Going up means catching "
                "more of the real events. The dashed white line is the budget you set.",
         watch="Read straight up from the dashed line and ignore everything to its right: it is "
               "unaffordable however much it catches. The vertical gap between the lines at exactly "
               "that point is what the better model is really worth. Hover any point for the pair "
               "of numbers.",
         notebook="Section 15 - which model ranks the risk best.",
         takeaway="Everything to the right of the budget line is unaffordable, however much it "
                  "catches."),

    dict(id="manager", phase=5, ward="Spending The Five", ai="Attention-Budget Optimizer",
         step="9 - Turn predictions into decisions",
         doing="Turn a risk number into a decision.",
         tech="a bucket of tokens, and a level of worry that moves with what is left",
         site=("On a quiet night a nurse checks a hunch.",
               "In the worst ten minutes, only a certainty moves them."),
         challenge=("A fixed level cannot do that.",
                    "The right answer depends on how busy the ward is."),
         ai_link=("The level moves with the budget left.",
                  "Full bucket: check a maybe.",
                  "Nearly empty: only certainties, and always an emergency."),
         plain="An 'optimizer' here is not heavy maths. It is simply the part that decides how to "
               "spend a limited budget, using a risk number it did not work out itself.",
         figure="Alerts sent in each hour of the test period. The dashed red line is the budget you "
                "allowed.",
         watch="Averaged over the whole period the line sits below the budget, which is the point - "
               "the fixed-limit method spent every hour far above it. Individual hours still poke "
               "above the line, marked in red, and there are two honest reasons: the bucket refills "
               "steadily, so a quiet spell lets the next hour burst, and an emergency is sent "
               "whatever is left in the bucket. Hover any hour to see how many alerts went out.",
         notebook="Section 16 - model 5, the attention-budget optimizer.",
         takeaway="Same forest, same risk numbers. Only the decision changed, and that is where the "
                  "problem was."),

    dict(id="patient", phase=5, ward="One Patient, Minute By Minute", ai="The Policy In Action",
         step="9 - Turn predictions into decisions",
         doing="Follow one patient, and label every reading with the move chosen.",
         tech="every reading marked with the move it produced",
         site=("Follow one patient.",
               "From the first sign of trouble to the crisis."),
         challenge=("Averages hide what happens to a person.",
                    "A scoreboard cannot show who was reached in time."),
         ai_link=("Every mark is the computer choosing.",
                  "Re-check, watch, call the nurse, escalate."),
         plain="A 'policy' is the rule that turns a risk number into a move. Same numbers, different "
               "policy, completely different ward.",
         figure="The purple line is the computer's level of worry about this one patient over time. "
                "Zero on the bottom axis is the moment of crisis, so everything left of it is the "
                "run-up. The two dotted lines are the levels at which it calls a nurse and calls an "
                "emergency, and each marker is the move it chose at that reading.",
         watch="Count the markers: nearly all of them are the free ones. The triangle is the single "
               "interruption that mattered, and it lands well before zero - that gap is the warning "
               "time the ward actually gets. Hover a marker to see the move and the risk at that "
               "minute.",
         notebook="Section 17 - watching one patient.",
         takeaway="Most of the work is done by the actions that interrupt nobody."),

    dict(id="nurses", phase=5, ward="The Nurse's Shift", ai="A Queue With Two Servers",
         step="10 - Test against the real world",
         doing="Test against reality: only two nurses exist, and they have to walk.",
         tech="8 minutes for a call, 20 for an emergency, emergencies jump the queue",
         site=("Nobody is treated by an alert.",
               "A nurse has to walk over.",
               "There are only two of them."),
         challenge=("More work than two people can do builds a queue.",
                    "It never clears.",
                    "Right alerts wait behind wrong ones."),
         ai_link=("Score each method on patients reached in time.",
                  "Not on alerts sent."),
         plain="'A queue with two servers' is the supermarket-till idea: alerts arrive whenever they "
               "like, but only two people can serve them, so a rush builds a line.",
         figure="Four columns for each method: how many alerts an hour it sends, how many nurse "
                "minutes that costs, how long a patient typically waited for somebody to arrive, "
                "and how many patients were actually reached in time.",
         watch="Read the first two columns together. Any method asking for more minutes than the "
               "ward has builds a queue that never clears, and you can see the result in the third "
               "column - the wait. The loudest method sends the most alerts and delivers the "
               "slowest nurse.",
         notebook="Section 18 - workload and response time.",
         takeaway="An alert that sits in a queue for two hours did not help anybody."),

    dict(id="scoreboard", phase=5, ward="What The Ward Would Choose", ai="The Comparison",
         step="11 - Compare and choose",
         doing="Compare every method on the same days, then choose.",
         tech="the five methods, side by side, on the numbers a ward sister asks about",
         site=("The questions a ward sister asks.",
               "Was anybody missed?",
               "Did a nurse arrive in time?",
               "How many false alarms?"),
         challenge=("No method wins every column.",
                    "The loud one is answered late.",
                    "The quiet one misses people."),
         ai_link=("Judge on what a patient would care about.",
                  "Did somebody get there in time?"),
         plain="'Metrics' are the columns you agree to be judged on. Choosing them badly is how a "
               "system passes its own test and still fails the ward.",
         figure="The same four methods on the numbers that matter, drawn as bars so the trade-offs "
                "are visible, and then the full table underneath with every column.",
         watch="No bar is tallest everywhere. Read across one method at a time and ask what it "
               "spent to get its score - the loud one reaches people by asking for more nursing "
               "time than the ward has.",
         notebook="Sections 19 and 20 - the scoreboard and the honest limitations.",
         takeaway="A prediction is not a decision, and attention is the scarce resource."),
]
# --------------------------------------------------------------- the 27 clues
# story.FEATURES is a bare list of column names. On its own it teaches nothing:
# "spo2_smooth_d30" is not English. Every feature the forest is given is named
# here in three parts - the column, what it actually is, and what it is FOR -
# so a first-time reader can read the importance chart without a decoder ring.
# A reading arrives every 2 minutes, so 5 readings = 10 minutes and 15 = 30.
FEATURE_GROUPS = [
    dict(name="The five raw readings",
         idea="Exactly what the monitor puts on the screen, with nothing done to it.",
         plan="We hand these to the model too, but on their own they are precisely what makes a "
              "monitor beep at everybody.",
         rows=[
             ("hr", "Heart rate, beats per minute.",
              "The headline number; alone it cannot tell fast-because-ill from fast-because-frightened."),
             ("spo2", "Oxygen in the blood, as a percentage, from the finger probe.",
              "Falls in real deterioration - and also every time the probe slips off."),
             ("rr", "Breaths per minute, from the chest sticker.",
              "The earliest signal of the three, and the one that peels off most often."),
             ("sbp", "The top blood-pressure number, from the arm cuff.",
              "Only refreshed every 16 minutes, so we must tell the model how old it is."),
             ("temp", "Body temperature in Celsius.",
              "Moves slowly, so it is worth little alone and useful beside the others."),
         ]),
    dict(name="Middle-of-five smoothing",
         idea="The middle value of the last five readings, which is 10 minutes of history.",
         plan="Take the middle value rather than the average: one wild spike is thrown away entirely "
              "instead of being blended in.",
         rows=[
             ("hr_smooth", "Heart rate with one-off spikes removed.",
              "Lets a real climb show through without every twitch counting."),
             ("spo2_smooth", "Oxygen with one-off drops removed.",
              "A probe that slips for a single reading no longer looks like a crisis."),
             ("rr_smooth", "Breathing rate with one-off jumps removed.",
              "Separates a cough from a genuine change in breathing."),
         ]),
    dict(name="Distance from this patient's own normal",
         idea="The smoothed value now, minus what this same patient usually sits at - the middle of "
              "their last 4 hours, ending half an hour ago.",
         plan="The single most valuable idea in the build. It compares a patient with themselves "
              "instead of with a textbook, so somebody who simply lives at 88 beats a minute stops "
              "alarming all week.",
         rows=[
             ("hr_off", "How far the heart rate is from this patient's own usual.",
              "+15 on somebody who sits at 62 matters; the very same 77 is nothing on somebody else."),
             ("spo2_off", "How far oxygen has drifted from their own usual.",
              "Catches a slow slide that never crosses the fixed low limit."),
             ("rr_off", "How far breathing is from their own usual.",
              "Usually the first of the five to move when a patient is deteriorating."),
             ("sbp_off", "How far blood pressure is from their own usual.",
              "Confirms the others; a lone cuff reading is too noisy to trust."),
             ("temp_off", "How far temperature is from their own usual.",
              "Small but genuine when the cause is an infection."),
         ]),
    dict(name="Direction of travel",
         idea="The value now, minus the value 30 minutes ago.",
         plan="Answers a question no single reading can: not 'is this bad?' but 'is this getting "
              "worse?' Steady-but-odd and sliding-fast look identical without it.",
         rows=[
             ("hr_smooth_d30", "Change in heart rate over the last half hour.",
              "A steady climb is the classic early shape of trouble."),
             ("spo2_smooth_d30", "Change in oxygen over the last half hour.",
              "A falling trend counts even while the number is still technically normal."),
             ("rr_smooth_d30", "Change in breathing rate over the last half hour.",
              "Rising breathing plus falling oxygen is the pair worth waking somebody for."),
             ("sbp_d30", "Change in blood pressure over the last half hour.",
              "A drop here is late, but serious."),
             ("temp_d30", "Change in temperature over the last half hour.",
              "Slow by nature; included so a rising fever is not invisible."),
         ]),
    dict(name="How much the sensor can be trusted",
         idea="A 0-to-1 score for how well the probe is actually gripping, plus how stale the cuff "
              "reading is.",
         plan="This is the group an ordinary monitor throws away, and it is what lets the model tell "
              "a broken sensor from a sick person.",
         rows=[
             ("quality", "Sensor confidence right now: 0 = fallen off, 1 = perfect grip.",
              "Collapses during a glitch while the patient is fine - the giveaway."),
             ("quality_smooth", "The same confidence, middle of the last five readings.",
              "Separates a momentary wobble from a probe that is genuinely off."),
             ("bp_age", "Minutes since the blood-pressure cuff last inflated, 0 to 14.",
              "Tells the model the pressure on screen may be a quarter of an hour old."),
         ]),
    dict(name="What was just given to the patient",
         idea="Which medicine was administered, and how long ago.",
         plan="Medicines change vital signs on purpose. Telling the model this turns a whole class of "
              "false alarms into an expected, explainable change.",
         rows=[
             ("mins_since_med", "Minutes since the last dose, capped at 999 for 'nothing recently'.",
              "Recency is what matters: a drug given 4 hours ago is not the explanation."),
             ("med_recent", "1 if any medicine was given in the last 90 minutes, otherwise 0.",
              "A quick catch-all flag meaning 'expect this patient's numbers to move'."),
             ("med_speeds_heart", "1 if a nebuliser was given in the last hour.",
              "A nebuliser is meant to raise the heart rate - not a reason to call anyone."),
             ("med_slows_heart", "1 if a beta blocker was given in the last 4 hours.",
              "Explains a heart rate that has dropped below the fixed low limit."),
             ("med_slows_breathing", "1 if an opioid was given in the last 2.5 hours.",
              "Explains slower breathing - and is the one case where it can still be real."),
         ]),
    dict(name="Time",
         idea="The hour on the clock, 0 to 23.",
         plan="Kept because bodies and wards both run on a daily rhythm; the model can learn that 3 "
              "a.m. is not 3 p.m.",
         rows=[
             ("hour_of_day", "Which hour of the day this reading came from.",
              "Lets the forest allow for normal night-time dips instead of alarming at them."),
         ]),
]

FEATURE_COUNT = sum(len(g["rows"]) for g in FEATURE_GROUPS)


BY_ID = {s["id"]: s for s in STEPS}
ORDER = [s["id"] for s in STEPS]
