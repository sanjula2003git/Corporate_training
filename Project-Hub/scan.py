"""Reads the repository off disk so the hub never disagrees with the files.

catalog.py says what a project *is*. This module says what it currently
*contains*: notebooks and their cell counts, the Streamlit app and its size,
data files, the README, and how many `?stage=` deep-links the notebook carries.

Nothing here imports streamlit, so it can be run and tested on its own:

    python scan.py
"""
from __future__ import annotations

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

CODE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".mjs"}
DATA_EXT = {".csv", ".json", ".db", ".wav", ".npy"}
SKIP_DIRS = {"node_modules", "__pycache__", ".git", "dist", "release", "build", ".venv"}

STAGE_LINK = re.compile(r"\?stage=")


def _read_text(path, limit=None):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read() if limit is None else handle.read(limit)
    except OSError:
        return ""


def _count_lines(path):
    try:
        with open(path, "rb") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def notebook_facts(path):
    """Cell counts, saved-output flag and deep-link count, without parsing JSON.

    The largest notebooks here are ~6 MB of embedded PNG output; counting
    marker substrings is both faster and far cheaper in memory than json.load,
    and every count below is a marker that only ever appears once per cell.
    """
    text = _read_text(path)
    code = text.count('"cell_type": "code"') or text.count('"cell_type":"code"')
    md = text.count('"cell_type": "markdown"') or text.count('"cell_type":"markdown"')
    outputs = bool(re.search(r'"outputs":\s*\[\s*\{', text))
    hosts = sorted(set(re.findall(r"https://([a-z0-9\-]+\.streamlit\.app)", text)))
    return dict(
        name=os.path.basename(path),
        path=path,
        rel=os.path.relpath(path, ROOT).replace("\\", "/"),
        size=os.path.getsize(path) if os.path.exists(path) else 0,
        code_cells=code,
        markdown_cells=md,
        cells=code + md,
        has_outputs=outputs,
        stage_links=len(STAGE_LINK.findall(text)),
        hosts=hosts,
    )


def _walk(folder):
    """Every file under `folder`, skipping vendored and generated directories."""
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            yield os.path.join(dirpath, name)


def scan_folder(folder_name):
    """Everything the filesystem knows about one project folder."""
    folder = os.path.join(ROOT, folder_name)
    facts = dict(
        folder=folder_name,
        exists=os.path.isdir(folder),
        notebooks=[],
        code_files=0,
        code_lines=0,
        data_files=[],
        modules=[],
        readme="",
        readme_path="",
        requirements=[],
        app_lines=0,
        has_app=False,
        total_bytes=0,
    )
    if not facts["exists"]:
        return facts

    for path in _walk(folder):
        ext = os.path.splitext(path)[1].lower()
        rel = os.path.relpath(path, folder).replace("\\", "/")
        try:
            facts["total_bytes"] += os.path.getsize(path)
        except OSError:
            pass

        if ext == ".ipynb":
            facts["notebooks"].append(notebook_facts(path))
        elif ext in CODE_EXT:
            facts["code_files"] += 1
            facts["code_lines"] += _count_lines(path)
            if ext == ".py" and os.path.dirname(path) == folder:
                facts["modules"].append(rel)
        elif ext in DATA_EXT and os.path.dirname(path) == folder:
            facts["data_files"].append(rel)

    app = os.path.join(folder, "app.py")
    if os.path.isfile(app):
        facts["has_app"] = True
        facts["app_lines"] = _count_lines(app)

    readme = os.path.join(folder, "README.md")
    if os.path.isfile(readme):
        facts["readme_path"] = readme
        facts["readme"] = _read_text(readme)

    reqs = os.path.join(folder, "requirements.txt")
    if os.path.isfile(reqs):
        facts["requirements"] = [
            line.strip() for line in _read_text(reqs).splitlines() if line.strip()
        ]

    facts["notebooks"].sort(key=lambda n: n["name"])
    facts["modules"].sort()
    facts["data_files"].sort()
    return facts


def scan_all(folders):
    return {name: scan_folder(name) for name in folders}


def readme_lede(readme):
    """First heading and first paragraph of a README, for the card blurb."""
    title, lede = "", ""
    for line in readme.splitlines():
        stripped = line.strip()
        if not title and stripped.startswith("# "):
            title = stripped[2:].strip()
            continue
        if title and stripped and not stripped.startswith("#"):
            lede = stripped
            break
    return title, lede


def totals(scans):
    notebooks = [nb for facts in scans.values() for nb in facts["notebooks"]]
    return dict(
        folders=sum(1 for f in scans.values() if f["exists"]),
        notebooks=len(notebooks),
        cells=sum(nb["cells"] for nb in notebooks),
        code_cells=sum(nb["code_cells"] for nb in notebooks),
        apps=sum(1 for f in scans.values() if f["has_app"]),
        app_lines=sum(f["app_lines"] for f in scans.values()),
        code_lines=sum(f["code_lines"] for f in scans.values()),
        stage_links=sum(nb["stage_links"] for nb in notebooks),
        megabytes=sum(f["total_bytes"] for f in scans.values()) / 1_048_576,
    )


if __name__ == "__main__":
    import catalog

    scans = scan_all([p["folder"] for p in catalog.PROJECTS])
    missing = [name for name, f in scans.items() if not f["exists"]]
    print(f"root: {ROOT}")
    for key, value in totals(scans).items():
        print(f"  {key:12s} {value:,.0f}" if isinstance(value, (int, float)) else key)
    print(f"  missing folders: {missing or 'none'}")
