# Автоматическое обновление GitHub Project

Доска: https://github.com/users/vbl0-0/projects/1.

Автоматизация меняет поле Status существующих карточек Issues. Она не создаёт
дубликаты карточек, не закрывает Issues и не подменяет review другого участника.

## Как пользоваться после активации

| Действие команды | Результат на доске |
|---|---|
| Push в ветку `AITU-8-frontend-delivery` | Задача #8 → In Progress |
| Draft PR в `main`, в описании `Task: #8` | Задача #8 → In Progress |
| Обычный PR или Ready for review, `Task: #8` | Задача #8 → Review |
| Изменения в ветке с открытым готовым PR | Задача остаётся в Review |
| Слияние частичного PR с `Refs #8`, Issue остаётся открытым | Задача #8 → In Progress |
| Issue закрыт как completed, в том числе после слияния PR с `Closes #8` | Задача #8 → Done |
| Issue открыт повторно | To Do, либо состояние текущего PR |
| Issue закрыт как not planned | To Do; не выдаётся за выполненную задачу |

Исходный экспорт использует одинаковые номера AITU-N и GitHub #N для всех
18 задач. Поэтому в ветках используется `AITU-N-описание`. Если позднее нумерация
разойдётся, используйте GitHub-номер задачи в имени ветки и явный `Task: #N` в PR.

В PR укажите отдельной строкой:

```text
Task: #8
Refs #8
```

Когда PR действительно выполняет все критерии задачи, замените `Refs #8` на
`Closes #8`. Сам `Task: #8` только связывает PR для статуса, не закрывая Issue.
Закрытие через `Closes` выполняет GitHub после слияния в основную ветку при
включённом Auto-close issues with merged linked pull requests.

Учитываются только PR от `vbl0-0` и `igiiaw` из этого же репозитория в основную
ветку. Если есть хотя бы один готовый PR по задаче, выбирается Review; если
есть только черновики — In Progress. Другие репозитории и примеры в блоках
кода не рассматриваются как ссылки на ваши задачи.

После событий запускается GitHub Actions. Расписание примерно раз в 15 минут
повторно сверяет статусы с текущими открытыми PR и состояниями Issues; GitHub
может задерживать запуски. Это восстанавливает синхронизацию при временных
ошибках, но не восстанавливает старый push в ветку до установки workflow.

Новые Issues добавляйте в Project отдельно: синхронизация обслуживает карточки,
которые уже находятся на доске. `Done` всегда определяется фактическим закрытием
Issue как completed. Интервью и отзыв руководителя не выполняются загрузкой кода.

## Однократная активация

Текущая авторизация Git Credential Manager имеет `repo`, `workflow`, `gist`,
но не `project`. Обычный `GITHUB_TOKEN` из Actions тоже не даёт доступа к Projects.
Поэтому требуется отдельный секрет. Не отправляйте его в чат и не храните в Git.

1. После слияния PR настройки под аккаунтом `vbl0-0` создайте personal access
   token с правом записи в пользовательские Projects. Для fine-grained token
   используйте User/Account Projects: read and write; для выбранного
   `AITU-Career` — Issues: read и Pull requests: read. Если ваш интерфейс не
   предлагает пользовательские Projects, используйте classic token со scope
   `project`; для этого публичного репозитория чтение публичных Issue/PR не
   требует доступа к другим частным репозиториям. Ограничьте срок действия.
2. Откройте https://github.com/vbl0-0/AITU-Career/settings/secrets/actions.
   Создайте **New repository secret** с именем **PROJECTS_TOKEN** и вставьте
   токен непосредственно в поле Secret.
3. В https://github.com/vbl0-0/AITU-Career/actions выберите **Project status sync**,
   затем **Run workflow**, ветка `main`.
4. Проверьте лог **Synchronize existing issue cards**. Он сообщает число
   проверенных карточек и реальные изменения статусов. Без секрета выводится
   предупреждение, а доска не меняется: успешный запуск сам по себе не означает
   активацию, если в логе написано `Project sync is inactive`.
5. Для проверки создайте обычную рабочую ветку `AITU-N-...` по реальной задаче,
   затем Draft PR с `Task: #N`. Убедитесь в In Progress. Переведите PR в Ready
   for review и убедитесь в Review. Не закрывайте невыполненную задачу ради теста.

Если срок токена истёк, замените значение `PROJECTS_TOKEN` и запустите workflow
ещё раз. Скрипт сообщает об HTTP/GraphQL-ошибках, не печатая секреты.

## Реализация и проверки

- `.github/project-sync.json` — репозиторий, Project и участники.
- `.github/workflows/project-sync.yml` — события и запуск синхронизации.
- `.github/scripts/project-sync.mjs` — ссылки на задачи, выбор статусов и GraphQL.
- `.github/scripts/project-sync.test.mjs` — проверки правил и API-взаимодействия
  без настоящих токенов и без изменения живой доски.
- `.github/workflows/automation-checks.yml` — автоматический запуск этих тестов.

Локальная проверка:

```powershell
node --test .github/scripts/project-sync.test.mjs
```

Статусный workflow запускает скрипт только из основной ветки, не устанавливает
зависимости и не исполняет код PR. Fork PR не получает секрет. Workflow тестов
секретов не использует. Временные комментарии, одобрения и фиктивные выполненные
задачи для демонстрации автоматизации не создаются.

Официальные инструкции:

- https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/automating-projects-using-actions
- https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue
