---
name: stack
description: "Token optimization stack control for Claude Code. Turn tools on or off: rtk, headroom, cbm, context-mode, caveman, ponytail, te (TokenEconomizer). Synonyms: /stack status, /stack off headroom, /stack on all, /stack mode doc, /stack update, /stack normalize."
---

# Skill: stack - token optimization stack control

`/stack` without arguments: run at once

```
python3 ~/.claude/skills/stack/toggle.py status
```

Print the table to the user verbatim. Add nothing unless the user asked a question.

## Commands

| User intent | Command |
|---|---|
| Show status | `python3 ~/.claude/skills/stack/toggle.py status` |
| Documents mode | `python3 ~/.claude/skills/stack/toggle.py mode doc` |
| Development mode | `python3 ~/.claude/skills/stack/toggle.py mode dev` |
| Turn a tool off | `python3 ~/.claude/skills/stack/toggle.py off <tool>` |
| Turn a tool on | `python3 ~/.claude/skills/stack/toggle.py on <tool>` |
| Turn everything off | `python3 ~/.claude/skills/stack/toggle.py off all` |
| Turn everything on | `python3 ~/.claude/skills/stack/toggle.py on all` |
| Check for updates | `python3 ~/.claude/skills/stack/toggle.py update` |
| Apply updates | `python3 ~/.claude/skills/stack/toggle.py update apply [tool\|all]` |
| Normalize the configuration | `python3 ~/.claude/skills/stack/toggle.py normalize` |

`<tool>` is one of `rtk`, `headroom`, `cbm`, `context-mode`, `caveman`, `ponytail`, `te`.

The status shows no savings percentages: they were not measured on this machine. Vendor claims are collected in `docs/STACK.md` of the stack repository. `rtk` and `te` are experimental.

