from pathlib import Path
import json,sys,textwrap
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE));import bridge
APP="https://tower-crane-placement.streamlit.app"
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

## Part 1 · On the construction site
{s['site']}

## Part 2 · The engineering challenge
{s['challenge']}"""),md(f"""## Part 3 · Where the AI comes in
{s['ai_link']}

**Construction Planning:** {s['civil']} → **AI:** {s['ai']} → `{s['tech']}`

> 🎬 **See this illustrated and interactive:** [{APP}/?stage={s['id']}]({APP}/?stage={s['id']})

## Part 4 · The technical explanation"""),*tech,md(f"""## Part 5 · What you just built

**In the notebook:** {s['notebook']}

**Takeaway:** {s['takeaway']}

{' &nbsp;|&nbsp; '.join(nav)}""")]

cells=[md(f"""# 🏗️ AI-Based Tower Crane Placement Optimization Using a Neural Network Surrogate

Train an MLP to estimate candidate-location cost, search it with a genetic algorithm, and verify the final location with exact geometry.

> Educational planning demonstration—not a lift plan or safety approval.

👉 **Open the interactive companion:** [{APP}]({APP}/?stage=start)"""),md(f"""## Complete workflow

Site geometry → exact candidate costs → MLP surrogate → genetic search → exact verification → before/after report.

## Interactive learning journey

{chr(10).join(f"- [{s['civil']}]({APP}/?stage={s['id']}) — {s['ai']}" for s in bridge.STEPS)}"""),co("""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error,mean_squared_error
import tensorflow as tf
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Input,Dense
from tensorflow.keras.callbacks import EarlyStopping
SEED=42;np.random.seed(SEED);tf.random.set_seed(SEED)
SITE=(80,60);LIFTS=np.array([[20,15],[55,20],[40,45]],float);FREQ=np.array([30,15,40]);REACH=45;OBST=(25,32,25,38);SAFE=(5,22,2,10)""")]
problem=md("""The output is an X,Y coordinate. The surrogate predicts a score; it does not directly output or certify the final position. Exact verification remains mandatory.""")
demand=co("""def weighted_distance(p):
 d=np.linalg.norm(LIFTS-p,axis=1);return float((FREQ*d).sum()),d
for p in [np.array([15,20]),np.array([40,30]),np.array([65,25])]:print(p,weighted_distance(p))""")
constraints=co("""def inside(p,rect):return rect[0]<=p[0]<=rect[1] and rect[2]<=p[1]<=rect[3]
def feasibility(p):
 effort,d=weighted_distance(p);return dict(boundary=0<=p[0]<=80 and 0<=p[1]<=60,obstacle=inside(p,OBST),safety_zone=inside(p,SAFE),reachable=d<=REACH,distances=d)
for p in [np.array([15,20]),np.array([40,30]),np.array([65,25])]:print(p,feasibility(p))""")
cost=co("""def exact_cost(p,details=False):
 effort,d=weighted_distance(p);f=feasibility(p);penalty=15000*(f["obstacle"]+f["safety_zone"]+int(not f["boundary"]))+10000*(~f["reachable"]).sum();total=effort+penalty
 return (total,effort,penalty,f) if details else total
