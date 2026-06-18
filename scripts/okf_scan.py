# scripts/okf_scan.py
"""Walk a target folder and list importable candidates (markdown + convertible
text formats) with light metadata, so the `scan` skill can apply the capture
filter and route accepted items through `add`/`convert`. Read-only."""
import argparse, json, sys
from pathlib import Path
import okf_bundle as ob
import okf_frontmatter as fm

CANDIDATE_EXTS = (".md", ".txt", ".html", ".htm", ".csv", ".json")
SKIP_DIRS = {".git", "node_modules", ".obsidian", "__pycache__", ".venv", ".idea"}

def _first_heading(raw, ext):
    if ext == ".md":
        _, body, _ = fm.split_frontmatter(raw)
        for ln in body.splitlines():
            if ln.startswith("# "):
                return ln[2:].strip()
        text = body
    else:
        text = raw
    for ln in text.splitlines():
        s = ln.strip()
        if s:
            return s[:80]
    return ""

def scan_candidates(target, bundle_root=None):
    """Return [{path, ext, size, first_heading, has_frontmatter, in_bundle}] for
    each candidate under target, skipping reserved files and noisy directories."""
    target = Path(target).resolve()
    broot = Path(bundle_root).resolve() if bundle_root else None
    out = []
    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(target).parts[:-1]):
            continue
        ext = path.suffix.lower()
        if ext not in CANDIDATE_EXTS or path.name in ob.RESERVED:
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        has_fm = ext == ".md" and fm.split_frontmatter(raw)[2]
        in_bundle = False
        if broot is not None:
            try:
                path.relative_to(broot)
                in_bundle = True
            except ValueError:
                in_bundle = False
        out.append({"path": str(path), "ext": ext, "size": path.stat().st_size,
                    "first_heading": _first_heading(raw, ext),
                    "has_frontmatter": bool(has_fm), "in_bundle": in_bundle})
    return out

def main(argv=None):
    ap = argparse.ArgumentParser(description="List importable candidates under a folder.")
    ap.add_argument("target")
    ap.add_argument("--bundle", default=None, help="bundle root, to flag in-bundle files")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    cands = scan_candidates(args.target, args.bundle)
    if args.as_json:
        print(json.dumps({"target": str(Path(args.target).resolve()),
                          "count": len(cands), "candidates": cands}, indent=2))
        return 0
    for c in cands:
        flag = " [in-bundle]" if c["in_bundle"] else ""
        print("%s  (%s, %d bytes)%s" % (c["path"], c["ext"], c["size"], flag))
        if c["first_heading"]:
            print("    %s" % c["first_heading"])
    print("\n%d candidate(s)." % len(cands))
    return 0

if __name__ == "__main__":
    sys.exit(main())
