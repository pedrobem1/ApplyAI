from pathlib import Path

from app.services.text_service import normalize_whitespace


class PdfParsingError(RuntimeError):
    pass


def extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise PdfParsingError(
            "pypdf is not installed. Run backend dependency setup first."
        ) from exc

    try:
        reader = PdfReader(str(path))
        page_texts = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise PdfParsingError(f"Could not extract text from PDF: {exc}") from exc

    text = normalize_whitespace("\n".join(page_texts))
    if not text:
        raise PdfParsingError("The PDF did not contain extractable text.")

    return text
