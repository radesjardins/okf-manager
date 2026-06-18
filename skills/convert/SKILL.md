---
name: convert
description: >
  Convert a non-markdown file into an OKF concept — turn a .txt/.html/.csv/.json
  file (or, via your own extraction, a PDF/docx) into one conformant markdown
  concept and wire it into the bundle. Use when the user says "convert this file",
  "turn this CSV/JSON/HTML into a note", "import this PDF into my knowledge base",
  or points at a non-markdown source. For loose markdown, use the `add` skill.
argument-hint: "<source-file> [into <bundle path>]"
user-invocable: true
allowed-tools: Bash Read
---

# okfm: convert

Bring a non-markdown source into the bundle as one concept.

1. Identify the source format:
   - **`.txt` / `.html` / `.csv` / `.json`** — handled natively by the engine.
   - **`.md`** — already a concept; use the `add` skill instead.
   - **PDF / docx / other binary** — read it yourself (your own file reading), then create the concept with `new --body "<extracted text>"`. The engine stays dependency-free.
2. Apply the **capture filter** — only convert what is Relevant, Actionable, has Depth, and is Authoritative.
3. Decide the **dest** path (`<folder>/<slug>.md`) and the frontmatter: **type**, **title**, **description**, **tags**. Read the source to ground these.
4. **One file → one concept.** If a source is too large or covers several distinct concepts, split it: run `convert` (or `new --body`) once per concept rather than producing one giant note.
5. **Preview:** run with `--dry-run --json` and summarize the plan (source, format, dest, what gets indexed):
   `python "${CLAUDE_PLUGIN_ROOT}/scripts" convert <src> <dest> --bundle <root> --type "<type>" --title "<title>" --description "<desc>" --dry-run --json`
6. On the user's OK, run without `--dry-run`. The engine converts the body (CSV → table, JSON → fenced block, HTML → headings/lists/links, TXT → text), writes the concept, regenerates the index, and logs a `Convert` entry.
7. Run `check` and report. Collisions are refused, not clobbered — rename or pass `--force` only on explicit confirmation.

> HTML/PDF conversion is best-effort; skim the result and tidy it with the `okf` conventions (source-preserving edits) if needed.
