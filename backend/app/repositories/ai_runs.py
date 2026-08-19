from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AiRun


def create_ai_run(
    db: Session,
    *,
    task_type: str,
    model: str,
    user_id: int | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    latency_ms: int | None = None,
    success: bool = True,
    error_message: str | None = None,
) -> AiRun:
    run = AiRun(
        user_id=user_id,
        task_type=task_type,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost=None,
        latency_ms=latency_ms,
        success="true" if success else "false",
        error_message=error_message,
    )
    db.add(run)
    db.flush()
    return run


def create_ai_run_from_metrics(
    db: Session,
    *,
    task_type: str,
    metrics: dict[str, Any],
    user_id: int | None = None,
) -> AiRun:
    return create_ai_run(
        db,
        task_type=task_type,
        user_id=user_id,
        model=str(metrics.get("model") or "unknown"),
        input_tokens=_optional_int(metrics.get("input_tokens")),
        output_tokens=_optional_int(metrics.get("output_tokens")),
        latency_ms=_optional_int(metrics.get("latency_ms")),
        success=bool(metrics.get("success", True)),
        error_message=_optional_str(metrics.get("error_message")),
    )


def list_recent_ai_runs(db: Session, *, limit: int = 50) -> list[AiRun]:
    return list(
        db.scalars(
            select(AiRun)
            .order_by(AiRun.created_at.desc(), AiRun.id.desc())
            .limit(limit)
        )
    )


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)

