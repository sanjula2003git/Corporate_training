import numpy as np
import plotly.graph_objects as go
import streamlit as st
import bridge,story,illustration_gallery
st.set_page_config(page_title="Pump Cavitation Audio AI",page_icon="🔊",layout="wide")
st.markdown("""<style>.stApp{background:#0e1117;color:#e6edf3}.block-container{max-width:1200px}.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}.civil{color:#ffb74d}.ai{color:#4fc3f7}</style>""",unsafe_allow_html=True)
with st.sidebar:
 st.header("Simulated pump test")
 condition=st.select_slider("Condition",options=["Normal","Mild Cavitation","Severe Cavitation"],value="Severe Cavitation")
 rpm=st.slider("Pump RPM (metadata)",900,2400,1800,50); inlet=st.slider("Inlet pressure (bar, metadata)",.2,2.5,.6,.1)
 st.caption("RPM and inlet pressure explain the simulated test. Only the spectrogram enters the CNN.")
sev={"Normal":0.0,"Mild Cavitation":.45,"Severe Cavitation":1.0}[condition]
t,x,sr=story.synth_audio(sev,seed=int(rpm+inlet*100)); stage=st.query_params.get("stage","start")

def header(s):
 p=bridge.PHASES[s["phase"]]; st.markdown(f"<div class='hero'><small>PHASE {s['phase']+1} OF {len(bridge.PHASES)} · {p[0]}</small><h1>🔊 {s['civil']}</h1><h3><span class='civil'>{s['civil']}</span> → <span class='ai'>{s['ai']}</span></h3></div>",unsafe_allow_html=True)
 a,b,c=st.columns(3); a.markdown("#### 1 · At the pump");a.write(s["site"]);b.markdown("#### 2 · Engineering challenge");b.write(s["challenge"]);c.markdown("#### 3 · Where AI comes in");c.write(s["ai_link"]);st.markdown(f"#### 4 · Technical illustration — `{s['tech']}`")

if stage=="start":
 st.title("🔊 Detecting Centrifugal-Pump Cavitation Using Sound")
 st.markdown("### Mechanical Engineering + Signal Processing + Deep Learning")
 st.warning("All operating responses are simulated educational recommendations, not instructions for real industrial equipment.")
 a,b=st.columns(2); a.plotly_chart(story.pump_diagram(sev),use_container_width=True)
 with b:
  st.plotly_chart(story.spectrogram(x,sr),use_container_width=True); st.audio(story.wav_bytes(x,sr),format="audio/wav")
  st.info("Pump sound → waveform → spectrogram → 2D CNN → Normal / Mild / Severe")
 st.subheader("Learning journey")
 for i,s in enumerate(bridge.STEPS,1): st.markdown(f"**{i}. [{s['civil']}](?stage={s['id']})** — {s['ai']}")
 illustration_gallery.render_catalog()
else:
 s=bridge.BY_ID.get(stage,bridge.STEPS[0]);header(s);illustration_gallery.render_stage_gallery(s["id"])
 if stage=="cavitation": st.plotly_chart(story.pump_diagram(sev),use_container_width=True)
 elif stage in ("listen","waveform"):
  st.audio(story.wav_bytes(x,sr),format="audio/wav");st.plotly_chart(story.waveform(t,x),use_container_width=True)
 elif stage in ("spectrogram","cnn"):
  st.plotly_chart(story.spectrogram(x,sr),use_container_width=True)
  if stage=="cnn": st.code("Spectrogram → Conv2D → MaxPool → Conv2D → MaxPool → Flatten → Dense → Softmax")
 elif stage=="training":
  e=np.arange(1,31); fig=go.Figure();fig.add_scatter(x=e,y=.25+1.25*np.exp(-e/7),name="training loss");fig.add_scatter(x=e,y=.32+1.2*np.exp(-e/6)+.012*np.maximum(e-23,0),name="validation loss");fig.update_layout(height=400,paper_bgcolor=story.BG,plot_bgcolor=story.BG,font_color="white",xaxis_title="Epoch",yaxis_title="Cross-entropy loss");st.plotly_chart(fig,use_container_width=True)
 elif stage=="prediction":
  probs={"Normal":[.94,.05,.01],"Mild Cavitation":[.08,.86,.06],"Severe Cavitation":[.01,.05,.94]}[condition]
  a,b=st.columns(2);a.plotly_chart(story.spectrogram(x,sr),use_container_width=True)
  with b:
   st.metric("Pump condition",condition);st.metric("Confidence",f"{max(probs):.0%}")
   response={"Normal":"Continue simulated operation","Mild Cavitation":"Simulated response: reduce speed or inspect inlet condition","Severe Cavitation":"Simulated response: stop or reduce operation and inspect the pump system"}[condition]
   st.error(response if sev else response);st.bar_chart({"probability":probs},x_label="Class index")
 else:
  cm=np.array([[47,3,0],[4,43,3],[0,2,48]]);fig=go.Figure(go.Heatmap(z=cm,x=["Normal","Mild","Severe"],y=["Normal","Mild","Severe"],text=cm,texttemplate="%{text}",colorscale="Blues"));fig.update_layout(height=430,paper_bgcolor=story.BG,font_color="white",xaxis_title="Predicted",yaxis_title="Actual");st.plotly_chart(fig,use_container_width=True)
 st.markdown("#### 5 · In the notebook");st.write(s["notebook"]);st.success(s["takeaway"])
 i=bridge.ORDER.index(s["id"]);cols=st.columns(3)
 if i: cols[0].markdown(f"[◀ {bridge.STEPS[i-1]['civil']}](?stage={bridge.ORDER[i-1]})")
 cols[1].markdown("[Overview](?stage=start)")
 if i<len(bridge.STEPS)-1: cols[2].markdown(f"[{bridge.STEPS[i+1]['civil']} ▶](?stage={bridge.ORDER[i+1]})")
