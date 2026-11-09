# Troubleshooting

English | [Русский](TROUBLESHOOTING.ru.md)

| Problem | Symptom | Fix |
|---|---|---|
| Codex asks to review hooks after the stack moved | start screen "Hooks need review: 1 hook is new or changed" | the RTK hook command changed; Codex trusts a hook by the hash of its command and its position in `hooks.json`. Since 0.2.1 the command goes through the skill link `~/.agents/skills/token-stack`, so moving the repository no longer changes it. After an upgrade from an older version choose "Trust all and continue" once after checking `~/.codex/hooks.json`; an unattended worker waits on this screen |
| `codex sandbox` fails inside a Codex session | `error building bubblewrap command: app-server socket directory must be a user-owned directory with mode 0700`, while the same command passes in an ordinary shell | the check ran inside Codex's own sandbox; run `manage.py doctor` and the Codex tests from a normal terminal, not from a Codex tool call |
| OpenCode global instructions do not load | rules from `instructions` of `~/.config/opencode/opencode.json` are missing in sessions started in other folders | relative `instructions` paths resolve from the working directory, not the config directory; use an absolute path |
| Codex permission profile hides the Codex binary | every shell command fails with `bwrap: execvp <home>/.codex/packages/.../codex: No such file or directory`; the agent stops without a result | do not deny `":root"` in the profile; deny only secret paths, or allow reading the Codex installation. Check: `codex sandbox -- /bin/true`. Do not "fix" it with `-s workspace-write`: the legacy mode replaces the profile and opens every file for reading |
| Claude `Read(/abs/path)` deny rule does not protect the file | the file stays readable by Claude's Read tool although a deny rule names it | in permission rules a single leading `/` is relative to the settings source (`~/.claude` for user settings); write `Read(//abs/path)`. In `sandbox.filesystem.denyRead` a single `/` is absolute, so the two lists need different spellings of the same path |
| CBM installer or updater configures every agent it finds | duplicate hooks, a global MCP registration next to the project one, a large block in `AGENTS.md` | after `install` or `update` check every agent; `/stack normalize` (Claude), `manage.py install` (Codex). If CBM is attached per project, never run `codebase-memory-mcp install` |
| Caveman hooks registered twice | the Caveman rules block arrives twice at start and on every message | remove the standalone installer's hooks from `settings.json`; the plugin registers its own |
| One MCP server declared in several files | duplicate tools, a larger schema | keep one source (`~/.claude.json`, `~/.claude/.mcp.json`, the project `.mcp.json` or the plugin) |
| context-mode hooks take more than 2 s | delay on every tool call; `/ctx-doctor` still shows `[OK]` | cause: the dependency helper runs `npm install better-sqlite3` on every hook call, the install fails (`Cannot read properties of null (reading 'edgesOut')`) and the error is swallowed. Measure hook time after every plugin update (budget about 100 ms). A hand-made `node_modules` in the plugin cache is lost on update and may remove other plugin dependencies (`Cannot find module 'turndown'` in `ctx_fetch_and_index` was observed); prefer reinstalling the plugin and reporting upstream |
| CBM gate hook in a project without a graph | about 1.5 s on every Grep and Glob | early exit in `~/.claude/hooks/cbm-code-discovery-gate` when the project has no CBM: [agents/claude-code/hooks/cbm-gate-early-exit.sh](../agents/claude-code/hooks/cbm-gate-early-exit.sh) |
| Headroom with a SOCKS proxy in the environment | service exits with `ImportError: Using SOCKS proxy, but the 'socksio' package is not installed` | install and update with `uv tool install 'headroom-ai[proxy]' --with socksio --force`; `uv tool upgrade` drops the extras |
| Headroom turned off by deleting `ANTHROPIC_BASE_URL` | the agent keeps calling the stopped proxy (`ConnectionRefused` or a silent hang) because the variable is still set in the shell | set `ANTHROPIC_BASE_URL=https://api.anthropic.com` explicitly instead of deleting it |
| Updates or indexing from two agents at once | broken or conflicting shared CBM cache | update the shared binary and index a project from one agent at a time; never delete the cache as a fix |
| Codex commands get `Operation not permitted` on a local Unix socket (`hc`, Docker) | `hc` then tries to start a core and fails on systemd or a read-only file system | the permission profile has the network off; reinstall the stack (`workspace-only` turns it on), restart Codex, check `codex sandbox -- hc ls` |
| RTK rewrites `rg --files` wrongly | the command fails or searches instead of listing | old RTK (0.42.4) rewrote it to `rtk grep --files`; check `rtk hook check 'rg --files'`, `manage.py doctor` checks it too |
| context-mode installed by hand from a tarball | the plugin folder disappears | Claude Code deletes unknown folders in the plugin cache; install and update through `claude plugin` |

Checks after an installation:

```bash
rtk --version && rtk gain
rtk hook check 'rg --files'
codebase-memory-mcp --version
codex sandbox -- /bin/true
curl -s http://127.0.0.1:8787/livez      # Headroom, only if it is on: {"alive":true}
```
