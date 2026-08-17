"""Deterministic synthetic accounting-control simulation. No real supplier data."""
from __future__ import annotations
import re
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
import numpy as np
import pandas as pd
import plotly.graph_objects as go

COLORS={"bg":"#0e1117","panel":"#161b22","green":"#66bb6a","red":"#ef5350","amber":"#ffb74d","blue":"#42a5f5","purple":"#ba68c8","white":"#f5f7fa","grey":"#8b949e"}

@dataclass
class Invoice:
    invoice_id:str="INV-7841"; supplier_id:str="SUP-014"; po_id:str="PO-2317"
    invoice_qty:int=120; po_qty:int=120; received_qty:int=100
    invoice_unit_price:float=525; contract_unit_price:float=500
    tax_rate:float=.18; reported_tax:float=11340; bank_changed:bool=True
    authorized_bank_change:bool=False; po_found:bool=True; grn_found:bool=True
    previously_paid:bool=False; days_to_due:int=4; supplier_criticality:float=.75
    cash_balance:float=500000; minimum_reserve:float=250000
    @property
    def subtotal(self): return self.invoice_qty*self.invoice_unit_price
    @property
    def invoice_total(self): return self.subtotal+self.reported_tax

def normalize_invoice_id(value):
    return re.sub(r"[^A-Z0-9]","",str(value).upper()).lstrip("0")

def three_way_match(inv:Invoice,qty_tolerance=.02,price_tolerance=.01,tax_tolerance=2):
    calc_tax=round(inv.subtotal*inv.tax_rate,2)
    rows=[
        ("Quantity",inv.invoice_qty,inv.received_qty,inv.invoice_qty-inv.received_qty,abs(inv.invoice_qty-inv.received_qty)<=max(1,inv.received_qty*qty_tolerance)),
        ("Unit price",inv.invoice_unit_price,inv.contract_unit_price,inv.invoice_unit_price-inv.contract_unit_price,abs(inv.invoice_unit_price-inv.contract_unit_price)<=inv.contract_unit_price*price_tolerance),
        ("Tax",inv.reported_tax,calc_tax,inv.reported_tax-calc_tax,abs(inv.reported_tax-calc_tax)<=tax_tolerance)]
    return pd.DataFrame(rows,columns=["control","invoice_value","source_value","difference","pass"])

def duplicate_similarity(inv:Invoice,history:pd.DataFrame):
    if history.empty:return {"probability":0.0,"closest":None,"evidence":[]}
    scores=[]
    for row in history.itertuples():
        number=SequenceMatcher(None,normalize_invoice_id(inv.invoice_id),normalize_invoice_id(row.invoice_id)).ratio()
        supplier=float(inv.supplier_id==row.supplier_id); amount=max(0,1-abs(inv.invoice_total-row.amount)/max(inv.invoice_total,1))
        po=float(inv.po_id==row.po_id); paid=float(row.paid)
        score=.30*number+.20*supplier+.20*amount+.15*po+.15*paid
        scores.append((score,row,number,supplier,amount,po,paid))
    score,row,*parts=max(scores,key=lambda x:x[0]); labels=["similar invoice number","same supplier","same amount","same PO","previously paid"]
    return {"probability":round(score,3),"closest":row.invoice_id,"evidence":[l for l,v in zip(labels,parts) if v>.85]}

def anomaly_score(inv:Invoice):
    price=abs(inv.invoice_unit_price-inv.contract_unit_price)/max(inv.contract_unit_price,1)
    qty=max(0,inv.invoice_qty-inv.received_qty)/max(inv.received_qty,1)
    tax=abs(inv.reported_tax-inv.subtotal*inv.tax_rate)/max(inv.subtotal,1)
    missing=(not inv.po_found)+(not inv.grn_found)
    raw=3.2*price+2.8*qty+2.2*tax+.9*inv.bank_changed+.7*missing
    return round(float(1-np.exp(-raw)),3)

def guardian_decision(inv:Invoice,history:pd.DataFrame):
    match=three_way_match(inv); dup=duplicate_similarity(inv,history); anomaly=anomaly_score(inv)
    reasons=[]; action="AUTO_APPROVE"
    if inv.previously_paid or dup["probability"]>=.90: action="HOLD_DUPLICATE"; reasons.append("Prior-payment evidence or a near-duplicate was found")
    if not inv.po_found or not inv.grn_found: action="REQUEST_DOCUMENT"; reasons.append("A required internal source document is missing")
    if not bool(match.loc[match.control=="Quantity","pass"].iloc[0]): action="HOLD_QUANTITY_MISMATCH"; reasons.append("Invoice quantity exceeds accepted goods")
    if not bool(match.loc[match.control=="Unit price","pass"].iloc[0]): action="HOLD_PRICE_MISMATCH"; reasons.append("Billed price exceeds the authorized price")
    if inv.bank_changed and not inv.authorized_bank_change: action="ESCALATE_BANK_CHANGE"; reasons.append("Payment destination changed without an approved master-data change")
    if not bool(match.loc[match.control=="Tax","pass"].iloc[0]): action="ESCALATE_TAX_ERROR"; reasons.append("Reported tax differs from recalculation")
    if action=="AUTO_APPROVE" and anomaly>.65: action="HUMAN_REVIEW"; reasons.append("Unusual pattern exceeds the review threshold")
    return {"action":action,"reasons":reasons or ["Mandatory controls passed"],"match":match,"duplicate":dup,"anomaly":anomaly}

