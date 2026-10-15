"""Public export boundary, malformed source handling and local serving checks."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("portal_build", ROOT / "portal/build.py")
portal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(portal)

class PublicPortalTests(unittest.TestCase):
    def test_prague_time_handles_summer_winter_and_dst_transition(self):
        self.assertEqual(portal.prague_time("2026-10-15T14:24:00Z"), "15. 10. 2026 16:24:00 · Praha (CEST)")
        self.assertEqual(portal.prague_time("2026-12-15T14:24:00+00:00"), "15. 12. 2026 15:24:00 · Praha (CET)")
        self.assertEqual(portal.prague_time("2026-10-25T00:30:00Z"), "25. 10. 2026 02:30:00 · Praha (CEST)")
        self.assertEqual(portal.prague_time("2026-10-25T01:30:00Z"), "25. 10. 2026 02:30:00 · Praha (CET)")
        with self.assertRaises(ValueError):
            portal.prague_time("2026-10-15T14:24:00")

    def test_render_displays_prague_but_preserves_utc_datetime(self):
        data = portal.public_data()
        data["events"] = [{"title":"Test", "utc":"2026-10-15T14:24:00Z"}]
        page = portal.render(data)
        self.assertIn('<time datetime="2026-10-15T14:24:00Z">15. 10. 2026 16:24:00 · Praha (CEST)</time>', page)
        self.assertIn("Čas checkpointu (Praha)", page)
        self.assertNotIn("Vygenerování stránky (UTC)", page)

    def fixture(self, directory):
        root = Path(directory)
        for name in ("ROADMAP.md", "TASKS.md", "state/current.json"):
            dest = root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text((ROOT / name).read_text())
        state = json.loads((root / "state/current.json").read_text())
        checkpoint = root / state["last_checkpoint"]
        checkpoint.parent.mkdir(parents=True)
        checkpoint.write_text("PRIVATE_CHECKPOINT_MARKER")
        return root

    def test_only_allowlisted_data_reaches_export(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(temp)
            p = root / "state/current.json"
            state = json.loads(p.read_text())
            state["current_summary"] = "PRIVATE_STATE_MARKER"
            state["warnings"] = ["PRIVATE_WARNING_MARKER"]
            state["ssh_transport"] = {"private_inventory": "PRIVATE_SSH_MARKER"}
            state["operations_service"] = {"private_policy": "PRIVATE_POLICY_MARKER"}
            p.write_text(json.dumps(state))
            tasks = root / "TASKS.md"
            tasks.write_text(tasks.read_text().replace("Operator + Codex", "PRIVATE_OWNER_MARKER"))
            exported = portal.render(portal.public_data(root))
            self.assertNotIn("PRIVATE_", exported)
            self.assertNotIn("/opt/", exported)
            self.assertNotIn("<form", exported)

    def test_invalid_status_and_unknown_task_fail_closed(self):
        for replacement in ("INVALID", "DONE | extra"):
            with self.subTest(replacement=replacement), tempfile.TemporaryDirectory() as temp:
                root = self.fixture(temp)
                p = root / "TASKS.md"
                p.write_text(p.read_text().replace("| FH-0001 | M00 | DONE |", f"| FH-0001 | M00 | {replacement} |"))
                with self.assertRaises(ValueError):
                    portal.public_data(root)
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(temp)
            p = root / "TASKS.md"
            p.write_text(p.read_text() + "\n| FH-9999 | M02 | READY | anyone | secret |\n")
            with self.assertRaises(ValueError):
                portal.public_data(root)

    def test_public_events_require_reviewed_ids_and_valid_timestamps(self):
        for event in ({"id":"PRIVATE_UNKNOWN","utc":"2026-10-15T11:00:00Z"},
                      {"id":"admin_prepare_pass","utc":"invalid"},
                      {"id":"admin_prepare_pass","utc":"2026-10-15T11:00:00Z","raw":"PRIVATE"}):
            with self.subTest(event=event), tempfile.TemporaryDirectory() as temp:
                root=self.fixture(temp)
                path=root/"state/current.json"
                state=json.loads(path.read_text());state["public_events"]=[event]
                path.write_text(json.dumps(state))
                with self.assertRaises(ValueError): portal.public_data(root)

    def test_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(temp)
            p = root / "state/current.json"
            state = json.loads(p.read_text())
            state["last_checkpoint"] = "../private.md"
            p.write_text(json.dumps(state))
            with self.assertRaises(ValueError):
                portal.public_data(root)

    def test_render_escapes_text_and_build_excludes_repository(self):
        data = portal.public_data()
        data["tasks"][0]["title"] = '<script>alert("x")</script>'
        self.assertNotIn('<script>alert', portal.render(data))
        self.assertIn("&lt;script&gt;", portal.render(data))
        with tempfile.TemporaryDirectory() as temp:
            portal.build(Path(temp))
            self.assertEqual({p.name for p in Path(temp).iterdir()}, {"index.html", "style.css", "app.js"})

    def test_lab_is_separate_static_landing_without_admin(self):
        with tempfile.TemporaryDirectory() as temp:
            portal.build_lab(Path(temp))
            self.assertEqual({p.name for p in Path(temp).iterdir()}, {"index.html", "style.css"})
            body = (Path(temp) / "index.html").read_text()
            self.assertIn("https://project.lab.ventureout.cz/", body)
            self.assertIn("nasazování zatím není dostupné", body)
            self.assertNotIn("<form", body)
            self.assertNotIn("/opt/", body)

if __name__ == "__main__":
    unittest.main()
