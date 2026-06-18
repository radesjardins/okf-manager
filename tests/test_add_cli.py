# tests/test_add_cli.py
import sys, os, unittest, tempfile, pathlib, json, subprocess
SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS)
import okf_add as add

def run(*args):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "okf_add.py"), *args],
                          capture_output=True, text=True)

class TUnit(unittest.TestCase):
    def test_normalize_seeds_frontmatter_when_absent(self):
        out = add.normalize_import("# Just a heading\nbody\n",
            [("type", "Note"), ("title", "T"), ("timestamp", "2026-06-15T00:00:00Z")])
        self.assertTrue(out.startswith("---\ntype: Note"))
        self.assertIn("title: T", out)
        self.assertIn("# Just a heading", out)        # original body kept

    def test_normalize_preserves_existing_keys(self):
        src = "---\ntype: Existing\ntitle: Keep\n---\nx\n"
        out = add.normalize_import(src, [("type", "New"), ("title", "Other"),
                                         ("description", "added")])
        self.assertIn("type: Existing", out)          # not overwritten
        self.assertIn("title: Keep", out)
        self.assertIn("description: added", out)       # missing key filled

    def test_normalize_includes_resource(self):
        out = add.normalize_import("body\n",
            [("type", "Note"), ("title", "T"), ("resource", "urn:x"),
             ("timestamp", "2026-06-15T00:00:00Z")])
        self.assertIn("resource: urn:x", out)

    def test_normalize_fenced_block_not_treated_as_body(self):
        # a fenced frontmatter block that parses to no clean keys must stay a
        # frontmatter block (filled), not be shoved into the body with a new fence
        src = "---\ntype: Keep\n---\nbody here\n"
        out = add.normalize_import(src, [("type", "X"), ("title", "T")])
        self.assertEqual(out.count("---"), 2)         # exactly one frontmatter block
        self.assertIn("type: Keep", out)              # existing value preserved
        self.assertIn("title: T", out)                # missing key filled in-block
        self.assertIn("body here", out)

class TCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "index.md").write_text("# Bundle\n", encoding="utf-8")
        (self.root / "log.md").write_text("# Bundle Log\n", encoding="utf-8")
        self.src = self.root / "_incoming.md"
        self.src.write_text("# Loose note\nsome content\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_import_places_and_indexes(self):
        proc = run(str(self.src), "notes/loose.md", "--bundle", str(self.root),
                   "--type", "Note", "--title", "Loose",
                   "--timestamp", "2026-06-15T00:00:00Z", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        dest = self.root / "notes" / "loose.md"
        self.assertTrue(dest.exists())
        self.assertIn("type: Note", dest.read_text(encoding="utf-8"))
        self.assertIn("[Loose](loose.md)",
                      (self.root / "notes" / "index.md").read_text(encoding="utf-8"))

    def test_import_with_resource(self):
        proc = run(str(self.src), "notes/r.md", "--bundle", str(self.root),
                   "--type", "Note", "--title", "R", "--resource", "urn:abc",
                   "--timestamp", "2026-06-15T00:00:00Z")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("resource: urn:abc",
                      (self.root / "notes" / "r.md").read_text(encoding="utf-8"))

    def test_refuses_overwrite(self):
        (self.root / "dup.md").write_text("x", encoding="utf-8")
        proc = run(str(self.src), "dup.md", "--bundle", str(self.root),
                   "--type", "Note", "--title", "Dup")
        self.assertEqual(proc.returncode, 2)

    def test_rejects_dest_outside_bundle(self):
        proc = run(str(self.src), "../escape.md", "--bundle", str(self.root),
                   "--type", "Note", "--title", "Esc")
        self.assertEqual(proc.returncode, 2)
        self.assertFalse((self.root.parent / "escape.md").exists())

    def test_preserves_source_crlf(self):
        crlf = self.root / "_crlf.md"
        crlf.write_bytes("# Note\r\nline two\r\n".encode("utf-8"))
        proc = run(str(crlf), "notes/c.md", "--bundle", str(self.root),
                   "--type", "Note", "--title", "C",
                   "--timestamp", "2026-06-15T00:00:00Z")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        raw = (self.root / "notes" / "c.md").read_bytes()
        self.assertIn(b"\r\n", raw)            # source CRLF preserved
        self.assertNotIn(b"\r\r", raw)          # not doubled

if __name__ == "__main__":
    unittest.main()
