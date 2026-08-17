"""Synthetic bakery economics and rescue controller for teaching only."""
from __future__ import annotations
from dataclasses import dataclass,asdict
import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go

COLORS=dict(bg="#0e1117",panel="#161b22",cyan="#4fc3f7",amber="#ffb74d",red="#ef5350",
            green="#66bb6a",purple="#ba68c8",grey="#8b949e",white="#e6edf3",blue="#42a5f5")
PRODUCTS={
 "Bread":dict(price=80,cost=36,opening=50,life=14,production_min=55,disposal=4,elasticity=.45,popularity=1.05,batch=20),
 "Croissant":dict(price=95,cost=43,opening=42,life=10,production_min=50,disposal=5,elasticity=1.15,popularity=.82,batch=16),
 "Sandwich":dict(price=90,cost=42,opening=48,life=8,production_min=35,disposal=6,elasticity=1.55,popularity=1.00,batch=18),
 "Cake slice":dict(price=140,cost=61,opening=28,life=12,production_min=70,disposal=7,elasticity=1.30,popularity=.62,batch=12),
 "Savoury roll":dict(price=75,cost=33,opening=44,life=9,production_min=40,disposal=5,elasticity=1.05,popularity=.90,batch=18),}
DAYS=("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday")
DAY_FACTOR=dict(Monday=.88,Tuesday=.92,Wednesday=.96,Thursday=1.,Friday=1.10,Saturday=1.28,Sunday=1.16)
WEATHER_FACTOR=dict(Clear=1.,Cloudy=.94,Rain=.72,Heavy_rain=.55,Hot=.86)
ACTIONS=("maintain","discount_5","discount_10","discount_20","discount_30","bundle","promote","donate_reserve")

@dataclass
class State:
    product:str="Sandwich"
    day:str="Monday"
    hour:int=17
    stock:int=38
    weather:str="Rain"
    rain_probability:float=.82
    footfall:str="Low"
    local_event:bool=False
    recent_sales_rate:float=4
    shelter_available:bool=True
    shelter_pickup_hour:float=19.25
    shelter_capacity:int=40
    shelf_life_remaining:float=5
    promised_donation:int=0
    ingredient_cost_change:float=0
    sensor_ok:bool=True

def demand_rate(product,hour,day="Monday",weather="Clear",footfall="Normal",event=False,
                price_ratio=1.,seed=7):
    p=PRODUCTS[product]; peak=4.4*np.exp(-((hour-9)/2.0)**2)+3.0*np.exp(-((hour-13)/2.4)**2)+3.8*np.exp(-((hour-18)/2.2)**2)
    foot={"Low":.62,"Normal":1.,"High":1.42}[footfall]
    base=(.7+peak)*p["popularity"]*DAY_FACTOR[day]*WEATHER_FACTOR[weather]*foot*(1.32 if event else 1.)
    return max(.05,base*price_ratio**(-p["elasticity"]))

def generate_dataset(days=70,seed=7):
    rng=np.random.default_rng(seed); rows=[]
    for d in range(days):
        day=DAYS[d%7]; weather=str(rng.choice(list(WEATHER_FACTOR),p=[.42,.22,.18,.08,.10])); event=rng.random()<.12
        for product,p in PRODUCTS.items():
            stock=p["opening"]+int(rng.integers(-6,8)); recent=0.
            for hour in range(7,21):
                footfall=str(rng.choice(["Low","Normal","High"],p=[.22,.60,.18]))
                discount=0.; expected=demand_rate(product,hour,day,weather,footfall,event,1.,seed+d)
                demand=int(rng.poisson(expected)); sales=min(stock,demand); start=stock; stock-=sales
                rows.append(dict(day=day,day_index=d,hour=hour,product=product,opening_stock=start,
                    remaining_stock=stock,hours_to_close=20-hour,shelf_life_remaining=max(0,p["life"]-(hour-7)),
                    regular_price=p["price"],current_discount=discount,unit_cost=p["cost"],footfall=footfall,
                    rainfall=weather in ("Rain","Heavy_rain"),weather=weather,temperature=float(rng.normal(27,4)),
                    local_event=int(event),recent_sales_rate=recent,next_hour_demand=demand))
                recent=.65*recent+.35*sales
    return pd.DataFrame(rows)

def remaining_demand(state:State,discount=0.,bundle=False):
    p=PRODUCTS[state.product]; deadline=min(20.,state.hour+state.shelf_life_remaining)
    total=0.
    weather="Heavy_rain" if state.rain_probability>.9 else state.weather
    for h in np.arange(state.hour,deadline,1):
        ratio=1-discount
        rate=demand_rate(state.product,h,state.day,weather,state.footfall,state.local_event,ratio)
        if bundle: rate*=1.22
        total+=rate
    # Recent local evidence gets half the weight.
    local=state.recent_sales_rate*max(0,deadline-state.hour)
    return .5*total+.5*local

def donation_feasible(state:State):
    time_left=state.shelter_pickup_hour-state.hour
    life_at_pickup=state.shelf_life_remaining-max(0,time_left)
    return state.shelter_available and time_left>=0 and life_at_pickup>=2

