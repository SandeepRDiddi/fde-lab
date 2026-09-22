# FDE-029: GlobalRetail engagement — Stage 10 (Agent Engineering)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-017, FDE-028
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017)

## User story
As a student, I want Stage 10 to hand me a real multi-step investigation
and a runaway-retry-loop failure to design against, so my agent workflow
has to actually bound its own retries instead of assuming every tool call
eventually succeeds.

## Motivation

Eleventh stage-content story on FDE-017's primitive, and the final stage of
Mission 3 (Engineer); appends `GLOBAL_RETAIL_STAGES[10]`. Per the
framework: **Situation** — a real investigation isn't one lookup, it's a
chain of checks across systems that ends in a decision about what to do
next. **Assets** — the working AI service from Stage 9, a target task
requiring real multi-step reasoning. **FDE must** — design planner/executor
separation, state and memory, human-in-the-loop checkpoints, and retries
that actually terminate. **Injected** — one agent run enters a retry loop
against a tool call that keeps failing, quietly burning tokens until
someone notices. **GlobalRetail specifics** — an order-delay investigation:
check status, check inventory, check supplier ETA, decide whether to
escalate. **Deliverable** — Agent Workflow.

Same scope judgment as Stage 9 (FDE-028): no agent-execution framework
exists in this repo to actually run a multi-step loop, so the runaway-retry
failure is persona-narrated and the deliverable is a design writeup graded
on whether it bounds retries and defines the investigation chain — not
runnable agent code.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[10]` with a persona
   (Taylor Brooks, continuing from Stage 9) that, only on request,
   describes the order-delay investigation chain (status → inventory →
   supplier ETA → escalate/don't) and the injected runaway-retry incident
   (an agent run stuck retrying a failing tool call, unbounded, burning
   tokens until someone noticed).
2. THE `compliance_checklist` SHALL gate the Agent Workflow deliverable on
   defining planner/executor separation, a human-in-the-loop checkpoint,
   an explicit retry limit (the direct fix for the injected incident), and
   the escalate/don't-escalate decision point.
3. WHEN `GLOBAL_RETAIL_STAGES` is passed to `POST /engagements/global-retail`,
   THE resulting engagement SHALL include stage 10, locked until stage 9's
   submission is approved — existing FDE-017 behavior, unchanged. This
   closes out Mission 3 (Engineer, Stages 9-10).

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[10]` authored (persona + compliance_checklist)
- [x] Tests: stage 10 config validates, persona doesn't leak facts
      unprompted, persona encodes the runaway-retry incident, a compliant
      workflow passes the checklist, each missing element fails its rule
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[10]` in
`backend/app/engagement_content/global_retail.py`, closing out Mission 3
(Engineer: Stages 9–10). Persona continues as Taylor Brooks. Reveals the
four-step order-delay investigation chain and the injected runaway-retry
incident (unbounded tool-call retries burning tokens for hours before
anyone noticed) only on request. `compliance_checklist` requires
planner/executor separation, a human checkpoint before the escalate
decision, an explicit retry limit (the direct fix for the injected
incident), and the escalate decision point itself.

Caught a repeated-word test bug while writing the negative fixtures: the
compliant text uses both "planner" and "human" twice each (once in the
main design, once in a secondary reference), so an early draft of the
planner-separation negative test only stripped one occurrence and left the
checklist passing anyway — fixed by replacing all occurrences (`.replace`
already does this by default; the bug was replacing a longer phrase that
didn't match the second occurrence's wording, not `replace`'s behavior
itself). Same class of mistake as FDE-022's double-"deterministic" fixture
bug — worth remembering for any future stage whose required word appears
more than once in its own fixture.

Tests: `backend/tests/test_global_retail_stage10.py` (8 tests) — config
validates, no technical_task/data_gen, persona doesn't dump facts
unprompted, persona encodes the runaway-retry incident, compliant workflow
passes, and three negative cases (missing retry limit, missing human
checkpoint, missing planner separation) each fail their specific rule.
Full backend suite: 233 passed (up from 225 before this story).

This closes out Mission 3 (Engineer) of "The FDE Engagement Framework" —
Stages 9-10 authored, alongside Mission 1 (0-4) and Mission 2 (5-8), all
gradable end to end via `POST /engagements/global-retail`. Mission 4
(Industrialize, Stages 11-16 — the largest mission, six stages) is next
(FDE-030 onward).
