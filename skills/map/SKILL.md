---
name: map
description: >
  Generate a self-contained HTML graph of an OKF knowledge bundle (no
  dependencies, opens in a browser). Use when the user says "visualize my
  knowledge base", "show me the map", "map my OKF bundle", or wants to see
  how concepts connect.
argument-hint: "<path-to-bundle>"
user-invocable: true
allowed-tools: Bash Read
---

# okfm: map

1. Determine the bundle path: use the argument if given, otherwise the bundle the user is working in (the CLI defaults to the current directory `.`).
2. Run: `python "${CLAUDE_PLUGIN_ROOT}/scripts" map <path> --name "<bundle name>"`
3. Report the output file path and tell the user they can open it by double-clicking. Offer to open it if they want (`Start-Process <file>` on Windows; `open <file>` on macOS; `xdg-open <file>` on Linux).

This only writes `viz.html` (an output artifact); it never modifies knowledge files.
