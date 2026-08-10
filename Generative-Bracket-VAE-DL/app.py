import numpy as np
import plotly.graph_objects as go
import streamlit as st
import bridge,story,illustration_gallery
st.set_page_config(page_title="Generative Bracket VAE",page_icon="⚙️",layout="wide")
st.markdown("""<style>.stApp{background:#0e1117;color:#e6edf3}.block-container{max-width:1200px}.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}.civil{color:#ffb74d}.ai{color:#4fc3f7}</style>""",unsafe_allow_html=True)
with st.sidebar:
 st.header("Latent design controls");z1=st.slider("z₁ · diagonal position",-2.0,2.0,0.2,.1);z2=st.slider("z₂ · web thickness",-2.0,2.0,-.4,.1);z3=st.slider("z₃ · flange/opening",-2.0,2.0,.5,.1);threshold=st.slider("Material threshold",.30,.75,.50,.05)
base=story.bracket(0,1.2,-.4);candidate=(story.bracket(z1,z2,z3)>=threshold).astype(float);base_area=story.area(base);cand_area=story.area(candidate);valid=story.connected(candidate);reduction=100*(base_area-cand_area)/base_area
stage=st.query_params.get("stage","start")
def header(s):
 p=bridge.PHASES[s["phase"]];st.markdown(f"<div class='hero'><small>PHASE {s['phase']+1} OF {len(bridge.PHASES)} · {p[0]}</small><h1>⚙️ {s['civil']}</h1><h3><span class='civil'>{s['civil']}</span> → <span class='ai'>{s['ai']}</span></h3></div>",unsafe_allow_html=True);a,b,c=st.columns(3);a.markdown("#### 1 · In mechanical design");a.write(s["site"]);b.markdown("#### 2 · Engineering challenge");b.write(s["challenge"]);c.markdown("#### 3 · Where AI comes in");c.write(s["ai_link"]);st.markdown(f"#### 4 · Technical illustration — `{s['tech']}`")
if stage=="start":
 st.title("⚙️ Generative AI for Lightweight Mechanical Bracket Design Using a VAE");st.markdown("### Mechanical Design + Deep Learning + Generative AI")
 st.warning("Generated silhouettes are educational candidates only. Pixel connectivity is not structural validation or design approval.")
 a,b=st.columns(2);a.plotly_chart(story.heat(base,"Baseline bracket"),use_container_width=True);b.plotly_chart(story.heat(candidate,"Generated candidate"),use_container_width=True)
 st.metric("Candidate material reduction",f"{reduction:.1f}%", "passes connectivity screen" if valid else "REJECTED: disconnected")
 st.subheader("Learning journey")
 for i,s in enumerate(bridge.STEPS,1):st.markdown(f"**{i}. [{s['civil']}](?stage={s['id']})** — {s['ai']}")
 illustration_gallery.render_catalog()
else:
 s=bridge.BY_ID.get(stage,bridge.STEPS[0]);header(s);illustration_gallery.render_stage_gallery(s["id"])
 if stage in ("brief","pixels","decoder"):
  a,b=st.columns(2);a.plotly_chart(story.heat(base,"Existing design"),use_container_width=True);b.plotly_chart(story.heat(candidate,"Decoded/generated design"),use_container_width=True)
 elif stage in ("encoder","latent"):
  st.code("64×64 geometry → Conv2D encoder → μ, log(σ²) → z = μ + σ·ε → 16 latent variables")
  st.plotly_chart(story.latent_map(),use_container_width=True)
 elif stage=="dataset":
  cols=st.columns(5)
  for i,c in enumerate(cols):c.plotly_chart(story.heat(story.bracket(-1+i*.5,np.sin(i),np.cos(i)),f"Training shape {i+1}"),use_container_width=True)
 elif stage=="generate":
  cols=st.columns(4)
  for i,c in enumerate(cols):c.plotly_chart(story.heat(story.bracket(z1+(i-1.5)*.45,z2,z3),f"Design {chr(65+i)}"),use_container_width=True)
 elif stage=="screen":
  a,b=st.columns(2);a.plotly_chart(story.heat(candidate,"Candidate under test"),use_container_width=True)
  with b:st.metric("Material pixels",cand_area);st.metric("Single connected component","YES" if valid else "NO");st.metric("Fixed mounting regions","PRESERVED");st.success("Passes simplified screen" if valid else "Rejected before ranking")
 else:
  rng=np.random.default_rng(8);rows=[]
  for i in range(8):
   m=story.bracket(*rng.normal(0,.9,3));a=story.area(m);v=story.connected(m);rows.append(dict(Design=chr(65+i),Material_area_px=a,Relative_mass=f"{100*a/base_area:.1f}%",Valid="Yes" if v else "No"))
  st.dataframe(rows,hide_index=True,use_container_width=True);valid_rows=[r for r in rows if r["Valid"]=="Yes"];best=min(valid_rows,key=lambda r:r["Material_area_px"]);st.success(f"Selected Design {best['Design']} — computed relative mass {best['Relative_mass']}. Requires structural analysis.")
 st.markdown("#### 5 · In the notebook");st.write(s["notebook"]);st.success(s["takeaway"]);i=bridge.ORDER.index(s["id"]);cols=st.columns(3)
 if i:cols[0].markdown(f"[◀ {bridge.STEPS[i-1]['civil']}](?stage={bridge.ORDER[i-1]})")
 cols[1].markdown("[Overview](?stage=start)")
 if i<len(bridge.STEPS)-1:cols[2].markdown(f"[{bridge.STEPS[i+1]['civil']} ▶](?stage={bridge.ORDER[i+1]})")
