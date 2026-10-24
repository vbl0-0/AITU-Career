"""Render the English dossier with black text and original-color visual assets."""
from pathlib import Path
import html
import json
import shutil
import re
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED
from submission_content_en import build_content

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/pre-defense-1'
OUT.mkdir(parents=True, exist_ok=True)
for name in ('prototype', 'templates', 'evidence', 'diagrams'):
    (OUT / name).mkdir(exist_ok=True)
cfg = json.loads((OUT / 'submission.json').read_text(encoding='utf-8'))
REPORT_DATE = cfg.get('report_date', '19 October 2026')
REPORT_STATUS = cfg.get('report_status', 'Draft for academic review. User discussions and supervisor feedback have not yet been obtained.')
cfg['team_size'] = 2
cfg['members'] = (cfg.get('members') or [])[:2]
while len(cfg['members']) < 2:
    cfg['members'].append({'name':'', 'gitlab':'', 'contribution':''})
cfg.pop('title_ru', None)
(OUT / 'submission.json').write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
sources, sections = build_content(cfg, ROOT)
front_blocks = []
academic = cfg.get('report_layout') == 'academic'
if academic:
    from submission_academic import prepare_academic_report
    front_blocks, sections = prepare_academic_report(sources, sections, cfg, ROOT)
toc_entries = [{'title': 'Submission Information', 'anchor': 'front-summary', 'level': 0}]
for number, section in enumerate(sections, 1):
    section['anchor'] = f'chapter-{number}'
    toc_entries.append({'title': section['title'], 'anchor': section['anchor'], 'level': 0})
    subsection = table_number = figure_number = 0
    heading = 'Overview'
    for block in section['blocks']:
        if block['type'] == 'h3':
            subsection += 1
            block['anchor'] = f'chapter-{number}-sub-{subsection}'
            heading = re.sub(r'^\d+\.\d+\s+', '', block['text'])
            toc_entries.append({'title': block['text'], 'anchor': block['anchor'], 'level': 1})
        elif block['type'] == 'table':
            table_number += 1
            block['caption'] = f'Table {number}.{table_number}. {heading}'
            headers=block['headers']
            if not block.get('widths'):
                if headers[0]=='Task': block['widths']=[51,16,18,15]
                elif headers[0]=='ID / priority': block['widths']=[13,19,43,25]
                elif headers[0]=='Decision': block['widths']=[19,45,36]
                elif len(headers)==2: block['widths']=[28,72]
                elif len(headers)==3: block['widths']=[26,38,36]
        elif block['type'] == 'image':
            figure_number += 1
            caption = re.sub(r'^Figure\s+\d+(?:\.\d+)?\.\s*', '', block['caption'])
            block['caption'] = f'Figure {number}.{figure_number}. {caption}'
toc_file = OUT / 'toc-pages.json'
page_map = json.loads(toc_file.read_text(encoding='utf-8')).get('page_map', {}) if toc_file.exists() else {}
history_file=OUT/'evidence/development-history.json'
known_commits={item['commit'][:7]:item['commit'] for item in json.loads(history_file.read_text(encoding='utf-8')).get('commits',[])} if history_file.exists() else {}

# Preserve the actual application screenshots, including their original colors.
for name in ('landing.png','dashboard.png','mobile.png','job-detail.png','admin.png'):
    source = ROOT / '.local/screenshots' / name
    if not source.exists():
        source = OUT / 'prototype' / name
    destination = OUT / 'prototype' / name
    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)

