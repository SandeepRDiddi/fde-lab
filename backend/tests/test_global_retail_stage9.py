from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_WRITEUP = (
    "Working AI Service design. Supplier-lookup resilience: calls wrap a "
    "bounded retry with exponential backoff, since the API occasionally "
    "returns a bare 500; the response body carries nothing else to act "
    "on. After the retry budget is exhausted, the tool call fails loud "
    "rather than hanging. Retrieval "
    "quality: on an ambiguous supplier-substitution question, the current "
    "vector search answers fluently but wrongly instead of admitting "
    "uncertainty. The fix is a confidence check on retrieval score: below "
    "threshold, the service asks a clarifying question instead of "
    "answering outright, rather than presenting a guess as fact."
)


def test_stage_9_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[9])


def test_stage_9_has_no_technical_task_or_dataset():
    """Both injected failure modes are persona-narrated -- no RAG/vector
    search service exists in this repo, and the legacy-api mock has no
    intermittent-500 scenario built (FDE-020 made the equivalent scope
    call for a second live legacy-system call)."""
    stage = GLOBAL_RETAIL_STAGES[9]
    assert "technical_task" not in stage
    assert "data_gen" not in stage
    assert "legacy_system" not in stage


def test_stage_9_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[9]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_9_persona_encodes_both_injected_failure_modes():
    prompt = GLOBAL_RETAIL_STAGES[9]["persona"]["system_prompt"]
    assert "bare HTTP 500" in prompt
    assert "confident answer that is simply wrong" in prompt


def test_compliant_writeup_passes_stage_9_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_WRITEUP, GLOBAL_RETAIL_STAGES[9]["compliance_checklist"])
    assert passed, failures


def test_missing_retry_fails_stage_9_checklist():
    without_retry = _COMPLIANT_WRITEUP.replace("retry", "backoff strategy")
    passed, failures = evaluate_submission(without_retry, GLOBAL_RETAIL_STAGES[9]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "flaky-api-resilience" for f in failures)


def test_missing_clarifying_question_mitigation_fails_stage_9_checklist():
    without_mitigation = _COMPLIANT_WRITEUP.replace("asks a clarifying question", "says it's unsure")
    passed, failures = evaluate_submission(without_mitigation, GLOBAL_RETAIL_STAGES[9]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "ambiguous-query-mitigation" for f in failures)
