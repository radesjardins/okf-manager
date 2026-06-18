# scripts/okf_io.py
"""Newline-preserving UTF-8 file I/O for the write side.
Read normalizes to LF internally; write re-applies the file's original
newline so editing a CRLF bundle on Windows doesn't churn every line."""
from pathlib import Path

def detect_newline(raw):
    if "\r\n" in raw:
        return "\r\n"
    if "\r" in raw:
        return "\r"
    return "\n"

def read(path):
    """Return (text_normalized_to_LF, original_newline)."""
    raw = Path(path).read_bytes().decode("utf-8")
    nl = detect_newline(raw)
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    return text, nl

def write(path, text, newline="\n"):
    """Write text using the given newline style. Input is normalized to LF first,
    so a stray CRLF in `text` can't become a doubled '\\r\\r\\n' on output."""
    lf = text.replace("\r\n", "\n").replace("\r", "\n")
    out = lf.replace("\n", newline) if newline != "\n" else lf
    Path(path).write_bytes(out.encode("utf-8"))
