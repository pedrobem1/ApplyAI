from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.schemas.resume import ResumeExtractionResponse, ResumeUploadResponse
from app.services.ai_client import AiConfigurationError, StructuredOutputError
from app.services.extraction_service import extract_resume_evidence
from app.services.pdf_parser import PdfParsingError, extract_pdf_text
from app.services.text_service import limit_text

router = APIRouter()


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: Annotated[UploadFile, File()]) -> ResumeUploadResponse:
    filename = file.filename or "resume.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    path = upload_dir / f"{uuid4()}-{filename}"
    path.write_bytes(await file.read())

    try:
        raw_text = extract_pdf_text(path)
    except PdfParsingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return ResumeUploadResponse(
        filename=filename,
        character_count=len(raw_text),
        preview=limit_text(raw_text, 600),
    )


@router.post("/extract", response_model=ResumeExtractionResponse)
def extract_resume(payload: ResumeUploadResponse) -> ResumeExtractionResponse:
    try:
        extracted = extract_resume_evidence(payload.preview)
    except AiConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except StructuredOutputError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return ResumeExtractionResponse(filename=payload.filename, evidence=extracted.evidence)


@router.get("/current")
def get_current_resume() -> dict[str, str]:
    return {"status": "stub", "message": "Current resume endpoint is ready."}
