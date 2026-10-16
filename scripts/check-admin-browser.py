#!/usr/bin/env python3
"""Disposable browser tests for multi-node inventory, no live/remote mutation."""
import json
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tests'))
import test_admin
out=ROOT/'.local/qa/admin-inventory';out.mkdir(parents=True,exist_ok=True)
checks=[]
with sync_playwright() as p:
    browser=p.chromium.launch()
    try:
        for width in (360,768,1440):
            app=test_admin.AdminTests();app.setUp()
            try:
                context=browser.new_context(viewport={'width':width,'height':900});page=context.new_page()
                page.goto(app.origin);page.locator('[name=username]').fill('admin');page.locator('[name=password]').fill(app.password);page.get_by_role('button',name='Přihlásit se',exact=True).click()
                for name,value in {'id':'fixture-two','name':'Second fixture','host':'192.0.2.20','ssh_port':'22','ssh_user':'service','credential_ref':'fixture-only','description':'Fixture create'}.items():
                    page.locator('#server-form [name='+name+']').fill(value)
                page.locator('[name=platform]').select_option('vm');page.get_by_role('button',name='Uložit konfiguraci',exact=True).click()
                expect(page.get_by_role('heading',name='Second fixture',exact=True)).to_be_visible()
                inventory=json.loads((app.data/'inventory.json').read_text());assert len(inventory['servers'])==2
                page.goto(app.origin+'/?edit=fixture-two#server-form');assert page.locator('[name=id]').get_attribute('readonly') is not None
                page.locator('[name=description]').fill('Fixture edited');page.locator('[name=enabled]').uncheck();page.get_by_role('button',name='Uložit konfiguraci',exact=True).click()
                node=next(n for n in json.loads((app.data/'inventory.json').read_text())['servers'] if n['id']=='fixture-two')
                assert node['description']=='Fixture edited' and node['enabled'] is False and node['observations']['fingerprint']['status']=='NEEDS_TEST'
                expect(page.get_by_text('Fixture edited',exact=True)).to_be_visible();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                page.screenshot(path=str(out/f'inventory-{width}.png'),full_page=True)
                page.get_by_role('button',name='Odhlásit',exact=True).click();expect(page.get_by_role('button',name='Přihlásit se',exact=True)).to_be_visible()
                context.close();checks.append({'width':width,'login_create_second_node_edit_disable_logout':'PASS','overflow':False})
            finally:app.tearDown()
    finally:browser.close()
print(json.dumps({'disposable_inventory_browser':checks,'production_inventory_changes':False}))
