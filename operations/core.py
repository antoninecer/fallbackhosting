"""Local broker core. No shell/SSH/Docker execution; injected reviewed driver only."""
import base64
from datetime import datetime, timezone
import hashlib
import fcntl
import os
import queue
import hmac
import json
import re
import sqlite3
import threading
import time

ACTIONS = {'list','inspect','logs','start','stop','restart','deploy','remove'}
WRITES = {'start','stop','restart','deploy','remove'}
ID = re.compile(r'[a-z][a-z0-9-]{0,39}\Z')
CID = re.compile(r'[a-f0-9]{64}\Z')
STATES = {'created','running','paused','restarting','removing','exited','dead','missing','unknown'}
MAX_LOG_BYTES = 4096


class Denied(ValueError):
    def __init__(self, code):
        self.code=code
        super().__init__(code)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)


def decode_json(value):
    def unique(pairs):
        result={}
        for key,item in pairs:
            if key in result: raise Denied('DUPLICATE_FIELD')
            result[key]=item
        return result
    try:return json.loads(value,object_pairs_hook=unique)
    except (ValueError,TypeError) as exc:raise Denied('INVALID_JSON') from exc


def exact(value, fields):
    if not isinstance(value,dict) or set(value)!=set(fields.split()):raise Denied('INVALID_FIELDS')


def identifier(value):
    if not isinstance(value,str) or not ID.fullmatch(value):raise Denied('INVALID_ID')


def utc():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


class Signer:
    """Fixture/trusted authority only; never give signing keys to PHP callers."""
    def __init__(self,key):
        if not isinstance(key,bytes) or len(key)<32:raise Denied('WEAK_AUTHORITY_KEY')
        self.key=key

    def issue(self,claims):
        body=base64.urlsafe_b64encode(canonical(claims).encode()).decode().rstrip('=')
        return body+'.'+hmac.new(self.key,body.encode(),hashlib.sha256).hexdigest()

    def verify(self,token,now):
        if not isinstance(token,str) or len(token)>8192:raise Denied('INVALID_TOKEN')
        try:
            body,signature=token.split('.')
            if not re.fullmatch(r'[A-Za-z0-9_-]+',body) or not re.fullmatch(r'[a-f0-9]{64}',signature):raise Denied('INVALID_TOKEN')
            if not hmac.compare_digest(hmac.new(self.key,body.encode(),hashlib.sha256).hexdigest(),signature):raise Denied('BAD_SIGNATURE')
            claims=decode_json(base64.b64decode(body+'='*(-len(body)%4),altchars=b'-_',validate=True))
            if not isinstance(claims,dict) or type(claims.get('expires')) is not int or not now<claims['expires']<=now+300:raise Denied('EXPIRED_TOKEN')
            return claims
        except (ValueError,UnicodeError) as exc:raise Denied('INVALID_TOKEN') from exc


