import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import unittest

import test_admin
from operations.core import Denied
from operations.protocol import serve_connection
from standby.control import Control

ROOT=Path(__file__).resolve().parents[1]


class StandbyControlTest(unittest.TestCase):
    def test_restart_preserves_scheduled_control_and_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            control=Control(tmp,os.getuid(),'admin')
            windows=[{'start_utc':'2026-10-16T12:00:00Z','end_utc':'2026-10-16T13:00:00Z'}]
            control.submit({'kind':'set_control','actor':'admin','app':'demo','revision':1,'params':{'manual_maintenance':False,'windows':windows}},os.getuid())
            restored=Control(tmp,os.getuid(),'admin').view()
            self.assertEqual(restored['control']['windows'],windows);self.assertEqual(restored['revision'],2);self.assertEqual(len(restored['audit']),1)

    def test_peer_actor_scope_fields_revision_and_fail_closed_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime=Path(tmp);control=Control(runtime,os.getuid(),'admin')
            view={'kind':'view','actor':'admin','app':'demo'}
            self.assertEqual(control.read(view,os.getuid())['revision'],1)
            for bad in (dict(view,actor='other'),dict(view,app='other'),dict(view,command='rm')):
                with self.assertRaises(Denied):control.read(bad,os.getuid())
            with self.assertRaises(Denied):control.read(view,os.getuid()+1)
            request={'kind':'set_control','actor':'admin','app':'demo','revision':1,'params':{'manual_maintenance':True,'windows':[]}}
            result=control.submit(request,os.getuid())
            self.assertEqual(result['revision'],2);self.assertTrue((runtime/'maintenance').exists())
            with self.assertRaises(Denied):control.submit(request,os.getuid())
            request['revision']=2;request['params']['manual_maintenance']=False
            control.submit(request,os.getuid())
            self.assertTrue((runtime/'unhealthy').exists());self.assertFalse((runtime/'maintenance').exists())
            self.assertEqual(len(control.view()['audit']),2)
            request['revision']=3;request['params']['windows']=[{'start_utc':'bad','end_utc':'bad'}]
            with self.assertRaises(Denied):control.submit(request,os.getuid())
            self.assertEqual(control.view()['revision'],3)

    def test_actual_php_auth_csrf_and_unix_control_roundtrip(self):
        app=test_admin.AdminTests();app.setUp();stop=threading.Event();listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        listener.bind(str(app.data/'standby.sock'));listener.listen(5);listener.settimeout(.1)
        control=Control(app.data/'standby-runtime',os.getuid(),'admin',{'release':'fixture-only','remote_backup':'VERIFIED_READBACK_RESTORE'})
        def serve():
            while not stop.is_set():
                try:c,_=listener.accept()
                except socket.timeout:continue
                serve_connection(c,control)
        thread=threading.Thread(target=serve,daemon=True);thread.start()
        try:
            self.assertEqual(app.request('/?standby=1')[0],401)
            app.login()
            status,body,_=app.request('/?standby=1');self.assertEqual(status,200)
            self.assertIn('Zapnout údržbu',body);self.assertIn('Chybí aktuální ověření',body)
            import re
            csrf=re.search(r'name="csrf" value="([a-f0-9]+)"',body)[1]
            data={'action':'standby-control','csrf':csrf,'revision':'1','mode':'maintenance'}
            self.assertEqual(app.request('/?standby=1',data,origin='https://invalid.example')[0],403)
            self.assertEqual(app.request('/?standby=1',dict(data,csrf='wrong'))[0],403)
            self.assertEqual(app.request('/?standby=1',data)[0],303)
            self.assertTrue((control.runtime/'maintenance').exists())
            self.assertEqual(app.request('/?standby=1',data)[0],422)
            self.assertEqual(app.request('/?standby=1',dict(data,revision='2',mode='shell'))[0],422)
            self.assertEqual(app.request('/?standby=1',dict(data,revision='2',mode='auto',command='bad'))[0],422)
            self.assertEqual(app.request('/?standby=1',dict(data,revision='2',mode='auto'))[0],303)
            self.assertFalse((control.runtime/'maintenance').exists())
            self.assertTrue((control.runtime/'unhealthy').exists())
        finally:stop.set();thread.join(3);listener.close();app.tearDown()

    def test_prague_conversion_rejects_dst_ambiguity_and_nonexistent_time(self):
        code="require 'admin/lib.php'; require 'admin/standby.php'; $i=json_decode(stream_get_contents(STDIN),true); try{echo standby_prague_utc($i['date']);}catch(InputError $e){exit(2);}"
        for value,expected in (('2026-10-16T16:00','2026-10-16T14:00:00Z'),('2026-12-16T16:00','2026-12-16T15:00:00Z')):
            result=subprocess.run(['php','-r',code],cwd=ROOT,input=json.dumps({'date':value}),capture_output=True,text=True)
            self.assertEqual(result.returncode,0);self.assertEqual(result.stdout,expected)
        for value in ('2026-10-25T02:30','2026-03-29T02:30','2026-02-30T10:00'):
            result=subprocess.run(['php','-r',code],cwd=ROOT,input=json.dumps({'date':value}),capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
