import unittest

from operations.core import Denied
from operations.planning import Planner, Target


class ProviderPlanningTests(unittest.TestCase):
    def setUp(self):
        self.planner = Planner([
            Target('demo-docker', 'application_node', 'coolify-docker'),
            Target('demo-pve', 'virtualization_host', 'proxmox'),
            Target('demo-kvm', 'virtualization_host', 'libvirt-kvm'),
        ])

    def test_docker_application_needs_no_hypervisor(self):
        planner = Planner([Target('plain-linux', 'application_node', 'coolify-docker')])
        plan = planner.plan({'action': 'deploy_app', 'target': 'plain-linux', 'resource': 'demo'})
        self.assertEqual(plan['provider'], 'coolify-docker')
        self.assertFalse(plan['execution_allowed'])
        self.assertEqual(plan['driver_state'], 'NOT_IMPLEMENTED')

    def test_vm_provider_selected_from_trusted_target_only(self):
        for target, provider in [('demo-pve', 'proxmox'), ('demo-kvm', 'libvirt-kvm')]:
            plan = self.planner.plan({'action': 'provision_vm', 'target': target, 'resource': 'demo-vm'})
            self.assertEqual(plan['provider'], provider)
            self.assertFalse(plan['execution_allowed'])

    def test_wrong_layer_unknown_target_and_provider_override_fail(self):
        requests = [
            {'action': 'provision_vm', 'target': 'demo-docker', 'resource': 'demo'},
            {'action': 'deploy_app', 'target': 'demo-pve', 'resource': 'demo'},
            {'action': 'backup_vm', 'target': 'missing', 'resource': 'demo'},
            {'action': 'snapshot', 'target': 'demo-kvm', 'resource': 'demo'},
            {'action': 'deploy_app', 'target': 'demo-docker', 'resource': 'demo', 'provider': 'libvirt-kvm'},
            {'action': 'deploy_app', 'target': 'demo-docker', 'resource': 'demo;reboot'},
        ]
        for request in requests:
            with self.subTest(request=request), self.assertRaises(Denied):
                self.planner.plan(request)

    def test_restore_requires_independent_target_and_coverage_gates(self):
        plan = self.planner.plan({'action': 'restore_vm', 'target': 'demo-kvm', 'resource': 'demo'})
        for gate in ('isolated_restore_target', 'no_existing_resource_overwrite',
                     'consistency_policy', 'backup_destination_and_coverage', 'restore_test'):
            self.assertIn(gate, plan['required_gates'])

    def test_duplicate_or_unknown_provider_is_not_accepted(self):
        for targets in [
            [Target('same', 'application_node', 'coolify-docker')] * 2,
            [Target('demo', 'virtualization_host', 'shell')],
        ]:
            with self.assertRaises(Denied):
                Planner(targets)
