---
name: okf
description: >
  Conventions for working inside an OKF knowledge bundle (a directory of
  markdown files with YAML frontmatter, plus reserved index.md/log.md). Use
  whenever reading, editing, or creating files in or near an OKF bundle — to
  preserve source formatting, keep links OKF-conformant, maintain the log, and
  apply trust tiers. Auto-applies when an okf.json or a bundle index.md is present.
user-invocable: false
allowed-tools: Bash Read Edit
---

# okfm: conventions

How to behave inside an OKF bundle so it stays healthy.

## Engine invocation
These skills call the okfm engine through one CLI, written here as `okf <command>`. Resolve it for the current harness:
- **Claude Code:** `python "${CLAUDE_PLUGIN_ROOT}/scripts" <command> <args>` (the form used in the command skills).
- **Any other harness / plain shell:** `okf <command>` (the CLI on PATH) or `python okf.pyz <command>` or `python /path/to/scripts <command>`.

The `<command> <args>` part is identical everywhere; subcommands are `new`, `add`, `convert`, `seed`, `move`, `check`, `map`, `find`, `scan`. Porting a skill to another harness is just swapping that prefix.

## Workflow
- **Read before work:** start from the relevant concept, follow links for context, treat notes as orientation, then verify against the live repo/state.
- **Write back:** when a durable decision changes, update the concept and add a `log.md` entry.

## Source-preserving edits
- Never re-render a whole file. Change only the bytes that change. Keep manually aligned tables, ASCII diagrams, and whitespace pristine.
- Frontmatter edits preserve key order, indentation, inline comments, and unknown custom keys. Use `okf_fmwrite` (via the `new`/`add`/`move` commands) rather than hand-rewriting blocks.

## Links
- Standard markdown links only — `[text](/path.md)` (absolute from bundle root) or relative. Avoid wikilinks: standard links stay OKF-conformant and parseable by `check`, and Obsidian reads them fine (a folder of markdown is already a valid Obsidian vault).
- Prefer **absolute** links (the default `link_style`); they survive `move` unchanged.
- A broken link means "knowledge not yet written" — surface it, never delete it.

## Reserved files
- `index.md` is engine-owned: regenerate it with `check --fix` rather than hand-editing (your frontmatter `title`/`description` are the source of truth for each bullet).
- `log.md` is newest-first, ISO `## YYYY-MM-DD` headings, bullets prefixed with a bold action (`* **Update**: ...`). Add an entry on any automated change.

## Fields
- `type` is the only required key. Recommended: `title`, `description`, `resource`, `tags`, `timestamp`.
- `resource` is a URI uniquely identifying the underlying asset (a table, an endpoint, a document). It is the stable identity key for catalog-style concepts; omit it for abstract concepts.

## Body sections (conventional)
- `# Schema` — structured field/column descriptions. `# Examples` — usage in code blocks. `# Citations` — numbered sources (absolute URLs, bundle-relative paths, or concepts under `references/`).
- `convert` writes a `# Citations` block automatically (the source file, or explicit `--citation` URLs). Agent-curated concepts with no citations are flagged `no-citations` by `check` — a nudge, not an error.
- `references/` holds external-source concepts (`type: Reference`) that other concepts cite.

## Trust tiers
- Machine-drafted concepts carry `curated_by: agent`. When a human reviews and verifies one, change it to `curated_by: human` so AI drafts never blend invisibly into verified knowledge.

## Capture filter
- Capture only what is **Relevant, Actionable, has Depth, and is Authoritative**. Skip raw dumps, image-only notes, secrets, uncurated transcripts.

## Forward-compatible keys (documented now; no view renders them yet)
- `status` (Backlog/Todo/In Progress/In Review/Done), `priority`, `assignee`, `epic`, and a `# Dependencies` section with `Blocks` / `Blocked by` bullets. Capturing these now means v3 views "just work" later.
