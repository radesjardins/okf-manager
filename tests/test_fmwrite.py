# tests/test_fmwrite.py
import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_fmwrite as fmw
import okf_frontmatter as fm

DOC = """---
type: Thing
title: Old Title
# a standalone comment
custom: keep me
---

# Body
Untouched [x](y.md).
"""

class T(unittest.TestCase):
    def test_set_existing_key_in_place(self):
        out = fmw.set_key(DOC, "title", "New Title")
        meta, body, _ = fm.parse_frontmatter(out)
        self.assertEqual(meta["title"], "New Title")
        self.assertEqual(meta["custom"], "keep me")        # unknown key preserved
        self.assertIn("# a standalone comment", out)         # comment preserved
        self.assertIn("# Body\nUntouched [x](y.md).", out)   # body byte-identical

    def test_add_new_key_before_fence(self):
        out = fmw.set_key(DOC, "status", "Todo")
        meta, _, _ = fm.parse_frontmatter(out)
        self.assertEqual(meta["status"], "Todo")
        self.assertEqual(meta["type"], "Thing")

    def test_render_frontmatter_roundtrips(self):
        block = fmw.render_frontmatter([("type", "Note"), ("tags", ["a", "b"])])
        meta, _, errors = fm.parse_frontmatter(block + "\nbody\n")
        self.assertEqual(meta["type"], "Note")
        self.assertEqual(meta["tags"], ["a", "b"])
        self.assertEqual(errors, [])

    def test_normalize_type_first(self):
        doc = "---\ntitle: T\ntype: Thing\n---\nx\n"
        out = fmw.normalize_type_first(doc)
        fm_lines = out.splitlines()
        self.assertEqual(fm_lines[1], "type: Thing")        # type moved to top
        self.assertIn("title: T", out)

    def test_normalize_noop_when_already_first(self):
        doc = "---\ntype: Thing\ntitle: T\n---\nx\n"
        self.assertEqual(fmw.normalize_type_first(doc), doc)

    def test_normalize_noop_when_type_absent(self):
        doc = "---\ntitle: T\n---\nx\n"
        self.assertEqual(fmw.normalize_type_first(doc), doc)

    def test_set_key_dedupes_duplicate_keys(self):
        doc = "---\ntype: X\ntitle: First\ntitle: Second\n---\nbody\n"
        out = fmw.set_key(doc, "title", "Only")
        self.assertEqual(out.count("title:"), 1)
        meta, _, _ = fm.parse_frontmatter(out)
        self.assertEqual(meta["title"], "Only")

    def test_set_key_creates_block_when_absent(self):
        out = fmw.set_key("just body\n", "type", "Note")
        meta, body, _ = fm.parse_frontmatter(out)
        self.assertEqual(meta["type"], "Note")
        self.assertIn("just body", body)

if __name__ == "__main__":
    unittest.main()
