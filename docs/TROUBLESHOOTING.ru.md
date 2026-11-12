# Неисправности

[English](TROUBLESHOOTING.md) | Русский

| Проблема | Признак | Решение |
|---|---|---|
| Codex просит проверить hooks после переноса стека | экран запуска «Hooks need review: 1 hook is new or changed» | изменилась команда hook RTK; Codex доверяет hook по хэшу его команды и позиции в `hooks.json`. С версии 0.2.1 команда идёт через ссылку скилла `~/.agents/skills/token-stack`, поэтому перенос репозитория её не меняет. После обновления со старой версии один раз выбрать «Trust all and continue», проверив `~/.codex/hooks.json`; исполнитель без человека ждёт на этом экране |
| `codex sandbox` падает внутри сессии Codex | `error building bubblewrap command: app-server socket directory must be a user-owned directory with mode 0700`, хотя та же команда в обычной оболочке проходит | проверка запущена внутри песочницы самого Codex; `manage.py doctor` и тесты Codex запускать из обычного терминала, а не вызовом инструмента Codex |
| Глобальные инструкции OpenCode не загружаются | правила из `instructions` файла `~/.config/opencode/opencode.json` отсутствуют в сессиях, запущенных в других папках | относительные пути `instructions` отсчитываются от рабочего каталога, а не от каталога конфигурации; указывать абсолютный путь |
| Профиль прав Codex скрывает бинарник Codex | любая команда оболочки падает с `bwrap: execvp <home>/.codex/packages/.../codex: No such file or directory`; агент останавливается без результата | не запрещать `":root"` в профиле; запрещать только пути секретов либо разрешить чтение установки Codex. Проверка: `codex sandbox -- /bin/true`. Не «исправлять» через `-s workspace-write`: старый режим заменяет профиль и открывает чтение всех файлов |
| Правило Claude `Read(/abs/path)` не защищает файл | файл читается инструментом Read, хотя правило запрета его называет | в правилах прав одиночный ведущий `/` отсчитывается от источника настроек (`~/.claude` для пользовательских); писать `Read(//abs/path)`. В `sandbox.filesystem.denyRead` одиночный `/` абсолютный, поэтому один путь в двух списках пишется по-разному |
| Установщик или updater CBM настраивает всех найденных агентов | дубли hooks, глобальная регистрация MCP рядом с проектной, крупный блок в `AGENTS.md` | после `install` или `update` проверить всех агентов; `/stack normalize` (Claude), `manage.py install` (Codex). Если CBM подключается к проекту, `codebase-memory-mcp install` не запускать |
| Hooks Caveman зарегистрированы дважды | блок правил Caveman приходит дважды при старте и на каждое сообщение | удалить hooks автономного установщика из `settings.json`; плагин регистрирует свои |
| Один MCP-сервер объявлен в нескольких файлах | дубли инструментов, увеличенная схема | оставить один источник (`~/.claude.json`, `~/.claude/.mcp.json`, проектный `.mcp.json` или плагин) |
| Hooks context-mode выполняются дольше 2 с | задержка при каждом вызове инструмента; `/ctx-doctor` при этом показывает `[OK]` | причина: модуль зависимостей запускает `npm install better-sqlite3` при каждом вызове hook, установка падает (`Cannot read properties of null (reading 'edgesOut')`), ошибка подавляется. Замерять время hooks после каждого обновления плагина (бюджет около 100 мс). Ручной `node_modules` в кэше плагина теряется при обновлении и может удалить другие зависимости плагина (наблюдалось `Cannot find module 'turndown'` в `ctx_fetch_and_index`); предпочтительно переустановить плагин и сообщить разработчику |
| Hook-шлюз CBM в проекте без графа | около 1,5 с на каждый Grep и Glob | ранний выход в `~/.claude/hooks/cbm-code-discovery-gate` при отсутствии CBM в проекте: [agents/claude-code/hooks/cbm-gate-early-exit.sh](../agents/claude-code/hooks/cbm-gate-early-exit.sh) |
| `/stack on cbm` или `on context-mode` регистрирует падающий hook | ошибка hook `SessionStart` или `Grep\|Glob` на каждом событии: не найден `~/.claude/hooks/cbm-session-reminder` или `context-mode-cache-heal.mjs` | скрипты создавал только запрещённый стеком установщик производителя. Установить оба скрипта CBM из [agents/claude-code/hooks/](../agents/claude-code/hooks/); после исправления `toggle.py` пропускает hook без скрипта и сообщает об этом |
| Headroom при SOCKS-прокси в окружении | сервис завершается с `ImportError: Using SOCKS proxy, but the 'socksio' package is not installed` | устанавливать и обновлять командой `uv tool install 'headroom-ai[proxy]' --with socksio --force`; `uv tool upgrade` теряет дополнительные зависимости |
| Headroom выключен удалением `ANTHROPIC_BASE_URL` | агент продолжает обращаться к остановленному прокси (`ConnectionRefused` или молчаливое зависание), потому что переменная задана в оболочке | явно задавать `ANTHROPIC_BASE_URL=https://api.anthropic.com` вместо удаления |
| Обновление или индексация из двух агентов одновременно | повреждение или конфликт общего кэша CBM | обновлять общий бинарник и индексировать проект из одного агента за раз; не удалять кэш как способ исправления |
| Команды Codex получают `Operation not permitted` на локальном Unix-сокете (`hc`, Docker) | затем `hc` пытается запустить ядро и падает на systemd или файловой системе только для чтения | в профиле прав выключена сеть; переустановить стек (`workspace-only` её включает), перезапустить Codex, проверить `codex sandbox -- hc ls` |
| Обычный `codex` выполняет команды с `HC_TERMINAL_ID` другого терминала, вложенный `codex sandbox` падает с `app-server socket directory must be a user-owned directory with mode 0700` | сессия подключилась к общему демону app-server, который выполняет команды вне вызывающего терминала | переустановить стек (`daemon_auto_start = false`), один раз остановить демон, перезапустить Codex; `codex --no-daemon` даёт то же для одной сессии |
| Команды владельца на Codex падают с `Read-only file system` в `~/.cache/herdr-orch` | профиль разрешал запись только в рабочей папке | переустановить стек (общие кэши оркестрации доступны для записи), перезапустить Codex |
| RTK неверно переписывает `rg --files` | команда падает или ищет вместо вывода списка | старый RTK (0.42.4) переписывал её в `rtk grep --files`; проверка `rtk hook check 'rg --files'`, её выполняет и `manage.py doctor` |
| context-mode установлен вручную из архива | каталог плагина исчезает | Claude Code удаляет неизвестные каталоги в кэше плагинов; устанавливать и обновлять через `claude plugin` |

Проверки после установки:

```bash
rtk --version && rtk gain
rtk hook check 'rg --files'
codebase-memory-mcp --version
codex sandbox -- /bin/true
curl -s http://127.0.0.1:8787/livez      # Headroom, только если включён: {"alive":true}
```