`normalize` is idempotent: it removes duplicate hooks in `~/.claude/settings.json`, hooks of the standalone Caveman installer (they duplicate the plugin's hooks), and global MCP registrations of `codebase-memory-mcp` and `context-mode` in `~/.claude.json` and `~/.claude/.mcp.json`. It runs automatically on `mode` and after `update apply cbm`; run it by hand after any third-party installer.

## Modes

**doc** - documents mode: turns off `caveman` (answer style), `context-mode` (output summarization) and `ponytail` (minimal code rules). Claude answers in full sentences and does not shorten tool output.

**dev** - development mode: turns on the full stack (`rtk`, `cbm`, `context-mode`, `caveman`, `ponytail`). It does not turn on `headroom`; Headroom is turned on only by an explicit `on headroom`.

Modes do not touch `te`: only `on te` / `off te` (and `on|off all`).

## Command: stack update

### Coordination with other agents on the same machine

RTK and CBM binaries and the CBM index cache are shared with Codex and other agents. Before `update apply rtk`, `update apply cbm` or `update apply all` read the "Shared machine" section of `docs/STACK.md` in the stack repository. Never update a shared binary from two agents at once.

The target CBM version is the pin and SHA-256 in `BINARY_SPECS` of `agents/codex/skills/token-stack/scripts/manage.py` in the stack repository. Claude does not download CBM itself and never runs `codebase-memory-mcp update` or `codebase-memory-mcp install` (the latter rewrites the configuration of every agent it finds).

`update apply cbm`:
- installed version not below the pin: changes nothing and reports that the pin is raised in the Codex part (pin + SHA-256, then `manage.py install` and `doctor`), after which `normalize` runs here;
- installed version below the pin: if no other updater runs, calls `manage.py bootstrap` (downloads the pinned build and checks SHA-256; RTK is raised to its pin too), then `normalize`.

`update apply all` skips the shared `rtk` and `cbm`: they are updated only by an explicit `update apply rtk|cbm`.

Never delete `~/.cache/codebase-memory-mcp` or the indexes for a "clean reinstall" without an explicit request. Switching Claude-only components (`headroom`, `context-mode`, `caveman`, `ponytail`) must not change `~/.codex`.

**Mandatory order:**

### Step 1. Check versions (current session)
Run `python3 ~/.claude/skills/stack/toggle.py update` and show the table.

### Step 2. Prepare the update
Always, even if everything seems to work:

1. Ask the user to run `/stack off all` in this session. Make sure every tool is OFF. "Restart Claude Code" marks are expected.
2. Ask the user to restart Claude Code. Running MCP servers (context-mode, cbm) hold processes; replacing files under them can fail or not take effect.
3. In the new session the user runs `/stack update apply all`, or `/stack update apply <tool>` for one tool.

### Step 3. After the update
1. Run `/stack mode dev` to turn the stack back on (`on all` would also turn on `headroom`).
2. Restart Claude Code again so the new MCP server versions load.
3. In the final session run `/stack` and check that every tool except `headroom` is ON.
4. Run `/stack update` and check that the versions changed.

### Exception
`headroom` and `markitdown` updates need no session restart: Headroom is a systemd service reloaded in place, markitdown is a separate CLI, not an MCP server.

## Rules

After every change run `status` and print the resulting table.

If the output contains `(restart Claude Code)`, tell the user the change takes effect after a session restart.

`headroom` applies to new Claude Code sessions and new terminals. `off headroom` turns it off completely: `systemctl --user disable --now headroom-proxy`, `ANTHROPIC_BASE_URL` in `settings.json` -> `env` replaced with `https://api.anthropic.com`, the Headroom block removed from `~/.bashrc`, Headroom mentions removed from `settings.json` -> `autoMode.environment` (the original lines go to the stash). `on headroom` restores all of it and runs `enable --now`. Any leftover counts as ON, so a repeated `off headroom` finishes a partial shutdown.

A stash in the status line is normal: it lists tools whose configuration is saved for restoring.

---

## Reference: locations and installation

### RTK

| Parameter | Value |
|---|---|
| Binary | `~/.local/bin/rtk` |
| Repository | https://github.com/rtk-ai/rtk |
| Installation | download `rtk-x86_64-unknown-linux-musl.tar.gz` from GitHub Releases, unpack, replace the binary |
| Configuration | `~/.claude/settings.json` -> `hooks.PreToolUse` -> matcher `Bash`, command `~/.local/bin/rtk hook claude` (absolute path) |
| Version | `rtk --version` |
| Update check | `https://api.github.com/repos/rtk-ai/rtk/releases/latest` -> `.tag_name` |
| Status | experimental |
| Update | only explicitly with `toggle.py update apply rtk` (not part of `update apply all`); shared with Codex |

### Headroom

| Parameter | Value |
|---|---|
| Binary | `~/.local/bin/headroom` (via `uv tool`) |
| Python package | `headroom-ai` on PyPI |
| Repository | https://github.com/chopratejas/headroom |
| Installation | `uv tool install headroom-ai`, systemd user service `headroom-proxy` |
| Service | `~/.config/systemd/user/headroom-proxy.service` (ExecStart: `headroom proxy --port 8787`) |
| Environment | `ANTHROPIC_BASE_URL=http://127.0.0.1:8787` in `~/.claude/settings.json` -> `env` and in `~/.bashrc` (only while Headroom is on) |
| Check | `curl -s http://127.0.0.1:8787/livez` -> `{"alive":true}` |
| Version | `headroom --version` |
| Update check | `https://pypi.org/pypi/headroom-ai/json` -> `.info.version` |
| Update | `uv tool install 'headroom-ai[proxy]' --with socksio --force && systemctl --user restart headroom-proxy` |
| SOCKS proxy in the environment | with `ALL_PROXY=socks5h://...` set, headroom >= 0.26 needs `socksio`, which it does not depend on; without it the service exits with `ImportError: Using SOCKS proxy, but the 'socksio' package is not installed`. Always install and update with `[proxy] --with socksio`; `uv tool upgrade headroom-ai` drops the extras |
| `ANTHROPIC_BASE_URL` on off | `off headroom` sets `https://api.anthropic.com` in `settings.json` instead of deleting the key. A terminal opened before the shutdown keeps `ANTHROPIC_BASE_URL=http://127.0.0.1:8787`; without the explicit override Claude Code started from it hangs on the stopped proxy. Never delete the key |

### Codebase Memory MCP (cbm)

| Parameter | Value |
|---|---|
| Binary | `~/.local/bin/codebase-memory-mcp` (shared with other agents) |
| Repository | https://github.com/DeusData/codebase-memory-mcp |
| MCP registration | **per project only**: `.mcp.json` in the root of a project with code (template in `docs/STACK.md`). Global registration in `~/.claude.json` and `~/.claude/.mcp.json` is forbidden and removed by `normalize` |
| Hooks (`on/off cbm`) | `~/.claude/settings.json` -> `hooks.PreToolUse` matcher `Grep\|Glob` (`cbm-code-discovery-gate`, adds to the result, never blocks), `hooks.SessionStart` (`cbm-session-reminder`). Scripts: `agents/claude-code/hooks/` of the stack repository; `on cbm` skips a hook whose script is missing |
| Index cache | `~/.cache/codebase-memory-mcp` (shared; never delete) |
| Version | `codebase-memory-mcp --version` |
| Update check | `https://api.github.com/repos/DeusData/codebase-memory-mcp/releases/latest` -> `.tag_name` |
| Target version | the Codex pin: `BINARY_SPECS` in `manage.py` |
| Update | raise the pin and SHA-256 in `manage.py`, run `manage.py install` and `doctor`, then `toggle.py normalize` here; `toggle.py update apply cbm` only catches up with the pin through `manage.py bootstrap`. Restart Claude Code and Codex |
| Forbidden | `codebase-memory-mcp update`, `codebase-memory-mcp install` (adds hooks and a global MCP to every agent) |

### context-mode

| Parameter | Value |
|---|---|
| Installation | plugin `context-mode@context-mode` (marketplace `mksglu/context-mode`) |
| Plugin folder | `~/.claude/plugins/cache/context-mode/context-mode/<version>/` |
| MCP and hooks | declared by the plugin itself; a global `mcpServers.context-mode` in `~/.claude.json` duplicates the server and is removed by `normalize` |
| Switch | `settings.json` -> `enabledPlugins["context-mode@context-mode"]` + optional self-heal hook `~/.claude/hooks/context-mode-cache-heal.mjs` (SessionStart), registered only if the script exists |
| Version | `installed_plugins.json` -> `plugins["context-mode@context-mode"][0].version`; no `installPath` means BROKEN |
| Update check | `https://api.github.com/repos/mksglu/context-mode/releases/latest` -> `.tag_name` |
| Update and reinstall | `toggle.py update apply context-mode` (`claude plugin marketplace update` + `claude plugin update` or `install`), restart Claude Code. A hand-unpacked tarball in `cache/context-mode/<version>` does not work: Claude Code deletes such a folder as unknown |

### Caveman

| Parameter | Value |
|---|---|
| Installation | plugin `caveman@caveman` (marketplace `JuliusBrussee/caveman`) |
| Plugin folder | `~/.claude/plugins/cache/caveman/caveman/<version>/` |
| Hooks | declared by the plugin (`SessionStart`, `UserPromptSubmit`). Copies in `settings.json` pointing to `~/.claude/hooks/caveman-activate.js` and `caveman-mode-tracker.js` come from the standalone installer, duplicate the plugin and are removed by `normalize` |
| Switch | `settings.json` -> `enabledPlugins["caveman@caveman"]` |
| Statusline | `~/.claude/hooks/caveman-statusline.sh` |
| MCP shrink | `~/.claude/plugins/marketplaces/caveman/src/mcp-servers/caveman-shrink/index.js` (wraps CBM in project `.mcp.json`) |
| Version | `installed_plugins.json` -> `plugins["caveman@caveman"][0].gitCommitSha` (first 12 characters) |
| Update check | `https://api.github.com/repos/JuliusBrussee/caveman/commits/main` -> `.sha[:12]` + `.commit.author.date` |
| Update | `toggle.py update apply caveman`, restart Claude Code |

### Ponytail

| Parameter | Value |
|---|---|
| Purpose | minimal code rules against over-engineering (YAGNI -> reuse -> stdlib -> platform -> installed dependency -> minimal new code) |
| Installation | plugin `ponytail@ponytail` (marketplace `DietrichGebert/ponytail`), default level full |
| Plugin folder | `~/.claude/plugins/cache/ponytail/ponytail/<version>/` |
| Hooks | declared by the plugin: `SessionStart` (rules into the session), `SubagentStart` (rules into every subagent), `UserPromptSubmit` (`/ponytail lite\|full\|ultra\|off`) |
| State | flag `~/.claude/.ponytail-active`; default level from `PONYTAIL_DEFAULT_MODE` or `~/.config/ponytail/config.json` |
| Commands | `/ponytail-review`, `/ponytail-audit`, `/ponytail-debt`, `/ponytail-gain`, `/ponytail-help` |
| Switch | `settings.json` -> `enabledPlugins["ponytail@ponytail"]` |
| Version | `installed_plugins.json` -> `plugins["ponytail@ponytail"][0].version` |
| Update check | `https://api.github.com/repos/DietrichGebert/ponytail/releases/latest` -> `.tag_name` |
| Update | `toggle.py update apply ponytail`, restart Claude Code |
| Codex | the plugin is not installed; compact rules live in the Codex `AGENTS.md` |

### TokenEconomizer (te)

| Parameter | Value |
|---|---|
| Status | experimental; observation only |
| Installation | plugin `tokeneconomizer@tokeneconomizer` (marketplace `microsoft/TokenEconomizer`), user scope |
| Plugin folder | `~/.claude/plugins/cache/tokeneconomizer/tokeneconomizer/<version>/` |
| Hooks | declared by the plugin: `SessionStart`, `UserPromptSubmit`, `PostToolUse`, `PostToolUseFailure`, `Stop`, `SessionEnd` (`scripts/te-hook`, about 60 ms per call) |
| Shared configuration | `~/.tokeneconomizer/config.json` (`shadow=true`, `toolprune=propose`) is shared with Codex; `toggle.py` only reads it |
| Compatibility | with `shadow=true` it adds no context, writes no deny lists or notices, so it does not overlap with context-mode, Caveman and Ponytail. The loop guard judge may call `claude -p --model haiku` on a turn that looks like a loop before the shadow check |
| Switch | `settings.json` -> `enabledPlugins["tokeneconomizer@tokeneconomizer"]`; `TE_DISABLE=1` and `enabled=false` in the shared file are not used (the latter turns TE off in Codex too) |
| Version | `installed_plugins.json` -> `plugins["tokeneconomizer@tokeneconomizer"][0].version` |
| Update check | `https://raw.githubusercontent.com/microsoft/TokenEconomizer/main/plugin/.claude-plugin/plugin.json` -> `.version` |
| Update | `toggle.py update apply te`, restart Claude Code |
| Codex | a separate Codex plugin, switched by `manage.py on\|off te` |

### markitdown

| Parameter | Value |
|---|---|
| Binary | `~/.local/bin/markitdown` (via `uv tool`) |
| Python package | `markitdown[all]` on PyPI (Microsoft MarkItDown) |
| Installation | `uv tool install 'markitdown[all]>=0.1.7' --with 'azure-ai-contentunderstanding>=1.2.0b1' --prerelease=if-necessary-or-explicit` (0.1.7 depends on a pre-release of `azure-ai-contentunderstanding`; without it the resolver stays on 0.1.5) |
| Version | `markitdown --version` (ignore ffmpeg warnings) |
| Update check | `https://pypi.org/pypi/markitdown/json` -> `.info.version` |
| Update | `uv tool upgrade markitdown` (uv keeps the install options in its receipt) |
| Note | not part of the token stack switched by `toggle.py`: a separate document reading tool |

---

## Documents

Tools that change answer text: `caveman` (style), `context-mode` (summarization), `ponytail` (minimal code rules). For formal documents turn them off with `python3 ~/.claude/skills/stack/toggle.py mode doc`. Traffic tools (`rtk`, `headroom`, `cbm`) do not change answer content.
