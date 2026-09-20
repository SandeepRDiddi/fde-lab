# FDE Lab — Architecture

This document is the technical companion to `intent.md`. `intent.md` defines *what*
FDE Lab is and *why* it's built the way it is; this document defines *how* it's built.
If the two ever disagree, `intent.md` wins on intent and this document should be
updated to match — this file exists to serve that vision, not the other way around.
See `ROADMAP.md` for the phased plan for building this out.

## System overview

FDE Lab is a platform, not a content bundle. Students log into a scheduled,
time-boxed scenario workspace; instructors configure and monitor cohorts from a
console in the same app. Under the hood, a scenario engine orchestrates timing and
state, an AI persona service plays the stakeholder/client role, a set of enterprise
system mocks reproduce real-world constraints, and everything reads/writes to a
shared data layer.

```
Student browser ──┐
                   ├──> FDE Lab platform ──> Data & storage
Instructor console ┘         │
                              ├── Scenario engine (FastAPI + Celery scheduler)
                              ├── AI persona (Claude via PromptOps Gateway)
                              └── Enterprise system mocks (legacy API, compliance, approvals)
```

## Components

### Frontend — single Next.js app, role-gated
Students and instructors share one app, gated by role:
- **Student view**: scenario workspace — AI-persona chat, incoming artifact/ticket
  feed, data explorer for the synthetic dataset, submission panel.
- **Instructor view**: cohort configuration, scenario scheduling, live progress
  monitoring across the cohort.

### LTI launch service — LMS entry point
Added in Phase 3 (see `ROADMAP.md`). Handles the LTI 1.3 launch handshake (OIDC-based)
from the course LMS (Canvas, Moodle, etc.): a student clicks a link inside their
course and lands directly in their scenario instance, no separate login. Maps the
LMS course/cohort onto a scenario instance in the scenario engine. Optional
extensions once the core launch works: Names and Roles Provisioning Service (NRPS)
to auto-populate a cohort from the LMS roster, and Assignment and Grade Services
(AGS) to push a completion/score back to the LMS gradebook.

### Backend — FastAPI + Celery/Redis
A Python/FastAPI service owns scenario state, submissions, and the websocket
connection for the persona chat (streaming, not just request/response — the
demo/defend moments need to feel live). Celery + Redis handle everything
time-based:
- Unlocking a scenario at its scheduled time
- Auto-closing a scenario when its time-box expires
- Firing a scripted mid-scenario pivot (the "client changes their mind" moment) at a
  cohort-configured time

This mirrors the FastAPI + Celery + Redis stack already proven on `genai-pulse-bot`.

### AI persona service — open-weight model via PromptOps Gateway
Each scenario defines a persona: a system prompt encoding personality, agenda, and
what the persona does/doesn't know, plus per-student conversation state. Persona
calls route through [[promptops-gateway]] rather than hitting the Claude API
directly — this gives centralized usage governance and observability across the
whole training program for free, reusing infrastructure that already exists instead
of building it twice.

Implemented (FDE-004) as its own `persona-service/` FastAPI app, sharing the same
Postgres instance as the backend rather than calling it over HTTP: the persona
lives in the existing `scenario_instances.config` JSON column as
`config["persona"] = {"system_prompt", "agenda"}`, and the persona service
reads/writes that column directly (`app/scenario_ref.py`) while owning its own
`conversations` / `messages` tables for per-student history. The system prompt is
rebuilt from the current config on every turn, so any change to
`config["persona"]` takes effect on the next message without starting a new
conversation — either path below picks this up automatically:
- FDE-002's scripted pivot job merges `pivot_config` into `config` directly in
  Postgres (now a one-level-deep merge, so a `persona` key in `pivot_config`
  updates fields like `agenda` without clobbering `system_prompt`).
- `POST /scenario-instances/{id}/persona/pivot` updates `agenda` the same way,
  for a manual/instructor-triggered pivot outside the scripted-time path.
