# tests/test_map_cli.py
import sys, os, unittest, tempfile, pathlib, subprocess
SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "index.md").write_text("# root\n", encoding="utf-8")
        (self.root / "a.md").write_text("---\ntype: Thing\n---\nx\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_writes_html(self):
        out = self.root / "viz.html"
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "okf_map.py"), str(self.root),
             "--out", str(out), "--name", "T"],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(out.exists())
        self.assertIn("<!doctype html", out.read_text(encoding="utf-8").lower())

if __name__ == "__main__":
    unittest.main()
