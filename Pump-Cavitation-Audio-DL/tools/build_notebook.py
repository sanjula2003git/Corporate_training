"""Generate the Colab notebook from the shared teaching scaffold."""
from pathlib import Path
import json, sys, textwrap
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import bridge

APP = "https://pump-cavitation-audio.streamlit.app"

def md(s):
    return {"cell_type":"markdown","metadata":{},"source":textwrap.dedent(s).strip().splitlines(True)}

def co(s):
    return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":textwrap.dedent(s).strip().splitlines(True)}

def lesson(s,n,body):
    p=bridge.PHASES[s["phase"]]
    i=n-1
    prev_s=bridge.STEPS[i-1] if i>0 else None
    next_s=bridge.STEPS[i+1] if i<len(bridge.STEPS)-1 else None
    nav=[]
    if prev_s: nav.append(f"◀ [Previous: {prev_s['civil']}]({APP}/?stage={prev_s['id']})")
    nav.append(f"[Project overview]({APP}/?stage=start)")
    if next_s: nav.append(f"[Next: {next_s['civil']}]({APP}/?stage={next_s['id']}) ▶")
    part12=md(f"""---
# {n}. {s['civil']}
### Phase {s['phase']+1} of {len(bridge.PHASES)} · {p[0]}

## Part 1 · At the pump
{s['site']}

## Part 2 · Engineering challenge
{s['challenge']}

""")
    part3=md(f"""## Part 3 · Where AI comes in
{s['ai_link']}

**Mechanical Engineering:** {s['civil']} → **AI:** {s['ai']} → `{s['tech']}`

> 🎬 **See this illustrated and interactive:** [{APP}/?stage={s['id']}]({APP}/?stage={s['id']})

## Part 4 · Technical explanation""")
    part5=md(f"""## Part 5 · What you just built

**In the notebook:** {s['notebook']}

**Takeaway:** {s['takeaway']}

{' &nbsp;|&nbsp; '.join(nav)}""")
    return [part12,part3,*body,part5]

cells=[md(f"""# 🔊 Detecting Centrifugal-Pump Cavitation Using Sound
## Mechanical Engineering + Signal Processing + Deep Learning

This notebook turns a short pump recording into a log Mel-spectrogram and uses a 2D CNN to classify **Normal**, **Mild Cavitation**, or **Severe Cavitation**.

> All operating responses are simulated educational recommendations. They are not instructions for real industrial equipment.

👉 **Open the interactive companion:** [{APP}]({APP}/?stage=start)"""),
md(f"""## The complete system

Pump sound → normalized waveform → Mel-spectrogram → 2D CNN → condition probability → simulated engineering response.

Pump RPM, inlet pressure, flow rate, and valve opening are retained as engineering metadata for generation and labelling. **Only the spectrogram enters the CNN.**

## Interactive learning journey

{chr(10).join(f"- [{s['civil']}]({APP}/?stage={s['id']}) — {s['ai']}" for s in bridge.STEPS)}"""),
co("""# Colab setup: uncomment if packages are missing.
# !pip -q install librosa tensorflow scikit-learn soundfile
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import librosa, librosa.display
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import tensorflow as tf
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
SEED=42; np.random.seed(SEED); tf.random.set_seed(SEED)
SR,DURATION,N_MELS=8000,4,64
CLASSES=["Normal","Mild Cavitation","Severe Cavitation"]
print("Audio duration:",DURATION,"s | sample rate:",SR,"Hz")""")]

