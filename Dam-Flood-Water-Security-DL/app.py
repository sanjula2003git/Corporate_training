import numpy as np
import plotly.graph_objects as go
import streamlit as st
import bridge,story,illustration_gallery
st.set_page_config(page_title="Dam Flood and Water Security AI",page_icon="🌊",layout="wide")
st.markdown("""<style>.stApp{background:#0e1117;color:#e6edf3}.block-container{max-width:1200px}.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}.civil{color:#ffb74d}.ai{color:#4fc3f7}</style>""",unsafe_allow_html=True)
with st.sidebar:
 st.header("Pre-storm conditions");level=st.slider("Reservoir level (%)",50,99,88);rain=st.slider("Forecast rainfall (mm)",0,220,120);inflow=st.slider("Upstream inflow (m³/s)",40,700,420);down_name=st.select_slider("Downstream river level",["Low","Moderate","High","Very high"],value="High");down=["Low","Moderate","High","Very high"].index(down_name);free=100-level;release=st.slider("Current release (m³/s)",0,450,150)
pred=story.forecast(level,rain,inflow,down,free,release);recommended=story.release_rule(pred,down)
no_path,no_spill,_=story.simulate(level,rain,inflow,down,release,0);ai_path,ai_spill,early=story.simulate(level,rain,inflow,down,release,recommended)
stage=st.query_params.get("stage","start")
def header(s):
 p=bridge.PHASES[s["phase"]];st.markdown(f"<div class='hero'><small>PHASE {s['phase']+1} OF {len(bridge.PHASES)} · {p[0]}</small><h1>🌊 {s['civil']}</h1><h3><span class='civil'>{s['civil']}</span> → <span class='ai'>{s['ai']}</span></h3></div>",unsafe_allow_html=True);a,b,c=st.columns(3);a.markdown("#### 1 · At the dam");a.write(s["site"]);b.markdown("#### 2 · Engineering challenge");b.write(s["challenge"]);c.markdown("#### 3 · Where AI comes in");c.write(s["ai_link"]);st.markdown(f"#### 4 · Technical illustration — `{s['tech']}`")
if stage=="start":
 st.title("🌊 The Dam That Chooses Between Flood Protection and Water Security");st.markdown("### Civil Engineering + Deep Learning · Six-hour MLP forecast")
 st.warning("Educational decision-support simulation only. It does not authorize or recommend operation of a real dam.")
 a,b=st.columns(2);a.plotly_chart(story.reservoir(pred,"Predicted after 6 h"),use_container_width=True)
 with b:
  st.metric("Predicted level",f"{pred:.1f}%");st.metric("Constrained pre-release",f"{recommended} m³/s");st.write(f"Downstream condition: **{down_name}**");st.plotly_chart(story.comparison(no_path,ai_path),use_container_width=True)
 st.subheader("Learning journey")
 for i,s in enumerate(bridge.STEPS,1):st.markdown(f"**{i}. [{s['civil']}](?stage={s['id']})** — {s['ai']}")
 illustration_gallery.render_catalog()
else:
 s=bridge.BY_ID.get(stage,bridge.STEPS[0]);header(s);illustration_gallery.render_stage_gallery(s["id"])
 if stage in ("dilemma","inputs","decision"):
  a,b=st.columns(2);a.plotly_chart(story.reservoir(pred,"Forecast"),use_container_width=True)
  with b:
   st.metric("Forecast level",f"{pred:.1f}%");st.metric("Proposed constrained release",f"{recommended} m³/s");st.write(f"Free storage now: **{free}%**");st.write(f"Downstream: **{down_name}**");st.info("Forecast band proposes a release; downstream condition caps it.")
 elif stage=="mlp":
  st.code("6 engineering inputs → Dense 64 → Dense 32 → Dense 16 → future reservoir level")
  xs=np.arange(1,36);fig=go.Figure();fig.add_scatter(x=xs,y=.45+5*np.exp(-xs/8),name="train MAE");fig.add_scatter(x=xs,y=.65+4.8*np.exp(-xs/7),name="validation MAE");fig.update_layout(height=400,paper_bgcolor=story.BG,plot_bgcolor=story.BG,font_color="white",xaxis_title="Epoch",yaxis_title="MAE (%)");st.plotly_chart(fig,use_container_width=True)
 elif stage=="compare":
  st.plotly_chart(story.comparison(no_path,ai_path),use_container_width=True)
  st.dataframe({"Metric":["Peak reservoir level","Emergency spill index","Early release volume","Retained level after storm"],"Without AI":[f"{no_path.max():.1f}%",f"{no_spill:.0f}","0 Mm³",f"{no_path[-1]:.1f}%"],"With AI":[f"{ai_path.max():.1f}%",f"{ai_spill:.0f}",f"{early:.2f} Mm³",f"{ai_path[-1]:.1f}%"]},hide_index=True,use_container_width=True)
 elif stage=="audit":
  actual=np.array([82,87,91,94,97,99]);preds=np.array([82.4,86.3,91.8,93.2,95.9,97.8]);fig=go.Figure();fig.add_scatter(x=actual,y=preds,mode="markers+text",text=["event "+str(i) for i in range(6)]);fig.add_scatter(x=[80,100],y=[80,100],mode="lines",name="perfect");fig.update_layout(height=420,paper_bgcolor=story.BG,plot_bgcolor=story.BG,font_color="white",xaxis_title="Actual (%)",yaxis_title="Predicted (%)");st.plotly_chart(fig,use_container_width=True)
 else:
  st.plotly_chart(story.comparison(no_path,ai_path),use_container_width=True)
 st.markdown("#### 5 · In the notebook");st.write(s["notebook"]);st.success(s["takeaway"]);i=bridge.ORDER.index(s["id"]);cols=st.columns(3)
 if i:cols[0].markdown(f"[◀ {bridge.STEPS[i-1]['civil']}](?stage={bridge.ORDER[i-1]})")
 cols[1].markdown("[Overview](?stage=start)")
 if i<len(bridge.STEPS)-1:cols[2].markdown(f"[{bridge.STEPS[i+1]['civil']} ▶](?stage={bridge.ORDER[i+1]})")
