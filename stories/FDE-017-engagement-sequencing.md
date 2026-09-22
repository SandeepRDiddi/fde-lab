# FDE-017: Engagement sequencing primitive

**Status:** Done
**Priority:** P0
**Depends on:** FDE-001, FDE-002, FDE-007
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis

## User story
As an instructor, I want to launch one continuous, multi-stage engagement for
a cohort — not 22 disconnected scenario instances — so that a decision a
student makes in an early stage (e.g. the semantic model they define) is the
thing a later stage actually builds on, and the next stage only opens once
the current one is genuinely done, not on a fixed clock.

## Motivation

Every scenario instance today (FDE-001/002) is a standalone 1:1 unit: one
`config`, one dataset, one technical task, one time-box, at most one scripted
time-triggered pivot. That's the right shape for a single lab, but it can't
express "The FDE Engagement Framework" artifact the instructor is now
building from — 22 stages across 6 missions where later stages consume
earlier stages' output (Stage 6's semantic model feeds Stage 9's build;
Stage 8's data contracts get referenced again in Stage 19's change request)
and progression is gated on the student's submission being approved, not on
a timer. Confirmed via a live-code survey (not just the architecture doc,
which is stale on some of this — e.g. it references a `team` concept that
doesn't exist in `backend/app` at all): `ScenarioInstance` has no
stages/ordering table, FDE-002's `pivot_at` supports exactly one time-fired
JSON merge (not an event fired by submission approval, not more than one),
and there is zero cross-instance linkage today beyond a shared
`cohort_id`/`student_id`. This story adds the missing primitive; it
deliberately does not author any of the 22 stages' content — that's
FDE-018 onward, each depending on this one.

## Design direction (non-binding on implementation details, binding on shape)

- A new `Engagement` row groups an ordered sequence of `ScenarioInstance`s
  (`engagement_id` + `stage_order` added to `ScenarioInstance`, nullable —
  a standalone scenario instance with no engagement is still valid and
  unchanged).
- `Engagement` owns a `context` JSON column that accumulates across stages
  (each stage can read everything written so far, and appends/merges its
  own output on approval) — additive, not last-write-wins like today's
  `pivot_config` merge.
- Advancing to the next stage is triggered by the current stage's
  `approval_outcome` (FDE-007) turning "approved", not by a clock. A stage
  can still additionally carry FDE-002's existing time-box/pivot fields for
  in-stage timing (e.g. Stage 18's incident window) — this story adds a
  second, event-triggered advance path alongside the existing time-triggered
  one, it doesn't replace it.
- Advancing an engagement unlocks the next `ScenarioInstance` in sequence
  (same `unlock` mechanics FDE-002 already has, just triggered differently)
  and injects the accumulated `context` into that instance's `config` before
  it opens, so e.g. Stage 9's persona/task can reference Stage 6's semantic
  model verbatim.

## Acceptance criteria (EARS)
1. WHEN an instructor creates an engagement with an ordered list of stage
   configs, THE backend SHALL persist one `Engagement` row and one
   `ScenarioInstance` per stage, linked and ordered, with only the first
   stage unlocked.
2. WHEN a student's submission on the current stage of an engagement is
   marked "approved" (existing FDE-007 approval outcome), THE backend SHALL
   unlock the next stage's `ScenarioInstance` and merge the current
   engagement `context` plus that stage's own declared output into the next
   stage's `config` before it becomes visible to the student.
3. IF a stage is rejected (not approved), THEN THE backend SHALL NOT unlock
   the next stage — the current stage stays open for resubmission, mirroring
   FDE-007's existing rejection behavior on a single instance.
4. WHERE an engagement's last stage is approved, THE backend SHALL mark the
   `Engagement` complete and make its full accumulated `context` available
   read-only (for Stage 21's handover pack to consume, once authored).
5. THE existing single-instance time-box/pivot/close mechanics (FDE-002)
   SHALL continue to work unmodified for any `ScenarioInstance` not attached
   to an `Engagement`, and for in-stage timing on one that is.

## Definition of done
- [x] `Engagement` + `ScenarioInstance.engagement_id`/`stage_order` migration,
      one Alembic head after merge (check per CLAUDE.md's heads command)
- [x] Approval-triggered advance (AC2/3) implemented alongside, not
      replacing, FDE-002's time-triggered path
- [x] Context accumulation is additive across stages (AC2), not overwritten
- [x] Existing FDE-001/002/007 single-instance tests still pass unmodified
- [x] New tests: multi-stage create, approve-advances, reject-blocks,
      last-stage-completes-engagement, context accumulates correctly across
      3+ stages
- [x] Story status updated below
- [x] architecture.md updated (new subsection under Backend, and correct the
      stale `team` reference noted above while touching this section)
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — New `Engagement` model (`backend/app/models.py`): `id`,
`cohort_id`, `student_id`, `status` (`active`/`completed`), `context` (JSON,
accumulates per-stage output keyed by stage order as a string), timestamps.
`ScenarioInstance` gained nullable `engagement_id` (FK) + `stage_order` — both
null for a standalone instance, unaffected by any of this (AC5). Migration
`0007_create_engagements.py`, single Alembic head confirmed (`0007`).

New router `backend/app/routers/engagements.py`: `POST /engagements` (AC1 —
takes `cohort_id`/`student_id`/`stages: [{config}]`, creates one
`ScenarioInstance` per stage with `stage_order` 0..N-1, only stage 0 set
`active`, the rest default `not_started`, i.e. locked); `GET
/engagements/{id}` (chain + accumulated context, ordered by `stage_order`).
Reuses `scenario_instances.py`'s existing `_to_read_model` (answer-key
redaction) rather than duplicating it.

Advance logic lives in `app/tasks.py`'s new `_advance_engagement`, called
from the existing `apply_submission_decision` (shared by both the manual
decision route and FDE-007's auto-decide Celery task, so both paths trigger
engagement advance identically) only when the decision is `approved` and the
instance has an `engagement_id` (AC5 no-op otherwise). It records the
just-approved submission's `content`/`grading_result` into
`Engagement.context[str(stage_order)]` — a new key added each time, so
earlier stages' entries are never overwritten (AC2, "additive"). If a next
`ScenarioInstance` exists at `stage_order + 1`, its `config` gets
`engagement_context` set to the full updated context dict and its status
flips to `active` (unlock). If not, the `Engagement` itself is marked
`completed` (AC4). A rejected decision never calls `_advance_engagement` at
all — the current stage's existing FDE-007 behavior (stays open, can be
resubmitted) is completely unchanged (AC3).

`config["engagement_context"]` intentionally carries the *whole*
accumulated context (not just the immediately-preceding stage's), so a later
stage can reference any earlier stage's output directly — this is what lets
Stage 9's build reference Stage 6's semantic model even though Stage 7/8 sit
between them.

Tests: `backend/tests/test_engagements.py` (8 tests) — only-first-stage-
unlocked, approve-unlocks-next-and-carries-context, reject-blocks-and-allows-
resubmission, last-stage-approval-completes-engagement, context-accumulates-
across-3-stages (verifies stage 2 sees both stage 0 and stage 1's output),
standalone-instance-unaffected, empty-stages-list-rejected (422). Full
backend suite: 148 passed (up from 140 pre-existing — this story added 8, no
existing test needed changes). Alembic heads check: `['0007']`.

No `backend/.venv` existed yet in this environment (first time these commands
ran here) — created per CLAUDE.md's standard per-service venv pattern before
running tests.

architecture.md: new "Engagement sequencing (FDE-017)" subsection under
Backend, and the stale `intent.md` traceability row claiming a "team-scoped
submissions" data model (no `team` concept exists anywhere in
`backend/app` — confirmed by grep) corrected to describe what's actually
built (`Engagement` chains, no multi-student/team submission concept).
