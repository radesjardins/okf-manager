# scripts/okf_new.py
"""CLI: scaffold a new OKF concept (and optionally a bundle with --init).
Writes the file, regenerates the root index, and appends a log entry.
--dry-run previews; existing files are not overwritten without --force."""
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
import okf_bundle as ob
import okf_config as cfg
import okf_io as oio
import okf_index as oi
import okf_log as olog
import okf_fmwrite as fmw

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def build_concept(ctype, title, description, tags, timestamp, curated_by, body,
                  resource="", citations=None):
    pairs = [("type", ctype), ("title", title)]
    if description:
        pairs.append(("description", description))
    if resource:
        pairs.append(("resource", resource))
    if tags:
        pairs.append(("tags", tags))
    pairs += [("timestamp", timestamp), ("curated_by", curated_by)]
    block = fmw.render_frontmatter(pairs)
    body = (body or "").strip()
    if citations:
        cites = "\n".join("%d. %s" % (i + 1, c) for i, c in enumerate(citations))
        section = "# Citations\n\n" + cites
        body = (body + "\n\n" + section) if body else section
    return block + "\n" + (body + "\n" if body else "")

def _err(msg, as_json):
    if as_json:
        print(json.dumps({"error": msg}))
    else:
        print(msg, file=sys.stderr)
    return 2

def main(argv=None):
    ap = argparse.ArgumentParser(description="Scaffold a new OKF concept.")
    ap.add_argument("path", help="destination .md path (relative to the bundle, or absolute)")
    ap.add_argument("--type", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--tag", action="append", default=[], dest="tags")
    ap.add_argument("--resource", default="", help="URI identifying the underlying asset")
    ap.add_argument("--citation", action="append", default=[], dest="citations",
                    help="source URL/path; repeatable; emitted as a # Citations section")
    ap.add_argument("--body", default="")
    ap.add_argument("--timestamp", default=None)
    ap.add_argument("--curated-by", default="agent", dest="curated_by")
    ap.add_argument("--bundle", default=None, help="bundle root (default: auto-detect)")
    ap.add_argument("--init", action="store_true", help="also scaffold index.md/log.md/okf.json")
    ap.add_argument("--name", default=None, help="bundle name for --init")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    dest = Path(args.path)
    if args.bundle:
        root = Path(args.bundle)
    elif dest.is_absolute():
        root = Path(ob.find_bundle_root(dest))
    else:
        root = Path(ob.find_bundle_root(Path.cwd()))
    root = root.resolve()
    dest = (dest if dest.is_absolute() else root / dest).resolve()

    # keep every write inside the bundle: a dest that escapes root (absolute
    # elsewhere, or via '..') would crash concept_id and write outside the bundle
    try:
        dest.relative_to(root)
    except ValueError:
        return _err("destination is outside the bundle: %s" % dest, args.as_json)

    if args.timestamp:
        try:
            datetime.fromisoformat(args.timestamp.replace("Z", "+00:00"))
        except ValueError:
            return _err("invalid --timestamp (use ISO 8601): %s" % args.timestamp, args.as_json)

    config = cfg.load_config(root)
    name = args.name or config["name"]
    ts = args.timestamp or now_iso()

    if dest.exists() and not args.force:
        return _err("refusing to overwrite %s (use --force)" % dest, args.as_json)

    # index.md/log.md are always written (regenerate/append); classify each as a
    # create or update by whether it exists now. okf.json is created only on --init.
    creates, updates = [], []
    if args.init and not (root / "okf.json").exists():
        creates.append(str(root / "okf.json"))
    for fn in ("index.md", "log.md"):
        p = root / fn
        (updates if p.exists() else creates).append(str(p))
    creates.append(str(dest))

    if args.dry_run:
        out = {"root": str(root), "creates": creates, "updates": sorted(set(updates))}
        print(json.dumps(out, indent=2) if args.as_json
              else "Would create:\n  " + "\n  ".join(creates))
        return 0

    if args.init:
        root.mkdir(parents=True, exist_ok=True)
        if not (root / "index.md").exists():
            oio.write(root / "index.md", "# %s\n" % name)
        if not (root / "log.md").exists():
            oio.write(root / "log.md", olog.new_log(name))
        if not (root / "okf.json").exists():
            cfg.save_config(root, {"name": name})

    dest.parent.mkdir(parents=True, exist_ok=True)
    oio.write(dest, build_concept(args.type, args.title, args.description,
                                  args.tags, ts, args.curated_by, args.body,
                                  resource=args.resource, citations=args.citations))
    oi.regenerate(root, name)
    cid = ob.concept_id(dest, root)
    olog.append(root, name, ts[:10], "New", "added %s" % cid)

    print(json.dumps({"created": str(dest), "id": cid}) if args.as_json
          else "Created %s" % dest)
    return 0

if __name__ == "__main__":
    sys.exit(main())
