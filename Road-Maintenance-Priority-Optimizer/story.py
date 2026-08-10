import numpy as np
import pandas as pd
import plotly.graph_objects as go
BG="#0e1117";CYAN="#4fc3f7";AMBER="#ffb74d";RED="#ef5350";GREEN="#66bb6a";VIOLET="#ba68c8"
def roads(n=12,seed=5):
 rng=np.random.default_rng(seed);condition=rng.integers(20,82,n);traffic=rng.integers(2500,28000,n);risk=rng.integers(1,11,n);importance=rng.integers(1,11,n);cost=np.clip((100-condition)*.15+traffic/9000+rng.normal(2,2,n),4,24).round().astype(int);damage=100-condition;benefit=100*(.35*damage/80+.25*traffic/28000+.22*risk/10+.18*importance/10);return pd.DataFrame(dict(Road=[f"Road {chr(65+i)}" for i in range(n)],Condition=condition,Traffic=traffic,Cost_lakh=cost,Risk=risk,Importance=importance,Benefit=benefit))
def knapsack(df,budget,value="Benefit"):
 dp=np.zeros((len(df)+1,budget+1));take=np.zeros_like(dp,bool)
 for i,row in enumerate(df.itertuples(),1):
  c=int(row.Cost_lakh);v=float(getattr(row,value));dp[i]=dp[i-1]
  for b in range(c,budget+1):
   if dp[i-1,b-c]+v>dp[i,b]:dp[i,b]=dp[i-1,b-c]+v;take[i,b]=True
 b=budget;sel=[]
 for i in range(len(df),0,-1):
  if take[i,b]:sel.append(i-1);b-=int(df.iloc[i-1].Cost_lakh)
 return sorted(sel),dp[-1,budget]
def scatter(df,selected):
 colors=[GREEN if i in selected else "#59636e" for i in range(len(df))];fig=go.Figure(go.Scatter(x=df.Cost_lakh,y=df.Benefit,mode="markers+text",text=df.Road,textposition="top center",marker=dict(size=16,color=colors)));fig.update_layout(height=450,paper_bgcolor=BG,plot_bgcolor=BG,font_color="white",xaxis_title="Repair cost (₹ lakh)",yaxis_title="Predicted benefit");return fig