Neither path calls the other — they're two independent ways to reach the same
`config["persona"]` update, not a call chain. No real PromptOps Gateway exists
yet, and a hosted frontier-model API (Claude, GPT) costs real money per call
for a training lab, so `app/gateway.py` talks to an open-weight model via the
OpenAI-compatible chat/completions contract instead — the shape Groq,
Together, DeepInfra, OpenRouter, and Ollama's own `/v1` endpoint all share, so
switching provider is a URL/key/model env-var change, not a rewrite. Defaults
to Groq (`FDE_PROMPTOPS_GATEWAY_URL=https://api.groq.com/openai/v1`, model
`openai/gpt-oss-20b`) — free tier, and inference-hardware-backed so it isn't
competing with the host machine's own CPU/GPU the way a local Ollama instance
was; `FDE_PROMPTOPS_GATEWAY_URL` can still be pointed at a local Ollama's
`/v1` path (no API key needed) to go fully local again, or at a real
PromptOps Gateway once one exists. `backend/app/scenario_generator.py`
(FDE-014) talks to the same backend via the same env vars.

### Enterprise system mocks
Three purpose-built services reproducing the "someone else's constraints" friction:
- **Legacy API simulator** — mock REST endpoints with intentionally quirky behavior
  (inconsistent schemas, latency, auth friction)
- **Compliance checklist engine** — a rules-based gate a submission must satisfy
  before it can "ship"
- **Approval workflow** — a state machine (submitted → pending_review →
  approved/rejected), optionally with a built-in delay to simulate a real
  review cycle. Implemented (FDE-007) directly in `backend/`, not as a
  standalone `mocks/` service: a `Submission` table (FK to
  `scenario_instances`) plus a `scenario.auto_decide` Celery task, reusing
  the same ETA-scheduling pattern as the scenario pivot/unlock/close jobs
  (`app/tasks.py`). This needed real DB persistence and delay-based
  scheduling to satisfy its acceptance criteria, which the compliance engine
  and legacy API mock didn't — so it resolves the "separate service vs.
  backend route" open question for itself only, not for the other two.

### Synthetic data generation
A standalone module (`data-gen/`) that runs at **cohort setup time**, not randomly or
on a fixed schedule. It reads its config from the scenario instance's own
`config.data_gen` block (`domain`, `row_count`, `messiness`), generates that cohort's
dataset fresh, uploads it to object storage under a `uuid4`-suffixed key (so a dataset
is never overwritten or reused across runs, even a re-run of the same instance), and
records the resulting location back onto the scenario instance via
`PATCH /scenario-instances/{id}/dataset` on the backend (`dataset_location` column).

Domains are code-defined schemas (v1 ships `ecommerce_orders` and `hr_employees`) —
each a fixed column list, an id column, and a Faker-backed row builder that generates
fake PII (names, emails) to mask. Messiness is exposed as three named levels rather
than raw per-field knobs, since scenario authors think in terms of "how messy," not
individual rates:

| Level  | Null rate | Duplicate rate | Schema drift |
|--------|-----------|-----------------|--------------|
| low    | 2%        | 1%              | none |
| medium | 8%        | 5%              | renamed/extra columns on a subset of rows |
| high   | 20%       | 12%             | renamed/extra columns on a subset of rows |

Output is newline-delimited JSON, not CSV — schema drift means rows can carry
differing column sets, which a flat CSV can't represent. Freshness (never reusing a
previous cohort's dataset) comes from two independent guarantees: the RNG seed is
freshly drawn per run (never derived from the cohort/instance id), and the storage
key always includes a new `uuid4`.

### Technical deliverable grading
The compliance checklist and approval workflow above gate a submission's
*prose* — required/forbidden phrases, a minimum length. Neither checks
whether the student actually solved anything, so FDE-013 adds a second,
independent gate for scenarios that configure `config["technical_task"]`:
the submission is graded by actually running it, not by scanning its text.
v1 supports one `task_type`, `sql_query` — implemented directly in
`backend/app/grading.py` (not a standalone `mocks/` service, same reasoning
as the approval workflow: it needs the instance's live `dataset_location`
and runs inline in the same request as the compliance gate, not on a
schedule). The submitted query is checked for `SELECT`-only/single-statement
before it runs, executed read-only against an in-memory SQLite table loaded
from the scenario's own synthetic dataset (FDE-003's `dataset_location`,
fetched via the same S3-compatible object storage everything else uses),
and its result set compared to a scenario-configured `reference_query`'s.
`create_submission` runs this after the compliance gate when
`technical_task` is configured — both must pass; either failing returns the
same `{message, failures}` 422 shape the compliance gate already used, so no
new client-facing contract was needed. A passing submission records what was
graded (`Submission.grading_result`) alongside the existing approval-workflow
columns.

