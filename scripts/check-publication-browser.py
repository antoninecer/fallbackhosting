#!/usr/bin/env python3
"""Disposable authenticated publication browser workflow, no production/SSH calls."""
import json
import os
from pathlib import Path
import socket
import sys
import threading
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
import test_admin
from test_standby import fixture
from test_standby_publishing import PublishingTests
from operations.protocol import serve_connection
from standby.control import Control
from standby.publish_service import PublicationAPI

out=ROOT/'.local/qa/publication';out.mkdir(parents=True,exist_ok=True)
checks=[]
with fixture() as (root,origin,*_), sync_playwright() as pw:
    browser=pw.chromium.launch()
    flow,old=PublishingTests().workflow(root,origin)
    os.environ['FH_STANDBY_RELEASES']=str(flow.public/'releases')
    app=test_admin.AdminTests();app.setUp();os.environ.pop('FH_STANDBY_RELEASES')
    stop=threading.Event();listeners=[];threads=[]
    for name,api in [('standby',Control(app.data/'runtime',os.getuid(),'admin')),('publication',PublicationAPI(flow,os.getuid(),'admin'))]:
        listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);listener.bind(str(app.data/(name+'.sock')));listener.listen(8);listener.settimeout(.1);listeners.append(listener)
        def serve(listener=listener,api=api):
            while not stop.is_set():
                try:connection,_=listener.accept()
                except socket.timeout:continue
                serve_connection(connection,api)
        thread=threading.Thread(target=serve);thread.start();threads.append(thread)
    def worker():
        while not stop.wait(.05):flow.advance()
    thread=threading.Thread(target=worker);thread.start();threads.append(thread)
    try:
        for width in (360,768,1440):
            context=browser.new_context(viewport={'width':width,'height':900});page=context.new_page()
            page.goto(app.origin);page.locator('[name=username]').fill('admin');page.locator('[name=password]').fill(app.password);page.get_by_role('button',name='Přihlásit se',exact=True).click()
            page.goto(app.origin+'/?standby=1');page.get_by_role('button',name='Připravit novou verzi',exact=True).click()
            for _ in range(60):
                if flow.view()['phase'] not in ('PREPARING',):break
                page.wait_for_timeout(200)
            assert flow.view()['phase']=='READY',flow.view()
            page.reload();expect(page.get_by_role('button',name='Publikovat připravenou verzi',exact=True)).to_be_visible()
            assert flow.current()==old.name
            with page.expect_popup() as popup:
                page.get_by_role('link',name='Prohlédnout záložní verzi ↗',exact=True).click()
            preview=popup.value;preview.wait_for_load_state('networkidle')
            expect(preview.get_by_role('heading',name='Kontakt během údržby',exact=True)).to_be_visible()
            assert preview.locator('form,script,input').count()==0
            assert preview.locator('img').evaluate('(e)=>e.complete && e.naturalWidth>0')
            assert preview.evaluate('document.styleSheets.length')==1
            preview.screenshot(path=str(out/f'preview-{width}.png'),full_page=True);preview.close()
            page.get_by_role('button',name='Publikovat připravenou verzi',exact=True).click()
            for _ in range(40):
                if flow.view()['phase']=='PUBLISHED':break
                page.wait_for_timeout(100)
            assert flow.view()['phase']=='PUBLISHED'
            page.reload();page.get_by_role('button',name='Vrátit předchozí verzi',exact=True).click()
            for _ in range(40):
                if flow.view()['phase']=='ROLLED_BACK':break
                page.wait_for_timeout(100)
            assert flow.current()==old.name
            page.reload();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            page.screenshot(path=str(out/f'controls-{width}.png'),full_page=True)
            candidate=flow.view()['candidate'];page.get_by_role('button',name='Odhlásit',exact=True).click()
            assert context.request.get(app.origin+'/?publication-preview='+candidate).status==401
            context.close();checks.append({'width':width,'prepare_preview_publish_rollback':'PASS','preview_assets':'PASS','logout_denial':'PASS'})
    finally:
        browser.close();stop.set()
        for thread in threads:thread.join(5)
        for listener in listeners:listener.close()
        app.tearDown()
print(json.dumps({'publication_browser':checks,'production_changes':False}))
