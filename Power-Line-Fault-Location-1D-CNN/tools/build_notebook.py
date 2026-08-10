from pathlib import Path
import json,sys,textwrap
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE));import bridge
APP="https://power-line-fault-location.streamlit.app"
def md(s):return {"cell_type":"markdown","metadata":{},"source":textwrap.dedent(s).strip().splitlines(True)}
def co(s):return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":textwrap.dedent(s).strip().splitlines(True)}
def lesson(s,n,technical):
 i=n-1;p=bridge.PHASES[s["phase"]];prev=bridge.STEPS[i-1] if i else None;nxt=bridge.STEPS[i+1] if i<len(bridge.STEPS)-1 else None;nav=[]
 if prev:nav.append(f"◀ [Previous: {prev['civil']}]({APP}/?stage={prev['id']})")
 nav.append(f"[Project overview]({APP}/?stage=start)")
 if nxt:nav.append(f"[Next: {nxt['civil']}]({APP}/?stage={nxt['id']}) ▶")
 p12=md(f"""---
# {n}. {s['civil']}
### Phase {s['phase']+1} of {len(bridge.PHASES)} · {p[0]}

## Part 1 · On the power line
{s['site']}

## Part 2 · The engineering challenge
{s['challenge']}""")
 p3=md(f"""## Part 3 · Where the AI comes in
{s['ai_link']}

**Electrical Engineering:** {s['civil']} → **AI:** {s['ai']} → `{s['tech']}`

> 🎬 **See this illustrated and interactive:** [{APP}/?stage={s['id']}]({APP}/?stage={s['id']})

## Part 4 · The technical explanation""")
 p5=md(f"""## Part 5 · What you just built

**In the notebook:** {s['notebook']}

**Takeaway:** {s['takeaway']}

{' &nbsp;|&nbsp; '.join(nav)}""")
 return [p12,p3,*technical,p5]

cells=[md(f"""# ⚡ Power-Line Fault Section Identification Using Voltage–Current Waveforms and a 1D CNN

A 500×2 voltage/current transient is classified into one of four 5 km inspection sections on a simulated 20 km line.

> Educational synthetic locator only—not protection equipment or a trip command.

👉 **Open the interactive companion:** [{APP}]({APP}/?stage=start)"""),md(f"""## Complete workflow

Generate fault waveforms → normalize two channels → train 1D CNN → predict section probabilities → display kilometre region → audit neighbouring errors.

## Interactive learning journey

{chr(10).join(f"- [{s['civil']}]({APP}/?stage={s['id']}) — {s['ai']}" for s in bridge.STEPS)}"""),co("""import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score,classification_report,confusion_matrix,ConfusionMatrixDisplay
import tensorflow as tf
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Input,Conv1D,MaxPooling1D,GlobalAveragePooling1D,Dense,Dropout
from tensorflow.keras.callbacks import EarlyStopping
SEED=42;np.random.seed(SEED);tf.random.set_seed(SEED)
N=500;SECTIONS=["0–5 km","5–10 km","10–15 km","15–20 km"]""")]

