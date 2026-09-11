# FDE Lab — roadmap

The plan of action for building FDE Lab, phased so each stage is independently
useful and validated before the next one adds complexity. This supersedes the
single-pass Railway deployment plan in the original `architecture.md` — that
document has been updated to match.

## Phase 0 — Foundations (done)

`intent.md`, `architecture.md`, the story backlog, and the GitHub Project board.
Nothing to build here; this is the planning already completed.

## Phase 1 — Core loop, Docker Compose, one cohort at a time

Goal: prove the full scenario loop works end to end, running locally.

- Build stories FDE-001 through FDE-008 (scenario engine, scheduler, data
  generator, persona service, enterprise mocks, student workspace)
- Containerize each service (one Dockerfile per service)
- Wire them together with a `docker-compose.yml` — Postgres, Redis, object
  storage (e.g. MinIO for local dev), and all app services
- Validate: `docker compose up` runs one full scenario, one cohort, start to
  finish, on a single machine

## Phase 2 — Instructor tooling and multi-cohort validation (still Docker Compose)

Goal: prove cohort isolation logic works before adding a real orchestrator.

- Build FDE-009 (instructor console)
- Run multiple cohorts side by side locally (separate Compose project names or
  port ranges) to validate that scenario state, data, and mocks don't leak
  across cohorts
- This is a deliberate checkpoint: multi-cohort correctness gets proven on the
  simple orchestrator before Kubernetes adds its own complexity on top

## Phase 3 — LMS integration (LTI 1.3)

Goal: a student can launch a scenario directly from their course in the LMS.

- Build an LTI launch service: handles the OIDC-based LTI 1.3 launch handshake,
  maps the LMS course/cohort to a scenario instance
- Optional, once the core launch works: Names and Roles Provisioning Service
  (NRPS) to auto-populate a cohort from the LMS roster, and Assignment and
  Grade Services (AGS) to push a completion/score back to the LMS gradebook
- Still fine to run behind Docker Compose for an early single-course pilot —
  the LMS integration and the orchestrator migration are independent axes

## Phase 4 — Kubernetes migration for scale

Goal: support multiple concurrent cohorts across courses/institutions.

- Containerized services from Phase 1 get Kubernetes manifests (or a Helm
  chart)
- Per-cohort Kubernetes namespace, provisioned automatically on LTI launch or
  instructor action
- Ingress routing per cohort; autoscaling for concurrent load across courses
- This phase retires the Docker Compose deployment path for production use —
  Compose remains for local development

## Sequencing notes

- Phases 1 and 2 do not depend on the LMS or on Kubernetes at all — they're
  fully buildable and demoable in isolation, which keeps the "no lesser
  options" end-to-end demo (from `intent.md`) achievable early.
- Phase 3 (LMS) and Phase 4 (Kubernetes) are independent of each other and
  could, in principle, be reordered — Kubernetes was sequenced last here
  because it's the highest-complexity piece and the "learn as we go" priority
  favors deferring it until the rest of the platform is proven.
