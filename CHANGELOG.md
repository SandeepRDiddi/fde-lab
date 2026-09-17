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
