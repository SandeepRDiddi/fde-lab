# FDE-030: GlobalRetail engagement — Stage 11 (Enterprise Controls)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-017, FDE-021, FDE-029
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017)

## User story
As a student, I want Stage 11 to surface a real PII leak in the exact
supplier-contract PDFs I already knew were unindexed, and to have security
reject the escalation tool I already chose, so the Security Control Matrix
I produce fixes problems this specific engagement actually has, not a
generic checklist.

## Motivation

Twelfth stage-content story on FDE-017's primitive, and the first stage of
Mission 4 (Industrialize — the framework's largest mission, six stages);
appends `GLOBAL_RETAIL_STAGES[11]`. Per the framework: **Situation** — this
platform touches real customer and operational data across departments
that don't fully trust each other yet. **Assets** — the customer's data
classification policy, a role list spanning frontline, operations, and
executive users. **FDE must** — implement RBAC/ABAC, redact PII in
retrieval, get an approved alternative tool through security review.
**Injected** — a retrieved document turns out to contain PII nobody
flagged, and security blocks the tool you'd already picked for the
escalation workflow. **GlobalRetail specifics** — a supplier contract PDF
has an employee's personal details buried in it; security blocks the
first-choice escalation tool outright. **Deliverable** — Security Control
Matrix.

Persona is Jordan Lee, reused a fourth time (Stages 1/4, and implicitly the
governance stance behind Stage 7's ARB), now explicitly in the security-
review seat — consistent with an IT Director plausibly chairing both. The
PII finding lands in the same "half the supplier docs are unindexed PDFs"
gap Stage 3 already flagged, and the blocked tool is deliberately not
named (Stage 5's ADRs never named a specific product) — the student has to
propose *an* approved alternative, not match a hardcoded name.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[11]` with a persona
   (Jordan Lee) that, only on request, reveals the role list (frontline/
   ops/executive) needing RBAC, the PII finding in a supplier contract PDF,
   and the rejection of the FDE's first-choice escalation tool.
2. THE `compliance_checklist` SHALL gate the Security Control Matrix on
   naming RBAC, addressing PII redaction, referencing the specific
   supplier-contract finding, and proposing an approved alternative tool
   for the blocked escalation workflow.
3. WHEN `GLOBAL_RETAIL_STAGES` is passed to `POST /engagements/global-retail`,
   THE resulting engagement SHALL include stage 11, locked until stage 10's
   submission is approved — existing FDE-017 behavior, unchanged.

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[11]` authored (persona + compliance_checklist)
- [x] Tests: stage 11 config validates, persona doesn't leak facts
      unprompted, a compliant matrix passes the checklist, each missing
      element fails its rule
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[11]` in
`backend/app/engagement_content/global_retail.py`, opening Mission 4
(Industrialize). Persona is Jordan Lee, reused a fourth time (Stages 1/4),
now in the security-review seat. Reveals the three-tier role list, the PII
finding in a supplier contract PDF (the same unindexed-PDF gap Stage 3
flagged), and the blocked escalation tool only on request. The blocked
tool is deliberately not given a name in either the persona or the
checklist, since Stage 5's ADRs never named a specific product —
`compliance_checklist` requires RBAC, PII redaction, the specific supplier-
contract finding, and proposing *an* approved alternative generically.

Tests: `backend/tests/test_global_retail_stage11.py` (7 tests) — config
validates, no technical_task/data_gen, persona doesn't dump facts
unprompted, persona references the Stage 3 supplier-PDF gap verbatim
(continuity check), compliant matrix passes, and three negative cases
(missing RBAC, missing approved-alternative, missing the supplier-contract
reference) each fail their specific rule. Full backend suite: 241 passed
(up from 233 before this story).
