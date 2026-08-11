"""Pandas Basics - the illustration app for the notebook.

One page per teaching step, routed by ?stage=<id>. The data, the cleaning and
the selectors are the notebook's; the sidebar lets a student break the file on
purpose and watch every later page react.
"""
import numpy as np
import pandas as pd
import streamlit as st

import bridge
import story

st.set_page_config(page_title="Pandas Basics — Student Data", layout="wide")
st.markdown("""<style>
.stApp{background:#0e1117;color:#e6edf3}
.block-container{max-width:1200px}
.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}
.data{color:#ffb74d}.pd{color:#4fc3f7}
code{color:#4fc3f7}
</style>""", unsafe_allow_html=True)


# --------------------------------------------------------------- controls
with st.sidebar:
    st.header("Break the data")
    n = st.slider("Students in the file", 20, 200, 60, step=10)
    n_missing = st.slider("Empty cells", 0, 20, 6,
                          help="Spread across all three columns.")
    n_duplicates = st.slider("Duplicated rows glued on the end", 0, 12, 4)
    n_extreme = st.slider("Extreme students planted", 0, 8, 3,
                          help="Decimal slips — 17.5 hours typed where 1.75 was meant. "
                               "The notebook plants the first three.")
    st.divider()
    st.header("Cleaning choices")
    fill = st.radio("Fill the numeric holes with", ["median", "mean"], horizontal=True)
    st.caption("Change anything here and every page below re-runs.")

# The 1.5 in "Q1 - 1.5 x IQR" is the notebook's, and the notebook's is the convention.
K = 1.5


@st.cache_data(show_spinner="Writing the messy file...")
def get_raw(n, n_missing, n_duplicates, n_extreme):
    return story.build_raw(n=n, n_missing=n_missing, n_duplicates=n_duplicates,
                           n_extreme=n_extreme)


@st.cache_data(show_spinner="Cleaning...")
def get_run(n, n_missing, n_duplicates, n_extreme, fill):
    return story.clean(get_raw(n, n_missing, n_duplicates, n_extreme), k=K, fill=fill)


raw = get_raw(n, n_missing, n_duplicates, n_extreme)
run = get_run(n, n_missing, n_duplicates, n_extreme, fill)
labelled, filled, final = run["labelled"], run["filled"], run["final"]
stage = st.query_params.get("stage", "start")

NOTE = ("Invented students. The point is the pandas, not the conclusion — no real class was "
        "measured and nothing here says anything about real people.")


