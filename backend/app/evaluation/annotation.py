"""Prepare blind annotation sheets and freeze real supplied ratings for task #10."""
import argparse
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import random
import re
import sys
from typing import Literal, Self

from pydantic import Field, field_validator, model_validator
from app.evaluation.agreement import weighted_cohen_kappa
from app.evaluation.dataset import (Dataset, InputModel, Job, NonBlank, Profile, Skill,
    _object_without_duplicate_keys, _reject_json_constant, _term, _unique)

PROTOCOL = 'aitu-relevance-0-2-v1'
RATING_FIELDS = ['source_sha256', 'assessor_id', 'profile_id', 'job_id', 'grade', 'note']


class AnnotationSource(InputModel):
    schema_version: Literal[1]
    dataset_id: NonBlank
    kind: Literal['synthetic', 'independent']
    provenance: NonBlank
    person_groups: dict[NonBlank, NonBlank]
    catalog: list[Skill] = Field(min_length=1)
    jobs: list[Job] = Field(min_length=1)
    profiles: list[Profile] = Field(min_length=1)

    @field_validator('schema_version', mode='before')
    @classmethod
    def strict_version(cls, value):
        if type(value) is not int:
            raise ValueError('schema_version must be integer 1')
        return value

    @model_validator(mode='after')
    def references_and_splits(self) -> Self:
        skills = _unique((s.id for s in self.catalog), 'skill ID')
        jobs = _unique((j.id for j in self.jobs), 'job ID')
        profiles = _unique((p.id for p in self.profiles), 'profile ID')
        terms = {}
        for skill in self.catalog:
            for name in [skill.name, *skill.aliases]:
                term = _term(name)
                if term in terms and terms[term] != skill.id:
                    raise ValueError('Ambiguous catalogue term: ' + name)
                terms[term] = skill.id
        for job in self.jobs:
            if any(r.skill_id not in skills for r in job.requirements):
                raise ValueError('Unknown requirement skill in job ' + job.id)
        if set(self.person_groups) != profiles:
            raise ValueError('person_groups must cover every profile exactly')
        splits = {}
        for profile in self.profiles:
            if any(j not in jobs for j in profile.candidate_job_ids):
                raise ValueError('Unknown candidate job in profile ' + profile.id)
            used = [s.skill_id for s in profile.skills] + [s for p in profile.projects for s in p.skill_ids]
            if any(s not in skills for s in used):
                raise ValueError('Unknown profile skill in ' + profile.id)
            group = self.person_groups[profile.id]
            if group in splits and splits[group] != profile.split:
                raise ValueError('Person group occurs in both dev and test: ' + group)
            splits[group] = profile.split
        return self


def _json(raw):
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=_object_without_duplicate_keys,
                      parse_constant=_reject_json_constant)


def _bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _slug(identifier):
    if not isinstance(identifier, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,39}', identifier):
        raise ValueError('Assessor IDs must be anonymous filename-safe IDs, e.g. R1 and R2')
    return identifier


@contextmanager
def _output(folder):
    folder = Path(folder)
    if folder.exists() and (not folder.is_dir() or any(folder.iterdir())):
        raise ValueError('Output must be a new or empty directory; previous files are preserved')
    folder.mkdir(parents=True, exist_ok=True)
    lock = folder / '.annotation.lock'
    with lock.open('x', encoding='utf-8'):
        pass
    try:
        if any(p != lock for p in folder.iterdir()):
            raise ValueError('Output changed concurrently; no existing file was overwritten')
        yield folder
    finally:
        lock.unlink()


def _write(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)


