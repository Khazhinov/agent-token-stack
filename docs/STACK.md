# Stack

English | [Русский](STACK.ru.md)

## 1. Principle

Savings come from independent levels, so tools are installed one at a time and each can be
switched off alone.

| Level | What shrinks | Tool |
|---|---|---|
| Data source | code the agent reads while exploring a project | codebase-memory-mcp (CBM) |
| Shell output | output of `git`, tests, builds, `grep`, logs | RTK |
| Tool output in context | large outputs stay in a sandbox, a summary enters the context | context-mode |
| Traffic to the provider | the whole request is compressed before the API | Headroom |
| Model answers | prose in the agent's answers | Caveman |
| Generated code | code volume, by refusing over-engineering | Ponytail |
| Observation | measures waste before any automatic pruning | TokenEconomizer |

Ponytail is not a token tool in the narrow sense: it reduces generated code and is part of the
stack as a development policy.

## 2. Components and compatibility

Savings figures are vendor claims and depend on the kind of work; this repository does not repeat
them as measured facts.

| Tool | Repository | Vendor claim | Mechanism | Compatibility notes |
|---|---|---|---|---|
| CBM | [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) | up to 99% on code exploration | MCP server with a code knowledge graph, plus a CLI mode | any MCP client; its installer configures about 40 environments at once (see section 4) |
| RTK | [rtk-ai/rtk](https://github.com/rtk-ai/rtk) | 60-90% on CLI output | hook that rewrites shell commands to `rtk <cmd>` | only environments that can intercept commands (hook or plugin); elsewhere only an instruction |
| context-mode | [mksglu/context-mode](https://github.com/mksglu/context-mode) | up to 98% on large outputs | sandbox MCP server and hooks | full mode in Claude Code, Codex CLI, Cursor, OpenCode, Gemini CLI, Copilot and others; Node.js >= 22.5 or Bun |
| Headroom | [chopratejas/headroom](https://github.com/chopratejas/headroom) | 47-92% on traffic | local proxy between the agent and the provider | `headroom wrap <agent>` for Claude Code, Codex, OpenCode and others; changes the provider route and authorization |
| Caveman | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | 50-75% on answers | answer style rules (skill or plugin) | skill in 30+ environments; plugin with hooks and statusline in Claude Code; plugin for OpenCode |
| Ponytail | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | not a goal; less code | "ladder" of minimal implementation | plugin with hooks: Claude Code, Codex, Copilot CLI, OpenCode, Gemini CLI, Cursor; rules only: any environment reading `AGENTS.md` |
| TokenEconomizer | [microsoft/TokenEconomizer](https://github.com/microsoft/TokenEconomizer/tree/main/plugin) | depends on the mechanism | plugin: loop guard, tool pruning proposals, micro-skills | Claude Code and Codex plugins share `~/.tokeneconomizer/config.json` |

## 3. Per-agent wiring

| Tool | Claude Code | Codex CLI | OpenCode |
|---|---|---|---|
| CBM | `.mcp.json` per project with code | one global `[mcp_servers.codebase-memory]` with `enabled_tools` allow-list | `mcp` in the project's `opencode.json` |
| RTK | `PreToolUse` hook `rtk hook claude` | `PreToolUse` hook through an adapter (`rtk-codex-hook.py`) | plugin `rtk.ts` (`rtk init -g --opencode`) |
| context-mode | plugin `context-mode@context-mode` | not used: native `tool_output_token_limit`, `project_doc_max_bytes`, compaction | npm plugin `context-mode` |
| Headroom | `ANTHROPIC_BASE_URL` to the proxy, off by default | not used | `headroom wrap opencode`, off by default |
| Caveman | plugin `caveman@caveman` | not used (global rules are compact already) | plugin from `src/plugins/opencode` |
| Ponytail | plugin `ponytail@ponytail` | compact rules in the global `AGENTS.md` | plugin `@dietrichgebert/ponytail` |
| TokenEconomizer | plugin, `shadow=true` | plugin, `shadow=true` | not used |
| Permissions | `permissions.deny` and `sandbox.filesystem.denyRead` for secrets, auto mode | profile `workspace-only` mirroring Claude's read denies, `auto_review` | defaults |

Installed plugins and MCP servers take effect after a session restart.

### 3.1. CBM per project (Claude Code)

A global MCP registration loads the schemas of all its tools into every session, including folders
without code. Claude Code gets CBM through `.mcp.json` in the root of each project with code:

```json
{
  "mcpServers": {
    "codebase-memory-mcp": {
      "command": "codebase-memory-mcp"
    }
  }
}
```

Optionally the command is wrapped by `caveman-shrink`, which compresses tool output:
`"command": "node", "args": ["<caveman>/src/mcp-servers/caveman-shrink/index.js", "<path to codebase-memory-mcp>"]`.
After connecting, the agent checks `index_status` and runs `index_repository` if there is no index.
Without MCP the same tools run through `codebase-memory-mcp cli <tool> '<json>'`.

Signal for an agent: the project has code, but no `mcp__codebase-memory-mcp__*` tools are listed -
the graph is not attached to this project. Create `.mcp.json`, ask the person to restart the session.

### 3.2. Codex: native limits and an allow-list

Codex covers the role of context-mode with native mechanisms. Managed by
[agents/codex](../agents/codex/README.md):

```toml
tool_output_token_limit = 10000
project_doc_max_bytes = 16384

[features]
hooks = true

[mcp_servers.codebase-memory]
command = "/absolute/path/to/codebase-memory-mcp"
enabled = true
startup_timeout_sec = 20
tool_timeout_sec = 120
enabled_tools = ["index_status", "index_repository", "detect_changes", "search_graph", "get_architecture", "trace_path", "get_code_snippet", "search_code"]
```

`enabled_tools` limits the number of tool schemas loaded into the context.

## 4. Shared machine

Several agents on one machine share some things and must not share others.

| Object | Owner | Rule |
|---|---|---|
| `~/.claude/**`, `~/.claude.json` | Claude part | Codex and OpenCode only read it |
| `~/.codex/**`, `~/.agents/skills/token-stack` | Codex part | change through `manage.py`, never by hand from another agent |
| `~/.config/opencode/**` | OpenCode part | change through its installer |
| `~/.local/bin/rtk`, `~/.local/bin/codebase-memory-mcp` | shared | one version per machine; the pin and SHA-256 live in `BINARY_SPECS` of `manage.py`; only one process updates them |
| `~/.cache/codebase-memory-mcp` | shared | indexes and daemon state; never delete; never index one project from two agents at once |
| `~/.tokeneconomizer/config.json` | shared | changed only in agreement for all agents; each agent switches only its own plugin |
| Headroom, context-mode, Caveman | per agent | never add their provider, env, hooks or MCP to another agent's configuration |
| Ponytail | per agent | Claude Code and OpenCode: plugin; Codex: compact rules in `AGENTS.md`. Do not install the plugin in Codex: its hooks duplicate those rules |

Switches are independent: turning RTK off for Claude must not turn it off for Codex, and the
reverse. Shared are only the binaries and the index data.

Forbidden:

1. Second copies of RTK or CBM inside `~/.claude`, `~/.codex` or a project.
2. `codebase-memory-mcp install` or `update` to update: it finds every agent and adds hooks, skills,
   instructions and duplicate MCP registrations to all of them.
3. Deleting `~/.cache/codebase-memory-mcp`, `_config.db` or `*.db` as a way to update.
4. Two updaters or two `index_repository` runs for one project at the same time.

Coordinated update of RTK or CBM:

1. Record the state: `toggle.py status`, `manage.py status`, `rtk --version`, `codebase-memory-mcp --version`.
2. Make sure no other agent updates or indexes. Raise the pin and SHA-256 in `BINARY_SPECS`
   (from the official release), run `manage.py install` and `manage.py doctor`.
3. After any third-party installer restore both managed configurations: `toggle.py normalize`,
   `manage.py install`, `manage.py doctor`.
4. Restart every MCP client so it loads the new CBM process.
5. Repeat both status commands; check the project with `index_status`. Re-index only missing or
   incompatible indexes, one project at a time.

## 5. Rules for agent instruction files

Copy the block into `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` or an equivalent; drop lines about tools
that are not installed. The Codex version lives in [agents/codex/AGENTS.md](../agents/codex/AGENTS.md),
the Claude version in [agents/claude-code/RULES.md](../agents/claude-code/RULES.md).

```markdown
## Context economy

- Start code exploration with codebase-memory-mcp: `index_status`, then `search_graph`,
  `get_architecture`, `trace_path`, `get_code_snippet`. Grep and file reads confirm details and cover
  files without code. A missing index does not stop the task.
- Run noisy commands through RTK (`rtk git`, `rtk test`, `rtk grep`, `rtk log`, `rtk json`); the hook
  rewrites suitable commands. Do not use RTK when the full verbatim output is needed.
- Do not keep outputs of several hundred lines in context: process them in the context-mode sandbox
  (`ctx_execute`, `ctx_batch_execute`) and print only the result.
- Do not preload references. Keep the instruction file short, narrow rules in nested files,
  repeatable processes in skills.
- Before compaction record open decisions, verified facts and changed files.
```

## 6. Modes

Tools that change answer text (Caveman, context-mode, Ponytail) get in the way of document work:
answers become fragmentary and outputs are shortened. Traffic tools (RTK, Headroom, CBM) do not
change answer content.

| Mode | On | Off |
|---|---|---|
| dev | everything except Headroom | Headroom |
| doc | RTK, CBM | Caveman, context-mode, Ponytail, Headroom |

Claude Code: `/stack mode doc|dev`. OpenCode: `/caveman off`, `/ponytail off` for the session, or
`CAVEMAN_DEFAULT_MODE=off PONYTAIL_DEFAULT_MODE=off`. Codex keeps compact rules in `AGENTS.md`
and has no answer-style plugin to switch.

A switcher for another environment needs: `status`, `mode dev|doc`, `on|off <tool|all>`;
plugins switched by the environment's own flag; hooks and MCP saved to a stash on off and restored
from it on on; `normalize` that removes duplicates after third-party installers; restart marks in
`status`; no effect on another agent's configuration.

## 7. Verified versions

Snapshot of 2026-11-03, Linux (WSL2).

| Component | Version |
|---|---|
| Claude Code | 2.1.316 |
| Codex CLI | 0.166.0 |
| OpenCode | 1.19.5 |
| RTK | 0.49.0 |
| codebase-memory-mcp | 0.12.1 |
| context-mode (Claude plugin) | 1.0.169 at the 2026-09-21 measurement; current version requires a check |
| Caveman (OpenCode plugin) | 2.7.0 |
| Ponytail | 4.10.0 (Codex rules), 5.3.3 (OpenCode plugin) |
| TokenEconomizer | 0.1.0 |
| Node.js | 22.22.0 |

The real version of a shared tool is what its binary reports, not what a document says.
