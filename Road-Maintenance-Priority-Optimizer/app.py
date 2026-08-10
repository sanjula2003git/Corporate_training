import numpy as np
import plotly.graph_objects as go
import streamlit as st
import bridge,story,illustration_gallery
st.set_page_config(page_title="Road Maintenance Priority Optimizer",page_icon="🛣️",layout="wide")
st.markdown("""<style>.stApp{background:#0e1117;color:#e6edf3}.block-container{max-width:1200px}.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}.civil{color:#ffb74d}.ai{color:#4fc3f7}</style>""",unsafe_allow_html=True)
with st.sidebar:st.header("Maintenance programme");budget=st.slider("Available budget (₹ lakh)",15,100,50);nroads=st.slider("Candidate roads",8,20,12)
df=story.roads(nroads);selected,total_benefit=story.knapsack(df,budget);used=int(df.iloc[selected].Cost_lakh.sum());stage=st.query_params.get("stage","start")
def header(s):
 p=bridge.PHASES[s["phase"]];st.markdown(f"<div class='hero'><small>PHASE {s['phase']+1} OF {len(bridge.PHASES)} · {p[0]}</small><h1>🛣️ {s['civil']}</h1><h3><span class='civil'>{s['civil']}</span> → <span class='ai'>{s['ai']}</span></h3></div>",unsafe_allow_html=True);a,b,c=st.columns(3);a.markdown("#### 1 · In road maintenance");a.write(s["site"]);b.markdown("#### 2 · Engineering challenge");b.write(s["challenge"]);c.markdown("#### 3 · Where AI comes in");c.write(s["ai_link"]);st.markdown(f"#### 4 · Technical illustration — `{s['tech']}`")
if stage=="start":
 st.title("🛣️ AI-Based Road Maintenance Priority Optimizer");st.warning("Educational budget-planning simulation. Final programmes require accountable engineering, finance, safety, equity, and statutory review.");a,b=st.columns([1.1,.9]);a.plotly_chart(story.scatter(df,selected),use_container_width=True)
 with b:st.metric("Budget",f"₹{budget} lakh");st.metric("Budget used",f"₹{used} lakh");st.metric("Selected roads",len(selected));st.metric("Estimated total benefit",f"{total_benefit:.1f}");st.write("Repair programme:");[st.write(f"{i}. {df.iloc[j].Road} — ₹{df.iloc[j].Cost_lakh}L") for i,j in enumerate(selected,1)]
 st.subheader("Learning journey");[st.markdown(f"**{i}. [{s['civil']}](?stage={s['id']})** — {s['ai']}") for i,s in enumerate(bridge.STEPS,1)];illustration_gallery.render_catalog()
else:
 s=bridge.BY_ID.get(stage,bridge.STEPS[0]);header(s);illustration_gallery.render_stage_gallery(s["id"])
 if stage in ("problem","inputs","benefit","ranking","budget"):st.plotly_chart(story.scatter(df,selected),use_container_width=True);st.dataframe(df.assign(Decision=["REPAIR" if i in selected else "DEFER" for i in range(len(df))]),hide_index=True,use_container_width=True)
 elif stage in ("data","prepare","rank_audit"):
  fig=go.Figure(go.Bar(x=df.Road,y=df.Benefit,marker_color=[story.GREEN if i in selected else story.AMBER for i in range(len(df))]));fig.update_layout(height=430,paper_bgcolor=story.BG,plot_bgcolor=story.BG,font_color="white",xaxis_title="Road",yaxis_title="Priority benefit");st.plotly_chart(fig,use_container_width=True)
 else:
  budgets=np.arange(10,101,5);vals=[story.knapsack(df,int(b))[1] for b in budgets];fig=go.Figure(go.Scatter(x=budgets,y=vals,mode="lines+markers",line=dict(color=story.GREEN,width=3)));fig.update_layout(height=430,paper_bgcolor=story.BG,plot_bgcolor=story.BG,font_color="white",xaxis_title="Budget (₹ lakh)",yaxis_title="Maximum programme benefit");st.plotly_chart(fig,use_container_width=True)
 st.markdown("#### 5 · In the notebook");st.write(s["notebook"]);st.success(s["takeaway"]);i=bridge.ORDER.index(s["id"]);cols=st.columns(3)
 if i:cols[0].markdown(f"[◀ {bridge.STEPS[i-1]['civil']}](?stage={bridge.ORDER[i-1]})")
 cols[1].markdown("[Overview](?stage=start)")
 if i<len(bridge.STEPS)-1:cols[2].markdown(f"[{bridge.STEPS[i+1]['civil']} ▶](?stage={bridge.ORDER[i+1]})")

