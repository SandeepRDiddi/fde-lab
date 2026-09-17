# Compliance checklist engine

One of the three "enterprise system mocks" described in `architecture.md` →
Enterprise system mocks. Gates a student's submission behind a scenario-specific
checklist of rules before it can "ship."

## Model

- **`Rule`** — an id, a human-readable description, and a predicate over a
  `Submission`.
- **`ComplianceEngine`** — holds one checklist (ordered list of `Rule`s) per
  `scenario_id`, registered via `register_checklist`.
- **`Submission`** — `scenario_id` + free-text `content` + a `metadata` dict for
  structured fields (e.g. `pii_reviewed`, `approval_ticket`) a real submission
  form would collect alongside the write-up.
- **`ChecklistResult`** — every rule's pass/fail (`.results`), plus `.passed`
  (all rules passed) and `.failures` (the specific rules that didn't).

`checklists.py` holds the actual scenario checklists shipped today (currently
`data-migration-01`). Adding a scenario means adding a rule list + registering
it in `default_engine()` — the engine itself doesn't change.

## Usage

```python
from compliance_engine import Submission, default_engine

engine = default_engine()

submission = Submission(
    scenario_id="data-migration-01",
    content="Risk Assessment: low. Rollback plan: revert to snapshot X.",
    metadata={"pii_reviewed": True, "approval_ticket": "APR-42"},
)

result = engine.evaluate(submission)
if not result.passed:
    # block the submission; result.failures lists the specific failing rules
    for failure in result.failures:
        print(failure.rule_id, failure.description)
```

An unrecognized `scenario_id` raises `UnknownScenarioError` — the caller is
expected to only route submissions for scenarios that exist.

This is deployed as a plain importable module here rather than as its own
networked service; `architecture.md`'s open question on whether the three
enterprise mocks are separate services or routes within the backend is still
unresolved, so `evaluate()` is the integration point either way (called
directly today, or wrapped in a route/endpoint once that decision is made).

## Running the tests

Stdlib-only, no dependencies to install:

```bash
python3 -m unittest discover -s mocks/compliance-engine/tests -v
```
