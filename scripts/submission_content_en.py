"""English report content. Confirmed details come from submission.json; unknown fields stay blank."""
import json
from pathlib import Path


def build_content(cfg, root):
    # Keep the previously verified bibliographic records and their canonical links.
    sources = json.loads((root / 'docs/pre-defense-1/sources.json').read_text(encoding='utf-8'))
    notes = [
        ('Scientific publication', 'Expert annotation of hard and soft skill mentions and domain-adapted extraction models.', 'English job postings do not establish performance on Russian/Kazakh texts or AITU profiles.', 'Evaluate extraction separately from ranking; retain reference spans and annotation rules.'),
        ('Scientific publication', 'Survey of terminology, datasets and neural skill extraction methods.', 'Different datasets and task definitions prevent direct comparison of reported scores.', 'Define the annotation unit, skill terminology and normalization rules before evaluation.'),
        ('Scientific publication', 'Multilingual domain-adaptive pre-training using the ESCO taxonomy.', 'Transfer to local occupations and languages requires validation; large-model adaptation needs resources.', 'Maintain canonical skills and aliases; consider ESCO alignment as a future extension.'),
        ('Scientific publication', 'Few-shot LLM extraction explores complex skill mentions.', 'The study does not establish universal superiority over supervised methods; inference requires quality control and resources.', 'Keep external LLM calls optional and assess extraction against fixed labels.'),
        ('Scientific publication', 'Multilingual vacancy–candidate matching through skill extraction, ESCO alignment and a knowledge graph.', 'The graph pipeline is more complex than a dictionary, and its benefit for AITU graduates remains unmeasured.', 'Compare normalization with semantic expansion and retain the origin of each match.'),
        ('Scientific publication', 'Job-title representations incorporate information from descriptions beyond extracted skills.', 'Learning job-title representations is different from assessing an individual candidate.', 'Describe the current score as skill-requirement coverage, not a probability of being hired.'),
        ('Scientific publication; foundational work', 'Siamese sentence encoders enable efficient embedding-based text comparison.', 'Text similarity does not prove skill proficiency or satisfaction of all job conditions.', 'Use similarity only as supplementary evidence with a limited contribution.'),
        ('Scientific publication', 'Contrastive learning produces sentence representations in supervised and unsupervised settings.', 'Semantic textual similarity benchmarks do not replace domain-specific matching evaluation.', 'Select an encoder using local ranking quality and latency as well as general benchmarks.'),
        ('Technical report / preprint', 'A family of multilingual retrieval embeddings offers different model sizes.', 'Input conventions, model size and inference cost affect suitability.', 'Include E5 in a future comparison; it is not the model currently configured in the prototype.'),
        ('Official classification', 'A standardized vocabulary of occupations and skills.', 'A European taxonomy requires validation in the local context.', 'Allow future external identifiers in the skill catalog.'),
        ('Official product documentation', 'Profile/resume qualifications are compared with job requirements and explained.', 'Availability may depend on subscription and rollout.', 'Compare against modern matching features rather than assuming competitors only list jobs.'),
        ('Official product documentation', 'Recommendations use student interests and platform activity.', 'Behavioral signals require interaction history.', 'Use explicit profile data for the cold-start MVP.'),
        ('Official product documentation', 'Key skills are used in job descriptions and search.', 'This source does not establish the complete current matching feature set.', 'Use hh.kz as a regional reference; mark unsupported capabilities as not established.'),
        ('Official product documentation', 'Career roles are linked to skills, courses and practical learning.', 'A product description does not establish improved employment outcomes.', 'Distinguish learning recommendations from employment probability.'),
        ('Official technical documentation', 'Typed validation and OpenAPI support.', 'Authorization and application-specific checks still require implementation.', 'Use a validated API boundary and generated Swagger documentation.'),
        ('Official technical documentation', 'Relational integrity, constraints and transactions.', 'Database operation remains a team responsibility.', 'Use foreign keys, uniqueness constraints and migrations.'),
        ('Official technical documentation', 'Embedding similarity computation.', 'A similarity threshold depends on the task and data.', 'Keep the threshold configurable and provide a keyword fallback.'),
    ]
    for record, values in zip(sources, notes):
        record.update(zip(['type', 'finding', 'limitation', 'application'], values))
    sources[12]['citation'] = 'hh.kz. Digitizing candidate skills: guidance on key skills in vacancies.'
    sources[13]['citation'] = 'Coursera. Introducing Career Academy.'
    sections = []
    def sec(title):
        b = []; sections.append({'title': title, 'blocks': b}); return b
    def p(b, text): b.append({'type':'p', 'text':text})
    def sub(b, text): b.append({'type':'h3', 'text':text})
    def t(b, headers, rows): b.append({'type':'table', 'headers':headers, 'rows':rows})
    def img(b, path, caption): b.append({'type':'image', 'path':path, 'caption':caption})

    b = sec('1. Project Proposal and Scope')
    p(b, cfg['title'] + '.')
    p(b, 'Problem statement. Graduates need to compare their educational and practical experience with heterogeneous IT job requirements and identify an actionable next step. The existence and scale of this need specifically among AITU graduates remain hypotheses until local user discussions are completed. Research on skill extraction supports the technical relevance of the task, but does not establish local demand [S01–S05].')
    p(b, 'Target users are senior AITU students and graduates, plus an administrator of the educational prototype. A career-center representative is a potential requirements expert. An employer dashboard is outside the current MVP.')
    p(b, 'Aim. Develop and evaluate a reproducible prototype that explains how a graduate profile covers IT vacancy skill requirements, identifies skill gaps and suggests development actions. The matching percentage is not a probability of employment.')
    t(b, ['Objective', 'Verifiable outcome'], [
        ['Investigate the domain', 'At least 12 meaningfully used sources, including 8 scientific publications; comparison of four systems; evidence from 3–5 real discussions once conducted.'],
        ['Specify requirements', 'A priority, acceptance criterion and verification method for each mandatory requirement.'],
        ['Design the system', 'System context, use cases, components, data relationships and API responsibilities.'],
        ['Implement the core journey', 'Profile → skills → vacancy → explained match → development actions.'],
        ['Evaluate the approach', 'Compare exact matching, normalization and optional semantics under one fixed protocol.'],
        ['Prepare submission evidence', 'Unified report, editable diagrams, traceable tasks and genuine discussion/review records.'],
    ])
    p(b, 'Included: authentication and graduate/admin roles; AITU-oriented profiles and education; skills with proficiency levels; projects, certificates and experience; vacancies and saved jobs; transparent weighted matching; saved analyses with staleness detection; recommendations and administration. The local seed contains 30 fictional vacancies clearly identified as demonstration data.')
    p(b, 'Excluded from this stage: automated hiring decisions, validated prediction of employment, university SSO/DU/Moodle integration, large-scale collection of external vacancies, production SLA, employer accounts and training a large language model. Visual similarity to university services does not imply integration or institutional endorsement.')
    p(b, 'The team consists of two students. Confirmed names and GitHub accounts are recorded below. Actual contributions are recorded when supported by completed work and review evidence.')
    t(b, ['Team member', 'Full name', 'GitHub account', 'Agreed contribution'], [
        [str(index + 1), member.get('name', ''), member.get('github', ''), member.get('contribution', '')]
        for index, member in enumerate(cfg['members'])
    ])

    b = sec('2. Evidence of Relevance and User Research')
    p(b, 'Evidence status as of 19 October 2026: no user interviews or substantive agreement with a real client have been obtained. This section specifies evidence collection rather than presenting hypothetical answers as findings. The requirement for 3–5 discussions has not yet been met.')
    t(b, ['Claim', 'Evidence status', 'Validation method'], [
        ['Skill extraction and normalization are nontrivial engineering tasks.', 'Supported by scientific literature [S01–S05].', 'Inspect errors on a locally annotated dataset.'],
        ['AITU graduates struggle to explain why a vacancy does not fit.', 'Hypothesis H1.', 'Discuss a recent job search and ask participants to interpret a vacancy.'],
        ['Gap explanations are more useful than a score alone.', 'Hypothesis H2.', 'Compare interpretation and action selection with and without explanations.'],
        ['Projects and experience support skill evidence.', 'Hypothesis H3 and an engineering assumption.', 'Discuss concrete evidence with a graduate and career adviser.'],
        ['Readiness reflects actual employment preparedness.', 'Not empirically established.', 'Compare the internal indicator with independent expert assessments.'],
    ])
    p(b, 'Planned sample: 2–3 students/graduates from different IT directions, one career-center representative and one junior recruiter or hiring specialist. Minimum: three substantive discussions; target: five. Convenience sampling limits generalization. Target dates are 20–22 October; actual meeting dates must be recorded separately.')
    p(b, 'A 20–30 minute session covers consent for anonymized notes, a recent search experience, interpretation of a vacancy, a prototype walkthrough and a check of score interpretation. Record observations or quotations separately from analyst interpretations, then link findings to requirement IDs. Do not publish identifying interview data.')
    t(b, ['Discussion prompt', 'Evidence to capture'], [
        ['How did you select your last two or three vacancies?', 'Actual process, tools and time spent.'],
        ['Which requirements are mandatory and which are preferred?', 'A concrete ambiguity or misinterpretation.'],
        ['Which skills can you support with project or experience evidence?', 'The distinction between self-assessment and observable evidence.'],
        ['What does an 80% score mean on this page?', 'Whether coverage is confused with a probability of being hired.'],
        ['What would you do next after reading the explanation?', 'An actionable next step and its rationale.'],
        ['Which profile data would you prefer not to share?', 'Privacy expectations and data-minimization needs.'],
    ])
    t(b, ['Discussion record', 'Date', 'Participant role', 'Evidence reference'], [[str(i), '', '', ''] for i in range(1,6)])
    p(b, 'After collection, assign INT-01…INT-05 to actual records, distinguish confirmed findings from assumptions and revise priorities. A rejected hypothesis must lead to a documented scope or requirement decision.')

    b = sec('3. Critical Literature Review')
    p(b, 'A targeted engineering search was performed on 19 October 2026 using ACL Anthology, arXiv and official product/technical documentation. Queries covered skill extraction from job postings, multilingual skill matching, sentence embeddings and job-title representations. Inclusion required verifiable metadata and a direct connection to extraction, retrieval or an engineering decision. This is not claimed to be an exhaustive systematic review.')
    p(b, 'The review uses 17 sources: eight peer-reviewed scientific publications S01–S08, technical report S09 and eight official materials S10–S17. The scientific core is from 2021–2025; Sentence-BERT (2019) is retained as foundational work. The limitations and applications below are the project’s analysis of transferability, not verbatim author claims.')
    t(b, ['Source and approach', 'Limitation for this project', 'Engineering implication'], [[s['id']+'. '+s['finding'], s['limitation'], s['application']] for s in sources[:9]])
    sub(b, 'Synthesis and research questions')
    p(b, 'S01–S04 motivate separating a skill mention, its canonical label and evidence of proficiency. The MVP therefore distinguishes an explicitly reported skill/level from inferred text evidence. Dictionary matching is reproducible but limited by catalog coverage and language variation. S03 and S05 motivate taxonomy alignment without establishing a need for a graph database at this scale.')
    p(b, 'S06 highlights information in vacancy descriptions beyond skill lists. The current score consequently measures only coverage of explicit or extracted skill requirements. S07–S09 justify evaluating embeddings against literal matching, but textual proximity alone does not establish competence. Semantic evidence is therefore capped at a partial contribution and its method is recorded.')
    p(b, 'RQ1: do alias normalization and optional semantic matching improve nDCG@5 over exact skill matching on a fixed profile/vacancy dataset while retaining interpretable explanations? RQ2: do users distinguish skill coverage from the probability of employment? The contribution is a testable engineering adaptation to AITU. Superiority over commercial systems is not asserted.')

    b = sec('4. Existing System Comparison')
    p(b, 'Four relevant systems are compared on eight consistent criteria using official public documentation: LinkedIn [S11], Handshake [S12], hh.kz [S13] and Coursera Career Academy [S14]. No private product accounts were audited. “Not established” means that the cited sources do not establish the capability; it does not mean the capability is absent.')
    t(b, ['Criterion', 'LinkedIn', 'Handshake', 'hh.kz', 'Career Academy'], [
        ['Primary purpose', 'Job discovery and matching', 'Early-career discovery and recommendations', 'Regional job search', 'Role-oriented skill development'],
        ['User information', 'Profile and resume', 'Profile, interests and activity', 'Resume and key skills', 'Learning pathway; vacancy matching not established'],
        ['Personalized vacancies', 'Documented', 'Documented', 'Exact mechanism not established by S13', 'Not established'],
        ['Skills and requirements', 'Profile and job qualifications', 'S12 emphasizes interests and activity', 'Key skills', 'Skills associated with a career role'],
        ['Match explanation', 'Documented', 'Per-requirement explanation not established', 'Not established', 'Role skills rather than individual vacancy fit'],
        ['Development actions', 'Profile improvement and upskilling', 'Career recommendations; detail not established', 'Not established', 'Courses and practical projects'],
        ['Published exact scoring formula', 'Not established', 'Not established', 'Not established', 'Not established'],
        ['AITU-program alignment', 'Not established', 'Not established', 'Not established', 'Not established'],
    ])
    p(b, 'Matching and skill-development recommendations already exist in competing systems. The rationale for this prototype is controllable AITU-specific adaptation, an accessible per-requirement calculation and reproducible evaluation on a fixed dataset. User discussions must still establish demand. Commercial systems are not quantitative baselines because their internal algorithms and evaluation data are unavailable.')

    b = sec('5. Technology Comparison and Architectural Decisions')
    p(b, 'The alternatives are assessed for a small educational prototype with a Python analysis module, relational data and no interaction history. Assessments are qualitative; no unperformed performance measurements are implied.')
    t(b, ['Decision', 'Reasonable alternatives and trade-offs', 'Selected solution and rationale'], [
        ['Backend platform', 'FastAPI: validation/OpenAPI and direct Python NLP integration [S15]. Django REST: mature conventions and administration, with a larger framework surface. Node.js/NestJS: a shared frontend language, but Python NLP needs an additional integration boundary.', 'FastAPI supports one small API/analysis process and a modular code structure.'],
        ['Data storage', 'PostgreSQL: relational constraints and transactions [S16]. SQLite: simple setup with a different concurrency/operation profile. MongoDB: flexible documents, with a different strategy for cross-record integrity.', 'PostgreSQL with SQLAlchemy and Alembic preserves linked profiles, catalog entries and vacancy requirements.'],
        ['Matching approach', 'Exact matching: transparent but sensitive to wording. Dictionary/aliases/weights: explainable but requires catalog maintenance. Embedding hybrid: supports paraphrases [S07–S09] but adds calibration and inference cost.', 'Weighted normalized keyword matching is the default; embeddings remain optional and require separate evaluation.'],
        ['Component communication', 'REST/JSON: straightforward CRUD and OpenAPI. GraphQL: flexible selections with an additional schema/cost-control layer. gRPC: typed binary communication but more integration work for a browser client.', 'REST/JSON under /api, with Vite/nginx proxying to a single browser origin.'],
        ['Frontend', 'React/TypeScript: typed components already implemented. Vue/TypeScript: a comparable SPA option requiring component migration. Server templates: a smaller client stack but a different approach to interactive profile editing.', 'React/TypeScript with Vite follows the implemented journeys; no unmeasured speed advantage is claimed.'],
    ])
    p(b, 'ADR-01: use a modular monolith. Authorization, API, analysis and persistence have separate code responsibilities but share one backend deployment. Revisit separation only if profiling demonstrates interference from inference. ADR-02: PostgreSQL is the source of truth; preserve algorithm version and input revisions with saved analyses. ADR-03: absence of the optional model must not break keyword analysis.')

    b = sec('6. Requirements Specification and Acceptance Criteria')
    p(b, 'MoSCoW priorities: Must denotes mandatory MVP behavior; Should denotes a planned improvement; Could denotes an optional extension. An implemented feature is not evidence that users need it. Requirement IDs connect the specification, components, tasks and verification.')
    t(b, ['ID / priority', 'Requirement', 'Acceptance criterion', 'Verification'], [
        ['FR-01 / Must', 'Registration and sessions', 'A new email creates a graduate account; invalid passwords are rejected; logout invalidates the previous access token.', 'API authentication tests; browser login/logout'],
        ['FR-02 / Must', 'Authorization boundaries', 'Other users’ records are inaccessible; graduates cannot execute admin actions or grant themselves an admin role.', 'API ownership/role tests'],
        ['FR-03 / Must', 'Profile and education', 'Program, graduation year and desired role are saved; an invalid graduation year is rejected.', 'API validation; graduate E2E'],
        ['FR-04 / Must', 'Skills and proficiency', 'Catalog skills use levels 1–3; duplicates and unknown IDs are rejected.', 'API skill tests'],
        ['FR-05 / Must', 'Portfolio', 'Projects, technologies, certificates and experience support CRUD; an end date before the start date is rejected.', 'API and portfolio E2E'],
        ['FR-06 / Must', 'Vacancies and saved jobs', 'Search/filters return matching records; details expose requirements; repeated save/remove operations are handled consistently.', 'API vacancy tests; graduate E2E'],
        ['FR-07 / Must', 'Deterministic matching', 'Identical keyword inputs/configuration produce the same score; four of five equal full matches yield 80%; no requirements yield null.', 'Unit matching tests'],
        ['FR-08 / Must', 'Explanations', 'Each requirement belongs to matched/partial/missing; contribution, weight, method, version and gap-based actions are available.', 'Matching tests; detail/analysis inspection'],
        ['FR-09 / Must', 'Stale analysis', 'Profile, vacancy or relevant context changes flag saved results as stale and offer recalculation.', 'API fingerprint/staleness tests; E2E'],
        ['FR-10 / Must', 'Administration', 'Admins manage jobs/catalogs; deleting a referenced category is handled without data loss.', 'API constraints; admin E2E'],
        ['FR-11 / Should', 'Semantic extension', 'No model triggers keyword fallback; a semantic match is labeled and contributes at most 0.5.', 'Controlled semantic/fallback tests; real-model evaluation separately'],
        ['FR-12 / Must', 'Demonstration-data labels', 'Fictional vacancies are labeled; readiness reports its sample scope and components.', 'UI inspection; career summary'],
    ])
    t(b, ['ID / priority', 'Quality attribute', 'Acceptance criterion', 'Verification'], [
        ['NFR-01 / Must', 'Security', 'Argon2id passwords, signed JWTs, HttpOnly refresh cookies, hashed refresh secrets and rejection of untrusted origins.', 'API tests; configuration review'],
        ['NFR-02 / Must', 'Integrity', 'Foreign keys, UNIQUE/CHECK constraints and migrations are enforced; repeat seeding creates no duplicates.', 'PostgreSQL tests; Alembic check'],
        ['NFR-03 / Must', 'Reproducible startup', 'A supported clean environment can run setup, migrations, seed and health checks; native Windows and Compose instructions are separate.', 'Runbook; container startup not yet verified'],
        ['NFR-04 / Must', 'Mobile usability', 'The core journey fits 390×844 without horizontal overflow; menu, inputs and actions remain available.', 'Playwright and screenshots'],
        ['NFR-05 / Should', 'Accessibility', 'Keyboard focus is visible; normal text contrast is at least 4.5:1; errors have textual descriptions.', 'Targeted audit; comprehensive audit remains outstanding'],
        ['NFR-06 / Should', 'Latency', 'Target: keyword matching p95 ≤500 ms on 30 demonstration vacancies after warm-up; no measurement is claimed.', '30 warm-up and 200 measured requests on fixed hardware'],
        ['NFR-07 / Must', 'Traceability', 'Saved results include algorithm version, mode, revisions and a context fingerprint.', 'Unit/API fingerprint tests'],
        ['NFR-08 / Must', 'Confidentiality', 'Submission files exclude .env/tokens and identifiable interview data.', 'Package inventory and staged-diff review'],
    ])
    sub(b, 'Matching and readiness rules')
    p(b, 'Score = 100 × Σ(weight × contribution) / Σ(weight). For an explicit skill, contribution = min(1, user_level / required_level); for an absent skill it is zero. Inferred text and semantic evidence are capped at 0.5. Required/preferred skill weights default to 2/1 and may be set to other positive values. Scores across different vacancies do not imply equal job difficulty.')
    p(b, 'Readiness is an internal heuristic: market 60%, projects 15%, experience 10%, certificates 5% and education 10%, with configurable normalized weights. Market uses up to five highest-scoring target-role vacancies; relevant experience is capped at 180 non-overlapping days. These weights have not been empirically validated as predictors of employment.')

    b = sec('7. Architecture, Diagrams and Data')
    p(b, 'Students/graduates and administrators use a browser application backed by FastAPI and PostgreSQL. External job boards, university SSO and DU/Moodle are not connected. The optional embedding model is loaded from a local cache; default keyword analysis does not require an external AI service.')
    for path, caption in [('context.svg','Figure 1. System context and responsibility boundaries.'),('use-cases.svg','Figure 2. User roles and protected use cases.'),('components.svg','Figure 3. Draft component architecture aligned with the implementation.')]: img(b,'diagrams/'+path,caption)
    t(b, ['Component', 'Responsibility', 'Related requirements'], [
        ['frontend/src/pages and components', 'Profile, vacancies, analysis and admin screens; routes and error states.', 'FR-03–FR-10; NFR-04/05'],
        ['auth routes and core/security.py', 'Passwords, JWTs, sessions and permission checks.', 'FR-01/02; NFR-01'],
        ['profile/jobs/admin routes', 'Input validation, CRUD, catalog and application journeys.', 'FR-03–FR-06; FR-10/12'],
        ['ai/matching.py', 'Competencies, score, gaps, recommendations, fingerprint and optional semantics.', 'FR-07–FR-09/11; NFR-07'],
        ['models/database/migrations', 'Relationships, constraints, persisted analyses and repeatable seed.', 'NFR-02/03'],
    ])
    p(b, 'Data relationships: User 1:1 GraduateProfile; GraduateProfile 1:N Education, UserSkill, Project, Certificate, Experience, MatchResult and Recommendation. UserSkill/JobSkill link profiles/jobs to Skill; ProjectSkill links project technologies. SkillAlias stores normalization rules. CareerRole and categories are controlled dictionaries. User has AuthSession records; SavedJob links users to jobs. MatchResult preserves a calculated snapshot and its input/version context.')
    p(b, 'Analysis flow: authenticate and authorize → validate profile/job → normalize catalog terms → collect structured and textual evidence → obtain requirements → calculate weighted coverage → group matched/partial/missing requirements → derive development actions → persist the result with revisions → display it. Input changes do not silently replace the saved snapshot; they flag it as stale.')
    t(b, ['API route / resource', 'Purpose'], [
        ['POST /api/auth/register, /login, /refresh, /logout', 'Account creation and session management.'],
        ['/api/profile, /api/skills, /api/projects, /api/certificates, /api/experience', 'Profile and portfolio operations; supported methods depend on the resource.'],
        ['GET /api/jobs; GET /api/jobs/{id}; POST /api/jobs/{id}/match', 'Vacancy discovery, details and matching.'],
        ['GET /api/recommendations; GET /api/admin/statistics', 'Career overview and administrator statistics.'],
        ['GET /api/health; /docs', 'Health check and generated API contract.'],
    ])
    p(b, 'The full current API contract is available locally at http://localhost:8000/docs. Diagram deliverables include editable SVG, JSON layout models, Mermaid/PlantUML sources and PNG exports. Diagram changes must remain consistent with the code and requirement IDs.')

    b = sec('8. UX and Prototype')
    p(b, 'The prototype is the working React application at http://localhost:5173. This loopback address works on the host computer and is not a remote committee-access link. Static screenshots document the existing interface in its original colors. The interface itself is Russian; explanatory report text and figure captions are English.')
    t(b, ['Journey', 'Steps', 'Expected outcome'], [
        ['UC-01: Start', 'Landing → registration/sign-in → dashboard.', 'An authenticated session and an accessible profile.'],
        ['UC-02: Profile', 'Education program → desired role → skills → project.', 'Saved data and explicit confirmation.'],
        ['UC-03: Match', 'Search → vacancy → score → detailed analysis.', 'Requirement groups and a traceable calculation.'],
        ['UC-04: Improve', 'Add FastAPI → open an old analysis → recalculate.', 'A stale warning followed by a result based on current inputs.'],
        ['UC-05: Administer', 'Admin sign-in → jobs → create/update.', 'Permission checks and validated skill requirements.'],
    ])
    p(b, 'UX states include loading, no records, validation errors, server failures, save confirmation and stale results. Focus indication, labels and accessible action names are implemented; a comprehensive accessibility audit remains outstanding. A user-evaluation task asks participants to find a relevant vacancy, identify two gaps and explain the score.')
    for file,caption in [('landing.png','Figure 4. Entry to the graduate journey.'),('dashboard.png','Figure 5. Demonstration graduate dashboard.'),('mobile.png','Figure 6. Mobile interface at 390×844.'),('job-detail.png','Figure 7. Vacancy requirements and explained matching.'),('admin.png','Figure 8. Administrative vacancy management.')]: img(b,'prototype/'+file,caption)

    b = sec('9. Verification and Evaluation Plan')
    p(b, 'Verification checks implementation against requirements. Evaluation examines ranking quality and user understanding. Passing software tests does not demonstrate improved employment outcomes or model accuracy on the real labor market.')
    t(b, ['Local check on 19 October 2026', 'Observed result'], [
        ['Pytest unit/API tests with PostgreSQL', '29 tests passed; one TestClient/httpx deprecation warning.'],
        ['Playwright Chromium', 'Four scenarios passed: graduate matching/stale analysis, mobile access, portfolio CRUD and admin vacancy management.'],
        ['TypeScript and production Vite build', 'Passed.'],
        ['Alembic check', 'No new upgrade operations detected.'],
        ['Prototype captures', 'Five actual views saved; demo administrator access confirmed.'],
    ])
    t(b, ['Level', 'Verification focus', 'Artifact'], [
        ['Unit', 'Formula, levels, boundaries, aliases, partial evidence and semantic fallback/cap.', 'backend/tests/test_matching.py'],
        ['API and database', 'Sessions, roles, ownership, CRUD, constraints and staleness.', 'backend/tests/test_api.py'],
        ['Browser', 'Graduate journey, portfolio, administration and mobile viewport.', 'frontend/tests/career.spec.ts'],
        ['Structure', 'Type checking, production build and model/migration consistency.', 'npm run build; alembic check'],
        ['Quality evaluation', 'Independent labels and a fixed baseline comparison.', 'Protocol below; experiment not yet performed'],
    ])
    p(b, 'Proposed evaluation data: 20 anonymized or synthetic profiles and 50 legally usable vacancies across four or five IT directions. Fix the dataset version, seed and hashes. Ten profiles form development data (500 pairs); the remaining ten form held-out test data (500 pairs). Two experts independently label each pair 0/1/2. Preserve disagreements before adjudication. Do not tune the dictionary or threshold on held-out judgments. Shared vacancies mean this protocol assesses new-profile rather than unseen-vacancy generalization.')
    p(b, 'B0: exact case-normalized skill-name overlap, without aliases, as an unweighted fraction. B1: the current alias dictionary, proficiency levels and weights. B2: B1 with optional semantic evidence. Use identical candidate vacancies, profiles and labels; choose the semantic threshold on development data only. Ablations without levels and without inferred evidence help explain the source of any improvement.')
    t(b, ['Metric', 'Calculation and conditions', 'Decision criterion / status'], [
        ['Precision@5', 'Fraction of top-five items labeled 2; macro-average over test profiles.', 'Measure B0/B1/B2; no values claimed.'],
        ['nDCG@5', 'Gain = 2^rel−1; ideal ranking from the same labels.', 'Primary metric; hypothesis B1>B0. Preserve negative outcomes.'],
        ['Extraction F1', 'Canonical-skill exact match against reference labels; micro and per-language results.', 'Separate extraction quality from ranking quality.'],
        ['Expert agreement', 'Weighted Cohen’s κ before resolving disagreements.', 'Report ambiguity rather than hiding disagreement.'],
        ['Latency', '30 warm-up and 200 measured requests; median/p95 on the same CPU.', 'Keyword p95 target ≤500 ms; measurement outstanding.'],
        ['Explanation comprehension', 'Five to eight volunteers identify gaps and interpret the score.', 'Pilot target: ≥80% correct responses; not representative evidence.'],
    ])
    p(b, 'Record CPU/RAM, Python/Node/PostgreSQL versions, model revision, threshold, cache state, algorithm version and data hash. Report paired nDCG differences and bootstrap intervals over test profiles with a fixed seed (for example 42 and 1,000 resamples). Small samples limit statistical power; no significance claim is justified without calculation.')
    p(b, 'Validity threats include convenience sampling, self-reported skills, synthetic vacancies, language bias, tuning leakage, facilitator effects and a small profile sample. Mitigations are independent annotation, a held-out split, negative examples, fixed comparison conditions and retention of raw judgments and errors. Docker and the real embedding model were not exercised in this environment; controlled tests do not replace their evaluation.')

    b = sec('10. Project Management, Responsibilities and Risks')
    p(b, 'The team has two members. The following work split records planned responsibilities; completed individual contributions require linked changes and review evidence. Both members should review each other’s substantive changes and share integration, user research and evaluation responsibilities.')
    t(b, ['Team member', 'Full name', 'Proposed primary responsibilities', 'Agreed contribution'], [
        ['1', cfg['members'][0].get('name', ''), 'Backend/API, database, matching implementation and automated backend verification.', cfg['members'][0].get('contribution', '')],
        ['2', cfg['members'][1].get('name', ''), 'Frontend/UX, prototype evidence, literature/comparison coordination and browser verification.', cfg['members'][1].get('contribution', '')],
    ])
    p(b, 'On 22 October 2026, the 18 saved YouTrack tasks AITU-1 through AITU-18 were migrated to GitHub repository vbl0-0/AITU-Career as issues #1 through #18. Descriptions, acceptance criteria, priorities, original due dates and source IDs are preserved. Ayadil (@vbl0-0) and Zhan (@igiiaw) each have nine assigned issues, alongside the Planned owner field. The mapping and verified API snapshot are in github-tasks.csv, github-project-migration.json and evidence/github-project-snapshot.json. The original YouTrack snapshot remains historical evidence. Application code upload, progressive contribution history, actual reviews and supervisor/committee verification remain outstanding.')
    p(b, 'Board URL: https://github.com/users/vbl0-0/projects/1. Repository URL: https://github.com/vbl0-0/AITU-Career. The public project has a Diploma Board view and a Tasks and Deadlines table. Columns are To Do, In Progress, Review and Done. All migrated tasks retain the To Do status from the saved Backlog export; completion requires actual evidence. GitHub Projects is used as the requested tracker alternative; acceptance of the substitution should be confirmed with the supervisor.')
    t(b, ['Milestone', 'Target date', 'Deliverable or dependency'], [
        ['Analysis and prototype preparation', '19 October', 'Report draft, reviewed sources, diagrams and local prototype.'],
        ['Demand validation', '20–22 October', '3–5 actual discussions and resulting requirement changes.'],
        ['Repository and tracker access', 'By 22 October', 'Public repository and GitHub Project created; both students assigned. Upload code, record reviews and verify reviewer access.'],
        ['Supervisor review', '22–23 October', 'Substantive feedback and documented response decisions.'],
        ['Submission freeze', '23 October', 'Actual evidence, final export and link/access verification.'],
        ['Team representative submits', '24 October before 18:00, UTC+5', 'Unified report and separate board/task evidence PDF.'],
    ])
    t(b, ['Risk', 'Likelihood / impact', 'Mitigation or trigger'], [
        ['No user discussions', 'High / high', 'Arrange meetings on 20–22 October; keep local-demand claims provisional.'],
        ['Committee cannot open links', 'Medium / critical', 'Check access under the intended account; localhost is insufficient.'],
        ['Late development history', 'High / high', 'Record genuine changes from now on; do not manufacture past contributions.'],
        ['False semantic matches', 'Medium / high', 'Cap inferred evidence, label its method and retain keyword baselines.'],
        ['Demo data mistaken for market evidence', 'Medium / high', 'Label the dataset and limit readiness claims.'],
        ['Documents change after export', 'Medium / medium', 'Rebuild and review the final export; tag the reviewed version.'],
        ['Form or upload problems', 'Medium / high', 'Verify fields and upload limits before the deadline.'],
    ])
    p(b, 'Workflow: personal identities → task branch → linked commit → pull/merge request → review by the other member → main. A task is complete only after its acceptance criteria are met. Tag the exact reviewed submission pre-defense-1; retain submitted tags unchanged and continue in the same repository. Earlier contributions and review comments cannot be reconstructed from a directory snapshot.')

    b = sec('11. Supervisor Feedback and Response Plan')
    p(b, 'No actual supervisor feedback has been received as of 19 October 2026. This section provides a review agenda and an empty response log. No approval, signature or positive conclusion is attributed to the supervisor.')
    t(b, ['Deliverable for review', 'Question to resolve', 'Decision evidence'], [
        ['Proposal and scope', 'Is the aim feasible and sufficiently complex?', 'A substantive comment and a linked acceptance/change decision.'],
        ['Relevance', 'Do the participants and observations support the need?', 'Discussion records and priority changes.'],
        ['Literature and comparisons', 'Are claims supported and decisions connected to sources?', 'Specific section references and revisions.'],
        ['Requirements and architecture', 'Are Must criteria testable and diagrams consistent?', 'Reviewed requirements and diagrams.'],
        ['Evaluation', 'Are labels, baselines and success criteria appropriate?', 'Protocol agreed before running the experiment.'],
    ])
    t(b, ['Review date', 'Reviewer', 'Comment / artifact', 'Response and linked change'], [['','','',''] for _ in range(4)])
    p(b, 'For each actual comment, retain the reviewed version, rationale, resulting task/commit and any follow-up confirmation. Substantive review must be distinguished from merely sharing a link or agreeing to supervise.')

    b = sec('Appendix A. References')
    for s in sources: p(b, f'[{s["id"]}] {s["citation"]} {s["type"]}. {s["url"]} Accessed 19 October 2026.')

    b = sec('Appendix B. Submission Checklist and Evidence Status')
    p(b, 'Requirements originate from the supplied 24 October checklist and submission announcement. The stated deadline is 24 October 2026 before 18:00, expressed here in Asia/Qyzylorda (UTC+5). Submission form: '+cfg['form_url']+'. An earlier automated attempt displayed only Loading; fields and file limits must be checked manually.')
    t(b, ['Requirement', 'Material prepared', 'Evidence still required'], [
        ['Proposal', 'Section 1, confirmed team names/groups and supervisor details.', 'Responsibility agreement, supervisor review and actual contribution evidence.'],
        ['Relevance', 'Research plan and empty discussion records.', '3–5 actual discussions or a substantive client agreement.'],
        ['Literature', '17 sources, including eight peer-reviewed publications.', 'Supervisor review and any topic-specific corrections.'],
        ['Systems / technology', 'Four systems × eight criteria; five technical decisions.', 'Review of applicability to the local user context.'],
        ['Requirements / architecture / UX', 'Sections 6–8, editable diagrams and actual prototype figures.', 'Feedback-based validation and revisions.'],
        ['Verification and evaluation', 'Section 9, passed local checks and a defined experiment.', 'Independent labels and quality/latency measurements at the planned stage.'],
        ['Management and traceability', 'Public GitHub Project, 18 issues and nine assignments to each personal account.', 'Application code, progressive repository history, supervisor verification and reviews.'],
        ['Supervisor feedback', 'Agenda and an empty response log.', 'Actual comments and traceable changes.'],
        ['Board/task PDF', 'tracker-evidence.pdf contains the real board and all 18 task detail pages.', 'Review readability and refresh after actual progress or account assignments.'],
        ['Unified report', 'This editable English draft and PDF export.', 'Final review after adding genuine evidence.'],
    ])
    p(b, 'One representative submits on behalf of both students. Before submission, verify the topic, supervisor details, each participant’s full name/account and actual contribution, repository/tracker links and committee access. Upload the unified report and a separate PDF of real board/task screenshots, then retain confirmation. Known names and groups are recorded from the supplied project justification; any remaining blank fields require confirmed information before final submission.')
    return sources, sections
