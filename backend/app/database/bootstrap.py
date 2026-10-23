"""Explicit administrator provisioning; passwords never appear in CLI arguments or output."""
import argparse
import getpass
import sys
from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select
from app.core.config import get_settings
from app.core.security import passwords
from app.database.session import SessionLocal
from app.models import GraduateProfile, User
from app.repositories.common import commit
from app.schemas.inputs import Register


def bootstrap_admin(db, *, email: str, name: str, password: str = '') -> bool:
    """Create an active administrator or preserve an existing one without promotion/reset."""
    try:
        address = str(TypeAdapter(EmailStr).validate_python(email)).lower()
    except ValidationError:
        raise ValueError('Provide a valid administrator email.') from None
    existing = db.scalar(select(User).where(User.email == address))
    if existing:
        if existing.role != 'admin' or not existing.active:
            raise ValueError('This email belongs to a non-administrator or disabled account. No changes made.')
        return False
    try:
        details = Register(email=address, name=name, password=password)
    except ValidationError as error:
        # Pydantic's default exception includes input values, including the password.
        fields = ', '.join(sorted({str(item['loc'][0]) for item in error.errors()}))
        raise ValueError(f'Invalid administrator fields: {fields}. Name: 2–150 characters; password: 10–128 characters.') from None
    user = User(email=address, role='admin', password_hash=passwords.hash(details.password))
    user.profile = GraduateProfile(name=details.name)
    db.add(user)
    commit(db)
    return True


def main(argv=None):
    settings = get_settings()
    parser = argparse.ArgumentParser(description='Initialize reference data and explicitly provision an administrator.')
    parser.add_argument('--email', default=settings.bootstrap_admin_email, help='Administrator email address')
    parser.add_argument('--name', default=settings.bootstrap_admin_name, help='Administrator display name')
    parser.add_argument('--password-stdin', action='store_true', help='Read the password from one stdin line instead of prompting')
    args = parser.parse_args(argv)
    if not args.email:
        parser.error('Provide --email or BOOTSTRAP_ADMIN_EMAIL.')
    try:
        if args.password_stdin:
            password = sys.stdin.readline().rstrip('\r\n')
        else:
            password = settings.bootstrap_admin_password or getpass.getpass('Administrator password: ')
        from app.database.seed import seed_catalog
        with SessionLocal() as db:
            seed_catalog(db)
            created = bootstrap_admin(db, email=args.email, name=args.name, password=password)
            db.commit()
    except (ValueError, EOFError) as error:
        parser.exit(1, str(error) + '\n')
    print('Administrator created. Reference catalog initialized.' if created else 'Administrator already exists; account preserved. Reference catalog initialized.')


if __name__ == '__main__':
    main()
