# tests/test_config.py
import sys, os, unittest, tempfile, pathlib, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import okf_config as cfg

class T(unittest.TestCase):
    def test_defaults_when_absent(self):
        with tempfile.TemporaryDirectory() as d:
            c = cfg.load_config(d)
            self.assertEqual(c["stale_days"], 180)
            self.assertEqual(c["link_style"], "absolute")
            self.assertEqual(c["name"], pathlib.Path(d).name)

    def test_file_overrides(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "okf.json").write_text(
                json.dumps({"name": "Brain", "stale_days": 30}), encoding="utf-8")
            c = cfg.load_config(d)
            self.assertEqual(c["name"], "Brain")
            self.assertEqual(c["stale_days"], 30)
            self.assertEqual(c["link_style"], "absolute")   # default fills the gap

    def test_save_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            cfg.save_config(d, {"name": "X", "stale_days": 90, "link_style": "relative"})
            c = cfg.load_config(d)
            self.assertEqual(c["name"], "X")
            self.assertEqual(c["link_style"], "relative")

    def test_save_ignores_unknown_keys(self):
        with tempfile.TemporaryDirectory() as d:
            cfg.save_config(d, {"name": "X", "bogus": 1})
            self.assertNotIn("bogus", cfg.load_config(d))

    def test_wrong_typed_value_falls_back_to_default(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "okf.json").write_text(
                json.dumps({"stale_days": "soon", "name": "Keep"}), encoding="utf-8")
            c = cfg.load_config(d)
            self.assertEqual(c["stale_days"], 180)   # bad type dropped -> default
            self.assertEqual(c["name"], "Keep")      # good value kept

    def test_non_dict_json_falls_back(self):
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "okf.json").write_text("[1, 2, 3]", encoding="utf-8")
            self.assertEqual(cfg.load_config(d)["stale_days"], 180)

    def test_save_writes_trailing_newline(self):
        with tempfile.TemporaryDirectory() as d:
            cfg.save_config(d, {"name": "X"})
            raw = (pathlib.Path(d) / "okf.json").read_text(encoding="utf-8")
            self.assertTrue(raw.endswith("\n"))

if __name__ == "__main__":
    unittest.main()
