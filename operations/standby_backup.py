"""Fixed private SSH backup repository; no mount, Docker or service needed."""
import base64
from datetime import datetime, timezone
import fcntl
import hashlib
import gzip
import io
import json
import os
from pathlib import Path
import re
import stat
import tarfile
from itertools import islice

NAMES={'index.html','assets/style.css','assets/hero.webp','manifest.json'}


def catalog(root):
    """Read-only bounded discovery; never create a lock/file or execute a manifest."""
    root=Path(root)
    if not root.exists():return {'repository':'ABSENT','backups':[]}
    info=root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077:raise ValueError('Unsafe repository')
    entries=list(islice(root.iterdir(),1001))
    if len(entries)>1000:raise ValueError('Repository entry budget exceeded')
    records=sorted(p for p in entries if re.fullmatch('[a-f0-9]{64}[.]json',p.name))
    if len(records)>100:raise ValueError('Catalog record budget exceeded')
    result=[]
    for record in records:
        ident=record.stem
        row={'id':ident,'kind':'STATIC_SNAPSHOT','scope':'PUBLIC_STATIC_DEMO_ONLY','integrity':'UNKNOWN','restore':'NOT_TESTED','provenance':'PINNED_SSH_REPOSITORY_NOT_SIGNED_ARCHIVE'}
        try:
            if record.is_symlink() or not record.is_file() or record.stat().st_size>8192:raise ValueError('Unsafe catalog record')
            def unique(pairs):
                value={}
                for k,v in pairs:
                    if k in value:raise ValueError('Repeated catalog field')
                    value[k]=v
                return value
            meta=json.loads(record.read_text(),object_pairs_hook=unique)
            if not isinstance(meta,dict):raise ValueError('Catalog object required')
            required={'schema_version','sha256','bytes','release','received_utc','integrity','restore'}
            if not required.issubset(meta) or set(meta)-required-{'restore_tested_utc','restore_method'}:raise ValueError('Unexpected catalog fields')
            if meta['restore'] not in ('NOT_TESTED','TESTED_READBACK_LOCAL'):raise ValueError('Unknown restore evidence')
            if meta.get('schema_version')!=1 or meta.get('sha256')!=ident or type(meta.get('bytes')) is not int or not 1<=meta['bytes']<=32*1024*1024:raise ValueError('Unsupported catalog')
            if not re.fullmatch(r'\d{8}T\d{6}Z-[a-f0-9]{8}',meta.get('release','')):raise ValueError('Invalid release')
            datetime.strptime(meta['received_utc'],'%Y-%m-%dT%H:%M:%SZ')
            target=root/(ident+'.tgz')
            if target.is_symlink() or not target.is_file() or target.stat().st_size!=meta['bytes']:raise ValueError('Missing/unsafe archive')
            body=target.read_bytes()
            if hashlib.sha256(body).hexdigest()!=ident:raise ValueError('Archive damaged')
            manifest=check_archive(body)
            if manifest['release']!=meta['release']:raise ValueError('Release mismatch')
            row.update(release=meta['release'],bytes=meta['bytes'],received_utc=meta['received_utc'],integrity='VERIFIED',compatibility='STATIC_SNAPSHOT_V1')
            if meta.get('restore')=='TESTED_READBACK_LOCAL':
                datetime.strptime(meta['restore_tested_utc'],'%Y-%m-%dT%H:%M:%SZ')
                if meta.get('restore_method')!='OPERATOR_TOOL_AFTER_READBACK_ISOLATED_STATIC_RESTORE':raise ValueError('Unknown restore provenance')
                row.update(restore='TESTED_READBACK_LOCAL_ATTESTED',restore_tested_utc=meta['restore_tested_utc'])
        except (ValueError,TypeError,KeyError,OSError,RecursionError,tarfile.TarError):row.update(integrity='UNKNOWN',restore='NOT_TESTED',error='CATALOG_OR_ARCHIVE_UNVERIFIED',compatibility='UNKNOWN')
        result.append(row)
    return {'repository':'FOUND','backups':result}


def check_archive(body):
    with gzip.GzipFile(fileobj=io.BytesIO(body),mode='rb') as stream: raw=stream.read(34*1024*1024+1)
    if len(raw)>34*1024*1024:raise ValueError('Uncompressed archive exceeds budget')
    files={}
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as archive:
        for member in archive:
            if member.name not in NAMES or member.name in files or not member.isfile() or member.size>8*1024*1024:
                raise ValueError('Invalid backup member')
            data=archive.extractfile(member).read(8*1024*1024+1)
            if len(data)!=member.size:raise ValueError('Invalid backup size')
            files[member.name]=data
    if set(files)!=NAMES:raise ValueError('Incomplete backup')
    manifest=json.loads(files['manifest.json'])
    if not isinstance(manifest,dict):raise ValueError('Manifest object required')
    if manifest.get('schema_version')!=1 or set(manifest.get('files',{}))!=NAMES-{'manifest.json'}:raise ValueError('Unsupported manifest')
    for name,digest in manifest['files'].items():
        if hashlib.sha256(files[name]).hexdigest()!=digest:raise ValueError('Backup integrity mismatch')
    return manifest


def main(payload):
    os.umask(0o077)
    action=payload['action']
    if action=='list':
        if set(payload)!={'action'}:raise ValueError('Unexpected discovery input')
        print(json.dumps(catalog(Path.home()/'.fallback-standby-backups')));return
    digest=payload['sha256']
    if action not in ('put','get','verify','mark_restore_tested') or not re.fullmatch('[a-f0-9]{64}',digest):raise ValueError('Invalid fixed action')
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
            catalog_path=root/(digest+'.json')
            pending=root/(digest+'.pending')
            pending.write_text(json.dumps(record));pending.replace(catalog_path)
            print(json.dumps({'stored':True,'sha256':digest,'bytes':len(body),'integrity':'VERIFIED'}))
            return
        if target.is_symlink() or target.stat().st_size>32*1024*1024:raise ValueError('Unsafe archive')
        body=target.read_bytes()
        if hashlib.sha256(body).hexdigest()!=digest:raise ValueError('Stored archive damaged')
        check_archive(body)
        result={'sha256':digest,'bytes':len(body),'integrity':'VERIFIED'}
        if action=='get':result['archive']=base64.b64encode(body).decode()
        if action=='mark_restore_tested':
            record=root/(digest+'.json')
            if record.is_symlink() or record.stat().st_size>8192:raise ValueError('Unsafe restore record')
            meta=json.loads(record.read_text());assert meta['sha256']==digest
            meta.update(restore='TESTED_READBACK_LOCAL',restore_tested_utc=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),restore_method='OPERATOR_TOOL_AFTER_READBACK_ISOLATED_STATIC_RESTORE')
            pending=root/(digest+'.pending');pending.write_text(json.dumps(meta));pending.replace(record)
            result['restore']='TESTED_READBACK_LOCAL_ATTESTED'
        print(json.dumps(result))


if __name__=='__main__':main(PAYLOAD_PLACEHOLDER)
