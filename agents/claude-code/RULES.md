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
- Do not read a whole file with Read or cat to answer a structural question about code: use
  `get_code_snippet` or `search_graph`.

## Ponytail

- The `ponytail@ponytail` plugin injects its rules into the session and every subagent;
  `/ponytail-review` checks the current diff, `/ponytail-audit` the repository. `mode doc` turns it off.
- Ponytail does not replace questions: ambiguous requirements are still resolved by asking, not by a
  simpler default. Tasks without code (documents, prose) are outside its scope.
- GSD projects (`.planning/`): the planner applies the ladder when forming plan tasks; a task that
  duplicates existing code, the standard library or an installed dependency is a plan defect. An
  approved `PLAN.md` is explicitly requested work: the executor implements every task with minimal
  code, does not shrink the plan and records redundancy in SUMMARY as a deviation. Tests required by
  the plan, `tdd_mode` or `nyquist_validation` are explicitly requested. Code review of a phase adds
  `/ponytail-review` of its diff.
