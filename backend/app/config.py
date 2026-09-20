from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment variables / .env."""

    database_url: str = "postgresql+psycopg2://fde:fde@localhost:5432/fde_lab"
    redis_url: str = "redis://localhost:6379/0"

    # FDE-012: platform-level service (not per-cohort, lives outside any
    # cohort's own namespace) that holds the cluster credentials to create
    # cohort namespaces. Only meaningful when this backend is itself
    # running in a Kubernetes cluster (Phase 4) -- unused by the Docker
    # Compose deployment target.
    k8s_provisioner_url: str = "http://k8s-provisioner.fde-lab-platform.svc.cluster.local:8000"

    # FDE-005's mock legacy API (mocks/legacy-api). Backend proxies to it
    # (app/routers/legacy_system.py) so students never need to know its
    # internal service address, and so the mock's own quirks -- schema
    # drift, latency, an unhelpful 401 on missing/wrong auth -- come through
    # to the student exactly as that service produces them.
    legacy_api_base_url: str = "http://localhost:8005"

    # FDE-013: technical-task grading fetches the scenario's own synthetic
    # dataset (data-gen's output) to grade a submitted SQL query against --
    # same bucket/credentials shape as generator/config.py in data-gen/.
    s3_endpoint_url: str = "http://localhost:9000"
    s3_bucket: str = "fde-lab-datasets"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"

    # FDE-014: scenario generator drafts a scenario's config from a raw
    # instructor requirement via the same OpenAI-compatible model backend
    # persona-service uses (see persona-service/app/gateway.py) -- Groq by
    # default (open-weight models, free tier, far faster than a local
    # CPU-bound Ollama instance was).
    promptops_gateway_url: str = "https://api.groq.com/openai/v1"
    promptops_gateway_api_key: str = ""
    promptops_gateway_model: str = "openai/gpt-oss-20b"

    model_config = SettingsConfigDict(env_prefix="FDE_", env_file=".env", extra="ignore")


settings = Settings()
