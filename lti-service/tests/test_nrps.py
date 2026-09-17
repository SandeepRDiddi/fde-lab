import pytest

from app import nrps
from app.launch import LtiLaunch


def _launch(with_nrps=True, test_platform=None):
    return LtiLaunch(
        subject="student-42",
        issuer=test_platform.issuer,
        client_id=test_platform.client_id,
        deployment_id="1:abc123",
        context_id="course-101",
        roles=[],
        name=None,
        email=None,
        nrps={
            "context_memberships_url": "https://canvas.test.instructure.com/api/lti/courses/101/names_and_roles",
            "service_versions": ["2.0"],
        }
        if with_nrps
        else None,
    )


def test_fetch_roster_returns_members(test_platform, monkeypatch):
    launch = _launch(test_platform=test_platform)
    monkeypatch.setattr(nrps, "get_access_token", lambda platform, scope: "fake-token")

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"members": [{"user_id": "student-42", "roles": ["Learner"]}]}

    monkeypatch.setattr(nrps.httpx, "get", lambda url, headers, timeout: FakeResponse())

    members = nrps.fetch_roster(launch)
    assert members == [{"user_id": "student-42", "roles": ["Learner"]}]


def test_fetch_roster_without_nrps_claim_raises(test_platform):
    launch = _launch(with_nrps=False, test_platform=test_platform)
    with pytest.raises(ValueError):
        nrps.fetch_roster(launch)
