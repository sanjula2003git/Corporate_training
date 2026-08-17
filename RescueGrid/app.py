"""Interactive engineering illustrations for the RescueGrid notebook."""
import pandas as pd
import streamlit as st
import bridge
import rescuegrid as rg

st.set_page_config(page_title="RescueGrid",page_icon="🟩",layout="wide")
st.markdown("""<style>.stApp{background:#0e1117;color:#e6edf3}.block-container{max-width:1200px}
.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}
.scene{color:#ffb74d}.ai{color:#4fc3f7}.stButton button{background:transparent;border:1px solid #30363d;color:#e6edf3;text-align:left}
.stButton button:hover{border-color:#4fc3f7;color:#4fc3f7;background:#161b22}</style>""",unsafe_allow_html=True)
DISCLAIMER=("Educational simulation using invented scenes. It is not a medical device or emergency system. "
            "It organizes space and must not diagnose, select treatment, or override responders.")

with st.sidebar:
    st.header("Scene")
    width=st.slider("Room width (tiles)",7,18,12); height=st.slider("Room height (tiles)",7,18,12)
    entrance=st.selectbox("Responder entrance",["East","North","West","South"])
    helpers=st.slider("Helpers",1,7,4); crowd=st.slider("Crowd size",0,45,18)
    obstacles=st.slider("Obstacle ratio",.02,.32,.10,.01)
    mat_fraction=st.slider("Working mat fraction",.5,1.,1.,.05)
    failure=st.slider("Sensor failure rate",0.,.35,0.,.01)
    seed=st.number_input("Scene seed",0,999,7)

scene=rg.Scene(width=width,height=height,entrance=entrance,helpers=helpers,crowd=crowd,
               obstacle_ratio=obstacles,mat_fraction=mat_fraction,sensor_failure=failure,seed=int(seed))
world=rg.build_scene(scene); result=rg.optimize_layout(world)
events=rg.sensor_stream(world,result["layout"],50,int(seed),failure)
stage=st.query_params.get("stage","start")

def goto(target,label,key,where=None):
    if (where or st).button(label,key=key,width="stretch"):
        st.query_params["stage"]=target; st.rerun()

def header(s):
    p=bridge.PHASES[s["phase"]]
    st.markdown(f"<div class='hero'><small>PHASE {s['phase']+1} OF 4 · {p[0]}</small><h1>🟩 {s['scene']}</h1>"
                f"<h3><span class='scene'>{s['scene']}</span> → <span class='ai'>{s['ai']}</span></h3></div>",unsafe_allow_html=True)
    a,b,c=st.columns(3); a.markdown("#### 1 · In the scene"); a.write(s["site"])
    b.markdown("#### 2 · Why it is hard"); b.write(s["challenge"])
    c.markdown("#### 3 · Where AI comes in"); c.write(s["ai_link"])
    st.markdown(f"#### 4 · What it looks like — `{s['tech']}`")

def footer(s):
    st.markdown("#### 5 · In the notebook"); st.write(s["notebook"]); st.success(s["takeaway"])
    i=bridge.ORDER.index(s["id"]); cols=st.columns(3)
    if i: goto(bridge.ORDER[i-1],"◀ "+bridge.STEPS[i-1]["scene"],"p"+s["id"],cols[0])
    goto("start","Overview","h"+s["id"],cols[1])
    if i<len(bridge.ORDER)-1: goto(bridge.ORDER[i+1],bridge.STEPS[i+1]["scene"]+" ▶","n"+s["id"],cols[2])

def dashboard():
    m=result["metrics"]
    a,b,c,d=st.columns(4); a.metric("Access path","CLEAR" if m["access_clear"] else "BLOCKED")
    b.metric("Primary helper","ASSIGNED" if "primary" in result["layout"] else "WAIT")
    c.metric("Equipment distance",f"{m['equipment_distance']} tiles")
    d.metric("Layout cost",f"{m['layout_cost']:.0f}")
    st.plotly_chart(rg.fig_grid(world,result),width="stretch")
    st.warning(rg.feedback(world,result,events,crowd_violations=max(0,crowd-28)))

