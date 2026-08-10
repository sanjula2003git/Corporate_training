"""Generate Metro_Evacuation_Flood_LSTM.ipynb from the shared teaching scaffold."""
from pathlib import Path
import json, sys, textwrap

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
import bridge

APP = "https://metro-evacuation-flood.streamlit.app"


def md(text):
    return {"cell_type":"markdown","metadata":{},"source":textwrap.dedent(text).strip().splitlines(True)}


def code(text):
    return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],
            "source":textwrap.dedent(text).strip().splitlines(True)}


def lesson(step, number, technical_cells):
    phase = bridge.PHASES[step["phase"]]
    i = number - 1
    prev_step = bridge.STEPS[i-1] if i > 0 else None
    next_step = bridge.STEPS[i+1] if i < len(bridge.STEPS)-1 else None
    nav = []
    if prev_step:
        nav.append(f"◀ [Previous: {prev_step['civil']}]({APP}/?stage={prev_step['id']})")
    nav.append(f"[Project overview]({APP}/?stage=start)")
    if next_step:
        nav.append(f"[Next: {next_step['civil']}]({APP}/?stage={next_step['id']}) ▶")
    part12 = md(f"""
    ---
    # {number}. {step['civil']}
    ### Phase {step['phase']+1} of {len(bridge.PHASES)} · {phase[0]}

    ## Part 1 · On the metro
    {step['site']}

    ## Part 2 · The engineering challenge
    {step['challenge']}

    """)
    part3 = md(f"""
    ## Part 3 · Where the AI comes in
    {step['ai_link']}

    **Civil Engineering:** {step['civil']} → **AI:** {step['ai']} → **Technical mechanism:** `{step['tech']}`

    > 🎬 **See this illustrated and interactive:** [{APP}/?stage={step['id']}]({APP}/?stage={step['id']})

    ## Part 4 · Technical explanation
    """)
    closer = md(f"""
    ## Part 5 · What you just built

    **In the notebook:** {step['notebook']}

    **Takeaway:** {step['takeaway']}

    {' &nbsp;|&nbsp; '.join(nav)}
    """)
    return [part12, part3, *technical_cells, closer]


cells = [
md(f"""
# 🚇 AI That Predicts Which Metro Evacuation Route Will Flood
## Civil Engineering + Deep Learning with an LSTM

A normal evacuation route may look safe now and flood while passengers are using it. This notebook predicts **water depth five minutes ahead** for two routes and recommends the safer exit.

> This is an educational decision-support demonstration. The safety bands below are project assumptions, not universal evacuation standards. A real deployment requires site-specific hydraulic analysis, approved operating procedures, sensor redundancy, validation, and human command.

👉 **Open the interactive companion:** [{APP}]({APP}/?stage=start)
"""),
md(f"""
## The complete system

Five measurements each minute → previous ten minutes → LSTM → route depth at +5 minutes → project safety band → compare Route A and Route B → recommend exit.

| Input | Unit | Meaning |
|---|---:|---|
| Rainfall intensity | mm/hr | Water supplied by the storm |
| Entrance water level | cm | Water near the station entrance |
| Tunnel water level | cm | Water entering through the tunnel |
| Drainage flow | L/s | Water removed by drains |
| Current route water level | cm | Water already on the route |

**Output:** route water depth in centimetres, five minutes later.

## Interactive learning journey

{chr(10).join(f"- [{s['civil']}]({APP}/?stage={s['id']}) — {s['ai']}" for s in bridge.STEPS)}
"""),
code("""
# Colab setup: uncomment only if your runtime is missing a package.
# !pip -q install tensorflow scikit-learn pandas matplotlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Input, LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import tensorflow as tf

SEED = 42
np.random.seed(SEED)
tf.random.set_seed(SEED)
FEATURES = ["rainfall_mm_hr", "entrance_water_cm", "tunnel_water_cm", "drainage_l_s", "route_water_cm"]
LOOKBACK, HORIZON = 10, 5
print("Ready: 5 inputs, 10-minute history, 5-minute forecast")
""")]

technical = {}
technical["station"] = [md("""
At 10:03, Route A can contain only 4 cm of water and appear usable. If rainfall, entrance inflow, and tunnel inflow are rising while drainage is weakening, its condition at 10:08 is the relevant engineering question.

```
             EXIT A
                ↑
           ROUTE A
                ↑
PLATFORM ───────┤
                ↓
           ROUTE B
                ↓
             EXIT B
```
""")]

