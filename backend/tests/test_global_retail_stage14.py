from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_HARNESS = (
    "Evaluation Harness, run against the held-out anonymized ticket set. "
    "Functional evaluation checks each tool call returns the right shape "
    "of answer for a known ticket. Agent-behavior evaluation replays "
    "multi-step investigations and checks the agent reaches the right "
    "escalate/don't-escalate decision, not just the right final sentence. "
    "RAG-accuracy evaluation scores retrieved passages against the "
    "held-out tickets' known-correct answers. Adversarial evaluation runs "
    "security's supplied prompts specifically to catch injection and "
    "access-boundary attempts. Regression evaluation reruns every prior "
    "case on each change so a fix in one area is confirmed not to break "
    "another."
)


def test_stage_14_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[14])


def test_stage_14_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[14]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_14_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[14]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_14_persona_states_the_real_readiness_bar():
    prompt = GLOBAL_RETAIL_STAGES[14]["persona"]["system_prompt"]
    assert "1,200 stores" in prompt


def test_compliant_harness_passes_stage_14_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_HARNESS, GLOBAL_RETAIL_STAGES[14]["compliance_checklist"])
    assert passed, failures


def test_missing_agent_behavior_eval_fails_stage_14_checklist():
    without_agent_behavior = _COMPLIANT_HARNESS.replace("Agent-behavior evaluation", "Workflow evaluation")
    passed, failures = evaluate_submission(without_agent_behavior, GLOBAL_RETAIL_STAGES[14]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "agent-behavior-eval" for f in failures)


def test_missing_adversarial_eval_fails_stage_14_checklist():
    without_adversarial = _COMPLIANT_HARNESS.replace("Adversarial evaluation", "Security evaluation")
    passed, failures = evaluate_submission(without_adversarial, GLOBAL_RETAIL_STAGES[14]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "adversarial-security-eval" for f in failures)


def test_missing_regression_eval_fails_stage_14_checklist():
    without_regression = _COMPLIANT_HARNESS.replace("Regression evaluation", "Change-safety evaluation")
    passed, failures = evaluate_submission(without_regression, GLOBAL_RETAIL_STAGES[14]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "regression-eval" for f in failures)
