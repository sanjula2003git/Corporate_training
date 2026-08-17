"""The data and the pictures for the pandas-basics illustration app.

Same generator as the notebook (seed 7, sixty visitors), but every knob the
sidebar offers is a parameter here, so a visitor can break the data on purpose
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

COLS = ["person", "height_cm", "weight_kg", "allowed"]
NUMERIC = ["height_cm", "weight_kg"]

# (row, column, value) - the first three are the ones the notebook plants
EXTREMES = []  # deliberately empty: this project studies clean normal distributions


# --------------------------------------------------------------- the data
def build_raw(n=60, n_missing=6, n_duplicates=4, n_extreme=0, seed=7):
    """The messy file, exactly as section 0 of the notebook writes it."""
    rng = np.random.default_rng(seed)

    person = [f"P{i+1:03d}" for i in range(n)]
    height_cm = np.round(rng.normal(160.0, 15.0, n), 1)
    weight_kg = np.round(rng.normal(67.0, 14.0, n), 1)

    # Simulated classroom rule, not an actual Hong Kong attraction policy.
    allowed = np.where((height_cm >= 145) & (height_cm <= 190) & (weight_kg <= 90),
                       "Allowed", "Not Allowed")

    df = pd.DataFrame({"person": person, "height_cm": height_cm,
                       "weight_kg": weight_kg, "allowed": allowed})

    # punch holes, spread across the three columns
    if n_missing:
        holes = rng.choice(n, size=min(n_missing, n), replace=False)
        for i, row in enumerate(holes):
            df.loc[row, ["height_cm", "weight_kg"][i % 2]] = np.nan

    # glue duplicated rows on the end
    if n_duplicates:
        picks = [i % max(1, min(6, n)) for i in range(n_duplicates)]
        df = pd.concat([df, df.iloc[picks]], ignore_index=True)

    return df


def zscore_bounds(series, limit=3.0):
    """Return mean, population standard deviation and the ±limit bounds."""
    mean = series.mean()
    std = series.std(ddof=0)
    return mean, std, mean - limit * std, mean + limit * std


def clean(raw, k=3.0, fill="mean"):
    """Run the notebook's whole cleaning pipeline, keeping every intermediate."""
    deduped = raw.drop_duplicates().reset_index(drop=True)
    labelled = deduped.copy()

    filled = labelled.copy()
    fills = {}
    for col in NUMERIC:
        value = filled[col].mean() if fill == "mean" else filled[col].median()
        fills[col] = round(float(value), 2)
        filled[col] = filled[col].fillna(value)

    mask = pd.Series(True, index=filled.index)
    bounds = {}
    for col in NUMERIC:
        mean, std, low, high = zscore_bounds(filled[col], k)
        bounds[col] = dict(mean=mean, std=std, low=low, high=high)
        mask &= filled[col].between(low, high)

    # A large absolute z-score is a review flag, not proof that a real person is bad data.
    # Keep every valid measurement; students can inspect the flagged rows separately.
    final = filled.copy().reset_index(drop=True)
    final["allowed"] = np.where(final["height_cm"].between(145, 190) &
                                final["weight_kg"].le(90), "Allowed", "Not Allowed")
    final["ride_check"] = "inside limits"
    final.loc[final["allowed"].eq("Not Allowed"), "ride_check"] = "outside limits"

    return dict(raw=raw, deduped=deduped, labelled=labelled, filled=filled,
                outliers=filled[~mask], final=final, bounds=bounds, fills=fills,
                stages=[("raw file", len(raw)),
                        ("after drop_duplicates", len(deduped)),
                        ("after checking missing values", len(labelled)),
                        ("after the z-score check", len(final))])


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


def fig_allowed_not_allowed(df):
    counts = df["allowed"].value_counts().reindex(["Allowed", "Not Allowed"]).fillna(0)
    fig = go.Figure(go.Bar(x=list(counts.index), y=counts.to_numpy(),
                           marker_color=[GREEN, RED],
                           text=counts.to_numpy().astype(int), textposition="outside"))
    return _layout(fig, height=330, yaxis_title="visitors",
                   title="value_counts() — how many of each")


