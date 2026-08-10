"""The teaching registry: one entry per page, in the order the notebook works.

Every entry keeps the same five parts as the notebook's sections, and the same
plain-English house style: short sentences, everyday words.
  ward      - what is happening on the ward, with no AI in it
  challenge - why that is hard for people
  ai_link   - what the AI is actually being asked to do
  tech      - the one-line technical idea
  notebook  - which notebook section this matches
  takeaway  - one sentence to remember
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
         notebook="Section 5 - the five actions.",
         takeaway="Being able to be unsure without spending a nurse is what makes the budget survivable."),

    dict(id="budget", phase=2, ward="Five Interruptions An Hour", ai="The Attention Budget",
         tech="600 readings an hour, 5 alerts allowed, 120 nurse-minutes in total",
         site="Two nurses have 120 minutes of attention in every hour, and the ward has everything else "
              "to do as well.",
         challenge="Twenty alerts an hour at eight minutes each asks for more time than an hour "
                   "contains. The queue never empties, so it grows all shift.",
         ai_link="Treat attention as a resource with a hard limit, and make the model spend it.",
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
         notebook="Section 8 - model 1, simple limits.",
         takeaway="Each limit is sensible on its own; together they make a ward nobody can work on."),

    dict(id="score", phase=3, ward="The Early Warning Score", ai="A Hand-Written Risk Model",
         tech="points per abnormal reading, alert at 5, emergency at 7",
         site="A version of this hangs on the wall of most wards. Give points for how abnormal each "
              "number is, and add them up.",
         challenge="Points only arrive once a number is already clearly abnormal, so a patient sliding "
                   "downhill inside the normal ranges scores zero.",
         ai_link="Requiring several measurements to agree is a real idea and costs nothing to compute.",
         notebook="Section 11 - model 2, a risk score.",
         takeaway="Waiting for agreement is what silences the noise, and what makes the warning late."),

    dict(id="clues", phase=4, ward="What A Good Nurse Notices", ai="Feature Engineering",
         tech="own normal · direction of travel · middle-of-five smoothing",
         site="An experienced nurse does not read the screen. They notice this patient is different from "
              "how they were an hour ago.",
         challenge="None of that is in the raw data. It has to be built.",
         ai_link="Add each patient's own normal, the change over 30 minutes, and a median that throws "
                 "spikes away almost for free.",
         notebook="Section 10 - turning raw readings into useful clues.",
         takeaway="A model is only as good as what you show it."),

    dict(id="forest", phase=4, ward="Learning From Past Patients", ai="Random Forest",
         tech="150 trees vote on 27 clues at once",
         site="Instead of writing the rules, show a machine several days of the ward and let it find "
              "which combinations of clues came before real trouble.",
         challenge="It is far more accurate than the rules, and at a fixed alert level it can still be "
                   "wrong in both directions - silent on a quiet night, buried on a bad one.",
         ai_link="Use the forest for what it is good at, which is putting patients in the right order.",
         notebook="Section 12 - model 3, a random forest.",
         takeaway="A single alert level chosen in advance cannot be right on every kind of night."),

    dict(id="sequence", phase=4, ward="Reading The Whole Hour", ai="LSTM",
         tech="30 readings in order, and learning what to forget",
         site="A nurse looking at an hour of the chart sees a shape, not a number.",
         challenge="The forest sees hand-built summaries of the past, and somebody had to decide in "
                   "advance that 30 minutes was the interesting gap.",
         ai_link="Hand the network the raw hour and let it find the shape itself - including learning to "
                 "drop a two-minute spike and keep a slow lean.",
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
         notebook="Section 16 - model 5, the attention-budget optimizer.",
         takeaway="Same forest, same risk numbers. Only the decision changed, and that is where the "
                  "problem was."),

    dict(id="patient", phase=5, ward="One Patient, Minute By Minute", ai="The Policy In Action",
         tech="every reading labelled with the action it produced",
         site="Follow a single patient from the moment they start to deteriorate until the crisis.",
         challenge="Averages hide what a policy actually does to a person.",
         ai_link="Watch the quiet re-checks that cost nothing, the one alert that goes out, and the "
                 "escalation if the risk keeps climbing.",
         notebook="Section 17 - watching one patient.",
         takeaway="Most of the work is done by the actions that interrupt nobody."),

    dict(id="nurses", phase=5, ward="The Nurse's Shift", ai="A Queue With Two Servers",
         tech="8 minutes a notify, 20 an emergency, priority to the emergency",
         site="Nobody is treated by an alert. A nurse has to walk over, and only two of them exist.",
         challenge="Once demand passes supply the queue can never catch up, and the alerts that were "
                   "right wait behind the ones that were not.",
         ai_link="Score every method on the patients a nurse physically reached before the crisis, not "
                 "on the alerts it sent.",
         notebook="Section 18 - workload and response time.",
         takeaway="An alert that sits in a queue for two hours did not help anybody."),

    dict(id="scoreboard", phase=5, ward="What The Ward Would Choose", ai="The Comparison",
         tech="five methods, the same days, the metrics a ward sister asks about",
         site="Events missed, patients reached in time, warning minutes, false alarms, workload, "
              "response time.",
         challenge="No method wins everything. The loud one is answered late, the quiet one misses "
                   "people, and the accurate one leaves the budget unspent.",
         ai_link="Judge on what a patient would recognise as mattering: did somebody arrive in time?",
         notebook="Sections 19 and 20 - the scoreboard and the honest limitations.",
         takeaway="A prediction is not a decision, and attention is the scarce resource."),
]

BY_ID = {s["id"]: s for s in STEPS}
ORDER = [s["id"] for s in STEPS]
