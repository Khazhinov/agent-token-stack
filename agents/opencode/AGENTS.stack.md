# OpenCode stack rules

These rules are supplied as ambient instructions through the `instructions` array of
`~/.config/opencode/opencode.json`. They are the stack part of the global rules; personal and
non-stack rules stay in the machine's own `AGENTS.md`.

## Code exploration

Start with `codebase-memory` (MCP `codebase-memory-mcp`): `index_status`, then `search_graph`,
`get_architecture`, `trace_path` or `get_code_snippet`. Confirm exact details with `rg` and minimal
file ranges. When MCP is unavailable, use `codebase-memory-mcp cli <tool> '<json>'`. A missing index
does not stop the task.

Attach the graph per project: the MCP `codebase-memory-mcp` is set in `opencode.json` at the root of
a project with code, not in the global configuration. Use the shared binary and the shared index
cache `~/.cache/codebase-memory-mcp`. When the current project has no MCP attachment, use the CLI.
Read the shared-node document before installing, updating or clearing the cache.

## RTK

Prefer RTK for noisy commands: `rtk git`, `rtk test`, `rtk read`, `rtk grep`, `rtk log`, `rtk json`.
Do not use RTK where the full verbatim output is needed. The `plugins/rtk.ts` plugin rewrites
suitable Bash commands through `rtk rewrite`.

## context-mode

When context-mode is loaded, run large outputs, network requests and data analysis through the
`ctx_*` tools: `ctx_batch_execute`, `ctx_execute`, `ctx_execute_file`, `ctx_fetch_and_index`,
`ctx_search`. Do not keep raw logs, JSON and test output in context. The `context-mode` plugin
registers the `ctx_*` tools; no separate MCP is attached.

## Caveman and Ponytail

Both modes are plugins (`plugins/caveman`, `plugins/ponytail`) and inject their rules automatically.
Do not duplicate those rules in `AGENTS.md`. The default level is `full`; switch with
`/caveman off|lite|full|ultra` and `/ponytail off|lite|full|ultra`. The documents mode is described in
the OpenCode README of the agent-token-stack repository.

## Shared components

RTK and codebase-memory-mcp are shared with other agents on the machine, together with the index
cache `~/.cache/codebase-memory-mcp`. Do not create second copies and do not run parallel updates or
indexing. The coordinated update order is described in the OpenCode shared-node document.

Near the context limit, use native OpenCode compaction. Before compaction record open decisions,
verified facts and changed files.
