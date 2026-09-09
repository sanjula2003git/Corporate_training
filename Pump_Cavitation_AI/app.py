"""Deployment-friendly Pump Cavitation AI teaching application."""
import numpy as np
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split

st.set_page_config(page_title="Pump Cavitation AI",page_icon="⚙️",layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
:root{--ink:#eaf3f8;--muted:#9aafbf;--line:rgba(139,174,194,.20);--panel:#111d27;--cyan:#52d3ff;--amber:#ffbc57;--green:#5ed5a7;--red:#ff6d6d}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}.stApp{color:var(--ink);font-size:17px;background:radial-gradient(circle at 82% -8%,rgba(36,143,181,.22),transparent 34%),#07121a}
.block-container{max-width:1180px;padding-top:2rem;padding-bottom:4rem}h1,h2,h3,h4{font-family:'Manrope',sans-serif!important;letter-spacing:-.025em}p,li{line-height:1.6}
.stMarkdown p,.stMarkdown li,.problem,.card,.term,.chip{font-size:1.05rem}div[data-testid="stSidebar"] label,div[data-testid="stSidebar"] p{font-size:1rem}div[data-testid="stDataFrame"]{font-size:1rem}
.hero{padding:1.65rem 1.8rem;border:1px solid var(--line);border-radius:24px;background:linear-gradient(135deg,#172a37,#0c1821);overflow:hidden}.eyebrow{color:var(--cyan);font-size:.75rem;font-weight:800;letter-spacing:.15em}.hero h1{font-size:clamp(2rem,4vw,3.5rem);margin:.5rem 0}.hero p{color:#bfd0dc;font-size:1.05rem}.flow{display:flex;gap:.65rem;align-items:center;flex-wrap:wrap;margin-top:1rem}.chip{padding:.55rem .75rem;border:1px solid var(--line);border-radius:11px;background:rgba(255,255,255,.035)}
.problem{padding:1.2rem 1.3rem;border-left:4px solid var(--amber);background:rgba(255,188,87,.08);border-radius:5px 16px 16px 5px}.card{height:100%;padding:1rem 1.1rem;border:1px solid var(--line);border-radius:16px;background:rgba(17,29,39,.85);overflow-wrap:anywhere}.card b{color:var(--cyan)}
.glossary{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:.7rem}.term{padding:.85rem 1rem;border:1px solid var(--line);border-radius:14px;background:#111d27}.term b{display:block;color:var(--cyan);margin-bottom:.25rem}.term span{color:#bccbd5}
div[data-testid="stSidebar"]{background:#0d1922;border-right:1px solid var(--line)}div[data-baseweb="select"]>div{background:#152632;border-radius:12px}div[data-testid="stPlotlyChart"],div[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:17px;overflow:hidden}div[data-testid="stMetric"]{padding:.9rem;border:1px solid var(--line);border-radius:14px;background:var(--panel)}.stButton button{min-height:46px;border-radius:12px;font-weight:700}
</style>""",unsafe_allow_html=True)

PAGES=["Overview","1 · Collect sensor data","2 · Clean the data","3 · Train the model","4 · Evaluate the model","5 · Diagnose the pump"]
page=st.sidebar.selectbox("Project stage",PAGES)
st.sidebar.caption("A visual mechanical-engineering learning project. Simulated data—not a machinery safety controller.")

def hero():
    st.markdown("""<div class='hero'><div class='eyebrow'>INTERACTIVE MECHANICAL ENGINEERING LAB</div><h1>⚙️ Pump Cavitation AI</h1><p>Distinguish cavitation from bearing and alignment faults—and tell the engineer what to inspect first.</p><div class='flow'><div class='chip'>Pump sensors</div><span>→</span><div class='chip'>Fault pattern</div><span>→</span><div class='chip'>Likely cause</div><span>→</span><div class='chip'>Inspection priority</div></div></div>""",unsafe_allow_html=True)

@st.cache_data
def make_data(n=1200):
    rng=np.random.default_rng(42)
    classes=np.array(["Normal","Cavitation","Bearing fault","Misalignment"])
    labels=rng.choice(classes,n,p=[.38,.25,.20,.17])
    rows=[]
    means={
        "Normal":[1.15,2.0,100,2.0,2.5,61,12.0],
        "Cavitation":[.48,12.0,76,6.8,13.0,82,13.1],
        "Bearing fault":[1.10,3.2,96,8.0,10.0,78,13.6],
        "Misalignment":[1.08,4.2,91,7.0,5.5,72,14.2],
    }
    scales=[.12,1.2,5,1.0,1.5,3.2,.8]
    for label in labels:
        vals=rng.normal(means[label],scales)
        rows.append(vals.tolist()+[label])
    df=pd.DataFrame(rows,columns=["inlet_pressure_bar","pressure_pulse_pct","flow_pct","vibration_rms","high_freq_vibration","sound_db","motor_current_a","condition"])
    df["inlet_pressure_bar"]=df["inlet_pressure_bar"].clip(.1,1.6)
    df["flow_pct"]=df["flow_pct"].clip(45,115)
    dirty=df.copy()
    for col in ["inlet_pressure_bar","flow_pct","vibration_rms"]:
        dirty.loc[rng.choice(dirty.index,12,replace=False),col]=np.nan
    dirty.loc[rng.choice(dirty.index,5,replace=False),"sound_db"]=170
    dirty=pd.concat([dirty,dirty.iloc[:8]],ignore_index=True)
    return dirty

def clean_data(raw):
    df=raw.drop_duplicates().copy()
    numeric=df.select_dtypes(include="number").columns
    df[numeric]=df[numeric].fillna(df[numeric].median())
    for col in numeric:
        low,high=df[col].quantile([.01,.99])
        df[col]=df[col].clip(low,high)
    return df

@st.cache_resource
def train_model():
    clean=clean_data(make_data())
    X=clean.drop(columns="condition");y=clean["condition"]
    X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=.25,random_state=42,stratify=y)
    model=RandomForestClassifier(n_estimators=220,max_depth=12,min_samples_leaf=3,class_weight="balanced",random_state=42,n_jobs=-1)
    model.fit(X_train,y_train)
    pred=model.predict(X_test)
    return model,X_train,X_test,y_train,y_test,pred

def pump_cutaway():
    fig=go.Figure()
    fig.add_shape(type="circle",x0=3,x1=7,y0=2,y1=6,fillcolor="#1d4051",line=dict(color="#52d3ff",width=3))
    fig.add_shape(type="rect",x0=0,x1=3,y0=3.2,y1=4.8,fillcolor="#264655",line=dict(color="#86aabc",width=2))
    fig.add_shape(type="rect",x0=7,x1=10,y0=3.2,y1=4.8,fillcolor="#264655",line=dict(color="#86aabc",width=2))
    for angle in np.linspace(0,2*np.pi,7)[:-1]:
        fig.add_trace(go.Scatter(x=[5,5+1.5*np.cos(angle)],y=[4,4+1.5*np.sin(angle)],mode="lines",line=dict(color="#ffbc57",width=9),showlegend=False,hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[1.0,1.5,2.0,2.4],y=[4.1,3.8,4.35,3.7],mode="markers",marker=dict(size=[15,20,13,17],color="#eaf3f8",line=dict(color="#52d3ff",width=2)),name="Vapour bubbles"))
    fig.add_annotation(x=1.7,y=5.3,text="Low inlet pressure creates bubbles",showarrow=True,ax=30,ay=-65,arrowcolor="#ffbc57",font=dict(size=15))
    fig.add_annotation(x=4.1,y=2.4,text="Bubbles collapse near the impeller",showarrow=True,ax=30,ay=65,arrowcolor="#ff6d6d",font=dict(size=15))
    fig.update_xaxes(visible=False,range=[-.3,10.3]);fig.update_yaxes(visible=False,range=[1,7])
    fig.update_layout(title="What the engineer cannot see inside a running pump",height=480,paper_bgcolor="#07121a",plot_bgcolor="#0e1a23",font=dict(color="#eaf3f8"),showlegend=False,margin=dict(l=30,r=30,t=65,b=20))
    return fig

def sensor_figure(df):
    sample=df.dropna().sample(160,random_state=4)
    colors={"Normal":"#5ed5a7","Cavitation":"#ff6d6d","Bearing fault":"#ffbc57","Misalignment":"#52d3ff"}
    fig=make_subplots(rows=1,cols=2,subplot_titles=("Pressure and flow","Vibration and sound"),horizontal_spacing=.13)
    for label,color in colors.items():
        d=sample[sample.condition==label]
        fig.add_trace(go.Scatter(x=d.inlet_pressure_bar,y=d.flow_pct,mode="markers",name=label,legendgroup=label,marker=dict(color=color,size=8,opacity=.75)),1,1)
        fig.add_trace(go.Scatter(x=d.vibration_rms,y=d.sound_db,mode="markers",name=label,legendgroup=label,showlegend=False,marker=dict(color=color,size=8,opacity=.75)),1,2)
    fig.update_xaxes(title="Inlet pressure (bar)",row=1,col=1);fig.update_yaxes(title="Flow (% of normal)",row=1,col=1)
    fig.update_xaxes(title="Vibration RMS (mm/s)",row=1,col=2);fig.update_yaxes(title="Sound level (dB)",row=1,col=2)
    fig.update_layout(height=520,paper_bgcolor="#07121a",plot_bgcolor="#0e1a23",font=dict(color="#eaf3f8"),legend=dict(orientation="h",y=1.12),margin=dict(l=45,r=25,t=90,b=55))
    return fig

def flow_chart():
    st.markdown("""<div class='flow'><div class='chip'><b>1 · Measure</b><br>Sound, vibration, pressure and flow</div><span>→</span><div class='chip'><b>2 · Compare</b><br>Learned pump-fault patterns</div><span>→</span><div class='chip'><b>3 · Diagnose</b><br>Most likely condition</div><span>→</span><div class='chip'><b>4 · Act</b><br>Inspect the likely cause first</div></div>""",unsafe_allow_html=True)

hero()
raw=make_data();clean=clean_data(raw);model,X_train,X_test,y_train,y_test,pred=train_model()

if page=="Overview":
    st.markdown("## The mechanical engineer’s problem")
    st.markdown("""<div class='problem'>A pump in a factory, water-treatment plant or power station is making noise, shaking and moving less liquid than expected.<br><br><b>Pump cavitation</b> happens when low pressure creates vapour bubbles in the liquid. When these bubbles collapse, they create tiny impacts inside the pump. This makes the pump noisy, increases vibration, reduces the liquid flow and can slowly damage the rotating blades.<br><br>A worn bearing or parts that are not lined up correctly can cause similar warning signs. This project helps the engineer find the most likely cause and decide what to inspect first.</div>""",unsafe_allow_html=True)
    st.subheader("What happens inside a pump during cavitation")
    st.image(str(Path(__file__).parent / "assets" / "pump_cavitation_cutaway.png"), use_column_width=True)
    st.warning("**What is wrong?** Low pressure at the pump inlet creates vapour bubbles. They collapse near the rotating impeller and can damage its metal surface.")
    st.markdown("## How AI supports the engineer");flow_chart()

elif page==PAGES[1]:
    st.markdown("## Phase 1 · Collect sensor data")
    st.markdown("""<div class='card'><b>What happens in this phase?</b><br>The engineer places sensors on the pump and records what the pump is doing. Each row represents one short operating period.</div>""",unsafe_allow_html=True)
    table=pd.DataFrame([
        ["Inlet pressure","Pressure where liquid enters","bar","Pressure sensor"],["Pressure pulse","How unstable pressure is","%","Pressure sensor"],["Flow","Liquid delivered compared with normal","%","Flow meter"],["Vibration RMS","Overall machine vibration","mm/s","Vibration sensor"],["High-frequency vibration","Fast vibration linked to impacts","relative value","Vibration sensor"],["Sound level","How loud the pump is","dB","Microphone"],["Motor current","Electric current used by the motor","A","Current sensor"],["Condition","Known pump state used for learning","text","Engineer inspection"]],columns=["Information collected","What it means","Unit","Where it comes from"])
    st.dataframe(table,use_container_width=True,hide_index=True)
    st.markdown("### How the collected data looks")
    st.dataframe(raw.head(12),use_container_width=True,hide_index=True)
    st.plotly_chart(sensor_figure(raw),use_container_width=True,config={"displayModeBar":False})
    st.info("Cavitation usually combines low inlet pressure, reduced flow, unstable pressure, louder sound and stronger high-frequency vibration.")

elif page==PAGES[2]:
    st.markdown("## Phase 2 · Clean the data")
    st.markdown("""<div class='card'><b>What happens in this phase?</b><br>Repeated rows are removed, empty measurements are filled and extreme sensor errors are clipped before model training.</div>""",unsafe_allow_html=True)
    duplicate_count=int(raw.duplicated().sum());missing_count=int(raw.isna().sum().sum());outlier_count=int((raw.sound_db>120).sum())
    a,b,c=st.columns(3);a.metric("Repeated rows",duplicate_count);b.metric("Empty cells",missing_count);c.metric("Extreme sound readings",outlier_count)
    tabs=st.tabs(["1 · Remove duplicates","2 · Fill missing values","3 · Clip outliers","4 · Before and after"])
    with tabs[0]:st.write("The same operating period should not teach the model twice.");st.code("data = data.drop_duplicates()",language="python")
    with tabs[1]:st.write("Empty numeric cells are filled with the middle value of that column.");st.code("data[numeric] = data[numeric].fillna(data[numeric].median())",language="python")
    with tabs[2]:st.write("A sensor error can be capped at a reasonable data limit instead of deleting the complete row.");st.code("low, high = data[col].quantile([0.01, 0.99])\ndata[col] = data[col].clip(low, high)",language="python")
    with tabs[3]:
        x,y=st.columns(2);x.markdown("#### Before cleaning");x.dataframe(raw.head(10),use_container_width=True,hide_index=True);y.markdown("#### After cleaning");y.dataframe(clean.head(10),use_container_width=True,hide_index=True)
    st.success(f"Cleaning reduced {len(raw):,} rows to {len(clean):,} unique, usable rows.")

elif page==PAGES[3]:
    st.markdown("## Phase 3 · Train the model")
    st.markdown("""<div class='card'><b>What happens in this phase?</b><br>The model studies sensor rows whose pump condition is already known. It learns combinations that separate normal operation, cavitation, bearing faults and misalignment.</div>""",unsafe_allow_html=True)
    st.markdown("### Why Random Forest?")
    st.write("Random Forest combines many decision trees. It works well with table-shaped sensor data, learns nonlinear fault patterns and does not require feature scaling.")
    flow_chart()
    st.code("""model = RandomForestClassifier(
    n_estimators=220,
    max_depth=12,
    class_weight="balanced",
    random_state=42,
)
model.fit(X_train, y_train)""",language="python")
    importance=pd.DataFrame({"Measurement":X_train.columns,"Importance":model.feature_importances_}).sort_values("Importance")
    fig=go.Figure(go.Bar(x=importance.Importance,y=importance.Measurement,orientation="h",marker_color="#52d3ff"))
    fig.update_layout(title="Measurements the model relied on",height=430,paper_bgcolor="#07121a",plot_bgcolor="#0e1a23",font=dict(color="#eaf3f8"),margin=dict(l=40,r=30,t=65,b=40))
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    st.caption("Feature importance shows what the model used most. It does not prove that a measurement directly caused the fault.")

elif page==PAGES[4]:
    st.markdown("## Phase 4 · Evaluate the model")
    st.markdown("""<div class='card'><b>What happens in this phase?</b><br>The model receives pump rows it did not see during training. Its answers are compared with the known pump conditions.</div>""",unsafe_allow_html=True)
    acc=accuracy_score(y_test,pred);a,b,c=st.columns(3);a.metric("Unseen test rows",len(y_test));b.metric("Correct classifications",int((pred==y_test).sum()));c.metric("Accuracy",f"{acc:.1%}")
    labels=list(model.classes_);cm=confusion_matrix(y_test,pred,labels=labels)
    fig=go.Figure(go.Heatmap(z=cm,x=labels,y=labels,colorscale=[[0,"#101d27"],[1,"#52d3ff"]],text=cm,texttemplate="%{text}",showscale=False))
    fig.update_layout(title="Confusion matrix: known condition versus model answer",xaxis_title="Model answer",yaxis_title="Known condition",height=520,paper_bgcolor="#07121a",plot_bgcolor="#0e1a23",font=dict(color="#eaf3f8"))
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    report=pd.DataFrame(classification_report(y_test,pred,output_dict=True,zero_division=0)).T.reset_index().rename(columns={"index":"Condition"})
    st.dataframe(report.round(3),use_container_width=True,hide_index=True)
    st.warning("High performance on simulated test data does not guarantee the same performance on a real pump. Real sensor data and engineer-labelled faults are required before field use.")

elif page==PAGES[5]:
    st.markdown("## Phase 5 · Diagnose the pump")
    st.markdown("""<div class='card'><b>What happens in this phase?</b><br>Enter the current measurements. The model suggests the most likely condition and tells the engineer what to inspect first.</div>""",unsafe_allow_html=True)
    l,r=st.columns(2)
    inlet=l.slider("Inlet pressure (bar)",.1,1.6,.48,.01);pulse=r.slider("Pressure fluctuation (%)",0.0,20.0,12.0,.2)
    flow=l.slider("Flow compared with normal (%)",45.0,115.0,76.0,1.0);vib=r.slider("Overall vibration RMS (mm/s)",.5,12.0,6.8,.1)
    high=l.slider("High-frequency vibration",.5,18.0,13.0,.1);sound=r.slider("Sound level (dB)",45.0,100.0,82.0,1.0)
    current=l.slider("Motor current (A)",8.0,18.0,13.1,.1)
    row=pd.DataFrame([[inlet,pulse,flow,vib,high,sound,current]],columns=X_train.columns)
    probabilities=model.predict_proba(row)[0];prediction=model.classes_[np.argmax(probabilities)]
    st.markdown("### Model result")
    p1,p2=st.columns(2);p1.metric("Most likely condition",prediction);p2.metric("Model confidence",f"{probabilities.max():.1%}")
    prob_df=pd.DataFrame({"Condition":model.classes_,"Probability":probabilities}).sort_values("Probability")
    fig=go.Figure(go.Bar(x=prob_df.Probability,y=prob_df.Condition,orientation="h",marker_color=["#ff6d6d" if x==prediction else "#52d3ff" for x in prob_df.Condition],text=[f"{v:.0%}" for v in prob_df.Probability],textposition="outside"))
    fig.update_layout(title="How the model compared possible pump conditions",xaxis_tickformat=".0%",xaxis_range=[0,1.08],height=390,paper_bgcolor="#07121a",plot_bgcolor="#0e1a23",font=dict(color="#eaf3f8"),margin=dict(l=40,r=45,t=65,b=40))
    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    advice={
        "Cavitation":("Cavitation is likely.",["Check tank liquid level.","Confirm the inlet valve is fully open.","Inspect the inlet pipe and filter for blockage.","Check liquid temperature and pump speed."]),
        "Bearing fault":("A bearing fault is likely.",["Inspect bearing lubrication.","Check bearing temperature and looseness.","Review the vibration frequency spectrum."]),
        "Misalignment":("Shaft misalignment is likely.",["Check motor-to-pump shaft alignment.","Inspect coupling condition and mounting bolts.","Confirm pipe strain is not pulling the pump."]),
        "Normal":("The measurements resemble normal operation.",["Continue routine monitoring.","Investigate if the operator still reports unusual noise or loss of flow."])
    }
    title,items=advice[prediction];st.success(f"**{title}**");st.markdown("#### What the engineer should inspect first");st.markdown("\n".join(f"- {item}" for item in items))
    st.error("The model supports diagnosis; it does not decide whether machinery is safe to operate. Follow site procedures and qualified engineering judgment.")
