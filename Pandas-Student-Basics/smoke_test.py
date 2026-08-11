"""Walk every page of the app and fail loudly on the first exception.

Run:  python smoke_test.py
"""
import sys

from streamlit.testing.v1 import AppTest

import bridge

TIMEOUT = 120


def run(stage, **params):
    at = AppTest.from_file("app.py", default_timeout=TIMEOUT)
    at.query_params["stage"] = stage
    at.run()
    for name, value in params.items():
        widget = next((w for w in list(at.slider) + list(at.radio) + list(at.selectbox)
                       if w.label.startswith(name)), None)
        if widget is None:
            raise AssertionError(f"no widget starting with {name!r} on ?stage={stage}")
        widget.set_value(value)
        at.run()
    if at.exception:
        for e in at.exception:
            print(f"\n[FAIL] ?stage={stage} {params}\n{e.message}\n{e.stack_trace}")
        return False
    return True


def main():
    ok = True
    for stage in ["start"] + bridge.ORDER:
        good = run(stage)
        print(f"{'ok  ' if good else 'FAIL'}  ?stage={stage}")
        ok &= good

    # the edges of every sidebar control, on the pages that consume them
    edges = [
        ("start", dict(Students=20)),
        ("start", dict(Students=200)),
        ("dupes", {"Duplicated rows glued": 0}),
        ("holes", {"Empty cells": 0}),
        ("holes", {"Empty cells": 20}),
        ("fill", {"Fill the numeric holes": "mean"}),
        ("iqr", {"IQR multiplier": 0.5}),
        ("iqr", {"IQR multiplier": 3.0}),
        ("after", {"IQR multiplier": 0.5}),
        ("payoff", {"Extreme students planted": 0}),
        ("fill", {"Extreme students planted": 8}),
        ("iqr", {"Extreme students planted": 0}),
        ("payoff", {"Students": 20, "Empty cells": 20}),
        ("iloc", {"Row positions": (0, 12)}),
        ("loc", {"Index labels": (0, 12)}),
    ]
    for stage, params in edges:
        good = run(stage, **params)
        print(f"{'ok  ' if good else 'FAIL'}  ?stage={stage}  {params}")
        ok &= good

    print("\nALL PAGES OK" if ok else "\nFAILURES ABOVE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
