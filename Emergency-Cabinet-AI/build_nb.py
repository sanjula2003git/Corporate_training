"""Build the One Door Opens emergency-cabinet teaching notebook.

Run with:  python -X utf8 build_nb.py
Then execute:  python -m jupyter execute --inplace One_Door_Opens_Emergency_Cabinet.ipynb

House style for this notebook: short sentences, everyday words, no drama. Every
technical word gets a plain-English meaning in the same sentence it first
appears. No number is written into the prose until it has been computed.
"""
import os

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []


def md(t):
    cells.append(nbf.v4.new_markdown_cell(t))


def code(t):
    cells.append(nbf.v4.new_code_cell(t))


# ------------------------------------------------------------------ 0. framing
md("""# One Door Opens

### Building an intelligent emergency cabinet

An emergency cabinet has seven locked compartments. This project builds the part that decides
which ones to unlock, using what is known about the emergency and what is left in the cabinet.

---

## Please read this first

Everything in this notebook is **made up by a program written further down the page**. No real
cabinet, no real patient, no real emergency. It is a teaching example.

A real cabinet like this would be medical equipment, and medical equipment has to be approved by
the people whose job that is. Nothing here is approved, and nothing here should be used to help
a real person.

---

## What is in the cabinet

Seven compartments. Each one is locked until something decides to open it.

| Compartment | What is inside | What the cabinet can sense |
|---|---|---|
| Protective equipment | Gloves and face barriers | Weight, item count |
| Bleeding supplies | Approved bleeding-control supplies | Weight, package seal |
| Burn supplies | Approved burn-care supplies | Temperature, item count |
| AED | Defibrillator, used under dispatcher direction | Door, weight, seal, return |
| Traffic safety | Reflective markers and warning lights | RFID tag, return |
| Flotation | Water-rescue equipment | Door, weight |
| Communication unit | Speaker, camera, link to the dispatcher | Docking, battery |

---

## The question this project answers

Someone presses the button and says:

> "A cyclist has fallen. There is bleeding, but I don't know how serious it is."

That is not much to go on. The cabinet has to decide:

- which compartments to **open now**
- which to **keep locked**
- when to **wait for a person** instead of guessing

---

## Why a simple rule is not enough

The obvious answer is a rule:

```python
if emergency == "bleeding":
    open_bleeding_compartment()
```

That rule is fine until one of these happens, and one of them usually does:

- the description is vague
- more than one thing is wrong
- the shelf is empty
- the item on the shelf has expired
- two compartments hold things that would both work
- another emergency is expected nearby and will need the same supplies
- opening extra doors slows the person down
- the dispatcher changes their mind about what happened

So the real job is not *"what is the emergency"*. It is:

> **which supplies, given how sure we are, what is in stock, how urgent it is, what has expired,
> and what the next emergency will probably need.**

---

## The rule this whole project is built around

The order below is the design. It is not a suggestion, and the code follows it exactly.

```
approved protocol / dispatcher   ->   list of equipment allowed for this incident
        ->   the AI picks from that list
        ->   fixed safety checks
        ->   the compartment unlocks
        ->   sensors check what actually happened
```

**The AI never invents medical advice.** It never decides what treatment someone needs. It picks
*which supplies to hand over*, out of a list it was given by an approved protocol. Everything it
picks then has to survive a set of plain, fixed safety checks that the AI cannot argue with.

That boundary is the most important idea in this notebook. Keep it in mind on every page.

---

## What we will build, in order

1. Watch a person choose supplies by hand, and measure how it goes
2. Write the inventory down in Python
3. Make up a lot of emergencies, including unclear ones
4. Build a rule-based cabinet
5. Break it on purpose
6. Train a model that can predict several needs at once
7. Add the fixed safety checks
8. Pick the smallest kit that is still enough
9. Run a whole day, and see who runs out of supplies
10. Read the sensor events
11. Spot misuse and broken sensors
12. Put it all behind seven clickable doors""")

md("""## 1. Setup

We use numpy, pandas, matplotlib and scikit-learn. All four are already installed in Colab.

- **numpy** does maths on lists of numbers.
- **pandas** gives us tables, like a spreadsheet you can write code against.
- **matplotlib** draws the pictures.
- **scikit-learn** has the models we train later on.""")

code('''import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["figure.figsize"] = (11, 4)
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.3
pd.set_option("display.width", 120)

# The seven compartments, in the order they sit in the cabinet.
COMPARTMENTS = ["protective", "bleeding", "burns", "aed", "traffic", "flotation", "comms"]

# A readable name for each one, for printing.
NAMES = {
    "protective": "Protective equipment",
    "bleeding":   "Bleeding supplies",
    "burns":      "Burn supplies",
    "aed":        "AED",
    "traffic":    "Traffic safety",
    "flotation":  "Flotation",
    "comms":      "Communication unit",
}

print(f"{len(COMPARTMENTS)} compartments:")
for c in COMPARTMENTS:
    print(" -", NAMES[c])''')

# ------------------------------------------------------------------ 1. by hand
md("""## 2. First, a person tries it

Before building anything, it is worth seeing how the job goes without help.

Picture someone who has never done this. Seven closed doors, small printed labels, and a
situation they have never been in. They read a label, decide, move to the next one.

We will simulate that person. The simulation is simple on purpose:

- they read the labels in whatever order they happen to look
- each label takes a few seconds to read and think about
- they open a compartment if a word on the label matches a word in what they were told
- they stop once they think they have enough

The important part is the last rule. **Matching words is not the same as knowing what is
needed.** If nobody said the word "gloves", gloves do not get taken.""")

code('''rng_manual = np.random.default_rng(0)

# Which words on a label a person is likely to connect to which compartment.
LABEL_WORDS = {
    "protective": ["gloves", "protect", "barrier"],
    "bleeding":   ["bleeding", "blood", "cut", "wound"],
    "burns":      ["burn", "fire", "scald"],
    "aed":        ["heart", "cardiac", "collapsed", "unresponsive", "aed"],
    "traffic":    ["traffic", "road", "car", "cyclist", "lane"],
    "flotation":  ["water", "river", "pool", "drowning"],
    "comms":      ["call", "speak", "dispatcher", "phone"],
}

SECONDS_PER_LABEL = 6.0      # reading a label and deciding
SECONDS_PER_DOOR = 4.0       # opening a compartment and taking something out


def person_chooses(words_heard, seed):
    """Simulate an untrained person picking supplies. Returns (chosen, seconds)."""
    rng = np.random.default_rng(seed)
    order = list(COMPARTMENTS)
    rng.shuffle(order)                       # they look in no particular order

    chosen, seconds = [], 0.0
    for compartment in order:
        seconds += SECONDS_PER_LABEL
        matched = any(w in words_heard for w in LABEL_WORDS[compartment])
        if matched:
            chosen.append(compartment)
            seconds += SECONDS_PER_DOOR
        # once they have grabbed a couple of things, most people stop looking
        if len(chosen) >= 3 and rng.random() < 0.5:
            break
    return chosen, seconds


heard = ["cyclist", "fallen", "bleeding"]
picked, took = person_chooses(heard, seed=1)
print("They were told :", " ".join(heard))
print("They took      :", [NAMES[c] for c in picked])
print(f"It took        : {took:.0f} seconds")''')

md("""Run that a few times in your head with different people and you can already see the two
problems.

**They take what was said out loud, not what is needed.** Nobody said "gloves", so nobody took
gloves. Nobody said "call", so the communication unit stays in the cabinet.

**They stop early.** Which is reasonable — they are in a hurry — but it means the last few
compartments are never even looked at.

We will come back to these numbers at the end and compare them properly.""")

# ------------------------------------------------------------------ 2. inventory
md("""## 3. Writing the inventory down

Now we tell Python what is in the cabinet.

A **dictionary** in Python is a set of labelled boxes. You put something in under a name, and
later you ask for it back by that name. Here is a tiny one:""")

code('''small_example = {"apples": 4, "pears": 2}

print(small_example["apples"])       # ask for one thing by name
small_example["apples"] = 3          # change it
print(small_example)''')

md("""The cabinet is the same idea, just with a dictionary inside each dictionary. For every
compartment we record:

- `quantity` — how many are on the shelf
- `sealed` — is the package still closed and untouched
- `days_to_expiry` — how many days before it should be thrown away (negative means it is already
  past that date)
- `battery` — only matters for the AED and the communication unit
- `restricted` — some things only open once a dispatcher has confirmed the emergency
- `consumable` — is it used up, or does it come back?

That last one matters more than it looks, so it is worth being clear about the three kinds of
thing in this cabinet:

- **Used up.** Gloves, dressings, burn supplies. Once handed over they are gone.
- **Comes back.** Traffic markers, the float, the defibrillator. Borrowed, then returned — though
  not always, and that is a problem we deal with later.
- **Never leaves.** The communication unit is bolted in. Talking to a dispatcher does not use
  anything up.""")

code('''def fresh_cabinet(seed=7, fill=1.0):
    """Build one cabinet. `fill` scales how full the shelves start, 0 to 1."""
    rng = np.random.default_rng(seed)

    def stock(full):
        return int(round(full * fill))

    return {
        "protective": dict(quantity=stock(24), sealed=True,
                           days_to_expiry=int(rng.integers(300, 900)),
                           battery=None, consumable=True, restricted=False),
        "bleeding":   dict(quantity=stock(10), sealed=True,
                           days_to_expiry=int(rng.integers(200, 800)),
                           battery=None, consumable=True, restricted=False),
        "burns":      dict(quantity=stock(6), sealed=True,
                           days_to_expiry=int(rng.integers(-30, 700)),
                           battery=None, consumable=True, restricted=False),
        "aed":        dict(quantity=1, sealed=True,
                           days_to_expiry=int(rng.integers(200, 600)),
                           battery=int(rng.integers(35, 100)),
                           consumable=False, restricted=True),
        "traffic":    dict(quantity=stock(4), sealed=True,
                           days_to_expiry=9999,
                           battery=None, consumable=False, restricted=False),
        "flotation":  dict(quantity=stock(2), sealed=True,
                           days_to_expiry=9999,
                           battery=None, consumable=False, restricted=False),
        "comms":      dict(quantity=1, sealed=True,
                           days_to_expiry=9999,
                           battery=int(rng.integers(60, 100)),
                           consumable=False, restricted=False),
    }


cabinet = fresh_cabinet()
print("What is in the AED compartment:")
print(cabinet["aed"])''')

