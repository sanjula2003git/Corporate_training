from pathlib import Path
import json,sys,textwrap
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE));import bridge
APP="https://gearbox-vibration-prediction.streamlit.app"
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

## Part 1 · At the gearbox
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

cells=[md(f"""# ⚙️ Predictive Gearbox Vibration Control Using a 1D Convolutional Neural Network

Forecast vibration 30 seconds ahead from a 1000-sample vibration waveform plus RPM, torque, temperature, and motor current.

> The 7 mm/s danger threshold and all responses are educational simulation assumptions.

👉 **Open the interactive companion:** [{APP}]({APP}/?stage=start)"""),md(f"""## Complete workflow

Waveform → 1D CNN features + operating values → fusion network → future vibration → project condition band → simulated response.

## Interactive learning journey

{chr(10).join(f"- [{s['civil']}]({APP}/?stage={s['id']}) — {s['ai']}" for s in bridge.STEPS)}"""),co("""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error,mean_squared_error,confusion_matrix,ConfusionMatrixDisplay
import tensorflow as tf
from tensorflow.keras import layers,Model
from tensorflow.keras.callbacks import EarlyStopping
SEED=42;np.random.seed(SEED);tf.random.set_seed(SEED)
N=1000;THRESHOLD=7.0""")]
problem=md("""The target is continuous future vibration in mm/s. Normal, Warning, and Dangerous are calculated afterward so the model and project operating assumption remain separate.""")
inputs=co("""example={"rpm":1800,"torque_nm":42,"current_vibration":4.8,"temperature_c":68,"motor_current_a":11.2}
pd.Series(example,name="Current operating state")""")
wave=co("""def waveform(rpm,torque,wear,resonance,seed):
 rng=np.random.default_rng(seed);t=np.linspace(0,.5,N);shaft=rpm/60;mesh=shaft*12;amp=.7+1.5*wear+1.8*resonance+torque/90
 x=amp*np.sin(2*np.pi*shaft*t)+.32*amp*np.sin(2*np.pi*mesh*t)+.18*amp*np.sin(2*np.pi*(mesh-shaft)*t)
 impacts=(rng.random(N)<wear*.018)*rng.normal(0,3*amp,N);x+=np.convolve(impacts,np.exp(-np.arange(20)/5),mode="same")+.12*rng.normal(size=N);return t,x.astype("float32")
fig,ax=plt.subplots(1,3,figsize=(15,3))
for a,(w,r,title) in zip(ax,[(.1,.1,"Normal"),(.5,.5,"Developing"),(.9,.9,"Dangerous")]):
 t,x=waveform(1800,42,w,r,int(w*100));a.plot(t,x,linewidth=.6);a.set_title(title);a.grid(alpha=.2)
plt.show()""")
data=co("""rng=np.random.default_rng(SEED);waves=[];ops=[];targets=[]
for k in range(2400):
 rpm=rng.uniform(700,2900);torque=rng.uniform(8,85);temp=rng.uniform(35,95);motor=2.5+.18*torque+rng.normal(0,.7);wear=rng.uniform(0,1);res=np.exp(-((rpm-rng.choice([1500,2100]))/260)**2);current=max(.5,.7+.0011*rpm+.022*torque+.025*(temp-45)+1.6*wear+1.4*res+rng.normal(0,.35));t,x=waveform(rpm,torque,wear,res,k);future=max(.5,current+.00008*torque*rpm+.020*(temp-50)+1.3*wear+1.8*res-2.7+rng.normal(0,.3));waves.append(x);ops.append([rpm,torque,temp,motor]);targets.append(future)
Xw=np.array(waves)[...,None];Xo=np.array(ops,dtype="float32");y=np.array(targets,dtype="float32")
print(Xw.shape,Xo.shape,y.shape);print("Future range:",y.min(),y.max())""")
prepare=co("""indices=np.arange(len(y));tr,tmp=train_test_split(indices,test_size=.30,random_state=SEED);va,te=train_test_split(tmp,test_size=.50,random_state=SEED)
wave_scaler=StandardScaler().fit(Xw[tr].reshape(-1,1));op_scaler=StandardScaler().fit(Xo[tr])
def sw(a):return wave_scaler.transform(a.reshape(-1,1)).reshape(a.shape)
Xw_train,Xw_val,Xw_test=sw(Xw[tr]),sw(Xw[va]),sw(Xw[te]);Xo_train,Xo_val,Xo_test=op_scaler.transform(Xo[tr]),op_scaler.transform(Xo[va]),op_scaler.transform(Xo[te]);y_train,y_val,y_test=y[tr],y[va],y[te]
print(Xw_train.shape,Xo_train.shape)""")
fusion=co("""win=layers.Input((1000,1),name="vibration_waveform");x=layers.Conv1D(32,11,activation="relu")(win);x=layers.MaxPooling1D(2)(x);x=layers.Conv1D(64,7,activation="relu")(x);x=layers.GlobalAveragePooling1D()(x)
oin=layers.Input((4,),name="operating_values");o=layers.Dense(16,activation="relu")(oin);f=layers.Concatenate()([x,o]);f=layers.Dense(48,activation="relu")(f);f=layers.Dropout(.15)(f);out=layers.Dense(1)(f);model=Model([win,oin],out);model.compile(optimizer="adam",loss="mae",metrics=["mae"]);model.summary()""")
forecast=co("""early=EarlyStopping(monitor="val_loss",patience=6,restore_best_weights=True);history=model.fit([Xw_train,Xo_train],y_train,validation_data=([Xw_val,Xo_val],y_val),epochs=45,batch_size=48,callbacks=[early],verbose=0)
pred=model.predict([Xw_test,Xo_test],verbose=0).ravel();print("MAE:",mean_absolute_error(y_test,pred));print("RMSE:",mean_squared_error(y_test,pred)**.5)
plt.figure(figsize=(6,6));plt.scatter(y_test,pred,s=10,alpha=.35);plt.plot([0,12],[0,12],"r--");plt.xlabel("Actual future mm/s");plt.ylabel("Predicted future mm/s");plt.grid(alpha=.2);plt.show()""")
decision=co("""def condition(v):return "NORMAL" if v<5 else "WARNING" if v<THRESHOLD else "DANGEROUS"
def response(c):return {"NORMAL":"Continue simulated operation","WARNING":"Simulated response: reduce RPM slightly","DANGEROUS":"Simulated response: move away from speed / stop for inspection"}[c]
i=8;print(f"Current vibration: {y_test[i]-1.5:.1f} mm/s");print(f"Predicted after 30 s: {pred[i]:.1f} mm/s");print("Condition:",condition(pred[i]));print(response(condition(pred[i])))""")
compare=co("""current=4.8;future=8.1;t=np.arange(31);without=current+(future-current)*(t/30)**1.35;with_ai=without.copy();with_ai[8:]-=np.linspace(0,future-6.2,23)
comparison=pd.DataFrame({"Metric":["Peak vibration","Time above threshold","Emergency shutdown","Early warning"],"Without AI":[f"{without.max():.1f} mm/s",f"{(without>7).sum()} s","Yes","0 s"],"With AI":[f"{with_ai.max():.1f} mm/s",f"{(with_ai>7).sum()} s","Avoided","22 s"]});display(comparison)
plt.plot(t,without,label="Without AI");plt.plot(t,with_ai,label="With simulated response");plt.axhline(7,color="red",ls="--");plt.xlabel("Seconds");plt.ylabel("Vibration mm/s");plt.grid(alpha=.2);plt.legend();plt.show()
actual_band=np.array([condition(v) for v in y_test]);pred_band=np.array([condition(v) for v in pred]);ConfusionMatrixDisplay(confusion_matrix(actual_band,pred_band,labels=["NORMAL","WARNING","DANGEROUS"]),display_labels=["Normal","Warning","Dangerous"]).plot(cmap="Blues");plt.show()
print("Limitations: synthetic waveform, simplified resonance/wear, no gearbox-specific limits, no sensor mounting study, no causal diagnosis, no validated control response.")""")
body={"problem":[problem],"inputs":[inputs],"waveform":[wave],"data":[data],"prepare":[prepare],"fusion":[fusion],"forecast":[forecast],"decision":[decision],"compare":[compare]}
for i,s in enumerate(bridge.STEPS,1):cells.extend(lesson(s,i,body[s["id"]]))
cells.append(md("""---
# Final engineering conclusion

The model fuses learned vibration-waveform patterns with current operating state to predict vibration 30 seconds ahead. A separate project rule turns that physical forecast into a simulated condition and response. Real machinery requires equipment-specific validation and approved controls."""))
nb={"cells":cells,"metadata":{"colab":{"name":"Gearbox_Vibration_Prediction_1D_CNN.ipynb","toc_visible":True,"provenance":[]},"kernelspec":{"display_name":"Python 3","name":"python3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":0}
out=BASE/"Gearbox_Vibration_Prediction_1D_CNN.ipynb";out.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+"\n",encoding="utf-8");print("Wrote",out,"with",len(cells),"cells")
