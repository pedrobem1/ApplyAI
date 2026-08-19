from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.ai_runs import create_ai_run_from_metrics
from app.repositories.jobs import (
    create_job,
    delete_job_for_user,
    get_job,
    list_jobs_for_user,
    replace_job_requirements,
)
from app.repositories.users import get_or_create_demo_user
from app.schemas.job import (
    ImportJobUrlRequest,
    JobImportResponse,
    JobListItem,
    JobPreviewResponse,
    JobRequirementExtractionResponse,
    JobRequirementResponse,
    ManualJobRequest,
)
from app.services.ai_client import AiConfigurationError, StructuredOutputError
from app.services.extraction_service import (
    extract_job_requirements,
    extract_job_requirements_with_metrics,
)
from app.services.job_scraper import JobScrapingError, scrape_job_url
from app.services.text_service import limit_text, normalize_whitespace

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/preview-url", response_model=JobPreviewResponse)
def preview_job_from_url(payload: ImportJobUrlRequest) -> JobPreviewResponse:
    try:
        scraped = scrape_job_url(str(payload.url))
    except JobScrapingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return JobPreviewResponse(
        source_type="url",
        url=str(payload.url),
        title=scraped.title,
        scrape_status=scraped.scrape_status,
        character_count=len(scraped.clean_text),
        preview=limit_text(scraped.clean_text, 1200),
        description=scraped.clean_text,
    )


@router.post("/import-url", response_model=JobImportResponse)
def import_job_from_url(
    payload: ImportJobUrlRequest,
    db: DbSession,
) -> JobImportResponse:
    try:
        scraped = scrape_job_url(str(payload.url))
    except JobScrapingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    user = get_or_create_demo_user(db)
    job = create_job(
        db,
        user_id=user.id,
        url=str(payload.url),
        title=scraped.title,
        raw_description=scraped.raw_text,
        clean_description=scraped.clean_text,
        source_type="url",
        scrape_status=scraped.scrape_status,
    )
    db.commit()

    return JobImportResponse(
        job_id=job.id,
        source_type="url",
        url=str(payload.url),
        title=scraped.title,
        scrape_status=scraped.scrape_status,
        character_count=len(scraped.clean_text),
        preview=limit_text(scraped.clean_text, 1200),
    )


@router.post("/manual", response_model=JobImportResponse)
def create_manual_job(
    payload: ManualJobRequest,
    db: DbSession,
) -> JobImportResponse:
    clean_description = normalize_whitespace(payload.description)
    user = get_or_create_demo_user(db)
    job = create_job(
        db,
        user_id=user.id,
        title=payload.title,
        company=payload.company,
        raw_description=payload.description,
        clean_description=clean_description,
        source_type="manual",
    )
    db.commit()

    return JobImportResponse(
        job_id=job.id,
        source_type="manual",
        title=payload.title,
        company=payload.company,
        character_count=len(clean_description),
        preview=limit_text(clean_description, 1200),
    )


@router.post("/extract-requirements", response_model=JobRequirementExtractionResponse)
def extract_requirements(payload: ManualJobRequest) -> JobRequirementExtractionResponse:
    clean_description = normalize_whitespace(payload.description)
    try:
        extracted = extract_job_requirements(clean_description)
    except AiConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except StructuredOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return JobRequirementExtractionResponse(
        job_id=None,
        role=extracted.role or payload.title,
        company=extracted.company or payload.company,
        location=extracted.location,
        requirements=extracted.requirements,
    )


@router.post("/{job_id:int}/extract-requirements", response_model=JobRequirementExtractionResponse)
def extract_persisted_requirements(
    job_id: int,
    db: DbSession,
) -> JobRequirementExtractionResponse:
    job = get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    try:
        extracted, metrics = extract_job_requirements_with_metrics(job.clean_description)
    except AiConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except StructuredOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    create_ai_run_from_metrics(
        db,
        task_type="job_requirement_extraction",
        user_id=job.user_id,
        metrics=metrics,
    )
    requirement_rows = replace_job_requirements(db, job=job, extracted=extracted)
    db.commit()

    return JobRequirementExtractionResponse(
        job_id=job.id,
        role=job.title,
        company=job.company,
        location=job.location,
        requirements=[
            JobRequirementResponse(
                id=item.id,
                name=item.name,
                category=item.category,
                importance=item.importance,
                raw_text=item.raw_text,
            )
            for item in requirement_rows
        ],
    )


@router.delete("/{job_id:int}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, db: DbSession) -> Response:
    user = get_or_create_demo_user(db)
    deleted = delete_job_for_user(db, job_id=job_id, user_id=user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found.")

    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("", response_model=list[JobListItem])
def list_jobs(db: DbSession) -> list[JobListItem]:
    user = get_or_create_demo_user(db)
    jobs = list_jobs_for_user(db, user_id=user.id)
    db.commit()

    return [
        JobListItem(
            job_id=job.id,
            source_type=job.source_type,
            url=job.url,
            title=job.title,
            company=job.company,
            location=job.location,
            scrape_status=job.scrape_status,
            character_count=len(job.clean_description),
            preview=limit_text(job.clean_description, 300),
        )
        for job in jobs
    ]
