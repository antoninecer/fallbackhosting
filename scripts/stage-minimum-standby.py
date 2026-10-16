#!/usr/bin/env python3
"""Freeze a reviewable root-owned candidate under ignored repository-local .local.

Does not install units, change /etc, switch a release or reload any service.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from standby.snapshot import verify
from standby.gateway import server_locations

ROOT=Path(__file__).resolve().parents[1]
CODE=['standby/__init__.py','standby/control.py','standby/gateway.py','standby/snapshot.py',
      'operations/__init__.py','operations/core.py','operations/protocol.py']


def main():
    if os.geteuid()!=0:raise ValueError('Root ownership staging required')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    base=ROOT/'.local/standby-candidate'
    if base.exists():raise ValueError('Candidate already exists; reconcile before restaging')
    base.mkdir(mode=0o755)
    def git_file(name):return subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)
    spec=importlib.util.spec_from_file_location('release_checker',ROOT/'scripts/verify-center-release.py');checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
    admin=base/'admin';admin.mkdir()
    for name,source in checker.SOURCES.items():
        dest=admin/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(git_file(source))
    artifact=(ROOT/'.local/standby-admin-artifact/current').resolve(strict=True)
    shutil.copytree(artifact,admin/'center-artifact')
    bundle=base/'code';bundle.mkdir()
    for name in CODE:
        dest=bundle/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(git_file(name))
    for name in ('fallback-standby-demo.service','fallback-standby-demo.socket'):(base/name).write_bytes(git_file('deploy/'+name))
    release=(ROOT/'.local/standby-publish/current').resolve();report=verify(release)
    shutil.copytree(release,base/'snapshot')
    inventory=json.loads(Path('/var/lib/fallback-web/admin/inventory.json').read_text())
    node=next(n for n in inventory['servers'] if n['id']=='ctx1' and n['enabled'])
    origin='http://'+node['host']+':18080'
    assert origin==json.loads((ROOT/'.local/standby-review/transport.json').read_text())['origin']
    assert node['observations']['fingerprint']['status']=='PASS'
    policy={'runtime':'/var/lib/fallback-standby-demo/runtime','origin':origin,'web_uid':pwd.getpwnam('fallback-web').pw_uid,'service_uid':pwd.getpwnam('www-data').pw_uid,
            'actor':json.loads(Path('/var/lib/fallback-web/admin/auth.json').read_text())['username'],
            'snapshot':{'release':report['release'],'remote_backup':'VERIFIED_READBACK_RESTORE','source_bytes':report['image_source_bytes'],'optimized_bytes':report['image_result_bytes']}}
    (base/'policy.json').write_text(json.dumps(policy,indent=2))
    site=Path('/etc/nginx/sites-available/lab.ventureout.cz');before=site.read_text()
    assert '/demo/' not in before and '# BEGIN FallbackHosting' not in before
    fragment=server_locations(origin,'/var/www/fallback-standby-demo/current','/var/lib/fallback-standby-demo/runtime/unhealthy','/var/lib/fallback-standby-demo/runtime/maintenance',prefix='/demo')
    i=before.rfind('\n}');assert i>0
    (base/'lab-before.conf').write_text(before)
    (base/'lab-candidate.conf').write_text(before[:i]+'\n    # BEGIN FallbackHosting isolated public demo\n'+fragment+'\n    # END FallbackHosting isolated public demo\n'+before[i:])
    previous=Path('/var/www/fallback-admin/current').resolve()
    metadata={'revision':revision,'previous_admin':str(previous),'admin_manifest_sha256':hashlib.sha256((admin/'center-artifact/manifest.json').read_bytes()).hexdigest(),
              'lab_before_sha256':hashlib.sha256(before.encode()).hexdigest(),'snapshot_release':report['release'],'snapshot_sha256':hashlib.sha256((base/'snapshot/manifest.json').read_bytes()).hexdigest(),
              'inventory_sha256':hashlib.sha256(Path('/var/lib/fallback-web/admin/inventory.json').read_bytes()).hexdigest(),
              'auth_sha256':hashlib.sha256(Path('/var/lib/fallback-web/admin/auth.json').read_bytes()).hexdigest()}
    (base/'metadata.json').write_text(json.dumps(metadata,indent=2))
    for path in [base,*base.rglob('*')]:
        assert not path.is_symlink();os.chown(path,0,0);path.chmod(0o755 if path.is_dir() else 0o644)
    (base/'policy.json').chmod(0o600)
    checker.verify(admin,revision,metadata['admin_manifest_sha256'],require_root=True)
    hashes={p.relative_to(base).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(base.rglob('*')) if p.is_file()}
    (base/'manifest.json').write_text(json.dumps(hashes,sort_keys=True,indent=2)+'\n');(base/'manifest.json').chmod(0o600)
    print(json.dumps({'staging':'PASS_ROOT_OWNED','revision':revision,'admin':'EXACT_GIT_VERIFIED','static':'INTEGRITY_VERIFIED','files':len(hashes),'activation':'NOT_PERFORMED'}))


if __name__=='__main__':main()
