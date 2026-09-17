"""Step 2 of the LTI 1.3 launch: validate the platform's id_token and hand
the student off to their scenario instance with no separate FDE Lab login.

Covers acceptance criteria 1 and 2 of FDE-011. NRPS/AGS (criteria 3 and 4)
are separate, optional calls made from `nrps.py` / `ags.py` using the claims
extracted here.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import jwt
from fastapi import HTTPException

from .config import settings
from .keys import public_key_for_kid
from .state_store import state_store

CLAIM_MESSAGE_TYPE = "https://purl.imsglobal.org/spec/lti/claim/message_type"
CLAIM_VERSION = "https://purl.imsglobal.org/spec/lti/claim/version"
CLAIM_DEPLOYMENT_ID = "https://purl.imsglobal.org/spec/lti/claim/deployment_id"
CLAIM_CONTEXT = "https://purl.imsglobal.org/spec/lti/claim/context"
CLAIM_ROLES = "https://purl.imsglobal.org/spec/lti/claim/roles"
CLAIM_NRPS = "https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice"
CLAIM_AGS = "https://purl.imsglobal.org/spec/lti-ags/claim/endpoint"

REQUIRED_MESSAGE_TYPE = "LtiResourceLinkRequest"
REQUIRED_VERSION = "1.3.0"


@dataclass
class LtiLaunch:
    subject: str
    issuer: str
    client_id: str
    deployment_id: str
    context_id: Optional[str]
    roles: List[str]
    name: Optional[str]
    email: Optional[str]
    context_label: Optional[str] = field(default=None)
    nrps: Optional[Dict[str, Any]] = field(default=None)
    ags: Optional[Dict[str, Any]] = field(default=None)


def _decode_header(id_token: str) -> Dict[str, Any]:
    try:
        return jwt.get_unverified_header(id_token)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=400, detail=f"Malformed id_token: {exc}") from exc


def validate_launch(*, state: str, id_token: str) -> LtiLaunch:
    stored = state_store.pop(f"lti:login-state:{state}")
    if stored is None:
        raise HTTPException(status_code=400, detail="Unknown or expired launch state")
    platform_key, expected_nonce, expected_deployment_id = stored.split("|", 2)
    platform = next((p for p in settings.platforms.values() if p.key == platform_key), None)
    if platform is None:
        raise HTTPException(status_code=400, detail="Launch state refers to an unknown platform")

    header = _decode_header(id_token)
    kid = header.get("kid")
    if not kid:
        raise HTTPException(status_code=400, detail="id_token is missing 'kid'")

    try:
        public_key = public_key_for_kid(platform.key_set_url, kid)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        claims = jwt.decode(
            id_token,
            key=public_key,
            algorithms=["RS256"],
            audience=platform.client_id,
            issuer=platform.issuer,
            options={"require": ["exp", "iat", "nonce", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=400, detail=f"id_token failed verification: {exc}") from exc

    # IMS Security Framework: when aud is an array (multiple audiences), azp
    # identifies which one is the actual authorized party -- pyjwt's audience
    # check only confirms our client_id is *somewhere* in aud, which isn't
    # enough to rule out audience confusion with a multi-value aud.
    aud = claims.get("aud")
    if isinstance(aud, list) and len(aud) > 1:
        if claims.get("azp") != platform.client_id:
            raise HTTPException(status_code=400, detail="azp does not match the expected client_id")

    if claims["nonce"] != expected_nonce:
        raise HTTPException(status_code=400, detail="nonce mismatch (possible replay)")

    if claims.get(CLAIM_MESSAGE_TYPE) != REQUIRED_MESSAGE_TYPE:
        raise HTTPException(status_code=400, detail="Only LtiResourceLinkRequest launches are supported")
    if claims.get(CLAIM_VERSION) != REQUIRED_VERSION:
        raise HTTPException(status_code=400, detail="Unsupported LTI version")

    deployment_id = claims.get(CLAIM_DEPLOYMENT_ID)
    if deployment_id not in platform.deployment_ids:
        raise HTTPException(status_code=400, detail=f"Unregistered deployment_id: {deployment_id!r}")
    if expected_deployment_id and expected_deployment_id != deployment_id:
        raise HTTPException(status_code=400, detail="deployment_id changed between login and launch")

    context = claims.get(CLAIM_CONTEXT) or {}

    return LtiLaunch(
        subject=claims["sub"],
        issuer=platform.issuer,
        client_id=platform.client_id,
        deployment_id=deployment_id,
        context_id=context.get("id"),
        context_label=context.get("label"),
        roles=claims.get(CLAIM_ROLES, []),
        name=claims.get("name"),
        email=claims.get("email"),
        nrps=claims.get(CLAIM_NRPS),
        ags=claims.get(CLAIM_AGS),
    )
