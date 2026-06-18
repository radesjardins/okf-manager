# scripts/okf_log.py
"""Generate, prepend to, validate, and append to the bundle's log.md
(newest-first, ISO 'YYYY-MM-DD' headings, bold action-prefixed bullets)."""
import re
from pathlib import Path
import okf_io as oio

DATE_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2})\s*$")

def new_log(name):
    return "# %s Log\n" % name

def prepend_entry(text, date, action, message):
    """Insert '* **action**: message' under a '## date' heading (newest-first).
    Creates the date heading (just below the title) if it isn't present."""
    bullet = "* **%s**: %s" % (action, message)
    lines = text.splitlines() if text.strip() else ["# Log"]
    title_end = 0
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            title_end = i + 1
            break
    for i in range(title_end, len(lines)):
        m = DATE_RE.match(lines[i])
        if m and m.group(1) == date:
            lines.insert(i + 1, bullet)
            return "\n".join(lines).strip("\n") + "\n"
    # blank separator only when there's a title above the new date heading
    block = (["", "## %s" % date, bullet] if title_end else ["## %s" % date, bullet])
    for off, b in enumerate(block):
        lines.insert(title_end + off, b)
    return "\n".join(lines).strip("\n") + "\n"

def validate_log(log_text):
    findings = []
    if not log_text.strip():
        return findings
    lines = log_text.splitlines()
    if not any(ln.startswith("# ") for ln in lines):
        findings.append({"severity": "warning", "code": "log-format", "id": "log",
                         "message": "log.md has no '# ...' title"})
    dates = [m.group(1) for ln in lines for m in [DATE_RE.match(ln)] if m]
    if dates != sorted(dates, reverse=True):
        findings.append({"severity": "warning", "code": "log-format", "id": "log",
                         "message": "date headings are not newest-first"})
    return findings

def append(root, name, date, action, message):
    """Add an entry to the log's history (inserted newest-first at the top of
    root/log.md), creating the file if absent. Preserves newline style."""
    p = Path(root) / "log.md"
    if p.exists():
        text, nl = oio.read(p)
    else:
        text, nl = new_log(name), "\n"
    oio.write(p, prepend_entry(text, date, action, message), nl)

if __name__ == "__main__":
    pass
