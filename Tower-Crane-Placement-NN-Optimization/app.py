import numpy as np
import plotly.graph_objects as go
import streamlit as st
import bridge,story,illustration_gallery
st.set_page_config(page_title="Tower Crane Placement AI",page_icon="🏗️",layout="wide")
st.markdown("""<style>.stApp{background:#0e1117;color:#e6edf3}.block-container{max-width:1200px}.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}.civil{color:#ffb74d}.ai{color:#4fc3f7}</style>""",unsafe_allow_html=True)
with st.sidebar:st.header("Candidate crane");x=st.slider("Crane X (m)",0.,80.,37.,1.);y=st.slider("Crane Y (m)",0.,60.,29.,1.);show_reach=st.toggle("Show boom reach",True)
p=np.array([x,y]);cost,dist,viol,unreach=story.evaluate(p);stage=st.query_params.get("stage","start")
def header(s):
 q=bridge.PHASES[s["phase"]];st.markdown(f"<div class='hero'><small>PHASE {s['phase']+1} OF {len(bridge.PHASES)} · {q[0]}</small><h1>🏗️ {s['civil']}</h1><h3><span class='civil'>{s['civil']}</span> → <span class='ai'>{s['ai']}</span></h3></div>",unsafe_allow_html=True);a,b,c=st.columns(3);a.markdown("#### 1 · On the construction site");a.write(s["site"]);b.markdown("#### 2 · Engineering challenge");b.write(s["challenge"]);c.markdown("#### 3 · Where AI comes in");c.write(s["ai_link"]);st.markdown(f"#### 4 · Technical illustration — `{s['tech']}`")
if stage=="start":
 st.title("🏗️ AI-Based Tower Crane Placement Optimization Using a Neural Network Surrogate");st.warning("Educational site-layout optimization only. It is not a lift plan, crane selection, structural design, or safety approval.");a,b=st.columns([1.3,.7]);a.plotly_chart(story.site((x,y)),use_container_width=True)
 with b:st.metric("Weighted lifting distance",f"{(dist*story.FREQ).sum():,.0f} m-lifts/day");st.metric("Reachable lift points",f"{100*(3-unreach)/3:.0f}%");st.metric("Safety violations",viol);st.metric("Exact penalized cost",f"{cost:,.0f}")
 st.subheader("Learning journey");[st.markdown(f"**{i}. [{s['civil']}](?stage={s['id']})** — {s['ai']}") for i,s in enumerate(bridge.STEPS,1)];illustration_gallery.render_catalog()
else:
 s=bridge.BY_ID.get(stage,bridge.STEPS[0]);header(s);illustration_gallery.render_stage_gallery(s["id"])
 if stage in ("problem","demand","constraints","cost","verify"):st.plotly_chart(story.site((x,y)),use_container_width=True)
 elif stage in ("dataset","surrogate","audit"):
  gx=np.linspace(0,80,41);gy=np.linspace(0,60,31);z=np.array([[story.evaluate(np.array([a,b]))[0] for a in gx] for b in gy]);fig=go.Figure(go.Contour(x=gx,y=gy,z=np.log1p(z),colorscale="Viridis",colorbar_title="log cost"));fig.update_layout(height=480,paper_bgcolor=story.BG,plot_bgcolor=story.BG,font_color="white",xaxis_title="X",yaxis_title="Y");st.plotly_chart(fig,use_container_width=True)
 else:
  g=np.arange(40);best=3600*np.exp(-g/9)+1650+30*np.sin(g/2);fig=go.Figure(go.Scatter(x=g,y=best,mode="lines+markers",line=dict(color=story.GREEN,width=3)));fig.update_layout(height=420,paper_bgcolor=story.BG,plot_bgcolor=story.BG,font_color="white",xaxis_title="GA generation",yaxis_title="Best predicted cost");st.plotly_chart(fig,use_container_width=True)
 st.markdown("#### 5 · In the notebook");st.write(s["notebook"]);st.success(s["takeaway"]);i=bridge.ORDER.index(s["id"]);cols=st.columns(3)
 if i:cols[0].markdown(f"[◀ {bridge.STEPS[i-1]['civil']}](?stage={bridge.ORDER[i-1]})")
 cols[1].markdown("[Overview](?stage=start)")
 if i<len(bridge.STEPS)-1:cols[2].markdown(f"[{bridge.STEPS[i+1]['civil']} ▶](?stage={bridge.ORDER[i+1]})")

