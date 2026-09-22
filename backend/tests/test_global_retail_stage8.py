from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_CONTRACT = (
    "Data Contract: warehouse/inventory integration. Every payload carries "
    "an explicit schema version field so the consumer knows which shape to "
    "expect instead of guessing from field casing. Incoming payloads go "
    "through validation against the declared schema version before "
    "anything downstream touches them -- a payload that fails validation "
    "is quarantined, not silently accepted like the salvaged vendor code "
    "did. The warehouse team keeps its independent release calendar; the "
    "contract's job is to make a schema change loud and caught at the "
    "boundary, not to block their releases."
)


def test_stage_8_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[8])


def test_stage_8_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[8]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_8_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[8]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_8_persona_references_the_same_schema_drift_found_earlier():
    prompt = GLOBAL_RETAIL_STAGES[8]["persona"]["system_prompt"]
    assert "inconsistent schema between calls" in prompt


def test_compliant_contract_passes_stage_8_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_CONTRACT, GLOBAL_RETAIL_STAGES[8]["compliance_checklist"])
    assert passed, failures


def test_missing_schema_versioning_fails_stage_8_checklist():
    without_versioning = _COMPLIANT_CONTRACT.replace("schema version", "shape identifier")
    passed, failures = evaluate_submission(without_versioning, GLOBAL_RETAIL_STAGES[8]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "schema-versioning" for f in failures)


def test_missing_validation_fails_stage_8_checklist():
    without_validation = _COMPLIANT_CONTRACT.replace("validation", "a sanity check")
    passed, failures = evaluate_submission(without_validation, GLOBAL_RETAIL_STAGES[8]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "validation" for f in failures)


def test_missing_release_calendar_ack_fails_stage_8_checklist():
    without_calendar = _COMPLIANT_CONTRACT.replace("release calendar", "release schedule")
    passed, failures = evaluate_submission(without_calendar, GLOBAL_RETAIL_STAGES[8]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "independent-release-calendar" for f in failures)
