# Setup

English | [Русский](SETUP.ru.md)

Procedure for an agent that sets up the stack on a machine. It works for Claude Code, Codex CLI,
OpenCode or any combination of them. Before installing, check every command against the current
README of the tool: supported environments change between versions.

## 1. Discover the environment and save the initial state

1. Find the OS, WSL or container, architecture, home folder, installed `codex`, `claude`, `opencode`,
   `rtk`, `codebase-memory-mcp`, the active `CODEX_HOME` and Claude settings. Check how agents are
   really started (a terminal multiplexer or desktop app may override profiles or environment);
   do not infer it from folder names.
2. Record versions, MCP servers and plugins, active hooks, binary paths, current limits and
   permissions. Look up projects that already have CBM indexes; do not index them all up front.
3. Back up every file you will change. Do not overwrite the model, authorization, other MCP servers,
   the person's instructions or secrets. Do not print secrets.
4. If the machine already has management scripts or skills, study them and use them as the source of
   configuration: change the source file, then apply it with its installer; never patch only the
   generated copy in the home folder.
5. Write what you found to `local/README.md` (machine profile) and start `local/JOURNAL.md`.

## 2. Shared layer

1. Install one compatible CBM version from the
   [official releases](https://github.com/DeusData/codebase-memory-mcp/releases) and check the
   SHA-256 of the binary. `manage.py install` does this for the pinned version. Never run
   `codebase-memory-mcp install` over an existing configuration of several agents.
2. Attach CBM exactly once per agent ([STACK.md](STACK.md), section 3). Index a project when work in
   it starts.
3. RTK is optional: install it only together with a task on which it can be compared with a run
   without RTK. Keep one shared binary.
4. Install TokenEconomizer only if the current agent versions are supported. Start with the shared
   `shadow=true` and `toolprune=propose`, with no automatic tool pruning.

## 3. Each agent

**Codex:** run `agents/codex/install.sh`. It links `~/.codex/AGENTS.md` and the `token-stack` skill,
merges the managed blocks into `~/.codex/config.toml` (keeping the model, trust and other settings),
adds the RTK hook to `~/.codex/hooks.json` and runs `doctor`. Local rules for this machine go to
`local/codex/AGENTS.md`; with that file `install` writes public plus local rules to `~/.codex/AGENTS.md`
instead of linking it. Details:
[agents/codex/README.md](../agents/codex/README.md).

**Claude Code:** link `agents/claude-code/skills/stack` to `~/.claude/skills/stack`, add the rules
from [agents/claude-code/RULES.md](../agents/claude-code/RULES.md) to `~/.claude/CLAUDE.md`
(or import them with `@<path>`), install the plugins you choose and run `/stack normalize`, then
`/stack`. Details: [agents/claude-code/README.md](../agents/claude-code/README.md).

**OpenCode:** run `agents/opencode/install.sh`, merge the stack keys of `opencode.example.json` into the
global `opencode.json` (keep the model and provider settings), then run `agents/opencode/verify.sh`.
Details: [agents/opencode/README.md](../agents/opencode/README.md).

**Several agents:** shared binaries and the CBM cache are updated by one agent at a time; settings,
hooks and plugins are switched per agent. Check independence: record the state of every agent and of
the shared TokenEconomizer file, switch one component in one agent, make sure the others did not
change, restore.

## 4. Launch environment

If agents are usually started from a multiplexer or desktop app, write this into the **global**
instructions of each agent through `local/<agent>/` so the rule applies in an empty folder too:
where the agent process runs, where the UI runs, and that the launcher may override parameters.

## 5. Checks

1. Syntax of every changed configuration, one instance of each MCP server, plugin states, per-agent
   switches, native limits, unchanged permission policy.
2. `manage.py doctor` (includes `codex sandbox -- /bin/true`), `/stack`, `opencode debug config`.
3. One small request through each installed agent.
4. Hook latency: every hook below about 100 ms ([TROUBLESHOOTING.md](TROUBLESHOOTING.md)).
5. If an integration breaks an agent, turn off only its local component, restore the file from the
   backup and check again. Do not delete shared binaries or indexes during a local rollback.

## 6. Report to the person

Found environments and versions; changed files and backups; shared and local components; exact
`status`, `on`, `off` commands per agent; check results; what stays experimental. Write the same to
`local/JOURNAL.md`.

## 7. Measuring savings

Take 10-15 typical tasks from the person's repositories. Compare identical commits, models and
effort, at least three runs each: base stack, without RTK, then one TokenEconomizer mechanism at a
time. Measure full and cached input and output tokens, turns and compactions, time, test results and
the share of successful first attempts. Note subscription cost and unavailable metrics separately,
without invented prices. Restore the baseline after every run; do not turn off auto review.
