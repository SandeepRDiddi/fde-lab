"""Step 1 of the LTI 1.3 launch: third-party initiated OIDC login.

The LMS hits this endpoint first (per the IMS Security Framework), we look
up the platform registration, stash a `state`/`nonce` pair, and redirect the
browser to the platform's own authorization endpoint. The platform then
form_posts an id_token back to /lti/launch.
"""
import secrets
import urllib.parse
from typing import Optional

from fastapi import HTTPException

from .config import settings
from .state_store import state_store


def build_authentication_redirect(
    *,
    iss: str,
    login_hint: str,
    target_link_uri: str,
    client_id: Optional[str],
    lti_deployment_id: Optional[str],
    lti_message_hint: Optional[str],
) -> str:
    platform = settings.platform_for(iss, client_id)
    if platform is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unregistered LTI platform (iss={iss!r}, client_id={client_id!r})",
        )

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    # The launch handler needs the platform + deployment back to validate the
    # id_token against the right registration; carry them alongside the nonce
    # rather than trusting whatever the id_token claims until it's verified.
    state_store.put(
        f"lti:login-state:{state}",
        f"{platform.key}|{nonce}|{lti_deployment_id or ''}",
        settings.login_state_ttl_seconds,
    )

    params = {
        "scope": "openid",
        "response_type": "id_token",
        "client_id": platform.client_id,
        "redirect_uri": target_link_uri,
        "login_hint": login_hint,
        "state": state,
        "nonce": nonce,
        "response_mode": "form_post",
        "prompt": "none",
    }
    if lti_deployment_id:
        params["lti_deployment_id"] = lti_deployment_id
    if lti_message_hint:
        params["lti_message_hint"] = lti_message_hint

    return f"{platform.auth_login_url}?{urllib.parse.urlencode(params)}"
