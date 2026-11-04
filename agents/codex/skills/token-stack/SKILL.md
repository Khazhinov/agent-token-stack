---
name: token-stack
description: "Checks, installs and switches the global Codex context economy stack: RTK, codebase-memory-mcp, TokenEconomizer, native limits and compaction, permission profile. Use for questions about tokens, context, stack status, installation, updates or turning stack components on and off."
---

# Token Stack

Status:

```bash
python3 ~/.agents/skills/token-stack/scripts/manage.py status
```

Before installing, restoring the managed configuration or changing a component, read [references/components.md](references/components.md), then run one of:

```bash
python3 ~/.agents/skills/token-stack/scripts/manage.py install
python3 ~/.agents/skills/token-stack/scripts/manage.py on rtk|cbm|native|te|all
python3 ~/.agents/skills/token-stack/scripts/manage.py off rtk|cbm|native|te|all
python3 ~/.agents/skills/token-stack/scripts/manage.py doctor
```

After a change always run `status`; after an installation or update run `doctor`. `te` switches only the Codex plugin, not the TokenEconomizer settings and not the Claude plugin. Global rules and Ponytail stay active on `off all`; only technical components are switched.

Never run `codebase-memory-mcp install` over a shared installation: it may add duplicates to Codex and Claude. To update, pin the version and SHA-256 of the official binary in `BINARY_SPECS`, then run `manage.py install`: it checks the hash and keeps the shared cache. A new Codex session is needed to load a new MCP process.
