"""Fixed owned demo HTML update with retained old image/container and rollback."""
import base64
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import time
import urllib.request

NAME='fallbackhosting-standby-demo'
JOURNAL=Path.home()/'.fallback-standby-demo'


def run(args,data=None,timeout=40):
    return subprocess.run(args,input=data,check=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=timeout).stdout


def inspect(ident):return json.loads(run(['docker','container','inspect',ident]))[0]


def main():
    if set(PAYLOAD)!={'html','sha256'}:raise ValueError('Exact fixed HTML update required')
    body=base64.b64decode(PAYLOAD['html'],validate=True)
    if len(body)>32768 or hashlib.sha256(body).hexdigest()!=PAYLOAD['sha256'] or b'<form' in body or b'<script' in body:raise ValueError('Expected bounded inert demo HTML')
    saved=json.loads((JOURNAL/'owned.json').read_text());old=inspect(saved['id'])
    if old['Name']!='/'+NAME or old['Image']!=saved['image'] or old['Config']['Labels'].get('io.fallback.app')!='standby-demo':raise ValueError('Owned demo identity drift')
    originals=[inspect(i) for i in run(['docker','ps','-aq','--no-trunc']).decode().split() if i!=saved['id']]
    baseline=[(d['Id'],d['Image'],d['State']['Running'],d['State']['StartedAt'],d['RestartCount']) for d in originals]
    timestamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');tag='fallbackhosting/standby-demo:page-'+timestamp
    base='fallbackhosting/standby-demo:initial'
    if json.loads(run(['docker','image','inspect',base]))[0]['Id']!=old['Image']:raise ValueError('Base image tag drift')
    dockerfile=('FROM '+base+'\nCOPY --chown=1000:1000 index.html /www/index.html\n').encode()
    buf=io.BytesIO()
    with tarfile.open(fileobj=buf,mode='w') as tar:
        for name,data in [('Dockerfile',dockerfile),('index.html',body)]:
            info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;tar.addfile(info,io.BytesIO(data))
    run(['docker','build','--pull=false','--network=none','--tag',tag,'-'],buf.getvalue(),timeout=120)
    image=json.loads(run(['docker','image','inspect',tag]))[0]['Id']
    backup=JOURNAL/('page-update-'+timestamp+'.json')
    state={'phase':'PREPARED','previous':saved,'new_image':image,'html_sha256':PAYLOAD['sha256'],'old_name':NAME+'-previous-'+timestamp}
    backup.write_text(json.dumps(state));backup.chmod(0o600)
    ident=None;renamed=False
    try:
        run(['docker','stop','--time','3',saved['id']]);run(['docker','rename',saved['id'],state['old_name']]);renamed=True
        ident=run(['docker','create','--name',NAME,'--label','io.fallback.app=standby-demo','--label','io.fallback.managed=true','--restart','unless-stopped','--read-only','--user','1000:1000','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','48m','--cpus','0.25','--pids-limit','32','--log-driver','local','--log-opt','max-size=1m','--log-opt','max-file=2','--publish',saved['bind_host']+':18080:8080',image]).decode().strip()
        run(['docker','start',ident])
        for _ in range(60):
            try:
                with urllib.request.urlopen('http://'+saved['bind_host']+':18080/index.html',timeout=2) as r:
                    if r.read()!=body:raise ValueError('HTML mismatch')
                break
            except Exception:time.sleep(.2)
        else:raise ValueError('New HTML not healthy')
        for before in baseline:
            d=inspect(before[0]);assert before==(d['Id'],d['Image'],d['State']['Running'],d['State']['StartedAt'],d['RestartCount'])
        updated={**saved,'id':ident,'image':image};temp=JOURNAL/'owned.pending';temp.write_text(json.dumps(updated));temp.chmod(0o600);temp.replace(JOURNAL/'owned.json')
        state.update(phase='VERIFIED_OLD_CONTAINER_RETAINED',new=updated);backup.write_text(json.dumps(state))
        print(json.dumps({'update':'PASS','html_sha256':PAYLOAD['sha256'],'unrelated_unchanged':True,'old_container_retained':True,'restart_policy':'unless-stopped'}))
    except Exception:
        if ident:
            subprocess.run(['docker','stop','--time','2',ident],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            run(['docker','rm',ident])
        if renamed:run(['docker','rename',saved['id'],NAME])
        run(['docker','start',saved['id']]);state['phase']='ROLLED_BACK';backup.write_text(json.dumps(state));raise


if __name__=='__main__':
    PAYLOAD=PAYLOAD_PLACEHOLDER
    main()
