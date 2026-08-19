"""Render every page of the hub headlessly and fail loudly on any exception.

Per-page AppTest is the only thing that catches Streamlit's magic-display
traps, so every page gets its own run, and the detail page gets one run per
project in the catalog.

    python smoke_test.py
"""
import os
import sys

from streamlit.testing.v1 import AppTest

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "app.py")
sys.path.insert(0, HERE)

import catalog  # noqa: E402

PAGES = ["Overview", "All projects", "Project detail", "Tracks", "Run & deploy"]


def run(page, project=None):
    app = AppTest.from_file(APP, default_timeout=180)
    app.query_params["page"] = page
    if project:
        app.query_params["project"] = project
    app.run()
    label = page if not project else f"{page}: {project}"
    if app.exception:
        raise AssertionError(f"{label} raised: {app.exception[0].value}")
    return label, app


def main():
    failures = []
    for page in PAGES:
        try:
            label, app = run(page)
            print(f"  ok  {label:<16} ({len(app.markdown)} markdown, "
                  f"{len(app.dataframe)} tables, {len(app.button)} buttons)")
        except AssertionError as error:
            failures.append(str(error))
            print(f"  FAIL {page}: {error}")

    for project in catalog.PROJECTS:
        try:
            run("Project detail", project["folder"])
        except AssertionError as error:
            failures.append(str(error))
            print(f"  FAIL detail {project['folder']}: {error}")
    print(f"  ok  Project detail rendered for all {len(catalog.PROJECTS)} projects"
          if not failures else "")

    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nAll pages rendered clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
