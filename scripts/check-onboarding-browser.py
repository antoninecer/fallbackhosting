#!/usr/bin/env python3
"""Disposable node wizard/browser/Unix-worker test. No SSH or package changes."""
from pathlib import Path
import json,os,socket,sys,threading
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
import test_admin
from test_node_onboarding import SPEC,KEY,FACTS
from operations.node_onboarding import Onboarding
from operations.protocol import serve_connection
out=ROOT/'.local/qa/onboarding';out.mkdir(parents=True,exist_ok=True);checks=[]
with sync_playwright() as p:
 b=p.chromium.launch()
 for width in (360,768,1440):
  app=test_admin.AdminTests();app.setUp();stop=threading.Event();calls=[]
  def driver(spec,action):
   calls.append(action);return dict(FACTS,**({'docker_cli':True,'docker_ready':True,'docker_version':'fixture-docker','compose_version':'fixture-compose'} if action=='prepare' else {}))
  api=Onboarding(app.data/'runtime',os.getuid(),'admin',KEY,driver);listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);listener.bind(str(app.data/'onboarding.sock'));listener.listen(8);listener.settimeout(.1)
  def serve():
   while not stop.is_set():
    try:connection,_=listener.accept()
    except socket.timeout:continue
    serve_connection(connection,api)
  def work():
   while not stop.wait(.05):api.advance()
  threads=[threading.Thread(target=serve),threading.Thread(target=work)]
  for t in threads:t.start()
  try:
   ctx=b.new_context(viewport={'width':width,'height':900});page=ctx.new_page();page.goto(app.origin);page.locator('[name=username]').fill('admin');page.locator('[name=password]').fill(app.password);page.get_by_role('button',name='Přihlásit se',exact=True).click()
   page.get_by_role('link',name='+ Přidat server',exact=True).click();expect(page.get_by_role('heading',name='Přidat server',exact=True)).to_be_visible()
   expect(page.get_by_role('textbox',name='Veřejný SSH klíč',exact=True)).to_have_value(KEY)
   for name,value in dict(id=SPEC['id'],name='Fixture VM',host=SPEC['host'],ssh_port='22',ssh_user=SPEC['ssh_user'],host_fingerprint=SPEC['fingerprint']).items():page.locator('input[name='+name+']').fill(value)
   page.get_by_role('button',name='Ověřit připojení',exact=True).click()
   for _ in range(30):
    if api.view(SPEC['id'])['phase']=='READY':break
    page.wait_for_timeout(100)
   page.reload();expect(page.get_by_role('heading',name='Chcete server inicializovat?',exact=True)).to_be_visible();assert calls==['inspect']
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path=str(out/f'confirm-{width}.png'),full_page=True)
   page.get_by_role('checkbox',name='Chci automaticky připravit tento server.',exact=True).check();page.get_by_role('button',name='Inicializovat server',exact=True).click()
   for _ in range(30):
    if api.view(SPEC['id'])['phase']=='SUCCEEDED':break
    page.wait_for_timeout(100)
   page.reload();expect(page.get_by_role('heading',name='Server je připravený',exact=True)).to_be_visible();assert calls==['inspect','prepare']
   page.get_by_role('button',name='Dokončit a uložit ověření',exact=True).click()
   expect(page.get_by_role('heading',name='Fixture VM',exact=True)).to_be_visible();assert next(n for n in app.inventory()['servers'] if n['id']==SPEC['id'])['observations']['docker']['status']=='PASS'
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.get_by_role('button',name='Odhlásit',exact=True).click();assert ctx.request.get(app.origin+'/?onboard=1').status==401
   ctx.close();checks.append({'width':width,'access_check_explicit_confirmation_initialization_inventory_logout':'PASS'})
  finally:
   stop.set()
   for t in threads:t.join(3)
   listener.close();api.process_lock.close();app.tearDown()
 b.close()
print(json.dumps({'onboarding_browser':checks,'real_ssh_or_initialization':False}))