def fig_hist(df, col):
    fig = go.Figure(go.Histogram(x=df[col].dropna(), nbinsx=14, marker_color=CYAN))
    return _layout(fig, height=330, xaxis_title=col, yaxis_title="visitors",
                   title=f"Distribution of {col}")


def fig_scatter(df):
    fig = go.Figure()
    for label, colour in (("Allowed", GREEN), ("Not Allowed", RED)):
        part = df[df["allowed"] == label]
        fig.add_scatter(x=part["height_cm"], y=part["weight_kg"], mode="markers", name=label,
                        marker=dict(color=colour, size=9, line=dict(color=BG, width=1)))
    return _layout(fig, height=380, xaxis_title="Height (cm)", yaxis_title="Weight (kg)",
                   title="Normally distributed height and weight")


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


def fig_zscore_explained(series, limit=3.0, title="The ±3 z-score check"):
    """Every visitor as a dot, with mean and three-standard-deviation bounds."""
    mean, std, low, high = zscore_bounds(series, limit)
    values = series.dropna()
    inside = values.between(low, high)
    jitter = np.random.default_rng(1).normal(0, 0.10, len(values))

    # Drawn by hand so the visual shows standard-deviation bands explicitly.
    fig = go.Figure()
    fig.add_hrect(y0=mean-std, y1=mean+std, fillcolor=CYAN, opacity=0.10, line_width=0)
    for keep, colour, label in ((True, CYAN, "within ±3σ"), (False, RED, "review: |z| > 3")):
        sel = (inside == keep).to_numpy()
        if sel.any():
            fig.add_scatter(x=jitter[sel], y=values.to_numpy()[sel], mode="markers", name=label,
                            marker=dict(color=colour, size=8, line=dict(color=BG, width=1)))
    for value, colour, dash, label in ((high, RED, "dot", f"+3σ  {high:.1f}"),
                                       (mean+std, GREY, "dash", f"+1σ  {mean+std:.1f}"),
                                       (mean, CYAN, "solid", f"mean  {mean:.1f}"),
                                       (mean-std, GREY, "dash", f"−1σ  {mean-std:.1f}"),
                                       (low, RED, "dot", f"−3σ  {low:.1f}")):
        fig.add_hline(y=value, line=dict(color=colour, width=2, dash=dash),
                      annotation_text=label, annotation_position="right",
                      annotation_font_color=colour, annotation_font_size=12)
    fig.add_annotation(x=-0.40, y=mean, text=f"σ = {std:.2f}", showarrow=False,
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
    barely moves a boxplot. What a visitor needs to see is the gap between the
    two candidate values, and which one the outliers dragged.
    """
    values = labelled[col].dropna()
    mean_v, median_v = values.mean(), values.median()

    fig = go.Figure(go.Histogram(x=values, nbinsx=20, marker_color="#1f4f6f",
                                 marker_line=dict(color=CYAN, width=1), name="visitors"))
    for value, colour, label, where in ((median_v, CYAN, f"median {median_v:.2f}", "bottom left"),
                                        (mean_v, AMBER, f"mean {mean_v:.2f}", "top right")):
        fig.add_vline(x=value, line=dict(color=colour, width=3),
                      annotation_text=label, annotation_position=where,
                      annotation_font_color=colour, annotation_font_size=13)
    return _layout(fig, height=380, showlegend=False, xaxis_title=col, yaxis_title="visitors",
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
    """One panel per column so centimetres and kilograms keep honest scales."""
    from plotly.subplots import make_subplots

    fig = make_subplots(rows=1, cols=2,
                        subplot_titles=("average height_cm", "average weight_kg %"))
    for i, (col, colour) in enumerate((("height_cm", CYAN), ("weight_kg", VIOLET)), start=1):
        means = final.groupby("allowed")[col].mean().reindex(["Not Allowed", "Allowed"])
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
