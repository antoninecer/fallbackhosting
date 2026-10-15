#!/usr/bin/env python3
"""Browser auth integration using disposable PHP auth/inventory; no live credentials."""
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
from unittest.mock import patch
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
center=module('center_auth_build',ROOT/'center/build.py')
admin_tests=module('disposable_admin_tests',ROOT/'tests/test_admin.py')
release=center.build(delivery='admin-query')
output=ROOT/'.local/qa'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-center-auth')
output.mkdir(parents=True,exist_ok=True)
app=admin_tests.AdminTests(methodName='test_auth_boundary_cookie_logout_and_setup_closed')
checks=[]
with patch.dict(os.environ,{'FH_CENTER_ARTIFACT':str(release)}):
    app.setUp()
try:
    before=(app.data/'inventory.json').read_bytes()
    with sync_playwright() as p:
        browser=p.chromium.launch()
        for width in (360,768,1440):
            context=browser.new_context(viewport={'width':width,'height':900},accept_downloads=True,permissions=['clipboard-read','clipboard-write'])
            page=context.new_page();errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            assert context.request.get(app.origin+'/?center=resume.txt').status==401
            page.goto(app.origin,wait_until='networkidle')
            page.get_by_role('textbox',name='Uživatelské jméno').fill('admin')
            page.locator('input[name=password]').fill(app.password)
            post_origins=[]
            def inspect_login(request):
                if request.method == 'POST':
                    post_origins.append(request.all_headers().get('origin')==app.origin)
            page.on('request',inspect_login)
            page.get_by_role('button',name='Přihlásit se').click()
            expect(page.get_by_role('link',name='Řídicí centrum')).to_be_visible()
            page.get_by_role('link',name='Řídicí centrum').click()
            expect(page.get_by_role('heading',name='Co je hotové. Co ověřit dál.')).to_be_visible()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            for asset in ('index.html','center.css','center.js','resume.txt','manifest.json'):
                assert context.request.get(app.origin+'/?center='+asset).status==200
            page.locator('#task-filter').select_option('DONE')
            assert page.locator('.task:visible').count()>0
            page.locator('#copy-resume').click()
            expect(page.locator('#copy-result')).to_contain_text('zkopírován')
            assert page.evaluate('navigator.clipboard.readText()')==page.locator('#resume-prompt').input_value()
            with page.expect_download() as download:
                page.get_by_role('link',name='Stáhnout TXT').click()
            assert Path(download.value.path()).read_text()==(release/'resume.txt').read_text()
            page.evaluate('scrollTo(0,0)')
            page.screenshot(path=str(output/f'protected-center-{width}.png'))
            page.get_by_role('link',name='Správa serverů').click()
            page.get_by_role('button',name='Odhlásit',exact=True).click()
            expect(page.get_by_role('button',name='Přihlásit se')).to_be_visible()
            for asset in ('index.html','center.css','center.js','resume.txt','manifest.json'):
                assert context.request.get(app.origin+'/?center='+asset).status==401
            assert not errors
            assert post_origins and all(post_origins), 'Browser POST Origin must match configured origin'
            checks.append({'width':width,'status':'PASS','session_asset_gate':'PASS','login_and_logout':'PASS','clipboard_and_download':'PASS','page_overflow':False,'javascript_errors':0})
            context.close()
        browser.close()
    assert (app.data/'inventory.json').read_bytes()==before
finally:
    app.tearDown()
report={'verified_at_utc':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'local_release':release.name,'checks':checks,'disposable_inventory_unchanged':True,'test_server_stopped':True}
(output/'center-auth-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
print('Private screenshots/report:',output.relative_to(ROOT))
