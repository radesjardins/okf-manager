# scripts/okf_fmwrite.py
"""Surgical, dependency-free writer for OKF YAML frontmatter.
set_key edits an existing block in place (preserving order, standalone
comments, and unknown keys); render_frontmatter builds a fresh block for new
files; normalize_type_first moves the required 'type' key to the top."""
import okf_frontmatter as fm

def serialize_scalar(v):
    s = str(v)
    if s == "":
        return '""'
    if s[0] in "\"'[" or s != s.strip():
        return '"%s"' % s
    return s

def serialize_value(value):
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(serialize_scalar(v) for v in value) + "]"
    return serialize_scalar(value)

def render_frontmatter(pairs):
    """Build a fresh frontmatter block (ending with the closing fence) from an
    ordered list of (key, value) pairs."""
    lines = ["%s: %s" % (k, serialize_value(v)) for k, v in pairs]
    return "---\n" + "\n".join(lines) + "\n---\n"

def _is_key_line(ln):
    s = ln.strip()
    return bool(s) and not s.startswith("#") and not s.startswith("- ") and ":" in ln

def set_key(text, key, value):
    """Set key=value in text's frontmatter. Replaces the value of an existing
    key in place (dropping any block-list items it owned), or appends a new key
    line before the closing fence. A fresh block is created if none exists.
    Any duplicate occurrences of the key are removed, since the reader is
    last-wins — leaving one would make the effective value disagree with ours.
    NOTE: an inline '# comment' on the exact replaced key line is not preserved;
    standalone comment lines always are."""
    new_line = "%s: %s" % (key, serialize_value(value))
    raw_fm, body, has_fm = fm.split_frontmatter(text)
    if not has_fm:
        return "---\n%s\n---\n\n%s" % (new_line, text)
    lines = raw_fm.splitlines()
    out, replaced, i = [], False, 0
    while i < len(lines):
        ln = lines[i]
        if _is_key_line(ln) and ln.partition(":")[0].strip() == key:
            if not replaced:
                out.append(new_line)   # first hit: insert here
                replaced = True
            i += 1
            while i < len(lines) and lines[i].strip().startswith("- "):
                i += 1   # drop block-list items belonging to this (first or duplicate) key
            continue
        out.append(ln)
        i += 1
    if not replaced:
        out.append(new_line)
    return "---\n" + "\n".join(out) + "\n---\n" + body

def normalize_type_first(text):
    """Move the 'type' key (with any standalone comment lines directly above it)
    to the top of the frontmatter. No-op if already first or absent.
    Assumes comments above 'type' document 'type', not the preceding key. Its
    only caller (check --fix) skips frontmatter containing comments, so the
    ambiguous "comment sandwiched between two keys" case never reaches here."""
    raw_fm, body, has_fm = fm.split_frontmatter(text)
    if not has_fm:
        return text
    lines = raw_fm.splitlines()
    type_idx = first_key = None
    for i, ln in enumerate(lines):
        if _is_key_line(ln):
            if first_key is None:
                first_key = i
            if ln.partition(":")[0].strip() == "type":
                type_idx = i
                break
    if type_idx is None or type_idx == first_key:
        return text
    start = type_idx
    while start - 1 >= 0 and lines[start - 1].strip().startswith("#"):
        start -= 1
    block = lines[start:type_idx + 1]
    rest = lines[:start] + lines[type_idx + 1:]
    return "---\n" + "\n".join(block + rest) + "\n---\n" + body
