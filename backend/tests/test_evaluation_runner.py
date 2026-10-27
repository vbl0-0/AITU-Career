"""Exercise the offline experiment boundary without databases or a real AI model."""
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
from types import SimpleNamespace as N

import pytest

from app.evaluation import runner
from app.evaluation.dataset import Dataset


@pytest.fixture
def payload():
    profiles = [
        {'id': 'profile-test', 'split': 'test', 'language': 'en',
         'candidate_job_ids': ['j-none', 'j-python', 'j-js'],
         'skills': [{'skill_id': 1, 'level': 1}],
         'projects': [{'name': 'Alias evidence', 'description': 'JS development', 'skill_ids': []}]},
        {'id': 'profile-dev', 'split': 'dev', 'language': 'ru',
         'candidate_job_ids': ['j-none', 'j-python', 'j-js'],
         'skills': [], 'projects': []},
    ]
    return {
        'schema_version': 1, 'dataset_id': 'unit-test-only', 'kind': 'synthetic',
        'catalog': [{'id': 1, 'name': 'Python', 'aliases': ['py-lang']},
                    {'id': 2, 'name': 'JavaScript', 'aliases': ['JS development']},
                    {'id': 3, 'name': 'Docker', 'aliases': []}],
        'jobs': [
            {'id': 'j-python', 'title': 'Python role', 'requirements': [
                {'skill_id': 1, 'level': 3, 'weight': 3.0},
                {'skill_id': 3, 'level': 1, 'weight': 1.0}]},
            {'id': 'j-js', 'title': 'JavaScript role', 'requirements': [
                {'skill_id': 2, 'level': 1, 'weight': 1.0}]},
            {'id': 'j-none', 'title': 'Unscorable role', 'description': 'Unspecified duties'},
        ],
        'profiles': profiles,
        'judgments': [
            {'profile_id': profile['id'], 'job_id': job_id,
             'ratings': [{'assessor_id': 'synthetic-test-fixture', 'grade': grade}]}
            for profile in profiles
            for job_id, grade in [('j-none', 0), ('j-python', 2), ('j-js', 3)]
        ],
    }


@pytest.fixture
def dataset_file(payload, tmp_path):
    path = tmp_path / 'dataset.json'
    path.write_text(json.dumps(payload), encoding='utf-8')
    return path


def save(path, payload):
    path.write_text(json.dumps(payload), encoding='utf-8')


def experiment(path, output, **overrides):
    options = {'allow_synthetic': True, 'repeats': 2, 'warmup': 0}
    options.update(overrides)
    return runner.run_evaluation(path, output, **options)


def csv_rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def test_real_production_weights_levels_and_alias_evidence_change_the_baseline_order(payload):
    dataset = Dataset.model_validate(payload)
    profile = dataset.profiles[0]
    jobs = {job.id: job for job in dataset.jobs}
    catalog = runner._catalog(dataset)
    exact = runner.rank_profile(profile, jobs, catalog, 'B0')
    weighted = runner.rank_profile(profile, jobs, catalog, 'B1')
    assert exact == [{'job_id': 'j-python', 'score': 50.0},
                     {'job_id': 'j-js', 'score': 0.0},
                     {'job_id': 'j-none', 'score': None}]
    assert weighted == [{'job_id': 'j-js', 'score': 50.0},
                        {'job_id': 'j-python', 'score': 25.0},
                        {'job_id': 'j-none', 'score': None}]


@pytest.mark.parametrize('baseline', ['B0', 'B1'])
def test_equal_scores_are_sorted_by_job_id_independently_of_candidate_order(payload, baseline):
    dataset = Dataset.model_validate(payload)
    profile = dataset.profiles[1]
    result = runner.rank_profile(profile, {job.id: job for job in dataset.jobs}, runner._catalog(dataset), baseline)
    assert result == [{'job_id': 'j-js', 'score': 0.0},
                      {'job_id': 'j-python', 'score': 0.0},
                      {'job_id': 'j-none', 'score': None}]


def test_exact_baseline_uses_case_insensitive_whole_canonical_terms(payload):
    payload['profiles'][0]['skills'] = []
    payload['profiles'][0]['projects'][0]['description'] = 'PYTHON and JavaScript'
    dataset = Dataset.model_validate(payload)
    result = runner.rank_profile(dataset.profiles[0], {job.id: job for job in dataset.jobs}, runner._catalog(dataset), 'B0')
    assert result[0] == {'job_id': 'j-js', 'score': 100.0}
    assert result[1] == {'job_id': 'j-python', 'score': 50.0}
    assert runner._canonical_ids('JavaScript', [N(id=4, name='Java')]) == set()


