"""Interactive engineering illustrations for the Guardian Road notebook."""
import pandas as pd
import streamlit as st

import bridge
import guardian as g

st.set_page_config(page_title="Guardian Road", page_icon="🛣️", layout="wide")
st.markdown("""<style>
.stApp{background:#0e1117;color:#e6edf3}.block-container{max-width:1200px}
.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}
.scene{color:#ffb74d}.ai{color:#4fc3f7}
.stButton button{background:transparent;border:1px solid #30363d;color:#e6edf3;text-align:left}
.stButton button:hover{border-color:#4fc3f7;color:#4fc3f7;background:#161b22}
</style>""", unsafe_allow_html=True)

DISCLAIMER = ("Educational simulation using invented traffic. It is not a traffic controller, "
              "medical device or emergency system, and must not control a real road.")

with st.sidebar:
    st.header("Road conditions")
    speed = st.slider("Approach speed (km/h)", 30, 110, 72, 2)
    weather = st.selectbox("Weather", list(g.WEATHER), index=1)
    reaction = st.slider("Driver reaction (s)", .7, 2.8, 1.4, .1)
    vehicle = st.selectbox("Closest vehicle", list(g.VEHICLES), index=1)
    density = st.slider("Traffic density (vehicles/km)", 5, 75, 34)
    left = st.slider("Left-lane occupancy", .05, .98, .32, .01)
    right = st.slider("Right-lane occupancy", .05, .98, .78, .01)
    eta = st.slider("Ambulance ETA (minutes)", 1, 15, 9)
    st.header("Sensor health")
    camera = st.checkbox("Camera available", True)
    radar = st.checkbox("Radar available", True)
    comms = st.checkbox("Control link available", True)
    studs = st.slider("Road studs responding", 0., 1., 1., .05)
    confidence = st.slider("Incident confidence", .4, 1., .97, .01)
    st.caption("Every page uses these conditions.")

scene = g.Scene(speed_kmh=speed, weather=weather, reaction_s=reaction,
                vehicle_type=vehicle, density=density, left_occupancy=left,
                right_occupancy=right, ambulance_eta_min=eta,
                detection_confidence=confidence, radar_ok=radar,
                camera_ok=camera, studs_ok=studs, communications_ok=comms)
action = g.controller(scene)
stage = st.query_params.get("stage", "start")


def goto(target, label, key, where=None):
    if (where or st).button(label, key=key, width="stretch"):
        st.query_params["stage"] = target
        st.rerun()


def header(s):
    phase = bridge.PHASES[s["phase"]]
    st.markdown(f"<div class='hero'><small>PHASE {s['phase']+1} OF 4 · {phase[0]}</small>"
                f"<h1>🛣️ {s['scene']}</h1><h3><span class='scene'>{s['scene']}</span> → "
                f"<span class='ai'>{s['ai']}</span></h3></div>", unsafe_allow_html=True)
    a,b,c=st.columns(3)
    a.markdown("#### 1 · On the road"); a.write(s["site"])
    b.markdown("#### 2 · Why it is hard"); b.write(s["challenge"])
    c.markdown("#### 3 · Where AI comes in"); c.write(s["ai_link"])
    st.markdown(f"#### 4 · What it looks like — `{s['tech']}`")


def footer(s):
    st.markdown("#### 5 · In the notebook")
    st.write(s["notebook"]); st.success(s["takeaway"])
    i=bridge.ORDER.index(s["id"]); cols=st.columns(3)
    if i: goto(bridge.ORDER[i-1],"◀ "+bridge.STEPS[i-1]["scene"],"p"+s["id"],cols[0])
    goto("start","Overview","h"+s["id"],cols[1])
    if i<len(bridge.ORDER)-1: goto(bridge.ORDER[i+1],bridge.STEPS[i+1]["scene"]+" ▶","n"+s["id"],cols[2])


