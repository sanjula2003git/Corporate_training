from pathlib import Path
import json,sys,textwrap
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE));import bridge
APP="https://engine-operating-condition.streamlit.app"
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

## Part 1 · At the engine
{s['site']}

## Part 2 · The engineering challenge
{s['challenge']}"""),md(f"""## Part 3 · Where the AI comes in
{s['ai_link']}

**Mechanical Engineering:** {s['civil']} → **AI:** {s['ai']} → `{s['tech']}`

> 🎬 **See this illustrated and interactive:** [{APP}/?stage={s['id']}]({APP}/?stage={s['id']})

## Part 4 · The technical explanation"""),*tech,md(f"""## Part 5 · What you just built

**In the notebook:** {s['notebook']}

**Takeaway:** {s['takeaway']}

{' &nbsp;|&nbsp; '.join(nav)}""")]

cells=[md(f"""# 🚗 AI-Based Engine Operating Condition Classification with an MLP

Seven current sensor readings → MLP → Normal, High Load, Overheating, Inefficient Operation, or Abnormal.

> Recommendations are simulated educational responses.

👉 **Open the interactive companion:** [{APP}]({APP}/?stage=start)"""),md(f"""## Complete workflow

Generate/load rows → clean → normalize → train MLP → enter readings → condition probabilities → simulated response.

## Interactive learning journey

{chr(10).join(f"- [{s['civil']}]({APP}/?stage={s['id']}) — {s['ai']}" for s in bridge.STEPS)}"""),co("""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report,confusion_matrix,ConfusionMatrixDisplay
import tensorflow as tf
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Input,Dense,Dropout
from tensorflow.keras.callbacks import EarlyStopping
SEED=42;np.random.seed(SEED);tf.random.set_seed(SEED)
FEATURES=["rpm","load_pct","coolant_c","intake_c","fuel_l_hr","manifold_bar","exhaust_c"]
CLASSES=["NORMAL","HIGH LOAD","OVERHEATING","INEFFICIENT","ABNORMAL"]""")]
problem=md("""Each sample is an independent snapshot. The notebook deliberately uses no sequence window: it asks what condition the engine is in now from seven synchronized values.""")
inputs=co("""example=dict(rpm=2400,load_pct=78,coolant_c=96,intake_c=42,fuel_l_hr=8.4,manifold_bar=1.3,exhaust_c=520)
pd.Series(example,name="Example sensor snapshot")""")
data=co("""def make_class(label,n=600,seed=0):
 rng=np.random.default_rng(seed)
 centres=[[1600,42,82,30,4.8,1.0,370],[2850,90,91,39,9.2,1.48,545],[2250,68,111,45,8.0,1.25,590],[1950,55,89,36,9.1,.98,475],[2100,58,97,43,7.8,1.12,535]][label]
 scales=[420,12,5,5,.8,.12,45] if label<4 else [800,24,13,11,2.1,.28,110]
 a=rng.normal(centres,scales,(n,7));a[:,0]=np.clip(a[:,0],600,4200);a[:,1]=np.clip(a[:,1],0,100);a[:,2]=np.clip(a[:,2],50,125);a[:,3]=np.clip(a[:,3],5,70);a[:,4]=np.clip(a[:,4],1,14);a[:,5]=np.clip(a[:,5],.5,2);a[:,6]=np.clip(a[:,6],180,750)
 return pd.DataFrame(a,columns=FEATURES).assign(condition=label)
