from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import Job, JobRequirement, RequirementMatch
from app.schemas.ai import ExtractedJob


def create_job(
    db: Session,
    *,
    user_id: int,
    raw_description: str,
    clean_description: str,
    source_type: str,
    url: str | None = None,
    title: str | None = None,
    company: str | None = None,
    location: str | None = None,
    scrape_status: str | None = None,
) -> Job:
    job = Job(
        user_id=user_id,
        url=url,
        title=title,
        company=company,
        location=location,
        raw_description=raw_description,
        clean_description=clean_description,
        source_type=source_type,
        scrape_status=scrape_status,
    )
    db.add(job)
    db.flush()
    return job


def get_job(db: Session, job_id: int) -> Job | None:
    return db.get(Job, job_id)


def delete_job_for_user(db: Session, *, job_id: int, user_id: int) -> bool:
    job = db.scalar(select(Job).where(Job.id == job_id).where(Job.user_id == user_id))
    if job is None:
        return False

    requirement_ids = select(JobRequirement.id).where(JobRequirement.job_id == job.id)
    db.execute(delete(RequirementMatch).where(RequirementMatch.requirement_id.in_(requirement_ids)))
    db.execute(delete(JobRequirement).where(JobRequirement.job_id == job.id))
    db.delete(job)
    return True


def list_jobs_for_user(db: Session, *, user_id: int) -> list[Job]:
    return list(
        db.scalars(
            select(Job)
            .where(Job.user_id == user_id)
            .order_by(Job.created_at.desc(), Job.id.desc())
        )
    )


def replace_job_requirements(
    db: Session,
    *,
    job: Job,
    extracted: ExtractedJob,
) -> list[JobRequirement]:
    requirement_ids = select(JobRequirement.id).where(JobRequirement.job_id == job.id)
    db.execute(
        delete(RequirementMatch).where(RequirementMatch.requirement_id.in_(requirement_ids))
    )
    db.execute(delete(JobRequirement).where(JobRequirement.job_id == job.id))

    if extracted.role:
        job.title = extracted.role
    if extracted.company:
        job.company = extracted.company
    if extracted.location:
        job.location = extracted.location

    requirement_rows = [
        JobRequirement(
            job_id=job.id,
            name=item.name,
            category=item.category,
            importance=item.importance,
            raw_text=item.raw_text,
        )
        for item in extracted.requirements
    ]
    db.add_all(requirement_rows)
    db.flush()
    return requirement_rows
