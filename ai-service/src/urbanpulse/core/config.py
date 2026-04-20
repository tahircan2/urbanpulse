"""
urbanpulse.core.config — Centralised Pydantic settings.

Reads .env from project root. All configuration flows through this module.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── OpenAI ────────────────────────────────────────────────────────────
    openai_api_key: str = "your_openai_api_key_here"

    # ── Agent models ──────────────────────────────────────────────────────
    classifier_model: str = "gpt-4o-mini"
    planner_model:    str = "gpt-4o-mini"
    monitor_model:    str = "gpt-4o-mini"

    # ── Spring Boot callback ──────────────────────────────────────────────
    spring_backend_url: str = "http://localhost:8080/api"
    internal_secret:    str = "urbanpulse-secret-2024"

    # ── Service ───────────────────────────────────────────────────────────
    service_host: str = "0.0.0.0"
    service_port: int = 8000
    environment:  str = "development"
    log_level:    str = "INFO"

    # ── Tool tuning ───────────────────────────────────────────────────────
    tool_max_rounds: int = 2

    # ── LangSmith ─────────────────────────────────────────────────────────
    langsmith_tracing: str = "true"
    langsmith_api_key: str = ""
    langsmith_project: str = "urbanpulse-langgraph"

    # ── LangGraph ─────────────────────────────────────────────────────────
    langgraph_model: str = "gpt-4o-mini"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
