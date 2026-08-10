from pathlib import Path
import json,sys,textwrap
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE));import bridge
APP="https://rainwater-harvesting-recommender.streamlit.app"
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

## Part 1 · In civil engineering
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
cells=[md(f"""# 💧 AI-Based Rainwater Harvesting System and Storage Capacity Recommendation Using MLP Optimization

Predict useful annual rainwater supply for candidate tanks, optimize storage capacity, and recommend a system concept.

> Educational simulation only—not construction-ready drainage, plumbing, water-quality, or structural design.

👉 **Open the interactive companion:** [{APP}]({APP}/?stage=start)"""),md(f"""## Complete workflow

Site inputs → daily water balance → synthetic examples → MLP surrogate → capacity optimization → system recommendation → sensitivity review.

## Interactive learning journey

{chr(10).join(f"- [{s['civil']}]({APP}/?stage={s['id']}) — {s['ai']}" for s in bridge.STEPS)}"""),co("""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error,r2_score
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Input,Dense,Dropout
from tensorflow.keras.callbacks import EarlyStopping
SEED=42;np.random.seed(SEED);tf.random.set_seed(SEED)
FEATURES=["roof_area_m2","annual_rain_mm","daily_demand_L","runoff_coefficient","tank_cost_per_L","max_capacity_L","candidate_capacity_L"]""")]
problem=md("""The AI predicts **useful annual supply for each candidate capacity**. A separate optimizer then weighs shortage, overflow, cost, and space, keeping the engineering trade-off visible.""")
inputs=co("""site={"roof_area_m2":180,"annual_rain_mm":900,"daily_demand_L":650,"runoff_coefficient":.85,"tank_cost_per_L":6,"max_capacity_L":12000}
potential=site["roof_area_m2"]*site["annual_rain_mm"]*site["runoff_coefficient"]
print("Theoretical annual harvest:",f"{potential:,.0f} L");pd.Series(site)""")
balance=co("""def simulate_balance(area,rain_mm,demand,runoff,capacity,seed=0):
 rng=np.random.default_rng(seed);wet=rng.random(365)<np.clip(.12+rain_mm/3500,.16,.65);weights=rng.gamma(1.4,1,365)*wet;daily_rain=rain_mm*weights/weights.sum();store=supply=overflow=shortage=0.
 for mm in daily_rain:
  inflow=area*mm*runoff;overflow+=max(store+inflow-capacity,0);store=min(capacity,store+inflow);used=min(store,demand);store-=used;supply+=used;shortage+=demand-used
 return supply,overflow,shortage
print(dict(zip(["supplied_L","overflow_L","shortage_L"],simulate_balance(180,900,650,.85,8000,1))))""")
data=co("""rng=np.random.default_rng(SEED);rows=[]
for i in range(5000):
 area=rng.uniform(40,600);rain=rng.uniform(300,2200);demand=rng.uniform(100,2500);runoff=rng.uniform(.5,.95);cost=rng.uniform(2,15);maximum=rng.uniform(3000,30000);cap=rng.uniform(1000,maximum);sup,over,short=simulate_balance(area,rain,demand,runoff,cap,i)
 rows.append([area,rain,demand,runoff,cost,maximum,cap,sup,over,short])
data=pd.DataFrame(rows,columns=FEATURES+["supplied_L","overflow_L","shortage_L"]);print(data.describe().T);data.head()""")
prepare=co("""train,temp=train_test_split(data,test_size=.30,random_state=SEED);val,test=train_test_split(temp,test_size=.50,random_state=SEED);scaler=StandardScaler().fit(train[FEATURES]);Xtr,Xva,Xte=scaler.transform(train[FEATURES]),scaler.transform(val[FEATURES]),scaler.transform(test[FEATURES]);ytr,yva,yte=train.supplied_L.to_numpy(),val.supplied_L.to_numpy(),test.supplied_L.to_numpy();print(Xtr.shape,Xva.shape,Xte.shape)""")
model=co("""net=Sequential([Input((7,)),Dense(64,activation="relu"),Dropout(.1),Dense(32,activation="relu"),Dense(1)]);net.compile(optimizer="adam",loss="mae");early=EarlyStopping(monitor="val_loss",patience=8,restore_best_weights=True);history=net.fit(Xtr,ytr,validation_data=(Xva,yva),epochs=80,batch_size=64,callbacks=[early],verbose=0);pd.DataFrame(history.history).plot();plt.ylabel("MAE (L/year)");plt.grid(alpha=.2);plt.show();net.summary()""")
audit=co("""pred=net.predict(Xte,verbose=0).ravel();physical_max=np.minimum(test.roof_area_m2*test.annual_rain_mm*test.runoff_coefficient,test.daily_demand_L*365);pred=np.clip(pred,0,physical_max);print("MAE:",mean_absolute_error(yte,pred));print("R²:",r2_score(yte,pred));plt.scatter(yte,pred,s=8,alpha=.3);plt.xlabel("Simulated supply");plt.ylabel("MLP supply");plt.grid(alpha=.2);plt.show()""")
optimize=co("""caps=np.arange(1000,site["max_capacity_L"]+1,1000);candidates=pd.DataFrame([{**site,"candidate_capacity_L":c} for c in caps]);supply=net.predict(scaler.transform(candidates[FEATURES]),verbose=0).ravel();potential=site["roof_area_m2"]*site["annual_rain_mm"]*site["runoff_coefficient"];annual_demand=site["daily_demand_L"]*365;supply=np.clip(supply,0,np.minimum(potential,annual_demand));candidates["supply_L"]=supply;candidates["demand_met"]=supply/annual_demand;candidates["overflow_L"]=np.maximum(potential-supply,0);candidates["shortage_L"]=np.maximum(annual_demand-supply,0);candidates["cost_INR"]=caps*site["tank_cost_per_L"];candidates["score"]=1-(.5*candidates.shortage_L/annual_demand+.2*candidates.overflow_L/potential+.3*candidates.cost_INR/candidates.cost_INR.max());best=candidates.loc[candidates.score.idxmax()];display(candidates[["candidate_capacity_L","demand_met","overflow_L","shortage_L","cost_INR","score"]].style.format({"demand_met":"{:.1%}","cost_INR":"₹{:,.0f}","score":"{:.3f}"}));print("Recommended tank:",f"{best.candidate_capacity_L:,.0f} L")""")
system=co("""def choose_system(cap,max_cap,rain,overflow):
 if rain>=1100 and overflow>30000:return "Recharge + storage system","High rainfall and remaining overflow create a recharge opportunity."
 if cap<=3000:return "Small rooftop tank","The selected storage requirement is small."
 if cap>=8000 and max_cap<=12000:return "Underground storage tank","The selected capacity is large relative to available installation space."
 return "Modular storage tanks","Modular storage provides scalable above-ground capacity."
system,reason=choose_system(best.candidate_capacity_L,site["max_capacity_L"],site["annual_rain_mm"],best.overflow_L)
print("Recommended system:",system);print("Reason:",reason);print("Expected demand supplied:",f"{best.demand_met:.1%}")
print("Required review: local daily rainfall, first flush, filtration, water quality, mosquito control, overflow routing, soil/groundwater, structural loads, access, maintenance, codes, and professional approval.")""")
body={"problem":[problem],"inputs":[inputs],"balance":[balance],"data":[data],"prepare":[prepare],"model":[model],"audit":[audit],"optimize":[optimize],"system":[system]}
for i,s in enumerate(bridge.STEPS,1):cells.extend(lesson(s,i,body[s["id"]]))
cells.append(md("""---
# Final engineering conclusion

The MLP surrogate estimates useful annual supply across feasible tank capacities. The optimizer exposes the cost–shortage–overflow trade-off, and an interpretable layer recommends a system concept. Real design requires local time-series rainfall and full civil, water-quality, regulatory, and maintenance review."""))
nb={"cells":cells,"metadata":{"colab":{"name":"Rainwater_Harvesting_System_Recommender.ipynb","toc_visible":True,"provenance":[]},"kernelspec":{"display_name":"Python 3","name":"python3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":0}
out=BASE/"Rainwater_Harvesting_System_Recommender.ipynb";out.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+"\n",encoding="utf-8");print("Wrote",out,"with",len(cells),"cells")

