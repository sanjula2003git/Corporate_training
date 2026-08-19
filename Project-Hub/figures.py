"""The hub's three figures, kept out of app.py so they can be rendered and looked at.

    python figures.py            # writes PNGs next to this file and reports sizes
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import catalog

BG = "#0e1117"
MUTED = "#8b949e"
DARK = dict(template="plotly_dark", paper_bgcolor=BG, plot_bgcolor=BG)


def track_bar(frame):
    """How many projects sit in each teaching track."""
    counts = (frame.groupby("Track")
              .agg(Projects=("Project", "count"), Cells=("Cells", "sum"))
              .reindex(catalog.TRACK_ORDER).fillna(0).reset_index())
    figure = px.bar(counts, x="Projects", y="Track", orientation="h", text="Projects",
                    color="Projects", color_continuous_scale=["#1f6feb", "#4fc3f7"],
                    hover_data=["Cells"])
    figure.update_traces(textposition="outside", cliponaxis=False)
    figure.update_layout(height=330, margin=dict(l=10, r=40, t=10, b=10),
                         coloraxis_showscale=False, yaxis_title="", xaxis_title="",
                         xaxis=dict(range=[0, counts.Projects.max() * 1.18]), **DARK)
    return figure


def status_donut(frame):
    """Deployment status, coloured the same way as the status dots on the cards.

    Counts the `deploy` code, not the Status text: the displayed label is a
    presentation choice that has already been shortened once, and matching on it
    would leave this chart silently empty the next time it changes.
    """
    counts = frame.deploy.value_counts()
    keys = [key for key in catalog.DEPLOY_LABEL if key in counts.index]
    figure = go.Figure(go.Pie(
        labels=[catalog.DEPLOY_LABEL[key] for key in keys],
        values=[int(counts[key]) for key in keys], hole=.55, sort=False,
        marker=dict(colors=[catalog.DEPLOY_COLOR[key] for key in keys],
                    line=dict(color=BG, width=2)),
        textinfo="value"))
    figure.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10),
                         legend=dict(font=dict(size=11)), **DARK)
    return figure


def build_timeline(frame):
    """A Gantt-style band per project, from first commit to last, coloured by track.

    Same-day projects would otherwise draw a zero-width bar and vanish, so the
    end date always gets a day added to it.
    """
    data = frame.copy()
    data["Start"] = pd.to_datetime(data.Started)
    data["End"] = pd.to_datetime(data.Updated) + pd.Timedelta(days=1)
    data = data.sort_values(["Start", "Project"])
    figure = px.timeline(data, x_start="Start", x_end="End", y="Project", color="Track",
                         hover_data=["Discipline", "Approach", "Status"],
                         category_orders={"Track": catalog.TRACK_ORDER},
                         color_discrete_sequence=px.colors.qualitative.Set2)
    figure.update_yaxes(autorange="reversed", title="", tickfont=dict(size=10))
    figure.update_xaxes(title="", gridcolor="#21262d")
    # The legend needs its own strip of margin: floated over the plot at y=1.03
    # it covered the first three rows, which all happen to share one start date.
    figure.update_layout(height=max(420, 17 * len(data)), bargap=.25,
                         margin=dict(l=10, r=10, t=64, b=10),
                         legend=dict(orientation="h", yanchor="bottom", y=1.01,
                                     xanchor="left", x=0, title=""), **DARK)
    return figure


def _demo_frame():
    """The same records app.py builds, without importing streamlit."""
    import scan
    scans = scan.scan_all([p["folder"] for p in catalog.PROJECTS])
    return pd.DataFrame([
        dict(Project=p["title"], Track=p["track"], Discipline=p["discipline"],
             Approach=p["family"], Status=catalog.DEPLOY_SHORT[p["deploy"]],
             deploy=p["deploy"],
             Cells=sum(nb["cells"] for nb in scans[p["folder"]]["notebooks"]),
             Started=p["started"], Updated=p["updated"])
        for p in catalog.PROJECTS])


if __name__ == "__main__":
    import os

    frame = _demo_frame()
    here = os.path.dirname(os.path.abspath(__file__))
    for name, figure in [("track_bar", track_bar(frame)),
                         ("status_donut", status_donut(frame)),
                         ("timeline", build_timeline(frame))]:
        path = os.path.join(here, f"_check_{name}.png")
        figure.write_image(path, scale=2)
        print(f"{name:14s} {os.path.getsize(path) / 1024:6.0f} KB  {path}")
