from pathlib import Path
import json,sys,textwrap
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE));import bridge
APP="https://generative-bracket-vae.streamlit.app"
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

## Part 1 · In mechanical design
{s['site']}

## Part 2 · The engineering challenge
{s['challenge']}""")
 p3=md(f"""## Part 3 · Where the AI comes in
{s['ai_link']}

**Mechanical Design:** {s['civil']} → **AI:** {s['ai']} → `{s['tech']}`

> 🎬 **See this illustrated and interactive:** [{APP}/?stage={s['id']}]({APP}/?stage={s['id']})

## Part 4 · The technical explanation""")
 p5=md(f"""## Part 5 · What you just built

**In the notebook:** {s['notebook']}

**Takeaway:** {s['takeaway']}

{' &nbsp;|&nbsp; '.join(nav)}""")
 return [p12,p3,*technical,p5]

cells=[md(f"""# ⚙️ Generative AI for Lightweight Mechanical Bracket Design Using a VAE

**Question:** Can a VAE learn existing mechanical shapes and generate lighter design alternatives automatically?

> Generated silhouettes are educational candidates, not validated components.

👉 **Open the interactive companion:** [{APP}]({APP}/?stage=start)"""),md(f"""## Complete workflow

Bracket masks → encoder → 16-variable latent distribution → decoder → new masks → geometry checks → material-area ranking.

## Interactive learning journey

{chr(10).join(f"- [{s['civil']}]({APP}/?stage={s['id']}) — {s['ai']}" for s in bridge.STEPS)}"""),co("""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import ndimage
import tensorflow as tf
from tensorflow.keras import layers,Model
SEED=42;np.random.seed(SEED);tf.random.set_seed(SEED)
SIZE,LATENT_DIM=64,16
Y,X=np.mgrid[:SIZE,:SIZE];MOUNTS=[(18,46),(46,18)]""")]

