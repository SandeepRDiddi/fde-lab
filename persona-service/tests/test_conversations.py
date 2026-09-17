import uuid


def _persona_config(agenda="Cut Q3 budget by 10% without headcount"):
    return {
        "persona": {
            "system_prompt": "You are Dana, VP of Finance. Skeptical, terse, hates vague asks.",
            "agenda": agenda,
        }
    }


def test_send_message_uses_persona_system_prompt(client, seed_scenario_instance, fake_gateway):
    scenario_id = uuid.uuid4()
    student_id = uuid.uuid4()
    seed_scenario_instance(scenario_id, _persona_config())

    response = client.post(
        f"/scenario-instances/{scenario_id}/messages",
        json={"student_id": str(student_id), "message": "What's the top priority this quarter?"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "persona"
    assert body["content"] == "[persona reply #1]"

    assert len(fake_gateway.calls) == 1
    call = fake_gateway.calls[0]
    assert "Dana, VP of Finance" in call["system_prompt"]
    assert "Cut Q3 budget by 10%" in call["system_prompt"]
    assert call["messages"] == [{"role": "user", "content": "What's the top priority this quarter?"}]


def test_send_message_without_persona_config_is_rejected(client, seed_scenario_instance):
    scenario_id = uuid.uuid4()
    seed_scenario_instance(scenario_id, {})

    response = client.post(
        f"/scenario-instances/{scenario_id}/messages",
        json={"student_id": str(uuid.uuid4()), "message": "Hello?"},
    )

    assert response.status_code == 400


def test_send_message_unknown_scenario_instance_404s(client):
    response = client.post(
        f"/scenario-instances/{uuid.uuid4()}/messages",
        json={"student_id": str(uuid.uuid4()), "message": "Hello?"},
    )

    assert response.status_code == 404


def test_conversation_history_persists_across_turns(client, seed_scenario_instance):
    scenario_id = uuid.uuid4()
    student_id = uuid.uuid4()
    seed_scenario_instance(scenario_id, _persona_config())

    client.post(
        f"/scenario-instances/{scenario_id}/messages",
        json={"student_id": str(student_id), "message": "First question"},
    )
    client.post(
        f"/scenario-instances/{scenario_id}/messages",
        json={"student_id": str(student_id), "message": "Second question"},
    )

    response = client.get(f"/scenario-instances/{scenario_id}/messages", params={"student_id": str(student_id)})

    assert response.status_code == 200
    body = response.json()
    contents = [m["content"] for m in body["messages"]]
    assert contents == [
        "First question",
        "[persona reply #1]",
        "Second question",
        "[persona reply #2]",
    ]


def test_conversation_is_scoped_per_student(client, seed_scenario_instance):
    scenario_id = uuid.uuid4()
    student_a = uuid.uuid4()
    student_b = uuid.uuid4()
    seed_scenario_instance(scenario_id, _persona_config())

    client.post(
        f"/scenario-instances/{scenario_id}/messages",
        json={"student_id": str(student_a), "message": "From student A"},
    )

    response = client.get(f"/scenario-instances/{scenario_id}/messages", params={"student_id": str(student_b)})

    assert response.status_code == 200
    assert response.json()["messages"] == []


def test_pivot_updates_agenda_without_resetting_conversation(client, seed_scenario_instance, fake_gateway):
    scenario_id = uuid.uuid4()
    student_id = uuid.uuid4()
    seed_scenario_instance(scenario_id, _persona_config(agenda="Original agenda: cut budget"))

    client.post(
        f"/scenario-instances/{scenario_id}/messages",
        json={"student_id": str(student_id), "message": "What matters most?"},
    )

    pivot_response = client.post(
        f"/scenario-instances/{scenario_id}/persona/pivot",
        json={"agenda": "New agenda: freeze the budget cut, prioritize retention instead"},
    )
    assert pivot_response.status_code == 204

    client.post(
        f"/scenario-instances/{scenario_id}/messages",
        json={"student_id": str(student_id), "message": "Has anything changed?"},
    )

    assert len(fake_gateway.calls) == 2
    assert "Original agenda" in fake_gateway.calls[0]["system_prompt"]
    assert "New agenda: freeze the budget cut" in fake_gateway.calls[1]["system_prompt"]

    # History accumulated across the pivot instead of restarting.
    second_call_messages = fake_gateway.calls[1]["messages"]
    assert [m["content"] for m in second_call_messages] == [
        "What matters most?",
        "[persona reply #1]",
        "Has anything changed?",
    ]

    history = client.get(
        f"/scenario-instances/{scenario_id}/messages", params={"student_id": str(student_id)}
    ).json()["messages"]
    assert len(history) == 4
