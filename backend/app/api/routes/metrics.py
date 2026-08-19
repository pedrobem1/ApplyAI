from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.ai_runs import list_recent_ai_runs
from app.schemas.metrics import AiRunResponse

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/ai-runs", response_model=list[AiRunResponse])
def list_ai_runs(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[AiRunResponse]:
    return [
        AiRunResponse(
            id=run.id,
            user_id=run.user_id,
            task_type=run.task_type,
            model=run.model,
            input_tokens=run.input_tokens,
            output_tokens=run.output_tokens,
            estimated_cost=run.estimated_cost,
            latency_ms=run.latency_ms,
            success=run.success,
            error_message=run.error_message,
            created_at=run.created_at,
        )
        for run in list_recent_ai_runs(db, limit=limit)
    ]

