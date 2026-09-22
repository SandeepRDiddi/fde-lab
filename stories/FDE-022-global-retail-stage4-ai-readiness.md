# FDE-022: GlobalRetail engagement — Stage 4 (AI Readiness Assessment)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-017, FDE-021
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017)

## User story
As a student, I want Stage 4 to hand me leadership's "we want an AI agent"
ask alongside a skeptical stakeholder and a use case that legally can't be
one, so my deliverable is a real classification with a defensible reason,
not an assumption that AI solves everything on the list.

## Motivation

Fifth stage-content story on FDE-017's primitive, and the last of Mission 1
(Discover); appends `GLOBAL_RETAIL_STAGES[4]`. Per the framework:
**Situation** — leadership's opening ask was "we want an AI agent"; not
every part of the problem should be one. **Assets** — the Stage 1
stakeholder wishlist, a rough inventory of candidate use cases spanning
lookups, investigation, and action. **FDE must** — sort each use case into
deterministic, AI-assisted, or agentic, and justify the split to a
skeptical stakeholder. **Injected** — one business rule has hard legal/
policy constraints, not judgment calls, and can't be left to an LLM.
**GlobalRetail specifics** — order status, delay root-cause, and supplier
escalation are fair game for AI; return-eligibility policy is not — it's
deterministic, full stop. **Deliverable** — AI Readiness Matrix.

Same mechanic as Stages 0–2 (persona + compliance_checklist prose) — this
stage is content authoring on the established pattern, not new mechanism.
The skeptical stakeholder is recast as Jordan Lee (already introduced as
the governance-focused IT Director in Stage 1) rather than a new character,
for continuity.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[4]` with a persona
   (Jordan Lee, skeptical of "AI does everything") holding four candidate
   use cases — order status lookup, delay root-cause investigation,
   supplier escalation, and return-eligibility determination — revealed
   only on request, same ask-to-reveal mechanic as prior stages.
2. THE persona SHALL encode the injected legal constraint explicitly:
   return-eligibility determination is governed by consumer protection law
   and cannot be delegated to an LLM's judgment, full stop — not a
   judgment call like the other three.
3. THE `compliance_checklist` SHALL gate the AI Readiness Matrix on
   classifying all four use cases correctly (lookup → deterministic,
   investigation → AI-assisted, action → agentic, return-eligibility →
   deterministic with the legal justification named) — the closest this
   rule engine gets to checking "correct classification with justification"
   without a live model judge.
4. WHEN `GLOBAL_RETAIL_STAGES` is passed to `POST /engagements/global-retail`,
   THE resulting engagement SHALL include stage 4, locked until stage 3's
   submission is approved — existing FDE-017 behavior, unchanged.

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[4]` authored (persona + compliance_checklist)
- [x] Tests: stage 4 config validates, persona doesn't leak facts
      unprompted, persona encodes the legal constraint, a compliant matrix
      passes the checklist, each missing classification fails its rule
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[4]` in
`backend/app/engagement_content/global_retail.py`, completing Mission 1
(Discover: Stages 0-4). Persona is Jordan Lee, reused from Stage 1
(governance-focused IT Director) rather than a new character, cast here as
the skeptical stakeholder pushing back on "AI does everything." Reveals the
four-use-case list and the injected legal constraint (return-eligibility
governed by consumer protection law, no LLM in that decision path) only on
request. `compliance_checklist` requires all four classifications by name
(deterministic / AI-assisted / agentic / deterministic-with-legal-
justification).

Hit a variant of FDE-019's negation-fixture lesson while writing the
negative test for the "deterministic" rule: the compliant fixture uses the
word "deterministic" twice (once for the lookup, once for
return-eligibility), so stripping only the first occurrence left
`must_include("deterministic")` still satisfied by the second — not a
compliance-engine bug this time, just an artifact of choosing the same
classification word for two different use cases in one deliverable. Fixed
by stripping both occurrences in the test.

Tests: `backend/tests/test_global_retail_stage4.py` (8 tests) — config
validates, no technical_task/data_gen, persona doesn't dump facts
unprompted, persona encodes the legal constraint, compliant matrix passes,
and three negative cases (missing deterministic/agentic classification,
missing legal justification) each fail their specific rule. Full backend
suite: 187 passed (up from 179 before this story).

This closes out Mission 1 (Discover) of "The FDE Engagement Framework" —
Stages 0-4 all authored and gradable end to end via
`POST /engagements/global-retail`. Mission 2 (Architect, Stages 5-8) is
next (FDE-023 onward).
