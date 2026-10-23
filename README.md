# AITU Career

AI-Based Platform to Support the Employment of Astana IT University Graduates.

The platform compares a graduate profile with IT vacancy skill requirements,
explains matched and missing skills, and suggests practical learning steps.

## Problem, users and expected outcomes

Students and graduates need to compare their education and practical experience
with vacancy requirements. The prototype targets AITU students/graduates and an
administrator. Local demand remains a hypothesis until user discussions are
conducted. Expected outcomes are an explainable working prototype and a
reproducible comparison of matching methods; scores are not hiring probabilities.

## Team and supervision

The team consists of two students:

- Қожабек Аяділ Нұрланұлы — SE-2425, GitHub [vbl0-0](https://github.com/vbl0-0).
- Амантай Жан Әділұлы — SE-2419, GitHub [igiiaw](https://github.com/igiiaw).

Supervisor: Оразова Арайлым Жанболаткызы, Senior Lecturer.
Names retain the spelling in the supplied project justification. Confirmed
details are stored in [submission.json](docs/pre-defense-1/submission.json).
Planned work areas include backend/data, frontend/UX, research and QA; actual
individual contributions still require linked changes and review evidence.

Repository: [vbl0-0/AITU-Career](https://github.com/vbl0-0/AITU-Career).
The [GitHub Project](https://github.com/users/vbl0-0/projects/1) contains 18 issues
migrated from AITU-1 through AITU-18. Ayadil (@vbl0-0) and Zhan (@igiiaw) each
have nine assigned issues. Status, priority, original due date, planned owner and
YouTrack ID are recorded. Board and table views are public for reading.
Uploading the application code, progressive contributions, actual reviews and
supervisor/committee verification remain outstanding. Confirm the tracker
substitution with the supervisor. See [migration evidence](docs/pre-defense-1/github-project-migration.json).

## Scope and current status

Implemented locally: authentication and roles; AITU-oriented profile and education;
skills with levels; projects, certificates and experience; jobs and saved jobs;
weighted matching with explanations; stale analysis detection; recommendations;
and administration. Seed data contains 30 explicitly fictional vacancies.
An explicit HeadHunter import/refresh integration now supports source links,
deduplication and vacancy availability. Live provider access currently returns
403; no real vacancy import has been claimed. See the import setup guide below.

For an installation without demo content, set `SEED_DEMO=false`. Reference
catalogues are still initialized. Provision the first administrator with
`python -m app.database.bootstrap --email your.name@aitu.edu.kz` from `backend/`
(the password is prompted), or explicitly configure `BOOTSTRAP_ADMIN_*` for
startup. Existing accounts and passwords are preserved. See the development guide.

Out of scope: automated hiring decisions, university SSO/DU/Moodle integration,
mandatory external job providers and production deployment. Semantic matching is
optional and its real model quality has not been evaluated. The readiness formula
is an internal heuristic, not a validated employment predictor.

## Documentation and October submission

- [Submission package and remaining work](docs/pre-defense-1/README.md)
- [Two-part initial delivery and collaboration instructions](docs/TEAM_DELIVERY.md)
- [Unified report (PDF)](docs/pre-defense-1/report.pdf)
- [Editable report (Word)](docs/pre-defense-1/report.docx)
- [Browser report](docs/pre-defense-1/report.html)
- [Sources](docs/pre-defense-1/sources.json), [diagrams](docs/pre-defense-1/diagrams/),
  [proposed tracker tasks](docs/pre-defense-1/tasks.csv)
- [Development and demo guide](docs/DEVELOPMENT.md)
- [HeadHunter import and access setup](docs/VACANCY_IMPORT.md)
- [Validation on 19 October](docs/pre-defense-1/evidence/validation.html)
- [Historical validation on 5 October](docs/VALIDATION.md)
- [Original project specification](docs/ORIGINAL_PROJECT_SPECIFICATION.md)

The dossier covers proposal, relevance, literature, existing systems, technology
choices, requirements, architecture, prototype, evaluation, management/risks and
supervisor feedback. Interviews and real feedback are pending and clearly labeled.
The deadline stated in the announcement is **24 October 2026, before 18:00 UTC+5**.

## Technology and structure

React 19 / TypeScript / Vite; Python 3.12 / FastAPI; SQLAlchemy / Alembic;
PostgreSQL; pytest; Playwright. Optional sentence-transformers model with a
keyword fallback. Docker Compose defines database, backend and frontend services.

- `frontend/src/`: components, pages, hooks and API client
- `backend/app/`: routes, schemas, security, models, persistence and AI module
- `backend/migrations/`: versioned database migrations
- `backend/tests/`, `frontend/tests/`: automated checks
- `docs/pre-defense-1/`: report, editable diagrams, prototype and planning artifacts
- `scripts/`: setup, local startup and reproducible dossier preparation

## Run on Windows

Prerequisites: Python 3.12+, Node.js 22.12+ and PostgreSQL. The local PostgreSQL
binaries on this computer are in `D:\postgres\bin`.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

After dependencies have been installed:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-local.ps1 -SkipInstall
```

Website: http://localhost:5173. API: http://localhost:8000/docs.
The script preserves existing `.env` and uses a separate project PostgreSQL
cluster on `127.0.0.1:55432`. Stop application processes with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/stop-local.ps1
```

Docker alternative (configuration provided; not executed in this environment):

```powershell
python scripts/setup_env.py
docker compose up --build
```

Docker website: http://localhost:8080.

## Testing

From `backend/`:

```powershell
..\.venv\Scripts\python.exe -m pytest
..\.venv\Scripts\python.exe -m alembic check
```

From `frontend/`, with both application servers running:

```powershell
npm ci
npm run build
npm run check:i18n
npx playwright install chromium
npm run test:e2e
```

API tests use an isolated random PostgreSQL schema. E2E tests create temporary
records and clean up their own users/jobs using the demo administrator. They need
DEMO_PASSWORD from the local environment. See the development guide for details.

## Interface languages

The interface supports Kazakh, Russian and English. Use the globe selector in
the header; the choice is remembered in the browser. See [localization](docs/I18N.md)
for translation files, fallback rules and dynamic-content handling.

## Security and review

Never commit `.env`, passwords, tokens, local database contents or identifiable
interview records. `.env.example` contains placeholders only. Each participant
must use an identifiable personal account. Link branches/commits/merge requests
to real tracker task IDs, review before merging, and tag the exact reviewed
submission as `pre-defense-1` without moving that tag later. See
[workflow](docs/pre-defense-1/templates/repository-workflow.html).
