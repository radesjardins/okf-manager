# scripts/okf_seed.py
"""Seed OKF concepts from a structured source (offline, stdlib only).

Three modes, each a pure spec-builder plus a shared writer:
  - sqlite : one Table concept per table, with a # Schema column listing
  - openapi: one API Endpoint per path+method (OpenAPI), or one Schema per
             definition (JSON Schema), or one Schema for a bare document
  - tree   : one File concept per file under a directory (structure preserved)

The engine never touches the network. Web enrichment lives in the `enrich`
skill, which fetches pages itself and writes via `new`/`convert`."""
import argparse, json, sqlite3, sys
from datetime import datetime, timezone
from pathlib import Path
import okf_bundle as ob
import okf_config as cfg
import okf_io as oio
import okf_index as oi
import okf_log as olog
import okf_new as onew

def _slug(s):
    out = "".join(c.lower() if c.isalnum() else "-" for c in str(s))
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-") or "item"

def _quote_ident(name):
    return '"' + name.replace('"', '""') + '"'

# --- sqlite ------------------------------------------------------------------
def specs_from_sqlite(db_path, dest_dir):
    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%' ORDER BY name")
        specs = []
        for (t,) in cur.fetchall():
            cols = cur.execute("PRAGMA table_info(%s)" % _quote_ident(t)).fetchall()
            rows = ["| column | type | not null | pk |", "| --- | --- | --- | --- |"]
            for c in cols:   # (cid, name, type, notnull, dflt, pk)
                rows.append("| %s | %s | %s | %s |"
                            % (c[1], c[2] or "", "yes" if c[3] else "", "yes" if c[5] else ""))
            specs.append({
                "dest": "%s/%s.md" % (dest_dir, _slug(t)), "type": "Table", "title": t,
                "description": "Table %s (%d columns)." % (t, len(cols)),
                "resource": "sqlite://%s#%s" % (Path(db_path).name, t),
                "body": "# Schema\n\n" + "\n".join(rows) + "\n"})
        return specs
    finally:
        con.close()

# --- openapi / json schema ---------------------------------------------------
_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")

def _schema_body(sch):
    props = sch.get("properties") if isinstance(sch, dict) else None
    if not isinstance(props, dict) or not props:
        return ""
    required = set(sch.get("required") or [])
    rows = ["# Schema", "", "| field | type | required |", "| --- | --- | --- |"]
    for name in sorted(props):
        p = props[name] if isinstance(props[name], dict) else {}
        rows.append("| %s | %s | %s |" % (name, p.get("type", ""),
                                          "yes" if name in required else ""))
    return "\n".join(rows) + "\n"

def specs_from_openapi(obj, dest_dir):
    if not isinstance(obj, dict):
        return []
    if obj.get("openapi") or obj.get("swagger"):
        specs = []
        for path, item in sorted((obj.get("paths") or {}).items()):
            if not isinstance(item, dict):
                continue
            for method, op in sorted(item.items()):
                if method.lower() not in _METHODS:
                    continue
                op = op or {}
                lines = ["# Schema", ""]
                params = op.get("parameters") or []
                if params:
                    lines += ["| parameter | in | required |", "| --- | --- | --- |"]
                    for p in params:
                        if isinstance(p, dict):
                            lines.append("| %s | %s | %s |" % (p.get("name", ""), p.get("in", ""),
                                                               "yes" if p.get("required") else ""))
                summary = op.get("summary") or op.get("description") or ""
                specs.append({
                    "dest": "%s/%s.md" % (dest_dir, _slug(method + "-" + path)),
                    "type": "API Endpoint", "title": "%s %s" % (method.upper(), path),
                    "description": " ".join(str(summary).split())[:200],
                    "resource": path, "body": "\n".join(lines) + "\n"})
        return specs
    # JSON Schema: one concept per named definition, else one for the document
    defs = {}
    for key in ("definitions", "$defs"):
        if isinstance(obj.get(key), dict):
            defs.update(obj[key])
    comp = obj.get("components")
    if isinstance(comp, dict) and isinstance(comp.get("schemas"), dict):
        defs.update(comp["schemas"])
    if defs:
        out = []
        for name, sch in sorted(defs.items()):
            sch = sch if isinstance(sch, dict) else {}
            out.append({"dest": "%s/%s.md" % (dest_dir, _slug(name)), "type": "Schema",
                        "title": name, "description": " ".join(str(sch.get("description", "")).split()),
                        "resource": "#/definitions/%s" % name, "body": _schema_body(sch)})
        return out
    return [{"dest": "%s/schema.md" % dest_dir, "type": "Schema", "title": "Schema",
             "description": " ".join(str(obj.get("description", "")).split()),
             "resource": "", "body": _schema_body(obj)}]

# --- directory tree ----------------------------------------------------------
_TEXT_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".md", ".txt", ".json", ".html", ".css",
             ".sh", ".yml", ".yaml", ".toml", ".cfg", ".ini", ".rs", ".go", ".java",
             ".c", ".h", ".cpp", ".rb", ".php", ".sql"}
_SKIP_DIR = {".git", "node_modules", "__pycache__", ".venv", "venv", ".idea", ".vscode",
             "dist", "build", ".mypy_cache", ".pytest_cache"}

