# AI-Based Platform to Support the Employment of Astana IT University Graduates

## Implementation and local launch

The working implementation is in `frontend/` and `backend/`. Setup, demo accounts, matching formulas, optional semantic matching, and testing instructions: [Development guide](DEVELOPMENT.md).

```bash
python scripts/setup_env.py
docker compose up --build
```

Website: http://localhost:8080. Windows without Docker: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-local.ps1` (see the guide for the PostgreSQL binary path).

The original project specification is preserved below.

## Project Overview

This project is an AI-based web platform designed to support Astana IT University (AITU) students and graduates in finding suitable employment opportunities.

The platform analyzes a graduate's education, technical skills, soft skills, projects, certificates, and experience, and compares this information with the requirements of IT job vacancies.

The main goal is not to create another simple job board. The platform should provide intelligent career support by answering:

- Which vacancies are suitable for the graduate?
- How well does the graduate match a specific vacancy?
- Which required skills does the graduate already have?
- Which skills are missing?
- What skills should the graduate improve?
- Which IT career directions are most suitable?

## Main Workflow

```text
Graduate Profile
       ↓
Competency Analysis
       ↓
Job Vacancy Analysis
       ↓
AI Matching
       ↓
Match Score
       ↓
Skill Gap Analysis
       ↓
Personalized Recommendations
```

## 1. Target Users

### Graduate / Student

The graduate should be able to:

- Register and log in
- Create and edit a personal profile
- Specify education
- Add technical skills
- Add soft skills
- Add projects
- Add certificates
- Add internship/work experience
- Select a desired career direction
- Browse IT vacancies
- Receive AI-based matching results
- See missing skills
- Receive career recommendations

### Administrator

The administrator should be able to:

- Manage users
- Add vacancies
- Edit vacancies
- Delete vacancies
- Manage skills
- Manage job categories
- View basic platform statistics

The first version should focus mainly on graduate functionality.

## 2. AITU-Specific Focus

The platform should be specifically adapted for Astana IT University.

A graduate profile should contain:

- University
- Degree
- Educational program
- Graduation year
- Technical skills
- Soft skills
- Programming languages
- Technologies
- Tools
- Projects
- Certificates
- Internship experience
- Work experience
- Preferred job role

The platform should connect:

```text
AITU Education
       ↓
Competencies
       ↓
IT Job Roles
       ↓
Employment Opportunities
```

The system should feel like an AITU-focused employment platform rather than a generic job website.

## 3. Main Problem

Graduates often have difficulty understanding whether they are ready for a specific job.

For example, a graduate may know:

```text
Python
SQL
Git
PostgreSQL
```

while a job vacancy requires:

```text
Python
FastAPI
PostgreSQL
Docker
Git
```

A normal job platform simply shows the vacancy.

Our platform should additionally explain:

```text
Match Score: 75%

Matched Skills:
- Python
- PostgreSQL
- Git

Missing Skills:
- FastAPI
- Docker
```

The system should then recommend what the graduate should learn.

## 4. Main Features

### 4.1 Authentication

Users should be able to:

- Register
- Log in
- Log out
- Securely access their profile

Use JWT authentication and secure password hashing.

### 4.2 Graduate Profile

The graduate should be able to create and edit a profile.

Personal information:

- Name
- Email
- Phone
- Location

Education:

- University
- Degree
- Program
- Graduation year

Career preferences:

- Desired position
- Preferred technologies
- Preferred employment type
- Preferred location

## 5. Skills

Users should be able to add their skills.

Each skill should contain:

- Skill name
- Category
- Proficiency level

Example:

```text
Python       — Advanced
SQL          — Intermediate
Git          — Intermediate
PostgreSQL   — Intermediate
Docker       — Beginner
```

Possible categories:

- Programming Languages
- Databases
- Frameworks
- DevOps
- Cloud
- Cybersecurity
- Data Science
- Soft Skills
- Tools

## 6. Projects

Users should be able to add projects.

Each project should contain:

- Project name
- Description
- Technologies
- GitHub URL
- Project type

Example:

```text
Project:
Food Store Backend

Technologies:
Go
PostgreSQL
Docker
REST API
```

Projects should be considered when generating career recommendations.

## 7. Certificates

Users should be able to add certificates.

Example:

