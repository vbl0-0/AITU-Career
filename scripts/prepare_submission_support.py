"""Build the public screen viewer and submission notes from confirmed local evidence."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/pre-defense-1'
cfg = json.loads((OUT / 'submission.json').read_text(encoding='utf-8'))
validation = json.loads((OUT / 'evidence/validation.json').read_text(encoding='utf-8'))
review = json.loads((OUT / 'evidence/ui-review/review.json').read_text(encoding='utf-8'))
escape = html.escape
repo = cfg['repository_url']
version = repo + '/tree/' + cfg['submission_tag']
counts = json.loads((OUT / 'evidence/github-current-issues.json').read_text(encoding='utf-8'))['counts']
feedback_notice = ('Supervisor feedback received on 24 October 2026 is recorded in Section 11. AI scope, the evaluation protocol and delivery evidence have been clarified; actual GitHub peer review and independent matching evaluation remain planned.' if cfg.get('supervisor_feedback_record') else 'Supervisor feedback is optional and no feedback record is claimed.')

steps = [
    ('Dashboard', 'Readiness explanation, ranked vacancies and skill gaps', '/dashboard'),
    ('Profile', 'Stored personal, career and education fields', '/profile'),
    ('Skills', 'Stored skill levels and editing actions', '/skills'),
    ('Projects', 'Project evidence and technology tags', '/projects'),
    ('Certificates', 'Certificates and their editing actions', '/certificates'),
    ('Experience', 'Employment records and dates', '/experience'),
    ('Vacancies', 'Search, filters and demonstration-data labels', '/jobs'),
    ('Vacancy details', 'Covered, partial and missing requirements', '/jobs/1'),
    ('Saved vacancies', 'Clear empty state and navigation to jobs', '/saved'),
    ('Career recommendations', 'Actions and readiness components from the profile', '/recommendations'),
    ('Administration', 'Role-protected catalogue and vacancy management', '/admin'),
]
sections = []
for number, (title, note, route) in enumerate(steps, 1):
    shots = [r for r in review['records'] if r['route'] == route]
    figures = ''.join('<figure><a href="ui-review/'+escape(r['file'])+'"><img loading="lazy" src="ui-review/'+escape(r['file'])+'" alt="'+escape(title)+' at '+str(r['width'])+' pixels"></a><figcaption>'+str(r['width'])+'px; no horizontal document overflow or blocking page error detected.</figcaption></figure>' for r in shots)
    sections.append('<section><h2>'+str(number)+'. '+escape(title)+' — passed targeted checks</h2><p>'+escape(note)+'. Desktop and mobile captures were inspected together. Stable navigation, page content and original AITU palette are visible.</p><div class="shots">'+figures+'</div></section>')
style = 'body{font:16px/1.6 Arial,sans-serif;color:#171717;max-width:1200px;margin:24px auto;padding:0 18px}a{color:inherit}h1,h2{line-height:1.2}.shots{display:flex;gap:20px;align-items:flex-start}.shots figure{margin:0;max-width:72%}.shots figure:last-child{max-width:26%}img{display:block;max-width:100%;border:1px solid #ddd}section{margin:42px 0}figcaption{font-size:13px} @media(max-width:650px){.shots{display:block}.shots figure,.shots figure:last-child{max-width:100%;margin-bottom:18px}}'
(OUT / 'evidence/ui-review.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AITU Career — targeted UI review</title><style>'+style+'</style><h1>Targeted UI and accessibility review — 24 October 2026</h1><p>Scope: eleven core screens at 1440px and 390px, captured from the actual local application with fictional demo data. All 22 states rendered without horizontal document overflow. Keyboard traversal showed a visible 3px focus outline on the skip link; the Dashboard browser test separately verifies mobile-menu focus trapping and Escape focus restoration.</p><p>Strengths: consistent navy navigation, light content surfaces, explicit demonstration labels, useful empty states, compact profile evidence and visible main actions. Remaining risks: long mobile vacancy/admin lists require scrolling; no claim of a comprehensive contrast, screen-reader, zoom or WCAG-conformance audit is made. The actual browser suite also checks all three interface languages. Review performed with OpenAI Codex assistance; no human teammate or supervisor approval is claimed.</p>'+''.join(sections)+'</html>', encoding='utf-8')

checks = ''.join('<tr><td>'+escape(c['command'])+'</td><td>'+escape(c['result'])+'</td><td>'+escape(str(c.get('count','')))+' '+escape(c.get('note',''))+'</td></tr>' for c in validation['checks'])
(OUT / 'evidence/validation.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>AITU Career verification</title><style>'+style+'table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:10px;text-align:left}</style><h1>Actual verification — 24 October 2026</h1><table><thead><tr><th>Command</th><th>Result</th><th>Details</th></tr></thead><tbody>'+checks+'</tbody></table><h2>Limits</h2><ul>'+''.join('<li>'+escape(x)+'</li>' for x in validation['limitations'])+'</ul><p><a href="ui-review.html">Screen-by-screen targeted UI review</a></p></html>', encoding='utf-8')

names = '\n\n'.join(str(i+1)+') '+m['name']+' — '+m['group']+' — '+m['github']+'\n'+m['contribution'] for i,m in enumerate(cfg['members']))
answers = ('FORM ANSWERS — one representative for both members\n\nTopic:\n'+cfg['title']+'\n\nSupervisor:\n'+cfg['supervisor']+' — '+cfg['supervisor_position']+'\n\n4. Repository URL:\n'+repo+'\n\n5. Tagged project version URL:\n'+version+'\n\n6. Responsibilities and contributions:\n'+names+'\n\nTask references: Ayadil — GitHub issues #7, #9, #12, #14; Zhan — #4, #5, #8, #16, #17. GitHub Projects is used as the permitted tracker alternative; the original YouTrack IDs are retained in issue descriptions. Dates and links document actual publication. No independent initial authorship or human peer approval is inferred from account attribution.\n\n7. Current project status, limitations and next steps:\nThe local React/FastAPI/PostgreSQL prototype implements registration, authentication and roles, graduate profiles and portfolio CRUD, vacancy browsing/saving, weighted skill matching with matched/partial/missing explanations, readiness components, recommendations, administration and Kazakh/Russian/English interfaces. Verification passed: 60 backend tests, 20 browser tests, 459 translation keys, production build and Alembic consistency. The public screen walkthrough is '+cfg['prototype_url']+' . The complete authenticated application is reproducible locally. Vacancies are fictional demonstration data; live HeadHunter access was unavailable. The real embedding model, Docker runtime and independent ranking-quality evaluation have not been exercised. Next phase: independent relevance labels, baseline/latency experiments and authorized live vacancy sourcing. Interviews and supervisor feedback are optional according to the team clarification; none are fabricated.\n\n8. Upload board/task PDF:\ntracker-evidence.pdf (one PDF, maximum 10 MB)\n\n9. Upload consolidated report PDF:\n'+cfg['report_upload_filename']+' (one PDF, maximum 100 MB)\n\nFinal page:\nIts requirements could not be read through the available automated form access. Check it in your normal signed-in browser. Do not treat this preparation as a submitted response. Retain the actual confirmation after submitting before 18:00 UTC+5 on 24 October 2026.\n')
if cfg.get('supervisor_feedback_record'):
    answers = answers.replace('Interviews and supervisor feedback are optional according to the team clarification; none are fabricated.', 'Interviews remain optional and were not conducted. '+feedback_notice)
(OUT / 'FORM_ANSWERS.txt').write_text(answers, encoding='utf-8')

index = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AITU Career — prototype and submission materials</title><style>
*{box-sizing:border-box}body{margin:0;background:#f4f7fb;color:#172b42;font:16px/1.6 'Segoe UI',Arial,sans-serif}header{padding:32px max(20px,calc((100vw - 1160px)/2));background:#102e4b;color:white}header p{max-width:850px;margin-bottom:0}main{max-width:1200px;margin:auto;padding:26px 20px}h1{margin:0;font-size:30px}h2{margin:0 0 12px}a{color:inherit}nav{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}button,.download{font:inherit;border:1px solid #bacbdc;background:white;border-radius:8px;padding:10px 16px;color:#173b5c;cursor:pointer}button[aria-pressed=true]{background:#dcefff;border-color:#0f6cbf}button:focus-visible,a:focus-visible{outline:3px solid #0f6cbf;outline-offset:3px}.panel{padding:22px;background:white;border:1px solid #dce4ee;border-radius:12px;margin-bottom:22px}.notice{border-left:4px solid #0f6cbf;padding:12px 16px;background:#edf6ff}#screen{display:block;max-width:100%;max-height:1000px;margin:auto;border:1px solid #dce4ee}#caption{margin:14px 0 0}.downloads{display:flex;gap:12px;flex-wrap:wrap}.download{text-decoration:none}.small{font-size:14px}footer{margin:28px 0;color:#526579} @media(max-width:600px){header{padding:24px 20px}h1{font-size:25px}.panel{padding:14px}button{padding:9px 12px}}
</style><header><h1>AITU Career</h1><p>AI-based career guidance and employment support for Astana IT University graduates.</p></header><main><section class="panel"><h2>Prototype screen walkthrough</h2><p class="notice">These are actual captures of the local application, with explicitly fictional demo vacancies. This public viewer lets you inspect screens; it does not host authentication, editable profiles, live matching or a backend service.</p><nav aria-label="Choose a prototype screen" id="screens"></nav><a id="full" href="pre-defense-1/prototype/dashboard.png"><img id="screen" src="pre-defense-1/prototype/dashboard.png" alt="Actual AITU Career dashboard screenshot"></a><p id="caption">Dashboard: readiness explanation, ranked vacancies and skill gaps.</p><p class="small">Select a screen above; open the image for full-resolution inspection. The complete application supports Kazakh, Russian and English. <a href="https://github.com/vbl0-0/AITU-Career/blob/prob-period-1/docs/DEVELOPMENT.md">Run the complete API-backed application locally.</a></p></section><section class="panel"><h2>Probationary period 1 materials</h2><div class="downloads"><a class="download" href="pre-defense-1/report.pdf">Report PDF</a><a class="download" href="pre-defense-1/report.docx">Editable Word report</a><a class="download" href="pre-defense-1/report.html">HTML report</a><a class="download" href="pre-defense-1/tracker-evidence.pdf">Board and task PDF</a><a class="download" href="pre-defense-1/evidence/validation.html">Verification evidence</a><a class="download" href="pre-defense-1/evidence/ui-review.html">Screen review</a></div><p><a href="https://github.com/vbl0-0/AITU-Career/tree/prob-period-1/docs/pre-defense-1/diagrams">Editable diagrams and exports</a> · <a href="https://github.com/vbl0-0/AITU-Career/tree/prob-period-1">Submitted repository version</a> · <a href="https://github.com/users/vbl0-0/projects/1">GitHub Project</a></p><p class="small">Implementation tests passed; employment outcomes and real model ranking quality have not been validated. Interviews and supervisor feedback are optional for this submission. AI assistance and actual delivery records are disclosed in the report.</p></section><footer>AITU Career · Two-member diploma project · 24 October 2026</footer></main><script>
const views=[['Dashboard','dashboard.png','Dashboard: readiness explanation, ranked vacancies and skill gaps.'],['Vacancy details','job-detail.png','Vacancy details: demonstration labels and matched, partial and missing requirements.'],['Mobile','mobile.png','Mobile dashboard: the same application at a narrow viewport.'],['Administration','admin.png','Administration: role-protected management in the complete local application.'],['Landing','landing.png','Public entry to the actual graduate journey.']];const nav=document.querySelector('#screens');function select(i){const [title,file,caption]=views[i];document.querySelector('#screen').src='pre-defense-1/prototype/'+file;document.querySelector('#screen').alt='Actual AITU Career '+title+' screenshot';document.querySelector('#full').href='pre-defense-1/prototype/'+file;document.querySelector('#caption').textContent=caption;nav.querySelectorAll('button').forEach((b,j)=>b.setAttribute('aria-pressed',String(i===j)));}views.forEach((v,i)=>{const b=document.createElement('button');b.type='button';b.textContent=v[0];b.setAttribute('aria-pressed',String(i===0));b.onclick=()=>select(i);nav.append(b);});
</script></html>'''
(ROOT / 'docs/index.html').write_text(index, encoding='utf-8')
(ROOT / 'docs/.nojekyll').write_text('', encoding='utf-8')

readme = '''# Probationary period 1 submission

The English report contains an academic title page, submission summary, a detailed contents list, eleven ordered chapters and two appendices. Text is black; screenshot and diagram colors are preserved. Academic tables have white backgrounds and thin horizontal rules. Unknown personal details are not invented.

The PDF has plain Roman front-matter and Arabic chapter page numbers, without the branded AITU Career footer. The Word copy has native headings and an editable contents field; update the contents fields after editing. Personal names use English spelling throughout the report.

- Form report upload: [SE-2425_Kozhabek_ProbPeriod1.pdf](SE-2425_Kozhabek_ProbPeriod1.pdf).
- Editable report: [report.docx](report.docx); [HTML](report.html); [PDF](report.pdf).
- Separate board/task upload: [tracker-evidence.pdf](tracker-evidence.pdf), maximum 10 MB. The compact selection shows the board, complete task table and one completed task per team member; all original screenshots remain in the repository.
- Copy/paste form answers: [FORM_ANSWERS.txt](FORM_ANSWERS.txt).
- Public screen walkthrough: https://vbl0-0.github.io/AITU-Career/ . It is not a hosted backend.
- Exact submission version: https://github.com/vbl0-0/AITU-Career/tree/prob-period-1 .
- [Editable diagrams](diagrams/) and [current verification](evidence/validation.html).

The application source, setup scripts and migration instructions are in the repository. Run the full authenticated application locally with the development guide. Both personal accounts have published deliveries; AI assistance and limitations of authorship attribution are stated in the report.

Interviews and supervisor feedback are optional according to the team's 24 October clarification; none are fabricated. Independent matching-quality evaluation, real embedding-model evaluation, Docker runtime and live HeadHunter access remain separate limitations/next-stage work. The representative still needs to inspect the final form page, upload the two PDFs and retain the actual submission confirmation before 18:00 UTC+5 on 24 October 2026.

Current tracker: {completed} completed issues; {not_planned} optional activities closed as not planned; {open} open issues (#10/#11 are later-stage evaluation, #18 is actual submission). GitHub's built-in closure workflow places both completed and not-planned cards in Done; the state reason distinguishes activities that were not performed.

Current issue state is in [github-current-issues.json](evidence/github-current-issues.json) and the refreshed GitHub screenshots. The dated YouTrack export, `tasks.csv`, `youtrack-plan.json` and 22 October migration snapshot are historical planning/migration evidence, not current completion claims.
'''
readme = readme.format(**counts)
if cfg.get('supervisor_feedback_record'):
    readme += '\n'+feedback_notice+'\n'
(OUT / 'README.md').write_text(readme, encoding='utf-8')
print('Prepared public screen viewer, targeted UI report, validation page, form answers and package README.')
