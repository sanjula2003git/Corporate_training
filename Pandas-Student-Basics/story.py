"""The data and the pictures for the pandas-basics illustration app.

Same generator as the notebook (seed 7, sixty students), but every knob the
sidebar offers is a parameter here, so a student can break the data on purpose
and watch each cleaning step react.

Nothing in this file is a model. It is pandas, and pictures of pandas.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

BG = "#0e1117"
CYAN = "#4fc3f7"
AMBER = "#ffb74d"
RED = "#ef5350"
GREEN = "#66bb6a"
VIOLET = "#ba68c8"
GREY = "#8b949e"
PANEL = "#161b22"

COLS = ["study_hours", "attendance", "result"]
NUMERIC = ["study_hours", "attendance"]

# (row, column, value) - the first three are the ones the notebook plants
EXTREMES = [(3, "study_hours", 17.5), (21, "study_hours", 15.0), (9, "attendance", 22.0),
            (14, "study_hours", 16.2), (30, "study_hours", 18.4), (37, "study_hours", 14.8),
            (44, "attendance", 18.0), (50, "study_hours", 19.1)]


# --------------------------------------------------------------- the data
def build_raw(n=60, n_missing=6, n_duplicates=4, n_extreme=3, seed=7):
    """The messy file, exactly as section 0 of the notebook writes it."""
    rng = np.random.default_rng(seed)

    study_hours = np.round(rng.normal(5.0, 1.8, n).clip(0.5, 9.5), 1)
    attendance = np.round(rng.normal(80, 10, n).clip(45, 100), 0)

    # Students far outside the crowd. The first three are the notebook's; the rest are
    # there so a student can turn the dial up and watch the mean move while the median
    # does not. They read as decimal slips - 17.5 typed where 1.75 was meant.
    for row, col, value in EXTREMES[:n_extreme]:
        if row < n:
            (study_hours if col == "study_hours" else attendance)[row] = value

    score = 0.55 * study_hours + 0.06 * attendance + rng.normal(0, 0.7, n)
    result = np.where(score > 7.5, "Pass", "Fail")

    df = pd.DataFrame({"study_hours": study_hours, "attendance": attendance, "result": result})

    # punch holes, spread across the three columns
    if n_missing:
        holes = rng.choice(n, size=min(n_missing, n), replace=False)
        for i, row in enumerate(holes):
            df.loc[row, COLS[i % 3]] = np.nan

    # glue duplicated rows on the end
    if n_duplicates:
        picks = [i % max(1, min(6, n)) for i in range(n_duplicates)]
        df = pd.concat([df, df.iloc[picks]], ignore_index=True)

    return df


def iqr_bounds(series, k=1.5):
    """Return (Q1, Q3, IQR, lower, upper) — the notebook's helper."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    return q1, q3, iqr, q1 - k * iqr, q3 + k * iqr


def clean(raw, k=1.5, fill="median"):
    """Run the notebook's whole cleaning pipeline, keeping every intermediate."""
    deduped = raw.drop_duplicates().reset_index(drop=True)
    labelled = deduped.dropna(subset=["result"]).reset_index(drop=True)

    filled = labelled.copy()
    fills = {}
    for col in NUMERIC:
        value = filled[col].mean() if fill == "mean" else filled[col].median()
        fills[col] = round(float(value), 2)
        filled[col] = filled[col].fillna(value)

    mask = pd.Series(True, index=filled.index)
    bounds = {}
    for col in NUMERIC:
        q1, q3, iqr, low, high = iqr_bounds(filled[col], k)
        bounds[col] = dict(q1=q1, q3=q3, iqr=iqr, low=low, high=high)
        mask &= filled[col].between(low, high)

    final = filled[mask].reset_index(drop=True)
    final["risk"] = "ok"
    final.loc[(final["study_hours"] < 4) | (final["attendance"] < 70), "risk"] = "at risk"

    return dict(raw=raw, deduped=deduped, labelled=labelled, filled=filled,
                outliers=filled[~mask], final=final, bounds=bounds, fills=fills,
                stages=[("raw file", len(raw)),
                        ("after drop_duplicates", len(deduped)),
                        ("after dropna on result", len(labelled)),
                        ("after the IQR filter", len(final))])


