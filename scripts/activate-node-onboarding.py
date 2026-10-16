#!/usr/bin/env python3
"""Freeze/install only server-onboarding units and an immutable admin release."""
import argparse
from datetime import datetime,timezone
import hashlib,importlib.util,json,os,pwd,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=Path('/var/lib/fallback-node-onboarding');CURRENT=Path('/var/www/fallback-admin/current')
UNITS=('fallback-node-onboarding.socket','fallback-node-onboarding.service')
CODE=('operations/__init__.py','operations/core.py','operations/protocol.py','operations/node_onboarding.py','operations/bootstrap_node.py','standby/__init__.py','standby/gateway.py','standby/snapshot.py')

def run(*args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=45)
def write(path,data):
 temp=path.with_suffix('.pending');temp.write_text(json.dumps(data,indent=2)+'\n');temp.chmod(0o600);temp.replace(path)
def switch(target):
 temp=CURRENT.with_name('.onboarding-switch');assert not os.path.lexists(temp);temp.symlink_to(target,target_is_directory=True);temp.replace(CURRENT)
def rollback(backup):
 if backup.parent!=Path('/var/backups') or not backup.name.startswith('fallbackhosting-node-onboarding-'):raise ValueError('Unexpected rollback journal')
 data=json.loads((backup/'journal.json').read_text())
 for unit in UNITS:
  path=Path('/etc/systemd/system')/unit
  if path.exists():
   if hashlib.sha256(path.read_bytes()).hexdigest()!=data['units'][unit]:raise ValueError('Unit drift')
   run('systemctl','disable','--now',unit)
 if CURRENT.resolve()==Path(data['new']):switch(Path(data['previous']));run('php-fpm8.3','-t');run('systemctl','reload','php8.3-fpm')
 elif CURRENT.resolve()!=Path(data['previous']):raise ValueError('Release drift')
 data['phase']='ROLLED_BACK_PRESERVED_JOBS';write(backup/'journal.json',data)
 print('PASS scoped rollback; all private jobs and remote journals preserved')
def apply(artifact):
 if os.geteuid()!=0:raise ValueError('Root activation required')
 revision=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip();release=CURRENT.parent/'releases'/revision
 if any(os.path.lexists(p) for p in (BASE,release,Path('/var/lib/fallback-web/admin/onboarding.sock'),*[Path('/etc/systemd/system')/n for n in UNITS])):raise ValueError('Existing targets require reconciliation')
 previous=CURRENT.resolve(strict=True);artifact=artifact.resolve(strict=True);manifest=hashlib.sha256((artifact/'manifest.json').read_bytes()).hexdigest()
 def blob(name):return subprocess.check_output(['git','-C',str(ROOT),'show',revision+':'+name])
 run('python3',str(ROOT/'scripts/activate-admin.py'),'verify')
 before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('/var/lib/fallback-web/admin')/n for n in ('auth.json','inventory.json')]+[Path('/etc/php/8.3/fpm/pool.d/fallback-admin.conf')]}
 backup=Path('/var/backups')/('fallbackhosting-node-onboarding-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));backup.mkdir(mode=0o700)
 data={'phase':'PREPARED','previous':str(previous),'new':str(release),'revision':revision,'artifact_sha256':manifest,'before':before,'units':{n:hashlib.sha256(blob('deploy/'+n)).hexdigest() for n in UNITS}}
 write(backup/'journal.json',data)
 try:
  BASE.mkdir(mode=0o755);code=BASE/'code';code.mkdir(mode=0o755)
  for source in CODE:
   path=code/source;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(blob(source));path.chmod(0o644)
  technical=pwd.getpwnam('fallback-agent');web=pwd.getpwnam('fallback-web')
  runtime=BASE/'runtime';runtime.mkdir(mode=0o700);os.chown(runtime,technical.pw_uid,technical.pw_gid)
  policy={'runtime':str(runtime),'web_uid':web.pw_uid,'actor':json.loads(Path('/var/lib/fallback-web/admin/auth.json').read_text())['username'],'source':str(code/'operations/bootstrap_node.py')}
  write(BASE/'policy.json',policy);os.chown(BASE/'policy.json',0,technical.pw_gid);(BASE/'policy.json').chmod(0o640)
  spec=importlib.util.spec_from_file_location('checker',ROOT/'scripts/verify-center-release.py');checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
  release.mkdir(mode=0o755)
  for name,source in checker.SOURCES.items():
   p=release/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(blob(source));p.chmod(0o644)
  shutil.copytree(artifact,release/'center-artifact')
  for p in [release,*release.rglob('*')]:
   if p.is_symlink():raise ValueError('Symlink artifact')
   os.chown(p,0,0);p.chmod(0o755 if p.is_dir() else 0o644)
  checker.verify(release,revision,manifest,require_root=True)
  for unit in UNITS:
   p=Path('/etc/systemd/system')/unit;p.write_bytes(blob('deploy/'+unit));p.chmod(0o644)
  run('systemd-analyze','verify',*[str(Path('/etc/systemd/system')/n) for n in UNITS]);run('systemctl','daemon-reload')
  for unit in UNITS:run('systemctl','enable','--now',unit)
  run('systemctl','is-active','--quiet',UNITS[1])
  if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=v for p,v in before.items()):raise ValueError('Private state drift')
  run('php-fpm8.3','-t');switch(release);run('systemctl','reload','php8.3-fpm');run('python3',str(ROOT/'scripts/activate-admin.py'),'verify')
  data['phase']='ACTIVATED_NEEDS_BROWSER_ACCEPTANCE';write(backup/'journal.json',data)
  print(json.dumps({'activation':'NEEDS_BROWSER_ACCEPTANCE','revision':revision,'journal':str(backup)}))
 except Exception:
  data['phase']='FAILED';write(backup/'journal.json',data);rollback(backup);raise
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--artifact',type=Path);p.add_argument('--apply',action='store_true');p.add_argument('--rollback',type=Path);args=p.parse_args()
 if os.geteuid()!=0:p.error('Root activation required')
 if args.rollback:rollback(args.rollback)
 elif args.apply and args.artifact:apply(args.artifact)
 else:p.error('Choose --apply --artifact or --rollback journal')
