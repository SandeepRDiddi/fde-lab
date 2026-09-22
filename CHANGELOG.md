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
- 2026-09-21 — Fixed a live-caught bug affecting both model-backend
  callers (`scenario_generator.py` and `persona-service/app/gateway.py`):
  neither request set an explicit `max_tokens`, and the default model
  (`openai/gpt-oss-20b`) is a reasoning model that spends completion
  tokens on hidden chain-of-thought before writing its actual answer. A
  harder/more ambiguous requirement ("I want to automate my Payroll using
  Agentic AI") could burn the whole provider-default token budget on
  reasoning and return `finish_reason: "length"` with zero characters of
  real output — surfaced to the instructor as an opaque "Model output was
  not valid JSON" error. Fixed by requesting a generous `max_tokens`
  (8192 for the generator, 4096 for persona chat) and raising a clear,
  specific error when this still happens instead of an unhelpful JSON
  parse failure. Also fixed a related bug in the generator's own retry
  loop: a `GeneratorError` from the model-backend call itself (this one,
  or a network failure) used to skip the retry entirely instead of giving
  the model a second attempt the way an unparseable draft already did.
- 2026-09-21 — scenario_generator.py now drafts python_script tasks too
  (previously sql_query only), biased toward scripts by default since
  that's the more realistic FDE deliverable shape. Same fixed-naming fix
  applied to input/output filenames as was applied to SQL's table name.
  Live testing caught the same null-comparison bug class in generated
  *code*: a validation-passing reference_solution crashed on a real
  dataset because the validation sample data had no nulls in it — fixed by
  putting a null inside the sample duplicate pair a script must merge, so
  non-null-safe generated code is now rejected before it ships. Honest,
  documented limitation: even after that fix, the model doesn't always
  follow the "use this exact filename" instruction inside a script's own
  source — python_script generation has a real, lower one-shot success
  rate than sql_query's on this free/small model, not just occasional bad
  luck; the validation-and-retry catches it (never ships a broken
  scenario) but doesn't eliminate it.
- FDE-016: Python script task type — a scenario can now require a script
  (not just a single SQL query), run in a resource-limited,
  environment-stripped sandbox and compared to a reference solution's own
  output. Closes the "answering a SQL question isn't FDE work" gap: a
  script has real control flow, closer to an actual deliverable. Also
  fixed, in the same change: every scenario-instance API response was
  leaking the grading answer key (`reference_query`/`reference_solution`)
  straight to the student's browser — now redacted on every read endpoint;
  affected the already-shipped SQL task type too, not just the new one.
  Live testing against a real dataset also caught a row-comparison bug in
  both the new and existing grading paths: a column holding `null` in one
  row and a string in another (real datasets have nulls) crashed the
  result-set comparison, since Python can't order `None` against `str` —
  fixed in both `evaluate_sql_submission` and the new
  `evaluate_python_script_submission`.
- FDE-015: Technical task workspace — a student can now see the actual
  dataset (columns + real rows, not a raw unopenable `s3://...` link)
  before writing a query, run a query and see its real result before
  deciding what to submit (non-graded, doesn't touch the actual graded
  submission), and writes it in a real syntax-highlighted SQL editor
  instead of a plain textarea. Closes the "submit blind, first try is the
  only try" gap in FDE-013's technical-task flow.
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
- FDE-017: Engagement sequencing primitive — `Engagement` chains ordered
  `ScenarioInstance` stages, approval-triggered (not time-triggered) unlock,
  additive cross-stage context. Foundation for the 22-stage FDE Engagement
  Framework content stories (FDE-018+).
- FDE-018: GlobalRetail engagement, Stage 0 (Mission Briefing) — first
  stage-content story on FDE-017's primitive. Onboarding persona + brief
  compliance checklist, `POST /engagements/global-retail` convenience
  launcher.
- FDE-019: GlobalRetail engagement, Stage 1 (Discovery & Problem Framing) —
  conflicting-stakeholder persona, symptom-vs-cause + dual "customer"
  definition compliance checklist. Found and worked around a
  negation-window false positive in the FDE-007 compliance rule engine.
- FDE-020: GlobalRetail engagement, Stage 2 (Current-State Assessment) —
  wires FDE-005's real legacy-system mock as a genuine (not narrated)
  blocked-access injection; second undocumented-dependency finding
  conveyed via persona since the platform only supports one legacy system
  per instance today.
- FDE-021: GlobalRetail engagement, Stage 3 (Data & Knowledge Discovery) —
  first stage-content story to grade a real technical_task (SQL profiling
  query against a deliberately messy synthetic dataset) instead of
  persona+compliance_checklist prose.
- FDE-022: GlobalRetail engagement, Stage 4 (AI Readiness Assessment) —
  closes out Mission 1 (Discover, Stages 0-4), all gradable end to end via
  `POST /engagements/global-retail`.
- FDE-023: Surface engagement context to the persona — found and fixed a
  real gap in FDE-017: accumulated cross-stage context was being written to
  config but never read by persona-service's system prompt, so it never
  actually reached a later stage's conversation.
- FDE-024: GlobalRetail engagement, Stage 5 (Solution Framing) — opens
  Mission 2 (Architect); first stage-content story to actually exercise
  FDE-023's cross-stage context fix.
- FDE-025: GlobalRetail engagement, Stage 6 (Semantic & Context Layer) —
  canonical "order"/"delay" definitions reconciling three systems' meanings
  of each.
- FDE-026: GlobalRetail engagement, Stage 7 (Enterprise Architecture) —
  Architecture Review Board rejects direct-database-access outright; found
  a possessive-apostrophe tokenizer quirk in the compliance rule engine
  while writing fixtures.
