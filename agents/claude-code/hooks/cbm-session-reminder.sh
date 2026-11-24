#!/bin/bash
# Install as ~/.claude/hooks/cbm-session-reminder for the SessionStart event.
exec python3 -c '
import json
import sys
from pathlib import Path

try:
    payload = json.load(sys.stdin)
    cwd = payload.get("cwd") or Path.cwd()
    with (Path(cwd) / ".mcp.json").open(encoding="utf-8") as config:
        servers = json.load(config).get("mcpServers")
except (AttributeError, OSError, TypeError, ValueError):
    sys.exit(0)

if isinstance(servers, dict) and isinstance(servers.get("codebase-memory-mcp"), dict):
    print("codebase-memory-mcp is configured: start code exploration with index_status, then "
          "search_graph, get_architecture, trace_path, get_code_snippet; run index_repository "
          "if there is no index.")
'
