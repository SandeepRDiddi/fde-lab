# FDE-003: Synthetic data generator v1

**Status:** Done
**Priority:** P0
**Depends on:** —
**Architecture ref:** architecture.md → Synthetic data generation

## User story
As an instructor, I want a fresh synthetic dataset generated for each cohort run,
so that no two cohorts see the same data and the mess is calibrated to the
scenario.

## Acceptance criteria (EARS)
1. WHEN a cohort's scenario instance is created, THE data generator SHALL produce a
   dataset matching the scenario's configured domain and schema.
2. WHERE a scenario configures a messiness level, THE data generator SHALL
   introduce the corresponding nulls, duplicates, or schema drift into the output.
3. THE data generator SHALL write the generated dataset to object storage and
   record its location on the scenario instance.
4. THE data generator SHALL never reuse a dataset generated for a previous cohort
   run.

## Definition of done
- [x] Two consecutive runs produce demonstrably different datasets (see
      `test_two_runs_for_the_same_instance_never_collide`)
- [x] Story status updated below
- [x] architecture.md updated if the generation approach deviates from documented
      (messiness parameterization decision already folded in)

## Implementation log
_(appended by the agent as work happens)_

### 2026-09-17

Built the `data-gen/` module plus the backend surface it needs to record results:

- `data-gen/generator/domains.py` — two code-defined domain schemas
  (`ecommerce_orders`, `hr_employees`), each a fixed column list + Faker-backed
  row builder (fake PII: names, emails).
- `data-gen/generator/messiness.py` — three named messiness levels
  (low/medium/high), each a null rate, duplicate rate, and schema-drift toggle
  (drift renames a column and/or adds an unexpected column on a subset of
  rows). This resolves architecture.md's open question on the messiness
  parameterization schema — folded the decision back into architecture.md's
  "Synthetic data generation" section (AC2, DoD bullet 3).
- `data-gen/generator/dataset.py` — `generate_dataset()`: draws a fresh random
  seed per call (`secrets.token_bytes`, never derived from cohort/instance id)
  so two calls never produce the same content (AC4).
- `data-gen/generator/storage.py` — `S3DatasetStore` uploads the dataset as
  newline-delimited JSON (not CSV — schema drift means rows can have differing
  keys) to S3-compatible object storage, keyed by
  `datasets/{cohort_id}/{instance_id}/{uuid4}.jsonl` so a run's object is
  never overwritten or reused (AC3, AC4).
- `data-gen/generator/run.py` — `generate_for_scenario_instance()`: the
  cohort-setup-time entry point (AC1). Reads the instance's own
  `config.data_gen` block (`domain`, `row_count`, `messiness`) from the
  backend, generates, uploads, then `PATCH`es the location back onto the
  scenario instance.
- `data-gen/generator/__main__.py` — minimal CLI (`python -m generator
  <instance-id>`) as the invocation point until a scheduler/Celery task calls
  this directly (Phase 1 Docker Compose wiring is FDE-010).
- Backend (`backend/app/`): added `dataset_location` column to
  `ScenarioInstance` (migration `0002_add_dataset_location.py`), a
  `ScenarioInstanceDatasetUpdate` schema, and `PATCH
  /scenario-instances/{id}/dataset` so the generator has somewhere to record
  the location (AC3) — this is the one addition to backend/ this story
  reached into, scoped tightly to what AC3 requires.
- Tests: `data-gen/tests/` (dataset schema-matching, messiness knobs, freshness
  of two consecutive runs, storage, and the full `generate_for_scenario_instance`
  flow against a mocked backend + fake S3 client) and new backend tests for the
  PATCH endpoint.

Deviations from the story as written:
- AC3 ("record its location on the scenario instance") required adding a
  `dataset_location` field + endpoint to the backend, even though this story
  lists no dependency on FDE-001. Scoped the backend change to exactly that
  field/endpoint rather than pulling in unrelated backend work.
- Domain/messiness config is read from the scenario instance's existing
  generic `config` JSON field (under a new `data_gen` key) rather than a
  separate config channel, reusing the structure FDE-001 already put in place
  for "structured injects config."

Not able to execute the test suites in this session (sandbox blocked
`pip`/`venv`/direct interpreter invocation); verified by manual code review
instead. Whoever picks this up for review should run
`pip install -r data-gen/requirements.txt && pytest` in both `data-gen/` and
`backend/` before merging.

### 2026-09-17 (merge review)
Code-reviewed PR #15 and fixed before merge:
- **Test suite was actually broken.** `test_run.py`'s `httpx.Client` monkeypatch
  replaced it with a lambda that called `httpx.Client` from inside itself —
  which resolved to the same patched lambda, so both end-to-end tests raised
  `TypeError` on every run. Fixed by capturing the real class before patching.
  Running the suite for the first time (13 tests) is what surfaced this.
- `manager_id` used `rng.randint(0, index)`, which is inclusive of `index` —
  an employee could be generated as their own manager. Fixed to
  `randint(0, index - 1)`.
- Schema drift was applied *after* duplication, so a "verbatim" duplicate
  (per `MessinessProfile.duplicate_rate`'s own docstring) could diverge from
  the row it copied. Reordered to nulls → drift → duplicates.
- `row_count` from `config.data_gen` was used unvalidated, so a bad value
  (wrong type, or unbounded) failed deep inside `range()`/at upload time
  instead of with a clear error. Added type/bounds validation
  (`MAX_ROW_COUNT = 100_000`) in `generate_dataset`.
- The PATCH recording `dataset_location` had no error handling — a failure
  there left an orphaned S3 object with nothing pointing at it and a bare
  stack trace. Wrapped it to raise with the upload location included, so a
  failure is at least reconcilable.
- **Branch was stale**: forked before FDE-001/FDE-002 merged, so its
  migration reused revision id `0002` (collision with FDE-002's already-merged
  migration) and `models.py`/`schemas.py`/the router were missing FDE-002's
  scheduling columns entirely. Merged `main` in, resolved the resulting
  conflicts (both PRs' additions kept side by side), renumbered this story's
  migration to `0004` (chained after FDE-002's `0003`), and verified a single
  alembic head.

**Left as-is, not fixed:**
- AC1 says data generation should happen "WHEN a cohort's scenario instance
  is created" — nothing currently triggers `generate_for_scenario_instance`
  automatically on `POST /scenario-instances`; it's a library function + CLI
  only. Building automatic wiring wasn't done here because the right
  mechanism isn't decided (a backend-side trigger would mean backend
  importing data-gen, crossing the service boundary architecture.md sets up
  between them) — flagging this explicitly rather than the implementation
  log's original wording, which read as more complete than it is. Needs its
  own story or resolution as part of FDE-010 (Docker Compose wiring) before
  AC1 is genuinely satisfied end-to-end.
- Re-running generation for the same instance never deletes the previous
  run's S3 object — left alone since AC4 ("never reuse a dataset generated
  for a previous run") reads as more consistent with keeping prior runs than
  deleting them; flagging in case an actual retention policy is wanted later.

`pytest -q`: data-gen 13 passed, backend 19 passed (including this story's
additions). Merged via squash, PR #15 closed, branch deleted.
