"""Supabase Data API storage. Recovery-code hashes scope all profile requests."""
import json,re,urllib.request,urllib.error
from datetime import datetime,timezone
from server_settings import setting

class StorageError(OSError):pass

def enabled():
    return str(setting('LEARNER_STORAGE','local')).lower()=='supabase'

def request(method,suffix='',payload=None,prefer=None):
    url=str(setting('SUPABASE_URL','')).rstrip('/')
    key=str(setting('SUPABASE_SECRET_KEY','') or setting('SUPABASE_SERVICE_ROLE_KEY',''))
    if not re.fullmatch(r'https://[a-z0-9-]+\.supabase\.co',url) or not key:
        raise StorageError('Add your Supabase project URL and server secret key in Streamlit Secrets.')
    headers={'apikey':key,'Content-Type':'application/json','Accept':'application/json','User-Agent':'ServerInfrastructureTutor/1.0'}
    # New secret keys use apikey only. Legacy service-role JWTs also need bearer auth.
    if not key.startswith('sb_secret_'):headers['Authorization']='Bearer '+key
    if prefer:headers['Prefer']=prefer
    req=urllib.request.Request(url+'/rest/v1/server_tutor_learners'+suffix,method=method,headers=headers,data=json.dumps(payload).encode() if payload is not None else None)
    try:
        with urllib.request.urlopen(req,timeout=15) as response:
            raw=response.read(1_100_000)
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        if error.code in (401,403):raise StorageError('Supabase denied access. Check the server secret key and table permissions.') from None
        if error.code==404:raise StorageError('The learner table is missing. Run supabase_setup.sql in the Supabase SQL editor.') from None
        raise StorageError('Supabase could not save or load learning. Your current session remains available; download a backup and retry.') from None
    except (OSError,ValueError):raise StorageError('Supabase is unreachable or returned an invalid response. Check whether the project is paused, then retry.') from None

def check():
    request('GET','?select=id&limit=0')

def valid_id(profile_id):
    if not re.fullmatch('[0-9a-f]{64}',profile_id):raise ValueError('Invalid profile identifier')

def save(profile_id,payload,create=False):
    valid_id(profile_id)
    request('POST','?on_conflict=id',{'id':profile_id,'payload':payload,'updated_at':datetime.now(timezone.utc).isoformat()},'return=minimal' if create else 'resolution=merge-duplicates,return=minimal')

def restore(profile_id):
    valid_id(profile_id)
    rows=request('GET','?id=eq.'+profile_id+'&select=payload&limit=1')
    if not rows:raise ValueError('No saved learner matches this recovery code')
    if not isinstance(rows,list) or not isinstance(rows[0],dict) or not isinstance(rows[0].get('payload'),dict):raise StorageError('Supabase returned invalid learning data.')
    return rows[0]['payload']
