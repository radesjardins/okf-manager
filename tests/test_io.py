# tests/test_io.py
import sys, os, unittest, tempfile, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_io as oio

class T(unittest.TestCase):
    def test_detect_and_roundtrip_crlf(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "f.md"
            p.write_bytes("a\r\nb\r\n".encode("utf-8"))
            text, nl = oio.read(p)
            self.assertEqual(text, "a\nb\n")     # normalized to LF internally
            self.assertEqual(nl, "\r\n")
            oio.write(p, text + "c\n", nl)        # re-apply original newline
            self.assertEqual(p.read_bytes(), "a\r\nb\r\nc\r\n".encode("utf-8"))

    def test_lf_default(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "f.md"
            oio.write(p, "x\ny\n")
            self.assertEqual(p.read_bytes(), b"x\ny\n")

    def test_read_lf_reports_lf(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "f.md"
            p.write_bytes(b"a\nb\n")
            text, nl = oio.read(p)
            self.assertEqual((text, nl), ("a\nb\n", "\n"))

    def test_detect_newline_cr_only(self):
        self.assertEqual(oio.detect_newline("a\rb\r"), "\r")

    def test_write_tolerates_unnormalized_input(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "f.md"
            oio.write(p, "a\r\nb\n", "\r\n")          # mixed input, CRLF target
            self.assertEqual(p.read_bytes(), b"a\r\nb\r\n")   # no doubled \r

if __name__ == "__main__":
    unittest.main()
