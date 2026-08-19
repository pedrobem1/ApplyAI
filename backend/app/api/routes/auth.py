from hmac import compare_digest
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.services.demo_seed_service import seed_demo_workspace

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


class AuthStatusResponse(BaseModel):
    access_required: bool
    demo_login_enabled: bool
    demo_username: str | None = None


class AuthLoginRequest(BaseModel):
    username: str
    password: str


class AuthLoginResponse(BaseModel):
    access_token: str
    demo_seeded: bool


@router.get("/auth/status", response_model=AuthStatusResponse)
def get_auth_status() -> AuthStatusResponse:
    demo_login_enabled = bool(settings.demo_login_username and settings.demo_login_password)
    return AuthStatusResponse(
        access_required=bool(settings.app_access_token),
        demo_login_enabled=demo_login_enabled,
        demo_username=settings.demo_login_username if demo_login_enabled else None,
    )


@router.post("/auth/login", response_model=AuthLoginResponse)
def login(payload: AuthLoginRequest, db: DbSession) -> AuthLoginResponse:
    if not settings.app_access_token:
        raise HTTPException(status_code=503, detail="APP_ACCESS_TOKEN is not configured.")
    if not settings.demo_login_username or not settings.demo_login_password:
        raise HTTPException(status_code=404, detail="Demo login is not enabled.")

    username_matches = compare_digest(payload.username, settings.demo_login_username)
    password_matches = compare_digest(payload.password, settings.demo_login_password)
    if not username_matches or not password_matches:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    seed_demo_workspace(db)
    db.commit()
    return AuthLoginResponse(access_token=settings.app_access_token, demo_seeded=True)
