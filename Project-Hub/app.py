"""Project Hub -- one Streamlit app that indexes everything in this repository.

Run from the repository root or from this folder:

    streamlit run Project-Hub/app.py

catalog.py holds the curated description of each project; scan.py reads the
folders themselves, so the counts on every page come from the files that are
actually on disk right now.
"""
import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import catalog
import figures
import scan

st.set_page_config(page_title="Corporate Training -- Project Hub",
                   page_icon="🗂️", layout="wide")

BG, CARD, LINE, TEXT, MUTED = "#0e1117", "#161b22", "#30363d", "#e6edf3", "#8b949e"
ACCENT = "#4fc3f7"

st.markdown(f"""<style>
.stApp {{background:{BG}; color:{TEXT}}}
.block-container {{max-width:1280px; padding-top:1.4rem}}
.hero {{padding:1.4rem 1.6rem; border:1px solid {LINE}; border-radius:16px;
        background:linear-gradient(135deg,{CARD} 0%,#11161d 100%)}}
.hero h1 {{margin:.2rem 0 .4rem 0; font-size:2.1rem}}
.hero p {{color:{MUTED}; margin:0; max-width:78ch}}
/* Each card is its own column block, so the Open/Live buttons under a row only
   line up if every card is the SAME height -- a min-height alone just floors the
   short ones. Title, blurb and pill tray each get a fixed height, and the blurb
   is clamped rather than allowed to run on. */
.card {{border:1px solid {LINE}; border-radius:14px; background:{CARD};
        padding:1rem 1.1rem; margin-bottom:.6rem}}
.card h4 {{margin:.1rem 0 .35rem 0; font-size:1.02rem; line-height:1.3;
           height:2.6em; overflow:hidden}}
.card p {{color:{MUTED}; font-size:.86rem; margin:.35rem 0 .5rem 0; line-height:1.45;
          height:5.8em; overflow:hidden; display:-webkit-box; -webkit-line-clamp:4;
          -webkit-box-orient:vertical}}
.tray {{height:3.6em; overflow:hidden}}
.pill {{display:inline-block; padding:.12rem .55rem; border-radius:999px;
        font-size:.7rem; border:1px solid {LINE}; color:{MUTED}; margin:0 .25rem .3rem 0}}
.dot {{display:inline-block; width:.55rem; height:.55rem; border-radius:50%; margin-right:.35rem}}
.kicker {{color:{MUTED}; font-size:.72rem; letter-spacing:.09em; text-transform:uppercase}}
.note {{padding:.75rem 1rem; border-left:4px solid #d29922; background:#1b2028;
        border-radius:6px; color:{TEXT}; font-size:.88rem}}
a {{color:{ACCENT}}}
[data-testid="stMetricValue"] {{font-size:1.7rem}}
</style>""", unsafe_allow_html=True)

SCAN_VERSION = 3  # bump to invalidate the cache after changing scan.py


@st.cache_data(show_spinner="Reading the repository...")
def load(version):
    """Scan every catalogued folder. `version` is the cache key, deliberately
    an argument rather than a module constant -- a module-level constant baked
    into a cached function survives a redeploy and then disagrees with the code."""
    scans = scan.scan_all([p["folder"] for p in catalog.PROJECTS])
    return scans, scan.totals(scans)


SCANS, TOTALS = load(SCAN_VERSION)


def facts(project):
    return SCANS.get(project["folder"], {})


def rows():
    """One flat record per project: catalog fields merged with scanned fields."""
    out = []
    for project in catalog.PROJECTS:
        found = facts(project)
        notebooks = found.get("notebooks", [])
        out.append(dict(
            Project=project["title"],
            About=project["blurb"],
            Folder=project["folder"],
            Track=project["track"],
            Discipline=project["discipline"],
            Approach=project["family"],
            Status=catalog.DEPLOY_SHORT[project["deploy"]],
            FullStatus=catalog.DEPLOY_LABEL[project["deploy"]],
            deploy=project["deploy"],
            Notebooks=len(notebooks),
            Cells=sum(nb["cells"] for nb in notebooks),
            App=found.get("has_app", False),
            AppLines=found.get("app_lines", 0),
            CodeLines=found.get("code_lines", 0),
            Links=sum(nb["stage_links"] for nb in notebooks),
            Slug=project.get("slug", ""),
            Started=project["started"],
            Updated=project["updated"],
            URL=catalog.live_url(project),
        ))
    return pd.DataFrame(out)


