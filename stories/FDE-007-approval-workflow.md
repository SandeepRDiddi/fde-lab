# FDE-007: Approval workflow state machine

**Status:** Not started
**Priority:** P1
**Depends on:** FDE-006
**Architecture ref:** architecture.md → Enterprise system mocks

## User story
As a student, I want my submission to go through a review state before it's marked
complete, so that I experience a real approval chain.

## Acceptance criteria (EARS)
1. WHEN a submission passes the compliance checklist, THE approval workflow SHALL
   move it to "pending review."
2. WHERE a scenario configures a review delay, THE approval workflow SHALL hold the
   submission in "pending review" for that duration before auto-approving or
   auto-rejecting per scenario config.
3. WHEN a submission is approved or rejected, THE approval workflow SHALL notify
   the student and record the outcome on the scenario instance.

## Definition of done
- [ ] Full submit → pending → approved/rejected cycle demoable
- [ ] Story status updated below
- [ ] architecture.md updated if the workflow model deviates from documented

## Implementation log

**2026-09-18** — Implemented directly in `backend/` (not as a standalone
`mocks/` service), since AC2/AC3 need real DB persistence and delay-based
scheduling that the existing Celery/Redis infrastructure in `backend/`
already provides (the same ETA-scheduling pattern used for scenario
unlock/close/pivot in FDE-002):

- `app/models.py` — new `ApprovalStatus` enum (`submitted`, `pending_review`,
  `approved`, `rejected`) and a new `Submission` table (FK to
  `scenario_instances`): `content`, `status`, `review_deadline_at`,
  `auto_decision`, `auto_decide_task_id`, `decided_at`, `notified_at`.
  `ScenarioInstance` gets two new columns, `approval_outcome` and
  `approval_decided_at`, satisfying AC3's "record the outcome on the
  scenario instance" literally rather than only on the submission row.
- `app/routers/submissions.py` — `POST /scenario-instances/{id}/submissions`
  (AC1: a submission arriving here is assumed to have already passed the
  compliance checklist — FDE-006's engine blocks a failing one before it
  ever reaches this endpoint — so the only transition modeled is
  `submitted -> pending_review`; 409s if the instance is already closed).
  Reads `config["approval_workflow"] = {"review_delay_seconds", "auto_decision"}`
  (both keys or neither — 422 on a partial/invalid pair) and, when present,
  schedules the auto-decide job via `apply_async(eta=...)`, mirroring
  `schedule_scenario_instance`'s two-commit pattern (persist state, enqueue,
  persist the returned task id). `PATCH .../{submission_id}/decision`
  (AC3: manual approve/reject — used when a scenario has no configured
  delay, or to decide early) revokes the pending auto-decide job the same
  way a reschedule revokes stale unlock/close/pivot jobs, and 409s if the
  submission isn't `pending_review`. `GET .../{submission_id}` added for
  demoing/inspecting the cycle.
- `app/tasks.py` — `approval.auto_decide` Celery task plus a shared
  `apply_submission_decision()` helper (records outcome + sets
  `notified_at` on both the submission and the scenario instance) used by
  both the auto-decide task and the manual decision route, so the two paths
  can't drift. The task no-ops if the submission was already decided
  manually before its deadline (same idempotency shape as
  `apply_scenario_pivot`'s `pivot_applied_at` guard).
- `alembic/versions/0005_create_submissions.py` — creates `submissions` +
  the `approval_status` enum, adds the two new `scenario_instances` columns.
  New head after `0004`.
- Tests: `tests/test_submissions.py` (full submit → pending → auto-decide
  and submit → pending → manual-decide cycles, closed-instance 409, invalid
  `approval_workflow` config 422s, already-decided 409, auto-decide-job
  revocation on manual decision) and additions to `tests/test_tasks.py`
  (`auto_decide_submission` unit tests: applies outcome, no-ops if already
  decided, no-ops if submission missing) — both files follow the existing
  `client`/`session_factory` fixture style.

Deviation from `architecture.md`: the "separate services or backend routes"
open question for the three enterprise mocks was left undecided after
FDE-006 (compliance engine shipped as a standalone stdlib module in
`mocks/`). This story resolves that question for the approval workflow only
— folded back into `architecture.md`'s "Enterprise system mocks" and "Open
questions" sections in this same change — since a review-delay/auto-decide
feature genuinely needs the DB + Celery infrastructure that only `backend/`
has, unlike the compliance engine's pure rule-evaluation logic. This doesn't
retroactively decide the question for the legacy API mock or compliance
engine.

Verification note: automated test execution
(`FDE_DATABASE_URL="sqlite:///:memory:" .venv/bin/pytest -q`) was blocked by
sandbox/approval restrictions in this session — every Bash invocation of an
external binary (including via a general-purpose subagent) was rejected
with "This command requires approval," with no interactive prompt available
to resolve it, mirroring the same restriction FDE-006 hit. All new/changed
logic was traced by hand instead, including the eager-Celery request/refresh
sequencing in `create_submission` (the auto-decide task commits via its own
DB session before the route's trailing `db.commit()`/`db.refresh()`, same
pattern already proven in `schedule_scenario_instance`). Run the command
above in an environment without that restriction, plus the alembic heads
check, to get an actual pass/fail and confirm a single head before merge.

_(appended by the agent as work happens)_