md("""A dictionary is easy to write and easy to read, but hard to look at all at once.

A **DataFrame** is a table. Same information, laid out so you can see every compartment side by
side. `pandas` turns the dictionary into one for us.""")

code('''def as_table(cabinet):
    """Turn the cabinet dictionary into a table."""
    table = pd.DataFrame(cabinet).T           # .T flips it so compartments are rows
    table.index.name = "compartment"
    return table


as_table(cabinet)''')

md("""Now a question we can already answer: **is anything in this cabinet unusable right now?**

Three things make an item unusable:

- there are none left
- the package has been opened
- the expiry date has passed""")

code('''def usable(item):
    """True if this item can actually be handed to somebody."""
    return item["quantity"] > 0 and item["sealed"] and item["days_to_expiry"] > 0


for name in COMPARTMENTS:
    item = cabinet[name]
    if usable(item):
        note = "ok"
    elif item["quantity"] <= 0:
        note = "empty"
    elif not item["sealed"]:
        note = "package already opened"
    else:
        note = f"expired {-item['days_to_expiry']} days ago"
    print(f"{NAMES[name]:<22} {note}")''')

md("""Notice that the burn supplies were given an expiry date that is sometimes already in the
past. That was on purpose. A cabinet that assumes everything on its shelves is fine is a cabinet
that will hand somebody an expired package.""")

# ------------------------------------------------------------------ 3. cases
md("""## 4. Making up emergencies

To build anything we need examples. Lots of them.

Here is the part that matters most, and it is worth slowing down for. There are **two different
things** in every emergency:

1. **What is actually happening.** Someone really is bleeding, or really is not.
2. **What the cabinet was told.** A frightened person, describing it in a hurry, on a speaker.

These are not the same, and the gap between them is the whole problem. So the generator makes
the truth first, then makes a report *from* that truth, and damages the report on the way.""")

code('''INCIDENTS = ["road_accident", "fall", "fire", "water", "cardiac", "unclear"]


def make_truth(rng):
    """What is really happening. The cabinet never sees this."""
    incident = INCIDENTS[rng.integers(0, len(INCIDENTS))]

    truth = dict(incident=incident,
                 bleeding=0, unresponsive=0, fire=0, water=0, traffic=0,
                 people=1)

    if incident == "road_accident":
        truth["bleeding"] = int(rng.random() < 0.75)
        truth["traffic"] = 1
        truth["unresponsive"] = int(rng.random() < 0.15)
    elif incident == "fall":
        truth["bleeding"] = int(rng.random() < 0.55)
        truth["traffic"] = int(rng.random() < 0.30)
    elif incident == "fire":
        truth["fire"] = 1
        truth["bleeding"] = int(rng.random() < 0.20)
    elif incident == "water":
        truth["water"] = 1
        truth["unresponsive"] = int(rng.random() < 0.40)
    elif incident == "cardiac":
        truth["unresponsive"] = 1
    else:                                     # unclear: something is wrong, nobody knows what
        truth["bleeding"] = int(rng.random() < 0.35)
        truth["unresponsive"] = int(rng.random() < 0.20)
        truth["fire"] = int(rng.random() < 0.10)
        truth["water"] = int(rng.random() < 0.10)
        truth["traffic"] = int(rng.random() < 0.30)

    truth["people"] = 1 + int(rng.random() < 0.20) + int(rng.random() < 0.06)
    return truth


def make_report(truth, rng):
    """What the cabinet is actually told. Made from the truth, then damaged."""
    report = dict(
        incident=truth["incident"],
        reported_bleeding=truth["bleeding"],
        fire_present=truth["fire"],
        water_incident=truth["water"],
        traffic_hazard=truth["traffic"],
        people_affected=truth["people"],
        person_responsive="no" if truth["unresponsive"] else "yes",
        dispatcher_confirmed=1,
    )

    # A caller who is not sure what they are looking at.
    if rng.random() < 0.25:
        report["incident"] = "unclear"
    # Nobody checks whether a person is breathing unless they are told to.
    if rng.random() < 0.35:
        report["person_responsive"] = "unknown"
    # Standing in the road, people forget to mention the road.
    if truth["traffic"] and rng.random() < 0.30:
        report["traffic_hazard"] = 0
    # Bleeding gets both missed and imagined.
    if rng.random() < 0.10:
        report["reported_bleeding"] = 1 - report["reported_bleeding"]
    # Sometimes the dispatcher has not picked up yet.
    if rng.random() < 0.20:
        report["dispatcher_confirmed"] = 0

    return report''')

md("""Now the other half: **what was actually needed**.

This is the answer key. We work it out from the truth, not from the report, because that is what
"the right answer" means here.

Two of the seven are always needed, and it is worth saying why:

- **Protective equipment.** Anyone helping is about to touch a stranger's blood. Gloves cost
  almost nothing and are useful in every single case.
- **Communication unit.** Getting a trained person on the line helps in every case too.

The other five depend on what is happening.""")

code('''def what_is_needed(truth):
    """The answer key: which compartments this emergency really needed."""
    return {
        "protective": 1,                       # always
        "comms":      1,                       # always
        "bleeding":   truth["bleeding"],
        "aed":        truth["unresponsive"],
        "burns":      truth["fire"],
        "flotation":  truth["water"],
        "traffic":    truth["traffic"],
    }


def make_cases(n, seed=3):
    """Make n emergencies. Returns one table of reports and one of answers."""
    rng = np.random.default_rng(seed)
    reports, answers = [], []
    for _ in range(n):
        truth = make_truth(rng)
        reports.append(make_report(truth, rng))
        answers.append(what_is_needed(truth))
    return pd.DataFrame(reports), pd.DataFrame(answers)[COMPARTMENTS]


reports, answers = make_cases(4000)
print("what the cabinet is told:")
print(reports.head(3).to_string(index=False))
print()
print("what was actually needed (1 = needed):")
print(answers.head(3).to_string(index=False))''')

code('''print("How often each compartment is genuinely needed:")
share = answers.mean().sort_values(ascending=False)
for name, value in share.items():
    print(f"  {NAMES[name]:<22} {value:6.1%}")

print()
print("How many compartments a single emergency needs:")
print(answers.sum(axis=1).value_counts().sort_index().to_string())''')

code('''fig, axes = plt.subplots(1, 2, figsize=(12, 3.6))

share = answers.mean().sort_values()
axes[0].barh([NAMES[n] for n in share.index], 100 * share.to_numpy(), color="#4a7fb5")
axes[0].set_xlabel("% of emergencies that needed it")
axes[0].set_title("How often each compartment is needed")

counts = answers.sum(axis=1).value_counts().sort_index()
axes[1].bar(counts.index.astype(str), counts.to_numpy(), color="#4c9f70")
axes[1].set_xlabel("compartments needed by one emergency")
axes[1].set_ylabel("emergencies")
axes[1].set_title("Almost never just one")

plt.tight_layout(); plt.show()''')

md("""Read the right-hand chart again, because it decides what kind of model we need later.

**Almost no emergency needs only one compartment.** Most need three or four. So the question is
never "which one thing is this" — it is "which of these seven, all at once". That is a different
kind of question, and section 7 is where we deal with it properly.

And look at how often the report is wrong about something:""")

code('''# How often the report disagrees with the truth. We can only do this because we
# made both up ourselves - a real cabinet never gets to check.
rng_check = np.random.default_rng(3)
disagree = {"responsiveness not known": 0, "traffic hazard not mentioned": 0,
            "incident called unclear": 0, "bleeding reported wrongly": 0,
            "no dispatcher yet": 0}

for _ in range(4000):
    truth = make_truth(rng_check)
    report = make_report(truth, rng_check)
    disagree["responsiveness not known"] += report["person_responsive"] == "unknown"
    disagree["traffic hazard not mentioned"] += truth["traffic"] and not report["traffic_hazard"]
    disagree["incident called unclear"] += (report["incident"] == "unclear"
                                           and truth["incident"] != "unclear")
    disagree["bleeding reported wrongly"] += report["reported_bleeding"] != truth["bleeding"]
    disagree["no dispatcher yet"] += report["dispatcher_confirmed"] == 0

for reason, count in disagree.items():
    print(f"  {reason:<32} {count / 4000:5.1%} of calls")''')

md("""None of those are unusual or unlucky. They are what a phone call from a frightened stranger
normally sounds like. Any cabinet that only works on clear descriptions will not work.""")

# ------------------------------------------------------------------ 4. rules
md("""## 5. The rule-based cabinet

Now the first real system. Plain rules, written by hand, in the order a person would think of
them.

This is a good starting point and we are not being rude about it. It is easy to read, easy to
argue about, and anybody can check it. Every system after this has to beat it to earn its
place.""")

code('''def rule_cabinet(report):
    """Decide which compartments to open, using fixed rules. Returns a dict of 0/1."""
    open_now = {c: 0 for c in COMPARTMENTS}

    # Always. Gloves protect the helper, the speaker gets a trained person on the line.
    open_now["protective"] = 1
    open_now["comms"] = 1

    if report["reported_bleeding"]:
        open_now["bleeding"] = 1
    if report["person_responsive"] == "no":
        open_now["aed"] = 1
    if report["fire_present"]:
        open_now["burns"] = 1
    if report["water_incident"]:
        open_now["flotation"] = 1
    if report["traffic_hazard"]:
        open_now["traffic"] = 1

    return open_now


example = reports.iloc[0].to_dict()
print("Report:")
for key, value in example.items():
    print(f"   {key}: {value}")
print()
print("The rules open:", [NAMES[c] for c, v in rule_cabinet(example).items() if v])''')

md("""Now we need a way to say how well any system did. Three numbers, and they mean different
things:

- **Missed** — something was needed and the door stayed shut. This is the bad one.
- **Extra** — a door opened that did not need to. Wastes supplies and slows the person down.
- **Exactly right** — every needed door open, no extra ones.""")

