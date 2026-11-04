# OpenCode, Claude Code and Codex on one node

Read this before changing the shared optimization stack. The node runs three independent control
centers. Their machine paths are recorded in `local/` and are not published.

## Ownership

| Object | Owner | Rule |
|---|---|---|
| `~/.config/opencode/**`, `~/.opencode/opencode.json` | OpenCode part | managed by the OpenCode installer; do not edit by hand |
| `~/.claude/**`, `~/.claude.json` | Claude Code part | do not copy settings from it into OpenCode automatically |
| `~/.codex/**`, `~/.agents/skills/token-stack` | Codex part | do not edit by hand from OpenCode |
| `~/.local/bin/rtk` | shared | one version for all agents; only one process updates it |
| `~/.local/bin/codebase-memory-mcp` | shared | one build for all agents; restart MCP clients after an update |
| `~/.cache/codebase-memory-mcp` | shared | shared indexes and daemon state; never delete and never index one project in parallel |
| context-mode | per agent | a Claude Code plugin in Claude, an npm plugin in OpenCode; state is not transferred |
| Caveman, Ponytail | per agent | OpenCode uses its own plugins; mode state lives in `~/.config/opencode/.caveman-active` and `.ponytail-active` |

Switches are independent. Changing the OpenCode configuration must not change Claude Code or Codex.
Only binaries and index data are shared.

CBM is attached in OpenCode per project through `opencode.json` at the root of a project with code.
The OpenCode installer creates no global MCP registration; updating CBM does not require adding the
server to the global configuration.

## Prohibitions

1. Do not create second copies of RTK or CBM inside agent directories or a project.
2. Do not run `codebase-memory-mcp install` to update. It finds several agents and may add hooks,
   skills, instructions and duplicate MCP registrations at once.
3. Do not delete `~/.cache/codebase-memory-mcp`, `_config.db` or all `*.db` files as an update
   method. Migrate the index format only on an explicit request from the person.
4. Do not run two updaters or two `index_repository` runs for one project at the same time.
5. Do not add Headroom providers, environment variables or hooks to the OpenCode configuration by
   hand; use `headroom wrap opencode`.

## Coordinated update of RTK or CBM

1. Record the initial state: `rtk --version`, `codebase-memory-mcp --version`, and the status command
   of every agent on the node.
2. Make sure no other agent is updating or indexing. Update the shared binary once, through the
   single updater chosen for the machine.
3. After the updater, restore every managed configuration: the Claude `normalize` command, the Codex
   `manage.py install` command and `agents/opencode/install.sh`.
4. Restart OpenCode, Claude Code and Codex so the MCP clients load the new CBM process.
5. Repeat the checks and re-index only the missing or incompatible index, one project at a time.

## Sources of truth

- OpenCode: this directory and the `agent-token-stack` repository.
- Claude Code: `agents/claude-code`.
- Codex: `agents/codex`.
- The real version of a shared tool is what the binary reports, not what a document says.