### Scenario generator
FDE-013 made a submission gradable by execution instead of only by keyword;
FDE-014 does the same for the scenario itself — instead of an instructor
hand-writing a scenario's JSON config, `backend/app/scenario_generator.py`
drafts one from a raw requirement via the same model backend
persona-service uses (`FDE_PROMPTOPS_GATEWAY_URL`/`_API_KEY`/`_MODEL`,
duplicated config rather than shared, per this repo's independent-services
convention). The model can only choose from what the rest of the platform
actually knows how to run — data-gen's two domains
(`ecommerce_orders`/`hr_employees`, mirrored column lists) and the two
pre-authored legacy-mock scenarios (`acme-crm`/`northwind-erp`) — not
free-form invention, since nothing downstream could serve a domain or
endpoint that doesn't already exist. The drafted `technical_task.reference_query`
is executed against an empty table shaped like the chosen domain before the
draft is ever returned, catching a hallucinated column immediately rather
than at first student submission; a broken or unparseable draft is retried
once with the specific error fed back to the model, then surfaced as a
clean failure rather than handed to the instructor broken.
`POST /scenario-generator/draft` returns the draft for review — it isn't
persisted itself, an instructor creates the real instance via the
already-existing `POST /scenario-instances` with the (optionally edited)
result, so the generator adds no new creation path, only a new way to
produce that endpoint's input. Data-gen's dataset is still not
auto-triggered on instance creation (see below) — a freshly generated
scenario needs that one manual step before its technical task has anything
to grade against.

### Data layer
- **Postgres** — cohorts, students, scenario definitions, submissions, scores
- **Redis** — task queue and live session state for time-boxing
- **Object storage** (S3-compatible — R2 or S3) — synthetic datasets, artifact
  documents, submitted deliverables

## Repository layout

```
fde-lab/
  frontend/        # Next.js app (student + instructor views)
  backend/         # FastAPI service + Celery workers
  persona-service/ # Claude persona logic, routed via PromptOps Gateway
  lti-service/      # LTI 1.3 launch handling (Phase 3)
  mocks/           # legacy API sim, compliance engine, approval workflow
  data-gen/        # synthetic dataset generator
  orchestrator/    # LangGraph story-picker (see AGENT-WORKFLOW.md)
  infra/
    docker-compose.yml  # Phase 1-2: local/single-host deployment
    k8s/                # Phase 4: per-cohort namespaces (FDE-012)
      chart/             # Helm chart: one release == one cohort's full stack
      provisioner/        # small FastAPI service, the only thing holding
                           # cluster credentials to create cohort namespaces
      provision_cohort.py # CLI wrapper around provisioner/app/provision.py,
                           # for direct/ops use against a repo checkout
  intent.md
  architecture.md
  ROADMAP.md
```

## Deployment

Every service is containerized regardless of orchestrator — that part isn't
optional either way. What changes across phases is what runs those containers.
Full detail and sequencing lives in `ROADMAP.md`; summary:

**Phase 1-2: Docker Compose.** A `docker-compose.yml` wires together the FastAPI
backend, Celery workers, persona service, frontend, Postgres, Redis, and a local
S3-compatible store (e.g. MinIO). Single host, one cohort at a time. Fast to build
and validate the full core loop and, later, multi-cohort isolation logic on a
simple orchestrator before adding Kubernetes' complexity on top.

**Phase 4: Kubernetes.** Implemented (FDE-012) as a Helm chart at
`infra/k8s/chart/` — one release of the chart is one cohort: its own
namespace (`cohort-<slug>`), Postgres, Redis, MinIO, `backend`,
`celery-worker`, `persona-service`, and `frontend`, mirroring
`infra/docker-compose.yml` service-for-service (the one-shot
`backend-migrate`/`persona-migrate`/`minio-init` steps become
`post-install,post-upgrade` Helm hook Jobs; `data-gen` stays a one-off Job
rendered per scenario-instance setup rather than a standing workload,
matching its Compose `profiles: tools` treatment). A `NetworkPolicy`
default-denies cross-namespace traffic and only allows the ingress
controller's namespace in to the `frontend` Service (AC4) — only the
frontend is exposed publicly (its own server-side `/api/*` routes already
reach `backend`/`persona-service`, per the Frontend section above), so
`backend`/`persona-service`/`celery-worker`/Postgres/Redis/MinIO stay
ClusterIP-only per namespace. `Ingress` routes on `<cohortId>.<domain>`
(AC3) — since an Ingress can't reference a Service outside its own
namespace, cross-cohort routing isn't reachable even by misconfiguration.

