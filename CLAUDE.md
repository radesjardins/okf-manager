# okfm — OKF Manager

## What this is
A single Claude Code plugin (`okfm`) that builds and maintains an Open Knowledge Format (OKF) knowledge base. The repo is both the plugin (root `.claude-plugin/plugin.json`) and a marketplace of one (`.claude-plugin/marketplace.json`, `source: "."`). Commands are `/okfm:<skill>`.

## Tech stack
- Dependency-free stdlib **Python 3** engine in `scripts/` — no pip, no SDK, and **no network**. `enrich`'s web access lives in the skill layer (Claude's WebFetch), never in the engine.
- Skills (markdown) in `skills/<name>/SKILL.md`.
- Tests in `tests/` using stdlib `unittest` (no pytest). Run all:
  `for t in tests/test_*.py; do python "$t" || break; done`

## Conventions
- Every write previews first and is never destructive. The engine owns the nested `index.md` tree and `log.md`.
- Match existing module idioms; keep the engine offline and dependency-free.
- License: Apache-2.0.

## Origin
Extracted from `rad-claude-skills` (formerly the `rad-okf` plugin) on 2026-06-18; renamed `rad-okf` → `okfm`.
