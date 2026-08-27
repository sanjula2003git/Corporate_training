"""Interactive illustrations for the Unexpected Foundation Settlement notebook."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

import bridge
import story

st.set_page_config(page_title="Foundation Settlement AI",page_icon="🏗️",layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root{--ink:#eaf2f8;--muted:#91a4b7;--line:rgba(147,171,194,.18);--panel:#111a24;
--panel2:#172432;--cyan:#54d2ff;--amber:#ffbd59;--green:#5dd6a8;--red:#ff6b6b}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}.stApp{color:var(--ink);
background:radial-gradient(circle at 82% -10%,rgba(40,142,180,.20),transparent 32%),
radial-gradient(circle at -10% 55%,rgba(255,189,89,.08),transparent 25%),#081019}
.block-container{max-width:1180px;padding-top:2.4rem;padding-bottom:4rem}
h1,h2,h3,h4{font-family:'Manrope',sans-serif!important;letter-spacing:-.025em}
p,li{line-height:1.62}.hero{position:relative;overflow:hidden;padding:1.55rem 1.7rem;border:1px solid var(--line);
border-radius:24px;background:linear-gradient(135deg,rgba(23,36,50,.96),rgba(11,22,32,.96));
box-shadow:0 24px 70px rgba(0,0,0,.25)}
.hero:after{content:'';position:absolute;width:260px;height:260px;right:-75px;top:-105px;border-radius:50%;
background:radial-gradient(circle,rgba(84,210,255,.22),transparent 68%);pointer-events:none}
.hero small{display:inline-flex;color:#a9c0d2;letter-spacing:.13em;font-weight:700;font-size:.72rem;
padding:.38rem .7rem;border:1px solid var(--line);border-radius:999px;background:rgba(255,255,255,.025)}
.hero h1{font-size:clamp(2rem,3.5vw,3rem);line-height:1.08;margin:.65rem 0 .55rem;max-width:900px}
.hero h3{font-size:clamp(1rem,1.6vw,1.25rem);font-weight:600;margin:0;color:#c7d6e2}
.hero-top{display:flex;align-items:center;gap:1rem;margin-top:1.15rem}
.hero-icon{width:62px;height:62px;display:grid;place-items:center;flex:0 0 62px;border-radius:17px;
background:linear-gradient(145deg,rgba(84,210,255,.18),rgba(255,189,89,.12));border:1px solid rgba(84,210,255,.28);
box-shadow:inset 0 1px 0 rgba(255,255,255,.08);font-size:1.75rem;color:var(--cyan)}
.hero-copy h1{margin:0;font-size:clamp(1.85rem,3.5vw,3rem);letter-spacing:-.045em}
.hero-copy p{margin:.3rem 0 0;color:var(--muted);font-size:.96rem}
.outcome-row{display:flex;align-items:center;gap:.65rem;flex-wrap:wrap;margin-top:1.25rem}
.outcome-chip{display:inline-flex;align-items:center;gap:.48rem;padding:.58rem .8rem;border-radius:11px;
border:1px solid var(--line);background:rgba(255,255,255,.035);font-size:.94rem;font-weight:600;color:#d7e4ed}
.outcome-chip b{color:var(--amber)}.outcome-chip.result b{color:var(--cyan)}
.flow-arrow{color:#7890a3;font-size:1.15rem;font-weight:700}
.site{color:var(--amber)}.ai{color:var(--cyan)}
.problem-card{margin:1rem 0;padding:1.25rem 1.4rem;border-left:4px solid var(--amber);border-radius:4px 18px 18px 4px;
background:linear-gradient(90deg,rgba(255,189,89,.10),rgba(23,36,50,.65));font-size:1.05rem}
.glossary-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:.75rem;margin:.55rem 0 1.1rem}
.term-card{padding:.9rem 1rem;border:1px solid var(--line);border-radius:14px;background:rgba(17,26,36,.78)}
.term-card b{display:block;color:var(--cyan);font-family:'Manrope';margin-bottom:.25rem}.term-card span{color:#b9c8d5;font-size:.91rem;line-height:1.4}
.hero,.problem-card,.term-card,.outcome-chip{overflow-wrap:anywhere;word-break:normal;min-width:0}
div[data-testid="stSidebar"]{background:linear-gradient(180deg,#101b26,#0a131d);border-right:1px solid var(--line)}
div[data-testid="stSidebar"] .block-container{padding-top:1.5rem}
div[data-baseweb="select"]>div{background:#152330;border-color:#315069;border-radius:12px;min-height:48px}
.stSlider [data-baseweb="slider"]{padding-top:.7rem}.stButton button{min-height:46px;border:1px solid var(--line);
border-radius:12px;background:rgba(17,26,36,.75);color:var(--ink);font-weight:600;text-align:left;
transition:all .18s ease}.stButton button:hover{border-color:var(--cyan);color:var(--cyan);
background:rgba(84,210,255,.07);transform:translateY(-1px)}
div[data-testid="stPlotlyChart"]{border:1px solid var(--line);border-radius:18px;overflow:hidden;
box-shadow:0 14px 45px rgba(0,0,0,.18)}
div[data-testid="stAlert"]{border-radius:14px;border-width:1px}
div[data-testid="stMetric"]{padding:1rem;border:1px solid var(--line);border-radius:14px;background:var(--panel)}
div[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:14px;overflow:hidden}
hr{border-color:var(--line)!important;margin:2rem 0!important}
@media(max-width:700px){.block-container{padding:1rem}.hero{padding:1.2rem}.hero-top{align-items:flex-start}.hero-icon{width:52px;height:52px;flex-basis:52px}.hero h1,.hero-copy h1{font-size:1.85rem}.flow-arrow{display:none}.outcome-chip{width:100%}}
</style>""",unsafe_allow_html=True)

