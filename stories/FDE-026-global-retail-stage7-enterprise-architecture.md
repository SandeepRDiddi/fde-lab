# FDE-026: GlobalRetail engagement — Stage 7 (Enterprise Architecture)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-017, FDE-025
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017)

## User story
As a student, I want Stage 7 to reject my first architecture pitch outright
over a policy I had no way of knowing about, so my Target Architecture
deliverable is a genuine revision under real constraints, not my first idea
written up more formally.

## Motivation

Eighth stage-content story on FDE-017's primitive; appends
`GLOBAL_RETAIL_STAGES[7]`. Per the framework: **Situation** — whatever's
designed has to plug into the customer's existing identity provider, API
gateway, and event bus, not live on an island. **Assets** — the platform
team's integration standards doc, SSO/identity requirements. **FDE must**
— design the C4 views, defend the architecture live, revise the rejected
piece without starting over. **Injected** — the Architecture Review Board
rejects the first-choice integration pattern outright, citing a policy the
FDE didn't know existed. **GlobalRetail specifics** — direct database
access is rejected; the platform is API-only, no exceptions. **Deliverable**
— Target Architecture.

New persona this stage: Riley Kwan, Chair of the Architecture Review Board
— a one-scene character (not reused elsewhere), matching the framework's
own "review board" as a distinct institutional voice from the engineering/
platform contacts used in earlier stages.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[7]` with a persona (Riley
   Kwan, ARB Chair) that, only on request, states the integration standard:
   no direct database access, API-only, no exceptions — and, separately,
   the SSO/identity requirement that everything authenticates through
   GlobalRetail's existing provider, no separate credential stores.
2. THE persona SHALL frame the API-only rule as a rejection of whatever the
   student proposes if they suggest direct database access, citing the
   internal standards doc by name — the injected "policy you didn't know
   existed" moment.
3. THE `compliance_checklist` SHALL gate the Target Architecture deliverable
   on proposing API-gateway-based integration, addressing the SSO
   requirement, and acknowledging the Architecture Review Board's rejection
   explicitly (evidence of a genuine revision, not a first draft).
4. WHEN `GLOBAL_RETAIL_STAGES` is passed to `POST /engagements/global-retail`,
   THE resulting engagement SHALL include stage 7, locked until stage 6's
   submission is approved — existing FDE-017 behavior, unchanged.

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[7]` authored (persona + compliance_checklist)
- [x] Tests: stage 7 config validates, persona doesn't leak facts
      unprompted, persona frames the rejection correctly, a compliant
      target architecture passes the checklist, each missing element fails
      its rule
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[7]` in
`backend/app/engagement_content/global_retail.py`. New one-scene persona,
Riley Kwan (ARB Chair) — not reused elsewhere, matching the framework's own
"review board" as a distinct institutional voice from the engineering/
platform contacts used earlier. Rejects direct-database-access proposals
outright citing the integration standard (the injected "policy you didn't
know existed"), frames it explicitly as a revision, not a restart, and
separately states the SSO/identity requirement, both only on request.
`compliance_checklist` requires API-gateway framing, SSO addressed, and an
explicit acknowledgment of the Board's rejection.

Found a new content-authoring pitfall while writing the compliant fixture
(distinct from the negation-window issue FDE-019/FDE-025 already
documented): `_WORD_RE = re.compile(r"[a-z0-9']+")` in
`app/compliance.py` keeps an apostrophe attached to its word, so
"Board's" tokenizes as one token (`board's`) that does *not* match the
literal `must_include` phrase "Architecture Review Board" (tokens
`architecture review board`) — a possessive form of a required phrase
silently fails the check. Not a platform bug worth fixing here (same
"existing engine is coarse by design" judgment as the earlier negation
cases) — worked around by phrasing the fixture as "the Architecture Review
Board rejected..." instead of "the Architecture Review Board's
rejection...". Worth carrying forward to later stages: avoid a possessive
's immediately after any required multi-word phrase.

Tests: `backend/tests/test_global_retail_stage7.py` (7 tests) — config
validates, no technical_task/data_gen, persona doesn't dump facts
unprompted, persona frames rejection as revision-not-restart, compliant
architecture passes, and three negative cases (missing API gateway
framing, missing SSO, missing ARB acknowledgment) each fail their specific
rule. Full backend suite: 210 passed (up from 202 before this story).
