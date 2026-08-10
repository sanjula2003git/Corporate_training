import io, wave
import numpy as np
import plotly.graph_objects as go
BG="#0e1117"; AMBER="#ffb74d"; CYAN="#4fc3f7"; VIOLET="#ba68c8"; GREEN="#66bb6a"; RED="#ef5350"

def synth_audio(severity=0.0,duration=4,sr=8000,seed=7):
 rng=np.random.default_rng(seed); t=np.arange(int(sr*duration))/sr
 x=.32*np.sin(2*np.pi*120*t)+.16*np.sin(2*np.pi*240*t)+.07*np.sin(2*np.pi*360*t)
 x+=.025*rng.normal(size=len(t))
 impulses=rng.random(len(t)) < severity*.006
 crack=np.convolve(impulses*rng.normal(0,1,len(t)),np.exp(-np.arange(70)/13),mode="same")
 x+=severity*(.18*rng.normal(size=len(t))+.8*crack)
 x/=max(1e-9,np.max(np.abs(x))); return t,x,sr

def wav_bytes(x,sr):
 b=io.BytesIO()
 with wave.open(b,"wb") as w:
  w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((x*32767).astype("<i2").tobytes())
 return b.getvalue()

def waveform(t,x):
 fig=go.Figure(go.Scatter(x=t[::8],y=x[::8],line=dict(color=CYAN,width=1)))
 fig.update_layout(height=280,paper_bgcolor=BG,plot_bgcolor=BG,font_color="white",xaxis_title="Time (s)",yaxis_title="Normalized amplitude",margin=dict(l=40,r=10,t=15,b=40)); return fig

def spectrogram(x,sr):
 n=256; hop=96; win=np.hanning(n); frames=[]
 for i in range(0,len(x)-n,hop): frames.append(np.abs(np.fft.rfft(x[i:i+n]*win))**2)
 S=np.array(frames).T; db=10*np.log10(S+1e-9); f=np.fft.rfftfreq(n,1/sr); tt=np.arange(db.shape[1])*hop/sr
 fig=go.Figure(go.Heatmap(z=db,x=tt,y=f,colorscale="Magma",colorbar_title="dB"))
 fig.update_layout(height=380,paper_bgcolor=BG,plot_bgcolor=BG,font_color="white",xaxis_title="Time (s)",yaxis_title="Frequency (Hz)",margin=dict(l=50,r=20,t=15,b=40)); return fig

def pump_diagram(severity):
 fig=go.Figure(); fig.add_shape(type="circle",x0=2,x1=8,y0=1,y1=7,line=dict(color=CYAN,width=4),fillcolor="#18252c")
 for a in np.linspace(0,2*np.pi,8,endpoint=False): fig.add_shape(type="line",x0=5,y0=4,x1=5+2.3*np.cos(a),y1=4+2.3*np.sin(a),line=dict(color=AMBER,width=8))
 rng=np.random.default_rng(3); n=int(5+severity*35)
 fig.add_trace(go.Scatter(x=5+rng.normal(0,.8,n),y=4+rng.normal(0,.8,n),mode="markers",marker=dict(size=6+severity*5,color="white",opacity=.65),name="vapour bubbles"))
 fig.add_annotation(x=5,y=.45,text="LOW PRESSURE AT IMPELLER EYE → BUBBLES → COLLAPSE",showarrow=False,font_color="white")
 fig.update_xaxes(visible=False,range=[0,10]); fig.update_yaxes(visible=False,range=[0,8]); fig.update_layout(height=430,paper_bgcolor=BG,plot_bgcolor=BG,showlegend=False,margin=dict(l=0,r=0,t=10,b=0)); return fig