body={}
body["cavitation"]=[md("""Cavitation begins when local pressure falls below the liquid's vapour pressure. Bubbles form near the impeller eye and collapse after entering a higher-pressure region. The collapse produces pressure pulses, broadband noise, vibration, and potentially erosion.

The notebook does not claim that sound alone proves a hydraulic diagnosis. It demonstrates how sound can contribute to condition monitoring.""")]
body["listen"]=[co("""def synth_clip(label,seed):
    rng=np.random.default_rng(seed); t=np.arange(SR*DURATION)/SR
    rpm=rng.uniform(1100,2200); shaft=rpm/60
    x=.34*np.sin(2*np.pi*shaft*t)+.17*np.sin(2*np.pi*2*shaft*t)+.08*np.sin(2*np.pi*3*shaft*t)
    x+=.025*rng.normal(size=len(t))
    severity=[0,.45,1.0][label]
    impulses=rng.random(len(t)) < severity*.006
    crack=np.convolve(impulses*rng.normal(size=len(t)),np.exp(-np.arange(70)/13),mode="same")
    x+=severity*(.18*rng.normal(size=len(t))+.8*crack)
    inlet=max(.2,1.8-1.15*severity+rng.normal(0,.08)); flow=80-18*severity+rng.normal(0,3)
    valve=92-30*severity+rng.normal(0,3)
    return x.astype("float32"),dict(rpm=rpm,inlet_pressure_bar=inlet,flow_l_min=flow,valve_open_pct=valve)

x,meta=synth_clip(2,7)
print(meta); print("waveform samples:",x.shape)
plt.figure(figsize=(13,3));plt.plot(np.arange(len(x))/SR,x,linewidth=.5);plt.xlabel("Time (s)");plt.ylabel("Amplitude");plt.grid(alpha=.2);plt.show()""")]
body["waveform"]=[co("""def normalize_audio(x):
    x=x-np.mean(x)
    return x/(np.max(np.abs(x))+1e-9)

x_norm=normalize_audio(x)
print("Mean:",x_norm.mean().round(6),"Peak:",np.abs(x_norm).max())""")]
body["spectrogram"]=[co("""def mel_image(x):
    x=normalize_audio(x)
    mel=librosa.feature.melspectrogram(y=x,sr=SR,n_fft=512,hop_length=128,n_mels=N_MELS,fmin=20,fmax=SR/2)
    return librosa.power_to_db(mel,ref=np.max).astype("float32")

fig,ax=plt.subplots(1,3,figsize=(16,4))
for label,name in enumerate(CLASSES):
    sample,_=synth_clip(label,100+label)
    librosa.display.specshow(mel_image(sample),sr=SR,hop_length=128,x_axis="time",y_axis="mel",ax=ax[label],cmap="magma")
    ax[label].set_title(name)
plt.tight_layout();plt.show()""")]
body["cnn"]=[co("""X,y,metadata=[],[],[]
for label in range(3):
    for run in range(120):
        audio,meta=synth_clip(label,10000*label+run)
        X.append(mel_image(audio));y.append(label);metadata.append(meta)
X=np.array(X)[...,None];y=np.array(y)
print("CNN input:",X.shape,"labels:",y.shape)

X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=.20,stratify=y,random_state=SEED)
X_train,X_val,y_train,y_val=train_test_split(X_train,y_train,test_size=.20,stratify=y_train,random_state=SEED)
model=Sequential([Input(shape=X.shape[1:]),Conv2D(16,3,activation="relu"),MaxPooling2D(),
                  Conv2D(32,3,activation="relu"),MaxPooling2D(),Flatten(),Dense(48,activation="relu"),
                  Dropout(.25),Dense(3,activation="softmax")])
model.compile(optimizer="adam",loss="sparse_categorical_crossentropy",metrics=["accuracy"])
model.summary()""")]
body["training"]=[co("""early=EarlyStopping(monitor="val_loss",patience=5,restore_best_weights=True)
history=model.fit(X_train,y_train,validation_data=(X_val,y_val),epochs=35,batch_size=24,callbacks=[early],verbose=0)
fig,ax=plt.subplots(1,2,figsize=(12,4))
ax[0].plot(history.history["loss"],label="train");ax[0].plot(history.history["val_loss"],label="validation");ax[0].set_title("Loss")
ax[1].plot(history.history["accuracy"],label="train");ax[1].plot(history.history["val_accuracy"],label="validation");ax[1].set_title("Accuracy")
for a in ax:a.set_xlabel("Epoch");a.grid(alpha=.2);a.legend()
plt.show()""")]
body["prediction"]=[co("""i=5;probs=model.predict(X_test[i:i+1],verbose=0)[0];pred=int(np.argmax(probs))
print("Pump Condition:",CLASSES[pred]);print("Confidence:",f"{probs[pred]:.1%}")
for name,p in zip(CLASSES,probs):print(f"  {name:18s} {p:.1%}")
responses={0:"Continue simulated operation",1:"Reduce simulated speed or inspect inlet condition",2:"Stop or reduce simulated operation and inspect the pump system"}
print("Recommended simulated response:",responses[pred])
plt.figure(figsize=(10,4));librosa.display.specshow(X_test[i,:,:,0],sr=SR,hop_length=128,x_axis="time",y_axis="mel",cmap="magma");plt.colorbar(format="%+2.0f dB");plt.title(CLASSES[pred]);plt.show()""")]
body["audit"]=[co("""test_probs=model.predict(X_test,verbose=0);test_pred=np.argmax(test_probs,axis=1)
print(classification_report(y_test,test_pred,target_names=CLASSES))
cm=confusion_matrix(y_test,test_pred)
ConfusionMatrixDisplay(cm,display_labels=CLASSES).plot(cmap="Blues",xticks_rotation=20)
plt.title("Unseen synthetic clips");plt.show()
print("Limitations: synthetic audio, one simulated pump family, simplified noise, no microphone/domain-shift study.")
print("A real study must use controlled labelled pump tests and independent validation across pumps, loads, microphones, and sites.")""")]

for i,s in enumerate(bridge.STEPS,1):
    cells.extend(lesson(s,i,body[s["id"]]))
cells.append(md("""---
# Final engineering conclusion

The project connects three disciplines: cavitation physics supplies the phenomenon, signal processing makes its sound visible, and a 2D CNN learns time-frequency patterns. The final output is a condition probability and a **simulated** response—not an autonomous industrial control instruction."""))
nb={"cells":cells,"metadata":{"colab":{"name":"Pump_Cavitation_Audio_CNN.ipynb","toc_visible":True,"provenance":[]},"kernelspec":{"display_name":"Python 3","name":"python3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":0}
out=BASE/"Pump_Cavitation_Audio_CNN.ipynb"
out.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+"\n",encoding="utf-8")
print("Wrote",out,"with",len(cells),"cells")
