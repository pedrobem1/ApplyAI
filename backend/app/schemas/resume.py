from pydantic import BaseModel, Field

from app.schemas.ai import ExtractedResumeEvidence


class ResumeUploadResponse(BaseModel):
    resume_id: int
    filename: str
    character_count: int
    preview: str


class ResumeEvidenceResponse(BaseModel):
    id: int
    skill: str
    evidence_text: str
    source: str | None
    evidence_type: str


class AdditionalResumeEvidenceRequest(BaseModel):
    skill: str = Field(min_length=1, max_length=160)
    evidence_text: str = Field(min_length=1)


class ResumeExtractionResponse(BaseModel):
    resume_id: int
    filename: str
    evidence: list[ResumeEvidenceResponse]


class StatelessResumeExtractionRequest(BaseModel):
    filename: str
    character_count: int
    preview: str


class StatelessResumeExtractionResponse(BaseModel):
    filename: str
    evidence: list[ExtractedResumeEvidence]


class CurrentResumeResponse(BaseModel):
    resume_id: int
    filename: str
    character_count: int
    preview: str
