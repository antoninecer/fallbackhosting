"""No real commands, reload, certificate issuance or network access."""
from contextlib import contextmanager
import importlib.util
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('renewal_hook',ROOT/'deploy/certificate-deploy-hook.py')
hook=importlib.util.module_from_spec(spec);spec.loader.exec_module(hook)

class RenewalHookTests(unittest.TestCase):
    def run_hook(self,domain='project.lab.ventureout.cz',failure=None):
        self.calls=[]
        @contextmanager
        def guard():
            self.calls.append('lock')
            try:yield
            finally:self.calls.append('unlock')
        def canary(stage):
            self.calls.append('canary-'+stage)
            if failure=='canary-'+stage:raise hook.HookFailure('test')
        def command(argv,timeout):
            self.assertEqual(timeout,10);self.calls.append(tuple(argv))
            if failure=='syntax' and argv==hook.COMMANDS[0]:raise hook.HookFailure('test')
            if failure=='reload' and argv==hook.COMMANDS[1]:raise TimeoutError('test')
        def loaded(lineage,name):
            self.calls.append('certificate-match');self.assertEqual(name,domain)
            if failure=='certificate':raise hook.HookFailure('test')
        return hook.perform({'RENEWED_LINEAGE':'/etc/letsencrypt/live/'+domain,'RENEWED_DOMAINS':domain},command,canary,loaded,guard)

    def test_each_owned_certificate_uses_guarded_single_graceful_reload(self):
        for domain in hook.LINEAGES.values():
            self.assertEqual(self.run_hook(domain)['status'],'VERIFIED_RELOAD')
            self.assertEqual(self.calls,['lock','canary-before',tuple(hook.COMMANDS[0]),tuple(hook.COMMANDS[1]),'certificate-match','canary-after','unlock'])

    def test_reference_or_syntax_failure_prevents_reload(self):
        for failure in ('canary-before','syntax'):
            with self.assertRaises(hook.HookFailure):self.run_hook(failure=failure)
            self.assertNotIn(tuple(hook.COMMANDS[1]),self.calls)
            self.assertEqual(self.calls[-1],'unlock')

    def test_post_reload_uncertainty_does_not_retry_or_restart(self):
        for failure in ('reload','certificate','canary-after'):
            with self.assertRaises((hook.HookFailure,TimeoutError)):self.run_hook(failure=failure)
            self.assertEqual(self.calls.count(tuple(hook.COMMANDS[1])),1)
            self.assertFalse(any('restart' in call for call in self.calls if isinstance(call,tuple)))
            self.assertEqual(self.calls[-1],'unlock')

    def test_unknown_lineage_and_domain_injection_cannot_dispatch(self):
        def deny(*args,**kwargs):raise AssertionError('No callback permitted')
        for lineage in ('','/etc/letsencrypt/live/unrelated','/etc/letsencrypt/live/lab.ventureout.cz/../other','x; command'):
            self.assertEqual(hook.perform({'RENEWED_LINEAGE':lineage},deny,deny,deny,deny)['status'],'SKIPPED_UNRELATED_CERTIFICATE')
        for value in ('','lab.ventureout.cz other.example','lab.ventureout.cz;command'):
            with self.assertRaises(hook.HookFailure):hook.perform({'RENEWED_LINEAGE':'/etc/letsencrypt/live/lab.ventureout.cz','RENEWED_DOMAINS':value},deny,deny,deny,deny)

    def test_show_plan_cannot_reload_and_execution_requires_flag(self):
        result=subprocess.run(['python3',str(ROOT/'deploy/certificate-deploy-hook.py'),'--show-plan'],capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,0);self.assertIn('PROPOSAL_NOT_INSTALLED',result.stdout)
        result=subprocess.run(['python3',str(ROOT/'deploy/certificate-deploy-hook.py')],capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,2)