FRAME = rows()


def goto(page, folder=None):
    st.query_params["page"] = page
    if folder:
        st.query_params["project"] = folder
    elif "project" in st.query_params:
        del st.query_params["project"]
    st.rerun()


def status_dot(deploy):
    color = catalog.DEPLOY_COLOR[deploy]
    return f"<span class='dot' style='background:{color}'></span>{catalog.DEPLOY_LABEL[deploy]}"


def card(project, key_prefix):
    found = facts(project)
    notebooks = found.get("notebooks", [])
    cells = sum(nb["cells"] for nb in notebooks)
    bits = [f"<span class='pill'>{project['discipline']}</span>",
            f"<span class='pill'>{project['family']}</span>"]
    if notebooks:
        bits.append(f"<span class='pill'>{cells} cells</span>")
    if found.get("has_app"):
        bits.append(f"<span class='pill'>Streamlit app</span>")
    st.markdown(
        f"<div class='card'><div class='kicker'>{status_dot(project['deploy'])}</div>"
        f"<h4>{project['title']}</h4><p>{project['blurb']}</p>"
        f"<div class='tray'>{''.join(bits)}</div></div>",
        unsafe_allow_html=True)
    left, right = st.columns([1, 1])
    if left.button("Open", key=f"{key_prefix}-{project['folder']}", width="stretch"):
        goto("Project detail", project["folder"])
    url = catalog.live_url(project)
    if url:
        right.link_button("Live app", url, width="stretch")
    else:
        right.button("Not deployed", key=f"nd-{key_prefix}-{project['folder']}",
                     disabled=True, width="stretch")


def grid(projects, key_prefix, columns=3):
    for start in range(0, len(projects), columns):
        chunk = projects[start:start + columns]
        for column, project in zip(st.columns(columns), chunk):
            with column:
                card(project, key_prefix)



# Ten columns is what fits across the page without a horizontal scrollbar; the
# rest are opt-in, and the description is wide enough to squeeze everything else.
TABLE_COLUMNS = ["Project", "Discipline", "Approach", "Status",
                 "Notebooks", "Cells", "App", "CodeLines", "URL"]

EXTRA_COLUMNS = {
    "What it teaches": "About",
    "Track": "Track",
    "Deep-links": "Links",
    "Folder on disk": "Folder",
    "Deploy slug": "Slug",
    "Started": "Started",
    "Last touched": "Updated",
}

COLUMN_CONFIG = {
    "Project": st.column_config.TextColumn("Project", width="large"),
    "About": st.column_config.TextColumn("What it teaches", width="large"),
    "Approach": st.column_config.TextColumn("Model / approach", width="medium"),
    "Notebooks": st.column_config.NumberColumn("NB", format="%d", help="Notebooks in the folder"),
    "Cells": st.column_config.NumberColumn("Cells", format="%d"),
    "App": st.column_config.CheckboxColumn("App", help="Folder contains app.py"),
    "CodeLines": st.column_config.NumberColumn("Lines", format="%d"),
    "Links": st.column_config.NumberColumn("Links", format="%d",
                                           help="?stage= deep-links inside the notebooks"),
    "URL": st.column_config.LinkColumn("Live app", display_text="open"),
    "Status": st.column_config.TextColumn(
        "Status", help="Live = reachable · Wired = slug sits in the notebook but was "
                       "never claimed · In progress = scaffold only · No app = notebooks "
                       "or web code only"),
}

STATUS_LEGEND = ("**Live** reachable now · **Wired** the slug is in the notebook but was "
                 "never claimed, so those links are dead · **In progress** scaffold only · "
                 "**No app** notebooks or web code only")


