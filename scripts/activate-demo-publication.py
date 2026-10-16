#!/usr/bin/env python3
"""Journaled fixed-demo publication activation. No Nginx/DNS/remote runtime edits."""
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

ROOT=Path(__file__).resolve().parents[1]
BASE=Path('/var/lib/fallback-publication-demo')
PUBLIC=Path('/var/www/fallback-standby-demo')
ADMIN=Path('/var/www/fallback-admin/current')
UNITS=('fallback-publication-demo.socket','fallback-publication-demo.service')
CODE=('standby/__init__.py','standby/publishing.py','standby/publish_service.py','standby/snapshot.py','standby/backup.py','standby/gateway.py','standby/transport.py','operations/__init__.py','operations/core.py','operations/protocol.py','operations/standby_backup.py')


def run(*args):
    subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60)


def write_json(path,data):
    temp=path.with_suffix('.pending')
    temp.write_text(json.dumps(data,indent=2)+'\n');temp.chmod(0o600);temp.replace(path)


def switch(path,target):
    temp=path.with_name('.publication-switch')
    if os.path.lexists(temp):raise ValueError('Unreconciled switch')
    temp.symlink_to(target,target_is_directory=True);temp.replace(path)


def rollback(journal):
    if journal.parent!=Path('/var/backups') or not journal.name.startswith('fallbackhosting-publication-demo-'):raise ValueError('Unexpected journal')
    data=json.loads((journal/'journal.json').read_text())
    for unit in UNITS:
        path=Path('/etc/systemd/system')/unit
        if path.exists():
            if hashlib.sha256(path.read_bytes()).hexdigest()!=data['unit_hashes'][unit]:raise ValueError('Unit drift')
            run('systemctl','disable','--now',unit)
    if ADMIN.resolve()==Path(data['new_admin']):
        switch(ADMIN,Path(data['previous_admin']));run('php-fpm8.3','-t');run('systemctl','reload','php8.3-fpm')
    elif ADMIN.resolve()!=Path(data['previous_admin']):raise ValueError('PHP release drift')
    # Publication jobs must be reconciled, never blindly overwrite a newer static pointer.
    current=(PUBLIC/'current').resolve()
    if current!=Path(data['previous_static']):
        state=BASE/'runtime/publication.json'
        item=json.loads(state.read_text()) if state.exists() else {}
        candidate=item.get('candidate')
        if not isinstance(candidate,str) or current!=PUBLIC/'releases'/candidate:raise ValueError('Static pointer drift')
        switch(PUBLIC/'current',Path(data['previous_static']))
    for path,info in data['ownership'].items():os.chown(path,info[0],info[1]);os.chmod(path,info[2])
    data['phase']='ROLLED_BACK_PRESERVED_DATA';write_json(journal/'journal.json',data)
    print('PASS scoped publication rollback; artifacts and private journal retained')


