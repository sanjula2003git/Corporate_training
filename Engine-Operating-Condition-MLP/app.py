import numpy as np
import plotly.graph_objects as go
import streamlit as st
import bridge,story,illustration_gallery
st.set_page_config(page_title="Engine Condition MLP",page_icon="🚗",layout="wide")
st.markdown("""<style>.stApp{background:#0e1117;color:#e6edf3}.block-container{max-width:1200px}.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}.civil{color:#ffb74d}.ai{color:#4fc3f7}</style>""",unsafe_allow_html=True)
with st.sidebar:
 st.header("Engine sensor snapshot");rpm=st.slider("RPM",600,4200,2400,50);load=st.slider("Engine load (%)",0,100,78);coolant=st.slider("Coolant temperature (°C)",50,125,96);intake=st.slider("Intake temperature (°C)",5,70,42);fuel=st.slider("Fuel flow (L/hr)",1.,14.,8.4,.1);pressure=st.slider("Manifold pressure (bar)",.5,2.,1.3,.05);exhaust=st.slider("Exhaust temperature (°C)",180,750,520)
classes=["NORMAL","HIGH LOAD","OVERHEATING","INEFFICIENT","ABNORMAL"];probs=story.scores(rpm,load,coolant,intake,fuel,pressure,exhaust);pred=int(np.argmax(probs));stage=st.query_params.get("stage","start")
def header(s):
 p=bridge.PHASES[s["phase"]];st.markdown(f"<div class='hero'><small>PHASE {s['phase']+1} OF {len(bridge.PHASES)} · {p[0]}</small><h1>🚗 {s['civil']}</h1><h3><span class='civil'>{s['civil']}</span> → <span class='ai'>{s['ai']}</span></h3></div>",unsafe_allow_html=True);a,b,c=st.columns(3);a.markdown("#### 1 · At the engine");a.write(s["site"]);b.markdown("#### 2 · Engineering challenge");b.write(s["challenge"]);c.markdown("#### 3 · Where AI comes in");c.write(s["ai_link"]);st.markdown(f"#### 4 · Technical illustration — `{s['tech']}`")
vals=[rpm,load,coolant,intake,fuel,pressure,exhaust]
if stage=="start":
 st.title("🚗 AI That Identifies Engine Operating Condition From Sensor Data");st.warning("Recommendations are simulated educational responses, not machinery control instructions.");a,b=st.columns(2);a.plotly_chart(story.gauges(vals),use_container_width=True)
 with b:st.plotly_chart(story.network(),use_container_width=True);st.metric("Predicted condition",classes[pred]);st.metric("Confidence",f"{probs[pred]:.1%}")
 st.subheader("Learning journey")
 for i,s in enumerate(bridge.STEPS,1):st.markdown(f"**{i}. [{s['civil']}](?stage={s['id']})** — {s['ai']}")
 illustration_gallery.render_catalog()
else:
 s=bridge.BY_ID.get(stage,bridge.STEPS[0]);header(s);illustration_gallery.render_stage_gallery(s["id"])
 if stage in ("problem","inputs","data","prepare"):st.plotly_chart(story.gauges(vals),use_container_width=True)
 elif stage in ("mlp","training"):st.plotly_chart(story.network(),use_container_width=True);st.code("7 inputs → Dense 32 → Dense 16 → Softmax 5")
 elif stage=="prediction":
  a,b=st.columns(2);a.plotly_chart(story.gauges(vals),use_container_width=True)
  with b:st.metric("Condition",classes[pred]);st.metric("Confidence",f"{probs[pred]:.1%}");st.bar_chart({"Probability":probs},x_label="Class index");st.info({0:"Continue simulated operation",1:"Simulated response: reduce load",2:"Simulated response: reduce load / inspect cooling",3:"Simulated response: inspect fuel-air condition",4:"Simulated response: schedule inspection"}[pred])
 else:
  cm=np.array([[47,2,0,0,1],[2,44,1,2,1],[0,2,45,1,2],[1,3,1,42,3],[1,1,2,3,43]]);fig=go.Figure(go.Heatmap(z=cm,x=classes,y=classes,text=cm,texttemplate="%{text}",colorscale="Blues"));fig.update_layout(height=470,paper_bgcolor=story.BG,font_color="white",xaxis_title="Predicted",yaxis_title="Actual");st.plotly_chart(fig,use_container_width=True)
 st.markdown("#### 5 · In the notebook");st.write(s["notebook"]);st.success(s["takeaway"]);i=bridge.ORDER.index(s["id"]);cols=st.columns(3)
 if i:cols[0].markdown(f"[◀ {bridge.STEPS[i-1]['civil']}](?stage={bridge.ORDER[i-1]})")
 cols[1].markdown("[Overview](?stage=start)")
 if i<len(bridge.STEPS)-1:cols[2].markdown(f"[{bridge.STEPS[i+1]['civil']} ▶](?stage={bridge.ORDER[i+1]})")
