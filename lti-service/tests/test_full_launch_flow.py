"""End-to-end simulation of a Canvas-shaped LTI 1.3 launch, from OIDC login
initiation through to landing on the mapped scenario instance with a session
cookie set -- no live Canvas/Moodle sandbox available in this environment,
so this is the check that stands in for FDE-011's "test launch from at least
one LMS" definition-of-done item. See lti-service/README.md.
"""
import time
import urllib.parse

import jwt
from fastapi.testclient import TestClient

from app import keys, scenario_client
from app.config import settings
from app.main import app
from tests.conftest import TEST_DEPLOYMENT_ID, TEST_KID

client = TestClient(app)


def test_login_then_launch_lands_on_mapped_scenario_instance(
    test_platform, platform_keys, monkeypatch
):
    monkeypatch.setattr(keys, "fetch_platform_jwks", lambda url: platform_keys["jwks"])

    class FakeScenarioResponse:
        status_code = 200

        def json(self):
            return {"scenario_instance_id": "sc-inst-777", "launch_path": "/scenario/sc-inst-777"}

    monkeypatch.setattr(
        scenario_client.httpx, "get", lambda *a, **kw: FakeScenarioResponse()
    )

    login_response = client.get(
        "/lti/login",
        params={
            "iss": test_platform.issuer,
            "login_hint": "student-42",
            "target_link_uri": "https://lti.fde-lab.test/lti/launch",
            "client_id": test_platform.client_id,
            "lti_deployment_id": TEST_DEPLOYMENT_ID,
        },
        follow_redirects=False,
    )
    assert login_response.status_code == 302
    redirect_url = login_response.headers["location"]
    query = dict(urllib.parse.parse_qsl(redirect_url.partition("?")[2]))
    state = query["state"]
    nonce = query["nonce"]

    now = int(time.time())
    id_token = jwt.encode(
        {
            "iss": test_platform.issuer,
            "aud": test_platform.client_id,
            "sub": "student-42",
            "iat": now,
            "exp": now + 300,
            "nonce": nonce,
            "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest",
            "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id": TEST_DEPLOYMENT_ID,
            "https://purl.imsglobal.org/spec/lti/claim/context": {"id": "course-101"},
            "https://purl.imsglobal.org/spec/lti/claim/roles": [],
            "name": "Ada Student",
            "email": "ada@example.com",
        },
        platform_keys["private_key"],
        algorithm="RS256",
        headers={"kid": TEST_KID},
    )

    launch_response = client.post(
        "/lti/launch",
        data={"state": state, "id_token": id_token},
        follow_redirects=False,
    )

    assert launch_response.status_code == 303
    assert launch_response.headers["location"] == f"{settings.frontend_base_url}/scenario/sc-inst-777"
    assert settings.session_cookie_name in launch_response.cookies
