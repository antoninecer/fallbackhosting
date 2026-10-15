#!/usr/bin/env python3
"""Record a reviewed public event after verified work; rebuild and check live view.
Evidence/next-step text stays in checkpoint/state, never exported as raw text.
"""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('portal',ROOT/'portal/build.py')
portal=importlib.util.module_from_spec(spec);spec.loader.exec_module(portal)
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('event',choices=portal.PUBLIC_EVENTS)
p.add_argument('--evidence',required=True)
p.add_argument('--next',required=True)
a=p.parse_args()
now=datetime.now(timezone.utc);utc=now.strftime('%Y-%m-%dT%H:%M:%SZ')
path=ROOT/'state/current.json';state=json.loads(path.read_text())
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
checkpoint=f"checkpoints/{now.strftime('%Y%m%dT%H%M%SZ')}-{state['task_id']}-{a.event.replace('_','-')}.md"
(ROOT/checkpoint).write_text(f'''# {Path(checkpoint).stem}
- UTC: {utc}; Codex; {state['milestone']}/{state['task_id']} {state['phase']}.
- Associated Git revision: {revision}; uncommitted changes must be inspected before resumption.
- Last verified action/results: {a.evidence}
- Files changed: state/current.json, this checkpoint and generated public artifact; inspect Git for source/docs changes.
- Infrastructure scope: approved ADMIN-ACTIVATION.md only; actual actions/results above. No home runtime changes.
- Open issues/unverified: independent fingerprint, external application baseline, full dependency/backup coverage, browser QA and certificate-renewal reload validation remain open.
- Next exact step: {a.next}
- Rollback: approved scoped activation rollback; preserve private journal/data/release/certificate/account. Interrupted phases require reconciliation.
- Required approvals: none within already approved activation/Git-push scope.
''')
state['last_checkpoint']=checkpoint
state['current_summary']=a.evidence
state['next_safe_action']=a.next
state.setdefault('public_events',[]).append({'id':a.event,'utc':utc})
path.write_text(json.dumps(state,indent=2)+'\n')
portal.build(ROOT/'public')
with urllib.request.urlopen('https://project.lab.ventureout.cz/',timeout=10) as response:
    content=response.read(1048576).decode()
    assert response.status == 200 and portal.PUBLIC_EVENTS[a.event] in content and Path(checkpoint).stem in content
print('PASS checkpoint/state/public event visible via verified HTTPS:',a.event)
