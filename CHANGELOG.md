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