```text
Certificate:
AWS Cloud Practitioner

Issuer:
Amazon Web Services

Date:
2026
```

## 8. Experience

Users should be able to add:

- Internships
- Part-time jobs
- Full-time jobs
- Freelance experience

Each experience should contain:

- Company
- Position
- Description
- Start date
- End date

## 9. Job Vacancies

The platform should contain IT job vacancies.

Each vacancy should have:

- Job title
- Company
- Location
- Description
- Employment type
- Experience level
- Salary
- Required skills
- Preferred skills

Example:

```text
Position:
Junior Backend Developer

Required Skills:
Python
FastAPI
PostgreSQL
Docker
Git

Experience:
0-1 years
```

For the MVP, use a prepared dataset of IT vacancies.

Do not make the entire system dependent on an external job website.

The application should include demo/seed data.

Create at least 20-50 realistic IT vacancies.

## 10. Supported IT Career Directions

The platform should support different IT positions, for example:

- Software Engineer
- Backend Developer
- Frontend Developer
- Full-Stack Developer
- Mobile Developer
- Data Analyst
- Data Scientist
- Machine Learning Engineer
- DevOps Engineer
- QA Engineer
- Cybersecurity Specialist
- Cloud Engineer
- System Administrator

The system should be designed so that additional positions can be added later.

## 11. AI Competency Analysis

The AI module should analyze the graduate profile and identify relevant competencies.

For example:

```text
Profile:

Python
SQL
PostgreSQL
Git
Docker

Experience:
Backend development

Projects:
REST API
```

The system should transform this information into a structured competency profile.

## 12. Vacancy Analysis

The AI/NLP module should analyze job descriptions.

Example:

```text
We are looking for a Backend Developer
with experience in Python, FastAPI,
PostgreSQL, Docker and Git.
```

The system should extract:

```text
Python
FastAPI
PostgreSQL
Docker
Git
```

These extracted requirements will be used by the matching algorithm.

## 13. AI Matching

The most important AI feature is matching a graduate profile with a job vacancy.

The system should calculate a matching score from 0 to 100%.

Example:

```text
Graduate Skills:

Python
SQL
Git
PostgreSQL
Docker

Vacancy Requirements:

Python
FastAPI
PostgreSQL
Docker
Git
```

Result:

```text
Match Score: 85%
```

The system should show:

### Matched Skills

- Python
- PostgreSQL
- Docker
- Git

### Missing Skills

- FastAPI

The score must be calculated from actual user skills and vacancy requirements.

Do not generate random matching percentages.

## 14. Semantic Matching

The system should support semantic similarity when possible.

For example:

```text
JavaScript Development
```

and

```text
JS Programming
```

should be recognized as related skills.

Possible technology:

```text
sentence-transformers
```

or another suitable embedding model.

However, the system should also contain a simple keyword-based fallback.

## 15. Skill Gap Analysis

After matching the graduate with a vacancy, the system should identify:

1. Matched skills
2. Partially matched skills
3. Missing skills

Example:

```text
MATCHED

Python
Git
PostgreSQL
Docker

PARTIALLY MATCHED

AWS

MISSING

FastAPI
Kubernetes
```

This information should be clearly displayed to the user.

## 16. AI Recommendations

The system should generate personalized recommendations.

Example:

```text
Your profile is suitable for Junior Backend Developer
positions.

To improve your compatibility with current vacancies,
we recommend focusing on:

1. FastAPI
2. Docker
3. AWS fundamentals
```

Recommendations may include:

- Skills to learn
- Technologies to practice
- Project ideas
- Career directions
- Profile improvements

Recommendations should be short and practical.

## 17. Employment Readiness

The platform should provide an overall employment readiness indicator.

Example:

```text
Employment Readiness

78%
```

This score can be based on:

- Skills
- Experience
- Projects
- Certificates
- Education
- Market requirements

The exact formula should be transparent and configurable.

## 18. Dashboard

The graduate dashboard should contain:

### Employment Readiness

```text
78%
```

### Top Skills

```text
Python       85%
SQL          80%
Git          75%
PostgreSQL   72%
```

### Recommended Jobs

```text
Backend Developer       87%
Python Developer        84%
Software Engineer       80%
Data Analyst            72%
```

### Skill Gap

```text
Docker
FastAPI
AWS
```

