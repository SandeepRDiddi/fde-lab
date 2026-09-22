# FDE-037: GlobalRetail engagement — Stage 18 (Incident Simulation)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-017, FDE-031, FDE-036
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017)

## User story
As a student, I want Stage 18 to hand me a live-feeling latency spike with
a stakeholder already fielding complaints, so my RCA has to actually name
a root cause and a mitigation, not just acknowledge something's wrong.

## Motivation

Nineteenth stage-content story on FDE-017's primitive; appends
`GLOBAL_RETAIL_STAGES[18]`. Per the framework: **Situation** — mid-morning
on a weekday, response latency quietly climbs and frontline users start
calling the tool "useless now." **Assets** — live telemetry from Stage 12,
an active simulated incident. **FDE must** — diagnose from telemetry
alone, find the real root cause, mitigate, and communicate status while
it's still unfolding. **Injected** — response latency jumps by nearly an
order of magnitude with no deployment change to explain it. **GlobalRetail
specifics** — 2 seconds to 18 seconds, felt by store associates mid-shift,
with nothing in the deploy log. **Deliverable** — Incident RCA.

Persona is Priya Anand, reused from Stage 1 (VP of Operations, the one who
already cares about store-level speed and hears from store associates
directly) rather than a new character — she's the natural person fielding
frontline complaints during this specific incident.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[18]` with a persona
   (Priya Anand) that, only on request, states the specific latency jump
   (2 seconds to 18 seconds), that nothing in the deploy log explains it,
   and that store associates mid-shift are the ones affected.
2. THE `compliance_checklist` SHALL gate the Incident RCA on naming the
   specific latency numbers (evidence of engaging with the real incident,
   not a generic template), a root cause, a mitigation, and a status
   update communicated while the incident is still unfolding.
3. WHEN `GLOBAL_RETAIL_STAGES` is passed to `POST /engagements/global-retail`,
   THE resulting engagement SHALL include stage 18, locked until stage 17's
   submission is approved — existing FDE-017 behavior, unchanged.

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[18]` authored (persona + compliance_checklist)
- [x] Tests: stage 18 config validates, persona doesn't leak facts
      unprompted, a compliant RCA passes the checklist, each missing
      element fails its rule
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[18]` in
`backend/app/engagement_content/global_retail.py`. Persona is Priya Anand,
reused from Stage 1 (VP of Operations) — the natural person fielding
frontline complaints during this specific incident. States the 2s-to-18s
latency jump and the empty deploy log only on request.
`compliance_checklist` requires the specific latency numbers (not a vague
"it got slow"), a named root cause, a mitigation, and a status update
communicated while the incident is still unfolding — not just an eventual
RCA after the fact.

Tests: `backend/tests/test_global_retail_stage18.py` (7 tests) — config
validates, no technical_task/data_gen, persona doesn't dump facts
unprompted, persona states the specific numbers, compliant RCA passes, and
three negative cases (missing latency numbers, missing status update,
missing root cause) each fail their specific rule. Full backend suite: 296
passed (up from 288 before this story).
