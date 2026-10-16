from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import gzip
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from operations import standby_backup
from standby.backup import create
from standby.backup import restore
from standby.recovery import plan
from standby.snapshot import build
from test_standby import fixture


class StandbyRecoveryTest(unittest.TestCase):
    def test_decompression_budget_rejects_before_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive=Path(tmp)/'oversized.tgz';body=gzip.compress(b'\0'*(34*1024*1024+1));archive.write_bytes(body)
            with self.assertRaises(ValueError):standby_backup.check_archive(body)
            with self.assertRaises(ValueError):restore(archive,Path(tmp)/'restored',hashlib.sha256(body).hexdigest())
            self.assertFalse((Path(tmp)/'restored').exists())

    def test_catalog_real_archive_read_only_and_restore_preview(self):
        with fixture() as (root,origin,state,files):
            release,manifest=build(origin,root/'releases','notice','contact')
            repository=root/'.fallback-standby-backups';repository.mkdir(mode=0o700)
            archive=root/'archive.tgz';digest=create(release,archive)
            (repository/(digest+'.tgz')).write_bytes(archive.read_bytes())
            record={'schema_version':1,'sha256':digest,'bytes':archive.stat().st_size,'release':manifest['release'],'received_utc':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'integrity':'VERIFIED','restore':'NOT_TESTED'}
            meta=repository/(digest+'.json');meta.write_text(json.dumps(record))
            before={p.name:p.read_bytes() for p in repository.iterdir()}
            out=io.StringIO()
            with patch.object(Path,'home',return_value=root),redirect_stdout(out):standby_backup.main({'action':'list'})
            result=json.loads(out.getvalue())
            self.assertEqual(len(result['backups']),1);self.assertEqual(result['backups'][0]['integrity'],'VERIFIED')
            self.assertEqual({p.name:p.read_bytes() for p in repository.iterdir()},before)
            target=root/'isolated-destination';preview=plan(result,digest,target)
            self.assertEqual(preview['action'],'PREVIEW_ONLY_NO_EXECUTION');self.assertFalse(target.exists())
            self.assertFalse(preview['automatic_publish']);self.assertEqual(preview['controller_database_or_secrets_restore'],'UNSUPPORTED')
            with self.assertRaises(ValueError):plan(result,digest,root)
            (repository/(digest+'.tgz')).write_bytes(b'damaged')
            bad=standby_backup.catalog(repository)
            self.assertEqual(bad['backups'][0]['integrity'],'UNKNOWN')
            with self.assertRaises(ValueError):plan(bad,digest,target)

    def test_malformed_symlink_unknown_format_and_duplicate_selection_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);digest='a'*64
            (root/(digest+'.json')).write_text('{"schema_version":1,"schema_version":2}')
            result=standby_backup.catalog(root)
            self.assertEqual(result['backups'][0]['integrity'],'UNKNOWN')
            (root/(digest+'.json')).unlink();(root/(digest+'.json')).symlink_to('/etc/passwd')
            self.assertEqual(standby_backup.catalog(root)['backups'][0]['integrity'],'UNKNOWN')
            with self.assertRaises(ValueError):plan(result,digest,root/'new')
            row={'id':digest,'kind':'CONTROLLER_DATABASE','integrity':'VERIFIED','compatibility':'STATIC_SNAPSHOT_V1'}
            with self.assertRaises(ValueError):plan({'repository':'FOUND','backups':[row]},digest,root/'new')
            row.update(kind='STATIC_SNAPSHOT')
            with self.assertRaises(ValueError):plan({'repository':'FOUND','backups':[row,row]},digest,root/'new')
            self.assertEqual(standby_backup.catalog(root/'missing'),{'repository':'ABSENT','backups':[]})
