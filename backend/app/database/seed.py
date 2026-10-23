"""Repeatable, clearly labeled fictional vacancies; never overwrites user data."""
from datetime import date
from sqlalchemy import select
from app.ai.matching import ALGORITHM_VERSION, analyze
from app.core.config import get_settings
from app.core.security import passwords
from app.database.session import SessionLocal
from app.models import CareerRole, Certificate, Education, Experience, GraduateProfile, Job, JobCategory, JobSkill, MatchResult, Project, ProjectSkill, Recommendation, Skill, SkillAlias, SkillCategory, User, UserSkill

SKILLS = {
    'Programming Languages': ['Python', 'JavaScript', 'TypeScript', 'Java', 'Go', 'C++', 'C#', 'Kotlin', 'Swift', 'Dart', 'Bash'],
    'Databases': ['SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis'],
    'Frameworks': ['FastAPI', 'Django', 'Flask', 'React', 'Vue', 'Angular', 'Node.js', 'Express', 'Spring Boot', '.NET', 'Flutter', 'React Native'],
    'DevOps': ['Docker', 'Kubernetes', 'CI/CD', 'Terraform', 'Ansible', 'Jenkins', 'GitHub Actions'],
    'Cloud': ['AWS', 'Azure', 'Google Cloud'],
    'Cybersecurity': ['Network Security', 'Linux Security', 'OWASP', 'SIEM', 'Penetration Testing'],
    'Data Science': ['Pandas', 'NumPy', 'scikit-learn', 'PyTorch', 'TensorFlow', 'Power BI', 'Tableau', 'Excel', 'Statistics', 'Machine Learning'],
    'Tools': ['Git', 'Linux', 'REST API', 'GraphQL', 'Figma', 'Postman', 'Jira', 'Selenium', 'Playwright', 'pytest', 'Networking'],
    'Soft Skills': ['Communication', 'Teamwork', 'Problem Solving', 'English', 'Agile'],
}
ALIASES = {'JavaScript': ['JS', 'JavaScript Development', 'JS Programming'], 'TypeScript': ['TS'],
           'PostgreSQL': ['Postgres'], 'Node.js': ['NodeJS', 'Node JS'], 'C#': ['C Sharp'],
           'C++': ['CPP'], 'AWS': ['Amazon Web Services'], 'Google Cloud': ['GCP'],
           'scikit-learn': ['sklearn'], '.NET': ['dotnet'], 'CI/CD': ['continuous integration'],
           'React': ['React.js', 'ReactJS'], 'Power BI': ['PowerBI']}
ROLES = ['Software Engineer', 'Backend Developer', 'Frontend Developer', 'Full-Stack Developer',
         'Mobile Developer', 'Data Analyst', 'Data Scientist', 'Machine Learning Engineer',
         'DevOps Engineer', 'QA Engineer', 'Cybersecurity Specialist', 'Cloud Engineer', 'System Administrator']
