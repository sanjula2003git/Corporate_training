import ast,json,pathlib,textwrap
ROOT=pathlib.Path(__file__).parent
source=ROOT.joinpath("invoice_guardian.py").read_text(encoding="utf-8")
tree=ast.parse(source); lines=source.splitlines(); blocks={}
for node in tree.body:
    if isinstance(node,(ast.FunctionDef,ast.ClassDef)):
        start=min([node.lineno]+[d.lineno for d in node.decorator_list])
        blocks[node.name]="\n".join(lines[start-1:node.end_lineno])+"\n"
cells=[]
def md(s): cells.append({"cell_type":"markdown","metadata":{},"source":textwrap.dedent(s).strip()+"\n"})
def co(s): cells.append({"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":textwrap.dedent(s).strip()+"\n"})
def core(*names):
    for name in names: co(blocks[name])

md("""# 🧾 Before We Pay Twice
### Building an AI Invoice Guardian for Small Businesses

One supplier invoice can fail several controls. The goal is not to call it fraudulent; the goal is to identify the failed evidence, protect cash, and tell the accountant what happens next.

> **Research question:** Can three-way controls, duplicate similarity, anomaly detection and payment scheduling reduce incorrect payments and processing time without excessive false holds?

⚠️ Every record is synthetic. This notebook never authorizes a real payment or accuses a real supplier.""")
md('🎬 **The illustrated version — open it once.**\n\n[Open the Invoice Guardian illustration app in a second tab](https://invoice-guardian-ai.streamlit.app/?stage=start) and leave it open beside this notebook.\n\nEvery lesson below carries a line like *"🎬 Illustration tab → step 3 · *Duplicate trail*"*. That names the page to open from\nthe **Learning journey** list in the app\'s sidebar. There is deliberately no second link to click: Colab gives every link click a brand-new browser tab,\nso one anchor here keeps you at two tabs instead of sixty.\n')
md("""### Learning journey

Manual work → linked records → realistic errors → three-way matching → fixed rules → rule failures → duplicate similarity → anomaly detection → hybrid control → explanations → missing documents → bank changes → scheduling → liquidity → review queue → control room.""")
md("## Setup\nFunctions arrive in short cells so each accounting idea can be read before it is used.")
co("""try:
    import plotly.graph_objects as go
    import sklearn
except ModuleNotFoundError:
    import micropip
    await micropip.install(["plotly","scikit-learn","ipywidgets","nbformat"])
import re
from dataclasses import dataclass,asdict
from difflib import SequenceMatcher
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from IPython.display import display,clear_output
import ipywidgets as widgets
np.random.seed(17)
print("Invoice Guardian laboratory ready.")""")
co('COLORS={"bg":"#0e1117","panel":"#161b22","green":"#66bb6a","red":"#ef5350","amber":"#ffb74d","blue":"#42a5f5","purple":"#ba68c8","white":"#f5f7fa","grey":"#8b949e"}')
core("Invoice")

md("## 1 · A small business paying invoices manually\nFirst quantify the workload and control losses.")
co("""manual=pd.Series({"suppliers":50,"purchase_orders":500,"receipts":450,"invoices":600,
"review_minutes_per_invoice":18,"incorrect_payments":7,"duplicates_paid":4,"late_payments":31,
"discounts_missed_rupees":42000})
manual["processing_hours"]=manual.invoices*manual.review_minutes_per_invoice/60
manual.to_frame("simulated month")""")

md("## 2 · Build linked accounting records\nA decision begins with source records, not an isolated invoice image.")
core("example_history")
co("""purchase_orders=pd.DataFrame([("PO-2317","SUP-014",120,500,.18)],columns=["po_id","supplier_id","quantity","unit_price","tax_rate"])
goods_received=pd.DataFrame([("GRN-441","PO-2317",100,0,"Accepted")],columns=["grn_id","po_id","accepted_qty","rejected_qty","status"])
supplier_invoices=pd.DataFrame([asdict(Invoice())]); payment_history=example_history()
display(purchase_orders,goods_received,supplier_invoices.head(),payment_history)""")

md("## 3 · Introduce errors—and genuine exceptions\nA difference is evidence to investigate, not proof of wrongdoing.")
core("generate_invoices")
co("quarter=generate_invoices(5000); quarter.true_case.value_counts().rename('invoices').to_frame()")
co("quarter.groupby('true_case')[[\"invoice_total\",\"days_to_due\"]].agg([\"count\",\"mean\"]).round(1)")

md("## 4 · Three-way matching\nCompare what was authorized, accepted and billed.")
core("three_way_match")
co("scenario=Invoice(); match=three_way_match(scenario); match")
core("_style")
core("fig_match")
co('fig_match(match,"INV-7841: invoice minus source evidence").show()')

