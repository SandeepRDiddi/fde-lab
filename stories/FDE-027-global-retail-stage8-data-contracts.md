# FDE-027: GlobalRetail engagement — Stage 8 (Data Contracts & Integration)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-017, FDE-026
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017)

## User story
As a student, I want Stage 8 to make me write an actual data contract
against the same warehouse system I already found drifting schema back in
Stage 2, so the contract I design is a real fix for a problem I already
diagnosed, not an abstract exercise.

## Motivation

Ninth stage-content story on FDE-017's primitive, and the final stage of
Mission 2 (Architect); appends `GLOBAL_RETAIL_STAGES[8]`. Per the
framework: **Situation** — upstream teams ship schema changes on their own
release calendar; nobody asks the AI platform team first. **Assets** —
informal integration code salvaged from the abandoned vendor attempt. **FDE
must** — define explicit contracts, validation, and versioning so an
upstream change doesn't silently break the platform. **GlobalRetail
specifics** — the warehouse team owns its own schema and release calendar,
independent of the AI platform. **Deliverable** — ODCS / Data Contracts.

New persona: Devon Ruiz, Warehouse Systems Lead — the owning team on the
other side of the contract, and the same system Stage 2's persona (Taylor
Brooks) already flagged as schema-drifting via the `northwind-erp` mock.
This stage's deliverable is a genuine fix for a problem the student already
diagnosed two stages ago, not a fresh abstract exercise.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[8]` with a persona (Devon
   Ruiz, Warehouse Systems Lead) that, only on request, confirms the
   warehouse team ships schema changes on its own release calendar with no
   coordination with the AI platform team, and that the salvaged vendor
   integration code has no contract or validation — it just parses
   whatever comes back.
2. THE `compliance_checklist` SHALL gate the Data Contract deliverable on
   naming schema versioning, validation, and the warehouse team's
   independent release calendar explicitly — the three concrete elements
   FDE-005/FDE-017's own architecture already needs to survive an upstream
   change.
3. WHEN `GLOBAL_RETAIL_STAGES` is passed to `POST /engagements/global-retail`,
   THE resulting engagement SHALL include stage 8, locked until stage 7's
   submission is approved — existing FDE-017 behavior, unchanged. This
   closes out Mission 2 (Architect, Stages 5-8).

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[8]` authored (persona + compliance_checklist)
- [x] Tests: stage 8 config validates, persona doesn't leak facts
      unprompted, a compliant data contract passes the checklist, each
      missing element fails its rule
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[8]` in
`backend/app/engagement_content/global_retail.py`, closing out Mission 2
(Architect: Stages 5–8). New persona, Devon Ruiz (Warehouse Systems Lead) —
the owning team behind the same schema-drifting integration Stage 2's
persona (Taylor Brooks) already flagged, so this stage's deliverable fixes
a problem the student diagnosed two stages earlier rather than presenting a
fresh abstract exercise. Reveals the independent release calendar and the
salvaged code's lack of contract/validation only on request.
`compliance_checklist` requires explicit schema versioning, validation, and
acknowledgment of the independent release calendar.

Tests: `backend/tests/test_global_retail_stage8.py` (7 tests) — config
validates, no technical_task/data_gen, persona doesn't dump facts
unprompted, persona's schema-drift description matches Stage 2's wording
verbatim (continuity check), compliant contract passes, and three negative
cases (missing versioning, missing validation, missing release-calendar
acknowledgment) each fail their specific rule. Full backend suite: 218
passed (up from 210 before this story).

This closes out Mission 2 (Architect) of "The FDE Engagement Framework" —
Stages 5-8 all authored and gradable end to end via
`POST /engagements/global-retail`, alongside Mission 1 (Stages 0-4).
Mission 3 (Engineer, Stages 9-10) is next (FDE-028 onward).
