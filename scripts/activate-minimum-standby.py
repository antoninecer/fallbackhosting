#!/usr/bin/env python3
"""Exact scoped activation/rollback. Requires separate operator authorization.

Default check mode is read-only. Never modify DNS/firewall/VPN/other sites.
"""
import argparse
from datetime import datetime, timezone
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

ROOT=Path(__file__).resolve().parents[1]
SITE=Path('/etc/nginx/sites-available/lab.ventureout.cz')
CURRENT=Path('/var/www/fallback-admin/current')
PUBLIC=Path('/var/www/fallback-standby-demo')
SERVICE=Path('/var/lib/fallback-standby-demo')
UNITS=('fallback-standby-demo.socket','fallback-standby-demo.service')


def run(*args):
    subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=40)


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,data,mode=0o644):
    temp=path.with_name(path.name+'.fallback-pending')
    with temp.open('xb') as stream:stream.write(data)
    temp.chmod(mode);os.replace(temp,path)


def state(backup,data):
    path=backup/'journal.json'
    write(path,json.dumps(data,indent=2).encode(),0o600)


def switch(target):
    temp=CURRENT.with_name('.fallback-demo-current')
    temp.symlink_to(target,target_is_directory=True);os.replace(temp,CURRENT)


def candidate_check(base):
    manifest=json.loads((base/'manifest.json').read_text())
    actual={p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}
    if actual!=set(manifest)|{'manifest.json'}:raise ValueError('Candidate file set changed')
    for p in [base,*base.rglob('*')]:
        if p.is_symlink() or p.stat().st_uid!=0 or p.stat().st_mode&0o022:raise ValueError('Candidate must be frozen root-owned files')
    for name,value in manifest.items():
        if digest(base/name)!=value:raise ValueError('Candidate hash changed')
    metadata=json.loads((base/'metadata.json').read_text())
    spec=importlib.util.spec_from_file_location('checker',ROOT/'scripts/verify-center-release.py');checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
    checker.verify(base/'admin',metadata['revision'],metadata['admin_manifest_sha256'],require_root=True)
    verify(base/'snapshot')
    if digest(SITE)!=metadata['lab_before_sha256'] or CURRENT.resolve()!=Path(metadata['previous_admin']):raise ValueError('Live state drifted since preparation')
    if digest('/var/lib/fallback-web/admin/inventory.json')!=metadata['inventory_sha256'] or digest('/var/lib/fallback-web/admin/auth.json')!=metadata['auth_sha256']:raise ValueError('Private inventory/auth changed since preparation')
    for path in [PUBLIC,SERVICE,*[Path('/etc/systemd/system')/name for name in UNITS],Path('/var/lib/fallback-web/admin/standby.sock')]:
        if os.path.lexists(path):raise ValueError('Existing target requires reconciliation')
    if (Path('/var/www/fallback-admin/releases')/metadata['revision']).exists():raise ValueError('Release target already exists')
    run('nginx','-t');run('php-fpm8.3','-t')
    run('/usr/bin/python3',str(ROOT/'scripts/activate-admin.py'),'verify')
    return metadata,manifest


