# tests/test_validate.py
import sys, os, unittest, tempfile, pathlib
from datetime import datetime, timezone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_validate as ov
import okf_index as oi

def write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        write(self.root, "index.md", "# root\n* [A](/a.md)\n")
        write(self.root, "a.md", "---\ntype: Thing\n---\n[gone](/missing.md)\n")
        write(self.root, "notype.md", "---\ntitle: no type here\n---\nx\n")
        write(self.root, "unlisted.md", "---\ntype: Thing\n---\nz\n")  # not in index
        # dates intentionally oldest-first (not newest-first) to trip log-format
        write(self.root, "log.md", "# Log\n\n## 2026-06-01\nx\n\n## 2026-06-15\ny\n")

    def tearDown(self):
        self.tmp.cleanup()

    def test_codes(self):
        res = ov.validate(self.root, max_age_days=180,
                          now=datetime(2026, 6, 14, tzinfo=timezone.utc))
        codes = {f["code"] for f in res["findings"]}
        self.assertIn("missing-type", codes)     # notype.md
        self.assertIn("broken-link", codes)       # a.md -> /missing.md
        self.assertIn("index-drift", codes)       # unlisted.md not in index
        self.assertIn("log-format", codes)        # log dates not newest-first

    def test_missing_type_is_error(self):
        res = ov.validate(self.root)
        sev = [f["severity"] for f in res["findings"] if f["code"] == "missing-type"]
        self.assertEqual(sev, ["error"])

    def test_index_drift_targets_unlisted(self):
        res = ov.validate(self.root)
        drift_ids = {f["id"] for f in res["findings"] if f["code"] == "index-drift"}
        self.assertIn("unlisted", drift_ids)

    def test_no_log_md_no_crash_no_logformat(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            write(root, "index.md", "# root\n* [A](/a.md)\n")
            write(root, "a.md", "---\ntype: Thing\n---\nx\n")
            codes = {f["code"] for f in ov.validate(root)["findings"]}
            self.assertNotIn("log-format", codes)   # absent log.md must not crash or flag

    def test_okf_version_missing_flags_info(self):
        # setUp's index.md has no frontmatter -> no okf_version declared
        res = ov.validate(self.root)
        vf = [f for f in res["findings"] if f["code"] == "okf-version"]
        self.assertEqual(len(vf), 1)
        self.assertEqual(vf[0]["severity"], "info")

    def test_okf_version_present_clears(self):
        write(self.root, "index.md",
              "---\nokf_version: %s\n---\n# root\n* [A](/a.md)\n" % oi.OKF_VERSION)
        codes = {f["code"] for f in ov.validate(self.root)["findings"]}
        self.assertNotIn("okf-version", codes)

    def test_no_citations_flags_agent_concept(self):
        write(self.root, "drafted.md", "---\ntype: Thing\ncurated_by: agent\n---\nbody\n")
        codes = {(f["code"], f["id"]) for f in ov.validate(self.root)["findings"]}
        self.assertIn(("no-citations", "drafted"), codes)

    def test_citations_section_clears_no_citations(self):
        write(self.root, "drafted.md",
              "---\ntype: Thing\ncurated_by: agent\n---\nbody\n\n# Citations\n\n1. https://x\n")
        ids = {f["id"] for f in ov.validate(self.root)["findings"] if f["code"] == "no-citations"}
        self.assertNotIn("drafted", ids)

    def test_human_curated_not_flagged_for_citations(self):
        write(self.root, "verified.md", "---\ntype: Thing\ncurated_by: human\n---\nbody\n")
        ids = {f["id"] for f in ov.validate(self.root)["findings"] if f["code"] == "no-citations"}
        self.assertNotIn("verified", ids)

    def test_index_links_missing_concept_is_drift(self):
        # index points at a concept that does not exist -> phantom-link drift
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            write(root, "index.md", "# root\n* [Ghost](/ghost.md)\n")
            drift = [f for f in ov.validate(root)["findings"]
                     if f["code"] == "index-drift" and f["id"] == "ghost"]
            self.assertEqual(len(drift), 1)
            self.assertEqual(drift[0]["severity"], "warning")

if __name__ == "__main__":
    unittest.main()
