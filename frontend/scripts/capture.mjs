import { chromium } from '@playwright/test';
import { readFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const output = resolve('..', '.local', 'screenshots');
mkdirSync(output, { recursive: true });
const password = readFileSync(resolve('..', '.env'), 'utf8').split(/\r?\n/).find(x => x.startsWith('DEMO_PASSWORD='))?.slice(14);
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
  await page.goto('http://localhost:5173');
  await page.getByRole('heading', { name: /Твои навыки/ }).waitFor();
  await page.screenshot({ path: resolve(output, 'landing.png'), fullPage: true, animations: 'disabled' });
  await page.goto('http://localhost:5173/login');
  await page.getByLabel('Email', { exact: true }).fill('student.demo@aitu.edu.kz');
  await page.getByLabel('Пароль').fill(password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await page.getByRole('heading', { name: 'Привет, Demo 👋' }).waitFor();
  await page.screenshot({ path: resolve(output, 'dashboard.png'), fullPage: true, animations: 'disabled' });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: resolve(output, 'mobile.png'), fullPage: true, animations: 'disabled' });
  console.log('Screenshots saved to .local/screenshots');
} finally { await browser.close(); }
