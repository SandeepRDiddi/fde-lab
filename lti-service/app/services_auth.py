"""OAuth2 client-credentials (JWT-bearer) flow the tool uses to call a
platform's NRPS/AGS service APIs, per the IMS Security Framework. Shared by
nrps.py and ags.py -- they only differ in which scope they request.
"""
import time
import uuid
from typing import Dict

import httpx
import jwt

from .config import PlatformConfig, settings

_token_cache: Dict[str, Dict[str, float]] = {}


def _cache_key(platform: PlatformConfig, scope: str) -> str:
    return f"{platform.key}:{scope}"


def get_access_token(platform: PlatformConfig, scope: str) -> str:
    key = _cache_key(platform, scope)
    cached = _token_cache.get(key)
    if cached and cached["expires_at"] > time.time():
        return cached["access_token"]

    now = int(time.time())
    client_assertion = jwt.encode(
        {
            "iss": platform.client_id,
            "sub": platform.client_id,
            "aud": platform.auth_token_url,
            "iat": now,
            "exp": now + 60,
            "jti": uuid.uuid4().hex,
        },
        settings.tool_private_key_pem,
        algorithm="RS256",
        headers={"kid": settings.tool_key_id},
    )

    response = httpx.post(
        platform.auth_token_url,
        data={
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": client_assertion,
            "scope": scope,
        },
        timeout=10.0,
    )
    response.raise_for_status()
    body = response.json()
    _token_cache[key] = {
        "access_token": body["access_token"],
        "expires_at": time.time() + body.get("expires_in", 3600) - 30,
    }
    return body["access_token"]
