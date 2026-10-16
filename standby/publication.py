"""Compose export -> backup verification -> atomic publication.

Backup provider is injected; deployment/UI remain separate from static serving.
"""
from datetime import datetime, timezone
from pathlib import Path

from standby.backup import create
from standby.gateway import atomic_json
from standby.snapshot import build, publish


def publish_with_backup(config, backup_provider):
    if set(config)!={'origin','store','message','contact','asset_prefix'}:raise ValueError('Unsupported publication config')
    store=Path(config['store']);store.mkdir(parents=True,exist_ok=True)
    release,manifest=build(config['origin'],store/'releases',config['message'],config['contact'],config['asset_prefix'])
    backups=store/'backups';backups.mkdir(exist_ok=True)
    archive=backups/(manifest['release']+'.tgz');digest=create(release,archive)
    journal=store/('publication-'+manifest['release']+'.json')
    atomic_json(journal,{'release':manifest['release'],'phase':'VERIFYING_BACKUP','sha256':digest})
    try:
        result=backup_provider(release,archive,digest)
        if (result.get('sha256')!=digest or result.get('remote_copy')!='VERIFIED' or result.get('remote_readback')!='VERIFIED' or result.get('isolated_restore')!='PASS'):
            raise ValueError('Independent verified backup/readback/restore required')
        publish(release,store/'current')
        report={'release':manifest['release'],'phase':'PUBLISHED','sha256':digest,
                'utc':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'backup':result,
                'image_source_bytes':manifest['image_source_bytes'],'image_result_bytes':manifest['image_result_bytes']}
        atomic_json(journal,report)
        return report
    except Exception:
        atomic_json(journal,{'release':manifest['release'],'phase':'NOT_PUBLISHED','sha256':digest})
        raise