def risk_contributions(inv:Invoice,history):
    d=guardian_decision(inv,history); m=d["match"].set_index("control")
    rows={"Quantity mismatch":35*(not bool(m.loc["Quantity","pass"])),"Changed payment account":30*(inv.bank_changed and not inv.authorized_bank_change),"Unit-price deviation":18*(not bool(m.loc["Unit price","pass"])),"Near duplicate":12*d["duplicate"]["probability"],"Tax difference":8*(not bool(m.loc["Tax","pass"])),"Missing documents":25*((not inv.po_found) or (not inv.grn_found))}
    return pd.DataFrame({"factor":rows.keys(),"risk_points":rows.values()}).sort_values("risk_points",ascending=True)

def payment_schedule(inv:Invoice,discount_rate=.02,discount_days=3,annual_cash_cost=.12):
    valid=guardian_decision(inv,example_history())["action"]=="AUTO_APPROVE"
    cash_available=inv.cash_balance-inv.minimum_reserve
    benefit=inv.invoice_total*discount_rate; carrying=inv.invoice_total*annual_cash_cost*max(inv.days_to_due-discount_days,0)/365
    if not valid:return {"decision":"HOLD — controls not cleared","day":None,"benefit":0,"cash_after":inv.cash_balance}
    if inv.invoice_total>cash_available:return {"decision":"ESCALATE CASH SHORTAGE","day":None,"benefit":0,"cash_after":inv.cash_balance}
    early=benefit>carrying and discount_days<=inv.days_to_due
    return {"decision":"CAPTURE EARLY DISCOUNT" if early else "PAY ON DUE DATE","day":discount_days if early else inv.days_to_due,"benefit":round(benefit if early else 0,2),"cash_after":round(inv.cash_balance-inv.invoice_total,2)}

def example_history():
    return pd.DataFrame([("INV-07841","SUP-014","PO-2317",74340,True,12),("INV-5520","SUP-008","PO-1108",42800,True,31),("INV-7710","SUP-014","PO-2250",61500,True,45)],columns=["invoice_id","supplier_id","po_id","amount","paid","days_ago"])

def generate_invoices(n=1000,seed=17):
    rng=np.random.default_rng(seed); rows=[]
    cases=np.array(["clean","quantity","price","duplicate","bank","tax","missing","authorized_exception"]); probs=[.68,.06,.06,.05,.04,.04,.04,.03]
    for i,case in enumerate(rng.choice(cases,n,p=probs)):
        qty=int(rng.integers(5,180)); received=qty; price=float(rng.integers(80,2500)); billed=price; bank=False; docs=2; paid=False; auth=False
        if case=="quantity": received=max(1,int(qty*rng.uniform(.65,.92)))
        if case=="price": billed=price*rng.uniform(1.04,1.18)
        if case=="duplicate": paid=True
        if case=="bank": bank=True
        if case=="missing": docs=1
        if case=="authorized_exception": billed=price*1.02; auth=True
        subtotal=qty*billed; calc=subtotal*.18; reported=calc+(rng.uniform(25,250) if case=="tax" else rng.uniform(-1,1))
        rows.append((f"INV-{10000+i}",f"SUP-{rng.integers(1,101):03d}",f"PO-{rng.integers(1000,9999)}",qty,received,billed,price,reported,calc,subtotal+reported,bank,docs,int(rng.integers(-4,31)),paid,auth,case))
    return pd.DataFrame(rows,columns=["invoice_id","supplier_id","po_id","invoice_qty","received_qty","invoice_unit_price","contract_unit_price","reported_tax","calculated_tax","invoice_total","bank_changed","document_count","days_to_due","previously_paid","authorized_exception","true_case"])

def compare_systems():
    return pd.DataFrame({"system":["Manual","Exact rules","AI only","Guardian","Guardian + scheduler"],"processing_hours":[620,210,135,105,112],"incorrect_payments":[34,13,9,3,3],"false_holds":[21,143,62,38,38],"financial_loss":[527000,296000,244000,91000,23000]})

def review_queue(invoices):
    df=invoices.copy(); df["priority_score"]=df.invoice_total/10000+8*df.bank_changed+7*df.previously_paid+5*(df.document_count<2)+np.maximum(0,5-df.days_to_due)
    return df.sort_values("priority_score",ascending=False).head(12)[["invoice_id","supplier_id","true_case","invoice_total","days_to_due","priority_score"]]

def fig_match(match,title="Three-way accounting match"):
    fig=go.Figure(go.Bar(x=match.control,y=match.difference,marker_color=[COLORS["green"] if x else COLORS["red"] for x in match["pass"]],text=match.difference.round(2),textposition="outside")); return _style(fig,title,"Control","Difference")

def fig_risk(contrib,title="Why the invoice is held"):
    fig=go.Figure(go.Bar(x=contrib.risk_points,y=contrib.factor,orientation="h",marker_color=COLORS["amber"],text=contrib.risk_points.round(1),textposition="outside")); return _style(fig,title,"Risk points","")

def fig_compare(df):
    fig=go.Figure(); fig.add_bar(name="Incorrect payments",x=df.system,y=df.incorrect_payments,marker_color=COLORS["red"]); fig.add_bar(name="False holds",x=df.system,y=df.false_holds,marker_color=COLORS["amber"]); return _style(fig,"Simulated control-system comparison","System","Cases")

def _style(fig,title,x,y):
    fig.update_layout(title=title,template="plotly_dark",paper_bgcolor=COLORS["bg"],plot_bgcolor=COLORS["panel"],font_color=COLORS["white"],xaxis_title=x,yaxis_title=y,margin=dict(l=50,r=30,t=60,b=50)); return fig
