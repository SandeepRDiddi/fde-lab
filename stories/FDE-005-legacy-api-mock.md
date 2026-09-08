# FDE-005: Legacy API mock service

**Status:** Not started
**Priority:** P1
**Depends on:** —
**Architecture ref:** architecture.md → Enterprise system mocks

## User story
As a student, I want to encounter a mock legacy system with realistic quirks, so
that I practice integrating with imperfect infrastructure.

## Acceptance criteria (EARS)
1. THE legacy API mock SHALL expose at least one endpoint per scenario that returns
   intentionally inconsistent field names or types across calls.
2. WHERE a scenario configures added latency, THE legacy API mock SHALL delay
   responses by the configured amount.
3. IF a request omits the scenario's required auth header, THEN THE legacy API mock
   SHALL return a 401 with a deliberately unhelpful error message.

## Definition of done
- [ ] Mock behavior is configurable per scenario without a code change
- [ ] Story status updated below
- [ ] architecture.md updated if the mock approach deviates from documented

## Implementation log
_(appended by the agent as work happens)_
