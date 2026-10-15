"""Offline provider selection from trusted inventory. No execution or credentials.

This model does not authorize jobs or implement a production adapter. Existing
broker authorization and write approvals remain mandatory for real operations.
"""
from dataclasses import dataclass
from types import MappingProxyType

from operations.core import Denied, identifier


@dataclass(frozen=True)
class Target:
    id: str
    role: str
    provider: str


# Products/APIs reused by future adapters; none is an installed driver here.
CAPABILITIES = MappingProxyType({
    ('application_node', 'coolify-docker'): frozenset({'deploy_app'}),
    ('virtualization_host', 'proxmox'): frozenset({'provision_vm', 'backup_vm', 'restore_vm'}),
    ('virtualization_host', 'libvirt-kvm'): frozenset({'provision_vm', 'backup_vm', 'restore_vm'}),
})
ACTIONS = frozenset(action for actions in CAPABILITIES.values() for action in actions)


class Planner:
    def __init__(self, targets):
        inventory = {}
        for target in targets:
            if not isinstance(target, Target):
                raise Denied('INVALID_TARGET')
            identifier(target.id)
            if target.id in inventory or (target.role, target.provider) not in CAPABILITIES:
                raise Denied('INVALID_PROVIDER_INVENTORY')
            inventory[target.id] = target
        self.targets = MappingProxyType(inventory)

    def plan(self, request):
        if not isinstance(request, dict) or set(request) != {'action', 'target', 'resource'}:
            raise Denied('INVALID_FIELDS')
        for key in ('target', 'resource'):
            identifier(request[key])
        if not isinstance(request['action'], str) or request['action'] not in ACTIONS:
            raise Denied('UNSUPPORTED_OPERATION')
        target = self.targets.get(request['target'])
        if target is None:
            raise Denied('UNKNOWN_TARGET')
        if request['action'] not in CAPABILITIES[target.role, target.provider]:
            raise Denied('WRONG_TARGET_CAPABILITY')
        action = request['action']
        return {
            'action': action, 'target': target.id, 'resource': request['resource'],
            'provider': target.provider,
            'mode': 'OFFLINE_PLAN_ONLY', 'driver_state': 'NOT_IMPLEMENTED',
            'execution_allowed': False,
            'required_gates': [
                'current_resource_authorization', 'approved_exact_scope',
                'protected_provider_credentials', 'verified_provider_capabilities',
                'tested_driver_and_rollback',
            ] + (['backup_destination_and_coverage', 'consistency_policy', 'restore_test']
                 if action in {'backup_vm', 'restore_vm'} else [])
              + (['isolated_restore_target', 'no_existing_resource_overwrite']
                 if action == 'restore_vm' else []),
        }
