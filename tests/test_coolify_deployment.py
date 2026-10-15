"""Regression checks for the reviewed private-only controller deployment."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CoolifyDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'deploy/coolify-compose.json').read_text())

    def test_only_controller_ports_are_published_on_loopback(self):
        services = self.config['services']
        self.assertEqual(set(services), {'coolify', 'postgres', 'redis'})
        self.assertEqual(services['coolify']['ports'], [
            '127.0.0.1:8000:8080', '127.0.0.1:6001:6001', '127.0.0.1:6002:6002'])
        for name in ('postgres', 'redis'):
            self.assertFalse(services[name].get('ports'))

    def test_runtime_services_cannot_mount_host_socket_or_privileged_paths(self):
        for service in self.config['services'].values():
            self.assertFalse(service.get('privileged'))
            self.assertNotEqual(service.get('network_mode'), 'host')
            self.assertNotEqual(service.get('pid'), 'host')
            for volume in service.get('volumes', []):
                source = volume['source'] if isinstance(volume, dict) else volume.split(':')[0]
                self.assertTrue(source.startswith('/data/coolify/') or source in {'coolify-db', 'coolify-redis'})

    def test_images_are_pinned_and_logs_resources_bounded(self):
        for service in self.config['services'].values():
            self.assertRegex(service['image'], r'^[a-z0-9/-]+@sha256:[a-f0-9]{64}$')
            self.assertGreater(service['cpus'], 0)
            self.assertLessEqual(service['cpus'], 1)
            self.assertGreater(service['pids_limit'], 0)
            self.assertIn(service['logging']['options']['max-file'], {'2', '3'})
            self.assertEqual(service['logging']['options']['max-size'], '10m')
            self.assertEqual(service['labels']['io.fallback.app'], 'coolify-control')
