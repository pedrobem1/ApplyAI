import json
import time

from pydantic import BaseModel

from app.core.config import settings


class AiConfigurationError(RuntimeError):
    pass


class StructuredOutputError(RuntimeError):
    pass


def _get_openai_client():
    if not settings.openai_api_key:
        raise AiConfigurationError("OPENAI_API_KEY is not configured.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise AiConfigurationError(
            "openai is not installed. Run backend dependency setup first."
        ) from exc

    return OpenAI(api_key=settings.openai_api_key)


def generate_structured_output[StructuredModel: BaseModel](
    *,
    schema: type[StructuredModel],
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
) -> tuple[StructuredModel, dict[str, int | str | bool | None]]:
    client = _get_openai_client()
    started_at = time.perf_counter()

    try:
        response = client.responses.create(
            model=model or settings.openai_extraction_model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema.__name__,
                    "schema": schema.model_json_schema(),
                    "strict": True,
                }
            },
        )
    except Exception as exc:
        raise StructuredOutputError(f"OpenAI structured output request failed: {exc}") from exc

    latency_ms = int((time.perf_counter() - started_at) * 1000)

    try:
        parsed = schema.model_validate(json.loads(response.output_text))
    except Exception as exc:
        raise StructuredOutputError(f"Could not validate structured output: {exc}") from exc

    usage = getattr(response, "usage", None)
    metrics = {
        "model": model or settings.openai_extraction_model,
        "input_tokens": getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
        "latency_ms": latency_ms,
        "success": True,
    }

    return parsed, metrics


def generate_embedding(text: str) -> list[float]:
    embedding, _metrics = generate_embedding_with_metrics(text)
    return embedding


def generate_embedding_with_metrics(
    text: str,
) -> tuple[list[float], dict[str, int | str | bool | None]]:
    client = _get_openai_client()
    started_at = time.perf_counter()
    response = client.embeddings.create(model=settings.openai_embedding_model, input=text)
    latency_ms = int((time.perf_counter() - started_at) * 1000)
    usage = getattr(response, "usage", None)

    metrics = {
        "model": settings.openai_embedding_model,
        "input_tokens": getattr(usage, "prompt_tokens", None)
        or getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
        "latency_ms": latency_ms,
        "success": True,
    }

    return response.data[0].embedding, metrics
