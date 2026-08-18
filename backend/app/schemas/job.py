from pydantic import BaseModel, HttpUrl

from app.schemas.ai import ExtractedJobRequirement


class ImportJobUrlRequest(BaseModel):
    url: HttpUrl


class ManualJobRequest(BaseModel):
    title: str | None = None
    company: str | None = None
    description: str


class JobImportResponse(BaseModel):
    source_type: str
    url: str | None = None
    title: str | None = None
    company: str | None = None
    scrape_status: str | None = None
    character_count: int
    preview: str


class JobRequirementExtractionResponse(BaseModel):
    role: str | None = None
    company: str | None = None
    location: str | None = None
    requirements: list[ExtractedJobRequirement]