Namespace provisioning (AC2) is a small standalone `k8s-provisioner`
FastAPI service (`infra/k8s/provisioner/`) that runs `helm upgrade
--install` against the chart — deliberately its own service rather than a
route on `backend`, since it's the one component in the platform holding
cluster credentials broad enough to create namespaces, and giving that to
the public-facing student/instructor API would be a real
privilege-escalation smell. The instructor-action trigger is real: `POST
/cohorts/{cohort_id}/provision` on `backend` (`app/routers/cohorts.py`)
calls it over HTTP. The LTI-launch trigger from `ROADMAP.md`'s "on LTI
launch, on instructor action" is *not* wired up as of FDE-012 — `backend`
still has no `/internal/lti-mappings` endpoint for `lti-service` to call at
all (the gap FDE-011 already flagged), and auto-provisioning cluster
namespaces off of an unauthenticated LMS launch's 404 would itself be a
resource-exhaustion vector, not just an incomplete feature. Once
`/internal/lti-mappings` gains a real *create* path (an instructor linking
an LMS course to a cohort), that's the point to call the same provisioner
— tracked as follow-up, not solved here.

The time-boxed scenario lifecycle (unlock/close/pivot) continues to run as
Celery tasks against `celery-worker` inside each cohort's own namespace,
not Kubernetes Jobs/CronJobs — Celery/Redis already does ETA-based
one-shot scheduling (see Backend section above), so there was no need to
duplicate that with a second scheduling mechanism at the cluster level; if
that's read as a deviation from this document's original wording, this is
the correction. Docker Compose remains the local development target even
after Kubernetes is the production target — nothing above changes
`infra/docker-compose.yml`.

## Traceability to intent.md

| Intent.md requirement | Architecture answer |
|---|---|
| Flexible scenario engine, cohort-calibrated | Scenario engine service + per-cohort scenario config |
| Synthetic data generated fresh per run | Data-gen module, triggered at cohort setup |
| AI-driven persona (stakeholder + demo audience) | Persona service on Claude, via PromptOps Gateway |
| Enterprise constraints (legacy systems, compliance, approvals) | Mocks service (three sub-components) |
| Scheduled, time-boxed cohort pacing | Celery + Redis scheduling in the backend |
| Solo scenarios, team capstone | Data model supports both individual and team-scoped submissions |
| End-to-end, client-ready v1 (no smaller slice) | Docker Compose deployment of the full stack above, not a partial slice |
| LMS-integrated delivery for cohorts | LTI 1.3 launch service (Phase 3) + Kubernetes per-cohort namespaces (Phase 4) |

## Open questions

- Auth model for students who arrive outside an LMS launch (LTI login covers the
  LMS-launched path; instructors and non-LMS access still need something — email/
  magic-link vs SSO)
- How persona personality/agenda gets *authored* per scenario — the storage format
  is now decided (`scenario_instances.config["persona"]`, see AI persona service
  above), but there's no authoring tooling yet; instructors currently need config
  written by hand/API call
- Whether the legacy API mock and compliance engine are separate services or
  route-namespaced within the main backend for v1 — the approval workflow
  resolved this for itself in FDE-007 (backend route + DB table, not a
  standalone service), but that doesn't settle it for the other two
- Which LMS(s) to target first for Phase 3 (Canvas and Moodle both speak LTI 1.3,
  but roster/grade APIs have platform-specific quirks worth confirming early)
- Namespace provisioning trigger for Phase 4 — resolved for the instructor-action
  path (FDE-012: `POST /cohorts/{cohort_id}/provision`); the LTI-launch path is
  still open, blocked on `backend` gaining a real `/internal/lti-mappings` create
  endpoint (see Deployment → Phase 4 above and FDE-011's implementation log)
