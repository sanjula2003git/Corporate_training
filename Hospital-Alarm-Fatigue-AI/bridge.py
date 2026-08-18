"""The teaching registry: one entry per page, in the order the notebook works.

Every entry keeps the same five parts as the notebook's sections, and the same
plain-English house style: short sentences, everyday words.
  ward      - what is happening on the ward, with no AI in it
  challenge - why that is hard for people
  ai_link   - what the AI is actually being asked to do
  tech      - the one-line technical idea
  plain     - the technical name in everyday words, for a first-time reader
  notebook  - which notebook section this matches
  takeaway  - one sentence to remember

'plain' exists because every heading on the page carries a term of art -
"action space", "random forest", "feature engineering". A student meeting
those for the first time should never have to guess, so each page says what
its own jargon means before it uses it.
"""

PHASES = [
    ("The Ward At 3 a.m.", "Too many alarms, and one of them matters."),
    ("What We Can Measure", "Seven signals, two of which everyone throws away."),
    ("The Decision", "Five actions, and only five interruptions an hour."),
    ("Rules People Wrote", "Fixed limits and a points score."),
    ("Models That Learn", "A forest, and a network that reads an hour."),
    ("Spending Attention", "Ranking, budgets, and who a nurse actually reaches."),
]

STEPS = [
    dict(id="flood", phase=0, ward="Too Many Alarms", ai="The Real Problem",
         tech="hundreds of alarms a day, almost none of them useful",
         site="A monitor beeps. A nurse walks over. The probe had slipped off the finger. This happens "
              "again and again, all shift.",
         challenge="A monitor is built to be safe on its own, so it beeps at anything unusual. That is "
                   "right for one patient in theatre and wrong for twenty patients and two nurses.",
         ai_link="The job is not to spot every abnormal number. It is to decide which few are worth a "
                 "person's time.",
         plain="'Alarm fatigue' is what happens when a warning goes off so often that people stop "
               "reacting to it. Nobody is being careless; the alarm has simply stopped carrying news.",
         notebook="Section 1 - the problem: too many alarms.",
         takeaway="Being louder does not create more emergencies. It only buries the ones you have."),

    dict(id="ward", phase=1, ward="Twenty Patients, Seven Signals", ai="The Input Data",
         tech="heart rate, oxygen, breathing, blood pressure, temperature, sensor quality, medicines",
         site="Each patient is wired to a monitor that reports every 2 minutes. Blood pressure comes from "
              "a cuff every 16 minutes, so on screen it is often old.",
         challenge="Everyone has a different normal. One person sits at 62 beats a minute all week and "
                   "another at 88, and both are healthy.",
         ai_link="Feed the model the two signals a plain monitor ignores: how much the sensor can be "
                 "trusted, and what drug was just given.",
         plain="'Input data' just means everything the model is allowed to look at. Here that is seven "
               "measurements per patient, arriving every 2 minutes.",
         notebook="Sections 2 and 3 - the ward and how it is built.",
         takeaway="A fixed limit compares a patient with a textbook. A useful model compares them with "
                  "themselves."),

    dict(id="noise", phase=1, ward="A Loose Probe Or A Sick Patient?", ai="Signal Versus Artifact",
         tech="tall, sudden and short = noise · small, slow and persistent = illness",
         site="Probes slip, patients scratch their nose, breathing stickers peel off. The number jumps, "
              "the monitor beeps, and the patient is completely fine.",
         challenge="On this ward a sensor misbehaves about three times as often as a patient "
                   "deteriorates, and the glitch looks far more dramatic than the illness.",
         ai_link="Give the model sensor quality and a few minutes of history, and the two stop looking "
                 "alike.",
         plain="An 'artifact' is a reading that is wrong because of the equipment, not because of the "
               "patient - a slipped probe, a peeled sticker. The number is real; the illness is not.",
         notebook="Sections 4 and 9 - three patients, and where the false alarms come from.",
         takeaway="Noise is tall, sudden and short. Illness is small, slow and persistent."),

    dict(id="actions", phase=2, ward="Five Things The System Can Do", ai="The Action Space",
         tech="ignore · repeat the measurement · keep watching · notify · urgent response",
         site="A nurse who is unsure does not always interrupt someone. Often they simply take the "
              "reading again in a few minutes.",
         challenge="If the only options are 'alarm' and 'silence', every worrying reading has to become "
                   "an interruption.",
         ai_link="Three of the five actions cost nobody anything. They are what let the system be "
                 "suspicious a hundred times an hour and still interrupt a person only five times.",
         plain="The 'action space' is simply the list of things the system is allowed to do. Ours has "
               "five, and only two of them ever interrupt a human being.",
         notebook="Section 5 - the five actions.",
         takeaway="Being able to be unsure without spending a nurse is what makes the budget survivable."),

    dict(id="budget", phase=2, ward="Five Interruptions An Hour", ai="The Attention Budget",
         tech="600 readings an hour, 5 alerts allowed, 120 nurse-minutes in total",
         site="Two nurses have 120 minutes of attention in every hour, and the ward has everything else "
              "to do as well.",
         challenge="Twenty alerts an hour at eight minutes each asks for more time than an hour "
                   "contains. The queue never empties, so it grows all shift.",
         ai_link="Treat attention as a resource with a hard limit, and make the model spend it.",
         plain="An 'attention budget' treats a nurse's time like money: there is a fixed amount per "
               "hour, and spending it on one patient means not spending it on another.",
         notebook="Sections 6 and 7 - the budget, and the days we judge on.",
         takeaway="Any system that ignores how much attention exists will be switched off by the people "
                  "it was built for."),

    dict(id="limits", phase=3, ward="The Monitor On The Wall", ai="Fixed Thresholds",
         tech="beep if any single number leaves its range",
         site="Set a high and a low limit for each measurement. This is what almost every monitor in "
              "every hospital does today.",
         challenge="Six of our twenty patients live permanently near a limit and are not ill. Their bed "
                   "alarms all week, and the ward learns to ignore it.",
         ai_link="Use it as the honest baseline that any model has to beat, and keep it running "
                 "underneath as a safety net.",
         plain="A 'threshold' is a cut-off line. Above it the machine beeps, below it stays quiet, and "
               "nothing else about the patient is taken into account.",
         notebook="Section 8 - model 1, simple limits.",
         takeaway="Each limit is sensible on its own; together they make a ward nobody can work on."),

    dict(id="score", phase=3, ward="The Early Warning Score", ai="A Hand-Written Risk Model",
         tech="points per abnormal reading, alert at 5, emergency at 7",
         site="A version of this hangs on the wall of most wards. Give points for how abnormal each "
              "number is, and add them up.",
         challenge="Points only arrive once a number is already clearly abnormal, so a patient sliding "
                   "downhill inside the normal ranges scores zero.",
         ai_link="Requiring several measurements to agree is a real idea and costs nothing to compute.",
         plain="A 'hand-written model' means a human decided the rules in advance. No learning happens: "
               "somebody chose the points, and the machine only adds them up.",
         notebook="Section 11 - model 2, a risk score.",
         takeaway="Waiting for agreement is what silences the noise, and what makes the warning late."),

    dict(id="clues", phase=4, ward="What A Good Nurse Notices", ai="Feature Engineering",
         tech="own normal · direction of travel · middle-of-five smoothing",
         site="An experienced nurse does not read the screen. They notice this patient is different from "
              "how they were an hour ago.",
         challenge="None of that is in the raw data. It has to be built.",
         ai_link="Add each patient's own normal, the change over 30 minutes, and a median that throws "
                 "spikes away almost for free.",
         plain="'Feature engineering' is building better columns out of the ones you already have. The "
               "monitor gives a heart rate; we work out whether it is high for this patient.",
         notebook="Section 10 - turning raw readings into useful clues.",
         takeaway="A model is only as good as what you show it."),

    dict(id="forest", phase=4, ward="Learning From Past Patients", ai="Random Forest",
         tech="150 trees vote on 27 clues at once",
         site="Instead of writing the rules, show a machine several days of the ward and let it find "
              "which combinations of clues came before real trouble.",
         challenge="It is far more accurate than the rules, and at a fixed alert level it can still be "
                   "wrong in both directions - silent on a quiet night, buried on a bad one.",
         ai_link="Use the forest for what it is good at, which is putting patients in the right order.",
         plain="A 'random forest' is a crowd of simple yes/no flowcharts, each shown a different slice "
               "of the data. They vote, and the share of votes becomes the risk number.",
         notebook="Section 12 - model 3, a random forest.",
         takeaway="A single alert level chosen in advance cannot be right on every kind of night."),

    dict(id="sequence", phase=4, ward="Reading The Whole Hour", ai="LSTM",
         tech="30 readings in order, and learning what to forget",
         site="A nurse looking at an hour of the chart sees a shape, not a number.",
         challenge="The forest sees hand-built summaries of the past, and somebody had to decide in "
                   "advance that 30 minutes was the interesting gap.",
         ai_link="Hand the network the raw hour and let it find the shape itself - including learning to "
                 "drop a two-minute spike and keep a slow lean.",
         plain="An 'LSTM' is a model that reads readings in order, like a sentence, keeping a small "
               "memory as it goes so it can tell a passing blip from a steady drift.",
         notebook="Sections 13 and 14 - one neuron, then model 4.",
         takeaway="Deep learning earns its place when the raw signal is rich and hand-built clues are "
                  "poor. Here neither is true, and the simpler model wins."),

    dict(id="ranking", phase=5, ward="Who Is Top Of The List?", ai="Ranking, Not Thresholds",
         tech="events caught, for each possible alert rate",
         site="Ask each method to sort the ward with the patient it is most worried about at the top.",
         challenge="Comparing methods by counting their alerts at one arbitrary setting tells you almost "
                   "nothing about them.",
         ai_link="Read every curve at the budget line. The gap there is the real value of a better "
                 "model.",
         plain="'Ranking' asks a different question from alarming. Not 'is this patient in danger?' but "
               "'of everyone here, who should be looked at first?'",
         notebook="Section 15 - which model ranks the risk best.",
         takeaway="Everything to the right of the budget line is unaffordable, however much it catches."),

    dict(id="manager", phase=5, ward="Spending The Five", ai="Attention-Budget Optimizer",
         tech="a bucket of tokens, and a level that moves with what is left",
         site="On a quiet night a senior nurse will go and check a hunch. At the worst moment of a bad "
              "shift they move only for something they are sure about.",
         challenge="A fixed level cannot do that, because the right answer depends on what else is "
                   "going on, not only on the patient.",
         ai_link="Refill five tokens an hour. When the bucket is full, a maybe is worth checking. When "
                 "it is nearly empty, only near-certainties get through - and an emergency always does.",
         plain="An 'optimizer' here is not maths jargon: it is the part that decides how to spend a "
               "limited budget, given a risk number it did not calculate itself.",
         notebook="Section 16 - model 5, the attention-budget optimizer.",
         takeaway="Same forest, same risk numbers. Only the decision changed, and that is where the "
                  "problem was."),

    dict(id="patient", phase=5, ward="One Patient, Minute By Minute", ai="The Policy In Action",
         tech="every reading labelled with the action it produced",
         site="Follow a single patient from the moment they start to deteriorate until the crisis.",
         challenge="Averages hide what a policy actually does to a person.",
         ai_link="Watch the quiet re-checks that cost nothing, the one alert that goes out, and the "
                 "escalation if the risk keeps climbing.",
         plain="A 'policy' is the rule that turns a risk number into an action. The same numbers plus a "
               "different policy gives a completely different ward.",
         notebook="Section 17 - watching one patient.",
         takeaway="Most of the work is done by the actions that interrupt nobody."),

    dict(id="nurses", phase=5, ward="The Nurse's Shift", ai="A Queue With Two Servers",
         tech="8 minutes a notify, 20 an emergency, priority to the emergency",
         site="Nobody is treated by an alert. A nurse has to walk over, and only two of them exist.",
         challenge="Once demand passes supply the queue can never catch up, and the alerts that were "
                   "right wait behind the ones that were not.",
         ai_link="Score every method on the patients a nurse physically reached before the crisis, not "
                 "on the alerts it sent.",
         plain="A 'queue with two servers' is the supermarket-till idea: alerts arrive whenever they "
               "like, but only two people can serve them, so a rush builds a line.",
         notebook="Section 18 - workload and response time.",
         takeaway="An alert that sits in a queue for two hours did not help anybody."),

    dict(id="scoreboard", phase=5, ward="What The Ward Would Choose", ai="The Comparison",
         tech="five methods, the same days, the metrics a ward sister asks about",
         site="Events missed, patients reached in time, warning minutes, false alarms, workload, "
              "response time.",
         challenge="No method wins everything. The loud one is answered late, the quiet one misses "
                   "people, and the accurate one leaves the budget unspent.",
         ai_link="Judge on what a patient would recognise as mattering: did somebody arrive in time?",
         plain="'Metrics' are the columns you agree to be judged on. Choosing them badly is how a system "
               "passes its own test and still fails the ward.",
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
