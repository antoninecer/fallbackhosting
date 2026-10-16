import hashlib
import json
import os
from pathlib import Path
import re
import socket
import threading
import unittest

import test_admin
from test_standby import fixture
from operations.core import Denied
from operations.protocol import serve_connection
from standby.backup import restore
from standby.gateway import atomic_json
from standby.publish_service import PublicationAPI
from standby.publishing import Publishing
from standby.snapshot import build, publish


class PublishingTests(unittest.TestCase):
    def workflow(self, root, origin, provider=None):
        public=root/'public';(public/'releases').mkdir(parents=True)
        old,_=build(origin,public/'releases','old notice','contact','/demo/__fallback_assets')
        publish(old,public/'current')
        def good(candidate, archive, digest):
            restore(archive,archive.parent/(candidate.name+'-restored'),digest)
            return {'sha256':digest,'remote_copy':'VERIFIED','remote_readback':'VERIFIED','isolated_restore':'PASS'}
        config=dict(origin=origin,store=str(root/'work'),public=str(public),message='new notice',contact='contact',asset_prefix='/demo/__fallback_assets')
        return Publishing(config,provider or good),old

    def prepare(self, flow):
        flow.request('prepare',flow.view()['revision']);flow.advance()

    def test_prepare_preview_publish_and_rollback_without_changing_live_control(self):
        with fixture() as (root,origin,*_):
            flow,old=self.workflow(root,origin)
            self.prepare(flow)
            state=flow.view();self.assertEqual(state['phase'],'READY')
            self.assertEqual(flow.current(),old.name)
            self.assertNotIn('origin',json.dumps(state));self.assertNotIn(str(root),json.dumps(state))
            candidate=state['candidate']
            self.assertIn('new notice',(flow.public/'releases'/candidate/'index.html').read_text())
            flow.request('publish',state['revision']);flow.advance()
            self.assertEqual(flow.current(),candidate);self.assertEqual(flow.view()['phase'],'PUBLISHED')
            flow.request('rollback',flow.view()['revision']);flow.advance()
            self.assertEqual(flow.current(),old.name);self.assertEqual(flow.view()['phase'],'ROLLED_BACK')

    def test_failed_backup_and_stale_or_busy_requests_preserve_current(self):
        with fixture() as (root,origin,*_):
            flow,old=self.workflow(root,origin,lambda *args:{})
            with self.assertRaises(Denied):flow.request('publish',1)
            flow.request('prepare',1)
            with self.assertRaises(Denied):flow.request('prepare',1)
            with self.assertRaises(Denied):flow.request('prepare',flow.view()['revision'])
            flow.advance();self.assertEqual(flow.view()['phase'],'FAILED');self.assertEqual(flow.current(),old.name)
            self.assertIsNone(flow.view()['candidate'])

    def test_tamper_and_concurrent_pointer_change_refuse_publication(self):
        with fixture() as (root,origin,*_):
            flow,old=self.workflow(root,origin);self.prepare(flow)
            state=flow.view();candidate=flow.public/'releases'/state['candidate']
            saved=(candidate/'index.html').read_bytes();(candidate/'index.html').write_text('tampered')
            with self.assertRaises(ValueError):flow.request('publish',state['revision'])
            self.assertEqual(flow.current(),old.name)
            (candidate/'index.html').write_bytes(saved)
            other,_=build(origin,flow.public/'releases','other notice','contact','/demo/__fallback_assets')
            publish(other,flow.public/'current')
            with self.assertRaises(Denied):flow.request('publish',state['revision'])
            self.assertEqual(flow.current(),other.name)

    def test_restart_requires_review_instead_of_repeating_interrupted_operation(self):
        with fixture() as (root,origin,*_):
            flow,old=self.workflow(root,origin);flow.request('prepare',1)
            recovered=Publishing(flow.config,lambda *args:self.fail('Must not retry backup'))
            self.assertEqual(recovered.view()['phase'],'NEEDS_REVIEW')
            recovered.advance();self.assertEqual(recovered.current(),old.name)
            with self.assertRaises(Denied):recovered.request('prepare',recovered.view()['revision'])

    def test_api_peer_actor_scope_and_no_arbitrary_fields(self):
        with fixture() as (root,origin,*_):
            flow,old=self.workflow(root,origin);api=PublicationAPI(flow,os.getuid(),'admin')
            request={'kind':'publication','actor':'admin','app':'demo','revision':1,'operation':'prepare'}
            for bad in (dict(request,actor='other'),dict(request,app='other'),dict(request,origin=origin),dict(request,operation='shell')):
                with self.assertRaises(Denied):api.submit(bad,os.getuid())
            with self.assertRaises(Denied):api.submit(request,os.getuid()+1)
            self.assertTrue(api.submit(request,os.getuid())['ok'])

    def test_php_authenticated_workflow_preview_assets_csrf_and_traversal(self):
        with fixture() as (root,origin,*_):
            flow,old=self.workflow(root,origin);self.prepare(flow)
            app=test_admin.AdminTests()
            saved=os.environ.get('FH_STANDBY_RELEASES');os.environ['FH_STANDBY_RELEASES']=str(flow.public/'releases')
            try:app.setUp()
            finally:
                if saved is None:os.environ.pop('FH_STANDBY_RELEASES',None)
                else:os.environ['FH_STANDBY_RELEASES']=saved
            listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);listener.bind(str(app.data/'publication.sock'));listener.listen(5);listener.settimeout(.1)
            stopped=threading.Event();api=PublicationAPI(flow,os.getuid(),'admin')
            def serve():
                while not stopped.is_set():
                    try:connection,_=listener.accept()
                    except socket.timeout:continue
                    serve_connection(connection,api)
            thread=threading.Thread(target=serve);thread.start()
            try:
                candidate=flow.view()['candidate'];url='/?publication-preview='+candidate
                self.assertEqual(app.request(url)[0],401)
                app.login()
                status,body,headers=app.request(url)
                self.assertEqual(status,200);self.assertNotIn('<form',body)
                self.assertIn('&amp;asset=assets/style.css',body);self.assertIn('sandbox',headers['Content-Security-Policy'])
                self.assertEqual(app.request(url+'&asset=assets/style.css')[0],200)
                for bad in ('../manifest.json','manifest.json','assets/../../secret'):
                    self.assertEqual(app.request(url+'&asset='+bad)[0],404)
                self.assertEqual(app.request('/?publication-preview=../../secret')[0],404)
                data={'action':'standby-publication','csrf':app.csrf(),'revision':str(flow.view()['revision']),'operation':'publish'}
                self.assertEqual(app.request('/?standby=1',dict(data,csrf='wrong'))[0],403)
                self.assertEqual(app.request('/?standby=1',data,origin='https://wrong.example')[0],403)
                self.assertEqual(app.request('/?standby=1',dict(data,origin='https://unapproved.example'))[0],422)
                self.assertEqual(app.request('/?standby=1',data)[0],303)
                flow.advance();self.assertEqual(flow.current(),candidate)
                self.assertEqual(app.request('/?standby=1',data)[0],422)
            finally:stopped.set();thread.join(3);listener.close();app.tearDown()
