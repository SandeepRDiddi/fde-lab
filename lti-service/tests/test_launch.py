import time

import jwt
import pytest
from fastapi import HTTPException

from app import keys
from app.launch import validate_launch
from app.state_store import state_store
from tests.conftest import TEST_DEPLOYMENT_ID, TEST_KID


def _seed_login_state(test_platform, nonce="test-nonce", deployment_id=TEST_DEPLOYMENT_ID):
    state = "test-state"
    state_store.put(
        f"lti:login-state:{state}",
        f"{test_platform.key}|{nonce}|{deployment_id}",
        60,
    )
    return state


def _sign_id_token(test_platform, platform_keys, *, nonce="test-nonce", overrides=None):
    now = int(time.time())
    claims = {
        "iss": test_platform.issuer,
        "aud": test_platform.client_id,
        "sub": "student-42",
        "iat": now,
        "exp": now + 300,
        "nonce": nonce,
        "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest",
        "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
        "https://purl.imsglobal.org/spec/lti/claim/deployment_id": TEST_DEPLOYMENT_ID,
        "https://purl.imsglobal.org/spec/lti/claim/context": {
            "id": "course-101",
            "label": "AI-201",
        },
        "https://purl.imsglobal.org/spec/lti/claim/roles": [
            "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"
        ],
        "name": "Ada Student",
        "email": "ada@example.com",
    }
    if overrides:
        claims.update(overrides)
    return jwt.encode(
        claims,
        platform_keys["private_key"],
        algorithm="RS256",
        headers={"kid": TEST_KID},
    )


@pytest.fixture(autouse=True)
def _patch_platform_jwks(monkeypatch, platform_keys):
    monkeypatch.setattr(keys, "fetch_platform_jwks", lambda url: platform_keys["jwks"])


def test_valid_launch_extracts_lti_claims(test_platform, platform_keys):
    state = _seed_login_state(test_platform)
    id_token = _sign_id_token(test_platform, platform_keys)

    launch = validate_launch(state=state, id_token=id_token)

    assert launch.subject == "student-42"
    assert launch.issuer == test_platform.issuer
    assert launch.deployment_id == TEST_DEPLOYMENT_ID
    assert launch.context_id == "course-101"
    assert launch.name == "Ada Student"
    assert "Learner" in launch.roles[0]

    # state is one-time use
    with pytest.raises(HTTPException):
        validate_launch(state=state, id_token=id_token)


def test_nonce_mismatch_is_rejected(test_platform, platform_keys):
    state = _seed_login_state(test_platform, nonce="expected-nonce")
    id_token = _sign_id_token(test_platform, platform_keys, nonce="wrong-nonce")

    with pytest.raises(HTTPException) as exc_info:
        validate_launch(state=state, id_token=id_token)
    assert exc_info.value.status_code == 400


def test_unregistered_deployment_is_rejected(test_platform, platform_keys):
    state = _seed_login_state(test_platform, deployment_id="1:unknown-deployment")
    id_token = _sign_id_token(
        test_platform,
        platform_keys,
        overrides={
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id": "1:unknown-deployment"
        },
    )

    with pytest.raises(HTTPException):
        validate_launch(state=state, id_token=id_token)


def test_unknown_state_is_rejected(test_platform, platform_keys):
    id_token = _sign_id_token(test_platform, platform_keys)
    with pytest.raises(HTTPException) as exc_info:
        validate_launch(state="never-issued", id_token=id_token)
    assert exc_info.value.status_code == 400


def test_multi_audience_without_matching_azp_is_rejected(test_platform, platform_keys):
    state = _seed_login_state(test_platform)
    id_token = _sign_id_token(
        test_platform,
        platform_keys,
        overrides={"aud": [test_platform.client_id, "some-other-client"], "azp": "some-other-client"},
    )

    with pytest.raises(HTTPException) as exc_info:
        validate_launch(state=state, id_token=id_token)
    assert exc_info.value.status_code == 400


def test_multi_audience_with_matching_azp_is_accepted(test_platform, platform_keys):
    state = _seed_login_state(test_platform)
    id_token = _sign_id_token(
        test_platform,
        platform_keys,
        overrides={"aud": [test_platform.client_id, "some-other-client"], "azp": test_platform.client_id},
    )

    launch = validate_launch(state=state, id_token=id_token)
    assert launch.subject == "student-42"


def test_nrps_and_ags_claims_pass_through(test_platform, platform_keys):
    state = _seed_login_state(test_platform)
    id_token = _sign_id_token(
        test_platform,
        platform_keys,
        overrides={
            "https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice": {
                "context_memberships_url": "https://canvas.test.instructure.com/api/lti/courses/101/names_and_roles",
                "service_versions": ["2.0"],
            },
            "https://purl.imsglobal.org/spec/lti-ags/claim/endpoint": {
                "scope": ["https://purl.imsglobal.org/spec/lti-ags/scope/score"],
                "lineitem": "https://canvas.test.instructure.com/api/lti/courses/101/line_items/9",
            },
        },
    )

    launch = validate_launch(state=state, id_token=id_token)

    assert launch.nrps["context_memberships_url"].endswith("/names_and_roles")
    assert launch.ags["lineitem"].endswith("/line_items/9")
