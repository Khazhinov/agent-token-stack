#!/bin/bash
# codebase-memory-mcp reminder (Claude Code SessionStart). Install as
# ~/.claude/hooks/cbm-session-reminder (the name toggle.py and the CBM installer use).
# Prints one line into the session only in projects whose .mcp.json attaches CBM;
# elsewhere it prints nothing, so sessions without code get no extra context.
payload=$(cat)
cwd=$(printf '%s' "$payload" | sed -n 's/.*"cwd"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -n "$cwd" ] || cwd=$PWD
grep -qs codebase-memory "$cwd/.mcp.json" || exit 0
echo "codebase-memory-mcp is attached: start code exploration with index_status, then search_graph, get_architecture, trace_path, get_code_snippet; run index_repository if there is no index."
exit 0
