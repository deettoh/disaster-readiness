"""Environment and runtime settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Hyperlocal Disaster Readiness API"
    app_env: Literal["local", "dev", "staging", "prod"] = "local"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"

    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    redis_url: str = "redis://localhost:6379/0"
    queue_backend: Literal["mock", "rq"] = "mock"
    queue_name: str = "image-processing"
    queue_default_timeout: int = 300
    queue_retry_max: int = 3
    queue_retry_intervals: list[int] = Field(default_factory=lambda: [1, 3, 5])
    queue_enqueue_max_attempts: int = 3
    queue_enqueue_backoff_seconds: list[float] = Field(
        default_factory=lambda: [0.0, 0.0, 0.0]
    )
    upload_allowed_content_types: list[str] = Field(
        default_factory=lambda: ["image/jpeg", "image/png", "image/webp"]
    )
    upload_max_size_bytes: int = 10 * 1024 * 1024
    rate_limit_reports_per_minute: int = 20
    rate_limit_report_images_per_minute: int = 30
    supabase_url: str | None = None
    supabase_publishable_key: str | None = None
    supabase_secret_key: str | None = None
    database_url: str
    data_backend: Literal["mock", "sql"] = "mock"
    routing_backend: Literal["mock", "sql"] = "mock"
    routing_algorithm: Literal["dijkstra", "astar"] = "dijkstra"
    weather_backend: Literal["mock", "live"] = "mock"
    readiness_alert_threshold: float = 40.0
    road_penalty_radius_m: float = 500.0
    road_penalty_weight: float = 50.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings loaded from environment."""
    return Settings()
