from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_DASHBOARD = (
    "Unit Economics Dashboard, built from six weeks of pilot usage data. "
    "Cost attribution breaks every transaction down by model, tool call, "
    "and token count, so a spike is traceable to its source instead of "
    "showing up as one opaque total. Model routing sends simple "
    "order-status lookups to a cheaper model instead of the same "
    "heavyweight model used for complex investigations. Caching answers "
    "repeat questions about the same order without a fresh model call "
    "every time. A per-transaction budget alert fires before a single "
    "question's cost can exceed the margin on the order it's about -- the "
    "exact gap Finance flagged."
)


def test_stage_15_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[15])


def test_stage_15_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[15]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_15_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[15]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_15_persona_states_the_margin_gap():
    prompt = GLOBAL_RETAIL_STAGES[15]["persona"]["system_prompt"]
    assert "costing more, per transaction, than the margin" in prompt


def test_compliant_dashboard_passes_stage_15_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_DASHBOARD, GLOBAL_RETAIL_STAGES[15]["compliance_checklist"])
    assert passed, failures


def test_missing_model_routing_fails_stage_15_checklist():
    without_routing = _COMPLIANT_DASHBOARD.replace("Model routing sends", "The system sends")
    passed, failures = evaluate_submission(without_routing, GLOBAL_RETAIL_STAGES[15]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "model-routing" for f in failures)


def test_missing_caching_fails_stage_15_checklist():
    without_caching = _COMPLIANT_DASHBOARD.replace("Caching answers", "The system answers")
    passed, failures = evaluate_submission(without_caching, GLOBAL_RETAIL_STAGES[15]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "caching" for f in failures)


def test_missing_margin_framing_fails_stage_15_checklist():
    without_margin = _COMPLIANT_DASHBOARD.replace("margin", "target")
    passed, failures = evaluate_submission(without_margin, GLOBAL_RETAIL_STAGES[15]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "margin-gap-addressed" for f in failures)
