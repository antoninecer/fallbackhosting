"""Fixed SSH runtime preparation. No web-provided commands, packages or URLs."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.request

KEY_SHA256='e6c650e0700b1bf4868b693b30761b926844befc8a0acb7ac0dd9b1faf1b7423'
PACKAGES=['docker-ce','docker-ce-cli','containerd.io','docker-buildx-plugin','docker-compose-plugin']


def run(args, timeout=30, check=True):
    r=subprocess.run(args,capture_output=True,text=True,timeout=timeout)
    if check and r.returncode:raise RuntimeError('FIXED_COMMAND_FAILED')
    return r


def inspect():
    system={}
    for line in Path('/etc/os-release').read_text().splitlines():
        if '=' in line:
            k,v=line.split('=',1);system[k]=v.strip('"')
    sudo=run(['sudo','-n','true'],check=False).returncode==0
    docker=shutil.which('docker') is not None
    docker_command=['sudo','-n','docker'] if sudo else ['docker']
    ready=docker and run(docker_command+['info','--format','{{.ServerVersion}}'],check=False).returncode==0
    compose=run(docker_command+['compose','version','--short'],check=False).stdout.strip() if ready else ''
    version=run(docker_command+['version','--format','{{.Server.Version}}'],check=False).stdout.strip() if ready else ''
    return {'user':run(['id','-un']).stdout.strip(),'os':system.get('ID','unknown'),'version':system.get('VERSION_ID','unknown'),
            'cpus':os.cpu_count(),'memory_kib':int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemTotal:'))),
            'disk_available_bytes':shutil.disk_usage('/var').free,'sudo':sudo,'docker_cli':docker,'docker_ready':ready,
            'docker_version':version[:80],'compose_version':compose[:80],
            'preparation_supported':bool(ready and compose) or (sudo and system.get('ID')=='rocky' and system.get('VERSION_ID','').split('.')[0]=='9')}


def atomic(path,data):
    temp=path.with_suffix('.pending');temp.write_text(json.dumps(data,indent=2)+'\n');temp.chmod(0o600);temp.replace(path)


def prepare():
    facts=inspect()
    if facts['docker_ready'] and facts['compose_version']:return {**facts,'preparation':'ALREADY_READY'}
    if not facts['sudo'] or not facts['preparation_supported']:raise ValueError('UNSUPPORTED_OR_NO_SUDO')
    if facts['docker_cli']:raise ValueError('EXISTING_RUNTIME_REQUIRES_RECONCILIATION')
    if run(['sudo','-n','test','-e','/var/lib/docker'],check=False).returncode==0:raise ValueError('EXISTING_DATA_REQUIRES_RECONCILIATION')
    repo=Path('/etc/yum.repos.d/docker-ce.repo')
    if repo.exists():raise ValueError('EXISTING_REPOSITORY_REQUIRES_RECONCILIATION')
    base=Path.home()/'.fallback-node-bootstrap';base.mkdir(mode=0o700,exist_ok=True)
    journal=base/'journal.json'
    if journal.exists():raise ValueError('PREVIOUS_OPERATION_REQUIRES_RECONCILIATION')
    state={'phase':'STARTED','utc':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'before':facts,'packages':PACKAGES}
    atomic(journal,state)
    def step(name,args,timeout=240):
        state['phase']=name+'_INTENT';atomic(journal,state)
        r=run(args,timeout=timeout,check=False)
        log=base/(name+'.log');log.write_text((r.stdout+r.stderr)[-524288:]);log.chmod(0o600)
        if r.returncode:raise RuntimeError('PREPARATION_STEP_FAILED')
        state['phase']=name+'_PASS';atomic(journal,state)
    try:
        # Verify vendor signing key before any repository or package change.
        key=urllib.request.urlopen('https://download.docker.com/linux/centos/gpg',timeout=15).read(32768)
        if hashlib.sha256(key).hexdigest()!=KEY_SHA256:raise ValueError('VENDOR_SIGNING_KEY_CHANGED')
        pub=base/'docker-signing-key.asc';pub.write_bytes(key);pub.chmod(0o600)
        step('PREREQUISITES',['sudo','-n','dnf','-y','--setopt=install_weak_deps=False','install','dnf-plugins-core'])
        step('SIGNING_KEY',['sudo','-n','rpm','--import',str(pub)])
        step('REPOSITORY',['sudo','-n','dnf','config-manager','--add-repo','https://download.docker.com/linux/centos/docker-ce.repo'])
        step('PACKAGES',['sudo','-n','dnf','-y','--setopt=install_weak_deps=False','install',*PACKAGES],timeout=480)
        step('SERVICE',['sudo','-n','systemctl','enable','--now','docker'],timeout=60)
        after=inspect()
        if not after['docker_ready'] or not after['compose_version']:raise RuntimeError('RUNTIME_NOT_VERIFIED')
        state.update(phase='VERIFIED',after=after);atomic(journal,state)
        return {**after,'preparation':'VERIFIED'}
    except Exception:
        state['phase']='NEEDS_REVIEW';atomic(journal,state);raise


if __name__=='__main__':
    request=PAYLOAD_PLACEHOLDER
    if not isinstance(request,dict) or set(request)!={'action'} or request['action'] not in ('inspect','prepare'):raise ValueError('INVALID_REQUEST')
    try:print(json.dumps({'ok':True,'facts':inspect() if request['action']=='inspect' else prepare()}))
    except Exception:print(json.dumps({'ok':False,'error':'PREPARATION_REQUIRES_REVIEW'}))
