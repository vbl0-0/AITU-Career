# Первая загрузка проекта двумя участниками

Репозиторий: https://github.com/vbl0-0/AITU-Career

Доска: https://github.com/users/vbl0-0/projects/1

Первая загрузка разделена на две самостоятельные поставки модулей. Общего
начального коммита со всем приложением не требуется. Каждый участник проверяет
свой пакет и публикует его под собственным аккаунтом с фактической датой.
Такой импорт фиксирует поставку текущего модуля; сам по себе он не восстанавливает
предыдущие этапы разработки или личное авторство всех существующих строк.

## Что кому загружать

| Участник | Пакет / этап | Файлы | Связанные задачи |
|---|---|---|---|
| Ayadil, `vbl0-0` | `00-repository` | README, `.gitignore`, `.env.example`, инструкция команды и упаковщик; код приложения отсутствует | #12, #14 |
| Ayadil, `vbl0-0` | `01-backend` | `backend/`: API, модели, миграции, matching, seed, тесты, зависимости и Dockerfile | #9, #12; часть #3, #7 |
| Zhan, `igiiaw` | `01-frontend` | `frontend/`: интерфейс, переводы, тесты, зависимости, Dockerfile, браузерные скрипты | #8, #9 |
| Ayadil, `vbl0-0` | `02-architecture-and-run` | Docker Compose, настройка/запуск, исходники и экспорты диаграмм, инструкции backend и проверки | #6, #7, #9 |
| Zhan, `igiiaw` | `02-research-and-report-sources` | Источники литературы, исходный текст и генератор отчёта, инструкции i18n, шаблоны и сравнения в разделах отчёта | #4, #5, #16 |
| Zhan, `igiiaw` | `03-submission-materials` | Word/PDF/HTML, скриншоты, экспорт задач, подтверждения и остальные материалы предзащиты | #13, #16, #17 |

