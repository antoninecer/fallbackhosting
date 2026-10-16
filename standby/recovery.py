"""A nonexecuting first restore planner for the explicitly supported static format."""
from pathlib import Path
import re


def plan(catalog, selected, destination):
    if not isinstance(selected,str) or not re.fullmatch('[a-f0-9]{64}',selected):raise ValueError('Invalid backup selection')
    if not isinstance(catalog,dict) or set(catalog)!={'repository','backups'} or catalog['repository']!='FOUND' or not isinstance(catalog['backups'],list) or len(catalog['backups'])>100:
        raise ValueError('Unsupported discovery result')
    if not all(isinstance(row,dict) for row in catalog['backups']):raise ValueError('Invalid catalog records')
    rows=[row for row in catalog['backups'] if row.get('id')==selected]
    if len(rows)!=1:raise ValueError('Select exactly one discovered backup')
    row=rows[0]
    if row.get('kind')!='STATIC_SNAPSHOT' or row.get('integrity')!='VERIFIED' or row.get('compatibility')!='STATIC_SNAPSHOT_V1':raise ValueError('Selected format or integrity unsupported')
    if type(row.get('bytes')) is not int or not 1<=row['bytes']<=32*1024*1024 or not isinstance(row.get('release'),str) or not re.fullmatch(r'\d{8}T\d{6}Z-[a-f0-9]{8}',row['release']):raise ValueError('Invalid restore metadata')
    destination=Path(destination).absolute()
    if destination.exists() or destination.is_symlink() or any(p.is_symlink() for p in destination.parents):raise ValueError('New isolated destination without symlinked parents required')
    return {'schema_version':1,'action':'PREVIEW_ONLY_NO_EXECUTION','backup_id':selected,'scope':'STATIC_SNAPSHOT_ONLY',
            'destination':str(destination),'release':row['release'],'bytes':row['bytes'],'integrity':'VERIFIED',
            'restore_evidence':row.get('restore','NOT_TESTED'),'provenance':row.get('provenance','UNKNOWN'),
            'requires_operator_selection':True,'automatic_publish':False,'controller_database_or_secrets_restore':'UNSUPPORTED',
            'steps':['Fetch selected archive through independently verified SSH identity','Verify selected archive checksum against approved recovery point','Restore bounded static format into a new isolated directory','Verify manifest/file hashes and preview','Publish only through separately authorized verified publication flow']}
