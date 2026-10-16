"""Operator-only fixed demo resource; PAYLOAD arrives through trusted SSH stdin.

No web interface accepts this payload or any command/image/path override.
"""
import base64
from datetime import datetime, timezone
import hashlib
import io
import ipaddress
import json
from pathlib import Path
import socket
import subprocess
import tarfile
import time
import urllib.request

NAME='fallbackhosting-standby-demo'
journal=Path.home()/'.fallback-standby-demo'


def run(args, data=None, timeout=30):
    result=subprocess.run(args,input=data,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=timeout,check=True)
    return result.stdout


def inspect(ident): return json.loads(run(['docker','container','inspect',ident]))[0]


def baseline():
    ids=run(['docker','ps','-aq','--no-trunc']).decode().split()
    if len(ids)>50:raise ValueError('bounded baseline required')
    return [{k:d[k] for k in ('Id','Image','RestartCount')}|dict(running=d['State']['Running'],started=d['State']['StartedAt']) for d in (inspect(ident) for ident in ids)]


def check_original(records):
    for old in records:
        d=inspect(old['Id'])
        assert old==({k:d[k] for k in ('Id','Image','RestartCount')}|dict(running=d['State']['Running'],started=d['State']['StartedAt']))


def main():
    action=PAYLOAD['action']
    if action=='deploy':
        if journal.exists():raise ValueError('existing journal requires reconciliation; do not repeat')
        ip=ipaddress.ip_address(PAYLOAD['bind_host'])
        assert ip in ipaddress.ip_network('100.64.0.0/10')
        with socket.socket() as probe:probe.bind((str(ip),18080))
        assert subprocess.run(['docker','container','inspect',NAME],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0
        journal.mkdir(mode=0o700)
        original=baseline()
        (journal/'before.json').write_text(json.dumps(original));(journal/'before.json').chmod(0o600)
        images=json.loads((Path.home()/'.fallback-coolify-deploy/images.json').read_text())
        image=images['docker.io/library/busybox:1.37']['digest']
        assert '@sha256:' in image
        files=PAYLOAD['files']
        assert set(files)=={'index.html','style.css','hero.jpg'}
        dockerfile=f'FROM {image}\nCOPY --chown=1000:1000 site /www\nUSER 1000:1000\nEXPOSE 8080\nCMD ["httpd","-f","-p","8080","-h","/www"]\n'
        entries={'Dockerfile':dockerfile.encode(),'site/health':b'fallback-demo-healthy\n','site/objednavka/index.html':'<!doctype html><html lang="cs"><meta charset="utf-8"><title>Ukázková objednávka</title><h1>Objednávka · pouze demo</h1><p>Toto není skutečný objednávkový systém.</p><a href="/">Zpět na kavárnu</a></html>'.encode()}
        for name,encoded in files.items():
            body=base64.b64decode(encoded,validate=True)
            assert len(body)<=8*1024*1024
            entries['site/'+name]=body
        buf=io.BytesIO()
        with tarfile.open(fileobj=buf,mode='w') as archive:
            for name,body in entries.items():
                member=tarfile.TarInfo(name);member.size=len(body);member.mode=0o644;archive.addfile(member,io.BytesIO(body))
        (journal/'started.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'build_sha256':hashlib.sha256(buf.getvalue()).hexdigest()}))
        tag='fallbackhosting/standby-demo:initial'
        run(['docker','build','--pull=false','--network=none','--tag',tag,'-'],buf.getvalue(),timeout=120)
        image_id=json.loads(run(['docker','image','inspect',tag]))[0]['Id']
        ident=run(['docker','create','--name',NAME,'--label','io.fallback.app=standby-demo','--label','io.fallback.managed=true','--read-only','--user','1000:1000','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','48m','--cpus','0.25','--pids-limit','32','--log-driver','local','--log-opt','max-size=1m','--log-opt','max-file=2','--publish',str(ip)+':18080:8080',image_id]).decode().strip()
        saved={'id':ident,'image':image_id,'bind_host':str(ip),'port':18080}
        (journal/'owned.json').write_text(json.dumps(saved));(journal/'owned.json').chmod(0o600)
        run(['docker','start',ident])
        for _ in range(40):
            try:
                with urllib.request.urlopen('http://'+str(ip)+':18080/health',timeout=2) as r:assert r.read()==b'fallback-demo-healthy\n'
                break
            except Exception:time.sleep(.25)
        else:raise ValueError('demo health unverified')
        check_original(original)
        (journal/'ready.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat()}))
        print(json.dumps({'demo':'RUNNING','only_tailnet_binding':True,'unrelated_unchanged':True,'image_pull':False,'volumes':False}))
        return
    if action not in ('status','stop','start','remove'):raise ValueError('unsupported fixed action')
    saved=json.loads((journal/'owned.json').read_text());d=inspect(saved['id'])
    assert d['Id']==saved['id'] and d['Config']['Image']==saved['image']
    assert d['Config']['Labels'].get('io.fallback.app')=='standby-demo' and d['Config']['Labels'].get('io.fallback.managed')=='true'
    if action=='stop':run(['docker','stop','--time','3',saved['id']])
    if action=='start':run(['docker','start',saved['id']])
    if action=='remove':
        if d['State']['Running']:run(['docker','stop','--time','3',saved['id']])
        run(['docker','rm',saved['id']])
        assert subprocess.run(['docker','container','inspect',saved['id']],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0
    check_original(json.loads((journal/'before.json').read_text()))
    print(json.dumps({'action':action,'owned_resource_verified':True,'unrelated_unchanged':True}))


if __name__=='__main__':
    PAYLOAD=PAYLOAD_PLACEHOLDER
    main()
