"""Build two disjoint delivery archives without secrets, dependencies or Git history."""
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / '.local/team-delivery'
OMIT = {'.git', '.env', '.venv', '.local', '__pycache__', '.pytest_cache', 'node_modules',
        'dist', 'test-results', 'playwright-report', 'coverage'}
SUFFIXES = {'.pyc', '.pyo', '.log', '.tsbuildinfo', '.zip'}


def accepted(path):
    return not (set(path.parts) & OMIT) and path.suffix.lower() not in SUFFIXES


def candidates():
    result = [ROOT / name for name in ('.gitignore', '.env.example', 'README.md', 'docker-compose.yml')]
    for name in ('.github', 'backend', 'frontend', 'scripts', 'docs'):
        result.extend(path for path in (ROOT / name).rglob('*') if path.is_file() and accepted(path.relative_to(ROOT)))
    for path in result:
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError(f'Symlink or external file refused: {path.relative_to(ROOT)}')
    return sorted(set(result))


def destination(relative):
    path = relative.as_posix()
    if path.startswith('.github/') or path in ('.gitignore', '.env.example', 'README.md', 'docs/TEAM_DELIVERY.md', 'docs/PROJECT_AUTOMATION.md',
                'scripts/package_team_deliveries.py', 'scripts/apply-team-stage.ps1'):
        return 'Ayadil', '00-repository'
    if path.startswith('backend/'):
        return 'Ayadil', '01-backend'
    if path.startswith('frontend/'):
        return 'Zhan', '01-frontend'
    if path.startswith('docs/pre-defense-1/diagrams/') or path in (
            'docker-compose.yml', 'docs/index.html', 'docs/.nojekyll', 'docs/DEVELOPMENT.md', 'docs/VALIDATION.md', 'docs/VACANCY_IMPORT.md',
            'scripts/setup_env.py', 'scripts/start-local.ps1', 'scripts/stop-local.ps1', 'scripts/local-postgres.ps1'):
        return 'Ayadil', '02-architecture-and-run'
    if path.startswith('scripts/') or path in ('docs/I18N.md', 'docs/ORIGINAL_PROJECT_SPECIFICATION.md', 'docs/pre-defense-1/sources.json'):
        return 'Zhan', '02-research-and-report-sources'
    if path.startswith('docs/pre-defense-1/'):
        return 'Zhan', '03-submission-materials'
    raise ValueError(f'Assign this new project file explicitly before packing: {path}')


def secret_values():
    path = ROOT / '.env'
    values = []
    if path.exists():
        for line in path.read_text(encoding='utf-8').splitlines():
            key, separator, value = line.partition('=')
            value = value.strip().strip('\"\'')
            if separator and re.search(r'PASSWORD|SECRET|TOKEN', key, re.I) and len(value) >= 8:
                values.append(value.encode('utf-8'))
    return values


def main():
    files = candidates()
    secrets = secret_values()
    deliveries = {'Ayadil': {}, 'Zhan': {}}
    for file in files:
        relative = file.relative_to(ROOT)
        payload = file.read_bytes()
        if any(secret in payload for secret in secrets):
            raise ValueError(f'A local secret was detected in {relative}; no new archives created.')
        if re.search(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)', payload):
            raise ValueError(f'Credential-like content detected in {relative}; review before publishing.')
        owner, stage = destination(relative)
        entry = {'path': relative.as_posix(), 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}
        deliveries[owner].setdefault(stage, []).append((entry, payload))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifests = []
    helper = (ROOT / 'scripts/apply-team-stage.ps1').read_bytes()
    # A UTF-8 BOM makes the Russian instruction readable in Windows PowerShell 5.
    instructions = (ROOT / 'docs/TEAM_DELIVERY.md').read_text(encoding='utf-8')
    for owner, stages in deliveries.items():
        manifest = {'owner': owner, 'github_login': 'vbl0-0' if owner == 'Ayadil' else 'igiiaw',
                    'repository': 'https://github.com/vbl0-0/AITU-Career',
                    'stages': [{'name': stage, 'files': [entry for entry, _ in entries]} for stage, entries in sorted(stages.items())]}
        path = OUTPUT / f'AITU-Career-{owner}.zip'
        prefix = f'AITU-Career-{owner}'
        with ZipFile(path, 'w', compression=ZIP_DEFLATED) as archive:
            archive.writestr(prefix + '/START_HERE.md', f'# Package: {owner}\n\nGitHub: @{manifest["github_login"]}\n\n' + instructions)
            archive.writestr(prefix + '/manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
            archive.writestr(prefix + '/apply-team-stage.ps1', b'\xef\xbb\xbf' + helper.removeprefix(b'\xef\xbb\xbf'))
            for stage, entries in stages.items():
                for entry, payload in entries:
                    archive.writestr(prefix + '/stages/' + stage + '/' + entry['path'], payload)
        with ZipFile(path) as archive:
            assert archive.testzip() is None
            for stage, entries in stages.items():
                for entry, _ in entries:
                    stored = archive.read(prefix + '/stages/' + stage + '/' + entry['path'])
                    assert hashlib.sha256(stored).hexdigest() == entry['sha256']
        manifests.append(manifest)
        print(json.dumps({'archive': str(path), 'owner': owner, 'bytes': path.stat().st_size,
                          'stages': {name: len(entries) for name, entries in stages.items()}}, ensure_ascii=True))
    owned = [{entry['path'] for stage in manifest['stages'] for entry in stage['files']} for manifest in manifests]
    assert not (owned[0] & owned[1])
    assert owned[0] | owned[1] == {path.relative_to(ROOT).as_posix() for path in files}
    (OUTPUT / 'delivery-manifest.json').write_text(json.dumps({'packages': manifests, 'coverage': len(files), 'overlapping_project_paths': 0}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Validated {len(files)} project files, no overlapping delivery paths, no local secrets found.')


if __name__ == '__main__':
    main()
