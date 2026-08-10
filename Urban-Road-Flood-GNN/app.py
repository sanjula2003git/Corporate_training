import numpy as np
import plotly.graph_objects as go
import streamlit as st
import bridge,story,illustration_gallery
st.set_page_config(page_title="Urban Road Flood GNN",page_icon="🌧️",layout="wide")
st.markdown("""<style>.stApp{background:#0e1117;color:#e6edf3}.block-container{max-width:1200px}.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}.civil{color:#ffb74d}.ai{color:#4fc3f7}</style>""",unsafe_allow_html=True)
with st.sidebar:st.header("Virtual storm");rain=st.slider("Rainfall intensity (mm/hr)",0,150,85);drain=st.slider("Drainage performance",.4,1.4,1.,.1);show_flow=st.toggle("Show connected influence",True)
risk=story.risks(rain,drain);order=sorted(risk,key=risk.get,reverse=True);stage=st.query_params.get("stage","start")
def header(s):
 p=bridge.PHASES[s["phase"]];st.markdown(f"<div class='hero'><small>PHASE {s['phase']+1} OF {len(bridge.PHASES)} · {p[0]}</small><h1>🌧️ {s['civil']}</h1><h3><span class='civil'>{s['civil']}</span> → <span class='ai'>{s['ai']}</span></h3></div>",unsafe_allow_html=True);a,b,c=st.columns(3);a.markdown("#### 1 · On the road network");a.write(s["site"]);b.markdown("#### 2 · Engineering challenge");b.write(s["challenge"]);c.markdown("#### 3 · Where AI comes in");c.write(s["ai_link"]);st.markdown(f"#### 4 · Technical illustration — `{s['tech']}`")
if stage=="start":
 st.title("🌧️ Urban Road Flood-Risk Prediction Using Graph Neural Networks");st.warning("Educational synthetic drainage network only—not a traffic-control or emergency-routing system.");a,b=st.columns([1.2,.8]);a.plotly_chart(story.network(rain,drain),use_container_width=True)
 with b:st.metric("First road likely to flood",f"ROAD {order[0]}");st.metric("Flood probability",f"{risk[order[0]]:.1%}");st.write("Predicted order:");[st.write(f"{i}. Road {k} — {risk[k]:.0%}") for i,k in enumerate(order,1)]
 st.subheader("Learning journey");[st.markdown(f"**{i}. [{s['civil']}](?stage={s['id']})** — {s['ai']}") for i,s in enumerate(bridge.STEPS,1)];illustration_gallery.render_catalog()
else:
 s=bridge.BY_ID.get(stage,bridge.STEPS[0]);header(s);illustration_gallery.render_stage_gallery(s["id"])
 if stage in ("problem","graph","features","ranking"):st.plotly_chart(story.network(rain,drain),use_container_width=True)
 elif stage in ("adjacency","gcn"):
  st.code("Road features X + normalized adjacency Â\n\nH₁ = ReLU(Â X W₁)\nH₂ = ReLU(Â H₁ W₂)\nProbabilities = Softmax(H₂ Wout)");st.plotly_chart(story.network(rain,drain),use_container_width=True)
 elif stage in ("simulate","training"):
  x=np.arange(1,36);fig=go.Figure();fig.add_scatter(x=x,y=.2+1.4*np.exp(-x/8),name="GCN train loss");fig.add_scatter(x=x,y=.28+1.3*np.exp(-x/7),name="validation loss");fig.update_layout(height=400,paper_bgcolor=story.BG,plot_bgcolor=story.BG,font_color="white",xaxis_title="Epoch",yaxis_title="Loss");st.plotly_chart(fig,use_container_width=True)
 else:
  cm=np.array([[91,7,2],[8,78,14],[2,12,86]]);fig=go.Figure(go.Heatmap(z=cm,x=["Low","Medium","High"],y=["Low","Medium","High"],text=cm,texttemplate="%{text}",colorscale="Blues"));fig.update_layout(height=440,paper_bgcolor=story.BG,font_color="white",xaxis_title="Predicted",yaxis_title="Actual");st.plotly_chart(fig,use_container_width=True);st.info("Audit question: does the GNN outperform the same model after all graph edges are removed?")
 st.markdown("#### 5 · In the notebook");st.write(s["notebook"]);st.success(s["takeaway"]);i=bridge.ORDER.index(s["id"]);cols=st.columns(3)
 if i:cols[0].markdown(f"[◀ {bridge.STEPS[i-1]['civil']}](?stage={bridge.ORDER[i-1]})")
 cols[1].markdown("[Overview](?stage=start)")
 if i<len(bridge.STEPS)-1:cols[2].markdown(f"[{bridge.STEPS[i+1]['civil']} ▶](?stage={bridge.ORDER[i+1]})")

