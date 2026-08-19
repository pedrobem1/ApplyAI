from pydantic import BaseModel


class RetrievedEvidenceResponse(BaseModel):
    evidence_id: int
    skill: str
    evidence_text: str
    source: str | None
    distance: float


class AnalysisMatchResponse(BaseModel):
    requirement_id: int
    requirement_name: str
    category: str
    importance: str
    classification: str
    confidence: int
    explanation: str
    gap_type: str
    evidence: list[RetrievedEvidenceResponse]


class AnalysisResponse(BaseModel):
    job_id: int
    resume_id: int
    score: float
    embedded_resume_evidence: int
    embedded_job_requirements: int
    matches: list[AnalysisMatchResponse]

