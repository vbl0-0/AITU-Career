import { readFileSync, readdirSync } from 'node:fs';
import ts from 'typescript';

const root = new URL('../src/', import.meta.url);
const resources = Object.fromEntries(['kk', 'ru', 'en'].map(language => [language, JSON.parse(readFileSync(new URL(`i18n/locales/${language}/translation.json`, root), 'utf8'))]));
const keys = Object.keys(resources.en).sort();
const failures = [];
const placeholders = value => [...value.matchAll(/\{\{\s*([^}]+?)\s*\}\}/g)].map(match => match[1]).sort().join(',');
for (const [language, resource] of Object.entries(resources)) {
  if (JSON.stringify(Object.keys(resource).sort()) !== JSON.stringify(keys)) failures.push(`Translation key mismatch in ${language}`);
  for (const key of keys) {
    if (!resource[key]?.trim()) failures.push(`Empty translation: ${language}/${key}`);
    else if (/\?{2,}/.test(resource[key])) failures.push(`Corrupted translation: ${language}/${key}`);
    else if (placeholders(resource[key]) !== placeholders(resources.en[key])) failures.push(`Interpolation mismatch: ${language}/${key}`);
  }
}
function inspect(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const url = new URL(entry.name + (entry.isDirectory() ? '/' : ''), directory);
    if (entry.isDirectory()) { if (entry.name !== 'locales') inspect(url); continue; }
    if (!/\.tsx?$/.test(entry.name)) continue;
    const source = ts.createSourceFile(url.pathname, readFileSync(url, 'utf8'), ts.ScriptTarget.Latest, true, entry.name.endsWith('tsx') ? ts.ScriptKind.TSX : ts.ScriptKind.TS);
    function visit(node) {
      if (ts.isCallExpression(node) && node.expression.getText(source) === 't' && node.arguments[0] && ts.isStringLiteral(node.arguments[0]) && !resources.en[node.arguments[0].text]) failures.push(`Unknown key ${node.arguments[0].text} in ${entry.name}`);
      if (ts.isJsxText(node) && /[\u0400-\u04ff]/.test(node.text)) failures.push(`Untranslated JSX text in ${entry.name}: ${node.text.trim()}`);
      ts.forEachChild(node, visit);
    }
    visit(source);
  }
}
inspect(root);
if (failures.length) throw new Error(failures.join('\n'));
console.log(`Validated ${keys.length} keys in kk/ru/en, interpolation parameters and static translation references.`);