def dashboard():
    o=g.outcome(scene,action)
    a,b,c,d=st.columns(4)
    a.metric("Required warning",f"{action['warning_m']} m")
    b.metric("Collision risk",f"{100*o['collision_probability']:.1f}%")
    c.metric("Temporary limit",f"{action['speed_limit']} km/h")
    d.metric("Merge plan",action["merge"])
    st.plotly_chart(g.fig_road(scene,action),width="stretch")
    a,b,c,d=st.columns(4)
    a.metric("Queue / delay estimate",f"{o['traffic_delay_s']:.0f} s")
    b.metric("Ambulance ETA",f"{scene.ambulance_eta_min:.0f} min")
    c.metric("Ambulance lane","Reserved" if action["reserve_ambulance"] else "Not reserved")
    d.metric("Mode","FALLBACK" if action["fallback"] else "Protected")


if stage == "start":
    st.title("🛣️ Guardian Road")
    st.warning(DISCLAIMER)
    st.markdown("**Can a physics-guided AI controller reduce simulated secondary-collision risk "
                "while producing less severe braking and less traffic delay than a fixed warning?**")
    dashboard()
    st.subheader("Learning journey")
    for i,s in enumerate(bridge.STEPS,1):
        goto(s["id"],f"**{i}. {s['scene']}** — {s['ai']}","j"+s["id"])
else:
    s=bridge.BY_ID.get(stage,bridge.STEPS[0]); header(s)
    if s["id"]=="scene": dashboard()
    elif s["id"]=="detect":
        st.plotly_chart(g.fig_detection(),width="stretch")
        st.info("The traffic warning begins conservatively before a person verifies the event. Medical condition remains unknown.")
    elif s["id"]=="distance":
        d=g.required_warning(scene)
        st.dataframe(pd.DataFrame({"metres":[d["reaction_m"],d["braking_m"],d["base_stop_m"],d["required_m"]]},
                     index=["reaction","braking","level-road stop","with margins"]),width="stretch")
        st.plotly_chart(g.fig_tradeoff(scene),width="stretch")
    elif s["id"]=="zones":
        elapsed=st.slider("Seconds since obstruction confirmation",0.,8.,8.,.5)
        live=dict(action)
        # An immediate 120 m warning appears first; the optimized field expands over five seconds.
        live["warning_m"]=int(min(action["warning_m"],120+max(0,action["warning_m"]-120)*elapsed/5))
        st.plotly_chart(g.fig_road(scene,live),width="stretch")
        st.dataframe(g.road_zones(live).set_index("zone"),width="stretch")
        st.caption("Move the time control: warning appears immediately, then expands without waiting for optimization.")
    elif s["id"]=="merge":
        dashboard(); st.info(action["merge_reason"])
        st.write("The ambulance lane is " + ("reserved now." if action["reserve_ambulance"] else "not reserved yet."))
    elif s["id"]=="routes":
        cost=g.hazard_grid(active_lanes=() if action["upstream_red"] else (0,2),reserve_lane=0)
        path=g.plan_path(cost)
        st.plotly_chart(g.fig_hazard(cost,path),width="stretch")
        st.warning("A real deployment must confirm that vehicle flows are stopped before showing this route.")
    elif s["id"]=="failure":
        dashboard()
        if action["fallback"]: st.error("Conservative fallback is active: expand protection and stop conflicting entries.")
        else: st.success("Required sensors and communications are healthy.")
    elif s["id"]=="score":
        table=g.compare_controllers(scene)
        shown=table[["Controller","warning_m","collision_probability","max_deceleration","traffic_delay_s","ambulance_blockage"]]
        st.dataframe(shown.set_index("Controller").style.format("{:.2f}"),width="stretch")
        st.plotly_chart(g.fig_tradeoff(scene),width="stretch")
    elif s["id"]=="restore":
        st.markdown("1. Confirm lane clearance\n2. Remove the red exclusion zone\n3. Keep a temporary reduced speed\n4. Release queued traffic gradually\n5. Restore signals\n6. Record failed studs and sensors")
        st.info("Responder authorization is a required guard. The optimizer cannot declare the road clear.")
    footer(s)
