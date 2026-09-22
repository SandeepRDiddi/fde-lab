# FDE-035: GlobalRetail engagement — Stage 16 (DevSecOps / AIDLC)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-017, FDE-033, FDE-034
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017)

## User story
As a student, I want Stage 16 to reject "we tested it locally" outright, so
the pipeline I design actually wires Stage 14's evaluation harness in as a
real deployment gate, not a manual step someone might skip.

## Motivation

Seventeenth stage-content story on FDE-017's primitive, and the final
stage of Mission 4 (Industrialize — six stages, the framework's largest
mission); appends `GLOBAL_RETAIL_STAGES[16]`. Per the framework:
**Situation** — the platform team won't accept "we tested it locally" as a
deployment gate. **Assets** — existing CI/CD pipeline standards, the Stage
14 evaluation harness. **FDE must** — wire prompt/model versioning, policy
gates, and automated tests into a real pipeline. **Deliverable** —
Production Pipeline. (Like Stage 12, the framework artifact has no injected
mid-stage complication here — the standing requirement itself is the
constraint.)

Persona continues as Taylor Brooks (the recurring technical/platform
thread) rather than a new character, since CI/CD ownership fits the same
role as Stages 2/3/6/9/10/12.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[16]` with a persona that,
   only on request, states the platform team's standing rule: "tested
   locally" is not an acceptable deployment gate, and references Stage
   14's evaluation harness as the thing that has to actually run in the
   pipeline, not be described as available.
2. THE `compliance_checklist` SHALL gate the Production Pipeline
   deliverable on naming prompt/model versioning, policy gates, automated
   tests wired into the pipeline, and the pipeline itself.
3. WHEN `GLOBAL_RETAIL_STAGES` is passed to `POST /engagements/global-retail`,
   THE resulting engagement SHALL include stage 16, locked until stage 15's
   submission is approved — existing FDE-017 behavior, unchanged. This
   closes out Mission 4 (Industrialize, Stages 11-16).

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[16]` authored (persona + compliance_checklist)
- [x] Tests: stage 16 config validates, persona doesn't leak facts
      unprompted, a compliant pipeline writeup passes the checklist, each
      missing element fails its rule
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[16]` in
`backend/app/engagement_content/global_retail.py`, closing out Mission 4
(Industrialize: Stages 11–16, the framework's largest mission). Persona
continues as Taylor Brooks. States the "tested locally is not an acceptable
gate" standing rule only on request. `compliance_checklist` requires
prompt/model versioning, policy gates, automated (not manual) test wiring,
and description of an actual pipeline.

Tests: `backend/tests/test_global_retail_stage16.py` (7 tests) — config
validates, no technical_task/data_gen, persona doesn't dump facts
unprompted, persona rejects "tested locally" verbatim, compliant pipeline
passes, and three negative cases (missing policy gates, missing automated
wiring, missing versioning) each fail their specific rule. Full backend
suite: 280 passed (up from 272 before this story).

This closes out Mission 4 (Industrialize) of "The FDE Engagement
Framework" — Stages 11-16 authored, alongside Missions 1-3 (Stages 0-10),
all gradable end to end via `POST /engagements/global-retail`. Mission 5
(Operate Under Pressure, Stages 17-19) is next (FDE-036 onward).
