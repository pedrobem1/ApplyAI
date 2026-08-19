from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.repositories.ai_runs import create_ai_run_from_metrics
from app.repositories.resumes import (
    add_resume_evidence,
    create_resume,
    delete_resume_evidence,
    delete_resume_for_user,
    get_latest_resume,
    get_resume,
    list_resume_evidence,
    replace_resume_evidence,
)
from app.repositories.users import get_or_create_demo_user
from app.schemas.resume import (
    AdditionalResumeEvidenceRequest,
    CurrentResumeResponse,
    ResumeEvidenceResponse,
    ResumeExtractionResponse,
    ResumeUploadResponse,
    StatelessResumeExtractionRequest,
    StatelessResumeExtractionResponse,
)
from app.services.ai_client import AiConfigurationError, StructuredOutputError
from app.services.extraction_service import (
    extract_resume_evidence,
    extract_resume_evidence_with_metrics,
)
from app.services.pdf_parser import PdfParsingError, extract_pdf_text
from app.services.text_service import limit_text

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: Annotated[UploadFile, File()],
    db: DbSession,
) -> ResumeUploadResponse:
    filename = file.filename or "resume.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    path = upload_dir / f"{uuid4()}-{filename}"
    contents = await file.read()
    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="PDF is larger than the upload limit.")

    path.write_bytes(contents)

    try:
        raw_text = extract_pdf_text(path)
    except PdfParsingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        if settings.delete_uploaded_pdf_after_parse:
            path.unlink(missing_ok=True)

    user = get_or_create_demo_user(db)
    resume = create_resume(db, user_id=user.id, filename=filename, raw_text=raw_text)
    db.commit()

    return ResumeUploadResponse(
        resume_id=resume.id,
        filename=filename,
        character_count=len(raw_text),
        preview=limit_text(raw_text, 600),
    )


@router.post("/extract", response_model=StatelessResumeExtractionResponse)
def extract_resume(
    payload: StatelessResumeExtractionRequest,
) -> StatelessResumeExtractionResponse:
    try:
        extracted = extract_resume_evidence(payload.preview)
    except AiConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except StructuredOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return StatelessResumeExtractionResponse(filename=payload.filename, evidence=extracted.evidence)


@router.post("/{resume_id:int}/extract", response_model=ResumeExtractionResponse)
def extract_persisted_resume(
    resume_id: int,
    db: DbSession,
) -> ResumeExtractionResponse:
    resume = get_resume(db, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found.")

    try:
        extracted, metrics = extract_resume_evidence_with_metrics(resume.raw_text)
    except AiConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except StructuredOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    create_ai_run_from_metrics(
        db,
        task_type="resume_evidence_extraction",
        user_id=resume.user_id,
        metrics=metrics,
    )
    replace_resume_evidence(db, resume=resume, extracted=extracted)
    evidence_rows = list_resume_evidence(db, resume_id=resume.id)
    db.commit()

    return ResumeExtractionResponse(
        resume_id=resume.id,
        filename=resume.filename,
        evidence=[_evidence_response(item) for item in evidence_rows],
    )


@router.get("/{resume_id:int}/evidence", response_model=ResumeExtractionResponse)
def get_resume_evidence(resume_id: int, db: DbSession) -> ResumeExtractionResponse:
    user = get_or_create_demo_user(db)
    resume = get_resume(db, resume_id)
    if resume is None or resume.user_id != user.id:
        raise HTTPException(status_code=404, detail="Resume not found.")

    evidence_rows = list_resume_evidence(db, resume_id=resume.id)
    db.commit()

    return ResumeExtractionResponse(
        resume_id=resume.id,
        filename=resume.filename,
        evidence=[_evidence_response(item) for item in evidence_rows],
    )


@router.post("/{resume_id:int}/evidence", response_model=ResumeEvidenceResponse)
def add_manual_resume_evidence(
    resume_id: int,
    payload: AdditionalResumeEvidenceRequest,
    db: DbSession,
) -> ResumeEvidenceResponse:
    user = get_or_create_demo_user(db)
    resume = get_resume(db, resume_id)
    if resume is None or resume.user_id != user.id:
        raise HTTPException(status_code=404, detail="Resume not found.")

    skill = payload.skill.strip()
    evidence_text = payload.evidence_text.strip()
    if not skill or not evidence_text:
        raise HTTPException(status_code=422, detail="Skill and evidence text are required.")

    evidence = add_resume_evidence(
        db,
        resume=resume,
        skill=skill,
        evidence_text=evidence_text,
    )
    db.commit()

    return _evidence_response(evidence)


@router.delete("/{resume_id:int}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(resume_id: int, db: DbSession) -> Response:
    user = get_or_create_demo_user(db)
    deleted = delete_resume_for_user(db, resume_id=resume_id, user_id=user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resume not found.")

    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{resume_id:int}/evidence/{evidence_id:int}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_manual_resume_evidence(
    resume_id: int,
    evidence_id: int,
    db: DbSession,
) -> Response:
    user = get_or_create_demo_user(db)
    deleted = delete_resume_evidence(
        db,
        resume_id=resume_id,
        evidence_id=evidence_id,
        user_id=user.id,
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Resume evidence not found.")

    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/current")
def get_current_resume(db: DbSession) -> CurrentResumeResponse:
    user = get_or_create_demo_user(db)
    resume = get_latest_resume(db, user_id=user.id)
    db.commit()

    if resume is None:
        raise HTTPException(status_code=404, detail="No resume uploaded yet.")

    return CurrentResumeResponse(
        resume_id=resume.id,
        filename=resume.filename,
        character_count=len(resume.raw_text),
        preview=limit_text(resume.raw_text, 600),
    )


def _evidence_response(item) -> ResumeEvidenceResponse:
    return ResumeEvidenceResponse(
        id=item.id,
        skill=item.skill,
        evidence_text=item.evidence_text,
        source=item.source,
        evidence_type=item.evidence_type,
    )