for p in [np.array([15,20]),np.array([40,30]),np.array([65,25])]:print(p,exact_cost(p,True))""")
dataset=co("""rng=np.random.default_rng(SEED);candidates=np.column_stack([rng.uniform(0,80,10000),rng.uniform(0,60,10000)]);targets=np.array([exact_cost(p) for p in candidates],dtype="float32")
data=pd.DataFrame(dict(x=candidates[:,0],y=candidates[:,1],cost=targets));print(data.describe());plt.scatter(candidates[:,0],candidates[:,1],c=np.log1p(targets),s=5,cmap="viridis");plt.colorbar(label="log exact cost");plt.xlabel("X");plt.ylabel("Y");plt.show()""")
surrogate=co("""Xtr,Xte,ytr,yte=train_test_split(candidates,targets,test_size=.20,random_state=SEED);scaler=StandardScaler().fit(Xtr);Xtr_s,Xte_s=scaler.transform(Xtr),scaler.transform(Xte);ys=StandardScaler().fit(ytr.reshape(-1,1));ytr_s=ys.transform(ytr.reshape(-1,1))
model=Sequential([Input((2,)),Dense(64,activation="relu"),Dense(64,activation="relu"),Dense(32,activation="relu"),Dense(1)]);model.compile(optimizer="adam",loss="mae");early=EarlyStopping(monitor="val_loss",patience=7,restore_best_weights=True);model.fit(Xtr_s,ytr_s,validation_split=.15,epochs=70,batch_size=96,callbacks=[early],verbose=0)
def predict_cost(points):return ys.inverse_transform(model.predict(scaler.transform(points),verbose=0)).ravel()
print(model.summary())""")
audit=co("""pred=predict_cost(Xte);print("Overall MAE:",mean_absolute_error(yte,pred));feasible=yte<10000;print("Feasible-region MAE:",mean_absolute_error(yte[feasible],pred[feasible]));print("RMSE:",mean_squared_error(yte,pred)**.5)
plt.scatter(yte,pred,s=7,alpha=.25);lim=max(yte.max(),pred.max());plt.plot([0,lim],[0,lim],"r--");plt.xlabel("Exact cost");plt.ylabel("Surrogate cost");plt.show()
exact_top=set(np.argsort(yte)[:100]);pred_top=set(np.argsort(pred)[:100]);print("Top-100 ranking overlap:",len(exact_top&pred_top),"%")""")
search=co("""rng=np.random.default_rng(11);pop=np.column_stack([rng.uniform(0,80,120),rng.uniform(0,60,120)]);history=[]
for generation in range(55):
 scores=predict_cost(pop);order=np.argsort(scores);elite=pop[order[:24]];history.append(scores[order[0]]);parents=elite[rng.integers(0,len(elite),(96,2))];children=(parents[:,0]+parents[:,1])/2+rng.normal(0,[3,2],(96,2));children[:,0]=np.clip(children[:,0],0,80);children[:,1]=np.clip(children[:,1],0,60);pop=np.vstack([elite,children])
plt.plot(history);plt.xlabel("Generation");plt.ylabel("Best predicted cost");plt.grid(alpha=.2);plt.show();print("Best surrogate candidates:",pop[np.argsort(predict_cost(pop))[:5]])""")
verify=co("""# Recheck the best surrogate candidates with the original exact evaluator.
shortlist=pop[np.argsort(predict_cost(pop))[:30]];verified=sorted([(exact_cost(p),p,exact_cost(p,True)) for p in shortlist],key=lambda x:x[0]);best_cost,best,details=verified[0];baseline=np.array([15.,20.]);base_details=exact_cost(baseline,True)
print(f"OPTIMAL VERIFIED CRANE POSITION: X={best[0]:.1f} m, Y={best[1]:.1f} m");print("Weighted lifting effort:",details[1]);print("Reachable lift points:",100*details[3]["reachable"].mean(),"%");print("Safety-zone violations:",int(details[3]["obstacle"])+int(details[3]["safety_zone"]));print("Exact cost:",best_cost)
comparison=pd.DataFrame({"Metric":["Weighted effort","Reachable points","Safety violations","Exact total cost"],"Baseline":[base_details[1],f"{100*base_details[3]['reachable'].mean():.0f}%",int(base_details[3]["obstacle"])+int(base_details[3]["safety_zone"]),base_details[0]],"Optimized":[details[1],f"{100*details[3]['reachable'].mean():.0f}%",int(details[3]["obstacle"])+int(details[3]["safety_zone"]),best_cost]});display(comparison)
print("Limitations: 2D distance proxy only; no load chart, hook height, cycle time, slew collision, foundation, ties, power lines, sequencing, multiple cranes, wind, or regulatory planning.")""")
body={"problem":[problem],"demand":[demand],"constraints":[constraints],"cost":[cost],"dataset":[dataset],"surrogate":[surrogate],"audit":[audit],"search":[search],"verify":[verify]}
for i,s in enumerate(bridge.STEPS,1):cells.extend(lesson(s,i,body[s["id"]]))
cells.append(md("""---
# Final engineering conclusion

The MLP surrogate accelerates exploration, the genetic algorithm proposes low-cost coordinates, and the original exact evaluator decides which feasible candidate is reported. This separation prevents a learned approximation from silently overriding site constraints."""))
nb={"cells":cells,"metadata":{"colab":{"name":"Tower_Crane_Placement_NN_Optimization.ipynb","toc_visible":True,"provenance":[]},"kernelspec":{"display_name":"Python 3","name":"python3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":0}
out=BASE/"Tower_Crane_Placement_NN_Optimization.ipynb";out.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+"\n",encoding="utf-8");print("Wrote",out,"with",len(cells),"cells")
