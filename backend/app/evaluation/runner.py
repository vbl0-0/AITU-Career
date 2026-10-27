"""Reproducible, fully judged ranking experiments using the production matcher."""
import csv
import hashlib
import importlib.metadata
import json
import logging
import math
import platform
import re
import statistics
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace as N

from app.ai import matching
from app.evaluation.dataset import parse_dataset
from app.evaluation.metrics import evaluate_ranking, percentile

RUNNER_VERSION = 'matching-evaluation-1.0'
BASELINES = {'B0': 'Exact canonical skill overlap',
             'B1': 'Production weighted skills, aliases and proficiency',
             'B2': 'Production weighted skills with the real semantic model'}


def _hash_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _catalog(dataset):
    return [N(id=s.id, name=s.name, aliases=[N(name=a) for a in s.aliases]) for s in dataset.catalog]


def _profile(profile, catalog):
    by_id = {s.id: s for s in catalog}
    return N(skills=[N(skill=by_id[s.skill_id], level=s.level) for s in profile.skills],
             projects=[N(name=p.name, description=p.description,
                         technologies=[N(skill=by_id[s]) for s in p.skill_ids]) for p in profile.projects],
             experience=[N(**x.model_dump()) for x in profile.experience],
             certificates=[N(**x.model_dump()) for x in profile.certificates])


def _canonical_ids(text, catalog):
    return {s.id for s in catalog if re.search(r'(?<![\w+#])' + re.escape(s.name) + r'(?![\w+#])', text, re.I)}


def _requirements(job, catalog, exact=False):
    by_id = {s.id: s for s in catalog}
    if job.requirements:
        return [{**r.model_dump(), 'name': by_id[r.skill_id].name} for r in job.requirements]
    skills = ([s for s in catalog if s.id in _canonical_ids(job.description, catalog)] if exact
              else matching.extract_skills(job.description, catalog))
    return [{'skill_id': s.id, 'name': s.name, 'required': True, 'level': 1, 'weight': 2.0} for s in skills]


def rank_profile(profile, jobs, catalog, baseline):
    """Include every fixed candidate; do not recommend candidates without a score."""
    if baseline not in BASELINES:
        raise ValueError('Unknown baseline: ' + baseline)
    available = None
    if baseline == 'B0':
        known = {s.skill_id for s in profile.skills}
        for project in profile.projects:
            known.update(project.skill_ids)
            known.update(_canonical_ids(project.description, catalog))
        for experience in profile.experience:
            known.update(_canonical_ids(experience.position + ' ' + experience.description, catalog))
        for certificate in profile.certificates:
            known.update(_canonical_ids(certificate.name, catalog))
    else:
        available = matching.competencies(_profile(profile, catalog), catalog)
    result = []
    for job_id in profile.candidate_job_ids:
        requirements = _requirements(jobs[job_id], catalog, exact=baseline == 'B0')
        if baseline == 'B0':
            score = round(100 * sum(r['skill_id'] in known for r in requirements) / len(requirements), 1) if requirements else None
        else:
            score = matching.score_requirements(available, requirements, semantic=baseline == 'B2',
                                                 strict_semantic=baseline == 'B2')['score']
        if score is not None and (not math.isfinite(score) or not 0 <= score <= 100):
            raise ValueError('Invalid matching score for ' + job_id + '; check requirement weights and scoring inputs.')
        result.append({'job_id': job_id, 'score': score})
    return sorted(result, key=lambda item: (item['score'] is None, -(item['score'] or 0), item['job_id']))


class _SemanticGuard(logging.Handler):
    """Turn the production adapter's explicit fallback warnings into a failed B2 run."""
    def __init__(self):
        super().__init__(logging.WARNING)
        self.failed = False

    def emit(self, record):
        self.failed = True

    def check(self):
        if self.failed:
            raise ValueError('B2 semantic inference failed. No keyword fallback may be reported as B2.')


