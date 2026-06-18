# tests/test_fix.py
import sys, os, unittest, tempfile, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_fix as fix
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
        write(self.root, "index.md", "# B\n")                       # stale: lists nothing
        write(self.root, "a.md", "---\ntitle: A\ntype: Thing\n---\nx\n")  # type not first
        write(self.root, "b.md", "---\ntype: Thing\n# note\ntitle: B\n---\ny\n")  # has comment

    def tearDown(self):
        self.tmp.cleanup()

    def test_plan_lists_index_and_frontmatter(self):
        plan = fix.build_fix_plan(self.root, "B")
        actions = {(c["action"], pathlib.Path(c["path"]).name) for c in plan["changes"]}
        self.assertIn(("index", "index.md"), actions)
        self.assertIn(("frontmatter", "a.md"), actions)
        self.assertNotIn(("frontmatter", "b.md"), actions)   # comment-bearing -> skipped

    def test_apply_writes_changes(self):
        plan = fix.build_fix_plan(self.root, "B")
        n = fix.apply_plan(plan)
        self.assertEqual(n, len(plan["changes"]))
        idx = (self.root / "index.md").read_text(encoding="utf-8")
        self.assertIn("[A](a.md)", idx)
        a = (self.root / "a.md").read_text(encoding="utf-8")
        keys = [ln.split(":")[0] for ln in a.splitlines() if ":" in ln]
        self.assertLess(keys.index("type"), keys.index("title"))   # type now precedes title
        m = om.build_model(self.root)
        self.assertEqual(oi.validate_index(m), [])             # drift resolved

    def test_clean_bundle_has_empty_plan(self):
        fix.apply_plan(fix.build_fix_plan(self.root, "B"))      # first pass fixes everything
        plan2 = fix.build_fix_plan(self.root, "B")             # second pass: nothing to do
        self.assertEqual(plan2["changes"], [])
        self.assertEqual(fix.apply_plan(plan2), 0)

if __name__ == "__main__":
    unittest.main()
