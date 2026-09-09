"""Build a source upload package without credentials or learner records."""
import re,zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OPTIONAL_STORAGE_FILES=['cloud_store.py','server_settings.py']
FILES=['app.py','lessons.py','examples.py','tutor.py','groq_tutor.py','knowledge.py','learner_store.py','build_knowledge.py','test_tutor.py','requirements.txt','README.md','DEPLOYMENT.md','package_deploy.py','.gitignore','.streamlit/config.toml','.streamlit/secrets.toml.example','.github/workflows/check.yml']

def build():
    files=[ROOT/p for p in FILES+OPTIONAL_STORAGE_FILES]
    for folder in ('viewer','assets','knowledge_base'):
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    for p in files:
        if not p.is_file():raise RuntimeError('Missing deployment file: '+p.name)
        if p.suffix in ('.py','.md','.json','.toml','.mjs','.html','.yml') and re.search(rb'gsk_[A-Za-z0-9]{20,}',p.read_bytes()):
            raise RuntimeError('Possible credential in deployment file: '+p.name)
    target=ROOT/'Streamlit_Deployment.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
        for p in files:archive.write(p,p.relative_to(ROOT).as_posix())
    print(f'Created {target.name}: {len(files)} files; secrets and learner database excluded.')

if __name__=='__main__':build()