with st.sidebar:
    st.header("Project stages")
    nav_items=[("start","⓪ Start — understand the problem")]+[(s["id"],f"{i+1} · {s['title']}") for i,s in enumerate(bridge.STEPS)]
    nav_ids=[x[0] for x in nav_items]
    nav_labels=[x[1] for x in nav_items]
    current=nav_ids.index(st.query_params.get("stage","start")) if st.query_params.get("stage","start") in nav_ids else 0
    chosen=st.selectbox("Where are we in the project?",nav_labels,index=current,key=f"stage_nav_{nav_ids[current]}")
    chosen_id=nav_ids[nav_labels.index(chosen)]
    if chosen_id != nav_ids[current]:
        st.query_params["stage"]=chosen_id
        st.rerun()
    st.caption("Choose any stage. You can move forward or return here at any time.")
    st.divider()
    st.header("Try different conditions")
    softness=st.slider("Soft-clay pocket thickness (m)",3.0,10.0,7.0,.5,
                       help="Maximum extra compressible-clay thickness in the southeast zone.")
    groundwater=st.slider("Groundwater drop near pocket (m)",0.0,2.5,1.2,.1)
    load_scale=st.slider("Building load multiplier",.6,1.5,1.0,.1)
    st.caption("Change a setting. The figures are recalculated.")

@st.cache_data(show_spinner="Building the virtual site...")
def get_site(s,g,l): return story.build_site(s,g,l)

@st.cache_resource(show_spinner="Training the settlement model...")
def get_model(s,g,l):
    df,_=get_site(s,g,l)
    return story.train_model(df)

df,boreholes=get_site(softness,groundwater,load_scale)
model,test,metrics=get_model(softness,groundwater,load_scale)
grid,xx,yy=story.risk_grid(model,boreholes,softness,groundwater,load_scale)
stage=st.query_params.get("stage","start")
CLEAN_COLUMNS={
    "spt_n":"SPT blow count","cpt_qc_mpa":"CPT resistance","soft_clay_m":"Soft-clay thickness",
    "groundwater_drop_m":"Groundwater drop","column_load_kn":"Building load",
    "foundation_width_m":"Foundation width","settlement_mm":"Downward movement"
}
clean_column="settlement_mm"
if stage=="cleaning":
    with st.sidebar:
        st.divider()
        st.subheader("Distribution chart")
        clean_column=st.selectbox("Choose a column",list(CLEAN_COLUMNS),
            index=list(CLEAN_COLUMNS).index("settlement_mm"),format_func=lambda x:CLEAN_COLUMNS[x])
        st.caption("The histogram and curve update when you choose another column.")

def goto(target,label,key,column=None):
    host=column or st
    if host.button(label,key=key,use_container_width=True):
        st.query_params["stage"]=target; st.rerun()

def lines(col,value): col.markdown("\n".join(f"- {x}" for x in value))

def header(s):
    st.markdown(f"""<div class='hero'><small>PHASE {s['phase']+1} OF {len(bridge.PHASES)} · {bridge.PHASES[s['phase']]} &nbsp;·&nbsp; {s['step']}</small>
    <h1>🏗️ {s['title']}</h1><h3><span class='site'>On the site</span> → <span class='ai'>{s['ai']}</span></h3></div>""",unsafe_allow_html=True)
    if s.get("doing"):
        st.markdown(f"**What we are doing and why.** {s['doing']}")
    a,b,c=st.columns(3)
    with a.container(border=True):
        st.markdown("#### 1 · On the site"); lines(st,s["site"])
    with b.container(border=True):
        st.markdown("#### 2 · Why it is hard"); lines(st,s["challenge"])
    with c.container(border=True):
        st.markdown("#### 3 · Where AI helps"); lines(st,s["ai_link"])
    st.info(f"**In plain words.** {s['plain']}")
    glossary(s["id"])
    st.markdown(f"#### 4 · Interactive illustration — `{s['tech']}`")

