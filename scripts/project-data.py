#!/usr/bin/env python3
"""Validate canonical records or regenerate their Markdown tables; local only."""
import argparse
import json
import importlib.util
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('project_model', ROOT / 'portal/model.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('command', choices=('check', 'sync'))
args = parser.parse_args()
catalog = model.load(ROOT)
baseline = subprocess.run(['git', 'show', 'HEAD:state/catalog.json'], cwd=ROOT, capture_output=True, text=True)
if baseline.returncode == 0:
    model.validate_change(json.loads(baseline.stdout), catalog)
for item in catalog['milestones'] + catalog['tasks']:
    if item['completion_revision']:
        subprocess.run(['git', 'cat-file', '-e', item['completion_revision'] + '^{commit}'], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
model.sync_markdown(ROOT, catalog, write=args.command == 'sync')
print(f"PASS canonical catalog: {len(catalog['milestones'])} milestones, {len(catalog['tasks'])} tasks; evidence/revisions/tables validated")
