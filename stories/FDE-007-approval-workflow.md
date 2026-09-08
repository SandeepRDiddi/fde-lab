# FDE-007: Approval workflow state machine

**Status:** Not started
**Priority:** P1
**Depends on:** FDE-006
**Architecture ref:** architecture.md → Enterprise system mocks

## User story
As a student, I want my submission to go through a review state before it's marked
complete, so that I experience a real approval chain.

## Acceptance criteria (EARS)
1. WHEN a submission passes the compliance checklist, THE approval workflow SHALL
   move it to "pending review."
2. WHERE a scenario configures a review delay, THE approval workflow SHALL hold the
   submission in "pending review" for that duration before auto-approving or
   auto-rejecting per scenario config.
3. WHEN a submission is approved or rejected, THE approval workflow SHALL notify
   the student and record the outcome on the scenario instance.

## Definition of done
- [ ] Full submit → pending → approved/rejected cycle demoable
- [ ] Story status updated below
- [ ] architecture.md updated if the workflow model deviates from documented

## Implementation log
_(appended by the agent as work happens)_