code('''def score_system(opened, answers, name, seconds=None):
    """Compare what a system opened against what was actually needed."""
    opened = np.asarray(opened)
    needed = answers[COMPARTMENTS].to_numpy()

    missed = ((needed == 1) & (opened == 0)).sum()
    extra = ((needed == 0) & (opened == 1)).sum()
    perfect = (((needed == 1) == (opened == 1)).all(axis=1)).mean()
    got_everything = (((needed == 1) <= (opened == 1)).all(axis=1)).mean()

    row = {"System": name,
           "Missed items": int(missed),
           "Extra items": int(extra),
           "Got everything needed": f"{got_everything:.0%}",
           "Exactly right": f"{perfect:.0%}"}
    if seconds is not None:
        row["Seconds"] = round(float(np.mean(seconds)), 1)
    return row


rule_opened = np.array([[rule_cabinet(r)[c] for c in COMPARTMENTS]
                        for r in reports.to_dict("records")])

scoreboard = [score_system(rule_opened, answers, "Rules")]
pd.DataFrame(scoreboard)''')

md("""Hold on to that "missed items" number. Every system from here on gets compared against it.

But the total hides the interesting part. Let us look at where the misses actually are.""")

code('''needed = answers[COMPARTMENTS].to_numpy()

rows = []
for i, name in enumerate(COMPARTMENTS):
    rows.append({"Compartment": NAMES[name],
                 "Missed": int(((needed[:, i] == 1) & (rule_opened[:, i] == 0)).sum()),
                 "Extra": int(((needed[:, i] == 0) & (rule_opened[:, i] == 1)).sum())})

pd.DataFrame(rows).set_index("Compartment")''')

md("""That table is worth more than the total was.

The rules are not uniformly bad. On some compartments they are **perfect** — nothing missed and
nothing extra. On others they fall apart completely.

The difference is not the rule. The rules are all the same shape. The difference is **how
reliable the report is** for that particular thing. Where the caller tells us something clearly,
a plain rule is unbeatable. Where the caller says "I don't know", or forgets to mention it, the
rule has nothing to work with and quietly does nothing.

So the problem is not that rules are too simple. The problem is that a rule needs a clear answer,
and half the time nobody has one.""")

# ------------------------------------------------------------------ 5. breaking
md("""## 6. Breaking the rules on purpose

The rules work on tidy emergencies. Here are seven that are not tidy. Each one is a real
situation, and each one breaks the rulebook in a different way.

We will run all seven and look at what happens.""")

code('''awkward = [
    ("Bleeding, and the person is standing in the road",
     dict(incident="road_accident", reported_bleeding=1, fire_present=0, water_incident=0,
          traffic_hazard=1, people_affected=1, person_responsive="yes", dispatcher_confirmed=1)),

    ("A burn, but the burn shelf is empty",
     dict(incident="fire", reported_bleeding=0, fire_present=1, water_incident=0,
          traffic_hazard=0, people_affected=1, person_responsive="yes", dispatcher_confirmed=1)),

    ("Collapsed person, AED battery is low",
     dict(incident="cardiac", reported_bleeding=0, fire_present=0, water_incident=0,
          traffic_hazard=0, people_affected=1, person_responsive="no", dispatcher_confirmed=1)),

    ("Someone in the water, the float has already been taken",
     dict(incident="water", reported_bleeding=0, fire_present=0, water_incident=1,
          traffic_hazard=0, people_affected=1, person_responsive="unknown",
          dispatcher_confirmed=1)),

    ("Two people hurt, in two different ways",
     dict(incident="road_accident", reported_bleeding=1, fire_present=1, water_incident=0,
          traffic_hazard=1, people_affected=2, person_responsive="unknown",
          dispatcher_confirmed=1)),

    ("The button was pressed by mistake",
     dict(incident="unclear", reported_bleeding=0, fire_present=0, water_incident=0,
          traffic_hazard=0, people_affected=1, person_responsive="yes", dispatcher_confirmed=0)),

    ("Half a sentence, then the caller stops talking",
     dict(incident="unclear", reported_bleeding=0, fire_present=0, water_incident=0,
          traffic_hazard=0, people_affected=1, person_responsive="unknown",
          dispatcher_confirmed=0)),
]

for title, report in awkward:
    opened = [NAMES[c] for c, v in rule_cabinet(report).items() if v]
    print(f"{title}")
    print(f"   rules open: {', '.join(opened)}")
    print()''')

md("""Now go through them one at a time. The rules are not stupid — they are just answering a
smaller question than the one that was asked.

**1. Bleeding in the road.** The rules get this right, and it is worth noticing why it is hard:
two separate things are wrong at once, and each needed a different rule to fire. Add a few more
combinations and the rulebook starts growing quickly.

**2. A burn with an empty shelf.** The rules open the burn compartment. There is nothing in it.
The rules never checked. Nobody told them to.

**3. A low AED battery.** The rules open it. That may well be the right answer — a weak AED is
better than none — but the rules do not know there is anything to think about.

**4. The float is already gone.** Same as 2. The door opens onto an empty shelf, and the person
loses time finding that out.

**5. Two people, two problems.** Here the rules do reasonably. But notice `people_affected` is 2
and nothing in the rulebook looks at it, so one person's worth of supplies comes out.

**6 and 7. Nobody is really there, or nobody has confirmed anything.** The rules open the
protective compartment and the speaker anyway. For a false alarm that is a small waste. The
bigger problem is that the rules have no idea the report is thin — they treat "I don't know" and
"definitely not" as the same thing.

That last one is the important one.""")

code('''# "unknown" and "no" are completely different, and the rulebook cannot tell.
for state in ["yes", "no", "unknown"]:
    report = dict(incident="fall", reported_bleeding=0, fire_present=0, water_incident=0,
                  traffic_hazard=0, people_affected=1, person_responsive=state,
                  dispatcher_confirmed=1)
    opened = [c for c, v in rule_cabinet(report).items() if v]
    print(f"person_responsive = {state:<8} -> AED {'open' if 'aed' in opened else 'stays locked'}")''')

md("""`unknown` and `no` get the same treatment, and they should not.

If we do not know whether someone is breathing, that is not the same as knowing they are fine.
It is a reason to get a person on the line and to be ready — not a reason to do nothing.

To handle that, the cabinet needs something the rulebook does not have: a way of saying **how
likely** each compartment is to be needed, instead of just yes or no. That is what the next
section is for.""")

# ------------------------------------------------------------------ 6. model
md("""## 7. A model that can say "probably"

The rules answer yes or no. We want something that can answer **"probably"**, because half our
reports do not deserve a yes or a no.

### One incident, several answers

Most models pick one answer out of several — cat or dog, spam or not spam. That is not our
problem. Our emergency might need bleeding supplies **and** traffic markers **and** gloves, all
at the same time.

This is called **multi-label**: each case can carry several labels at once. The trick is simple.
Instead of one model choosing between seven compartments, we train **seven small models**, one
per compartment, each answering a single yes-or-no question:

> "For this report, is my compartment needed?"

`scikit-learn` will do the seven-at-once bookkeeping for us.

### First, turn the report into numbers

Models take numbers, not words. `incident` is a word, and `person_responsive` is one of three
words. We turn each word into its own 0-or-1 column. That is called **one-hot encoding**, and
`pandas` has it built in.""")

code('''def to_numbers(reports):
    """Turn the report table into a table of plain numbers a model can read."""
    table = pd.get_dummies(reports, columns=["incident", "person_responsive"])
    # Make sure every possible column exists, even if this batch never saw it.
    wanted = ([f"incident_{i}" for i in INCIDENTS]
              + [f"person_responsive_{s}" for s in ["yes", "no", "unknown"]])
    for column in wanted:
        if column not in table.columns:
            table[column] = 0
    return table.astype(float)


FEATURES = sorted(to_numbers(reports).columns)
X = to_numbers(reports)[FEATURES]

print(f"{len(FEATURES)} columns go into the model:")
print(", ".join(FEATURES))
print()
print(X.head(3).to_string(index=False))''')

md("""### Two compartments do not need a model

Before training anything, look back at the table in section 4 that counted how often each
compartment was needed. Two of them came out at 100%.

Protective equipment and the communication unit are needed in **every single emergency**. There
is nothing to predict. A model trained on that would only ever learn to say "yes", which is a
long way round to get to an answer we already knew.

So we do not model those two. They are a rule: always open, if there is anything in there. Only
the other five get a model.

This is worth doing for real reasons, not tidiness. A model trained on a column that never
changes cannot be tested, cannot be wrong in a useful way, and hides a decision that should be
written down where people can see it.""")

code('''# The two that are always needed. These are a rule, not a prediction.
ALWAYS_OPEN = ["protective", "comms"]

# The five that actually depend on what happened.
MODELLED = [c for c in COMPARTMENTS if c not in ALWAYS_OPEN]

for name in COMPARTMENTS:
    kind = "always open (a rule)" if name in ALWAYS_OPEN else "depends - needs a model"
    print(f"{NAMES[name]:<22} needed {answers[name].mean():6.1%}   {kind}")''')

md("""### Split the data before training anything

We keep some emergencies aside and never train on them. Then we test on those. Without this,
a model can score well simply by memorising, and we would never find out.""")

code('''from sklearn.model_selection import train_test_split

Y = answers[MODELLED]

X_train, X_test, Y_train, Y_test = train_test_split(
    X, Y, test_size=0.30, random_state=42)

print(f"train on {len(X_train)} emergencies, test on {len(X_test)}")
print(f"predicting {len(MODELLED)} compartments: {', '.join(MODELLED)}")''')

md("""### Train three of them

Three different models, all doing the same multi-label job, so we can see whether the choice
matters.

- **Logistic regression** draws a straight dividing line. Simple and quick.
- **Random forest** asks a lot of yes/no questions and lets many small decision trees vote.
- **Decision tree** is a single flowchart. Easy to print out and read.""")

code('''from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.multiclass import OneVsRestClassifier
from sklearn.multioutput import MultiOutputClassifier

models = {
    "Logistic regression": OneVsRestClassifier(LogisticRegression(max_iter=1000)),
    "Random forest": MultiOutputClassifier(
        RandomForestClassifier(n_estimators=200, min_samples_leaf=5, random_state=42)),
    "Decision tree": DecisionTreeClassifier(max_depth=6, min_samples_leaf=20, random_state=42),
}

for name, model in models.items():
    model.fit(X_train, Y_train)
    print(f"trained: {name}")''')

md("""### Getting probabilities out

Each model can give a **probability** for every compartment: a number between 0 and 1 saying how
likely it is that this compartment is needed.

The three model types hand this back in slightly different shapes, so one small helper sorts
that out and gives us the same thing every time.""")