def evaluate_action(state:State,action,weights=None):
    p=PRODUCTS[state.product]; discount=0.; bundle=False; donation=0
    if action.startswith("discount_"): discount=int(action.split("_")[1])/100
    if action=="bundle": discount=1-(1.67/2); bundle=True
    forecast=remaining_demand(state,discount,bundle)
    sellable=max(0,state.stock-state.promised_donation)
    sales=min(sellable,forecast)
    if action=="promote": sales=min(sellable,forecast*1.12)
    surplus=max(0,state.stock-sales-state.promised_donation)
    if action=="donate_reserve" and donation_feasible(state): donation=min(surplus,state.shelter_capacity)
    donation=max(donation,state.promised_donation)  # a promise is never reclaimed for a small late sale
    waste=max(0,state.stock-sales-donation)
    price=p["price"]*(1-discount); revenue=sales*price
    production_cost=state.stock*(p["cost"]+state.ingredient_cost_change)
    disposal=waste*p["disposal"]; transport=120 if donation>0 else 0
    profit=revenue-production_cost-disposal-transport
    lost=max(0,forecast-sellable); customers=sales+(donation*.65)
    discount_cost=sales*p["price"]*discount
    w=weights or dict(profit=1.,waste=90.,donation=18.,customers=8.,lost=25.)
    utility=w["profit"]*profit-w["waste"]*waste+w["donation"]*donation+w["customers"]*customers-w["lost"]*lost
    safe=state.shelf_life_remaining>0
    return dict(action=action,discount=discount,public_price=round(price,2),expected_sales=float(sales),
        expected_revenue=float(revenue),profit=float(profit),remaining=float(waste),donation=float(donation),
        waste=float(waste),customers_served=float(customers),lost_sales=float(lost),discount_cost=float(discount_cost),
        disposal_cost=float(disposal),transport_cost=float(transport),forecast=float(forecast),utility=float(utility),safe=safe)

def strategy_weights(strategy):
    return {"Profit-first":dict(profit=1.,waste=25.,donation=2.,customers=3.,lost=8.),
      "Waste-first":dict(profit=.35,waste=160.,donation=22.,customers=5.,lost=10.),
      "Balanced":dict(profit=.75,waste=95.,donation=18.,customers=8.,lost=22.),
      "Community-first":dict(profit=.40,waste=105.,donation=55.,customers=12.,lost=18.)}[strategy]

def recommend(state:State,strategy="Balanced"):
    if state.shelf_life_remaining<=0:
        return dict(action="unavailable",reason="The approved safe sale period has ended.",public_price=0,
                    expected_sales=0,profit=0,waste=state.stock,donation=0,forecast=0,utility=-math.inf)
    rows=[evaluate_action(state,a,strategy_weights(strategy)) for a in ACTIONS]
    # Deep discount frequency is limited by policy outside this one-step controller.
    feasible=[r for r in rows if r["safe"] and r["public_price"]>=PRODUCTS[state.product]["cost"]*.92]
    best=max(feasible,key=lambda r:r["utility"])
    surplus=max(0,state.stock-best["forecast"])
    production="Stop" if surplus>PRODUCTS[state.product]["batch"]*.35 else "Review small batch"
    best.update(reason=f"{state.stock} remain; {best['forecast']:.0f} expected before deadline; public price ₹{best['public_price']:.0f}.",
                predicted_surplus=float(surplus),production=production)
    return best

def production_decision(state:State,batch_fraction=1.):
    p=PRODUCTS[state.product]; qty=int(p["batch"]*batch_fraction); demand=remaining_demand(state)
    incremental_sales=min(qty,max(0,demand-state.stock)); leftover=qty-incremental_sales
    contribution=incremental_sales*p["price"]-qty*(p["cost"]+state.ingredient_cost_change)-leftover*p["disposal"]
    return dict(batch_units=qty,incremental_sales=incremental_sales,expected_leftover=leftover,
                expected_contribution=contribution,decision="Produce" if contribution>0 else "Stop")

def accounting_summary(rows):
    df=pd.DataFrame(rows)
    revenue=df.expected_revenue.sum(); cogs=sum(PRODUCTS[p]["cost"]*q for p,q in zip(df["product"],df["produced"]))
    return pd.Series({"Sales revenue":revenue,"Less: cost of goods sold":cogs,
      "Gross profit":revenue-cogs,"Less: discount cost":df.discount_cost.sum(),
      "Less: disposal cost":df.disposal_cost.sum(),"Less: donation transport":df.transport_cost.sum(),
      "Net operating contribution":revenue-cogs-df.disposal_cost.sum()-df.transport_cost.sum(),
      "Closing usable inventory":df.closing.sum(),"Food discarded":df.waste.sum(),"Food donated":df.donation.sum()})

