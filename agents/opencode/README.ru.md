# OpenCode

[English](README.md) | Русский

## Состав

| Путь | Назначение |
|---|---|
| `opencode.example.json` | глобальный `~/.config/opencode/opencode.json`: компактизация и плагины; без глобального MCP |
| `opencode.project.example.json` | `opencode.json` для корня проекта с кодом (CBM на уровне проекта) |
| `rtk.ts` | плагин RTK в том виде, как его создаёт `rtk init -g --opencode`; делегирует `rtk rewrite` |

## Установка

1. Хранить управляемые файлы в каталоге под контролем версий и связывать их с `~/.config/opencode`
   идемпотентным установщиком, который сохраняет резервные копии заменяемых файлов.
2. Плагины в массиве `plugin` файла `opencode.json`:
   - `context-mode` (npm) регистрирует инструменты `ctx_*`; отдельный MCP не нужен;
   - `./plugins/rtk.ts` (скопировать `rtk.ts` в `~/.config/opencode/plugins/`);
   - Caveman из `JuliusBrussee/caveman`, каталог `src/plugins/opencode` (`plugin.js`, `package.json`,
     `caveman-config.cjs`, `caveman-parse.cjs`) и его `SKILL.md` в `~/.config/opencode/skills/caveman`;
   - Ponytail из npm-пакета `@dietrichgebert/ponytail`.
3. CBM: перенести `mcp` из `opencode.project.example.json` в `opencode.json` каждого проекта с кодом;
   если файл есть, добавить только объект `mcp`. Перезапустить OpenCode.

Проверки: `opencode debug info` (плагины загружены), `opencode debug config` (массив `plugin`),
`opencode mcp list` из корня проекта, затем `index_status`; `rtk rewrite "git status"`.

## Почему настроено так

| Выбор | Причина |
|---|---|
| CBM на уровне проекта | та же причина, что в Claude Code: глобальная регистрация загружает около 14 схем инструментов в каждую сессию |
| плагины хранятся в репозитории, а не ставятся установщиками разработчиков | установщик Caveman копирует файлы, дописывает блок в `AGENTS.md` и может добавить `mcp.caveman-shrink`, выходя за управляемый набор; копии в репозитории работают без сети и воспроизводимо |
| нет разделов Caveman и Ponytail в `AGENTS.md` | плагины внедряют свои правила (около 760 и 490 слов на уровне `full`) на каждом ходе; копия в `AGENTS.md` удваивала их |
| Headroom только через `headroom wrap opencode` | не входит в конфигурацию OpenCode; по умолчанию выключен |

## Режимы

Caveman и Ponytail переключаются на сессию командами `/caveman off`, `/ponytail off` (или
`lite|full|ultra`). Режим документов на весь запуск: `CAVEMAN_DEFAULT_MODE=off PONYTAIL_DEFAULT_MODE=off opencode`.
Удаление строки из `plugin` и перезапуск полностью прекращают загрузку плагина.
