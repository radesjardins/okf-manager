# scripts/okf_links.py
"""Markdown link parsing and resolution to OKF concept ids."""
import re, posixpath
from pathlib import PurePosixPath

LINK_RE = re.compile(r"\[(?P<text>[^\]]*)\]\((?P<target>[^)]+)\)")
_FENCE_RE = re.compile(r"(`{3,}|~{3,})")

def _fenced_spans(body):
    """Char ranges covered by ``` / ~~~ fenced code blocks. Links inside these
    are examples (e.g. seeded file content), not real OKF cross-links."""
    spans, fence, start, pos = [], None, None, 0
    for line in body.splitlines(keepends=True):
        m = _FENCE_RE.match(line.lstrip())
        if fence is None:
            if m:
                fence, start = m.group(1)[0], pos
        elif m and m.group(1)[0] == fence:
            spans.append((start, pos + len(line)))
            fence = None
        pos += len(line)
    if fence is not None:                 # unclosed fence runs to end of body
        spans.append((start, pos))
    return spans

def find_links(body):
    spans = _fenced_spans(body)
    out = []
    for m in LINK_RE.finditer(body):
        if any(s <= m.start() < e for s, e in spans):
            continue                      # skip links inside fenced code blocks
        out.append({
            "text": m.group("text"),
            "target": m.group("target").strip(),
            "start": m.start(),
            "end": m.end(),
        })
    return out

def is_external(target):
    return "://" in target or target.startswith("mailto:")

def resolve_target(target, source_id):
    """Resolve a link target to a concept id (path minus .md), or None for
    external/empty links. source_id is the concept id of the linking file."""
    if is_external(target):
        return None
    path_part = target.split("#", 1)[0].strip()
    if not path_part:
        return None
    if path_part.startswith("/"):
        cid = path_part.lstrip("/")
    else:
        base = PurePosixPath(source_id).parent
        cid = posixpath.normpath(str(base / path_part))
    return cid[:-3] if cid.endswith(".md") else cid