data=pd.concat([make_class(i,seed=100+i) for i in range(5)],ignore_index=True).sample(frac=1,random_state=SEED).reset_index(drop=True)
print(data.shape);print(data.condition.value_counts().sort_index());data.head()""")
prepare=co("""# Add a few realistic missing sensor readings for the cleaning demonstration.
rng=np.random.default_rng(9);dirty=data.copy();dirty.loc[rng.choice(dirty.index,30,replace=False),"intake_c"]=np.nan
train,temp=train_test_split(dirty,test_size=.30,stratify=dirty.condition,random_state=SEED);val,test=train_test_split(temp,test_size=.50,stratify=temp.condition,random_state=SEED)
imputer=SimpleImputer(strategy="median").fit(train[FEATURES]);scaler=StandardScaler().fit(imputer.transform(train[FEATURES]))
def prep(d):return scaler.transform(imputer.transform(d[FEATURES]))
X_train,X_val,X_test=prep(train),prep(val),prep(test);y_train,y_val,y_test=train.condition.to_numpy(),val.condition.to_numpy(),test.condition.to_numpy()
print(X_train.shape,X_val.shape,X_test.shape)""")
mlp=co("""model=Sequential([Input((7,)),Dense(32,activation="relu"),Dropout(.12),Dense(16,activation="relu"),Dense(5,activation="softmax")]);model.compile(optimizer="adam",loss="sparse_categorical_crossentropy",metrics=["accuracy"]);model.summary()
print("Why MLP: one independent tabular row. CNN expects local signal/image structure; LSTM expects an ordered sequence; Transformer adds unnecessary capacity here.")""")
training=co("""early=EarlyStopping(monitor="val_loss",patience=7,restore_best_weights=True);history=model.fit(X_train,y_train,validation_data=(X_val,y_val),epochs=60,batch_size=48,callbacks=[early],verbose=0)
fig,ax=plt.subplots(1,2,figsize=(12,4));ax[0].plot(history.history["loss"],label="train");ax[0].plot(history.history["val_loss"],label="validation");ax[1].plot(history.history["accuracy"],label="train");ax[1].plot(history.history["val_accuracy"],label="validation")
for a in ax:a.set_xlabel("Epoch");a.grid(alpha=.2);a.legend()
plt.show()""")
prediction=co("""row=pd.DataFrame([example]);probs=model.predict(prep(row),verbose=0)[0];pred=int(np.argmax(probs));actions={0:"Continue simulated operation",1:"Simulated response: reduce load",2:"Simulated response: reduce load / inspect cooling",3:"Simulated response: inspect fuel-air condition",4:"Simulated response: schedule inspection"}
print("Predicted condition:",CLASSES[pred]);print("Confidence:",f"{probs[pred]:.1%}");print(actions[pred])
for c,p in zip(CLASSES,probs):print(f"{c:12s} {p:.1%}")""")
audit=co("""probs=model.predict(X_test,verbose=0);pred=np.argmax(probs,axis=1);print(classification_report(y_test,pred,target_names=CLASSES));ConfusionMatrixDisplay(confusion_matrix(y_test,pred),display_labels=CLASSES).plot(cmap="Blues",xticks_rotation=25);plt.show()
confidence=probs.max(1);print("Low-confidence test rows (<60%):",int((confidence<.6).sum()))
mins=train[FEATURES].min();maxs=train[FEATURES].max();outside=((row[FEATURES]<mins)|(row[FEATURES]>maxs)).any(axis=1).iloc[0];print("Example outside training ranges:",outside)
print("Limitations: synthetic regimes, snapshot only, no transient detection, no engine-family transfer study, no calibrated decision costs, no direct machinery control.")""")
body={"problem":[problem],"inputs":[inputs],"data":[data],"prepare":[prepare],"mlp":[mlp],"training":[training],"prediction":[prediction],"audit":[audit]}
for i,s in enumerate(bridge.STEPS,1):cells.extend(lesson(s,i,body[s["id"]]))
cells.append(md("""---
# Final engineering conclusion

An MLP is appropriate because each example is one independent row of seven named sensor readings. The model returns five condition probabilities, while the recommendation remains a separate, transparent simulated layer."""))
nb={"cells":cells,"metadata":{"colab":{"name":"Engine_Operating_Condition_MLP.ipynb","toc_visible":True,"provenance":[]},"kernelspec":{"display_name":"Python 3","name":"python3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":0}
out=BASE/"Engine_Operating_Condition_MLP.ipynb";out.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+"\n",encoding="utf-8");print("Wrote",out,"with",len(cells),"cells")
