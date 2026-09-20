from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment variables / .env."""

    # Shared Postgres instance with the scenario engine (backend) — the persona
    # service reads/writes the `scenario_instances.config` column directly rather
    # than calling the backend over HTTP, per architecture.md's "shared data layer".
    database_url: str = "postgresql+psycopg2://fde:fde@localhost:5432/fde_lab"

    # PromptOps Gateway — all model calls are meant to route through here
    # (architecture.md → AI persona service), but no real gateway exists yet
    # and a hosted Claude/GPT API costs real money for a training lab.
    # Defaults to Groq (see gateway.py) -- hosts open-weight models on
    # dedicated inference hardware, free tier covers a training cohort's
    # volume, far faster than a local CPU-bound Ollama instance was. Swap the
    # URL to a real gateway (or back to a local Ollama's /v1 endpoint) later
    # without touching the rest of the app -- gateway.py speaks the same
    # OpenAI-compatible contract either way.
    promptops_gateway_url: str = "https://api.groq.com/openai/v1"
    promptops_gateway_api_key: str = ""
    promptops_gateway_model: str = "openai/gpt-oss-20b"

    model_config = SettingsConfigDict(env_prefix="FDE_", env_file=".env", extra="ignore")


settings = Settings()
