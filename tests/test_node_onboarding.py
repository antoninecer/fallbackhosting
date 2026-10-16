import json
import os
from pathlib import Path
import re
import socket
import tempfile
import threading
import unittest

import test_admin
from operations.core import Denied
from operations.node_onboarding import Onboarding,validate
from operations.protocol import serve_connection
from standby.gateway import atomic_json

SPEC={'id':'vm-test','host':'100.64.0.20','ssh_port':22,'ssh_user':'fallback-agent','fingerprint':'SHA256:'+'A'*43}
KEY='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKJY/BEcTxuLxnhKJbINHPfrkxpLz7aPXzf4JCIxwSAZ fixture'
FACTS={'user':'fallback-agent','os':'rocky','version':'9.8','cpus':2,'memory_kib':4000000,'disk_available_bytes':40000000000,'sudo':True,'docker_cli':False,'docker_ready':False,'docker_version':'','compose_version':'','preparation_supported':True}


class NodeOnboardingTests(unittest.TestCase):
    def api(self,tmp,driver=None):
        def default(spec,action):return dict(FACTS,**({'docker_ready':True,'docker_cli':True,'docker_version':'fixture-version','compose_version':'fixture-compose'} if action=='prepare' else {}))
        api=Onboarding(tmp,os.getuid(),'admin',KEY,driver or default);self.addCleanup(api.process_lock.close);return api
    def check(self,api):return api.submit({'kind':'inspect_node','actor':'admin','spec':SPEC},os.getuid())
    def test_actual_stages_require_explicit_revision_bound_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls=[]
            def driver(spec,action):
                calls.append(action);return dict(FACTS,**({'docker_ready':True,'compose_version':'fixture'} if action=='prepare' else {}))
            api=self.api(tmp,driver);self.check(api);self.assertEqual(calls,[]);api.advance();self.assertEqual(calls,['inspect'])
            state=api.view('vm-test');self.assertEqual(state['phase'],'READY')
            request={'kind':'initialize_node','actor':'admin','node':'vm-test','revision':state['revision'],'confirmation':False}
            with self.assertRaises(Denied):api.submit(request,os.getuid())
            with self.assertRaises(Denied):api.submit(dict(request,confirmation=True,revision=0),os.getuid())
            api.submit(dict(request,confirmation=True),os.getuid());self.assertEqual(calls,['inspect']);api.advance()
            self.assertEqual(calls,['inspect','prepare']);self.assertEqual(api.view('vm-test')['phase'],'SUCCEEDED')
            with self.assertRaises(Denied):api.submit(dict(request,confirmation=True),os.getuid())
    def test_target_validation_peer_actor_and_command_rejection(self):
        for change in ({'host':'127.0.0.1'},{'host':'192.168.1.1'},{'host':'example.com'},{'id':'../escape'},{'ssh_user':'root; id'},{'ssh_port':True},{'fingerprint':'SHA256:bad'}):
            with self.assertRaises(Denied):validate(dict(SPEC,**change))
        with tempfile.TemporaryDirectory() as tmp:
            api=self.api(tmp);request={'kind':'inspect_node','actor':'admin','spec':SPEC}
            with self.assertRaises(Denied):api.submit(request,os.getuid()+1)
            with self.assertRaises(Denied):api.submit(dict(request,actor='guest'),os.getuid())
            with self.assertRaises(Denied):api.submit(dict(request,command='id'),os.getuid())
    def test_failed_or_interrupted_preparation_cannot_be_replayed(self):
        with tempfile.TemporaryDirectory() as tmp:
            def driver(spec,action):
                if action=='prepare':raise TimeoutError('private error must not be returned')
                return FACTS
            api=self.api(tmp,driver);self.check(api);api.advance();s=api.view('vm-test')
            api.submit({'kind':'initialize_node','actor':'admin','node':'vm-test','revision':s['revision'],'confirmation':True},os.getuid());api.advance()
            self.assertEqual(api.view('vm-test')['phase'],'NEEDS_REVIEW');self.assertNotIn('private error',json.dumps(api.view('vm-test')))
            with self.assertRaises(Denied):self.check(api)
        with tempfile.TemporaryDirectory() as tmp:
            api=self.api(tmp);self.check(api);api.process_lock.close();restored=self.api(tmp)
            self.assertEqual(restored.view('vm-test')['phase'],'NEEDS_REVIEW')
    def test_php_auth_check_confirm_save_and_forged_target_denied(self):
        app=test_admin.AdminTests();app.setUp();self.addCleanup(app.tearDown)
        api=self.api(app.data/'onboard-runtime');listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);listener.bind(str(app.data/'onboarding.sock'));listener.listen(8);listener.settimeout(.1);stopped=threading.Event()
        def serve():
            while not stopped.is_set():
                try:c,_=listener.accept()
                except socket.timeout:continue
                serve_connection(c,api)
        thread=threading.Thread(target=serve);thread.start()
        try:
            self.assertEqual(app.request('/?onboard=1')[0],401);app.login()
            status,body,_=app.request('/?onboard=1');self.assertEqual(status,200);self.assertIn('Veřejný SSH klíč',body)
            data={'action':'onboard-check','csrf':app.csrf(),'id':SPEC['id'],'name':'Fixture VM','host':SPEC['host'],'ssh_port':'22','ssh_user':SPEC['ssh_user'],'host_fingerprint':SPEC['fingerprint']}
            self.assertEqual(app.request('/?onboard=1',dict(data,csrf='bad'))[0],403)
            self.assertEqual(app.request('/?onboard=1',data,origin='https://invalid.example')[0],403)
            self.assertEqual(app.request('/?onboard=1',dict(data,command='id'))[0],422)
            self.assertEqual(app.request('/?onboard=1',data)[0],303);api.advance();state=api.view(SPEC['id'])
            path='/?onboard=job&node='+SPEC['id'];self.assertIn('Inicializovat server',app.request(path)[1])
            request={'action':'onboard-init','csrf':app.csrf(),'id':SPEC['id'],'revision':str(state['revision'])}
            self.assertEqual(app.request(path,request)[0],422)
            self.assertEqual(app.request(path,dict(request,confirmation='1'))[0],303)
            saved=next(n for n in app.inventory()['servers'] if n['id']==SPEC['id']);self.assertEqual(saved['observations']['fingerprint']['status'],'PASS');self.assertEqual(saved['observations']['docker']['status'],'UNKNOWN')
            api.advance();state=api.view(SPEC['id'])
            self.assertEqual(app.request(path,{'action':'onboard-finish','csrf':app.csrf(),'id':SPEC['id'],'revision':str(state['revision'])})[0],303)
            saved=next(n for n in app.inventory()['servers'] if n['id']==SPEC['id']);self.assertEqual(saved['observations']['docker']['status'],'PASS')
            app.request(data={'action':'logout','csrf':app.csrf()});self.assertEqual(app.request(path)[0],401)
        finally:stopped.set();thread.join(3);listener.close()