CSS = '''
@page { size:A4; margin:18mm 16mm 19mm; }
* { box-sizing:border-box; } body { color:#111; font:10.5pt/1.45 'Segoe UI',Arial,sans-serif; margin:0; }
h1 { color:#111; font-size:25pt; line-height:1.2; } h2 { font-size:18pt; color:#111; line-height:1.3; margin:0 0 18px; }
h3 { font-size:12pt; color:#111; } p { margin:0 0 10px; orphans:3; widows:3; } a { color:#111; overflow-wrap:anywhere; }
section { break-before:page; } .cover { min-height:238mm; display:flex; flex-direction:column; justify-content:space-between; }
.label { color:#333; font-weight:700; letter-spacing:2px; font-size:10pt; } .status { border-left:3px solid #555; background:#f3f3f3; padding:14px; }
table { width:100%; border-collapse:collapse; table-layout:fixed; margin:12px 0 16px; font-size:9pt; line-height:1.4; }
th,td { border:1px solid #d9e3ed; padding:7px; vertical-align:top; overflow-wrap:anywhere; } th { background:#eaf3fc; text-align:left; color:#111; }
tr { break-inside:avoid; } thead { display:table-header-group; } figure { margin:18px 0; break-inside:avoid; }
figure img { display:block; max-width:100%; max-height:210mm; margin:auto; object-fit:contain; } figcaption { font-size:9pt; color:#444; margin:8px 0; }
.toc { line-height:2; list-style:none; padding:0; } .small { font-size:9pt; color:#444; }
.section-1, .section-2 { font-size:10pt; line-height:1.38; }
.section-1 table, .section-2 table { font-size:8.8pt; line-height:1.35; }
.section-1 td, .section-1 th, .section-2 td, .section-2 th { padding:6px; }
.section-2 { font-size:9.7pt; line-height:1.35; }
.section-2 table { font-size:8.7pt; line-height:1.3; }
.section-2 td, .section-2 th { padding:5.5px; }
.section-12 { font-size:9.5pt; line-height:1.35; }
.fields td { height:28px; } h2,h3 { break-after:avoid; }
'''
if academic:
    CSS = '''
@page { size:A4; margin:25mm 20mm 22mm 30mm; }
* { box-sizing:border-box; }
body { margin:0; color:#111; background:white; font:11pt/1.28 'Times New Roman',Times,serif; }
h1,h2,h3 { color:#111; font-family:'Times New Roman',Times,serif; break-after:avoid; }
h1 { font-size:23pt; line-height:1.22; font-weight:400; }
h2 { font-size:18pt; line-height:1.15; font-weight:400; margin:18pt 0 12pt; }
h3 { font-size:13pt; line-height:1.18; font-weight:700; margin:15pt 0 7pt; }
p { margin:0 0 7pt; text-align:justify; orphans:3; widows:3; }
a { color:#111; text-decoration:underline; overflow-wrap:anywhere; }
ul,ol { padding-left:6mm; margin:5pt 0 9pt; } li { margin-bottom:4pt; }
table { width:100%; border-collapse:collapse; table-layout:fixed; font-size:8.6pt; line-height:1.18; margin:7pt 0 10pt; border-top:.7pt solid #111; border-bottom:.7pt solid #111; }
th,td { border:0; border-bottom:.35pt solid #aaa; padding:4pt 3pt; text-align:left; vertical-align:top; overflow-wrap:anywhere; }
th { color:#111; background:white; font-weight:700; border-bottom:.7pt solid #111; }
thead { display:table-header-group; } tr { break-inside:avoid; }
caption { caption-side:top; color:#111; text-align:center; font-size:10pt; padding-bottom:5pt; }
figure { margin:12pt 0 15pt; break-inside:avoid; text-align:center; }
figure img { display:block; max-width:100%; max-height:188mm; width:auto; height:auto; object-fit:contain; margin:0 auto; }
figcaption { color:#111; font-size:10pt; line-height:1.2; margin-top:6pt; text-align:center; }
.cover { height:248mm; display:flex; flex-direction:column; align-items:center; text-align:center; break-after:page; }
.cover-title { border-top:3px double #111; border-bottom:3px double #111; padding:6mm 0; margin:13mm 0 11mm; width:100%; }
.cover-title h1 { margin:0; }
.cover p { text-align:center; margin:0 0 5mm; }
.cover-authors { margin:1mm 0 0; }
.university-logo { width:49mm; height:49mm; object-fit:contain; margin:1mm 0; }
.cover-bottom { margin-top:auto; padding-bottom:2mm; }
.cover-bottom p { margin-bottom:2mm; }
.front-matter { break-after:page; font-size:10.5pt; line-height:1.22; }
.front-matter h2,.toc-section h2 { margin-top:0; font-size:23pt; }
.front-matter h3 { font-size:13pt; }
.front-matter table { font-size:8.6pt; }
.front-matter table:first-of-type td:first-child { width:27%; }
.toc-section { break-after:page; }
.toc-row { break-inside:avoid; margin:0 0 4pt; line-height:1.25; }
.toc-row a { display:flex; align-items:baseline; gap:5pt; text-decoration:none; }
.toc-row.level-0 { font-weight:700; margin-top:7pt; }
.toc-row.level-1 { padding-left:6mm; }
.toc-dots { flex:1; border-bottom:1px dotted #777; min-width:6mm; }
.toc-page { min-width:10mm; text-align:right; }
.chapter { break-before:auto; }
.chapter.first-chapter h2 { margin-top:0; }
.small { font-size:9pt; }
@media screen { body { width:160mm; margin:25mm auto; } }
'''

