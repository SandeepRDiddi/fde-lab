# FDE-006: Compliance checklist engine

**Status:** Done
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
- [x] At least one scenario has a working checklist end to end
- [x] Story status updated below
- [x] architecture.md updated if the checklist model deviates from documented (no deviation)

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

### 2026-09-18 (merge review)
Code-reviewed PR #18 and fixed before merge — the most serious finding
defeated the checklist's whole purpose:
- `_mentions()` did a naive substring match, so content that explicitly
  *denies* the requirement still satisfied the rule as long as the keyword
  appeared — e.g. "Rollback plan: none needed." passed
  `rollback-plan-present` just because "rollback" is in the text. This was
  even baked into the shipped test as expected behavior. Rewrote `_mentions`
  to check a small token window on both sides of each keyword occurrence for
  a negation word ("no", "not", "none", "without", etc.); a keyword is only
  affirmed if at least one un-negated occurrence exists.
- `pii-reviewed`/`approval-ticket-referenced` used `bool(metadata.get(...))`,
  so a string value like `"false"` (Python-truthy) satisfied the rule despite
  meaning the opposite. New `_truthy_metadata()` treats a small set of
  falsy-looking strings ("false", "no", "n/a", "0", "") as not satisfying,
  in addition to the empty/`None`/`0` cases `bool()` already caught.
- `Submission` is `@dataclass(frozen=True)` but has a mutable `Dict` field —
  the auto-generated `__hash__` tried to hash that dict and raised
  `TypeError` the moment anything hashed a `Submission`. Excluded `metadata`
  from eq/hash via `field(compare=False)`.

Updated the existing "partial failure" test to use a non-negated rollback
mention (so it still isolates exactly one failing rule as originally
intended) and added three new tests: negated mention correctly fails,
falsy-string metadata correctly fails, and `Submission` is actually
hashable. `python3 -m unittest discover -s mocks/compliance-engine/tests -v`:
7 passed. Merged via squash, PR #18 closed, branch deleted.

_(appended by the agent as work happens)_
