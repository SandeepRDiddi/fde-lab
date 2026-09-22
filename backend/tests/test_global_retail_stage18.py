from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_RCA = (
    "Incident RCA: response latency jumped from roughly 2 seconds to 18 "
    "seconds mid-morning, with no matching deployment in the log. The "
    "root cause traces to a connection pool exhausted by a retry storm "
    "against a slow downstream call, not a code change. Mitigation: cap "
    "and back off the retries, and add a circuit breaker so one slow "
    "dependency can't starve the whole pool again. A status update went "
    "out to store operations as soon as the pool exhaustion was "
    "confirmed, well before the fix was fully deployed, so associates "
    "knew it was being actively worked."
)


def test_stage_18_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[18])


def test_stage_18_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[18]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_18_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[18]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_18_persona_states_specific_latency_numbers():
    prompt = GLOBAL_RETAIL_STAGES[18]["persona"]["system_prompt"]
    assert "2 seconds to about 18 seconds" in prompt


def test_compliant_rca_passes_stage_18_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_RCA, GLOBAL_RETAIL_STAGES[18]["compliance_checklist"])
    assert passed, failures


def test_missing_latency_numbers_fails_stage_18_checklist():
    without_numbers = _COMPLIANT_RCA.replace("18 seconds", "much slower")
    passed, failures = evaluate_submission(without_numbers, GLOBAL_RETAIL_STAGES[18]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "latency-numbers-named" for f in failures)


def test_missing_status_update_fails_stage_18_checklist():
    without_status = _COMPLIANT_RCA.replace("A status update went out", "Operations was told")
    passed, failures = evaluate_submission(without_status, GLOBAL_RETAIL_STAGES[18]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "status-update-while-unfolding" for f in failures)


def test_missing_root_cause_fails_stage_18_checklist():
    without_root_cause = _COMPLIANT_RCA.replace("The root cause traces to", "This was caused by")
    passed, failures = evaluate_submission(without_root_cause, GLOBAL_RETAIL_STAGES[18]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "root-cause-named" for f in failures)
