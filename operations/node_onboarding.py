"""Private peer-authenticated node enrollment and explicit runtime preparation."""
import argparse
import base64
from datetime import datetime,timezone
import fcntl
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import pwd
import re
import selectors
import signal
import socket
import stat
import subprocess
import threading

from operations.core import Denied,exact
from operations.protocol import serve_connection
from standby.gateway import atomic_json


def utc():return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def validate(spec):
    exact(spec,'id host ssh_port ssh_user fingerprint')
    if not isinstance(spec['id'],str) or not re.fullmatch('[a-z][a-z0-9-]{0,39}',spec['id']):raise Denied('INVALID_NODE')
    if not isinstance(spec['host'],str):raise Denied('TAILNET_ADDRESS_REQUIRED')
    try:address=ipaddress.ip_address(spec['host'])
    except (ValueError,TypeError):raise Denied('TAILNET_ADDRESS_REQUIRED')
    if address not in ipaddress.ip_network('100.64.0.0/10'):raise Denied('TAILNET_ADDRESS_REQUIRED')
    if type(spec['ssh_port']) is not int or not 1<=spec['ssh_port']<=65535:raise Denied('INVALID_PORT')
    if not isinstance(spec['ssh_user'],str) or not re.fullmatch('[a-z_][a-z0-9_-]{0,31}',spec['ssh_user']):raise Denied('INVALID_ACCOUNT')
    if not isinstance(spec['fingerprint'],str) or not re.fullmatch('SHA256:[A-Za-z0-9+/]{43}',spec['fingerprint']):raise Denied('SERVER_FINGERPRINT_REQUIRED')
    return spec


class SSHDriver:
    def __init__(self,root,home,source,max_reply=16384):
        self.root,self.home,self.source=Path(root),Path(home),Path(source)
        self.max_reply=max_reply
        self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
    def __call__(self,spec,action):
        validate(spec);folder=self.root/spec['id'];folder.mkdir(mode=0o700,exist_ok=True)
        scan=subprocess.run(['ssh-keyscan','-T','5','-p',str(spec['ssh_port']),'-t','ed25519',spec['host']],capture_output=True,text=True,timeout=15)
        lines=[line for line in scan.stdout.splitlines() if line and not line.startswith('#')]
        if len(lines)!=1:raise Denied('HOST_KEY_UNAVAILABLE')
        pinned=folder/'known_hosts';temp=folder/'key.pending';temp.write_text(lines[0]+'\n');temp.chmod(0o600)
        try:
            digest=subprocess.check_output(['ssh-keygen','-lf',str(temp),'-E','sha256'],text=True,timeout=5).split()[1]
            if digest!=spec['fingerprint']:raise Denied('HOST_KEY_MISMATCH')
            temp.replace(pinned)
        finally:temp.unlink(missing_ok=True)
        body=self.source.read_text()
        if body.count('PAYLOAD_PLACEHOLDER')!=1:raise ValueError('Fixed payload binding required')
        body=body.replace('PAYLOAD_PLACEHOLDER',repr({'action':action}))
        args=['ssh','-F','/dev/null','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','PasswordAuthentication=no','-o','KbdInteractiveAuthentication=no','-o','StrictHostKeyChecking=yes','-o','HostKeyAlgorithms=ssh-ed25519','-o','UserKnownHostsFile='+str(pinned),'-o','GlobalKnownHostsFile=/dev/null','-o','IdentitiesOnly=yes','-o','IdentityAgent=none','-o','ForwardAgent=no','-o','ClearAllForwardings=yes','-i',str(self.home/'.ssh/id_ed25519'),'-p',str(spec['ssh_port']),'-T',spec['ssh_user']+'@'+spec['host'],'python3','-']
        result=subprocess.run(args,input=body,capture_output=True,text=True,timeout=660)
        if result.returncode or len(result.stdout)>self.max_reply:raise Denied('SSH_OR_REMOTE_CHECK_FAILED')
        reply=json.loads(result.stdout)
        if reply.get('ok') is not True:raise Denied('REMOTE_PREPARATION_REQUIRES_REVIEW')
        facts=reply['facts']
        if facts.get('user')!=spec['ssh_user']:raise Denied('REMOTE_ACCOUNT_MISMATCH')
        return facts


