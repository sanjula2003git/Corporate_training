"""Build Bakery_Rescue_AI.ipynb. Run: py -3 -X utf8 build_nb.py"""
from pathlib import Path
import ast
import nbformat as nbf
from nbformat.v4 import new_notebook,new_markdown_cell,new_code_cell
ROOT=Path(__file__).resolve().parent;cells=[]
def md(s):cells.append(new_markdown_cell(s.strip()))
def co(s):cells.append(new_code_cell(s.strip()))
CORE_SOURCE=(ROOT/"bakery.py").read_text(encoding="utf-8");CORE_LINES=CORE_SOURCE.splitlines();CORE_TREE=ast.parse(CORE_SOURCE)
CORE_BLOCKS={n.name:"\n".join(CORE_LINES[n.lineno-1:n.end_lineno]) for n in CORE_TREE.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
FIRST_DEF=min(n.lineno for n in CORE_TREE.body if isinstance(n,ast.FunctionDef));CORE_BLOCKS["__preamble__"]="\n".join(CORE_LINES[:FIRST_DEF-1])
def core(*names):co("\n\n".join(CORE_BLOCKS[n] for n in names))

md(r"""
# 🥐 Sell It, Share It, Don’t Waste It
### Building an AI Bakery Rescue System

At 5 PM, 38 vegetable sandwiches remain. Rain has reduced footfall. The bakery closes in three
hours, and a shelter can collect at 7:15 PM.

**Should the bakery maintain the price, discount, bundle, donate, or stop production?**

This is not a profit-only optimizer. It balances profit, customers served and social value against
food waste and lost sales.

> ⚠️ Everything here is simulated. The controller uses one truthful public price for everyone in
> the same period. It never sells or donates food after the approved safe period.

### Research question

Can an AI system reduce bakery food waste while maintaining profit by coordinating transparent
discounts, production decisions and scheduled donations better than fixed-price and closing-time policies?
""")
md('🎬 **The illustrated version — open it once.**\n\n[Open the Bakery Rescue illustration app in a second tab](https://bakery-rescue-ai.streamlit.app/?stage=start) and leave it open beside this notebook.\n\nEvery lesson below carries a line like *"🎬 Illustration tab → step 5 · *Whose Definition Of Best?*"*. That names the page to open from\nthe app\'s **Learning journey** list, then move with its own ◀ ▶ buttons. There is deliberately no second link to click: Colab gives every link click a brand-new browser tab,\nso one anchor here keeps you at two tabs instead of sixty.\n')
md("""
### Contents

1. Monday morning at the bakery
2. Customers arrive
3. Fixed-price strategy
4. Closing-time discount
5. Price elasticity
6. Create the hourly dataset
7. Predict next-hour demand
8. Predict remaining-day demand
9. Build the rule-based rescue system
10. Evaluate every possible action
11. Multi-objective optimization
12. Donation logistics
13. Stop-production decision
14. Customer behaviour and fairness
15. Unexpected events
16. Final bakery control room
""")
md("## Setup\n\nThe simulation is embedded so the notebook runs top to bottom in Colab with fixed seeds.")
co(r"""
# !pip install numpy pandas plotly scikit-learn ipywidgets
try:
    import plotly.graph_objects as go
    import sklearn
except ModuleNotFoundError:
    import micropip
    await micropip.install(["plotly", "scikit-learn", "ipywidgets", "nbformat"])
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error,mean_squared_error
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor,GradientBoostingRegressor
from IPython.display import display,clear_output
import ipywidgets as widgets
np.random.seed(7)
print("Ready.")
""")
core("__preamble__")

md(r"""
## 1 · Monday morning at the bakery

Five products begin with price, cost, opening stock, safe life, production time and disposal cost.
Before forecasting anything, calculate the trading result from ordinary inventory arithmetic.
""")
co("catalogue=pd.DataFrame(PRODUCTS).T;catalogue")
co(r"""
example=pd.DataFrame({"product":list(PRODUCTS),"produced":[50,42,48,28,44],"sold":[44,34,39,23,35]})
example["closing"]=example.produced-example.sold
example["revenue"]=[example.loc[i,"sold"]*PRODUCTS[p]["price"] for i,p in enumerate(example["product"])]
example["production_cost"]=[example.loc[i,"produced"]*PRODUCTS[p]["cost"] for i,p in enumerate(example["product"])]
example["wastage_cost"]=[example.loc[i,"closing"]*PRODUCTS[p]["disposal"] for i,p in enumerate(example["product"])]
example["gross_profit"]=example.revenue-example.production_cost-example.wastage_cost
example.set_index("product")
""")
md("**Read it like this.** Closing inventory is not automatically waste, but a short-life item beyond its safe window becomes both lost value and disposal cost.")

md(r"""
## 2 · Customers arrive

Demand changes with hour, weekday, weather, nearby events, footfall, price and product popularity.
The three daily peaks are generated rather than copied from real customers, so no personal data is used.
""")
core("demand_rate")
core("_layout","fig_demand")
co("fig_demand('Sandwich').show()")
co(r"""
hours=np.arange(7,21)
curves=pd.DataFrame({p:[demand_rate(p,h,"Monday") for h in hours] for p in PRODUCTS},index=hours)
curves.index.name="hour";curves.round(2)
""")

md(r"""
## 3 · Fixed-price strategy

Prices never change. This is transparent and simple, but inventory cannot react when observed demand
differs from the morning plan. It becomes the baseline every later controller must beat honestly.
""")
core("remaining_demand")
core("donation_feasible")
core("evaluate_action")
core("strategy_weights","recommend")
core("accounting_summary")
core("simulate_day")
co(r"""
fixed_rows,fixed_summary=simulate_day("Fixed price","Monday","Clear",7)
fixed_summary.round(2).to_frame("₹ or items")
""")

md(r"""
## 4 · Closing-time discount

A universal 30% reduction in the final hour may rescue some stock. It can also discount products that
would have sold at full price and leave shelters too little collection time.
""")
co(r"""
closing_rows,closing_summary=simulate_day("Last-hour discount","Monday","Clear",7)
pd.concat([fixed_summary.rename("Fixed price"),closing_summary.rename("Last-hour 30%")],axis=1).round(2)
""")
md("**The policy is consistent but not adaptive.** A predictable deep discount can also teach some customers to wait.")

md(r"""
## 5 · Understand price elasticity

\[
D(p)=D_0\left(\frac{p}{p_0}\right)^{-\epsilon}
\]

Bread has low elasticity; sandwiches and premium pastries react more strongly. Elasticity is a
product-level business assumption here—not a personal characteristic.
""")
core("fig_elasticity")
co("fig_elasticity().show()")
co(r"""
pd.DataFrame({"elasticity":{p:v["elasticity"] for p,v in PRODUCTS.items()},
              "demand at 20% discount":{p:.8**(-v["elasticity"]) for p,v in PRODUCTS.items()}}).round(2)
""")

md(r"""
## 6 · Create the hourly dataset

Each row is one product during one hour. The target is next-hour demand. The table contains business
context and aggregate shop conditions—not customer identity or protected characteristics.
""")
core("generate_dataset")
co(r"""
data=generate_dataset(70,7)
print(data.shape)
data.head()
""")
co(r"""
data.groupby(["product","hour"]).next_hour_demand.mean().unstack(0).round(1)
""")

md(r"""
## 7 · Predict next-hour demand

Compare a moving average, linear regression, tree, forest and gradient boosting. MAE and RMSE show
error size. Bias shows direction: persistent overprediction creates waste, while underprediction
creates stockouts and lost sales.
""")
co(r"""
features=["day","hour","product","opening_stock","remaining_stock","hours_to_close",
          "shelf_life_remaining","regular_price","current_discount","unit_cost","footfall",
          "rainfall","temperature","local_event","recent_sales_rate"]
cat=["day","product","footfall"];num=[x for x in features if x not in cat]
train=data[data.day_index<52];test=data[data.day_index>=52]
prep=ColumnTransformer([("num",StandardScaler(),num),("cat",OneHotEncoder(handle_unknown="ignore"),cat)])
models={"linear":LinearRegression(),"tree":DecisionTreeRegressor(max_depth=9,min_samples_leaf=18,random_state=7),
 "forest":RandomForestRegressor(n_estimators=120,max_depth=14,min_samples_leaf=4,n_jobs=-1,random_state=7),
 "gradient boosting":GradientBoostingRegressor(n_estimators=120,max_depth=3,random_state=7)}
pred={"moving average":test.recent_sales_rate.to_numpy()};fitted={}
for name,model in models.items():
    pipe=make_pipeline(prep,model);pipe.fit(train[features],train.next_hour_demand)
    fitted[name]=pipe;pred[name]=np.maximum(0,pipe.predict(test[features]))
pd.DataFrame([{"model":n,"MAE":mean_absolute_error(test.next_hour_demand,p),
 "RMSE":mean_squared_error(test.next_hour_demand,p)**.5,"bias (forecast−actual)":np.mean(p-test.next_hour_demand)} for n,p in pred.items()]).set_index("model").round(3)
""")

md(r"""
## 8 · Predict remaining-day demand

The rescue decision needs the total likely sales before the earlier of closing and the safe deadline:

\[
D_{remaining}=\sum_{t=now}^{deadline}\hat D_t,\qquad
S=\max(0,stock-D_{remaining}).
\]
""")
co(r"""
state=State()
forecast=remaining_demand(state);surplus=max(0,state.stock-forecast)
pd.Series({"remaining stock":state.stock,"forecast before deadline":forecast,
           "predicted surplus":surplus,"safe hours remaining":state.shelf_life_remaining}).round(1)
""")

md(r"""
## 9 · Build the rule-based rescue system

Rules are useful because a manager can read them. They struggle when high stock, rain, collection
time, margin, elasticity and a donation promise interact.
""")
co(r"""
def rescue_rule(state):
    surplus=max(0,state.stock-remaining_demand(state))
    if state.shelf_life_remaining<=0:return "unavailable"
    if donation_feasible(state) and state.shelf_life_remaining<3 and surplus>0:return "donate_reserve"
    if 20-state.hour<=2 and surplus>10:return "discount_20"
    if surplus<=0:return "maintain"
    return "promote"
print("Rule recommendation:",rescue_rule(state))
""")

md(r"""
## 10 · Evaluate every possible action

Every action is played forward against the same state. The table keeps money, waste, donation,
customers and lost sales visible instead of hiding them inside one score.
""")
core("fig_actions")
co(r"""
actions=pd.DataFrame([evaluate_action(state,a,strategy_weights("Balanced")) for a in ACTIONS])
actions[["action","public_price","expected_sales","profit","waste","donation","customers_served","lost_sales"]].set_index("action").round(1)
""")
co("fig_actions(actions).show()")

md(r"""
## 11 · Multi-objective optimization

\[
J=w_1P-w_2W+w_3D+w_4C-w_5L
\]

The weights expose business values. Profit-first, waste-first, balanced and community-first strategies
may select different feasible actions from exactly the same forecast.
""")
co(r"""
rows=[]
for strategy in ["Profit-first","Waste-first","Balanced","Community-first"]:
    r=recommend(state,strategy);rows.append(dict(strategy=strategy,action=r["action"],price=r["public_price"],
        profit=r["profit"],waste=r["waste"],donation=r["donation"],customers=r["customers_served"],utility=r["utility"]))
pd.DataFrame(rows).set_index("strategy").round(1)
""")
md("**The weights are not discovered facts.** They are policy choices that should be visible, reviewed and tested.")

md(r"""
## 12 · Donation logistics

A shelter needs capacity, an accepted product, a pickup time and at least two hours of safe life at
collection. Donation is planned before closing. Once promised, stock is reserved from late sales.
""")
co(r"""
shelters=pd.DataFrame([
 ("Station Shelter",40,3.2,19.25,["Bread","Sandwich"],2),
 ("Community Kitchen",28,5.8,18.75,["Bread","Croissant","Savoury roll"],2.5),
 ("Night Centre",18,2.1,20.0,["Sandwich","Cake slice"],3)],
 columns=["shelter","capacity","distance_km","pickup_hour","accepted_products","minimum_life"])
shelters
""")
co(r"""
state.promised_donation=10
late=evaluate_action(state,"discount_20",strategy_weights("Profit-first"))
pd.Series({"promised units":state.promised_donation,"units still reserved":late["donation"],
           "late action":late["action"],"collection feasible":donation_feasible(state)})
""")
md("**A promise is a constraint.** The controller cannot silently cancel it because a late customer offers a slightly higher contribution.")

md(r"""
## 13 · Stop-production decision

Marginal costing asks whether the next batch pays for itself:

\[
contribution=incremental\ sales\ revenue-batch\ cost-expected\ waste\ cost.
\]

Morning costs already incurred do not justify avoidable afternoon production.
""")
core("production_decision")
co(r"""
pd.DataFrame([production_decision(state,x) for x in (1,.5,0)]).set_index("batch_units").round(1)
""")

md(r"""
## 14 · Customer behaviour and fairness

Some customers buy immediately, respond to a discount, prefer a bundle, substitute or leave. A deep
discount may improve today while training future customers to wait.

Hard policy rules:

- One public price for comparable customers during the same period.
- No identity or protected characteristic is used.
- The original price is not inflated before a discount.
- Scarcity claims must match inventory.
- Deep-discount frequency is capped.
""")
co(r"""
def fairness_audit(price_log,regular_price):
    log=pd.DataFrame(price_log)
    return pd.Series({"one price per period":bool((log.groupby("hour").public_price.nunique()<=1).all()),
      "truthful reference price":bool((log.reference_price<=regular_price).all()),
      "deep-discount periods":int((log.public_price<.75*regular_price).sum()),
      "uses customer identity":False})
fairness_audit([dict(hour=17,public_price=90,reference_price=90),dict(hour=18,public_price=81,reference_price=90)],90)
""")

md(r"""
## 15 · Unexpected events

Now disturb the plan: sudden rain, a sports event, refrigerator failure, shelter cancellation,
ingredient inflation or a failed footfall sensor. The forecast may change; safety, fair pricing and
donation promises do not.
""")
co(r"""
scenarios={
 "normal":State(),"sudden rain":State(weather="Heavy_rain",rain_probability=.98),
 "festival":State(local_event=True,footfall="High"),"shelter unavailable":State(shelter_available=False),
 "refrigerator failure":State(shelf_life_remaining=1.2),"ingredient inflation":State(ingredient_cost_change=9),
 "footfall sensor failure":State(sensor_ok=False,footfall="Normal")}
shock_rows=[]
for name,s in scenarios.items():
    r=recommend(s,"Balanced");shock_rows.append(dict(scenario=name,action=r["action"],price=r["public_price"],
      forecast=r.get("forecast",0),waste=r.get("waste",0),donation=r.get("donation",0),production=r.get("production","Stop")))
pd.DataFrame(shock_rows).set_index("scenario").round(1)
""")

md(r"""
## 16 · Final bakery control room

Change product, day, weather, footfall, stock, time, shelter availability and strategy. The control
room recomputes one public decision and its explanation.
""")
co(r"""
product_w=widgets.Dropdown(options=list(PRODUCTS),value="Sandwich",description="Product")
day_w=widgets.Dropdown(options=list(DAYS),value="Monday",description="Day")
weather_w=widgets.Dropdown(options=list(WEATHER_FACTOR),value="Rain",description="Weather")
foot_w=widgets.Dropdown(options=["Low","Normal","High"],value="Low",description="Footfall")
stock_w=widgets.IntSlider(value=38,min=0,max=90,description="Stock")
hour_w=widgets.IntSlider(value=17,min=7,max=20,description="Hour")
life_w=widgets.FloatSlider(value=5,min=0,max=14,step=.5,description="Safe life")
shelter_w=widgets.Checkbox(value=True,description="Shelter available")
strategy_w=widgets.Dropdown(options=["Profit-first","Waste-first","Balanced","Community-first"],value="Balanced",description="Strategy")
out=widgets.Output()
def redraw(*_):
    with out:
        clear_output(wait=True)
        s=State(product=product_w.value,day=day_w.value,weather=weather_w.value,footfall=foot_w.value,
                stock=stock_w.value,hour=hour_w.value,shelf_life_remaining=life_w.value,shelter_available=shelter_w.value)
        r=recommend(s,strategy_w.value)
        display(pd.Series({"Recommended action":r["action"],"Public price":f"₹{r['public_price']:.0f}",
          "Expected sales":round(r.get("expected_sales",0),1),"Expected profit":round(r["profit"],0),
          "Predicted surplus":round(r.get("predicted_surplus",0),1),"Donation reserve":round(r.get("donation",0),1),
          "Waste risk":round(r.get("waste",0),1),"Safe life remaining":s.shelf_life_remaining,"Explanation":r.get("reason","")}))
        fig_actions(pd.DataFrame([evaluate_action(s,a,strategy_weights(strategy_w.value)) for a in ACTIONS])).show()
for w in [product_w,day_w,weather_w,foot_w,stock_w,hour_w,life_w,shelter_w,strategy_w]:w.observe(redraw,"value")
display(widgets.VBox([widgets.HBox([product_w,day_w,weather_w]),widgets.HBox([foot_w,stock_w,hour_w]),
                      widgets.HBox([life_w,shelter_w,strategy_w])]),out);redraw()
""")

md("## Seven-day strategy comparison\n\nEvery number below is simulated. The purpose is comparison, not a claim about a real bakery.")
core("simulate_week","fig_week")
co(r"""
week=simulate_week(("Fixed price","Last-hour discount","Balanced"),7)
week.set_index("Strategy").round(0)
""")
co("fig_week(week).show()")
md(r"""
## What this simulation may claim

It can demonstrate how forecasts, marginal costing, public discounts and early donation reservations
interact inside an invented bakery. It cannot establish real elasticity, shelter suitability or food
safety without validated local data and responsible human approval.

### Rules that do not move

- One truthful public price applies to everyone in the same period.
- Protected characteristics and customer identity are not inputs.
- Food is unavailable after its approved safe period and unusable food is never donated.
- Promised donations are protected.
- Scarcity and reference prices remain truthful.
- Accounting, waste, donation, customer and fairness outcomes stay visible separately.
""")

# One anchor near the top; each lesson names the step to open in the illustration tab.
# Colab opens a fresh tab per link click, so per-cell links are deliberately NOT emitted.
_STEPS=['Monday Morning At The Bakery', 'Customers Do Not Arrive Evenly', 'A Discount Changes Demand', 'Sell, Bundle, Promote Or Reserve', 'Whose Definition Of Best?', 'Donation Needs A Clock', 'Should We Bake Another Batch?', 'Do Not Train Everyone To Wait', 'The Forecast Is Allowed To Be Wrong', 'Seven Days, One Honest Ledger']
_SMAP={1: 1, 2: 2, 3: 1, 4: 3, 5: 3, 6: 2, 7: 2, 8: 2, 9: 4, 10: 4, 11: 5, 12: 6, 13: 7, 14: 8, 15: 9, 16: 10}
_FINALS={'Seven-day strategy comparison': 10}
import re as _re
for _cell in cells:
    if _cell["cell_type"]!="markdown": continue
    _src=_cell["source"] if isinstance(_cell["source"],str) else "".join(_cell["source"])
    _m=_re.match(r"##\s+(\d+)\s+·",_src.lstrip())
    _step=_SMAP.get(int(_m.group(1))) if _m else next(
        (_v for _k,_v in _FINALS.items() if _src.lstrip().startswith("## "+_k)),None)
    if _step:
        _cell["source"]=_src.rstrip()+"\n\n> 🎬 **Illustration tab →** step %d · *%s*\n"%(_step,_STEPS[_step-1])
nb=new_notebook(cells=cells,metadata={"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
 "language_info":{"name":"python","version":"3"},"colab":{"name":"Bakery_Rescue_AI.ipynb","provenance":[]}})
out=ROOT/"Bakery_Rescue_AI.ipynb";nbf.write(nb,out);print(f"Wrote {out.name}: {len(cells)} cells")
