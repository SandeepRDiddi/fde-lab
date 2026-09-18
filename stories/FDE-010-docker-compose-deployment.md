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
- [x] `docker compose up` runs a full scenario end to end on a clean machine
      (verified live 2026-09-18, once Docker's pulls recovered — see the
      second merge-review entry below: full instance-create → schedule →
      unlock → chat → submit → approve → data-gen-to-MinIO cycle, all
      against real containers, not a mock)
- [ ] Two cohorts run side by side locally without cross-contamination (still
      not verified — the single-cohort run above used one project name/port
      set; running two side by side wasn't exercised)
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

### 2026-09-18 (validation pass — Docker recovered, actually ran it this time)
The Docker Hub connectivity issue from the entry above turned out to be
transient (a plain `docker pull hello-world` worked fine on retry later the
same day). With a live daemon actually reachable, ran the real thing —
`docker compose build` then `docker compose up -d` under an isolated
project name and remapped host ports (`COMPOSE_PROJECT_NAME=fde-lab-validate`,
ports shifted to 13000/18000/18001/19000/19001) so as not to collide with
the other unrelated containers already running on this machine. Two real
bugs surfaced that no amount of reading the compose file would have caught:

- **MinIO has pulled `minio/minio` and `minio/mc` off Docker Hub entirely**
  — both now 403 with "repository does not exist... denied." This is an
  external, time-dependent break: nothing in this repo's history caused it,
  and it may well have still been fine on Docker Hub when this story or its
  first merge review were written. Current official home is
  `quay.io/minio/minio` / `quay.io/minio/mc`; repointed both
  `infra/docker-compose.yml` and the Helm chart's `values.yaml` (FDE-012)
  there, confirmed by actually pulling both from quay.io successfully.
- **`backend-migrate` failed on a genuinely fresh database** — a bug in
  FDE-007's migration `0005_create_submissions.py`, not this story's own
  files, but it blocked "docker compose up ... one full scenario end to
  end" so it got fixed here rather than filed away: an explicit
  `CREATE TYPE approval_status` up front, combined with `create_type=False`
  on the columns to (the author's stated intent) avoid a second
  `CREATE TYPE` — except `create_type=False` doesn't actually suppress
  `create_table`'s own `before_create` attempt to create the enum, so it
  tried to create the same type twice inside one transaction and
  Postgres's `DuplicateObject` error rolled the whole migration back.
  Fixed by using a single plain `sa.Enum` shared by identity across all
  three column uses and dropping the explicit pre-create entirely — the
  same pattern already proven working in `0001_create_scenario_instances.py`.
  Reproduced against a real Postgres via `docker compose run --rm
  backend-migrate alembic upgrade head` both before (confirmed the failure)
  and after (confirmed 0001→0005 all apply cleanly) the fix.
- Also found and fixed while chatting through persona-service live:
  an unreachable PromptOps Gateway (the ordinary case — it isn't part of
  this repo) produced an unhandled 500 with a half-written student message
  left flushed. See FDE-004's story log for that fix; caught here because
  this was the first time anyone actually sent a message against a running
  persona-service with no gateway behind it.

Once both fixes landed, the full stack came up healthy and a real
end-to-end run worked: created a scenario instance on the live backend,
scheduled it (`POST .../schedule`) and watched the real Celery unlock job
flip it to `active` with `notified_at` set, hit the persona chat endpoint
(confirmed the clean-502 behavior above), submitted content that passed a
real `compliance_checklist` rule, approved it through the manual-decision
endpoint and watched `approval_outcome` land on the instance, listed the
cohort's instances and the submission through the FDE-009 instructor-console
endpoints, loaded `/instructor/<cohortId>` itself, and ran
`docker compose run --rm data-gen python -m generator <instance-id>`
against the real MinIO — the dataset actually landed in the bucket and
`dataset_location` was recorded back on the instance. Torn all the way down
afterward (`docker compose down -v`) with no leftover containers, volumes,
or network, and the other pre-existing containers on the machine were left
untouched throughout.

Not run: the second DoD item (two cohorts side by side) — this pass used
one cohort under one project name/port set throughout.
