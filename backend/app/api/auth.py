from hmac import compare_digest

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from app.core.config import settings

ACCESS_TOKEN_HEADER = "x-applyai-access-token"
PUBLIC_PATHS = {"/health", "/auth/status", "/auth/login"}


class SharedAccessTokenMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        if _is_public_request(request):
            return await call_next(request)

        expected_token = settings.app_access_token
        if not expected_token:
            return await call_next(request)

        provided_token = request.headers.get(ACCESS_TOKEN_HEADER, "")
        if not compare_digest(provided_token, expected_token):
            return JSONResponse(
                {"detail": "Invalid access token."},
                status_code=401,
            )

        return await call_next(request)


def _is_public_request(request: Request) -> bool:
    return request.method == "OPTIONS" or request.url.path in PUBLIC_PATHS
