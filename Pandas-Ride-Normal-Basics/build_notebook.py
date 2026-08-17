import json
from pathlib import Path

REFERENCE = Path(r"C:\Users\fersa\Corporate Training\Pandas-Student-Basics\pandas_student_basics.ipynb")
OUT = Path(__file__).parent / "pandas_ride_normal_basics.ipynb"
nb = json.loads(REFERENCE.read_text(encoding="utf-8"))

replacements = [
    ("Pandas Basics — Student Performance Data", "Pandas Basics — Hong Kong Ride Eligibility"),
    ("Pandas Student Basics", "Pandas Ride Normal Basics"),
    ("pandas-student-basics", "pandas-ride-normal-basics"),
    ("study_hours", "height_cm"), ("attendance", "weight_kg"), ("result", "allowed"),
    ("students.csv", "hong_kong_ride_visitors.csv"), ("students", "visitors"),
    ("student", "visitor"), ("Student", "Visitor"),
    ("Pass", "Allowed"), ("Fail", "Not Allowed"),
    ("hours per week", "centimetres"), ("study hours", "height"),
    ("attendance, in percent", "weight, in kilograms"),
]
for cell in nb["cells"]:
    text = "".join(cell.get("source", []))
    for old, new in replacements:
        text = text.replace(old, new)
    cell["source"] = text
    if cell["cell_type"] == "code":
        cell["execution_count"] = None; cell["outputs"] = []

