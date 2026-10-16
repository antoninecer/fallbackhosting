"""Fixed-app publication workflow. Web callers never supply URLs, paths or SSH data."""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import re
import shutil

from operations.core import Denied, exact
from standby.backup import create
from standby.gateway import atomic_json
from standby.snapshot import build, publish, verify

RELEASE = re.compile(r'[0-9]{8}T[0-9]{6}Z-[a-f0-9]{8}')


def utc():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


class Publishing:
    def __init__(self, config, backup_provider):
        exact(config, 'origin store public message contact asset_prefix')
        self.config = config
        self.store = Path(config['store'])
        self.public = Path(config['public'])
        self.backup_provider = backup_provider
        self.store.mkdir(parents=True, exist_ok=True)
        with self.lock():
            if not self.path.exists():
                atomic_json(self.path, {'revision': 1, 'phase': 'IDLE', 'audit': []})
            state = self.load()
            if state['phase'] in ('PREPARING', 'PUBLISHING', 'ROLLING_BACK'):
                self.save(state, phase='NEEDS_REVIEW', error='INTERRUPTED_OPERATION')

    @property
    def path(self):
        return self.store / 'publication.json'

    @contextmanager
    def lock(self):
        with (self.store / 'publication.lock').open('a') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            yield

    def load(self):
        return json.loads(self.path.read_text())

    def save(self, state, **changes):
        state.update(changes)
        state['revision'] += 1
        state['utc'] = utc()
        state['audit'] = (state['audit'] + [{'utc': state['utc'], 'phase': state['phase']}])[-20:]
        atomic_json(self.path, state)
        return state

    def current(self):
        current = self.public / 'current'
        if not current.is_symlink():
            raise ValueError('Existing published symlink required')
        target = current.resolve(strict=True)
        if target.parent != (self.public / 'releases').resolve() or not RELEASE.fullmatch(target.name):
            raise ValueError('Current release outside fixed store')
        verify(target)
        return target.name

    def view(self):
        with self.lock():
            state = self.load()
            # No configuration, endpoints, filesystem paths or raw errors cross the socket.
            result = {k: state[k] for k in ('revision', 'phase', 'utc', 'candidate', 'previous', 'backup', 'error', 'audit') if k in state}
            result['current'] = self.current()
            return result

    def request(self, operation, revision):
        with self.lock():
            state = self.load()
            if type(revision) is not int or state['revision'] != revision:
                raise Denied('STALE_REVISION')
            if state['phase'] in ('PREPARING', 'PUBLISHING', 'ROLLING_BACK', 'NEEDS_REVIEW'):
                raise Denied('PUBLICATION_BUSY_OR_REVIEW_REQUIRED')
            if operation == 'prepare':
                current = self.current()
                self.save(state, phase='PREPARING', previous=current, candidate=None, backup=None, error=None)
            elif operation == 'publish':
                if state['phase'] != 'READY':
                    raise Denied('PREVIEW_NOT_READY')
                if self.current() != state['previous']:
                    raise Denied('CURRENT_CHANGED')
                self.validate_candidate(state)
                self.save(state, phase='PUBLISHING')
            elif operation == 'rollback':
                if state['phase'] != 'PUBLISHED' or self.current() != state['candidate']:
                    raise Denied('ROLLBACK_NOT_AVAILABLE')
                verify(self.public / 'releases' / state['previous'])
                self.save(state, phase='ROLLING_BACK')
            else:
                raise Denied('UNKNOWN_OPERATION')
        return self.view()

    def validate_candidate(self, state):
        name = state.get('candidate')
        if not isinstance(name, str) or not RELEASE.fullmatch(name):
            raise Denied('INVALID_RELEASE')
        release = self.public / 'releases' / name
        if release.is_symlink():
            raise Denied('INVALID_RELEASE')
        manifest = verify(release)
        digest = hashlib.sha256((release / 'manifest.json').read_bytes()).hexdigest()
        if digest != state.get('manifest_sha256') or manifest['release'] != name or state.get('backup') != 'VERIFIED_READBACK_RESTORE':
            raise Denied('CANDIDATE_CHANGED_OR_BACKUP_MISSING')
        return release

    def advance(self):
        """Called by the private worker, never within the web request deadline."""
        with self.lock():
            state = self.load()
            phase = state['phase']
            if phase not in ('PREPARING', 'PUBLISHING', 'ROLLING_BACK'):
                return
        try:
            if phase == 'PREPARING':
                cfg = self.config
                release, manifest = build(cfg['origin'], self.store / 'releases', cfg['message'], cfg['contact'], cfg['asset_prefix'])
                backups = self.store / 'backups'
                backups.mkdir(exist_ok=True)
                archive = backups / (release.name + '.tgz')
                digest = create(release, archive)
                result = self.backup_provider(release, archive, digest)
                if (result.get('sha256') != digest or result.get('remote_copy') != 'VERIFIED' or
                        result.get('remote_readback') != 'VERIFIED' or result.get('isolated_restore') != 'PASS'):
                    raise ValueError('Independent backup required')
                destination = self.public / 'releases' / release.name
                shutil.copytree(release, destination)
                for path in [destination, *destination.rglob('*')]:
                    path.chmod(0o755 if path.is_dir() else 0o644)
                verify(destination)
                with self.lock():
                    state = self.load()
                    self.save(state, phase='READY', candidate=release.name, backup='VERIFIED_READBACK_RESTORE',
                              manifest_sha256=hashlib.sha256((destination / 'manifest.json').read_bytes()).hexdigest())
            else:
                with self.lock():
                    state = self.load()
                    expected = state['previous'] if phase == 'PUBLISHING' else state['candidate']
                    if self.current() != expected:
                        raise ValueError('Concurrent publication detected')
                    release = self.validate_candidate(state) if phase == 'PUBLISHING' else self.public / 'releases' / state['previous']
                    publish(release, self.public / 'current')
                    self.save(state, phase='PUBLISHED' if phase == 'PUBLISHING' else 'ROLLED_BACK', error=None)
        except Exception:
            with self.lock():
                state = self.load()
                # A pointer might already have changed: interrupted publish requires reconciliation.
                self.save(state, phase='FAILED' if phase == 'PREPARING' else 'NEEDS_REVIEW', error='OPERATION_FAILED')
