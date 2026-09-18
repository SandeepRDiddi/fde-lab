# Changelog

One line per merged story (see `AGENT-WORKFLOW.md`).

- FDE-001: Scenario engine skeleton — FastAPI backend, `scenario_instances`
  table + migration, create/read endpoints. (PR #13)
- FDE-002: Time-box scheduler — Celery/Redis unlock/close/pivot jobs,
  `/schedule` endpoint, reschedule cancels stale jobs. (PR #14)
- FDE-003: Synthetic data generator v1 — domain/messiness-parameterized
  dataset generation, S3 upload, `dataset_location` on the instance.
  Automatic trigger on instance creation still unbuilt (needs FDE-010 or a
  follow-up story). (PR #15)
- FDE-004: AI persona service — persona chat via PromptOps Gateway,
  per-student conversation history, pivot updates agenda in place. Fixed
  FDE-002's shallow pivot merge (was dropping nested persona fields). (PR #16)
- FDE-005: Legacy API mock service — scenario-configured schema drift,
  latency, unhelpful 401s; a scenario is a JSON file, no code change. (PR #17)
- FDE-006: Compliance checklist engine — per-scenario rules block submission
  and name failures. Fixed keyword matching that a negating sentence
  ("no rollback plan") could trivially satisfy. (PR #18)
- FDE-011: LTI 1.3 launch service — OIDC login/launch handshake, NRPS
  roster pull, AGS score push. Fixed a replay race in the one-time state
  store and a missing `azp` audience check. Scenario-engine mapping
  endpoint it depends on still doesn't exist (needs FDE-010 or a follow-up
  story). (PR #19)
- FDE-008: Student scenario workspace — Next.js workspace: status/countdown,
  persona chat, artifact feed, dataset link, submission panel. Fixed a
  hydration mismatch and an optimistic-message leak on send failure. (PR #20)
- FDE-010: Docker Compose deployment — full stack incl. frontend wired up.
  Fixed an Alembic version-table collision between backend/persona-service
  and a minio healthcheck that always failed (curl removed from the image),
  both of which would have broken a fresh `docker compose up`. (PR #21;
  verified live 2026-09-18 — see below.)
- FDE-007: Approval workflow state machine — submit → pending_review →
  approved/rejected, manual or auto-decided after a configured delay. Fixed
  a response-shape mismatch that would have crashed the FDE-008 frontend on
  every submission, and a race between manual/auto decisions. (PR #22)
- FDE-009: Instructor console — schedule a cohort, monitor student status,
  view and approve/reject submissions, all from one screen. Verified live
  end to end 2026-09-18; no bugs found. (PR #23)
- FDE-012: Kubernetes migration — per-cohort Helm chart, standalone
  provisioner service, ingress + NetworkPolicy isolation. Fixed a missing
  `--create-namespace` that would have broken provisioning any brand-new
  cohort. LTI-launch auto-provisioning still not wired (needs
  `/internal/lti-mappings` on the backend first). (PR #24)
- 2026-09-18 — Live `docker compose up` validation pass (all PRs above were
  merged directly by the repo owner without review; ran a full pass after
  the fact): MinIO removed `minio/minio`/`minio/mc` from Docker Hub
  entirely (moved to quay.io) — repointed both `docker-compose.yml` and the
  Helm chart. A double-`CREATE TYPE` bug in FDE-007's migration
  (`create_type=False` doesn't suppress `create_table`'s own auto-create)
  broke `backend-migrate` on any genuinely fresh database — fixed. An
  unreachable PromptOps Gateway crashed `persona-service` with a bare 500
  instead of a clean error — fixed (see FDE-004's log). Full instance
  create → schedule → unlock → chat → submit → approve → data-gen-to-MinIO
  cycle confirmed working end to end against real containers after fixes.
