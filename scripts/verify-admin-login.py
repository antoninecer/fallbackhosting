#!/usr/bin/env python3
"""Operator-only auth smoke test; no credential/response output, inventory unmodified."""
import hashlib
import http.client
import json
from pathlib import Path
import re
from urllib.parse import urlencode
ROOT=Path('/opt/fallback')
credentials=json.loads((ROOT/'.local/operator/initial-admin.json').read_text())
# Hash-only check of actual inventory before/after; run as root for private runtime.
p=Path('/var/lib/fallback-web/admin/inventory.json')
before=hashlib.sha256(p.read_bytes()).digest()
cookie=''
def request(data=None):
    global cookie
    connection=http.client.HTTPSConnection('lab.ventureout.cz',timeout=10)
    headers={'Cookie':cookie} if cookie else {}
    if data is not None:
        headers.update({'Origin':'https://lab.ventureout.cz','Content-Type':'application/x-www-form-urlencoded'})
    connection.request('POST' if data is not None else 'GET','/',body=urlencode(data) if data is not None else None,headers=headers)
    response=connection.getresponse();body=response.read(1048576).decode();status=response.status
    flags=response.getheader('Set-Cookie','')
    if flags:cookie=flags.split(';',1)[0]
    connection.close()
    return status,body,flags
status,body,flags=request()
assert status==200 and 'name="password"' in body and 'ctx1' not in body
assert all(flag in flags.lower() for flag in ['secure','httponly','samesite=strict'])
csrf=re.search(r'name="csrf" value="([a-f0-9]+)"',body)[1]
old=cookie
status,_,_=request({'action':'login','csrf':csrf,'username':credentials['username'],'password':credentials['password']})
assert status==303 and old!=cookie
status,body,_=request();assert status==200 and 'ctx1' in body and 'docker' in body
csrf=re.search(r'name="csrf" value="([a-f0-9]+)"',body)[1]
assert request({'action':'logout','csrf':csrf})[0]==303
assert 'ctx1' not in request()[1]
assert hashlib.sha256(p.read_bytes()).digest()==before
print('PASS real admin HTTPS login, rotated secure session, ctx1 Docker inventory, logout; inventory unchanged')
