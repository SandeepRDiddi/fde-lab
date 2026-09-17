# FDE-002: Time-box scheduler

**Status:** Done
**Priority:** P0
**Depends on:** FDE-001
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis

## User story
As an instructor, I want scenarios to automatically unlock and close on the schedule
I configure, so that the cohort experiences a time-boxed engagement without manual
intervention.

## Acceptance criteria (EARS)
1. WHEN an instructor sets a start and end time for a scenario instance, THE
   scheduler SHALL enqueue an unlock job and a close job in Celery/Redis for those
   times.
2. WHEN the unlock job fires, THE scenario engine SHALL transition the scenario
   instance to "active" and notify the student.
3. WHEN the close job fires, THE scenario engine SHALL transition the scenario
   instance to "closed" and lock further submissions.
4. IF an instructor configures a mid-scenario pivot time, THEN THE scheduler SHALL
   enqueue a pivot job that injects the configured change at that time.

## Definition of done
- [x] Scheduled jobs verified against a test cohort with compressed timings (eager-mode
      test suite; no live Redis/worker in this environment — see merge review below)
- [x] Story status updated below
- [x] architecture.md updated if the scheduling model deviates from what's documented (no deviation)

## Implementation log

### 2026-09-17
Built the time-box scheduler on top of the FDE-001 `backend/` skeleton:
- `app/models.py` — added `pivot_at`, `pivot_config` (JSON), `pivot_applied_at`,
  `notified_at` columns to `ScenarioInstance`.
- `app/celery_app.py` — new Celery app, Redis broker/backend from
  `FDE_REDIS_URL` (new setting in `app/config.py`, defaults to local Redis).
- `app/tasks.py` — three tasks: `unlock_scenario_instance` (AC2: status →
  `active`, sets `notified_at`), `close_scenario_instance` (AC3: status →
  `closed`), `apply_scenario_pivot` (AC4: merges `pivot_config` into `config`,
  sets `pivot_applied_at`; no-ops if no `pivot_config` set).
- `app/schemas.py` / `app/routers/scenario_instances.py` — new
  `POST /scenario-instances/{id}/schedule` endpoint (AC1/AC4): instructor
  submits `start_at`/`end_at`/optional `pivot_at`+`pivot_config`; validates
  `end_at > start_at` and `start_at < pivot_at < end_at`, persists the
  schedule, then enqueues the unlock/close/pivot jobs via `apply_async(eta=...)`.
- `alembic/versions/0002_scenario_instance_scheduling.py` — migration for the
  new columns.
- `requirements.txt` — added `celery[redis]`.
- `tests/test_tasks.py` — unit tests for each task's DB transition, run
  against an in-memory SQLite DB via a monkeypatched `SessionLocal` (tasks use
  their own DB session, not the FastAPI `get_db` dependency).
- `tests/test_scheduler.py` — integration tests for the schedule endpoint
  (enqueue + validation), and `tests/conftest.py` — `client` fixture now also
  points `app.tasks.SessionLocal` at the test DB and flips Celery to
  `task_always_eager` so scheduled jobs fire synchronously in-process against
  compressed (second-scale) timings, with no live Redis/worker needed.

AC3 ("lock further submissions") is implemented as far as this story's scope
reaches: the instance transitions to `status = closed`. There is no
submission endpoint yet (that's FDE-008, student workspace) — enforcement
("reject writes when closed") belongs there and should check this field when
built.

No deviation from architecture.md — Celery/Redis stays in the FastAPI
backend as documented, nothing split into a separate service.

Same environment limitation as FDE-001: this sandboxed session could not run
shell commands (`pip install`, `pytest`, `alembic upgrade`) — every `Bash`
call required approval that wasn't granted. Implemented and tests written,
but **not executed here**. Please run before merging:
```
cd backend && pip install -r requirements.txt
pytest -q
# with a local Postgres reachable at FDE_DATABASE_URL:
alembic upgrade head
```

### 2026-09-17 (merge review)
Code-reviewed PR #14 and fixed before merge — two CONFIRMED bugs, plus
smaller gaps:
- Rescheduling never cancelled the previous schedule's unlock/close/pivot
  Celery jobs, so a reschedule left the old jobs pending to fire at their
  stale times alongside the new ones. Added `unlock_task_id`/`close_task_id`/
  `pivot_task_id` columns (migration `0003`) and revoke the previous ids on
  reschedule (best-effort — skipped under eager execution, where the prior
  jobs already ran synchronously before the reschedule call).
- `apply_scenario_pivot` checked only `pivot_config` truthiness, not
  `pivot_applied_at`, so a redelivered/retried task could silently re-merge
  a since-changed `pivot_config`. Now checks `pivot_applied_at is None` too.
- `ScenarioInstanceSchedule` allowed naive datetimes, which crashed the
  `end_at <= start_at` comparison with an unhandled 500 instead of a clean
  422 if one field's timezone offset got dropped. Added a validator
  rejecting naive input.
- `conftest.py`'s `client` fixture flipped `task_always_eager` globally and
  never reset it — fixed to restore the prior value on teardown.
- Enqueue order changed to chronological (unlock, pivot, close) so
  eager-mode tests exercise the same sequence real ETA scheduling would.
- Instance wasn't refreshed after scheduling, so the response could
  under-report state a task already committed via its own session under
  eager execution — added a `db.refresh` before returning.

Added tests: pivot idempotency (`test_pivot_task_is_idempotent`), naive
datetime rejection, and reschedule revocation
(`test_reschedule_revokes_previous_jobs`, faking `apply_async`/`revoke` so
it runs without a live broker). `pytest -q` now passes: 17 passed. Merged
via squash, PR #14 closed, branch deleted.

_(appended by the agent as work happens)_
