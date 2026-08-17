import ast,json,pathlib
ROOT=pathlib.Path(__file__).parent
src=ROOT.joinpath('complaint_rescue.py').read_text(encoding='utf-8'); tree=ast.parse(src); ls=src.splitlines(); blocks={}
for n in tree.body:
    if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
        start=min([n.lineno]+[d.lineno for d in n.decorator_list]); blocks[n.name]='\n'.join(ls[start-1:n.end_lineno])+'\n'
cells=[]
def md(s): cells.append({'cell_type':'markdown','metadata':{},'source':s.strip()+'\n'})
def co(s): cells.append({'cell_type':'code','execution_count':None,'metadata':{},'outputs':[],'source':s.strip()+'\n'})
def core(*names):
    for name in names: co(blocks[name])

md("# 🛟 From Complaint to Correction\n### Building an AI Consumer Complaint Rescue System\n\nA complaint is not merely text to classify. It needs ownership, evidence, a fair remedy and sometimes a correction to the whole system.\n\n> **Research question:** Can a hybrid AI system reduce resolution time and repeat contacts while improving urgent-case detection, remedy consistency and early identification of systemic problems?\n\n⚠️ All complaints are fictitious. Real guidance and remedies must follow applicable law and approved policy.")
md('🎬 **The illustrated version — open it once.**\n\n[Open the Complaint Rescue illustration app in a second tab](https://complaint-rescue-ai.streamlit.app/?stage=start) and leave it open beside this notebook.\n\nEvery lesson below carries a line like *"🎬 Illustration tab → step 3 · *Routing*"*. That names the page to open from\nthe **Learning journey** list in the app\'s sidebar. There is deliberately no second link to click: Colab gives every link click a brand-new browser tab,\nso one anchor here keeps you at two tabs instead of sixty.\n')
md('### Learning journey\n\nCustomer journey → synthetic cases → privacy filtering → urgency versus anger → urgency rules → priority model → multi-team routing → minimum evidence → policy remedies → fair choice → disparity audit → complaint clusters → defect warning → ownership → verified closure → control room.')
md('## Setup\nEvery function appears in a small cell before students use it.')
co("try:\n    import plotly.graph_objects as go\n    import sklearn\nexcept ModuleNotFoundError:\n    import micropip\n    await micropip.install(['plotly','scikit-learn','ipywidgets','nbformat'])\nimport re\nfrom dataclasses import dataclass,asdict\nimport numpy as np\nimport pandas as pd\nimport plotly.graph_objects as go\nfrom IPython.display import display,clear_output\nimport ipywidgets as widgets\nnp.random.seed(23)\nprint('Complaint Rescue laboratory ready.')")
co("COLORS={'bg':'#0e1117','panel':'#161b22','green':'#66bb6a','red':'#ef5350','amber':'#ffb74d','blue':'#42a5f5','purple':'#ba68c8','white':'#f5f7fa','grey':'#8b949e'}\nSAFETY=('smoke','burning','hot','shock','fire','spark','injury','exploded')\nUNAUTHORIZED=('unauthorized','not mine','did not approve','unknown charge')")
core('Complaint')
md('## 1 · A customer lost inside the company\nRepeated transfers increase waiting, handling time and abandonment risk.')
co("journey=pd.DataFrame({'department':['Customer service','Delivery team','Store','Manufacturer','Customer service again'],'wait_hours':[3,9,7,18,11],'handling_minutes':[12,18,14,25,20]})\njourney['cumulative_wait']=journey.wait_hours.cumsum(); transfers=len(journey)-1; abandonment=1-np.exp(-journey.wait_hours.sum()/55)\ndisplay(journey,pd.Series({'transfers':transfers,'waiting_hours':journey.wait_hours.sum(),'repeated_explanations':4,'employee_minutes':journey.handling_minutes.sum(),'abandonment_probability':abandonment}).to_frame('value'))")
md('## 2 · Generate fictitious complaint records\nThe dataset links text, channel, evidence, effort and outcomes.')
core('generate_complaints'); co("complaints=generate_complaints(1500); complaints.head()"); co("complaints.groupby(['category','channel']).size().unstack(fill_value=0)")
md('## 3 · Clean text without deleting important emotion\nRemove contact details while preserving facts and wording.')
core('privacy_filter'); core('detect_signals'); co("raw='Call +91 98765 43210 or priya@example.com. The charger made a burning smell!'; pd.Series({'raw':raw,'privacy_filtered':privacy_filter(raw),**detect_signals(raw)})")
md('## 4 · Why sentiment is not urgency\nA calm safety complaint may require faster action than an angry delivery complaint.')
core('urgency'); co("anger_case=Complaint(text='I am extremely angry that my package arrived one day late.',days_open=1,previous_contacts=0)\nsafety_case=Complaint(text='The charger became hot and made a faint burning smell.',days_open=0,previous_contacts=0)\nurgency_rows=pd.DataFrame([{'complaint':'Angry late parcel',**urgency(anger_case)},{'complaint':'Calm burning smell',**urgency(safety_case)}]); urgency_rows[['complaint','priority','score','anger','reasons']]")
core('_style'); core('fig_urgency'); co("fig_urgency(urgency_rows.rename(columns={'score':'urgency_score'})).show()")
md('## 5 · Build a baseline urgency rule\nSafety, unauthorized payment, vulnerable service and unresolved effort are explicit controls.')
co("pd.DataFrame([{'case':name,**urgency(case)} for name,case in [('angry',anger_case),('safety',safety_case),('repeated',Complaint(text='My refund is delayed.',days_open=12,previous_contacts=5))]])")
md('## 6 · Train a priority model\nEvaluate recall for genuinely urgent complaints—not accuracy alone.')
co("from sklearn.feature_extraction.text import TfidfVectorizer\nfrom sklearn.compose import ColumnTransformer\nfrom sklearn.pipeline import make_pipeline\nfrom sklearn.linear_model import LogisticRegression\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.metrics import classification_report\nX=complaints[['complaint_text','days_open','previous_contacts','purchase_value']]; y=complaints.safety_indicator.astype(int)\ntrain_x,test_x,train_y,test_y=train_test_split(X,y,test_size=.25,random_state=23,stratify=y)\nprep=ColumnTransformer([('text',TfidfVectorizer(ngram_range=(1,2)),'complaint_text'),('numeric','passthrough',['days_open','previous_contacts','purchase_value'])])\npriority_model=make_pipeline(prep,LogisticRegression(max_iter=500,class_weight='balanced')).fit(train_x,train_y)\nprint(classification_report(test_y,priority_model.predict(test_x),target_names=['routine','urgent']))")
md('## 7 · Multi-department routing\nOne accountable owner may coordinate several supporting teams.')
core('route_case'); co("pd.DataFrame([{'scenario':name,**route_case(case)} for name,case in [('overheating',safety_case),('renewal',Complaint(text='I did not approve this subscription renewal.')),('delivery',Complaint(text='My delivery arrived damaged.'))]])")
md('## 8 · Required-document engine\nRequest only the minimum evidence genuinely needed.')
core('required_documents'); co("required_documents(Complaint()).drop(columns='available')")
md('## 9 · Policy-based remedy engine\nAI retrieves eligible options; deterministic policy prevents invented remedies.')
core('eligible_remedies'); co("pd.DataFrame([{'issue':name,'eligible_remedies':eligible_remedies(case)} for name,case in [('safety',safety_case),('wrong item',Complaint(text='The wrong item was delivered.')),('charge',Complaint(text='I did not approve this charge.'))]])")
md('## 10 · Choose a fair remedy\nBalance cost, time, repeat-contact risk, unfairness and unnecessary escalation.')
co("remedies=pd.DataFrame({'remedy':['Information correction','Repair','Replacement','Refund','Specialist investigation'],'cost':[50,900,2200,4800,1200],'hours':[2,72,48,24,12],'repeat_risk':[.45,.18,.10,.08,.12],'fairness_penalty':[.55,.18,.08,.05,.05],'escalation_cost':[0,0,0,0,.35]})\nremedies['objective']=.15*remedies.cost/100+.20*remedies.hours+40*remedies.repeat_risk+45*remedies.fairness_penalty+20*remedies.escalation_cost\nremedies.sort_values('objective')")
md('## 11 · Fairness audit\nCompare outcomes across channels after holding legitimate case facts constant.')
core('fairness_audit'); co("audit=pd.DataFrame({'channel':np.repeat(['email','phone','store','social'],50),'remedy':np.random.default_rng(23).choice(['Repair','Replacement','Refund'],200,p=[.42,.34,.24])})\nrates,disparity=fairness_audit(audit); display(rates,pd.Series({'remedy_disparity':disparity}).to_frame('audit'))")
md('## 12 · Find repeated complaints\nProduct, component, timing and description reveal possible shared failures.')
core('cluster_signal'); co("complaints.query(\"systemic_cluster!='none'\").groupby(['product','systemic_cluster']).size().rename('complaints').to_frame()")
md('## 13 · Early-defect warning\nRecommend investigation when an unusual cluster grows.')
core('fig_systemic'); co("days=np.arange(1,31); counts=np.maximum(0,np.round(np.linspace(1,14,30)+np.sin(days/3))).astype(int); fig_systemic(days,counts).show(); pd.Series({'observed':int(counts[-1]),'expected':'1–3','recommended_action':'Product-safety investigation','confidence':'Moderate — some serial numbers missing'})")
md('## 14 · Complaint ownership\nEvery case receives one owner, supporting teams, a deadline and one next action.')
core('recommend'); co("result=recommend(Complaint()); pd.Series({k:v for k,v in result.items() if k not in ['documents','remedies']})")
md('## 15 · Resolution verification\nInitiating a remedy is not completing it.')
core('resolution_check'); co("checks,may_close=resolution_check(True,False,True,True,False); display(checks.to_frame(),pd.Series({'may_close':may_close}).to_frame('decision'))")
md('## 16 · Final complaint control room\nChange the facts and watch urgency, ownership, evidence and deadlines respond.')
co("text_w=widgets.Textarea(value=Complaint().text,description='Complaint'); contacts_w=widgets.IntSlider(value=3,min=0,max=8,description='Contacts'); days_w=widgets.IntSlider(value=5,min=0,max=30,description='Days open'); invoice_w=widgets.Checkbox(value=True,description='Invoice'); video_w=widgets.Checkbox(value=True,description='Video'); serial_w=widgets.Checkbox(value=False,description='Serial'); out=widgets.Output()\ndef redraw(*_):\n    with out:\n        clear_output(wait=True); c=Complaint(text=text_w.value,previous_contacts=contacts_w.value,days_open=days_w.value,invoice_available=invoice_w.value,video_available=video_w.value,serial_available=serial_w.value); r=recommend(c)\n        display(pd.Series({'priority':r['priority'],'owner':r['owner'],'supporting':', '.join(r['supporting']),'missing':', '.join(r['missing']),'next action':r['next_action'],'deadline hours':r['deadline_hours']}).to_frame('value')); display(r['documents'])\nfor w in [text_w,contacts_w,days_w,invoice_w,video_w,serial_w]: w.observe(redraw,'value')\ndisplay(widgets.VBox([text_w,widgets.HBox([contacts_w,days_w]),widgets.HBox([invoice_w,video_w,serial_w])]),out); redraw()")
md('## Final simulated comparison\nMeasure resolution, transfers, repeat contacts, missed urgency and fairness exceptions.')
core('compare_systems'); core('fig_compare'); co("comparison=compare_systems(); fig_compare(comparison).show(); comparison")
md('## What this simulation may claim\n\nIt can compare complaint workflows inside a fictitious world. It cannot interpret consumer law, invent policy, deny statutory rights, confirm a product defect or close a real case.\n\n### Rules that do not move\n\n- Calm wording never suppresses a safety signal.\n- Protected attributes never reduce remedies.\n- Sensitive or uncertain cases receive human review.\n- Ask only for necessary evidence.\n- Give every case one accountable owner.\n- Close only after remedy and required investigation are verified.')
# One anchor near the top; each lesson names the step to open in the illustration tab.
# Colab opens a fresh tab per link click, so per-cell links are deliberately NOT emitted.
_STEPS=['Start', 'Urgency is not anger', 'Routing', 'Minimum evidence', 'Fair remedy', 'Systemic warning', 'Resolution check', 'Benchmark']
_SMAP={1: 1, 2: 1, 3: 2, 4: 2, 5: 2, 6: 2, 7: 3, 8: 4, 9: 5, 10: 5, 11: 5, 12: 6, 13: 6, 14: 3, 15: 7, 16: 8}
_FINALS={'Final simulated comparison': 8}
import re as _re
for _cell in cells:
    if _cell["cell_type"]!="markdown": continue
    _src=_cell["source"] if isinstance(_cell["source"],str) else "".join(_cell["source"])
    _m=_re.match(r"##\s+(\d+)\s+·",_src.lstrip())
    _step=_SMAP.get(int(_m.group(1))) if _m else next(
        (_v for _k,_v in _FINALS.items() if _src.lstrip().startswith("## "+_k)),None)
    if _step:
        _cell["source"]=_src.rstrip()+"\n\n> 🎬 **Illustration tab →** step %d · *%s*\n"%(_step,_STEPS[_step-1])
nb={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3'},'colab':{'name':'Complaint_Rescue_AI.ipynb','provenance':[]}},'nbformat':4,'nbformat_minor':5}
ROOT.joinpath('Complaint_Rescue_AI.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1),encoding='utf-8'); print(f'Wrote Complaint_Rescue_AI.ipynb: {len(cells)} cells')
