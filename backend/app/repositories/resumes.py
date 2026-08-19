from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.db.models import RequirementMatch, Resume, ResumeEvidence
from app.schemas.ai import ExtractedResume


def create_resume(
    db: Session,
    *,
    user_id: int,
    filename: str,
    raw_text: str,
) -> Resume:
    resume = Resume(
        user_id=user_id,
        filename=filename,
        raw_text=raw_text,
        parsed_json={},
    )
    db.add(resume)
    db.flush()
    return resume


def get_resume(db: Session, resume_id: int) -> Resume | None:
    return db.get(Resume, resume_id)


def get_latest_resume(db: Session, *, user_id: int) -> Resume | None:
    return db.scalar(
        select(Resume)
        .where(Resume.user_id == user_id)
        .order_by(Resume.created_at.desc(), Resume.id.desc())
        .limit(1)
    )


def delete_resume_for_user(db: Session, *, resume_id: int, user_id: int) -> bool:
    resume = db.scalar(
        select(Resume).where(Resume.id == resume_id).where(Resume.user_id == user_id)
    )
    if resume is None:
        return False

    db.execute(delete(RequirementMatch).where(RequirementMatch.resume_id == resume.id))
    db.execute(delete(ResumeEvidence).where(ResumeEvidence.resume_id == resume.id))
    db.delete(resume)
    return True


def list_resume_evidence(db: Session, *, resume_id: int) -> list[ResumeEvidence]:
    return list(
        db.scalars(
            select(ResumeEvidence)
            .where(ResumeEvidence.resume_id == resume_id)
            .order_by(ResumeEvidence.id)
        )
    )


def add_resume_evidence(
    db: Session,
    *,
    resume: Resume,
    skill: str,
    evidence_text: str,
    source: str = "manual",
    evidence_type: str = "manual_context",
) -> ResumeEvidence:
    evidence = ResumeEvidence(
        resume_id=resume.id,
        skill=skill,
        evidence_text=evidence_text,
        source=source,
        evidence_type=evidence_type,
    )
    db.add(evidence)
    db.flush()
    return evidence


def delete_resume_evidence(
    db: Session,
    *,
    resume_id: int,
    evidence_id: int,
    user_id: int,
) -> bool:
    resume = db.scalar(
        select(Resume).where(Resume.id == resume_id).where(Resume.user_id == user_id)
    )
    if resume is None:
        return False

    evidence = db.scalar(
        select(ResumeEvidence)
        .where(ResumeEvidence.id == evidence_id)
        .where(ResumeEvidence.resume_id == resume.id)
    )
    if evidence is None:
        return False

    db.execute(delete(RequirementMatch).where(RequirementMatch.resume_id == resume.id))
    db.delete(evidence)
    return True


def replace_resume_evidence(
    db: Session,
    *,
    resume: Resume,
    extracted: ExtractedResume,
) -> list[ResumeEvidence]:
    db.execute(
        delete(ResumeEvidence)
        .where(ResumeEvidence.resume_id == resume.id)
        .where(or_(ResumeEvidence.source.is_(None), ResumeEvidence.source != "manual"))
    )

    evidence_rows = [
        ResumeEvidence(
            resume_id=resume.id,
            skill=item.skill,
            evidence_text=item.evidence_text,
            source=item.source,
            evidence_type=item.evidence_type,
        )
        for item in extracted.evidence
    ]
    db.add_all(evidence_rows)
    resume.parsed_json = extracted.model_dump()
    db.flush()
    return evidence_rows
