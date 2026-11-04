# OpenCode

[English](README.md) | Русский

## Состав

| Путь | Назначение |
|---|---|
| `install.sh` | связывает плагины стека, навык Caveman и правила стека с `~/.config/opencode`; сохраняет заменяемые файлы с суффиксом `.pre-agent-token-stack` |
| `verify.sh` | проверяет бинарники, симлинки, загруженные плагины, импорт правил и модули плагинов; запускает `local/opencode/verify.local.sh`, если он есть |
| `AGENTS.stack.md` | правила стека, подключаемые как ambient instructions через массив `instructions` глобального `opencode.json` |
| `plugins/rtk.ts` | плагин RTK в том виде, как его создаёт `rtk init -g --opencode`; делегирует `rtk rewrite` |
| `plugins/caveman/` | файлы плагина Caveman для OpenCode и LICENSE |
| `plugins/ponytail/` | файлы плагина Ponytail, команды, навыки и LICENSE |
| `skills/caveman/` | `SKILL.md` Caveman, который плагин читает при каждом запросе |
| `docs/shared-node.md` | границы владения и порядок согласованного обновления OpenCode, Claude Code и Codex |
| `docs/REPORT-2026-11-02.md` | общие выводы переноса OpenCode |
| `opencode.example.json` | часть стека в глобальном `~/.config/opencode/opencode.json`: компактизация, плагины и instructions; без глобального MCP |
| `opencode.project.example.json` | `opencode.json` для корня проекта с кодом (CBM на уровне проекта) |

## Установка

```bash
./agents/opencode/install.sh
./agents/opencode/verify.sh
```

Установщик идемпотентен. Он:

- связывает `plugins/caveman`, `plugins/ponytail`, `plugins/rtk.ts`, `skills/caveman` и
  `AGENTS.stack.md` с `~/.config/opencode`;
- один раз сохраняет заменяемый файл или симлинк с суффиксом `.pre-agent-token-stack`;
- сообщает, найдены ли `rtk` и `codebase-memory-mcp` в `PATH`.

После первой установки или обновления плагинов перезапустить OpenCode.

## Слияние части стека с глобальным конфигом

Глобальный `opencode.json` содержит и настройки машины: модели, отключённые провайдеры и плагины,
не относящиеся к стеку. Этот файл остаётся в собственном каталоге машины; заменять его примером
нельзя. Из `opencode.example.json` переносятся только ключи стека:

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

Остальные ключи глобального файла сохраняются. Указывается абсолютный путь к `AGENTS.stack.md`:
OpenCode разрешает относительные пути instructions от рабочего каталога, а не от каталога конфига.
Пути плагинов разрешаются через симлинки в `~/.config/opencode/plugins`.

CBM в глобальный файл не добавляется. Объект `mcp` из `opencode.project.example.json` переносится
в `opencode.json` каждого проекта с кодом; если файл уже есть, добавляется только объект `mcp`.
После изменения перезапустить OpenCode.

## Проверки

```bash
opencode debug info
opencode debug config
opencode mcp list
rtk rewrite "git status"
```

`opencode debug info` показывает загруженные плагины. `opencode debug config` показывает массив
`plugin` и импортированные `instructions`. `opencode mcp list` из корня проекта показывает,
подключён ли CBM; затем в сессии вызывается `index_status`.

## Почему настроено так

| Выбор | Причина |
|---|---|
| CBM на уровне проекта | глобальная регистрация загружает около 14 схем инструментов в каждую сессию, включая проекты без кода |
| файлы плагинов хранятся в репозитории | установщики разработчиков копируют файлы, дописывают блоки в `AGENTS.md` и могут добавлять записи MCP; копии в репозитории работают без сети и воспроизводимо |
| нет правил Caveman и Ponytail в `AGENTS.md` | плагины внедряют свои правила на каждом ходе; копия дублировала бы их |
| правила стека импортируются через `instructions` | глобальный `AGENTS.md` содержит только личные правила и правила вне стека, а правила стека остаются в этом репозитории |
| Headroom только через `headroom wrap opencode` | он не входит в конфигурацию OpenCode и по умолчанию выключен |

## Режимы

Caveman и Ponytail переключаются на сессию командами `/caveman off` и `/ponytail off` (или
`lite|full|ultra`). Режим документов на весь запуск:

```bash
CAVEMAN_DEFAULT_MODE=off PONYTAIL_DEFAULT_MODE=off opencode
```

Удаление строки из `plugin` и перезапуск полностью прекращают загрузку плагина.

Значения конкретной машины, имена моделей и список проектов с CBM остаются в `local/opencode/`.
