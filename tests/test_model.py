# tests/test_model.py
import sys, os, unittest, tempfile, pathlib
from datetime import datetime, timezone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_model as om

def write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        write(self.root, "index.md", "# root\n* [A](/a.md)\n")
        write(self.root, "a.md", "---\ntype: Thing\ntimestamp: 2026-06-01T00:00:00Z\n---\n[B](/b.md)\n")
        write(self.root, "orphan.md", "---\ntype: Thing\ntimestamp: 2020-01-01T00:00:00Z\n---\nx\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_model_files_and_links(self):
        m = om.build_model(self.root)
        self.assertIn("a", m["files"])
        self.assertEqual(m["files"]["a"]["type"], "Thing")
        broken = [l for l in m["links"] if not l["resolved"]]
        self.assertTrue(any(l["target"] == "/b.md" for l in broken))

    def test_orphans(self):
        m = om.build_model(self.root)
        self.assertIn("orphan", om.orphans(m))
        self.assertNotIn("a", om.orphans(m))  # linked from index

    def test_stale(self):
        m = om.build_model(self.root)
        now = datetime(2026, 6, 14, tzinfo=timezone.utc)
        stale_ids = [s["id"] for s in om.stale(m, 180, now=now)]
        self.assertIn("orphan", stale_ids)
        self.assertNotIn("a", stale_ids)

if __name__ == "__main__":
    unittest.main()
