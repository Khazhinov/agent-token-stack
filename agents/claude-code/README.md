# Claude Code

English | [Русский](README.ru.md)

## Contents

| Path | Purpose |
|---|---|
| `skills/stack/` | `stack` skill: `toggle.py` switches the stack, modes, updates, `normalize`; `test_toggle.py` runs in a temporary HOME |
| `RULES.md` | block for the global `~/.claude/CLAUDE.md` |
| `settings.example.json` | example of `~/.claude/settings.json` parts the stack relies on: secret read denies, plugins, explicit API URL |
| `mcp.example.json` | `.mcp.json` for the root of a project with code (CBM per project) |
| `hooks/cbm-gate-early-exit.sh` | CBM Grep/Glob gate with an early exit for projects without a graph |

## Installation

```bash
ln -s "$(pwd)/agents/claude-code/skills/stack" ~/.claude/skills/stack
```

Then:

1. Install the plugins you choose (two separate messages in Claude Code for each marketplace):
   `/plugin marketplace add mksglu/context-mode` + `/plugin install context-mode@context-mode`,
   `JuliusBrussee/caveman` + `caveman@caveman`, `DietrichGebert/ponytail` + `ponytail@ponytail`,
   `microsoft/TokenEconomizer` + `tokeneconomizer@tokeneconomizer`.
2. RTK hook: `rtk init -g`, or `/stack on rtk` after the binary is installed.
3. CBM: shared binary (see the Codex part for the pinned install), `.mcp.json` per project from
   `mcp.example.json`, the gate hook from `hooks/`.
4. Add `RULES.md` to `~/.claude/CLAUDE.md` (copy, or `@<path to RULES.md>`).
5. `/stack normalize`, then `/stack`. Restart the session where marked.

## Why it is configured this way

| Choice | Reason |
|---|---|
| CBM per project, not global | a global registration loads about 14 tool schemas into every session, including folders without code |
| Caveman, Ponytail, context-mode as plugins only | a second copy of the rules in `CLAUDE.md` or standalone hooks injects them twice on every turn |
| `normalize` after any third-party installer | the CBM installer and updater add global MCP entries and duplicate hooks |
| Headroom off by default, explicit `ANTHROPIC_BASE_URL` | the proxy changes the API route; deleting the variable leaves old terminals on a stopped proxy |
| doc and dev modes | answer-shaping tools damage formal documents |
| secret paths in both `permissions.deny` and `sandbox.filesystem.denyRead` | the first covers Claude's tools, the second shell commands in the sandbox; Codex mirrors both (see the Codex part) |
| hook latency checked after each plugin update | a broken dependency helper once made every hook take over 2 s while the vendor doctor reported OK |

## Permission rule paths

The two lists anchor paths differently
([permissions](https://code.claude.com/docs/en/permissions),
[sandbox path prefixes](https://code.claude.com/docs/en/settings-reference)):

| Prefix | `permissions.deny` `Read(...)` | `sandbox.filesystem.denyRead` |
|---|---|---|
| `//path` | absolute | absolute |
| `/path` | relative to the settings source: `~/.claude/path` in user settings | absolute |
| `~/path` | home | home |
| `path`, `./path` | relative to the current directory | relative to `~/.claude` in user settings |

So `Read(/srv/app/.env)` in `~/.claude/settings.json` protects `~/.claude/srv/app/.env`, not the
file you meant. Write absolute secret paths as `Read(//srv/app/.env)`. The Codex installer follows the
same rules when it mirrors the lists.
