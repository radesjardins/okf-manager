# scripts/okf_add.py
"""CLI: import an existing markdown file into the bundle. Ensures frontmatter
exists and fills only the MISSING keys from the supplied values; existing
frontmatter is preserved. Then places the file and wires it into index + log."""
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
import okf_bundle as ob
import okf_config as cfg
import okf_io as oio
import okf_index as oi
import okf_log as olog
import okf_frontmatter as fm
import okf_fmwrite as fmw

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def normalize_import(text, defaults):
    """defaults: ordered [(key, value), ...]. If text has no frontmatter, build
    a fresh block from the non-empty defaults and keep the text as body. If it
    does, fill only keys that are missing/blank."""
    # detect frontmatter structurally (a fenced block), so a malformed-but-fenced
    # block isn't mistaken for "no frontmatter" and shoved into the body
    _, _, has_fm = fm.split_frontmatter(text)
    if not has_fm:
        pairs = [(k, v) for k, v in defaults if v]
        return fmw.render_frontmatter(pairs) + "\n" + text.strip() + "\n"
    meta, _, _ = fm.parse_frontmatter(text)
    out = text
    for k, v in defaults:
        present = meta.get(k)
        filled = (isinstance(present, list) and present) or \
                 (isinstance(present, str) and present.strip())
        if v and not filled:
            out = fmw.set_key(out, k, v)
    return out

def _err(msg, as_json):
    if as_json:
        print(json.dumps({"error": msg}))
    else:
        print(msg, file=sys.stderr)
    return 2

def main(argv=None):
    ap = argparse.ArgumentParser(description="Import existing markdown into an OKF bundle.")
    ap.add_argument("src", help="existing markdown file to import")
    ap.add_argument("dest", help="destination .md path (relative to the bundle, or absolute)")
    ap.add_argument("--type", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--tag", action="append", default=[], dest="tags")
    ap.add_argument("--resource", default="", help="URI identifying the underlying asset")
    ap.add_argument("--timestamp", default=None)
    ap.add_argument("--curated-by", default="agent", dest="curated_by")
    ap.add_argument("--bundle", default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    src = Path(args.src)
    if not src.exists():
        return _err("source not found: %s" % src, args.as_json)
    dest = Path(args.dest)
    root = Path(args.bundle) if args.bundle else Path(ob.find_bundle_root(dest if dest.is_absolute() else Path.cwd()))
    root = root.resolve()
    dest = (dest if dest.is_absolute() else root / dest).resolve()

    # keep every write inside the bundle (mirrors okf_new's guard)
    try:
        dest.relative_to(root)
    except ValueError:
        return _err("destination is outside the bundle: %s" % dest, args.as_json)

    if args.timestamp:
        try:
            datetime.fromisoformat(args.timestamp.replace("Z", "+00:00"))
        except ValueError:
            return _err("invalid --timestamp (use ISO 8601): %s" % args.timestamp, args.as_json)

    if dest.exists() and not args.force:
        return _err("refusing to overwrite %s (use --force)" % dest, args.as_json)

    config = cfg.load_config(root)
    name = config["name"]
    ts = args.timestamp or now_iso()

    if args.dry_run:
        updates = [str(p) for p in (root / "index.md", root / "log.md") if p.exists()]
        creates, dest_str = [], str(dest)
        (updates if dest.exists() else creates).append(dest_str)  # --force overwrites = update
        out = {"root": str(root), "creates": creates, "updates": updates}
        print(json.dumps(out, indent=2) if args.as_json else "Would import to %s" % dest)
        return 0

    defaults = [("type", args.type), ("title", args.title),
                ("description", args.description), ("resource", args.resource),
                ("tags", args.tags), ("timestamp", ts), ("curated_by", args.curated_by)]
    text, nl = oio.read(src)
    dest.parent.mkdir(parents=True, exist_ok=True)
    oio.write(dest, normalize_import(text, defaults), nl)   # preserve the source file's newline
    oi.regenerate(root, name)
    cid = ob.concept_id(dest, root)
    olog.append(root, name, ts[:10], "Add", "imported %s" % cid)

    print(json.dumps({"imported": str(dest), "id": cid}) if args.as_json
          else "Imported %s" % dest)
    return 0

if __name__ == "__main__":
    sys.exit(main())
