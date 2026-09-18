from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment variables / .env."""

    # Shared Postgres instance with the scenario engine (backend) — the persona
    # service reads/writes the `scenario_instances.config` column directly rather
    # than calling the backend over HTTP, per architecture.md's "shared data layer".
    database_url: str = "postgresql+psycopg2://fde:fde@localhost:5432/fde_lab"

    # PromptOps Gateway — all model calls are meant to route through here
    # (architecture.md → AI persona service), but no real gateway exists yet
    # and a hosted Claude API costs real money for a training lab. Defaults
    # to a local Ollama instance instead (see gateway.py) -- free, runs
    # entirely on the training-cohort's own infrastructure. Swap the URL to
    # a real gateway later without touching the rest of the app.
    promptops_gateway_url: str = "http://host.docker.internal:11434"
    promptops_gateway_api_key: str = ""
    # A smaller model: on ordinary hardware sharing the machine with everything
    # else running locally, an 8B-class model (e.g. llama3.1) took 5+ minutes
    # to respond over HTTP; this 3B model answers in ~1-2s. Bump this if the
    # host has GPU headroom to spare.
    promptops_gateway_model: str = "llama3.2:3b"

    model_config = SettingsConfigDict(env_prefix="FDE_", env_file=".env", extra="ignore")


settings = Settings()
