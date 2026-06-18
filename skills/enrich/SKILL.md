---
name: enrich
description: >
  Enrich an OKF bundle from the web — fetch a bounded set of seed URLs, and for
  each page decide whether to augment an existing concept, add a new reference
  under references/, or skip. Use when the user says "enrich my bundle from
  these URLs", "pull in docs from <site>", "add web references", or "research and
  add sources for <concept>". Requires a domain allowlist and never crawls
  openly. For seeding from a local structured source (database, OpenAPI, repo),
  use the `seed` skill.
argument-hint: "<seed urls> [for <bundle path>]"
user-invocable: true
allowed-tools: WebFetch Bash Read Edit
---

# okfm: enrich

Grow a bundle from web sources under hard guardrails. The Python engine never
touches the network — **you** fetch here and write through `new`/`convert`, so
all provenance and limits live in this skill.

## Guardrails (do not skip)
- **Domain allowlist is required.** Ask for it if the user didn't give one. Fetch only URLs whose host is on the list; never follow links off-allowlist.
- **Hard page cap: 50.** Stop fetching at 50 pages even if more are queued, and report what was skipped.
- **Every page yields a citation.** Any concept you write or augment records its source URL in a `# Citations` section.
- **Agent trust tier.** New concepts are `curated_by: agent`; the user verifies before flipping to `human`.
- **Capture filter.** Skip pages that are thin, secret-bearing, or off-topic — keep only what is Relevant, Actionable, has Depth, and is Authoritative.

## Workflow
1. Collect the seed URLs, the domain allowlist, and the target bundle. Confirm the allowlist and the 50-page cap with the user before fetching.
2. Read the bundle's index tree and relevant concepts so you augment rather than duplicate.
3. For each allowed URL, up to 50:
   - Fetch it (WebFetch).
   - Apply the capture filter; skip if it fails.
   - Decide:
     - **augment** an existing concept — Edit its body to add the new material, add the source under its `# Citations` section, and add a `log.md` note; or
     - **add a reference** — a new concept under `references/` via `new` (or `convert` if you saved the page) with `--type Reference --citation <url>`.
4. Run `check` and report: pages fetched, concepts added/augmented, pages skipped (with reasons), and anything left over the cap.

Writing a reference (preview first, then again without `--dry-run` on the user's OK):
`python "${CLAUDE_PLUGIN_ROOT}/scripts" new references/<slug>.md --bundle <root> --type Reference --title "<title>" --citation "<url>" --body "<extracted summary>" --dry-run --json`
