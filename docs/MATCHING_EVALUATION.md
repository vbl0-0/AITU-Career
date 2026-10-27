# Matching evaluation

This offline tool supports [task #11](https://github.com/vbl0-0/AITU-Career/issues/11).
It evaluates ranking against supplied relevance judgments without connecting to the
application database or changing production matching behavior. Independent judgments
are not included yet. Synthetic smoke results verify the tool, not matching quality
or employment outcomes.

## Run a smoke check

Use the existing backend environment and run from `backend/`:

```powershell
python -m app.evaluation --dataset evaluation/synthetic-smoke.json --output ../.local/matching-evaluation/smoke --allow-synthetic
```

Choose a new or empty output directory for each run. Existing results are preserved;
exclusive output files and a publication lock prevent simultaneous runs from mixing results.
The explicit `--allow-synthetic` flag is required for synthetic datasets. The defaults
are the `test` split, top five results, relevance at grade 2 or above, five measured
repetitions and one warm-up repetition. No model download is performed by the runner.

## Baselines

| Baseline | Behavior |
|---|---|
| B0 | Exact canonical skill overlap, including whole-term canonical names in text; ignores aliases, proficiency levels and requirement weights. |
| B1 | Existing `competencies()` and `score_requirements()` with semantic inference disabled: catalogue aliases, proficiency ratios, weights and partial inferred evidence. |
| B2 | The same production scoring with the optional real semantic model enabled; semantic evidence remains partial. |

B0 and B1 run by default. To request B2, first install the optional dependencies
from `backend/requirements-ai.txt` and provide the real model in the local cache or
an existing local model directory. In the evaluation process only:

```powershell
$env:SEMANTIC_ENABLED = 'true'
$env:SEMANTIC_MODEL = 'C:\models\matching-model'
python -m app.evaluation --dataset evaluation/independent.json --output ../.local/matching-evaluation/independent-test --baselines B0 B1 B2
```

Use the agreed, recorded model rather than changing it after examining test results.
If requested B2 cannot load or execute, the experiment fails explicitly; keyword
fallback must not be presented as a completed semantic experiment. Controlled model
substitutes in unit tests do not establish real-model quality.

## Dataset handoff from task #10

Zhan coordinates the independent judgments in
[task #10](https://github.com/vbl0-0/AITU-Career/issues/10), planned for 6 November 2026.
Ayadil runs the comparisons for task #11, planned for 13 November 2026.

The JSON dataset uses `schema_version: 1`, a nonblank `dataset_id` and `kind` set to
`synthetic` or `independent`. The checked smoke fixture demonstrates the full format.

| Collection | Required content |
|---|---|
| `catalog` | Unique positive integer skill IDs, canonical names and optional aliases. Terms must be unambiguous across different skills. |
| `jobs` | Unique string IDs, titles, descriptions and optional structured requirements (`skill_id`, level 1–3, positive weight, `required`). |
| `profiles` | Unique anonymous IDs, `dev`/`test` split, `kk`/`ru`/`en` language and a fixed list of candidate job IDs; structured skills and optional projects, experience and certificates. |
| `judgments` | Exactly one entry for every profile/candidate-job pair: raw `ratings` with assessor IDs and integer grades 0–3; adjudication where necessary. |

Each independent pair needs ratings from at least two distinct assessors. Preserve
their individual grades before discussion. If they disagree, supply an
`adjudicated_grade` and retain the disagreement in the raw ratings. Do not silently
average grades, treat missing judgments as irrelevant, or generate independent
labels from the algorithm being evaluated.

The [annotation workflow](ANNOTATION_GUIDE.md) uses the three-level rubric recorded
in the submitted protocol. The schema also accepts grade 3 for separately versioned
future studies; it does not require a four-level rubric. Fix one scale before labeling:

| Grade | Interpretation |
|---|---|
| 0 | Irrelevant to the profile or target direction. |
| 1 | Partly relevant; important requirements are missing or underdeveloped. |
| 2 | Suitable based on the supplied profile and vacancy evidence. |

Assessors should inspect the same profile and vacancy evidence without seeing the
baseline scores. Keep grades grounded in that evidence, not assumptions about age,
gender or other unrelated personal characteristics. Document assessor instructions,
agreement and adjudication decisions with the dataset handoff.

Before freezing the data:

1. Obtain permission for any real records; remove names, contacts and account IDs.
   Keep private identity mappings and confidential records outside Git.
2. Assign all variants of one real person to one split. Deduplicate near-identical
   vacancy descriptions before fixing the candidate pools; document deliberate
   candidate reuse across splits.
3. Fix profile/job IDs, language, candidate lists, raw ratings and adjudication.
   Every candidate must have a judgment, including unsuitable candidates.
4. Tune rules and thresholds on `dev` only. Freeze the model/configuration before
   the `test` run; preserve unsuccessful comparisons as well as improvements.

## Metrics and timing

Precision@5 counts grades 2–3 as relevant and divides by five. Short lists are padded
with nonrelevant positions rather than receiving an artificially smaller denominator.
nDCG@5 uses gain `2^grade - 1` and discount `log2(rank + 1)` with one-based ranks; the
ideal order uses all judged candidates. A query with no positive ideal gain has
`null` nDCG and is excluded from its macro average; the excluded count is reported.
Ties are resolved deterministically by job ID.
Candidates without any extractable or structured requirements have no score and are
not recommended; they remain visible in `rankings.csv` with blank rank and score.

Latency measures ranking all candidates for one profile, including competency
construction. File reading, dataset validation, model loading and output writing
are outside the warm measured interval. The run records warm-up and repeat counts;
p95 uses linear interpolation over the measured query durations. These are offline
matching timings, not API response times or concurrent-service measurements.

## Outputs and completion

Each output directory contains `report.json`, `rankings.csv`, `queries.csv` and
`latencies.csv`. Preserve the dataset/catalogue, algorithm, model/configuration hashes,
runtime details and Git revision recorded by the run together with its outputs.
Timing varies by machine; compare baselines under the same recorded conditions.
The input hash covers the exact bytes validated for the run. The real B2 fingerprint
includes weights, tokenizer, ordered module configurations and encoding options.

The `Matching evaluation checks` GitHub workflow runs the database-free unit tests
and synthetic B0/B1 smoke experiment. It does not download a model or claim B2 results.

Task #11 remains open until the independent data and actual requested baseline runs
are available and reviewed. Smoke checks and an unavailable B2 do not complete it.
Have Zhan personally review the implementation PR and record substantive comments
and any resulting fixes; AI-assisted checks are technical verification, not his review.

The submitted `prob-period-1` snapshot at
`7849592ef474e53aeacd0c611aa9c740133ccb07` stays unchanged. Keep this next-stage work
in new branches and retain the original submitted report and task evidence.
