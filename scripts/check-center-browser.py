#!/usr/bin/env python3
"""Loopback-only browser QA for the local static control-center artifact."""
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('center_qa', ROOT / 'center/build.py')
center = importlib.util.module_from_spec(spec)
spec.loader.exec_module(center)
release = center.build()
output = ROOT / '.local/qa' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-center')
output.mkdir(parents=True,exist_ok=True)
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server = ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(release)))
thread = Thread(target=server.serve_forever,daemon=True)
thread.start()
origin = f'http://127.0.0.1:{server.server_port}'
checks=[]
try:
    with sync_playwright() as p:
        browser=p.chromium.launch()
        for width in (360,768,1440):
            context=browser.new_context(viewport={'width':width,'height':900},permissions=['clipboard-read','clipboard-write'],accept_downloads=True)
            page=context.new_page()
            errors=[];requests=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.on('request',lambda request:requests.append(request.url))
            assert page.goto(origin,wait_until='networkidle').status==200
            page.keyboard.press('Tab')
            assert page.locator('.skip').evaluate('(e)=>document.activeElement===e')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            for section in ('prehled','ukoly','milniky','incidenty','zdravi','agent','postupy','navazani'):
                assert page.locator('#'+section).count()==1
            for option in ('DONE','ACTIVE','BLOCKED','READY','ALL'):
                page.locator('#task-filter').select_option(option)
                expected=page.locator('.task').evaluate_all("(items,o)=>items.filter(t=>o==='ALL'||t.dataset.status===o||(o==='ACTIVE'&&['IN_PROGRESS','TESTING'].includes(t.dataset.status))).length",option)
                assert page.locator('.task:visible').count()==expected
            summary=page.locator('.task details summary').first
            summary.focus();page.keyboard.press('Enter')
            assert page.locator('.task details').first.get_attribute('open') is not None
            page.locator('#copy-resume').click()
            expect(page.locator("#copy-result")).to_contain_text("zkopírován")
            assert page.evaluate('navigator.clipboard.readText()')==page.locator('#resume-prompt').input_value()
            with page.expect_download() as download:
                page.get_by_role('link',name='Stáhnout TXT').click()
            assert Path(download.value.path()).read_text()==(release/'resume.txt').read_text()
            # Long Czech text remains contained without document-wide overflow.
            page.locator('.task p').nth(1).evaluate("(e)=>e.textContent='Dlouhýčeskýtextbezmezery'.repeat(150)")
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.reload(wait_until='networkidle')
            page.evaluate('scrollTo(0,0)')
            page.screenshot(path=str(output/f'center-{width}-top.png'))
            page.screenshot(path=str(output/f'center-{width}-full.png'),full_page=True)
            assert not errors
            assert all(url.startswith(origin+'/') for url in requests), 'External resource dependency'
            checks.append({'width':width,'status':'PASS','modules':8,'filters':5,'clipboard_and_download':'PASS','keyboard':'PASS','long_text':'PASS','external_requests':0,'javascript_errors':0})
            context.close()
        browser.close()
finally:
    server.shutdown();server.server_close();thread.join(timeout=5)
report={'verified_at_utc':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'local_release':release.name,'checks':checks,'loopback_server_stopped':True}
(output/'center-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
print('Private screenshots/report:',output.relative_to(ROOT))
