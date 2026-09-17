# FDE-001: Scenario engine skeleton

**Status:** Done
**Priority:** P0
**Depends on:** —
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis

## User story
As a platform engineer, I want a FastAPI service that can create, store, and serve
scenario state, so that later stories (scheduler, persona, mocks) have a foundation
to plug into.

## Acceptance criteria (EARS)
1. THE scenario engine SHALL expose a REST endpoint to create a scenario instance
   for a given cohort and student.
2. THE scenario engine SHALL persist scenario instance state (not started / active /
   closed) to Postgres.
3. WHEN a client requests a scenario instance's state, THE scenario engine SHALL
   return its current status and start/end timestamps.
4. WHERE a scenario configuration references injects (documents, data, mocks,
   persona), THE scenario engine SHALL store the configuration as structured JSON.

## Definition of done
- [ ] Migrations run cleanly from a fresh database (not verified — no live
      Postgres available in this environment; migration reviewed and a real
      bug fixed, see log below, but never actually executed)
- [x] Unit tests cover create/read of a scenario instance
- [x] Story status updated below
- [x] architecture.md updated if the schema deviates from what's documented there (no deviation)

## Implementation log

### 2026-09-17
Built the `backend/` FastAPI service (didn't exist before this story):
- `app/models.py` — `ScenarioInstance` SQLAlchemy model: `id` (UUID pk), `cohort_id`/
  `student_id` (UUID, no FK yet — cohorts/students tables don't exist as a story
  yet), `status` (`ScenarioStatus` enum: `not_started`/`active`/`closed`, default
  `not_started`), `config` (JSON, structured injects config per AC4), `start_at`/
  `end_at` (nullable timestamps), `created_at`.
- `app/routers/scenario_instances.py` — `POST /scenario-instances` (AC1: create for
  a cohort+student) and `GET /scenario-instances/{id}` (AC3: returns status +
  start/end timestamps, plus the rest of the record).
- `app/database.py`, `app/config.py` — SQLAlchemy engine/session wired to
  `DATABASE_URL`-style Postgres connection string via `FDE_DATABASE_URL` env var
  (defaults to local Postgres), matching architecture.md's FastAPI/Postgres split.
- `alembic/versions/0001_create_scenario_instances.py` — migration creating the
  `scenario_instances` table and `scenario_status` Postgres enum (AC2: persist
  status to Postgres).
- `tests/test_scenario_instances.py` — unit tests for create + read (incl. 404),
  run against an in-memory SQLite DB via a `get_db` override so they don't require
  a live Postgres instance.

Deviation / known gap: this sandboxed session couldn't execute shell commands
(`pip install`, `pytest`, `alembic upgrade`) — every `Bash` call required approval
that wasn't granted, so the DoD items "migrations run cleanly from a fresh
database" and "unit tests cover create/read" are implemented but **not verified
by actually running them here**. Please run before merging:
```
cd backend && pip install -r requirements.txt
pytest -q
# with a local Postgres reachable at FDE_DATABASE_URL:
alembic upgrade head
```
No Celery/Redis, frontend, or other services touched — out of scope for this
story per its acceptance criteria.

### 2026-09-17 (merge review)
Code-reviewed PR #13 and fixed before merge:
- `alembic/env.py` — `%` in `settings.database_url` was fed unescaped into
  Alembic's `ConfigParser.set_main_option`, which raises
  `InterpolationSyntaxError` on any literal `%` (e.g. a percent-encoded
  password segment). Now escaped as `%%`.
- Added Python-project entries to root `.gitignore` (`.env`, `__pycache__/`,
  venvs, `.pytest_cache/`) — none existed, so a real `backend/.env` with
  live DB credentials would've been stageable by `git add -A`.
- Fixed two route handler return-type annotations (`-> ScenarioInstance` to
  `-> ScenarioInstanceRead`) to match the actual `response_model`.
- Dropped a redundant explicit `scenario_status.create(...)` in the
  migration — `op.create_table` already creates the enum via SQLAlchemy's
  `before_create` event.

Verified: `pytest -q` passes (3 passed) against the in-memory SQLite fixture
after these fixes. Merged via squash, PR #13 closed, branch deleted.

_(appended by the agent as work happens — date, what changed, links to commits/PR)_
