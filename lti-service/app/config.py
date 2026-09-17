"""Environment-driven configuration for the LTI launch service.

Kept as a single module (rather than pydantic BaseSettings) to avoid pulling
in a settings-management dependency this small service doesn't otherwise
need -- every other module imports `settings` from here.
"""
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class PlatformConfig:
    """One registered LMS (a Canvas or Moodle instance) speaking LTI 1.3 to us."""

    issuer: str
    client_id: str
    deployment_ids: List[str]
    auth_login_url: str
    auth_token_url: str
    key_set_url: str

    @property
    def key(self) -> str:
        # A platform can issue on behalf of several client_ids (e.g. a Canvas
        # instance shared by two courses registered as separate dev keys), so
        # (issuer, client_id) together identify a registration, not issuer alone.
        return f"{self.issuer}::{self.client_id}"


def _load_platforms() -> Dict[str, PlatformConfig]:
    raw = os.environ.get("LTI_PLATFORMS_JSON", "[]")
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"LTI_PLATFORMS_JSON is not valid JSON: {exc}") from exc
    platforms: Dict[str, PlatformConfig] = {}
    for entry in entries:
        cfg = PlatformConfig(
            issuer=entry["issuer"],
            client_id=entry["client_id"],
            deployment_ids=entry.get("deployment_ids", []),
            auth_login_url=entry["auth_login_url"],
            auth_token_url=entry["auth_token_url"],
            key_set_url=entry["key_set_url"],
        )
        platforms[cfg.key] = cfg
    return platforms


@dataclass
class Settings:
    platforms: Dict[str, PlatformConfig] = field(default_factory=_load_platforms)

    # This tool's own RSA keypair, used to (a) sign the FDE Lab session token
    # issued after a successful launch and (b) sign client-assertion JWTs when
    # requesting NRPS/AGS access tokens from the platform's token endpoint.
    tool_private_key_pem: str = os.environ.get("LTI_TOOL_PRIVATE_KEY_PEM", "")
    tool_public_key_pem: str = os.environ.get("LTI_TOOL_PUBLIC_KEY_PEM", "")
    tool_key_id: str = os.environ.get("LTI_TOOL_KEY_ID", "fde-lti-key-1")

    # Where the launch redirects a student once the session is established.
    frontend_base_url: str = os.environ.get("FRONTEND_BASE_URL", "http://localhost:3000")

    # Scenario engine's internal API (FDE-001). Not yet deployed alongside
    # this service in this branch -- see lti-service/README.md.
    scenario_engine_base_url: str = os.environ.get(
        "SCENARIO_ENGINE_BASE_URL", "http://backend:8000"
    )
    scenario_engine_internal_token: str = os.environ.get(
        "SCENARIO_ENGINE_INTERNAL_TOKEN", ""
    )

    session_ttl_seconds: int = int(os.environ.get("LTI_SESSION_TTL_SECONDS", "3600"))
    login_state_ttl_seconds: int = int(os.environ.get("LTI_LOGIN_STATE_TTL_SECONDS", "300"))
    session_cookie_name: str = os.environ.get("LTI_SESSION_COOKIE_NAME", "fde_session")

    redis_url: Optional[str] = os.environ.get("REDIS_URL")

    def platform_for(self, issuer: str, client_id: Optional[str] = None) -> Optional[PlatformConfig]:
        if client_id is not None:
            return self.platforms.get(f"{issuer}::{client_id}")
        matches = [p for p in self.platforms.values() if p.issuer == issuer]
        return matches[0] if len(matches) == 1 else None


settings = Settings()
