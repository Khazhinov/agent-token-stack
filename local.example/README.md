# This machine

Copy `local.example/` to `local/` and fill it in. Git ignores `local/`.

## Environment

| Item | Value |
|---|---|
| OS, WSL or container | |
| Agents in use and versions | |
| How agents are started (terminal, multiplexer, desktop app) | |
| Where agent processes run and where the UI runs | |
| Proxies and network constraints | |
| Secret locations agents must never read | |

## Agent-specific notes

- `local/codex/AGENTS.md`: appended to the global Codex rules by `manage.py install`.
- `local/claude-code/RULES.md`: import from `~/.claude/CLAUDE.md` with `@<path>`.
- `local/private-patterns.txt`: one regular expression per line; `scripts/self-check.sh` refuses
  public files that match (host names, user names, project names).
