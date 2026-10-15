#!/usr/bin/env python3
"""Private multi-node PHP/RPC fixture page and loopback browser verification."""
from datetime import datetime,timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import sys
import threading
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'tests'))
import test_php_operations

out=ROOT/'.local/qa'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-operations')
web=out/'fixture-page';web.mkdir(parents=True)
fixture=test_php_operations.PHPIntegrationTests(methodName='test_php_fixture_full_lifecycle_and_scoped_history')
fixture.setUp();release_event=threading.Event();running_event=threading.Event();worker=None
try:
    f=fixture.fixture
    f.policy['apps']['app-two']={'node':'node-two','project':'project-one','template':'demo'}
    def request(action,app='app-one',node='node-one',params=None):
        r=f.request(action,params);r.update(app=app,node=node)
        r['authorization']=f.auth.issue({'principal':'alice','peer_uid':f.uid,'project':'project-one','node':node,'actions':sorted(test_php_operations.test_operations.ACTIONS),'expires':1100})
        if action in test_php_operations.test_operations.WRITES:f.approve(r)
        return r
    def view(app,node):
        r=request('inspect',app,node);packet={k:r[k] for k in ('request_id','node','project','app','authorization')};packet['kind']='view'
        return fixture.call(packet)
    assert fixture.call(request('deploy'))['state']=='SUCCEEDED'
    assert fixture.call(request('start'))['state']=='SUCCEEDED'
    assert fixture.call(request('remove',params={'confirm_container':f.unrelated}))['state']=='FAILED'
    assert fixture.call(request('deploy','app-two','node-two'))['state']=='SUCCEEDED'
    f.driver.fail=TimeoutError('fixture timeout')
    assert fixture.call(request('start','app-two','node-two'))['state']=='UNKNOWN'
    f.driver.fail=None
    original=f.driver.execute
    def paused(node,action,params,**limits):
        if action=='restart':running_event.set();release_event.wait(timeout=10)
        return original(node,action,params,**limits)
    f.driver.execute=paused
    packet=request('restart');result=[]
    worker=threading.Thread(target=lambda:result.append(fixture.call(packet)))
    worker.start();assert running_event.wait(timeout=5)
    views=[view('app-one','node-one'),view('app-two','node-two')]
    assert any(j['state']=='RUNNING' for j in views[0]['jobs'])
    assert any(j['state']=='UNKNOWN' for j in views[1]['jobs'])
    html=fixture.render(views);assert html.returncode==0
    assert 'authorization' not in html.stdout and 'APPROVAL' not in html.stdout
    (web/'index.html').write_text(html.stdout)
    for name in ('admin.css','operations.css'):
        source=ROOT/'admin/public/admin.css' if name=='admin.css' else ROOT/'admin/operations.css'
        shutil.copyfile(source,web/name)
    release_event.set();worker.join(timeout=5);assert not worker.is_alive();assert result[0]['state']=='SUCCEEDED'
finally:
    release_event.set()
    if worker:worker.join(timeout=12)
    fixture.tearDown()

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(web)))
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
origin=f'http://127.0.0.1:{server.server_port}';checks=[]
try:
    with sync_playwright() as p:
        browser=p.chromium.launch()
        for width in (360,768,1440):
            page=browser.new_page(viewport={'width':width,'height':900});errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            assert page.goto(origin,wait_until='networkidle').status==200
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            assert page.locator('.node').count()==2
            text=page.locator('body').inner_text()
            for value in ('node-one','node-two','app-one','app-two','Probíhá','Výsledek nejasný','Selhalo','Audit operací','neověřená','uložený výsledek'):
                assert value in text,value
            assert 'PRIVATE' not in text and 'authorization' not in text
            if width==360:
                assert page.locator('td[data-label]').first.evaluate('(e)=>getComputedStyle(e).display')=='block'
            page.screenshot(path=str(out/f'operations-{width}-top.png'))
            page.screenshot(path=str(out/f'operations-{width}-full.png'),full_page=True)
            assert not errors
            checks.append({'width':width,'status':'PASS','scoped_nodes':2,'actual_transient_job_snapshot':True,'unknown_not_live_health':True,'page_overflow':False,'javascript_errors':0})
            page.close()
        browser.close()
finally:
    server.shutdown();server.server_close();thread.join(timeout=5)
report={'verified_at_utc':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'checks':checks,'php_rpc_fixture':True,'listeners_stopped':True,'real_docker_operations':False}
(out/'operations-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2));print('Private screenshots/report:',out.relative_to(ROOT))
