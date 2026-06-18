---
name: new
description: >
  Scaffold a new concept in an OKF knowledge bundle from a plain-English
  description — pick the type, title, tags, and placement, then write a
  conformant file and wire it into the index. Use when the user says "add a
  concept", "new OKF note", or "create a knowledge file for". To bootstrap a
  brand-new bundle from scratch, use the `start` skill; for importing existing
  markdown, use the `add` skill.
argument-hint: "<what to capture> [in <bundle path>]"
user-invocable: true
allowed-tools: Bash Read
---

# okfm: new

Turn a plain-English description into a conformant OKF concept. Every write is
previewed first.

1. Decide the concept's fields from what the user said:
   - **type** — a short noun phrase (e.g. `Concept`, `Runbook`, `Provider`, `Product`). Reuse types already present in the bundle when they fit.
   - **title** — a human title; **description** — one sentence; **tags** — a few lowercase keywords.
   - **path** — `<folder>/<slug>.md` under the bundle, grouping with related concepts. Slug is kebab-case of the title.
2. Determine the bundle: the path the user named, else the bundle they're working in. To create a brand-new bundle, add `--init --name "<Bundle Name>"`.
3. **Preview:** run with `--dry-run --json` and show the user, in plain English, exactly what will be created/updated:
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/okf_new.py" <path> --bundle <root> --type "<type>" --title "<title>" --description "<desc>" --tag <t1> --tag <t2> --dry-run --json`
4. On the user's OK, run the same command **without** `--dry-run` to write. The engine sets `timestamp` and `curated_by: agent` automatically.
5. Run `check` (the check skill / `okf_check.py`) and report the result.

Machine-drafted concepts carry `curated_by: agent`. When the user has reviewed and verified one, change it to `curated_by: human`.
