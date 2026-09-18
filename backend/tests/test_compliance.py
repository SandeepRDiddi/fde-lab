from app.compliance import evaluate_submission


def test_empty_rules_always_passes():
    passed, failures = evaluate_submission("anything", [])
    assert passed is True
    assert failures == []


def test_must_include_passes_when_phrase_present():
    rules = [{"id": "risk", "description": "risk assessment", "check": "must_include", "value": "risk assessment"}]
    passed, failures = evaluate_submission("Here is my risk assessment: low.", rules)
    assert passed is True
    assert failures == []


def test_must_include_fails_when_phrase_absent():
    rules = [{"id": "risk", "description": "risk assessment", "check": "must_include", "value": "risk assessment"}]
    passed, failures = evaluate_submission("Here is my migration plan.", rules)
    assert passed is False
    assert failures == [{"rule_id": "risk", "description": "risk assessment"}]


def test_must_include_negated_mention_does_not_satisfy_rule():
    """"No rollback plan" contains the word "rollback" but explicitly denies
    having one -- shouldn't satisfy a must_include rule just because the
    keyword is present."""
    rules = [{"id": "rollback", "description": "rollback plan", "check": "must_include", "value": "rollback"}]
    passed, failures = evaluate_submission("Rollback plan: none needed.", rules)
    assert passed is False
    assert failures == [{"rule_id": "rollback", "description": "rollback plan"}]


def test_must_exclude_fails_when_phrase_present():
    rules = [{"id": "no-ssn", "description": "no raw SSNs", "check": "must_exclude", "value": "SSN"}]
    passed, failures = evaluate_submission("Customer SSN: 123-45-6789", rules)
    assert passed is False
    assert failures == [{"rule_id": "no-ssn", "description": "no raw SSNs"}]


def test_min_length_fails_when_too_short():
    rules = [{"id": "len", "description": "at least 10 chars", "check": "min_length", "value": 10}]
    passed, failures = evaluate_submission("short", rules)
    assert passed is False
    assert failures == [{"rule_id": "len", "description": "at least 10 chars"}]


def test_unknown_check_type_fails_closed():
    rules = [{"id": "mystery", "description": "some new rule", "check": "not_a_real_check", "value": "x"}]
    passed, failures = evaluate_submission("anything", rules)
    assert passed is False
    assert failures == [{"rule_id": "mystery", "description": "some new rule"}]


def test_multiple_rules_names_every_failure():
    rules = [
        {"id": "risk", "description": "risk assessment", "check": "must_include", "value": "risk assessment"},
        {"id": "len", "description": "at least 50 chars", "check": "min_length", "value": 50},
    ]
    passed, failures = evaluate_submission("short", rules)
    assert passed is False
    assert {f["rule_id"] for f in failures} == {"risk", "len"}
