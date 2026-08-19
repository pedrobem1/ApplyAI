from functools import cached_property

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    database_url: str = Field(
        default="postgresql+psycopg://jobintel:jobintel@localhost:5432/jobintel",
        alias="DATABASE_URL",
    )
    backend_cors_origins_raw: str = Field(
        default="http://localhost:3000",
        alias="BACKEND_CORS_ORIGINS",
    )
    app_access_token: str = Field(default="", alias="APP_ACCESS_TOKEN")
    demo_login_username: str = Field(default="", alias="DEMO_LOGIN_USERNAME")
    demo_login_password: str = Field(default="", alias="DEMO_LOGIN_PASSWORD")
    upload_dir: str = Field(default="uploads", alias="UPLOAD_DIR")
    max_upload_bytes: int = Field(default=5_000_000, alias="MAX_UPLOAD_BYTES")
    delete_uploaded_pdf_after_parse: bool = Field(
        default=True,
        alias="DELETE_UPLOADED_PDF_AFTER_PARSE",
    )
    openai_extraction_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_EXTRACTION_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="OPENAI_EMBEDDING_MODEL",
    )

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @cached_property
    def backend_cors_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.backend_cors_origins_raw.split(",")
            if origin.strip()
        ]


settings = Settings()
