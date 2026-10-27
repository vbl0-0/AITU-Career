"""Exercise annotation handoff with fabricated unit-test records, never human evidence."""
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from app.evaluation import annotation
from app.evaluation.dataset import load_dataset
from app.evaluation.runner import run_evaluation


@pytest.fixture
def source_payload():
    return {
        'schema_version': 1, 'dataset_id': 'annotation-unit-fixture-only',
        'kind': 'synthetic', 'provenance': 'Fabricated unit-test cases, not research evidence.',
        'person_groups': {'p-dev': 'person-a', 'p-test': 'person-b'},
        'catalog': [{'id': 1, 'name': 'Python', 'aliases': ['py-lang']},
                    {'id': 2, 'name': 'SQL', 'aliases': []}],
        'jobs': [{'id': 'j-python', 'title': 'Fictional Python role', 'description': 'Python API',
                  'requirements': [{'skill_id': 1, 'level': 2, 'weight': 2.0}]},
                 {'id': 'j-sql', 'title': 'Fictional SQL role',
                  'requirements': [{'skill_id': 2, 'level': 1, 'weight': 1.0}]}],
        'profiles': [{'id': 'p-dev', 'split': 'dev', 'language': 'ru',
                      'candidate_job_ids': ['j-python', 'j-sql'],
                      'skills': [{'skill_id': 2, 'level': 1}]},
                     {'id': 'p-test', 'split': 'test', 'language': 'en',
                      'candidate_job_ids': ['j-python', 'j-sql'],
                      'skills': [{'skill_id': 1, 'level': 2}],
                      'projects': [{'name': 'Fictional exercise', 'description': 'SQL project',
                                    'skill_ids': []}]}],
    }


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')


@pytest.fixture
def source_file(source_payload, tmp_path):
    path = tmp_path / 'source-input.json'
    save_json(path, source_payload)
    return path


