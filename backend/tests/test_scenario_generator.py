import json

import pytest

from app import scenario_generator as gen
from app.scenario_generator import GeneratorError, generate_scenario_config

VALID_DRAFT = {
    "persona": {
        "system_prompt": "You are Priya, VP of Ops. Terse, stressed about a deadline.",
        "agenda": "Get the duplicate-order issue fixed before EOD.",
    },
    "data_gen": {"domain": "ecommerce_orders", "messiness": "medium"},
    "technical_task": {
        "instructions": "Return one row per order_id.",
        "reference_query": "SELECT DISTINCT order_id, customer_email FROM orders",
    },
    "legacy_system": "acme-crm",
}


def _canned(*responses):
    calls = iter(responses)

    def fake(_prompt, *, client=None):
        return next(calls)

    return fake


def test_generate_returns_valid_config_on_first_attempt(monkeypatch):
    monkeypatch.setattr(gen, "_call_model_backend", _canned(json.dumps(VALID_DRAFT)))

    config = generate_scenario_config("Client's nightly sync keeps duplicating orders.")

    assert config["persona"]["agenda"] == VALID_DRAFT["persona"]["agenda"]
    assert config["data_gen"] == {"domain": "ecommerce_orders", "messiness": "medium"}
    assert config["technical_task"]["task_type"] == "sql_query"
    assert config["technical_task"]["table_name"] == "orders"
    assert config["technical_task"]["reference_query"] == VALID_DRAFT["technical_task"]["reference_query"]
    assert "compliance_checklist" not in config
    assert config["legacy_system"]["scenario_id"] == "acme-crm"
    assert config["legacy_system"]["auth_header_name"] == "X-Legacy-Auth"


def test_generate_strips_markdown_code_fences(monkeypatch):
    fenced = "Here you go:\n```json\n" + json.dumps(VALID_DRAFT) + "\n```"
    monkeypatch.setattr(gen, "_call_model_backend", _canned(fenced))

    config = generate_scenario_config("anything")

    assert config["technical_task"]["reference_query"] == VALID_DRAFT["technical_task"]["reference_query"]


def test_generate_retries_on_invalid_json_then_succeeds(monkeypatch):
    monkeypatch.setattr(gen, "_call_model_backend", _canned("not json at all", json.dumps(VALID_DRAFT)))

    config = generate_scenario_config("anything")

    assert config["data_gen"]["domain"] == "ecommerce_orders"


def test_generate_retries_on_unknown_domain_then_succeeds(monkeypatch):
    bad = {**VALID_DRAFT, "data_gen": {"domain": "made_up_domain", "messiness": "low"}}
    monkeypatch.setattr(gen, "_call_model_backend", _canned(json.dumps(bad), json.dumps(VALID_DRAFT)))

    config = generate_scenario_config("anything")

    assert config["data_gen"]["domain"] == "ecommerce_orders"


def test_generate_retries_on_reference_query_hallucinated_column(monkeypatch):
    bad = {
        **VALID_DRAFT,
        "technical_task": {**VALID_DRAFT["technical_task"], "reference_query": "SELECT nonexistent_column FROM orders"},
    }
    monkeypatch.setattr(gen, "_call_model_backend", _canned(json.dumps(bad), json.dumps(VALID_DRAFT)))

    config = generate_scenario_config("anything")

    assert "nonexistent_column" not in config["technical_task"]["reference_query"]


def test_generate_retries_on_non_select_reference_query(monkeypatch):
    bad = {**VALID_DRAFT, "technical_task": {**VALID_DRAFT["technical_task"], "reference_query": "DELETE FROM orders"}}
    monkeypatch.setattr(gen, "_call_model_backend", _canned(json.dumps(bad), json.dumps(VALID_DRAFT)))

    config = generate_scenario_config("anything")

    assert config["technical_task"]["reference_query"].lower().startswith("select")


