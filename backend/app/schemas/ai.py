from pydantic import BaseModel, Field


class ExtractedResumeEvidence(BaseModel):
    skill: str
    evidence_text: str
    source: str | None = None
    evidence_type: str


class ExtractedResume(BaseModel):
    evidence: list[ExtractedResumeEvidence] = Field(default_factory=list)


class ExtractedJobRequirement(BaseModel):
    name: str
    category: str
    importance: str
    raw_text: str


class ExtractedJob(BaseModel):
    role: str | None = None
    company: str | None = None
    location: str | None = None
    requirements: list[ExtractedJobRequirement] = Field(default_factory=list)


class RequirementVerification(BaseModel):
    classification: str
    confidence: int = Field(ge=0, le=100)
    explanation: str
    matched_evidence_ids: list[int] = Field(default_factory=list)
    gap_type: str

