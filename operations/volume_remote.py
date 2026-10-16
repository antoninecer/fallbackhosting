"""Fixed operations on uniquely labelled, artificial Redis/file fixtures only."""
import base64,hashlib,io,json,os,re,shutil,subprocess,tarfile
from pathlib import Path

LABEL='io.fallbackhosting.volume-exercise'
def command(args,raw=False,input=None,timeout=90):
 r=subprocess.run(args,input=input,capture_output=True,timeout=timeout)
 if r.returncode:raise RuntimeError('FIXTURE_COMMAND_FAILED')
 return r.stdout if raw else r.stdout.decode().strip()

def main(request):
 op=request['op'];name=request.get('name','')
 if op not in ('probe','create','verify','write','export','restore','start','restart','cleanup'):raise ValueError('INVALID_ACTION')
 if op!='probe' and not re.fullmatch('fh-move-[0-9a-f]{16}',name):raise ValueError('INVALID_FIXTURE')
 sudo=subprocess.run(['sudo','-n','true'],capture_output=True).returncode==0
 docker=['sudo','-n','docker'] if sudo else ['docker']
 def d(*args,**kw):return command(docker+list(args),**kw)
 def owned(resource,volume=False):
  data=json.loads(d(*(['volume','inspect'] if volume else ['inspect']),resource))[0]
  labels=data.get('Labels') if volume else data['Config'].get('Labels')
  if not labels or labels.get(LABEL)!=name:raise ValueError('RESOURCE_OWNERSHIP_MISMATCH')
  return data
 def pair():
  for suffix in ('db','web'):owned(name+'-'+suffix)
  for suffix in ('data','files'):owned(name+'-'+suffix,True)
 def verify():
  pair();marker=d('exec',name+'-db','redis-cli','--raw','GET','fixture');counter=d('exec',name+'-db','redis-cli','--raw','GET','counter')
  if not re.fullmatch('[0-9a-f]{16}',marker) or not counter.isdigit():raise ValueError('INVALID_DATA')
  web=d('exec',name+'-web','wget','-qO-','http://127.0.0.1:8080/')
  if web!=marker+':'+counter:raise ValueError('DATA_MISMATCH')
  return {'marker':marker,'counter':int(counter),'file_sha256':hashlib.sha256(web.encode()).hexdigest()}
 if op=='probe':
  info=json.loads(d('info','--format','{{json .}}'))
  # Root directory can be private to Docker; df uses the actual filesystem path via existing sudo.
  mounts=[line.split()[4].replace('\\040',' ') for line in Path('/proc/self/mountinfo').read_text().splitlines()]
  mount=max((m for m in mounts if info['DockerRootDir']==m or info['DockerRootDir'].startswith(m.rstrip('/')+'/')),key=len)
  disk=command(['df','-Pk',mount]).splitlines()[-1].split()
  mem={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemTotal:','MemAvailable:'))}
  others={}
  ids=d('ps','-aq').splitlines()
  if ids:
   for c in json.loads(d('inspect',*ids)):
    if not (c['Config'].get('Labels') or {}).get(LABEL):others[c['Id']]={k:c['State'][k] for k in ('Status','StartedAt','Restarting')}
  cpu=sum(float(x.rstrip('%')) for x in d('stats','--no-stream','--format','{{.CPUPerc}}').splitlines())
  return {'docker_version':info['ServerVersion'],'architecture':info['Architecture'],'cpus':info['NCPU'],'memory_bytes':mem['MemTotal'],'memory_available_bytes':mem['MemAvailable'],'disk_available_bytes':int(disk[3])*1024,'containers':len(ids),'others':others,'historical_peak':'UNKNOWN','current_container_cpu_percent':round(cpu,2),'storage_scope':'DockerRootDir filesystem; fixture uses named volumes only'}
 if op=='create' or op=='restore':
  for resource in (name+'-db',name+'-web'):
   if subprocess.run(docker+['inspect',resource],capture_output=True).returncode==0:raise ValueError('EXISTING_CONTAINER')
  for resource in (name+'-data',name+'-files'):
   if subprocess.run(docker+['volume','inspect',resource],capture_output=True).returncode==0:raise ValueError('EXISTING_VOLUME')
  images=request.get('images',{'db':'redis:7.4-alpine','web':'busybox:1.37.0'})
  for kind,ref in images.items():
   repository={'db':'redis','web':'busybox'}[kind]
   if ref not in ('redis:7.4-alpine','busybox:1.37.0') and not re.fullmatch(repository+'@sha256:[0-9a-f]{64}',ref):raise ValueError('INVALID_IMAGE')
   d('pull',ref,timeout=150)
  pinned={kind:json.loads(d('image','inspect',ref))[0]['RepoDigests'][0] for kind,ref in images.items()}
  for suffix in ('data','files'):d('volume','create','--label',LABEL+'='+name,name+'-'+suffix)
  common=['--label',LABEL+'='+name,'--network','none','--restart','no','--pids-limit','64','--memory','96m','--cpus','0.25','--log-driver','local','--log-opt','max-size=1m','--log-opt','max-file=2']
  d('create','--name',name+'-db',*common,'--mount','type=volume,src='+name+'-data,dst=/data',pinned['db'],'redis-server','--appendonly','no','--save','')
  d('create','--name',name+'-web',*common,'--mount','type=volume,src='+name+'-files,dst=/data',pinned['web'],'httpd','-f','-p','8080','-h','/data')
  if op=='restore':
   for suffix in ('db','web'):
    blob=base64.b64decode(request['archives'][suffix]['data'],validate=True)
    if len(blob)>1048576 or hashlib.sha256(blob).hexdigest()!=request['archives'][suffix]['sha256']:raise ValueError('ARCHIVE_CHECKSUM')
    with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
     for member in tar.getmembers():
      normalized=member.name.removeprefix('./').rstrip('/')
      if normalized not in ('','.','dump.rdb' if suffix=='db' else 'index.html') or not (member.isdir() or member.isfile()) or member.size>524288:raise ValueError('UNEXPECTED_ARCHIVE_MEMBER')
    d('cp','-',name+'-'+suffix+':/data',input=blob)
  d('start',name+'-db',name+'-web')
  import time
  for attempt in range(30):
   if subprocess.run(docker+['exec',name+'-db','redis-cli','ping'],capture_output=True).stdout.strip()==b'PONG':break
   time.sleep(.2)
  if op=='create':
   marker=request['marker']
   if not re.fullmatch('[0-9a-f]{16}',marker):raise ValueError('INVALID_MARKER')
   d('exec',name+'-db','redis-cli','SET','fixture',marker);d('exec',name+'-db','redis-cli','SET','counter','7')
   d('exec',name+'-web','sh','-c','printf "%s" "$1" > /data/index.html','fixture',marker+':7');d('exec',name+'-db','redis-cli','SAVE')
  return {'images':pinned,'verification':verify()}
 if op in ('verify','write','export','start','restart','cleanup'):pair()
 if op=='write':
  marker=d('exec',name+'-db','redis-cli','--raw','GET','fixture');counter=d('exec',name+'-db','redis-cli','--raw','INCR','counter')
  d('exec',name+'-web','sh','-c','printf "%s" "$1" > /data/index.html','fixture',marker+':'+counter);d('exec',name+'-db','redis-cli','SAVE')
 if op=='export':
  before=verify();d('exec',name+'-db','redis-cli','SAVE');d('stop','-t','10',name+'-web',name+'-db')
  archives={}
  for suffix in ('db','web'):
   data=d('cp',name+'-'+suffix+':/data/.','-',raw=True)
   if len(data)>1048576:raise ValueError('FIXTURE_TOO_LARGE')
   archives[suffix]={'data':base64.b64encode(data).decode(),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
  return {'archives':archives,'verification':before}
 if op in ('start','restart'):
  d(op,name+'-db',name+'-web')
  import time
  for attempt in range(30):
   if subprocess.run(docker+['exec',name+'-db','redis-cli','ping'],capture_output=True).stdout.strip()==b'PONG':break
   time.sleep(.2)
 if op=='cleanup':
  d('rm','-f',name+'-db',name+'-web')
  for suffix in ('data','files'):d('volume','rm',name+'-'+suffix)
  return {'cleaned':True}
 return {'verification':verify()}

if __name__=='__main__':
 request=PAYLOAD_PLACEHOLDER
 try:
  facts=main(request['action']);facts['user']=command(['id','-un']);print(json.dumps({'ok':True,'facts':facts}))
 except Exception:print(json.dumps({'ok':False,'error':'FIXTURE_REQUIRES_REVIEW'}))
