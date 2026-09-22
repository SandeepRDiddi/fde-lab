# FDE-024: GlobalRetail engagement — Stage 5 (Solution Framing)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-017, FDE-022, FDE-023
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017)

## User story
As a student, I want Stage 5 to hand me three already-failed vendor pitches
and a budget/timeline ceiling, so my architecture decision has to actually
be justified against my own Stage 4 classification — not picked because
it's the most impressive-sounding option on a slide.

## Motivation

Sixth stage-content story on FDE-017's primitive, and the first stage of
Mission 2 (Architect); appends `GLOBAL_RETAIL_STAGES[5]`. Per the
framework: **Situation** — three vendors already pitched three different
architectures (a chatbot, a RAG search tool, a "fully autonomous" agent
platform); none of them shipped. **Assets** — the three abandoned vendor
proposals, a budget ceiling, a 90-day timeline. **FDE must** — evaluate
build-vs-buy and RAG-vs-workflow-vs-agent against the AI Readiness Matrix
(Stage 4's deliverable), not against what's fashionable. **Deliverable** —
Architecture Decision Records.

First stage to actually depend on FDE-023's fix: the persona's system
prompt gets Stage 4's approved AI Readiness Matrix appended automatically
via `config["engagement_context"]` at conversation time, so the persona can
reference "your classification from last stage" as established fact without
this stage's own content needing to restate it.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[5]` with a persona
   (Marcus Chen, reused from Stage 0 as the VP of Engineering the student
   reports to) holding the three abandoned vendor pitches, the budget
   ceiling, and the 90-day timeline — revealed only on request.
2. THE `compliance_checklist` SHALL gate the ADR deliverable on choosing
   RAG for the AI-assisted use case, an agentic workflow for the agentic
   use case, respecting the budget constraint, and explicitly excluding
   return-eligibility from any AI architecture — i.e. the decision has to
   trace back to Stage 4's classification, not just name technologies in
   the abstract.
3. WHEN `GLOBAL_RETAIL_STAGES` is passed to `POST /engagements/global-retail`,
   THE resulting engagement SHALL include stage 5, locked until stage 4's
   submission is approved — existing FDE-017 behavior, unchanged.

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[5]` authored (persona + compliance_checklist)
- [x] Tests: stage 5 config validates, persona doesn't leak facts
      unprompted, a compliant ADR set passes the checklist, each missing
      element fails its rule
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[5]` in
`backend/app/engagement_content/global_retail.py`, opening Mission 2
(Architect). Persona is Marcus Chen, reused from Stage 0 (VP of Engineering,
the student's reporting line) rather than a new character. Reveals the
three abandoned vendor pitches, the $400K budget, and the 90-day timeline
only on request. `compliance_checklist` requires the RAG/agentic-workflow
split per Stage 4's classification, an explicit return-eligibility
exclusion, and budget framing — the decision has to trace back to the
earlier classification, not just name technologies abstractly.

First stage that actually exercises FDE-023's fix in practice: Stage 4's
approved AI Readiness Matrix now reaches this persona automatically via
`config["engagement_context"]` at conversation time, so the persona prompt
here doesn't need to restate the classification itself — it's established
fact by the time this stage's conversation starts.

Tests: `backend/tests/test_global_retail_stage5.py` (7 tests) — config
validates, no technical_task/data_gen, persona doesn't dump facts
unprompted, persona references all three failed vendor pitches, compliant
ADR set passes, and three negative cases (missing RAG choice, missing
return-eligibility exclusion, missing budget framing) each fail their
specific rule. Full backend suite: 195 passed (up from 187 before this
story).
