# scripts/okf_check.py
"""CLI: validate an OKF bundle, optionally applying safe --fix repairs."""
import argparse, json, sys
import okf_bundle as ob
import okf_config as cfg
import okf_validate as ov
import okf_fix as fix

def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate (and optionally fix) an OKF bundle.")
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--stale-days", type=int, default=None)
    ap.add_argument("--fix", action="store_true",
                    help="regenerate index.md and normalize frontmatter ordering")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run",
                    help="with --fix: show the change set without writing")
    args = ap.parse_args(argv)

    root = ob.find_bundle_root(args.path)
    config = cfg.load_config(root)
    stale_days = args.stale_days if args.stale_days is not None else config["stale_days"]

    if args.dry_run and not args.fix:
        print("warning: --dry-run has no effect without --fix", file=sys.stderr)

    if args.fix:
        plan = fix.build_fix_plan(root, config["name"])
        if args.dry_run:
            if args.as_json:
                print(json.dumps({"plan": [{"path": c["path"], "action": c["action"]}
                                           for c in plan["changes"]]}, indent=2))
            else:
                for c in plan["changes"]:
                    print("would %s: %s" % (c["action"], c["path"]))
                print("\n%d file(s) would change." % len(plan["changes"]))
            return 0
        n = fix.apply_plan(plan)
        print("Fixed %d file(s)." % n)

    result = ov.validate(root, max_age_days=stale_days)

    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        for f in result["findings"]:
            print("[%s] %s: %s — %s" % (f["severity"], f["code"], f["id"], f["message"]))
        print("\n%d findings across %d files." % (len(result["findings"]), result["counts"]["files"]))

    return 1 if any(f["severity"] == "error" for f in result["findings"]) else 0

if __name__ == "__main__":
    sys.exit(main())