technical["inputs"] = [code("""
def generate_route(route, minutes=1440, seed=42):
    rng = np.random.default_rng(seed)
    t = np.arange(minutes)
    # Several smooth storm cells plus instrument noise.
    rain = np.zeros(minutes)
    for centre, width, peak in [(260,55,72),(690,80,105),(1120,65,82)]:
        rain += peak*np.exp(-0.5*((t-centre)/width)**2)
    rain = np.clip(rain + rng.normal(0,2.2,minutes), 0, None)
    entrance = np.zeros(minutes); tunnel = np.zeros(minutes); drainage = np.zeros(minutes); depth = np.zeros(minutes)
    bias = 1.0 if route == "A" else .68
    protection = 1.0 if route == "A" else 1.25
    for i in range(1, minutes):
        entrance[i] = max(0, .86*entrance[i-1] + .055*rain[i-2] + rng.normal(0,.35))*bias
        tunnel[i] = max(0, .91*tunnel[i-1] + .026*rain[i-3] + rng.normal(0,.20))*bias
        drainage[i] = np.clip((17-.075*rain[i]+rng.normal(0,.6))*protection, 3, 24)
        inflow = .050*rain[i] + .13*entrance[i] + .18*tunnel[i]
        depth[i] = max(0, .94*depth[i-1] + .16*inflow - .115*drainage[i] + rng.normal(0,.16))
    return pd.DataFrame({"minute":t,"route":route,"rainfall_mm_hr":rain,
                         "entrance_water_cm":entrance,"tunnel_water_cm":tunnel,
                         "drainage_l_s":drainage,"route_water_cm":depth})

data = pd.concat([generate_route("A", seed=42), generate_route("B", seed=84)], ignore_index=True)
print(data.shape)
data.head()
"""), code("""
fig, ax = plt.subplots(2,1,figsize=(13,7),sharex=True)
for route, colour in [("A","crimson"),("B","seagreen")]:
    d=data[data.route==route]
    ax[0].plot(d.minute,d.rainfall_mm_hr,label=f"Route {route}",alpha=.8,color=colour)
    ax[1].plot(d.minute,d.route_water_cm,label=f"Route {route}",color=colour)
ax[0].set_ylabel("Rainfall (mm/hr)"); ax[1].set_ylabel("Route depth (cm)"); ax[1].set_xlabel("Minute")
for a in ax: a.grid(alpha=.2); a.legend()
plt.tight_layout(); plt.show()
""")]

technical["prepare"] = [code("""
# Demonstrate realistic short sensor gaps, then repair them per route.
dirty = data.copy()
rng = np.random.default_rng(7)
gap_rows = rng.choice(dirty.index, size=18, replace=False)
dirty.loc[gap_rows, "tunnel_water_cm"] = np.nan
print("Missing before cleaning:", dirty[FEATURES].isna().sum().sum())
clean = dirty.sort_values(["route","minute"]).copy()
clean[FEATURES] = clean.groupby("route")[FEATURES].transform(lambda s: s.interpolate().bfill().ffill())
print("Missing after cleaning :", clean[FEATURES].isna().sum().sum())
""")]

technical["sequences"] = [code("""
def make_raw_sequences(frame, lookback=LOOKBACK, horizon=HORIZON):
    X, y, routes, target_minutes = [], [], [], []
    for route, d in frame.groupby("route", sort=False):
        d=d.sort_values("minute").reset_index(drop=True)
        values=d[FEATURES].to_numpy(dtype=np.float32)
        for end in range(lookback, len(d)-horizon):
            X.append(values[end-lookback:end])
            y.append(values[end+horizon-1, FEATURES.index("route_water_cm")])
            routes.append(route); target_minutes.append(int(d.loc[end+horizon-1,"minute"]))
    return np.array(X), np.array(y), np.array(routes), np.array(target_minutes)

X_raw,y_raw,route_id,target_minute=make_raw_sequences(clean)
print("X:",X_raw.shape,"= examples × 10 minutes × 5 inputs")
print("y:",y_raw.shape,"= depth 5 minutes later")
""")]

technical["lstm"] = [code("""
# Time-ordered split: earlier storm history trains; later history tests.
train_mask = target_minute < 950
val_mask = (target_minute >= 950) & (target_minute < 1160)
test_mask = target_minute >= 1160

# Fit scaling on training measurements only.
x_scaler=MinMaxScaler().fit(X_raw[train_mask].reshape(-1,len(FEATURES)))
y_scaler=MinMaxScaler().fit(y_raw[train_mask].reshape(-1,1))
def sx(x): return x_scaler.transform(x.reshape(-1,len(FEATURES))).reshape(x.shape)
X_scaled=sx(X_raw); y_scaled=y_scaler.transform(y_raw.reshape(-1,1))

model=Sequential([
    Input(shape=(LOOKBACK,len(FEATURES))),
    LSTM(32),
    Dropout(.15),
    Dense(16,activation="relu"),
    Dense(1)
])
model.compile(optimizer="adam",loss="mae",metrics=["mae"])
model.summary()
""")]

