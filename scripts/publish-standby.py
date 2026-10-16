#!/usr/bin/env python3
"""Operator-approved composition: export, remote backup/readback/restore, publish."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from standby.backup import restore
from standby.publication import publish_with_backup
from standby.transport import fixed_script

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);p.add_argument('--inventory',type=Path,required=True);p.add_argument('--backup-node',required=True);p.add_argument('--execute-approved-publication',action='store_true');args=p.parse_args()
if not args.execute_approved_publication:p.error('--execute-approved-publication required')
config=json.loads(args.config.read_text())
node=next(n for n in json.loads(args.inventory.read_text())['servers'] if n['id']==args.backup_node and n['enabled'])
if node['observations']['fingerprint']['status']!='PASS':raise ValueError('Verified identity required')
def backup_provider(release,archive,digest):
    source=ROOT/'operations/standby_backup.py';body=archive.read_bytes()
    saved=fixed_script(source,{'action':'put','sha256':digest,'archive':base64.b64encode(body).decode()},node)
    assert saved['stored'] and saved['sha256']==digest
    result=fixed_script(source,{'action':'get','sha256':digest},node);readback=base64.b64decode(result['archive'],validate=True)
    assert hashlib.sha256(readback).hexdigest()==digest
    returned=archive.with_suffix('.readback.tgz')
    with returned.open('xb') as stream:stream.write(readback)
    returned.chmod(0o600)
    restore(returned,archive.parent/(release.name+'-restore'),digest)
    fixed_script(source,{'action':'mark_restore_tested','sha256':digest},node)
    return {'remote_copy':'VERIFIED','remote_readback':'VERIFIED','isolated_restore':'PASS','sha256':digest}
print(json.dumps(publish_with_backup(config,backup_provider)))
