# Codex CLI

English | [Русский](README.ru.md)

## Contents

| Path | Purpose |
|---|---|
| `install.sh` | runs `manage.py install` and `manage.py doctor` |
| `skills/token-stack/` | `token-stack` skill; `scripts/manage.py` installs, switches and checks the stack; `scripts/rtk-codex-hook.py` adapts the RTK hook to Codex |
| `AGENTS.md` | public global rules, linked or copied to `~/.codex/AGENTS.md` |
| `config.fragment.toml` | reference copy of the managed blocks of `~/.codex/config.toml` |
| `tests/` | installer tests in a temporary HOME |

## Installation

```bash
./agents/codex/install.sh
python3 agents/codex/skills/token-stack/scripts/manage.py status
```

The installer is idempotent. It:

- downloads the pinned RTK and CBM for Linux x86_64 if they are missing or older, checks SHA-256 and
  installs them into the shared `~/.local/bin`; it never downgrades;
- links `~/.codex/AGENTS.md` to `AGENTS.md`, or, when `local/codex/AGENTS.md` exists, writes the
  public rules followed by the local ones;
- links `~/.agents/skills/token-stack` to the skill;
- merges the managed blocks into `~/.codex/config.toml`, keeping the model, project trust and other
  settings;
- builds the permission profile from Claude Code's read denies;
- adds the RTK `PreToolUse` hook to `~/.codex/hooks.json`, keeping other hooks;
- removes the duplicate CBM registration its official updater may add.

Existing global files are saved once with the suffix `.pre-token-stack`.

Optional machine preferences in `local/codex/settings.json` are applied on installation:
`{"reasoning_effort":"medium","trust_all_directories":true}`. The second option installs a
standalone Codex launcher for all folders, preserving Auto-review and separate hook trust.
The native stack now compacts at 160000 tokens; model and effort stay unchanged unless explicitly
selected in that local file. `doctor` validates configuration against the installed CLI as well.
TokenEconomizer's shadow mode can still spend tokens on judge calls; switch it only after measuring.

Create `local/codex/settings.json` with `{}` to keep existing effort and launcher choices, or select:

| Key | Effect |
|---|---|
| `reasoning_effort` | Changes the global effort; project and explicit CLI overrides remain available. |
| `trust_all_directories: true` | Installs the launcher for a standalone Codex installation. |
| `read_denies` | Adds a list of private file or directory paths to the read denies. |

Auto-trust loads project-local configuration without asking for folder trust. It does not approve
new or changed hooks. The previous command is backed up as `~/.local/bin/codex.pre-token-stack`;
a future standalone update can restore its own link, so rerun this installer if needed.
Machine-specific plugin activation is not changed by installation. For a measured Codex-only
TokenEconomizer disable, use `manage.py off te`; the shared config and Claude plugin are unchanged.
Existing Codex read denies survive synchronization even when Claude no longer lists them.
Restart Codex to load the complete setup; a resumed conversation can retain its earlier effort.

## Switches

```bash
python3 agents/codex/skills/token-stack/scripts/manage.py on|off rtk|cbm|native|te|all
python3 agents/codex/skills/token-stack/scripts/manage.py doctor
```

| Component | Codex implementation | Shared with Claude |
|---|---|---|
| `rtk` | `PreToolUse` -> adapter -> `rtk hook claude`; the adapter adds `permissionDecision: allow` | one `~/.local/bin/rtk` |
| `cbm` | global MCP with a tool allow-list; the CLI stays as a cheap fallback | one binary and one index cache |
| `native` | `tool_output_token_limit`, `project_doc_max_bytes`, compaction and `/compact` | Codex only |
| `te` | TokenEconomizer plugin, switched apart from Claude | mechanism settings and data are shared, plugin activation is not |

`off all` turns off technical components but keeps the global rules and Ponytail.

## Why it is configured this way

| Choice | Reason |
|---|---|
| permissions as in Claude Code | one policy for every agent; the profile denies only Claude's read-denied paths, writes stay in the workspace, `auto_review` judges the rest |
| no `":root"` deny | Codex starts its own binary inside bwrap; hiding it breaks every shell command (`bwrap: execvp .../codex`); `doctor` checks `codex sandbox -- /bin/true` |
| no `-s` in agent commands | the legacy sandbox mode replaces the profile and opens every file for reading |
| native limits instead of context-mode | they cover the role without a second filter |
| Ponytail as rules in `AGENTS.md`, no plugin | the plugin's hooks would duplicate the permanent rules |
| no Headroom | it changes the provider route and authorization |
| CBM and RTK pinned with SHA-256 here | one source of truth for shared binaries on the machine |

## Updating CBM

Change the version, URL and SHA-256 in `BINARY_SPECS` of `manage.py` from the official release,
run `manage.py install` and `doctor`, then `/stack normalize` in Claude Code, and restart the MCP
clients. CBM 0.12.1 rebuilds each old index once on the next indexing; do not delete the shared cache.
