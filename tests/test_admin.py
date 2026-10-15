"""Black-box PHP inventory/auth tests on loopback, with disposable private data."""
import concurrent.futures
import http.client
import json
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import tempfile
import time
import unittest
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]

def node(node_id='ctx-test', **extra):
    return dict(id=node_id, name=node_id, host='192.0.2.10', ssh_port='22',
                ssh_user='service', runtime='docker', platform='lxc',
                credential_ref='test-identity', host_fingerprint='', description='',
                enabled='1', **extra)

class AdminTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.data = Path(self.temp.name)
        self.env = os.environ.copy()
        self.env['FH_ADMIN_DATA'] = str(self.data)
        self.password = secrets.token_urlsafe(24)
        self.cli('bootstrap', {'username':'admin', 'password':self.password})
        seeded = node()
        seeded['observations'] = {
            'ssh':{'status':'PASS','observed_at_utc':'2026-10-15T08:25:31Z'},
            'docker':{'status':'PASS','observed_at_utc':'2026-10-15T08:35:47Z'},
            'fingerprint':{'status':'NEEDS_TEST'}}
        self.cli('seed', {'servers':[seeded]})
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0))
            self.port=sock.getsockname()[1]
        self.origin=f'http://127.0.0.1:{self.port}'
        self.env.update(FH_ADMIN_ORIGIN=self.origin,FH_ADMIN_ALLOW_LOCAL_HTTP='1')
        self.process=subprocess.Popen(['php','-S',f'127.0.0.1:{self.port}','-t',str(ROOT/'admin/public')],env=self.env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        self.cookie=''
        for attempt in range(100):
            try:
                status, _, _ = self.request()
                if status: break
            except OSError:
                time.sleep(0.02)
        else:
            self.fail('Local PHP server unavailable')

    def tearDown(self):
        self.process.terminate()
        try:self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:self.process.kill();self.process.wait()
        self.temp.cleanup()

    def cli(self,command,data,check=True):
        return subprocess.run(['php',str(ROOT/'admin/manage.php'),command],env=self.env,
            input=json.dumps(data),text=True,capture_output=True,check=check)

    def request(self,path='/',data=None,origin=None):
        connection=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        headers={}
        if self.cookie:headers['Cookie']=self.cookie
        if data is not None:
            headers.update({'Content-Type':'application/x-www-form-urlencoded','Origin':self.origin if origin is None else origin})
        connection.request('GET' if data is None else 'POST',path,body=None if data is None else urlencode(data),headers=headers)
        response=connection.getresponse();body=response.read().decode();status=response.status;result=dict(response.getheaders())
        if result.get('Set-Cookie'): self.cookie=result['Set-Cookie'].split(';',1)[0]
        connection.close()
        return status,body,result

    def csrf(self):
        status,body,_=self.request();self.assertEqual(status,200)
        return re.search(r'name="csrf" value="([a-f0-9]+)"',body)[1]

    def login(self):
        csrf=self.csrf();before=self.cookie
        result=self.request(data={'action':'login','csrf':csrf,'username':'admin','password':self.password})
        self.assertEqual(result[0],303)
        self.assertNotEqual(before,self.cookie)

    def post_node(self,record,revision=1,mode='create',**extra):
        return self.request(data=dict(action='save-server',csrf=self.csrf(),revision=str(revision),mode=mode,**record,**extra))

    def inventory(self):return json.loads((self.data/'inventory.json').read_text())

    def test_auth_boundary_cookie_logout_and_setup_closed(self):
        self.cookie=''
        status,body,headers=self.request()
        self.assertEqual(status,200);self.assertNotIn('192.0.2.10',body)
        flags={item.strip().lower() for item in headers['Set-Cookie'].split(';')[1:]}
        self.assertTrue({'secure','httponly','samesite=strict'} <= flags)
        self.assertIn('no-store',headers['Cache-Control'].split(', '))
        self.assertIn("frame-ancestors 'none'",headers['Content-Security-Policy'])
        self.assertEqual(self.post_node(node('second'))[0],401)
        self.login();self.assertIn('192.0.2.10',self.request()[1])
        old_cookie=self.cookie
        self.assertEqual(self.request(data={'action':'logout','csrf':self.csrf()})[0],303)
        self.cookie=old_cookie;self.assertNotIn('192.0.2.10',self.request()[1])
        (self.data/'auth.json').unlink()
        self.assertEqual(self.request()[0],503)

    def test_csrf_origin_and_unauthorized_raw_paths(self):
        self.login()
        self.assertEqual(self.request(data={'action':'save-server','csrf':'bad'})[0],403)
        self.assertEqual(self.request(data={'action':'logout','csrf':self.csrf()},origin='https://evil.example')[0],403)
        for path in ['/inventory.json','/auth.json','/.local/admin/inventory.json','/lib.php','/manage.php']:
            self.assertEqual(self.request(path)[0],404)
        self.assertEqual(self.inventory()['revision'],1)

    def test_multiple_nodes_edit_disable_and_concurrency(self):
        self.login()
        second=node('second');second['runtime']='podman';second['platform']='vm'
        self.assertEqual(self.post_node(second)[0],303)
        self.assertEqual(len(self.inventory()['servers']),2)
        self.assertEqual(self.post_node(node('third'),revision=1)[0],409)
        self.assertEqual(self.post_node(node('second'),revision=2)[0],422)
        changed=node();changed['host']='192.0.2.11';changed['enabled']='0'
        self.assertEqual(self.post_node(changed,revision=2,mode='edit')[0],303)
        current=self.inventory();self.assertEqual(current['revision'],3)
        edited=current['servers'][0];self.assertFalse(edited['enabled'])
        self.assertEqual(edited['observations']['ssh']['status'],'UNKNOWN')
        self.assertEqual(edited['observations']['docker']['status'],'UNKNOWN')
        self.assertEqual(edited['observations']['fingerprint']['status'],'NEEDS_TEST')
        self.assertEqual(len(current['audit']),2)
        self.assertEqual(len(current['servers']),2)

    def test_display_escaping_and_no_forged_observations(self):
        self.login()
        record=node('xss-test');record['name']='<script>alert(1)</script>'
        self.assertEqual(self.post_node(record)[0],303)
        body=self.request()[1];self.assertNotIn('<script>alert',body);self.assertIn('&lt;script&gt;',body)
        self.assertEqual(self.post_node(node('forged'),revision=2,observations='PASS')[0],422)
        self.assertEqual(self.post_node(node('key-test'),revision=2,private_key='NOT_A_REAL_KEY')[0],422)

    def test_invalid_target_key_paths_and_commands_are_rejected(self):
        self.login()
        for key,value in [('host','host;touch example'),('host','https://example.com'),('host','-oProxyCommand=bad'),('ssh_port','0'),('ssh_user','root;id'),('credential_ref','/private/key'),('runtime','shell'),('host_fingerprint','fake')]:
            with self.subTest(key=key,value=value):
                record=node('invalid');record[key]=value
                self.assertEqual(self.post_node(record)[0],422)
        self.assertEqual(self.inventory()['revision'],1)

    def test_metadata_edit_preserves_dated_observations(self):
        self.login()
        record=node();record['name']='Readable name'
        self.assertEqual(self.post_node(record,mode='edit')[0],303)
        self.assertEqual(self.inventory()['servers'][0]['observations']['docker']['status'],'PASS')

    def test_rate_limit_and_bootstrap_cannot_overwrite(self):
        token=self.csrf()
        for _ in range(5):
            self.assertEqual(self.request(data={'action':'login','csrf':token,'username':'admin','password':'incorrect'})[0],401)
        self.assertEqual(self.request(data={'action':'login','csrf':token,'username':'admin','password':self.password})[0],429)
        before=(self.data/'auth.json').read_bytes()
        self.assertNotEqual(self.cli('bootstrap',{'username':'other','password':secrets.token_urlsafe(24)},check=False).returncode,0)
        self.assertEqual((self.data/'auth.json').read_bytes(),before)
        self.assertNotEqual(self.cli('seed',{'servers':[node('overwrite')]},check=False).returncode,0)

    def test_atomic_revision_lock_across_processes(self):
        command="require $argv[1]; $a=json_decode(stream_get_contents(STDIN),true); try { save_server($a,1,'test','create'); echo 'saved'; } catch (RevisionConflict $e) { echo 'conflict'; }"
        def save(i):
            return subprocess.run(['php','-r',command,str(ROOT/'admin/lib.php')],input=json.dumps(node(f'parallel-{i}')),text=True,capture_output=True,env=self.env,check=True).stdout
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(save,[1,2]))
        self.assertEqual(sorted(results),['conflict','saved'])
        self.assertEqual(self.inventory()['revision'],2)
        for filename in ['inventory.json','auth.json','inventory.lock']:
            self.assertEqual((self.data/filename).stat().st_mode & 0o077,0)

if __name__=='__main__':unittest.main()
