# FDE-021: GlobalRetail engagement — Stage 3 (Data & Knowledge Discovery)

**Status:** Done
**Priority:** P1
**Depends on:** FDE-003, FDE-004, FDE-013, FDE-017, FDE-020
**Architecture ref:** architecture.md → Backend — FastAPI + Celery/Redis → Engagement sequencing (FDE-017); Synthetic data generation; Technical deliverable grading

## User story
As a student, I want Stage 3's "assess data quality" instruction to mean
actually profiling a real, deliberately messy synthetic dataset with a SQL
query — graded on whether my query returns the right answer, not on whether
my prose sounds right — since that's the concrete half of "data discovery"
the earlier narrative stages couldn't exercise.

## Motivation

Fourth stage-content story on FDE-017's primitive; appends
`GLOBAL_RETAIL_STAGES[3]`. Per the framework: **Situation** — the same core
entity means something different in every source system, and institutional
knowledge lives in unindexed documents. **Assets** — sample extracts per
source, a shared drive of contracts/SOPs, no data dictionary. **FDE must**
— profile the data, identify ownership per source, assess quality, find the
real gaps. **GlobalRetail specifics** — "Order" means something different
in SAP, Salesforce, and the warehouse system; half the supplier docs are
unindexed PDFs. **Deliverable** — Data Product / Source Map.

This is the first stage to use `config["data_gen"]` (FDE-003) and
`config["technical_task"]` (FDE-013) rather than persona+compliance_checklist
alone — "profile the data" and "assess quality" are concrete, gradable work
against a real dataset, not something a prose rubric can check. Per FDE-014's
already-documented lesson, a `technical_task`'s submission content is the
query itself, so it can't also carry a `compliance_checklist` prose
requirement in the same field — the "identify ownership" / "find the real
gaps" half of the stage stays in the persona (ask-to-reveal, same mechanic
as prior stages), not a second graded artifact.

## Acceptance criteria (EARS)
1. THE backend SHALL define `GLOBAL_RETAIL_STAGES[3]` with
   `config["data_gen"] = {"domain": "ecommerce_orders", "row_count": 300,
   "messiness": "high"}` — deliberately messy (FDE-003's `high` profile:
   20% null rate, schema drift, 12% duplicate rate) so there's a genuine
   quality gap to find, matching data-gen's existing domain/messiness
   contract.
2. THE backend SHALL define `config["technical_task"]` as a `sql_query`
   task (`table_name: "orders"`) whose `reference_query` counts orders
   missing a `customer_email` — the concrete "assess quality" deliverable,
   graded by FDE-013's existing result-set comparison (exact wording/column
   alias doesn't matter, only the returned value).
3. THE persona SHALL, only on request, name which department owns which
   source system's data and confirm that half the supplier documentation
   lives in unindexed PDFs on a shared drive rather than a queryable
   system — the "ownership" and "real gaps" half of the stage, not graded
   automatically (no compliance_checklist on this stage, per the
   FDE-014-documented one-content-field constraint above).
4. WHEN a correct profiling query is submitted, THE grader SHALL accept it;
   WHEN an incorrect one is submitted, THE grader SHALL reject it — same
   FDE-013 mechanics, exercised here against this stage's specific
   `reference_query`, not new grading logic.

## Definition of done
- [x] `GLOBAL_RETAIL_STAGES[3]` authored (persona + data_gen + technical_task,
      no compliance_checklist)
- [x] Tests: stage 3 config validates, no `compliance_checklist` present,
      persona doesn't leak ownership/gap facts unprompted, a correct
      profiling query passes grading, an incorrect one fails, grading
      exercised via the same fake-S3-bucket pattern FDE-013/FDE-014's own
      tests use (no live MinIO in this dev environment)
- [x] Story status updated below
- [x] STORIES.md row added
- [x] CHANGELOG.md entry added

## Implementation log

**2026-09-22** — Appended `GLOBAL_RETAIL_STAGES[3]` in
`backend/app/engagement_content/global_retail.py`: `data_gen` requests a
300-row `ecommerce_orders` dataset at `high` messiness (FDE-003's profile —
20% null rate, schema drift, 12% duplicate rate), and `technical_task` is a
`sql_query` task (`table_name: "orders"`) whose `reference_query` counts
orders missing `customer_email` — graded by FDE-013's existing exact
result-set comparison (column naming/aliasing is irrelevant, only the
returned value tuples are compared). Persona (Taylor Brooks, continuing
from Stage 2) reveals per-source data ownership (Operations owns SAP,
Customer Service owns Salesforce, Logistics owns the warehouse export) and
the unindexed-supplier-PDFs gap only on request — no `compliance_checklist`
on this stage, since a technical_task's submission content is the SQL query
itself and a prose rule on that same field could never be jointly
satisfiable (the exact bug FDE-014's implementation log already found and
fixed for the generator; this story avoids reintroducing it by construction).

Tests: `backend/tests/test_global_retail_stage3.py` (7 tests) — config
validates, no compliance_checklist present, data_gen uses high messiness,
persona doesn't dump facts unprompted, and (using the same fake-S3-client
pattern FDE-013/FDE-014's own tests use, since no live MinIO runs in this
dev environment) a correct profiling query passes real grading end-to-end
via `POST .../submissions` and an incorrect one gets rejected with 422.
Full backend suite: 179 passed (up from 173 before this story).
