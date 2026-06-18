---
name: start
description: >
  Guided onboarding for a new OKF knowledge bundle — a short interview, then
  scaffold a starter structure and walk the user through their first concepts.
  Use when the user says "start a knowledge base", "set up an OKF bundle",
  "onboard me to OKF", "I want a second brain", or has no bundle yet.
argument-hint: "[where to create the bundle]"
user-invocable: true
allowed-tools: Bash Read AskUserQuestion
---

# okfm: start

Stand up a healthy bundle and make the first capture feel easy.

1. **Short interview** (ask, don't assume):
   - What are you organizing — a developer repo's knowledge, or a personal "second brain"?
   - One central bundle, or per-project bundles?
   - Where should it live (path)?
2. **Teach the capture filter** in one line: capture things that are **Relevant, Actionable, have Depth, and are Authoritative**. Don't capture raw article dumps, image-only notes, secrets, or uncurated transcripts.
3. **Scaffold** the bundle by creating its first concept with `--init`, which also creates `index.md`, `log.md`, and `okf.json`:
   `python "${CLAUDE_PLUGIN_ROOT}/scripts" new <folder>/<first-slug>.md --bundle <root> --init --name "<Bundle Name>" --type "<type>" --title "<title>" --description "<desc>" --dry-run --json`
   Show the plan, then run it for real on the user's OK.
4. Propose a starter folder shape that fits their answer (e.g. `concepts/`, `projects/`, `providers/`, `runbooks/` for a dev bundle; or PARA-style `projects/`, `areas/`, `resources/` with a `00-inbox/` for a personal brain). Create folders by placing concepts in them via `new`.
5. Walk them through creating 1–2 real concepts with the `new` skill, then run `check` and `map` so they see the payoff immediately.

Keep it light. The goal is a living bundle the user wants to come back to.
