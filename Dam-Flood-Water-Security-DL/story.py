import numpy as np
import plotly.graph_objects as go
BG="#0e1117";AMBER="#ffb74d";CYAN="#4fc3f7";GREEN="#66bb6a";RED="#ef5350";VIOLET="#ba68c8"
def forecast(level,rain,inflow,downstream,free,current_release):
 storm=(.045*rain+.0055*inflow*6-.0045*current_release*6)*(1+.12*downstream)
 return float(np.clip(level+storm,0,105))
def release_rule(pred,downstream):
 base=0 if pred<85 else 120 if pred<90 else 250 if pred<=95 else 400
 caps=[450,320,250,180];return min(base,caps[int(downstream)])
def simulate(level,rain,inflow,downstream,current_release,pre_release):
 hours=np.arange(7);shape=np.array([.25,.65,1,.85,.55,.30,.12]);storm_gain=(rain/120)*shape*2.25
 pre=np.where(hours<3,pre_release/230,0);release=np.full(7,current_release/300)
 path=[level]
 spill=[]
 for i in range(6):
  nxt=path[-1]+storm_gain[i]+inflow/850-release[i]-pre[i]
  spill.append(max(0,nxt-100)*100);path.append(min(100,nxt))
 return np.array(path),max(spill+[0]),pre_release*3*3600/1e6
def reservoir(level,title="Reservoir"):
 fig=go.Figure();fig.add_shape(type="rect",x0=2,x1=8,y0=1,y1=9,line=dict(color="white",width=3));fig.add_shape(type="rect",x0=2,x1=8,y0=1,y1=1+8*min(level,100)/100,fillcolor=CYAN,line_width=0,opacity=.65);fig.add_annotation(x=5,y=5,text=f"<b>{title}</b><br>{level:.1f}%",showarrow=False,font=dict(size=24,color="white"));fig.update_xaxes(visible=False,range=[0,10]);fig.update_yaxes(visible=False,range=[0,10]);fig.update_layout(height=430,paper_bgcolor=BG,plot_bgcolor=BG,margin=dict(l=0,r=0,t=10,b=0));return fig
def comparison(no,ai):
 fig=go.Figure();fig.add_trace(go.Scatter(x=np.arange(7),y=no,mode="lines+markers",name="Without AI",line=dict(color=RED,width=4)));fig.add_trace(go.Scatter(x=np.arange(7),y=ai,mode="lines+markers",name="With AI pre-release",line=dict(color=GREEN,width=4)));fig.add_hline(y=100,line_dash="dash",line_color=RED);fig.update_layout(height=410,paper_bgcolor=BG,plot_bgcolor=BG,font_color="white",xaxis_title="Hours",yaxis_title="Reservoir level (%)");return fig

