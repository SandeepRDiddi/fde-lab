# FDE-032: GlobalRetail engagement — Stage 13 (Failure Engineering)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-017, FDE-020, FDE-031
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017)

## User story
As a student, I want Stage 13 to demand proof, not a description — Marcus
Chen wants resilience demonstrated against the same SAP-standin system I've
touched since Stage 2, in the room, not asserted on a slide.

## Motivation

Fourteenth stage-content story on FDE-017's primitive; appends
`GLOBAL_RETAIL_STAGES[13]`. Per the framework: **Situation** — in
production, upstream systems will time out and the model backend will
occasionally be unreachable; the platform has to bend, not break. **Assets**
— the Stage 2 dependency map, the known-flaky endpoints surfaced back in
Stage 9. **FDE must** — add retry, fallback, circuit breaker, and
dead-letter handling, then prove it under an induced failure. **Injected**
— demonstrate rollback and graceful degradation live, in the room, not on a
slide. **GlobalRetail specifics** — the SAP mock is induced to time out for
the demonstration. **Deliverable** — Failure Playbook.

Scope note: the FDE-005 mock has no configurable timeout/failure-injection
scenario (only a fixed `latency_ms` and a 401-on-missing-auth path — see
FDE-020's and FDE-028's equivalent scope calls); a live induced timeout
demo isn't buildable without extending the mock service, out of this
content story's scope. The persona instead plays the demo audience —
Marcus Chen, reused from Stages 0/5 — demanding the design account for the
same SAP-standin dependency (`acme-crm`, already live-touched in Stage 2)
specifically, not a hypothetical system.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[13]` with a persona
   (Marcus Chen) that, only on request, states the SAP-standin system is
   being induced to time out for this review and that he wants the design
   proven against that specific dependency, not described abstractly.
2. THE `compliance_checklist` SHALL gate the Failure Playbook deliverable
   on naming all four resilience patterns the framework specifies (retry,
   fallback, circuit breaker, dead-letter handling) plus explicit rollback/
   graceful-degradation framing.
3. WHEN `GLOBAL_RETAIL_STAGES` is passed to `POST /engagements/global-retail`,
   THE resulting engagement SHALL include stage 13, locked until stage 12's
   submission is approved — existing FDE-017 behavior, unchanged.

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[13]` authored (persona + compliance_checklist)
- [x] Tests: stage 13 config validates, persona doesn't leak facts
      unprompted, a compliant playbook passes the checklist, each missing
      element fails its rule
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[13]` in
`backend/app/engagement_content/global_retail.py`. Persona is Marcus Chen,
reused a third time (Stages 0/5), playing the live-demo audience — reveals
that the SAP-standin dependency (the same `acme-crm` mock Stage 2 already
live-touched) is being induced to time out, only on request. Confirmed the
FDE-005 mock has no configurable timeout/failure-injection scenario before
writing this (only fixed `latency_ms` and a 401-on-missing-auth path), so
the induced failure stays persona-narrated — same scope call FDE-020 and
FDE-028 already made. `compliance_checklist` requires all four framework-
named resilience patterns (retry, fallback, circuit breaker, dead-letter)
plus explicit rollback/graceful-degradation framing.

Caught a repeated-phrase test bug again while writing the dead-letter
negative fixture (same class as FDE-022/FDE-029): the compliant text
mentions "dead-letter" twice (once capitalized as the pattern-name intro,
once lowercase later) — an initial single `.replace("Dead-letter", ...)`
left the second, lowercase occurrence intact, which would have kept the
checklist passing. Fixed by stripping both occurrences explicitly.

Tests: `backend/tests/test_global_retail_stage13.py` (7 tests) — config
validates, no technical_task/data_gen, persona doesn't dump facts
unprompted, persona references the Stage 2 SAP-standin access gap, compliant
playbook passes, and three negative cases (missing circuit breaker, missing
dead-letter, missing graceful degradation) each fail their specific rule.
Full backend suite: 256 passed (up from 248 before this story).