def rollback(backup):
    if backup.parent!=Path('/var/backups') or not backup.name.startswith('fallbackhosting-standby-demo-'):raise ValueError('Unexpected rollback journal path')
    data=json.loads((backup/'journal.json').read_text())
    for name in UNITS:
        path=Path('/etc/systemd/system')/name
        if path.exists() and digest(path)!=data['unit_hashes'][name]:raise ValueError('New unit changed; operator reconciliation required')
    for name in UNITS:
        if (Path('/etc/systemd/system')/name).exists():
            subprocess.run(['systemctl','disable','--now',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=40,check=True)
    nginx_changed=False;fpm_changed=False
    if digest(SITE)==data['candidate_hash']:
        write(SITE,(backup/'lab-before.conf').read_bytes());nginx_changed=True
    elif digest(SITE)!=data['before_hash']:raise ValueError('Vhost changed concurrently; do not overwrite')
    if CURRENT.resolve()==Path(data['new_admin']):switch(Path(data['previous_admin']));fpm_changed=True
    elif CURRENT.resolve()!=Path(data['previous_admin']):raise ValueError('Admin changed concurrently; do not overwrite')
    if fpm_changed:run('php-fpm8.3','-t');run('systemctl','reload','php8.3-fpm')
    if nginx_changed:run('nginx','-t');run('systemctl','reload','nginx')
    run('/usr/bin/python3',str(ROOT/'scripts/activate-admin.py'),'verify')
    data['phase']='ROLLED_BACK_PRESERVED_DATA';state(backup,data)
    print('PASS scoped rollback; data/artifacts/new disabled unit files retained')


def apply(base):
    metadata,manifest=candidate_check(base)
    backup=Path('/var/backups')/('fallbackhosting-standby-demo-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    backup.mkdir(mode=0o700)
    shutil.copyfile(SITE,backup/'lab-before.conf');(backup/'lab-before.conf').chmod(0o600)
    new_admin=Path('/var/www/fallback-admin/releases')/metadata['revision']
    data={'phase':'PREPARED','candidate_hash':manifest['lab-candidate.conf'],'before_hash':metadata['lab_before_sha256'],'previous_admin':metadata['previous_admin'],'new_admin':str(new_admin),'unit_hashes':{name:manifest[name] for name in UNITS}}
    state(backup,data)
    try:
        PUBLIC.mkdir(mode=0o755);(PUBLIC/'releases').mkdir(mode=0o755)
        shutil.copytree(base/'snapshot',PUBLIC/'releases'/metadata['snapshot_release'])
        (PUBLIC/'current').symlink_to(PUBLIC/'releases'/metadata['snapshot_release'],target_is_directory=True)
        SERVICE.mkdir(mode=0o755);shutil.copytree(base/'code',SERVICE/'code')
        policy=json.loads((base/'policy.json').read_text())
        write(SERVICE/'policy.json',json.dumps(policy,indent=2).encode(),0o640)
        account=pwd.getpwnam('www-data');os.chown(SERVICE/'policy.json',0,account.pw_gid)
        runtime=SERVICE/'runtime';runtime.mkdir(mode=0o750);os.chown(runtime,account.pw_uid,account.pw_gid)
        (runtime/'unhealthy').touch();os.chown(runtime/'unhealthy',account.pw_uid,account.pw_gid)
        shutil.copytree(base/'admin',new_admin)
        for name in UNITS:write(Path('/etc/systemd/system')/name,(base/name).read_bytes())
        data['phase']='FILES_INSTALLED_NOT_ACTIVATED';state(backup,data)
        run('systemctl','daemon-reload')
        run('systemctl','enable','--now','fallback-standby-demo.socket')
        run('systemctl','enable','--now','fallback-standby-demo.service')
        run('systemctl','is-active','--quiet','fallback-standby-demo.service')
        switch(new_admin);run('php-fpm8.3','-t');run('systemctl','reload','php8.3-fpm')
        write(SITE,(base/'lab-candidate.conf').read_bytes())
        run('nginx','-t');run('systemctl','reload','nginx')
        data['phase']='ACTIVATED_NEEDS_LIVE_ACCEPTANCE';state(backup,data)
        run('/usr/bin/python3',str(ROOT/'scripts/activate-admin.py'),'verify')
        print(json.dumps({'activation':'NEEDS_LIVE_ACCEPTANCE','journal':str(backup),'revision':metadata['revision']}))
    except Exception:
        data['phase']='FAILED_NEEDS_SCOPED_ROLLBACK';state(backup,data)
        rollback(backup)
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,default=ROOT/'.local/standby-candidate');p.add_argument('--apply-approved-scope',action='store_true');p.add_argument('--rollback',type=Path);args=p.parse_args()
    if os.geteuid()!=0:raise ValueError('Run root only within exact operator-approved scope')
    if args.rollback:
        if not args.apply_approved_scope:p.error('Rollback also requires approved exact scope')
        rollback(args.rollback)
    elif args.apply_approved_scope:apply(args.candidate)
    else:
        metadata,manifest=candidate_check(args.candidate)
        print(json.dumps({'candidate':'PASS','revision':metadata['revision'],'activation':'NOT_PERFORMED','required_operator_scope':'docs/MINIMUM-STANDBY.md'}))


if __name__=='__main__':main()
