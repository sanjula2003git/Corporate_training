# Project Hub

One Streamlit app that indexes every project in this repository — the engineering AI series, the
emergency-response projects, the business-decision notebooks, the pandas foundations, the
eight-stage full-stack web track, and the classroom tools.

## Run

```bash
pip install -r Project-Hub/requirements.txt
streamlit run Project-Hub/app.py
```

It reads the folders **above** it, so it has to stay inside the repository. Nothing is copied or
cached to disk; the counts come from the files as they are right now.

## Pages

| Page | What it does |
| --- | --- |
| Overview | Headline counts, projects per track, deployment status, a build timeline, and the full 52-row table |
| All projects | The table, with search and filters; add optional columns, download CSV, or switch to cards |
| Project detail | One project: counts, run command, notebook table, deep-link host check, requirements, README |
| Tracks | The same table split by teaching track, with each track's method described above it |
| Run & deploy | Every deployable app, its Streamlit Cloud main-file path, and the slugs still waiting to be claimed |

Every table lists projects; **clicking a row opens that project's detail page**. Nine columns are
shown by default because that is what fits the page without a horizontal scrollbar — `Add columns`
on the All-projects page brings in the description, deep-link count, folder, slug and dates. The
status column is abbreviated there (`Live`, `Wired`, `In progress`, `No app`); the legend sits
under each table and the full wording is on the cards.

## Files

- `app.py` — the pages and the layout.
- `catalog.py` — the curated part: what each project teaches, its discipline, its model family,
  where it is deployed. Add a project here when you add a folder.
- `scan.py` — reads the repository. Runs standalone (`python scan.py`) and prints the totals.
- `figures.py` — the three charts. Run standalone (`python figures.py`) to write them to PNG and
  actually look at them; that is how the legend was found sitting on top of the first three
  timeline rows.
- `smoke_test.py` — renders every page headlessly, plus the detail page once per project, and
  fails on any exception.

## Adding a project

Append a `dict(...)` to `PROJECTS` in `catalog.py` with `folder`, `title`, `blurb`, `discipline`,
`family`, `track`, `deploy`, `started` and `updated`. Add `slug` when a Streamlit Cloud URL is
wired into the notebook, and `live` for a URL that is not a Streamlit Cloud one. Then:

```bash
python Project-Hub/scan.py          # confirms the folder is found
python Project-Hub/smoke_test.py    # confirms every page still renders
```

`deploy` is one of `live`, `reserved` (slug wired into the notebook but never claimed in the deploy
dialog, so those links are dead), `local`, `external`, `scaffold`, or `none`.

## Two things this app deliberately demonstrates

- `load()` takes `SCAN_VERSION` as an **argument** rather than reading a module-level constant. A
  constant read from inside a `@st.cache_data` function survives a redeploy and then disagrees with
  the new code, which no `AppTest` can see.
- Nothing is written as a bare `st.x() if cond else st.y()` expression. Streamlit's magic display
  re-parses those and raises a `SyntaxError` that points at the wrong thing entirely.
