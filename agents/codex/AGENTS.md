# Global Codex rules

These rules apply to every Codex model. Their source is `agents/codex` of the agent-token-stack repository; the `token-stack` skill manages the global installation. Change the shared configuration in the repository first, then run `python3 ~/.agents/skills/token-stack/scripts/manage.py install`.

## Token optimization stack

This machine runs a token optimization stack across its agents. It changes command output, the tool set and reply style. The source of truth is this repository's `AGENTS.md`; machine state is in `local/`. The absolute repository path is in the appended local rules.

If a stack component gets in the way of a task, or one could help, tell the person and name the switch command: `python3 ~/.agents/skills/token-stack/scripts/manage.py on|off rtk|cbm|native|te|all`. Do not switch, install or update stack components without an explicit command from the person.

Write compactly and start with the result. Do not shorten code, commands, paths, diagnostics and document content where precision matters more than length.

When exploring a codebase, start with `codebase-memory` (`index_status`, then `search_graph`, `get_architecture` or `trace_path`) if the MCP server is available and the project is indexed. Confirm exact details with `rg` and minimal file ranges. Without MCP use `codebase-memory-mcp cli <tool> '<json>'`; a missing index must not stop the task.

Prefer RTK for noisy commands (`rtk git`, `rtk test`, `rtk pytest`, `rtk read`, `rtk grep`, `rtk log`, `rtk json`). Do not use RTK where the full verbatim output is needed. The global hook usually rewrites suitable Bash commands automatically.

Do not load large references up front. Keep `AGENTS.md` files short, put narrow rules into the nearest nested `AGENTS.md` and repeatable conditional processes into skills. Near the context limit use native compaction; before `/compact` record open decisions, verified facts and changed files.

## Minimal implementation (Ponytail full)

After understanding the task and the whole execution path, stop at the first rung that holds: do not create what is not needed (YAGNI); reuse what the project already has; use the standard library; use a native platform feature; use an already installed dependency; only then write the minimum of new code.

Do not add abstractions with one implementation, scaffolding "for later", extra dependencies or boilerplate. Prefer deletion to addition, simple code to clever code and the fewest files. Fix the root cause at the shared point of the flow, not the symptom at one caller.

Minimalism does not cancel understanding the task, input validation at trust boundaries, protection from data loss, security, accessibility and explicitly requested requirements. Non-trivial logic gets one minimal runnable check; trivial changes need no test infrastructure.