def specs_from_tree(src_dir, dest_dir, max_bytes=20000):
    src = Path(src_dir)
    specs = []
    for p in sorted(src.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(src)
        if any(part in _SKIP_DIR or part.startswith(".") for part in rel.parts):
            continue
        relposix = rel.as_posix()
        body = "# File\n\n- path: `%s`\n- size: %d bytes\n" % (relposix, p.stat().st_size)
        if p.suffix.lower() in _TEXT_EXT and p.stat().st_size <= max_bytes:
            try:
                content = p.read_text(encoding="utf-8").rstrip()
                body += "\n```%s\n%s\n```\n" % (p.suffix.lstrip("."), content)
            except (UnicodeDecodeError, OSError):
                pass
        dest = "%s/%s" % (dest_dir, relposix if relposix.endswith(".md") else relposix + ".md")
        specs.append({"dest": dest, "type": "File", "title": rel.name,
                      "description": "File `%s`." % relposix, "resource": relposix, "body": body})
    return specs

# --- dispatch + writer -------------------------------------------------------
def detect_mode(src):
    p = Path(src)
    if p.is_dir():
        return "tree"
    if p.suffix.lower() in (".db", ".sqlite", ".sqlite3"):
        return "sqlite"
    try:
        with open(p, "rb") as fh:
            if fh.read(16).startswith(b"SQLite format 3"):
                return "sqlite"
    except OSError:
        pass
    return "openapi"

def build_specs(mode, src, dest_dir):
    if mode == "sqlite":
        return specs_from_sqlite(src, dest_dir)
    if mode == "tree":
        return specs_from_tree(src, dest_dir)
    return specs_from_openapi(json.loads(Path(src).read_text(encoding="utf-8")), dest_dir)

def _err(msg, as_json):
    print(json.dumps({"error": msg}) if as_json else msg, file=None if as_json else sys.stderr)
    return 2

def main(argv=None):
    ap = argparse.ArgumentParser(description="Seed OKF concepts from a structured source.")
    ap.add_argument("src", help="sqlite db, OpenAPI/JSON-Schema file, or a directory")
    ap.add_argument("--bundle", default=None, help="bundle root (default: auto-detect)")
    ap.add_argument("--mode", default="auto", choices=["auto", "sqlite", "openapi", "tree"])
    ap.add_argument("--dest-dir", default=None, dest="dest_dir",
                    help="subdirectory for seeded concepts (default: slug of the source name)")
    ap.add_argument("--timestamp", default=None)
    ap.add_argument("--curated-by", default="agent", dest="curated_by")
    ap.add_argument("--force", action="store_true", help="overwrite existing concept files")
    ap.add_argument("--dry-run", action="store_true", dest="dry_run")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)

    src = Path(args.src)
    if not src.exists():
        return _err("source not found: %s" % src, args.as_json)
    root = Path(args.bundle).resolve() if args.bundle else Path(ob.find_bundle_root(Path.cwd())).resolve()
    mode = detect_mode(src) if args.mode == "auto" else args.mode
    dest_dir = args.dest_dir or _slug(src.stem if src.is_file() else src.name) or "seed"
    ts = args.timestamp or onew.now_iso()
    name = cfg.load_config(root)["name"]

    try:
        specs = build_specs(mode, str(src), dest_dir)
    except (sqlite3.Error, ValueError, OSError) as e:
        return _err("could not read source as %s: %s" % (mode, e), args.as_json)
    if not specs:
        return _err("no concepts found in source (mode=%s)" % mode, args.as_json)

    # provenance: every seeded concept cites the source it was generated from
    src_label = "Seeded from `%s` (%s)" % (src.name, mode)
    for s in specs:
        s.setdefault("citations", [src_label])

    # keep every dest inside the bundle
    contained = []
    for s in specs:
        dest = (root / s["dest"]).resolve()
        try:
            dest.relative_to(root)
            contained.append((s, dest))
        except ValueError:
            pass

    if args.dry_run:
        out = {"root": str(root), "mode": mode, "dest_dir": dest_dir,
               "would_create": [s["dest"] for s, _ in contained]}
        print(json.dumps(out, indent=2) if args.as_json
              else "Would seed %d concept(s) (mode=%s) into %s/" % (len(contained), mode, dest_dir))
        return 0

    created, skipped = [], []
    for s, dest in contained:
        if dest.exists() and not args.force:
            skipped.append(s["dest"]); continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        oio.write(dest, onew.build_concept(
            s["type"], s["title"], s.get("description", ""), s.get("tags", []),
            ts, args.curated_by, s.get("body", ""),
            resource=s.get("resource", ""), citations=s.get("citations") or None))
        created.append(s["dest"])
    if created:
        oi.regenerate(root, name)
        olog.append(root, name, ts[:10], "Seed",
                    "seeded %d concept(s) from %s (mode=%s)" % (len(created), src.name, mode))

    result = {"created": created, "skipped": skipped, "mode": mode}
    print(json.dumps(result, indent=2) if args.as_json
          else "Seeded %d concept(s); skipped %d existing." % (len(created), len(skipped)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
