from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import Job, JobRequirement, RequirementMatch, Resume, ResumeEvidence
from app.schemas.ai import RequirementVerification


def list_requirements_for_job(db: Session, *, job_id: int) -> list[JobRequirement]:
    return list(
        db.scalars(
            select(JobRequirement)
            .where(JobRequirement.job_id == job_id)
            .order_by(JobRequirement.id)
        )
    )


def list_evidence_for_resume(db: Session, *, resume_id: int) -> list[ResumeEvidence]:
    return list(
        db.scalars(
            select(ResumeEvidence)
            .where(ResumeEvidence.resume_id == resume_id)
            .order_by(ResumeEvidence.id)
        )
    )


def find_latest_resume_for_job(db: Session, *, job: Job) -> Resume | None:
    return db.scalar(
        select(Resume)
        .where(Resume.user_id == job.user_id)
        .order_by(Resume.created_at.desc(), Resume.id.desc())
        .limit(1)
    )


def find_similar_resume_evidence(
    db: Session,
    *,
    resume_id: int,
    embedding: list[float],
    limit: int = 3,
) -> list[tuple[ResumeEvidence, float]]:
    distance = ResumeEvidence.embedding.cosine_distance(embedding).label("distance")
    rows = db.execute(
        select(ResumeEvidence, distance)
        .where(ResumeEvidence.resume_id == resume_id)
        .where(ResumeEvidence.embedding.is_not(None))
        .order_by(distance)
        .limit(limit)
    ).all()
    return [(row[0], float(row[1])) for row in rows]


def replace_matches_for_job(db: Session, *, job_id: int) -> None:
    requirement_ids = select(JobRequirement.id).where(JobRequirement.job_id == job_id)
    db.execute(delete(RequirementMatch).where(RequirementMatch.requirement_id.in_(requirement_ids)))


def create_requirement_match(
    db: Session,
    *,
    requirement_id: int,
    resume_id: int,
    verification: RequirementVerification,
) -> RequirementMatch:
    match = RequirementMatch(
        requirement_id=requirement_id,
        resume_id=resume_id,
        classification=verification.classification,
        confidence=verification.confidence,
        explanation=verification.explanation,
        matched_evidence_ids=verification.matched_evidence_ids,
        gap_type=verification.gap_type,
    )
    db.add(match)
    db.flush()
    return match


def get_resume_evidence_by_ids(
    db: Session,
    *,
    evidence_ids: list[int],
) -> dict[int, ResumeEvidence]:
    if not evidence_ids:
        return {}

    rows = db.scalars(select(ResumeEvidence).where(ResumeEvidence.id.in_(evidence_ids)))
    return {row.id: row for row in rows}


def list_matches_for_job(
    db: Session,
    *,
    job_id: int,
) -> list[tuple[JobRequirement, RequirementMatch]]:
    return list(
        db.execute(
            select(JobRequirement, RequirementMatch)
            .join(RequirementMatch, RequirementMatch.requirement_id == JobRequirement.id)
            .where(JobRequirement.job_id == job_id)
            .order_by(JobRequirement.id)
        ).all()
    )