technical["training"] = [code("""
early=EarlyStopping(monitor="val_loss",patience=7,restore_best_weights=True)
history=model.fit(X_scaled[train_mask],y_scaled[train_mask],
                  validation_data=(X_scaled[val_mask],y_scaled[val_mask]),
                  epochs=60,batch_size=64,callbacks=[early],verbose=0)
print("Epochs run:",len(history.history["loss"]))
plt.figure(figsize=(9,4)); plt.plot(history.history["loss"],label="train MAE")
plt.plot(history.history["val_loss"],label="validation MAE"); plt.xlabel("Epoch"); plt.ylabel("Scaled MAE")
plt.grid(alpha=.2); plt.legend(); plt.show()
""")]

technical["forecast"] = [code("""
pred_scaled=model.predict(X_scaled[test_mask],verbose=0)
pred_cm=y_scaler.inverse_transform(pred_scaled).ravel()
actual_cm=y_raw[test_mask]
mae=mean_absolute_error(actual_cm,pred_cm)
rmse=mean_squared_error(actual_cm,pred_cm)**0.5
print(f"Test MAE : {mae:.2f} cm")
print(f"Test RMSE: {rmse:.2f} cm")

n=min(260,len(pred_cm)); plt.figure(figsize=(13,4))
plt.plot(actual_cm[:n],label="Actual",color="black",linewidth=2)
plt.plot(pred_cm[:n],label="LSTM predicted",color="deepskyblue")
plt.ylabel("Route water depth (cm)"); plt.xlabel("Successive test sequences")
plt.grid(alpha=.2); plt.legend(); plt.show()
""")]

technical["thresholds"] = [code("""
def safety_band(depth_cm):
    # EDUCATIONAL PROJECT ASSUMPTION — not a universal evacuation standard.
    if depth_cm < 10: return "SAFE"
    if depth_cm <= 20: return "WARNING"
    return "UNSAFE"

for depth in [6,15,28]: print(depth,"cm ->",safety_band(depth))
""")]

technical["routes"] = [code("""
def latest_forecast(route):
    candidates=np.where(test_mask & (route_id==route))[0]
    idx=candidates[-1]
    prediction=y_scaler.inverse_transform(model.predict(X_scaled[idx:idx+1],verbose=0)).item()
    return prediction

route_a=latest_forecast("A"); route_b=latest_forecast("B")
def recommend(a,b):
    usable=[(d,r) for d,r in [(a,"A"),(b,"B")] if safety_band(d)!="UNSAFE"]
    if not usable: return "NO MODEL-APPROVED ROUTE — invoke emergency procedure"
    return "ROUTE "+min(usable)[1]

print(f"Route A after 5 min: {route_a:.1f} cm — {safety_band(route_a)}")
print(f"Route B after 5 min: {route_b:.1f} cm — {safety_band(route_b)}")
print("AI RECOMMENDATION:",recommend(route_a,route_b))
"""), md("""
```
             EXIT A
               ↑
          ROUTE A ❌
        Predicted: 28 cm
               ↑
            PLATFORM
               ↓
          ROUTE B ✓
         Predicted: 6 cm
               ↓
             EXIT B

AI RECOMMENDATION: EVACUATE USING ROUTE B
```
""")]

technical["audit"] = [code("""
def bands(values): return np.array([safety_band(v) for v in values])
actual_band=bands(actual_cm); predicted_band=bands(pred_cm)
band_accuracy=(actual_band==predicted_band).mean()
unsafe_as_safe=((actual_band=="UNSAFE") & (predicted_band=="SAFE")).sum()
print(f"MAE                 : {mae:.2f} cm")
print(f"RMSE                : {rmse:.2f} cm")
print(f"Safety-band accuracy: {band_accuracy:.1%}")
print(f"UNSAFE predicted SAFE: {unsafe_as_safe}")
print("\\nA real project would also test sensor failures, rare extreme storms, uncertainty, hydraulic-model consistency, latency, alarms, and evacuation drills.")
""")]

for i,step in enumerate(bridge.STEPS,1):
    cells.extend(lesson(step,i,technical[step["id"]]))

cells.append(md("""
---
# Final engineering conclusion

The LSTM predicts a physical quantity—route water depth five minutes ahead—from the previous ten minutes of five measurements. A separate, transparent project rule assigns a safety band. Forecasts for Routes A and B are compared, and the control room receives an actionable recommendation.

The system does **not** replace evacuation authorities or guarantee safety. Its meaningful contribution is earlier warning: it can reject a route that looks safe now but is forecast to flood before passengers complete the evacuation.
"""))

nb={"cells":cells,"metadata":{"colab":{"name":"Metro_Evacuation_Flood_LSTM.ipynb","provenance":[],"toc_visible":True},
    "kernelspec":{"display_name":"Python 3","name":"python3"},"language_info":{"name":"python"}},"nbformat":4,"nbformat_minor":0}
out=BASE/"Metro_Evacuation_Flood_LSTM.ipynb"
out.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+"\n",encoding="utf-8")
print(f"Wrote {out} with {len(cells)} cells ({sum(c['cell_type']=='code' for c in cells)} code)")