md("## 5 · Build fixed accounting rules\nMandatory controls remain explicit and auditable.")
co("""def exact_rule(inv):
    m=three_way_match(inv).set_index("control")
    if inv.previously_paid: return "HOLD_DUPLICATE"
    if not inv.po_found or not inv.grn_found: return "REQUEST_DOCUMENT"
    if not m.loc["Quantity","pass"]: return "HOLD_QUANTITY_MISMATCH"
    if inv.bank_changed and not inv.authorized_bank_change: return "ESCALATE_BANK_CHANGE"
    if not m.loc["Unit price","pass"]: return "HOLD_PRICE_MISMATCH"
    if not m.loc["Tax","pass"]: return "ESCALATE_TAX_ERROR"
    return "AUTO_APPROVE"
exact_rule(scenario)""")

md("## 6 · Make exact rules fail\nPunctuation can hide duplicates; legitimate same-value invoices can create false alarms.")
core("normalize_invoice_id")
co("""pairs=pd.DataFrame([("INV-1204","INV1204",True),("INV-1204","INV-1205",False),("MAR-RENT","APR-RENT",False)],columns=["new","old","truly_same"])
pairs["exact_match"]=pairs.new==pairs.old
pairs["normalized_match"]=[normalize_invoice_id(a)==normalize_invoice_id(b) for a,b in zip(pairs.new,pairs.old)]
pairs""")

md("## 7 · Duplicate-invoice similarity engine\nSeveral weak clues become useful when their evidence is shown together.")
core("duplicate_similarity")
co("duplicate=duplicate_similarity(scenario,payment_history); pd.Series(duplicate)")

md("## 8 · Anomaly detection\nAnomaly means review this pattern—not fraud confirmed.")
core("anomaly_score")
co("""examples=[Invoice(),Invoice(invoice_qty=100,received_qty=100,invoice_unit_price=500,contract_unit_price=500,reported_tax=9000,bank_changed=False),Invoice(bank_changed=False,grn_found=False)]
pd.DataFrame([{"case":name,"anomaly_score":anomaly_score(inv)} for name,inv in zip(["multi-control exception","clean","missing receipt"],examples)])""")
co("""from sklearn.ensemble import IsolationForest
features=quarter.assign(price_dev=lambda d:(d.invoice_unit_price-d.contract_unit_price)/d.contract_unit_price,qty_dev=lambda d:(d.invoice_qty-d.received_qty)/d.received_qty,tax_dev=lambda d:(d.reported_tax-d.calculated_tax)/d.invoice_total)[["price_dev","qty_dev","tax_dev","bank_changed","document_count"]]
iso=IsolationForest(contamination=.15,random_state=17).fit(features)
quarter["isolation_score"]=-iso.score_samples(features)
quarter.groupby("true_case").isolation_score.mean().sort_values(ascending=False).round(3).to_frame()""")

md("## 9 · Combine rules and AI\nRules stop known failures; AI prioritizes uncertain residual patterns.")
core("guardian_decision")
co("""decision=guardian_decision(scenario,payment_history)
pd.Series({"action":decision["action"],"duplicate_probability":decision["duplicate"]["probability"],"anomaly":decision["anomaly"],"reasons":"; ".join(decision["reasons"])})""")

md("## 10 · Explain every hold\nCite the failed source-record comparisons.")
core("risk_contributions")
core("fig_risk")
co("contributions=risk_contributions(scenario,payment_history); fig_risk(contributions).show(); contributions.sort_values('risk_points',ascending=False)")

md("## 11 · Missing-document workflow\nInternal receipt confirmation belongs with stores—not the supplier.")
co("""pd.DataFrame({"document":["Purchase order","Goods-received note","Supplier invoice","Contract price"],
"status":["Found","Missing","Found","Found"],"owner":["Purchasing","Stores","Accounts payable","Purchasing"]})""")
co('print("Request goods-received confirmation from stores; keep payment on hold.")')

md("## 12 · Safe bank-detail-change workflow\nInvoice contact information cannot verify its own payment destination.")
co("""pd.DataFrame({"step":range(1,7),"control":["Hold payment","Compare supplier master","Find authorized change request","Verify independently","Record approver","Release after policy clears"]})""")

md("## 13 · Payment scheduling\nOnly a valid invoice reaches the scheduler.")
core("payment_schedule")
co("""clean=Invoice(invoice_qty=100,received_qty=100,invoice_unit_price=500,contract_unit_price=500,reported_tax=9000,bank_changed=False,days_to_due=10)
pd.Series(payment_schedule(clean))""")

