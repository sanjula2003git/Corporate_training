import numpy as np
import plotly.graph_objects as go
BG="#0e1117";CYAN="#4fc3f7";AMBER="#ffb74d";RED="#ef5350";GREEN="#66bb6a";VIOLET="#ba68c8"
def waveforms(distance=12.5,resistance=.3,seed=2,n=500):
 rng=np.random.default_rng(seed);t=np.linspace(-.025,.075,n);phase=2*np.pi*50*t;v=np.sin(phase);i=.55*np.sin(phase-.18)
 onset=t>=0;atten=.34+.025*distance+.13*resistance;surge=5.2-.13*distance-.8*resistance
 v[onset]*=atten;i[onset]=surge*np.sin(phase[onset]-.35)+.9*np.exp(-t[onset]/.012)*np.sin(2*np.pi*520*t[onset])
 v+=.025*rng.normal(size=n);i+=.045*rng.normal(size=n);return t,v,i
def waveform_fig(distance,resistance):
 t,v,i=waveforms(distance,resistance);fig=go.Figure();fig.add_scatter(x=t*1000,y=v,name="Voltage (pu)",line=dict(color=CYAN));fig.add_scatter(x=t*1000,y=i,name="Current (pu)",line=dict(color=RED));fig.add_vline(x=0,line_dash="dash",line_color=AMBER);fig.update_layout(height=420,paper_bgcolor=BG,plot_bgcolor=BG,font_color="white",xaxis_title="Time around fault (ms)",yaxis_title="Per-unit signal");return fig
def line_map(distance):
 fig=go.Figure();colors=[CYAN,CYAN,CYAN,CYAN]
 for k in range(4):fig.add_shape(type="rect",x0=5*k,x1=5*(k+1),y0=.35,y1=.65,fillcolor=colors[k],opacity=.22,line=dict(color=colors[k],width=3));fig.add_annotation(x=2.5+5*k,y=.5,text=f"SECTION {k+1}<br>{5*k}–{5*(k+1)} km",showarrow=False,font_color="white")
 fig.add_trace(go.Scatter(x=[distance],y=[.82],mode="markers+text",text=[f"FAULT {distance:.1f} km"],textposition="top center",marker=dict(size=18,color=RED,symbol="x"),showlegend=False));fig.add_annotation(x=0,y=.15,text="SUBSTATION A",showarrow=False,font_color=AMBER);fig.add_annotation(x=20,y=.15,text="SUBSTATION B",showarrow=False,font_color=AMBER);fig.update_xaxes(range=[-1,21],visible=False);fig.update_yaxes(range=[0,1.2],visible=False);fig.update_layout(height=300,paper_bgcolor=BG,plot_bgcolor=BG,margin=dict(l=0,r=0,t=25,b=0));return fig