def esc(value): return html.escape(str(value))

def linked(value):
    parts = re.split(r'(https?://[^\s<>]+)', str(value))
    rendered = []
    for part in parts:
        if part.startswith(('https://', 'http://')):
            url = part.rstrip('.,;')
            rendered.append('<a href="'+esc(url)+'">'+esc(url)+'</a>'+esc(part[len(url):]))
        else:
            def reference(match):
                token=match.group(0)
                if token.startswith('#'):
                    url=cfg['repository_url']+'/issues/'+token[1:]
                elif token[:7] in known_commits:
                    url=cfg['repository_url']+'/commit/'+known_commits[token[:7]]
                else:
                    return token
                return '<a href="'+esc(url)+'">'+token+'</a>'
            rendered.append(re.sub(r'(?<![\w])(?:#\d+|[a-f0-9]{7,40})(?![\w])',reference,esc(part)))
    return ''.join(rendered)

def render_block(block):
    kind=block['type']
    if kind in ('p','h3'):
        anchor=f' id="{esc(block["anchor"])}"' if block.get('anchor') else ''
        return f'<{kind}{anchor}>{linked(block["text"])}</{kind}>'
    if kind=='list':
        return '<ul>'+''.join('<li>'+linked(item)+'</li>' for item in block['items'])+'</ul>'
    if kind=='table':
        headers=block['headers']
        head=''.join('<th>'+esc(v)+'</th>' for v in headers)
        rows=''.join('<tr>'+''.join('<td>'+linked(v)+'</td>' for v in row)+'</tr>' for row in block['rows'])
        widths=block.get('widths')
        if not widths:
            if headers[0]=='Decision': widths=[19,45,36]
            elif headers[0]=='ID / priority': widths=[13,19,43,25]
            elif headers[0]=='Objective': widths=[34,66]
            elif headers[0]=='Metric': widths=[21,46,33]
        cols='<colgroup>'+''.join(f'<col style="width:{v}%">' for v in widths)+'</colgroup>' if widths else ''
        caption='<caption>'+esc(block['caption'])+'</caption>' if block.get('caption') else ''
        return f'<table>{caption}{cols}<thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>'
    if kind=='image':
        if not (OUT/block['path']).exists(): raise FileNotFoundError(block['path'])
        return f'<figure><img src="{esc(block["path"])}"><figcaption>{esc(block["caption"])}</figcaption></figure>'
    raise ValueError(kind)

