from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment variables / .env."""

    # Optional extra Helm values file (e.g. a cluster-specific
    # values-prod.yaml overriding image registries/ingress domain) applied
    # on top of chart/values.yaml for every provision call.
    chart_values_file: str | None = None

    model_config = SettingsConfigDict(env_prefix="FDE_K8S_PROVISIONER_", env_file=".env", extra="ignore")


settings = Settings()
