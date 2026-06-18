import sys, os, unittest, tempfile, pathlib, json, subprocess
SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")

def run(*args):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "okf_new.py"), *args],
                          capture_output=True, text=True)

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "index.md").write_text("# Bundle\n", encoding="utf-8")
        (self.root / "log.md").write_text("# Bundle Log\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_dry_run_writes_nothing(self):
        proc = run("concepts/foo.md", "--bundle", str(self.root),
                   "--type", "Concept", "--title", "Foo", "--dry-run", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(any("foo.md" in c for c in data["creates"]))
        self.assertFalse((self.root / "concepts" / "foo.md").exists())

    def test_creates_concept_and_updates_index_log(self):
        proc = run("concepts/foo.md", "--bundle", str(self.root),
                   "--type", "Concept", "--title", "Foo",
                   "--description", "A test.", "--tag", "x", "--tag", "y",
                   "--timestamp", "2026-06-15T00:00:00Z", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        f = self.root / "concepts" / "foo.md"
        self.assertTrue(f.exists())
        text = f.read_text(encoding="utf-8")
        self.assertIn("type: Concept", text)
        self.assertIn("tags: [x, y]", text)
        self.assertIn("curated_by: agent", text)
        self.assertIn("[Foo](foo.md) — A test.",
                      (self.root / "concepts" / "index.md").read_text(encoding="utf-8"))
        self.assertIn("* **New**: added concepts/foo",
                      (self.root / "log.md").read_text(encoding="utf-8"))

    def test_resource_and_citation_round_trip(self):
        proc = run("concepts/bar.md", "--bundle", str(self.root),
                   "--type", "Concept", "--title", "Bar",
                   "--resource", "https://example.com/bar",
                   "--citation", "https://src.example/page",
                   "--timestamp", "2026-06-15T00:00:00Z", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        text = (self.root / "concepts" / "bar.md").read_text(encoding="utf-8")
        self.assertIn("resource: https://example.com/bar", text)
        self.assertIn("# Citations", text)
        self.assertIn("1. https://src.example/page", text)

    def test_refuses_overwrite(self):
        (self.root / "dup.md").write_text("x", encoding="utf-8")
        proc = run("dup.md", "--bundle", str(self.root),
                   "--type", "Concept", "--title", "Dup")
        self.assertEqual(proc.returncode, 2)

    def test_rejects_dest_outside_bundle(self):
        proc = run("../escape.md", "--bundle", str(self.root),
                   "--type", "Concept", "--title", "Esc")
        self.assertEqual(proc.returncode, 2)
        self.assertFalse((self.root.parent / "escape.md").exists())

    def test_rejects_bad_timestamp(self):
        proc = run("t.md", "--bundle", str(self.root),
                   "--type", "Concept", "--title", "T", "--timestamp", "today")
        self.assertEqual(proc.returncode, 2)

    def test_init_scaffolds_fresh_bundle(self):
        with tempfile.TemporaryDirectory() as d:
            # Point --bundle at a subdirectory that does NOT yet exist to reproduce
            # the real onboarding path (user runs --init in a brand-new location).
            fresh = pathlib.Path(d) / "new-bundle"
            self.assertFalse(fresh.exists())
            proc = run("concepts/first.md", "--bundle", str(fresh), "--init",
                       "--name", "Brain", "--type", "Concept", "--title", "First",
                       "--timestamp", "2026-06-15T00:00:00Z", "--json")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue((fresh / "okf.json").exists())
            self.assertTrue((fresh / "log.md").exists())
            self.assertIn("[First](first.md)",
                          (fresh / "concepts" / "index.md").read_text(encoding="utf-8"))

    def test_force_overwrites_and_reindexes(self):
        run("dup.md", "--bundle", str(self.root), "--type", "Concept",
            "--title", "Dup", "--timestamp", "2026-06-15T00:00:00Z")
        proc = run("dup.md", "--bundle", str(self.root), "--type", "Concept",
                   "--title", "Dup Two", "--timestamp", "2026-06-15T00:00:00Z", "--force")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("title: Dup Two", (self.root / "dup.md").read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
