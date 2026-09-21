# FDE-015: Technical task workspace (dataset preview, run-before-submit, real editor)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-003, FDE-008, FDE-013

**Architecture ref:** architecture.md → Technical deliverable grading

## User story
As a student, I want to see the actual dataset and try my query before I
submit it for grading, so that writing a technical deliverable feels like
real engineering work instead of guessing blind and hoping.

## Motivation

FDE-013 made a submission gradable by execution, but the interaction around
it was thin: a plain textarea, no way to see the data before writing a
query against it, and no way to know if a query even ran correctly before
the one and only graded attempt. Real FDE work starts with looking at what
you're dealing with, then iterating — write, run, check the result, adjust,
run again — before committing to an answer. This story closes that gap for
the existing SQL technical-task type (a new task type is separate,
out-of-scope work) with three pieces: a dataset preview panel, a non-graded
"Run" step, and a real SQL editor.

## Acceptance criteria (EARS)
1. WHERE a scenario instance has a generated dataset, THE student workspace
   SHALL show a preview of its actual rows and columns, not just a raw
   storage location.
2. WHEN a student runs a technical-task query before submitting, THE
   backend SHALL execute it against the real dataset and return its actual
   result, without grading or persisting anything.
3. THE technical-task query input SHALL be a syntax-highlighted SQL editor,
   not a plain text box.
4. Running a query SHALL NOT count as or affect a graded submission —
   submitting is still a separate, explicit action.

## Definition of done
- [x] Dataset preview works against a real dataset (verified live, not just
      mocked)
- [x] Run-before-submit shows the query's real result and is clearly
      distinguished from a graded submission
- [x] Story status updated below
- [x] architecture.md updated
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-21** — Extracted the S3/dataset-fetch logic FDE-013's
`app/grading.py` already had into a new shared `app/dataset_store.py`
(`fetch_dataset_rows`, plus a new `preview_dataset(location, limit)` that
returns the union of columns across all rows — schema drift means later
rows can carry columns the first row doesn't — alongside the first `limit`
rows and a total count). `grading.py` now imports from there instead of
duplicating it, and gained `run_query()`: same read-only enforcement
(single `SELECT`, no write/schema keywords) and same in-memory-SQLite
execution as `evaluate_sql_submission`, but returns the actual result
(columns, up to 50 rows, total row count, a `truncated` flag) instead of a
pass/fail — nothing is compared to `reference_query` or persisted (AC2,
AC4).

New endpoints: `GET /scenario-instances/{id}/dataset-preview` (AC1, in
`scenario_instances.py`, reuses `preview_dataset`) and
`POST /scenario-instances/{id}/technical-task/run` (new
`routers/technical_task.py`, reuses `run_query`) — both 404 cleanly when
there's no dataset/technical_task configured yet.

Frontend: `DatasetPreview` component (replaces `DatasetLink`, which just
rendered the raw `s3://...` URI as a link — not actually openable in a
browser, so effectively dead) — fetches the preview and renders a
scrollable table, `null` values shown distinctly from empty strings.
`SubmissionPanel` swaps its plain `<textarea>` for a `@uiw/react-codemirror`
+ `@codemirror/lang-sql` editor when `technical_task` is configured (AC3),
adds a "Run" button next to "Submit query" that calls the new run endpoint
and renders the result in the same table style as the dataset preview,
clearly labeled "not graded, this is just a preview" so it can't be
confused with an actual submission result.

Tests: `backend/tests/test_dataset_preview.py` (4), extended
`backend/tests/test_grading.py` with `run_query` coverage (6 new — actual
result returned, preview-limit truncation, non-`SELECT`/disallowed-keyword/
execution-error all raise, missing dataset raises), new
`backend/tests/test_technical_task_run.py` (4 — real result returned and
nothing persisted, 404 without a technical task configured, non-`SELECT`
input 422s, unknown instance 404s). Existing `grading.py`/`submissions.py`
tests' S3 monkeypatch target updated from `app.grading.boto3.client` to
`app.dataset_store.boto3.client` to match the extraction. Full backend
suite: 104 passed. `npm run typecheck`/`build`: clean (CodeMirror adds
~150kB to the workspace page's first-load JS — a real, accepted cost of a
proper editor, not something this story tried to avoid).

Verified live against the real running stack (not just mocked tests): a
scenario instance created via the FDE-014 generator, its dataset already
present from a live `data-gen` run, opened in a real browser (Playwright).
Dataset preview rendered the actual 560-row dataset including real
messiness (nulls, schema-drift columns `source_system`/`order_date_legacy`
that the first row doesn't have). Typed a query into the CodeMirror editor,
clicked Run — got the real 50-row preview, explicitly labeled non-graded.
Submitted the same (wrong) query — "Grading failed" with the real row-count
mismatch, distinct from the Run result above it. Submitted the scenario's
actual `reference_query` — "Query graded correct.", `pending_review`.

_(appended by the agent as work happens)_
