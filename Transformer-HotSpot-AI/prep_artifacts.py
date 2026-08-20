"""
prep_artifacts.py - run the expensive work once, offline.
=========================================================
Streamlit Community Cloud gives this app a fraction of one CPU and sleeps the
container when nobody is using it. Every wake-up therefore used to re-simulate
a year of substation history and refit thirteen models, which is what got the
app CPU-throttled.

This script does all of that once and writes the results to artifacts/. The app
then loads tables instead of fitting models, and story.py falls back to
computing live whenever the folder is absent - so a fresh clone still runs with
no build step, and deleting artifacts/ restores the original behaviour exactly.

What is NOT shipped: the fitted Random Forest, which pickles to 72 MB. The
forest page only ever read four things off it - the first tree's split chain,
the tree count, the mean depth, and test MAE against the number of trees
averaged - so those are precomputed instead and the object is thrown away.

Run:  python -X utf8 prep_artifacts.py
Then commit artifacts/ along with any code change that affects the numbers.
"""
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "artifacts"

sys.path.insert(0, str(HERE))
import story  # noqa: E402

# Build from scratch, never from a previous build: point story at a folder that
# does not exist so every loader misses and every value is computed live.
story.ART = HERE / "__building__"

_t0 = time.perf_counter()
_steps = []


def step(label, fn):
    t = time.perf_counter()
    out = fn()
    dt = time.perf_counter() - t
    _steps.append((label, dt))
    print(f"  {label:38s} {dt:7.2f}s")
    return out


def save(df, name):
    df.to_parquet(OUT / f"{name}.parquet", compression="zstd")
    kb = (OUT / f"{name}.parquet").stat().st_size / 1024
    print(f"      -> {name}.parquet  {kb:8.1f} KB")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    print("Simulating and cleaning")
    raw = step("year of substation history", story._compute_raw_log)
    clean, report, before = step("cleaning + audit trail", story._compute_clean_log)
    feats = step("feature engineering", story._compute_features)

    print("Fitting the leaderboard")
    models = step("linear + forest + boosting + xgb", story._compute_models)
    best = models["best"]
    fitted = models["fitted"]

    print("Deriving what the pages read off the fitted models")
    # --- linear coefficients ------------------------------------------------
    lin_mdl, _sc, lin_feats = fitted["lin_raw"]
    coefs = pd.DataFrame({"feature": lin_feats, "coef": lin_mdl.coef_})

    # --- feature importances, best model against the forest -----------------
    imp = pd.DataFrame({
        "feature": story.ENG_FEATURES,
        story.BEST_LABEL.get(best, "Best model"):
            getattr(fitted[best], "feature_importances_",
                    np.zeros(len(story.ENG_FEATURES))),
        "Random Forest": fitted["rf"].feature_importances_,
    })

    # --- everything the forest page needs, so the 72 MB forest can be dropped
    def forest_facts():
        rf = fitted["rf"]
        t0 = rf.estimators_[0].tree_
        node, rules = 0, []
        for _ in range(5):
            if t0.children_left[node] == -1:
                break
            rules.append({"feature": story.ENG_FEATURES[t0.feature[node]],
                          "threshold": float(t0.threshold[node])})
            node = t0.children_left[node]
        Xte = feats.loc[models["test_mask"], story.ENG_FEATURES].values
        each = np.array([t.predict(Xte) for t in rf.estimators_])
        running = np.cumsum(each, axis=0) / np.arange(1, len(each) + 1)[:, None]
        mae = np.abs(running - models["y_test"]).mean(axis=1)
        return rules, rf, mae

    rules, rf, rf_mae = step("forest: tree rules + MAE by tree count", forest_facts)
    forest = {
        "rules": rules,
        "trees": len(rf.estimators_),
        "mean_depth": float(np.mean([t.get_depth() for t in rf.estimators_])),
        "one_tree_mae": float(rf_mae[0]),
    }
    rf_curve = pd.DataFrame({"trees": np.arange(1, len(rf_mae) + 1), "mae": rf_mae})

    print("Running the per-page experiments")
    boost = step("boosting curve (sklearn GB, 200 trees)", story._compute_boost_curve)
    drops = step("instrument-drop refits (6 models)", story._compute_instrument_drops)
    splits = step("test-set comparison (2 models)", story._compute_split_comparison)
    holdout = step("hold out a whole unit (4 models)", story._compute_holdout_units)

    print("Writing artifacts")
    save(raw, "raw_log")
    save(clean, "clean_log")
    save(report, "clean_report")
    save(feats, "features")
    save(models["board"], "board")
    save(pd.DataFrame({**models["preds"], "y_test": models["y_test"]}), "preds")
    save(coefs, "lin_raw_coefs")
    save(imp, "importances")
    save(rf_curve, "rf_curve")
    save(pd.DataFrame({"trees": boost.index.to_numpy(), "mae": boost.to_numpy()}),
         "boost_curve")
    save(drops, "instrument_drops")
    save(splits, "split_comparison")
    save(holdout, "holdout_units")

    # --- the one model that has to survive as an object ---------------------
    # Four pages predict from live slider values, so the best model is written
    # out too. XGBoost gets its own portable format; sklearn gets joblib.
    model_file = None
    if best == "xgb":
        model_file = "best_model.ubj"
        fitted[best].save_model(str(OUT / model_file))
    else:
        import joblib
        model_file = "best_model.pkl"
        joblib.dump(fitted[best], OUT / model_file, compress=3)
    print(f"      -> {model_file}  {(OUT / model_file).stat().st_size / 1024:8.1f} KB")

    import sklearn
    meta = {
        "built": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
        "best": best,
        "best_model_file": model_file,
        "rows_before_cleaning": int(before),
        "forest": forest,
        "rows": {"raw": len(raw), "clean": len(clean), "test": int(feats.test.sum())},
        "versions": {"pandas": pd.__version__, "numpy": np.__version__,
                     "scikit-learn": sklearn.__version__},
    }
    try:
        import xgboost
        meta["versions"]["xgboost"] = xgboost.__version__
    except Exception:
        meta["versions"]["xgboost"] = None
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"      -> meta.json")

    total_kb = sum(p.stat().st_size for p in OUT.iterdir()) / 1024
    print(f"\nBuilt in {time.perf_counter() - _t0:.1f}s "
          f"({sum(d for _, d in _steps):.1f}s of it computation)")
    print(f"artifacts/ is {total_kb / 1024:.2f} MB across {len(list(OUT.iterdir()))} files")
    print("\nLeaderboard as built:")
    print(models["board"].to_string(index=False,
                                    formatters={"MAE (°C)": "{:.3f}".format,
                                                "RMSE (°C)": "{:.3f}".format,
                                                "R²": "{:.4f}".format}))
    if meta["versions"]["xgboost"] is None:
        print("\nWARNING: xgboost was not installed, so the leaderboard has no XGBoost "
              "row and the best model fell back to Gradient Boosting. The deployed app "
              "installs xgboost from requirements.txt - build with it installed, or the "
              "app will be missing a model the notebook talks about.")


if __name__ == "__main__":
    main()
