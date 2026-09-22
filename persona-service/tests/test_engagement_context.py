import uuid


def _persona_config(engagement_context=None):
    config = {
        "persona": {
            "system_prompt": "You are Dana, VP of Finance. Skeptical, terse, hates vague asks.",
            "agenda": "Cut Q3 budget by 10% without headcount",
        }
    }
    if engagement_context is not None:
        config["engagement_context"] = engagement_context
    return config


def test_engagement_context_renders_into_system_prompt(client, seed_scenario_instance, fake_gateway):
    scenario_id = uuid.uuid4()
    student_id = uuid.uuid4()
    seed_scenario_instance(
        scenario_id,
        _persona_config(
            engagement_context={
                "0": {"submission_content": "Reports to Marcus Chen.", "grading_result": None},
            }
        ),
    )

    client.post(
        f"/scenario-instances/{scenario_id}/messages",
        json={"student_id": str(student_id), "message": "What did I already establish?"},
    )

    call = fake_gateway.calls[0]
    assert "Context from earlier stages" in call["system_prompt"]
    assert "Stage 0: Reports to Marcus Chen." in call["system_prompt"]
    # Persona's own system prompt/agenda still present, unaffected.
    assert "Dana, VP of Finance" in call["system_prompt"]
    assert "Cut Q3 budget by 10%" in call["system_prompt"]


def test_absent_engagement_context_changes_nothing(client, seed_scenario_instance, fake_gateway):
    scenario_id = uuid.uuid4()
    student_id = uuid.uuid4()
    seed_scenario_instance(scenario_id, _persona_config(engagement_context=None))

    client.post(
        f"/scenario-instances/{scenario_id}/messages",
        json={"student_id": str(student_id), "message": "Hello"},
    )

    call = fake_gateway.calls[0]
    assert "Context from earlier stages" not in call["system_prompt"]


def test_empty_engagement_context_changes_nothing(client, seed_scenario_instance, fake_gateway):
    scenario_id = uuid.uuid4()
    student_id = uuid.uuid4()
    seed_scenario_instance(scenario_id, _persona_config(engagement_context={}))

    client.post(
        f"/scenario-instances/{scenario_id}/messages",
        json={"student_id": str(student_id), "message": "Hello"},
    )

    call = fake_gateway.calls[0]
    assert "Context from earlier stages" not in call["system_prompt"]


def test_engagement_context_ordered_by_stage_number_not_insertion_order(client, seed_scenario_instance, fake_gateway):
    scenario_id = uuid.uuid4()
    student_id = uuid.uuid4()
    # Intentionally inserted out of numeric order (dict preserves insertion
    # order; "10" sorts before "2" lexicographically) to prove the render is
    # sorted numerically, not lexicographically or by insertion.
    seed_scenario_instance(
        scenario_id,
        _persona_config(
            engagement_context={
                "10": {"submission_content": "tenth stage output", "grading_result": None},
                "2": {"submission_content": "second stage output", "grading_result": None},
                "1": {"submission_content": "first stage output", "grading_result": None},
            }
        ),
    )

    client.post(
        f"/scenario-instances/{scenario_id}/messages",
        json={"student_id": str(student_id), "message": "Hello"},
    )

    prompt = fake_gateway.calls[0]["system_prompt"]
    assert prompt.index("Stage 1:") < prompt.index("Stage 2:") < prompt.index("Stage 10:")
