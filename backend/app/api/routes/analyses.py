from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.jobs import get_job
from app.repositories.matches import get_resume_evidence_by_ids, list_matches_for_job
from app.schemas.analysis import (
    AnalysisMatchResponse,
    AnalysisResponse,
    RetrievedEvidenceResponse,
)
from app.services.ai_client import AiConfigurationError, StructuredOutputError
from app.services.analysis_service import AnalysisError, analyze_job_against_latest_resume
from app.services.scoring_service import calculate_match_score

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/jobs/{job_id:int}/analyze", response_model=AnalysisResponse)
def analyze_job(job_id: int, db: DbSession) -> AnalysisResponse:
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    try:
        analysis = analyze_job_against_latest_resume(db, job=job)
    except AnalysisError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AiConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except StructuredOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    db.commit()
    return analysis


@router.get("/jobs/{job_id:int}/analysis", response_model=AnalysisResponse)
def get_job_analysis(job_id: int, db: DbSession) -> AnalysisResponse:
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    rows = list_matches_for_job(db, job_id=job.id)
    if not rows:
        raise HTTPException(status_code=404, detail="No analysis found for this job.")

    evidence_ids = [
        evidence_id
        for _requirement, match in rows
        for evidence_id in match.matched_evidence_ids
    ]
    evidence_by_id = get_resume_evidence_by_ids(db, evidence_ids=evidence_ids)
    resume_ids = {match.resume_id for _requirement, match in rows if match.resume_id is not None}
    resume_id = resume_ids.pop() if len(resume_ids) == 1 else 0

    matches = [
        AnalysisMatchResponse(
            requirement_id=requirement.id,
            requirement_name=requirement.name,
            category=requirement.category,
            importance=requirement.importance,
            classification=match.classification,
            confidence=match.confidence,
            explanation=match.explanation,
            gap_type=match.gap_type,
            evidence=[
                RetrievedEvidenceResponse(
                    evidence_id=evidence.id,
                    skill=evidence.skill,
                    evidence_text=evidence.evidence_text,
                    source=evidence.source,
                    distance=0.0,
                )
                for evidence_id in match.matched_evidence_ids
                if (evidence := evidence_by_id.get(evidence_id)) is not None
            ],
        )
        for requirement, match in rows
    ]
    score = calculate_match_score(
        [
            {"classification": item.classification, "importance": item.importance}
            for item in matches
        ]
    )

    return AnalysisResponse(
        job_id=job.id,
        resume_id=resume_id,
        score=score,
        embedded_resume_evidence=0,
        embedded_job_requirements=0,
        matches=matches,
    )
