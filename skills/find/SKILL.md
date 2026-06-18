---
name: find
description: >
  Search an OKF knowledge bundle by text, type, tag, or status — returns ranked
  concepts with their paths and the concepts they link to. Use when the user says
  "find notes about X", "search my knowledge base", "what do I have on Y",
  "list all <type> concepts", or "show concepts tagged Z".
argument-hint: "<query> [in <bundle path>]"
user-invocable: true
allowed-tools: Bash Read
---

# okfm: find

Help the user locate knowledge fast.

1. Translate the request into filters: free **text**, and/or `--type`, `--tag`, `--status`. Combine them — filters are ANDed.
2. Run the search (JSON for parsing):
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/okf_find.py" <bundle> --text "<words>" --type "<type>" --tag "<tag>" --status "<status>" --json`
   Omit any flag you don't need. Results are ranked title > description > body.
3. Present the top matches as a short list — `id`, `type`, `title` — and mention each hit's **related** concepts (its links), since those are often what the user actually wants.
4. Offer to open or read a specific hit. `find` is read-only; it never changes the bundle.
