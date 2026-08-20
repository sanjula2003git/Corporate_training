"""
run_notebook.py - execute every code cell and report what breaks.
=================================================================
The notebook's prose quotes numbers that its code computes, so a cell that
merely parses can still be wrong. This runs all of them in one namespace with
the plotting calls stubbed out, and prints any cell that raises.

Run:  python -X utf8 run_notebook.py
"""
import ast
import io
import sys
import traceback
from pathlib import Path

import nbformat as nbf

HERE = Path(__file__).resolve().parent
NB = HERE / "Transformer_HotSpot_Temperature_AI.ipynb"

nb = nbf.read(NB.open(encoding="utf-8"), as_version=4)
code = [(i, c.source) for i, c in enumerate(nb.cells) if c.cell_type == "code"]
print(f"{len(nb.cells)} cells, {len(code)} of them code\n")

# 1. every cell must parse
bad = []
for i, src in code:
    try:
        ast.parse(src)
    except SyntaxError as e:
        bad.append((i, f"SyntaxError: {e}"))
if bad:
    for i, e in bad:
        print(f"  cell {i}: {e}")
    sys.exit(1)
print("all code cells parse")

# 2. and every cell must run
import matplotlib
matplotlib.use("Agg")
import plotly.graph_objects as go
import plotly.io as pio
go.Figure.show = lambda self, *a, **k: None
pio.show = lambda *a, **k: None

ns = {"__name__": "__main__"}
buf = io.StringIO()
real_stdout = sys.stdout
failures = []
for n, (i, src) in enumerate(code, 1):
    sys.stdout = buf
    try:
        exec(compile(src, f"<cell {i}>", "exec"), ns)
    except Exception:
        sys.stdout = real_stdout
        failures.append((n, i, traceback.format_exc().strip().split("\n")[-1]))
        print(f"  FAIL  code cell {n} (notebook cell {i})")
        print("        " + failures[-1][2])
    finally:
        sys.stdout = real_stdout

print(f"\n{len(code) - len(failures)}/{len(code)} code cells ran clean")
if failures:
    print("\nFAILURES:")
    for n, i, err in failures:
        print(f"  - code cell {n} (cell {i}): {err}")
sys.exit(1 if failures else 0)
