"""Organize the evidenced AITU Career content as an academic submission report.

The supplied report is a layout reference only. Project facts, measurements and
figures continue to come from this project's own content and saved evidence.
"""
from copy import deepcopy
import json
import re


def prepare_academic_report(sources, sections, cfg, root):
    """Return submission front matter and the eleven chapters plus appendices."""
    result = deepcopy(sections)
    original = deepcopy(sections)
    repo = cfg['repository_url'].rstrip('/')
    tag = cfg['submission_tag']
    version = f'{repo}/tree/{tag}'
    evidence_base = f'{repo}/blob/{tag}/docs/pre-defense-1/evidence/'

    def p(text):
        return {'type': 'p', 'text': text}

    def h(text):
        return {'type': 'h3', 'text': text}

    def table(headers, rows):
        return {'type': 'table', 'headers': headers, 'rows': rows}

    def listing(items):
        return {'type': 'list', 'items': items}

    def group(number, title, blocks):
        return [h(f'{number} {title}'), *deepcopy(blocks)]

    def load_evidence(name, fallback):
        path = root / 'docs/pre-defense-1/evidence' / name
        return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else fallback

    issue_snapshot = load_evidence('github-current-issues.json', {'issues': [], 'counts': {}})
    issues = sorted(issue_snapshot.get('issues', []), key=lambda item: item['number'])
    validation = load_evidence('validation.json', {'checks': []})
    check_counts = {check['command']: check.get('count') for check in validation.get('checks', [])}
    scientific = sum(str(source.get('type', '')).startswith('Scientific publication') for source in sources)
    functional = len(original[5]['blocks'][1]['rows'])
    nonfunctional = len(original[5]['blocks'][2]['rows'])

    members = '; '.join(
        member.get('name', '') + (', ' + member['group'] if member.get('group') else '')
        for member in cfg['members']
    )
    supervisor = cfg.get('supervisor', '')
    if cfg.get('supervisor_position'):
        supervisor += ', ' + cfg['supervisor_position']
    completed = [
        f'Analysis: proposal and scope, a targeted review of {len(sources)} sources including {scientific} scientific publications, comparison of four systems against eight common criteria, and five technology decisions.',
        f'Requirements: {functional} functional and {nonfunctional} non-functional requirements with priorities, acceptance criteria and verification methods.',
        'Design: system context, protected use cases, component architecture, data relationships and an API contract; readable exports and editable diagram sources.',
        'Working version: FastAPI and PostgreSQL backend; React interface; authentication and roles; graduate portfolio, vacancies, explained skill matching, recommendations and administration.',
        'Prototype: actual application captures and a public screen walkthrough; Kazakh, Russian and English interfaces in the locally running application.',
        'Project management: a shared repository and GitHub Project with assigned tasks, original deadlines, current issue states and links to actual commits and pull requests.',
    ]
    backend_count = check_counts.get('python -m pytest')
    browser_count = check_counts.get('npm run test:e2e')
    if backend_count is not None and browser_count is not None:
        completed.insert(5, f'Verification: {backend_count} backend tests and {browser_count} browser tests passed; translation parity, production build and Alembic consistency were checked. The detailed results are in Chapter 9.')
    if cfg.get('supervisor_feedback_record'):
        completed.append('Supervisor feedback: the messages of 24 October 2026 and the reporting changes made in response are recorded in Chapter 11.')

    front_blocks = [
        table(['Field', 'Details'], [
            ['Project', cfg['title']],
            ['Team', members],
            ['Supervisor', supervisor],
            ['Repository', repo],
            ['Submitted version', version],
            ['Task tracker', cfg['tracker_url']],
            ['Prototype', cfg.get('prototype_url', '') + ' — screen walkthrough; full application runs locally'],
            ['Diagram sources', f'{repo}/tree/{tag}/docs/pre-defense-1/diagrams'],
            ['Report date', cfg.get('report_date', '')],
        ]),
        h('Completed work'),
        listing(completed),
        h('Known limitations'),
        listing([
            'The vacancy seed contains 30 fictional demonstration positions. The HeadHunter adapter is implemented, but live provider access and a real vacancy import have not been verified.',
            'The verified matching baseline uses deterministic catalogue and evidence rules. The optional embedding adapter has not been evaluated with a real model.',
            'Independent relevance labels and ranking-quality experiments are not yet available; passing functional tests establishes software behavior rather than matching effectiveness.',
            'The public prototype presents captured screens. Authentication, editing and live calculations require the locally running backend.',
            'Docker runtime, a comprehensive accessibility audit and independent human peer review remain outstanding.',
            'User interviews were optional for this submission and were not conducted. Their proposed role in later validation is described in Chapter 2.',
        ]),
        h('Outstanding tasks'),
        listing([
            'Prepare the frozen evaluation dataset and independent relevance labels (GitHub issue #10).',
            'Compare the B0/B1/B2 matching methods and record ranking quality, latency and error analysis (issue #11).',
            'Introduce reciprocal human review of substantive pull requests and retain review comments, follow-up fixes and actual contribution records.',
            'Complete the final file/link check, submit through the form and retain the real confirmation (issue #18).',
        ]),
        h('Chapters and repository files'),
        p('The report is generated from versioned project content and evidence. The following paths identify its exported chapters and the principal implementation or evidence sources.'),
        table(['Chapter', 'Repository files'], [
            ['1. Project Proposal', 'docs/pre-defense-1/01-section.html; docs/pre-defense-1/submission.json'],
            ['2. Evidence of Relevance', 'docs/pre-defense-1/02-section.html; docs/pre-defense-1/sources.json'],
            ['3. Literature Review', 'docs/pre-defense-1/03-section.html; docs/pre-defense-1/sources.json'],
            ['4. Existing System Comparison', 'docs/pre-defense-1/04-section.html; scripts/submission_content_en.py'],
            ['5. Technology Comparison', 'docs/pre-defense-1/05-section.html; scripts/submission_content_en.py'],
            ['6. Requirements Specification', 'docs/pre-defense-1/06-section.html; backend/app/ai/matching.py; backend/tests/test_matching.py'],
            ['7. Architecture and Diagrams', 'docs/pre-defense-1/07-section.html; docs/pre-defense-1/diagrams; docs/pre-defense-1/evidence/openapi.json'],
            ['8. UX and Prototype', 'docs/pre-defense-1/08-section.html; frontend/src/pages; docs/pre-defense-1/prototype'],
            ['9. Verification and Evaluation Plan', 'docs/pre-defense-1/09-section.html; docs/pre-defense-1/evidence/validation.json; backend/tests; frontend/tests'],
            ['10. Project Management and Risks', 'docs/pre-defense-1/10-section.html; docs/TEAM_DELIVERY.md; docs/pre-defense-1/evidence/development-history.json'],
            ['11. Supervisor Feedback', 'docs/pre-defense-1/11-section.html; docs/pre-defense-1/evidence/supervisor-feedback-2026-10-24.json'],
        ]),
    ]
    previous = cfg.get('previous_submission_tag')
    if previous:
        front_blocks[0]['rows'].append(['Earlier prepared version', f'{repo}/tree/{previous}'])
    front_blocks[0]['widths'] = [22, 78]
    for block in front_blocks:
        if block['type'] == 'table' and block['headers'][0] == 'Chapter':
            block['widths'] = [35, 65]

    chapter_titles = [
        'Project Proposal', 'Evidence of Relevance', 'Literature Review',
        'Existing System Comparison', 'Technology Comparison',
        'Requirements Specification', 'Architecture and Diagrams',
        'UX and Prototype', 'Verification and Evaluation Plan',
        'Project Management and Risks', 'Supervisor Feedback',
    ]
    for number, title in enumerate(chapter_titles, 1):
        result[number - 1]['title'] = f'{number}. {title}'

    b = original[0]['blocks']
    result[0]['blocks'] = [
        *group('1.1', 'Problem', b[1:2]),
        *group('1.2', 'Target users', b[2:3]),
        *group('1.3', 'Aim and objectives', b[3:5]),
        *group('1.4', 'Scope', b[5:7]),
        *group('1.5', 'Team', b[7:9]),
    ]
    result[0]['blocks'][-2] = p('The project is carried out by two students. Their confirmed identities and account-linked delivery responsibilities are recorded below; detailed contribution evidence is provided in Chapter 10.')
    result[0]['blocks'][-1] = table(['Student', 'Group', 'GitHub account'], [
        [member.get('name', ''), member.get('group', ''), member.get('github', '')]
        for member in cfg['members']
    ])

    b = original[1]['blocks']
    result[1]['blocks'] = [
        h('2.1 Sources of evidence'),
        p('Relevance at this stage is grounded in the scientific literature and system comparison in Chapters 3–4. User interviews were optional and were not conducted; local demand and user-comprehension claims therefore remain hypotheses.'),
        *group('2.2', 'Findings and assumptions', b[2:3]),
        h('2.3 Further validation'),
        p('Later validation may include anonymized discussions with graduates, career-center staff and recruiters. Record actual dates and consent, distinguish observations from interpretations, and link findings to requirement decisions.'),
    ]

    b = deepcopy(original[2]['blocks'])
    b[0]['text'] = b[0]['text'].replace(' This is not claimed to be an exhaustive systematic review.', '')
    b[1]['text'] = b[1]['text'].replace(' The limitations and applications below are the project’s analysis of transferability, not verbatim author claims.', ' The table connects the reviewed findings and limitations to engineering decisions for this project.')
    result[2]['blocks'] = [
        *group('3.1', 'Search scope', b[:2]),
        *group('3.2', 'Literature comparison', b[2:3]),
        *group('3.3', 'Synthesis and research questions', b[4:]),
    ]

    b = original[3]['blocks']
    result[3]['blocks'] = [
        *group('4.1', 'Systems and criteria', b[:1]),
        *group('4.2', 'Comparison', b[1:2]),
        *group('4.3', 'Implications for AITU Career', b[2:]),
    ]
    b = original[4]['blocks']
    result[4]['blocks'] = [
        *group('5.1', 'Technology alternatives', b[:2]),
        *group('5.2', 'Architectural decisions', b[2:]),
    ]

    b = deepcopy(original[5]['blocks'])
    b[9]['text'] = b[9]['text'].replace('Illustrative calculation, not a real student result:', 'Illustrative calculation:').replace(' This demonstrates an explainable calculation, not measured recommendation accuracy.', '')
    result[5]['blocks'] = [
        *group('6.1', 'Priorities and traceability', b[:1]),
        *group('6.2', 'Functional requirements', b[1:2]),
        *group('6.3', 'Non-functional requirements', b[2:3]),
        *group('6.4', 'Matching and readiness rules', b[4:6]),
        *group('6.5', 'AI functionality and implementation status', b[7:9]),
        *group('6.6', 'Worked example', b[9:]),
    ]

    b = original[6]['blocks']
    result[6]['blocks'] = [
        *group('7.1', 'System context', b[:2]),
        *group('7.2', 'Use cases', b[2:3]),
        *group('7.3', 'Components', b[3:5]),
        *group('7.4', 'Data model and analysis flow', b[5:7]),
        *group('7.5', 'API and editable sources', b[7:8]),
        p('OpenAPI contract: ' + evidence_base + 'openapi.json' + '. Local Swagger documentation: http://localhost:8000/docs. Editable diagram sources and exports: ' + f'{repo}/tree/{tag}/docs/pre-defense-1/diagrams' + '.'),
    ]
    b = original[7]['blocks']
    result[7]['blocks'] = [
        *group('8.1', 'Prototype access', b[:1]),
        *group('8.2', 'User scenarios', b[1:2]),
        *group('8.3', 'UX states and accessibility', b[2:3]),
        *group('8.4', 'Screen examples', b[3:]),
    ]

    b = deepcopy(original[8]['blocks'])
    b[0] = p('Verification checks the software against the specified requirements. Evaluation compares matching quality and user interpretation under controlled conditions.')
    b[2] = p('Commands, environment details and observed verification results are retained in ' + evidence_base + 'validation.json' + '.')
    b[9]['text'] = b[9]['text'].replace(' account ownership or an AI-assisted check is not treated as expert relevance annotation.', '').replace('Independent raters must be recruited;', 'Independent raters must be recruited.')
    b[10]['text'] = b[10]['text'].replace('Expected evaluation artifacts:', 'Planned evaluation artifacts:').replace(' These artifacts are planned and are not listed as already available.', '')
    result[8]['blocks'] = [
        *group('9.1', 'Verification results', b[:4]),
        *group('9.2', 'Dataset and matching baselines', b[5:7]),
        *group('9.3', 'Independent labels and evaluation metrics', b[7:9]),
        *group('9.4', 'Execution responsibilities and planned artifacts', b[9:11]),
        *group('9.5', 'Validity threats', b[11:]),
    ]

    b = deepcopy(original[9]['blocks'])
    disclosure = ('OpenAI Codex supported implementation, documentation and technical verification. '
                  'The contribution table records dated deliveries under each account. Existing modules '
                  'were imported on 23–24 October 2026; earlier individual development is not reconstructed. '
                  'No independent peer review is recorded in the checked PRs #19–25. The next-stage '
                  'review workflow is defined in Section 10.4.')
    b[1]['headers'][2] = 'Delivery record'
    for row in b[1]['rows']:
        row[2] = 'AI-assisted module delivery; linked commits and pull requests.'
    b[8]['text'] = b[8]['text'].replace(' These are the real recorded publication stages; no earlier incremental history is reconstructed.', '')
    for row in b[4]['rows']:
        if row[0] == 'Optional evidence shown as mandatory':
            row[:] = ['Different evidence requirements are confused', 'Keep interviews optional for this stage, record the received supervisor feedback, and introduce reciprocal peer review for subsequent development.']
    task_rows = []
    for issue in issues:
        deadline = re.search(r'(?:Original due date|Due date):\s*(\d{4}-\d{2}-\d{2})', issue.get('body', ''))
        due = deadline.group(1) if deadline else ''
        state = issue.get('state', '')
        reason = issue.get('state_reason')
        status = 'Completed' if state == 'closed' and reason == 'completed' else 'Not planned' if state == 'closed' and reason == 'not_planned' else 'Open'
        owners = ', '.join('@' + person['login'] for person in issue.get('assignees', []))
        title = re.sub(r'^\[AITU-\d+\]\s*', '', issue['title'])
        task_rows.append([f'#{issue["number"]}: {title}', owners, due, status])
    task_blocks = [b[3]]
    if task_rows:
        task_blocks += [table(['Task', 'Assignee', 'Original deadline', 'Status'], task_rows), p('The deadlines above are the original recorded planning dates. They are retained alongside the actual issue states; completion evidence and timestamps are available on the linked GitHub issues.')]
    task_blocks += [b[6]]
    review_steps = [
        'Create or refine a task with one responsible student, an expected result, acceptance criteria, deadline and current status.',
        'Create a task branch from the current main branch and make small commits that identify the actual task and the change performed.',
        'Open a pull request explaining the change, the task link, relevant tests and any AI assistance. Update the README and related documentation when behavior or setup changes.',
        'The other student personally reviews the diff and runs the relevant checks: Zhan reviews Ayadil’s backend changes; Ayadil reviews Zhan’s frontend and report changes.',
        'Record substantive comments, link corrective commits and obtain a recheck before approval. Preserve the actual review discussion and the participant’s implementation, testing and review actions.',
        'Merge only after acceptance checks and the required review are satisfied. Add the resulting commit or pull-request link to the task and then update its status.',
        'Before each submission, verify all shared links and the complete README, and confirm that the report and artifacts match the submitted tag. Preserve versions after they have been submitted.',
    ]
    result[9]['blocks'] = [
        h('10.1 Team contributions'), p(disclosure), b[1], b[2],
        *group('10.2', 'Task allocation, deadlines and progress', task_blocks),
        *group('10.3', 'Recorded development history', b[8:9]),
        h('10.4 Git workflow and reciprocal peer review'),
        p('The supervisor’s general guidance calls for a traceable development process and mutual review, rather than publication of completed files alone. The existing delivery history and task records are retained. The following process is planned for the next substantive changes; independent approvals and a protected-main review gate have not yet been introduced.'),
        listing(review_steps),
        p('The proposed repository gate is one independent approval with the relevant checks passing before merge. Its activation and actual human review records remain next-stage work. The checked review-status snapshot is retained in ' + evidence_base + 'peer-review-status-2026-10-24.json' + '.'),
        *group('10.5', 'Risks', b[4:5]),
    ]

    b = original[10]['blocks']
    result[10]['blocks'] = [
        h('11.1 Reviews received'),
        p('Written supervisor feedback dated 24 October 2026 was supplied to the team. The messages below contain the assessment and requested improvements. They refer to the pre-defence materials without specifying an exact reviewed commit.'),
        p('24 October 2026, 15:28 — original English message:'), b[2],
        p('24 October 2026, 15:29 — English translation of the Russian message:'), b[4],
        p('The original text and translation are retained in ' + evidence_base + 'supervisor-feedback-2026-10-24.json' + '.'),
        *group('11.2', 'Comments and decisions', b[7:8]),
        h('11.3 Follow-up'),
        p('The present revision clarifies the AI functionality, evaluation protocol and delivery evidence. Independent matching evaluation and reciprocal GitHub peer review remain prospective actions in Chapters 9–10. Further comments will be recorded with the affected artifact, the resulting task and the corrective commit or pull request.'),
    ]
    decisions = next(block for block in result[10]['blocks'] if block['type'] == 'table')
    decisions['rows'].append([
        'General guidance: demonstrate real development history, individual task ownership, deadlines/statuses and reciprocal review; keep README and shared links current.',
        'Section 10 presents the actual task register, original commit evidence and reciprocal review workflow; the submission summary maps chapters to repository files.',
        'Existing delivery records documented. Independent human review remains planned; README and link checks form part of each release check.'
    ])
    result[10]['blocks'].append(p('The additional general instruction is retained in ' + evidence_base + 'general-development-guidance.json' + '; its original message timestamp was not supplied.'))

    return front_blocks, result
