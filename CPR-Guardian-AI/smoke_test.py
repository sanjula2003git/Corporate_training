"""Walk every page of the app and fail loudly on the first exception.

Run:  python smoke_test.py

AppTest starts a fresh process with an empty cache on every run, so this
exercises the current source and nothing else. That is the point - but it also
means it can never reproduce a stale-cache failure on a deployed app.
"""
import sys

from streamlit.testing.v1 import AppTest

import bridge

TIMEOUT = 300


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

    # The sidebar edges, on the pages that consume them.
    edges = [
        ("release", {"Who is on the floor?": "Child (4-5 cm)"}),
        ("peaks", {"How much helper A tires": 0.0}),
        ("peaks", {"How much helper A tires": 1.5}),
        ("fatigue", {"How much helper A tires": 0.0}),
        ("switch", {"How much helper A tires": 1.5}),
        ("timeline", {"Pad slipping (cm per minute)": 1.0}),
        ("rules", {"Pad slipping (cm per minute)": 1.0}),
    ]
    for stage, params in edges:
        good = run(stage, **params)
        print(f"{'ok  ' if good else 'FAIL'}  ?stage={stage}  {params}")
        ok &= good

    print("\nALL PAGES OK" if ok else "\nFAILURES ABOVE")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
