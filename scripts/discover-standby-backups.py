#!/usr/bin/env python3
"""Read-only fixed repository discovery and optional nonexecuting restore preview."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from standby.transport import fixed_script
from standby.recovery import plan

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inventory',type=Path,required=True);p.add_argument('--node',required=True);p.add_argument('--select');p.add_argument('--destination',type=Path);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
if bool(args.select)!=bool(args.destination):p.error('Selection and new destination must be provided together')
node=next(n for n in json.loads(args.inventory.read_text())['servers'] if n['id']==args.node and n['enabled'])
if node['observations']['fingerprint']['status']!='PASS':raise ValueError('Verified host identity required')
result=fixed_script(ROOT/'operations/standby_backup.py',{'action':'list'},node)
if args.select:result=plan(result,args.select,args.destination)
with args.output.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
args.output.chmod(0o600)
print(json.dumps({'discovery':'PASS_READ_ONLY','catalog_entries':len(result.get('backups',[])),'preview':bool(args.select),'output':'PRIVATE_OPERATOR_FILE','restore_executed':False}))
