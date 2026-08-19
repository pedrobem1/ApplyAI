from datetime import datetime

from pydantic import BaseModel


class AiRunResponse(BaseModel):
    id: int
    user_id: int | None
    task_type: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    estimated_cost: str | None
    latency_ms: int | None
    success: str
    error_message: str | None
    created_at: datetime

