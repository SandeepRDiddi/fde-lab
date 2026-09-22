# FDE-028: GlobalRetail engagement — Stage 9 (Build the AI Capability)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-017, FDE-027
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017)

## User story
As a student, I want Stage 9 to hand me a genuinely flaky downstream API
and a documented case where retrieval confidently returns the wrong answer,
so the "working AI service" I design actually has to account for both
failure modes instead of assuming the happy path.

## Motivation

Tenth stage-content story on FDE-017's primitive, and the first stage of
Mission 3 (Engineer); appends `GLOBAL_RETAIL_STAGES[9]`. Per the framework:
**Situation** — time to build the real thing: retrieval over the
customer's own documents, tool calls into their live systems. **Assets** —
the semantic model, the data contracts, sandboxed access to mocked versions
of the customer's core endpoints. **FDE must** — build the RAG and
tool-calling core, and notice both failure modes below instead of shipping
past them. **Injected** — a downstream API occasionally returns a bare HTTP
500 with no explanation, and vector search hands back a fluent, confident,
wrong answer on an ambiguous query. **GlobalRetail specifics** — the
supplier-lookup API is the flaky one; the wrong answer surfaces on an
ambiguous supplier-substitution question. **Deliverable** — Working AI
Service.

Scope note: this repo has no vector-search/RAG service (see `CLAUDE.md`'s
service list) and FDE-005's legacy-api mock has no "intermittent 500"
scenario built (only a 200-cycling response set, or a 401 when an
`auth_header` is configured and missing — no code path returns 500 at all).
Building either a real vector-search component or extending the mock's
scenario schema with a new failure mode is a platform-level change out of
this content story's scope (same judgment FDE-020 already applied when it
scaled back a second live legacy-system call). Both failure modes are
therefore persona-narrated, same ask-to-reveal mechanic as Stages 0/1/3–6,
and the deliverable is a design/build writeup graded on whether it actually
accounts for both — not runnable RAG/tool-calling code, which nothing in
this platform can execute or grade yet.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[9]` with a persona
   (Taylor Brooks, continuing the technical thread from Stages 2/3/6)
   that, only on request, describes the supplier-lookup API's intermittent
   bare-500 behavior and the vector search's confident-wrong-answer failure
   on an ambiguous supplier-substitution question.
2. THE `compliance_checklist` SHALL gate the Working AI Service deliverable
   on addressing resilience for the flaky API (mentions retry) with
   evidence the student engaged with the specific failure (mentions the 500
   status), and on addressing the ambiguous-query failure mode (mentions
   both "ambiguous" and a mitigation like a clarifying question).
3. WHEN `GLOBAL_RETAIL_STAGES` is passed to `POST /engagements/global-retail`,
   THE resulting engagement SHALL include stage 9, locked until stage 8's
   submission is approved — existing FDE-017 behavior, unchanged.

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[9]` authored (persona + compliance_checklist)
- [x] Tests: stage 9 config validates, persona doesn't leak facts
      unprompted, persona encodes both injected failure modes, a compliant
      writeup passes the checklist, each missing element fails its rule
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[9]` in
`backend/app/engagement_content/global_retail.py`, opening Mission 3
(Engineer). Persona continues as Taylor Brooks (Stages 2/3/6). Both
injected failure modes (flaky supplier API, confidently-wrong ambiguous
retrieval) are persona-narrated rather than live/executable — confirmed
during implementation that this repo has no vector-search/RAG service at
all, and FDE-005's legacy-api mock's `scenario_loader.py` only ever returns
a 200 (cycling through `responses`) or a 401 (missing configured
`auth_header`) — there is no code path that returns 500, so a live
"intermittent 500" couldn't be wired the way Stage 2 wired a live 401
without first extending the mock service itself, a platform-level change
out of this content story's scope (same judgment FDE-020 already made for
a second live legacy-system call).

Hit the same negation-window pitfall as FDE-019/025 while writing the
compliant fixture: "returns a bare 500 with no explanation" put "no" two
tokens after "500," which would have made `must_include("500")` fail on
its only occurrence. Rewrote as two sentences ("...returns a bare 500; the
response body carries nothing else to act on...") to keep the negation
word out of the 3-token window — "nothing" tokenizes as one word, not "no",
so it doesn't trip the heuristic at all.

`compliance_checklist` requires retry-based resilience for the flaky API
with evidence of the specific 500 (not just "handles errors" abstractly),
and both naming the ambiguous-query failure and proposing a concrete
mitigation (a clarifying question).

Tests: `backend/tests/test_global_retail_stage9.py` (8 tests) — config
validates, no technical_task/data_gen/legacy_system, persona doesn't dump
facts unprompted, persona encodes both failure modes, compliant writeup
passes, and two negative cases (missing retry, missing the clarifying-
question mitigation) each fail their specific rule. Full backend suite:
225 passed (up from 218 before this story).
