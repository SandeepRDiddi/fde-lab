from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_DEPLOYMENT = (
    "Deployment plan: every component -- the backend API, the persona/"
    "agent service, and the data layer -- gets its own container image, "
    "built and pushed by the Stage 16 pipeline itself, not run by hand "
    "from a laptop. The target is a production-like cloud environment "
    "with real networking and secrets management, not a local dev "
    "compose setup. Rollout goes through the pipeline's existing gates "
    "end to end, so what ships is exactly what evaluation already passed."
)


def test_stage_17_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[17])


def test_stage_17_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[17]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_17_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[17]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_17_persona_insists_on_pipeline_deploy_not_manual():
    prompt = GLOBAL_RETAIL_STAGES[17]["persona"]["system_prompt"]
    assert "not a manual deploy step" in prompt


def test_compliant_deployment_passes_stage_17_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_DEPLOYMENT, GLOBAL_RETAIL_STAGES[17]["compliance_checklist"])
    assert passed, failures


def test_missing_container_fails_stage_17_checklist():
    without_container = _COMPLIANT_DEPLOYMENT.replace("container image", "deployable image")
    passed, failures = evaluate_submission(without_container, GLOBAL_RETAIL_STAGES[17]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "containerized" for f in failures)


def test_missing_production_framing_fails_stage_17_checklist():
    without_production = _COMPLIANT_DEPLOYMENT.replace("production-like", "realistic")
    passed, failures = evaluate_submission(without_production, GLOBAL_RETAIL_STAGES[17]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "production-like-environment" for f in failures)


def test_missing_agent_component_fails_stage_17_checklist():
    without_agent = _COMPLIANT_DEPLOYMENT.replace("persona/agent service", "persona service")
    passed, failures = evaluate_submission(without_agent, GLOBAL_RETAIL_STAGES[17]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "agent-component" for f in failures)