problem=md("""A line trip protects equipment, but restoration work also needs a search region. This model ranks one of four sections for inspection. It does not replace impedance-based protection, travelling-wave methods, or field procedures.""")
sections=co("""def section_label(distance_km):return min(3,int(distance_km//5))
for d in [2,7,12,17]:print(d,"km → Section",section_label(d)+1,SECTIONS[section_label(d)])""")
physics=co("""def simulate_fault(distance,resistance,seed=0):
 rng=np.random.default_rng(seed);t=np.linspace(-.025,.075,N);phase=2*np.pi*50*t;v=np.sin(phase);i=.55*np.sin(phase-.18);on=t>=0
 attenuation=.34+.025*distance+.13*resistance;surge=5.2-.13*distance-.8*resistance
 v[on]*=attenuation;i[on]=surge*np.sin(phase[on]-.35)+.9*np.exp(-t[on]/.012)*np.sin(2*np.pi*520*t[on])
 v+=rng.normal(0,.025,N);i+=rng.normal(0,.045,N);return t,np.stack([v,i],axis=1).astype("float32")
t,w=simulate_fault(12.5,.3,7)
plt.figure(figsize=(13,4));plt.plot(t*1000,w[:,0],label="Voltage");plt.plot(t*1000,w[:,1],label="Current");plt.axvline(0,color="black",ls="--");plt.xlabel("Time (ms)");plt.ylabel("pu");plt.grid(alpha=.2);plt.legend();plt.show()""")
generate=co("""rng=np.random.default_rng(SEED);X,y,distances=[],[],[]
for label in range(4):
 for k in range(450):
  d=rng.uniform(label*5+.05,(label+1)*5-.05);r=rng.uniform(0,1);_,wave=simulate_fault(d,r,10000*label+k);X.append(wave);y.append(label);distances.append(d)
X=np.array(X);y=np.array(y);distances=np.array(distances)
print(X.shape,"= examples × 500 samples × 2 channels")
pd.DataFrame({"distance_km":distances[:8],"label":y[:8],"voltage_min":X[:8,:,0].min(1),"current_peak":np.abs(X[:8,:,1]).max(1)})""")
prepare=co("""X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=.20,stratify=y,random_state=SEED)
X_train,X_val,y_train,y_val=train_test_split(X_train,y_train,test_size=.20,stratify=y_train,random_state=SEED)
scaler=StandardScaler().fit(X_train.reshape(-1,2))
def scale(a):return scaler.transform(a.reshape(-1,2)).reshape(a.shape)
X_train,X_val,X_test=scale(X_train),scale(X_val),scale(X_test)
print(X_train.shape,X_val.shape,X_test.shape)""")
cnn=co("""model=Sequential([Input((500,2)),Conv1D(32,9,activation="relu"),MaxPooling1D(2),Conv1D(64,7,activation="relu"),MaxPooling1D(2),Conv1D(96,5,activation="relu"),GlobalAveragePooling1D(),Dropout(.2),Dense(32,activation="relu"),Dense(4,activation="softmax")])
model.compile(optimizer="adam",loss="sparse_categorical_crossentropy",metrics=["accuracy"]);model.summary()""")
training=co("""early=EarlyStopping(monitor="val_loss",patience=6,restore_best_weights=True)
history=model.fit(X_train,y_train,validation_data=(X_val,y_val),epochs=45,batch_size=48,callbacks=[early],verbose=0)
fig,ax=plt.subplots(1,2,figsize=(12,4));ax[0].plot(history.history["loss"],label="train");ax[0].plot(history.history["val_loss"],label="validation");ax[1].plot(history.history["accuracy"],label="train");ax[1].plot(history.history["val_accuracy"],label="validation")
for a in ax:a.set_xlabel("Epoch");a.grid(alpha=.2);a.legend()
plt.show()""")
prediction=co("""distance=12.5;_,new_wave=simulate_fault(distance,.3,999);new_scaled=scale(new_wave[None,...]);probs=model.predict(new_scaled,verbose=0)[0];pred=int(np.argmax(probs))
print("FAULT DETECTED");print("Predicted fault section: SECTION",pred+1);print("Region:",SECTIONS[pred],"from Substation A");print("Confidence:",f"{probs[pred]:.1%}")
for i,p in enumerate(probs):print(f"Section {i+1}: {p:.1%}")""")
audit=co("""start=time.perf_counter();test_probs=model.predict(X_test,verbose=0);elapsed=time.perf_counter()-start;pred=np.argmax(test_probs,axis=1)
print(classification_report(y_test,pred,target_names=[f"Section {i}" for i in range(1,5)]));print(f"Mean inference time: {1000*elapsed/len(X_test):.3f} ms/sample")
errors=np.abs(pred-y_test);print("Adjacent-section errors:",int((errors==1).sum()));print("Non-adjacent errors:",int((errors>1).sum()))
ConfusionMatrixDisplay(confusion_matrix(y_test,pred),display_labels=["S1","S2","S3","S4"]).plot(cmap="Blues");plt.show()
# Deliberately weak magnitude-only baseline.
peak=np.abs(X_test[:,:,1]).max(1);threshold_pred=np.digitize(peak,np.quantile(peak,[.25,.5,.75]));print("Magnitude baseline accuracy:",accuracy_score(y_test,threshold_pred));print("1D CNN accuracy:",accuracy_score(y_test,pred))
print("Field exclusions: simplified line, synthetic source/fault model, no CT/CVT saturation, no topology changes, no timing uncertainty, no protection coordination study.")""")
body={"problem":[problem],"sections":[sections],"physics":[physics],"generate":[generate],"prepare":[prepare],"cnn":[cnn],"training":[training],"prediction":[prediction],"audit":[audit]}
for i,s in enumerate(bridge.STEPS,1):cells.extend(lesson(s,i,body[s["id"]]))
cells.append(md("""---
# Final engineering conclusion

The 1D CNN learns directly from synchronized voltage and current transients and returns a probable 5 km inspection region. The output can prioritize field inspection, but the synthetic notebook is not protection logic or a validated utility locator."""))
nb={"cells":cells,"metadata":{"colab":{"name":"Power_Line_Fault_Section_1D_CNN.ipynb","toc_visible":True,"provenance":[]},"kernelspec":{"display_name":"Python 3","name":"python3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":0}
out=BASE/"Power_Line_Fault_Section_1D_CNN.ipynb";out.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+"\n",encoding="utf-8");print("Wrote",out,"with",len(cells),"cells")
