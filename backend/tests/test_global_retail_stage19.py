from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_ASSESSMENT = (
    "Change Impact Assessment: the warehouse's schema change touches every "
    "consumer of the inventory feed. Blast radius covers the order-status "
    "lookup, the delay-investigation agent, and the nightly reconciliation "
    "job -- all three read this field. The contract's schema version bumps "
    "to reflect the new shape, and validation now accepts both the old and "
    "new field names for a transition window, so the change stays backward "
    "compatible for anything already live rather than breaking it outright. "
    "Separately, the new capability Ops asked for this week gets scoped and "
    "scheduled on its own track -- it doesn't block shipping the schema fix "
    "first."
)


def test_stage_19_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[19])


def test_stage_19_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[19]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_19_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[19]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_19_persona_relays_the_separate_ops_ask():
    prompt = GLOBAL_RETAIL_STAGES[19]["persona"]["system_prompt"]
    assert "Priya Anand" in prompt
    assert "not asking to block the schema fix" in prompt


def test_compliant_assessment_passes_stage_19_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_ASSESSMENT, GLOBAL_RETAIL_STAGES[19]["compliance_checklist"])
    assert passed, failures


def test_missing_blast_radius_fails_stage_19_checklist():
    without_blast_radius = _COMPLIANT_ASSESSMENT.replace("Blast radius covers", "This touches")
    passed, failures = evaluate_submission(without_blast_radius, GLOBAL_RETAIL_STAGES[19]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "blast-radius-assessed" for f in failures)


def test_missing_backward_compatibility_fails_stage_19_checklist():
    without_compat = _COMPLIANT_ASSESSMENT.replace("backward compatible", "safe")
    passed, failures = evaluate_submission(without_compat, GLOBAL_RETAIL_STAGES[19]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "backward-compatible" for f in failures)


def test_missing_new_capability_addressed_fails_stage_19_checklist():
    without_capability = _COMPLIANT_ASSESSMENT.replace("the new capability Ops asked for", "the Ops request")
    passed, failures = evaluate_submission(without_capability, GLOBAL_RETAIL_STAGES[19]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "new-capability-addressed" for f in failures)
