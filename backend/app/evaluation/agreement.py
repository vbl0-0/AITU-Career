"""Agreement between two raw annotation sheets, before any adjudication."""


def weighted_cohen_kappa(first: list[int], second: list[int], max_grade=2):
    """Return quadratic weighted Cohen's kappa and its observed rating counts.

    Grades use the complete ordinal scale 0..max_grade. Squared distance is
    divided by max_grade**2 for both observed and expected disagreement; that
    common factor cancels in kappa. Integer disagreement totals avoid premature
    floating-point rounding. Undefined kappa is kept separate from exact
    agreement, including perfectly agreeing constant sheets.
    """
    if type(max_grade) is not int or max_grade < 1:
        raise ValueError('max_grade must be a positive integer')
    try:
        first, second = list(first), list(second)
    except TypeError:
        raise ValueError('Both rating sequences must contain integer grades') from None
    if not first or len(first) != len(second):
        raise ValueError('Rating sequences must be nonempty and have equal lengths')
    if any(type(grade) is not int or not 0 <= grade <= max_grade
           for grades in (first, second) for grade in grades):
        raise ValueError('Grades must be integers from 0 to max_grade')

    count = len(first)
    size = max_grade + 1
    matrix = [[0] * size for _ in range(size)]
    for grade_a, grade_b in zip(first, second, strict=True):
        matrix[grade_a][grade_b] += 1
    rater_a = [sum(row) for row in matrix]
    rater_b = [sum(matrix[a][b] for a in range(size)) for b in range(size)]
    observed = sum((a - b) ** 2 * matrix[a][b]
                   for a in range(size) for b in range(size))
    expected = sum((a - b) ** 2 * rater_a[a] * rater_b[b]
                   for a in range(size) for b in range(size))
    kappa = 1 - count * observed / expected if expected else None
    return {'count': count,
            'exact_agreement': sum(matrix[a][a] for a in range(size)) / count,
            'quadratic_weighted_kappa': kappa,
            'undefined_reason': None if expected else 'Both raters used the same single grade; expected disagreement is zero (no marginal variation).',
            'confusion_matrix': matrix,
            'rater_a_counts': rater_a,
            'rater_b_counts': rater_b,
            'weighting': 'quadratic'}
