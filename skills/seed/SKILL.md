---
name: seed
description: >
  Seed an OKF bundle from a structured source — a SQLite database, an OpenAPI or
  JSON-Schema file, or a directory tree — minting one conformant concept per
  table, endpoint/definition, or file. Use when the user says "seed from",
  "import my database schema", "catalog this repo", "build concepts from this
  OpenAPI spec", or "generate a knowledge base from <source>". For importing one
  markdown file use `add`; for one non-markdown file use `convert`.
argument-hint: "<source> [into <bundle path>]"
user-invocable: true
allowed-tools: Bash Read
---

# okfm: seed

Generate many concepts at once from a structured source. The engine is offline
and dependency-free; every write previews first; generated concepts are
`curated_by: agent` until a human verifies them.

1. Identify the source and the bundle. The engine auto-detects the mode
   (`sqlite` / `openapi` / `tree`); pass `--mode` to override, and `--dest-dir`
   to choose the subdirectory (defaults to a slug of the source name).
2. **Preview:**
   `python "${CLAUDE_PLUGIN_ROOT}/scripts" seed <source> --bundle <root> --dest-dir <subdir> --dry-run --json`
   Show the user the list of concepts that would be created and where.
3. On their OK, run the same command **without** `--dry-run`. Existing files are
   skipped unless `--force`. The engine sets `timestamp` and `curated_by: agent`,
   regenerates the index tree, and appends a `log.md` entry.
4. Run `check` and report. Remind the user the new concepts are agent-drafted —
   they should review and flip verified ones to `curated_by: human`.

## Modes
- **sqlite** — one `Table` concept per table, with a `# Schema` column listing and a `sqlite://<db>#<table>` resource.
- **openapi** — one `API Endpoint` per path+method (OpenAPI), or one `Schema` per definition (JSON Schema), or one `Schema` for a bare schema document.
- **tree** — one `File` concept per file, directory structure preserved; small text files embed their content; binaries and dot-directories (`.git`, `node_modules`, …) are skipped.

For ongoing growth from the web, use the `enrich` skill.
