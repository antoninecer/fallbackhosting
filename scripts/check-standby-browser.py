#!/usr/bin/env python3
"""Actual PHP/Unix-control browser fixture; no production service/SSH calls."""
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import socket
import sys
import threading
import time
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
import test_admin
from test_standby import fixture
from standby.control import Control,run_server

out=ROOT/'.local/qa/standby-control';out.mkdir(parents=True,exist_ok=True)
checks=[]
with fixture() as (tmp,origin,state,files), sync_playwright() as pw:
    browser=pw.chromium.launch()
    for width in (360,768,1440):
        app=test_admin.AdminTests();app.setUp()
        listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);listener.bind(str(app.data/'standby.sock'));listener.listen(8)
        control=Control(app.data/'runtime',os.getuid(),'admin',{'release':'local-fixture','remote_backup':'VERIFIED_READBACK_RESTORE'})
        worker=threading.Thread(target=run_server,args=(listener,control,origin,15),daemon=True);worker.start()
        try:
            context=browser.new_context(viewport={'width':width,'height':900});page=context.new_page()
            page.goto(app.origin);page.locator('[name=username]').fill('admin');page.locator('[name=password]').fill(app.password)
            page.get_by_role('button',name='Přihlásit se',exact=True).click()
            page.get_by_role('link',name='Dostupnost a údržba',exact=True).click()
            expect(page.get_by_role('heading',name='Živý web, záložní verze a údržba',exact=True)).to_be_visible()
            page.get_by_role('button',name='Zapnout údržbu',exact=True).click()
            assert (control.runtime/'maintenance').exists()
            page.get_by_role('button',name='Automatický režim',exact=True).click()
            assert not (control.runtime/'maintenance').exists()
            start=datetime.now(ZoneInfo('Europe/Prague'))+timedelta(hours=1)
            page.locator('[name=start]').fill(start.strftime('%Y-%m-%dT%H:%M'))
            page.locator('[name=end]').fill((start+timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'))
            page.get_by_role('button',name='Uložit interval',exact=True).click()
            expect(page.get_by_role('textbox',name='Oznámení pro zákazníky')).to_be_visible()
            assert control.view()['control']['windows']
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=str(out/f'control-{width}.png'),full_page=True)
            page.get_by_role('button',name='Zrušit interval',exact=True).click()
            assert not control.view()['control']['windows']
            page.get_by_role('button',name='Odhlásit',exact=True).click()
            assert context.request.get(app.origin+'/?standby=1').status==401
            context.close();checks.append({'width':width,'authenticated_mode_changes':'PASS','schedule_and_announcement':'PASS','logout_denial':'PASS','overflow':False})
        finally:
            worker.join(18);listener.close();app.tearDown()
    browser.close()
print(json.dumps({'control_browser':checks,'real_infrastructure_changes':False,'screenshots':'PRIVATE_LOCAL_QA'}))
