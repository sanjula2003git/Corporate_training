import numpy as np
import plotly.graph_objects as go
BG="#0e1117";CYAN="#4fc3f7";AMBER="#ffb74d";RED="#ef5350";GREEN="#66bb6a";VIOLET="#ba68c8"
def waveform(rpm=1800,torque=42,wear=.55,resonance=.7,seed=4,n=1000):
 rng=np.random.default_rng(seed);t=np.linspace(0,.5,n);shaft=rpm/60;mesh=shaft*12;amp=.7+1.5*wear+1.8*resonance+torque/90
 x=amp*np.sin(2*np.pi*shaft*t)+.32*amp*np.sin(2*np.pi*mesh*t)+.18*amp*np.sin(2*np.pi*(mesh-shaft)*t)
 impacts=(rng.random(n)<wear*.018)*rng.normal(0,3*amp,n);x+=np.convolve(impacts,np.exp(-np.arange(20)/5),mode="same")+.12*rng.normal(size=n);return t,x
def future(rpm,torque,current,temp,wear,resonance):return float(max(.5,current+.0008*torque*rpm/10+.028*(temp-50)+2.2*wear+2.4*resonance-3.0))
def wavefig(rpm,torque,wear,resonance):
 t,x=waveform(rpm,torque,wear,resonance);fig=go.Figure(go.Scatter(x=t,y=x,line=dict(color=CYAN,width=1)));fig.update_layout(height=390,paper_bgcolor=BG,plot_bgcolor=BG,font_color="white",xaxis_title="Time (s)",yaxis_title="Vibration signal");return fig
def trajectories(current,pred,threshold=7):
 t=np.arange(31);no=current+(pred-current)*(t/30)**1.35;action=no.copy();action[8:]-=np.linspace(0,max(0,pred-6.2),23);fig=go.Figure();fig.add_scatter(x=t,y=no,name="Without early response",line=dict(color=RED,width=4));fig.add_scatter(x=t,y=action,name="With simulated speed reduction",line=dict(color=GREEN,width=4));fig.add_hline(y=threshold,line_dash="dash",line_color=AMBER);fig.update_layout(height=410,paper_bgcolor=BG,plot_bgcolor=BG,font_color="white",xaxis_title="Seconds",yaxis_title="Vibration (mm/s)");return fig,no,action

