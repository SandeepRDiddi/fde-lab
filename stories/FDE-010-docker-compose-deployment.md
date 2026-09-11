# FDE-010: Docker Compose deployment

**Status:** Not started
**Priority:** P0
**Depends on:** FDE-001, FDE-002, FDE-003, FDE-004
**Architecture ref:** architecture.md → Deployment (Phase 1-2)

## User story
As a platform owner, I want the full stack deployable with a single Docker Compose
command, so that the end-to-end demo runs reliably on any machine, not just the one
it was built on.

## Acceptance criteria (EARS)
1. THE deployment SHALL provide a Dockerfile for each service (backend, Celery
   workers, persona service, frontend).
2. THE deployment SHALL provide a `docker-compose.yml` that wires together all
   services plus Postgres, Redis, and a local S3-compatible store.
3. WHEN a developer runs `docker compose up`, THE stack SHALL come up healthy and
   support running one full scenario end to end.
4. THE deployment SHALL support running multiple cohorts side by side locally
   (e.g. via separate Compose project names) without state leaking between them.

## Definition of done
- [ ] `docker compose up` runs a full scenario end to end on a clean machine
- [ ] Two cohorts run side by side locally without cross-contamination
- [ ] Story status updated below
- [ ] architecture.md updated if the deployment approach deviates from documented

## Implementation log
_(appended by the agent as work happens)_


## Implementation log
_(appended by the agent as work happens)_
