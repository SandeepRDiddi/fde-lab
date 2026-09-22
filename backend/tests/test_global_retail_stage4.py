from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_MATRIX = (
    "AI Readiness Matrix: order-status lookup is deterministic -- it's a "
    "simple database read, no judgment involved. Delay root-cause "
    "investigation is AI-assisted -- synthesizing signals across SAP, "
    "Salesforce, and the warehouse export benefits from AI, but a human "
    "still makes the final call. Supplier escalation is agentic -- it's a "
    "multi-step decision chain (check status, check inventory, check "
    "supplier ETA) that warrants an autonomous workflow with a human "
    "checkpoint. Return-eligibility determination stays deterministic: it "
    "is governed by consumer protection law, so an LLM plays no role in "
    "that decision path regardless of how well it might perform."
)


def test_stage_4_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[4])


def test_stage_4_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[4]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_4_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[4]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_4_persona_encodes_legal_constraint():
    prompt = GLOBAL_RETAIL_STAGES[4]["persona"]["system_prompt"]
    assert "consumer protection law" in prompt
    assert "must not be the one" in prompt


def test_compliant_matrix_passes_stage_4_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_MATRIX, GLOBAL_RETAIL_STAGES[4]["compliance_checklist"])
    assert passed, failures


def test_missing_deterministic_classification_fails_stage_4_checklist():
    # "deterministic" also appears once for the return-eligibility
    # classification -- must strip both occurrences for must_include to
    # actually fail.
    without_deterministic = _COMPLIANT_MATRIX.replace("deterministic", "fixed-logic")
    passed, failures = evaluate_submission(
        without_deterministic, GLOBAL_RETAIL_STAGES[4]["compliance_checklist"]
    )
    assert not passed
    assert any(f["rule_id"] == "lookup-deterministic" for f in failures)


def test_missing_agentic_classification_fails_stage_4_checklist():
    without_agentic = _COMPLIANT_MATRIX.replace("Supplier escalation is agentic", "Supplier escalation is complex")
    passed, failures = evaluate_submission(without_agentic, GLOBAL_RETAIL_STAGES[4]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "action-agentic" for f in failures)


def test_missing_legal_justification_fails_stage_4_checklist():
    without_legal = _COMPLIANT_MATRIX.replace("consumer protection law", "company policy")
    passed, failures = evaluate_submission(without_legal, GLOBAL_RETAIL_STAGES[4]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "return-eligibility-legal" for f in failures)
