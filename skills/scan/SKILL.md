---
name: scan
description: >
  Mine a repo or a PARA/notes folder for knowledge worth importing into an OKF
  bundle — list the candidate files, apply the capture filter, and propose what
  to import and where it belongs, nothing without confirmation. Use when the user
  says "scan this folder for notes to import", "what in this repo is worth
  capturing", "triage my notes into the bundle", or points at a folder of mixed files.
argument-hint: "<folder to scan> [into <bundle path>]"
user-invocable: true
allowed-tools: Bash Read Glob
---

# okfm: scan

Triage a folder into the bundle without dumping noise into it.

1. List the candidates (markdown + convertible text formats) with metadata:
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/okf_scan.py" <folder> --bundle <root> --json`
   Each candidate carries `ext`, `size`, `first_heading`, `has_frontmatter`, and `in_bundle`.
2. **Apply the capture filter** to each candidate — keep only what is Relevant, Actionable, has Depth, and is Authoritative. Skip raw article dumps, image-only notes, secrets, uncurated transcripts, and anything already `in_bundle`. Read promising files to judge; use `first_heading` to prioritize.
3. **Propose** a short import plan: for each kept file, the dest path (which domain folder it belongs in) and the route — `.md` → `add`, everything else → `convert`. Show it as a list; import nothing yet.
4. On the user's OK, run each item through `add` / `convert` (each with its own `--dry-run` preview as those skills define).
5. Finish with `check` and a one-line summary of what was imported and what you skipped (and why).
