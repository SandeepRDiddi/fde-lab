import io
import json
import uuid

from app.compliance import evaluate_submission
from app.engagement_content.global_retail import GLOBAL_RETAIL_STAGES
from app.schemas import EngagementStageCreate

_COMPLIANT_PACK = (
    "Production Handover Pack. Runbook: a step-by-step guide covering "
    "every operational procedure someone who wasn't here could follow "
    "cold, from restart to rollback. Architecture: a full write-up of "
    "context layer, agent layer, and governance stack that assumes zero "
    "prior context. Support model: who gets paged, when, and how "
    "escalation actually works day to day. The 90-day backlog lists the "
    "next concrete priorities so the platform team isn't starting from "
    "zero on what comes after this handover."
)


def test_stage_21_config_validates_as_engagement_stage():
    EngagementStageCreate(config=GLOBAL_RETAIL_STAGES[21])


def test_stage_21_has_no_technical_task_or_dataset():
    stage = GLOBAL_RETAIL_STAGES[21]
    assert "technical_task" not in stage
    assert "data_gen" not in stage


def test_stage_21_persona_does_not_dump_facts_unprompted():
    prompt = GLOBAL_RETAIL_STAGES[21]["persona"]["system_prompt"]
    assert "ONLY when specifically asked" in prompt


def test_stage_21_persona_confirms_no_fde_on_call_after_this():
    prompt = GLOBAL_RETAIL_STAGES[21]["persona"]["system_prompt"]
    assert "there's no FDE on call after this" in prompt


def test_compliant_pack_passes_stage_21_checklist():
    passed, failures = evaluate_submission(_COMPLIANT_PACK, GLOBAL_RETAIL_STAGES[21]["compliance_checklist"])
    assert passed, failures


def test_missing_runbook_fails_stage_21_checklist():
    without_runbook = _COMPLIANT_PACK.replace("Runbook:", "Operating notes:")
    passed, failures = evaluate_submission(without_runbook, GLOBAL_RETAIL_STAGES[21]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "runbook-included" for f in failures)


def test_missing_support_model_fails_stage_21_checklist():
    without_support = _COMPLIANT_PACK.replace("Support model:", "On-call plan:")
    passed, failures = evaluate_submission(without_support, GLOBAL_RETAIL_STAGES[21]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "support-model-defined" for f in failures)


def test_missing_backlog_fails_stage_21_checklist():
    without_backlog = _COMPLIANT_PACK.replace("90-day backlog", "roadmap")
    passed, failures = evaluate_submission(without_backlog, GLOBAL_RETAIL_STAGES[21]["compliance_checklist"])
    assert not passed
    assert any(f["rule_id"] == "backlog-defined" for f in failures)


# --- End-to-end: all 22 stages, approved in order ---------------------------


class _FakeBody:
    def __init__(self, data: bytes):
        self._buf = io.BytesIO(data)

    def read(self):
        return self._buf.read()


class _FakeS3Client:
    def __init__(self, objects: dict[str, bytes]):
        self._objects = objects

    def get_object(self, *, Bucket, Key):
        return {"Body": _FakeBody(self._objects[f"{Bucket}/{Key}"])}


def _generic_compliant_content(compliance_checklist: list[dict]) -> str:
    """Builds content that satisfies an arbitrary compliance_checklist by
    construction -- one plain, negation-free sentence per must_include
    rule, padded to clear any min_length rule. Used here so this
    end-to-end test doesn't hand-duplicate every stage's own hand-crafted
    fixture (already covered individually by each stage's own test file)."""
    parts = [f"This deliverable directly addresses {rule['value']}." for rule in compliance_checklist if rule["check"] == "must_include"]
    content = " ".join(parts)
    min_length = next((rule["value"] for rule in compliance_checklist if rule["check"] == "min_length"), 0)
    while len(content) < min_length:
        content += " Additional supporting detail is included here to meet the length requirement."
    return content


def test_full_22_stage_engagement_completes_end_to_end(client, monkeypatch):
    payload = {"cohort_id": str(uuid.uuid4()), "student_id": str(uuid.uuid4())}
    engagement = client.post("/engagements/global-retail", json=payload).json()
    assert len(engagement["stages"]) == 22

    body = "\n".join(
        json.dumps({"order_id": f"ORD-{i}", "customer_email": None if i % 3 == 0 else f"c{i}@example.com"})
        for i in range(20)
    ).encode("utf-8")

    for stage_order in range(22):
        fetched = client.get(f"/engagements/{engagement['id']}").json()
        stage = fetched["stages"][stage_order]
        assert stage["status"] == "active", f"stage {stage_order} not active"

        # The API redacts technical_task answer-key fields (reference_query)
        # from every response (app/routers/scenario_instances.py's
        # _redact_technical_task) -- read the unredacted authored content
        # straight from GLOBAL_RETAIL_STAGES instead, same as an instructor
        # authoring the scenario would have it, not as a student would see it.
        authored_config = GLOBAL_RETAIL_STAGES[stage_order]
        technical_task = authored_config.get("technical_task")
        if technical_task:
            # Stage 3: real grading via a fake S3-backed dataset (same
            # pattern as test_global_retail_stage3.py).
            dataset_location = f"s3://fde-lab-datasets/instances/{stage['id']}/orders.ndjson"
            client.patch(f"/scenario-instances/{stage['id']}/dataset", json={"dataset_location": dataset_location})
            fake_client = _FakeS3Client({f"fde-lab-datasets/instances/{stage['id']}/orders.ndjson": body})
            monkeypatch.setattr("app.dataset_store.boto3.client", lambda *a, **kw: fake_client)
            content = technical_task["reference_query"]
        else:
            content = _generic_compliant_content(authored_config.get("compliance_checklist") or [])

        submission = client.post(f"/scenario-instances/{stage['id']}/submissions", json={"content": content})
        assert submission.status_code == 201, (stage_order, submission.text)
        submission_id = submission.json()["id"]

        decided = client.patch(
            f"/scenario-instances/{stage['id']}/submissions/{submission_id}/decision",
            json={"decision": "approved"},
        )
        assert decided.status_code == 200, (stage_order, decided.text)

    final = client.get(f"/engagements/{engagement['id']}").json()
    assert final["status"] == "completed"
    assert final["completed_at"] is not None
    assert set(final["context"].keys()) == {str(i) for i in range(22)}
    assert all(stage["status"] == "active" for stage in final["stages"])
