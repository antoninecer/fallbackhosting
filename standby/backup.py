"""Portable snapshot backup and strict isolated restore; no disk/service changes."""
import hashlib
import gzip
import io
import json
from pathlib import Path
import tarfile

from standby.snapshot import verify

NAMES = {'index.html', 'assets/style.css', 'assets/hero.webp', 'manifest.json'}


def create(release, archive):
    release = Path(release); verify(release); archive = Path(archive)
    with archive.open('xb') as stream:
        with tarfile.open(fileobj=stream, mode='w:gz') as tar:
            for name in sorted(NAMES):
                body = (release/name).read_bytes()
                info = tarfile.TarInfo(name); info.mode = 0o644; info.size = len(body)
                tar.addfile(info, io.BytesIO(body))
    return hashlib.sha256(archive.read_bytes()).hexdigest()


def restore(archive, destination, expected_sha256):
    archive, destination = Path(archive), Path(destination)
    if archive.stat().st_size > 32 * 1024 * 1024: raise ValueError('Backup too large')
    if hashlib.sha256(archive.read_bytes()).hexdigest() != expected_sha256: raise ValueError('Archive integrity mismatch')
    with gzip.open(archive,'rb') as stream: raw=stream.read(34*1024*1024+1)
    if len(raw)>34*1024*1024:raise ValueError('Uncompressed backup exceeds budget')
    bodies = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as tar:
        for member in tar:
            if member.name not in NAMES or member.name in bodies or not member.isfile() or member.size > 8 * 1024 * 1024:
                raise ValueError('Unexpected, duplicate, linked or oversized backup member')
            stream = tar.extractfile(member)
            body = stream.read(8 * 1024 * 1024 + 1)
            if len(body) != member.size: raise ValueError('Truncated archive')
            bodies[member.name] = body
    if set(bodies) != NAMES: raise ValueError('Incomplete archive')
    manifest = json.loads(bodies['manifest.json'])
    if manifest.get('schema_version') != 1 or set(manifest.get('files', {})) != NAMES - {'manifest.json'}: raise ValueError('Invalid backup manifest')
    for name, digest in manifest['files'].items():
        if hashlib.sha256(bodies[name]).hexdigest() != digest: raise ValueError('Backup member integrity mismatch')
    destination.mkdir(exist_ok=False)
    for name, body in bodies.items():
        path = destination/name; path.parent.mkdir(exist_ok=True)
        with path.open('xb') as stream: stream.write(body)
    verify(destination)
    return manifest
