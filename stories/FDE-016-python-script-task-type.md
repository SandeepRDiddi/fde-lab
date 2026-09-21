# FDE-016: Python script task type (sandboxed code execution)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-003, FDE-013, FDE-015

**Architecture ref:** architecture.md → Technical deliverable grading

## User story
As a student, I want to write an actual script that fixes the client's data
— not just answer one SQL question — so that the deliverable feels like
real engineering work: read messy input, produce a correct output,
verified by actually running it.

## Motivation

FDE-013/015 made a SQL query gradable and iterable, but "answer a SQL
question" is a single, narrow shape of FDE work. This story adds a second
`technical_task.task_type`, `python_script`: the student writes a script
that reads the scenario's dataset (as a JSON file) and writes a corrected
output file, executed in a real sandbox and compared to a reference
solution's own output — a script, with real control flow (loops,
conditionals, error handling for bad rows), not a single statement.

This required a genuinely new capability the SQL path never needed:
running arbitrary student *code*, not a constrained read-only query inside
SQLite's own sandbox. `backend/app/code_runner.py` is that sandbox — its
own docstring states the trust model plainly: resource-limited (CPU,
memory, open files) and environment-stripped (a script can't read this
service's own secrets out of `os.environ`), but **not** network-isolated —
a script here shares this container's network namespace and could reach
internal services the way any other process in it can. That's a real,
accepted gap for a training lab (trusted students, not adversarial input),
not an oversight; the module's docstring says so explicitly, and it
shouldn't be pointed at untrusted/public input without real process
isolation (a container-per-run, gVisor, Firecracker) added first.

## Acceptance criteria (EARS)
1. WHERE a scenario configures `technical_task.task_type == "python_script"`,
   THE backend SHALL grade a submission by running it in the sandbox against
   the scenario's dataset and comparing its output to a reference
   solution's.
2. THE sandbox SHALL bound CPU time, memory, and file-descriptor use, and
   SHALL NOT expose this service's own environment variables to the
   script.
3. A non-graded "Run" step (FDE-015) SHALL work for `python_script` the
   same way it works for `sql_query` — a student can see a script's actual
   output before submitting it for real.
4. THE answer key (`reference_query`/`reference_solution`) SHALL NEVER be
   returned by any scenario-instance API response reachable from a
   student's browser.

## Definition of done
- [x] A correct script passes, an incorrect one fails with a real mismatch
      description, a broken script surfaces its actual error
- [x] Sandbox resource limits verified (timeout, no parent-env leakage)
- [x] AC4 (answer-key redaction) fixed and verified — found via design
      review while building this story, affects the already-shipped
      sql_query path too, not just the new one
- [x] Story status updated below
- [x] architecture.md updated
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-21** — Before writing any of this story's new code, found (via
design review, not live testing this time) that `GET /scenario-instances/
{id}` — and every other read endpoint on that router — returned the full
stored `config`, including `technical_task.reference_query`. Any student
could open devtools, read the network response, and copy-paste the exact
answer; grading a submission by comparing it to a reference the student
could just read defeats the entire premise of FDE-013. Fixed first, since
`python_script`'s `reference_solution` (a full working script) would have
leaked even worse than one SQL query: added `_redact_technical_task()` +
`_to_read_model()` in `backend/app/routers/scenario_instances.py`, applied
to every endpoint on that router (list, create, get, schedule, dataset
update) — `reference_query`/`reference_solution` are stripped from
`config.technical_task` in every response. Nothing legitimate needed them
via these endpoints: grading (`app/grading.py`) and the run-preview
endpoint (`app/routers/technical_task.py`) read the ORM object directly,
not through this read model, and the only place an answer key should ever
be visible is the generator's own draft-preview
(`POST /scenario-generator/draft`), an instructor-authoring step before an
instance exists — unaffected by this change (AC4).

