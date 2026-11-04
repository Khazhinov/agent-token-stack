# Changelog

## 0.1.0 - 2026-11-03

- First public version: stack description, setup and update procedures, decisions, journal,
  troubleshooting, Claude Code, Codex and OpenCode configuration examples with rationale.
- Codex installer (`manage.py`): permission profile mirrors Claude Code read denies (no `":root"` deny),
  `doctor` checks `codex sandbox -- /bin/true`, local rules from `local/codex/AGENTS.md` are appended
  to the global `AGENTS.md`.
- Claude Code switcher (`toggle.py`) and both installers without machine-specific paths.
- `scripts/self-check.sh`: installer tests, privacy and typography checks.
