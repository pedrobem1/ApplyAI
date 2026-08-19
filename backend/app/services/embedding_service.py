from sqlalchemy.orm import Session

from app.db.models import JobRequirement, ResumeEvidence
from app.repositories.ai_runs import create_ai_run_from_metrics
from app.services.ai_client import generate_embedding_with_metrics


def embed_resume_evidence(
    db: Session,
    evidence: list[ResumeEvidence],
    *,
    user_id: int | None = None,
) -> int:
    updated = 0
    for item in evidence:
        if item.embedding is None:
            item.embedding, metrics = generate_embedding_with_metrics(_resume_evidence_text(item))
            create_ai_run_from_metrics(
                db,
                task_type="resume_evidence_embedding",
                user_id=user_id,
                metrics=metrics,
            )
            updated += 1
    db.flush()
    return updated


def embed_job_requirements(
    db: Session,
    requirements: list[JobRequirement],
    *,
    user_id: int | None = None,
) -> int:
    updated = 0
    for item in requirements:
        if item.embedding is None:
            item.embedding, metrics = generate_embedding_with_metrics(_job_requirement_text(item))
            create_ai_run_from_metrics(
                db,
                task_type="job_requirement_embedding",
                user_id=user_id,
                metrics=metrics,
            )
            updated += 1
    db.flush()
    return updated


def _resume_evidence_text(item: ResumeEvidence) -> str:
    return (
        f"Skill: {item.skill}\n"
        f"Evidence: {item.evidence_text}\n"
        f"Source: {item.source or 'unknown'}"
    )


def _job_requirement_text(item: JobRequirement) -> str:
    return (
        f"Requirement: {item.name}\n"
        f"Category: {item.category}\n"
        f"Importance: {item.importance}\n"
        f"Original text: {item.raw_text}"
    )
