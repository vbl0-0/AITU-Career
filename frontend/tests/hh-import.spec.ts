import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const dictionary = Object.fromEntries(['ru', 'en', 'kk'].map(language => [language,
  JSON.parse(readFileSync(resolve(`src/i18n/locales/${language}/translation.json`), 'utf8')) as Record<string, string>,
]));

test('admin can configure import and refresh, with localized access errors and preserved form state', async ({ page }) => {
  await page.route('**/api/auth/refresh', route => route.fulfill({ json: {
    access_token: 'browser-test-token', user: { id: 99, name: 'Import Tester', email: 'test@example.invalid', role: 'admin' },
  } }));
  await page.route('**/api/catalog/*', route => {
    const kind = route.request().url().split('/').pop();
    return route.fulfill({ json: kind === 'skills' ? [] : [{ id: 1, name: kind === 'career-roles' ? 'Backend Developer' : 'Engineering' }] });
  });
  await page.route('**/api/admin/statistics', route => route.fulfill({ json: { users: 1, jobs: 0, skills: 0, matches: 0 } }));
  await page.route('**/api/admin/jobs', route => route.fulfill({ json: [] }));
  let result = false;
  let releaseImport: (() => void) | undefined;
  const importReady = new Promise<void>(resolve => { releaseImport = resolve; });
  const requests: unknown[] = [];
  await page.route('**/api/admin/jobs/import/hh', async route => {
    requests.push(route.request().postDataJSON());
    if (result) await importReady;
    await route.fulfill(result ? { json: { created: 1, updated: 0, unchanged: 0, archived: 0, skipped: 0 } }
      : { status: 502, json: { detail: 'errors.hhAccess' } });
  });
  await page.route('**/api/admin/jobs/sync/hh', route => route.fulfill({ json: { created: 0, updated: 1, unchanged: 0, archived: 1, skipped: 0 } }));
  await page.goto('/admin');
  await page.getByRole('button', { name: dictionary.ru['admin.hhTitle'], exact: true }).click();
  const dialog = page.getByRole('dialog');
  await dialog.locator('input[name="text"]').fill('Python');
  await dialog.locator('select[name="role_id"]').selectOption('1');
  await dialog.locator('select[name="category_id"]').selectOption('1');
  await dialog.locator('.language-switcher select').selectOption('kk');
  await expect(dialog.locator('input[name="text"]')).toHaveValue('Python');
  await dialog.getByRole('button', { name: dictionary.kk['admin.hhImport'], exact: true }).click();
  await expect(dialog.getByRole('alert')).toContainText(dictionary.kk['errors.hhAccess']);
  await dialog.locator('.language-switcher select').selectOption('en');
  await expect(dialog.getByRole('alert')).toContainText(dictionary.en['errors.hhAccess']);
  expect(requests[0]).toEqual({ text: 'Python', role_id: 1, category_id: 1, limit: 10, area_id: '40', experience: 'noExperience' });
  result = true;
  await dialog.getByRole('button', { name: dictionary.en['admin.hhImport'], exact: true }).click();
  await expect(dialog.locator('button[type="submit"]')).toBeDisabled();
  await page.keyboard.press('Escape');
  await expect(dialog).toBeVisible();
  releaseImport!();
  await expect(dialog.locator('.success')).toContainText('Created: 1');
  await dialog.getByLabel(dictionary.en['admin.hhMode']).selectOption('sync');
  await dialog.getByRole('button', { name: dictionary.en['admin.hhSync'], exact: true }).click();
  await expect(dialog.locator('.success')).toContainText('Closed: 1');
  await dialog.locator('.form-actions').getByRole('button', { name: dictionary.en['common.close'], exact: true }).click();
  await expect(dialog).toHaveCount(0);
});