GLOSSARY={
    "problem":[("Foundation","The part of a building that transfers its weight to the ground."),("Settlement","Downward movement of a building or its foundation."),("Differential settlement","One part moves down more than another part.")],
    "evidence":[("Borehole","A narrow hole used to inspect soil below the ground."),("Tested spot","A place where engineers have directly checked the soil."),("Computer-made map","A picture created from test results to estimate what may lie between tested spots.")],
    "tests":[("Soil resistance","How strongly the soil resists a test probe."),("Soft clay","A soil layer that can compress under weight.")],
    "model":[("Model","A computer method that learns patterns from examples."),("MAE","The typical prediction error, shown here in millimetres."),("R²","A score showing how well predictions follow measured values.")],
    "causes":[("Feature","One input given to the model."),("Importance","How much the model relied on an input. It does not prove a cause.")],
    "maps":[("Risk","How much settlement the model expects."),("Uncertainty","How unsure the estimate is."),("Evidence","Measurements that support an estimate.")],
    "next":[("Priority","A suggested order for further investigation."),("Investigation","A new test or inspection used to reduce uncertainty.")],
    "limits":[("Observed","Measured directly."),("Estimated","Calculated from data and a model."),("Unknown","Not available from the supplied information.")],
    "collection":[("Borehole","A narrow hole drilled so engineers can see the soil layers below the ground."),("CPT","A pointed rod is slowly pushed into the ground. Hard soil pushes back more. Soft soil pushes back less."),("SPT","A hammer pushes a small tube into the ground. Engineers count the blows. More blows usually mean harder soil.")],
    "cleaning":[("Missing value","A measurement that was not recorded."),("Duplicate","The same record appearing more than once."),("Unit","The scale used for a number, such as metres or millimetres.")],
    "training":[("Measured settlement","The actual downward movement recorded at a foundation location. It is the known answer used while training."),("Regression model","A model that predicts a number, such as settlement in millimetres."),("Decision tree","A model that reaches an answer by following a series of yes-or-no questions."),("Random sample","A smaller selection of training rows chosen by chance for one tree."),("Weight","A number Linear Regression learns to control how strongly one input changes its prediction."),("Bias","The starting value Linear Regression learns before adding the effects of its inputs."),("Feature scaling","Putting inputs with different units onto comparable number ranges. KNN needs this; Random Forest usually does not."),("Neighbour","In KNN, an earlier location with measurements similar to the new location."),("Nonlinear","A relationship that cannot be represented well by one straight line."),("Branch","One path through a decision tree. A yes-or-no answer decides which branch a row follows."),("Split rule","A yes-or-no question in a tree, such as: Is soft clay thicker than 5 metres?"),("Threshold","The dividing value in a split rule—for example, 5 metres."),("Squared error","A way to measure how far the tree's answers are from the measured settlements. A smaller value is better."),("Feature importance","An estimate of how much Random Forest used each input in its rules.")],
    "evaluation":[("Prediction error","The difference between predicted and measured movement."),("Risk","How much movement the model expects."),("Uncertainty","How unsure the estimate is.")],
}

def glossary(stage_id):
    terms=GLOSSARY.get(stage_id,[])
    if not terms: return
    st.markdown("##### 📘 Small glossary")
    cards="".join(f"<div class='term-card'><b>{term}</b><span>{meaning}</span></div>" for term,meaning in terms)
    st.markdown(f"<div class='glossary-grid'>{cards}</div>",unsafe_allow_html=True)

def limits_figure():
    fig=go.Figure()
    groups=["Directly observed","Estimated by model","Not known from these data"]
    values=[4,3,5]; colors=[story.GREEN,story.AMBER,story.RED]
    fig.add_trace(go.Bar(x=groups,y=values,marker_color=colors,text=["SPT/CPT, loads, sensors, groundwater","settlement map, uncertainty, test priority","hidden reinforcement, exact layers, future changes, safety"],
        hovertemplate="%{x}<br>%{text}<extra></extra>"))
    fig.update_yaxes(visible=False)
    return story.layout(fig,"The boundary of the system",440)

def collection_tables():
    st.markdown("#### Watch how the site data is collected")
    st.write("This short animation follows each measurement from the site into one dataset row.")
    st.video("assets/site-data-collection-explainer.webm",autoplay=False,muted=False)
    st.caption("🔊 Press play and check that the speaker icon in the video controls is not muted.")

    st.markdown("#### What data do engineers collect?")
    st.write("Each row belongs to one location on the site. Each column records one fact about that location.")
    dictionary=pd.DataFrame([
        ("East and north position","Where the test was carried out","metres","Site survey"),
        ("SPT result","Hammer blows needed to push the test tube into the soil. A low count usually means softer soil. A high count usually means harder soil.","blow count","SPT test"),
        ("CPT result","How strongly the soil pushed against the rod","MPa","CPT test"),
        ("Soft-clay thickness","How much soft clay was found","metres","Borehole/CPT"),
        ("Groundwater drop","How much the underground water level fell","metres","Water-level sensor"),
        ("Building load","Weight carried at that foundation location","kN","Structural calculation"),
        ("Foundation width","Width of the foundation","metres","Building drawing"),
        ("Measured settlement","How far the foundation moved downward","millimetres","Settlement sensor"),
    ],columns=["Information collected","What it means","Unit","Where it comes from"])
    st.dataframe(dictionary,use_container_width=True,hide_index=True)

    st.markdown("#### How does it look as a dataset?")
    sample=(df[["x_m","y_m","spt_n","cpt_qc_mpa","soft_clay_m","groundwater_drop_m",
                "column_load_kn","foundation_width_m","settlement_mm"]].head(6).round(2).rename(columns={
        "x_m":"East (m)","y_m":"North (m)","spt_n":"SPT blows","cpt_qc_mpa":"CPT resistance (MPa)",
        "soft_clay_m":"Soft clay (m)","groundwater_drop_m":"Water drop (m)",
        "column_load_kn":"Building load (kN)","foundation_width_m":"Foundation width (m)",
        "settlement_mm":"Downward movement (mm)"}))
    st.dataframe(sample,use_container_width=True,hide_index=True)
    st.caption("Example: one row = one tested or monitored location. The model learns from many rows like these.")

