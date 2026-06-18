# tests/test_log.py
import sys, os, unittest, tempfile, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_log as olog

class T(unittest.TestCase):
    def test_new_day_inserted_on_top(self):
        text = "# B Log\n\n## 2026-06-01\n* **Init**: started\n"
        out = olog.prepend_entry(text, "2026-06-15", "Update", "added x")
        self.assertLess(out.index("2026-06-15"), out.index("2026-06-01"))  # newest first
        self.assertIn("* **Update**: added x", out)
        self.assertIn("* **Init**: started", out)                          # old entry kept

    def test_same_day_stacks_newest_first(self):
        text = "# B Log\n\n## 2026-06-15\n* **First**: a\n"
        out = olog.prepend_entry(text, "2026-06-15", "Second", "b")
        self.assertLess(out.index("**Second**"), out.index("**First**"))

    def test_validate_detects_unordered(self):
        bad = "# B Log\n\n## 2026-06-01\nx\n\n## 2026-06-15\ny\n"
        codes = [f["code"] for f in olog.validate_log(bad)]
        self.assertIn("log-format", codes)

    def test_append_creates_and_writes(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            olog.append(root, "B", "2026-06-15", "New", "added x")
            text = (root / "log.md").read_text(encoding="utf-8")
            self.assertIn("# B Log", text)
            self.assertIn("* **New**: added x", text)

    def test_append_to_existing_stacks_on_top(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "log.md").write_text("# B Log\n\n## 2026-06-01\n* **Old**: a\n",
                                         encoding="utf-8")
            olog.append(root, "B", "2026-06-15", "New", "b")
            text = (root / "log.md").read_text(encoding="utf-8")
            self.assertLess(text.index("2026-06-15"), text.index("2026-06-01"))
            self.assertIn("* **Old**: a", text)

    def test_validate_happy_path_returns_empty(self):
        good = "# B Log\n\n## 2026-06-15\n* **A**: x\n\n## 2026-06-01\n* **B**: y\n"
        self.assertEqual(olog.validate_log(good), [])

    def test_prepend_without_title_has_no_leading_blank(self):
        out = olog.prepend_entry("## 2026-06-01\n* **Old**: a\n",
                                 "2026-06-15", "New", "b")
        self.assertFalse(out.startswith("\n"))           # no stray leading blank line
        self.assertTrue(out.startswith("## 2026-06-15"))
        self.assertIn("* **Old**: a", out)

if __name__ == "__main__":
    unittest.main()
