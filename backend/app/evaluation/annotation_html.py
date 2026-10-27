"""Self-contained, blind annotation sheets with explicit, initially blank ratings."""
import html
import json


LEVELS = {1: 'Beginner', 2: 'Intermediate', 3: 'Advanced'}
HEADERS = ['source_sha256', 'assessor_id', 'profile_id', 'job_id', 'grade', 'note']


def _escape(value):
    return html.escape(str(value), quote=True)


def _json(value):
    # Script elements do not honor HTML entities. Escape their closing-tag delimiter.
    return (json.dumps(value, ensure_ascii=False).replace('&', '\\u0026')
            .replace('<', '\\u003c').replace('>', '\\u003e')
            .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))


def _paragraph(text, empty='Not supplied.'):
    return '<p class="text">' + _escape(text or empty) + '</p>'


def _items(values, empty='None supplied.'):
    return '<ul>' + ''.join('<li>' + value + '</li>' for value in values) + '</ul>' if values else '<p>' + empty + '</p>'


def _profile_details(profile, names):
    skills = [_escape(names[s['skill_id']]) + ' — ' + _escape(LEVELS[s['level']])
              for s in profile.get('skills', [])]
    projects = []
    for project in profile.get('projects', []):
        text = '<strong>' + _escape(project['name']) + '</strong>' + _paragraph(project.get('description', ''))
        if project.get('skill_ids'):
            text += '<p>Technologies: ' + ', '.join(_escape(names[s]) for s in project['skill_ids']) + '</p>'
        projects.append(text)
    experience = ['<strong>' + _escape(item['position']) + '</strong> — ' + _escape(item['company'])
                  + _paragraph(item.get('description', '')) for item in profile.get('experience', [])]
    certificates = [_escape(item['name']) for item in profile.get('certificates', [])]
    return ('<h3>Declared skills</h3>' + _items(skills)
            + '<h3>Projects</h3>' + _items(projects)
            + '<h3>Experience</h3>' + _items(experience)
            + '<h3>Certificates</h3>' + _items(certificates))


def _job_details(job, names):
    requirements = [_escape(names[item['skill_id']]) + ' — ' + _escape(LEVELS[item['level']])
                    + ('; Required' if item.get('required', True) else '; Preferred')
                    for item in job.get('requirements', [])]
    return ('<h3>Description</h3>' + _paragraph(job.get('description', ''))
            + '<h3>Skill requirements</h3>' + _items(requirements, 'No structured requirements supplied; inspect the description.'))


