# FDE-011: LTI 1.3 launch service

**Status:** Not started
**Priority:** P1
**Depends on:** FDE-001
**Architecture ref:** architecture.md → LTI launch service — LMS entry point

## User story
As a student, I want to launch my scenario directly from a link inside my course's
LMS, so that I don't need a separate login or destination to get into FDE Lab.

## Acceptance criteria (EARS)
1. WHEN a student clicks an LTI 1.3 launch link in the course LMS, THE launch
   service SHALL complete the OIDC-based launch handshake and authenticate the
   student without a separate FDE Lab login.
2. THE launch service SHALL map the LMS course/cohort to the correct scenario
   instance in the scenario engine.
3. WHERE the LMS supports Names and Roles Provisioning Service (NRPS), THE launch
   service SHALL be able to use it to populate a cohort's roster automatically.
4. WHERE the LMS supports Assignment and Grade Services (AGS), THE launch service
   SHALL be able to push a completion/score back to the LMS gradebook once a
   scenario finishes.

## Definition of done
- [ ] A test launch from at least one LMS (Canvas or Moodle) lands the student in
      the correct scenario instance
- [ ] Story status updated below
- [ ] architecture.md updated if the LTI approach deviates from documented

## Implementation log
_(appended by the agent as work happens)_


## Implementation log
_(appended by the agent as work happens)_
