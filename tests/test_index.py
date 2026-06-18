# tests/test_index.py
import sys, os, unittest, tempfile, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_model as om
import okf_index as oi

def write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        write(self.root, "index.md", "# B\n")
        write(self.root, "product/faunero.md",
              "---\ntype: Product\ntitle: Faunero\ndescription: The app.\n---\nx\n")
        write(self.root, "concepts/flow.md",
              "---\ntype: Concept\ntitle: Flow\n---\ny\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_generate_tree_groups_by_directory(self):
        m = om.build_model(self.root)
        tree = oi.generate_index_tree(m, "My Bundle")
        self.assertIn("", tree)
        self.assertIn("product", tree)
        self.assertIn("concepts", tree)
        self.assertIn("* [Faunero](faunero.md) — The app.", tree["product"])  # relative link
        self.assertIn("* [Flow](flow.md)", tree["concepts"])   # no description -> no em dash
        self.assertNotIn("flow.md) —", tree["concepts"])
        self.assertTrue(tree[""].startswith("---\n"))          # only root carries frontmatter
        self.assertIn("[Product](product/index.md)", tree[""])  # root navigates down one level
        self.assertNotIn("faunero.md", tree[""])

    def test_drift_detects_missing(self):
        m = om.build_model(self.root)               # index.md ("# B") lists nothing
        codes = {(f["code"], f["id"]) for f in oi.validate_index(m)}
        self.assertIn(("index-drift", "product/faunero"), codes)
        self.assertIn(("index-drift", "concepts/flow"), codes)

    def test_regenerate_writes_nested_and_clean(self):
        oi.regenerate(self.root, "My Bundle")
        self.assertTrue((self.root / "product" / "index.md").exists())
        self.assertTrue((self.root / "concepts" / "index.md").exists())
        self.assertIn("[Faunero](faunero.md)",
                      (self.root / "product" / "index.md").read_text(encoding="utf-8"))
        m2 = om.build_model(self.root)
        self.assertEqual(oi.validate_index(m2), [])   # no drift after regen

    def test_child_index_has_no_frontmatter(self):
        oi.regenerate(self.root, "My Bundle")
        prod = (self.root / "product" / "index.md").read_text(encoding="utf-8")
        self.assertFalse(prod.startswith("---"))      # frontmatter is root-only per spec

    def test_no_title_falls_back_to_humanized_filename(self):
        write(self.root, "notes/raw-note.md", "---\ntype: Note\n---\nz\n")
        m = om.build_model(self.root)
        tree = oi.generate_index_tree(m, "B")
        self.assertIn("* [Raw Note](raw-note.md)", tree["notes"])

    def test_description_internal_whitespace_collapses(self):
        write(self.root, "x.md", "---\ntype: T\ntitle: X\ndescription: a   b\n---\nq\n")
        m = om.build_model(self.root)
        tree = oi.generate_index_tree(m, "B")
        self.assertIn("* [X](x.md) — a b", tree[""])   # root-level concept stays in root index

    def test_empty_bundle_just_title(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "index.md").write_text("# B\n", encoding="utf-8")
            m = om.build_model(root)
            expected = "---\nokf_version: %s\n---\n\n# B\n" % oi.OKF_VERSION
            self.assertEqual(oi.generate_index_text(m, "B"), expected)
            self.assertEqual(oi.validate_index(m), [])

    def test_index_declares_okf_version(self):
        m = om.build_model(self.root)
        out = oi.generate_index_text(m, "My Bundle")
        self.assertIn("okf_version: %s" % oi.OKF_VERSION, out)

    def test_index_version_reads_back(self):
        oi.regenerate(self.root, "My Bundle")
        m = om.build_model(self.root)
        self.assertEqual(oi.index_version(m), oi.OKF_VERSION)

    def test_regenerate_preserves_unknown_root_fm_keys(self):
        write(self.root, "index.md",
              "---\nokf_version: %s\nmaintainer: ryan\n---\n\n# B\n" % oi.OKF_VERSION)
        oi.regenerate(self.root, "My Bundle")
        text = (self.root / "index.md").read_text(encoding="utf-8")
        self.assertIn("maintainer: ryan", text)                    # unknown key survives
        self.assertIn("okf_version: %s" % oi.OKF_VERSION, text)    # version still authoritative

if __name__ == "__main__":
    unittest.main()