# Title, company, role, required, preferred, location, level, type, salary range.
VACANCIES = [
    ('Junior Python Backend Developer', 'Steppe Digital', 'Backend Developer', ['Python', 'FastAPI', 'PostgreSQL', 'Docker', 'Git'], ['REST API'], 'Astana', 'Junior', 'Full-time', 300000, 500000),
    ('Django Backend Developer', 'Qala Systems', 'Backend Developer', ['Python', 'Django', 'PostgreSQL', 'Git'], ['Redis', 'Docker'], 'Almaty', 'Junior', 'Full-time', 350000, 550000),
    ('Java Backend Intern', 'Nomad Finance Lab', 'Backend Developer', ['Java', 'SQL', 'Git'], ['Spring Boot'], 'Astana', 'Intern', 'Internship', 150000, 220000),
    ('Go Backend Developer', 'Steppe Cloud', 'Backend Developer', ['Go', 'PostgreSQL', 'Docker', 'REST API'], ['Kubernetes'], 'Remote', 'Junior', 'Full-time', 400000, 650000),
    ('Junior React Developer', 'Qala Studio', 'Frontend Developer', ['JavaScript', 'React', 'Git', 'REST API'], ['TypeScript', 'Figma'], 'Astana', 'Junior', 'Full-time', 280000, 450000),
    ('Vue Frontend Developer', 'Nomad Commerce', 'Frontend Developer', ['JavaScript', 'Vue', 'Git'], ['TypeScript', 'Playwright'], 'Almaty', 'Junior', 'Full-time', 300000, 500000),
    ('Angular UI Engineer', 'Saryarqa Software', 'Frontend Developer', ['TypeScript', 'Angular', 'Git', 'REST API'], ['Figma'], 'Remote', 'Middle', 'Full-time', 600000, 900000),
    ('Junior Full-Stack Developer', 'Steppe Ventures', 'Full-Stack Developer', ['JavaScript', 'React', 'Node.js', 'PostgreSQL', 'Git'], ['Docker'], 'Astana', 'Junior', 'Full-time', 350000, 550000),
    ('Python Full-Stack Intern', 'Qala Education', 'Full-Stack Developer', ['Python', 'React', 'SQL', 'Git'], ['FastAPI'], 'Astana', 'Intern', 'Internship', 150000, 250000),
    ('Android Developer', 'Nomad Mobile', 'Mobile Developer', ['Kotlin', 'REST API', 'Git'], ['Java', 'Postman'], 'Almaty', 'Junior', 'Full-time', 350000, 600000),
    ('Flutter Developer', 'Steppe Apps', 'Mobile Developer', ['Dart', 'Flutter', 'Git', 'REST API'], ['Figma'], 'Remote', 'Junior', 'Full-time', 320000, 550000),
    ('iOS Developer Intern', 'Qala Mobile Lab', 'Mobile Developer', ['Swift', 'Git'], ['REST API', 'Figma'], 'Astana', 'Intern', 'Internship', 160000, 230000),
    ('Junior Data Analyst', 'Nomad Analytics', 'Data Analyst', ['SQL', 'Python', 'Pandas', 'Excel'], ['Power BI', 'Statistics'], 'Astana', 'Junior', 'Full-time', 300000, 500000),
    ('Business Intelligence Analyst', 'Saryarqa Insights', 'Data Analyst', ['SQL', 'Power BI', 'Excel', 'Statistics'], ['Python'], 'Almaty', 'Junior', 'Full-time', 350000, 550000),
    ('Data Analytics Intern', 'Steppe Research', 'Data Analyst', ['SQL', 'Excel', 'Communication'], ['Tableau'], 'Remote', 'Intern', 'Internship', 130000, 200000),
    ('Junior Data Scientist', 'Qala AI Lab', 'Data Scientist', ['Python', 'Pandas', 'NumPy', 'scikit-learn', 'Statistics'], ['SQL'], 'Astana', 'Junior', 'Full-time', 400000, 650000),
    ('Applied Data Scientist', 'Nomad Research', 'Data Scientist', ['Python', 'Machine Learning', 'Statistics', 'SQL'], ['PyTorch', 'Docker'], 'Almaty', 'Middle', 'Full-time', 700000, 1100000),
    ('ML Engineering Intern', 'Steppe AI', 'Machine Learning Engineer', ['Python', 'NumPy', 'scikit-learn', 'Git'], ['PyTorch'], 'Astana', 'Intern', 'Internship', 180000, 280000),
    ('Junior ML Engineer', 'Qala Vision', 'Machine Learning Engineer', ['Python', 'PyTorch', 'Docker', 'FastAPI'], ['AWS', 'Machine Learning'], 'Remote', 'Junior', 'Full-time', 450000, 700000),
    ('DevOps Intern', 'Nomad Infrastructure', 'DevOps Engineer', ['Linux', 'Git', 'Bash', 'Docker'], ['CI/CD'], 'Astana', 'Intern', 'Internship', 180000, 250000),
    ('Junior DevOps Engineer', 'Steppe Cloud Ops', 'DevOps Engineer', ['Linux', 'Docker', 'CI/CD', 'Terraform'], ['Kubernetes', 'AWS'], 'Almaty', 'Junior', 'Full-time', 400000, 650000),
    ('Manual QA Engineer', 'Qala Quality', 'QA Engineer', ['Postman', 'Jira', 'SQL', 'Communication'], ['Git', 'REST API'], 'Astana', 'Junior', 'Full-time', 250000, 400000),
    ('QA Automation Engineer', 'Nomad Testing', 'QA Engineer', ['Python', 'pytest', 'Selenium', 'Git'], ['Docker'], 'Remote', 'Junior', 'Full-time', 350000, 550000),
    ('Web QA Intern', 'Steppe Quality Lab', 'QA Engineer', ['JavaScript', 'Playwright', 'Git'], ['Postman'], 'Astana', 'Intern', 'Internship', 140000, 220000),
    ('Cybersecurity Intern', 'Qala Security', 'Cybersecurity Specialist', ['Networking', 'Linux', 'Network Security'], ['OWASP', 'Python'], 'Astana', 'Intern', 'Internship', 170000, 250000),
    ('Junior SOC Analyst', 'Nomad Defense', 'Cybersecurity Specialist', ['SIEM', 'Network Security', 'Linux Security'], ['Python', 'Bash'], 'Almaty', 'Junior', 'Full-time', 350000, 550000),
    ('Junior Cloud Engineer', 'Steppe Infrastructure', 'Cloud Engineer', ['AWS', 'Linux', 'Terraform', 'Docker'], ['Networking'], 'Remote', 'Junior', 'Full-time', 400000, 650000),
    ('Azure Cloud Intern', 'Qala Cloud Lab', 'Cloud Engineer', ['Azure', 'Networking', 'Linux'], ['Terraform'], 'Astana', 'Intern', 'Internship', 170000, 250000),
    ('Junior System Administrator', 'Saryarqa Networks', 'System Administrator', ['Linux', 'Networking', 'Bash'], ['Ansible', 'Docker'], 'Astana', 'Junior', 'Full-time', 280000, 450000),
    ('Junior Software Engineer', 'Nomad Engineering', 'Software Engineer', ['Java', 'Git', 'SQL', 'Problem Solving'], ['Spring Boot', 'Teamwork'], 'Almaty', 'Junior', 'Full-time', 350000, 600000),
]


