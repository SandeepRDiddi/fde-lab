# FDE-003: Synthetic data generator v1

**Status:** Not started
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
- [ ] Two consecutive runs produce demonstrably different datasets
- [ ] Story status updated below
- [ ] architecture.md updated if the generation approach deviates from documented

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
