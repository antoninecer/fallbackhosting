#!/usr/bin/env python3
"""Operator-only bootstrap. Password stays on stdin/memory; never printed."""
import argparse
import getpass
import json
import os
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('command', choices=['bootstrap'])
parser.add_argument('--data-dir', type=Path, required=True)
parser.add_argument('--username', default='admin')
args = parser.parse_args()
if not sys.stdin.isatty():
    parser.error('Run in your private interactive terminal; no password arguments or environment variables.')
password = getpass.getpass('Nové heslo správce (nejméně 14 znaků): ')
if password != getpass.getpass('Heslo znovu: '):
    parser.error('Hesla se neshodují.')
if not args.data_dir.is_dir():
    parser.error('Private data directory must already exist with mode 0700 and correct owner.')
env = os.environ.copy()
env['FH_ADMIN_DATA'] = str(args.data_dir.resolve())
result = subprocess.run(['php', str(Path(__file__).resolve().parents[1] / 'admin/manage.php'), 'bootstrap'],
                        input=json.dumps({'username': args.username, 'password': password}), text=True, env=env)
raise SystemExit(result.returncode)
