
co(r'''
# --- Soil mechanics used to generate every site and to sanity-check every model ---

def eff_stress(z, dw, fill_t):
    "Effective vertical stress (kPa) at depth z (m). Water table at dw. Fill / sand / clay."
    z, dw, fill_t = np.asarray(z, float), np.asarray(dw, float), np.asarray(fill_t, float)
    tops = [np.zeros_like(fill_t), fill_t, fill_t + SAND_T]
    ths  = [fill_t, np.full_like(fill_t, SAND_T), np.full_like(fill_t, 60.0)]
    out = np.zeros_like(z, dtype=float)
    for t0, th, g in zip(tops, ths, [G_FILL, G_SAND, G_CLAY]):
        bot = np.minimum(t0 + th, z)
        seg = np.maximum(bot - t0, 0.0)
        sub = np.clip(bot - np.maximum(dw, t0), 0.0, seg)      # the part below the water table
        out += (seg - sub) * g + sub * (g - G_W)
    return out

def U_of_Tv(Tv):
    "Average degree of consolidation from the time factor (Terzaghi, standard approximation)."
    Tv = np.asarray(Tv, float)
    return np.clip(np.where(Tv < 0.286,
                            np.sqrt(4.0 * Tv / np.pi),
                            1.0 - 10.0 ** ((1.781 - Tv) / 0.933) / 100.0), 0.0, 1.0)

def settlement_parts(c, month):
    "The four things that push a column down, in mm, at `month` months after completion."
    q_net = np.maximum(c["bearing_kpa"].values - G_FILL * DF, 5.0)
    B, H  = c["footing_b_m"].values, c["clay_thk_true"].values

    # 1. Immediate settlement of the fill and sand under the footing (elastic).
    Es  = 0.5 * (c["n60_true"].values + 15.0)                       # MPa, from SPT N60
    s_i = q_net * B * (1 - NU ** 2) * I_SHAPE / Es

    # 2. Consolidation of the soft clay (Terzaghi), driven by three stress increases.
    z_mid  = c["fill_thk_true"].values + SAND_T + H / 2.0
    s0     = np.maximum(eff_stress(z_mid, c["gw_depth_m"].values, c["fill_thk_true"].values), 5.0)
    zb     = np.maximum(z_mid - DF, 0.3)
    d_foot = q_net * B * B / ((B + zb) ** 2)                        # 2:1 spread, decays with depth
    d_area = c["surcharge_kpa"].values                              # slab + stored goods, no decay
    d_gw   = c["gw_drop_m"].values * G_W                            # drawdown raises effective stress
    Cr     = np.clip(0.055 + 0.020 * H, 0.05, 0.20)                 # Cc/(1+e0), softer where thicker
    s_c_ult = np.where(H > 0.05,
                       Cr * H * 1000.0 * np.log10((s0 + d_foot + d_area + d_gw) / s0), 0.0)
    cv  = np.clip(1.30 - 0.14 * H, 0.30, 1.30)                      # m2/yr
    Tv  = cv * (month / 12.0) / np.maximum(H / 2.0, 0.05) ** 2      # double drainage
    s_c = s_c_ult * U_of_Tv(Tv)

    # 3. Collapse of loose fill when a leaking pipe wets it.
    s_col = (c["collapse_pot"].values * c["fill_thk_true"].values * 1000.0
             * np.exp(-(c["dist_leak_m"].values / 14.0) ** 2)
             * np.clip((month - c["leak_month"].values) / 6.0, 0.0, 1.0))

    # 4. Ground drawn towards a nearby deep excavation (settlement trough, exponential decay).
    s_exc = (c["exc_amp_mm"].values * np.exp(-c["dist_exc_m"].values / 20.0)
             * np.clip((month - c["exc_month"].values) / 4.0, 0.0, 1.0))

    return s_i, s_c, s_col, s_exc, s_c_ult

print("Ground model loaded: elastic + consolidation + collapse + excavation.")
''')

step("🗺️", "Eighteen sites, one of them still open",
     "Seventeen buildings with two and a half years of monitoring, plus the warehouse under investigation.")

