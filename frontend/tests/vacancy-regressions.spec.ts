import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const text = Object.fromEntries(['ru', 'kk', 'en'].map(language => [language,
  JSON.parse(readFileSync(resolve(`src/i18n/locales/${language}/translation.json`), 'utf8')) as Record<string, string>,
]));

test('vacancy salary handles every missing bound in all three interface languages', async ({ page }) => {
  await page.route('**/api/auth/refresh', route => route.fulfill({ json: {
    access_token: 'browser-test-token', user: { id: 999, name: 'Salary Tester', email: 'test@example.invalid', role: 'graduate' },
  } }));
  let salaryMin: number | null = 300000;
  let salaryMax: number | null = null;
  await page.route('**/api/jobs/999', route => route.fulfill({ json: {
    id: 999, title: 'Salary Regression Vacancy', company: 'Example', location: 'Astana', description: 'Test fixture vacancy.',
    employment_type: 'Full-time', role: 'Backend Developer', experience_level: 'Junior', is_demo: true,
    salary_min: salaryMin, salary_max: salaryMax, currency: 'KZT', saved: false, skills: [],
  } }));
  await page.route('**/api/jobs/999/match', route => route.fulfill({ json: {
    id: 999, score: null, matched: [], partial: [], missing: [], recommendations: [],
  } }));
  await page.goto('/jobs/999');
  for (const language of ['ru', 'kk', 'en']) {
    await page.locator('.language-switcher select').selectOption(language);
    const locale = { ru: 'ru-RU', kk: 'kk-KZ', en: 'en-GB' }[language];
    // Chromium and Node can ship different ICU data; use the browser's locale formatting.
    const numbers = await page.evaluate(locale => Object.fromEntries([0, 300000, 500000].map(value =>
      [value, new Intl.NumberFormat(locale).format(value)])), locale);
    const number = (value: number) => numbers[value];
    for (const [min, max] of [[300000, null], [null, 500000], [null, null], [0, 0], [300000, 500000]] as const) {
      salaryMin = min; salaryMax = max;
      await page.reload();
      const expected = min === null && max === null ? text[language]['jobs.noSalary']
        : `${min === null ? '…' : number(min)}–${max === null ? '…' : number(max)} KZT`;
      await expect(page.locator('.job-description > h2')).toHaveText(expected);
      await expect(page.locator('.job-description')).not.toContainText('undefined');
      await expect(page.locator('.language-switcher select')).toHaveValue(language);
    }
  }
});