if stage=="start":
    st.title("🟩 RescueGrid")
    st.warning(DISCLAIMER)
    st.markdown("**Can an adaptive illuminated mat reduce responder-path blockages, incorrect helper positioning "
                "and equipment-placement time compared with static floor markings?**")
    dashboard(); st.subheader("Learning journey")
    for i,s in enumerate(bridge.STEPS,1): goto(s["id"],f"**{i}. {s['scene']}** — {s['ai']}","j"+s["id"])
else:
    s=bridge.BY_ID.get(stage,bridge.STEPS[0]); header(s)
    if s["id"]=="scene": dashboard()
    elif s["id"]=="rules":
        rule=rg.rule_layout(world); rr={"layout":rule,"metrics":rg.layout_metrics(world,rule),"path":rg.access_path(world,rule)}
        a,b=st.columns(2); a.plotly_chart(rg.fig_grid(world,rr,"Nearest-free rules"),width="stretch")
        b.plotly_chart(rg.fig_grid(world,result,"Constrained layout"),width="stretch")
    elif s["id"]=="graph":
        st.plotly_chart(rg.fig_grid(world,result,"A* keeps a connected responder lane"),width="stretch")
        st.info(f"{width*height} possible tiles · {int((world['grid']!=rg.OBSTACLE).sum())} graph nodes · path length {len(result['path'])}")
    elif s["id"]=="optimize":
        st.plotly_chart(rg.fig_grid(world,result),width="stretch"); st.dataframe(pd.Series(result["metrics"],name="value"),width="stretch")
    elif s["id"]=="roles":
        people=[dict(id=f"H{i+1}",training_verified=i==0,mobility="limited" if i==2 else "normal",
                     carrying_equipment=i==1,fatigue=.15*i) for i in range(helpers)]
        st.dataframe(rg.assign_roles(people).set_index("role"),width="stretch")
        st.info("Training is declared or verified. Appearance is never an input.")
    elif s["id"]=="sensors":
        st.plotly_chart(rg.fig_sensor(events),width="stretch"); st.warning(rg.feedback(world,result,events))
    elif s["id"]=="replan":
        old=result
        blocked=old["layout"].get("secondary",old["layout"].get("replacement",world["entrance"]))
        new_world=dict(world); new_world["grid"]=world["grid"].copy(); new_world["grid"][blocked]=rg.OBSTACLE
        new=rg.optimize_layout(new_world,previous=old["layout"],crowd_tiles=[blocked])
        a,b=st.columns(2); a.plotly_chart(rg.fig_grid(world,old,"Before obstruction"),width="stretch")
        b.plotly_chart(rg.fig_grid(new_world,new,"After stable replanning"),width="stretch")
        st.metric("People moved",new["metrics"]["people_moved"])
        st.caption(f"A new obstruction occupies tile {blocked}; unchanged safe assignments keep their positions.")
    elif s["id"]=="fatigue":
        fatigue=st.slider("Primary helper fatigue",0.,1.,.65,.05)
        st.plotly_chart(rg.fig_grid(world,result,"Yellow replacement position prepared"),width="stretch")
        st.info("PREPARE REPLACEMENT" if fatigue>.6 else "PRIMARY POSITION VERIFIED")
        st.caption("The mat prepares space. Dispatcher-approved protocols govern any handover.")
    elif s["id"]=="environments":
        env=st.selectbox("Environment",["Airport hall","Railway platform","Classroom","Bus aisle","Small office","Sports field","Lift lobby","Shopping centre","Roadside shoulder"])
        ew=rg.build_scene(rg.environment_scene(env,int(seed))); er=rg.optimize_layout(ew)
        st.plotly_chart(rg.fig_grid(ew,er,env),width="stretch")
    elif s["id"]=="benchmark":
        table=rg.compare_controllers(scene); st.dataframe(table.set_index("controller"),width="stretch")
        st.plotly_chart(rg.fig_controller_bars(table),width="stretch")
    footer(s)
