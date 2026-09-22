from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_DASHBOARD = (
    "Observability design: every answer gets a full trace correlating the "
    "prompt sent to the model, every tool call it made and what each "
    "returned, and the resulting decision, so a repeat of the unexplained "
    "live incident could be reconstructed after the fact instead of "
    "shrugged at. Each trace also records latency per step and token "
    "usage, so a slow or expensive answer is visible in the same view as "
    "the reasoning that produced it, not a separate spreadsheet."
)


def test_stage_12_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[12])


def test_stage_12_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[12]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_12_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[12]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_12_persona_describes_unexplainable_incident():
    prompt = GLOBAL_RETAIL_STAGES[12]["persona"]["system_prompt"]
    assert "nobody could explain why" in prompt


def test_compliant_dashboard_passes_stage_12_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_DASHBOARD, GLOBAL_RETAIL_STAGES[12]["compliance_checklist"])
    assert passed, failures


def test_missing_tool_call_tracking_fails_stage_12_checklist():
    without_tool_calls = _COMPLIANT_DASHBOARD.replace("tool call", "system call")
    passed, failures = evaluate_submission(without_tool_calls, GLOBAL_RETAIL_STAGES[12]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "tool-calls-tracked" for f in failures)


def test_missing_latency_tracking_fails_stage_12_checklist():
    without_latency = _COMPLIANT_DASHBOARD.replace("latency", "timing")
    passed, failures = evaluate_submission(without_latency, GLOBAL_RETAIL_STAGES[12]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "tokens-latency-tracked" for f in failures)