def test_generate_retries_when_dedup_instructions_but_query_does_not_dedup(monkeypatch):
    # Caught live against the real model: instructions described removing
    # duplicate order records, but the reference_query was just a column
    # projection with no DISTINCT/GROUP BY -- syntactically fine, executes
    # fine, but doesn't actually resolve what it claims to.
    bad = {
        **VALID_DRAFT,
        "technical_task": {
            "instructions": "Write a query to remove the duplicate order records.",
            "reference_query": "SELECT order_id, customer_email FROM orders",
        },
    }
    monkeypatch.setattr(gen, "_call_model_backend", _canned(json.dumps(bad), json.dumps(VALID_DRAFT)))

    config = generate_scenario_config("anything")

    assert "distinct" in config["technical_task"]["reference_query"].lower()


def test_generate_retries_when_query_references_domain_name_instead_of_table(monkeypatch):
    # Caught live against the real model: it's told the table is named
    # "orders" but sometimes queries "FROM ecommerce_orders" (the domain
    # name) instead -- the model's own two fields disagreeing with each
    # other. technical_task.table_name isn't taken from the model at all
    # any more (see TABLE_NAMES), so this can only show up as an execution
    # failure against the fixed table name, same as any other bad query.
    bad = {
        **VALID_DRAFT,
        "technical_task": {
            "instructions": "Return one row per order_id.",
            "reference_query": "SELECT DISTINCT order_id, customer_email FROM ecommerce_orders",
        },
    }
    monkeypatch.setattr(gen, "_call_model_backend", _canned(json.dumps(bad), json.dumps(VALID_DRAFT)))

    config = generate_scenario_config("anything")

    assert config["technical_task"]["table_name"] == "orders"
    assert "FROM orders" in config["technical_task"]["reference_query"]


def test_generate_raises_after_two_failed_attempts(monkeypatch):
    monkeypatch.setattr(gen, "_call_model_backend", _canned("garbage", "still garbage"))

    with pytest.raises(GeneratorError):
        generate_scenario_config("anything")


def test_generate_defaults_invalid_messiness_to_medium(monkeypatch):
    draft = {**VALID_DRAFT, "data_gen": {"domain": "ecommerce_orders", "messiness": "extreme"}}
    monkeypatch.setattr(gen, "_call_model_backend", _canned(json.dumps(draft)))

    config = generate_scenario_config("anything")

    assert config["data_gen"]["messiness"] == "medium"


def test_generate_never_emits_compliance_checklist_even_if_model_adds_one(monkeypatch):
    # A submission's whole content is the SQL query -- a prose rule on that
    # same field could never be jointly satisfiable with a working query, so
    # the generator drops it even if an older/confused model output includes
    # one anyway.
    draft = {
        **VALID_DRAFT,
        "compliance_checklist": [
            {"id": "ok", "description": "fine", "check": "must_include", "value": "rollback"}
        ],
    }
    monkeypatch.setattr(gen, "_call_model_backend", _canned(json.dumps(draft)))

    config = generate_scenario_config("anything")

    assert "compliance_checklist" not in config


def test_generate_legacy_system_none_when_unrecognized(monkeypatch):
    draft = {**VALID_DRAFT, "legacy_system": "some_made_up_system"}
    monkeypatch.setattr(gen, "_call_model_backend", _canned(json.dumps(draft)))

    config = generate_scenario_config("anything")

    assert "legacy_system" not in config


def test_generate_legacy_system_omitted_when_none(monkeypatch):
    draft = {**VALID_DRAFT, "legacy_system": "none"}
    monkeypatch.setattr(gen, "_call_model_backend", _canned(json.dumps(draft)))

    config = generate_scenario_config("anything")

    assert "legacy_system" not in config


def test_empty_requirement_raises():
    with pytest.raises(GeneratorError):
        generate_scenario_config("   ")


def test_call_model_backend_sends_bearer_auth_and_openai_shape(monkeypatch):
    import httpx

    from app.scenario_generator import _call_model_backend

    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"choices": [{"message": {"content": "hi"}}]})

    monkeypatch.setattr(gen.settings, "promptops_gateway_api_key", "test-key")
    test_client = httpx.Client(transport=httpx.MockTransport(handler))

    reply = _call_model_backend("a prompt", client=test_client)

    assert reply == "hi"
    assert captured["path"].endswith("/chat/completions")
    assert captured["auth"] == "Bearer test-key"
