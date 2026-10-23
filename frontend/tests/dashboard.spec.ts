import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const fixture = {
  readiness: 42.5,
  readiness_components: { market: .5, projects: .5, experience: 0, certificates: 0, education: .5 },
  readiness_weights: { market: .6, projects: .15, experience: .1, certificates: .05, education: .1 },
  readiness_contributions: { market: 30, projects: 7.5, experience: 0, certificates: 0, education: 5 },
  market_sample_size: 5, competency_count: 2, recommended_job_count: 9, skill_gap_count: 8,
  desired_role: 'Backend Developer',
  top_skills: [{ skill_id: 1, name: 'Python', level: 2, inferred: false, sources: ['Заявленный навык'] }],
  skill_gaps: [{ skill: 'Docker', priority: 8, action: 'Создай проект с Docker и пересчитай соответствие выбранным вакансиям.' }],
  profile_improvements: ['Добавь проект и его технологии.'],
  recommended_jobs: [
    { id: 1, title: 'Lower matching role', company: 'Test Company', location: 'Astana', employment_type: 'Internship', score: 72, is_demo: true, saved: false, skills: [{ name: 'Python', required: true }] },
    { id: 2, title: 'Highest matching role', company: 'Test Company', location: 'Remote', score: 95, is_demo: true, saved: false, skills: [{ name: 'Docker', required: true }] },
    ...[null, 0, -1, 101].map((score, index) => ({ id: index + 3, title: `Invalid recommendation ${index}`, company: 'Test Company', score, is_demo: true, saved: false, skills: [] })),
  ],
};

async function mockAuth(page: Page, admin = false) {
  await page.route('**/api/auth/refresh', route => route.fulfill({ json: {
    access_token: 'browser-test-token', user: { id: 999, name: 'Dashboard Tester', email: 'test@example.invalid', role: admin ? 'admin' : 'graduate' },
  } }));
}

test('dashboard uses ranked valid matches, real factor contributions and stored proficiency', async ({ page }) => {
  await mockAuth(page);
  let requests = 0;
  await page.route('**/api/dashboard', route => { requests++; return route.fulfill({ json: fixture }); });
  await page.goto('/dashboard');
  await expect(page.getByRole('heading', { name: 'Рекомендуемые вакансии' })).toBeVisible();
  const rows = page.locator('.dashboard-job');
  await expect(rows).toHaveCount(2);
  await expect(rows.first()).toContainText('Highest matching role');
  await expect(rows.nth(1)).toContainText('Стажировка');
  await expect(rows.nth(1).locator('.tag')).toHaveText('Python');
  await expect(page.getByText('Invalid recommendation', { exact: false })).toHaveCount(0);
  await expect(page.locator('.dashboard-stat').first().locator(':scope > strong')).toHaveText('9');
  await expect(page.locator('.dashboard-stat').last().locator(':scope > strong')).toHaveText('8');
  await expect(page.locator('.skill-bar-label')).toContainText('Средний · 2/3');
  await expect(page.locator('.skill-bars .progress-track > span')).toHaveAttribute('style', /66\.66/);
  await page.getByRole('link', { name: 'Как считается оценка' }).click();
  await expect(page.locator('.dashboard-assessment')).toHaveAttribute('open', '');
  await expect(page.locator('.assessment-factor')).toHaveCount(5);
  await expect(page.locator('.assessment-factor').first()).toContainText('+30 п.п.');
  await expect(page.locator('.assessment-content')).toContainText('42,5%');
  await expect(page.getByRole('link', { name: 'Администрирование', exact: true })).toHaveCount(0);
  await expect(page.getByRole('link', { name: 'Подробнее: Highest matching role' })).toHaveAttribute('href', '/jobs/2');
  await expect(page.getByRole('link', { name: 'Заполнить', exact: true })).toHaveAttribute('href', '/projects');
  expect(requests).toBe(1);
});

