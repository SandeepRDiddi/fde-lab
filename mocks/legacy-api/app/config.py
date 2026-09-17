from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment variables / .env."""

    scenario_dir: Path = Path(__file__).resolve().parent.parent / "scenarios"

    model_config = SettingsConfigDict(env_prefix="LEGACY_MOCK_", env_file=".env", extra="ignore")


settings = Settings()
