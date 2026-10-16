"""Private fixed-app publication socket and background worker."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import socket
import stat
import threading

from operations.core import Denied, exact
from operations.protocol import serve_connection
from standby.backup import restore
from standby.publishing import Publishing
from standby.transport import fixed_script


class PublicationAPI:
    def __init__(self, workflow, uid, actor):
        self.workflow, self.uid, self.actor = workflow, uid, actor

    def authorize(self, request, uid):
        if uid != self.uid or request.get('actor') != self.actor or request.get('app') != 'demo':
            raise Denied('FORBIDDEN')

    def read(self, request, uid):
        exact(request, 'kind actor app'); self.authorize(request, uid)
        if request['kind'] != 'view': raise Denied('UNKNOWN_OPERATION')
        return {'ok': True, **self.workflow.view()}

    def submit(self, request, uid):
        exact(request, 'kind actor app revision operation'); self.authorize(request, uid)
        if request['kind'] != 'publication': raise Denied('UNKNOWN_OPERATION')
        return {'ok': True, **self.workflow.request(request['operation'], request['revision'])}


def backup_provider(node, source):
    def run(release, archive, digest):
        saved = fixed_script(source, {'action': 'put', 'sha256': digest, 'archive': base64.b64encode(archive.read_bytes()).decode()}, node)
        if saved.get('stored') is not True or saved.get('sha256') != digest: raise ValueError('Backup failed')
        result = fixed_script(source, {'action': 'get', 'sha256': digest}, node)
        readback = base64.b64decode(result['archive'], validate=True)
        if hashlib.sha256(readback).hexdigest() != digest: raise ValueError('Readback failed')
        returned = archive.with_suffix('.readback.tgz')
        with returned.open('xb') as stream: stream.write(readback)
        returned.chmod(0o600)
        restore(returned, archive.parent / (release.name + '-restore'), digest)
        fixed_script(source, {'action': 'mark_restore_tested', 'sha256': digest}, node)
        return {'sha256': digest, 'remote_copy': 'VERIFIED', 'remote_readback': 'VERIFIED', 'isolated_restore': 'PASS'}
    return run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', type=Path, required=True)
    args = parser.parse_args()
    info = args.policy.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
        raise ValueError('Immutable root-owned policy required')
    policy = json.loads(args.policy.read_text())
    if os.geteuid() != policy['service_uid']: raise ValueError('Incorrect identity')
    if policy['node']['observations']['fingerprint']['status'] != 'PASS': raise ValueError('Verified backup identity required')
    workflow = Publishing(policy['config'], backup_provider(policy['node'], policy['backup_script']))
    api = PublicationAPI(workflow, policy['web_uid'], policy['actor'])
    listener = socket.socket(fileno=3)
    selector = selectors.DefaultSelector(); selector.register(listener, selectors.EVENT_READ)
    stopped = threading.Event()
    signal.signal(signal.SIGTERM, lambda *unused: stopped.set())
    signal.signal(signal.SIGINT, lambda *unused: stopped.set())
    failed = threading.Event()
    def worker():
        try:
            while not stopped.wait(.2): workflow.advance()
        except Exception:
            failed.set(); stopped.set()
    thread = threading.Thread(target=worker); thread.start()
    try:
        while not stopped.is_set():
            for key, mask in selector.select(.2):
                connection, _ = listener.accept(); serve_connection(connection, api)
    finally:
        stopped.set(); thread.join(); selector.close(); listener.close()
    if failed.is_set(): raise RuntimeError('Publication worker unavailable; inspect private state')


if __name__ == '__main__': main()
