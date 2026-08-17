"""Synthetic consumer-complaint coordination simulation."""
from __future__ import annotations
import re
from dataclasses import dataclass,asdict
import numpy as np
import pandas as pd
import plotly.graph_objects as go

COLORS={"bg":"#0e1117","panel":"#161b22","green":"#66bb6a","red":"#ef5350","amber":"#ffb74d","blue":"#42a5f5","purple":"#ba68c8","white":"#f5f7fa","grey":"#8b949e"}
SAFETY=("smoke","burning","hot","shock","fire","spark","injury","exploded")
UNAUTHORIZED=("unauthorized","not mine","did not approve","unknown charge")

@dataclass
class Complaint:
    complaint_id:str="CMP-1048"; channel:str="email"; language:str="English"; product:str="MX-210 mixer"
    text:str="The mixer produced smoke during its second use. I have the invoice and a video."
    amount:float=4800; days_open:int=5; previous_contacts:int=3; invoice_available:bool=True
    video_available:bool=True; serial_available:bool=False; delivery_photo:bool=False
    requested_remedy:str="Replacement"; affected_customers:int=1; vulnerable_interruption:bool=False

def privacy_filter(text):
    text=str(text or "")
    text=re.sub(r"[\w.+-]+@[\w.-]+","[EMAIL]",text)
    text=re.sub(r"\b(?:\+?\d[\d -]{8,}\d)\b","[PHONE]",text)
    return re.sub(r"\s+"," ",text).strip()

def detect_signals(text):
    clean=privacy_filter(text).lower()
    return {"safety":any(w in clean for w in SAFETY),"unauthorized":any(w in clean for w in UNAUTHORIZED),"anger":sum(w in clean for w in ("angry","furious","terrible","unacceptable","hate")),"clean_text":clean}

def urgency(comp:Complaint):
    s=detect_signals(comp.text); score=0; reasons=[]
    if s["safety"]: score+=70; reasons.append("possible product-safety signal")
    if s["unauthorized"]: score+=60; reasons.append("possible unauthorized transaction")
    if comp.vulnerable_interruption: score+=55; reasons.append("vulnerable-service interruption")
    if comp.days_open>7: score+=15; reasons.append("service deadline exceeded")
    if comp.previous_contacts>=3: score+=15; reasons.append("repeated unresolved contacts")
    if comp.affected_customers>=5: score+=20; reasons.append("multiple customers may be affected")
    level="HIGH" if score>=55 else "MEDIUM" if score>=20 else "ROUTINE"
    return {"priority":level,"score":min(score,100),"reasons":reasons or ["no urgent control signal found"],"anger":s["anger"]}

def route_case(comp:Complaint):
    s=detect_signals(comp.text); text=s["clean_text"]; teams=[]
    if s["safety"]: teams+=['Product Safety','Customer Resolution','Warranty']
    if any(w in text for w in ('delivery','package','wrong item','missing item')): teams+=['Logistics','Customer Resolution']
    if s["unauthorized"] or any(w in text for w in ('refund','charge','billing')): teams+=['Billing','Compliance','Customer Resolution']
    if any(w in text for w in ('privacy','data','account hacked')): teams+=['Privacy','Compliance']
    if any(w in text for w in ('cancel','subscription','renewal')): teams+=['Subscription','Billing']
    teams=list(dict.fromkeys(teams or ['Customer Resolution']))
    return {"owner":teams[0],"supporting":teams[1:]}

def required_documents(comp:Complaint):
    s=detect_signals(comp.text); required=[("Invoice",comp.invoice_available)]
    if s["safety"]: required += [("Product serial number",comp.serial_available),("Video or inspection evidence",comp.video_available)]
    if any(w in s["clean_text"] for w in ('delivery','wrong item','missing item')): required.append(("Delivery photograph",comp.delivery_photo))
    if s["unauthorized"]: required.append(("Payment evidence",False))
    df=pd.DataFrame(required,columns=['document','available']); df['status']=np.where(df.available,'Available','Missing'); return df

def eligible_remedies(comp:Complaint):
    s=detect_signals(comp.text); text=s['clean_text']; remedies=[]
    if s['safety']: remedies=['Stop-use guidance','Approved inspection or collection','Repair','Replacement','Refund subject to policy/law']
    elif 'wrong item' in text: remedies=['Replacement','Refund']
    elif 'late' in text or 'delivery' in text: remedies=['Delivery-fee remedy','Approved compensation','Information correction']
    elif s['unauthorized'] or 'duplicate charge' in text: remedies=['Payment investigation','Correction or fee reversal']
    elif 'refund' in text: remedies=['Trace refund','Payment correction']
    else: remedies=['Information correction','Repair','Replacement','Refund subject to eligibility']
    return remedies

