/** Capture genuine board/task pages from the user's already authorized browser. */
import { chromium } from '@playwright/test';
import { readFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const root=resolve(import.meta.dirname,'../..');
const folder=resolve(root,'docs/pre-defense-1/evidence/tracker-screenshots');
const snapshot=JSON.parse(readFileSync(resolve(root,'docs/pre-defense-1/evidence/youtrack-snapshot.json'),'utf8'));
const origin=snapshot.instance_url;
const browser=await chromium.connectOverCDP('http://127.0.0.1:9223');
const page=browser.contexts()[0].pages().find(p=>p.url().startsWith(origin));
if(!page)throw new Error('The authenticated YouTrack browser must be open.');
mkdirSync(folder,{recursive:true});
await page.setViewportSize({width:1680,height:1100});
await page.goto(snapshot.board_url,{waitUntil:'domcontentloaded'});
await page.getByText('AITU Career - Diploma',{exact:true}).first().waitFor();
await page.getByText('Confirm team details and project scope',{exact:false}).first().waitFor();
await page.getByText('Ayadil',{exact:true}).first().waitFor();
await page.screenshot({path:resolve(folder,'01-board.png'),animations:'disabled'});
await page.getByText('Verify access and submit the team materials',{exact:false}).first().scrollIntoViewIfNeeded();
await page.screenshot({path:resolve(folder,'01b-board-bottom.png'),animations:'disabled'});
for(const [index,issue] of snapshot.issues.toSorted((a,b)=>Number(a.idReadable.split('-')[1])-Number(b.idReadable.split('-')[1])).entries()){
  await page.goto(origin+'/issue/'+issue.idReadable,{waitUntil:'domcontentloaded'});
  await page.getByText(issue.summary,{exact:true}).first().waitFor();
  await page.getByRole('heading',{name:/^Acceptance criteria/}).first().waitFor();
  await page.screenshot({path:resolve(folder,`${String(index+2).padStart(2,'0')}-${issue.idReadable}.png`),fullPage:true,animations:'disabled'});
  console.log('Captured',issue.idReadable);
}
await page.goto(snapshot.board_url,{waitUntil:'domcontentloaded'});
await page.bringToFront();
console.log('Captured the real board and all 18 task details. Browser remains open.');
process.exit(0);
