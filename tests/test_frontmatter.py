# tests/test_frontmatter.py
import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_frontmatter as fm

DOC = """---
type: Product Concept
title: Faunero
tags: [a, b]
status: In Progress
# a human comment
custom_key: keep me
---

# Body
Hello [x](y.md).
"""

class T(unittest.TestCase):
    def test_parses_known_and_unknown_keys(self):
        meta, body, errors = fm.parse_frontmatter(DOC)
        self.assertEqual(meta["type"], "Product Concept")
        self.assertEqual(meta["title"], "Faunero")
        self.assertEqual(meta["tags"], ["a", "b"])
        self.assertEqual(meta["custom_key"], "keep me")
        self.assertEqual(errors, [])
        self.assertTrue(body.startswith("\n# Body"))

    def test_block_list(self):
        meta, _, _ = fm.parse_frontmatter("---\ntags:\n  - one\n  - two\n---\nx")
        self.assertEqual(meta["tags"], ["one", "two"])

    def test_no_frontmatter_reports_error(self):
        meta, body, errors = fm.parse_frontmatter("no fm here")
        self.assertEqual(meta, {})
        self.assertEqual(body, "no fm here")
        self.assertTrue(errors)

if __name__ == "__main__":
    unittest.main()
