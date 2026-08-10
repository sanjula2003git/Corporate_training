import numpy as np
import plotly.graph_objects as go
import streamlit as st
import bridge,story,illustration_gallery
st.set_page_config(page_title="Power-Line Fault Location 1D CNN",page_icon="⚡",layout="wide")
st.markdown("""<style>.stApp{background:#0e1117;color:#e6edf3}.block-container{max-width:1200px}.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}.civil{color:#ffb74d}.ai{color:#4fc3f7}</style>""",unsafe_allow_html=True)
with st.sidebar:
 st.header("Simulated fault");distance=st.slider("Fault distance from Substation A (km)",.2,19.8,12.5,.1);resistance=st.slider("Fault resistance (relative)",.0,1.0,.3,.05);noise=st.slider("Measurement noise",.0,.12,.03,.01)
section=min(3,int(distance//5));regions=["0–5 km","5–10 km","10–15 km","15–20 km"];centres=np.array([2.5,7.5,12.5,17.5]);scores=np.exp(-((centres-distance)/3.4)**2)+.03;scores/=scores.sum();stage=st.query_params.get("stage","start")
def header(s):
 p=bridge.PHASES[s["phase"]];st.markdown(f"<div class='hero'><small>PHASE {s['phase']+1} OF {len(bridge.PHASES)} · {p[0]}</small><h1>⚡ {s['civil']}</h1><h3><span class='civil'>{s['civil']}</span> → <span class='ai'>{s['ai']}</span></h3></div>",unsafe_allow_html=True);a,b,c=st.columns(3);a.markdown("#### 1 · On the power line");a.write(s["site"]);b.markdown("#### 2 · Engineering challenge");b.write(s["challenge"]);c.markdown("#### 3 · Where AI comes in");c.write(s["ai_link"]);st.markdown(f"#### 4 · Technical illustration — `{s['tech']}`")
if stage=="start":
 st.title("⚡ Power-Line Fault Section Identification Using Voltage–Current Waveforms and a 1D CNN");st.warning("Educational synthetic locator only. It is not protection equipment, a trip command, or a field-validated fault locator.");st.plotly_chart(story.line_map(distance),use_container_width=True);st.plotly_chart(story.waveform_fig(distance,resistance),use_container_width=True);st.success(f"Predicted inspection region: SECTION {section+1} · {regions[section]}")
 st.subheader("Learning journey")
 for i,s in enumerate(bridge.STEPS,1):st.markdown(f"**{i}. [{s['civil']}](?stage={s['id']})** — {s['ai']}")
 illustration_gallery.render_catalog()
else:
 s=bridge.BY_ID.get(stage,bridge.STEPS[0]);header(s);illustration_gallery.render_stage_gallery(s["id"])
 if stage in ("problem","sections","prediction"):
  st.plotly_chart(story.line_map(distance),use_container_width=True)
  if stage=="prediction":
   a,b=st.columns(2);a.metric("Predicted section",f"SECTION {section+1}");a.metric("Region",regions[section]);a.metric("Confidence",f"{scores[section]:.1%}");b.bar_chart({"Probability":scores},x_label="Section index")
 elif stage in ("physics","generate","prepare"):
  st.plotly_chart(story.waveform_fig(distance,resistance),use_container_width=True);st.code("CNN input shape: (500 time samples, 2 channels)\nChannel 1: voltage · Channel 2: current")
 elif stage=="cnn":
  st.code("500×2 → Conv1D(32) → MaxPool → Conv1D(64) → GlobalAveragePooling → Dense → Softmax(4)");st.plotly_chart(story.waveform_fig(distance,resistance),use_container_width=True)
 elif stage=="training":
  e=np.arange(1,31);fig=go.Figure();fig.add_scatter(x=e,y=.18+1.3*np.exp(-e/7),name="train loss");fig.add_scatter(x=e,y=.24+1.2*np.exp(-e/6),name="validation loss");fig.update_layout(height=400,paper_bgcolor=story.BG,plot_bgcolor=story.BG,font_color="white",xaxis_title="Epoch",yaxis_title="Loss");st.plotly_chart(fig,use_container_width=True)
 else:
  cm=np.array([[46,4,0,0],[3,44,3,0],[0,4,43,3],[0,0,3,47]]);fig=go.Figure(go.Heatmap(z=cm,x=["S1","S2","S3","S4"],y=["S1","S2","S3","S4"],text=cm,texttemplate="%{text}",colorscale="Blues"));fig.update_layout(height=430,paper_bgcolor=story.BG,font_color="white",xaxis_title="Predicted",yaxis_title="Actual");st.plotly_chart(fig,use_container_width=True);st.info("Most simulated errors are between neighbouring sections—the pattern to inspect, not hide inside overall accuracy.")
 st.markdown("#### 5 · In the notebook");st.write(s["notebook"]);st.success(s["takeaway"]);i=bridge.ORDER.index(s["id"]);cols=st.columns(3)
 if i:cols[0].markdown(f"[◀ {bridge.STEPS[i-1]['civil']}](?stage={bridge.ORDER[i-1]})")
 cols[1].markdown("[Overview](?stage=start)")
 if i<len(bridge.STEPS)-1:cols[2].markdown(f"[{bridge.STEPS[i+1]['civil']} ▶](?stage={bridge.ORDER[i+1]})")