def test_experiment_exports_hashes_scores_latency_and_unscorable_rows(dataset_file, tmp_path, monkeypatch):
    # Any settings load would require JWT/application configuration; B0/B1 must not use it.
    def forbid_settings():
        raise AssertionError('Offline B0/B1 evaluation must not load application settings')
    monkeypatch.setattr(runner.matching, 'get_settings', forbid_settings)
    output = tmp_path / 'result'
    report = experiment(dataset_file, output)
    assert set(path.name for path in output.iterdir()) == {'report.json', 'queries.csv', 'rankings.csv', 'latencies.csv'}
    assert json.loads((output / 'report.json').read_text(encoding='utf-8')) == report
    assert report['dataset_id'] == 'unit-test-only'
    assert report['dataset_kind'] == 'synthetic'
    assert report['dataset_sha256'] == hashlib.sha256(dataset_file.read_bytes()).hexdigest()
    assert len(report['catalog_sha256']) == len(report['config_sha256']) == 64
    assert len(report['runtime']['source_sha256']) == 4
    assert all(len(value) == 64 for value in report['runtime']['source_sha256'].values())
    assert report['config']['split'] == 'test'
    assert report['config']['precision_denominator'] == 5
    assert report['independent_quality_evidence'] is False
    assert report['complete_B0_B1_B2_comparison'] is False
    assert report['semantic']['status'] == 'not_run'
    assert 'Synthetic pipeline test only' in report['annotation_status']
    assert all(summary['query_count'] == 1 for summary in report['baselines'].values())
    assert all(summary['latency_samples'] == 2 for summary in report['baselines'].values())
    assert all(summary['latency_p95_ms'] >= 0 for summary in report['baselines'].values())
    assert report['baselines']['B1']['ndcg_at_k'] == pytest.approx(1)
    assert report['baselines']['B0']['ndcg_at_k'] < 1
    assert report['baselines']['B0']['precision_at_k'] == pytest.approx(2 / 5)
    queries = csv_rows(output / 'queries.csv')
    assert len(queries) == 2
    assert {row['profile_id'] for row in queries} == {'profile-test'}
    assert {row['candidate_count'] for row in queries} == {'3'}
    assert {row['scored_count'] for row in queries} == {'2'}
    rankings = csv_rows(output / 'rankings.csv')
    assert len(rankings) == 6
    assert all(row['rank'] == row['score'] == '' for row in rankings if row['job_id'] == 'j-none')
    assert len(csv_rows(output / 'latencies.csv')) == 4


@pytest.mark.parametrize('split, expected', [('test', 'profile-test'), ('dev', 'profile-dev')])
def test_explicit_split_is_respected_without_resampling(dataset_file, tmp_path, split, expected):
    output = tmp_path / 'result'
    report = experiment(dataset_file, output, split=split, baselines=('B1',))
    assert report['config']['split'] == split
    assert {row['profile_id'] for row in csv_rows(output / 'queries.csv')} == {expected}


def test_zero_ideal_gain_is_reported_separately_in_macro_aggregation(payload, dataset_file, tmp_path):
    for judgment in payload['judgments']:
        judgment['ratings'][0]['grade'] = 0
    save(dataset_file, payload)
    report = experiment(dataset_file, tmp_path / 'result', baselines=('B1',))
    summary = report['baselines']['B1']
    assert summary['precision_at_k'] == 0
    assert summary['ndcg_at_k'] is None
    assert summary['ndcg_query_count'] == 0
    assert summary['zero_ideal_gain_query_count'] == 1


def test_synthetic_dataset_requires_explicit_permission_before_any_output(dataset_file, tmp_path):
    output = tmp_path / 'result'
    with pytest.raises(ValueError, match='allow-synthetic'):
        experiment(dataset_file, output, allow_synthetic=False)
    assert not output.exists()