def cleaning_walkthrough():
    """Interactive overview and before/after cleaning demonstration."""
    selected=clean_column; label=CLEAN_COLUMNS[selected]
    base=df.head(120).copy(); dirty=pd.concat([base,base.iloc[[2,7,7]]],ignore_index=True)
    dirty.loc[[4,19,44],"spt_n"]=np.nan;dirty.loc[[8,31],"groundwater_drop_m"]=np.nan
    dirty.loc[16,selected]=np.nan
    normal_max=base[selected].max();dirty.loc[27,selected]=normal_max*4

    def centered(fig):
        left,middle,right=st.columns([.08,.84,.08])
        with middle: st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    def distribution(series,title,color="#54d2ff"):
        values=series.dropna().astype(float).to_numpy();xs=np.linspace(values.min(),values.max(),180)
        std=max(values.std(),1e-6);bw=max(1.06*std*(len(values)**(-.2)),std*.08)
        curve=np.exp(-.5*((xs[:,None]-values[None,:])/bw)**2).mean(axis=1)/(bw*np.sqrt(2*np.pi))
        fig=go.Figure()
        fig.add_trace(go.Histogram(x=values,nbinsx=24,histnorm="probability density",name="Histogram",marker_color=color,opacity=.72))
        fig.add_trace(go.Scatter(x=xs,y=curve,name="Smooth curve",line=dict(color="#ffbd59",width=4)))
        fig.update_layout(height=380,title=title,paper_bgcolor=story.BG,plot_bgcolor=story.PANEL,
            font=dict(color="#e6edf3"),margin=dict(l=40,r=25,t=65,b=45),xaxis_title=label,
            yaxis_title="Density",legend=dict(orientation="h",y=1.12,x=.5,xanchor="center"))
        return fig

    st.markdown("### The cleaning order")
    st.markdown("**1. Understand → 2. Remove duplicates → 3. Handle missing values → 4. Clip outliers**")
    st.markdown("#### Step 1 · Understand the dataset")
    st.code("df.head()\ndf.tail()\ndf.info()\ndf.describe()",language="python")
    head_tab,tail_tab,info_tab,describe_tab=st.tabs(["head()","tail()","info()","describe()"])
    shown=["x_m","y_m","spt_n","cpt_qc_mpa","soft_clay_m","groundwater_drop_m","settlement_mm"]
    with head_tab: st.dataframe(dirty[shown].head().round(2),use_container_width=True,hide_index=True)
    with tail_tab: st.dataframe(dirty[shown].tail().round(2),use_container_width=True,hide_index=True)
    with info_tab:
        info=pd.DataFrame({"Column":dirty.columns,"Type":[str(x) for x in dirty.dtypes],"Present":dirty.notna().sum().values,"Missing":dirty.isna().sum().values})
        st.dataframe(info,use_container_width=True,hide_index=True)
    with describe_tab: st.dataframe(dirty[shown].describe().T.round(2),use_container_width=True)

    st.markdown(f"#### Distribution of {label}")
    st.write("Choose another column from the left sidebar. Both the histogram and smooth curve will update.")
    centered(distribution(dirty[selected],f"{label} before cleaning"))

    st.markdown("#### Step 2 · Remove duplicates first")
    st.code("duplicates = df.duplicated().sum()\ndf = df.drop_duplicates()",language="python")
    duplicate_count=int(dirty.duplicated().sum());dedup=dirty.drop_duplicates().reset_index(drop=True)
    fig=go.Figure(go.Bar(x=["Before","After"],y=[len(dirty),len(dedup)],marker_color=["#ff6b6b","#5dd6a8"],text=[len(dirty),len(dedup)],textposition="outside"))
    fig.update_layout(height=320,title="Rows before and after duplicate removal",paper_bgcolor=story.BG,plot_bgcolor=story.PANEL,font=dict(color="#e6edf3"),yaxis_title="Rows",margin=dict(t=60,b=35))
    centered(fig);st.success(f"Removed {duplicate_count} repeated rows.")

    st.markdown("#### Step 3 · Handle missing values")
    st.code("median = df[column].median()\ndf[column] = df[column].fillna(median)",language="python")
    missing_before=int(dedup.isna().sum().sum());filled=dedup.copy()
    for col in filled.columns:
        if filled[col].isna().any(): filled[col]=filled[col].fillna(filled[col].median())
    fig=go.Figure(go.Bar(x=["Before","After"],y=[missing_before,int(filled.isna().sum().sum())],marker_color=["#ffbd59","#5dd6a8"],text=[missing_before,0],textposition="outside"))
    fig.update_layout(height=320,title="Missing values before and after filling",paper_bgcolor=story.BG,plot_bgcolor=story.PANEL,font=dict(color="#e6edf3"),yaxis_title="Missing values",margin=dict(t=60,b=35))
    centered(fig);st.info("The median is the middle value. It is less affected by one extremely large value.")

    st.markdown("#### Step 4 · Handle outliers with clipping")
    st.code(f'q1 = df["{selected}"].quantile(0.25)\nq3 = df["{selected}"].quantile(0.75)\niqr = q3 - q1\nlower = q1 - 1.5 * iqr\nupper = q3 + 1.5 * iqr\ndf["{selected}"] = df["{selected}"].clip(lower, upper)',language="python")
    q1,q3=filled[selected].quantile([.25,.75]);iqr=q3-q1;low,high=q1-1.5*iqr,q3+1.5*iqr
    flagged=(filled[selected]<low)|(filled[selected]>high);cleaned=filled.copy();cleaned[selected]=cleaned[selected].clip(low,high)
    st.write(f"**{int(flagged.sum())} value(s)** in {label} were outside the IQR limits and were clipped to the nearest limit.")
    before,after=st.columns(2)
    with before: st.plotly_chart(distribution(filled[selected],"Before clipping","#ff6b6b"),use_container_width=True,config={"displayModeBar":False})
    with after: st.plotly_chart(distribution(cleaned[selected],"After clipping","#5dd6a8"),use_container_width=True,config={"displayModeBar":False})
    st.warning("Clipping keeps the row but limits an extreme value. On a real project, an engineer checks the original measurement before applying it.")
    a,b,c=st.columns(3);a.metric("Starting rows",len(dirty));b.metric("Clean rows",len(cleaned));c.metric("Missing values left",int(cleaned.isna().sum().sum()))

