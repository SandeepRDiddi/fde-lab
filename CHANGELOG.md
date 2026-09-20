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
- 2026-09-20 — Moved the model backend (persona chat and the scenario
  generator) from local Ollama to Groq's free tier: local CPU inference was
  slow and competed with the host machine for resources. Both
  `persona-service/app/gateway.py` and `backend/app/scenario_generator.py`
  now speak the OpenAI-compatible chat/completions contract (Groq, Together,
  DeepInfra, OpenRouter, and Ollama's own `/v1` endpoint all share it), so
  switching provider is an env-var change (`FDE_PROMPTOPS_GATEWAY_URL/
  _API_KEY/_MODEL`), not a rewrite — a local Ollama setup with no API key
  still works by pointing the URL at its `/v1` path. Still open-weight
  models only, no paid frontier-model API. Result: ~1.5-4s per generation
  (down from 8-40s on local CPU Ollama) at effectively no cost for a
  training lab's volume.

  Live testing surfaced two more issues before this was called done:
  Groq had already retired the model id first configured
  (`llama-3.1-8b-instant` 404'd — "does not exist or you do not have
  access to it"); switched to `openai/gpt-oss-20b`, currently live on
  Groq's `/v1/models` list. Separately, the scenario generator's
  `technical_task.reference_query` sometimes failed to execute because the
  model's own `table_name` field and the table name inside its
  `reference_query` disagreed (e.g. `table_name: "orders"` but
  `FROM ecommerce_orders`) — fixed by no longer letting the model choose
  `table_name` at all; it's now fixed per domain
  (`scenario_generator.TABLE_NAMES`) and given to the model as a
  constraint, removing the whole failure class instead of just detecting
  it.
- FDE-014: Scenario generator — an instructor pastes a raw client
  requirement and the backend drafts a full scenario config (persona,
  synthetic-dataset shape, a graded technical task with a validated
  reference query, optionally a legacy-system quirk) via the configured
  model backend, for review before creating a real instance. Deliberately
  never emits a compliance checklist alongside the technical task — a
  submission has one content field, used for the graded query, so a prose
  rule on it could never be jointly satisfiable (caught live, see the story
  log). The other half of FDE-013: that story made submissions gradable
  by execution; this one makes the scenarios themselves generatable instead
  of hand-authored JSON.
- FDE-013: Technical deliverable grading — a scenario can require a real SQL
  query, graded by actually running it against the scenario's own synthetic
  dataset and comparing its result to a reference query's, instead of only
  grading submission prose by keyword. Closes the gap where a submission
  could describe a correct fix without the fix actually being correct.
- 2026-09-18 — Wired the FDE-005 legacy-system mock into the student flow:
  it had shipped as a standalone service with nothing calling it. Added a
  backend proxy endpoint and a workspace panel to query it; verified live
  (curl + Playwright) that the mock's unhelpful 401 and schema-drifting 200
  responses reach the student unchanged. Also replaced the LLM behind
  persona chat with a locally-run Ollama model (`llama3.2:3b`) instead of a
  paid hosted API, and moved the compliance-checklist gate (FDE-006) so the
  backend enforces it server-side instead of only the frontend.
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