def simulate_day(strategy="Balanced",day="Monday",weather="Clear",seed=7,shelter=True):
    rng=np.random.default_rng(seed); rows=[]
    for product,p in PRODUCTS.items():
        stock=p["opening"]; produced=stock; deep_used=False; promised=0
        revenue=0.; discount_cost=0.; customers=0; lost_sales=0.
        for hour in range(7,21):
            state=State(product=product,day=day,hour=hour,stock=stock,weather=weather,
                        rain_probability=.8 if weather=="Rain" else .1,footfall="Normal",local_event=False,
                        recent_sales_rate=max(1,demand_rate(product,hour-1,day,weather)),shelter_available=shelter,
                        shelf_life_remaining=max(0,p["life"]-(hour-7)),promised_donation=promised)
            if strategy=="Fixed price": action="maintain"
            elif strategy=="Last-hour discount": action="discount_30" if hour==19 and not deep_used else "maintain"
            elif strategy=="Stock rule": action="discount_20" if hour>=17 and stock>p["batch"] else "maintain"
            else: action=recommend(state,strategy if strategy in ("Profit-first","Waste-first","Balanced","Community-first") else "Balanced")["action"]
            if action=="discount_30": deep_used=True
            result=evaluate_action(state,action,strategy_weights("Balanced"))
            potential=int(rng.poisson(max(.05,result["expected_sales"]/max(1,20-hour))))
            available=max(0,stock-promised); hourly=min(available,potential)
            stock-=hourly; customers+=hourly; lost_sales+=max(0,potential-available)
            revenue+=hourly*result["public_price"]
            discount_cost+=hourly*(p["price"]-result["public_price"])
            if action=="donate_reserve": promised=max(promised,int(result["donation"]))
        donation=min(stock,promised) if shelter else 0; waste=max(0,stock-donation)
        rows.append(dict(product=product,produced=produced,expected_revenue=revenue,discount_cost=discount_cost,
                         disposal_cost=waste*p["disposal"],transport_cost=120 if donation else 0,closing=stock,
                         waste=waste,donation=donation,customers=customers,lost_sales=lost_sales))
    summary=accounting_summary(rows); summary["Customers served"]=sum(r["customers"] for r in rows)
    return pd.DataFrame(rows),summary

def simulate_week(strategies=("Fixed price","Last-hour discount","Balanced"),seed=7):
    rows=[]
    for strategy in strategies:
        totals=[]
        for i,day in enumerate(DAYS): totals.append(simulate_day(strategy,day,"Rain" if day=="Tuesday" else "Clear",seed+i)[1])
        t=pd.concat(totals,axis=1).sum(axis=1)
        rows.append(dict(Strategy=strategy,Revenue=t["Sales revenue"],Gross_profit=t["Gross profit"],
                         Discarded=t["Food discarded"],Donated=t["Food donated"],Customers=t["Customers served"]))
    return pd.DataFrame(rows)

def _layout(fig,height=420,**kw):
    fig.update_layout(height=height,paper_bgcolor=COLORS["bg"],plot_bgcolor=COLORS["bg"],font_color=COLORS["white"],
                      margin=dict(l=50,r=20,t=55,b=45),legend=dict(bgcolor="rgba(0,0,0,0)"),**kw)
    fig.update_xaxes(gridcolor="#21262d");fig.update_yaxes(gridcolor="#21262d");return fig

def fig_demand(product="Sandwich"):
    fig=go.Figure()
    for day,color in zip(("Monday","Friday","Saturday"),(COLORS["cyan"],COLORS["amber"],COLORS["green"])):
        hours=np.arange(7,21); vals=[demand_rate(product,h,day) for h in hours]
        fig.add_scatter(x=hours,y=vals,name=day,line=dict(color=color,width=3))
    return _layout(fig,title=f"{product}: demand changes through the day",xaxis_title="hour",yaxis_title="expected units/hour")

def fig_elasticity():
    fig=go.Figure(); ratios=np.linspace(.7,1,31)
    for product,color in zip(PRODUCTS,(COLORS["cyan"],COLORS["purple"],COLORS["green"],COLORS["amber"],COLORS["blue"])):
        e=PRODUCTS[product]["elasticity"];fig.add_scatter(x=ratios*100,y=ratios**(-e),name=product,line=dict(color=color,width=2.5))
    return _layout(fig,title="A discount changes products differently",xaxis_title="price (% of regular)",yaxis_title="demand multiplier")

def fig_actions(table):
    fig=go.Figure()
    fig.add_bar(x=table.action,y=table.profit,name="expected profit",marker_color=COLORS["cyan"])
    fig.add_bar(x=table.action,y=-table.waste*50,name="waste penalty (−50/item)",marker_color=COLORS["red"])
    fig.add_bar(x=table.action,y=table.donation*20,name="donation value (20/item)",marker_color=COLORS["green"])
    return _layout(fig,barmode="relative",title="Every action exposes a different trade-off",yaxis_title="simulated ₹ / value units")

def fig_week(table):
    fig=go.Figure()
    fig.add_bar(x=table.Strategy,y=table.Gross_profit,name="gross profit",marker_color=COLORS["cyan"])
    fig.add_bar(x=table.Strategy,y=table.Discarded*100,name="discarded × ₹100",marker_color=COLORS["red"])
    fig.add_bar(x=table.Strategy,y=table.Donated*100,name="donated × ₹100",marker_color=COLORS["green"])
    return _layout(fig,barmode="group",title="Seven simulated days: money, waste and community value")