def _semantic_metadata():
    settings = matching.get_settings()
    if not settings.semantic_enabled:
        raise ValueError('B2 requires SEMANTIC_ENABLED=true and a locally installed real model.')
    started = time.perf_counter()
    model = matching.semantic_model()
    if model is None:
        raise ValueError('B2 model is unavailable locally; B2 was not evaluated.')
    # Load and fingerprint actual weights, rather than hashing only a model name.
    digest = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        value = tensor.detach().cpu().contiguous()
        digest.update(name.encode())
        digest.update(str(value.dtype).encode())
        digest.update(str(tuple(value.shape)).encode())
        digest.update(value.numpy().tobytes())
    tokenizers = []
    for module in model.modules():
        tokenizer = getattr(module, 'tokenizer', None)
        backend = getattr(tokenizer, 'backend_tokenizer', None)
        if backend is not None:
            tokenizers.append(backend.to_str())
    if not tokenizers:
        raise ValueError('Cannot fingerprint the B2 tokenizer; no reproducible B2 result was produced.')
    modules = []
    for name, module in model.named_children():
        module_config = module.get_config_dict() if hasattr(module, 'get_config_dict') else {}
        auto_model = getattr(module, 'auto_model', None)
        if auto_model is not None:
            module_config = {**module_config, 'transformer_config': auto_model.config.to_dict()}
        modules.append({'name': name, 'class': type(module).__module__ + '.' + type(module).__qualname__,
                        'config': module_config})
    config = {'model': settings.semantic_model, 'threshold': settings.semantic_threshold,
              'embedding_dimension': model.get_sentence_embedding_dimension(),
              'device': str(model.device), 'modules': modules,
              'prompts': getattr(model, 'prompts', {}),
              'default_prompt_name': getattr(model, 'default_prompt_name', None),
              'truncate_dim': getattr(model, 'truncate_dim', None),
              'max_seq_length': model.max_seq_length, 'tokenizers_sha256': _hash_json(tokenizers)}
    return {**config, 'weights_sha256': digest.hexdigest(), 'config_sha256': _hash_json(config),
            'startup_and_fingerprint_ms': (time.perf_counter() - started) * 1000}


def _source_metadata():
    backend = Path(__file__).resolve().parents[2]
    paths = ['ai/matching.py', 'evaluation/runner.py', 'evaluation/dataset.py', 'evaluation/metrics.py']
    source = {p: hashlib.sha256((backend / 'app' / p).read_bytes()).hexdigest() for p in paths}
    # Only version metadata is read; no environment variables or credentials are exported.
    try:
        sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=backend, stderr=subprocess.DEVNULL).decode().strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--', 'backend/app/ai', 'backend/app/evaluation'], cwd=backend.parents[0], stderr=subprocess.DEVNULL).strip())
    except (OSError, subprocess.CalledProcessError):
        sha, dirty = None, None
    versions = {}
    for package in ['pydantic', 'sentence-transformers', 'torch', 'numpy']:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return {'runner_version': RUNNER_VERSION, 'algorithm_version': matching.ALGORITHM_VERSION,
            'source_sha256': source, 'git_commit': sha, 'working_tree_dirty': dirty,
            'python': platform.python_version(), 'platform': platform.platform(),
            'machine': platform.machine(), 'processor': platform.processor(), 'packages': versions}


