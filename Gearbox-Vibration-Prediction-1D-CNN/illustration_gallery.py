"""Thirty-two dedicated technical scenes derived from the local teaching registry."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import bridge

BG="#0e1117"; CYAN="#4fc3f7"; AMBER="#ffb74d"; VIOLET="#ba68c8"; GREEN="#66bb6a"; RED="#ef5350"
ASPECTS=("Engineering system","Data and evidence","AI mechanism","Decision and audit")

def _scene_specs():
    n=len(bridge.STEPS); out=[]
    for i in range(32):
        step=bridge.STEPS[i%n]; aspect=ASPECTS[(i//n)%len(ASPECTS)]
        out.append(dict(number=i+1,stage=step["id"],title=f"{step['civil']} · {aspect}",aspect=aspect,step=step))
    return out

SCENES=_scene_specs()

def _layout(fig,height=360):
    fig.update_layout(height=height,paper_bgcolor=BG,plot_bgcolor=BG,font_color="white",margin=dict(l=35,r=15,t=45,b=35))
    return fig

def _engineering(scene):
    s=scene["step"]; labels=[s["civil"],"Engineering challenge",s["ai"],"System contribution"]
    fig=go.Figure(go.Sankey(node=dict(label=labels,color=[AMBER,RED,CYAN,GREEN],pad=24,thickness=22),link=dict(source=[0,1,2],target=[1,2,3],value=[1,1,1],color=["rgba(255,183,77,.35)","rgba(239,83,80,.35)","rgba(79,195,247,.35)"])))
    return _layout(fig)

def _data(scene):
    s=scene["step"]; x=np.linspace(0,1,80); seed=sum(map(ord,s["id"])); rng=np.random.default_rng(seed)
    raw=np.sin(2*np.pi*(2+seed%4)*x)*(.4+.1*(seed%3))+.18*rng.normal(size=len(x)); prepared=np.convolve(raw,np.ones(7)/7,mode="same")
    fig=go.Figure();fig.add_scatter(x=x,y=raw,name="Observed evidence",line=dict(color=AMBER));fig.add_scatter(x=x,y=prepared,name="Prepared model input",line=dict(color=CYAN,width=3));fig.update_xaxes(title="Normalized observation window");fig.update_yaxes(title="Relative value")
    return _layout(fig)

def _ai(scene):
    s=scene["step"]; names=["Inputs","Representation",s["ai"],"Output"]
    fig=go.Figure()
    for i,(name,count,color) in enumerate(zip(names,[5,7,5,3],[AMBER,CYAN,VIOLET,GREEN])):
        ys=np.linspace(1,9,count);fig.add_trace(go.Scatter(x=[i]*count,y=ys,mode="markers",marker=dict(size=18,color=color),name=name))
    fig.update_xaxes(visible=False,range=[-.4,3.4]);fig.update_yaxes(visible=False);fig.add_annotation(x=1.5,y=.25,text=s["tech"],showarrow=False,font_color="white")
    return _layout(fig)

def _decision(scene):
    s=scene["step"]; seed=sum(map(ord,s["id"])); vals=np.array([.62,.24,.10,.04]);vals=np.roll(vals,seed%4)
    fig=go.Figure(go.Bar(x=["Preferred","Alternative","Warning","Reject"],y=vals,marker_color=[GREEN,CYAN,AMBER,RED],text=[f"{v:.0%}" for v in vals],textposition="outside"));fig.update_yaxes(range=[0,1],title="Illustrative decision evidence");fig.add_annotation(x=1.5,y=.88,text=s["takeaway"],showarrow=False,bgcolor="#161b22",bordercolor=VIOLET,font_color="white")
    return _layout(fig)

def render_stage_gallery(stage_id):
    scenes=[s for s in SCENES if s["stage"]==stage_id]
    if not scenes:return
    st.markdown("### Dedicated illustration gallery")
    st.caption(f"{len(scenes)} distinct scenes on this page · 32 across the complete companion app")
    tabs=st.tabs([f"{s['number']:02} · {s['aspect']}" for s in scenes])
    for tab,scene in zip(tabs,scenes):
        with tab:
            st.markdown(f"#### Illustration {scene['number']:02} · {scene['title']}")
            if scene["aspect"]==ASPECTS[0]:fig=_engineering(scene)
            elif scene["aspect"]==ASPECTS[1]:fig=_data(scene)
            elif scene["aspect"]==ASPECTS[2]:fig=_ai(scene)
            else:fig=_decision(scene)
            st.plotly_chart(fig,use_container_width=True,key=f"scene-{scene['number']}-{stage_id}")
            st.info(scene["step"]["takeaway"])

def render_catalog():
    st.markdown("### All 32 technical illustrations")
    for s in SCENES:
        st.markdown(f"**{s['number']:02}. [{s['title']}](?stage={s['stage']})**")
