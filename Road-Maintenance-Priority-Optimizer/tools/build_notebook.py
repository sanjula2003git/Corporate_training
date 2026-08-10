from pathlib import Path
import json,sys,textwrap
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE));import bridge
APP="https://road-maintenance-priority.streamlit.app"
def md(s):return {"cell_type":"markdown","metadata":{},"source":textwrap.dedent(s).strip().splitlines(True)}
def co(s):return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":textwrap.dedent(s).strip().splitlines(True)}
def lesson(s,n,tech):
 i=n-1;p=bridge.PHASES[s["phase"]];prev=bridge.STEPS[i-1] if i else None;nxt=bridge.STEPS[i+1] if i<len(bridge.STEPS)-1 else None;nav=[]
 if prev:nav.append(f"◀ [Previous: {prev['civil']}]({APP}/?stage={prev['id']})")
 nav.append(f"[Project overview]({APP}/?stage=start)")
 if nxt:nav.append(f"[Next: {nxt['civil']}]({APP}/?stage={nxt['id']}) ▶")
 return [md(f"""---
# {n}. {s['civil']}
### Phase {s['phase']+1} of {len(bridge.PHASES)} · {p[0]}

## Part 1 · In road maintenance
{s['site']}

## Part 2 · The engineering challenge
{s['challenge']}"""),md(f"""## Part 3 · Where the AI comes in
{s['ai_link']}

**Civil Engineering:** {s['civil']} → **AI:** {s['ai']} → `{s['tech']}`

> 🎬 **See this illustrated and interactive:** [{APP}/?stage={s['id']}]({APP}/?stage={s['id']})

## Part 4 · The technical explanation"""),*tech,md(f"""## Part 5 · What you just built

**In the notebook:** {s['notebook']}

**Takeaway:** {s['takeaway']}

{' &nbsp;|&nbsp; '.join(nav)}""")]