co(r'''
# --- Build the portfolio. Every site gets its own buried channel, fill and loading. ---

EPOCHS  = [3, 6, 12, 18, 24, 30]      # months after completion, when each survey was run
SPACING = 7.5                          # column spacing, m

def ground_fields(rng, W, L, demo=False):
    "Callables giving true clay thickness, fill thickness and SPT N60 anywhere on the site."
    if demo:
        p = dict(x0=0.66 * W, amp=14.0, wl=1.7 * L, width=13.0, hmax=6.4, ph=0.9)
    else:
        p = dict(x0=rng.uniform(0.25, 0.75) * W, amp=rng.uniform(5, 22), wl=rng.uniform(45, 110),
                 width=rng.uniform(9, 20),
                 hmax=(0.0 if rng.random() < 0.18 else rng.uniform(2.4, 7.0)),
                 ph=rng.uniform(0, 6.3))
    f0, f1, f2 = rng.uniform(0.8, 1.9), rng.uniform(0.2, 0.7), rng.uniform(40, 90)
    nb, na, nw = rng.uniform(17, 33), rng.uniform(2, 6), rng.uniform(35, 80)
    ph2, ph3 = rng.uniform(0, 6.3), rng.uniform(0, 6.3)

    def clay(x, y):
        centre = p["x0"] + p["amp"] * np.sin(2 * np.pi * y / p["wl"] + p["ph"])
        return np.clip(p["hmax"] * np.exp(-((x - centre) / p["width"]) ** 2) - 0.5, 0.0, None)

    def fill(x, y):
        return np.clip(f0 + f1 * np.sin(2 * np.pi * (x + 0.6 * y) / f2 + ph2), 0.4, 2.8)

    def n60(x, y):
        return np.clip(nb + na * np.cos(2 * np.pi * (0.7 * x - y) / nw + ph3)
                       - 5.0 * (fill(x, y) - 1.2), 6.0, 45.0)

    return clay, fill, n60

def build_site(sid, seed, demo=False):
    rng = np.random.default_rng(seed)
    nx, ny = (7, 6) if demo else (int(rng.integers(5, 8)), int(rng.integers(4, 7)))
    xs, ys = np.arange(nx) * SPACING + 10.0, np.arange(ny) * SPACING + 10.0
    X, Y = np.meshgrid(xs, ys)
    X, Y = X.ravel(), Y.ravel()
    W, L = xs.max() + 10.0, ys.max() + 10.0
    clay, fill, n60 = ground_fields(rng, W, L, demo)

    edge = (X == xs.min()) | (X == xs.max()) | (Y == ys.min()) | (Y == ys.max())
    load = rng.uniform(750, 1300) * np.where(edge, 0.58, 1.0) * rng.uniform(0.88, 1.12, X.size)
    B = np.clip(np.round(np.sqrt(load / 160.0), 1), 1.2, 3.2)

    gw_depth = rng.uniform(1.5, 3.4)
    gw_drop  = 0.0 if demo else (rng.uniform(0.8, 3.2) if rng.random() < 0.35 else 0.0)

    if demo or rng.random() < 0.25:
        lx, ly = (0.82 * W, 0.18 * L) if demo else (rng.uniform(0, W), rng.uniform(0, L))
        dist_leak = np.hypot(X - lx, Y - ly)
        leak_month = 11.0 if demo else float(rng.integers(5, 17))
        cpot = 0.016 if demo else rng.uniform(0.008, 0.018)
    else:
        dist_leak, leak_month, cpot = np.full(X.size, 120.0), 99.0, 0.0
        lx, ly = np.nan, np.nan

    if (not demo) and rng.random() < 0.30:
        d = X if rng.random() < 0.5 else Y
        dist_exc = d if rng.random() < 0.5 else (d.max() + 8.0 - d)
        exc_amp, exc_month = rng.uniform(8, 22), float(rng.integers(3, 19))
    else:
        dist_exc, exc_amp, exc_month = np.full(X.size, 120.0), 0.0, 99.0

    cols = pd.DataFrame({
        "site": sid,
        "col_id": [f"C{i + 1:02d}" for i in range(X.size)],
        "x_m": X, "y_m": Y,
        "load_kn": load.round(0), "footing_b_m": B,
        "bearing_kpa": (load / B ** 2).round(1),
        "surcharge_kpa": np.clip(rng.uniform(12, 42) + rng.normal(0, 5, X.size), 5, 58).round(1),
        "gw_depth_m": round(gw_depth, 2), "gw_drop_m": round(gw_drop, 2),
        "dist_leak_m": np.round(dist_leak, 1),
        "dist_exc_m": np.round(np.asarray(dist_exc, float), 1),
        "leak_month": leak_month, "exc_month": exc_month,
        "collapse_pot": cpot, "exc_amp_mm": exc_amp,
        "clay_thk_true": clay(X, Y).round(2),
        "fill_thk_true": fill(X, Y).round(2),
        "n60_true": n60(X, Y).round(1),
    })

    # Boreholes: drilled near planned column lines, before anything was built.
    nbh = 5 if demo else int(rng.integers(4, 7))
    pick = np.array([0, 6, 35, 41, 24]) if demo else rng.choice(X.size, size=nbh, replace=False)
    bx, by = X[pick] + rng.uniform(-3, 3, nbh), Y[pick] + rng.uniform(-3, 3, nbh)
    bh = pd.DataFrame({
        "site": sid, "bh_id": [f"BH{i + 1}" for i in range(nbh)],
        "x_m": bx.round(1), "y_m": by.round(1),
        "fill_thk_m": fill(bx, by).round(2),
        "clay_top_m": (fill(bx, by) + SAND_T).round(2),
        "clay_thk_m": clay(bx, by).round(2),
        "n60_bearing": n60(bx, by).round(0),
    })

    return cols, bh, dict(clay=clay, fill=fill, n60=n60, W=W, L=L, xs=xs, ys=ys, leak=(lx, ly))

SITES, BHS, FIELDS = [], [], {}
for i in range(1, 18):
    c, b, f = build_site(f"S{i:02d}", 1000 + i)
    SITES.append(c); BHS.append(b); FIELDS[f"S{i:02d}"] = f
c, b, f = build_site("NGW", 77, demo=True)
SITES.append(c); BHS.append(b); FIELDS["NGW"] = f

COLUMNS   = pd.concat(SITES, ignore_index=True)
BOREHOLES = pd.concat(BHS, ignore_index=True)
DEMO      = "NGW"      # Northgate warehouse, the building under investigation

print(f"{COLUMNS['site'].nunique()} sites, {len(COLUMNS)} columns, {len(BOREHOLES)} boreholes")
print(f"Soft clay is really present under {(COLUMNS['clay_thk_true'] > 0.5).mean():.0%} of columns.")
print("Nobody knows that yet - it is the truth we hide from the model and check against later.")
''')
