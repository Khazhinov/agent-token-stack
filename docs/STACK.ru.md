# Стек

[English](STACK.md) | Русский

## 1. Принцип

Экономия достигается на независимых уровнях, поэтому инструменты устанавливаются по одному, и каждый
можно выключить отдельно.

| Уровень | Что сокращается | Инструмент |
|---|---|---|
| Источник данных | код, который агент читает при исследовании проекта | codebase-memory-mcp (CBM) |
| Вывод оболочки | вывод `git`, тестов, сборки, `grep`, журналов | RTK |
| Выводы инструментов в контексте | крупные выводы остаются в песочнице, в контекст попадает выжимка | context-mode |
| Трафик к провайдеру | сжатие запроса целиком перед API | Headroom |
| Ответы модели | объём прозы в ответах агента | Caveman |
| Генерируемый код | объём кода за счёт отказа от избыточного проектирования | Ponytail |
| Наблюдение | замер потерь до любого автоматического сокращения | TokenEconomizer |

Ponytail не является инструментом экономии токенов в узком смысле: он сокращает объём кода и входит
в стек как политика разработки.

## 2. Состав и совместимость

Проценты экономии - заявления разработчиков, зависят от характера работы; репозиторий не выдаёт их
за измеренные факты.

| Инструмент | Репозиторий | Заявленная экономия | Механизм | Особенности совместимости |
|---|---|---|---|---|
| CBM | [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) | до 99% на исследовании кода | MCP-сервер с графом знаний кода и режимом CLI | любой MCP-клиент; установщик настраивает около 40 сред сразу (раздел 4) |
| RTK | [rtk-ai/rtk](https://github.com/rtk-ai/rtk) | 60-90% на выводе CLI | hook, переписывающий команды в `rtk <cmd>` | только среды с перехватом команд (hook или плагин); в остальных - правило в инструкциях |
| context-mode | [mksglu/context-mode](https://github.com/mksglu/context-mode) | до 98% на крупных выводах | MCP-сервер песочницы и hooks | полный режим в Claude Code, Codex CLI, Cursor, OpenCode, Gemini CLI, Copilot и других; Node.js >= 22.5 или Bun |
| Headroom | [chopratejas/headroom](https://github.com/chopratejas/headroom) | 47-92% на трафике | локальный прокси между агентом и провайдером | `headroom wrap <agent>` для Claude Code, Codex, OpenCode и других; меняет маршрут к провайдеру и авторизацию |
| Caveman | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) | 50-75% на ответах | правила стиля ответа (скилл или плагин) | скилл - более 30 сред; плагин с hooks и строкой состояния - Claude Code; плагин для OpenCode |
| Ponytail | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | не цель; меньше кода | «лестница» минимальной реализации | плагин с hooks: Claude Code, Codex, Copilot CLI, OpenCode, Gemini CLI, Cursor; только правила - любая среда с `AGENTS.md` |
| TokenEconomizer | [microsoft/TokenEconomizer](https://github.com/microsoft/TokenEconomizer/tree/main/plugin) | зависит от механизма | плагин: защита от зацикливания, предложения по отключению инструментов, микроскиллы | плагины Claude Code и Codex используют общий `~/.tokeneconomizer/config.json` |

## 3. Подключение по средам

| Инструмент | Claude Code | Codex CLI | OpenCode |
|---|---|---|---|
| CBM | `.mcp.json` в каждом проекте с кодом | один глобальный `[mcp_servers.codebase-memory]` со списком `enabled_tools` | `mcp` в `opencode.json` проекта |
| RTK | hook `PreToolUse` `rtk hook claude` | hook `PreToolUse` через адаптер (`rtk-codex-hook.py`) | плагин `rtk.ts` (`rtk init -g --opencode`) |
| context-mode | плагин `context-mode@context-mode` | не используется: нативные `tool_output_token_limit`, `project_doc_max_bytes`, компактизация | npm-плагин `context-mode` |
| Headroom | `ANTHROPIC_BASE_URL` на прокси, по умолчанию выключен | не используется | `headroom wrap opencode`, по умолчанию выключен |
| Caveman | плагин `caveman@caveman` | не используется (глобальные правила и так компактны) | плагин из `src/plugins/opencode` |
| Ponytail | плагин `ponytail@ponytail` | компактные правила в глобальном `AGENTS.md` | плагин `@dietrichgebert/ponytail` |
| TokenEconomizer | плагин, `shadow=true` | плагин, `shadow=true` | не используется |
| Права | `permissions.deny` и `sandbox.filesystem.denyRead` для секретов, auto mode | профиль `workspace-only`, повторяющий запреты чтения Claude, сеть включена, `auto_review` | по умолчанию |

Установленные плагины и MCP-серверы вступают в силу после перезапуска сессии.

### 3.1. CBM на уровне проекта (Claude Code)

Глобальная регистрация MCP-сервера загружает схемы всех его инструментов в каждую сессию, в том числе
в каталоги без кода. Claude Code получает CBM файлом `.mcp.json` в корне каждого проекта с кодом:

```json
{
  "mcpServers": {
    "codebase-memory-mcp": {
      "command": "codebase-memory-mcp"
    }
  }
}
```

Команду можно обернуть в `caveman-shrink`, который сжимает вывод инструментов:
`"command": "node", "args": ["<caveman>/src/mcp-servers/caveman-shrink/index.js", "<путь к codebase-memory-mcp>"]`.
После подключения агент проверяет `index_status` и при отсутствии индекса вызывает `index_repository`.
Без MCP те же инструменты вызываются через `codebase-memory-mcp cli <tool> '<json>'`.

Признак для агента: в проекте есть код, но инструментов `mcp__codebase-memory-mcp__*` нет - граф к
проекту не подключён. Создать `.mcp.json` и попросить человека перезапустить сессию.

### 3.2. Codex: нативные лимиты и список инструментов

В Codex роль context-mode выполняют нативные механизмы. Блоки ведёт [agents/codex](../agents/codex/README.ru.md):

```toml
tool_output_token_limit = 10000
project_doc_max_bytes = 16384

[features]
hooks = true

[mcp_servers.codebase-memory]
command = "/absolute/path/to/codebase-memory-mcp"
enabled = true
startup_timeout_sec = 20
tool_timeout_sec = 120
enabled_tools = ["index_status", "index_repository", "detect_changes", "search_graph", "get_architecture", "trace_path", "get_code_snippet", "search_code"]
```

`enabled_tools` ограничивает число схем инструментов, загружаемых в контекст.

## 4. Общая машина

Несколько агентов на одной машине одно разделяют, а другое разделять не должны.

| Объект | Владелец | Правило |
|---|---|---|
| `~/.claude/**`, `~/.claude.json` | часть Claude | Codex и OpenCode только читают |
| `~/.codex/**`, `~/.agents/skills/token-stack` | часть Codex | менять через `manage.py`, не вручную из другого агента |
| `~/.config/opencode/**` | часть OpenCode | менять через её установщик |
| `~/.local/bin/rtk`, `~/.local/bin/codebase-memory-mcp` | общие | одна версия на машину; pin и SHA-256 в `BINARY_SPECS` файла `manage.py`; обновляет только один процесс |
| `~/.cache/codebase-memory-mcp` | общий | индексы и состояние демона; не удалять; не индексировать один проект из двух агентов одновременно |
| `~/.tokeneconomizer/config.json` | общий | меняется только согласованно для всех агентов; каждый агент переключает только свой плагин |
| Headroom, context-mode, Caveman | у каждого агента свои | не добавлять их провайдер, env, hooks или MCP в конфигурацию другого агента |
| Ponytail | у каждого агента свой | Claude Code и OpenCode: плагин; Codex: краткие правила в `AGENTS.md`. Плагин в Codex не устанавливать: его hooks дублируют эти правила |

Переключатели независимы: выключение RTK у Claude не выключает его у Codex, и наоборот. Общими
остаются только бинарники и данные индексов.

Запрещено:

1. Вторые копии RTK или CBM внутри `~/.claude`, `~/.codex` или проекта.
2. `codebase-memory-mcp install` или `update` для обновления: команда находит всех агентов и дописывает
   им hooks, skills, инструкции и дубли MCP.
3. Удаление `~/.cache/codebase-memory-mcp`, `_config.db` или `*.db` как способ обновления.
4. Два updater'а или два `index_repository` для одного проекта одновременно.

Согласованное обновление RTK или CBM:

1. Зафиксировать состояние: `toggle.py status`, `manage.py status`, `rtk --version`, `codebase-memory-mcp --version`.
2. Убедиться, что другой агент не обновляет и не индексирует. Поднять pin и SHA-256 в `BINARY_SPECS`
   (по официальному релизу), выполнить `manage.py install` и `manage.py doctor`.
3. После любого стороннего установщика восстановить обе управляемые конфигурации: `toggle.py normalize`,
   `manage.py install`, `manage.py doctor`.
4. Перезапустить все MCP-клиенты, чтобы они загрузили новый процесс CBM.
5. Повторить оба status; проверить проект через `index_status`. Переиндексировать только отсутствующий
   или несовместимый индекс, по одному проекту.

## 5. Правила для файла инструкций агента

Блок копируется в `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` или аналог; строки об отсутствующих инструментах
удаляются. Вариант для Codex - [agents/codex/AGENTS.md](../agents/codex/AGENTS.md), для Claude -
[agents/claude-code/RULES.md](../agents/claude-code/RULES.md).

```markdown
## Context economy

- Start code exploration with codebase-memory-mcp: `index_status`, then `search_graph`,
  `get_architecture`, `trace_path`, `get_code_snippet`. Grep and file reads confirm details and cover
  files without code. A missing index does not stop the task.
- Run noisy commands through RTK (`rtk git`, `rtk test`, `rtk grep`, `rtk log`, `rtk json`); the hook
  rewrites suitable commands. Do not use RTK when the full verbatim output is needed.
- Do not keep outputs of several hundred lines in context: process them in the context-mode sandbox
  (`ctx_execute`, `ctx_batch_execute`) and print only the result.
- Do not preload references. Keep the instruction file short, narrow rules in nested files,
  repeatable processes in skills.
- Before compaction record open decisions, verified facts and changed files.
```

## 6. Режимы

Инструменты, меняющие текст ответа (Caveman, context-mode, Ponytail), мешают работе с документами:
ответы становятся фрагментарными, выводы сокращаются. Инструменты сокращения трафика (RTK, Headroom,
CBM) на содержание ответов не влияют.

| Режим | Включено | Выключено |
|---|---|---|
| dev | всё, кроме Headroom | Headroom |
| doc | RTK, CBM | Caveman, context-mode, Ponytail, Headroom |

Claude Code: `/stack mode doc|dev`. OpenCode: `/caveman off`, `/ponytail off` на сессию или
`CAVEMAN_DEFAULT_MODE=off PONYTAIL_DEFAULT_MODE=off`. Codex хранит компактные правила в `AGENTS.md`,
плагина стиля ответов для переключения у него нет.

Переключатель для другой среды должен иметь: `status`, `mode dev|doc`, `on|off <tool|all>`;
переключение плагинов штатным флагом среды; сохранение hooks и MCP в stash при выключении и
восстановление из него при включении; `normalize`, удаляющий дубли после сторонних установщиков;
пометки о перезапуске в `status`; отсутствие влияния на конфигурацию другого агента.

## 7. Проверенные версии

Снимок на 2026-11-03, Linux (WSL2).

| Компонент | Версия |
|---|---|
| Claude Code | 2.1.316 |
| Codex CLI | 0.166.0 |
| OpenCode | 1.19.5 |
| RTK | 0.49.0 |
| codebase-memory-mcp | 0.12.1 |
| context-mode (плагин Claude) | 1.0.169 на момент замера 2026-09-21; текущая версия требует уточнения |
| Caveman (плагин OpenCode) | 2.7.0 |
| Ponytail | 4.10.0 (правила Codex), 5.3.3 (плагин OpenCode) |
| TokenEconomizer | 0.1.0 |
| Node.js | 22.22.0 |

Фактическая версия общего инструмента - то, что сообщает его бинарник, а не запись в документе.