`backend/app/code_runner.py` (new): `run_python_script(source, input_data,
input_filename=, output_filename=, timeout=)` writes the script and input
JSON into a fresh temp directory, runs it as a subprocess with that
directory as cwd, and returns the JSON it wrote to `output_filename`.
`_limit_resources()` (subprocess `preexec_fn`) applies `RLIMIT_CPU`,
`RLIMIT_AS`, and `RLIMIT_NOFILE`, each independently best-effort (macOS's
`RLIMIT_AS` accounting is unreliable and raised during local dev testing —
this always actually runs in the Linux container in
`infra/docker-compose.yml`, so a limit macOS's host Python can't set
shouldn't crash the sandbox; production-mode Linux applies all three).
The subprocess env is a fresh two-key dict (`PATH`, `PYTHONDONTWRITEBYTECODE`),
never `os.environ` — the direct fix for the "read this service's own
secrets" vector (AC2).

`backend/app/grading.py` gained `evaluate_python_script_submission` (runs
`reference_solution` and the student's code through the sandbox, compares
outputs as an order-insensitive set of rows — same comparison shape
`evaluate_sql_submission` already used — and returns a `result_mismatch`/
`script_execution_error`/`invalid_output_shape` failure, or a
`GradingError` for a setup problem like a missing dataset) and
`run_python_script_preview` (same execution, no comparison, same response
shape as FDE-015's `run_query` so the frontend renders both with the same
table component) — AC1, AC3. `evaluate_technical_submission` and the
`/technical-task/run` router now dispatch on `task_type` between
`sql_query` and `python_script`.

Frontend: `TechnicalTask` became a discriminated union (`SqlQueryTask` |
`PythonScriptTask`) with the answer-key fields marked optional (present
only in a generator draft, absent everywhere else, matching the redaction
fix). `SubmissionPanel`'s CodeMirror editor picks `python()` or `sql()`
based on `task_type`, and instructions/placeholder/labels ("Write your
script" vs "Write your query") adapt the same way — the Run/Submit flow
itself needed no changes, since both task types return the same response
shapes.

Deliberately not in this story's scope: `scenario_generator.py` (FDE-014)
still only drafts `sql_query` tasks. Generating a *working* reference
script from a small model, then validating it actually executes
(mirroring the SQL path's empty-table executability check, but for real
code) is a meaningfully different validation problem — worth its own pass
rather than folding into an already-large change that also fixed a
security leak. A `python_script` scenario is hand-authored via
`POST /scenario-instances` today, same as `sql_query` scenarios were
before FDE-014 existed.

Tests: `backend/tests/test_code_runner.py` (7 — input/output round-trip,
custom filenames, non-zero exit, missing output file, invalid output JSON,
timeout, parent-environment secrets not visible to the script),
`backend/tests/test_grading.py` (+8 — correct/incorrect script,
script-error surfaced, non-list output rejected, missing reference raises,
missing dataset raises, dispatch by task_type, run-preview), 6 new tests
in `backend/tests/test_scenario_instances.py` for the redaction fix across
every affected endpoint, 2 new tests in `backend/tests/test_technical_task_run.py`,
1 full end-to-end test in `backend/tests/test_submissions.py` (wrong
script 422s with `result_mismatch`, correct script 201s with
`grading_result`), and `test_scenario_generator_router.py`'s existing
create-instance test updated for the now-redacted response. Full backend
suite: 129 passed. `npm run typecheck`/`build`: clean.

Hit one real cross-platform issue while getting these green locally:
`RLIMIT_AS` raised `ValueError: current limit exceeds maximum limit` on
macOS (this contributor's dev machine), which crashed the whole sandbox
via `preexec_fn`'s propagated exception. Fixed by making each `setrlimit`
call independently best-effort (see code_runner.py's docstring/comments
above) rather than assuming every limit applies identically across
platforms — verified the real target (Linux, via the actual Docker image)
separately, see below.

Verified live against the running Docker stack — and it caught a real bug
neither the mocked unit tests nor the earlier SQL-path live testing had
hit. First live submission (a hand-authored dedup-script scenario, real
data-gen dataset) 500'd: `TypeError: '<' not supported between instances
of 'NoneType' and 'str'`, from `_normalize_rows`' `sorted()` call. Root
cause: a column holding `None` in one row and a string in another (real
datasets have nulls — data-gen's own messiness) can't be ordered by
Python's default `<`, and `sorted()` only reaches that comparison when an
earlier column ties between two rows — which a full-dataset script
(hundreds of rows) hits constantly, unlike the hand-picked 3-row fixtures
in `test_grading.py`. Fixed by sorting on `key=repr` (always a string,
always comparable) instead of relying on default tuple ordering — equality
between the two normalized lists still compares real values, so
correctness isn't affected, only the sort's ability to complete. Re-audited
`evaluate_sql_submission`'s own `sorted(map(tuple, ...))` comparison while
fixing this — same latent bug, hadn't been hit yet only because every
query tested so far happened to select a leading column (like `order_id`)
unique enough that ties on a nullable column were never reached. Fixed
there too, same `key=repr` approach, plus a regression test with an
explicitly mixed-null-and-string column for both paths.

After that fix, re-verified end to end: created a python_script instance
(hand-authored — see "deliberately not in this story's scope" above),
confirmed the answer-key redaction live (`reference_solution` absent from
both the create and GET responses' `technical_task`), ran `data-gen`
against it for a real 525-row dataset, and exercised the full loop through
a real browser (Playwright) — Python syntax highlighting in the editor,
dataset preview showing the actual messy rows (many real nulls, exactly
what triggered the bug above), Run showing an actual result, and Submit
correctly grading a passthrough (no-dedup) script as failed
(`result_mismatch`, 525 vs 500 rows) and the real dedup script as
"Graded correct." One test-methodology note, not a product bug: driving
the editor via Playwright's raw keystroke-by-keystroke typing
(`pressSequentially`) mangled the script's indentation because
CodeMirror's Python auto-indent double-applies against synthetic
character-by-character input; switching the test to a clipboard paste
(how a student would actually get code into the editor, or how any normal
typing rhythm behaves) showed clean, correctly-indented input with no
issue — confirmed by rereading the editor's own content after paste
before submitting.

Also directly confirmed the resource-limit portability fix: `RLIMIT_AS`,
which raised on this contributor's local macOS `.venv` during test setup,
applies successfully inside the real backend container (checked directly
via `docker exec`) — the production target was never actually at risk,
only local cross-platform test runs were.

Final state: backend suite 131 passed (was 129 before the two live-caught
fixes; +1 test for the null-comparison regression on each of the SQL and
python_script paths). `npm run typecheck`/`build`: clean.

_(appended by the agent as work happens)_