code('''def probabilities(model, X):
    """Return a table of probabilities, one column per compartment.

    The two always-open compartments are filled in at 1.0 by rule. The other
    five come from the model.
    """
    raw = model.predict_proba(X)
    if isinstance(raw, list):
        # random forest and one-vs-rest give a list, one array per compartment
        out = np.column_stack([p[:, 1] for p in raw])
    else:
        out = np.asarray(raw)

    table = pd.DataFrame(out, columns=MODELLED, index=X.index)
    for name in ALWAYS_OPEN:
        table[name] = 1.0
    return table[COMPARTMENTS]


forest = models["Random forest"]
p_test = probabilities(forest, X_test)

# The example from the very top of the notebook.
cyclist = pd.DataFrame([dict(reported_bleeding=1, fire_present=0, water_incident=0,
                             traffic_hazard=1, people_affected=1, dispatcher_confirmed=1,
                             incident="road_accident", person_responsive="unknown")])
cyclist_p = probabilities(forest, to_numbers(cyclist).reindex(columns=FEATURES, fill_value=0.0))

print('"A cyclist has fallen. There is bleeding, but I don\\'t know how serious it is."')
print()
for name, value in cyclist_p.iloc[0].sort_values(ascending=False).items():
    print(f"   {NAMES[name]:<22} {value:.2f}")''')

md("""That is the output we wanted. Not a yes or a no — a **ranking**, with a number attached.

Look at what it does with the AED. Nobody said the person had stopped breathing. Nobody said
they were fine either — the caller said they did not know. The model has learned from past cases
roughly how often "I don't know" turns out to be serious, and gives back a number in between.

The rules could only say `no`. This says `maybe, and here is how much`.

### Which model is best, and do any of them beat the rules?

Now we have to be careful, because it is very easy to run a comparison that is not a comparison.

Two traps, and both are easy to fall into:

1. The rules were scored on **all 4000** emergencies. The models must be scored only on the 1200
   they never saw. Different sets of emergencies are not comparable.
2. The models only predict **five** compartments. The rules decided all **seven**. Counting five
   against seven would flatter the models for free.

So we put everything on the same footing: the same 1200 unseen emergencies, and all seven
compartments, with the two always-open ones filled in by rule for the models as well.""")

code('''def opened_by_model(model, X):
    """What a model would open, all seven compartments, as 0/1."""
    predicted = pd.DataFrame(model.predict(X), columns=MODELLED, index=X.index)
    for name in ALWAYS_OPEN:
        predicted[name] = 1                    # the rule from earlier
    return predicted[COMPARTMENTS].to_numpy()


# The same unseen emergencies for everybody.
test_reports = reports.loc[X_test.index]
test_answers = answers.loc[X_test.index]

rules_on_test = np.array([[rule_cabinet(r)[c] for c in COMPARTMENTS]
                          for r in test_reports.to_dict("records")])

fair = [score_system(rules_on_test, test_answers, "Rules")]
for name, model in models.items():
    fair.append(score_system(opened_by_model(model, X_test), test_answers, name))

pd.DataFrame(fair).set_index("System")''')

code('''best_model = models["Random forest"]
model_opened = opened_by_model(best_model, X_test)
truth_test = test_answers[COMPARTMENTS].to_numpy()

missed_rules = [((truth_test[:, i] == 1) & (rules_on_test[:, i] == 0)).sum()
                for i in range(len(COMPARTMENTS))]
missed_model = [((truth_test[:, i] == 1) & (model_opened[:, i] == 0)).sum()
                for i in range(len(COMPARTMENTS))]

spot = np.arange(len(COMPARTMENTS))
fig, ax = plt.subplots(figsize=(11, 3.8))
ax.bar(spot - 0.2, missed_rules, 0.4, label="rules", color="#c94f4f")
ax.bar(spot + 0.2, missed_model, 0.4, label="random forest", color="#4a7fb5")
ax.set_xticks(spot)
ax.set_xticklabels([NAMES[c] for c in COMPARTMENTS], rotation=25, ha="right")
ax.set_ylabel("times it was needed and stayed shut")
ax.set_title("Where each system misses things, on the same 1200 emergencies")
ax.legend()
plt.tight_layout(); plt.show()''')

md("""The bars show where the improvement came from, and it is not spread evenly at all.

Two compartments have no bars for either system. Those are the ones the caller reports reliably,
and there the plain rules were already perfect. A model cannot improve on perfect.

The gain is concentrated in the compartments where **something was left out** of the report — the
ones the rules could only answer by guessing "no". The model picks those up because the missing
fact is still hinted at elsewhere: somebody who says "road accident" is probably standing near
traffic even if they never say so.

And notice the one compartment where the model is no better, or slightly worse. That is the one
we damaged by **flipping the report at random**. A random flip leaves no trace anywhere else in
the data, so there is nothing for any model to find. Missing information can sometimes be worked
out from context. Wrong information cannot.""")

md("""### Where the model still cannot win

Before we get carried away, one honest check. Some of what we are asking is genuinely
unknowable from the report.

If a caller says "I don't know if they are breathing", then two emergencies that look **exactly
the same on paper** can have different right answers. No model can separate those, because there
is nothing left to separate them with. The information is simply not in the report.

So there is a ceiling, and it is worth knowing roughly where it is.""")

code('''# Group the test cases by their report. Where identical reports had different
# answers, no model could ever have told them apart.
grouped = X_test.copy()
grouped["_key"] = [tuple(r) for r in X_test.to_numpy()]
best_possible = 0
for key, part in grouped.groupby("_key"):
    truth = Y_test.loc[part.index, MODELLED].to_numpy()
    # the best any model can do is answer with the most common label per compartment
    majority = (truth.mean(axis=0) >= 0.5).astype(int)
    best_possible += ((truth == 1) & (majority == 0)).sum()

print(f"identical reports in the test set: {grouped['_key'].duplicated().sum()}")
print(f"items no model could ever get, from the report alone: {best_possible}")''')

# ------------------------------------------------------------------ 7. safety
md("""## 8. The safety checks

Now the most important section in the notebook.

The model has given us seven probabilities. It knows nothing about the shelves. It has never
seen an expiry date. It does not know whether a dispatcher is on the line. It was trained on
what emergencies *need*, and that is all it knows.

So its answer is a **suggestion**, and a suggestion is not allowed to open a door.

Between the suggestion and the lock sits a set of plain, fixed checks. They are ordinary
`if` statements. There is no model in them, and nothing about them is clever. That is on
purpose: you can read them, argue with them, and test them one at a time.

**The checks can only ever take things away.** They never add a compartment the model did not
ask for, and the model can never talk them out of a decision.

### The five states a door can be in""")

code('''# A door is always in exactly one of these five states.
UNLOCKED = "unlocked"        # green  - open it, take what you need
LOCKED = "locked"            # red    - not needed for this emergency
WAITING = "waiting"          # amber  - probably needed, but a person must confirm first
UNAVAILABLE = "unavailable"  # grey   - nothing usable in there
ELSEWHERE = "elsewhere"      # blue   - empty here, but the next cabinet has one

LOW_BATTERY = 25             # percent, below which we warn but still hand it over

for state in [UNLOCKED, LOCKED, WAITING, UNAVAILABLE, ELSEWHERE]:
    print(state)''')

md("""### The checks themselves

Read these in order. Each one has a reason, and the reason matters more than the code.

1. **Is there anything usable in there?** Empty, opened, or expired means the door stays shut and
   says so. Opening a door onto an empty shelf costs the helper time and tells them nothing.
2. **Is another cabinet nearby holding one?** Then say so, instead of just saying no.
3. **Is this item restricted, and has a dispatcher confirmed the emergency?** If not, the door
   waits. It does not refuse, and it does not open — it asks.
4. **Is the battery low?** Hand it over anyway, and raise a restocking flag. A weak defibrillator
   is better than no defibrillator; this is a maintenance problem, not an emergency decision.
5. **Protective equipment always opens** if there is any. Gloves help in every case and harm in
   none.""")

code('''def safety_checks(wanted, cabinet, report, neighbour_has=()):
    """Decide the final state of every door.

    `wanted` is the set of compartments the AI asked for. This function can
    remove them and can change their state. It cannot add a new one, except for
    protective equipment, which is a floor rather than a suggestion.
    """
    states, notes, restock = {}, {}, []

    for name in COMPARTMENTS:
        item = cabinet[name]
        asked_for = name in wanted or name == "protective"

        if not asked_for:
            states[name] = LOCKED
            notes[name] = "not needed for this emergency"
            continue

        # 1. is there anything usable in there
        if not usable(item):
            if item["quantity"] <= 0:
                why = "empty"
            elif not item["sealed"]:
                why = "package already opened"
            else:
                why = "expired"
            restock.append(name)
            # 2. does a neighbour have one
            if name in neighbour_has:
                states[name] = ELSEWHERE
                notes[name] = f"{why} here - the next cabinet has one"
            else:
                states[name] = UNAVAILABLE
                notes[name] = why
            continue

        # 3. restricted items wait for a person
        if item["restricted"] and not report["dispatcher_confirmed"]:
            states[name] = WAITING
            notes[name] = "waiting for the dispatcher to confirm"
            continue

        # 4. low battery is a warning, not a refusal
        states[name] = UNLOCKED
        notes[name] = "open"
        if item["battery"] is not None and item["battery"] < LOW_BATTERY:
            notes[name] = f"open - battery {item['battery']}%, needs replacing"
            restock.append(name)

    return states, notes, restock


# Try it with a cabinet that has problems.
broken = fresh_cabinet(seed=7)
broken["burns"]["quantity"] = 0
broken["aed"]["battery"] = 12
broken["bleeding"]["sealed"] = False

report = dict(incident="fire", reported_bleeding=1, fire_present=1, water_incident=0,
              traffic_hazard=0, people_affected=1, person_responsive="unknown",
              dispatcher_confirmed=0)

states, notes, restock = safety_checks(
    {"bleeding", "burns", "aed", "comms"}, broken, report, neighbour_has={"burns"})

for name in COMPARTMENTS:
    print(f"{NAMES[name]:<22} {states[name]:<12} {notes[name]}")
print()
print("needs restocking:", [NAMES[n] for n in restock])''')

