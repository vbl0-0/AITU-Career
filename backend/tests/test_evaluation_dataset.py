"""Dataset checks reject ambiguous or incomplete ranking evaluation inputs."""
from copy import deepcopy
import hashlib
import json

import pytest
from pydantic import ValidationError

from app.evaluation.dataset import Dataset, dataset_hash, load_dataset


@pytest.fixture
def dataset_payload():
    return {
        'schema_version': 1,
        'dataset_id': 'contract-fixture',
        'kind': 'synthetic',
        'catalog': [{'id': 1, 'name': 'Python', 'aliases': ['Python programming']},
                    {'id': 2, 'name': 'Docker', 'aliases': []}],
        'jobs': [
            {'id': 'python-role', 'title': 'Python developer',
             'requirements': [{'skill_id': 1, 'level': 2, 'weight': 2}]},
            {'id': 'docker-role', 'title': 'Docker developer',
             'requirements': [{'skill_id': 2, 'level': 1, 'weight': 1}]},
        ],
        'profiles': [{'id': 'profile-1', 'split': 'test', 'language': 'en',
                      'candidate_job_ids': ['python-role', 'docker-role'],
                      'skills': [{'skill_id': 1, 'level': 2}],
                      'projects': [{'name': 'API', 'skill_ids': [1], 'description': 'Python API'}]}],
        'judgments': [
            {'profile_id': 'profile-1', 'job_id': 'python-role',
             'ratings': [{'assessor_id': 'synthetic-fixture', 'grade': 3}]},
            {'profile_id': 'profile-1', 'job_id': 'docker-role',
             'ratings': [{'assessor_id': 'synthetic-fixture', 'grade': 0}]},
        ],
    }


def test_loads_valid_dataset_and_hashes_exact_input(dataset_payload, tmp_path):
    path = tmp_path / 'dataset.json'
    data = json.dumps(dataset_payload, ensure_ascii=False, indent=2).encode()
    path.write_bytes(data)
    dataset = load_dataset(path)
    assert dataset.dataset_id == 'contract-fixture'
    assert [item.grade for item in dataset.judgments] == [3, 0]
    assert dataset_hash(path) == hashlib.sha256(data).hexdigest()
    assert dataset.profiles[0].experience == []


@pytest.mark.parametrize('target', ['catalog', 'jobs', 'profiles', 'judgments'])
def test_rejects_empty_required_collections(dataset_payload, target):
    dataset_payload[target] = []
    with pytest.raises(ValidationError):
        Dataset.model_validate(dataset_payload)


@pytest.mark.parametrize('target', ['catalog', 'jobs', 'profiles', 'judgments'])
def test_rejects_duplicate_entities_and_judgment_pairs(dataset_payload, target):
    dataset_payload[target].append(deepcopy(dataset_payload[target][0]))
    with pytest.raises(ValidationError, match='Duplicate'):
        Dataset.model_validate(dataset_payload)


@pytest.mark.parametrize('value', ['3', 3.0, True, -1, 4])
def test_relevance_grades_are_strict_integers_zero_through_three(dataset_payload, value):
    dataset_payload['judgments'][0]['ratings'][0]['grade'] = value
    with pytest.raises(ValidationError):
        Dataset.model_validate(dataset_payload)


@pytest.mark.parametrize('value', ['1', 1.0, True])
def test_catalog_skill_ids_are_strict_integers(dataset_payload, value):
    dataset_payload['catalog'][0]['id'] = value
    with pytest.raises(ValidationError):
        Dataset.model_validate(dataset_payload)


@pytest.mark.parametrize('value', ['1', 1.0, True, 2])
def test_schema_version_does_not_accept_coercion(dataset_payload, value):
    dataset_payload['schema_version'] = value
    with pytest.raises(ValidationError):
        Dataset.model_validate(dataset_payload)


@pytest.mark.parametrize('value', [float('nan'), float('inf'), float('-inf'), 0, -1, '2'])
def test_requirement_weights_are_positive_finite_numbers(dataset_payload, value):
    dataset_payload['jobs'][0]['requirements'][0]['weight'] = value
    with pytest.raises(ValidationError):
        Dataset.model_validate(dataset_payload)


@pytest.mark.parametrize('location', ['requirement', 'profile_skill', 'project_skill', 'candidate',
                                     'judgment_profile', 'judgment_job'])
def test_rejects_unknown_references(dataset_payload, location):
    profile = dataset_payload['profiles'][0]
    if location == 'requirement':
        dataset_payload['jobs'][0]['requirements'][0]['skill_id'] = 99
    elif location == 'profile_skill':
        profile['skills'][0]['skill_id'] = 99
    elif location == 'project_skill':
        profile['projects'][0]['skill_ids'] = [99]
    elif location == 'candidate':
        profile['candidate_job_ids'].append('unknown-role')
    elif location == 'judgment_profile':
        dataset_payload['judgments'][0]['profile_id'] = 'unknown-profile'
    else:
        dataset_payload['judgments'][0]['job_id'] = 'unknown-role'
    with pytest.raises(ValidationError, match='Unknown'):
        Dataset.model_validate(dataset_payload)


