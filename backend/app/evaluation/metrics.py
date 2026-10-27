"""Small, explicit ranking and latency metrics for offline matching evaluation."""
import math
from numbers import Real


def _positive_k(k):
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError('k must be a positive integer')
    return k


def _grade(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 3:
        raise ValueError('Relevance grades must be integers from 0 to 3')
    return value


def _grades(values):
    return [_grade(value) for value in values]


def precision_at_k(grades, k=5, threshold=2):
    """Count relevant results among k slots; unfilled slots are non-relevant.

    A result is relevant when its 0--3 grade reaches ``threshold``. Keeping
    the denominator at k makes a short recommendation list explicit.
    """
    _positive_k(k)
    _grade(threshold)
    values = _grades(grades)
    return sum(value >= threshold for value in values[:k]) / k


def ndcg_at_k(grades, ideal_grades, k=5):
    """Use exponential gains and logarithmic discount; no ideal gain is None.

    ``ideal_grades`` must contain all judged candidate grades for the query,
    rather than just the returned list. Queries without any positive ideal
    gain have undefined nDCG and should be reported separately by callers.
    """
    _positive_k(k)
    values = _grades(grades)
    ideal = sorted(_grades(ideal_grades), reverse=True)

    def dcg(ranking):
        return sum((2 ** grade - 1) / math.log2(index + 2)
                   for index, grade in enumerate(ranking[:k]))

    denominator = dcg(ideal)
    return dcg(values) / denominator if denominator else None


def percentile(values, p=95):
    """Linearly interpolate sorted timings at index (n - 1) * p / 100."""
    if isinstance(p, bool) or not isinstance(p, Real) or not math.isfinite(p) or not 0 <= p <= 100:
        raise ValueError('p must be a finite number from 0 to 100')
    timings = list(values)
    if not timings:
        raise ValueError('At least one timing is required')
    if any(isinstance(value, bool) or not isinstance(value, Real)
           or not math.isfinite(value) or value < 0 for value in timings):
        raise ValueError('Timings must be finite non-negative numbers')
    timings.sort()
    index = (len(timings) - 1) * p / 100
    lower, upper = math.floor(index), math.ceil(index)
    return float(timings[lower] + (timings[upper] - timings[lower]) * (index - lower))


def evaluate_ranking(ranked_job_ids, labels, k=5, threshold=2):
    """Evaluate a ranking against complete candidate labels supplied by the caller."""
    _positive_k(k)
    _grade(threshold)
    ranking = list(ranked_job_ids)
    if len(set(ranking)) != len(ranking):
        raise ValueError('Ranked job IDs must be unique')
    if any(identifier not in labels for identifier in ranking):
        raise ValueError('Every ranked job must have a relevance label')
    grades = [labels[identifier] for identifier in ranking]
    ideal = list(labels.values())
    return {'precision_at_k': precision_at_k(grades, k, threshold),
            'ndcg_at_k': ndcg_at_k(grades, ideal, k)}
