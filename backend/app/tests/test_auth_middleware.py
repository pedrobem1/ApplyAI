from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.auth import ACCESS_TOKEN_HEADER, SharedAccessTokenMiddleware
from app.core.config import settings


def create_test_client() -> TestClient:
    app = FastAPI()
    app.add_middleware(SharedAccessTokenMiddleware)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/private")
    def private():
        return {"status": "private"}

    return TestClient(app)


def test_shared_access_token_blocks_private_routes(monkeypatch):
    monkeypatch.setattr(settings, "app_access_token", "secret")
    client = create_test_client()

    assert client.get("/health").status_code == 200
    assert client.get("/private").status_code == 401
    assert client.get("/private", headers={ACCESS_TOKEN_HEADER: "wrong"}).status_code == 401
    assert client.get("/private", headers={ACCESS_TOKEN_HEADER: "secret"}).status_code == 200


def test_shared_access_token_is_optional(monkeypatch):
    monkeypatch.setattr(settings, "app_access_token", "")
    client = create_test_client()

    assert client.get("/private").status_code == 200
