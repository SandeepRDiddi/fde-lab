# FDE-034: GlobalRetail engagement — Stage 15 (FinOps / Token Economics)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-017, FDE-033
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017)

## User story
As a student, I want Stage 15 to hand me a Finance stakeholder with a
spreadsheet who directly challenges the per-transaction AI cost, so my unit
economics deliverable has to survive scrutiny from someone who isn't
impressed by the architecture — only the bill.

## Motivation

Sixteenth stage-content story on FDE-017's primitive; appends
`GLOBAL_RETAIL_STAGES[15]`. Per the framework: **Situation** — Finance sees
the pilot's model bill and asks, in a meeting, why one transaction costs
more than it should. **Assets** — six weeks of usage and cost data from the
pilot. **FDE must** — attribute cost per model/tool/token, introduce
routing, caching, and budgets that survive scrutiny. **Injected** — Finance
challenges the per-transaction AI cost directly, spreadsheet in hand.
**GlobalRetail specifics** — answering "where's my order" is currently
costing more than the margin on some of the SKUs in that order. **Deliverable**
— Unit Economics Dashboard.

New one-scene persona: Morgan Patel, VP of Finance — the first
finance-side stakeholder in the engagement, distinct from the
engineering/platform/security voices used so far.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[15]` with a persona
   (Morgan Patel, VP of Finance) that, only on request, states six weeks of
   usage/cost data exists and that answering "where's my order" currently
   costs more than the margin on some SKUs — the concrete number Finance is
   challenging.
2. THE `compliance_checklist` SHALL gate the Unit Economics Dashboard on
   naming cost attribution (per model/tool/token), model routing, caching,
   and a real budget mechanism, plus explicitly addressing the
   margin-vs-cost gap Finance raised.
3. WHEN `GLOBAL_RETAIL_STAGES` is passed to `POST /engagements/global-retail`,
   THE resulting engagement SHALL include stage 15, locked until stage 14's
   submission is approved — existing FDE-017 behavior, unchanged.

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[15]` authored (persona + compliance_checklist)
- [x] Tests: stage 15 config validates, persona doesn't leak facts
      unprompted, a compliant dashboard writeup passes the checklist, each
      missing element fails its rule
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[15]` in
`backend/app/engagement_content/global_retail.py`. New one-scene persona,
Morgan Patel (VP of Finance) — the first finance-side stakeholder, distinct
from the engineering/platform/security voices used in every prior stage.
Reveals the six-weeks-of-data fact and the specific margin-vs-cost gap only
on request. `compliance_checklist` requires cost attribution, model
routing, caching, a budget mechanism, and explicit margin framing.

Tests: `backend/tests/test_global_retail_stage15.py` (8 tests) — config
validates, no technical_task/data_gen, persona doesn't dump facts
unprompted, persona states the margin gap verbatim, compliant dashboard
passes, and three negative cases (missing model routing, missing caching,
missing margin framing) each fail their specific rule. Full backend suite:
272 passed (up from 264 before this story).
