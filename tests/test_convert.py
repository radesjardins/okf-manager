# tests/test_convert.py
import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_convert as cv

class T(unittest.TestCase):
    def test_csv_to_markdown_table(self):
        out = cv.to_markdown_body("name,role\nRyan,dev\nA,b\n", ".csv")
        lines = out.strip().splitlines()
        self.assertEqual(lines[0], "| name | role |")
        self.assertEqual(lines[1], "| --- | --- |")
        self.assertEqual(lines[2], "| Ryan | dev |")

    def test_csv_pipes_escaped_and_ragged_rows_padded(self):
        out = cv.to_markdown_body("a|b,c\nx\n", ".csv")
        self.assertIn(r"a\|b", out)          # literal pipe escaped
        self.assertIn("| x |  |", out)        # short row padded to width 2

    def test_json_pretty_block(self):
        out = cv.to_markdown_body('{"b":1,"a":2}', ".json")
        self.assertTrue(out.startswith("```json\n"))
        self.assertIn('"b": 1', out)          # re-serialized with indent
        self.assertTrue(out.rstrip().endswith("```"))

    def test_json_invalid_is_fenced_raw(self):
        out = cv.to_markdown_body("{not valid", ".json")
        self.assertIn("```json", out)
        self.assertIn("{not valid", out)

    def test_html_headings_links_lists_and_script_dropped(self):
        html = ("<h1>Title</h1><p>See <a href='/x.md'>X</a> now.</p>"
                "<ul><li>one</li><li>two</li></ul><script>BADJS</script>")
        out = cv.to_markdown_body(html, ".html")
        self.assertIn("# Title", out)
        self.assertIn("[X](/x.md)", out)
        self.assertIn("- one", out)
        self.assertIn("- two", out)
        self.assertNotIn("BADJS", out)

    def test_txt_passthrough_trimmed(self):
        self.assertEqual(cv.to_markdown_body("  hello\nworld  \n", ".txt"), "hello\nworld\n")

    def test_unsupported_extension_raises(self):
        with self.assertRaises(ValueError):
            cv.to_markdown_body("x", ".pdf")

    def test_html_br_splits_blocks(self):
        out = cv.to_markdown_body("<p>a<br>b</p>", ".html")
        self.assertIn("a", out)
        self.assertIn("b", out)
        self.assertNotIn("ab", out)          # must not be concatenated

    def test_html_table_cells_separated(self):
        out = cv.to_markdown_body(
            "<table><tr><td>a</td><td>b</td></tr></table>", ".html")
        self.assertIn("a | b", out)      # cells separated
        self.assertNotIn("ab", out)      # not glued together

    def test_csv_multiline_cell_collapsed(self):
        out = cv.to_markdown_body('"a\nb",c\nd,e\n', ".csv")
        lines = out.strip().splitlines()
        self.assertEqual(lines[0], "| a b | c |")   # newline collapsed to space
        self.assertEqual(lines[1], "| --- | --- |")
        self.assertEqual(lines[2], "| d | e |")

if __name__ == "__main__":
    unittest.main()
