def row(item):
    return {column.name: getattr(item, column.name) for column in item.__table__.columns
            if column.name not in {'password_hash', 'refresh_hash'}}


def skill(item):
    return {**row(item), 'name': item.skill.name, 'category': item.skill.category.name}


def project(item):
    return {**row(item), 'skill_ids': [s.skill_id for s in item.technologies],
            'technologies': [s.skill.name for s in item.technologies]}


def profile(item):
    return {**row(item), 'email': item.user.email, 'education': [row(e) for e in item.education],
            'desired_role': item.desired_role.name if item.desired_role else None}


def job(item):
    return {**row(item), 'role': item.role.name, 'category': item.category.name,
            'skills': [{**row(s), 'name': s.skill.name} for s in item.skills]}
