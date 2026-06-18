# okfm — OKF Manager

A Claude Code plugin for building and maintaining an [Open Knowledge Format (OKF)](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) knowledge base — a plain directory of markdown files with YAML frontmatter that a human can read, git can track, and any AI agent can consume without an SDK or server.

okfm gives you a set of commands to create that directory, keep its links and frontmatter consistent, generate concepts from existing sources, and read the whole thing back as a browsable HTML file. The engine is dependency-free stdlib Python 3, and every command previews its changes before writing.

## What an OKF bundle is

A bundle is a folder of `.md` files. Each file (a "concept") has a YAML frontmatter block with at least a `type`, and a markdown body. Files link to each other with ordinary markdown links. Two filenames are reserved: `index.md` (a generated table of contents, one per directory) and `log.md` (a change log). That's the whole format — there's no database and no proprietary store. okfm is a manager for that folder, not a new storage system.

This plugin implements the OKF v0.1 spec. It is not affiliated with the upstream OKF project; it targets that spec and links to it above.

## Who it's for

- Developers consolidating a repository's scattered knowledge into one agent-readable place.
- Anyone building a markdown "second brain" who wants structure and link-checking without adopting a heavier tool.

If you already keep notes as markdown (including in Obsidian — a folder of markdown is a valid vault), okfm works on that folder in place.

## Install

In Claude Code:

```
/plugin marketplace add RadOrigin-LLC/okf-manager
/plugin install okfm@okf-manager
```

## Requirements

- **Python 3 on your PATH** — nothing else to install: no `pip` packages, no server, no API keys. (The `enrich` command is the exception: it uses Claude's own web-fetch capability; see its note below.)

## Commands

Every command that writes shows you a preview first and asks before changing anything.

### Get started
- **`/okfm:start`** — guided onboarding: a short interview, an explanation of the capture filter (what's worth keeping), scaffolds a new bundle, and walks you through your first concepts.
- **`/okfm:new`** — create one concept with valid frontmatter. `--init` bootstraps a fresh bundle (`index.md`, `log.md`, `okf.json`).

### Bring existing material in
- **`/okfm:add`** — import an existing markdown file: fill in only the missing frontmatter, place it, and wire it into the index. Your existing frontmatter and body are left as-is.
- **`/okfm:convert`** — turn a single non-markdown file into a concept. Native formats: `.txt`, `.html`, `.htm`, `.csv`, `.json`. For PDF/docx, the agent extracts the text and writes it via `new` (the engine itself doesn't parse binaries). A `# Citations` section records the source.
- **`/okfm:scan`** — walk a repo or notes folder and propose what's worth importing and where, applying the capture filter. Proposes only; you confirm before anything is written.

### Generate concepts in bulk
- **`/okfm:seed`** — create many concepts at once from a structured source. Three modes (auto-detected, or pass `--mode`):
  - **sqlite** — one `Table` concept per table, with a `# Schema` column listing.
  - **openapi** — one `API Endpoint` per path+method (OpenAPI), or one `Schema` per definition (JSON Schema).
  - **tree** — one `File` concept per file in a directory, preserving the directory structure; small text files embed their contents.

  Seeding is offline and preview-gated. Generated concepts are marked `curated_by: agent` and cite the source they came from.
- **`/okfm:enrich`** — grow a bundle from web pages you point it at. You provide seed URLs and a domain allowlist; for each page the agent decides whether to add a reference (under `references/`, with a citation) or skip it. See the honest note in [Limitations](#limitations) about how its guardrails are enforced.

### Maintain
- **`/okfm:check`** — validate the bundle (details below). `--fix` regenerates the index and normalizes frontmatter ordering, always behind a preview. It never deletes files and never rewrites your broken links for you.
- **`/okfm:move`** — rename or relocate a concept and rewrite every inbound link across the bundle so nothing dangles.

### Read it back
- **`/okfm:find`** — search by `--text`, `--type`, `--tag`, or `--status`, ranked, returning matches plus their linked concepts. This is keyword/field matching, not semantic (embedding) search.
- **`/okfm:map`** — write a single self-contained HTML file (no dependencies, opens in any browser) that acts as an offline browser for the bundle: a search box, a directory-grouped concept list, a reader panel showing each concept's frontmatter/body/links/backlinks, a "needs attention" lens that surfaces the same findings `check` reports, and an optional graph view.

There is also an always-on `okf` conventions skill (not a command) that keeps the agent's edits inside a bundle source-preserving and link-safe.

## What `check` validates

`check` reports findings at three levels:

- **Errors** — a file with no parseable frontmatter, or frontmatter missing a non-empty `type`.
- **Warnings** — a markdown link pointing at a concept that doesn't exist (broken link), or a `log.md` whose dated entries aren't newest-first.
- **Notes (advisory)** — a concept listed in no index (index drift), a concept with no inbound links (orphan), a stale timestamp (older than the configured `stale_days`, default 180), a root index missing its `okf_version`, and an agent-curated concept with no `# Citations` section.

A broken link is treated as "knowledge not yet written," so it's surfaced, never auto-deleted.

## How it treats your files

- **Dependency-free.** A stdlib Python 3 engine (23 small modules under `scripts/`). No `pip`, no server, no SDK.
- **Never destructive.** Every write is previewed first. Hand-authored text, comments, frontmatter key order, and unknown frontmatter keys are preserved; the engine edits only the bytes that change.
- **The engine owns two things.** The nested `index.md` tree and `log.md` are regenerated/appended by the engine; everything else is yours.
- **Trust tiers.** Machine-drafted concepts carry `curated_by: agent`. When you review one, you flip it to `curated_by: human`, so AI drafts never silently blend into verified knowledge.
- **Sync-agnostic.** okfm manages the folder; you sync it however you like (git, a cloud-synced folder, Obsidian, Syncthing). It does no syncing of its own.

## Limitations

Things it deliberately does **not** do, so there are no surprises:

- **Standard markdown links only.** `check` reads `[text](path.md)` links (absolute-from-root or relative), which is what OKF requires. Obsidian `[[wikilink]]` syntax is not parsed. If you author in Obsidian, set it to use Markdown links so `check` can see them.
- **`enrich`'s limits are agent-followed, not code-enforced.** The required allowlist, the 50-page cap, and the one-citation-per-page rule are instructions the `enrich` skill follows while it fetches. The Python engine never makes network requests, so these are guardrails on the agent's behavior, not hard limits checked in code.
- **HTML-to-markdown conversion is best-effort.** `convert` handles headings, paragraphs, lists, links, and tables with the standard library; complex pages won't round-trip perfectly.
- **No binary parsing.** PDF/docx aren't read by the engine; the agent extracts text first.
- **`find` is keyword/field search**, not semantic search — there are no embeddings or vector index.
- **`--fix` is conservative.** It regenerates indexes and normalizes frontmatter ordering. It does not retarget broken links or delete anything — those stay manual.
- **Claude Code only.** A Codex port is planned but not in this repo yet.

## Development

The engine has no third-party dependencies, and the tests use the standard-library `unittest` runner (no pytest):

```bash
# from the repo root
for t in tests/test_*.py; do python "$t" || break; done
```

At the time of writing this is 138 tests across the `tests/` directory.

## License

Apache-2.0. See [LICENSE](LICENSE).
