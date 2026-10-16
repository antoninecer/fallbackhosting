#!/usr/bin/env python3
"""Operator CLI for the minimum standby slice; no shared service changes."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from standby.snapshot import build, publish, verify
from standby.gateway import atomic_json, tick, server_config, standalone_config, maintenance_active
from standby.backup import create, restore


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    export = sub.add_parser('export'); export.add_argument('--origin', required=True); export.add_argument('--store', type=Path, required=True)
    export.add_argument('--message', required=True); export.add_argument('--contact', required=True)
    activate = sub.add_parser('publish'); activate.add_argument('release', type=Path); activate.add_argument('--current', type=Path, required=True)
    backup = sub.add_parser('backup'); backup.add_argument('release', type=Path); backup.add_argument('archive', type=Path)
    recover = sub.add_parser('restore'); recover.add_argument('archive', type=Path); recover.add_argument('destination', type=Path); recover.add_argument('--sha256', required=True)
    config = sub.add_parser('config'); config.add_argument('--origin', required=True); config.add_argument('--store', type=Path, required=True); config.add_argument('--listen', default='127.0.0.1:18081')
    watch = sub.add_parser('watch'); watch.add_argument('--origin', required=True); watch.add_argument('--store', type=Path, required=True); watch.add_argument('--seconds', type=int, default=60)
    control = sub.add_parser('maintenance'); control.add_argument('--store', type=Path, required=True); control.add_argument('--enabled', choices=('yes','no'), required=True)
    args = p.parse_args()
    if args.action == 'export':
        release, report = build(args.origin, args.store/'releases', args.message, args.contact)
        print(json.dumps({'release': str(release), 'report': report}, ensure_ascii=False))
    elif args.action == 'publish':
        publish(args.release, args.current); print('PASS verified release published atomically')
    elif args.action == 'backup':
        print(json.dumps({'sha256': create(args.release, args.archive)}))
    elif args.action == 'restore':
        print(json.dumps({'restored_release': restore(args.archive, args.destination, args.sha256)['release']}))
    elif args.action == 'config':
        store = args.store.absolute(); store.mkdir(parents=True, exist_ok=True)
        if not (store/'control.json').exists(): atomic_json(store/'control.json', {'manual_maintenance': False, 'windows': []})
        (store/'unhealthy').touch()
        server = server_config(args.origin, store/'current', store/'unhealthy', store/'maintenance', args.listen)
        (store/'server.conf').write_text(server)
        (store/'nginx.conf').write_text(standalone_config(server, store))
        print('PASS isolated Nginx config prepared; no server started or shared config changed')
    elif args.action == 'watch':
        if not 1 <= args.seconds <= 3600: raise ValueError('Bounded watcher 1–3600 seconds required')
        with (args.store/'watch.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            deadline = time.monotonic() + args.seconds
            while time.monotonic() < deadline:
                tick(args.origin, args.store); time.sleep(2)
        print('Bounded health/maintenance watcher finished; inspect saved health evidence')
    elif args.action == 'maintenance':
        control = json.loads((args.store/'control.json').read_text()); control['manual_maintenance'] = args.enabled == 'yes'
        atomic_json(args.store/'control.json', control)
        # Immediate local control, even if a watcher is stopped. Turning off
        # maintenance still leaves the independent health gate intact.
        marker = args.store/'maintenance'
        if control['manual_maintenance'] or maintenance_active(control['windows'], datetime.now(timezone.utc)): marker.touch()
        else:
            (args.store/'unhealthy').touch()
            atomic_json(args.store/'health.json', {'successes':0,'maintenance_recovery':True})
            if marker.exists(): marker.unlink()
        print('Maintenance control updated; live health must still be checked')


if __name__ == '__main__': main()