def test_requires_labels_for_every_candidate_and_rejects_extra_labels(dataset_payload):
    dataset_payload['judgments'].pop()
    with pytest.raises(ValidationError, match='exactly cover candidate pairs'):
        Dataset.model_validate(dataset_payload)
    dataset_payload['profiles'][0]['candidate_job_ids'] = ['docker-role']
    with pytest.raises(ValidationError, match='extra='):
        Dataset.model_validate(dataset_payload)


@pytest.mark.parametrize('location', ['requirement', 'profile_skill', 'project_skill', 'candidate', 'assessor'])
def test_rejects_duplicates_within_entities(dataset_payload, location):
    profile = dataset_payload['profiles'][0]
    collection = {
        'requirement': dataset_payload['jobs'][0]['requirements'],
        'profile_skill': profile['skills'],
        'project_skill': profile['projects'][0]['skill_ids'],
        'candidate': profile['candidate_job_ids'],
        'assessor': dataset_payload['judgments'][0]['ratings'],
    }[location]
    collection.append(deepcopy(collection[0]))
    with pytest.raises(ValidationError, match='Duplicate'):
        Dataset.model_validate(dataset_payload)


def test_independent_annotations_need_two_distinct_assessors_per_pair(dataset_payload):
    dataset_payload['kind'] = 'independent'
    with pytest.raises(ValidationError, match='two distinct assessors'):
        Dataset.model_validate(dataset_payload)
    for judgment in dataset_payload['judgments']:
        judgment['ratings'] = [{'assessor_id': 'rater-a', 'grade': judgment['ratings'][0]['grade']},
                               {'assessor_id': 'rater-b', 'grade': judgment['ratings'][0]['grade']}]
    dataset = Dataset.model_validate(dataset_payload)
    assert [item.grade for item in dataset.judgments] == [3, 0]


def test_preserves_disagreement_and_requires_an_explicit_final_grade(dataset_payload):
    judgment = dataset_payload['judgments'][0]
    judgment['ratings'] = [{'assessor_id': 'rater-a', 'grade': 3}, {'assessor_id': 'rater-b', 'grade': 1}]
    with pytest.raises(ValidationError, match='Disagreeing ratings'):
        Dataset.model_validate(dataset_payload)
    judgment['adjudicated_grade'] = 2
    dataset = Dataset.model_validate(dataset_payload)
    assert dataset.judgments[0].grade == 2
    assert [item.grade for item in dataset.judgments[0].ratings] == [3, 1]


def test_adjudication_does_not_silently_override_unanimous_ratings(dataset_payload):
    judgment = dataset_payload['judgments'][0]
    judgment['ratings'].append({'assessor_id': 'another-rater', 'grade': 3})
    judgment['adjudicated_grade'] = 0
    with pytest.raises(ValidationError, match='contradicts agreeing ratings'):
        Dataset.model_validate(dataset_payload)


@pytest.mark.parametrize('conflict', ['canonical', 'alias', 'whitespace'])
def test_canonical_and_alias_terms_are_unambiguous_across_skills(dataset_payload, conflict):
    if conflict == 'canonical':
        dataset_payload['catalog'][1]['name'] = 'PYTHON'
    elif conflict == 'alias':
        dataset_payload['catalog'][1]['aliases'] = ['python']
    else:
        dataset_payload['catalog'][1]['aliases'] = ['  Python   programming ']
    with pytest.raises(ValidationError, match='Ambiguous catalog term'):
        Dataset.model_validate(dataset_payload)


@pytest.mark.parametrize('target', ['dataset', 'skill', 'profile', 'judgment'])
def test_forbids_unknown_fields_in_all_input_models(dataset_payload, target):
    obj = {'dataset': dataset_payload, 'skill': dataset_payload['catalog'][0],
           'profile': dataset_payload['profiles'][0], 'judgment': dataset_payload['judgments'][0]}[target]
    obj['unrecognized'] = 'value'
    with pytest.raises(ValidationError, match='Extra inputs are not permitted'):
        Dataset.model_validate(dataset_payload)


@pytest.mark.parametrize('target', ['dataset_id', 'profile_id', 'skill_name', 'alias', 'assessor_id'])
def test_rejects_blank_identity_and_catalog_fields(dataset_payload, target):
    if target == 'dataset_id':
        dataset_payload['dataset_id'] = '  '
    elif target == 'profile_id':
        dataset_payload['profiles'][0]['id'] = '  '
    elif target == 'skill_name':
        dataset_payload['catalog'][0]['name'] = '  '
    elif target == 'alias':
        dataset_payload['catalog'][0]['aliases'] = ['  ']
    else:
        dataset_payload['judgments'][0]['ratings'][0]['assessor_id'] = '  '
    with pytest.raises(ValidationError):
        Dataset.model_validate(dataset_payload)


@pytest.mark.parametrize('text, message', [
    ('{"schema_version": 1, "schema_version": 2}', 'Duplicate JSON object key'),
    ('{"weight": NaN}', 'Non-finite JSON number'),
    ('{"weight": Infinity}', 'Non-finite JSON number'),
])
def test_json_reader_rejects_duplicate_keys_and_nonfinite_constants(tmp_path, text, message):
    path = tmp_path / 'dataset.json'
    path.write_text(text, encoding='utf-8')
    with pytest.raises(ValueError, match=message):
        load_dataset(path)
