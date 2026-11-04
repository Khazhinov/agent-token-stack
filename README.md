# agent-token-stack

English | [Русский](README.ru.md)

A central, versioned description of a token and context optimization stack for coding agents
(Claude Code, Codex CLI, OpenCode), with working configuration examples, the reasons behind them
and a journal of how the stack evolved.

The repository is written for two readers:

- **an agent** that sets up or updates its own environment: it starts at [AGENTS.md](AGENTS.md);
- **a person** who wants to know what the stack does and why: this README and [docs/](docs/).

Hand the repository to another person and their agent can set up the same stack on their machine,
then come back from time to time, see what changed and update the local setup.

## What it saves

| Level | What shrinks | Tool |
|---|---|---|
| Data source | code the agent reads while exploring a project | codebase-memory-mcp (CBM) |
| Shell output | output of `git`, tests, builds, `grep`, logs | RTK |
| Tool output in context | large outputs stay in a sandbox, only a summary enters the context | context-mode (Claude, OpenCode); native limits and compaction (Codex) |
| Traffic to the provider | the whole request is compressed before the API | Headroom (off by default) |
| Model answers | prose in the agent's answers | Caveman |
| Generated code | code volume, by refusing over-engineering | Ponytail |
| Observation | measurement before any automatic pruning | TokenEconomizer (shadow mode) |

Details, compatibility and the per-agent wiring: [docs/STACK.md](docs/STACK.md).

## Layout

| Path | Content |
|---|---|
| [AGENTS.md](AGENTS.md) | entry point for an agent: setup and update procedure |
| [docs/STACK.md](docs/STACK.md) | components, compatibility, shared machine rules, instruction rules, modes, verified versions |
| [docs/SETUP.md](docs/SETUP.md) | step-by-step setup of a new environment |
| [docs/UPDATE.md](docs/UPDATE.md) | how an agent checks this repository for updates and applies them |
| [docs/DECISIONS.md](docs/DECISIONS.md) | decisions with rationale and rejected alternatives |
| [docs/JOURNAL.md](docs/JOURNAL.md) | dated evolution of the stack |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | known problems, symptoms and fixes |
| [agents/claude-code/](agents/claude-code/) | `stack` skill (`toggle.py`), settings and rules examples |
| [agents/codex/](agents/codex/) | `token-stack` skill (`manage.py`), global rules, config fragment, tests |
| [agents/opencode/](agents/opencode/) | configuration example, RTK plugin, plugin layout |
| `local/` | **git-ignored**: everything specific to one machine (paths, proxies, secret locations, private journal). Template: [local.example/](local.example/) |

## Public and private parts

Everything committed here must be useful on any machine. Machine specifics live in `local/`,
which git ignores: environment profile, local rules appended to the global agent instructions,
private journal entries. `scripts/self-check.sh` refuses home paths, drive mounts and the patterns
listed in `local/private-patterns.txt`, so a commit cannot leak them by accident.

## Quick start

```bash
git clone https://github.com/Khazhinov/agent-token-stack.git
cd agent-token-stack
cp -r local.example local          # then describe your machine in local/
```

Then start your agent in this folder and ask it: `Set up my environment according to AGENTS.md`.

## Checks

```bash
./scripts/self-check.sh            # tests of both installers, privacy and typography checks
```

## License

MIT. See [LICENSE](LICENSE). Third-party notices: [agents/codex/THIRD_PARTY_NOTICES.md](agents/codex/THIRD_PARTY_NOTICES.md).
