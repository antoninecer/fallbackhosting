import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('release_check', ROOT / 'scripts/verify-center-release.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.release = Path(self.temp.name) / 'release'
        self.release.mkdir(mode=0o755)
        self.revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        for name, source in checker.SOURCES.items():
            path = self.release / name
            path.parent.mkdir(mode=0o755, exist_ok=True)
            path.write_bytes(subprocess.check_output(['git', 'show', self.revision + ':' + source], cwd=ROOT))
            path.chmod(0o644)
        artifact = self.release / 'center-artifact'
        artifact.mkdir(mode=0o755)
        manifest = {}
        for name in checker.LIMITS:
            body = (' '.join('"/?center=' + x + '"' for x in ('center.css', 'center.js', 'resume.txt'))
                    if name == 'index.html' else 'fixture')
            (artifact / name).write_text(body)
            (artifact / name).chmod(0o644)
            manifest[name] = hashlib.sha256(body.encode()).hexdigest()
        raw = json.dumps(manifest).encode()
        (artifact / 'manifest.json').write_bytes(raw)
        (artifact / 'manifest.json').chmod(0o644)
        self.digest = hashlib.sha256(raw).hexdigest()

    def verify(self):
        return checker.verify(self.release, self.revision, self.digest)

    def test_exact_pinned_release_only_reports_offline_checks(self):
        result = self.verify()
        self.assertEqual(result['source'], 'PASS')
        self.assertEqual(result['activation'], 'NOT_PERFORMED')
        self.assertEqual(result['runtime_auth_canaries_rollback'], 'NOT_TESTED')

    def test_source_or_artifact_tamper_rejected(self):
        for name in ('lib.php', 'center-artifact/center.js', 'center-artifact/manifest.json'):
            with self.subTest(name=name):
                path = self.release / name
                original = path.read_bytes()
                path.write_bytes(original + b'!')
                with self.assertRaises(ValueError):
                    self.verify()
                path.write_bytes(original)

    def test_extra_file_symlink_and_permissions_rejected(self):
        extra = self.release / 'public/private.json'
        extra.write_text('{}')
        with self.assertRaises(ValueError):
            self.verify()
        extra.unlink()
        link = self.release.parent / 'link'
        link.symlink_to(self.release, target_is_directory=True)
        with self.assertRaises(ValueError):
            checker.verify(link, self.revision, self.digest)
        path = self.release / 'lib.php'
        path.chmod(0o666)
        with self.assertRaises(ValueError):
            self.verify()

    def test_missing_file_wrong_pin_and_short_revision_rejected(self):
        with self.assertRaises(ValueError):
            checker.verify(self.release, self.revision[:8], self.digest)
        with self.assertRaises(ValueError):
            checker.verify(self.release, self.revision, '0' * 64)
        (self.release / 'center.php').unlink()
        with self.assertRaises(ValueError):
            self.verify()
