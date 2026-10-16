#!/usr/bin/env python3
"""Disposable browser/queue trial. Never connects to SSH or live Docker."""
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from operations.install_worker import run_one
spec=importlib.util.spec_from_file_location('admin_fixture',ROOT/'tests/test_admin.py')
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
out=ROOT/'.local/qa'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-install-wizard')
out.mkdir(parents=True,exist_ok=True)
checks=[]
with sync_playwright() as playwright:
    browser=playwright.chromium.launch()
    for width in (360,768,1440):
        app=fixture.AdminTests();app.setUp()
        try:
            inventory=app.inventory();inventory['servers'][0]['observations']['fingerprint']={'status':'PASS'}
            (app.data/'inventory.json').write_text(json.dumps(inventory))
            (app.data/'install-worker.json').write_text(json.dumps(dict(utc=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),node='ctx-test',template='coolify-4.4.6',ready=True)))
            context=browser.new_context(viewport={'width':width,'height':900});page=context.new_page();errors=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(app.origin)
            page.get_by_role('textbox',name='Uživatelské jméno').fill('admin')
            page.locator('[name=password]').fill(app.password)
            page.get_by_role('button',name='Přihlásit se',exact=True).click()
            page.get_by_role('link',name='Aplikace',exact=True).click()
            page.locator('select[name=node]').select_option('ctx-test')
            page.get_by_role('button',name='Pokračovat na Coolify a nápovědu').click()
            expect(page.get_by_role('heading',name='Účet prvního správce')).to_be_visible()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(out/f'review-{width}.png'),full_page=True)
            page.locator('[name=email]').fill('operator@example.org')
            page.locator('[name=password]').fill('Browser-Trial8!Secret')
            page.locator('[name=password_confirmation]').fill('Browser-Trial8!Secret')
            page.locator('[name=confirmation]').check()
            page.get_by_role('button',name='Nainstalovat Coolify',exact=True).click()
            expect(page.get_by_role('heading',name='Čeká na převzetí',exact=True)).to_be_visible()
            ident=next((app.data/'install-requests').glob('*.request.json')).name.removesuffix('.request.json')
            ledger=app.data/'fixture-ledger';ledger.mkdir()
            assert run_one(app.data/'install-requests',ledger,dict(node='ctx-test',actor='admin'),lambda secret:dict(healthy_services=3,admin_created=True,registration_disabled=True,unrelated_unchanged=True),ident,os.getuid())=='SUCCEEDED'
            page.reload()
            expect(page.get_by_role('heading',name='Instalace dokončena',exact=True)).to_be_visible()
            assert 'Browser-Trial8!Secret' not in page.content()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(out/f'result-{width}.png'),full_page=True)
            page.get_by_role('button',name='Odhlásit',exact=True).click()
            assert context.request.get(app.origin+'/?install=1').status==401
            assert not errors
            checks.append(dict(width=width,wizard='PASS',queued_fixture='PASS',result='PASS',logout='PASS',overflow=False))
            context.close()
        finally:app.tearDown()
    browser.close()
print(json.dumps({'checks':checks,'real_docker_changes':False,'screenshots':'PRIVATE_LOCAL_QA'}))
