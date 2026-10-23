"""Generate local secrets once, without overwriting an existing .env."""
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parents[1]
target = ROOT / '.env'
if target.exists():
    print('.env already exists; preserved.')
else:
    db_password = secrets.token_urlsafe(24)
    jwt_secret = secrets.token_urlsafe(48)
    demo_password = secrets.token_urlsafe(18)
    content = (ROOT / '.env.example').read_text(encoding='utf-8')
    content = content.replace('aitu:CHANGE_ME@', f'aitu:{db_password}@')
    content = content.replace('POSTGRES_PASSWORD=\n', f'POSTGRES_PASSWORD={db_password}\n')
    content = content.replace('JWT_SECRET=\n', f'JWT_SECRET={jwt_secret}\n')
    content = content.replace('DEMO_PASSWORD=\n', f'DEMO_PASSWORD={demo_password}\n')
    target.write_text(content, encoding='utf-8')
    print('Created .env with generated secrets. Demo account password is DEMO_PASSWORD in .env.')
