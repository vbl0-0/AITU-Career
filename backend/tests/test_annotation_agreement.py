import pytest

from app.evaluation.agreement import weighted_cohen_kappa


def test_agreement_matches_a_hand_calculated_nontrivial_table():
    result = weighted_cohen_kappa([0, 0, 1, 1, 2, 2], [0, 1, 1, 2, 2, 0])
    # Raw table has weighted observed disagreement 6 / (6 * 4) = 1/4.
    # Uniform marginals give expected disagreement 48 / (36 * 4) = 1/3.
    # Thus kappa = 1 - (1/4)/(1/3) = 1/4, before resolving any disagreement.
    assert result == {'count': 6, 'exact_agreement': .5,
                      'quadratic_weighted_kappa': .25, 'undefined_reason': None,
                      'confusion_matrix': [[1, 1, 0], [0, 1, 1], [1, 0, 1]],
                      'rater_a_counts': [2, 2, 2], 'rater_b_counts': [2, 2, 2],
                      'weighting': 'quadratic'}


def test_perfect_agreement_with_variation_is_one():
    result = weighted_cohen_kappa([0, 1, 2, 2], [0, 1, 2, 2])
    assert result['quadratic_weighted_kappa'] == 1
    assert result['exact_agreement'] == 1
    assert result['undefined_reason'] is None


@pytest.mark.parametrize('grades', [[0], [1, 1], [2, 2, 2]])
def test_perfect_constant_sheets_keep_kappa_undefined(grades):
    result = weighted_cohen_kappa(grades, grades)
    assert result['quadratic_weighted_kappa'] is None
    assert result['exact_agreement'] == 1
    assert 'expected disagreement is zero' in result['undefined_reason']


def test_reversed_extreme_ratings_can_produce_negative_kappa():
    result = weighted_cohen_kappa([0, 2], [2, 0])
    assert result['quadratic_weighted_kappa'] == -1
    assert result['exact_agreement'] == 0


def test_quadratic_weighting_distinguishes_near_and_extreme_disagreements():
    near = weighted_cohen_kappa([0, 1, 2], [1, 0, 2])
    extreme = weighted_cohen_kappa([0, 1, 2], [2, 1, 0])
    assert near['exact_agreement'] == extreme['exact_agreement'] == pytest.approx(1 / 3)
    assert near['quadratic_weighted_kappa'] == .5
    assert extreme['quadratic_weighted_kappa'] == -1


def test_different_constant_sheets_have_nonzero_expected_disagreement():
    result = weighted_cohen_kappa([0, 0], [2, 2])
    assert result['quadratic_weighted_kappa'] == 0
    assert result['undefined_reason'] is None


def test_custom_binary_scale_and_rater_swap_preserve_the_coefficient():
    first, second = [0, 0, 1, 1], [0, 1, 1, 1]
    result = weighted_cohen_kappa(first, second, max_grade=1)
    swapped = weighted_cohen_kappa(second, first, max_grade=1)
    assert result['quadratic_weighted_kappa'] == swapped['quadratic_weighted_kappa'] == .5
    assert result['exact_agreement'] == .75
    assert result['confusion_matrix'] == [[1, 1], [0, 2]]
    assert result['rater_a_counts'] == swapped['rater_b_counts']
    assert result['rater_b_counts'] == swapped['rater_a_counts']


def test_raw_ratings_are_not_mutated():
    first, second = [0, 1, 2], [1, 1, 2]
    weighted_cohen_kappa(first, second)
    assert first == [0, 1, 2]
    assert second == [1, 1, 2]


@pytest.mark.parametrize('first,second', [([], []), ([0], []), ([0], [0, 1]), (None, [0]), ([0], None)])
def test_missing_or_unpaired_ratings_are_rejected(first, second):
    with pytest.raises(ValueError):
        weighted_cohen_kappa(first, second)


@pytest.mark.parametrize('grade', [-1, 3, 1.0, True, '1', None, float('nan'), float('inf')])
def test_invalid_grades_are_not_coerced_or_treated_as_missing(grade):
    with pytest.raises(ValueError):
        weighted_cohen_kappa([grade], [0])
    with pytest.raises(ValueError):
        weighted_cohen_kappa([0], [grade])


@pytest.mark.parametrize('maximum', [0, -1, 2.0, True, '2', None])
def test_invalid_grade_scales_are_rejected(maximum):
    with pytest.raises(ValueError):
        weighted_cohen_kappa([0], [0], max_grade=maximum)
