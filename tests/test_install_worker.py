import json
import os
from pathlib import Path
import tempfile
import unittest
from operations import install_worker as worker


class InstallWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.queue=Path(self.temp.name)/'queue';self.queue.mkdir(mode=0o700)
        self.ledger=Path(self.temp.name)/'ledger';self.ledger.mkdir(mode=0o700)
        self.ident='a'*32
        self.policy=dict(node='ctx1',actor='admin')
        self.request=dict(schema_version=1,id=self.ident,action='install',node='ctx1',template=worker.TEMPLATE,inventory_revision=3,actor='admin',created_utc=worker.utc())
        self.secret=dict(email='operator@example.org',password='Strong-Fixture8!Pass')
        self.calls=[]

    def write(self,request=None,secret=None):
        for suffix,value in (('request',self.request if request is None else request),('secret',self.secret if secret is None else secret)):
            path=self.queue/(self.ident+'.'+suffix+'.json');path.write_text(json.dumps(value));path.chmod(0o600)

    def driver(self,secret):
        self.calls.append(secret)
        return dict(healthy_services=3,admin_created=True,registration_disabled=True,unrelated_unchanged=True)

    def run_job(self,driver=None):
        return worker.run_one(self.queue,self.ledger,self.policy,driver or self.driver,self.ident,os.getuid())

    def test_success_is_one_shot_and_credentials_never_enter_status_or_ledger(self):
        self.write();self.assertEqual(self.run_job(),'SUCCEEDED')
        self.assertEqual(len(self.calls),1)
        self.assertFalse((self.queue/(self.ident+'.secret.json')).exists())
        for p in [*self.queue.iterdir(),*self.ledger.iterdir()]:
            self.assertNotIn(self.secret['password'],p.read_text());self.assertNotIn(self.secret['email'],p.read_text())
        self.write();self.assertEqual(self.run_job(),'UNKNOWN');self.assertEqual(len(self.calls),1)

    def test_untrusted_scope_schema_expiry_and_password_fail_before_dispatch(self):
        mutations=[dict(command='id'),dict(node='other'),dict(template='arbitrary:latest'),dict(actor='guest'),dict(created_utc='2000-01-01T00:00:00Z'),dict(inventory_revision=True)]
        for i,change in enumerate(mutations):
            self.ident=f'{i:032x}';self.request['id']=self.ident
            self.write(dict(self.request,**change))
            self.assertEqual(self.run_job(),'FAILED')
        self.assertEqual(self.calls,[])

    def test_timeout_or_incomplete_verification_is_unknown_and_never_replayed(self):
        self.write()
        def fail(secret): raise TimeoutError('sensitive diagnostic must not escape')
        self.assertEqual(self.run_job(fail),'UNKNOWN')
        self.assertEqual(json.loads((self.queue/(self.ident+'.status.json')).read_text())['state'],'UNKNOWN')
        self.assertFalse((self.queue/(self.ident+'.secret.json')).exists())
        self.assertNotIn('diagnostic',(self.queue/(self.ident+'.status.json')).read_text())

    def test_symlink_duplicate_keys_oversize_and_unsafe_modes_are_rejected(self):
        target=Path(self.temp.name)/'secret';target.write_text('{}');target.chmod(0o600)
        link=self.queue/'link';link.symlink_to(target)
        with self.assertRaises(OSError):worker.read_private(link,os.getuid())
        target.write_text('{"x":1,"x":2}')
        with self.assertRaises(ValueError):worker.read_private(target,os.getuid())
        target.write_text('x'*8193)
        with self.assertRaises(ValueError):worker.read_private(target,os.getuid())
        target.write_text('{}');target.chmod(0o644)
        with self.assertRaises(ValueError):worker.read_private(target,os.getuid())

    def test_partial_or_false_success_is_unknown(self):
        self.write();self.assertEqual(self.run_job(lambda secret:dict(admin_created=True)),'UNKNOWN')

if __name__=='__main__':unittest.main()
