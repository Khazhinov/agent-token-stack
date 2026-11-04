# Global Codex rules

These rules apply to every Codex model. Their source is `agents/codex` of the agent-token-stack repository; the `token-stack` skill manages the global installation. Change the shared configuration in the repository first, then run `python3 ~/.agents/skills/token-stack/scripts/manage.py install`.

Write compactly and start with the result. Do not shorten code, commands, paths, diagnostics and document content where precision matters more than length.

When exploring a codebase, start with `codebase-memory` (`index_status`, then `search_graph`, `get_architecture` or `trace_path`) if the MCP server is available and the project is indexed. Confirm exact details with `rg` and minimal file ranges. Without MCP use `codebase-memory-mcp cli <tool> '<json>'`; a missing index must not stop the task.

Work with files outside the current project only when the user explicitly asks and names the folder or file. This applies to reading and to changes; do not treat neighbouring folders as allowed by default. If the target is unclear, ask before touching external files.

Prefer RTK for noisy commands (`rtk git`, `rtk test`, `rtk pytest`, `rtk read`, `rtk grep`, `rtk log`, `rtk json`). Do not use RTK where the full verbatim output is needed. The global hook usually rewrites suitable Bash commands automatically.

Do not load large references up front. Keep `AGENTS.md` files short, put narrow rules into the nearest nested `AGENTS.md` and repeatable conditional processes into skills. Near the context limit use native compaction; before `/compact` record open decisions, verified facts and changed files.

## Minimal implementation (Ponytail full)

After understanding the task and the whole execution path, stop at the first rung that holds: do not create what is not needed (YAGNI); reuse what the project already has; use the standard library; use a native platform feature; use an already installed dependency; only then write the minimum of new code.

Do not add abstractions with one implementation, scaffolding "for later", extra dependencies or boilerplate. Prefer deletion to addition, simple code to clever code and the fewest files. Fix the root cause at the shared point of the flow, not the symptom at one caller.

Minimalism does not cancel understanding the task, input validation at trust boundaries, protection from data loss, security, accessibility and explicitly requested requirements. Non-trivial logic gets one minimal runnable check; trivial changes need no test infrastructure.
