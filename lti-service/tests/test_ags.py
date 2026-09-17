import pytest
from fastapi.testclient import TestClient

from app import ags
from app.launch import LtiLaunch
from app.launch_context_cache import remember
from app.main import app

client = TestClient(app)


def _launch(with_ags=True, lineitem="https://canvas.test.instructure.com/api/lti/courses/101/line_items/9", test_platform=None):
    return LtiLaunch(
        subject="student-42",
        issuer=test_platform.issuer,
        client_id=test_platform.client_id,
        deployment_id="1:abc123",
        context_id="course-101",
        roles=[],
        name=None,
        email=None,
        ags={
            "scope": ["https://purl.imsglobal.org/spec/lti-ags/scope/score"],
            "lineitem": lineitem,
        }
        if with_ags
        else None,
    )


def test_publish_score_posts_to_lineitem_scores_endpoint(test_platform, monkeypatch):
    launch = _launch(test_platform=test_platform)
    monkeypatch.setattr(ags, "get_access_token", lambda platform, scope: "fake-token")

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return FakeResponse()

    monkeypatch.setattr(ags.httpx, "post", fake_post)

    ags.publish_score(launch, score_given=90, score_maximum=100)

    assert captured["url"] == launch.ags["lineitem"] + "/scores"
    assert captured["json"]["userId"] == "student-42"
    assert captured["json"]["scoreGiven"] == 90
    assert captured["json"]["scoreMaximum"] == 100
    assert captured["json"]["gradingProgress"] == "FullyGraded"


def test_publish_score_without_ags_claim_raises(test_platform):
    launch = _launch(with_ags=False, test_platform=test_platform)
    with pytest.raises(ValueError):
        ags.publish_score(launch, score_given=90, score_maximum=100)


def test_publish_score_without_lineitem_raises(test_platform):
    launch = _launch(lineitem=None, test_platform=test_platform)
    with pytest.raises(ValueError):
        ags.publish_score(launch, score_given=90, score_maximum=100)


def test_score_push_endpoint_accepts_json_body(test_platform, monkeypatch):
    """Regression test: this endpoint used to bind student_sub/score_given/
    score_maximum as query params (no request model), which doesn't match
    how a real caller posts a score."""
    launch = _launch(test_platform=test_platform)
    key = remember(launch)
    monkeypatch.setattr(ags, "publish_score", lambda *a, **kw: None)

    response = client.post(
        f"/internal/lti-contexts/{key}/scores",
        json={"student_sub": "student-42", "score_given": 90, "score_maximum": 100},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "submitted"}
