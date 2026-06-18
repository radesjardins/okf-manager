# scripts/okf_map.py
"""CLI: generate a self-contained HTML view of an OKF bundle."""
import argparse, sys
from pathlib import Path
import okf_bundle as ob
import okf_config as cfg
import okf_model as om
import okf_viz as ov
import okf_validate as oval

def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate a self-contained HTML view.")
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--out", default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--view", default="graph", choices=["graph"])  # table/board in v3
    args = ap.parse_args(argv)

    root = ob.find_bundle_root(args.path)
    name = args.name or cfg.load_config(root)["name"]
    model = om.build_model(root)
    findings = oval.validate(root)["findings"]   # the attention lens uses the same findings as `check`
    out = Path(args.out) if args.out else Path(root) / "viz.html"
    out.write_text(ov.render_html(model, name, findings), encoding="utf-8")
    print("Wrote %s" % out)
    return 0

if __name__ == "__main__":
    sys.exit(main())
