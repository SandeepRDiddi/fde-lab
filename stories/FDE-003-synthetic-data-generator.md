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
