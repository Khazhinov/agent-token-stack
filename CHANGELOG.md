# Changelog

## 0.2.3 - 2026-11-09

- Codex: `features.daemon_auto_start = false`; a plain `codex` no longer runs commands in the shared
  app-server daemon with another terminal's environment.
- Codex: the profile `workspace-only` allows writes to the shared orchestration caches
  `~/.cache/herdr-orch` and `~/.cache/herdr-agent-kit`.

## 0.2.2 - 2026-11-09

- Codex: the permission profile `workspace-only` turns the network on, as for Claude Code Bash;
  without it commands cannot reach local Unix sockets (herdr-core `hc`, Docker).

## 0.2.1 - 2026-11-04

- Codex: the RTK hook command goes through the skill link `~/.agents/skills/token-stack`; moving the
  repository no longer makes Codex ask to review hooks again.

## 0.2.0 - 2026-11-04

- OpenCode: `install.sh`, `verify.sh`, plugin copies (RTK, Caveman, Ponytail), Caveman skill and
  `AGENTS.stack.md` loaded through `instructions`.
- Global rules of every agent carry a short stack notice; agents suggest switches, the person runs them.
- Claude Code `RULES.md`: structural read rule, Ponytail and GSD rules.
- Troubleshooting: `codex sandbox` inside a Codex session, relative OpenCode `instructions`.

## 0.1.0 - 2026-11-03

- First public version: stack description, setup and update procedures, decisions, journal,
  troubleshooting, Claude Code, Codex and OpenCode configuration examples with rationale.
- Codex installer (`manage.py`): permission profile mirrors Claude Code read denies (no `":root"` deny),
  `doctor` checks `codex sandbox -- /bin/true`, local rules from `local/codex/AGENTS.md` are appended
  to the global `AGENTS.md`.
- Claude Code switcher (`toggle.py`) and both installers without machine-specific paths.
- `scripts/self-check.sh`: installer tests, privacy and typography checks.

## Unreleased

- Carry upstream-maintenance authorization in shared instructions for all three runtimes and require propagation into consuming project instructions.
