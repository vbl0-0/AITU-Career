# HeadHunter vacancy import

The integration uses the official [HeadHunter API](https://api.hh.ru/openapi/redoc)
with `host=hh.kz` and a Kazakhstan area filter. It does not scrape website HTML.
Imported records are distinct from the fictional demo dataset.

## Access and activation

Apply migrations and restart the backend after installing the new code. During
development verification, live vacancy search returned **403 Forbidden**. A live
import has therefore not been claimed or populated using substitute data.

Obtain permitted application access through [HeadHunter developers](https://dev.hh.ru/).
Configure `HH_ACCESS_TOKEN` in the server environment / ignored local `.env` if
required for that access. Do not send the token in chat or commit it.
`HH_USER_AGENT` identifies the application (default `AITU-Career/1.0`); configure
it according to the application's registered details and provider requirements.
`HH_TIMEOUT_SECONDS` defaults to 10. Docker Compose forwards these settings.

The token is sent only in an Authorization header to the fixed API host.
401/403, rate limits and network errors produce explicit localized errors.
Failed network batches save no import changes. Existing vacancies remain intact.

## Usage

An administrator opens **Administration → Vacancies → hh.kz import**. Import mode
requires search terms, an existing career role and category. These classifications
are explicitly assigned by the administrator. Search defaults to Kazakhstan,
no-experience vacancies and a limit of 10, with a maximum batch size of 20.
Review the chosen search and classification before importing.

Refresh mode checks previously imported records, starting with the least recently
checked. It can filter by role. This is an explicit operation; no background
scheduler has been configured.

The same operations are available from `backend/`:

```text
python -m app.services.hh_import --query "Python" --role-id <id> --category-id <id> --limit 10
python -m app.services.hh_import --sync --limit 20
```

Administrator API endpoints:

- `POST /api/admin/jobs/import/hh`: `text`, `role_id`, `category_id`, optional
  `area_id` (default `40`), `experience`, `limit`.
- `POST /api/admin/jobs/sync/hh`: optional `role_id`, `limit`.

Responses report `created`, `updated`, `unchanged`, `archived`, `skipped` counts.
Import preserves original company, title and location text. Descriptions are
converted to plain text, stripping markup and script/style contents. Source
URLs must be HTTPS links to HeadHunter. Missing salary bounds remain unknown.

## Matching and lifecycle

`source + external_id` has a database uniqueness constraint. Repeating an import
updates the existing record rather than inserting another vacancy. Unchanged
content preserves its revision and existing analyses; meaningful changes mark
old analyses stale. Source URL, publication date and last-check date are stored.

HeadHunter key skills are matched to the existing skill catalogue. If key skills
are absent, names are extracted from the description. No new technical skills
or proficiency estimates are invented. Imported catalogue requirements initially
use level 1 and weight 2 because the provider does not supply this platform's
levels/weights or required/preferred classification. The UI explains this and
links to the original; administrators can review and adjust requirements.
The administrator editor preserves provider experience/employment labels and
unknown values. Refresh replaces provider fields and detected requirements;
manual refinements should be reviewed again after a refresh.

Only a confirmed archived response, 404 or 410 closes an existing vacancy.
Absence from a bounded search never closes other records. Closed vacancies are
excluded from search and dashboard calculations, remain visible through saved
links, and cannot receive new match analyses. Refresh does not delete them.

Tests use HTTPX transport fixtures and an isolated migrated PostgreSQL schema;
they do not require or make live provider requests. Coverage includes imports,
deduplication, changes, provenance, access denial, 429, missing/closed records,
partial network failures, unsafe URLs and administrator permissions.
