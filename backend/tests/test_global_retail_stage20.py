from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_DEMO = (
    "Executive Demo script. Architecture: a five-minute walkthrough of the "
    "context layer, agent layer, and governance stack, aimed at the CIO. "
    "Risk: the failure-engineering and security work already proven "
    "resilient against real induced failures, demonstrated live rather "
    "than shown on a slide. ROI: "
    "the pilot's per-transaction spend now sits under the SKU margin it "
    "used to exceed. Store-level impact: median order-status resolution "
    "time cut for associates helping shoppers in person, framed for Priya "
    "specifically. The last-minute feature ask three hours out gets a "
    "concrete cost estimate on the spot -- not a promise to follow up -- "
    "so both audiences leave with a real number, not a maybe."
)


def test_stage_20_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[20])


def test_stage_20_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[20]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_20_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[20]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_20_persona_relays_both_audiences():
    prompt = GLOBAL_RETAIL_STAGES[20]["persona"]["system_prompt"]
    assert "architecture and risk" in prompt
    assert "store-level impact" in prompt


def test_compliant_demo_passes_stage_20_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_DEMO, GLOBAL_RETAIL_STAGES[20]["compliance_checklist"])
    assert passed, failures


def test_missing_store_level_impact_fails_stage_20_checklist():
    without_impact = _COMPLIANT_DEMO.replace("Store-level impact", "Operational impact")
    passed, failures = evaluate_submission(without_impact, GLOBAL_RETAIL_STAGES[20]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "store-level-impact-covered" for f in failures)


def test_missing_roi_fails_stage_20_checklist():
    without_roi = _COMPLIANT_DEMO.replace("ROI:", "Value:")
    passed, failures = evaluate_submission(without_roi, GLOBAL_RETAIL_STAGES[20]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "roi-covered" for f in failures)


def test_missing_cost_pricing_fails_stage_20_checklist():
    without_cost = _COMPLIANT_DEMO.replace("gets a concrete cost estimate", "gets a concrete answer")
    passed, failures = evaluate_submission(without_cost, GLOBAL_RETAIL_STAGES[20]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "last-minute-cost-priced" for f in failures)
