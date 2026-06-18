---
name: add
description: >
  Import existing markdown into an OKF knowledge bundle — apply the capture
  filter, propose placement, fill in missing frontmatter, and wire it into the
  index. Use when the user says "import this note", "add this file to my
  bundle", "bring these markdown files in", or points at a loose .md file or
  folder. For authoring a concept from scratch, use the `new` skill.
argument-hint: "<file-or-folder> [into <bundle path>]"
user-invocable: true
allowed-tools: Bash Read Glob
---

# okfm: add

Bring existing markdown into a bundle without losing the author's content.

1. Collect the source file(s). For a folder, glob `*.md` and consider each.
2. Apply the **capture filter** — import only what is Relevant, Actionable, has Depth, and is Authoritative. Skip raw article dumps, image-only notes, secrets, and uncurated transcripts. Tell the user what you're skipping and why.
3. For each kept file, decide: **dest** path (`<folder>/<slug>.md`), and the frontmatter to fill where missing — **type**, **title**, **description**, **tags**. Read the file to ground these; never overwrite frontmatter the file already has.
4. **Preview:** run with `--dry-run --json` and summarize the import plan (which files, where, what frontmatter gets added):
   `python "${CLAUDE_PLUGIN_ROOT}/scripts" add <src> <dest> --bundle <root> --type "<type>" --title "<title>" --description "<desc>" --tag <t1> --dry-run --json`
5. On the user's OK, run without `--dry-run` (once per file). The engine fills only missing keys and sets `timestamp`/`curated_by: agent` when absent.
6. Run `check` and report. Collisions are refused, not clobbered — rename or pass `--force` only on explicit confirmation.
