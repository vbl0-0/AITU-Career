import math

import pytest

from app.evaluation.metrics import evaluate_ranking, ndcg_at_k, percentile, precision_at_k


def test_precision_uses_threshold_and_all_five_positions():
    assert precision_at_k([3, 2, 1, 0, 2, 3]) == pytest.approx(3 / 5)
    assert precision_at_k([3, 2]) == pytest.approx(2 / 5)
    assert precision_at_k([]) == 0
    assert precision_at_k([3, 2, 1], k=3, threshold=3) == pytest.approx(1 / 3)


def test_ndcg_matches_hand_calculated_graded_ranking():
    actual = 3 / math.log2(2) + 7 / math.log2(3) + 1 / math.log2(4)
    ideal = 7 / math.log2(2) + 3 / math.log2(3) + 1 / math.log2(4)
    assert ndcg_at_k([2, 3, 1], [1, 2, 3], k=3) == pytest.approx(actual / ideal)
    assert ndcg_at_k([3, 2, 1], [1, 2, 3], k=3) == pytest.approx(1)


def test_ndcg_uses_all_candidate_labels_for_ideal_and_handles_short_lists():
    ideal = 7 + 3 / math.log2(3)
    assert ndcg_at_k([2], [2, 3], k=5) == pytest.approx(3 / ideal)
    assert ndcg_at_k([], [3]) == 0
    assert ndcg_at_k([0, 0], [0, 0]) is None
    assert ndcg_at_k([], []) is None


def test_rank_evaluation_uses_job_ids_and_preserves_undefined_ndcg():
    labels = {'best': 3, 'good': 2, 'weak': 1, 'irrelevant': 0}
    result = evaluate_ranking(['good', 'best', 'weak'], labels)
    assert result['precision_at_k'] == pytest.approx(2 / 5)
    assert result['ndcg_at_k'] == pytest.approx(ndcg_at_k([2, 3, 1], labels.values()))
    assert evaluate_ranking(['zero'], {'zero': 0}) == {'precision_at_k': 0, 'ndcg_at_k': None}


@pytest.mark.parametrize('ranking, labels', [(['a', 'a'], {'a': 3}), (['missing'], {'a': 3})])
def test_rank_evaluation_rejects_duplicate_or_unjudged_results(ranking, labels):
    with pytest.raises(ValueError):
        evaluate_ranking(ranking, labels)


@pytest.mark.parametrize('value', [-1, 4, 1.5, True, '2', None])
def test_invalid_grades_are_not_silently_coerced(value):
    with pytest.raises(ValueError):
        precision_at_k([value])
    with pytest.raises(ValueError):
        ndcg_at_k([], [value])
    with pytest.raises(ValueError):
        ndcg_at_k([value], [3])
    with pytest.raises(ValueError):
        evaluate_ranking([], {'not_returned': value})


@pytest.mark.parametrize('k', [0, -1, 2.5, True])
def test_invalid_cutoffs_fail_even_for_empty_rankings(k):
    with pytest.raises(ValueError):
        precision_at_k([], k=k)
    with pytest.raises(ValueError):
        ndcg_at_k([], [], k=k)
    with pytest.raises(ValueError):
        evaluate_ranking([], {}, k=k)


@pytest.mark.parametrize('threshold', [-1, 4, 1.5, True])
def test_invalid_thresholds_are_rejected(threshold):
    with pytest.raises(ValueError):
        precision_at_k([3], threshold=threshold)


def test_percentile_interpolates_known_values_and_accepts_single_measurement():
    assert percentile([40, 10, 30, 20]) == pytest.approx(38.5)
    assert percentile([10, 20, 30, 40], 50) == pytest.approx(25)
    assert percentile([10, 20], 0) == 10
    assert percentile([10, 20], 100) == 20
    assert percentile([7]) == 7
    assert percentile([0]) == 0


@pytest.mark.parametrize('values', [[], [-1], [float('inf')], [float('nan')], [True], ['1']])
def test_percentile_rejects_invalid_timings(values):
    with pytest.raises(ValueError):
        percentile(values)


@pytest.mark.parametrize('p', [-1, 101, float('inf'), float('nan'), True, '95'])
def test_percentile_rejects_invalid_percentages(p):
    with pytest.raises(ValueError):
        percentile([1], p)
