"""Generate the Dam Flood and Water Security Colab notebook."""
from pathlib import Path
import json,sys,textwrap
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE));import bridge
APP="https://dam-flood-water-security.streamlit.app"
def md(s):return {"cell_type":"markdown","metadata":{},"source":textwrap.dedent(s).strip().splitlines(True)}
def co(s):return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":textwrap.dedent(s).strip().splitlines(True)}
def lesson(s,n,content):
 p=bridge.PHASES[s["phase"]]
 i=n-1;prev_s=bridge.STEPS[i-1] if i>0 else None;next_s=bridge.STEPS[i+1] if i<len(bridge.STEPS)-1 else None
 nav=[]
 if prev_s:nav.append(f"◀ [Previous: {prev_s['civil']}]({APP}/?stage={prev_s['id']})")
 nav.append(f"[Project overview]({APP}/?stage=start)")
 if next_s:nav.append(f"[Next: {next_s['civil']}]({APP}/?stage={next_s['id']}) ▶")
 part12=md(f"""---
# {n}. {s['civil']}
### Phase {s['phase']+1} of {len(bridge.PHASES)} · {p[0]}

## Part 1 · At the dam
{s['site']}

## Part 2 · Engineering challenge
{s['challenge']}

""")
 part3=md(f"""## Part 3 · Where AI comes in
{s['ai_link']}

**Civil Engineering:** {s['civil']} → **AI:** {s['ai']} → `{s['tech']}`

> 🎬 **See this illustrated and interactive:** [{APP}/?stage={s['id']}]({APP}/?stage={s['id']})

## Part 4 · Technical explanation""")
 part5=md(f"""## Part 5 · What you just built

**In the notebook:** {s['notebook']}

**Takeaway:** {s['takeaway']}

{' &nbsp;|&nbsp; '.join(nav)}""")
 return [part12,part3,*content,part5]

