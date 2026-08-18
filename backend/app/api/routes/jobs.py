from fastapi import APIRouter, HTTPException

from app.schemas.job import (
    ImportJobUrlRequest,
    JobImportResponse,
    JobRequirementExtractionResponse,
    ManualJobRequest,
)
from app.services.ai_client import AiConfigurationError, StructuredOutputError
from app.services.extraction_service import extract_job_requirements
from app.services.job_scraper import JobScrapingError, scrape_job_url
from app.services.text_service import limit_text, normalize_whitespace

router = APIRouter()


@router.post("/import-url", response_model=JobImportResponse)
def import_job_from_url(payload: ImportJobUrlRequest) -> JobImportResponse:
    try:
        scraped = scrape_job_url(str(payload.url))
    except JobScrapingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return JobImportResponse(
        source_type="url",
        url=str(payload.url),
        title=scraped.title,
        scrape_status=scraped.scrape_status,
        character_count=len(scraped.clean_text),
        preview=limit_text(scraped.clean_text, 1200),
    )


@router.post("/manual", response_model=JobImportResponse)
def create_manual_job(payload: ManualJobRequest) -> JobImportResponse:
    clean_description = normalize_whitespace(payload.description)
    return JobImportResponse(
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
        role=extracted.role or payload.title,
        company=extracted.company or payload.company,
        location=extracted.location,
        requirements=extracted.requirements,
    )


@router.get("")
def list_jobs() -> list[dict[str, str]]:
    return []
