"""Opt-in local persistence. Random recovery codes grant access to one profile."""
import hashlib,json,os,secrets,sqlite3
from contextlib import contextmanager
from pathlib import Path
import cloud_store

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
    if cloud_store.enabled():
        cloud_store.save(identifier(code),snapshot(state),create=True)
        return code
    with connect() as db:db.execute('INSERT INTO learners VALUES (?,?)',(identifier(code),json.dumps(snapshot(state))))
    return code
def save(code,state):
    if cloud_store.enabled():
        cloud_store.save(identifier(code),snapshot(state))
        return
    with connect() as db:db.execute('UPDATE learners SET payload=? WHERE id=?',(json.dumps(snapshot(state)),identifier(code)))
def restore(code):
    if cloud_store.enabled():return cloud_store.restore(identifier(code))
    with connect() as db:row=db.execute('SELECT payload FROM learners WHERE id=?',(identifier(code),)).fetchone()
    if not row:raise ValueError('No saved learner matches this recovery code')
    return json.loads(row[0])

def export_backup(state):
    return json.dumps({'version':1,'learning':snapshot(state)},ensure_ascii=False)

def import_backup(raw):
    from lessons import BY_ID
    from tutor import DEFAULT_PROFILE
    if len(raw)>1_000_000:raise ValueError('Backup exceeds 1 MB')
    data=json.loads(raw)
    if not isinstance(data,dict) or data.get('version')!=1:raise ValueError('Unsupported backup')
    state=data.get('learning')
    if not isinstance(state,dict):raise ValueError('Invalid learning data')
    profile=state.get('profile',{})
    if not isinstance(profile,dict):raise ValueError('Invalid preferences')
    profile={k:str(profile.get(k,v))[:160] for k,v in DEFAULT_PROFILE.items()}
    if profile['style'] not in ('Step by step','Short answers','Analogies'):profile['style']=DEFAULT_PROFILE['style']
    if profile['level'] not in ('Beginner','More technical'):profile['level']=DEFAULT_PROFILE['level']
    def messages(items):
        if not isinstance(items,list):raise ValueError('Invalid conversation')
        result=[]
        for item in items[-24:]:
            if not isinstance(item,dict) or item.get('role') not in ('user','assistant') or not isinstance(item.get('content'),str):raise ValueError('Invalid message')
            result.append({'role':item['role'],'content':item['content'][:16000],**({'topic_id':item['topic_id']} if item.get('topic_id') in BY_ID else {})})
        return result
    chats=state.get('chats',{});struggles=state.get('struggles',{});completed=state.get('completed',[])
    if not isinstance(chats,dict) or not isinstance(struggles,dict) or not isinstance(completed,list):raise ValueError('Invalid progress')
    return dict(profile=profile,chats={k:messages(v) for k,v in chats.items() if k in BY_ID},shared_history=messages(state.get('shared_history',[]))[-20:],completed=[k for k in completed if isinstance(k,str) and k in BY_ID],struggles={k:min(v,10000) for k,v in struggles.items() if k in BY_ID and type(v) is int and v>=0})
