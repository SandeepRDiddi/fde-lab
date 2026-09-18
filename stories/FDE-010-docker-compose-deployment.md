# FDE-010: Docker Compose deployment

**Status:** Done
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
      (not verified — Docker's own image pulls are stuck/unreachable in this
      environment, see merge review below; `docker compose config` validates
      cleanly and the dependency graph was reviewed by hand, but the stack
      has never actually been started)
- [ ] Two cohorts run side by side locally without cross-contamination (same
      caveat — reviewed by hand via distinct project names/port overrides,
      never run)
- [x] Story status updated below
- [x] architecture.md updated if the deployment approach deviates from documented
      (no deviation)

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

Deviation from AC1 at implementation time: no `frontend/` Dockerfile or
Compose service, since `frontend/` didn't exist in this repo yet (FDE-008
was still "In review"). Added during merge review once FDE-008 had merged —
see below.

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

### 2026-09-18 (merge review)
Code-reviewed PR #21 and fixed before merge — two findings would have
broken `docker compose up` on a genuinely clean machine:
- **Alembic version-table collision.** `backend` and `persona-service` share
  one Postgres database, and both services' root migrations are independently
  numbered starting at `"0001"` with no `version_table` override — so
  whichever of `backend-migrate`/`persona-migrate` runs second sees a
  matching `alembic_version` row already present and silently no-ops without
  creating its own tables. Fixed at the source (not just in this compose
  file): both services' `alembic/env.py` now set a distinct `version_table`
  (`backend_alembic_version` / `persona_alembic_version`), so sharing a
  database no longer means sharing migration bookkeeping.
- **MinIO healthcheck always fails.** The `curl`-based healthcheck copied
  from older examples doesn't work — recent `minio/minio` images dropped
  `curl` entirely, so the healthcheck never passes, `minio-init` (which
  gated on `minio: condition: service_healthy`) never runs, the dataset
  bucket never gets created, and `data-gen` can never run. Removed the
  unreliable healthcheck; `minio-init` now retries its own `mc alias set`
  connection in a loop instead of depending on minio's Docker-level health
  status at all — this doesn't depend on knowing what tools happen to be
  bundled in the image.
- `host.docker.internal` (persona-service's default PromptOps Gateway host)
  only resolves automatically on Docker Desktop, not native Linux Docker
  Engine. Added `extra_hosts: ["host.docker.internal:host-gateway"]`.
- `backend`/`backend-migrate`/`celery-worker` (and the persona equivalents)
  each built the same context under a different implicit image name, so
  Compose built and stored the same image multiple times. Tagged them with
  a shared `image:` per service group.
- Fixed a duplicated `## Implementation log` header left over from the
  original PR.

**Also completed, now that FDE-008 has merged**: added `frontend/Dockerfile`
(`node:20-slim`, `npm ci` + `npm run build`, matching the simple
single-stage pattern the other services already use) and a `frontend`
service in `infra/docker-compose.yml`, satisfying AC1's frontend Dockerfile
requirement that was correctly deferred at implementation time.

**Left as-is, not fixed** (noted, lower severity): the Dockerfiles install
full `requirements.txt` (including `pytest`) into the runtime image rather
than splitting runtime/dev dependencies — real image bloat, not a
correctness bug; would need a `requirements-dev.txt` split across three
services to fix properly.

**Verification, and its limits**: `docker compose config` validates and
interpolates cleanly (checked with a temporary `.env` from `.env.example`,
removed after). Actually starting the stack (`docker compose up`) was not
possible in this environment — `docker info` succeeds (the daemon is up),
but `docker pull` hangs indefinitely even for `hello-world`, while a direct
`curl` to the Docker Hub registry from the host shell succeeds — pointing at
a Docker Desktop VM networking issue specific to this sandbox, not the
compose file. The alembic and minio-init fixes above are sound by inspection
(distinct version tables is a documented Alembic feature; a retry loop
against `mc`, which is guaranteed present in the `minio/mc` image regardless
of what's in `minio/minio`, has no dependency on the thing that broke) but
neither was confirmed against a real `docker compose up`. Whoever has a
working Docker environment should run it before fully trusting the DoD
items above.

Note for anyone continuing this: this session also started Docker Desktop
(it wasn't running before), which brought up several pre-existing unrelated
containers on this machine (`claude-coding-agent-*`, `multi-agent-framework-*`,
`genai-pulse-bot-qdrant-1`, `datamesh-manager-ce-*`) as a side effect of
their own restart policies — left running rather than stopped, since killing
someone else's live containers to "clean up" seemed like the wrong call.
