from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import http.server
import io
import json
from pathlib import Path
import shutil
import socket
import subprocess
import tarfile
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

from standby.snapshot import build, publish, verify, origin_url
from standby.gateway import atomic_json, tick, server_config, standalone_config, maintenance_active
from standby.backup import create, restore
from standby.publication import publish_with_backup

ROOT = Path(__file__).resolve().parents[1]


def port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0)); return s.getsockname()[1]


@contextmanager
def fixture():
    state = {'healthy': True, 'posts': 0, 'cookie': False, 'redirect': False}
    with tempfile.TemporaryDirectory(prefix='fallback-standby-') as tmp:
        path = Path(tmp); image = path/'image.jpg'
        subprocess.run(['convert','-size','1200x800','plasma:fractal','-quality','95',str(image)],check=True,capture_output=True,timeout=20)
        files = {'/index.html': (ROOT/'demo/site/index.html').read_bytes(), '/style.css': (ROOT/'demo/site/style.css').read_bytes(), '/hero.jpg': image.read_bytes()}
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                if not state['healthy']: self.send_error(503); return
                if state['redirect'] and self.path == '/index.html': self.send_response(302); self.send_header('Location','http://127.0.0.1:1/private'); self.end_headers(); return
                if self.path == '/health': body=b'fallback-demo-healthy\n'
                elif self.path in ('/','/index.html'): body=files['/index.html']
                elif self.path in files: body=files[self.path]
                else: self.send_error(404); return
                self.send_response(200)
                self.send_header('Content-Type', 'text/html' if self.path in ('/','/index.html') else ('text/css' if self.path=='/style.css' else ('image/jpeg' if self.path=='/hero.jpg' else 'text/plain')))
                if state['cookie']:self.send_header('Set-Cookie','private=session')
                self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
            def do_POST(self):
                state['posts']+=1;self.send_response(200);self.end_headers();self.wfile.write(b'DEMO_ONLY')
        httpd=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=httpd.serve_forever,daemon=True);thread.start()
        try: yield path, 'http://127.0.0.1:'+str(httpd.server_port), state, files
        finally:httpd.shutdown();httpd.server_close();thread.join()


def get(url, data=None):
    try: response=urllib.request.urlopen(url,data=data,timeout=8)
    except urllib.error.HTTPError as e:response=e
    return response.code,response.headers,response.read()


