# tests/test_viz.py
import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_viz as ov

MODEL = {
    "root": "/x",
    "files": {"a": {"id": "a", "type": "Thing", "reserved": False, "errors": []},
              "index": {"id": "index", "type": "", "reserved": True, "errors": []}},
    "links": [{"src": "a", "dst": "index", "resolved": True}],
}

class T(unittest.TestCase):
    def test_self_contained_html(self):
        out = ov.render_html(MODEL, name="My Bundle")
        self.assertTrue(out.lstrip().lower().startswith("<!doctype html"))
        self.assertIn("My Bundle", out)
        self.assertIn('"id": "a"', out)            # node data inlined
        # Self-contained means no external resource FETCHES. The SVG namespace URI
        # (http://www.w3.org/2000/svg) is a local identifier, never loaded over the
        # network, so a blanket http:// ban would be wrong — target real fetches.
        self.assertNotIn('src="http', out)
        self.assertNotIn('href="http', out)
        self.assertNotIn("<link", out)
        self.assertNotIn("<script src", out)
        self.assertNotIn("//cdn", out)

    def test_includes_detail_legend_and_backlinks(self):
        rich = {
            "root": "/x",
            "files": {
                "a": {"id": "a", "type": "Thing", "reserved": False, "errors": [],
                      "meta": {"title": "Alpha", "description": "first", "resource": "urn:a"},
                      "body": "Alpha body text"},
                "b": {"id": "b", "type": "Other", "reserved": False, "errors": [],
                      "meta": {"title": "Beta"}, "body": "Beta body"},
                "index": {"id": "index", "type": "", "reserved": True, "errors": [],
                          "meta": {}, "body": ""},
            },
            "links": [{"src": "a", "dst": "b", "resolved": True}],
        }
        out = ov.render_html(rich, name="B")
        self.assertIn("Thing", out)              # type drives the legend/colours
        self.assertIn("Alpha body text", out)    # body embedded for the detail panel
        self.assertIn("urn:a", out)              # resource embedded
        self.assertIn("Backlinks", out)          # backlinks UI present
        self.assertIn("search", out.lower())     # search control present

    def test_attention_lens_from_findings(self):
        model = {
            "root": "/x",
            "files": {"a": {"id": "a", "type": "Thing", "reserved": False, "errors": [],
                            "meta": {"title": "Alpha"}, "body": "x"}},
            "links": [],
        }
        findings = [{"severity": "info", "code": "orphan", "id": "a", "message": "m"},
                    {"severity": "warning", "code": "broken-link", "id": "a", "message": "m"}]
        out = ov.render_html(model, name="B", findings=findings)
        self.assertIn("Needs attention", out)   # the lens UI
        self.assertIn("orphan", out)            # the issue rides along in node data
        self.assertIn("broken-link", out)

    def test_script_breakout_is_escaped(self):
        # A concept id/type containing </script> must not terminate the inline
        # <script> block in the output.
        model = {
            "root": "/x",
            "files": {"evil": {"id": "evil</script><img src=x onerror=alert(1)>",
                               "type": "T</script>", "reserved": False, "errors": []}},
            "links": [],
        }
        out = ov.render_html(model)
        self.assertNotIn("</script><img", out)   # raw breakout absent
        self.assertIn("<\\/script>", out)         # escaped form present

if __name__ == "__main__":
    unittest.main()
