"""Bounded, operator-started single Coolify installation. No shell or service install."""
from datetime import datetime, timezone
import argparse
import base64
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time

TEMPLATE = 'coolify-4.4.6'
REQUEST_KEYS = {'schema_version','id','action','node','template','inventory_revision','actor','created_utc'}

def utc(): return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def read_private(path, uid, limit=8192):
    fd=os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=uid or info.st_nlink!=1 or info.st_mode & 0o077 or info.st_size>limit:
            raise ValueError('unsafe private input')
        raw=os.read(fd,limit+1)
        if len(raw)>limit: raise ValueError('input too large')
        def unique(pairs):
            result={}
            for key,value in pairs:
                if key in result: raise ValueError('duplicate field')
                result[key]=value
            return result
        return json.loads(raw, object_pairs_hook=unique)
    finally: os.close(fd)

def validate(request, secret, policy, ident):
    if not isinstance(request,dict) or set(request)!=REQUEST_KEYS: raise ValueError('request shape')
    if not re.fullmatch('[a-f0-9]{32}',ident) or request['id']!=ident: raise ValueError('id')
    if type(request['schema_version']) is not int or request['schema_version']!=1: raise ValueError('version')
    if request['action']!='install' or request['template']!=TEMPLATE or request['node']!=policy['node'] or request['actor']!=policy['actor']: raise ValueError('scope')
    if type(request['inventory_revision']) is not int or request['inventory_revision']<1: raise ValueError('revision')
    created=datetime.strptime(request['created_utc'],'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    age=(datetime.now(timezone.utc)-created).total_seconds()
    if not -30<=age<=900: raise ValueError('expired')
    if not isinstance(secret,dict) or set(secret)!={'email','password'}: raise ValueError('secret shape')
    email,password=secret['email'],secret['password']
    if not isinstance(email,str) or len(email)>254 or not re.fullmatch(r'[^\s@\x00-\x1f]+@[^\s@\x00-\x1f]+\.[^\s@\x00-\x1f]+',email): raise ValueError('email')
    if not isinstance(password,str) or not 12<=len(password)<=128 or not re.fullmatch(r'[\x21-\x7e]+',password): raise ValueError('password')
    if not all(re.search(p,password) for p in ('[a-z]','[A-Z]','[0-9]','[^a-zA-Z0-9]')): raise ValueError('password strength')

def atomic_public(path, data, gid=None):
    fd,temp=tempfile.mkstemp(prefix='.worker-',dir=path.parent)
    try:
        os.fchmod(fd,0o640 if gid is not None else 0o600)
        if gid is not None: os.fchown(fd,-1,gid)
        with os.fdopen(fd,'w') as stream: json.dump(data,stream); stream.write('\n')
        os.replace(temp,path)
    finally:
        if os.path.exists(temp): os.unlink(temp)

def status(queue, ident, state, gid=None):
    atomic_public(queue/(ident+'.status.json'),dict(id=ident,state=state,utc=utc()),gid)

def run_one(queue, ledger, policy, driver, ident, uid, gid=None):
    secret_path=queue/(ident+'.secret.json')
    dispatched=False
    try:
        fd=os.open(ledger/(ident+'.attempted'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as stream: stream.write(utc())
        request=read_private(queue/(ident+'.request.json'),uid)
        secret=read_private(secret_path,uid)
        validate(request,secret,policy,ident)
        status(queue,ident,'VALIDATING',gid)
        # A protected durable intent prevents automatic replay after interruption.
        fd=os.open(ledger/(ident+'.started'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as stream: stream.write(utc())
        status(queue,ident,'DEPLOYING',gid)
        dispatched=True
        result=driver(secret)
        if result!={'healthy_services':3,'admin_created':True,'registration_disabled':True,'unrelated_unchanged':True}:
            raise RuntimeError('unverified result')
        status(queue,ident,'SUCCEEDED',gid)
        atomic_public(ledger/(ident+'.done'),{'utc':utc(),'state':'SUCCEEDED'})
        return 'SUCCEEDED'
    except FileExistsError:
        status(queue,ident,'UNKNOWN',gid)
        return 'UNKNOWN'
    except Exception:
        outcome='UNKNOWN' if dispatched else 'FAILED'
        status(queue,ident,outcome,gid)
        return outcome
    finally:
        # Never retain submitted credentials in history or retry them automatically.
        if secret_path.exists() and not secret_path.is_symlink(): secret_path.unlink()

def ssh_driver(policy, source, secret):
    host,user,port=policy['host'],policy['ssh_user'],policy['ssh_port']
    if not re.fullmatch(r'[a-zA-Z0-9.:-]+',host) or host.startswith('-') or not re.fullmatch(r'[a-z_][a-z0-9_-]{0,31}',user) or type(port) is not int or not 1<=port<=65535:
        raise ValueError('invalid protected mapping')
    payload=dict(secret,compose_sha256=policy['compose_sha256'])
    encoded=base64.b64encode(json.dumps(payload).encode()).decode()
    remote='import base64,json\nPAYLOAD=json.loads(base64.b64decode('+repr(encoded)+'))\n'+source
    args=['sudo','-n','-u','fallback-agent','ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','HostKeyAlgorithms=ssh-ed25519','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','ForwardAgent=no','-o','ClearAllForwardings=yes','-T','-p',str(port),user+'@'+host,'python3','-']
    result=subprocess.run(args,input=remote,text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=420,check=True)
    if len(result.stdout)>4096: raise ValueError('oversized result')
    return json.loads(result.stdout)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy',type=Path,required=True)
    parser.add_argument('--wait-seconds',type=int,default=0)
    args=parser.parse_args()
    if os.geteuid()!=0 or not 0<=args.wait_seconds<=1800: parser.error('root and bounded wait required')
    policy=read_private(args.policy,0)
    queue=Path(policy['queue']); ledger=Path(policy['ledger']); data=queue.parent
    for path in (args.policy.parent,ledger):
        info=path.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or info.st_mode&0o077: raise ValueError('unsafe protected state')
    # Pin directory descriptors: a compromised PHP process cannot redirect root
    # writes by renaming its queue and replacing it with a directory symlink.
    queue_fd=os.open(queue,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    data_fd=os.open(data,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    for fd in (queue_fd,data_fd):
        info=os.fstat(fd)
        if info.st_uid!=policy['web_uid'] or info.st_mode&0o077: raise ValueError('unsafe web state')
    queue=Path('/proc/self/fd')/str(queue_fd);data=Path('/proc/self/fd')/str(data_fd)
    source_path=Path(policy['remote_source']); info=source_path.stat()
    if source_path.is_symlink() or info.st_uid!=0 or info.st_mode&0o022: raise ValueError('unsafe worker source')
    source=source_path.read_text()
    with open(ledger/'worker.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if any(not p.with_suffix('.done').exists() for p in ledger.glob('*.started')):
            raise ValueError('interrupted operation requires operator reconciliation')
        # Exactly one pre-authorized attempt per explicit operator invocation.
        deadline=time.monotonic()+args.wait_seconds
        try:
            while True:
                atomic_public(data/'install-worker.json',dict(utc=utc(),node=policy['node'],template=TEMPLATE,ready=True),policy['web_gid'])
                paths=sorted(queue.glob('*.request.json'),key=lambda p:p.lstat().st_mtime)
                for path in paths:
                    ident=path.name.removesuffix('.request.json')
                    if not re.fullmatch('[a-f0-9]{32}',ident): continue
                    if (ledger/(ident+'.attempted')).exists(): continue
                    # Withdraw readiness before consuming the only allowed attempt.
                    atomic_public(data/'install-worker.json',dict(utc=utc(),node=policy['node'],template=TEMPLATE,ready=False),policy['web_gid'])
                    outcome=run_one(queue,ledger,policy,lambda secret:ssh_driver(policy,source,secret),ident,policy['web_uid'],policy['web_gid'])
                    print(json.dumps({'id':ident,'state':outcome}),flush=True)
                    return
                if time.monotonic()>=deadline: return
                time.sleep(3)
        finally:
            atomic_public(data/'install-worker.json',dict(utc=utc(),node=policy['node'],template=TEMPLATE,ready=False),policy['web_gid'])

if __name__=='__main__': main()
