# tests/test_check_cli.py
import sys, os, unittest, tempfile, pathlib, json, subprocess
SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")

def write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

def run(*args):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "okf_check.py"), *args],
                          capture_output=True, text=True)

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        write(self.root, "index.md", "# root\n")
        write(self.root, "notype.md", "---\ntitle: x\n---\ny\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_json_output_and_exit_code(self):
        proc = run(str(self.root), "--json")
        data = json.loads(proc.stdout)
        codes = {f["code"] for f in data["findings"]}
        self.assertIn("missing-type", codes)
        self.assertEqual(proc.returncode, 1)  # errors present

    def test_fix_dry_run_writes_nothing(self):
        before = (self.root / "index.md").read_text(encoding="utf-8")
        proc = run(str(self.root), "--fix", "--dry-run", "--json")
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertTrue(any(c["action"] == "index" for c in data["plan"]))
        self.assertEqual((self.root / "index.md").read_text(encoding="utf-8"), before)

    def test_fix_regenerates_index(self):
        proc = run(str(self.root), "--fix")
        self.assertEqual(proc.returncode, 1)   # notype.md still an error after fix
        self.assertIn("[x](notype.md)", (self.root / "index.md").read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