# --------------------------------------------------------------- figures
def _layout(fig, height=400, right=70, **kw):
    # right defaults wide: bar labels and fence annotations sit outside the plot area
    legend = dict(bgcolor="rgba(0,0,0,0)")
    legend.update(kw.pop("legend", {}))
    fig.update_layout(height=height, paper_bgcolor=BG, plot_bgcolor=BG, font_color="white",
                      margin=dict(l=45, r=right, t=45, b=40), legend=legend, **kw)
    fig.update_xaxes(gridcolor="#21262d")
    fig.update_yaxes(gridcolor="#21262d")
    return fig


def fig_pass_fail(df):
    counts = df["result"].value_counts().reindex(["Pass", "Fail"]).fillna(0)
    fig = go.Figure(go.Bar(x=list(counts.index), y=counts.to_numpy(),
                           marker_color=[GREEN, RED],
                           text=counts.to_numpy().astype(int), textposition="outside"))
    return _layout(fig, height=330, yaxis_title="students",
                   title="value_counts() — how many of each")


def fig_hist(df, col):
    fig = go.Figure(go.Histogram(x=df[col].dropna(), nbinsx=14, marker_color=CYAN))
    return _layout(fig, height=330, xaxis_title=col, yaxis_title="students",
                   title=f"Distribution of {col}")


def fig_scatter(df):
    fig = go.Figure()
    for label, colour in (("Pass", GREEN), ("Fail", RED)):
        part = df[df["result"] == label]
        fig.add_scatter(x=part["study_hours"], y=part["attendance"], mode="markers", name=label,
                        marker=dict(color=colour, size=9, line=dict(color=BG, width=1)))
    return _layout(fig, height=380, xaxis_title="study_hours", yaxis_title="attendance",
                   title="The two numbers against each other")


def fig_missing_map(df):
    z = df[COLS].isnull().astype(int).to_numpy()
    fig = go.Figure(go.Heatmap(z=z, x=COLS, y=list(df.index), colorscale=[[0, PANEL], [1, AMBER]],
                               showscale=False, xgap=2, ygap=0.4,
                               hovertemplate="row %{y}, %{x}<br>%{z}<extra></extra>"))
    fig.update_yaxes(autorange="reversed")  # row 0 at the top, the way a table reads
    return _layout(fig, height=520, yaxis_title="row number",
                   title="Every orange stripe is an empty cell")


def fig_box(df, cols=NUMERIC, title="Boxplot"):
    fig = go.Figure()
    for col, colour in zip(cols, (CYAN, VIOLET)):
        fig.add_box(y=df[col].dropna(), name=col, marker_color=colour, boxpoints="outliers")
    return _layout(fig, height=400, title=title)


def fig_iqr_explained(series, k=1.5, title="The 1.5 × IQR fence"):
    """Every student as a dot, with the four lines the rule actually computes."""
    q1, q3, iqr, low, high = iqr_bounds(series, k)
    values = series.dropna()
    inside = values.between(low, high)
    jitter = np.random.default_rng(1).normal(0, 0.10, len(values))

    # drawn by hand rather than with add_box: plotly's own whiskers use plotly's own
    # 1.5-IQR rule, which would contradict the fence the student just chose
    fig = go.Figure()
    fig.add_hrect(y0=q1, y1=q3, fillcolor=CYAN, opacity=0.10, line_width=0)
    for keep, colour, label in ((True, CYAN, "inside the fence"), (False, RED, "outlier")):
        sel = (inside == keep).to_numpy()
        if sel.any():
            fig.add_scatter(x=jitter[sel], y=values.to_numpy()[sel], mode="markers", name=label,
                            marker=dict(color=colour, size=8, line=dict(color=BG, width=1)))
    for value, colour, dash, label in ((high, RED, "dot", f"upper fence  {high:.1f}"),
                                       (q3, GREY, "dash", f"Q3  {q3:.1f}"),
                                       (values.median(), CYAN, "solid",
                                        f"median  {values.median():.1f}"),
                                       (q1, GREY, "dash", f"Q1  {q1:.1f}"),
                                       (low, RED, "dot", f"lower fence  {low:.1f}")):
        fig.add_hline(y=value, line=dict(color=colour, width=2, dash=dash),
                      annotation_text=label, annotation_position="right",
                      annotation_font_color=colour, annotation_font_size=12)
    fig.add_annotation(x=-0.40, y=(q1 + q3) / 2, text=f"IQR = {iqr:.2f}", showarrow=False,
                       font=dict(color=CYAN, size=13), bgcolor=BG)
    fig.update_xaxes(showticklabels=False, range=[-0.55, 0.55], zeroline=False)
    return _layout(fig, height=460, right=175, title=title,
                   legend=dict(orientation="h", y=1.03, x=0))


