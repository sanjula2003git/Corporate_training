"""Build a credential-free package suitable for GitHub/Streamlit Cloud."""
from pathlib import Path
import zipfile,re
ROOT=Path(__file__).parent
files=[p for p in ROOT.rglob('*') if p.is_file() and not any(x in p.relative_to(ROOT).parts for x in ('__pycache__','.git','.venv')) and p.suffix not in ('.zip','.blend1') and p.name not in ('secrets.toml','.env')]
for p in files:
    if p.suffix in ('.py','.json','.toml','.md','.html','.mjs','.js') and re.search(rb'gsk_[A-Za-z0-9]{20,}',p.read_bytes()):raise RuntimeError('Possible key in '+p.name)
with zipfile.ZipFile(ROOT/'HeartLab_Deployment.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(p,p.relative_to(ROOT).as_posix())
print('Packaged',len(files),'files. Private secrets excluded.')
