#!/usr/bin/env python3
"""Read-only offline release checks. Never installs, switches or reloads anything."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'public/index.php': 'admin/public/index.php',
    'public/admin.css': 'admin/public/admin.css',
    'lib.php': 'admin/lib.php',
    'center.php': 'admin/center.php',
    'install.php': 'admin/install.php',
    'standby.php': 'admin/standby.php',
    'operations-client.php': 'admin/operations-client.php',
    'installer/install_worker.py': 'operations/install_worker.py',
    'installer/coolify_reinstall.py': 'operations/coolify_reinstall.py',
}
LIMITS = {'index.html': 1048576, 'center.css': 262144,
          'center.js': 131072, 'resume.txt': 131072}


def verify(release, revision, manifest_digest, require_root=False):
    if not re.fullmatch(r'[a-f0-9]{40}', revision):
        raise ValueError('An exact full Git revision is required')
    if not re.fullmatch(r'[a-f0-9]{64}', manifest_digest):
        raise ValueError('A separately reviewed artifact manifest digest is required')
    release = Path(release).absolute()
    for path in [*release.parents, release]:
        if path.is_symlink():
            raise ValueError('Symlinked release path')
    expected = set(SOURCES) | {'center-artifact/' + n for n in (*LIMITS, 'manifest.json')}
    expected_dirs = {'public', 'center-artifact', 'installer'}
    found = set()
    for path in [release, *release.rglob('*')]:
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
            raise ValueError('Only ordinary files and directories are accepted')
        if stat.S_IMODE(info.st_mode) != (0o755 if path.is_dir() else 0o644):
            raise ValueError('Release modes must be exactly 0755/0644')
        if require_root and (info.st_uid != 0 or info.st_gid != 0):
            raise ValueError('Production release must be root:root owned')
        if path == release:
            continue
        name = path.relative_to(release).as_posix()
        if path.is_dir():
            if name not in expected_dirs:
                raise ValueError('Unexpected directory')
        else:
            if name not in expected or info.st_size > 1048576:
                raise ValueError('Unexpected or oversized file')
            found.add(name)
    if found != expected:
        raise ValueError('Release file set differs')
    for name, source in SOURCES.items():
        original = subprocess.run(['git', 'show', revision + ':' + source], cwd=ROOT,
                                  check=True, capture_output=True, timeout=10).stdout
        if (release / name).read_bytes() != original:
            raise ValueError('Release source differs from pinned commit')
    artifact = release / 'center-artifact'
    manifest_bytes = (artifact / 'manifest.json').read_bytes()
    if len(manifest_bytes) > 8192 or hashlib.sha256(manifest_bytes).hexdigest() != manifest_digest:
        raise ValueError('Artifact manifest differs from reviewed digest')
    manifest = json.loads(manifest_bytes)
    if not isinstance(manifest, dict) or set(manifest) != set(LIMITS):
        raise ValueError('Artifact manifest file set differs')
    for name, limit in LIMITS.items():
        body = (artifact / name).read_bytes()
        if (len(body) > limit or not isinstance(manifest[name], str)
                or not re.fullmatch(r'[a-f0-9]{64}', manifest[name])
                or hashlib.sha256(body).hexdigest() != manifest[name]):
            raise ValueError('Artifact content differs')
    html = (artifact / 'index.html').read_text()
    if not all('"/?center=' + name + '"' in html for name in ('center.css', 'center.js', 'resume.txt')):
        raise ValueError('Artifact must use authenticated admin-query delivery')
    return {'source': 'PASS', 'artifact': 'PASS',
            'ownership': 'PASS_ROOT' if require_root else 'NOT_CHECKED',
            'runtime_auth_canaries_rollback': 'NOT_TESTED', 'activation': 'NOT_PERFORMED'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release', type=Path)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--artifact-manifest-sha256', required=True)
    parser.add_argument('--require-root-owned', action='store_true')
    args = parser.parse_args()
    try:
        result = verify(args.release, args.revision, args.artifact_manifest_sha256,
                        args.require_root_owned)
    except (ValueError, OSError, subprocess.SubprocessError):
        parser.exit(1, 'FAIL: offline release validation; no activation performed\n')
    print(json.dumps(result, sort_keys=True))
