from dataclasses import replace
import unittest

from operations.access import Grant, Identity, Policy
from operations.core import Denied


class ApplicationAccessTests(unittest.TestCase):
    def setUp(self):
        self.identity = Identity('alice', 'session-one', 1, 2000, True, strong_verified=True)
        self.grant = Grant('alice', 'node-one', 'project-one', 'app-one', 'manager')
        self.policy = Policy(1, [self.grant])

    def check(self, action, identity=None, policy=None, **scope):
        return (policy or self.policy).authorize(identity or self.identity,
            scope.get('node', 'node-one'), scope.get('project', 'project-one'),
            scope.get('app', 'app-one'), action, 1000)

    def test_manager_operations_remain_subject_to_broker_approval(self):
        self.assertFalse(self.check('inspect').requires_write_approval)
        self.assertTrue(self.check('restart').requires_write_approval)
        for action in ('remove', 'delete_data', 'assign_members', 'exec', 'provision_vm'):
            with self.subTest(action=action), self.assertRaises(Denied):
                self.check(action)

    def test_each_scope_dimension_is_enforced(self):
        for scope in ({'node': 'other'}, {'project': 'other'}, {'app': 'other'}):
            for action in ('inspect', 'restart', 'job_status'):
                with self.subTest(scope=scope, action=action), self.assertRaises(Denied):
                    self.check(action, **scope)

    def test_observer_and_log_permission_are_independent(self):
        policy = Policy(2, [replace(self.grant, role='observer')])
        self.check('inspect', policy=policy)
        for action in ('restart', 'deploy', 'logs'):
            with self.assertRaises(Denied):
                self.check(action, policy=policy)
        self.check('logs', policy=Policy(3, [replace(self.grant, role='observer', logs=True)]))
        with self.assertRaises(Denied):
            self.check('logs')

    def test_admin_destructive_actions_need_fresh_verification(self):
        admin = replace(self.identity, platform_admin=True)
        for action in ('remove', 'delete_data', 'assign_members'):
            with self.assertRaises(Denied):
                self.check(action, identity=admin)
            self.assertTrue(self.check(action, identity=replace(admin, verified_at=999)).requires_write_approval)
            for stamp in (700, 1001):
                with self.assertRaises(Denied):
                    self.check(action, identity=replace(admin, verified_at=stamp))

    def test_weak_session_cannot_write_even_with_app_membership(self):
        weak = replace(self.identity, strong_verified=False)
        self.check('inspect', identity=weak)
        with self.assertRaisesRegex(Denied, 'STRONG_VERIFICATION_REQUIRED'):
            self.check('restart', identity=weak)

    def test_revoked_expired_or_changed_identity_invalidates_pending(self):
        pending = self.check('restart')
        self.policy.recheck(pending, self.identity, 1001)
        for identity in (replace(self.identity, active=False), replace(self.identity, expires_at=1000),
                         replace(self.identity, revision=2), replace(self.identity, session='session-two'),
                         replace(self.identity, principal='bob')):
            with self.subTest(identity=identity), self.assertRaises(Denied):
                self.policy.recheck(pending, identity, 1001)

    def test_membership_or_policy_change_invalidates_pending(self):
        pending = self.check('restart')
        for policy in (Policy(2, []), Policy(2, [replace(self.grant, role='observer')]),
                       Policy(2, [self.grant])):
            with self.assertRaises(Denied):
                policy.recheck(pending, self.identity, 1001)

    def test_duplicate_policy_or_raw_browser_identity_rejected(self):
        with self.assertRaises(Denied):
            Policy(1, [self.grant, self.grant])
        with self.assertRaises(Denied):
            self.policy.authorize({'principal': 'alice', 'platform_admin': True},
                                  'node-one', 'project-one', 'app-one', 'remove', 1000)