def recommend(comp:Complaint,similar_count=14):
    u=urgency(comp); route=route_case(comp); docs=required_documents(comp); remedies=eligible_remedies(comp)
    missing=docs.loc[~docs.available,'document'].tolist(); next_action="Request only: "+", ".join(missing) if missing else "Employee reviews eligible remedy"
    if detect_signals(comp.text)['safety']: next_action="Advise stop-use; request serial photograph; arrange approved inspection or collection"
    return {"priority":u['priority'],"urgency_score":u['score'],"reasons":u['reasons'],"owner":route['owner'],"supporting":route['supporting'],"documents":docs,"missing":missing,"remedies":remedies,"next_action":next_action,"deadline_hours":4 if u['priority']=='HIGH' else 24 if u['priority']=='MEDIUM' else 72,"systemic_alert":similar_count>=8}

def generate_complaints(n=1500,seed=23):
    rng=np.random.default_rng(seed); templates=[('delivery','I am extremely angry that my package arrived one day late.'),('safety','The charger became hot and made a faint burning smell.'),('billing','I did not approve this renewal charge.'),('refund','My refund has not arrived after ten days.'),('defect','The mixer motor stopped during its third use.'),('privacy','My account data appears to have been exposed.')]
    rows=[]
    for i in range(n):
        case,text=templates[int(rng.integers(len(templates)))]; safety=case=='safety'; contacts=int(rng.integers(0,5)); days=int(rng.integers(0,20)); channel=rng.choice(['email','phone','store','social']); language=rng.choice(['English','Hindi','Tamil','Spanish']); value=float(rng.integers(300,50000)); model='MX-210' if safety and rng.random()<.65 else rng.choice(['MX-100','MX-210','CH-55','SV-9'])
        rows.append((f'CMP-{1000+i}',text,channel,language,model,value,days,contacts,safety,case,'Product Safety' if safety else 'Customer Resolution',max(3,72-3*contacts-2*days),contacts>2,'motor-overheat' if safety and model=='MX-210' else 'none'))
    return pd.DataFrame(rows,columns=['complaint_id','complaint_text','channel','language','product','purchase_value','days_open','previous_contacts','safety_indicator','category','true_owner','resolution_hours','repeat_complaint','systemic_cluster'])

def fairness_audit(df):
    work=df.copy(); work['favourable']=work['remedy'].isin(['Refund','Replacement']); rates=work.groupby('channel').favourable.mean(); disparity=float(rates.max()-rates.min()) if len(rates)>1 else 0
    return rates.rename('favourable_remedy_rate').to_frame(),round(disparity,3)

def cluster_signal(df,cluster='motor-overheat',window=30,baseline=2):
    observed=int((df.systemic_cluster==cluster).sum()); confidence='Moderate' if observed and observed<20 else 'High'
    return {'cluster':cluster,'observed':observed,'expected_high':baseline+1,'alert':observed>baseline+3,'confidence':confidence}

def resolution_check(remedy_approved,remedy_delivered,customer_informed,safety_open=True,repeat_contact=False):
    checks={'Remedy approved':remedy_approved,'Remedy delivered':remedy_delivered,'Customer informed':customer_informed,'Required safety investigation open':safety_open,'No unresolved repeat contact':not repeat_contact}
    return pd.Series(checks,name='complete'),all(checks.values())

def compare_systems():
    return pd.DataFrame({'system':['Manual inbox','Keyword rules','Sentiment priority','ML classifier','Rescue system','Fair Rescue system'],'resolution_hours':[72,48,52,27,19,20],'wrong_transfers':[428,190,241,94,61,63],'repeat_complaints':[312,221,248,139,104,101],'urgent_missed':[18,8,15,5,2,2],'fairness_exceptions':[37,29,33,14,11,6]})

def _style(fig,title,x,y):
    fig.update_layout(title=title,template='plotly_dark',paper_bgcolor=COLORS['bg'],plot_bgcolor=COLORS['panel'],font_color=COLORS['white'],xaxis_title=x,yaxis_title=y,margin=dict(l=55,r=30,t=60,b=55)); return fig

def fig_urgency(rows):
    fig=go.Figure(go.Bar(x=rows['complaint'],y=rows['urgency_score'],marker_color=[COLORS['amber'],COLORS['red']],text=rows['urgency_score'],textposition='outside')); return _style(fig,'Anger is not urgency','Complaint','Urgency score')

def fig_systemic(days,counts,baseline=2):
    fig=go.Figure(); fig.add_scatter(x=days,y=counts,mode='lines+markers',name='Observed complaints',line_color=COLORS['red']); fig.add_hline(y=baseline+3,line_dash='dash',line_color=COLORS['amber'],annotation_text='Investigation threshold'); return _style(fig,'Early product-pattern warning','Day','Similar complaints (30-day window)')

def fig_compare(df):
    fig=go.Figure(); fig.add_bar(name='Wrong transfers',x=df.system,y=df.wrong_transfers,marker_color=COLORS['amber']); fig.add_bar(name='Urgent cases missed',x=df.system,y=df.urgent_missed,marker_color=COLORS['red']); return _style(fig,'Simulated complaint-system comparison','System','Cases')
