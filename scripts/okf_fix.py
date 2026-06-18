# scripts/okf_fix.py
"""Build and apply the safe set of --fix changes: regenerate the root index and
move 'type' to the top of frontmatter. Never deletes files or retargets links.
A change is {path, action: 'index'|'frontmatter', after: <full new text>}."""
from pathlib import Path
import okf_io as oio
import okf_model as om
import okf_index as oi
import okf_fmwrite as fmw
import okf_frontmatter as fm

def build_fix_plan(root, name):
    root = Path(root)
    model = om.build_model(root)
    changes = []

    for d, text in oi.generate_index_tree(model, name, oi.root_fm_pairs(root)).items():
        idx_path = root / d / "index.md"
        cur = oio.read(idx_path)[0] if idx_path.exists() else ""
        if cur != text:
            changes.append({"path": str(idx_path), "action": "index", "after": text})

    for cid, f in model["files"].items():
        if f["reserved"]:
            continue
        cur, _ = oio.read(f["path"])
        raw_fm, _, has_fm = fm.split_frontmatter(cur)
        if not has_fm:
            continue
        if any(ln.strip().startswith("#") for ln in raw_fm.splitlines()):
            continue   # leave comment-bearing frontmatter untouched
        new = fmw.normalize_type_first(cur)
        if new != cur:
            changes.append({"path": f["path"], "action": "frontmatter", "after": new})

    return {"root": str(root), "changes": changes}

def apply_plan(plan):
    for ch in plan["changes"]:
        p = Path(ch["path"])
        nl = oio.read(p)[1] if p.exists() else "\n"
        oio.write(p, ch["after"], nl)
    return len(plan["changes"])
