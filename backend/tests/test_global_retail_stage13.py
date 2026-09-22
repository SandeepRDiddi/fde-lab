from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_PLAYBOOK = (
    "Failure Playbook, proven against the SAP-standin dependency's induced "
    "timeout. Retry: bounded attempts with backoff before giving up on the "
    "call. Fallback: if retries exhaust, serve the last-known-good cached "
    "order status instead of a hard failure. Circuit breaker: after "
    "repeated timeouts, the breaker opens and stops sending calls for a "
    "cooldown window, protecting the rest of the platform from cascading "
    "delay. Dead-letter: any request that still can't complete lands in a "
    "dead-letter queue for manual replay rather than silently vanishing. "
    "Rollback and graceful degradation: the system serves a clearly-marked "
    "stale answer rather than crashing, and a later successful call "
    "reconciles the record automatically."
)


def test_stage_13_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[13])


def test_stage_13_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[13]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_13_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[13]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_13_persona_references_stage2_sap_standin():
    prompt = GLOBAL_RETAIL_STAGES[13]["persona"]["system_prompt"]
    assert "already hit a real access gap" in prompt


def test_compliant_playbook_passes_stage_13_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_PLAYBOOK, GLOBAL_RETAIL_STAGES[13]["compliance_checklist"])
    assert passed, failures


def test_missing_circuit_breaker_fails_stage_13_checklist():
    without_breaker = _COMPLIANT_PLAYBOOK.replace("Circuit breaker", "Overload protection")
    passed, failures = evaluate_submission(without_breaker, GLOBAL_RETAIL_STAGES[13]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "circuit-breaker-pattern" for f in failures)


def test_missing_dead_letter_fails_stage_13_checklist():
    # Two occurrences (the pattern-name intro and the later mention) --
    # both must go for must_include to actually fail.
    without_dlq = (
        _COMPLIANT_PLAYBOOK.replace("Dead-letter", "Unrecoverable requests")
        .replace("dead-letter queue", "a manual-replay queue")
    )
    passed, failures = evaluate_submission(without_dlq, GLOBAL_RETAIL_STAGES[13]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "dead-letter-pattern" for f in failures)


def test_missing_graceful_degradation_fails_stage_13_checklist():
    without_degradation = _COMPLIANT_PLAYBOOK.replace("graceful degradation", "a fallback path")
    passed, failures = evaluate_submission(without_degradation, GLOBAL_RETAIL_STAGES[13]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "rollback-degradation" for f in failures)
