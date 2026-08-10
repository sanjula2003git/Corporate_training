import numpy as np
import plotly.graph_objects as go
import streamlit as st
import bridge,story,illustration_gallery
st.set_page_config(page_title="Predictive Gearbox Vibration",page_icon="⚙️",layout="wide")
st.markdown("""<style>.stApp{background:#0e1117;color:#e6edf3}.block-container{max-width:1200px}.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}.civil{color:#ffb74d}.ai{color:#4fc3f7}</style>""",unsafe_allow_html=True)
with st.sidebar:
 st.header("Gearbox operating state");rpm=st.slider("RPM",600,3000,1800,50);torque=st.slider("Torque (Nm)",5,90,42);current=st.slider("Current vibration (mm/s)",.5,8.0,4.8,.1);temp=st.slider("Temperature (°C)",30,100,68);motor=st.slider("Motor current (A)",2.0,25.0,11.2,.1);wear=st.slider("Simulated wear severity",0.,1.,.55,.05);resonance=st.slider("Resonance proximity",0.,1.,.70,.05)
pred=story.future(rpm,torque,current,temp,wear,resonance);condition="NORMAL" if pred<5 else "WARNING" if pred<7 else "DANGEROUS";stage=st.query_params.get("stage","start")
def header(s):
 p=bridge.PHASES[s["phase"]];st.markdown(f"<div class='hero'><small>PHASE {s['phase']+1} OF {len(bridge.PHASES)} · {p[0]}</small><h1>⚙️ {s['civil']}</h1><h3><span class='civil'>{s['civil']}</span> → <span class='ai'>{s['ai']}</span></h3></div>",unsafe_allow_html=True);a,b,c=st.columns(3);a.markdown("#### 1 · At the gearbox");a.write(s["site"]);b.markdown("#### 2 · Engineering challenge");b.write(s["challenge"]);c.markdown("#### 3 · Where AI comes in");c.write(s["ai_link"]);st.markdown(f"#### 4 · Technical illustration — `{s['tech']}`")
if stage=="start":
 st.title("⚙️ Predictive Gearbox Vibration Control Using a 1D Convolutional Neural Network");st.warning("All operating responses are simulated. The 7 mm/s danger threshold is a project assumption, not a universal equipment limit.");a,b=st.columns(2);a.plotly_chart(story.wavefig(rpm,torque,wear,resonance),use_container_width=True)
 with b:st.metric("Current vibration",f"{current:.1f} mm/s");st.metric("Predicted after 30 s",f"{pred:.1f} mm/s");st.metric("Predicted condition",condition);st.plotly_chart(story.trajectories(current,pred)[0],use_container_width=True)
 st.subheader("Learning journey")
 for i,s in enumerate(bridge.STEPS,1):st.markdown(f"**{i}. [{s['civil']}](?stage={s['id']})** — {s['ai']}")
 illustration_gallery.render_catalog()
else:
 s=bridge.BY_ID.get(stage,bridge.STEPS[0]);header(s);illustration_gallery.render_stage_gallery(s["id"])
 if stage in ("waveform","data","prepare","inputs"):st.plotly_chart(story.wavefig(rpm,torque,wear,resonance),use_container_width=True);st.code("CNN input: 1000 vibration samples\nOperating input: RPM, torque, temperature, motor current")
 elif stage=="fusion":st.code("Waveform → Conv1D → Pool → Conv1D → GlobalAveragePooling ┐\nRPM + torque + temperature + current → Dense ─────────────┤ → Concatenate → Dense → future mm/s")
 elif stage in ("forecast","decision"):
  a,b=st.columns(2);a.plotly_chart(story.wavefig(rpm,torque,wear,resonance),use_container_width=True)
  with b:st.metric("Predicted vibration",f"{pred:.1f} mm/s");st.metric("Condition",condition);st.error({"NORMAL":"Continue simulated operation","WARNING":"Simulated response: reduce RPM slightly","DANGEROUS":"Simulated response: move away from speed / stop for inspection"}[condition])
 elif stage=="compare":
  fig,no,act=story.trajectories(current,pred);st.plotly_chart(fig,use_container_width=True);st.dataframe({"Metric":["Peak vibration","Time above 7 mm/s","Emergency shutdown","Early warning"],"Without AI":[f"{no.max():.1f} mm/s",f"{(no>7).sum()} s","Yes" if no.max()>8 else "No","0 s"],"With AI":[f"{act.max():.1f} mm/s",f"{(act>7).sum()} s","Avoided" if act.max()<8 else "Possible","22 s"]},hide_index=True,use_container_width=True)
 else:st.plotly_chart(story.trajectories(current,pred)[0],use_container_width=True)
 st.markdown("#### 5 · In the notebook");st.write(s["notebook"]);st.success(s["takeaway"]);i=bridge.ORDER.index(s["id"]);cols=st.columns(3)
 if i:cols[0].markdown(f"[◀ {bridge.STEPS[i-1]['civil']}](?stage={bridge.ORDER[i-1]})")
 cols[1].markdown("[Overview](?stage=start)")
 if i<len(bridge.STEPS)-1:cols[2].markdown(f"[{bridge.STEPS[i+1]['civil']} ▶](?stage={bridge.ORDER[i+1]})")