test('empty profile and absent vacancy data have useful empty states', async ({ page }) => {
  await mockAuth(page);
  await page.route('**/api/dashboard', route => route.fulfill({ json: {
    ...fixture, readiness: 0, competency_count: 0, market_sample_size: 0, desired_role: null,
    recommended_job_count: 0, skill_gap_count: 0, top_skills: [], skill_gaps: [], recommended_jobs: [],
    readiness_components: { market: 0, projects: 0, experience: 0, certificates: 0, education: 0 },
    readiness_contributions: { market: 0, projects: 0, experience: 0, certificates: 0, education: 0 },
    profile_improvements: ['Выбери карьерное направление.', 'Добавь образование AITU.', 'Добавь навыки с текущими уровнями.'],
  } }));
  await page.goto('/dashboard');
  await expect(page.getByRole('heading', { name: 'Начни с добавления навыков' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Покажи свои навыки' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Недостаточно данных для анализа' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Перейти к вакансиям' })).toHaveAttribute('href', '/jobs');
  await expect(page.locator('.dashboard-job')).toHaveCount(0);
  await expect(page.locator('.dashboard-stat').last().locator(':scope > strong')).toHaveText('—');
});

test('dashboard shows loading, an actionable error and successful retry', async ({ page }) => {
  await mockAuth(page);
  let release!: () => void;
  const ready = new Promise<void>(resolve => { release = resolve; });
  let requests = 0;
  await page.route('**/api/dashboard', async route => {
    if (++requests === 1) { await ready; await route.fulfill({ status: 503, json: { detail: 'Dashboard temporarily unavailable' } }); }
    else await route.fulfill({ json: fixture });
  });
  await page.goto('/dashboard');
  await expect(page.getByRole('status')).toContainText('Загружаем данные');
  release();
  await expect(page.getByRole('alert')).toContainText('Dashboard temporarily unavailable');
  await page.getByRole('button', { name: 'Повторить' }).click();
  await expect(page.getByRole('heading', { name: 'Рекомендуемые вакансии' })).toBeVisible();
  expect(requests).toBe(2);
});

test('responsive dashboard preserves statistics and accessible role-based navigation', async ({ page }) => {
  await mockAuth(page, true);
  await page.route('**/api/dashboard', route => route.fulfill({ json: fixture }));
  await page.goto('/dashboard');
  await expect(page.locator('.dashboard-job')).toHaveCount(2);
  await expect(page.getByRole('link', { name: 'Администрирование', exact: true })).toBeVisible();
  for (const width of [1440, 1280, 1024, 820, 768, 760, 600, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(page.getByRole('heading', { name: 'Подходящие вакансии' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Навыки для развития' })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth), `overflow at ${width}px`).toBeLessThanOrEqual(width);
    const clipped = await page.locator('.dashboard article, .dashboard section').evaluateAll(elements => elements.some(element => {
      const rect = element.getBoundingClientRect();
      return rect.left < 0 || rect.right > window.innerWidth + 1;
    }));
    expect(clipped, `clipped card at ${width}px`).toBe(false);
  }
  const menu = page.getByRole('button', { name: 'Открыть меню' });
  await menu.click();
  const drawer = page.getByRole('dialog', { name: 'Навигация AITU Career' });
  await expect(drawer).toBeVisible();
  await expect(menu).toHaveAttribute('aria-expanded', 'true');
  await expect(drawer.getByRole('button', { name: 'Закрыть меню' })).toBeFocused();
  await drawer.locator('a').last().focus();
  await page.keyboard.press('Tab');
  await expect(drawer.locator('a').first()).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(menu).toBeFocused();
  await expect(menu).toHaveAttribute('aria-expanded', 'false');
  await menu.click();
  await drawer.getByRole('link', { name: 'Обзор', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
});

test('populated local profile renders backend data and vacancy navigation end to end', async ({ page }) => {
  const env = readFileSync(resolve('..', '.env'), 'utf8');
  const password = process.env.DEMO_PASSWORD || env.split(/\r?\n/).find(line => line.startsWith('DEMO_PASSWORD='))?.slice('DEMO_PASSWORD='.length);
  expect(password).toBeTruthy();
  const login = await page.request.post('/api/auth/login', { data: { email: 'student.demo@aitu.edu.kz', password } });
  expect(login.ok()).toBeTruthy();
  const response = page.waitForResponse(response => response.url().endsWith('/api/dashboard'));
  await page.goto('/dashboard');
  const data = await (await response).json();
  await expect(page.getByRole('img', { name: `${Math.round(data.readiness)}% готовность` })).toBeVisible();
  await expect(page.locator('.dashboard-stat').first().locator(':scope > strong')).toHaveText(String(data.recommended_job_count));
  const best = data.recommended_jobs.filter((job: { score: number | null }) => job.score !== null && job.score > 0).sort((a: { score: number }, b: { score: number }) => b.score - a.score)[0];
  expect(best).toBeTruthy();
  await expect(page.locator('.dashboard-job').first()).toContainText(best.title);
  await page.getByRole('link', { name: `Подробнее: ${best.title}`, exact: true }).click();
  await expect(page.getByRole('heading', { name: best.title, exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Обзор', exact: true }).click();
  await page.getByRole('link', { name: 'Редактировать профиль' }).click();
  await expect(page.getByRole('heading', { name: 'Мой профиль', exact: true })).toBeVisible();
});
