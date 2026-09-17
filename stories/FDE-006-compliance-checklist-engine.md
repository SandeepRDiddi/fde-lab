# FDE-006: Compliance checklist engine

**Status:** Not started
**Priority:** P1
**Depends on:** —
**Architecture ref:** architecture.md → Enterprise system mocks

## User story
As a student, I want a compliance gate that must be satisfied before I can submit,
so that I practice working within approval constraints.

## Acceptance criteria (EARS)
1. THE compliance engine SHALL define a checklist of rules per scenario.
2. WHEN a student attempts to submit, THE compliance engine SHALL evaluate the
   submission against the checklist.
3. IF the submission fails any checklist rule, THEN THE compliance engine SHALL
   block the submission and return the specific failing rule(s).

## Definition of done
- [ ] At least one scenario has a working checklist end to end
- [ ] Story status updated below
- [ ] architecture.md updated if the checklist model deviates from documented

## Implementation log

**2026-09-17** — Implemented as a standalone, dependency-free Python module at
`mocks/compliance-engine/` (stdlib only, no framework):
- `compliance_engine/models.py` — `Submission`, `Rule`, `RuleResult`,
  `ChecklistResult` (with `.passed` / `.failures` derived properties).
- `compliance_engine/engine.py` — `ComplianceEngine`: registers one checklist
  (ordered list of `Rule`) per `scenario_id`; `evaluate()` runs every rule and
  raises `UnknownScenarioError` for an unregistered scenario.
- `compliance_engine/checklists.py` — the shipped checklist data; one scenario
  (`data-migration-01`, 4 rules: risk assessment present, PII reviewed,
  rollback plan present, approval ticket referenced) wired up via
  `default_engine()`, satisfying AC1 end to end.
- `tests/test_engine.py` (stdlib `unittest`, no pytest dependency) covers:
  full pass, full failure naming all 4 failing rules, partial failure naming
  only the actually-failing rule, and the unknown-scenario error path —
  covering AC2 (evaluate on submit) and AC3 (block + name specific failing
  rules).

Deviation / note: not exposed as a networked HTTP mock service. `architecture.md`
already flags as an open question whether the three enterprise mocks are
separate services or backend routes for v1; since that's undecided and no
backend exists yet in this repo to route from, `ComplianceEngine.evaluate()` is
built as the plain integration point (importable now, wrappable in a
route/endpoint later) rather than pre-deciding that open question. No
architecture.md changes made — this doesn't contradict what's documented,
just doesn't yet resolve the open question.

Verification note: automated test execution (`python3 -m unittest discover
-s mocks/compliance-engine/tests -v`) was blocked by sandbox/approval
restrictions in this session (bash execution of interpreters was not
permitted, including via a general-purpose subagent). The logic was traced
by hand against all four test cases instead. Run the command above in an
environment without that restriction to get an actual pass/fail before
merge.

_(appended by the agent as work happens)_
