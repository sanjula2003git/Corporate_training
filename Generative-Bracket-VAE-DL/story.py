import numpy as np
import plotly.graph_objects as go
from collections import deque
BG="#0e1117";CYAN="#4fc3f7";AMBER="#ffb74d";GREEN="#66bb6a";RED="#ef5350";VIOLET="#ba68c8"
def bracket(z1=0,z2=0,z3=0,size=64):
 y,x=np.mgrid[:size,:size];mask=np.zeros((size,size),bool)
 left=(18,46);right=(46,18);r=8
 mask|=(x-left[0])**2+(y-left[1])**2<=r*r;mask|=(x-right[0])**2+(y-right[1])**2<=r*r
 # Variable diagonal web and lower flange.
 line_y=62-x+z1*3;thick=7+2*z2;mask|=(np.abs(y-line_y)<thick)&(x>12)&(x<53)
 mask|=(y>44-z3*2)&(y<55+z3*2)&(x>10)&(x<35)
 mask|=(x>40-z3*2)&(x<52+z3*2)&(y>12)&(y<38)
 # Mount holes remain empty.
 for cx,cy in (left,right):mask[(x-cx)**2+(y-cy)**2<4.2**2]=0
 # Latent lightening opening.
 cx,cy=32+3*z1,35-2*z2;rx,ry=7+2*max(z3,0),5+2*max(z2,0);mask[((x-cx)/rx)**2+((y-cy)/ry)**2<1]=0
 return mask.astype(float)
def connected(mask):
 m=mask>.5;pts=np.argwhere(m)
 if not len(pts):return False
 seen={tuple(pts[0])};q=deque(seen)
 while q:
  y,x=q.popleft()
  for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
   p=(y+dy,x+dx)
   if 0<=p[0]<64 and 0<=p[1]<64 and m[p] and p not in seen:seen.add(p);q.append(p)
 return len(seen)>=.96*m.sum()
def area(mask):return int((mask>.5).sum())
def heat(mask,title="Bracket geometry"):
 fig=go.Figure(go.Heatmap(z=mask,colorscale=[[0,"#05080a"],[1,CYAN]],showscale=False,zmin=0,zmax=1));fig.update_yaxes(autorange="reversed",visible=False);fig.update_xaxes(visible=False);fig.update_layout(title=title,height=440,paper_bgcolor=BG,plot_bgcolor=BG,font_color="white",margin=dict(l=10,r=10,t=45,b=10));return fig
def latent_map():
 xs=np.linspace(-2,2,9);fig=go.Figure()
 for a in xs:
  for b in xs:fig.add_trace(go.Scatter(x=[a],y=[b],mode="markers",marker=dict(size=8+area(bracket(a,b,0))/160,color=area(bracket(a,b,0)),colorscale="Viridis",showscale=False),showlegend=False))
 fig.update_layout(height=430,paper_bgcolor=BG,plot_bgcolor=BG,font_color="white",xaxis_title="Latent coordinate z₁",yaxis_title="Latent coordinate z₂");return fig