@st.cache_data(show_spinner=False)
def compare_regressors(data):
    X=data[story.FEATURES];y=data["settlement_mm"]
    X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=.25,random_state=42)
    candidates={
        "Median baseline":DummyRegressor(strategy="median"),
        "Linear regression":LinearRegression(),
        "KNN regressor":make_pipeline(StandardScaler(),KNeighborsRegressor(n_neighbors=7,weights="distance")),
        "Decision tree":DecisionTreeRegressor(max_depth=7,min_samples_leaf=4,random_state=42),
        "Random Forest":RandomForestRegressor(n_estimators=200,min_samples_leaf=4,max_features=.8,random_state=42,n_jobs=1),
    }
    rows=[]
    for name,candidate in candidates.items():
        candidate.fit(X_train,y_train);prediction=candidate.predict(X_test)
        rows.append((name,mean_absolute_error(y_test,prediction),r2_score(y_test,prediction)))
    return pd.DataFrame(rows,columns=["Model","MAE (mm)","R²"]).round(3)

def random_forest_flow_figure():
    fig=go.Figure()
    tree_x=[1.3,3.8,6.2,8.7]
    rules=["Soft clay<br>&gt; 3.6 m?","SPT result<br>&lt; 12?","Building load<br>&gt; 1,500 kN?","Water drop<br>&gt; 1.2 m?"]
    answers=["15 mm","17 mm","14 mm","16 mm"]
    # Arrows are drawn behind the flowchart shapes.
    for tx in tree_x:
        fig.add_annotation(x=tx,y=7.9,ax=5,ay=9.15,xref="x",yref="y",axref="x",ayref="y",
            text="",showarrow=True,arrowhead=3,arrowsize=1.1,arrowwidth=2,arrowcolor="#60788e")
        fig.add_annotation(x=tx,y=5.85,ax=tx,ay=6.65,xref="x",yref="y",axref="x",ayref="y",
            text="",showarrow=True,arrowhead=3,arrowsize=1.1,arrowwidth=2,arrowcolor="#ffbd59")
        fig.add_annotation(x=5,y=4.25,ax=tx,ay=5.0,xref="x",yref="y",axref="x",ayref="y",
            text="",showarrow=True,arrowhead=3,arrowsize=1.1,arrowwidth=2,arrowcolor="#60788e")
    fig.add_annotation(x=5,y=1.55,ax=5,ay=2.55,xref="x",yref="y",axref="x",ayref="y",
        text="",showarrow=True,arrowhead=3,arrowsize=1.2,arrowwidth=3,arrowcolor="#54d2ff")

    fig.add_shape(type="rect",x0=3.25,x1=6.75,y0=9.05,y1=10.45,line=dict(color="#54d2ff",width=2),fillcolor="#173244")
    fig.add_annotation(x=5,y=9.75,text="<b>CLEANED SITE DATA</b><br>soil · water · load<br>measured settlement",showarrow=False,font=dict(color="#eaf2f8",size=15),align="center")
    for i,(tx,rule,answer) in enumerate(zip(tree_x,rules,answers),1):
        fig.add_shape(type="path",path=f"M {tx} 7.9 L {tx+1.0} 7.25 L {tx} 6.6 L {tx-1.0} 7.25 Z",
            line=dict(color="#ffbd59",width=2),fillcolor="#2b291d")
        fig.add_annotation(x=tx,y=7.25,text=f"<b>TREE {i}</b><br>{rule}",showarrow=False,font=dict(color="#eaf2f8",size=12),align="center")
        fig.add_annotation(x=tx+.16,y=6.25,text="YES",showarrow=False,font=dict(color="#ffbd59",size=11))
        fig.add_shape(type="rect",x0=tx-.72,x1=tx+.72,y0=5.0,y1=5.85,line=dict(color="#5dd6a8",width=2),fillcolor="#173228")
        fig.add_annotation(x=tx,y=5.43,text=f"ANSWER<br><b>{answer}</b>",showarrow=False,font=dict(color="#eaf2f8",size=12),align="center")
    fig.add_annotation(x=.12,y=8.7,text="Different sample + inputs<br>for every tree",showarrow=False,xanchor="left",font=dict(color="#91a4b7",size=13),align="left")
    fig.add_annotation(x=9.85,y=6.35,text="A real tree repeats<br>several splits",showarrow=False,xanchor="right",font=dict(color="#91a4b7",size=13),align="right")
    fig.add_shape(type="path",path="M 5 4.25 L 6.25 3.4 L 5 2.55 L 3.75 3.4 Z",line=dict(color="#5dd6a8",width=2),fillcolor="#173228")
    fig.add_annotation(x=5,y=3.4,text="<b>AVERAGE</b><br>the four answers",showarrow=False,font=dict(color="#eaf2f8",size=14),align="center")
    fig.add_shape(type="rect",x0=3.6,x1=6.4,y0=.25,y1=1.55,line=dict(color="#54d2ff",width=3),fillcolor="#173244")
    fig.add_annotation(x=5,y=.9,text="<b>FINAL OUTPUT</b><br>Predicted settlement<br><b>15.5 mm</b>",showarrow=False,font=dict(color="#eaf2f8",size=15),align="center")
    fig.update_xaxes(range=[0,10],visible=False);fig.update_yaxes(range=[0,10.6],visible=False)
    fig.update_layout(height=720,paper_bgcolor=story.BG,plot_bgcolor=story.BG,margin=dict(l=15,r=15,t=15,b=15),showlegend=False)
    return fig

