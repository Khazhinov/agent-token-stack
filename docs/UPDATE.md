# Update

English | [Русский](UPDATE.ru.md)

The repository changes; a machine set up from it follows by an explicit update. An agent does this
on request or when the person asks whether the stack is current.

## 1. Check

```bash
git -C <repo> fetch --tags
git -C <repo> log --oneline HEAD..origin/main
cat <repo>/VERSION; git -C <repo> show origin/main:VERSION
```

No new commits: the stack is current. Otherwise read the new entries of `CHANGELOG.md` and
`docs/JOURNAL.md` between the two versions and list which of them concern the agents on this machine
(`local/README.md`).

## 2. Apply

1. Tell the person what will change and in which agents; ask before anything that changes
   permissions, removes a component or restarts sessions.
2. `git -C <repo> pull --ff-only`. Local changes in `local/` stay, git ignores them.
3. Per agent on this machine:

| Agent | Command | After |
|---|---|---|
| Codex | `python3 agents/codex/skills/token-stack/scripts/manage.py install` | `manage.py doctor`, new Codex session |
| Claude Code | `/stack normalize` (the skill is a link into the repository, so it is already current) | `/stack`, restart if marked |
| OpenCode | the steps of the changed part of [agents/opencode/README.md](../agents/opencode/README.md) | `opencode debug config` |

4. Shared binaries (RTK, CBM) change only when their pin changed; follow the coordinated update in
   [STACK.md](STACK.md), section 4.

## 3. Record

Add a dated line to `local/JOURNAL.md`: versions before and after, what was applied, check results.
If the update showed a problem that any machine would meet, fix it in the public part (see
[AGENTS.md](../AGENTS.md), section 4).
