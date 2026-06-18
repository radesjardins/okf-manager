# scripts/okf_search.py
"""In-memory ranked search over the normalized model (okf_model.build_model).
Pure: never touches the filesystem. This is the seam a future SQLite/MCP-backed
search replaces behind the same `search()` signature (design §7)."""

def _terms(text):
    return [t for t in text.lower().split() if t]

def _hits(field, terms):
    low = str(field).lower()
    return sum(low.count(t) for t in terms)

def related(model, cid):
    """Concept ids linked to or from cid (resolved links only), sorted."""
    out = set()
    for lk in model["links"]:
        if not lk["resolved"]:
            continue
        if lk["src"] == cid:
            out.add(lk["dst"])
        elif lk["dst"] == cid:
            out.add(lk["src"])
    return sorted(out)

def search(model, text="", ctype=None, tag=None, status=None, limit=None):
    """Return ranked results: [{id, path, title, type, score, related}].
    Filters (ctype/tag/status) are exact, case-insensitive, and ANDed. `text` is
    a substring match scored title(5) > description(3) > body(1); a text query
    with no hit is dropped. With no text, every match scores 0 and results are
    id-sorted.
    Reserved files (index.md/log.md) are excluded."""
    terms = _terms(text)
    ct = ctype.lower() if ctype else None
    tg = tag.lower() if tag else None
    st = status.lower() if status else None
    results = []
    for cid, f in model["files"].items():
        if f["reserved"]:
            continue
        meta = f.get("meta", {})
        if ct is not None and str(f.get("type", "")).lower() != ct:
            continue
        if st is not None and str(meta.get("status", "")).lower() != st:
            continue
        if tg is not None:
            tags = meta.get("tags", [])
            tags = tags if isinstance(tags, list) else [tags]
            if tg not in [str(x).lower() for x in tags]:
                continue
        title = str(meta.get("title") or "")
        desc = str(meta.get("description") or "")
        score = 0
        if terms:
            score = (5 * _hits(title, terms) + 3 * _hits(desc, terms)
                     + 1 * _hits(f.get("body", ""), terms))
            if score == 0:
                continue
        results.append({"id": cid, "path": f["path"], "title": title or cid,
                        "type": f.get("type", ""), "score": score,
                        "related": related(model, cid)})
    results.sort(key=lambda r: (-r["score"], r["id"]))
    return results[:limit] if limit is not None else results
