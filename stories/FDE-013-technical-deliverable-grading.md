# FDE-013: Technical deliverable grading

**Status:** Done
**Priority:** P1
**Depends on:** FDE-001, FDE-003, FDE-006, FDE-007
**Architecture ref:** architecture.md → Enterprise system mocks / Data layer

## User story
As a student, I want my actual technical deliverable checked for correctness —
not just whether my write-up mentions the right words — so that the scenario
grades whether I solved the real problem, not how I described it.

## Motivation

Every scenario up to this point ends the same way: the student writes prose,
and `app/compliance.py` checks it for required/forbidden phrases and a
minimum length. That's a real gate (FDE-006/FDE-007), but it never checks
whether the student actually fixed anything — a well-worded description of a
fix that doesn't work passes exactly as well as one that does. A real FDE
engagement ends with a working artifact (a query, a script, a config) run
against the client's actual (messy) data, not a paragraph about one. This
story adds that gate for one concrete task type — a read-only SQL query,
graded by running it against the scenario's own synthetic dataset and
comparing its result to a reference query's — so "correct" means "produces
the right rows," not "used the right words."

## Acceptance criteria (EARS)
1. WHERE a scenario instance's `config["technical_task"]` is configured with
   `task_type: "sql_query"`, THE backend SHALL grade a submission by running
   it as a read-only query against the instance's own synthetic dataset and
   comparing its result set to `reference_query`'s.
2. IF the submitted query's result does not match the reference query's
   result (by the configured `compare` mode), THEN THE backend SHALL reject
   the submission (422) and name the mismatch, without persisting it.
3. IF the submitted content is not a single read-only `SELECT` statement,
   THEN THE backend SHALL reject it without executing it against the
   dataset.
4. WHEN a technical-task submission passes, THE backend SHALL record what
   was graded (`grading_result`) on the persisted submission, in addition to
   the existing compliance-checklist gate (both must pass).

## Definition of done
- [x] A scenario configured with `technical_task` is graded by execution, not
      by scanning submitted text
- [x] Story status updated below
- [x] architecture.md updated (new subsection; grading reuses the existing
      submission/compliance flow, not a competing one)
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-20** — Added `backend/app/grading.py`: `evaluate_sql_submission`
loads the scenario's dataset (`ScenarioInstance.dataset_location`, an
`s3://bucket/key` NDJSON file data-gen already produces — FDE-003) into an
in-memory SQLite table named `technical_task.table_name`, runs
`technical_task.reference_query` to get the expected result, then runs the
student's submitted content and compares result sets (`compare:
"unordered_rows"` by default, sorted-tuple comparison; `"ordered_rows"` for
exact order). Before executing anything, the submission must be a single
statement starting with `SELECT` and must not contain a write/schema keyword
(`insert`/`update`/`delete`/`drop`/`alter`/`create`/`attach`/`pragma`/etc.) —
AC3. `create_submission` (`backend/app/routers/submissions.py`) runs this
after the existing compliance-checklist gate when
`instance.config["technical_task"]` is set; either gate failing returns 422
with the same `{message, failures}` shape the compliance gate already used,
so the frontend's existing failure-list rendering needed no new code path —
AC1/AC2. A passing technical submission stores
`grading_result: {task_type, passed: true}` on the `Submission` row
(new nullable JSON column, migration `0006`) — AC4.

Dataset fetch uses `boto3` directly (added to `backend/requirements.txt`),
against the same MinIO bucket/credentials shape `data-gen/generator/config.py`
already uses — new `FDE_S3_*` settings in `backend/app/config.py`, wired in
`infra/docker-compose.yml`'s `backend` service (also added a
`minio-init: service_completed_successfully` dependency so the bucket exists
before backend serves). Not yet wired into the Helm chart
(`infra/k8s/chart/templates/backend.yaml`) — pre-existing gap, since
`FDE_LEGACY_API_BASE_URL` (FDE-005) wasn't wired there either and the chart
has never been run against a real cluster (see FDE-012's own log).

Frontend: `TechnicalTask` type added (`frontend/lib/types.ts`);
`SubmissionPanel` renders the task's instructions and a monospace textarea
when `instance.config.technical_task` is set, and reuses its existing
pass/fail rendering (the failure list shape — `{rule_id, description}` — is
identical between compliance and grading failures, so no new UI branch was
needed there). `InstructorConsole` shows "Auto-graded (sql_query): correct"
instead of the generic compliance line when a submission carries a
`grading_result`.

Security note: the disallowed-keyword check is a naive substring scan (a
query containing the literal text "drop" inside a string literal is also
rejected) — deliberately conservative for a training lab with trusted
students, not adversarial-input-hardened; `sqlite3`'s own single-statement
`execute()` and the in-memory-only connection (no `ATTACH`, no filesystem
access) are the actual containment, the keyword check is a clearer error
message on top of that, not the safety boundary itself.

Tests: `backend/tests/test_grading.py` (12 tests — correct query passes,
row-order-independent compare, dedup-missing query fails with
`result_mismatch`, non-`SELECT`/multi-statement/disallowed-keyword all
rejected pre-execution, malformed SQL surfaces `query_execution_error`,
missing dataset/`reference_query` raise `GradingError`, dispatch by
`task_type`, unknown `task_type` raises) plus three new integration tests in
`backend/tests/test_submissions.py` (technical-task submission rejects a
wrong query, accepts a correct one and records `grading_result`, 422s
cleanly when the instance has no dataset yet) — all via a fake S3 client
(`monkeypatch.setattr("app.grading.boto3.client", ...)`), same pattern as
`test_legacy_system.py`'s `httpx.get` fake. Full backend suite: 72 passed.
`npm run typecheck` / `npm run build`: clean.

Verified live: brought the updated `backend`/`frontend` images up in the
running Docker Compose stack, created a scenario instance with a real
`ecommerce_orders` dataset (data-gen, uploaded to the actual MinIO bucket)
and a `technical_task` deduping that dataset's `order_id`, then exercised
the student workspace in a real browser (Playwright): submitting `SELECT *
FROM orders` (misses the dedup) shows "Grading failed" / result mismatch;
submitting the correct deduping query shows "Query graded correct." and
moves to pending review.

_(appended by the agent as work happens)_
