# FDE-038: GlobalRetail engagement — Stage 19 (Change Request)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-017, FDE-027, FDE-037
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017)

## User story
As a student, I want Stage 19 to break the exact data contract I already
signed off as stable in Stage 8, in the same week a stakeholder wants a new
capability, so my change impact assessment has to genuinely triage two real
competing asks, not one tidy change request.

## Motivation

Twentieth stage-content story on FDE-017's primitive, and the final stage
of Mission 5 (Operate Under Pressure); appends `GLOBAL_RETAIL_STAGES[19]`.
Per the framework: **Situation** — weeks after go-live, an upstream team
changes their schema without warning, and a business stakeholder
separately wants a new capability. **Assets** — the Stage 8 data
contracts, the new (informal) feature ask. **FDE must** — assess blast
radius, update the contract, ship the change without breaking anything
already live. **Injected** — a database schema changes mid-engagement,
breaking a contract already signed off as stable. **GlobalRetail
specifics** — the warehouse team changes the inventory schema three weeks
post-launch; Ops wants a new capability the same week. **Deliverable** —
Change Impact Assessment.

Persona is Devon Ruiz, reused from Stage 8 (Warehouse Systems Lead) — the
same person on the other side of the contract that's now breaking, per
that contract's own stated independent release calendar. Devon also relays
the separate Ops capability ask (from Priya Anand, reused conceptually the
way Stage 1 had one persona relay multiple stakeholders), since the
platform supports one persona per stage.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[19]` with a persona
   (Devon Ruiz) that, only on request, confirms the inventory schema
   changed three weeks post-launch (exactly the independent release
   calendar Stage 8's contract already anticipated) and relays a separate
   new-capability ask from Ops the same week.
2. THE `compliance_checklist` SHALL gate the Change Impact Assessment on
   assessing blast radius, bumping the schema version per Stage 8's
   contract mechanism, confirming backward compatibility for what's
   already live, and addressing the new capability ask without treating it
   as blocking the schema fix.
3. WHEN `GLOBAL_RETAIL_STAGES` is passed to `POST /engagements/global-retail`,
   THE resulting engagement SHALL include stage 19, locked until stage 18's
   submission is approved — existing FDE-017 behavior, unchanged. This
   closes out Mission 5 (Operate Under Pressure, Stages 17-19).

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[19]` authored (persona + compliance_checklist)
- [x] Tests: stage 19 config validates, persona doesn't leak facts
      unprompted, a compliant assessment passes the checklist, each
      missing element fails its rule
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[19]` in
`backend/app/engagement_content/global_retail.py`, closing out Mission 5
(Operate Under Pressure: Stages 17–19). Persona is Devon Ruiz, reused from
Stage 8 (Warehouse Systems Lead) — the same contract counterparty, now on
the breaking side of their own independent release calendar. Relays a
separate Ops capability ask (from Priya Anand) the same platform-persona-
per-stage way Stage 1 relayed multiple departments through one character.
`compliance_checklist` requires blast-radius assessment, a schema-version
bump (Stage 8's actual contract mechanism), explicit backward-compatibility
framing, and the new capability addressed without blocking the schema fix
on it.

Tests: `backend/tests/test_global_retail_stage19.py` (8 tests) — config
validates, no technical_task/data_gen, persona doesn't dump facts
unprompted, persona relays the separate Ops ask by name, compliant
assessment passes, and three negative cases (missing blast radius, missing
backward compatibility, missing new-capability handling) each fail their
specific rule. Full backend suite: 304 passed (up from 296 before this
story).

This closes out Mission 5 (Operate Under Pressure) of "The FDE Engagement
Framework" — Stages 17-19 authored, alongside Missions 1-4 (Stages 0-16),
all gradable end to end via `POST /engagements/global-retail`. Mission 6
(Deliver the Outcome, Stages 20-21 — the final two stages) is next
(FDE-039 onward).
