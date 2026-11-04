# Agent entry point

You are an agent asked to set up, check or update a token optimization stack on this machine.
This repository is the source of truth. Work in this order and stop to ask the person whenever
something is ambiguous or would overwrite their settings.

## 1. Orient

1. Read `local/README.md` if it exists: it describes this machine (OS, agents in use, launch
   environment, secret locations, proxies). If `local/` does not exist, copy `local.example/` to
   `local/` and fill it in together with the person. Never commit `local/`.
2. Detect which agents are installed (`claude`, `codex`, `opencode`) and how they are started.
   Configure only agents that exist.
3. Read [docs/STACK.md](docs/STACK.md), then [docs/DECISIONS.md](docs/DECISIONS.md). Do not install
   a component the decisions reject without a measured reason.

## 2. Set up or repair

Follow [docs/SETUP.md](docs/SETUP.md). Per agent:

| Agent | Installer | Check |
|---|---|---|
| Codex | `agents/codex/install.sh` (runs `manage.py install` and `doctor`) | `manage.py status`, `manage.py doctor` |
| Claude Code | link `agents/claude-code/skills/stack` to `~/.claude/skills/stack` | `/stack`, `toggle.py normalize` |
| OpenCode | [agents/opencode/README.md](agents/opencode/README.md) | `opencode debug config` |

Back up every file you change. Never print secrets. Never delete shared caches
(`~/.cache/codebase-memory-mcp`) or shared binaries.

## 3. Update

Follow [docs/UPDATE.md](docs/UPDATE.md): fetch this repository, read new entries of
[CHANGELOG.md](CHANGELOG.md) and [docs/JOURNAL.md](docs/JOURNAL.md), apply what concerns the agents
on this machine, run the checks.

## 4. Record

Machine-specific results go to `local/JOURNAL.md`: what you changed, why, and check results.
A finding useful on any machine (a new problem and its fix, a better default) goes to the public
docs: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md), [docs/DECISIONS.md](docs/DECISIONS.md),
a dated entry in [docs/JOURNAL.md](docs/JOURNAL.md) and a line in [CHANGELOG.md](CHANGELOG.md),
written without names of people, projects, hosts or paths of this machine. Keep the English file and
its `*.ru.md` copy in sync. Run `./scripts/self-check.sh` before a commit.
