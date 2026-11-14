# Codex stack components

## RTK

Binary shared with Claude: `~/.local/bin/rtk`, pinned at 1.2.0. Codex PreToolUse calls `scripts/rtk-codex-hook.py` through the compatible `hook claude` handler, and the adapter adds the `permissionDecision: allow` field Codex requires. The hook command uses the stable skill link `~/.agents/skills/token-stack`, not the repository path: Codex trusts a hook by its command hash, and a repository move must not trigger a new review. Any other change of the command still asks once to trust the new hash. RTK is experimental: shorter tool output is not the same as fewer tokens or a cheaper finished task; judge it only by an A/B run on your own work.

Checks: `rtk --version`, `rtk hook check 'rg --files'`, `python3 scripts/manage.py doctor`. Do not skip the `rg --files` check: RTK 0.42.4 wrongly rewrote it to `rtk grep --files`.

If the binary is missing or older than the pin, `manage.py install` downloads the release asset, checks SHA-256 and installs it into the shared `~/.local/bin`. It never downgrades a newer version.

## Codebase Memory

Shared binary and cache: `~/.local/bin/codebase-memory-mcp` and `~/.cache/codebase-memory-mcp`. Codex registers one global MCP server `codebase-memory` with an allow-list of eight tools. Start with `index_status`; index a new code project only when needed.

Fallback without the MCP schema: `codebase-memory-mcp cli <tool> '<json>'`. Version 0.12.1 rebuilds each old index once on the next indexing; do not delete the shared cache and do not rebuild every project without need. The CBM updater may add a second `codebase-memory-mcp` server, a SessionStart hook and a large block in `AGENTS.md`; a repeated `manage.py install` removes the duplicates and restores the managed file.

## Native

`tool_output_token_limit` caps one stored tool result. `project_doc_max_bytes` caps the combined project instruction budget, not each individual file. `model_auto_compact_token_limit = 160000` starts compaction before a large context keeps growing; `/compact` starts it by hand. Compaction has a cost and can lose detail; this threshold is an operating default, not a measured savings guarantee.

## Permissions

The profile `workspace-only` gives Codex the same reach as Claude Code: the whole file system is readable except the paths Claude may not read (`permissions.deny` with `Read(...)` and `sandbox.filesystem.denyRead` in `~/.claude/settings.json`); writes stay in the workspace; `approvals_reviewer = "auto_review"` judges actions outside it. The profile never denies `":root"`: Codex starts its own binary inside bwrap, and a hidden binary breaks every shell command with `bwrap: execvp .../codex`. `doctor` runs `codex sandbox -- /bin/true` to catch this.

## Local preferences

Machine preferences may live in the ignored `local/codex/settings.json`: `{"reasoning_effort":"medium","trust_all_directories":true}`. Only an explicit preference changes the person's effort. The auto-trust option installs `scripts/codex-launch.py` as `~/.local/bin/codex` for a standalone installation, backing up the previous link as `codex.pre-token-stack`. It calls the normal current binary with `--no-daemon` and an exact trust override for the selected cwd, including `-C`/`--cd`. A trusted ancestor or wildcard does not implement trust for all folders. Action review and hook trust remain independent; the launcher does not bypass either. A future standalone updater may restore its own command link; rerun the stack installer then.

`local/codex/settings.json` may also list `read_denies` (for example `~/.private/file`). Installation
retains existing Codex deny entries even if Claude no longer lists them. Skill backups named
`token-stack.pre-*` are moved from `~/.agents/skills` to `~/.agents/skill-backups` without deletion.

## Global rules and Ponytail

`~/.codex/AGENTS.md` links to the public `AGENTS.md` of this folder; with `local/codex/AGENTS.md` in the repository it is a generated file: public rules followed by local ones. The rules hold the short permanent policy: progressive disclosure, CBM first, RTK for noisy output, compaction and Ponytail full. The Ponytail source is pinned at 4.10.0 (`1d95ff7d39de12d87014ea40d4e22201bddc501b`, MIT).

The full Ponytail plugin is not needed on purpose: its SessionStart and UserPrompt hooks would duplicate the permanent rules. When updating Ponytail, compare the upstream `AGENTS.md`, keep the safety boundaries and update the version here.

## Headroom and Claude-only tools

Do not route Codex through Headroom: it is a proxy/provider and changes the authorization path. Claude `context-mode`, Caveman and `caveman-shrink` are not carried over either: native compaction, limits, compact CBM 0.12.1 output, RTK and the global rules cover part of their role. Add a second filter only after measuring it on identical tasks.

## Configuration compatibility

Use `approval_policy = "on-request"` with Auto-review; `never` prevents escalation instead of automating it. Do not generate `auto_review.extra_policy`: Codex 0.169 rejects that unsupported field under `--strict-config`. `doctor` checks strict startup too.

## TokenEconomizer

`shadow=true` suppresses interventions, not every model call: the loop guard can still run a separate judge. Inspect the Codex ledger's `kind=overhead` records before assuming observation is free. Its fallback-weighted `effective_tokens` are estimates, not subscription usage or raw token counts. Disable only the Codex plugin with `manage.py off te` when explicitly requested; leave the shared config and Claude plugin unchanged. Installation preserves that choice.