def fig_before_after(before, after, col):
    fig = go.Figure()
    fig.add_box(y=before[col].dropna(), name="before", marker_color=AMBER, boxpoints="outliers")
    fig.add_box(y=after[col].dropna(), name="after", marker_color=CYAN, boxpoints="outliers")
    return _layout(fig, height=380, title=col)


def fig_fill_compare(labelled, col):
    """Why the median is the safer filler: show what the extremes do to the mean.

    Comparing boxplots of the two fills is useless — a handful of filled cells
    barely moves a boxplot. What a student needs to see is the gap between the
    two candidate values, and which one the outliers dragged.
    """
    values = labelled[col].dropna()
    mean_v, median_v = values.mean(), values.median()

    fig = go.Figure(go.Histogram(x=values, nbinsx=20, marker_color="#1f4f6f",
                                 marker_line=dict(color=CYAN, width=1), name="students"))
    for value, colour, label, where in ((median_v, CYAN, f"median {median_v:.2f}", "bottom left"),
                                        (mean_v, AMBER, f"mean {mean_v:.2f}", "top right")):
        fig.add_vline(x=value, line=dict(color=colour, width=3),
                      annotation_text=label, annotation_position=where,
                      annotation_font_color=colour, annotation_font_size=13)
    return _layout(fig, height=380, showlegend=False, xaxis_title=col, yaxis_title="students",
                   title=f"The two candidate fill values for {col}")


def fig_stages(stages):
    labels = [s[0] for s in stages]
    values = [s[1] for s in stages]
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h",
                           marker_color=[GREY, CYAN, CYAN, GREEN],
                           text=values, textposition="outside"))
    fig.update_yaxes(autorange="reversed")
    return _layout(fig, height=330, xaxis_title="rows left",
                   title="What each cleaning step costs you")


def fig_group_means(final):
    """One panel per column — a shared y-axis would bury hours under percentages."""
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("average study_hours", "average attendance %"))
    for i, (col, colour) in enumerate((("study_hours", CYAN), ("attendance", VIOLET)), start=1):
        means = final.groupby("result")[col].mean().reindex(["Fail", "Pass"])
        fig.add_bar(x=list(means.index), y=means.to_numpy(), marker_color=colour,
                    text=means.round(1), textposition="outside", showlegend=False,
                    cliponaxis=False, row=1, col=i)
        fig.update_yaxes(range=[0, means.max() * 1.25], row=1, col=i)
    # no outer title: it would sit on top of the subplot titles
    return _layout(fig, height=360)


def fig_selection(df, rows, cols, title, n_show=12):
    """Draw the frame as a grid and light up exactly the cells a selector returns.

    This is the picture that makes iloc and loc stop being confusing.
    """
    view = df.head(n_show)
    z, text = [], []
    for r in view.index:
        z_row, t_row = [], []
        for c in COLS:
            hit = (r in rows) and (c in cols)
            z_row.append(1 if hit else 0)
            value = view.loc[r, c]
            t_row.append(f"{value:.1f}" if isinstance(value, (int, float, np.floating))
                         and not pd.isna(value) else str(value))
        z.append(z_row)
        text.append(t_row)

    fig = go.Figure(go.Heatmap(
        z=z, x=COLS, y=[str(i) for i in view.index], text=text, texttemplate="%{text}",
        textfont=dict(size=12), colorscale=[[0, PANEL], [1, "#1f6feb"]], showscale=False,
        xgap=3, ygap=3, hovertemplate="row %{y}, %{x} = %{text}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", title="index label")
    return _layout(fig, height=60 + 34 * len(view), title=title)