cells=[md(f"""# 🌊 The Dam That Chooses Between Flood Protection and Water Security
## Civil Engineering + Deep Learning with an MLP

Predict reservoir level six hours after a forecast storm, then select a pre-release that creates flood storage without ignoring downstream river condition or stored-water security.

> Educational decision-support simulation only. This notebook does not authorize or recommend operation of a real dam.

👉 **Open the interactive companion:** [{APP}]({APP}/?stage=start)"""),
md(f"""## Six inputs and one model output

| Input | Unit |
|---|---:|
| Current reservoir level | % |
| Forecast rainfall | mm |
| Upstream inflow | m³/s |
| Downstream river level | encoded Low–Very high |
| Reservoir capacity remaining | % |
| Current release rate | m³/s |

**MLP output:** predicted reservoir level after six hours. A separate rule-based layer selects and constrains the pre-release.

## Interactive learning journey

{chr(10).join(f"- [{s['civil']}]({APP}/?stage={s['id']}) — {s['ai']}" for s in bridge.STEPS)}"""),
co("""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import tensorflow as tf
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Input,Dense,Dropout
from tensorflow.keras.callbacks import EarlyStopping
SEED=42;np.random.seed(SEED);tf.random.set_seed(SEED)
FEATURES=["level_pct","rain_mm","inflow_m3s","downstream_code","free_storage_pct","current_release_m3s"]
print("Six summarized inputs → MLP → six-hour reservoir level")""")]
body={}
body["dilemma"]=[md("""A pre-release creates storage before storm inflow arrives. Its benefit is avoiding a late emergency spill; its cost is water that may not be recovered if the forecast overstates the event. The model predicts one physical quantity. The operating balance remains a transparent decision problem.""")]
body["inputs"]=[co("""example={"level_pct":88,"rain_mm":120,"inflow_m3s":420,"downstream_code":2,"free_storage_pct":12,"current_release_m3s":150}
pd.Series(example,name="Example pre-storm snapshot")""")]
body["data"]=[co("""def generate_events(n=5000,seed=42):
 rng=np.random.default_rng(seed);level=rng.uniform(55,96,n);rain=np.clip(rng.gamma(2.1,38,n),0,230);inflow=np.clip(55+2.4*rain+rng.normal(0,60,n),30,750);down=np.clip((.006*inflow+rng.normal(0,.65,n)).astype(int),0,3);free=100-level;release=np.clip(45+2.2*np.maximum(level-70,0)+rng.normal(0,35,n),0,450)
 # Simplified six-hour storage response; noise represents forecast/model uncertainty.
 storm=.042*rain+.0052*inflow*6-.0044*release*6+.55*down+rng.normal(0,.8,n)
 future=np.clip(level+storm,30,103)
 return pd.DataFrame(dict(level_pct=level,rain_mm=rain,inflow_m3s=inflow,downstream_code=down,free_storage_pct=free,current_release_m3s=release,future_level_pct=future))
data=generate_events();print(data.shape);data.head()"""),co("""# Conservation check in simplified percentage-storage units.
assert np.allclose(data.free_storage_pct,100-data.level_pct)
data.describe().T""")]
body["prepare"]=[co("""# Time-ordered split: first 70% train, next 15% validate, last 15% test.
n=len(data);i1=int(.70*n);i2=int(.85*n)
train,val,test=data.iloc[:i1],data.iloc[i1:i2],data.iloc[i2:]
scaler=StandardScaler().fit(train[FEATURES])
X_train=scaler.transform(train[FEATURES]);X_val=scaler.transform(val[FEATURES]);X_test=scaler.transform(test[FEATURES])
y_train=train.future_level_pct.to_numpy();y_val=val.future_level_pct.to_numpy();y_test=test.future_level_pct.to_numpy()
print(X_train.shape,X_val.shape,X_test.shape)""")]
body["mlp"]=[co("""model=Sequential([Input(shape=(6,)),Dense(64,activation="relu"),Dropout(.10),Dense(32,activation="relu"),Dense(16,activation="relu"),Dense(1)])
model.compile(optimizer="adam",loss="mae",metrics=["mae"])
early=EarlyStopping(monitor="val_loss",patience=7,restore_best_weights=True)
history=model.fit(X_train,y_train,validation_data=(X_val,y_val),epochs=70,batch_size=64,callbacks=[early],verbose=0)
model.summary()
plt.figure(figsize=(9,4));plt.plot(history.history["loss"],label="train");plt.plot(history.history["val_loss"],label="validation");plt.xlabel("Epoch");plt.ylabel("MAE (%)");plt.grid(alpha=.2);plt.legend();plt.show()""")]
body["decision"]=[co("""def release_decision(predicted_level,downstream_code):
    proposed=0 if predicted_level<85 else 120 if predicted_level<90 else 250 if predicted_level<=95 else 400
    downstream_caps={0:450,1:320,2:250,3:180} # project assumptions for this simulation
    return min(proposed,downstream_caps[int(downstream_code)]),proposed

sample=pd.DataFrame([example]);pred=float(model.predict(scaler.transform(sample[FEATURES]),verbose=0)[0,0])
recommended,unconstrained=release_decision(pred,example["downstream_code"])
print(f"Predicted level after 6 hours: {pred:.1f}%")
print("Unconstrained release band:",unconstrained,"m³/s")
print("Downstream-constrained release:",recommended,"m³/s")""")]
body["compare"]=[co("""def scenario(level,rain,inflow,current_release,pre_release):
 hours=np.arange(7);shape=np.array([.25,.65,1,.85,.55,.30,.12]);path=[level];spill=[]
 for h in range(6):
  gain=(rain/120)*shape[h]*2.25+inflow/850
  early=pre_release/230 if h<3 else 0
  nxt=path[-1]+gain-current_release/300-early
  spill.append(max(0,nxt-100)*100);path.append(min(100,nxt))
 return np.array(path),max(spill+[0])

no_ai,no_spill=scenario(88,120,420,150,0);with_ai,ai_spill=scenario(88,120,420,150,recommended)
comparison=pd.DataFrame({"Metric":["Peak reservoir level","Emergency spill index","Water released before storm","Water retained after storm"],"No pre-release":[f"{no_ai.max():.1f}%",f"{no_spill:.0f}","0 Mm³",f"{no_ai[-1]:.1f}%"],"AI pre-release":[f"{with_ai.max():.1f}%",f"{ai_spill:.0f}",f"{recommended*3*3600/1e6:.2f} Mm³",f"{with_ai[-1]:.1f}%"]})
display(comparison)
plt.figure(figsize=(10,4));plt.plot(no_ai,"o-",label="Without AI");plt.plot(with_ai,"o-",label="With constrained pre-release");plt.axhline(100,color="red",ls="--");plt.xlabel("Hours");plt.ylabel("Reservoir level (%)");plt.grid(alpha=.2);plt.legend();plt.show()""")]
body["audit"]=[co("""pred_test=model.predict(X_test,verbose=0).ravel();mae=mean_absolute_error(y_test,pred_test);rmse=mean_squared_error(y_test,pred_test)**.5
extreme=y_test>95;under=((y_test-pred_test)>2)&extreme
print(f"Test MAE: {mae:.2f} percentage points");print(f"Test RMSE: {rmse:.2f} percentage points")
print(f"Extreme events (>95% actual): {extreme.sum()}");print(f"Extreme underpredictions by >2 points: {under.sum()}")
plt.figure(figsize=(6,6));plt.scatter(y_test,pred_test,s=10,alpha=.35);plt.plot([50,103],[50,103],"r--");plt.xlabel("Actual (%)");plt.ylabel("Predicted (%)");plt.grid(alpha=.2);plt.show()
print("Deployment exclusions: no real dam, no calibrated catchment, no forecast ensemble, no rule curve, no emergency-action integration, and no operational authority.")""")]
for i,s in enumerate(bridge.STEPS,1):cells.extend(lesson(s,i,body[s["id"]]))
cells.append(md("""---
# Final engineering conclusion

The MLP predicts a six-hour reservoir level from six summarized conditions. A separate project-assumption rule proposes a pre-release and caps it when the downstream river is high. The scenario comparison evaluates both flood protection and retained water. This separation keeps the model, operating assumptions, and safety constraints visible."""))
nb={"cells":cells,"metadata":{"colab":{"name":"Dam_Flood_Water_Security_MLP.ipynb","toc_visible":True,"provenance":[]},"kernelspec":{"display_name":"Python 3","name":"python3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":0}
out=BASE/"Dam_Flood_Water_Security_MLP.ipynb";out.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+"\n",encoding="utf-8");print("Wrote",out,"with",len(cells),"cells")
