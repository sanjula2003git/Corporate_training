"""
text_budget.py - how much reading each page actually asks for.
==============================================================
The brief is that no page should be a wall of text. This renders every page
and counts the words a student is faced with, so "too long" is a measurement
rather than an opinion.

Run:  python -X utf8 text_budget.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from streamlit.testing.v1 import AppTest  # noqa: E402
import bridge  # noqa: E402

BUDGET = 700          # words per page, summed across its tabs (a student sees one tab at a time)
TAG = re.compile(r"<[^>]+>")


def words(at):
    """Prose a student actually reads. The injected <style> block is not prose."""
    n = 0
    for group in (at.markdown, at.caption, at.info, at.warning, at.success, at.error):
        for el in group:
            raw = str(el.value)
            if "<style>" in raw or ".stApp {" in raw:
                continue
            n += len(TAG.sub(" ", raw).split())
    return n


print(f"{'page':<12} {'words':>6}   budget {BUDGET}\n")
rows, over = [], []
for sid in ["start"] + list(bridge.ORDER):
    at = AppTest.from_file(str(HERE / "app.py"), default_timeout=300)
    at.query_params["stage"] = sid
    at.run()
    if at.exception:
        print(f"  {sid:<12} EXCEPTION {at.exception[0].value}")
        continue
    n = words(at)
    rows.append((sid, n))
    flag = "  <-- over" if n > BUDGET else ""
    if n > BUDGET:
        over.append((sid, n))
    print(f"  {sid:<12} {n:>6}{flag}")

print(f"\ntotal {sum(n for _, n in rows)} words across {len(rows)} pages")
print(f"mean {sum(n for _, n in rows) // max(1, len(rows))} words per page")
if over:
    print("\nover budget: " + ", ".join(f"{s} ({n})" for s, n in over))
sys.exit(1 if over else 0)
