import copy,json,os,socket,tempfile,threading,unittest
from pathlib import Path
import test_admin
from test_node_onboarding import KEY
from operations.core import Denied
from operations.node_onboarding import Onboarding
from operations.protocol import serve_connection
from operations.volume_migration import VolumeMigration

class Driver:
 def __init__(self):self.calls=[];self.data={};self.low=False;self.fail=False
 def __call__(self,spec,r):
  self.calls.append((spec,r['op']));op=r['op'];name=r.get('name')
  if op=='probe':return dict(docker_version='fixture',architecture='x86_64',cpus=2,memory_available_bytes=10**9,disk_available_bytes=0 if self.low else 10**10,containers=2,others={'unrelated':'unchanged'},current_container_cpu_percent=1,historical_peak='UNKNOWN')
  if self.fail:raise RuntimeError('private detail')
  if op=='create':
   self.data[name]={'marker':r['marker'],'counter':7,'file_sha256':'fixture'}
   return {'images':{'db':'redis@sha256:'+'a'*64,'web':'busybox@sha256:'+'b'*64},'verification':dict(self.data[name])}
  if op=='export':return {'verification':dict(self.data[name]),'archives':{'db':{'bytes':10,'sha256':'d','data':json.dumps(self.data[name])},'web':{'bytes':10,'sha256':'w','data':'fixture'}}}
  if op=='restore':self.data[name]=json.loads(r['archives']['db']['data'])
  if op=='write':self.data[name]['counter']+=1
  return {'verification':dict(self.data[name])}

class VolumeMigrationTests(unittest.TestCase):
 def setup_api(self,tmp):
  driver=Driver();api=VolumeMigration(Path(tmp)/'migration',{'ctx1':'ctx1','vasatkova':'vasatkova'},driver);return api,driver
 def submit(self,api,op,target='ctx1',**kw):return api.submit(dict(kind='migration_'+op,actor='admin',revision=api.load()['revision'],confirmation=True,target=target,**kw))
 def check(self,api,target):self.submit(api,'check',target);api.advance();self.assertEqual(api.load()['phase'],'READY')
 def create(self,api):self.check(api,'ctx1');self.submit(api,'create');api.advance();self.assertEqual(api.load()['phase'],'RUNNING')
 def test_two_directions_new_writes_persistence_originals_and_private_archives(self):
  with tempfile.TemporaryDirectory() as tmp:
   api,d=self.setup_api(tmp);self.create(api);original=api.load()['current']['name']
   for target in ('vasatkova','ctx1'):
    self.check(api,target);self.submit(api,'move',target);api.advance();self.assertEqual(api.load()['step'],'RESTORE_INTENT');api.advance();self.assertEqual(api.load()['current']['node'],target)
    self.assertIn(original,d.data)
    if target=='vasatkova':self.submit(api,'write',target);api.advance()
   self.submit(api,'restart','ctx1');api.advance();s=api.load();self.assertEqual(s['verification']['counter'],8);self.assertEqual(len(s['transfers']),2)
   view=api.submit({'kind':'migration_view','actor':'admin'})['job'];self.assertNotIn('archives',view);self.assertNotIn('target_baseline',view)
 def test_insufficient_capacity_confirmation_revision_target_and_order_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   api,d=self.setup_api(tmp)
   for bad in ({'confirmation':False},{'revision':99},{'target':'production'},{'command':'rm'}):
    r=dict(kind='migration_check',actor='admin',revision=0,confirmation=True,target='ctx1');r.update(bad)
    with self.assertRaises(Denied):api.submit(r)
   with self.assertRaises(Denied):self.submit(api,'create')
   d.low=True;self.check(api,'ctx1');self.assertFalse(api.load()['readiness'])
   with self.assertRaises(Denied):self.submit(api,'create')
   self.assertEqual([op for _,op in d.calls],['probe'])
 def test_interruption_and_failed_copy_preserve_source_and_prevent_replay(self):
  with tempfile.TemporaryDirectory() as tmp:
   api,d=self.setup_api(tmp);self.create(api);self.check(api,'vasatkova');self.submit(api,'move','vasatkova');api.advance();source=api.load()['current'];d.fail=True;api.advance()
   self.assertEqual(api.load()['phase'],'NEEDS_REVIEW');self.assertEqual(api.load()['current'],source);self.assertIn('archives',api.load());self.assertNotIn('private detail',json.dumps(api.load()))
   with self.assertRaises(Denied):self.submit(api,'move','vasatkova')
  with tempfile.TemporaryDirectory() as tmp:
   api,d=self.setup_api(tmp);self.submit(api,'check');restored=VolumeMigration(api.root,api.nodes,d);self.assertEqual(restored.load()['phase'],'NEEDS_REVIEW');restored.advance();self.assertEqual(d.calls,[])
 def test_php_real_peer_socket_csrf_origin_confirmation_and_roundtrip(self):
  app=test_admin.AdminTests();app.setUp();self.addCleanup(app.tearDown)
  broker=Onboarding(app.data/'runtime',os.getuid(),'admin',KEY,lambda *a:None);self.addCleanup(broker.process_lock.close)
  broker.migration,d=self.setup_api(app.data/'runtime')
  listener=socket.socket(socket.AF_UNIX);listener.bind(str(app.data/'onboarding.sock'));listener.listen(8);listener.settimeout(.1);stop=threading.Event()
  def serve():
   while not stop.is_set():
    try:c,_=listener.accept()
    except socket.timeout:continue
    serve_connection(c,broker)
  thread=threading.Thread(target=serve);thread.start()
  try:
   self.assertEqual(app.request('/?migration=1')[0],401);app.login();self.assertIn('Přesun aplikací',app.request('/?migration=1')[1])
   def post(op,target):
    r=dict(action='migration-action',op=op,target=target,csrf=app.csrf(),revision=str(broker.migration.load()['revision']),confirmation='1')
    self.assertEqual(app.request('/?migration=1',dict(r,csrf='bad'))[0],403)
    self.assertEqual(app.request('/?migration=1',r,origin='https://invalid.example')[0],403)
    self.assertEqual(app.request('/?migration=1',dict(r,confirmation='0'))[0],422)
    self.assertEqual(app.request('/?migration=1',r)[0],303);broker.migration.advance()
   post('check','ctx1');post('create','ctx1');post('check','vasatkova');post('move','vasatkova');broker.migration.advance();post('write','vasatkova');post('check','ctx1');post('move','ctx1');broker.migration.advance();post('restart','ctx1')
   self.assertEqual(broker.migration.load()['verification']['counter'],8);self.assertEqual(len(broker.migration.load()['transfers']),2)
  finally:stop.set();thread.join(3);listener.close()