def split_example_figure(data):
    feature="soft_clay_m";label="Soft-clay thickness";unit="m"
    values=data[[feature,"settlement_mm"]].dropna().sort_values(feature)
    x=values[feature].to_numpy();y=values["settlement_mm"].to_numpy()
    candidates=(x[:-1]+x[1:])/2
    best=None
    for threshold in np.unique(candidates):
        left=y[x<=threshold];right=y[x>threshold]
        if len(left)<12 or len(right)<12: continue
        error=((left-left.mean())**2).sum()+((right-right.mean())**2).sum()
        if best is None or error<best[0]: best=(error,threshold,left.mean(),right.mean(),len(left),len(right))
    _,threshold,left_mean,right_mean,left_n,right_n=best
    side=np.where(x<=threshold,"Left group","Right group")
    fig=go.Figure()
    for group,color in [("Left group","#54d2ff"),("Right group","#ffbd59")]:
        keep=side==group
        fig.add_trace(go.Scatter(x=x[keep],y=y[keep],mode="markers",name=group,
            marker=dict(color=color,size=7,opacity=.58),hovertemplate=f"{label}: %{{x:.2f}} {unit}<br>Measured settlement: %{{y:.2f}} mm<extra></extra>"))
    fig.add_vline(x=threshold,line_width=3,line_dash="dash",line_color="#eaf2f8",
        annotation_text=f"Chosen threshold: {threshold:.2f} {unit}",annotation_position="top")
    fig.add_shape(type="line",x0=x.min(),x1=threshold,y0=left_mean,y1=left_mean,line=dict(color="#54d2ff",width=4))
    fig.add_shape(type="line",x0=threshold,x1=x.max(),y0=right_mean,y1=right_mean,line=dict(color="#ffbd59",width=4))
    fig.add_annotation(x=(x.min()+threshold)/2,y=left_mean,text=f"Left answer: {left_mean:.1f} mm<br>{left_n} rows",showarrow=False,
        bgcolor="#173244",bordercolor="#54d2ff",font=dict(color="#eaf2f8",size=13))
    fig.add_annotation(x=(threshold+x.max())/2,y=right_mean,text=f"Right answer: {right_mean:.1f} mm<br>{right_n} rows",showarrow=False,
        bgcolor="#2b291d",bordercolor="#ffbd59",font=dict(color="#eaf2f8",size=13))
    fig.update_layout(height=470,title="Example: testing one split using soft-clay thickness",paper_bgcolor=story.BG,
        plot_bgcolor=story.PANEL,font=dict(color="#e6edf3"),xaxis_title=f"{label} ({unit})",yaxis_title="Measured settlement (mm)",
        legend=dict(orientation="h",y=1.09,x=.5,xanchor="center"),margin=dict(t=90,b=55,l=60,r=25))
    return fig,threshold