md("## 14 · Working-capital optimizer\nSchedule approved invoices while preserving the cash reserve.")
co("""approved=quarter.query("true_case in ['clean','authorized_exception']").nsmallest(15,"days_to_due").copy()
approved["priority"]=np.maximum(0,5-approved.days_to_due)+approved.invoice_total/100000
cash=500000; reserve=250000; schedule=[]
for row in approved.sort_values("priority",ascending=False).itertuples():
    pay=row.invoice_total<=cash-reserve; schedule.append((row.invoice_id,row.invoice_total,row.days_to_due,"PAY" if pay else "DEFER",cash-row.invoice_total if pay else cash))
    if pay: cash-=row.invoice_total
pd.DataFrame(schedule,columns=["invoice","amount","due_days","decision","cash_after"])""")

md("## 15 · Human-review queue\nRank exposure, deadline and control severity—not merely anomaly.")
core("review_queue")
co("queue=review_queue(quarter); queue")

md("## 16 · Final Invoice Guardian control room\nChange an invoice and watch the controls respond.")
co("""qty_w=widgets.IntSlider(value=120,min=80,max=140,description="Invoice qty"); received_w=widgets.IntSlider(value=100,min=60,max=140,description="Received")
price_w=widgets.IntSlider(value=525,min=450,max=600,description="Price ₹"); bank_w=widgets.Checkbox(value=True,description="Bank changed"); grn_w=widgets.Checkbox(value=True,description="Receipt found"); out=widgets.Output()
def redraw(*_):
    with out:
        clear_output(wait=True); inv=Invoice(invoice_qty=qty_w.value,received_qty=received_w.value,invoice_unit_price=price_w.value,bank_changed=bank_w.value,grn_found=grn_w.value); d=guardian_decision(inv,payment_history)
        display(pd.Series({"action":d["action"],"duplicate probability":d["duplicate"]["probability"],"anomaly score":d["anomaly"],"reasons":"; ".join(d["reasons"])}).to_frame("value")); fig_match(d["match"]).show()
for w in [qty_w,received_w,price_w,bank_w,grn_w]: w.observe(redraw,"value")
display(widgets.VBox([widgets.HBox([qty_w,received_w,price_w]),widgets.HBox([bank_w,grn_w])]),out); redraw()""")

md("## Final simulated benchmark\nCompare systems using business outcomes—not accuracy alone.")
core("compare_systems")
core("fig_compare")
co("comparison=compare_systems(); fig_compare(comparison).show(); comparison")
md("""## What this simulation may claim

It can compare strategies inside a synthetic quarter. It cannot validate a real supplier, approve a bank change, authorize a payment or establish fraud.

### Rules that do not move

- Never release a confirmed duplicate.
- Never let AI override bank-change verification policy.
- Never infer wrongdoing from an anomaly score.
- Cite source records behind every hold.
- Preserve liquidity only after invoice validity is established.
- Keep an accountable human reviewer in uncertain cases.""")

# One anchor near the top; each lesson names the step to open in the illustration tab.
# Colab opens a fresh tab per link click, so per-cell links are deliberately NOT emitted.
_STEPS=['Start', 'Three-way match', 'Duplicate trail', 'Explain the hold', 'Missing documents', 'Bank-change control', 'Payment scheduler', 'Quarterly benchmark']
_SMAP={1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 2, 7: 3, 8: 3, 9: 3, 10: 4, 11: 5, 12: 6, 13: 7, 14: 7, 15: 4, 16: 8}
_FINALS={'Final simulated benchmark': 8}
import re as _re
for _cell in cells:
    if _cell["cell_type"]!="markdown": continue
    _src=_cell["source"] if isinstance(_cell["source"],str) else "".join(_cell["source"])
    _m=_re.match(r"##\s+(\d+)\s+·",_src.lstrip())
    _step=_SMAP.get(int(_m.group(1))) if _m else next(
        (_v for _k,_v in _FINALS.items() if _src.lstrip().startswith("## "+_k)),None)
    if _step:
        _cell["source"]=_src.rstrip()+"\n\n> 🎬 **Illustration tab →** step %d · *%s*\n"%(_step,_STEPS[_step-1])
nb={"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3"},"colab":{"name":"Invoice_Guardian_AI.ipynb","provenance":[]}},"nbformat":4,"nbformat_minor":5}
ROOT.joinpath("Invoice_Guardian_AI.ipynb").write_text(json.dumps(nb,ensure_ascii=False,indent=1),encoding="utf-8")
print(f"Wrote Invoice_Guardian_AI.ipynb: {len(cells)} cells")
