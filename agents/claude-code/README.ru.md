# Claude Code

[English](README.md) | Русский

## Состав

| Путь | Назначение |
|---|---|
| `skills/stack/` | скилл `stack`: `toggle.py` переключает стек, режимы, обновления, `normalize`; `test_toggle.py` работает во временном HOME |
| `RULES.md` | блок для глобального `~/.claude/CLAUDE.md` |
| `settings.example.json` | пример частей `~/.claude/settings.json`, на которые опирается стек: запреты чтения секретов, плагины, явный адрес API |
| `mcp.example.json` | `.mcp.json` для корня проекта с кодом (CBM на уровне проекта) |
| `hooks/cbm-gate-early-exit.sh` | шлюз CBM для Grep/Glob с ранним выходом в проектах без графа |

## Установка

```bash
ln -s "$(pwd)/agents/claude-code/skills/stack" ~/.claude/skills/stack
```

Затем:

1. Установить выбранные плагины (в Claude Code двумя отдельными сообщениями для каждого marketplace):
   `/plugin marketplace add mksglu/context-mode` + `/plugin install context-mode@context-mode`,
   `JuliusBrussee/caveman` + `caveman@caveman`, `DietrichGebert/ponytail` + `ponytail@ponytail`,
   `microsoft/TokenEconomizer` + `tokeneconomizer@tokeneconomizer`.
2. Hook RTK: `rtk init -g` или `/stack on rtk` после установки бинарника.
3. CBM: общий бинарник (закреплённая установка - в части Codex), `.mcp.json` проекта по образцу
   `mcp.example.json`, hook-шлюз из `hooks/`.
4. Добавить `RULES.md` в `~/.claude/CLAUDE.md` (копией или `@<путь к RULES.md>`).
5. `/stack normalize`, затем `/stack`. Перезапустить сессию, где помечено.

## Почему настроено так

| Выбор | Причина |
|---|---|
| CBM на уровне проекта, не глобально | глобальная регистрация загружает около 14 схем инструментов в каждую сессию, включая папки без кода |
| Caveman, Ponytail, context-mode только плагинами | вторая копия правил в `CLAUDE.md` или автономные hooks внедряют их дважды на каждом ходе |
| `normalize` после любого стороннего установщика | установщик и updater CBM добавляют глобальные MCP и дубли hooks |
| Headroom по умолчанию выключен, явный `ANTHROPIC_BASE_URL` | прокси меняет маршрут к API; удаление переменной оставляет старые терминалы на остановленном прокси |
| режимы doc и dev | инструменты, меняющие ответ, портят официальные документы |
| пути секретов и в `permissions.deny`, и в `sandbox.filesystem.denyRead` | первое закрывает инструменты Claude, второе - команды оболочки в песочнице; Codex повторяет оба списка (см. часть Codex) |
| замер задержки hooks после каждого обновления плагина | неисправный модуль зависимостей однажды сделал каждый hook дольше 2 с при OK штатной диагностики |

## Пути в правилах прав

Два списка трактуют пути по-разному
([permissions](https://code.claude.com/docs/en/permissions),
[sandbox path prefixes](https://code.claude.com/docs/en/settings-reference)):

| Префикс | `permissions.deny` `Read(...)` | `sandbox.filesystem.denyRead` |
|---|---|---|
| `//path` | абсолютный | абсолютный |
| `/path` | от источника настроек: `~/.claude/path` в пользовательских настройках | абсолютный |
| `~/path` | домашний каталог | домашний каталог |
| `path`, `./path` | от текущего каталога | от `~/.claude` в пользовательских настройках |

Поэтому `Read(/srv/app/.env)` в `~/.claude/settings.json` защищает `~/.claude/srv/app/.env`, а не
задуманный файл. Абсолютные пути секретов писать как `Read(//srv/app/.env)`. Установщик Codex следует
тем же правилам, когда повторяет списки.
