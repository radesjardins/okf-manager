---
name: move
description: >
  Rename or relocate a concept in an OKF bundle without breaking links — finds
  every backlink and surgically rewrites it to the new location, then updates
  the index. Use when the user says "rename this concept", "move this note to",
  "reorganize my bundle", or "relocate this file". Link-safe and non-destructive.
argument-hint: "<old path> <new path>"
user-invocable: true
allowed-tools: Bash Read
---

# okfm: move

Relocate a concept and keep every cross-link intact.

1. Identify the source path and the destination path (both inside the bundle).
2. **Preview:** run with `--dry-run --json` and show the user the move plus every backlink that will be rewritten and in how many files:
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/okf_move.py" <old> <new> --bundle <root> --dry-run --json`
3. On the user's OK, run without `--dry-run`. The engine moves the file, rewrites inbound backlink destinations (in the bundle's `link_style`, default absolute), regenerates the index, and logs the move.
4. Run `check` and report — confirm no new broken links appeared.

Note: `move` rewrites links *pointing at* the moved file. If the moved file itself uses **relative** links to others, verify those after the move (the recommended convention is absolute links, which are unaffected). Also, image links (`![alt](...)`) and link targets containing parentheses are not matched by the link parser, so verify those manually if your bundle uses them.
