from app.core.config import Settings


def test_database_url_normalizes_postgres_scheme():
    settings = Settings(DATABASE_URL="postgres://user:pass@example.com:5432/app")

    assert settings.database_url == "postgresql+psycopg://user:pass@example.com:5432/app"


def test_database_url_normalizes_postgresql_scheme():
    settings = Settings(DATABASE_URL="postgresql://user:pass@example.com:5432/app")

    assert settings.database_url == "postgresql+psycopg://user:pass@example.com:5432/app"


def test_database_url_keeps_explicit_psycopg_scheme():
    settings = Settings(DATABASE_URL="postgresql+psycopg://user:pass@example.com:5432/app")

    assert settings.database_url == "postgresql+psycopg://user:pass@example.com:5432/app"


def test_backend_cors_origins_strip_whitespace_and_trailing_slashes():
    settings = Settings(
        BACKEND_CORS_ORIGINS=" https://apply-ai-navy.vercel.app/, http://localhost:3000/ "
    )

    assert settings.backend_cors_origins == [
        "https://apply-ai-navy.vercel.app",
        "http://localhost:3000",
    ]
