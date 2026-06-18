# tests/test_scan.py
import sys, os, unittest, tempfile, pathlib, json, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_scan as sc
SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")

def write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        write(self.root, "notes/idea.md", "---\ntype: Note\n---\n# Big Idea\nbody\n")
        write(self.root, "notes/raw.txt", "first line of text\nsecond\n")
        write(self.root, "data/rows.csv", "a,b\n1,2\n")
        write(self.root, "skip.png", "binary-ish")
        write(self.root, "index.md", "# reserved\n")             # reserved -> skipped
        write(self.root, ".git/config.json", "{}")               # noisy dir -> skipped

    def tearDown(self):
        self.tmp.cleanup()

    def test_lists_only_candidate_formats(self):
        cands = sc.scan_candidates(self.root)
        exts = sorted(c["ext"] for c in cands)
        self.assertEqual(exts, [".csv", ".md", ".txt"])         # no .png, no reserved, no .git

    def test_metadata_first_heading_and_frontmatter(self):
        cands = {pathlib.Path(c["path"]).name: c for c in sc.scan_candidates(self.root)}
        self.assertEqual(cands["idea.md"]["first_heading"], "Big Idea")
        self.assertTrue(cands["idea.md"]["has_frontmatter"])
        self.assertEqual(cands["raw.txt"]["first_heading"], "first line of text")
        self.assertFalse(cands["raw.txt"]["has_frontmatter"])

    def test_in_bundle_flag(self):
        cands = {pathlib.Path(c["path"]).name: c for c in
                 sc.scan_candidates(self.root / "notes", bundle_root=self.root)}
        self.assertTrue(cands["idea.md"]["in_bundle"])

    def test_cli_json(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "okf_scan.py"), str(self.root), "--json"],
            capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertEqual(data["count"], 3)

if __name__ == "__main__":
    unittest.main()