def model_choice_content():
    st.markdown("### What is Random Forest?")
    st.write("A **Random Forest Regressor** is a machine-learning model that combines many decision trees to predict a number. Here, the number is how many millimetres a foundation may move downward. Each tree produces an estimate, and the forest averages the estimates to give one final prediction.")
    st.markdown("#### How it works — step by step")
    st.markdown("""
1. Give the model cleaned examples containing soil, water, building-load and measured-settlement values.
2. Create many random samples from those examples. Each decision tree learns from a slightly different sample and selection of inputs.
3. Each tree learns yes-or-no split rules, such as **“Is the soft clay thicker than 5 metres?”**
4. The new location passes through every tree, and each tree produces its own settlement estimate.
5. Average all tree estimates to produce the final predicted settlement.
""")
    st.markdown("#### How does a tree choose a split?")
    st.markdown("""
1. The tree starts with records from places engineers have already measured.
2. It asks a simple **Yes or No** question. Example: **“Is the soft clay 5 metres thick or less?”**
3. If the answer is **Yes**, that record moves to the **left side of the tree**.
4. If the answer is **No**, the soft clay is more than 5 metres thick, so that record moves to the **right side of the tree**.
5. The tree finds the average downward movement on each side. That average becomes the answer for that side.
6. The tree tries many different questions. It keeps the question that gives answers closest to the movements engineers actually measured.
7. It asks more Yes-or-No questions farther down the tree until another question would no longer make the answers better.
""")
    st.markdown("#### Random Forest flowchart")
    st.plotly_chart(random_forest_flow_figure(),use_container_width=True,config={"displayModeBar":False})
    st.markdown("#### Watch the same process")
    st.video("assets/random-forest-internal.mp4",autoplay=False,muted=False)
    st.caption("The animation follows one cleaned row through several decision trees and then averages their predictions.")

    st.markdown("### Why was Random Forest chosen?")
    st.write("We considered four regression models:")
    st.markdown("""
- **Linear Regression** learns one weight for each input and one bias. It is easy to explain, but it expects the relationship to be close to a straight line.
- **KNN Regressor** finds locations with similar measurements and averages their settlement. It can learn curves, but its answer is sensitive to feature scaling and the choice of neighbours.
- **Decision Tree Regressor** learns clear yes-or-no rules. It captures nonlinear patterns, but one tree can memorize the training data and change greatly when the data changes.
- **Random Forest Regressor** builds many varied decision trees and averages their answers. This keeps the nonlinear learning of a tree while making the final prediction more stable.
""")
    st.markdown("#### What does Random Forest learn?")
    st.write("Random Forest does **not** learn weights and a bias. Each tree learns **split rules** and **thresholds**. The rules lead to one settlement estimate from each tree. The forest averages those estimates. **Feature importance** summarizes which inputs were used most across the rules.")
    st.success("**Selected model: Random Forest Regressor.** Settlement may depend on nonlinear combinations of soil, water and load. Using many trees is also more stable than relying on one decision tree.")
    st.info("No model is automatically best for every real site, so we still compare their errors on unseen test data.")
    st.markdown("#### Compare it with simpler models")
    comparison=compare_regressors(df)
    st.dataframe(comparison,use_container_width=True,hide_index=True)
    chart=go.Figure(go.Bar(x=comparison["Model"],y=comparison["MAE (mm)"],
        marker_color=["#9bb0c2","#ffbd59","#54d2ff","#ff8a65","#5dd6a8"],text=comparison["MAE (mm)"],textposition="outside"))
    chart.update_layout(height=340,title="Lower prediction error is better",paper_bgcolor=story.BG,
        plot_bgcolor=story.PANEL,font=dict(color="#e6edf3"),yaxis_title="Mean absolute error (mm)",margin=dict(t=60,b=35))
    left,middle,right=st.columns([.1,.8,.1])
    with middle: st.plotly_chart(chart,use_container_width=True,config={"displayModeBar":False})

    st.markdown("#### Scikit-learn code")
    st.code('''from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

X = df[FEATURES]                 # soil, water, load and location columns
y = df["settlement_mm"]         # value the model must predict

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)

model = RandomForestRegressor(
    n_estimators=200,             # build 200 decision trees
    min_samples_leaf=4,           # avoid very specific rules
    max_features=0.8,             # each tree sees a different set of clues
    random_state=42
)

model.fit(X_train, y_train)
predictions = model.predict(X_test)

print("MAE:", mean_absolute_error(y_test, predictions))
print("R²:", r2_score(y_test, predictions))''',language="python")

