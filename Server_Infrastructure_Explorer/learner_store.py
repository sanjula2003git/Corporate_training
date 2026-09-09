"""Opt-in local persistence. Random recovery codes grant access to one profile."""
import hashlib,json,os,secrets,sqlite3
from contextlib import contextmanager
from pathlib import Path

DB=Path(os.getenv('LEARNER_DB_PATH',str(Path(__file__).parent/'runtime'/'learners.sqlite3')))
FIELDS=('profile','chats','shared_history','completed','struggles')
@contextmanager
def connect():
    DB.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(DB,timeout=10)
    try:
        with conn:
            conn.execute('CREATE TABLE IF NOT EXISTS learners (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
            yield conn
    finally:
        conn.close()
def identifier(code):
    if not isinstance(code,str) or not 30<=len(code)<=100:raise ValueError('Invalid recovery code')
    return hashlib.sha256(code.encode()).hexdigest()
def snapshot(state):
    return {k:list(state[k]) if isinstance(state.get(k),set) else state.get(k,{} if k in ('profile','chats','struggles') else []) for k in FIELDS}
def create(state):
    code=secrets.token_urlsafe(32)
    with connect() as db:db.execute('INSERT INTO learners VALUES (?,?)',(identifier(code),json.dumps(snapshot(state))))
    return code
def save(code,state):
    with connect() as db:db.execute('UPDATE learners SET payload=? WHERE id=?',(json.dumps(snapshot(state)),identifier(code)))
def restore(code):
    with connect() as db:row=db.execute('SELECT payload FROM learners WHERE id=?',(identifier(code),)).fetchone()
    if not row:raise ValueError('No saved learner matches this recovery code')
    return json.loads(row[0])
