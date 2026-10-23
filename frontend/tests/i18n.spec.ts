import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
const [kk, ru, en] = ['kk', 'ru', 'en'].map(language => JSON.parse(readFileSync(resolve(`src/i18n/locales/${language}/translation.json`), 'utf8')) as Record<string, string>);

const dictionaries: Record<string, Record<string, string>> = { kk, ru, en };
const env = readFileSync(resolve('..', '.env'), 'utf8');
const password = process.env.DEMO_PASSWORD || env.split(/\r?\n/).find(line => line.startsWith('DEMO_PASSWORD='))?.slice('DEMO_PASSWORD='.length);
const selector = (page: Page) => page.locator('.language-switcher select');
async function signIn(page: Page, admin = false) {
  const response = await page.request.post('/api/auth/login', { data: { email: admin ? 'admin.demo@aitu.edu.kz' : 'student.demo@aitu.edu.kz', password } });
  expect(response.ok()).toBeTruthy();
  return response.json();
}

test('language selection changes public and authentication pages without losing input', async ({ page }) => {
  await page.goto('/register');
  await page.locator('input[name="name"]').fill('Әділ Ғалым Қанатұлы');
  await page.locator('input[name="email"]').fill('language.test@example.invalid');
  let navigations = 0;
  page.on('framenavigated', frame => { if (frame === page.mainFrame()) navigations++; });
  for (const language of ['kk', 'en', 'ru']) {
    await selector(page).selectOption(language);
    await expect(page.locator('html')).toHaveAttribute('lang', language);
    await expect(page.getByRole('heading', { name: dictionaries[language]['auth.createTitle'] })).toBeVisible();
    await expect(page.locator('input[name="name"]')).toHaveValue('Әділ Ғалым Қанатұлы');
    await expect(page.locator('input[name="email"]')).toHaveValue('language.test@example.invalid');
    await expect(page.getByRole('button', { name: dictionaries[language]['auth.register'], exact: true })).toBeVisible();
  }
  expect(navigations).toBe(0);
  await selector(page).selectOption('kk');
  await page.reload();
  await expect(selector(page)).toHaveValue('kk');
  await page.getByRole('link', { name: kk['auth.home'] }).click();
  await expect(page.getByRole('link', { name: kk['landing.start'] })).toBeVisible();
  await expect(page).toHaveTitle(kk['meta.title']);
});

test('client and server validation messages update in the selected language', async ({ page }) => {
  await page.goto('/login');
  await selector(page).selectOption('kk');
  await page.getByRole('button', { name: kk['auth.login'], exact: true }).click();
  expect(await page.locator('input[name="email"]').evaluate((input: HTMLInputElement) => input.validationMessage)).toBe(kk['validation.required']);
  await selector(page).selectOption('en');
  expect(await page.locator('input[name="email"]').evaluate((input: HTMLInputElement) => input.validationMessage)).toBe(en['validation.required']);
  await page.locator('input[name="email"]').fill('not.an.account@example.com');
  await page.locator('input[name="password"]').fill('incorrect-password');
  await page.getByRole('button', { name: en['auth.login'], exact: true }).click();
  await expect(page.getByRole('alert')).toContainText(en['errors.credentials']);
  await selector(page).selectOption('ru');
  await expect(page.getByRole('alert')).toContainText(ru['errors.credentials']);
});

test('profile edits, notifications and API enum values survive language changes and sign-in', async ({ page }) => {
  await signIn(page);
  await page.goto('/profile');
  await expect(page.locator('input[name="name"]')).toBeVisible();
  await page.locator('input[name="name"]').fill('Unsaved multilingual name');
  await page.locator('select[name="employment_type"]').selectOption('Part-time');
  await selector(page).selectOption('kk');
  await expect(page.locator('input[name="name"]')).toHaveValue('Unsaved multilingual name');
  await expect(page.locator('select[name="employment_type"]')).toHaveValue('Part-time');
  await expect(page.locator('select[name="employment_type"] option:checked')).toHaveText(kk['enum.partTime']);
  await page.reload(); // Discard test edits; never change the real demo profile.
  await expect(page.getByRole('heading', { name: kk['common.profile'], exact: true })).toBeVisible();
  await page.route('**/api/profile', async route => {
    if (route.request().method() === 'PUT') {
      const original = await page.request.get('/api/profile', { headers: { Authorization: 'Bearer ' + (await signIn(page)).access_token } });
      await route.fulfill({ json: await original.json() });
    } else await route.continue();
  });
  await page.getByRole('button', { name: kk['profile.save'] }).click();
  await expect(page.locator('.success[role="status"]')).toContainText(kk['profile.updated']);
  await selector(page).selectOption('en');
  await expect(page.locator('.success[role="status"]')).toContainText(en['profile.updated']);
  await page.getByRole('button', { name: en['nav.logout'], exact: true }).click();
  await expect(page.getByRole('heading', { name: en['auth.welcome'] })).toBeVisible();
  await signIn(page);
  await page.goto('/dashboard');
  await expect(selector(page)).toHaveValue('en');
});

