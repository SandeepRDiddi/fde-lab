import uuid

from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_FRAME = (
    "The leadership complaint ('can't answer questions fast enough') is "
    "only a symptom. The real root cause is fragmented data across SAP and "
    "Salesforce systems that were built independently, with no unified "
    "view of order status. The stakeholders also disagree on who 'the "
    "customer' is: Ops means the store associate helping a shopper in "
    "person, while Customer Service means the shopper calling in directly. "
    "Any success metric has to account for both. Proposed measurable "
    "outcome: cut median order-status resolution time in half within 90 "
    "days, measured separately for in-store and phone-in interactions."
)


def test_stage_1_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[1])


def test_stage_1_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[1]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_1_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[1]["persona"]["system_prompt"]
    assert "ONLY when the FDE specifically" in prompt


def test_stage_1_persona_encodes_both_injected_conflicts():
    prompt = GLOBAL_RETAIL_STAGES[1]["persona"]["system_prompt"]
    assert "contradicts Ops's speed ask" in prompt
    assert "different definition of" in prompt


def test_compliant_problem_frame_passes_stage_1_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_FRAME, GLOBAL_RETAIL_STAGES[1]["compliance_checklist"])
    assert passed, failures


def test_missing_symptom_framing_fails_stage_1_checklist():
    without_symptom = _COMPLIANT_FRAME.replace("is only a symptom", "needs fixing")
    passed, failures = evaluate_submission(without_symptom, GLOBAL_RETAIL_STAGES[1]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "symptom-not-cause" for f in failures)


def test_missing_a_customer_definition_fails_stage_1_checklist():
    without_shopper = _COMPLIANT_FRAME.replace("shopper", "caller")
    passed, failures = evaluate_submission(without_shopper, GLOBAL_RETAIL_STAGES[1]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "customer-definition-shopper" for f in failures)


def test_launching_global_retail_engagement_now_yields_two_stages(client):
    payload = {"cohort_id": str(uuid.uuid4()), "student_id": str(uuid.uuid4())}
    engagement = client.post("/engagements/global-retail", json=payload).json()

    assert len(engagement["stages"]) == 2
    assert engagement["stages"][0]["status"] == "active"
    assert engagement["stages"][1]["status"] == "not_started"
