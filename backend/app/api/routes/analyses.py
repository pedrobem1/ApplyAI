from fastapi import APIRouter

router = APIRouter()


@router.post("/jobs/{job_id}/analyze")
def analyze_job(job_id: int) -> dict[str, int | str]:
    return {
        "job_id": job_id,
        "status": "stub",
        "message": "Analysis endpoint is ready for the matching pipeline.",
    }


@router.get("/jobs/{job_id}/analysis")
def get_job_analysis(job_id: int) -> dict[str, int | str]:
    return {"job_id": job_id, "status": "stub"}

