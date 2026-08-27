from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application configuration, sourced from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "vector-db"
    app_env: str = "development"
    log_level: str = "INFO"

    chroma_host: str = "localhost"
    chroma_port: int = 8001


@lru_cache
def get_settings() -> Settings:
    return Settings()
