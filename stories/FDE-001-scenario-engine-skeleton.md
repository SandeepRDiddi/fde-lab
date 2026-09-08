# FDE-001: Scenario engine skeleton

**Status:** Not started
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
- [ ] Migrations run cleanly from a fresh database
- [ ] Unit tests cover create/read of a scenario instance
- [ ] Story status updated below
- [ ] architecture.md updated if the schema deviates from what's documented there

## Implementation log
_(appended by the agent as work happens — date, what changed, links to commits/PR)_
