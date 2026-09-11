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

### AI persona service — Claude via PromptOps Gateway
Each scenario defines a persona: a system prompt encoding personality, agenda, and
what the persona does/doesn't know, plus per-student conversation state. Persona
calls route through [[promptops-gateway]] rather than hitting the Claude API
directly — this gives centralized usage governance and observability across the
whole training program for free, reusing infrastructure that already exists instead
of building it twice.

### Enterprise system mocks
Three purpose-built services reproducing the "someone else's constraints" friction:
- **Legacy API simulator** — mock REST endpoints with intentionally quirky behavior
  (inconsistent schemas, latency, auth friction)
- **Compliance checklist engine** — a rules-based gate a submission must satisfy
  before it can "ship"
- **Approval workflow** — a state machine (submitted → pending → approved/rejected),
  optionally with a built-in delay to simulate a real review cycle

### Synthetic data generation
A standalone module that runs at **cohort setup time**, not randomly or on a fixed
schedule. Given a scenario config (domain, target messiness, schema), it generates
that cohort's dataset fresh — nulls, duplicates, schema drift, fake PII to mask — so
no two training runs reuse the same data.

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
    k8s/                # Phase 4: manifests or Helm chart, per-cohort namespaces
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

**Phase 4: Kubernetes.** Once the LMS integration (Phase 3) is real, multiple
courses/cohorts can launch concurrently, each needing an isolated environment —
fresh synthetic data, its own mock services, its own time-box clock. Each cohort
gets its own Kubernetes namespace, provisioned automatically on LTI launch or
instructor action. Ingress routes per cohort; the time-boxed scenario lifecycle
(unlock/close/pivot) maps onto Kubernetes Jobs/CronJobs. Docker Compose remains
the local development target even after Kubernetes is the production target.

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
- How persona personality/agenda gets authored per scenario (config format, tooling)
- Exact parameterization schema for the data generator (what "messiness" knobs exist)
- Whether the legacy API mock, compliance engine, and approval workflow are separate
  services or route-namespaced within the main backend for v1
- Which LMS(s) to target first for Phase 3 (Canvas and Moodle both speak LTI 1.3,
  but roster/grade APIs have platform-specific quirks worth confirming early)
- Namespace provisioning trigger for Phase 4 — on LTI launch, on instructor action,
  or both

- Namespace provisioning trigger for Phase 4 — on LTI launch, on instructor action,
-   or both