def ensure(db, model, **values):
    item = db.scalar(select(model).where(model.name == values['name']))
    if not item:
        item = model(**values)
        db.add(item)
        db.flush()
    return item


def seed_catalog(db):
    """Initialize shared reference data independently of fictional demo content."""
    categories = {name: ensure(db, SkillCategory, name=name) for name in SKILLS}
    skills = {}
    for category, names in SKILLS.items():
        for name in names:
            item = ensure(db, Skill, name=name, category_id=categories[category].id)
            existing = {a.name.lower() for a in item.aliases}
            item.aliases.extend(SkillAlias(name=alias.lower()) for alias in ALIASES.get(name, []) if alias.lower() not in existing)
            skills[name] = item
    roles = {name: ensure(db, CareerRole, name=name) for name in ROLES}
    job_categories = {name: ensure(db, JobCategory, name=name) for name in ['Engineering', 'Data & AI', 'Infrastructure', 'Security', 'Quality']}
    return skills, roles, job_categories


def seed(db):
    settings = get_settings()
    skills, roles, job_categories = seed_catalog(db)
    if settings.bootstrap_admin_email or settings.bootstrap_admin_password:
        from app.database.bootstrap import bootstrap_admin
        bootstrap_admin(db, email=settings.bootstrap_admin_email, name=settings.bootstrap_admin_name,
                        password=settings.bootstrap_admin_password)
    if not settings.seed_demo:
        db.commit()
        return
    for title, company, role, required, preferred, location, level, employment, low, high in VACANCIES:
        if db.scalar(select(Job).where(Job.title == title, Job.company == company, Job.is_demo.is_(True))):
            continue
        category = 'Data & AI' if role in ['Data Analyst', 'Data Scientist', 'Machine Learning Engineer'] else 'Infrastructure' if role in ['DevOps Engineer', 'Cloud Engineer', 'System Administrator'] else 'Security' if role == 'Cybersecurity Specialist' else 'Quality' if role == 'QA Engineer' else 'Engineering'
        description = (f'{company} is a fictional demo employer looking for a {title} to join its {location} team. '
                       f'You will contribute to production-style projects, participate in code reviews, and collaborate with mentors. '
                       f'Required skills: {", ".join(required)}. Preferred skills: {", ".join(preferred)}. '
                       'Students and recent AITU graduates are encouraged to demonstrate relevant coursework and portfolio projects. '
                       'This vacancy is prepared for platform demonstration and is not an actual job advertisement.')
        item = Job(title=title, company=company, role_id=roles[role].id, category_id=job_categories[category].id,
                   description=description, location=location, experience_level=level, employment_type=employment,
                   salary_min=low, salary_max=high, is_demo=True, source='demo')
        item.skills = [JobSkill(skill_id=skills[name].id, required=True, level=2 if level == 'Middle' else 1, weight=2)
                       for name in required] + [JobSkill(skill_id=skills[name].id, required=False, level=1, weight=1) for name in preferred]
        db.add(item)
    db.commit()
    if not settings.demo_password:
        print('Vacancies and catalog seeded. Set DEMO_PASSWORD to create demo accounts.')
        return
    if len(settings.demo_password) < 10:
        raise ValueError('DEMO_PASSWORD must be at least 10 characters')
    demo = [
        ('student.demo@aitu.edu.kz', 'Demo Graduate', 'graduate', 'Software Engineering', 'Backend Developer', ['Python', 'SQL', 'Git', 'PostgreSQL', 'Docker']),
        ('analyst.demo@aitu.edu.kz', 'Demo Data Analyst', 'graduate', 'Big Data Analysis', 'Data Analyst', ['Python', 'SQL', 'Pandas', 'Excel', 'Statistics']),
        ('frontend.demo@aitu.edu.kz', 'Demo Frontend Graduate', 'graduate', 'Computer Science', 'Frontend Developer', ['JavaScript', 'React', 'Git', 'TypeScript', 'Figma']),
        ('admin.demo@aitu.edu.kz', 'Demo Administrator', 'admin', 'Software Engineering', 'Software Engineer', ['Git', 'Python']),
    ]
    for email, name, role, program, target, names in demo:
        if db.scalar(select(User).where(User.email == email)):
            continue
        user = User(email=email, password_hash=passwords.hash(settings.demo_password), role=role)
        profile = GraduateProfile(name=name, desired_role_id=roles[target].id,
                                  bio='Demonstration profile. Replace these details with your own competencies.')
        profile.education = [Education(university='Astana IT University', degree='Bachelor', program=program, graduation_year=2026)]
        profile.skills = [UserSkill(skill_id=skills[n].id, level=3 if i == 0 else 2) for i, n in enumerate(names)]
        project = Project(name=f'{target} portfolio project', description=f'A university project practicing {", ".join(names[:3])}.', project_type='Academic')
        project.technologies = [ProjectSkill(skill_id=skills[n].id) for n in names[:3]]
        profile.projects = [project]
        profile.experience = [Experience(company='AITU Demo Lab', position=f'{target} intern',
                                         description=f'Worked with {names[0]} and {names[1]} on supervised coursework.',
                                         start_date=date(2026, 6, 1), end_date=date(2026, 8, 31), employment_type='Internship')]
        profile.certificates = [Certificate(name=f'{names[0]} Fundamentals', issuer='Demo Learning Academy', issued_date=date(2026, 5, 1))]
        user.profile = profile
        db.add(user)
    db.commit()
    catalog = list(db.scalars(select(Skill)))
    for email, *_ in demo:
        user = db.scalar(select(User).where(User.email == email))
        if db.scalar(select(MatchResult).where(MatchResult.profile_id == user.profile.id)):
            continue
        jobs = list(db.scalars(select(Job).where(Job.role_id == user.profile.desired_role_id)))
        if jobs:
            best = max(jobs, key=lambda j: analyze(user.profile, j, catalog)['score'] or 0)
            result = analyze(user.profile, best, catalog)
            match = MatchResult(profile_id=user.profile.id, job_id=best.id, score=result['score'],
                                profile_revision=user.profile.revision, job_revision=best.revision,
                                algorithm_version=ALGORITHM_VERSION, result=result)
            match.recommendations = [Recommendation(profile_id=user.profile.id, content=r) for r in result['recommendations']]
            db.add(match)
    db.commit()


if __name__ == '__main__':
    with SessionLocal() as db:
        seed(db)
    print('Catalog initialization complete. Demo data follows SEED_DEMO; existing accounts are preserved.')