def cover_fields():
    rows=[['Team size','2'], ['Student 1 — full name',cfg['members'][0].get('name','')], ['Student 2 — full name',cfg['members'][1].get('name','')], ['Group',cfg.get('group','')], ['Supervisor',cfg.get('supervisor','')], ['Supervisor position',cfg.get('supervisor_position','')], ['Repository URL',cfg.get('repository_url','')], ['Issue tracker URL',cfg.get('tracker_url','')]]
    return rows

def render():
    if academic:
        authors=''.join('<p>'+esc(member['name'])+'<br><span class="small">Group '+esc(member.get('group',''))+'</span></p>' for member in cfg['members'])
        cover='<div class="cover"><div class="cover-title"><h1>'+esc(cfg['title'])+'</h1></div><p>First Submission of Materials, Probationary Period 1</p><p>By</p><div class="cover-authors">'+authors+'</div><img class="university-logo" src="university-logo.png" alt="Astana IT University"><div class="cover-bottom"><p>Astana IT University</p><p>Supervisor: '+esc(cfg['supervisor'])+'<br>'+esc(cfg.get('supervisor_position',''))+'</p><p>October 2026<br>Astana</p></div></div>'
        front='<section class="front-matter"><h2 id="front-summary">Submission Information</h2>'+''.join(render_block(block) for block in front_blocks)+'</section>'
        toc='<section class="toc-section"><h2>Table of Contents</h2>'+''.join('<div class="toc-row level-'+str(entry['level'])+'"><a href="#'+esc(entry['anchor'])+'"><span>'+esc(entry['title'])+'</span><span class="toc-dots"></span><span class="toc-page">'+esc(page_map.get(entry['anchor'],''))+'</span></a></div>' for entry in toc_entries)+'</section>'
        body=''.join('<section class="chapter'+(' first-chapter' if i==0 else '')+'"><h2 id="'+esc(section['anchor'])+'">'+esc(section['title'])+'</h2>'+''.join(render_block(block) for block in section['blocks'])+'</section>' for i,section in enumerate(sections))
        (OUT/'report.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AITU Career — First Submission of Materials</title><style>'+CSS+'</style><body>'+cover+front+toc+body+'</body></html>',encoding='utf-8')
        (OUT/'report-content.json').write_text(json.dumps({'config':cfg,'sources':sources,'front_matter':front_blocks,'sections':sections,'toc_entries':toc_entries},ensure_ascii=False,indent=2),encoding='utf-8')
        (OUT/'sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
        for i,section in enumerate(sections,1):
            (OUT/f'{i:02d}-section.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><style>'+CSS+'</style><h2>'+esc(section['title'])+'</h2>'+''.join(render_block(block) for block in section['blocks'])+'</html>',encoding='utf-8')
        return
    fields='<table class="fields">'+''.join('<tr><td>'+esc(k)+'</td><td>'+esc(v)+'</td></tr>' for k,v in cover_fields())+'</table>'
    cover='<div class="cover"><div><p class="label">ASTANA IT UNIVERSITY · 2026</p><p>Pre-defense 1 · Report</p></div><div><h1>'+esc(cfg['title'])+'</h1><p>19 October 2026</p><div class="status">Draft for academic review. User discussions and supervisor feedback have not yet been obtained.</div></div><div>'+fields+'<p class="small">Submission deadline: 24 October 2026 before 18:00 (UTC+5).</p></div></div>'
    cover=cover.replace('19 October 2026', esc(REPORT_DATE)).replace('Draft for academic review. User discussions and supervisor feedback have not yet been obtained.', esc(REPORT_STATUS))
    toc='<section><h2>Contents</h2><ol class="toc">'+''.join('<li>'+esc(s['title'])+'</li>' for s in sections)+'</ol></section>'
    body=''.join(f'<section class="section-{i}"><h2>'+esc(s['title'])+'</h2>'+''.join(render_block(x) for x in s['blocks'])+'</section>' for i,s in enumerate(sections,1))
    (OUT/'report.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>AITU Career — Pre-defense Report</title><style>'+CSS+'</style><body>'+cover+toc+body+'</body></html>',encoding='utf-8')
    (OUT/'report-content.json').write_text(json.dumps({'config':cfg,'sources':sources,'sections':sections},ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
    for i,s in enumerate(sections,1):
        (OUT/f'{i:02d}-section.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><style>'+CSS+'</style><h2>'+esc(s['title'])+'</h2>'+''.join(render_block(x) for x in s['blocks'])+'</html>',encoding='utf-8')

def templates():
    forms=[
        ('interview-record.html','User Discussion Record',['Discussion ID','Actual date','Interviewer','Participant role','Consent to anonymized notes'],['Question / observation','Response / quotation','Interpretation','Requirement / decision']),
        ('supervisor-feedback.html','Supervisor Review Record',['Review date','Supervisor','Reviewed version / commit','Meeting format'],['Artifact / section','Actual comment','Response and rationale','Task / commit / confirmation']),
    ]
    for name,title,fields,columns in forms:
        b=[{'type':'table','headers':['Field','Value'],'rows':[[f,cfg.get('supervisor','') if f=='Supervisor' else ''] for f in fields]}, {'type':'table','headers':columns,'rows':[['']*len(columns) for _ in range(8)]}]
        (OUT/'templates'/name).write_text('<!doctype html><html lang="en"><meta charset="utf-8"><style>'+CSS+'</style><h1>'+title+'</h1>'+''.join(render_block(x) for x in b)+'</html>',encoding='utf-8')
    # Keep the repository workflow and submission checklist synchronized with the report language.
    for name,title,items in [
        ('repository-workflow.html','Repository and Traceability',[
            'Use one GitHub or GitLab repository throughout the diploma project. Each of the two students uses a personal account and identifiable commits.',
            'Give both team members, the supervisor and committee appropriate access. Check actual access before submission.',
            'Create real tracker tasks and assign each to one of the two students. Record the expected outcome, priority, acceptance criteria and deadline.',
            'Use actual task IDs in branches and commit/merge-request descriptions. Link the implementation back to its task.',
            'Keep main as the checked baseline. Preserve actual review comments and disclose AI-assisted checks; do not invent a human review.',
            'Tag the exact reviewed version prob-period-1 without moving previously submitted tags. Do not fabricate earlier history.',
            'Exclude secrets, local databases and identifying research records.']),
        ('submission-checklist.html','Submission Checklist',[
            'Deadline: 24 October 2026 before 18:00 (UTC+5). One representative submits on behalf of both students.',
            'Complete the blank identity, supervisor, account and link fields with confirmed information.',
            'User interviews are optional for this submission according to the team clarification; do not fabricate records.',
            'Supervisor feedback is optional; record actual comments and resulting changes only if received.',
            'Verify real task assignments, contributions, reviews and committee access.',
            'Combine actual board and task screenshots into one separate PDF using submission.mjs evidence.',
            'Review the editable Word report, export the final PDF, upload both PDFs and retain submission confirmation.'])]:
        (OUT/'templates'/name).write_text('<!doctype html><html lang="en"><meta charset="utf-8"><style>'+CSS+'</style><h1>'+title+'</h1><ol>'+''.join('<li>'+esc(x)+'</li>' for x in items)+'</ol></html>',encoding='utf-8')

render()
templates()


def write_docx():
    """Create a native editable DOCX using OOXML; no office installation required."""
    if academic:
        from submission_docx import write_academic_docx
        write_academic_docx(cfg, front_blocks, sections, OUT, toc_entries=toc_entries, page_map=page_map)
        return
    ns='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    rels=[]; media=[]
    def para(text,style=None):
        prop=f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ''
        runs=[]
        for part in re.split(r'(https?://[^\s<>]+)', str(text)):
            if part.startswith(('https://', 'http://')):
                url=part.rstrip('.,;'); rid='rLink'+str(len(rels)+1)
                rels.append('<Relationship Id="'+rid+'" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="'+html.escape(url,quote=True)+'" TargetMode="External"/>')
                runs.append('<w:hyperlink r:id="'+rid+'"><w:r><w:rPr><w:color w:val="111111"/><w:u w:val="single"/></w:rPr><w:t>'+escape(url)+'</w:t></w:r></w:hyperlink>')
                part=part[len(url):]
            runs.append('<w:r><w:t xml:space="preserve">'+escape(part)+'</w:t></w:r>')
        return '<w:p>'+prop+''.join(runs)+'</w:p>'
    body=para(cfg['title'],'Title')+para('Pre-defense 1 report | '+REPORT_DATE)
    body+=para('Team size: 2')
    body+=para(REPORT_STATUS)
    for label,value in cover_fields()[1:]:
        body+=para(label+': '+value)
    body+=para('Submission deadline: 24 October 2026 before 18:00 (UTC+5).')
    body+=para('Contents','Heading1')
    for s in sections:
        body+=para(s['title'])
    for s in sections:
        body+=para(s['title'],'Heading1')
        for block in s['blocks']:
            if block['type'] in ('p','h3'): body+=para(block['text'],'Heading2' if block['type']=='h3' else None)
            elif block['type']=='table':
                rows=[block['headers']]+block['rows']; cells=[]
                for idx,row in enumerate(rows):
                    props='<w:trPr><w:tblHeader/></w:trPr>' if idx==0 else ''
                    cells.append('<w:tr>'+props+''.join('<w:tc><w:tcPr><w:tcW w:w="0" w:type="auto"/></w:tcPr>'+para(v)+'</w:tc>' for v in row)+'</w:tr>')
                body+='<w:tbl><w:tblPr><w:tblW w:w="5000" w:type="pct"/><w:tblBorders>'+''.join(f'<w:{side} w:val="single" w:sz="4" w:color="DCE4EE"/>' for side in ['top','bottom','left','right','insideH','insideV'])+'</w:tblBorders></w:tblPr>'+''.join(cells)+'</w:tbl>'
            elif block['type']=='image':
                file=OUT/block['path']; file=file.with_suffix('.png') if file.suffix=='.svg' else file
                if file.exists():
                    import struct
                    data=file.read_bytes(); width,height=struct.unpack('>II',data[16:24]); scale=min(6.8/width,8.6/height)
                    cx=int(width*scale*914400);cy=int(height*scale*914400); n=len(media)+1; rid=f'rId{n}'
                    media.append((f'image{n}.png',data));rels.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image{n}.png"/>')
                    body+=f'<w:p><w:r><w:drawing><wp:inline><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{n}" name="Figure {n}"/><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="{n}" name="Figure {n}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
                body+=para(block['caption'])
    body+='<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1020" w:right="900" w:bottom="1020" w:left="900"/></w:sectPr>'
    document=f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><w:body>{body}</w:body></w:document>'
    styles=f'''<?xml version="1.0" encoding="UTF-8"?><w:styles xmlns:w="{ns}"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:color w:val="111111"/><w:lang w:val="en-US"/><w:sz w:val="22"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="120"/></w:pPr></w:pPrDefault></w:docDefaults><w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:rPr><w:b/><w:sz w:val="40"/><w:color w:val="111111"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:pPr><w:pageBreakBefore/><w:keepNext/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:sz w:val="32"/><w:color w:val="111111"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:pPr><w:keepNext/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:sz w:val="26"/></w:rPr></w:style></w:styles>'''
    rels.append('<Relationship Id="rStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>')
    with ZipFile(OUT/'report.docx','w',ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','''<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>''')
        z.writestr('_rels/.rels','''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rDoc" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>''')
        z.writestr('word/document.xml',document); z.writestr('word/styles.xml',styles)
        z.writestr('word/_rels/document.xml.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(rels)+'</Relationships>')
        for name,data in media:z.writestr('word/media/'+name,data)
    print('Wrote editable report.docx with',len(media),'figures')


write_docx()
