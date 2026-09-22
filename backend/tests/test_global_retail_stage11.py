from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_MATRIX = (
    "Security Control Matrix. RBAC covers three tiers: frontline store "
    "associates get order-status read access only, operations staff get "
    "broader operational data, executives get aggregate reporting -- none "
    "share a role. PII redaction runs on every retrieved document before "
    "it reaches the model, catching cases like the supplier contract PDF "
    "that had an employee's personal details buried in it and was never "
    "flagged before. For the escalation workflow, since the first-choice "
    "tool is blocked outright, the proposal names an approved alternative "
    "that already clears the access-control bar rather than appealing the "
    "decision."
)


def test_stage_11_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[11])


def test_stage_11_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[11]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_11_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[11]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_11_persona_references_stage3_supplier_pdf_gap():
    prompt = GLOBAL_RETAIL_STAGES[11]["persona"]["system_prompt"]
    assert "unindexed supplier contract PDFs" in prompt


def test_compliant_matrix_passes_stage_11_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_MATRIX, GLOBAL_RETAIL_STAGES[11]["compliance_checklist"])
    assert passed, failures


def test_missing_rbac_fails_stage_11_checklist():
    without_rbac = _COMPLIANT_MATRIX.replace("RBAC covers", "Access control covers")
    passed, failures = evaluate_submission(without_rbac, GLOBAL_RETAIL_STAGES[11]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "rbac-proposed" for f in failures)


def test_missing_approved_alternative_fails_stage_11_checklist():
    without_alt = _COMPLIANT_MATRIX.replace("an approved alternative", "a different tool")
    passed, failures = evaluate_submission(without_alt, GLOBAL_RETAIL_STAGES[11]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "approved-alternative" for f in failures)


def test_missing_supplier_contract_reference_fails_stage_11_checklist():
    without_reference = _COMPLIANT_MATRIX.replace("supplier contract PDF", "internal document")
    passed, failures = evaluate_submission(without_reference, GLOBAL_RETAIL_STAGES[11]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "supplier-contract-finding" for f in failures)
