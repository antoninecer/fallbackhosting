"""Actual PHP/Unix peer RPC with inert Docker and a trusted fixture authority."""
import copy
import json
from pathlib import Path
import socket
import struct
import subprocess
import threading
import unittest
from uuid import uuid4
import test_operations
from operations.protocol import serve_connection

ROOT=Path(__file__).resolve().parents[1]

class PHPIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.fixture=test_operations.OperationsTests(methodName='test_all_operations_only_touch_registered_labelled_app')
        self.fixture.setUp()
        self.path=Path(self.fixture.temp.name)/'broker.sock'
    def tearDown(self):self.fixture.tearDown()
    def rpc(self,request,oversized=False):
        path=self.path.with_name('rpc-'+uuid4().hex[:12]+'.sock')
        listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);listener.bind(str(path));listener.listen(1);listener.settimeout(3)
        path.chmod(0o600)
        def serve():
            try:
                connection,_=listener.accept()
                if oversized:
                    connection.sendall(struct.pack('!I',20000));connection.close()
                else:serve_connection(connection,self.fixture.broker)
            finally:listener.close()
        thread=threading.Thread(target=serve);thread.start()
        try:
            result=subprocess.run(['php',str(ROOT/'admin/operations-client.php')],input=json.dumps({'socket':str(path),'request':request}),capture_output=True,text=True,timeout=25)
        finally:
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
            path.unlink(missing_ok=True)
        return result
    def call(self,request):
        response=self.rpc(request);self.assertEqual(response.returncode,0,response.stderr)
        return json.loads(response.stdout)
    def view(self):
        r=self.fixture.request('inspect')
        request={k:r[k] for k in ('request_id','node','project','app','authorization')};request['kind']='view'
        return self.call(request)
    def render(self,views):
        return subprocess.run(['php',str(ROOT/'admin/operations-view.php')],input=json.dumps(views),capture_output=True,text=True,timeout=5)

    def test_php_fixture_full_lifecycle_and_scoped_history(self):
        created=self.call(self.fixture.request('deploy'));self.assertEqual(created['state'],'SUCCEEDED');cid=created['result']['container_id']
        for action in ('start','restart','inspect','list'):
            self.assertEqual(self.call(self.fixture.request(action))['state'],'SUCCEEDED')
        self.assertEqual(self.call(self.fixture.request('logs',{'tail':5,'max_bytes':100}))['state'],'SUCCEEDED')
        self.assertEqual(self.call(self.fixture.request('stop'))['state'],'SUCCEEDED')
        view=self.view();self.assertEqual(view['app'],'app-one');self.assertEqual(view['last_observation']['state'],'exited')
        rendered=self.render([view]);self.assertEqual(rendered.returncode,0,rendered.stderr)
        for text in ('Aplikace podle serverů','Požadavky, průběh a výsledky','Chyby a nejasné výsledky','Audit operací','neověřená','uložený výsledek'):
            self.assertIn(text,rendered.stdout)
        self.assertNotIn('authorization',rendered.stdout);self.assertNotIn('privatevalue',rendered.stdout)
        removed=self.call(self.fixture.request('remove',{'confirm_container':cid}));self.assertEqual(removed['result']['state'],'missing')
        self.assertEqual(self.fixture.driver.containers[('node-one',self.fixture.unrelated)]['state'],'running')

    def test_php_cannot_mint_principal_or_operator_approval(self):
        r=self.fixture.request('deploy');r['approval']=None
        response=self.call(r);self.assertIn('error',response);self.assertEqual(self.fixture.driver.calls,[])
        r=self.fixture.request('inspect');r['principal']='root'
        self.assertEqual(self.call(r),{'error':'INVALID_FIELDS'})
        r=self.fixture.request('inspect');r['project']='project-two'
        self.assertEqual(self.call(r),{'error':'SCOPE_DENIED'})

    def test_php_rejects_oversized_frame_without_leaking_socket_or_token(self):
        result=self.rpc(self.fixture.request(),oversized=True)
        self.assertEqual(result.returncode,1);self.assertEqual(result.stdout,'')
        self.assertEqual(result.stderr,'Operations request unavailable or invalid.\n')

    def test_view_escapes_untrusted_job_text_and_handles_no_apps(self):
        self.call(self.fixture.request('deploy'));view=self.view()
        view['jobs'][0]['action']='<script>alert("x")</script>'
        rendered=self.render([view]);self.assertEqual(rendered.returncode,0)
        self.assertNotIn('<script>alert',rendered.stdout);self.assertIn('&lt;script&gt;',rendered.stdout)
        empty=self.render([]);self.assertEqual(empty.returncode,0);self.assertIn('Žádné přiřazené aplikace',empty.stdout)
        view['authorization']='PRIVATE_CAPABILITY'
        self.assertEqual(self.render([view]).returncode,1)
