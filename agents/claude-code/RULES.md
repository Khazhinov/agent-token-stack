## Context economy stack

- Start code exploration with codebase-memory-mcp: `index_status`, then `search_graph`,
  `get_architecture`, `trace_path`, `get_code_snippet`. Grep, Glob and Read come after the graph gave
  no answer, or for files without code. If a project has code but no `mcp__codebase-memory-mcp__*`
  tools, the graph is not attached: create `.mcp.json` in the project root and ask for a session
  restart.
- When a tool returns more than about 500 lines, process it in the context-mode sandbox
  (`ctx_execute`, `ctx_batch_execute`) and keep only the result. Do not hold raw logs, test output or
  large JSON in context.
- The RTK hook rewrites suitable Bash commands; do not bypass it.
- Answer style follows Caveman while it is on; documents are written in full prose.
- Switch the stack only with the `stack` skill (`/stack`, `/stack mode doc|dev`,
  `/stack on|off <tool>`, `/stack normalize` after any third-party installer), never by editing
  settings by hand.
- Shared binaries (RTK, CBM) and the CBM index cache belong to every agent on the machine: update
  them from one agent at a time, never delete the cache.
