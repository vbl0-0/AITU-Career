# Current implementation verification

Checked on 24 October 2026. The existing local PostgreSQL cluster was started; no user tables were replaced.

| Check | Result |
|---|---|
| python -m pytest | passed; 60 checks. 35.06 seconds; one Starlette TestClient/httpx deprecation warning. The initial database connection timeout was resolved by starting the existing project cluster. |
| npm run test:e2e | passed; 20 checks. Chromium: graduate and admin journeys, portfolio CRUD, Dashboard states, role restrictions, responsive navigation, kk/ru/en and vacancy import/salary regressions. Some focused tests use API fixtures; the core journey and multilingual pages also use the real local API. |
| npm run check:i18n | passed; 459 checks. Translation keys, interpolation parity and static references in kk/ru/en. |
| npm run build | passed; TypeScript and production Vite build. Existing main-chunk warning: 501.13 kB before gzip. |
| python -m alembic upgrade head; python -m alembic check | passed; Migrations applied; no new upgrade operations detected. |
| node --test .github/scripts/project-sync.test.mjs | passed; 9 checks. Reference parsing, trusted PR filtering, transitions, partial merges, pagination and status-only/idempotent mutations. |
| Targeted UI review (eleven routes, desktop/mobile) | passed; 22 checks. Screenshots inspected; no horizontal document overflow or blocking page alert at 1440px/390px. Keyboard skip-link focus has a 3px outline. This is not comprehensive WCAG conformance. |

## Limits

- Docker image build and Compose runtime were not executed because Docker CLI is unavailable.
- The optional real embedding model is disabled/uninstalled; fallback and controlled semantic behavior are tested, not real model quality.
- Independent relevance labels and real ranking-quality/latency experiments are next-stage work, not measured results.
- User interviews and supervisor feedback are optional according to the team clarification of 24 October; none were fabricated.
- The public prototype is a screen walkthrough; the complete API-backed application is reproducible locally.
- The final form page and submission confirmation require the representative to check the actual form.

Current machine-readable results: [validation.json](pre-defense-1/evidence/validation.json). Screen-by-screen evidence: [targeted UI review](pre-defense-1/evidence/ui-review.html).
