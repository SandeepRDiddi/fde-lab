from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_ARCHITECTURE = (
    "Revised Target Architecture, after the Architecture Review Board "
    "rejected the original direct-database-access proposal: every "
    "integration now routes through an API gateway in front of SAP, "
    "Salesforce, and the warehouse system -- no service reads a database "
    "directly, satisfying the platform's API-only standard. Identity: all "
    "components authenticate through GlobalRetail's existing SSO/OIDC "
    "provider rather than a separate credential store, per the platform "
    "team's identity requirement. The rest of the original design -- the "
    "context layer, the agent layer, the event stream consumers -- is "
    "unchanged; only the data-access pattern was revised."
)


def test_stage_7_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[7])


def test_stage_7_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[7]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_7_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[7]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_7_persona_frames_rejection_as_revision_not_restart():
    prompt = GLOBAL_RETAIL_STAGES[7]["persona"]["system_prompt"]
    assert "rejected" in prompt
    assert "not start over" in prompt


def test_compliant_architecture_passes_stage_7_checklist():
    passed, failures = evaluate_submission(
        _COMPLIANT_ARCHITECTURE, GLOBAL_RETAIL_STAGES[7]["compliance_checklist"]
    )
    assert passed, failures


def test_missing_api_gateway_fails_stage_7_checklist():
    without_gateway = _COMPLIANT_ARCHITECTURE.replace("API gateway", "API layer")
    passed, failures = evaluate_submission(without_gateway, GLOBAL_RETAIL_STAGES[7]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "api-gateway-integration" for f in failures)


def test_missing_sso_fails_stage_7_checklist():
    without_sso = _COMPLIANT_ARCHITECTURE.replace("SSO/OIDC", "single sign-on")
    passed, failures = evaluate_submission(without_sso, GLOBAL_RETAIL_STAGES[7]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "sso-addressed" for f in failures)


def test_missing_arb_acknowledgment_fails_stage_7_checklist():
    without_arb = _COMPLIANT_ARCHITECTURE.replace("Architecture Review Board", "the reviewers")
    passed, failures = evaluate_submission(without_arb, GLOBAL_RETAIL_STAGES[7]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "acknowledges-rejection" for f in failures)
