from datetime import UTC, datetime
from enum import StrEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RequirementImportance(StrEnum):
    REQUIRED = "required"
    PREFERRED = "preferred"
    NICE_TO_HAVE = "nice_to_have"
    UNKNOWN = "unknown"


class MatchClassification(StrEnum):
    MATCH = "MATCH"
    PARTIAL = "PARTIAL"
    NO_MATCH = "NO_MATCH"


class GapType(StrEnum):
    NONE = "NONE"
    SKILL_GAP = "SKILL_GAP"
    EVIDENCE_GAP = "EVIDENCE_GAP"
    UNKNOWN = "UNKNOWN"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)


class Resume(TimestampMixin, Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    evidence: Mapped[list["ResumeEvidence"]] = relationship(back_populates="resume")


class ResumeEvidence(TimestampMixin, Base):
    __tablename__ = "resume_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"), nullable=False)
    skill: Mapped[str] = mapped_column(String(160), nullable=False)
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(255))
    evidence_type: Mapped[str] = mapped_column(String(80), nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))

    resume: Mapped[Resume] = relationship(back_populates="evidence")


class Job(TimestampMixin, Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(String(255))
    company: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    raw_description: Mapped[str] = mapped_column(Text, nullable=False)
    clean_description: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    scrape_status: Mapped[str | None] = mapped_column(String(80))

    requirements: Mapped[list["JobRequirement"]] = relationship(back_populates="job")


class JobRequirement(TimestampMixin, Base):
    __tablename__ = "job_requirements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    importance: Mapped[str] = mapped_column(String(40), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))

    job: Mapped[Job] = relationship(back_populates="requirements")


class RequirementMatch(TimestampMixin, Base):
    __tablename__ = "requirement_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requirement_id: Mapped[int] = mapped_column(ForeignKey("job_requirements.id"), nullable=False)
    resume_id: Mapped[int | None] = mapped_column(ForeignKey("resumes.id"))
    classification: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    matched_evidence_ids: Mapped[list[int]] = mapped_column(JSONB, default=list, nullable=False)
    gap_type: Mapped[str] = mapped_column(String(40), nullable=False)


class UserSkill(TimestampMixin, Base):
    __tablename__ = "user_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    skill: Mapped[str] = mapped_column(String(160), nullable=False)
    level: Mapped[str] = mapped_column(String(40), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)


class AiRun(TimestampMixin, Base):
    __tablename__ = "ai_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    task_type: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    estimated_cost: Mapped[str | None] = mapped_column(String(40))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    success: Mapped[str] = mapped_column(String(10), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
