"""Check blind evidence selection, escaping and initially unfilled form controls."""
from html.parser import HTMLParser
import json
import re
import shutil
import subprocess

import pytest

from app.evaluation.annotation_html import HEADERS, render_annotation_html


class Elements(HTMLParser):
    def __init__(self, document):
        super().__init__()
        self.tags = []
        self.feed(document)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


@pytest.fixture
def source():
    return {'dataset_id': 'fixture', 'kind': 'synthetic',
            'catalog': [{'id': 1, 'name': 'Python', 'aliases': ['HIDDEN_ALIAS_MARKER']}],
            'profiles': [{'id': 'p1', 'split': 'HIDDEN_SPLIT_MARKER', 'language': 'en',
                          'candidate_job_ids': ['j1', 'j2'], 'skills': [{'skill_id': 1, 'level': 2}],
                          'projects': [{'name': 'Actual project', 'description': 'Original evidence', 'skill_ids': [1]}],
                          'experience': [{'company': 'Practice lab', 'position': 'Intern', 'description': 'Original experience'}],
                          'certificates': [{'name': 'Original certificate'}]}],
            'jobs': [{'id': 'j1', 'title': 'Python role', 'description': 'Original vacancy text',
                      'requirements': [{'skill_id': 1, 'level': 3, 'weight': 9827.3749, 'required': True}],
                      'score': 'HIDDEN_BASELINE_MARKER'},
                     {'id': 'j2', 'title': 'Other role', 'description': '',
                      'requirements': [{'skill_id': 1, 'level': 1, 'weight': 8234.3921, 'required': False}]}],
            'judgments': [{'grade': 'HIDDEN_JUDGMENT_MARKER'}]}


def render(source, pairs=None):
    return render_annotation_html(source, pairs or [('p1', 'j1'), ('p1', 'j2')], 'R1', 'a' * 64)


def test_only_observable_evidence_is_rendered(source):
    document = render(source)
    for visible in ['Python', 'Intermediate', 'Advanced', 'Required', 'Preferred',
                    'Actual project', 'Original evidence', 'Practice lab', 'Intern',
                    'Original experience', 'Original certificate', 'Original vacancy text']:
        assert visible in document
    for hidden in ['HIDDEN_ALIAS_MARKER', 'HIDDEN_SPLIT_MARKER', 'HIDDEN_BASELINE_MARKER',
                   'HIDDEN_JUDGMENT_MARKER', '9827.3749', '8234.3921']:
        assert hidden not in document


def test_all_grades_and_notes_start_blank(source):
    parsed = Elements(render(source))
    selected = [attrs for tag, attrs in parsed.tags if tag == 'option' and 'selected' in attrs]
    assert selected == [{'value': '', 'selected': None}, {'value': '', 'selected': None}]
    assert sum(tag == 'textarea' for tag, _ in parsed.tags) == 2
    assert sum(tag == 'select' and attrs.get('class') == 'grade' for tag, attrs in parsed.tags) == 2
    assert '0 of 2 rated' in render(source)


def test_exact_csv_columns_and_all_rows_are_exported(source):
    document = render(source)
    match = re.search(r'const HEADERS = (\[.*?\]);', document)
    assert json.loads(match.group(1)) == HEADERS == [
        'source_sha256', 'assessor_id', 'profile_id', 'job_id', 'grade', 'note']
    assert 'currentRows().map(row => [SOURCE_SHA, ASSESSOR' in document
    assert "filter(row => row.grade !== '')" in document  # Progress only; export is not filtered.
    assert 'text.replaceAll(\'"\', \'""\')' in document


def test_untrusted_descriptions_and_script_delimiters_are_safe(source):
    attack = '</script><script>alert(1)</script><img src=x onerror=alert(1)>'
    source['profiles'][0]['projects'][0]['description'] = attack
    source['jobs'][0]['title'] = 'Role " onmouseover="alert(2)'
    document = render_annotation_html(source, [('p1', 'j1')], 'R1</script><script>bad()</script>', '<bad&hash>')
    parsed = Elements(document)
    assert sum(tag == 'script' for tag, _ in parsed.tags) == 1
    assert not any(tag == 'img' for tag, _ in parsed.tags)
    assert '&lt;img src=x onerror=alert(1)&gt;' in document
    assert '\\u003c/script\\u003e' in document
    assert '\\u003cbad\\u0026hash\\u003e' in document
    assert 'Role &quot; onmouseover=&quot;alert(2)' in document


