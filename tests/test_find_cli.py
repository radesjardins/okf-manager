# tests/test_find_cli.py
import sys, os, unittest, tempfile, pathlib, json, subprocess
SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")

def write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

def run(*args):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "okf_find.py"), *args],
                          capture_output=True, text=True)

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        write(self.root, "index.md", "# B\n")
        write(self.root, "a.md", "---\ntype: Note\ntitle: Faunero\n---\nx\n")
        write(self.root, "b.md", "---\ntype: Concept\ntitle: Other\n---\ny\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_text_search_json(self):
        proc = run(str(self.root), "--text", "faunero", "--json")
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["id"], "a")

    def test_type_filter_json(self):
        proc = run(str(self.root), "--type", "Concept", "--json")
        ids = [r["id"] for r in json.loads(proc.stdout)["results"]]
        self.assertEqual(ids, ["b"])

    def test_no_match_human_output_exit_zero(self):
        proc = run(str(self.root), "--text", "zzz")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("No matches", proc.stdout)

if __name__ == "__main__":
    unittest.main()