### AI Recommendation

```text
Your profile is highly suitable for junior backend
positions. Learning FastAPI and improving Docker
skills can increase your compatibility with
backend developer vacancies.
```

## 19. Main Pages

The application should contain:

1. Landing Page
2. Login
3. Registration
4. Dashboard
5. My Profile
6. My Skills
7. My Projects
8. My Certificates
9. My Experience
10. Vacancies
11. Vacancy Details
12. Match Analysis
13. Career Recommendations
14. Admin Dashboard

## 20. Vacancy Details

The vacancy details page is one of the most important pages.

It should contain:

- Job title
- Company
- Location
- Description
- Requirements

And an AI section:

```text
YOUR MATCH

82%
```

### Matched Skills

```text
Python
Git
PostgreSQL
Docker
```

### Missing Skills

```text
FastAPI
```

### AI Explanation

```text
Your profile matches most of the required
backend development skills.

Your main competency gap is FastAPI.
```

## 21. Technology Stack

### Frontend

- React
- JavaScript or TypeScript
- HTML
- CSS

### Backend

- Python
- FastAPI

### Database

- PostgreSQL

### ORM

- SQLAlchemy

### Database Migrations

- Alembic

### AI / ML

Possible libraries:

- scikit-learn
- sentence-transformers
- numpy
- pandas

An external LLM API can be used if necessary.

API keys must never be hardcoded.

Use environment variables.

Example:

```env
OPENAI_API_KEY=
```

### Authentication

- JWT
- Secure password hashing
- Role-based access

### Containerization

- Docker
- Docker Compose

The project should be possible to start with:

```bash
docker compose up
```

## 22. System Architecture

Recommended architecture:

```text
                    ┌───────────────────┐
                    │     Graduate      │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │     Frontend      │
                    │       React       │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │      Backend      │
                    │      FastAPI      │
                    └─────────┬─────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
     ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
     │ PostgreSQL  │   │  AI / NLP   │   │ Job Module  │
     └─────────────┘   └──────┬──────┘   └─────────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │  AI Matching    │
                      │  Skill Gap      │
                      │  Recommendations│
                      └─────────────────┘
```

## 23. Database Structure

Main entities:

```text
User
GraduateProfile
Education
Skill
UserSkill
Project
Certificate
Experience
Job
JobSkill
SavedJob
MatchResult
Recommendation
```

Main relationships:

```text
User
 ↓
GraduateProfile
 ├── Education
 ├── UserSkill
 ├── Project
 ├── Certificate
 └── Experience

Job
 ↓
JobSkill

GraduateProfile + Job
 ↓
MatchResult
 ↓
Recommendation
```

Use foreign keys and proper relational database design.

## 24. Backend API

Example API structure:

```text
POST /api/auth/register
POST /api/auth/login

GET /api/profile
PUT /api/profile

GET /api/skills
POST /api/skills
PUT /api/skills/{id}
DELETE /api/skills/{id}

GET /api/projects
POST /api/projects
PUT /api/projects/{id}
DELETE /api/projects/{id}

GET /api/jobs
GET /api/jobs/{id}

POST /api/jobs/{id}/match

GET /api/recommendations
```

Admin:

```text
GET /api/admin/users

POST /api/admin/jobs
PUT /api/admin/jobs/{id}
DELETE /api/admin/jobs/{id}
```

Use Pydantic schemas and proper validation.

## 25. Security

Implement:

- JWT authentication
- Secure password hashing
- Protected routes
- Role-based authorization
- Input validation
- CORS configuration
- Environment variables
- No secrets in source code

Never commit `.env`.

Provide:

```text
.env.example
```

## 26. Testing

Use:

```text
pytest
```

Test at least:

- Registration
- Login
- Profile creation
- Skills
- Projects
- Job retrieval
- Matching algorithm
- Skill gap detection
- Recommendations

The matching algorithm should have unit tests with predictable results.

## 27. Demo Data

The project should contain seed data.

Include:

- Several graduate profiles
- 20-50 IT vacancies
- Multiple skills
- Different job roles
- Example recommendations

Example vacancies:

- Junior Backend Developer
- Frontend Developer
- Full Stack Developer
- Data Analyst
- QA Engineer
- DevOps Intern
- Cybersecurity Intern
- Python Developer
- Java Developer
- Software Engineer

