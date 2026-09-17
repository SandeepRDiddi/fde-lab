import urllib.parse

import pytest
from fastapi import HTTPException

from app.oidc_login import build_authentication_redirect
from app.state_store import state_store


def test_redirects_to_platform_authorization_endpoint(test_platform):
    redirect_url = build_authentication_redirect(
        iss=test_platform.issuer,
        login_hint="student-42",
        target_link_uri="https://lti.fde-lab.test/lti/launch",
        client_id=test_platform.client_id,
        lti_deployment_id="1:abc123",
        lti_message_hint="hint-xyz",
    )

    base, _, query = redirect_url.partition("?")
    params = dict(urllib.parse.parse_qsl(query))

    assert base == test_platform.auth_login_url
    assert params["response_type"] == "id_token"
    assert params["scope"] == "openid"
    assert params["client_id"] == test_platform.client_id
    assert params["redirect_uri"] == "https://lti.fde-lab.test/lti/launch"
    assert params["login_hint"] == "student-42"
    assert params["response_mode"] == "form_post"
    assert params["prompt"] == "none"
    assert params["lti_deployment_id"] == "1:abc123"
    assert params["lti_message_hint"] == "hint-xyz"
    assert "state" in params and "nonce" in params

    stored = state_store.peek(f"lti:login-state:{params['state']}")
    assert stored is not None
    platform_key, nonce, deployment_id = stored.split("|", 2)
    assert platform_key == test_platform.key
    assert nonce == params["nonce"]
    assert deployment_id == "1:abc123"


def test_unregistered_platform_is_rejected():
    with pytest.raises(HTTPException) as exc_info:
        build_authentication_redirect(
            iss="https://not-registered.example.com",
            login_hint="student-42",
            target_link_uri="https://lti.fde-lab.test/lti/launch",
            client_id=None,
            lti_deployment_id=None,
            lti_message_hint=None,
        )
    assert exc_info.value.status_code == 400
