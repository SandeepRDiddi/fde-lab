import uuid


def _create_engagement(client, stage_configs):
    payload = {
        "cohort_id": str(uuid.uuid4()),
        "student_id": str(uuid.uuid4()),
        "stages": [{"config": config} for config in stage_configs],
    }
    response = client.post("/engagements", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _submit_and_approve(client, instance_id, content="my deliverable"):
    submission = client.post(
        f"/scenario-instances/{instance_id}/submissions", json={"content": content}
    ).json()
    decided = client.patch(
        f"/scenario-instances/{instance_id}/submissions/{submission['id']}/decision",
        json={"decision": "approved"},
    )
    assert decided.status_code == 200, decided.text
    return decided.json()


def test_create_engagement_unlocks_only_first_stage(client):
    engagement = _create_engagement(client, [{"a": 1}, {"b": 2}, {"c": 3}])

    assert engagement["status"] == "active"
    assert engagement["context"] == {}
    stages = engagement["stages"]
    assert len(stages) == 3
    assert [s["stage_order"] for s in stages] == [0, 1, 2]
    assert stages[0]["status"] == "active"
    assert stages[1]["status"] == "not_started"
    assert stages[2]["status"] == "not_started"
    assert all(s["engagement_id"] == engagement["id"] for s in stages)


def test_approving_a_stage_unlocks_the_next_and_carries_context(client):
    engagement = _create_engagement(client, [{}, {}])
    stage0_id = engagement["stages"][0]["id"]

    _submit_and_approve(client, stage0_id, content="stage 0 output")

    fetched = client.get(f"/engagements/{engagement['id']}").json()
    stage1 = fetched["stages"][1]
    assert stage1["status"] == "active"
    assert stage1["config"]["engagement_context"]["0"]["submission_content"] == "stage 0 output"
    assert fetched["status"] == "active"


def test_rejecting_a_stage_does_not_unlock_the_next(client):
    engagement = _create_engagement(client, [{}, {}])
    stage0_id = engagement["stages"][0]["id"]

    submission = client.post(
        f"/scenario-instances/{stage0_id}/submissions", json={"content": "not good enough"}
    ).json()
    client.patch(
        f"/scenario-instances/{stage0_id}/submissions/{submission['id']}/decision",
        json={"decision": "rejected"},
    )

    fetched = client.get(f"/engagements/{engagement['id']}").json()
    assert fetched["stages"][1]["status"] == "not_started"
    assert fetched["status"] == "active"

    # Resubmission on the same (still-open) stage still works.
    resubmit = client.post(
        f"/scenario-instances/{stage0_id}/submissions", json={"content": "better this time"}
    )
    assert resubmit.status_code == 201


def test_approving_last_stage_completes_the_engagement(client):
    engagement = _create_engagement(client, [{}])
    stage0_id = engagement["stages"][0]["id"]

    _submit_and_approve(client, stage0_id)

    fetched = client.get(f"/engagements/{engagement['id']}").json()
    assert fetched["status"] == "completed"
    assert fetched["completed_at"] is not None


def test_context_accumulates_additively_across_three_stages(client):
    engagement = _create_engagement(client, [{}, {}, {}])
    stages = engagement["stages"]

    _submit_and_approve(client, stages[0]["id"], content="output A")
    fetched = client.get(f"/engagements/{engagement['id']}").json()
    stage1_id = fetched["stages"][1]["id"]
    assert fetched["stages"][1]["config"]["engagement_context"] == {
        "0": {"submission_content": "output A", "grading_result": None}
    }

    _submit_and_approve(client, stage1_id, content="output B")
    fetched = client.get(f"/engagements/{engagement['id']}").json()
    stage2 = fetched["stages"][2]
    assert stage2["config"]["engagement_context"]["0"]["submission_content"] == "output A"
    assert stage2["config"]["engagement_context"]["1"]["submission_content"] == "output B"
    assert fetched["status"] == "active"

    _submit_and_approve(client, stage2["id"], content="output C")
    fetched = client.get(f"/engagements/{engagement['id']}").json()
    assert fetched["status"] == "completed"
    assert set(fetched["context"].keys()) == {"0", "1", "2"}


def test_standalone_scenario_instance_is_unaffected(client):
    """FDE-017 AC5: an instance with no engagement_id behaves exactly as
    before -- approval doesn't try to advance anything."""
    instance = client.post(
        "/scenario-instances",
        json={"cohort_id": str(uuid.uuid4()), "student_id": str(uuid.uuid4()), "config": {}},
    ).json()
    assert instance["engagement_id"] is None
    assert instance["stage_order"] is None

    decided = _submit_and_approve(client, instance["id"])
    assert decided["status"] == "approved"


def test_create_engagement_requires_at_least_one_stage(client):
    response = client.post(
        "/engagements",
        json={"cohort_id": str(uuid.uuid4()), "student_id": str(uuid.uuid4()), "stages": []},
    )
    assert response.status_code == 422
