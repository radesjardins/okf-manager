# scripts/okf_frontmatter.py
"""Tolerant, dependency-free reader for OKF YAML frontmatter (read side).
Surgical editing arrives in Plan 2; this module only reads."""

FENCE = "---"

def split_frontmatter(text):
    """Return (raw_fm, body, has_fm). raw_fm excludes the fences."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != FENCE:
        return "", text, False
    for i in range(1, len(lines)):
        if lines[i].strip() == FENCE:
            return "".join(lines[1:i]), "".join(lines[i + 1:]), True
    return "", text, False  # no closing fence

def _split_inline_list(inner):
    items, buf, q = [], "", None
    for ch in inner:
        if q:
            buf += ch
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
            buf += ch
        elif ch == ",":
            items.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        items.append(buf)
    return items

def parse_scalar(value):
    v = value.strip()
    if len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]:
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [parse_scalar(x) for x in _split_inline_list(inner)] if inner else []
    return v

def parse_frontmatter(text):
    """Return (meta: dict, body: str, errors: list[str]). Never raises.
    Unknown keys are preserved in meta."""
    raw_fm, body, has_fm = split_frontmatter(text)
    if not has_fm:
        return {}, body, ["no parseable YAML frontmatter block"]
    meta, errors, current_key, block_list = {}, [], None, None
    for ln in raw_fm.splitlines():
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        stripped = ln.strip()
        if stripped.startswith("- "):
            if current_key is None:
                errors.append("list item without a key: %r" % stripped)
                continue
            if block_list is None:
                block_list = []
                meta[current_key] = block_list
            block_list.append(parse_scalar(stripped[2:]))
            continue
        if ":" in ln:
            key, _, val = ln.partition(":")
            current_key, block_list = key.strip(), None
            meta[current_key] = "" if val.strip() == "" else parse_scalar(val)
        else:
            errors.append("unparseable frontmatter line: %r" % ln)
    return meta, body, errors
