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
_(appended by the agent as work happens)_
