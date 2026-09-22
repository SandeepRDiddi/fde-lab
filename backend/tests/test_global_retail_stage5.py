from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_ADRS = (
    "ADR-1: Delay root-cause investigation will use RAG over the order/"
    "inventory/supplier data -- retrieval-augmented synthesis with a human "
    "still deciding, matching the AI-assisted classification. ADR-2: "
    "Supplier escalation will use an agentic workflow -- a planner/"
    "executor loop checking status, inventory, and supplier ETA before "
    "deciding whether to escalate, with a human checkpoint. ADR-3: "
    "return-eligibility stays fully deterministic -- it is explicitly "
    "excluded from any AI architecture given the legal constraint "
    "established earlier. All three decisions fit within the $400K "
    "budget: RAG and the agentic workflow share infrastructure, keeping "
    "cost proportional to what each use case actually needs rather than "
    "buying one expensive autonomous platform for everything."
)


def test_stage_5_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[5])


def test_stage_5_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[5]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_5_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[5]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_5_persona_references_three_failed_vendor_pitches():
    prompt = GLOBAL_RETAIL_STAGES[5]["persona"]["system_prompt"]
    assert "chatbot" in prompt
    assert "RAG search tool" in prompt
    assert "fully autonomous agent" in prompt


def test_compliant_adrs_pass_stage_5_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_ADRS, GLOBAL_RETAIL_STAGES[5]["compliance_checklist"])
    assert passed, failures


def test_missing_rag_choice_fails_stage_5_checklist():
    without_rag = _COMPLIANT_ADRS.replace("RAG", "a search tool")
    passed, failures = evaluate_submission(without_rag, GLOBAL_RETAIL_STAGES[5]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "chose-rag-for-investigation" for f in failures)


def test_missing_return_eligibility_exclusion_fails_stage_5_checklist():
    without_exclusion = _COMPLIANT_ADRS.replace("return-eligibility", "returns")
    passed, failures = evaluate_submission(without_exclusion, GLOBAL_RETAIL_STAGES[5]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "excludes-return-eligibility" for f in failures)


def test_missing_budget_framing_fails_stage_5_checklist():
    without_budget = _COMPLIANT_ADRS.replace("budget", "cost ceiling")
    passed, failures = evaluate_submission(without_budget, GLOBAL_RETAIL_STAGES[5]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "respects-budget" for f in failures)