def _csv(path, fields, rows):
    with path.open('x', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def prepare(source_path, output, assessors=('R1', 'R2'), seed=42):
    if len(assessors) != 2 or len(set(assessors)) != 2:
        raise ValueError('Select exactly two distinct assessor IDs')
    assessors = [_slug(a) for a in assessors]
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    raw = Path(source_path).read_bytes()
    source = AnnotationSource.model_validate(_json(raw))
    frozen = _bytes(source.model_dump())
    fingerprint = _sha(frozen)
    pairs = [(p.id, j) for p in source.profiles for j in p.candidate_job_ids]
    random.Random(seed).shuffle(pairs)
    manifest = {'schema_version': 1, 'protocol': PROTOCOL, 'prepared_at_utc': datetime.now(timezone.utc).isoformat(),
                'dataset_id': source.dataset_id, 'kind': source.kind, 'provenance': source.provenance,
                'input_sha256': _sha(raw), 'source_sha256': fingerprint, 'assessors': assessors,
                'seed': seed, 'grade_scale': [0, 1, 2], 'agreement_weighting': 'quadratic',
                'pairs': [{'profile_id': p, 'job_id': j} for p, j in pairs],
                'split_profiles': {s: sorted(p.id for p in source.profiles if p.split == s) for s in ['dev', 'test']},
                'person_groups': source.person_groups,
                'rating_status': 'Blank templates only; no independent ratings have been supplied.'}
    from app.evaluation.annotation_html import render_annotation_html
    with _output(output) as folder:
        _write(folder / 'source.json', frozen)
        _write(folder / 'manifest.json', _bytes(manifest))
        for assessor in assessors:
            rows = [{'source_sha256': fingerprint, 'assessor_id': assessor, 'profile_id': p,
                     'job_id': j, 'grade': '', 'note': ''} for p, j in pairs]
            _csv(folder / f'assessor-{assessor}.csv', RATING_FIELDS, rows)
            page = render_annotation_html(source.model_dump(), pairs, assessor, fingerprint)
            _write(folder / f'assessor-{assessor}.html', page.encode('utf-8'))
        _write(folder / 'README.txt', ('BLIND ANNOTATION PACKET\n\nGive each assessor only their own HTML and/or CSV, not another assessor\'s ratings.\nGrade 0 = irrelevant, 1 = partly suitable, 2 = suitable. Start with blank grades.\nDo not show algorithm scores. Fill every pair independently before discussion.\nPreserve notes and source_sha256; save downloaded CSV separately.\nAssessor IDs are pseudonyms, not proof of actual people or expertise. Record real identity, qualification and assessment dates privately.\n\nDataset kind: ' + source.kind + '\nProvenance: ' + source.provenance + '\n').encode())
    return manifest


def _packet(folder):
    folder = Path(folder)
    manifest = _json((folder / 'manifest.json').read_bytes())
    raw = (folder / 'source.json').read_bytes()
    source = AnnotationSource.model_validate(_json(raw))
    if manifest.get('schema_version') != 1 or manifest.get('protocol') != PROTOCOL or manifest.get('grade_scale') != [0, 1, 2]:
        raise ValueError('Unsupported or changed annotation protocol')
    if manifest.get('source_sha256') != _sha(raw):
        raise ValueError('Frozen source was modified after packet preparation')
    for field in ['dataset_id', 'kind', 'provenance']:
        if manifest.get(field) != getattr(source, field):
            raise ValueError('Frozen source metadata was modified: ' + field)
    if manifest.get('agreement_weighting') != 'quadratic' or type(manifest.get('seed')) is not int:
        raise ValueError('Frozen agreement configuration or order seed was modified')
    assessors = manifest.get('assessors', [])
    if len(assessors) != 2 or len(set(assessors)) != 2:
        raise ValueError('Packet must declare two distinct assessors')
    for assessor in assessors:
        _slug(assessor)
    expected = {(p.id, j) for p in source.profiles for j in p.candidate_job_ids}
    pairs = [(p['profile_id'], p['job_id']) for p in manifest['pairs']]
    if len(pairs) != len(set(pairs)) or set(pairs) != expected:
        raise ValueError('Packet candidate pairs were modified')
    expected_order = [(p.id, j) for p in source.profiles for j in p.candidate_job_ids]
    random.Random(manifest['seed']).shuffle(expected_order)
    if pairs != expected_order:
        raise ValueError('Frozen case order does not match its recorded seed')
    splits = {s: sorted(p.id for p in source.profiles if p.split == s) for s in ['dev', 'test']}
    if manifest.get('split_profiles') != splits or manifest.get('person_groups') != source.person_groups:
        raise ValueError('Frozen split/person-group manifest was modified')
    return source, manifest, pairs, raw


def _rows(raw, expected_fields):
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline=''))
    if reader.fieldnames is None or len(reader.fieldnames) != len(expected_fields) or set(reader.fieldnames) != set(expected_fields):
        raise ValueError('CSV headers must be: ' + ', '.join(expected_fields))
    rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError('Malformed CSV row')
    return rows


