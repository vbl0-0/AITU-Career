"""Record supplied supervisor comments and distinguish report fixes from future work."""
import json


def apply_supervisor_feedback(sources, sections, cfg, root):
    record = json.loads((root / cfg['supervisor_feedback_record']).read_text(encoding='utf-8'))
    repo, tag = cfg['repository_url'], cfg['submission_tag']
    artifact = f'{repo}/blob/{tag}/docs/pre-defense-1/evidence/'
    code = f'{repo}/blob/{tag}/backend/app/ai/matching.py'
    by_number = {i: section for i, section in enumerate(sections, 1)}

    def p(text):
        return {'type': 'p', 'text': text}

    def h(text):
        return {'type': 'h3', 'text': text}

    def t(headers, rows):
        return {'type': 'table', 'headers': headers, 'rows': rows}

    by_number[6]['blocks'].extend([
        h('AI functionality: implemented baseline and optional learned extension'),
        p('The implemented decision-support baseline is deterministic: it extracts known skill terms and aliases, combines profile evidence, scores vacancy requirements and derives gap-based actions. This is a knowledge-based matching pipeline, not a trained employment predictor or a generative assistant. The learned AI extension is a local sentence-embedding adapter; it is disabled in the verified configuration. The report therefore separates working rule-based functionality from available but unevaluated machine-learning functionality.'),
        t(['Capability', 'Actual mechanism and output', 'Evidence / current status'], [
            ['Skill extraction and normalization', 'Whole-term catalogue/alias matching in project descriptions, experience text and certificate names; canonical skill IDs and evidence sources are retained.', 'extract_skills() and competencies(); implemented and covered by tests. This is not an LLM or a general CV parser.'],
            ['Proficiency-aware vacancy matching', 'Requirement weights and stored skill levels produce a coverage score and matched/partial/missing groups. Inferred evidence contributes at most 0.5; no requirements produce a null score.', 'score_requirements() and analyze(); implemented deterministic baseline, algorithm weighted-skills-1.0.'],
            ['Career recommendations', 'Missing and partial requirements are sorted by importance and converted into skill-specific development actions. Readiness combines profile evidence with vacancy coverage.', 'analyze() and career_summary(); implemented rules, not learned generation or a probability of hiring.'],
            ['Semantic skill matching', 'Optional SentenceTransformer encodes skill names; normalized dot-product similarity selects a candidate above the configured threshold. Semantic evidence remains partial.', 'semantic_candidate(); adapter exists, default threshold 0.85. Real model disabled/unavailable in the verified run; controlled tests and fallback only.'],
            ['Learned ranking or employment prediction', 'A model trained on local hiring outcomes, validated success probabilities and an adaptive recommender are not implemented.', 'Future research possibilities; no effectiveness result is claimed.'],
        ]),
        p('Illustrative calculation, not a real student result: Python level 3 of required 3 with weight 2 contributes 2; SQL level 1 of required 2 with weight 2 contributes 1; absent Git with weight 1 contributes 0. The score is 100 × (2 + 1 + 0) / (2 + 2 + 1) = 60%. Python is matched, SQL is partial and Git is missing. This demonstrates an explainable calculation, not measured recommendation accuracy.'),
        p('Implementation reference: ' + code + '. Matching correctness tests verify rules and boundaries. Only an independent relevance experiment can establish whether this approach ranks useful vacancies better than simpler alternatives.'),
    ])

    verification = by_number[9]['blocks']
    old_protocol = next(i for i, block in enumerate(verification) if block.get('text', '').startswith('Proposed evaluation data:'))
    validity_note = verification[-1]
    by_number[9]['blocks'] = verification[:old_protocol]
    by_number[9]['blocks'].extend([
        h('Operational evaluation protocol in response to SUP-01 and SUP-02'),
        p('The following is a next-stage protocol, not a completed experiment. Freeze 20 anonymized or synthetic profiles and 50 legally usable vacancies, using at least five candidates per evaluated profile. Use ten profiles for development and ten held-out profiles for testing; store IDs, source permissions, split membership and data hashes. This produces 500 development and 500 held-out profile–vacancy pairs. Where development and test share vacancies, the stated claim concerns new profiles rather than unseen vacancies.'),
        t(['Comparison', 'Controlled change', 'Result status'], [
            ['B0 — exact overlap', 'Case-normalized canonical skill-name overlap, without aliases, proficiency levels or requirement weighting.', 'Not yet measured.'],
            ['B1 — current baseline', 'Current catalogue/aliases, evidence levels and requirement weights, with semantic inference disabled.', 'Implementation verified; ranking quality not yet measured.'],
            ['B2 — semantic extension', 'B1 plus the optional local embedding adapter, with model revision and threshold fixed before the held-out run.', 'Real model not evaluated. If it cannot be loaded, record B2 as not run; do not substitute a fabricated score.'],
        ]),
        p('Two raters independent of the matching implementation should assign relevance grades 0 (irrelevant), 1 (partly relevant) and 2 (suitable), without seeing algorithm scores. Store both original ratings and weighted Cohen\'s kappa before adjudication. Rater identities and actual dates remain unfilled until the work occurs. Tune aliases and semantic thresholds only on development data; use the same eligible candidates for all methods and break score ties by vacancy ID.'),
        t(['Measure', 'Calculation / procedure', 'Decision and retained artifact'], [
            ['Ranking relevance', 'Precision@5 = count of grade-2 vacancies in the first five / 5. nDCG@5 uses gains 2^grade − 1 and log2(rank + 1) discount, normalized by the ideal top-five ranking.', 'Macro-average per held-out profile. Profiles with zero ideal gain have undefined nDCG and are counted separately; report their number and candidate coverage. Preserve per-profile rankings and labels.'],
            ['Extraction accuracy', 'Micro precision, recall and F1 against annotated canonical skill mentions; show separate Kazakh/Russian/English results and representative errors.', 'Keep span/skill reference annotations and the exact normalization rules. No extraction-accuracy figure is currently claimed.'],
            ['Efficiency', 'Same CPU, RAM, data, process and cache conditions; 30 warm-up requests, then 200 measured requests. Record median and p95, model loading separately, and errors.', 'Keyword p95 target is at most 500 ms. Pre-register a separate semantic latency/memory budget before comparing B2. Preserve request timings and environment details.'],
            ['Uncertainty and adoption', 'Use seed 42 and 1,000 paired profile-level bootstrap resamples for the nDCG difference; report a 95% interval and Precision@5 changes.', 'Adopt an extension only if held-out nDCG improves with an interval above zero, Precision@5 does not deteriorate, its registered resource budget is met and functional regressions are absent. Otherwise retain the simpler method and report the negative outcome.'],
        ]),
        p('Execution responsibilities are planned: Zhan coordinates the dataset, annotation records and error analysis; Ayadil prepares the reproducible B0/B1/B2 runner, model/configuration hashes and latency measurements. Both inspect the held-out results and review each other\'s experiment changes. Independent raters must be recruited; account ownership or an AI-assisted check is not treated as expert relevance annotation. The tracker schedules label preparation in #10 and baseline/latency evaluation in #11 for the next stage.'),
        p('Expected evaluation artifacts: a dataset/split manifest, independent labels and agreement record, a committed comparison runner, environment/model configuration, per-profile rankings, metrics/timing files and an interpretation of errors and negative results. These artifacts are planned and are not listed as already available. The 60 backend and 20 browser tests establish implementation behavior, not AI effectiveness.'),
        validity_note,
    ])

    management = by_number[10]['blocks']
    management[0] = p('Responsibilities below are supported by dated account-linked delivery records. OpenAI Codex assisted implementation, packaging, technical verification and publication. These records establish what was delivered under each account; imported history alone does not establish exclusive original authorship or the time each person spent. Actual human peer review remains to be added in GitHub, as requested by the supervisor.')
    management[1] = t(['Participant / work area', 'Concrete delivered artifacts and traceability', 'Evidence limit'], [
            [cfg['members'][0]['name'] + ' / @vbl0-0', 'Backend API/models/migrations: 6c434f2; regression tests/container setup: 0b8c8bb; architecture/startup delivery: 26c8605. Related PRs #19, #21, #23 and issues #7/#9/#12/#14.', 'AI-assisted current deliveries. No percentage, independent initial code authorship or unrecorded manual review is inferred.'],
            [cfg['members'][1]['name'] + ' / @igiiaw', 'Frontend/i18n/browser tests: 7717652; references/documentation: c12021f; report sources: 203f7c7; report/evidence exports: d308bb1 and adc5d46. Related PRs #20/#22/#24/#25 and issues #4/#5/#8/#16/#17.', 'AI-assisted current deliveries. Account attribution and module responsibility are distinguished from proof of who wrote every imported line.'],
        ])
    management.extend([
        h('Development history supported by original Git metadata'),
        p('The original Git metadata records repository setup, automation and frontend import on 23 October 2026, followed by backend, report-source, architecture and submission deliveries on 24 October 2026 (UTC+5 author timestamps). These are the real recorded publication stages; no earlier incremental history is reconstructed. The pre-feedback snapshot contains 11 non-merge commits, preserved with their original author dates and subjects: ' + artifact + 'development-history.json' + '.'),
        h('Peer review process to introduce in GitHub'),
        p('The checked PRs #19–25 contain no submitted GitHub review records. Their merge status, automated tests and supervisor feedback are not peer approval. This remains an improvement action, not a completed feature. For the next substantive backend change, Zhan should review Ayadil\'s PR; for a frontend/report change, Ayadil should review Zhan\'s PR. Each reviewer personally inspects the diff, runs the relevant checks and records concrete comments and test evidence. The author links resulting fixes, and the reviewer rechecks before approval. Only actual actions may be recorded under a person\'s account.'),
        p('Use small task-focused PRs, a contribution log stating the participant\'s actual implementation/test/review actions and any AI assistance, and a checklist covering correctness, authorization/data handling, edge cases and regression evidence. Where repository settings support it, require one independent approval and passing relevant checks before merging; enabling that rule is planned, not claimed as already configured. Preserve review comments and resulting commits rather than creating approvals after the fact. Peer-review status evidence: ' + artifact + 'peer-review-status-2026-10-24.json' + '.'),
    ])

    by_number[11]['title'] = '11. Supervisor Feedback and Response to Comments'
    by_number[11]['blocks'] = [
        p('Supervisor feedback was supplied to the team on 24 October 2026. The following record reproduces the two messages transcribed by Ayadil, attributed to ' + record['supervisor'] + ' (display name Arailym). The original private chat was not independently accessed and the messages do not identify an exact reviewed commit. Their positive assessment is recorded without turning it into an unconditional final approval.'),
        h('SUP-01 — 24 October 2026, 15:28; original English message'),
        p('“' + record['messages'][0]['text'] + '”'),
        h('SUP-02 — 24 October 2026, 15:29; English translation of the Russian message'),
        p('“' + record['messages'][1]['english_translation'] + '”'),
        p('The original Russian text, English translation, times and source limitations are retained in ' + artifact + 'supervisor-feedback-2026-10-24.json' + '.'),
        p('The previous prepared snapshot is retained at ' + repo + '/tree/' + cfg['previous_submission_tag'] + '. It is a preserved pre-feedback assembly, not a claim that the supervisor reviewed that exact commit. The current prob-period-1 package incorporates the reporting changes below before form submission.'),
        t(['Supervisor comment', 'Change in this report', 'Implementation / next-stage status'], [
            ['Clarify the AI functionality.', 'Section 6 now distinguishes deterministic extraction/matching/recommendation rules, the optional embedding adapter and functionality that does not exist; includes a worked calculation and code reference.', 'Documentation updated. No new trained model or generative service is claimed.'],
            ['Explain how matching effectiveness will be evaluated.', 'Section 9 specifies B0/B1/B2, data splits, blind independent labels, metrics, latency conditions, adoption criteria and retained artifacts.', 'Protocol clarified. Independent quality and latency experiments remain planned in #10/#11.'],
            ['Show each participant\'s actual contribution and development history.', 'Section 10 lists concrete account-linked artifacts, commit IDs, PRs, real author dates and limits of historical authorship attribution.', 'Published evidence documented. Subsequent contribution logs must record actual personal implementation, testing and review actions.'],
            ['Add peer review and improve development practices.', 'Section 10 defines cross-review responsibilities, task-focused PRs, review evidence, follow-up fixes and a proposed independent-approval gate.', 'Not yet performed/configured. No GitHub peer approval is fabricated.'],
            ['Continue system testing.', 'Section 9 preserves actual 60-backend/20-browser verification separately from independent model evaluation and identifies untested areas.', 'Current verification recorded; further regression coverage and quality experiments belong to the next stage.'],
        ]),
        p('Documentation changes above address the current reporting comments. The remaining engineering and evaluation actions are explicitly prospective. Receiving supervisor feedback does not substitute for independent GitHub peer review, independent relevance labels or measured matching effectiveness.'),
    ]

    for block in by_number[13]['blocks']:
        if block['type'] != 'table':
            continue
        for row in block['rows']:
            if row[0] == 'Optional interviews and feedback':
                row[:] = ['Interviews and supervisor feedback', 'No interviews; actual supervisor messages of 24 October and the response matrix are recorded in Section 11.', 'Evaluation and human peer review remain next-stage work.']
    return sources, sections
