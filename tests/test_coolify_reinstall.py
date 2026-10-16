import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from operations import install_worker

ROOT=Path(__file__).resolve().parents[1]

class CoolifyReinstallTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('coolify_trial',ROOT/'operations/coolify_reinstall.py')
        self.driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.driver)
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.j=Path(self.temp.name);self.driver.journal=self.j
        (self.j/'wizard-removal-done.json').write_text('{}')
        self.template=json.loads((ROOT/'deploy/coolify-compose.json').read_text())
        raw=json.dumps(self.template).encode();(self.j/'compose.json').write_bytes(raw)
        (self.j/'wizard-removal-started.json').write_text('{"others":[]}')
        self.driver.PAYLOAD=dict(email='operator@example.org',password='Fixture-Sensitive9!Password',compose_sha256=hashlib.sha256(raw).hexdigest())
        self.commands=[]

    def run_command(self,args,timeout=30,env=None):
        self.commands.append((args,env))
        if 'cat' in args: return (self.j/'compose.json').read_text()
        if args[:3]==['docker','volume','inspect']:
            return json.dumps([dict(Labels={'io.fallback.app':'coolify-control'})]*2)
        if 'config' in args:
            services={k:dict(image=v['image']) for k,v in self.template['services'].items()}
            services['coolify']['environment']=dict(AUTOUPDATE='false',NGINX_LISTEN_IP_PROTOCOL='ipv4')
            return json.dumps(dict(services=services))
        if args[:3]==['docker','container','inspect']:
            return json.dumps([dict(Id=str(i),Name='/'+n,Config=dict(Labels={'io.fallback.app':'coolify-control','io.fallback.managed':'true'}),State=dict(Health=dict(Status='healthy'))) for i,n in enumerate(self.driver.NAMES)])
        return ''

    def test_complete_native_bootstrap_uses_fixed_argv_and_secret_environment_only(self):
        responses=[dict(users=0),dict(admin_created=True,registration_disabled=True)]
        with patch.object(self.driver,'run',side_effect=self.run_command),patch.object(self.driver.subprocess,'run',return_value=SimpleNamespace(returncode=1)),patch.object(self.driver,'query',side_effect=responses),patch.object(self.driver.urllib.request,'urlopen') as health:
            health.return_value.__enter__.return_value.status=200
            self.driver.main()
        args,env=next(x for x in self.commands if 'db:seed' in x[0])
        self.assertNotIn(self.driver.PAYLOAD['password'],' '.join(args))
        self.assertNotIn(self.driver.PAYLOAD['email'],' '.join(args))
        self.assertEqual(env['ROOT_USER_PASSWORD'],self.driver.PAYLOAD['password'])
        self.assertTrue((self.j/'owned-containers.json').is_file())

    def test_existing_container_or_wrong_template_prevents_any_creation(self):
        with patch.object(self.driver.subprocess,'run',return_value=SimpleNamespace(returncode=0)),patch.object(self.driver,'run') as command:
            with self.assertRaises(AssertionError):self.driver.main()
            command.assert_not_called()
        self.driver.PAYLOAD['compose_sha256']='0'*64
        with patch.object(self.driver,'run') as command:
            with self.assertRaises(AssertionError):self.driver.main()
            command.assert_not_called()

    def test_ssh_mapping_and_payload_cannot_become_shell_arguments(self):
        policy=dict(host='192.0.2.5',ssh_user='service',ssh_port=22,compose_sha256='0'*64)
        secret=dict(email='operator@example.org',password='Special9!$(touch /tmp/NEVER);')
        with patch.object(install_worker.subprocess,'run') as command:
            command.return_value.stdout='{}'
            install_worker.ssh_driver(policy,'# fixed source',secret)
            args=command.call_args.args[0]
            self.assertNotIn(secret['password'],' '.join(args))
            self.assertFalse(command.call_args.kwargs.get('shell',False))
            self.assertIn('StrictHostKeyChecking=yes',args)
            self.assertNotIn(secret['password'],command.call_args.kwargs['input'])
        with patch.object(install_worker.subprocess,'run') as command:
            with self.assertRaises(ValueError):install_worker.ssh_driver(dict(policy,host='-oProxyCommand=evil'),'# fixed',secret)
            command.assert_not_called()

if __name__=='__main__':unittest.main()