nb["cells"][0]["source"] = """# Pandas Basics — Hong Kong Ride Eligibility

A hands-on replica of the Student Basics lesson using a **pure normally distributed dataset**.

The supplied table has three columns:

| Column | Meaning |
|---|---|
| `person` | Fictitious visitor identifier |
| `height_cm` | Height in centimetres, generated from a normal distribution |
| `weight_kg` | Weight in kilograms, generated from a normal distribution |

After cleaning, pandas derives `allowed` using the simulated classroom rule: height 145–190 cm and weight at most 90 kg.

> These are invented teaching limits, not the published policy of an actual Hong Kong attraction.
"""
nb["cells"][1]["source"] = """🎬 **The illustrated version.**

[Open the Pandas Ride Normal Basics illustration app once, in a second tab](https://pandas-ride-normal-basics.streamlit.app/?stage=start).
"""
nb["cells"][2]["source"] = """## 0. Setup — create normally distributed data

Height and weight are generated with `rng.normal`. We still add missing cells and duplicate rows so students can practise cleaning, but we deliberately add **no skew and no planted extreme values**.
"""
nb["cells"][3]["source"] = """import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

pd.set_option("display.max_rows", 20)
plt.rcParams["figure.figsize"] = (6, 4)
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.3

rng = np.random.default_rng(7)
n = 60
person = [f"P{i+1:03d}" for i in range(n)]
height_cm = np.round(rng.normal(160, 15, n), 1)
weight_kg = np.round(rng.normal(67, 14, n), 1)

df_raw = pd.DataFrame({"person": person, "height_cm": height_cm, "weight_kg": weight_kg})
df_raw.loc[[5, 18, 40], "height_cm"] = np.nan
df_raw.loc[[11, 33, 52], "weight_kg"] = np.nan
df_raw = pd.concat([df_raw, df_raw.iloc[[0, 1, 2, 3]]], ignore_index=True)
df_raw.to_csv("hong_kong_ride_visitors.csv", index=False)

print("rows written:", len(df_raw))
df_raw.head()
"""
nb["cells"][5]["source"] = 'df = pd.read_csv("hong_kong_ride_visitors.csv")\ndf'
nb["cells"][13]["source"] = """# `allowed` is derived only after numeric cleaning
preview = df.copy()
preview["allowed"] = np.where(
    preview["height_cm"].between(145, 190) & preview["weight_kg"].le(90),
    "Allowed", "Not Allowed")
preview["allowed"].value_counts()
"""
nb["cells"][14]["source"] = 'preview["allowed"].value_counts(normalize=True).round(3)'
nb["cells"][16]["source"] = """fig, axes = plt.subplots(1, 3, figsize=(14, 4))
preview["allowed"].value_counts().reindex(["Allowed", "Not Allowed"]).plot(kind="bar", ax=axes[0], color=["#4c9f70", "#c94f4f"])
axes[0].set_title("Simulated ride eligibility"); axes[0].tick_params(axis="x", rotation=0)
axes[1].hist(df["height_cm"].dropna(), bins=12, color="#4a7ebb", edgecolor="white")
axes[1].set_title("Normal distribution of height"); axes[1].set_xlabel("height_cm")
axes[2].hist(df["weight_kg"].dropna(), bins=12, color="#9b6fb6", edgecolor="white")
axes[2].set_title("Normal distribution of weight"); axes[2].set_xlabel("weight_kg")
plt.tight_layout(); plt.show()
"""
nb["cells"][17]["source"] = "The two histograms are approximately bell-shaped. Mean and median should therefore be close; this is the key contrast with the skewed-data lesson."
nb["cells"][20]["source"] = 'df[df.duplicated(keep=False)].sort_values("person")'
nb["cells"][26]["source"] = """# Numeric columns are approximately symmetric and normal, so use the MEAN.
for col in ["height_cm", "weight_kg"]:
    mean_value = df[col].mean()
    df[col] = df[col].fillna(mean_value)
    print(f"{col:<12} filled with mean = {mean_value:.2f}")

df["allowed"] = np.where(
    df["height_cm"].between(145, 190) & df["weight_kg"].le(90),
    "Allowed", "Not Allowed")
print("missing values left:", df.isnull().sum().sum())
"""
nb["cells"][28]["source"] = """fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for ax, col in zip(axes, ["height_cm", "weight_kg"]):
    ax.boxplot(df[col], patch_artist=True, boxprops=dict(facecolor="#cfe0f3"), medianprops=dict(color="#c94f4f", linewidth=2))
    ax.set_title(f"Boxplot — {col}"); ax.set_xticks([])
plt.tight_layout(); plt.show()
"""
nb["cells"][29]["source"] = 'df[["height_cm", "weight_kg"]].describe().loc[["min", "25%", "50%", "mean", "75%", "max"]]'
nb["cells"][30]["source"] = """def iqr_bounds(series):
    q1, q3 = series.quantile([0.25, 0.75]); iqr = q3 - q1
    return q1, q3, iqr, q1 - 1.5 * iqr, q3 + 1.5 * iqr

for col in ["height_cm", "weight_kg"]:
    q1, q3, iqr, low, high = iqr_bounds(df[col])
    flagged = df[(df[col] < low) | (df[col] > high)]
    print(col, "mean", round(df[col].mean(),2), "median", round(df[col].median(),2), "IQR flags", len(flagged))
"""
nb["cells"][31]["source"] = """# For this pure normal teaching dataset, inspect IQR flags but do not automatically delete valid people.
df_outliers = pd.concat([df[(df[c] < iqr_bounds(df[c])[3]) | (df[c] > iqr_bounds(df[c])[4])] for c in ["height_cm", "weight_kg"]]).drop_duplicates()
df_clean = df.copy().reset_index(drop=True)
print("rows flagged for inspection:", len(df_outliers))
print("rows retained:", len(df_clean))
df_outliers
"""
nb["cells"][32]["source"] = """fig, axes = plt.subplots(1, 2, figsize=(10, 4))
for ax, col in zip(axes, ["height_cm", "weight_kg"]):
    ax.hist(df_clean[col], bins=12, color="#4a7ebb", edgecolor="white")
    ax.axvline(df_clean[col].mean(), color="#ffb74d", label="mean")
    ax.axvline(df_clean[col].median(), color="#4fc3f7", linestyle="--", label="median")
    ax.set_title(col); ax.legend()
plt.suptitle("Normal data: mean and median stay close"); plt.tight_layout(); plt.show()
"""
nb["cells"][33]["source"] = "The IQR rule may flag valid tail observations even in a normal distribution. We inspect them, but we do not delete real people merely because their measurements are uncommon."
nb["cells"][39]["source"] = 'df_clean.loc[0:4, ["person", "height_cm", "weight_kg", "allowed"]]'
nb["cells"][40]["source"] = 'df_clean.loc[df_clean["height_cm"] > 170]'
nb["cells"][41]["source"] = 'eligible_tall = df_clean.loc[(df_clean["height_cm"] >= 145) & (df_clean["height_cm"] <= 190) & (df_clean["weight_kg"] <= 90)]\nprint("inside simulated limits:", len(eligible_tall))\neligible_tall.head()'
nb["cells"][42]["source"] = """df_clean["allowed"] = "Allowed"
df_clean.loc[(df_clean["height_cm"] < 145) | (df_clean["height_cm"] > 190) | (df_clean["weight_kg"] > 90), "allowed"] = "Not Allowed"
df_clean["allowed"].value_counts()
"""
nb["cells"][43]["source"] = 'pd.crosstab(df_clean["allowed"], columns="visitors")'
nb["cells"][45]["source"] = """summary = pd.DataFrame({"stage":["raw file","after drop_duplicates","after mean fill","final retained"],"rows":[len(df_raw),len(df_raw.drop_duplicates()),len(df),len(df_clean)]})
print(summary.to_string(index=False)); print("final missing:",df_clean.isnull().sum().sum()); print("final duplicates:",df_clean.duplicated().sum()); df_clean.describe(include="all")
"""
nb["cells"][46]["source"] = """fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for ax,col,unit in zip(axes,["height_cm","weight_kg"],["cm","kg"]):
    df_clean.groupby("allowed")[col].mean().plot(kind="bar",ax=ax,color=["#4c9f70","#c94f4f"])
    ax.set_title(f"Average {col} by eligibility"); ax.set_ylabel(unit); ax.tick_params(axis="x",rotation=0)
plt.tight_layout(); plt.show()
"""
nb["cells"][47]["source"] = """## 8. Your turn

1. Compare mean and median for both normal numeric columns.
2. Use `loc` to show visitors taller than 170 cm.
3. Recalculate eligibility with a different **simulated** height limit.
4. Count IQR flags without deleting them.
5. Explain why mean imputation is reasonable here but may be poor for skewed data.
"""

linked=[]
for cell in nb["cells"]:
    linked.append(cell)
    linked.append({"cell_type":"markdown","metadata":{},"source":"🎬 [Open this lesson in the Pandas Ride illustration app](https://pandas-ride-normal-basics.streamlit.app/?stage=start)\n"})
nb["cells"]=linked
nb["metadata"].setdefault("colab",{})["name"]="pandas_ride_normal_basics.ipynb"
OUT.write_text(json.dumps(nb,ensure_ascii=False,indent=1),encoding="utf-8")
print("Wrote",OUT,"with",len(linked),"cells")
