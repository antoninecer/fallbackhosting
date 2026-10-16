import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/generate-admin-credential.py'
spec = importlib.util.spec_from_file_location('credential_generator', SCRIPT)
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class CredentialsTest(unittest.TestCase):
    def test_default_and_boundaries_have_every_required_category(self):
        for length in (16, 20, 128):
            for _ in range(100):
                password = generator.generate_password(length)
                self.assertEqual(len(password), length)
                self.assertTrue(all(any(c in group for c in password) for group in generator.GROUPS))
        self.assertEqual(len(generator.generate_password()), 16)
        for length in (True, 0, 15, 129):
            with self.assertRaises(ValueError):
                generator.generate_password(length)

    def test_private_file_no_stdout_secret_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'credential.json'
            result = subprocess.run(['python3', str(SCRIPT), '--output', str(path)], capture_output=True, text=True, check=True)
            secret = json.loads(path.read_text())['password']
            self.assertNotIn(secret, result.stdout + result.stderr)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            before = path.read_bytes()
            retry = subprocess.run(['python3', str(SCRIPT), '--output', str(path)], capture_output=True)
            self.assertNotEqual(retry.returncode, 0)
            self.assertEqual(path.read_bytes(), before)
            Path(tmp).chmod(0o755)
            unsafe = subprocess.run(['python3', str(SCRIPT), '--output', str(Path(tmp)/'unsafe.json')], capture_output=True)
            self.assertNotEqual(unsafe.returncode, 0)
            self.assertFalse((Path(tmp)/'unsafe.json').exists())
