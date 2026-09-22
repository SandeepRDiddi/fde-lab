from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_MODEL = (
    "Canonical entity: Order. SAP represents an order as a purchase "
    "transaction record with line items and pricing. Salesforce's 'order' "
    "is actually a support case referencing an order number, not the order "
    "itself -- these are related entities, not the same one. The warehouse "
    "system's 'order' is a fulfillment job with pick/pack/ship states. The "
    "canonical model treats these as three linked entities under one order "
    "identifier, not one shared table. Canonical entity: Delay. Ops "
    "defines delay as exceeding a defined SLA window from order placement. "
    "The warehouse's internal backlog notion is a leading indicator, not "
    "the canonical definition -- it's reconciled into the same SLA clock "
    "rather than tracked separately."
)


def test_stage_6_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[6])


def test_stage_6_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[6]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_6_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[6]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_6_persona_encodes_three_order_meanings():
    prompt = GLOBAL_RETAIL_STAGES[6]["persona"]["system_prompt"]
    assert "purchase transaction" in prompt
    assert "support case" in prompt
    assert "fulfillment job" in prompt


def test_compliant_semantic_model_passes_stage_6_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_MODEL, GLOBAL_RETAIL_STAGES[6]["compliance_checklist"])
    assert passed, failures


def test_missing_canonical_framing_fails_stage_6_checklist():
    without_canonical = _COMPLIANT_MODEL.replace("Canonical entity", "Entity").replace("canonical model", "model")
    passed, failures = evaluate_submission(without_canonical, GLOBAL_RETAIL_STAGES[6]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "canonical-definition" for f in failures)


def test_missing_sla_reconciliation_fails_stage_6_checklist():
    without_sla = _COMPLIANT_MODEL.replace("SLA", "target")
    passed, failures = evaluate_submission(without_sla, GLOBAL_RETAIL_STAGES[6]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "delay-sla-meaning" for f in failures)
