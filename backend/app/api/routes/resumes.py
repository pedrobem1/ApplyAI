from fastapi import APIRouter, File, UploadFile

router = APIRouter()


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)) -> dict[str, str]:
    return {
        "filename": file.filename or "resume.pdf",
        "status": "stub",
        "message": "Resume upload endpoint is ready for the parsing pipeline.",
    }


@router.get("/current")
def get_current_resume() -> dict[str, str]:
    return {"status": "stub", "message": "Current resume endpoint is ready."}