def draw(s):
    if s["id"]=="collection": return story.soil_map(df,boreholes)
    if s["id"]=="cleaning": return story.cleaning_figure()
    if s["id"]=="training": return story.importance(model)
    if s["id"]=="evaluation": return story.model_check(test,metrics)
    if s["id"]=="problem": return story.foundation_cutaway()
    if s["id"]=="evidence": return story.soil_map(df,boreholes)
    if s["id"]=="tests": return story.borehole_view(df,boreholes)
    if s["id"]=="model": return story.model_check(test,metrics)
    if s["id"]=="causes": return story.importance(model)
    if s["id"]=="maps": return story.risk_maps(grid,xx,yy,boreholes)
    if s["id"]=="next": return story.investigation_map(grid,xx,yy,boreholes)[0]
    return limits_figure()

def footer(s):
    st.markdown("#### 5 · What the picture shows"); st.write(s["figure"])
    st.warning(f"**What to look for.** {s['watch']}")
    st.success(f"**Takeaway:** {s['takeaway']}")
    i=bridge.ORDER.index(s["id"]); a,b,c=st.columns(3)
    if i: goto(bridge.ORDER[i-1],f"◀ {bridge.STEPS[i-1]['title']}",f"prev_{s['id']}",a)
    goto("start","Overview",f"home_{s['id']}",b)
    if i<len(bridge.ORDER)-1: goto(bridge.ORDER[i+1],f"{bridge.STEPS[i+1]['title']} ▶",f"next_{s['id']}",c)

def start_page():
    st.markdown("""<div class='hero'>
    <small>INTERACTIVE ENGINEERING LAB</small>
    <div class='hero-top'>
      <div class='hero-icon'>⌁</div>
      <div class='hero-copy'>
        <h1>Foundation Settlement AI</h1>
        <p>A visual guide to uneven ground movement.</p>
      </div>
    </div>
    <div class='outcome-row'>
      <div class='outcome-chip'><span>01</span><b>Find</b> where sinking may occur</div>
      <div class='flow-arrow'>→</div>
      <div class='outcome-chip result'><span>02</span><b>Decide</b> what to inspect next</div>
    </div>
    </div>""",unsafe_allow_html=True)
    st.markdown("## The problem")
    st.markdown("""<div class='problem-card'>
    A building stands on the ground through its foundation.<br><br>
    Some areas of the ground may be strong. Other areas may be soft.<br><br>
    The soft ground can sink more under the building's weight. This can make one side of the building move lower than the other.<br><br>
    <b>As a result:</b><br>
    • Walls may crack.<br>
    • Floors may become uneven.<br>
    • Doors and windows may stop closing properly.<br><br>
    Engineers cannot easily see the soil below a building. They can test it only at selected locations, so a soft area may be missed.<br><br>
    This project combines available soil tests and building measurements. It helps engineers find possible problem areas and decide where another inspection or soil test may be needed.
    </div>""",unsafe_allow_html=True)
    glossary("problem")
    st.plotly_chart(story.foundation_cutaway(),use_container_width=True,config={"displayModeBar":False})
    st.warning("**Look at the arrow.** The right side stands on soft clay. It sinks more. Unequal movement can create the crack shown above.")
    st.info("Use **Project stages** on the left to continue.")

if stage=="start": start_page()
elif stage in bridge.BY_ID:
    page=bridge.BY_ID[stage]; header(page)
    if stage in ("model","evaluation"):
        a,b=st.columns(2); a.metric("Typical error (MAE)",f"{metrics['mae']:.2f} mm"); b.metric("R²",f"{metrics['r2']:.2f}")
    if stage=="training":
        model_choice_content()
    st.plotly_chart(draw(page),use_container_width=True,config={"displayModeBar":False})
    if stage=="collection":
        collection_tables()
    if stage=="cleaning":
        cleaning_walkthrough()
    if stage=="evaluation":
        st.markdown("#### Prediction and uncertainty maps")
        st.plotly_chart(story.risk_maps(grid,xx,yy,boreholes),use_container_width=True,config={"displayModeBar":False})
        st.info("**Final engineering check:** review the original measurements, inspect the marked location and collect another soil test when evidence is weak.")
    if stage=="next":
        _,top=story.investigation_map(grid,xx,yy,boreholes)
        st.dataframe(top[["x_m","y_m","prediction","uncertainty","priority"]].round(2).rename(columns={"x_m":"East (m)","y_m":"North (m)","prediction":"Predicted mm","uncertainty":"Uncertainty","priority":"Test priority"}),use_container_width=True,hide_index=True)
    footer(page)
else:
    st.error("Unknown illustration step."); goto("start","Return to overview","bad_stage")
