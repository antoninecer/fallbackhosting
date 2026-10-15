"""Adversarial data validation, freshness, migration and export failure safety."""
import copy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('portal_model_tests', ROOT / 'portal/build.py')
portal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(portal)
model = portal.model


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = model.load(ROOT)

    def reject(self, mutate):
        candidate = copy.deepcopy(self.catalog)
        mutate(candidate)
        with self.assertRaises(ValueError):
            model.validate(candidate, ROOT)

    def test_migration_preserves_all_existing_ids_and_generated_tables(self):
        self.assertEqual([m['id'] for m in self.catalog['milestones']], [f'M{i:02}' for i in range(11)])
        self.assertEqual([t['id'] for t in self.catalog['tasks'][:18]], [f'FH-{i:04}' for i in range(1, 19)])
        self.assertEqual(len({t['id'] for t in self.catalog['tasks']}),len(self.catalog['tasks']))
        model.sync_markdown(ROOT, self.catalog)

    def test_committed_status_and_history_cannot_be_silently_rewritten(self):
        before = copy.deepcopy(self.catalog)
        after = copy.deepcopy(before)
        after['tasks'][1]['status'] = 'IN_PROGRESS' if before['tasks'][1]['status']=='READY' else 'READY'
        with self.assertRaises(ValueError): model.validate_change(before, after)
        after = copy.deepcopy(before)
        after['tasks'][5]['history'] = []
        with self.assertRaises(ValueError): model.validate_change(before, after)
        after = copy.deepcopy(before)
        after['tasks'] = after['tasks'][1:]
        with self.assertRaises(ValueError): model.validate_change(before, after)
        after = copy.deepcopy(before)
        after['tasks'][0]['evidence'] = []
        with self.assertRaises(ValueError): model.validate_change(before, after)
        model.validate_change(before, copy.deepcopy(before))

    def test_broken_reference_duplicate_and_dependency_cycle_rejected(self):
        self.reject(lambda c: c['tasks'][0].update(milestone='M99'))
        self.reject(lambda c: c['tasks'][0].update(dependencies=['FH-9999']))
        self.reject(lambda c: c['tasks'][1].update(id=c['tasks'][0]['id']))
        def cycle(c):
            c['tasks'][0]['dependencies'] = [c['tasks'][1]['id']]
            c['tasks'][1]['dependencies'] = [c['tasks'][0]['id']]
        self.reject(cycle)

    def test_done_requires_existing_evidence_timestamp_and_revision(self):
        self.reject(lambda c: c['tasks'][0].update(evidence=[]))
        self.reject(lambda c: c['tasks'][0].update(evidence=['checkpoints/missing.md']))
        self.reject(lambda c: c['tasks'][0].update(completed_at_utc=None))
        self.reject(lambda c: c['tasks'][0].update(completion_revision='UNKNOWN'))
        self.reject(lambda c: c['tasks'][1].update(completion_revision='0' * 40))

    def test_transitions_cannot_skip_testing_or_reopen_done(self):
        def history(c, before, after):
            c['tasks'][5]['history'] = [dict(**{'from':before}, to=after, utc='2026-10-15T14:30:36Z', evidence=['checkpoints/20261015T143036Z-FH-0006-start.md'])]
        self.reject(lambda c: history(c, 'READY', 'DONE'))
        self.reject(lambda c: history(c, 'DONE', 'IN_PROGRESS'))
        self.reject(lambda c: history(c, 'BACKLOG', 'READY'))  # mismatches current state
        self.reject(lambda c: c['tasks'][5]['history'][0].update(evidence=[]))

    def test_unknown_fields_and_unsafe_evidence_rejected(self):
        self.reject(lambda c: c['tasks'][0].update(private_key='PRIVATE'))
        self.reject(lambda c: c['tasks'][0].update(evidence=['../private.md']))
        self.reject(lambda c: c['tasks'][0].update(evidence=['.local/operator/initial-admin.json']))
        self.reject(lambda c: c.update(schema_version=True))
        self.reject(lambda c: c['tasks'][0].update(title='bad | table\nrow'))

    def test_malformed_and_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'state'
            path.mkdir()
            for content in ('{', '{"schema_version":1,"schema_version":2}'):
                (path / 'catalog.json').write_text(content)
                with self.assertRaises(ValueError):
                    model.load(Path(temp))

    def test_health_expiry_missing_time_and_future_are_explicit(self):
        now = datetime(2026, 10, 15, 15, tzinfo=timezone.utc)
        observation = dict(self.catalog['observations'][0], provenance='OBSERVED', observed_at_utc='2026-10-15T14:00:00Z', expires_at_utc='2026-10-15T15:00:00Z')
        self.assertEqual(model.observation_state(observation, now), 'STALE')
        observation['expires_at_utc'] = '2026-10-15T16:00:00Z'
        self.assertEqual(model.observation_state(observation, now), 'PASS')
        observation['observed_at_utc'] = '2026-10-15T15:30:00Z'
        self.assertEqual(model.observation_state(observation, now), 'UNKNOWN')
        observation['expires_at_utc'] = None
        self.assertEqual(model.observation_state(observation, now), 'UNKNOWN')
        self.assertEqual(model.observation_state(self.catalog['observations'][0], now), 'UNKNOWN')

    def test_observation_needs_provenance_and_evidence(self):
        self.reject(lambda c: c['observations'][0].update(provenance='OBSERVED', evidence=[]))
        self.reject(lambda c: c['observations'][0].update(provenance='PLANNED', status='PASS'))
        self.reject(lambda c: c['observations'][0].update(expires_at_utc='2026-01-01T00:00:00Z'))
        self.reject(lambda c: c['observations'][0].update(dependencies=['OBS-9999']))

    def test_agent_never_claims_execution_from_task_status(self):
        now = datetime(2026, 10, 15, 15, tzinfo=timezone.utc)
        agent = dict(self.catalog['agent'], session_ended=False, heartbeat_utc=None)
        self.assertEqual(model.agent_state(agent, now), 'UNKNOWN')
        agent['heartbeat_utc'] = '2026-10-15T14:56:00Z'
        self.assertEqual(model.agent_state(agent, now), 'RECENT')
        agent['heartbeat_utc'] = '2026-10-15T14:55:00Z'
        self.assertEqual(model.agent_state(agent, now), 'STALE')
        agent['heartbeat_utc'] = '2026-10-15T15:01:00Z'
        self.assertEqual(model.agent_state(agent, now), 'UNKNOWN')
        agent['session_ended'] = True
        self.assertEqual(model.agent_state(agent, now), 'STOPPED')

    def test_failed_build_preserves_last_valid_page(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'public'
            output.mkdir()
            (output / 'index.html').write_text('KNOWN_GOOD')
            bad_root = Path(temp) / 'bad'
            (bad_root / 'state').mkdir(parents=True)
            (bad_root / 'state/catalog.json').write_text('{')
            with self.assertRaises(ValueError):
                portal.build(output, root=bad_root)
            self.assertEqual((output / 'index.html').read_text(), 'KNOWN_GOOD')

    def test_untrusted_catalog_text_never_reaches_public_export(self):
        # Reviewed labels, not title/acceptance/owner strings, are public.
        original = model.load
        def poisoned(root):
            candidate = copy.deepcopy(self.catalog)
            candidate['tasks'][0].update(title='<script>PRIVATE_TITLE</script>', owner='PRIVATE_OWNER', acceptance='PRIVATE_ACCEPTANCE')
            return candidate
        original_sync = model.sync_markdown
        try:
            model.load = poisoned
            model.sync_markdown = lambda *a, **kw: None
            page = portal.render(portal.public_data(ROOT))
            self.assertNotIn('PRIVATE_', page)
        finally:
            model.load = original
            model.sync_markdown = original_sync