setup=co("""def make_bracket(seed=0):
 rng=np.random.default_rng(seed);m=np.zeros((SIZE,SIZE),bool);r=rng.uniform(7,10)
 for cx,cy in MOUNTS:m|=(X-cx)**2+(Y-cy)**2<=r*r
 slope=rng.uniform(-1.12,-.86);intercept=rng.uniform(59,67);thick=rng.uniform(5.5,9)
 m|=(np.abs(Y-(slope*X+intercept))<thick)&(X>10)&(X<54)
 m|=(Y>rng.uniform(42,48))&(Y<rng.uniform(53,58))&(X>9)&(X<35)
 m|=(X>rng.uniform(39,44))&(X<rng.uniform(51,56))&(Y>10)&(Y<39)
 for cx,cy in MOUNTS:m[(X-cx)**2+(Y-cy)**2<rng.uniform(3.5,4.8)**2]=0
 cx,cy=rng.uniform(28,36),rng.uniform(29,39);rx,ry=rng.uniform(4,9),rng.uniform(3,7)
 m[((X-cx)/rx)**2+((Y-cy)/ry)**2<1]=0
 return m.astype("float32")
baseline=make_bracket(4)
plt.imshow(baseline,cmap="gray");plt.title("Baseline bracket");plt.axis("off");plt.show()""")
pixels=co("""print("Grid:",baseline.shape,"Material pixels:",int(baseline.sum()))
plt.figure(figsize=(7,7));plt.imshow(baseline,cmap="gray",interpolation="nearest");plt.xticks(range(0,65,8));plt.yticks(range(0,65,8));plt.grid(alpha=.25);plt.show()""")
dataset=co("""images=np.array([make_bracket(i) for i in range(900)])[...,None]
rng=np.random.default_rng(SEED);rng.shuffle(images);train,val,test=images[:700],images[700:800],images[800:]
fig,ax=plt.subplots(2,6,figsize=(12,4))
for a,img in zip(ax.ravel(),train[:12]):a.imshow(img[:,:,0],cmap="gray");a.axis("off")
plt.tight_layout();plt.show();print(train.shape,val.shape,test.shape)""")
encoder_code=co("""inp=layers.Input((64,64,1));x=layers.Conv2D(16,3,2,padding="same",activation="relu")(inp);x=layers.Conv2D(32,3,2,padding="same",activation="relu")(x);x=layers.Conv2D(64,3,2,padding="same",activation="relu")(x);x=layers.Flatten()(x);mean=layers.Dense(LATENT_DIM)(x);logvar=layers.Dense(LATENT_DIM)(x)
class Sampling(layers.Layer):
 def call(self,v):
  m,l=v;return m+tf.exp(.5*l)*tf.random.normal(tf.shape(m))
z=Sampling()([mean,logvar]);encoder=Model(inp,[mean,logvar,z]);encoder.summary()""")
vae_code=co("""zin=layers.Input((LATENT_DIM,));d=layers.Dense(8*8*64,activation="relu")(zin);d=layers.Reshape((8,8,64))(d)
for filters in (64,32,16):d=layers.Conv2DTranspose(filters,3,2,padding="same",activation="relu")(d)
decoder=Model(zin,layers.Conv2D(1,3,padding="same",activation="sigmoid")(d))
class VAE(Model):
 def train_step(self,data):
  x=data[0] if isinstance(data,tuple) else data
  with tf.GradientTape() as tape:
   m,l,z=encoder(x);r=decoder(z);rec=tf.reduce_mean(tf.reduce_sum(tf.keras.losses.binary_crossentropy(x,r),axis=(1,2)));kl=-.5*tf.reduce_mean(tf.reduce_sum(1+l-tf.square(m)-tf.exp(l),axis=1));loss=rec+kl
  g=tape.gradient(loss,self.trainable_weights);self.optimizer.apply_gradients(zip(g,self.trainable_weights));return {"loss":loss,"reconstruction":rec,"kl":kl}
vae=VAE();vae.encoder=encoder;vae.decoder=decoder;vae.compile(optimizer="adam")""")
train_code=co("""vae.fit(train,epochs=25,batch_size=32,verbose=0)
m,_,_=encoder.predict(test[:8],verbose=0);recon=decoder.predict(m,verbose=0)
fig,ax=plt.subplots(2,8,figsize=(15,4))
for i in range(8):ax[0,i].imshow(test[i,:,:,0],cmap="gray");ax[1,i].imshow(recon[i,:,:,0],cmap="gray");ax[0,i].axis("off");ax[1,i].axis("off")
plt.tight_layout();plt.show()""")
gen_code=co("""latent=np.random.normal(size=(12,LATENT_DIM)).astype("float32");probabilities=decoder.predict(latent,verbose=0);generated=(probabilities>.5).astype("uint8")
fig,ax=plt.subplots(3,4,figsize=(8,8))
for i,a in enumerate(ax.ravel()):a.imshow(generated[i,:,:,0],cmap="gray");a.set_title(f"Design {chr(65+i)}");a.axis("off")
plt.tight_layout();plt.show()""")
screen_code=co("""def valid_geometry(mask):
 labels,n=ndimage.label(mask.astype(bool))
 if n==0:return False,"no material"
 mount=[]
 for cx,cy in MOUNTS:
  ring=((X-cx)**2+(Y-cy)**2>=25)&((X-cx)**2+(Y-cy)**2<=81);vals=labels[ring&(mask>0)]
  if len(vals)<18:return False,"mount missing"
  mount.append(np.bincount(vals).argmax())
 if mount[0]!=mount[1]:return False,"mounts disconnected"
 return True,"passes simplified checks"
for i,g in enumerate(generated):print(chr(65+i),valid_geometry(g[:,:,0]))""")
rank_code=co("""base=int(baseline.sum());rows=[]
for i,g in enumerate(generated):
 mask=g[:,:,0];valid,reason=valid_geometry(mask);area=int(mask.sum());rows.append(dict(Design=chr(65+i),Material_area=area,Relative_mass=100*area/base,Valid=valid,Reason=reason))
results=pd.DataFrame(rows);display(results)
valid=results[results.Valid].sort_values("Material_area")
if len(valid):
 best=valid.iloc[0];print(f"Selected Design {best.Design}: {100-best.Relative_mass:.1f}% less material by pixel proxy.")
print("Next: CAD reconstruction, loads, FEA, fatigue/buckling/manufacturing review, prototype, and test.")""")
body={"brief":[setup],"pixels":[pixels],"dataset":[dataset],"encoder":[encoder_code],"latent":[vae_code],"decoder":[train_code],"generate":[gen_code],"screen":[screen_code],"rank":[rank_code]}
for i,s in enumerate(bridge.STEPS,1):cells.extend(lesson(s,i,body[s["id"]]))
cells.append(md("""---
# Final engineering conclusion

The VAE samples a continuous latent space to create bracket candidates. Fixed-mount and connectivity checks come before material ranking. Every surviving silhouette still requires proper mechanical analysis and verification."""))
nb={"cells":cells,"metadata":{"colab":{"name":"Generative_Bracket_Design_VAE.ipynb","toc_visible":True,"provenance":[]},"kernelspec":{"display_name":"Python 3","name":"python3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":0}
out=BASE/"Generative_Bracket_Design_VAE.ipynb";out.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+"\n",encoding="utf-8");print("Wrote",out,"with",len(cells),"cells")
