# Journal

English | [Русский](JOURNAL.ru.md)

Dated evolution of the stack. Each entry: what changed, why, and what it gave. Machine-specific
details stay in `local/JOURNAL.md`.

## 2026-07-02 - context audit (Claude Code)

- Caveman hooks were registered twice: by the plugin and by explicit entries left in `settings.json`
  by the standalone installer. The rules block arrived twice at session start and on every message.
  The explicit entries were removed; the plugin is the only source.
- CBM was registered twice globally (`~/.claude.json` and `~/.claude/.mcp.json`), loading about 14
  tool schemas into every session. Both entries were removed; CBM moved to `.mcp.json` per project.
- Rarely needed parts of the global `CLAUDE.md` moved into skills loaded by trigger phrases
  (progressive disclosure).
- The stack switcher skill was moved under version control.

## 2026-09-17 - Codex stack and the CBM updater

- First managed installation of the Codex stack (the `*.pre-token-stack` backups date from this day).
- The CBM 0.11.0 updater added a global MCP registration and duplicate hooks again; `normalize` was
  confirmed to remove them. CBM 0.11 changed the index format: old indexes were dropped and rebuilt
  on first use.

## 2026-09-21 - hook latency

- context-mode hooks took 2.2-2.3 s: a dependency helper ran `npm install better-sqlite3` on every
  hook call, the install failed and the error was swallowed. After the fix: about 40 ms.
- The CBM gate on Grep and Glob took 1.6 s even in projects without a graph. An early exit when the
  project has no CBM in `.mcp.json` brought it to 9 ms.
- The vendor doctor reported OK in the broken state; hook timing became a check of its own.

## 2026-09-28 - shareable description

- First description of the stack meant for other people's agents: levels, compatibility,
  per-agent wiring, known problems, mode switcher requirements. Verified then: RTK 0.49.0,
  CBM 0.11.0, context-mode 1.0.169, Ponytail 4.10.0, Codex CLI 0.154.0.

## 2026-10-01 - Headroom off

- Headroom was turned off by default because of unstable operation. Turning it off by deleting
  `ANTHROPIC_BASE_URL` left terminals opened earlier pointing at the stopped proxy; the switch now
  writes the official URL explicitly.

## 2026-11-02 - Codex snapshot, TokenEconomizer, OpenCode

- Codex CLI 0.166.0, CBM 0.12.1 (one rebuild of each old index on the next indexing).
- TokenEconomizer 0.1.0 installed as a plugin in Claude Code and Codex with the shared
  `shadow=true`, `toolprune=propose`; about 60 ms per hook call.
- Codex got a permission profile and `auto_review` through the stack installer.
- OpenCode got its own managed configuration: CBM per project, context-mode as an npm plugin,
  RTK plugin, Caveman 2.7.0 and Ponytail 5.3.3 as plugins kept in the repository. Full Caveman and
  Ponytail sections were removed from its `AGENTS.md`: the plugins inject the same rules
  (about 760 and 490 words) on every turn.
- A portable brief for setting up the stack by another agent was written.

## 2026-11-03 - Codex sandbox regression, permission parity, this repository

- The Codex profile denied `":root"`. Codex starts its own binary inside bwrap, so every shell
  command failed with `bwrap: execvp .../codex`; agents started without an explicit `-s` stopped
  without doing anything. A workaround with `-s workspace-write` hid the error but dropped the
  profile and opened every file for reading.
- Fix: the Codex profile now mirrors Claude Code - everything readable except paths Claude may not
  read, writes in the workspace, `auto_review` for the rest. `doctor` runs `codex sandbox -- /bin/true`.
- Claude Code path conventions differ between lists: in `Read(...)` rules a single leading `/` is
  relative to the settings source (`~/.claude` for user settings), in `sandbox.filesystem.denyRead` it is
  absolute. The Codex installer follows both conventions.
- The stack moved into this repository: one public description with examples and reasons for every
  agent, machine specifics in the git-ignored `local/`.

## 2026-11-04 - all agents run the stack from this repository

- Each agent moved its stack part here: the Claude Code `stack` skill is linked from
  `agents/claude-code`, its switcher state stays next to it and is git-ignored; Codex installs from
  `agents/codex`; OpenCode got an installer, a verifier, plugin copies and an instructions file.
  The former per-agent folders keep only settings unrelated to the stack.
- Every agent's global rules got a short notice: a stack exists, where it is described, which
  command switches a component, and that the agent only suggests a switch and never switches by itself.
- OpenCode resolves relative `instructions` paths from the working directory; the global file uses an
  absolute path.
- `codex sandbox -- /bin/true` fails when started from inside a Codex session; the check is run from
  an ordinary terminal.
