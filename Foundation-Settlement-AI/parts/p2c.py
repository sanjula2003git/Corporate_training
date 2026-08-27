
step("📋", "Record 1 — the borehole log",
     "A hole in the ground and what came out of it, layer by layer. It is exact, and it is exact at one point only.")

co(r'''
# The five boreholes drilled at the Northgate warehouse before construction.

log = BOREHOLES[BOREHOLES.site == DEMO].copy()
log["log_text"] = [f"0.00-{f:.2f} m loose fill / {f:.2f}-{t:.2f} m medium dense sand / "
                   + (f"{t:.2f}-{t + c:.2f} m SOFT CLAY / below dense sand"
                      if c > 0.3 else "below dense sand, no clay")
                   for f, t, c in zip(log.fill_thk_m, log.clay_top_m, log.clay_thk_m)]
print(log[["bh_id", "x_m", "y_m", "log_text"]].to_string(index=False))

fig = go.Figure()
for i, r in enumerate(log.itertuples()):
    bars = [(0, r.fill_thk_m, "Loose fill", "#c9a227"),
            (r.fill_thk_m, r.clay_top_m, "Medium dense sand", "#d9b382"),
            (r.clay_top_m, r.clay_top_m + r.clay_thk_m, "Soft clay", "#7d5a3c"),
            (r.clay_top_m + r.clay_thk_m, 14.0, "Dense sand", "#a8763e")]
    for top, bot, name, colr in bars:
        if bot - top <= 0.01:
            continue
        fig.add_trace(go.Bar(x=[r.bh_id], y=[bot - top], base=[-bot], marker_color=colr,
                             name=name, legendgroup=name, showlegend=(i == 0),
                             hovertemplate=f"{name}<br>%{{base:.1f}} to " + f"{-top:.1f} m<extra></extra>"))
fig.update_layout(barmode="stack", title="Northgate warehouse: what the five boreholes found",
                  yaxis_title="Depth (m below ground)", height=430, template=PLT)
fig.show()
''')

step("🔩", "Record 2 — the SPT profile",
     "A hammer is dropped on a rod. The blows needed to drive it 300 mm is N. Low N means the ground is easy to push through, and easy to push through means weak.")

co(r'''
# SPT blow counts down each borehole, generated from the layers it passed through.

rng = np.random.default_rng(5)
rows = []
for r in BOREHOLES.itertuples():
    for z in np.arange(1.5, 14.1, 1.5):
        if z <= r.fill_thk_m:
            n = rng.normal(7, 1.5)
        elif z <= r.clay_top_m:
            n = rng.normal(r.n60_bearing, 3)
        elif z <= r.clay_top_m + r.clay_thk_m:
            n = rng.normal(3.5, 1.0)                       # soft clay: the rod almost falls
        else:
            n = rng.normal(38 + 1.2 * (z - r.clay_top_m), 4)
        rows.append(dict(site=r.site, bh_id=r.bh_id, depth_m=z, n_value=max(1, round(n))))
SPT = pd.DataFrame(rows)

d = SPT[SPT.site == DEMO]
fig = go.Figure()
for bh, g in d.groupby("bh_id"):
    fig.add_trace(go.Scatter(x=g.n_value, y=-g.depth_m, mode="lines+markers", name=bh))
fig.add_vrect(x0=0, x1=8, fillcolor=RED, opacity=0.10, line_width=0,
              annotation_text="weak", annotation_position="top left")
fig.update_layout(title="SPT N against depth. The dip to N&lt;5 is the soft clay.",
                  xaxis_title="SPT N (blows per 300 mm)", yaxis_title="Depth (m)",
                  height=430, template=PLT)
fig.show()

print(SPT[SPT.site == DEMO].head(4).to_string(index=False))
''')

step("💧", "Record 3 — the piezometer",
     "A standpipe with a dip meter. It records how far below ground the water sits, month by month.")

co(r'''
# Two piezometers per site, monthly, for 32 months.

rng = np.random.default_rng(9)
rows = []
for sid, g in COLUMNS.groupby("site", sort=False):
    f = FIELDS[sid]
    base, drop = g.gw_depth_m.iloc[0], g.gw_drop_m.iloc[0]
    for pid, (px, py) in zip(["P1", "P2"], [(0.2 * f["W"], 0.25 * f["L"]), (0.8 * f["W"], 0.2 * f["L"])]):
        for m in range(1, 33):
            season = 0.35 * np.sin(2 * np.pi * m / 12.0)
            pumped = drop * np.clip((m - 6) / 12.0, 0, 1)        # dewatering, ramping in
            leak   = 0.0
            if sid == DEMO and pid == "P2" and m >= 10:
                leak = -0.9 * np.clip((m - 10) / 4.0, 0, 1)      # water table RISES near the leak
            rows.append(dict(site=sid, piezo_id=pid, x_m=px, y_m=py, month=m,
                             gw_depth_m=round(base + season + pumped + leak + rng.normal(0, 0.04), 2)))
PIEZO = pd.DataFrame(rows)

d = PIEZO[PIEZO.site == DEMO]
fig = go.Figure()
for pid, g in d.groupby("piezo_id"):
    fig.add_trace(go.Scatter(x=g.month, y=-g.gw_depth_m, mode="lines",
                             name=f"{pid}" + (" (southeast corner)" if pid == "P2" else " (northwest)"),
                             line=dict(width=3, color=CYAN if pid == "P2" else MUTED)))
fig.add_vline(x=10, line=dict(color=RED, dash="dot"),
              annotation_text="water rises here", annotation_position="top left")
fig.update_layout(title="Northgate: the water table rose in the southeast, and only there",
                  xaxis_title="Month", yaxis_title="Water level (m relative to ground)",
                  height=380, template=PLT)
fig.show()
''')