@pytest.fixture
def packet(source_file, tmp_path):
    path = tmp_path / 'packet'
    annotation.prepare(source_file, path)
    return path


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def save_csv(path, fields, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sheet(packet, assessor, path, *, disagree=False):
    fields, rows = read_csv(packet / f'assessor-{assessor}.csv')
    grades = {('p-dev', 'j-python'): 0, ('p-dev', 'j-sql'): 1,
              ('p-test', 'j-python'): 2, ('p-test', 'j-sql'): 2}
    if disagree:
        grades['p-test', 'j-python'] = 1
    for row in rows:
        row['grade'] = str(grades[row['profile_id'], row['job_id']])
        row['note'] = f'Unit-test note for {assessor}, quoted "text"\nsecond line'
    save_csv(path, fields, rows)
    return path


@pytest.fixture
def ratings(packet, tmp_path):
    return [sheet(packet, 'R1', tmp_path / 'filled-r1.csv'),
            sheet(packet, 'R2', tmp_path / 'filled-r2.csv', disagree=True)]


def resolved_adjudication(packet, ratings, tmp_path):
    analysis = tmp_path / 'analysis'
    annotation.analyze(packet, ratings, analysis)
    fields, rows = read_csv(analysis / 'adjudication.csv')
    for row in rows:
        row['final_grade'] = '2'
        row['reason'] = 'Unit-test resolution from the supplied evidence.'
    result = tmp_path / 'resolved-adjudication.csv'
    save_csv(result, fields, rows)
    return result


def test_prepare_keeps_every_grade_blank_and_uses_exact_sheet_headers(packet):
    manifest = json.loads((packet / 'manifest.json').read_text())
    assert manifest['grade_scale'] == [0, 1, 2]
    assert manifest['kind'] == 'synthetic'
    assert manifest['rating_status'].startswith('Blank templates')
    for assessor in ['R1', 'R2']:
        fields, rows = read_csv(packet / f'assessor-{assessor}.csv')
        assert fields == annotation.RATING_FIELDS
        assert len(rows) == 4
        assert all(row['grade'] == '' and row['note'] == '' for row in rows)
        assert {row['assessor_id'] for row in rows} == {assessor}
        assert {row['source_sha256'] for row in rows} == {manifest['source_sha256']}
        assert (packet / f'assessor-{assessor}.html').is_file()


def test_prepare_freezes_source_splits_groups_and_a_reproducible_pair_order(source_file, packet, tmp_path):
    second = tmp_path / 'same-seed'
    annotation.prepare(source_file, second, seed=42)
    first_manifest = json.loads((packet / 'manifest.json').read_text())
    second_manifest = json.loads((second / 'manifest.json').read_text())
    assert first_manifest['pairs'] == second_manifest['pairs']
    assert first_manifest['source_sha256'] == second_manifest['source_sha256']
    assert first_manifest['split_profiles'] == {'dev': ['p-dev'], 'test': ['p-test']}
    assert first_manifest['person_groups'] == {'p-dev': 'person-a', 'p-test': 'person-b'}
    assert first_manifest['source_sha256'] == hashlib.sha256((packet / 'source.json').read_bytes()).hexdigest()
    assert (packet / 'assessor-R1.csv').read_bytes() == (second / 'assessor-R1.csv').read_bytes()


@pytest.mark.parametrize('change', ['labels', 'person-leak', 'candidate', 'skill'])
def test_prepare_rejects_scored_or_inconsistent_source_data(source_payload, source_file, tmp_path, change):
    if change == 'labels':
        source_payload['judgments'] = []
    elif change == 'person-leak':
        source_payload['person_groups']['p-test'] = 'person-a'
    elif change == 'candidate':
        source_payload['profiles'][0]['candidate_job_ids'].append('unknown-job')
    else:
        source_payload['jobs'][0]['requirements'][0]['skill_id'] = 999
    save_json(source_file, source_payload)
    output = tmp_path / 'rejected'
    with pytest.raises(ValueError):
        annotation.prepare(source_file, output)
    assert not output.exists()


@pytest.mark.parametrize('assessors', [('R1', 'R1'), ('../escape', 'R2'), ('R1', 'x/y'), ('R1', 'R2', 'R3')])
def test_assessor_pseudonyms_cannot_collide_or_change_file_locations(source_file, tmp_path, assessors):
    with pytest.raises(ValueError):
        annotation.prepare(source_file, tmp_path / 'invalid-assessors', assessors=assessors)


@pytest.mark.parametrize('target', ['source', 'split', 'pairs', 'protocol', 'kind',
                                    'dataset-id', 'provenance', 'weighting', 'seed',
                                    'seed-type', 'order'])
def test_analyze_rejects_modified_frozen_input_or_manifest(packet, ratings, tmp_path, target):
    path = packet / ('source.json' if target == 'source' else 'manifest.json')
    value = json.loads(path.read_text())
    if target == 'source':
        value['jobs'][0]['title'] = 'Changed after freezing'
    elif target == 'split':
        value['split_profiles']['dev'] = ['p-test']
    elif target == 'pairs':
        value['pairs'].pop()
    elif target == 'protocol':
        value['protocol'] = 'another-protocol'
    elif target == 'kind':
        value['kind'] = 'independent'
    elif target == 'dataset-id':
        value['dataset_id'] = 'different-dataset'
    elif target == 'provenance':
        value['provenance'] = 'Changed provenance claim'
    elif target == 'weighting':
        value['agreement_weighting'] = 'linear'
    elif target == 'seed':
        value['seed'] = 43
    elif target == 'seed-type':
        value['seed'] = True
    else:
        value['pairs'].reverse()
    save_json(path, value)
    with pytest.raises(ValueError):
        annotation.analyze(packet, ratings, tmp_path / 'rejected-analysis')


@pytest.mark.parametrize('change', ['missing', 'blank', 'duplicate', 'unknown', 'fingerprint', 'same-assessor'])
def test_rating_handoff_rejects_incomplete_mixed_or_wrong_sheets(packet, ratings, tmp_path, change):
    fields, rows = read_csv(ratings[1])
    if change == 'missing':
        rows.pop()
    elif change == 'blank':
        rows[0]['grade'] = ''
    elif change == 'duplicate':
        rows.append(dict(rows[0]))
    elif change == 'unknown':
        rows[0]['job_id'] = 'unlisted-job'
    elif change == 'fingerprint':
        rows[0]['source_sha256'] = '0' * 64
    else:
        for row in rows:
            row['assessor_id'] = 'R1'
    save_csv(ratings[1], fields, rows)
    output = tmp_path / 'rejected-ratings'
    with pytest.raises(ValueError):
        annotation.analyze(packet, ratings, output)
    assert not output.exists()


def test_analysis_preserves_original_files_and_measures_agreement_before_resolution(packet, ratings, tmp_path):
    original = [path.read_bytes() for path in ratings]
    output = tmp_path / 'analysis'
    result = annotation.analyze(packet, ratings, output)
    assert result['overall']['count'] == 4
    assert result['overall']['exact_agreement'] == .75
    assert result['overall']['quadratic_weighted_kappa'] == pytest.approx(.8)
    assert result['disagreement_count'] == 1
    assert result['by_split']['dev']['count'] == result['by_split']['test']['count'] == 2
    assert result['stage'].startswith('Raw ratings, before adjudication')
    for index, assessor in enumerate(['R1', 'R2']):
        assert ratings[index].read_bytes() == original[index]
        assert (output / f'raw-{assessor}.csv').read_bytes() == original[index]
        assert result['rating_files_sha256'][assessor] == hashlib.sha256(original[index]).hexdigest()
    fields, disputes = read_csv(output / 'adjudication.csv')
    assert fields == ['source_sha256', 'profile_id', 'job_id', 'grade_R1', 'grade_R2', 'final_grade', 'reason']
    assert len(disputes) == 1
    assert disputes[0]['profile_id'] == 'p-test' and disputes[0]['job_id'] == 'j-python'
    assert disputes[0]['grade_R1'] == '2' and disputes[0]['grade_R2'] == '1'
    assert disputes[0]['final_grade'] == disputes[0]['reason'] == ''


def test_finalize_requires_explicit_resolution_for_every_disagreement(packet, ratings, tmp_path):
    output = tmp_path / 'unresolved'
    with pytest.raises(ValueError, match='explicit adjudication'):
        annotation.finalize(packet, ratings, output)
    assert not output.exists()


@pytest.mark.parametrize('change', ['raw-grade', 'blank-reason', 'extra-case', 'missing-case'])
def test_finalize_rejects_tampered_or_incomplete_resolution_records(packet, ratings, tmp_path, change):
    path = resolved_adjudication(packet, ratings, tmp_path)
    fields, rows = read_csv(path)
    if change == 'raw-grade':
        rows[0]['grade_R1'] = '0'
    elif change == 'blank-reason':
        rows[0]['reason'] = '   '
    elif change == 'extra-case':
        rows.append({**rows[0], 'job_id': 'j-sql'})
    else:
        rows.clear()
    save_csv(path, fields, rows)
    output = tmp_path / 'invalid-resolution'
    with pytest.raises(ValueError):
        annotation.finalize(packet, ratings, output, adjudication=path)
    assert not output.exists()


def test_final_dataset_preserves_raw_grades_notes_and_pre_resolution_agreement(packet, ratings, tmp_path):
    adjudication = resolved_adjudication(packet, ratings, tmp_path)
    output = tmp_path / 'compiled'
    result = annotation.finalize(packet, ratings, output, adjudication=adjudication)
    dataset = load_dataset(output / 'dataset.json')
    assert dataset.kind == result['kind'] == 'synthetic'
    assert result['independent_quality_evidence'] is False
    assert len(dataset.judgments) == 4
    disputed = next(j for j in dataset.judgments if (j.profile_id, j.job_id) == ('p-test', 'j-python'))
    assert [(r.assessor_id, r.grade) for r in disputed.ratings] == [('R1', 2), ('R2', 1)]
    assert disputed.adjudicated_grade == disputed.grade == 2
    for original, assessor in zip(ratings, ['R1', 'R2'], strict=True):
        assert (output / f'raw-{assessor}.csv').read_bytes() == original.read_bytes()
        _, rows = read_csv(output / f'raw-{assessor}.csv')
        assert all('quoted "text"\nsecond line' in row['note'] for row in rows)
    assert (output / 'adjudication.csv').read_bytes() == adjudication.read_bytes()
    agreement = json.loads((output / 'agreement.json').read_text())
    assert agreement == json.loads((tmp_path / 'analysis/agreement.json').read_text())
    assert agreement['overall']['exact_agreement'] == .75
    manifest = json.loads((output / 'dataset-manifest.json').read_text())
    assert manifest['dataset_sha256'] == hashlib.sha256((output / 'dataset.json').read_bytes()).hexdigest()
    assert manifest['split_profiles'] == {'dev': ['p-dev'], 'test': ['p-test']}
    assert manifest['adjudication_sha256'] == hashlib.sha256(adjudication.read_bytes()).hexdigest()


def test_agreeing_sheets_export_without_adjudication_and_feed_the_existing_runner(packet, tmp_path):
    paths = [sheet(packet, assessor, tmp_path / f'completed-{assessor}.csv') for assessor in ['R1', 'R2']]
    output = tmp_path / 'agreed-dataset'
    annotation.finalize(packet, paths, output)
    dataset = load_dataset(output / 'dataset.json')
    assert all(j.adjudicated_grade is None for j in dataset.judgments)
    report = run_evaluation(output / 'dataset.json', tmp_path / 'experiment', allow_synthetic=True,
                            repeats=1, warmup=0)
    assert report['dataset_kind'] == 'synthetic'
    assert report['independent_quality_evidence'] is False
    assert set(report['baselines']) == {'B0', 'B1'}


@pytest.mark.parametrize('foreign_name', ['old-result.json', '.annotation.lock'])
def test_prepare_preserves_existing_output_and_foreign_lock(source_file, tmp_path, foreign_name):
    output = tmp_path / 'previous-output'
    output.mkdir()
    foreign = output / foreign_name
    foreign.write_bytes(b'preserve another run')
    with pytest.raises((ValueError, FileExistsError)):
        annotation.prepare(source_file, output)
    assert foreign.read_bytes() == b'preserve another run'
    assert sorted(p.name for p in output.iterdir()) == [foreign_name]


def test_cli_prepare_runs_without_database_jwt_env_file_or_git(source_file, tmp_path):
    isolated = tmp_path / 'isolated-backend'
    isolated.mkdir()
    app = Path(__file__).resolve().parents[1] / 'app'
    shutil.copytree(app, isolated / 'app', ignore=shutil.ignore_patterns('__pycache__'))
    output = tmp_path / 'cli-packet'
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    for name in ['JWT_SECRET', 'DATABASE_URL', 'TEST_DATABASE_URL', 'PYTHONPATH']:
        env.pop(name, None)
    process = subprocess.run([sys.executable, '-m', 'app.evaluation.annotation', 'prepare',
                              '--source', str(source_file), '--output', str(output)],
                             cwd=isolated, env=env, capture_output=True, text=True, encoding='utf-8')
    assert process.returncode == 0, process.stderr
    summary = json.loads(process.stdout)
    assert summary['kind'] == 'synthetic' and summary['grades'] == 'blank' and summary['pairs'] == 4
    assert (output / 'assessor-R1.html').exists()
