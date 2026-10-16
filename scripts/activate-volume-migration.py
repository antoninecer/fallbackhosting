#!/usr/bin/env python3
"""Journaled update of the existing private onboarding service and PHP release."""
import argparse,hashlib,importlib.util,json,os,pwd,shutil,subprocess
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=Path('/var/lib/fallback-node-onboarding');CURRENT=Path('/var/www/fallback-admin/current');UNIT='fallback-node-onboarding.service'
def run(*args):subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60)
def write(path,value):
 temp=path.with_suffix('.pending');temp.write_text(json.dumps(value,indent=2)+'\n');temp.chmod(0o600);temp.replace(path)
def switch(path):
 temp=CURRENT.with_name('.volume-migration-switch');assert not os.path.lexists(temp);temp.symlink_to(path,target_is_directory=True);temp.replace(CURRENT)
def rollback(backup):
 if backup.parent!=Path('/var/backups') or not backup.name.startswith('fallbackhosting-volume-migration-'):raise ValueError('Invalid journal')
 j=json.loads((backup/'journal.json').read_text());run('systemctl','stop',UNIT)
 if Path(j['previous_code']).exists():
  failed=BASE/('code-failed-'+j['revision'][:12]);assert not failed.exists();(BASE/'code').rename(failed);Path(j['previous_code']).rename(BASE/'code')
 shutil.copy2(backup/'policy.json',BASE/'policy.json');os.chown(BASE/'policy.json',0,pwd.getpwnam('fallback-agent').pw_gid)
 switch(Path(j['previous_php']));run('php-fpm8.3','-t');run('systemctl','reload','php8.3-fpm');run('systemctl','start',UNIT);run('python3',str(ROOT/'scripts/activate-admin.py'),'verify');j['phase']='ROLLED_BACK_RUNTIME_PRESERVED';write(backup/'journal.json',j)
 print('PASS exact code/policy/PHP rollback; private runtime retained')
def apply(artifact):
 revision=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip();release=CURRENT.parent/'releases'/revision
 if release.exists():raise ValueError('Existing release requires reconciliation')
 for p in (BASE/'runtime').glob('*.json'):
  if json.loads(p.read_text()).get('phase') in ('CHECKING','INITIALIZING'):raise ValueError('Active onboarding')
 migration=BASE/'runtime/migration/job.json'
 if migration.exists() and json.loads(migration.read_text())['phase'] in ('CHECKING','CREATING','MOVING','WRITING','RESTARTING'):raise ValueError('Active migration')
 run('python3',str(ROOT/'scripts/activate-admin.py'),'verify')
 artifact=artifact.resolve(strict=True);manifest=hashlib.sha256((artifact/'manifest.json').read_bytes()).hexdigest()
 backup=Path('/var/backups')/('fallbackhosting-volume-migration-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));backup.mkdir(mode=0o700)
 j={'phase':'PREPARED','revision':revision,'previous_php':str(CURRENT.resolve()),'new_php':str(release),'previous_code':str(BASE/('code-prior-'+revision[:12])),'before':{n:hashlib.sha256((Path('/var/lib/fallback-web/admin')/n).read_bytes()).hexdigest() for n in ('auth.json','inventory.json')}}
 write(backup/'journal.json',j);shutil.copy2(BASE/'policy.json',backup/'policy.json')
 def blob(name):return subprocess.check_output(['git','-C',str(ROOT),'show',revision+':'+name])
 spec=importlib.util.spec_from_file_location('onboarding_activation',ROOT/'scripts/activate-node-onboarding.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 stage=BASE/('code-staged-'+revision[:12]);stage.mkdir(mode=0o755)
 for source in (*module.CODE,'operations/volume_remote.py','operations/volume_migration.py'):
  p=stage/source;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(blob(source));p.chmod(0o644)
 spec=importlib.util.spec_from_file_location('checker',ROOT/'scripts/verify-center-release.py');checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
 release.mkdir(mode=0o755)
 for name,source in checker.SOURCES.items():
  p=release/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(blob(source));p.chmod(0o644)
 shutil.copytree(artifact,release/'center-artifact')
 for p in [release,*release.rglob('*')]:
  if p.is_symlink():raise ValueError('Unexpected symlink')
  os.chown(p,0,0);p.chmod(0o755 if p.is_dir() else 0o644)
 checker.verify(release,revision,manifest,require_root=True)
 policy=json.loads((BASE/'policy.json').read_text());inventory=json.loads(Path('/var/lib/fallback-web/admin/inventory.json').read_text())
 policy['migration_nodes']={}
 for node in inventory['servers']:
  if node['id'] in ('ctx1','vasatkova'):
   if not node['enabled'] or node['observations']['fingerprint']['status']!='PASS':raise ValueError('Unverified target')
   policy['migration_nodes'][node['id']]={**{k:node[k] for k in ('id','host','ssh_port','ssh_user')},'fingerprint':node['host_fingerprint']}
 if set(policy['migration_nodes'])!={'ctx1','vasatkova'}:raise ValueError('Missing fixed exercise targets')
 policy['migration_source']=str(BASE/'code/operations/volume_remote.py')
 try:
  run('systemctl','stop',UNIT);(BASE/'code').rename(j['previous_code']);stage.rename(BASE/'code');write(BASE/'policy.json',policy);os.chown(BASE/'policy.json',0,pwd.getpwnam('fallback-agent').pw_gid);(BASE/'policy.json').chmod(0o640)
  run('systemctl','start',UNIT);run('systemctl','is-active','--quiet',UNIT);run('php-fpm8.3','-t');switch(release);run('systemctl','reload','php8.3-fpm');run('python3',str(ROOT/'scripts/activate-admin.py'),'verify')
  for n,h in j['before'].items():
   if hashlib.sha256((Path('/var/lib/fallback-web/admin')/n).read_bytes()).hexdigest()!=h:raise ValueError('Private state drift')
  j['phase']='ACTIVATED_NEEDS_LIVE_ACCEPTANCE';write(backup/'journal.json',j);print(json.dumps({'activation':j['phase'],'revision':revision,'journal':str(backup)}))
 except Exception:
  rollback(backup);raise
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--artifact',type=Path);p.add_argument('--apply',action='store_true');p.add_argument('--rollback',type=Path);a=p.parse_args()
 if os.geteuid()!=0:p.error('Root required')
 if a.rollback:rollback(a.rollback)
 elif a.apply and a.artifact:apply(a.artifact)
 else:p.error('Select apply/artifact or rollback journal')
