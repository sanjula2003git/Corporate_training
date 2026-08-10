import numpy as np
import plotly.graph_objects as go
BG="#0e1117";CYAN="#4fc3f7";AMBER="#ffb74d";RED="#ef5350";GREEN="#66bb6a";VIOLET="#ba68c8"
POS={"A":(0,3),"B":(0,2),"C":(-1,1),"D":(1,1),"E":(-1,0)};EDGES=[("A","B"),("B","C"),("B","D"),("C","E")]
def risks(rain=85,drainage_scale=1):
 elev={"A":108,"B":104,"C":99,"D":105,"E":98};drain={"A":60,"B":40,"C":20,"D":50,"E":24};depth={"A":3,"B":4,"C":5,"D":2,"E":4};out={}
 for k in POS:out[k]=1/(1+np.exp(-(.055*(rain-drain[k]*drainage_scale)+.12*depth[k]+.10*(104-elev[k]))))
 out["C"]=min(1,out["C"]+.18*out["B"]+.12*out["E"]);out["E"]=min(1,out["E"]+.12*out["C"]);return out
def network(rain=85,drainage_scale=1):
 r=risks(rain,drainage_scale);fig=go.Figure()
 for a,b in EDGES:fig.add_trace(go.Scatter(x=[POS[a][0],POS[b][0]],y=[POS[a][1],POS[b][1]],mode="lines",line=dict(color="#5c6773",width=5),showlegend=False))
 for k,(x,y) in POS.items():fig.add_trace(go.Scatter(x=[x],y=[y],mode="markers+text",text=[f"ROAD {k}<br>{r[k]:.0%}"],textposition="middle center",marker=dict(size=78,color=r[k],colorscale=[[0,GREEN],[.5,AMBER],[1,RED]],cmin=0,cmax=1,line=dict(color="white",width=2)),showlegend=False))
 fig.update_xaxes(visible=False,range=[-2,2]);fig.update_yaxes(visible=False,range=[-.7,3.7]);fig.update_layout(height=520,paper_bgcolor=BG,plot_bgcolor=BG,margin=dict(l=0,r=0,t=20,b=0));return fig

