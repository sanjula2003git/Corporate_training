import numpy as np
import plotly.graph_objects as go
BG="#0e1117";CYAN="#4fc3f7";AMBER="#ffb74d";RED="#ef5350";GREEN="#66bb6a";VIOLET="#ba68c8"
LIFTS=np.array([[20,15],[55,20],[40,45]],float);FREQ=np.array([30,15,40]);OBST=(25,32,25,38);SAFE=(5,22,2,10);REACH=45
def inside(p,r):return r[0]<=p[0]<=r[1] and r[2]<=p[1]<=r[3]
def evaluate(p):
 d=np.linalg.norm(LIFTS-p,axis=1);viol=int(inside(p,OBST))+int(inside(p,SAFE));unreach=(d>REACH).sum();return float((d*FREQ).sum()+viol*15000+unreach*10000),d,viol,unreach
def site(crane=(37,29),title="Construction site"):
 p=np.array(crane);cost,d,v,u=evaluate(p);fig=go.Figure();fig.add_shape(type="rect",x0=0,x1=80,y0=0,y1=60,line=dict(color="white",width=3));fig.add_shape(type="rect",x0=OBST[0],x1=OBST[1],y0=OBST[2],y1=OBST[3],fillcolor="#555",line_color="white");fig.add_shape(type="rect",x0=SAFE[0],x1=SAFE[1],y0=SAFE[2],y1=SAFE[3],fillcolor=RED,opacity=.28,line_color=RED);fig.add_shape(type="circle",x0=p[0]-REACH,x1=p[0]+REACH,y0=p[1]-REACH,y1=p[1]+REACH,line=dict(color=CYAN,dash="dot"))
 fig.add_trace(go.Scatter(x=LIFTS[:,0],y=LIFTS[:,1],mode="markers+text",text=[f"Lift {chr(65+i)}<br>{FREQ[i]}/day" for i in range(3)],textposition="top center",marker=dict(size=18,color=AMBER),name="Lift points"));fig.add_trace(go.Scatter(x=[p[0]],y=[p[1]],mode="markers+text",text=[f"CRANE<br>({p[0]:.1f},{p[1]:.1f})"],textposition="top center",marker=dict(size=22,color=GREEN if not(v+u) else RED,symbol="star"),name="Crane"))
 for q in LIFTS:fig.add_shape(type="line",x0=p[0],y0=p[1],x1=q[0],y1=q[1],line=dict(color=CYAN,width=1))
 fig.update_xaxes(range=[-5,85],title="X (m)");fig.update_yaxes(range=[-5,65],title="Y (m)",scaleanchor="x",scaleratio=1);fig.update_layout(title=title,height=560,paper_bgcolor=BG,plot_bgcolor=BG,font_color="white");return fig