def header(s):
    p = bridge.PHASES[s["phase"]]
    st.markdown(
        f"<div class='hero'><small>PHASE {s['phase'] + 1} OF {len(bridge.PHASES)} · {p[0]}</small>"
        f"<h1>{s['title']}</h1><h3><span class='data'>{s['title']}</span> → "
        f"<span class='pd'>{s['pandas']}</span></h3></div>", unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.markdown("#### 1 · What you have")
    a.write(s["data"])
    b.markdown("#### 2 · Why it is a problem")
    b.write(s["problem"])
    c.markdown("#### 3 · What pandas does")
    c.write(s["pandas_link"])
    st.markdown(f"#### 4 · What it looks like — `{s['tech']}`")


def footer(s):
    st.markdown("#### 5 · In the notebook")
    st.write(s["notebook"])
    st.success(s["takeaway"])
    i = bridge.ORDER.index(s["id"])
    cols = st.columns(3)
    if i:
        cols[0].markdown(f"[◀ {bridge.STEPS[i - 1]['title']}](?stage={bridge.ORDER[i - 1]})")
    cols[1].markdown("[Overview](?stage=start)")
    if i < len(bridge.STEPS) - 1:
        cols[2].markdown(f"[{bridge.STEPS[i + 1]['title']} ▶](?stage={bridge.ORDER[i + 1]})")


def code(src):
    st.code(src, language="python")


# --------------------------------------------------------------- landing
if stage == "start":
    st.title("Pandas Basics — Student Data")
    st.info(NOTE)
    st.markdown(
        "Three columns: **study_hours**, **attendance**, **result**. "
        "One messy file. Everything a dataset needs before anybody is allowed to draw a "
        "conclusion from it.\n\n"
        "**Use the sidebar.** Break the file on purpose — add empty cells, add duplicates, "
        "plant extreme students — and watch which page notices.")

    a, b, c, d = st.columns(4)
    a.metric("Rows in the file", len(raw))
    b.metric("Duplicated rows", int(raw.duplicated().sum()))
    c.metric("Empty cells", int(raw.isnull().sum().sum()))
    d.metric("Rows that survive", len(final),
             delta=f"{len(final) - len(raw)} lost", delta_color="inverse")

    st.plotly_chart(story.fig_stages(run["stages"]), width="stretch")

    st.subheader("Learning journey")
    for i, s in enumerate(bridge.STEPS, 1):
        st.markdown(f"**{i}. [{s['title']}](?stage={s['id']})** — {s['pandas']}")

    st.subheader("The notebook")
    st.markdown(
        "[Open the full teaching notebook in Colab]"
        "(https://colab.research.google.com/github/sanjula2003git/Corporate_training/blob/main/"
        "Pandas-Student-Basics/pandas_student_basics.ipynb)")

else:
    s = bridge.BY_ID.get(stage, bridge.STEPS[0])
    header(s)

    if s["id"] == "messy":
        code('df = pd.read_csv("students.csv")\ndf')
        st.dataframe(raw, width="stretch", height=380)
        a, b, c = st.columns(3)
        a.metric("Rows", len(raw))
        b.metric("Duplicated rows", int(raw.duplicated().sum()))
        c.metric("Empty cells", int(raw.isnull().sum().sum()))
        st.warning("Scroll it. You cannot see the duplicates, and the empty cells are easy to miss. "
                   "That is the whole reason the next five pages exist.")

    elif s["id"] == "peek":
        code("df.head()      # first 5 rows\ndf.tail()      # last 5 rows\ndf.shape       # (rows, columns)")
        a, b = st.columns(2)
        a.markdown("**`df.head()`** — the top")
        a.dataframe(raw.head(), width="stretch")
        b.markdown("**`df.tail()`** — the bottom")
        b.dataframe(raw.tail(), width="stretch")
        if n_duplicates:
            st.error(f"Look at `tail()`. Those last {n_duplicates} rows are the duplicates, glued on "
                     "by whoever exported this file. `head()` alone would never have shown you.")
        else:
            st.success("No duplicates glued on at the moment — add some in the sidebar and look at "
                       "`tail()` again.")
        st.write(f"`df.shape` → **{raw.shape}** — {raw.shape[0]} rows, {raw.shape[1]} columns.")

    elif s["id"] == "info":
        code("df.info()")
        counts = pd.DataFrame({
            "dtype": raw.dtypes.astype(str),
            "non-null": raw.notnull().sum(),
            "missing": raw.isnull().sum(),
        })
        st.dataframe(counts, width="stretch")
        st.markdown(
            f"Every column should show **{len(raw)}** non-null values. "
            + (f"These do not: **{', '.join(counts[counts['missing'] > 0].index)}** — that gap "
               "*is* the missing data."
               if counts["missing"].sum() else "All of them do, right now."))
        st.caption("dtype matters too: a numeric column that arrives as `object` will not average, "
                   "and pandas will not warn you.")

    elif s["id"] == "describe":
        code("df.describe()                  # numeric columns only\n"
             "df['result'].value_counts()    # the text column")
        st.dataframe(raw.describe(), width="stretch")
        a, b = st.columns([1, 2])
        a.markdown("**`value_counts()`**")
        a.dataframe(raw["result"].value_counts().rename("students"), width="stretch")
        b.plotly_chart(story.fig_pass_fail(raw), width="stretch")
        hi = raw["study_hours"].max()
        st.info(f"Read the **max** row. The largest study_hours here is **{hi:.1f} hours a week**, "
                f"against a mean of {raw['study_hours'].mean():.1f}. describe() cannot tell you "
                "whether that is a real student or a typo — but it can tell you to go and look.")

    elif s["id"] == "picture":
        a, b = st.columns(2)
        a.plotly_chart(story.fig_pass_fail(raw), width="stretch")
        b.plotly_chart(story.fig_hist(raw, "study_hours"), width="stretch")
        st.plotly_chart(story.fig_scatter(raw.dropna(subset=["result"])), width="stretch")
        st.markdown("The passing students sit to the **right** and **higher**. The far-right dots are "
                    "the extreme students — visible instantly here, invisible in `describe()`.")

    elif s["id"] == "dupes":
        code("df.duplicated().sum()          # how many extra copies\n"
             "df[df.duplicated(keep=False)]  # show every copy, original included\n"
             "df = df.drop_duplicates()")
        dupes = raw[raw.duplicated(keep=False)].sort_values(story.COLS)
        a, b = st.columns(2)
        a.metric("Extra copies", int(raw.duplicated().sum()))
        b.metric("Rows after drop_duplicates()", len(run["deduped"]),
                 delta=f"{len(run['deduped']) - len(raw)}", delta_color="inverse")
        if len(dupes):
            st.markdown("**Every copy, original included** — `keep=False` is what shows you both sides:")
            st.dataframe(dupes, width="stretch")
        else:
            st.success("No duplicates at the moment. Add some in the sidebar.")
        st.info("`duplicated()` marks the **second** and later copies, not the first — which is why "
                "the count is smaller than the number of rows you see above.")

    elif s["id"] == "holes":
        code("df.isnull().sum()                 # per column\n"
             "df[df.isnull().any(axis=1)]       # the actual rows")
        a, b = st.columns([1, 2])
        a.markdown("**Missing per column**")
        a.dataframe(run["deduped"].isnull().sum().rename("missing"), width="stretch")
        a.metric("Total empty cells", int(run["deduped"].isnull().sum().sum()))
        b.plotly_chart(story.fig_missing_map(run["deduped"]), width="stretch")
        rows = run["deduped"][run["deduped"].isnull().any(axis=1)]
        if len(rows):
            st.markdown("**The rows themselves** — always look before deciding:")
            st.dataframe(rows, width="stretch")
        st.warning("NaN is contagious. One empty cell makes a `mean()` return NaN, and `NaN > 5` is "
                   "`False`, so a filter drops the row without telling you.")

    elif s["id"] == "fill":
        code(f"df = df.dropna(subset=['result'])          # cannot invent a Pass\n"
             f"df['study_hours'] = df['study_hours'].fillna(df['study_hours'].{fill}())")
        a, b, c = st.columns(3)
        a.metric("Rows dropped (no result)", len(run["deduped"]) - len(labelled))
        b.metric(f"study_hours ← {fill}", run["fills"]["study_hours"])
        c.metric(f"attendance ← {fill}", run["fills"]["attendance"])
        st.plotly_chart(story.fig_fill_compare(labelled, "study_hours"), width="stretch")
        mean_v = labelled["study_hours"].mean()
        median_v = labelled["study_hours"].median()
        gap = mean_v - median_v
        st.markdown(
            f"On this data the mean is **{mean_v:.2f}** and the median is **{median_v:.2f}** — "
            f"a gap of **{abs(gap):.2f} hours**"
            + (f", the extreme students pulling the mean {'upward' if gap > 0 else 'downward'}. "
               "Fill with the mean and you hand that distortion to every row that was empty."
               if abs(gap) > 0.05 else
               ". With no extreme students planted the two barely differ — put them back with the "
               "sidebar and watch the mean move while the median stays put."))
        st.info("Push **Extreme students planted** up to 8 in the sidebar. The mean line slides to "
                "the right and the median barely moves — that is the whole argument for the median, "
                "in one picture.")

    elif s["id"] == "box":
        st.plotly_chart(story.fig_box(filled, title="One box per numeric column"),
                        width="stretch")
        st.dataframe(filled[story.NUMERIC].describe().loc[["min", "25%", "50%", "75%", "max"]],
                     width="stretch")
        st.markdown(
            "- The **box** spans Q1 to Q3 — the middle half of your students.\n"
            "- The **line** inside is the median, not the mean.\n"
            "- The **whiskers** reach the furthest point still inside the fence.\n"
            "- The **dots** are everything beyond it.")

    elif s["id"] == "iqr":
        code("""q1 = df[col].quantile(0.25)
q3 = df[col].quantile(0.75)
iqr = q3 - q1
low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
outliers = df[(df[col] < low) | (df[col] > high)]""")
        col = st.selectbox("Which column?", story.NUMERIC)
        bounds = run["bounds"][col]
        a, b, c, d = st.columns(4)
        a.metric("Q1", f"{bounds['q1']:.2f}")
        b.metric("Q3", f"{bounds['q3']:.2f}")
        c.metric("IQR", f"{bounds['iqr']:.2f}")
        d.metric("Fence", f"{bounds['low']:.1f} to {bounds['high']:.1f}")
        st.plotly_chart(story.fig_iqr_explained(filled[col], K, f"{col} — fence at 1.5 × IQR"),
                        width="stretch")
        out = filled[(filled[col] < bounds["low"]) | (filled[col] > bounds["high"])]
        st.markdown(f"**{len(out)} outlier(s)** in `{col}`, in red above:")
        if len(out):
            st.dataframe(out, width="stretch")
        st.warning("**The 1.5 is a convention, not a law.** Nothing in statistics derives it — it is "
                   "the number Tukey chose because it flags roughly 1 in 150 values from a normal "
                   "distribution. Use a smaller multiplier and almost everyone becomes an outlier; "
                   "use a larger one and almost nobody does. The data would not have changed.")

    elif s["id"] == "after":
        a, b = st.columns(2)
        a.plotly_chart(story.fig_before_after(filled, final, "study_hours"),
                       width="stretch")
        b.plotly_chart(story.fig_before_after(filled, final, "attendance"),
                       width="stretch")
        st.metric("Rows removed by the filter", len(run["outliers"]))
        if len(run["outliers"]):
            st.dataframe(run["outliers"], width="stretch")
        st.error("**Look at the 'after' boxes: new dots have appeared.** That is not a bug. Removing "
                 "the extremes shrinks the IQR, so the fence moves inwards and the next-most-unusual "
                 "students fall outside it. Loop this to zero and you will delete your dataset.")

    elif s["id"] == "iloc":
        st.markdown("Pick a slice and watch which cells it actually returns.")
        a, b = st.columns(2)
        r0, r1 = a.slider("Row positions  `iloc[r0:r1]`", 0, 12, (0, 5))
        c0, c1 = b.slider("Column positions  `iloc[:, c0:c1]`", 0, 3, (0, 2))
        code(f"df.iloc[{r0}:{r1}, {c0}:{c1}]")
        picked_rows = set(final.index[r0:r1])
        picked_cols = story.COLS[c0:c1]
        st.plotly_chart(story.fig_selection(final, picked_rows, picked_cols,
                                            f"iloc[{r0}:{r1}, {c0}:{c1}] — {len(picked_rows)} rows × "
                                            f"{len(picked_cols)} columns"),
                        width="stretch")
        st.dataframe(final.iloc[r0:r1, c0:c1], width="stretch")
        st.info(f"`iloc[{r0}:{r1}]` returns **{max(0, r1 - r0)}** rows — position {r1} is **excluded**, "
                "exactly like a Python list.")

    elif s["id"] == "loc":
        st.markdown("The same picture, but `loc` reads **labels** — and the end is included.")
        lo, hi = st.slider("Index labels  `loc[lo:hi]`", 0, 12, (0, 4))
        code(f"df.loc[{lo}:{hi}, ['study_hours', 'result']]")
        st.plotly_chart(story.fig_selection(final, set(range(lo, hi + 1)),
                                            ["study_hours", "result"],
                                            f"loc[{lo}:{hi}] — {hi - lo + 1} rows, end INCLUDED"),
                        width="stretch")
        a, b = st.columns(2)
        a.markdown(f"**`loc[{lo}:{hi}]`** → {hi - lo + 1} rows")
        a.dataframe(final.loc[lo:hi, ["study_hours", "result"]], width="stretch")
        b.markdown(f"**`iloc[{lo}:{hi}]`** → {max(0, hi - lo)} rows")
        b.dataframe(final.iloc[lo:hi][["study_hours", "result"]], width="stretch")
        st.error("Same two numbers, different row counts. This is the one that catches everybody.")

        st.markdown("#### And the thing only `loc` can do — conditions")
        hours = st.slider("Show students studying more than", 0.0, 10.0, 7.0, step=0.5)
        code(f"df.loc[df['study_hours'] > {hours}]")
        hits = final.loc[final["study_hours"] > hours]
        st.write(f"**{len(hits)}** of {len(final)} students match.")
        st.dataframe(hits, width="stretch")

    elif s["id"] == "write":
        code("""df['risk'] = 'ok'
df.loc[(df['study_hours'] < 4) | (df['attendance'] < 70), 'risk'] = 'at risk'""")
        a, b = st.columns([1, 2])
        a.dataframe(final["risk"].value_counts().rename("students"), width="stretch")
        b.dataframe(pd.crosstab(final["risk"], final["result"]), width="stretch")
        st.dataframe(final.head(12), width="stretch")
        st.markdown("The crosstab is the check: a flag that does not line up with the real outcome is "
                    "a flag nobody should act on.")
        st.error("**The trap:** `df[df['study_hours'] < 4]['risk'] = 'at risk'` looks equivalent and "
                 "does nothing. It edits a temporary copy, and pandas only warns you sometimes. "
                 "Row test and column name go inside **one** `loc`.")

    elif s["id"] == "payoff":
        st.plotly_chart(story.fig_group_means(final), width="stretch")
        st.plotly_chart(story.fig_stages(run["stages"]), width="stretch")
        gap_raw = (raw.dropna(subset=["result"]).groupby("result")["study_hours"].mean())
        gap_final = final.groupby("result")["study_hours"].mean()
        a, b = st.columns(2)
        a.metric("Pass − Fail gap, messy file",
                 f"{gap_raw.get('Pass', np.nan) - gap_raw.get('Fail', np.nan):.2f} h")
        b.metric("Pass − Fail gap, cleaned",
                 f"{gap_final.get('Pass', np.nan) - gap_final.get('Fail', np.nan):.2f} h")
        st.dataframe(final.groupby("result")[story.NUMERIC].mean().round(2),
                     width="stretch")
        st.markdown(
            "Both numbers point the same way here, and the cleaning still mattered: the messy "
            "version was computed on duplicated rows, with two students who study fifteen hours a "
            "week sitting inside the average.\n\n"
            "**Push the sidebar to the extremes** — 20 empty cells, 12 duplicates — and watch the "
            "two gaps separate.")
        st.info(NOTE)

    footer(s)
