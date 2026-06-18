# scripts/okf_model.py
"""Normalized in-memory model of a bundle: files, metadata, links.
This is the single source of truth for check/map and the seam a future
SQLite/MCP layer replaces (keep the build_model signature stable)."""
from pathlib import Path
from datetime import datetime, timezone

import okf_frontmatter as fm
import okf_bundle as ob
import okf_links as ol

def _parse_ts(value):
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None

def build_model(root):
    root = Path(root)
    files = {}
    for path in ob.iter_concept_files(root):
        cid = ob.concept_id(path, root)
        reserved = path.name in ob.RESERVED
        text = path.read_text(encoding="utf-8")
        if reserved:
            meta, body, errors = {}, text, []
        else:
            meta, body, errors = fm.parse_frontmatter(text)
        files[cid] = {
            "id": cid, "path": str(path), "name": path.name,
            "type": meta.get("type", "") if isinstance(meta.get("type", ""), str) else "",
            "meta": meta, "errors": errors, "reserved": reserved,
            "body": body, "links": [],
        }
    ids = set(files)
    links = []
    for cid, f in files.items():
        for lk in ol.find_links(f["body"]):
            if ol.is_external(lk["target"]):
                continue
            dst = ol.resolve_target(lk["target"], cid)
            rec = {"src": cid, "target": lk["target"], "dst": dst,
                   "resolved": dst in ids, "start": lk["start"], "end": lk["end"]}
            links.append(rec)
            f["links"].append(rec)
    return {"root": str(root), "files": files, "links": links}

def inbound_counts(model):
    counts = {cid: 0 for cid in model["files"]}
    for lk in model["links"]:
        if lk["resolved"]:
            counts[lk["dst"]] = counts.get(lk["dst"], 0) + 1
    return counts

def orphans(model):
    counts = inbound_counts(model)
    return sorted(cid for cid, f in model["files"].items()
                  if not f["reserved"] and counts.get(cid, 0) == 0)

def stale(model, max_age_days, now=None):
    now = now or datetime.now(timezone.utc)
    out = []
    for cid, f in model["files"].items():
        if f["reserved"]:
            continue
        ts = _parse_ts(f["meta"].get("timestamp", ""))
        if ts is None:
            out.append({"id": cid, "reason": "no/invalid timestamp"})
        elif (now - ts).days > max_age_days:
            out.append({"id": cid, "reason": "%dd old" % (now - ts).days})
    return out
