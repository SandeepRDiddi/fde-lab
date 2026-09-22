from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_PIPELINE = (
    "Production Pipeline: every prompt and model change gets explicit "
    "versioning, so a regression can be traced to the exact version that "
    "introduced it. Policy gate checks (PII redaction rules, RBAC "
    "coverage) run before anything reaches a real environment. The "
    "evaluation harness runs as an automated step on every pull request, "
    "not something a person triggers by hand -- a failing run blocks the "
    "merge outright. The pipeline as a whole refuses to ship anything "
    "that skipped these steps, regardless of who's asking."
)


def test_stage_16_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[16])


def test_stage_16_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[16]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_16_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[16]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_16_persona_rejects_tested_locally_as_a_gate():
    prompt = GLOBAL_RETAIL_STAGES[16]["persona"]["system_prompt"]
    assert "not an acceptable gate" in prompt


def test_compliant_pipeline_passes_stage_16_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_PIPELINE, GLOBAL_RETAIL_STAGES[16]["compliance_checklist"])
    assert passed, failures


def test_missing_policy_gates_fails_stage_16_checklist():
    without_gates = _COMPLIANT_PIPELINE.replace("Policy gate checks", "Compliance checks")
    passed, failures = evaluate_submission(without_gates, GLOBAL_RETAIL_STAGES[16]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "policy-gates" for f in failures)


def test_missing_automated_wiring_fails_stage_16_checklist():
    without_automated = _COMPLIANT_PIPELINE.replace("runs as an automated step", "runs on every pull request")
    passed, failures = evaluate_submission(without_automated, GLOBAL_RETAIL_STAGES[16]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "automated-tests-wired-in" for f in failures)


def test_missing_versioning_fails_stage_16_checklist():
    without_versioning = _COMPLIANT_PIPELINE.replace("versioning", "a change tag")
    passed, failures = evaluate_submission(without_versioning, GLOBAL_RETAIL_STAGES[16]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "prompt-model-versioning" for f in failures)
