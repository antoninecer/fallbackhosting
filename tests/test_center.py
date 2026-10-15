"""Local-only center export, hostile text, atomic failure and snapshot semantics."""
import copy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('control_center', ROOT / 'center/build.py')
center = importlib.util.module_from_spec(spec)
spec.loader.exec_module(center)


class CenterTests(unittest.TestCase):
    def setUp(self):
        self.data = center.snapshot(now=datetime(2026,10,15,18,tzinfo=timezone.utc))

    def test_all_modules_and_unknown_activity_are_explicit(self):
        page = center.render(self.data)
        for section in ('prehled','ukoly','milniky','incidenty','zdravi','agent','postupy','navazani'):
            self.assertIn(f'id="{section}"',page)
        self.assertIn('Žádné incidenty nejsou zaznamenané',page)
        self.assertEqual(self.data['agent']['current_state'],'UNKNOWN')
        self.assertEqual(self.data['observations'][0]['current_state'],'UNKNOWN')
        self.assertIn('Není zaznamenaný',page)
        self.assertNotIn('ssh_transport',page)
        self.assertNotIn('initial-admin.json',page)
        self.assertNotIn('<form',page)

    def test_hostile_text_and_resume_cannot_inject_html(self):
        poison = '</textarea><script>alert("PRIVATE_XSS")</script><img src=x onerror=alert(1)>'
        data = copy.deepcopy(self.data)
        for field in ('title','scope','acceptance','rollback','owner'):
            data['tasks'][0][field] = poison
        current = next(t for t in data['tasks'] if t['id']==data['current_task'])
        current['acceptance'] = poison
        page = center.render(data)
        self.assertNotIn('<script>alert',page)
        self.assertNotIn('<img src=x',page)
        self.assertIn('&lt;script&gt;',page)
        self.assertEqual(page.count('</textarea>'),1)

    def test_resume_contains_required_reading_actual_ids_and_safety(self):
        text = center.resume_prompt(self.data)
        for name in ('AGENTS.md','PROJECT.md','ARCHITECTURE.md','STATE.md','TASKS.md','SECURITY.md','RUNBOOK.md',self.data['checkpoint'],self.data['current_task']):
            self.assertIn(name,text)
        self.assertIn('není důkaz běžícího agenta',text)
        self.assertNotIn('ssh_transport',text)
        self.assertNotIn('initial-admin',text)

    def test_stale_health_and_agent_never_look_current(self):
        data = copy.deepcopy(self.data)
        data['agent']['current_state']='STALE'
        data['observations'][0]['current_state']='STALE'
        self.assertGreaterEqual(center.render(data).count('Zastaralé'),2)
        data['incidents']=[]
        data['observations']=[]
        self.assertIn('Žádná pozorování. Stav je neznámý.',center.render(data))

    def test_builder_refuses_public_output(self):
        with self.assertRaises(ValueError):
            center.build(ROOT / 'public/center')

    def test_atomic_build_manifest_and_failed_build_preserve_known_good(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(center,'snapshot',return_value=self.data):
                release = center.build(root=root)
            current = root / '.local/control-center/current'
            self.assertEqual(current.resolve(),release)
            self.assertEqual({p.name for p in release.iterdir()}, {'index.html','center.css','center.js','resume.txt','manifest.json'})
            self.assertEqual(set(json.loads((release/'manifest.json').read_text())), {'index.html','center.css','center.js','resume.txt'})
            with patch.object(center,'snapshot',side_effect=ValueError('Invalid source')):
                with self.assertRaises(ValueError): center.build(root=root)
            self.assertEqual(current.resolve(),release)
            self.assertEqual((release/'resume.txt').read_text(),center.resume_prompt(self.data))

    def test_modified_immutable_release_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(center,'snapshot',return_value=self.data):
                release = center.build(root=root)
                (release/'index.html').write_text('CORRUPTED')
                with self.assertRaises(ValueError): center.build(root=root)

    def test_snapshot_does_not_export_raw_session_fields(self):
        original = center.json.loads
        def poisoned(value,*args,**kwargs):
            data = original(value,*args,**kwargs)
            if isinstance(data,dict) and data.get('project')=='FallbackHosting':
                data.update(private_key='PRIVATE_KEY_MARKER',current_summary='PRIVATE_RAW_SUMMARY')
                data['ssh_transport']={'PRIVATE_RAW_TRANSPORT':'PRIVATE'}
            return data
        with patch.object(center.json,'loads',side_effect=poisoned):
            data = center.snapshot()
        self.assertNotIn('PRIVATE_',json.dumps(data))
