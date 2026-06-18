# scripts/okf_bundle.py
"""Bundle root detection and concept-file iteration."""
from pathlib import Path

RESERVED = {"index.md", "log.md"}

def find_bundle_root(start):
    p = Path(start).resolve()
    base = p if p.is_dir() else p.parent
    cur, found_index = base, None
    while True:
        if (cur / "okf.json").exists():
            return cur
        if (cur / "index.md").exists():
            found_index = cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return found_index or base

def load_indexignore(root):
    f = Path(root) / ".indexignore"
    if not f.exists():
        return []
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line.rstrip("/"))
    return out

def iter_concept_files(root):
    """Yield every .md path under root (including reserved files), skipping
    directories named in .indexignore."""
    root = Path(root)
    patterns = load_indexignore(root)
    for path in sorted(root.rglob("*.md")):
        rel_dirs = path.relative_to(root).parts[:-1]
        if any(part in patterns for part in rel_dirs):
            continue
        yield path

def concept_id(path, root):
    rel = Path(path).relative_to(root).as_posix()
    return rel[:-3] if rel.endswith(".md") else rel