class StandbyTest(unittest.TestCase):
    def test_failed_backup_preserves_last_published_release(self):
        with fixture() as (root,origin,state,files):
            release,_=build(origin,root/'releases','old notice','contact');publish(release,root/'current')
            config={'origin':origin,'store':str(root),'message':'new notice','contact':'contact','asset_prefix':'/__fallback_assets'}
            with self.assertRaises(ValueError):publish_with_backup(config,lambda *args:{'remote_copy':'NOT_VERIFIED'})
            self.assertEqual((root/'current').resolve(),release)
            def verified_fixture_provider(candidate,archive,digest):
                restore(archive,root/'fixture-restore',digest)
                return {'sha256':digest,'remote_copy':'VERIFIED','remote_readback':'VERIFIED','isolated_restore':'PASS'}
            result=publish_with_backup(config,verified_fixture_provider)
            self.assertEqual(result['phase'],'PUBLISHED');self.assertNotEqual((root/'current').resolve(),release)

    def test_export_strips_dynamic_keeps_theme_and_optimizes(self):
        with fixture() as (root,origin,state,files):
            files['/index.html']=files['/index.html'].replace(b'</body>',b'<form method="post" action="/checkout"><input name="private"><button>Submit</button></form></body>')
            release,report=build(origin,root/'releases','Provádíme údržbu.','Kontakt: demo@example.invalid')
            html=(release/'index.html').read_text()
            self.assertNotIn('<form',html);self.assertNotIn('<input',html)
            self.assertNotIn('Objednat online',html)
            self.assertIn('/__fallback_assets/hero.webp',html);self.assertIn('fallback-contact',html)
            self.assertIn('Dobrá káva',html)
            self.assertLess(report['image_result_bytes'],report['image_source_bytes'])
            self.assertEqual(verify(release),report)
            publish(release,root/'current');self.assertEqual((root/'current').resolve(),release)
            (release/'assets/style.css').write_text('tampered')
            with self.assertRaises(ValueError):publish(release,root/'current')

    def test_active_markup_css_redirect_cookie_and_origin_rejection(self):
        with fixture() as (root,origin,state,files):
            files['/index.html']=files['/index.html'].replace(b'</body>',b'<script>fetch("/private")</script><img src="/private.jpg"></body>')
            with self.assertRaises(ValueError):build(origin,root/'releases','notice','contact')
            files['/index.html']=(ROOT/'demo/site/index.html').read_bytes()
            files['/style.css']=b'body{background:url(http://127.0.0.1/private)}'
            with self.assertRaises(ValueError):build(origin,root/'releases','notice','contact')
            files['/style.css']=(ROOT/'demo/site/style.css').read_bytes()
            state['cookie']=True
            with self.assertRaises(ValueError):build(origin,root/'releases','notice','contact')
            state['cookie']=False;state['redirect']=True
            with self.assertRaises(ValueError):build(origin,root/'releases','notice','contact')
        for origin in ('http://user:pass@host','http://host/path','file:///etc/passwd','http://host/#fragment'):
            with self.assertRaises(ValueError):origin_url(origin)

    def test_backup_restore_and_reject_tampering_traversal_overwrite(self):
        with fixture() as (root,origin,state,files):
            release,_=build(origin,root/'releases','notice','contact')
            archive=root/'backup.tgz';digest=create(release,archive)
            restored=restore(archive,root/'restored',digest)
            self.assertEqual(restored,verify(release))
            with self.assertRaises(FileExistsError):restore(archive,root/'restored',digest)
            with self.assertRaises(ValueError):restore(archive,root/'bad','0'*64)
            evil=root/'evil.tgz'
            with tarfile.open(evil,'w:gz') as tar:
                info=tarfile.TarInfo('../escape');info.size=1;tar.addfile(info,io.BytesIO(b'x'))
            with self.assertRaises(ValueError):restore(evil,root/'escape',hashlib.sha256(evil.read_bytes()).hexdigest())
            self.assertFalse((root/'escape').exists())

    def test_maintenance_windows_and_stable_recovery(self):
        with fixture() as (root,origin,state,files):
            atomic_json(root/'control.json',{'manual_maintenance':False,'windows':[{'start_utc':'2026-10-16T12:00:00Z','end_utc':'2026-10-16T13:00:00Z'}]})
            now=datetime(2026,10,16,12,30,tzinfo=timezone.utc)
            for _ in range(3):result=tick(origin,root,now)
            self.assertEqual(result['mode'],'MAINTENANCE');self.assertTrue((root/'maintenance').exists())
            state['healthy']=False
            result=tick(origin,root,datetime(2026,10,16,13,1,tzinfo=timezone.utc))
            self.assertEqual(result['mode'],'OVERRUN');self.assertTrue((root/'unhealthy').exists())
            state['healthy']=True
            for _ in range(2):self.assertEqual(tick(origin,root,datetime(2026,10,16,13,2,tzinfo=timezone.utc))['mode'],'OVERRUN')
            self.assertEqual(tick(origin,root,datetime(2026,10,16,13,2,tzinfo=timezone.utc))['mode'],'ONLINE')
            self.assertFalse((root/'unhealthy').exists())

    @unittest.skipUnless(shutil.which('nginx') and shutil.which('convert'),'Existing Nginx/ImageMagick required')
    def test_prefixed_public_route_and_unrelated_endpoint_isolation(self):
        with fixture() as (root,origin,state,files):
            release,_=build(origin,root/'releases','maintenance','contact',asset_prefix='/demo/__fallback_assets')
            publish(release,root/'current');listen=port()
            server=server_config(origin,root/'current',root/'unhealthy',root/'maintenance',f'127.0.0.1:{listen}',prefix='/demo')
            server=server.rsplit('}',1)[0]+'location = /unrelated { return 200 "independent"; }\n}\n'
            cfg=root/'nginx.conf';cfg.write_text(standalone_config(server,root))
            subprocess.run(['nginx','-t','-p',str(root)+'/', '-c',str(cfg)],check=True,capture_output=True)
            proc=subprocess.Popen(['nginx','-p',str(root)+'/', '-c',str(cfg),'-g','daemon off;'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            base=f'http://127.0.0.1:{listen}'
            try:
                for _ in range(50):
                    try:status,headers,body=get(base+'/demo/');break
                    except OSError:time.sleep(.05)
                self.assertEqual(status,200);self.assertIn(b'href="/demo/style.css"',body)
                self.assertIn(b'href="/demo/objednavka/"',body)
                self.assertNotIn(b'<form',body)
                self.assertEqual(get(base+'/demo/hero.jpg')[0],200)
                state['healthy']=False
                status,headers,body=get(base+'/demo/objednavka/')
                self.assertEqual(status,503);self.assertIn(b'/demo/__fallback_assets/hero.webp',body)
                self.assertEqual(get(base+'/demo/__fallback_assets/hero.webp')[0],200)
                self.assertEqual(get(base+'/demo/__fallback_assets/style.css')[0],200)
                self.assertEqual(get(base+'/unrelated')[2],b'independent')
                self.assertEqual(get(base+'/__standby_demo')[0],404)
                (root/'maintenance').touch();state['healthy']=True
                self.assertEqual(get(base+'/demo/',b'order=test')[0],503)
                self.assertEqual(state['posts'],0)
                self.assertEqual(get(base+'/unrelated')[2],b'independent')
            finally:proc.terminate();proc.wait(timeout=5)

    @unittest.skipUnless(shutil.which('nginx') and shutil.which('convert'),'Existing Nginx/ImageMagick required')
    def test_real_nginx_outage_maintenance_assets_and_controller_independence(self):
        with fixture() as (root,origin,state,files):
            release,_=build(origin,root/'releases','Probíhá údržba.','Kontakt: demo@example.invalid');publish(release,root/'current')
            listen=port();cfg=root/'nginx.conf'
            cfg.write_text(standalone_config(server_config(origin,root/'current',root/'unhealthy',root/'maintenance',f'127.0.0.1:{listen}'),root))
            subprocess.run(['nginx','-t','-p',str(root)+'/', '-c',str(cfg)],check=True,capture_output=True)
            proc=subprocess.Popen(['nginx','-p',str(root)+'/', '-c',str(cfg),'-g','daemon off;'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            try:
                for _ in range(50):
                    try:status,headers,body=get(f'http://127.0.0.1:{listen}/');break
                    except OSError:time.sleep(.05)
                self.assertEqual(status,200);self.assertEqual(headers['X-Fallback-Mode'],'online')
                state['healthy']=False
                status,headers,body=get(f'http://127.0.0.1:{listen}/')
                self.assertEqual(status,503);self.assertEqual(headers['X-Fallback-Mode'],'standby');self.assertIn(b'fallback-contact',body)
                self.assertEqual(get(f'http://127.0.0.1:{listen}/__fallback_assets/hero.webp')[0],200)
                self.assertEqual(get(f'http://127.0.0.1:{listen}/__fallback_assets/style.css')[0],200)
                state['healthy']=True;(root/'maintenance').touch()
                before=state['posts']
                self.assertEqual(get(f'http://127.0.0.1:{listen}/objednavka/',b'name=demo')[0],503)
                self.assertEqual(state['posts'],before)
                self.assertNotIn(b'<form',get(f'http://127.0.0.1:{listen}/')[2])
                (root/'maintenance').unlink();(root/'unhealthy').touch()
                self.assertEqual(get(f'http://127.0.0.1:{listen}/')[0],503)
                (root/'unhealthy').unlink()
                self.assertEqual(get(f'http://127.0.0.1:{listen}/')[0],200)
                # No PHP, controller, database or watcher process was started.
            finally:
                proc.terminate();proc.wait(timeout=5)


if __name__=='__main__':unittest.main()
