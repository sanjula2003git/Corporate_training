import numpy as np
import pandas as pd
import plotly.graph_objects as go
BG="#0e1117";CYAN="#4fc3f7";AMBER="#ffb74d";RED="#ef5350";GREEN="#66bb6a";VIOLET="#ba68c8"
def evaluate(area=180,rain=900,demand=650,runoff=.85,cost_per_l=6,max_tank=12000):
 caps=np.arange(1000,max_tank+1,1000);annual=min(area*rain*runoff,demand*365);seasonality=.72+.20*np.tanh(caps/(demand*12));capture=1-np.exp(-caps/(max(800,area*rain*runoff/30)));supplied=np.minimum(annual,annual*seasonality*capture);overflow=np.maximum(area*rain*runoff-supplied,0);shortage=np.maximum(demand*365-supplied,0);cost=caps*cost_per_l
 ns=shortage/(demand*365);no=overflow/(area*rain*runoff+1e-9);nc=cost/(max(cost)+1e-9);score=1-(.5*ns+.2*no+.3*nc)
 return pd.DataFrame(dict(Capacity_L=caps,Supplied_L=supplied,Demand_met=supplied/(demand*365),Overflow_L=overflow,Shortage_L=shortage,Cost_INR=cost,Score=score))
def system_type(cap,max_tank,rain,overflow):
 if rain>=1100 and overflow>30000:return "Recharge + storage system"
 if cap<=3000:return "Small rooftop tank"
 if cap>=8000 and max_tank<=12000:return "Underground storage tank"
 return "Modular storage tanks"
def chart(df):
 fig=go.Figure();fig.add_scatter(x=df.Capacity_L,y=100*df.Demand_met,name="Demand supplied (%)",line=dict(color=GREEN,width=3));fig.add_scatter(x=df.Capacity_L,y=100*df.Overflow_L/(df.Supplied_L+df.Overflow_L),name="Overflow (%)",line=dict(color=AMBER,width=3));fig.update_layout(height=430,paper_bgcolor=BG,plot_bgcolor=BG,font_color="white",xaxis_title="Tank capacity (L)",yaxis_title="Percent");return fig