def project_table(projects, key, columns=None):
    """The projects as a table. Clicking a row opens that project's detail page.

    Height is set from the row count so a 52-row catalogue is not served through
    a 400-pixel window, but capped so the page still scrolls as one page.
    """
    folders = [p["folder"] for p in projects]
    order = {folder: index for index, folder in enumerate(folders)}
    table = FRAME[FRAME.Folder.isin(folders)].copy()
    table = table.sort_values("Folder", key=lambda column: column.map(order))
    chosen = list(columns or TABLE_COLUMNS)
    table = table[[column for column in chosen if column in table.columns]]
    event = st.dataframe(table, width="stretch", hide_index=True,
                         height=min(38 * len(table) + 44, 1000),
                         column_config=COLUMN_CONFIG, key=key,
                         on_select="rerun", selection_mode="single-row")
    st.caption(STATUS_LEGEND)
    picked = event.selection.rows
    if picked:
        goto("Project detail", folders[picked[0]])
    return table


# --------------------------------------------------------------------- pages
def page_overview():
    st.markdown(
        "<div class='hero'><div class='kicker'>Corporate Training</div>"
        "<h1>🗂️ Project Hub</h1>"
        "<p>Every teaching project built in this repository, in one place: the engineering AI "
        "series, the emergency-response projects, the business-decision notebooks, the pandas "
        "foundations, and the eight-stage full-stack web track. Counts on this page are read "
        "from the folders themselves each time the app starts.</p></div>",
        unsafe_allow_html=True)
    st.write("")

    live = int((FRAME.deploy.isin(["live", "external"])).sum())
    columns = st.columns(6)
    columns[0].metric("Projects", len(FRAME))
    columns[1].metric("Notebooks", TOTALS["notebooks"])
    columns[2].metric("Notebook cells", f"{TOTALS['cells']:,}")
    columns[3].metric("Streamlit apps", TOTALS["apps"])
    columns[4].metric("Lines of code", f"{TOTALS['code_lines']:,}")
    columns[5].metric("Deployed", live)

    st.divider()
    left, right = st.columns([3, 2])

    with left:
        st.markdown("#### Where the work went")
        st.plotly_chart(figures.track_bar(FRAME), width="stretch")

    with right:
        st.markdown("#### Deployment status")
        st.plotly_chart(figures.status_donut(FRAME), width="stretch")

    st.markdown("#### When each project was built")
    st.caption("First to last commit touching that folder, coloured by track.")
    st.plotly_chart(figures.build_timeline(FRAME), width="stretch")

    st.markdown("#### Live right now")
    deployed = [p for p in catalog.PROJECTS if catalog.live_url(p)]
    for project in deployed:
        url = catalog.live_url(project)
        note = project.get("note", "")
        line = f"- **{project['title']}** — [{url}]({url})"
        if note:
            line += f"  \n  <span style='color:{MUTED}; font-size:.85rem'>{note}</span>"
        st.markdown(line, unsafe_allow_html=True)

    st.markdown("#### Every project")
    st.caption("Click a row to open it. The All-projects page has search and filters.")
    project_table(catalog.PROJECTS, "overview-table")

    reserved = [p for p in catalog.PROJECTS if p["deploy"] == "reserved"]
    st.markdown(
        f"<div class='note'><b>{len(reserved)} apps are wired but not claimed.</b> Their notebooks "
        "already contain <code>?stage=</code> deep-links pointing at a chosen "
        "<code>&lt;slug&gt;.streamlit.app</code>. Those links stay dead until someone types that "
        "exact slug into the <b>App URL</b> field of the Streamlit deploy dialog. The Run &amp; "
        "deploy page lists every slug still waiting.</div>", unsafe_allow_html=True)