class Onboarding:
    def __init__(self,runtime,uid,actor,public_key,driver):
        self.root=Path(runtime);self.root.mkdir(mode=0o700,parents=True,exist_ok=True)
        self.uid,self.actor,self.public_key,self.driver=uid,actor,public_key,driver
        self.lock=threading.RLock()
        # A second service process may not dispatch against this runtime.
        self.process_lock=(self.root/'service.lock').open('a')
        fcntl.flock(self.process_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for p in self.root.glob('*.json'):
            state=json.loads(p.read_text())
            if state.get('phase') in ('CHECKING','INITIALIZING'):
                state.update(phase='NEEDS_REVIEW',error='INTERRUPTED_OPERATION',utc=utc(),revision=state['revision']+1);atomic_json(p,state)
    def authorize(self,request,uid):
        if uid!=self.uid or request.get('actor')!=self.actor:raise Denied('FORBIDDEN')
    def path(self,ident):
        if not isinstance(ident,str) or not re.fullmatch('[a-z][a-z0-9-]{0,39}',ident):raise Denied('INVALID_NODE')
        return self.root/(ident+'.json')
    def view(self,ident):
        path=self.path(ident)
        return json.loads(path.read_text()) if path.exists() else None
    def read(self,request,uid):
        exact(request,'kind actor node');self.authorize(request,uid)
        if request['kind']!='view':raise Denied('UNKNOWN_OPERATION')
        with self.lock:return {'ok':True,'public_key':self.public_key,'job':self.view(request['node'])}
    def submit(self,request,uid):
        self.authorize(request,uid)
        if isinstance(request.get('kind'),str) and request['kind'].startswith('migration_'):
            if not getattr(self,'migration',None):raise Denied('MIGRATION_NOT_CONFIGURED')
            return self.migration.submit(request)
        with self.lock:
            if request.get('kind')=='inspect_node':
                exact(request,'kind actor spec');spec=validate(request['spec']);old=self.view(spec['id'])
                if old and old['phase'] in ('CHECKING','INITIALIZING','NEEDS_REVIEW'):raise Denied('BUSY_OR_REVIEW_REQUIRED')
                if sum(1 for p in self.root.glob('*.json'))>=100 and not old:raise Denied('NODE_LIMIT')
                state={'id':spec['id'],'spec':spec,'phase':'CHECKING','revision':(old['revision'] if old else 0)+1,'utc':utc()}
            elif request.get('kind')=='initialize_node':
                exact(request,'kind actor node revision confirmation');state=self.view(request['node'])
                if not state or state['phase']!='READY' or type(request['revision']) is not int or request['revision']!=state['revision']:raise Denied('STALE_OR_NOT_READY')
                if request['confirmation'] is not True:raise Denied('CONFIRMATION_REQUIRED')
                if not state['facts'].get('preparation_supported'):raise Denied('UNSUPPORTED_PREPARATION')
                state={**state,'phase':'INITIALIZING','revision':state['revision']+1,'utc':utc()}
            else:raise Denied('UNKNOWN_OPERATION')
            atomic_json(self.path(state['id']),state)
            return {'ok':True,'job':state}
    def advance(self):
        with self.lock:
            candidates=[json.loads(p.read_text()) for p in sorted(self.root.glob('*.json'))]
            state=next((s for s in candidates if s['phase'] in ('CHECKING','INITIALIZING')),None)
        if state is None:return
        phase=state['phase']
        try:
            facts=self.driver(state['spec'],'inspect' if phase=='CHECKING' else 'prepare')
            if phase=='INITIALIZING' and not (facts.get('docker_ready') and facts.get('compose_version')):raise Denied('RUNTIME_NOT_READY')
            result={**state,'phase':'READY' if phase=='CHECKING' else 'SUCCEEDED','facts':facts,'utc':utc(),'revision':state['revision']+1}
        except Exception as error:
            result={**state,'phase':'FAILED' if phase=='CHECKING' else 'NEEDS_REVIEW','error':error.code if isinstance(error,Denied) else 'OPERATION_FAILED','utc':utc(),'revision':state['revision']+1}
        with self.lock:atomic_json(self.path(state['id']),result)


def main():
    p=argparse.ArgumentParser();p.add_argument('--policy',type=Path,required=True);args=p.parse_args()
    info=args.policy.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022:raise ValueError('Immutable root policy required')
    policy=json.loads(args.policy.read_text());account=pwd.getpwnam('fallback-agent')
    if os.geteuid()!=account.pw_uid:raise ValueError('Incorrect service identity')
    public=(Path(account.pw_dir)/'.ssh/id_ed25519.pub').read_text().strip()
    api=Onboarding(policy['runtime'],policy['web_uid'],policy['actor'],public,SSHDriver(Path(policy['runtime'])/'trust',account.pw_dir,policy['source']))
    if policy.get('migration_nodes'):
        from operations.volume_migration import VolumeMigration
        nodes=policy['migration_nodes']
        for spec in nodes.values():validate(spec)
        api.migration=VolumeMigration(Path(policy['runtime'])/'migration',nodes,SSHDriver(Path(policy['runtime'])/'migration-trust',account.pw_dir,policy['migration_source'],max_reply=4*1024*1024))
    listener=socket.socket(fileno=3);selector=selectors.DefaultSelector();selector.register(listener,selectors.EVENT_READ);stop=threading.Event();failed=threading.Event()
    signal.signal(signal.SIGTERM,lambda *unused:stop.set());signal.signal(signal.SIGINT,lambda *unused:stop.set())
    def work():
        try:
            while not stop.wait(.2):
                api.advance()
                if getattr(api,'migration',None):api.migration.advance()
        except Exception:failed.set();stop.set()
    thread=threading.Thread(target=work);thread.start()
    try:
        while not stop.is_set():
            for key,mask in selector.select(.2):
                connection,_=listener.accept();serve_connection(connection,api)
    finally:stop.set();thread.join();listener.close();selector.close()
    if failed.is_set():raise RuntimeError('Private state requires review')


if __name__=='__main__':main()
