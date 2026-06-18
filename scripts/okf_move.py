# scripts/okf_move.py
"""CLI: link-safe rename/relocate of a concept. Moves the file, rewrites every
inbound backlink's destination to the new id (in the configured link style),
regenerates the index, and logs the move. --dry-run previews."""
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
import okf_bundle as ob
import okf_config as cfg
import okf_io as oio
import okf_model as om
import okf_index as oi
import okf_log as olog
import okf_linkedit as le

def _err(msg, as_json):
    if as_json:
        print(json.dumps({"error": msg}))
    else:
        print(msg, file=sys.stderr)
    return 2

def main(argv=None):
    ap = argparse.ArgumentParser(description="Link-safe move/rename of a concept.")
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--bundle", default=None)
    ap.add_argument("--dry-run", action="store_true", dest="dry_run")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    src = Path(args.src)
    dst = Path(args.dst)
    root = Path(args.bundle) if args.bundle else Path(ob.find_bundle_root(src))
    root = root.resolve()
    src = (src if src.is_absolute() else root / src).resolve()
    dst = (dst if dst.is_absolute() else root / dst).resolve()

    # both paths must stay inside the bundle (mirrors okf_new/okf_add)
    for label, p in (("source", src), ("destination", dst)):
        try:
            p.relative_to(root)
        except ValueError:
            return _err("%s is outside the bundle: %s" % (label, p), args.as_json)
    if src.name in ob.RESERVED or dst.name in ob.RESERVED:
        return _err("cannot move a reserved file (index.md / log.md)", args.as_json)
    if src == dst:
        return _err("source and destination are the same", args.as_json)
    if not src.exists():
        return _err("source not found: %s" % src, args.as_json)
    if dst.exists():
        return _err("destination exists: %s" % dst, args.as_json)

    config = cfg.load_config(root)
    style = config["link_style"]
    old_cid = ob.concept_id(src, root)
    new_cid = ob.concept_id(dst, root)

    model = om.build_model(root)
    backlinks = {}
    for cid, f in model["files"].items():
        if f["reserved"]:
            continue   # index/log are regenerated; skip to avoid redundant rewrite
        n = sum(1 for lk in f["links"] if lk["resolved"] and lk["dst"] == old_cid)
        if n:
            backlinks[cid] = (f["path"], n)

    if args.dry_run:
        out = {"move": {"from": old_cid, "to": new_cid},
               "backlinks": [{"id": cid, "count": cnt}
                             for cid, (p, cnt) in sorted(backlinks.items())],
               "updates": [str(root / "index.md"), str(root / "log.md")]}
        if args.as_json:
            print(json.dumps(out, indent=2))
        else:
            print("Move %s -> %s" % (old_cid, new_cid))
            for cid, (p, cnt) in sorted(backlinks.items()):
                print("  rewrite %d link(s) in %s" % (cnt, cid))
        return 0

    dst.parent.mkdir(parents=True, exist_ok=True)
    text, nl = oio.read(src)
    oio.write(dst, text, nl)
    src.unlink()

    # src is now gone; if a backlink rewrite or reindex fails, surface it cleanly
    # (the file has already moved) so the user knows to run check, rather than
    # dumping a raw traceback.
    try:
        for cid, (path, cnt) in backlinks.items():
            link_path, link_src = Path(path), cid
            if cid == old_cid:                 # the moved file linked to itself
                link_path, link_src = dst, new_cid
            btext, bnl = oio.read(link_path)
            new_btext, _ = le.rewrite_targets(btext, link_src, old_cid, new_cid, style=style)
            oio.write(link_path, new_btext, bnl)

        oi.regenerate(root, config["name"])
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        olog.append(root, config["name"], date, "Move", "%s -> %s" % (old_cid, new_cid))
    except Exception as e:  # noqa: BLE001 - want any failure surfaced, not a traceback
        return _err("file moved to %s but a follow-up update failed (%s); run check"
                    % (dst, e), args.as_json)

    print(json.dumps({"moved": {"from": old_cid, "to": new_cid}}) if args.as_json
          else "Moved %s -> %s" % (old_cid, new_cid))
    return 0

if __name__ == "__main__":
    sys.exit(main())