def render_annotation_html(source: dict, pairs: list[tuple[str, str]], assessor_id: str, source_sha256: str) -> str:
    """Render only profile/vacancy evidence; do not serialize the complete source.

    The frozen pair order is supplied by the packet builder. Every opening starts
    blank, even when storage exists. A rater may explicitly restore only their
    own draft for the same assessment by pressing the restore button.
    """
    if not pairs:
        raise ValueError('At least one annotation pair is required')
    if len(set(pairs)) != len(pairs):
        raise ValueError('Annotation pairs must be unique')
    profiles = {profile['id']: profile for profile in source['profiles']}
    jobs = {job['id']: job for job in source['jobs']}
    names = {skill['id']: skill['name'] for skill in source['catalog']}
    cards = []
    for number, (profile_id, job_id) in enumerate(pairs, 1):
        if profile_id not in profiles or job_id not in jobs:
            raise ValueError('Unknown profile or vacancy in annotation pair')
        profile, job = profiles[profile_id], jobs[job_id]
        if job_id not in profile.get('candidate_job_ids', []):
            raise ValueError('Annotation vacancy is outside the fixed candidate pool')
        cards.append(
            '<article class="case" data-profile="' + _escape(profile_id) + '" data-job="' + _escape(job_id) + '"'
            + (' hidden' if number > 1 else '') + '><h2>Case ' + str(number) + '</h2><div class="evidence">'
            + '<section><h3>Profile ' + _escape(profile_id) + '</h3>' + _profile_details(profile, names) + '</section>'
            + '<section><h3>Vacancy ' + _escape(job_id) + ': ' + _escape(job['title']) + '</h3>'
            + _job_details(job, names) + '</section></div><div class="rating">'
            + '<label for="grade-' + str(number) + '">Your relevance grade</label>'
            + '<select class="grade" id="grade-' + str(number) + '">'
            + '<option value="" selected>Choose a grade</option><option value="0">0 — Irrelevant</option>'
            + '<option value="1">1 — Partial fit</option><option value="2">2 — Suitable</option></select>'
            + '<label for="note-' + str(number) + '">Reason or note (optional)</label>'
            + '<textarea class="note" id="note-' + str(number) + '" rows="3"></textarea></div></article>')
    profile_options = ''.join('<option value="' + _escape(identifier) + '">' + _escape(identifier) + '</option>'
                              for identifier in sorted({p for p, _ in pairs}))
    case_options = ''.join('<option value="' + str(i) + '">' + str(i + 1) + ' — ' + _escape(p)
                           + ' / ' + _escape(j) + '</option>' for i, (p, j) in enumerate(pairs))
    css = '''*{box-sizing:border-box}body{margin:0;color:#172b42;background:#f5f7fa;font:16px/1.55 system-ui,sans-serif}
header,main{max-width:1180px;margin:auto;padding:22px 20px}header{border-bottom:1px solid #cbd5df}h1{font-size:26px;margin:0 0 10px}h2{font-size:21px;margin-top:0}h3{font-size:17px;margin:18px 0 7px}p,li{overflow-wrap:anywhere}p{margin:6px 0 14px}.text{white-space:pre-wrap}ul{padding-left:22px}.small{font-size:14px;color:#46596b}.toolbar,.navigation{display:flex;flex-wrap:wrap;gap:12px;align-items:end}.toolbar>div{flex:1 1 240px;min-width:0}label{display:block;font-weight:600;margin:7px 0}select,textarea,button{font:inherit;border:1px solid #7e90a2;border-radius:6px;color:#172b42;background:white;padding:10px;max-width:100%}select,textarea{width:100%}textarea{resize:vertical}button{cursor:pointer}button:disabled{cursor:default;opacity:.5}#download{background:#173b5d;color:white;border-color:#173b5d}button:focus-visible,select:focus-visible,textarea:focus-visible,a:focus-visible{outline:3px solid #1b6e9d;outline-offset:3px}.case{margin:20px 0;background:white;border:1px solid #cbd5df;border-radius:9px;padding:22px}.case[hidden]{display:none}.evidence{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:28px}.evidence>section{min-width:0}.rating{border-top:1px solid #d9e0e7;margin-top:18px;padding-top:12px}progress{width:100%;height:15px;accent-color:#173b5d}.notice{padding:12px 15px;background:#eaf0f6;border-left:4px solid #173b5d}.navigation{margin-top:16px}#position{font-weight:600}.digest{overflow-wrap:anywhere}#storage-status{min-height:1.5em}@media(max-width:650px){header,main{padding:18px 14px}.evidence{grid-template-columns:minmax(0,1fr);gap:8px}.case{padding:16px}.navigation button{flex:1 1 100px}h1{font-size:23px}}'''
    head = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            + '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; script-src \'unsafe-inline\'; connect-src \'none\'; base-uri \'none\'; form-action \'none\'">'
            + '<title>AITU Career — independent relevance annotation</title><style>' + css + '</style></head><body>'
            + '<header><h1>Independent relevance annotation</h1><p>Assessor: <strong>' + _escape(assessor_id) + '</strong></p>'
            + '<p class="small digest">Frozen source SHA-256: ' + _escape(source_sha256) + '</p>'
            + '<p class="notice">Rate each profile–vacancy pair independently. Use only the evidence shown. '
            + 'Do not consult another assessor’s sheet before submitting your original ratings.</p>'
            + '<p><strong>0 — Irrelevant:</strong> unsuitable. <strong>1 — Partial fit:</strong> some relevance with substantial gaps. '
            + '<strong>2 — Suitable:</strong> a suitable opportunity based on the supplied evidence.</p>'
            + '<p class="small">Skill levels: 1 = Beginner; 2 = Intermediate; 3 = Advanced. '
            + 'A blank grade is unfinished and is never treated as zero.</p></header><main>'
            + '<div class="toolbar"><div><label for="profile-filter">Profile filter</label><select id="profile-filter"><option value="">All profiles</option>' + profile_options + '</select></div>'
            + '<div><label for="case-select">Case</label><select id="case-select">' + case_options + '</select></div></div>'
            + '<div class="navigation"><button type="button" id="previous">Previous</button><output id="position" aria-live="polite"></output>'
            + '<button type="button" id="next">Next</button><button type="button" id="ungraded">Next ungraded</button></div>'
            + '<p><output id="progress-text" aria-live="polite">0 of ' + str(len(pairs)) + ' rated</output></p>'
            + '<progress id="progress" value="0" max="' + str(len(pairs)) + '" aria-label="Completed ratings"></progress>'
            + ''.join(cards)
            + '<div class="navigation"><button type="button" id="download">Download my ratings CSV</button>'
            + '<button type="button" id="restore-draft">Restore my saved draft</button></div>'
            + '<p class="small">The download includes every pair, including unfinished rows. Notes are exported exactly as entered; '
            + 'import CSV columns as text in spreadsheet software. Download a copy before closing this page.</p>'
            + '<p id="storage-status" class="small" role="status"></p></main>')
    constants = '<script>\nconst SOURCE_SHA = ' + _json(source_sha256) + ';\nconst ASSESSOR = ' + _json(assessor_id) + ';\nconst HEADERS = ' + _json(HEADERS) + ';\n'
    script = '''const cards = Array.from(document.querySelectorAll('.case'));
const profileFilter = document.querySelector('#profile-filter');
const caseSelect = document.querySelector('#case-select');
const storageStatus = document.querySelector('#storage-status');
const storageKey = 'aitu-annotation-v1:' + SOURCE_SHA + ':' + ASSESSOR;
let visible = cards.map((_, i) => i);
let current = 0;
storageStatus.textContent = 'Grades start blank on every opening. Restore a draft only if it is your own work for this same assessment.';
function currentRows() {
  return cards.map(card => ({profile_id: card.dataset.profile, job_id: card.dataset.job,
    grade: card.querySelector('.grade').value, note: card.querySelector('.note').value}));
}
function updateProgress() {
  const count = currentRows().filter(row => row.grade !== '').length;
  document.querySelector('#progress').value = count;
  document.querySelector('#progress-text').textContent = count + ' of ' + cards.length + ' rated';
}
function saveDraft() {
  try { localStorage.setItem(storageKey, JSON.stringify(currentRows()));
    storageStatus.textContent = 'Draft saved in this browser. Download your CSV to keep a separate copy.';
  } catch (_) { storageStatus.textContent = 'Browser autosave is unavailable. Download your CSV before closing this page.'; }
  updateProgress();
}
function restoreDraft() {
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey) || '[]');
    let restored = 0;
    if (Array.isArray(saved)) {
      const byPair = new Map(saved.filter(row => row && typeof row.profile_id === 'string' && typeof row.job_id === 'string')
        .map(row => [JSON.stringify([row.profile_id, row.job_id]), row]));
      cards.forEach(card => {
        const row = byPair.get(JSON.stringify([card.dataset.profile, card.dataset.job]));
        if (row && ['', '0', '1', '2'].includes(row.grade) && typeof row.note === 'string') {
          card.querySelector('.grade').value = row.grade; card.querySelector('.note').value = row.note;
          restored += 1;
        }
      });
    }
    storageStatus.textContent = restored ? 'Your saved draft was restored. Continue only if these are your own ratings for this same assessment.' : 'No saved draft was found for this assessor and frozen source.';
  } catch (_) { storageStatus.textContent = 'Browser draft storage is unavailable. Your current entries were kept.'; }
  updateProgress();
}
document.querySelector('#restore-draft').addEventListener('click', restoreDraft);
function showCase(index) {
  current = index;
  cards.forEach((card, i) => { card.hidden = i !== current; });
  caseSelect.value = String(current);
  const position = visible.indexOf(current);
  document.querySelector('#position').textContent = 'Case ' + (position + 1) + ' of ' + visible.length;
  document.querySelector('#previous').disabled = position <= 0;
  document.querySelector('#next').disabled = position >= visible.length - 1;
}
profileFilter.addEventListener('change', () => {
  visible = cards.map((_, i) => i).filter(i => !profileFilter.value || cards[i].dataset.profile === profileFilter.value);
  Array.from(caseSelect.options).forEach(option => { option.hidden = !visible.includes(Number(option.value)); });
  showCase(visible[0]);
});
caseSelect.addEventListener('change', () => showCase(Number(caseSelect.value)));
document.querySelector('#previous').addEventListener('click', () => showCase(visible[visible.indexOf(current) - 1]));
document.querySelector('#next').addEventListener('click', () => showCase(visible[visible.indexOf(current) + 1]));
document.querySelector('#ungraded').addEventListener('click', () => {
  const start = visible.indexOf(current);
  const sequence = visible.slice(start + 1).concat(visible.slice(0, start + 1));
  const found = sequence.find(i => cards[i].querySelector('.grade').value === '');
  if (found !== undefined) showCase(found);
  else storageStatus.textContent = 'Every case in the current filter has a grade.';
});
cards.forEach(card => { card.querySelector('.grade').addEventListener('change', saveDraft);
  card.querySelector('.note').addEventListener('input', saveDraft); });
function csvCell(value) {
  const text = String(value ?? '');
  return /[",\\r\\n]/.test(text) ? '"' + text.replaceAll('"', '""') + '"' : text;
}
function buildCsv() {
  const rows = currentRows().map(row => [SOURCE_SHA, ASSESSOR, row.profile_id, row.job_id, row.grade, row.note]);
  return [HEADERS, ...rows].map(row => row.map(csvCell).join(',')).join('\\r\\n') + '\\r\\n';
}
document.querySelector('#download').addEventListener('click', () => {
  const blob = new Blob(['\\ufeff', buildCsv()], {type: 'text/csv;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a'); link.href = url;
  link.download = 'ratings-' + ASSESSOR.replace(/[^a-zA-Z0-9_-]/g, '_') + '.csv';
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
updateProgress(); showCase(visible[0]);
</script></body></html>'''
    return head + constants + script
