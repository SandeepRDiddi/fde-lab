from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment variables / .env."""

    s3_endpoint_url: str = "http://localhost:9000"
    s3_bucket: str = "fde-lab-datasets"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    backend_base_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_prefix="FDE_", env_file=".env", extra="ignore")


settings = Settings()
