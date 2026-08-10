import numpy as np
import plotly.graph_objects as go
import streamlit as st
import bridge,story,illustration_gallery
st.set_page_config(page_title="Rainwater Harvesting Recommender",page_icon="💧",layout="wide")
st.markdown("""<style>.stApp{background:#0e1117;color:#e6edf3}.block-container{max-width:1200px}.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}.civil{color:#ffb74d}.ai{color:#4fc3f7}</style>""",unsafe_allow_html=True)
with st.sidebar:
 st.header("Site and water inputs");area=st.slider("Roof area (m²)",40,600,180);rain=st.slider("Annual rainfall (mm)",300,2200,900,50);demand=st.slider("Daily demand (L)",100,2500,650,50);runoff=st.slider("Runoff coefficient",.50,.95,.85,.01);cost=st.slider("Tank cost (₹/L)",2,15,6);space=st.slider("Maximum tank capacity (L)",2000,30000,12000,1000)
df=story.evaluate(area,rain,demand,runoff,cost,space);best=df.loc[df.Score.idxmax()];system=story.system_type(best.Capacity_L,space,rain,best.Overflow_L);stage=st.query_params.get("stage","start")
def header(s):
 p=bridge.PHASES[s["phase"]];st.markdown(f"<div class='hero'><small>PHASE {s['phase']+1} OF {len(bridge.PHASES)} · {p[0]}</small><h1>💧 {s['civil']}</h1><h3><span class='civil'>{s['civil']}</span> → <span class='ai'>{s['ai']}</span></h3></div>",unsafe_allow_html=True);a,b,c=st.columns(3);a.markdown("#### 1 · In civil engineering");a.write(s["site"]);b.markdown("#### 2 · Engineering challenge");b.write(s["challenge"]);c.markdown("#### 3 · Where AI comes in");c.write(s["ai_link"]);st.markdown(f"#### 4 · Technical illustration — `{s['tech']}`")
if stage=="start":
 st.title("💧 AI-Based Rainwater Harvesting System Recommender");st.warning("Educational simulation only. Use local rainfall records, water-quality requirements, codes, site investigation, and professional design for real projects.");a,b=st.columns([1.1,.9]);a.plotly_chart(story.chart(df),use_container_width=True)
 with b:st.metric("Recommended system",system);st.metric("Tank capacity",f"{best.Capacity_L:,.0f} L");st.metric("Expected demand supplied",f"{best.Demand_met:.1%}");st.metric("Illustrative tank cost",f"₹{best.Cost_INR:,.0f}")
 st.dataframe(df.style.format({"Capacity_L":"{:,.0f}","Supplied_L":"{:,.0f}","Demand_met":"{:.1%}","Overflow_L":"{:,.0f}","Shortage_L":"{:,.0f}","Cost_INR":"₹{:,.0f}","Score":"{:.3f}"}),hide_index=True,use_container_width=True);st.subheader("Learning journey");[st.markdown(f"**{i}. [{s['civil']}](?stage={s['id']})** — {s['ai']}") for i,s in enumerate(bridge.STEPS,1)];illustration_gallery.render_catalog()
else:
 s=bridge.BY_ID.get(stage,bridge.STEPS[0]);header(s);illustration_gallery.render_stage_gallery(s["id"]);st.plotly_chart(story.chart(df),use_container_width=True)
 if stage in ("inputs","balance","optimize","system"):st.dataframe(df.style.format({"Capacity_L":"{:,.0f}","Demand_met":"{:.1%}","Overflow_L":"{:,.0f}","Cost_INR":"₹{:,.0f}","Score":"{:.3f}"}),hide_index=True,use_container_width=True)
 st.markdown("#### 5 · In the notebook");st.write(s["notebook"]);st.success(s["takeaway"]);i=bridge.ORDER.index(s["id"]);cols=st.columns(3)
 if i:cols[0].markdown(f"[◀ {bridge.STEPS[i-1]['civil']}](?stage={bridge.ORDER[i-1]})")
 cols[1].markdown("[Overview](?stage=start)")
 if i<len(bridge.STEPS)-1:cols[2].markdown(f"[{bridge.STEPS[i+1]['civil']} ▶](?stage={bridge.ORDER[i+1]})")
