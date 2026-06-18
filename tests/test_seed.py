import sys, os, unittest, tempfile, pathlib, sqlite3, json, subprocess
SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")
sys.path.insert(0, SCRIPTS)
import okf_seed as seed

class TParsers(unittest.TestCase):
    def test_sqlite_one_concept_per_table(self):
        with tempfile.TemporaryDirectory() as d:
            db = pathlib.Path(d) / "x.db"
            con = sqlite3.connect(db)
            con.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
            con.execute("CREATE TABLE orders(id INTEGER)")
            con.commit(); con.close()
            specs = seed.specs_from_sqlite(str(db), "tables")
            self.assertEqual(sorted(s["title"] for s in specs), ["orders", "users"])
            users = next(s for s in specs if s["title"] == "users")
            self.assertEqual(users["type"], "Table")
            self.assertEqual(users["dest"], "tables/users.md")
            self.assertIn("# Schema", users["body"])
            self.assertIn("name", users["body"])
            self.assertTrue(users["resource"].startswith("sqlite://"))

    def test_openapi_endpoint_per_operation(self):
        obj = {"openapi": "3.0.0",
               "paths": {"/pets": {"get": {"summary": "List pets"}, "post": {"summary": "Create"}}}}
        specs = seed.specs_from_openapi(obj, "api")
        self.assertEqual(sorted(s["title"] for s in specs), ["GET /pets", "POST /pets"])
        self.assertEqual(specs[0]["type"], "API Endpoint")
        self.assertEqual(specs[0]["resource"], "/pets")

    def test_jsonschema_definitions(self):
        obj = {"$schema": "x", "definitions": {
            "Pet": {"type": "object", "description": "a pet",
                    "properties": {"name": {"type": "string"}}, "required": ["name"]}}}
        specs = seed.specs_from_openapi(obj, "schema")
        self.assertEqual(specs[0]["title"], "Pet")
        self.assertEqual(specs[0]["type"], "Schema")
        self.assertIn("a pet", specs[0]["description"])
        self.assertIn("| name | string | yes |", specs[0]["body"])

    def test_tree_concept_per_file_preserves_structure_and_skips_dotdirs(self):
        with tempfile.TemporaryDirectory() as d:
            r = pathlib.Path(d)
            (r / "src").mkdir(); (r / "src" / "a.py").write_text("print(1)\n", encoding="utf-8")
            (r / "README.md").write_text("# hi\n", encoding="utf-8")
            (r / ".git").mkdir(); (r / ".git" / "cfg").write_text("x", encoding="utf-8")
            specs = seed.specs_from_tree(str(r), "catalog")
            dests = sorted(s["dest"] for s in specs)
            self.assertIn("catalog/src/a.py.md", dests)      # non-md gets .md suffix, structure kept
            self.assertIn("catalog/README.md", dests)        # already-md stays single-suffixed
            self.assertTrue(all(".git" not in x for x in dests))   # dot-dirs skipped
            apy = next(s for s in specs if s["dest"] == "catalog/src/a.py.md")
            self.assertIn("print(1)", apy["body"])           # small text file content embedded

class TCli(unittest.TestCase):
    def run_seed(self, *args):
        return subprocess.run([sys.executable, os.path.join(SCRIPTS, "okf_seed.py"), *args],
                              capture_output=True, text=True)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "index.md").write_text("# B\n", encoding="utf-8")
        (self.root / "okf.json").write_text('{"name": "B"}', encoding="utf-8")
        self.db = self.root / "src.db"
        con = sqlite3.connect(self.db)
        con.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT)")
        con.commit(); con.close()

    def tearDown(self):
        self.tmp.cleanup()

    def test_dry_run_writes_nothing(self):
        proc = self.run_seed(str(self.db), "--bundle", str(self.root),
                             "--dest-dir", "tables", "--dry-run", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertIn("tables/users.md", data["would_create"])
        self.assertFalse((self.root / "tables" / "users.md").exists())

    def test_seed_writes_concepts_indexes_and_passes_check(self):
        proc = self.run_seed(str(self.db), "--bundle", str(self.root), "--dest-dir", "tables",
                             "--timestamp", "2026-06-15T00:00:00Z", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        f = self.root / "tables" / "users.md"
        self.assertTrue(f.exists())
        text = f.read_text(encoding="utf-8")
        self.assertIn("type: Table", text)
        self.assertIn("# Citations", text)      # seed records its source as provenance
        self.assertIn("src.db", text)
        # wired into its directory index
        self.assertIn("[users](users.md)",
                      (self.root / "tables" / "index.md").read_text(encoding="utf-8"))
        # bundle validates with no errors
        chk = subprocess.run([sys.executable, os.path.join(SCRIPTS, "okf_check.py"),
                              str(self.root), "--json"], capture_output=True, text=True)
        errs = [x for x in json.loads(chk.stdout)["findings"] if x["severity"] == "error"]
        self.assertEqual(errs, [])

    def test_rejects_missing_source(self):
        proc = self.run_seed(str(self.root / "nope.db"), "--bundle", str(self.root), "--json")
        self.assertEqual(proc.returncode, 2)

if __name__ == "__main__":
    unittest.main()
