from pathlib import Path
import json,sys,textwrap
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE));import bridge
APP="https://urban-road-flood-gnn.streamlit.app"
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

## Part 1 · On the road network
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

cells=[md(f"""# 🌧️ Urban Road Flood-Risk Prediction Using Graph Neural Networks

Predict Low, Medium, or High flood risk for every connected road section and rank which roads are likely to flood first.

> Educational synthetic city—not an emergency-routing system.

👉 **Open the interactive companion:** [{APP}]({APP}/?stage=start)"""),md(f"""## Complete workflow

Create road graph → assign five node features → simulate storms → normalize adjacency → train GCN → map risk → rank roads → compare with isolated-road MLP.

## Interactive learning journey

{chr(10).join(f"- [{s['civil']}]({APP}/?stage={s['id']}) — {s['ai']}" for s in bridge.STEPS)}"""),co("""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report,confusion_matrix,ConfusionMatrixDisplay
import tensorflow as tf
from tensorflow.keras import layers,Model
SEED=42;np.random.seed(SEED);tf.random.set_seed(SEED)
N_NODES,N_FEATURES,N_CLASSES=30,5,3
FEATURES=["rain_mm_hr","elevation_m","water_depth_cm","drainage_mm_hr","slope_pct"]""")]
problem=md("""The model returns a risk class and probability for every road node. Sorting High-risk probability produces the predicted flooding order.""")
graph=co("""rng=np.random.default_rng(SEED);G=nx.random_geometric_graph(N_NODES,.31,seed=SEED)
while not nx.is_connected(G):G=nx.random_geometric_graph(N_NODES,.34,seed=int(rng.integers(9999)))
A=nx.to_numpy_array(G,dtype="float32");pos=nx.get_node_attributes(G,"pos")
nx.draw(G,pos,node_size=180,node_color="skyblue",edge_color="gray",with_labels=True);plt.title("Virtual 30-road network");plt.show()
print("Road nodes:",G.number_of_nodes(),"Connections:",G.number_of_edges())""")
features=co("""elevation=rng.uniform(96,112,N_NODES);drainage=rng.uniform(18,70,N_NODES);slope=rng.uniform(.2,4,N_NODES)
example=pd.DataFrame(dict(Road=np.arange(N_NODES),Elevation_m=elevation,Drainage_mm_hr=drainage,Slope_pct=slope));example.head()""")
simulate=co("""def storm_snapshot(rain):
 depth=np.clip(.045*rain-.035*drainage+.12*(105-elevation)+rng.normal(0,.8,N_NODES),0,None)
 # Water influence travels preferentially toward lower connected roads.
 incoming=np.zeros(N_NODES)
 for i,j in G.edges:
  if elevation[i]>elevation[j]:incoming[j]+=.16*depth[i]
  else:incoming[i]+=.16*depth[j]
 future=depth+incoming+.018*np.maximum(0,rain-drainage)
 labels=np.digitize(future,[7,14])
 X=np.column_stack([np.full(N_NODES,rain),elevation,depth,drainage,slope]).astype("float32")
 return X,labels,future,incoming
Xs,ys=[],[]
for _ in range(650):
 X,y,_,_=storm_snapshot(rng.uniform(20,145));Xs.append(X);ys.append(y)
Xs=np.array(Xs);ys=np.array(ys);print(Xs.shape,ys.shape,"class counts",np.bincount(ys.ravel()))""")
adj=co("""A_self=A+np.eye(N_NODES,dtype="float32");degree=A_self.sum(1);D_inv=np.diag(1/np.sqrt(degree));A_norm=(D_inv@A_self@D_inv).astype("float32")
road=7;print("Road",road,"neighbors:",list(G.neighbors(road)));print("Self weight:",A_norm[road,road]);plt.imshow(A_norm,cmap="Blues");plt.colorbar();plt.title("Normalized adjacency Â");plt.show()""")
gcn=co("""class GraphConv(layers.Layer):
 def __init__(self,units,activation=None):super().__init__();self.units=units;self.activation=tf.keras.activations.get(activation)
 def build(self,input_shape):self.w=self.add_weight(shape=(input_shape[-1],self.units),initializer="glorot_uniform")
 def call(self,inputs):
  x,a=inputs;h=tf.matmul(x,self.w);out=tf.einsum("ij,bjk->bik",a,h);return self.activation(out) if self.activation else out
xin=layers.Input((N_NODES,N_FEATURES));ain=layers.Input((N_NODES,N_NODES));h=GraphConv(32,"relu")([xin,ain]);h=layers.Dropout(.12)(h);h=GraphConv(24,"relu")([h,ain]);out=layers.Dense(N_CLASSES,activation="softmax")(h);gcn_model=Model([xin,ain],out);gcn_model.compile(optimizer="adam",loss="sparse_categorical_crossentropy",metrics=["accuracy"]);gcn_model.summary()""")
training=co("""idx=np.arange(len(Xs));tr,tmp=train_test_split(idx,test_size=.30,random_state=SEED);va,te=train_test_split(tmp,test_size=.50,random_state=SEED)
scaler=StandardScaler().fit(Xs[tr].reshape(-1,N_FEATURES));scale=lambda x:scaler.transform(x.reshape(-1,N_FEATURES)).reshape(x.shape);Xtr,Xva,Xte=scale(Xs[tr]),scale(Xs[va]),scale(Xs[te]);Atr=np.repeat(A_norm[None],len(tr),0);Ava=np.repeat(A_norm[None],len(va),0);Ate=np.repeat(A_norm[None],len(te),0)
weights=np.array([1,1.4,1.8]);sample_weight=weights[ys[tr]];history=gcn_model.fit([Xtr,Atr],ys[tr],sample_weight=sample_weight,validation_data=([Xva,Ava],ys[va]),epochs=40,batch_size=24,verbose=0)
plt.plot(history.history["loss"],label="train");plt.plot(history.history["val_loss"],label="validation");plt.grid(alpha=.2);plt.legend();plt.show()""")
ranking=co("""X_new,y_true,future,incoming=storm_snapshot(85);probs=gcn_model.predict([scale(X_new[None]),A_norm[None]],verbose=0)[0];order=np.argsort(probs[:,2])[::-1]
print("AI FLOOD PREDICTION")
for rank,node in enumerate(order[:5],1):print(f"{rank}. Road {node:02d} — high-risk probability {probs[node,2]:.1%}")
top=order[0];print("\\nFirst road likely to flood: ROAD",top);print("Main reasons:",f"elevation {elevation[top]:.1f} m, drainage {drainage[top]:.1f} mm/hr, upstream contribution {incoming[top]:.1f} cm")
colors=probs[:,2];nx.draw(G,pos,node_color=colors,cmap="RdYlGn_r",vmin=0,vmax=1,with_labels=True,node_size=230);plt.title("Predicted high-flood-risk probability");plt.show()""")
audit=co("""pred=np.argmax(gcn_model.predict([Xte,Ate],verbose=0),axis=2);print(classification_report(ys[te].ravel(),pred.ravel(),target_names=["Low","Medium","High"]));ConfusionMatrixDisplay(confusion_matrix(ys[te].ravel(),pred.ravel()),display_labels=["Low","Medium","High"]).plot(cmap="Blues");plt.show()
# Edge-removal ablation: same trained model, isolated self-only graph.
isolated=np.repeat(np.eye(N_NODES,dtype="float32")[None],len(te),0);isolated_pred=np.argmax(gcn_model.predict([Xte,isolated],verbose=0),axis=2)
print("GCN high-risk recall:",((pred==2)&(ys[te]==2)).sum()/(ys[te]==2).sum());print("Edges removed high-risk recall:",((isolated_pred==2)&(ys[te]==2)).sum()/(ys[te]==2).sum())
print("Limitations: synthetic topology, simplified surface transfer, no inlet/pipe capacity model, no terrain raster, no blockage, no uncertainty ensemble, no traffic or emergency integration.")""")
body={"problem":[problem],"graph":[graph],"features":[features],"simulate":[simulate],"adjacency":[adj],"gcn":[gcn],"training":[training],"ranking":[ranking],"audit":[audit]}
for i,s in enumerate(bridge.STEPS,1):cells.extend(lesson(s,i,body[s["id"]]))
cells.append(md("""---
# Final engineering conclusion

The GCN predicts every road using its own five measurements and messages from connected neighbours. Flood-order ranking converts node probabilities into inspection priorities, while the edge-removal audit tests whether connectivity genuinely adds value."""))
nb={"cells":cells,"metadata":{"colab":{"name":"Urban_Road_Flood_Risk_GNN.ipynb","toc_visible":True,"provenance":[]},"kernelspec":{"display_name":"Python 3","name":"python3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":0}
out=BASE/"Urban_Road_Flood_Risk_GNN.ipynb";out.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+"\n",encoding="utf-8");print("Wrote",out,"with",len(cells),"cells")