md("""Read the AED line again, because it is the one that shows what these checks are for.

The model was fairly sure the AED might be needed. The shelf has one. It works. And the door
still did not open — because nobody has confirmed what is happening yet.

That is not the model being overruled by a better model. It is the model being overruled by a
rule that a person wrote down in advance, on purpose, for exactly this situation. **The AI
recommends. The fixed checks control the lock.**

The bleeding compartment shows the other half. The model asked for it, the shelf says there is
stock, but the seal is broken. Nobody is handing that to anybody.""")

# ------------------------------------------------------------------ 8. cost
md("""## 9. Choosing the smallest kit that is still enough

We now have probabilities and we know which doors are allowed to open. One question left: out
of the doors we *could* open, which ones *should* we?

Opening everything is not the safe answer, even though it sounds like it. Seven open doors in
front of a frightened person is seven decisions they now have to make.

So we write down what makes a kit good or bad. In words first:

- **Missing something that was needed** is the worst thing that can happen.
- **Handing over something that was not needed** wastes it and slows the person down.
- **Every extra open door** costs a few seconds of reading and choosing.
- **Using the last of something** may leave the next emergency short.
- **Opening something the safety checks said no to** must never happen at all.

Now the same thing as a sum. Each line gets a weight — a number saying how much we care.""")

code('''# The weights. Bigger number = we care more. These are a choice, not a fact,
# and they are written here where anybody can argue with them.
W_MISSING = 10.0      # something needed, door shut
W_DELAY = 0.15        # per extra door, for the seconds it costs
W_SHORTAGE = 3.0      # using up the last of something
W_UNSAFE = 100.0      # opening something the checks refused

print("What the cabinet is trying to avoid, in order:")
for label, weight in [("opening something unsafe", W_UNSAFE),
                      ("missing something needed", W_MISSING),
                      ("leaving the next emergency short", W_SHORTAGE),
                      ("each extra door to read", W_DELAY)]:
    print(f"   {weight:6.2f}   {label}")''')

md("""### Not every door costs the same to open

One weight is missing from that list, and it is the one worth thinking hardest about: what it
costs to hand something over that turns out not to have been needed.

That cannot be a single number, because the seven compartments are nothing like each other.

Handing over a pair of gloves that were not needed costs almost nothing. There are six pairs in
there and they do not expire this week. Handing over **the** defibrillator costs a great deal
more: there is exactly one, it is the only thing in the cabinet that cannot be replaced by
improvising, and taking it out means it is not there for the next call.

So this weight is a small table instead of one number.""")

code('''# What it costs to hand each thing over when it turns out not to have been needed.
# Scarce, single, hard-to-replace things cost more.
COST_IF_UNNEEDED = {
    "protective": 0.2,     # six pairs, cheap, useful anyway
    "comms": 0.2,          # nothing is used up by talking to a dispatcher
    "traffic": 0.8,        # usually comes back afterwards
    "bleeding": 1.0,       # a real supply, used up
    "burns": 1.0,          # a real supply, used up
    "flotation": 1.5,      # only two, and bulky to carry to the wrong place
    "aed": 6.0,            # there is one, and it is the one thing nobody can improvise
}

print("cost of handing this over when it was not needed:")
for name in sorted(COST_IF_UNNEEDED, key=COST_IF_UNNEEDED.get, reverse=True):
    print(f"   {COST_IF_UNNEEDED[name]:4.1f}   {NAMES[name]}")''')

md("""### The cost of one particular kit

`cost_of` takes one possible kit and returns a single number. Lower is better.

The first two lines are the interesting ones. We do not know what was really needed — that is the
whole problem — so we use the probability instead:

- if a compartment is needed with probability `p` and we leave it shut, we expect to be wrong
  `p` of the time
- if it is needed with probability `p` and we open it, we expect it to be unnecessary `1 - p` of
  the time""")

code('''def cost_of(kit, chances, cabinet, allowed, expected_later=None):
    """How bad is this kit? Lower is better.

    kit            - set of compartments we are thinking of opening
    chances        - probability each compartment is needed
    allowed        - what the safety checks will actually permit
    expected_later - how many of each item the rest of the day is likely to want
    """
    expected_later = expected_later or {}
    cost = 0.0

    for name in COMPARTMENTS:
        p = chances[name]
        if name in kit:
            cost += COST_IF_UNNEEDED[name] * (1 - p)      # probably not needed
            cost += W_DELAY                               # one more door to read
            if name not in allowed:
                cost += W_UNSAFE                          # must never happen
            # Only things that get used up can leave the next call short. A
            # borrowed float or defibrillator comes back.
            if cabinet[name]["consumable"]:
                left_after = cabinet[name]["quantity"] - 1
                short_by = expected_later.get(name, 0) - left_after
                if short_by > 0:
                    cost += W_SHORTAGE * short_by
        else:
            cost += W_MISSING * p                         # probably needed, shut anyway

    return cost''')

md("""### Trying every possible kit

There are seven compartments, so there are 2 x 2 x 2 x 2 x 2 x 2 x 2 = **128** possible kits.

128 is a small number. A computer can score all of them and pick the best in well under a
second, and then we *know* it is the best — there is nothing left to check.

That is worth saying plainly, because it is easy to reach for something clever when you do not
need to. Clever search algorithms exist for when you cannot look at every option. Here we can.""")

code('''from itertools import combinations


def best_kit(chances, cabinet, allowed, expected_later=None):
    """Score all 128 possible kits and return the cheapest."""
    best, best_cost = None, np.inf
    for size in range(len(COMPARTMENTS) + 1):
        for kit in combinations(COMPARTMENTS, size):
            c = cost_of(set(kit), chances, cabinet, allowed, expected_later)
            if c < best_cost:
                best, best_cost = set(kit), c
    return best, best_cost


def greedy_kit(chances, cabinet, allowed, expected_later=None):
    """Keep adding whichever single door helps most, and stop when none do."""
    kit, current = set(), cost_of(set(), chances, cabinet, allowed, expected_later)
    while True:
        improvements = [(cost_of(kit | {n}, chances, cabinet, allowed, expected_later), n)
                        for n in COMPARTMENTS if n not in kit]
        if not improvements:
            break
        cheapest, name = min(improvements)
        if cheapest >= current:
            break
        kit, current = kit | {name}, cheapest
    return kit, current


chances = cyclist_p.iloc[0].to_dict()
full = fresh_cabinet()
allowed = set(COMPARTMENTS)

pick, pick_cost = best_kit(chances, full, allowed)
gpick, gcost = greedy_kit(chances, full, allowed)

print("The cyclist call again, with the probabilities from section 7.")
print()
print(f"all 128 checked : {sorted(NAMES[n] for n in pick)}")
print(f"                  cost {pick_cost:.2f}")
print(f"one at a time   : {sorted(NAMES[n] for n in gpick)}")
print(f"                  cost {gcost:.2f}")
print()
print("same answer" if pick == gpick else "different answers")''')

md("""### Watching the kit change as we get less sure

The most useful thing about a cost function is that you can turn one dial and watch the answer
move.

Below we take the same call and slide the AED probability from 0 up to 1, leaving everything else
alone. At some point the cabinet changes its mind and opens the AED door. There is nothing hidden
about where that point is — it is decided by the weights we printed above.""")

code('''def door_opens_above(name, chances, cabinet, allowed):
    """The lowest probability at which this door starts opening."""
    for p in np.linspace(0, 1, 201):
        trial = dict(chances)
        trial[name] = p
        kit, _ = best_kit(trial, cabinet, allowed)
        if name in kit:
            return p
    return None


print("How sure the cabinet has to be before each door opens:")
for name in sorted(COMPARTMENTS, key=lambda n: COST_IF_UNNEEDED[n]):
    point = door_opens_above(name, {**chances, name: 0.0}, full, allowed)
    shown = f"{point:.0%}" if point is not None else "never on chance alone"
    print(f"   {NAMES[name]:<22} opens above {shown:>22}   "
          f"(costs {COST_IF_UNNEEDED[name]} if unneeded)")''')

md("""None of those numbers were typed in by anybody. Every one of them falls out of the weights.

Read the column on the right next to the column in the middle. The more it costs to hand
something over needlessly, the surer the cabinet has to be before it opens that door. Gloves
open on almost any suspicion. The defibrillator does not.

That is exactly the behaviour we wanted at the top of the notebook — *do not guess aggressively*
— and we got it without writing a single rule that says so. It came out of writing down what we
care about.

That is the real reason to write the cost down instead of hiding it in a chain of `if`
statements: **the trade-off becomes something you can see, argue about, and change on
purpose.**""")

# ------------------------------------------------------------------ 9. the day
md("""## 10. A whole day, and five cabinets

Everything so far looked at one emergency on its own. A real cabinet does not get that luxury.
It gets a whole day, it starts with a fixed number of things on the shelf, and nobody comes to
refill it between calls.

So we run a day. Five cabinets in different places, emergencies arriving through the day, and
three different ways of deciding.

- **Strategy A — open everything that might help.** Sounds generous. Watch what it does to the
  shelves.
- **Strategy B — open the nearest matching kit.** The plain rulebook from section 5.
- **Strategy C — the smallest kit that is still enough**, using the model, the safety checks and
  the cost function, and looking at what the rest of the day will probably need.

Strategy C is the only one that knows the day is not over.""")

