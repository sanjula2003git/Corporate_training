import numpy as np
import pandas as pd
import plotly.graph_objects as go
BG="#0e1117";CYAN="#4fc3f7";AMBER="#ffb74d";RED="#ef5350";GREEN="#66bb6a";VIOLET="#ba68c8"
WALLS=["Gravity wall","Cantilever RCC wall","Anchored wall","MSE wall"]
BASE_COST={"Gravity wall":2.6,"Cantilever RCC wall":3.4,"Anchored wall":5.1,"MSE wall":2.9}
def suitability(height,soil,water,width,budget):
 scores=np.array([72,70,55,62],float)
 scores+=np.array([12 if height<=4 else -7*(height-4),12-2.5*abs(height-5.5),4.5*height,2.5*height])
 scores+=np.array([8 if width>=4 else -18,5 if width>=2.5 else -12,18 if width<3 else 2,16 if width>=6 else -16])
 if water=="High":scores+=np.array([-14,-8,7,-5])
 elif water=="Low":scores+=np.array([5,3,0,4])
 if soil=="Clay":scores+=np.array([-5,-2,8,-8])
 elif soil=="Gravel":scores+=np.array([7,2,-2,6])
 elif soil=="Sand":scores+=np.array([2,4,2,7])
 scores+=({"Low":np.array([7,-3,-15,5]),"Medium":np.array([1,5,-4,5]),"High":np.array([0,3,8,3])}[budget])
 p=np.exp((scores-scores.max())/12);return p/p.sum()
def recommend(height=6,soil="Sand",water="Medium",width=6,budget="Medium",alpha=.75):
 p=suitability(height,soil,water,width,budget);cost=np.array([BASE_COST[w]*height*(1+.03*height) for w in WALLS]);cost[3]*=.9 if width>=6 else 1.18;cost[2]*=.92 if width<3 else 1.08
 norm=(cost-cost.min())/(cost.max()-cost.min()+1e-9);combined=alpha*p-(1-alpha)*norm
 return pd.DataFrame({"Wall":WALLS,"Suitability":p,"Estimated_cost_lakh":cost,"Combined_score":combined}).sort_values("Combined_score",ascending=False).reset_index(drop=True)
def ranking_chart(df):
 fig=go.Figure(go.Bar(y=df.Wall,x=100*df.Suitability,orientation="h",marker_color=[GREEN,CYAN,AMBER,RED],text=[f"{v:.1%}" for v in df.Suitability],textposition="outside"));fig.update_layout(height=410,paper_bgcolor=BG,plot_bgcolor=BG,font_color="white",xaxis_title="Illustrative suitability",yaxis_title="",yaxis_autorange="reversed",xaxis_range=[0,105]);return fig