def test_offline_form_has_no_external_resources_or_form_submission(source):
    document = render(source)
    parsed = Elements(document)
    assert not any(tag in {'iframe', 'img', 'form', 'link'} for tag, _ in parsed.tags)
    assert not any('src' in attrs for _, attrs in parsed.tags)
    assert "connect-src 'none'" in document
    assert 'fetch(' not in document and 'XMLHttpRequest' not in document
    assert 'innerHTML' not in document
    assert 'outline:3px solid' in document and '@media(max-width:650px)' in document


def test_pair_order_is_preserved_and_only_first_case_is_visible(source):
    parsed = Elements(render(source, [('p1', 'j2'), ('p1', 'j1')]))
    articles = [attrs for tag, attrs in parsed.tags if tag == 'article']
    assert [attrs['data-job'] for attrs in articles] == ['j2', 'j1']
    assert 'hidden' not in articles[0] and 'hidden' in articles[1]


@pytest.mark.parametrize('pairs', [[], [('p1', 'j1'), ('p1', 'j1')], [('missing', 'j1')], [('p1', 'missing')]])
def test_invalid_pairs_are_rejected(source, pairs):
    with pytest.raises(ValueError):
        render_annotation_html(source, pairs, 'R1', 'a' * 64)


def test_outside_candidate_pool_is_rejected(source):
    source['profiles'][0]['candidate_job_ids'] = ['j1']
    with pytest.raises(ValueError, match='candidate pool'):
        render_annotation_html(source, [('p1', 'j2')], 'R1', 'a' * 64)


def test_browser_storage_is_never_restored_until_the_assessor_clicks(source):
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node is optional for this browser-script regression')
    documents = [render_annotation_html(source, [('p1', 'j1')], assessor, 'a' * 64)
                 for assessor in ['R1', 'R2']]
    scripts = [re.search(r'<script>(.*?)</script>', document, re.S).group(1) for document in documents]
    harness = r'''
const vm = require('node:vm');
const saved = new Map([['aitu-annotation-v1:' + 'a'.repeat(64) + ':R1', JSON.stringify([
  {profile_id:'p1', job_id:'j1', grade:'2', note:'Own saved note'}])]]);
function open(script) {
  const grade = {value:'', addEventListener(){}};
  const note = {value:'', addEventListener(){}};
  const card = {dataset:{profile:'p1',job:'j1'}, querySelector(s){return s === '.grade' ? grade : note;}};
  const controls = new Map();
  const get = s => {
    if (!controls.has(s)) controls.set(s, {value:'', textContent:'', options:[], events:{},
      addEventListener(name, fn){this.events[name] = fn;}});
    return controls.get(s);
  };
  const reads = [];
  vm.runInNewContext(script, {document:{querySelector:get,querySelectorAll:()=>[card]},
    localStorage:{getItem(key){reads.push(key);return saved.get(key) ?? null;},setItem(key,v){saved.set(key,v);}}});
  const initial = {grade:grade.value,note:note.value,reads:reads.length,progress:get('#progress-text').textContent};
  get('#restore-draft').events.click();
  return {initial,after:{grade:grade.value,note:note.value,reads:reads.length,progress:get('#progress-text').textContent}};
}
console.log(JSON.stringify(SCRIPTS.map(open)));
'''.replace('SCRIPTS', json.dumps(scripts))
    result = subprocess.run([node, '-'], input=harness, text=True, capture_output=True, check=True)
    first, second = json.loads(result.stdout)
    assert first['initial'] == {'grade': '', 'note': '', 'reads': 0, 'progress': '0 of 1 rated'}
    assert first['after'] == {'grade': '2', 'note': 'Own saved note', 'reads': 1, 'progress': '1 of 1 rated'}
    assert second['initial'] == {'grade': '', 'note': '', 'reads': 0, 'progress': '0 of 1 rated'}
    assert second['after'] == {'grade': '', 'note': '', 'reads': 1, 'progress': '0 of 1 rated'}
