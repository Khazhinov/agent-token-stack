# OpenCode

English | [Русский](README.ru.md)

## Contents

| Path | Purpose |
|---|---|
| `install.sh` | links the stack plugins, the Caveman skill and the stack rules into `~/.config/opencode`; backs up replaced files with `.pre-agent-token-stack` |
| `verify.sh` | checks the binaries, links, loaded plugins, imported rules and plugin modules; runs `local/opencode/verify.local.sh` when present |
| `AGENTS.stack.md` | stack rules supplied as ambient instructions through the `instructions` array of the global `opencode.json` |
| `plugins/rtk.ts` | RTK plugin as created by `rtk init -g --opencode`; delegates to `rtk rewrite` |
| `plugins/caveman/` | Caveman OpenCode plugin files and LICENSE |
| `plugins/ponytail/` | Ponytail OpenCode plugin files, commands, skills and LICENSE |
| `skills/caveman/` | Caveman `SKILL.md`, read by the plugin on every request |
| `docs/shared-node.md` | ownership and coordinated update rules for OpenCode, Claude Code and Codex |
| `docs/REPORT-2026-11-02.md` | generic findings from the OpenCode migration |
| `opencode.example.json` | stack part of the global `~/.config/opencode/opencode.json`: compaction, plugins and instructions; no global MCP |
| `opencode.project.example.json` | `opencode.json` for the root of a project with code (CBM per project) |

## Installation

```bash
./agents/opencode/install.sh
./agents/opencode/verify.sh
```

The installer is idempotent. It:

- links `plugins/caveman`, `plugins/ponytail`, `plugins/rtk.ts`, `skills/caveman` and `AGENTS.stack.md`
  into `~/.config/opencode`;
- saves a replaced file or symlink once with the suffix `.pre-agent-token-stack`;
- reports whether `rtk` and `codebase-memory-mcp` are in `PATH`.

Restart OpenCode after the first installation or after a plugin update.

## Merging the stack part into a global config

A global `opencode.json` also carries machine settings: models, disabled providers and non-stack
plugins. Keep that file in the machine's own configuration folder; do not replace it with the
example. Merge only the stack keys from `opencode.example.json`:

```json
{
  "compaction": {
    "auto": true,
    "prune": true
  },
  "plugin": [
    "context-mode",
    "./plugins/caveman/plugin.js",
    "./plugins/ponytail/.opencode/plugins/ponytail.mjs"
  ],
  "instructions": ["/absolute/path/to/agent-token-stack/agents/opencode/AGENTS.stack.md"]
}
```

Keep any other keys of the global file. Use the absolute path to `AGENTS.stack.md`: OpenCode resolves
relative instruction paths from the working directory, not from the config folder. The plugin paths
resolve through the links in `~/.config/opencode/plugins`.

CBM is not added to the global file. Put `mcp` from `opencode.project.example.json` into the
`opencode.json` of each project with code; if the project already has that file, add only the `mcp`
object. Restart OpenCode after the change.

## Checks

```bash
opencode debug info
opencode debug config
opencode mcp list
rtk rewrite "git status"
```

`opencode debug info` lists the loaded plugins. `opencode debug config` shows the `plugin` array and
the imported `instructions`. `opencode mcp list` run from a project root shows whether CBM is
attached; then call `index_status` in the session.

## Why it is configured this way

| Choice | Reason |
|---|---|
| CBM per project | a global registration loads about 14 tool schemas into every session, including folders without code |
| plugin files kept in the repository | the vendor installers copy files, append blocks to `AGENTS.md` and may add MCP entries; repository copies work offline and reproducibly |
| no Caveman or Ponytail rules in `AGENTS.md` | the plugins inject their rules on every turn; a copy would duplicate them |
| stack rules imported through `instructions` | the global `AGENTS.md` keeps only personal and non-stack rules, while the stack rules stay in this repository |
| Headroom only through `headroom wrap opencode` | it is not part of the OpenCode configuration and is off by default |

## Modes

Caveman and Ponytail switch per session with `/caveman off` and `/ponytail off` (or
`lite|full|ultra`). Documents mode for a whole run:

```bash
CAVEMAN_DEFAULT_MODE=off PONYTAIL_DEFAULT_MODE=off opencode
```

Removing a line from `plugin` and restarting stops loading the plugin entirely.

Machine-specific values, model names and the list of projects with CBM stay in `local/opencode/`.
