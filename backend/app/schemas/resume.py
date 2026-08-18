from pydantic import BaseModel

from app.schemas.ai import ExtractedResumeEvidence


class ResumeUploadResponse(BaseModel):
    filename: str
    character_count: int
    preview: str


class ResumeExtractionResponse(BaseModel):
    filename: str
    evidence: list[ExtractedResumeEvidence]

