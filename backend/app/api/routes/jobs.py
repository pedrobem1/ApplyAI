from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl

router = APIRouter()


class ImportJobUrlRequest(BaseModel):
    url: HttpUrl


class ManualJobRequest(BaseModel):
    title: str | None = None
    company: str | None = None
    description: str


@router.post("/import-url")
def import_job_from_url(payload: ImportJobUrlRequest) -> dict[str, str]:
    return {
        "url": str(payload.url),
        "status": "stub",
        "message": "Job URL import endpoint is ready for scraping.",
    }


@router.post("/manual")
def create_manual_job(payload: ManualJobRequest) -> dict[str, str | None]:
    return {
        "title": payload.title,
        "company": payload.company,
        "status": "stub",
        "message": "Manual job endpoint is ready for extraction.",
    }


@router.get("")
def list_jobs() -> list[dict[str, str]]:
    return []