def test_declared_independent_annotations_remain_subject_to_human_verification(payload, dataset_file, tmp_path):
    # These ratings are unit-test input, not a genuine independently annotated dataset.
    payload['kind'] = 'independent'
    for judgment in payload['judgments']:
        grade = judgment['ratings'][0]['grade']
        judgment['ratings'] = [{'assessor_id': 'test-rater-a', 'grade': grade},
                               {'assessor_id': 'test-rater-b', 'grade': grade}]
    save(dataset_file, payload)
    report = experiment(dataset_file, tmp_path / 'result', allow_synthetic=False)
    assert report['dataset_kind'] == 'independent'
    assert report['independent_quality_evidence'] is True
    assert report['assessor_ids'] == ['test-rater-a', 'test-rater-b']
    assert 'identities/provenance still require human verification' in report['annotation_status']


def test_existing_output_is_preserved(dataset_file, tmp_path):
    output = tmp_path / 'result'
    output.mkdir()
    existing = output / 'report.json'
    existing.write_text('previous results', encoding='utf-8')
    with pytest.raises(ValueError, match='previous results are preserved'):
        experiment(dataset_file, output)
    assert existing.read_text(encoding='utf-8') == 'previous results'
    assert list(output.iterdir()) == [existing]


@pytest.mark.parametrize('overrides', [{'repeats': 0}, {'repeats': True}, {'warmup': -1},
                                       {'baselines': ('B1', 'B1')}])
def test_invalid_run_configuration_creates_no_artifacts(dataset_file, tmp_path, overrides):
    output = tmp_path / 'result'
    with pytest.raises(ValueError):
        experiment(dataset_file, output, **overrides)
    assert not output.exists()


def test_incomplete_candidate_judgments_stop_the_run(payload, dataset_file, tmp_path):
    payload['judgments'].pop()
    save(dataset_file, payload)
    output = tmp_path / 'result'
    with pytest.raises(ValueError, match='exactly cover candidate pairs'):
        experiment(dataset_file, output)
    assert not output.exists()


def test_empty_selected_split_stops_the_run(payload, dataset_file, tmp_path):
    payload['profiles'][0]['split'] = 'dev'
    save(dataset_file, payload)
    output = tmp_path / 'result'
    with pytest.raises(ValueError, match='No profiles in selected split'):
        experiment(dataset_file, output)
    assert not output.exists()


@pytest.mark.parametrize('enabled, error', [(False, 'requires SEMANTIC_ENABLED'), (True, 'unavailable locally')])
def test_disabled_or_unavailable_b2_is_never_reported_as_evaluated(dataset_file, tmp_path, monkeypatch, enabled, error):
    monkeypatch.setattr(runner.matching, 'get_settings', lambda: N(semantic_enabled=enabled))
    monkeypatch.setattr(runner.matching, 'semantic_model', lambda: None)
    output = tmp_path / 'result'
    handlers = list(runner.matching.LOGGER.handlers)
    with pytest.raises(ValueError, match=error):
        experiment(dataset_file, output, baselines=('B0', 'B1', 'B2'))
    assert not output.exists()
    assert runner.matching.LOGGER.handlers == handlers


@pytest.mark.parametrize('warmup', [0, 1])
def test_runtime_semantic_fallback_warning_aborts_before_any_result_is_written(dataset_file, tmp_path, monkeypatch, warmup):
    # Controlled guard test only: no genuine B2 model or model result is claimed.
    monkeypatch.setattr(runner, '_semantic_metadata', lambda: {'test_guard_metadata': True})
    original = runner.rank_profile

    def failed_semantics(profile, jobs, catalog, baseline):
        if baseline == 'B2':
            runner.matching.LOGGER.warning('Semantic inference failed; using keyword fallback')
            return original(profile, jobs, catalog, 'B1')
        return original(profile, jobs, catalog, baseline)

    monkeypatch.setattr(runner, 'rank_profile', failed_semantics)
    output = tmp_path / 'result'
    with pytest.raises(ValueError, match='No keyword fallback may be reported as B2'):
        experiment(dataset_file, output, baselines=('B2',), warmup=warmup)
    assert not output.exists()


def test_changing_rankings_between_repeats_fail_without_output(dataset_file, tmp_path, monkeypatch):
    original = runner.rank_profile
    calls = 0

    def changing_rankings(profile, jobs, catalog, baseline):
        nonlocal calls
        calls += 1
        result = original(profile, jobs, catalog, baseline)
        result[0]['score'] += calls
        return result

    monkeypatch.setattr(runner, 'rank_profile', changing_rankings)
    output = tmp_path / 'result'
    with pytest.raises(ValueError, match='Ranking changed between repeats'):
        experiment(dataset_file, output, baselines=('B1',))
    assert not output.exists()


