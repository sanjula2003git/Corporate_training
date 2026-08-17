import streamlit as st
from invoice_guardian import *

st.set_page_config(page_title="Invoice Guardian",page_icon="🧾",layout="wide")
st.title("🧾 Before We Pay Twice")
st.caption("A simulated accounting-control laboratory — no real supplier or bank data")
pages=["Start","Three-way match","Duplicate trail","Explain the hold","Missing documents","Bank-change control","Payment scheduler","Quarterly benchmark"]
stage=st.query_params.get("stage","start"); default={p.lower().replace(" ","-"):p for p in pages}.get(stage,"Start")
page=st.sidebar.radio("Learning journey",pages,index=pages.index(default))

history=example_history()
with st.sidebar.expander("Invoice controls",expanded=True):
    qty=st.slider("Invoice quantity",80,140,120); received=st.slider("Goods received",60,140,100)
    price=st.slider("Invoice unit price (₹)",450,600,525); contract=st.slider("Contract price (₹)",450,600,500)
    bank=st.checkbox("Bank account changed",True); bank_ok=st.checkbox("Approved master-data change",False)
    po=st.checkbox("Purchase order found",True); grn=st.checkbox("Goods-received note found",True)
    cash=st.slider("Cash balance (₹)",100000,1000000,500000,25000)
inv=Invoice(invoice_qty=qty,received_qty=received,invoice_unit_price=price,contract_unit_price=contract,bank_changed=bank,authorized_bank_change=bank_ok,po_found=po,grn_found=grn,cash_balance=cash)
result=guardian_decision(inv,history)

if page=="Start":
    st.header("One invoice, several independent controls")
    a,b,c=st.columns(3); a.metric("Requested payment",f"₹{inv.invoice_total:,.0f}"); b.metric("Guardian action",result["action"]); c.metric("Anomaly score",f"{result['anomaly']:.0%}")
    st.info("The AI does not call an invoice fraudulent. It identifies the failed control and recommends the next accounting action.")
elif page=="Three-way match":
    st.header("Purchase order ↔ receipt ↔ invoice")
    st.plotly_chart(fig_match(result["match"]),use_container_width=True); st.dataframe(result["match"],hide_index=True,use_container_width=True)
elif page=="Duplicate trail":
    st.header("Near-duplicate evidence")
    st.metric("Duplicate probability",f"{result['duplicate']['probability']:.0%}"); st.write("Closest paid invoice:",result["duplicate"]["closest"]); st.write(result["duplicate"]["evidence"]); st.dataframe(history,use_container_width=True)
elif page=="Explain the hold":
    st.header(result["action"]); st.plotly_chart(fig_risk(risk_contributions(inv,history)),use_container_width=True)
    for reason in result["reasons"]: st.error(reason)
elif page=="Missing documents":
    st.header("Ask the right internal team for the missing evidence")
    st.table({"Document":["Purchase order","Goods-received note","Supplier invoice","Contract price"],"Status":["Found" if po else "Missing","Found" if grn else "Missing","Found","Found"]})
    if not grn: st.warning("Request goods-received confirmation from stores. Do not ask the supplier to verify an internal receipt.")
elif page=="Bank-change control":
    st.header("A deterministic payment-destination control")
    steps=["Hold payment","Compare supplier master","Find authorized change request","Verify independently","Record approver","Release only after policy clears"]
    for i,s in enumerate(steps,1): st.write(f"{i}. {s}")
    if bank and not bank_ok: st.error("Invoice contact details must never be the sole verification source.")
    else: st.success("No unresolved bank-change control.")
elif page=="Payment scheduler":
    st.header("Validity first; timing second")
    plan=payment_schedule(inv); st.json(plan); st.caption("The scheduler cannot override an invoice hold.")
else:
    st.header("Simulated quarterly benchmark")
    comp=compare_systems(); st.plotly_chart(fig_compare(comp),use_container_width=True); st.dataframe(comp,use_container_width=True,hide_index=True)
    st.caption("Illustrative synthetic results—not evidence of real-world performance.")
