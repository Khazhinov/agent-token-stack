# Agent entry point

## Publication safety (mandatory, read first)

This repository is public. Every agent working here, including one that only installs or configures something, keeps
the machine out of git:

1. Machine-specific data stays in git-ignored places (`local/`, `stash.json`). Never copy it into tracked files,
   commit messages, tags, release notes, pull requests or issues.
2. Tracked files never contain absolute home or mount paths, user, host, company or project names,
   private service addresses, tokens, keys, `.env` values, filled MCP configs or session logs. Use
   placeholders (`<home>`, `/absolute/path/to/...`, `example.com`).
3. A new tool, installer or config may write files into the working tree. Before the first commit
   add such paths to `.gitignore` and check `git status --short --ignored`.
4. Before a commit read `git diff --cached` and run `./scripts/self-check.sh`. Commit only with the author identity
   the person set for this repository. Push and publish only when the person asks.
5. In doubt whether something is private, do not commit it: ask the person.

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
| OpenCode | `agents/opencode/install.sh`, then merge the stack keys of `opencode.example.json` ([agents/opencode/README.md](agents/opencode/README.md)) | `agents/opencode/verify.sh` |

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
