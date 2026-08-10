import numpy as np
import plotly.graph_objects as go
import streamlit as st
import bridge,story,illustration_gallery
st.set_page_config(page_title="Retaining Wall Type Recommender",page_icon="🧱",layout="wide")
st.markdown("""<style>.stApp{background:#0e1117;color:#e6edf3}.block-container{max-width:1200px}.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}.civil{color:#ffb74d}.ai{color:#4fc3f7}</style>""",unsafe_allow_html=True)
with st.sidebar:
 st.header("Site conditions");height=st.slider("Wall height (m)",2.0,12.0,6.0,.5);soil=st.selectbox("Soil type",["Clay","Sand","Gravel","Mixed"]);water=st.selectbox("Groundwater",["Low","Medium","High"],1);width=st.slider("Available width (m)",1.0,10.0,6.0,.5);budget=st.selectbox("Budget",["Low","Medium","High"],1);alpha=st.slider("Technical-suitability weight",.5,.95,.75,.05)
df=story.recommend(height,soil,water,width,budget,alpha);stage=st.query_params.get("stage","start")
def header(s):
 p=bridge.PHASES[s["phase"]];st.markdown(f"<div class='hero'><small>PHASE {s['phase']+1} OF {len(bridge.PHASES)} · {p[0]}</small><h1>🧱 {s['civil']}</h1><h3><span class='civil'>{s['civil']}</span> → <span class='ai'>{s['ai']}</span></h3></div>",unsafe_allow_html=True);a,b,c=st.columns(3);a.markdown("#### 1 · In civil engineering");a.write(s["site"]);b.markdown("#### 2 · Engineering challenge");b.write(s["challenge"]);c.markdown("#### 3 · Where AI comes in");c.write(s["ai_link"]);st.markdown(f"#### 4 · Technical illustration — `{s['tech']}`")
if stage=="start":
 st.title("🧱 AI-Based Retaining Wall Type Recommender");st.warning("Educational concept-screening simulation only. It is not a retaining-wall design, safety approval, or substitute for geotechnical and structural checks.");a,b=st.columns([1.1,.9]);a.plotly_chart(story.ranking_chart(df),use_container_width=True)
 with b:
  st.metric("Recommended concept",df.iloc[0].Wall);st.metric("Suitability",f"{df.iloc[0].Suitability:.1%}");st.metric("Illustrative cost",f"₹{df.iloc[0].Estimated_cost_lakh:.1f} lakh");st.dataframe(df.style.format({"Suitability":"{:.1%}","Estimated_cost_lakh":"₹{:.1f}","Combined_score":"{:.3f}"}),hide_index=True,use_container_width=True)
 st.subheader("Learning journey");[st.markdown(f"**{i}. [{s['civil']}](?stage={s['id']})** — {s['ai']}") for i,s in enumerate(bridge.STEPS,1)];illustration_gallery.render_catalog()
else:
 s=bridge.BY_ID.get(stage,bridge.STEPS[0]);header(s);illustration_gallery.render_stage_gallery(s["id"]);st.plotly_chart(story.ranking_chart(df),use_container_width=True)
 if stage in ("inputs","cost","review"):st.dataframe(df.style.format({"Suitability":"{:.1%}","Estimated_cost_lakh":"₹{:.1f}","Combined_score":"{:.3f}"}),hide_index=True,use_container_width=True)
 elif stage in ("labels","data","prepare"):
  fig=go.Figure(go.Scatter(x=np.arange(2,13),y=[story.recommend(h,soil,water,width,budget,alpha).iloc[0].Suitability for h in np.arange(2,13)],mode="lines+markers",line=dict(color=story.CYAN,width=3)));fig.update_layout(height=380,paper_bgcolor=story.BG,plot_bgcolor=story.BG,font_color="white",xaxis_title="Wall height (m)",yaxis_title="Top suitability");st.plotly_chart(fig,use_container_width=True)
 st.markdown("#### 5 · In the notebook");st.write(s["notebook"]);st.success(s["takeaway"]);i=bridge.ORDER.index(s["id"]);cols=st.columns(3)
 if i:cols[0].markdown(f"[◀ {bridge.STEPS[i-1]['civil']}](?stage={bridge.ORDER[i-1]})")
 cols[1].markdown("[Overview](?stage=start)")
 if i<len(bridge.STEPS)-1:cols[2].markdown(f"[{bridge.STEPS[i+1]['civil']} ▶](?stage={bridge.ORDER[i+1]})")
