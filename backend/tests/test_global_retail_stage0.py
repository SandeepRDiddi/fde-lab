import uuid

from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_BRIEF = (
    "Per my conversation with Dana, I report to Marcus Chen, VP of "
    "Engineering, for the duration of this engagement. The two stakeholders "
    "who matter most day to day are Priya Anand (VP of Operations, focused "
    "on store-level speed) and Jordan Lee (Director of IT, focused on data "
    "governance and access control). Explicitly out of scope: replacing the "
    "core POS system -- leadership will not authorize touching it given "
    "past scope creep. I'll keep this boundary in mind as I scope the rest "
    "of the engagement."
)


def test_stage_0_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[0])


def test_stage_0_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[0]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_0_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[0]["persona"]["system_prompt"]
    assert "ONLY when the FDE specifically asks" in prompt or "do not volunteer" in prompt.lower()


def _create_global_retail_engagement(client):
    payload = {"cohort_id": str(uuid.uuid4()), "student_id": str(uuid.uuid4())}
    response = client.post("/engagements/global-retail", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_launching_global_retail_engagement_activates_stage_0(client):
    engagement = _create_global_retail_engagement(client)
    assert engagement["status"] == "active"
    assert len(engagement["stages"]) == len(GLOBAL_RETAIL_STAGES)
    assert engagement["stages"][0]["status"] == "active"
    assert engagement["stages"][0]["config"]["persona"]["agenda"]


def test_compliant_brief_passes_stage_0_checklist(client):
    engagement = _create_global_retail_engagement(client)
    stage0_id = engagement["stages"][0]["id"]

    response = client.post(
        f"/scenario-instances/{stage0_id}/submissions", json={"content": _COMPLIANT_BRIEF}
    )
    assert response.status_code == 201, response.text


def test_brief_missing_a_required_element_fails_stage_0_checklist():
    from app.compliance import evaluate_submission

    missing_scope = _COMPLIANT_BRIEF.replace(
        "Explicitly out of scope: replacing the core POS system -- "
        "leadership will not authorize touching it given past scope creep. ",
        "",
    )
    passed, failures = evaluate_submission(missing_scope, GLOBAL_RETAIL_STAGES[0]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "out-of-scope" for f in failures)


def test_brief_missing_a_stakeholder_fails_stage_0_checklist():
    from app.compliance import evaluate_submission

    missing_stakeholder = _COMPLIANT_BRIEF.replace("Jordan Lee", "the IT lead")
    passed, failures = evaluate_submission(
        missing_stakeholder, GLOBAL_RETAIL_STAGES[0]["compliance_checklist"]
    )
    assert not passed
    assert any(f["rule_id"] == "stakeholder-it" for f in failures)