def _grade(value):
    if not isinstance(value, str) or not re.fullmatch('[012]', value.strip()):
        raise ValueError('Every grade must be explicitly filled with 0, 1 or 2; blank is not zero')
    return int(value.strip())


def _ratings(paths, manifest, pairs):
    if len(paths) != 2:
        raise ValueError('Supply exactly two independently filled rating CSV files')
    expected = set(pairs)
    result, raw_files = {}, {}
    for path in paths:
        raw = Path(path).read_bytes()
        rows = _rows(raw, RATING_FIELDS)
        ids = {row['assessor_id'].strip() for row in rows}
        if len(ids) != 1:
            raise ValueError('Each sheet must contain exactly one assessor ID and all candidate pairs')
        assessor = ids.pop()
        if assessor not in manifest['assessors'] or assessor in result:
            raise ValueError('Unknown or duplicate assessor sheet: ' + assessor)
        labels = {}
        for row in rows:
            if row['source_sha256'].strip() != manifest['source_sha256']:
                raise ValueError('Rating sheet belongs to a different frozen source')
            pair = (row['profile_id'].strip(), row['job_id'].strip())
            if pair not in expected or pair in labels:
                raise ValueError('Unknown or duplicate rated pair: ' + str(pair))
            labels[pair] = {'grade': _grade(row['grade']), 'note': row['note']}
        if set(labels) != expected:
            raise ValueError('Rating sheet is incomplete for assessor ' + assessor)
        result[assessor], raw_files[assessor] = labels, raw
    return result, raw_files


def _agreement(source, manifest, pairs, ratings, raw_files):
    first, second = manifest['assessors']
    calculate = lambda items: weighted_cohen_kappa([ratings[first][p]['grade'] for p in items], [ratings[second][p]['grade'] for p in items])
    profile_splits = {p.id: p.split for p in source.profiles}
    return {'protocol': PROTOCOL, 'dataset_id': source.dataset_id, 'dataset_kind': source.kind,
            'source_sha256': manifest['source_sha256'], 'assessors': [first, second],
            'stage': 'Raw ratings, before adjudication; not matching effectiveness.',
            'assessor_identity_status': 'Declared pseudonyms; actual independence and expertise require human verification.',
            'rating_files_sha256': {a: _sha(raw) for a, raw in raw_files.items()},
            'overall': calculate(pairs),
            'by_split': {split: calculate(items) if (items := [p for p in pairs if profile_splits[p[0]] == split]) else None for split in ['dev', 'test']}}


def _adjudication_fields(manifest):
    return ['source_sha256', 'profile_id', 'job_id', *['grade_' + a for a in manifest['assessors']], 'final_grade', 'reason']


def analyze(packet, paths, output):
    source, manifest, pairs, _ = _packet(packet)
    ratings, raw_files = _ratings(paths, manifest, pairs)
    agreement = _agreement(source, manifest, pairs, ratings, raw_files)
    first, second = manifest['assessors']
    disputes = [{'source_sha256': manifest['source_sha256'], 'profile_id': p, 'job_id': j,
                 'grade_' + first: ratings[first][p, j]['grade'], 'grade_' + second: ratings[second][p, j]['grade'],
                 'final_grade': '', 'reason': ''} for p, j in pairs if ratings[first][p, j]['grade'] != ratings[second][p, j]['grade']]
    agreement['disagreement_count'] = len(disputes)
    with _output(output) as folder:
        _write(folder / 'agreement.json', _bytes(agreement))
        _csv(folder / 'adjudication.csv', _adjudication_fields(manifest), disputes)
        for assessor, raw in raw_files.items():
            _write(folder / f'raw-{assessor}.csv', raw)
    return agreement


