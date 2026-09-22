# FDE-018: GlobalRetail engagement — Stage 0 (Mission Briefing)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-004, FDE-017
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017)

## User story
As a student, I want my first engagement stage to actually feel like being
dropped into an existing, messy account — a kickoff email, a partial org
chart, an abandoned vendor deck — so that my first deliverable is "figure out
who I report to and what's out of scope," not a generic "welcome" screen.

## Motivation

This is the first of the 22 stage-content stories riding on FDE-017's
sequencing primitive. It intentionally authors *only* Stage 0 ("FDE Mission
Briefing," Mission 1: Discover) from the FDE Engagement Framework artifact —
later stories (FDE-019 onward) each append one more stage to the same
growing content module, so `GLOBAL_RETAIL_STAGES` gets one entry longer per
merged story and the real, launchable GlobalRetail engagement grows
incrementally rather than needing all 22 written before anything is usable.

Per the framework: **Situation** — you've been deployed into an existing
customer environment, mid-history, with two prior failed attempts behind
you. **Assets provided** — kickoff email, partial org chart, the abandoned
vendor deck, scope/NDA boundaries. **FDE must** — read the account history,
identify who they actually report to, map named stakeholders, note what's
explicitly out of scope. **Deliverable** — Engagement Brief.

No technical task or dataset here (this is a narrative/discovery stage, not
a data task) — the deliverable is a written brief, and the persona is the
account contact who onboards the student and holds the facts they need to
extract by asking, not by being handed a document dump upfront.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[0]` as a valid
   `EngagementStageCreate`-shaped config: a `persona` (system prompt +
   agenda) for the onboarding contact, and a `compliance_checklist` that
   gates the Engagement Brief on covering the three required elements
   (reporting line, named stakeholders, out-of-scope items) plus a minimum
   length — no `technical_task`, no `data_gen`, matching the stage's
   narrative nature.
2. THE persona's system prompt SHALL encode the two-prior-failed-attempts
   backstory and hold the specific facts (who the student reports to, at
   least two named stakeholders, at least one explicit out-of-scope item)
   so a student who asks good questions can extract all three — the facts
   SHALL NOT be dumped in the opening message unprompted.
3. WHEN `GLOBAL_RETAIL_STAGES` (currently length 1) is passed as the
   `stages` list to `POST /engagements`, THE resulting engagement SHALL be
   created successfully and stage 0 SHALL be immediately active, per
   FDE-017's existing behavior — this story adds content, not new mechanism.
4. THE backend SHALL expose `POST /engagements/global-retail` as a
   convenience endpoint that launches an engagement from the current
   `GLOBAL_RETAIL_STAGES` content for a given cohort/student, so an
   instructor doesn't have to hand-assemble the stages list.

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[0]` authored (persona + compliance_checklist)
- [x] `POST /engagements/global-retail` launches successfully from current
      content (length 1 today, grows as later stories append)
- [x] Tests: stage 0 config validates against `EngagementStageCreate`, a
      compliant brief passes the checklist, one missing each required
      element fails it, persona system prompt doesn't leak the facts
      unprompted (content-level assertion, not an LLM judge)
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — New `backend/app/engagement_content/global_retail.py`:
`GLOBAL_RETAIL_STAGES`, a list of `EngagementStageCreate`-shaped configs
appended to one-per-story. Stage 0's persona (Dana Whitfield, IT Program
Manager) holds three canonical facts — reports-to (Marcus Chen), two named
stakeholders (Priya Anand, Jordan Lee), one out-of-scope item (POS system
replacement) — with an explicit "do not volunteer unprompted" instruction in
the system prompt (AC2). `compliance_checklist` gates the Engagement Brief
on all three plus a 200-char minimum length, using exact-name
`must_include` rules since this is scripted/canonical content, not a
per-student generated scenario (AC1) — no `technical_task`/`data_gen`, per
the stage's narrative nature.

`backend/app/routers/engagements.py`: refactored the stage-persisting body
of `create_engagement` into a shared `_create_engagement` helper, and added
`POST /engagements/global-retail` (AC4) — takes just `cohort_id`/
`student_id`, builds the stages list from `GLOBAL_RETAIL_STAGES` itself, so
launching the worked-example engagement doesn't require the caller to
hand-assemble stage configs. Currently launches a 1-stage engagement; the
list (and therefore what this endpoint launches) grows as FDE-019 onward
each append their own stage.

Tests: `backend/tests/test_global_retail_stage0.py` (7 tests) — stage 0
validates as an `EngagementStageCreate`, has no technical_task/data_gen,
persona prompt contains the no-unprompted-dump instruction, launching via
the new endpoint activates stage 0, a compliant brief passes the checklist
end-to-end via a real submission, and two negative cases (missing the
out-of-scope mention, missing a named stakeholder) fail the expected rule
via direct `evaluate_submission` calls. Full backend suite: 155 passed
(148 pre-existing after FDE-017 + 7 new).
