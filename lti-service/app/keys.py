"""RSA key handling: this tool's own signing key, and cached JWKS fetches
for the platforms it trusts (needed to verify each platform's id_token)."""
import base64
import json
import time
from typing import Any, Dict

import httpx
from cryptography.hazmat.primitives import serialization
from jwt.algorithms import RSAAlgorithm

from .config import settings

_JWKS_CACHE_TTL_SECONDS = 3600
_jwks_cache: Dict[str, Any] = {}


def tool_jwks() -> Dict[str, Any]:
    """This service's public JWKS, served at /.well-known/jwks.json so a
    platform can verify the client-assertion JWTs we send it for NRPS/AGS."""
    if not settings.tool_public_key_pem:
        raise RuntimeError("LTI_TOOL_PUBLIC_KEY_PEM is not configured")
    try:
        public_key = serialization.load_pem_public_key(settings.tool_public_key_pem.encode())
    except ValueError as exc:
        raise RuntimeError(f"LTI_TOOL_PUBLIC_KEY_PEM is not a valid PEM public key: {exc}") from exc
    jwk = json_web_key_from_public_key(public_key)
    jwk["kid"] = settings.tool_key_id
    jwk["use"] = "sig"
    jwk["alg"] = "RS256"
    return {"keys": [jwk]}


def json_web_key_from_public_key(public_key) -> Dict[str, Any]:
    numbers = public_key.public_numbers()

    def to_b64(n: int) -> str:
        length = (n.bit_length() + 7) // 8
        return base64.urlsafe_b64encode(n.to_bytes(length, "big")).rstrip(b"=").decode()

    return {
        "kty": "RSA",
        "n": to_b64(numbers.n),
        "e": to_b64(numbers.e),
    }


def fetch_platform_jwks(key_set_url: str) -> Dict[str, Any]:
    cached = _jwks_cache.get(key_set_url)
    if cached and cached["expires_at"] > time.monotonic():
        return cached["jwks"]
    response = httpx.get(key_set_url, timeout=10.0)
    response.raise_for_status()
    jwks = response.json()
    _jwks_cache[key_set_url] = {"jwks": jwks, "expires_at": time.monotonic() + _JWKS_CACHE_TTL_SECONDS}
    return jwks


def public_key_for_kid(key_set_url: str, kid: str):
    jwks = fetch_platform_jwks(key_set_url)
    for jwk in jwks.get("keys", []):
        if jwk.get("kid") == kid:
            return RSAAlgorithm.from_jwk(json.dumps(jwk))
    # kid rotated since our cache was populated -- refetch once before giving up
    _jwks_cache.pop(key_set_url, None)
    jwks = fetch_platform_jwks(key_set_url)
    for jwk in jwks.get("keys", []):
        if jwk.get("kid") == kid:
            return RSAAlgorithm.from_jwk(json.dumps(jwk))
    raise ValueError(f"No matching key for kid={kid!r} at {key_set_url}")
