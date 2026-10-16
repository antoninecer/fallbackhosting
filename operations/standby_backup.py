"""Fixed private SSH backup repository; no mount, Docker or service needed."""
import base64
from datetime import datetime, timezone
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import tarfile

NAMES={'index.html','assets/style.css','assets/hero.webp','manifest.json'}


def check_archive(body):
    files={}
    with tarfile.open(fileobj=io.BytesIO(body),mode='r:gz') as archive:
        for member in archive:
            if member.name not in NAMES or member.name in files or not member.isfile() or member.size>8*1024*1024:
                raise ValueError('Invalid backup member')
            data=archive.extractfile(member).read(8*1024*1024+1)
            if len(data)!=member.size:raise ValueError('Invalid backup size')
            files[member.name]=data
    if set(files)!=NAMES:raise ValueError('Incomplete backup')
    manifest=json.loads(files['manifest.json'])
    if manifest.get('schema_version')!=1 or set(manifest.get('files',{}))!=NAMES-{'manifest.json'}:raise ValueError('Unsupported manifest')
    for name,digest in manifest['files'].items():
        if hashlib.sha256(files[name]).hexdigest()!=digest:raise ValueError('Backup integrity mismatch')
    return manifest


def main(payload):
    os.umask(0o077)
    action=payload['action'];digest=payload['sha256']
    if action not in ('put','get','verify') or not re.fullmatch('[a-f0-9]{64}',digest):raise ValueError('Invalid fixed action')
    root=Path.home()/'.fallback-standby-backups'
    if action=='put':root.mkdir(mode=0o700,exist_ok=True)
    info=root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077:raise ValueError('Unsafe repository')
    with (root/'repository.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        target=root/(digest+'.tgz')
        if action=='put':
            body=base64.b64decode(payload['archive'],validate=True)
            if len(body)>32*1024*1024 or hashlib.sha256(body).hexdigest()!=digest:raise ValueError('Invalid supplied archive')
            manifest=check_archive(body)
            if target.exists():
                if target.is_symlink() or hashlib.sha256(target.read_bytes()).hexdigest()!=digest:raise ValueError('Repository collision')
            else:
                with target.open('xb') as stream:stream.write(body)
            record={'schema_version':1,'sha256':digest,'bytes':len(body),'release':manifest['release'],'received_utc':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'integrity':'VERIFIED','restore':'NOT_TESTED'}
            catalog=root/(digest+'.json')
            pending=root/(digest+'.pending')
            pending.write_text(json.dumps(record));pending.replace(catalog)
            print(json.dumps({'stored':True,'sha256':digest,'bytes':len(body),'integrity':'VERIFIED'}))
            return
        if target.is_symlink() or target.stat().st_size>32*1024*1024:raise ValueError('Unsafe archive')
        body=target.read_bytes()
        if hashlib.sha256(body).hexdigest()!=digest:raise ValueError('Stored archive damaged')
        check_archive(body)
        result={'sha256':digest,'bytes':len(body),'integrity':'VERIFIED'}
        if action=='get':result['archive']=base64.b64encode(body).decode()
        print(json.dumps(result))


if __name__=='__main__':main(PAYLOAD_PLACEHOLDER)