Это распределение загрузки и проверки. Обсуждения с пользователями (#2),
содержательный отзыв руководителя (#15), итоговая отправка (#18) и отдельное
исследование качества (#10/#11) не выполняются автоматически при загрузке файлов.

## Порядок работы на двух компьютерах

1. Ayadil создаёт пустую основную ветку `main` только из `00-repository`.
   В ней ещё нет backend или frontend. Это техническая подготовка репозитория.
2. Оба клонируют один и тот же репозиторий. Ayadil готовит ветку
   `AITU-12-backend-delivery`, Zhan — `AITU-8-frontend-delivery`.
   Пакеты `01` не пересекаются по файлам, их можно проверять параллельно.
3. Каждый запускает проверки своей части и открывает Pull Request в `main`.
   Второй участник читает изменения, проверяет запуск и оставляет содержательный
   review. Пароли и доступ к аккаунту друг друга не требуются.
4. После проверки оба PR объединяются. Только теперь `main` содержит
   обе части приложения. Следующие ветки всегда создаются от обновлённого `main`.
5. Затем Ayadil публикует `02-architecture-and-run`, Zhan —
   `02-research-and-report-sources`. Проверяют друг друга и объединяют PR.
6. После актуализации отчёта и проверки скриншотов Zhan публикует
   `03-submission-materials`, Ayadil проверяет комплектность и ссылки.
7. Выполняют интеграционные проверки, фиксируют фактический вклад и готовят
   версию предзащиты. Тег `pre-defense-1` ставится на проверенную общую версию.

Переход между этапами определяется результатом проверки, а не ожиданием
нескольких часов или созданием коммитов по искусственному расписанию.

## Начальные команды для Ayadil

Распакуй свой ZIP в отдельную папку пакета. Выполняй команды в новой рабочей
папке, чтобы не затронуть существующее приложение и локальную базу:

```powershell
git clone https://github.com/vbl0-0/AITU-Career.git AITU-Career-shared
cd AITU-Career-shared
git switch --orphan main
git config --local user.name "Ayadil"
git config --local user.email "231680607+vbl0-0@users.noreply.github.com"
```

Если в репозитории уже есть `main` с файлами, команду `switch --orphan` не
выполнять: использовать существующую ветку. Помощник `apply-team-stage.ps1`
копирует только один выбранный этап и готовит его файлы в index:

```powershell
& 'C:\path\to\Ayadil-package\apply-team-stage.ps1' -Stage 00-repository -Repository (Get-Location).Path
git diff --cached --stat
git diff --cached
git commit -m "AITU-12: Prepare shared repository metadata"
git push -u origin main

git switch -c AITU-12-backend-delivery
& 'C:\path\to\Ayadil-package\apply-team-stage.ps1' -Stage 01-backend -Repository (Get-Location).Path
git diff --cached --stat
# Проверить содержимое и backend, затем:
git commit -m "AITU-12: Import current backend module with migrations and tests"
git push -u origin AITU-12-backend-delivery
```

Если уже работаешь в инициализированной папке исходного проекта, не запускай
в ней команды создания пустой ветки: используй отдельную копию из примера.

## Начальные команды для Zhan

Дождись появления `main` с метаданными, распакуй свой ZIP отдельно от рабочей
копии и клонируй репозиторий:

```powershell
git clone https://github.com/vbl0-0/AITU-Career.git
cd AITU-Career
git config --local user.name "Zhan"
# В Settings → Emails своего GitHub скопировать личный noreply или verified email:
git config --local user.email "YOUR_OWN_GITHUB_EMAIL"
git switch -c AITU-8-frontend-delivery
& 'C:\path\to\Zhan-package\apply-team-stage.ps1' -Stage 01-frontend -Repository (Get-Location).Path
cd frontend
npm ci
npm run check:i18n
npm run build
cd ..
git diff --cached --stat
git commit -m "AITU-8: Import current frontend module and browser checks"
git push -u origin AITU-8-frontend-delivery
```

Собственный email нужно указать до коммита; значение из примера не использовать.
GitHub Desktop можно использовать вместо команд commit/push, войдя в свой аккаунт.

## Следующие этапы

Перед каждой новой веткой:

```powershell
git switch main
git pull --ff-only origin main
git switch -c AITU-7-architecture-delivery
```

Затем применить свой следующий этап помощником, проверить, закоммитить и
отправить новую ветку. Zhan использует, например,
`AITU-4-research-delivery` и `AITU-16-submission-materials`.
Не копировать ZIP целиком в рабочую копию: в ней должны появляться только
файлы выбранного этапа. Существующую Git-историю помощник не переносит.

## Проверки

- Backend: установить Python 3.12+, зависимости `backend/requirements.lock.txt`,
  создать собственный `.env` по примеру и собственную PostgreSQL-базу;
  затем из `backend/` выполнить `python -m pytest`, `python -m alembic upgrade head`
  и `python -m alembic check`. Тесты требуют доступной PostgreSQL с CREATE SCHEMA.
- Frontend: `npm ci`, `npm run check:i18n`, `npm run build` из `frontend/`.
- Браузерные тесты запускать после подключения API, каталогов и seed:
  `npx playwright install chromium`, затем `npm run test:e2e` из `frontend/`.
- Отчёт: после получения исходников диаграмм и генератора проверить Word/PDF,
  ссылки, соответствие текущему коду, источники и реальные результаты проверки.

Инструкция полного запуска находится в `docs/DEVELOPMENT.md`; она появляется
в этапе архитектуры Ayadil. `.env`, локальные пароли и базы не передаются.
Рабочую папку для запусков можно дополнить текущими файлами другого участника
через его ветку после согласования, но коммитить только свой выбранный этап.

## Pull Requests и доска

В PR записать: `Task: #8`, перечень фактически проверенных изменений,
команды и результаты, оставшиеся ограничения. Если PR выполняет лишь часть
задачи, использовать `Refs #8`. Если все критерии задачи выполнены и проверены,
использовать `Closes #8`.

`Closes #8` закрывает Issue после слияния в основную ветку при включённом
автоматическом закрытии. Для статусов подготовлен workflow: push в ветку
`AITU-8-...` → In Progress; готовый PR с отдельной строкой `Task: #8` → Review;
фактически закрытая completed-задача → Done. Частичный PR оставляет Issue
открытым. Номер в сообщении обычного коммита сам по себе не закрывает задачу.

Сначала необходимо слить PR настройки и добавить секрет `PROJECTS_TOKEN`.
Без секрета workflow сообщает о неактивной синхронизации и не меняет доску.
Пошаговая активация и ограничения: [PROJECT_AUTOMATION.md](PROJECT_AUTOMATION.md).
Загрузка файлов не должна автоматически закрывать интервью, review руководителя
или всю задачу, выполненную только частично.

## Что содержат ZIP

В каждом архиве есть `START_HERE.md`, `manifest.json`, отдельные этапы и помощник
`apply-team-stage.ps1`. Полного приложения в одном пакете нет. Вместе пакеты
покрывают все выбранные материалы проекта, без пересечений по файлам.
В manifest хранятся относительные пути, размер и SHA-256 каждого файла.
Упаковщик исключает `.env`, `.git`, базы, `.local`, зависимости, кеши и
не относящийся к диплому `aws_academy_progress.md`.