for (const language of ['kk', 'ru', 'en']) test(`all protected pages, analysis, admin forms and mobile navigation work in ${language}`, async ({ page }) => {
  const text = dictionaries[language];
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await signIn(page, true);
  await page.goto('/dashboard');
  await selector(page).selectOption(language);
  const routes = [
    ['/dashboard', 'dashboard.recommendedJobs'], ['/profile', 'common.profile'], ['/skills', 'portfolio.skillsTitle'],
    ['/projects', 'portfolio.projectsTitle'], ['/certificates', 'portfolio.certificatesTitle'], ['/experience', 'portfolio.experienceTitle'],
    ['/saved', 'jobs.savedTitle'], ['/recommendations', 'career.title'], ['/admin', 'common.admin'], ['/jobs', 'jobs.title'],
  ];
  for (const [route, key] of routes) {
    await page.goto(route);
    await expect(page.getByRole('heading', { name: text[key], exact: true }).first()).toBeVisible();
    await expect(selector(page)).toHaveValue(language);
    for (const width of [1280, 390, 320]) {
      await page.setViewportSize({ width, height: 900 });
      expect(await page.evaluate(() => document.documentElement.scrollWidth), `overflow on ${route} in ${language} at ${width}`).toBeLessThanOrEqual(width);
    }
    await page.setViewportSize({ width: 1280, height: 900 });
  }
  const first = page.locator('.job-title').first();
  const jobTitle = await first.innerText();
  await first.click();
  await expect(page.getByRole('heading', { name: jobTitle, exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: text['jobs.about'], exact: true })).toBeVisible();
  await page.getByRole('link', { name: text['match.detail'], exact: true }).click();
  await expect(page.getByRole('heading', { name: text['match.title'], exact: true })).toBeVisible();
  if (language !== 'ru') await expect(page.locator('.analysis-explanation')).not.toContainText('Полностью покрыто');
  if (language === 'ru') await expect(page.locator('.analysis-explanation')).toContainText('Набрано:');
  await page.goto('/admin');
  await page.getByRole('button', { name: text['common.add'], exact: true }).click();
  const dialog = page.getByRole('dialog');
  await dialog.locator('input[name="title"]').fill('Unsaved vacancy');
  await dialog.locator('select[name="employment_type"]').selectOption('Internship');
  await dialog.locator('.language-switcher select').selectOption(language === 'en' ? 'kk' : 'en');
  await expect(dialog.locator('input[name="title"]')).toHaveValue('Unsaved vacancy');
  await expect(dialog.locator('select[name="employment_type"]')).toHaveValue('Internship');
  await dialog.locator('.language-switcher select').selectOption(language);
  await dialog.getByRole('button', { name: text['common.cancel'], exact: true }).click();
  await page.locator('.table-actions').first().getByRole('button').last().click();
  await expect(page.getByRole('dialog', { name: text['common.confirmTitle'] })).toBeVisible();
  await expect(page.getByRole('dialog').getByRole('button', { name: text['common.delete'], exact: true })).toBeVisible();
  await page.getByRole('dialog').getByRole('button', { name: text['common.cancel'], exact: true }).click();
  await page.goto('/dashboard');
  for (const width of [1024, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(selector(page)).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth), `overflow in ${language} at ${width}`).toBeLessThanOrEqual(width);
  }
  await page.getByRole('button', { name: text['nav.openMenu'] }).click();
  await page.getByRole('dialog').getByRole('link', { name: text['common.skills'], exact: true }).click();
  await expect(page.getByRole('heading', { name: text['portfolio.skillsTitle'] })).toBeVisible();
  expect(errors).toEqual([]);
});

test('saved preference wins, unsupported browser language falls back to English and missing keys fall back', async ({ browser }) => {
  const context = await browser.newContext({ locale: 'fr-FR' });
  const page = await context.newPage();
  await page.goto('http://localhost:5173/login');
  await expect(selector(page)).toHaveValue('en');
  await selector(page).selectOption('kk');
  await page.reload();
  await expect(selector(page)).toHaveValue('kk');
  const fallback = await page.evaluate(async () => {
    const path = '/src/i18n/index.ts';
    const { default: i18n } = await import(path);
    const bundle = i18n.getResourceBundle('kk', 'translation');
    const original = bundle['common.save'];
    delete bundle['common.save'];
    const value = i18n.t('common.save');
    i18n.addResource('kk', 'translation', 'common.save', original);
    return value;
  });
  expect(fallback).toBe(en['common.save']);
  await context.close();
});