code('''N_CABINETS = 5
EMERGENCIES_PER_DAY = 100


def expected_rest_of_day(done, total, share):
    """Roughly how many more of each used-up item today's remaining calls want."""
    calls_left = max(0, total / N_CABINETS - done)
    return {name: share[name] * calls_left for name in COMPARTMENTS}


def what_is_allowed(cabinet, report):
    """The compartments there is any point asking for.

    Only physical availability is checked here. Whether a restricted item is
    allowed to open yet is NOT decided at this step - the AI is still allowed to
    ask for it, and the safety checks turn that request into a `waiting` door.
    Filtering it out here instead would mean the cabinet could never ask.
    """
    return {n for n in COMPARTMENTS if usable(cabinet[n])}


def run_day(strategy, seed=11, fill=1.0):
    """Run one whole day across five cabinets. Returns a log of what happened."""
    rng = np.random.default_rng(seed)
    cabinets = [fresh_cabinet(seed=20 + i, fill=fill) for i in range(N_CABINETS)]
    handled = [0] * N_CABINETS
    share = answers.mean().to_dict()
    log = []

    for _ in range(EMERGENCIES_PER_DAY):
        truth = make_truth(rng)
        report = make_report(truth, rng)
        need = what_is_needed(truth)
        which = int(rng.integers(0, N_CABINETS))
        cabinet = cabinets[which]

        # what the neighbours could supply
        neighbour_has = {n for n in COMPARTMENTS
                         for j, other in enumerate(cabinets)
                         if j != which and usable(other[n])}

        if strategy == "A":
            wanted = set(COMPARTMENTS)
        elif strategy == "B":
            wanted = {n for n, v in rule_cabinet(report).items() if v}
        else:
            row = to_numbers(pd.DataFrame([report])).reindex(columns=FEATURES, fill_value=0.0)
            chances = probabilities(forest, row).iloc[0].to_dict()
            wanted, _ = best_kit(chances, cabinet, what_is_allowed(cabinet, report),
                                 expected_rest_of_day(handled[which], EMERGENCIES_PER_DAY, share))

        states, notes, restock = safety_checks(wanted, cabinet, report, neighbour_has)
        opened = [n for n in COMPARTMENTS if states[n] == UNLOCKED]

        # Used-up things leave the shelf. Borrowed things mostly come back, and
        # the communication unit never leaves at all.
        for name in opened:
            if cabinet[name]["consumable"]:
                cabinet[name]["quantity"] -= 1
            elif name != "comms" and rng.random() > 0.85:
                cabinet[name]["quantity"] -= 1        # borrowed and not returned

        handled[which] += 1
        log.append(dict(
            cabinet=which,
            missed=sum(1 for n in COMPARTMENTS if need[n] and states[n] != UNLOCKED),
            extra=sum(1 for n in COMPARTMENTS if not need[n] and states[n] == UNLOCKED),
            doors=len(opened),
            fully_supplied=all(states[n] == UNLOCKED for n in COMPARTMENTS if need[n]),
            waiting=sum(1 for n in COMPARTMENTS if states[n] == WAITING),
            restock=len(restock),
        ))

    left = sum(max(0, c[n]["quantity"]) for c in cabinets for n in COMPARTMENTS)
    return pd.DataFrame(log), left


STRATEGIES = [("A", "A - open everything"),
              ("B", "B - the rulebook"),
              ("C", "C - smallest sufficient kit")]


FILLS = [1.0, 0.7, 0.5, 0.3]

# Run every combination once and keep the results. Each run searches all 128
# kits for 100 emergencies, so doing this once instead of per-table matters.
days = {(strategy, fill): run_day(strategy, fill=fill)
        for strategy, _ in STRATEGIES for fill in FILLS}


def day_table(fill):
    rows = []
    for strategy, label in STRATEGIES:
        log, left = days[(strategy, fill)]
        rows.append({
            "Strategy": label,
            "Emergencies fully supplied": f"{log.fully_supplied.mean():.0%}",
            "Items missed": int(log.missed.sum()),
            "Handed over unnecessarily": int(log.extra.sum()),
            "Doors per call": round(log.doors.mean(), 1),
            "Items left at the end": int(left),
        })
    return pd.DataFrame(rows).set_index("Strategy")


print("Cabinets starting full")
day_table(1.0)''')

md("""### Now start the cabinets half empty

The table above is a cabinet that was restocked this morning. That is the easy case, and it is
worth noticing how little difference the clever strategy makes there. When there is plenty of
everything, being careful about supplies buys you nothing, because nothing is scarce.

A real cabinet is often not like that. It sits on a wall for weeks, gets used, and is refilled
on somebody's round. So let us run exactly the same day again with the shelves starting at half,
and then at a third.""")

code('''for fill in [0.5, 0.3]:
    print(f"Cabinets starting at {fill:.0%}")
    print(day_table(fill).to_string())
    print()''')

code('''fig, ax = plt.subplots(figsize=(11, 3.8))
for (strategy, label), colour in zip(STRATEGIES, ["#c94f4f", "#e0a458", "#4c9f70"]):
    supplied = [100 * days[(strategy, fill)][0].fully_supplied.mean() for fill in FILLS]
    ax.plot([100 * f for f in FILLS], supplied, "-o", lw=2.2, color=colour, label=label)
ax.set_xlabel("how full the cabinets started (%)")
ax.set_ylabel("emergencies fully supplied (%)")
ax.set_title("The same day, at five different stock levels")
ax.legend()
plt.tight_layout(); plt.show()''')

md("""### Reading those tables

Take strategy A first, at every stock level. It opens every door on every call, so on paper it
should never miss a thing. Look at whether it actually manages that, and look at what it does to
the last column.

That is the first lesson, and it is the one people find least obvious. **Being generous is not
the safe option.** Every item handed over unnecessarily in the morning is an item that is not
there in the afternoon, and nobody refills the cabinet between emergencies.

Now compare B and C, and compare them **across** the three tables rather than inside one. This is
the part of the notebook where the result is more interesting than the one we were hoping for.

B and C see the same shelves and the same emergencies. C knows two extra things: how sure it is,
and how much of the day is still to come. So C should win. Read the three tables and check
whether it does.

What comes out is a middle band, and the chart above shows it more clearly than the tables do.
Follow the green line and the amber line and watch where they separate:

- **Full shelves.** The two lines meet. C has nothing to gain, because there is plenty of
  everything and being careful only saves things nobody was going to need. B is just as good and
  opens fewer doors.
- **Partly stocked.** The lines pull apart, and C is on top. This is where knowing what is left
  and what the rest of the day will want is actually worth something.
- **Nearly empty.** The lines cross back over. Nothing helps any more — there are not enough
  supplies for the day whatever order you hand them out in — and now C's habit of opening a few
  extra doors is a liability rather than a hedge.

So the honest summary is: **the clever strategy earns its place when supplies are tight but not
hopeless.** That is a narrower claim than "the AI wins", and it is the one the numbers support.

It is also the more useful claim. If you are deciding whether to build this, the question is not
"is the AI better" — it is "are my cabinets in the middle band". If they are always full, save
your money and use the rulebook.""")

# ------------------------------------------------------------------ 10. events
md("""## 11. What the sensors saw

Deciding to unlock a door is not the end of the job. The cabinet then has to find out **what
actually happened**, because quite often it is not what was supposed to happen.

Each compartment has sensors: a door switch, a weight pad, a seal check, a docking contact. Every
time one of them changes, the cabinet writes a line in a log with the time on it.

Here is what one call looks like.""")

code('''def make_events(start="10:42:00"):
    """A list of (time, compartment, what happened) for one call."""
    base = pd.Timestamp(f"2026-05-14 {start}")
    raw = [
        (1,  None,          "cabinet activated"),
        (4,  "protective",  "unlocked"),
        (7,  "protective",  "item removed"),
        (9,  "bleeding",    "unlocked"),
        (12, "bleeding",    "item removed"),
        (14, "traffic",     "unlocked"),
        (16, "burns",       "unlocked"),
        (19, "traffic",     "item removed"),
        (25, "aed",         "door forced"),
        (25, None,          "warning issued"),
        (27, "aed",         "item removed"),
        (31, "comms",       "unlocked"),
        (33, "comms",       "in use"),
        (95, "bleeding",    "seal broken"),
        (783, "traffic",    "item returned"),
    ]
    return pd.DataFrame([{"time": base + pd.Timedelta(seconds=s),
                          "compartment": c, "event": e} for s, c, e in raw])


events = make_events()
shown = events.copy()
shown["time"] = shown["time"].dt.strftime("%H:%M:%S")
shown["compartment"] = shown["compartment"].fillna("-")
print(shown.to_string(index=False))''')

md("""Now read the log the way the cabinet has to: one line at a time, with no idea what is coming
next.

Four things in there are worth noticing, and only one of them is obvious.

The **forced AED door** is the obvious one. That compartment was never unlocked, somebody pulled
it open anyway, and two seconds later the defibrillator left the cabinet. The warning went out in
the same second the door moved.

The **traffic markers came back thirteen minutes later**, which is exactly what should happen.
Borrowed, used, returned.

The **burn compartment was unlocked and nothing was taken out of it.** Nobody did anything wrong.
It just means we opened a door that was not needed, and that door is now sitting open.

And the quiet one: **the bleeding compartment's seal broke at 95 seconds**, long after the item
was taken. That is not a person doing anything wrong either. It is a package left open on the
pavement, and it means what is left in that compartment is no longer sealed.""")

code('''def read_events(events):
    """Work out what the cabinet should conclude from one call's events."""
    findings = []
    unlocked, removed, returned = set(), set(), set()

    for row in events.itertuples():
        what, where = row.event, row.compartment
        if what == "unlocked":
            unlocked.add(where)
        elif what == "item removed":
            removed.add(where)
            if where not in unlocked:
                findings.append((where, "something was taken from a door that never unlocked"))
        elif what == "door forced":
            findings.append((where, "door opened without being unlocked"))
        elif what == "seal broken":
            findings.append((where, "package no longer sealed - mark unusable"))
        elif what == "item returned":
            returned.add(where)

    # unlocked, but nobody took anything
    for name in unlocked - removed:
        if name != "comms":
            findings.append((name, "unlocked but nothing was taken - relock it"))

    return findings


for where, note in read_events(events):
    print(f"{NAMES.get(where, where):<22} {note}")''')

md("""One of those lines is the cabinet tidying up after itself, and it is easy to skip past.

**"Unlocked but nothing was taken."** The cabinet opened a door and the person never used it.
That is not an emergency, but it is information: that compartment is now sitting open on a wall,
and it should be locked again. It is also a small sign that we opened a door we did not need to.

The other thing the log gives us is what to put on the restocking list, and which returnable
items never came back.""")

code('''def outstanding(events, after_seconds=600):
    """Borrowed things that have not come back yet."""
    out = []
    taken = set(events[events.event == "item removed"].compartment.dropna())
    back = set(events[events.event == "item returned"].compartment.dropna())
    for name in sorted(taken - back):
        if not fresh_cabinet()[name]["consumable"]:
            out.append(name)
    return out


print("used up, add to the restocking list:")
for name in sorted(set(events[events.event == "item removed"].compartment.dropna())):
    if fresh_cabinet()[name]["consumable"]:
        print("  ", NAMES[name])

print()
print("borrowed and not yet returned:")
for name in outstanding(events):
    print("  ", NAMES[name])''')

