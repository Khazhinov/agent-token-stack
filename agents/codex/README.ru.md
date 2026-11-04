# Codex CLI

[English](README.md) | Русский

## Состав

| Путь | Назначение |
|---|---|
| `install.sh` | выполняет `manage.py install` и `manage.py doctor` |
| `skills/token-stack/` | скилл `token-stack`; `scripts/manage.py` устанавливает, переключает и проверяет стек; `scripts/rtk-codex-hook.py` адаптирует hook RTK к Codex |
| `AGENTS.md` | публичные глобальные правила; связываются или копируются в `~/.codex/AGENTS.md` |
| `config.fragment.toml` | справочная копия управляемых блоков `~/.codex/config.toml` |
| `tests/` | тесты установщика во временном HOME |

## Установка

```bash
./agents/codex/install.sh
python3 agents/codex/skills/token-stack/scripts/manage.py status
```

Установщик идемпотентен. Он:

- скачивает закреплённые RTK и CBM для Linux x86_64 при отсутствии или устаревшей версии, проверяет
  SHA-256 и устанавливает в общий `~/.local/bin`; более новые версии не понижает;
- связывает `~/.codex/AGENTS.md` с `AGENTS.md`, а при наличии `local/codex/AGENTS.md` записывает
  публичные правила и следом локальные;
- связывает `~/.agents/skills/token-stack` со скиллом;
- объединяет управляемые блоки с `~/.codex/config.toml`, сохраняя модель, доверие к проектам и прочие
  настройки;
- строит профиль прав по запретам чтения Claude Code;
- добавляет hook RTK `PreToolUse` в `~/.codex/hooks.json`, сохраняя чужие hooks;
- удаляет дублирующую регистрацию CBM, которую может добавить его официальный updater.

Существующие глобальные файлы один раз сохраняются с суффиксом `.pre-token-stack`.

## Переключение

```bash
python3 agents/codex/skills/token-stack/scripts/manage.py on|off rtk|cbm|native|te|all
python3 agents/codex/skills/token-stack/scripts/manage.py doctor
```

| Компонент | Реализация в Codex | Общее с Claude |
|---|---|---|
| `rtk` | `PreToolUse` -> адаптер -> `rtk hook claude`; адаптер добавляет `permissionDecision: allow` | один `~/.local/bin/rtk` |
| `cbm` | глобальный MCP со списком разрешённых инструментов; CLI остаётся дешёвым резервом | один бинарник и один кэш индексов |
| `native` | `tool_output_token_limit`, `project_doc_max_bytes`, компактизация и `/compact` | только Codex |
| `te` | плагин TokenEconomizer, переключается отдельно от Claude | настройки механизмов и данные общие, активация плагина нет |

`off all` выключает технические компоненты, но сохраняет глобальные правила и Ponytail.

## Почему настроено так

| Выбор | Причина |
|---|---|
| права как у Claude Code | одна политика для всех агентов; профиль запрещает только пути, закрытые для чтения Claude, запись в рабочей папке, остальное оценивает `auto_review` |
| нет запрета `":root"` | Codex запускает собственный бинарник внутри bwrap; если его скрыть, ломается любая команда оболочки (`bwrap: execvp .../codex`); `doctor` проверяет `codex sandbox -- /bin/true` |
| нет `-s` в командах агентов | старый режим песочницы заменяет профиль и открывает чтение всех файлов |
| нативные лимиты вместо context-mode | закрывают роль без второго фильтра |
| Ponytail правилами в `AGENTS.md`, без плагина | hooks плагина дублировали бы постоянные правила |
| без Headroom | меняет маршрут к провайдеру и авторизацию |
| pin CBM и RTK с SHA-256 здесь | один источник истины для общих бинарников машины |

## Обновление CBM

Изменить версию, URL и SHA-256 в `BINARY_SPECS` файла `manage.py` по официальному релизу, выполнить
`manage.py install` и `doctor`, затем `/stack normalize` в Claude Code и перезапустить MCP-клиенты.
CBM 0.12.1 однократно перестраивает каждый старый индекс при следующей индексации; общий кэш не удалять.
