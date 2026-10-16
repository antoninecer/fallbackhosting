"""Fixed remote payload for the retained, previously verified ctx1 installation.

PAYLOAD is supplied on stdin by the isolated worker, never as shell arguments.
No caller may supply paths, commands, images, ports, mounts or SSH destinations.
"""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import urllib.request

HELPER='coollabsio/coolify-helper@sha256:c7a7748b233da32a7541213bd6c124d104d2221ac7d9020976dbfa02ba88e57d'
NAMES=('coolify','coolify-db','coolify-redis')
journal=Path.home()/'.fallback-coolify-deploy'

def run(args,timeout=30,env=None):
    result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=timeout,check=True,env=env)
    if len(result.stdout)>1048576: raise ValueError('oversized internal output')
    return result.stdout

def query(code,env=None):
    args=['docker','exec']
    if env is not None:
        args+=['-e','ROOT_USER_EMAIL','-e','ROOT_USER_PASSWORD','-e','ROOT_USERNAME']
    output=run(args+['coolify','php','artisan','tinker','--execute',code],env=env)
    for line in output.splitlines():
        if line.startswith('{') and line.endswith('}'): return json.loads(line)
    raise ValueError('native query did not return verified JSON')

def main():
    assert (journal/'wizard-removal-done.json').is_file()
    assert hashlib.sha256((journal/'compose.json').read_bytes()).hexdigest()==PAYLOAD['compose_sha256']
    assert all(subprocess.run(['docker','container','inspect',n],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10).returncode!=0 for n in NAMES)
    baseline=json.loads((journal/'wizard-removal-started.json').read_text())['others']
    volumes=json.loads(run(['docker','volume','inspect','coolify-db','coolify-redis']))
    assert len(volumes)==2 and all(v.get('Labels',{}).get('io.fallback.app')=='coolify-control' for v in volumes)
    helper=['docker','run','--rm','--pull=never','--network','none','--memory','256m','--cpus','0.5','--pids-limit','128','--label','io.fallback.app=coolify-install','--mount','type=bind,src=/data/coolify/source,dst=/data/coolify/source,readonly','--mount','type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock',HELPER]
    actual_compose=run(helper+['cat','/data/coolify/source/compose.json'])
    assert hashlib.sha256(actual_compose.encode()).hexdigest()==PAYLOAD['compose_sha256']
    compose=helper+['docker','compose','--project-name','fallback-coolify','--env-file','/data/coolify/source/.env','-f','/data/coolify/source/compose.json']
    config=json.loads(run(compose+['config','--format','json']))
    expected=json.loads((journal/'compose.json').read_text())
    assert set(config['services'])=={'coolify','postgres','redis'}
    for name,service in config['services'].items():
        assert service['image']==expected['services'][name]['image'] and '@sha256:' in service['image']
        assert not service.get('privileged') and not service.get('pid') and not service.get('network_mode')
        assert all(p.get('host_ip')=='127.0.0.1' for p in service.get('ports',[]))
        assert not service.get('ports') or name=='coolify'
    settings=config['services']['coolify']['environment']
    assert settings['AUTOUPDATE']=='false' and settings['NGINX_LISTEN_IP_PROTOCOL']=='ipv4'
    for service in config['services'].values(): run(['docker','image','inspect',service['image']])
    for old in baseline:
        d=json.loads(run(['docker','container','inspect',old['Id']]))[0]
        assert old==({k:d[k] for k in ('Id','Image','RestartCount')}|dict(running=d['State']['Running'],started=d['State']['StartedAt']))
    if PAYLOAD.get('preflight_only') is True:
        print(json.dumps(dict(preflight='PASS',containers_absent=3,retained_volumes=2,images_cached=True,unrelated_unchanged=True)))
        return
    marker=journal/'wizard-install-started.json'
    if marker.exists(): raise ValueError('previous attempt requires reconciliation')
    marker.write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}));marker.chmod(0o600)
    run(compose+['up','-d','--pull','never','--wait','--wait-timeout','180'],timeout=240)
    rows=json.loads(run(['docker','container','inspect',*NAMES]))
    assert len(rows)==3 and all(d['Config']['Labels'].get('io.fallback.app')=='coolify-control' and d['Config']['Labels'].get('io.fallback.managed')=='true' and d['State'].get('Health',{}).get('Status')=='healthy' for d in rows)
    owned=[dict(name=d['Name'].lstrip('/'),id=d['Id']) for d in rows]
    owned_path=journal/'owned-containers.json';owned_path.write_text(json.dumps(owned));owned_path.chmod(0o600)
    assert query("echo json_encode(['users'=>App\\Models\\User::count()]);")=={'users':0}
    env=os.environ.copy();env.update(ROOT_USER_EMAIL=PAYLOAD['email'],ROOT_USER_PASSWORD=PAYLOAD['password'],ROOT_USERNAME='FallbackAdmin')
    run(['docker','exec','-e','ROOT_USER_EMAIL','-e','ROOT_USER_PASSWORD','-e','ROOT_USERNAME','coolify','php','artisan','db:seed','--class=RootUserSeeder','--force'],timeout=90,env=env)
    account=query("$u=App\\Models\\User::find(0); echo json_encode(['admin_created'=>$u!==null && $u->email===getenv('ROOT_USER_EMAIL') && Illuminate\\Support\\Facades\\Hash::check(getenv('ROOT_USER_PASSWORD'),$u->password) && $u->teams()->where('teams.id',0)->wherePivot('role','owner')->exists(),'registration_disabled'=>!App\\Models\\InstanceSettings::findOrFail(0)->is_registration_enabled]);",env)
    assert account=={'admin_created':True,'registration_disabled':True}
    with urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=15) as response: assert response.status==200
    for old in baseline:
        d=json.loads(run(['docker','container','inspect',old['Id']]))[0]
        assert old==({k:d[k] for k in ('Id','Image','RestartCount')}|dict(running=d['State']['Running'],started=d['State']['StartedAt']))
    print(json.dumps(dict(healthy_services=3,admin_created=True,registration_disabled=True,unrelated_unchanged=True)))

if __name__=='__main__': main()