# ------------------------------------------------------------------ 11. anomaly
md("""## 12. Misuse, and sensors that lie

The last section trusted the sensors. This one does not.

Two different things can go wrong, and it is worth keeping them apart:

- **Somebody misuses the cabinet.** Forcing a door, emptying a shelf, walking off with the
  defibrillator.
- **A sensor stops telling the truth.** A weight pad that has drifted, a door switch that is
  stuck, a count that never changes.

The second is easy to miss, because a broken sensor does not look broken. It looks like a cabinet
where nothing ever happens.

### First, the things we can just check

Some of these do not need a model at all. If the weight changed while the door sensor says the
door was shut, one of those two sensors is wrong. That is not a judgement call — it is
arithmetic.""")

code('''def sensor_rules(reading):
    """Plain checks on one set of sensor readings. Returns a list of problems."""
    problems = []

    if reading["weight_change_g"] != 0 and not reading["door_open"]:
        problems.append("weight changed while the door was shut")
    if reading["items_taken"] > 0 and reading["count_change"] == 0:
        problems.append("something was taken but the count did not move")
    if reading["returned_weight_g"] > 0 and reading["returned_weight_g"] < 0.7 * reading["expected_weight_g"]:
        problems.append("what came back is lighter than what went out")
    if reading["seconds_unchanged"] > 7 * 24 * 3600:
        problems.append("this sensor has not moved in a week")
    if reading["items_taken"] > 3:
        problems.append("a lot taken at once")

    return problems


examples = [
    dict(name="a normal call", weight_change_g=-120, door_open=True, items_taken=1,
         count_change=-1, returned_weight_g=0, expected_weight_g=0, seconds_unchanged=300),
    dict(name="weight moved, door shut", weight_change_g=-340, door_open=False, items_taken=0,
         count_change=0, returned_weight_g=0, expected_weight_g=0, seconds_unchanged=120),
    dict(name="taken, but the count did not move", weight_change_g=-95, door_open=True,
         items_taken=1, count_change=0, returned_weight_g=0, expected_weight_g=0,
         seconds_unchanged=60),
    dict(name="an empty box came back", weight_change_g=0, door_open=True, items_taken=0,
         count_change=0, returned_weight_g=300, expected_weight_g=1400, seconds_unchanged=90),
    dict(name="nothing for nine days", weight_change_g=0, door_open=False, items_taken=0,
         count_change=0, returned_weight_g=0, expected_weight_g=0, seconds_unchanged=9 * 86400),
    dict(name="somebody emptied the shelf", weight_change_g=-1400, door_open=True, items_taken=6,
         count_change=-6, returned_weight_g=0, expected_weight_g=0, seconds_unchanged=45),
]

for reading in examples:
    found = sensor_rules(reading)
    print(f"{reading['name']:<36} {'; '.join(found) if found else 'looks normal'}")''')

md("""Those checks are good, and you should always write them first. They cost nothing, they never
surprise you, and every one of them can be explained to somebody in a sentence.

But they only catch what somebody thought of in advance.

### Now the things nobody wrote a rule for

An **isolation forest** finds unusual readings without being told what unusual means.

The idea is easier than the name. Split the data at random, over and over. A reading sitting in
the middle of the crowd takes a lot of random splits to separate from its neighbours. A reading
out on its own gets separated almost immediately. So **how quickly a reading can be split off
from the rest** is a measure of how unusual it is.

The important part is what we train it on: **normal days only.** We never show it a single
example of misuse. It learns what ordinary looks like, and then we ask it what does not fit.""")

code('''from sklearn.ensemble import IsolationForest

SENSOR_COLUMNS = ["weight_change_g", "items_taken", "seconds_open", "hour", "count_change"]

# A cabinet is busy in the daytime and almost never touched at night.
HOUR_WEIGHTS = np.array([1, 1, 1, 1, 1, 2, 4, 8, 12, 13, 13, 13, 13,
                         13, 13, 13, 12, 11, 9, 7, 5, 3, 2, 1], dtype=float)
HOUR_WEIGHTS = HOUR_WEIGHTS / HOUR_WEIGHTS.sum()


def normal_days(n, seed=5):
    """Ordinary cabinet use. No misuse in here at all."""
    rng = np.random.default_rng(seed)
    hour = rng.choice(np.arange(24), size=n, p=HOUR_WEIGHTS)
    taken = rng.choice([1, 2, 3], size=n, p=[0.65, 0.28, 0.07])
    return pd.DataFrame({
        "weight_change_g": -taken * rng.normal(120, 18, n),
        "items_taken": taken,
        "seconds_open": rng.gamma(6, 6, n) + 8,
        "hour": hour,
        "count_change": -taken,
    })


train_normal = normal_days(4000)
watch_normal = normal_days(800, seed=6)          # more normal days, to set the line

detector = IsolationForest(n_estimators=300, contamination="auto",
                           random_state=42).fit(train_normal[SENSOR_COLUMNS])


def strangeness(frame):
    """Higher = more unusual. sklearn returns the opposite sign, so we flip it."""
    return -detector.score_samples(frame[SENSOR_COLUMNS])


normal_scores = strangeness(watch_normal)
for allowed_false_alarms in [0.05, 0.01]:
    line = float(np.quantile(normal_scores, 1 - allowed_false_alarms))
    print(f"willing to accept {allowed_false_alarms:.0%} false alarms "
          f"-> flag anything above {line:.3f}")

LINE = float(np.quantile(normal_scores, 0.95))''')

md("""That choice matters more than the model does.

We did not pick the cut-off by trying numbers until the answers looked good. We picked it by
saying **how many false alarms we are willing to live with** on days we know were fine, and then
reading off whatever number that turns out to be. A cabinet that cries wolf gets ignored, so
somebody should make that decision on purpose.

We will use the more forgiving line, and accept the false alarms that come with it.

Now some odd days it has never seen.""")

code('''odd_days = pd.DataFrame([
    dict(what="somebody emptied the shelf", weight_change_g=-1400, items_taken=6,
         seconds_open=44, hour=14, count_change=-6),
    dict(what="a busy-hour amount, at three in the morning", weight_change_g=-360,
         items_taken=3, seconds_open=30, hour=3, count_change=-3),
    dict(what="door left open twenty minutes", weight_change_g=-120, items_taken=1,
         seconds_open=1200, hour=15, count_change=-1),
    dict(what="weight moved, count did not", weight_change_g=-260, items_taken=2,
         seconds_open=30, hour=11, count_change=0),
    dict(what="an ordinary call", weight_change_g=-125, items_taken=1,
         seconds_open=33, hour=13, count_change=-1),
])

odd_days["strangeness"] = strangeness(odd_days).round(3)
odd_days["forest"] = np.where(odd_days.strangeness > LINE, "flagged", "looks normal")
odd_days[["what", "strangeness", "forest"]]''')

md("""Check the last row before anything else. **An ordinary call has to come out as ordinary.** A
detector that flags everything is not a detector, and this one passes that test.

Now look at the rest, and notice that it misses several of them. That is not a mistake in the
code. It is worth understanding, because it is a property of this kind of model that surprises
people.

### Why it misses the obvious ones

An isolation forest splits **inside the range of values it has already seen.** During training it
never saw more than three items taken at once, so every split it ever learned to make on that
column falls somewhere between one and three.

Now hand it a day where six items were taken. There is no split that separates six from three,
because no such split was ever created. The reading simply follows the same branch as the largest
normal days and ends up nearby.

So the pattern is:

- **Unusual combinations of ordinary values** — the sort of thing nobody would write a rule for —
  are what it is good at.
- **The same thing, but much more of it** is what it is worst at. And that is most of what
  actually goes wrong with a cabinet.

### So which one should you use?

Let us actually measure it, rather than assume.""")

code('''def rules_on_reading(row):
    """The plain checks from earlier, applied to one row of sensor readings."""
    problems = []
    if row["items_taken"] > 3:
        problems.append("a lot taken at once")
    if row["seconds_open"] > 300:
        problems.append("door left open a long time")
    if row["items_taken"] > 0 and row["count_change"] == 0:
        problems.append("something was taken but the count did not move")
    if row["hour"] < 5 and row["items_taken"] > 1:
        problems.append("several items in the middle of the night")
    return problems


compare = odd_days.copy()
# The last row is a normal day. Being ignored is the right answer for it.
compare["really wrong"] = [True, True, True, True, False]
compare["rules"] = ["caught" if rules_on_reading(r) else "missed"
                    for _, r in odd_days.iterrows()]

verdicts = []
for _, row in compare.iterrows():
    spotted = row["forest"] == "flagged" or row["rules"] == "caught"
    if row["really wrong"]:
        verdicts.append("caught" if spotted else "MISSED BY BOTH")
    else:
        verdicts.append("false alarm" if spotted else "correctly ignored")
compare["result"] = verdicts

compare[["what", "really wrong", "rules", "forest", "result"]]''')

md("""Read the last column first, then the two before it.

The plain `if` statements do most of the work here. They are the ones catching the faults that
actually happen, and every one of them can be explained to somebody in a single sentence.

That is the honest conclusion of this section, and it is not the one people expect: **for this
problem, the simple thing is better.** The forest earns a place as a backstop, for the odd
combinations nobody wrote down — but it is not the main defence, and building it first would have
been a mistake.

The general lesson is worth more than the cabinet. Reach for the simple check first, measure it,
and only add the model where the measurement shows a gap. Doing it the other way round gives you
something impressive that catches less.""")

# ------------------------------------------------------------------ 12. the cabinet
md("""## 13. The whole cabinet, in one function

Everything so far has been a piece. Here they are joined up, in the order from the top of the
notebook, with nothing skipped.

Read the function slowly. The order of the four steps **is** the design.""")

