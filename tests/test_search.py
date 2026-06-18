# tests/test_search.py
import sys, os, unittest, tempfile, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_model as om
import okf_search as se

def write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        write(self.root, "index.md", "# B\n")
        write(self.root, "a.md",
              "---\ntype: Note\ntitle: Faunero overview\ntags: [app, core]\n"
              "status: Done\n---\nLinks to [b](/b.md). Mentions widget.\n")
        write(self.root, "b.md",
              "---\ntype: Concept\ntitle: Plumbing\n---\nThe faunero widget pipeline.\n")

    def tearDown(self):
        self.tmp.cleanup()

    def model(self):
        return om.build_model(self.root)

    def test_title_hit_outranks_body_hit(self):
        res = se.search(self.model(), text="faunero")
        self.assertEqual(res[0]["id"], "a")            # title match beats body match
        self.assertEqual({r["id"] for r in res}, {"a", "b"})
        self.assertGreater(res[0]["score"], res[1]["score"])

    def test_type_filter(self):
        res = se.search(self.model(), ctype="Concept")
        self.assertEqual([r["id"] for r in res], ["b"])

    def test_tag_filter_case_insensitive(self):
        res = se.search(self.model(), tag="CORE")
        self.assertEqual([r["id"] for r in res], ["a"])

    def test_status_filter(self):
        res = se.search(self.model(), status="done")
        self.assertEqual([r["id"] for r in res], ["a"])

    def test_related_surfaces_links_both_directions(self):
        res = se.search(self.model(), text="faunero")
        by_id = {r["id"]: r for r in res}
        self.assertIn("b", by_id["a"]["related"])      # a -> b (outbound)
        self.assertIn("a", by_id["b"]["related"])      # a -> b (inbound for b)

    def test_no_text_returns_all_filtered_id_sorted(self):
        res = se.search(self.model())
        self.assertEqual([r["id"] for r in res], ["a", "b"])
        self.assertTrue(all(r["score"] == 0 for r in res))

    def test_limit_zero_returns_empty(self):
        self.assertEqual(se.search(self.model(), limit=0), [])

    def test_multi_term_scoring_sums_per_term(self):
        # b's body has both "widget" and "pipeline"; a's body has only "widget"
        res = se.search(self.model(), text="widget pipeline")
        self.assertEqual(res[0]["id"], "b")
        self.assertGreater(res[0]["score"], res[1]["score"])

if __name__ == "__main__":
    unittest.main()
