"""Prepare reviewable YouTrack issue payloads without making remote changes."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/pre-defense-1'
translations = [
    ('Confirm team details and project scope', 'Record the two students, group, personal accounts and supervisor in submission.json. Confirm the topic and scope with the supervisor.'),
    ('Conduct 3–5 user discussions', 'Retain actual anonymized discussion records, dates, consent and participant roles. Separate observations from assumptions.'),
    ('Revise requirements using discussion findings', 'Link each confirmed finding to FR/NFR IDs and record the rationale for changed or rejected requirements.'),
    ('Review the literature and source analysis', 'Use at least 12 meaningful sources, including eight scientific publications. Connect limitations to engineering decisions.'),
    ('Review existing systems against common criteria', 'Compare four relevant systems against eight consistent criteria. Distinguish unsupported capabilities from absent features.'),
    ('Review technology alternatives and ADRs', 'Compare at least three key decisions with two or three reasonable alternatives each. Link trade-offs to requirements.'),
    ('Review architectural diagrams', 'Check system context, use cases and components against the implementation. Retain readable exports and editable sources.'),
    ('Verify the updated interface palette and UX', 'Review the AITU-style application palette, visible keyboard focus and core desktop/mobile screens without horizontal overflow.'),
    ('Verify the application and preserve results', 'Record pytest, production build, browser E2E and Alembic results. Explicitly identify checks that were not performed.'),
    ('Prepare independent matching relevance labels', 'Freeze development/test splits, preserve independent expert ratings and record agreement before resolving disagreements.'),
    ('Evaluate matching baselines and latency', 'Compare B0/B1/B2 using nDCG@5, Precision@5 and p95 latency under fixed conditions. Preserve negative outcomes.'),
    ('Set up the shared repository and access', 'Use one real repository and personal accounts. Verify access for both students, the supervisor and committee.'),
    ('Set up the tracker and assign responsibilities', 'Create the real board and tasks. Assign the two actual participants, priorities, deadlines and acceptance criteria. Verify reviewer access.'),
    ('Link code changes and reviews to real tasks', 'Use real issue IDs in branches and commits/MRs. Link changes back to tasks and preserve review comments and individual contributions.'),
    ('Obtain substantive supervisor feedback', 'Retain actual comments on deliverables and decisions, the reviewed version and a response decision for each comment.'),
    ('Address review comments and finalize the report', 'Link revisions to actual feedback. Complete confirmed identity fields and regenerate reviewed final Word/PDF files.'),
    ('Compile actual board and task screenshots into PDF', 'Capture the real overview and readable task cards with assignees, deadlines and acceptance criteria. Combine them into one PDF.'),
    ('Verify access and submit the team materials', 'One representative verifies all links, uploads the unified report and separate tracker-evidence PDF, and submits before 18:00 UTC+5 on 24 October 2026. Retain confirmation.'),
]
with (OUT / 'tasks.csv').open(encoding='utf-8-sig', newline='') as stream:
    original = list(csv.DictReader(stream))
assert len(original) == len(translations)
issues = []
for row, (summary, criterion) in zip(original, translations):
    issues.append({
        'local_id': row['Local ID'],
        'summary': summary,
        'description': '\n\n'.join([
            '## Expected outcome\n' + criterion,
            '## Acceptance criteria\n- ' + criterion,
            '## Traceability\nReport requirement/section: ' + row['Requirement / section'].replace('приложение', 'Appendix').replace('Приложение', 'Appendix'),
            '## Planning\nDue date: ' + row['Due date'] + '\nSuggested work area: ' + row['Proposed owner role'],
            '## Evidence\nLink actual artifacts, commits and review records before marking this task complete.',
            'Local planning reference: ' + row['Local ID'],
        ]),
        'priority': row['Priority'],
        'state': 'Open',
        'assignee': None,
        'due_date': row['Due date'],
    })
plan = {
    'instance_url': 'https://aitu-career-diploma.youtrack.cloud',
    'project_name': 'AITU Career',
    'suggested_project_key': 'AITU',
    'board_name': 'AITU Career — Diploma',
    'requested_columns': ['To Do', 'In Progress', 'Review', 'Done'],
    'team_size': 2,
    'issues': issues,
    'status': 'Prepared locally; not yet created in YouTrack.',
}
snapshot_path = OUT / 'evidence/youtrack-snapshot.json'
if snapshot_path.exists():
    snapshot = json.loads(snapshot_path.read_text(encoding='utf-8'))
    actual = {item['summary']: item for item in snapshot['issues']}
    plan.update(
        status='Created in YouTrack according to the saved snapshot; personal-account assignments and reviewer access remain pending.',
        board_url=snapshot['board_url'], project_id=snapshot['project_id'],
    )
    for issue in issues:
        item = actual.get(issue['summary'])
        if item:
            issue.update(
                youtrack_id=item['idReadable'],
                url=snapshot['instance_url'] + '/issue/' + item['idReadable'],
                planned_owner=next(field['value']['name'] for field in item['customFields'] if field['name']=='Planned owner'),
                state=next(field['value']['name'] for field in item['customFields'] if field['name']=='Stage'),
            )
(OUT / 'youtrack-plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Prepared {len(issues)} English tasks for {plan["instance_url"]}; no remote writes.')
