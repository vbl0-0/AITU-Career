# Independent relevance annotation

This workflow supports [Zhan's task #10](https://github.com/vbl0-0/AITU-Career/issues/10),
planned for 6 November 2026, and supplies the data for
[Ayadil's task #11](https://github.com/vbl0-0/AITU-Career/issues/11), planned for 13 November.
Real records and independent assessors have not been supplied. The tools and blank
templates do not complete task #10 or establish matching quality.

The supplied example contains three synthetic profiles, six fictional vacancies and
18 candidate pairs. It tests the annotation workflow only. The submitted protocol
plans 20 profiles (ten development and ten test) and 50 legally usable vacancies;
the example does not meet that research target.

## Agree the protocol before annotation

Use the three-level scale recorded in the submitted report:

| Grade | Meaning |
|---|---|
| 0 | Irrelevant to the supplied profile or target direction. |
| 1 | Partly relevant; important competencies are missing or underdeveloped. |
| 2 | Suitable, based on the available profile and vacancy evidence. |

The evaluation schema accepts grades 0–3, so this 0–2 scale is a valid subset; the
prepared annotation sheets use 0–2 only. Grade 2 is relevant for Precision@5. Fix the
rubric before collecting ratings; changing it later requires a documented new study
version. Keep the submitted `prob-period-1` report unchanged.

Recruit exactly two assessors independent of the matching implementation. `R1` and
`R2` are pseudonyms for separate people, not evidence that those people exist. Keep
their actual identity, relevant expertise, instructions and annotation dates in a
private study record. Do not invent those details or use model-generated grades as
independent human judgments. Keep names, contacts and private identity mappings out
of Git.

## Prepare and freeze the source

Start from `backend/evaluation/annotation-source.example.json`, which contains no
judgments. Replace its fictional material only with records you are permitted to use.
Remove identifying details, document provenance, and manually inspect near-duplicate
profiles and vacancies. Preserve unsuitable candidate vacancies as well as suitable
ones. Every candidate pair must eventually receive both independent ratings.
Use opaque IDs such as `P001` and `V001`; IDs must not reveal split membership.

The source contains the catalogue, jobs, profiles with explicit `dev`/`test` splits,
`provenance`, and `person_groups`. Map every profile ID to an anonymous person-group
ID; all variants of the same person must remain in one split. The tool detects a
declared group crossing splits, but cannot discover undisclosed duplicate people.
Freeze candidate pools and document any deliberate vacancy reuse across splits;
shared vacancies support a new-profile claim rather than an unseen-vacancy claim.

From `backend/`, using the existing backend environment:

```powershell
python -m app.evaluation.annotation prepare --source evaluation/annotation-source.example.json --output ../.local/annotation-packet --assessors R1 R2 --seed 42
```

Use a new or empty output directory. Preserve `manifest.json` and `source.json`;
they record the frozen input, split membership and source fingerprint. The packet
also contains a README and separate `assessor-R1.csv` / `assessor-R1.html` and
`assessor-R2.csv` / `assessor-R2.html` sheets. All grades start blank. The seed fixes
case order for reproduction; it does not generate relevance grades.

Send each assessor only their own sheet. The offline HTML displays the supplied
profile and vacancy evidence without baseline scores, numeric algorithm weights,
other judgments or development/test labels. Assessors work independently, without
seeing each other's grades. They should judge the supplied evidence rather than
unrelated assumptions about age, gender or other personal characteristics.

## Collect two complete raw sheets

An assessor can fill the CSV directly or grade cases in their offline HTML and
download the CSV. Preserve the raw file before any discussion or adjudication.
Keep returned downloads separately, for example as
`.local/annotation-ratings/ratings-R1.csv` and `ratings-R2.csv`; do not overwrite
the blank templates. Each page opens blank; resume your own saved browser draft
only by explicitly selecting `Restore my saved draft` for the same assessment.
The CSV columns are:

```text
source_sha256,assessor_id,profile_id,job_id,grade,note
```

Keep the generated fingerprint and IDs intact. Blank grades mean unanswered cases,
not grade zero. Notes are optional observations by the assessor. Do not insert grades
for them, copy one person's sheet into the other, or average disagreeing grades.

With the two completed files, run:

```powershell
python -m app.evaluation.annotation analyze --packet ../.local/annotation-packet --ratings ../.local/annotation-ratings/ratings-R1.csv ../.local/annotation-ratings/ratings-R2.csv --output ../.local/annotation-agreement
```

Analysis requires complete, correctly identified ratings for every frozen candidate
pair. It writes `agreement.json` from the original ratings **before adjudication**:
exact agreement, the confusion matrix and quadratic-weighted Cohen's kappa. Kappa
uses squared ordinal distance; if expected disagreement is zero, it is undefined
and reported as `null` with a reason rather than fabricated as a perfect statistic.
Metric reference: [scikit-learn's Cohen's kappa documentation](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html).

The accompanying `adjudication.csv` contains disagreement cases with blank
`final_grade` and `reason`. Preserve the original ratings while the assessors discuss
each disagreement and record the agreed grade and actual rationale. Agreement must
not be recomputed from the resolved grades and presented as independent agreement.

## Finalize the handoff

After resolving every disagreement:

```powershell
python -m app.evaluation.annotation finalize --packet ../.local/annotation-packet --ratings ../.local/annotation-ratings/ratings-R1.csv ../.local/annotation-ratings/ratings-R2.csv --adjudication ../.local/annotation-agreement/adjudication.csv --output ../.local/annotation-final
```

The `--adjudication` argument is optional when there are no disagreements. Finalization
retains the source, raw CSV files, pre-adjudication agreement and provenance manifest,
and produces `dataset.json` validated for the existing evaluator. Previous outputs
are preserved. The source kind is retained: labeling a synthetic example does not
turn it into independent real-world data or evidence of employment outcomes.

Ayadil can then run `python -m app.evaluation --dataset ../.local/annotation-final/dataset.json --output ../.local/matching-evaluation/annotated-test`.
Synthetic sources still require `--allow-synthetic`. Tune rules on development data
only; preserve the held-out split and unsuccessful outcomes. See
[MATCHING_EVALUATION.md](MATCHING_EVALUATION.md) for B0/B1/B2 and timing details.

Before closing #10, retain the real assessor records, original complete ratings,
agreement, adjudication and frozen data/split hashes, and obtain substantive peer
review. The tooling delivery is a separate PR stacked on PR #30; neither PR merging
nor an AI-assisted check constitutes a person's review or completed human annotation.
