"""Virtual geotechnical site, model, and Plotly illustrations."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

BG, PANEL = "#0e1117", "#161b22"
CYAN, AMBER, RED, GREEN, GREY = "#4fc3f7", "#ffb74d", "#ef5350", "#66bb6a", "#8b949e"
FEATURES = ["x_m","y_m","spt_n","cpt_qc_mpa","soft_clay_m","groundwater_drop_m",
            "column_load_kn","foundation_width_m","pressure_kpa","distance_to_borehole_m"]

def build_site(softness=7.0, groundwater_drop=1.2, load_scale=1.0, seed=42):
    rng = np.random.default_rng(seed)
    n = 850
    x, y = rng.uniform(0,100,n), rng.uniform(0,80,n)
    zone = np.exp(-(((x-74)/22)**2 + ((y-21)/17)**2))
    clay = np.clip(1 + softness*zone + rng.normal(0,.7,n), 0, 12)
    spt = np.clip(33 - (3.1*softness)*zone + rng.normal(0,3,n), 2, 55)
    cpt = np.clip(11.5 - (1.05*softness)*zone + rng.normal(0,1,n), .6, 22)
    gw_drop = np.clip(rng.gamma(1.5,.3,n) + groundwater_drop*zone, 0, 4)
    load = rng.uniform(550,2500,n)*load_scale
    width = rng.uniform(1.5,3.8,n)
    pressure = load/width**2
    boreholes = np.array([[8,8],[18,65],[48,38],[88,68],[92,12],[60,72]])
    distance = np.min(np.hypot(x[:,None]-boreholes[:,0], y[:,None]-boreholes[:,1]),axis=1)
    settlement = np.clip(1.5 + .55*clay + .009*pressure + 1.3*gw_drop +
                         .12*(35-spt).clip(0) + 4.8*zone + rng.normal(0,1.5,n),0,None)
    df = pd.DataFrame(dict(x_m=x,y_m=y,spt_n=spt,cpt_qc_mpa=cpt,soft_clay_m=clay,
        groundwater_drop_m=gw_drop,column_load_kn=load,foundation_width_m=width,
        pressure_kpa=pressure,distance_to_borehole_m=distance,settlement_mm=settlement))
    return df, boreholes

def train_model(df):
    rng=np.random.default_rng(7); order=rng.permutation(len(df)); cut=int(.75*len(df))
    tr, te=df.iloc[order[:cut]],df.iloc[order[cut:]]
    m=RandomForestRegressor(n_estimators=120,min_samples_leaf=4,max_features=.8,n_jobs=1,random_state=7)
    m.fit(tr[FEATURES],tr.settlement_mm)
    p=m.predict(te[FEATURES])
    metrics={"mae":mean_absolute_error(te.settlement_mm,p),"r2":r2_score(te.settlement_mm,p)}
    return m,te.assign(predicted_mm=p),metrics

def layout(fig,title,height=520):
    fig.update_layout(title=title,height=height,paper_bgcolor=BG,plot_bgcolor=PANEL,
        font=dict(color="#e6edf3"),margin=dict(l=35,r=25,t=65,b=35),legend=dict(orientation="h"))
    return fig

def foundation_cutaway():
    fig=go.Figure()
    fig.add_shape(type="rect",x0=0,x1=50,y0=0,y1=3,fillcolor="#7a6348",line_width=0)
    fig.add_shape(type="rect",x0=50,x1=100,y0=0,y1=3,fillcolor="#d87545",line_width=0)
    fig.add_shape(type="rect",x0=0,x1=100,y0=0,y1=.45,fillcolor="#3187b8",line_width=0)
    fig.add_trace(go.Scatter(x=[10,50,50,90,90,10,10],y=[3,3,2.55,2.55,2.9,3.35,3],
        fill="toself",fillcolor="#6f7f8c",line=dict(color="#c7d1d9"),name="Foundation"))
    for x0,y0,lean in [(14,3.3,0),(43,3.3,0),(58,3.0,1),(84,2.7,2)]:
        fig.add_trace(go.Scatter(x=[x0,x0+4,x0+4+lean,x0+lean,x0],y=[y0,y0,y0+6,y0+6,y0],
            fill="toself",fillcolor="#8998a5",line=dict(color="#c7d1d9"),showlegend=False))
    fig.add_trace(go.Scatter(x=[12,88],y=[9.3,9.3],line=dict(color="#c7d1d9",width=12),name="Building"))
    fig.add_trace(go.Scatter(x=[67,70,68,72],y=[8.2,7,6,4.7],line=dict(color=RED,width=4),name="Crack"))
    fig.add_annotation(x=25,y=1.5,text="Strong soil",showarrow=False,font=dict(size=18))
    fig.add_annotation(x=75,y=1.5,text="Soft clay",showarrow=False,font=dict(size=18,color="white"))
    fig.add_annotation(x=82,y=3.2,text="This side sinks more",showarrow=True,ax=-55,ay=-55)
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False,range=[0,11])
    return layout(fig,"A building behaves like a table with one leg on soft ground")

def soil_map(df,boreholes):
    # Use fewer, larger dots here. The lesson is the location of the weak area,
    # not the number of simulated observations.
    shown=df.iloc[::2].copy()
    fig=make_subplots(rows=1,cols=2,horizontal_spacing=.12,
        subplot_titles=("Soft-soil depth<br><span style='font-size:13px;color:#9bb0c2'>Light = thin · Orange = thick</span>",
                        "Downward movement<br><span style='font-size:13px;color:#9bb0c2'>Green = small · Red = large</span>"))
    fig.add_trace(go.Scatter(x=shown.x_m,y=shown.y_m,mode="markers",marker=dict(
        size=8,color=shown.soft_clay_m,colorscale=[[0,"#fff2b2"],[.45,"#ffb347"],[1,"#b63b16"]],
        opacity=.9,showscale=False),
        text=shown.soft_clay_m.round(1),hovertemplate="Soft clay: %{text} m<extra></extra>"),1,1)
    fig.add_trace(go.Scatter(x=shown.x_m,y=shown.y_m,mode="markers",marker=dict(
        size=8,color=shown.settlement_mm,colorscale=[[0,"#48b978"],[.5,"#ffd166"],[1,"#e84a4a"]],
        opacity=.9,showscale=False),
        text=shown.settlement_mm.round(1),hovertemplate="Downward movement: %{text} mm<extra></extra>"),1,2)
    for c in (1,2):
        fig.add_trace(go.Scatter(x=boreholes[:,0],y=boreholes[:,1],mode="markers",marker=dict(
            symbol="star",size=15,color=CYAN,line=dict(color="white",width=1.5)),name="Soil test location",
            showlegend=False,hovertemplate="Soil test location<extra></extra>"),1,c)
    # The same dashed circle appears on both maps, so the learner can connect
    # the suspected cause on the left with the observed result on the right.
    fig.add_shape(type="circle",x0=57,x1=91,y0=4,y1=38,xref="x",yref="y",
                  line=dict(color=RED,width=3,dash="dash"))
    fig.add_shape(type="circle",x0=57,x1=91,y0=4,y1=38,xref="x2",yref="y2",
                  line=dict(color=RED,width=3,dash="dash"))
    fig.add_annotation(x=74,y=21,xref="x",yref="y",text="Soft soil is<br>thickest here",showarrow=True,
        ax=-75,ay=-75,arrowcolor=RED,arrowwidth=3,bgcolor="#172432",bordercolor=RED,borderpad=7,font=dict(color="white",size=13))
    fig.add_annotation(x=74,y=21,xref="x2",yref="y2",text="The same area<br>sank more",showarrow=True,
        ax=72,ay=-75,arrowcolor=RED,arrowwidth=3,bgcolor="#172432",bordercolor=RED,borderpad=7,font=dict(color="white",size=13))
    fig.update_xaxes(title="Position from west to east (m)",range=[0,100],showgrid=False)
    fig.update_yaxes(title="Position from south to north (m)",range=[0,80],showgrid=True,gridcolor="rgba(255,255,255,.08)")
    fig.update_layout(height=610,paper_bgcolor=BG,plot_bgcolor=PANEL,font=dict(color="#e6edf3"),
                      showlegend=False,margin=dict(l=45,r=30,t=72,b=55))
    return fig

def borehole_view(df,boreholes):
    nearest=[]
    for i,(bx,by) in enumerate(boreholes):
        row=df.iloc[np.argmin(np.hypot(df.x_m-bx,df.y_m-by))]
        nearest.append((f"BH-{i+1}",row.spt_n,row.cpt_qc_mpa,row.soft_clay_m))
    b=pd.DataFrame(nearest,columns=["hole","SPT N","CPT qc","soft clay"])
    fig=make_subplots(rows=1,cols=3,subplot_titles=("SPT resistance","CPT resistance","Soft clay"))
    for c,(col,color) in enumerate([("SPT N",CYAN),("CPT qc",GREEN),("soft clay",AMBER)],1):
        fig.add_trace(go.Bar(x=b.hole,y=b[col],marker_color=color,text=b[col].round(1),textposition="outside",showlegend=False),1,c)
    return layout(fig,"Six narrow tests cannot reveal every pocket between them",470)

def cleaning_figure():
    """Before/after illustration of common data checks."""
    labels=["Empty records","Repeated records","Wrong units","Sensor errors"]
    before=[38,24,17,31]
    after=[3,0,1,6]
    fig=make_subplots(rows=1,cols=2,subplot_titles=("Before cleaning","After cleaning"),horizontal_spacing=.16)
    fig.add_trace(go.Bar(x=labels,y=before,marker_color=RED,text=before,textposition="outside",showlegend=False),1,1)
    fig.add_trace(go.Bar(x=labels,y=after,marker_color=GREEN,text=after,textposition="outside",showlegend=False),1,2)
    fig.add_annotation(x="Sensor errors",y=6,xref="x2",yref="y2",
        text="Kept for review:<br>this may be a real warning",showarrow=True,ax=-70,ay=-70,
        arrowcolor=AMBER,arrowwidth=3,bgcolor=PANEL,bordercolor=AMBER,borderpad=6)
    fig.update_xaxes(tickangle=-18)
    fig.update_yaxes(title="Records needing attention",range=[0,45],gridcolor="rgba(255,255,255,.08)")
    return layout(fig,"Cleaning removes data errors—not real engineering warnings",500)

def model_check(test,metrics):
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=test.settlement_mm,y=test.predicted_mm,mode="markers",
        marker=dict(color=CYAN,opacity=.65),text=test.distance_to_borehole_m.round(1),
        hovertemplate="Measured %{x:.1f} mm<br>Predicted %{y:.1f} mm<br>Nearest borehole %{text} m<extra></extra>"))
    lim=max(test.settlement_mm.max(),test.predicted_mm.max())
    fig.add_trace(go.Scatter(x=[0,lim],y=[0,lim],mode="lines",line=dict(dash="dash",color=RED),name="Perfect"))
    fig.add_annotation(x=.03,y=.96,xref="paper",yref="paper",showarrow=False,align="left",
        text=f"MAE: {metrics['mae']:.2f} mm<br>R²: {metrics['r2']:.2f}",bgcolor=PANEL)
    fig.update_xaxes(title="Measured settlement (mm)"); fig.update_yaxes(title="AI prediction (mm)")
    return layout(fig,"Test the model on locations it did not learn from")

def importance(model):
    s=pd.Series(model.feature_importances_,index=FEATURES).sort_values()
    fig=go.Figure(go.Bar(x=s,y=s.index,orientation="h",marker_color=GREEN,
                         hovertemplate="%{y}<br>importance %{x:.3f}<extra></extra>"))
    fig.update_xaxes(title="Model importance")
    return layout(fig,"Which clues the forest used most",520)

def risk_grid(model,boreholes,softness,groundwater_drop,load_scale):
    xx,yy=np.meshgrid(np.linspace(0,100,51),np.linspace(0,80,41)); x,y=xx.ravel(),yy.ravel()
    zone=np.exp(-(((x-74)/22)**2+((y-21)/17)**2)); clay=1+softness*zone
    spt=np.clip(33-3.1*softness*zone,2,55); cpt=np.clip(11.5-1.05*softness*zone,.6,22)
    load=np.full(len(x),1700*load_scale); width=np.full(len(x),2.4)
    dist=np.min(np.hypot(x[:,None]-boreholes[:,0],y[:,None]-boreholes[:,1]),axis=1)
    g=pd.DataFrame(dict(x_m=x,y_m=y,spt_n=spt,cpt_qc_mpa=cpt,soft_clay_m=clay,
        groundwater_drop_m=.45+groundwater_drop*zone,column_load_kn=load,foundation_width_m=width,
        pressure_kpa=load/width**2,distance_to_borehole_m=dist))
    g["prediction"]=model.predict(g[FEATURES])
    trees=np.vstack([t.predict(g[FEATURES].to_numpy()) for t in model.estimators_])
    g["uncertainty"]=.55*np.clip(trees.std(0)/2.5,0,1)+.45*np.clip(dist/35,0,1)
    return g,xx,yy

def risk_maps(grid,xx,yy,boreholes):
    fig=make_subplots(rows=1,cols=2,subplot_titles=("Predicted settlement risk","Uncertainty / missing evidence"))
    fig.add_trace(go.Contour(x=xx[0],y=yy[:,0],z=grid.prediction.to_numpy().reshape(xx.shape),colorscale="RdYlGn_r",colorbar=dict(title="mm",x=.43),hovertemplate="%{z:.1f} mm<extra></extra>"),1,1)
    fig.add_trace(go.Contour(x=xx[0],y=yy[:,0],z=grid.uncertainty.to_numpy().reshape(xx.shape),colorscale="Magma_r",colorbar=dict(title="uncertainty"),hovertemplate="%{z:.2f}<extra></extra>"),1,2)
    for c in (1,2):
        fig.add_trace(go.Scatter(x=boreholes[:,0],y=boreholes[:,1],mode="markers",marker=dict(symbol="star",size=13,color=CYAN,line=dict(color="white",width=1)),name="Boreholes",showlegend=(c==1)),1,c)
    risky=grid.loc[grid.prediction.idxmax()]
    uncertain=grid.loc[grid.uncertainty.idxmax()]
    fig.add_annotation(x=risky.x_m,y=risky.y_m,xref="x",yref="y",text="WHAT IS WRONG:<br>largest predicted sinking",showarrow=True,ax=-85,ay=-75,arrowcolor=RED,arrowwidth=3,bgcolor=PANEL,font=dict(color="white"))
    fig.add_annotation(x=uncertain.x_m,y=uncertain.y_m,xref="x2",yref="y2",text="WHAT IS MISSING:<br>not enough nearby evidence",showarrow=True,ax=-75,ay=-75,arrowcolor=AMBER,arrowwidth=3,bgcolor=PANEL,font=dict(color="white"))
    fig.update_xaxes(title="East (m)"); fig.update_yaxes(title="North (m)")
    return layout(fig,"Risk and confidence are different questions",570)

def investigation_map(grid,xx,yy,boreholes):
    score=(grid.prediction/grid.prediction.quantile(.95)).clip(0,1)*.6+grid.uncertainty*.4
    top=grid.assign(priority=score).nlargest(5,"priority")
    fig=go.Figure(go.Contour(x=xx[0],y=yy[:,0],z=score.to_numpy().reshape(xx.shape),colorscale="YlOrRd",colorbar=dict(title="priority")))
    fig.add_trace(go.Scatter(x=top.x_m,y=top.y_m,mode="markers+text",text=[f"Test {i}" for i in range(1,6)],textposition="top center",marker=dict(size=16,color=CYAN,line=dict(color="white",width=2)),name="Suggested tests"))
    fig.add_trace(go.Scatter(x=boreholes[:,0],y=boreholes[:,1],mode="markers",marker=dict(symbol="star",size=12,color="white"),name="Existing boreholes"))
    fig.update_xaxes(title="East (m)"); fig.update_yaxes(title="North (m)")
    return layout(fig,"Where one more test would be most useful",550),top
