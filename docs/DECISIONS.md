# Decisions

English | [Русский](DECISIONS.ru.md)

| # | Decision | Rationale | Rejected alternative |
|---|---|---|---|
| S1 | One copy of each shared binary (RTK, CBM) per machine, one index cache, one updater at a time; the CBM and RTK pins with SHA-256 live in one place (`BINARY_SPECS` of `manage.py`) | two copies drift apart; parallel updates and indexing corrupt the shared cache | each agent installs its own copy |
| S2 | CBM is attached per project in Claude Code and OpenCode; in Codex it is one global server with an allow-list of eight tools | a global registration loads about 14 tool schemas into every Claude session, including folders without code; Codex `enabled_tools` keeps the schema small | global registration everywhere |
| S3 | `codebase-memory-mcp install` and `update` are never used for updates; `normalize` (Claude) and `manage.py install` (Codex) run after any third-party installer | the installer finds every agent and adds hooks, global MCP entries and an `AGENTS.md` block to all of them | trust the vendor installer |
| S4 | Codex uses native `tool_output_token_limit`, `project_doc_max_bytes` and compaction instead of context-mode | native mechanisms cover the role without a second filter on the same output | context-mode in Codex |
| S5 | Headroom is off by default and is never used for Codex | it changes the provider route and authorization; unstable operation led to turning it off; when off, `ANTHROPIC_BASE_URL` is set explicitly to the official URL | permanent proxy for every agent |
| S6 | RTK is experimental and is judged only by an A/B run on identical tasks; Codex calls it through an adapter that adds `permissionDecision: allow` | `rtk gain` measures shorter output, not the cost of a finished task | count `rtk gain` as savings |
| S7 | TokenEconomizer runs with the shared `shadow=true` and `toolprune=propose`; each agent switches only its own plugin | observation first; the shared file affects every agent | turn mechanisms on without measurement; disable through the shared file |
| S8 | Caveman and Ponytail rules have one source per agent: a plugin (Claude Code, OpenCode) or the global `AGENTS.md` (Codex) | a plugin and a copy in the instruction file inject the same rules twice on every turn | both |
| S9 | Two modes: dev (full stack without Headroom) and doc (no Caveman, context-mode, Ponytail) | answer-shaping tools damage formal documents; traffic tools do not | one mode for everything |
| S10 | Codex permissions mirror Claude Code: whole file system readable except Claude's read-denied paths, writes in the workspace and in the shared orchestration caches `~/.cache/herdr-orch`, `~/.cache/herdr-agent-kit`, `auto_review` for the rest; the profile never denies `":root"`; `doctor` runs `codex sandbox -- /bin/true` | one policy for every agent of the person; a `":root"` deny hides the Codex binary from its own bwrap sandbox and breaks every shell command | a stricter Codex-only profile; `-s workspace-write` in worker commands (it drops the profile and opens all reads) |
| S11 | Hook latency budget about 100 ms per hook; measured after each plugin update | hooks run on every tool call; a vendor doctor may report OK while a hook takes seconds | trust the vendor diagnostics |
| S12 | Public part in git, machine specifics in the git-ignored `local/`; local agent rules are appended to the generated global rules | the same repository serves the author and anyone it is handed to, without leaking paths, hosts or secret locations | a private fork per machine |
| S13 | Each agent owns its configuration folder; others only read it | independent switches; one agent's change cannot break another | one script managing every agent |
