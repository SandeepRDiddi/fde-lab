# FDE-020: GlobalRetail engagement — Stage 2 (Current-State Assessment)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-005, FDE-017, FDE-019
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017); Enterprise system mocks

## User story
As a student, I want Stage 2 to hand me a genuinely blocked system access
(a real 401 from a real mock, not a narrated one) alongside a system I *can*
reach but that behaves unreliably, so my dependency map reflects what I
actually observed rather than what I was told.

## Motivation

Third stage-content story on FDE-017's primitive; appends
`GLOBAL_RETAIL_STAGES[2]`. Per the framework: **Situation** — core business
data lives scattered across the customer's own transactional systems,
linked by integrations nobody fully documented. **Assets** — an outdated
network diagram, a partial list of known integration points, read access to
some but not all systems. **FDE must** — reverse-engineer the real data
flow from what's observable, flag every undocumented dependency, decide how
to proceed without full access. **Injected** — access to the system of
record isn't available yet (procurement never finished). **GlobalRetail
specifics** — order/inventory/supplier data across SAP, Salesforce, and the
storefront; SAP access specifically is stuck in procurement. **Deliverable**
— C4 + Dependency Map.

Unlike Stages 0–1 (persona-only), this stage wires `config["legacy_system"]`
to FDE-005's actual mock service so the "SAP access isn't available"
injection is a real, live 401 the student has to hit themselves (mirroring
FDE-005's already-proven "reaches the student unchanged" behavior), not
something narrated by a persona. A second mock scenario stands in for a
system that *is* reachable but exhibits schema drift across calls — the
undocumented-dependency-to-flag half of the stage.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[2]` with a persona (the
   platform architect handing over the outdated diagram and integration
   list on request) and `config["legacy_system"]` pointing at the mock's
   `acme-crm` scenario with `auth_header_name` set — calling it without
   credentials the student doesn't have SHALL return the mock's real
   unhelpful 401 (`ERR-4471`), standing in for the stuck-in-procurement SAP
   access gap.
2. THE persona SHALL, only on request, confirm that SAP access is stuck in
   procurement and describe a second, reachable integration point (the
   warehouse/inventory system) as returning an inconsistent schema between
   calls — the platform supports one `config["legacy_system"]` per instance
   today (FDE-005), so this second system's undocumented behavior is
   conveyed through the persona's account rather than a second live proxy
   call; extending the mock config to multiple systems is out of this
   story's scope.
3. THE `compliance_checklist` SHALL gate the C4 + Dependency Map deliverable
   on: evidence the student actually hit the blocked system (mentions the
   real `ERR-4471` code or `401`), evidence they noticed the reachable
   system's schema drift, and an explicit statement of how they're
   proceeding without full access (mentions `procurement`).
4. WHEN `GLOBAL_RETAIL_STAGES` is passed to `POST /engagements/global-retail`,
   THE resulting engagement SHALL now have 3 stages; stage 2's
   `config["legacy_system"]` SHALL be present and valid against the shape
   `app/routers/legacy_system.py` already expects (FDE-005), unchanged by
   this story.

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[2]` authored (persona + legacy_system config +
      compliance_checklist)
- [x] Tests: stage 2 config validates, legacy_system shape matches FDE-005's
      router expectations, hitting it unauthenticated 401s with the real
      mock body (monkeypatched-httpx pattern, matching FDE-005's own
      tests — no live mock service running in this dev environment),
      compliant deliverable passes the checklist, each missing element
      fails its rule, launching includes stage 2's legacy_system config
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[2]` in
`backend/app/engagement_content/global_retail.py`. `legacy_system` points
at FDE-005's `acme-crm` mock scenario (`auth_header_name: "X-Legacy-Auth"`)
— calling `GET /scenario-instances/{id}/legacy-system` without that header
returns the mock's real `ERR-4471` 401 through the existing FDE-005 proxy
unchanged, so "SAP access is stuck in procurement" is a genuine blocked
call, not a narrated one. Persona (Taylor Brooks, Platform Architect)
reveals the outdated network diagram, confirms the procurement gap, and
describes the second (schema-drifting) integration point only on request —
scaled back from the story draft's original AC2 (a second live legacy-system
call) once implementation confirmed `config["legacy_system"]` only supports
one system per instance today; extending it to multiple is out of scope for
a content-only story, so that finding is conveyed through the persona's
account instead, same mechanic as Stages 0–1.

`compliance_checklist` requires the literal `ERR-4471` code (proof of a real
attempted call, not just "I got an error"), the word "schema" (the
drift finding), and "procurement" (the explicit proceed-without-access
decision).

Also fixed forward-compatibility bugs in Stage 0/1's own tests:
`test_global_retail_stage1.py`'s "yields two stages" test hardcoded
`len(stages) == 2`, which broke the moment this story appended a third —
changed to assert on stage 1 specifically (`>= 2` total) so it stays valid
as later stories keep appending, and gave the equivalent stage-2 test the
same `>=` treatment up front.

Tests: `backend/tests/test_global_retail_stage2.py` (9 tests) — config
validates, no technical_task/data_gen, legacy_system shape matches the
router's expected fields, persona doesn't dump facts unprompted, launching
includes stage 2's legacy_system config, an unauthenticated call gets the
real 401 body through the actual proxy endpoint, compliant map passes,
and three negative cases (missing error code / schema mention /
procurement mention) each fail their specific rule. Full backend suite:
173 passed (up from 163 before this story).