step("📡", "Record 4 — the settlement survey",
     "Levelling to each column at six dates. This is the answer column: what the model is asked to predict.")

co(r'''
# Six surveys per column. Real records contain faults, so this one does too.

rng = np.random.default_rng(21)
bias = {(r.site, r.col_id): rng.normal(0, 0.8) for r in COLUMNS.itertuples()}   # setup error per column

rows = []
for m in EPOCHS:
    s_i, s_c, s_col, s_exc, s_ult = settlement_parts(COLUMNS, m)
    total = s_i + s_c + s_col + s_exc
    part = pd.DataFrame({
        "site": COLUMNS.site, "col_id": COLUMNS.col_id, "month": m,
        "settlement_mm": np.round(total + [bias[(s, c)] for s, c in zip(COLUMNS.site, COLUMNS.col_id)]
                                  + rng.normal(0, 1.2, len(COLUMNS)), 1),
        "s_immediate": s_i.round(2), "s_consolidation": s_c.round(2),
        "s_collapse": s_col.round(2), "s_excavation": s_exc.round(2),
        "s_consolidation_ultimate": s_ult.round(2),
    })
    rows.append(part)
MONITOR = pd.concat(rows, ignore_index=True).sort_values(["site", "col_id", "month"]).reset_index(drop=True)

# The truth is split off here and not touched again until the model has to be checked.
TRUTH   = MONITOR[["site", "col_id", "month", "s_immediate", "s_consolidation",
                   "s_collapse", "s_excavation", "s_consolidation_ultimate"]].copy()
MONITOR = MONITOR[["site", "col_id", "month", "settlement_mm"]].copy()

# Four kinds of fault that every monitoring dataset contains.
f = np.random.default_rng(3)
idx = MONITOR.index.to_numpy()
MONITOR.loc[f.choice(idx, 22, replace=False), "settlement_mm"] = np.nan            # dip meter not read
MONITOR.loc[f.choice(idx, 14, replace=False), "settlement_mm"] = -99.9             # logger default
MONITOR.loc[f.choice(idx, 16, replace=False), "settlement_mm"] += 45.0             # transcription slip
sel = f.choice(idx, 18, replace=False)
MONITOR.loc[sel, "settlement_mm"] = MONITOR.loc[sel, "settlement_mm"].values - 14.0  # apparent rebound

print(f"{len(MONITOR):,} survey readings, {MONITOR.settlement_mm.isna().sum()} of them blank")
print()
print(MONITOR[(MONITOR.site == DEMO) & (MONITOR.col_id.isin(["C01", "C42"]))].to_string(index=False))
''')

step("🏢", "Record 5 — the building itself",
     "Column positions, loads and footing sizes come off the structural drawings. Without them the ground data means nothing.")

co(r'''
# The Northgate column grid: position, load, and the pressure each footing applies.

d = COLUMNS[COLUMNS.site == DEMO]
fig = go.Figure(go.Scatter(
    x=d.x_m, y=d.y_m, mode="markers+text", text=d.col_id, textposition="top center",
    textfont=dict(size=8), marker=dict(size=d.load_kn / 55, color=d.bearing_kpa,
    colorscale="Blues", showscale=True, colorbar=dict(title="Bearing<br>(kPa)"),
    line=dict(color=INK, width=1))))
fig.update_layout(title="42 columns. Marker size is load, colour is bearing pressure.",
                  xaxis_title="Easting (m)", yaxis_title="Northing (m)", height=460, template=PLT)
fig.show()

print(d[["col_id", "load_kn", "footing_b_m", "bearing_kpa", "surcharge_kpa"]].describe()
      .loc[["min", "mean", "max"]].round(1).to_string())
''')

step("🔗", "Five records, one table",
     "Every row is one column at one survey date. That single shape is what a model can learn from.")

co(r'''
# The join. Ground data still missing - that is phase 4.

RAW = MONITOR.merge(COLUMNS, on=["site", "col_id"], how="left")
print(f"{len(RAW):,} rows x {RAW.shape[1]} columns")
print()
print(RAW[RAW.site == DEMO].head(4)[
    ["site", "col_id", "month", "settlement_mm", "load_kn", "footing_b_m",
     "bearing_kpa", "gw_drop_m"]].to_string(index=False))
''')
