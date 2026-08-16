"""The teaching registry: one entry per page, in the order the notebook works.

Same five parts as the notebook's sections, same plain house style: short
sentences, everyday words, no drama.

No computed figure is quoted in this prose. Every number on a page is worked out
by that page, so the two can never drift apart.
"""

PHASES = [
    ("Seven Locked Doors", "One person, no training, and a cabinet full of choices."),
    ("What The Cabinet Knows", "The report, the shelves, and the gap between them."),
    ("Rules, And Where They Stop", "The honest baseline, and the cases that break it."),
    ("A Model That Can Say Probably", "Several answers at once, with a number attached."),
    ("Deciding Safely", "Fixed checks, the cost of being wrong, and a whole day."),
    ("After The Door Opens", "Sensors, misuse, and what this would get wrong."),
]

STEPS = [
    dict(id="door", phase=0, scene="Seven Doors, One Person", ai="The Real Problem",
         tech="which compartments to open, which to keep shut, and when to ask a person",
         site="Somebody presses the button and says a cyclist has fallen and there is bleeding, "
              "but they do not know how bad it is. Seven doors, all locked.",
         challenge="The person standing there has never done this. Reading seven labels takes "
                   "time they do not have, and they will take what was said out loud rather "
                   "than what is needed.",
         ai_link="The cabinet decides which doors to open. It never decides what treatment "
                 "anybody needs - it chooses which supplies to hand over.",
         notebook="Sections 1 and 2 - the cabinet, and a person trying it by hand.",
         takeaway="Opening every door is not the safe answer. Seven open doors is seven more "
                  "decisions for somebody who cannot make them."),

    dict(id="inventory", phase=1, scene="What Is On The Shelves", ai="The Inventory",
         tech="quantity, sealed, expiry date, battery, used up or borrowed",
         site="Each compartment holds a count, a seal, and a date. Some things are used up when "
              "they are taken. Others are borrowed and come back.",
         challenge="A cabinet that assumes everything on its shelves is fine will eventually "
                   "hand somebody an expired package, or open a door onto an empty shelf.",
         ai_link="Write the shelves down as data, so every later decision can look at them "
                 "instead of assuming.",
         notebook="Section 3 - writing the inventory down.",
         takeaway="Three kinds of thing live in this cabinet: used up, comes back, and never "
                  "leaves. Mixing them up is how the maths goes wrong later."),

    dict(id="report", phase=1, scene="What The Caller Says", ai="Truth Versus Report",
         tech="the truth, then the same thing after a frightened person describes it",
         site="Somebody is really bleeding, or really is not. Then a stranger describes it on a "
              "speaker, in a hurry, while trying to help.",
         challenge="Those two things are not the same, and the gap between them is the whole "
                   "problem. People say they do not know. They forget to mention the road.",
         ai_link="Generate the truth first, then damage it on the way into the report. Now the "
                 "cabinet is being asked the question it will really be asked.",
         notebook="Section 4 - making up emergencies.",
         takeaway="Any cabinet that only works on clear descriptions will not work."),

    dict(id="rules", phase=2, scene="The Rulebook", ai="Fixed Rules",
         tech="if bleeding was reported, open the bleeding compartment",
         site="Plain rules, written by hand, in the order a person would think of them. Anybody "
              "can read them and argue with them.",
         challenge="A rule needs a clear answer, and about half the time nobody has one.",
         ai_link="Keep it as the honest baseline. Everything built afterwards has to beat it to "
                 "earn its place.",
         notebook="Section 5 - the rule-based cabinet.",
         takeaway="The rules are not too simple. They are perfect where the report is reliable "
                  "and helpless where it is not."),

    dict(id="breaks", phase=2, scene="Seven Awkward Calls", ai="Where Rules Stop",
         tech="empty shelves, low batteries, two problems at once, half a sentence",
         site="A burn with an empty burn compartment. A collapsed person and a low battery. "
              "Somebody who pressed the button by mistake.",
         challenge="Each one needs a new rule, and the rules start multiplying. Worse, the "
                   "rulebook treats 'I do not know' and 'definitely not' as the same answer.",
         ai_link="Instead of adding rules, give the cabinet a way to say how likely each "
                 "compartment is to be needed.",
         notebook="Section 6 - breaking the rules on purpose.",
         takeaway="Not knowing whether somebody is breathing is not the same as knowing they "
                  "are fine."),

    dict(id="model", phase=3, scene="Several Answers At Once", ai="A Multi-Label Model",
         tech="one small yes-or-no model per compartment, all trained together",
         site="One emergency may need gloves and bleeding supplies and traffic markers. Almost "
              "no emergency needs only one thing.",
         challenge="Most models pick one answer out of several. That is the wrong shape for this "
                   "question.",
         ai_link="Train one small model per compartment, each answering: for this report, is my "
                 "compartment needed?",
         notebook="Section 7 - a model that can say probably.",
         takeaway="Two compartments are needed every single time. Those do not get a model - "
                  "they get a rule, written where people can see it."),

    dict(id="gain", phase=3, scene="Where The Model Helps", ai="Reading The Improvement",
         tech="the same unseen emergencies, all seven compartments, scored the same way",
         site="Put the rules and the model on exactly the same emergencies and count what each "
              "one missed.",
         challenge="It is very easy to run a comparison that is not a comparison - a different "
                   "set of cases, or a different number of compartments, and the result is "
                   "meaningless.",
         ai_link="Score everything on the same unseen calls, then look at where the improvement "
                 "actually came from.",
         notebook="Section 7 - which model is best, and where the ceiling is.",
         takeaway="Missing information can often be worked out from context. Wrong information "
                  "cannot be recovered by anybody."),

    dict(id="safety", phase=4, scene="The Fixed Checks", ai="The Safety Layer",
         tech="empty, expired, unsealed, restricted, low battery - plain if statements",
         site="The model knows nothing about the shelves. It has never seen an expiry date and "
              "does not know whether a dispatcher is on the line.",
         challenge="A suggestion is not allowed to open a door. Something has to stand between "
                   "the two, and it has to be something a person can read and test.",
         ai_link="Ordinary checks, in a fixed order, that can only ever take things away. The "
                 "model can never talk them out of a decision.",
         notebook="Section 8 - the safety checks.",
         takeaway="The AI recommends. The fixed checks control the lock. That order is the "
                  "design, and it is enforced by the code, not by a comment."),

    dict(id="waiting", phase=4, scene="When It Should Not Guess", ai="Deferring To A Person",
         tech="a fifth state: not open, not refused, waiting",
         site="Somebody has collapsed and is not responding. The defibrillator is very likely to "
              "be needed. Nobody has picked up at the dispatcher yet.",
         challenge="Opening it would be guessing about the one restricted item in the cabinet. "
                   "Refusing would be pretending we think it is not needed.",
         ai_link="Do the harmless useful things immediately, and ask a person about the serious "
                 "one.",
         notebook="Section 13 - the whole cabinet, and the case it exists for.",
         takeaway="Whether a shock should be given belongs to the AED and to trained people. "
                  "Nothing here decides that, and nothing here ever should."),

    dict(id="cost", phase=4, scene="The Smallest Kit That Is Enough", ai="A Cost Function",
         tech="missing, unnecessary, delay, future shortage, unsafe - each with a weight",
         site="Out of the doors the cabinet could open, which ones should it? Opening everything "
              "is not the answer.",
         challenge="Handing over a spare pair of gloves costs almost nothing. Handing over the "
                   "only defibrillator costs a great deal. One number cannot describe both.",
         ai_link="Write down what makes a kit good or bad, give each line a weight, and let the "
                 "answer fall out of that instead of out of a chain of if statements.",
         notebook="Section 9 - choosing the smallest kit that is still enough.",
         takeaway="The more it costs to hand something over needlessly, the surer the cabinet "
                  "has to be before it opens that door. Nobody typed those numbers in."),

    dict(id="search", phase=4, scene="Checking Every Possible Kit", ai="Exhaustive Search",
         tech="seven compartments means 128 possible kits",
         site="Score every kit the cabinet could hand over and keep the cheapest.",
         challenge="Clever search algorithms exist for when you cannot look at every option.",
         ai_link="Here you can. 128 is a small number, and checking all of them means the answer "
                 "is the best one, with nothing left to wonder about.",
         notebook="Section 9 - trying every possible kit.",
         takeaway="Reach for the clever method when the simple one runs out, not before."),

    dict(id="day", phase=4, scene="A Whole Day, Five Cabinets", ai="Saving Stock For Later",
         tech="open everything, follow the rulebook, or take the smallest sufficient kit",
         site="A hundred emergencies through the day, five cabinets, and nobody comes to refill "
              "them in between.",
         challenge="Being generous is not the safe option. Every item handed over unnecessarily "
                   "in the morning is one that is not there in the afternoon.",
         ai_link="Let the cabinet look at what is left and at how much of the day is still to "
                 "come, and see whether that knowledge is worth anything.",
         notebook="Section 10 - a whole day, and five cabinets.",
         takeaway="The careful strategy earns its place when supplies are tight but not "
                  "hopeless. With full shelves there is nothing to save."),

    dict(id="sensors", phase=5, scene="What The Sensors Saw", ai="The Event Log",
         tech="a line with a time on it, every time a sensor changes",
         site="A door switch, a weight pad, a seal check. The cabinet writes down what happened "
              "and has to work out what it means.",
         challenge="Deciding to unlock a door is not the end of the job. Quite often what "
                   "happens next is not what was supposed to happen.",
         ai_link="Read the log and pick out the forced door, the borrowed item that never came "
                 "back, and the door that opened onto nothing.",
         notebook="Section 11 - what the sensors saw.",
         takeaway="A door that was opened and never used is worth knowing about. It means we "
                  "opened something we did not need to."),

    dict(id="misuse", phase=5, scene="Misuse, And Sensors That Lie", ai="Rules Beat The Model",
         tech="plain checks first, then an isolation forest as a backstop",
         site="Somebody empties a shelf. A weight pad drifts. A count stops moving while the "
              "weight keeps changing.",
         challenge="A broken sensor does not look broken. It looks like a cabinet where nothing "
                   "ever happens.",
         ai_link="Write the checks you can state, measure them, and only add a model where the "
                 "measurement shows a gap.",
         notebook="Section 12 - misuse, and sensors that lie.",
         takeaway="An isolation forest is good at odd combinations and bad at 'the same thing "
                  "but much more of it' - which is most of what breaks a cabinet."),

    dict(id="limits", phase=5, scene="What This Would Get Wrong", ai="The Honest List",
         tech="invented data, an invented answer key, and weights somebody chose",
         site="A cabinet that hands equipment to a frightened stranger deserves a harder look "
              "than a demo usually gets.",
         challenge="We wrote the rules that made the data, then trained a model that learned "
                   "them back. That is a circle, and it flatters everything on these pages.",
         ai_link="Say what would break, in order, and be specific enough that somebody could go "
                 "and test each one.",
         notebook="Section 14 - what this would get wrong.",
         takeaway="The weights are a value judgement, not a fact. They should be signed off by "
                  "the people responsible for the service."),
]

BY_ID = {s["id"]: s for s in STEPS}
ORDER = [s["id"] for s in STEPS]
