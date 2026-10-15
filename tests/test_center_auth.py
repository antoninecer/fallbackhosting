"""Disposable PHP session tests for every protected center artifact."""
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import tempfile
import time
import unittest
from unittest.mock import patch
import test_admin


class ProtectedCenterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.artifact = Path(self.temp.name)
        self.files = {'index.html':'<!doctype html><h1>PRIVATE_CENTER_TEST</h1>', 'center.css':'body{color:black}', 'center.js':'"use strict";', 'resume.txt':'PRIVATE_RESUME_TEST'}
        for name, body in self.files.items(): (self.artifact/name).write_text(body)
        self.manifest={name:hashlib.sha256(body.encode()).hexdigest() for name,body in self.files.items()}
        (self.artifact/'manifest.json').write_text(json.dumps(self.manifest))
        self.environment=patch.dict(os.environ, {'FH_CENTER_ARTIFACT':str(self.artifact)})
        self.environment.start()
        self.app=test_admin.AdminTests(methodName='test_auth_boundary_cookie_logout_and_setup_closed')
        self.app.setUp()
        self.before=(self.app.data/'inventory.json').read_bytes()

    def tearDown(self):
        self.app.tearDown();self.environment.stop();self.temp.cleanup()

    def request(self,asset,method='GET'):
        connection=http.client.HTTPConnection('127.0.0.1',self.app.port,timeout=5)
        connection.request(method,'/?center='+asset,headers={'Cookie':self.app.cookie} if self.app.cookie else {})
        response=connection.getresponse();body=response.read().decode();result=(response.status,body,dict(response.getheaders()))
        connection.close();return result

    def test_all_assets_require_session_and_logout_revokes_every_asset(self):
        for asset in list(self.files)+['manifest.json']:
            self.assertEqual(self.request(asset)[0],401)
        self.app.login()
        for asset in list(self.files)+['manifest.json']:
            status,body,headers=self.request(asset)
            self.assertEqual(status,200)
            self.assertIn('no-store',headers['Cache-Control'])
            self.assertEqual(headers['X-Content-Type-Options'],'nosniff')
            if asset in self.files:self.assertEqual(body,self.files[asset])
        self.assertIn('attachment',self.request('resume.txt')[2]['Content-Disposition'])
        csrf=self.app.csrf()
        self.assertEqual(self.app.request(data={'action':'logout','csrf':csrf})[0],303)
        for asset in list(self.files)+['manifest.json']:
            self.assertEqual(self.request(asset)[0],401)
        self.assertEqual((self.app.data/'inventory.json').read_bytes(),self.before)

    def test_head_supported_but_mutating_methods_and_unknown_paths_denied(self):
        self.app.login()
        status,body,headers=self.request('index.html','HEAD')
        self.assertEqual((status,body),(200,''))
        self.assertEqual(int(headers['Content-Length']),len(self.files['index.html']))
        for method in ('POST','PUT','DELETE'):
            self.assertEqual(self.request('index.html',method)[0],405)
        for path in ('../lib.php','%2e%2e%2flib.php','index.php','resume.txt%00','unknown.json','index.html&center[]=resume.txt'):
            self.assertEqual(self.request(path)[0],404)

    def test_missing_corrupt_oversized_and_symlink_assets_fail_closed(self):
        self.app.login()
        for body in ('CORRUPTED','x'*131073):
            (self.artifact/'resume.txt').write_text(body)
            status,body,_=self.request('resume.txt')
            self.assertEqual(status,503);self.assertNotIn('PRIVATE_RESUME_TEST',body)
        (self.artifact/'resume.txt').unlink()
        self.assertEqual(self.request('resume.txt')[0],503)
        (self.artifact/'resume.txt').symlink_to(self.artifact/'index.html')
        self.assertEqual(self.request('resume.txt')[0],503)
        (self.artifact/'manifest.json').write_text('{}')
        self.assertEqual(self.request('index.html')[0],503)

    def test_expired_session_cannot_fetch_resume_or_html(self):
        self.app.login()
        session_id=self.app.cookie.split('=',1)[1]
        path=self.app.data/'sessions'/('sess_'+session_id)
        contents=path.read_text()
        changed,count=re.subn(r'last_seen\|i:\d+;',f'last_seen|i:{int(time.time())-1900};',contents)
        self.assertEqual(count,1)
        path.write_text(changed)
        self.assertEqual(self.request('resume.txt')[0],401)
        self.assertEqual(self.request('index.html')[0],401)
