"""The teaching registry: one entry per page, in the order the notebook works.

Every entry keeps the same five parts as the notebook's sections, and the same
plain-English house style: short sentences, everyday words.
  title       - the page name, in the language of the data
  pandas      - the short technical label it maps to
  data        - what is actually in front of you, with no pandas in it
  problem     - why that is a problem for a person
  pandas_link - what pandas is being asked to do about it
  tech        - the one-line technical idea
  notebook    - which notebook section this matches
  takeaway    - one sentence to remember
"""

PHASES = [
    ("The File You Were Sent", "Nobody hands you clean data."),
    ("The First Look", "Four functions, four different questions."),
    ("Cleaning", "Duplicates and empty cells, in that order."),
    ("Distribution", "Bell curves, standard deviation and z-scores."),
    ("Selecting Rows", "iloc counts. loc reads labels."),
    ("The Payoff", "What the cleaned table finally says."),
]

STEPS = [
    dict(id="messy", phase=0, title="The File You Were Sent", pandas="The Starting Point",
         tech="60 visitors, 3 supplied columns, and ordinary data-quality problems",
         data="A spreadsheet with person, height_cm and weight_kg. Eligibility is derived only "
              "after the measurements have been cleaned.",
         problem="It has duplicated rows, empty cells and a normally distributed measurements. "
                 "None of that is visible by scrolling.",
         pandas_link="Load it and find the damage before trusting a single average.",
         notebook="Sections 0 and 1 — writing and reading the CSV.",
         takeaway="Do not calculate eligibility statistics until duplicates and missing measurements are handled."),

    dict(id="peek", phase=1, title="head() and tail()", pandas="Look At It First",
         tech="df.head() · df.tail() · df.shape",
         data="The first five rows and the last five rows.",
         problem="A file can look perfect at the top and be broken at the bottom — that is where "
                 "exports glue their junk.",
         pandas_link="Always look at both ends. It takes two seconds and catches most disasters.",
         notebook="Section 2 — head() and tail().",
         takeaway="Look at the bottom of the file. That is where the surprises live."),

    dict(id="info", phase=1, title="info() — The Health Check", pandas="Types And Counts",
         tech="df.info() · df.dtypes",
         data="A list of the columns, the type of each one, and how many values are not empty.",
         problem="A column of numbers stored as text will not add up, and no error tells you.",
         pandas_link="Compare each non-null count with the row count. Any gap is a missing value.",
         notebook="Section 2 — info() and dtypes.",
         takeaway="If non-null is smaller than the row count, that column has holes."),

    dict(id="describe", phase=1, title="describe() — The Numbers", pandas="The Summary",
         tech="df.describe() · df['col'].value_counts()",
         data="Count, mean, smallest, largest and the quartiles of every numeric column.",
         problem="describe() ignores text columns completely, so the answer you care about — how "
                 "how many are allowed — is not in it.",
         pandas_link="Use describe() for numbers and value_counts() for categories. They are two "
                     "different tools.",
         notebook="Section 2 — describe() and value_counts().",
         takeaway="Mean and median that sit close together is describe() telling you to look at a boxplot."),

    dict(id="picture", phase=1, title="A Picture Beats describe()", pandas="Plot It Early",
         tech="bar · histogram · scatter",
         data="The same three columns, drawn instead of tabulated.",
         problem="A table of eight numbers per column does not show you a shape, a gap or a cluster.",
         pandas_link="One bar chart, one histogram and one scatter plot answer more than describe() "
                     "does.",
         notebook="Section 2 — the three quick illustrations.",
         takeaway="Two seconds of looking beats twenty seconds of reading numbers."),

    dict(id="dupes", phase=2, title="The Same Visitor Twice", pandas="Duplicates",
         tech="df.duplicated() · df.drop_duplicates()",
         data="Rows that are identical to a row further up the file.",
         problem="Usually a merge or an export accident. Every duplicate quietly drags the averages "
                 "towards itself and inflates your row count.",
         pandas_link="duplicated() marks them, drop_duplicates() keeps the first and removes the "
                     "rest.",
         notebook="Section 3 — duplicates.",
         takeaway="Do this before anything else. A duplicate poisons every number that follows."),

    dict(id="holes", phase=2, title="Where Are The Holes?", pandas="Finding Missing Values",
         tech="df.isnull().sum() · df[df.isnull().any(axis=1)]",
         data="Empty cells, shown as NaN — not a number.",
         problem="NaN spreads. One empty cell turns a mean into NaN, and a comparison against NaN is "
                 "always False, so filtering silently drops the row.",
         pandas_link="Count them per column, then look at the actual rows before deciding anything.",
         notebook="Section 4 — isnull() and the missing-values map.",
         takeaway="Find them all before you fix any of them."),

    dict(id="fill", phase=2, title="Drop Or Fill?", pandas="Handling Missing Values",
         tech="dropna(subset=…) · fillna(median) · fillna(mean)",
         data="Three choices for the same empty cell, with three different answers.",
         problem="Dropping rows throws away good data in the other columns. Filling invents a value "
                 "that was never measured.",
         pandas_link="Drop when the answer column is missing — you cannot invent a Allowed. Fill the "
                     "numeric columns, and use the mean when the distribution is symmetric and verified as approximately normal.",
         notebook="Section 4 — dropna on the target, mean fill on the normally distributed numbers.",
         takeaway="For a symmetric normal distribution, mean and median should be close."),

    dict(id="box", phase=3, title="Reading A Boxplot", pandas="Distribution At A Glance",
         tech="Q1 · median · Q3 · whiskers · dots",
         data="Five numbers per column, drawn as a box with a line through it.",
         problem="An average height says nothing about whether that is everyone, or half at 3 and "
                 "half at 8.",
         pandas_link="The box is the middle half of your visitors. The dots are the ones worth a "
                     "second look.",
         notebook="Section 5 — boxplots.",
         takeaway="The box holds the middle 50%. Everything interesting is at the edges."),

    dict(id="iqr", phase=3, title="The ±3 Z-Score Check", pandas="Normal-Data Inspection",
         tech="z = (x − mean) / standard deviation · inspect when |z| > 3",
         data="A standardized distance from the mean for an approximately normal column.",
         problem="Raw centimetres and kilograms use different scales, so distance must be standardized.",
         pandas_link="Compute mean and standard deviation, then inspect records more than three "
                     "standard deviations away.",
         notebook="Section 5 — the z-score helper.",
         takeaway="A large z-score means unusual, not wrong; verify the measurement before acting."),

    dict(id="after", phase=3, title="After The Z-Score Check", pandas="Inspect, Do Not Auto-Delete",
         tech="df[z.abs() > 3] · verify flagged measurements",
         data="The normally distributed columns with unusual tail records identified.",
         problem="A real person can be unusually tall, short, light or heavy without being a data error.",
         pandas_link="Flag unusual records for verification and retain them unless evidence shows an error.",
         notebook="Section 5 — z-score inspection and retention.",
         takeaway="Normal-data cleaning uses z-scores for inspection, not automatic deletion."),

    dict(id="iloc", phase=4, title="iloc — By Position", pandas="Integer Location",
         tech="df.iloc[0:5, 0:2] — end excluded, like a Python list",
         data="Counting rows and columns from zero, the way you count a list.",
         problem="After dropping rows the index no longer matches the position. Row 7 of the table "
                 "may be labelled 9.",
         pandas_link="iloc ignores labels completely. It counts.",
         notebook="Section 6 — iloc.",
         takeaway="iloc = integer. Position counts from 0, and the end is excluded."),

    dict(id="loc", phase=4, title="loc — By Label And Condition", pandas="Location By Name",
         tech="df.loc[0:4, ['a','b']] — end INCLUDED · df.loc[df.x > 5]",
         data="Selecting by the index label and the column name, or by a true/false test.",
         problem="loc[0:4] returns five rows and iloc[0:4] returns four. This trips up everybody, "
                 "once.",
         pandas_link="loc is the one that takes conditions, which is what you actually use all day.",
         notebook="Section 6 — loc.",
         takeaway="loc = label. The end IS included, and only loc accepts conditions."),

    dict(id="write", phase=4, title="loc That Writes", pandas="Conditional Assignment",
         tech="df.loc[condition, 'new_column'] = value",
         data="Writing the simulated ride eligibility result from height and weight limits.",
         problem="Doing this with df[condition]['col'] = value changes a copy and silently does "
                 "nothing to your real table.",
         pandas_link="Put the row test and the column name in one loc, on the left of the equals "
                     "sign.",
         notebook="Section 6 — loc as a writer, plus the crosstab.",
         takeaway="One loc, one equals sign. Two brackets means you edited a copy."),

    dict(id="payoff", phase=5, title="What The Clean Table Says", pandas="The Result",
         tech="groupby('allowed').mean() · crosstab",
         data="Average height and weight for visitors classified Allowed and Not Allowed.",
         problem="This comparison was always available. It was just wrong, because duplicates, "
                 "empty cells and missing values and duplicated rows were sitting inside the averages.",
         pandas_link="Every step before this one existed so that this number could be trusted.",
         notebook="Sections 7 and 8 — the summary and the exercises.",
         takeaway="Cleaning is not admin. It is what makes the answer true."),
]

BY_ID = {s["id"]: s for s in STEPS}
ORDER = [s["id"] for s in STEPS]