def apply():
    if os.geteuid()!=0:raise ValueError('Root activation required')
    revision=subprocess.check_output(['git','-c','safe.directory=/opt/fallback','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    release=Path('/var/www/fallback-admin/releases')/revision
    targets=[BASE,release,*[Path('/etc/systemd/system')/u for u in UNITS],Path('/var/lib/fallback-web/admin/publication.sock')]
    if any(os.path.lexists(p) for p in targets):raise ValueError('Existing target; reconcile instead of replay')
    run('python3',str(ROOT/'scripts/activate-admin.py'),'verify')
    before={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ('/var/lib/fallback-web/admin/auth.json','/var/lib/fallback-web/admin/inventory.json')}
    previous=ADMIN.resolve(strict=True)
    spec=importlib.util.spec_from_file_location('checker',ROOT/'scripts/verify-center-release.py');checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
    def blob(name):return subprocess.check_output(['git','-c','safe.directory=/opt/fallback','show',revision+':'+name],cwd=ROOT)
    journal=Path('/var/backups')/('fallbackhosting-publication-demo-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));journal.mkdir(mode=0o700)
    data={'phase':'PREPARED','revision':revision,'previous_admin':str(previous),'new_admin':str(release),'previous_static':str((PUBLIC/'current').resolve(strict=True)),
          'ownership':{str(p):[p.stat().st_uid,p.stat().st_gid,p.stat().st_mode&0o777] for p in (PUBLIC,PUBLIC/'releases')},
          'unit_hashes':{u:hashlib.sha256(blob('deploy/'+u)).hexdigest() for u in UNITS}}
    write_json(journal/'journal.json',data)
    try:
        BASE.mkdir(mode=0o755);code=BASE/'code';code.mkdir(mode=0o755)
        for source in CODE:
            path=code/source;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(blob(source));path.chmod(0o644)
        technical=pwd.getpwnam('fallback-agent');web=pwd.getpwnam('fallback-web')
        runtime=BASE/'runtime';runtime.mkdir(mode=0o700);os.chown(runtime,technical.pw_uid,technical.pw_gid)
        inventory=json.loads(Path('/var/lib/fallback-web/admin/inventory.json').read_text())
        node=next(n for n in inventory['servers'] if n['id']=='ctx1' and n['enabled'])
        if node['observations']['fingerprint']['status']!='PASS':raise ValueError('Verified backup identity required')
        config=json.loads((ROOT/'.local/standby-review/publication-config.json').read_text())
        if config['origin']!=json.loads(Path('/var/lib/fallback-standby-demo/policy.json').read_text())['origin']:raise ValueError('Source origin drift')
        config.pop('store');config.update(store=str(runtime),public=str(PUBLIC))
        policy={'service_uid':technical.pw_uid,'web_uid':web.pw_uid,'actor':json.loads(Path('/var/lib/fallback-web/admin/auth.json').read_text())['username'],'config':config,'node':node,'backup_script':str(code/'operations/standby_backup.py')}
        write_json(BASE/'policy.json',policy);os.chown(BASE/'policy.json',0,technical.pw_gid);(BASE/'policy.json').chmod(0o640)
        for path in (PUBLIC,PUBLIC/'releases'):os.chown(path,technical.pw_uid,technical.pw_gid)
        release.mkdir(mode=0o755)
        for name,source in checker.SOURCES.items():
            path=release/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(blob(source));path.chmod(0o644)
        shutil.copytree(previous/'center-artifact',release/'center-artifact')
        artifact_hash=hashlib.sha256((release/'center-artifact/manifest.json').read_bytes()).hexdigest()
        checker.verify(release,revision,artifact_hash,require_root=True)
        for unit in UNITS:
            path=Path('/etc/systemd/system')/unit;path.write_bytes(blob('deploy/'+unit));path.chmod(0o644)
        run('systemd-analyze','verify',*[str(Path('/etc/systemd/system')/u) for u in UNITS])
        run('systemctl','daemon-reload')
        for unit in UNITS:run('systemctl','enable','--now',unit)
        run('systemctl','is-active','--quiet',UNITS[1])
        if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=v for p,v in before.items()):raise ValueError('Private state drift')
        switch(ADMIN,release);run('php-fpm8.3','-t');run('systemctl','reload','php8.3-fpm')
        data['phase']='ACTIVATED_NEEDS_HTTPS_ACCEPTANCE';write_json(journal/'journal.json',data)
        run('python3',str(ROOT/'scripts/activate-admin.py'),'verify')
        print(json.dumps({'activation':'NEEDS_HTTPS_ACCEPTANCE','revision':revision,'journal':str(journal)}))
    except Exception:
        data['phase']='FAILED';write_json(journal/'journal.json',data);rollback(journal);raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');p.add_argument('--rollback',type=Path);args=p.parse_args()
    if os.geteuid()!=0:p.error('Root execution required')
    if args.rollback:rollback(args.rollback)
    elif args.apply:apply()
    else:p.error('Choose explicit --apply or --rollback journal')
