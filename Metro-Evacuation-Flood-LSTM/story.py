"""Reusable Plotly illustrations for the Streamlit companion."""
import numpy as np
import plotly.graph_objects as go

BG = "#0e1117"
AMBER, CYAN, VIOLET = "#ffb74d", "#4fc3f7", "#ba68c8"
GREEN, RED, MUTED = "#66bb6a", "#ef5350", "#8b949e"


def station_map(a_depth, b_depth, threshold_warning=10, threshold_unsafe=20):
    def colour(v):
        return GREEN if v < threshold_warning else AMBER if v <= threshold_unsafe else RED
    fig = go.Figure()
    fig.add_shape(type="rect", x0=2.7, x1=7.3, y0=4.4, y1=5.6, fillcolor="#263238", line_color=MUTED)
    fig.add_annotation(x=5, y=5, text="PLATFORM", showarrow=False, font=dict(size=19, color="white"))
    for x, depth, label, exit_y in [(3.6, a_depth, "ROUTE A", 9), (6.4, b_depth, "ROUTE B", 1)]:
        y0, y1 = (5.6, 8.2) if label.endswith("A") else (1.8, 4.4)
        fig.add_shape(type="rect", x0=x-0.75, x1=x+0.75, y0=y0, y1=y1,
                      fillcolor=colour(depth), opacity=.35, line=dict(color=colour(depth), width=3))
        fig.add_annotation(x=x, y=(y0+y1)/2, text=f"<b>{label}</b><br>{depth:.1f} cm", showarrow=False,
                           font=dict(size=16, color="white"))
        fig.add_annotation(x=x, y=exit_y, text=f"EXIT {label[-1]}", showarrow=False,
                           font=dict(size=18, color=CYAN))
    fig.update_xaxes(visible=False, range=[1.5, 8.5]); fig.update_yaxes(visible=False, range=[0, 10])
    fig.update_layout(height=520, margin=dict(l=0,r=0,t=20,b=0), paper_bgcolor=BG, plot_bgcolor=BG)
    return fig


def forecast_chart(current_a, current_b, pred_a, pred_b):
    t = np.arange(6)
    a = current_a + (pred_a-current_a) * (t/5) ** 1.35
    b = current_b + (pred_b-current_b) * (t/5) ** 1.2
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=a, mode="lines+markers", name="Route A forecast", line=dict(color=RED, width=4)))
    fig.add_trace(go.Scatter(x=t, y=b, mode="lines+markers", name="Route B forecast", line=dict(color=GREEN, width=4)))
    fig.add_hrect(y0=0, y1=10, fillcolor=GREEN, opacity=.08, line_width=0)
    fig.add_hrect(y0=10, y1=20, fillcolor=AMBER, opacity=.08, line_width=0)
    fig.add_hrect(y0=20, y1=max(35, pred_a+5, pred_b+5), fillcolor=RED, opacity=.08, line_width=0)
    fig.add_hline(y=10, line_dash="dot", line_color=AMBER)
    fig.add_hline(y=20, line_dash="dot", line_color=RED)
    fig.update_layout(height=420, paper_bgcolor=BG, plot_bgcolor=BG, font_color="white",
                      xaxis_title="Minutes from now", yaxis_title="Route water depth (cm)", legend_orientation="h")
    return fig


def sequence_window():
    fig = go.Figure()
    for i in range(10):
        fig.add_shape(type="rect", x0=i, x1=i+.82, y0=1, y1=2.2, fillcolor=CYAN, opacity=.22, line_color=CYAN)
        fig.add_annotation(x=i+.41, y=1.6, text=f"t-{9-i}", showarrow=False, font_color="white")
    fig.add_annotation(x=11.2, y=1.6, text="LSTM", showarrow=False, bgcolor=VIOLET, borderpad=16, font_color="white")
    fig.add_annotation(x=13.8, y=1.6, text="depth<br>t+5", showarrow=False, bgcolor=AMBER, borderpad=12, font_color="black")
    fig.add_annotation(x=10.2, y=1.6, ax=9.5, ay=1.6, text="", showarrow=True, arrowhead=3, arrowcolor="white")
    fig.add_annotation(x=12.9, y=1.6, ax=12, ay=1.6, text="", showarrow=True, arrowhead=3, arrowcolor="white")
    fig.update_xaxes(visible=False, range=[-.3,15]); fig.update_yaxes(visible=False, range=[0,3])
    fig.update_layout(height=250, margin=dict(l=0,r=0,t=20,b=0), paper_bgcolor=BG, plot_bgcolor=BG)
    return fig

