from pathlib import Path
import json,sys,textwrap
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE));import bridge
APP="https://retaining-wall-recommender.streamlit.app"
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
cells=[md(f"""# 🧱 Retaining Wall Type Recommendation Using an MLP and Cost Optimization

Rank four wall concepts from five site inputs, then transparently balance technical suitability and estimated cost.

> Educational concept-screening simulation only—not structural or geotechnical design.

👉 **Open the interactive companion:** [{APP}]({APP}/?stage=start)"""),md(f"""## Complete workflow

Site inputs → educational labels → preprocessing → MLP → ranked suitability → cost optimization → sensitivity review.

## Interactive learning journey

{chr(10).join(f"- [{s['civil']}]({APP}/?stage={s['id']}) — {s['ai']}" for s in bridge.STEPS)}"""),co("""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.metrics import classification_report,ConfusionMatrixDisplay
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Input,Dense,Dropout
from tensorflow.keras.callbacks import EarlyStopping
SEED=42;np.random.seed(SEED);tf.random.set_seed(SEED)
WALLS=np.array(["Gravity wall","Cantilever RCC wall","Anchored wall","MSE wall"])
NUM=["height_m","width_m"];CAT=["soil","groundwater","budget"];FEATURES=NUM+CAT""")]
problem=md("""This notebook separates two questions: **Which wall concepts fit the site technically?** and **How should illustrative cost influence a technically acceptable shortlist?**""")
inputs=co("""example=pd.DataFrame([{"height_m":6.0,"soil":"Sand","groundwater":"Medium","width_m":6.0,"budget":"Medium"}]);example""")
labels=co("""def engineering_scores(h,soil,water,w,budget):
 s=np.array([72,70,55,62],float)+np.array([12 if h<=4 else -7*(h-4),12-2.5*abs(h-5.5),4.5*h,2.5*h])+np.array([8 if w>=4 else -18,5 if w>=2.5 else -12,18 if w<3 else 2,16 if w>=6 else -16])
 if water=="High":s+=np.array([-14,-8,7,-5])
 elif water=="Low":s+=np.array([5,3,0,4])
 if soil=="Clay":s+=np.array([-5,-2,8,-8])
 elif soil=="Gravel":s+=np.array([7,2,-2,6])
 elif soil=="Sand":s+=np.array([2,4,2,7])
 s+={"Low":np.array([7,-3,-15,5]),"Medium":np.array([1,5,-4,5]),"High":np.array([0,3,8,3])}[budget]
 return s
print(dict(zip(WALLS,engineering_scores(6,"Sand","Medium",6,"Medium"))))""")
data=co("""rng=np.random.default_rng(SEED);n=6000
df=pd.DataFrame({"height_m":rng.uniform(2,12,n),"soil":rng.choice(["Clay","Sand","Gravel","Mixed"],n),"groundwater":rng.choice(["Low","Medium","High"],n,p=[.35,.4,.25]),"width_m":rng.uniform(1,10,n),"budget":rng.choice(["Low","Medium","High"],n,p=[.3,.45,.25])})
scores=np.vstack([engineering_scores(r.height_m,r.soil,r.groundwater,r.width_m,r.budget) for r in df.itertuples()]);scores+=rng.normal(0,6,scores.shape);df["wall_type"]=WALLS[scores.argmax(1)];print(df.wall_type.value_counts());df.head()""")
prepare=co("""train,temp=train_test_split(df,test_size=.30,stratify=df.wall_type,random_state=SEED);val,test=train_test_split(temp,test_size=.50,stratify=temp.wall_type,random_state=SEED)
prep=ColumnTransformer([("num",StandardScaler(),NUM),("cat",OneHotEncoder(handle_unknown="ignore",sparse_output=False),CAT)]).fit(train[FEATURES])
Xtr,Xva,Xte=prep.transform(train[FEATURES]),prep.transform(val[FEATURES]),prep.transform(test[FEATURES]);lookup={w:i for i,w in enumerate(WALLS)};encode=lambda y:np.array([lookup[v] for v in y]);ytr,yva,yte=encode(train.wall_type),encode(val.wall_type),encode(test.wall_type);print(Xtr.shape,Xva.shape,Xte.shape)""")
model=co("""net=Sequential([Input((Xtr.shape[1],)),Dense(32,activation="relu"),Dropout(.12),Dense(16,activation="relu"),Dense(4,activation="softmax")]);net.compile(optimizer="adam",loss="sparse_categorical_crossentropy",metrics=["accuracy"]);early=EarlyStopping(monitor="val_loss",patience=7,restore_best_weights=True);history=net.fit(Xtr,ytr,validation_data=(Xva,yva),epochs=60,batch_size=64,callbacks=[early],verbose=0);pd.DataFrame(history.history)[["loss","val_loss"]].plot();plt.grid(alpha=.2);plt.show();net.summary()""")
audit=co("""pred=net.predict(Xte,verbose=0).argmax(1);print(classification_report(yte,pred,target_names=WALLS));ConfusionMatrixDisplay.from_predictions(yte,pred,display_labels=WALLS,xticks_rotation=25,cmap="Blues");plt.show()
p=net.predict(prep.transform(example),verbose=0)[0];ranking=pd.DataFrame({"Wall":WALLS,"Suitability":p}).sort_values("Suitability",ascending=False);display(ranking.style.format({"Suitability":"{:.1%}"}))""")
cost=co("""BASE_COST={"Gravity wall":2.6,"Cantilever RCC wall":3.4,"Anchored wall":5.1,"MSE wall":2.9};h=float(example.height_m.iloc[0]);w=float(example.width_m.iloc[0]);costs=np.array([BASE_COST[x]*h*(1+.03*h) for x in WALLS]);costs[3]*=.9 if w>=6 else 1.18;costs[2]*=.92 if w<3 else 1.08
alpha=.75;norm=(costs-costs.min())/(costs.max()-costs.min());combined=alpha*p-(1-alpha)*norm;decision=pd.DataFrame({"Wall":WALLS,"Suitability":p,"Estimated_cost_lakh":costs,"Combined_score":combined}).sort_values("Combined_score",ascending=False);display(decision.style.format({"Suitability":"{:.1%}","Estimated_cost_lakh":"₹{:.1f}","Combined_score":"{:.3f}"}));print("Recommended concept:",decision.iloc[0].Wall)""")
review=co("""scenarios=pd.DataFrame([{"height_m":h,"soil":"Sand","groundwater":"Medium","width_m":6.0,"budget":"Medium"} for h in [4,6,8,10]]);probs=net.predict(prep.transform(scenarios),verbose=0);summary=scenarios.copy();summary["Top recommendation"]=WALLS[probs.argmax(1)];summary["Confidence"]=probs.max(1);display(summary)
print("Required next steps: survey, ground investigation, stability and bearing checks, structural design, drainage, seismic/code checks, constructability, lifecycle cost, and licensed professional approval.")""")
body={"problem":[problem],"inputs":[inputs],"labels":[labels],"data":[data],"prepare":[prepare],"model":[model],"audit":[audit],"cost":[cost],"review":[review]}
for i,s in enumerate(bridge.STEPS,1):cells.extend(lesson(s,i,body[s["id"]]))
cells.append(md("""---
# Final engineering conclusion

The MLP produces a ranked concept shortlist from five site inputs. A separate, declared cost layer demonstrates trade-offs without hiding technical suitability. Final selection still requires project-specific geotechnical and structural design."""))
nb={"cells":cells,"metadata":{"colab":{"name":"Retaining_Wall_Type_Recommender.ipynb","toc_visible":True,"provenance":[]},"kernelspec":{"display_name":"Python 3","name":"python3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":0}
out=BASE/"Retaining_Wall_Type_Recommender.ipynb";out.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+"\n",encoding="utf-8");print("Wrote",out,"with",len(cells),"cells")

