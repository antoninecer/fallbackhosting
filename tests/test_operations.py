"""Fixture-only security/lifecycle/durable recovery tests, no real Docker."""
import copy
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import sqlite3
import struct
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from operations.core import ACTIONS, WRITES, Broker, Denied, Signer, canonical, decode_json
from operations.fixtures import FakeDriver
from operations.protocol import serve_connection, read_exact, MAX_FRAME


class OperationsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'jobs.db'
        self.uid=os.getuid();self.auth_key=secrets.token_bytes(32);self.approval_key=secrets.token_bytes(32)
        self.auth=Signer(self.auth_key);self.approvals=Signer(self.approval_key);self.sequence=0
        self.policy={'peers':[self.uid],'principals':{'alice':{'peers':[self.uid],'projects':['project-one'],'actions':sorted(ACTIONS)}},'apps':{'app-one':{'node':'node-one','project':'project-one','template':'demo'},'app-two':{'node':'node-two','project':'project-two','template':'demo'}},'templates':{'demo':{'image':'registry.example/demo@sha256:'+'a'*64}}}
        self.driver=FakeDriver();self.unrelated='f'*64
        self.driver.containers[('node-one',self.unrelated)]={'id':self.unrelated,'state':'running','labels':{}}
        self.broker=Broker(self.path,self.policy,self.driver,self.auth_key,self.approval_key,clock=lambda:1000)
    def tearDown(self):
        self.broker.close();self.temp.cleanup()
    def request(self,action='inspect',params=None):
        self.sequence+=1
        r={'version':1,'request_id':f'request-{self.sequence}','node':'node-one','project':'project-one','app':'app-one','action':action,'params':params or {},'authorization':self.auth.issue({'principal':'alice','peer_uid':self.uid,'project':'project-one','node':'node-one','actions':sorted(ACTIONS),'expires':1100}),'approval':None}
        if action in WRITES:self.approve(r)
        return r
    def approve(self,r,nonce=None):
        body={k:r[k] for k in ('version','request_id','node','project','app','action','params')}
        digest=hashlib.sha256(canonical(dict(body,principal='alice')).encode()).hexdigest()
        r['approval']=self.approvals.issue({'nonce':nonce or r['request_id'],'principal':'alice','digest':digest,'expires':1100})
    def submit(self,r):return self.broker.submit(r,self.uid)
    def deploy(self):
        result=self.submit(self.request('deploy'));self.assertEqual(result['state'],'SUCCEEDED');return result['result']['container_id']

    def test_job_progress_and_admin_view_are_scoped_historical_projections(self):
        self.assertEqual(self.submit(self.request('list'))['result'],{'containers':[]})
        cid=self.deploy()
        r=self.request('inspect')
        request={k:r[k] for k in ('request_id','node','project','app','authorization')}
        request['kind']='view'
        view=self.broker.read(request,self.uid)
        self.assertEqual(view['last_observation']['container_id'],cid)
        self.assertEqual(view['current_health'],'UNKNOWN')
        self.assertEqual(view['health_provenance'],'HISTORICAL')
        self.assertTrue(view['jobs']);self.assertTrue(view['audit'])
        self.assertNotIn('authorization',canonical(view));self.assertNotIn('logs',canonical(view))
        request['project']='project-two'
        with self.assertRaises(Denied):self.broker.read(request,self.uid)

    def test_all_operations_only_touch_registered_labelled_app(self):
        cid=self.deploy()
        for action,state in [('inspect','created'),('start','running'),('restart','running'),('stop','exited')]:
            result=self.submit(self.request(action));self.assertEqual(result['state'],'SUCCEEDED');self.assertEqual(result['result']['state'],state)
        result=self.submit(self.request('list'));self.assertEqual([c['container_id'] for c in result['result']['containers']],[cid])
        self.assertEqual(self.submit(self.request('logs',{'tail':10,'max_bytes':100}))['state'],'SUCCEEDED')
        result=self.submit(self.request('remove',{'confirm_container':cid}));self.assertEqual(result['result']['state'],'missing')
        self.assertEqual(self.driver.containers[('node-one',self.unrelated)]['state'],'running')
        self.assertNotIn(('node-one',cid),self.driver.containers)

    def test_peer_principal_project_scope_and_forged_token_denied_before_driver(self):
        r=self.request()
        with self.assertRaises(Denied):self.broker.submit(r,self.uid+1000)
        for mutate in (lambda r:r.update(authorization=r['authorization']+'0'),lambda r:r.update(project='project-two'),lambda r:r.update(app='app-two'),lambda r:r.update(principal='root')):
            candidate=copy.deepcopy(r);mutate(candidate)
            with self.assertRaises(Denied):self.submit(candidate)
        self.assertEqual(self.driver.calls,[])

    def test_no_shell_paths_options_or_arbitrary_container_parameters(self):
        for key,value in [('command','id;uname'),('host','evil'),('env',{}),('mounts',['/:/host']),('image','evil:latest')]:
            r=self.request('deploy');r['params'][key]=value;self.approve(r)
            with self.assertRaises(Denied):self.submit(r)
        for key in ('node','app','project','request_id'):
            r=self.request();r[key]='x; touch /tmp/injected'
            with self.assertRaises(Denied):self.submit(r)
        self.assertFalse(self.driver.calls)

    def test_expired_or_replayed_or_wrong_action_write_approval_denied(self):
        r=self.request('deploy');r['approval']=None
        with self.assertRaises(Denied):self.submit(r)
        r=self.request('deploy');r['approval']=self.approvals.issue({'nonce':'expired','principal':'alice','digest':'0'*64,'expires':999})
        with self.assertRaises(Denied):self.submit(r)
        r=self.request('deploy');r['action']='start'
        with self.assertRaises(Denied):self.submit(r)
        cid=self.deploy()
        one=self.request('start');self.approve(one,nonce='one-use');self.assertEqual(self.submit(one)['state'],'SUCCEEDED')
        two=self.request('stop');self.approve(two,nonce='one-use')
        with self.assertRaisesRegex(Denied,'APPROVAL_REPLAY'):self.submit(two)
        self.assertEqual(self.driver.containers[('node-one',cid)]['state'],'running')

    def test_managed_registry_and_labels_both_required_and_remove_confirmed(self):
        self.assertEqual(self.submit(self.request())['code'],'NOT_MANAGED')
        cid=self.deploy()
        wrong=self.request('remove',{'confirm_container':self.unrelated})
        self.assertEqual(self.submit(wrong)['code'],'CONFIRMATION_MISMATCH')
        self.driver.containers[('node-one',cid)]['labels']['io.fallbackhosting.project']='project-two'
        self.assertEqual(self.submit(self.request('start'))['code'],'OWNERSHIP_MISMATCH')
        self.assertEqual(self.driver.containers[('node-one',self.unrelated)]['state'],'running')

    def test_running_container_must_be_explicitly_stopped_before_remove(self):
        cid=self.deploy();self.submit(self.request('start'))
        self.assertEqual(self.submit(self.request('remove',{'confirm_container':cid}))['code'],'STOP_BEFORE_REMOVE')
        self.assertIn(('node-one',cid),self.driver.containers)

    def test_deploy_uses_approved_digest_and_fixed_resource_isolation(self):
        self.deploy();spec=next(c[2] for c in self.driver.calls if c[0]=='deploy')
        self.assertEqual(spec['network'],'none');self.assertEqual(spec['ports'],[]);self.assertEqual(spec['mounts'],[])
        self.assertTrue(spec['read_only']);self.assertTrue(spec['no_new_privileges']);self.assertFalse(spec['privileged'])
        self.assertLessEqual(spec['memory_bytes'],64*1024*1024);self.assertEqual(spec['cap_drop'],['ALL'])
        self.policy['templates']['demo']['image']='demo:latest'
        self.policy['apps']['app-one']['template']='missing'
        # Existing managed application cannot be silently recreated.
        self.assertEqual(self.submit(self.request('deploy'))['code'],'APP_ALREADY_MANAGED')

    def test_idempotency_conflict_and_no_automatic_replay(self):
        r=self.request('deploy');first=self.submit(r);calls=len(self.driver.calls)
        self.assertEqual(self.submit(r),first);self.assertEqual(len(self.driver.calls),calls)
        different=copy.deepcopy(r);different['action']='start';self.approve(different)
        with self.assertRaisesRegex(Denied,'REQUEST_ID_CONFLICT'):self.submit(different)

    def test_bounded_logs_redacted_and_not_persisted_in_jobs_or_audit(self):
        self.deploy();self.driver.logs='password=privatevalue token=privatevalue\n'+'ž'*5000
        result=self.submit(self.request('logs',{'tail':5,'max_bytes':100}))
        self.assertNotIn('privatevalue',result['result']['logs']);self.assertLessEqual(len(result['result']['logs'].encode()),100)
        self.assertTrue(result['result']['truncated'])
        with self.broker.db() as db:
            for row in db.execute('SELECT result FROM jobs'):
                self.assertNotIn('privatevalue',str(row));self.assertNotIn('ž',str(row))
        for params in ({'tail':0,'max_bytes':1},{'tail':1,'max_bytes':4097},{'tail':True,'max_bytes':1}):
            with self.assertRaises(Denied):self.submit(self.request('logs',params))

    def test_timeout_unknown_blocks_new_writes_until_reconciled(self):
        self.deploy();self.driver.fail=TimeoutError('PRIVATE_RAW_ERROR')
        result=self.submit(self.request('start'))
        self.assertEqual((result['state'],result['code']),('UNKNOWN','DRIVER_OUTCOME_UNKNOWN'))
        self.assertNotIn('PRIVATE_RAW_ERROR',json.dumps(result))
        with self.assertRaisesRegex(Denied,'NODE_BUSY_OR_UNRECONCILED'):self.submit(self.request('stop'))

    def test_actual_driver_timeout_is_bounded_without_claiming_remote_stop(self):
        self.deploy();original=self.driver.execute
        def slow(*args,**kwargs):time.sleep(0.2);return original(*args,**kwargs)
        self.driver.execute=slow;self.policy['test_timeout_seconds']=0.01
        started=time.monotonic();result=self.submit(self.request('start'))
        self.assertLess(time.monotonic()-started,0.15);self.assertEqual(result['state'],'UNKNOWN')
        time.sleep(0.25)  # owned fixture thread completes; no active external operation

    def test_restart_recovery_marks_dispatched_unknown_without_driver_call(self):
        self.deploy()
        with self.broker.db() as db:db.execute("UPDATE jobs SET state='RUNNING'")
        self.broker.close();before=len(self.driver.calls)
        self.broker=Broker(self.path,self.policy,self.driver,self.auth_key,self.approval_key,clock=lambda:1000)
        with self.broker.db() as db:row=db.execute('SELECT state,code FROM jobs').fetchone()
        self.assertEqual(row,('UNKNOWN','INTERRUPTED'));self.assertEqual(len(self.driver.calls),before)

    def test_second_broker_cannot_reset_inflight_work(self):
        with self.assertRaisesRegex(Denied,'BROKER_ALREADY_RUNNING'):
            Broker(self.path,self.policy,self.driver,self.auth_key,self.approval_key,clock=lambda:1000)

    def test_unix_peer_identity_and_bounded_framing(self):
        request=self.request('deploy')
        left,right=socket.socketpair(socket.AF_UNIX,socket.SOCK_STREAM)
        thread=threading.Thread(target=serve_connection,args=(right,self.broker));thread.start()
        body=canonical(request).encode();left.sendall(struct.pack('!I',len(body))+body)
        count=struct.unpack('!I',read_exact(left,4))[0];response=decode_json(read_exact(left,count))
        thread.join(timeout=3);left.close();self.assertEqual(response['state'],'SUCCEEDED')
        left,right=socket.socketpair(socket.AF_UNIX,socket.SOCK_STREAM)
        thread=threading.Thread(target=serve_connection,args=(right,self.broker));thread.start();left.sendall(struct.pack('!I',MAX_FRAME+1))
        count=struct.unpack('!I',read_exact(left,4))[0];response=decode_json(read_exact(left,count))
        thread.join(timeout=3);left.close();self.assertEqual(response,{'error':'FRAME_TOO_LARGE'})

    def test_frame_budget_is_absolute_even_when_bytes_keep_arriving(self):
        from operations.protocol import read_exact
        class Drip:
            count=0
            def settimeout(self,value): pass
            def recv(self,count): self.count+=1;return b'x'
        connection=Drip()
        with patch('operations.protocol.time.monotonic',side_effect=[0.0,0.8,1.6,2.4]):
            with self.assertRaisesRegex(Denied,'FRAME_TIMEOUT'):
                read_exact(connection,4,deadline=2)
        self.assertEqual(connection.count,3)

    def test_duplicate_json_fields_and_unknown_actions_rejected(self):
        with self.assertRaises(Denied):decode_json('{"action":"list","action":"remove"}')
        r=self.request();r['action']='shell'
        with self.assertRaises(Denied):self.submit(r)
