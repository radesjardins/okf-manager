"""Surgical link rewriting: replace only the destination substring of matching
markdown links, preserving every other byte (link text, other links, anchors)."""
import posixpath
from pathlib import PurePosixPath
import okf_links as ol

def target_for(new_cid, source_id, style="absolute", anchor=""):
    """Build a link target string pointing at new_cid from source_id."""
    suffix = "#" + anchor if anchor else ""
    if style == "relative":
        base = str(PurePosixPath(source_id).parent)
        return posixpath.relpath(new_cid, base) + ".md" + suffix
    return "/" + new_cid + ".md" + suffix

def rewrite_targets(text, source_id, old_cid, new_cid, style="absolute"):
    """Return (new_text, count). Rewrites every link in text whose resolved
    target == old_cid to point at new_cid, changing only the destination.
    Processes matches right-to-left so byte offsets stay valid."""
    count = 0
    for lk in sorted(ol.find_links(text), key=lambda l: l["start"], reverse=True):
        tgt = lk["target"]
        if ol.is_external(tgt) or ol.resolve_target(tgt, source_id) != old_cid:
            continue
        anchor = tgt.split("#", 1)[1] if "#" in tgt else ""
        new_target = target_for(new_cid, source_id, style, anchor)
        seg = text[lk["start"]:lk["end"]]
        cut = seg.index("](")   # link text has no ']', so the first '](' is the true boundary
        new_seg = seg[:cut + 2] + new_target + ")"
        text = text[:lk["start"]] + new_seg + text[lk["end"]:]
        count += 1
    return text, count
