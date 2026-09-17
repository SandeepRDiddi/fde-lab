from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment variables / .env."""

    database_url: str = "postgresql+psycopg2://fde:fde@localhost:5432/fde_lab"
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_prefix="FDE_", env_file=".env", extra="ignore")


settings = Settings()
