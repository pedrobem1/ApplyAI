from pydantic import BaseModel, HttpUrl

from app.schemas.ai import ExtractedJobRequirement


class ImportJobUrlRequest(BaseModel):
    url: HttpUrl


class ManualJobRequest(BaseModel):
    title: str | None = None
    company: str | None = None
    description: str


class JobImportResponse(BaseModel):
    job_id: int
    source_type: str
    url: str | None = None
    title: str | None = None
    company: str | None = None
    scrape_status: str | None = None
    character_count: int
    preview: str


class JobPreviewResponse(BaseModel):
    source_type: str
    url: str | None = None
    title: str | None = None
    company: str | None = None
    scrape_status: str | None = None
    character_count: int
    preview: str
    description: str


class JobListItem(BaseModel):
    job_id: int
    source_type: str
    url: str | None = None
    title: str | None = None
    company: str | None = None
    location: str | None = None
    scrape_status: str | None = None
    character_count: int
    preview: str


class JobRequirementResponse(BaseModel):
    id: int
    name: str
    category: str
    importance: str
    raw_text: str


class JobRequirementExtractionResponse(BaseModel):
    job_id: int | None = None
    role: str | None = None
    company: str | None = None
    location: str | None = None
    requirements: list[ExtractedJobRequirement] | list[JobRequirementResponse]
