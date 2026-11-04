# OpenCode

English | [Русский](README.ru.md)

## Contents

| Path | Purpose |
|---|---|
| `opencode.example.json` | global `~/.config/opencode/opencode.json`: compaction and plugins; no global MCP |
| `opencode.project.example.json` | `opencode.json` for the root of a project with code (CBM per project) |
| `rtk.ts` | RTK plugin as created by `rtk init -g --opencode`; delegates to `rtk rewrite` |

## Installation

1. Keep the managed files in a folder under version control and link them into
   `~/.config/opencode` with an idempotent installer that backs up replaced files.
2. Plugins in the `plugin` array of `opencode.json`:
   - `context-mode` (npm) registers the `ctx_*` tools; no separate MCP is needed;
   - `./plugins/rtk.ts` (copy `rtk.ts` into `~/.config/opencode/plugins/`);
   - Caveman from `JuliusBrussee/caveman`, folder `src/plugins/opencode` (`plugin.js`, `package.json`,
     `caveman-config.cjs`, `caveman-parse.cjs`) plus its `SKILL.md` in `~/.config/opencode/skills/caveman`;
   - Ponytail from the npm package `@dietrichgebert/ponytail`.
3. CBM: put `mcp` from `opencode.project.example.json` into `opencode.json` of each project with code;
   add only the `mcp` object if the file exists. Restart OpenCode.

Checks: `opencode debug info` (plugins loaded), `opencode debug config` (the `plugin` array),
`opencode mcp list` from the project root, then `index_status`; `rtk rewrite "git status"`.

## Why it is configured this way

| Choice | Reason |
|---|---|
| CBM per project | the same reason as in Claude Code: a global registration loads about 14 tool schemas into every session |
| plugins kept in the repository, not installed by vendor installers | the Caveman installer copies files, appends a block to `AGENTS.md` and may add `mcp.caveman-shrink`, leaving the managed set; repository copies work offline and reproducibly |
| no Caveman or Ponytail sections in `AGENTS.md` | the plugins inject their rules (about 760 and 490 words at `full`) on every turn; a copy in `AGENTS.md` doubled them |
| Headroom only through `headroom wrap opencode` | not part of the OpenCode configuration; off by default |

## Modes

Caveman and Ponytail switch per session with `/caveman off`, `/ponytail off` (or `lite|full|ultra`).
Documents mode for a whole run: `CAVEMAN_DEFAULT_MODE=off PONYTAIL_DEFAULT_MODE=off opencode`.
Removing a line from `plugin` and restarting stops loading the plugin entirely.
