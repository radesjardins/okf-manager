# tests/test_linkedit.py
import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_linkedit as le

class T(unittest.TestCase):
    def test_absolute_rewrite_preserves_other_bytes(self):
        body = "See [A](/old.md) and [B](/keep.md) and text.\n"
        out, n = le.rewrite_targets(body, "src", "old", "new", style="absolute")
        self.assertEqual(n, 1)
        self.assertIn("[A](/new.md)", out)
        self.assertIn("[B](/keep.md)", out)        # untouched
        self.assertTrue(out.endswith("and text.\n"))

    def test_relative_rewrite(self):
        body = "[A](../old.md)\n"
        out, n = le.rewrite_targets(body, "dir/src", "old", "moved/new", style="relative")
        self.assertEqual(n, 1)
        self.assertIn("[A](../moved/new.md)", out)

    def test_preserves_anchor(self):
        body = "[A](/old.md#sec)\n"
        out, n = le.rewrite_targets(body, "src", "old", "new")
        self.assertIn("[A](/new.md#sec)", out)

    def test_two_links_same_target(self):
        body = "[1](/old.md) [2](/old.md)\n"
        out, n = le.rewrite_targets(body, "src", "old", "new")
        self.assertEqual(n, 2)
        self.assertEqual(out, "[1](/new.md) [2](/new.md)\n")

    def test_no_match_returns_unchanged(self):
        body = "[A](/keep.md) and [ext](http://x.com)\n"
        out, n = le.rewrite_targets(body, "src", "old", "new")
        self.assertEqual(n, 0)
        self.assertEqual(out, body)

    def test_self_link_rewritten(self):
        # the moved file links to itself; source_id is the OLD id
        body = "intro [me](/old.md) end\n"
        out, n = le.rewrite_targets(body, "old", "old", "archive/old")
        self.assertEqual(n, 1)
        self.assertIn("[me](/archive/old.md)", out)

if __name__ == "__main__":
    unittest.main()
