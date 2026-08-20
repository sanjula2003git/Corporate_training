"""
smoke_pages.py - render every stage and time it.
================================================
A page can pass every numeric check and still crash at draw time, so this runs
the real app once per stage through Streamlit's AppTest and reports any
exception plus how long the page took.

Run:  python -X utf8 smoke_pages.py
"""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from streamlit.testing.v1 import AppTest  # noqa: E402
import bridge  # noqa: E402

stages = ["start"] + list(bridge.ORDER)
print(f"Rendering {len(stages)} stages\n")

fails, times = [], []
for sid in stages:
    at = AppTest.from_file(str(HERE / "app.py"), default_timeout=300)
    at.query_params["stage"] = sid
    t = time.perf_counter()
    try:
        at.run()
        dt = time.perf_counter() - t
        if at.exception:
            fails.append((sid, at.exception[0].value))
            print(f"  FAIL  {sid:22s} {dt:6.2f}s  {at.exception[0].value}")
        else:
            times.append((sid, dt))
            print(f"  ok    {sid:22s} {dt:6.2f}s")
    except Exception as e:
        dt = time.perf_counter() - t
        fails.append((sid, repr(e)))
        print(f"  ERROR {sid:22s} {dt:6.2f}s  {e!r}")

print(f"\n{len(stages) - len(fails)}/{len(stages)} stages rendered clean")
if times:
    slow = sorted(times, key=lambda x: -x[1])[:5]
    print("slowest:", ", ".join(f"{s} {d:.2f}s" for s, d in slow))
    print(f"total render time: {sum(d for _, d in times):.1f}s")
if fails:
    print("\nFAILURES:")
    for sid, err in fails:
        print(f"  - {sid}: {err}")
sys.exit(1 if fails else 0)
