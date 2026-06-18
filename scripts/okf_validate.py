# scripts/okf_validate.py
"""Validation rules over the normalized model. Returns findings; never mutates."""
import okf_model as om
import okf_index as oi
import okf_log as olog

def _has_citations(body):
    """True if the body has a '# Citations' heading at any level."""
    for ln in body.splitlines():
        s = ln.strip()
        if s.startswith("#") and s.lstrip("#").strip().lower() == "citations":
            return True
    return False

def validate(root, max_age_days=180, now=None):
    model = om.build_model(root)
    findings = []

    def add(severity, code, cid, message):
        findings.append({"severity": severity, "code": code, "id": cid, "message": message})

    for cid, f in model["files"].items():
        if f["reserved"]:
            continue
        for e in f["errors"]:
            add("error", "frontmatter", cid, e)
        if not f["errors"] and not f["type"]:
            add("error", "missing-type", cid, "frontmatter has no non-empty 'type'")
        if f["meta"].get("curated_by") == "agent" and not _has_citations(f["body"]):
            add("info", "no-citations", cid, "agent-curated concept has no # Citations section")

    for lk in model["links"]:
        if not lk["resolved"]:
            add("warning", "broken-link", lk["src"],
                "link to '%s' has no target concept" % lk["target"])

    for cid in om.orphans(model):
        add("info", "orphan", cid, "not reachable from any index or link")

    for s in om.stale(model, max_age_days, now=now):
        add("info", "stale", s["id"], s["reason"])

    findings.extend(oi.validate_index(model))

    if model["files"].get("index") is not None and oi.index_version(model) != oi.OKF_VERSION:
        add("info", "okf-version", "index",
            "root index.md missing or unexpected okf_version (expected %s)" % oi.OKF_VERSION)

    log = model["files"].get("log")
    if log is not None:
        findings.extend(olog.validate_log(log.get("body", "")))

    return {
        "root": model["root"],
        "findings": findings,
        "counts": {"files": len(model["files"]), "links": len(model["links"])},
    }