def test_cli_runs_in_isolated_copy_without_env_jwt_database_or_git(dataset_file, tmp_path):
    backend = Path(__file__).resolve().parents[1]
    isolated = tmp_path / 'isolated' / 'backend'
    shutil.copytree(backend / 'app', isolated / 'app', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    env = dict(os.environ)
    for name in ['JWT_SECRET', 'DATABASE_URL', 'TEST_DATABASE_URL', 'SEMANTIC_ENABLED', 'SEMANTIC_MODEL']:
        env.pop(name, None)
    env['PYTHONPATH'] = str(isolated)
    output = tmp_path / 'result'
    arguments = [sys.executable, '-m', 'app.evaluation', '--dataset', str(dataset_file),
                 '--output', str(output), '--repeats', '1', '--warmup', '0']
    denied = subprocess.run(arguments, cwd=isolated, env=env, capture_output=True, text=True, timeout=30)
    assert denied.returncode == 2
    assert 'allow-synthetic' in denied.stderr
    assert 'Traceback' not in denied.stderr
    assert not output.exists()
    completed = subprocess.run(arguments + ['--allow-synthetic'], cwd=isolated, env=env,
                               capture_output=True, text=True, timeout=30)
    assert completed.returncode == 0, completed.stderr
    summary = json.loads(completed.stdout)
    assert summary['dataset_kind'] == 'synthetic'
    assert summary['independent_quality_evidence'] is False
    assert summary['baselines'] == ['B0', 'B1']
    report = json.loads((output / 'report.json').read_text(encoding='utf-8'))
    assert report['runtime']['git_commit'] is None
    assert report['semantic']['status'] == 'not_run'


def test_dataset_hash_identifies_loaded_bytes_if_input_changes_during_ranking(dataset_file, tmp_path, monkeypatch):
    loaded_bytes = dataset_file.read_bytes()
    original = runner.rank_profile
    changed = False

    def mutate_input_after_scoring(profile, jobs, catalog, baseline):
        nonlocal changed
        result = original(profile, jobs, catalog, baseline)
        if not changed:
            dataset_file.write_bytes(b'{"changed_after_loading": true}')
            changed = True
        return result

    monkeypatch.setattr(runner, 'rank_profile', mutate_input_after_scoring)
    report = experiment(dataset_file, tmp_path / 'result')
    assert changed
    assert report['dataset_sha256'] == hashlib.sha256(loaded_bytes).hexdigest()
    assert report['dataset_sha256'] != hashlib.sha256(dataset_file.read_bytes()).hexdigest()
    assert report['dataset_id'] == 'unit-test-only'
    assert report['baselines']['B1']['ndcg_at_k'] == pytest.approx(1)


def test_concurrent_output_writer_is_preserved_without_partial_experiment_files(dataset_file, tmp_path, monkeypatch):
    original = runner.rank_profile
    output = tmp_path / 'result'
    foreign = output / 'report.json'
    foreign_bytes = b'{"written_by_another_process": true}'

    def concurrent_writer(profile, jobs, catalog, baseline):
        result = original(profile, jobs, catalog, baseline)
        if not foreign.exists():
            output.mkdir()
            foreign.write_bytes(foreign_bytes)
        return result

    monkeypatch.setattr(runner, 'rank_profile', concurrent_writer)
    with pytest.raises(ValueError, match='Output is no longer empty'):
        experiment(dataset_file, output)
    assert foreign.read_bytes() == foreign_bytes
    assert list(output.iterdir()) == [foreign]


def test_another_process_output_lock_is_not_removed(dataset_file, tmp_path, monkeypatch):
    original = runner.rank_profile
    output = tmp_path / 'result'
    foreign_lock = output / '.evaluation.lock'

    def concurrent_lock(profile, jobs, catalog, baseline):
        result = original(profile, jobs, catalog, baseline)
        if not foreign_lock.exists():
            output.mkdir()
            foreign_lock.write_text('owned by another process', encoding='utf-8')
        return result

    monkeypatch.setattr(runner, 'rank_profile', concurrent_lock)
    with pytest.raises(FileExistsError):
        experiment(dataset_file, output)
    assert foreign_lock.read_text(encoding='utf-8') == 'owned by another process'
    assert list(output.iterdir()) == [foreign_lock]


def test_source_change_during_run_prevents_publishing_mixed_revision_results(dataset_file, tmp_path, monkeypatch):
    original = runner._source_metadata
    calls = 0

    def changed_source_metadata():
        nonlocal calls
        calls += 1
        metadata = original()
        if calls > 1:
            metadata['source_sha256']['evaluation/runner.py'] = 'f' * 64
        return metadata

    monkeypatch.setattr(runner, '_source_metadata', changed_source_metadata)
    output = tmp_path / 'result'
    with pytest.raises(ValueError, match='source files changed during the run'):
        experiment(dataset_file, output)
    assert calls == 2
    assert not output.exists()


@pytest.fixture
def controlled_semantic_model(monkeypatch):
    """Tiny API fakes test fingerprint sensitivity, never genuine AI quality."""
    class Tensor:
        dtype = 'float32'
        shape = (2,)

        def __init__(self):
            self.values = [1.0, 2.0]

        def detach(self):
            return self

        def cpu(self):
            return self

        def contiguous(self):
            return self

        def numpy(self):
            return N(tobytes=lambda: struct.pack('<2f', *self.values))

    class Encoder:
        def __init__(self):
            self.tokenizer = N(backend_tokenizer=N(to_str=lambda: '{"test_tokenizer":1}'))
            self.auto_model = N(config=N(to_dict=lambda: {'model_type': 'controlled-unit-test'}))

        def get_config_dict(self):
            return {'max_seq_length': 128}

    class Pooling:
        def __init__(self):
            self.config = {'pooling_mode_mean_tokens': True, 'pooling_mode_cls_token': False}

        def get_config_dict(self):
            return dict(self.config)

    class Model:
        device = 'cpu'
        max_seq_length = 128

        def __init__(self):
            self.tensor = Tensor()
            self.encoder = Encoder()
            self.pooling = Pooling()

        def state_dict(self):
            return {'encoder.weight': self.tensor}

        def modules(self):
            return [self, self.encoder, self.pooling]

        def named_children(self):
            return [('0', self.encoder), ('1', self.pooling)]

        def get_sentence_embedding_dimension(self):
            return 2

    model = Model()
    settings = N(semantic_enabled=True, semantic_model='controlled-test-only', semantic_threshold=0.85)
    monkeypatch.setattr(runner.matching, 'get_settings', lambda: settings)
    monkeypatch.setattr(runner.matching, 'semantic_model', lambda: model)
    return model


def test_semantic_config_fingerprint_changes_when_pooling_changes(controlled_semantic_model):
    before = runner._semantic_metadata()
    controlled_semantic_model.pooling.config['pooling_mode_mean_tokens'] = False
    controlled_semantic_model.pooling.config['pooling_mode_cls_token'] = True
    after = runner._semantic_metadata()
    assert after['config_sha256'] != before['config_sha256']
    assert after['weights_sha256'] == before['weights_sha256']
    assert after['device'] == 'cpu'
    assert [module['name'] for module in after['modules']] == ['0', '1']
    assert after['modules'][0]['config']['transformer_config'] == {'model_type': 'controlled-unit-test'}


def test_semantic_weight_fingerprint_changes_even_when_config_is_identical(controlled_semantic_model):
    before = runner._semantic_metadata()
    controlled_semantic_model.tensor.values[0] = 7.5
    after = runner._semantic_metadata()
    assert after['weights_sha256'] != before['weights_sha256']
    assert after['config_sha256'] == before['config_sha256']


@pytest.mark.parametrize('weights', [(1e308, 1e308), (1e308, 1.0)])
def test_finite_weights_that_overflow_production_arithmetic_cannot_publish_scores(payload, dataset_file, tmp_path, weights):
    # Both inputs are finite: one overflows the sum and one the percentage
    # multiplication. The production matcher must never yield NaN/Infinity CSVs.
    for requirement, weight in zip(payload['jobs'][0]['requirements'], weights):
        requirement['weight'] = weight
        requirement['level'] = 1
    Dataset.model_validate(payload)
    save(dataset_file, payload)
    output = tmp_path / 'result'
    with pytest.raises(ValueError, match='Invalid matching score for j-python'):
        experiment(dataset_file, output, baselines=('B1',))
    assert not output.exists()
