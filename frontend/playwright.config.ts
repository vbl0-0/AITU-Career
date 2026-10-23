import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', fullyParallel: false, workers: 1,
  timeout: 60000,
  use: { baseURL: process.env.E2E_BASE_URL || 'http://localhost:5173', headless: true, locale: 'ru-RU', trace: 'retain-on-failure' },
  reporter: 'list',
});
