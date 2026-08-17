"""Interactive illustrations for the bakery rescue notebook."""
import pandas as pd
import streamlit as st
import bakery as b
import bridge

st.set_page_config(page_title="Bakery Rescue AI",page_icon="🥐",layout="wide")
st.markdown("""<style>.stApp{background:#0e1117;color:#e6edf3}.block-container{max-width:1200px}
.hero{padding:1.1rem 1.3rem;border:1px solid #30363d;border-radius:15px;background:#161b22}
.scene{color:#ffb74d}.ai{color:#4fc3f7}.stButton button{background:transparent;border:1px solid #30363d;color:#e6edf3;text-align:left}
.stButton button:hover{border-color:#4fc3f7;color:#4fc3f7;background:#161b22}</style>""",unsafe_allow_html=True)

with st.sidebar:
    st.header("Bakery state")
    product=st.selectbox("Product",list(b.PRODUCTS),index=2);day=st.selectbox("Day",list(b.DAYS))
    hour=st.slider("Hour",7,20,17);stock=st.slider("Remaining stock",0,90,38)
    weather=st.selectbox("Weather",list(b.WEATHER_FACTOR),index=2);footfall=st.selectbox("Footfall",["Low","Normal","High"])
    recent=st.slider("Recent sales/hour",0.,15.,4.,.5);life=st.slider("Safe life remaining (h)",0.,14.,5.,.5)
    shelter=st.checkbox("Shelter available",True);strategy=st.selectbox("Strategy",["Profit-first","Waste-first","Balanced","Community-first"],index=2)
state=b.State(product=product,day=day,hour=hour,stock=stock,weather=weather,footfall=footfall,
              recent_sales_rate=recent,shelf_life_remaining=life,shelter_available=shelter)
rec=b.recommend(state,strategy);stage=st.query_params.get("stage","start")

def goto(target,label,key,where=None):
    if (where or st).button(label,key=key,width="stretch"):st.query_params["stage"]=target;st.rerun()
def header(s):
    p=bridge.PHASES[s["phase"]];st.markdown(f"<div class='hero'><small>PHASE {s['phase']+1} OF 4 · {p[0]}</small><h1>🥐 {s['scene']}</h1>"
      f"<h3><span class='scene'>{s['scene']}</span> → <span class='ai'>{s['ai']}</span></h3></div>",unsafe_allow_html=True)
    a,c,d=st.columns(3);a.markdown("#### 1 · In the bakery");a.write(s["site"]);c.markdown("#### 2 · Why it is hard");c.write(s["challenge"])
    d.markdown("#### 3 · Where AI comes in");d.write(s["ai_link"]);st.markdown(f"#### 4 · What it looks like — `{s['tech']}`")
def footer(s):
    st.markdown("#### 5 · In the notebook");st.write(s["notebook"]);st.success(s["takeaway"]);i=bridge.ORDER.index(s["id"]);cols=st.columns(3)
    if i:goto(bridge.ORDER[i-1],"◀ "+bridge.STEPS[i-1]["scene"],"p"+s["id"],cols[0])
    goto("start","Overview","h"+s["id"],cols[1])
    if i<len(bridge.ORDER)-1:goto(bridge.ORDER[i+1],bridge.STEPS[i+1]["scene"]+" ▶","n"+s["id"],cols[2])
def dashboard():
    a,c,d,e=st.columns(4);a.metric("Recommended action",rec["action"].replace("_"," ").title());c.metric("Public price",f"₹{rec['public_price']:.0f}")
    d.metric("Predicted surplus",f"{rec.get('predicted_surplus',0):.0f}");e.metric("Donation reserve",f"{rec.get('donation',0):.0f}")
    actions=pd.DataFrame([b.evaluate_action(state,x,b.strategy_weights(strategy)) for x in b.ACTIONS])
    st.plotly_chart(b.fig_actions(actions),width="stretch");st.info(rec.get("reason",""));st.caption("One public price applies to every comparable customer during this period.")

if stage=="start":
    st.title("🥐 Sell It, Share It, Don’t Waste It");st.warning("Educational simulation. Prices, sales and social-value results are invented.")
    st.markdown("**Can AI reduce bakery waste while maintaining profit through transparent public discounts, production decisions and planned donations?**")
    dashboard();st.subheader("Learning journey")
    for i,s in enumerate(bridge.STEPS,1):goto(s["id"],f"**{i}. {s['scene']}** — {s['ai']}","j"+s["id"])
else:
    s=bridge.BY_ID.get(stage,bridge.STEPS[0]);header(s)
    if s["id"]=="morning":
        st.dataframe(pd.DataFrame(b.PRODUCTS).T,width="stretch");st.plotly_chart(b.fig_demand(product),width="stretch")
    elif s["id"]=="demand":st.plotly_chart(b.fig_demand(product),width="stretch")
    elif s["id"]=="price":st.plotly_chart(b.fig_elasticity(),width="stretch")
    elif s["id"] in ("actions","objective"):
        dashboard();st.dataframe(pd.DataFrame([b.evaluate_action(state,x,b.strategy_weights(strategy)) for x in b.ACTIONS]).set_index("action"),width="stretch")
    elif s["id"]=="donation":
        st.metric("Collection feasible","YES" if b.donation_feasible(state) else "NO");dashboard();st.warning("Reserved donations are not reclaimed for a small late profit.")
    elif s["id"]=="production":
        st.dataframe(pd.DataFrame([b.production_decision(state,x) for x in (1,.5,0)]).set_index("batch_units"),width="stretch")
    elif s["id"]=="behaviour":
        st.markdown("- One public price per period\n- Regular price remains truthful\n- Deep discounts are frequency-limited\n- No identity or protected characteristic is used\n- No misleading scarcity")
    elif s["id"]=="shocks":
        shock=st.selectbox("Unexpected event",["Sudden rain","Sports event","Refrigerator failure","Shelter cancels","Footfall sensor fails"])
        st.warning(f"Replanning for: {shock}");dashboard()
    elif s["id"]=="week":
        week=b.simulate_week();st.dataframe(week.set_index("Strategy"),width="stretch");st.plotly_chart(b.fig_week(week),width="stretch")
    footer(s)
