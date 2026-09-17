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

**2026-09-18** — Implemented Docker Compose deployment per architecture.md →
Deployment (Phase 1-2).

Added:
- `backend/Dockerfile`, `persona-service/Dockerfile`, `data-gen/Dockerfile`
  (python:3.11-slim, mirroring `lti-service/Dockerfile`'s existing pattern),
  plus a `.dockerignore` for each.
- `infra/docker-compose.yml`: postgres (16-alpine), redis (7-alpine), minio
  (local S3-compatible store) + a `minio-init` one-shot container that
  creates the dataset bucket via `mc`, `backend-migrate`/`persona-migrate`
  one-shot containers that run `alembic upgrade head` before the long-running
  `backend`, `celery-worker`, and `persona-service` containers start
  (`depends_on: condition: service_completed_successfully`), and a `data-gen`
  service under Compose profile `tools` (one-off, invoked per cohort setup
  via `docker compose run --rm data-gen python -m generator <instance-id>`,
  matching how FDE-003 already expected this piece to be wired). All
  long-running services carry healthchecks so `docker compose up` reports
  healthy only once the stack can actually serve traffic (AC3).
- `infra/.env.example` documenting all overridable env vars, in particular
  the `*_PORT` vars and `COMPOSE_PROJECT_NAME` needed to run two cohorts side
  by side without collision (AC4) — Compose prefixes named volumes/network
  with the project name automatically, so `-p cohort-a` / `-p cohort-b` (or
  `COMPOSE_PROJECT_NAME`) with distinct `.env.cohort-*` port overrides gives
  full state isolation between cohorts with no code changes.

Deviation from AC1: no `frontend/` Dockerfile or Compose service. `frontend/`
does not exist in this repo yet — FDE-008 (the story that creates it) is
still "In review", not merged to `main`, and per CLAUDE.md's standing
instruction not to invent commands/services for code that isn't built, a
Dockerfile/service was not fabricated for it. `docker compose up` therefore
brings up backend + Celery worker + persona-service + data (Postgres/Redis/
MinIO) healthy, and "one full scenario end to end" (AC3) is exercised via the
backend/persona-service APIs and the `data-gen` one-off container rather than
through a UI. Once FDE-008 merges, add a `frontend` service to
`infra/docker-compose.yml` following the same Dockerfile pattern (Next.js
build) — no other part of this compose setup needs to change for that.

architecture.md's Deployment/Repository-layout sections already described
this shape accurately (backend, Celery workers, persona service, frontend,
Postgres, Redis, MinIO, `infra/docker-compose.yml`) — no architecture.md
changes were needed beyond the frontend sequencing gap noted above, which is
a merge-order fact, not a design deviation.

Not yet verified against a live Docker daemon: Bash tool access in this
session was restricted to command approval that could not be granted
interactively, so `docker compose config` / `docker compose up` could not be
run here to confirm the stack actually comes up healthy end to end. The
compose file was reviewed carefully by hand (dependency graph, healthchecks,
env var interpolation, `depends_on` conditions) but running it on a real
machine is still needed before checking off the Definition of done boxes
above.


## Implementation log
_(appended by the agent as work happens)_
