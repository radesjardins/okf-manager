---
name: check
description: >
  Validate an OKF knowledge bundle — conformance (frontmatter + required type),
  broken cross-links, orphaned concepts, and staleness. Use when the user says
  "check my OKF bundle", "validate my knowledge base", "what's broken in my
  notes", or after importing or editing concepts.
argument-hint: "<path-to-bundle>"
user-invocable: true
allowed-tools: Bash Read
---

# okfm: check

Run the validator and report results in plain language.

1. Determine the bundle path: use the argument if given, otherwise the bundle the user is working in. If neither is clear, the CLI defaults to the current directory (`.`) and walks up to the bundle root.
2. Run: `python "${CLAUDE_PLUGIN_ROOT}/scripts/okf_check.py" <path> --json`
3. Parse the JSON. Summarize findings grouped by severity (errors first), each as: `<code> (<id>) — <message>`. The `code` (e.g. `broken-link`, `missing-type`, `orphan`, `stale`) is the rule that fired and is the most useful part for the user; `id` is the concept it applies to.
4. End with the totals line and, if there are errors, a one-line "what to fix first" suggestion.

To repair safely, run `--fix` behind a preview: first
`python "${CLAUDE_PLUGIN_ROOT}/scripts/okf_check.py" <path> --fix --dry-run --json`
and show the user which files would change (index regeneration + frontmatter
ordering). On their OK, run the same command without `--dry-run`. `--fix` never
deletes files and never retargets broken links — those remain manual.
