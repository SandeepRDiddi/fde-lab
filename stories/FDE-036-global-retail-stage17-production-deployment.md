# FDE-036: GlobalRetail engagement — Stage 17 (Production Deployment)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-017, FDE-035
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017)

## User story
As a student, I want Stage 17 to require an actual containerized,
multi-component deployment plan, so it's the real thing running somewhere
real — not a description of components that stayed on a laptop.

## Motivation

Eighteenth stage-content story on FDE-017's primitive, and the first stage
of Mission 5 (Operate Under Pressure); appends `GLOBAL_RETAIL_STAGES[17]`.
Per the framework: **Situation** — it's time to actually run this
somewhere real, not on a laptop. **Assets** — target cloud environment
access, the Stage 16 production pipeline. **FDE must** — containerize and
deploy the APIs, agent, and data components into a realistic environment.
**Deliverable** — Running Production-like System. (No injected mid-stage
complication in the framework artifact for this stage.)

Persona continues as Taylor Brooks (the recurring platform/infra thread)
for continuity with Stages 2/3/6/9/10/12/16.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[17]` with a persona that,
   only on request, confirms cloud environment access is available and
   that the Stage 16 pipeline is the thing that should actually deploy
   it — not a manual deploy step.
2. THE `compliance_checklist` SHALL gate the deployment deliverable on
   naming containerization, the API components, the agent component, and
   framing the target as a realistic (production-like) environment, not a
   local one.
3. WHEN `GLOBAL_RETAIL_STAGES` is passed to `POST /engagements/global-retail`,
   THE resulting engagement SHALL include stage 17, locked until stage 16's
   submission is approved — existing FDE-017 behavior, unchanged.

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[17]` authored (persona + compliance_checklist)
- [x] Tests: stage 17 config validates, persona doesn't leak facts
      unprompted, a compliant deployment writeup passes the checklist,
      each missing element fails its rule
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[17]` in
`backend/app/engagement_content/global_retail.py`, opening Mission 5
(Operate Under Pressure). Persona continues as Taylor Brooks. States cloud
access is ready and insists deployment go through the Stage 16 pipeline,
not a manual step, only on request. `compliance_checklist` requires
containerization, the API and agent components named, and production-like
environment framing.

Tests: `backend/tests/test_global_retail_stage17.py` (7 tests) — config
validates, no technical_task/data_gen, persona doesn't dump facts
unprompted, persona insists on pipeline-not-manual deploy, compliant
deployment passes, and three negative cases (missing container framing,
missing production framing, missing agent component) each fail their
specific rule. Full backend suite: 288 passed (up from 280 before this
story).
