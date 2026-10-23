"""Apply the current submission evidence without inventing interviews or reviews."""
import json


def finalize_sections(sources, sections, cfg, root):
    def paragraph(text):
        return {'type': 'p', 'text': text}

    def table(headers, rows):
        return {'type': 'table', 'headers': headers, 'rows': rows}

    by_number = {index: section for index, section in enumerate(sections, 1)}
    repo = cfg['repository_url']
    tag = cfg['submission_tag']
    version = f'{repo}/tree/{tag}'
    prototype = cfg['prototype_url']
    diagrams = f'{repo}/tree/{tag}/docs/pre-defense-1/diagrams'
    clarification = ('On 24 October 2026, the team clarified that user interviews and '
                     'supervisor feedback are optional for this submission. This is a '
                     'team-reported requirement clarification, not a recorded supervisor approval.')
    evidence_file = root / 'docs/pre-defense-1/evidence/validation.json'
    evidence = json.loads(evidence_file.read_text(encoding='utf-8'))

    # Retain the scientific relevance argument while making its evidence limits explicit.
    first = by_number[1]['blocks']
    for block in first:
        if block['type'] == 'table' and block['headers'][0] == 'Objective':
            block['rows'][0][1] = 'At least 12 meaningfully used sources including eight scientific publications; comparison of four systems. Optional user research is planned for later validation.'
            block['rows'][-1][1] = 'Unified report, editable diagrams, traceable tasks and actual verification evidence.'
    by_number[2]['title'] = '2. Evidence of Relevance and Optional User Research'
    by_number[2]['blocks'] = [
        paragraph(clarification),
        paragraph('Relevance at this stage is supported by the literature and system comparison in Sections 3–4. No user interviews were conducted and no interview results are presented. Local demand, explanation usefulness and the employment-readiness indicator remain hypotheses rather than empirically established conclusions.'),
        table(['Claim', 'Available evidence', 'Limit'], [
            ['Skill extraction and normalization require explicit design decisions.', 'Scientific publications S01–S05.', 'Transfer to Kazakh/Russian and AITU profiles needs local evaluation.'],
            ['Existing services combine vacancy matching and skill development.', 'Official system materials S11–S14 and the common-criteria comparison.', 'This does not prove unmet local demand or superiority of this prototype.'],
            ['Explanations can expose covered, partial and missing skills.', 'Implemented calculation and automated functional checks.', 'User comprehension and usefulness have not been measured.'],
            ['Employment readiness summarizes profile and vacancy evidence.', 'Documented configurable heuristic.', 'It is not a validated predictor of hiring success.'],
        ]),
        paragraph('Future optional research may include anonymized discussions with graduates, career-center staff and recruiters. Findings should be recorded with actual dates and consent, separated from interpretations and linked to requirement decisions. Such evidence is not a prerequisite for this submission and no participant identities or fabricated responses are included.'),
    ]

    for block in by_number[4]['blocks']:
        if block['type'] == 'p':
            block['text'] = block['text'].replace('User discussions must still establish demand.', 'Optional future user research can test the local-demand hypothesis.')
    for block in by_number[7]['blocks']:
        if block['type'] == 'p' and block['text'].startswith('Students/graduates'):
            block['text'] = 'Students/graduates and administrators use React, FastAPI and PostgreSQL. An explicit HeadHunter API adapter supports import, refresh, deduplication and source/availability tracking; live provider access was not available and no real import is claimed. University SSO and DU/Moodle are not integrated. Default keyword analysis needs no external AI service; the optional embedding model is disabled in the verified configuration.'
    by_number[7]['blocks'].append(paragraph('Editable diagram sources and exports: ' + diagrams + '. Local OpenAPI: http://localhost:8000/docs. The API is not publicly hosted by the static prototype viewer.'))
    by_number[8]['blocks'][0] = paragraph('Public screen walkthrough: ' + prototype + '. It presents actual captures of the local application with navigation between screens, not a hosted backend or live editing service. The complete application runs locally using the published development instructions. The interface supports Kazakh, Russian and English; the report is in English. Original screenshot and diagram colors are preserved.')

    results = []
    for check in evidence['checks']:
        detail = check.get('note', '')
        count = check.get('count')
        if count is not None:
            detail = f'{count} checks passed. ' + detail
        results.append([check['command'], check['result'] + (': ' + detail if detail else '')])
    for block in by_number[9]['blocks']:
        if block['type'] == 'table' and block['headers'][0].startswith('Local check'):
            block['headers'] = ['Verification on 24 October 2026', 'Observed result']
            block['rows'] = results
    by_number[9]['blocks'].insert(2, paragraph('Machine-readable results: ' + f'{repo}/blob/{tag}/docs/pre-defense-1/evidence/validation.json' + '. The initial connection timeout was resolved by starting the existing project PostgreSQL cluster; no application tables were replaced. Software checks do not establish ranking quality, real-market coverage or improved employment outcomes.'))

    by_number[10]['blocks'] = [
        paragraph('The two accounts publish current module deliveries with actual dates. Account attribution documents delivery and verification; it does not reconstruct earlier development history or prove independent authorship of every line. Packaging, code assistance, verification and publication were assisted by OpenAI Codex. No human teammate approval or supervisor approval is claimed.'),
        table(['Member', 'Published responsibility and evidence'], [
            [member['name'], member['contribution']] for member in cfg['members']
        ]),
        paragraph('Merged delivery records: ' + repo + '/pull/19 (repository automation); ' + repo + '/pull/20 (frontend); ' + repo + '/pull/21 (backend and regression tests); ' + repo + '/pull/22 (research and report sources). Further delivery PRs are recorded in the repository and linked issue comments. Original commits are preserved through merge commits.'),
        paragraph('Tracker: ' + cfg['tracker_url'] + '. The 18 original tasks retain their source IDs, priorities, planned owners and original deadlines. GitHub Issues contain actual acceptance criteria, account assignments and completion evidence. Optional interview/feedback tasks are distinguished from completed work. Later-stage independent labels and matching-quality experiments are not marked complete.'),
        table(['Risk or remaining limit', 'Response'], [
            ['Static prototype versus the complete application', 'The public viewer is clearly labelled; use the development guide to run authenticated CRUD and matching.'],
            ['Demonstration vacancies mistaken for live jobs', 'The seed dataset is fictional and labelled. No live HeadHunter import or current market representativeness is claimed.'],
            ['Unmeasured model or employment outcomes', 'Keep the evaluation protocol; do not infer efficacy from passing implementation tests.'],
            ['Confusing account history with individual authorship', 'Preserve real dates and links; state the use of AI assistance and distinguish delivery from historical authorship.'],
            ['Documents differ from the submitted version', 'Use the exact prob-period-1 tag and the matching PDF exports; do not move the submitted tag.'],
            ['Optional evidence shown as mandatory', 'Record the team clarification and keep future interviews/reviews optional.'],
        ]),
        paragraph('Submission version: ' + version + '. One representative submits both students\' materials before 18:00 UTC+5 on 24 October 2026. A form confirmation is retained only after actual submission.'),
    ]
    current_issues = root / 'docs/pre-defense-1/evidence/github-current-issues.json'
    if current_issues.exists():
        counts = json.loads(current_issues.read_text(encoding='utf-8'))['counts']
        by_number[10]['blocks'].append(paragraph('Tracker snapshot: '+str(counts['completed'])+' completed, '+str(counts['not_planned'])+' optional activities closed as not planned, and '+str(counts['open'])+' open. GitHub\'s built-in closed-item workflow places both closure types in Done; the issue state reason distinguishes cancelled scope from performed work. Snapshot: '+f'{repo}/blob/{tag}/docs/pre-defense-1/evidence/github-current-issues.json'+'.'))
    by_number[11]['title'] = '11. Review Status and Optional Supervisor Feedback'
    by_number[11]['blocks'] = [
        paragraph(clarification),
        paragraph('No substantive supervisor feedback has been supplied and no approval, signature, meeting or quotation is invented. The absence of optional feedback is not treated as an incomplete mandatory requirement. Independent human peer review is not claimed; available automated technical reviews and corrections are recorded on the actual GitHub issues and PRs.'),
        table(['Actual revision', 'Rationale and evidence'], [
            ['Clarify optional interviews and supervisor feedback.', 'Team clarification relayed on 24 October 2026; Sections 2 and 11 now state the actual evidence status.'],
            ['Update current implementation verification.', '60 backend tests, full browser tests, translation parity, production build and migration checks are recorded in the validation artifact.'],
            ['Document real deliveries and contributions.', 'Merged PRs and original account-linked commits; Section 10 distinguishes publication from initial code authorship.'],
            ['Use the required submission tag and accessible materials.', 'prob-period-1 links, public screen walkthrough, editable diagram sources and separate report/task PDFs.'],
        ]),
        paragraph('If optional feedback is received later, record its actual date, reviewed version, comment, response and linked change. Do not retroactively attribute the current technical checks to the supervisor.'),
    ]
    by_number[13]['blocks'] = [
        paragraph('Submission form: ' + cfg['form_url'] + '. The provided screenshots specify a repository URL, the exact prob-period-1 version URL, individual contributions, current status, one board/task PDF (maximum 10 MB) and one consolidated report PDF (maximum 100 MB). This report contains the eleven main sections in order and a table of contents.'),
        table(['Requirement', 'Prepared artifact', 'Scope or remaining limit'], [
            ['Repository and version', repo + '; ' + version, 'The tag identifies the submitted package.'],
            ['Identity and contributions', 'Confirmed names, groups, supervisor and account-linked delivery records.', 'AI assistance and current-delivery limits are disclosed.'],
            ['Research and comparisons', '17 sources including eight scientific publications; four systems and eight common criteria; five technology decisions.', 'Local user demand and real matching quality are not empirically established.'],
            ['Requirements and architecture', 'Testable FR/NFR criteria and editable diagram sources/exports.', diagrams],
            ['Prototype', prototype, 'A public screen walkthrough; the complete API-backed application runs locally.'],
            ['Verification', 'Current backend, browser, build, translation and migration results.', 'Docker runtime and real embedding-model evaluation were not performed.'],
            ['Optional interviews and feedback', 'Actual absence and team clarification recorded.', 'No fabricated interview, approval or review record.'],
            ['Task evidence PDF', 'tracker-evidence.pdf with genuine board and task captures.', 'Tasks show actual progress; later-stage work can remain open.'],
            ['Unified editable report', 'report.docx, report.html and matching report.pdf.', 'Use the final named PDF copy for the form.'],
            ['Form submission', 'Prepared answers and both upload files.', 'The representative must verify the final form page and retain the actual confirmation.'],
        ]),
        paragraph('Report upload filename: ' + cfg['report_upload_filename'] + '. Deadline: 24 October 2026 before 18:00 UTC+5. Known fields are completed; any genuinely unknown personal information stays blank. The package does not assert that the form has already been submitted.'),
    ]
    return sources, sections