cells=[md(f"""# 🛣️ AI-Based Road Maintenance Priority Optimizer

MLP road-benefit ranking + exact budget-constrained portfolio optimization.

> Educational planning simulation; benefit weights are declared policy assumptions.

👉 **Open the interactive companion:** [{APP}]({APP}/?stage=start)"""),md(f"""## Complete workflow

Road data → transparent benefit labels → normalized MLP → predicted scores → 0/1 knapsack → repair/defer schedule → policy comparison.

## Interactive learning journey

{chr(10).join(f"- [{s['civil']}]({APP}/?stage={s['id']}) — {s['ai']}" for s in bridge.STEPS)}"""),co("""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error,mean_squared_error
import tensorflow as tf
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Input,Dense,Dropout
from tensorflow.keras.callbacks import EarlyStopping
SEED=42;np.random.seed(SEED);tf.random.set_seed(SEED)
FEATURES=["condition_score","traffic_vpd","repair_cost_lakh","accident_risk","importance"]""")]
problem=md("""The neural model estimates individual maintenance benefit. The budget optimizer then chooses a combination. Keeping these tasks separate makes affordability and policy assumptions visible.""")
inputs=co("""example=dict(condition_score=35,traffic_vpd=18000,repair_cost_lakh=12,accident_risk=8,importance=9)
pd.Series(example,name="Road A")""")
benefit=co("""def policy_benefit(df):
 damage=(100-df.condition_score)/80;traffic=df.traffic_vpd/30000;risk=df.accident_risk/10;importance=df.importance/10
 return 100*(.35*damage+.25*traffic+.22*risk+.18*importance)
print("Declared weights: damage 35%, traffic 25%, accident risk 22%, importance 18%")""")
data=co("""rng=np.random.default_rng(SEED);n=5000;condition=rng.uniform(18,88,n);traffic=np.clip(rng.lognormal(9.2,.55,n),1200,32000);risk=np.clip((100-condition)/12+rng.normal(2,1.5,n),1,10);importance=rng.uniform(1,10,n);cost=np.clip((100-condition)*.16+traffic/9000+rng.normal(2,2,n),3,28)
data=pd.DataFrame(dict(condition_score=condition,traffic_vpd=traffic,repair_cost_lakh=cost,accident_risk=risk,importance=importance));data["benefit"]=policy_benefit(data)+rng.normal(0,3,n)
print(data.describe().T);data.head()""")
prepare=co("""train,temp=train_test_split(data,test_size=.30,random_state=SEED);val,test=train_test_split(temp,test_size=.50,random_state=SEED);imputer=SimpleImputer(strategy="median").fit(train[FEATURES]);scaler=StandardScaler().fit(imputer.transform(train[FEATURES]));prep=lambda d:scaler.transform(imputer.transform(d[FEATURES]));Xtr,Xva,Xte=prep(train),prep(val),prep(test);ytr,yva,yte=train.benefit.to_numpy(),val.benefit.to_numpy(),test.benefit.to_numpy();print(Xtr.shape,Xva.shape,Xte.shape)""")
ranking=co("""model=Sequential([Input((5,)),Dense(32,activation="relu"),Dropout(.1),Dense(16,activation="relu"),Dense(1)]);model.compile(optimizer="adam",loss="mae");early=EarlyStopping(monitor="val_loss",patience=7,restore_best_weights=True);model.fit(Xtr,ytr,validation_data=(Xva,yva),epochs=60,batch_size=64,callbacks=[early],verbose=0);model.summary()""")
rank_audit=co("""pred=model.predict(Xte,verbose=0).ravel();print("MAE:",mean_absolute_error(yte,pred));print("RMSE:",mean_squared_error(yte,pred)**.5);print("Spearman rank correlation:",spearmanr(yte,pred).statistic)
k=50;overlap=len(set(np.argsort(yte)[-k:])&set(np.argsort(pred)[-k:]));print(f"Top-{k} overlap:",overlap,"of",k);plt.scatter(yte,pred,s=8,alpha=.3);plt.xlabel("Target benefit");plt.ylabel("Predicted benefit");plt.grid(alpha=.2);plt.show()""")
budget=co("""programme=data.sample(20,random_state=9).reset_index(drop=True);programme["Road"]=[f"Road {chr(65+i)}" for i in range(20)];programme["predicted_benefit"]=model.predict(prep(programme),verbose=0).ravel();programme["cost_int"]=programme.repair_cost_lakh.round().clip(1).astype(int)
def knapsack(df,budget):
 n=len(df);dp=np.zeros((n+1,budget+1));take=np.zeros((n+1,budget+1),bool)
 for i in range(1,n+1):
  c=int(df.iloc[i-1].cost_int);v=float(df.iloc[i-1].predicted_benefit);dp[i]=dp[i-1]
  for b in range(c,budget+1):
   if dp[i-1,b-c]+v>dp[i,b]:dp[i,b]=dp[i-1,b-c]+v;take[i,b]=True
 b=budget;sel=[]
 for i in range(n,0,-1):
  if take[i,b]:sel.append(i-1);b-=int(df.iloc[i-1].cost_int)
 return sorted(sel),dp[n,budget]
selected,total=knapsack(programme,50);programme["Decision"]=["REPAIR" if i in selected else "DEFER" for i in range(len(programme))];display(programme[["Road","predicted_benefit","cost_int","Decision"]].sort_values("predicted_benefit",ascending=False));print("Budget used:",programme.iloc[selected].cost_int.sum(),"lakh | Total predicted benefit:",total)""")
compare=co("""def greedy(df,budget,order):
 used=0;sel=[]
 for i in order:
  c=int(df.iloc[i].cost_int)
  if used+c<=budget:sel.append(i);used+=c
 return sel
worst=greedy(programme,50,np.argsort(programme.condition_score));score=greedy(programme,50,np.argsort(programme.predicted_benefit)[::-1]);opt,_=knapsack(programme,50)
rows=[]
for name,sel in [("Worst condition first",worst),("Highest score first",score),("Knapsack optimized",opt)]:rows.append(dict(Policy=name,Roads=len(sel),Cost=int(programme.iloc[sel].cost_int.sum()),Benefit=float(programme.iloc[sel].predicted_benefit.sum())))
display(pd.DataFrame(rows));budgets=np.arange(10,101,5);values=[knapsack(programme,int(b))[1] for b in budgets];plt.plot(budgets,values,"o-");plt.xlabel("Budget ₹ lakh");plt.ylabel("Maximum predicted benefit");plt.grid(alpha=.2);plt.show()
print("Governance limits: weights are assumptions; no lifecycle treatment choice, deterioration forecast, geographic equity, accessibility duty, utility coordination, inflation, procurement, or uncertainty optimization.")""")
body={"problem":[problem],"inputs":[inputs],"benefit":[benefit],"data":[data],"prepare":[prepare],"ranking":[ranking],"rank_audit":[rank_audit],"budget":[budget],"compare":[compare]}
for i,s in enumerate(bridge.STEPS,1):cells.extend(lesson(s,i,body[s["id"]]))
cells.append(md("""---
# Final engineering conclusion

The MLP estimates road-level maintenance benefit from five attributes. Exact knapsack optimization then selects the highest-benefit affordable combination. Separating score prediction from portfolio selection keeps policy, cost, and budget constraints reviewable."""))
nb={"cells":cells,"metadata":{"colab":{"name":"Road_Maintenance_Priority_Optimizer.ipynb","toc_visible":True,"provenance":[]},"kernelspec":{"display_name":"Python 3","name":"python3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":0}
out=BASE/"Road_Maintenance_Priority_Optimizer.ipynb";out.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+"\n",encoding="utf-8");print("Wrote",out,"with",len(cells),"cells")
