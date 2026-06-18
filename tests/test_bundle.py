# tests/test_bundle.py
import sys, os, unittest, tempfile, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_bundle as ob

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        (self.root / "index.md").write_text("# root", encoding="utf-8")
        (self.root / "tables").mkdir()
        (self.root / "tables" / "users.md").write_text("---\ntype: T\n---\n", encoding="utf-8")
        (self.root / "templates").mkdir()
        (self.root / "templates" / "tpl.md").write_text("x", encoding="utf-8")
        (self.root / ".indexignore").write_text("templates\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_find_root_by_index(self):
        self.assertEqual(ob.find_bundle_root(self.root / "tables"), self.root)

    def test_iter_skips_ignored(self):
        ids = sorted(ob.concept_id(p, self.root) for p in ob.iter_concept_files(self.root))
        self.assertIn("tables/users", ids)
        self.assertIn("index", ids)
        self.assertNotIn("templates/tpl", ids)

if __name__ == "__main__":
    unittest.main()
