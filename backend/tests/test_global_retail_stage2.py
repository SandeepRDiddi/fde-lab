import uuid

import httpx

from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_MAP = (
    "Current-state assessment: SAP (core ERP), Salesforce, and the "
    "storefront all feed a central data lake per the existing diagram, "
    "though the diagram is known to be out of date. I attempted the SAP "
    "integration point directly and got back ERR-4471 with a 401 -- access "
    "is genuinely not available yet. Rather than wait on procurement to "
    "finish the request, I'm proceeding with what's reachable and flagging "
    "this as an open dependency to revisit. Separately, the warehouse/"
    "inventory integration is reachable but returns an inconsistent "
    "schema between calls -- I'm flagging this as an undocumented risk "
    "for anything built on top of it."
)


def test_stage_2_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[2])


def test_stage_2_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[2]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_2_legacy_system_shape_matches_router_expectations():
    legacy = GLOBAL_RETAIL_STAGES[2]["legacy_system"]
    assert legacy["scenario_id"] == "acme-crm"
    assert legacy["path"] == "/accounts"
    assert legacy["auth_header_name"] == "X-Legacy-Auth"


def test_stage_2_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[2]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_launching_global_retail_engagement_includes_stage_2_legacy_system(client):
    payload = {"cohort_id": str(uuid.uuid4()), "student_id": str(uuid.uuid4())}
    engagement = client.post("/engagements/global-retail", json=payload).json()

    assert len(engagement["stages"]) >= 3
    assert engagement["stages"][2]["config"]["legacy_system"]["scenario_id"] == "acme-crm"


def test_calling_stage_2_legacy_system_without_credentials_gets_real_401(client, monkeypatch):
    """The injected access gap is real, not narrated (FDE-020 AC1): no
    X-Legacy-Auth header means the mock's actual unhelpful 401 comes back
    through the existing FDE-005 proxy unchanged."""
    payload = {"cohort_id": str(uuid.uuid4()), "student_id": str(uuid.uuid4())}
    engagement = client.post("/engagements/global-retail", json=payload).json()
    stage2_id = engagement["stages"][2]["id"]

    def fake_get(url, headers=None, timeout=None):
        assert not headers
        return httpx.Response(401, json={"error": "ERR-4471", "message": "request could not be completed"})

    monkeypatch.setattr("app.routers.legacy_system.httpx.get", fake_get)

    response = client.get(f"/scenario-instances/{stage2_id}/legacy-system")
    assert response.status_code == 401
    assert response.json()["error"] == "ERR-4471"


def test_compliant_dependency_map_passes_stage_2_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_MAP, GLOBAL_RETAIL_STAGES[2]["compliance_checklist"])
    assert passed, failures


def test_missing_blocked_system_evidence_fails_stage_2_checklist():
    without_error_code = _COMPLIANT_MAP.replace("ERR-4471", "an error")
    passed, failures = evaluate_submission(without_error_code, GLOBAL_RETAIL_STAGES[2]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "hit-blocked-system" for f in failures)


def test_missing_schema_drift_flag_fails_stage_2_checklist():
    without_schema = _COMPLIANT_MAP.replace("inconsistent schema between calls", "unreliable")
    passed, failures = evaluate_submission(without_schema, GLOBAL_RETAIL_STAGES[2]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "flagged-schema-drift" for f in failures)


def test_missing_procurement_decision_fails_stage_2_checklist():
    without_procurement = _COMPLIANT_MAP.replace("procurement", "IT")
    passed, failures = evaluate_submission(without_procurement, GLOBAL_RETAIL_STAGES[2]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "proceeding-without-access" for f in failures)
