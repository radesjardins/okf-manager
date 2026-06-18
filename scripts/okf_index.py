# scripts/okf_index.py
"""Generate, parse, validate, and regenerate the bundle's root index.md.
The engine owns the index: sections are grouped by top-level directory and
bullets come from each concept's frontmatter (title + description), so
regeneration is lossless when frontmatter is filled in."""
from pathlib import Path
import okf_links as ol
import okf_io as oio
import okf_model as om
import okf_fmwrite as fmw
import okf_frontmatter as fm

# OKF spec version this engine targets. Declared in the root index.md frontmatter
# (the only place the spec permits index.md frontmatter).
OKF_VERSION = "0.1"

def humanize(name):
    return name.replace("-", " ").replace("_", " ").strip().title()

def _bullet(model, cid, base_dir):
    """Bullet linking concept `cid` from an index in `base_dir` (a relative link)."""
    meta = model["files"][cid].get("meta", {})
    title = meta.get("title") or humanize(cid.split("/")[-1])
    rel = cid[len(base_dir) + 1:] if base_dir else cid
    line = "* [%s](%s.md)" % (title, rel)
    desc = meta.get("description")
    if isinstance(desc, str) and desc.strip():
        line += " — %s" % " ".join(desc.split())   # collapse newlines so the bullet stays one line
    return line

def _index_dirs(concepts):
    """Map the concept set to the directories that need an index. Returns
    (index_dirs, direct, children): every ancestor directory ('' = root),
    the concepts directly in each, and each dir's immediate child dirs."""
    index_dirs, direct = {""}, {}
    for cid in concepts:
        parts = cid.split("/")
        parent_parts = parts[:-1]
        direct.setdefault("/".join(parent_parts), []).append(cid)
        for i in range(len(parent_parts) + 1):
            index_dirs.add("/".join(parent_parts[:i]))
    children = {}
    for d in index_dirs:
        if d:
            children.setdefault("/".join(d.split("/")[:-1]), []).append(d)
    return index_dirs, direct, children

def _dir_body(model, d, name, direct, children):
    title = name if d == "" else humanize(d.split("/")[-1])
    lines = ["# %s" % title, ""]
    for cid in sorted(direct.get(d, [])):
        lines.append(_bullet(model, cid, d))
    if direct.get(d):
        lines.append("")
    childs = sorted(children.get(d, []))
    if childs:
        lines.append("## Subdirectories")
        for c in childs:
            seg = c.split("/")[-1]
            lines.append("* [%s](%s/index.md)" % (humanize(seg), seg))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"

def generate_index_tree(model, name, fm_pairs=None):
    """Return {dir_relpath: index_text} for every directory needing an index.
    '' is the bundle root and carries the okf_version frontmatter (with unknown
    keys in fm_pairs preserved); child indexes carry none, per the spec."""
    concepts = sorted(cid for cid, f in model["files"].items() if not f["reserved"])
    index_dirs, direct, children = _index_dirs(concepts)
    preserved = [(k, v) for (k, v) in (fm_pairs or []) if k != "okf_version"]
    pairs = [("okf_version", OKF_VERSION)] + preserved
    tree = {}
    for d in index_dirs:
        body = _dir_body(model, d, name, direct, children)
        tree[d] = (fmw.render_frontmatter(pairs) + "\n" + body) if d == "" else body
    return tree

def generate_index_text(model, name, fm_pairs=None):
    """Root index.md text (the '' entry of the tree). Kept for callers that only
    touch the root index."""
    return generate_index_tree(model, name, fm_pairs)[""]

def root_fm_pairs(root):
    """Existing root index.md frontmatter as ordered (key, value) pairs, or []."""
    p = Path(root) / "index.md"
    if not p.exists():
        return []
    meta, _, _ = fm.parse_frontmatter(p.read_text(encoding="utf-8"))
    return list(meta.items())

def index_version(model):
    """The okf_version declared in the root index.md, or None."""
    idx = model["files"].get("index")
    if idx is None:
        return None
    meta, _, _ = fm.parse_frontmatter(idx["body"])
    v = meta.get("okf_version")
    return v if isinstance(v, str) else None

def index_entries(index_text, from_cid="index"):
    """Set of ids the index links to, resolved relative to the index's own cid."""
    out = set()
    for lk in ol.find_links(index_text):
        if ol.is_external(lk["target"]):
            continue
        cid = ol.resolve_target(lk["target"], from_cid)
        if cid:
            out.add(cid)
    return out

def _index_files(model):
    """{cid: file} for every index.md in the bundle (root and nested)."""
    return {cid: f for cid, f in model["files"].items()
            if f["reserved"] and f["name"] == "index.md"}

def validate_index(model):
    """Findings for concepts listed in no index and index links pointing at
    things that no longer exist. Pure (does not write). Spans the nested index
    tree: a concept reachable from any index.md is considered listed.
    Note: a concept absent from every index will often also trip okf_model's
    'orphan' check; the two findings are intentionally distinct and may co-fire."""
    findings = []
    expected = {cid for cid, f in model["files"].items() if not f["reserved"]}
    indexes = _index_files(model)
    if not indexes:
        for cid in sorted(expected):
            findings.append({"severity": "info", "code": "index-drift", "id": cid,
                             "message": "no index.md; concept is unlisted"})
        return findings
    listed, allids = set(), set(model["files"])
    for icid, f in indexes.items():
        listed |= index_entries(f.get("body", ""), icid)
    for cid in sorted(expected - listed):
        findings.append({"severity": "info", "code": "index-drift", "id": cid,
                         "message": "not listed in any index.md"})
    for cid in sorted(listed - allids):
        findings.append({"severity": "warning", "code": "index-drift", "id": cid,
                         "message": "index.md links to a missing concept"})
    return findings

def regenerate(root, name):
    """Rebuild the full index tree (root + nested), preserving the root index's
    newline style. Existing index.md in now-empty directories are left in place
    (never destructive); a stale one surfaces as index-drift on the next check."""
    root = Path(root)
    rp = root / "index.md"
    nl = "\n"
    if rp.exists():
        _, nl = oio.read(rp)
    pairs = root_fm_pairs(root)
    model = om.build_model(root)
    for d, text in generate_index_tree(model, name, pairs).items():
        p = root / d / "index.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        oio.write(p, text, nl)
