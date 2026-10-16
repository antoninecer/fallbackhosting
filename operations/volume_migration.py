"""Durable web-driven migration of owned artificial fixtures. No general app import."""
import json,secrets,threading
from pathlib import Path
from operations.core import Denied,exact
from standby.gateway import atomic_json
from datetime import datetime,timezone

def utc():return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
ACTIVE={'CHECKING','CREATING','MOVING','WRITING','RESTARTING'}

class VolumeMigration:
 def __init__(self,root,nodes,driver):
  self.root=Path(root);self.root.mkdir(mode=0o700,parents=True,exist_ok=True);self.path=self.root/'job.json';self.nodes=nodes;self.driver=driver;self.lock=threading.RLock()
  if self.path.exists() and self.load()['phase'] in ACTIVE:
   state=self.load();self.save(state,phase='NEEDS_REVIEW',error='INTERRUPTED_OPERATION')
 def load(self):return json.loads(self.path.read_text()) if self.path.exists() else {'phase':'IDLE','revision':0,'utc':utc(),'placements':[]}
 def save(self,state,**extra):
  state={**state,**extra,'revision':state['revision']+1,'utc':utc()};atomic_json(self.path,state);return state
 def view(self,state):
  return {k:v for k,v in state.items() if k in ('phase','revision','utc','source','target','current','verification','error','step','capacity','marker','transfers','readiness')}
 def submit(self,r):
  with self.lock:
   s=self.load();kind=r['kind']
   if kind=='migration_view':
    exact(r,'kind actor');return {'ok':True,'job':self.view(s),'nodes':list(self.nodes)}
   exact(r,'kind actor revision confirmation target')
   if type(r['revision']) is not int or r['revision']!=s['revision'] or r['confirmation'] is not True:raise Denied('CONFIRMATION_OR_REVISION_REQUIRED')
   if s['phase'] in ACTIVE or s['phase']=='NEEDS_REVIEW':raise Denied('BUSY_OR_REVIEW_REQUIRED')
   if r['target'] not in self.nodes:raise Denied('UNKNOWN_DESTINATION')
   if kind=='migration_check':
    s=self.save(s,phase='CHECKING',target=r['target'],error=None)
   elif kind=='migration_create':
    if s['phase']!='READY' or s.get('current') or s['target']!=r['target'] or not s['readiness']:raise Denied('CHECK_REQUIRED')
    self.fresh(s)
    s=self.save(s,phase='CREATING',marker=secrets.token_hex(8),pending_name='fh-move-'+secrets.token_hex(8))
   elif kind=='migration_move':
    if s['phase']!='READY' or not s.get('current') or s['current']['node']==r['target'] or s['target']!=r['target'] or not s['readiness']:raise Denied('CHECK_REQUIRED')
    self.fresh(s)
    if len(s.get('placements',[]))>=20:raise Denied('RETAINED_COPY_LIMIT_REACHED')
    s=self.save(s,phase='MOVING',source=s['current']['node'],pending_name='fh-move-'+secrets.token_hex(8),step='EXPORT_INTENT')
   elif kind in ('migration_write','migration_restart'):
    if not s.get('current') or s['phase'] not in ('RUNNING','READY') or r['target']!=s['current']['node']:raise Denied('NO_CURRENT_FIXTURE')
    s=self.save(s,phase='WRITING' if kind=='migration_write' else 'RESTARTING')
   else:raise Denied('UNKNOWN_OPERATION')
   return {'ok':True,'job':self.view(s)}
 def fresh(self,s):
  if (datetime.now(timezone.utc)-datetime.strptime(s['utc'],'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)).total_seconds()>300:raise Denied('CAPACITY_CHECK_EXPIRED')
 def sufficient(self,facts):
  return facts['disk_available_bytes']>=512*1024*1024 and facts['memory_available_bytes']>=256*1024*1024 and facts['cpus']>=1
 def advance(self):
  with self.lock:s=self.load()
  phase=s['phase']
  if phase not in ACTIVE:return
  def call(node,op,**kw):return self.driver(self.nodes[node],{'op':op,**kw})
  try:
   if phase=='CHECKING':
    facts=call(s['target'],'probe');baseline=facts.pop('others');s['target_baseline']=baseline
    size=sum(a['bytes'] for a in s.get('archives',{}).values());required=max(512*1024*1024,size*4)
    ready=facts['disk_available_bytes']>=required and facts['memory_available_bytes']>=256*1024*1024 and facts['cpus']>=1
    s=self.save(s,phase='READY',capacity={**facts,'required_disk_bytes':required,'required_memory_bytes':256*1024*1024},readiness=ready)
   elif phase=='CREATING':
    if not self.sufficient(call(s['target'],'probe')):raise ValueError('CAPACITY_CHANGED')
    result=call(s['target'],'create',name=s['pending_name'],marker=s['marker']);s['images']=result['images']
    if result['verification']['marker']!=s['marker'] or result['verification']['counter']!=7:raise ValueError('INITIAL_DATA_MISMATCH')
    placement={'node':s['target'],'name':s['pending_name']};s['placements'].append(placement)
    if call(s['target'],'probe')['others']!=s['target_baseline']:raise ValueError('UNRELATED_STATE_CHANGED')
    s=self.save(s,phase='RUNNING',current=placement,verification=result['verification'],transfers=[])
   elif phase=='MOVING':
    source=s['current']
    if s['step']=='EXPORT_INTENT':
     if not self.sufficient(call(s['target'],'probe')):raise ValueError('CAPACITY_CHANGED')
     baseline=call(source['node'],'probe')['others']
     result=call(source['node'],'export',name=source['name'])
     if call(source['node'],'probe')['others']!=baseline:raise ValueError('UNRELATED_SOURCE_CHANGED')
     s=self.save(s,archives=result['archives'],expected=result['verification'],step='RESTORE_INTENT')
    elif s['step']=='RESTORE_INTENT':
     result=call(s['target'],'restore',name=s['pending_name'],images=s['images'],archives=s['archives'])
     if result['verification']!=s['expected']:raise ValueError('RESTORE_DATA_MISMATCH')
     if call(s['target'],'probe')['others']!=s['target_baseline']:raise ValueError('UNRELATED_STATE_CHANGED')
     placement={'node':s['target'],'name':s['pending_name']};s['placements'].append(placement)
     s['transfers'].append({'source':source['node'],'target':s['target'],'utc':utc(),'verification':result['verification'],'sha256':{k:a['sha256'] for k,a in s['archives'].items()}})
     s=self.save(s,phase='RUNNING',current=placement,verification=result['verification'],step='VERIFIED')
   else:
    result=call(s['current']['node'],'write' if phase=='WRITING' else 'restart',name=s['current']['name'])
    expected={**s['verification']}
    if result['verification']['marker']!=s['marker'] or result['verification']['counter']!=expected['counter']+(1 if phase=='WRITING' else 0):raise ValueError('PERSISTENCE_MISMATCH')
    s=self.save(s,phase='RUNNING',verification=result['verification'])
  except Exception:
   # Preserve original volumes and archive; no blind retry or stale writer restart.
   s=self.save(s,phase='NEEDS_REVIEW',error='OPERATION_REQUIRES_RECONCILIATION')
