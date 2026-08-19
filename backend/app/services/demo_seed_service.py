from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Job, JobRequirement, Resume, ResumeEvidence
from app.repositories.users import get_or_create_demo_user

DEMO_RESUME_FILENAME = "demo-ana-souza-resume.txt"
DEMO_JOB_TITLE = "Backend Software Engineer Intern (Demo)"
DEMO_JOB_COMPANY = "Nubank"

DEMO_RESUME_TEXT = """
Ana Souza is a computer science student focused on backend engineering and data products.
She built a FastAPI service with PostgreSQL for a university finance project, including
REST endpoints, SQL queries, pytest coverage and Docker-based local development. Ana also
worked on a Python data pipeline that cleaned CSV files, generated reports and documented
tradeoffs for non-technical stakeholders. She uses Git and GitHub in team projects, writes
clear pull request notes and communicates progress in English and Portuguese. Ana is
available for a full-time internship starting January 2027 and is authorized to work in Brazil.
""".strip()

DEMO_JOB_DESCRIPTION = """
Nubank is looking for a backend software engineer intern to help build reliable financial
products. The person should have experience with Python or another backend language, SQL
databases, REST APIs, Git, automated tests and clear communication. Experience with Docker,
cloud services or financial products is a plus. The internship requires availability for a
full-time program in Brazil and comfort collaborating with product, design and engineering teams.
""".strip()

DEMO_EVIDENCE = [
    {
        "skill": "Python",
        "evidence_text": (
            "Built a FastAPI backend and a Python data pipeline for university projects."
        ),
        "source": "demo_resume",
        "evidence_type": "project",
    },
    {
        "skill": "SQL and PostgreSQL",
        "evidence_text": "Used PostgreSQL and SQL queries in a university finance project.",
        "source": "demo_resume",
        "evidence_type": "project",
    },
    {
        "skill": "REST APIs",
        "evidence_text": "Implemented REST endpoints in a FastAPI service.",
        "source": "demo_resume",
        "evidence_type": "project",
    },
    {
        "skill": "Testing",
        "evidence_text": "Added pytest coverage for backend behavior.",
        "source": "demo_resume",
        "evidence_type": "project",
    },
    {
        "skill": "Docker",
        "evidence_text": "Used Docker-based local development for backend services.",
        "source": "demo_resume",
        "evidence_type": "project",
    },
    {
        "skill": "Communication",
        "evidence_text": "Documents tradeoffs and communicates progress in English and Portuguese.",
        "source": "demo_resume",
        "evidence_type": "skill",
    },
    {
        "skill": "Availability",
        "evidence_text": "Available for a full-time internship starting January 2027 in Brazil.",
        "source": "demo_resume",
        "evidence_type": "skill",
    },
]

DEMO_REQUIREMENTS = [
    {
        "name": "Backend programming",
        "category": "technical",
        "importance": "required",
        "raw_text": "Experience with Python or another backend language.",
    },
    {
        "name": "SQL databases",
        "category": "technical",
        "importance": "required",
        "raw_text": "Experience with SQL databases.",
    },
    {
        "name": "REST APIs",
        "category": "technical",
        "importance": "required",
        "raw_text": "Experience building or using REST APIs.",
    },
    {
        "name": "Automated tests",
        "category": "technical",
        "importance": "preferred",
        "raw_text": "Experience with automated tests.",
    },
    {
        "name": "Docker",
        "category": "technical",
        "importance": "nice_to_have",
        "raw_text": "Experience with Docker is a plus.",
    },
    {
        "name": "Communication",
        "category": "non_technical",
        "importance": "required",
        "raw_text": (
            "Clear communication and collaboration with product, design and engineering teams."
        ),
    },
    {
        "name": "Brazil full-time internship availability",
        "category": "non_technical",
        "importance": "required",
        "raw_text": "Availability for a full-time internship program in Brazil.",
    },
]


def seed_demo_workspace(db: Session) -> dict[str, bool | int]:
    user = get_or_create_demo_user(db)
    resume_created = _ensure_demo_resume(db, user_id=user.id)
    job_created = _ensure_demo_job(db, user_id=user.id)
    db.flush()

    return {
        "resume_created": resume_created,
        "job_created": job_created,
        "resume_evidence": len(DEMO_EVIDENCE),
        "job_requirements": len(DEMO_REQUIREMENTS),
    }


def _ensure_demo_resume(db: Session, *, user_id: int) -> bool:
    resume = db.scalar(
        select(Resume)
        .where(Resume.user_id == user_id)
        .where(Resume.filename == DEMO_RESUME_FILENAME)
        .limit(1)
    )
    if resume is not None:
        return False

    resume = Resume(
        user_id=user_id,
        filename=DEMO_RESUME_FILENAME,
        raw_text=DEMO_RESUME_TEXT,
        parsed_json={},
    )
    db.add(resume)
    db.flush()
    db.add_all(
        [
            ResumeEvidence(
                resume_id=resume.id,
                skill=item["skill"],
                evidence_text=item["evidence_text"],
                source=item["source"],
                evidence_type=item["evidence_type"],
            )
            for item in DEMO_EVIDENCE
        ]
    )
    return True


def _ensure_demo_job(db: Session, *, user_id: int) -> bool:
    job = db.scalar(
        select(Job)
        .where(Job.user_id == user_id)
        .where(Job.title == DEMO_JOB_TITLE)
        .where(Job.company == DEMO_JOB_COMPANY)
        .limit(1)
    )
    if job is not None:
        return False

    job = Job(
        user_id=user_id,
        url=None,
        title=DEMO_JOB_TITLE,
        company=DEMO_JOB_COMPANY,
        location="Brazil",
        raw_description=DEMO_JOB_DESCRIPTION,
        clean_description=DEMO_JOB_DESCRIPTION,
        source_type="demo",
        scrape_status="demo_seeded",
    )
    db.add(job)
    db.flush()
    db.add_all(
        [
            JobRequirement(
                job_id=job.id,
                name=item["name"],
                category=item["category"],
                importance=item["importance"],
                raw_text=item["raw_text"],
            )
            for item in DEMO_REQUIREMENTS
        ]
    )
    return True