def _csv(path, fields, rows):
    with path.open('x', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_evaluation(dataset_path, output, *, baselines=('B0', 'B1'), split='test', k=5,
                   threshold=2, repeats=5, warmup=1, allow_synthetic=False):
    for name, value, minimum in [('k', k, 1), ('repeats', repeats, 1), ('warmup', warmup, 0)]:
        if type(value) is not int or value < minimum:
            raise ValueError(name + ' must be an integer >= ' + str(minimum))
    if type(threshold) is not int or not 1 <= threshold <= 3:
        raise ValueError('threshold must be an integer from 1 to 3')
    if split not in {'dev', 'test'}:
        raise ValueError('split must be dev or test')
    if not baselines or len(set(baselines)) != len(baselines) or any(b not in BASELINES for b in baselines):
        raise ValueError('Select distinct baselines from B0, B1 and B2')
    dataset_path, output = Path(dataset_path), Path(output)
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError('Output must be a new or empty directory; previous results are preserved.')
    raw_dataset = dataset_path.read_bytes()
    input_hash = hashlib.sha256(raw_dataset).hexdigest()
    dataset = parse_dataset(raw_dataset)
    if dataset.kind == 'synthetic' and not allow_synthetic:
        raise ValueError('Synthetic fixtures require --allow-synthetic; they are not evidence of matching quality.')
    profiles = sorted((p for p in dataset.profiles if p.split == split), key=lambda p: p.id)
    if not profiles:
        raise ValueError('No profiles in selected split: ' + split)
    runtime = _source_metadata()
    catalog, jobs = _catalog(dataset), {j.id: j for j in dataset.jobs}
    labels = {(j.profile_id, j.job_id): j.grade for j in dataset.judgments}
    semantic = {'status': 'not_run', 'reason': 'B2 was not requested.'}
    guard = _SemanticGuard()
    matching.LOGGER.addHandler(guard)
    query_rows, ranking_rows, latency_rows = [], [], []
    summaries = {}
    try:
        if 'B2' in baselines:
            semantic = {'status': 'evaluated', **_semantic_metadata()}
            guard.check()
        for baseline in baselines:
            baseline_queries, timings = [], []
            for profile in profiles:
                for _ in range(warmup):
                    rank_profile(profile, jobs, catalog, baseline)
                    if baseline == 'B2':
                        guard.check()
                ranking = None
                for repeat in range(repeats):
                    start = time.perf_counter_ns()
                    current = rank_profile(profile, jobs, catalog, baseline)
                    elapsed = (time.perf_counter_ns() - start) / 1_000_000
                    if baseline == 'B2':
                        guard.check()
                    if ranking is not None and ranking != current:
                        raise ValueError('Ranking changed between repeats; preserve fixed conditions before measuring.')
                    ranking = current
                    timings.append(elapsed)
                    latency_rows.append({'baseline': baseline, 'profile_id': profile.id, 'repeat': repeat + 1,
                                         'candidate_count': len(current), 'elapsed_ms': elapsed})
                valid = [r['job_id'] for r in ranking if r['score'] is not None]
                relevant = {j: labels[profile.id, j] for j in profile.candidate_job_ids}
                quality = evaluate_ranking(valid, relevant, k=k, threshold=threshold)
                row = {'baseline': baseline, 'profile_id': profile.id, 'language': profile.language,
                       'candidate_count': len(ranking), 'scored_count': len(valid), **quality}
                query_rows.append(row)
                baseline_queries.append(row)
                for rank, result in enumerate(ranking, 1):
                    ranking_rows.append({'baseline': baseline, 'profile_id': profile.id,
                                         'rank': rank if result['score'] is not None else None,
                                         **result, 'grade': relevant[result['job_id']]})
            ndcgs = [q['ndcg_at_k'] for q in baseline_queries if q['ndcg_at_k'] is not None]
            summaries[baseline] = {'description': BASELINES[baseline], 'query_count': len(baseline_queries),
                                   'precision_at_k': statistics.mean(q['precision_at_k'] for q in baseline_queries),
                                   'ndcg_at_k': statistics.mean(ndcgs) if ndcgs else None,
                                   'ndcg_query_count': len(ndcgs), 'zero_ideal_gain_query_count': len(baseline_queries) - len(ndcgs),
                                   'latency_samples': len(timings), 'latency_p50_ms': percentile(timings, 50),
                                   'latency_p95_ms': percentile(timings, 95)}
    finally:
        matching.LOGGER.removeHandler(guard)
    config = {'baselines': list(baselines), 'split': split, 'k': k, 'relevance_threshold': threshold,
              'warmup': warmup, 'repeats': repeats, 'tie_break': 'score descending, then job_id ascending',
              'unscorable_candidates': 'not recommended; retained in rankings.csv with blank rank/score',
              'latency_scope': 'per-profile full candidate ranking, including competency extraction; excludes input/output and model startup',
              'baseline_order': list(baselines), 'precision_denominator': k,
              'ndcg_gain': '2**grade - 1', 'ndcg_zero_ideal_gain': 'null, excluded from macro average',
              'randomness': 'No sampling or random split; explicit profile split and candidate lists are used.'}
    if _source_metadata()['source_sha256'] != runtime['source_sha256']:
        raise ValueError('Evaluation source files changed during the run; retry with a fixed revision.')
    report = {'created_at_utc': datetime.now(timezone.utc).isoformat(), 'dataset_id': dataset.dataset_id,
              'dataset_kind': dataset.kind, 'dataset_file': dataset_path.name, 'dataset_sha256': input_hash,
              'catalog_sha256': _hash_json([s.model_dump() for s in dataset.catalog]),
              'config': config, 'config_sha256': _hash_json(config), 'runtime': runtime,
              'semantic': semantic, 'baselines': summaries,
              'independent_quality_evidence': dataset.kind == 'independent',
              'complete_B0_B1_B2_comparison': set(baselines) == set(BASELINES),
              'annotation_status': 'Declared independent annotations; identities/provenance still require human verification.' if dataset.kind == 'independent' else 'Synthetic pipeline test only; these numbers do not validate employment or matching effectiveness.',
              'judgment_count': len(dataset.judgments), 'assessor_ids': sorted({r.assessor_id for j in dataset.judgments for r in j.ratings})}
    output.mkdir(parents=True, exist_ok=True)
    lock = output / '.evaluation.lock'
    with lock.open('x', encoding='utf-8'):
        pass
    try:
        if any(path != lock for path in output.iterdir()):
            raise ValueError('Output is no longer empty; another run may have completed. Nothing was overwritten.')
        _csv(output / 'queries.csv', ['baseline', 'profile_id', 'language', 'candidate_count', 'scored_count', 'precision_at_k', 'ndcg_at_k'], query_rows)
        _csv(output / 'rankings.csv', ['baseline', 'profile_id', 'rank', 'job_id', 'score', 'grade'], ranking_rows)
        _csv(output / 'latencies.csv', ['baseline', 'profile_id', 'repeat', 'candidate_count', 'elapsed_ms'], latency_rows)
        with (output / 'report.json').open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    finally:
        lock.unlink()
    return report