def page_browse():
    st.markdown("### All projects")
    st.caption(f"{len(FRAME)} projects, {TOTALS['notebooks']} notebooks, "
               f"{TOTALS['apps']} Streamlit apps.")

    top = st.columns([2, 2, 2, 1.4])
    query = top[0].text_input("Search", placeholder="crane, pandas, CNN, invoice...")
    tracks = top[1].multiselect("Track", catalog.TRACK_ORDER)
    disciplines = top[2].multiselect("Discipline", sorted(FRAME.Discipline.unique()))
    view = top[3].radio("View", ["Table", "Cards"], horizontal=True)

    only = st.columns(3)
    want_app = only[0].checkbox("Has a Streamlit app")
    want_nb = only[1].checkbox("Has a notebook")
    want_live = only[2].checkbox("Deployed and reachable")

    selected = []
    for project in catalog.PROJECTS:
        found = facts(project)
        if tracks and project["track"] not in tracks:
            continue
        if disciplines and project["discipline"] not in disciplines:
            continue
        if want_app and not found.get("has_app"):
            continue
        if want_nb and not found.get("notebooks"):
            continue
        if want_live and not catalog.live_url(project):
            continue
        if query:
            haystack = " ".join([project["title"], project["blurb"], project["folder"],
                                 project["family"], project["discipline"],
                                 project["track"]]).lower()
            if query.lower() not in haystack:
                continue
        selected.append(project)

    st.caption(f"{len(selected)} match" + ("" if len(selected) == 1 else "es"))
    if not selected:
        st.info("Nothing matches those filters.")
        return

    if view == "Cards":
        grid(selected, "browse")
        return

    st.caption("Click any row to open that project. Drag a column edge to widen it, "
               "or use the toolbar above the table to sort, search and go full-screen.")
    extras = st.multiselect("Add columns", list(EXTRA_COLUMNS),
                            help="The ten default columns fit the page; these do not.")
    columns = list(TABLE_COLUMNS)
    for label in extras:
        column = EXTRA_COLUMNS[label]
        columns.insert(1 if column == "About" else len(columns) - 1, column)
    table = project_table(selected, "browse-table", columns=columns)
    st.download_button("Download this table as CSV",
                       table.to_csv(index=False).encode("utf-8"),
                       file_name="corporate-training-projects.csv", mime="text/csv")


def page_detail():
    folders = [p["folder"] for p in catalog.PROJECTS]
    current = st.query_params.get("project", folders[0])
    if current not in folders:
        current = folders[0]
    titles = {p["folder"]: p["title"] for p in catalog.PROJECTS}
    chosen = st.selectbox("Project", folders, index=folders.index(current),
                          format_func=lambda f: titles[f])
    if chosen != current:
        st.query_params["project"] = chosen
        current = chosen

    project = catalog.BY_FOLDER[current]
    found = facts(project)
    notebooks = found.get("notebooks", [])

    st.markdown(
        f"<div class='hero'><div class='kicker'>{project['track']} &nbsp;·&nbsp; "
        f"{status_dot(project['deploy'])}</div><h1>{project['title']}</h1>"
        f"<p>{project['blurb']}</p></div>", unsafe_allow_html=True)
    st.write("")

    columns = st.columns(5)
    columns[0].metric("Notebooks", len(notebooks))
    columns[1].metric("Notebook cells", sum(nb["cells"] for nb in notebooks))
    columns[2].metric("App lines", found.get("app_lines", 0))
    columns[3].metric("Code lines", found.get("code_lines", 0))
    columns[4].metric("Stage deep-links", sum(nb["stage_links"] for nb in notebooks))

    # Built as a list first: a fixed three-column row leaves a hole where the
    # live-app button would have been for the projects that have no live app.
    url = catalog.live_url(project)
    actions = []
    if url:
        actions.append(("Open the live app", url, "primary"))
    if notebooks:
        actions.append(("Open the notebook in Colab",
                        f"https://colab.research.google.com/github/"
                        f"{catalog.REPO.split('github.com/')[-1]}/blob/{catalog.BRANCH}/"
                        f"{notebooks[0]['rel']}", "secondary"))
    actions.append(("Browse the folder on GitHub",
                    f"{catalog.REPO}/tree/{catalog.BRANCH}/{project['folder']}", "secondary"))
    for column, (label, href, kind) in zip(st.columns(len(actions)), actions):
        column.link_button(label, href, width="stretch", type=kind)

    if project.get("note"):
        st.markdown(f"<div class='note'>{project['note']}</div>", unsafe_allow_html=True)
    if project["deploy"] == "reserved":
        st.markdown(
            f"<div class='note'>The notebook's deep-links point at "
            f"<code>https://{project['slug']}.streamlit.app</code>. Claim exactly that slug in the "
            "<b>App URL</b> field when deploying, or swap the host in the notebook afterwards.</div>",
            unsafe_allow_html=True)

    st.divider()
    left, right = st.columns([1, 1])

    with left:
        st.markdown("#### How to run it")
        if found.get("has_app"):
            st.code(f"cd \"{project['folder']}\"\n"
                    f"pip install -r requirements.txt\n"
                    f"streamlit run app.py", language="bash")
        elif notebooks:
            st.code(f"jupyter notebook \"{notebooks[0]['rel']}\"", language="bash")
        else:
            st.caption("No Python entry point -- see the folder's README.")

        if found.get("requirements"):
            with st.expander(f"requirements.txt ({len(found['requirements'])} packages)"):
                st.code("\n".join(found["requirements"]))

        if found.get("modules"):
            st.markdown("#### Python modules")
            st.write(" · ".join(f"`{m}`" for m in found["modules"]))
        if found.get("data_files"):
            st.markdown("#### Data files")
            st.write(" · ".join(f"`{d}`" for d in found["data_files"]))

    with right:
        st.markdown("#### Notebooks")
        if notebooks:
            st.dataframe(pd.DataFrame([
                dict(Notebook=nb["name"], Cells=nb["cells"], Code=nb["code_cells"],
                     Markdown=nb["markdown_cells"], Outputs=nb["has_outputs"],
                     Links=nb["stage_links"], MB=round(nb["size"] / 1_048_576, 2))
                for nb in notebooks]), width="stretch", hide_index=True)
            hosts = sorted({h for nb in notebooks for h in nb["hosts"]})
            if len(hosts) > 1:
                st.warning("More than one Streamlit host appears inside this folder's notebooks: "
                           + ", ".join(hosts) + ". That usually means a link-wiring pass ran twice.")
            elif hosts:
                st.caption(f"Deep-links point at `{hosts[0]}`.")
        else:
            st.caption("No notebook in this folder.")

    if found.get("readme"):
        with st.expander("README.md", expanded=False):
            st.markdown(found["readme"])
    else:
        st.caption("This folder has no README.md.")


