/** Export local submission documents and real tracker screenshots using existing Playwright. */
import { chromium } from '@playwright/test';
import { readFileSync, mkdirSync, readdirSync, existsSync } from 'node:fs';
import { resolve, extname, basename } from 'node:path';
import { pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';

const root = resolve(import.meta.dirname, '../..');
const output = resolve(root, 'docs/pre-defense-1');
const mode = process.argv[2] || 'report';
const escape = value => String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
function prepare() {
  const python=resolve(root,'.venv/Scripts/python.exe');
  for(const script of ['submission_diagrams.py','prepare_submission.py']) {
    const result=spawnSync(python,[resolve(root,'scripts',script)],{cwd:root,encoding:'utf8'});
    if(result.status!==0)throw new Error(result.stderr||result.stdout);
    process.stdout.write(result.stdout);
  }
}
const browser=await chromium.launch();
try {
  const page=await browser.newPage({viewport:{width:1440,height:1100}});
  if(mode==='capture') {
    const lines=readFileSync(resolve(root,'.env'),'utf8').split(/\r?\n/);
    const password=lines.find(x=>x.startsWith('DEMO_PASSWORD='))?.slice(14);
    if(!password)throw new Error('DEMO_PASSWORD is missing in local .env');
    mkdirSync(resolve(root,'.local/screenshots'),{recursive:true});
    const base='http://localhost:5173';
    await page.goto(base);await page.getByRole('heading',{name:/Твои навыки/}).waitFor();
    await page.screenshot({path:resolve(root,'.local/screenshots/landing.png'),fullPage:true,animations:'disabled'});
    await page.goto(base+'/login');
    await page.getByLabel('Email',{exact:true}).fill('student.demo@aitu.edu.kz');
    await page.getByLabel('Пароль',{exact:true}).fill(password);
    await page.getByRole('button',{name:'Войти',exact:true}).click();
    await page.getByRole('heading',{name:'Привет, Demo 👋'}).waitFor();
    await page.screenshot({path:resolve(root,'.local/screenshots/dashboard.png'),fullPage:true,animations:'disabled'});
    await page.setViewportSize({width:390,height:844});
    if(await page.evaluate(()=>document.documentElement.scrollWidth)>390)throw new Error('Mobile dashboard overflows');
    await page.screenshot({path:resolve(root,'.local/screenshots/mobile.png'),fullPage:true,animations:'disabled'});
    await page.setViewportSize({width:1440,height:1100});
    await page.goto(base+'/jobs');
    await page.getByRole('link',{name:'Junior Python Backend Developer',exact:true}).click();
    await page.getByRole('heading',{name:'Недостающие навыки'}).waitFor();
    await page.screenshot({path:resolve(root,'.local/screenshots/job-detail.png'),fullPage:true,animations:'disabled'});
    await page.getByRole('button',{name:'Выйти',exact:true}).click();
    await page.getByLabel('Email',{exact:true}).fill('admin.demo@aitu.edu.kz');
    await page.getByLabel('Пароль',{exact:true}).fill(password);
    await page.getByRole('button',{name:'Войти',exact:true}).click();
    await page.getByRole('link',{name:'Администрирование',exact:true}).click();
    await page.getByRole('heading',{name:'Администрирование',exact:true}).waitFor();
    await page.getByRole('cell',{name:'Junior Python Backend Developer',exact:true}).waitFor();
    await page.screenshot({path:resolve(root,'.local/screenshots/admin.png'),fullPage:true,animations:'disabled'});
    await page.getByRole('button',{name:'Выйти',exact:true}).click();
    console.log('Captured five real prototype views; admin access verified.');
  } else if(mode==='report' || mode==='report-pdf') {
    if(mode==='report') {
    prepare();
    for(const name of ['context','components','use-cases']) {
      await page.goto(pathToFileURL(resolve(output,`diagrams/${name}.svg`)).href);
      await page.locator('svg').screenshot({path:resolve(output,`diagrams/${name}.png`)});
    }
    prepare(); // Include raster diagrams in editable DOCX and current prototype files.
    }
    await page.goto(pathToFileURL(resolve(output,'report.html')).href);
    await page.evaluate(()=>document.fonts.ready);
    const missing=await page.locator('.missing').allTextContents();
    const broken=await page.locator('img').evaluateAll(imgs=>imgs.filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src));
    if(missing.length||broken.length)throw new Error('Incomplete report images: '+JSON.stringify({missing,broken}));
    await page.pdf({path:resolve(output,'report.pdf'),format:'A4',printBackground:true,displayHeaderFooter:true,headerTemplate:'<span></span>',footerTemplate:'<div style="font:9px Arial;width:100%;text-align:center;color:#444444">AITU Career · Probationary period 1 · <span class="pageNumber"></span> / <span class="totalPages"></span></div>',preferCSSPageSize:true});
    await page.screenshot({path:resolve(output,'report-cover.png')});
    console.log(mode==='report' ? 'Exported report.pdf and report.docx.' : 'Exported report.pdf from existing HTML; DOCX and prototype images preserved.');
  } else if(mode==='evidence') {
    const folder=resolve(process.argv[3]||resolve(output,'evidence/tracker-screenshots'));
    if(!existsSync(folder))throw new Error('Provide a directory containing real tracker screenshots. No screenshots were supplied.');
    const images=readdirSync(folder).filter(name=>/^\.(png|jpe?g|webp)$/i.test(extname(name))).sort();
    if(!images.length)throw new Error('No real screenshots found; no evidence PDF was created.');
    const assets=images.map(name=>{const file=resolve(folder,name);const mime=extname(name).toLowerCase()==='.png'?'image/png':extname(name).toLowerCase()==='.webp'?'image/webp':'image/jpeg';return {name,src:`data:${mime};base64,${readFileSync(file).toString('base64')}`};});
    await page.setContent(assets.map(x=>`<img src="${x.src}">`).join(''));
    const sizes=await page.locator('img').evaluateAll(imgs=>Promise.all(imgs.map(async i=>{await i.decode();return {width:i.naturalWidth,height:i.naturalHeight};})));
    const manifestFile=resolve(folder,'capture-manifest.json');
    const captures=existsSync(manifestFile)?JSON.parse(readFileSync(manifestFile,'utf8')).screenshots:[];
    const items=[];
    for(const [i,asset] of assets.entries()){
      const heightMm=sizes[i].height*273/sizes[i].width;
      let parts=Math.max(1,Math.ceil(heightMm/165)),widthMm=273;
      // Avoid a nearly empty continuation page while keeping text legible.
      if(parts>1 && heightMm-(parts-1)*165<58){parts--;widthMm=273*(parts*165)/heightMm;}
      const capture=captures.find(x=>x.file===asset.name);
      const link=capture?` · <a href="${escape(capture.url)}">Open actual GitHub page</a>`:'';
      for(let part=0;part<parts;part++)items.push(`<section><h2>${i+1}. ${escape(basename(asset.name))} — part ${part+1}/${parts}${link}</h2><div class="frame"><img src="${asset.src}" style="top:-${part*165}mm;width:${widthMm}mm;left:${(273-widthMm)/2}mm"></div></section>`);
    }
    await page.setContent('<!doctype html><meta charset="utf-8"><style>@page{size:A4 landscape;margin:12mm}body{margin:0;font:12px Arial;color:#111111}a{color:inherit}section{break-before:page}section:first-child{break-before:auto}h2{font-size:12px;margin:0 0 5mm}.frame{position:relative;width:273mm;height:165mm;overflow:hidden}img{position:absolute;left:0;display:block;width:273mm;height:auto}</style>'+items.join(''));
    await page.locator('img').evaluateAll(imgs=>Promise.all(imgs.map(i=>i.decode())));
    await page.pdf({path:resolve(output,'tracker-evidence.pdf'),printBackground:true,preferCSSPageSize:true});
    console.log(`Combined ${images.length} supplied screenshots into tracker-evidence.pdf. Content and access must still be reviewed.`);
  } else throw new Error('Usage: node scripts/submission.mjs capture | report | report-pdf | evidence <screenshots-directory>');
} finally {await browser.close();}
