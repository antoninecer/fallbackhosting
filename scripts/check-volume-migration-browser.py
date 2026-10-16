#!/usr/bin/env python3
"""Exercise web-owned fixture create/move/write/reverse/restart; --live uses real nodes."""
from pathlib import Path
import argparse,json,os,socket,sys,threading,time
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from playwright.sync_api import sync_playwright,expect
p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');args=p.parse_args();checks=[]
out=ROOT/'.local/qa'/('volume-migration-live' if args.live else 'volume-migration-fixture');out.mkdir(mode=0o700,parents=True,exist_ok=True)
if args.live:
 creds=json.loads((ROOT/'.local/operator/initial-admin.json').read_text());base='https://lab.ventureout.cz'
else:
 import test_admin
 from test_node_onboarding import KEY
 from test_volume_migration import Driver
 from operations.node_onboarding import Onboarding
 from operations.volume_migration import VolumeMigration
 from operations.protocol import serve_connection
 app=test_admin.AdminTests();app.setUp();creds={'username':'admin','password':app.password};base=app.origin
 broker=Onboarding(app.data/'runtime',os.getuid(),'admin',KEY,lambda *a:None);broker.migration=VolumeMigration(app.data/'runtime/migration',{'ctx1':'ctx1','vasatkova':'vasatkova'},Driver())
 listener=socket.socket(socket.AF_UNIX);listener.bind(str(app.data/'onboarding.sock'));listener.listen(8);listener.settimeout(.1);stop=threading.Event()
 def serve():
  while not stop.is_set():
   try:c,_=listener.accept()
   except socket.timeout:continue
   serve_connection(c,broker)
 def advance():
  while not stop.wait(.05):broker.migration.advance()
 threads=[threading.Thread(target=serve),threading.Thread(target=advance)]
 for t in threads:t.start()
def mark(s):checks.append(s);print('PASS '+s,flush=True);(out/'report.json').write_text(json.dumps({'real_ssh_docker':args.live,'checks':checks},indent=2))
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch();ctx=browser.new_context(viewport={'width':1440,'height':900});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  assert ctx.request.get(base+'/?migration=1').status==401
  page.goto(base);page.locator('[name=username]').fill(creds['username']);page.locator('[name=password]').fill(creds['password']);page.get_by_role('button',name='Přihlásit se',exact=True).click();page.get_by_role('link',name='Přesun aplikací',exact=True).click()
  expect(page.get_by_role('heading',name='Vyberte server pro testovací aplikaci',exact=True)).to_be_visible()
  form=page.locator('form').filter(has=page.get_by_role('button',name='Prověřit cíl ctx1',exact=True));data={i.get_attribute('name'):i.get_attribute('value') for i in form.locator('input[type=hidden]').all()};data['confirmation']='1'
  assert ctx.request.post(base+'/?migration=1',form=dict(data,csrf='bad'),headers={'Origin':base}).status==403
  assert ctx.request.post(base+'/?migration=1',form=data,headers={'Origin':'https://invalid.example'}).status==403
  for width in (360,768,1440):
   page.set_viewport_size({'width':width,'height':900});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(out/f'select-{width}.png'),full_page=True)
  mark('auth CSRF Origin and first view3607681440')
  def step(button,heading):
   form=page.locator('form').filter(has=page.get_by_role('button',name=button,exact=True));form.get_by_role('checkbox').check();form.get_by_role('button',name=button,exact=True).click()
   for attempt in range(150):
    if page.get_by_role('heading',name=heading,exact=True).count():break
    if page.get_by_role('heading',name='Přesun vyžaduje kontrolu',exact=True).count():raise RuntimeError('RECONCILIATION_REQUIRED_AFTER_'+button)
    page.wait_for_timeout(2000 if args.live else 100);page.reload()
   expect(page.get_by_role('heading',name=heading,exact=True)).to_be_visible();mark(button)
  running='Aplikace běží a data jsou ověřená';ready='Kontrola cíle dokončena'
  step('Prověřit cíl ctx1',ready);expect(page.locator('main')).to_contain_text('Historické maximum')
  step('Vytvořit testovací aplikaci na ctx1',running)
  step('Prověřit cíl vasatkova',ready)
  step('Přesunout testovací aplikaci na vasatkova',running)
  step('Přidat testovací záznam',running)
  step('Ověřit data po restartu testovací aplikace',running)
  step('Prověřit cíl ctx1',ready)
  step('Přesunout testovací aplikaci na ctx1',running)
  step('Ověřit data po restartu testovací aplikace',running)
  expect(page.locator('main')).to_contain_text('ctx1 → vasatkova');expect(page.locator('main')).to_contain_text('vasatkova → ctx1')
  values=page.locator('dt').filter(has_text='Ověřená hodnota').locator('+ dd');expect(values).to_have_text('8')
  for width in (360,768,1440):
   page.set_viewport_size({'width':width,'height':900});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(out/f'roundtrip-{width}.png'),full_page=True)
  assert not errors;page.get_by_role('button',name='Odhlásit',exact=True).click();assert ctx.request.get(base+'/?migration=1').status==401
  mark('both directions counter8 DB/file persistence mobile tablet desktop logout');browser.close()
finally:
 if not args.live:
  stop.set()
  for t in threads:t.join(3)
  listener.close();broker.process_lock.close();app.tearDown()
