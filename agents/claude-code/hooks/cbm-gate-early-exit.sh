#!/bin/bash
# codebase-memory-mcp search augmenter (Claude Code PreToolUse on Grep|Glob),
# with an early exit for projects without a graph. Install as
# ~/.claude/hooks/cbm-code-discovery-gate (the name the CBM installer uses).
# It never blocks a tool call: any failure is silent (exit 0, no output).
BIN="${CBM_BIN:-$HOME/.local/bin/codebase-memory-mcp}"
[ -x "$BIN" ] || exit 0

# The graph is attached per project by a local .mcp.json. Without one the
# binary still spends about 1.5 s to answer nothing, on every Grep and Glob.
payload=$(cat)
cwd=$(printf '%s' "$payload" | sed -n 's/.*"cwd"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
if [ -n "$cwd" ] && ! grep -qs codebase-memory "$cwd/.mcp.json"; then
  exit 0
fi

printf '%s' "$payload" | "$BIN" hook-augment 2>/dev/null
exit 0
