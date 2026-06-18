# tests/test_move_cli.py
import sys, os, unittest, tempfile, pathlib, json, subprocess
SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")

def write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

def run(*args):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "okf_move.py"), *args],
                          capture_output=True, text=True)

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        write(self.root, "index.md", "# Bundle\n")
        write(self.root, "log.md", "# Bundle Log\n")
        write(self.root, "old.md", "---\ntype: Thing\ntitle: Old\n---\nbody\n")
        write(self.root, "ref.md",
              "---\ntype: Thing\ntitle: Ref\n---\nsee [Old](/old.md) and keep text.\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_dry_run_reports_backlinks(self):
        proc = run("old.md", "archive/old.md", "--bundle", str(self.root),
                   "--dry-run", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["move"], {"from": "old", "to": "archive/old"})
        self.assertTrue(any(b["id"] == "ref" for b in data["backlinks"]))
        self.assertTrue((self.root / "old.md").exists())   # nothing moved yet

    def test_move_rewrites_backlinks_and_relocates(self):
        proc = run("old.md", "archive/old.md", "--bundle", str(self.root), "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertFalse((self.root / "old.md").exists())
        self.assertTrue((self.root / "archive" / "old.md").exists())
        ref = (self.root / "ref.md").read_text(encoding="utf-8")
        self.assertIn("[Old](/archive/old.md)", ref)       # rewritten
        self.assertIn("and keep text.", ref)                # surrounding bytes intact
        self.assertIn("[Old](old.md)",
                      (self.root / "archive" / "index.md").read_text(encoding="utf-8"))

    def test_rejects_dest_outside_bundle(self):
        proc = run("old.md", "../escape.md", "--bundle", str(self.root))
        self.assertEqual(proc.returncode, 2)
        self.assertTrue((self.root / "old.md").exists())   # untouched

    def test_refuses_moving_reserved_file(self):
        proc = run("index.md", "moved-index.md", "--bundle", str(self.root))
        self.assertEqual(proc.returncode, 2)
        self.assertTrue((self.root / "index.md").exists())

    def test_no_backlinks_move_still_relocates(self):
        write(self.root, "lonely.md", "---\ntype: Thing\ntitle: Lonely\n---\nx\n")
        proc = run("lonely.md", "kept/lonely.md", "--bundle", str(self.root), "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue((self.root / "kept" / "lonely.md").exists())
        self.assertFalse((self.root / "lonely.md").exists())

    def test_relative_link_style_rewrites_relatively(self):
        (self.root / "okf.json").write_text('{"link_style": "relative"}', encoding="utf-8")
        proc = run("old.md", "archive/old.md", "--bundle", str(self.root), "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        ref = (self.root / "ref.md").read_text(encoding="utf-8")
        self.assertIn("[Old](archive/old.md)", ref)        # relative from ref (root-level)
        self.assertNotIn("[Old](/archive/old.md)", ref)     # not absolute

if __name__ == "__main__":
    unittest.main()
