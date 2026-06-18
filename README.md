# okfm — OKF Manager

A Claude Code plugin to build and maintain an [Open Knowledge Format (OKF)](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) knowledge base — for developers consolidating a repo's knowledge and for non-technical knowledge workers building an AI-readable "second brain."

An OKF bundle is just a directory of markdown files with YAML frontmatter: human-readable, git-friendly, and consumable by any AI agent without an SDK or server. This plugin keeps one **healthy** — easy to build, hard to let rot.

## Status

In active development.
- **Available now:** `start` (guided onboarding), `new` (create concept/bundle), `add` (import existing markdown), `convert` (non-markdown → concept), `seed` (generate concepts from a database/OpenAPI/repo), `enrich` (bounded web sourcing), `move` (link-safe rename/relocate), `check` (validate, with `--fix`), `map` (visualize), `find` (search), and `scan` (triage a folder for import), plus an always-on `okf` conventions skill.

## Commands

- **`/okfm:start`** — guided onboarding: short interview, teaches the capture filter, scaffolds the bundle, and walks through the first concepts.
- **`/okfm:new`** — create a new concept file with validated frontmatter; supports `--init` to bootstrap a fresh bundle.
- **`/okfm:add`** — import an existing markdown file into the bundle: fill in missing frontmatter, place it, and wire it into the index.
- **`/okfm:convert`** — convert a non-markdown file (`.txt`/`.html`/`.htm`/`.csv`/`.json`, or an agent-extracted PDF/docx) into a conformant concept and wire it into the index.
- **`/okfm:seed`** — generate many concepts at once from a structured source: a SQLite database (one concept per table), an OpenAPI/JSON-Schema file (per endpoint/definition), or a directory tree (per file). Offline, preview-gated.
- **`/okfm:enrich`** — grow a bundle from the web under hard guardrails (required domain allowlist, 50-page cap, a citation per page). Fetching happens in the skill; the engine stays offline.
- **`/okfm:move`** — rename or relocate a concept and rewrite all inbound links bundle-wide so nothing breaks.
- **`/okfm:check`** — validate a bundle: frontmatter + required `type`, broken cross-links, orphaned concepts, and staleness. Supports `--fix` (preview-gated index/frontmatter repair).
- **`/okfm:map`** — generate a self-contained HTML browser for the bundle (no dependencies, opens in a browser): search, a directory-grouped concept list, a reader panel with links and backlinks, a "needs attention" lens mirroring `check`, and an optional graph view.
- **`/okfm:find`** — search the bundle by text, type, tag, or status; returns ranked concepts and their linked (related) concepts.
- **`/okfm:scan`** — walk a repo or notes folder, apply the capture filter, and propose what's worth importing and where — confirmation-gated.

> **Link syntax:** okfm checks standard markdown links (`[text](path.md)`), which is what OKF requires. Obsidian `[[wikilink]]` syntax isn't parsed yet — if you author in Obsidian, enable its **"Use [[Wikilinks]]" → off / Markdown links** setting so links stay OKF-conformant and `check` can see them.

## Design principles

- **Dependency-free:** stdlib Python 3 engine. No `pip`, no server, no SDK.
- **Never destructive:** every write is previewed before it happens; your hand-authored text, comments, and formatting are preserved.
- **Sync-agnostic:** the plugin manages the knowledge; you sync the folder however you like (git, a cloud-synced folder, Obsidian, Syncthing).

## Requirements

- Python 3 on PATH.

## License

Apache-2.0
