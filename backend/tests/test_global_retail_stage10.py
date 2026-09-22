from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_WORKFLOW = (
    "Agent Workflow: order-delay investigation. A planner decomposes the "
    "task into check-status, check-inventory, check-supplier-ETA, then "
    "decide; a separate executor runs each tool call, keeping the planner "
    "free of tool-specific detail. Every tool call carries a hard retry "
    "limit of three attempts with exponential backoff -- past that, the "
    "step fails explicitly instead of looping forever, the direct fix for "
    "the earlier runaway run that burned tokens for hours. Before the "
    "agent decides whether to escalate to a human, a human checkpoint "
    "reviews the gathered evidence -- the escalate decision itself is "
    "never fully autonomous."
)


def test_stage_10_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[10])


def test_stage_10_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[10]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_10_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[10]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_10_persona_encodes_runaway_retry_incident():
    prompt = GLOBAL_RETAIL_STAGES[10]["persona"]["system_prompt"]
    assert "no limit on attempts" in prompt
    assert "burning through the token budget" in prompt


def test_compliant_workflow_passes_stage_10_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_WORKFLOW, GLOBAL_RETAIL_STAGES[10]["compliance_checklist"])
    assert passed, failures


def test_missing_retry_limit_fails_stage_10_checklist():
    without_limit = _COMPLIANT_WORKFLOW.replace("retry limit", "retry policy")
    passed, failures = evaluate_submission(without_limit, GLOBAL_RETAIL_STAGES[10]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "bounded-retries" for f in failures)


def test_missing_human_checkpoint_fails_stage_10_checklist():
    without_human = _COMPLIANT_WORKFLOW.replace("human checkpoint", "review step").replace(
        "escalate to a human", "escalate"
    )
    passed, failures = evaluate_submission(without_human, GLOBAL_RETAIL_STAGES[10]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "human-checkpoint" for f in failures)


def test_missing_planner_separation_fails_stage_10_checklist():
    without_planner = _COMPLIANT_WORKFLOW.replace("planner", "coordinator")
    passed, failures = evaluate_submission(without_planner, GLOBAL_RETAIL_STAGES[10]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "planner-executor-separation" for f in failures)