code('''def cabinet_decides(report, cabinet, neighbour_has=(), expected_later=None):
    """The whole thing, start to finish.

    1. the model says how likely each compartment is to be needed
    2. the safety checks say what is allowed at all
    3. the cost function picks the smallest kit worth opening
    4. the safety checks run again on that kit, and get the last word
    """
    row = to_numbers(pd.DataFrame([report])).reindex(columns=FEATURES, fill_value=0.0)
    chances = probabilities(forest, row).iloc[0].to_dict()          # 1

    allowed = what_is_allowed(cabinet, report)                      # 2
    kit, _ = best_kit(chances, cabinet, allowed, expected_later)    # 3

    # Also work out what it would have asked for if every shelf were full.
    # Without this, a compartment that is needed but empty comes back saying
    # "not needed for this emergency", which is a very different statement.
    ideal, _ = best_kit(chances, cabinet, set(COMPARTMENTS), expected_later)

    states, notes, restock = safety_checks(kit | ideal, cabinet, report,   # 4
                                           neighbour_has)
    return chances, states, notes, restock


def show_cabinet(report, cabinet, neighbour_has=()):
    chances, states, notes, restock = cabinet_decides(report, cabinet, neighbour_has)
    order = {UNLOCKED: 0, WAITING: 1, ELSEWHERE: 2, UNAVAILABLE: 3, LOCKED: 4}
    mark = {UNLOCKED: "OPEN    ", WAITING: "WAITING ", ELSEWHERE: "NEXT ONE",
            UNAVAILABLE: "EMPTY   ", LOCKED: "locked  "}

    for name in sorted(COMPARTMENTS, key=lambda n: (order[states[n]], -chances[n])):
        print(f"  {mark[states[name]]}  {NAMES[name]:<22} "
              f"chance needed {chances[name]:.2f}   {notes[name]}")
    if restock:
        print("  restock:", ", ".join(NAMES[n] for n in restock))


print('"A cyclist has fallen. There is bleeding, but I don\\'t know how serious it is."')
print()
show_cabinet(dict(incident="road_accident", reported_bleeding=1, fire_present=0,
                  water_incident=0, traffic_hazard=1, people_affected=1,
                  person_responsive="unknown", dispatcher_confirmed=1),
             fresh_cabinet())''')

md("""### The cabinet, drawn

Seven doors, in the five colours from the start of this section. This is what somebody standing
in front of the cabinet would see.""")

code('''from matplotlib.patches import Rectangle

DOOR_COLOURS = {
    UNLOCKED:    ("#4c9f70", "OPEN"),
    LOCKED:      ("#c94f4f", "locked"),
    WAITING:     ("#e0a458", "WAITING"),
    UNAVAILABLE: ("#9aa0a6", "empty"),
    ELSEWHERE:   ("#4a7fb5", "NEXT CABINET"),
}


def draw_cabinet(report, cabinet, neighbour_has=(), title=""):
    """Draw the seven doors, coloured by what the cabinet decided."""
    chances, states, notes, _ = cabinet_decides(report, cabinet, neighbour_has)

    fig, ax = plt.subplots(figsize=(11.5, 3.4))
    for i, name in enumerate(COMPARTMENTS):
        colour, word = DOOR_COLOURS[states[name]]
        x = i * 1.05
        ax.add_patch(Rectangle((x, 0), 1.0, 2.0, facecolor=colour, edgecolor="#2b2b2b", lw=1.5))
        ax.text(x + 0.5, 1.62, word, ha="center", va="center", color="white",
                fontsize=9, fontweight="bold")
        ax.text(x + 0.5, 1.15, NAMES[name].replace(" ", "\\n"), ha="center", va="center",
                color="white", fontsize=8.5)
        ax.text(x + 0.5, 0.35, f"chance {chances[name]:.2f}", ha="center", va="center",
                color="white", fontsize=8)

    ax.set_xlim(-0.1, len(COMPARTMENTS) * 1.05)
    ax.set_ylim(-0.1, 2.1)
    ax.axis("off")
    ax.set_title(title, fontsize=11)
    plt.tight_layout(); plt.show()


draw_cabinet(dict(incident="road_accident", reported_bleeding=1, fire_present=0,
                  water_incident=0, traffic_hazard=1, people_affected=1,
                  person_responsive="unknown", dispatcher_confirmed=1),
             fresh_cabinet(),
             title="A cyclist has fallen. There is bleeding, but I don't know how serious it is.")''')

md("""That is the answer from the top of the notebook, and now every part of it can be traced back
to something.

Now the case the whole project exists for. Somebody has collapsed and is not responding, so the
defibrillator is very likely to be needed — but **nobody has picked up at the dispatcher yet**.
The AED is the one restricted item in the cabinet.""")

code('''waiting_call = dict(incident="cardiac", reported_bleeding=0, fire_present=0,
                    water_incident=0, traffic_hazard=0, people_affected=1,
                    person_responsive="no", dispatcher_confirmed=0)

show_cabinet(waiting_call, fresh_cabinet())
draw_cabinet(waiting_call, fresh_cabinet(),
             title="Somebody has collapsed. No dispatcher on the line yet.")''')

md("""Look at the AED line. The model is as sure as it ever gets. The shelf has one. It works.

And the door still did not open. It also did not refuse — it says **waiting**. The cabinet has
asked a person, and until that person answers, it is holding.

Everything else carried on as normal. The protective compartment opened, because gloves help
whatever is happening and cost nothing to be wrong about.

That is what "do not guess aggressively" looks like once it is written down as code: **do the
harmless useful things immediately, and ask about the serious one.**

### Try it yourself

The sliders below let you build any call you like and watch the doors change.""")

code('''try:
    import ipywidgets as widgets
    from IPython.display import display
    HAVE_WIDGETS = True
except Exception:
    HAVE_WIDGETS = False


def try_it(incident="road_accident", bleeding=True, fire=False, water=False,
           traffic=True, responsive="unknown", people=1, dispatcher=True, stock=1.0):
    report = dict(incident=incident, reported_bleeding=int(bleeding),
                  fire_present=int(fire), water_incident=int(water),
                  traffic_hazard=int(traffic), people_affected=people,
                  person_responsive=responsive, dispatcher_confirmed=int(dispatcher))
    show_cabinet(report, fresh_cabinet(fill=stock))


if HAVE_WIDGETS:
    widgets.interact(
        try_it,
        incident=widgets.Dropdown(options=INCIDENTS, value="road_accident"),
        bleeding=widgets.Checkbox(value=True, description="bleeding reported"),
        fire=widgets.Checkbox(value=False, description="fire"),
        water=widgets.Checkbox(value=False, description="water"),
        traffic=widgets.Checkbox(value=True, description="traffic hazard"),
        responsive=widgets.Dropdown(options=["yes", "no", "unknown"], value="unknown"),
        people=widgets.IntSlider(min=1, max=4, value=1, description="people"),
        dispatcher=widgets.Checkbox(value=True, description="dispatcher confirmed"),
        stock=widgets.FloatSlider(min=0.1, max=1.0, step=0.1, value=1.0, description="stock"),
    )
else:
    print("(ipywidgets is not available here - call try_it(...) with your own values instead)")
    try_it(incident="cardiac", bleeding=False, traffic=False, responsive="unknown",
           dispatcher=False)''')

# ------------------------------------------------------------------ 13. limits
md("""## 14. What this would get wrong

An honest list. A cabinet that hands equipment to a frightened stranger deserves a harder look
than a demo usually gets.

**The data is invented.** Every emergency on these pages came from the generator in section 4,
written by somebody who already knew what the analysis should find. Real calls go wrong in ways
nobody thought to simulate.

**The answer key was invented too, and that is worse.** We decided that a fire means burn
supplies and an unresponsive person means the AED. Those are our rules, written into the data,
and then a model learned them back. That is a circle. In real life the answer key would come from
approved medical protocols, and it would not always agree with us.

**We never tested it on a real cabinet.** Sensors drift, doors jam in cold weather, and a weight
pad with a puddle on it reports confident nonsense.

**The weights in section 9 are a value judgement.** We decided the defibrillator costs six times
more to hand over needlessly than a dressing does. Somebody could reasonably pick a different
number and get a different cabinet. That number should be signed off by the people responsible
for the service, not chosen by whoever wrote the notebook.

**One cabinet, one emergency at a time.** Two emergencies at the same cabinet at the same moment
would confuse everything here.

**People are not in the model.** A person who is panicking takes the wrong thing, takes four of
them, or freezes and takes nothing. None of that is represented.

**And the boundary that does not move:** this system chooses *supplies*, from a list an approved
protocol allows. It never decides what treatment somebody needs. If you build the real thing,
keep that line exactly where it is, and get the whole thing approved by the people whose job that
is.""")

# ------------------------------------------------------------------ 14. exercises
md("""## 15. Your turn

1. **Change what you care about.** In section 9, set the cost of handing over the AED needlessly
   to `1.0`, the same as a dressing. Re-run the threshold table. How sure does the cabinet now
   have to be before it opens that door, and is that a cabinet you would want on your wall?

2. **Take the gloves away.** Set `protective` to `quantity=0` in `fresh_cabinet` and run
   `show_cabinet`. What does the cabinet say? Should it stop the person from helping at all?

3. **Make the caller vaguer.** In `make_report`, raise the chance of `person_responsive` becoming
   `"unknown"` from 0.35 to 0.8. Re-run section 7. Which compartment suffers most, and why that
   one?

4. **Add an eighth compartment.** Say, a blanket for someone in shock. What has to change:
   `COMPARTMENTS`, `what_is_needed`, `fresh_cabinet`, `COST_IF_UNNEEDED`. How many possible kits
   are there now?

5. **Break a sensor slowly.** In section 12, add a drift of 2 grams per day to
   `weight_change_g`. How many days before the isolation forest notices? Would a plain rule have
   caught it sooner?

6. **The two-emergency problem.** Write down, in words, what the cabinet should do if a second
   button press arrives while the first kit is still out. You do not have to code it — the
   hard part is deciding what the right answer is.

### The short version

```python
# a report is not the truth - keep them apart in your code
truth  = make_truth(rng)
report = make_report(truth, rng)

# several answers at once = multi-label, one small model per label
MultiOutputClassifier(RandomForestClassifier())

# do not model something that is always true - write it down as a rule
ALWAYS_OPEN = ["protective", "comms"]

# write the trade-off down where people can argue with it
cost = W_MISSING * p + COST_IF_UNNEEDED[name] * (1 - p) + ...

# seven doors = 128 kits, so just check all of them
for size in range(8):
    for kit in combinations(COMPARTMENTS, size): ...

# the model recommends, the fixed checks control the lock
chances = model(...)      # a suggestion
states  = safety_checks(...)   # the last word
```

**The one sentence to remember:** the AI chooses which supplies, and approved rules written by
people decide what is allowed to open.""")

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python"},
    "colab": {"provenance": [], "toc_visible": True},
}

out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "One_Door_Opens_Emergency_Cabinet.ipynb")
nbf.write(nb, out)
print("written", out, len(cells), "cells")
