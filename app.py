"""Streamlit companion: AI That Predicts Which Metro Evacuation Route Will Flood."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import bridge
import story

st.set_page_config(page_title="Metro Evacuation Flood AI", page_icon="🚇", layout="wide")
st.markdown("""<style>
.stApp{background:#0e1117;color:#e6edf3}.block-container{max-width:1200px;padding-top:1.5rem}
.hero{padding:1.2rem 1.4rem;border:1px solid #30363d;border-radius:16px;background:#161b22}
.civil{color:#ffb74d}.ai{color:#4fc3f7}.tech{color:#ba68c8}
.note{padding:.8rem 1rem;border-left:4px solid #ffb74d;background:#1b2028;border-radius:6px}
</style>""", unsafe_allow_html=True)


def status(depth):
    return "SAFE" if depth < 10 else "WARNING" if depth <= 20 else "UNSAFE"


def simple_forecast(rain, entrance, tunnel, drainage, route):
    """Transparent surrogate for the trained notebook LSTM used by the live illustration."""
    inflow = .10*rain + .25*entrance + .30*tunnel
    removal = .35*drainage
    return max(0.0, route + 5 * max(-.5, (inflow-removal)/2.3))


def teaching_header(step):
    phase = bridge.PHASES[step["phase"]]
    st.markdown(f"<div class='hero'><small>PHASE {step['phase']+1} OF {len(bridge.PHASES)} · {phase[0]}</small>"
                f"<h1>🚇 {step['civil']}</h1><h3><span class='civil'>{step['civil']}</span> → "
                f"<span class='ai'>{step['ai']}</span></h3></div>", unsafe_allow_html=True)
    c1,c2,c3=st.columns(3)
    c1.markdown("#### 1 · On the metro"); c1.write(step["site"])
    c2.markdown("#### 2 · Engineering challenge"); c2.write(step["challenge"])
    c3.markdown("#### 3 · Where AI comes in"); c3.write(step["ai_link"])
    st.markdown(f"#### 4 · Technical illustration — `{step['tech']}`")


def controls():
    with st.sidebar:
        st.header("Live storm inputs")
        rain=st.slider("Rainfall intensity (mm/hr)",0,120,75)
        entrance=st.slider("Entrance water level (cm)",0,40,18)
        tunnel=st.slider("Tunnel water level (cm)",0,30,9)
        drainage=st.slider("Drainage flow (L/s)",0,30,12)
        st.caption("Route-specific current depth is set in the route comparison.")
    return rain,entrance,tunnel,drainage


rain, entrance, tunnel, drainage = controls()
stage = st.query_params.get("stage", "start")

if stage == "start":
    st.title("🚇 AI That Predicts Which Metro Evacuation Route Will Flood")
    st.markdown("### Civil Engineering + Deep Learning · LSTM five-minute forecasting")
    st.info("A route can look safe now and flood while passengers are using it. This project forecasts the water depth five minutes ahead and redirects passengers before that happens.")
    a,b=st.columns([1.1,.9])
    with a:
        st.plotly_chart(story.station_map(28,6), use_container_width=True)
    with b:
        st.markdown("#### The entire decision system")
        st.markdown("**Five inputs** → ten-minute sequence → **LSTM** → route depth at +5 minutes → project safety band → compare Route A and Route B → recommend exit")
        st.warning("Educational project assumption only: below 10 cm = SAFE, 10–20 cm = WARNING, above 20 cm = UNSAFE. These are not presented as universal evacuation standards.")
        st.success("Example: Route A 28 cm, Route B 6 cm → EVACUATE USING ROUTE B")
    st.markdown("### Learning journey")
    for i,s in enumerate(bridge.STEPS,1):
        st.markdown(f"**{i}. [{s['civil']}](?stage={s['id']})** — {s['ai']}")
else:
    step=bridge.BY_ID.get(stage,bridge.STEPS[0]); teaching_header(step)
    if stage in ("sequences","lstm"):
        st.plotly_chart(story.sequence_window(), use_container_width=True)
        if stage=="lstm":
            st.markdown("**Forget gate:** release obsolete storm history · **Input gate:** admit new evidence · **Output gate:** expose useful memory for the depth forecast")
    elif stage in ("routes","thresholds","forecast","station"):
        c1,c2=st.columns(2)
        with c1:
            a_now=st.slider("Route A current depth (cm)",0.0,25.0,4.0,.5)
            b_now=st.slider("Route B current depth (cm)",0.0,25.0,2.0,.5)
            pred_a=simple_forecast(rain,entrance,tunnel,drainage,a_now)
            pred_b=simple_forecast(rain*.72,entrance*.25,tunnel*.65,drainage*1.25,b_now)
            st.plotly_chart(story.station_map(pred_a,pred_b),use_container_width=True)
        with c2:
            st.plotly_chart(story.forecast_chart(a_now,b_now,pred_a,pred_b),use_container_width=True)
            if status(pred_a)=="UNSAFE" and status(pred_b)!="UNSAFE": rec="ROUTE B"
            elif status(pred_b)=="UNSAFE" and status(pred_a)!="UNSAFE": rec="ROUTE A"
            else: rec="ROUTE A" if pred_a<pred_b else "ROUTE B"
            st.metric("Route A after 5 min",f"{pred_a:.1f} cm",status(pred_a))
            st.metric("Route B after 5 min",f"{pred_b:.1f} cm",status(pred_b))
            st.success(f"AI RECOMMENDATION: EVACUATE USING {rec}")
    elif stage=="inputs":
        names=["Rainfall","Entrance","Tunnel","Drainage","Route depth"]
        vals=[rain,entrance,tunnel,drainage,4]
        fig=go.Figure(go.Bar(x=names,y=vals,marker_color=[story.CYAN]*5,text=vals,textposition="outside"))
        fig.update_layout(height=420,paper_bgcolor=story.BG,plot_bgcolor=story.BG,font_color="white",yaxis_title="Raw value (different units)")
        st.plotly_chart(fig,use_container_width=True)
    elif stage=="training":
        e=np.arange(1,41); train=8*np.exp(-e/10)+1.2; val=7*np.exp(-e/9)+1.7+.12*np.maximum(e-28,0)
        fig=go.Figure(); fig.add_scatter(x=e,y=train,name="Training MAE"); fig.add_scatter(x=e,y=val,name="Validation MAE")
        fig.update_layout(height=420,paper_bgcolor=story.BG,plot_bgcolor=story.BG,font_color="white",xaxis_title="Epoch",yaxis_title="MAE (cm)")
        st.plotly_chart(fig,use_container_width=True)
    else:
        st.plotly_chart(story.forecast_chart(4,2,27,6),use_container_width=True)
    st.markdown("#### 5 · In the notebook")
    st.write(step["notebook"])
    st.success(step["takeaway"])
    idx=bridge.ORDER.index(step["id"]); nav=st.columns(3)
    if idx>0: nav[0].markdown(f"[◀ {bridge.STEPS[idx-1]['civil']}](?stage={bridge.ORDER[idx-1]})")
    nav[1].markdown("[Project overview](?stage=start)")
    if idx<len(bridge.STEPS)-1: nav[2].markdown(f"[{bridge.STEPS[idx+1]['civil']} ▶](?stage={bridge.ORDER[idx+1]})")
