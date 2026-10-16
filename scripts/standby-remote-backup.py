#!/usr/bin/env python3
"""Copy one verified static release to approved node, read back and restore-test."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from standby.backup import restore
from standby.transport import fixed_script

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--inventory',type=Path,required=True)
p.add_argument('--node',required=True)
p.add_argument('--archive',type=Path,required=True)
p.add_argument('--readback',type=Path,required=True)
p.add_argument('--restore-to',type=Path,required=True)
p.add_argument('--execute-owned-backup',action='store_true')
args=p.parse_args()
if not args.execute_owned_backup:p.error('--execute-owned-backup required')
node=next(n for n in json.loads(args.inventory.read_text())['servers'] if n['id']==args.node and n['enabled'])
if node['observations']['fingerprint']['status']!='PASS':raise ValueError('Verified SSH identity required')
body=args.archive.read_bytes();digest=hashlib.sha256(body).hexdigest()
if len(body)>32*1024*1024:raise ValueError('Bounded archive required')
source=ROOT/'operations/standby_backup.py'
result=fixed_script(source,{'action':'put','sha256':digest,'archive':base64.b64encode(body).decode()},node)
assert result['stored'] and result['sha256']==digest
result=fixed_script(source,{'action':'get','sha256':digest},node)
readback=base64.b64decode(result.pop('archive'),validate=True)
assert hashlib.sha256(readback).hexdigest()==digest
with args.readback.open('xb') as stream:stream.write(readback)
args.readback.chmod(0o600)
restored=restore(args.readback,args.restore_to,digest)
report={'remote_copy':'VERIFIED','remote_readback':'VERIFIED','isolated_restore':'PASS','sha256':digest,'bytes':len(body),'release':restored['release'],'scope':'STATIC_DEMO_RELEASE_ONLY'}
print(json.dumps(report))
