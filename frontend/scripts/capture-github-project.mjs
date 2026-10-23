/** Capture actual public GitHub pages; no fabricated board or task rendering. */
import { chromium } from '@playwright/test';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '../..');
const manifest = JSON.parse(readFileSync(resolve(root, 'docs/pre-defense-1/github-project-migration.json'), 'utf8'));
const folder = resolve(root, 'docs/pre-defense-1/evidence/github-screenshots');
mkdirSync(folder, { recursive: true });
const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width: 1680, height: 1100 }, deviceScaleFactor: 1 });
  const result = [];
  async function capture(url, file, title, options = {}) {
    const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    if (!response?.ok()) throw new Error(`GitHub returned ${response?.status()} for ${url}`);
    await page.getByText(title, { exact: false }).first().waitFor({ timeout: 30000 });
    await page.evaluate(() => document.fonts.ready);
    if (options.criteria) await page.getByRole('heading', { name: 'Acceptance criteria', exact: true }).waitFor();
    await page.screenshot({ path: resolve(folder, file), fullPage: Boolean(options.fullPage), animations: 'disabled' });
    result.push({ url, file, title });
    console.log('Captured', file);
  }
  await capture(manifest.project_url + '/views/1', '01-board.png', 'Confirm team details and project scope');
  await capture(manifest.project_url + '/views/2', '02-table.png', 'Confirm team details and project scope');
  // Scroll the actual table's scroll containers so later tasks are also visible.
  const lastTask = page.getByText('Verify access and submit the team materials', { exact: false }).first();
  await lastTask.scrollIntoViewIfNeeded();
  await page.screenshot({ path: resolve(folder, '03-table-bottom.png'), animations: 'disabled' });
  result.push({ url: page.url(), file: '03-table-bottom.png', title: 'Remaining tasks and deadlines' });
  for (const [index, issue] of manifest.issues.entries()) {
    await capture(issue.url, `${String(index + 4).padStart(2, '0')}-${issue.legacy_id}.png`, issue.title, { criteria: true, fullPage: true });
  }
  writeFileSync(resolve(folder, 'capture-manifest.json'), JSON.stringify({ captured_on: '2026-10-22', public_access_verified: true, screenshots: result }, null, 2) + '\n');
  console.log(`Verified public access and captured ${result.length} genuine GitHub views.`);
} finally {
  await browser.close();
}