def page_tracks():
    st.markdown("### Tracks")
    st.caption("The same material, grouped the way it is taught.")
    for track in catalog.TRACK_ORDER:
        members = [p for p in catalog.PROJECTS if p["track"] == track]
        subset = FRAME[FRAME.Track == track]
        st.markdown(f"## {track}")
        st.markdown(f"<p style='color:{MUTED}; max-width:80ch'>{catalog.TRACK_BLURB[track]}</p>",
                    unsafe_allow_html=True)
        columns = st.columns(4)
        columns[0].metric("Projects", len(members))
        columns[1].metric("Notebooks", int(subset.Notebooks.sum()))
        columns[2].metric("Cells", f"{int(subset.Cells.sum()):,}")
        columns[3].metric("Apps", int(subset.App.sum()))
        # Same nine columns as the All-projects table: adding the description here
        # pushed everything from Status rightwards off the page.
        project_table(members, f"track-table-{track[:8]}")
        st.divider()


def page_deploy():
    st.markdown("### Run and deploy")
    st.markdown(
        "Every Streamlit project in this repository follows the same shape: a folder with "
        "`app.py`, a `bridge.py` or `story.py` holding the model and the figures, a "
        "`requirements.txt`, and a Colab notebook that links back into the app stage by stage.")

    st.markdown("#### Run any project locally")
    st.code('cd "<Folder>"\npip install -r requirements.txt\nstreamlit run app.py', language="bash")
    st.markdown("#### Run this hub")
    st.code("streamlit run Project-Hub/app.py", language="bash")

    st.divider()
    st.markdown("#### Streamlit Community Cloud")
    st.markdown(
        "All of these deploy from the same repository and branch; only the **main file path** "
        "differs, so one repo carries every app. Apps redeploy on every push to "
        f"`{catalog.BRANCH}`.")

    # Only claimed apps get a clickable URL. An unclaimed slug would render as a
    # perfectly ordinary link that lands on a login page, which reads as "the app
    # is private" rather than "this app does not exist".
    deployable = [p for p in catalog.PROJECTS if SCANS[p["folder"]].get("has_app")]
    table = pd.DataFrame([
        dict(Project=p["title"],
             MainFile=f"{p['folder']}/app.py",
             Status=catalog.DEPLOY_LABEL[p["deploy"]],
             Slug=p.get("slug", ""),
             URL=catalog.live_url(p))
        for p in deployable])
    st.dataframe(table, width="stretch", hide_index=True,
                 column_config={
                     "MainFile": st.column_config.TextColumn("Main file path"),
                     "Slug": st.column_config.TextColumn("Slug in the notebook"),
                     "URL": st.column_config.LinkColumn("Reachable URL", display_text="open"),
                 })

    reserved = [p for p in catalog.PROJECTS if p["deploy"] == "reserved"]
    st.markdown(
        f"<div class='note'><b>Slugs still waiting to be claimed ({len(reserved)}).</b> Each "
        "notebook already links to its slug, so deploying under a different name leaves the "
        "in-notebook links dead. Either claim the slug in the deploy dialog, or swap the host "
        "string in that folder's <code>.ipynb</code> and <code>build_nb.py</code> afterwards "
        "— a markdown-only change that needs no re-execution.</div>", unsafe_allow_html=True)
    st.write(" ".join(f"`{p['slug']}`" for p in reserved))

    st.divider()
    st.markdown("#### Wiring check")
    st.markdown(
        "Every deep-link in a notebook is built as `<host>/?stage=<id>`, so the host baked into "
        "the notebook is the only thing that decides whether those links land anywhere. This "
        "compares the host actually present in each notebook against the slug recorded in "
        "`catalog.py`. **Streamlit answers every slug — real or invented — with a 303 to its "
        "login page, so no script can tell you whether an app is deployed or public.** Only a "
        "logged-out browser can.")

    checks = []
    for project in catalog.PROJECTS:
        notebooks = SCANS[project["folder"]]["notebooks"]
        hosts = sorted({host for nb in notebooks for host in nb["hosts"]})
        links = sum(nb["stage_links"] for nb in notebooks)
        if not hosts and not links:
            continue
        slug = project.get("slug", "")
        if len(hosts) > 1:
            verdict = "Two hosts in one folder — a link-wiring pass probably ran twice"
        elif not hosts:
            verdict = f"{links} deep-links but no Streamlit host"
        elif not slug:
            verdict = "Notebook is wired, but catalog.py records no slug"
        elif slug not in hosts[0]:
            verdict = f"Catalog says {slug}"
        else:
            verdict = "Matches"
        checks.append(dict(Project=project["title"], Links=links,
                           HostInNotebook=", ".join(hosts) or "—", Verdict=verdict))

    frame = pd.DataFrame(checks)
    problems = frame[frame.Verdict != "Matches"]
    if problems.empty:
        st.success(f"All {len(frame)} wired notebooks agree with the catalog.")
    else:
        st.warning(f"{len(problems)} of {len(frame)} wired notebooks disagree with the catalog.")
        st.dataframe(problems, width="stretch", hide_index=True)
    with st.expander(f"All {len(frame)} wired notebooks"):
        st.dataframe(frame, width="stretch", hide_index=True)

    st.divider()
    st.markdown("#### Two traps worth remembering")
    st.markdown(
        "- **A bare conditional expression crashes the page.** Writing "
        "`st.success(a) if ok else st.error(b)` as a statement makes Streamlit's magic display "
        "re-parse it and raise a misleading `SyntaxError`. Use a real `if` block. Only a "
        "per-page `AppTest` run finds it.\n"
        "- **A module-level constant inside a cached function survives a redeploy.** If a "
        "`@st.cache_data` function reads a constant that later changes, the stale cache raises a "
        "`KeyError` against the new code. Pass the constant in as an argument instead — the way "
        "`SCAN_VERSION` is passed to `load()` in this app.")


PAGES = {
    "Overview": page_overview,
    "All projects": page_browse,
    "Project detail": page_detail,
    "Tracks": page_tracks,
    "Run & deploy": page_deploy,
}


def main():
    with st.sidebar:
        st.markdown("## 🗂️ Project Hub")
        st.caption("Corporate Training repository")
        requested = st.query_params.get("page", "Overview")
        if requested not in PAGES:
            requested = "Overview"
        page = st.radio("Page", list(PAGES), index=list(PAGES).index(requested),
                        label_visibility="collapsed")
        if page != requested:
            st.query_params["page"] = page
        st.divider()
        st.metric("Projects", len(FRAME))
        st.metric("Notebook cells", f"{TOTALS['cells']:,}")
        st.metric("Repository size", f"{TOTALS['megabytes']:.0f} MB")
        st.divider()
        st.caption(f"Scanning `{scan.ROOT}`")
        st.link_button("Repository on GitHub", catalog.REPO, width="stretch")

    PAGES[page]()


main()
