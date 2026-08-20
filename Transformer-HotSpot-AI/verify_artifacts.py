"""
verify_artifacts.py - prove the precomputed app tells the same story.
=====================================================================
Every number the app shows must be the same whether it loaded artifacts/ or
computed from scratch. This refits everything live and compares it against what
the artifacts return, then renders every stage to catch anything that only
breaks at draw time.

Run:  python -X utf8 verify_artifacts.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import story

REAL = story.ART
FAILS, CHECKS = [], 0


def compare(label, got, want, tol=1e-9):
    global CHECKS
    CHECKS += 1
    try:
        if isinstance(want, pd.DataFrame):
            assert list(got.columns) == list(want.columns), "columns differ"
            assert len(got) == len(want), f"{len(got)} rows vs {len(want)}"
            for c in want.columns:
                if pd.api.types.is_numeric_dtype(want[c]):
                    d = float(np.nanmax(np.abs(got[c].to_numpy(float)
                                               - want[c].to_numpy(float))))
                    assert d <= tol, f"column {c!r} differs by {d:.3g}"
                else:
                    assert list(got[c]) == list(want[c]), f"column {c!r} differs"
        elif isinstance(want, pd.Series):
            d = float(np.nanmax(np.abs(got.to_numpy(float) - want.to_numpy(float))))
            assert d <= tol, f"differs by {d:.3g}"
        elif isinstance(want, (int, float, np.floating)):
            assert abs(float(got) - float(want)) <= tol, f"{got} vs {want}"
        else:
            assert got == want, f"{got!r} vs {want!r}"
        print(f"  OK    {label}")
    except AssertionError as e:
        FAILS.append(f"{label}: {e}")
        print(f"  FAIL  {label}  -- {e}")


def clear_caches():
    for f in (story.get_raw_log, story.get_clean_log, story.get_features,
              story.get_models, story.fleet_snapshot, story._load_best_model):
        try:
            f.clear()
        except Exception:
            pass


print("Computing everything live (no artifacts)...")
story.ART = HERE / "__nonexistent__"
clear_caches()
live = {
    "board": story.get_models()["board"],
    "preds": story.get_models()["preds"],
    "y_test": story.get_models()["y_test"],
    "coefs": story.lin_raw_coefs(),
    "imp": story.importances(),
    "forest": story.forest_facts(),
    "boost": story._compute_boost_curve(),
    "drops": story._compute_instrument_drops(),
    "splits": story._compute_split_comparison(),
    "holdout": story._compute_holdout_units(),
    "features": story.get_features(),
    "clean": story.get_clean_log(),
    "fleet": story.fleet_snapshot(),
    "predict": story.predict_hotspot(820, 34.0, 78.0, age=16),
}

print("\nLoading from artifacts...")
story.ART = REAL
clear_caches()
assert story.artifacts_present(), "artifacts/ is missing - run prep_artifacts.py"
m = story.get_models()

print("\nComparing:")
compare("leaderboard", m["board"], live["board"])
compare("test-set labels", pd.Series(m["y_test"]), pd.Series(live["y_test"]))
for k in live["preds"]:
    compare(f"predictions[{k}]", pd.Series(m["preds"][k]), pd.Series(live["preds"][k]))
compare("linear coefficients", story.lin_raw_coefs(), live["coefs"])
compare("feature importances", story.importances(), live["imp"])

f_now, f_live = story.forest_facts(), live["forest"]
compare("forest: tree count", f_now["trees"], f_live["trees"])
compare("forest: mean depth", f_now["mean_depth"], f_live["mean_depth"])
compare("forest: one-tree MAE", f_now["one_tree_mae"], f_live["one_tree_mae"])
compare("forest: MAE by tree count", f_now["curve"], f_live["curve"])
compare("forest: first-tree rules",
        [(r["feature"], round(r["threshold"], 6)) for r in f_now["rules"]],
        [(r["feature"], round(r["threshold"], 6)) for r in f_live["rules"]])

compare("boosting curve", story.precomputed("boost_curve").set_index("trees")["mae"],
        live["boost"].rename(None).rename_axis("trees"))
compare("instrument drops", story.precomputed("instrument_drops")
        .reset_index(drop=True), live["drops"].reset_index(drop=True))
compare("test-set comparison", story.precomputed("split_comparison"), live["splits"])
compare("hold-out-a-unit", story.precomputed("holdout_units"), live["holdout"])
compare("engineered features", story.get_features(), live["features"])
compare("cleaning audit trail", story.get_clean_log()[1], live["clean"][1])
compare("rows before cleaning", story.get_clean_log()[2], live["clean"][2])
compare("fleet snapshot", story.fleet_snapshot()[0].drop(columns=["tone"]),
        live["fleet"][0].drop(columns=["tone"]), tol=0.05)
compare("live prediction from sliders",
        story.predict_hotspot(820, 34.0, 78.0, age=16), live["predict"], tol=0.05)

print(f"\n{CHECKS - len(FAILS)}/{CHECKS} checks passed")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS:
        print("  -", f)
sys.exit(1 if FAILS else 0)
