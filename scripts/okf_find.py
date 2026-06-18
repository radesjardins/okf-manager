# scripts/okf_find.py
"""CLI: search a bundle by text/type/tag/status. Read-only — never writes."""
import argparse, json, sys
import okf_bundle as ob
import okf_model as om
import okf_search as se

def main(argv=None):
    ap = argparse.ArgumentParser(description="Search an OKF bundle.")
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--text", default="")
    ap.add_argument("--type", default=None)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--status", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    root = ob.find_bundle_root(args.path)
    model = om.build_model(root)
    results = se.search(model, text=args.text, ctype=args.type,
                        tag=args.tag, status=args.status, limit=args.limit)

    if args.as_json:
        print(json.dumps({"root": str(root), "count": len(results),
                          "results": results}, indent=2))
        return 0

    if not results:
        print("No matches.")
        return 0
    for r in results:
        line = "%s  [%s]  %s" % (r["id"], r["type"] or "?", r["title"])
        if r["score"]:
            line += "  (score %d)" % r["score"]
        print(line)
        if r["related"]:
            print("    related: " + ", ".join(r["related"]))
    print("\n%d match(es)." % len(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())