The platform should work immediately after installation without manually entering all data.

## 28. Project Structure

Recommended structure:

```text
project-root/

├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── ...
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── ai/
│   │   ├── database/
│   │   └── utils/
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── ...
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## 29. Development Phases

### Phase 1 — Analysis

- Study the existing university prototype.
- Analyze existing employment platforms.
- Define AITU-specific requirements.
- Define system users.
- Define competencies and job roles.

### Phase 2 — System Design

- Design architecture.
- Design database.
- Design API.
- Design UI/UX.
- Define competency model.

### Phase 3 — Backend

Implement:

- Authentication
- Users
- Profiles
- Skills
- Projects
- Certificates
- Experience
- Vacancies

### Phase 4 — Frontend

Implement:

- Login
- Registration
- Dashboard
- Profile
- Skills
- Projects
- Vacancies
- Vacancy Details

### Phase 5 — Matching

Implement:

- Keyword matching
- Match score
- Matched skills
- Missing skills

### Phase 6 — AI

Implement:

- NLP vacancy analysis
- Competency extraction
- Semantic matching
- Skill gap analysis
- Recommendations

### Phase 7 — Admin

Implement:

- Vacancy management
- User management
- Skill management
- Statistics

### Phase 8 — Testing

Test:

- Authentication
- Profile
- Vacancies
- Matching
- Recommendations
- API

### Phase 9 — Deployment

Add:

- Docker
- Docker Compose
- Environment configuration
- Database migrations
- Seed data

### Phase 10 — Finalization

- Fix bugs
- Improve UI
- Improve performance
- Write documentation
- Prepare demonstration

## 30. MVP Scope

The first working version should focus on:

```text
Registration
     ↓
Graduate Profile
     ↓
Skills
     ↓
Job Vacancies
     ↓
AI Matching
     ↓
Match Score
     ↓
Skill Gap
     ↓
Recommendations
```

Do not implement unnecessary features before this workflow works correctly.

## 31. Example Complete Scenario

A graduate registers on the platform.

The graduate creates a profile:

```text
University:
Astana IT University

Program:
Software Engineering

Skills:
Python
SQL
Git
PostgreSQL
Docker
```

The graduate selects:

```text
Target Role:
Backend Developer
```

The system analyzes available vacancies.

It finds:

```text
Junior Backend Developer

Required:
Python
FastAPI
PostgreSQL
Docker
Git
```

The system calculates:

```text
Match Score: 85%
```

Then displays:

```text
Matched Skills:

Python
PostgreSQL
Docker
Git
```

```text
Missing Skills:

FastAPI
```

The system generates:

```text
AI Recommendation:

Your profile is highly suitable for this position.
Learning FastAPI would improve your compatibility
with backend developer vacancies.
```

The user can then:

- Save the vacancy
- View other recommended jobs
- Improve their profile
- Add new skills
- View career recommendations

## 32. Important Development Rules

1. Build a working MVP first.
2. Do not implement unnecessary features.
3. Do not generate random AI scores.
4. Matching must be based on actual user and vacancy data.
5. Keep AI logic explainable.
6. Use clean modular architecture.
7. Keep frontend and backend separated.
8. Use PostgreSQL.
9. Use environment variables for secrets.
10. Provide seed/demo data.
11. Provide Docker configuration.
12. Provide tests.
13. Provide clear documentation.
14. Make the project easy to run locally.
15. Do not hardcode user information.
16. Do not depend completely on external job websites.
17. Prioritize working functionality over unnecessary complexity.

## 33. Final Project Goal

The final system should demonstrate that an AITU graduate can:

```text
Create Profile
      ↓
Add Competencies
      ↓
Select Career Direction
      ↓
View IT Vacancies
      ↓
Receive AI Match Score
      ↓
See Skill Gaps
      ↓
Receive Personalized Recommendations
      ↓
Improve Employment Readiness
```

The final product should be a functional AI-based employment support platform specifically adapted for Astana IT University graduates.

## 34. First Development Step

Before implementing the entire system, inspect the current project directory.

Then provide:

1. Final system architecture
2. Recommended folder structure
3. Database entities and relationships
4. API structure
5. AI matching approach
6. Development phases

Do not immediately implement the entire application.

First prepare the architecture and wait for confirmation.
