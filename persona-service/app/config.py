from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment variables / .env."""

    # Shared Postgres instance with the scenario engine (backend) — the persona
    # service reads/writes the `scenario_instances.config` column directly rather
    # than calling the backend over HTTP, per architecture.md's "shared data layer".
    database_url: str = "postgresql+psycopg2://fde:fde@localhost:5432/fde_lab"

    # PromptOps Gateway — all model calls route through here, never the Claude API
    # directly (architecture.md → AI persona service).
    promptops_gateway_url: str = "http://localhost:8100"
    promptops_gateway_api_key: str = ""
    promptops_gateway_model: str = "claude-sonnet-5"

    model_config = SettingsConfigDict(env_prefix="FDE_", env_file=".env", extra="ignore")


settings = Settings()
