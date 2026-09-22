# FDE-031: GlobalRetail engagement — Stage 12 (Observability)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-017, FDE-030
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017)

## User story
As a student, I want Stage 12 to hand me the actual moment nobody could
explain a wrong answer in front of a stakeholder, so the tracing I design
is motivated by that specific failure, not instrumentation for its own
sake.

## Motivation

Thirteenth stage-content story on FDE-017's primitive; appends
`GLOBAL_RETAIL_STAGES[12]`. Per the framework: **Situation** — the agent
gives a wrong answer in front of a stakeholder, and nobody can explain why
after the fact. **Assets** — raw, unstructured application logs, no
existing tracing. **FDE must** — instrument prompts, tool calls, latency,
tokens, and decisions so every answer is explainable after the fact.
**Deliverable** — Langfuse/OTel Dashboard. (This is the one stage in the
framework artifact with no injected mid-stage complication — the situation
itself is the constraint.)

Persona continues as Taylor Brooks (the recurring technical thread) rather
than introducing a new character, since this is infrastructure work
continuous with Stages 2/3/6/9/10.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[12]` with a persona that,
   only on request, describes the specific incident (a wrong answer given
   live in front of a stakeholder, unexplainable afterward from the raw
   logs alone) motivating the tracing work.
2. THE `compliance_checklist` SHALL gate the Observability deliverable on
   naming trace instrumentation, prompts, tool calls, and token/latency
   tracking — the four concrete signal types the framework names.
3. WHEN `GLOBAL_RETAIL_STAGES` is passed to `POST /engagements/global-retail`,
   THE resulting engagement SHALL include stage 12, locked until stage 11's
   submission is approved — existing FDE-017 behavior, unchanged.

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[12]` authored (persona + compliance_checklist)
- [x] Tests: stage 12 config validates, persona doesn't leak facts
      unprompted, a compliant dashboard writeup passes the checklist, each
      missing element fails its rule
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[12]` in
`backend/app/engagement_content/global_retail.py`. Persona continues as
Taylor Brooks. Reveals the unexplainable-wrong-answer incident only on
request — the framework's own artifact has no injected mid-stage
complication for this stage, so the situation itself (no tracing, raw
unstructured logs) is the whole motivating constraint, nothing added.
`compliance_checklist` requires the four concrete signal types the
framework names: trace-level instrumentation, prompts, tool calls, and
latency/token tracking.

Tests: `backend/tests/test_global_retail_stage12.py` (7 tests) — config
validates, no technical_task/data_gen, persona doesn't dump facts
unprompted, persona describes the unexplainable incident, compliant
dashboard writeup passes, and two negative cases (missing tool-call
tracking, missing latency tracking) each fail their specific rule. Full
backend suite: 248 passed (up from 241 before this story).