test('imported vacancy shows its origin and a closed vacancy is not analyzed', async ({ page }) => {
  await page.route('**/api/auth/refresh', route => route.fulfill({ json: {
    access_token: 'browser-test-token', user: { id: 99, name: 'Graduate', email: 'test@example.invalid', role: 'graduate' },
  } }));
  await page.route('**/api/jobs/999', route => route.fulfill({ json: {
    id: 999, title: 'Imported Test Vacancy', company: 'Example', location: 'Astana', description: 'Original provider description.',
    salary_min: 300000, salary_max: null, currency: 'KZT', employment_type: 'Full-time', experience_level: 'No experience',
    role: 'Backend Developer', skills: [], saved: false, source: 'hh', source_url: 'https://hh.kz/vacancy/999',
    last_synced_at: '2026-10-19T09:00:00Z', is_active: false, is_demo: false,
  } }));
  let matches = 0;
  await page.route('**/api/jobs/999/match', route => { matches++; return route.fulfill({ status: 409, json: { detail: 'jobs.closed' } }); });
  await page.goto('/jobs/999');
  await expect(page.getByRole('heading', { name: 'Imported Test Vacancy', exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: dictionary.ru['jobs.original'] })).toHaveAttribute('href', 'https://hh.kz/vacancy/999');
  await expect(page.locator('.job-description')).toContainText(dictionary.ru['jobs.closed']);
  expect(matches).toBe(0);
  await expect(page.getByRole('link', { name: dictionary.ru['common.admin'], exact: true })).toHaveCount(0);
  await page.route('**/api/catalog/career-roles', route => route.fulfill({ json: [] }));
  await page.route('**/api/saved-jobs', route => route.fulfill({ json: [{
    id: 999, title: 'Imported Test Vacancy', company: 'Example', location: 'Astana',
    employment_type: '', experience_level: '', salary_min: null, salary_max: null,
    currency: 'KZT', skills: [], source: 'hh', source_url: 'https://hh.kz/vacancy/999',
    is_active: false, is_demo: false,
  }] }));
  await page.goto('/saved');
  const card = page.locator('.job-card');
  await expect(card).toBeVisible();
  await expect(card.locator('.job-meta')).toHaveText('');
  await expect(card).toContainText(dictionary.ru['jobs.noSalary']);
  await expect(card).toContainText(dictionary.ru['jobs.closed']);
});

test('administrator edits imported requirements without replacing provider experience and employment labels', async ({ page }) => {
  const job = { id: 999, title: 'Imported Test Vacancy', company: 'Example', location: 'Astana',
    description: 'Original provider description for the imported vacancy.', role_id: 1, category_id: 1,
    experience_level: 'No experience', employment_type: 'Flexible schedule', skills: [],
    salary_min: null, salary_max: null, currency: 'KZT', source: 'hh', is_demo: false, is_active: true };
  await page.route('**/api/auth/refresh', route => route.fulfill({ json: {
    access_token: 'browser-test-token', user: { id: 99, name: 'Import Tester', email: 'test@example.invalid', role: 'admin' },
  } }));
  await page.route('**/api/catalog/*', route => route.fulfill({ json:
    route.request().url().endsWith('/skills') ? [] : [{ id: 1, name: 'Engineering' }],
  }));
  await page.route('**/api/admin/statistics', route => route.fulfill({ json: { users: 1, jobs: 1, skills: 0, matches: 0 } }));
  await page.route('**/api/admin/jobs', route => route.fulfill({ json: [job] }));
  let updated: Record<string, unknown> | undefined;
  await page.route('**/api/admin/jobs/999', route => {
    updated = route.request().postDataJSON();
    return route.fulfill({ json: { ...job, ...updated } });
  });
  await page.goto('/admin');
  await page.locator('.table-actions button').first().click();
  const dialog = page.getByRole('dialog');
  await expect(dialog.locator('[name="experience_level"]')).toHaveValue('No experience');
  await expect(dialog.locator('[name="employment_type"]')).toHaveValue('Flexible schedule');
  await dialog.locator('.language-switcher select').selectOption('kk');
  await dialog.getByRole('button', { name: dictionary.kk['common.save'], exact: true }).click();
  await expect(dialog).toHaveCount(0);
  expect(updated).toMatchObject({ experience_level: 'No experience', employment_type: 'Flexible schedule' });
});
