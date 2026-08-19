from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models import Job, JobRequirement, ResumeEvidence
from app.repositories.ai_runs import create_ai_run_from_metrics
from app.repositories.matches import (
    create_requirement_match,
    find_latest_resume_for_job,
    find_similar_resume_evidence,
    list_evidence_for_resume,
    list_requirements_for_job,
    replace_matches_for_job,
)
from app.schemas.analysis import AnalysisMatchResponse, AnalysisResponse, RetrievedEvidenceResponse
from app.services.ai_client import AiConfigurationError, StructuredOutputError
from app.services.embedding_service import embed_job_requirements, embed_resume_evidence
from app.services.extraction_service import verify_requirement_match_with_metrics
from app.services.scoring_service import calculate_match_score


class AnalysisError(RuntimeError):
    pass


@dataclass(frozen=True)
class AnalysisRunStats:
    embedded_resume_evidence: int
    embedded_job_requirements: int


def analyze_job_against_latest_resume(db: Session, *, job: Job) -> AnalysisResponse:
    resume = find_latest_resume_for_job(db, job=job)
    if resume is None:
        raise AnalysisError("No resume found. Upload and extract a resume before analysis.")

    requirements = list_requirements_for_job(db, job_id=job.id)
    if not requirements:
        raise AnalysisError("No job requirements found. Extract requirements before analysis.")

    evidence = list_evidence_for_resume(db, resume_id=resume.id)
    if not evidence:
        raise AnalysisError("No resume evidence found. Extract resume evidence before analysis.")

    stats = AnalysisRunStats(
        embedded_resume_evidence=embed_resume_evidence(db, evidence, user_id=job.user_id),
        embedded_job_requirements=embed_job_requirements(db, requirements, user_id=job.user_id),
    )

    replace_matches_for_job(db, job_id=job.id)

    responses: list[AnalysisMatchResponse] = []
    for requirement in requirements:
        if requirement.embedding is None:
            raise AnalysisError(f"Requirement {requirement.id} has no embedding.")

        retrieved = find_similar_resume_evidence(
            db,
            resume_id=resume.id,
            embedding=requirement.embedding,
            limit=3,
        )
        verification, metrics = _verify_requirement(requirement, retrieved)
        create_ai_run_from_metrics(
            db,
            task_type="requirement_match_verification",
            user_id=job.user_id,
            metrics=metrics,
        )
        saved_match = create_requirement_match(
            db,
            requirement_id=requirement.id,
            resume_id=resume.id,
            verification=verification,
        )

        responses.append(
            AnalysisMatchResponse(
                requirement_id=requirement.id,
                requirement_name=requirement.name,
                category=requirement.category,
                importance=requirement.importance,
                classification=saved_match.classification,
                confidence=saved_match.confidence,
                explanation=saved_match.explanation,
                gap_type=saved_match.gap_type,
                evidence=[
                    RetrievedEvidenceResponse(
                        evidence_id=item.id,
                        skill=item.skill,
                        evidence_text=item.evidence_text,
                        source=item.source,
                        distance=round(distance, 6),
                    )
                    for item, distance in retrieved
                ],
            )
        )

    score = calculate_match_score(
        [
            {"classification": item.classification, "importance": item.importance}
            for item in responses
        ]
    )

    return AnalysisResponse(
        job_id=job.id,
        resume_id=resume.id,
        score=score,
        embedded_resume_evidence=stats.embedded_resume_evidence,
        embedded_job_requirements=stats.embedded_job_requirements,
        matches=responses,
    )


def _verify_requirement(
    requirement: JobRequirement,
    retrieved: list[tuple[ResumeEvidence, float]],
):
    evidence_payload = [
        {
            "id": item.id,
            "skill": item.skill,
            "evidence_text": item.evidence_text,
            "source": item.source or "unknown",
            "semantic_distance": round(distance, 6),
        }
        for item, distance in retrieved
    ]

    try:
        return verify_requirement_match_with_metrics(
            requirement_name=requirement.name,
            requirement_raw_text=requirement.raw_text,
            evidence=evidence_payload,
        )
    except AiConfigurationError:
        raise
    except StructuredOutputError:
        raise
