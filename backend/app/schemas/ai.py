from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RequirementCategory = Literal[
    "technical",
    "non_technical",
    "domain",
    "language",
    "education",
    "experience",
]
RequirementImportance = Literal["required", "preferred", "nice_to_have", "unknown"]
EvidenceType = Literal["experience", "project", "education", "skill", "certification"]
MatchClassification = Literal["MATCH", "PARTIAL", "NO_MATCH"]
GapType = Literal["NONE", "SKILL_GAP", "EVIDENCE_GAP", "UNKNOWN"]


class ExtractedResumeEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill: str
    evidence_text: str
    source: str | None
    evidence_type: EvidenceType


class ExtractedResume(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence: list[ExtractedResumeEvidence]


class ExtractedJobRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    category: RequirementCategory
    importance: RequirementImportance
    raw_text: str


class ExtractedJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: str | None
    company: str | None
    location: str | None
    requirements: list[ExtractedJobRequirement]


class RequirementVerification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classification: MatchClassification
    confidence: int = Field(ge=0, le=100)
    explanation: str
    matched_evidence_ids: list[int]
    gap_type: GapType
