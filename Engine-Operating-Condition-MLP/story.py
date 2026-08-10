import numpy as np
import plotly.graph_objects as go
BG="#0e1117";CYAN="#4fc3f7";AMBER="#ffb74d";RED="#ef5350";GREEN="#66bb6a";VIOLET="#ba68c8"
FEATURES=["RPM","Load %","Coolant °C","Intake °C","Fuel L/hr","Pressure bar","Exhaust °C"]
def scores(rpm,load,coolant,intake,fuel,pressure,exhaust):
 normal=-abs(load-45)/35-abs(coolant-82)/25-abs(exhaust-390)/180;high=(load-72)/18+(rpm-2200)/1300;hot=(coolant-96)/12+(exhaust-500)/130;ineff=(fuel-(3.2+.055*load))/2.2+abs(pressure-1.05);abn=abs(exhaust-(250+3.2*load))/180+abs(coolant-85)/30
 z=np.array([normal,high,hot,ineff,abn]);e=np.exp(z-z.max());return e/e.sum()
def gauges(values):
 fig=go.Figure(go.Bar(x=FEATURES,y=values,marker_color=[CYAN,CYAN,RED,AMBER,GREEN,VIOLET,RED],text=[f"{v:.1f}" for v in values],textposition="outside"));fig.update_layout(height=420,paper_bgcolor=BG,plot_bgcolor=BG,font_color="white",yaxis_title="Raw value (different units)");return fig
def network():
 fig=go.Figure();layers=[(0,7,"7 sensors",CYAN),(1,6,"Dense 32",VIOLET),(2,5,"Dense 16",VIOLET),(3,5,"5 conditions",AMBER)]
 for x,n,label,color in layers:
  ys=np.linspace(1,9,n)
  fig.add_trace(go.Scatter(x=[x]*n,y=ys,mode="markers",marker=dict(size=18,color=color),name=label))
 fig.update_xaxes(visible=False,range=[-.5,3.5]);fig.update_yaxes(visible=False);fig.update_layout(height=430,paper_bgcolor=BG,plot_bgcolor=BG,font_color="white",legend_orientation="h");return fig