def finalize(packet, paths, output, adjudication=None):
    source, manifest, pairs, raw_source = _packet(packet)
    ratings, raw_files = _ratings(paths, manifest, pairs)
    agreement = _agreement(source, manifest, pairs, ratings, raw_files)
    first, second = manifest['assessors']
    disputes = {p for p in pairs if ratings[first][p]['grade'] != ratings[second][p]['grade']}
    adjudicated, raw_adjudication = {}, None
    if adjudication is not None:
        raw_adjudication = Path(adjudication).read_bytes()
        for row in _rows(raw_adjudication, _adjudication_fields(manifest)):
            pair = (row['profile_id'].strip(), row['job_id'].strip())
            if pair not in disputes or pair in adjudicated:
                raise ValueError('Unknown, agreeing or duplicate adjudication pair: ' + str(pair))
            if row['source_sha256'].strip() != manifest['source_sha256']:
                raise ValueError('Adjudication belongs to a different frozen source')
            for assessor in [first, second]:
                if _grade(row['grade_' + assessor]) != ratings[assessor][pair]['grade']:
                    raise ValueError('Raw grade was altered in adjudication')
            if not row['reason'].strip():
                raise ValueError('Every adjudication must retain a reason')
            adjudicated[pair] = {'grade': _grade(row['final_grade']), 'reason': row['reason']}
    if set(adjudicated) != disputes:
        raise ValueError('All disagreements require explicit adjudication before dataset export')
    judgments = []
    for p, j in pairs:
        judgment = {'profile_id': p, 'job_id': j, 'ratings': [{'assessor_id': a, 'grade': ratings[a][p, j]['grade']} for a in manifest['assessors']]}
        if (p, j) in adjudicated:
            judgment['adjudicated_grade'] = adjudicated[p, j]['grade']
        judgments.append(judgment)
    payload = source.model_dump(exclude={'provenance', 'person_groups'})
    payload['judgments'] = judgments
    dataset = Dataset.model_validate(payload)
    frozen = _bytes(dataset.model_dump())
    agreement['disagreement_count'] = len(disputes)
    record = {**manifest, 'compiled_at_utc': datetime.now(timezone.utc).isoformat(), 'dataset_sha256': _sha(frozen),
              'rating_files_sha256': {a: _sha(raw) for a, raw in raw_files.items()},
              'adjudication_sha256': _sha(raw_adjudication) if raw_adjudication is not None else None,
              'rating_status': 'Supplied rating records compiled; human identity/independence not certified by the tool.'}
    with _output(output) as folder:
        _write(folder / 'dataset.json', frozen)
        _write(folder / 'source.json', raw_source)
        _write(folder / 'dataset-manifest.json', _bytes(record))
        _write(folder / 'agreement.json', _bytes(agreement))
        for assessor, raw in raw_files.items():
            _write(folder / f'raw-{assessor}.csv', raw)
        if raw_adjudication is not None:
            _write(folder / 'adjudication.csv', raw_adjudication)
    return {'dataset_id': dataset.dataset_id, 'kind': dataset.kind, 'judgments': len(judgments),
            'dataset_sha256': record['dataset_sha256'], 'independent_quality_evidence': False,
            'status': 'Annotations compiled; evaluate separately with task #11.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Blind annotation tools; never invents human ratings.')
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--source', required=True)
    prep.add_argument('--output', required=True)
    prep.add_argument('--assessors', nargs=2, default=['R1', 'R2'])
    prep.add_argument('--seed', type=int, default=42)
    for name in ['analyze', 'finalize']:
        command = commands.add_parser(name)
        command.add_argument('--packet', required=True)
        command.add_argument('--ratings', nargs=2, required=True)
        command.add_argument('--output', required=True)
        if name == 'finalize':
            command.add_argument('--adjudication')
    args = parser.parse_args(argv)
    try:
        if args.command == 'prepare':
            result = prepare(args.source, args.output, args.assessors, args.seed)
            summary = {'kind': result['kind'], 'pairs': len(result['pairs']), 'grades': 'blank', 'output': args.output}
        elif args.command == 'analyze':
            result = analyze(args.packet, args.ratings, args.output)
            summary = {'pairs': result['overall']['count'], 'disagreements': result['disagreement_count'], 'output': args.output}
        else:
            summary = finalize(args.packet, args.ratings, args.output, args.adjudication)
    except (ValueError, OSError, KeyError, TypeError) as error:
        print('Annotation workflow not completed: ' + str(error), file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