class Broker:
    def __init__(self,path,policy,driver,auth_key,approval_key,clock=time.time):
        if auth_key==approval_key:raise Denied('SEPARATE_AUTHORITIES_REQUIRED')
        self.path=str(path);self.policy=policy;self.driver=driver;self.clock=clock
        self.lease=os.open(self.path+'.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:fcntl.flock(self.lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            os.close(self.lease)
            raise Denied('BROKER_ALREADY_RUNNING')
        self.worker_slots=threading.BoundedSemaphore(4)
        self.auth=Signer(auth_key);self.approvals=Signer(approval_key)
        self.lock=threading.RLock()
        with self.db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, digest TEXT NOT NULL, principal TEXT NOT NULL,
                    project TEXT NOT NULL, node TEXT NOT NULL, app TEXT NOT NULL, action TEXT NOT NULL,
                    state TEXT NOT NULL, created TEXT NOT NULL, finished TEXT, code TEXT, result TEXT);
                CREATE TABLE IF NOT EXISTS approvals(nonce TEXT PRIMARY KEY, job_id TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS resources(node TEXT NOT NULL, project TEXT NOT NULL, app TEXT NOT NULL,
                    container TEXT NOT NULL UNIQUE, PRIMARY KEY(node,project,app));
                CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY, utc TEXT NOT NULL, job_id TEXT,
                    principal TEXT NOT NULL, action TEXT NOT NULL, result TEXT NOT NULL);
            ''')
            # Never replay dispatched or queued jobs after process loss.
            db.execute("UPDATE jobs SET state='UNKNOWN',code='INTERRUPTED',finished=? WHERE state IN ('RUNNING','QUEUED')",(utc(),))

    def close(self):
        if self.lease is not None:
            os.close(self.lease);self.lease=None

    def call(self,kind,*args,timeout,output_limit):
        # A timeout is UNKNOWN: daemon work may still finish; no blind replay.
        if not self.worker_slots.acquire(blocking=False):raise RuntimeError('Driver capacity exhausted')
        results=queue.Queue(maxsize=1)
        def run():
            try:results.put((True,getattr(self.driver,kind)(*args,timeout=timeout,output_limit=output_limit)))
            except Exception:results.put((False,None))
            finally:self.worker_slots.release()
        threading.Thread(target=run,daemon=True).start()
        try:success,result=results.get(timeout=min(timeout,self.policy.get('test_timeout_seconds',timeout)))
        except queue.Empty:raise TimeoutError('Driver outcome unknown')
        if not success:raise RuntimeError('Driver outcome unknown')
        return result

    def db(self):
        db=sqlite3.connect(self.path,timeout=2)
        db.execute('PRAGMA busy_timeout=2000')
        return db

    def audit(self,db,job,principal,action,result):
        db.execute('INSERT INTO audit(utc,job_id,principal,action,result) VALUES(?,?,?,?,?)',(utc(),job,principal,action,result))
        db.execute('DELETE FROM audit WHERE seq NOT IN (SELECT seq FROM audit ORDER BY seq DESC LIMIT 1000)')

    def authorize(self,request,peer_uid):
        exact(request,'version request_id node project app action params authorization approval')
        if type(request['version']) is not int or request['version']!=1:raise Denied('INVALID_VERSION')
        for key in ('request_id','node','project','app'):identifier(request[key])
        action=request['action']
        if not isinstance(action,str) or action not in ACTIONS:raise Denied('INVALID_ACTION')
        if type(peer_uid) is not int or peer_uid not in self.policy['peers']:raise Denied('PEER_DENIED')
        claims=self.auth.verify(request['authorization'],int(self.clock()))
        exact(claims,'principal peer_uid project node actions expires')
        principal=claims['principal'];identifier(principal)
        grant=self.policy['principals'].get(principal)
        if not grant or type(claims['peer_uid']) is not int or claims['peer_uid']!=peer_uid or claims['project']!=request['project'] or claims['node']!=request['node'] or not isinstance(claims['actions'],list) or action not in claims['actions']:raise Denied('SCOPE_DENIED')
        if request['project'] not in grant['projects'] or action not in grant['actions'] or peer_uid not in grant['peers']:raise Denied('PRINCIPAL_DENIED')
        binding=self.policy['apps'].get(request['app'])
        if not binding or binding['project']!=request['project'] or binding['node']!=request['node']:raise Denied('APP_DENIED')
        params=request['params']
        if action=='logs':
            exact(params,'tail max_bytes')
            if type(params['tail']) is not int or not 1<=params['tail']<=100 or type(params['max_bytes']) is not int or not 1<=params['max_bytes']<=MAX_LOG_BYTES:raise Denied('LOG_BOUNDS')
        elif action=='remove':
            exact(params,'confirm_container')
            if not isinstance(params['confirm_container'],str) or not CID.fullmatch(params['confirm_container']):raise Denied('CONFIRMATION_REQUIRED')
        else:exact(params,'')
        body={k:request[k] for k in ('version','request_id','node','project','app','action','params')}
        digest=hashlib.sha256(canonical(dict(body,principal=principal)).encode()).hexdigest()
        nonce=None
        if action in WRITES:
            approval=self.approvals.verify(request['approval'],int(self.clock()))
            exact(approval,'nonce principal digest expires')
            identifier(approval['nonce'])
            if approval['principal']!=principal or approval['digest']!=digest:raise Denied('APPROVAL_SCOPE')
            nonce=approval['nonce']
        elif request['approval'] is not None:raise Denied('UNEXPECTED_APPROVAL')
        return principal,binding,digest,nonce

    def managed(self,db,request):
        row=db.execute('SELECT container FROM resources WHERE node=? AND project=? AND app=?',(request['node'],request['project'],request['app'])).fetchone()
        if not row:raise Denied('NOT_MANAGED')
        observed=self.call('inspect',request['node'],row[0],timeout=5,output_limit=8192)
        expected={'io.fallbackhosting.managed':'true','io.fallbackhosting.project':request['project'],'io.fallbackhosting.app':request['app'],'io.fallbackhosting.node':request['node']}
        if not isinstance(observed,dict) or observed.get('id')!=row[0] or not isinstance(observed.get('labels'),dict) or any(observed['labels'].get(k)!=v for k,v in expected.items()):raise Denied('OWNERSHIP_MISMATCH')
        state=observed.get('state')
        if state not in STATES:state='unknown'
        return row[0],state

    def submit(self,request,peer_uid):
        try:return self._submit(request,peer_uid)
        except Denied as failure:
            with self.db() as db:self.audit(db,None,'denied','denied',failure.code)
            raise

    def _submit(self,request,peer_uid):
        principal,binding,digest,nonce=self.authorize(request,peer_uid)
        with self.lock, self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT digest,state,code,result,principal FROM jobs WHERE id=?',(request['request_id'],)).fetchone()
            if row:
                if row[0]!=digest or row[4]!=principal:raise Denied('REQUEST_ID_CONFLICT')
                return {'job_id':request['request_id'],'state':row[1],'code':row[2],'result':json.loads(row[3]) if row[3] else None}
            if db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]>=1000:raise Denied('JOB_STORE_FULL')
            if db.execute("SELECT COUNT(*) FROM jobs WHERE state IN ('QUEUED','RUNNING')").fetchone()[0]>=16:raise Denied('OVERLOADED')
            if db.execute("SELECT 1 FROM jobs WHERE node=? AND (state IN ('QUEUED','RUNNING') OR (state='UNKNOWN' AND ?))",(request['node'],int(request['action'] in WRITES))).fetchone():raise Denied('NODE_BUSY_OR_UNRECONCILED')
            if nonce:
                try:db.execute('INSERT INTO approvals VALUES(?,?)',(nonce,request['request_id']))
                except sqlite3.IntegrityError as exc:raise Denied('APPROVAL_REPLAY') from exc
            db.execute('INSERT INTO jobs(id,digest,principal,project,node,app,action,state,created) VALUES(?,?,?,?,?,?,?,?,?)',(request['request_id'],digest,principal,request['project'],request['node'],request['app'],request['action'],'QUEUED',utc()))
            self.audit(db,request['request_id'],principal,request['action'],'QUEUED')
        with self.db() as db:
            db.execute("UPDATE jobs SET state='RUNNING' WHERE id=?",(request['request_id'],))
        state,code,result='SUCCEEDED','OK',None
        try:
            result=self.perform(request,binding)
        except Denied as failure:state,code='FAILED',failure.code
        except Exception:state,code='UNKNOWN','DRIVER_OUTCOME_UNKNOWN'
        with self.db() as db:
            db.execute('UPDATE jobs SET state=?,code=?,result=?,finished=? WHERE id=?',(state,code,canonical({'logs_available':True} if request['action']=='logs' and result is not None else result),utc(),request['request_id']))
            self.audit(db,request['request_id'],principal,request['action'],state)
        return {'job_id':request['request_id'],'state':state,'code':code,'result':result}

    def perform(self,r,binding):
        action=r['action'];node=r['node']
        with self.db() as db:
            if action=='deploy':
                if db.execute('SELECT 1 FROM resources WHERE node=? AND project=? AND app=?',(node,r['project'],r['app'])).fetchone():raise Denied('APP_ALREADY_MANAGED')
                template=self.policy['templates'].get(binding['template'])
                if not template or not re.fullmatch(r'[A-Za-z0-9./:_-]+@sha256:[a-f0-9]{64}',template['image']):raise Denied('UNAPPROVED_TEMPLATE')
                labels={'io.fallbackhosting.managed':'true','io.fallbackhosting.project':r['project'],'io.fallbackhosting.app':r['app'],'io.fallbackhosting.node':node}
                spec={'image':template['image'],'labels':labels,'network':'none','read_only':True,'cap_drop':['ALL'],'no_new_privileges':True,'memory_bytes':67108864,'cpu_quota':25000,'pids_limit':64,'ports':[],'mounts':[],'privileged':False,'user':'1000:1000'}
                created=self.call('execute',node,'deploy',spec,timeout=15,output_limit=8192)
                cid=created.get('id') if isinstance(created,dict) else None
                if not isinstance(cid,str) or not CID.fullmatch(cid):raise RuntimeError('Unknown create outcome')
                db.execute('INSERT INTO resources VALUES(?,?,?,?)',(node,r['project'],r['app'],cid))
                db.commit()
                try:_,observed=self.managed(db,r)
                except Denied as exc:raise RuntimeError('Post-dispatch ownership unconfirmed') from exc
                return {'container_id':cid,'state':observed,'observed_utc':utc()}
            if action=='list' and not db.execute('SELECT 1 FROM resources WHERE node=? AND project=? AND app=?',(node,r['project'],r['app'])).fetchone():
                return {'containers':[]}
            cid,observed=self.managed(db,r)
            if action in {'list','inspect'}:
                item={'container_id':cid,'app':r['app'],'state':observed,'observed_utc':utc()}
                return {'containers':[item]} if action=='list' else item
            if action=='remove' and r['params']['confirm_container']!=cid:raise Denied('CONFIRMATION_MISMATCH')
            if action=='remove' and observed=='running':raise Denied('STOP_BEFORE_REMOVE')
            params={'container_id':cid}
            if action=='logs':params.update(r['params'])
            outcome=self.call('execute',node,action,params,timeout=15,output_limit=MAX_LOG_BYTES if action=='logs' else 8192)
            if action=='logs':
                if not isinstance(outcome,dict) or not isinstance(outcome.get('logs'),str):raise RuntimeError('Invalid log result')
                value=outcome['logs'].encode()[:r['params']['max_bytes']].decode(errors='replace')
                value=re.sub(r'(?i)(password|token|secret|authorization)(\s*[:=]\s*)\S+',r'\1\2[REDACTED]',value)
                value=value.encode()[:r['params']['max_bytes']].decode(errors='ignore')
                return {'logs':value,'truncated':len(outcome['logs'].encode())>r['params']['max_bytes'],'observed_utc':utc()}
            after=self.call('inspect',node,cid,timeout=5,output_limit=8192)
            if action=='remove':
                if after is not None:raise RuntimeError('Removal unconfirmed')
                db.execute('DELETE FROM resources WHERE container=?',(cid,))
                return {'container_id':cid,'state':'missing','observed_utc':utc()}
            try:_,actual=self.managed(db,r)
            except Denied as exc:raise RuntimeError('Post-dispatch ownership unconfirmed') from exc
            expected='exited' if action=='stop' else 'running'
            if actual!=expected:raise RuntimeError('Outcome unconfirmed')
            return {'container_id':cid,'state':actual,'observed_utc':utc()}


    def read_scope(self,request,peer_uid):
        exact(request,'kind request_id node project app authorization')
        if request['kind'] not in {'view','job_status'}:raise Denied('INVALID_READ_KIND')
        synthetic=dict(version=1,request_id=request['request_id'],node=request['node'],project=request['project'],app=request['app'],action='inspect',params={},authorization=request['authorization'],approval=None)
        principal,_,_,_=self.authorize(synthetic,peer_uid)
        return principal

    def read(self,request,peer_uid):
        principal=self.read_scope(request,peer_uid)
        with self.db() as db:
            if request['kind']=='job_status':
                row=db.execute('SELECT state,code,result FROM jobs WHERE id=? AND principal=? AND project=? AND node=? AND app=?',(request['request_id'],principal,request['project'],request['node'],request['app'])).fetchone()
                if not row:raise Denied('JOB_NOT_FOUND')
                return {'job_id':request['request_id'],'state':row[0],'code':row[1],'result':json.loads(row[2]) if row[2] else None}
            rows=db.execute('SELECT id,action,state,code,created,finished,result FROM jobs WHERE principal=? AND project=? AND node=? AND app=? ORDER BY rowid DESC LIMIT 16',(principal,request['project'],request['node'],request['app'])).fetchall()
            jobs=[dict(job_id=r[0],action=r[1],state=r[2],code=r[3],created_utc=r[4],finished_utc=r[5]) for r in rows]
            observation=None
            for row in rows:
                result=json.loads(row[6]) if row[6] else None
                if isinstance(result,dict) and 'container_id' in result and 'state' in result:
                    observation={k:result[k] for k in ('container_id','state','observed_utc')}
                    break
            audit=[dict(utc=r[0],job_id=r[1],action=r[2],result=r[3]) for r in db.execute('SELECT utc,job_id,action,result FROM audit WHERE principal=? AND job_id IN (SELECT id FROM jobs WHERE project=? AND node=? AND app=?) ORDER BY seq DESC LIMIT 16',(principal,request['project'],request['node'],request['app']))]
        return {'node':request['node'],'project':request['project'],'app':request['app'],'last_observation':observation,'health_provenance':'HISTORICAL' if observation else 'UNKNOWN','current_health':'UNKNOWN','jobs':jobs,'errors':[j for j in jobs if j['state'] in {'FAILED','UNKNOWN'}],'audit':audit}
